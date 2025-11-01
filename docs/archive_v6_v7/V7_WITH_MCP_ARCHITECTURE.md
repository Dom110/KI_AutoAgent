# v7.0 mit MCP Library - Architektur-Vorschlag

**Date:** 2025-10-29
**Task:** Wie sähe v7.0 aus mit echter MCP Library (wie v6.x)?

---

## 🔍 **v6 MCP-Architektur (Current State)**

### **Wie v6 MCP nutzt:**

```python
# 1. MCPClient erstellen
from mcp.mcp_client import MCPClient

mcp = MCPClient(workspace_path="/path/to/workspace")
await mcp.initialize()  # Startet alle MCP-Server als subprocesses

# 2. MCP-Calls in Agents
# Research Agent
result = await mcp.call(
    server="perplexity",
    tool="search",
    arguments={"query": "FastAPI patterns", "max_results": 5}
)

# Architect Agent
await mcp.call(
    server="memory",
    tool="search_memory",
    arguments={"query": "architecture design", "k": 2}
)

# Codesmith Agent
await mcp.call(
    server="claude",
    tool="claude_generate",
    arguments={
        "prompt": "Generate code...",
        "system_prompt": "You are...",
        "workspace_path": workspace_path,
        "tools": ["Read", "Edit", "Bash"]
    },
    timeout=900  # 15 min
)

# ReviewFix Agent
await mcp.call(
    server="file_tools",
    tool="write_file",
    arguments={"file_path": "src/app.py", "content": code}
)
```

---

## 📊 **v6 MCP-Server Architektur**

### **MCP-Server als Subprocesses:**

```
MCPClient
   ├─→ perplexity_server.py (subprocess)
   │     Tool: search()
   │     Communication: JSON-RPC über stdin/stdout
   │
   ├─→ memory_server.py (subprocess)
   │     Tools: store_memory(), search_memory()
   │     Communication: JSON-RPC über stdin/stdout
   │
   ├─→ claude_cli_server.py (subprocess)
   │     Tool: claude_generate()
   │     Communication: JSON-RPC über stdin/stdout
   │     → Startet seinerseits Claude CLI subprocess!
   │
   ├─→ file_tools_server.py (subprocess)
   │     Tools: write_file(), read_file(), list_files()
   │     Communication: JSON-RPC über stdin/stdout
   │
   ├─→ tree_sitter_server.py (subprocess)
   │     Tools: validate_syntax(), analyze_code()
   │
   └─→ asimov_server.py (subprocess)
         Tools: validate_rules(), check_security()
```

### **Kommunikations-Flow:**

```
Agent (Python)
    ↓
MCPClient.call()
    ↓
JSON-RPC Request → stdin
    ↓
MCP Server (subprocess)
    ↓ (verarbeitet Request)
    ↓ (sendet Progress-Notifications via $/progress)
    ↓
JSON-RPC Response ← stdout
    ↓
MCPClient.call() return
    ↓
Agent (erhält Result)
```

---

## 🏗️ **v7.0 MIT MCP-Library Architektur**

### **Wie würde v7.0 mit MCP aussehen?**

### **Option 1: Vollständiger MCP-Umbau**

**Alle Agents nutzen MCP-Client:**

```python
# backend/utils/mcp_manager.py
class MCPManager:
    """
    Global MCP Manager für alle Agents.

    Singleton, der einen MCPClient pro Workspace verwaltet.
    """
    _clients: dict[str, MCPClient] = {}

    @classmethod
    async def get_client(cls, workspace_path: str) -> MCPClient:
        if workspace_path not in cls._clients:
            mcp = MCPClient(workspace_path=workspace_path)
            await mcp.initialize()
            cls._clients[workspace_path] = mcp
        return cls._clients[workspace_path]


# backend/agents/codesmith_agent.py
from backend.utils.mcp_manager import MCPManager

class CodesmithAgent:
    async def execute(self, state: dict) -> dict:
        workspace_path = state["workspace_path"]
        mcp = await MCPManager.get_client(workspace_path)

        # Code generation via MCP
        result = await mcp.call(
            server="claude",
            tool="claude_generate",
            arguments={
                "prompt": self._build_prompt(...),
                "system_prompt": self._get_system_prompt(),
                "workspace_path": workspace_path,
                "tools": ["Read", "Edit", "Bash"]
            },
            timeout=900
        )

        return {"generated_files": result["files_created"]}
```

---

### **Option 2: Hybrid (MCP + Direct APIs)**

**Große Tools via MCP, schnelle APIs direkt:**

```python
class ArchitectAgent:
    def __init__(self):
        # Direkte API für schnelle Calls
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.4)

    async def execute(self, state: dict) -> dict:
        mcp = await MCPManager.get_client(state["workspace_path"])

        # 1. Memory via MCP (weil cross-session State)
        research = await mcp.call(
            server="memory",
            tool="search_memory",
            arguments={"query": "research findings"}
        )

        # 2. LLM direkt (weil schneller als MCP-Call)
        response = await self.llm.ainvoke([
            SystemMessage(content=self._get_system_prompt()),
            HumanMessage(content=self._build_prompt(...))
        ])

        architecture = self._parse_response(response.content)

        # 3. Memory speichern via MCP
        await mcp.call(
            server="memory",
            tool="store_memory",
            arguments={"content": architecture}
        )

        return {"architecture": architecture}
```

---

### **Option 3: MCP-Wrapper für bestehende v7.0 Services**

**v7.0 Services als MCP-Server verpacken:**

```python
# backend/mcp_servers/openai_server.py (NEU)
"""
MCP Server für OpenAI API.

Wrapper um bestehenden OpenAIService.
"""

from backend.utils.openai_service import OpenAIService

class OpenAIMCPServer:
    def __init__(self):
        self.service = OpenAIService()

    async def complete(self, arguments: dict) -> dict:
        """MCP Tool: complete()"""
        request = AIRequest(
            prompt=arguments["prompt"],
            system_prompt=arguments.get("system_prompt"),
            temperature=arguments.get("temperature", 0.7),
            max_tokens=arguments.get("max_tokens", 4000)
        )

        response = await self.service.complete(request)

        return {
            "content": [{"type": "text", "text": response.content}],
            "success": response.success
        }


# backend/mcp_servers/perplexity_server.py (NEU)
"""
MCP Server für Perplexity API.

Wrapper um bestehenden PerplexityService.
"""

from backend.utils.perplexity_service import PerplexityService

class PerplexityMCPServer:
    def __init__(self):
        self.service = PerplexityService()

    async def search(self, arguments: dict) -> dict:
        """MCP Tool: search()"""
        # ... nutzt PerplexityService intern
```

---

## 📊 **Vergleich: v7 Current vs v7 mit MCP**

| Aspekt | v7.0 Current (subprocess/REST) | v7.0 mit MCP | Gewinner |
|--------|-------------------------------|--------------|----------|
| **Code-Komplexität** | Medium (AI Factory) | High (MCP Manager + Servers) | **Current** |
| **Performance** | Schnell (direkte API-Calls) | Langsamer (JSON-RPC Overhead) | **Current** |
| **Event-Streaming** | Custom (benötigt Impl.) | `$/progress` (built-in MCP) | **MCP** ✅ |
| **Progress-Reporting** | Manuell | Automatisch via MCP | **MCP** ✅ |
| **Tool-Erweiterbarkeit** | Neue AI-Provider Klassen | Neue MCP-Server | **Tie** |
| **Debugging** | Einfach (direct calls) | Schwer (subprocess, JSON-RPC) | **Current** |
| **Standards-Compliance** | Custom | MCP-Protocol | **MCP** ✅ |
| **Maintenance** | Einfach (weniger Layers) | Complex (viele Subprocesses) | **Current** |
| **Memory-Usage** | Low | High (viele Subprocesses) | **Current** |
| **Parallel Execution** | asyncio.gather() | mcp.call_multiple() | **Tie** |
| **Error Handling** | Direkt | JSON-RPC Errors | **Current** |
| **Setup-Aufwand** | Minimal | Hoch (MCP-Servers starten) | **Current** |

**Score: Current 7 : 3 MCP**

---

## ✅ **Event-Streaming mit MCP**

### **Der EINZIGE Vorteil von MCP: `$/progress` Notifications!**

#### **Wie MCP Progress-Reporting funktioniert:**

```python
# MCP Server (z.B. claude_cli_server.py)
async def claude_generate(arguments: dict) -> dict:
    """
    Generate code with Claude CLI.

    Sends progress notifications during execution!
    """
    # Send progress notification (0%)
    await send_progress(
        progress=0.0,
        message="🧠 Analyzing architecture and planning code structure",
        total=1.0
    )

    # Start Claude CLI
    process = await asyncio.create_subprocess_exec(...)

    # Send progress notification (30%)
    await send_progress(
        progress=0.3,
        message="⚙️ Generating code with Claude CLI...",
        total=1.0
    )

    # Wait for Claude CLI
    stdout, stderr = await process.communicate()

    # Send progress notification (80%)
    await send_progress(
        progress=0.8,
        message="📝 Parsing generated files...",
        total=1.0
    )

    # Parse files
    files = parse_output(stdout)

    # Send progress notification (100%)
    await send_progress(
        progress=1.0,
        message="✅ Code generation complete",
        total=1.0
    )

    return {"files_created": files}


async def send_progress(progress: float, message: str, total: float):
    """
    Send MCP progress notification.

    This is sent via stdout as JSON-RPC notification (no "id" field).
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
```

#### **Client empfängt Progress:**

```python
# MCPClient._raw_call() in mcp_client.py (Zeile 303-369)
async def _raw_call(self, server: str, method: str, params: dict) -> dict:
    # ... send request ...

    while True:
        response_line = await process.stdout.readline()
        message = json.loads(response_line.decode().strip())

        # Check if this is the final response
        if "id" in message and message["id"] == request_id:
            return message  # Final result!

        # This is a progress notification!
        if "method" in message and message["method"] == "$/progress":
            params = message.get("params", {})
            logger.debug(f"📊 {server}: {params.get('message', 'progress...')}")

            # ⭐ HIER können wir Events streamen!
            await event_bus.emit({
                "type": "agent_event",
                "agent": server,
                "event_type": "progress",
                "message": params.get("message"),
                "progress": params.get("progress"),
                "total": params.get("total")
            })
```

---

## 🏆 **Empfehlung: Hybrid-Ansatz**

### **Beste Lösung: MCP NUR für Event-Streaming, Rest bleibt current**

```python
# backend/utils/mcp_progress.py (NEU)
"""
MCP-kompatibles Progress-Reporting OHNE volles MCP.

Nutzt nur das $/progress Notification-Format.
"""

from contextvars import ContextVar
from backend.utils.event_stream import event_bus

current_session_id: ContextVar[str | None] = ContextVar('session_id', default=None)

async def report_progress(
    progress: float,
    message: str,
    agent: str,
    phase: str,  # "think" | "progress" | "result"
    total: float = 1.0
):
    """
    Send MCP-style progress notification.

    Format ist MCP-kompatibel, aber läuft über unseren Event-Bus.
    """
    session_id = current_session_id.get()
    if not session_id:
        return

    # MCP-kompatibles Format
    event = {
        "jsonrpc": "2.0",
        "method": "$/progress",
        "params": {
            "progress": progress,
            "message": message,
            "total": total,
            "agent": agent,
            "phase": phase
        }
    }

    # Über unseren Event-Bus senden
    await event_bus.emit(event)


# In Agents nutzen:
async def codesmith_execute(state: dict):
    current_session_id.set(state["session_id"])

    await report_progress(0.0, "Analyzing architecture", "codesmith", "think")

    # ... Claude CLI call ...

    await report_progress(0.5, "Generating code", "codesmith", "progress")

    # ... wait ...

    await report_progress(1.0, "Code generation complete", "codesmith", "result")
```

---

## 📋 **Migration-Plan: v7.0 → v7.0 mit MCP-Style Progress**

### **Phase 1: MCP-Style Progress API (ohne MCP Library)**
```python
# backend/utils/mcp_progress.py erstellen
# Alle Agents anpassen: report_progress() nutzen
```

### **Phase 2: Event-Bus Integration**
```python
# backend/utils/event_stream.py erweitern
# WebSocket Handler anpassen: $/progress Events forwarden
```

### **Phase 3: Frontend Update**
```javascript
// Client empfängt MCP-style Events
ws.on('message', (event) => {
    if (event.method === '$/progress') {
        const {progress, message, agent, phase} = event.params;
        updateProgressBar(agent, progress, message);
    }
});
```

### **Phase 4: Optional - Echte MCP-Server für Tools**
```python
# Nur für Tools, die es brauchen (Tree-sitter, Asimov, etc.)
# NICHT für OpenAI/Perplexity (zu viel Overhead)
```

---

## ✅ **Fazit**

### **Vollständiger MCP-Umbau? NEIN! ❌**

**Gründe:**
1. ❌ **Zu komplex:** Viele MCP-Server-Subprocesses
2. ❌ **Performance-Overhead:** JSON-RPC statt direkte API-Calls
3. ❌ **Wartung aufwändig:** Mehr Layers, mehr Fehlerquellen
4. ❌ **Debugging schwerer:** Subprocesses, JSON-RPC-Parsing
5. ❌ **Memory-Usage höher:** Viele Subprocesses pro Workspace

### **MCP-Style Progress-Reporting? JA! ✅**

**Gründe:**
1. ✅ **Standard-Format:** `$/progress` ist MCP-Standard
2. ✅ **Built-in Progress-Bar:** 0-100% mit message
3. ✅ **Wenig Aufwand:** Nur API + Event-Bus Integration
4. ✅ **Kein Overhead:** Keine Subprocesses nötig
5. ✅ **Future-proof:** Kann später zu echtem MCP migriert werden

### **Empfohlener Ansatz:**

```
v7.0 Current (subprocess/REST)
    +
MCP-Style Progress API ($/progress Format)
    +
Event-Bus mit ContextVars
    +
SSE Transport
    =
⭐ Beste Lösung! ⭐
```

**Das ist GENAU was ich in "COMPLETE_SOLUTION_COMPARISON.md" als "MCP-Style Hybrid (Ansatz 5)" vorgeschlagen habe!**

---

## 📄 **Zusammenfassung**

| Ansatz | Code-Komplexität | Performance | Progress-Reporting | Empfehlung |
|--------|------------------|-------------|-------------------|------------|
| **v7.0 Current** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ Keine | - |
| **v7.0 Full MCP** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ Zu komplex |
| **v7.0 MCP-Style** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ **EMPFOHLEN!** |

**v7.0 mit MCP-Style Progress = Beste Balance zwischen Komplexität und Features!**
