# Integration Guide: Dynamic Workflow Planner

## How to Replace Intent Detector with Workflow Planner

### Current Flow (v6.1-alpha)
```
User Input → Intent Detector → Fixed Workflow (CREATE/FIX/etc.) → Agents
```

### New Flow (v6.2 Proposal)
```
User Input → Workflow Planner → Dynamic Graph Builder → Conditional Agents
```

## Integration Changes Required

### 1. Modify `workflow_v6_integrated.py`

#### Replace intent_detection_node (line 639-698)

**OLD:**
```python
async def intent_detection_node(self, state: Dict) -> Dict:
    """Detect user intent and route to appropriate workflow."""
    # ... uses intent_detector_v6.detect_intent_v6()
    intent_result = await detect_intent_v6(user_input)
    state["intent"] = intent_result.get("intent", "CREATE")
```

**NEW:**
```python
async def workflow_planning_node(self, state: Dict) -> Dict:
    """Plan dynamic workflow based on user task."""
    from cognitive.workflow_planner_v6_prototype import WorkflowPlannerV6

    planner = WorkflowPlannerV6()
    user_input = state.get("user_input", "")
    workspace_path = state.get("workspace_path", "")

    # Get dynamic plan
    plan = await planner.plan_workflow(
        user_task=user_input,
        workspace_path=workspace_path,
        context={
            "existing_files": state.get("existing_files", []),
            "previous_error": state.get("error"),
            "language": "de" if "untersuche" in user_input.lower() else "en"
        }
    )

    # Store plan in state
    state["workflow_plan"] = plan
    state["planned_agents"] = [step.agent.value for step in plan.agents]
    state["current_agent_index"] = 0

    return state
```

#### Modify build_graph() (line 1026-1111)

**OLD:**
```python
def build_graph(self) -> StateGraph:
    """Build the LangGraph workflow with all nodes and edges."""
    graph = StateGraph(dict)

    # Static nodes
    graph.add_node("intent_detection", self.intent_detection_node)
    graph.add_node("research", self.research_node)
    # ... more static nodes

    # Static edges
    graph.add_conditional_edges(
        "intent_detection",
        _intent_decide_next,
        {"research": "research", "architect": "architect", ...}
    )
```

**NEW:**
```python
async def build_graph(self, plan: WorkflowPlan = None) -> StateGraph:
    """Build dynamic graph based on workflow plan."""
    graph = StateGraph(dict)

    # Always add planning node
    graph.add_node("workflow_planning", self.workflow_planning_node)
    graph.set_entry_point("workflow_planning")

    if plan:
        # Build graph from plan
        previous_node = "workflow_planning"

        for i, step in enumerate(plan.agents):
            node_name = f"{step.agent.value}_{i}"

            # Add node based on agent type
            if step.agent == AgentType.RESEARCH:
                graph.add_node(node_name, self.research_node)
            elif step.agent == AgentType.ARCHITECT:
                graph.add_node(node_name, self.architect_node)
            elif step.agent == AgentType.CODESMITH:
                graph.add_node(node_name, self.codesmith_node)
            elif step.agent == AgentType.REVIEWFIX:
                graph.add_node(node_name, self.reviewfix_node)

            # Add conditional edge based on step condition
            if step.condition == ConditionType.ALWAYS:
                graph.add_edge(previous_node, node_name)
            elif step.condition == ConditionType.IF_SUCCESS:
                graph.add_conditional_edges(
                    previous_node,
                    lambda s: node_name if not s.get("error") else END,
                    {node_name: node_name, END: END}
                )
            elif step.condition == ConditionType.PARALLEL:
                # Use Send() API for parallel execution
                pass  # TODO: Implement

            previous_node = node_name

        # Add final edge to END
        graph.add_edge(previous_node, END)
    else:
        # Default static graph as fallback
        self._add_static_nodes(graph)
        self._add_static_edges(graph)

    return graph.compile()
```

### 2. Add Dynamic Routing Functions

```python
async def _dynamic_decide_next(self, state: Dict) -> str:
    """Dynamically decide next node based on current state and plan."""
    plan = state.get("workflow_plan")
    current_index = state.get("current_agent_index", 0)

    if not plan or current_index >= len(plan.agents):
        return END

    current_step = plan.agents[current_index]

    # Check condition
    if current_step.condition == ConditionType.IF_LLM_DECIDES:
        # Ask LLM if this agent should run
        decision = await self._ask_llm_for_decision(state, current_step)
        if not decision:
            # Skip this agent
            state["current_agent_index"] += 1
            return self._dynamic_decide_next(state)

    # Check quality gate
    if current_step.condition == ConditionType.IF_QUALITY_LOW:
        quality = state.get("quality_score", 1.0)
        threshold = current_step.condition_params.get("threshold", 0.8)
        if quality >= threshold:
            # Skip ReviewFix if quality is good
            state["current_agent_index"] += 1
            return self._dynamic_decide_next(state)

    # Move to next agent
    state["current_agent_index"] += 1
    return current_step.agent.value
```

### 3. Update Agent Nodes for Conditional Execution

```python
async def architect_node(self, state: Dict) -> Dict:
    """Architect agent with conditional next-agent decision."""
    # ... existing architect logic ...

    # NEW: Check if next agent should run
    plan = state.get("workflow_plan")
    if plan:
        current_index = state.get("current_agent_index", 0)
        if current_index + 1 < len(plan.agents):
            next_step = plan.agents[current_index + 1]

            if next_step.condition == ConditionType.IF_LLM_DECIDES:
                # Ask LLM if next agent needed
                should_continue = await self.llm.ainvoke([
                    SystemMessage(f"Should {next_step.agent} run after architect?"),
                    HumanMessage(f"Architecture: {state.get('architecture')}")
                ])

                if not should_continue:
                    state["skip_next"] = True

    return state
```

## Testing the Integration

### Test Script
```python
# test_dynamic_workflow.py
import asyncio
from backend.workflow_v6_integrated import V6IntegratedWorkflow

async def test_dynamic_workflow():
    workflow = V6IntegratedWorkflow()

    # Test German EXPLAIN request
    result = await workflow.process_message(
        message="Untersuche die App und erkläre die Architektur",
        session_id="test_001",
        workspace_path="/Users/test/app"
    )

    print(f"Workflow executed: {result['agents_completed']}")
    print(f"Dynamic plan worked: {'explain' in result['agents_completed']}")

if __name__ == "__main__":
    asyncio.run(test_dynamic_workflow())
```

## Migration Path

### Phase 1: Add Planner Alongside Intent Detector
- Keep intent_detector_v6.py for backwards compatibility
- Add workflow_planner_v6.py as alternative
- Add feature flag to switch between them

### Phase 2: Test with Beta Users
- Enable planner for specific session IDs
- Compare performance and accuracy
- Gather feedback on dynamic workflows

### Phase 3: Full Migration
- Replace intent detector completely
- Remove static workflow definitions
- Enable full dynamic capabilities

## Benefits of This Approach

1. **Minimal Disruption** - Existing workflows continue to work
2. **Gradual Migration** - Can test with subset of users
3. **Fallback Safety** - Static graph as backup if planning fails
4. **Extensible** - Easy to add new agents without code changes
5. **Intelligent** - AI adapts workflow to specific tasks

## Potential Issues & Solutions

### Issue 1: Invalid Agent in Plan
**Solution:** Validate plan before building graph, use fallback if invalid

### Issue 2: Infinite Loops
**Solution:** Add max_iterations to state, terminate after limit

### Issue 3: Performance Overhead
**Solution:** Cache common workflow patterns (optional)

### Issue 4: Debugging Complexity
**Solution:** Log workflow plan, save to state for inspection

## Next Steps

1. **Review and approve approach**
2. **Implement workflow_planner_v6.py** (prototype done)
3. **Create feature flag system**
4. **Modify workflow_v6_integrated.py**
5. **Test with various scenarios**
6. **Deploy to beta users**
7. **Monitor and iterate**