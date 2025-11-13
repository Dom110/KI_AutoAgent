# FIX #3: Response Routing Debug Strategy

**Status**: 🔴 KRITISCH - Workflow responses werden nicht propagiert

## Problem Summary

```
E2E Test Timeline:
19:24:04.827* - research_agent sends mcp_progress ✅ (in logs)
19:24:06.830 - TIMEOUT - No response ❌ (E2E waits)

Root Issue:
research_agent.send() → MCP server → stdout ✅
                       MCPManager._raw_call() → ? ❌
                       Workflow event stream → ? ❌
                       WebSocket client → ? ❌
```

## Architecture to Debug

```
1️⃣ MCP Server (research_agent_server.py)
   └─ Sends JSON response to stdout
   └─ Location: /tmp/mcp_research_agent.log

2️⃣ MCPManager (backend/utils/mcp_manager.py)
   └─ async def _raw_call()
   └─ Reads from server.process.stdout
   └─ Must handle response

3️⃣ Workflow (backend/api/workflow_v7_mcp.py)
   └─ Awaits mcp.call() result
   └─ Gets response or timeout

4️⃣ WebSocket Event Stream
   └─ Sends progress to client
   └─ Location: backend/api/server_v7_mcp.py
```

## Debug Plan

### Phase 1: Trace Response Path
1. Add logging in `MCPManager._raw_call()` at:
   - Entry point (before calling)
   - When sending request
   - When reading response
   - When returning result

2. Add logging in MCP server stdout reading

3. Track exact timestamps

### Phase 2: Test Response Routing
Create minimal test:
```python
async def test_response_routing():
    mcp = get_mcp_manager(workspace_path=test_workspace)
    await mcp.initialize()
    
    # Send request
    result = await mcp.call(
        server="research_agent",
        tool="research",
        arguments={"instructions": "test"}
    )
    
    # Log result timing
    assert result is not None
    assert "output" in result
```

### Phase 3: Async Context Issues
Possible blocking points:
- `asyncio.wait_for()` in MCPManager
- Event loop not processing other tasks
- Task cancellation not handled
- Response buffering

## Files to Modify

### Must Check:
- `backend/utils/mcp_manager.py` - Line 337 (_raw_call)
- `mcp_servers/research_agent_server.py` - Response sending
- `backend/api/workflow_v7_mcp.py` - Workflow event streaming
- `backend/api/server_v7_mcp.py` - WebSocket handling

### Logging Strategy:
```python
# Add these markers in logs:
logger.debug(f"📤 [mcp_call] Sending: {method}")
logger.debug(f"⏳ [mcp_call] Waiting for response...")
logger.debug(f"📥 [mcp_response] Received: {len(response)} bytes")
logger.debug(f"✅ [mcp_call] Complete in {elapsed}s")
```

## Success Criteria

✅ FIX #3 is complete when:
1. E2E test receives workflow result within 60s
2. No timeouts (change from 120s to actual response time)
3. Agents invoked list is not empty
4. Code is generated in workspace
5. Logs show continuous response flow
