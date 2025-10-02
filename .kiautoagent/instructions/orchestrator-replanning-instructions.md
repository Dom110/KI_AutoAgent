# Orchestrator Re-Planning Instructions

## Purpose
The Orchestrator handles dynamic workflow modification when agents request collaboration. It adds new steps to the execution plan at runtime without recompiling the graph.

## Two Modes of Operation

### Mode 1: Initial Planning
When workflow starts:
1. Receive user task
2. Analyze task complexity
3. Create initial execution plan
4. Route to first agent

### Mode 2: Re-Planning (Collaboration)
When agent requests collaboration:
1. Receive `needs_replan=True` signal
2. Read `suggested_agent` and `suggested_query`
3. Create new ExecutionStep
4. Add to execution plan
5. Clear replan flags
6. Continue workflow

## Re-Planning Flow

### Step 1: Detection
```python
if state.get("needs_replan"):
    # RE-PLANNING MODE
    logger.info("🔄 RE-PLANNING MODE: Agent requested collaboration")
```

### Step 2: Extract Collaboration Request
```python
suggested_agent = state.get("suggested_agent", "unknown")
suggested_query = state.get("suggested_query", "Continue work")
```

**Examples:**
- Reviewer finds bugs → `suggested_agent="fixer"`, `suggested_query="Fix SQL injection..."`
- CodeSmith needs info → `suggested_agent="research"`, `suggested_query="Research API docs..."`

### Step 3: Create New ExecutionStep
```python
existing_plan = state.get("execution_plan", [])
next_step_id = len(existing_plan) + 1

new_step = ExecutionStep(
    id=next_step_id,
    agent=suggested_agent,
    task=suggested_query,
    status="pending",
    dependencies=[]  # No dependencies - execute immediately
)
```

**Important:**
- Step ID = len(existing_plan) + 1
- Status = "pending" (will be picked up by router)
- No dependencies = can execute immediately
- Task = suggested_query from requesting agent

### Step 4: Update Execution Plan
```python
existing_plan.append(new_step)
state["execution_plan"] = list(existing_plan)  # Trigger LangGraph update
```

**Critical:**
- Must create NEW list: `list(existing_plan)`
- LangGraph only detects changes if object reference changes
- Appending alone won't trigger update

### Step 5: Clear Replan Flags
```python
state["needs_replan"] = False
state["suggested_agent"] = None
state["suggested_query"] = None
```

**Why:**
- Prevent infinite loop
- Router checks `needs_replan` flag
- Must clear to allow normal routing

### Step 6: Continue Execution
```python
state["status"] = "executing"
return state
```

Router will:
1. Check `needs_replan` → False (cleared)
2. Find new pending step (we just added)
3. Route to suggested agent

## Routing Integration

### Router Logic
```python
def route_to_next_agent(state):
    # CHECK 1: Re-planning needed?
    if state.get("needs_replan"):
        return "orchestrator"  # Loop back

    # CHECK 2: Find next pending step
    for step in state["execution_plan"]:
        if step.status == "pending":
            return step.agent  # Route to new step
```

**Flow:**
1. Reviewer sets `needs_replan=True` → Router routes to Orchestrator
2. Orchestrator adds Fixer step, clears flags → Router finds Fixer step
3. Router routes to Fixer → Fixer executes
4. Fixer sets `needs_replan=True` (for re-review) → Router routes to Orchestrator
5. Orchestrator adds Reviewer step → Router finds Reviewer step
6. And so on...

## Complete Collaboration Cycle

### Example: Code Review → Fix → Re-Review

**Initial Plan:**
```
Step 1: Architect (design)
Step 2: CodeSmith (implement)
Step 3: Reviewer (review)
```

**After Step 3 (Reviewer finds bugs):**
```python
state["needs_replan"] = True
state["suggested_agent"] = "fixer"
state["suggested_query"] = "Fix SQL injection in auth.py"
```

**Orchestrator Re-Planning:**
```
Step 1: Architect (completed)
Step 2: CodeSmith (completed)
Step 3: Reviewer (completed)
Step 4: Fixer (pending) ← NEW STEP ADDED
```

**After Step 4 (Fixer completes):**
```python
state["needs_replan"] = True
state["suggested_agent"] = "reviewer"
state["suggested_query"] = "Re-review fixed code"
```

**Orchestrator Re-Planning Again:**
```
Step 1: Architect (completed)
Step 2: CodeSmith (completed)
Step 3: Reviewer (completed)
Step 4: Fixer (completed)
Step 5: Reviewer (pending) ← NEW STEP ADDED
```

**After Step 5 (Reviewer approves):**
```python
# No needs_replan set
state["needs_replan"] = False
```

**Router:**
- No pending steps
- No replan needed
- Routes to END ✅

## Implementation Code

### orchestrator_node() Implementation
```python
async def orchestrator_node(self, state: ExtendedAgentState) -> ExtendedAgentState:
    logger.info("🎯 Orchestrator node executing")
    state["current_agent"] = "orchestrator"

    # 🔄 CHECK: Re-planning request?
    if state.get("needs_replan"):
        logger.info("🔄 RE-PLANNING MODE: Agent requested collaboration")

        # Extract collaboration request
        suggested_agent = state.get("suggested_agent", "unknown")
        suggested_query = state.get("suggested_query", "Continue work")

        # Create new step
        existing_plan = state.get("execution_plan", [])
        next_step_id = len(existing_plan) + 1

        new_step = ExecutionStep(
            id=next_step_id,
            agent=suggested_agent,
            task=suggested_query,
            status="pending",
            dependencies=[]
        )

        # Add to plan
        existing_plan.append(new_step)
        state["execution_plan"] = list(existing_plan)

        # Clear flags
        state["needs_replan"] = False
        state["suggested_agent"] = None
        state["suggested_query"] = None

        logger.info(f"  ✅ Added Step {next_step_id}: {suggested_agent}")
        state["status"] = "executing"
        return state

    # 📋 INITIAL PLANNING MODE
    # ... (existing initial planning code)
```

## Best Practices

1. **Always Clear Flags**: Prevent infinite loops
2. **Trigger State Update**: Use `list()` to create new object
3. **No Dependencies**: New steps execute immediately
4. **Log Everything**: Debug collaboration flow
5. **Validate Agent**: Check if agent node exists

## Testing

Test scenarios:
1. **Single Collaboration**: Review → Fix → END
2. **Multiple Cycles**: Review → Fix → Review → Fix → Review → END
3. **Different Agents**: CodeSmith → Research → CodeSmith
4. **Nested Collaboration**: Architect → CodeSmith → Review → Fix → Review

## Error Handling

If suggested agent doesn't exist:
```python
if suggested_agent not in AVAILABLE_NODES:
    logger.warning(f"⚠️ Suggested agent '{suggested_agent}' has no node")
    # Don't add step, clear flags, continue
    state["needs_replan"] = False
    return state
```

## Limitations

**What This DOES Support:**
- Adding new steps during execution
- Agent collaboration loops
- Dynamic workflow extension

**What This DOES NOT Support:**
- Adding new agent nodes at runtime
- Modifying graph structure
- Deleting/reordering existing steps

**Workaround for New Agents:**
- Pre-define all possible agent nodes
- Use routing to skip unused ones
- Validate agent exists before adding step
