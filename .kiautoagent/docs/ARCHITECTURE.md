# ⚠️ KRITISCHE ARCHITEKTUR-REGELN - KI_AutoAgent System

## 🚨 WICHTIGSTE REGEL: PYTHON-BACKEND ARCHITEKTUR (September 2025)

### ⛔ NIEMALS - ABSOLUTE VERBOTE:
1. **KEINE Agent-Implementierungen in TypeScript/JavaScript**
   - Alle Agents MÜSSEN im Python Backend sein (`backend/agents/`)
   - TypeScript ist NUR für UI-Komponenten

2. **KEINE Business-Logic im VS Code Extension Frontend**
   - Keine direkten AI-API Calls aus TypeScript
   - Keine Workflow-Logic in VS Code Extension
   - Keine Agent-Intelligence im Frontend

3. **KEINE direkten Model-Calls aus TypeScript**
   - Alle OpenAI/Anthropic/Perplexity Calls NUR aus Python Backend
   - Frontend kommuniziert NUR über WebSocket mit Backend

### ✅ ARCHITEKTUR-ÜBERBLICK:

```
📦 KI_AutoAgent/
├── 🐍 backend/                  # ALLE INTELLIGENZ HIER!
│   ├── api/                     # FastAPI Server (Port 8001)
│   ├── agents/                  # ALLE Agent-Implementierungen
│   ├── langgraph_system/        # LangGraph Workflow Engine
│   ├── core/                    # Memory, SharedContext, Workflows
│   └── utils/                   # AI Service Integrations
│
└── 🎨 vscode-extension/          # NUR UI - KEINE LOGIC!
    ├── src/
    │   ├── api/BackendClient.ts # WebSocket zu Python
    │   └── webview/             # Chat UI
    └── [DEPRECATED]/            # Alte TS Agents - NICHT VERWENDEN!
```

### 🎯 GOLDEN RULES:

| Component | Location | Responsibility |
|-----------|----------|----------------|
| **Agents** | `backend/agents/` | ALLE AI-Agent Implementierungen |
| **AI APIs** | `backend/utils/` | OpenAI, Anthropic, Perplexity Calls |
| **Memory** | `backend/core/memory/` | Vector DB, Pattern Recognition |
| **Workflows** | `backend/langgraph_system/` | Task Decomposition, Parallel Execution |
| **VS Code UI** | `vscode-extension/` | NUR Visual Display & User Input |
| **WebSocket** | `ws://localhost:8001/ws/chat` | Einzige Verbindung Frontend↔Backend |

### 🔄 WORKFLOW:

```
User Input (VS Code)
    ↓ [WebSocket]
Python Backend (localhost:8001)
    ↓ [Process]
Agent Intelligence (Python)
    ↓ [WebSocket]
Display Result (VS Code)
```

### ⚠️ MIGRATION STATUS (September 2025):
- ✅ Python Backend läuft auf Port 8001
- ✅ FastAPI mit WebSocket Support
- ✅ LangGraph v5.0.0 Integration
- ✅ BaseAgent & Extended State System
- 🚧 TypeScript Agents werden NICHT mehr verwendet
- 🚧 VS Code Extension ist reiner UI-Client

---

# 📁 STANDARDISIERTE PROJEKT-ORDNER - KI_AutoAgent System

## 🎯 STANDARD PROJEKTORDNER: `.kiautoagent`

### ⚠️ WICHTIG: NUR EINEN ORDNER VERWENDEN!
**Standardisiert auf:** `.kiautoagent` (mit Unterstrich, lowercase)

**NIEMALS verwenden:**
- ❌ `.ki_autoagent` (mit Unterstrich + Großbuchstaben)
- ❌ `.KI_AutoAgent`
- ❌ `.ki-autoagent`
- ❌ Andere Varianten

### 📂 STRUKTUR:
```
.kiautoagent/
├── instructions/        # Agent-spezifische Anweisungen
├── config/             # Konfigurationsdateien
├── learning/           # Agent-Lernverlauf
├── docs/               # Ausgelagerte Dokumentation
├── search.db          # SQLite Suchindex
└── system_analysis.json # System-Analyse Cache
```

### ✅ VERWENDUNG IN CODE:
```python
# Korrekt:
base_path = os.path.join(workspace_path, '.kiautoagent')
instructions_path = '.kiautoagent/instructions'

# Falsch:
# base_path = os.path.join(workspace_path, '.ki_autoagent')  # NEIN!
```
