# Known Issues - KI AutoAgent v6.1-alpha

**Last Updated:** 2025-10-12

---

## 🐛 Critical Issues

### Issue #1: Research Subgraph `list.remove()` Error

**Severity:** HIGH
**Status:** OPEN
**Discovered:** 2025-10-12 (E2E Testing)

**Description:**
The Research Subgraph crashes with a `list.remove(x): x not in list` error when processing complex CREATE requests. This causes the workflow to enter HITL (Human-in-the-Loop) mode and block indefinitely waiting for user input.

**Error Message:**
```
Research failed: list.remove(x): x not in list
```

**Reproduction Steps:**
1. Send a complex CREATE request with 8+ files and multiple features
2. System routes to Research Subgraph for analysis
3. Research Subgraph crashes
4. System enters HITL mode
5. Workflow blocks (timeout: 300s)

**Affected Workflows:**
- ✅ Simple CREATE requests work (no research needed)
- ❌ Complex CREATE requests fail (research triggered)
- ✅ FIX workflow works (no research needed)

**Example Request that Fails:**
```
Create a complete Task Manager web application with:
- Backend (Python FastAPI) with CRUD API
- Frontend (HTML/CSS/JS) with modern UI
- 8+ files: backend/main.py, models.py, storage.py, frontend/index.html, style.css, app.js, etc.
- Multiple features: filtering, priority, persistence, validation
```

**Workaround:**
- Use simpler CREATE requests with fewer files
- Use FIX workflow instead to iteratively build complex apps
- Manually approve HITL request (if available)

**Root Cause:**
Research Subgraph tries to remove an element from a list that doesn't exist. Likely issue with cleanup or state management in `backend/subgraphs/research_subgraph_v6_1.py`.

**Suggested Fix:**
1. Add proper exception handling in Research Subgraph
2. Use `if x in list: list.remove(x)` instead of `list.remove(x)`
3. Improve error recovery (don't go to HITL for known errors)
4. Add fallback: skip research if it fails

**Impact:**
- Blocks complex app generation
- Users cannot create multi-file projects in one shot
- Requires iterative approach via FIX workflow

---

## ⚠️ Minor Issues

### Issue #2: Workflow Timeout for Long Refactorings

**Severity:** LOW
**Status:** OPEN
**Discovered:** 2025-10-12 (E2E Testing)

**Description:**
The FIX workflow can take longer than 5 minutes for extensive refactorings, causing test timeouts even though the workflow completes successfully.

**Example:**
- hello.py refactoring: 31 lines → 364 lines (11.7x growth)
- Duration: 6 minutes 5 seconds
- Test timeout: 5 minutes
- Result: Test fails with timeout, but files are generated correctly

**Affected Workflows:**
- ✅ CREATE workflow: Usually completes in <5 minutes
- ❌ FIX workflow: Can exceed 5 minutes for major refactorings

**Workaround:**
- Increase test timeout to 10 minutes
- Check workspace files even if test times out
- Workflow continues running after test timeout

**Suggested Fix:**
1. Increase default timeout to 10 minutes for FIX workflow
2. Add progress indicators so users know it's still working
3. Optimize ReviewFix loop to reduce iterations
4. Consider parallel execution for independent fixes

**Impact:**
- Test failures (but workflow succeeds)
- User confusion (looks like failure, but files are generated)
- No functional impact on actual workflow

---

## 📋 Future Improvements

### Enhancement #1: Parallel Agent Execution
Currently agents run sequentially. Could parallelize:
- Research + File Discovery (Phase 5 Message Bus ready!)
- Multiple Fixer iterations (if independent)
- Multiple file validations

**Expected Improvement:** 30-50% faster workflows

### Enhancement #2: Incremental Code Generation
For complex apps, generate files incrementally:
1. Generate backend first → Review → Fix
2. Generate frontend next → Review → Fix
3. Generate docs/tests → Review → Fix

**Benefits:**
- Avoids Research Subgraph (smaller requests)
- Better quality (focused reviews)
- Progress visibility

### Enhancement #3: Smart Research Fallback
If Research fails:
1. Log error but continue
2. Use cached knowledge from previous similar requests
3. Fall back to basic CREATE without research insights

**Benefits:**
- No HITL blocking
- Degraded but functional workflow
- Better user experience

---

## ✅ Fixed Issues

None yet (v6.1-alpha initial release)

---

## 🧪 Testing Status

**E2E Tests (2025-10-12):**

| Test | Status | Duration | Notes |
|------|--------|----------|-------|
| Simple CREATE (hello.py) | ✅ PASS | 3:09 | Perfect quality (1.00) |
| FIX Workflow (hello.py) | ✅ PASS* | 6:05 | *Timeout but succeeded |
| Complex CREATE (Task Manager) | ❌ FAIL | N/A | Research Subgraph bug |

**Overall System Health:** 🟡 GOOD (2/3 workflows functional)

---

## 📞 Reporting Issues

If you encounter issues:
1. Check this document first
2. Enable debug logging: `export DEBUG=1`
3. Check backend logs: `/tmp/v6_server.log`
4. Provide minimal reproduction case
5. Include session ID from logs

---

## 🔄 Update History

- **2025-10-12:** Initial Known Issues document created
  - Documented Research Subgraph bug
  - Documented FIX workflow timeout
  - Added E2E test results
