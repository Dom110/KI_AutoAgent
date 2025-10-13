# KI AutoAgent Tests - v6.2

**Last Updated:** 2025-10-13
**Version:** v6.2.0-alpha

---

## 📁 Directory Structure

```
backend/tests/
├── README.md                          # This file
├── __init__.py
│
├── e2e_comprehensive_v6_2.py          # ✅ v6.2 Comprehensive E2E Test
├── e2e_test3_error_handling.py        # ✅ v6.2 Error Handling E2E Test
│
├── test_planner_only.py               # ✅ Workflow Planner Unit Tests
├── test_workflow_planner_e2e.py       # ✅ Planner E2E Tests
├── test_workflow_planner_smoke.py     # ✅ Planner Smoke Tests
├── test_memory_manager_v6_2.py        # ✅ Memory Manager Tests
├── test_memory_manager_unit.py        # ✅ Memory Unit Tests
├── test_message_bus_v6.py             # ✅ Message Bus Tests
├── test_base_agent_communication.py   # ✅ Agent Communication Tests
├── test_codesmith_direct.py           # ✅ Codesmith Direct Tests
│
├── monitor_e2e.sh                     # ✅ E2E Monitoring Script
├── monitor_test.sh                    # ✅ Test Monitoring Script
├── cleanup_tests.sh                   # ⚠️ Legacy cleanup script
│
└── legacy/                            # 📦 Archived tests (v6.0/v6.1)
    ├── README.md                      # Archive documentation
    ├── e2e/                           # Old E2E tests
    ├── unit/                          # Old unit tests
    ├── native/                        # Manual intervention tests
    └── test_file_validation.py        # File validation tests
```

---

## 🧪 Active Tests (v6.2)

### E2E Tests

#### `e2e_comprehensive_v6_2.py`
**Purpose:** Tests all v6.2 features (10 features across 4 phases)
**Coverage:** ~70% (7/10 features)
**Duration:** ~10-15 minutes
**Workspace:** `~/TestApps/v6_2_comprehensive_test`

**Features Tested:**
- Phase 1: Perplexity API, ASIMOV Rule 3
- Phase 2: Learning System, Curiosity System, Predictive System
- Phase 3: Tool Registry, Approval Manager, Dynamic Workflow
- Phase 4: Neurosymbolic Reasoning, Self-Diagnosis

**Run:**
```bash
python3.10 e2e_comprehensive_v6_2.py
```

#### `e2e_test3_error_handling.py`
**Purpose:** Tests the 3 features missed by comprehensive test
**Coverage:** 100% combined with comprehensive test
**Duration:** ~5-10 minutes
**Workspace:** `~/TestApps/v6_2_error_test`

**Features Tested:**
- ASIMOV Rule 3 (Global Error Search)
- Approval Manager (Destructive operations)
- Self-Diagnosis (Error recovery)

**Run:**
```bash
python3.10 e2e_test3_error_handling.py
```

---

### Unit Tests

#### `test_planner_only.py`
**Purpose:** Tests workflow planner with research agent modes
**Tests:** 8 test cases including German language support
**Duration:** ~30 seconds
**Features:** v6.2 research agent modes (research/explain/analyze)

**Run:**
```bash
python3.10 test_planner_only.py
```

#### `test_workflow_planner_e2e.py`
**Purpose:** End-to-end planner tests with full workflow
**Duration:** ~2-3 minutes

#### `test_workflow_planner_smoke.py`
**Purpose:** Quick smoke tests for planner
**Duration:** ~10 seconds

#### `test_memory_manager_v6_2.py`
**Purpose:** Memory manager v6.2 tests
**Features:** Memory store, search, stats, count

#### `test_memory_manager_unit.py`
**Purpose:** Memory unit tests

#### `test_message_bus_v6.py`
**Purpose:** Message bus tests

#### `test_base_agent_communication.py`
**Purpose:** Agent communication tests

#### `test_codesmith_direct.py`
**Purpose:** Direct codesmith tests

---

## 🚨 Critical Rules

### Test Workspace Isolation

**GOLDEN RULE:**
```
🚨 NEVER run E2E tests in development repository!
🚨 ALWAYS use separate test workspace (~/TestApps/)
```

**Why?**
- Claude CLI finds old test artifacts in dev repo
- Gets confused: "App already exists!"
- Tests fail but bug is hidden
- Subprocess CWD must be explicit

**Correct Setup:**
```python
TEST_WORKSPACE = Path.home() / "TestApps" / "v6_2_test"  # ✅ CORRECT
# NOT: Path(__file__).parent / "test_output"              # ❌ WRONG
```

**See:** `/E2E_TESTING_GUIDE.md` for complete documentation

---

## 📊 Running Tests

### All Tests:
```bash
cd /Users/dominikfoert/git/KI_AutoAgent/backend/tests

# Quick unit tests (~1 minute)
python3.10 test_planner_only.py
python3.10 test_workflow_planner_smoke.py

# Full E2E tests (~20 minutes)
python3.10 e2e_comprehensive_v6_2.py
python3.10 e2e_test3_error_handling.py
```

### Monitoring:
```bash
# Monitor E2E test in separate terminal
./monitor_e2e.sh

# Monitor specific test
./monitor_test.sh
```

---

## 🗑️ Cleanup

### Temporary Files (Generated during tests):
- `*.log` - Test output logs
- `*.json` - Test result files
- `test*_output.log` - Specific test outputs
- `test*_results_*.json` - Timestamped results

**These are in `.gitignore` and should NOT be committed!**

### Clean Up:
```bash
# Remove all temporary test files
rm -f *.log *.json test*_output.log test*_results_*.json

# Or use git clean (careful!)
git clean -n backend/tests/  # Preview
git clean -f backend/tests/  # Execute
```

---

## 📦 Legacy Tests

**Location:** `legacy/`
**Status:** Archived (v6.0/v6.1)
**Reason:** Superseded by v6.2 architecture

**Contents:**
- 10 legacy test files
- Old E2E workflows
- Old memory/checkpoint tests
- Manual intervention tests

**Usage:**
- Kept for reference
- NOT run in CI/CD
- May require import updates
- See `legacy/README.md` for details

**To run legacy tests:**
1. Update imports to v6.2 architecture
2. Check API key requirements
3. May require manual intervention

---

## 🎯 Test Coverage Goals

| Feature | Test | Status |
|---------|------|--------|
| Workflow Planner | test_planner_only.py | ✅ |
| Research Modes | test_planner_only.py | ✅ |
| Memory Manager | test_memory_manager_*.py | ✅ |
| Message Bus | test_message_bus_v6.py | ✅ |
| Agent Communication | test_base_agent_communication.py | ✅ |
| Codesmith | test_codesmith_direct.py | ✅ |
| E2E Comprehensive | e2e_comprehensive_v6_2.py | ✅ |
| E2E Error Handling | e2e_test3_error_handling.py | ✅ |

**Overall Coverage:** 100% of v6.2 features validated

---

## 📚 Related Documentation

- **E2E Testing Guide:** `/E2E_TESTING_GUIDE.md`
- **Critical Failure Instructions:** `/CRITICAL_FAILURE_INSTRUCTIONS.md`
- **Claude CLI Integration:** `/CLAUDE_CLI_INTEGRATION.md`
- **Build Validation:** `/BUILD_VALIDATION_GUIDE.md`
- **System Architecture:** `/ARCHITECTURE_v6.2_CURRENT.md`

---

## 🔧 Troubleshooting

### Test Fails with "App already exists"
**Cause:** Test running in dev repo, Claude finds old artifacts
**Fix:** Ensure `workspace_path` points to `~/TestApps/`

### Claude CLI crashes after 5 minutes
**Cause:** Wrong working directory, reads wrong files
**Fix:** Set `cwd=workspace_path` in subprocess call

### Files generated in wrong location
**Cause:** Backend not using correct workspace_path
**Fix:** Check WebSocket init message includes workspace_path

**See:** `/E2E_TESTING_GUIDE.md` for detailed troubleshooting

---

## ✅ Pre-Commit Checklist

Before committing test changes:

- [ ] All tests pass locally
- [ ] No `.log` or `.json` files in commit
- [ ] Test workspaces in `~/TestApps/` (not dev repo)
- [ ] Updated documentation if test behavior changed
- [ ] Legacy tests remain untouched (archived)

---

**Last Updated:** 2025-10-13
**Maintainer:** KI AutoAgent Team
**Questions:** See related documentation or check `legacy/README.md` for historical context
