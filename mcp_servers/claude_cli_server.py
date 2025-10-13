#!/usr/bin/env python3
"""
Claude CLI MCP Server - Expose Claude CLI as MCP tool

Wraps ClaudeCLISimple as an MCP server for parallel execution.

Tools:
1. claude_generate - Generate code or text with Claude
2. claude_read_file - Read file via Claude (uses Read tool)
3. claude_run_command - Run bash command via Claude (uses Bash tool)

Benefits:
- Parallel execution with other MCP tools
- Consistent error handling
- Timeout management
- HITL support via workspace_path

Register:
    claude mcp add claude python mcp_servers/claude_cli_server.py

Usage:
    result = await mcp.call("claude", "generate", {
        "prompt": "Generate React component",
        "workspace_path": "/path/to/workspace",
        "agent_name": "codesmith",
        "temperature": 0.2,
        "max_tokens": 8192
    })

Author: KI AutoAgent Team
Version: 1.0.0
"""

import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from adapters.claude_cli_simple import ClaudeCLISimple
from langchain_core.messages import SystemMessage, HumanMessage


async def claude_generate(
    prompt: str,
    workspace_path: str,
    system_prompt: str | None = None,
    agent_name: str = "assistant",
    temperature: float = 0.3,
    max_tokens: int = 4096,
    tools: list[str] | None = None
) -> dict[str, Any]:
    """
    Generate code or text with Claude CLI.

    Args:
        prompt: User prompt (task description)
        workspace_path: Absolute path to workspace
        system_prompt: System prompt (agent instructions)
        agent_name: Agent name (for HITL tracking)
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        tools: Available tools (default: ["Read", "Edit", "Bash"])

    Returns:
        {
            "success": bool,
            "content": str,
            "agent": str,
            "duration_ms": float,
            "files_created": list[dict]
        }
    """
    try:
        # Create Claude CLI instance
        llm = ClaudeCLISimple(
            model="claude-sonnet-4-20250514",
            temperature=temperature,
            max_tokens=max_tokens,
            agent_name=agent_name,
            agent_tools=tools or ["Read", "Edit", "Bash"],
            workspace_path=workspace_path
        )

        # Build messages
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        # Execute
        start = datetime.now()
        response = await llm.ainvoke(messages)
        duration_ms = (datetime.now() - start).total_seconds() * 1000

        # Extract files created
        files_created = []
        if hasattr(llm, 'last_events') and llm.last_events:
            files_created = llm.extract_file_paths_from_events(llm.last_events)

        return {
            "success": True,
            "content": response.content if hasattr(response, 'content') else str(response),
            "agent": agent_name,
            "duration_ms": duration_ms,
            "files_created": files_created,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "agent": agent_name,
            "timestamp": datetime.now().isoformat()
        }


async def claude_read_file(
    file_path: str,
    workspace_path: str
) -> dict[str, Any]:
    """
    Read file via Claude (uses Read tool).

    Args:
        file_path: Path to file (relative to workspace)
        workspace_path: Absolute path to workspace

    Returns:
        {
            "success": bool,
            "content": str,
            "file_path": str
        }
    """
    try:
        llm = ClaudeCLISimple(
            agent_name="reader",
            agent_tools=["Read"],
            workspace_path=workspace_path
        )

        prompt = f"Read the file: {file_path}"
        response = await llm.ainvoke([HumanMessage(content=prompt)])

        return {
            "success": True,
            "content": response.content if hasattr(response, 'content') else str(response),
            "file_path": file_path,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path,
            "timestamp": datetime.now().isoformat()
        }


async def claude_run_command(
    command: str,
    workspace_path: str
) -> dict[str, Any]:
    """
    Run bash command via Claude (uses Bash tool).

    Args:
        command: Bash command to run
        workspace_path: Absolute path to workspace

    Returns:
        {
            "success": bool,
            "output": str,
            "command": str
        }
    """
    try:
        llm = ClaudeCLISimple(
            agent_name="runner",
            agent_tools=["Bash"],
            workspace_path=workspace_path
        )

        prompt = f"Run this command: {command}"
        response = await llm.ainvoke([HumanMessage(content=prompt)])

        return {
            "success": True,
            "output": response.content if hasattr(response, 'content') else str(response),
            "command": command,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "command": command,
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# MCP PROTOCOL HANDLER
# ============================================================================

async def handle_request(request: dict) -> dict:
    """Handle MCP JSON-RPC request"""

    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    # Initialize
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "claude-cli-mcp-server",
                    "version": "1.0.0"
                }
            }
        }

    # List tools
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {
                        "name": "claude_generate",
                        "description": "Generate code or text with Claude CLI. Supports file creation via Edit tool.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "prompt": {"type": "string", "description": "User prompt (task)"},
                                "workspace_path": {"type": "string", "description": "Workspace path"},
                                "system_prompt": {"type": "string", "description": "System prompt (optional)"},
                                "agent_name": {"type": "string", "description": "Agent name (default: assistant)"},
                                "temperature": {"type": "number", "description": "Temperature (default: 0.3)"},
                                "max_tokens": {"type": "integer", "description": "Max tokens (default: 4096)"},
                                "tools": {"type": "array", "description": "Tools list (default: [Read, Edit, Bash])"}
                            },
                            "required": ["prompt", "workspace_path"]
                        }
                    },
                    {
                        "name": "claude_read_file",
                        "description": "Read file via Claude (uses Read tool)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "file_path": {"type": "string", "description": "File path (relative to workspace)"},
                                "workspace_path": {"type": "string", "description": "Workspace path"}
                            },
                            "required": ["file_path", "workspace_path"]
                        }
                    },
                    {
                        "name": "claude_run_command",
                        "description": "Run bash command via Claude (uses Bash tool)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "command": {"type": "string", "description": "Bash command"},
                                "workspace_path": {"type": "string", "description": "Workspace path"}
                            },
                            "required": ["command", "workspace_path"]
                        }
                    }
                ]
            }
        }

    # Execute tool
    elif method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})

        try:
            if tool_name == "claude_generate":
                result = await claude_generate(**tool_args)
            elif tool_name == "claude_read_file":
                result = await claude_read_file(**tool_args)
            elif tool_name == "claude_run_command":
                result = await claude_run_command(**tool_args)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"}
                }

            # Format response
            content_text = f"# Claude CLI Result\n\n**Tool:** {tool_name}\n\n"
            content_text += f"**Result:**\n```json\n{json.dumps(result, indent=2)}\n```\n"

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": content_text}]
                }
            }

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": f"Tool execution failed: {e}"}
            }

    # Unknown method
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        }


# ============================================================================
# MAIN SERVER LOOP
# ============================================================================

async def main():
    """Main MCP server loop (stdin/stdout protocol)"""

    print(f"[{datetime.now()}] Claude CLI MCP Server started", file=sys.stderr)

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            request = json.loads(line)
            response = await handle_request(request)

            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

        except json.JSONDecodeError as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"}
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Internal error: {e}"}
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] Interrupted by user", file=sys.stderr)
    except Exception as e:
        print(f"[{datetime.now()}] Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
