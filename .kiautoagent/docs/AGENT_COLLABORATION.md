# Agent Collaboration System

## Overview
The Agent Collaboration System enables specialized agents to work together dynamically, requesting help from each other when needed. This creates flexible, self-organizing workflows that adapt to task requirements.

## Core Concept
Instead of fixed linear workflows (A → B → C), agents can request collaboration:
- **Reviewer** finds bugs → Requests **FixerBot**
- **FixerBot** completes → Requests **Reviewer** for re-review
- **CodeSmith** needs info → Requests **ResearchBot**
- **Architect** needs validation → Requests **PerformanceBot**

## Architecture

### 1. Collaboration Mechanism

#### State-Based Communication
Agents communicate via state flags:
```python
# Agent A needs Agent B's help
state["needs_replan"] = True
state["suggested_agent"] = "agent_b"
state["suggested_query"] = "Specific task for Agent B"
```

#### Orchestrator Coordination
- Receives collaboration requests
- Creates new execution steps
- Manages workflow continuation
- Prevents infinite loops

#### Dynamic Routing
- Router checks for collaboration requests
- Routes back to orchestrator when needed
- Continues with added steps
- Completes when all agents satisfied

### 2. Collaboration Types

#### Type 1: Sequential Collaboration
**Pattern:** A → B → C
```
Architect → Design
CodeSmith → Implement
Reviewer → Review
```

#### Type 2: Iterative Collaboration
**Pattern:** A → B → A → B (cycle)
```
Reviewer → Find bugs
Fixer → Fix bugs
Reviewer → Re-review
Fixer → Fix remaining
Reviewer → Approve
```

#### Type 3: Nested Collaboration
**Pattern:** A → (B → C) → A
```
CodeSmith → Start implementation
  ↓ (needs info)
  ResearchBot → Gather information
  ↓
  CodeSmith → Complete with info
```

#### Type 4: Parallel Collaboration (Future)
**Pattern:** A → [B, C, D] → A
```
Architect → Design
  ↓
  [PerformanceBot, SecurityBot, CostBot] → All analyze
  ↓
  Architect → Refine based on all feedback
```

## Implemented Collaborations

### 1. Reviewer ↔ FixerBot

#### Trigger Conditions
Reviewer detects any of:
- `"critical"` - Critical severity issues
- `"bug"` - Logic or runtime bugs
- `"error"` - Error conditions
- `"vulnerability"` - Security vulnerabilities
- `"security issue"` - Security concerns
- `"fix needed"` - Explicit fix requirement
- `"must fix"` - Mandatory fixes
- `"requires fix"` - Fix requirement
- `"issue found"` - Any identified issue

#### Flow
```python
# Step 1: Reviewer analyzes code
review_result = "Critical: SQL injection found in auth.py:45"

# Step 2: Reviewer triggers collaboration
state["needs_replan"] = True
state["suggested_agent"] = "fixer"
state["suggested_query"] = "Fix the SQL injection in auth.py:45"

# Step 3: Router → Orchestrator
# Step 4: Orchestrator adds Fixer step
# Step 5: Fixer executes and fixes
# Step 6: Fixer can request re-review
state["needs_replan"] = True
state["suggested_agent"] = "reviewer"
state["suggested_query"] = "Re-review the fixed code"

# Step 7: Cycle continues until approved
```

#### Example Execution Plan
```
Initial:
1. Architect: Design API
2. CodeSmith: Implement API
3. Reviewer: Review code

After Reviewer (found issues):
1. Architect: Design API (completed)
2. CodeSmith: Implement API (completed)
3. Reviewer: Review code (completed)
4. Fixer: Fix SQL injection (pending) ← Added

After Fixer (fixed issues):
1. Architect: Design API (completed)
2. CodeSmith: Implement API (completed)
3. Reviewer: Review code (completed)
4. Fixer: Fix SQL injection (completed)
5. Reviewer: Re-review fixed code (pending) ← Added

After Re-Review (approved):
All steps completed ✅
```

### 2. CodeSmith → ResearchBot (Planned)

#### Trigger Conditions
CodeSmith detects:
- `"need more information"`
- `"requires research"`
- `"unclear"`
- `"need to research"`
- `"look up"`
- `"find documentation"`

#### Flow
```python
# CodeSmith needs API documentation
result = "Implementation blocked: Need Stripe API docs for payment processing"

state["needs_replan"] = True
state["suggested_agent"] = "research"
state["suggested_query"] = "Research Stripe payment API documentation"

# Research finds info
# CodeSmith continues with documentation
```

**Status:** ⏳ Pending - ResearchBot node not yet implemented

## Implementation Guide

### For Agent Developers

#### 1. Detect Collaboration Need
```python
async def your_agent_node(state):
    # Execute your task
    result = await execute_task(state)

    # Analyze result
    needs_help = check_if_collaboration_needed(result)

    if needs_help:
        # Trigger collaboration
        state["needs_replan"] = True
        state["suggested_agent"] = "helper_agent"
        state["suggested_query"] = "What helper should do"

    return state
```

#### 2. Keyword-Based Detection
```python
# Simple keyword check
result_text = str(result).lower()
needs_fixer = any(keyword in result_text for keyword in [
    "bug", "error", "issue", "fix needed"
])
```

#### 3. AI-Based Detection
```python
# Use AI to analyze result
detection_prompt = f"""
Analyze this output: {result}

Does it indicate that another agent is needed?
- If yes, specify which agent and why
- If no, respond with "NO"
"""

ai_response = await ai.complete(detection_prompt)

if "YES" in ai_response:
    state["needs_replan"] = True
    # ... extract agent and query from AI response
```

#### 4. Context-Aware Collaboration
```python
# Check previous steps
had_issues_before = any(
    step.agent == "fixer"
    for step in state["execution_plan"]
)

if has_new_issues and had_issues_before:
    # This is a recurring problem, maybe need different approach
    state["suggested_agent"] = "architect"
    state["suggested_query"] = "Review approach, issues keep occurring"
```

### For Orchestrator

#### 1. Validate Collaboration Request
```python
# Check if suggested agent exists
AVAILABLE_AGENTS = {"orchestrator", "architect", "codesmith", "reviewer", "fixer"}

if state.get("needs_replan"):
    suggested = state.get("suggested_agent")

    if suggested not in AVAILABLE_AGENTS:
        logger.error(f"❌ Agent '{suggested}' not available")
        state["needs_replan"] = False
        return state
```

#### 2. Prevent Infinite Loops
```python
# Track collaboration count
collab_count = state.get("collaboration_count", 0)

if collab_count > MAX_COLLABORATIONS:
    logger.error("❌ Too many collaborations, stopping")
    state["needs_replan"] = False
    state["status"] = "failed"
    state["error"] = "Exceeded max collaboration cycles"
    return state

state["collaboration_count"] = collab_count + 1
```

#### 3. Add Context to New Steps
```python
new_step = ExecutionStep(
    id=next_id,
    agent=suggested_agent,
    task=suggested_query,
    status="pending",
    dependencies=[],
    metadata={
        "triggered_by": state.get("current_agent"),
        "trigger_reason": "collaboration_request",
        "original_step": current_step_id
    }
)
```

## Best Practices

### 1. Clear Communication
```python
# ❌ Vague
state["suggested_query"] = "Fix this"

# ✅ Specific
state["suggested_query"] = "Fix SQL injection vulnerability in auth.py line 45 by using parameterized queries"
```

### 2. Include Context
```python
# Pass relevant information
state["suggested_query"] = f"""
Fix the issues found in review:
- SQL injection in auth.py:45
- XSS vulnerability in templates/user.html:23

Original implementation: {current_step.result}
Review findings: {review_result}
"""
```

### 3. Set Appropriate Importance
```python
# Store in memory with importance based on criticality
memory.store_memory(
    content=f"Collaboration: {suggested_agent} requested",
    importance=0.9 if "critical" in query else 0.6,
    metadata={
        "collaboration": True,
        "agent": suggested_agent
    }
)
```

### 4. Log Collaboration Flow
```python
logger.info(f"🔄 COLLABORATION REQUESTED")
logger.info(f"  From: {state['current_agent']}")
logger.info(f"  To: {suggested_agent}")
logger.info(f"  Reason: {suggested_query[:100]}")
```

## Testing Collaborations

### Unit Test: Detection
```python
async def test_reviewer_detects_issues():
    state = {
        "current_step": step,
        "execution_plan": [step]
    }

    # Mock review with issues
    with patch('execute_review', return_value="Critical bug found"):
        result = await reviewer_node(state)

    assert result["needs_replan"] == True
    assert result["suggested_agent"] == "fixer"
```

### Integration Test: Full Cycle
```python
async def test_review_fix_cycle():
    workflow = create_agent_workflow()

    # Task that will have bugs
    state = await workflow.execute(
        task="Create SQL-based login without validation"
    )

    # Verify collaboration happened
    agents = [s.agent for s in state["execution_plan"]]

    # Should have: architect, codesmith, reviewer, fixer, reviewer
    assert agents.count("reviewer") >= 2  # Initial + re-review
    assert "fixer" in agents

    # Verify sequence
    first_review = agents.index("reviewer")
    fixer = agents.index("fixer")
    second_review = agents.index("reviewer", first_review + 1)

    assert first_review < fixer < second_review
```

### Load Test: Multiple Cycles
```python
async def test_multiple_collaboration_cycles():
    # Test that system handles 5+ collaboration cycles
    state = await workflow.execute(
        task="Create complex system with intentional issues"
    )

    collaboration_count = state.get("collaboration_count", 0)
    assert collaboration_count >= 5
    assert collaboration_count <= MAX_COLLABORATIONS
```

## Metrics and Monitoring

### Collaboration Metrics
```python
# Track collaboration statistics
collaboration_stats = {
    "total_collaborations": 0,
    "by_agent": {
        "reviewer": {"requested": 0, "fulfilled": 0},
        "fixer": {"requested": 0, "fulfilled": 0},
        # ...
    },
    "avg_cycles": 0,
    "max_cycles": 0
}
```

### Performance Monitoring
```python
# Measure collaboration overhead
collab_start = time.time()
# ... collaboration ...
collab_duration = time.time() - collab_start

logger.info(f"⏱️ Collaboration took {collab_duration:.2f}s")
```

### Success Rate
```python
# Track if collaboration resolved the issue
collaboration_success = {
    "total": 0,
    "resolved": 0,
    "unresolved": 0,
    "partial": 0
}
```

## Common Patterns

### Pattern 1: Immediate Collaboration
Agent realizes it needs help right away
```python
if insufficient_information:
    state["needs_replan"] = True
    state["suggested_agent"] = "research"
    return state
```

### Pattern 2: Post-Task Collaboration
Agent completes, then realizes issue
```python
current_step.status = "completed"
current_step.result = result

if quality_check_fails(result):
    state["needs_replan"] = True
    state["suggested_agent"] = "quality_bot"
```

### Pattern 3: Conditional Collaboration
Only collaborate if certain conditions met
```python
if has_critical_issues and not is_simple_fix:
    state["needs_replan"] = True
    state["suggested_agent"] = "fixer"
elif has_critical_issues and is_simple_fix:
    # Fix it myself
    result = self.quick_fix(result)
```

### Pattern 4: Escalation
Try one agent, if fails, escalate
```python
if fixer_failed:
    state["suggested_agent"] = "architect"
    state["suggested_query"] = "Redesign approach, fixes failing"
```

## Future Enhancements

### 1. Command Pattern
Replace state flags with LangGraph Command objects:
```python
return Command(
    goto="orchestrator",
    update={
        "suggested_agent": "fixer",
        "suggested_query": "Fix bugs"
    }
)
```

### 2. Agent Negotiation
Agents negotiate who should handle task:
```python
# Fixer: "This is architectural, send to Architect"
# Architect: "This is just a bug, send to Fixer"
# Orchestrator: Resolves conflict
```

### 3. Parallel Collaboration
Multiple agents work simultaneously:
```python
state["parallel_collaboration"] = [
    {"agent": "security_bot", "query": "Check security"},
    {"agent": "performance_bot", "query": "Analyze performance"},
    {"agent": "cost_bot", "query": "Estimate costs"}
]
```

### 4. Learning from Collaboration
Track patterns and suggest improvements:
```python
# After multiple review→fix cycles
memory.learn_pattern(
    pattern="SQL injection common in auth",
    solution="Use ORM or parameterized queries from start"
)

# Next time
architect_prompt += "\\nNote: Use parameterized queries to prevent SQL injection"
```

## Troubleshooting

### Issue: Collaboration Not Triggered
**Check:**
- Keywords are in result text
- `needs_replan` flag is set
- `suggested_agent` is specified
- Router checks for flag

### Issue: Wrong Agent Receives Request
**Check:**
- `suggested_agent` value is correct
- Agent name matches node name
- Orchestrator validation logic
- Router routing logic

### Issue: Infinite Collaboration Loop
**Check:**
- Flags are cleared after handling
- Max collaboration limit is set
- Detection logic isn't too sensitive
- Agents aren't requesting each other infinitely

### Issue: Collaboration Overhead Too High
**Optimize:**
- Use keyword detection before AI analysis
- Cache collaboration patterns
- Batch multiple requests
- Implement collaboration cooldown

## References
- **Orchestrator Loop-Back:** ORCHESTRATOR_LOOPBACK.md
- **LangGraph Workflow:** LANGGRAPH_WORKFLOW.md
- **Session Fixes:** FIXES_SESSION_2025_10_02.md
- **Instructions:** .kiautoagent/instructions/*-collaboration-instructions.md
