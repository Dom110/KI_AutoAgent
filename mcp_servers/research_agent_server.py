#!/usr/bin/env python3
"""
⚠️ MCP BLEIBT: Research Agent MCP Server
⚠️ WICHTIG: MCP BLEIBT! Research Agent läuft NUR als MCP-Server!
⚠️ KEINE direkten API-Calls! Alles über MCPClient!

This MCP server provides research capabilities including:
- Workspace analysis and file discovery
- Web search via Perplexity (through MCP)
- Error analysis and debugging help
- Technology verification
- Security vulnerability research

MCP Protocol Compliance:
- JSON-RPC 2.0 over stdin/stdout
- $/progress notifications for all research stages
- Dynamic tool discovery
- Calls other MCP servers (Perplexity) via MCPClient

Author: KI AutoAgent v7.0
Date: 2025-10-30
"""

import sys
import json
import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

# Configure logging to stderr (stdout is for JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("research_mcp_server")


class ResearchAgentMCPServer:
    """
    ⚠️ MCP BLEIBT: Research Agent als vollständiger MCP Server

    Der Research Agent ist jetzt ein MCP Server und nutzt andere MCP Server
    (wie Perplexity) für externe Suchen. KEINE direkten API-Calls mehr!
    """

    def __init__(self):
        self.request_id = 0
        self.initialized = False
        self.mcp = None  # MCPClient instance (injected during initialization)
        self.workspace_path = None

        # ⚠️ MCP BLEIBT: Tool registry
        self.tools = {
            "research": {
                "description": "Execute research based on instructions (workspace analysis, web search, error analysis, etc.)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "instructions": {
                            "type": "string",
                            "description": "What to research (e.g., 'analyze workspace', 'search best practices for FastAPI')"
                        },
                        "workspace_path": {
                            "type": "string",
                            "description": "Path to workspace to analyze"
                        },
                        "error_info": {
                            "type": "array",
                            "description": "List of errors to investigate",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["instructions"]
                }
            },
            "analyze_workspace": {
                "description": "Analyze workspace structure and detect project type",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace_path": {
                            "type": "string",
                            "description": "Path to workspace directory"
                        }
                    },
                    "required": ["workspace_path"]
                }
            },
            "search_web": {
                "description": "Search web for information using Perplexity",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            },
            "analyze_errors": {
                "description": "Analyze errors and suggest fixes",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "errors": {
                            "type": "array",
                            "description": "List of error messages",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["errors"]
                }
            }
        }

    async def send_progress(self, progress: float, message: str):
        """
        ⚠️ MCP BLEIBT: Send $/progress notification
        """
        notification = {
            "jsonrpc": "2.0",
            "method": "$/progress",
            "params": {
                "progress": progress,
                "total": 1.0,
                "message": message,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        await self.send_message(notification)

    async def send_message(self, message: Dict[str, Any]):
        """Send JSON-RPC message to stdout."""
        try:
            json_str = json.dumps(message)
            sys.stdout.write(json_str + "\n")
            sys.stdout.flush()
            logger.debug(f"Sent: {json_str}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⚠️ MCP BLEIBT: Handle initialize request
        """
        self.initialized = True

        # Store workspace_path if provided
        self.workspace_path = params.get("workspace_path")

        logger.info("Research Agent MCP Server initialized")
        if self.workspace_path:
            logger.info(f"   Workspace: {self.workspace_path}")

        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "notifications": {
                    "progress": True
                }
            },
            "serverInfo": {
                "name": "research-agent-mcp-server",
                "version": "7.0.0",
                "description": "⚠️ MCP BLEIBT: Research Agent for KI AutoAgent"
            }
        }

    async def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⚠️ MCP BLEIBT: List available tools
        """
        return {
            "tools": [
                {
                    "name": name,
                    "description": tool["description"],
                    "inputSchema": tool["inputSchema"]
                }
                for name, tool in self.tools.items()
            ]
        }

    async def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⚠️ MCP BLEIBT: Execute tool call
        """
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        # Route to appropriate handler
        if tool_name == "research":
            return await self.tool_research(arguments)
        elif tool_name == "analyze_workspace":
            return await self.tool_analyze_workspace(arguments)
        elif tool_name == "search_web":
            return await self.tool_search_web(arguments)
        elif tool_name == "analyze_errors":
            return await self.tool_analyze_errors(arguments)

        raise ValueError(f"Tool {tool_name} not implemented")

    async def tool_research(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⚠️ MCP BLEIBT: Execute comprehensive research

        This is the main entry point that orchestrates all research activities.
        """
        try:
            await self.send_progress(0.0, "🔍 Starting research...")

            instructions = args.get("instructions", "")
            workspace_path = args.get("workspace_path", self.workspace_path)
            error_info = args.get("error_info", [])

            logger.info(f"Research: {instructions[:100]}...")

            research_context = {}

            # Workspace analysis
            if "workspace" in instructions.lower() or "analyze" in instructions.lower():
                await self.send_progress(0.2, "📁 Analyzing workspace...")
                research_context["workspace_analysis"] = await self.tool_analyze_workspace({
                    "workspace_path": workspace_path
                })

            # Web search
            if "best practice" in instructions.lower() or "research" in instructions.lower() or "search" in instructions.lower():
                await self.send_progress(0.5, "🌐 Searching web...")
                # ⚠️ MCP BLEIBT: Web search via Perplexity MCP server!
                web_results = await self.tool_search_web({"query": instructions})
                research_context["web_results"] = web_results

            # Error analysis
            if error_info or "error" in instructions.lower() or "fix" in instructions.lower():
                await self.send_progress(0.7, "🔧 Analyzing errors...")
                research_context["error_analysis"] = await self.tool_analyze_errors({
                    "errors": error_info
                })

            await self.send_progress(1.0, "✅ Research complete")

            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(research_context, indent=2)
                    }
                ],
                "metadata": {
                    "research_areas": list(research_context.keys()),
                    "instructions": instructions,
                    "timestamp": datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Research failed: {e}")
            await self.send_progress(1.0, f"❌ Error: {str(e)}")
            raise

    async def tool_analyze_workspace(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⚠️ MCP BLEIBT: Analyze workspace structure

        This is a LOCAL operation - no MCP calls needed.
        """
        workspace_path = args.get("workspace_path", self.workspace_path)

        logger.info(f"Analyzing workspace: {workspace_path}")

        if not workspace_path or not os.path.exists(workspace_path):
            return {
                "error": "Invalid workspace path",
                "file_count": 0,
                "project_type": "unknown"
            }

        analysis = {
            "workspace_path": workspace_path,
            "file_count": 0,
            "file_types": {},
            "directories": [],
            "project_type": "unknown",
            "languages": [],
            "frameworks": [],
            "has_tests": False,
            "has_docs": False,
            "configuration_files": []
        }

        try:
            # Walk directory tree
            for root, dirs, files in os.walk(workspace_path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

                for file in files:
                    if file.startswith('.'):
                        continue

                    analysis["file_count"] += 1
                    ext = Path(file).suffix.lower()

                    if ext:
                        analysis["file_types"][ext] = analysis["file_types"].get(ext, 0) + 1

                    # Configuration files
                    if file in ["package.json", "requirements.txt", "pyproject.toml", "Cargo.toml", "go.mod"]:
                        analysis["configuration_files"].append(file)

                    # Tests
                    if "test" in file.lower() or "spec" in file.lower():
                        analysis["has_tests"] = True

                    # Docs
                    if file.lower() in ["readme.md", "readme.rst"]:
                        analysis["has_docs"] = True

            # Detect languages and project type
            if ".py" in analysis["file_types"]:
                analysis["languages"].append("Python")
                if "requirements.txt" in analysis["configuration_files"]:
                    analysis["project_type"] = "Python"

            if ".js" in analysis["file_types"] or ".ts" in analysis["file_types"]:
                analysis["languages"].append("JavaScript/TypeScript")
                if "package.json" in analysis["configuration_files"]:
                    analysis["project_type"] = "Node.js"

            if ".rs" in analysis["file_types"]:
                analysis["languages"].append("Rust")
                analysis["project_type"] = "Rust"

            if ".go" in analysis["file_types"]:
                analysis["languages"].append("Go")
                analysis["project_type"] = "Go"

            # Detect frameworks
            if os.path.exists(os.path.join(workspace_path, "manage.py")):
                analysis["frameworks"].append("Django")
            if os.path.exists(os.path.join(workspace_path, "app.py")):
                analysis["frameworks"].append("Flask/FastAPI")

            logger.info(f"   ✅ Analysis complete: {analysis['file_count']} files, type={analysis['project_type']}")

        except Exception as e:
            logger.error(f"   ❌ Workspace analysis error: {e}")
            analysis["error"] = str(e)

        return analysis

    async def tool_search_web(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⚠️ MCP BLEIBT: Search web via Perplexity MCP Server

        WICHTIG: Dieser Code ruft NIEMALS direkt Perplexity API auf!
        Alle Suchen gehen über den Perplexity MCP Server!
        """
        query = args.get("query")

        logger.info(f"Web search: {query[:50]}...")

        try:
            # ⚠️ MCP BLEIBT: Call Perplexity via MCP!
            # TODO: This will be implemented once MCPClient is available
            # For now, return placeholder indicating MCP architecture

            # In the final implementation:
            # result = await self.mcp.call(
            #     server="perplexity",
            #     tool="search",
            #     arguments={"query": query}
            # )

            # Placeholder for MCP migration phase
            return {
                "title": "Web Search via MCP (Not Yet Connected)",
                "summary": f"⚠️ MCP BLEIBT: Search for '{query}' will use Perplexity MCP server when MCPClient is connected",
                "citations": [],
                "timestamp": datetime.now().isoformat(),
                "note": "This will call Perplexity MCP server in final implementation"
            }

        except Exception as e:
            logger.error(f"   ❌ Web search error: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def tool_analyze_errors(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⚠️ MCP BLEIBT: Analyze errors and suggest fixes

        This is a LOCAL operation using pattern matching.
        """
        errors = args.get("errors", [])

        logger.info(f"Analyzing {len(errors)} errors")

        analysis = {
            "error_count": len(errors),
            "errors": [],
            "root_cause": "Unknown",
            "suggested_fix": "Further investigation needed"
        }

        for error in errors[:5]:  # Analyze max 5 errors
            error_str = str(error)
            error_analysis = {
                "error": error_str,
                "type": "unknown",
                "suggestion": ""
            }

            # Pattern matching
            if "ImportError" in error_str or "ModuleNotFoundError" in error_str:
                error_analysis["type"] = "import"
                error_analysis["suggestion"] = "Check if module is installed and import path is correct"

            elif "SyntaxError" in error_str:
                error_analysis["type"] = "syntax"
                error_analysis["suggestion"] = "Check for missing parentheses, colons, or indentation"

            elif "TypeError" in error_str:
                error_analysis["type"] = "type"
                error_analysis["suggestion"] = "Check argument types and function signatures"

            elif "AttributeError" in error_str:
                error_analysis["type"] = "attribute"
                error_analysis["suggestion"] = "Verify object has the attribute/method being accessed"

            elif "KeyError" in error_str:
                error_analysis["type"] = "key"
                error_analysis["suggestion"] = "Check if dictionary key exists before accessing"

            elif "test" in error_str.lower() and "fail" in error_str.lower():
                error_analysis["type"] = "test_failure"
                error_analysis["suggestion"] = "Review test assertions and expected vs actual values"

            analysis["errors"].append(error_analysis)

        # Determine root cause
        error_types = [e["type"] for e in analysis["errors"]]
        if error_types:
            most_common = max(set(error_types), key=error_types.count)
            analysis["root_cause"] = f"Primarily {most_common} errors"

            if most_common == "import":
                analysis["suggested_fix"] = "Review dependencies and import statements"
            elif most_common == "test_failure":
                analysis["suggested_fix"] = "Fix implementation to match test expectations"

        logger.info(f"   ✅ Error analysis complete: root_cause={analysis['root_cause']}")

        return analysis

    async def handle_request(self, request: Dict[str, Any]):
        """
        ⚠️ MCP BLEIBT: Handle incoming JSON-RPC request
        """
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        logger.info(f"Request {request_id}: {method}")

        try:
            # Route to handler
            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "tools/list":
                result = await self.handle_tools_list(params)
            elif method == "tools/call":
                result = await self.handle_tools_call(params)
            else:
                raise ValueError(f"Unknown method: {method}")

            # Send success response
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            await self.send_message(response)

        except Exception as e:
            logger.error(f"Request {request_id} failed: {e}")
            # Send error response
            error_response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            await self.send_message(error_response)

    async def run(self):
        """
        ⚠️ MCP BLEIBT: Main server loop
        """
        logger.info("🚀 Research Agent MCP Server starting...")
        logger.info("⚠️ MCP BLEIBT: This server MUST remain MCP-compliant!")

        try:
            loop = asyncio.get_event_loop()

            while True:
                line = await loop.run_in_executor(None, sys.stdin.readline)

                if not line:
                    logger.info("EOF received, shutting down")
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    await self.handle_request(request)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    continue

        except Exception as e:
            logger.error(f"Server error: {e}")
            raise


async def main():
    """
    ⚠️ MCP BLEIBT: Entry point for Research Agent MCP Server
    """
    server = ResearchAgentMCPServer()
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
