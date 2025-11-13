# 🏗️ Agent-spezifische LLM Architecture

**Status:** Design Phase  
**Date:** 2025-11-10  
**Approach:** Zentrales Config File (JSON) + .env für Secrets

---

## 🎯 Überblick

Jeder Agent kann **seinen eigenen LLM Provider und Model** nutzen:

```
┌─────────────────────────────────────────────────────┐
│        agent_llm_config.json (zentrales Config)     │
├─────────────────────────────────────────────────────┤
│ {                                                   │
│   "supervisor": {                                   │
│     "provider": "openai",                           │
│     "model": "gpt-4o-2024-11-20",                   │
│     "temperature": 0.4                              │
│   },                                                │
│   "codesmith": {                                    │
│     "provider": "anthropic",                        │
│     "model": "claude-sonnet-4-20250514",            │
│     "temperature": 0.2                              │
│   },                                                │
│   "architect": {                                    │
│     "provider": "anthropic",                        │
│     "model": "claude-opus-4-1",                     │
│     "temperature": 0.3                              │
│   }                                                 │
│ }                                                   │
├─────────────────────────────────────────────────────┤
│        .env (nur API Keys + Zencoder)               │
├─────────────────────────────────────────────────────┤
│ OPENAI_API_KEY=sk-...                              │
│ ANTHROPIC_API_KEY=sk-ant-...                       │
│ ZENCODER_API_KEY=zenc-... (if available)           │
│ ZENCODER_WORKSPACE=... (if available)              │
└─────────────────────────────────────────────────────┘
```

---

## 📁 File Struktur

```
backend/
├── config/
│   ├── agent_llm_config.json          # ← ZENTRALE CONFIG
│   └── agent_llm_config.schema.json   # ← Validierung
├── core/
│   ├── agent_llm_config.py            # ← Dataclass + Loader
│   ├── agent_llm_factory.py           # ← Factory per Agent
│   └── zencoder_adapter.py            # ← Zencoder Integration (if possible)
├── utils/
│   └── config_validator.py            # ← JSON Schema Validation
└── tests/
    └── test_agent_llm_*.py            # ← Unit Tests
```

---

## 📋 agent_llm_config.json

```json
{
  "version": "1.0",
  "agents": {
    "supervisor": {
      "description": "Central routing decision maker",
      "provider": "openai",
      "model": "gpt-4o-2024-11-20",
      "temperature": 0.4,
      "max_tokens": 2000,
      "timeout_seconds": 30
    },
    "codesmith": {
      "description": "Code generation from architecture",
      "provider": "anthropic",
      "model": "claude-sonnet-4-20250514",
      "temperature": 0.2,
      "max_tokens": 4000,
      "timeout_seconds": 60
    },
    "architect": {
      "description": "System design and architecture",
      "provider": "anthropic",
      "model": "claude-opus-4-1",
      "temperature": 0.3,
      "max_tokens": 3000,
      "timeout_seconds": 45
    },
    "research": {
      "description": "Context gathering and research",
      "provider": "anthropic",
      "model": "claude-haiku-4",
      "temperature": 0.7,
      "max_tokens": 1000,
      "timeout_seconds": 20
    },
    "reviewfix": {
      "description": "Code review and bug fixing",
      "provider": "openai",
      "model": "gpt-4o-mini",
      "temperature": 0.2,
      "max_tokens": 2000,
      "timeout_seconds": 30
    },
    "responder": {
      "description": "Final response formatting",
      "provider": "openai",
      "model": "gpt-4o-2024-11-20",
      "temperature": 0.5,
      "max_tokens": 1500,
      "timeout_seconds": 15
    }
  },
  "defaults": {
    "temperature": 0.4,
    "max_tokens": 2000,
    "timeout_seconds": 30
  }
}
```

---

## 🔑 .env File (nur Secrets!)

```env
# OpenAI
OPENAI_API_KEY=sk-proj-xxx...

# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-v0-xxx...

# Zencoder (OPTIONAL - wenn CLI existiert)
ZENCODER_API_KEY=zenc_xxx...
ZENCODER_WORKSPACE=workspace_id

# Logging / Debug
DEBUG_AGENT_LLM=true
LOG_LEVEL=INFO
```

---

## 💻 Python Implementierung

### **1. agent_llm_config.py**

```python
# backend/core/agent_llm_config.py
from dataclasses import dataclass
from typing import Optional
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class AgentLLMSettings:
    """LLM Settings für einen Agent"""
    description: str
    provider: str              # "openai", "anthropic", "zencoder"
    model: str                 # "gpt-4o-2024-11-20", "claude-sonnet-...", etc
    temperature: float
    max_tokens: int
    timeout_seconds: int

class AgentLLMConfig:
    """Zentrale Config für alle Agent LLMs"""
    
    _instance: Optional["AgentLLMConfig"] = None
    _config: dict = {}
    
    def __init__(self):
        """Load config from JSON file"""
        config_path = Path(__file__).parent.parent / "config" / "agent_llm_config.json"
        
        logger.info(f"🤖 Loading agent LLM config from: {config_path}")
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"❌ agent_llm_config.json not found at {config_path}\n"
                f"Create it from agent_llm_config.example.json"
            )
        
        try:
            with open(config_path) as f:
                self._config = json.load(f)
            
            logger.info(f"✅ Loaded config for {len(self._config['agents'])} agents")
            
            # Log each agent's LLM
            for agent_name, settings in self._config['agents'].items():
                logger.info(
                    f"   {agent_name:15} → {settings['provider']:12} / {settings['model']}"
                )
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in agent_llm_config.json: {e}")
            raise
        except KeyError as e:
            logger.error(f"❌ Missing required key in config: {e}")
            raise
    
    @classmethod
    def get_instance(cls) -> "AgentLLMConfig":
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = AgentLLMConfig()
        return cls._instance
    
    def get_agent_settings(self, agent_name: str) -> AgentLLMSettings:
        """Get LLM settings for specific agent"""
        
        logger.debug(f"📋 Getting LLM settings for agent: {agent_name}")
        
        if agent_name not in self._config['agents']:
            available = list(self._config['agents'].keys())
            logger.error(f"❌ Agent '{agent_name}' not in config")
            logger.error(f"   Available agents: {', '.join(available)}")
            raise ValueError(f"Unknown agent: {agent_name}")
        
        agent_config = self._config['agents'][agent_name]
        
        settings = AgentLLMSettings(
            description=agent_config['description'],
            provider=agent_config['provider'],
            model=agent_config['model'],
            temperature=agent_config['temperature'],
            max_tokens=agent_config['max_tokens'],
            timeout_seconds=agent_config['timeout_seconds']
        )
        
        logger.info(
            f"✅ Agent '{agent_name}' → {settings.provider}/{settings.model}"
        )
        
        return settings
    
    def list_agents(self) -> list[str]:
        """List all configured agents"""
        return list(self._config['agents'].keys())
```

### **2. agent_llm_factory.py**

```python
# backend/core/agent_llm_factory.py
from typing import Protocol
import logging
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from backend.core.agent_llm_config import AgentLLMConfig, AgentLLMSettings

logger = logging.getLogger(__name__)

class LLMProvider(Protocol):
    """Interface für LLM Providers"""
    async def generate(self, prompt: str) -> str:
        ...
    async def generate_with_tools(self, prompt: str, tools: list) -> dict:
        ...

class OpenAIProvider:
    """OpenAI LLM Provider"""
    
    def __init__(self, settings: AgentLLMSettings):
        self.settings = settings
        
        logger.info(f"🤖 Initializing OpenAI Provider")
        logger.info(f"   Model: {settings.model}")
        logger.info(f"   Temperature: {settings.temperature}")
        logger.info(f"   Max Tokens: {settings.max_tokens}")
        
        self.llm = ChatOpenAI(
            model=settings.model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens
        )
        
        logger.info(f"✅ OpenAI Provider ready")

class AnthropicProvider:
    """Anthropic (Claude) LLM Provider"""
    
    def __init__(self, settings: AgentLLMSettings):
        self.settings = settings
        
        logger.info(f"🤖 Initializing Anthropic Provider")
        logger.info(f"   Model: {settings.model}")
        logger.info(f"   Temperature: {settings.temperature}")
        logger.info(f"   Max Tokens: {settings.max_tokens}")
        
        self.llm = ChatAnthropic(
            model=settings.model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens
        )
        
        logger.info(f"✅ Anthropic Provider ready")

class ZencoderProvider:
    """Zencoder CLI Provider (if available)"""
    
    def __init__(self, settings: AgentLLMSettings):
        import subprocess
        
        self.settings = settings
        self.api_key = os.getenv("ZENCODER_API_KEY")
        
        logger.info(f"🤖 Initializing Zencoder Provider")
        logger.info(f"   Model: {settings.model}")
        
        # Verify Zencoder CLI exists
        try:
            result = subprocess.run(
                ["zencoder", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                raise RuntimeError("zencoder CLI returned error")
            
            logger.info(f"   CLI Version: {result.stdout.strip()}")
            logger.info(f"✅ Zencoder Provider ready")
        
        except FileNotFoundError:
            logger.error(f"❌ zencoder CLI not found in PATH")
            logger.error(f"   Install: brew install zencoder")
            raise

class AgentLLMFactory:
    """Factory für Agent-spezifische LLMs"""
    
    @staticmethod
    def get_llm_for_agent(agent_name: str):
        """Get LLM for specific agent"""
        
        config = AgentLLMConfig.get_instance()
        settings = config.get_agent_settings(agent_name)
        
        logger.info(f"🏭 Creating LLM for agent: {agent_name}")
        
        if settings.provider == "openai":
            return OpenAIProvider(settings)
        
        elif settings.provider == "anthropic":
            return AnthropicProvider(settings)
        
        elif settings.provider == "zencoder":
            return ZencoderProvider(settings)
        
        else:
            raise ValueError(f"Unknown provider: {settings.provider}")
```

### **3. Usage in supervisor_mcp.py**

```python
# backend/core/supervisor_mcp.py
from backend.core.agent_llm_factory import AgentLLMFactory

class SupervisorMCP:
    def __init__(self, ...):
        # Instead of:
        # self.llm = ChatOpenAI(model="gpt-4o-2024-11-20")
        
        # Now use:
        self.llm = AgentLLMFactory.get_llm_for_agent("supervisor")
        
        logger.info("✅ SupervisorMCP initialized with agent-specific LLM")
```

---

## 🧪 Tests

```python
# backend/tests/test_agent_llm_config.py
import pytest
from backend.core.agent_llm_config import AgentLLMConfig

def test_load_config():
    """Test loading agent LLM config"""
    config = AgentLLMConfig.get_instance()
    assert config is not None
    logger.info(f"✅ Config loaded with {len(config.list_agents())} agents")

def test_supervisor_settings():
    """Test supervisor LLM settings"""
    config = AgentLLMConfig.get_instance()
    settings = config.get_agent_settings("supervisor")
    
    assert settings.provider == "openai"
    assert settings.model == "gpt-4o-2024-11-20"
    assert settings.temperature == 0.4
    logger.info(f"✅ Supervisor settings correct")

def test_codesmith_settings():
    """Test codesmith LLM settings"""
    config = AgentLLMConfig.get_instance()
    settings = config.get_agent_settings("codesmith")
    
    assert settings.provider == "anthropic"
    assert settings.model == "claude-sonnet-4-20250514"
    logger.info(f"✅ Codesmith settings correct")

def test_factory_creates_openai():
    """Test factory creates OpenAI provider"""
    llm = AgentLLMFactory.get_llm_for_agent("supervisor")
    assert llm is not None
    assert isinstance(llm, OpenAIProvider)
    logger.info(f"✅ Factory created OpenAI provider")

def test_factory_creates_anthropic():
    """Test factory creates Anthropic provider"""
    llm = AgentLLMFactory.get_llm_for_agent("codesmith")
    assert llm is not None
    assert isinstance(llm, AnthropicProvider)
    logger.info(f"✅ Factory created Anthropic provider")

def test_invalid_agent():
    """Test error handling for unknown agent"""
    config = AgentLLMConfig.get_instance()
    
    with pytest.raises(ValueError):
        config.get_agent_settings("nonexistent_agent")
    
    logger.info(f"✅ Properly rejects unknown agent")
```

---

## 📊 Logging Output

Wenn das System startet:

```
🤖 Loading agent LLM config from: /Users/.../backend/config/agent_llm_config.json
✅ Loaded config for 6 agents
   supervisor       → openai       / gpt-4o-2024-11-20
   codesmith        → anthropic    / claude-sonnet-4-20250514
   architect        → anthropic    / claude-opus-4-1
   research         → anthropic    / claude-haiku-4
   reviewfix        → openai       / gpt-4o-mini
   responder        → openai       / gpt-4o-2024-11-20

🤖 Initializing Supervisor LLM
🏭 Creating LLM for agent: supervisor
🤖 Initializing OpenAI Provider
   Model: gpt-4o-2024-11-20
   Temperature: 0.4
   Max Tokens: 2000
✅ OpenAI Provider ready

🤖 Initializing Codesmith LLM
🏭 Creating LLM for agent: codesmith
🤖 Initializing Anthropic Provider
   Model: claude-sonnet-4-20250514
   Temperature: 0.2
   Max Tokens: 4000
✅ Anthropic Provider ready

📤 Calling supervisor with new request
📤 Calling codesmith with design requirements
✅ Codesmith responded in 2.34s
```

---

## 🚀 Implementation Steps

### **Phase 1: Core Config System (2h)**
- [ ] Create `backend/config/agent_llm_config.json`
- [ ] Create `backend/core/agent_llm_config.py`
- [ ] Create `backend/core/agent_llm_factory.py`
- [ ] Create `backend/tests/test_agent_llm_*.py`
- [ ] Test: `pytest backend/tests/test_agent_llm_*.py -v`

### **Phase 2: Integration with Agents (2h)**
- [ ] Update `backend/core/supervisor_mcp.py`
- [ ] Update `mcp_servers/codesmith_agent_server.py`
- [ ] Update `mcp_servers/architect_agent_server.py`
- [ ] Test: `python start_server.py` (check logs)

### **Phase 3: Zencoder Research & Integration (conditional)**
- [ ] Research: `which zencoder && zencoder --version`
- [ ] If YES: Create `backend/core/zencoder_adapter.py`
- [ ] If NO: Document in ARCHITECTURE.md

### **Phase 4: Documentation & Testing (1h)**
- [ ] Update LANGGRAPH_ARCHITECTURE.md
- [ ] Update backend/CLAUDE.md
- [ ] Run E2E tests

---

## ✅ Advantages of This Approach

| Aspekt | Vorteil |
|--------|---------|
| **Einfachheit** | JSON Config ist leicht zu verstehen |
| **Flexibilität** | Jeder Agent hat eigene LLM-Wahl |
| **Testing** | A/B Test verschiedene Models |
| **Secrets** | API Keys nur in .env, nicht in JSON |
| **Logging** | Clear visibility welcher Agent welchen LLM nutzt |
| **Maintenance** | Zentral in einem File, nicht über Code verteilt |
| **Zencoder Ready** | Einfach "zencoder" hinzufügen wenn CLI existiert |

---

**Last Updated:** 2025-11-10  
**Status:** Architecture Design Complete  
**Next:** Implementation Phase 1
