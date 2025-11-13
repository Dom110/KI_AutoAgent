# 🚨 Root Cause: AsyncIO Blocking I/O in MCP Servers

## Problem Discovered

The research_agent MCP server uses **blocking I/O** in an async loop:

```python
async def run(self):
    loop = asyncio.get_event_loop()
    while True:
        line = await loop.run_in_executor(None, sys.stdin.readline)  # ⚠️ BLOCKS!
        # ...
```

This causes:
1. After sending a response, the server tries to read the next request from stdin
2. If stdin is waiting for input (parent process hasn't sent next request yet)
3. The `run_in_executor()` thread blocks
4. The asyncio event loop can't process other events
5. The MCPManager times out waiting for the server (thinks it crashed)
6. MCPManager kills the process and restarts it

Result: **Infinite restart loop (179 restarts in logs!)**

## Why This Breaks Everything

1. **E2E Test Timeline**:
   - 19:24:04: Supervisor sends first request to research_agent
   - 19:24:26-39: research_agent processes and responds ✅
   - 19:24:42-47: Server blocks on next stdin read (parent hasn't sent next request yet)
   - 19:24:47: MCPManager detects timeout and restarts server
   - 19:24:58: New server starts, processes next request
   - Repeat cycle...

2. **Why Only Research Agent Has This Issue**:
   - Other agents might have the same problem but our E2E test times out before seeing multiple cycles
   - Research agent is called first, so it hits this problem first

3. **Why Tests Report "PASS"**:
   - E2E test times out and closes WebSocket
   - Because no errors are seen (just timeouts), test reports "PASS"
   - Actual failures are masked by the timeout wrapper

## Solution: Non-Blocking stdin

Instead of `loop.run_in_executor(None, sys.stdin.readline)`, use:
1. **asyncio-based stdin reading** 
2. **Or: proper EOF/timeout handling**
3. **Or: avoid blocking at all with StreamReader**

### Option 1: Use StreamReader (BEST)

```python
async def run(self):
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader, lambda: None)
    
    transport, _ = await asyncio.get_event_loop().connect_read_pipe(
        lambda: protocol, sys.stdin
    )
    
    while True:
        try:
            line = await asyncio.wait_for(
                reader.readline(), 
                timeout=30.0  # 30s timeout per request
            )
            if not line:
                break
            # Process request
        except asyncio.TimeoutError:
            logger.warning("Request timeout (30s)")
            continue
```

### Option 2: Use Timeout on Executor (QUICK FIX)

```python
async def run(self):
    loop = asyncio.get_event_loop()
    while True:
        try:
            line = await asyncio.wait_for(
                loop.run_in_executor(None, sys.stdin.readline),
                timeout=120.0  # Match MCPManager timeout
            )
            # ...
        except asyncio.TimeoutError:
            logger.warning("stdin read timeout - waiting for next request")
            continue
```

### Option 3: Check if stdin is available (ROBUST)

```python
async def run(self):
    import select
    loop = asyncio.get_event_loop()
    
    while True:
        # Check if stdin is readable (non-blocking)
        ready = select.select([sys.stdin], [], [], 0.1)  # 100ms timeout
        if ready[0]:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            # Process
        else:
            await asyncio.sleep(0.1)  # Yield to other tasks
```

## Impact on Current System

This bug affects **ALL MCP servers**:
- research_agent_server.py (currently hitting this)
- architect_agent_server.py (same pattern)
- codesmith_agent_server.py (same pattern)
- reviewfix_agent_server.py (same pattern)
- responder_agent_server.py (same pattern)
- other MCP servers...

All use the same blocking `run_in_executor()` pattern!

## Why This Wasn't Caught Before

1. Development likely tested with direct agent instantiation
2. Pure MCP architecture is NEW (v7.0)
3. This bug only appears under load or with specific timing
4. E2E tests are relatively slow, so requests arrive close together
5. This creates the perfect storm for the blocking I/O issue

## Fix Priority

**CRITICAL** - This is blocking the entire E2E test suite

Should fix in this order:
1. research_agent_server.py (affects E2E test)
2. All other MCP servers
3. Verify with E2E tests

## Testing the Fix

After fix, E2E test should:
1. ✅ Not timeout
2. ✅ See all agents execute (research → architect → codesmith → etc)
3. ✅ Generate actual code in workspace
4. ✅ Not see server restarts in logs

