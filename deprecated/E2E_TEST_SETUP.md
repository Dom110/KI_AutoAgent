# E2E Test Setup Guide

## 🎯 Architecture Overview

```
Production Server:
├─ Location: /Users/dominikfoert/git/KI_AutoAgent
├─ Venv: /Users/dominikfoert/git/KI_AutoAgent/venv
├─ Listens on: ws://localhost:8002/ws/chat
└─ MUST start from project root

E2E Tests:
├─ Location: ~/TestApps/e2e_test_workspace (separate!)
├─ No server startup needed
├─ Connects via WebSocket ONLY
└─ Uses project's Python/venv
```

## ⚠️ Critical Rule

**NEVER** run tests from `/Users/dominikfoert/git/KI_AutoAgent` directory!

→ Architect Agent scans project codebase
→ Finds itself
→ Infinite loop + data corruption ❌

## ✅ Correct E2E Test Workflow

### 1️⃣ Start the Server (Once)

```bash
# Terminal 1: Start server
cd /Users/dominikfoert/git/KI_AutoAgent
source venv/bin/activate
python backend/api/server_v7_mcp.py

# Output should show:
# ✅ Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8002
```

**Or use the quick restart script:**
```bash
/Users/dominikfoert/git/KI_AutoAgent/dev_restart_server.sh
```

### 2️⃣ Create Test Workspace (Once)

```bash
# Create workspace OUTSIDE project
mkdir -p ~/TestApps/e2e_test_workspace
cd ~/TestApps/e2e_test_workspace
```

### 3️⃣ Setup Python Environment for Tests

```bash
# Still in project root, activate venv
cd /Users/dominikfoert/git/KI_AutoAgent
source venv/bin/activate

# Copy test file to test workspace
cp e2e_test_v7_0_supervisor.py ~/TestApps/e2e_test_workspace/
```

### 4️⃣ Run Tests (from test workspace)

```bash
# Terminal 2: Run tests
cd ~/TestApps/e2e_test_workspace
python e2e_test_v7_0_supervisor.py

# Tests connect to: ws://localhost:8002/ws/chat
# Server processes the requests
# Results displayed in Terminal 2
```

## 🔄 During Development

**To modify server code and restart:**

```bash
# In project root terminal
# Press CTRL+C to stop server
# Edit files
/Users/dominikfoert/git/KI_AutoAgent/dev_restart_server.sh

# In test terminal, just re-run tests
cd ~/TestApps/e2e_test_workspace
python e2e_test_v7_0_supervisor.py
```

## 📋 Complete Setup Script (Automated)

```bash
#!/bin/bash
# setup_e2e_tests.sh

# 1. Create test workspace
mkdir -p ~/TestApps/e2e_test_workspace

# 2. Copy test file
cp /Users/dominikfoert/git/KI_AutoAgent/e2e_test_v7_0_supervisor.py \
   ~/TestApps/e2e_test_workspace/

# 3. Start server
cd /Users/dominikfoert/git/KI_AutoAgent
source venv/bin/activate
python backend/api/server_v7_mcp.py &

# Wait for server to start
sleep 5

# 4. Run tests
cd ~/TestApps/e2e_test_workspace
python e2e_test_v7_0_supervisor.py

echo "✅ E2E tests complete!"
```

## 🚀 Quick Commands Reference

```bash
# Quick restart (kills old, starts new)
/Users/dominikfoert/git/KI_AutoAgent/dev_restart_server.sh

# Run tests (from test workspace)
cd ~/TestApps/e2e_test_workspace && python e2e_test_v7_0_supervisor.py

# Check server is running
curl http://localhost:8002/health

# Check logs while running
tail -f ~/TestApps/e2e_test_workspace/test.log
```

## ❌ Common Mistakes

| ❌ Wrong | ✅ Correct |
|---------|----------|
| Run test from project root | Run test from ~/TestApps/e2e_test_workspace |
| Start server from random folder | Start server from /Users/dominikfoert/git/KI_AutoAgent |
| Copy entire project to test folder | Copy ONLY test file to test folder |
| No venv activated | Venv activated (from project root) |
| Test tries to start server | Test only uses WebSocket |

## 🔍 Troubleshooting

### Server fails to start: "SERVER MUST RUN FROM PROJECT ROOT"
→ Make sure you're in: `/Users/dominikfoert/git/KI_AutoAgent`
→ Check: `pwd` command shows correct path

### Tests can't connect to server
→ Is server running? Check: `ps aux | grep server_v7_mcp`
→ Is port 8002 listening? Check: `lsof -i :8002`

### "Infinite loop" / Agent finding itself
→ You're running tests from wrong location
→ Must be: ~/TestApps/e2e_test_workspace
→ NOT: /Users/dominikfoert/git/KI_AutoAgent

### Import errors
→ Venv not activated
→ Python doesn't see backend module
→ Fix: `source venv/bin/activate` from project root

## 📝 Summary

| Component | Location | How to Start |
|-----------|----------|-------------|
| **Server** | `/Users/dominikfoert/git/KI_AutoAgent` | `python backend/api/server_v7_mcp.py` |
| **Tests** | `~/TestApps/e2e_test_workspace` | `python e2e_test_v7_0_supervisor.py` |
| **Connection** | N/A | WebSocket: `ws://localhost:8002/ws/chat` |
| **Python** | Project venv | `source venv/bin/activate` (from project root) |

**Key Rule:** Server and tests are completely separate processes. Tests are just clients!