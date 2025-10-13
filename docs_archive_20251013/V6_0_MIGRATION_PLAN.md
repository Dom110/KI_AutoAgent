# KI AutoAgent v6.0 Direct Migration Plan

**Date:** 2025-10-08
**Strategy:** Direct jump from v5.9.0 → v6.0 (SKIP v5.9.2)
**Focus:** LangGraph Best Practices + Comprehensive Testing + Documentation

---

## 🎯 MISSION: v6.0 Direct Migration

### Core Principles (USER REQUIREMENTS):

1. ✅ **Python 3.13 ONLY** - No backwards compatibility
2. ✅ **Test EVERYTHING** - Every feature, every step
3. ✅ **Document EVERYTHING** - Single source of truth
4. ✅ **Clean Start** - Delete old docs, old tests
5. ✅ **Native Testing** - Test wie User es nutzen würde
6. ✅ **Debugging First** - Debugging tools from day 1

---

## 📋 PHASE 0: CLEANUP & PREPARATION (2-3h)

### 0.1 Delete Old Documentation

**Zu löschen:**
```bash
# Old version-specific docs (superseded)
rm V5_8_3_*.md
rm V5_8_4_*.md
rm V5_8_5_*.md
rm V5_8_6_*.md
rm V5_8_7_*.md
rm SESSION_SUMMARY_*.md
rm DETAILLIERTE_ZUSAMMENFASSUNG_*.md
rm FIXES_APPLIED_*.md
rm E2E_TEST_RESULTS_*.md
rm EVALUATION_COMPLEX_APP.md
rm REAL_VS_SIMULATION_ANALYSIS.md
rm PLAYWRIGHT_SUCCESS_REPORT.md
rm VIDEO_ANALYSIS_PLAN.md
rm ORCHESTRATOR_PATTERN_ANALYSIS.md
rm AI_SYSTEMS_STATUS_REPORT.md
rm CLEANUP_*.md
rm CODE_CLEANUP_*.md
rm FOLDER_ANALYSIS_*.md
rm test-*.md
rm RELEASE_NOTES_*.md (keep only latest v5.9.0)
rm MIGRATION_GUIDE_v4.md
rm V4_RELEASE_SUMMARY.md

# Keep ONLY:
# - README.md
# - CHANGELOG.md
# - CLAUDE.md
# - PYTHON_BEST_PRACTICES.md
# - SYSTEM_ARCHITECTURE_v5.9.0.md (als Referenz für Migration)
# - PERFORMANCE_OPTIMIZATION_REPORT_v5.9.0.md
# - ISSUES_AND_PLAN_v5.9.2.md (wird zu V6_0_MIGRATION_PLAN.md)
```

**Zu erstellen:**
```bash
# Master Documentation (NEW in v6.0)
MASTER_FEATURES_v6.0.md        # Single source of truth für Features
PROGRESS_TRACKER_v6.0.md        # Quick start für neue Chats
V6_0_ARCHITECTURE.md            # Neue Architektur Dokumentation
V6_0_MIGRATION_LOG.md           # Live log während Migration
V6_0_TEST_RESULTS.md            # Test results pro Phase
V6_0_KNOWN_ISSUES.md            # Was funktioniert NICHT und WARUM
```

### 0.2 Delete Old Tests

**Zu löschen:**
```bash
# Old test files (incompatible with v6.0)
rm -rf backend/tests/test_*.py (alle alten)
rm -rf backend/tests/fixtures/old_*

# Keep structure:
backend/tests/
  ├─ __init__.py
  └─ README.md (Test strategy documentation)
```

**Neu erstellen:**
```bash
backend/tests/
  ├─ v6/                              # v6.0 specific tests
  │   ├─ test_routing_v6.py           # Routing logic (CRITICAL!)
  │   ├─ test_subgraphs.py            # Subgraph architecture
  │   ├─ test_templates.py            # LangGraph templates
  │   ├─ test_checkpointer.py         # AsyncSqliteSaver
  │   └─ integration/
  │       ├─ test_full_workflow.py    # End-to-end workflows
  │       ├─ test_memory_system.py    # Memory, Asimov, etc.
  │       └─ test_all_features.py     # EVERY feature
  ├─ fixtures/
  │   ├─ routing/                     # Golden files für routing
  │   ├─ workflows/                   # Expected workflow outputs
  │   └─ test_apps/                   # Test apps (calculator, react)
  └─ conftest.py                      # Pytest configuration
```

### 0.3 Git Strategy

```bash
# Current: main branch (v5.9.0)

# Step 1: Create v6.0-alpha branch
git checkout -b v6.0-alpha

# Step 2: Cleanup commit
git add .
git commit -m "chore(v6.0): Cleanup old docs and tests

- Removed superseded version-specific documentation
- Removed incompatible v5.x tests
- Prepared clean slate for v6.0 migration
- Created v6.0 documentation structure

Breaking changes expected - this is alpha development branch"

git push -u origin v6.0-alpha

# Step 3: Update version
# backend/version.json: "6.0.0-alpha.1"
# vscode-extension/package.json: "6.0.0-alpha"
```

**Duration:** 2-3 Stunden

---

## 📋 PHASE 1: DOCUMENTATION FOUNDATION (2-3h)

### 1.1 Create Master Documentation

**File: `MASTER_FEATURES_v6.0.md`**

Structure:
```markdown
# KI AutoAgent - Master Features v6.0

## 1. IMPLEMENTED FEATURES
### 1.1 Core System
- Multi-Agent Workflow (v6.0: Subgraphs)
- LangGraph State Management
- WebSocket Communication
- [... complete list ...]

### 1.2 Specialized Agents
- Architect Agent (v6.0: Custom, not create_react_agent)
- Codesmith Agent (v6.0: create_react_agent + file_tools)
- Reviewer Agent (v6.0: create_react_agent + browser_tester)
- Fixer Agent (v6.0: create_react_agent + file_tools)
- Research Agent (v6.0: create_react_agent + perplexity_tool)
- [... complete list ...]

### 1.3 Advanced Features (TO TEST EVERY PHASE!)
- ✅ Agent Memory (SQLite + FAISS Vector Store)
- ✅ Asimov Rules (MUST be enforced)
- ✅ Tree-Sitter Code Parsing
- ✅ Graph Visualization
- ✅ Markdown Documentation Generation
- ✅ Learning System (Cross-session)
- ✅ Curiosity System
- ✅ Agentic RAG
- ✅ Neurosymbolic Reasoning
- ✅ Self-Diagnosis System
- ✅ Tool Discovery & Registry
- [... complete list ...]

## 2. v6.0 ARCHITECTURE CHANGES
### 2.1 From execution_plan to Subgraphs
### 2.2 From custom BaseAgent to create_react_agent()
### 2.3 From MemorySaver to AsyncSqliteSaver
### 2.4 From imperative to declarative routing

## 3. TECHNICAL DEBT ELIMINATED
- ❌ execution_plan (replaced by Graph structure)
- ❌ route_to_next_agent() (replaced by Subgraph routing)
- ❌ Manual state manipulation (replaced by Graph edges)

## 4. TESTING REQUIREMENTS (EVERY PHASE!)
- Test Workflow execution
- Test Memory creation & retrieval
- Test Asimov rule enforcement
- Test Tree-Sitter parsing
- Test Graph generation
- Test Markdown docs
- Test Learning system
- [... complete list ...]
```

**File: `PROGRESS_TRACKER_v6.0.md`**

Structure:
```markdown
# KI AutoAgent - Progress Tracker v6.0
**For New Claude Sessions - Quick Start Guide**

## CURRENT STATUS (Live Updated!)

### Version Info
- Backend: v6.0.0-alpha.X (in development)
- Frontend: v6.0.0-alpha (in development)
- Branch: v6.0-alpha
- Last Updated: [AUTO-GENERATED DATE]

### What Works ✅
[UPDATED AFTER EACH PHASE]

### Known Issues 🐛
[DOCUMENTED IN V6_0_KNOWN_ISSUES.md]

### In Progress ⏳
[CURRENT PHASE]

### Architecture Quick Reference
- Main File: backend/langgraph_system/workflow_v6.py (new!)
- Subgraphs: backend/langgraph_system/subgraphs/
- State: backend/langgraph_system/state_v6.py
- Tests: backend/tests/v6/

### Common Tasks
1. Start backend: ~/.ki_autoagent/start.sh
2. View logs: tail -f ~/.ki_autoagent/logs/backend.log
3. Run tests: pytest backend/tests/v6/
4. Debug: See V6_0_DEBUGGING.md

### FOR NEW CHAT SESSIONS
1. Read this document (you are here!)
2. Check V6_0_MIGRATION_LOG.md for latest changes
3. Check V6_0_KNOWN_ISSUES.md for current problems
4. Check MASTER_FEATURES_v6.0.md for all features
```

**File: `V6_0_ARCHITECTURE.md`**

Structure:
```markdown
# KI AutoAgent v6.0 Architecture

## Subgraph Structure

```
SupervisorGraph (Orchestrator)
├─ Input: user_query, workspace_path
├─ Output: final_result
│
├─ ResearchSubgraph
│  ├─ Input: research_query
│  ├─ Output: research_results, citations
│  └─ Agent: create_react_agent(perplexity_tool)
│
├─ ArchitectSubgraph
│  ├─ Input: requirements, research_results
│  ├─ Output: architecture_design, tech_stack
│  └─ Agent: Custom (too specialized for template)
│
├─ CodesmithSubgraph
│  ├─ Input: architecture_design
│  ├─ Output: generated_files[]
│  └─ Agent: create_react_agent(file_tools)
│
└─ ReviewFixSubgraph (Loop)
   ├─ ReviewerNode
   │  ├─ Input: generated_files
   │  ├─ Output: quality_score, issues[]
   │  └─ Agent: create_react_agent(browser_tester)
   │
   ├─ FixerNode
   │  ├─ Input: issues[]
   │  ├─ Output: fixed_files[]
   │  └─ Agent: create_react_agent(file_tools)
   │
   └─ Loop Condition: quality_score >= 0.8 OR iterations >= 3
```

## State Schemas

### SupervisorState
### ResearchState
### ArchitectState
### CodesmithState
### ReviewFixState

[... detailed schemas ...]

## Routing Logic

[... declarative edge definitions ...]
```

**File: `V6_0_MIGRATION_LOG.md`**

Structure:
```markdown
# v6.0 Migration Log

**Live log of all changes during migration**

## 2025-10-08 18:00 - Phase 0: Cleanup
- ✅ Deleted old documentation (V5_8_*.md, etc.)
- ✅ Deleted old tests
- ✅ Created v6.0-alpha branch
- ✅ Updated version to 6.0.0-alpha.1
- 🐛 Issues: None yet
- ⏭️  Next: Phase 1 Documentation

## 2025-10-08 20:00 - Phase 1: Documentation
- ✅ Created MASTER_FEATURES_v6.0.md
- ✅ Created PROGRESS_TRACKER_v6.0.md
- ✅ Created V6_0_ARCHITECTURE.md
- 🐛 Issues: None
- ⏭️  Next: Phase 2 AsyncSqliteSaver

[... continues with each phase ...]
```

**File: `V6_0_KNOWN_ISSUES.md`**

Structure:
```markdown
# v6.0 Known Issues

**What doesn't work and WHY**

## CRITICAL (Blockers)
[Empty at start, updated during migration]

## HIGH (Broken features)
[Updated during testing]

## MEDIUM (Partial functionality)
[Updated during testing]

## LOW (Minor issues)
[Updated during testing]

## RESOLVED
[Moved here when fixed]

---

## Example Entry:

### Issue #1: Memory System Not Creating Embeddings
**Status:** 🔴 CRITICAL
**Discovered:** Phase 3, 2025-10-08 22:00
**Symptom:** Agent memory query returns empty results
**Root Cause:** FAISS vector store not initialized in Subgraph state
**Fix Attempted:** [describe attempts]
**Workaround:** [if any]
**Source Reference:** backend/langgraph_system/subgraphs/research_subgraph.py:145
**Resolution:** [when fixed]
```

**File: `V6_0_DEBUGGING.md`**

Structure:
```markdown
# v6.0 Debugging Guide

## Debug Mode Activation

### Backend Debug Mode
```bash
# Set in .env
DEBUG=true
LOG_LEVEL=DEBUG

# Or at runtime
export DEBUG=true
export LOG_LEVEL=DEBUG
~/.ki_autoagent/start.sh
```

### VS Code Extension Debug Mode
```typescript
// In MultiAgentChatPanel.ts
private debugMode = true; // Enable verbose logging
```

## Debugging Tools

### 1. Interactive Debugging (Python)
```python
# Add breakpoints in code
import pdb; pdb.set_trace()

# Or use ipdb (better)
pip install ipdb
import ipdb; ipdb.set_trace()
```

### 2. LangGraph Studio (Visual Debugger)
```bash
# Install LangGraph Studio
pip install langgraph-studio

# Run
langgraph-studio backend/langgraph_system/workflow_v6.py
```

### 3. Log Analysis
```bash
# Real-time log watching
tail -f ~/.ki_autoagent/logs/backend.log | grep ERROR

# Search for specific agent
grep "CODESMITH" ~/.ki_autoagent/logs/backend.log

# Count routing decisions
grep "🔀" ~/.ki_autoagent/logs/backend.log | wc -l
```

### 4. Test WebSocket Client
```python
# backend/tests/tools/test_websocket_client.py
import asyncio
import websockets
import json

async def test_workflow():
    uri = "ws://localhost:8001/ws/chat"
    async with websockets.connect(uri) as websocket:
        # Init
        await websocket.send(json.dumps({
            "type": "init",
            "workspace_path": "/Users/.../test-workspace"
        }))

        # Send message
        await websocket.send(json.dumps({
            "type": "chat",
            "message": "Create a calculator app"
        }))

        # Receive responses
        while True:
            response = await websocket.recv()
            print(json.dumps(json.loads(response), indent=2))

asyncio.run(test_workflow())
```

### 5. State Inspection
```python
# Add to workflow_v6.py
def debug_state(state: SupervisorState):
    import json
    print("=" * 80)
    print("STATE SNAPSHOT:")
    print(json.dumps({
        "current_subgraph": state.get("current_subgraph"),
        "subgraph_states": {k: str(v)[:100] for k, v in state.get("subgraph_states", {}).items()},
        "errors": state.get("errors", []),
    }, indent=2))
    print("=" * 80)
    return state

# Use in graph
workflow.add_node("debug", debug_state)
```

## Common Issues & Solutions

### Issue: "Subgraph not found"
**Symptom:** KeyError when routing to subgraph
**Debug:** Check AVAILABLE_SUBGRAPHS dict
**Fix:** Ensure subgraph registered in workflow

### Issue: "Memory not persisting"
**Symptom:** Agent forgets context between runs
**Debug:** Check ~/.ki_autoagent/data/embeddings/
**Fix:** Verify PersistentAgentMemory initialization

[... more common issues ...]
```

**Duration:** 2-3 Stunden

---

## 📋 PHASE 2: ASYNC SQLITE SAVER (FOUNDATION) (2-3h)

### 2.1 Implementation

**File:** `backend/langgraph_system/workflow_v6.py` (NEW FILE!)

```python
"""
v6.0 Workflow - Clean Implementation
Source: V6_0_ARCHITECTURE.md
"""

from __future__ import annotations
import asyncio
import logging
from datetime import datetime
from typing import Any

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import StateGraph, END
import aiosqlite
import os

from .state_v6 import SupervisorState, create_initial_state
from .subgraphs import research_subgraph, architect_subgraph, codesmith_subgraph, reviewfix_subgraph

logger = logging.getLogger(__name__)


class WorkflowV6:
    """
    v6.0 Supervisor Workflow

    Architecture: Subgraphs with AsyncSqliteSaver
    Documentation: V6_0_ARCHITECTURE.md
    Testing: tests/v6/test_workflow_v6.py
    """

    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self.checkpointer = None  # Initialized in compile()

    async def compile_workflow(self):
        """Initialize AsyncSqliteSaver and compile workflow"""
        # v6.0: AsyncSqliteSaver FIRST (foundation)
        db_path = os.path.join(
            self.workspace_path,
            ".ki_autoagent_ws/cache/workflow_checkpoints_v6.db"
        )
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        try:
            conn = await aiosqlite.connect(db_path)
            self.checkpointer = AsyncSqliteSaver(conn)
            logger.info(f"✅ AsyncSqliteSaver initialized: {db_path}")
        except Exception as e:
            logger.error(f"❌ AsyncSqliteSaver failed: {e}")
            raise

        # Create workflow
        workflow = self.create_workflow()

        # Compile with checkpointer
        self.workflow = workflow.compile(checkpointer=self.checkpointer)
        logger.info("✅ Workflow v6.0 compiled")

    def create_workflow(self) -> StateGraph:
        """Create supervisor workflow graph"""
        workflow = StateGraph(SupervisorState)

        # Add supervisor node
        workflow.add_node("supervisor", self.supervisor_node)

        # Entry point
        workflow.set_entry_point("supervisor")

        # For now: simple flow to test AsyncSqliteSaver
        workflow.add_edge("supervisor", END)

        return workflow

    async def supervisor_node(self, state: SupervisorState) -> dict[str, Any]:
        """Supervisor orchestration logic"""
        logger.info("🎯 Supervisor node executing")

        # For Phase 2: Just test checkpointing
        return {
            "final_result": "Phase 2: AsyncSqliteSaver works!",
            "status": "completed"
        }
```

**File:** `backend/langgraph_system/state_v6.py` (NEW FILE!)

```python
"""
v6.0 State Schemas
Source: V6_0_ARCHITECTURE.md
"""

from __future__ import annotations
from typing import TypedDict, Annotated, Any
import operator
from datetime import datetime


class SupervisorState(TypedDict):
    """Supervisor graph state"""
    # Input
    user_query: str
    workspace_path: str
    client_id: str
    session_id: str

    # Subgraph states
    research_results: dict[str, Any] | None
    architecture_design: dict[str, Any] | None
    generated_files: list[dict[str, Any]]
    review_feedback: dict[str, Any] | None

    # Workflow control
    current_subgraph: str | None
    status: str  # initializing, executing, completed, failed

    # Results
    final_result: Any | None
    errors: Annotated[list[dict[str, Any]], operator.add]

    # Timestamps
    start_time: datetime
    end_time: datetime | None


def create_initial_state(
    user_query: str,
    workspace_path: str,
    client_id: str,
    session_id: str
) -> SupervisorState:
    """Create initial supervisor state"""
    return SupervisorState(
        user_query=user_query,
        workspace_path=workspace_path,
        client_id=client_id,
        session_id=session_id,
        research_results=None,
        architecture_design=None,
        generated_files=[],
        review_feedback=None,
        current_subgraph=None,
        status="initializing",
        final_result=None,
        errors=[],
        start_time=datetime.now(),
        end_time=None
    )
```

### 2.2 Testing (COMPREHENSIVE!)

**File:** `backend/tests/v6/test_checkpointer.py`

```python
"""
v6.0 Checkpointer Tests
Tests AsyncSqliteSaver functionality
"""

import pytest
import asyncio
import os
import tempfile
from backend.langgraph_system.workflow_v6 import WorkflowV6
from backend.langgraph_system.state_v6 import create_initial_state


@pytest.mark.asyncio
async def test_checkpointer_initialization():
    """Test: AsyncSqliteSaver initializes correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workflow = WorkflowV6(workspace_path=tmpdir)
        await workflow.compile_workflow()

        # Check DB file exists
        db_path = os.path.join(tmpdir, ".ki_autoagent_ws/cache/workflow_checkpoints_v6.db")
        assert os.path.exists(db_path), "Checkpoint DB not created"

        # Check checkpointer is set
        assert workflow.checkpointer is not None, "Checkpointer not initialized"


@pytest.mark.asyncio
async def test_checkpoint_persistence():
    """Test: State persists across workflow runs"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workflow = WorkflowV6(workspace_path=tmpdir)
        await workflow.compile_workflow()

        # Create initial state
        state = create_initial_state(
            user_query="Test query",
            workspace_path=tmpdir,
            client_id="test-client",
            session_id="test-session"
        )

        # Run workflow
        result = await workflow.workflow.ainvoke(
            state,
            config={"configurable": {"thread_id": "test-thread"}}
        )

        # Check result
        assert result["final_result"] == "Phase 2: AsyncSqliteSaver works!"
        assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_checkpoint_resume_after_interruption():
    """Test: Workflow resumes from checkpoint after interruption"""
    # TODO: Implement after Phase 3 (when we have multi-step workflow)
    pass


def test_checkpoint_cleanup():
    """Test: Old checkpoints can be cleaned up"""
    # TODO: Implement checkpoint cleanup utility
    pass
```

### 2.3 Native Testing (User Perspective)

**File:** `backend/tests/tools/native_test_client.py`

```python
"""
Native Testing Client
Simulates user interaction via WebSocket
"""

import asyncio
import websockets
import json
import sys


async def test_basic_workflow():
    """Test: Basic workflow execution"""
    print("🧪 Starting native test: Basic workflow")

    uri = "ws://localhost:8001/ws/chat"

    try:
        async with websockets.connect(uri) as websocket:
            # Step 1: Init
            print("📤 Sending init message...")
            await websocket.send(json.dumps({
                "type": "init",
                "workspace_path": "/Users/dominikfoert/Desktop/test-v6-native"
            }))

            response = await websocket.recv()
            init_response = json.loads(response)
            print(f"📥 Init response: {init_response}")

            assert init_response["type"] == "initialized", "Init failed"

            # Step 2: Send query
            print("📤 Sending chat message...")
            await websocket.send(json.dumps({
                "type": "chat",
                "message": "Test AsyncSqliteSaver"
            }))

            # Step 3: Collect responses
            while True:
                response = await websocket.recv()
                message = json.loads(response)
                print(f"📥 {message['type']}: {message.get('text', message)}")

                if message["type"] == "completed":
                    print("✅ Workflow completed")
                    break
                elif message["type"] == "error":
                    print(f"❌ Error: {message}")
                    sys.exit(1)

    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)

    print("✅ Native test passed!")


if __name__ == "__main__":
    asyncio.run(test_basic_workflow())
```

**Usage:**
```bash
# Terminal 1: Start backend
cd ~/.ki_autoagent && ./start.sh

# Terminal 2: Run native test
python backend/tests/tools/native_test_client.py
```

### 2.4 Testing Checklist (Phase 2)

```markdown
## Phase 2 Testing Checklist

### Unit Tests
- [ ] test_checkpointer_initialization() passes
- [ ] test_checkpoint_persistence() passes
- [ ] Checkpoint DB file created in correct location
- [ ] No Python < 3.13 code warnings

### Integration Tests
- [ ] Backend starts without errors
- [ ] WebSocket connection established
- [ ] Init message accepted
- [ ] Chat message processed
- [ ] Checkpoint saved to DB

### Native Tests
- [ ] native_test_client.py runs successfully
- [ ] User perspective workflow works
- [ ] All responses logged correctly

### Feature Tests (CRITICAL!)
- [ ] ⚠️ Memory System: NOT TESTED YET (Phase 3)
- [ ] ⚠️ Asimov Rules: NOT TESTED YET (Phase 3)
- [ ] ⚠️ Tree-Sitter: NOT TESTED YET (Phase 3)
- [ ] ⚠️ Graphs: NOT TESTED YET (Phase 3)
- [ ] ⚠️ Markdown: NOT TESTED YET (Phase 3)
- [ ] ⚠️ Learning: NOT TESTED YET (Phase 3)
- [ ] ✅ AsyncSqliteSaver: TESTED ✅

### Documentation
- [ ] V6_0_MIGRATION_LOG.md updated
- [ ] V6_0_KNOWN_ISSUES.md updated (if issues found)
- [ ] Source code commented with references
- [ ] Test results documented in V6_0_TEST_RESULTS.md
```

**Duration:** 2-3 Stunden

---

## 📋 REMAINING PHASES (OVERVIEW)

### PHASE 3: Research Subgraph + create_react_agent() (4-6h)
- Implement ResearchSubgraph with create_react_agent()
- Add Perplexity tool
- **TEST FEATURES:** Memory (FAISS), Asimov, Learning
- Native testing with actual research queries
- Update all documentation

### PHASE 4: Architect Subgraph (Custom Agent) (3-4h)
- Implement ArchitectSubgraph (custom, not template)
- **TEST FEATURES:** Tree-Sitter parsing, Markdown generation
- Native testing with architecture design
- Update all documentation

### PHASE 5: Codesmith Subgraph + create_react_agent() (4-6h)
- Implement CodesmithSubgraph with create_react_agent()
- Add file_tools
- **TEST FEATURES:** File creation, Graph generation
- Native testing with code generation
- Update all documentation

### PHASE 6: ReviewFix Subgraph + Loop (6-8h)
- Implement ReviewFixSubgraph (Reviewer + Fixer loop)
- Both use create_react_agent()
- **TEST FEATURES:** Browser testing, Quality scoring
- Native testing with review-fix cycles
- **CRITICAL:** Test max iterations (no infinite loops!)
- Update all documentation

### PHASE 7: Supervisor Integration (4-6h)
- Connect all subgraphs
- Implement supervisor routing logic
- **TEST FEATURES:** ALL features together!
- Native testing with complete workflows
- Update all documentation

### PHASE 8: End-to-End Testing (8-10h)
- Test Calculator App (simple)
- Test React App (complex)
- Test ALL advanced features:
  - Memory creation & retrieval
  - Asimov rule enforcement
  - Tree-Sitter parsing
  - Graph visualization
  - Markdown documentation
  - Learning system
  - Curiosity system
  - Agentic RAG
  - Neurosymbolic reasoning
  - Self-diagnosis
  - Tool discovery
- Performance benchmarks
- Update all documentation

### PHASE 9: Frontend Integration (3-4h)
- Update VS Code extension for v6.0
- Test WebSocket protocol
- Update UI for subgraph progress
- Native testing from VS Code
- Update all documentation

### PHASE 10: Final Polish & Release (4-6h)
- Final documentation review
- CHANGELOG.md update
- README.md update
- Create v6.0.0 release
- Migration guide for users

---

## 🎯 TOTAL ESTIMATED TIME

**Core Development:** 40-60 hours
**Testing (comprehensive!):** +30-40 hours
**Documentation:** +15-20 hours

**TOTAL:** 85-120 hours (~2-3 Wochen full-time)

---

## 📊 TESTING REQUIREMENTS (EVERY PHASE!)

### Feature Test Matrix

| Feature | Phase Tested | Test Method | Status |
|---------|--------------|-------------|--------|
| AsyncSqliteSaver | 2 | Unit + Native | ⏳ |
| Memory System | 3 | Unit + Native | ⏳ |
| Asimov Rules | 3 | Unit + Native | ⏳ |
| Tree-Sitter | 4 | Unit + Native | ⏳ |
| Graphs | 5 | Unit + Native | ⏳ |
| Markdown | 4 | Unit + Native | ⏳ |
| Learning | 3 | Unit + Native | ⏳ |
| Curiosity | 8 | Integration | ⏳ |
| Agentic RAG | 8 | Integration | ⏳ |
| Neurosymbolic | 8 | Integration | ⏳ |
| Self-Diagnosis | 8 | Integration | ⏳ |
| Tool Discovery | 7 | Integration | ⏳ |

---

## 🚀 APPROVAL REQUIRED

**Bereit zum Start?**

**Phase 0 (JETZT):**
- Cleanup alte Docs
- Cleanup alte Tests
- Git branch erstellen
- Neue Docs erstellen

**Phase 2 (DANN):**
- AsyncSqliteSaver implementieren
- Tests schreiben (unit + native)
- Alles testen
- Dokumentieren

**Danach:**
- Phase für Phase
- Jede Phase komplett testen
- Jede Phase dokumentieren
- Keine Phase ohne alle Features getestet!

**Soll ich starten?**
