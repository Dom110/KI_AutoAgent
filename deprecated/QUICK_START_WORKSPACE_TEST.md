# 🚀 Quick Start: Workspace Isolation Test

## 3-Step Test Execution

### Step 1: Start the Server
```bash
cd /Users/dominikfoert/git/KI_AutoAgent
python start_server.py
```

**Expected Output:**
```
✅ ALL CHECKS PASSED - READY TO START SERVER
🚀 STARTING SERVER...
    WebSocket: ws://localhost:8002/ws/chat
    Health Check: http://localhost:8002/health
    Diagnostics: http://localhost:8002/diagnostics

INFO:     Started server process [PID]
INFO:     Application startup complete.
...
🔒 Workspace Isolation Enabled - Server Root: /Users/dominikfoert/git/KI_AutoAgent
```

**Status:** ✅ Server is ready (keep this terminal running)

---

### Step 2: Run the Workspace Isolation Test
Open another terminal and run:

```bash
cd /Users/dominikfoert/git/KI_AutoAgent
python test_workspace_isolation.py
```

**First Prompt:**
```
⚠️  This test requires:
  1. Server running: python start_server.py
  2. No active clients connected

Press ENTER to start tests, or Ctrl+C to cancel...
```

Press **ENTER** to continue.

---

### Step 3: Review Results

The test will run 7 scenarios. Expected output:

```
================================================================================
🔒 WORKSPACE ISOLATION TEST
================================================================================

Server Root: /Users/dominikfoert/git/KI_AutoAgent
Test Start: 2025-11-03T14:00:00.000000

Test 1: Outside server - /tmp location
  Server Root: /Users/dominikfoert/git/KI_AutoAgent
  Client Workspace: /tmp/e2e_test_workspace
  Expected: ✅ ALLOWED
  Status: ✅ PASS

Test 2: Outside server - home directory
  Server Root: /Users/dominikfoert/git/KI_AutoAgent
  Client Workspace: /Users/dominikfoert/TestApps/test_workspace
  Expected: ✅ ALLOWED
  Status: ✅ PASS

Test 3: INSIDE server - direct subdirectory
  Server Root: /Users/dominikfoert/git/KI_AutoAgent
  Client Workspace: /Users/dominikfoert/git/KI_AutoAgent/test_workspace
  Expected: ❌ BLOCKED
  Status: ✅ PASS
     Error: ❌ Workspace Isolation Violation: Client workspace cannot be inside server workspace...

Test 4: INSIDE server - nested subdirectory
  Expected: ❌ BLOCKED
  Status: ✅ PASS
     Error: ❌ Workspace Isolation Violation...

Test 5: INSIDE server - TestApps subdirectory
  Expected: ❌ BLOCKED
  Status: ✅ PASS
     Error: ❌ Workspace Isolation Violation...

Test 6: IDENTICAL to server root
  Expected: ❌ BLOCKED
  Status: ✅ PASS
     Error: ❌ Workspace Isolation Violation...

Test 7: INSIDE server - parent path traversal
  Expected: ❌ BLOCKED
  Status: ✅ PASS
     Error: ❌ Workspace Isolation Violation...

================================================================================
📊 TEST SUMMARY
================================================================================

  ✅ PASS  Test 1: Outside server - /tmp location
  ✅ PASS  Test 2: Outside server - home directory
  ✅ PASS  Test 3: INSIDE server - direct subdirectory
  ✅ PASS  Test 4: INSIDE server - nested subdirectory
  ✅ PASS  Test 5: INSIDE server - TestApps subdirectory
  ✅ PASS  Test 6: IDENTICAL to server root
  ✅ PASS  Test 7: INSIDE server - parent path traversal

Results: 7/7 tests passed

✅ ALL TESTS PASSED - WORKSPACE ISOLATION WORKING!
```

---

## What the Test Proves

✅ **Allowed Scenarios** (2 tests)
- Workspaces in `/tmp` → ✅ Initialize normally
- Workspaces in user home dirs → ✅ Initialize normally
- **Result:** Legitimate external workspaces work fine

❌ **Blocked Scenarios** (5 tests)
- Workspaces inside server root → ❌ Blocked with clear error
- Workspaces matching server root → ❌ Blocked with clear error
- Path traversal attempts → ❌ Blocked with clear error
- **Result:** ALL attempts to use server-internal paths are rejected

---

## Understanding the Output

### For ✅ PASS on Allowed Tests:
```
Status: ✅ PASS
Response: ⚠️ MCP BLEIBT: v7.0 Pure MCP workflow ready!
```
= Client can initialize successfully in external workspace

### For ✅ PASS on Blocked Tests:
```
Status: ✅ PASS
Error: ❌ Workspace Isolation Violation: Client workspace cannot be inside server workspace...
```
= Server correctly rejected the malicious/accidental request

---

## Troubleshooting

### "CONNECTION FAILED"
**Problem:** Test can't reach server
```
❌ CONNECTION FAILED
   Cannot connect to ws://localhost:8002/ws/chat
```

**Solution:**
1. Ensure server is running: `python start_server.py` in another terminal
2. Check if port 8002 is available: `lsof -i :8002`
3. If blocked, kill it: `kill -9 $(lsof -t -i :8002)`

### "TIMEOUT"
**Problem:** Server not responding

**Solution:**
1. Check server terminal for errors
2. Restart server: `Ctrl+C` then `python start_server.py`
3. Wait 2-3 seconds before running test again

### "FAIL - Expected error but got initialization"
**Problem:** Test 3-7 should block but didn't

**This means workspace isolation is NOT working!**

**Debug:**
1. Check server logs for workspace validation messages
2. Verify server root is set: Look for `🔒 Workspace Isolation Enabled`
3. Restart server: The environment variable might not be set
4. Check start_server.py has the fix (line 197)
5. Check server_v7_mcp.py has the validation function (line 228+)

---

## Integration with E2E Tests

After confirming workspace isolation works, update your E2E tests:

### ✅ DO THIS:
```python
# Use workspace OUTSIDE server
workspace_path = "/Users/dominikfoert/TestApps/e2e_test_workspace"

# or for temporary tests:
workspace_path = "/tmp/e2e_test_workspace"
```

### ❌ DON'T DO THIS:
```python
# Never use paths inside server
workspace_path = "/Users/dominikfoert/git/KI_AutoAgent/TestApps/..."  # BLOCKED!
workspace_path = "/Users/dominikfoert/git/KI_AutoAgent/test"  # BLOCKED!
```

---

## What Changed in Your System

### Files Modified:
1. **`start_server.py`** (line 197)
   - Added: `os.environ['KI_AUTOAGENT_SERVER_ROOT'] = str(project_root.resolve())`
   - Effect: Server now knows its own root directory

2. **`backend/api/server_v7_mcp.py`** (line 228-272)
   - Added: `validate_workspace_isolation()` function
   - Effect: Validates workspace before initialization

3. **`backend/api/server_v7_mcp.py`** (line 687-696)
   - Added: Validation in WebSocket init handler
   - Effect: Blocks invalid workspace paths with error

### Files Created:
1. **`test_workspace_isolation.py`** - The test suite
2. **`WORKSPACE_ISOLATION_TEST.md`** - Full documentation
3. **`QUICK_START_WORKSPACE_TEST.md`** - This quick start guide

---

## Security Impact

### Before This Change
❌ Server could be accidentally modified by E2E tests  
❌ Test workspace could conflict with server code  
❌ Recursive issues possible  

### After This Change
✅ Server is isolated from client workspaces  
✅ Path traversal attacks blocked  
✅ Clear error messages for violations  
✅ Automatic validation on all init attempts  

---

## Next Steps

1. ✅ **Run the test** (this quick start)
2. ✅ **Confirm isolation works** (all 7 tests pass)
3. ✅ **Update E2E tests** to use external workspace paths
4. ✅ **Review logs** in WORKSPACE_ISOLATION_TEST.md for detailed info

---

## Server Logs to Watch

When the test runs, your server terminal should show:

```
# Initial startup:
2025-11-03 14:00:00 - server_v7_mcp - INFO - 🔒 Workspace Isolation Enabled - Server Root: /Users/dominikfoert/git/KI_AutoAgent

# During test (allowed case):
2025-11-03 14:00:01 - server_v7_mcp - INFO - ✅ Client client_xxx initialized with workspace: /tmp/e2e_test_workspace

# During test (blocked case):
2025-11-03 14:00:02 - server_v7_mcp - WARNING - 🔒 Workspace isolation violation from client_yyy: ❌ Workspace Isolation Violation...
```

---

## Success Criteria

You've successfully implemented workspace isolation when:

| Criteria | Status |
|----------|--------|
| Server starts and shows isolation enabled | ✅ |
| Test 1-2 (external workspaces) pass | ✅ |
| Test 3-7 (internal workspaces) are blocked | ✅ |
| All 7/7 tests pass | ✅ |
| No errors in server logs | ✅ |
| E2E tests use external workspace paths | ✅ |

---

**Time to Run Test:** ~15 seconds  
**Success Rate:** Should be 100% (7/7 tests pass)  
**Next Run:** Can be repeated anytime to verify system health

Good luck! 🚀

---

Questions? See `WORKSPACE_ISOLATION_TEST.md` for detailed information.