

---

## 🏗️ SYSTEM-ARCHITEKTUR (v5.8.0+)

### **WICHTIG: Backend ist GLOBAL installiert!**

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

#### 2. **Backend Starten**
```bash
# Als Service (alle Workspaces)
$HOME/.ki_autoagent/start.sh [/path/to/workspace]

# VS Code Extension startet automatisch mit KI_WORKSPACE_PATH
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
2. **Workspace Separation** → Analysiert NUR `$KI_WORKSPACE_PATH`
3. **Base Instructions** → Globale Agent-Identität
4. **Project Instructions** → Workspace-spezifische Regeln
5. **Cache Isolation** → Jeder Workspace: `.ki_autoagent_ws/cache/`

### **Verzeichnisse:**
```
GLOBAL:     $HOME/.ki_autoagent/           (Agent Service)
WORKSPACE:  $WORKSPACE/.ki_autoagent_ws/   (Projekt-Daten)
LEGACY:     ~/.ki-autoagent/               (Backwards Compatibility)
```

---

## 🚨 REMINDER: ARCHITEKTUR-REGELN BEACHTEN!

**Bei JEDER Änderung am System:**
1. Agents → Python Backend (`$HOME/.ki_autoagent/backend/`)
2. UI → TypeScript (`vscode-extension/`)
3. AI Calls → NUR Python Backend
4. Frontend → NUR WebSocket zu Backend
5. **Workspace Analyse → NUR `$KI_WORKSPACE_PATH`, NICHT Backend-Code!**
6. **Base Instructions → `$HOME/.ki_autoagent/config/instructions/`**
7. **Project Instructions → `$WORKSPACE/.ki_autoagent_ws/instructions/`**

**Verstöße gegen diese Regeln führen zu Duplikation und Chaos!**

---
