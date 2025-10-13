# KI AutoAgent v6.0 - COMPLETE TEST PLAN

**Date:** 2025-10-08
**Status:** PLANNING - Awaiting Approval
**Principle:** EVERY feature tested in EVERY relevant phase

---

## 🧩 PART 1: FEATURE DEPENDENCY MATRIX

### Core Principle: **ALLE Agents nutzen ALLE gemeinsamen Features!**

| Feature | Research | Architect | Codesmith | Reviewer | Fixer | Why? |
|---------|----------|-----------|-----------|----------|-------|------|
| **Memory System** | ✅ | ✅ | ✅ | ✅ | ✅ | **ALL agents share memory!** Research findings → Architect context → Codesmith implementation → Reviewer checks → Fixer learns from mistakes |
| **Asimov Rules** | ✅ | ✅ | ✅ | ✅ | ✅ | **Security critical!** Research can't execute code, Codesmith can't delete files, Reviewer validates Asimov compliance |
| **Learning System** | ✅ | ✅ | ✅ | ✅ | ✅ | **Cross-session learning!** All agents learn from past successes/failures |
| **Tree-Sitter** | ⚠️ | ✅ | ✅ | ✅ | ✅ | Research: NO (no code). Architect: Analyze existing code. Codesmith: Parse templates. Reviewer: Validate syntax. Fixer: Understand bugs |
| **Markdown Gen** | ✅ | ✅ | ✅ | ✅ | ⚠️ | Research: Format findings. Architect: ADRs. Codesmith: README. Reviewer: Reports. Fixer: Minimal |
| **Graph Viz** | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | Research: NO. Architect: Architecture diagrams. Codesmith: Module dependencies. Reviewer: Call graphs. Fixer: Minimal |
| **File Tools** | ❌ | ⚠️ | ✅ | ✅ | ✅ | Research: NO (read-only web). Architect: Read templates. Codesmith: CREATE files. Reviewer: READ files. Fixer: MODIFY files |
| **Browser Testing** | ❌ | ❌ | ❌ | ✅ | ⚠️ | Only Reviewer runs browser tests. Fixer: Validates fixes work |
| **Quality Scoring** | ❌ | ⚠️ | ❌ | ✅ | ✅ | Architect: Self-eval. Reviewer: Main scorer. Fixer: Checks improvement |
| **Perplexity API** | ✅ | ⚠️ | ❌ | ❌ | ❌ | Research: Primary. Architect: Rare (tech research). Rest: NO |
| **Tool Discovery** | ✅ | ✅ | ✅ | ✅ | ✅ | **ALL agents!** Each can discover & use tools |
| **Curiosity System** | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | Research/Architect: High. Codesmith: Medium. Reviewer/Fixer: Low (task-focused) |
| **Self-Diagnosis** | ✅ | ✅ | ✅ | ✅ | ✅ | **ALL agents!** Detect when stuck, escalate |

**Legend:**
- ✅ = MUST have, test thoroughly
- ⚠️ = Optional/conditional, test if used
- ❌ = Should NOT have (security/design)

---

## 🔗 PART 2: AGENT COMMUNICATION FLOWS

### How Agents Share Context (via Memory!)

```
┌─────────────┐
│  Research   │ ──┐
└─────────────┘   │
                  ├──> Memory Store (FAISS + SQLite)
┌─────────────┐   │    - Research findings
│  Architect  │ ──┤    - Architecture decisions
└─────────────┘   │    - Code patterns
                  │    - Test results
┌─────────────┐   │    - Bug fixes
│  Codesmith  │ ──┤    - Quality scores
└─────────────┘   │    - Learnings
                  │
┌─────────────┐   │
│  Reviewer   │ ──┤
└─────────────┘   │
                  │
┌─────────────┐   │
│   Fixer     │ ──┘
└─────────────┘
```

**Critical Test:** Memory MUST persist across agents!

**Example Flow:**
1. Research finds: "React 18+ uses Vite, not CRA"
2. Memory stores: `{"tech": "vite", "source": "react docs", "confidence": 0.95}`
3. Architect reads memory: "Use Vite" → Architecture decision
4. Codesmith reads memory: Generates `vite.config.ts`
5. Reviewer reads memory: Validates Vite usage
6. Fixer reads memory: If error, knows Vite context

**If Memory fails:** Agents work in silos, duplicate work, make contradicting decisions!

---

## 📋 PART 3: REVISED PHASE TESTING

### PHASE 0: Foundation (ALREADY PLANNED)
- Cleanup
- Documentation
- Git branch

---

### PHASE 2: AsyncSqliteSaver + Base Memory (3-4h)

**Implementation:**
- AsyncSqliteSaver (workflow checkpoints)
- Base Memory System (FAISS + SQLite embeddings)
- Persistent Agent Memory class

**Test ALL:**
- ✅ AsyncSqliteSaver persists workflow state
- ✅ Memory system creates embeddings
- ✅ Memory system retrieves by similarity
- ✅ Memory persists across Python restarts
- ⚠️ Asimov: NOT YET (no agents to test)
- ⚠️ Learning: NOT YET (needs multiple runs)

**Native Test:**
```python
# Test memory persistence
workflow = WorkflowV6(workspace="/test")
workflow.memory.store("Test fact", metadata={"agent": "test"})
# Restart Python
workflow2 = WorkflowV6(workspace="/test")
results = workflow2.memory.query("Test fact")
assert len(results) > 0, "Memory not persisted!"
```

**Duration:** 3-4h

---

### PHASE 3: Research Subgraph (6-8h) ← INCREASED!

**Implementation:**
- ResearchSubgraph with create_react_agent()
- Perplexity tool integration
- Memory integration (store findings)
- Asimov rules (read-only, no file access)
- Learning (store successful searches)

**Test ALL:**
- ✅ **Memory:** Research stores findings to FAISS
- ✅ **Memory:** Research retrieves past searches
- ✅ **Asimov:** Research CANNOT execute code (blocked)
- ✅ **Asimov:** Research CANNOT write files (blocked)
- ✅ **Asimov:** Research CAN read web (allowed)
- ✅ **Learning:** Successful searches stored
- ✅ **Learning:** Failed searches marked (to avoid retry)
- ✅ **Markdown:** Research outputs formatted markdown
- ✅ **Tool Discovery:** Research finds Perplexity tool
- ✅ **Curiosity:** Research asks follow-up questions
- ✅ **Self-Diagnosis:** Research detects bad queries
- ⚠️ **Tree-Sitter:** NO (Research doesn't parse code)
- ⚠️ **Graphs:** NO (Research doesn't generate graphs)
- ⚠️ **File Tools:** NO (Research is read-only)

**Native Test:**
```python
# Test: Research Agent full workflow
query = "Best practices for React calculator app 2024"

# 1. Memory query (should find nothing first time)
past_research = memory.query(query, k=3)
assert len(past_research) == 0, "Clean slate expected"

# 2. Research execution
result = await research_subgraph.ainvoke({"query": query})

# 3. Validate results
assert "React" in result["findings"], "Research failed"
assert len(result["citations"]) > 0, "No sources found"

# 4. Memory check (should store findings)
stored = memory.query(query, k=1)
assert len(stored) > 0, "Memory not storing!"
assert "React" in stored[0]["content"], "Wrong content stored"

# 5. Asimov check (Research tried file access?)
asimov_violations = result.get("asimov_violations", [])
assert len(asimov_violations) == 0, "Research violated Asimov!"

# 6. Learning check
learnings = learning_system.get_learnings("research")
assert len(learnings) > 0, "Learning not stored!"

# 7. Markdown check
assert result["findings"].startswith("#"), "Not markdown format"
```

**Duration:** 6-8h (increased for comprehensive testing!)

---

### PHASE 4: Architect Subgraph (8-10h) ← INCREASED!

**Implementation:**
- ArchitectSubgraph (custom agent, not template - too specialized)
- Memory integration (read Research, store decisions)
- Tree-Sitter (analyze existing code if any)
- Markdown generation (ADRs, architecture docs)
- Graph visualization (architecture diagrams)
- Asimov rules (read files, no execution)
- Learning (store successful architectures)

**Test ALL:**
- ✅ **Memory:** Architect READS Research findings
- ✅ **Memory:** Architect STORES architecture decisions
- ✅ **Memory:** Cross-agent communication works (Research → Architect)
- ✅ **Asimov:** Architect CAN read files
- ✅ **Asimov:** Architect CANNOT execute code
- ✅ **Asimov:** Architect CANNOT delete files
- ✅ **Tree-Sitter:** Architect parses existing code (if workspace not empty)
- ✅ **Tree-Sitter:** Architect analyzes project structure
- ✅ **Markdown:** Architect generates ADRs
- ✅ **Markdown:** Architect generates architecture docs
- ✅ **Graph Viz:** Architect generates architecture diagrams (Mermaid)
- ✅ **Graph Viz:** Architect generates C4 diagrams
- ✅ **Learning:** Architect stores successful patterns
- ✅ **Learning:** Architect retrieves similar past projects
- ✅ **Tool Discovery:** Architect finds diagram tools
- ✅ **Curiosity:** Architect asks clarifying questions
- ✅ **Self-Diagnosis:** Architect detects unclear requirements

**Native Test:**
```python
# Test: Architect Agent full workflow WITH Research context

# 1. Setup: Research has already run
research_results = {
    "findings": "React 18 with Vite is recommended...",
    "citations": [...]
}
memory.store(research_results, metadata={"agent": "research", "query": "calculator"})

# 2. Architect execution (should READ Research from memory)
result = await architect_subgraph.ainvoke({
    "requirements": "Create calculator app",
    "workspace_path": "/test-workspace"
})

# 3. Validate Architect READ Research findings
assert "Vite" in result["tech_stack"], "Architect didn't read Research!"
assert "React" in result["tech_stack"], "Architect didn't use Research!"

# 4. Memory check (Architect stored decisions)
decisions = memory.query("architecture decision calculator", k=3)
assert len(decisions) > 0, "Architect didn't store decisions!"

# 5. Tree-Sitter check (if existing code)
if has_existing_code:
    assert result["existing_code_analysis"] is not None, "Didn't analyze code"

# 6. Markdown check (ADRs generated)
assert "ADR" in result["documentation"], "No ADR generated"
assert result["documentation"].startswith("#"), "Not markdown"

# 7. Graph check (diagrams generated)
assert "graph" in result or "mermaid" in result["documentation"], "No diagram"

# 8. Asimov check
violations = result.get("asimov_violations", [])
assert len(violations) == 0, "Architect violated Asimov!"

# 9. Learning check
learnings = learning_system.get_learnings("architect")
assert len(learnings) > 0, "Architect didn't learn!"
```

**Duration:** 8-10h (testing ALLE features!)

---

### PHASE 5: Codesmith Subgraph (10-12h) ← SIGNIFICANTLY INCREASED!

**Why longer?** Codesmith MUST:
- Read Research findings
- Read Architect design
- Generate ACTUAL files
- Parse own output (Tree-Sitter)
- Generate documentation (Markdown)
- Generate dependency graphs
- Respect Asimov rules (file permissions)
- Learn from past code

**Implementation:**
- CodesmithSubgraph with create_react_agent()
- File tools (create, write, read)
- Memory integration (read Research + Architect, store code patterns)
- Tree-Sitter (parse generated code for validation)
- Markdown (README, code comments)
- Graph Viz (module dependency graphs)
- Asimov rules (CAN write files, CANNOT delete, CANNOT execute)
- Learning (store successful code patterns)

**Test ALL:**
- ✅ **Memory:** Codesmith READS Research findings
- ✅ **Memory:** Codesmith READS Architect design
- ✅ **Memory:** Codesmith STORES code patterns
- ✅ **Memory:** Cross-agent communication (Research → Architect → Codesmith)
- ✅ **Asimov:** Codesmith CAN create files
- ✅ **Asimov:** Codesmith CAN write files
- ✅ **Asimov:** Codesmith CANNOT delete files
- ✅ **Asimov:** Codesmith CANNOT execute code
- ✅ **Asimov:** Codesmith CANNOT access network (except APIs)
- ✅ **Tree-Sitter:** Codesmith parses OWN generated code
- ✅ **Tree-Sitter:** Codesmith validates syntax before committing
- ✅ **Markdown:** Codesmith generates README.md
- ✅ **Markdown:** Codesmith generates code comments
- ✅ **Markdown:** Codesmith generates API docs
- ✅ **Graph Viz:** Codesmith generates module dependency graph
- ✅ **Graph Viz:** Codesmith generates component tree
- ✅ **File Tools:** Files actually created on filesystem
- ✅ **File Tools:** File permissions correct
- ✅ **Learning:** Codesmith stores successful patterns
- ✅ **Learning:** Codesmith retrieves similar code
- ✅ **Tool Discovery:** Codesmith finds file tools
- ✅ **Curiosity:** Codesmith asks about unclear design
- ✅ **Self-Diagnosis:** Codesmith detects incomplete spec

**Native Test:**
```python
# Test: Codesmith full workflow WITH context

# 1. Setup: Research + Architect already ran
memory.store({
    "agent": "research",
    "findings": "Vite + React 18 recommended"
})
memory.store({
    "agent": "architect",
    "tech_stack": ["React", "TypeScript", "Vite"],
    "file_structure": {
        "src/App.tsx": "Main component",
        "src/main.tsx": "Entry point",
        "vite.config.ts": "Build config"
    }
})

# 2. Codesmith execution
result = await codesmith_subgraph.ainvoke({
    "requirements": "Calculator app",
    "workspace_path": "/test-workspace"
})

# 3. Validate files CREATED
assert os.path.exists("/test-workspace/src/App.tsx"), "App.tsx not created!"
assert os.path.exists("/test-workspace/vite.config.ts"), "vite.config not created!"
assert os.path.exists("/test-workspace/README.md"), "README not created!"

# 4. Validate Codesmith READ context from memory
with open("/test-workspace/vite.config.ts") as f:
    config = f.read()
    assert "react" in config.lower(), "Didn't use React from context!"

# 5. Tree-Sitter validation (Codesmith parsed own code)
assert result["syntax_valid"] == True, "Generated code has syntax errors!"
assert len(result["parse_errors"]) == 0, "Parser found errors!"

# 6. Markdown validation (README generated)
with open("/test-workspace/README.md") as f:
    readme = f.read()
    assert readme.startswith("#"), "README not markdown!"
    assert "Calculator" in readme, "README missing project name!"

# 7. Graph validation (dependency graph)
assert result["dependency_graph"] is not None, "No dependency graph!"
assert "mermaid" in result or "graphviz" in result, "No graph format!"

# 8. Asimov validation (file operations logged)
operations = result.get("file_operations", [])
assert all(op["type"] in ["create", "write", "read"] for op in operations), "Invalid operations!"
assert not any(op["type"] == "delete" for op in operations), "Codesmith deleted files!"
assert not any(op["type"] == "execute" for op in operations), "Codesmith executed code!"

# 9. Memory validation (patterns stored)
patterns = memory.query("vite react code pattern", k=3)
assert len(patterns) > 0, "Codesmith didn't store patterns!"

# 10. Learning validation
learnings = learning_system.get_learnings("codesmith")
assert len(learnings) > 0, "Codesmith didn't learn!"
assert "vite" in str(learnings).lower(), "Wrong learning stored!"
```

**Duration:** 10-12h (MOST COMPLEX AGENT!)

---

### PHASE 6: ReviewFix Subgraph (12-16h) ← SIGNIFICANTLY INCREASED!

**Why longest?** Reviewer & Fixer together MUST:
- Read ALL previous context (Research → Architect → Codesmith)
- Validate Asimov compliance (CRITICAL!)
- Parse code (Tree-Sitter)
- Run browser tests
- Generate test reports (Markdown)
- Generate coverage graphs
- Fix bugs
- Learn from mistakes
- Loop correctly (no infinite loops!)

**Implementation:**
- ReviewFixSubgraph (loop with Reviewer + Fixer)
- Reviewer: create_react_agent(browser_tester)
- Fixer: create_react_agent(file_tools)
- Both share memory
- Asimov validation (Reviewer checks, Fixer enforces)
- Tree-Sitter (both parse code)
- Markdown (test reports)
- Graphs (coverage, quality trends)
- Learning (both learn)
- Quality scoring
- Max iterations (prevent infinite loops)

**Test ALL:**

**Reviewer Tests:**
- ✅ **Memory:** Reviewer READS all context (Research, Architect, Codesmith)
- ✅ **Memory:** Reviewer STORES test results
- ✅ **Asimov:** Reviewer VALIDATES Codesmith followed rules
- ✅ **Asimov:** Reviewer checks for security violations
- ✅ **Asimov:** Reviewer validates file permissions
- ✅ **Tree-Sitter:** Reviewer parses generated code
- ✅ **Tree-Sitter:** Reviewer detects syntax errors
- ✅ **Tree-Sitter:** Reviewer analyzes complexity
- ✅ **Markdown:** Reviewer generates test report
- ✅ **Markdown:** Reviewer formats findings
- ✅ **Graph Viz:** Reviewer generates coverage graph
- ✅ **Graph Viz:** Reviewer generates quality trends
- ✅ **Browser Testing:** Reviewer runs app in browser
- ✅ **Browser Testing:** Reviewer validates UI
- ✅ **Quality Scoring:** Reviewer scores code (0-1)
- ✅ **Quality Scoring:** Score based on multiple factors
- ✅ **Learning:** Reviewer stores test strategies
- ✅ **Tool Discovery:** Reviewer finds browser tools
- ✅ **Self-Diagnosis:** Reviewer detects when tests fail

**Fixer Tests:**
- ✅ **Memory:** Fixer READS Reviewer feedback
- ✅ **Memory:** Fixer READS original requirements
- ✅ **Memory:** Fixer STORES bug fixes
- ✅ **Asimov:** Fixer CAN modify files
- ✅ **Asimov:** Fixer CANNOT delete original files (only modify)
- ✅ **Asimov:** Fixer CANNOT execute code
- ✅ **Tree-Sitter:** Fixer parses code to understand bugs
- ✅ **Tree-Sitter:** Fixer validates fixes don't break syntax
- ✅ **File Tools:** Fixer modifies files
- ✅ **Markdown:** Fixer documents changes (optional)
- ✅ **Learning:** Fixer stores successful fix patterns
- ✅ **Learning:** Fixer learns from failures
- ✅ **Tool Discovery:** Fixer finds file tools
- ✅ **Self-Diagnosis:** Fixer detects when fix doesn't work

**Loop Tests:**
- ✅ **Max Iterations:** Loop stops after 3 iterations
- ✅ **Quality Threshold:** Loop stops when score >= 0.8
- ✅ **Infinite Loop Prevention:** CRITICAL TEST!
- ✅ **Memory Accumulation:** Each iteration learns from previous

**Native Test:**
```python
# Test: ReviewFix Loop full workflow

# 1. Setup: Codesmith generated code (with intentional bug)
codesmith_result = {
    "files": [
        {"path": "src/App.tsx", "content": "const x = 1/0; // BUG!"},
    ]
}
memory.store(codesmith_result, metadata={"agent": "codesmith"})

# 2. Execute ReviewFix loop
result = await reviewfix_subgraph.ainvoke({
    "generated_files": codesmith_result["files"],
    "quality_threshold": 0.8,
    "max_iterations": 3
})

# 3. Validate Reviewer ran
assert result["review_iteration"] > 0, "Reviewer never ran!"
assert "quality_score" in result, "No quality score!"

# 4. Validate Reviewer READ context
reviewer_used_context = any(
    "research" in m or "architect" in m
    for m in memory.query("calculator", k=10)
)
assert reviewer_used_context, "Reviewer didn't read context!"

# 5. Validate Asimov check by Reviewer
assert "asimov_report" in result, "Reviewer didn't check Asimov!"
if "1/0" in codesmith_result["files"][0]["content"]:
    # Reviewer should flag this as suspicious
    assert result["quality_score"] < 0.8, "Reviewer missed bug!"

# 6. Validate Tree-Sitter usage
assert "parse_errors" in result or "syntax_check" in result, "No Tree-Sitter!"

# 7. Validate Browser Testing
assert "browser_test_result" in result, "No browser test!"

# 8. Validate Markdown report
assert "test_report" in result, "No test report!"
assert result["test_report"].startswith("#"), "Report not markdown!"

# 9. Validate Graph generation
assert "coverage_graph" in result or "quality_graph" in result, "No graphs!"

# 10. Validate Fixer ran (if needed)
if result["quality_score"] < 0.8:
    assert result["review_iteration"] >= 2, "Fixer didn't run!"
    assert "fixed_files" in result, "Fixer didn't fix!"

# 11. Validate Fixer READ Reviewer feedback
if "fixed_files" in result:
    fixer_fixes = result["fixed_files"]
    assert "1/0" not in str(fixer_fixes), "Fixer didn't fix bug!"

# 12. Validate Loop termination
assert result["review_iteration"] <= 3, "Loop didn't stop at max!"

# 13. Validate Memory persistence (learning)
learnings_reviewer = learning_system.get_learnings("reviewer")
learnings_fixer = learning_system.get_learnings("fixer")
assert len(learnings_reviewer) > 0, "Reviewer didn't learn!"
if result["review_iteration"] >= 2:
    assert len(learnings_fixer) > 0, "Fixer didn't learn!"

# 14. CRITICAL: Quality improvement check
if result["review_iteration"] >= 2:
    assert result["quality_score"] > result["initial_quality_score"], "Quality didn't improve!"
```

**Duration:** 12-16h (MOST TESTING!)

---

## 📊 PART 4: CUMULATIVE FEATURE TESTING

### Testing Progression

| Phase | New Features | Cumulative Features Tested |
|-------|--------------|----------------------------|
| 2 | AsyncSqliteSaver, Base Memory | 2 |
| 3 | Research Agent, Perplexity | 2 + 8 = 10 |
| 4 | Architect Agent, Tree-Sitter, Graphs | 10 + 4 = 14 |
| 5 | Codesmith Agent, File Tools | 14 + 2 = 16 |
| 6 | ReviewFix Loop, Browser Testing, Quality | 16 + 3 = 19 |

**By Phase 6:** ALL 19+ features tested!

---

## 🎯 PART 5: INTEGRATION TESTING MATRIX

### Phase 7: Supervisor Integration (8-10h)

**Test:** ALL agents working together through Supervisor

**Test Scenarios:**

**Scenario 1: Simple Calculator (HTML)**
- Supervisor decomposes task
- Research finds best practices
- Architect designs single-file HTML
- Codesmith generates calculator.html
- Reviewer validates (browser test)
- (Fixer: only if issues)
- **Test ALL features in workflow:**
  - Memory: All agents share context
  - Asimov: All agents respect rules
  - Tree-Sitter: Parse HTML/JS
  - Markdown: README generated
  - Graphs: Architecture diagram
  - Learning: All agents learn
  - Browser: Reviewer tests in browser
  - Quality: Score >= 0.8

**Scenario 2: Complex React + Vite App**
- Research finds React 18 + Vite patterns
- Architect designs multi-file structure
- Codesmith generates:
  - package.json
  - vite.config.ts
  - tsconfig.json
  - tsconfig.node.json
  - src/App.tsx
  - src/main.tsx
  - README.md
- Reviewer validates:
  - npm install works
  - npm run dev works
  - Browser loads app
  - Asimov compliance
  - Code quality
- Fixer (if needed): Fix any issues
- **Test ALL features + additional:**
  - Memory: Complex multi-agent context
  - Tree-Sitter: Parse TypeScript
  - Graphs: Module dependencies
  - Multiple file operations
  - Build system validation

**Duration:** 8-10h

---

### Phase 8: End-to-End Feature Testing (12-16h)

**Test:** EVERY feature explicitly

**Test Matrix:**

| Feature | Test Method | Success Criteria |
|---------|-------------|------------------|
| Memory System | Store 100 facts, retrieve by similarity | 95%+ accuracy |
| Asimov Rules | Try 20 forbidden operations | 100% blocked |
| Tree-Sitter | Parse 10 different languages | 95%+ success |
| Graphs | Generate 5 diagram types | All render |
| Markdown | Generate 10 doc types | All valid markdown |
| Learning | 10 tasks, check improvements | 80%+ better |
| Curiosity | 5 ambiguous tasks | Asks clarifications |
| Agentic RAG | 5 knowledge queries | Retrieves correct docs |
| Neurosymbolic | 3 reasoning tasks | Logical consistency |
| Self-Diagnosis | 5 stuck scenarios | Escalates correctly |
| Tool Discovery | 10 tools available | Finds all |
| Browser Testing | 5 web apps | All load correctly |
| Quality Scoring | 10 code samples | Scores match manual review |
| File Operations | Create/Read/Write 100 files | 100% success |
| Checkpoint Resume | Interrupt 5 workflows | All resume |

**Duration:** 12-16h

---

## ⏱️ REVISED TIME ESTIMATES

| Phase | Original | Revised | Reason |
|-------|----------|---------|--------|
| 0 | 2-3h | 2-3h | ✅ Same |
| 2 | 2-3h | 3-4h | + Base Memory System |
| 3 | 4-6h | 6-8h | + Comprehensive testing |
| 4 | 3-4h | 8-10h | + ALL features (Tree-Sitter, Graphs, Memory) |
| 5 | 4-6h | 10-12h | + MOST features (Files, Graphs, Memory, Tree-Sitter) |
| 6 | 6-8h | 12-16h | + ALL features + Loop testing |
| 7 | 4-6h | 8-10h | + Supervisor integration |
| 8 | 8-10h | 12-16h | + EVERY feature explicitly |
| 9 | 3-4h | 3-4h | ✅ Same (Frontend) |
| 10 | 4-6h | 4-6h | ✅ Same (Polish) |

**Original Total:** 40-60h development + 30-40h testing = 70-100h
**Revised Total:** 60-80h development + 50-70h testing = **110-150h**

**Why increase?**
- ✅ You're RIGHT: ALL features in ALL phases
- ✅ Comprehensive testing prevents bugs later
- ✅ Credits saved from skipping v5.9.2 invested in quality

---

## 🚀 APPROVAL REQUIRED

**This is the CORRECT, COMPLETE test plan!**

**Key Changes from original:**
1. ✅ **ALL agents test Memory** (not just Research)
2. ✅ **ALL agents test Asimov** (critical security!)
3. ✅ **ALL agents test Learning** (cross-session intelligence)
4. ✅ **Codesmith tests Tree-Sitter** (parses own code!)
5. ✅ **Reviewer tests EVERYTHING** (validates full stack!)
6. ✅ **Fixer knows Codesmith + Reviewer** (via Memory!)
7. ✅ **Explicit feature testing matrix** (nothing missed!)
8. ✅ **Increased time estimates** (realistic!)

**Bereit zum Start mit diesem COMPLETE Plan?**

**Next:** Phase 0 (Cleanup) → Phase 2 (Foundation) → Phase 3-6 (Agents) → Phase 7-8 (Integration)

**Soll ich anfangen?** 🚀
