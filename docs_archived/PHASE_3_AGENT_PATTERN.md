# 🔄 Phase 3: Agent Integration Pattern (Reusable)

**Das Muster, das ALLE 6 Agents folgen sollen**

---

## Das Pattern (5 Schritte)

### Schritt 1: Imports aktualisieren

```python
# ENTFERNEN
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

# HINZUFÜGEN
from backend.core.llm_factory import AgentLLMFactory
from backend.core.llm_config import AgentLLMConfigManager
from pathlib import Path
import logging

logger = logging.getLogger("agent.your_agent_name")
```

---

### Schritt 2: __init__() anpassen

```python
class YourAgent:
    # VORHER
    def __init__(self, model: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model, temperature=0.4)
    
    # NACHHER
    def __init__(self, agent_name: str = "codesmith"):
        """
        Initialize agent with Factory-based LLM.
        
        Args:
            agent_name: Name in agent_llm_config.json
        """
        logger.info(f"🤖 Initializing {agent_name}...")
        
        # Initialize config (once per app startup)
        config_path = Path("backend/config/agent_llm_config.json")
        AgentLLMConfigManager.initialize(config_path)
        
        # Get LLM provider from factory
        self.llm_provider = AgentLLMFactory.get_provider_for_agent(agent_name)
        
        # Log configuration
        logger.info(f"   ✅ Provider: {self.llm_provider.get_provider_name()}")
        logger.info(f"   ✅ Model: {self.llm_provider.model}")
        logger.info(f"   ✅ Temperature: {self.llm_provider.temperature}")
        logger.info(f"   ✅ Max tokens: {self.llm_provider.max_tokens}")
        logger.info(f"   ✅ Timeout: {self.llm_provider.timeout_seconds}s")
        
        self.agent_name = agent_name
        logger.info(f"✅ {agent_name} initialized")
```

---

### Schritt 3: LLM-Aufrufe ersetzen

#### 3a: Einfache Text-Generierung

```python
# VORHER
async def generate_code(self, prompt: str) -> str:
    response = self.llm.invoke(prompt)
    return response.content

# NACHHER
async def generate_code(self, prompt: str) -> str:
    logger.info(f"📤 Generating code...")
    logger.debug(f"   Prompt: {prompt[:100]}...")
    
    try:
        response = await self.llm_provider.generate_text_with_retries(
            prompt=prompt,
            system_prompt="You are an expert code generator",
            max_retries=3
        )
        
        logger.info(f"✅ Code generated")
        logger.info(f"   Tokens: {response.total_tokens}")
        logger.info(f"   Time: {response.response_time_ms}ms")
        logger.debug(f"   Content: {response.content[:200]}...")
        
        return response.content
        
    except Exception as e:
        logger.error(f"❌ Code generation failed: {e}")
        raise
```

#### 3b: Strukturierte Outputs (Entscheidungen, JSON)

```python
from pydantic import BaseModel

class CodeReview(BaseModel):
    quality: int  # 1-10
    issues: list[str]
    recommendations: str
    approve: bool

# VORHER
async def review_code(self, code: str) -> dict:
    response = self.llm.with_structured_output(CodeReview).invoke(code)
    return response.dict()

# NACHHER
async def review_code(self, code: str) -> CodeReview:
    logger.info(f"🔍 Reviewing code...")
    
    try:
        review = await self.llm_provider.generate_structured_output(
            prompt=f"Review this code:\n{code}",
            output_model=CodeReview,
            system_prompt="You are a code reviewer. Respond with JSON.",
            max_retries=3
        )
        
        logger.info(f"✅ Review complete")
        logger.info(f"   Quality: {review.quality}/10")
        logger.info(f"   Issues: {len(review.issues)}")
        logger.info(f"   Approve: {review.approve}")
        
        return review
        
    except ValueError as e:
        logger.error(f"❌ Review parsing failed: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Review generation failed: {e}")
        raise
```

---

### Schritt 4: Error-Handling standardisieren

```python
async def some_agent_method(self):
    """Template für alle LLM-Aufrufe."""
    
    logger.info(f"📤 Starting {self.agent_name} operation...")
    
    try:
        # Call LLM via provider
        result = await self.llm_provider.generate_text_with_retries(...)
        logger.info(f"✅ Operation successful")
        return result
        
    except asyncio.TimeoutError:
        logger.error(f"❌ LLM call timed out")
        logger.error(f"   Timeout: {self.llm_provider.timeout_seconds}s")
        raise
        
    except ValueError as e:
        logger.error(f"❌ Invalid response format: {e}")
        raise
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {type(e).__name__}")
        logger.error(f"   Message: {str(e)}")
        logger.debug(f"   Full traceback:", exc_info=True)
        raise
```

---

### Schritt 5: Konfiguration in agent_llm_config.json

```json
{
  "agents": {
    "supervisor": {
      "provider": "openai",
      "model": "gpt-4o-2024-11-20",
      "temperature": 0.3,
      "max_tokens": 1500,
      "timeout_seconds": 30
    },
    "codesmith": {
      "provider": "anthropic",
      "model": "claude-3-5-sonnet-20241022",
      "temperature": 0.2,
      "max_tokens": 4000,
      "timeout_seconds": 60
    },
    "architect": {
      "provider": "anthropic",
      "model": "claude-opus-4-1",
      "temperature": 0.3,
      "max_tokens": 8000,
      "timeout_seconds": 60
    },
    "research": {
      "provider": "anthropic",
      "model": "claude-haiku-4",
      "temperature": 0.7,
      "max_tokens": 2000,
      "timeout_seconds": 45
    },
    "reviewfix": {
      "provider": "openai",
      "model": "gpt-4o-mini",
      "temperature": 0.2,
      "max_tokens": 2000,
      "timeout_seconds": 30
    },
    "responder": {
      "provider": "openai",
      "model": "gpt-4o-2024-11-20",
      "temperature": 0.5,
      "max_tokens": 1000,
      "timeout_seconds": 30
    }
  }
}
```

---

## Das Pattern Zusammengefasst

```
┌─────────────────────────────────────────────────────────────┐
│                    PHASE 3 PATTERN                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. IMPORTS                                                │
│     ChatOpenAI/ChatAnthropic ❌                            │
│     → AgentLLMFactory ✅                                   │
│                                                             │
│  2. __init__()                                             │
│     self.llm = ChatOpenAI(...) ❌                          │
│     → self.llm_provider = Factory.get_provider(...) ✅     │
│     → Logging: Provider + Model + Temp ✅                 │
│                                                             │
│  3. LLM CALLS (Simple)                                    │
│     self.llm.invoke(...) ❌                               │
│     → await self.llm_provider.generate_text_with_retries(..) │
│                                                             │
│  3. LLM CALLS (Structured)                                │
│     self.llm.with_structured_output(...).invoke(...) ❌    │
│     → await self.llm_provider.generate_structured_output(...) │
│                                                             │
│  4. ERROR HANDLING                                         │
│     Standardisiert (asyncio, ValueError, Exception) ✅     │
│                                                             │
│  5. CONFIG                                                 │
│     Alle Einstellungen in agent_llm_config.json ✅         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Logging Pattern

### ✅ Was JEDER Agent loggen soll

```python
# 1. INIT
logger.info(f"🤖 Initializing {agent_name}...")
logger.info(f"   ✅ Provider: {provider_name}")
logger.info(f"   ✅ Model: {model}")

# 2. REQUEST
logger.info(f"📤 Calling LLM for {operation}...")
logger.debug(f"   Prompt: {prompt[:100]}...")

# 3. RESPONSE
logger.info(f"✅ {operation} complete")
logger.info(f"   Tokens: {response.total_tokens}")
logger.info(f"   Time: {response.response_time_ms}ms")

# 4. ERROR
logger.error(f"❌ {operation} failed: {error_type}")
logger.error(f"   Message: {error_msg}")
logger.debug(f"   Details:", exc_info=True)
```

### ❌ Was NICHT geloggt werden soll

```python
logger.info(f"API Key: {api_key}")  # ❌ SECRETS!
print(f"DEBUG: {var}")               # ❌ Use logger.debug()
logger.info("...")                   # ❌ Silent failures!
```

---

## Konkrete Beispiele für die 6 Agents

### 1️⃣ Supervisor (bereits dokumentiert)
```
Datei: backend/core/supervisor_mcp.py
Pattern: Text + Structured Output (SupervisorDecision)
Config: openai:gpt-4o, temp=0.3
```

### 2️⃣ Codesmith
```
Datei: backend/agents/specialized/codesmith_agent.py
Pattern: Structured Output (CodeQualityCheck, GeneratedCode)
Config: anthropic:claude-sonnet, temp=0.2
```

### 3️⃣ Architect
```
Datei: backend/agents/specialized/architect_agent.py
Pattern: Structured Output (ArchitectureDecision)
Config: anthropic:claude-opus, temp=0.3
```

### 4️⃣ Research
```
Datei: backend/agents/specialized/research_agent.py
Pattern: Simple Text (Web-Recherche)
Config: anthropic:claude-haiku, temp=0.7
```

### 5️⃣ ReviewFix
```
Datei: backend/agents/specialized/reviewer_gpt_agent.py
Pattern: Structured Output (ReviewResult)
Config: openai:gpt-4o-mini, temp=0.2
```

### 6️⃣ Responder
```
Datei: [needs to be found]
Pattern: Simple Text (User-Response)
Config: openai:gpt-4o, temp=0.5
```

---

## Checklist pro Agent

```python
✅ Step 1: Imports aktualisiert?
   - ChatOpenAI/ChatAnthropic ENTFERNT?
   - AgentLLMFactory + AgentLLMConfigManager HINZUGEFÜGT?

✅ Step 2: __init__() angepasst?
   - Config laden via AgentLLMConfigManager?
   - Provider via Factory?
   - Logging für Provider + Model + Temp?

✅ Step 3: LLM-Aufrufe ersetzt?
   - generate_text_with_retries() für einfache Text?
   - generate_structured_output() für strukturierte?
   - Alle async/await?

✅ Step 4: Error-Handling standardisiert?
   - asyncio.TimeoutError?
   - ValueError (parsing)?
   - Generic Exception mit full traceback?

✅ Step 5: Config in JSON?
   - Agent-Name richtig geschrieben?
   - Provider + Model korrekt?
   - Temperature/Tokens sensible Defaults?

✅ Step 6: Tests?
   - Unit test: __init__() nutzt Factory?
   - Integration test: LLM-Call funktioniert?
   - E2E test: Agent funktioniert im Workflow?
   - Logging test: 🤖📤✅❌ visible?
```

---

## Timing pro Agent

```
Pro Agent (durchschnittlich):
- Imports + __init__(): 15 min
- LLM-Aufrufe ersetzen: 20 min
- Error-Handling: 10 min
- Config JSON: 5 min
- Tests schreiben: 30 min
- Verifizieren + Logging: 20 min
─────────────────────────────
Total: ~100 min (1.5-2 Stunden) pro Agent

Für alle 6 Agents:
- Supervisor: 2h (komplexer mit structured output)
- Codesmith: 1.5h
- Architect: 1.5h
- Research: 1h (einfacher, nur Text)
- ReviewFix: 1.5h
- Responder: 1h (einfacher)
─────────────────────────────
Total: ~9 Stunden für alle Agents
```

---

## Success Criteria (pro Agent)

```
✅ Code compiles ohne Errors
✅ Imports sind korrekt (kein CircularImport)
✅ __init__() zeigt Logging mit 🤖, ✅
✅ LLM-Calls zeigen 📤 und ✅ mit Tokens + Time
✅ Errors zeigen ❌ mit aussagekräftiger Meldung
✅ Config in JSON, nicht hardcoded
✅ Alle Tests ✅ passing
✅ Keine API-Calls in Tests (mock only)
✅ Keine Secrets in Logs
✅ E2E-Test zeigt korrekte Reihenfolge
```

---

## Reihenfolge der Implementation

```
DAY 1:
  🔜 supervisor_mcp.py (2h) - CORE
  🔜 Tests schreiben (1h)
  🔜 Verify + Logging (0.5h)

DAY 2:
  🔜 codesmith_agent.py (1.5h)
  🔜 architect_agent.py (1.5h)
  🔜 Tests (1h)

DAY 3:
  🔜 research_agent.py (1h)
  🔜 reviewfix_agent.py (1.5h)
  🔜 responder_agent.py (1h)
  🔜 Tests (1h)

DAY 4:
  🔜 Full E2E Testing
  🔜 Performance Benchmarks
  🔜 Documentation Update
  🔜 Final Verification
```

---

## Questions? 

Falls bei irgendeinem Agent unklar, was zu tun ist:
1. Lese diese Datei + den Agent-File
2. Lese PHASE_3_SUPERVISOR_UPDATE_GUIDE.md (concrete example)
3. Vergleiche mit supervisor_mcp.py (updated version)
4. Folge der Checklist

**Das Pattern ist konsistent für ALLE Agents!**

