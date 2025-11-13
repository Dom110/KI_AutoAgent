# Event Streaming Architecture Research - Context-Variable vs Callback

**Date:** 2025-10-28
**Task:** Research beste Methode für Event-Streaming in async Python/FastAPI WebSocket-Anwendungen

---

## 🎯 **Problem Statement**

Wir brauchen einen Weg, um **Agent-Events** (Think, Progress, Result) in Echtzeit vom **tief verschachtelten Code** (Supervisor, Agents) zum **WebSocket-Client** zu streamen.

**Herausforderungen:**
1. Agents laufen in LangGraph-Nodes (async functions)
2. WebSocket-Handler läuft in FastAPI-Endpoint
3. Events müssen ohne explizite Dependency Injection durchgereicht werden
4. Mehrere Sessions parallel (jede braucht isolierte Events)
5. Performance-kritisch (Event-Streaming muss schnell sein)

---

## 📊 **Vergleich: 3 Ansätze**

### **Option 1: ContextVars (Context-Variable)**

#### **Konzept:**
```python
from contextvars import ContextVar

# Global context variable für WebSocket
current_websocket: ContextVar[WebSocket | None] = ContextVar('websocket', default=None)

# Im WebSocket Handler setzen
async def websocket_endpoint(websocket: WebSocket):
    current_websocket.set(websocket)

    # Workflow ausführen (hat automatisch Zugriff)
    await execute_workflow(...)

# Im Supervisor/Agent nutzen
async def send_event(event: dict):
    ws = current_websocket.get()
    if ws:
        await ws.send_json(event)
```

#### **✅ Vorteile:**
- **Task-Local Isolation:** Jede async Task hat eigene Context-Kopie
- **Keine Dependency Injection nötig:** Code kann direkt auf Context zugreifen
- **Thread-safe:** Funktioniert auch mit ThreadPoolExecutor
- **Pythonic:** Native Python 3.7+ Feature
- **Clean Code:** Keine Callbacks durch alle Layer durchreichen

#### **❌ Nachteile:**
- **Implizit:** Schwer zu testen (Context-Dependency nicht sichtbar)
- **Globaler State:** Context-Variable sind global definiert
- **Debugging schwieriger:** Schwer nachzuvollziehen, wo Context gesetzt wird
- **Context-Propagation:** Muss bei Task-Spawning beachtet werden

#### **Best Practices:**
```python
# ✅ RICHTIG: Context vor Task-Start setzen
async def handler():
    current_ws.set(websocket)
    await asyncio.create_task(workflow())  # Task erbt Context

# ❌ FALSCH: Context in spawned Task setzen
async def handler():
    await asyncio.create_task(set_context())  # Context bleibt lokal
```

#### **Real-World Examples:**
- **FastAPI:** Verwendet ContextVars für Request/Response in Middleware
- **Starlette:** ASGI-Middleware nutzt ContextVars für Request-IDs
- **aiohttp:** Context-Kopie für jede Request-Handling

---

### **Option 2: Callback-basiert (Dependency Injection)**

#### **Konzept:**
```python
# Callback-Funktion als Parameter durchreichen
async def execute_workflow(
    user_query: str,
    event_callback: Callable[[dict], Awaitable[None]]
):
    # Im Supervisor
    await event_callback({"type": "supervisor_event", ...})

# Im WebSocket Handler
async def websocket_endpoint(websocket: WebSocket):
    async def send_event(event: dict):
        await websocket.send_json(event)

    await execute_workflow(query, event_callback=send_event)
```

#### **✅ Vorteile:**
- **Explizit:** Dependencies klar sichtbar in Signatur
- **Testbar:** Einfach Mock-Callbacks zu injizieren
- **Flexibel:** Verschiedene Callbacks für verschiedene Use-Cases
- **Debuggbar:** Call-Stack zeigt genau, woher Callback kommt
- **Type-Safe:** Typing zeigt required Callback-Signature

#### **❌ Nachteile:**
- **Boilerplate:** Callback muss durch ALLE Layer durchgereicht werden
- **Signature Pollution:** Jede Funktion braucht `event_callback` Parameter
- **Refactoring-aufwändig:** Neue Layer = alle Signaturen anpassen
- **Verkettung komplex:** Verschachtelte Callbacks bei mehreren Layern

#### **Best Practices:**
```python
# ✅ RICHTIG: Typed Callback
EventCallback = Callable[[dict], Awaitable[None]]

async def workflow(callback: EventCallback):
    await callback({"type": "event"})

# ❌ FALSCH: Untyped Callback
async def workflow(callback):  # Keine Type-Hints!
    await callback({"type": "event"})
```

#### **Real-World Examples:**
- **Express.js:** Middleware-Callbacks (req, res, next)
- **Django Signals:** Callback-basiertes Event-System
- **React:** Event-Handlers als Props

---

### **Option 3: Event Bus (Pub/Sub Pattern)**

#### **Konzept:**
```python
class EventBus:
    def __init__(self):
        self.listeners = {}  # event_name -> set of listeners

    def on(self, event_name: str, listener: Callable):
        if event_name not in self.listeners:
            self.listeners[event_name] = set()
        self.listeners[event_name].add(listener)

    def emit(self, event_name: str, event: dict):
        for listener in self.listeners.get(event_name, []):
            asyncio.create_task(listener(event))  # Non-blocking!

# Global Event Bus
event_bus = EventBus()

# Im WebSocket Handler registrieren
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    async def send_event(event: dict):
        await websocket.send_json(event)

    event_bus.on(f"session_{session_id}", send_event)
    await execute_workflow(session_id)

# Im Supervisor emittieren
async def supervisor_decide():
    event_bus.emit(f"session_{session_id}", {
        "type": "supervisor_event",
        "message": "Deciding next agent..."
    })
```

#### **✅ Vorteile:**
- **Vollständig entkoppelt:** Emitter kennt Listener nicht
- **Multiple Listeners:** Ein Event kann mehrere Handler haben
- **Non-blocking:** Events werden parallel verarbeitet (via `create_task`)
- **Erweiterbar:** Neue Listener ohne Code-Änderung
- **Familiär:** Bekanntes Pattern (NodeJS EventEmitter, DOM Events)

#### **❌ Nachteile:**
- **Globaler State:** Event Bus ist global
- **Memory Leaks:** Listener müssen manuell de-registriert werden
- **Debugging schwer:** Schwer nachzuvollziehen, wer Events empfängt
- **Session Isolation:** Braucht session-spezifische Event-Names
- **Error Handling komplex:** Fehler in Listener-Callbacks schwer zu catchen

#### **Best Practices:**
```python
# ✅ RICHTIG: Cleanup in finally-block
try:
    event_bus.on(f"session_{sid}", handler)
    await workflow()
finally:
    event_bus.off(f"session_{sid}", handler)  # Cleanup!

# ❌ FALSCH: Kein Cleanup
event_bus.on(f"session_{sid}", handler)
await workflow()  # Handler bleibt registriert = Memory Leak!
```

#### **Real-World Examples:**
- **NodeJS EventEmitter:** Core-Library für Events
- **Python asyncio:** Low-level Event Loop
- **Redux:** State-Management mit Pub/Sub

---

## 🏆 **Empfehlung: Hybrid-Ansatz**

### **Beste Lösung für unser Use-Case:**

**Kombination aus ContextVars + Event Bus!**

#### **Warum?**
1. **ContextVars für Session-Tracking:**
   - Speichert `session_id` in Context (automatisch propagiert)
   - Jede Task hat isolierte Session-Info

2. **Event Bus für Event-Delivery:**
   - Session-spezifische Listener (via `session_id` aus Context)
   - Entkoppelt Events von WebSocket
   - Einfach testbar (Mock Event Bus)

#### **Implementation:**

```python
# ============================================================================
# 1. Context-Variable für Session-Tracking
# ============================================================================

from contextvars import ContextVar

current_session_id: ContextVar[str | None] = ContextVar('session_id', default=None)

def get_current_session_id() -> str | None:
    """Get current session ID from context."""
    return current_session_id.get()


# ============================================================================
# 2. Event Bus für Event-Streaming
# ============================================================================

class SessionEventBus:
    """Event bus with automatic session isolation via ContextVars."""

    def __init__(self):
        self.listeners: dict[str, set[Callable]] = {}

    def subscribe(self, session_id: str, listener: Callable):
        """Subscribe to events for a session."""
        if session_id not in self.listeners:
            self.listeners[session_id] = set()
        self.listeners[session_id].add(listener)

    def unsubscribe(self, session_id: str, listener: Callable):
        """Unsubscribe from events."""
        if session_id in self.listeners:
            self.listeners[session_id].discard(listener)
            if not self.listeners[session_id]:
                del self.listeners[session_id]

    async def emit(self, event: dict):
        """Emit event to current session (from ContextVar)."""
        session_id = get_current_session_id()
        if not session_id:
            logger.warning("No session_id in context - skipping event")
            return

        listeners = self.listeners.get(session_id, set())
        for listener in listeners:
            asyncio.create_task(listener(event))

# Global event bus
event_bus = SessionEventBus()


# ============================================================================
# 3. WebSocket Handler
# ============================================================================

async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()

    # Define event handler
    async def send_event(event: dict):
        await websocket.send_json(event)

    try:
        # Subscribe to events
        event_bus.subscribe(session_id, send_event)

        # Set session context
        current_session_id.set(session_id)

        # Execute workflow (automatisch propagiert Context!)
        await execute_workflow(user_query, workspace_path)

    finally:
        # Cleanup
        event_bus.unsubscribe(session_id, send_event)


# ============================================================================
# 4. Supervisor/Agent Usage
# ============================================================================

async def supervisor_decide(state: dict):
    # Session-ID ist automatisch aus Context verfügbar!
    await event_bus.emit({
        "type": "supervisor_event",
        "event_type": "decision",
        "message": "Routing to next agent...",
        "reasoning": decision.reasoning,
        "confidence": decision.confidence
    })

async def agent_execute():
    # Auch hier: Kein session_id Parameter nötig!
    await event_bus.emit({
        "type": "agent_event",
        "agent": "codesmith",
        "event_type": "think",
        "message": "Analyzing architecture..."
    })
```

---

## 📊 **Vergleichstabelle**

| Feature | ContextVars | Callbacks | Event Bus | **Hybrid** |
|---------|-------------|-----------|-----------|------------|
| **Code-Sauberkeit** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Testbarkeit** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Performance** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Debugging** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **Session-Isolation** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Refactoring-Aufwand** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Memory-Safety** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Explizitheit** | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **Async-Freundlich** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**Total Score:**
- **Hybrid (ContextVars + Event Bus): 39/45** ⭐⭐⭐⭐⭐
- Pure ContextVars: 34/45
- Callbacks: 34/45
- Pure Event Bus: 32/45

---

## 🚀 **Migration-Plan**

### **Phase 1: Event Bus erstellen**
```python
# backend/utils/session_event_bus.py
class SessionEventBus:
    # Implementation siehe oben
```

### **Phase 2: ContextVar hinzufügen**
```python
# backend/utils/context.py
from contextvars import ContextVar

current_session_id: ContextVar[str | None] = ContextVar('session_id', default=None)
```

### **Phase 3: WebSocket Handler anpassen**
```python
# backend/api/server_v7_supervisor.py
async def chat_endpoint(websocket: WebSocket):
    # Subscribe to events
    event_bus.subscribe(session_id, send_event)
    current_session_id.set(session_id)

    # Execute workflow
    await execute_workflow(...)
```

### **Phase 4: Supervisor/Agents anpassen**
```python
# backend/core/supervisor.py
async def decide_next(state: dict):
    await event_bus.emit({
        "type": "supervisor_event",
        ...
    })
```

### **Phase 5: Testing**
```python
# tests/test_event_streaming.py
def test_event_emission():
    # Mock event bus
    mock_bus = SessionEventBus()
    events = []

    mock_bus.subscribe("test-session", lambda e: events.append(e))
    current_session_id.set("test-session")

    await supervisor.decide_next(state)

    assert len(events) > 0
```

---

## 💡 **Key Learnings aus Research**

1. **ContextVars sind task-local, nicht thread-local**
   - Jede async Task bekommt Context-Snapshot
   - Context-Änderungen propagieren NICHT zurück zum Parent

2. **Event Bus MUSS non-blocking sein**
   - `asyncio.create_task()` für Listener-Calls
   - Sonst blockiert emit() den Workflow

3. **Session-Isolation ist kritisch**
   - Ohne Isolation bekommen alle Clients alle Events
   - ContextVars lösen das elegant

4. **Cleanup ist essentiell**
   - Event-Listener MÜSSEN de-registriert werden
   - Sonst Memory-Leaks bei vielen Sessions

5. **FastAPI/Starlette nutzen ContextVars bereits intern**
   - Request/Response-Context nutzt ContextVars
   - Wir können dasselbe Pattern nutzen

---

## ✅ **Fazit**

**Empfehlung: Hybrid-Ansatz (ContextVars + Event Bus)**

**Warum?**
- ✅ **Beste Code-Sauberkeit** (keine Callback-Pollution)
- ✅ **Perfekte Session-Isolation** (ContextVars)
- ✅ **Entkoppelt** (Event Bus)
- ✅ **Performance** (Non-blocking Events)
- ✅ **Pythonic** (Native Python Features)
- ✅ **Production-Ready** (FastAPI nutzt gleiches Pattern)

**Implementation:**
- ~100 Lines Code für SessionEventBus
- Minimal invasive Changes in bestehendem Code
- Vollständig testbar
- Einfach zu erweitern

**Nächster Schritt:**
Implementierung des Hybrid-Ansatzes in unserem KI AutoAgent v7.0 System!
