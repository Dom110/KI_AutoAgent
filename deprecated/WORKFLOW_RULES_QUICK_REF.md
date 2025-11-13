# 📄 WORKFLOW RULES - ONE PAGE QUICK REFERENCE

**Version:** 7.0 Pure MCP | **Print this page** for your desk!

---

## 🎯 THE COMPLETE WORKFLOW IN ONE TABLE

```
╔════════════════════════════════════════════════════════════════════════════╗
║              APP DEVELOPMENT WORKFLOW (CREATE/DEVELOP/FIX)                ║
╚════════════════════════════════════════════════════════════════════════════╝

┌─────────┬──────────────────────────────────────────────────┬─────────┐
│ Agent   │ Decision / Action                                │ Output  │
├─────────┼──────────────────────────────────────────────────┼─────────┤
│         │ 1. Always first                                  │         │
│ ARCHITECT│ 2. Existing architecture?                       │         │
│         │    ├─ YES: Improve? → YES: Research needed?     │ arch.   │
│         │    │                 ├─ YES: REQUEST RESEARCH   │ json    │
│         │    │                 └─ NO: Design improvements │         │
│         │    │                 [Complex? → HITL]          │         │
│         │    └─ NO: Research needed? → YES: REQUEST        │         │
│         │ 3. Create architecture.json + mermaid diagram   │         │
├─────────┼──────────────────────────────────────────────────┼─────────┤
│         │ 1. Find best practices for topic                │ research│
│ RESEARCH│ 2. Return findings + recommendations            │ _context│
│         │ 3. Back to ARCHITECT with context               │         │
│ (Opt.)  │                                                  │         │
├─────────┼──────────────────────────────────────────────────┼─────────┤
│         │ 1. Receive architecture from Architect           │ code    │
│ CODESMITH│ 2. Generate files: main.py, models.py, etc     │ files   │
│         │ 3. Write to workspace                            │         │
│         │ 4. Retry up to 3x if validation fails           │         │
├─────────┼──────────────────────────────────────────────────┼─────────┤
│         │ 1. Validate: Code matches architecture?         │ valid   │
│REVIEWFIX│ 2. Check: CRUD ops? Error handling? Syntax ok?  │ results │
│         │ 3. If PASS: → RESPONDER                         │         │
│         │    If FAIL & retries left: → CODESMITH fix       │         │
│         │    If FAIL & no retries: → RESPONDER (error)    │         │
├─────────┼──────────────────────────────────────────────────┼─────────┤
│ HITL    │ 1. Show architecture proposal to user            │ user    │
│(Opt.)   │ 2. Get approval or feedback                      │ feedback│
│         │ 3. If approved: → CODESMITH                      │         │
│         │    If feedback: → ARCHITECT (loop)               │         │
├─────────┼──────────────────────────────────────────────────┼─────────┤
│         │ 1. Receive: arch + code + validation results    │ formatted│
│RESPONDER│ 2. Format beautifully                            │ response│
│         │ 3. Show: what created, diagram, files, testing  │ ✅ DONE │
│         │ 4. USER SEES RESULT                             │         │
└─────────┴──────────────────────────────────────────────────┴─────────┘
```

---

## 🤔 ARCHITECT DECISION TREE (5 Decisions)

```
DECISION 1: Existing architecture?
└─ YES → DECISION 1b-1: Improvements?
         └─ YES → DECISION 1b-2: Research needed?
                  ├─ YES → RESEARCH → back to ARCHITECT
                  └─ NO → DECISION 1b-2a-1: Complex? → HITL or CODESMITH
         └─ NO → CODESMITH
└─ NO (Greenfield) → DECISION 1a-1: Research needed?
                     ├─ YES → RESEARCH → back to ARCHITECT
                     └─ NO → DESIGN → CODESMITH
```

---

## 🚦 SUPERVISOR ROUTING MATRIX

| Last Agent | If... | Then... |
|-----------|-------|---------|
| START | Initial | → ARCHITECT |
| ARCHITECT | needs_research=true | → RESEARCH |
| ARCHITECT | architecture_complete=true | → CODESMITH |
| ARCHITECT | needs_hitl=true | → HITL |
| RESEARCH | done | → ARCHITECT (with context) |
| CODESMITH | code_complete=true | → REVIEWFIX |
| REVIEWFIX | passed=true | → RESPONDER |
| REVIEWFIX | passed=false & retries<3 | → CODESMITH (fix) |
| REVIEWFIX | passed=false & retries≥3 | → RESPONDER (error) |
| HITL | approved=true | → CODESMITH |
| HITL | approved=false | → ARCHITECT (loop) |
| RESPONDER | done | → END (workflow complete) |

---

## 🔄 STATE FLOWS (Simplified)

**SIMPLE NEW APP:**
```
START → ARCHITECT:design → CODESMITH → REVIEWFIX:pass → RESPONDER → END
```

**COMPLEX NEW APP (with research):**
```
START → ARCHITECT → RESEARCH → ARCHITECT → CODESMITH → REVIEWFIX → RESPONDER → END
```

**EXISTING APP (with HITL):**
```
START → ARCHITECT → HITL → [approve] → CODESMITH → REVIEWFIX → RESPONDER → END
                         └─[feedback] → ARCHITECT [loop]
```

**CODE WITH ISSUES:**
```
START → ARCHITECT → CODESMITH → REVIEWFIX:fail → CODESMITH:fix → REVIEWFIX:pass → RESPONDER → END
```

---

## ⚠️ LOOP PREVENTION RULES

| Agent | Max Calls | Action |
|-------|-----------|--------|
| ARCHITECT | 3 | Force HITL or error |
| RESEARCH | 2 | Error |
| CODESMITH | 3 | → RESPONDER with error |
| REVIEWFIX | 1 | No retries (just fail) |
| RESPONDER | 1 | End workflow |
| HITL | 5 | End workflow |

**Max Iterations:** 20 total (then END)

---

## 📊 STATE FIELDS TO TRACK

**Architecture State:**
- `arch_state` = "none", "partial", "complete", "needs_review"
- `architecture` = {name, framework, db, layers, files, mermaid_diagram}

**Code State:**
- `code_state` = "none", "in_progress", "complete", "needs_fix"
- `generated_files` = list of created files

**Validation State:**
- `validation_state` = "not_run", "passed", "failed", "warnings"
- `validation_results` = {passed: T/F, issues: [...]}

**Agent Tracking:**
- `agent_call_count` = {architect: 1, research: 1, ...}
- `iteration` = current iteration counter
- `last_agent` = which agent just ran

---

## 🎯 DECISION LOGIC IN 10 LINES

```python
if not has_architecture(workspace):
    if needs_research(instructions):
        return RESEARCH
    return ARCHITECT → CODESMITH
else:
    if wants_improvements(instructions):
        if complex_change: return HITL
        if needs_research: return RESEARCH
    return CODESMITH
return CODESMITH → REVIEWFIX → RESPONDER
```

---

## ✅ CRITICAL SUCCESS FACTORS

1. ✅ **ARCHITECT FIRST:** Always start with Architect
2. ✅ **STATE TRACKING:** Track all state changes carefully
3. ✅ **LOOP PREVENTION:** Stop after 3 agent calls
4. ✅ **RESEARCH OPTIONAL:** Only if needed
5. ✅ **HITL FOR COMPLEX:** Ask user for complex changes
6. ✅ **CODESMITH FOLLOWS ARCH:** No freelancing!
7. ✅ **VALIDATE EVERYTHING:** ReviewFix is mandatory
8. ✅ **RESPONDER COMMUNICATES:** Beautiful output to user
9. ✅ **MCP PROTOCOL:** All via JSON-RPC, no direct calls
10. ✅ **ERROR RECOVERY:** Retry Codesmith max 3x

---

## 🚀 QUICK START: 3 STEPS

1. **Read:** APP_DEVELOPMENT_WORKFLOW_RULES.md (20 min)
2. **Review:** This page + WORKFLOW_VISUAL_DIAGRAM.md (20 min)
3. **Implement:** WORKFLOW_RULES_INTEGRATION_GUIDE.md Phase 1 (2 hours)

---

## 🆘 COMMON QUESTIONS

**Q: When do we need Research?**  
A: Specialized topics (ML, microservices). Standard stacks don't need it.

**Q: When do we need HITL?**  
A: Complex refactors with breaking changes. Simple updates skip it.

**Q: Can Codesmith skip Architect?**  
A: NO! Architecture is input to Codesmith. Must always follow it.

**Q: What if code validation fails 3x?**  
A: Go to Responder with error. Don't retry infinitely.

**Q: Can user modify architecture during HITL?**  
A: YES! Feedback loops back to Architect for revision.

**Q: Is RESPONDER always last?**  
A: YES! Responder is the only user-facing agent.

---

## 📁 FILES CREATED FOR YOU

```
✅ APP_DEVELOPMENT_WORKFLOW_RULES.md        ← Full spec
✅ ARCHITECT_AGENT_DECISION_TREE.md         ← Decision logic
✅ WORKFLOW_VISUAL_DIAGRAM.md               ← Diagrams (7 total)
✅ supervisor_routing_rules.py              ← Python class
✅ WORKFLOW_RULES_INTEGRATION_GUIDE.md      ← How to build
✅ WORKFLOW_RULES_SUMMARY.md                ← Overview
✅ WORKFLOW_RULES_INDEX.md                  ← Navigation
✅ WORKFLOW_RULES_QUICK_REF.md              ← This file!
```

---

## 🎓 WHERE TO FIND ANSWERS

| Question | Document | Section |
|----------|----------|---------|
| How does workflow work? | WORKFLOW_VISUAL_DIAGRAM.md | Diagram 1 |
| How does Architect decide? | ARCHITECT_AGENT_DECISION_TREE.md | Decision Tree |
| Show me examples | WORKFLOW_VISUAL_DIAGRAM.md | Diagram 6 |
| How do I implement? | WORKFLOW_RULES_INTEGRATION_GUIDE.md | Phase 1 |
| How to prevent loops? | WORKFLOW_VISUAL_DIAGRAM.md | Diagram 4 |
| What are state transitions? | WORKFLOW_VISUAL_DIAGRAM.md | Diagram 3 |
| Quick decision guide? | WORKFLOW_VISUAL_DIAGRAM.md | Diagram 5 |
| Agent roles? | WORKFLOW_VISUAL_DIAGRAM.md | Diagram 7 |

---

## 🌟 KEY INSIGHT

**The workflow is designed so that:**
- Architect plans the structure
- Codesmith builds the code  
- ReviewFix validates the result
- Responder communicates to user
- Supervisor orchestrates everything
- User approves complex changes (HITL)

**Result:** Predictable, quality app generation! ✅

---

**Print this page!** Keep it on your desk for quick reference.

**Last Updated:** 2025-11-03 | **Version:** 7.0 | **Status:** ✅ READY