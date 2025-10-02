# LangGraph Workflow Integration

## Overview
This document explains how KI AutoAgent uses LangGraph for multi-agent workflow orchestration, including state management, conditional routing, and dynamic collaboration patterns.

## LangGraph Architecture

### Core Components

#### 1. StateGraph
Defines the workflow structure with nodes and edges
```python
from langgraph.graph import StateGraph, END

# Create graph
workflow = StateGraph(ExtendedAgentState)

# Add nodes
workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("architect", architect_node)
workflow.add_node("codesmith", codesmith_node)
workflow.add_node("reviewer", reviewer_node)
workflow.add_node("fixer", fixer_node)

# Set entry point
workflow.set_entry_point("orchestrator")
```

#### 2. State Schema
Typed state that flows through the graph
```python
class ExtendedAgentState(TypedDict):
    # User input
    messages: List[Dict[str, str]]

    # Execution tracking
    execution_plan: List[ExecutionStep]
    current_step_id: Optional[int]
    current_agent: str
    status: str  # planning, executing, completed, failed

    # Collaboration
    needs_replan: bool
    suggested_agent: Optional[str]
    suggested_query: Optional[str]

    # Context
    workspace_path: str
    session_id: str
    available_tools: List[str]
    errors: List[Dict]
```

#### 3. Node Functions
Async functions that process state
```python
async def agent_node(state: ExtendedAgentState) -> ExtendedAgentState:
    # Update state
    state["current_agent"] = "agent_name"

    # Execute agent logic
    result = await execute_agent_task(state)

    # Update execution plan
    current_step.result = result
    current_step.status = "completed"

    # Trigger state update (CRITICAL!)
    state["execution_plan"] = list(state["execution_plan"])

    return state
```

#### 4. Edges and Routing
Define how state flows between nodes

**Static Edges:**
```python
# Always go from A to B
workflow.add_edge("architect", "codesmith")
```

**Conditional Edges:**
```python
# Route based on function result
workflow.add_conditional_edges(
    "orchestrator",
    route_to_next_agent,  # Routing function
    {
        "architect": "architect",
        "codesmith": "codesmith",
        "reviewer": "reviewer",
        "fixer": "fixer",
        "end": END
    }
)
```

## State Management Deep Dive

### Critical Rule: Object References
LangGraph only detects state changes when object **references** change, not when object **contents** change.

#### ❌ WRONG - Won't trigger update
```python
# Modifying list in-place
state["execution_plan"].append(new_step)
# LangGraph doesn't see this change!
```

#### ✅ CORRECT - Triggers update
```python
# Create new list reference
existing_plan = state["execution_plan"]
existing_plan.append(new_step)
state["execution_plan"] = list(existing_plan)  # New reference!
```

### Why This Matters
```python
# Without new reference
step.status = "completed"
# Router still sees old state, routes incorrectly

# With new reference
step.status = "completed"
state["execution_plan"] = list(state["execution_plan"])
# Router sees updated state, routes correctly
```

### State Update Checklist
After modifying state:
1. ✅ Modified execution_plan items? → Create new list
2. ✅ Added new step? → Create new list
3. ✅ Changed step status? → Create new list
4. ✅ Updated step result? → Create new list

## Routing Patterns

### Pattern 1: Sequential Routing
Route through agents in order
```python
def route_sequential(state):
    if not architect_done:
        return "architect"
    elif not codesmith_done:
        return "codesmith"
    elif not reviewer_done:
        return "reviewer"
    else:
        return "end"
```

### Pattern 2: Conditional Routing
Route based on state conditions
```python
def route_conditional(state):
    if state.get("needs_replan"):
        return "orchestrator"  # Loop back

    if has_pending_steps(state):
        return next_pending_agent(state)

    return "end"
```

### Pattern 3: Priority Routing
Check conditions in priority order
```python
def route_to_next_agent(state):
    # Priority 1: Re-planning needed
    if state.get("needs_replan"):
        return "orchestrator"

    # Priority 2: In-progress steps (bug fix)
    if has_in_progress_steps(state):
        return get_in_progress_agent(state)

    # Priority 3: Pending steps
    if has_pending_steps(state):
        return get_next_pending_agent(state)

    # Priority 4: All done
    return "end"
```

### Pattern 4: Loop-Back Routing
Allow routing back to previous nodes
```python
workflow.add_conditional_edges(
    "approval",
    route_after_approval,
    {
        "orchestrator": "orchestrator",  # ← Loop-back
        "architect": "architect",
        "codesmith": "codesmith",
        "reviewer": "reviewer",
        "fixer": "fixer",
        "end": END
    }
)
```

## Dynamic Workflow Modification

### What LangGraph Supports
✅ Conditional routing based on state
✅ Loop-back to previous nodes
✅ State-driven workflow changes
✅ Parallel node execution (supersteps)

### What LangGraph Does NOT Support
❌ Adding new nodes at runtime
❌ Removing nodes from graph
❌ Recompiling graph during execution
❌ Modifying edge connections at runtime

### Workaround: Dynamic Step Addition
Instead of adding nodes, add steps to execution plan:

```python
# Can't do this
# workflow.add_node("new_agent", new_agent_node)  ❌

# Do this instead
new_step = ExecutionStep(
    agent="existing_agent",  # Must be pre-defined node
    task="new_task"
)
state["execution_plan"].append(new_step)
state["execution_plan"] = list(state["execution_plan"])  ✅
```

## Collaboration Implementation

### Step-by-Step Flow

#### 1. Agent Signals Need
```python
# In reviewer_node
if has_critical_issues:
    state["needs_replan"] = True
    state["suggested_agent"] = "fixer"
    state["suggested_query"] = "Fix the bugs"
    return state
```

#### 2. Router Detects Signal
```python
def route_to_next_agent(state):
    if state.get("needs_replan"):
        logger.info("🔄 Re-planning needed")
        return "orchestrator"  # Loop back
    # ...
```

#### 3. Orchestrator Handles Request
```python
# In orchestrator_node
if state.get("needs_replan"):
    # Get request details
    suggested_agent = state.get("suggested_agent")
    suggested_query = state.get("suggested_query")

    # Create new step
    new_step = ExecutionStep(
        id=len(state["execution_plan"]) + 1,
        agent=suggested_agent,
        task=suggested_query,
        status="pending"
    )

    # Add to plan
    state["execution_plan"].append(new_step)
    state["execution_plan"] = list(state["execution_plan"])

    # Clear flags
    state["needs_replan"] = False
    state["suggested_agent"] = None
    state["suggested_query"] = None

    return state
```

#### 4. Router Routes to New Agent
```python
def route_to_next_agent(state):
    # Replan flag now False
    if state.get("needs_replan"):
        return "orchestrator"  # Skipped

    # Find new pending step
    for step in state["execution_plan"]:
        if step.status == "pending":
            step.status = "in_progress"
            return step.agent  # Returns "fixer"
```

#### 5. New Agent Executes
```python
# fixer_node executes
# Can also request re-review
if needs_rereviewing:
    state["needs_replan"] = True
    state["suggested_agent"] = "reviewer"
    # Cycle repeats
```

## Execution Flow Diagram

```
User Request
    ↓
[StateGraph Created]
    ↓
Entry Point: orchestrator_node
    ↓
orchestrator_node executes
    ├─ Creates execution_plan
    ├─ Sets status = "planning"
    └─ Returns state
    ↓
[Router: route_to_next_agent]
    ├─ Check needs_replan → False
    ├─ Find next pending → "architect"
    └─ Return "architect"
    ↓
architect_node executes
    ├─ Execute task
    ├─ Set step.status = "completed"
    ├─ state["execution_plan"] = list(...)  ← Trigger update
    └─ Returns state
    ↓
[Router: route_to_next_agent]
    ├─ Check needs_replan → False
    ├─ Find next pending → "codesmith"
    └─ Return "codesmith"
    ↓
codesmith_node executes
    ├─ Execute task
    ├─ Set step.status = "completed"
    ├─ state["execution_plan"] = list(...)
    └─ Returns state
    ↓
[Router: route_to_next_agent]
    ├─ Check needs_replan → False
    ├─ Find next pending → "reviewer"
    └─ Return "reviewer"
    ↓
reviewer_node executes
    ├─ Execute review
    ├─ Find critical issues
    ├─ Set needs_replan = True
    ├─ Set suggested_agent = "fixer"
    └─ Returns state
    ↓
[Router: route_to_next_agent]
    ├─ Check needs_replan → True  ← LOOP-BACK TRIGGER
    └─ Return "orchestrator"
    ↓
orchestrator_node executes (RE-PLANNING MODE)
    ├─ Detect needs_replan = True
    ├─ Create new step for "fixer"
    ├─ Append to execution_plan
    ├─ state["execution_plan"] = list(...)
    ├─ Clear needs_replan = False
    └─ Returns state
    ↓
[Router: route_to_next_agent]
    ├─ Check needs_replan → False
    ├─ Find next pending → "fixer"
    └─ Return "fixer"
    ↓
fixer_node executes
    ├─ Fix issues
    ├─ Set step.status = "completed"
    ├─ state["execution_plan"] = list(...)
    └─ Returns state
    ↓
[Router: route_to_next_agent]
    ├─ Check needs_replan → False
    ├─ No pending steps
    └─ Return "end"
    ↓
[Workflow Completes]
    └─ Final state returned
```

## Best Practices

### 1. Always Update State References
```python
# Pattern: Modify → Create New Reference
step.status = "completed"
state["execution_plan"] = list(state["execution_plan"])
```

### 2. Check Routing Order
Priority matters!
```python
# ✅ Correct order
if needs_replan: return "orchestrator"    # Highest priority
if in_progress: return in_progress_agent  # Second
if pending: return pending_agent          # Third
return "end"                              # Lowest

# ❌ Wrong order
if pending: return pending_agent          # Might skip replan!
if needs_replan: return "orchestrator"    # Too late
```

### 3. Log State Transitions
```python
logger.info(f"🎯 {node_name} executing")
logger.info(f"📊 State before: {state['status']}")
# ... execute ...
logger.info(f"📊 State after: {state['status']}")
logger.info(f"🔀 Returning state to router")
```

### 4. Validate State
```python
# Before routing
if not state.get("execution_plan"):
    logger.error("❌ No execution plan!")
    return "end"

if state.get("needs_replan") and not state.get("suggested_agent"):
    logger.error("❌ Replan flag set but no suggested agent!")
    state["needs_replan"] = False
```

### 5. Handle Errors Gracefully
```python
try:
    result = await execute_task(state)
except Exception as e:
    logger.error(f"❌ Task failed: {e}")
    current_step.status = "failed"
    current_step.error = str(e)
    state["execution_plan"] = list(state["execution_plan"])
    state["status"] = "failed"
    return state
```

## Performance Optimization

### 1. Minimize State Updates
```python
# ❌ Multiple updates
state["execution_plan"] = list(state["execution_plan"])
state["execution_plan"] = list(state["execution_plan"])
state["execution_plan"] = list(state["execution_plan"])

# ✅ Single update
# ... make all changes ...
state["execution_plan"] = list(state["execution_plan"])
```

### 2. Use Efficient Routing
```python
# ❌ Slow - checks every step
for step in state["execution_plan"]:
    if step.status == "pending":
        return step.agent

# ✅ Fast - early return
for step in state["execution_plan"]:
    if step.status == "pending":
        return step.agent  # Return immediately
```

### 3. Cache Routing Decisions
```python
# For complex routing logic
@lru_cache(maxsize=100)
def determine_next_agent(plan_hash: int) -> str:
    # Expensive routing logic
    pass

# In router
plan_hash = hash(tuple(step.status for step in state["execution_plan"]))
return determine_next_agent(plan_hash)
```

## Debugging

### Enable Verbose Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
```

### Trace State Flow
```python
# Add to each node
logger.debug(f"📥 {node_name} received state: {json.dumps(state, indent=2)}")
# ... execute ...
logger.debug(f"📤 {node_name} returning state: {json.dumps(state, indent=2)}")
```

### Visualize Execution Plan
```python
def print_execution_plan(state):
    print("\\n📋 EXECUTION PLAN:")
    for i, step in enumerate(state["execution_plan"], 1):
        status_icon = {"pending": "⏸️", "in_progress": "⏳", "completed": "✅", "failed": "❌"}
        print(f"  {i}. [{status_icon[step.status]}] {step.agent}: {step.task[:50]}")
```

### Track Routing Decisions
```python
# Add to router
routing_history = []

def route_to_next_agent(state):
    decision = determine_route(state)
    routing_history.append({
        "from": state.get("current_agent"),
        "to": decision,
        "reason": get_routing_reason(state, decision)
    })
    return decision
```

## Common Pitfalls

### 1. Forgetting State Update
**Symptom:** Changes don't appear in next node
**Fix:** Always use `list()` after modifications

### 2. Wrong Routing Order
**Symptom:** Re-planning doesn't trigger
**Fix:** Check `needs_replan` FIRST in router

### 3. Infinite Loops
**Symptom:** Same nodes execute forever
**Fix:** Clear `needs_replan` flag after handling

### 4. Type Errors
**Symptom:** `NoneType has no attribute...`
**Fix:** Use `.get()` with defaults: `state.get("key", default)`

### 5. Lost State
**Symptom:** State resets between nodes
**Fix:** Always return state from node functions

## References
- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/
- **LangGraph Concepts:** https://langchain-ai.github.io/langgraph/concepts/
- **Multi-Agent:** https://langchain-ai.github.io/langgraph/concepts/multi_agent/
- **Conditional Edges:** https://langchain-ai.github.io/langgraph/concepts/low_level/
- **Orchestrator Loop-Back:** ORCHESTRATOR_LOOPBACK.md
- **Agent Collaboration:** AGENT_COLLABORATION.md
