# Workflow_v6_integrated.py Update Guide

## Changes Needed

### 1. Update Imports

**Line 109:**
```python
# OLD:
from cognitive.workflow_planner_v6 import WorkflowPlannerV6, WorkflowPlan, AgentType, ConditionType

# NEW:
from cognitive.workflow_estimator_v6 import WorkflowEstimator
from cognitive.asimov_rules import AsimovRules
```

### 2. Update __init__ (around line 200)

```python
# Replace WorkflowPlannerV6 with WorkflowEstimator
self.estimator = WorkflowEstimator()
self.asimov_rules = AsimovRules()
logger.info("⚖️  Asimov Rules initialized")
```

### 3. Replace Workflow Planning (around line 320-350)

**OLD:**
```python
# Get workflow plan
plan = await self.planner.plan(...)
```

**NEW:**
```python
# Get workflow estimate (ADVISORY ONLY - not used for routing!)
estimate = await self.estimator.plan(...)  # Still uses same interface
logger.info(f"📊 Estimated duration: {estimate.estimated_duration}")
logger.info(f"📊 Estimated complexity: {estimate.complexity}")
logger.info(f"📊 NOTE: Estimates are advisory - actual routing by agents + Asimov Rules")
```

### 4. Add Universal Routing Function (NEW - add around line 400)

```python
def _route_next_agent(self, state: SupervisorState, current_agent: str) -> str:
    """
    Universal routing function with Asimov Rules enforcement.

    Priority:
    1. Asimov Rules (CANNOT be violated!)
    2. Agent's autonomous decision
    3. HITL fallback
    """
    from langgraph.graph import END

    # FIRST: Check Asimov Rules (HIGHEST PRIORITY)
    asimov_override = self.asimov_rules.enforce_all_rules(state)
    if asimov_override:
        next_agent = asimov_override["next_agent"]
        reason = asimov_override["routing_reason"]
        rule = asimov_override["asimov_rule_enforced"]

        logger.warning(f"⚠️  ASIMOV OVERRIDE: {current_agent} → {next_agent}")
        logger.warning(f"   Rule: {rule}")
        logger.warning(f"   Reason: {reason}")

        # Update state with override
        state.update(asimov_override)
        return next_agent

    # SECOND: Agent's autonomous decision
    next_agent = state.get("next_agent")
    confidence = state.get("routing_confidence", 0.0)
    reason = state.get("routing_reason", "No reason provided")

    if next_agent and next_agent != "END":
        logger.info(f"✅ {current_agent} → {next_agent} (confidence: {confidence:.2f})")
        logger.info(f"   Reason: {reason}")

        # Track execution
        executed = state.get("executed_agents", [])
        if current_agent not in executed:
            executed.append(current_agent)
            state["executed_agents"] = executed

        return next_agent

    # Agent wants to end?
    if next_agent == "END" or state.get("can_end_workflow"):
        logger.info(f"✅ {current_agent} → END (workflow complete)")
        return END

    # THIRD: No decision from agent → HITL
    logger.warning(f"⚠️  {current_agent} provided no routing decision → HITL")
    return "hitl"
```

### 5. Replace ALL Routing Functions (lines ~1200-1500)

**Replace complex routing logic with simple delegation:**

```python
def _research_decide_next(self, state: SupervisorState) -> str:
    """Research routing - delegates to universal router."""
    return self._route_next_agent(state, "research")

def _architect_decide_next(self, state: SupervisorState) -> str:
    """Architect routing - delegates to universal router."""
    return self._route_next_agent(state, "architect")

def _codesmith_decide_next(self, state: SupervisorState) -> str:
    """Codesmith routing - delegates to universal router."""
    return self._route_next_agent(state, "codesmith")

def _reviewfix_decide_next(self, state: SupervisorState) -> str:
    """ReviewFix routing - delegates to universal router."""
    return self._route_next_agent(state, "reviewfix")
```

### 6. Initialize State Fields (in workflow execution start)

```python
# Initialize Asimov tracking fields
state.setdefault("architect_modes_executed", [])
state.setdefault("reviewfix_iteration", 0)
state.setdefault("user_summary_shown", False)
state.setdefault("asimov_rule_enforced", None)
state.setdefault("executed_agents", [])
state.setdefault("files_modified", [])
state.setdefault("next_agent", None)
state.setdefault("routing_confidence", 0.0)
state.setdefault("routing_reason", "")
state.setdefault("can_end_workflow", False)
```

## Summary

1. ✅ Import AsimovRules and WorkflowEstimator
2. ✅ Initialize both in __init__
3. ✅ Use estimator for duration prediction only (not routing!)
4. ✅ Add universal _route_next_agent() with Asimov Rules
5. ✅ Replace all routing functions with simple delegation
6. ✅ Initialize state fields at workflow start

This creates a clean, simple routing architecture where:
- Agents make decisions
- Asimov Rules enforce constraints
- No conflicts, single source of truth
