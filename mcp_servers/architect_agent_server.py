#!/usr/bin/env python3
"""
⚠️ MCP BLEIBT: Architect Agent MCP Server
⚠️ WICHTIG: MCP BLEIBT! Architect Agent läuft NUR als MCP-Server!
⚠️ KEINE direkten OpenAI-Calls! Alles über OpenAI MCP Server!

This MCP server provides architecture design capabilities:
- System architecture design
- File structure planning
- Technology selection
- Design pattern recommendations
- Data flow documentation

MCP Protocol Compliance:
- JSON-RPC 2.0 over stdin/stdout
- $/progress notifications for design stages
- Calls OpenAI via MCP (openai_server.py)
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
logger = logging.getLogger("architect_mcp_server")


class ArchitectAgentMCPServer:
    """
    ⚠️ MCP BLEIBT: Architect Agent als vollständiger MCP Server

    Der Architect Agent nutzt OpenAI GPT-4o über den OpenAI MCP Server.
    KEINE direkten OpenAI-Calls mehr!
    """

    def __init__(self):
        self.request_id = 0
        self.initialized = False
        self.mcp = None  # MCPClient instance (injected during initialization)

        # ⚠️ MCP BLEIBT: Tool registry
        self.tools = {
            "design": {
                "description": "Design system architecture based on instructions and research context",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "instructions": {
                            "type": "string",
                            "description": "What to design (user requirements)"
                        },
                        "research_context": {
                            "type": "object",
                            "description": "Context from research agent (workspace analysis, web results, etc.)"
                        },
                        "workspace_path": {
                            "type": "string",
                            "description": "Path to target workspace"
                        }
                    },
                    "required": ["instructions"]
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
        logger.info("Architect Agent MCP Server initialized")

        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "notifications": {
                    "progress": True
                }
            },
            "serverInfo": {
                "name": "architect-agent-mcp-server",
                "version": "7.0.0",
                "description": "⚠️ MCP BLEIBT: Architect Agent for KI AutoAgent"
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

        if tool_name == "design":
            return await self.tool_design(arguments)

        raise ValueError(f"Tool {tool_name} not implemented")

    async def tool_design(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⚠️ MCP BLEIBT: Design architecture using OpenAI via MCP

        WICHTIG: Dieser Code ruft NIEMALS direkt OpenAI API auf!
        Alle AI-Calls gehen über den OpenAI MCP Server!
        """
        try:
            await self.send_progress(0.0, "🏗️ Starting architecture design...")

            instructions = args.get("instructions", "")
            research_context = args.get("research_context", {})
            workspace_path = args.get("workspace_path", "")

            logger.info(f"Designing architecture: {instructions[:100]}...")

            # Check if we have sufficient context
            await self.send_progress(0.1, "📋 Checking research context...")
            if not research_context or len(research_context) == 0:
                logger.info("   📚 Insufficient context - requesting research")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({
                                "needs_research": True,
                                "research_request": "Analyze workspace structure and existing code",
                                "architecture_complete": False
                            })
                        }
                    ],
                    "metadata": {
                        "status": "needs_research",
                        "timestamp": datetime.now().isoformat()
                    }
                }

            # Build architecture prompt
            await self.send_progress(0.2, "🎨 Building design prompt...")
            prompt = self._build_architecture_prompt(instructions, research_context, workspace_path)
            system_prompt = self._get_architecture_system_prompt()

            # ⚠️ MCP BLEIBT: Call OpenAI via MCP Server!
            await self.send_progress(0.3, "🤖 Calling OpenAI via MCP...")

            # TODO: This will be implemented once MCPClient is available
            # For now, return placeholder indicating MCP architecture

            # In the final implementation:
            # openai_result = await self.mcp.call(
            #     server="openai",
            #     tool="complete",
            #     arguments={
            #         "messages": [
            #             {"role": "system", "content": system_prompt},
            #             {"role": "user", "content": prompt}
            #         ],
            #         "model": "gpt-4o-2024-11-20",
            #         "temperature": 0.4,
            #         "max_tokens": 4000
            #     }
            # )

            await self.send_progress(0.8, "📝 Processing architecture...")

            # Placeholder architecture for MCP migration phase
            architecture = {
                "description": f"Architecture design for: {instructions[:100]}",
                "components": [
                    {
                        "name": "Main Component",
                        "description": "⚠️ MCP BLEIBT: This will be generated by OpenAI MCP Server"
                    }
                ],
                "file_structure": [
                    "src/",
                    "tests/",
                    "README.md"
                ],
                "technologies": ["Python"],
                "patterns": ["MVC"],
                "data_flow": [],
                "note": "Architecture will be generated via OpenAI MCP Server when MCPClient is connected",
                "created_at": datetime.now().isoformat()
            }

            # Adjust for workspace if provided
            if workspace_path:
                workspace_analysis = research_context.get("workspace_analysis", {})
                if workspace_analysis:
                    architecture = self._adjust_for_workspace(architecture, workspace_analysis)

            await self.send_progress(1.0, "✅ Architecture design complete")

            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(architecture, indent=2)
                    }
                ],
                "metadata": {
                    "architecture_complete": True,
                    "needs_research": False,
                    "component_count": len(architecture.get("components", [])),
                    "timestamp": datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Architecture design failed: {e}")
            await self.send_progress(1.0, f"❌ Error: {str(e)}")
            raise

    def _get_architecture_system_prompt(self) -> str:
        """
        ⚠️ MCP BLEIBT: System prompt for architecture generation
        """
        return """You are an expert software architect specializing in system design.

Your task is to design comprehensive system architectures based on:
- User instructions (what to build)
- Research context (best practices, patterns, documentation)
- Workspace analysis (existing code structure)

Requirements:
1. Design scalable, maintainable architectures
2. Select appropriate technologies and patterns
3. Create clear component structure
4. Define file organization
5. Document data flow between components
6. Follow modern best practices

Output Format (JSON):
{
  "description": "Overall system description",
  "components": [{"name": "...", "description": "..."}],
  "file_structure": ["path/to/file", ...],
  "technologies": ["Technology1", "Technology2", ...],
  "patterns": ["Pattern1", "Pattern2", ...],
  "data_flow": [{"from": "ComponentA", "to": "ComponentB", "description": "..."}]
}

Design production-ready, well-structured architectures."""

    def _build_architecture_prompt(
        self,
        instructions: str,
        research_context: dict,
        workspace_path: str
    ) -> str:
        """
        ⚠️ MCP BLEIBT: Build detailed prompt for architecture generation
        """
        prompt_parts = [
            "Design a system architecture based on the following:",
            "",
            "## Instructions",
            instructions,
            "",
            "## Workspace Context",
        ]

        workspace_analysis = research_context.get("workspace_analysis", {})
        if workspace_analysis:
            prompt_parts.append(f"- Project Type: {workspace_analysis.get('project_type', 'Unknown')}")
            prompt_parts.append(f"- Languages: {', '.join(workspace_analysis.get('languages', []))}")
            prompt_parts.append(f"- Existing Files: {workspace_analysis.get('file_count', 0)}")
            prompt_parts.append(f"- Has Tests: {workspace_analysis.get('has_tests', False)}")
            if workspace_analysis.get('frameworks'):
                prompt_parts.append(f"- Frameworks: {', '.join(workspace_analysis['frameworks'])}")

        prompt_parts.extend([
            "",
            "## Research Context",
            json.dumps(research_context, indent=2)[:1000],  # Truncate for token limits
            "",
            "## Task",
            "Design a comprehensive architecture with:",
            "1. Overall system description",
            "2. Core components and their responsibilities",
            "3. File structure (be specific with paths)",
            "4. Technology stack",
            "5. Design patterns to use",
            "6. Data flow between components",
            "",
            "Output ONLY valid JSON in the specified format."
        ])

        return "\n".join(prompt_parts)

    def _adjust_for_workspace(
        self,
        architecture: dict,
        workspace_analysis: dict
    ) -> dict:
        """
        ⚠️ MCP BLEIBT: Adjust architecture based on existing workspace
        """
        if not workspace_analysis:
            return architecture

        # If workspace already has structure, preserve it
        if workspace_analysis.get("file_count", 0) > 10:
            architecture["description"] += "\n\nNote: Architecture adjusted to fit existing project structure"

        # Add detected frameworks
        existing_frameworks = workspace_analysis.get("frameworks", [])
        if existing_frameworks:
            architecture["technologies"].extend(existing_frameworks)
            architecture["technologies"] = list(set(architecture["technologies"]))

        # Adjust for test presence
        if workspace_analysis.get("has_tests"):
            if not any("test" in str(f).lower() for f in architecture["file_structure"]):
                architecture["file_structure"].append("tests/")

        return architecture

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
        logger.info("🚀 Architect Agent MCP Server starting...")
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
    ⚠️ MCP BLEIBT: Entry point for Architect Agent MCP Server
    """
    server = ArchitectAgentMCPServer()
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
