#!/usr/bin/env python3
"""
⚠️ MCP BLEIBT: MCP Manager - Global MCP Client for v7.0 Pure MCP Architecture
⚠️ WICHTIG: MCP BLEIBT! Alle Agent-Calls gehen AUSSCHLIESSLICH über diesen Manager!
⚠️ KEINE direkten Agent-Instanzen! Alles über MCP!

This replaces ALL direct agent instantiation with MCP protocol calls.

Architecture:
- Single global MCPManager instance per backend process
- Manages all MCP server subprocesses (agents + utilities)
- Routes all agent calls via JSON-RPC over stdin/stdout
- Handles progress notifications from MCP servers
- Supports parallel execution via asyncio.gather()

Usage:
    from backend.utils.mcp_manager import get_mcp_manager

    mcp = get_mcp_manager(workspace_path="/path/to/workspace")
    await mcp.initialize()

    # Call agent via MCP
    result = await mcp.call(
        server="research_agent",
        tool="research",
        arguments={"instructions": "analyze workspace"}
    )

    # Parallel execution
    results = await asyncio.gather(
        mcp.call("research_agent", "research", {...}),
        mcp.call("architect_agent", "design", {...}),
        mcp.call("codesmith_agent", "generate", {...})
    )

Author: KI AutoAgent v7.0
Date: 2025-10-30
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


class MCPConnectionError(Exception):
    """⚠️ MCP BLEIBT: Raised when MCP server connection fails"""
    pass


class MCPToolError(Exception):
    """⚠️ MCP BLEIBT: Raised when MCP tool execution fails"""
    pass


class MCPManager:
    """
    ⚠️ MCP BLEIBT: Global MCP Manager - Single point of contact for ALL agent operations.

    This manager replaces ALL direct agent instantiation:
    - ResearchAgent → research_agent MCP server
    - ArchitectAgent → architect_agent MCP server
    - CodesmithAgent → codesmith_agent MCP server
    - ReviewFixAgent → reviewfix_agent MCP server
    - ResponderAgent → responder_agent MCP server

    Architecture:
    - One MCPManager instance per backend process
    - Maintains persistent connections to all MCP servers
    - Handles reconnection and error recovery
    - Routes tool calls to appropriate servers
    - Forwards $/progress notifications to callback
    - Supports parallel execution via asyncio.gather()
    """

    def __init__(
        self,
        workspace_path: str,
        servers: list[str] | None = None,
        auto_reconnect: bool = True,
        timeout: float = 120.0,  # 2 minutes default (Claude CLI can be slow)
        progress_callback: Callable[[str, str, float], None] | None = None
    ):
        """
        ⚠️ MCP BLEIBT: Initialize MCP Manager

        Args:
            workspace_path: Absolute path to workspace
            servers: List of MCP servers to connect to (default: all v7 agents)
            auto_reconnect: Auto-reconnect on connection failure
            timeout: Default timeout for MCP calls (seconds)
            progress_callback: Callback for progress notifications (server, message, progress)
        """
        self.workspace_path = workspace_path
        self.progress_callback = progress_callback

        # ⚠️ MCP BLEIBT: v7.0 Pure MCP Server Registry
        self.servers = servers or [
            # === AGENT MCP SERVERS (v7.0) ===
            "openai",              # OpenAI GPT-4o wrapper
            "research_agent",      # Research Agent
            "architect_agent",     # Architect Agent
            "codesmith_agent",     # Codesmith Agent
            "reviewfix_agent",     # ReviewFix Agent
            "responder_agent",     # Responder Agent

            # === UTILITY MCP SERVERS ===
            "perplexity",          # Web search (existing)
            "memory",              # Memory system (existing)
            "build_validation",    # Build validation (existing)
            "file_tools",          # File operations (existing)
            "tree_sitter",         # Code parsing (existing)
        ]

        self.auto_reconnect = auto_reconnect
        self.timeout = timeout

        # Connection state
        self._connections: dict[str, Any] = {}
        self._processes: dict[str, Any] = {}
        self._initialized = False
        self._request_id = 0

        # ⚠️ MCP BLEIBT: MCP server paths (find project root)
        current_path = Path(__file__).resolve()
        project_root = current_path.parent.parent.parent

        # Walk up to find .git directory
        max_depth = 10
        for _ in range(max_depth):
            if (project_root / ".git").exists():
                break
            if project_root.parent == project_root:
                project_root = Path(__file__).resolve().parent.parent.parent
                break
            project_root = project_root.parent

        self._project_root = project_root

        # ⚠️ MCP BLEIBT: Server path registry
        self._server_paths = {
            # === v7.0 AGENT MCP SERVERS ===
            "openai": project_root / "mcp_servers" / "openai_server.py",
            "research_agent": project_root / "mcp_servers" / "research_agent_server.py",
            "architect_agent": project_root / "mcp_servers" / "architect_agent_server.py",
            "codesmith_agent": project_root / "mcp_servers" / "codesmith_agent_server.py",
            "reviewfix_agent": project_root / "mcp_servers" / "reviewfix_agent_server.py",
            "responder_agent": project_root / "mcp_servers" / "responder_agent_server.py",

            # === UTILITY MCP SERVERS ===
            "perplexity": project_root / "mcp_servers" / "perplexity_server.py",
            "memory": project_root / "mcp_servers" / "memory_server.py",
            "build_validation": project_root / "mcp_servers" / "build_validation_server.py",
            "file_tools": project_root / "mcp_servers" / "file_tools_server.py",
            "tree_sitter": project_root / "mcp_servers" / "tree_sitter_server.py",
        }

        # Find Python interpreter
        self._python_exe = str(project_root / "venv" / "bin" / "python")

        logger.info(f"📡 MCPManager created for workspace: {workspace_path}")
        logger.info(f"   Servers to connect: {len(self.servers)}")

    async def initialize(self) -> None:
        """
        ⚠️ MCP BLEIBT: Initialize connections to all MCP servers

        This MUST be called before any tool calls!

        Raises:
            MCPConnectionError: If any server fails to connect
        """
        logger.info("🚀 Initializing MCP connections...")
        logger.info("⚠️ MCP BLEIBT: Starting Pure MCP v7.0 agent servers...")

        # Connect to all servers in parallel
        tasks = [self._connect_server(server) for server in self.servers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check for failures
        failures = []
        for server, result in zip(self.servers, results):
            if isinstance(result, Exception):
                failures.append((server, str(result)))
                logger.error(f"❌ Failed to connect to {server}: {result}")
            else:
                logger.info(f"✅ Connected to {server}")

        if failures:
            error_msg = "\n".join([f"  - {srv}: {err}" for srv, err in failures])
            raise MCPConnectionError(f"Failed to connect to MCP servers:\n{error_msg}")

        self._initialized = True
        logger.info(f"✅ All {len(self.servers)} MCP servers connected")
        logger.info("⚠️ MCP BLEIBT: Pure MCP architecture active!")

    async def _connect_server(self, server_name: str) -> None:
        """
        ⚠️ MCP BLEIBT: Connect to a single MCP server

        Starts the MCP server as a subprocess and initializes it.

        Args:
            server_name: Name of MCP server (e.g., "research_agent")

        Raises:
            MCPConnectionError: If connection fails
        """
        try:
            # Get server script path
            server_path = self._server_paths.get(server_name)
            if not server_path or not server_path.exists():
                raise MCPConnectionError(f"Server script not found: {server_path}")

            # ⚠️ MCP BLEIBT: Start MCP server as subprocess
            # Run from project root, NOT workspace (workspace might not exist yet)
            logger.debug(f"Starting {server_name} server: {server_path}")
            process = await asyncio.create_subprocess_exec(
                self._python_exe,
                str(server_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self._project_root)
            )

            self._processes[server_name] = process

            # ⚠️ MCP BLEIBT: Initialize via JSON-RPC
            init_request = {
                "jsonrpc": "2.0",
                "id": self._next_request_id(),
                "method": "initialize",
                "params": {"workspace_path": self.workspace_path}
            }

            process.stdin.write((json.dumps(init_request) + "\n").encode())
            await process.stdin.drain()

            # Read init response (with timeout)
            try:
                line = await asyncio.wait_for(
                    process.stdout.readline(),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise MCPConnectionError(f"{server_name} failed to respond to initialization")

            init_response = json.loads(line.decode().strip())
            if "error" in init_response:
                raise MCPConnectionError(f"Init failed: {init_response['error']}")

            # ⚠️ MCP BLEIBT: List available tools
            tools_request = {
                "jsonrpc": "2.0",
                "id": self._next_request_id(),
                "method": "tools/list",
                "params": {}
            }

            process.stdin.write((json.dumps(tools_request) + "\n").encode())
            await process.stdin.drain()

            line = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=5.0
            )

            tools_response = json.loads(line.decode().strip())
            if "error" in tools_response:
                raise MCPConnectionError(f"tools/list failed: {tools_response['error']}")

            # Cache connection info
            tools = tools_response.get("result", {}).get("tools", [])
            self._connections[server_name] = {
                "status": "connected",
                "tools": [t["name"] for t in tools],
                "last_ping": datetime.now()
            }

            logger.debug(f"Server {server_name} has {len(tools)} tools: {', '.join([t['name'] for t in tools])}")

        except Exception as e:
            # Cleanup on failure
            if server_name in self._processes:
                process = self._processes[server_name]
                process.kill()
                await process.wait()
                del self._processes[server_name]
            raise MCPConnectionError(f"Failed to connect to {server_name}: {e}")

    def _next_request_id(self) -> int:
        """Generate next JSON-RPC request ID"""
        self._request_id += 1
        return self._request_id

    async def _raw_call(
        self,
        server: str,
        method: str,
        params: dict[str, Any]
    ) -> dict[str, Any]:
        """
        ⚠️ MCP BLEIBT: Execute raw JSON-RPC call to MCP server

        Sends request to server's stdin, reads response from stdout.
        Handles $/progress notifications via callback.

        Args:
            server: MCP server name
            method: JSON-RPC method
            params: Method parameters

        Returns:
            JSON-RPC response

        Raises:
            MCPConnectionError: If call fails
        """
        if server not in self._processes:
            raise MCPConnectionError(f"Server {server} not started")

        process = self._processes[server]

        # Check if process is still alive
        if process.returncode is not None:
            raise MCPConnectionError(
                f"Server {server} process has died (exit code: {process.returncode})"
            )

        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": method,
            "params": params
        }

        try:
            # ⚠️ MCP BLEIBT: Send request to stdin
            request_line = json.dumps(request) + "\n"
            process.stdin.write(request_line.encode())
            await process.stdin.drain()
            logger.debug(f"   📤 Request sent to {server} (id={request['id']}, method={method})")

            # ⚠️ MCP BLEIBT: Read response (handle progress notifications)
            request_id = request["id"]
            start_time = asyncio.get_event_loop().time()
            lines_read = 0

            while True:
                # Check global timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > self.timeout:
                    logger.error(f"   ❌ {server} timeout after {elapsed:.1f}s (read {lines_read} lines)")
                    raise MCPConnectionError(
                        f"MCP call to {server} timed out after {elapsed:.1f}s "
                        f"(exceeded timeout of {self.timeout}s, read {lines_read} lines)"
                    )

                # Log every 10 seconds
                if int(elapsed) % 10 == 0 and elapsed > 0:
                    logger.info(f"   ⏳ {server} still processing... ({elapsed:.0f}s elapsed)")

                try:
                    # Read one line with short timeout (15s per line)
                    response_line = await asyncio.wait_for(
                        process.stdout.readline(),
                        timeout=15.0
                    )
                    lines_read += 1
                except asyncio.TimeoutError:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > self.timeout:
                        raise MCPConnectionError(
                            f"MCP call to {server} timed out after {elapsed:.1f}s"
                        )
                    raise MCPConnectionError(
                        f"MCP call to {server} timed out (no output for 15s)"
                    )

                if not response_line:
                    raise MCPConnectionError(f"Server {server} closed stdout")

                # Parse message
                message = json.loads(response_line.decode().strip())

                # Check if this is the response to our request
                if "id" in message and message["id"] == request_id:
                    # ⚠️ MCP BLEIBT: This is our response!
                    return message

                # ⚠️ MCP BLEIBT: Handle $/progress notification
                if "method" in message:
                    method_name = message["method"]
                    if method_name == "$/progress":
                        # Progress notification - forward to callback
                        params_data = message.get("params", {})
                        progress_msg = params_data.get("message", "")
                        progress_val = params_data.get("progress", 0.0)

                        logger.debug(f"📊 {server}: {progress_msg}")

                        # ⚠️ MCP BLEIBT: Forward to callback for event streaming!
                        if self.progress_callback:
                            try:
                                self.progress_callback(server, progress_msg, progress_val)
                            except Exception as e:
                                logger.warning(f"Progress callback error: {e}")
                    else:
                        logger.debug(f"📨 {server} notification: {method_name}")
                    continue

                # Unknown message
                logger.warning(f"⚠️  {server} sent unexpected message: {message}")
                continue

        except json.JSONDecodeError as e:
            raise MCPConnectionError(f"Invalid JSON response from {server}: {e}")
        except Exception as e:
            raise MCPConnectionError(f"MCP call to {server} failed: {e}")

    async def call(
        self,
        server: str,
        tool: str,
        arguments: dict[str, Any],
        timeout: float | None = None
    ) -> dict[str, Any]:
        """
        ⚠️ MCP BLEIBT: Call an MCP tool

        THIS IS THE MAIN ENTRY POINT FOR ALL AGENT CALLS!

        Instead of:
            research_agent = ResearchAgent()
            result = await research_agent.execute(state)

        Use:
            result = await mcp.call(
                server="research_agent",
                tool="research",
                arguments={"instructions": "..."}
            )

        Args:
            server: MCP server name (e.g., "research_agent")
            tool: Tool name (e.g., "research")
            arguments: Tool arguments
            timeout: Call timeout (overrides default)

        Returns:
            Tool result

        Raises:
            MCPToolError: If tool execution fails

        Example:
            result = await mcp.call(
                server="architect_agent",
                tool="design",
                arguments={
                    "instructions": "Design REST API",
                    "research_context": {...}
                }
            )
        """
        if not self._initialized:
            raise MCPConnectionError("MCPManager not initialized! Call initialize() first.")

        if server not in self._connections:
            raise MCPConnectionError(f"Server '{server}' not connected")

        logger.info(f"🔧 Calling {server}.{tool}() with timeout={timeout or self.timeout}s")
        logger.debug(f"   Arguments keys: {list(arguments.keys())}")

        # Auto-add workspace_path if tool expects it
        if "workspace_path" not in arguments:
            arguments["workspace_path"] = self.workspace_path

        # ⚠️ MCP BLEIBT: Build tool call request
        params = {
            "name": tool,
            "arguments": arguments
        }

        # Save timeout
        original_timeout = self.timeout
        if timeout:
            logger.info(f"   📊 Setting custom timeout: {self.timeout}s → {timeout}s")
            self.timeout = timeout

        try:
            # ⚠️ MCP BLEIBT: Execute tool call via JSON-RPC
            logger.debug(f"   🔄 Sending request to {server}...")
            response = await self._raw_call(
                server=server,
                method="tools/call",
                params=params
            )
            logger.info(f"   ✅ {server}.{tool}() received response")

            # Check for errors
            if "error" in response:
                error = response["error"]
                raise MCPToolError(
                    f"Tool {server}.{tool} failed: {error.get('message', 'Unknown error')}"
                )

            # Extract result
            result = response.get("result", {})

            logger.debug(f"✅ {server}.{tool}() completed")
            return result

        except MCPConnectionError as e:
            # ⚠️ MCP BLEIBT: Connection error - try to reconnect
            if self.auto_reconnect:
                logger.warning(f"⚠️  Connection lost to {server}, attempting reconnect...")
                try:
                    await self._connect_server(server)
                    logger.info(f"✅ Reconnected to {server}, retrying call...")
                    return await self.call(server, tool, arguments, timeout)
                except Exception as reconnect_error:
                    logger.error(f"❌ Reconnect failed: {reconnect_error}")
            raise

        finally:
            # Restore timeout
            self.timeout = original_timeout

    async def call_multiple(
        self,
        calls: list[tuple[str, str, dict[str, Any]]]
    ) -> list[dict[str, Any]]:
        """
        ⚠️ MCP BLEIBT: Execute multiple MCP calls in parallel

        This enables parallel agent execution for performance!

        Args:
            calls: List of (server, tool, arguments) tuples

        Returns:
            List of results (same order as calls)

        Example:
            results = await mcp.call_multiple([
                ("research_agent", "research", {"instructions": "..."}),
                ("architect_agent", "design", {"instructions": "..."}),
                ("codesmith_agent", "generate", {"instructions": "..."})
            ])
            # All 3 agents run in parallel!
        """
        logger.info(f"🚀 Executing {len(calls)} MCP calls in parallel...")
        logger.info("⚠️ MCP BLEIBT: Parallel agent execution via MCP!")

        tasks = [
            self.call(server, tool, args)
            for server, tool, args in calls
        ]

        # ⚠️ MCP BLEIBT: Execute ALL in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log errors
        errors = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                server, tool, _ = calls[i]
                errors.append(f"{server}.{tool}: {result}")
                logger.error(f"❌ {server}.{tool} failed: {result}")

        if errors:
            logger.warning(f"⚠️  {len(errors)}/{len(calls)} calls failed")
        else:
            logger.info(f"✅ All {len(calls)} calls completed successfully")

        return results

    async def close(self) -> None:
        """
        ⚠️ MCP BLEIBT: Close all MCP connections

        Terminates all MCP server subprocesses.
        """
        logger.info("🔌 Closing MCP connections...")

        # Terminate all server processes
        for server_name, process in self._processes.items():
            try:
                if process.returncode is None:
                    process.terminate()
                    try:
                        await asyncio.wait_for(process.wait(), timeout=5.0)
                        logger.debug(f"Terminated {server_name} process")
                    except asyncio.TimeoutError:
                        process.kill()
                        await process.wait()
                        logger.warning(f"Had to kill {server_name} process")
            except Exception as e:
                logger.warning(f"Error closing {server_name}: {e}")

        self._processes.clear()
        self._connections.clear()
        self._initialized = False
        logger.info("✅ MCP connections closed")

    async def cleanup(self) -> None:
        """Alias for close()"""
        await self.close()

    def get_server_status(self) -> dict[str, Any]:
        """
        ⚠️ MCP BLEIBT: Get status of all connected MCP servers

        Returns:
            {
                "server_name": {
                    "status": "connected",
                    "tools": ["tool1", "tool2"],
                    "last_ping": "2025-10-30T..."
                }
            }
        """
        return {
            server: {
                **info,
                "last_ping": info["last_ping"].isoformat()
            }
            for server, info in self._connections.items()
        }


# ============================================================================
# Global Singleton
# ============================================================================

_global_mcp_manager: MCPManager | None = None


def get_mcp_manager(
    workspace_path: str | None = None,
    progress_callback: Callable[[str, str, float], None] | None = None,
    force_new: bool = False
) -> MCPManager:
    """
    ⚠️ MCP BLEIBT: Get global MCP Manager instance

    This returns a singleton MCPManager for the backend process.

    Args:
        workspace_path: Workspace path (required for first call)
        progress_callback: Progress notification callback
        force_new: Force create new instance

    Returns:
        MCPManager instance

    Example:
        mcp = get_mcp_manager(workspace_path="/path/to/workspace")
        await mcp.initialize()
        result = await mcp.call("research_agent", "research", {...})
    """
    global _global_mcp_manager

    if force_new or _global_mcp_manager is None:
        if not workspace_path:
            raise ValueError("workspace_path required for first call to get_mcp_manager()")

        logger.info("⚠️ MCP BLEIBT: Creating global MCPManager instance")
        _global_mcp_manager = MCPManager(
            workspace_path=workspace_path,
            progress_callback=progress_callback
        )

    return _global_mcp_manager


async def close_mcp_manager() -> None:
    """
    ⚠️ MCP BLEIBT: Close global MCP Manager

    Call this on backend shutdown.
    """
    global _global_mcp_manager

    if _global_mcp_manager:
        await _global_mcp_manager.close()
        _global_mcp_manager = None
        logger.info("⚠️ MCP BLEIBT: Global MCPManager closed")


# ============================================================================
# Export
# ============================================================================

__all__ = [
    "MCPManager",
    "MCPConnectionError",
    "MCPToolError",
    "get_mcp_manager",
    "close_mcp_manager"
]
