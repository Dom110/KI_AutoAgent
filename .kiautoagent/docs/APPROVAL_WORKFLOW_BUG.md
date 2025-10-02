# Architecture Approval Workflow Bug (v5.3.1)

**Status:** 🔴 CRITICAL - Workflow does not continue after user approval
**Created:** 2025-10-02
**Version:** v5.3.1

---

## Problem Summary

The architecture proposal approval system is partially working but fails to continue the workflow after user approval is received.

### What Works ✅
1. Architecture proposal is created by Architect agent
2. Proposal is sent via WebSocket to frontend
3. User approval is received via WebSocket
4. Backend sends "architectureApprovalProcessed" acknowledgment

### What Doesn't Work ❌
1. Workflow does NOT continue to CodeSmith/implementation after approval
2. No further agent execution occurs
3. Workflow times out after approval without progress

---

## Root Cause Analysis

### Investigation Timeline

1. **Initial Symptom:** Test script receives approval acknowledgment but workflow never continues

2. **Discovery 1:** `active_workflows` dict not initialized
   - **Fixed in commit f6299be** ✅
   - Added `self.active_workflows = {}` in `__init__`

3. **Discovery 2:** Workflow state not stored when approval needed
   - State only stored if `status == "waiting_architecture_approval"` (line 2560)
   - This status is **never set** anywhere in the code
   - Therefore `active_workflows` dict remains empty when approval arrives

4. **Discovery 3:** Routing function never called
   - Added debug logging to `route_from_architect()` (line 989)
   - Logs confirm: function **never executes**
   - Architecture proposal bypasses normal routing flow

---

## Technical Details

### Relevant Code Sections

#### 1. Architect Node (workflow.py:519-557)
```python
# Creates proposal and sets state flags
state["proposal_status"] = "pending"
state["needs_approval"] = True
state["approval_type"] = "architecture_proposal"

# Sends via WebSocket
await self.websocket_manager.send_json(state["client_id"], {
    "type": "architecture_proposal",
    "proposal": proposal,
    ...
})

# ❌ PROBLEM: Returns immediately, doesn't wait for approval
return state
```

#### 2. Route from Architect (workflow.py:982-1009)
```python
def route_from_architect(self, state: ExtendedAgentState) -> str:
    # Should route to approval node if proposal created
    if state.get("needs_approval") and state.get("approval_type") == "architecture_proposal":
        if state.get("proposal_status") == "pending":
            return "approval"  # ❌ NEVER REACHED

    return self.route_to_next_agent(state)
```

#### 3. State Storage (workflow.py:2560-2567)
```python
# Only stores state if specific status set
if final_state.get("status") == "waiting_architecture_approval":
    self.active_workflows[session_id] = final_state
    logger.info("⏸️  Workflow paused...")

# ❌ PROBLEM: This status is never set anywhere!
```

#### 4. Approval Handler (server_langgraph.py:339-424)
```python
elif message_type == "architecture_approval":
    # Tries to find workflow state
    workflow_state = None
    for ws_session_id, ws_state in workflow_system.active_workflows.items():
        if ws_session_id == session_id:
            workflow_state = ws_state  # ❌ Never found (dict is empty)
            break

    if workflow_state:
        # Resume workflow
        await workflow_system.workflow.ainvoke(workflow_state, ...)
    else:
        # ❌ Always reaches here - state not found
```

---

## Why It Fails

### The Fundamental Problem

The architecture proposal system has a **state machine design flaw**:

1. **Architect node** creates proposal and sends it via WebSocket
2. But it **returns immediately** - doesn't pause workflow execution
3. Workflow continues and **completes** (reaches END state)
4. When approval arrives later, **workflow is already finished**
5. No state stored because status was never set to "waiting_architecture_approval"
6. `active_workflows` dict is empty
7. Approval handler can't find workflow to resume

### Expected Flow vs Actual Flow

**Expected:**
```
Architect → Creates Proposal → Routes to "approval" node →
Workflow PAUSES → Waits for WebSocket approval →
Approval arrives → Resume from checkpoint → Continue to CodeSmith
```

**Actual:**
```
Architect → Creates Proposal → Returns state →
Routes to next agent (NOT approval) →
Workflow completes → Reaches END →
Approval arrives → No state found → Nothing happens
```

---

## Evidence

### Test Results (test_tetris_websocket_workflow.py)

```
✅ Architecture Proposal Received: True
✅ Proposal Approved: True
✅ Approval Processed Acknowledgment: True
❌ Workflow Completed: False (timeout after 120s)

Message Flow:
1. connected
2. agent_thinking (Orchestrator)
3. step_completed (Orchestrator)
4. agent_thinking (Architect)
5. architecture_proposal
6. architectureApprovalProcessed
[No further messages - workflow stopped]
```

### Debug Logging

Added logging to `route_from_architect()`:
```python
logger.info(f"🔍 DEBUG route_from_architect: needs_approval={state.get('needs_approval')}, ...")
```

**Result:** Log line **never appeared** in server output
**Conclusion:** Routing function is not being called

---

## Attempted Fixes

1. ✅ **Fixed `active_workflows` initialization** (commit f6299be)
   - Necessary but not sufficient
   - Dict still remains empty because state is never stored

2. ❌ **Added debug logging to routing**
   - Confirmed routing function never called
   - Architecture proposal bypasses normal flow

3. ⏸️ **Not attempted:** Fundamental redesign of approval flow
   - Would require changing state machine structure
   - Need to implement proper "approval" node that pauses workflow
   - Need checkpoint/resume mechanism for async user input

---

## Proposed Solution

### Option A: Approval Node (Recommended)

Create a proper approval node in the LangGraph workflow:

```python
def approval_node(state: ExtendedAgentState):
    """
    Special node that pauses workflow and waits for external approval
    """
    # Set status to waiting
    state["status"] = "waiting_architecture_approval"

    # Store state in active_workflows
    session_id = state.get("session_id")
    self.active_workflows[session_id] = state

    # Return state with interrupt flag
    # LangGraph should pause here until resumed externally
    return state

# Add to workflow graph
workflow.add_node("approval", approval_node)
workflow.add_edge("architect", "approval")  # After architect
workflow.add_edge("approval", "codesmith")  # After approval
```

Then modify approval handler to use LangGraph's built-in interrupt/resume:
```python
# When approval arrives
config = {"configurable": {"thread_id": session_id}}

# Update state with approval decision
update = {"proposal_status": "approved", "status": "executing"}

# Resume from checkpoint
final_state = await workflow_system.workflow.ainvoke(
    update,
    config=config
)
```

### Option B: Synchronous Approval (Simpler but blocks)

Make architect node wait synchronously for approval:
- Send proposal via WebSocket
- Create asyncio.Event()
- Wait for event to be set by approval handler
- Continue execution

**Downside:** Blocks agent thread, not scalable

---

## Testing Plan

1. Implement approval node (Option A)
2. Run test_tetris_websocket_workflow.py
3. Verify:
   - ✅ Proposal sent
   - ✅ Workflow pauses (status = "waiting_architecture_approval")
   - ✅ State stored in active_workflows
   - ✅ Approval received
   - ✅ Workflow resumes from checkpoint
   - ✅ CodeSmith executes
   - ✅ Workflow completes

---

## Files to Modify

1. **backend/langgraph_system/workflow.py**
   - Add `approval_node()` function
   - Add node to workflow graph
   - Fix routing from architect to approval
   - Ensure state storage happens in approval node

2. **backend/api/server_langgraph.py**
   - Modify approval handler to use LangGraph resume mechanism
   - Use checkpointer to resume from stored state

3. **Test file**
   - test_tetris_websocket_workflow.py already exists
   - Should pass after fix

---

## Related Issues

- Architecture Proposal System (v5.2.0 feature)
- LangGraph state management and checkpoints
- WebSocket-based async user input
- Multi-agent workflow orchestration

---

## References

- Original implementation: Commits around v5.2.0
- Test file: test_tetris_websocket_workflow.py
- Related docs:
  - .kiautoagent/docs/AGENT_COLLABORATION.md
  - .kiautoagent/docs/LANGGRAPH_WORKFLOW.md
  - .kiautoagent/docs/ORCHESTRATOR_LOOPBACK.md

---

**Next Steps:**
1. Implement approval node with proper workflow pause
2. Test with Tetris workflow
3. Document successful approval flow
4. Consider generalizing for other approval types (code review, deployment, etc.)
