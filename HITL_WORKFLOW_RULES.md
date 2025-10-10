# Human-in-the-Loop (HITL) Workflow Rules for KI AutoAgent

**Date:** 2025-10-10
**Based on:** Systematic debugging session with User
**Purpose:** Define optimal collaboration patterns between Human and AI Agent

---

## 📋 TABLE OF CONTENTS

1. [Version Strategy (v6 vs v6_1)](#version-strategy)
2. [HITL Interaction Patterns](#hitl-interaction-patterns)
3. [Autonomous Mode Rules](#autonomous-mode-rules)
4. [Debug Output Strategy](#debug-output-strategy)
5. [Problem Escalation](#problem-escalation)
6. [Documentation Requirements](#documentation-requirements)
7. [Testing Protocol](#testing-protocol)
8. [Communication Protocol](#communication-protocol)

---

## 1. VERSION STRATEGY (v6 vs v6_1)

### Why We Have Multiple Versions

**Problem:**
```python
# v6.0 - Original
from langchain_anthropic import ChatAnthropic  # BROKEN: Pydantic conflicts

# v6.1 - Fixed
from adapters.claude_cli_simple import ClaudeCLISimple as ChatAnthropic  # WORKS!
```

**Strategy:**

| Version | Purpose | When to Use |
|---------|---------|-------------|
| **v6** | Original implementation | Reference, comparison, fallback |
| **v6_1** | Refactored for Claude CLI | Production, current development |

**Rules:**
- ✅ **KEEP both versions** during transition period
- ✅ **Document differences** at top of v6_1 files
- ✅ **Mark v6 as deprecated** once v6_1 is stable
- ✅ **Delete v6** only after full v6_1 validation

**Template for v6_1 files:**
```python
"""
<Component> v6.1 - Custom Node Implementation

This is a refactored version that uses direct LLM calls
instead of create_react_agent.

Changes from v6.0:
- Direct LLM.ainvoke() calls (no create_react_agent)
- Manual file operations instead of tool-calling agent
- Works with ClaudeCLISimple adapter
- [Agent-specific changes]

Author: KI AutoAgent Team
Python: 3.13+
"""
```

---

## 2. HITL INTERACTION PATTERNS

### Pattern 1: "ULTRATHINK THROUGH THIS STEP BY STEP"

**User Signal:** Requests systematic, methodical analysis

**Agent Response:**
```
✅ DO:
- Break problem into clear steps
- Number each step explicitly
- Show reasoning at each step
- Document assumptions
- Create TODO list for complex tasks

❌ DON'T:
- Jump to conclusions
- Skip explanation steps
- Assume context
```

**Example from Session:**
```
User: "ULTRATHINK THROUGH THIS STEP BY STEP: Why timeout?"

Agent:
1. Check if command itself works (manual bash test)
2. Check if subprocess config is correct
3. Compare working vs failing configurations
4. Identify exact difference
5. Apply fix and verify
```

---

### Pattern 2: Autonomous Mode

**User Signal:** "Ich bin erstmal nicht da jetzt" (I'm away now)

**Agent Behavior:**

```python
AUTONOMOUS_MODE_RULES = {
    "work_continuously": True,
    "skip_blocking_issues": True,
    "document_everything": True,
    "create_summaries": True,
    "prepare_report": True
}
```

**DO in Autonomous Mode:**
- ✅ Test each component independently
- ✅ Document successes AND failures
- ✅ Skip issues that would require human input
- ✅ Mark skipped items with reason
- ✅ Create comprehensive summary for user return
- ✅ Save all outputs for later review

**DON'T in Autonomous Mode:**
- ❌ Wait for confirmation
- ❌ Ask clarifying questions
- ❌ Stop at first failure
- ❌ Delete failed code (mark it instead)

**Session Example:**
```
User: "Mach erstmal alles was geht. Wenn was nicht geht, lass es und
       mach die nächste Funktion ohne Unterbrechung."

Agent Actions:
✅ Test 1: Research subgraph → SUCCESS
✅ Test 2: Codesmith subgraph → SUCCESS
✅ Test 3: ReviewFix subgraph → SUCCESS
⏸️ Test 4: E2E workflow → SKIP (timeout >320s, needs profiling)
✅ Created: TEST_RESULTS_2025-10-10.md
✅ Created: Complete summary for user
```

---

### Pattern 3: "Zeig mir den Output" (Show me the output)

**User Signal:** User returns and wants to help debug

**Agent Response:**

```
✅ PROVIDE IMMEDIATELY:
- Exact command executed
- Complete output (not truncated)
- Error messages (full stack trace)
- Configuration used
- Environment variables
- File paths involved
- Timing information
```

**Format:**
```markdown
## Command Executed
```bash
claude --model ... --agents '...' -p "..."
```

## Output Received
```
[FULL OUTPUT HERE - NO TRUNCATION]
```

## Environment
- Model: claude-sonnet-4-20250514
- Timeout: 40s
- Tools: ["Read", "Bash"]
- Permission Mode: acceptEdits

## Result
❌ TIMEOUT after 20s
```

**Session Example:**
```
User: "zeig mit den genauen cli aufruf und die Streaming responses einzeln."

Agent: [Shows EXACT command + ALL 3 JSONL events + timing]
User: [Can now see the issue and help]
```

---

## 3. AUTONOMOUS MODE RULES

### When User is Away

**Detection Signals:**
- "Ich bin erstmal nicht da"
- "Mach alles was geht"
- "Ohne Unterbrechung"
- No response for >5 minutes in active session

**Agent Protocol:**

```python
class AutonomousMode:
    def __init__(self):
        self.tasks = []
        self.completed = []
        self.skipped = []
        self.blocked = []

    def execute(self):
        for task in self.tasks:
            try:
                result = self.attempt(task, timeout=SHORT)

                if result.success:
                    self.completed.append({
                        "task": task,
                        "result": result,
                        "duration": result.duration
                    })
                else:
                    # Don't block! Skip and continue
                    self.skipped.append({
                        "task": task,
                        "reason": result.error,
                        "recommendation": self.suggest_fix(result)
                    })

            except Exception as e:
                # Log but continue
                self.blocked.append({
                    "task": task,
                    "error": str(e),
                    "needs_human": True
                })

        # Generate report
        self.create_summary()
```

**Task Prioritization:**

```
Priority 1: Individual components (fast, independent)
Priority 2: Integration tests (slow, dependencies)
Priority 3: Documentation (always possible)
Priority 4: Cleanup/refactoring (nice-to-have)
```

**Session Example:**
```
Attempted Tasks:
1. ✅ DEBUG_OUTPUT variable       → 5 min  → SUCCESS
2. ✅ Test Research subgraph      → 25s    → SUCCESS
3. ✅ Test Codesmith subgraph     → 30s    → SUCCESS
4. ✅ Test ReviewFix subgraph     → 20s    → SUCCESS
5. ⏸️ Test E2E workflow           → >320s  → SKIP (too slow)
6. ✅ Create documentation        → 10 min → SUCCESS

Result: 5/6 completed, 1 deferred with reason
```

---

## 4. DEBUG OUTPUT STRATEGY

### The Problem

**Before:**
```python
# Hard-coded print() everywhere
print("🚀 EXECUTING CLAUDE CLI")
print(f"Command parts: {cmd}")
print(f"⏳ Starting subprocess...")
```

**Production Problem:**
- ❌ Can't disable output
- ❌ Clutters production logs
- ❌ No granularity control

### The Solution

**After:**
```python
# DEBUG_OUTPUT flag at top of file
DEBUG_OUTPUT = True  # Set to False in production

# Conditional output
if DEBUG_OUTPUT:
    print("🚀 EXECUTING CLAUDE CLI")
    print(f"Command parts: {cmd}")
```

### Rules for Debug Output

**DO:**
- ✅ **Single global flag** per module: `DEBUG_OUTPUT = True`
- ✅ **Top of file** for easy toggling
- ✅ **Wrap ALL print()** statements (except critical errors)
- ✅ **Use logger** for production messages
- ✅ **Keep output information** (don't delete!)

**DON'T:**
- ❌ Delete debug print() statements
- ❌ Multiple flags per file
- ❌ Hard to find flag location
- ❌ Mix debug and production logging

**Session Example:**
```python
# User Request: "Lass Debug output drin. mach dafür lieber eine
#                Variable, wenn die true ist wird development
#                output ausgegeben."

# Agent Implementation:
DEBUG_OUTPUT = True  # Line 35

if DEBUG_OUTPUT:
    print("🚀 EXECUTING CLAUDE CLI")  # Line 239
    print(f"Command parts:")           # Line 242

# Result: Easy to disable in production with one line change
```

---

## 5. PROBLEM ESCALATION

### When to Continue vs When to Stop

**CONTINUE (Don't block!):**
- ✅ Test fails but other tests can run
- ✅ Slow operation (>60s) but not critical path
- ✅ Missing feature but workaround exists
- ✅ Non-critical error with fallback

**STOP (Ask for help!):**
- ❌ Critical system broken (no workaround)
- ❌ Data corruption risk
- ❌ Security issue
- ❌ Unclear requirements (ambiguous task)

**Escalation Template:**

```markdown
## ⚠️ ISSUE DETECTED - NEEDS HUMAN INPUT

**Problem:** E2E workflow times out after 320s

**What I tried:**
1. Increased timeout to 320s → Still timeout
2. Tested individual subgraphs → All work (<60s)
3. Checked logs → No specific error

**Analysis:**
- Individual components: ✅ Working
- Integration: ❌ Too slow
- Root cause: Likely sequential initialization of v6 systems

**Recommendation:**
- ⏸️ DEFER E2E test (not blocking)
- ✅ CONTINUE with other tasks
- 📋 TODO: Profile workflow to find bottleneck

**User Action Needed:**
- [ ] Confirm defer strategy
- [ ] OR: Provide profiling approach
```

**Session Example:**
```
Issue: E2E workflow >320s timeout

Agent Decision:
⏸️ DEFER (not blocking)
✅ Document in TEST_RESULTS_2025-10-10.md
✅ Continue with feature implementation
✅ Create TODO for next session

Result: User confirmed this was correct approach
```

---

## 6. DOCUMENTATION REQUIREMENTS

### What to Document

**ALWAYS document:**
- ✅ **All fixes applied** (what, why, where)
- ✅ **Test results** (success AND failures)
- ✅ **Configuration changes**
- ✅ **Performance metrics**
- ✅ **Issues encountered**
- ✅ **Decisions made** (especially skips/defers)
- ✅ **Next steps** (recommendations)

**Documentation Structure:**

```markdown
# [SESSION_NAME] - [DATE]

## ✅ COMPLETED SUCCESSFULLY
[List of achievements with details]

## 🔧 CRITICAL FIXES APPLIED
[Problem → Solution → Evidence]

## ⏸️ DEFERRED ITEMS
[What → Why → Recommendation]

## 📊 SYSTEM STATUS
[Component-by-component status table]

## 📈 PERFORMANCE METRICS
[Timing data, success rates]

## 🎯 RECOMMENDATIONS
[Immediate, Short-term, Medium-term]

## 📝 FILES MODIFIED
[Complete list with change descriptions]
```

**Session Example:**
Created 3 documentation files:
1. `TEST_RESULTS_2025-10-10.md` - Complete session summary
2. `CLAUDE_BEST_PRACTICES.md` - Lessons learned
3. `CLAUDE.md` - Updated with CLI guide

Total: ~500 lines of documentation for ~3 hours of work

---

## 7. TESTING PROTOCOL

### Systematic Testing Approach

**Step 1: Hypothesis**
```
Problem: Claude CLI timeouts with long prompts
Hypothesis: System prompt placement causes issue
```

**Step 2: Design Tests**
```python
configurations = [
    {"system": "in_agent", "tools": ["Read", "Bash"]},
    {"system": "in_p", "tools": ["Read", "Bash"]},
    {"system": "in_p", "tools": []},
    # ... 11 total configurations
]
```

**Step 3: Execute Systematically**
```
Test 1: baseline → TIMEOUT
Test 2: system_in_agent → TIMEOUT
Test 3: system_in_p → SUCCESS (24.4s)
Test 4: with_tools → SUCCESS (18.8s)
Test 5: without_tools → TIMEOUT
...
```

**Step 4: Identify Pattern**
```
✅ SUCCESS pattern:
- System prompt in -p parameter
- Non-empty tools array
- Include --verbose

❌ FAILURE pattern:
- System prompt ONLY in agent.prompt
- Empty tools array
- Missing --verbose
```

**Step 5: Apply Fix**
```python
# Implement successful pattern
combined_prompt = f"{system_prompt}\n\n{user_prompt}"
agent_tools = ["Read", "Bash"]  # Non-empty!
```

**Step 6: Verify**
```
Manual test: ✅ 13.5s
Python test: ✅ 16.7s
All subgraphs: ✅ Working
```

**Session Example:**
- 26 test configurations executed
- 3 test files created
- Pattern identified after 11 systematic tests
- Fix validated across 4 components
- 100% success rate after fix

---

## 8. COMMUNICATION PROTOCOL

### Agent-to-User Communication

**Status Updates Format:**

```
================================================================================
🎉 [MILESTONE] - [STATUS]
================================================================================

✅ SUCCESS:
- Item 1: Details
- Item 2: Details

⏸️ DEFERRED:
- Item 3: Reason

❌ FAILED:
- Item 4: Error + Next steps

📊 METRICS:
- Duration: Xs
- Files: N
- Tests: M passed, K failed

🎯 NEXT:
- Immediate action
- User decision needed
================================================================================
```

**Session Example:**
```
================================================================================
🎉 AUTONOMOUS WORK SESSION COMPLETE - 2025-10-10
================================================================================

TASK: Test all subgraphs + implement missing features (autonomous mode)

📊 RESULTS SUMMARY:
✅ Research Agent:  ~20-25s  → PASS
✅ Codesmith Agent: ~25-30s  → PASS
✅ ReviewFix Agent: ~15-20s  → PASS
⏸️ E2E Workflow:    >320s    → DEFERRED (needs profiling)

[... detailed breakdown ...]

📖 READ NEXT: TEST_RESULTS_2025-10-10.md (complete details)
================================================================================
```

### User-to-Agent Signals

**Recognized Patterns:**

| User Says | Agent Interprets | Response |
|-----------|------------------|----------|
| "ULTRATHINK THROUGH THIS" | Systematic analysis needed | Step-by-step breakdown |
| "Ich bin erstmal nicht da" | Autonomous mode | Continue without blocking |
| "Zeig mir den Output" | Debug mode | Show ALL details |
| "Wenn was nicht geht, lass es" | Skip failures | Document and continue |
| "Noch mal probieren" | Retry with adjustments | Repeat with debug output |
| "Warum...?" | Explain reasoning | Detailed explanation |

---

## 9. IMPLEMENTATION CHECKLIST

### For Implementing HITL in Code

**1. Mode Detection**
```python
class HITLMode(Enum):
    INTERACTIVE = "interactive"      # User present, ask questions
    AUTONOMOUS = "autonomous"        # User away, don't block
    DEBUG = "debug"                  # Show everything
    PRODUCTION = "production"        # Minimal output

def detect_mode(user_message: str) -> HITLMode:
    if "nicht da" in user_message.lower():
        return HITLMode.AUTONOMOUS
    if "zeig mir" in user_message.lower():
        return HITLMode.DEBUG
    return HITLMode.INTERACTIVE
```

**2. Task Management**
```python
class TaskManager:
    def __init__(self, mode: HITLMode):
        self.mode = mode
        self.tasks = []
        self.completed = []
        self.skipped = []

    async def execute_task(self, task):
        if self.mode == HITLMode.AUTONOMOUS:
            timeout = SHORT_TIMEOUT  # Don't wait forever
            skip_on_error = True
        else:
            timeout = LONG_TIMEOUT
            skip_on_error = False

        try:
            result = await task.run(timeout=timeout)
            self.completed.append((task, result))
            return result
        except TimeoutError:
            if skip_on_error:
                self.skipped.append((task, "Timeout"))
                return None
            else:
                raise
```

**3. Output Control**
```python
class OutputManager:
    DEBUG_OUTPUT = True  # Global flag

    @classmethod
    def debug(cls, message: str):
        if cls.DEBUG_OUTPUT:
            print(f"🔍 {message}")

    @classmethod
    def info(cls, message: str):
        # Always show important info
        print(f"ℹ️  {message}")

    @classmethod
    def error(cls, message: str):
        # Always show errors
        print(f"❌ {message}")
```

**4. Documentation Generator**
```python
class SessionDocumentor:
    def __init__(self):
        self.start_time = datetime.now()
        self.actions = []

    def add_action(self, action: str, result: str, duration: float):
        self.actions.append({
            "action": action,
            "result": result,
            "duration": duration,
            "timestamp": datetime.now()
        })

    def generate_report(self) -> str:
        total_duration = (datetime.now() - self.start_time).seconds

        return f"""
# Session Report - {self.start_time.strftime('%Y-%m-%d')}

## Summary
Duration: {total_duration}s
Actions: {len(self.actions)}
Success: {self.count_success()}
Failed: {self.count_failed()}

## Actions Taken
{self.format_actions()}

## Recommendations
{self.generate_recommendations()}
"""
```

---

## 10. REAL-WORLD EXAMPLES

### Example 1: Systematic Debugging

**Scenario:** Claude CLI timeouts with long prompts

**User Behavior:**
```
1. "ULTRATHINK THROUGH THIS STEP BY STEP"
2. Provides high-level task
3. Lets agent work autonomously
4. Returns for output: "zeig mir den output"
5. Provides insight when agent stuck
```

**Agent Behavior:**
```
1. ✅ Break into systematic tests (26 configs)
2. ✅ Test each independently
3. ✅ Document all results
4. ✅ Identify pattern
5. ✅ Apply fix
6. ✅ Verify across all components
7. ✅ Create comprehensive documentation
```

**Outcome:**
- ✅ Root cause identified
- ✅ Fix validated
- ✅ All components working
- ✅ Complete documentation

---

### Example 2: Autonomous Task Execution

**Scenario:** Test all subgraphs + implement features

**User Behavior:**
```
"Mach erstmal alles was geht. Wenn was nicht geht, lass es und
 mach die nächste Funktion ohne Unterbrechung. Ich bin erstmal
 nicht da jetzt."
```

**Agent Behavior:**
```
1. ✅ Create TODO list (5 tasks)
2. ✅ Execute tasks sequentially
3. ⏸️ Skip slow E2E test (>320s)
4. ✅ Continue with documentation
5. ✅ Create comprehensive summary
6. ✅ Prepare for user return
```

**Outcome:**
- ✅ 5/6 tasks completed
- ✅ 1 deferred with clear reason
- ✅ User can review and decide
- ✅ No time wasted waiting

---

### Example 3: Debug Output Management

**Scenario:** Clean up production logs

**User Behavior:**
```
"Lass Debug output drin. mach dafür lieber eine Variable,
 wenn die true ist wird development output ausgegeben."
```

**Agent Behavior:**
```
1. ✅ Add DEBUG_OUTPUT = True at top
2. ✅ Wrap ALL print() with if DEBUG_OUTPUT:
3. ✅ Keep information intact
4. ✅ Test that it works
5. ✅ Document in code
```

**Outcome:**
- ✅ Production-ready debug management
- ✅ Easy to toggle (one line)
- ✅ No information lost
- ✅ Clean production logs possible

---

## 11. KEY PRINCIPLES

### The Golden Rules

1. **Autonomy with Accountability**
   - Work independently when possible
   - Document everything for later review
   - Prepare detailed reports for user return

2. **Don't Block, Document**
   - If stuck, mark and continue
   - Explain WHY skipped
   - Provide recommendations for later

3. **Output on Demand**
   - User says "zeig mir" → show EVERYTHING
   - No truncation in debug mode
   - Full context for troubleshooting

4. **Systematic over Random**
   - Test multiple configurations
   - Document patterns
   - Apply evidence-based fixes

5. **Preserve Knowledge**
   - Don't delete debug code
   - Make it toggleable instead
   - Future debugging will thank you

6. **Clear Communication**
   - Use emojis for visual parsing (✅❌⏸️)
   - Structure output consistently
   - Separate concerns (success/failure/defer)

7. **Trust but Verify**
   - User provides direction (what)
   - Agent provides implementation (how)
   - Both verify results (test)

---

## 12. ANTI-PATTERNS TO AVOID

### What NOT to Do

**❌ Waiting for Perfect**
```
Bad: "I need clarification on X, Y, Z before I can start"
Good: "Starting with best guess, will adjust based on results"
```

**❌ Blocking on Non-Critical Issues**
```
Bad: "E2E test fails, stopping all work"
Good: "E2E test fails, documenting and continuing with unit tests"
```

**❌ Hiding Failures**
```
Bad: "Some tests failed but overall success"
Good: "4/6 tests passed, 1 failed, 1 deferred - see details"
```

**❌ Deleting Debug Code**
```
Bad: Remove all print() statements
Good: Wrap with DEBUG_OUTPUT flag
```

**❌ Assuming Context**
```
Bad: "Fixed the timeout issue" [no details]
Good: "Fixed timeout: system prompt in -p (not agent.prompt) + stdin=DEVNULL"
```

**❌ Single-Shot Testing**
```
Bad: Try one config, declare victory
Good: Test 11 configs, identify pattern, verify fix
```

---

## 13. INTEGRATION WITH ASIMOV RULES

### HITL as Asimov Rule 4

**Asimov Rule 4: Human-in-the-Loop (HITL)**
```python
ASIMOV_RULE_4_HITL = {
    "description": "Agent must optimize for human collaboration",

    "requirements": [
        "Detect user presence/absence",
        "Adjust behavior accordingly",
        "Provide output on demand",
        "Document all decisions",
        "Enable async collaboration"
    ],

    "modes": {
        "interactive": {
            "ask_clarifications": True,
            "wait_for_approval": True,
            "short_updates": True
        },
        "autonomous": {
            "ask_clarifications": False,
            "skip_blockers": True,
            "detailed_report": True
        },
        "debug": {
            "show_everything": True,
            "no_truncation": True,
            "timing_info": True
        }
    },

    "escalation": {
        "critical_errors": "STOP",
        "slow_operations": "DEFER",
        "missing_info": "CONTINUE_WITH_BEST_GUESS",
        "test_failures": "DOCUMENT_AND_CONTINUE"
    }
}
```

---

## 14. METRICS FOR SUCCESS

### How to Measure Good HITL

**Quantitative Metrics:**
```
1. Tasks Completed / Tasks Attempted (success rate)
2. Time Blocked Waiting for Human (minimize)
3. Time Saved by Autonomous Work (maximize)
4. Documentation Completeness (100% target)
5. Issues Correctly Escalated (precision/recall)
```

**Qualitative Metrics:**
```
1. User satisfaction with reports
2. Clarity of documentation
3. Ease of picking up where agent left off
4. Usefulness of recommendations
5. Accuracy of problem diagnosis
```

**Session Metrics:**
```
Duration:          ~3 hours
Tasks Attempted:   6
Tasks Completed:   5 (83%)
Tasks Deferred:    1 (with reason)
Documentation:     3 files (500+ lines)
User Wait Time:    0 minutes
Autonomy Level:    HIGH
Blockers Hit:      0
```

---

## 15. FUTURE IMPROVEMENTS

### What Could Be Better

**1. Automatic Mode Detection**
- Detect user away time automatically
- Switch to autonomous mode after 5min silence
- Alert user when back online

**2. Progress Streaming**
- Real-time progress updates
- Show current task
- Estimated time remaining

**3. Better Escalation**
- Confidence scores on decisions
- Automatic retry strategies
- Smart timeout adjustment

**4. Learning from Sessions**
- Pattern recognition (what works)
- Personalized user preferences
- Historical decision accuracy

**5. Collaborative Debugging**
- Shared debug session
- Interactive log viewer
- Real-time output streaming

---

## 📖 REFERENCES

**This Document Based On:**
- Session: 2025-10-10 Claude CLI debugging
- Files: TEST_RESULTS_2025-10-10.md, CLAUDE_BEST_PRACTICES.md
- Approach: Systematic debugging with autonomous execution
- Outcome: 5/6 tasks completed, 0 blockers, complete documentation

**Related Documents:**
- `ASIMOV_RULES.md` - Security and safety rules
- `CLAUDE_BEST_PRACTICES.md` - Claude CLI guidelines
- `TEST_RESULTS_2025-10-10.md` - Session summary

**Further Reading:**
- Human-in-the-Loop Machine Learning (Monarch 2021)
- Collaborative Intelligence (Harvard Business Review)
- Async Communication Patterns (Basecamp)

---

**Last Updated:** 2025-10-10
**Version:** 1.0
**Status:** Living Document (update based on new sessions)
