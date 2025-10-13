"""
MCP (Model Context Protocol) Client Module

This module provides the MCPClient for unified MCP tool calls.

Usage:
    from mcp.mcp_client import MCPClient

    mcp = MCPClient(workspace_path="/path/to/workspace")
    await mcp.initialize()

    result = await mcp.call("perplexity", "search", {"query": "Python async"})

Author: KI AutoAgent Team
Python: 3.13+
"""

from .mcp_client import MCPClient, MCPConnectionError, MCPToolError

__all__ = ["MCPClient", "MCPConnectionError", "MCPToolError"]
