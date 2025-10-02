# ReviewerGPT Collaboration Instructions

## Purpose
ReviewerGPT analyzes code for bugs, security issues, and quality problems. When critical issues are found, it triggers collaboration with FixerBot.

## Collaboration Flow

### 1. Review Execution
- Receive code from CodeSmith or other sources
- Perform comprehensive analysis:
  - Security vulnerabilities
  - Bugs and logic errors
  - Performance issues
  - Code quality problems

### 2. Issue Classification
**Critical Issues** (trigger FixerBot):
- Security vulnerabilities
- Critical bugs
- Data corruption risks
- Logic errors
- Race conditions

**Non-Critical Issues** (document only):
- Style suggestions
- Minor optimizations
- Naming conventions
- Documentation gaps

### 3. Triggering Collaboration
When **critical issues** are found:

**State Updates:**
```python
state["needs_replan"] = True
state["suggested_agent"] = "fixer"
state["suggested_query"] = "Fix the issues found in code review: [issue summary]"
```

**Keywords that Trigger Collaboration:**
- "critical"
- "bug"
- "error"
- "vulnerability"
- "security issue"
- "fix needed"
- "must fix"
- "requires fix"

### 4. Review Output Format
```markdown
## Code Review Results

### Critical Issues ⚠️
1. [Issue description]
   - Severity: Critical
   - Location: [file:line]
   - Fix needed: [what needs to be done]

### Non-Critical Suggestions
1. [Suggestion]
   - Severity: Low
   - Recommended: [improvement]
```

## Workflow Pattern
```
CodeSmith → Reviewer → [Issues Found?] → Orchestrator → FixerBot → Reviewer
                ↓
            [No Issues] → END
```

## Examples

### Example 1: Security Issue Found
**Review Result:**
```
Critical security vulnerability found: SQL injection risk in user input handling.
Location: api/users.py:45
Fix needed: Use parameterized queries instead of string concatenation
```
→ Triggers: `needs_replan=True`, `suggested_agent=fixer`

### Example 2: No Critical Issues
**Review Result:**
```
Code quality is good. Minor suggestions:
- Consider adding more comments
- Variable naming could be improved
```
→ No collaboration triggered, workflow continues

## Implementation Details

### Detection Logic (in workflow.py)
```python
review_text = str(review_result).lower()
has_critical_issues = any(keyword in review_text for keyword in [
    "critical", "bug", "error", "vulnerability", "security issue",
    "fix needed", "must fix", "requires fix", "issue found"
])

if has_critical_issues:
    state["needs_replan"] = True
    state["suggested_agent"] = "fixer"
```

### Orchestrator Response
1. Receives `needs_replan=True` signal
2. Creates new ExecutionStep for FixerBot
3. Passes issue summary to FixerBot
4. Routes workflow to FixerBot

## Best Practices

1. **Be Specific**: Clearly describe what needs to be fixed
2. **Include Location**: File and line numbers when possible
3. **Explain Impact**: Why is this critical?
4. **Suggest Solution**: Give direction for the fix

## Testing

Test with code containing:
- SQL injection vulnerability → Should trigger fixer
- XSS vulnerability → Should trigger fixer
- Logic bug → Should trigger fixer
- Style issue only → Should NOT trigger fixer
