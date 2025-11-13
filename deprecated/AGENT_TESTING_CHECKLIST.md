# ✅ KI Agent Testing - Complete Checklist & Debugging Guide

---

## 📋 PRE-TEST CHECKLIST

### Environment Setup
- [ ] Project is cloned: `/Users/dominikfoert/git/KI_AutoAgent`
- [ ] Python 3.10+ installed: `python --version`
- [ ] Virtual environment active: `source venv/bin/activate`
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] `.env` configured with API keys (Claude API)
- [ ] Port 8002 is available: `lsof -i :8002` (should be empty)

### Workspace Setup
- [ ] `~/TestApps/` directory exists: `mkdir -p ~/TestApps`
- [ ] `~/TestApps/` is writable: `touch ~/TestApps/test.txt`
- [ ] Old test artifacts cleaned: `rm -rf ~/TestApps/*`
- [ ] No conflicts with development repo

### Backend Verification
- [ ] `start_server.py` exists: `ls -la start_server.py`
- [ ] Server config is correct: Check `backend/config.yaml`
- [ ] Backend can import agents: `python -c "from backend.agents import *"`
- [ ] WebSocket endpoint configured: Port 8002

### Test Scripts
- [ ] `test_agent_websocket_real_e2e.py` exists ✅
- [ ] `test_agent_manual_interactive.py` exists ✅
- [ ] Both scripts are executable: `chmod +x test_agent_*.py`
- [ ] Python path is correct in shebang

---

## 🚀 EXECUTION CHECKLIST

### Start Backend (Terminal 1)

```bash
cd /Users/dominikfoert/git/KI_AutoAgent
source venv/bin/activate  # if using venv
python start_server.py --port=8002
```

- [ ] Command executed without errors
- [ ] Server binding to port 8002
- [ ] Output shows: `✓ Server started` or similar
- [ ] WebSocket endpoint ready: `ws://localhost:8002/ws/chat`
- [ ] No connection errors in output
- [ ] No memory leaks (check RAM usage)

**Expected Output:**
```
✓ Backend server starting...
✓ WebSocket server running on ws://localhost:8002/ws/chat
✓ Ready for connections
```

### Run Interactive Test (Terminal 2)

```bash
cd /Users/dominikfoert/git/KI_AutoAgent
python test_agent_manual_interactive.py
```

- [ ] Script started without import errors
- [ ] Shows: "🔗 Connecting to agent..."
- [ ] Successfully connects: "✅ Connected and initialized!"
- [ ] Shows test scenario menu
- [ ] User can select scenario (1-4)
- [ ] Can type custom request

### Test Execution Flow

Once connected and scenario selected:

- [ ] Request sent: "📤 Sending request #1..."
- [ ] Monitoring started: "📨 Monitoring agent responses..."
- [ ] First status received within 5 seconds
- [ ] Multiple messages received from agent
- [ ] Message types vary: status, progress, output, complete
- [ ] No ERROR messages (unless intentional)
- [ ] Workflow completes: "✅ Agent work completed!"
- [ ] File count shown: "📁 Generated Files: Total: X files"

### Automated E2E Test (Terminal 2 - Alternative)

```bash
python test_agent_websocket_real_e2e.py
```

- [ ] Script starts without errors
- [ ] Shows: "🤖 STARTING KI AGENT E2E WEBSOCKET TEST"
- [ ] Workspace created: "✅ Workspace ready"
- [ ] Backend connection successful
- [ ] Test workspace initialized
- [ ] Request sent to agent
- [ ] Messages received and processed
- [ ] Validation passes for all phases
- [ ] Shows: "✅ E2E TEST PASSED!" at end
- [ ] Exit code is 0: `echo $?` → `0`

---

## 🔍 VALIDATION CHECKLIST

### Backend Response Validation
- [ ] Received at least 5 messages
- [ ] Message format is valid JSON
- [ ] All messages have required fields: `type`, `content`
- [ ] Message sequence makes sense:
  - status → progress → progress → ... → output → complete

### Agent Workflow Validation
- [ ] Supervisor processes request
- [ ] Codesmith creates structure (logs "package.json" or similar)
- [ ] ComponentWriter generates code (logs ".jsx" files)
- [ ] E2E Generator creates tests (logs ".test.js" files)
- [ ] ReviewFix validates (logs "validation" or "review")

### Generated Artifacts Validation
- [ ] Workspace has files: `ls -la ~/TestApps/...`
- [ ] Files have correct extensions:
  - React: `.jsx`, `.js`, `.json`, `.css`
  - Vue: `.vue`, `.js`, `.json`
  - FastAPI: `.py`, `.json`
- [ ] package.json exists (for frontend apps)
- [ ] src/ directory exists
- [ ] README.md exists
- [ ] No empty files (size > 0)

### File Content Validation (Spot Check)

```bash
# Check React component
cat ~/TestApps/.../src/App.jsx | head -20

# Should contain: import React, function/component, JSX
# Should NOT contain: [object Object], undefined, null

# Check package.json
cat ~/TestApps/.../package.json | python -m json.tool

# Should be valid JSON, should have dependencies
```

- [ ] JSON files are valid JSON: `python -m json.tool file.json`
- [ ] Code files start with shebang or imports (not garbage)
- [ ] No suspicious markers: `[object Object]`, `undefined` (in strings), etc.
- [ ] File permissions are correct: `644` for files, `755` for dirs

---

## 🐛 TROUBLESHOOTING CHECKLIST

### Issue: Connection Refused

**Symptom:**
```
❌ Connection failed: [Errno 111] Connection refused
```

**Debug Steps:**
- [ ] Backend is running: `ps aux | grep start_server`
- [ ] Port 8002 is listening: `lsof -i :8002`
- [ ] No firewall blocking: `sudo lsof -i :8002`
- [ ] Correct URL: `ws://localhost:8002/ws/chat` (not http://)
- [ ] Backend didn't crash: Check Terminal 1 for errors

**Fix:**
```bash
# Kill any existing processes on port 8002
lsof -i :8002 | awk 'NR!=1 {print $2}' | xargs kill -9

# Restart backend
python start_server.py --port=8002
```

### Issue: Init Failed

**Symptom:**
```
❌ Init failed: {'success': false}
```

**Debug Steps:**
- [ ] workspace_path is absolute: Starts with `/Users/`
- [ ] workspace_path exists: `ls -la /path/to/workspace`
- [ ] workspace_path is writable: `touch /path/to/workspace/test.txt`
- [ ] workspace_path is outside dev repo ✅
- [ ] No special characters in path

**Fix:**
```python
# Check workspace path
import os
ws = os.path.expanduser("~/TestApps/test")
os.makedirs(ws, exist_ok=True)
print(f"Workspace: {ws}")
print(f"Exists: {os.path.exists(ws)}")
print(f"Writable: {os.access(ws, os.W_OK)}")
```

### Issue: No Messages Received

**Symptom:**
```
❌ No messages received!
```

**Debug Steps:**
1. Check backend logs:
   ```bash
   tail -100 /tmp/v7_server.log
   ```

2. Check for agent errors:
   - [ ] "Claude API error" → Check API key & rate limits
   - [ ] "File not found" → Check workspace path
   - [ ] "JSON parse error" → Check message format
   - [ ] "Agent crashed" → Backend has bug

3. Verify connection:
   ```bash
   # Use wscat if installed
   pip install websocket-client
   python -c "
   import asyncio
   import websockets
   async def test():
       async with websockets.connect('ws://localhost:8002/ws/chat') as ws:
           print('Connected!')
           await ws.send('{\"type\":\"init\",\"workspace_path\":\"/tmp/test\"}')
           msg = await ws.recv()
           print('Received:', msg)
   asyncio.run(test())
   "
   ```

**Fix:**
- [ ] Backend logs show connection: `connection_received`
- [ ] Request received: `message_received`
- [ ] Agent started: `agent_started`
- [ ] If not: Restart backend with `--debug` flag

### Issue: Agent Timeout (No response for 60+ seconds)

**Symptom:**
```
⏱️  No response for 60 seconds...
```

**Debug Steps:**
1. Check backend still running:
   ```bash
   ps aux | grep start_server
   ```

2. Check CPU/Memory:
   ```bash
   top -n1 | head -20
   ```

3. Check Claude API status:
   - [ ] No rate limit errors
   - [ ] API key is valid
   - [ ] Request is reasonable size

4. Check logs for stuck process:
   ```bash
   tail -50 /tmp/v7_server.log | grep -i "timeout\|stuck\|hang"
   ```

**Fix:**
```bash
# If agent is hung:
# Terminal 1: Ctrl+C to stop backend
# Kill process if needed:
pkill -f "python start_server.py"

# Wait 5 seconds, then restart
sleep 5
python start_server.py --port=8002
```

### Issue: Generated Files in Wrong Location

**Symptom:**
```
Files generated in /Users/dominikfoert/git/KI_AutoAgent/app_name/
Instead of: ~/TestApps/app_name/
```

**Debug Steps:**
- [ ] workspace_path was sent in init message: Check logs
- [ ] workspace_path reached backend agents: Check agent logs
- [ ] Claude CLI subprocess received correct cwd

**Fix:**
```python
# In backend code, verify workspace_path is passed:
# backend/subgraphs/codesmith_subgraph.py

state.get("workspace_path")  # Should NOT be None!
```

### Issue: Old Files Being Read

**Symptom:**
```
❌ ERROR: File already exists
❌ ERROR: App already exists
```

**Debug Steps:**
- [ ] Workspace was cleaned: `ls ~/TestApps/ | wc -l` → 0
- [ ] Old workspace removed: `rm -rf ~/TestApps/*`
- [ ] Dev repo is clean: No test files in `/git/KI_AutoAgent/app*`

**Fix:**
```bash
# Clean everything
rm -rf ~/TestApps/*
rm -rf /Users/dominikfoert/git/KI_AutoAgent/task-manager-app 2>/dev/null
rm -rf /Users/dominikfoert/git/KI_AutoAgent/*_app 2>/dev/null

# Verify clean
find ~/TestApps -type f 2>/dev/null | wc -l  # Should be 0
find /Users/dominikfoert/git/KI_AutoAgent -maxdepth 1 -name "*app" 2>/dev/null  # Should be empty
```

---

## 🔧 DEBUGGING COMMANDS

### Quick Status Check

```bash
# 1. Is backend running?
ps aux | grep "start_server.py" | grep -v grep

# 2. Is port open?
lsof -i :8002

# 3. Can connect?
python -c "import socket; s=socket.socket(); s.connect(('localhost', 8002)); print('✓ Connected')"

# 4. Workspace status?
ls -la ~/TestApps/

# 5. Recent logs?
tail -20 /tmp/v7_server.log

# 6. Agent process healthy?
ps aux | grep -E "start_server|claude|python" | wc -l
```

### Detailed Debugging

```bash
# Enable debug logging
PYTHON_ASYNCIO_DEBUG=1 python start_server.py --debug

# Check specific agent
python -c "
from backend.agents.supervisor_agent import SupervisorAgent
print('✓ SupervisorAgent imports OK')
"

# Test WebSocket manually
python test_agent_manual_interactive.py 2>&1 | tee debug.log

# Parse JSON response
python -c "
import json
s = '{\"type\":\"status\",\"content\":\"test\"}'
d = json.loads(s)
print(json.dumps(d, indent=2))
"
```

### File Inspection

```bash
# List generated files
find ~/TestApps -type f -exec ls -lh {} \; | head -20

# Check for binary vs text
file ~/TestApps/*/package.json

# Validate JSON
python -m json.tool ~/TestApps/*/package.json > /dev/null && echo "✓ Valid JSON"

# Check for suspicious content
grep -r "undefined" ~/TestApps/ --include="*.js" --include="*.jsx"
grep -r "\[object Object\]" ~/TestApps/ --include="*.js"
```

---

## 📊 SUCCESS METRICS

### Pass Criteria

| Metric | Pass | Fail |
|--------|------|------|
| **Connection** | < 5s | timeout |
| **Messages** | > 10 | 0 |
| **Errors** | 0 | > 0 |
| **Files** | > 20 | 0 |
| **JSON Valid** | yes | no |
| **Structure** | Complete | Incomplete |
| **Location** | ~/TestApps | Dev Repo |
| **Duration** | < 120s | > 300s |

### Test Report

After running test, verify:

```bash
# ✓ Check exit code
echo $?  # Should be 0 for success

# ✓ Count files
find ~/TestApps -type f | wc -l  # Should be > 20

# ✓ List file types
find ~/TestApps -type f | sed 's/.*\.//' | sort | uniq -c

# ✓ Check for errors
grep -i "error" debug.log  # Should have 0 or expected errors only
```

---

## 🎯 NEXT STEPS

### If Test PASSED ✅

1. Note the workspace location: `~/TestApps/...`
2. Optionally inspect generated files
3. Run another test with different scenario
4. Move to integration testing

### If Test FAILED ❌

1. Identify which phase failed (see checklist)
2. Follow troubleshooting for that issue
3. Check debug logs and backend logs
4. Fix identified issue
5. Run test again

### For Production Deployment

1. Run automated test: `test_agent_websocket_real_e2e.py`
2. Must pass with exit code 0
3. Check performance metrics
4. Monitor logs for 24 hours
5. Deploy with confidence ✅

---

## 📚 Related Files

- **Quick Start**: `AGENT_E2E_TEST_QUICK_START.md`
- **E2E Guide**: `E2E_TESTING_GUIDE.md`
- **Testing Scripts**: 
  - `test_agent_websocket_real_e2e.py`
  - `test_agent_manual_interactive.py`
- **System Status**: `CURRENT_SYSTEM_STATUS_v7.0.md`

---

**Version**: 1.0  
**Last Updated**: 2025-02-15  
**Maintainer**: KI AutoAgent Team