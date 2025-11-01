#!/usr/bin/env python3
"""
Asimov Rules MCP Server - Safety & Compliance Validation

Provides code safety validation via MCP protocol.

The Four Asimov Rules:
1. NO FALLBACKS without documented reason
2. COMPLETE IMPLEMENTATION (no TODOs, no partial work)
3. GLOBAL ERROR SEARCH (fix ALL instances, not just one)
4. HUMAN-IN-THE-LOOP (escalate after 3-5 failed attempts)

Tools:
1. validate_code - Check code against Asimov Rules
2. global_error_search - Find ALL instances of an error
3. check_iteration_limit - Validate retry count
4. format_violations - Format validation report

Run:
    python mcp_servers/asimov_server.py

Register with Claude:
    claude mcp add asimov python mcp_servers/asimov_server.py

Test:
    claude "Validate this code for Asimov Rules"

Author: KI AutoAgent Team
Version: 1.0.0 (MCP Protocol)
"""

import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Direct import to avoid circular dependencies
import importlib.util
spec = importlib.util.spec_from_file_location(
    "asimov_rules",
    backend_path / "security" / "asimov_rules.py"
)
asimov_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asimov_module)

# Import functions
validate_asimov_rules = asimov_module.validate_asimov_rules
format_violations_report = asimov_module.format_violations_report
perform_global_error_search = asimov_module.perform_global_error_search
validate_iteration_limit = asimov_module.validate_iteration_limit


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================

async def validate_code(
    code: str,
    file_path: str = "unknown.py",
    strict: bool = False
) -> dict:
    """
    Validate code against Asimov Rules.

    Args:
        code: Code content to validate
        file_path: File path for context
        strict: If True, warnings treated as errors

    Returns:
        {
            "valid": bool,
            "violations": list[dict],
            "summary": dict,
            "report": str
        }
    """
    try:
        result = validate_asimov_rules(code, file_path, strict)

        # Add formatted report
        report = format_violations_report(result, file_path)
        result["report"] = report

        return {
            "success": True,
            **result,
            "file_path": file_path,
            "strict_mode": strict
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path
        }


async def global_error_search(
    workspace_path: str,
    error_pattern: str,
    file_extensions: list[str] | None = None
) -> dict:
    """
    Search entire workspace for all instances of an error pattern.

    Args:
        workspace_path: Path to workspace root
        error_pattern: Pattern to search for (regex or literal)
        file_extensions: List of extensions (e.g., [".py", ".js"])

    Returns:
        {
            "total_matches": int,
            "files": list[str],
            "matches": list[dict],
            "search_pattern": str,
            "workspace": str
        }
    """
    try:
        result = await perform_global_error_search(
            workspace_path,
            error_pattern,
            file_extensions
        )

        return {
            "success": True,
            **result
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "workspace": workspace_path,
            "search_pattern": error_pattern
        }


async def check_iteration_limit(
    retry_count: int,
    time_spent_minutes: float,
    task_id: str,
    last_error: str | None = None
) -> dict:
    """
    Check if agent should escalate to human (ASIMOV RULE 4).

    Args:
        retry_count: Number of retries for this task
        time_spent_minutes: Time spent on task
        task_id: Unique task identifier
        last_error: Optional, last error message

    Returns:
        {
            "valid": bool,
            "violations": list[dict],
            "should_ask_human": bool
        }
    """
    try:
        context = {
            "retry_count": retry_count,
            "time_spent_minutes": time_spent_minutes,
            "task_id": task_id
        }

        if last_error:
            context["last_error"] = last_error

        result = validate_iteration_limit(context)

        return {
            "success": True,
            **result,
            "context": context
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "task_id": task_id
        }


# ============================================================================
# MCP PROTOCOL HANDLER
# ============================================================================

async def handle_request(request: dict) -> dict:
    """
    Handle incoming MCP request.

    MCP uses JSON-RPC 2.0 protocol.
    """

    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    # Initialize: Return server capabilities
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "asimov-rules-mcp-server",
                    "version": "1.0.0"
                }
            }
        }

    # List available tools
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {
                        "name": "validate_code",
                        "description": "Validate code against Asimov Rules. Checks for: (1) Undocumented fallbacks, (2) Incomplete implementations (TODO/FIXME/NotImplementedError), (3) Pass statements, (4) Code quality issues.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "code": {
                                    "type": "string",
                                    "description": "Code content to validate"
                                },
                                "file_path": {
                                    "type": "string",
                                    "description": "File path for context (default: unknown.py)"
                                },
                                "strict": {
                                    "type": "boolean",
                                    "description": "If true, warnings treated as errors (default: false)"
                                }
                            },
                            "required": ["code"]
                        }
                    },
                    {
                        "name": "global_error_search",
                        "description": "Search entire workspace for all instances of an error pattern (ASIMOV RULE 3). When an error is found, find ALL instances across the project, not just the first one.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "workspace_path": {
                                    "type": "string",
                                    "description": "Absolute path to workspace root"
                                },
                                "error_pattern": {
                                    "type": "string",
                                    "description": "Pattern to search for (regex or literal string)"
                                },
                                "file_extensions": {
                                    "type": "array",
                                    "description": "File extensions to search (e.g., [\".py\", \".js\"])",
                                    "items": {
                                        "type": "string"
                                    }
                                }
                            },
                            "required": ["workspace_path", "error_pattern"]
                        }
                    },
                    {
                        "name": "check_iteration_limit",
                        "description": "Check if agent should escalate to human intervention (ASIMOV RULE 4). Validates retry count and time spent. Returns WARNING at 3 retries or 15 minutes, ERROR at 5 retries.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "retry_count": {
                                    "type": "integer",
                                    "description": "Number of retries for this task"
                                },
                                "time_spent_minutes": {
                                    "type": "number",
                                    "description": "Time spent on task in minutes"
                                },
                                "task_id": {
                                    "type": "string",
                                    "description": "Unique task identifier"
                                },
                                "last_error": {
                                    "type": "string",
                                    "description": "Optional: last error message"
                                }
                            },
                            "required": ["retry_count", "time_spent_minutes", "task_id"]
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
            # Call appropriate tool
            if tool_name == "validate_code":
                result = await validate_code(
                    code=tool_args.get("code", ""),
                    file_path=tool_args.get("file_path", "unknown.py"),
                    strict=tool_args.get("strict", False)
                )

            elif tool_name == "global_error_search":
                result = await global_error_search(
                    workspace_path=tool_args.get("workspace_path", ""),
                    error_pattern=tool_args.get("error_pattern", ""),
                    file_extensions=tool_args.get("file_extensions")
                )

            elif tool_name == "check_iteration_limit":
                result = await check_iteration_limit(
                    retry_count=tool_args.get("retry_count", 0),
                    time_spent_minutes=tool_args.get("time_spent_minutes", 0),
                    task_id=tool_args.get("task_id", "unknown"),
                    last_error=tool_args.get("last_error")
                )

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }

            # Format result
            content_text = f"# Asimov Rules Result\n\n"
            content_text += f"**Tool:** {tool_name}\n\n"
            content_text += f"**Result:**\n```json\n{json.dumps(result, indent=2)}\n```\n\n"
            content_text += f"**Timestamp:** {datetime.now().isoformat()}\n"

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": content_text
                        }
                    ]
                }
            }

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Tool execution failed: {str(e)}"
                }
            }

    # Unknown method
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }


# ============================================================================
# MAIN SERVER LOOP
# ============================================================================

async def main():
    """
    Main MCP server loop.

    Reads JSON-RPC requests from stdin (one per line),
    processes them, and writes responses to stdout.
    """

    # Log to stderr (stdout is reserved for MCP protocol)
    print(f"[{datetime.now()}] Asimov Rules MCP Server started", file=sys.stderr)
    print(f"[{datetime.now()}] Waiting for requests on stdin...", file=sys.stderr)

    # Main loop: read requests, send responses
    while True:
        try:
            # Read one line from stdin
            line = sys.stdin.readline()

            # End of input
            if not line:
                print(f"[{datetime.now()}] EOF reached, shutting down", file=sys.stderr)
                break

            line = line.strip()
            if not line:
                continue

            # Parse JSON-RPC request
            request = json.loads(line)
            print(f"[{datetime.now()}] Request: {request.get('method')}", file=sys.stderr)

            # Handle request
            response = await handle_request(request)

            # Write JSON-RPC response to stdout
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

            print(f"[{datetime.now()}] Response sent", file=sys.stderr)

        except json.JSONDecodeError as e:
            # Invalid JSON
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()
            print(f"[{datetime.now()}] JSON parse error: {e}", file=sys.stderr)

        except Exception as e:
            # Internal error
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()
            print(f"[{datetime.now()}] Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] Interrupted by user", file=sys.stderr)
    except Exception as e:
        print(f"[{datetime.now()}] Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
