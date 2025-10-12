"""
Permission-Aware Tool Registry v6.2

Dynamically filters available tools based on agent permissions.

Features:
- Tool registration with required permissions
- Dynamic tool filtering per agent
- Permission validation before tool access
- Audit logging of tool usage

Integration:
- Workflow: Get tools for specific agent
- Agents: Only see tools they have permission to use
- Permissions Manager: Check permissions before tool access

Example:
    registry = ToolRegistryV6()

    # Register tool with permission requirement
    registry.register_tool(
        tool_name="write_file",
        tool_callable=write_file,
        required_permission=Permission.CAN_WRITE_FILES,
        description="Write files to workspace"
    )

    # Get tools for specific agent
    tools = registry.get_tools_for_agent("codesmith")
    # Returns: [write_file, read_file, ...] (only permitted tools)

Author: KI AutoAgent Team
Version: 6.2.0 (Phase 3.3)
Python: 3.13+
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from security.asimov_permissions_v6 import get_permissions_manager, Permission

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Tool definition with permission requirements."""

    name: str
    callable: Callable
    required_permission: Permission | None
    description: str
    category: str = "general"


class ToolRegistryV6:
    """
    Permission-aware tool registry.

    Manages tools and filters them based on agent permissions.
    """

    def __init__(self):
        """Initialize tool registry."""
        self.tools: dict[str, ToolDefinition] = {}
        self.permissions_manager = get_permissions_manager()

        logger.info("🔧 Tool Registry v6 initialized (permission-aware)")

    def register_tool(
        self,
        tool_name: str,
        tool_callable: Callable,
        required_permission: Permission | None = None,
        description: str = "",
        category: str = "general"
    ) -> None:
        """
        Register a tool with optional permission requirement.

        Args:
            tool_name: Tool identifier
            tool_callable: Tool function/callable
            required_permission: Permission required to use tool (None = no restriction)
            description: Tool description
            category: Tool category (file, web, system, etc.)

        Example:
            registry.register_tool(
                tool_name="write_file",
                tool_callable=write_file,
                required_permission=Permission.CAN_WRITE_FILES,
                description="Write files to workspace",
                category="file"
            )
        """
        tool_def = ToolDefinition(
            name=tool_name,
            callable=tool_callable,
            required_permission=required_permission,
            description=description,
            category=category
        )

        self.tools[tool_name] = tool_def

        perm_str = required_permission.value if required_permission else "none"
        logger.debug(f"🔧 Registered tool: {tool_name} (permission: {perm_str})")

    def get_tools_for_agent(self, agent_id: str) -> list[Callable]:
        """
        Get list of tools agent has permission to use.

        Args:
            agent_id: Agent identifier

        Returns:
            List of tool callables agent can access

        Example:
            tools = registry.get_tools_for_agent("codesmith")
            # Returns: [write_file, read_file, execute_code, ...]
        """
        permitted_tools = []

        for tool_name, tool_def in self.tools.items():
            # If no permission required, tool is available to all
            if tool_def.required_permission is None:
                permitted_tools.append(tool_def.callable)
                continue

            # Check if agent has required permission
            if self.permissions_manager.check_permission(
                agent_id,
                tool_def.required_permission
            ):
                permitted_tools.append(tool_def.callable)
                logger.debug(f"✅ Tool '{tool_name}' available to {agent_id}")
            else:
                logger.debug(f"🚫 Tool '{tool_name}' denied to {agent_id} (requires {tool_def.required_permission.value})")

        logger.info(f"🔧 Agent {agent_id}: {len(permitted_tools)}/{len(self.tools)} tools available")

        return permitted_tools

    def get_tool_definitions_for_agent(self, agent_id: str) -> list[ToolDefinition]:
        """
        Get list of tool definitions agent has permission to use.

        Args:
            agent_id: Agent identifier

        Returns:
            List of ToolDefinition objects
        """
        permitted_defs = []

        for tool_def in self.tools.values():
            # If no permission required, tool is available to all
            if tool_def.required_permission is None:
                permitted_defs.append(tool_def)
                continue

            # Check if agent has required permission
            if self.permissions_manager.check_permission(
                agent_id,
                tool_def.required_permission
            ):
                permitted_defs.append(tool_def)

        return permitted_defs

    def get_all_tools(self) -> list[ToolDefinition]:
        """
        Get all registered tools (regardless of permissions).

        Returns:
            List of all tool definitions
        """
        return list(self.tools.values())

    def get_tools_by_category(self, category: str, agent_id: str | None = None) -> list[Callable]:
        """
        Get tools by category, optionally filtered by agent permissions.

        Args:
            category: Tool category (file, web, system, etc.)
            agent_id: Optional agent ID for permission filtering

        Returns:
            List of tool callables in category
        """
        category_tools = [
            tool_def for tool_def in self.tools.values()
            if tool_def.category == category
        ]

        if agent_id is None:
            # No filtering
            return [tool_def.callable for tool_def in category_tools]

        # Filter by permissions
        permitted_tools = []
        for tool_def in category_tools:
            if tool_def.required_permission is None:
                permitted_tools.append(tool_def.callable)
            elif self.permissions_manager.check_permission(agent_id, tool_def.required_permission):
                permitted_tools.append(tool_def.callable)

        return permitted_tools

    def check_tool_access(
        self,
        agent_id: str,
        tool_name: str
    ) -> tuple[bool, str]:
        """
        Check if agent can access specific tool.

        Args:
            agent_id: Agent identifier
            tool_name: Tool name to check

        Returns:
            (can_access, message)

        Example:
            can_access, msg = registry.check_tool_access("research", "write_file")
            if not can_access:
                print(f"Access denied: {msg}")
        """
        if tool_name not in self.tools:
            return (False, f"Tool '{tool_name}' not found in registry")

        tool_def = self.tools[tool_name]

        # No permission required
        if tool_def.required_permission is None:
            return (True, "Tool has no permission requirement")

        # Check permission
        has_permission = self.permissions_manager.check_permission(
            agent_id,
            tool_def.required_permission
        )

        if has_permission:
            return (True, "Permission granted")
        else:
            return (
                False,
                f"Agent {agent_id} lacks permission: {tool_def.required_permission.value}"
            )

    def get_tool_stats(self) -> dict[str, Any]:
        """
        Get tool registry statistics.

        Returns:
            Dict with:
            - total_tools: Total registered tools
            - by_category: Tool count per category
            - by_permission: Tool count per required permission
        """
        by_category: dict[str, int] = {}
        by_permission: dict[str, int] = {}

        for tool_def in self.tools.values():
            # Count by category
            by_category[tool_def.category] = by_category.get(tool_def.category, 0) + 1

            # Count by permission
            perm_key = tool_def.required_permission.value if tool_def.required_permission else "none"
            by_permission[perm_key] = by_permission.get(perm_key, 0) + 1

        return {
            "total_tools": len(self.tools),
            "by_category": by_category,
            "by_permission": by_permission
        }


# Global tool registry instance
_tool_registry: ToolRegistryV6 | None = None


def get_tool_registry() -> ToolRegistryV6:
    """Get global tool registry instance."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistryV6()
    return _tool_registry


# Export
__all__ = [
    "ToolRegistryV6",
    "ToolDefinition",
    "get_tool_registry"
]
