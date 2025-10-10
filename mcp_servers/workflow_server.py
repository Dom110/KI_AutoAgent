#!/usr/bin/env python3
"""
Workflow MCP Server - v6 Workflow Integration

Provides v6 workflow execution and monitoring via MCP protocol.

Features:
- Execute complete v6 workflows
- Query classification
- System health monitoring
- Learning history access

Tools:
1. execute_workflow - Start full v6 workflow
2. classify_query - Classify user query (type, complexity, agents)
3. get_system_health - Get self-diagnosis health report
4. get_learning_history - View past workflow executions

Run:
    backend/venv_v6/bin/python mcp_servers/workflow_server.py

Register with Claude:
    claude mcp add workflow backend/venv_v6/bin/python mcp_servers/workflow_server.py

Test:
    claude "Execute workflow: Build React app"

Author: KI AutoAgent Team
Version: 1.0.0 (MCP Protocol)
"""

import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

# Add backend to path for normal imports (fixes dataclass slots=True bug)
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# ============================================================================
# LAZY IMPORT HELPERS
# ============================================================================
# Import heavy v6 modules only when actually needed (not at server startup)
# This keeps server startup fast (< 1s instead of 2-3 minutes)

def _get_workflow_class():
    """Lazy import WorkflowV6Integrated."""
    from workflow_v6_integrated import WorkflowV6Integrated
    return WorkflowV6Integrated


def _get_classifier_class():
    """Lazy import QueryClassifierV6."""
    from cognitive.query_classifier_v6 import QueryClassifierV6
    return QueryClassifierV6


# ============================================================================
# GLOBAL STATE MANAGEMENT
# ============================================================================

# Active workflows (workspace -> workflow instance)
_active_workflows: dict[str, Any] = {}

# Workflow history (workspace -> list of executions)
_workflow_history: dict[str, list[dict]] = {}


async def get_or_create_workflow(workspace_path: str) -> Any:
    """Get or create WorkflowV6Integrated instance for workspace."""
    if workspace_path not in _active_workflows:
        WorkflowClass = _get_workflow_class()  # Lazy import
        workflow = WorkflowClass(workspace_path=workspace_path)
        await workflow.initialize()
        _active_workflows[workspace_path] = workflow

    return _active_workflows[workspace_path]


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================

async def execute_workflow(
    workspace_path: str,
    user_query: str,
    session_id: str | None = None
) -> dict:
    """
    Execute complete v6 workflow.

    Runs full multi-agent workflow with ALL v6 systems:
    - Query Classification
    - Curiosity System (clarifying questions)
    - Predictive System (duration/risk estimation)
    - Research → Architect → Codesmith → ReviewFix
    - Workflow Adapter (dynamic routing)
    - Neurosymbolic Reasoning (validation)
    - Learning System (post-execution)
    - Self-Diagnosis (error recovery)

    Args:
        workspace_path: Absolute path to workspace
        user_query: User's task description
        session_id: Optional session ID (default: timestamp)

    Returns:
        {
            "success": bool,
            "session_id": str,
            "execution_time": float,
            "quality_score": float,
            "result": {...},
            "errors": [...],
            "warnings": [...],
            "analysis": {...}  # Pre-execution analysis
        }
    """
    try:
        # Get or create workflow
        workflow = await get_or_create_workflow(workspace_path)

        # Generate session ID if not provided
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Execute workflow
        result = await workflow.run(
            user_query=user_query,
            session_id=session_id
        )

        # Store in history
        if workspace_path not in _workflow_history:
            _workflow_history[workspace_path] = []

        _workflow_history[workspace_path].append({
            "session_id": session_id,
            "query": user_query,
            "timestamp": datetime.now().isoformat(),
            "success": result["success"],
            "execution_time": result["execution_time"],
            "quality_score": result["quality_score"]
        })

        return {
            "success": True,
            **result,
            "workspace_path": workspace_path
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "workspace_path": workspace_path,
            "user_query": user_query
        }


async def classify_query(
    user_query: str,
    include_suggestions: bool = False
) -> dict:
    """
    Classify user query using QueryClassifierV6.

    Analyzes query to determine:
    - Type (CODE_GENERATION, DEBUGGING, REFACTORING, etc.)
    - Complexity (SIMPLE, MODERATE, COMPLEX)
    - Required agents (research, architect, codesmith, reviewfix)
    - Workflow type (linear, iterative, exploratory)
    - Entities (technologies, patterns, frameworks)

    Args:
        user_query: User's query/task
        include_suggestions: If true, include refinement suggestions

    Returns:
        {
            "query_type": str,
            "complexity": str,
            "confidence": float,
            "required_agents": list[str],
            "workflow_type": str,
            "entities": dict,
            "suggestions": list[str] (if include_suggestions=true)
        }
    """
    try:
        ClassifierClass = _get_classifier_class()  # Lazy import
        classifier = ClassifierClass()
        classification = await classifier.classify_query(user_query)

        result = {
            "success": True,
            "query": user_query,
            "classification": {
                "query_type": classification.query_type.value,
                "complexity": classification.complexity.value,
                "confidence": classification.confidence,
                "required_agents": classification.required_agents,
                "workflow_type": classification.workflow_type,
                "entities": classification.entities
            }
        }

        # Add refinement suggestions if requested
        if include_suggestions and classification.confidence < 0.7:
            suggestions = await classifier.suggest_refinements(classification)
            result["suggestions"] = suggestions

        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": user_query
        }


async def get_system_health(
    workspace_path: str
) -> dict:
    """
    Get system health report from Self-Diagnosis system.

    Provides insights about:
    - Active diagnostics
    - Error patterns
    - Healing suggestions
    - System status

    Args:
        workspace_path: Absolute path to workspace

    Returns:
        {
            "healthy": bool,
            "diagnostics_count": int,
            "active_issues": list[dict],
            "health_report": dict
        }
    """
    try:
        # Get workflow instance
        workflow = await get_or_create_workflow(workspace_path)

        # Get health report from self-diagnosis
        if workflow.self_diagnosis:
            health_report = workflow.self_diagnosis.get_health_report()

            return {
                "success": True,
                "workspace_path": workspace_path,
                "healthy": len(health_report.get("active_issues", [])) == 0,
                "diagnostics_count": health_report.get("total_diagnostics", 0),
                "health_report": health_report
            }
        else:
            return {
                "success": False,
                "error": "Self-diagnosis system not initialized",
                "workspace_path": workspace_path
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "workspace_path": workspace_path
        }


async def get_learning_history(
    workspace_path: str,
    limit: int = 10
) -> dict:
    """
    Get learning history from past workflow executions.

    Retrieves data from Learning System about:
    - Past workflow executions
    - Quality scores
    - Execution times
    - Common patterns

    Args:
        workspace_path: Absolute path to workspace
        limit: Maximum number of entries to return

    Returns:
        {
            "total_executions": int,
            "history": list[dict],
            "workspace_path": str
        }
    """
    try:
        # Get from local history
        history = _workflow_history.get(workspace_path, [])

        # Get workflow instance for more details
        workflow = await get_or_create_workflow(workspace_path)

        # Get learning stats if available
        learning_stats = {}
        if workflow.learning:
            # Try to get stats from memory
            if workflow.memory:
                stats = await workflow.memory.get_stats()
                learning_stats = {
                    "total_memories": stats.get("total_items", 0),
                    "by_agent": stats.get("by_agent", {}),
                    "by_type": stats.get("by_type", {})
                }

        return {
            "success": True,
            "workspace_path": workspace_path,
            "total_executions": len(history),
            "history": history[-limit:] if history else [],
            "learning_stats": learning_stats
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "workspace_path": workspace_path
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
                    "name": "workflow-mcp-server",
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
                        "name": "execute_workflow",
                        "description": "Execute complete v6 workflow with ALL intelligence systems. Runs Research → Architect → Codesmith → ReviewFix with dynamic adaptation. WARNING: This can take 5-15 minutes depending on task complexity.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "workspace_path": {
                                    "type": "string",
                                    "description": "Absolute path to workspace root"
                                },
                                "user_query": {
                                    "type": "string",
                                    "description": "User's task description (e.g., 'Build React todo app with auth')"
                                },
                                "session_id": {
                                    "type": "string",
                                    "description": "Optional session ID for tracking (default: auto-generated timestamp)"
                                }
                            },
                            "required": ["workspace_path", "user_query"]
                        }
                    },
                    {
                        "name": "classify_query",
                        "description": "Classify user query to determine type, complexity, and required agents. Fast analysis (< 1 second) to understand task before execution.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "user_query": {
                                    "type": "string",
                                    "description": "User's query or task description"
                                },
                                "include_suggestions": {
                                    "type": "boolean",
                                    "description": "If true, include query refinement suggestions (default: false)"
                                }
                            },
                            "required": ["user_query"]
                        }
                    },
                    {
                        "name": "get_system_health",
                        "description": "Get health report from Self-Diagnosis system. Shows active issues, diagnostics, and healing suggestions.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "workspace_path": {
                                    "type": "string",
                                    "description": "Absolute path to workspace root"
                                }
                            },
                            "required": ["workspace_path"]
                        }
                    },
                    {
                        "name": "get_learning_history",
                        "description": "Get learning history from past workflow executions. Includes quality scores, execution times, and patterns.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "workspace_path": {
                                    "type": "string",
                                    "description": "Absolute path to workspace root"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of history entries to return (default: 10)"
                                }
                            },
                            "required": ["workspace_path"]
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
            if tool_name == "execute_workflow":
                result = await execute_workflow(
                    workspace_path=tool_args.get("workspace_path", ""),
                    user_query=tool_args.get("user_query", ""),
                    session_id=tool_args.get("session_id")
                )

            elif tool_name == "classify_query":
                result = await classify_query(
                    user_query=tool_args.get("user_query", ""),
                    include_suggestions=tool_args.get("include_suggestions", False)
                )

            elif tool_name == "get_system_health":
                result = await get_system_health(
                    workspace_path=tool_args.get("workspace_path", "")
                )

            elif tool_name == "get_learning_history":
                result = await get_learning_history(
                    workspace_path=tool_args.get("workspace_path", ""),
                    limit=tool_args.get("limit", 10)
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
            content_text = f"# Workflow Result\\n\\n"
            content_text += f"**Tool:** {tool_name}\\n\\n"
            content_text += f"**Result:**\\n```json\\n{json.dumps(result, indent=2)}\\n```\\n\\n"
            content_text += f"**Timestamp:** {datetime.now().isoformat()}\\n"

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
    print(f"[{datetime.now()}] Workflow MCP Server started", file=sys.stderr)
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
            sys.stdout.write(json.dumps(response) + "\\n")
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
            sys.stdout.write(json.dumps(error_response) + "\\n")
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
            sys.stdout.write(json.dumps(error_response) + "\\n")
            sys.stdout.flush()
            print(f"[{datetime.now()}] Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\\n[{datetime.now()}] Interrupted by user", file=sys.stderr)
    except Exception as e:
        print(f"[{datetime.now()}] Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
