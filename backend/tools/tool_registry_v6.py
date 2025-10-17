"""
Tool Registry v6 - Dynamic tool discovery and management

Capabilities:
- Auto-discover available tools
- Tool metadata (name, description, parameters)
- Per-agent tool assignment
- Runtime tool registration
- Tool capability matching
- Async tool loading

Integration:
- Agent initialization (assign tools based on capabilities)
- Research agent gets perplexity_search
- Codesmith gets file_tools
- Dynamic composition based on task

Author: KI AutoAgent Team
Version: 6.0.0
Python: 3.13+
"""

from __future__ import annotations

import importlib
import inspect
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass()
class ToolMetadata:
    """Metadata for a registered tool."""

    name: str
    function: Callable
    description: str
    parameters: dict[str, Any]
    capabilities: list[str]  # e.g., ["web_search", "file_write"]
    async_tool: bool
    module: str


class ToolRegistryV6:
    """
    Dynamic tool registry for agent tools.

    Discovers, registers, and manages tools for agents.
    """

    def __init__(self):
        """Initialize tool registry."""
        self.tools: dict[str, ToolMetadata] = {}
        self._discovery_paths: list[Path] = []
        logger.info("🔧 Tool Registry v6 initialized")

    async def discover_tools(
        self,
        search_path: str | Path | None = None
    ) -> dict[str, ToolMetadata]:
        """
        Auto-discover tools from filesystem.

        Args:
            search_path: Path to search for tools (default: backend/tools/)

        Returns:
            Dict of discovered tools {tool_name: ToolMetadata}
        """
        if search_path is None:
            # Default to backend/tools directory
            search_path = Path(__file__).parent
        else:
            search_path = Path(search_path)

        logger.info(f"🔍 Discovering tools in: {search_path}")

        discovered = {}

        # Scan Python files in directory
        for file_path in search_path.glob("*.py"):
            if file_path.name.startswith("_") or file_path.name == "tool_registry_v6.py":
                continue  # Skip private files and self

            try:
                # Import module
                module_name = file_path.stem
                module = importlib.import_module(f"tools.{module_name}")

                # Find tool functions (decorated with @tool or exported)
                if hasattr(module, "__all__"):
                    tool_names = module.__all__
                else:
                    # Find all public functions defined in this module
                    tool_names = []
                    for name in dir(module):
                        if name.startswith("_"):
                            continue

                        obj = getattr(module, name)

                        # Only include functions/callables defined in this module
                        if callable(obj) and hasattr(obj, "__module__"):
                            # Check if it's from this module (not imported)
                            if obj.__module__ == f"tools.{module_name}":
                                tool_names.append(name)

                # Register each tool
                for tool_name in tool_names:
                    tool_func = getattr(module, tool_name)

                    if callable(tool_func):
                        try:
                            metadata = self._extract_metadata(tool_func, module_name)
                            discovered[tool_name] = metadata
                            logger.debug(f"   Found tool: {tool_name}")
                        except Exception as e:
                            logger.warning(f"⚠️  Failed to extract metadata from {tool_name}: {e}")
                            continue

            except Exception as e:
                logger.warning(f"⚠️  Failed to load tools from {file_path.name}: {e}")
                continue

        logger.info(f"✅ Discovered {len(discovered)} tools")

        # Register discovered tools
        for tool_name, metadata in discovered.items():
            self.register_tool(tool_name, metadata)

        return discovered

    def register_tool(
        self,
        tool_name: str,
        metadata: ToolMetadata | None = None,
        tool_function: Callable | None = None,
        capabilities: list[str] | None = None
    ) -> bool:
        """
        Register a tool manually.

        Args:
            tool_name: Name of the tool
            metadata: Pre-built ToolMetadata
            tool_function: Tool function (if metadata not provided)
            capabilities: List of capabilities (if metadata not provided)

        Returns:
            True if registered successfully
        """
        try:
            if metadata is None:
                if tool_function is None:
                    raise ValueError("Either metadata or tool_function must be provided")

                # Create metadata from function
                metadata = self._extract_metadata(
                    tool_function,
                    tool_function.__module__,
                    capabilities or []
                )

            self.tools[tool_name] = metadata
            logger.debug(f"✅ Registered tool: {tool_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to register tool {tool_name}: {e}")
            return False

    def get_tool(self, tool_name: str) -> ToolMetadata | None:
        """Get tool by name."""
        return self.tools.get(tool_name)

    def get_tools_by_capability(
        self,
        capability: str
    ) -> list[ToolMetadata]:
        """
        Get all tools with a specific capability.

        Args:
            capability: Capability to filter by (e.g., "web_search")

        Returns:
            List of tools with that capability
        """
        return [
            tool for tool in self.tools.values()
            if capability in tool.capabilities
        ]

    def get_tools_for_agent(
        self,
        agent_type: str
    ) -> list[ToolMetadata]:
        """
        Get recommended tools for an agent type.

        Args:
            agent_type: Type of agent (e.g., "research", "codesmith")

        Returns:
            List of tools suitable for this agent
        """
        # Map agent types to capabilities they need
        agent_tool_map = {
            "research": ["web_search", "research"],
            "codesmith": ["file_write", "file_read", "code_generation"],
            "architect": ["file_read"],
            "reviewer": ["file_read", "code_analysis"],
            "fixer": ["file_read", "file_write", "code_generation"],
        }

        capabilities = agent_tool_map.get(agent_type, [])

        tools = []
        for capability in capabilities:
            tools.extend(self.get_tools_by_capability(capability))

        # Remove duplicates
        seen = set()
        unique_tools = []
        for tool in tools:
            if tool.name not in seen:
                seen.add(tool.name)
                unique_tools.append(tool)

        return unique_tools

    def list_all_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self.tools.keys())

    def get_tool_info(self, tool_name: str) -> dict[str, Any] | None:
        """
        Get human-readable info about a tool.

        Args:
            tool_name: Name of tool

        Returns:
            Dict with tool information
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return None

        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
            "capabilities": tool.capabilities,
            "async": tool.async_tool,
            "module": tool.module
        }

    def _extract_metadata(
        self,
        tool_func: Callable,
        module_name: str,
        capabilities: list[str] | None = None
    ) -> ToolMetadata:
        """Extract metadata from a tool function."""

        # Handle LangChain StructuredTool objects
        if hasattr(tool_func, "name") and hasattr(tool_func, "description"):
            # This is a LangChain tool
            name = tool_func.name
            description = tool_func.description or ""

            # Get parameters from args_schema if available
            parameters = {}
            if hasattr(tool_func, "args_schema") and tool_func.args_schema:
                schema = tool_func.args_schema
                if hasattr(schema, "__fields__"):
                    for field_name, field in schema.__fields__.items():
                        # Handle both Pydantic v1 and v2
                        field_type = "Any"
                        field_required = True
                        field_default = None

                        # Try Pydantic v2 (FieldInfo)
                        if hasattr(field, "annotation"):
                            field_type = str(field.annotation)
                        # Try Pydantic v1 (ModelField)
                        elif hasattr(field, "type_"):
                            field_type = str(field.type_)

                        if hasattr(field, "is_required"):
                            field_required = field.is_required()
                        elif hasattr(field, "required"):
                            field_required = field.required

                        if hasattr(field, "default"):
                            field_default = field.default

                        parameters[field_name] = {
                            "type": field_type,
                            "required": field_required,
                            "default": field_default
                        }

            # Get the underlying function for async check
            if hasattr(tool_func, "coroutine"):
                # LangChain tool has coroutine attribute
                is_async = tool_func.coroutine is not None
            elif hasattr(tool_func, "func"):
                is_async = inspect.iscoroutinefunction(tool_func.func)
            else:
                is_async = False

        else:
            # Regular function
            name = tool_func.__name__
            description = (tool_func.__doc__ or "").strip().split("\n")[0]

            # Get parameters from signature
            sig = inspect.signature(tool_func)
            parameters = {}
            for param_name, param in sig.parameters.items():
                if param_name in ["self", "cls"]:
                    continue

                param_info = {
                    "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                    "required": param.default == inspect.Parameter.empty,
                    "default": None if param.default == inspect.Parameter.empty else param.default
                }
                parameters[param_name] = param_info

            is_async = inspect.iscoroutinefunction(tool_func)

        # Infer capabilities from name and docstring
        if capabilities is None:
            capabilities = self._infer_capabilities(name, description)

        return ToolMetadata(
            name=name,
            function=tool_func,
            description=description,
            parameters=parameters,
            capabilities=capabilities,
            async_tool=is_async,
            module=module_name
        )

    def _infer_capabilities(
        self,
        name: str,
        description: str
    ) -> list[str]:
        """Infer capabilities from tool name and description."""
        capabilities = []

        text = f"{name} {description}".lower()

        # Web/search capabilities
        if any(word in text for word in ["search", "web", "perplexity", "research"]):
            capabilities.append("web_search")

        # File capabilities
        if "write" in text or "create" in text:
            capabilities.append("file_write")
        if "read" in text or "load" in text:
            capabilities.append("file_read")
        if "edit" in text or "modify" in text:
            capabilities.append("file_edit")

        # Code capabilities
        if any(word in text for word in ["code", "syntax", "parse"]):
            capabilities.append("code_analysis")

        # Default
        if not capabilities:
            capabilities.append("general")

        return capabilities

    async def compose_tools_for_task(
        self,
        task_description: str
    ) -> list[ToolMetadata]:
        """
        Compose optimal tool set for a specific task.

        Analyzes task description to determine which tools are needed.

        Args:
            task_description: Description of the task

        Returns:
            List of tools recommended for this task
        """
        logger.info(f"🔧 Composing tools for task: {task_description[:60]}...")

        task_lower = task_description.lower()
        needed_capabilities = set()

        # Analyze task for required capabilities
        if any(word in task_lower for word in ["research", "search", "find", "learn"]):
            needed_capabilities.add("web_search")

        if any(word in task_lower for word in ["create", "write", "build", "implement"]):
            needed_capabilities.add("file_write")
            needed_capabilities.add("code_generation")

        if any(word in task_lower for word in ["read", "analyze", "review", "check"]):
            needed_capabilities.add("file_read")

        if any(word in task_lower for word in ["edit", "modify", "update", "change"]):
            needed_capabilities.add("file_edit")

        # Get tools for each capability
        composed_tools = []
        seen = set()

        for capability in needed_capabilities:
            for tool in self.get_tools_by_capability(capability):
                if tool.name not in seen:
                    composed_tools.append(tool)
                    seen.add(tool.name)

        logger.info(f"✅ Composed {len(composed_tools)} tools for task")
        logger.debug(f"   Tools: {[t.name for t in composed_tools]}")

        return composed_tools


# Global registry instance
_registry: ToolRegistryV6 | None = None


def get_tool_registry() -> ToolRegistryV6:
    """Get global tool registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistryV6()
    return _registry


async def initialize_tool_registry() -> ToolRegistryV6:
    """
    Initialize and auto-discover tools.

    Returns:
        Initialized registry with discovered tools
    """
    registry = get_tool_registry()
    await registry.discover_tools()
    return registry


# Export
__all__ = ["ToolRegistryV6", "ToolMetadata", "get_tool_registry", "initialize_tool_registry"]
