# E2E Testing Best Practices Guide

**Extracted from:** CLAUDE.md
**Date:** 2025-10-13
**Version:** v6.0+

---

## 🧪 E2E TESTING BEST PRACTICES (v6.0+)

### **CRITICAL: Test Workspace Isolation**

**Discovered:** 2025-10-11 E2E Test Bug - Claude CLI found old test artifacts in development repo

---

## 🚨 GOLDEN RULE

```
🚨 NIEMALS E2E Tests im Development Workspace durchführen!
🚨 NEVER run E2E tests in the development repository!
```

---

## ⚠️ Why This Matters

### **Problem Scenario:**
```
/Users/.../KI_AutoAgent/  ← Development Repo
├── backend/              ← Agent source code
├── test_e2e.py           ← E2E test script
└── task-manager-app/     ← OLD test output (❌ PROBLEM!)

# Claude CLI runs E2E test:
1. Test runs from: /Users/.../KI_AutoAgent/
2. Claude CLI subprocess CWD: /Users/.../KI_AutoAgent/
3. Claude finds: task-manager-app/ (old output)
4. Claude reads old app
5. Claude gets confused: "App already exists!"
6. Codesmith crashes after 5 minutes
7. ❌ Test FAILS but bug is hidden!
```

### **Impact:**
- Claude finds old test artifacts
- Gets confused about what to generate
- Context pollution with obsolete code
- Test failures that are hard to debug
- Claude CLI subprocess crashes
- Wasted API tokens and time

---

## ✅ Correct E2E Test Setup

### 1. Separate Test Workspace

```bash
# ✅ CORRECT: Isolated test directory
~/TestApps/
├── test_run_1/         # First test execution
│   └── task_manager_app/
├── test_run_2/         # Second test execution
│   └── task_manager_app/
└── current/            # Current test (symlink or latest)
    └── task_manager_app/

# ❌ WRONG: Test in development repo
~/git/KI_AutoAgent/
├── backend/            # Source code
├── test_e2e.py         # Test script
└── task-manager-app/   # Test output ❌ POLLUTES WORKSPACE!
```

### 2. Claude CLI Working Directory

**CRITICAL:** Set `cwd` parameter in subprocess!

```python
# File: backend/adapters/claude_cli_simple.py

# ❌ WRONG: No CWD specified
process = await asyncio.create_subprocess_exec(
    *cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
# Result: Runs from wherever Python was started (❌ chaos!)

# ✅ CORRECT: Explicit CWD to workspace
process = await asyncio.create_subprocess_exec(
    *cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=self.workspace_path  # 🎯 Use target workspace!
)
# Result: Claude CLI runs in clean, isolated workspace ✅
```

### 3. E2E Test Script Template

```python
#!/usr/bin/env python3
"""
E2E Test - Isolated Workspace Pattern

CRITICAL: This test MUST run in a separate workspace!
"""

import os
from pathlib import Path
import shutil

# ✅ CORRECT: Separate test workspace
TEST_WORKSPACE = Path.home() / "TestApps" / "e2e_test_run"

# ❌ WRONG: Development repo as workspace
# TEST_WORKSPACE = Path(__file__).parent / "test_output"  # ❌ NO!

def setup_test():
    """Setup clean test workspace."""
    # Remove old test artifacts
    if TEST_WORKSPACE.exists():
        print(f"🧹 Cleaning old workspace: {TEST_WORKSPACE}")
        shutil.rmtree(TEST_WORKSPACE)

    # Create fresh workspace
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created clean workspace: {TEST_WORKSPACE}")

    # Verify isolation
    assert not (TEST_WORKSPACE / "task-manager-app").exists()
    print("✅ Workspace verified clean")

async def run_e2e_test():
    """Run E2E test in isolated workspace."""
    setup_test()

    # Connect to backend with isolated workspace
    client = E2ETestClient(
        ws_url="ws://localhost:8002/ws/chat",
        workspace_path=str(TEST_WORKSPACE)
    )

    await client.connect()
    await client.send_task("Create Task Manager app...")

    # Verify files created in correct location
    assert (TEST_WORKSPACE / "README.md").exists()
    print("✅ Files generated in isolated workspace")

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
```

### 4. Backend Workspace Handling

```python
# File: backend/subgraphs/codesmith_subgraph_v6_1.py

async def codesmith_node(state: dict) -> dict:
    """Codesmith node - MUST use correct workspace."""

    # Get workspace from state (set by WebSocket init)
    workspace_path = state.get("workspace_path")

    if not workspace_path:
        raise ValueError("workspace_path required in state!")

    # Create Claude CLI LLM with correct workspace
    llm = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        workspace_path=workspace_path,  # 🎯 Pass to subprocess!
        ...
    )

    # Claude CLI will now run with correct CWD
    response = await llm.ainvoke([...])
```

---

## 🧹 Test Cleanup Best Practices

### After Each Test:

```python
def cleanup_test(keep_on_success: bool = False):
    """Cleanup test workspace."""

    if keep_on_success and test_passed:
        print(f"✅ Test passed - keeping workspace: {TEST_WORKSPACE}")
        # Optional: Create timestamped backup
        backup = TEST_WORKSPACE.parent / f"test_success_{datetime.now():%Y%m%d_%H%M%S}"
        shutil.copytree(TEST_WORKSPACE, backup)
        print(f"📦 Backup created: {backup}")
    else:
        print(f"🧹 Cleaning up test workspace: {TEST_WORKSPACE}")
        if TEST_WORKSPACE.exists():
            shutil.rmtree(TEST_WORKSPACE)
        print("✅ Cleanup complete")
```

### Continuous Integration:

```bash
# CI/CD pipeline test script
#!/bin/bash

# Create unique test workspace per run
TEST_ID=$(date +%Y%m%d_%H%M%S)_$$
TEST_WS="/tmp/ki_autoagent_e2e_${TEST_ID}"

echo "🧪 Running E2E test in: $TEST_WS"

# Run test
python test_e2e_websocket.py --workspace "$TEST_WS"
TEST_EXIT=$?

# Cleanup (always in CI)
rm -rf "$TEST_WS"

exit $TEST_EXIT
```

---

## 🛡️ Development Repo Protection

### Add to .gitignore:

```gitignore
# E2E Test Outputs (should NEVER be in development repo!)
test_output/
task-manager-app/
*_e2e_test/
TestApps/
tmp_*_workspace/

# Test artifacts
*.e2e.log
e2e_test_results_*.json
```

### Pre-commit Hook:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check for test artifacts in development repo
if git diff --cached --name-only | grep -E "task-manager-app|test_output"; then
    echo "❌ ERROR: E2E test artifacts found in commit!"
    echo "   E2E tests must run in separate workspace (~/TestApps/)"
    echo "   Remove: git reset HEAD <file>"
    exit 1
fi
```

---

## 🔍 Debugging E2E Test Issues

### Common Issues:

#### 1. "App already exists" / Claude reads wrong files:
```bash
# Debug: Check Claude CLI working directory
grep '"cwd":' /tmp/claude_cli_debug.log

# Should show:
"cwd": "/Users/.../TestApps/task_manager_app"

# NOT:
"cwd": "/Users/.../git/KI_AutoAgent"  ❌
```

#### 2. Files generated in wrong location:
```bash
# Check workspace_path in backend logs
tail -f /tmp/v6_server.log | grep "workspace_path"

# Should see:
workspace_path: /Users/.../TestApps/task_manager_app  ✅
```

#### 3. Claude CLI crashes after 5 minutes:
```bash
# Check raw CLI output
cat /var/folders/.../tmp*_claude_raw.jsonl | grep "Glob\|Read"

# If you see reads from development repo:
# → CWD is wrong! Fix subprocess cwd parameter
```

---

## ✅ Checklist for E2E Tests

### Before Running Test:
- [ ] Test workspace is OUTSIDE development repo
- [ ] Test workspace is clean (no old artifacts)
- [ ] Claude CLI `cwd` parameter is set correctly
- [ ] Backend receives correct `workspace_path` from client
- [ ] `.gitignore` excludes test outputs

### After Test Failure:
- [ ] Check Claude CLI working directory in logs
- [ ] Verify no old apps in test workspace
- [ ] Check if Claude read files from development repo
- [ ] Inspect subprocess CWD in debug logs
- [ ] Clean workspace and re-run

### After Test Success:
- [ ] Verify files in correct location
- [ ] Optional: Keep workspace for manual inspection
- [ ] Run cleanup unless debugging needed
- [ ] Document any new issues found

---

## 📊 E2E Test Best Practices Summary

| ✅ DO | ❌ DON'T |
|-------|----------|
| Use separate `~/TestApps/` directory | Test in development repo |
| Set `cwd=workspace_path` in subprocess | Let subprocess inherit CWD |
| Clean workspace before each test | Reuse old test workspaces |
| Verify workspace isolation | Assume CWD is correct |
| Add test outputs to `.gitignore` | Commit test artifacts |
| Use timestamped test directories | Overwrite previous tests |
| Log workspace_path in all agents | Trust default working directory |

---

## 🎯 Key Lesson

**The E2E test on 2025-10-11 discovered this critical bug:**

- Codesmith crashed after 5 minutes
- Root cause: Wrong working directory
- Claude found old test app in development repo
- Got confused and crashed
- **Fix:** Set `cwd=self.workspace_path` in subprocess

**This is why we do E2E testing!** 🎯

---

## 🚨 Critical Failure Detection

**See:** `CRITICAL_FAILURE_INSTRUCTIONS.md` for how to properly interpret test results.

**Key Rules:**
1. Test disconnection = Test FAILED (not "partial success")
2. 0% coverage = NO features validated (not "some features working")
3. Backend log activity ≠ Passing tests
4. Code existence ≠ Working system

**ANY error = System failure. NO exceptions.**

---

## 📚 Related Documentation

- **Critical Failure Instructions:** `/CRITICAL_FAILURE_INSTRUCTIONS.md`
- **Claude CLI Integration:** `/CLAUDE_CLI_INTEGRATION.md`
- **Build Validation:** `/BUILD_VALIDATION_GUIDE.md`
- **System Architecture:** `/ARCHITECTURE_v6.2_CURRENT.md`

---

**Last Updated:** 2025-10-13
**Reference:** See CRITICAL_FAILURE_INSTRUCTIONS.md for error handling guidelines
