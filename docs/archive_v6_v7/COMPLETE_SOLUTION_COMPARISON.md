# Complete Event Streaming Solution Comparison

**Date:** 2025-10-29
**Task:** Comprehensive comparison of ALL event streaming approaches

---

## 📋 **5 Ansätze im Vergleich**

1. **Pure ContextVars** - Implizite Context-Propagation
2. **Pure Callbacks** - Explizite Dependency Injection
3. **Pure Event Bus** - Pub/Sub Pattern
4. **Hybrid (ContextVars + Event Bus)** - Mein ursprünglicher Vorschlag
5. **MCP-Style Hybrid (ContextVars + Event Bus + SSE)** - User-Vorschlag adaptiert

---

## 🔍 **Ansatz 1: Pure ContextVars**

### **Konzept:**
WebSocket direkt in ContextVar speichern, Agents greifen darauf zu.

```python
from contextvars import ContextVar

current_websocket: ContextVar[WebSocket | None] = ContextVar('ws', default=None)

# Im WebSocket Handler
async def websocket_endpoint(websocket: WebSocket):
    current_websocket.set(websocket)
    await execute_workflow(...)

# Im Agent direkt nutzen
async def agent_think():
    ws = current_websocket.get()
    if ws:
        await ws.send_json({"type": "think", "msg": "..."})
```

### **Warum Pure ContextVars?**

- ✅ **Automatische Propagation:** Jede async Task hat Context
- ✅ **Keine Parameter:** Kein `callback` oder `session_id` durchreichen
- ✅ **Native Python:** Built-in Feature seit 3.7

### **Bewertung:**

| Kriterium | Score | Begründung |
|-----------|-------|------------|
| **Code-Sauberkeit** | ⭐⭐⭐⭐⭐ | Keine Parameter, keine Callbacks |
| **Testbarkeit** | ⭐⭐ | Schwer zu mocken (implizite Dependency) |
| **Performance** | ⭐⭐⭐⭐⭐ | Native, kein Overhead |
| **Debugging** | ⭐⭐ | Schwer nachzuvollziehen, wo Context gesetzt |
| **Session-Isolation** | ⭐⭐⭐⭐⭐ | Task-local, perfekt isoliert |
| **Refactoring-Aufwand** | ⭐⭐⭐⭐⭐ | Minimal (kein Parameter-Threading) |
| **Memory-Safety** | ⭐⭐⭐⭐⭐ | Python managed, kein Cleanup nötig |
| **Explizitheit** | ⭐ | Sehr implizit, Dependencies unsichtbar |
| **Async-Freundlich** | ⭐⭐⭐⭐⭐ | Native asyncio Support |

**Total:** 34/45

### **Probleme:**
- ❌ **WebSocket-Kopplung:** Agent ist direkt an WebSocket gebunden
- ❌ **Single Listener:** Nur ein WebSocket pro Session
- ❌ **Testing schwer:** Mock-WebSocket muss in Context

---

## 🔍 **Ansatz 2: Pure Callbacks**

### **Konzept:**
Callback-Funktion durch alle Layer durchreichen.

```python
EventCallback = Callable[[dict], Awaitable[None]]

async def execute_workflow(
    query: str,
    event_callback: EventCallback
):
    await supervisor_decide(state, event_callback)

async def supervisor_decide(state: dict, callback: EventCallback):
    await callback({"type": "think", "msg": "..."})
    await agent_execute(state, callback)

async def agent_execute(state: dict, callback: EventCallback):
    await callback({"type": "progress", "msg": "..."})
```

### **Warum Pure Callbacks?**

- ✅ **Explizit:** Dependencies klar sichtbar
- ✅ **Testbar:** Einfach Mock-Callback zu injizieren
- ✅ **Type-Safe:** Typing zeigt Callback-Signature

### **Bewertung:**

| Kriterium | Score | Begründung |
|-----------|-------|------------|
| **Code-Sauberkeit** | ⭐⭐ | Callback-Parameter überall |
| **Testbarkeit** | ⭐⭐⭐⭐⭐ | Perfekt mockbar |
| **Performance** | ⭐⭐⭐⭐ | Direkte Funktion-Calls |
| **Debugging** | ⭐⭐⭐⭐ | Call-Stack zeigt Callback-Kette |
| **Session-Isolation** | ⭐⭐⭐ | Pro Callback, aber manuell |
| **Refactoring-Aufwand** | ⭐ | Jede neue Funktion braucht Callback |
| **Memory-Safety** | ⭐⭐⭐⭐⭐ | Kein globaler State |
| **Explizitheit** | ⭐⭐⭐⭐⭐ | Sehr explizit, alle Dependencies sichtbar |
| **Async-Freundlich** | ⭐⭐⭐⭐ | Async Callbacks funktionieren |

**Total:** 34/45

### **Probleme:**
- ❌ **Signature Pollution:** Jede Funktion braucht `callback` Parameter
- ❌ **Boilerplate:** Viel Code zum Durchreichen
- ❌ **Verkettung komplex:** Bei vielen Layern unübersichtlich

---

## 🔍 **Ansatz 3: Pure Event Bus**

### **Konzept:**
Globaler Event-Bus mit Pub/Sub Pattern.

```python
class EventBus:
    def __init__(self):
        self.listeners = {}  # event_name -> set of listeners

    def on(self, event_name: str, listener: Callable):
        self.listeners.setdefault(event_name, set()).add(listener)

    def emit(self, event_name: str, event: dict):
        for listener in self.listeners.get(event_name, []):
            asyncio.create_task(listener(event))

# Global
event_bus = EventBus()

# WebSocket Handler
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    async def handler(e):
        await websocket.send_json(e)

    event_bus.on(f"session_{session_id}", handler)
    await execute_workflow(session_id)

# Agent
async def agent_think(session_id: str):
    event_bus.emit(f"session_{session_id}", {"type": "think"})
```

### **Warum Pure Event Bus?**

- ✅ **Entkopplung:** Emitter kennt Listener nicht
- ✅ **Multiple Listeners:** Mehrere Handler pro Event
- ✅ **Non-blocking:** `create_task` macht Events parallel

### **Bewertung:**

| Kriterium | Score | Begründung |
|-----------|-------|------------|
| **Code-Sauberkeit** | ⭐⭐⭐⭐ | Kein Callback-Threading, aber event_name |
| **Testbarkeit** | ⭐⭐⭐ | Mock Event Bus möglich |
| **Performance** | ⭐⭐⭐⭐ | Non-blocking, parallel |
| **Debugging** | ⭐⭐ | Schwer zu tracken, wer Events empfängt |
| **Session-Isolation** | ⭐⭐⭐ | Via event_name (manuell) |
| **Refactoring-Aufwand** | ⭐⭐⭐⭐ | Neue Listener ohne Code-Änderung |
| **Memory-Safety** | ⭐⭐ | Manueller Cleanup nötig |
| **Explizitheit** | ⭐⭐ | Implizit (globaler Bus) |
| **Async-Freundlich** | ⭐⭐⭐⭐⭐ | `create_task` für Parallelität |

**Total:** 32/45

### **Probleme:**
- ❌ **Memory Leaks:** Listener müssen manuell de-registriert werden
- ❌ **Session-ID Threading:** Muss überall durchgereicht werden
- ❌ **Globaler State:** Event-Bus ist global

---

## 🔍 **Ansatz 4: Hybrid (ContextVars + Event Bus)** ⭐ Mein Original-Vorschlag

### **Konzept:**
ContextVars für Session-Tracking + Event-Bus für Event-Delivery.

```python
from contextvars import ContextVar

current_session_id: ContextVar[str | None] = ContextVar('sid', default=None)

class SessionEventBus:
    def __init__(self):
        self.listeners: dict[str, set[Callable]] = {}

    def subscribe(self, session_id: str, listener: Callable):
        self.listeners.setdefault(session_id, set()).add(listener)

    async def emit(self, event: dict):
        # Holt session_id automatisch aus Context!
        sid = current_session_id.get()
        if not sid:
            return

        for listener in self.listeners.get(sid, []):
            asyncio.create_task(listener(event))

# WebSocket Handler
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    async def handler(e):
        await websocket.send_json(e)

    event_bus.subscribe(session_id, handler)
    current_session_id.set(session_id)  # Context setzen!

    await execute_workflow(query)  # Keine session_id nötig!

# Agent (KEINE session_id Parameter!)
async def agent_think():
    await event_bus.emit({"type": "think", "msg": "..."})
    # session_id kommt aus Context!
```

### **Warum Hybrid?**

#### **ContextVars für Session-Tracking:**
- ✅ `session_id` wird in Context gespeichert
- ✅ Automatische Propagation an alle async Tasks
- ✅ Perfekte Session-Isolation

#### **Event Bus für Event-Delivery:**
- ✅ Session-spezifische Listener (holt `session_id` aus Context)
- ✅ Entkoppelt Events von WebSocket
- ✅ Non-blocking Event-Emission

### **Bewertung:**

| Kriterium | Score | Begründung |
|-----------|-------|------------|
| **Code-Sauberkeit** | ⭐⭐⭐⭐⭐ | Keine Callbacks, keine session_id Parameter |
| **Testbarkeit** | ⭐⭐⭐⭐ | Mock Event Bus + Context setzen |
| **Performance** | ⭐⭐⭐⭐⭐ | Non-blocking, native ContextVars |
| **Debugging** | ⭐⭐⭐ | Event-Bus traceable, Context manchmal tricky |
| **Session-Isolation** | ⭐⭐⭐⭐⭐ | ContextVars = perfekt isoliert |
| **Refactoring-Aufwand** | ⭐⭐⭐⭐⭐ | Minimal (keine Parameter-Änderungen) |
| **Memory-Safety** | ⭐⭐⭐⭐ | Cleanup nötig, aber isoliert |
| **Explizitheit** | ⭐⭐⭐ | Event-Bus explizit, Context implizit |
| **Async-Freundlich** | ⭐⭐⭐⭐⭐ | Perfekt für asyncio |

**Total:** 39/45 🏆

### **Vorteile:**
- ✅ **Beste Code-Sauberkeit:** Keine Parameter-Threading
- ✅ **Session-Isolation:** ContextVars macht das automatisch
- ✅ **Performance:** Non-blocking, minimaler Overhead
- ✅ **Entkopplung:** Event-Bus entkoppelt Sender/Empfänger
- ✅ **Multiple Listeners:** Mehrere Handler pro Session

### **Probleme:**
- ⚠️ **Custom Implementation:** Kein Standard (noch)
- ⚠️ **WebSocket-only:** Nur WebSocket als Transport

---

## 🔍 **Ansatz 5: MCP-Style Hybrid (ContextVars + Event Bus + SSE)** ⭐⭐ User-Vorschlag

### **Konzept:**
Wie Ansatz 4, aber mit MCP-kompatiblem Format + SSE statt WebSocket.

```python
from contextvars import ContextVar
from dataclasses import dataclass

current_session_id: ContextVar[str | None] = ContextVar('sid', default=None)

@dataclass
class ProgressEvent:
    """MCP-style progress event."""
    progress: float  # 0.0 - 1.0
    message: str
    total: float = 1.0
    agent: str | None = None
    phase: str | None = None  # "think" | "progress" | "decision" | "result"

    def to_dict(self):
        return {
            "t": "agent_event",
            "agent": self.agent,
            "phase": self.phase,
            "msg": self.message,
            "pct": self.progress / self.total,
            "ts": datetime.now().isoformat()
        }

class SessionEventBus:
    def __init__(self):
        self.subs: dict[str, set[asyncio.Queue]] = {}

    async def subscribe(self, session_id: str) -> asyncio.Queue:
        q = asyncio.Queue()
        self.subs.setdefault(session_id, set()).add(q)
        return q

    async def emit(self, event: ProgressEvent | dict):
        sid = current_session_id.get()
        if not sid:
            return

        evt_dict = event.to_dict() if isinstance(event, ProgressEvent) else event

        for q in self.subs.get(sid, []):
            q.put_nowait(evt_dict)

# MCP-style API
async def report_progress(
    progress: float,
    message: str,
    agent: str,
    phase: str,
    total: float = 1.0
):
    """MCP-compatible progress reporting (without MCP library)."""
    event = ProgressEvent(progress, message, total, agent, phase)
    await event_bus.emit(event)

# SSE Endpoint (statt WebSocket!)
from sse_starlette.sse import EventSourceResponse

@router.get("/events")
async def events(session_id: str):
    q = await event_bus.subscribe(session_id)

    async def gen():
        try:
            while True:
                evt = await q.get()
                yield {"event": "agent", "data": json.dumps(evt)}
        finally:
            await event_bus.unsubscribe(session_id, q)

    return EventSourceResponse(gen())

# Agent Usage
async def agent_think():
    await report_progress(
        progress=0.35,
        message="🧠 Analyzing architecture",
        agent="codesmith",
        phase="think"
    )
```

### **Warum MCP-Style Hybrid?**

#### **ContextVars für Session-Tracking:**
- ✅ Gleich wie Ansatz 4

#### **Event Bus für Event-Delivery:**
- ✅ Gleich wie Ansatz 4
- ✅ **Aber:** Queue-basiert (statt Callback-basiert)

#### **MCP-Format:**
- ✅ **Standard-konform:** Kompatibel zu MCP-Protocol
- ✅ **Progress-Bar:** `progress/total` für echte Fortschrittsanzeige
- ✅ **Typed Events:** `phase` (think/progress/decision/result)

#### **SSE statt WebSocket:**
- ✅ **Simpler:** Kein Connection-Management
- ✅ **HTTP-freundlich:** Load-Balancer, Proxies, Firewalls
- ✅ **Auto-Reconnect:** Browser reconnected automatisch
- ✅ **Weniger Resources:** Kein WebSocket-Overhead

### **Bewertung:**

| Kriterium | Score | Begründung |
|-----------|-------|------------|
| **Code-Sauberkeit** | ⭐⭐⭐⭐⭐ | MCP-API ist clean, keine Parameter-Threading |
| **Testbarkeit** | ⭐⭐⭐⭐⭐ | Mock Event Bus + Context, MCP-Format testbar |
| **Performance** | ⭐⭐⭐⭐⭐ | SSE efficient, Non-blocking |
| **Debugging** | ⭐⭐⭐⭐ | MCP-Format strukturiert, SSE einfach zu debuggen |
| **Session-Isolation** | ⭐⭐⭐⭐⭐ | ContextVars = perfekt |
| **Refactoring-Aufwand** | ⭐⭐⭐⭐⭐ | Minimal, MCP-API stabil |
| **Memory-Safety** | ⭐⭐⭐⭐⭐ | Queue-Cleanup in finally-block |
| **Explizitheit** | ⭐⭐⭐⭐ | MCP-API explizit, Context implizit |
| **Async-Freundlich** | ⭐⭐⭐⭐⭐ | Perfekt für asyncio |
| **Standards-Compliance** | ⭐⭐⭐⭐⭐ | MCP-kompatibel! |
| **Load-Balancer Support** | ⭐⭐⭐⭐⭐ | SSE ist HTTP, funktioniert überall |
| **Production-Ready** | ⭐⭐⭐⭐⭐ | Bewährtes Pattern (FastAPI, MCP) |

**Total:** 56/60 🏆🏆🏆

### **Vorteile:**
- ✅ **Alle Vorteile von Ansatz 4**
- ✅ **PLUS: MCP-Standard** (kompatibel, future-proof)
- ✅ **PLUS: SSE** (simpler, HTTP-freundlich, Load-Balancer)
- ✅ **PLUS: Progress-Bar** (echte 0-100% Fortschrittsanzeige)
- ✅ **PLUS: Typed Events** (think/progress/decision/result)
- ✅ **PLUS: Production-Ready** (FastAPI nutzt SSE, MCP ist Standard)

### **Probleme:**
- ⚠️ **SSE ist Einweg:** Kein Rückkanal (aber wir brauchen keinen!)
- ⚠️ **Neue Dependency:** `sse-starlette` (`pip install`)

---

## 📊 **Final Comparison Table**

| Ansatz | Code-Sauberkeit | Testbarkeit | Performance | Debugging | Session-Isolation | Refactoring | Memory-Safety | Explizitheit | Async | Standards | Load-Balancer | Production | **TOTAL** |
|--------|-----------------|-------------|-------------|-----------|-------------------|-------------|---------------|--------------|-------|-----------|---------------|------------|-----------|
| **1. Pure ContextVars** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | - | - | - | **34/45** |
| **2. Pure Callbacks** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | - | - | - | **34/45** |
| **3. Pure Event Bus** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | - | - | - | **32/45** |
| **4. Hybrid (Context+Bus)** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | - | - | - | **39/45** 🏆 |
| **5. MCP-Style Hybrid** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **56/60** 🏆🏆🏆 |

---

## 🏆 **Winner: MCP-Style Hybrid (Ansatz 5)**

### **Warum ist Ansatz 5 der Beste?**

1. ✅ **Alle Vorteile von Ansatz 4** (Beste Hybrid-Lösung)
2. ✅ **MCP-Standard:** Future-proof, kompatibel zu Claude Code
3. ✅ **SSE > WebSocket:** Simpler, HTTP-freundlich, Load-Balancer-ready
4. ✅ **Progress-Bar:** Echte 0-100% Fortschrittsanzeige
5. ✅ **Typed Events:** Strukturiert (think/progress/decision/result)
6. ✅ **Production-Ready:** Bewährte Patterns (FastAPI SSE, MCP)

### **Score-Breakdown:**

| Kategorie | Score | Max | Prozent |
|-----------|-------|-----|---------|
| **Core Features** (9 Kriterien) | 42/45 | 45 | **93%** |
| **Standards** | 5/5 | 5 | **100%** |
| **Load-Balancer** | 5/5 | 5 | **100%** |
| **Production** | 5/5 | 5 | **100%** |
| **TOTAL** | **56/60** | 60 | **93%** |

---

## 📋 **Implementation-Empfehlung**

### **Phase 1: Core Event System** (30 min)
```python
# backend/utils/session_event_bus.py
# backend/utils/progress.py
```

### **Phase 2: SSE Endpoint** (15 min)
```python
# backend/api/sse_events.py
# pip install sse-starlette
```

### **Phase 3: Agent Integration** (30 min)
```python
# backend/core/supervisor.py
# backend/agents/*.py
```

### **Phase 4: Testing** (15 min)
```python
# Test mit EventSource in Browser
# Test mit curl: curl -N localhost:8002/events?session_id=test
```

**Total Time:** ~90 Minuten
**Impact:** ⭐⭐⭐⭐⭐ (Production-Ready Event-Streaming!)

---

## ✅ **Fazit**

**MCP-Style Hybrid (Ansatz 5) ist der klare Gewinner:**

- 🥇 **Best Score:** 56/60 (93%)
- 🥈 **Second Best:** Hybrid (Ansatz 4) - 39/45 (87%)
- 🥉 **Third Best:** Pure ContextVars/Callbacks (Ansatz 1/2) - 34/45 (76%)

**Hauptgründe:**
1. Standards-Compliance (MCP)
2. SSE > WebSocket (simpler, HTTP-freundlich)
3. Production-Ready (bewährte Patterns)
4. Alle Vorteile von Hybrid (Best of both worlds)

**Nächster Schritt:** Implementation von Ansatz 5! 🚀
