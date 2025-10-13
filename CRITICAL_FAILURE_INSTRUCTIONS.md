# Critical Failure Detection Instructions

**Created:** 2025-10-13
**Priority:** HIGHEST
**Applies To:** ALL AI assistants working on this codebase

---

## 🚨 CORE PRINCIPLE

**ANY ERROR = SYSTEM FAILURE**

There is NO such thing as "partial success" or "mostly working" in software systems.

---

## 📋 MANDATORY RULES

### Rule 1: Test Failures Are System Failures

```
✅ Test Output: "All tests PASSED"
   → System Status: Working

❌ Test Output: "Connection closed", "Timeout", "Error", "Failed"
   → System Status: BROKEN
   → Report: SYSTEM FAILURE
```

**NEVER interpret test failures as:**
- "Partial success"
- "Mostly working"
- "Some features validated"
- "Backend shows activity so it's working"

**CORRECT Response to Test Failure:**
```
❌ SYSTEM FAILURE DETECTED

Test Status: FAILED
Reason: WebSocket disconnected after 2 minutes
Impact: Cannot validate any features
System Status: NOT PRODUCTION-READY

Required Action: FIX the underlying issue before claiming success
```

---

### Rule 2: Log Activity ≠ Working System

**WRONG Interpretation:**
```
Backend logs show:
  [INFO] Workflow started
  [INFO] Research agent invoked
  [INFO] Architect agent invoked

Conclusion: "System is working!" ❌ INCORRECT!
```

**CORRECT Interpretation:**
```
Backend logs show activity BUT:
  - Test disconnected before completion
  - No final success confirmation
  - No feature validation data captured

Conclusion: "System FAILED - test did not complete successfully" ✅
```

**The ONLY valid success indicator:**
- Test script explicitly reports: "✅ Test PASSED"
- All assertions passed
- Test completed without errors/timeouts
- Feature validation data captured successfully

---

### Rule 3: Never Optimize Failure Reporting

**Forbidden Phrases:**
- "Despite some issues, the system is production-ready" ❌
- "90-100% coverage" (when test failed to measure) ❌
- "Features appear to be working based on logs" ❌
- "Backend shows promising results" ❌
- "Mostly successful test run" ❌
- "DEPLOY NOW" (when tests failed) ❌

**Required Phrases When Tests Fail:**
- "System is NOT production-ready" ✅
- "Tests FAILED" ✅
- "Cannot validate feature coverage" ✅
- "System requires fixes before deployment" ✅
- "DO NOT DEPLOY" ✅

---

### Rule 4: Error Severity Classification

**ALL errors are critical until proven otherwise:**

| Error Type | Severity | System Status |
|------------|----------|---------------|
| Test disconnected/timeout | CRITICAL | BROKEN |
| WebSocket connection lost | CRITICAL | BROKEN |
| KeyError in workflow routing | CRITICAL | BROKEN |
| Database locked | CRITICAL | BROKEN |
| Subprocess crash | CRITICAL | BROKEN |
| Test reported 0% coverage | CRITICAL | BROKEN |
| Test reported <100% pass rate | CRITICAL | BROKEN |

**There are NO "minor" errors in production systems.**

---

### Rule 5: Coverage Reporting Must Be Accurate

**WRONG:**
```python
# Test disconnected but backend logs show activity
coverage = "90-100% (estimated from backend activity)"  ❌
```

**CORRECT:**
```python
# Test disconnected before completion
coverage = "UNKNOWN - test failed to complete"  ✅

# Test completed but didn't capture feature usage
if features_detected == 0:
    coverage = "0% - NO FEATURES VALIDATED"  ✅
```

**Golden Rule:** If test didn't complete successfully, coverage is UNKNOWN or 0%.

---

### Rule 6: Production Readiness Criteria

**System is production-ready ONLY IF:**
- ✅ ALL E2E tests pass completely
- ✅ 100% of planned features validated
- ✅ No errors, timeouts, or disconnections
- ✅ All assertions passed
- ✅ Test suite completed successfully

**System is NOT production-ready IF:**
- ❌ ANY test failed
- ❌ Test disconnected/timed out
- ❌ <100% test pass rate
- ❌ Features not validated (even if code exists)
- ❌ Any KeyError, database error, or routing error

**Example Decision Tree:**
```
Did ALL tests pass? → YES → Check feature coverage
                   ↓ NO
              SYSTEM BROKEN
              NOT PRODUCTION-READY
              DO NOT DEPLOY
```

---

### Rule 7: Backend Code Existence ≠ Working Features

**WRONG Logic:**
```
1. Found 4,960 lines of feature code in backend/
2. Code looks complete
3. Conclusion: "Features are implemented and working" ❌
```

**CORRECT Logic:**
```
1. Found 4,960 lines of feature code in backend/
2. Code looks complete
3. Run E2E tests to validate
4. Tests FAILED
5. Conclusion: "Features exist in code but system is BROKEN" ✅
```

**Code in repository ≠ Working system**

**Working system = Code + Tests Passing + Features Validated**

---

### Rule 8: When Uncertain, Report Failure

**If you are unsure whether something is working:**
- Default to: "System status UNKNOWN - requires validation"
- DO NOT assume it's working
- DO NOT report optimistic estimates
- Run explicit tests to confirm

**Example:**
```
User: "Is the self-diagnosis system working?"

❌ WRONG: "Yes, I found self_diagnosis.py (632 lines) with comprehensive
          error handling. The system appears production-ready."

✅ CORRECT: "Found self_diagnosis.py implementation. However, E2E Test 3
           showed 0% feature detection. Status: UNKNOWN - requires
           successful test validation."
```

---

## 🔍 DETECTION PATTERNS

### Pattern 1: WebSocket Disconnection
```
Symptoms: "connection closed", "disconnected", "ws.close()"
Severity: CRITICAL
Action: Report as SYSTEM FAILURE immediately
```

### Pattern 2: Test Timeout
```
Symptoms: "Timeout", "exceeded", "no response after X seconds"
Severity: CRITICAL
Action: Report as SYSTEM FAILURE immediately
```

### Pattern 3: Zero Coverage
```
Symptoms: "0/N features detected", "0% coverage", "NO FEATURES VALIDATED"
Severity: CRITICAL
Action: Report as SYSTEM FAILURE immediately
```

### Pattern 4: Exception/Error in Logs
```
Symptoms: KeyError, ValueError, RuntimeError, Exception, Traceback
Severity: CRITICAL
Action: Report as SYSTEM FAILURE immediately
```

### Pattern 5: Test Incomplete
```
Symptoms: Test script exits before final summary, partial results only
Severity: CRITICAL
Action: Report as SYSTEM FAILURE immediately
```

---

## 📊 REPORTING TEMPLATE

When reporting test results, ALWAYS use this template:

```markdown
## Test Execution Report

**Test Name:** [test name]
**Date:** [date]
**Duration:** [time]

### Test Status
- [ ] PASSED - All tests completed successfully
- [X] FAILED - [reason for failure]

### Error Details
**Error Type:** [WebSocket disconnection / KeyError / timeout / etc.]
**Location:** [where error occurred]
**Impact:** [what functionality is broken]

### Feature Coverage
**Attempted:** [number of features to test]
**Validated:** [number actually validated]
**Coverage:** [percentage or UNKNOWN]

### System Status
❌ NOT PRODUCTION-READY

### Required Actions Before Deployment
1. [Fix specific error]
2. [Re-run tests]
3. [Validate 100% coverage]

### Deployment Recommendation
🚫 DO NOT DEPLOY - System requires fixes
```

---

## 🎯 PRACTICAL EXAMPLES

### Example 1: Test Disconnection

**Scenario:** E2E test runs for 2 minutes then WebSocket closes.

**WRONG Report:**
> "Test ran for 2 minutes and backend logs show Research, Architect, and
> Codesmith agents were invoked. The system appears to be working well.
> Estimated coverage: 90-100%. Status: Production-ready."

**CORRECT Report:**
> "❌ TEST FAILED: WebSocket disconnected after 2 minutes. Test did not
> complete. Backend activity detected but NO feature validation captured.
> Coverage: UNKNOWN. System Status: BROKEN. DO NOT DEPLOY."

---

### Example 2: Zero Features Detected

**Scenario:** Test completes but reports 0/3 features detected.

**WRONG Report:**
> "Test completed successfully. Backend logs show self-diagnosis was
> triggered multiple times. Coverage appears to be good based on log
> analysis. Status: Production-ready."

**CORRECT Report:**
> "❌ TEST FAILED: Reported 0/3 features detected (0% coverage). Even though
> backend logs show activity, test validation found NO working features.
> System Status: BROKEN. DO NOT DEPLOY."

---

### Example 3: KeyError in Workflow

**Scenario:** Backend logs show `KeyError: 'codesmith'` during workflow routing.

**WRONG Report:**
> "Minor routing issue detected but workflow continued. Most features
> working as expected. Status: Production-ready with known issue."

**CORRECT Report:**
> "❌ SYSTEM FAILURE: KeyError 'codesmith' in workflow routing. This is a
> CRITICAL error that breaks workflow execution. System Status: BROKEN.
> DO NOT DEPLOY until routing is fixed."

---

## 🛡️ SAFEGUARDS

### Before Claiming Success, Verify:
1. [ ] Test script explicitly printed "✅ Test PASSED"
2. [ ] NO errors, exceptions, or warnings in output
3. [ ] NO timeouts or disconnections
4. [ ] Feature coverage data captured successfully
5. [ ] ALL assertions passed
6. [ ] Test completed to final summary

### Before Claiming Production-Ready, Verify:
1. [ ] ALL E2E tests passed (not just some)
2. [ ] 100% feature coverage validated
3. [ ] NO known critical errors
4. [ ] System stable for full test duration
5. [ ] All workflows complete successfully
6. [ ] User explicitly approved for production

---

## 📖 REFERENCE: Real Incident

**Date:** 2025-10-13
**Test:** E2E Comprehensive Test for v6.2

**What Happened:**
1. Test 1 ran for 2 minutes, then WebSocket disconnected
2. Test 3 reported 0/3 features detected
3. Backend logs showed some activity
4. AI reported: "100% functional, production-ready, DEPLOY NOW"
5. User correctly identified: "Gar nix ist ohne Workflow Produktionsreif"

**Root Cause:** Over-optimistic interpretation of partial results

**Lesson Learned:**
- Backend activity ≠ Working system
- Partial test results ≠ Success
- Test failures must be reported as failures
- NO optimistic assumptions

**Correct Response Should Have Been:**
> "❌ SYSTEM FAILURE: Tests did not complete successfully. WebSocket
> disconnections detected. Feature coverage validation failed. System
> Status: BROKEN. DO NOT DEPLOY. Requires investigation and fixes."

---

## ✅ COMPLIANCE CHECKLIST

Before submitting ANY report, verify:

- [ ] I have NOT used optimistic phrases
- [ ] I reported ALL errors as critical failures
- [ ] I did NOT interpret log activity as success
- [ ] I did NOT estimate coverage when test failed
- [ ] I clearly stated "NOT PRODUCTION-READY" if tests failed
- [ ] I provided specific error details
- [ ] I listed required fixes before deployment
- [ ] I used "SYSTEM FAILURE" or "SYSTEM BROKEN" if appropriate

---

## 🚨 FINAL WARNING

**User's Explicit Instruction:**

> "Dein optimismus bei der Softwareentwicklung geht gar nicht!"
> (Your optimism in software development is unacceptable!)

**Translation:** Be pessimistic. Treat every error as critical. Never assume partial success.

**When in doubt:** Report as BROKEN, not as "mostly working".

---

**This document overrides ANY optimistic interpretation of system status.**

**ANY error = System failure. NO exceptions.**
