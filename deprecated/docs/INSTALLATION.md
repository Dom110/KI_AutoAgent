# 📦 KI AutoAgent Installation Guide

Detaillierte Anleitung zur Installation von KI AutoAgent v5.8.0 als globalen Agent-Service.

---

## 📋 Voraussetzungen

### System Requirements
- **OS**: macOS, Linux (Windows via WSL)
- **Python**: 3.8 oder höher
- **Git**: Für Repository-Klonen
- **Disk Space**: ~500 MB für Installation
- **RAM**: Minimum 4 GB (8 GB empfohlen)

### API Keys
Mindestens einer der folgenden API Keys wird benötigt:

- **OpenAI API Key** (empfohlen)
  - Models: GPT-4o, GPT-4o-mini
  - Registrierung: https://platform.openai.com/api-keys

- **Anthropic API Key** (empfohlen)
  - Models: Claude 4.1 Sonnet, Claude Opus 4.1
  - Registrierung: https://console.anthropic.com/

- **Perplexity API Key** (optional, für Web-Recherche)
  - Models: Sonar
  - Registrierung: https://www.perplexity.ai/settings/api

---

## 🚀 Installation

### Schritt 1: Repository klonen

```bash
# Repository klonen
git clone https://github.com/dominikfoert/KI_AutoAgent.git
cd KI_AutoAgent
```

### Schritt 2: Installation ausführen

```bash
# Installation starten
./install.sh
```

Die Installation führt automatisch folgende Schritte aus:

1. **Verzeichnis-Struktur erstellen**
   ```
   $HOME/.ki_autoagent/
   ├── backend/
   ├── config/
   ├── data/
   ├── venv/
   └── logs/
   ```

2. **Backend kopieren**
   - Python Agent Code
   - LangGraph Workflow System
   - Services und APIs

3. **Python Virtual Environment erstellen**
   - Erstellt isolierte Python-Umgebung
   - Installiert alle Dependencies aus `requirements.txt`

4. **Base Instructions installieren**
   - Kopiert Agent-Instructions nach `config/instructions/`
   - Basis-Identität für alle Agents

5. **Convenience Scripts erstellen**
   - `start.sh` - Backend starten
   - `stop.sh` - Backend stoppen
   - `status.sh` - Status überprüfen

### Schritt 3: API Keys konfigurieren

```bash
# .env Datei bearbeiten
vim $HOME/.ki_autoagent/config/.env

# ODER mit einem anderen Editor
nano $HOME/.ki_autoagent/config/.env
```

Füge deine API Keys hinzu:

```env
# OpenAI (GPT-4o, GPT-4o-mini)
OPENAI_API_KEY=sk-proj-...

# Anthropic (Claude 4.1 Sonnet, Opus)
ANTHROPIC_API_KEY=sk-ant-...

# Perplexity (Web Research) - Optional
PERPLEXITY_API_KEY=pplx-...

# Optional: Custom Settings
# AGENT_TEMPERATURE=0.7
# AGENT_MAX_TOKENS=4000
```

### Schritt 4: Installation verifizieren

```bash
# Status überprüfen
$HOME/.ki_autoagent/status.sh
```

Erwartete Ausgabe:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 KI AutoAgent Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Installation: /Users/your-user/.ki_autoagent
📦 Version: 5.8.0
⏹️  Backend: Not running
✅ Config: /Users/your-user/.ki_autoagent/config/.env
📝 Base Instructions: 10 files
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🔧 Backend starten

### Manueller Start

```bash
# Backend für spezifisches Workspace starten
$HOME/.ki_autoagent/start.sh /path/to/your/workspace

# Oder ohne Workspace (wird später von Client gesetzt)
$HOME/.ki_autoagent/start.sh
```

### VS Code Extension (automatisch)

```bash
# Extension installieren/aktivieren in VS Code
# Backend startet automatisch beim Öffnen eines Workspaces
```

### Verifikation

```bash
# Check ob Backend läuft
$HOME/.ki_autoagent/status.sh

# Oder check Port
lsof -ti :8001

# Oder check Health Endpoint
curl http://localhost:8001/health
```

Erwartete Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-04T...",
  "workflow_ready": true
}
```

---

## 🗂️ Verzeichnis-Struktur (nach Installation)

```
$HOME/.ki_autoagent/
├── backend/                          # Python Backend
│   ├── agents/
│   │   ├── base/                     # Base Agent Classes
│   │   └── specialized/              # Specialized Agents
│   ├── langgraph_system/             # Workflow Engine
│   ├── services/                     # Shared Services
│   ├── api/                          # FastAPI Server
│   └── __version__.py
│
├── config/
│   ├── .env                          # ⭐ API Keys (WICHTIG!)
│   ├── instructions/                 # ⭐ Base Agent Instructions
│   │   ├── architect-v2-instructions.md
│   │   ├── codesmith-v2-instructions.md
│   │   ├── reviewergpt-instructions.md
│   │   ├── fixerbot-instructions.md
│   │   ├── orchestrator-instructions.md
│   │   ├── research-instructions.md
│   │   ├── docubot-instructions.md
│   │   ├── performance-instructions.md
│   │   ├── tradestrat-instructions.md
│   │   └── opus-arbitrator-instructions.md
│   └── instructions_updates/         # Update Staging
│       ├── backups/                  # Backups vor Updates
│       └── vX.X.X/                   # Neue Versions-Instructions
│
├── data/
│   ├── cache/                        # Shared Agent Cache
│   ├── embeddings/                   # Vector Stores
│   ├── knowledge_base/               # Agent Knowledge
│   └── models/                       # Local Models (optional)
│
├── venv/                             # Python Virtual Environment
│   ├── bin/
│   ├── lib/
│   └── ...
│
├── logs/                             # Global Logs
│   ├── server.log
│   ├── agent_architect.log
│   └── ...
│
├── version.json                      # Installation Metadata
├── start.sh                          # ⭐ Start Script
├── stop.sh                           # ⭐ Stop Script
└── status.sh                         # ⭐ Status Script
```

---

## 🎯 Workspace Setup (Optional)

Für projekt-spezifische Agent-Konfiguration:

### 1. Workspace-Struktur erstellen

```bash
# In deinem Projekt
cd /path/to/your/project

# Workspace-Verzeichnis erstellen
mkdir -p .ki_autoagent_ws/{instructions,cache,memory,artifacts}
```

### 2. Project-Specific Instructions (optional)

```bash
# Beispiel: Architect Custom Instructions
cat > .ki_autoagent_ws/instructions/architect-custom.md << 'EOF'
# Project Architecture Instructions

## Tech Stack
- Framework: Next.js 14
- Database: PostgreSQL + Prisma
- Styling: Tailwind CSS
- Testing: Jest + Playwright

## Architecture Rules
- Use App Router (not Pages Router)
- Server Components by default
- Client Components only when needed
- API Routes in /app/api

## Code Style
- TypeScript strict mode
- Functional components with hooks
- Async/await (no .then chains)
- Error boundaries for all routes
EOF
```

Diese werden automatisch mit Base Instructions gemerged!

### 3. Workspace-spezifische Daten

```
/path/to/your/project/
└── .ki_autoagent_ws/
    ├── instructions/        # Projekt-Regeln (optional)
    ├── cache/              # SQLite DB, File Hashes (auto)
    ├── memory/             # Conversation History (auto)
    └── artifacts/          # Generated Code, Diagrams (auto)
```

---

## 🔄 Migration (von v5.7.0 oder älter)

### Automatische Migration

```bash
# install.sh erkennt alte Installation automatisch
./install.sh

# Output:
# ⚠️  Old installation detected at: /Users/you/.ki-autoagent
# Migrate to new structure (/Users/you/.ki_autoagent)? [Y/n]:
```

Wähle `Y` für automatische Migration.

### Manuelle Migration

```bash
# Migration Script direkt ausführen
./scripts/migrate.sh
```

Das Script:
1. Kopiert Backend von `~/.ki-autoagent` → `~/.ki_autoagent`
2. Migriert venv
3. Kopiert .env und Instructions
4. Migriert Daten und Logs
5. Fragt nach Löschen der alten Installation

### Was wird migriert?

- ✅ Backend Code
- ✅ Python venv
- ✅ API Keys (.env)
- ✅ Base Instructions
- ✅ Agent Data (Embeddings, Knowledge Base)
- ✅ Logs
- ✅ Version Info

---

## 🧪 Installation testen

### 1. Backend-Start testen

```bash
# Backend starten
$HOME/.ki_autoagent/start.sh /tmp/test-workspace

# In separatem Terminal: Status checken
$HOME/.ki_autoagent/status.sh
```

### 2. Health Check

```bash
# HTTP Health Endpoint
curl http://localhost:8001/health | jq

# WebSocket Connection (mit wscat)
npm install -g wscat
wscat -c ws://localhost:8001/ws/chat
```

### 3. Instructions Verifikation

```bash
# Check Base Instructions
ls -la $HOME/.ki_autoagent/config/instructions/

# Should show:
# architect-v2-instructions.md
# codesmith-v2-instructions.md
# ...
```

---

## 🐛 Troubleshooting

### Problem: Installation schlägt fehl

**Symptom**: `./install.sh` bricht mit Fehler ab

**Lösung**:
```bash
# Check Python Version
python3 --version  # Should be 3.8+

# Check Disk Space
df -h $HOME

# Check Permissions
ls -la $HOME | grep .ki_autoagent

# Manuelle Installation
mkdir -p $HOME/.ki_autoagent
# ... dann install.sh erneut
```

### Problem: venv Creation fails

**Symptom**: `python3 -m venv venv` schlägt fehl

**Lösung**:
```bash
# Install python3-venv (Ubuntu/Debian)
sudo apt-get install python3-venv

# Install python3-venv (macOS via brew)
brew install python@3.11
```

### Problem: Dependencies Installation fails

**Symptom**: `pip install -r requirements.txt` Fehler

**Lösung**:
```bash
# Update pip
$HOME/.ki_autoagent/venv/bin/pip install --upgrade pip

# Install with verbose output
$HOME/.ki_autoagent/venv/bin/pip install -r backend/requirements.txt -v

# Check specific failed package
$HOME/.ki_autoagent/venv/bin/pip install <failed-package>
```

### Problem: Backend startet nicht

**Symptom**: Port 8001 Error oder Crash

**Lösung**:
```bash
# Check Port
lsof -ti :8001

# Kill existing process
kill $(lsof -ti :8001)

# Check Logs
tail -f $HOME/.ki_autoagent/logs/server.log

# Start with debug
cd $HOME/.ki_autoagent && source venv/bin/activate
cd backend && python api/server_langgraph.py
```

### Problem: API Keys werden nicht geladen

**Symptom**: "API key not configured" Fehler

**Lösung**:
```bash
# Check .env exists
ls -la $HOME/.ki_autoagent/config/.env

# Check .env content
cat $HOME/.ki_autoagent/config/.env | grep API_KEY

# Verify format (no spaces around =)
# Correct:   OPENAI_API_KEY=sk-...
# Incorrect: OPENAI_API_KEY = sk-...

# Test loading
cd $HOME/.ki_autoagent/backend
source ../venv/bin/activate
python -c "from dotenv import load_dotenv; import os; load_dotenv('../config/.env'); print(os.getenv('OPENAI_API_KEY'))"
```

---

## 📝 Nächste Schritte

Nach erfolgreicher Installation:

1. **[UPDATE_GUIDE.md](UPDATE_GUIDE.md)** - Wie Updates funktionieren
2. **[README.md](../README.md)** - Grundlegende Nutzung
3. **[CLAUDE.md](../CLAUDE.md)** - Entwickler-Dokumentation

---

## 💡 Best Practices

### Sicherheit

- ✅ **Niemals** API Keys in Git committen
- ✅ `.env` ist in `.gitignore` (im global directory)
- ✅ Backup regelmäßig: `tar -czf ki-autoagent-backup.tar.gz ~/.ki_autoagent/`

### Performance

- ✅ SSD empfohlen für `data/embeddings/`
- ✅ Minimum 4 GB RAM für parallele Agent-Ausführung
- ✅ Cache regelmäßig cleanen: `rm -rf ~/.ki_autoagent/data/cache/*`

### Wartung

- ✅ Updates regelmäßig prüfen: `cd KI_AutoAgent && git pull`
- ✅ Logs monitoren: `tail -f ~/.ki_autoagent/logs/*.log`
- ✅ Version checken: `cat ~/.ki_autoagent/version.json`

---

**Installation erfolgreich? → Starte mit der [Nutzung](../README.md#-nutzung)!** 🚀
