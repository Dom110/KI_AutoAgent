---
description: Repository Information Overview
alwaysApply: true
---

# Repository Information Overview

## Repository Summary
KI AutoAgent is a **Universal Multi-Agent AI Development Platform** that orchestrates specialized AI agents to solve complex development tasks. It consists of a Pure MCP (Model Context Protocol) v7.0 backend using Python with FastAPI, and a VS Code extension frontend written in TypeScript. The system enables seamless integration of multiple AI models (GPT-4o, Claude Sonnet, Perplexity) for code generation, architecture design, testing, documentation, and trading strategy development.

## Repository Structure

### Main Directory Components
- **backend/**: Pure MCP v7.0 Python backend with FastAPI server and agent orchestration
- **vscode-extension/**: TypeScript/JavaScript VS Code extension with chat UI and agent integration
- **mcp_servers/**: 11 MCP servers implementing agent logic (6 agents + 5 utilities)
- **ki_autoagent_mcp/**: MCP configuration and initialization
- **agents/**, **api/**, **core/**, **config/**, **services/**: Backend module packages
- **scripts/**, **examples/**: Utility scripts and example applications
- **docs/**: Project documentation and guides

---

## Projects

### 1. Backend - Pure MCP v7.0 Architecture
**Configuration File**: `backend/requirements.txt` | **Server**: `backend/api/server_v7_mcp.py`

#### Language & Runtime
**Language**: Python
**Version**: 3.9.6+ (tested with 3.13+)
**Framework**: FastAPI 0.117.1 with uvicorn 0.37.0
**Build System**: Native (no build required, dependencies managed via pip)
**Package Manager**: pip

#### Dependencies
**Main Dependencies**:
- FastAPI (API framework) + uvicorn (ASGI server)
- openai (GPT models), anthropic (Claude), google-generativeai (Gemini)
- aiohttp (async HTTP for Perplexity), websockets (real-time communication)
- chromadb (vector database), redis (caching), sqlalchemy (ORM), aiosqlite (async SQLite)
- pydantic (data validation), python-dotenv (env config)

**Development Dependencies**:
- pytest, pytest-asyncio, pytest-mock, pytest-cov (testing)
- black (code formatting)

#### Build & Installation
```bash
# From project root
cd /Users/dominikfoert/git/KI_AutoAgent
source venv/bin/activate
pip install -r backend/requirements.txt
python backend/api/server_v7_mcp.py
```

#### Docker
**Docker Compose**: `docker-compose.yml`
**Services**:
- **backend**: Python FastAPI server (port 8000)
- **redis**: Redis cache (port 6379)
**Start**: `docker-compose up -d`

#### Main Files & Architecture
**Entry Points**:
- `backend/api/server_v7_mcp.py` - Main FastAPI server (MCP architecture)
- WebSocket: `ws://localhost:8002/ws/chat`

**MCP Server Registry (11 servers)**:
- **Agent Servers**: openai, research_agent, architect_agent, codesmith_agent, reviewfix_agent, responder_agent
- **Utility Servers**: perplexity, memory, build_validation, file_tools, tree_sitter
- Located in: `mcp_servers/` directory

**Configuration**:
- `.env.example` - Environment variables template
- `backend/config/` - Configuration modules
- `backend/core/` - Core utilities and base classes

#### Testing
**Framework**: pytest with asyncio support
**Test Location**: `backend/tests/` (37+ test files)
**Naming Convention**: `test_*.py` and `e2e_*.py`
**Configuration**: pytest auto-discovery

**⚠️ CRITICAL - E2E TESTS MUST RUN IN SEPARATE FOLDER!**

E2E tests create full applications and must NOT run from project root (`/Users/dominikfoert/git/KI_AutoAgent`).

**WHY**: 
- Architect agent scans codebase under test
- Running from project root = Architect scans itself → circular dependency
- Results in corruption/confusion of project state

**HOW TO RUN E2E TESTS**:
```bash
# 1. Create test workspace
mkdir -p ~/Tests/e2e_workspace

# 2. Copy test script there
cp /Users/dominikfoert/git/KI_AutoAgent/e2e_test_v7_0_supervisor.py ~/Tests/e2e_workspace/

# 3. Activate venv from PROJECT root
cd /Users/dominikfoert/git/KI_AutoAgent
source venv/bin/activate

# 4. Run test from TEST workspace
cd ~/Tests/e2e_workspace
python e2e_test_v7_0_supervisor.py
```

**Key Test Commands**:
```bash
# Unit tests (CAN run from project root)
cd /Users/dominikfoert/git/KI_AutoAgent
source venv/bin/activate
pytest backend/tests/ -v

# E2E tests (MUST run from ~/Tests/xxx)
cd ~/Tests/e2e_workspace
python e2e_test_v7_0_supervisor.py
```

**TEST FILES**:
- `e2e_test_v7_0_supervisor.py` - Full workflow test (must run from ~/Tests/)
- `comprehensive_e2e_test.py` - Comprehensive test suite (must run from ~/Tests/)
- All files in `backend/tests/` - Unit tests (can run from project)

---

### 2. VS Code Extension
**Configuration File**: `vscode-extension/package.json` | **Main**: `vscode-extension/src/extension.ts`

#### Language & Runtime
**Language**: TypeScript
**Version**: 5.0.0+
**Target**: ES2020 (CommonJS module system)
**Runtime**: Node.js v23.11.0
**Package Manager**: npm 10.9.2
**VS Code Engine**: ^1.90.0

#### Dependencies
**Main Dependencies**:
- @anthropic-ai/sdk (Claude integration)
- openai (GPT API)
- axios (HTTP client)
- eventemitter3 (event handling)
- @anthropic-ai/claude-code (Claude code generation)

**Development Dependencies**:
- TypeScript 5.0.0, webpack 5.101.3, ts-loader 9.5.4
- @types/node, @types/vscode

#### Build & Installation
```bash
# Install dependencies
cd vscode-extension
npm install

# Development build
npm run compile

# Production build
npm run package

# Auto-versioning & build
npm run build
```

#### Main Files & Structure
**Entry Point**: `vscode-extension/src/extension.ts`
**Output**: `vscode-extension/dist/extension.js` (bundled)

**Subdirectories**:
- `src/backend/` - Backend communication
- `src/config/` - Extension configuration
- `src/instructions/` - Agent instruction sets
- `src/types/` - TypeScript type definitions
- `src/ui/` - UI components

**Chat Participants (Agents)**:
- ki (Orchestrator), architect, codesmith, docu, reviewer, fixer, tradestrat, research
- Defined in package.json `contributes.chatParticipants`

#### Testing
**Framework**: VSCode Extension API testing (test files in root: `test_*.py`)
**Build Validation**: webpack compilation without errors
**Key Commands**:
```bash
npm run compile  # TypeScript compilation
npm run watch    # Watch mode for development
```

---

## Development Workflow

### Environment Setup
1. Python Backend: `source venv/bin/activate` → `pip install -r backend/requirements.txt`
2. VS Code Extension: `cd vscode-extension` → `npm install`
3. Configure `.env` with API keys (OpenAI, Anthropic, Perplexity)

### Running Services
```bash
# Backend (MCP server) - MUST BE RUN FROM VENV!
cd /Users/dominikfoert/git/KI_AutoAgent
source venv/bin/activate
python backend/api/server_v7_mcp.py

# OR via Docker
docker-compose up -d

# VS Code Extension
npm run compile  # Then reload VS Code
```

**⚠️ CRITICAL**: Server MUST be started from within venv:
- Always execute: `source venv/bin/activate` FIRST
- Then run: `python backend/api/server_v7_mcp.py`
- Otherwise: MCP servers won't initialize properly, dependencies won't load
- WebSocket will be: `ws://localhost:8002/ws/chat`

### Key Technologies
- **Python Backend**: FastAPI + MCP Protocol (JSON-RPC over stdin/stdout)
- **Frontend**: TypeScript + VS Code Extension API
- **Communication**: WebSocket + HTTP
- **Storage**: Redis, SQLite, ChromaDB (vector DB)
- **AI Models**: GPT-4o, Claude Sonnet, Perplexity Pro, Gemini

---

## Notable Features
- **Pure MCP Architecture**: All agents communicate via Model Context Protocol
- **Multi-Agent Orchestration**: Supervisor routing to 6 specialized agents
- **Progressive Autonomy**: Self-understanding and adaptation capabilities
- **Global Installation**: Runs from `$HOME/.ki_autoagent/` directory
- **Workspace Isolation**: Each project gets `.ki_autoagent_ws/` for local data
- **Cost Tracking**: Budget management and token usage monitoring
- **WebSocket Chat Interface**: Real-time streaming responses
