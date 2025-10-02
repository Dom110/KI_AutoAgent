# Orchestrator Loop-Back Pattern

## Overview
The Orchestrator Loop-Back pattern enables dynamic agent collaboration by allowing agents to route back to the orchestrator for re-planning. This creates a flexible workflow where agents can request help from other specialized agents at runtime.

## Problem Statement
Traditional static workflows don't allow for dynamic collaboration:
- Reviewer finds bugs → Can't request FixerBot
- CodeSmith needs research → Can't request ResearchBot
- Architect needs analysis → Can't request PerformanceBot

## Solution: Loop-Back Pattern
Agents can signal the need for collaboration, causing the workflow to:
1. Route back to Orchestrator
2. Orchestrator adds new step(s) to execution plan
3. Workflow continues with new step
4. Cycles repeat until all tasks complete

## Architecture

### Components

#### 1. State Flags
```python
# Agent sets these when collaboration needed
state["needs_replan"] = True
state["suggested_agent"] = "fixer"
state["suggested_query"] = "Fix the SQL injection bug..."
```

#### 2. Router Check
```python
def route_to_next_agent(state):
    # Priority 1: Check for re-planning request
    if state.get("needs_replan"):
        return "orchestrator"  # Loop back

    # Priority 2: Find next pending step
    for step in state["execution_plan"]:
        if step.status == "pending":
            return step.agent

    # All done
    return "end"
```

#### 3. Orchestrator Re-Planning
```python
async def orchestrator_node(state):
    # Check if this is a re-planning request
    if state.get("needs_replan"):
        # Extract collaboration request
        suggested_agent = state.get("suggested_agent")
        suggested_query = state.get("suggested_query")

        # Create new step
        new_step = ExecutionStep(
            id=len(state["execution_plan"]) + 1,
            agent=suggested_agent,
            task=suggested_query,
            status="pending",
            dependencies=[]  # Immediate execution
        )

        # Add to plan
        state["execution_plan"].append(new_step)
        state["execution_plan"] = list(state["execution_plan"])  # Trigger update

        # Clear flags
        state["needs_replan"] = False
        state["suggested_agent"] = None
        state["suggested_query"] = None

        return state

    # Otherwise, do initial planning
    # ...
```

#### 4. Conditional Edges
```python
workflow.add_conditional_edges(
    "approval",
    route_after_approval,
    {
        "orchestrator": "orchestrator",  # ← Loop-back enabled
        "architect": "architect",
        "codesmith": "codesmith",
        "reviewer": "reviewer",
        "fixer": "fixer",
        "end": END
    }
)
```

## Flow Diagram

### Single Collaboration
```
User: "Create login API"
    ↓
Orchestrator → Plan: [Architect, CodeSmith, Reviewer]
    ↓
Architect (Step 1) → Design API
    ↓
CodeSmith (Step 2) → Implement (with bug)
    ↓
Reviewer (Step 3) → Find SQL injection bug
    ↓
Set: needs_replan=True, suggested_agent=fixer
    ↓
Router → "orchestrator" (loop-back)
    ↓
Orchestrator → Add Step 4: Fixer
    ↓
Fixer (Step 4) → Fix SQL injection
    ↓
END
```

### Multiple Cycles
```
Reviewer (Step 3) → Issues found
    ↓
needs_replan=True, suggested_agent=fixer
    ↓
Orchestrator → Add Step 4: Fixer
    ↓
Fixer (Step 4) → Fix issues
    ↓
needs_replan=True, suggested_agent=reviewer (re-review)
    ↓
Orchestrator → Add Step 5: Reviewer
    ↓
Reviewer (Step 5) → Find more issues
    ↓
needs_replan=True, suggested_agent=fixer
    ↓
Orchestrator → Add Step 6: Fixer
    ↓
Fixer (Step 6) → Fix remaining issues
    ↓
needs_replan=True, suggested_agent=reviewer
    ↓
Orchestrator → Add Step 7: Reviewer
    ↓
Reviewer (Step 7) → Approved ✅
    ↓
END
```

## Implementation Details

### Agent Collaboration Detection

#### Reviewer Example
```python
async def reviewer_node(state):
    # Execute review
    review_result = await execute_review(state)
    current_step.result = review_result
    current_step.status = "completed"

    # Analyze result
    review_text = str(review_result).lower()
    has_critical_issues = any(keyword in review_text for keyword in [
        "critical", "bug", "error", "vulnerability"
    ])

    # Trigger collaboration if needed
    if has_critical_issues:
        logger.warning("⚠️ Critical issues found - requesting FixerBot")
        state["needs_replan"] = True
        state["suggested_agent"] = "fixer"
        state["suggested_query"] = f"Fix issues: {review_text[:200]}"

    return state
```

#### CodeSmith Example (future)
```python
async def codesmith_node(state):
    # Execute implementation
    result = await generate_code(state)
    current_step.result = result
    current_step.status = "completed"

    # Check if research needed
    needs_research = "need more information" in str(result).lower()

    if needs_research:
        logger.warning("📚 Need research - requesting ResearchBot")
        state["needs_replan"] = True
        state["suggested_agent"] = "research"
        state["suggested_query"] = f"Research for: {current_step.task}"

    return state
```

### State Management Rules

#### 1. Always Clear Flags
```python
# ❌ WRONG - Infinite loop!
state["needs_replan"] = True
# ... add step ...
# (forgot to clear)

# ✅ CORRECT
state["needs_replan"] = True
# ... add step ...
state["needs_replan"] = False
state["suggested_agent"] = None
state["suggested_query"] = None
```

#### 2. Trigger State Updates
```python
# ❌ WRONG - Won't trigger LangGraph update
state["execution_plan"].append(new_step)

# ✅ CORRECT - Triggers update
existing_plan = state["execution_plan"]
existing_plan.append(new_step)
state["execution_plan"] = list(existing_plan)
```

#### 3. No Dependencies on New Steps
```python
# New steps should have no dependencies
new_step = ExecutionStep(
    id=next_id,
    agent=suggested_agent,
    task=suggested_query,
    status="pending",
    dependencies=[]  # ← Execute immediately
)
```

## Routing Priority

The router checks in this order:

1. **Re-planning needed?** → Route to orchestrator
2. **In-progress steps?** → Continue those steps (bug fix)
3. **Pending steps?** → Route to next pending step
4. **All done?** → Route to END

```python
def route_to_next_agent(state):
    # CHECK 1: Re-planning
    if state.get("needs_replan"):
        return "orchestrator"

    # CHECK 2: In-progress (bug fix)
    for step in state["execution_plan"]:
        if step.status == "in_progress":
            return step.agent

    # CHECK 3: Pending
    for step in state["execution_plan"]:
        if step.status == "pending":
            step.status = "in_progress"
            return step.agent

    # CHECK 4: All done
    return "end"
```

## Use Cases

### 1. Code Review → Fix Cycle
**Trigger:** Reviewer finds critical bugs
**Collaboration:** Reviewer → Orchestrator → Fixer → Reviewer
**Outcome:** Code fixed and re-reviewed until approved

### 2. Implementation → Research Cycle
**Trigger:** CodeSmith lacks information
**Collaboration:** CodeSmith → Orchestrator → Research → CodeSmith
**Outcome:** Research provides info, CodeSmith completes implementation

### 3. Architecture → Performance Analysis
**Trigger:** Architect needs performance validation
**Collaboration:** Architect → Orchestrator → Performance → Architect
**Outcome:** Performance analysis informs architecture decisions

### 4. Documentation → Code Analysis
**Trigger:** DocuBot needs to understand complex code
**Collaboration:** DocuBot → Orchestrator → Reviewer → DocuBot
**Outcome:** Code analysis helps create better docs

## Limitations

### What This Pattern DOES Support
✅ Dynamic step addition during execution
✅ Agent-to-agent collaboration
✅ Multiple collaboration cycles
✅ Flexible workflow modification
✅ No graph recompilation needed

### What This Pattern DOES NOT Support
❌ Adding new agent nodes at runtime
❌ Modifying graph structure dynamically
❌ Deleting or reordering existing steps
❌ Conditional step execution based on future events

### Workarounds
- **New agents:** Pre-define all possible agents, route to them as needed
- **Complex flows:** Use multiple smaller graphs with subgraph invocation
- **Conditional execution:** Set step status to "skipped" if not needed

## Best Practices

### 1. Be Specific in Queries
```python
# ❌ Vague
state["suggested_query"] = "Fix the code"

# ✅ Specific
state["suggested_query"] = "Fix SQL injection in auth.py:45"
```

### 2. Log Everything
```python
if has_critical_issues:
    logger.warning("⚠️ Critical issues found")
    logger.info(f"  🔄 Requesting {suggested_agent}")
    logger.info(f"  📝 Query: {suggested_query[:100]}")
```

### 3. Validate Agent Exists
```python
AVAILABLE_NODES = {"orchestrator", "architect", "codesmith", "reviewer", "fixer"}

if suggested_agent not in AVAILABLE_NODES:
    logger.error(f"❌ Agent '{suggested_agent}' has no node")
    state["needs_replan"] = False  # Cancel request
    return state
```

### 4. Handle Edge Cases
```python
# What if suggested_agent or suggested_query is None?
suggested_agent = state.get("suggested_agent")
if not suggested_agent:
    logger.error("❌ No suggested_agent provided")
    state["needs_replan"] = False
    return state
```

## Testing

### Unit Tests
```python
def test_orchestrator_replan():
    state = {
        "needs_replan": True,
        "suggested_agent": "fixer",
        "suggested_query": "Fix bug",
        "execution_plan": [step1, step2]
    }

    result = await orchestrator_node(state)

    assert len(result["execution_plan"]) == 3
    assert result["execution_plan"][2].agent == "fixer"
    assert result["needs_replan"] == False
```

### Integration Tests
```python
async def test_reviewer_fixer_cycle():
    workflow = create_agent_workflow()

    # Code with bug
    state = await workflow.execute(
        task="Create login API with SQL"
    )

    # Check for collaboration
    agents = [s.agent for s in state["execution_plan"]]
    assert "reviewer" in agents
    assert "fixer" in agents

    # Verify sequence
    reviewer_idx = agents.index("reviewer")
    fixer_idx = agents.index("fixer")
    assert reviewer_idx < fixer_idx
```

## Troubleshooting

### Issue: Infinite Loop
**Symptom:** Workflow keeps adding fixer steps forever
**Cause:** Forgot to clear `needs_replan` flag
**Fix:** Always set `state["needs_replan"] = False` after handling

### Issue: Steps Not Added
**Symptom:** Orchestrator runs but no new steps appear
**Cause:** Didn't trigger state update with `list()`
**Fix:** Use `state["execution_plan"] = list(existing_plan)`

### Issue: Wrong Agent Executes
**Symptom:** Architect runs instead of Fixer
**Cause:** Router priority issue or flag not set
**Fix:** Check router order: replan → in_progress → pending → end

### Issue: Orchestrator Skipped
**Symptom:** Workflow goes straight to next step
**Cause:** Conditional edges don't include orchestrator
**Fix:** Add `"orchestrator": "orchestrator"` to edges mapping

## Future Enhancements

1. **Command Pattern:** Use LangGraph's Command object instead of state flags
2. **Priority Queue:** Allow agents to set priority for collaboration requests
3. **Parallel Collaboration:** Multiple agents collaborate simultaneously
4. **Conditional Collaboration:** Only collaborate if certain conditions met
5. **Collaboration Metrics:** Track collaboration frequency and success rate

## References
- LangGraph Multi-Agent: https://langchain-ai.github.io/langgraph/concepts/multi_agent/
- LangGraph Conditional Edges: https://langchain-ai.github.io/langgraph/concepts/low_level/
- Session Fixes: FIXES_SESSION_2025_10_02.md
- Collaboration Instructions: .kiautoagent/instructions/orchestrator-replanning-instructions.md
