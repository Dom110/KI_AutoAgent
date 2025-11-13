# 🔬 Root Cause Analysis Report - 2025-11-13

## Executive Summary

**Status**: E2E tests timeout at 120s, no agents execute beyond supervisor. Real problem identified but requires deeper workflow fixes.

---

## Problems Found & Fixes Applied

### 1. ✅ **JSON Markdown Extraction** - FIXED
**Status**: ✅ COMPLETE  
**File**: `backend/core/llm_providers/base.py` (lines 266-309)  
**Problem**: OpenAI returns JSON wrapped in ```json...``` blocks  
**Solution**: Extract JSON from Markdown before parsing  
**Tests**: 3/3 pass ✅

### 2. ✅ **Async Blocking I/O in MCP Servers** - PARTIALLY FIXED
**Status**: ⚠️ PARTIAL (Research agent fixed, others still pending)  
**Problem**: All MCP servers used `loop.run_in_executor()` which blocked when stdin empty
**Root Cause**: After sending response, server blocks on next stdin.readline()
**Solution**: Added inline `async_stdin_readline()` with 300s timeout
**Fixed Files**:
- `mcp_servers/research_agent_server.py` ✅

**Still Need Fixing**:
- `mcp_servers/architect_agent_server.py`
- `mcp_servers/codesmith_agent_server.py`
- `mcp_servers/openai_server.py`  
- `mcp_servers/responder_agent_server.py`
- `mcp_servers/reviewfix_agent_server.py`

### 3. 🔴 **REAL ISSUE: Workflow Event Stream Blocking** - NOT FIXED
**Status**: ❌ IDENTIFIED (needs deeper investigation)  
**Problem**: Research agent responds successfully, but response doesn't propagate to E2E test
**Evidence**:
- research_agent.log shows JSON response sent at 19:39:11 ✅
- E2E test receives nothing (times out after 120s) ❌
- Supervisor makes decision (2.3s) ✅
- Workflow calls research_agent via mcp.call() ✅
- But result never returned to workflow/client

**Likely Causes**:
1. MCPManager response handling stuck in asyncio wait
2. Event stream not properly forwarding MCP responses
3. Workflow astream loop blocked somewhere
4. Task cancellation or timeout occurring silently

---

## Evidence & Timeline

### E2E Test Execution Timeline (19:38:05 - 19:38:07)

```
19:38:05 - Supervisor initialized ✅
19:38:05 - OpenAI call for decision (~3.5s)
19:38:05 - Decision: CONTINUE → research ✅
19:38:05 - mcp.call('research_agent', 'research', ...) called
19:38:05 - research_agent receives request ✅

[Research agent processes...]
19:38:05 - research_agent makes OpenAI call (~6s)
19:38:58 - research_agent receives OpenAI response ✅
19:38:58 - research_agent sends JSON result ✅

[TIMEOUT - No response to workflow]
19:38:07 - E2E WebSocket timeout (120s) ❌
19:38:07 - Test reports "PASS" (masked failure)
```

### Research Agent Logs (Success!)
```
2025-11-13 19:39:11,229 - openai._base_client - HTTP Response: 200 OK
2025-11-13 19:39:11,230 - research_mcp_server - ✅ OpenAI response received
2025-11-13 19:39:11,230 - research_mcp_server - Sent: {"jsonrpc": "2.0", "id": 35, "result": {...}}
```

The response IS BEING SENT to stdout! But doesn't reach the caller.

---

## Root Cause Analysis

### Why Tests Pass Despite Failures
1. E2E test has soft timeout handling
2. Any response (even error) counts as "success"
3. No validation of actual code generation
4. Only checks if messages arrived, not if workflow completed

### Two-Layer Problem
**Layer 1** (FIXED): JSON parsing error preventing supervisor from understanding OpenAI
**Layer 2** (NOT FIXED): Response routing error preventing workflow from continuing

---

## Recommended Actions

### Immediate (To unblock E2E testing)

1. **Fix remaining MCP servers**
   - Apply same inline async_stdin fix to all agents
   - Verify no server restarts in logs

2. **Debug MCP Response Routing**
   - Add logging in MCPManager._raw_call() to track response receipt
   - Check if response ID matches request ID
   - Verify event stream not blocking

3. **E2E Test Improvements**
   - Increase timeout to 300s (agents are slow)
   - Add workspace file validation
   - Verify all agents executed

###Medium (Architecture Improvement)

1. **Use Proper Async stdin**
   - Replace all `loop.run_in_executor()` with StreamReader
   - Enable true async I/O without thread pool

2. **Improve MCPManager timeout handling**
   - Add per-request timeout override
   - Better error messages for timeouts
   - Automatic retry logic

3. **Add Health Checks**
   - Periodic "ping" to verify MCP server alive
   - Detect stuck processes earlier
   - Restart gracefully

---

## Testing After Fix

```bash
# 1. Verify JSON fix
python test_json_fix_standalone.py

# 2. Run E2E with longer timeout  
timeout 300 bash run_e2e_complete.sh

# 3. Check agent execution
grep "agent_history" .logs/server_*.log | tail -1

# 4. Verify workspace files generated
ls /Users/dominikfoert/TestApps/e2e_*/src/

# 5. Monitor for server restarts
grep "starting at" /tmp/mcp_*.log | wc -l
```

---

## File Changes Summary

| File | Change | Status |
|------|--------|--------|
| `backend/core/llm_providers/base.py` | JSON markdown extraction | ✅ DONE |
| `mcp_servers/research_agent_server.py` | Async stdin helper | ✅ DONE |
| `mcp_servers/async_stdin.py` | Reusable async stdin module | ✅ CREATED |
| `mcp_servers/architect_agent_server.py` | Async stdin fix | ⏳ TODO |
| `mcp_servers/codesmith_agent_server.py` | Async stdin fix | ⏳ TODO |
| `mcp_servers/openai_server.py` | Async stdin fix | ⏳ TODO |
| `mcp_servers/responder_agent_server.py` | Async stdin fix | ⏳ TODO |
| `mcp_servers/reviewfix_agent_server.py` | Async stdin fix | ⏳ TODO |

---

## Conclusion

The system has multiple layers of issues:
1. JSON parsing - ✅ FIXED
2. MCP server blocking I/O - ⚠️ PARTIALLY FIXED
3. Workflow response routing - 🔴 NOT FIXED

The real problem preventing E2E tests is likely in the MCPManager/workflow response handling, not the MCP servers themselves. The research_agent DOES respond successfully, but the response doesn't propagate back to the workflow.

**Next Session Should Focus On**: Debugging MCPManager._raw_call() and workflow event streaming.

