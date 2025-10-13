# Quick Reference: Running E2E Complex App Test

**Quick Start Guide for:** `test_e2e_complex_app_workflow.py`

---

## 🚀 Quick Start (3 Steps)

### 1. Start Backend

```bash
cd /Users/dominikfoert/git/KI_AutoAgent/backend
./venv/bin/python main_v6_websocket.py
```

**Verify:** Backend logs show "WebSocket server started on ws://localhost:8002"

### 2. Run Test

```bash
cd /Users/dominikfoert/git/KI_AutoAgent
./venv/bin/python backend/tests/test_e2e_complex_app_workflow.py
```

### 3. Check Results

```bash
# View test report
cat /tmp/e2e_complex_app_test_report.json | jq .

# View generated app
ls -la ~/TestApps/e2e_complex_app/

# View logs
tail -100 /tmp/e2e_complex_app_test.log
```

---

## 📊 Expected Result

### Success (Exit Code 0)

```
✅ Test PASSED
Pass Rate: 100.0%
Features Passed: 10/10
Duration: ~5 minutes
Files Generated: 47+
```

### Failure (Exit Code 1)

```
❌ Test FAILED
Pass Rate: <80%
Check errors in report
```

---

## 🔍 What Gets Tested

1. ✅ **Automatic Workflow Generation** (WorkflowPlannerV6)
2. ✅ **All 4 Agents Execute** (Research, Architect, Codesmith, ReviewFix)
3. ✅ **MCP Protocol** (All services via MCP)
4. ✅ **Complex App Generated** (47+ files, full-stack)
5. ✅ **High Quality** (Score > 0.75)
6. ✅ **Workspace Isolation** (Files in ~/TestApps/)
7. ✅ **No Errors** (Clean execution)

---

## 🐛 Quick Debug

### Backend Not Running?

```bash
# Check if backend is up
curl http://localhost:8002/health || echo "Backend not running"

# Start backend
cd backend && ./venv/bin/python main_v6_websocket.py
```

### MCP Servers Not Connected?

```bash
# Check MCP servers
claude mcp list

# Should show 5/6 connected (workflow may fail)
```

### Test Workspace Dirty?

```bash
# Clean workspace
rm -rf ~/TestApps/e2e_complex_app/

# Re-run test
./venv/bin/python backend/tests/test_e2e_complex_app_workflow.py
```

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `backend/tests/test_e2e_complex_app_workflow.py` | Test script |
| `/tmp/e2e_complex_app_test.log` | Test logs |
| `/tmp/e2e_complex_app_test_report.json` | Test report |
| `/tmp/v6_server.log` | Backend logs |
| `~/TestApps/e2e_complex_app/` | Generated application |

---

## ⏱️ Timing

| Phase | Duration |
|-------|----------|
| Workflow Planning | ~10s |
| Research | ~30s |
| Architect | ~45s |
| Codesmith | ~3-4 min |
| ReviewFix | ~30s |
| **Total** | **~5-6 min** |

---

## 📚 Full Documentation

See: `E2E_COMPLEX_APP_TEST.md` for complete documentation

---

**Last Updated:** 2025-10-13
