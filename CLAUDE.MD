

---

## 📚 MANDATORY READING - Claude Official Documentation

**CRITICAL:** Read these before making any Claude-related changes!

- **Claude Best Practices & Workflows:** `/CLAUDE_BEST_PRACTICES.md` (Complete guide)
- **Claude 4 Best Practices:** https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices
- **Usage Limits & Optimization:** https://support.claude.com/en/articles/9797557-usage-limit-best-practices
- **Command Pipelining (Claude Code):** https://www.anthropic.com/engineering/claude-code-best-practices
- **Claude Opus 4.1 Announcement:** https://www.anthropic.com/news/claude-opus-4-1
- **Prompt Caching (90% cost savings!):** https://docs.claude.com/en/docs/build-with-claude/prompt-caching
- **Streaming:** https://docs.claude.com/en/docs/build-with-claude/streaming
- **Context Editing/Memory:** https://docs.claude.com/en/docs/build-with-claude/context-editing

**Key Takeaways:**
1. **Prompt Caching:** Cache system prompts for 90% cost savings
2. **XML Tags:** Use `<task>`, `<context>`, `<requirements>` for structure
3. **Explicit Instructions:** "Go beyond the basics to create a fully-featured implementation"
4. **Parallel Execution:** Run independent tasks with `asyncio.gather()`
5. **Streaming:** Use for long responses, better UX
6. **Context Management:** Clear old tool results after 30k tokens
7. **Model Selection:** Opus 4.1 for complex coding, Sonnet 4.5 for general tasks
8. **NO Shell Substitution:** `subprocess.exec()` doesn't expand `$(...)` - read files in Python!

---

## 🏗️ SYSTEM-ARCHITEKTUR (v5.9.0+)

### **⚡ NEW in v5.9.0: Performance Optimizations**

**Implemented:**
- ✅ **uvloop**: 2-4x faster event loop (installed before asyncio)
- ✅ **orjson**: 2-3x faster JSON serialization (CacheManager)
- ⚠️ **aiosqlite**: Async SQLite prepared (TODO: convert 10 locations)
- 📋 **tenacity**: Circuit Breaker & Retry ready (installed)

**Expected Performance:** 30-40% faster (with full aiosqlite: 60-70%)

**Documentation:**
- `SYSTEM_ARCHITECTURE_v5.9.0.md` - Complete system overview
- `PERFORMANCE_OPTIMIZATION_REPORT_v5.9.0.md` - Detailed optimization analysis

---

## 🏗️ SYSTEM-ARCHITEKTUR (v5.8.1+ → v5.9.0)

### **WICHTIG: Backend ist GLOBAL und MULTI-CLIENT!**

```
$HOME/.ki_autoagent/                # Globale Agent-Service Installation
├── backend/                        # Python Backend (Agents, LangGraph)
│   ├── agents/
│   ├── api/
│   ├── langgraph_system/
│   └── ...
│
├── config/                         # Globale Konfiguration
│   ├── .env                        # API Keys (OpenAI, Anthropic, etc.)
│   ├── instructions/               # ⭐ AGENT BASIS-INSTRUCTIONS
│   │   ├── architect-v2-instructions.md
│   │   ├── codesmith-v2-instructions.md
│   │   └── ...
│   └── instructions_updates/       # Update Staging Area
│       ├── v5.8.0/                 # Neue Version (für manuelles Merge)
│       └── backups/                # Backups vor Updates
│
├── data/                           # Agent-globale Daten
│   ├── embeddings/                 # Vector Stores (Agent Memories)
│   └── knowledge_base/             # Agent Knowledge Base
│
├── venv/                           # Python Virtual Environment
├── logs/                           # Globale Logs
├── version.json                    # Installation Metadata
└── {start.sh,stop.sh,status.sh}    # Convenience Scripts

/Users/.../KI_AutoAgent/            # Development Repo (optional)
├── backend/                        # Backend Source Code
├── vscode-extension/               # VS Code Extension Source
├── install.sh                      # Installation Script
└── update.sh                       # Update Script

/Users/.../MyApp/                   # USER WORKSPACE
├── src/                            # User Code
└── .ki_autoagent_ws/               # ⭐ WORKSPACE-SPEZIFISCHE DATEN
    ├── instructions/               # 📝 Projekt-spezifische Instructions
    │   └── architect-custom.md     # "In diesem Projekt: NestJS, TypeORM..."
    ├── cache/                      # Workspace Cache (DB, File Hashes)
    ├── memory/                     # Agent Memories für dieses Projekt
    └── artifacts/                  # Generierte Outputs
```

### **Wie es funktioniert:**

#### 1. **Installation**
```bash
# Einmalig: Backend als globaler Service installieren
cd /path/to/KI_AutoAgent
./install.sh

# Installiert nach: $HOME/.ki_autoagent/
# Erstellt: start.sh, stop.sh, status.sh
```

#### 2. **Backend Starten** (v5.8.1: KEIN workspace parameter!)
```bash
# Als globaler Service für ALLE Workspaces
$HOME/.ki_autoagent/start.sh

# Backend läuft EINMAL und bedient alle Clients
# VS Code Extension VERBINDET SICH NUR (startet Backend NICHT)
```

#### 2a. **Multi-Client WebSocket Protocol** (v5.8.1)
```
Client (VS Code) → Backend:
  1. WebSocket Connect zu ws://localhost:8001/ws/chat
  2. Server sendet: {"type": "connected", "requires_init": true}
  3. Client sendet: {"type": "init", "workspace_path": "/Users/.../MyProject"}
  4. Server sendet: {"type": "initialized", "workspace_path": "...", "session_id": "..."}
  5. Client kann jetzt Chat-Messages senden

Vorteile:
  - Ein Backend bedient mehrere VS Code Fenster/Workspaces
  - Jeder Client sendet seinen workspace_path
  - Backend isoliert cache/memory per workspace
  - Kein spawning mehr in VS Code Extension!
```

#### 3. **Two-Tier Instruction System**
```python
# Agent lädt Instructions in 2 Ebenen:

# 1. BASE INSTRUCTIONS (Required)
#    $HOME/.ki_autoagent/config/instructions/architect-v2-instructions.md
#    → Agent-Identität, Core Capabilities, Basis-Verhalten

# 2. PROJECT INSTRUCTIONS (Optional)
#    $WORKSPACE/.ki_autoagent_ws/instructions/architect-custom.md
#    → "Verwende NestJS", "Code-Style", Projekt-Regeln

# Merge: Base + Project
```

#### 4. **Instructions Updates**
```bash
# Interaktiv (zeigt Diff, fragt für jede Datei)
./update.sh --instructions interactive

# Automatisch (überschreibt alle)
./update.sh --instructions overwrite

# Preserve (behält existierende, installiert nur neue)
./update.sh --instructions preserve

# Backup (speichert neue in Staging Area)
./update.sh --instructions backup
```

### **Key Principles:**

1. **Agent Service** → Läuft von `$HOME/.ki_autoagent/backend/`
2. **Multi-Client** → Ein Backend bedient ALLE Clients/Workspaces (v5.8.1)
3. **Workspace per Request** → Client sendet workspace_path bei Connect (v5.8.1)
4. **Workspace Separation** → Backend analysiert NUR den workspace des Clients
5. **Base Instructions** → Globale Agent-Identität
6. **Project Instructions** → Workspace-spezifische Regeln
7. **Cache Isolation** → Jeder Workspace: `.ki_autoagent_ws/cache/`
8. **NO Spawning** → VS Code Extension startet Backend NICHT, nur Verbindung (v5.8.1)

### **Verzeichnisse:**
```
GLOBAL:     $HOME/.ki_autoagent/           (Agent Service)
WORKSPACE:  $WORKSPACE/.ki_autoagent_ws/   (Projekt-Daten)
LEGACY:     ~/.ki-autoagent/               (Backwards Compatibility)
```

---

## 🚨 REMINDER: ARCHITEKTUR-REGELN BEACHTEN!

**Bei JEDER Änderung am System:**
1. **Backend** → Python (`$HOME/.ki_autoagent/backend/`)
2. **UI** → TypeScript (`vscode-extension/`)
3. **AI Calls** → NUR Python Backend
4. **Frontend ↔ Backend** → NUR WebSocket zu `ws://localhost:8001`
5. **Workspace Analyse** → NUR `session["workspace_path"]`, NICHT Backend-Code!
6. **Base Instructions** → `$HOME/.ki_autoagent/config/instructions/`
7. **Project Instructions** → `$WORKSPACE/.ki_autoagent_ws/instructions/`
8. **NO SPAWNING** → VS Code Extension darf Backend NICHT starten! (v5.8.1)
9. **Init Protocol** → Client MUSS init message mit workspace_path senden (v5.8.1)

**Verstöße gegen diese Regeln führen zu Duplikation und Chaos!**

---

## 🔧 CODE REFACTORING BEST PRACTICES (v5.8.4+)

### **OBSOLETE Code Handling Protocol**

**WICHTIG**: Beim Entfernen von Code IMMER diesen Prozess folgen:

#### 1. **Mark as OBSOLETE First** (NIEMALS direkt löschen!)
```python
# ============================================================================
# OBSOLETE v5.8.4: The following methods are no longer needed
# Reason: workflow.py handles actual execution, Orchestrator only plans
# Marked for removal after testing confirms everything works
# ============================================================================

async def execute_workflow(...):
    """
    OBSOLETE v5.8.4: This is a simulation only
    Real execution happens in workflow.py via _execute_*_task methods
    """
    # ... original code bleibt ...

# ============================================================================
# END OBSOLETE SECTION - All methods above marked for removal after testing
# ============================================================================
```

#### 2. **Test Thoroughly**
- Erstelle TestApp und validiere Funktionalität
- Überprüfe alle Call-Sites
- Sicherstellen dass neue Implementierung funktioniert

#### 3. **Only Then Remove**
- Nach erfolgreichen Tests kann Code entfernt werden
- Git Commit mit Verweis auf OBSOLETE Markierung
- Dokumentiere Removal im CHANGELOG

### **Warum dieser Prozess?**
- ✅ **Sicher**: Code bleibt funktional während Tests laufen
- ✅ **Nachvollziehbar**: Klare Markierung was entfernt werden soll
- ✅ **Revertable**: Easy rollback falls Probleme auftreten
- ✅ **Team-Friendly**: Andere sehen was deprecated ist

### **Anweisung für Fixer Agent**:
Wenn du OBSOLETE markierten Code findest:
1. Prüfe ob Tests existieren und erfolgreich sind
2. Wenn ja: Entferne OBSOLETE Sektion komplett
3. Wenn nein: Frage User ob Tests durchgeführt wurden
4. NIEMALS OBSOLETE Code ohne Bestätigung entfernen!

---

## 🐍 PYTHON CODING STANDARDS (v5.9.0+)

### **WICHTIG: Alle Python Code Änderungen MÜSSEN den Best Practices folgen!**

**Referenz:** `/PYTHON_BEST_PRACTICES.md` (Vollständige Dokumentation)

**Python Version:** 3.13+ (keine Rückwärtskompatibilität erforderlich)

### **Key Rules (Kurzfassung)**

#### 1. **Error Handling**
```python
# ✅ RICHTIG: Variablen VOR try initialisieren
result: AgentResult | None = None
content: str | None = None

try:
    result = agent.execute(task)
    content = result.content
except ExecutionError as e:
    logger.error(f"Failed: {e}")
    fallback = content[:100] if content else "No content"  # ✅ Safe!
```

**Anti-Patterns zu vermeiden:**
- ❌ Variablen in `try` definieren und in `except` verwenden → UnboundLocalError!
- ❌ Generic `except Exception:` → Immer spezifische Exceptions
- ❌ Silent failures mit `pass` → Immer loggen oder re-raise
- ❌ Bare `except:` → Catcht auch KeyboardInterrupt!

#### 2. **Type Hints (Python 3.10+ Syntax)**
```python
# ✅ RICHTIG: Native types und | operator
def process_data(
    items: list[str],
    config: dict[str, Any]
) -> dict[str, int] | None:
    pass

# ❌ FALSCH: Veraltete typing.* imports
from typing import List, Dict, Optional, Union
def process_data(items: List[str]) -> Optional[Dict[str, int]]:
    pass
```

**Regeln:**
- Alle public functions haben vollständige Type Hints
- `list[str]` statt `List[str]` (Python 3.9+)
- `X | Y` statt `Union[X, Y]` (Python 3.10+)
- `X | None` statt `Optional[X]` (Python 3.10+)

#### 3. **Context Managers für Resources**
```python
# ✅ RICHTIG: with statement
with open("data.txt") as file:
    data = file.read()

# ❌ FALSCH: Manuelles close()
file = open("data.txt")
data = file.read()
file.close()  # Vergessen = Resource Leak!
```

**Regeln:**
- IMMER `with` für File Operations
- IMMER `with` für Database Connections
- IMMER `with` für Network Connections
- Context Managers > try-finally

#### 4. **Async/Await Patterns**
```python
# ✅ RICHTIG: gather() für concurrent execution
results = await asyncio.gather(
    fetch_data(url1),
    fetch_data(url2),
    fetch_data(url3)
)

# ❌ FALSCH: Sequential awaits (langsam!)
result1 = await fetch_data(url1)
result2 = await fetch_data(url2)
result3 = await fetch_data(url3)
```

**Regeln:**
- Sequential `await` nur wenn wirklich sequential notwendig
- `gather()` für concurrent execution
- Timeouts für I/O operations setzen
- CPU-bound work zu ThreadPoolExecutor offloaden

#### 5. **Clean Code Principles**
```python
# ✅ RICHTIG: Early returns, keine deep nesting
def process(data: Data | None) -> Result:
    if not data:
        return error("No data")
    if not data.valid:
        return error("Invalid")
    if not data.user:
        return error("No user")

    # Happy path
    return success(data)

# ❌ FALSCH: Deep nesting
def process(data):
    if data:
        if data.valid:
            if data.user:
                # Do work here
                pass
```

**Regeln:**
- Functions < 50 Zeilen (idealerweise < 20)
- Single Responsibility Principle
- Early returns statt deep nesting
- Meaningful names (PEP 8)
- No magic numbers (use constants)

### **Code Review Checklist**

**Vor jedem Commit prüfen:**
- [ ] Variablen vor `try` initialisiert?
- [ ] Spezifische Exception Types verwendet?
- [ ] Type Hints vorhanden?
- [ ] Context Managers für Resources?
- [ ] Keine mutable default arguments?
- [ ] Docstrings für public functions?
- [ ] PEP 8 compliant (nutze `ruff` oder `black`)?
- [ ] No anti-patterns (siehe PYTHON_BEST_PRACTICES.md)?

### **Tools**

**Linting & Formatting:**
- `ruff` - Extremely fast linter (empfohlen)
- `black` - Code formatter
- `mypy` oder `pyright` - Static type checker

**Installation:**
```bash
pip install ruff black mypy
```

**Usage:**
```bash
# Linting
ruff check backend/

# Formatting
black backend/

# Type checking
mypy backend/
```

### **Bei Verstößen**

**Code der diese Standards verletzt MUSS refactored werden!**

1. Mark als OBSOLETE mit Kommentar
2. Schreibe neuen Code nach Standards
3. Teste thoroughly
4. Remove OBSOLETE Code
5. Commit mit klarer Message

**Beispiel Commit Message:**
```
fix: Modernize error handling in workflow.py

- Initialize variables before try blocks
- Use specific exception types
- Add type hints for all functions
- Replace try-finally with context managers

Follows PYTHON_BEST_PRACTICES.md guidelines
Ref: #123
```

---

## 🤖 CLAUDE CLI INTEGRATION (v6.0+)

### **CRITICAL: Correct Claude CLI Syntax**

**Model:** `claude-sonnet-4-20250514` (Sonnet 4.5) - Default for all agents

**Valid Tools:** ONLY `["Read", "Edit", "Bash"]`
- ❌ **"Write" does NOT exist!** Use "Edit" instead
- ✅ Read - Read files
- ✅ Edit - Create/modify files
- ✅ Bash - Execute shell commands

### **Complete CLI Command Template**

```bash
claude \
  --model claude-sonnet-4-20250514 \
  --permission-mode acceptEdits \
  --allowedTools Read Edit Bash \
  --agents '{
    "agent_name": {
      "description": "Brief description of agent role",
      "prompt": "System prompt defining agent behavior and instructions",
      "tools": ["Read","Edit","Bash"]
    }
  }' \
  --output-format stream-json \
  --verbose \
  -p "User task/prompt here"
```

### **Key Parameters**

1. **--permission-mode acceptEdits**
   - Auto-approves file edits (no manual confirmation needed)
   - Required for automated code generation

2. **--allowedTools Read Edit Bash**
   - Global tool whitelist
   - Space-separated list

3. **--agents '{...}'**
   - **OBJECT syntax**, not array: `{"name": {...}}`
   - NOT: `[{"name": "...", ...}]` ❌
   - Contains: description, prompt, tools

4. **--output-format stream-json**
   - Returns JSONL (JSON Lines)
   - Avoids truncation bug in regular JSON (Issue #2904)
   - Each line is a complete JSON event

5. **--verbose**
   - **REQUIRED** for stream-json to work properly
   - Without this, stream-json may timeout

6. **-p "..."**
   - User prompt/task (separate from agent.prompt)
   - Agent.prompt = system instructions
   - -p = user task

### **Python Integration Example**

```python
from adapters.use_claude_cli import use_claude_cli
use_claude_cli()

from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    temperature=0.2,
    max_tokens=8192,
    agent_name="codesmith",
    agent_description="Expert code generator following best practices",
    agent_tools=["Read", "Edit", "Bash"],  # NO Write!
    permission_mode="acceptEdits"
)

response = await llm.ainvoke([
    SystemMessage(content="Agent instructions..."),
    HumanMessage(content="User task...")
])
```

### **JSONL Response Format**

Claude CLI returns JSON Lines (one JSON object per line):

```jsonl
{"type":"system","subtype":"init",...}
{"type":"assistant","message":{...}}
{"type":"user","message":{...}}
{"type":"result","subtype":"success","result":"...",duration_ms:1234,...}
```

**Last line** contains the final result in `result` field.

### **Common Mistakes**

❌ **Using Write tool**
```python
agent_tools=["Read", "Write", "Edit"]  # WRONG! Write doesn't exist
```

✅ **Correct**
```python
agent_tools=["Read", "Edit", "Bash"]  # RIGHT!
```

❌ **Array syntax for --agents**
```bash
--agents '[{"name":"agent",...}]'  # WRONG!
```

✅ **Object syntax**
```bash
--agents '{"agent": {...}}'  # RIGHT!
```

❌ **Missing --verbose with stream-json**
```bash
--output-format stream-json  # WRONG! May timeout
```

✅ **Include --verbose**
```bash
--output-format stream-json --verbose  # RIGHT!
```

### **File Generation Best Practices**

When generating code, specify exact file paths in prompt:

```bash
-p "Generate Task Manager app.
Write files to:
  src/task.py
  src/manager.py
  main.py
  tests/test_manager.py"
```

This ensures Claude creates files at exact locations without asking.

---

## 🏗️ BUILD VALIDATION SYSTEM (v6.0+)

### **Comprehensive Multi-Language Build Validation**

**Implemented:** 2025-10-12 (v6.0.0)

The build validation system automatically runs appropriate build/lint checks after code generation to ensure generated code actually compiles/runs.

### **Supported Validation Types**

#### 1. **TypeScript Compilation Check** (Quality Threshold: 0.90)
- **Tool:** `tsc --noEmit`
- **Detects:** `.ts`, `.tsx` files
- **Requirements:** `tsconfig.json` and `package.json` in workspace
- **Timeout:** 60 seconds
- **Errors → Quality Score:** 0.50 (forces iteration)

**Example Output:**
```
📘 Project Type: TypeScript
   Quality Threshold: 0.90 (highest)
🔬 Running TypeScript compilation check (tsc --noEmit)...
✅ TypeScript compilation passed! (0.8s)
✅ Build validation PASSED
```

#### 2. **Python Type Checking** (Quality Threshold: 0.85)
- **Tool:** `python3 -m mypy`
- **Detects:** `.py` files
- **Flags:** `--ignore-missing-imports`, `--no-strict-optional`
- **Timeout:** 60 seconds
- **Graceful Degradation:** Warns if mypy not installed

**Example Output:**
```
🐍 Project Type: Python
   Quality Threshold: 0.85
🔬 Running Python mypy type check (5 files)...
✅ Python mypy type check passed!
✅ Build validation PASSED
```

#### 3. **JavaScript Linting** (Quality Threshold: 0.75)
- **Tool:** `npx eslint`
- **Detects:** `.js`, `.jsx` files (excluding `.ts`/`.tsx`)
- **Timeout:** 60 seconds
- **Return Codes:** 0 = success, 1 = lint errors, 2 = fatal error
- **Graceful Degradation:** Continues on configuration issues

**Example Output:**
```
📙 Project Type: JavaScript
   Quality Threshold: 0.75
🔬 Running JavaScript ESLint check (3 files)...
✅ JavaScript ESLint check passed!
✅ Build validation PASSED
```

### **Polyglot Project Support**

**NEW in v6.0.0:** Multiple validation checks run for mixed-language projects!

Changed from `elif` to `if` to support projects with multiple languages:

```python
# ✅ NOW: Multiple checks for polyglot projects
if has_typescript:
    # TypeScript check runs
if has_python:
    # Python check ALSO runs (if .py files exist)
if has_javascript:
    # JavaScript check ALSO runs (if .js files exist)
```

**Example:** TypeScript frontend + Python backend → BOTH checks run!

### **Quality Score Management**

When build validation **FAILS:**

1. **Original Quality Score Preserved** - Logged for debugging
2. **Quality Score Reduced to 0.50** - Forces another ReviewFix iteration
3. **Build Errors Appended to Feedback** - Fixer knows what to fix

**Example:**
```
⚠️  Build validation FAILED - reducing quality score to 0.50
   Original quality score: 0.82
   New quality score: 0.50

## BUILD VALIDATION ERRORS

**typescript_compilation:**
```
src/app.tsx(15,7): error TS2322: Type 'string' is not assignable to type 'number'.
src/utils.ts(23,12): error TS2304: Cannot find name 'process'.
```
```

### **Implementation Location**

File: `backend/subgraphs/reviewfix_subgraph_v6_1.py`

Build validation runs **AFTER** GPT-4o-mini code review, **BEFORE** storing review in memory.

```python
async def reviewer_node(state: ReviewFixState) -> ReviewFixState:
    # 1. Read generated files
    # 2. GPT-4o-mini review (quality score)
    # 3. BUILD VALIDATION (this is where it runs)
    # 4. Adjust quality score if build fails
    # 5. Store review in memory
    # 6. Return state
```

### **Error Handling**

All validation checks handle errors gracefully:

```python
try:
    result = subprocess.run(
        ['npx', 'tsc', '--noEmit'],
        cwd=workspace_path,
        capture_output=True,
        text=True,
        timeout=60
    )
    # Check result...
except subprocess.TimeoutExpired:
    logger.error("❌ TypeScript compilation timeout (60s)")
    build_validation_passed = False
except FileNotFoundError:
    logger.warning("⚠️  Tool not installed - skipping check")
except Exception as e:
    logger.error(f"❌ Check failed: {e}")
    build_validation_passed = False
```

### **Installation Requirements**

#### TypeScript Projects:
```bash
npm install -D typescript  # tsc must be available
```

#### Python Projects:
```bash
pip install mypy  # Optional but recommended
```

#### JavaScript Projects:
```bash
npm install -D eslint  # Optional but recommended
```

### **Configuration**

No configuration needed! System automatically:
1. Detects project type from generated files
2. Checks for required tools (tsconfig.json, mypy, eslint)
3. Runs appropriate validation
4. Skips validation if tool not available (with warning)

### **Performance**

- **TypeScript Check:** 0.8s (fast!)
- **Python Check:** 1-2s (depending on file count)
- **JavaScript Check:** 1-2s (depending on file count)
- **Total Overhead:** 1-5s (minimal impact on overall workflow)

### **Future Enhancements**

Potential improvements (not yet implemented):

1. **True Parallel Execution** - Run all checks with `asyncio.gather()`
2. **Go Validation** - `go build` or `go vet`
3. **Rust Validation** - `cargo check`
4. **Java Validation** - `javac` or Maven/Gradle
5. **Custom Validation** - User-defined validation scripts

Currently uses sequential execution but supports multiple checks for polyglot projects.

### **Debugging Build Validation**

#### Check if validation ran:
```bash
grep "Running.*compilation check" /tmp/v6_server.log
```

#### Check validation results:
```bash
grep "Build validation" /tmp/v6_server.log
```

#### Check project type detection:
```bash
grep "Project Type:" /tmp/v6_server.log
```

### **Known Issues**

- **Python mypy validation** - Not yet implemented (TODO)  ✅ **FIXED in v6.0.0!**
- **JavaScript ESLint validation** - Not yet implemented (TODO)  ✅ **FIXED in v6.0.0!**
- **Parallel validation** - Currently sequential  ⏳ **Polyglot support added, true async TBD**

### **Best Practices**

1. **Always install build tools** - TypeScript projects need `tsconfig.json`
2. **Check logs for validation results** - Build validation runs silently
3. **Quality score 0.50** - Indicates build failure, fixer will iterate
4. **Graceful degradation** - Missing tools warn but don't fail workflow

---

## 🧪 E2E TESTING BEST PRACTICES (v6.0+)

### **CRITICAL: Test Workspace Isolation**

**Discovered:** 2025-10-11 E2E Test Bug - Claude CLI found old test artifacts in development repo

### **GOLDEN RULE:**

```
🚨 NIEMALS E2E Tests im Development Workspace durchführen!
🚨 NEVER run E2E tests in the development repository!
```

### **Why This Matters:**

**Problem Scenario:**
```
/Users/.../KI_AutoAgent/  ← Development Repo
├── backend/              ← Agent source code
├── test_e2e.py           ← E2E test script
└── task-manager-app/     ← OLD test output (❌ PROBLEM!)

# Claude CLI runs E2E test:
1. Test runs from: /Users/.../KI_AutoAgent/
2. Claude CLI subprocess CWD: /Users/.../KI_AutoAgent/
3. Claude finds: task-manager-app/ (old output)
4. Claude reads old app
5. Claude gets confused: "App already exists!"
6. Codesmith crashes after 5 minutes
7. ❌ Test FAILS but bug is hidden!
```

**Impact:**
- Claude finds old test artifacts
- Gets confused about what to generate
- Context pollution with obsolete code
- Test failures that are hard to debug
- Claude CLI subprocess crashes
- Wasted API tokens and time

### **Correct E2E Test Setup:**

#### **1. Separate Test Workspace**

```bash
# ✅ CORRECT: Isolated test directory
~/TestApps/
├── test_run_1/         # First test execution
│   └── task_manager_app/
├── test_run_2/         # Second test execution
│   └── task_manager_app/
└── current/            # Current test (symlink or latest)
    └── task_manager_app/

# ❌ WRONG: Test in development repo
~/git/KI_AutoAgent/
├── backend/            # Source code
├── test_e2e.py         # Test script
└── task-manager-app/   # Test output ❌ POLLUTES WORKSPACE!
```

#### **2. Claude CLI Working Directory**

**CRITICAL:** Set `cwd` parameter in subprocess!

```python
# File: backend/adapters/claude_cli_simple.py

# ❌ WRONG: No CWD specified
process = await asyncio.create_subprocess_exec(
    *cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
# Result: Runs from wherever Python was started (❌ chaos!)

# ✅ CORRECT: Explicit CWD to workspace
process = await asyncio.create_subprocess_exec(
    *cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=self.workspace_path  # 🎯 Use target workspace!
)
# Result: Claude CLI runs in clean, isolated workspace ✅
```

#### **3. E2E Test Script Template**

```python
#!/usr/bin/env python3
"""
E2E Test - Isolated Workspace Pattern

CRITICAL: This test MUST run in a separate workspace!
"""

import os
from pathlib import Path
import shutil

# ✅ CORRECT: Separate test workspace
TEST_WORKSPACE = Path.home() / "TestApps" / "e2e_test_run"

# ❌ WRONG: Development repo as workspace
# TEST_WORKSPACE = Path(__file__).parent / "test_output"  # ❌ NO!

def setup_test():
    """Setup clean test workspace."""
    # Remove old test artifacts
    if TEST_WORKSPACE.exists():
        print(f"🧹 Cleaning old workspace: {TEST_WORKSPACE}")
        shutil.rmtree(TEST_WORKSPACE)

    # Create fresh workspace
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created clean workspace: {TEST_WORKSPACE}")

    # Verify isolation
    assert not (TEST_WORKSPACE / "task-manager-app").exists()
    print("✅ Workspace verified clean")

async def run_e2e_test():
    """Run E2E test in isolated workspace."""
    setup_test()

    # Connect to backend with isolated workspace
    client = E2ETestClient(
        ws_url="ws://localhost:8002/ws/chat",
        workspace_path=str(TEST_WORKSPACE)
    )

    await client.connect()
    await client.send_task("Create Task Manager app...")

    # Verify files created in correct location
    assert (TEST_WORKSPACE / "README.md").exists()
    print("✅ Files generated in isolated workspace")

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
```

#### **4. Backend Workspace Handling**

```python
# File: backend/subgraphs/codesmith_subgraph_v6_1.py

async def codesmith_node(state: dict) -> dict:
    """Codesmith node - MUST use correct workspace."""

    # Get workspace from state (set by WebSocket init)
    workspace_path = state.get("workspace_path")

    if not workspace_path:
        raise ValueError("workspace_path required in state!")

    # Create Claude CLI LLM with correct workspace
    llm = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        workspace_path=workspace_path,  # 🎯 Pass to subprocess!
        ...
    )

    # Claude CLI will now run with correct CWD
    response = await llm.ainvoke([...])
```

### **Test Cleanup Best Practices**

#### **After Each Test:**

```python
def cleanup_test(keep_on_success: bool = False):
    """Cleanup test workspace."""

    if keep_on_success and test_passed:
        print(f"✅ Test passed - keeping workspace: {TEST_WORKSPACE}")
        # Optional: Create timestamped backup
        backup = TEST_WORKSPACE.parent / f"test_success_{datetime.now():%Y%m%d_%H%M%S}"
        shutil.copytree(TEST_WORKSPACE, backup)
        print(f"📦 Backup created: {backup}")
    else:
        print(f"🧹 Cleaning up test workspace: {TEST_WORKSPACE}")
        if TEST_WORKSPACE.exists():
            shutil.rmtree(TEST_WORKSPACE)
        print("✅ Cleanup complete")
```

#### **Continuous Integration:**

```bash
# CI/CD pipeline test script
#!/bin/bash

# Create unique test workspace per run
TEST_ID=$(date +%Y%m%d_%H%M%S)_$$
TEST_WS="/tmp/ki_autoagent_e2e_${TEST_ID}"

echo "🧪 Running E2E test in: $TEST_WS"

# Run test
python test_e2e_websocket.py --workspace "$TEST_WS"
TEST_EXIT=$?

# Cleanup (always in CI)
rm -rf "$TEST_WS"

exit $TEST_EXIT
```

### **Development Repo Protection**

#### **Add to .gitignore:**

```gitignore
# E2E Test Outputs (should NEVER be in development repo!)
test_output/
task-manager-app/
*_e2e_test/
TestApps/
tmp_*_workspace/

# Test artifacts
*.e2e.log
e2e_test_results_*.json
```

#### **Pre-commit Hook:**

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check for test artifacts in development repo
if git diff --cached --name-only | grep -E "task-manager-app|test_output"; then
    echo "❌ ERROR: E2E test artifacts found in commit!"
    echo "   E2E tests must run in separate workspace (~/TestApps/)"
    echo "   Remove: git reset HEAD <file>"
    exit 1
fi
```

### **Debugging E2E Test Issues**

#### **Common Issues:**

**1. "App already exists" / Claude reads wrong files:**
```bash
# Debug: Check Claude CLI working directory
grep '"cwd":' /tmp/claude_cli_debug.log

# Should show:
"cwd": "/Users/.../TestApps/task_manager_app"

# NOT:
"cwd": "/Users/.../git/KI_AutoAgent"  ❌
```

**2. Files generated in wrong location:**
```bash
# Check workspace_path in backend logs
tail -f /tmp/v6_server.log | grep "workspace_path"

# Should see:
workspace_path: /Users/.../TestApps/task_manager_app  ✅
```

**3. Claude CLI crashes after 5 minutes:**
```bash
# Check raw CLI output
cat /var/folders/.../tmp*_claude_raw.jsonl | grep "Glob\|Read"

# If you see reads from development repo:
# → CWD is wrong! Fix subprocess cwd parameter
```

### **Checklist for E2E Tests**

**Before Running Test:**
- [ ] Test workspace is OUTSIDE development repo
- [ ] Test workspace is clean (no old artifacts)
- [ ] Claude CLI `cwd` parameter is set correctly
- [ ] Backend receives correct `workspace_path` from client
- [ ] `.gitignore` excludes test outputs

**After Test Failure:**
- [ ] Check Claude CLI working directory in logs
- [ ] Verify no old apps in test workspace
- [ ] Check if Claude read files from development repo
- [ ] Inspect subprocess CWD in debug logs
- [ ] Clean workspace and re-run

**After Test Success:**
- [ ] Verify files in correct location
- [ ] Optional: Keep workspace for manual inspection
- [ ] Run cleanup unless debugging needed
- [ ] Document any new issues found

### **E2E Test Best Practices Summary**

| ✅ DO | ❌ DON'T |
|-------|----------|
| Use separate `~/TestApps/` directory | Test in development repo |
| Set `cwd=workspace_path` in subprocess | Let subprocess inherit CWD |
| Clean workspace before each test | Reuse old test workspaces |
| Verify workspace isolation | Assume CWD is correct |
| Add test outputs to `.gitignore` | Commit test artifacts |
| Use timestamped test directories | Overwrite previous tests |
| Log workspace_path in all agents | Trust default working directory |

### **Key Lesson:**

**The E2E test on 2025-10-11 discovered this critical bug:**

- Codesmith crashed after 5 minutes
- Root cause: Wrong working directory
- Claude found old test app in development repo
- Got confused and crashed
- **Fix:** Set `cwd=self.workspace_path` in subprocess

**This is why we do E2E testing!** 🎯

---
