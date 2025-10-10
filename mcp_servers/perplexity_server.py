#!/usr/bin/env python3
"""
Perplexity MCP Server

Provides web search capabilities via Perplexity API as an MCP tool.

This server makes Perplexity search available to Claude CLI and any
other MCP-compatible client.

Register:
    claude mcp add perplexity python mcp_servers/perplexity_server.py

Usage:
    claude "Research Python async patterns using perplexity"
    # Claude will automatically use the perplexity_search tool!

Author: KI AutoAgent Team
Version: 1.0.0 (MCP Protocol)
"""

import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path

# Add backend to path to import our existing tools
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from dotenv import load_dotenv
# Load API keys from global config
env_path = Path.home() / ".ki_autoagent" / "config" / ".env"
load_dotenv(env_path)


async def perplexity_search(query: str, max_results: int = 5) -> dict:
    """
    Execute Perplexity search.

    Reuses existing PerplexityService implementation.

    Args:
        query: Search query
        max_results: Maximum number of results to return

    Returns:
        dict with search results
    """
    try:
        from utils.perplexity_service import PerplexityService

        service = PerplexityService()

        # Execute search
        result = await service.search_web(
            query=query,
            max_results=max_results,
            recency="month"  # Recent results (last month)
        )

        return {
            "success": True,
            "query": query,
            "content": result.get("answer", ""),
            "sources": result.get("citations", []),
            "timestamp": result.get("timestamp", datetime.now().isoformat()),
            "result_count": len(result.get("citations", []))
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "timestamp": datetime.now().isoformat()
        }


async def handle_request(request: dict) -> dict:
    """
    Handle incoming MCP request.

    Implements the MCP JSON-RPC 2.0 protocol.
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
                    "name": "perplexity-mcp-server",
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
                        "name": "perplexity_search",
                        "description": (
                            "Search the web using Perplexity API. "
                            "Provides high-quality research results with sources. "
                            "Ideal for technical research, documentation, and fact-checking."
                        ),
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query. Be specific for best results."
                                },
                                "max_results": {
                                    "type": "integer",
                                    "description": "Maximum number of results to return (default: 5)",
                                    "default": 5
                                }
                            },
                            "required": ["query"]
                        }
                    }
                ]
            }
        }

    # Execute tool
    elif method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})

        if tool_name == "perplexity_search":
            query = tool_args.get("query")
            max_results = tool_args.get("max_results", 5)

            if not query:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": "Missing required parameter: query"
                    }
                }

            # Execute search
            result = await perplexity_search(query, max_results)

            if result.get("success"):
                # Format result for Claude
                content_text = (
                    f"# Perplexity Search Results\n\n"
                    f"**Query:** {result.get('query', query)}\n\n"
                    f"**Content:**\n{result.get('content', '')}\n\n"
                )

                sources = result.get("sources", [])
                if sources:
                    content_text += "**Sources:**\n"
                    for i, source in enumerate(sources, 1):
                        # Handle both string URLs and dict objects
                        if isinstance(source, str):
                            content_text += f"{i}. {source}\n"
                        elif isinstance(source, dict):
                            content_text += f"{i}. {source.get('url', str(source))}\n"

                content_text += f"\n**Retrieved:** {result.get('timestamp', 'N/A')}"

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
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": f"Perplexity search failed: {result.get('error', 'Unknown error')}"
                    }
                }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": f"Unknown tool: {tool_name}"
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


async def main():
    """
    Main MCP server loop.

    Reads JSON-RPC requests from stdin, processes them, writes responses to stdout.
    """

    # Log to stderr (stdout is reserved for MCP protocol)
    print(f"[{datetime.now()}] Perplexity MCP Server started", file=sys.stderr)
    print(f"[{datetime.now()}] Using Perplexity API for web search", file=sys.stderr)
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
            method = request.get("method", "unknown")
            print(f"[{datetime.now()}] Request: {method}", file=sys.stderr)

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
            import traceback
            traceback.print_exc(file=sys.stderr)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] Interrupted by user", file=sys.stderr)
    except Exception as e:
        print(f"[{datetime.now()}] Fatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
