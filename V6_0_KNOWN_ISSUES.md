# KI AutoAgent v6.0 - Known Issues

**Version:** 6.0.0-alpha.1
**Last Updated:** 2025-10-08
**Status:** Alpha Development

---

## 🚨 Critical Issues

**None yet** - Development just started

---

## ⚠️ High Priority Issues

**None yet**

---

## 📌 Medium Priority Issues

### Issue #2: State Transformations Missing
**Category:** Feature / In Progress
**Severity:** Medium
**Status:** Expected for Phase 2
**Phase:** Phase 2 (detected), Phase 3 (will fix)
**Date:** 2025-10-08

**Description:**
workflow_v6.py does not implement state transformations between SupervisorState and subgraph states (ResearchState, ArchitectState, etc.)

**Expected Behavior:**
When SupervisorGraph invokes Research subgraph, state should be transformed:
- SupervisorState → ResearchState (via `supervisor_to_research()`)
- ResearchState → SupervisorState (via `research_to_supervisor()`)

**Actual Behavior:**
Research subgraph receives SupervisorState directly, causing:
```
KeyError: 'query'  # ResearchState expects 'query', gets SupervisorState with 'user_query'
```

**Steps to Reproduce:**
```bash
./venv/bin/python backend/workflow_v6.py
# Workflow starts, then crashes with KeyError
```

**Fix:**
Phase 3 will add state transformations in graph compilation:
```python
# Add input/output transformations to subgraph nodes
graph.add_node(
    "research",
    research_subgraph,
    input=supervisor_to_research,
    output=research_to_supervisor
)
```

**Related:**
- backend/state_v6.py (transformations defined but not used)
- V6_0_MIGRATION_PLAN.md Phase 3

---

### Issue #3: Pytest Async Fixtures Not Working
**Category:** Bug
**Severity:** Medium
**Status:** New
**Phase:** Phase 2
**Date:** 2025-10-08

**Description:**
Unit tests in test_workflow_v6_checkpoint.py have async fixture problems

**Expected Behavior:**
```python
@pytest.fixture
async def workflow(temp_workspace):
    wf = WorkflowV6(workspace_path=temp_workspace)
    await wf.initialize()
    yield wf
    await wf.cleanup()
```
Should provide initialized workflow to tests.

**Actual Behavior:**
```
AttributeError: 'async_generator' object has no attribute 'run'
```

**Fix:**
Need to use pytest-asyncio correctly:
```python
@pytest_asyncio.fixture
async def workflow(temp_workspace):
    # ...
```

**Workaround:**
Use manual smoke tests instead:
```bash
./venv/bin/python backend/workflow_v6.py
```

**Related:**
- backend/tests/unit/test_workflow_v6_checkpoint.py
- backend/tests/unit/test_memory_v6_basic.py

---

### Issue #4: Memory System Not Tested
**Category:** Testing
**Severity:** Medium
**Status:** New
**Phase:** Phase 2
**Date:** 2025-10-08

**Description:**
memory_system_v6.py code written but not tested yet

**Impact:**
- Unknown if FAISS integration works
- Unknown if OpenAI embeddings work
- Unknown if SQLite metadata storage works

**Expected Behavior:**
Run memory system smoke test and unit tests

**Fix Required:**
Phase 2.1 will:
1. Fix pytest fixtures
2. Run unit tests
3. Run smoke test with dummy embeddings

**Related:**
- backend/memory/memory_system_v6.py
- backend/tests/unit/test_memory_v6_basic.py

---

## 💡 Low Priority / Future Improvements

### Issue #1: Python 3.13 Only
**Category:** Design Decision
**Status:** By Design
**Description:** v6.0 only supports Python 3.13, no backwards compatibility

**Impact:**
- Users with older Python versions cannot use v6.0
- Requires Python 3.13 installation

**Workaround:**
- Install Python 3.13
- Or stay on v5.9.0

**Future:**
- Consider Python 3.12 support if requested
- Document Python version clearly in README

---

## 📝 Issue Template

```
### Issue #X: Title

**Category:** Bug | Feature | Performance | Documentation
**Severity:** Critical | High | Medium | Low
**Status:** New | In Progress | Fixed | Wontfix
**Phase:** Phase X where discovered
**Date:** YYYY-MM-DD

**Description:**
What is the issue?

**Expected Behavior:**
What should happen?

**Actual Behavior:**
What actually happens?

**Steps to Reproduce:**
1. Step 1
2. Step 2
3. ...

**Workaround:**
Temporary solution (if any)

**Fix:**
How to fix (if known)

**Related:**
- Related issues
- Related files
- Related documentation
```

---

## 🔍 Issue Statistics

**Total Issues:** 1 (design decision)
**Critical:** 0
**High:** 0
**Medium:** 0
**Low:** 1

**By Category:**
- Bugs: 0
- Features: 0
- Performance: 0
- Design: 1
- Documentation: 0

**By Status:**
- New: 0
- In Progress: 0
- Fixed: 0
- By Design: 1

---

## 📋 Issue Tracking Workflow

1. **Discovery:** Issue found during development/testing
2. **Documentation:** Add to this file with all details
3. **Triage:** Assign severity and category
4. **Fix:** Implement fix in code
5. **Test:** Verify fix works
6. **Update:** Mark as Fixed in this file
7. **Archive:** After 1 month, move to archive section

---

## 📦 Archive (Fixed Issues)

**None yet** - No issues fixed yet (just started!)

---

## 📝 Notes

- This file will be actively maintained during v6.0 development
- All issues discovered during testing will be documented here
- Critical and High priority issues block releases
- Medium priority issues should be fixed before stable release
- Low priority issues may be deferred to future versions
