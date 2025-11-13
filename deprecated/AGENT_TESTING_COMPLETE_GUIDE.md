# 🤖 KI Agent E2E Testing - COMPLETE GUIDE

**How to Test MCP Multi KI Agents that Generate Software**

---

## 📊 OVERVIEW

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  AGENT E2E TESTING = WebSocket + Workflow Validation      │
│                                                            │
│  Different from App E2E Testing!                          │
│                                                            │
│  App E2E:    Test the app that users interact with        │
│  Agent E2E:  Test the agent that creates apps             │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 🎯 WHAT IS AGENT E2E TESTING?

### The Agent Workflow

```
User Request
    ↓
WebSocket Message
    ↓
Backend Server (port 8002)
    ↓
Supervisor Agent (parses & routes)
    ↓
Codesmith Agent (creates structure)
    ↓
ComponentWriter Agent (generates code)
    ↓
E2E Generator Agent (creates tests)
    ↓
ReviewFix Agent (validates & fixes)
    ↓
Generated App Files in Workspace
    ↓
✅ Success / ❌ Failure
```

### What We Test

| Component | Test | Validates |
|-----------|------|-----------|
| **Connection** | WebSocket establishes | Agent reachable |
| **Request** | Send message to agent | Agent receives it |
| **Processing** | Agents execute workflow | Correct routing |
| **Output** | Receive response messages | Agent responds |
| **Artifacts** | Files generated | App created |
| **Location** | Files in correct workspace | Isolation verified |
| **Content** | Generated code quality | Syntax & structure |
| **Tests** | E2E tests generated | Test coverage |

---

## 🚀 THREE WAYS TO TEST

### 1. Manual Interactive Test (Development & Debugging)

```bash
python test_agent_manual_interactive.py
```

**Use When:**
- Developing new agent features
- Debugging issues
- Understanding workflow
- Manual validation

**Features:**
- ✅ Interactive menu with scenarios
- ✅ Real-time agent response display
- ✅ File generation monitoring
- ✅ Colored, readable output
- ✅ Choose custom requests

**Workflow:**
```
1. Script starts
2. Workspace created (~TestApps/...)
3. Connect to backend
4. Show test scenarios (1, 2, 3, custom)
5. Execute selected scenario
6. Monitor responses in real-time
7. Show generated files
8. Ask for another test
```

---

### 2. Automated E2E Test (CI/CD & Validation)

```bash
python test_agent_websocket_real_e2e.py
```

**Use When:**
- Continuous Integration
- Automated validation
- Performance testing
- Regression detection

**Features:**
- ✅ Fully automated
- ✅ 7-phase validation
- ✅ Comprehensive checks
- ✅ Detailed reporting
- ✅ Exit codes (0=pass, 1=fail)

**Phases:**
```
PHASE 1: Setup
  ✓ Workspace clean
  ✓ Backend ready

PHASE 2: Connect
  ✓ WebSocket established
  ✓ Init acknowledged

PHASE 3: Request
  ✓ App request sent
  ✓ Message ID tracked

PHASE 4: Monitor
  ✓ Responses received
  ✓ Timeout handled

PHASE 5: Validate
  ✓ No errors
  ✓ Workflow complete

PHASE 6: Verify
  ✓ Files generated
  ✓ Structure valid

PHASE 7: Summary
  ✓ Metrics reported
```

---

### 3. Manual WebSocket Test (Direct Testing)

```bash
# Connect directly
wscat -c ws://localhost:8002/ws/chat

# Send init
{"type":"init","workspace_path":"/tmp/test"}

# Send request
{"type":"message","content":"Create React app"}

# Monitor responses
[receive messages...]
```

**Use When:**
- Direct protocol testing
- Low-level debugging
- Protocol validation

---

## 📋 QUICK START (5 MINUTES)

### Step 1: Backend Server

```bash
# Terminal 1
cd /Users/dominikfoert/git/KI_AutoAgent
python start_server.py --port=8002

# Wait for: ✓ Server started on port 8002
```

### Step 2: Run Test

```bash
# Terminal 2
cd /Users/dominikfoert/git/KI_AutoAgent
python test_agent_manual_interactive.py
```

### Step 3: Select & Watch

```
1. Simple React Todo App
2. React Dashboard
3. Contact Form
4. Custom Request

Select: 1

[Watch agent generate app...]

✅ Complete!
```

---

## 🔍 WHAT GETS VALIDATED

### Phase 1: Environment
```
✓ Workspace outside dev repo
✓ Workspace is clean (no old files)
✓ Backend server running
✓ Port 8002 available
✓ No stale processes
```

### Phase 2: Connection
```
✓ WebSocket connects
✓ Connection timeout < 5s
✓ Init message sent
✓ Init acknowledged with success=true
```

### Phase 3: Request
```
✓ Request formatted correctly
✓ Message ID assigned
✓ Request sent to agent
✓ Agent receives it
```

### Phase 4: Execution
```
✓ Agent responds (first msg < 5s)
✓ Multiple messages received (> 10)
✓ Message types vary: status, progress, output
✓ No critical errors
✓ Workflow progresses logically
```

### Phase 5: Results
```
✓ Workflow completes (COMPLETE message)
✓ No unhandled exceptions
✓ Response consistent
✓ Timing reasonable (< 120s)
```

### Phase 6: Artifacts
```
✓ Files generated (> 20 files)
✓ Files in correct workspace
✓ Files NOT in dev repo
✓ App structure correct:
  ✓ package.json exists
  ✓ src/ directory exists
  ✓ README.md exists
```

### Phase 7: Quality
```
✓ Generated code has valid syntax
✓ JSON files are valid
✓ No suspicious content (undefined, [object Object])
✓ No executable vulnerabilities
✓ File permissions correct
```

---

## 🎓 AGENT TESTING PATTERNS

### Pattern 1: Request → Response

```python
# What we do:
async def test():
    client = E2EWebSocketClient(ws_url, workspace)
    await client.connect()
    await client.send_request("Create React app")
    messages = await client.receive_all_messages()
    assert len(messages) > 0
    assert messages[-1]["type"] == "complete"
```

### Pattern 2: State Tracking

```python
# What we do:
state_trace = []
for msg in messages:
    state_trace.append({
        "timestamp": msg["timestamp"],
        "agent": msg.get("agent"),
        "status": msg.get("status"),
        "artifact": msg.get("artifact")
    })

# Verify state transitions are logical
```

### Pattern 3: Artifact Validation

```python
# What we do:
generated_files = list(workspace.rglob("*"))

# Validate structure
assert (workspace / "package.json").exists()
assert (workspace / "src").is_dir()
assert len(generated_files) > 20

# Validate content
for file in generated_files:
    if file.suffix in [".js", ".jsx", ".json"]:
        validate_syntax(file)
```

### Pattern 4: Error Handling

```python
# What we do:
for msg in messages:
    if msg["type"] == "error":
        logger.error(f"Agent error: {msg['content']}")
        test_failed = True

assert not test_failed, "Agent encountered errors"
```

---

## ✅ SUCCESS CRITERIA

### Test Passes If:

```
✅ Connection established
✅ At least 10 messages received
✅ No ERROR type messages
✅ Workflow completed (type="complete")
✅ 30+ files generated
✅ Files in ~/TestApps/... (not dev repo)
✅ package.json valid JSON
✅ src/ directory exists
✅ No suspicious content in generated code
✅ Total execution time < 120 seconds
```

### Test Fails If:

```
❌ Connection timeout
❌ 0 messages received
❌ ERROR message found
❌ No complete message
❌ No files generated
❌ Files in development repo
❌ Invalid JSON
❌ Missing directories
❌ Garbage in generated code
❌ Execution > 300 seconds
```

**Rule:** ANY failure = Test FAILED. No partial credit!

---

## 🐛 DEBUGGING WORKFLOW

### Issue: Connection Refused

**Root Cause:** Backend not running on port 8002

**Debug:**
```bash
# Check if running
ps aux | grep start_server

# Check port
lsof -i :8002

# Check if process crashed
tail -20 /tmp/v7_server.log
```

**Fix:**
```bash
# Kill any zombie processes
pkill -f "start_server"

# Restart
python start_server.py --port=8002
```

---

### Issue: No Messages Received

**Root Cause:** Agent not processing request

**Debug:**
```bash
# Check backend logs
tail -50 /tmp/v7_server.log | grep -i "error\|exception"

# Check WebSocket connection
python -c "
import asyncio, websockets
async def test():
    try:
        async with websockets.connect('ws://localhost:8002/ws/chat') as ws:
            await ws.send('{\"type\":\"init\",\"workspace_path\":\"/tmp/t\"}')
            print(await ws.recv())
    except Exception as e:
        print(f'Error: {e}')
asyncio.run(test())
"
```

**Fix:**
- Check API key in `.env`
- Check rate limits
- Check request format
- Restart backend

---

### Issue: Files in Dev Repo

**Root Cause:** Wrong workspace_path or subprocess cwd

**Debug:**
```bash
# Check backend code
grep -r "workspace_path" backend/agents/

# Check if cwd is set in subprocess
grep -r "cwd=" backend/adapters/

# Verify sent workspace
grep "workspace_path" /tmp/v7_server.log
```

**Fix:**
- Ensure `workspace_path` sent in init
- Ensure backend receives it
- Ensure subprocess uses `cwd=workspace_path`
- Clean both ~/TestApps/ and dev repo

---

### Issue: Agent Timeout

**Root Cause:** Agent hung or very slow

**Debug:**
```bash
# Check if process is stuck
ps aux | grep -i "python\|claude"

# Check for Claude API rate limit
grep -i "rate\|limit\|429" /tmp/v7_server.log

# Monitor system resources
top -n5 -b | head -20
```

**Fix:**
- Wait longer (agent may be slow)
- Check Claude API dashboard
- Increase timeout value
- Restart backend

---

## 📊 MONITORING DURING TEST

### Live Backend Monitoring

```bash
# Terminal 3: Watch logs
tail -f /tmp/v7_server.log
```

**Look for:**
```
✓ Connection received from client
✓ Init message received
✓ workspace_path: /Users/.../TestApps/...
✓ Supervisor processing request
✓ Codesmith creating structure
✓ ComponentWriter generating code
✓ E2E generator creating tests
✓ ReviewFix validating
✓ Workflow completed
✓ Files written to workspace
```

### Live File Monitoring

```bash
# Terminal 4: Watch file generation
watch -n 1 'find ~/TestApps -type f | wc -l'

# Or with tree
tree -L 3 ~/TestApps
```

---

## 🔄 TESTING CYCLE

### Development Loop

```
1. Make change to agent code
   └─ backend/agents/supervisor_agent.py

2. Restart backend
   └─ python start_server.py --port=8002

3. Run test
   └─ python test_agent_manual_interactive.py

4. Observe output
   └─ Check terminal output & backend logs

5. Verify results
   └─ Check generated files

6. If passed: ✅ Deploy
   If failed: ❌ Fix code, goto 1
```

---

## 📈 PERFORMANCE EXPECTATIONS

| Metric | Expected | Max |
|--------|----------|-----|
| Connection | < 1s | 5s |
| First response | < 5s | 10s |
| Full execution | 60-120s | 300s |
| Messages | 15-50 | unlimited |
| Files | 30-100 | unlimited |
| File size | 1-100 KB | unlimited |

---

## 🎯 TEST SCENARIOS

### Scenario 1: React Todo App

```
Request:
Create a React Todo Application with:
- Input to add todos
- Display list
- Mark complete
- Delete functionality
- Local storage

Expected:
- React components generated
- Todo logic implemented
- Tests created
- ~40-50 files
- ~5 minutes
```

### Scenario 2: React Dashboard

```
Request:
Create React Dashboard with:
- Grid layout
- Data cards
- Chart
- Dark mode
- Statistics

Expected:
- Dashboard components
- Chart library integration
- Theme system
- ~50-60 files
- ~6 minutes
```

### Scenario 3: FastAPI Backend

```
Request:
Create FastAPI with:
- User CRUD
- Authentication
- Rate limiting
- API docs

Expected:
- FastAPI routes
- Database models
- Auth middleware
- Tests
- ~30-40 files
- ~5 minutes
```

---

## 🚨 CRITICAL RULES

### Rule 1: Workspace Isolation
```
❌ NEVER: ~/git/KI_AutoAgent/test_output/
✅ ALWAYS: ~/TestApps/...
```

### Rule 2: Clean Before Test
```bash
# Always clean first!
rm -rf ~/TestApps/*
```

### Rule 3: No Exceptions
```
✅ Test passes: All criteria met
❌ Test fails: ANY error found
(No partial success)
```

### Rule 4: Verify Location
```bash
# After test, check:
ls -la ~/TestApps/
# Should have generated app

# Check dev repo:
find /Users/dominikfoert/git/KI_AutoAgent -name "*app" -maxdepth 1
# Should be EMPTY
```

---

## 📚 DOCUMENTATION FILES

| File | Purpose |
|------|---------|
| **test_agent_websocket_real_e2e.py** | Automated E2E test |
| **test_agent_manual_interactive.py** | Interactive test |
| **AGENT_E2E_TEST_QUICK_START.md** | Quick start guide |
| **AGENT_TESTING_CHECKLIST.md** | Complete checklist |
| **E2E_TESTING_GUIDE.md** | Best practices |
| **CRITICAL_FAILURE_INSTRUCTIONS.md** | Error handling |

---

## 🎓 EXAMPLES

### Example 1: Successful Test

```
$ python test_agent_manual_interactive.py

🔗 Connecting to agent...
✅ Connected!

═══ Test Scenarios ═══
1. Simple React Todo App
2. React Dashboard
3. Contact Form

Select: 1
📤 Sending request...

📨 Monitoring...
ℹ️  Status: Processing...
⏳ Supervisor analyzing...
✓ ComponentWriter: Generated App.jsx
✓ ComponentWriter: Generated TodoList.jsx
✓ E2E Generator: Generated App.test.js
✅ COMPLETE!

📁 Generated Files:
   Total: 45 files
   .jsx: 8
   .json: 3
   .js: 12

Test another? (y/n): n

✅ Test passed!
```

### Example 2: Failed Test

```
$ python test_agent_websocket_real_e2e.py

📋 PHASE 1: SETUP
❌ Workspace not clean! Found: [old_app/]

Fix: rm -rf ~/TestApps/*

❌ E2E TEST FAILED!
Exit code: 1
```

---

## ❓ FAQ

**Q: Can I run multiple tests simultaneously?**  
A: Yes, on different ports (8002, 8003, 8004) and workspaces

**Q: How long does a test take?**  
A: 60-120 seconds normally

**Q: What if backend crashes?**  
A: Restart with `python start_server.py --port=8002`

**Q: Where are generated files?**  
A: `~/TestApps/manual_interactive_test/TIMESTAMP/APPNAME/`

**Q: Can I keep generated files after test?**  
A: Yes, they're in ~/TestApps/ automatically

**Q: How do I integrate into CI/CD?**  
A: Use `test_agent_websocket_real_e2e.py`, check exit code

**Q: What's the difference from app E2E testing?**  
A: Agent E2E tests the agent itself, not the generated app

---

## 🎯 NEXT STEPS

### If Test Passed ✅
1. Great! Agent is working
2. Proceed with production deployment
3. Run regularly for regression detection

### If Test Failed ❌
1. Identify failure phase (see checklist)
2. Follow debugging steps
3. Fix identified issue
4. Run test again

### For Continuous Testing
1. Add to CI/CD pipeline
2. Run on every commit
3. Alert on failures
4. Track metrics over time

---

**Version**: 1.0  
**Status**: READY FOR PRODUCTION ✅  
**Last Updated**: 2025-02-15

---

## 📞 Support

For issues:
1. Check AGENT_TESTING_CHECKLIST.md
2. Review CRITICAL_FAILURE_INSTRUCTIONS.md
3. Check backend logs: `tail -f /tmp/v7_server.log`
4. Run with `--debug` flag for verbose output