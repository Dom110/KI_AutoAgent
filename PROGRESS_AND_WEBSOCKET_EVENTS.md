# 📡 Progress Callbacks & WebSocket Events - Real-time Communication

**Version:** v7.0 Pure MCP  
**Date:** 2025-11-10  
**Framework:** FastAPI WebSocket + MCP Progress Notifications

---

## Overview: Real-Time Event Flow

```
MCP Server (research_agent)
        │
        ├─ Progress: 25%
        │ (via $/progress notification)
        │
        ▼
MCPManager (progress_callback)
        │
        ├─ event_manager.send_event(session_id, {...})
        │
        ▼
Server Event Queue
        │
        ├─ WebSocket Manager
        │
        ▼
Connected Clients (Browser)
        │
        └─ Real-time UI update! 🎉
```

---

## 🔄 Progress Callbacks: How It Works

### Step 1: MCP Server Sends Progress

**Location:** `mcp_servers/research_agent_server.py`

```python
async def send_progress(self, progress: float, message: str):
    """Send $/progress notification to parent"""
    
    # $/progress is standard MCP notification format
    notification = {
        "jsonrpc": "2.0",
        "method": "$/progress",
        "params": {
            "progress": progress,        # 0.0 to 1.0
            "total": 1.0,               # Always 1.0
            "message": message,          # Human-readable status
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    # Send to stdout (MCP protocol)
    await self.send_message(notification)
    
    # Example:
    await self.send_progress(0.25, "🔍 Analyzing workspace...")
    await self.send_progress(0.50, "🌐 Searching web for technologies...")
    await self.send_progress(0.75, "📝 Compiling research results...")
    await self.send_progress(1.0, "✅ Research complete!")
```

### Step 2: MCPManager Receives & Routes Progress

**Location:** `backend/utils/mcp_manager.py`

```python
class MCPManager:
    def __init__(self, workspace_path: str, progress_callback=None):
        # ✅ Optional callback for progress updates
        self.progress_callback = progress_callback
        
    async def _handle_progress_notification(self, notification: dict):
        """Handle $/progress notification from MCP server"""
        
        params = notification.get("params", {})
        server = self.current_server  # Which server is reporting?
        
        # Call the callback if provided
        if self.progress_callback:
            self.progress_callback(
                server=server,
                message=params.get("message"),
                progress=params.get("progress")
            )
```

### Step 3: Workflow Routes to Event Manager

**Location:** `backend/workflow_v7_mcp.py:803`

```python
def progress_callback(server: str, message: str, progress: float):
    """Callback from MCP server - route to event manager"""
    
    logger.info(f"📡 Progress [{server}]: {progress*100:.0f}% - {message}")
    
    # Send to all connected WebSocket clients
    event_manager.send_event(session_id, {
        "type": "mcp_progress",      # ← Event type
        "server": server,             # ← Which agent?
        "message": message,           # ← Status message
        "progress": progress,         # ← Progress 0.0-1.0
        "timestamp": datetime.now().isoformat()
    })

# Wire up the callback when creating MCPManager
mcp = get_mcp_manager(
    workspace_path=workspace_path,
    progress_callback=progress_callback  # ← Pass callback here!
)
```

### Step 4: WebSocket Sends to Browser

**Location:** `backend/api/server_v7_mcp.py:675+`

```python
async def websocket_chat(websocket: WebSocket):
    """WebSocket connection handler"""
    
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Listen for events
            event = event_manager.get_event(client_id)
            
            if event["type"] == "mcp_progress":
                # ✅ Send progress to browser
                await manager.send_json(client_id, {
                    "type": "progress",
                    "server": event["server"],
                    "message": event["message"],
                    "progress": event["progress"]
                })
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(client_id)
```

---

## 📊 Complete Progress Flow Example

### Real-World Example: Research Agent

```
Time    Agent              Output                      Progress
────────────────────────────────────────────────────────────────
t0      research_agent     Starting research...        0%
        │
        ├─ $/progress(0.0, "Starting research...")
        │
t1      MCPManager         ← receives progress         
        │
        ├─ progress_callback("research_agent", "Starting...", 0.0)
        │
t2      Event Manager      send_event(session, {...})
        │
        ├─ WebSocket: {"type": "progress", "progress": 0.0}
        │
t3      Browser UI         Display: "🔍 Starting..."  ✅

────────────────────────────────────────────────────────────────

t10     research_agent     Analyzing workspace...      25%
        │
        ├─ $/progress(0.25, "🔍 Analyzing workspace...")
        │
t11     MCPManager         ← receives 0.25
        │
        ├─ progress_callback("research_agent", "Analyzing...", 0.25)
        │
t12     Event Manager      send_event(session, {...})
        │
        ├─ WebSocket: {"type": "progress", "progress": 0.25}
        │
t13     Browser UI         Progress Bar: ████░░░░░░ 25%  ✅

────────────────────────────────────────────────────────────────

t20     research_agent     Searching web...            50%
t21     MCPManager         ← receives 0.50
t22     Event Manager      send_event(session, {...})
t23     Browser UI         Progress Bar: ████████░░ 50%  ✅

────────────────────────────────────────────────────────────────

t30     research_agent     Compiling results...        75%
t31     MCPManager         ← receives 0.75
t32     Event Manager      send_event(session, {...})
t33     Browser UI         Progress Bar: ████████░░ 75%  ✅

────────────────────────────────────────────────────────────────

t40     research_agent     Complete!                   100%
        │
        ├─ $/progress(1.0, "✅ Research complete!")
        ├─ return result
        │
t41     MCPManager         ← receives 1.0 & result
        │
        ├─ progress_callback("research_agent", "Complete!", 1.0)
        │
t42     Event Manager      send_event(session, {...})
        │
        ├─ WebSocket: {"type": "progress", "progress": 1.0}
        ├─ WebSocket: {"type": "agent_complete", "agent": "research", ...}
        │
t43     Browser UI         ✅ Research Complete!
                            Next: Architect Agent...
```

---

## 📨 All WebSocket Event Types

The system sends 7 different event types:

### Event 1: `supervisor_decision`
**Sent:** When Supervisor makes a routing decision

```json
{
  "type": "supervisor_decision",
  "decision": "research",
  "reason": "Need to understand workspace structure first",
  "iteration": 1,
  "timestamp": "2025-11-10T20:30:00Z"
}
```

**When:** After supervisor_node completes  
**Used for:** Show which agent is being called next

---

### Event 2: `agent_start`
**Sent:** When an agent starts execution

```json
{
  "type": "agent_start",
  "agent": "research_agent",
  "agent_name": "Research Agent",
  "instructions": "Analyze workspace and search for relevant technologies",
  "timestamp": "2025-11-10T20:30:05Z"
}
```

**When:** Before calling mcp.call()  
**Used for:** Show which agent is currently running

---

### Event 3: `agent_complete`
**Sent:** When an agent finishes execution

```json
{
  "type": "agent_complete",
  "agent": "research_agent",
  "agent_name": "Research Agent",
  "result_summary": "Found 5 technologies, 10 best practices",
  "result_size": "2.3 KB",
  "duration_ms": 3452,
  "timestamp": "2025-11-10T20:30:08Z"
}
```

**When:** After mcp.call() returns  
**Used for:** Show completion status and time taken

---

### Event 4: `research_request`
**Sent:** When an agent requests web research

```json
{
  "type": "research_request",
  "agent": "codesmith_agent",
  "query": "Best practices for FastAPI error handling",
  "timestamp": "2025-11-10T20:31:00Z"
}
```

**When:** During agent execution (via MCP call)  
**Used for:** Show what research is being done

---

### Event 5: `hitl_request`
**Sent:** When system requests human input

```json
{
  "type": "hitl_request",
  "request_type": "approve_architecture",
  "message": "Does this architecture look good to you?",
  "context": {
    "proposed_structure": {...},
    "reasoning": "..."
  },
  "timeout_seconds": 300,
  "timestamp": "2025-11-10T20:32:00Z"
}
```

**When:** System needs human approval  
**Used for:** Show modal/dialog asking for user input

---

### Event 6: `command_routing`
**Sent:** When supervisor routes to next command

```json
{
  "type": "command_routing",
  "from_node": "supervisor",
  "to_node": "architect",
  "command": {
    "goto": "architect",
    "update": {
      "last_agent": "supervisor",
      "iteration": 2
    }
  },
  "timestamp": "2025-11-10T20:33:00Z"
}
```

**When:** LangGraph Command is executed  
**Used for:** Debugging/visualization of workflow

---

### Event 7: `mcp_progress` ⭐ NEW!
**Sent:** MCP server progress notifications

```json
{
  "type": "mcp_progress",
  "server": "research_agent",
  "message": "🌐 Searching web for technologies...",
  "progress": 0.50,
  "timestamp": "2025-11-10T20:30:06Z"
}
```

**When:** MCP server sends $/progress  
**Used for:** Real-time progress bars and status

---

## 💡 Using Progress in Frontend

### Example: React Component

```jsx
function AgentProgress({ event }) {
  const [progress, setProgress] = useState(0);
  
  useEffect(() => {
    if (event.type === "mcp_progress") {
      setProgress(event.progress * 100);
    }
  }, [event]);
  
  return (
    <div className="progress-bar">
      <div className="progress-fill" style={{width: `${progress}%`}} />
      <span className="progress-text">
        {event.message} ({progress.toFixed(0)}%)
      </span>
    </div>
  );
}
```

### WebSocket Connection

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8002/ws/chat');

// Listen for events
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === "mcp_progress") {
    // Update progress bar
    updateProgressBar(data.server, data.progress);
  }
  
  if (data.type === "agent_complete") {
    // Show agent finished
    showAgentComplete(data.agent_name, data.duration_ms);
  }
};
```

---

## 🔧 Implementing Progress in New MCP Server

### Checklist: Add Progress to Custom Server

```python
class MyCustomServer:
    async def send_progress(self, progress: float, message: str):
        """✅ Required for progress notifications"""
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
    
    async def my_tool(self, args):
        """Tool implementation"""
        
        # Step 1: Start
        await self.send_progress(0.0, "Starting operation...")
        
        # Step 2: Processing
        await self.send_progress(0.25, "Processing data...")
        
        # Step 3: Mid-point
        result = await some_async_operation()
        await self.send_progress(0.50, "Half done...")
        
        # Step 4: Finalizing
        await self.send_progress(0.75, "Finalizing...")
        
        # Step 5: Complete
        await self.send_progress(1.0, "✅ Complete!")
        
        return result
```

---

## 📚 Progress Best Practices

### DO ✅
- Start with 0.0, end with 1.0
- Use meaningful messages (with emojis!)
- Report progress every 5-10% or logical step
- Include what you're doing in the message
- Always reach 1.0 (even on error!)

### DON'T ❌
- Don't jump from 0% to 100% instantly
- Don't send confusing messages
- Don't skip $/progress notifications
- Don't forget to flush stdout after sending
- Don't ignore errors (report them via message!)

### Example: Good vs Bad

**❌ BAD:**
```python
await send_progress(0.0, "Starting...")
# ... 10 seconds of work ...
await send_progress(1.0, "Done!")
# UI shows nothing for 10 seconds!
```

**✅ GOOD:**
```python
await send_progress(0.0, "Initializing...")
await asyncio.sleep(1)

await send_progress(0.2, "🔍 Analyzing files...")
await asyncio.sleep(1)

await send_progress(0.4, "📝 Processing data...")
await asyncio.sleep(1)

await send_progress(0.6, "🔗 Building relationships...")
await asyncio.sleep(1)

await send_progress(0.8, "✅ Finalizing...")
await asyncio.sleep(1)

await send_progress(1.0, "✅ Complete!")
```

---

## 🐛 Debugging Progress Issues

### Issue: No Progress Updates Showing

**Check:**
1. ✅ MCP server sends $/progress notifications?
   ```bash
   grep "send_progress" mcp_servers/research_agent_server.py
   ```

2. ✅ progress_callback wired in workflow?
   ```bash
   grep "progress_callback" backend/workflow_v7_mcp.py
   ```

3. ✅ event_manager.send_event() called?
   ```bash
   grep "send_event.*mcp_progress" backend/workflow_v7_mcp.py
   ```

4. ✅ WebSocket connection active?
   ```bash
   grep "ws://localhost:8002" logs/
   ```

### Issue: Progress Stuck at 0%

**Check:**
1. ✅ Progress value is float (not int)?
   ```python
   # ❌ WRONG:
   await send_progress(1, "Done!")
   
   # ✅ CORRECT:
   await send_progress(1.0, "Done!")
   ```

2. ✅ stdout flushed after each message?
   ```python
   sys.stdout.flush()  # ← Must do this!
   ```

### Issue: Progress Goes Over 100%

**Check:**
1. ✅ Progress value between 0.0 and 1.0?
   ```python
   # ❌ WRONG:
   await send_progress(200, "Done!")
   
   # ✅ CORRECT:
   await send_progress(1.0, "Done!")
   ```

---

## 🔗 References

- **MCP Server Example:** `mcp_servers/research_agent_server.py`
- **Workflow Integration:** `backend/workflow_v7_mcp.py:803+`
- **Server Events:** `backend/api/server_v7_mcp.py:388+`
- **WebSocket Handler:** `backend/api/server_v7_mcp.py:675+`

---

**Updated:** 2025-11-10  
**Status:** ✅ Complete  
**Related:** LANGGRAPH_ARCHITECTURE.md, START_HERE.md, STARTUP_REQUIREMENTS.md
