#!/usr/bin/env python3
"""
⚠️ MCP BLEIBT: Codesmith Agent MCP Server
⚠️ WICHTIG: MCP BLEIBT! Codesmith Agent läuft NUR als MCP-Server!
⚠️ KEINE direkten Claude CLI-Calls! Alles über Claude CLI MCP Server!

This MCP server provides code generation capabilities:
- Generate production-quality code from architecture
- Implement business logic
- Create tests
- Fix bugs
- Use modern best practices

MCP Protocol Compliance:
- JSON-RPC 2.0 over stdin/stdout
- $/progress notifications for generation stages
- Calls Claude CLI via MCP wrapper
- Dynamic tool discovery

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
logger = logging.getLogger("codesmith_mcp_server")


class CodesmithAgentMCPServer:
    """
    ⚠️ MCP BLEIBT: Codesmith Agent als vollständiger MCP Server

    Der Codesmith Agent nutzt Claude CLI über einen MCP-Wrapper.
    KEINE direkten subprocess-Calls mehr!
    """

    def __init__(self):
        self.request_id = 0
        self.initialized = False
        self.mcp = None  # MCPClient instance (injected during initialization)

        # ⚠️ MCP BLEIBT: Tool registry
        self.tools = {
            "generate": {
                "description": "Generate production-quality code from architecture design",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "instructions": {
                            "type": "string",
                            "description": "What to implement (user requirements)"
                        },
                        "architecture": {
                            "type": "object",
                            "description": "System design from architect agent"
                        },
                        "research_context": {
                            "type": "object",
                            "description": "Context from research agent"
                        },
                        "workspace_path": {
                            "type": "string",
                            "description": "Path to target workspace"
                        }
                    },
                    "required": ["instructions", "architecture", "workspace_path"]
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
        logger.info("Codesmith Agent MCP Server initialized")

        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "notifications": {
                    "progress": True
                }
            },
            "serverInfo": {
                "name": "codesmith-agent-mcp-server",
                "version": "7.0.0",
                "description": "⚠️ MCP BLEIBT: Codesmith Agent for KI AutoAgent"
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

        if tool_name == "generate":
            return await self.tool_generate(arguments)

        raise ValueError(f"Tool {tool_name} not implemented")

    async def tool_generate(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⚠️ MCP BLEIBT: Generate code using Claude CLI via MCP

        WICHTIG: Dieser Code ruft NIEMALS direkt Claude CLI subprocess auf!
        Alle AI-Calls gehen über den Claude CLI MCP Server!
        """
        try:
            await self.send_progress(0.0, "🔨 Starting code generation...")

            instructions = args.get("instructions", "")
            architecture = args.get("architecture", {})
            research_context = args.get("research_context", {})
            workspace_path = args.get("workspace_path", "")

            logger.info(f"Generating code: {instructions[:100]}...")
            logger.info(f"   Workspace: {workspace_path}")

            # Check if we need more research
            await self.send_progress(0.1, "📋 Checking prerequisites...")
            if not architecture:
                logger.info("   📚 Missing architecture - requesting research")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({
                                "needs_research": True,
                                "research_request": "Need architecture design before code generation",
                                "code_complete": False
                            })
                        }
                    ],
                    "metadata": {
                        "status": "needs_architecture",
                        "timestamp": datetime.now().isoformat()
                    }
                }

            # Build code generation prompt
            await self.send_progress(0.2, "📝 Building generation prompt...")
            prompt = self._build_code_generation_prompt(instructions, architecture)
            system_prompt = self._get_system_prompt()

            # ⚠️ MCP BLEIBT: Call Claude CLI via MCP Server!
            await self.send_progress(0.3, "🤖 Calling Claude CLI via MCP...")
            logger.info("   📡 Calling Claude CLI MCP server...")

            # ⚠️ MCP BLEIBT: Import MCPManager to call claude_cli server
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from backend.utils.mcp_manager import get_mcp_manager

            # Get global MCP manager
            mcp = get_mcp_manager(workspace_path=workspace_path)

            # Ensure initialized
            if not mcp._initialized:
                await mcp.initialize()

            # ⚠️ MCP BLEIBT: Call Claude CLI via MCP!
            claude_result = await mcp.call(
                server="claude_cli",
                tool="claude_generate",
                arguments={
                    "prompt": prompt,
                    "system_prompt": system_prompt,
                    "workspace_path": workspace_path,
                    "agent_name": "codesmith",
                    "tools": ["Read", "Edit", "Bash"],
                    "temperature": 0.3,
                    "max_tokens": 8000,
                    "stream_events": True  # Enable event streaming!
                },
                timeout=300.0  # 5 minutes for code generation
            )

            await self.send_progress(0.8, "📦 Processing Claude CLI response...")

            # Extract result from Claude CLI MCP response
            claude_content = claude_result.get("content", [])
            if claude_content and len(claude_content) > 0:
                result_text = claude_content[0].get("text", "")
                logger.info(f"   Claude CLI returned: {len(result_text)} chars")

                # Parse JSON from result (claude_cli_server returns formatted result)
                try:
                    # Extract JSON from markdown code block
                    if "```json" in result_text:
                        json_str = result_text.split("```json\n")[1].split("\n```")[0]
                    else:
                        json_str = result_text

                    claude_data = json.loads(json_str)

                    # Extract files_created list
                    files_created = claude_data.get("files_created", [])

                    if files_created:
                        # Convert to our format
                        generated_files = [
                            {
                                "path": f.get("path", "unknown"),
                                "content": "", # Content is in workspace, not returned
                                "language": f.get("language", "text"),
                                "lines": 0,
                                "description": f"Generated via Claude CLI MCP",
                                "tool": "Edit"
                            }
                            for f in files_created
                        ]
                        logger.info(f"   ✅ {len(generated_files)} files created")
                    else:
                        # No files_created - use content
                        generated_files = [
                            {
                                "path": "output.txt",
                                "content": claude_data.get("content", ""),
                                "language": "text",
                                "lines": len(claude_data.get("content", "").split("\n")),
                                "description": "Claude CLI output",
                                "tool": "Edit"
                            }
                        ]

                except (json.JSONDecodeError, IndexError, KeyError) as e:
                    logger.warning(f"   Failed to parse Claude CLI result: {e}")
                    # Fallback
                    generated_files = [
                        {
                            "path": "generated.txt",
                            "content": result_text[:500],
                            "language": "text",
                            "lines": len(result_text.split("\n")),
                            "description": "Claude CLI output (raw)",
                            "tool": "Edit"
                        }
                    ]
            else:
                logger.warning("   No content from Claude CLI")
                generated_files = []

            await self.send_progress(1.0, "✅ Code generation complete")
            logger.info(f"   ✅ Generated {len(generated_files)} files")

            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "generated_files": generated_files,
                            "code_complete": True,
                            "needs_research": False
                        }, indent=2)
                    }
                ],
                "metadata": {
                    "file_count": len(generated_files),
                    "timestamp": datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            await self.send_progress(1.0, f"❌ Error: {str(e)}")
            raise

    def _get_system_prompt(self) -> str:
        """
        ⚠️ MCP BLEIBT: System prompt for code generation
        """
        return """You are an expert software engineer specializing in code generation.

Your task is to generate high-quality, production-ready code based on:
- Architecture design (component structure, technologies, file organization)
- Research context (best practices, patterns, documentation)
- Specific instructions from the supervisor

Requirements:
1. Follow the architecture design exactly
2. Use modern best practices for the technology stack
3. Include proper error handling and validation
4. Add comprehensive docstrings and comments
5. Generate tests alongside implementation
6. Use the Read, Edit, and Bash tools to create actual files in the workspace
7. Follow security best practices

DO NOT:
- Create placeholder or TODO code
- Skip error handling
- Ignore the architecture design
- Generate code without tests

Generate production-ready, fully functional code."""

    def _build_code_generation_prompt(
        self,
        instructions: str,
        architecture: dict
    ) -> str:
        """
        ⚠️ MCP BLEIBT: Build detailed prompt for code generation
        """
        prompt_parts = [
            "Generate code based on the following:",
            "",
            "## Instructions",
            instructions,
            "",
            "## Architecture",
        ]

        # Add architecture details
        if "description" in architecture:
            prompt_parts.append(f"Description: {architecture['description']}")

        if "components" in architecture:
            prompt_parts.append("\nComponents:")
            for comp in architecture["components"]:
                if isinstance(comp, dict):
                    prompt_parts.append(f"- {comp.get('name', 'Component')}: {comp.get('description', '')}")
                else:
                    prompt_parts.append(f"- {comp}")

        if "technologies" in architecture:
            prompt_parts.append(f"\nTechnologies: {', '.join(architecture['technologies'])}")

        if "file_structure" in architecture:
            prompt_parts.append("\nFile Structure:")
            for file in architecture["file_structure"]:
                prompt_parts.append(f"- {file}")

        prompt_parts.extend([
            "",
            "## Task",
            "1. Create the file structure using the Edit tool",
            "2. Implement each component with production-quality code",
            "3. Add comprehensive tests",
            "4. Ensure all error handling is in place",
            "5. Verify the code with basic syntax checks if possible",
            "",
            "Use the Read, Edit, and Bash tools to create actual files in the workspace."
        ])

        return "\n".join(prompt_parts)

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
        logger.info("🚀 Codesmith Agent MCP Server starting...")
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
    ⚠️ MCP BLEIBT: Entry point for Codesmith Agent MCP Server
    """
    server = CodesmithAgentMCPServer()
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
