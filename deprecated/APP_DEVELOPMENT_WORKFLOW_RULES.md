# 🏗️ APP DEVELOPMENT WORKFLOW RULES v7.0 (PURE MCP)

## 📋 Workflow Overview

Dies ist das definitive Regelbuch für den **Create/Develop App** Workflow in KI AutoAgent v7.0 (Pure MCP Architecture).

**Version:** 7.0  
**Architecture:** Pure MCP (alle Agenten sind MCP-Server)  
**Orchestrator:** SupervisorMCP (Single Decision-Maker)  
**Created:** 2025-11-03

---

## 🎯 PRIMARY WORKFLOW: CREATE/DEVELOP APP

### Entry Point
```
User Input: "Create a ..." oder "Develop ..."
│
→ SUPERVISOR macht ERSTE Decision
```

---

## 1️⃣ ARCHITEKT AGENT - DECISION FLOW

Der **Architekt Agent** ist der Gatekeeper für app development.

### Phase 1.1: Architektur-Daten Check

```
Architekt erhält Instructions vom Supervisor
│
├─ Frage: "Gibt es bereits Architektur-Daten?" (TreeSitter, Mermaid, etc.)
│
├─ NEIN (Greenfield Project)
│  └─ Gehe zu 1.2a: Architektur Planung
│
└─ JA (Existing Project)
   └─ Gehe zu 1.2b: Architektur-Entscheidung
```

### Phase 1.2a: GREENFIELD - Neue Architektur Planen

```
Architekt: "Keine Architektur vorhanden. Planen wir neu."
│
├─ Frage: "Brauchen wir Web Research?"
│
├─ NEIN (Standard Stack)
│  ├─ Erstelle Architektur mit Standard-Stack
│  ├─ Erstelle Mermaid Diagramm
│  ├─ Output: architecture.json, architecture.md, structure.mermaid
│  └─ Return: architecture, Gehe zu Codesmith
│
└─ JA (Specialized/Research needed)
   ├─ Return: needs_research=true, research_request="..."
   └─ Supervisor leitet zu RESEARCH Agent
      └─ Nach Research: Zurück zu Architekt mit Research Context
         ├─ Erstelle Architektur MIT Research Context
         ├─ Erstelle Mermaid Diagramm
         ├─ Output: architecture.json, architecture.md, structure.mermaid
         └─ Return: architecture, Gehe zu Codesmith
```

### Phase 1.2b: EXISTING - Architektur Analyse

```
Architekt: "Architektur vorhanden. Werden Verbesserungen gewünscht?"
│
├─ NEIN (Use Existing)
│  ├─ Parse bestehende Architektur
│  ├─ Return: architecture (parsed), Gehe zu Codesmith
│  └─ Codesmith erhält: aktualisierte Architektur
│
└─ JA (Refactor/Improve)
   ├─ Frage: "Brauchen wir Web Research?"
   │
   ├─ NEIN
   │  ├─ Analyse bestehende Architektur
   │  ├─ Plane Verbesserungen
   │  ├─ Erstelle neue Architektur Entwurf
   │  ├─ Frage: "HITL notwendig?" (Human Review)
   │  │
   │  ├─ NEIN
   │  │  ├─ Output: architecture (improved), Gehe zu Codesmith
   │  │  └─ Codesmith erhält: neue Architektur
   │  │
   │  └─ JA (HITL)
   │     ├─ Return: HITL={
   │     │    research_findings: "...",
   │     │    architecture_plan: "...",
   │     │    mermaid_diagram: "...",
   │     │    recommendations: [...]
   │     │  }
   │     ├─ Supervisor leitet zu HITL Node
   │     ├─ User Review & Input
   │     ├─ Falls User sagt NEIN:
   │     │  └─ Zurück zu Architekt mit User Input → loop zu 1.2b
   │     └─ Falls User sagt JA:
   │        └─ Architecture approved, Gehe zu Codesmith
   │
   └─ JA (Research needed)
      ├─ Return: needs_research=true, research_request="..."
      ├─ Supervisor leitet zu RESEARCH Agent
      └─ Nach Research: Zurück zu Phase 1.2b mit Research Context
         ├─ Plane Verbesserungen MIT Research Context
         ├─ Erstelle neue Architektur Entwurf
         ├─ Frage: "HITL notwendig?"
         ├─ ... (siehe oben HITL Flow)
```

---

## 2️⃣ CODESMITH AGENT - CODE GENERATION

```
Codesmith erhält vom Supervisor:
├─ instructions: "Baue die App..."
├─ architecture: { ... } ← VON ARCHITEKT!
└─ workspace_path: "/path/to/workspace"

│
├─ Analysiere Architektur
├─ Generiere Dateien gemäß Architektur
├─ Implementiere CRUD, APIs, Frontend, etc.
├─ Files in workspace schreiben
│
└─ Return:
   ├─ generated_files: [...list of files...]
   ├─ code_complete: true
   └─ code_summary: "..."
   
   Supervisor leitet zu ReviewFix
```

---

## 3️⃣ REVIEWFIX AGENT - VALIDATION

```
ReviewFix erhält vom Supervisor:
├─ generated_files: [...] ← VON CODESMITH!
├─ architecture: { ... } ← VON ARCHITEKT!
└─ workspace_path: "/path/to/workspace"

│
├─ Frage 1: "Passt Code zur Architektur?"
│  └─ Vergleiche mit architecture.md
│
├─ Frage 2: "Funktioniert die App wie gewünscht?"
│  └─ Test CRUD, API Responses, Error Handling
│
├─ Issues found?
│  ├─ NEIN → validation_passed=true
│  └─ JA → issues=[...], validation_passed=false
│
└─ Return:
   ├─ validation_results: { ... }
   ├─ validation_passed: true/false
   ├─ issues: [...] or []
   └─ Supervisor leitet zu Responder (wenn passed=true)
      oder zu Codesmith (wenn passed=false → fix issues)
```

---

## 4️⃣ RESPONDER AGENT - USER COMMUNICATION

```
Responder erhält vom Supervisor:
├─ instructions: "Kommuniziere dem User..."
├─ architecture: { ... } ← VON ARCHITEKT!
├─ generated_files: [...] ← VON CODESMITH!
├─ validation_results: { ... } ← VON REVIEWFIX!
└─ workspace_path: "/path/to/workspace"

│
├─ Formatiere Ausgabe schön
├─ Zeige Zusammenfassung was gemacht wurde
├─ Zeige Architektur-Diagramm
├─ Zeige Dateistruktur
├─ Zeige Test-Instructions
│
└─ Return:
   ├─ user_response: "✅ App erstellt:\n\n..."
   ├─ response_ready: true
   └─ Workflow beendet (END)
```

---

## 🔄 SUPERVISOR ROUTING LOGIC

### Decision Matrix

| Last Agent | Condition | Next Agent | Rule |
|------------|-----------|-----------|------|
| START | Neue App | ARCHITECT | Immer Architect zuerst |
| ARCHITECT | needs_research=true | RESEARCH | Architekt fordert Research an |
| RESEARCH | research_done | ARCHITECT | Zurück zu Architekt mit Context |
| ARCHITECT | architecture_complete=true | CODESMITH | Architektur fertig |
| ARCHITECT | hitl_needed=true | HITL | Human Review nötig |
| HITL | user_approved=true | CODESMITH | User genehmigt Architektur |
| HITL | user_declined=true | ARCHITECT | Zurück mit User Input → Loop |
| CODESMITH | code_complete=true | REVIEWFIX | Code fertig |
| REVIEWFIX | validation_passed=true | RESPONDER | Code korrekt |
| REVIEWFIX | validation_passed=false | CODESMITH | Issues zu fixen |
| RESPONDER | response_ready=true | END | Workflow abgeschlossen |

---

## 🚀 SUPERVISOR DECISION INSTRUCTIONS

### Instruction Templates

#### 1. Initial ARCHITECT Call
```
Instructions for ARCHITECT:
- Task: Design architecture for: {user_query}
- Workspace: {workspace_path}
- Check: Do architecture files exist? (tree-sitter analysis)
- If NO: Create new architecture
- If YES: Use existing or improve?
- Provide: architecture.json, architecture.md, mermaid diagram
- Return: architecture object with full details
```

#### 2. CODESMITH Call (with Architecture)
```
Instructions for CODESMITH:
- Task: Implement app based on architecture
- Workspace: {workspace_path}
- Architecture: {architecture JSON}
- Requirements: {original user requirements}
- Follow: {architecture_path}/architecture.md exactly
- Create: All files listed in architecture.files
- Return: generated_files list with paths and descriptions
```

#### 3. REVIEWFIX Call (with Architecture)
```
Instructions for REVIEWFIX:
- Task: Validate generated code
- Workspace: {workspace_path}
- Architecture Reference: {architecture JSON}
- Generated Files: {generated_files}
- Checks:
  1. Code matches architecture design?
  2. All CRUD operations working?
  3. Error handling present?
  4. No syntax errors?
- Return: validation_results with issues list
```

#### 4. RESPONDER Call (with full Context)
```
Instructions for RESPONDER:
- Task: Summarize work to user
- Architecture: {architecture JSON}
- Generated: {generated_files}
- Validation: {validation_results}
- Format:
  1. What was done? (heading + summary)
  2. Architecture diagram (from mermaid)
  3. File structure (tree view)
  4. How to test? (quick guide)
  5. Next steps? (improvements, if any)
- Make it beautiful and clear for non-technical user
```

---

## ⚠️ ERROR HANDLING & LOOPS

### Loop Prevention Rules

```
Condition: Loop Detected (same agent called 3x)
├─ If ARCHITECT called 3x → Force HITL for manual review
├─ If CODESMITH called 3x → Return error to user via RESPONDER
├─ If REVIEWFIX called 3x → Return error to user via RESPONDER

Condition: Max Iterations (15)
├─ Stop workflow
├─ Route to RESPONDER with partial results
└─ Inform user of timeout
```

### Error Recovery

```
If ANY agent fails:
├─ Log error with context
├─ Increment error_count
├─ If error_count > 3:
│  └─ Route to RESPONDER immediately with error message
└─ Else:
   └─ Retry agent with refined instructions
```

---

## 🎓 RESEARCH AGENT (Support Role)

### When Called

```
- Architekt needs specialized knowledge (not standard stack)
- Codesmith needs library recommendations
- ReviewFix needs testing patterns
```

### What Returns

```
research_context: {
  "topic": "...",
  "findings": [
    {
      "source": "web search / docs",
      "summary": "...",
      "relevance": 0.9
    }
  ],
  "recommendations": [...],
  "confidence": 0.85
}
```

---

## 📊 STATE TRACKING

### State Fields by Agent

| Agent | Reads | Writes |
|-------|-------|--------|
| SUPERVISOR | last_agent, iteration | last_agent, iteration, instructions |
| ARCHITECT | instructions, workspace_path | architecture, architecture_complete, needs_research |
| RESEARCH | research_request, workspace_path | research_context |
| CODESMITH | instructions, architecture, workspace_path | generated_files, code_complete |
| REVIEWFIX | generated_files, architecture, workspace_path | validation_results, validation_passed, issues |
| RESPONDER | all above | user_response, response_ready |
| HITL | architecture, research_context | hitl_response, awaiting_human |

---

## ✅ WORKFLOW COMPLETION CRITERIA

Workflow is **COMPLETE** when:

```
1. response_ready = true ✓
2. user_response contains summary ✓
3. All generated files in workspace ✓
4. architecture JSON available ✓
5. validation_passed = true (if code generated) ✓
6. Responder node executed ✓
```

---

## 🔐 IMPORTANT CONSTRAINTS

### MCP Architecture Constraints

```
1. ⚠️ ALL agent calls via mcp.call() - NO direct instantiation
2. ⚠️ All communication via JSON-RPC 2.0
3. ⚠️ MCPManager handles process management
4. ⚠️ Progress via $/progress notifications
5. ⚠️ Rate limiting applied to all LLM calls
```

### Workspace Isolation

```
1. All workspaces must be EXTERNAL to server root
2. Valid paths: ~/TestApps/, /tmp/, ~/projects/
3. INVALID: /Users/dominikfoert/git/KI_AutoAgent/... (server root)
4. Validation happens at client init
```

### Agent Independence

```
1. Agents are stateless (except via state dict)
2. Each MCP server is independent process
3. No shared memory between agents
4. All context via SupervisorState
```

---

## 📚 EXAMPLES

### Example 1: Simple CRUD App

```
User: "Create a REST API with FastAPI for todo list"

1. Supervisor → ARCHITECT
   Task: Design todo API architecture
   
2. Architect designs:
   - Framework: FastAPI
   - DB: SQLite
   - Structure: models/routes/database.py
   
3. Supervisor → CODESMITH
   Architecture: { ... }
   Task: Implement using architecture
   
4. Codesmith generates:
   - main.py (FastAPI app + CRUD endpoints)
   - models.py (SQLAlchemy Todo model)
   - database.py (SQLite setup)
   - requirements.txt
   
5. Supervisor → REVIEWFIX
   Task: Validate implementation
   Checks: All CRUD endpoints? Error handling?
   Result: ✅ All good
   
6. Supervisor → RESPONDER
   Task: Tell user what's done
   Output: "✅ Todo API created at /workspace/..."
   
7. END
```

### Example 2: Existing App Refactor

```
User: "Improve the architecture of my app"

1. Supervisor → ARCHITECT
   Task: Analyze existing architecture
   
2. Architect finds:
   - Existing: src/app.py (monolithic)
   - Suggests: Modular structure (separate routes, models, db)
   - Detects: Needs Research for best patterns
   
3. Supervisor → RESEARCH
   Task: Find best patterns for {framework}
   Returns: Findings about microservices, modular design
   
4. Supervisor → ARCHITECT (with research context)
   Task: Create improved architecture
   Result: New modular design with mermaid diagram
   
5. Supervisor → HITL
   Shows: Architecture diagram + recommendations
   User input: "Approved but add authentication"
   
6. Supervisor → ARCHITECT (with user feedback)
   Task: Include authentication in architecture
   
7. Supervisor → CODESMITH
   Architecture: Refactored + auth
   Task: Refactor app
   
8. Supervisor → REVIEWFIX
   Validation: Does new code work? Architecture respected?
   
9. Supervisor → RESPONDER
   Output: "✅ App refactored with..."
   
10. END
```

---

## 🔄 IMPLEMENTATION CHECKLIST

- [ ] Supervisor Decision Logic updated with routing matrix
- [ ] Architect Agent has full decision tree
- [ ] Architecture object schema defined
- [ ] Research Agent integration tested
- [ ] HITL Node implemented
- [ ] State tracking fields verified
- [ ] Error handling with loop prevention
- [ ] E2E tests created for each workflow
- [ ] Documentation updated
- [ ] Responder formatting improved

---

**Last Updated:** 2025-11-03  
**Next Review:** When new agent types added  
**Maintained By:** KI AutoAgent Team