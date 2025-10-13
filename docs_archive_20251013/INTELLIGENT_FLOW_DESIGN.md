# Intelligent Multi-Agent Flow Design (v6.1)

**Date:** 2025-10-09
**Status:** DESIGN (Not yet implemented)
**Current:** Linear flow (STARR)
**Target:** Intelligent conditional flow (DYNAMISCH)

---

## 🚨 Current Problem:

**workflow_v6_integrated.py (lines 658-663):**
```python
# ❌ STARRER FLOW:
graph.add_edge("supervisor", "research")
graph.add_edge("research", "architect")
graph.add_edge("architect", "codesmith")
graph.add_edge("codesmith", "reviewfix")
graph.add_edge("reviewfix", END)
```

**Result:** Agents ALWAYS run in fixed order, NO intelligence, NO flexibility!

---

## ✅ Target: Intelligent Conditional Flow

### Principle:
**Agents entscheiden selbst basierend auf:**
- Ergebnis ihrer Arbeit
- Benötigte zusätzliche Information
- Fehler die auftreten
- Komplexität der Aufgabe

### Example Scenarios:

#### Scenario 1: Codesmith needs more research
```
User: "Build Stripe payment integration"

Flow:
1. Research → Finds basic Stripe docs
2. Architect → Designs payment flow
3. Codesmith → Starts coding
   ❓ "I need latest Stripe API v2024 docs"
   → DECISION: Call Research again
4. Research → Finds specific v2024 docs
5. Codesmith → Continues with updated info
6. ReviewFix → Checks
7. END
```

#### Scenario 2: ReviewFix can't fix error
```
User: "Create ML model trainer"

Flow:
1. Research → ML best practices
2. Architect → Model architecture
3. Codesmith → Generates code
4. ReviewFix → Finds import error
   ❌ Tries to fix → Fails
   ❌ Tries again → Fails (3x)
   → DECISION: HITL (ASIMOV RULE 4!)
5. Human → "Use tensorflow instead of torch"
6. Codesmith → Regenerates with tensorflow
7. ReviewFix → ✅ OK
8. END
```

#### Scenario 3: Simple task (skip unnecessary agents)
```
User: "Add a comment to function foo()"

Flow:
1. Research → NOT NEEDED (simple task)
   → DECISION: Skip to Architect
2. Architect → NOT NEEDED (no design required)
   → DECISION: Skip to Codesmith
3. Codesmith → Adds comment
   → DECISION: Skip ReviewFix (trivial change)
4. END
```

---

## 🏗️ Implementation Design

### 1. Decision Functions

Each agent has a decision function that returns next node:

```python
def codesmith_decide_next(state: SupervisorState) -> str:
    """
    Codesmith decides next step based on results.

    Returns:
        - "research": Need more information
        - "reviewfix": Code needs review
        - "hitl": Stuck, need human help (ASIMOV RULE 4)
        - END: All done
    """
    result = state.get("codesmith_result", {})

    # Check if we're stuck (ASIMOV RULE 4)
    retry_count = result.get("retry_count", 0)
    if retry_count >= 3:
        logger.warning("🛑 Codesmith stuck after 3 retries → HITL")
        return "hitl"

    # Check if we need more research
    if result.get("needs_more_info"):
        logger.info("🔍 Codesmith needs more research")
        return "research"

    # Check if code was generated
    files_generated = len(result.get("files", []))
    if files_generated == 0:
        logger.warning("⚠️ No files generated")
        return "reviewfix"  # Maybe reviewer can help

    # Check if there are errors
    if result.get("errors"):
        logger.info("🔬 Code has errors → ReviewFix")
        return "reviewfix"

    # All good!
    logger.info("✅ Codesmith complete")
    return END


def reviewfix_decide_next(state: SupervisorState) -> str:
    """
    ReviewFix decides next step after review.

    Returns:
        - "codesmith": Need to regenerate code
        - "hitl": Can't fix, need human (ASIMOV RULE 4)
        - END: All fixed
    """
    result = state.get("reviewfix_result", {})

    # Check ASIMOV RULE 4: Stuck after multiple attempts?
    fix_attempts = result.get("fix_attempts", 0)
    if fix_attempts >= 3:
        logger.warning("🛑 ReviewFix stuck after 3 attempts → HITL")
        return "hitl"

    # Check if fixes were applied
    if result.get("fixes_applied"):
        logger.info("✅ ReviewFix applied fixes")
        return END

    # If review found issues but can't fix
    if result.get("review_feedback") and not result.get("fixes_applied"):
        logger.warning("⚠️ ReviewFix can't auto-fix → HITL")
        return "hitl"

    # No issues found
    return END


def research_decide_next(state: SupervisorState) -> str:
    """
    Research decides next step.

    Returns:
        - "architect": Research done, proceed to design
        - "hitl": Can't find necessary info
    """
    result = state.get("research_result", {})

    # Check if research was successful
    if result.get("findings"):
        logger.info("✅ Research found information")
        return "architect"

    # No findings after research
    logger.warning("⚠️ Research found nothing → HITL")
    return "hitl"


def architect_decide_next(state: SupervisorState) -> str:
    """
    Architect decides next step.

    Returns:
        - "research": Need more technical details
        - "codesmith": Architecture ready
        - "hitl": Can't design (unclear requirements)
    """
    result = state.get("architect_result", {})

    # Check if design is complete
    if result.get("architecture_design"):
        confidence = result.get("confidence", 0.0)

        if confidence < 0.5:
            logger.warning("⚠️ Low confidence in design → need more research")
            return "research"

        logger.info("✅ Architecture complete")
        return "codesmith"

    # Can't create design
    logger.warning("⚠️ Architect can't design → HITL")
    return "hitl"
```

### 2. HITL Node

New node for Human-in-the-Loop:

```python
async def hitl_node(state: SupervisorState) -> dict[str, Any]:
    """
    Human-in-the-Loop node (ASIMOV RULE 4).

    This node is triggered when:
    - Agent is stuck after 3+ attempts
    - Agent can't complete task automatically
    - Critical decision required

    Sends request to user via WebSocket, waits for response.
    """
    logger.info("🛑 HITL: Requesting human intervention")

    # Determine what failed
    failed_agent = state.get("current_phase", "unknown")
    error = state.get("errors", ["Unknown error"])[-1]

    # Request human intervention via WebSocket
    if self.websocket_callback:
        hitl_request = {
            "type": "hitl_request",
            "agent": failed_agent,
            "error": error,
            "state": state,
            "suggestion": "Please provide guidance or corrections"
        }

        await self.websocket_callback(hitl_request)

        # Wait for human response (with timeout)
        response = await self._wait_for_hitl_response(timeout=600)  # 10 min

        if response["action"] == "retry":
            logger.info("👤 Human: Retry with new instructions")
            return {
                "hitl_response": response,
                "next_step": response.get("retry_agent", failed_agent)
            }

        elif response["action"] == "skip":
            logger.info("👤 Human: Skip this step")
            return {
                "hitl_response": response,
                "next_step": END
            }

        elif response["action"] == "abort":
            logger.info("👤 Human: Abort workflow")
            return {
                "hitl_response": response,
                "errors": ["User aborted workflow"]
            }

    # No WebSocket callback = can't continue
    logger.error("❌ No WebSocket callback for HITL")
    return {"errors": ["HITL required but no callback available"]}


def hitl_decide_next(state: SupervisorState) -> str:
    """Decide next step after HITL."""
    hitl_response = state.get("hitl_response", {})

    next_step = hitl_response.get("next_step")
    if next_step:
        return next_step

    return END
```

### 3. LangGraph Configuration

```python
# Create graph
graph = StateGraph(SupervisorState)

# Add ALL nodes
graph.add_node("supervisor", supervisor_node)
graph.add_node("research", research_node_wrapper)
graph.add_node("architect", architect_node_wrapper)
graph.add_node("codesmith", codesmith_node_wrapper)
graph.add_node("reviewfix", reviewfix_node_wrapper)
graph.add_node("hitl", hitl_node)  # NEW!

# Entry point
graph.set_entry_point("supervisor")

# Supervisor → Research (always start with research)
graph.add_edge("supervisor", "research")

# Research decides: architect OR hitl
graph.add_conditional_edges(
    "research",
    research_decide_next,
    {
        "architect": "architect",
        "hitl": "hitl"
    }
)

# Architect decides: codesmith OR research OR hitl
graph.add_conditional_edges(
    "architect",
    architect_decide_next,
    {
        "codesmith": "codesmith",
        "research": "research",  # Loop back if needed!
        "hitl": "hitl"
    }
)

# Codesmith decides: reviewfix OR research OR hitl OR END
graph.add_conditional_edges(
    "codesmith",
    codesmith_decide_next,
    {
        "reviewfix": "reviewfix",
        "research": "research",  # Can request more research!
        "hitl": "hitl",
        END: END
    }
)

# ReviewFix decides: codesmith OR hitl OR END
graph.add_conditional_edges(
    "reviewfix",
    reviewfix_decide_next,
    {
        "codesmith": "codesmith",  # Regenerate if needed
        "hitl": "hitl",
        END: END
    }
)

# HITL decides: Any agent OR END
graph.add_conditional_edges(
    "hitl",
    hitl_decide_next,
    {
        "research": "research",
        "architect": "architect",
        "codesmith": "codesmith",
        "reviewfix": "reviewfix",
        END: END
    }
)

# Compile
compiled = graph.compile(checkpointer=self.checkpointer)
```

---

## 📊 Flow Diagram

```
                    ┌─────────────┐
                    │  Supervisor │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
           ┌────────│   Research  │◄────────┐
           │        └──────┬──────┘         │
           │               │                │
           │               ▼                │
           │        ┌─────────────┐         │
           │   ┌────│  Architect  │─────┐   │
           │   │    └──────┬──────┘     │   │
           │   │           │            │   │
           │   │           ▼            │   │
           │   │    ┌─────────────┐    │   │
           │   │    │  Codesmith  │────┼───┘ (need more info)
           │   │    └──────┬──────┘    │
           │   │           │           │
           │   │           ▼           │
           │   │    ┌─────────────┐   │
           │   └───►│  ReviewFix  │   │
           │        └──────┬──────┘   │
           │               │          │
           │               ▼          │
           │        ┌─────────────┐   │
           └───────►│    HITL     │◄──┘ (stuck/error)
                    └──────┬──────┘
                           │
                           ▼
                        [ END ]
```

**Key Features:**
- ⭐ **Loops possible**: Research ↔ Architect, Codesmith → Research
- ⭐ **HITL on failures**: Any agent can escalate to HITL
- ⭐ **Smart decisions**: Each agent decides next step based on results
- ⭐ **No wasted work**: Skip agents if not needed

---

## 🎯 Implementation Steps

### Phase 1: Decision Functions (1 day)
- [ ] Implement `research_decide_next()`
- [ ] Implement `architect_decide_next()`
- [ ] Implement `codesmith_decide_next()`
- [ ] Implement `reviewfix_decide_next()`
- [ ] Add decision metadata to state results

### Phase 2: HITL Integration (1 day)
- [ ] Implement `hitl_node()`
- [ ] Implement `hitl_decide_next()`
- [ ] Add WebSocket HITL message type
- [ ] Add Extension UI for HITL requests
- [ ] Add timeout handling for HITL

### Phase 3: Conditional Edges (1 day)
- [ ] Replace `add_edge()` with `add_conditional_edges()`
- [ ] Test all possible paths
- [ ] Add cycle detection (prevent infinite loops)
- [ ] Add max iterations limit

### Phase 4: ASIMOV RULE 4 Integration (1 day)
- [ ] Add retry tracking to agent wrappers
- [ ] Integrate `validate_iteration_limit()` from asimov_rules.py
- [ ] Auto-escalate to HITL after 3 failures
- [ ] Track time spent per agent

### Phase 5: Testing (2 days)
- [ ] Test: Codesmith → Research → Codesmith flow
- [ ] Test: ReviewFix → HITL → Codesmith flow
- [ ] Test: Simple task (skip agents)
- [ ] Test: Complex task (all agents, loops)
- [ ] Test: HITL timeout
- [ ] Test: Infinite loop prevention

---

## 📝 Benefits

### Before (Linear):
```
Research → Architect → Codesmith → ReviewFix → END
```
- ❌ Always runs all agents (wasteful)
- ❌ Can't request more info mid-task
- ❌ No human intervention when stuck
- ❌ No intelligence

### After (Intelligent):
```
Dynamic flow based on:
- Task complexity
- Agent results
- Errors encountered
- Human decisions
```
- ✅ Only runs needed agents
- ✅ Agents can request more research
- ✅ HITL when stuck (ASIMOV RULE 4)
- ✅ Smart and efficient

---

## 🚀 Quick Win: Minimal Implementation

**Start with just Codesmith ↔ Research:**

```python
def codesmith_decide_next(state):
    result = state.get("codesmith_result", {})

    if result.get("needs_research"):
        return "research"
    if result.get("has_errors"):
        return "reviewfix"
    return END

graph.add_conditional_edges(
    "codesmith",
    codesmith_decide_next,
    {
        "research": "research",
        "reviewfix": "reviewfix",
        END: END
    }
)
```

**Test with:**
```
"Create Stripe payment integration with latest API v2024"
```

**Expected:**
1. Research → Initial Stripe docs
2. Architect → Payment design
3. Codesmith → Starts coding
   → "I need Stripe API v2024 specifics"
   → Calls Research again
4. Research → Gets v2024 docs
5. Back to Codesmith → Completes
6. ReviewFix → Checks
7. END

---

**Status:** DESIGN COMPLETE - Ready for implementation
**Estimated Work:** 5-7 days full implementation, 1 day for quick win
**Priority:** HIGH - This makes system truly intelligent!
