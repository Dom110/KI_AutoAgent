# 🏗️ ARCHITECT AGENT DECISION TREE v7.0 (PURE MCP)

## Overview

Dieser Decision Tree dokumentiert **ALLE Entscheidungen**, die der Architekt Agent treffen muss, um die richtige Architektur zu entwerfen.

**MCP Server:** `architect_agent_server.py`  
**Entry Point:** SupervisorMCP.decide_next() → route to "architect"  
**Output:** `architecture` state field + JSON files

---

## 🌳 DECISION TREE FULL FLOW

```
START: Architect erhält Instructions + workspace_path
│
├─────────────────────────────────────────────────────────────────┐
│ DECISION 1: Gibt es EXISTIERENDE Architektur-Dateien?          │
│ CHECK: tree-sitter analyse? architecture.md? mermaid.yaml?     │
│                                                                 │
│ Methode: Workspace-Analyse mit TreeSitterAnalyzer              │
│          - Prüfe auf .architecture/ Verzeichnis                │
│          - Prüfe auf structure.mermaid                         │
│          - Prüfe auf architecture.json                         │
│          - Prüfe auf architecture.md                           │
└─────────────────────────────────────────────────────────────────┘
│
├─ NEIN (Greenfield / New Project)
│  │
│  └──────────────────────────────────────────────────────────────┐
│  │ ENTSCHEIDUNG 1a: GREENFIELD MODE                            │
│  │                                                               │
│  │ Subtask: Planen neue Architektur from scratch                │
│  └──────────────────────────────────────────────────────────────┘
│     │
│     └─────────────────────────────────────────────────────────────┐
│     │ DECISION 1a-1: Brauchen wir RESEARCH für Specialties?      │
│     │ CHECK: Ist es Standard-Stack (Django, FastAPI, React)?    │
│     │        ODER speziell (Machine Learning, Blockchain)?      │
│     │                                                             │
│     │ Beispiele:                                                  │
│     │ - Standard: "REST API with FastAPI" → NO research         │
│     │ - Standard: "React todo app" → NO research                │
│     │ - Special: "ML pipeline with PyTorch" → YES research      │
│     │ - Special: "Real-time trading platform" → YES research    │
│     └─────────────────────────────────────────────────────────────┘
│        │
│        ├─ NEIN (Standard Stack)
│        │  │
│        │  └─ FLOW: Standard_Architecture_Design
│        │     └─ Return SupervisorDecision:
│        │        {
│        │          "action": "CONTINUE",
│        │          "next_agent": "codesmith",
│        │          "instructions": "Implement based on architecture",
│        │          "state_update": {
│        │            "architecture": {
│        │              "name": "...",
│        │              "framework": "...",
│        │              "database": "...",
│        │              "files": [...],
│        │              "layers": { ... }
│        │            },
│        │            "architecture_complete": true
│        │          }
│        │        }
│        │
│        └─ JA (Specialized / Needs Research)
│           │
│           └─ FLOW: RequestResearch
│              └─ Return SupervisorDecision:
│                 {
│                   "action": "CONTINUE",
│                   "next_agent": "research",
│                   "instructions": "Research {topic} best practices",
│                   "state_update": {
│                     "needs_research": true,
│                     "research_request": "Find best practices for {topic}",
│                     "last_agent": "architect"
│                   }
│                 }
│              
│              Supervisor calls Research Agent
│              │
│              └─ AFTER Research returns:
│                 Supervisor leitet ZURÜCK zu Architect mit research_context
│                 │
│                 └─ FLOW: Design_With_Research_Context
│                    └─ Architect erstellt Architektur MIT research findings
│                       └─ Return SupervisorDecision:
│                          {
│                            "action": "CONTINUE",
│                            "next_agent": "codesmith",
│                            "instructions": "Implement with research context",
│                            "state_update": {
│                              "architecture": {
│                                "name": "...",
│                                "based_on": research_context.findings,
│                                ...
│                              },
│                              "architecture_complete": true
│                            }
│                          }
│
│
└─ JA (Existing Project)
   │
   └──────────────────────────────────────────────────────────────┐
   │ ENTSCHEIDUNG 1b: EXISTING MODE                              │
   │                                                               │
   │ Subtask: Analyze existing, decide on improvements            │
   └──────────────────────────────────────────────────────────────┘
      │
      └─────────────────────────────────────────────────────────────┐
      │ DECISION 1b-1: Sind VERBESSERUNGEN der Architektur nötig? │
      │ CHECK: User asked for improvements?                        │
      │        Instructions contain "refactor" / "improve" ?       │
      │        Existing architecture analysis suggests changes?    │
      │                                                             │
      │ Methode: Parse instructions keyword matching               │
      │          - "improve", "refactor", "modernize"             │
      │          - "add", "modify", "enhance"                     │
      │          - Existing code quality analysis                  │
      └─────────────────────────────────────────────────────────────┘
         │
         ├─ NEIN (Use As-Is)
         │  │
         │  └─ FLOW: Use_Existing_Architecture
         │     └─ Parse existing architecture files
         │        └─ Return SupervisorDecision:
         │           {
         │             "action": "CONTINUE",
         │             "next_agent": "codesmith",
         │             "instructions": "Extend existing based on: ...",
         │             "state_update": {
         │               "architecture": { ... parsed ... },
         │               "architecture_complete": true
         │             }
         │           }
         │
         └─ JA (Refactor / Improve)
            │
            └─────────────────────────────────────────────────────────┐
            │ DECISION 1b-2: Brauchen wir RESEARCH für Verbesserungen?│
            │ CHECK: Ist Verbesserung Standard?                       │
            │        (Add new endpoint) → NO research                 │
            │        (Modernize to microservices) → YES research      │
            │                                                          │
            │ Beispiele:                                               │
            │ - "Add todo delete endpoint" → Standard, NO research   │
            │ - "Add authentication" → Standard, NO research         │
            │ - "Migrate to microservices" → Specialized, research  │
            │ - "Improve performance for 1M users" → Research needed │
            └─────────────────────────────────────────────────────────┘
               │
               ├─ NEIN (Standard Improvements)
               │  │
               │  └─────────────────────────────────────────────────────────┐
               │  │ DECISION 1b-2a: Refactor ohne Research                 │
               │  │                                                         │
               │  │ Subtask: Design improved architecture without research  │
               │  │ Methode: Analyze existing + apply best practices       │
               │  └─────────────────────────────────────────────────────────┘
               │     │
               │     └─────────────────────────────────────────────────────────┐
               │     │ DECISION 1b-2a-1: Ist HITL nötig?                     │
               │     │ CHECK: Komplexe Änderung?                            │
               │     │        Könnte User Feedback haben?                   │
               │     │        Architecture-Change breaking?                 │
               │     │                                                       │
               │     │ Richtlinien:                                         │
               │     │ - Minor improvements (add field) → NO HITL           │
               │     │ - Major refactor (new structure) → YES HITL          │
               │     │ - Pattern changes (monolith→modular) → YES HITL     │
               │     └─────────────────────────────────────────────────────────┘
               │        │
               │        ├─ NEIN (Minor / Clear)
               │        │  │
               │        │  └─ FLOW: Refactor_Direct_To_Codesmith
               │        │     └─ Return SupervisorDecision:
               │        │        {
               │        │          "action": "CONTINUE",
               │        │          "next_agent": "codesmith",
               │        │          "instructions": "Refactor with improvements: ...",
               │        │          "state_update": {
               │        │            "architecture": { ... improved ... }
               │        │          }
               │        │        }
               │        │
               │        └─ JA (Major / User Input Needed)
               │           │
               │           └─ FLOW: Request_HITL
               │              └─ Return SupervisorDecision:
               │                 {
               │                   "action": "CONTINUE",
               │                   "next_agent": "hitl",
               │                   "instructions": "Review architecture changes",
               │                   "state_update": {
               │                     "hitl_data": {
               │                       "current_architecture": { ... },
               │                       "proposed_architecture": { ... },
               │                       "mermaid_diagram": "...",
               │                       "improvements": [...]
               │                     }
               │                   }
               │                 }
               │              
               │              Supervisor calls HITL Node
               │              │
               │              ├─ CASE: User Approves (hitl_response == "approve")
               │              │  │
               │              │  └─ Supervisor leitet zu CODESMITH
               │              │     with approved architecture
               │              │
               │              └─ CASE: User Declines or Modifies
               │                 │
               │                 └─ User Input erhalten
               │                    └─ Supervisor leitet ZURÜCK zu Architect
               │                       with user_feedback
               │                       │
               │                       └─ LOOP zu Decision 1b-2a-1
               │
               └─ JA (Specialized Improvements)
                  │
                  └─ FLOW: RequestResearch_For_Improvements
                     └─ Return SupervisorDecision:
                        {
                          "action": "CONTINUE",
                          "next_agent": "research",
                          "instructions": "Research best practices for: ...",
                          "state_update": {
                            "needs_research": true,
                            "research_request": "..."
                          }
                        }
                     
                     Supervisor calls Research Agent
                     │
                     └─ AFTER Research returns:
                        Supervisor leitet ZURÜCK zu Architect mit research_context
                        │
                        └─ FLOW: Design_Improvements_With_Research
                           Architect erstellt verbesserte Architektur MIT research findings
                           │
                           └─────────────────────────────────────────────────────────┐
                           │ DECISION 1b-2b-1: Ist HITL nötig? (mit research)      │
                           │                                                        │
                           │ Richtlinien:                                          │
                           │ - Research findings clear → NO HITL                   │
                           │ - Research findings ambiguous → YES HITL              │
                           │ - Major changes based on research → YES HITL          │
                           └─────────────────────────────────────────────────────────┘
                              │
                              ├─ NEIN
                              │  └─ Gehe zu CODESMITH (wie oben)
                              │
                              └─ JA
                                 └─ Gehe zu HITL (mit research context + improvements)


END: Architecture complete + passed to Codesmith
```

---

## 📊 DECISION TABLE

| Decision Node | Condition | YES Path | NO Path |
|---------------|-----------|----------|---------|
| 1: Existing? | Workspace has .architecture/ or architecture.md? | → 1b (Existing Mode) | → 1a (Greenfield) |
| 1a-1: Research needed? | Standard stack (FastAPI, React, Django)? | → RESEARCH | → Design Standard |
| 1b-1: Improvements? | "refactor"/"improve"/"add" in instructions? | → 1b-2 | → Use As-Is → Codesmith |
| 1b-2: Research needed? | Specialized improvements (microservices, ML)? | → RESEARCH | → 1b-2a (Standard) |
| 1b-2a-1: HITL needed? | Major breaking changes to architecture? | → HITL | → Codesmith |
| 1b-2b-1: HITL needed? | Ambiguous research findings? | → HITL | → Codesmith |

---

## 🔄 STATE TRANSITIONS

### Greenfield Path

```
START
  ↓
[1: Existing?] NO
  ↓
[1a-1: Research?] NO
  ↓
Design Standard Architecture
  ↓
→ CODESMITH
```

### Greenfield with Research

```
START
  ↓
[1: Existing?] NO
  ↓
[1a-1: Research?] YES
  ↓
→ RESEARCH Agent
  ↓
Architect again (with research_context)
  ↓
Design with Research Context
  ↓
→ CODESMITH
```

### Existing As-Is

```
START
  ↓
[1: Existing?] YES
  ↓
[1b-1: Improvements?] NO
  ↓
Parse Existing Architecture
  ↓
→ CODESMITH (extend existing)
```

### Existing Refactor (Simple)

```
START
  ↓
[1: Existing?] YES
  ↓
[1b-1: Improvements?] YES
  ↓
[1b-2: Research?] NO
  ↓
[1b-2a-1: HITL?] NO
  ↓
Design Improvements
  ↓
→ CODESMITH
```

### Existing Refactor (Complex with HITL)

```
START
  ↓
[1: Existing?] YES
  ↓
[1b-1: Improvements?] YES
  ↓
[1b-2: Research?] NO
  ↓
[1b-2a-1: HITL?] YES
  ↓
→ HITL Node (User Review)
  ↓
  ├─ Approved → CODESMITH
  └─ Declined → Loop back to Architect with feedback
```

### Existing Refactor (with Research)

```
START
  ↓
[1: Existing?] YES
  ↓
[1b-1: Improvements?] YES
  ↓
[1b-2: Research?] YES
  ↓
→ RESEARCH Agent
  ↓
Architect again (with research_context + existing arch)
  ↓
[1b-2b-1: HITL?] NO/YES
  ↓
  ├─ NO → CODESMITH
  └─ YES → HITL (User Review)
           ├─ Approved → CODESMITH
           └─ Declined → Loop back with feedback
```

---

## 🎯 ARCHITECTURE OBJECT STRUCTURE

### Output Format from Architect

```python
architecture = {
    "name": "Todo REST API",
    "version": "1.0",
    "created_at": "2025-11-03T...",
    "framework": "FastAPI",
    "database": "SQLite",
    
    "layers": {
        "api": {
            "description": "REST endpoints",
            "files": ["main.py", "routes/"],
            "responsibilities": ["Request handling", "Response formatting"]
        },
        "models": {
            "description": "Data models",
            "files": ["models.py"],
            "responsibilities": ["SQLAlchemy ORM models"]
        },
        "database": {
            "description": "Database access",
            "files": ["database.py"],
            "responsibilities": ["SQLite connection", "Session management"]
        }
    },
    
    "files": [
        {
            "path": "main.py",
            "type": "module",
            "purpose": "FastAPI app initialization",
            "imports": ["fastapi", "sqlalchemy"],
            "exports": ["app"]
        },
        {
            "path": "models.py",
            "type": "module",
            "purpose": "SQLAlchemy models",
            "imports": ["sqlalchemy"],
            "exports": ["Base", "Todo"]
        },
        ...
    ],
    
    "data_flow": {
        "description": "How data flows through the system",
        "request": "Client → FastAPI route → Database query → Response",
        "crud": {
            "create": "POST /todos + Todo model → DB insert",
            "read": "GET /todos/{id} → DB query → Todo model",
            "update": "PUT /todos/{id} → DB update",
            "delete": "DELETE /todos/{id} → DB delete"
        }
    },
    
    "dependencies": [
        "fastapi",
        "sqlalchemy",
        "pydantic"
    ],
    
    "mermaid_diagram": "graph TD\n  Client[Client]\n  ...",
    
    "notes": "..."
}
```

---

## 📁 FILES CREATED BY ARCHITECT

When Architect completes, it creates:

1. **architecture.json** - Full architecture specification
2. **architecture.md** - Human-readable documentation
3. **structure.mermaid** - Visual architecture diagram
4. **.architecture/** - Directory with sub-documents (optional)
   - layers.md
   - data_flow.md
   - technology_stack.md

---

## 💭 ARCHITECT DECISION LOGIC (PSEUDO CODE)

```python
async def architect_decide(state):
    """
    Architect decision logic in pseudo-code
    """
    
    # Decision 1: Existing architecture?
    if has_existing_architecture(state.workspace_path):
        # Existing Mode
        if should_improve_architecture(state.instructions):
            # Improvements requested
            if needs_research_for_improvements(state.instructions):
                # Request research
                return route_to_research(
                    request="Research best practices for..."
                )
            else:
                # Standard improvements
                if is_complex_refactor(state.instructions):
                    # Need human approval
                    return route_to_hitl(
                        current_arch=parsed_arch,
                        proposed_arch=improved_arch,
                        diagram=mermaid_diagram
                    )
                else:
                    # Simple improvements, go to codesmith
                    return route_to_codesmith(
                        architecture=improved_arch
                    )
        else:
            # Use existing as-is
            return route_to_codesmith(
                architecture=parsed_arch
            )
    else:
        # Greenfield Mode
        if needs_research(state.instructions):
            # Specialized topic, request research
            return route_to_research(
                request="Research best practices for..."
            )
        else:
            # Standard stack, design directly
            return route_to_codesmith(
                architecture=new_arch
            )
```

---

## 🚀 IMPLEMENTATION NOTES

### In architect_agent_server.py

1. Implement decision node functions:
   - `has_existing_architecture(workspace_path)`
   - `should_improve_architecture(instructions)`
   - `needs_research_for_improvements(instructions)`
   - `is_complex_refactor(instructions)`

2. Implement flow functions:
   - `design_standard_architecture(instructions)`
   - `design_with_research_context(instructions, research_context)`
   - `parse_existing_architecture(workspace_path)`
   - `design_improvements(existing_arch, instructions)`

3. Return SupervisorDecision objects with:
   - Correct `next_agent` (codesmith, research, hitl, or END)
   - Clear `instructions` for next agent
   - Updated `state_update` dict

---

**Last Updated:** 2025-11-03  
**Status:** READY FOR IMPLEMENTATION  
**Test Coverage:** See APP_DEVELOPMENT_WORKFLOW_RULES.md examples