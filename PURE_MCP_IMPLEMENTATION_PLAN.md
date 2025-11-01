# Pure MCP Implementation Plan - v7.0 Direct Migration

**Date:** 2025-10-29
**Decision:** DIREKT zu Pure MCP, KEINE Rückwärtskompatibilität
**Mandate:** "MCP BLEIBT" - an mehreren Stellen im Code kommentieren

---

## 🎯 **Zielbild: Pure MCP v7.0**

```
┌─────────────────────────────────────────────────────────────┐
│                    WebSocket Client                         │
│                    (SSE für Events)                         │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ $/progress Notifications
                            │
┌─────────────────────────────────────────────────────────────┐
│              MCPClient (Global Manager)                     │
│  • Verbindet zu ALLEN MCP-Servern                          │
│  • Routet Calls                                            │
│  • Empfängt $/progress                                     │
└─────────────────────────────────────────────────────────────┘
         ▲                  ▲                  ▲
         │                  │                  │
    ┌────┴────┐      ┌──────┴──────┐    ┌─────┴──────┐
    │         │      │             │    │            │
┌───┴────┐ ┌─┴────┐ ┌┴──────────┐ │  ┌─┴──────────┐ │
│Supervisor│ │Research│ │Architect│ │  │Codesmith  │ │
│MCP Server│ │MCP Srv│ │MCP Srv  │ │  │MCP Server │ │
│(GPT-4o)  │ │(Perplx)│ │(GPT-4o) │ │  │(Claude)   │ │
└──────────┘ └───────┘ └─────────┘ │  └───────────┘ │
                                   │               │
                            ┌──────┴────────┐ ┌────┴──────┐
                            │ReviewFix      │ │Responder   │
                            │MCP Server     │ │MCP Server  │
                            │(Claude)       │ │(GPT-4o)    │
                            └───────────────┘ └────────────┘

❌ KEIN direkter API-Call mehr!
✅ ALLES über MCP-Protocol!
```

---

## 📋 **Step-by-Step Migration Plan**

### **Phase 1: MCP Server Infrastructure** ✅ Bereits vorhanden!

```
backend/mcp/
├── mcp_client.py              # ✅ Existiert (v6)
└── __init__.py

mcp_servers/
├── perplexity_server.py       # ✅ Existiert (v6)
├── memory_server.py           # ✅ Existiert (v6)
├── claude_cli_server.py       # ✅ Existiert (v6)
├── file_tools_server.py       # ✅ Existiert (v6)
├── tree_sitter_server.py      # ✅ Existiert (v6)
└── asimov_server.py           # ✅ Existiert (v6)
```

**Benötigt:**
```
mcp_servers/
├── openai_server.py           # ❌ NEU - Wrapper für OpenAI API
├── supervisor_server.py       # ❌ NEU - Supervisor als MCP-Server
├── research_agent_server.py   # ❌ NEU - Research Agent als Server
├── architect_agent_server.py  # ❌ NEU - Architect Agent als Server
├── codesmith_agent_server.py  # ❌ NEU - Codesmith Agent als Server
├── reviewfix_agent_server.py  # ❌ NEU - ReviewFix Agent als Server
└── responder_agent_server.py  # ❌ NEU - Responder Agent als Server
```

---

### **Phase 2: MCP Server für OpenAI** (NEU)

**Warum:** Architect, Responder, Supervisor nutzen OpenAI
**Was:** MCP-Wrapper um LangChain ChatOpenAI

```python
# mcp_servers/openai_server.py
"""
OpenAI MCP Server - Wrapper für OpenAI API via LangChain

⚠️ WICHTIG: MCP BLEIBT! Keine direkten OpenAI-Calls außerhalb MCP!

Provides:
- complete: Text completion
- chat: Chat completion
- embed: Embeddings

Author: KI AutoAgent Team
Version: 7.0.0-mcp
"""

import asyncio
import json
import sys
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


async def initialize():
    """Initialize MCP server."""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {
                "listChanged": True
            }
        },
        "serverInfo": {
            "name": "openai-server",
            "version": "1.0.0"
        }
    }


async def list_tools():
    """List available tools."""
    return {
        "tools": [
            {
                "name": "complete",
                "description": "Generate text completion using OpenAI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string"},
                        "system_prompt": {"type": "string"},
                        "model": {"type": "string", "default": "gpt-4o-2024-11-20"},
                        "temperature": {"type": "number", "default": 0.7},
                        "max_tokens": {"type": "number", "default": 4000}
                    },
                    "required": ["prompt"]
                }
            }
        ]
    }


async def call_tool(name: str, arguments: dict) -> dict:
    """Execute tool."""
    if name == "complete":
        return await complete(arguments)
    else:
        return {"error": f"Unknown tool: {name}"}


async def complete(args: dict) -> dict:
    """
    Generate completion using OpenAI.

    ⚠️ MCP BLEIBT: Dies ist der EINZIGE Weg OpenAI zu nutzen!
    """
    # Send progress
    await send_progress(0.0, "🧠 Initializing OpenAI...")

    # Create LLM
    llm = ChatOpenAI(
        model=args.get("model", "gpt-4o-2024-11-20"),
        temperature=args.get("temperature", 0.7),
        max_tokens=args.get("max_tokens", 4000)
    )

    # Build messages
    messages = []
    if args.get("system_prompt"):
        messages.append(SystemMessage(content=args["system_prompt"]))
    messages.append(HumanMessage(content=args["prompt"]))

    # Send progress
    await send_progress(0.3, "⚙️ Calling OpenAI API...")

    # Call API
    response = await llm.ainvoke(messages)

    # Send progress
    await send_progress(1.0, "✅ OpenAI complete")

    return {
        "content": [{"type": "text", "text": response.content}],
        "model": args.get("model", "gpt-4o-2024-11-20")
    }


async def send_progress(progress: float, message: str, total: float = 1.0):
    """
    Send MCP $/progress notification.

    ⚠️ MCP BLEIBT: Standard für Progress-Reporting!
    """
    notification = {
        "jsonrpc": "2.0",
        "method": "$/progress",
        "params": {
            "progress": progress,
            "message": message,
            "total": total
        }
    }
    print(json.dumps(notification), flush=True)


async def main():
    """Main MCP server loop."""
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break

            request = json.loads(line.strip())

            if request["method"] == "initialize":
                response = await initialize()
            elif request["method"] == "tools/list":
                response = await list_tools()
            elif request["method"] == "tools/call":
                response = await call_tool(
                    request["params"]["name"],
                    request["params"]["arguments"]
                )
            else:
                response = {"error": "Unknown method"}

            # Send response
            print(json.dumps({
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": response
            }), flush=True)

        except Exception as e:
            print(json.dumps({
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32603, "message": str(e)}
            }), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
```

---

### **Phase 3: Agent → MCP-Server Conversion**

**Konzept:** Jeder Agent wird ein MCP-Server

```python
# mcp_servers/research_agent_server.py
"""
Research Agent MCP Server

⚠️ MCP BLEIBT: Research Agent läuft NUR als MCP-Server!
⚠️ KEINE direkten API-Calls! Alles über MCPClient!

Tools:
- research: Execute research task
- analyze_workspace: Analyze workspace structure
- web_search: Search web via Perplexity (via MCP!)

Author: KI AutoAgent Team
Version: 7.0.0-mcp
"""

import asyncio
import json
import sys
from pathlib import Path

# ⚠️ MCP BLEIBT: MCPClient für Sub-Calls (Perplexity, Memory)
from mcp.mcp_client import MCPClient


class ResearchAgentServer:
    """Research Agent als MCP-Server."""

    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self.mcp: MCPClient | None = None

    async def initialize(self):
        """
        Initialize MCP connections.

        ⚠️ MCP BLEIBT: Research Agent nutzt Perplexity via MCP!
        """
        self.mcp = MCPClient(
            workspace_path=self.workspace_path,
            servers=["perplexity", "memory"]  # Sub-services
        )
        await self.mcp.initialize()

    async def research(self, args: dict) -> dict:
        """
        Execute research task.

        ⚠️ MCP BLEIBT: Perplexity-Call via MCP, NICHT direkt!
        """
        instructions = args.get("instructions", "")

        await send_progress(0.0, "🔍 Starting research...")

        results = {}

        # Web search via MCP (Perplexity)
        if "research" in instructions.lower():
            await send_progress(0.3, "🌐 Searching web via Perplexity...")

            # ⚠️ MCP BLEIBT: Perplexity via MCP!
            search_result = await self.mcp.call(
                server="perplexity",
                tool="search",
                arguments={"query": instructions, "max_results": 5}
            )

            results["web_results"] = search_result

        # Store in memory via MCP
        await send_progress(0.8, "💾 Storing results in memory...")

        # ⚠️ MCP BLEIBT: Memory via MCP!
        await self.mcp.call(
            server="memory",
            tool="store_memory",
            arguments={
                "workspace_path": self.workspace_path,
                "content": json.dumps(results),
                "metadata": {"agent": "research", "task": instructions}
            }
        )

        await send_progress(1.0, "✅ Research complete")

        return {
            "content": [{"type": "text", "text": json.dumps(results)}],
            "research_context": results
        }


# ... Standard MCP Server Boilerplate (main loop, etc.)
```

---

### **Phase 4: Supervisor als MCP-Orchestrator**

```python
# backend/core/supervisor_mcp.py
"""
Supervisor für Pure MCP Architecture

⚠️ MCP BLEIBT: Supervisor orchestriert NUR via MCP!
⚠️ KEINE direkten Agent-Imports! Alle via MCPClient!

Architecture:
- Supervisor = MCP-Client
- Agents = MCP-Server
- Communication = MCP-Protocol

Author: KI AutoAgent Team
Version: 7.0.0-mcp
"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.types import Command
from langgraph.graph import END

# ⚠️ MCP BLEIBT: MCPClient für ALLE Agent-Calls!
from mcp.mcp_client import MCPClient

logger = logging.getLogger(__name__)


class SupervisorMCP:
    """
    Supervisor orchestrates agents via MCP.

    ⚠️ MCP BLEIBT: Supervisor kennt keine Agent-Klassen mehr!
    ⚠️ Alle Agents sind MCP-Server, kommuniziert wird via MCPClient!
    """

    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self.mcp: MCPClient | None = None

    async def initialize(self):
        """
        Initialize MCP connections to all agents.

        ⚠️ MCP BLEIBT: Alle Agents als MCP-Server registriert!
        """
        self.mcp = MCPClient(
            workspace_path=self.workspace_path,
            servers=[
                # LLM Services
                "openai",         # For decision-making

                # Agent Servers
                "research_agent",
                "architect_agent",
                "codesmith_agent",
                "reviewfix_agent",
                "responder_agent",

                # Supporting Services
                "memory",
                "perplexity",
                "file_tools",
                "tree_sitter",
                "asimov"
            ]
        )

        await self.mcp.initialize()
        logger.info("✅ Supervisor MCP initialized with all agents")

    async def decide_next(self, state: dict[str, Any]) -> Command:
        """
        Make routing decision via MCP.

        ⚠️ MCP BLEIBT: Decision via OpenAI MCP-Server!
        ⚠️ Agent execution via MCP-Server-Calls!
        """
        # Get available agents dynamically from MCP
        # ⚠️ MCP BLEIBT: Dynamic discovery!
        agents = await self.mcp.list_servers()

        # Build decision prompt
        prompt = self._build_decision_prompt(state, agents)

        # Make decision via OpenAI MCP-Server
        # ⚠️ MCP BLEIBT: LLM-Call via MCP, NICHT direkt!
        decision_result = await self.mcp.call(
            server="openai",
            tool="complete",
            arguments={
                "prompt": prompt,
                "system_prompt": self._get_system_prompt(),
                "temperature": 0.3,
                "max_tokens": 1500
            }
        )

        # Parse decision
        decision_text = decision_result["content"][0]["text"]
        next_agent = self._parse_decision(decision_text)

        # Execute agent via MCP
        # ⚠️ MCP BLEIBT: Agent execution via MCP-Server-Call!
        if next_agent == "END":
            return Command(goto=END)

        result = await self.mcp.call(
            server=f"{next_agent}_agent",
            tool=next_agent,  # Tool name = agent name
            arguments=state
        )

        # Update state with result
        return Command(
            goto="supervisor",  # Back to supervisor for next decision
            update=result
        )
```

---

### **Phase 5: WebSocket Handler mit MCP-Progress**

```python
# backend/api/server_v7_mcp.py
"""
FastAPI Server for Pure MCP Architecture

⚠️ MCP BLEIBT: Server nutzt MCPClient für ALLE Operationen!
⚠️ KEINE direkten Agent-Imports mehr!

Author: KI AutoAgent Team
Version: 7.0.0-mcp
"""

from fastapi import FastAPI, WebSocket
from contextlib import asynccontextmanager

# ⚠️ MCP BLEIBT: Globaler MCP-Manager für alle Sessions
from backend.utils.mcp_manager import MCPManager

app = FastAPI()
mcp_manager = MCPManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan: Initialize/Cleanup MCP connections.

    ⚠️ MCP BLEIBT: MCP-Server werden beim Start/Stop verwaltet!
    """
    # Startup: Pre-warm MCP connections
    logger.info("🚀 Starting MCP Manager...")
    # (optional pre-warming)

    yield

    # Shutdown: Cleanup MCP connections
    logger.info("🛑 Shutting down MCP Manager...")
    await mcp_manager.cleanup_all()


app = FastAPI(lifespan=lifespan)


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint with Pure MCP.

    ⚠️ MCP BLEIBT: Workflow execution via MCPClient!
    ⚠️ Progress-Streaming via MCP $/progress!
    """
    await websocket.accept()

    workspace_path = "/path/to/workspace"  # From init message

    # Get MCP client for this session
    # ⚠️ MCP BLEIBT: MCPManager verwaltet Clients!
    mcp = await mcp_manager.get_client(workspace_path)

    try:
        # Execute workflow via MCP-Server
        # ⚠️ MCP BLEIBT: Supervisor via MCP aufgerufen!
        async for progress in mcp.call_with_progress(
            server="supervisor_agent",
            tool="execute_workflow",
            arguments={"task": user_query, "workspace_path": workspace_path}
        ):
            # Forward $/progress to WebSocket
            # ⚠️ MCP BLEIBT: Standard MCP-Progress-Format!
            await websocket.send_json({
                "jsonrpc": "2.0",
                "method": "$/progress",
                "params": {
                    "progress": progress.progress,
                    "message": progress.message,
                    "total": progress.total,
                    "agent": progress.server
                }
            })

    except Exception as e:
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()
```

---

## 📋 **Implementation Checklist**

### **Step 1: MCP Server Infrastructure** (2 Stunden)

- [ ] `mcp_servers/openai_server.py` - OpenAI MCP-Wrapper
- [ ] `mcp_servers/research_agent_server.py` - Research als MCP-Server
- [ ] `mcp_servers/architect_agent_server.py` - Architect als MCP-Server
- [ ] `mcp_servers/codesmith_agent_server.py` - Codesmith als MCP-Server
- [ ] `mcp_servers/reviewfix_agent_server.py` - ReviewFix als MCP-Server
- [ ] `mcp_servers/responder_agent_server.py` - Responder als MCP-Server
- [ ] Alle Server mit `⚠️ MCP BLEIBT` Kommentaren

### **Step 2: MCP Manager** (1 Stunde)

- [ ] `backend/utils/mcp_manager.py` - Global MCP Manager
- [ ] Lifecycle-Management (startup/shutdown)
- [ ] Per-Workspace MCPClient caching
- [ ] `⚠️ MCP BLEIBT` Kommentare

### **Step 3: Supervisor MCP** (2 Stunden)

- [ ] `backend/core/supervisor_mcp.py` - Supervisor als MCP-Orchestrator
- [ ] Alle Agent-Calls via `mcp.call()`
- [ ] LLM-Calls via `openai` MCP-Server
- [ ] `⚠️ MCP BLEIBT` Kommentare überall

### **Step 4: Workflow MCP** (1 Stunde)

- [ ] `backend/workflow_v7_mcp.py` - Workflow mit MCP
- [ ] LangGraph Nodes rufen MCP-Agents
- [ ] Progress-Streaming via $/progress
- [ ] `⚠️ MCP BLEIBT` Kommentare

### **Step 5: Server Integration** (1 Stunde)

- [ ] `backend/api/server_v7_mcp.py` - FastAPI mit MCP
- [ ] WebSocket Handler mit MCP-Progress
- [ ] SSE Endpoint (optional)
- [ ] `⚠️ MCP BLEIBT` Kommentare

### **Step 6: Remove Old Code** (1 Stunde)

- [ ] ❌ DELETE `backend/agents/*_agent.py` (alte Agent-Klassen)
- [ ] ❌ DELETE `backend/utils/ai_factory.py` (nicht mehr gebraucht)
- [ ] ❌ DELETE `backend/utils/*_service.py` (durch MCP-Server ersetzt)
- [ ] Kommentar in README: `⚠️ MCP BLEIBT - Keine direkten API-Calls!`

### **Step 7: Testing** (2 Stunden)

- [ ] Test: MCPClient connects zu allen Servern
- [ ] Test: Supervisor routes via MCP
- [ ] Test: Progress-Streaming funktioniert
- [ ] Test: Complete workflow via MCP

---

## ⚠️ **WICHTIG: "MCP BLEIBT" Kommentare**

**An folgenden Stellen MÜSSEN Kommentare sein:**

### **1. MCP Server Files** (ALLE!)
```python
"""
⚠️ MCP BLEIBT: Dieser Server ist Teil der MCP-Architecture!
⚠️ KEINE direkten API-Calls! Alles über MCPClient!
"""
```

### **2. Supervisor**
```python
# ⚠️ MCP BLEIBT: Supervisor orchestriert NUR via MCP!
# ⚠️ KEINE direkten Agent-Imports! Alle via MCPClient!
```

### **3. Workflow**
```python
# ⚠️ MCP BLEIBT: Workflow nutzt MCP-Agents!
# ⚠️ KEINE direkten Agent-Klassen mehr!
```

### **4. WebSocket Handler**
```python
# ⚠️ MCP BLEIBT: Alle Calls via MCPClient!
# ⚠️ Progress via MCP $/progress standard!
```

### **5. README.md**
```markdown
## ⚠️ WICHTIG: MCP ARCHITECTURE

**MCP BLEIBT!** Diese Architektur nutzt ausschließlich MCP-Protocol.

- KEINE direkten API-Calls
- ALLE Services via MCP-Server
- ALLE Agents als MCP-Server
- Progress via $/progress standard

Siehe: `/docs/MCP_ARCHITECTURE.md`
```

---

## ✅ **Vorteile dieser Pure MCP-Implementation**

1. ✅ **Composability:** LLM-Wechsel = Config-Änderung
2. ✅ **Ecosystem:** 1000+ Community-Server nutzbar
3. ✅ **Dynamic Discovery:** Tools zur Laufzeit
4. ✅ **Multi-Agent:** Standard Agent-to-Agent Communication
5. ✅ **Progress:** Built-in $/progress
6. ✅ **Security:** Process-Isolation
7. ✅ **Industry-Standard:** OpenAI, Google, Microsoft
8. ✅ **Testing:** Easy Mocking
9. ✅ **Observability:** Central Logging
10. ✅ **Future-Proof:** Standard bleibt

---

## 🚀 **Timeline: 10 Stunden Total**

- Step 1: MCP Servers (2h)
- Step 2: MCP Manager (1h)
- Step 3: Supervisor MCP (2h)
- Step 4: Workflow MCP (1h)
- Step 5: Server Integration (1h)
- Step 6: Remove Old Code (1h)
- Step 7: Testing (2h)

**Total: 10 Stunden für Pure MCP Migration!**

---

## ✅ **Ready to Implement?**

Bestätige, und ich starte mit der Implementation:

1. ✅ **Pure MCP** - Keine Rückwärtskompatibilität
2. ✅ **"MCP BLEIBT"** - Kommentare überall
3. ✅ **Delete Old Code** - Alte Agent-Klassen weg
4. ✅ **10 Stunden** - Komplette Migration

**Soll ich jetzt mit Step 1 (MCP Servers) beginnen?**
