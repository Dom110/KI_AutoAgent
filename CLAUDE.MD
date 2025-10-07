

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
