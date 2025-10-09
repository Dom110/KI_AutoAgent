# v6 Implementation Roadmap - Complete Feature List & Test Plan

**Document Purpose:** Complete handover for next session
**Created:** 2025-10-09
**Current Status:** Iterations 0-2 complete, 11 systems pending
**Next Session Goal:** Continue systematic implementation of missing features

---

## 📊 SYSTEM STATUS OVERVIEW

### ✅ Production Ready (Iterations 0-2 Complete)

**Core Workflow:** Research → Architect → Codesmith → ReviewFix → END
**Execution Time:** 49.1s
**Quality Score:** 0.90 (threshold: 0.75)
**Code Quality:** All validations passing
**Test Evidence:** Calculator app generated and runs successfully

**Key Metrics:**
- Memory cross-agent communication: ✅ Working (3256 chars context loaded)
- File generation: ✅ Working (5 files, 13565 bytes)
- Tree-sitter validation: ✅ Working (9% overhead)
- Asimov security: ✅ Working (12% overhead)
- Generated code quality: ✅ Runs without errors

---

## 📋 COMPLETE FEATURE INVENTORY

### ✅ IMPLEMENTED FEATURES (Iterations 0-2)

#### 1. **Core Workflow Engine** ✅
- **Status:** COMPLETE
- **Files:**
  - `backend/server_v6.py` (WebSocket server)
  - `backend/workflow_v6.py` (LangGraph supervisor)
  - `backend/state_v6.py` (State schemas)
- **Capabilities:**
  - Multi-client WebSocket server
  - Per-session workflow instances
  - Declarative task routing
  - AsyncSqliteSaver checkpointing
- **Test Evidence:** All 4 tests pass (Iterations 0-2)
- **Performance:** 40.1s baseline execution

#### 2. **Research Agent** ✅
- **Status:** COMPLETE (Perplexity stub, needs real API)
- **Files:**
  - `backend/subgraphs/research_subgraph_v6_1.py`
  - `backend/tools/perplexity_tool.py`
- **Capabilities:**
  - Async Claude Sonnet 4 integration
  - Memory storage (findings → vector store)
  - Error handling (no auto-fallback)
- **Current Behavior:** Returns error if PERPLEXITY_API_KEY missing (correct!)
- **Test Evidence:** Fails properly when API unavailable

#### 3. **Architect Agent** ✅
- **Status:** COMPLETE
- **Files:** `backend/subgraphs/architect_subgraph_v6_1.py`
- **Capabilities:**
  - GPT-4o design generation
  - Memory read (research findings)
  - Memory write (architecture design)
  - Cross-agent context loading
- **Test Evidence:** Generates 1531 char design, Calculator class structure
- **Performance:** ~15s per design

#### 4. **Codesmith Agent** ✅
- **Status:** COMPLETE
- **Files:** `backend/subgraphs/codesmith_subgraph_v6_1.py`
- **Capabilities:**
  - Claude Sonnet 4 code generation
  - FILE: format parsing
  - Multi-file generation
  - Memory read (research + design)
  - Memory write (implementation summary)
- **Validation Pipeline:**
  1. Parse FILE: format
  2. Tree-sitter syntax validation
  3. Asimov security validation
  4. Write file (only if all pass)
- **Test Evidence:**
  - Generated calculator.py (4481 bytes)
  - Syntax valid (Python parser)
  - Asimov rules passed
  - Code runs successfully
- **Performance:** ~20s generation + ~5s validation

#### 5. **ReviewFix Agent** ✅
- **Status:** COMPLETE
- **Files:** `backend/subgraphs/reviewfix_subgraph_v6_1.py`
- **Capabilities:**
  - GPT-4o-mini code review
  - Quality scoring (0.0-1.0)
  - Max 3 iterations
  - Threshold: 0.75
  - Reads generated_files from state
  - Provides feedback for improvements
- **Test Evidence:**
  - Quality score: 0.90 (above threshold)
  - Completes in 1 iteration
  - Workflow ends successfully
- **Performance:** ~8s per review

#### 6. **Memory System** ✅
- **Status:** COMPLETE
- **Files:**
  - `backend/memory/memory_v6.py`
  - `backend/memory/vector_store.py`
- **Capabilities:**
  - FAISS vector embeddings (384-dim)
  - SQLite metadata storage
  - Async store/search/update operations
  - Per-agent filtering
  - Cross-agent context sharing
- **Test Evidence:**
  - Research stores → Architect reads → Codesmith reads
  - 3 items stored (1 per agent)
  - Context loaded: 3256 chars
- **Storage:** `{workspace}/.ki_autoagent_ws/memory/`

#### 7. **Tree-sitter Validation** ✅ (Iteration 1)
- **Status:** COMPLETE
- **Files:** `backend/tools/tree_sitter_tools.py`
- **Capabilities:**
  - Multi-language parsing (Python, JavaScript, TypeScript)
  - Syntax validation before file writing
  - Error node detection
  - Language auto-detection from file extension
  - Graceful fallback (non-code files written without validation)
- **Integration:** Codesmith subgraph (lines 183-213)
- **Test Evidence:**
  - Valid code: ✅ ACCEPTED (calculator.py)
  - Invalid code: ❌ REJECTED (missing colons, unclosed parens)
  - Performance: +3.6s overhead (9%)

#### 8. **Asimov Security Rules** ✅ (Iteration 2)
- **Status:** COMPLETE (Rules 1 & 2 enforced at file level)
- **Files:**
  - `backend/security/asimov_rules.py`
  - `.kiautoagent/docs/ASIMOV_RULES.md`
- **Capabilities:**
  - Rule 1: NO FALLBACKS without `# ⚠️ FALLBACK:` comment
  - Rule 2: COMPLETE IMPLEMENTATION (no TODO/FIXME/pass/NotImplementedError)
  - Rule 3: GLOBAL ERROR SEARCH (workflow level, not yet implemented)
  - Regex pattern detection
  - Severity levels (error vs warning)
  - Violation reporting with line numbers
- **Integration:** Codesmith subgraph (lines 214-241)
- **Test Evidence:**
  - Calculator.py: ✅ No violations
  - Invalid code: ❌ Blocked with detailed report
  - Performance: +5.4s overhead (12%)

#### 9. **File Tools** ✅
- **Status:** COMPLETE
- **Files:** `backend/tools/file_tools.py`
- **Capabilities:**
  - Async read_file (with workspace_path parameter)
  - Async write_file (with workspace_path parameter)
  - Directory creation
  - Path validation
- **Test Evidence:** All files written successfully to workspace

#### 10. **Claude CLI Integration** ✅
- **Status:** COMPLETE
- **Files:** `backend/adapters/claude_cli_simple.py`
- **Capabilities:**
  - 100% Claude CLI (no Anthropic SDK)
  - Async-only compatibility
  - Streaming support
  - Error handling
- **Models Used:**
  - Research: claude-sonnet-4-20250514
  - Codesmith: claude-sonnet-4-20250514
- **Test Evidence:** All Claude agents working

---

### ❌ MISSING FEATURES (v5 Systems Not Yet Ported)

#### 11. **Perplexity API Integration** ❌
- **Status:** STUB (returns error)
- **Priority:** 🔴 CRITICAL
- **Effort:** 3-4 hours
- **Files:** `backend/tools/perplexity_tool.py` (lines 65-73)
- **Current Behavior:** Returns `{"error": "not_implemented"}`
- **Required:**
  - Real Perplexity Sonar API call
  - API key from `PERPLEXITY_API_KEY` env var
  - Response parsing (answer + sources)
  - Error handling (rate limits, timeouts)
  - NO auto-fallback (per user requirement)
- **Dependencies:**
  - Perplexity API key
  - `perplexity` or `httpx` library
- **Integration:** Research subgraph uses this tool
- **Test Specification:** (see TEST PLAN section below)

#### 12. **Asimov Rule 3: Global Error Search** ❌
- **Status:** DEFINED (not enforced)
- **Priority:** 🔴 CRITICAL
- **Effort:** 6-7 hours
- **Files:**
  - `backend/security/asimov_rules.py` (add new function)
  - `backend/workflow_v6.py` (add global search step)
- **Required:**
  - Workflow-level error detection
  - `ripgrep` integration for pattern search
  - Error aggregation across all files
  - Fix all instances, not just one
- **Documentation:** `.kiautoagent/docs/ASIMOV_RULES.md` (lines 64-96)
- **Implementation:**
  ```python
  async def perform_global_error_search(workspace_path: str, error: str):
      """
      When an error is found, search entire workspace for similar patterns.
      Returns: list of (file, line, match) tuples
      """
      # Use ripgrep to find all instances
      # Return aggregated results
  ```
- **Integration:** After ReviewFix, before workflow END
- **Test Specification:** (see TEST PLAN section)

#### 13. **Learning System** ❌
- **Status:** NOT IMPLEMENTED
- **Priority:** 🟡 HIGH
- **Effort:** 8-10 hours
- **Files (v5):**
  - `backend/cognitive_architecture/learning_system.py`
  - `backend/cognitive_architecture/learning_service.py`
- **Capabilities (v5):**
  - Pattern learning from workflow outcomes
  - Strategy adaptation
  - Feedback storage (success/failure)
  - Performance tracking
- **Required for v6:**
  - Port to async
  - Integrate with Memory System v6
  - Track workflow metrics (execution time, quality scores)
  - Store learnings per project type
  - Suggest improvements based on history
- **Integration:** Post-workflow analysis step
- **Test Specification:** (see TEST PLAN section)

#### 14. **Curiosity System** ❌
- **Status:** NOT IMPLEMENTED
- **Priority:** 🟡 HIGH
- **Effort:** 4-5 hours
- **Files (v5):** `backend/cognitive_architecture/curiosity_system.py`
- **Capabilities (v5):**
  - Identify knowledge gaps
  - Generate clarifying questions
  - Proactive context gathering
- **Required for v6:**
  - Integrate with Research agent
  - Memory-based gap detection
  - Async question generation
  - User prompt for clarifications
- **Integration:** Before Architect design (gather missing requirements)
- **Test Specification:** (see TEST PLAN section)

#### 15. **Predictive System** ❌
- **Status:** NOT IMPLEMENTED
- **Priority:** 🟡 HIGH
- **Effort:** 3-4 hours
- **Files (v5):** `backend/cognitive_architecture/predictive_system.py`
- **Capabilities (v5):**
  - Predict workflow duration
  - Anticipate potential issues
  - Suggest preventive actions
- **Required for v6:**
  - Integrate with Learning System
  - Predict based on task complexity
  - Memory-based pattern matching
  - Pre-workflow risk assessment
- **Integration:** Before workflow start (in Supervisor)
- **Test Specification:** (see TEST PLAN section)

#### 16. **Tool Registry** ❌
- **Status:** NOT IMPLEMENTED
- **Priority:** 🟢 MEDIUM
- **Effort:** 5-6 hours
- **Files (v5):** `backend/tools/tool_registry.py`
- **Capabilities (v5):**
  - Dynamic tool discovery
  - Tool versioning
  - Tool metadata (descriptions, parameters)
  - Tool validation
- **Required for v6:**
  - Async tool loading
  - Per-agent tool assignment
  - Tool capability matching
  - Runtime tool registration
- **Integration:** Agent initialization
- **Test Specification:** (see TEST PLAN section)

#### 17. **Approval Manager** ❌
- **Status:** NOT IMPLEMENTED
- **Priority:** 🟢 MEDIUM
- **Effort:** 4-5 hours
- **Files (v5):** `backend/review/approval_manager.py`
- **Capabilities (v5):**
  - User approval gates
  - Critical action blocking
  - Approval history
- **Required for v6:**
  - WebSocket approval prompts
  - Async approval wait
  - Configurable approval rules
  - File write approvals
  - Deployment approvals
- **Integration:** Before write_file, before deployment
- **Test Specification:** (see TEST PLAN section)

#### 18. **Dynamic Workflow** ❌
- **Status:** NOT IMPLEMENTED
- **Priority:** 🟢 MEDIUM
- **Effort:** 1-2 hours
- **Files (v5):** `backend/langgraph_system/dynamic_workflow.py`
- **Capabilities (v5):**
  - Workflow modification at runtime
  - Conditional agent execution
  - Custom routing logic
- **Required for v6:**
  - Already partially implemented (declarative routing)
  - Add conditional branches
  - Skip agents if not needed
  - Parallel agent execution
- **Integration:** Supervisor routing logic
- **Test Specification:** (see TEST PLAN section)

#### 19. **Neurosymbolic Reasoning** ❌
- **Status:** NOT IMPLEMENTED
- **Priority:** 🔵 LOW
- **Effort:** 6-8 hours
- **Files (v5):** `backend/cognitive_architecture/neurosymbolic.py`
- **Capabilities (v5):**
  - Combine neural (LLM) + symbolic (logic rules)
  - Constraint validation
  - Logical inference
- **Required for v6:**
  - Define symbolic rules for code generation
  - Integrate with Codesmith validation
  - AST-based reasoning
- **Integration:** Codesmith validation pipeline
- **Test Specification:** (see TEST PLAN section)

#### 20. **Query Classifier** ❌
- **Status:** NOT IMPLEMENTED
- **Priority:** 🔵 LOW
- **Effort:** 3-4 hours
- **Files (v5):** `backend/processing/query_classifier.py`
- **Capabilities (v5):**
  - Classify user intent
  - Route to appropriate workflow
  - Extract entities
- **Required for v6:**
  - LLM-based classification
  - Intent taxonomy (bug fix, feature, refactor, etc.)
  - Entity extraction (file names, tech stack)
- **Integration:** Before Supervisor (classify task type)
- **Test Specification:** (see TEST PLAN section)

#### 21. **Self-Diagnosis** ❌
- **Status:** NOT IMPLEMENTED
- **Priority:** 🔵 LOW
- **Effort:** 3-4 hours
- **Files (v5):** `backend/cognitive_architecture/self_diagnosis.py`
- **Capabilities (v5):**
  - Detect system health issues
  - Identify degraded performance
  - Auto-recovery
- **Required for v6:**
  - Monitor workflow failures
  - Track agent response times
  - Detect memory issues
  - Alert user on degradation
- **Integration:** Background monitoring service
- **Test Specification:** (see TEST PLAN section)

---

## 📅 IMPLEMENTATION PLAN (Logical Phases)

### **Phase 1: Critical Missing Features (9-11 hours)**
**Goal:** Complete production-critical features for real-world use

#### P1.1 - Perplexity API Integration (3-4h)
- **Why First:** Research agent currently returns errors
- **Blocker:** Real web search needed for non-trivial projects
- **Dependencies:** PERPLEXITY_API_KEY in .env
- **Files:** `backend/tools/perplexity_tool.py`
- **Test:** Research task "Latest React 18 patterns"
- **Success Criteria:** Real search results returned

#### P1.2 - Asimov Rule 3: Global Error Search (6-7h)
- **Why Second:** Prevents partial fixes (critical for code quality)
- **Blocker:** ReviewFix might miss duplicate errors
- **Dependencies:** ripgrep installed
- **Files:**
  - `backend/security/asimov_rules.py` (add function)
  - `backend/workflow_v6.py` (add step after ReviewFix)
- **Test:** Generate code with duplicate errors
- **Success Criteria:** ALL instances fixed, not just one

---

### **Phase 2: Intelligence & Adaptation (15-19 hours)**
**Goal:** Add learning and proactive capabilities

#### P2.1 - Learning System (8-10h)
- **Why First:** Foundation for other cognitive systems
- **Blocker:** No historical data for predictions
- **Dependencies:** Memory System (already implemented)
- **Files:**
  - `backend/cognitive_architecture/learning_system_v6.py` (port from v5)
  - `backend/cognitive_architecture/learning_service_v6.py`
- **Integration:** Post-workflow analysis
- **Test:** Run 5 workflows, verify learnings stored
- **Success Criteria:** Pattern detection, strategy suggestions

#### P2.2 - Curiosity System (4-5h)
- **Why Second:** Uses Learning System for gap detection
- **Blocker:** None (standalone)
- **Dependencies:** Learning System
- **Files:** `backend/cognitive_architecture/curiosity_system_v6.py`
- **Integration:** Before Architect (requirement gathering)
- **Test:** Ambiguous task "Build an app"
- **Success Criteria:** Generates clarifying questions

#### P2.3 - Predictive System (3-4h)
- **Why Third:** Uses Learning System for predictions
- **Blocker:** None (standalone)
- **Dependencies:** Learning System
- **Files:** `backend/cognitive_architecture/predictive_system_v6.py`
- **Integration:** Pre-workflow (Supervisor init)
- **Test:** Complex task (e.g., "Full-stack app")
- **Success Criteria:** Predicts duration, suggests approach

---

### **Phase 3: Dynamic Execution (10-13 hours)**
**Goal:** Flexible workflow and tool management

#### P3.1 - Tool Registry (5-6h)
- **Why First:** Foundation for dynamic tool selection
- **Blocker:** None (standalone)
- **Dependencies:** None
- **Files:**
  - `backend/tools/tool_registry_v6.py`
  - `backend/tools/tool_metadata.json`
- **Integration:** Agent initialization
- **Test:** Register new tool, verify agent uses it
- **Success Criteria:** Dynamic tool discovery

#### P3.2 - Approval Manager (4-5h)
- **Why Second:** Safety gates for critical actions
- **Blocker:** None (standalone)
- **Dependencies:** WebSocket protocol extension
- **Files:**
  - `backend/review/approval_manager_v6.py`
  - `backend/server_v6.py` (add approval message type)
- **Integration:** Before file writes
- **Test:** File write triggers approval prompt
- **Success Criteria:** User can approve/reject

#### P3.3 - Dynamic Workflow Enhancements (1-2h)
- **Why Third:** Minimal work (mostly done)
- **Blocker:** None (enhancement)
- **Dependencies:** None
- **Files:** `backend/workflow_v6.py` (enhance routing)
- **Integration:** Supervisor routing logic
- **Test:** Task that skips Research (e.g., "Fix typo in README")
- **Success Criteria:** Conditional agent execution

---

### **Phase 4: Advanced Intelligence (12-16 hours)**
**Goal:** Advanced reasoning and monitoring (optional)

#### P4.1 - Query Classifier (3-4h)
- **Why First:** Improves routing accuracy
- **Priority:** 🔵 LOW (nice-to-have)
- **Files:** `backend/processing/query_classifier_v6.py`
- **Integration:** Before Supervisor
- **Test:** Various task types
- **Success Criteria:** Correct intent classification

#### P4.2 - Neurosymbolic Reasoning (6-8h)
- **Why Second:** Advanced validation
- **Priority:** 🔵 LOW (Tree-sitter + Asimov sufficient)
- **Files:** `backend/cognitive_architecture/neurosymbolic_v6.py`
- **Integration:** Codesmith validation
- **Test:** Complex logic constraints
- **Success Criteria:** Symbolic rule validation

#### P4.3 - Self-Diagnosis (3-4h)
- **Why Third:** Monitoring and alerts
- **Priority:** 🔵 LOW (manual monitoring sufficient)
- **Files:** `backend/cognitive_architecture/self_diagnosis_v6.py`
- **Integration:** Background monitoring
- **Test:** Simulate failure conditions
- **Success Criteria:** Alerts triggered

---

## 🧪 DETAILED TEST PLAN

### Testing Methodology (Unchanged)

**Core Principle:** Live testing ONLY (no pytest, no mocking)

**Process:**
1. Start server: `$HOME/.ki_autoagent/start.sh`
2. Run test script: `python3 test_live_v6.py`
3. Validate results: check files, run code, verify logs
4. Debug: check `/tmp/server_v6.log`

**Test Structure:**
```python
WORKSPACE = Path.home() / "TestApps" / "{TestName}App"
SERVER_URL = "ws://localhost:8001/ws/chat"

TASK = """Specific user request for this feature..."""

async def test_live():
    # Clean workspace
    # Connect to WebSocket
    # Send init + task
    # Wait for result
    # Validate generated files
    # Run generated code
    # Check logs
```

---

### Test Specifications for Each Feature

#### TEST 1: Perplexity API Integration ✅→❌→✅
**Feature:** Real web search capability
**Status:** STUB → needs implementation
**File:** `test_perplexity_integration.py`

**Test Task:**
```python
TASK = """Research the latest best practices for React 18 in 2025.
Focus on:
- New concurrent features
- Server Components
- Suspense patterns
- Performance optimizations

Provide a summary with sources."""
```

**Expected Behavior:**
1. Research agent uses `perplexity_search` tool
2. Real API call to Perplexity Sonar
3. Response contains:
   - Summary of findings (200-500 words)
   - List of source URLs (3-5 URLs)
   - Recent information (2024-2025)
4. Memory stores research findings
5. Architect can access research in design phase

**Validation Criteria:**
- ✅ No `"error": "not_implemented"` in response
- ✅ Response contains URLs (not placeholder text)
- ✅ URLs are real web pages (not made up)
- ✅ Content mentions React 18 features
- ✅ Memory contains research findings
- ✅ Execution time: <60s

**Debug Checklist:**
- Check `.env` has `PERPLEXITY_API_KEY`
- Check API key is valid (test with curl)
- Check request format matches Perplexity docs
- Check response parsing handles edge cases
- Check error handling (rate limits, timeouts)

---

#### TEST 2: Asimov Rule 3 - Global Error Search ❌
**Feature:** Find and fix ALL error instances
**Status:** NOT IMPLEMENTED
**File:** `test_global_error_search.py`

**Test Task:**
```python
TASK = """Create a Python module with 3 files:
1. database.py - Database connection class
2. api.py - API endpoints using database
3. utils.py - Utility functions using database

All files should use a variable called 'db_connection'.
Intentionally introduce an error: use 'databse_connection' (typo) in api.py."""
```

**Expected Behavior:**
1. Codesmith generates 3 files
2. ReviewFix detects typo in api.py: `databse_connection`
3. **Asimov Rule 3 triggers:**
   - Search ALL files for pattern `databse_connection`
   - Find instance in api.py
   - Fix in api.py
   - Verify no other instances exist
4. Also search for correct pattern `db_connection`
5. Ensure consistency across all files
6. Workflow completes with all files using correct variable

**Validation Criteria:**
- ✅ All 3 files created
- ✅ Global search performed (logs show "🔍 Global search for...")
- ✅ ALL instances of error pattern found
- ✅ ALL instances fixed (not just one)
- ✅ No mixed usage (databse_connection vs db_connection)
- ✅ ReviewFix quality score >0.75

**Implementation Steps:**
1. Add `perform_global_error_search()` to `asimov_rules.py`
2. Integrate with ReviewFix node
3. Use `ripgrep` to search workspace
4. Aggregate all matches
5. Generate fix for ALL instances
6. Re-run Codesmith with fix instructions

---

#### TEST 3: Learning System ❌
**Feature:** Pattern learning and strategy adaptation
**Status:** NOT IMPLEMENTED
**File:** `test_learning_system.py`

**Test Task:** (Run 3 times)
```python
# Run 1: Simple calculator
TASK_1 = """Create a Python calculator with add/subtract/multiply/divide"""

# Run 2: Calculator with history
TASK_2 = """Create a Python calculator with calculation history tracking"""

# Run 3: Scientific calculator
TASK_3 = """Create a scientific calculator with trig functions"""
```

**Expected Behavior:**
1. After TASK_1:
   - Learning System records: "Calculator apps typically have 4 basic operations"
   - Pattern stored: `{"project_type": "calculator", "common_features": ["add", "subtract", "multiply", "divide"]}`
2. After TASK_2:
   - Learning System detects pattern: "Calculator apps might benefit from history"
   - Suggestion: "Consider adding history tracking to calculators"
3. Before TASK_3:
   - Predictive System suggests: "Based on history, calculator projects take ~45s"
   - Curiosity System asks: "Should I include history tracking? (learned from previous projects)"

**Validation Criteria:**
- ✅ Learnings stored in Memory after each run
- ✅ Patterns detected across multiple runs
- ✅ Suggestions generated based on history
- ✅ Query Learning System: returns relevant patterns
- ✅ Performance: <5s overhead per workflow

**Storage:**
```
{workspace}/.ki_autoagent_ws/memory/learnings.db
- Table: patterns (project_type, features, outcomes, timestamp)
- Table: strategies (approach, success_rate, avg_duration)
```

---

#### TEST 4: Curiosity System ❌
**Feature:** Identify gaps and ask clarifying questions
**Status:** NOT IMPLEMENTED
**File:** `test_curiosity_system.py`

**Test Task:**
```python
TASK = """Build an app"""
```

**Expected Behavior:**
1. Supervisor detects ambiguous task
2. Curiosity System analyzes task
3. Identifies knowledge gaps:
   - What type of app? (web, mobile, CLI)
   - What programming language?
   - What features?
   - What is the purpose?
4. Generates questions
5. Sends WebSocket message to user:
   ```json
   {
     "type": "clarification_needed",
     "questions": [
       "What type of application? (web, mobile, desktop, CLI)",
       "What programming language or tech stack?",
       "What is the primary purpose of this app?",
       "Any specific features or requirements?"
     ]
   }
   ```
6. Waits for user response
7. Continues workflow with clarified requirements

**Validation Criteria:**
- ✅ Detects ambiguous task (before Research)
- ✅ Generates 3-5 relevant questions
- ✅ Sends WebSocket clarification message
- ✅ Waits for user input (timeout: 5 minutes)
- ✅ Incorporates user answers into workflow
- ✅ Better output quality with clarifications

**Alternative Test (No clarifications):**
- User responds "Just proceed with your best guess"
- Workflow continues without blocking
- Default assumptions made (e.g., "Python CLI app")

---

#### TEST 5: Predictive System ❌
**Feature:** Predict workflow duration and risks
**Status:** NOT IMPLEMENTED
**File:** `test_predictive_system.py`

**Test Task:**
```python
TASK = """Create a full-stack web application with:
- React frontend
- Node.js Express backend
- PostgreSQL database
- User authentication
- RESTful API
- Docker deployment"""
```

**Expected Behavior:**
1. Before workflow starts, Predictive System analyzes task
2. Predicts:
   - **Duration:** ~180-240s (based on complexity)
   - **Risk:** Medium-High (multiple technologies)
   - **Suggested Approach:**
     - "This is a complex task with 6+ files"
     - "Consider breaking into smaller iterations"
     - "Estimated 3-4 ReviewFix iterations"
3. Sends prediction to user:
   ```json
   {
     "type": "prediction",
     "estimated_duration": 210,
     "complexity": "high",
     "suggested_approach": "Incremental development recommended",
     "risks": [
       "Multiple technologies require coordination",
       "Docker config might need manual testing"
     ]
   }
   ```
4. User can choose:
   - "Proceed" → Full workflow runs
   - "Simplify" → Asks to reduce scope
   - "Break down" → Creates sub-tasks

**Validation Criteria:**
- ✅ Prediction generated before workflow start
- ✅ Duration estimate within 20% of actual
- ✅ Risk assessment matches actual issues
- ✅ Suggestions are actionable
- ✅ Prediction improves with more history (Learning System)

**Metrics Tracked:**
- Task complexity score (0-10)
- File count prediction
- Technology stack complexity
- Historical similar projects
- Average execution time per complexity level

---

#### TEST 6: Tool Registry ❌
**Feature:** Dynamic tool discovery and assignment
**Status:** NOT IMPLEMENTED
**File:** `test_tool_registry.py`

**Test Setup:**
1. Create new tool: `backend/tools/linting_tool.py`
   ```python
   @tool
   async def run_linter(file_path: str) -> dict:
       """Run Python linter (ruff) on file"""
       # Implementation
   ```
2. Create tool metadata: `backend/tools/tool_metadata.json`
   ```json
   {
     "run_linter": {
       "agent": "reviewfix",
       "description": "Lint Python code for style issues",
       "version": "1.0.0"
     }
   }
   ```

**Test Task:**
```python
TASK = """Create a Python module calculator.py with basic operations"""
```

**Expected Behavior:**
1. Tool Registry loads all tools at startup
2. Discovers `run_linter` tool
3. Assigns to ReviewFix agent (based on metadata)
4. ReviewFix agent uses tool during review:
   - Reads calculator.py
   - Runs linter
   - Reports style issues
5. If issues found, triggers fix iteration

**Validation Criteria:**
- ✅ Tool Registry discovers new tool without code changes
- ✅ Tool assigned to correct agent
- ✅ Agent can invoke tool
- ✅ Tool results integrated into workflow
- ✅ Logs show: "Loaded 6 tools (5 existing + 1 new)"

**Extension Test:**
- Add second tool: `run_type_checker`
- Verify both tools available
- Verify no conflicts

---

#### TEST 7: Approval Manager ❌
**Feature:** User approval gates for critical actions
**Status:** NOT IMPLEMENTED
**File:** `test_approval_manager.py`

**Test Setup:**
1. Configure approval rules: `.ki_autoagent_ws/config.yaml`
   ```yaml
   approval_required:
     - file_write: true
     - file_delete: true
     - deployment: true
   ```

**Test Task:**
```python
TASK = """Create calculator.py with add/subtract methods"""
```

**Expected Behavior:**
1. Codesmith generates calculator.py
2. Before `write_file`, Approval Manager checks rules
3. Sends WebSocket approval request:
   ```json
   {
     "type": "approval_required",
     "action": "file_write",
     "details": {
       "file": "calculator.py",
       "size": 4228,
       "preview": "class Calculator:\n    def add..."
     },
     "options": ["approve", "reject", "preview_full"]
   }
   ```
4. Client responds:
   ```json
   {
     "type": "approval_response",
     "action_id": "abc123",
     "decision": "approve"
   }
   ```
5. File written, workflow continues

**Validation Criteria:**
- ✅ Approval request sent BEFORE file write
- ✅ Workflow blocks until user responds
- ✅ Timeout after 5 minutes (configurable)
- ✅ User can preview full file content
- ✅ Reject prevents file write
- ✅ Approve allows write
- ✅ Approval history logged

**Edge Cases:**
- User ignores prompt → Timeout → Workflow fails gracefully
- User rejects → Codesmith tries alternative
- Multiple files → Batch approval option

---

#### TEST 8: Dynamic Workflow Enhancements ❌
**Feature:** Conditional agent execution
**Status:** PARTIALLY IMPLEMENTED (needs enhancement)
**File:** `test_dynamic_workflow.py`

**Test Task 1: Skip Research**
```python
TASK = """Fix typo in README.md: change 'teh' to 'the'"""
```

**Expected Behavior:**
1. Supervisor detects simple task
2. Skips Research agent (no web search needed)
3. Skips Architect agent (no design needed)
4. Goes directly to Codesmith:
   - Reads README.md
   - Fixes typo
   - Writes file
5. ReviewFix verifies fix
6. Execution time: <15s (vs ~50s for full workflow)

**Test Task 2: Parallel Execution**
```python
TASK = """Create two independent modules:
1. math_utils.py - Math helper functions
2. string_utils.py - String helper functions"""
```

**Expected Behavior:**
1. Supervisor detects independent sub-tasks
2. Creates 2 parallel Codesmith instances:
   - Codesmith A generates math_utils.py
   - Codesmith B generates string_utils.py
   - Both run concurrently
3. ReviewFix validates both files
4. Execution time: ~30s (vs ~50s sequential)

**Validation Criteria:**
- ✅ Research skipped for simple tasks
- ✅ Architect skipped when no design needed
- ✅ Parallel execution when tasks independent
- ✅ Logs show routing decisions
- ✅ Performance improvement measured

**Implementation:**
- Enhance `should_continue()` in workflow_v6.py
- Add parallel routing logic
- Add task complexity classifier

---

#### TEST 9: Query Classifier ❌
**Feature:** Classify user intent and extract entities
**Status:** NOT IMPLEMENTED
**File:** `test_query_classifier.py`

**Test Tasks:**
```python
TASKS = [
    "Fix the authentication bug in login.py",           # Type: bug_fix
    "Add dark mode toggle to settings page",            # Type: feature
    "Refactor database.py to use async/await",          # Type: refactor
    "Explain how the caching system works",             # Type: explanation
    "Create a REST API for user management",            # Type: new_project
]
```

**Expected Behavior:**
```python
# For each task, classifier returns:
{
    "intent": "bug_fix",                    # or feature, refactor, etc.
    "confidence": 0.92,
    "entities": {
        "files": ["login.py"],
        "technologies": ["authentication"],
        "action": "fix"
    },
    "suggested_workflow": "minimal",        # or full, research_only
    "suggested_agents": ["codesmith", "reviewfix"]
}
```

**Routing Based on Classification:**
- `bug_fix` → Skip Research, go to Codesmith (read file, fix, test)
- `feature` → Full workflow (Research → Architect → Codesmith → ReviewFix)
- `refactor` → Skip Research, use Architect for refactor plan
- `explanation` → Skip all agents, use LLM directly with code reading
- `new_project` → Full workflow with extra Research time

**Validation Criteria:**
- ✅ Correct intent classification (>90% accuracy)
- ✅ Entity extraction (files, technologies)
- ✅ Workflow routing matches classification
- ✅ Execution time optimized per type
- ✅ Logs show classification rationale

---

#### TEST 10: Neurosymbolic Reasoning ❌
**Feature:** Combine neural (LLM) + symbolic (logic rules)
**Status:** NOT IMPLEMENTED
**Priority:** 🔵 LOW
**File:** `test_neurosymbolic_reasoning.py`

**Test Task:**
```python
TASK = """Create a banking transaction system with:
- Transfer money between accounts
- Check balance
- Transaction history

CONSTRAINTS:
- Balance cannot go negative
- Transfer amount must be positive
- Transaction history immutable"""
```

**Expected Behavior:**
1. Codesmith generates code using LLM (neural)
2. Neurosymbolic Validator extracts symbolic constraints:
   ```python
   rules = [
       "ALWAYS: balance >= 0",
       "ALWAYS: transfer_amount > 0",
       "NEVER: modify transaction_history after append"
   ]
   ```
3. Validates generated code against rules:
   - Parse AST
   - Find all `balance` assignments
   - Check for negative value guards
   - Find all `transfer_amount` usages
   - Check for positive value validation
4. If violations found:
   - Report to Codesmith
   - Regenerate with constraint hints
5. Final code guaranteed to satisfy constraints

**Validation Criteria:**
- ✅ Symbolic rules extracted from task
- ✅ Generated code satisfies all rules
- ✅ Violations caught before file write
- ✅ AST analysis accurate
- ✅ Works with multiple constraint types

**Implementation:**
- Define symbolic rule language
- Implement AST-based constraint checker
- Integrate with Codesmith validation pipeline

---

#### TEST 11: Self-Diagnosis ❌
**Feature:** System health monitoring and auto-recovery
**Status:** NOT IMPLEMENTED
**Priority:** 🔵 LOW
**File:** `test_self_diagnosis.py`

**Test Scenarios:**

**Scenario 1: Slow Agent Response**
```python
# Simulate slow LLM response
# (inject delay in test environment)
```
**Expected:**
- Self-Diagnosis detects Architect taking >30s (threshold: 20s)
- Alert logged: "⚠️ Architect response slow (35.2s)"
- Suggestion: "Consider using faster model or reducing context"

**Scenario 2: Memory Fragmentation**
```python
# Run 20 workflows in sequence
# (simulate memory growth)
```
**Expected:**
- Self-Diagnosis tracks memory usage over time
- Detects growth trend: 150MB → 180MB → 220MB
- Alert: "⚠️ Memory usage increasing (220MB, +47%)"
- Auto-recovery: Trigger garbage collection

**Scenario 3: Repeated Failures**
```python
# Generate code that always fails ReviewFix
TASK = """Create an impossible function that violates constraints"""
```
**Expected:**
- Self-Diagnosis detects 3 consecutive ReviewFix failures
- Alert: "❌ Workflow stuck in ReviewFix loop"
- Auto-recovery: Skip ReviewFix, proceed with best attempt
- User notification: "Quality threshold not met, proceeding anyway"

**Validation Criteria:**
- ✅ Monitors agent response times
- ✅ Tracks memory usage
- ✅ Detects failure patterns
- ✅ Triggers alerts
- ✅ Auto-recovery actions work
- ✅ User notified of issues

---

## 📊 PROGRESS TRACKING

### Completed (Iterations 0-2)
- [x] Core Workflow Engine
- [x] Research Agent (stub)
- [x] Architect Agent
- [x] Codesmith Agent
- [x] ReviewFix Agent
- [x] Memory System
- [x] Tree-sitter Validation
- [x] Asimov Rules 1 & 2
- [x] File Tools
- [x] Claude CLI Integration

**Subtotal:** 10/21 features (48%)

### Pending (44-57 hours)
- [ ] Perplexity API Integration (3-4h) 🔴
- [ ] Asimov Rule 3 (6-7h) 🔴
- [ ] Learning System (8-10h) 🟡
- [ ] Curiosity System (4-5h) 🟡
- [ ] Predictive System (3-4h) 🟡
- [ ] Tool Registry (5-6h) 🟢
- [ ] Approval Manager (4-5h) 🟢
- [ ] Dynamic Workflow (1-2h) 🟢
- [ ] Query Classifier (3-4h) 🔵
- [ ] Neurosymbolic Reasoning (6-8h) 🔵
- [ ] Self-Diagnosis (3-4h) 🔵

**Subtotal:** 11/21 features (52%)

---

## 🎯 NEXT SESSION CHECKLIST

### What You Need to Know
1. **Current Branch:** `v6.0-alpha`
2. **Last Commit:** "docs: Add Iteration 2 (Asimov) to IMPLEMENTATION_LOG"
3. **Server Status:** Running on `ws://localhost:8001/ws/chat`
4. **Test Workspace:** `~/TestApps/CalculatorApp/` (clean before each test)
5. **Logs:** `/tmp/server_v6.log` (check for errors)
6. **Current Performance:** 49.1s, Quality 0.90

### Files to Reference
- **Implementation Log:** `IMPLEMENTATION_LOG.md` (all progress so far)
- **This Roadmap:** `V6_IMPLEMENTATION_ROADMAP.md` (complete plan)
- **Missing Features:** `MISSING_FEATURES.md` (detailed analysis)
- **Status Report:** `V6_STATUS_REPORT.md` (production readiness)
- **Asimov Rules:** `.kiautoagent/docs/ASIMOV_RULES.md` (security policies)
- **Test Script:** `test_live_v6.py` (live testing template)

### Commands You'll Use
```bash
# Start server
$HOME/.ki_autoagent/start.sh

# Run test
python3 test_live_v6.py

# Check logs
tail -f /tmp/server_v6.log

# Check generated files
ls -lah ~/TestApps/CalculatorApp/

# Run generated code
cd ~/TestApps/CalculatorApp/ && python3 calculator.py

# Git workflow
git status
git add .
git commit -m "feat: Implement Perplexity API integration"
git push origin v6.0-alpha
```

### Testing Template (Copy-Paste)
```python
#!/usr/bin/env python3
"""Test for [FEATURE_NAME]"""
import asyncio
import aiohttp
import json
from pathlib import Path
import shutil

WORKSPACE = Path.home() / "TestApps" / "[FeatureName]App"
SERVER_URL = "ws://localhost:8001/ws/chat"

TASK = """[Your test task here]"""

async def test_live():
    print("=" * 80)
    print(f"🧪 TEST: [Feature Name]")
    print("=" * 80)

    # Clean workspace
    if WORKSPACE.exists():
        shutil.rmtree(WORKSPACE)
    WORKSPACE.mkdir(parents=True, exist_ok=True)

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(SERVER_URL) as ws:
            # Connect
            msg = await ws.receive_json()
            print(f"✅ {msg['type']}")

            # Init
            await ws.send_json({
                "type": "init",
                "workspace_path": str(WORKSPACE)
            })
            msg = await ws.receive_json()
            print(f"✅ {msg['type']}")

            # Send task
            await ws.send_json({
                "type": "chat",
                "content": TASK
            })

            # Wait for result
            while True:
                msg = await ws.receive_json()
                if msg["type"] == "result":
                    print(f"\n✅ COMPLETED")
                    print(json.dumps(msg.get("result", {}), indent=2))
                    break
                elif msg["type"] == "error":
                    print(f"\n❌ ERROR: {msg.get('error')}")
                    break

    # Validate
    print("\n" + "=" * 80)
    print("📊 VALIDATION")
    print("=" * 80)

    # [Add your validation checks here]

if __name__ == "__main__":
    asyncio.run(test_live())
```

### Recommended Next Steps
1. **START WITH:** Phase 1 (Perplexity + Asimov Rule 3)
2. **REASON:** Critical for production use
3. **ESTIMATED TIME:** 9-11 hours
4. **TEST AFTER EACH:** Don't batch implementations
5. **COMMIT AFTER EACH:** Small, focused commits
6. **UPDATE DOCS:** Add to IMPLEMENTATION_LOG.md

### Context for Next Agent
- User wants **continuous work without interruptions**
- User wants **user-like WebSocket tests** (no pytest)
- User wants **complete implementations** (no TODOs, no stubs)
- User wants **NO auto-fallbacks** (fail properly)
- User wants **git commits after each feature**
- User wants **IMPLEMENTATION_LOG.md updated** after each iteration

### Questions You Might Have
- **Q:** Should I implement all 11 features?
  **A:** Start with Phase 1 (🔴 CRITICAL), then check with user
- **Q:** What if tests fail?
  **A:** Debug with `/tmp/server_v6.log`, fix, re-test
- **Q:** Can I use pytest?
  **A:** NO - user requirement: only live WebSocket tests
- **Q:** Should I ask user before each feature?
  **A:** NO - user said "Bitte mit allem weitermachen ohne mich noch mal zu fragen"
- **Q:** What about code quality?
  **A:** MUST follow PYTHON_BEST_PRACTICES.md, Asimov Rules enforced

---

## 📝 SUMMARY

**What's Done:**
- 10/21 features complete (48%)
- 3 iterations completed successfully
- System runs end-to-end
- Generated code quality: 0.90
- Performance: 49.1s
- Validation overhead: 21% (acceptable)

**What's Next:**
- 11/21 features pending (52%)
- 44-57 hours estimated
- 4 phases planned
- Phase 1 is CRITICAL (9-11 hours)
- All tests specified
- Implementation order defined

**How to Continue:**
1. Read this document
2. Start with Phase 1
3. Implement → Test → Commit → Document
4. One feature at a time
5. Update IMPLEMENTATION_LOG.md
6. Move to next feature

**Key Principle:**
"Continuous work without interruptions, user-like testing, complete implementations, no auto-fallbacks"

---

**Document Complete - Ready for Next Session** ✅
