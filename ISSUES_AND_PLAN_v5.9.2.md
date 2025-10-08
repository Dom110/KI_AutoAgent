# KI AutoAgent - Issues & Feature Plan v5.9.2

**Date:** 2025-10-08
**Current Version:** Backend v5.9.0, Frontend v5.9.1

---

## 🐛 Critical Issues Found

### Issue 1: Proposal Missing Research Insights
**Problem:** Architecture proposal's `research_insights` field contains Architect's markdown output instead of actual research results.

**Evidence:**
```json
"research_insights": "# 🏗️ Architecture Proposal\n\n## Project: frontend-only..."
```

Should contain:
- Industry Standards (from research doc)
- Technology comparison table
- Best practices
- Performance/Security recommendations

**Root Cause:** `architect_agent.py:1296` - copies wrong content to research_insights field in JSON mode.

**Impact:**
- User can't see what research informed the architecture
- Reviewer can't validate against research findings
- Proposal lacks justification

**Fix Required:**
```python
# In architect_agent.py generate_documentation_with_research()
# Line 1296 should be:
"research_insights": research_insights[:1000] if research_insights else "No research available"
# NOT: research_insights from architect's own markdown
```

---

### Issue 2: Reviewer Skipped After Codesmith
**Problem:** Workflow ends after codesmith completes, reviewer never runs.

**Evidence:**
```
[11:45:33] codesmith completed: ✅ Implementation completed
[11:45:33] No reviewer activity
```

**Expected Flow:**
1. Architect → approved ✅
2. Codesmith → completed ✅
3. Reviewer → **SKIPPED ❌**
4. Fixer → never reached

**Root Cause:** Unknown - needs investigation:
- Check if execution_plan includes reviewer step
- Check if routing logic skips reviewer for "simple" projects
- Check if reviewer has dependency issues

**Impact:**
- Generated code never tested
- Bugs not caught (e.g., missing tsconfig.node.json)
- User gets broken app

---

### Issue 3: Generated App Has Missing Files
**Problem:** Vite app missing `tsconfig.node.json`, causing startup errors.

**Evidence:**
```
Error: ENOENT: no such file or directory, open 'tsconfig.node.json'
```

**Generated Files:**
- ✅ index.html
- ✅ package.json
- ✅ tsconfig.json
- ✅ vite.config.ts
- ❌ tsconfig.node.json (MISSING)

**Root Cause:** Codesmith agent incomplete Vite template.

**Fix Required:** Codesmith should generate:
```json
// tsconfig.node.json
{
  "compilerOptions": {
    "composite": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

---

### Issue 4: .vite Folder Created Too Early
**Problem:** `.vite` appears before `.ki_autoagent_ws` in timestamp.

**Explanation:** NOT A BUG! Codesmith runs `npm run dev` to test the app, creating `.vite`. This is correct behavior.

**Timestamps:**
```
11:41 - .ki_autoagent_ws created (research/architecture saved)
11:46 - Code generated
11:51 - .vite created (Codesmith testing app)
```

**No fix needed** - this is expected workflow.

---

## ✨ Feature Request: Detailed Agent Progress

### Current State (BAD UX):
```
💭 orchestrator thinking: 🤔 Processing...
⏳ research: Researching...
⏳ architect: Analyzing...
⏳ codesmith: Implementing...
```

User sees NOTHING about what agents actually do!

### Desired State (GOOD UX - Like Claude Code Chat):

#### Research Agent:
```
🔍 Research: Calculator App Best Practices

📊 Searching: "mobile app architecture 2024"
  ├─ Found 8 sources
  ├─ 🔗 Android Developers Guide
  ├─ 🔗 React Native Best Practices
  └─ 🔗 Flutter Architecture Patterns

💡 Key Findings:
  • MVVM pattern recommended for calculator apps
  • Single-file HTML approach for simple cases
  • Modern frameworks: Jetpack Compose, SwiftUI, Flutter

[Expand to see full research results]
```

#### Architect Agent:
```
🏗️ Architecture: Analyzing Requirements

📋 Project Classification:
  • Complexity: Simple
  • Type: Frontend-only
  • Stack: HTML/CSS/JavaScript

📊 Technology Selection:
  ├─ Considered: React, Vue, Vanilla JS
  ├─ Selected: Vanilla JS (simplicity)
  └─ Reasoning: No framework overhead for calculator

📁 Proposed Structure:
  calculator-app/
  └── index.html (220 lines)
      ├─ HTML structure (50 lines)
      ├─ CSS styling (80 lines)
      └─ JavaScript logic (90 lines)

[Expand for detailed breakdown]
```

#### Codesmith Agent:
```
💻 CodeSmith: Implementing Calculator

📝 Generating Files:
  ├─ ✅ index.html (220 lines)
  ├─ ✅ styles.css (embedded)
  └─ ✅ script.js (embedded)

🧪 Testing Implementation:
  ├─ ⏳ Basic arithmetic (2+2)
  ├─ ✅ Addition works
  ├─ ✅ Subtraction works
  ├─ ✅ Multiplication works
  ├─ ✅ Division works
  └─ ⚠️  Division by zero needs handling

🔍 Running browser test...
  └─ ✅ Calculator loads correctly

[Expand to see code preview]
```

#### Reviewer Agent:
```
🔎 Reviewer: Testing Implementation

🧪 Running Tests:
  ├─ ✅ HTML validation passed
  ├─ ✅ CSS syntax valid
  ├─ ✅ JavaScript no errors
  └─ ✅ Browser compatibility check

📊 Code Quality:
  ├─ Functions: 8 total
  ├─ Lines of Code: 220
  ├─ Complexity: Low
  └─ Best Practices: 95% compliance

⚠️  Issues Found:
  1. Division by zero not handled (line 145)
  2. Missing input validation (line 78)

Verdict: ✅ PASS with minor warnings

[Expand for detailed test results]
```

---

## 📋 Implementation Plan for v5.9.2

### Phase 1: Fix Critical Bugs (2-3 hours)

**1.1 Fix Proposal Research Insights**
- File: `backend/agents/specialized/architect_agent.py`
- Location: Line 1296 in `generate_documentation_with_research()`
- Change: Pass actual research_insights, not architect's markdown
- Test: Verify proposal JSON contains research findings

**1.2 Fix Reviewer Skipping**
- File: `backend/langgraph_system/workflow.py`
- Investigation needed:
  - Check execution plan generation
  - Check routing logic after codesmith
  - Check if reviewer dependencies met
- Fix: Ensure reviewer always runs after codesmith
- Test: Verify all 4 steps execute

**1.3 Fix Codesmith Vite Template**
- File: `backend/agents/specialized/codesmith_agent.py`
- Add: Generate `tsconfig.node.json` for Vite projects
- Template to add:
```json
{
  "compilerOptions": {
    "composite": true,
    "module": "ESNext",
    "moduleResolution": "bundler"
  },
  "include": ["vite.config.ts"]
}
```
- Test: Generated Vite app starts without errors

---

### Phase 2: Detailed Progress Messages (4-6 hours)

**2.1 Backend: Progress Streaming Infrastructure**

Create new `ProgressReporter` class:
```python
# backend/utils/progress_reporter.py
class ProgressReporter:
    def __init__(self, agent_name: str, websocket_manager, client_id: str):
        self.agent = agent_name
        self.manager = websocket_manager
        self.client_id = client_id

    async def report(self, stage: str, details: dict):
        """Send detailed progress update"""
        await self.manager.send_json(self.client_id, {
            "type": "agent_progress_detailed",
            "agent": self.agent,
            "stage": stage,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
```

**2.2 Research Agent: Live Search Updates**

Modify `research_agent.py`:
```python
async def execute(self, request: TaskRequest) -> TaskResult:
    reporter = ProgressReporter("research", self.manager, client_id)

    # Report search starting
    await reporter.report("searching", {
        "query": prompt[:100],
        "search_type": "web_search"
    })

    # Call Perplexity
    result = await self.perplexity_service.search_web(prompt)

    # Report findings
    await reporter.report("found_sources", {
        "source_count": len(result.get("citations", [])),
        "sources": result.get("citations", [])[:5]  # First 5
    })

    # Report key insights (extract first 3 bullet points)
    insights = self._extract_key_insights(result["answer"])
    await reporter.report("key_insights", {
        "insights": insights[:3]
    })

    return TaskResult(...)
```

**2.3 Architect Agent: Design Breakdown**

Modify `architect_agent.py`:
```python
async def execute(self, request: TaskRequest) -> TaskResult:
    reporter = ProgressReporter("architect", self.manager, client_id)

    # Report classification
    classification = await self._classify_task(...)
    await reporter.report("classified", {
        "complexity": classification["complexity"],
        "type": classification["type"],
        "stack": classification["suggested_stack"]
    })

    # Report structure planning
    structure = self._design_structure(classification)
    await reporter.report("structure_designed", {
        "files": structure["files"],
        "file_count": len(structure["files"]),
        "preview": structure["preview"][:200]
    })

    return TaskResult(...)
```

**2.4 Codesmith Agent: Generation Progress**

Modify `codesmith_agent.py`:
```python
async def execute(self, request: TaskRequest) -> TaskResult:
    reporter = ProgressReporter("codesmith", self.manager, client_id)

    # Report files being generated
    for file in files_to_create:
        await reporter.report("generating_file", {
            "filename": file.name,
            "lines": file.estimated_lines
        })

        # Generate file...

        await reporter.report("file_complete", {
            "filename": file.name,
            "actual_lines": len(content.split('\n'))
        })

    # Report testing
    await reporter.report("testing", {
        "test_type": "browser_test",
        "status": "running"
    })

    test_result = await self._test_implementation(...)

    await reporter.report("test_complete", {
        "status": test_result.status,
        "issues": test_result.issues
    })

    return TaskResult(...)
```

**2.5 Reviewer Agent: Test Reporting**

Modify `reviewer_agent.py`:
```python
async def execute(self, request: TaskRequest) -> TaskResult:
    reporter = ProgressReporter("reviewer", self.manager, client_id)

    # Report test stages
    await reporter.report("validating_syntax", {})
    syntax_ok = await self._check_syntax(...)

    await reporter.report("checking_best_practices", {})
    best_practices = await self._check_best_practices(...)

    await reporter.report("running_browser_tests", {})
    browser_tests = await self._run_browser_tests(...)

    # Report final verdict
    await reporter.report("review_complete", {
        "verdict": "PASS" if all_ok else "FAIL",
        "issues": issues_found,
        "score": quality_score
    })

    return TaskResult(...)
```

---

### Phase 3: Frontend UI for Detailed Progress (3-4 hours)

**3.1 New Message Type Handler**

In `MultiAgentChatPanel.ts`:
```typescript
this.backendClient.on('agent_progress_detailed', (message: any) => {
    this.sendMessage({
        type: 'progress_detailed',
        agent: message.agent,
        stage: message.stage,
        details: message.details,
        timestamp: message.timestamp
    });
});
```

**3.2 Expandable Progress Component**

In webview HTML/CSS:
```html
<div class="progress-detailed">
    <div class="progress-header">
        <span class="agent-icon">🔍</span>
        <span class="agent-name">Research</span>
        <span class="stage">Searching</span>
        <button class="expand-btn" onclick="toggleExpand(this)">
            ▼ Expand
        </button>
    </div>
    <div class="progress-body collapsed">
        <div class="progress-details">
            <!-- Detailed content here -->
        </div>
    </div>
</div>
```

```css
.progress-body {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease-out;
}

.progress-body:not(.collapsed) {
    max-height: 500px;
    overflow-y: auto;
}

.progress-details {
    padding: 8px;
    background: rgba(255,255,255,0.05);
    border-radius: 4px;
    font-size: 0.9em;
}
```

**3.3 Auto-Collapse Long Messages**

```typescript
function renderProgressDetailed(message: any): string {
    const content = formatProgressContent(message);
    const shouldCollapse = content.length > 200;

    return `
        <div class="progress-detailed ${shouldCollapse ? 'auto-collapsed' : ''}">
            <div class="progress-header">
                ${message.stage}
                ${shouldCollapse ? '<button class="expand-btn">▼ Expand</button>' : ''}
            </div>
            <div class="progress-body ${shouldCollapse ? 'collapsed' : ''}">
                ${content}
            </div>
        </div>
    `;
}
```

---

### Phase 4: Testing & Polish (2-3 hours)

**4.1 Test Scenarios**
1. Simple calculator app (HTML/CSS/JS)
2. React app with Vite
3. Multi-file project
4. Error scenarios (missing deps, syntax errors)

**4.2 Performance**
- Ensure progress messages don't spam (debounce if needed)
- Limit stored messages (keep last 100)
- Lazy load collapsed content

**4.3 Documentation**
- Update CLAUDE.md with progress reporter usage
- Add examples for custom agents
- Document message types

---

## 📦 Deliverables for v5.9.2

### Backend Changes:
- ✅ Fix proposal research_insights field
- ✅ Fix reviewer skipping bug
- ✅ Fix codesmith Vite template (tsconfig.node.json)
- ✅ Add ProgressReporter class
- ✅ Update all agents with detailed progress

### Frontend Changes:
- ✅ Add agent_progress_detailed handler
- ✅ Add expandable progress UI
- ✅ Auto-collapse messages >200 chars
- ✅ Add expand/collapse animations

### Documentation:
- ✅ Update CHANGELOG.md
- ✅ Update CLAUDE.md
- ✅ Create PROGRESS_MESSAGING_GUIDE.md

### Testing:
- ✅ End-to-end workflow test
- ✅ Progress message stress test
- ✅ UI responsiveness test

---

## 🎯 Success Criteria

### Must Have:
- [ ] Research insights appear in proposal
- [ ] Reviewer runs after codesmith
- [ ] Generated Vite apps work without errors
- [ ] User sees what agents are doing in real-time

### Nice to Have:
- [ ] Live code preview in chat
- [ ] Clickable file references
- [ ] Syntax highlighting in progress messages
- [ ] Progress timeline visualization

---

## ⏱️ Time Estimate

- **Phase 1 (Bug Fixes):** 2-3 hours
- **Phase 2 (Backend Progress):** 4-6 hours
- **Phase 3 (Frontend UI):** 3-4 hours
- **Phase 4 (Testing):** 2-3 hours

**Total:** 11-16 hours (1.5-2 full work days)

---

## 🔍 KRITISCHE ARCHITEKTUR-ANALYSE (2025-10-08 15:00)

### IST-Zustand: Was haben wir WIRKLICH?

#### ✅ IMPLEMENTIERT (Best Practices):
1. **TypedDict State Schema** ✅
   - `ExtendedAgentState` (state.py:227)
   - Typed channels für alle State-Felder

2. **Custom State Reducer** ✅
   - `merge_execution_steps` (state.py:40)
   - Immutability für execution_plan updates

3. **Dataclasses für Execution** ✅
   - `ExecutionStep` (state.py:96)
   - `TaskLedger`, `ProgressLedger` (state.py:166, 189)

4. **LangGraph Workflow** ✅
   - StateGraph mit nodes & edges (workflow.py:5220)
   - Checkpointer mit thread_id (workflow.py:5397)

#### ❌ NICHT Best Practice (ANTIPATTERN):

1. **Checkpointer: MemorySaver statt SqliteSaver**
   - Location: workflow.py:5331
   - Problem: Kein persistentes Memory über Restarts
   - Comment: "Use MemorySaver for simplicity - SqliteSaver has complex async requirements"
   - **FALSCH**: AsyncSqliteSaver ist verfügbar, aber nicht genutzt!

2. **Routing Logic: Alle Agents nutzen EINE Funktion**
   - Location: workflow.py:5286-5314
   - Problem: `route_to_next_agent()` für ALLE conditional edges
   - Antipattern: Imperative string-based routing statt declarative Graph edges

3. **execution_plan: Hybrid zwischen Graph und Manual Control**
   - Problem: execution_plan in State simuliert Workflow-Logik
   - Best Practice: Graph edges sollten Flow definieren, nicht State-Manipulation

4. **Keine Subgraphs**
   - Problem: Alle Agents im selben Graph, kein State-Isolation
   - Best Practice: Supervisor + Worker Subgraphs

---

## 🎯 DETAILLIERTER REFACTORING-PLAN v5.9.2

### Philosophie: **Evolution, nicht Revolution**

Wir refactoren **schrittweise** in v5.9.2:
- ✅ Fix kritische Bugs (execution_plan logic)
- ✅ Upgrade Checkpointer (MemorySaver → AsyncSqliteSaver)
- ✅ Verbessere Routing (dedicated functions statt one-size-fits-all)
- ❌ NICHT: Komplettes Redesign (das wäre v6.0)

---

## 📋 PHASE 1: Critical Bug Fixes (2-3 Stunden)

### 1.1 Fix: Research Insights in Proposal

**File:** `backend/agents/specialized/architect_agent.py`

**Problem (Line 1297):**
```python
"research_insights": research_insights[:500] if research_insights else "Architecture based on best practices"
```

**Root Cause Analysis benötigt:**
- Prüfen WAS in `research_insights` Parameter übergeben wird
- Prüfen ob Research Agent Output korrekt weitergegeben wird

**Expected Fix:**
```python
# In generate_documentation_with_research():
# Ensure research_insights contains ACTUAL research, not architect's own markdown

# Check caller site - WHO calls this function?
# Verify research_result.content is passed correctly
```

**Test Criteria:**
- Proposal JSON enthält Research findings (nicht Architect markdown)
- Research insights zeigen Citations/Sources
- Reasonably formatted (first 500 chars)

---

### 1.2 Fix: Reviewer wird übersprungen

**File:** `backend/langgraph_system/workflow.py`

**Problem Analysis:**

1. **Graph Edges sind korrekt:**
   - Line 5287: `"reviewer"` ist in loop für conditional edges
   - Line 5304: `"reviewer": "reviewer"` mapping existiert

2. **execution_plan muss Reviewer enthalten:**
   - Line 3874-3911: `create_execution_plan_for_task()`
   - Prüfen ob execution_plan step3 (reviewer) korrekt erstellt wird

3. **Dependencies müssen erfüllt sein:**
   - Line 3401-3409: `_dependencies_met()`
   - Reviewer dependency: `["step2"]` (codesmith)

**Root Cause Hypothese:**
```python
# workflow.py:3895
ExecutionStep(
    id="step3",
    agent="reviewer",
    dependencies=["step2"],  # ✅ Correct
    status="pending",
)

# BUT: route_to_next_agent() might skip if:
# 1. step2 status != "completed"
# 2. reviewer not in AVAILABLE_NODES (Line 3209 - IS THERE!)
# 3. Some other condition?
```

**Fix Strategy:**
```python
# 1. Add DEBUG logging in route_to_next_agent():
for step in state["execution_plan"]:
    logger.info(f"  Step {step.id} ({step.agent}): {step.status}")
    if step.agent == "reviewer":
        logger.info(f"    Reviewer dependencies: {step.dependencies}")
        logger.info(f"    Dependencies met: {self._dependencies_met(step, state['execution_plan'])}")

# 2. Check AVAILABLE_NODES includes "reviewer" (Line 3209)

# 3. If reviewer is skipped, log WARNING with detailed reason
```

**Test Criteria:**
- Calculator app workflow executes: architect → codesmith → reviewer → (fixer if needed)
- Reviewer step changes from pending → in_progress → completed
- Logs show "✅ Routing to reviewer for step step3"

---

### 1.3 Fix: Error Handling für übersprungene Tasks

**File:** `backend/langgraph_system/workflow.py`

**New Feature:** Detect when a task SHOULD run but gets skipped

**Implementation:**
```python
# In route_to_next_agent() - Line 3330-3346

if agent not in AVAILABLE_NODES:
    logger.warning(f"⚠️ Agent '{agent}' has no workflow node - marking as completed with stub")
    # v5.9.2: ADD ERROR TO STATE!
    error_info = {
        "type": "agent_skipped",
        "agent": agent,
        "step_id": step.id,
        "reason": f"Agent '{agent}' not in AVAILABLE_NODES",
        "timestamp": datetime.now().isoformat()
    }

    # Update state with error
    state["errors"].append(error_info)

    # Send WebSocket warning to user
    if client_id and manager:
        await manager.send_json(client_id, {
            "type": "agent_warning",
            "message": f"⚠️ {agent} was skipped - not implemented yet",
            "details": error_info
        })

    # Mark as completed with stub
    state.update(update_step_status(
        state, step.id, "completed",
        result=f"⚠️ Agent '{agent}' not yet implemented - stub response for: {step.task}",
        error=f"Agent not available: {agent}"
    ))
    continue
```

**Test Criteria:**
- When agent is skipped, user sees WebSocket warning
- State.errors[] contains skipped agent info
- Workflow continues (doesn't crash)

---

## 📋 PHASE 2: Checkpointer Upgrade (1-2 Stunden)

### 2.1 Upgrade: MemorySaver → AsyncSqliteSaver

**File:** `backend/langgraph_system/workflow.py`

**Current Code (Line 5329-5332):**
```python
# v5.5.3: Fixed checkpointer initialization
# Use MemorySaver for simplicity - SqliteSaver has complex async requirements
# The event loop issue was not from the checkpointer type, but from mixing sync/async
self.checkpointer = MemorySaver()
```

**Problem:** Comment is WRONG! AsyncSqliteSaver DOES work!

**Fix:**
```python
# v5.9.2: Upgrade to AsyncSqliteSaver for persistence
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import aiosqlite

# Create checkpointer with workspace-specific DB
workspace_name = self.workspace_path.split('/')[-1]
db_path = f"{self.workspace_path}/.ki_autoagent_ws/cache/workflow_checkpoints.db"

# Ensure directory exists
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Initialize async SQLite checkpointer
async with aiosqlite.connect(db_path) as conn:
    self.checkpointer = AsyncSqliteSaver(conn)
    logger.info(f"✅ Using AsyncSqliteSaver for workflow persistence: {db_path}")
```

**Benefits:**
- Workflow state persists across backend restarts
- Can resume interrupted workflows
- Better for production deployment

**Test Criteria:**
- Workflow checkpoint DB created in `.ki_autoagent_ws/cache/`
- After backend restart, can resume workflow
- No event loop errors

---

## 📋 PHASE 3: Routing Logic Refactoring (2-3 Stunden)

### 3.1 Problem: ONE routing function für ALLE agents

**Current Antipattern (Line 5286-5314):**
```python
for agent in ["codesmith", "reviewer", "fixer", "research", ...]:
    workflow.add_conditional_edges(
        agent,
        self.route_to_next_agent,  # ❌ SAME function for ALL!
        {...}
    )
```

**Why this is bad:**
- Reviewer-specific logic mixed with generic routing
- Hard to debug which agent caused which routing decision
- Violates Single Responsibility Principle

### 3.2 Solution: Dedicated Routing Functions

**Refactor:**
```python
# Create specialized routing functions

def route_from_codesmith(self, state: ExtendedAgentState) -> str:
    """Route after codesmith completes - ALWAYS go to reviewer"""
    logger.info("🔀 Routing from codesmith...")

    # Check if codesmith completed successfully
    codesmith_step = self._get_step_by_agent(state, "codesmith")
    if codesmith_step and codesmith_step.status == "completed":
        logger.info("✅ Codesmith completed - routing to reviewer")
        return "reviewer"

    # Error case
    logger.error("❌ Codesmith failed - routing to end")
    return "end"

def route_from_reviewer(self, state: ExtendedAgentState) -> str:
    """Route after reviewer completes - to fixer if issues found"""
    logger.info("🔀 Routing from reviewer...")

    reviewer_step = self._get_step_by_agent(state, "reviewer")
    if not reviewer_step:
        return "end"

    # Check quality score
    quality_score = state.get("last_quality_score", 1.0)
    threshold = state.get("quality_threshold", 0.8)

    if quality_score < threshold:
        # Check iteration limit
        review_iteration = state.get("review_iteration", 0)
        max_iterations = state.get("max_review_iterations", 3)

        if review_iteration < max_iterations:
            logger.info(f"🔧 Quality score {quality_score} < {threshold} - routing to fixer (iteration {review_iteration + 1}/{max_iterations})")
            state["review_iteration"] = review_iteration + 1
            return "fixer"
        else:
            logger.warning(f"⚠️ Max iterations reached ({max_iterations}) - ending workflow despite quality issues")
            return "end"

    logger.info(f"✅ Quality score {quality_score} >= {threshold} - workflow complete")
    return "end"

def route_from_fixer(self, state: ExtendedAgentState) -> str:
    """Route after fixer completes - back to reviewer"""
    logger.info("🔀 Routing from fixer - back to reviewer for validation")
    return "reviewer"
```

**Update Graph Creation:**
```python
# Replace generic routing with specific functions
workflow.add_conditional_edges(
    "codesmith",
    self.route_from_codesmith,
    {"reviewer": "reviewer", "end": END}
)

workflow.add_conditional_edges(
    "reviewer",
    self.route_from_reviewer,
    {"fixer": "fixer", "end": END}
)

workflow.add_conditional_edges(
    "fixer",
    self.route_from_fixer,
    {"reviewer": "reviewer", "end": END}
)

# Keep route_to_next_agent() only for generic agents (research, docbot, etc.)
```

**Benefits:**
- Clear, debuggable routing logic
- Easier to maintain and extend
- Follows LangGraph Best Practices (declarative edges)

---

## 📋 PHASE 4: Testing & Validation (2 Stunden)

### 4.1 Test Scenario: Simple Calculator App

**Command:**
```bash
# Start backend
cd ~/.ki_autoagent
./start.sh

# In VS Code: Open test workspace
mkdir -p ~/Desktop/test-calculator
cd ~/Desktop/test-calculator

# Send message: "Create a simple calculator web app"
```

**Expected Workflow:**
1. Orchestrator decomposes task
2. Research finds best practices (OPTIONAL - might skip for simple task)
3. Architect designs single-file HTML calculator
4. Codesmith generates `calculator.html`
5. **Reviewer validates** (THIS MUST HAPPEN!)
6. Fixer corrects issues (if any)
7. Final result delivered

**Success Criteria:**
- ✅ Reviewer step executes (not skipped!)
- ✅ Proposal contains research insights (if research ran)
- ✅ No "agent skipped" warnings (unless intentional)
- ✅ Generated calculator works in browser
- ✅ Workflow checkpoint DB created

### 4.2 Test Scenario: Complex React App

**Command:**
```
Create a React todo app with Vite, TypeScript, and local storage
```

**Expected Workflow:**
1. Research finds React + Vite best practices
2. Architect designs multi-file structure
3. Codesmith generates:
   - package.json
   - tsconfig.json
   - **tsconfig.node.json** (MUST BE CREATED!)
   - vite.config.ts
   - src/App.tsx
   - src/main.tsx
4. Reviewer validates all files
5. Result: Complete, runnable Vite app

**Success Criteria:**
- ✅ All Vite template files generated
- ✅ `npm install && npm run dev` works without errors
- ✅ No missing tsconfig.node.json error

---

## 📋 PHASE 5: Documentation Updates (1 Stunde)

### 5.1 Update CLAUDE.md

Add section:
```markdown
## 🔧 WORKFLOW ROUTING LOGIC (v5.9.2+)

### Dedicated Routing Functions (Best Practice)

Each agent now has a DEDICATED routing function:

- `route_from_codesmith()` → Always routes to reviewer
- `route_from_reviewer()` → Routes to fixer if quality < threshold, else END
- `route_from_fixer()` → Always routes back to reviewer

This follows LangGraph Best Practices:
- Clear, debuggable logic
- Single Responsibility Principle
- Declarative edge definitions

### Checkpointer: AsyncSqliteSaver

Workflow state now persists to:
`$WORKSPACE/.ki_autoagent_ws/cache/workflow_checkpoints.db`

Benefits:
- Resume interrupted workflows after backend restart
- Audit trail of all workflow executions
- Better production deployment
```

### 5.2 Update CHANGELOG.md

```markdown
## v5.9.2 - 2025-10-08

### 🐛 Critical Bug Fixes
- Fixed: Research insights in architecture proposal now show actual research (not architect markdown)
- Fixed: Reviewer agent no longer skipped after codesmith completion
- Fixed: Error handling when agents are skipped - user gets WebSocket warning

### ✨ Improvements
- Upgraded: MemorySaver → AsyncSqliteSaver for persistent workflow state
- Refactored: Dedicated routing functions for each agent (LangGraph Best Practice)
- Added: Detailed logging for routing decisions

### 🧪 Testing
- Validated with simple calculator app (single-file HTML)
- Validated with complex React + Vite + TypeScript app
- All generated apps run without errors
```

---

## 🎯 SUCCESS CRITERIA (v5.9.2)

### Must Have:
- [ ] Research insights appear correctly in proposal
- [ ] Reviewer ALWAYS runs after codesmith (not skipped!)
- [ ] User gets warning if agent is skipped
- [ ] Workflow state persists to SQLite DB
- [ ] Generated Vite apps include tsconfig.node.json
- [ ] Generated apps run without errors

### Nice to Have:
- [ ] Dedicated routing functions for all agents (not just codesmith/reviewer/fixer)
- [ ] Better error messages in WebSocket
- [ ] Workflow visualization (show which step is active)

---

## ⏱️ TIME ESTIMATE

- **Phase 1 (Bug Fixes):** 2-3 hours
- **Phase 2 (Checkpointer):** 1-2 hours
- **Phase 3 (Routing Refactor):** 2-3 hours
- **Phase 4 (Testing):** 2 hours
- **Phase 5 (Documentation):** 1 hour

**Total:** 8-11 hours (1-1.5 Arbeitstage)

---

## 🚀 IMPLEMENTATION ORDER

### TODAY (2025-10-08 Afternoon):
1. Phase 1.2: Fix Reviewer Skip Bug (CRITICAL!)
2. Phase 1.3: Add Error Handling for skipped tasks
3. Phase 4.1: Test with Calculator App

### TOMORROW (2025-10-09):
4. Phase 1.1: Fix Research Insights Bug
5. Phase 2.1: Upgrade Checkpointer
6. Phase 3.1-3.2: Routing Refactor
7. Phase 4.2: Test with React App
8. Phase 5: Update Documentation

---

## 📝 OPEN QUESTIONS FOR USER

1. **Checkpointer Location:**
   - Store in workspace: `$WORKSPACE/.ki_autoagent_ws/cache/workflow_checkpoints.db`
   - OR global: `~/.ki_autoagent/data/checkpoints/{workspace_hash}.db`
   - **Recommendation:** Workspace-specific (easier cleanup)

2. **Routing Refactor Scope:**
   - Only codesmith/reviewer/fixer? (Minimal)
   - OR all agents? (Complete)
   - **Recommendation:** Start minimal, extend later

3. **Breaking Changes:**
   - execution_plan structure stays same? (Yes)
   - OR refactor to pure Graph edges? (v6.0)
   - **Recommendation:** Keep execution_plan for now (evolution not revolution)

---

---

## 🚀 COMPREHENSIVE TECHNOLOGY & ARCHITECTURE PLAN (2025-10-08 16:00)

### TEIL 1: TECHNOLOGIE-STACK ANALYSE

#### IST-Zustand (Was wir HABEN):

**Backend (Python 3.13):**
```yaml
Framework:
  - FastAPI 0.117.1 (REST + WebSocket API)
  - Uvicorn 0.37.0 (ASGI Server)
  - uvloop 0.21.0 (2-4x faster event loop)

AI Services:
  - OpenAI 1.109.1 (GPT-4o, GPT-4o-mini)
  - Anthropic 0.68.0 (Claude Sonnet 4.5, Haiku, Opus)
  - Google Generative AI 0.8.3+ (Gemini Video Understanding)
  - Perplexity (via aiohttp 3.10.5 - manual integration)

LangGraph/LangChain:
  - langgraph 0.2.45
  - langchain 0.3.9
  - langchain-core 0.3.21
  - langchain-community 0.3.8
  - langchain-openai 0.2.10
  - langchain-anthropic 0.3.0
  - langgraph-checkpoint 2.0.7
  - langgraph-checkpoint-sqlite 2.0.1

Memory & Storage:
  - chromadb 0.4.15 (Vector Store)
  - redis 6.4.0 (Caching - orjson 3.10.12 for 2-3x faster JSON)
  - sqlalchemy 2.0.23 (ORM)
  - aiosqlite 0.20.0 (Async SQLite)
  - faiss-cpu 1.12.0 (Vector Memory)

Performance:
  - uvloop 0.21.0 (Event Loop Optimization)
  - orjson 3.10.12 (JSON Serialization)
  - tenacity 9.0.0 (Retry Logic + Circuit Breaker)
  - aiosqlite 0.20.0 (Async DB Operations)

Code Analysis:
  - tree-sitter 0.25.1 (Code Parsing)
  - jedi 0.19.1 (Python IntelliSense)
  - semgrep 1.52.0 (Security Analysis)
  - bandit 1.7.6 (Security Checks)
  - vulture 2.11 (Dead Code Detection)
  - radon 6.0.1 (Complexity Metrics)

Visualization:
  - mermaid-py 0.5.0 (Diagrams)
  - graphviz 0.20.3 (Graphs)
  - pyvis 0.3.2 (Network Viz)
  - diagrams 0.24.4 (Architecture Diagrams)

Testing & Profiling:
  - pytest 7.4.3 (Unit Tests)
  - py-spy 0.3.14 (Profiling)
  - scalene 1.5.55 (Memory Profiling)
```

**Frontend (TypeScript + VS Code Extension):**
```yaml
Framework:
  - VS Code Extension API
  - TypeScript
  - WebView (HTML/CSS/JS)

AI SDKs:
  - OpenAI SDK (node_modules)
  - Anthropic SDK (node_modules)

Communication:
  - WebSocket Client (ws://localhost:8001/ws/chat)
  - Axios (HTTP Client)
```

**Deployment:**
```yaml
Installation:
  - Global Service: $HOME/.ki_autoagent/
  - Backend Service: Python FastAPI + uvloop
  - Multi-Client Support: WebSocket per workspace

Architecture:
  - Backend: GLOBAL (runs ONCE)
  - Frontend: MULTI-CLIENT (one per VS Code window)
  - Communication: WebSocket with workspace_path in init message
```

---

#### SOLL-Zustand (LangGraph Best Practices - Was FEHLT):

**1. LangGraph Templates (❌ NICHT implementiert):**
```yaml
Missing Templates:
  ❌ create_react_agent() - Prebuilt ReAct agent
  ❌ Memory Agent Template - Cross-thread memory
  ❌ Retrieval Agent Template - RAG system
  ❌ Data-Enrichment Template - Web search + structure

Current Implementation:
  ✅ Custom Agents (Architect, Codesmith, Reviewer, Fixer)
  ❌ NOT using LangGraph prebuilt templates
  ❌ Manual implementation instead of templates

Gap:
  - Wir haben eigene Agents gebaut statt create_react_agent() zu nutzen
  - Kein Template-based development
  - Mehr Code zu maintainen
```

**2. LangGraph Cloud Deployment (❌ NICHT geplant):**
```yaml
Missing:
  ❌ LangGraph Cloud Integration
  ❌ LangGraph Studio for debugging
  ❌ CLI-based deployment (langgraph deploy)

Current:
  ✅ Local deployment only ($HOME/.ki_autoagent/)
  ❌ No cloud deployment strategy
```

**3. Prebuilt Agent Patterns (⚠️ TEILWEISE):**
```yaml
create_react_agent():
  ❌ NOT used - we built custom agents instead

Our Custom Agents:
  ✅ BaseAgent (2039 lines) - custom base class
  ✅ Specialized Agents (Architect, Codesmith, etc.)
  ❌ More complex than create_react_agent() would be

Gap:
  - Mehr Maintenance-Aufwand
  - Mehr Lines of Code
  - Weniger Standard-konform
```

**4. Subgraphs (❌ NICHT implementiert):**
```yaml
Missing:
  ❌ Supervisor + Worker Subgraphs
  ❌ State isolation per subgraph
  ❌ Parallel execution of independent subgraphs

Current:
  ✅ One big graph with all agents
  ❌ execution_plan simulates routing
  ❌ No true parallelization via subgraphs
```

**5. Vertex AI Integration (❌ NICHT implementiert):**
```yaml
Missing:
  ❌ agent_engines.LanggraphAgent() class
  ❌ Google Cloud integration
  ❌ Vertex AI Search tools
  ❌ Google Search retrieval

Current:
  ✅ Perplexity for web search (manual integration)
  ❌ No Google Cloud services
```

---

### TEIL 2: GAP-ANALYSE & EMPFEHLUNGEN

#### Critical Gaps (Must Fix):

**1. Routing Logic (ANTIPATTERN)**
- Problem: Alle Agents nutzen `route_to_next_agent()`
- Best Practice: Dedicated routing functions pro Agent
- Impact: Reviewer wird übersprungen, schwer zu debuggen
- Fix: Phase 3 (Routing Refactor)

**2. Checkpointer (SUBOPTIMAL)**
- Problem: MemorySaver statt AsyncSqliteSaver
- Best Practice: Persistent checkpointing
- Impact: Workflow state verloren bei Restart
- Fix: Phase 2 (Checkpointer Upgrade)

**3. execution_plan (HYBRID)**
- Problem: Manuelles Routing via State statt Graph Edges
- Best Practice: Declarative Graph edges
- Impact: Komplexer als nötig, schwer zu warten
- Fix: v6.0 (komplettes Redesign)

#### Strategic Gaps (Consider for v6.0):

**4. Template-based Agents**
- Opportunity: Nutze `create_react_agent()` statt custom BaseAgent
- Benefit: Weniger Code, Standard-konform
- Effort: Medium (refactor all agents)
- Recommendation: v6.0

**5. Subgraphs Architecture**
- Opportunity: Supervisor + Worker Subgraphs
- Benefit: Echte Parallelisierung, State isolation
- Effort: High (komplettes Redesign)
- Recommendation: v6.0

**6. LangGraph Cloud**
- Opportunity: Deploy to LangGraph Cloud
- Benefit: Scalability, Monitoring, Debugging
- Effort: Medium (deployment config)
- Recommendation: v6.0 (optional)

---

### TEIL 3: FEATURE-SAMMLUNG (Aus allen MD-Dokumenten)

#### Implementierte Features (v5.9.0):

**Core System:**
- ✅ Multi-Agent Workflow (Orchestrator, Architect, Codesmith, Reviewer, Fixer)
- ✅ LangGraph State Management (TypedDict + Custom Reducer)
- ✅ WebSocket Communication (Multi-Client Support)
- ✅ Plan-First Mode (User Approval for Execution Plans)
- ✅ Architecture Proposal System (User Approval for Architecture)
- ✅ Task Decomposition (Orchestrator breaks down complex tasks)
- ✅ Agent Memory (SQLite + FAISS Vector Store)
- ✅ Research Agent (Perplexity Web Search)
- ✅ Code Analysis (tree-sitter, jedi, semgrep)
- ✅ Performance Optimizations (uvloop, orjson, aiosqlite)

**Advanced Features:**
- ✅ Self-Diagnosis System (Workflow Health Monitoring)
- ✅ Intelligent Query Handler (Classification + Routing)
- ✅ Safe Orchestrator Execution (Depth Limiting)
- ✅ Review-Fix Iteration Tracking (Max 3 iterations)
- ✅ Escalation System (Research → Alternative Fixer → Opus Arbitrator)
- ✅ Parallel Execution Support (execution_plan with parallel_group)
- ✅ Timeout & Retry Management (per ExecutionStep)
- ✅ Tool Discovery & Registry
- ✅ Curiosity System
- ✅ Agentic RAG
- ✅ Neurosymbolic Reasoning

**Specialized Agents:**
- ✅ ArchitectAgent (System Architecture Design)
- ✅ CodeSmithAgent (Code Generation)
- ✅ ReviewerGPT (Code Review & Testing)
- ✅ FixerGPT/FixerBot (Bug Fixing)
- ✅ ResearchAgent (Web Research via Perplexity)
- ✅ DocuBot (Documentation Generation)
- ✅ PerformanceBot (Performance Analysis)
- ✅ VideoAgent (Video Understanding via Gemini)
- ✅ TradeStrat (Trading Strategy Analysis)
- ✅ OpusArbitrator (Conflict Resolution with Claude Opus)

#### Geplante Features (Aus MD-Dokumenten):

**From CONTINUATION_PLAN_v5.9.0.md:**
- ⏳ Live Progress Updates (wie Claude Code Chat)
- ⏳ Expandable Messages (>200 chars auto-collapse)
- ⏳ Detailed Agent Progress (Research findings, Architecture breakdown, etc.)

**From ISSUES_AND_PLAN_v5.9.2.md:**
- 🐛 Fix: Research insights in proposal (show actual research)
- 🐛 Fix: Reviewer skip bug (ensure reviewer always runs)
- 🐛 Fix: Error handling for skipped tasks (WebSocket warnings)
- ⏳ Upgrade: MemorySaver → AsyncSqliteSaver
- ⏳ Refactor: Dedicated routing functions per agent

**From V5_8_7_DEPLOYMENT_SUCCESS.md:**
- ✅ Multi-Workspace Support (COMPLETED v5.8.1)
- ✅ Graceful Shutdown (COMPLETED v5.8.2)
- ✅ Perplexity Integration (COMPLETED v5.8.2)

**Not Yet Implemented:**
- ❌ LangGraph Templates Integration
- ❌ Subgraphs Architecture
- ❌ LangGraph Cloud Deployment
- ❌ Vertex AI Integration
- ❌ Live Code Preview in Chat
- ❌ Syntax Highlighting in Progress Messages
- ❌ Progress Timeline Visualization
- ❌ Clickable File References in Chat

---

### TEIL 4: MASTER-DOKUMENTE (Zu erstellen)

#### Dokument 1: `MASTER_FEATURES_v6.0.md`

**Zweck:** Alle Features gesammelt an einem Ort (Single Source of Truth)

**Struktur:**
```markdown
# KI AutoAgent - Master Features Document v6.0

## 1. IMPLEMENTED FEATURES (v5.9.0)
### 1.1 Core System
- Multi-Agent Workflow
- LangGraph State Management
- ...

### 1.2 Specialized Agents
- Architect Agent
- Codesmith Agent
- ...

### 1.3 Advanced Features
- Self-Diagnosis
- Escalation System
- ...

## 2. PLANNED FEATURES (v5.9.2)
### 2.1 Bug Fixes
- Research insights fix
- Reviewer skip fix
- ...

### 2.2 Improvements
- Checkpointer upgrade
- Routing refactor
- ...

## 3. FUTURE FEATURES (v6.0+)
### 3.1 LangGraph Best Practices
- Template-based agents
- Subgraphs architecture
- ...

### 3.2 UI/UX Enhancements
- Live progress updates
- Expandable messages
- ...

### 3.3 Cloud Integration
- LangGraph Cloud deployment
- Vertex AI integration
- ...

## 4. TECHNICAL DEBT
- execution_plan → Pure Graph edges
- Custom agents → create_react_agent()
- ...
```

#### Dokument 2: `PROGRESS_TRACKER_v6.0.md`

**Zweck:** Für neue Chat-Sessions - Schneller Einstieg

**Struktur:**
```markdown
# KI AutoAgent - Progress Tracker v6.0
**Für neue Claude Sessions - Quick Start Guide**

## CURRENT STATUS (Snapshot 2025-10-08)

### Version Info
- Backend: v5.9.0 (Python 3.13)
- Frontend: v5.9.1 (VS Code Extension)
- Status: 🟡 In Development (v5.9.2 planned)

### What Works ✅
- Multi-agent workflows
- Code generation (simple & complex apps)
- Architecture proposals
- Web research
- Code review
- Bug fixing

### Known Issues 🐛
1. Reviewer sometimes skipped after codesmith
2. Research insights show architect markdown instead of research
3. Missing error handling for skipped agents

### In Progress ⏳
- v5.9.2 Bug Fixes (Phase 1-5)
- Routing refactor
- Checkpointer upgrade

### Next Steps 📋
See ISSUES_AND_PLAN_v5.9.2.md for detailed plan

---

## ARCHITECTURE QUICK REFERENCE

### Key Files
- Backend Core: backend/langgraph_system/workflow.py (5274 lines)
- Orchestrator: backend/agents/specialized/orchestrator_agent_v2.py
- State: backend/langgraph_system/state.py
- Frontend: vscode-extension/src/ui/MultiAgentChatPanel.ts

### Tech Stack
- Framework: FastAPI + LangGraph + uvloop
- AI: OpenAI + Anthropic + Gemini
- Memory: ChromaDB + FAISS + Redis
- Deployment: Global service at $HOME/.ki_autoagent/

### Common Tasks
1. Start backend: ~/.ki_autoagent/start.sh
2. View logs: tail -f ~/.ki_autoagent/logs/backend.log
3. Test workflow: Open VS Code → Open workspace → Chat

---

## LANGGRAPH BEST PRACTICES (Reference)

### What We Have
- ✅ TypedDict State Schema
- ✅ Custom State Reducer
- ✅ Checkpointer (MemorySaver - needs upgrade)
- ✅ Nodes & Edges

### What We're Missing
- ❌ create_react_agent() templates
- ❌ Subgraphs
- ❌ Dedicated routing functions
- ❌ AsyncSqliteSaver

### Gap Analysis
See ISSUES_AND_PLAN_v5.9.2.md § "KRITISCHE ARCHITEKTUR-ANALYSE"

---

## FOR NEW CHAT SESSIONS

### Start Here
1. Read this document (you are here!)
2. Check ISSUES_AND_PLAN_v5.9.2.md for current plan
3. Review MASTER_FEATURES_v6.0.md for all features
4. Check CLAUDE.md for system rules

### Context You Need
- System uses LangGraph but NOT following all best practices
- execution_plan is hybrid approach (manual routing + graph)
- Multi-client architecture (one backend, many frontends)
- Workspace-specific data isolation

### Common Questions
Q: Why not use create_react_agent()?
A: Historical - we built custom agents before discovering templates

Q: Why MemorySaver instead of AsyncSqliteSaver?
A: Old comment was wrong - AsyncSqliteSaver works, needs upgrade

Q: Why one routing function for all agents?
A: Technical debt - fixing in v5.9.2

---

**Last Updated:** 2025-10-08 16:00
**For Questions:** See ISSUES_AND_PLAN_v5.9.2.md
```

---

### TEIL 5: IMPLEMENTATION ROADMAP

#### Phase 0: Documentation (JETZT - vor Code-Änderungen)
```yaml
Tasks:
  1. Erstelle MASTER_FEATURES_v6.0.md
  2. Erstelle PROGRESS_TRACKER_v6.0.md
  3. Update ISSUES_AND_PLAN_v5.9.2.md mit diesem Plan

Duration: 1-2 Stunden
Status: ⏸️ AWAITING USER APPROVAL
```

#### Phase 1: v5.9.2 Bug Fixes (2-3 Stunden)
```yaml
Already Planned:
  1. Fix research insights in proposal
  2. Fix reviewer skip bug
  3. Add error handling for skipped tasks

Status: 📋 Planned in detail (see above)
```

#### Phase 2: v5.9.2 Improvements (3-4 Stunden)
```yaml
Already Planned:
  1. Upgrade MemorySaver → AsyncSqliteSaver
  2. Refactor routing (dedicated functions)
  3. Testing & validation

Status: 📋 Planned in detail (see above)
```

#### Phase 3: v6.0 LangGraph Modernization (1-2 Wochen)
```yaml
Major Refactor:
  1. Replace custom BaseAgent with create_react_agent()
  2. Implement Subgraphs (Supervisor + Workers)
  3. Remove execution_plan (use pure Graph edges)
  4. Implement LangGraph Templates where applicable

Status: 💡 Concept only - needs detailed planning
```

#### Phase 4: v6.0 UI/UX Enhancements (1 Woche)
```yaml
Frontend Features:
  1. Live progress updates (like Claude Code)
  2. Expandable messages
  3. Syntax highlighting
  4. Clickable file references
  5. Progress timeline visualization

Status: 💡 Concept only
```

#### Phase 5: v6.0 Cloud Integration (Optional)
```yaml
Cloud Features:
  1. LangGraph Cloud deployment
  2. LangGraph Studio integration
  3. Vertex AI tools
  4. Scalability & monitoring

Status: 💡 Future consideration
```

---

### TEIL 6: ENTSCHEIDUNGSFRAGEN FÜR USER

**Frage 1: Dokumentation zuerst?**
- Option A: Erstelle MASTER_FEATURES_v6.0.md + PROGRESS_TRACKER_v6.0.md JETZT
- Option B: Springe direkt zu Bug Fixes (Phase 1)
- **Empfehlung:** A (Dokumentation hilft bei allen weiteren Steps)

**Frage 2: v5.9.2 oder direkt v6.0?**
- Option A: v5.9.2 Bug Fixes → Dann v6.0 Refactor (Evolution)
- Option B: Direkt v6.0 mit allem (Revolution)
- **Empfehlung:** A (weniger Risiko, schrittweise)

**Frage 3: LangGraph Templates nutzen?**
- Option A: Eigene Agents behalten (mehr Kontrolle)
- Option B: Zu create_react_agent() migrieren (Standard-konform)
- **Empfehlung:** B für v6.0 (weniger Code, wartbarer)

**Frage 4: Subgraphs implementieren?**
- Option A: Ja, in v6.0 (Best Practice)
- Option B: Nein, execution_plan ausreichend
- **Empfehlung:** A (echte Parallelisierung, cleaner)

**Frage 5: Cloud Deployment?**
- Option A: LangGraph Cloud (SaaS)
- Option B: Eigenes Hosting (current)
- Option C: Beides unterstützen
- **Empfehlung:** C für v6.0 (Flexibilität)

---

### TEIL 7: SUMMARY & NEXT STEPS

#### Was ich JETZT mache (nach Approval):

**Option A: Dokumentation (1-2h)**
1. Erstelle `MASTER_FEATURES_v6.0.md`
2. Erstelle `PROGRESS_TRACKER_v6.0.md`
3. Commit to Git

**Option B: Bug Fixes (2-3h)**
1. Fix Reviewer Skip Bug (CRITICAL)
2. Fix Research Insights
3. Add Error Handling
4. Test mit Calculator App

**Option C: Beides (3-5h)**
1. Erst Dokumentation
2. Dann Bug Fixes

#### Was ich NICHT mache (ohne weiteres Approval):

- ❌ v6.0 Refactoring (zu groß)
- ❌ LangGraph Templates Migration (breaking changes)
- ❌ Subgraphs Implementation (komplexes Redesign)
- ❌ Cloud Deployment (neue Infrastruktur)

---

**Document Version:** 3.0 (COMPREHENSIVE PLAN)
**Last Updated:** 2025-10-08 16:30 PM
**Status:** 🚦 AWAITING USER APPROVAL

**Nächster Schritt:** User wählt Option A, B oder C

---

## 🎯 APPROVED PLAN: Option C + Git Strategy (2025-10-08 17:00)

### USER DECISIONS:
- ✅ **Option C:** Dokumentation + Bug Fixes bis Phase 2
- ✅ **Git Strategy:** Release 5 (v5.9.2) → Development Branch 6 (v6.0-alpha)
- ✅ **LangGraph Templates:** Ja, in v6.0
- ✅ **Subgraphs:** Ja, in v6.0
- ❓ **Cloud Deployment:** User entscheidet (siehe Erklärung oben)
- ❓ **UI/UX Phase 4:** User entscheidet (siehe Erklärung oben)

---

### IMPLEMENTATION PLAN - SCHRITT FÜR SCHRITT

#### BLOCK 1: Dokumentation (1-2h)

**Was wird erstellt:**

**Datei 1: `MASTER_FEATURES_v6.0.md`**
```markdown
Location: /Users/dominikfoert/git/KI_AutoAgent/MASTER_FEATURES_v6.0.md
Size: ~500-800 Zeilen
Content:
  - Vollständige Feature-Liste (implementiert, geplant, future)
  - Technologie-Stack Details
  - Spezialisierte Agents Übersicht
  - Advanced Features (Self-Diagnosis, Escalation, etc.)
  - Geplante Features (v5.9.2, v6.0, future)
  - Technical Debt Liste
```

**Datei 2: `PROGRESS_TRACKER_v6.0.md`**
```markdown
Location: /Users/dominikfoert/git/KI_AutoAgent/PROGRESS_TRACKER_v6.0.md
Size: ~300-400 Zeilen
Content:
  - Current Status Snapshot (v5.9.0 → v5.9.2 → v6.0-alpha)
  - What Works / Known Issues / In Progress
  - Architecture Quick Reference
  - LangGraph Best Practices Reference
  - FOR NEW CHAT SESSIONS (Quick Start Guide)
  - Common Questions & Answers
```

**Test Criteria:**
- [ ] Beide Dateien lesbar und formatiert (Markdown)
- [ ] Alle Features aus MD-Dokumenten gesammelt
- [ ] Quick Start Guide verständlich für neue Chat-Session

**Duration:** 1-2 Stunden

---

#### BLOCK 2: Phase 1 - Bug Fixes (2-3h)

**Bug Fix 1: Research Insights in Proposal**

File: `backend/agents/specialized/architect_agent.py`

Current Code (Line ~580-620):
```python
# TODO: Investigate what's passed to research_insights parameter
research_insights = ...  # Need to trace source
```

Investigation Steps:
1. Find WHO calls `generate_documentation_with_research()`
2. Check what's passed as `research_insights` parameter
3. Verify it's actual research content, not architect markdown

Expected Fix:
```python
# In caller function (likely in execute() method):
# Ensure we pass research_result.content, NOT self.proposal_markdown

async def execute(...):
    # Get research results
    research_insights = None
    if research_step:
        research_insights = research_step.result  # ✅ Actual research
        # NOT: research_insights = proposal_markdown  # ❌ Wrong!

    # Generate proposal
    proposal = await self.generate_documentation_with_research(
        design=design,
        research_insights=research_insights,  # ✅ Correct
        ...
    )
```

Test:
```bash
# Create test app and verify proposal contains research citations
# Expected: "research_insights": "Based on web research: MVVM pattern..."
# NOT: "research_insights": "# 🏗️ Architecture Proposal..."
```

**Bug Fix 2: Reviewer Skip Bug**

File: `backend/langgraph_system/workflow.py`

Investigation Steps:
1. Add DEBUG logging in `route_to_next_agent()` (Line 3202)
2. Log ALL steps when routing
3. Log specifically for reviewer step

Code Changes:
```python
# Line 3295-3365 in route_to_next_agent()

# CHECK 3: Find next pending step
for step in state["execution_plan"]:
    logger.info(f"  Step {step.id} ({step.agent}): {step.status}")

    # v5.9.2: SPECIAL logging for reviewer
    if step.agent == "reviewer":
        logger.info(f"    🔍 REVIEWER STEP DETAILS:")
        logger.info(f"       Status: {step.status}")
        logger.info(f"       Dependencies: {step.dependencies}")
        logger.info(f"       Dependencies met: {self._dependencies_met(step, state['execution_plan'])}")

        # Check dependency steps
        for dep_id in step.dependencies:
            dep_step = next((s for s in state["execution_plan"] if s.id == dep_id), None)
            if dep_step:
                logger.info(f"       Dependency {dep_id} status: {dep_step.status}")

    if step.status == "pending":
        if self._dependencies_met(step, state["execution_plan"]):
            # ... existing routing logic

            # v5.9.2: If routing to reviewer, extra confirmation
            if step.agent == "reviewer":
                logger.info(f"✅ CONFIRMED: Routing to REVIEWER for step {step.id}")
```

Test:
```bash
# Create calculator app
# Expected logs:
# "🔍 REVIEWER STEP DETAILS: Status: pending, Dependencies: ['step2']"
# "Dependency step2 status: completed"
# "✅ CONFIRMED: Routing to REVIEWER for step step3"
```

**Bug Fix 3: Error Handling for Skipped Tasks**

File: `backend/langgraph_system/workflow.py`

Code Changes:
```python
# Line 3330-3346 in route_to_next_agent()

if agent not in AVAILABLE_NODES:
    logger.warning(f"⚠️ Agent '{agent}' has no workflow node - marking as completed with stub")

    # v5.9.2: ADD ERROR TO STATE
    error_info = {
        "type": "agent_skipped",
        "agent": agent,
        "step_id": step.id,
        "reason": f"Agent '{agent}' not in AVAILABLE_NODES",
        "timestamp": datetime.now().isoformat()
    }

    state["errors"].append(error_info)

    # v5.9.2: SEND WEBSOCKET WARNING
    client_id = state.get("client_id")
    if client_id:
        try:
            # Import WebSocket manager
            from api.server_langgraph import manager

            await manager.send_json(client_id, {
                "type": "agent_warning",
                "message": f"⚠️ {agent} was skipped - not implemented yet",
                "details": error_info
            })
            logger.info(f"📤 Sent WebSocket warning to client {client_id}")
        except Exception as e:
            logger.error(f"❌ Failed to send WebSocket warning: {e}")

    # Mark as completed with stub
    state.update(update_step_status(
        state, step.id, "completed",
        result=f"⚠️ Agent '{agent}' not yet implemented",
        error=f"Agent not available: {agent}"
    ))
    continue
```

Frontend Handler (if needed):
```typescript
// vscode-extension/src/ui/MultiAgentChatPanel.ts
// Add handler for agent_warning type

this.backendClient.on('agent_warning', (message: any) => {
    this.sendMessage({
        type: 'warning',
        text: `⚠️ ${message.message}`,
        details: message.details
    });
});
```

Test:
```bash
# Trigger workflow with non-existent agent
# Expected: WebSocket warning in VS Code chat
# Expected: state["errors"] contains error_info
```

**Duration:** 2-3 Stunden

---

#### BLOCK 3: Phase 2 - Improvements (3-4h)

**Improvement 1: Checkpointer Upgrade**

File: `backend/langgraph_system/workflow.py`

Current Code (Line 5329-5332):
```python
# Use MemorySaver for simplicity
self.checkpointer = MemorySaver()
```

New Code:
```python
# v5.9.2: Upgrade to AsyncSqliteSaver for persistence
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import aiosqlite
import os

# Workspace-specific checkpoint DB
workspace_name = os.path.basename(self.workspace_path)
db_path = os.path.join(
    self.workspace_path,
    ".ki_autoagent_ws/cache/workflow_checkpoints.db"
)

# Ensure directory exists
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Initialize async SQLite checkpointer
try:
    # Create connection
    conn = await aiosqlite.connect(db_path)
    self.checkpointer = AsyncSqliteSaver(conn)
    logger.info(f"✅ Using AsyncSqliteSaver: {db_path}")
except Exception as e:
    logger.error(f"❌ Failed to init AsyncSqliteSaver: {e}")
    logger.warning("⚠️ Falling back to MemorySaver")
    self.checkpointer = MemorySaver()
```

Test:
```bash
# Run workflow
# Expected: .ki_autoagent_ws/cache/workflow_checkpoints.db created
# Expected: Workflow resumes after backend restart

# Test 1: Start workflow
# Test 2: Kill backend mid-workflow
# Test 3: Restart backend
# Test 4: Workflow continues from checkpoint
```

**Improvement 2: Routing Refactor - Dedicated Functions**

File: `backend/langgraph_system/workflow.py`

Add new methods (after `route_to_next_agent`):
```python
async def route_from_codesmith(self, state: ExtendedAgentState) -> str:
    """
    v5.9.2: Dedicated routing for codesmith
    ALWAYS route to reviewer after successful completion
    """
    logger.info("🔀 [CODESMITH ROUTING] Determining next step...")

    # Find codesmith step
    codesmith_step = next(
        (s for s in state["execution_plan"] if s.agent == "codesmith" and s.status == "completed"),
        None
    )

    if not codesmith_step:
        logger.error("❌ [CODESMITH ROUTING] No completed codesmith step found")
        return "end"

    logger.info(f"✅ [CODESMITH ROUTING] Codesmith completed: {codesmith_step.result[:100] if codesmith_step.result else 'No result'}")

    # Check if reviewer exists in execution_plan
    reviewer_step = next(
        (s for s in state["execution_plan"] if s.agent == "reviewer"),
        None
    )

    if reviewer_step:
        if reviewer_step.status == "pending":
            logger.info("✅ [CODESMITH ROUTING] Routing to REVIEWER")
            return "reviewer"
        else:
            logger.warning(f"⚠️ [CODESMITH ROUTING] Reviewer step exists but status is {reviewer_step.status}")
    else:
        logger.warning("⚠️ [CODESMITH ROUTING] No reviewer step in execution_plan")

    # Fallback: use generic routing
    logger.info("🔄 [CODESMITH ROUTING] Falling back to generic routing")
    return await self.route_to_next_agent(state)


async def route_from_reviewer(self, state: ExtendedAgentState) -> str:
    """
    v5.9.2: Dedicated routing for reviewer
    Route to fixer if quality < threshold, else END
    """
    logger.info("🔀 [REVIEWER ROUTING] Determining next step...")

    # Check quality score
    quality_score = state.get("last_quality_score", 1.0)
    threshold = state.get("quality_threshold", 0.8)

    logger.info(f"📊 [REVIEWER ROUTING] Quality: {quality_score}, Threshold: {threshold}")

    if quality_score < threshold:
        # Check iteration limit
        review_iteration = state.get("review_iteration", 0)
        max_iterations = state.get("max_review_iterations", 3)

        logger.info(f"🔄 [REVIEWER ROUTING] Iteration: {review_iteration + 1}/{max_iterations}")

        if review_iteration < max_iterations:
            logger.info(f"🔧 [REVIEWER ROUTING] Quality below threshold - routing to FIXER")
            state["review_iteration"] = review_iteration + 1
            return "fixer"
        else:
            logger.warning(f"⚠️ [REVIEWER ROUTING] Max iterations reached - ending despite low quality")
            return "end"

    logger.info("✅ [REVIEWER ROUTING] Quality passed - workflow complete")
    return "end"


async def route_from_fixer(self, state: ExtendedAgentState) -> str:
    """
    v5.9.2: Dedicated routing for fixer
    ALWAYS route back to reviewer for validation
    """
    logger.info("🔀 [FIXER ROUTING] Routing back to REVIEWER for validation")
    return "reviewer"
```

Update graph creation (Line 5286-5314):
```python
# v5.9.2: Use dedicated routing functions
workflow.add_conditional_edges(
    "codesmith",
    self.route_from_codesmith,
    {
        "reviewer": "reviewer",
        "orchestrator": "orchestrator",
        "end": END
    }
)

workflow.add_conditional_edges(
    "reviewer",
    self.route_from_reviewer,
    {
        "fixer": "fixer",
        "orchestrator": "orchestrator",
        "end": END
    }
)

workflow.add_conditional_edges(
    "fixer",
    self.route_from_fixer,
    {
        "reviewer": "reviewer",
        "orchestrator": "orchestrator",
        "end": END
    }
)

# Keep generic routing for other agents
for agent in ["research", "docbot", "performance", "tradestrat", "opus_arbitrator", "fixer_gpt"]:
    workflow.add_conditional_edges(
        agent,
        self.route_to_next_agent,
        {
            "orchestrator": "orchestrator",
            "architect": "architect",
            "codesmith": "codesmith",
            "reviewer": "reviewer",
            "fixer": "fixer",
            "research": "research",
            "fixer_gpt": "fixer_gpt",
            "docbot": "docbot",
            "performance": "performance",
            "tradestrat": "tradestrat",
            "opus_arbitrator": "opus_arbitrator",
            "end": END,
        }
    )
```

Test:
```bash
# Create calculator app
# Expected logs:
# "🔀 [CODESMITH ROUTING] Determining next step..."
# "✅ [CODESMITH ROUTING] Routing to REVIEWER"
# "🔀 [REVIEWER ROUTING] Determining next step..."
# "✅ [REVIEWER ROUTING] Quality passed - workflow complete"
```

**Duration:** 3-4 Stunden

---

#### BLOCK 4: Testing & Validation (2h)

**Test 1: Simple Calculator App**
```bash
# Start backend
cd ~/.ki_autoagent && ./start.sh

# Open VS Code
mkdir -p ~/Desktop/test-v5.9.2-calculator
cd ~/Desktop/test-v5.9.2-calculator
code .

# Send message: "Create a simple calculator web app"

Expected Results:
- ✅ Orchestrator decomposes task
- ✅ Architect designs HTML calculator
- ✅ Codesmith generates calculator.html
- ✅ Reviewer validates (NOT SKIPPED!)
- ✅ Workflow completes successfully
- ✅ calculator.html works in browser
- ✅ Checkpoint DB created: .ki_autoagent_ws/cache/workflow_checkpoints.db

Success Criteria:
- [ ] Reviewer executes (logs show "✅ CONFIRMED: Routing to REVIEWER")
- [ ] No "agent skipped" warnings
- [ ] Generated calculator works
- [ ] Checkpoint DB exists
```

**Test 2: Complex React + Vite App**
```bash
# Open new workspace
mkdir -p ~/Desktop/test-v5.9.2-react
cd ~/Desktop/test-v5.9.2-react
code .

# Send message: "Create a React todo app with Vite, TypeScript, and local storage"

Expected Results:
- ✅ Research finds React + Vite best practices
- ✅ Architect designs multi-file structure
- ✅ Codesmith generates:
  - package.json
  - tsconfig.json
  - tsconfig.node.json (MUST BE CREATED!)
  - vite.config.ts
  - src/App.tsx
  - src/main.tsx
- ✅ Reviewer validates all files
- ✅ npm install && npm run dev works

Success Criteria:
- [ ] All Vite files generated
- [ ] tsconfig.node.json present
- [ ] npm run dev starts without errors
- [ ] App runs in browser (localhost:5173)
```

**Test 3: Backend Restart Resume**
```bash
# Start calculator app workflow
# Kill backend mid-workflow (after codesmith, before reviewer)
kill $(pgrep -f "python.*server_langgraph")

# Restart backend
cd ~/.ki_autoagent && ./start.sh

# Expected: Workflow continues from last checkpoint
# Success: Reviewer runs and completes
```

**Duration:** 2 Stunden

---

#### BLOCK 5: Git Strategy & Release (1h)

**Git Branching:**
```bash
# Current branch: main (v5.9.0)

# Step 1: Create v5.9.2 release branch
git checkout -b release/v5.9.2

# Step 2: Commit all v5.9.2 changes
git add .
git commit -m "feat(v5.9.2): Documentation + Bug Fixes + Improvements

- Added MASTER_FEATURES_v6.0.md (complete feature list)
- Added PROGRESS_TRACKER_v6.0.md (quick start for new chats)
- Fixed research insights in architecture proposal
- Fixed reviewer skip bug with dedicated routing
- Added error handling for skipped agents
- Upgraded MemorySaver → AsyncSqliteSaver
- Refactored routing with dedicated functions per agent

Closes #[issue numbers if applicable]"

# Step 3: Merge to main
git checkout main
git merge release/v5.9.2

# Step 4: Tag release
git tag -a v5.9.2 -m "Release v5.9.2 - Bug Fixes & Improvements

## Bug Fixes
- Research insights now show actual research (not architect markdown)
- Reviewer no longer skipped after codesmith
- Error handling for skipped agents with WebSocket warnings

## Improvements
- AsyncSqliteSaver for persistent workflow state
- Dedicated routing functions per agent (cleaner, debuggable)
- Comprehensive feature documentation

## Testing
- Validated with simple calculator app
- Validated with complex React + Vite app
- All generated apps run without errors"

# Step 5: Push to remote
git push origin main
git push origin v5.9.2

# Step 6: Create GitHub Release
gh release create v5.9.2 \
  --title "v5.9.2 - Bug Fixes & Improvements" \
  --notes "See tag annotation for details" \
  --latest

# Step 7: Create v6.0-alpha development branch
git checkout -b dev/v6.0-alpha

# Step 8: Update version in files
# backend/version.json: "6.0.0-alpha.1"
# vscode-extension/package.json: "6.0.0-alpha"

git add .
git commit -m "chore: Initialize v6.0-alpha development branch

- Set version to 6.0.0-alpha.1
- Ready for LangGraph Templates migration
- Ready for Subgraphs implementation"

git push -u origin dev/v6.0-alpha
```

**Release Checklist:**
- [ ] All tests pass
- [ ] Documentation updated (CHANGELOG.md, CLAUDE.md)
- [ ] Version bumped in all files
- [ ] Tag created (v5.9.2)
- [ ] GitHub Release created
- [ ] v6.0-alpha branch created

**Duration:** 1 Stunde

---

#### BLOCK 6: v6.0-alpha Roadmap Planning (2h)

**Create Dokument: `V6_0_ALPHA_ROADMAP.md`**

```markdown
# KI AutoAgent v6.0-alpha Roadmap

## Mission: LangGraph Best Practices Adoption

### Phase 1: LangGraph Templates Migration (1 Woche)

**Goal:** Replace custom BaseAgent with `create_react_agent()`

**Tasks:**
1. Research Agent → Use create_react_agent() + Perplexity tool
2. Architect Agent → Keep custom (too specialized)
3. Codesmith Agent → Use create_react_agent() + file_tools
4. Reviewer Agent → Use create_react_agent() + browser_tester
5. Fixer Agent → Use create_react_agent() + file_tools

**Benefits:**
- Less code to maintain (BaseAgent: 2039 lines → ~500 lines)
- Standard-konform
- Better LangChain ecosystem integration

**Risks:**
- Breaking changes in agent behavior
- Loss of custom features
- Migration effort

**Mitigation:**
- Parallel implementation (old + new agents)
- Feature parity tests
- Gradual rollout

### Phase 2: Subgraphs Architecture (1-2 Wochen)

**Goal:** Supervisor + Worker Subgraphs

**Architecture:**
```
SupervisorGraph (Orchestrator)
├─ ResearchSubgraph (Worker 1)
│  └─ State: research_query, research_results
├─ ArchitectSubgraph (Worker 2)
│  └─ State: requirements, architecture_design
├─ CodesmithSubgraph (Worker 3)
│  └─ State: architecture, generated_files
└─ ReviewFixSubgraph (Worker 4 - Loop)
   ├─ Reviewer Node
   ├─ Fixer Node
   └─ State: code_files, review_feedback, quality_score
```

**Benefits:**
- True parallelization (Research + Architect can run concurrent)
- State isolation (each subgraph has own state)
- Cleaner separation of concerns
- Easier to test individual subgraphs

**Tasks:**
1. Define subgraph state schemas
2. Implement input/output transformations
3. Create supervisor routing logic
4. Migrate existing agents to subgraphs
5. Remove execution_plan (replaced by graph structure)

### Phase 3: Routing Logic Complete Overhaul (1 Woche)

**CRITICAL: Testing Strategy**

**Problem:**
- Routing war IMMER ein Riesenproblem
- Agents werden übersprungen
- Infinite loops
- Dependencies nicht erfüllt

**Solution: Test-First Development**

**Test Suite:**
```python
# tests/test_routing_v6.py

class TestSupervisorRouting:
    def test_simple_workflow_routes_correctly(self):
        """Test: research → architect → codesmith → reviewer → end"""
        pass

    def test_review_fail_routes_to_fixer(self):
        """Test: reviewer (fail) → fixer → reviewer (pass) → end"""
        pass

    def test_parallel_research_architect(self):
        """Test: research & architect run in parallel if no dependency"""
        pass

    def test_max_iterations_prevents_infinite_loop(self):
        """Test: reviewer → fixer loop stops after 3 iterations"""
        pass

    def test_subgraph_state_isolation(self):
        """Test: Research subgraph doesn't affect Codesmith state"""
        pass

# Golden Files (Snapshots)
tests/fixtures/routing/
  ├─ simple_calculator_workflow.json  # Expected routing steps
  ├─ complex_react_app_workflow.json
  └─ review_fix_loop_workflow.json
```

**Test Process:**
1. Write tests FIRST (TDD)
2. Implement routing logic
3. Run tests
4. Fix bugs
5. Repeat until all green
6. Create golden files for regression testing

**Acceptance Criteria:**
- [ ] 100% test coverage for routing logic
- [ ] No infinite loops possible
- [ ] All dependency chains validated
- [ ] Parallel execution works correctly
- [ ] State isolation verified

### Phase 4: AsyncSqliteSaver Full Migration (3 Tage)

**Tasks:**
1. Migrate ALL checkpointing to AsyncSqliteSaver
2. Implement checkpoint cleanup (delete old checkpoints)
3. Add checkpoint inspection tools
4. Test checkpoint resume after crash

### Phase 5: Cloud Deployment Support (Optional - 1 Woche)

**If User wants this:**
1. Create langgraph.json config
2. Add langgraph CLI support
3. Test deployment to LangGraph Cloud
4. Document deployment process
5. Support BOTH local + cloud

**If User doesn't want:**
- Skip this phase
- Keep local-only deployment

### Phase 6: UI/UX Enhancements (Optional - 1 Woche)

**If User wants this:**
1. Live progress updates
2. Expandable messages
3. Syntax highlighting
4. Clickable file references
5. Progress timeline

**If User doesn't want:**
- Skip this phase
- Keep current simple UI

---

## Timeline Summary

**Mandatory (v6.0-alpha):**
- Phase 1: Templates (1 Woche)
- Phase 2: Subgraphs (1-2 Wochen)
- Phase 3: Routing Tests (1 Woche)
- Phase 4: AsyncSqliteSaver (3 Tage)

**Total Mandatory:** 3-4 Wochen

**Optional:**
- Phase 5: Cloud (1 Woche)
- Phase 6: UI/UX (1 Woche)

**Total with Optional:** 5-6 Wochen

---

## Success Criteria

**Must Have:**
- [ ] All agents use create_react_agent() (except specialized)
- [ ] Subgraphs architecture implemented
- [ ] Routing logic 100% tested (no bugs)
- [ ] AsyncSqliteSaver working
- [ ] No execution_plan in State
- [ ] Pure declarative Graph edges

**Nice to Have:**
- [ ] Cloud deployment support
- [ ] Live progress updates
- [ ] Timeline visualization

---

## Risk Management

**High Risk: Routing Logic**
- Mitigation: Test-First Development (TDD)
- Mitigation: Golden Files for regression
- Mitigation: Gradual rollout (alpha → beta → stable)

**Medium Risk: Breaking Changes**
- Mitigation: Parallel implementation (v5.9.2 stays stable)
- Mitigation: Feature parity tests
- Mitigation: Migration guide for users

**Low Risk: Performance**
- Mitigation: Benchmark before/after
- Mitigation: Keep performance optimizations (uvloop, orjson)

---

**Last Updated:** 2025-10-08
**Status:** PLANNING PHASE
**Next:** User Approval → Start v5.9.2 Implementation
```

**Duration:** 2 Stunden

---

### SUMMARY: Was wird gemacht?

**Block 1: Dokumentation (1-2h)**
- Erstelle MASTER_FEATURES_v6.0.md
- Erstelle PROGRESS_TRACKER_v6.0.md

**Block 2: Bug Fixes (2-3h)**
- Fix Research Insights
- Fix Reviewer Skip Bug
- Add Error Handling

**Block 3: Improvements (3-4h)**
- Upgrade Checkpointer
- Refactor Routing

**Block 4: Testing (2h)**
- Test Calculator App
- Test React App
- Test Checkpoint Resume

**Block 5: Git Strategy (1h)**
- Commit & Push
- Create v5.9.2 Release
- Create v6.0-alpha Branch

**Block 6: v6.0 Planning (2h)**
- Erstelle V6_0_ALPHA_ROADMAP.md
- Plan LangGraph Templates Migration
- Plan Subgraphs Architecture
- Plan Routing Tests (CRITICAL!)

**Total Duration:** 11-15 Stunden (1.5-2 Arbeitstage)

---

### FRAGEN AN DICH:

1. **Cloud Deployment (Phase 5):**
   - Brauchst du: LangGraph Cloud support?
   - Oder: Nur local deployment OK?

2. **UI/UX (Phase 6):**
   - Brauchst du: Live progress, expandable messages, etc.?
   - Oder: Current UI ausreichend?

3. **v6.0 Timeline:**
   - Nur Mandatory (3-4 Wochen)?
   - Oder: Mit Optional (5-6 Wochen)?

---

**Status:** 🚦 AWAITING YOUR APPROVAL

**Soll ich anfangen? Welche Antworten auf die 3 Fragen?**
