# E2E Testing Scripts - User Guide

## 📋 Available Scripts

### 1. `run_e2e_complete.sh` ⭐ **RECOMMENDED**
**Purpose:** Complete E2E test orchestration with server startup and logging
**What it does:**
- Stops old server processes
- Validates websockets installation (13.1)
- Starts backend server with start_server.py
- Waits for server readiness (health check)
- Runs E2E tests with WebSocket logging
- Cleanly shuts down server
- Displays comprehensive summary

**Usage:**
```bash
bash run_e2e_complete.sh
```

**Output:**
- Server logs: `.logs/server_YYYYMMDD_HHMMSS.log`
- E2E logs: `.logs/e2e_test_YYYYMMDD_HHMMSS.log`
- Orchestration: `.logs/e2e_full_YYYYMMDD_HHMMSS.log`
- WebSocket logs: `~/TestApps/e2e_reviewfix_validation_*/logs/websocket_*.log`

**Time:** ~9-10 seconds for basic tests

---

### 2. `test_e2e_with_websocket_logging.py`
**Purpose:** Core E2E test with comprehensive WebSocket logging
**What it does:**
- Creates isolated test workspace
- Connects via WebSocket
- Initializes workspace
- Executes 4 phases of tests
- Logs every WebSocket message (sent/received)
- Generates separate logs for analysis

**Usage:**
```bash
# If server already running
python test_e2e_with_websocket_logging.py

# Or via the orchestration script (recommended)
bash run_e2e_complete.sh
```

**Features:**
- 6 test phases (Environment, Connection, Init, Query, Code Gen, ReviewFix)
- Separate log files for send/recv/combined
- Massive debugging output
- Proper error handling

**Log Files Created:**
```
~/TestApps/e2e_reviewfix_validation_YYYYMMDD_HHMMSS/logs/
├── e2e_main_*.log           # Main test execution
├── websocket_send_*.log     # Outgoing messages only
├── websocket_recv_*.log     # Incoming messages only
└── websocket_both_*.log     # Combined chronological view
```

---

### 3. `monitor_e2e_logs.sh`
**Purpose:** Real-time log monitoring during test execution
**What it does:**
- Displays server logs and test logs side-by-side
- Follows new entries in real-time
- Helps visualize what's happening during tests

**Usage:**
```bash
# Terminal 1: Start tests
bash run_e2e_complete.sh

# Terminal 2 (parallel): Monitor logs
bash monitor_e2e_logs.sh
```

**Output:**
- Real-time server events
- Real-time test progress
- Side-by-side view of both streams

---

## 🚀 Quick Start - 3 Ways

### Way 1: Automated (Easiest)
```bash
cd /Users/dominikfoert/git/KI_AutoAgent
bash run_e2e_complete.sh
```
This handles everything automatically.

### Way 2: With Monitoring (Recommended for Development)
```bash
# Terminal 1
bash run_e2e_complete.sh

# Terminal 2 (in parallel)
bash monitor_e2e_logs.sh
```

### Way 3: Manual (If server already running)
```bash
# Terminal 1: Ensure server is running
python start_server.py

# Terminal 2: Run tests
python test_e2e_with_websocket_logging.py
```

---

## 📊 Understanding Test Output

### Server Log Format
```
[HH:MM:SS] SERVER | <message>
[19:04:07] SERVER | 🚀 EXECUTING SUPERVISOR WORKFLOW v7.0 (PURE MCP + STREAMING)
[19:04:07] SERVER | 📡 Initializing MCP connections...
```

### E2E Test Log Format
```
HH:MM:SS.mmm | LEVEL | <message>
19:04:00.112 | INFO | 📁 Test Workspace: /Users/dominikfoert/TestApps/e2e_reviewfix_validation_20251113_190400
19:04:00.114 | INFO | ✅ Phase 'Backend Connection' complete (elapsed: 0.0s)
```

### WebSocket Combined Log (websocket_both_*.log)
```
>>> [1] SENT @ 2025-11-13T19:04:00.112428
{
  "type": "init",
  "workspace_path": "/Users/dominikfoert/TestApps/e2e_reviewfix_validation_20251113_190400"
}

<<< RECEIVED @ 2025-11-13T19:04:00.114039 | Type: initialized
{
  "type": "initialized",
  "session_id": "5cf3e5e2-7adc-4aa7-ba5d-ec37d25cf887",
  ...
}
```

---

## 🔍 Analyzing WebSocket Messages

### Find Latest WebSocket Logs
```bash
ls -lht ~/TestApps/e2e_reviewfix_validation_*/logs/ | head -10
```

### View Combined Message Flow
```bash
WORKSPACE=$(ls -td ~/TestApps/e2e_reviewfix_validation_* 2>/dev/null | head -1)
cat "$WORKSPACE/logs/websocket_both_*.log"
```

### Count Message Types
```bash
cat websocket_both_*.log | grep "<<< RECEIVED" | grep -o "Type: [^$]*" | sort | uniq -c
```

### Extract Only Errors
```bash
cat websocket_both_*.log | grep -i "error"
```

---

## 🐛 Troubleshooting

### "Server not responding"
- Check if port 8002 is in use: `lsof -i :8002`
- Kill old server: `pkill -f "python.*start_server.py"`
- Retry: `bash run_e2e_complete.sh`

### "WebSocket connection refused"
- Ensure server started: Check `.logs/server_*.log` for errors
- Wait 5-10 seconds for full startup
- Check health endpoint: `curl http://localhost:8002/health`

### "No messages received"
- Check message types match server expectations:
  - Init message: `"type": "init"` (not "initialize_workspace")
  - Chat messages: `"type": "chat"` (not "chat_message")
- Review server logs for "error" or "ERROR"
- Check WebSocket logs for error responses

### "Test fails quickly"
- Review WebSocket logs for error messages
- Check server logs for exceptions
- Verify workspace isolation: `/Users/dominikfoert/TestApps/` must be outside git repo

---

## 📈 Performance Expectations

| Metric | Typical Value | Range |
|--------|---------------|-------|
| Server startup | 5-7 seconds | 3-10s |
| WebSocket connect | <100ms | <500ms |
| Workspace init | 1-2 seconds | 0.5-3s |
| First query execute | 2-4 seconds | 1-6s |
| Total test cycle | 9-11 seconds | 8-15s |

---

## 🔄 Common Workflows

### Run test once
```bash
bash run_e2e_complete.sh
```

### Run tests repeatedly (for regression testing)
```bash
for i in {1..5}; do
  echo "Test run #$i"
  bash run_e2e_complete.sh
  sleep 5
done
```

### Monitor specific log file
```bash
# Watch server logs in real-time
tail -f .logs/server_*.log | grep -E "ERROR|error|WARNING"

# Watch E2E test progress
tail -f .logs/e2e_test_*.log | grep "Phase\|✅\|❌"
```

### Archive test results
```bash
WORKSPACE=$(ls -td ~/TestApps/e2e_reviewfix_validation_* | head -1)
tar -czf test_results_$(date +%Y%m%d_%H%M%S).tar.gz "$WORKSPACE"
```

---

## 📝 Log File Locations

**Server Logs:**
```
/Users/dominikfoert/git/KI_AutoAgent/.logs/server_YYYYMMDD_HHMMSS.log
```

**E2E Test Logs:**
```
/Users/dominikfoert/git/KI_AutoAgent/.logs/e2e_test_YYYYMMDD_HHMMSS.log
/Users/dominikfoert/git/KI_AutoAgent/.logs/e2e_full_YYYYMMDD_HHMMSS.log
```

**WebSocket Logs:**
```
~/TestApps/e2e_reviewfix_validation_YYYYMMDD_HHMMSS/logs/
├── websocket_send_YYYYMMDD_HHMMSS.log
├── websocket_recv_YYYYMMDD_HHMMSS.log
└── websocket_both_YYYYMMDD_HHMMSS.log
```

---

## 🎯 Expected Test Results

### Success Output
```
TEST EXECUTION SUMMARY
Total Duration: 9.1s
Phases Completed: 6/6
  Environment Setup → Backend Connection → Workspace Init → Simple Query → Code Generation → ReviewFix Validation
Messages Received: 14
Errors: 0
  ✅ No errors!

✅ Test PASSED - All phases complete!
```

### WebSocket Message Count
- **Sent:** 4 messages
- **Received:** 14-15 messages
- **Types:** connected, initialized, status, progress, agent_event, mcp_progress, workflow_complete, result

---

## 🔧 Maintenance

### Update websockets if needed
```bash
source venv/bin/activate
pip install --upgrade websockets==13.1
pip freeze | grep websockets  # Verify
```

### Clean old test workspaces
```bash
# Remove old tests
rm -rf ~/TestApps/e2e_reviewfix_validation_*

# Or keep last 3
ls -td ~/TestApps/e2e_reviewfix_validation_* | tail -n +4 | xargs rm -rf
```

### Clear logs
```bash
rm -f /Users/dominikfoert/git/KI_AutoAgent/.logs/*.log
```

---

## 📚 Related Documentation

- **Detailed Analysis:** `E2E_TEST_RESULTS_20251113.md`
- **Session Summary:** `SESSION_SUMMARY_20251113_E2E.md`
- **Architecture:** `MCP_MIGRATION_FINAL_SUMMARY.md`
- **Testing Guide:** `E2E_TESTING_GUIDE.md`
- **Core Instructions:** `CLAUDE.md`

---

## ✅ Checklist for Running Tests

- [ ] Activate venv: `source venv/bin/activate`
- [ ] Verify websockets 13.1: `pip list | grep websockets`
- [ ] Check port 8002 available: `lsof -i :8002` (should be empty)
- [ ] Ensure `.ki_autoagent/config/.env` exists with API keys
- [ ] Run `bash run_e2e_complete.sh`
- [ ] Monitor logs as needed
- [ ] Archive results if needed

---

**Last Updated:** 2025-11-13
**Status:** ✅ Production Ready
**Python:** 3.13.8+
**WebSockets:** 13.1
