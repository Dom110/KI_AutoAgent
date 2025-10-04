# 🤖 KI AutoAgent

**Global AI Agent Service - Universal Multi-Agent Development Platform**

[![Version](https://img.shields.io/badge/version-5.8.0-blue.svg)](https://github.com/dominikfoert/KI_AutoAgent)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-red.svg)](LICENSE)

KI AutoAgent ist ein **global installierter Agent-Service**, der spezialisierte KI-Agenten orchestriert, um komplexe Entwicklungsaufgaben zu lösen. Installiere einmal, nutze überall - von VS Code, CLI oder Web Apps.

---

## 🌟 Was ist neu in v5.8.0?

### 🚀 Global Agent Service
- **Eine Installation** → Alle Projekte nutzen denselben Agent-Service
- Läuft von `$HOME/.ki_autoagent/` - komplett getrennt von deinen Projekten
- Client-agnostic: VS Code Extension, CLI, Web App - alle nutzen denselben Service

### 📝 Two-Tier Instructions System
```
BASE INSTRUCTIONS          PROJECT INSTRUCTIONS
(Agent-Identität)     +    (Workspace-Regeln)
                      =    Merged Agent Behavior
```

**Base**: "Ich bin ArchitectAgent, ich erstelle System-Designs..."
**Project**: "In diesem Projekt: Verwende NestJS, TypeORM, Docker..."

### 🔄 Smart Update Management
```bash
./update.sh --instructions interactive  # Zeigt Diff, fragt für jede Datei
./update.sh --instructions backup       # Staging für manuelles Merge
```

### 🗂️ Workspace Isolation
Jedes Projekt bekommt `.ki_autoagent_ws/`:
- `instructions/` - Projekt-spezifische Regeln
- `cache/` - SQLite DB, File Hashes
- `memory/` - Conversation History
- `artifacts/` - Generated Outputs

---

## 🏗️ Architektur

```
$HOME/.ki_autoagent/               # GLOBAL AGENT SERVICE
├── config/
│   ├── .env                       # API Keys (OpenAI, Anthropic, ...)
│   ├── instructions/              # Base Agent Instructions
│   │   ├── architect-v2-instructions.md
│   │   ├── codesmith-v2-instructions.md
│   │   └── ...
│   └── instructions_updates/      # Update Staging Area
├── backend/                       # Python Agents (LangGraph)
├── data/                          # Agent Memories, Knowledge Base
├── venv/                          # Shared Python Environment
└── {start,stop,status}.sh         # Convenience Scripts

/Users/.../MyProject/              # DEIN WORKSPACE
├── src/                           # Dein Code
└── .ki_autoagent_ws/              # Agent Workspace Data
    ├── instructions/              # Projekt-spezifische Instructions
    ├── cache/                     # Workspace Cache
    ├── memory/                    # Agent Memories für dieses Projekt
    └── artifacts/                 # Generierte Artefakte
```

---

## 🚀 Quick Start

### Installation (Einmalig)

```bash
# 1. Repository klonen
git clone https://github.com/dominikfoert/KI_AutoAgent.git
cd KI_AutoAgent

# 2. Global installieren
./install.sh
# → Installiert nach $HOME/.ki_autoagent/
# → Erstellt start.sh, stop.sh, status.sh

# 3. API Keys konfigurieren
vim $HOME/.ki_autoagent/config/.env
# Füge hinzu:
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# PERPLEXITY_API_KEY=pplx-...
```

### Nutzung

#### Option 1: VS Code Extension (Empfohlen)
```bash
# Extension wird automatisch Backend starten
# Öffne VS Code in deinem Projekt
# Extension erkennt $HOME/.ki_autoagent/backend/ automatisch
```

#### Option 2: Manuell starten
```bash
# Backend als Service starten
$HOME/.ki_autoagent/start.sh /path/to/your/workspace

# Status checken
$HOME/.ki_autoagent/status.sh

# Stoppen
$HOME/.ki_autoagent/stop.sh
```

#### Option 3: CLI (coming soon)
```bash
ki-agent chat --workspace /path/to/project
ki-agent analyze --workspace /path/to/project
```

---

## 🤖 Die Agenten

| Agent | Rolle | Model | Spezialisierung |
|-------|-------|-------|-----------------|
| **🏗️ ArchitectAgent** | System Architect | GPT-4o | Architecture Design, System Planning, Tech Stack |
| **💻 CodeSmithAgent** | Senior Developer | Claude 4.1 Sonnet | Python/TS Development, Code Implementation |
| **🔍 ReviewerGPT** | Code Reviewer | GPT-4o-mini | Code Review, Security, Best Practices |
| **🔧 FixerBot** | Bug Hunter | Claude 4.1 Sonnet | Debugging, Performance, Error Fixes |
| **🎯 Orchestrator** | Task Manager | GPT-4o | Task Decomposition, Workflow Orchestration |
| **📚 ResearchBot** | Research Analyst | Perplexity Sonar | Web Research, Documentation Search |
| **📝 DocuBot** | Technical Writer | GPT-4o | Documentation, API Docs, Tutorials |
| **📈 TradeStrat** | Trading Expert | Claude 4.1 Sonnet | Trading Strategies, Backtesting |
| **⚡ PerformanceBot** | Performance Expert | GPT-4o | Performance Analysis, Optimization |
| **⚖️ OpusArbitrator** | Conflict Resolver | Claude Opus 4.1 | Multi-Agent Decisions, Arbitration |

---

## 📝 Project-Specific Instructions

Projekt-spezifische Regeln für Agents definieren:

```bash
# Erstelle Projekt-Instructions
mkdir -p /path/to/project/.ki_autoagent_ws/instructions

# Beispiel: Architect Custom Instructions
cat > /path/to/project/.ki_autoagent_ws/instructions/architect-custom.md << 'EOF'
# Project Architecture Rules

## Tech Stack
- Backend: NestJS + TypeORM
- Database: PostgreSQL
- Container: Docker Compose

## Code Style
- Use Dependency Injection
- Follow SOLID principles
- Write unit tests for all services

## Architecture Patterns
- Clean Architecture (Entities, Use Cases, Controllers)
- Repository Pattern for Data Access
- Event-Driven for async operations
EOF
```

Diese Instructions werden automatisch mit den Base Instructions gemerged!

---

## 🔄 Updates

### Update auf neue Version

```bash
cd /path/to/KI_AutoAgent
git pull

# Interaktives Update (empfohlen)
./update.sh --instructions interactive
# → Zeigt Diff für jede Instruction-Datei
# → Fragt: [1] Update [2] Keep [3] Save as .new [4] Show diff

# Automatisches Update (CI/CD)
./update.sh --instructions overwrite --no-prompt

# Preserve Modus (nur neue Dateien)
./update.sh --instructions preserve

# Backup Modus (neue in Staging Area)
./update.sh --instructions backup
# → Neue Instructions in: $HOME/.ki_autoagent/config/instructions_updates/v5.8.0/
```

### Migration von v5.7.0 (oder älter)

```bash
# Automatische Migration beim Install
./install.sh
# → Erkennt alte Installation bei ~/.ki-autoagent
# → Fragt nach Migration zu ~/.ki_autoagent

# Oder manuell
./scripts/migrate.sh
```

---

## 🛠️ Entwicklung

### Project Structure

```
KI_AutoAgent/
├── backend/                    # Python Agent Backend
│   ├── agents/                 # Agent Implementations
│   ├── langgraph_system/       # LangGraph Workflow System
│   ├── services/               # Shared Services
│   └── api/                    # FastAPI WebSocket Server
│
├── vscode-extension/           # VS Code Extension (TypeScript)
│   ├── src/
│   │   ├── backend/            # Backend Manager
│   │   └── ui/                 # Chat Panel UI
│   └── package.json
│
├── scripts/                    # Installation & Update Scripts
│   ├── update_instructions.py  # Interactive instruction updater
│   ├── create_version_info.py  # Version metadata
│   └── migrate.sh              # Migration script
│
├── install.sh                  # Global installation
├── update.sh                   # Update manager
└── README.md
```

### Agent Development

Neue Agents hinzufügen:

```python
# backend/agents/specialized/my_agent.py
from agents.base.chat_agent import ChatAgent, AgentConfig, AgentCapability

class MyCustomAgent(ChatAgent):
    def __init__(self):
        config = AgentConfig(
            agent_id="mycustom",
            name="MyCustomAgent",
            full_name="My Custom Specialist",
            description="Expert in custom domain",
            model="gpt-4o-2024-11-20",
            capabilities=[AgentCapability.CODE_GENERATION],
            temperature=0.7,
            max_tokens=4000,
            instructions_path=".ki_autoagent/instructions/mycustom-instructions.md",
            icon="🎨"
        )
        super().__init__(config)
```

Base Instructions erstellen:

```bash
# In KI_AutoAgent Repository (für Distribution)
cat > backend/.ki_autoagent/instructions/mycustom-instructions.md << 'EOF'
# MyCustomAgent Instructions

You are MyCustomAgent, an expert in [domain].

## Your Role
- Analyze requirements
- Generate solutions
- Optimize implementations

## Capabilities
- [Capability 1]
- [Capability 2]
EOF
```

Nach Installation landen diese in: `$HOME/.ki_autoagent/config/instructions/`

---

## 📚 Dokumentation

- **[INSTALLATION.md](docs/INSTALLATION.md)** - Detaillierte Installationsanleitung
- **[UPDATE_GUIDE.md](docs/UPDATE_GUIDE.md)** - Update-Workflows und Best Practices
- **[CLAUDE.md](CLAUDE.md)** - Entwickler-Dokumentation und Architektur
- **[API.md](docs/API.md)** - WebSocket API Referenz (coming soon)

---

## 🔧 Troubleshooting

### Backend startet nicht

```bash
# Check Status
$HOME/.ki_autoagent/status.sh

# Check Logs
tail -f $HOME/.ki_autoagent/logs/*.log

# Restart
$HOME/.ki_autoagent/stop.sh
$HOME/.ki_autoagent/start.sh /path/to/workspace
```

### Instructions werden nicht geladen

```bash
# Check Base Instructions
ls -la $HOME/.ki_autoagent/config/instructions/

# Check Project Instructions (optional)
ls -la /path/to/project/.ki_autoagent_ws/instructions/

# Reinstall Base Instructions
./update.sh --instructions overwrite
```

### Port 8001 bereits belegt

```bash
# Find process
lsof -ti :8001

# Kill process
kill $(lsof -ti :8001)

# Or use stop script
$HOME/.ki_autoagent/stop.sh
```

---

## 🤝 Contributing

Contributions welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **LangGraph** - Workflow orchestration framework
- **Anthropic Claude** - Advanced AI capabilities
- **OpenAI GPT-4** - System architecture and analysis
- **Perplexity AI** - Real-time research capabilities

---

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/dominikfoert/KI_AutoAgent/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/dominikfoert/KI_AutoAgent/discussions)
- 📧 **Email**: support@kiautoagent.dev

---

**Made with ❤️ by the KI AutoAgent Team**
