

---

## 🏗️ SYSTEM-ARCHITEKTUR (v5.7.0+)

### **WICHTIG: Backend ist GLOBAL installiert!**

```
~/.ki-autoagent/                    # Globale Installation
├── backend/                        # Python Backend (Agents, LangGraph)
│   ├── agents/
│   ├── api/
│   ├── langgraph_system/
│   └── ...
├── venv/                           # Python Virtual Environment
├── config/                         # Globale Konfiguration
│   ├── .env                        # API Keys
│   └── .kiautoagent/               # Agent Instructions
└── logs/                           # Globale Logs

/Users/.../KI_AutoAgent/            # Development Repo
├── backend/                        # Backend Source (für Development)
├── vscode-extension/               # Extension Source
└── ...

/Users/.../MyApp/                   # USER WORKSPACE
├── src/                            # User Code
└── .kiautoagent/                   # Workspace-spezifische Daten
```

### **Wie es funktioniert:**
1. **VS Code Extension** startet Backend aus `~/.ki-autoagent/backend/`
2. **Backend** läuft global, analysiert aber NUR den User-Workspace
3. **Environment Variable** `KI_WORKSPACE_PATH` teilt dem Backend mit, welcher Workspace analysiert werden soll
4. **Agents** arbeiten auf `$KI_WORKSPACE_PATH`, NICHT auf dem Backend-Code

### **Migration checklist:**
- [x] Backend nach `~/.ki-autoagent/backend/` kopiert
- [x] venv nach `~/.ki-autoagent/venv/` kopiert
- [x] .env nach `~/.ki-autoagent/config/.env` kopiert
- [x] BackendManager.ts updated (nutzt globales Backend, setzt KI_WORKSPACE_PATH)
- [x] server_langgraph.py updated (liest KI_WORKSPACE_PATH)
- [x] architect_agent.py updated (nutzt KI_WORKSPACE_PATH statt PROJECT_PATH)
- [x] **VERIFIZIERT**: ArchitectAgent analysiert TestApp (/Users/dominikfoert/TestApp), NICHT Backend!

---

## 🚨 REMINDER: ARCHITEKTUR-REGELN BEACHTEN!

**Bei JEDER Änderung am System:**
1. Agents → Python Backend (~/.ki-autoagent/backend/)
2. UI → TypeScript (vscode-extension/)
3. AI Calls → NUR Python Backend
4. Frontend → NUR WebSocket zu Backend
5. **Workspace Analyse → NUR $KI_WORKSPACE_PATH, NICHT Backend-Code!**

**Verstöße gegen diese Regeln führen zu Duplikation und Chaos!**

---
