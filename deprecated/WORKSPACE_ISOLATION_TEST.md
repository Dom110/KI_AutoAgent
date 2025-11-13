# 🔒 Workspace Isolation Test

## Overview

This test verifies a **critical security feature**: The KI AutoAgent server **BLOCKS** any client attempt to initialize a workspace that lies within the server's own workspace directory.

This prevents:
- ❌ Accidental test execution within server code
- ❌ Recursive/self-modification issues
- ❌ Potential security vulnerabilities
- ❌ Data corruption

## How It Works

### Implementation

**1. Server Root Registration** (`start_server.py`)
```python
# When start_server.py starts the server, it sets:
os.environ['KI_AUTOAGENT_SERVER_ROOT'] = str(project_root.resolve())
# This is: /Users/dominikfoert/git/KI_AutoAgent
```

**2. Workspace Validation** (`backend/api/server_v7_mcp.py`)
```python
def validate_workspace_isolation(workspace_path: str) -> tuple[bool, str]:
    """
    Validates that client workspace is NOT inside server workspace.
    
    Returns:
        (is_valid, error_message)
    """
    # Normalizes both paths and checks if client workspace
    # is a subdirectory of server root
    # If yes: Returns (False, error_message)
    # If no: Returns (True, "")
```

**3. Init Handler Enforcement** (WebSocket endpoint)
```python
# When client sends init message with workspace_path:
is_valid, error_msg = validate_workspace_isolation(workspace_path)
if not is_valid:
    # Send error to client
    await manager.send_json(client_id, {
        "type": "error",
        "message": error_msg,
        "error_code": "WORKSPACE_ISOLATION_VIOLATION"
    })
```

---

## Running the Test

### Prerequisites

```bash
# 1. Make sure you have the server running
cd /Users/dominikfoert/git/KI_AutoAgent
python start_server.py

# In another terminal:
# 2. Run the test
python test_workspace_isolation.py
```

### Test Scenarios

The test runs 7 scenarios:

| # | Scenario | Path | Expected | Result |
|---|----------|------|----------|--------|
| 1 | Outside server - /tmp | `/tmp/e2e_test_workspace` | ✅ ALLOWED | Should init |
| 2 | Outside server - home | `~/TestApps/test_workspace` | ✅ ALLOWED | Should init |
| 3 | INSIDE server - direct subdir | `{SERVER_ROOT}/test_workspace` | ❌ BLOCKED | Should error |
| 4 | INSIDE server - nested | `{SERVER_ROOT}/backend/test_workspace` | ❌ BLOCKED | Should error |
| 5 | INSIDE server - TestApps | `{SERVER_ROOT}/TestApps` | ❌ BLOCKED | Should error |
| 6 | IDENTICAL to server | `{SERVER_ROOT}` | ❌ BLOCKED | Should error |
| 7 | INSIDE server - path traversal | `{SERVER_ROOT}/../KI_AutoAgent/test` | ❌ BLOCKED | Should error |

### Expected Output

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
     Response: ⚠️ MCP BLEIBT: v7.0 Pure MCP workflow ready!

Test 2: Outside server - home directory
  Server Root: /Users/dominikfoert/git/KI_AutoAgent
  Client Workspace: /Users/dominikfoert/TestApps/test_workspace
  Expected: ✅ ALLOWED
  Status: ✅ PASS
     Response: ⚠️ MCP BLEIBT: v7.0 Pure MCP workflow ready!

Test 3: INSIDE server - direct subdirectory
  Server Root: /Users/dominikfoert/git/KI_AutoAgent
  Client Workspace: /Users/dominikfoert/git/KI_AutoAgent/test_workspace
  Expected: ❌ BLOCKED
  Status: ✅ PASS
     Error: ❌ Workspace Isolation Violation: Client workspace cannot be 
             inside server workspace...

... (more tests)

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

## Key Features of This Test

### 1. Path Normalization ✅
- Uses `Path.resolve()` to normalize all paths
- Handles path traversal (`../`) correctly
- Works across different path formats

### 2. Comprehensive Coverage ✅
- Tests valid external workspaces
- Tests multiple invalid internal locations
- Tests edge case: path traversal attacks
- Tests exact server root match

### 3. Clear Error Messages ✅
- Tells user exactly what went wrong
- Shows server root and client workspace
- Provides actionable feedback

### 4. Security by Default ✅
- If validation disabled, logs warning but allows (graceful degradation)
- Does not silently fail
- Provides proper error codes for programmatic handling

---

## Server Logs During Test

When running the test, look for these logs in the server output:

```
2025-11-03 14:00:00 - server_v7_mcp - INFO - 🔒 Workspace Isolation Enabled - Server Root: /Users/dominikfoert/git/KI_AutoAgent

# When test 1 runs (should pass):
2025-11-03 14:00:01 - server_v7_mcp - INFO - ✅ Client client_xyz initialized with workspace: /tmp/e2e_test_workspace

# When test 3 runs (should be blocked):
2025-11-03 14:00:02 - server_v7_mcp - WARNING - 🔒 Workspace isolation violation from client_abc: ❌ Workspace Isolation Violation: Client workspace cannot be inside server workspace...
```

---

## Architecture

### Before (Vulnerable)
```
Client Request
    ↓
Check workspace_path
    ↓
Use workspace directly (UNSAFE!)
```

### After (Secure)
```
Client Request with workspace_path
    ↓
Check 1: Is workspace_path provided?
    ↓
Check 2: Is workspace_path INSIDE server workspace?
    ├─ YES → Block with error (SECURITY)
    └─ NO → Initialize workspace (SAFE)
```

---

## Testing Edge Cases

### Edge Case 1: Relative Paths
```python
# Test sends: "./test_workspace"
# Server resolves to: "/Users/dominikfoert/git/KI_AutoAgent/test_workspace"
# Result: BLOCKED (inside server)
```

### Edge Case 2: Path Traversal
```python
# Test sends: "/Users/dominikfoert/git/KI_AutoAgent/../KI_AutoAgent/test"
# Server resolves to: "/Users/dominikfoert/git/KI_AutoAgent/test"
# Result: BLOCKED (inside server)
```

### Edge Case 3: Symlinks
```python
# If client_workspace is a symlink to server workspace:
# Path.resolve() follows symlinks
# Result: BLOCKED (correctly detected)
```

---

## Integration with E2E Tests

When running comprehensive E2E tests, use **external** workspaces:

✅ **CORRECT:**
```bash
# E2E test uses workspace outside server
/Users/dominikfoert/TestApps/e2e_test_workspace
```

❌ **WRONG:**
```bash
# E2E test uses workspace inside server (BLOCKED)
/Users/dominikfoert/git/KI_AutoAgent/TestApps/e2e_test_workspace
```

---

## Monitoring & Troubleshooting

### If tests fail:

1. **Check server started properly**
   ```bash
   curl http://localhost:8002/health
   ```

2. **Check environment variable set**
   ```bash
   # In server logs, look for:
   # "🔒 Workspace Isolation Enabled - Server Root: /Users/dominikfoert/git/KI_AutoAgent"
   ```

3. **Manual WebSocket test**
   ```python
   import websockets
   import json
   
   async def test():
       uri = "ws://localhost:8002/ws/chat"
       async with websockets.connect(uri) as ws:
           # Connect
           msg = await ws.recv()
           print(f"Server: {msg}")
           
           # Try init with blocked workspace
           await ws.send(json.dumps({
               "type": "init",
               "workspace_path": "/Users/dominikfoert/git/KI_AutoAgent/test"
           }))
           
           # Should get error
           response = await ws.recv()
           print(f"Response: {response}")
   ```

---

## Performance

- Validation is **instant** (< 1ms)
- Uses only filesystem path comparisons
- No network calls
- No database queries
- Minimal memory overhead

---

## Security Implications

### What This Protects Against

1. **Accidental Test Contamination**
   - E2E test accidentally uses server code directory
   - Risk: Test modifies server files

2. **Recursive Issues**
   - Agent creates workspace inside server
   - Risk: Infinite loops, self-modification

3. **Path Traversal Attacks**
   - Malicious client sends: `/../../../etc/passwd`
   - After normalization: `/Users/dominikfoert/git/KI_AutoAgent/etc/passwd`
   - Risk: Access files outside workspace

### What This Does NOT Protect

- OS-level permissions (use `chmod`)
- File content validation
- Malicious code in workspace
- Network attacks

---

## Future Enhancements

- [ ] Per-workspace ACL (Access Control Lists)
- [ ] Workspace quota limits
- [ ] Audit logging for isolation violations
- [ ] Rate limiting for init attempts
- [ ] Whitelist of allowed workspace roots

---

## Related Files

- `start_server.py` - Sets server root environment variable
- `backend/api/server_v7_mcp.py` - Implements validation
- `test_workspace_isolation.py` - This test suite
- `CURRENT_SYSTEM_STATUS_v7.0.md` - System overview

---

**Last Updated:** 2025-11-03  
**Test Status:** ✅ Ready to Run  
**Security Level:** 🔒 Protected