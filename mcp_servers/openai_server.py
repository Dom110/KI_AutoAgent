#!/usr/bin/env python3
"""
⚠️ MCP BLEIBT: OpenAI MCP Server - Wrapper für OpenAI API via LangChain
⚠️ WICHTIG: MCP BLEIBT! Keine direkten OpenAI-Calls außerhalb MCP!

This MCP server provides OpenAI GPT-4o access via standardized JSON-RPC protocol.
Used by: Architect Agent, Planning processes

MCP Protocol Compliance:
- JSON-RPC 2.0 over stdin/stdout
- $/progress notifications for streaming updates
- Dynamic tool discovery via tools/list
- Error handling with JSON-RPC error codes

Author: KI AutoAgent v7.0
Date: 2025-10-30
"""

import sys
import json
import asyncio
import logging
from typing import Any, Dict, Optional
from datetime import datetime

# ⚠️ MCP BLEIBT: LangChain für OpenAI Integration
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Configure logging to stderr (stdout is for JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("openai_mcp_server")


class OpenAIMCPServer:
    """
    ⚠️ MCP BLEIBT: OpenAI MCP Server Implementation

    Provides OpenAI API access via MCP protocol with:
    - Dynamic model selection (gpt-4o, gpt-4o-mini)
    - Streaming progress notifications
    - System message support
    - Temperature/max_tokens configuration
    """

    def __init__(self):
        self.request_id = 0
        self.initialized = False

        # ⚠️ MCP BLEIBT: Supported tools registry
        self.tools = {
            "complete": {
                "description": "Generate completion using OpenAI GPT-4o",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "description": "Array of message objects with 'role' and 'content'",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "role": {"type": "string", "enum": ["system", "user", "assistant"]},
                                    "content": {"type": "string"}
                                },
                                "required": ["role", "content"]
                            }
                        },
                        "model": {
                            "type": "string",
                            "description": "OpenAI model to use",
                            "enum": ["gpt-4o-2024-11-20", "gpt-4o-mini"],
                            "default": "gpt-4o-2024-11-20"
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Temperature (0.0-1.0)",
                            "default": 0.0
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens to generate",
                            "default": 8000
                        }
                    },
                    "required": ["messages"]
                }
            }
        }

    async def send_progress(self, progress: float, message: str):
        """
        ⚠️ MCP BLEIBT: Send $/progress notification

        Args:
            progress: Progress value 0.0-1.0
            message: Human-readable progress message
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

        Returns server capabilities and metadata.
        """
        self.initialized = True
        logger.info("OpenAI MCP Server initialized")

        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},  # We support tools/list and tools/call
                "notifications": {
                    "progress": True  # We send $/progress notifications
                }
            },
            "serverInfo": {
                "name": "openai-mcp-server",
                "version": "7.0.0",
                "description": "⚠️ MCP BLEIBT: OpenAI API wrapper for KI AutoAgent"
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

        if tool_name == "complete":
            return await self.tool_complete(arguments)

        raise ValueError(f"Tool {tool_name} not implemented")

    async def tool_complete(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⚠️ MCP BLEIBT: Generate OpenAI completion

        Args:
            args: Contains messages, model, temperature, max_tokens

        Returns:
            Result with content and usage statistics
        """
        try:
            await self.send_progress(0.0, "🧠 Initializing OpenAI...")

            messages_data = args.get("messages", [])
            model = args.get("model", "gpt-4o-2024-11-20")
            temperature = args.get("temperature", 0.0)
            max_tokens = args.get("max_tokens", 8000)

            logger.info(f"OpenAI complete: model={model}, messages={len(messages_data)}")

            # ⚠️ MCP BLEIBT: OpenAI via LangChain
            await self.send_progress(0.2, f"🔧 Creating {model} client...")
            llm = ChatOpenAI(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Convert messages to LangChain format
            await self.send_progress(0.3, "📝 Preparing messages...")
            lc_messages = []
            for msg in messages_data:
                role = msg.get("role")
                content = msg.get("content")

                if role == "system":
                    lc_messages.append(SystemMessage(content=content))
                elif role == "user":
                    lc_messages.append(HumanMessage(content=content))
                else:
                    logger.warning(f"Skipping message with role: {role}")

            # Generate completion
            await self.send_progress(0.5, "⚡ Generating completion...")
            response = await llm.ainvoke(lc_messages)

            await self.send_progress(0.9, "✅ Processing response...")

            result = {
                "content": [
                    {
                        "type": "text",
                        "text": response.content
                    }
                ],
                "metadata": {
                    "model": model,
                    "temperature": temperature,
                    "message_count": len(messages_data),
                    "response_length": len(response.content)
                }
            }

            await self.send_progress(1.0, "✅ OpenAI complete")
            logger.info(f"OpenAI completion successful: {len(response.content)} chars")

            return result

        except Exception as e:
            logger.error(f"OpenAI completion failed: {e}")
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
                    "code": -32603,  # Internal error
                    "message": str(e)
                }
            }
            await self.send_message(error_response)

    async def run(self):
        """
        ⚠️ MCP BLEIBT: Main server loop - read from stdin, write to stdout
        """
        logger.info("🚀 OpenAI MCP Server starting...")
        logger.info("⚠️ MCP BLEIBT: This server MUST remain MCP-compliant!")

        try:
            # Read JSON-RPC requests from stdin line by line
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
    ⚠️ MCP BLEIBT: Entry point for OpenAI MCP Server
    """
    server = OpenAIMCPServer()
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
