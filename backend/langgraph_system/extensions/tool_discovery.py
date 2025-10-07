"""
Tool Discovery System for LangGraph
Automatic tool discovery and registration for agents
"""

import inspect
import json
import logging
from collections.abc import Callable
from dataclasses import asdict
from typing import Any, get_type_hints

from ..state import ToolDefinition

logger = logging.getLogger(__name__)


def tool(name: str = None, description: str = None, tags: list[str] = None):
    """
    Decorator to mark a method as a tool for discovery

    Usage:
        @tool(name="fix_bugs", description="Fix bugs in code")
        async def fix_bugs(self, code: str, errors: List[str]) -> str:
            ...
    """

    def decorator(func):
        func._is_tool = True
        func._tool_name = name or func.__name__
        func._tool_description = description or func.__doc__ or ""
        func._tool_tags = tags or []
        return func

    return decorator


class ToolRegistry:
    """
    Central registry for tool discovery and management
    """

    def __init__(self):
        self.tools: dict[str, ToolDefinition] = {}
        self.agent_tools: dict[str, list[str]] = {}
        self.shared_tools: list[str] = []
        self.tool_usage_stats: dict[str, dict[str, Any]] = {}

    def auto_discover_tools(self, agent_instance: Any) -> list[ToolDefinition]:
        """
        Automatically discover tools from an agent instance

        Looks for:
        - Methods decorated with @tool
        - Methods starting with 'tool_'
        - Methods with _is_tool attribute
        """
        discovered_tools = []
        agent_name = agent_instance.__class__.__name__

        for method_name, method in inspect.getmembers(agent_instance, inspect.ismethod):
            tool_def = None

            # Check if decorated with @tool
            if hasattr(method, "_is_tool"):
                tool_def = self._create_tool_from_decorated(method, agent_name)
            # Check if starts with 'tool_'
            elif method_name.startswith("tool_"):
                tool_def = self._create_tool_from_prefix(method, agent_name)

            if tool_def:
                discovered_tools.append(tool_def)
                self.register_tool(tool_def)
                logger.info(f"Discovered tool: {tool_def.name} from {agent_name}")

        return discovered_tools

    def _create_tool_from_decorated(
        self, method: Callable, agent_name: str
    ) -> ToolDefinition:
        """Create tool definition from decorated method"""
        return ToolDefinition(
            name=method._tool_name,
            description=method._tool_description,
            parameters=self._extract_parameters(method),
            callable=method,
            agent_owner=agent_name,
            tags=getattr(method, "_tool_tags", []),
        )

    def _create_tool_from_prefix(
        self, method: Callable, agent_name: str
    ) -> ToolDefinition:
        """Create tool definition from method with 'tool_' prefix"""
        tool_name = method.__name__.replace("tool_", "")
        return ToolDefinition(
            name=tool_name,
            description=method.__doc__ or f"Tool: {tool_name}",
            parameters=self._extract_parameters(method),
            callable=method,
            agent_owner=agent_name,
            tags=[],
        )

    def _extract_parameters(self, method: Callable) -> dict[str, Any]:
        """Extract parameter schema from method signature"""
        sig = inspect.signature(method)
        params = {}

        try:
            type_hints = get_type_hints(method)
        except:
            type_hints = {}

        for param_name, param in sig.parameters.items():
            if param_name in ["self", "cls"]:
                continue

            param_info = {
                "type": "string",  # Default
                "required": param.default == inspect.Parameter.empty,
                "description": "",
            }

            # Get type from type hints
            if param_name in type_hints:
                param_type = type_hints[param_name]
                param_info["type"] = self._python_type_to_json_type(param_type)

            # Add default value if exists
            if param.default != inspect.Parameter.empty:
                param_info["default"] = param.default

            params[param_name] = param_info

        return params

    def _python_type_to_json_type(self, python_type: Any) -> str:
        """Convert Python type to JSON schema type"""
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            list: "array",
            dict: "object",
            dict: "object",
            Any: "any",
        }

        # Handle generic types
        if hasattr(python_type, "__origin__"):
            origin = python_type.__origin__
            return type_map.get(origin, "any")

        return type_map.get(python_type, "any")

    def register_tool(self, tool: ToolDefinition, shared: bool = False):
        """Register a tool in the registry"""
        self.tools[tool.name] = tool

        if shared:
            self.shared_tools.append(tool.name)
        else:
            if tool.agent_owner not in self.agent_tools:
                self.agent_tools[tool.agent_owner] = []
            self.agent_tools[tool.agent_owner].append(tool.name)

        # Initialize usage stats
        if tool.name not in self.tool_usage_stats:
            self.tool_usage_stats[tool.name] = {
                "calls": 0,
                "successes": 0,
                "failures": 0,
                "total_time": 0.0,
            }

    def discover_tools_for_agent(self, agent_name: str) -> list[ToolDefinition]:
        """Get all available tools for a specific agent"""
        available = []

        # Agent's own tools
        if agent_name in self.agent_tools:
            for tool_name in self.agent_tools[agent_name]:
                if tool_name in self.tools:
                    available.append(self.tools[tool_name])

        # Shared tools
        for tool_name in self.shared_tools:
            if tool_name in self.tools:
                available.append(self.tools[tool_name])

        return available

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any], track_usage: bool = True
    ) -> Any:
        """Execute a tool with given arguments"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found in registry")

        tool = self.tools[tool_name]
        start_time = None

        if track_usage:
            import time

            start_time = time.time()
            self.tool_usage_stats[tool_name]["calls"] += 1

        try:
            # Call the tool
            if inspect.iscoroutinefunction(tool.callable):
                result = await tool.callable(**arguments)
            else:
                result = tool.callable(**arguments)

            if track_usage:
                self.tool_usage_stats[tool_name]["successes"] += 1

            return result

        except Exception as e:
            if track_usage:
                self.tool_usage_stats[tool_name]["failures"] += 1
            logger.error(f"Tool execution failed: {tool_name} - {str(e)}")
            raise

        finally:
            if track_usage and start_time:
                import time

                elapsed = time.time() - start_time
                self.tool_usage_stats[tool_name]["total_time"] += elapsed

    def get_tool_schema(self, tool_name: str) -> dict[str, Any]:
        """Get OpenAPI-style schema for a tool"""
        if tool_name not in self.tools:
            return None

        tool = self.tools[tool_name]
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                "properties": tool.parameters,
                "required": [
                    k for k, v in tool.parameters.items() if v.get("required", False)
                ],
            },
            "tags": tool.tags,
            "owner": tool.agent_owner,
        }

    def list_all_tools(self) -> list[dict[str, Any]]:
        """List all registered tools with their schemas"""
        return [self.get_tool_schema(tool_name) for tool_name in self.tools.keys()]

    def get_usage_stats(self, tool_name: str | None = None) -> dict[str, Any]:
        """Get usage statistics for tools"""
        if tool_name:
            return self.tool_usage_stats.get(tool_name, {})
        return self.tool_usage_stats

    def export_tools(self, format: str = "json") -> str:
        """Export all tools in specified format"""
        tools_data = {
            "tools": [asdict(tool) for tool in self.tools.values()],
            "agent_mapping": self.agent_tools,
            "shared_tools": self.shared_tools,
            "usage_stats": self.tool_usage_stats,
        }

        if format == "json":
            return json.dumps(tools_data, indent=2, default=str)
        elif format == "yaml":
            import yaml

            return yaml.dump(tools_data)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def import_tools(self, data: str, format: str = "json"):
        """Import tools from exported data"""
        if format == "json":
            tools_data = json.loads(data)
        elif format == "yaml":
            import yaml

            tools_data = yaml.safe_load(data)
        else:
            raise ValueError(f"Unsupported import format: {format}")

        # Clear existing tools
        self.tools.clear()
        self.agent_tools.clear()
        self.shared_tools.clear()

        # Import tools
        for tool_dict in tools_data.get("tools", []):
            # Note: callable cannot be serialized, needs to be re-attached
            tool = ToolDefinition(**tool_dict)
            self.tools[tool.name] = tool

        self.agent_tools = tools_data.get("agent_mapping", {})
        self.shared_tools = tools_data.get("shared_tools", [])
        self.tool_usage_stats = tools_data.get("usage_stats", {})


# Global registry instance
_global_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance"""
    return _global_registry
