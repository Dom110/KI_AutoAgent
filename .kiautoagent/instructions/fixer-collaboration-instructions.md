# FixerBot Collaboration Instructions

## Purpose
FixerBot receives code with identified issues from ReviewerGPT and implements fixes. After fixing, code should be reviewed again to verify the fix.

## Collaboration Flow

### 1. Receiving Fix Request
FixerBot is invoked when:
- ReviewerGPT finds critical issues
- Orchestrator creates new step: `suggested_agent=fixer`
- Task contains: Issue description from review

**Input Context:**
```python
{
    "step_id": <step_number>,
    "previous_step_result": "<review_result>",
    "implementation": "<original_code>",
    "workspace_path": "/path/to/workspace"
}
```

### 2. Fix Execution

**Process:**
1. Parse review result to identify issues
2. Locate problematic code
3. Implement fixes
4. Run tests if available
5. Verify fix resolves the issue

**Focus Areas:**
- Security vulnerabilities → Use secure alternatives
- Bugs → Fix logic errors
- Performance issues → Optimize code
- Quality issues → Refactor

### 3. Fix Verification

After implementing fix:
```python
# Option 1: Request re-review (recommended)
state["needs_replan"] = True
state["suggested_agent"] = "reviewer"
state["suggested_query"] = "Re-review the fixed code to verify all issues are resolved"

# Option 2: Mark as complete (if confident)
current_step.status = "completed"
```

### 4. Fix Output Format
```markdown
## Fix Summary

### Issues Fixed
1. [Issue description]
   - Original problem: [description]
   - Fix applied: [what was changed]
   - Verification: [how it was tested]

### Changes Made
- File: [filename]
  - Lines modified: [line numbers]
  - Change: [description]

### Testing
- [Test results or verification steps]
```

## Workflow Pattern
```
Reviewer → Orchestrator → FixerBot → [Fixed?] → Reviewer → [Verified?] → END
                                         ↓
                                    [More fixes needed] → FixerBot
```

## Examples

### Example 1: SQL Injection Fix
**Input:**
```
Critical security vulnerability: SQL injection in user login
Location: api/auth.py:45
Current: query = f"SELECT * FROM users WHERE username='{username}'"
```

**Fix:**
```python
# Before
query = f"SELECT * FROM users WHERE username='{username}'"

# After
query = "SELECT * FROM users WHERE username=?"
cursor.execute(query, (username,))
```

**Output:**
```markdown
## Fix Summary
- Fixed SQL injection vulnerability
- Changed to parameterized query
- Tested with various inputs including SQL injection attempts
- Request re-review to verify fix
```

### Example 2: Logic Bug Fix
**Input:**
```
Bug found: Off-by-one error in loop iteration
Location: utils/data.py:23
Issue: Loop terminates one iteration early
```

**Fix:**
```python
# Before
for i in range(len(items) - 1):  # Bug: stops one early

# After
for i in range(len(items)):  # Fixed: iterates all items
```

## Implementation Details

### Detection of Fix Request
FixerBot node receives:
```python
current_step.task = "Fix the issues found in code review: [review summary]"
context["previous_step_result"] = <review_result>
context["implementation"] = <code_to_fix>
```

### Requesting Re-Review
```python
# After fixing
state["needs_replan"] = True
state["suggested_agent"] = "reviewer"
state["suggested_query"] = f"Re-review the code after fixing: {issue_summary}"
```

### Orchestrator Response
1. Receives `needs_replan=True` from FixerBot
2. Creates new ExecutionStep for Reviewer
3. Routes back to Reviewer for verification
4. Cycle continues until no issues found

## Best Practices

1. **Understand First**: Parse review to understand all issues
2. **Fix Completely**: Don't leave partial fixes
3. **Test Changes**: Verify fixes work
4. **Document**: Explain what was changed and why
5. **Request Review**: Always ask for re-review of critical fixes

## Testing

Test scenarios:
1. Fix SQL injection → Request re-review → Reviewer verifies → END
2. Fix multiple bugs → Request re-review → Reviewer finds one more → Fix again
3. Fix performance issue → Verify with metrics → Complete

## Error Handling

If fix fails:
```python
current_step.status = "failed"
current_step.error = "Unable to fix: [reason]"
# Don't set needs_replan - let workflow handle failure
```

## Integration with Real Agent

The real FixerBot agent (`backend/agents/specialized/fixerbot_agent.py`) should:
- Parse review context from `context["previous_step_result"]`
- Identify files to modify
- Use file_tools to read, edit, write
- Return comprehensive fix summary
