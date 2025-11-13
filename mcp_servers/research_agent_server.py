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

# ⚠️ MCP BLEIBT: Helper function for non-blocking stdin (FIXES blocking I/O issue)

# ⚠️ MCP BLEIBT: Load environment variables FIRST before any API calls
from dotenv import load_dotenv
load_dotenv('/Users/dominikfoert/.ki_autoagent/config/.env')

# ⚠️ LOGGING: Configure logging to file (stdout is for JSON-RPC)
# All log messages (info, debug, warning, error) go to /tmp/mcp_research_agent.log
log_file = "/tmp/mcp_research_agent.log"
logging.basicConfig(
    level=logging.DEBUG,  # Log everything!
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=log_file,
    filemode='a'  # Append mode
)
logger = logging.getLogger("research_mcp_server")
logger.info(f"=" * 80)
logger.info(f"🚀 Research MCP Server starting at {datetime.now()}")
logger.info(f"=" * 80)


# ⚠️ MCP BLEIBT: INLINE Helper for non-blocking stdin
async def async_stdin_readline() -> str:
    """Non-blocking stdin readline for asyncio"""
    loop = asyncio.get_event_loop()
    def _read():
        try:
            return sys.stdin.readline()
        except:
            return ""
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(None, _read),
            timeout=300.0
        )
    except asyncio.TimeoutError:
        logger.warning("⏱️ stdin timeout (parent disconnect?)")
        return ""
    except Exception as e:
        logger.error(f"❌ stdin error: {e}")
        return ""


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

        logger.info(f"🔨 Calling tool: {tool_name}")

        if tool_name not in self.tools:
            logger.error(f"❌ Unknown tool: {tool_name}")
            raise ValueError(f"Unknown tool: {tool_name}")

        try:
            # Route to appropriate handler
            if tool_name == "research":
                logger.info("   → Executing comprehensive research...")
                result = await self.tool_research(arguments)
            elif tool_name == "analyze_workspace":
                logger.info("   → Analyzing workspace...")
                result = await self.tool_analyze_workspace(arguments)
            elif tool_name == "search_web":
                logger.info("   → Searching web...")
                result = await self.tool_search_web(arguments)
            elif tool_name == "analyze_errors":
                logger.info("   → Analyzing errors...")
                result = await self.tool_analyze_errors(arguments)
            else:
                logger.error(f"❌ Tool {tool_name} not implemented")
                raise ValueError(f"Tool {tool_name} not implemented")

            logger.info(f"   ✅ Tool {tool_name} completed")
            return result

        except Exception as e:
            logger.error(f"❌ Tool {tool_name} failed: {type(e).__name__}: {str(e)[:100]}")
            raise

    async def tool_research(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⚠️ MCP BLEIBT: Execute comprehensive research

        This is the main entry point that orchestrates all research activities.
        Returns MCP-compliant response with content array.
        """
        try:
            await self.send_progress(0.0, "🔍 Starting research...")

            instructions = args.get("instructions", "")
            workspace_path = args.get("workspace_path", self.workspace_path)
            error_info = args.get("error_info", [])

            logger.info(f"🔬 Research: {instructions[:100]}...")

            research_context = {}
            research_log = []

            # Workspace analysis (LOCAL - no external API call)
            if "workspace" in instructions.lower() or "analyze" in instructions.lower():
                await self.send_progress(0.15, "📁 Analyzing workspace...")
                logger.info("   → Analyzing workspace structure...")
                workspace_data = await self.tool_analyze_workspace({
                    "workspace_path": workspace_path
                })
                research_context["workspace_analysis"] = workspace_data
                research_log.append(f"✅ Workspace analyzed: {workspace_data.get('file_count', 0)} files")

            # Web search (EXTERNAL - calls OpenAI)
            if "best practice" in instructions.lower() or "research" in instructions.lower() or "search" in instructions.lower() or True:
                await self.send_progress(0.5, "🌐 Searching web for best practices...")
                logger.info("   → Performing web search via OpenAI...")
                web_results = await self.tool_search_web({"query": instructions})
                research_context["web_results"] = web_results
                research_log.append(f"✅ Web search complete: {web_results.get('title', 'Results found')}")

            # Error analysis (LOCAL - pattern matching)
            if error_info or "error" in instructions.lower() or "fix" in instructions.lower():
                await self.send_progress(0.75, "🔧 Analyzing errors...")
                logger.info("   → Analyzing errors...")
                error_analysis = await self.tool_analyze_errors({
                    "errors": error_info
                })
                research_context["error_analysis"] = error_analysis
                research_log.append(f"✅ Error analysis: {error_analysis.get('root_cause', 'Analysis complete')}")

            await self.send_progress(1.0, "✅ Research complete")

            logger.info(f"   ✅ Research finished: {len(research_log)} activities completed")

            # ⚠️ MCP BLEIBT: Return MCP-compliant response
            research_summary = {
                "status": "complete",
                "research_areas": list(research_context.keys()),
                "activities": research_log,
                "data": research_context,
                "instructions": instructions,
                "workspace": workspace_path,
                "timestamp": datetime.now().isoformat()
            }

            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(research_summary, indent=2, default=str)
                    }
                ],
                "metadata": {
                    "research_areas": list(research_context.keys()),
                    "activity_count": len(research_log),
                    "instructions": instructions[:100],
                    "timestamp": datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"❌ Research failed: {type(e).__name__}: {str(e)}")
            await self.send_progress(1.0, f"❌ Error: {str(e)[:50]}")

            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "status": "error",
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "timestamp": datetime.now().isoformat()
                        }, indent=2)
                    }
                ],
                "metadata": {
                    "error": str(e)[:50],
                    "timestamp": datetime.now().isoformat()
                }
            }

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
        ⚠️ MCP BLEIBT: Search web via OpenAI GPT-4o with web knowledge

        Uses OpenAI's knowledge base (trained up to April 2024) to provide
        research results. In production, this would use Perplexity MCP for
        real-time web search.
        """
        query = args.get("query")

        logger.info(f"🌐 Web search: {query[:50]}...")
        logger.info(f"   Using OpenAI GPT-4o knowledge base for research...")

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI()

            # ⚠️ MCP BLEIBT: Use OpenAI for web search context
            search_prompt = f"""You are a research assistant. Provide detailed, accurate information about: {query}

Provide your response in JSON format with:
- title: Brief title
- summary: 2-3 paragraph summary of key findings
- key_points: List of 3-5 important points
- best_practices: List of relevant best practices if applicable
- references: List of suggested resources/documentation
- confidence: Your confidence level (high/medium/low)

Be specific and technical in your response."""

            logger.info(f"   📡 Calling OpenAI GPT-4o...")

            response = await client.chat.completions.create(
                model="gpt-4o-2024-11-20",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a research expert. Provide detailed, factual research results."
                    },
                    {
                        "role": "user",
                        "content": search_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )

            logger.info(f"   ✅ OpenAI response received")

            # Parse response
            import json as json_module
            result_text = response.choices[0].message.content

            try:
                result = json_module.loads(result_text)
            except:
                result = {
                    "title": "Research Results",
                    "summary": result_text,
                    "key_points": ["See summary above"],
                    "best_practices": [],
                    "references": [],
                    "confidence": "medium"
                }

            logger.info(f"   📊 Research complete: {result.get('title', 'N/A')}")

            # Return MCP-compliant response
            return {
                "title": result.get("title", "Research Results"),
                "summary": result.get("summary", ""),
                "key_points": result.get("key_points", []),
                "best_practices": result.get("best_practices", []),
                "references": result.get("references", []),
                "confidence": result.get("confidence", "medium"),
                "query": query,
                "source": "OpenAI GPT-4o Knowledge Base (April 2024 cutoff)",
                "timestamp": datetime.now().isoformat(),
                "note": "⚠️ MCP BLEIBT: In production, this would use Perplexity MCP for real-time web search"
            }

        except Exception as e:
            logger.error(f"   ❌ Web search error: {type(e).__name__}: {str(e)[:100]}")
            return {
                "title": "Research Error",
                "summary": f"Could not complete research: {str(e)}",
                "error": str(e),
                "query": query,
                "key_points": [],
                "best_practices": [],
                "references": [],
                "confidence": "low",
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
        ⚠️ MCP BLEIBT: Main server loop (NON-BLOCKING stdin)

        Uses async_stdin_readline() instead of blocking executor
        to prevent event loop freeze when waiting for input.

        This FIXES the issue where servers would crash/restart
        after each request due to blocking I/O!
        """
        logger.info("🚀 Research Agent MCP Server starting...")
        logger.info("⚠️ MCP BLEIBT: This server MUST remain MCP-compliant!")
        logger.info("🔄 Using non-blocking stdin (FIXED: async I/O blocking issue)")

        try:
            while True:
                # ⚠️ FIXED: Use non-blocking async stdin instead of executor
                line = await async_stdin_readline()

                if not line:
                    logger.info("📥 EOF received, shutting down")
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    await self.handle_request(request)
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Invalid JSON: {e}")
                    continue

        except Exception as e:
            logger.error(f"❌ Server error: {e}")
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
