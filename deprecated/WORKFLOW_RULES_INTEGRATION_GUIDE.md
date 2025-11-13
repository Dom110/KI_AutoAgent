# 🔧 WORKFLOW RULES INTEGRATION GUIDE v7.0

**Status:** READY FOR IMPLEMENTATION  
**Date:** 2025-11-03  
**Complexity:** Medium (several files need updates)

---

## 📋 Quick Overview

This guide shows how to integrate the new **App Development Workflow Rules** (from `APP_DEVELOPMENT_WORKFLOW_RULES.md`) into the existing KI AutoAgent codebase.

**Files to Create:**
- ✅ `APP_DEVELOPMENT_WORKFLOW_RULES.md` - Created
- ✅ `ARCHITECT_AGENT_DECISION_TREE.md` - Created
- ✅ `backend/core/supervisor_routing_rules.py` - Created

**Files to Modify:**
- 📝 `backend/core/supervisor_mcp.py` - Update routing logic
- 📝 `backend/workflow_v7_mcp.py` - Update workflow graph
- 📝 `mcp_servers/architect_agent_server.py` - Add decision tree
- 📝 `backend/utils/mcp_manager.py` - Add state tracking (optional)

---

## 🎯 INTEGRATION STRATEGY

### Phase 1: Minimal Integration (Quick Start)
Integrate only the critical routing logic changes.

**Effort:** 1-2 hours  
**Risk:** Low  
**Impact:** Medium

### Phase 2: Full Integration (Complete)
Integrate all improvements including state tracking and decision logic.

**Effort:** 4-6 hours  
**Risk:** Medium  
**Impact:** High

---

## 📝 PHASE 1: MINIMAL INTEGRATION

### Step 1: Update Supervisor Routing (supervisor_mcp.py)

**File:** `backend/core/supervisor_mcp.py`

**Location:** In `decide_next()` method, around line 350

**Current Code:**
```python
def _get_system_prompt(self) -> str:
    """System prompt for Supervisor"""
    return """You are the Supervisor, the ONLY decision maker...
    """
```

**Add this AFTER the system prompt:**

```python
from backend.core.supervisor_routing_rules import (
    get_supervisor_routing_rules,
    WorkflowContext,
    ArchitectureState,
    CodeState,
    ValidationState,
    WorkflowMode
)

def _decide_with_rules(self, state: dict) -> Command:
    """
    ⚠️ MCP BLEIBT: Use routing rules to decide next agent.
    
    This method applies the App Development Workflow Rules.
    """
    
    # Get routing rules instance
    routing_rules = get_supervisor_routing_rules()
    
    # Build workflow context from state
    context = WorkflowContext(
        mode=self._detect_workflow_mode(state),
        user_query=state.get("user_query", ""),
        workspace_path=state.get("workspace_path", ""),
        last_agent=state.get("last_agent"),
        iteration=state.get("iteration", 0),
        
        # Architecture
        architecture=state.get("architecture"),
        arch_state=self._detect_arch_state(state),
        
        # Code
        generated_files=state.get("generated_files"),
        code_state=self._detect_code_state(state),
        
        # Validation
        validation_results=state.get("validation_results"),
        validation_state=self._detect_validation_state(state),
        
        # Research
        research_context=state.get("research_context"),
        needs_research=state.get("needs_research", False),
        
        # History
        errors=state.get("errors", []),
        agent_call_count=self._count_agent_calls(state)
    )
    
    # Get routing decision
    decision = routing_rules.decide_next_agent(context)
    
    # Convert to Command
    return Command(
        goto=decision.next_agent,
        update={
            **decision.state_updates,
            "instructions": decision.instructions
        }
    )

def _detect_workflow_mode(self, state: dict) -> WorkflowMode:
    """Detect workflow mode from user query."""
    query = state.get("user_query", "").lower()
    if "create" in query or "build" in query:
        return WorkflowMode.CREATE
    elif "refactor" in query or "improve" in query:
        return WorkflowMode.REFACTOR
    elif "fix" in query:
        return WorkflowMode.FIX
    else:
        return WorkflowMode.DEVELOP

def _detect_arch_state(self, state: dict) -> ArchitectureState:
    """Detect architecture state."""
    arch = state.get("architecture")
    if not arch:
        return ArchitectureState.NONE
    if state.get("architecture_complete"):
        return ArchitectureState.COMPLETE
    if state.get("awaiting_human"):
        return ArchitectureState.NEEDS_REVIEW
    return ArchitectureState.PARTIAL

def _detect_code_state(self, state: dict) -> CodeState:
    """Detect code generation state."""
    if state.get("code_complete"):
        return CodeState.COMPLETE
    if state.get("generated_files"):
        return CodeState.IN_PROGRESS
    if state.get("validation_results", {}).get("issues"):
        return CodeState.NEEDS_FIX
    return CodeState.NONE

def _detect_validation_state(self, state: dict) -> ValidationState:
    """Detect validation state."""
    if not state.get("validation_results"):
        return ValidationState.NOT_RUN
    if state.get("validation_passed"):
        return ValidationState.PASSED
    issues = state.get("validation_results", {}).get("issues", [])
    if issues:
        return ValidationState.FAILED
    return ValidationState.WARNINGS

def _count_agent_calls(self, state: dict) -> dict:
    """Count how many times each agent has been called."""
    messages = state.get("messages", [])
    counts = {}
    for msg in messages:
        agent = msg.get("agent")
        if agent:
            counts[agent] = counts.get(agent, 0) + 1
    return counts
```

**Integration Point:** In `decide_next()`, replace the current LLM-based decision with:

```python
async def decide_next(self, state: dict[str, Any]) -> Command:
    """Make routing decision using workflow rules."""
    
    # First check termination conditions
    if state.get("response_ready", False):
        return Command(goto=END)
    
    if state.get("error_count", 0) > 3:
        return Command(goto="responder", update={
            "response_ready": True,
            "user_response": "Workflow failed due to too many errors."
        })
    
    # Use workflow rules
    return self._decide_with_rules(state)
```

### Step 2: Verify Workflow Graph Structure (workflow_v7_mcp.py)

**File:** `backend/workflow_v7_mcp.py`

**Check:** Around line 180, verify the graph has all nodes:

```python
# Should have these nodes:
builder.add_node("supervisor", supervisor_node)
builder.add_node("architect", architect_node)       # ✅ Required
builder.add_node("research", research_node)         # ✅ Required
builder.add_node("codesmith", codesmith_node)       # ✅ Required
builder.add_node("reviewfix", reviewfix_node)       # ✅ Required
builder.add_node("responder", responder_node)       # ✅ Required
builder.add_node("hitl", hitl_node)                 # ✅ Required

# All edges should be managed by Supervisor (Command-based routing)
# No explicit edges needed - Supervisor uses goto
```

### Step 3: Update Architect Server (architect_agent_server.py)

**File:** `mcp_servers/architect_agent_server.py`

**Add Decision Tree Implementation:**

```python
# Add to class ArchitectAgentMCPServer

async def handle_architect_decision(self, instructions: str) -> dict:
    """
    Main decision handler for architect agent.
    Implements the decision tree from ARCHITECT_AGENT_DECISION_TREE.md
    """
    
    # DECISION 1: Existing architecture?
    workspace_path = self.context.get("workspace_path", "")
    existing_arch = self._check_existing_architecture(workspace_path)
    
    if existing_arch:
        return await self._handle_existing_architecture(instructions, existing_arch)
    else:
        return await self._handle_greenfield_architecture(instructions)

async def _handle_greenfield_architecture(self, instructions: str) -> dict:
    """Handle DECISION 1a: Greenfield mode (no existing architecture)."""
    
    # DECISION 1a-1: Research needed?
    needs_research = self._detect_research_needed(instructions)
    
    if needs_research:
        return {
            "action": "request_research",
            "research_topic": self._extract_research_topic(instructions),
            "instructions": instructions,
            "next_agent": "research"
        }
    else:
        # Design standard architecture
        architecture = await self._design_standard_architecture(instructions)
        return {
            "action": "architecture_designed",
            "architecture": architecture,
            "next_agent": "codesmith"
        }

async def _handle_existing_architecture(
    self,
    instructions: str,
    existing_arch: dict
) -> dict:
    """Handle DECISION 1b: Existing architecture mode."""
    
    # DECISION 1b-1: Improvements requested?
    needs_improvements = self._detect_improvements_requested(instructions)
    
    if not needs_improvements:
        # Use as-is
        return {
            "action": "use_existing",
            "architecture": existing_arch,
            "next_agent": "codesmith"
        }
    
    # DECISION 1b-2: Research needed for improvements?
    needs_research = self._detect_research_needed(instructions)
    
    if needs_research:
        return {
            "action": "request_research",
            "research_topic": self._extract_research_topic(instructions),
            "existing_architecture": existing_arch,
            "next_agent": "research"
        }
    else:
        # Standard improvements
        is_complex = self._is_complex_refactor(existing_arch, instructions)
        
        if is_complex:
            # DECISION 1b-2a-1: Complex? → HITL needed
            improved_arch = await self._design_improvements(existing_arch, instructions)
            return {
                "action": "hitl_needed",
                "current_architecture": existing_arch,
                "proposed_architecture": improved_arch,
                "mermaid_diagram": improved_arch.get("mermaid_diagram"),
                "next_agent": "hitl"
            }
        else:
            # Simple improvements → go to codesmith
            improved_arch = await self._design_improvements(existing_arch, instructions)
            return {
                "action": "improvements_designed",
                "architecture": improved_arch,
                "next_agent": "codesmith"
            }

# Helper methods
def _check_existing_architecture(self, workspace_path: str) -> dict | None:
    """Check if architecture files exist."""
    try:
        # Look for .architecture/ directory or architecture.json
        import json
        from pathlib import Path
        
        arch_file = Path(workspace_path) / "architecture.json"
        if arch_file.exists():
            with open(arch_file) as f:
                return json.load(f)
    except:
        pass
    return None

def _detect_research_needed(self, instructions: str) -> bool:
    """Detect if research is needed for this task."""
    research_keywords = [
        "ml", "machine learning", "ai", "blockchain",
        "real-time", "microservices", "performance",
        "scalability", "security"
    ]
    return any(kw in instructions.lower() for kw in research_keywords)

def _detect_improvements_requested(self, instructions: str) -> bool:
    """Detect if improvements are requested."""
    improvement_keywords = [
        "improve", "refactor", "modernize", "add",
        "modify", "enhance", "upgrade", "fix",
        "better", "optimize"
    ]
    return any(kw in instructions.lower() for kw in improvement_keywords)

def _is_complex_refactor(self, existing_arch: dict, instructions: str) -> bool:
    """Determine if refactor is complex (needs HITL)."""
    # Complex if:
    # - Changing framework
    # - Changing database
    # - Major structural changes
    return any(phrase in instructions.lower() for phrase in [
        "microservices", "restructure", "complete rewrite",
        "new framework", "migrate", "redesign"
    ])

async def _design_standard_architecture(self, instructions: str) -> dict:
    """Design standard architecture (uses OpenAI MCP)."""
    # Call OpenAI via MCP
    # Returns full architecture object
    pass

async def _design_improvements(self, existing_arch: dict, instructions: str) -> dict:
    """Design improved architecture based on existing."""
    # Call OpenAI via MCP with context
    # Returns improved architecture object
    pass
```

---

## 📝 PHASE 2: FULL INTEGRATION

### Additional Changes

#### 1. Update State Initialization

**File:** `backend/workflow_v7_mcp.py`

**In SupervisorState TypedDict**, add:

```python
class SupervisorState(TypedDict):
    # ... existing fields ...
    
    # Workflow rules state
    workflow_mode: str  # "create", "develop", "refactor"
    arch_state: str    # "none", "partial", "complete", "needs_review"
    code_state: str    # "none", "in_progress", "complete", "needs_fix"
    validation_state: str  # "not_run", "passed", "failed", "warnings"
    agent_call_count: dict  # Track agent calls for loop detection
    awaiting_human: bool  # True during HITL
    response_ready: bool  # True when Responder done
```

#### 2. Add HITL Node

**File:** `backend/workflow_v7_mcp.py`

**Add new node:**

```python
async def hitl_node(state: SupervisorState) -> Command:
    """
    Human-in-the-Loop node for architecture review.
    
    Sends architecture proposal to user and waits for approval.
    """
    mcp = get_mcp_manager()
    
    # Format HITL data
    hitl_prompt = f"""
ARCHITECTURE REVIEW REQUIRED

Current Proposal:
{format_architecture(state.get('architecture'))}

Mermaid Diagram:
{state.get('architecture', {}).get('mermaid_diagram', 'N/A')}

Please review and provide feedback:
1. Approve the architecture?
2. Any changes needed?
3. Additional requirements?
"""
    
    # Get user feedback
    user_response = await get_user_feedback(
        session_id=state["session_id"],
        prompt=hitl_prompt
    )
    
    return Command(
        goto="supervisor",
        update={
            "last_agent": "hitl",
            "hitl_response": user_response,
            "awaiting_human": False
        }
    )

# Add to graph
builder.add_node("hitl", hitl_node)
```

#### 3. Add State Tracking to Messages

**File:** `backend/workflow_v7_mcp.py`

**Update message tracking:**

```python
async def supervisor_node(state: SupervisorState) -> Command:
    """Supervisor with better state tracking."""
    
    # Track state changes
    messages = state.get("messages", [])
    new_message = {
        "timestamp": datetime.now().isoformat(),
        "agent": "supervisor",
        "iteration": state.get("iteration"),
        "state": {
            "arch_state": state.get("arch_state"),
            "code_state": state.get("code_state"),
            "validation_state": state.get("validation_state")
        }
    }
    messages.append(new_message)
    
    # ... rest of supervisor logic ...
```

---

## 🧪 TESTING INTEGRATION

### Test 1: Verify Routing Logic

```python
# test_supervisor_routing.py
from backend.core.supervisor_routing_rules import (
    get_supervisor_routing_rules,
    WorkflowContext,
    WorkflowMode,
    ArchitectureState
)

def test_initial_routing():
    """Test initial routing to Architect."""
    routing = get_supervisor_routing_rules()
    
    context = WorkflowContext(
        mode=WorkflowMode.CREATE,
        user_query="Create a REST API",
        workspace_path="/tmp/test",
        last_agent=None,
        iteration=0,
        architecture=None,
        arch_state=ArchitectureState.NONE,
        generated_files=None,
        code_state=CodeState.NONE,
        validation_results=None,
        validation_state=ValidationState.NOT_RUN,
        research_context=None,
        needs_research=False,
        errors=[],
        agent_call_count={}
    )
    
    decision = routing.decide_next_agent(context)
    
    assert decision.next_agent == "architect"
    print(f"✅ Initial routing: {decision.next_agent}")
```

### Test 2: Run E2E with New Workflow

```bash
# Use existing E2E test but monitor state transitions
python test_e2e_1_new_app.py

# Check logs for routing decisions
grep "Supervisor deciding" server_e2e_test.log
```

### Test 3: Verify Architecture Files

```bash
# After test completes, check workspace
ls -la ~/TestApps/e2e_test_1_new_app/

# Should have:
# - architecture.json ✅
# - architecture.md ✅
# - structure.mermaid ✅
```

---

## 📊 ROLLOUT PLAN

### Stage 1: Staging (Day 1)
- [ ] Apply Phase 1 changes
- [ ] Run quick smoke test
- [ ] Verify supervisor routing still works

### Stage 2: Testing (Day 2-3)
- [ ] Run full E2E tests with new routing
- [ ] Test each workflow mode (create, develop, refactor)
- [ ] Monitor for errors and loops

### Stage 3: Deployment (Day 4)
- [ ] Deploy to production
- [ ] Monitor supervisor logs for routing decisions
- [ ] Collect feedback from tests

---

## 🔄 VERIFICATION CHECKLIST

- [ ] All workflow rules documented
- [ ] Architect decision tree implemented
- [ ] Supervisor routing updated
- [ ] HITL node added
- [ ] State tracking improved
- [ ] E2E tests pass
- [ ] No infinite loops
- [ ] Error handling works
- [ ] Responder gets all context
- [ ] User sees beautiful output

---

## 📚 RELATED DOCUMENTATION

- `APP_DEVELOPMENT_WORKFLOW_RULES.md` - Main workflow specification
- `ARCHITECT_AGENT_DECISION_TREE.md` - Architect decision logic
- `backend/core/supervisor_routing_rules.py` - Python implementation
- `backend/workflow_v7_mcp.py` - Workflow graph
- `backend/core/supervisor_mcp.py` - Supervisor agent

---

## 🆘 TROUBLESHOOTING

### Issue: Supervisor not making decisions
**Solution:** Check if `_decide_with_rules()` is being called. Verify routing rules import.

### Issue: Architect not receiving instructions
**Solution:** Check state_updates in RoutingDecision. Verify instructions field is being passed.

### Issue: HITL node not found
**Solution:** Make sure HITL node is added to graph with `builder.add_node("hitl", hitl_node)`

### Issue: Infinite loops
**Solution:** Check `max_agent_calls` in SupervisorRoutingRules. Increase iteration limit if needed.

---

**Last Updated:** 2025-11-03  
**Implementation Status:** READY  
**Next Steps:** Begin Phase 1 integration