# Complete Agent Architecture v7.0 - Alle Agenten erklärt

**Date:** 2025-10-29
**Version:** v7.0.0-alpha (Supervisor Pattern)

---

## 📋 **Übersicht: Alle 6 Agenten**

| Agent | Rolle | AI Provider | Communication | User-Facing? |
|-------|-------|-------------|---------------|--------------|
| **Research** | Support | Perplexity API | REST HTTP | ❌ NO |
| **Architect** | Designer | OpenAI GPT-4o | LangChain → REST | ❌ NO |
| **Codesmith** | Generator | Claude CLI | subprocess | ❌ NO |
| **ReviewFix** | Validator | Claude CLI | subprocess | ❌ NO |
| **Responder** | Presenter | OpenAI GPT-4o | LangChain → REST | ✅ YES |
| **HITL** | Clarifier | (keine AI) | - | ✅ YES |

**Wichtig:** Nur **Responder** und **HITL** kommunizieren mit Users!

---

## 🔍 **Agent 1: Research Agent**

### **Rolle:** Support Agent für Information Gathering

**File:** `backend/agents/research_agent.py`

### **Hauptaufgaben:**
1. 📁 **Workspace-Analyse** - Projektstruktur, Dateien, Frameworks
2. 🌐 **Web-Suche** - Best Practices via Perplexity API
3. 🔧 **Error-Analyse** - Fehlermuster erkennen und Lösungen vorschlagen
4. 🔒 **Security-Analyse** - Sicherheitslücken finden
5. 💾 **Memory/Learning** - Projekt-Wissen aus vorherigen Tasks

### **AI Provider:**

```python
from backend.utils.perplexity_service import PerplexityService

class ResearchAgent:
    def __init__(self):
        self.perplexity_service = PerplexityService(model="sonar")
```

**Communication Method:**
- ✅ **Perplexity REST API** - `https://api.perplexity.ai/chat/completions`
- ❌ **NICHT MCP** - Direkte HTTP REST API Calls

### **Funktionsweise:**

```python
async def execute(self, state: dict) -> dict:
    instructions = state.get("instructions", "")

    research_context = {}

    # 1. Workspace analysieren
    if "workspace" in instructions.lower():
        research_context["workspace_analysis"] = await self._analyze_workspace(workspace_path)

    # 2. Web suchen
    if "best practice" in instructions.lower():
        research_context["web_results"] = await self._search_web(instructions)

    # 3. Errors analysieren
    if "error" in instructions.lower():
        research_context["error_analysis"] = await self._analyze_errors(error_info)

    return {
        "research_context": research_context,
        "research_complete": True
    }
```

### **Special Features:**
- 🌍 **Global Memory** - Cross-project learning
- 💾 **Memory System** - Workspace-specific knowledge
- 🧠 **Learning System** - Optimierungsvorschläge aus früheren Tasks

### **Output Example:**
```json
{
  "research_context": {
    "workspace_analysis": {
      "project_type": "Python",
      "file_count": 42,
      "languages": ["Python"],
      "frameworks": ["FastAPI"],
      "has_tests": true
    },
    "web_results": [{
      "title": "FastAPI Best Practices",
      "summary": "...",
      "citations": ["https://..."]
    }]
  },
  "research_complete": true
}
```

---

## 🏗️ **Agent 2: Architect Agent**

### **Rolle:** System Design Specialist

**File:** `backend/agents/architect_agent.py`

### **Hauptaufgaben:**
1. 📐 **System-Architektur** - Komponenten-Design
2. 📂 **File-Struktur** - Datei-Organisation planen
3. 🛠️ **Technologie-Auswahl** - Stack-Entscheidungen
4. 📊 **Data-Flow** - Datenfluss zwischen Komponenten
5. 📚 **Pattern-Selection** - Design-Patterns wählen

### **AI Provider:**

```python
from backend.utils.ai_factory import AIFactory

class ArchitectAgent:
    def __init__(self):
        self.ai_provider = AIFactory.get_provider_for_agent("architect")
        # Provider: OpenAIService (GPT-4o via LangChain)
```

**Communication Method:**
- ✅ **OpenAI REST API** - Via LangChain's `ChatOpenAI`
- ❌ **NICHT MCP** - Direkte API Integration

### **Funktionsweise:**

```python
async def execute(self, state: dict) -> dict:
    instructions = state.get("instructions", "")
    research_context = state.get("research_context", {})

    # Check ob mehr Research nötig
    if self._needs_more_research(instructions, research_context):
        return {
            "needs_research": True,
            "research_request": "Gather more context for architecture design"
        }

    # Architecture mit AI generieren
    architecture = await self._design_architecture(
        instructions,
        research_context,
        workspace_path
    )

    return {
        "architecture": architecture,
        "architecture_complete": True
    }
```

### **AI Generation:**

```python
async def _generate_with_ai(self, instructions, research_context) -> dict:
    request = AIRequest(
        prompt=self._build_architecture_prompt(...),
        system_prompt=self._get_architecture_system_prompt(),
        temperature=0.4,  # Balanced
        max_tokens=4000
    )

    response = await self.ai_provider.complete(request)

    # Parse JSON response
    architecture = json.loads(response.content)
    return architecture
```

### **Output Example:**
```json
{
  "architecture": {
    "description": "FastAPI-based web service with REST endpoints",
    "components": [
      {
        "name": "APIRouter",
        "description": "Handles HTTP requests and responses"
      },
      {
        "name": "Database",
        "description": "PostgreSQL database for data persistence"
      }
    ],
    "file_structure": [
      "src/",
      "src/api/",
      "src/models/",
      "src/services/",
      "tests/"
    ],
    "technologies": ["FastAPI", "PostgreSQL", "Pydantic"],
    "patterns": ["MVC", "Dependency Injection"],
    "data_flow": [
      {
        "from": "APIRouter",
        "to": "Database",
        "description": "Store user data"
      }
    ]
  },
  "architecture_complete": true
}
```

---

## ⚒️ **Agent 3: Codesmith Agent**

### **Rolle:** Code Generation Specialist

**File:** `backend/agents/codesmith_agent.py`

### **Hauptaufgaben:**
1. 💻 **Code generieren** - Production-ready Code
2. 📝 **Tests schreiben** - Unit & Integration Tests
3. 📚 **Dokumentation** - Docstrings, Comments
4. 🛠️ **Implementation** - Business Logic umsetzen
5. 🔧 **Bug-Fixing** - Code-Fehler beheben

### **AI Provider:**

```python
from backend.utils.ai_factory import AIFactory

class CodesmithAgent:
    def __init__(self):
        self.ai_provider = AIFactory.get_provider_for_agent("codesmith")
        # Provider: ClaudeCLIService (subprocess)
```

**Communication Method:**
- ✅ **Claude CLI subprocess** - `asyncio.create_subprocess_exec`
- ❌ **NICHT MCP** - Nur stdin/stdout/stderr Pipes

### **Funktionsweise:**

```python
async def execute(self, state: dict) -> dict:
    instructions = state.get("instructions", "")
    architecture = state.get("architecture", {})

    # Generate code mit AI
    generated_files = await self._generate_code_with_ai(
        instructions,
        architecture,
        research_context,
        workspace_path
    )

    return {
        "generated_files": generated_files,
        "code_complete": True
    }
```

### **Claude CLI Call:**

```python
async def _generate_code_with_ai(self, instructions, architecture, workspace_path) -> list:
    request = AIRequest(
        prompt=self._build_code_generation_prompt(instructions, architecture),
        system_prompt=self._get_system_prompt(),
        workspace_path=workspace_path,
        tools=["Read", "Edit", "Bash"],  # Claude CLI tools
        temperature=0.3,  # Lower for code
        max_tokens=8000
    )

    # Call Claude CLI (subprocess!)
    response = await self.ai_provider.complete(request)

    # In claude_cli_service.py:
    # process = await asyncio.create_subprocess_exec(
    #     "claude", "--print", "--model", model,
    #     "--allowed-tools", "Read Edit Bash",
    #     "--system-prompt", system_prompt,
    #     prompt,
    #     stdin=asyncio.subprocess.DEVNULL,  # ← FIX für hanging!
    #     stdout=asyncio.subprocess.PIPE,
    #     stderr=asyncio.subprocess.PIPE,
    #     cwd=workspace_path
    # )

    return [{"path": "...", "content": response.content}]
```

### **Output Example:**
```json
{
  "generated_files": [
    {
      "path": "src/api/router.py",
      "content": "from fastapi import APIRouter\n...",
      "language": "python",
      "lines": 127,
      "description": "API router with endpoints",
      "provider": "claude-cli",
      "model": "claude-sonnet-4-20250514"
    }
  ],
  "code_complete": true
}
```

---

## 🔧 **Agent 4: ReviewFix Agent**

### **Rolle:** Code Validation & Debugging

**File:** `backend/agents/reviewfix_agent.py`

### **Hauptaufgaben:**
1. ✅ **Code validieren** - Syntax, Logic, Standards
2. 🔍 **Debugging** - Fehler finden und fixen
3. 🏗️ **Build Validation** - TypeScript/Python/JS Check
4. 🧪 **Playground Tests** - Funktionale Tests
5. 🎨 **Architecture Compare** - Mit Design vergleichen

### **AI Provider:**

```python
from backend.utils.ai_factory import AIFactory

class ReviewFixAgent:
    def __init__(self):
        self.ai_provider = AIFactory.get_provider_for_agent("reviewfix")
        # Provider: ClaudeCLIService (subprocess)
```

**Communication Method:**
- ✅ **Claude CLI subprocess** - Gleich wie Codesmith
- ❌ **NICHT MCP** - Subprocess mit stdin/stdout/stderr

### **Funktionsweise:**

```python
async def execute(self, state: dict) -> dict:
    instructions = state.get("instructions", "")
    generated_files = state.get("generated_files", [])
    architecture = state.get("architecture", {})

    # 1. Build Validation (wenn verfügbar)
    build_results = await self._run_build_validation(workspace_path)

    # 2. Architecture Comparison mit AI
    architecture_check = await self._compare_with_architecture(
        generated_files, architecture, workspace_path
    )

    # 3. Debugging mit AI (wenn Issues)
    if issues:
        debug_results = await self._debug_with_ai(
            generated_files, issues, workspace_path
        )

    # 4. Playground Tests
    test_results = await self._run_playground_tests(
        generated_files, workspace_path
    )

    return {
        "validation_results": {...},
        "validation_passed": all_checks_passed,
        "issues": found_issues
    }
```

### **Build Validation:**
```python
# Unterstützt:
# - TypeScript (tsc --noEmit)
# - Python (mypy)
# - JavaScript (eslint)

build_results = {
    "language": "typescript",
    "quality_score": 0.95,
    "passed": True,
    "error_count": 2,
    "warning_count": 5
}
```

### **Output Example:**
```json
{
  "validation_results": {
    "build_validation": {
      "passed": true,
      "quality_score": 0.95
    },
    "architecture_match": true,
    "test_results": {
      "passed": 8,
      "failed": 0
    }
  },
  "validation_passed": true,
  "issues": []
}
```

---

## 💬 **Agent 5: Responder Agent**

### **Rolle:** User-Facing Response Formatter ⭐ ONLY USER-FACING AGENT!

**File:** `backend/agents/responder_agent.py`

### **Hauptaufgaben:**
1. 📝 **Response formatieren** - Readable, structured
2. 🎨 **Markdown** - Beautiful output
3. 📊 **Summarize** - Komplexe Details vereinfachen
4. ❌ **Error Messages** - User-friendly errors
5. ✅ **Success Messages** - Clear confirmation

### **AI Provider:**

```python
class ResponderAgent:
    def __init__(self):
        # KEINE AI! (könnte Optional OpenAI nutzen für besseres Formatting)
        pass
```

**Communication Method:**
- ❌ **Keine AI** - Pure Python Logic
- ✅ **Optional:** Könnte OpenAI nutzen für besseres Formatting

### **Funktionsweise:**

```python
async def execute(self, state: dict) -> dict:
    instructions = state.get("instructions", "")
    all_results = state.get("all_results", {})

    # Extract results von allen Agents
    research_context = all_results.get("research_context", {})
    architecture = all_results.get("architecture", {})
    generated_files = all_results.get("generated_files", [])
    validation_results = all_results.get("validation_results", {})
    issues = all_results.get("issues", [])

    # Format response
    response = self._format_response(
        instructions,
        research_context,
        architecture,
        generated_files,
        validation_results,
        issues
    )

    return {
        "user_response": response,
        "response_ready": True
    }
```

### **Response Types:**

1. **CREATE Response:**
```markdown
# ✅ Created: FastAPI Web Service

## Generated Files (3)
- `src/api/router.py` (127 lines)
- `src/models/user.py` (45 lines)
- `tests/test_api.py` (89 lines)

## Architecture
- **Pattern:** MVC
- **Technologies:** FastAPI, PostgreSQL, Pydantic

## Validation
✅ All tests passed (8/8)
✅ Build validation: 95% quality score

## Next Steps
1. Run `pip install -r requirements.txt`
2. Start server: `uvicorn src.api:app`
3. Visit: http://localhost:8000/docs
```

2. **EXPLAIN Response:**
```markdown
# 🔍 Analysis: Project Structure

## Overview
This is a Python FastAPI project with...

## Key Components
...
```

3. **ERROR Response:**
```markdown
# ❌ Issues Found (2)

## Critical
- Import error in `router.py`: Module 'xyz' not found

## Warnings
- Missing type hints in function `foo()`

## Suggestions
1. Install missing dependency: `pip install xyz`
2. Add type hints for better code quality
```

---

## 👤 **Agent 6: HITL Agent**

### **Rolle:** Human-in-the-Loop Clarification

**File:** `backend/agents/hitl_agent.py`

### **Hauptaufgaben:**
1. ❓ **Clarification** - Bei niedrigem Confidence (<0.5)
2. 🎯 **Options präsentieren** - Mehrere Interpretationen
3. 📋 **Requirements sammeln** - Zusätzliche Infos einholen
4. ⚠️ **Ambiguität auflösen** - User entscheiden lassen
5. ✅ **Intent validieren** - User-Absicht bestätigen

### **AI Provider:**

```python
class HITLAgent:
    def __init__(self):
        # KEINE AI! Pure logic for user interaction
        pass
```

**Communication Method:**
- ❌ **Keine AI** - Reine WebSocket-Kommunikation
- ✅ **WebSocket** - Bidirektional für User Input

### **Funktionsweise:**

```python
async def execute(self, state: dict) -> dict:
    instructions = state.get("instructions", "")
    context = state.get("context", {})
    confidence = context.get("confidence", 0.0)
    options = state.get("options", [])
    errors = context.get("errors", [])

    # Build clarification request
    clarification_request = self._build_clarification_request(
        instructions, context, confidence, options, errors
    )

    # Format for user
    formatted_request = self._format_for_user(clarification_request)

    return {
        "clarification_request": formatted_request,
        "awaiting_user_input": True,
        "confidence_level": confidence
    }
```

### **Clarification Types:**

1. **Low Confidence:**
```json
{
  "type": "low_confidence",
  "message": "I'm not sure what you want. Did you mean:",
  "options": [
    "Create a new FastAPI application",
    "Modify existing FastAPI routes",
    "Explain FastAPI architecture"
  ],
  "priority": "high",
  "confidence": 0.45
}
```

2. **Ambiguous Request:**
```json
{
  "type": "ambiguous",
  "message": "Your request could mean multiple things. Please clarify:",
  "options": [...],
  "priority": "medium"
}
```

3. **Critical Decision:**
```json
{
  "type": "critical_decision",
  "message": "This will delete existing code. Are you sure?",
  "options": ["Yes, proceed", "No, cancel"],
  "priority": "critical"
}
```

---

## 📊 **Agent Communication Flow**

```
USER REQUEST
    ↓
┌─────────────────┐
│   SUPERVISOR    │  (GPT-4o) Makes routing decisions
│   (GPT-4o)      │
└─────────────────┘
    ↓
    ├─→ [Research Agent] (Perplexity REST API)
    │     ↓
    ├─→ [Architect Agent] (OpenAI GPT-4o via LangChain)
    │     ↓
    ├─→ [Codesmith Agent] (Claude CLI subprocess)
    │     ↓
    ├─→ [ReviewFix Agent] (Claude CLI subprocess)
    │     ↓
    ├─→ [Responder Agent] (No AI - Pure formatting)
    │     ↓
    │   USER RESPONSE ✅
    │
    └─→ [HITL Agent] (No AI - User interaction)
          ↓
        USER CLARIFICATION ❓
          ↓
        SUPERVISOR (retry with clarification)
```

---

## 🚫 **WICHTIG: Was IST NICHT MCP!**

❌ **NONE** of the v7.0 agents use MCP protocol!

| Agent | Kommunikation | MCP? |
|-------|---------------|------|
| Research | Perplexity REST API | ❌ NO |
| Architect | OpenAI via LangChain | ❌ NO |
| Codesmith | Claude CLI subprocess | ❌ NO |
| ReviewFix | Claude CLI subprocess | ❌ NO |
| Responder | No AI | ❌ NO |
| HITL | No AI | ❌ NO |

**MCP ist nur in v6.x Legacy-Code vorhanden!**

---

## ✅ **Zusammenfassung**

### **Agent-Typen:**

1. **Support Agents** (keine User-Kommunikation):
   - Research
   - Architect
   - Codesmith
   - ReviewFix

2. **User-Facing Agents** (ONLY these talk to users!):
   - **Responder** (formatiert alle Responses)
   - **HITL** (bittet um Clarification)

### **AI Provider Distribution:**

- **Perplexity:** Research (Web-Suche)
- **OpenAI GPT-4o:** Architect, Responder (via LangChain)
- **Claude CLI:** Codesmith, ReviewFix (subprocess)
- **No AI:** HITL (reine Logic)

### **Kommunikations-Methoden:**

- **REST API:** Research (Perplexity), Architect (OpenAI)
- **subprocess:** Codesmith, ReviewFix (Claude CLI)
- **Pure Logic:** Responder, HITL (kein AI Call)

**Kein einziger Agent nutzt MCP-Protocol in v7.0!**
