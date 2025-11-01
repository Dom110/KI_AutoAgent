#!/usr/bin/env python3
"""
⚠️ MCP BLEIBT: Responder Agent MCP Server
⚠️ WICHTIG: MCP BLEIBT! Responder Agent läuft NUR als MCP-Server!

This MCP server provides user response formatting:
- Format results for user presentation
- Create markdown responses
- Add emojis and formatting
- Handle success/error messages
- Simple formatting logic (NO AI needed)

MCP Protocol Compliance:
- JSON-RPC 2.0 over stdin/stdout
- $/progress notifications
- Dynamic tool discovery
- NO AI calls (pure formatting logic)

Author: KI AutoAgent v7.0
Date: 2025-10-30
"""

import sys
import json
import asyncio
import logging
from typing import Any, Dict, Optional
from datetime import datetime

# Configure logging to stderr (stdout is for JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("responder_mcp_server")


class ResponderAgentMCPServer:
    """
    ⚠️ MCP BLEIBT: Responder Agent als vollständiger MCP Server

    Der Responder Agent ist ein einfacher Formatter ohne AI.
    Trotzdem bleibt er ein MCP Server für konsistente Architektur!
    """

    def __init__(self):
        self.request_id = 0
        self.initialized = False

        # ⚠️ MCP BLEIBT: Tool registry
        self.tools = {
            "format_response": {
                "description": "Format results for user presentation with markdown and emojis",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_result": {
                            "type": "object",
                            "description": "Complete workflow result from supervisor"
                        },
                        "status": {
                            "type": "string",
                            "description": "Workflow status (success, error, partial)",
                            "enum": ["success", "error", "partial"]
                        }
                    },
                    "required": ["workflow_result", "status"]
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
        logger.info("Responder Agent MCP Server initialized")

        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "notifications": {
                    "progress": True
                }
            },
            "serverInfo": {
                "name": "responder-agent-mcp-server",
                "version": "7.0.0",
                "description": "⚠️ MCP BLEIBT: Responder Agent for KI AutoAgent"
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

        if tool_name == "format_response":
            return await self.tool_format_response(arguments)

        raise ValueError(f"Tool {tool_name} not implemented")

    async def tool_format_response(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⚠️ MCP BLEIBT: Format response for user

        WICHTIG: Dies ist reine Formatierungslogik - KEINE AI-Calls!
        Trotzdem ist es ein MCP Tool für konsistente Architektur.
        """
        try:
            await self.send_progress(0.0, "📝 Formatting response...")

            workflow_result = args.get("workflow_result", {})
            status = args.get("status", "success")

            logger.info(f"Formatting response: status={status}")

            # Build formatted response
            await self.send_progress(0.3, "🎨 Building markdown...")
            response_parts = []

            # Header based on status
            if status == "success":
                response_parts.append("# ✅ Task Completed Successfully\n")
            elif status == "error":
                response_parts.append("# ❌ Task Failed\n")
            else:
                response_parts.append("# ⚠️ Task Partially Completed\n")

            # Add summary
            if "summary" in workflow_result:
                response_parts.append(f"**Summary:** {workflow_result['summary']}\n")

            # Add generated files if present
            if "generated_files" in workflow_result:
                files = workflow_result["generated_files"]
                response_parts.append(f"\n## 📁 Generated Files ({len(files)})\n")
                for file in files[:10]:  # Limit to 10 files
                    if isinstance(file, dict):
                        path = file.get("path", "unknown")
                        desc = file.get("description", "")
                        response_parts.append(f"- `{path}` - {desc}")
                response_parts.append("")

            # Add architecture if present
            if "architecture" in workflow_result:
                arch = workflow_result["architecture"]
                response_parts.append("\n## 🏗️ Architecture\n")
                if "description" in arch:
                    response_parts.append(arch["description"])
                if "components" in arch:
                    response_parts.append(f"\n**Components:** {len(arch['components'])}")
                if "technologies" in arch:
                    response_parts.append(f"\n**Technologies:** {', '.join(arch['technologies'][:5])}")
                response_parts.append("")

            # Add validation results if present
            if "validation_passed" in workflow_result:
                passed = workflow_result["validation_passed"]
                if passed:
                    response_parts.append("\n## ✅ Validation\n")
                    response_parts.append("All tests passed successfully!\n")
                else:
                    response_parts.append("\n## ❌ Validation\n")
                    errors = workflow_result.get("validation_errors", [])
                    response_parts.append(f"Found {len(errors)} validation errors:\n")
                    for error in errors[:5]:  # Limit to 5 errors
                        response_parts.append(f"- {error}")
                    response_parts.append("")

            # Add errors if present
            if "error" in workflow_result:
                response_parts.append("\n## ❌ Error Details\n")
                response_parts.append(f"```\n{workflow_result['error']}\n```\n")

            # Add timestamp
            timestamp = workflow_result.get("timestamp", datetime.now().isoformat())
            response_parts.append(f"\n---\n*Completed at: {timestamp}*")

            await self.send_progress(0.8, "📤 Preparing response...")

            formatted_response = "\n".join(response_parts)

            await self.send_progress(1.0, "✅ Response formatted")

            return {
                "content": [
                    {
                        "type": "text",
                        "text": formatted_response
                    }
                ],
                "metadata": {
                    "status": status,
                    "response_length": len(formatted_response),
                    "timestamp": datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Response formatting failed: {e}")
            await self.send_progress(1.0, f"❌ Error: {str(e)}")
            raise

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
        logger.info("🚀 Responder Agent MCP Server starting...")
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
    ⚠️ MCP BLEIBT: Entry point for Responder Agent MCP Server
    """
    server = ResponderAgentMCPServer()
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
