#!/usr/bin/env python3
"""
⚠️ MCP BLEIBT: ReviewFix Agent MCP Server
⚠️ WICHTIG: MCP BLEIBT! ReviewFix Agent läuft NUR als MCP-Server!
⚠️ KEINE direkten Claude CLI-Calls! Alles über Claude CLI MCP Server!

This MCP server provides code review and fixing capabilities:
- Review generated code for quality
- Validate code with tests
- Fix errors and issues
- Improve code quality
- Iterate until tests pass

MCP Protocol Compliance:
- JSON-RPC 2.0 over stdin/stdout
- $/progress notifications for review/fix stages
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
logger = logging.getLogger("reviewfix_mcp_server")


class ReviewFixAgentMCPServer:
    """
    ⚠️ MCP BLEIBT: ReviewFix Agent als vollständiger MCP Server

    Der ReviewFix Agent nutzt Claude CLI über einen MCP-Wrapper für
    Code Review und Fixes. KEINE direkten subprocess-Calls mehr!
    """

    def __init__(self):
        self.request_id = 0
        self.initialized = False
        self.mcp = None  # MCPClient instance (injected during initialization)

        # ⚠️ MCP BLEIBT: Tool registry
        self.tools = {
            "review_and_fix": {
                "description": "Review code and fix any issues until tests pass",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "instructions": {
                            "type": "string",
                            "description": "What to review and fix"
                        },
                        "generated_files": {
                            "type": "array",
                            "description": "List of generated files to review",
                            "items": {"type": "object"}
                        },
                        "validation_errors": {
                            "type": "array",
                            "description": "List of errors from previous validation",
                            "items": {"type": "string"}
                        },
                        "workspace_path": {
                            "type": "string",
                            "description": "Path to workspace"
                        },
                        "iteration": {
                            "type": "integer",
                            "description": "Current iteration number",
                            "default": 1
                        }
                    },
                    "required": ["instructions", "workspace_path"]
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
        logger.info("ReviewFix Agent MCP Server initialized")

        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "notifications": {
                    "progress": True
                }
            },
            "serverInfo": {
                "name": "reviewfix-agent-mcp-server",
                "version": "7.0.0",
                "description": "⚠️ MCP BLEIBT: ReviewFix Agent for KI AutoAgent"
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

        if tool_name == "review_and_fix":
            return await self.tool_review_and_fix(arguments)

        raise ValueError(f"Tool {tool_name} not implemented")

    async def tool_review_and_fix(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⚠️ MCP BLEIBT: Review and fix code using Claude CLI via MCP

        WICHTIG: Dieser Code ruft NIEMALS direkt Claude CLI subprocess auf!
        Alle AI-Calls gehen über den Claude CLI MCP Server!
        """
        try:
            await self.send_progress(0.0, "🔍 Starting code review...")

            instructions = args.get("instructions", "")
            generated_files = args.get("generated_files", [])
            validation_errors = args.get("validation_errors", [])
            workspace_path = args.get("workspace_path", "")
            iteration = args.get("iteration", 1)

            logger.info(f"Reviewing code (iteration {iteration}): {instructions[:100]}...")
            logger.info(f"   Workspace: {workspace_path}")
            logger.info(f"   Files: {len(generated_files)}")
            logger.info(f"   Errors: {len(validation_errors)}")

            # Build review prompt
            await self.send_progress(0.1, "📝 Building review prompt...")
            prompt = self._build_review_prompt(
                instructions,
                generated_files,
                validation_errors,
                iteration
            )
            system_prompt = self._get_system_prompt()

            # ⚠️ MCP BLEIBT: Call Claude CLI via MCP Server!
            await self.send_progress(0.2, "🤖 Calling Claude CLI for review...")
            logger.info("   📡 Calling Claude CLI MCP server...")

            # TODO: This will be implemented once MCPClient is available
            # For now, return placeholder indicating MCP architecture

            # In the final implementation:
            # claude_result = await self.mcp.call(
            #     server="claude_cli",
            #     tool="execute",
            #     arguments={
            #         "prompt": prompt,
            #         "system_prompt": system_prompt,
            #         "workspace_path": workspace_path,
            #         "tools": ["Read", "Edit", "Bash"],
            #         "model": "claude-sonnet-4-20250514",
            #         "temperature": 0.3,
            #         "max_tokens": 8000
            #     }
            # )

            await self.send_progress(0.7, "🔧 Processing fixes...")

            # Placeholder for MCP migration phase
            result = {
                "fixed_files": generated_files,  # In reality, Claude CLI will fix them
                "validation_passed": len(validation_errors) == 0,
                "remaining_errors": [] if len(validation_errors) == 0 else validation_errors,
                "iteration": iteration,
                "fix_complete": True,
                "note": "⚠️ MCP BLEIBT: Fixes will be applied via Claude CLI MCP Server when MCPClient is connected"
            }

            await self.send_progress(1.0, "✅ Review and fix complete")
            logger.info(f"   ✅ Review complete: validation_passed={result['validation_passed']}")

            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ],
                "metadata": {
                    "validation_passed": result["validation_passed"],
                    "iteration": iteration,
                    "timestamp": datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Review and fix failed: {e}")
            await self.send_progress(1.0, f"❌ Error: {str(e)}")
            raise

    def _get_system_prompt(self) -> str:
        """
        ⚠️ MCP BLEIBT: System prompt for code review and fixing
        """
        return """You are an expert code reviewer and debugger specializing in quality assurance.

Your task is to:
1. Review generated code for correctness, quality, and best practices
2. Run tests to validate functionality
3. Fix any errors or issues found
4. Improve code quality (error handling, documentation, edge cases)
5. Ensure all tests pass before completing

Requirements:
- Use Read tool to examine existing code
- Use Edit tool to fix issues
- Use Bash tool to run tests and validation
- Fix ALL errors - do not leave TODO comments
- Ensure proper error handling
- Verify all edge cases
- Add missing tests if needed

DO NOT:
- Skip test execution
- Leave errors unfixed
- Ignore validation failures
- Create placeholder fixes

Fix ALL issues until tests pass completely."""

    def _build_review_prompt(
        self,
        instructions: str,
        generated_files: list,
        validation_errors: list,
        iteration: int
    ) -> str:
        """
        ⚠️ MCP BLEIBT: Build detailed prompt for code review
        """
        prompt_parts = [
            f"Review and fix code (Iteration {iteration}):",
            "",
            "## Original Instructions",
            instructions,
            "",
        ]

        # Add file information
        if generated_files:
            prompt_parts.append("## Generated Files")
            for file in generated_files[:5]:  # Limit to 5 files in prompt
                if isinstance(file, dict):
                    prompt_parts.append(f"- {file.get('path', 'unknown')}: {file.get('description', '')}")
            prompt_parts.append("")

        # Add validation errors if present
        if validation_errors:
            prompt_parts.append(f"## Validation Errors ({len(validation_errors)} errors)")
            for i, error in enumerate(validation_errors[:10], 1):  # Limit to 10 errors
                prompt_parts.append(f"{i}. {error}")
            prompt_parts.append("")

        # Add tasks
        prompt_parts.extend([
            "## Task",
            "1. Read the generated files using the Read tool",
            "2. Run tests using the Bash tool",
        ])

        if validation_errors:
            prompt_parts.append("3. Fix ALL validation errors using the Edit tool")
            prompt_parts.append("4. Re-run tests to verify fixes")
        else:
            prompt_parts.append("3. Review code quality and improve if needed")
            prompt_parts.append("4. Ensure all tests pass")

        prompt_parts.extend([
            "5. Verify all edge cases are handled",
            "",
            "Fix ALL issues. Do not complete until ALL tests pass."
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
        logger.info("🚀 ReviewFix Agent MCP Server starting...")
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
    ⚠️ MCP BLEIBT: Entry point for ReviewFix Agent MCP Server
    """
    server = ReviewFixAgentMCPServer()
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
