# MCP Implementation Plan - Complete Architecture Transformation

**Version:** 1.0.0
**Date:** 2025-10-13
**Status:** READY FOR EXECUTION
**Estimated Duration:** 8-12 hours implementation + 4-6 hours testing

---

## Executive Summary

This plan transforms KI_AutoAgent from a **synchronous direct-call architecture** to a **fully parallel MCP-based architecture**, targeting:

- **316% performance improvement** (12.5 min → 3 min)
- **Full parallelization** of all agent operations
- **Zero tolerance for direct service calls** - Everything through MCP
- **Professional test coverage** (10% → 100%)
- **Deletion of ALL obsolete code** - No legacy baggage

### Current State (WRONG)
```python
# Sequential blocking calls
result1 = perplexity_service.search(query)  # WAIT 30s
result2 = claude_cli.run(prompt)            # WAIT 60s
result3 = memory.store(data)                # WAIT 2s
# Total: 92s sequential
```

### Target State (CORRECT)
```python
# Parallel MCP calls
results = await asyncio.gather(
    mcp.call("perplexity", "search", {"query": query}),
    mcp.call("claude", "generate", {"prompt": prompt}),
    mcp.call("memory", "store", {"data": data})
)
# Total: 60s (max of all, not sum)
```

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Implementation Steps](#2-implementation-steps)
3. [Test Strategy](#3-test-strategy)
4. [Migration Checklist](#4-migration-checklist)
5. [Code Examples](#5-code-examples)
6. [Performance Targets](#6-performance-targets)
7. [Files to Delete](#7-files-to-delete)

---

## 1. Architecture Overview

### 1.1 Why MCP is Superior

**MCP (Model Context Protocol)** is a JSON-RPC 2.0 protocol providing:

1. **Dynamic Tool Discovery** - Agents discover available tools at runtime
2. **Parallel Execution** - Multiple tools run simultaneously via `asyncio.gather()`
3. **Error Recovery** - Graceful degradation with partial results
4. **Hot Reload** - Add/remove servers without restarting system
5. **Protocol Standardization** - Industry-standard JSON-RPC 2.0
6. **Workspace Isolation** - Each workspace gets its own MCP context

### 1.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    WebSocket Client                             │
│                (VS Code / CLI / Browser)                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ ws://localhost:8002/ws/chat
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│              FastAPI WebSocket Server                           │
│           (backend/api/server_v6_integrated.py)                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│          WorkflowV6Integrated Orchestrator                      │
│              (backend/workflow_v6_integrated.py)                │
│                                                                 │
│  ┌────────────────────────────────────────────────────┐       │
│  │           MCP Client Manager                        │       │
│  │  - Initialize MCP connections on startup            │       │
│  │  - Maintain connection pool                         │       │
│  │  - Handle reconnection logic                        │       │
│  │  - Route tool calls to correct MCP server          │       │
│  └────────────────────────────────────────────────────┘       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
        ┌──────────────────┴──────────────────┐
        │                                      │
        ↓                                      ↓
┌────────────────┐                  ┌──────────────────┐
│  Agent Layer   │                  │   MCP Servers    │
│                │                  │                  │
│  Research      │──────────────────│  perplexity      │
│  Architect     │──────────────────│  memory          │
│  Codesmith     │──────────────────│  tree-sitter     │
│  ReviewFix     │──────────────────│  asimov          │
│                │──────────────────│  workflow        │
│                │──────────────────│  claude (new!)   │
└────────────────┘                  └──────────────────┘

         ↓ Parallel Execution (asyncio.gather)

┌─────────────────────────────────────────────────────────────────┐
│                     External Services                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │Perplexity│  │  OpenAI  │  │ Claude   │  │   FAISS  │       │
│  │   API    │  │Embeddings│  │   CLI    │  │   DB     │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Parallel Execution Flow

**OLD (Sequential):**
```
T+0s:    Research starts → Perplexity API call
T+30s:   Research complete
T+30s:   Architect starts → Claude CLI call
T+90s:   Architect complete
T+90s:   Codesmith starts → Claude CLI call
T+600s:  Codesmith complete (15 min timeout!)
T+600s:  ReviewFix starts → Claude CLI call
T+750s:  COMPLETE (12.5 minutes)
```

**NEW (Parallel):**
```
T+0s:    ALL agents start simultaneously via MCP
         ├─ Research → perplexity MCP (async)
         ├─ Architect → claude MCP (async)
         ├─ Codesmith → claude MCP (async)
         └─ ReviewFix → claude MCP (async)

T+30s:   Research completes (fastest)
T+60s:   Architect completes
T+150s:  Codesmith completes
T+180s:  ReviewFix completes
T+180s:  COMPLETE (3 minutes - 75% faster!)
```

**Key Insight:** Operations run in parallel, so total time = MAX(individual times), not SUM!

---

## 2. Implementation Steps

### Phase 1: MCP Server Registration Fix (30 min)

#### Step 1.1: Fix Python Paths in install_mcp.sh

**Problem:** Script uses wrong Python interpreter paths

**File:** `/Users/dominikfoert/git/KI_AutoAgent/install_mcp.sh`

**Changes:**

```bash
# CURRENT (lines 91-131)
claude mcp add perplexity "${VENV_PYTHON}" "${SCRIPT_DIR}/mcp_servers/perplexity_server.py"
claude mcp add tree-sitter "${VENV_PYTHON}" "${SCRIPT_DIR}/mcp_servers/tree_sitter_server.py"
claude mcp add memory "${VENV_PYTHON}" "${SCRIPT_DIR}/mcp_servers/memory_server.py"
claude mcp add asimov "${VENV_PYTHON}" "${SCRIPT_DIR}/mcp_servers/asimov_server.py"

# ADD NEW SERVERS
# 5. Workflow
echo -e "${BLUE}⚙️  Registering Workflow MCP Server...${NC}"
claude mcp add workflow "${VENV_PYTHON}" "${SCRIPT_DIR}/mcp_servers/workflow_server.py"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Workflow registered${NC}"
else
    echo -e "${RED}❌ Workflow registration failed${NC}"
    exit 1
fi
echo ""

# 6. Claude CLI Wrapper (NEW!)
echo -e "${BLUE}🤖 Registering Claude CLI MCP Server...${NC}"
claude mcp add claude "${VENV_PYTHON}" "${SCRIPT_DIR}/mcp_servers/claude_cli_server.py"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Claude CLI registered${NC}"
else
    echo -e "${RED}❌ Claude CLI registration failed${NC}"
    exit 1
fi
echo ""
```

**Verification Command:**
```bash
./install_mcp.sh
claude mcp list
```

**Expected Output:**
```
Registered MCP Servers:
✓ perplexity - Connected
✓ tree-sitter - Connected
✓ memory - Connected
✓ asimov - Connected
✓ workflow - Connected
✓ claude - Connected
```

---

### Phase 2: Create MCP Client Wrapper (2 hours)

#### Step 2.1: Create MCP Client Manager

**New File:** `/Users/dominikfoert/git/KI_AutoAgent/backend/mcp/mcp_client.py`

```python
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
            "perplexity",
            "memory",
            "tree-sitter",
            "asimov",
            "workflow",
            "claude"
        ]
        self.auto_reconnect = auto_reconnect
        self.timeout = timeout

        # Connection state
        self._connections: dict[str, Any] = {}
        self._initialized = False
        self._request_id = 0

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
        Connect to a single MCP server.

        Uses `claude mcp call` command to verify server is accessible.

        Args:
            server_name: Name of MCP server (e.g., "perplexity")

        Raises:
            MCPConnectionError: If connection fails
        """
        try:
            # Test connection by calling tools/list
            result = await self._raw_call(
                server=server_name,
                method="tools/list",
                params={}
            )

            if "error" in result:
                raise MCPConnectionError(f"Server returned error: {result['error']}")

            # Cache available tools
            tools = result.get("result", {}).get("tools", [])
            self._connections[server_name] = {
                "status": "connected",
                "tools": [t["name"] for t in tools],
                "last_ping": datetime.now()
            }

            logger.debug(f"Server {server_name} has {len(tools)} tools")

        except Exception as e:
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
        Execute raw JSON-RPC call to MCP server.

        Uses `claude mcp call` command under the hood.

        Args:
            server: MCP server name
            method: JSON-RPC method
            params: Method parameters

        Returns:
            JSON-RPC response

        Raises:
            MCPConnectionError: If call fails
        """
        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": method,
            "params": params
        }

        try:
            # Build command
            cmd = [
                "claude",
                "mcp",
                "call",
                server,
                json.dumps(request)
            ]

            # Execute with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace_path
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise MCPConnectionError(f"MCP call to {server} timed out after {self.timeout}s")

            if process.returncode != 0:
                error = stderr.decode() if stderr else "Unknown error"
                raise MCPConnectionError(f"MCP call failed: {error}")

            # Parse response
            response = json.loads(stdout.decode())
            return response

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
        Close all MCP connections.

        Call this when done with the client (e.g., workflow completion).
        """
        logger.info("🔌 Closing MCP connections...")
        self._connections.clear()
        self._initialized = False
        logger.info("✅ MCP connections closed")

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
```

**Test Command:**
```python
# Test MCP client
python -c "
import asyncio
from mcp.mcp_client import MCPClient

async def test():
    mcp = MCPClient(workspace_path='/tmp/test')
    await mcp.initialize()

    # Single call
    result = await mcp.call('perplexity', 'search', {'query': 'Python async', 'max_results': 2})
    print('Search result:', result)

    # Parallel calls
    results = await mcp.call_multiple([
        ('perplexity', 'search', {'query': 'React'}),
        ('memory', 'count_memory', {})
    ])
    print('Parallel results:', results)

    await mcp.close()

asyncio.run(test())
"
```

---

#### Step 2.2: Create Claude CLI MCP Server

**New File:** `/Users/dominikfoert/git/KI_AutoAgent/mcp_servers/claude_cli_server.py`

```python
#!/usr/bin/env python3
"""
Claude CLI MCP Server - Expose Claude CLI as MCP tool

Wraps ClaudeCLISimple as an MCP server for parallel execution.

Tools:
1. claude_generate - Generate code or text with Claude
2. claude_read_file - Read file via Claude (uses Read tool)
3. claude_run_command - Run bash command via Claude (uses Bash tool)

Benefits:
- Parallel execution with other MCP tools
- Consistent error handling
- Timeout management
- HITL support via workspace_path

Register:
    claude mcp add claude python mcp_servers/claude_cli_server.py

Usage:
    result = await mcp.call("claude", "generate", {
        "prompt": "Generate React component",
        "workspace_path": "/path/to/workspace",
        "agent_name": "codesmith",
        "temperature": 0.2,
        "max_tokens": 8192
    })

Author: KI AutoAgent Team
Version: 1.0.0
"""

import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from adapters.claude_cli_simple import ClaudeCLISimple
from langchain_core.messages import SystemMessage, HumanMessage


async def claude_generate(
    prompt: str,
    workspace_path: str,
    system_prompt: str | None = None,
    agent_name: str = "assistant",
    temperature: float = 0.3,
    max_tokens: int = 4096,
    tools: list[str] | None = None
) -> dict[str, Any]:
    """
    Generate code or text with Claude CLI.

    Args:
        prompt: User prompt (task description)
        workspace_path: Absolute path to workspace
        system_prompt: System prompt (agent instructions)
        agent_name: Agent name (for HITL tracking)
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        tools: Available tools (default: ["Read", "Edit", "Bash"])

    Returns:
        {
            "success": bool,
            "content": str,
            "agent": str,
            "duration_ms": float,
            "files_created": list[dict]
        }
    """
    try:
        # Create Claude CLI instance
        llm = ClaudeCLISimple(
            model="claude-sonnet-4-20250514",
            temperature=temperature,
            max_tokens=max_tokens,
            agent_name=agent_name,
            agent_tools=tools or ["Read", "Edit", "Bash"],
            workspace_path=workspace_path
        )

        # Build messages
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        # Execute
        start = datetime.now()
        response = await llm.ainvoke(messages)
        duration_ms = (datetime.now() - start).total_seconds() * 1000

        # Extract files created
        files_created = []
        if hasattr(llm, 'last_events') and llm.last_events:
            files_created = llm.extract_file_paths_from_events(llm.last_events)

        return {
            "success": True,
            "content": response.content if hasattr(response, 'content') else str(response),
            "agent": agent_name,
            "duration_ms": duration_ms,
            "files_created": files_created,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "agent": agent_name,
            "timestamp": datetime.now().isoformat()
        }


async def claude_read_file(
    file_path: str,
    workspace_path: str
) -> dict[str, Any]:
    """
    Read file via Claude (uses Read tool).

    Args:
        file_path: Path to file (relative to workspace)
        workspace_path: Absolute path to workspace

    Returns:
        {
            "success": bool,
            "content": str,
            "file_path": str
        }
    """
    try:
        llm = ClaudeCLISimple(
            agent_name="reader",
            agent_tools=["Read"],
            workspace_path=workspace_path
        )

        prompt = f"Read the file: {file_path}"
        response = await llm.ainvoke([HumanMessage(content=prompt)])

        return {
            "success": True,
            "content": response.content if hasattr(response, 'content') else str(response),
            "file_path": file_path,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path,
            "timestamp": datetime.now().isoformat()
        }


async def claude_run_command(
    command: str,
    workspace_path: str
) -> dict[str, Any]:
    """
    Run bash command via Claude (uses Bash tool).

    Args:
        command: Bash command to run
        workspace_path: Absolute path to workspace

    Returns:
        {
            "success": bool,
            "output": str,
            "command": str
        }
    """
    try:
        llm = ClaudeCLISimple(
            agent_name="runner",
            agent_tools=["Bash"],
            workspace_path=workspace_path
        )

        prompt = f"Run this command: {command}"
        response = await llm.ainvoke([HumanMessage(content=prompt)])

        return {
            "success": True,
            "output": response.content if hasattr(response, 'content') else str(response),
            "command": command,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "command": command,
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# MCP PROTOCOL HANDLER
# ============================================================================

async def handle_request(request: dict) -> dict:
    """Handle MCP JSON-RPC request"""

    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    # Initialize
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "claude-cli-mcp-server",
                    "version": "1.0.0"
                }
            }
        }

    # List tools
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {
                        "name": "claude_generate",
                        "description": "Generate code or text with Claude CLI. Supports file creation via Edit tool.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "prompt": {"type": "string", "description": "User prompt (task)"},
                                "workspace_path": {"type": "string", "description": "Workspace path"},
                                "system_prompt": {"type": "string", "description": "System prompt (optional)"},
                                "agent_name": {"type": "string", "description": "Agent name (default: assistant)"},
                                "temperature": {"type": "number", "description": "Temperature (default: 0.3)"},
                                "max_tokens": {"type": "integer", "description": "Max tokens (default: 4096)"},
                                "tools": {"type": "array", "description": "Tools list (default: [Read, Edit, Bash])"}
                            },
                            "required": ["prompt", "workspace_path"]
                        }
                    },
                    {
                        "name": "claude_read_file",
                        "description": "Read file via Claude (uses Read tool)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "file_path": {"type": "string", "description": "File path (relative to workspace)"},
                                "workspace_path": {"type": "string", "description": "Workspace path"}
                            },
                            "required": ["file_path", "workspace_path"]
                        }
                    },
                    {
                        "name": "claude_run_command",
                        "description": "Run bash command via Claude (uses Bash tool)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "command": {"type": "string", "description": "Bash command"},
                                "workspace_path": {"type": "string", "description": "Workspace path"}
                            },
                            "required": ["command", "workspace_path"]
                        }
                    }
                ]
            }
        }

    # Execute tool
    elif method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})

        try:
            if tool_name == "claude_generate":
                result = await claude_generate(**tool_args)
            elif tool_name == "claude_read_file":
                result = await claude_read_file(**tool_args)
            elif tool_name == "claude_run_command":
                result = await claude_run_command(**tool_args)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"}
                }

            # Format response
            content_text = f"# Claude CLI Result\n\n**Tool:** {tool_name}\n\n"
            content_text += f"**Result:**\n```json\n{json.dumps(result, indent=2)}\n```\n"

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": content_text}]
                }
            }

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": f"Tool execution failed: {e}"}
            }

    # Unknown method
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        }


# ============================================================================
# MAIN SERVER LOOP
# ============================================================================

async def main():
    """Main MCP server loop (stdin/stdout protocol)"""

    print(f"[{datetime.now()}] Claude CLI MCP Server started", file=sys.stderr)

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            request = json.loads(line)
            response = await handle_request(request)

            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

        except json.JSONDecodeError as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"}
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Internal error: {e}"}
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] Interrupted by user", file=sys.stderr)
    except Exception as e:
        print(f"[{datetime.now()}] Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
```

---

### Phase 3: Convert All Direct Calls to MCP (4 hours)

#### Step 3.1: Update Research Subgraph

**File:** `/Users/dominikfoert/git/KI_AutoAgent/backend/subgraphs/research_subgraph_v6_1.py`

**DELETE these imports:**
```python
# REMOVE THESE LINES:
from adapters.claude_cli_simple import ClaudeCLISimple as ChatAnthropic
from tools.perplexity_tool import perplexity_search
```

**ADD these imports:**
```python
# ADD THESE LINES:
from mcp.mcp_client import MCPClient
```

**REPLACE `research_search_mode()` function (lines 42-152):**

```python
async def research_search_mode(
    state: ResearchState,
    workspace_path: str,
    memory: Any | None,
    mcp: MCPClient,  # ← NEW! MCP client instead of direct services
    hitl_callback: Any | None
) -> dict[str, Any]:
    """
    Research Mode: Web search with Perplexity via MCP.

    CHANGED: Uses MCP instead of direct PerplexityService calls.
    """
    logger.info(f"🌐 Research mode: web search for '{state['query']}'")

    # Step 1: Search with Perplexity (via MCP!)
    logger.info("🌐 Searching with Perplexity via MCP...")
    search_result = await mcp.call(
        server="perplexity",
        tool="perplexity_search",
        arguments={
            "query": state['query'],
            "max_results": 5
        }
    )

    # Extract content from MCP response
    search_findings = ""
    if search_result.get("success"):
        content_blocks = search_result.get("content", [])
        for block in content_blocks:
            if block.get("type") == "text":
                search_findings += block.get("text", "")
    else:
        search_findings = f"Search failed: {search_result.get('error', 'Unknown error')}"

    logger.info(f"✅ Perplexity results: {len(search_findings)} chars")

    # Step 2: Analyze with Claude (via MCP!)
    logger.info("🤖 Analyzing findings with Claude via MCP...")

    system_prompt = """You are a research analyst specializing in software development.

Your responsibilities:
1. Analyze search results and extract key insights
2. Identify relevant technologies, patterns, and best practices
3. Summarize findings concisely
4. Provide actionable recommendations

Output format:
- Key Findings: Main insights from the research
- Technologies: Relevant tools/frameworks mentioned
- Best Practices: Recommended approaches
- Sources: Where the information came from"""

    user_prompt = f"""Analyze the following research results:

**Query:** {state['query']}

**Search Results:**
{search_findings}

Provide a structured summary of the key findings."""

    # Call Claude via MCP
    claude_result = await mcp.call(
        server="claude",
        tool="claude_generate",
        arguments={
            "prompt": user_prompt,
            "system_prompt": system_prompt,
            "workspace_path": workspace_path,
            "agent_name": "research",
            "temperature": 0.3,
            "max_tokens": 4096,
            "tools": ["Read", "Bash"]
        }
    )

    analysis = ""
    if claude_result.get("success"):
        analysis = claude_result.get("content", "")
    else:
        analysis = f"Analysis failed: {claude_result.get('error', 'Unknown error')}"

    logger.info(f"✅ Analysis complete: {len(analysis)} chars")

    # Step 3: Create research report
    report = f"""# Research Report

**Query:** {state['query']}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Mode:** research (web search)

## Analysis

{analysis}

## Raw Search Results

{search_findings[:500]}...

---
*Generated by Research Agent v6.2 (research mode) via MCP*
"""

    findings = {
        "analysis": analysis,
        "raw_results": search_findings,
        "timestamp": datetime.now().isoformat(),
        "mode": "research"
    }

    # Step 4: Store in Memory (via MCP!)
    if memory:
        logger.info("💾 Storing findings in Memory via MCP...")
        await mcp.call(
            server="memory",
            tool="store_memory",
            arguments={
                "workspace_path": workspace_path,
                "content": analysis,
                "metadata": {
                    "agent": "research",
                    "type": "findings",
                    "mode": "research",
                    "query": state['query'],
                    "timestamp": findings["timestamp"]
                }
            }
        )

    return {"findings": findings, "report": report}
```

**APPLY SIMILAR CHANGES to:**
- `research_explain_mode()` (lines 155-277)
- `research_analyze_mode()` (lines 280-405)

**UPDATE `create_research_subgraph()` signature (line 412):**

```python
def create_research_subgraph(
    workspace_path: str,
    mcp: MCPClient,  # ← NEW! MCP client instead of memory
    hitl_callback: Any | None = None
) -> Any:
```

---

#### Step 3.2: Update Architect Subgraph

**File:** `/Users/dominikfoert/git/KI_AutoAgent/backend/subgraphs/architect_subgraph_v6_1.py`

**Changes:**

1. **Remove direct Claude CLI import:**
```python
# DELETE THIS:
from adapters.claude_cli_simple import ClaudeCLISimple
```

2. **Add MCP client import:**
```python
# ADD THIS:
from mcp.mcp_client import MCPClient
```

3. **Update `architect_node()` to use MCP:**

```python
async def architect_node(state: ArchitectState) -> ArchitectState:
    """Architect node - Design system architecture via MCP"""

    logger.info(f"🏗️ Architect designing: {state.get('requirements', 'N/A')}")

    # Get MCP client from state
    mcp: MCPClient = state.get("mcp_client")
    workspace_path = state.get("workspace_path", "")

    try:
        # Build prompt
        system_prompt = """You are a software architect..."""
        user_prompt = f"""Design architecture for: {state.get('requirements')}"""

        # Call Claude via MCP (no direct ClaudeCLISimple!)
        result = await mcp.call(
            server="claude",
            tool="claude_generate",
            arguments={
                "prompt": user_prompt,
                "system_prompt": system_prompt,
                "workspace_path": workspace_path,
                "agent_name": "architect",
                "temperature": 0.3,
                "max_tokens": 8192,
                "tools": ["Read", "Bash"]
            }
        )

        if result.get("success"):
            design = result.get("content", "")

            # Store in memory via MCP
            await mcp.call(
                server="memory",
                tool="store_memory",
                arguments={
                    "workspace_path": workspace_path,
                    "content": design,
                    "metadata": {
                        "agent": "architect",
                        "type": "design"
                    }
                }
            )

            return {
                **state,
                "design": design,
                "errors": []
            }
        else:
            raise Exception(result.get("error", "Unknown error"))

    except Exception as e:
        logger.error(f"❌ Architect failed: {e}")
        return {
            **state,
            "design": "",
            "errors": [{"error": str(e), "node": "architect"}]
        }
```

---

#### Step 3.3: Update Codesmith Subgraph

**File:** `/Users/dominikfoert/git/KI_AutoAgent/backend/subgraphs/codesmith_subgraph_v6_1.py`

**Changes:**

1. **Replace ClaudeCLISimple with MCP:**

```python
async def codesmith_node(state: CodesmithState) -> CodesmithState:
    """Codesmith node - Generate code via MCP"""

    logger.info("⚙️ Codesmith generating code...")

    mcp: MCPClient = state.get("mcp_client")
    workspace_path = state.get("workspace_path", "")

    try:
        # Build prompt with FILE: format instructions
        system_prompt = """You are a code generator.
CRITICAL: START YOUR RESPONSE WITH 'FILE:' immediately!
Format: FILE: path
```language
code
```
NO explanations!"""

        user_prompt = f"""Generate code for:

**Design:**
{state.get('design', '')}

**Requirements:**
{state.get('requirements', '')}

Generate ALL necessary files using the FILE: format."""

        # Call Claude via MCP
        result = await mcp.call(
            server="claude",
            tool="claude_generate",
            arguments={
                "prompt": user_prompt,
                "system_prompt": system_prompt,
                "workspace_path": workspace_path,
                "agent_name": "codesmith",
                "temperature": 0.2,
                "max_tokens": 16384,
                "tools": ["Read", "Edit", "Bash"]
            },
            timeout=900  # 15 min timeout for code generation
        )

        if result.get("success"):
            code = result.get("content", "")
            files_created = result.get("files_created", [])

            logger.info(f"✅ Code generated: {len(files_created)} files")

            return {
                **state,
                "code": code,
                "files_generated": files_created,
                "errors": []
            }
        else:
            raise Exception(result.get("error", "Unknown error"))

    except Exception as e:
        logger.error(f"❌ Codesmith failed: {e}")
        return {
            **state,
            "code": "",
            "files_generated": [],
            "errors": [{"error": str(e), "node": "codesmith"}]
        }
```

---

#### Step 3.4: Update ReviewFix Subgraph

**File:** `/Users/dominikfoert/git/KI_AutoAgent/backend/subgraphs/reviewfix_subgraph_v6_1.py`

**Changes:**

1. **Replace ClaudeCLISimple with MCP for reviewer:**

```python
async def reviewer_node(state: ReviewFixState) -> ReviewFixState:
    """Reviewer node - Review code via MCP"""

    logger.info("🔍 Reviewer analyzing code...")

    mcp: MCPClient = state.get("mcp_client")
    workspace_path = state.get("workspace_path", "")

    try:
        # Build review prompt
        system_prompt = """You are a code reviewer..."""
        user_prompt = f"""Review the following generated code..."""

        # Call Claude via MCP
        result = await mcp.call(
            server="claude",
            tool="claude_generate",
            arguments={
                "prompt": user_prompt,
                "system_prompt": system_prompt,
                "workspace_path": workspace_path,
                "agent_name": "reviewer",
                "temperature": 0.2,
                "max_tokens": 8192,
                "tools": ["Read", "Bash"]
            }
        )

        if result.get("success"):
            review = result.get("content", "")

            # Run build validation (still uses subprocess directly)
            build_passed, build_errors = await run_build_validation(
                workspace_path=workspace_path,
                generated_files=state.get("files_generated", [])
            )

            # Calculate quality score
            quality_score = calculate_quality_score(review)

            if not build_passed:
                quality_score = 0.50  # Force iteration
                review += "\n\n## Build Validation Errors\n\n" + format_build_errors(build_errors)

            return {
                **state,
                "review": review,
                "quality_score": quality_score,
                "build_passed": build_passed,
                "errors": [] if build_passed else build_errors
            }
        else:
            raise Exception(result.get("error", "Unknown error"))

    except Exception as e:
        logger.error(f"❌ Reviewer failed: {e}")
        return {
            **state,
            "review": "",
            "quality_score": 0.0,
            "build_passed": False,
            "errors": [{"error": str(e), "node": "reviewer"}]
        }
```

2. **Keep fixer_node similar (also use MCP)**

---

### Phase 4: Update Workflow Orchestrator (2 hours)

#### Step 4.1: Integrate MCP Client in Workflow

**File:** `/Users/dominikfoert/git/KI_AutoAgent/backend/workflow_v6_integrated.py`

**Changes:**

1. **Add MCP client initialization (line ~100):**

```python
from mcp.mcp_client import MCPClient, MCPConnectionError

class WorkflowV6Integrated:
    """Main workflow orchestrator with MCP integration"""

    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path

        # Initialize MCP client (CRITICAL!)
        self.mcp: MCPClient | None = None

        # ... rest of __init__

    async def initialize(self) -> None:
        """Initialize workflow and MCP connections"""
        logger.info("🚀 Initializing WorkflowV6Integrated...")

        # Initialize MCP client
        logger.info("📡 Initializing MCP client...")
        try:
            self.mcp = MCPClient(
                workspace_path=self.workspace_path,
                servers=["perplexity", "memory", "tree-sitter", "asimov", "workflow", "claude"],
                auto_reconnect=True,
                timeout=30.0
            )
            await self.mcp.initialize()
            logger.info("✅ MCP client initialized with 6 servers")
        except MCPConnectionError as e:
            logger.error(f"❌ MCP initialization failed: {e}")
            raise RuntimeError(f"Cannot start workflow without MCP: {e}")

        # Initialize memory
        self.memory = MemorySystem(self.workspace_path)
        await self.memory.initialize()

        logger.info("✅ Workflow initialized")
```

2. **Pass MCP client to subgraphs (line ~700):**

```python
async def execute_workflow(self, user_query: str) -> dict[str, Any]:
    """Execute full workflow with MCP"""

    # ... query classification, planning ...

    # Create subgraphs WITH MCP CLIENT
    research_graph = create_research_subgraph(
        workspace_path=self.workspace_path,
        mcp=self.mcp,  # ← Pass MCP client!
        hitl_callback=self.hitl_callback
    )

    architect_graph = create_architect_subgraph(
        workspace_path=self.workspace_path,
        mcp=self.mcp,  # ← Pass MCP client!
        hitl_callback=self.hitl_callback
    )

    codesmith_graph = create_codesmith_subgraph(
        workspace_path=self.workspace_path,
        mcp=self.mcp,  # ← Pass MCP client!
        hitl_callback=self.hitl_callback
    )

    reviewfix_graph = create_reviewfix_subgraph(
        workspace_path=self.workspace_path,
        mcp=self.mcp,  # ← Pass MCP client!
        hitl_callback=self.hitl_callback
    )

    # Execute agents WITH MCP
    # ... rest of execution logic ...
```

3. **Update state propagation to include mcp_client:**

```python
# Research input
research_input = {
    "query": user_query,
    "workspace_path": self.workspace_path,
    "mode": research_mode,
    "mcp_client": self.mcp,  # ← NEW!
    "findings": {},
    "sources": [],
    "report": "",
    "errors": []
}

# Similar for architect, codesmith, reviewfix states
```

4. **Add cleanup on workflow completion:**

```python
async def cleanup(self) -> None:
    """Cleanup resources"""
    logger.info("🧹 Cleaning up workflow resources...")

    # Close MCP connections
    if self.mcp:
        await self.mcp.close()
        logger.info("✅ MCP connections closed")

    # Close memory
    if self.memory:
        await self.memory.close()
        logger.info("✅ Memory closed")

    logger.info("✅ Workflow cleanup complete")
```

---

### Phase 5: Restore HITL Manager (1 hour)

#### Step 5.1: Restore from Git

**Command:**
```bash
cd /Users/dominikfoert/git/KI_AutoAgent

# Find the commit where HITL manager was deleted
git log --all --full-history -- "**/hitl_manager*"

# Restore from commit 1810fdd
git show 1810fdd:backend/workflow/hitl_manager_v6.py > backend/workflow/hitl_manager_v6.py

# Verify restoration
ls -lh backend/workflow/hitl_manager_v6.py
wc -l backend/workflow/hitl_manager_v6.py  # Should show ~626 lines
```

#### Step 5.2: Update HITL Manager for MCP

**File:** `/Users/dominikfoert/git/KI_AutoAgent/backend/workflow/hitl_manager_v6.py`

**Add MCP support:**

```python
# Add at top of file
from mcp.mcp_client import MCPClient

class HITLManagerV6:
    """HITL Manager with MCP integration"""

    def __init__(
        self,
        workspace_path: str,
        mcp: MCPClient,  # ← NEW!
        websocket: Any | None = None
    ):
        self.workspace_path = workspace_path
        self.mcp = mcp  # ← Store MCP client
        self.websocket = websocket

        # ... rest of __init__

    async def execute_with_tracking(
        self,
        agent_name: str,
        task_description: str,
        tool_calls: list[tuple[str, str, dict]]  # ← NEW! MCP calls
    ) -> dict[str, Any]:
        """
        Execute agent task with progress tracking via MCP.

        Args:
            agent_name: Name of agent (research, architect, etc.)
            task_description: Human-readable task description
            tool_calls: List of (server, tool, arguments) tuples for MCP

        Returns:
            Execution results
        """
        logger.info(f"🚀 Executing {agent_name}: {task_description}")

        # Send start event
        await self._send_progress_event({
            "type": "agent_start",
            "agent": agent_name,
            "task": task_description,
            "timestamp": datetime.now().isoformat()
        })

        try:
            # Execute ALL tool calls in parallel via MCP
            results = await self.mcp.call_multiple(tool_calls)

            # Send completion event
            await self._send_progress_event({
                "type": "agent_complete",
                "agent": agent_name,
                "task": task_description,
                "results_count": len(results),
                "timestamp": datetime.now().isoformat()
            })

            return {
                "success": True,
                "results": results
            }

        except Exception as e:
            logger.error(f"❌ {agent_name} failed: {e}")

            # Send error event
            await self._send_progress_event({
                "type": "agent_error",
                "agent": agent_name,
                "task": task_description,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

            return {
                "success": False,
                "error": str(e)
            }
```

---

## 3. Test Strategy

### 3.1 Test File Structure

```
backend/tests/
├── unit/                          # Unit tests (isolated)
│   ├── test_mcp_client.py         # MCP client unit tests
│   ├── test_mcp_perplexity.py     # Perplexity MCP server tests
│   ├── test_mcp_memory.py         # Memory MCP server tests
│   ├── test_mcp_claude.py         # Claude CLI MCP server tests
│   └── test_hitl_manager.py       # HITL manager tests
│
├── integration/                   # Integration tests (multi-component)
│   ├── test_mcp_parallel.py       # Parallel MCP execution tests
│   ├── test_research_mcp.py       # Research subgraph with MCP
│   ├── test_architect_mcp.py      # Architect subgraph with MCP
│   ├── test_codesmith_mcp.py      # Codesmith subgraph with MCP
│   └── test_reviewfix_mcp.py      # ReviewFix subgraph with MCP
│
└── e2e/                           # End-to-end tests (full workflow)
    ├── test_workflow_mcp.py       # Complete workflow with MCP
    ├── test_performance_mcp.py    # Performance benchmarks (3 min target)
    └── test_error_recovery_mcp.py # Error handling and partial results
```

### 3.2 Unit Tests

#### Test 1: MCP Client Initialization

**File:** `/Users/dominikfoert/git/KI_AutoAgent/backend/tests/unit/test_mcp_client.py`

```python
"""
Unit tests for MCP Client

Tests:
1. Initialization
2. Server connection
3. Tool calling
4. Parallel execution
5. Error handling
6. Reconnection logic
"""

import pytest
import asyncio
from pathlib import Path
from mcp.mcp_client import MCPClient, MCPConnectionError, MCPToolError


@pytest.fixture
async def mcp_client():
    """Create MCP client for testing"""
    workspace = Path("/tmp/test_workspace")
    workspace.mkdir(exist_ok=True)

    client = MCPClient(
        workspace_path=str(workspace),
        servers=["memory"],  # Only test memory server (always available)
        timeout=10.0
    )

    await client.initialize()
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_mcp_client_initialization():
    """Test MCP client initializes successfully"""
    workspace = Path("/tmp/test_workspace")
    workspace.mkdir(exist_ok=True)

    client = MCPClient(
        workspace_path=str(workspace),
        servers=["memory"]
    )

    # Should start uninitialized
    assert not client._initialized

    # Initialize
    await client.initialize()

    # Should be initialized
    assert client._initialized
    assert "memory" in client._connections
    assert client._connections["memory"]["status"] == "connected"

    # Cleanup
    await client.close()


@pytest.mark.asyncio
async def test_mcp_client_missing_server():
    """Test MCP client handles missing server gracefully"""
    workspace = Path("/tmp/test_workspace")
    workspace.mkdir(exist_ok=True)

    client = MCPClient(
        workspace_path=str(workspace),
        servers=["nonexistent_server"]
    )

    # Should raise MCPConnectionError
    with pytest.raises(MCPConnectionError) as exc_info:
        await client.initialize()

    assert "Failed to connect" in str(exc_info.value)


@pytest.mark.asyncio
async def test_mcp_single_call(mcp_client):
    """Test single MCP tool call"""
    result = await mcp_client.call(
        server="memory",
        tool="count_memory",
        arguments={}
    )

    # Should return successful result
    assert "success" in result
    assert "count" in result or "content" in result


@pytest.mark.asyncio
async def test_mcp_parallel_calls(mcp_client):
    """Test parallel MCP tool calls"""
    # Execute 3 calls in parallel
    results = await mcp_client.call_multiple([
        ("memory", "count_memory", {}),
        ("memory", "count_memory", {}),
        ("memory", "count_memory", {})
    ])

    # All 3 should succeed
    assert len(results) == 3

    # None should be exceptions (all succeed)
    errors = [r for r in results if isinstance(r, Exception)]
    assert len(errors) == 0


@pytest.mark.asyncio
async def test_mcp_call_without_initialization():
    """Test MCP call fails if not initialized"""
    workspace = Path("/tmp/test_workspace")
    workspace.mkdir(exist_ok=True)

    client = MCPClient(
        workspace_path=str(workspace),
        servers=["memory"]
    )

    # Should raise error if not initialized
    with pytest.raises(MCPConnectionError) as exc_info:
        await client.call("memory", "count_memory", {})

    assert "not initialized" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_mcp_timeout():
    """Test MCP call respects timeout"""
    workspace = Path("/tmp/test_workspace")
    workspace.mkdir(exist_ok=True)

    client = MCPClient(
        workspace_path=str(workspace),
        servers=["memory"],
        timeout=0.001  # 1ms timeout (too short)
    )

    await client.initialize()

    # Should timeout
    with pytest.raises(MCPConnectionError) as exc_info:
        await client.call("memory", "count_memory", {})

    assert "timeout" in str(exc_info.value).lower()

    await client.close()


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
```

**Run Command:**
```bash
cd /Users/dominikfoert/git/KI_AutoAgent
pytest backend/tests/unit/test_mcp_client.py -v
```

**Expected Output:**
```
test_mcp_client.py::test_mcp_client_initialization PASSED
test_mcp_client.py::test_mcp_client_missing_server PASSED
test_mcp_client.py::test_mcp_single_call PASSED
test_mcp_client.py::test_mcp_parallel_calls PASSED
test_mcp_client.py::test_mcp_call_without_initialization PASSED
test_mcp_client.py::test_mcp_timeout PASSED

====== 6 passed in 5.23s ======
```

---

#### Test 2: MCP Perplexity Server

**File:** `/Users/dominikfoert/git/KI_AutoAgent/backend/tests/unit/test_mcp_perplexity.py`

```python
"""
Unit tests for Perplexity MCP Server

Tests:
1. Search tool
2. Result formatting
3. Error handling
4. Citation extraction
"""

import pytest
from mcp.mcp_client import MCPClient
from pathlib import Path


@pytest.fixture
async def mcp_client():
    """Create MCP client with perplexity server"""
    workspace = Path("/tmp/test_workspace")
    workspace.mkdir(exist_ok=True)

    client = MCPClient(
        workspace_path=str(workspace),
        servers=["perplexity"],
        timeout=30.0
    )

    await client.initialize()
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_perplexity_search(mcp_client):
    """Test Perplexity search via MCP"""
    result = await mcp_client.call(
        server="perplexity",
        tool="perplexity_search",
        arguments={
            "query": "Python async best practices 2025",
            "max_results": 3
        }
    )

    # Should return content blocks
    assert "content" in result

    # Extract text from content blocks
    content_blocks = result.get("content", [])
    assert len(content_blocks) > 0

    # First block should be text
    assert content_blocks[0]["type"] == "text"
    text = content_blocks[0]["text"]

    # Should contain search results
    assert "Python" in text or "async" in text

    # Should contain sources
    assert "Sources:" in text or "Retrieved:" in text


@pytest.mark.asyncio
async def test_perplexity_empty_query(mcp_client):
    """Test Perplexity handles empty query gracefully"""
    result = await mcp_client.call(
        server="perplexity",
        tool="perplexity_search",
        arguments={
            "query": "",
            "max_results": 5
        }
    )

    # Should return error or empty result
    # (depends on implementation)
    assert "content" in result or "error" in result


@pytest.mark.asyncio
async def test_perplexity_parallel_searches(mcp_client):
    """Test multiple Perplexity searches in parallel"""
    results = await mcp_client.call_multiple([
        ("perplexity", "perplexity_search", {"query": "React 19", "max_results": 2}),
        ("perplexity", "perplexity_search", {"query": "Vue 3", "max_results": 2}),
        ("perplexity", "perplexity_search", {"query": "Angular 18", "max_results": 2})
    ])

    # All 3 should complete
    assert len(results) == 3

    # Check for errors
    errors = [r for r in results if isinstance(r, Exception)]
    assert len(errors) == 0, f"Some searches failed: {errors}"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
```

**Run Command:**
```bash
pytest backend/tests/unit/test_mcp_perplexity.py -v
```

**Expected Output:**
```
test_mcp_perplexity.py::test_perplexity_search PASSED
test_mcp_perplexity.py::test_perplexity_empty_query PASSED
test_mcp_perplexity.py::test_perplexity_parallel_searches PASSED

====== 3 passed in 12.45s ======
```

---

#### Test 3: MCP Memory Server

**File:** `/Users/dominikfoert/git/KI_AutoAgent/backend/tests/unit/test_mcp_memory.py`

```python
"""
Unit tests for Memory MCP Server

Tests:
1. Store memory
2. Search memory
3. Get statistics
4. Count items
"""

import pytest
from mcp.mcp_client import MCPClient
from pathlib import Path


@pytest.fixture
async def mcp_client():
    """Create MCP client with memory server"""
    workspace = Path("/tmp/test_workspace_memory")
    workspace.mkdir(exist_ok=True)

    client = MCPClient(
        workspace_path=str(workspace),
        servers=["memory"],
        timeout=10.0
    )

    await client.initialize()
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_memory_store(mcp_client):
    """Test storing memory via MCP"""
    result = await mcp_client.call(
        server="memory",
        tool="store_memory",
        arguments={
            "content": "React 18 + Vite is recommended for new projects",
            "metadata": {
                "agent": "research",
                "type": "technology"
            }
        }
    )

    # Extract from content blocks
    content_blocks = result.get("content", [])
    assert len(content_blocks) > 0

    text = content_blocks[0]["text"]

    # Should contain success indicator
    assert "success" in text.lower() or "stored" in text.lower()


@pytest.mark.asyncio
async def test_memory_count(mcp_client):
    """Test counting memory items via MCP"""
    result = await mcp_client.call(
        server="memory",
        tool="count_memory",
        arguments={}
    )

    # Extract from content blocks
    content_blocks = result.get("content", [])
    assert len(content_blocks) > 0

    text = content_blocks[0]["text"]

    # Should contain count
    assert "count" in text.lower()


@pytest.mark.asyncio
async def test_memory_search(mcp_client):
    """Test searching memory via MCP"""
    # First, store something
    await mcp_client.call(
        server="memory",
        tool="store_memory",
        arguments={
            "content": "TypeScript with strict mode enabled",
            "metadata": {
                "agent": "architect",
                "type": "design"
            }
        }
    )

    # Then search
    result = await mcp_client.call(
        server="memory",
        tool="search_memory",
        arguments={
            "query": "TypeScript configuration",
            "k": 5
        }
    )

    # Should return results
    content_blocks = result.get("content", [])
    assert len(content_blocks) > 0


@pytest.mark.asyncio
async def test_memory_stats(mcp_client):
    """Test getting memory statistics via MCP"""
    result = await mcp_client.call(
        server="memory",
        tool="get_memory_stats",
        arguments={}
    )

    # Should return stats
    content_blocks = result.get("content", [])
    assert len(content_blocks) > 0

    text = content_blocks[0]["text"]

    # Should contain statistics
    assert "total" in text.lower() or "stats" in text.lower()


@pytest.mark.asyncio
async def test_memory_parallel_operations(mcp_client):
    """Test parallel memory operations"""
    results = await mcp_client.call_multiple([
        ("memory", "store_memory", {
            "content": "Vue 3 Composition API",
            "metadata": {"agent": "research", "type": "technology"}
        }),
        ("memory", "store_memory", {
            "content": "Microservices architecture pattern",
            "metadata": {"agent": "architect", "type": "design"}
        }),
        ("memory", "count_memory", {})
    ])

    # All should succeed
    assert len(results) == 3

    errors = [r for r in results if isinstance(r, Exception)]
    assert len(errors) == 0


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
```

**Run Command:**
```bash
pytest backend/tests/unit/test_mcp_memory.py -v
```

**Expected Output:**
```
test_mcp_memory.py::test_memory_store PASSED
test_mcp_memory.py::test_memory_count PASSED
test_mcp_memory.py::test_memory_search PASSED
test_mcp_memory.py::test_memory_stats PASSED
test_mcp_memory.py::test_memory_parallel_operations PASSED

====== 5 passed in 8.12s ======
```

---

### 3.3 Integration Tests

#### Test 4: Research Subgraph with MCP

**File:** `/Users/dominikfoert/git/KI_AutoAgent/backend/tests/integration/test_research_mcp.py`

```python
"""
Integration test for Research Subgraph with MCP

Tests:
1. Research mode (web search)
2. Explain mode (codebase analysis)
3. Analyze mode (code quality)
4. Parallel MCP calls during research
"""

import pytest
import asyncio
from pathlib import Path
from mcp.mcp_client import MCPClient
from subgraphs.research_subgraph_v6_1 import create_research_subgraph


@pytest.fixture
async def mcp_client():
    """Create MCP client for testing"""
    workspace = Path("/tmp/test_workspace_research")
    workspace.mkdir(exist_ok=True)

    client = MCPClient(
        workspace_path=str(workspace),
        servers=["perplexity", "memory", "claude"],
        timeout=60.0
    )

    await client.initialize()
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_research_mode(mcp_client):
    """Test research subgraph in research mode"""
    workspace = Path("/tmp/test_workspace_research")

    # Create research subgraph
    graph = create_research_subgraph(
        workspace_path=str(workspace),
        mcp=mcp_client,
        hitl_callback=None
    )

    # Execute research
    result = await graph.ainvoke({
        "query": "React 19 new features",
        "workspace_path": str(workspace),
        "mode": "research",
        "findings": {},
        "sources": [],
        "report": "",
        "errors": []
    })

    # Should return report
    assert "report" in result
    assert len(result["report"]) > 100

    # Should have findings
    assert "findings" in result
    assert "analysis" in result["findings"]

    # Should have no errors
    assert len(result.get("errors", [])) == 0


@pytest.mark.asyncio
async def test_research_parallel_calls(mcp_client):
    """Test research makes parallel MCP calls"""
    workspace = Path("/tmp/test_workspace_research")

    # Monitor MCP call timing
    start = asyncio.get_event_loop().time()

    graph = create_research_subgraph(
        workspace_path=str(workspace),
        mcp=mcp_client,
        hitl_callback=None
    )

    result = await graph.ainvoke({
        "query": "Python async patterns",
        "workspace_path": str(workspace),
        "mode": "research",
        "findings": {},
        "sources": [],
        "report": "",
        "errors": []
    })

    end = asyncio.get_event_loop().time()
    duration = end - start

    # Should complete in <30s (parallel execution)
    # If sequential, would take ~60s (Perplexity 30s + Claude 30s)
    assert duration < 45, f"Research took {duration}s (should be <45s with parallelization)"

    # Should have results
    assert "report" in result
    assert len(result["report"]) > 100


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
```

**Run Command:**
```bash
pytest backend/tests/integration/test_research_mcp.py -v
```

**Expected Output:**
```
test_research_mcp.py::test_research_mode PASSED
test_research_mcp.py::test_research_parallel_calls PASSED

====== 2 passed in 35.67s ======
```

---

### 3.4 End-to-End Tests

#### Test 5: Complete Workflow Performance

**File:** `/Users/dominikfoert/git/KI_AutoAgent/backend/tests/e2e/test_performance_mcp.py`

```python
"""
E2E Performance Test - Full Workflow with MCP

Target: Complete workflow in 180 seconds (3 minutes)

Workflow:
- Research (web search): 30s
- Architect (design): 60s
- Codesmith (code generation): 150s
- ReviewFix (review + validation): 180s

Total: 180s (with parallel execution)
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime
from mcp.mcp_client import MCPClient
from workflow_v6_integrated import WorkflowV6Integrated


@pytest.mark.asyncio
@pytest.mark.slow
async def test_workflow_performance_target():
    """
    Test complete workflow completes in <180s (3 minutes).

    This is the CRITICAL performance test!
    """
    workspace = Path("/tmp/test_workspace_e2e")
    workspace.mkdir(exist_ok=True)

    # Create workflow
    workflow = WorkflowV6Integrated(workspace_path=str(workspace))
    await workflow.initialize()

    # Start timer
    start = datetime.now()
    print(f"\n🚀 Starting workflow at {start}")

    try:
        # Execute workflow
        result = await workflow.execute_workflow(
            user_query="Create a simple Task Manager app with React"
        )

        # End timer
        end = datetime.now()
        duration = (end - start).total_seconds()

        print(f"\n✅ Workflow completed at {end}")
        print(f"⏱️  Total duration: {duration:.1f}s ({duration/60:.1f} minutes)")

        # Performance assertion
        assert duration < 180, f"Workflow took {duration}s (target: <180s)"

        # Success assertion
        assert result.get("status") == "completed"
        assert len(result.get("errors", [])) == 0

        print(f"\n🎯 Performance target MET: {duration:.1f}s / 180s")

    finally:
        await workflow.cleanup()


@pytest.mark.asyncio
@pytest.mark.slow
async def test_workflow_parallelization():
    """
    Test workflow actually uses parallel execution.

    Measures time for individual agents vs. total time.
    """
    workspace = Path("/tmp/test_workspace_parallel")
    workspace.mkdir(exist_ok=True)

    workflow = WorkflowV6Integrated(workspace_path=str(workspace))
    await workflow.initialize()

    # Track agent timings
    agent_timings = {}

    # Hook to measure agent execution times
    original_execute = workflow.execute_workflow

    async def timed_execute(query):
        # ... measure individual agent times ...
        return await original_execute(query)

    workflow.execute_workflow = timed_execute

    start = datetime.now()
    result = await workflow.execute_workflow(
        user_query="Create a simple counter app"
    )
    end = datetime.now()
    total_duration = (end - start).total_seconds()

    await workflow.cleanup()

    # Calculate sum of individual agent times
    agent_sum = sum(agent_timings.values())

    # If truly parallel, total_duration should be < agent_sum
    parallelization_factor = agent_sum / total_duration

    print(f"\n📊 Parallelization Analysis:")
    print(f"   Total workflow time: {total_duration:.1f}s")
    print(f"   Sum of agent times: {agent_sum:.1f}s")
    print(f"   Parallelization factor: {parallelization_factor:.2f}x")

    # Should have >1.5x parallelization
    assert parallelization_factor > 1.5, \
        f"Low parallelization: {parallelization_factor:.2f}x (expected >1.5x)"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "slow"])
```

**Run Command:**
```bash
pytest backend/tests/e2e/test_performance_mcp.py -v -s -m slow
```

**Expected Output:**
```
test_performance_mcp.py::test_workflow_performance_target
🚀 Starting workflow at 2025-10-13 14:30:00
✅ Workflow completed at 2025-10-13 14:32:47
⏱️  Total duration: 167.3s (2.8 minutes)
🎯 Performance target MET: 167.3s / 180s
PASSED

test_performance_mcp.py::test_workflow_parallelization
📊 Parallelization Analysis:
   Total workflow time: 165.2s
   Sum of agent times: 420.5s
   Parallelization factor: 2.55x
PASSED

====== 2 passed in 332.50s (5.54 minutes) ======
```

---

### 3.5 Test Suite Summary

**Total Tests:** 16 test files, ~80 individual tests

**Coverage:**
- Unit tests: 6 files (MCP client, servers, HITL)
- Integration tests: 4 files (subgraphs with MCP)
- E2E tests: 3 files (full workflow, performance, error recovery)

**Run All Tests:**
```bash
cd /Users/dominikfoert/git/KI_AutoAgent

# Run all unit tests (fast)
pytest backend/tests/unit/ -v

# Run all integration tests (medium)
pytest backend/tests/integration/ -v

# Run all E2E tests (slow)
pytest backend/tests/e2e/ -v -m slow

# Run everything
pytest backend/tests/ -v
```

**Expected Total Duration:**
- Unit tests: 30-60s
- Integration tests: 2-3 min
- E2E tests: 10-15 min
- **Total: ~20 minutes for full test suite**

---

## 4. Migration Checklist

### Pre-Migration Validation

- [ ] **Backup current state**
  ```bash
  git checkout -b backup-pre-mcp-migration
  git add -A
  git commit -m "Backup before MCP migration"
  git push origin backup-pre-mcp-migration
  ```

- [ ] **Verify MCP servers exist**
  ```bash
  ls -lh mcp_servers/*.py
  # Should show: perplexity, memory, tree-sitter, asimov, workflow servers
  ```

- [ ] **Verify backend venv**
  ```bash
  ls -lh backend/venv_v6/bin/python
  # Should exist
  ```

- [ ] **Test Claude CLI**
  ```bash
  claude --version
  # Should show version 2.0.13 or later
  ```

### Migration Execution

- [ ] **Phase 1: Fix MCP Registration (30 min)**
  - [ ] Update install_mcp.sh with correct Python paths
  - [ ] Create claude_cli_server.py
  - [ ] Run ./install_mcp.sh
  - [ ] Verify: `claude mcp list` shows 6 connected servers

- [ ] **Phase 2: Create MCP Client (2 hours)**
  - [ ] Create backend/mcp/mcp_client.py
  - [ ] Create backend/mcp/__init__.py
  - [ ] Test: Run unit test test_mcp_client.py
  - [ ] Verify: All 6 tests pass

- [ ] **Phase 3: Convert Direct Calls (4 hours)**
  - [ ] Update research_subgraph_v6_1.py (use MCP)
  - [ ] Update architect_subgraph_v6_1.py (use MCP)
  - [ ] Update codesmith_subgraph_v6_1.py (use MCP)
  - [ ] Update reviewfix_subgraph_v6_1.py (use MCP)
  - [ ] Test: Run integration tests for each subgraph
  - [ ] Verify: No more direct PerplexityService or ClaudeCLISimple imports

- [ ] **Phase 4: Update Workflow (2 hours)**
  - [ ] Add MCP client initialization to workflow_v6_integrated.py
  - [ ] Pass MCP client to all subgraphs
  - [ ] Add cleanup logic
  - [ ] Test: Run test_workflow_mcp.py
  - [ ] Verify: Workflow uses MCP for all operations

- [ ] **Phase 5: Restore HITL (1 hour)**
  - [ ] Restore hitl_manager_v6.py from git
  - [ ] Update for MCP integration
  - [ ] Test: Run test_hitl_manager.py
  - [ ] Verify: HITL manager works with MCP

- [ ] **Phase 6: Delete Obsolete Code (30 min)**
  - [ ] Delete all files listed in section 7 below
  - [ ] Verify: `git status` shows deletions
  - [ ] Commit: "chore: Remove obsolete direct-call code"

### Post-Migration Validation

- [ ] **Run full test suite**
  ```bash
  pytest backend/tests/ -v
  # Expected: 100% pass rate
  ```

- [ ] **Performance test**
  ```bash
  pytest backend/tests/e2e/test_performance_mcp.py -v -s -m slow
  # Expected: <180s workflow duration
  ```

- [ ] **E2E smoke test**
  ```bash
  pytest backend/tests/e2e/test_workflow_mcp.py -v -s
  # Expected: Complete workflow execution
  ```

- [ ] **Manual verification**
  - [ ] Start backend: `python backend/api/server_v6_integrated.py`
  - [ ] Connect via WebSocket
  - [ ] Send test query: "Create a simple todo app"
  - [ ] Verify: Completes in <3 minutes
  - [ ] Verify: All agents use MCP (check logs for "MCP call to...")

### Rollback Plan (If Needed)

If migration fails:

```bash
# Restore from backup
git checkout backup-pre-mcp-migration

# Verify system works
pytest backend/tests/test_simple_websocket.py -v

# Document what went wrong
# Create GitHub issue with error logs
```

---

## 5. Code Examples

### Example 1: Simple MCP Call

```python
from mcp.mcp_client import MCPClient

async def example_simple():
    """Example: Single MCP call"""

    # Initialize
    mcp = MCPClient(workspace_path="/path/to/workspace")
    await mcp.initialize()

    # Single call
    result = await mcp.call(
        server="perplexity",
        tool="perplexity_search",
        arguments={
            "query": "Python async patterns",
            "max_results": 5
        }
    )

    print("Search result:", result)

    # Cleanup
    await mcp.close()
```

### Example 2: Parallel MCP Calls

```python
from mcp.mcp_client import MCPClient
import asyncio

async def example_parallel():
    """Example: Parallel MCP calls (KEY TO PERFORMANCE!)"""

    mcp = MCPClient(workspace_path="/path/to/workspace")
    await mcp.initialize()

    # Execute 5 calls in parallel
    results = await mcp.call_multiple([
        ("perplexity", "perplexity_search", {"query": "React 19"}),
        ("perplexity", "perplexity_search", {"query": "Vue 3"}),
        ("memory", "count_memory", {}),
        ("memory", "search_memory", {"query": "frontend", "k": 3}),
        ("claude", "claude_generate", {"prompt": "Explain MVC", "workspace_path": "/path"})
    ])

    # All 5 completed in parallel!
    # Total time = MAX(individual times), not SUM!

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Call {i} failed: {result}")
        else:
            print(f"Call {i} succeeded: {result}")

    await mcp.close()
```

### Example 3: Agent Using MCP

```python
from mcp.mcp_client import MCPClient
from langgraph.graph import StateGraph

async def research_agent(state: dict, mcp: MCPClient) -> dict:
    """Example: Research agent using MCP"""

    query = state.get("query", "")
    workspace = state.get("workspace_path", "")

    # Step 1: Search (Perplexity)
    search_task = mcp.call("perplexity", "perplexity_search", {"query": query})

    # Step 2: Analyze (Claude)
    analyze_task = mcp.call("claude", "claude_generate", {
        "prompt": f"Analyze this query: {query}",
        "workspace_path": workspace
    })

    # Execute BOTH in parallel
    search_result, analyze_result = await asyncio.gather(search_task, analyze_task)

    # Step 3: Store (Memory)
    await mcp.call("memory", "store_memory", {
        "workspace_path": workspace,
        "content": analyze_result.get("content", ""),
        "metadata": {"agent": "research", "type": "findings"}
    })

    return {
        **state,
        "search_results": search_result,
        "analysis": analyze_result,
        "errors": []
    }
```

### Example 4: Error Handling with MCP

```python
from mcp.mcp_client import MCPClient, MCPToolError
import asyncio

async def example_error_handling():
    """Example: Robust error handling with MCP"""

    mcp = MCPClient(workspace_path="/path")
    await mcp.initialize()

    try:
        # Execute multiple calls
        results = await mcp.call_multiple([
            ("perplexity", "perplexity_search", {"query": "test"}),
            ("memory", "count_memory", {}),
            ("invalid_server", "invalid_tool", {})  # This will fail!
        ])

        # Check for failures
        successes = []
        failures = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failures.append((i, str(result)))
            else:
                successes.append((i, result))

        print(f"✅ {len(successes)} succeeded")
        print(f"❌ {len(failures)} failed")

        # Continue with partial results
        if len(successes) > 0:
            print("Processing successful results...")
            # ... process successes ...

    except Exception as e:
        print(f"❌ Critical error: {e}")
    finally:
        await mcp.close()
```

---

## 6. Performance Targets

### 6.1 Current vs. Target Performance

| Metric | Current (v6.2) | Target (MCP) | Improvement |
|--------|----------------|--------------|-------------|
| **Total Workflow** | 749s (12.5 min) | 180s (3.0 min) | **4.16x faster** |
| **Research Agent** | 45s | 30s | 1.5x faster |
| **Architect Agent** | 135s | 60s | 2.25x faster |
| **Codesmith Agent** | 510s | 150s | 3.4x faster |
| **ReviewFix Agent** | 149s | 180s | 0.83x (acceptable) |
| **Parallelization** | 1.0x (sequential) | 2.8x (parallel) | **2.8x speedup** |

### 6.2 Performance Measurement

**Test Command:**
```bash
cd /Users/dominikfoert/git/KI_AutoAgent

# Run performance test
pytest backend/tests/e2e/test_performance_mcp.py -v -s -m slow

# Should output:
# ⏱️  Total duration: 167.3s (2.8 minutes)
# 🎯 Performance target MET: 167.3s / 180s
```

### 6.3 Performance Monitoring

**Add to workflow:**
```python
import time

class WorkflowV6Integrated:
    async def execute_workflow(self, user_query: str) -> dict:
        """Execute workflow with timing"""

        start = time.time()

        # ... workflow execution ...

        end = time.time()
        duration = end - start

        logger.info(f"⏱️  Workflow completed in {duration:.1f}s")

        # Log performance warning if >180s
        if duration > 180:
            logger.warning(f"⚠️  Performance target missed: {duration:.1f}s (target: <180s)")
        else:
            logger.info(f"✅ Performance target met: {duration:.1f}s / 180s")

        return {
            "status": "completed",
            "duration_seconds": duration,
            "performance_target_met": duration < 180,
            # ... rest of result ...
        }
```

### 6.4 Bottleneck Analysis

**Expected bottlenecks:**
1. **Claude CLI subprocess** - 60-150s per agent
   - Solution: Run multiple agents in parallel via MCP
   - Expected: 2.5x speedup

2. **Perplexity API** - 30s per search
   - Solution: Parallel searches if multiple queries
   - Expected: 1.5x speedup

3. **Memory operations** - 2-5s per operation
   - Solution: Batch operations, parallel stores
   - Expected: Minimal impact (already fast)

**Monitoring command:**
```bash
# Watch logs for timing info
tail -f /tmp/v6_server.log | grep "⏱️"
```

---

## 7. Files to Delete

### 7.1 Direct Service Implementations (OBSOLETE)

```bash
# Delete direct service files
rm backend/utils/perplexity_service.py          # Replaced by perplexity MCP server
rm backend/tools/perplexity_tool.py             # Replaced by MCP calls
```

### 7.2 Old Adapter Files (OBSOLETE)

```bash
# Keep claude_cli_simple.py (used by claude_cli_server.py)
# But delete old wrappers:
rm backend/adapters/use_claude_cli.py           # Obsolete wrapper
```

### 7.3 Obsolete Tests (NO LONGER VALID)

```bash
# Delete tests that test OLD architecture
rm backend/tests/test_simple_websocket.py       # Tests old sequential workflow
rm backend/tests/test_codesmith_direct.py       # Tests direct ClaudeCLISimple usage
rm backend/tests/test_base_agent_communication.py # Tests old agent communication
```

### 7.4 Old Agent Implementations (IF EXIST)

```bash
# Delete old agent files (replaced by subgraphs)
rm -f backend/agents/specialized/research_agent.py  # Old research agent
rm -f agents/specialized/research_agent.py          # Duplicate old agent
```

### 7.5 Verification Commands

**After deletion, verify NO references remain:**

```bash
cd /Users/dominikfoert/git/KI_AutoAgent

# Check for PerplexityService imports (should be ZERO)
grep -r "from utils.perplexity_service import" backend/ || echo "✅ No direct PerplexityService imports"
grep -r "PerplexityService()" backend/ || echo "✅ No direct PerplexityService instantiation"

# Check for direct ClaudeCLISimple imports in subgraphs (should be ZERO)
grep -r "from adapters.claude_cli_simple import" backend/subgraphs/ || echo "✅ No direct ClaudeCLISimple imports in subgraphs"

# Check for perplexity_tool imports (should be ZERO)
grep -r "from tools.perplexity_tool import" backend/ || echo "✅ No perplexity_tool imports"

# Verify MCP client IS imported (should be MANY)
grep -r "from mcp.mcp_client import MCPClient" backend/ | wc -l
# Expected: 5+ imports (subgraphs + workflow)
```

**Expected Output:**
```
✅ No direct PerplexityService imports
✅ No direct PerplexityService instantiation
✅ No direct ClaudeCLISimple imports in subgraphs
✅ No perplexity_tool imports
5 (MCPClient imports found - CORRECT!)
```

### 7.6 Commit Deletion

```bash
# After verification, commit deletions
git add -A
git commit -m "chore: Remove obsolete direct-call code (PerplexityService, perplexity_tool, old tests)

- Deleted backend/utils/perplexity_service.py (replaced by MCP)
- Deleted backend/tools/perplexity_tool.py (replaced by MCP)
- Deleted obsolete test files (test old architecture)
- All functionality now via MCP protocol
- Zero tolerance for direct service calls"
```

---

## 8. Summary

### What This Plan Achieves

1. **Performance:** 316% improvement (12.5 min → 3 min)
2. **Architecture:** Full MCP protocol, zero direct calls
3. **Parallelization:** 2.8x speedup via asyncio.gather()
4. **Test Coverage:** 10% → 100% (16 test files, 80 tests)
5. **Code Quality:** Deleted ALL obsolete code, clean architecture

### Success Criteria

- [ ] All 6 MCP servers connected: `claude mcp list`
- [ ] All 80 tests pass: `pytest backend/tests/ -v`
- [ ] Performance target met: `<180s workflow duration`
- [ ] Zero direct service calls: `grep -r "PerplexityService()" backend/` returns nothing
- [ ] Clean git status: No leftover obsolete files

### Execution Timeline

- **Phase 1 (MCP Registration):** 30 minutes
- **Phase 2 (MCP Client):** 2 hours
- **Phase 3 (Convert Calls):** 4 hours
- **Phase 4 (Update Workflow):** 2 hours
- **Phase 5 (Restore HITL):** 1 hour
- **Phase 6 (Delete Obsolete):** 30 minutes
- **Testing:** 4-6 hours
- **Total:** 14-16 hours

### Next Steps

1. **Review this plan** - Ensure completeness
2. **Create branch:** `git checkout -b feature/mcp-complete-migration`
3. **Execute Phase 1** - Fix MCP registration
4. **Test after each phase** - Incremental validation
5. **Document issues** - Track any blockers
6. **Commit regularly** - Atomic commits per phase
7. **Final validation** - Run full test suite
8. **Create PR** - Merge to v6.2-alpha-release

---

**End of MCP Implementation Plan**

**Author:** KI AutoAgent Team
**Date:** 2025-10-13
**Status:** READY FOR EXECUTION ✅
