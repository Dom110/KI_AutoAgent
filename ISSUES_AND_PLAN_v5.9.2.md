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

## 🚀 Next Steps

1. **Immediate (Today):** Fix critical bugs (Phase 1)
2. **Tomorrow:** Implement progress streaming (Phase 2)
3. **Day 3:** Build expandable UI (Phase 3)
4. **Day 3:** Test and release v5.9.2 (Phase 4)

---

**Document Version:** 1.0
**Last Updated:** 2025-10-08 12:00 PM
**Status:** READY FOR IMPLEMENTATION
