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
import os
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

# ⚠️ FIX: Add project_root to path (not backend!) so we can import backend.utils
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
env_path = Path.home() / ".ki_autoagent" / "config" / ".env"
if env_path.exists():
    load_dotenv(env_path)

# ⚠️ MCP BLEIBT: LangChain für OpenAI Integration
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Import API validator (decentralized validation)
# ⚠️ FIX: MCP servers run from project root, so import from backend.utils!
from backend.utils.api_validator import validate_openai_key

# ⚠️ LOGGING: Configure logging to file (stdout is for JSON-RPC)
# All log messages (info, debug, warning, error) go to /tmp/mcp_openai.log
log_file = "/tmp/mcp_openai.log"
logging.basicConfig(
    level=logging.DEBUG,  # Log everything!
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=log_file,
    filemode='a'  # Append mode
)
logger = logging.getLogger("openai_mcp_server")
logger.info(f"=" * 80)
logger.info(f"🚀 OpenAI MCP Server starting at {datetime.now()}")
logger.info(f"=" * 80)


# ⚠️ MCP BLEIBT: INLINE Helper for non-blocking stdin (FIX #2 V2: No Timeout)
async def async_stdin_readline() -> str:
    """
    🔧 FIX #2 V2: Non-blocking stdin readline WITHOUT arbitrary timeout
    
    Solves the asyncio blocking I/O issue while avoiding 300s timeout problems.
    
    Key improvements:
    - NO timeout → Operations complete fully, no interruptions at 300s
    - EOF detection → Natural shutdown when parent closes connection
    - Signal handling ready → Can add graceful shutdown handlers
    - Scales → Works for any operation duration
    
    How it works:
    - Uses run_in_executor() to keep event loop responsive
    - Waits indefinitely for stdin data or EOF from parent
    - Parent process controls server lifetime via connection
    - Signal handlers provide additional graceful shutdown control
    
    Returns:
        str: Line read from stdin, or empty string on EOF
        
    Logging:
        [stdin_v2] - All stdin operations prefixed with this tag
    """
    loop = asyncio.get_event_loop()
    
    def _read():
        """Blocking read - runs in executor thread, non-blocking to event loop"""
        try:
            logger.debug("[stdin_v2] sys.stdin.readline() called (blocking in executor)")
            line = sys.stdin.readline()
            
            if line:
                logger.debug(f"[stdin_v2] Read {len(line)} bytes")
            else:
                logger.info("[stdin_v2] EOF detected (empty line from stdin)")
            
            return line
            
        except Exception as e:
            logger.error(f"[stdin_v2] Read error: {type(e).__name__}: {e}")
            return ""
    
    try:
        logger.debug("[stdin_v2] Waiting for input (NO timeout - waits for EOF or data)")
        
        # KEY CHANGE: NO timeout!
        # The old code used: await asyncio.wait_for(..., timeout=300.0)
        # This interrupted operations after 300s arbitrarily.
        # New approach: Just await the executor directly.
        # Server lifetime is controlled by parent process closing stdin.
        result = await loop.run_in_executor(None, _read)
        
        return result
        
    except Exception as e:
        logger.error(f"[stdin_v2] Unexpected error: {type(e).__name__}: {e}")
        return ""


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
        ⚠️ FIX #2 V2: Uses async_stdin_readline() WITHOUT timeout (no blocking I/O)
        """
        logger.info("🚀 OpenAI MCP Server starting...")
        logger.info("⚠️ MCP BLEIBT: This server MUST remain MCP-compliant!")
        logger.info("📡 FIX #2 V2: Using async_stdin_readline() (NO timeout - waits for EOF)")

        try:
            request_count = 0
            while True:
                logger.debug(f"📥 [loop] Waiting for request #{request_count + 1}...")
                line = await async_stdin_readline()

                if not line:
                    logger.info("ℹ️ [loop] EOF detected, shutting down (no timeout)")
                    break

                line = line.strip()
                if not line:
                    logger.debug(f"📥 [loop] Empty line, skipping")
                    continue

                request_count += 1
                logger.debug(f"📥 [loop] Request #{request_count}: {line[:80]}...")

                try:
                    request = json.loads(line)
                    logger.info(f"📊 [request] ID={request.get('id')}, Method={request.get('method')}")
                    await self.handle_request(request)
                except json.JSONDecodeError as e:
                    logger.error(f"❌ [json] Parse error on request #{request_count}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"❌ [handler] Unexpected error: {type(e).__name__}: {e}")
                    continue

        except Exception as e:
            logger.error(f"❌ [server] Fatal error: {type(e).__name__}: {e}")
            raise


async def main():
    """
    ⚠️ MCP BLEIBT: Entry point for OpenAI MCP Server
    
    Validates API keys before starting the server.
    """
    # ✅ Validate OpenAI API key first (exit if invalid)
    logger.info("🔑 Validating OpenAI API key...")
    validate_openai_key(exit_on_fail=True)
    logger.info("✅ OpenAI MCP Server starting...")
    
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
