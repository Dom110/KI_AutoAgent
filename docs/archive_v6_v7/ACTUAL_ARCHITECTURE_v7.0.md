# Actual Architecture v7.0 - Agent Communication Analysis

**Date:** 2025-10-29
**Critical Finding:** Agents sind **NICHT** MCP-basiert!

---

## ❌ **MISCONCEPTION: "Die Agenten arbeiten als MCP Agenten"**

**ANTWORT: NEIN!** Die v7.0 Agents nutzen **KEIN MCP-Protocol**.

---

## 🔍 **Actual Implementation (v7.0)**

### **1. Codesmith Agent**

**File:** `backend/agents/codesmith_agent.py`

**Architecture:**
```python
from backend.utils.ai_factory import AIFactory, AIRequest

class CodesmithAgent:
    def __init__(self):
        # Holt AI Provider via Factory
        self.ai_provider = AIFactory.get_provider_for_agent("codesmith")
        # Provider = ClaudeCLIService (NOT MCP!)

    async def execute(self, state: dict):
        # Ruft Claude CLI via subprocess auf
        response = await self.ai_provider.complete(request)
```

**AI Provider:** `backend/utils/claude_cli_service.py`
```python
class ClaudeCLIService(AIProvider):
    """Uses Claude CLI for code generation."""

    async def complete(self, request: AIRequest):
        # Ruft Claude CLI binary als subprocess auf
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=workspace
        )

        stdout, stderr = await process.communicate()
        # ❌ KEIN MCP-Protocol!
        # ✅ Nur subprocess mit stdin/stdout/stderr
```

**Communication Method:**
- ❌ **NOT MCP:** Kein `mcp.server.progress.report_progress`
- ❌ **NOT MCP:** Keine MCP-Server/Client-Kommunikation
- ✅ **Subprocess:** Claude CLI binary wird als subprocess gestartet
- ✅ **stdout/stderr:** Output wird über Pipes gelesen

---

### **2. Research Agent**

**File:** `backend/agents/research_agent.py`

**Architecture:**
```python
from backend.utils.ai_factory import AIFactory

class ResearchAgent:
    def __init__(self):
        self.ai_provider = AIFactory.get_provider_for_agent("research")
        # Provider = PerplexityProvider (NOT MCP!)

    async def execute(self, state: dict):
        # Ruft Perplexity API direkt auf
        response = await self.ai_provider.complete(request)
```

**AI Provider:** `backend/utils/perplexity_provider.py`
```python
class PerplexityProvider(AIProvider):
    async def complete(self, request: AIRequest):
        # HTTP Request zu Perplexity API
        response = await httpx.post(
            "https://api.perplexity.ai/chat/completions",
            json=payload
        )
        # ❌ KEIN MCP-Protocol!
        # ✅ Nur HTTP REST API
```

**Communication Method:**
- ❌ **NOT MCP:** Keine MCP-Integration
- ✅ **REST API:** Direkte HTTP-Requests zu Perplexity

---

### **3. Architect Agent**

**File:** `backend/agents/architect_agent.py`

**Architecture:**
```python
from backend.utils.ai_factory import AIFactory

class ArchitectAgent:
    def __init__(self):
        self.ai_provider = AIFactory.get_provider_for_agent("architect")
        # Provider = OpenAIService (NOT MCP!)

    async def execute(self, state: dict):
        # Ruft OpenAI API direkt auf
        response = await self.ai_provider.complete(request)
```

**AI Provider:** `backend/utils/openai_service.py`
```python
class OpenAIService(AIProvider):
    async def complete(self, request: AIRequest):
        # ChatOpenAI von LangChain
        response = await self.llm.ainvoke(messages)
        # ❌ KEIN MCP-Protocol!
        # ✅ LangChain OpenAI Integration (REST API)
```

**Communication Method:**
- ❌ **NOT MCP:** Keine MCP-Integration
- ✅ **LangChain:** LangChain's ChatOpenAI (nutzt OpenAI REST API)

---

### **4. ReviewFix Agent**

**File:** `backend/agents/reviewfix_agent.py`

**Architecture:**
```python
from backend.utils.ai_factory import AIFactory

class ReviewFixAgent:
    def __init__(self):
        self.ai_provider = AIFactory.get_provider_for_agent("reviewfix")
        # Provider = ClaudeCLIService (NOT MCP!)

    async def execute(self, state: dict):
        # Ruft Claude CLI via subprocess auf
        response = await self.ai_provider.complete(request)
```

**Communication Method:**
- ❌ **NOT MCP:** Gleich wie Codesmith
- ✅ **Subprocess:** Claude CLI binary

---

## 📊 **Summary: v7.0 Agent Communication**

| Agent | AI Provider | Communication Method | MCP? |
|-------|-------------|---------------------|------|
| **Codesmith** | Claude CLI | subprocess (stdin/stdout/stderr) | ❌ NO |
| **ReviewFix** | Claude CLI | subprocess (stdin/stdout/stderr) | ❌ NO |
| **Research** | Perplexity | REST API (HTTP) | ❌ NO |
| **Architect** | OpenAI | LangChain → REST API (HTTP) | ❌ NO |
| **Responder** | OpenAI | LangChain → REST API (HTTP) | ❌ NO |

**Result:** **KEINE einzige v7.0 Agent nutzt MCP!**

---

## 🔍 **Where is MCP Used? (v6.x Legacy)**

MCP wird **nur in alten v6.x Files** genutzt:

```
backend/mcp/mcp_client.py              # MCP Client (v6.x)
backend/subgraphs/*_subgraph_v6_*.py   # Alte Subgraphs (v6.x)
backend/workflow_v6_integrated.py      # Alter Workflow (v6.x)
backend/tests/test_mcp_*.py            # Tests für v6.x
```

**v7.0 nutzt MCP NICHT!** Die Supervisor-Pattern-Migration hat MCP entfernt.

---

## 💡 **Was bedeutet das für unsere Event-Streaming-Lösung?**

### **Original MCP-Solution Annahme:**
```python
# Annahme: MCP-Tools mit report_progress
from mcp.server.progress import report_progress

await report_progress(
    ctx,
    progress=0.35,
    message="🧠 think: analyzing",
    total=1.0
)
```

### **Actual Reality:**
```python
# Reality: Subprocess, kein MCP-Context
process = await asyncio.create_subprocess_exec(
    "claude", "--print", prompt,
    stdin=asyncio.subprocess.DEVNULL,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE
)
# ❌ Kein ctx, kein report_progress möglich!
```

---

## ✅ **Korrigierte Lösung: MCP-Style WITHOUT MCP Library**

**Das ist GENAU was ich in "Hybrid-Hybrid" vorgeschlagen habe!**

### **Warum meine Lösung passt:**

```python
# MCP-STYLE API (ohne MCP Library!)
async def report_progress(
    progress: float,
    message: str,
    agent: str,
    phase: str,
    total: float = 1.0
):
    """MCP-compatible API without requiring MCP library."""
    event = ProgressEvent(progress, message, total, agent, phase)
    await event_bus.emit(event)

# Usage in Agent (funktioniert mit subprocess!)
async def codesmith_execute(state: dict):
    # BEFORE subprocess call
    await report_progress(0.0, "Starting code generation", "codesmith", "think")

    # Call subprocess (Claude CLI)
    process = await asyncio.create_subprocess_exec(...)

    # AFTER subprocess call
    await report_progress(1.0, "Code generation complete", "codesmith", "result")
```

**Das funktioniert, weil:**
- ✅ Wir rufen `report_progress()` VOR/NACH subprocess auf
- ✅ Nicht IN subprocess (wo kein MCP-Context existiert)
- ✅ MCP-kompatibles Format, aber Custom-Implementation
- ✅ ContextVars für Session-Routing
- ✅ Event-Bus für Delivery

---

## 🎯 **Finale Architektur-Klarstellung**

### **v7.0 Architecture:**

```
┌─────────────────────────────────────────────────────────────┐
│                    WEBSOCKET/SSE CLIENT                     │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ Events
                            │
┌─────────────────────────────────────────────────────────────┐
│              SESSION EVENT BUS (Custom)                     │
│  • ContextVars für Session-Routing                         │
│  • MCP-Style Format (ohne MCP Library)                     │
└─────────────────────────────────────────────────────────────┘
         ▲                  ▲                  ▲
         │                  │                  │
    ┌────┴────┐      ┌──────┴──────┐    ┌─────┴──────┐
    │         │      │             │    │            │
┌───┴────┐ ┌─┴────┐ ┌┴──────────┐ │  ┌─┴──────────┐ │
│SUPERVISOR│ │RESEARCH│ │ARCHITECT│ │  │CODESMITH│ │
│ GPT-4o  │ │Perplexity│ │GPT-4o  │ │  │Claude CLI│ │
│         │ │ REST API│ │LangChain│ │  │subprocess│ │
└─────────┘ └────────┘ └──────────┘ │  └──────────┘ │
                                    │               │
                             ┌──────┴────────┐ ┌────┴──────┐
                             │REVIEWFIX      │ │RESPONDER   │
                             │Claude CLI     │ │GPT-4o      │
                             │subprocess     │ │LangChain   │
                             └───────────────┘ └────────────┘

❌ KEIN MCP-Protocol!
✅ Subprocess (Claude CLI)
✅ REST APIs (OpenAI, Perplexity)
✅ Custom Event-Bus mit MCP-Style Format
```

---

## ✅ **Fazit**

1. ❌ **v7.0 Agents nutzen KEIN MCP** - Nur v6.x Legacy-Code hat MCP
2. ✅ **Claude CLI = subprocess** - NICHT MCP-basiert
3. ✅ **Meine "Hybrid-Hybrid" Lösung ist korrekt** - MCP-Style ohne MCP Library
4. ✅ **User-Vorschlag funktioniert NICHT direkt** - Braucht Anpassung (was ich bereits vorgeschlagen habe)

**Empfehlung bleibt:** MCP-Style Hybrid (Ansatz 5) - **OHNE echtes MCP**, nur MCP-kompatibles Format!
