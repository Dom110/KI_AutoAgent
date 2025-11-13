# Event Streaming Solution Comparison

**Date:** 2025-10-29
**Task:** Compare MCP-based solution vs. my Hybrid approach

---

## 🎯 **Proposed Solution Analysis**

Die vorgeschlagene Lösung ist **eleganter und besser** als mein Hybrid-Ansatz! Hier ist warum:

---

## 📊 **Vergleich: Mein Hybrid vs. MCP-Solution**

| Aspekt | Mein Hybrid (ContextVars + EventBus) | MCP-Solution | Gewinner |
|--------|--------------------------------------|--------------|----------|
| **Agent Communication** | Custom `event_bus.emit()` | `report_progress()` (MCP-Standard) | **MCP** ✅ |
| **Workflow Streaming** | Custom Queue + `astream` | `astream(stream_mode="updates")` | **MCP** ✅ |
| **Transport** | WebSocket only | SSE (primary) + WebSocket (optional) | **MCP** ✅ |
| **Session Routing** | ContextVars | ContextVars | **Tie** 🤝 |
| **Complexity** | Medium (~200 LOC) | Low (~100 LOC) | **MCP** ✅ |
| **Standards-Compliance** | Custom | MCP-Protocol | **MCP** ✅ |
| **Load-Balancer Support** | Complex (sticky sessions) | Easy (SSE is stateless) | **MCP** ✅ |

**Score: MCP-Solution gewinnt 6:0:1** 🏆

---

## ✅ **Warum MCP-Solution besser ist**

### **1. MCP `report_progress` ist ein STANDARD**

**Mein Ansatz:**
```python
# Custom Event-Format
await event_bus.emit({
    "type": "agent_event",
    "agent": "codesmith",
    "event_type": "think",
    "message": "Analyzing architecture...",
    "details": {...}
})
```

**MCP-Solution:**
```python
# MCP-Standard: Claude Code nutzt das bereits!
from mcp.server.progress import report_progress

await report_progress(
    ctx,
    progress=0.35,
    message="🧠 think: analyzing architecture",
    total=1.0
)
```

**Vorteile:**
- ✅ **Standard-konform:** Claude Code, MCP-Tools verstehen das sofort
- ✅ **Progress-Bar:** `progress/total` liefert echten Fortschritt (0-100%)
- ✅ **Weniger Code:** Keine Custom-Event-Klassen nötig
- ✅ **Kompatibilität:** Andere MCP-Tools können Events empfangen

---

### **2. SSE ist besser als WebSocket (für unser Use-Case)**

**Warum SSE?**

| Feature | WebSocket | SSE | Unser Bedarf |
|---------|-----------|-----|--------------|
| **Bidirektional** | ✅ | ❌ | ❌ (Einweg reicht) |
| **HTTP-freundlich** | ❌ | ✅ | ✅ (Load-Balancer) |
| **Auto-Reconnect** | Manual | ✅ Built-in | ✅ (Robustheit) |
| **Proxy-Support** | Complex | ✅ Native | ✅ (Firewalls) |
| **Resource Usage** | Higher | Lower | ✅ (Skalierung) |
| **Complexity** | Medium | Low | ✅ (Simplicity) |

**Unser aktueller WebSocket:**
- Brauchen **KEINE** Bidirektionalität (User sendet Task nur einmal)
- Events fließen nur **Server → Client**
- WebSocket ist **Overkill**!

**Mit SSE:**
```python
# Client (JavaScript)
const eventSource = new EventSource('/events?session_id=abc123');
eventSource.addEventListener('agent', (e) => {
    const event = JSON.parse(e.data);
    console.log(event);  // 🧠 think: analyzing...
});

// Server (FastAPI)
@router.get("/events")
async def events(session_id: str):
    q = queue_for_session(session_id)
    async def gen():
        try:
            await subscribe(session_id, q)
            while True:
                evt = await q.get()
                yield {"event": "agent", "data": json.dumps(evt)}
        finally:
            await unsubscribe(session_id, q)
    return EventSourceResponse(gen())
```

**Vorteile:**
- ✅ **Simpler:** Kein Connection-Management nötig
- ✅ **Auto-Reconnect:** Browser reconnected automatisch bei Verbindungsabbruch
- ✅ **HTTP-basiert:** Load-Balancer, Proxies, Firewalls verstehen es
- ✅ **Weniger Resources:** Kein WebSocket-Overhead

---

### **3. LangGraph `astream` macht bereits was wir brauchen**

**Mein Ansatz:**
```python
# Custom Queue + Background Task
event_queue = event_manager.subscribe(session_id)

async def stream_workflow_events():
    async for event in app.astream(initial_state, config=config, stream_mode="updates"):
        await event_queue.put({
            "type": "workflow_event",
            "node": node_name,
            "state_update": state_update,
            "timestamp": datetime.now().isoformat()
        })
```

**MCP-Solution:**
```python
# Direkt streamen - VIEL einfacher!
async for ev in app.astream(state, config=config, stream_mode="updates"):
    # ev enthält bereits {"node": "...", "update": {...}}
    await event_bus.emit({
        "t": "workflow_event",
        "node": ev.get("node"),
        "delta": ev.get("update")
    })
```

**Vorteile:**
- ✅ **Kein Background-Task:** Direkt yielden
- ✅ **Weniger Code:** Keine Custom-Queue-Logik
- ✅ **Native LangGraph:** Nutzt built-in Streaming

---

### **4. ContextVars bleibt (richtig!)**

Beide Lösungen nutzen ContextVars für Session-Routing - **das ist perfekt!**

```python
from contextvars import ContextVar

current_session = ContextVar("sid", default=None)

# Im WebSocket/SSE Handler setzen
current_session.set(session_id)

# Im Event-Bus nutzen
class Bus:
    async def emit(self, evt):
        sid = current_session.get()
        for q in list(self.subs.get(sid, ())):
            q.put_nowait(evt)
```

---

## 🔴 **Problem mit MCP-Solution: Claude CLI Integration**

### **Kritischer Punkt:**

Die MCP-Solution geht davon aus, dass wir **MCP-Tools** verwenden. Aber:

**Unser aktueller Stack:**
- ❌ **Codesmith:** Nutzt Claude CLI (subprocess, kein MCP)
- ❌ **ReviewFix:** Nutzt Claude CLI (subprocess, kein MCP)
- ✅ **Research:** Nutzt Perplexity API (könnte MCP-Report nutzen)
- ✅ **Architect:** Nutzt OpenAI API (könnte MCP-Report nutzen)

**Problem:**
```python
# Das funktioniert NICHT mit Claude CLI subprocess:
from mcp.server.progress import report_progress

await report_progress(ctx, progress=0.35, message="...")
# ❌ subprocess hat keinen MCP-Context!
```

**Claude CLI subprocess:**
```python
process = await asyncio.create_subprocess_exec(
    *cmd,
    stdin=asyncio.subprocess.DEVNULL,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
    cwd=workspace
)
# ❌ Kein MCP-Context, nur stdout/stderr
```

---

## 💡 **Hybrid-Hybrid-Ansatz: Das Beste aus beiden Welten**

### **Lösung: MCP-Style Events + ContextVars + SSE**

**Konzept:**
1. **Event-Schema:** MCP-kompatibel (aber ohne MCP-Library)
2. **ContextVars:** Session-Routing
3. **SSE:** Transport (statt WebSocket)
4. **Event-Bus:** Custom (aber MCP-Format)

### **Implementation:**

```python
# ============================================================================
# 1. MCP-Style Event (ohne MCP-Library)
# ============================================================================

from dataclasses import dataclass
from contextvars import ContextVar

current_session_id: ContextVar[str | None] = ContextVar('session_id', default=None)

@dataclass
class ProgressEvent:
    """MCP-style progress event (without MCP library)."""
    progress: float  # 0.0 - 1.0
    message: str
    total: float = 1.0
    agent: str | None = None
    phase: str | None = None  # "think" | "progress" | "decision" | "result"
    details: dict | None = None

    def to_dict(self):
        return {
            "t": "agent_event",
            "agent": self.agent,
            "phase": self.phase,
            "msg": self.message,
            "pct": self.progress / self.total if self.total > 0 else 0,
            "details": self.details or {},
            "ts": datetime.now().isoformat()
        }


# ============================================================================
# 2. Event Bus (MCP-compatible)
# ============================================================================

class SessionEventBus:
    """Event bus with ContextVars for session isolation."""

    def __init__(self):
        self.subs: dict[str, set[asyncio.Queue]] = defaultdict(set)

    async def subscribe(self, session_id: str) -> asyncio.Queue:
        """Subscribe to events for a session."""
        q = asyncio.Queue()
        self.subs[session_id].add(q)
        return q

    async def unsubscribe(self, session_id: str, q: asyncio.Queue):
        """Unsubscribe from events."""
        self.subs[session_id].discard(q)
        if not self.subs[session_id]:
            del self.subs[session_id]

    async def emit(self, event: ProgressEvent | dict):
        """Emit event to current session (from ContextVar)."""
        sid = current_session_id.get()
        if not sid:
            return

        # Convert to dict if ProgressEvent
        evt_dict = event.to_dict() if isinstance(event, ProgressEvent) else event

        # Send to all subscribers
        for q in list(self.subs.get(sid, ())):
            q.put_nowait(evt_dict)

event_bus = SessionEventBus()


# ============================================================================
# 3. Convenience Functions (MCP-style API)
# ============================================================================

async def report_progress(
    progress: float,
    message: str,
    total: float = 1.0,
    agent: str | None = None,
    phase: str | None = None,
    details: dict | None = None
):
    """MCP-style progress reporting (without MCP library)."""
    event = ProgressEvent(
        progress=progress,
        message=message,
        total=total,
        agent=agent,
        phase=phase,
        details=details
    )
    await event_bus.emit(event)


# ============================================================================
# 4. SSE Endpoint (FastAPI)
# ============================================================================

from sse_starlette.sse import EventSourceResponse

@router.get("/events")
async def events(session_id: str):
    """SSE endpoint for streaming events."""
    q = await event_bus.subscribe(session_id)

    async def gen():
        try:
            while True:
                evt = await q.get()
                yield {"event": "agent", "data": json.dumps(evt)}
        finally:
            await event_bus.unsubscribe(session_id, q)

    return EventSourceResponse(gen())


# ============================================================================
# 5. Usage in Agents
# ============================================================================

async def supervisor_decide(state: dict):
    """Supervisor with progress reporting."""
    # Set session context
    current_session_id.set(state["session_id"])

    # Report thinking
    await report_progress(
        progress=0.1,
        message="🧠 Analyzing state and making routing decision",
        agent="supervisor",
        phase="think",
        details={"iteration": state["iteration"]}
    )

    # Make decision
    decision = await _make_decision(state)

    # Report decision
    await report_progress(
        progress=1.0,
        message=f"🎯 Routing to {decision.next_agent}",
        agent="supervisor",
        phase="decision",
        details={
            "next_agent": decision.next_agent.value,
            "reasoning": decision.reasoning,
            "confidence": decision.confidence
        }
    )


async def codesmith_execute(state: dict):
    """Codesmith with progress reporting."""
    current_session_id.set(state["session_id"])

    # Report start
    await report_progress(
        progress=0.0,
        message="🚀 Starting code generation",
        agent="codesmith",
        phase="think"
    )

    # Generate code
    await report_progress(
        progress=0.3,
        message="📡 Calling Claude CLI for code generation",
        agent="codesmith",
        phase="progress"
    )

    # Call Claude CLI (subprocess - NO MCP!)
    response = await claude_cli_service.complete(request)

    # Report result
    await report_progress(
        progress=1.0,
        message=f"✅ Generated {len(files)} files",
        agent="codesmith",
        phase="result",
        details={"files": [f["path"] for f in files]}
    )
```

---

## 🏆 **Final Recommendation**

**Nutze den "Hybrid-Hybrid" Ansatz:**

1. ✅ **MCP-Style Events** (aber ohne MCP-Library - wegen Claude CLI)
2. ✅ **ContextVars** für Session-Routing
3. ✅ **SSE** als Transport (simpler als WebSocket)
4. ✅ **Event-Bus** mit `report_progress()` API
5. ✅ **LangGraph astream** für Workflow-Events

**Vorteile:**
- ✅ MCP-kompatibles Format (kann später zu echtem MCP migriert werden)
- ✅ Funktioniert mit Claude CLI subprocess
- ✅ Simpler als mein ursprünglicher Hybrid
- ✅ SSE statt WebSocket (weniger Overhead)
- ✅ Production-ready

**Migration-Path:**
- Wenn wir später Claude CLI durch MCP-Tools ersetzen → einfacher Switch zu `mcp.server.progress.report_progress`

---

## 📋 **Implementation Checklist**

- [ ] `backend/utils/session_event_bus.py` - Event-Bus mit ContextVars
- [ ] `backend/utils/progress.py` - `report_progress()` API
- [ ] `backend/api/sse_events.py` - SSE-Endpoint
- [ ] `backend/core/supervisor.py` - Progress-Reporting integrieren
- [ ] `backend/agents/*.py` - Progress-Reporting in allen Agents
- [ ] `backend/workflow_v7_supervisor.py` - `astream` für Workflow-Events
- [ ] Install `sse-starlette`: `pip install sse-starlette`
- [ ] Test mit Frontend (EventSource statt WebSocket)

---

## ✅ **Fazit**

**Die vorgeschlagene MCP-Solution ist brillant!** Aber wir müssen sie anpassen, weil:

1. **Claude CLI ist KEIN MCP-Tool** → Brauchen MCP-Style API ohne MCP-Library
2. **SSE statt WebSocket** → Viel einfacher für unser Use-Case
3. **ContextVars bleiben** → Perfekt für Session-Routing

**Ergebnis:** "Hybrid-Hybrid" = MCP-kompatibles Format + ContextVars + SSE + Custom Event-Bus

**Implementation-Time:** ~1 Stunde
**Complexity:** Medium
**Impact:** ⭐⭐⭐⭐⭐ (Production-ready Event-Streaming!)
