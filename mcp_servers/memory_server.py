#!/usr/bin/env python3
"""
Memory MCP Server - Agent Memory Access

Provides agent memory access via MCP protocol.

IMPORTANT: This server requires backend dependencies (aiosqlite, faiss, openai).
Run with backend venv Python:
    /path/to/backend/venv_v6/bin/python mcp_servers/memory_server.py

Features:
- Store memories with metadata (agent, type, etc.)
- Semantic search with FAISS + OpenAI embeddings
- Filter by metadata (agent, type, etc.)
- Get statistics (total, by agent, by type)

Tools:
1. store_memory - Store content with metadata
2. search_memory - Semantic search with filters
3. get_memory_stats - Get memory statistics
4. count_memory - Get total memory count

Technical:
- Uses existing MemorySystem (FAISS + SQLite + OpenAI)
- workspace_path required for each call
- Async/await throughout
- JSON-RPC 2.0 compliant

Run:
    python mcp_servers/memory_server.py

Register with Claude:
    claude mcp add memory python mcp_servers/memory_server.py

Test:
    claude "Store this in memory: Vite + React 18 recommended"

Author: KI AutoAgent Team
Version: 1.0.0 (MCP Protocol)
"""

import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Direct import to avoid circular dependencies
import importlib.util
spec = importlib.util.spec_from_file_location(
    "memory_system_v6",
    backend_path / "memory" / "memory_system_v6.py"
)
memory_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(memory_module)
MemorySystem = memory_module.MemorySystem


# ============================================================================
# GLOBAL MEMORY INSTANCES (cached per workspace)
# ============================================================================

# Cache memory instances to avoid reinitializing
_memory_cache: dict[str, Any] = {}


async def get_memory_system(workspace_path: str) -> Any:
    """
    Get or create MemorySystem for workspace.

    Uses cache to avoid reinitializing for same workspace.

    Args:
        workspace_path: Absolute path to workspace

    Returns:
        MemorySystem instance
    """
    if workspace_path not in _memory_cache:
        memory = MemorySystem(workspace_path)
        await memory.initialize()
        _memory_cache[workspace_path] = memory
        print(f"[{datetime.now()}] Memory initialized for: {workspace_path}", file=sys.stderr)
    else:
        print(f"[{datetime.now()}] Memory retrieved from cache: {workspace_path}", file=sys.stderr)

    return _memory_cache[workspace_path]


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================

async def store_memory(
    workspace_path: str,
    content: str,
    metadata: dict[str, Any]
) -> dict:
    """
    Store content in memory with metadata.

    Args:
        workspace_path: Absolute path to workspace
        content: Text content to store
        metadata: Metadata dict (agent, type, etc.)

    Returns:
        {
            "vector_id": int,
            "workspace": str,
            "success": bool
        }
    """
    try:
        memory = await get_memory_system(workspace_path)

        # Store in memory
        vector_id = await memory.store(content=content, metadata=metadata)

        return {
            "success": True,
            "vector_id": vector_id,
            "workspace": workspace_path,
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "metadata": metadata,
            "message": f"✅ Memory stored (ID: {vector_id})"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "workspace": workspace_path,
            "message": f"❌ Failed to store memory: {str(e)}"
        }


async def search_memory(
    workspace_path: str,
    query: str,
    filters: dict[str, Any] | None = None,
    k: int = 5
) -> dict:
    """
    Search memory using semantic similarity.

    Args:
        workspace_path: Absolute path to workspace
        query: Search query text
        filters: Metadata filters (e.g., {"agent": "research"})
        k: Number of results to return

    Returns:
        {
            "results": list[dict],
            "count": int,
            "query": str,
            "filters": dict
        }
    """
    try:
        memory = await get_memory_system(workspace_path)

        # Search memory
        results = await memory.search(query=query, filters=filters, k=k)

        return {
            "success": True,
            "results": results,
            "count": len(results),
            "query": query,
            "filters": filters,
            "workspace": workspace_path,
            "message": f"✅ Found {len(results)} result(s)"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "workspace": workspace_path,
            "query": query,
            "message": f"❌ Search failed: {str(e)}"
        }


async def get_memory_stats(workspace_path: str) -> dict:
    """
    Get memory system statistics.

    Args:
        workspace_path: Absolute path to workspace

    Returns:
        {
            "total_items": int,
            "by_agent": dict[str, int],
            "by_type": dict[str, int]
        }
    """
    try:
        memory = await get_memory_system(workspace_path)

        # Get stats
        stats = await memory.get_stats()

        return {
            "success": True,
            "workspace": workspace_path,
            "stats": stats,
            "message": f"✅ Memory stats retrieved ({stats['total_items']} items)"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "workspace": workspace_path,
            "message": f"❌ Failed to get stats: {str(e)}"
        }


async def count_memory(workspace_path: str) -> dict:
    """
    Get total number of memory items.

    Args:
        workspace_path: Absolute path to workspace

    Returns:
        {
            "count": int,
            "workspace": str
        }
    """
    try:
        memory = await get_memory_system(workspace_path)

        # Get count
        count = await memory.count()

        return {
            "success": True,
            "count": count,
            "workspace": workspace_path,
            "message": f"✅ Memory contains {count} item(s)"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "workspace": workspace_path,
            "message": f"❌ Failed to count: {str(e)}"
        }


# ============================================================================
# MCP PROTOCOL HANDLER
# ============================================================================

async def handle_request(request: dict) -> dict:
    """
    Handle incoming MCP request.

    MCP uses JSON-RPC 2.0 protocol:
    - Request: {"jsonrpc": "2.0", "id": 1, "method": "...", "params": {...}}
    - Response: {"jsonrpc": "2.0", "id": 1, "result": {...}}
    - Error: {"jsonrpc": "2.0", "id": 1, "error": {"code": -32601, "message": "..."}}
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
                    "name": "memory-mcp-server",
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
                        "name": "store_memory",
                        "description": "Store content in agent memory with metadata. Memories are stored in a FAISS vector store with semantic search capabilities. Use this to save important information, learnings, or decisions.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "workspace_path": {
                                    "type": "string",
                                    "description": "Absolute path to workspace (e.g., /Users/me/MyProject)"
                                },
                                "content": {
                                    "type": "string",
                                    "description": "Text content to store in memory"
                                },
                                "metadata": {
                                    "type": "object",
                                    "description": "Metadata for the memory (agent, type, confidence, etc.)",
                                    "properties": {
                                        "agent": {
                                            "type": "string",
                                            "description": "Agent name (research, architect, codesmith, reviewfix)"
                                        },
                                        "type": {
                                            "type": "string",
                                            "description": "Memory type (technology, design, learning, decision)"
                                        }
                                    }
                                }
                            },
                            "required": ["workspace_path", "content", "metadata"]
                        }
                    },
                    {
                        "name": "search_memory",
                        "description": "Search agent memory using semantic similarity. Finds memories similar to your query. Can filter by agent or type.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "workspace_path": {
                                    "type": "string",
                                    "description": "Absolute path to workspace"
                                },
                                "query": {
                                    "type": "string",
                                    "description": "Search query (semantic search)"
                                },
                                "filters": {
                                    "type": "object",
                                    "description": "Metadata filters (e.g., {\"agent\": \"research\"})"
                                },
                                "k": {
                                    "type": "integer",
                                    "description": "Number of results to return (default: 5)"
                                }
                            },
                            "required": ["workspace_path", "query"]
                        }
                    },
                    {
                        "name": "get_memory_stats",
                        "description": "Get memory system statistics including total items, breakdown by agent, and breakdown by type.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "workspace_path": {
                                    "type": "string",
                                    "description": "Absolute path to workspace"
                                }
                            },
                            "required": ["workspace_path"]
                        }
                    },
                    {
                        "name": "count_memory",
                        "description": "Get total number of memory items in the workspace.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "workspace_path": {
                                    "type": "string",
                                    "description": "Absolute path to workspace"
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
            if tool_name == "store_memory":
                result = await store_memory(
                    workspace_path=tool_args.get("workspace_path", ""),
                    content=tool_args.get("content", ""),
                    metadata=tool_args.get("metadata", {})
                )

            elif tool_name == "search_memory":
                result = await search_memory(
                    workspace_path=tool_args.get("workspace_path", ""),
                    query=tool_args.get("query", ""),
                    filters=tool_args.get("filters"),
                    k=tool_args.get("k", 5)
                )

            elif tool_name == "get_memory_stats":
                result = await get_memory_stats(
                    workspace_path=tool_args.get("workspace_path", "")
                )

            elif tool_name == "count_memory":
                result = await count_memory(
                    workspace_path=tool_args.get("workspace_path", "")
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
            content_text = f"# Memory Tool Result\n\n"
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
    print(f"[{datetime.now()}] Memory MCP Server started", file=sys.stderr)
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
