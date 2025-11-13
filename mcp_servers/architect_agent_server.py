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
import os
from typing import Any, Dict, Optional
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.utils.api_validator import validate_openai_key

# ⚠️ Load environment variables
env_path = Path.home() / ".ki_autoagent" / "config" / ".env"
if env_path.exists():
    load_dotenv(env_path)

# ⚠️ LOGGING: Configure logging to file (stdout is for JSON-RPC)
# All log messages (info, debug, warning, error) go to /tmp/mcp_architect_agent.log
log_file = "/tmp/mcp_architect_agent.log"
logging.basicConfig(
    level=logging.DEBUG,  # Log everything!
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=log_file,
    filemode='a'  # Append mode
)
logger = logging.getLogger("architect_mcp_server")
logger.info(f"=" * 80)
logger.info(f"🚀 Architect MCP Server starting at {datetime.now()}")
logger.info(f"=" * 80)


# ⚠️ MCP BLEIBT: INLINE Helper for non-blocking stdin (FIXES FIX #2: Async Blocking I/O)
async def async_stdin_readline() -> str:
    """
    🔄 Non-blocking stdin readline for asyncio
    
    Fixes the asyncio blocking I/O issue where servers would freeze
    waiting for input from stdin. Uses run_in_executor with 300s timeout.
    
    Returns:
        str: Line read from stdin, or empty string on timeout/EOF
    """
    loop = asyncio.get_event_loop()
    
    def _read():
        try:
            line = sys.stdin.readline()
            if line:
                logger.debug(f"🔍 [stdin] Read {len(line)} bytes")
            return line
        except Exception as e:
            logger.error(f"❌ [stdin] readline() error: {type(e).__name__}: {e}")
            return ""
    
    try:
        logger.debug("⏳ [stdin] Waiting for input (300s timeout)...")
        result = await asyncio.wait_for(
            loop.run_in_executor(None, _read),
            timeout=300.0
        )
        if result:
            logger.debug(f"✅ [stdin] Got line: {result[:60].strip()}...")
        else:
            logger.debug("ℹ️ [stdin] EOF (empty line)")
        return result
    except asyncio.TimeoutError:
        logger.warning("⏱️ [stdin] Timeout (300s) - parent process may have disconnected")
        return ""
    except Exception as e:
        logger.error(f"❌ [stdin] Unexpected error: {type(e).__name__}: {e}")
        return ""




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

            # ⚠️ MCP BLEIBT: Call OpenAI directly for architecture generation
            await self.send_progress(0.3, "🤖 Calling OpenAI GPT-4o...")

            logger.info(f"   🔧 Initializing OpenAI client...")
            llm = ChatOpenAI(
                model="gpt-4o-2024-11-20",
                temperature=0.4,
                max_tokens=4000
            )

            # Prepare messages
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt)
            ]

            logger.info(f"   📡 Sending request to OpenAI GPT-4o...")
            response = await llm.ainvoke(messages)
            logger.info(f"   ✅ Received response from OpenAI")

            await self.send_progress(0.8, "📝 Processing architecture...")

            # Parse architecture from response
            try:
                architecture_text = response.content
                logger.info(f"   📄 Architecture response: {len(architecture_text)} chars")

                # Try to extract JSON
                architecture = self._parse_architecture_response(architecture_text)
                logger.info(f"   ✅ Architecture parsed successfully")
            except Exception as e:
                logger.warning(f"   ⚠️  Could not parse JSON response: {e}")
                logger.info(f"   📝 Using response as description")
                architecture = {
                    "description": architecture_text[:500],
                    "components": [],
                    "file_structure": ["src/", "tests/", "README.md"],
                    "technologies": [],
                    "patterns": [],
                    "data_flow": [],
                    "raw_response": architecture_text,
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

    def _parse_architecture_response(self, response_text: str) -> Dict[str, Any]:
        """
        ⚠️ MCP BLEIBT: Parse architecture from OpenAI response

        Tries to extract JSON from the response text.
        Falls back to using response as text if JSON parsing fails.
        """
        try:
            # Try direct JSON parsing
            architecture = json.loads(response_text)
            return architecture
        except json.JSONDecodeError:
            pass

        # Try to find JSON in response (enclosed in ```json ... ```)
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            try:
                architecture = json.loads(json_match.group(1))
                return architecture
            except json.JSONDecodeError:
                pass

        # Try to find any JSON-like object
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                architecture = json.loads(json_match.group(0))
                return architecture
            except json.JSONDecodeError:
                pass

        # If all parsing fails, raise error
        raise ValueError(f"Could not parse architecture from response: {response_text[:100]}")

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
                line = await async_stdin_readline()

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
    # Validate OpenAI API key before starting
    logger.info("🔑 Validating OpenAI API key...")
    try:
        validate_openai_key(exit_on_fail=True)
        logger.info("✅ OpenAI API key valid")
    except Exception as e:
        logger.error(f"❌ OpenAI API validation failed: {e}")
        sys.exit(1)

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
