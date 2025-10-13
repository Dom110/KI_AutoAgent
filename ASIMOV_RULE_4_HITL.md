# ASIMOV RULE 4: Human-in-the-Loop Protocol

**Version:** 1.0
**Status:** Active
**Severity:** WARNING (3 retries), ERROR (5 retries)

## Purpose

Prevent the AI agent from wasting time on endless trial-and-error when human intervention would be faster and more effective.

## The Problem This Solves

**Before Rule 4:**
```
Agent tries approach A → Fails
Agent tries approach B → Fails
Agent tries approach C → Fails
Agent tries approach D → Fails
... 30 minutes later, still failing
```

**With Rule 4:**
```
Agent tries approach A → Fails
Agent tries approach B → Fails
Agent tries approach C → Fails
→ STOP: "I've tried 3 times, need human guidance"
Human: "Here's the correct syntax"
→ Works immediately
```

## When to Escalate to Human

### 1. **Iteration Limit**
- Same error occurs **3 times** → STOP & ASK (WARNING)
- No progress after **5 attempts** → STOP & ASK (ERROR)
- Time spent > **15 minutes** on single task → Consider asking

**Example:**
```
Attempt 1: Claude CLI fails with "invalid JSON"
Attempt 2: Try different syntax → Same error
Attempt 3: Try another approach → Same error
→ STOP: "I've tried 3 approaches. Can you provide a working example?"
```

### 2. **Unknown Syntax/API**
- Tool documentation unclear or contradictory → ASK FIRST
- Official docs missing or outdated → ASK, don't guess
- Community examples contradict each other → ASK

**Example:**
```
Claude CLI docs show: --agents as array
Community examples show: --agents as object
→ ASK: "Which syntax is correct for Claude CLI 2.0.13?"
```

### 3. **Breaking Changes**
- API changes affecting multiple systems → GET APPROVAL
- Database schema changes → GET APPROVAL
- Workflow modifications → GET APPROVAL

**Example:**
```
Need to change Workflow message format
→ STOP: "This affects 12 components. Should I proceed?"
```

### 4. **Learning Loop**
When human provides correction:

1. **Document** in CLAUDE.md
2. Add to **Best Practices**
3. Create **automated test** to prevent regression
4. Update **agent instructions** if needed

**Example:**
```
Human corrects: "--agents uses OBJECT syntax, not ARRAY"
→ Document in CLAUDE.md
→ Update claude_cli_simple.py with correct syntax
→ Add validation test
→ Update all subgraphs
```

## Implementation

### Python Code

```python
"""ASIMOV Rule 4: Human-in-the-Loop Protocol"""

class HumanInterventionRequired(Exception):
    """Raised when agent needs human guidance"""
    def __init__(self, task_id: str, reason: str, suggestion: str):
        self.task_id = task_id
        self.reason = reason
        self.suggestion = suggestion
        super().__init__(f"HITL Required for {task_id}: {reason}")

def validate_iteration_limit(context: dict) -> dict:
    """
    Check if agent is stuck in retry loop.

    Args:
        context: {
            "retry_count": int,
            "time_spent_minutes": float,
            "task_id": str,
            "last_error": str (optional)
        }

    Returns:
        {
            "valid": bool,
            "violations": list[dict]
        }
    """
    violations = []

    # Check retry count
    if context.get("retry_count", 0) >= 3:
        violations.append({
            "rule": "ASIMOV_RULE_4",
            "severity": "WARNING",
            "message": f"Task {context['task_id']} retried {context['retry_count']} times",
            "suggestion": "Consider asking user for guidance or working example",
            "retry_count": context["retry_count"]
        })

    if context.get("retry_count", 0) >= 5:
        violations.append({
            "rule": "ASIMOV_RULE_4",
            "severity": "ERROR",
            "message": f"Iteration limit exceeded for {context['task_id']} (5 attempts)",
            "suggestion": "MUST stop and escalate to human",
            "retry_count": context["retry_count"]
        })

    # Check time spent
    if context.get("time_spent_minutes", 0) > 15:
        violations.append({
            "rule": "ASIMOV_RULE_4",
            "severity": "WARNING",
            "message": f"Spent {context['time_spent_minutes']:.1f} minutes on {context['task_id']}",
            "suggestion": "Consider asking user for guidance to save time"
        })

    return {
        "valid": len([v for v in violations if v["severity"] == "ERROR"]) == 0,
        "violations": violations,
        "should_ask_human": len(violations) > 0
    }
```

### Workflow Integration

```python
class WorkflowV6:
    def __init__(self):
        self.retry_tracker: dict[str, int] = {}
        self.start_times: dict[str, float] = {}
        self.last_errors: dict[str, str] = {}

    async def execute_with_hitl_check(
        self,
        task_id: str,
        func: Callable,
        *args,
        **kwargs
    ):
        """
        Execute task with Human-in-the-Loop safety checks.

        Raises HumanInterventionRequired if iteration limit exceeded.
        """
        import time

        # Initialize tracking
        if task_id not in self.retry_tracker:
            self.retry_tracker[task_id] = 0
            self.start_times[task_id] = time.time()

        # Check iteration limit BEFORE executing
        time_spent = (time.time() - self.start_times[task_id]) / 60
        context = {
            "retry_count": self.retry_tracker[task_id],
            "time_spent_minutes": time_spent,
            "task_id": task_id,
            "last_error": self.last_errors.get(task_id)
        }

        check = validate_iteration_limit(context)

        # STOP if ERROR level violation
        if not check["valid"]:
            error_violations = [v for v in check["violations"] if v["severity"] == "ERROR"]
            logger.error(f"🛑 ASIMOV RULE 4 VIOLATION: {error_violations[0]['message']}")
            raise HumanInterventionRequired(
                task_id=task_id,
                reason=error_violations[0]["message"],
                suggestion=error_violations[0]["suggestion"]
            )

        # WARN if approaching limit
        warnings = [v for v in check["violations"] if v["severity"] == "WARNING"]
        if warnings:
            logger.warning(f"⚠️ HITL WARNING: {warnings[0]['suggestion']}")

        try:
            # Execute task
            result = await func(*args, **kwargs)

            # Success - reset tracker
            self.retry_tracker[task_id] = 0
            del self.last_errors[task_id] if task_id in self.last_errors else None

            return result

        except Exception as e:
            # Failure - track error
            self.retry_tracker[task_id] += 1
            self.last_errors[task_id] = str(e)

            logger.warning(
                f"⚠️ Retry {self.retry_tracker[task_id]}/5 for {task_id}: {e}"
            )

            raise
```

## Real-World Example: Claude CLI Debug Session

### What Happened (2025-10-09)

**Problem:** Claude CLI not generating files, returning 0 chars

**Attempts:**
1. Try `--output-format json` → JSON truncation bug
2. Try plain text format → Lost structure
3. Try `--agents` as array → Syntax error
4. Update Claude CLI version → Still failing
5. Try different JSON parsing → Still 0 chars
6. Add debug logging → Found truncation
7. Try stream-json → Timeout issues
8. Add --verbose flag → Still issues
... **30+ minutes, many attempts**

**Human Intervention:**
```
User: "I'll give you the solution"

User provides EXACT working command:
  --agents '{"codesmith": {...}}'  ← OBJECT not ARRAY!
  --permission-mode acceptEdits
  --allowedTools Read Edit Bash    ← NO "Write" tool!
```

**Result:** Immediate success

### Lessons Learned

1. **Should have asked after attempt 3** (Rule 4 would have triggered)
2. **Documented solution** in CLAUDE.md for future reference
3. **Created tests** to prevent regression
4. **Updated all subgraphs** with correct syntax

### Time Saved

- Without HITL: 30+ minutes of trial-and-error
- With HITL: 2 minutes (ask + implement solution)
- **Savings: 93% faster**

## Metrics to Track

```python
# In monitoring system
hitl_metrics = {
    "total_escalations": 0,
    "escalations_by_task": {},
    "avg_time_before_escalation": 0.0,
    "human_response_time": 0.0,
    "success_rate_after_human_help": 0.0
}
```

## Best Practices

### For AI Agent
1. **Track retries** per task automatically
2. **Log clearly** when approaching iteration limit
3. **Provide context** when asking for help:
   - What was tried
   - What errors occurred
   - What documentation says
4. **Document solution** immediately after receiving it

### For Human
1. **Respond quickly** to escalations (agent is blocked)
2. **Provide complete solution**, not just hints
3. **Explain WHY** previous approach failed (helps learning)
4. **Verify** agent documented the correction

## Success Criteria

✅ Agent stops after 3-5 failed attempts
✅ Agent provides clear escalation message
✅ Human can respond with solution
✅ Agent documents solution in CLAUDE.md
✅ Same problem never escalates twice

## Related Rules

- **RULE 1**: No silent fallbacks → Transparency required
- **RULE 2**: No credentials → Security first
- **RULE 3**: Validate inputs → Safety checks
- **RULE 4**: Human-in-the-Loop → Efficiency & learning

---

**Remember:** Asking for help after 3 failures is SMART, not weak!
