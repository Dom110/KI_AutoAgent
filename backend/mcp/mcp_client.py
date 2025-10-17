"""
MCP Client Manager - Unified interface for all MCP tool calls

This replaces ALL direct service calls with MCP protocol calls.

Usage:
    from mcp.mcp_client import MCPClient

    mcp = MCPClient(workspace_path="/path/to/workspace")
    await mcp.initialize()

    # Parallel execution
    results = await asyncio.gather(
        mcp.call("perplexity", "search", {"query": "React patterns"}),
        mcp.call("memory", "store", {"content": "..."}),
        mcp.call("claude", "generate", {"prompt": "..."})
    )

Author: KI AutoAgent Team
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MCPConnectionError(Exception):
    """Raised when MCP server connection fails"""
    pass


class MCPToolError(Exception):
    """Raised when MCP tool execution fails"""
    pass


class MCPClient:
    """
    MCP Client Manager - Single point of contact for all MCP operations.

    Architecture:
    - One MCPClient instance per workspace
    - Maintains persistent connections to all MCP servers
    - Handles reconnection and error recovery
    - Routes tool calls to appropriate servers
    - Supports parallel execution via asyncio.gather()
    """

    def __init__(
        self,
        workspace_path: str,
        servers: list[str] | None = None,
        auto_reconnect: bool = True,
        timeout: float = 30.0
    ):
        """
        Initialize MCP Client.

        Args:
            workspace_path: Absolute path to workspace
            servers: List of MCP servers to connect to (default: all registered)
            auto_reconnect: Auto-reconnect on connection failure
            timeout: Default timeout for MCP calls (seconds)
        """
        self.workspace_path = workspace_path
        self.servers = servers or [
            "build_validation",  # NEW: v6.2 MCP
            "file_tools",        # NEW: v6.2 MCP
            "perplexity",
            "memory",
            "tree-sitter",
            "asimov",
            # "workflow",  # TODO: Fix workflow server initialization
            "claude"
        ]
        self.auto_reconnect = auto_reconnect
        self.timeout = timeout

        # Connection state
        self._connections: dict[str, Any] = {}
        self._processes: dict[str, Any] = {}  # Store subprocess handles
        self._initialized = False
        self._request_id = 0

        # MCP server paths (find project root by looking for .git directory)
        # This is more robust than relative paths when imported from tests
        current_path = Path(__file__).resolve()
        project_root = current_path.parent.parent.parent  # Start with relative calculation

        # Walk up to find .git directory (handles test imports correctly)
        max_depth = 10
        for _ in range(max_depth):
            if (project_root / ".git").exists():
                break
            if project_root.parent == project_root:  # Reached filesystem root
                # Fallback: use relative path from __file__
                project_root = Path(__file__).resolve().parent.parent.parent
                break
            project_root = project_root.parent

        self._server_paths = {
            "build_validation": project_root / "mcp_servers" / "build_validation_server.py",
            "file_tools": project_root / "mcp_servers" / "file_tools_server.py",
            "perplexity": project_root / "mcp_servers" / "perplexity_server.py",
            "memory": project_root / "mcp_servers" / "memory_server.py",
            "tree-sitter": project_root / "mcp_servers" / "tree_sitter_server.py",
            "asimov": project_root / "mcp_servers" / "asimov_server.py",
            "workflow": project_root / "mcp_servers" / "workflow_server.py",
            "claude": project_root / "mcp_servers" / "claude_cli_server.py"
        }

        # Find Python interpreter (use venv from root)
        self._python_exe = str(project_root / "venv" / "bin" / "python")

        logger.info(f"📡 MCPClient created for workspace: {workspace_path}")

    async def initialize(self) -> None:
        """
        Initialize connections to all MCP servers.

        This MUST be called before any tool calls!

        Raises:
            MCPConnectionError: If any server fails to connect
        """
        logger.info("🚀 Initializing MCP connections...")

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

    async def _connect_server(self, server_name: str) -> None:
        """
        Connect to a single MCP server by starting it as a subprocess.

        Starts the MCP server as a long-running subprocess and initializes it.

        Args:
            server_name: Name of MCP server (e.g., "perplexity")

        Raises:
            MCPConnectionError: If connection fails
        """
        try:
            # Get server script path
            server_path = self._server_paths.get(server_name)
            if not server_path or not server_path.exists():
                raise MCPConnectionError(f"Server script not found: {server_path}")

            # Start MCP server as subprocess
            logger.debug(f"Starting {server_name} server: {server_path}")
            process = await asyncio.create_subprocess_exec(
                self._python_exe,
                str(server_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace_path
            )

            self._processes[server_name] = process

            # Initialize the server (send initialize request)
            init_request = {
                "jsonrpc": "2.0",
                "id": self._next_request_id(),
                "method": "initialize",
                "params": {}
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

            # List available tools
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

            logger.debug(f"Server {server_name} has {len(tools)} tools")

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
        Execute raw JSON-RPC call to MCP server via stdin/stdout.

        Sends request to server's stdin, reads response from stdout.

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
            raise MCPConnectionError(f"Server {server} process has died (exit code: {process.returncode})")

        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": method,
            "params": params
        }

        try:
            # Send request to stdin
            request_line = json.dumps(request) + "\n"
            process.stdin.write(request_line.encode())
            await process.stdin.drain()

            # Read response from stdout (loop to handle progress notifications)
            # MCP servers send progress notifications during long-running operations
            request_id = request["id"]
            start_time = asyncio.get_event_loop().time()

            while True:
                # Check global timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > self.timeout:
                    raise MCPConnectionError(
                        f"MCP call to {server} timed out after {elapsed:.1f}s "
                        f"(exceeded global timeout of {self.timeout}s)"
                    )

                try:
                    # Read one line with short timeout (15s per line)
                    # Servers send heartbeat every 10s, so 15s is safe
                    response_line = await asyncio.wait_for(
                        process.stdout.readline(),
                        timeout=15.0
                    )
                except asyncio.TimeoutError:
                    # No output for 15s - check if we're still within global timeout
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > self.timeout:
                        raise MCPConnectionError(
                            f"MCP call to {server} timed out after {elapsed:.1f}s "
                            f"(exceeded global timeout of {self.timeout}s)"
                        )
                    # Within timeout but no heartbeat - server may be stuck
                    raise MCPConnectionError(
                        f"MCP call to {server} timed out after {elapsed:.1f}s "
                        f"(no output for 15s - server may be stuck)"
                    )

                if not response_line:
                    raise MCPConnectionError(f"Server {server} closed stdout (process died)")

                # Parse message
                message = json.loads(response_line.decode().strip())

                # Check if this is the response to our request
                if "id" in message and message["id"] == request_id:
                    # This is our response!
                    return message

                # This is a notification (no "id" field) - log and continue
                if "method" in message:
                    method = message["method"]
                    if method == "$/progress":
                        # Progress notification - just log at debug level
                        params = message.get("params", {})
                        logger.debug(f"📊 {server}: {params.get('message', 'progress...')}")
                    else:
                        logger.debug(f"📨 {server} notification: {method}")
                    continue  # Keep reading

                # Unknown message format - log warning and continue
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
        Call an MCP tool.

        THIS IS THE MAIN ENTRY POINT FOR ALL MCP CALLS!

        Args:
            server: MCP server name (e.g., "perplexity")
            tool: Tool name (e.g., "search")
            arguments: Tool arguments
            timeout: Call timeout (overrides default)

        Returns:
            Tool result

        Raises:
            MCPToolError: If tool execution fails

        Example:
            result = await mcp.call(
                server="perplexity",
                tool="search",
                arguments={"query": "React patterns", "max_results": 5}
            )
        """
        if not self._initialized:
            raise MCPConnectionError("MCPClient not initialized! Call initialize() first.")

        if server not in self._connections:
            raise MCPConnectionError(f"Server '{server}' not connected")

        logger.debug(f"🔧 Calling {server}.{tool}()")

        # Auto-add workspace_path if tool expects it
        if "workspace_path" not in arguments and server in ["memory", "workflow", "asimov"]:
            arguments["workspace_path"] = self.workspace_path

        # Build tool call request
        params = {
            "name": tool,
            "arguments": arguments
        }

        # Save timeout
        original_timeout = self.timeout
        if timeout:
            self.timeout = timeout

        try:
            # Execute tool call
            response = await self._raw_call(
                server=server,
                method="tools/call",
                params=params
            )

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
            # Connection error - try to reconnect if enabled
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
        Execute multiple MCP calls in parallel.

        This is the KEY to performance - parallel execution!

        Args:
            calls: List of (server, tool, arguments) tuples

        Returns:
            List of results (same order as calls)

        Example:
            results = await mcp.call_multiple([
                ("perplexity", "search", {"query": "React"}),
                ("memory", "store", {"content": "..."}),
                ("claude", "generate", {"prompt": "..."})
            ])
            # All 3 calls run in parallel!
        """
        logger.info(f"🚀 Executing {len(calls)} MCP calls in parallel...")

        tasks = [
            self.call(server, tool, args)
            for server, tool, args in calls
        ]

        # Execute ALL in parallel with asyncio.gather
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log any errors but return partial results
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
        Close all MCP connections and terminate server subprocesses.

        Call this when done with the client (e.g., workflow completion).
        """
        logger.info("🔌 Closing MCP connections...")

        # Terminate all server processes
        for server_name, process in self._processes.items():
            try:
                if process.returncode is None:  # Still running
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
        """Alias for close() for convenience."""
        await self.close()

    def get_server_status(self) -> dict[str, Any]:
        """
        Get status of all connected MCP servers.

        Returns:
            {
                "server_name": {
                    "status": "connected",
                    "tools": ["tool1", "tool2"],
                    "last_ping": "2025-10-13T10:30:00"
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
