# KI AutoAgent v6.0 - Debugging Guide

**Version:** 6.0.0-alpha.1
**Last Updated:** 2025-10-08

---

## 🎯 Debugging Philosophy

**Set up debugging from Day 1, not when things break!**

v6.0 is built with debugging in mind:
- Comprehensive logging
- State inspection tools
- LangGraph Studio integration
- Python debugger ready

---

## 🛠️ Debugging Tools

### **1. Python Debugger (pdb)**

**Setup:**
```python
import pdb

# In any agent/workflow file:
def problematic_function(state):
    pdb.set_trace()  # Breakpoint here
    # ... rest of code
```

**Commands:**
- `n` (next): Execute next line
- `s` (step): Step into function
- `c` (continue): Continue until next breakpoint
- `l` (list): Show current code
- `p variable` (print): Print variable value
- `pp variable` (pretty print): Pretty print
- `w` (where): Show call stack
- `q` (quit): Quit debugger

**Example Session:**
```python
# workflow_v6.py
async def supervisor_node(state: SupervisorState):
    import pdb; pdb.set_trace()

    # Now you can inspect state:
    # (Pdb) p state
    # {'user_query': '...', 'workspace_path': '...'}
    # (Pdb) n  # Next line
```

---

### **2. LangGraph Studio**

**Installation:**
```bash
pip install langgraph-studio
```

**Usage:**
```python
# In workflow_v6.py
from langgraph.studio import visualize_graph

# After compiling workflow:
workflow = supervisor_graph.compile(checkpointer=checkpointer)

# Visualize
visualize_graph(workflow)
# Opens browser with interactive graph visualization
```

**Features:**
- Interactive workflow visualization
- Node-by-node state inspection
- Edge routing visualization
- Execution replay

**When to use:**
- Understanding workflow structure
- Debugging routing issues
- Visualizing state flow
- Demonstrating architecture

---

### **3. Comprehensive Logging**

**Setup:**
```python
import logging

# In each module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# In workflow_v6.py (main entry point)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/v6_debug.log'),
        logging.StreamHandler()  # Also print to console
    ]
)
```

**Usage:**
```python
# In agents/codesmith_agent_v6.py
logger.debug(f"Codesmith received state: {state}")
logger.info(f"Generating file: {file_path}")
logger.warning(f"Tree-Sitter validation failed: {error}")
logger.error(f"File write failed: {e}")
```

**Log Levels:**
- `DEBUG`: Detailed information (state, variables)
- `INFO`: General information (agent started, file created)
- `WARNING`: Something unexpected but handled
- `ERROR`: Actual errors that need attention

**Log Analysis:**
```bash
# View logs in real-time
tail -f logs/v6_debug.log

# Search for errors
grep "ERROR" logs/v6_debug.log

# Search for specific agent
grep "codesmith" logs/v6_debug.log

# View last 100 lines
tail -100 logs/v6_debug.log
```

---

### **4. State Inspection (AsyncSqliteSaver)**

**View Checkpoints:**
```python
import aiosqlite
import json

async def inspect_checkpoint(workspace_path: str, thread_id: str):
    db_path = f"{workspace_path}/.ki_autoagent_ws/cache/workflow_checkpoints_v6.db"

    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute(
            "SELECT checkpoint, metadata FROM checkpoints WHERE thread_id = ? ORDER BY checkpoint_id DESC LIMIT 1",
            (thread_id,)
        )
        row = await cursor.fetchone()
        if row:
            checkpoint_data, metadata = row
            print(json.dumps(json.loads(checkpoint_data), indent=2))
```

**When to use:**
- Workflow crashed, need to see last state
- Debugging state persistence issues
- Inspecting what was saved

---

### **5. Memory Inspection (FAISS + SQLite)**

**View Memory Contents:**
```python
import sqlite3

def inspect_memory(workspace_path: str):
    db_path = f"{workspace_path}/.ki_autoagent_ws/memory/metadata.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "SELECT content, metadata, timestamp FROM memory_items ORDER BY timestamp DESC LIMIT 10"
    )
    for content, metadata, timestamp in cursor.fetchall():
        print(f"[{timestamp}] {metadata}")
        print(f"  Content: {content[:100]}...")
        print()
```

**When to use:**
- Agent not finding context in Memory
- Debugging inter-agent communication
- Verifying Memory stores/searches

---

### **6. Native Test Client (WebSocket)**

**File:** `backend/tests/native/native_test_client.py`

**Usage:**
```python
import asyncio
import websockets
import json

async def test_workflow():
    uri = "ws://localhost:8001/ws/chat"

    async with websockets.connect(uri) as websocket:
        # 1. Initialize
        await websocket.send(json.dumps({
            "type": "init",
            "workspace_path": "/Users/.../test-workspace"
        }))
        response = await websocket.recv()
        print(f"Init: {response}")

        # 2. Send task
        await websocket.send(json.dumps({
            "type": "chat",
            "message": "Create a calculator app"
        }))

        # 3. Receive responses
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Response: {data['type']} - {data.get('content', '')[:100]}")

            if data["type"] == "complete":
                break

asyncio.run(test_workflow())
```

**When to use:**
- Testing actual workflow execution
- Debugging WebSocket communication
- Simulating user interactions
- End-to-end testing

---

## 🔍 Common Debugging Scenarios

### **Scenario 1: Workflow Not Starting**

**Symptoms:**
- WebSocket connects but no response
- Workflow hangs at first agent

**Debug Steps:**
1. Check logs: `tail -f logs/v6_debug.log`
2. Verify AsyncSqliteSaver connection:
   ```python
   logger.debug(f"Checkpointer connected: {checkpointer is not None}")
   ```
3. Check workflow compilation:
   ```python
   logger.debug(f"Workflow compiled: {workflow is not None}")
   ```
4. Add breakpoint in supervisor_node:
   ```python
   def supervisor_node(state):
       import pdb; pdb.set_trace()
       logger.debug(f"Supervisor received state: {state}")
   ```

---

### **Scenario 2: Agent Not Finding Memory Context**

**Symptoms:**
- Agent says "no context found"
- Agent doesn't use previous agent's results

**Debug Steps:**
1. Inspect Memory database:
   ```python
   inspect_memory(workspace_path)
   ```
2. Check if previous agent stored to Memory:
   ```python
   # In previous agent
   logger.debug(f"Storing to Memory: {content[:100]}")
   await memory.store(content, metadata)
   logger.debug("Memory store complete")
   ```
3. Check search query:
   ```python
   # In current agent
   logger.debug(f"Searching Memory: query={query}, filters={filters}")
   results = await memory.search(query, filters)
   logger.debug(f"Memory results: {len(results)} items")
   ```

---

### **Scenario 3: Asimov Permission Denied**

**Symptoms:**
- Agent action blocked
- "Permission denied" error

**Debug Steps:**
1. Check Asimov logs:
   ```bash
   grep "Asimov" logs/v6_debug.log
   ```
2. Verify permission:
   ```python
   # In agent
   logger.debug(f"Checking permission: agent={agent_name}, action={action}, context={context}")
   allowed = asimov.validate(agent_name, action, context)
   logger.debug(f"Permission result: {allowed}")
   ```
3. Check workspace boundary:
   ```python
   logger.debug(f"File path: {file_path}")
   logger.debug(f"Workspace: {workspace_path}")
   logger.debug(f"Is within workspace: {file_path.startswith(workspace_path)}")
   ```

---

### **Scenario 4: Tree-Sitter Parse Error**

**Symptoms:**
- "Syntax error in generated code"
- Tree-Sitter validation fails

**Debug Steps:**
1. Print code before parsing:
   ```python
   logger.debug(f"Code to parse:\n{code}")
   result = tree_sitter.parse(code, language)
   logger.debug(f"Parse result: {result}")
   ```
2. Check language detection:
   ```python
   logger.debug(f"Detected language: {language}")
   ```
3. Validate code manually:
   ```python
   # Save to temp file and run language parser
   with open("/tmp/test_code.py", "w") as f:
       f.write(code)
   # python3 -m py_compile /tmp/test_code.py
   ```

---

### **Scenario 5: ReviewFix Loop Not Terminating**

**Symptoms:**
- Loop runs 3 times but doesn't stop
- Quality score not improving

**Debug Steps:**
1. Check quality scores:
   ```python
   logger.debug(f"Iteration {iteration}, Quality: {quality_score}, Threshold: 0.75")
   ```
2. Check loop condition:
   ```python
   def should_continue_fixing(state):
       decision = "continue" if state["quality_score"] < 0.75 and state["iteration"] < 3 else "end"
       logger.debug(f"Loop decision: {decision} (score={state['quality_score']}, iter={state['iteration']})")
       return decision
   ```
3. Inspect review feedback:
   ```python
   logger.debug(f"Review feedback: {state['review_feedback']}")
   ```

---

## 📊 Performance Debugging

### **Slow Workflow Execution**

**Measure Checkpointing Overhead:**
```python
import time

# In workflow
start = time.time()
await checkpointer.aput(config, checkpoint)
end = time.time()
logger.debug(f"Checkpoint save took: {end - start:.2f}s")
```

**Measure Memory Search:**
```python
start = time.time()
results = await memory.search(query, filters)
end = time.time()
logger.debug(f"Memory search took: {end - start:.2f}s ({len(results)} results)")
```

**Measure Agent Execution:**
```python
# In supervisor
start = time.time()
result = await research_subgraph.ainvoke(state)
end = time.time()
logger.debug(f"Research agent took: {end - start:.2f}s")
```

---

## 🧪 Testing with Debugging

### **Unit Tests with pdb**

```python
import pytest

def test_memory_store():
    import pdb; pdb.set_trace()  # Breakpoint in test

    memory = MemorySystem("/tmp/test-workspace")
    await memory.store("test content", {"agent": "test"})

    results = await memory.search("test content")
    assert len(results) == 1
```

### **Native Tests with Verbose Logging**

```python
# native_test_client.py
logging.basicConfig(level=logging.DEBUG)

async def test_with_debugging():
    logger.debug("Starting native test...")

    async with websockets.connect(uri) as ws:
        logger.debug("WebSocket connected")

        await ws.send(json.dumps(init_message))
        logger.debug(f"Sent: {init_message}")

        response = await ws.recv()
        logger.debug(f"Received: {response}")
```

---

## 🎓 Best Practices

1. **Add logging BEFORE implementing**
   - Log entry points: "Agent X started with state: ..."
   - Log exit points: "Agent X completed with result: ..."
   - Log decisions: "Chose path A because ..."

2. **Use descriptive log messages**
   - ❌ Bad: `logger.debug(f"Result: {result}")`
   - ✅ Good: `logger.debug(f"Codesmith generated 3 files, validated with Tree-Sitter: {result}")`

3. **Log state at critical points**
   - Before agent invocation
   - After agent completion
   - Before Memory store/search
   - Before Asimov validation

4. **Use pdb strategically**
   - Don't leave breakpoints in committed code
   - Use conditional breakpoints for complex issues:
     ```python
     if state.get("error"):
         import pdb; pdb.set_trace()
     ```

5. **Native test for every phase**
   - Write native test BEFORE implementing agent
   - Run native test AFTER implementation
   - Use native test for debugging

6. **Visualize with LangGraph Studio**
   - Visualize BEFORE implementing complex workflows
   - Use to explain architecture to others
   - Use to debug routing issues

---

## 📝 Debugging Checklist

**Before starting implementation:**
- [ ] Logging configured (DEBUG level)
- [ ] Log file created (`logs/v6_debug.log`)
- [ ] LangGraph Studio installed
- [ ] Native test client ready
- [ ] pdb basics understood

**During implementation:**
- [ ] Log entry/exit points for all agents
- [ ] Log all Memory operations
- [ ] Log all Asimov validations
- [ ] Log all state transitions

**When stuck:**
- [ ] Check logs for errors
- [ ] Inspect last checkpoint
- [ ] Inspect Memory contents
- [ ] Add breakpoint at problem area
- [ ] Run native test in isolation
- [ ] Visualize workflow with LangGraph Studio

**After fixing:**
- [ ] Remove temporary pdb breakpoints
- [ ] Keep useful logs
- [ ] Document issue in V6_0_KNOWN_ISSUES.md
- [ ] Add test to prevent regression

---

## 🔗 References

- [Python pdb docs](https://docs.python.org/3/library/pdb.html)
- [LangGraph Studio](https://langchain-ai.github.io/langgraph/studio/)
- [Python logging docs](https://docs.python.org/3/library/logging.html)
