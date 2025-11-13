
# 🎯 Guidelines for KI AutoAgent Development (v7.0 + Phase 3)

**For AI Developers:** This guide explains what you need to know when modifying the KI AutoAgent backend.

**Latest Update:** Phase 3b Ultra-Logging Framework implemented (2025-11-10)
- ✅ Token tracking per agent
- ✅ Memory monitoring (psutil)
- ✅ Cost calculation (all providers)
- ✅ Structured metrics export
- See: `PHASE_3B_ULTRA_LOGGING_COMPLETE.md`

---

## 🚨 CRITICAL: ARCHITECTURE RULES

**Every change to the system must respect these rules:**

1. **Agents are MCP Servers ONLY**
   - ❌ DON'T: Direct Python imports of agent classes
   - ✅ DO: Call agents via `mcp.call("agent_name", "tool", {...})`

2. **LLM Configuration is Provider-Agnostic**
   - ❌ DON'T: Hard-code model names in agent code
   - ✅ DO: Use `LLMFactory.get_provider()` or `LLMConfig`
   - See: `LANGGRAPH_ARCHITECTURE.md` → "LLM Configuration & Flexibility"

3. **All Communication is JSON-RPC via MCP**
   - ❌ DON'T: Direct subprocess calls
   - ✅ DO: Use MCPManager for all agent communication

4. **Frontend Only Talks to Python Backend**
   - ❌ DON'T: Direct Python subprocess calls from TypeScript
   - ✅ DO: Send WebSocket messages to FastAPI

**Violations of these rules cause:**
- Duplicate code
- Unmaintainable architecture  
- Race conditions
- Silent failures

---

## 🔍 STDOUT Requirements (Debugging)

**The AI Agent MUST have extensive stdout output to understand what's happening.**

### What to Log (Minimum)

```python
# INIT: Show configuration when starting
logger.info(f"🤖 Supervisor initialized")
logger.info(f"   LLM Provider: {provider}")
logger.info(f"   Model: {model}")
logger.info(f"   Temperature: {temperature}")

# REQUEST: Show what's being requested
logger.info(f"📤 Calling {agent_name} with tool: {tool_name}")
logger.debug(f"   Parameters: {json.dumps(params, indent=2)}")

# PROGRESS: Show progress during execution
logger.info(f"⏳ Waiting for {agent_name} response...")
await self.send_progress(0.5, f"Processing in {agent_name}...")

# RESPONSE: Show what was returned
logger.info(f"✅ {agent_name} returned in {elapsed_ms}ms")
logger.debug(f"   Response: {json.dumps(response, indent=2)[:200]}...")

# ERROR: Show errors with actionable info
logger.error(f"❌ {agent_name} failed: {error_msg}")
logger.debug(f"   Error details: {traceback.format_exc()}")
```

### What NOT to Log

```python
# ❌ DON'T: Silent failures
try:
    result = await mcp.call(...)
except Exception:
    pass  # Silently fails!

# ❌ DON'T: Debug output to stdout
print(f"DEBUG: {some_var}")  # Use logger.debug() instead

# ❌ DON'T: Sensitive data in logs
logger.info(f"API Key: {api_key}")  # NEVER log secrets!
```

---

## 📋 Code Changes Checklist

Before committing any changes:

### For Agent/LLM Changes
- [ ] Read `LANGGRAPH_ARCHITECTURE.md` → "LLM Configuration & Flexibility"
- [ ] Read `PYTHON_BEST_PRACTICES.md` → "LLM Provider Abstraction Patterns"
- [ ] LLM model is NOT hard-coded
- [ ] LLM provider is configured via environment variable or factory
- [ ] Logging shows which LLM provider/model is being used
- [ ] Error handling for API key missing (helpful error message)
- [ ] Error handling for rate limits (retry logic)
- [ ] Tested with at least 2 different providers

### For MCP Server Changes
- [ ] Implements proper error handling
- [ ] Sends progress notifications via `$/progress`
- [ ] Logs all major operations to stdout
- [ ] Has timeout handling for long operations
- [ ] Includes try/catch with meaningful error messages
- [ ] Tested via `mcp.call()` from supervisor_node

### For Workflow Changes
- [ ] Command objects are returned (not direct state mutation)
- [ ] State updates use Annotated with Reducer for concurrent fields
- [ ] Error states are handled (fallback routing)
- [ ] Progress callbacks show workflow progress
- [ ] Tested with E2E test suite

### For Configuration Changes
- [ ] Environment variables documented in `.env.example`
- [ ] Defaults are sensible (should work without env vars)
- [ ] Configuration is logged on startup
- [ ] No hard-coded values for different environments

---

## 🧪 Testing Workflow

When implementing new features:

1. **Unit Test** - Test function in isolation
   ```bash
   pytest backend/tests/test_my_feature.py -v
   ```

2. **Integration Test** - Test MCP communication
   ```bash
   pytest backend/tests/test_mcp_integration.py -v
   ```

3. **E2E Test** - Test full workflow
   ```bash
   python start_server.py
   # In another terminal:
   python backend/tests/e2e_test.py
   ```

4. **Manual Test** - Test via WebSocket client
   ```bash
   # Start server
   python start_server.py
   
   # In another terminal, use wscat or similar
   wscat -c ws://localhost:8002/ws/chat
   ```

---

## 🐛 Debugging Workflow

### Problem: Agent call failing

1. **Check logs for error message**
   ```bash
   # Server logs show exactly what failed
   tail -f ~/.ki_autoagent/logs/server.log
   ```

2. **Enable debug logging**
   ```python
   # In your code
   logger.setLevel(logging.DEBUG)
   logger.debug(f"Detailed info: {variable}")
   ```

3. **Check MCP communication**
   ```bash
   # Verify agent server is running
   ps aux | grep "python mcp_servers"
   
   # Check if MCP server is listening
   lsof -i :PORT
   ```

4. **Simulate the call locally**
   ```python
   # backend/tests/test_debug.py
   import asyncio
   from backend.utils.mcp_manager import get_mcp_manager
   
   async def test_agent_call():
       mcp = get_mcp_manager()
       result = await mcp.call("agent_name", "tool", {...})
       print(json.dumps(result, indent=2))
   
   asyncio.run(test_agent_call())
   ```

---

## 📚 Key Documentation

Read these before making changes:

1. **LANGGRAPH_ARCHITECTURE.md**
   - How workflow routing works
   - Reducer Pattern for concurrent state updates
   - LLM Configuration & Flexibility section

2. **PYTHON_BEST_PRACTICES.md**
   - Python 3.13+ style requirements
   - LLM Provider Abstraction Patterns
   - Error handling best practices

3. **STARTUP_REQUIREMENTS.md**
   - 5 critical startup checks
   - Why direct execution doesn't work
   - Port management and cleanup

4. **PROGRESS_AND_WEBSOCKET_EVENTS.md**
   - How progress notifications flow
   - WebSocket event types
   - Real-time UI updates

---

## 🔗 Important Files

### Core Files (Don't break these!)
- `backend/api/server_v7_mcp.py` - FastAPI server (1021 lines)
- `backend/workflow_v7_mcp.py` - LangGraph workflow (1119 lines)
- `backend/core/supervisor_mcp.py` - Supervisor agent (~900 lines)
- `backend/utils/mcp_manager.py` - MCP client manager (745 lines)

### MCP Servers
- `mcp_servers/*/` - Individual agent servers
- Each server is a separate process
- Communication via JSON-RPC

### Configuration
- `config/config/agent-models.json` - (Legacy, v6.x)
- `.env.example` - Environment variables template
- Use `LLMFactory.get_provider()` for new LLM support

---

## ⚠️ Common Mistakes

### 1. Logging without context
```python
# ❌ BAD
logger.info("Done")

# ✅ GOOD
logger.info(f"✅ Completed {task_name} in {elapsed_ms}ms")
```

### 2. Hard-coded models
```python
# ❌ BAD
self.llm = ChatOpenAI(model="gpt-4o-2024-11-20")

# ✅ GOOD
llm = LLMFactory.get_provider(
    provider=os.getenv("LLM_PROVIDER", "openai"),
    model=os.getenv("LLM_MODEL", "gpt-4o-2024-11-20")
)
```

### 3. Missing error handling
```python
# ❌ BAD
result = await mcp.call("agent", "tool", {})

# ✅ GOOD
try:
    result = await mcp.call("agent", "tool", {})
except MCPConnectionError as e:
    logger.error(f"❌ Agent connection failed: {e}")
    raise
except MCPToolError as e:
    logger.error(f"❌ Agent tool error: {e}")
    raise
```

### 4. Silent failures
```python
# ❌ BAD
try:
    risky_operation()
except Exception:
    pass

# ✅ GOOD
try:
    risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise
```

---

## 🚀 Next Steps

1. **Read the Core Documentation** (1 hour)
   - LANGGRAPH_ARCHITECTURE.md
   - PYTHON_BEST_PRACTICES.md

2. **Understand MCP Communication** (1 hour)
   - `backend/utils/mcp_manager.py`
   - `mcp_servers/research_agent_server.py` (smallest example)

3. **Make Small Changes First** (2 hours)
   - Add logging to existing functions
   - Update error messages
   - Add debug output

4. **Implement Major Feature** (varies)
   - Follow all guidelines
   - Write unit tests
   - Run E2E tests
   - Update documentation

---

## 📋 AI DEVELOPER INSTRUCTIONS (v7.0 → v7.1+)

**These are YOUR instructions. Follow them strictly!**

### Core Principles

1. **Always Read Documentation First**
   - Before ANY code change: `cat LANGGRAPH_ARCHITECTURE.md`
   - Before ANY LLM change: `cat PYTHON_BEST_PRACTICES.md` → LLM Patterns
   - Before ANY MCP change: `cat backend/CLAUDE.md` (this file)

2. **Extensive STDOUT Logging (NON-NEGOTIABLE)**
   ```python
   # EVERY function must log:
   # 1. INIT: What config is being used
   # 2. REQUEST: What's being requested (with parameters summary)
   # 3. PROGRESS: What's happening right now
   # 4. RESPONSE: What was returned (first 200 chars)
   # 5. ERROR: What failed + WHY + HOW TO FIX
   
   logger.info(f"🤖 Starting operation")
   logger.info(f"   Config: provider={provider}, model={model}")
   logger.debug(f"   Full params: {json.dumps(params, indent=2)[:500]}")
   logger.info(f"⏳ Waiting for response...")
   logger.info(f"✅ Completed in {elapsed_ms}ms")
   ```

3. **Test in Simulation First (HITL: Human-In-The-Loop)**
   ```
   Step 1: Write small function (< 20 lines)
   Step 2: Test in isolation with mock data
   Step 3: Test with real dependencies
   Step 4: Test in workflow
   Step 5: Run E2E test
   Step 6: Only then merge
   ```

4. **Never Make Assumptions - Ask When Unclear (HITL)**
   - If you don't understand something → Ask user
   - If config is ambiguous → Ask user
   - If behavior is unclear → Ask user
   - Use `zencoder-server__ask_questions()` tool

5. **Update Documentation AFTER Every Action**
   - Code changed? → Update LANGGRAPH_ARCHITECTURE.md
   - LLM config changed? → Update PYTHON_BEST_PRACTICES.md
   - MCP Server added? → Update this file
   - E2E test passed? → Update test results
   - Error found? → Document in TROUBLESHOOTING.md (if needed)

6. **Debug Log Everything (Permanent Analysis)**
   ```python
   import time
   start_time = time.time()
   
   logger.info(f"📤 Calling LLM...")
   logger.debug(f"   Prompt length: {len(prompt)}")
   logger.debug(f"   Provider: {provider}")
   
   try:
       result = await llm.generate(prompt)
       elapsed = time.time() - start_time
       logger.info(f"✅ LLM responded in {elapsed:.2f}s")
       logger.debug(f"   Response length: {len(result)}")
       logger.debug(f"   First 200 chars: {result[:200]}")
   except Exception as e:
       elapsed = time.time() - start_time
       logger.error(f"❌ LLM failed after {elapsed:.2f}s")
       logger.error(f"   Error type: {type(e).__name__}")
       logger.error(f"   Error message: {str(e)}")
       logger.debug(f"   Full traceback:\n{traceback.format_exc()}")
       raise
   ```

7. **Minimal Functions, Maximum Testing**
   ```
   ❌ DON'T: One giant 100-line function
   ✅ DO: 5 small 15-20 line functions with unit tests
   
   Each function:
   - Does ONE thing
   - Has clear inputs/outputs
   - Has error handling
   - Logs everything
   - Has a unit test
   ```

8. **Python 3.13.8+ Only**
   ```python
   # ✅ Use native type unions
   def process(data: str | list) -> dict | None:
       pass
   
   # ❌ DON'T use old style
   from typing import Union, Optional
   def process(data: Union[str, list]) -> Optional[dict]:
       pass
   ```

---

### Implementation Checklist (v7.1: Zencoder Support)

**Current Goal:** Add Zencoder as flexible LLM provider (Approach 2)

**Phase 1: Research & Setup (2h)**
- [ ] Research Zencoder Python SDK (does it exist?)
- [ ] Create `AI_AGENT_IMPLEMENTATION_PLAN.md` with findings
- [ ] Decision: Use official SDK or create custom HTTP wrapper?
- [ ] Update `requirements.txt` with zencoder dependency
- [ ] Document in backend/CLAUDE.md

**Phase 2: Core LLMFactory Implementation (3h)**
- [ ] Create `backend/core/llm_factory.py`
  - [ ] Abstract `LLMProvider` base class
  - [ ] `OpenAIProvider` implementation
  - [ ] `AnthropicProvider` implementation
  - [ ] `LLMFactory.get_provider()` method
- [ ] Create `backend/core/llm_config.py`
  - [ ] `LLMConfig` class (env-based config)
  - [ ] Default values
  - [ ] Validation logic
- [ ] Create `backend/tests/test_llm_factory.py`
  - [ ] Unit tests for each provider
  - [ ] Error handling tests
  - [ ] Mock tests (don't call real APIs)

**Phase 3: Zencoder Adapter (2h)**
- [ ] Create `backend/core/zencoder_adapter.py`
  - [ ] `ZencoderProvider` class (implements `LLMProvider`)
  - [ ] API key handling
  - [ ] Error handling (API key missing, rate limits, etc.)
  - [ ] Logging for every call
- [ ] Create `backend/tests/test_zencoder_adapter.py`
  - [ ] Mock Zencoder API
  - [ ] Test error scenarios
  - [ ] Test logging output

**Phase 4: MCP Server Wrapper (3h)**
- [ ] Create `mcp_servers/zencoder_mcp_server.py`
  - [ ] Register tools in MCP registry
  - [ ] Implement progress notifications
  - [ ] Error handling with detailed messages
  - [ ] Logging template (copy from codesmith_agent_server.py)
- [ ] Create `backend/tests/test_zencoder_mcp_server.py`
  - [ ] Test MCP communication
  - [ ] Test tool calls

**Phase 5: Integration & Testing (2h)**
- [ ] Update `backend/core/supervisor_mcp.py`
  - [ ] Support Zencoder LLM for routing decisions
  - [ ] Test with env var: `LLM_PROVIDER=zencoder`
- [ ] Run E2E tests
- [ ] Benchmark: Zencoder vs OpenAI vs Anthropic
- [ ] Document results in LANGGRAPH_ARCHITECTURE.md

**Phase 6: Documentation (1h)**
- [ ] Update LANGGRAPH_ARCHITECTURE.md with Zencoder section
- [ ] Update .env.example with ZENCODER_API_KEY
- [ ] Create ZENCODER_SETUP.md (how to get API key, configure, etc.)
- [ ] Update backend/CLAUDE.md with new LLM patterns

---

### Success Criteria

- ✅ Zencoder SDK researched and documented
- ✅ `llm_factory.py` handles 3+ providers (OpenAI, Anthropic, Zencoder)
- ✅ All functions have 2+ log statements (init, completion/error)
- ✅ All functions have unit tests (>80% code coverage)
- ✅ E2E test runs with Zencoder backend
- ✅ Error messages are actionable (not just "error occurred")
- ✅ Configuration is fully documented
- ✅ Performance benchmarked and documented

---

### How to Run This Implementation

```bash
# Step 1: Research
# AI Developer reads Zencoder docs and updates AI_AGENT_IMPLEMENTATION_PLAN.md

# Step 2: Implement llm_factory.py
pytest backend/tests/test_llm_factory.py -v

# Step 3: Implement Zencoder adapter
pytest backend/tests/test_zencoder_adapter.py -v

# Step 4: Implement MCP Server
pytest backend/tests/test_zencoder_mcp_server.py -v

# Step 5: Integration test
python start_server.py
# In another terminal:
python backend/tests/e2e_test.py --provider zencoder

# Step 6: Verify logging
tail -f ~/.ki_autoagent/logs/server.log | grep -E "🤖|📤|✅|❌"
```

---

**Last Updated:** 2025-11-10  
**Status:** ✅ Ready for Implementation  
**Next Step:** Research Zencoder Python SDK


---

## 🔧 LLM Configuration System (v7.1+)

### Quick Reference

**Get LLM for agent:**
```python
from backend.core.llm_factory import AgentLLMFactory
from backend.core.llm_config import AgentLLMConfigManager

# Initialize once at startup
AgentLLMConfigManager.initialize("backend/config/agent_llm_config.json")

# Get provider for agent
provider = AgentLLMFactory.get_provider_for_agent("supervisor")

# Use it
response = await provider.generate_text_with_retries(
    prompt="What should I do?",
    system_prompt="You are helpful.",
    max_retries=3,
)

print(f"Response: {response.content}")
print(f"Tokens: {response.total_tokens}")
print(f"Time: {response.response_time_ms}ms")
```

### Configuration

**File:** `backend/config/agent_llm_config.json`
- Central config for all agents
- Specifies provider (openai/anthropic), model, temperature, timeouts
- Easy to change which agent uses which LLM

**Secrets:** `.env` file
- Keep API keys in `.env` (never in version control)
- `OPENAI_API_KEY=sk-proj-...`
- `ANTHROPIC_API_KEY=sk-ant-...`

### Adding New Provider

1. Create new class extending `LLMProvider`
   ```python
   from backend.core.llm_providers import LLMProvider, LLMResponse
   
   class GroqProvider(LLMProvider):
       async def generate_text(self, prompt, system_prompt=None):
           # Implement API call
           pass
       
       async def validate_api_key(self):
           # Check env var
           pass
       
       def get_provider_name(self):
           return "groq"
   ```

2. Register with factory
   ```python
   from backend.core.llm_factory import AgentLLMFactory
   AgentLLMFactory.register_provider("groq", GroqProvider)
   ```

3. Update config
   ```json
   {
     "agents": {
       "supervisor": {
         "provider": "groq",
         "model": "groq-model-name"
       }
     }
   }
   ```

### Important Notes

- ❌ **DON'T** hard-code model names in agent code
- ✅ **DO** use factory to get provider
- ✅ **DO** use `generate_text_with_retries()` for reliability
- ✅ **DO** log LLM provider/model on agent startup
- ✅ **DO** track response times and token counts
- ❌ **DON'T** expose API keys in logs
- ✅ **DO** initialize config once at app startup

### Phase 3: Agent Integration Pattern

**When updating any agent to use Factory (2025-11-10+):**

```python
# IMPORTS
import logging
from backend.core.llm_factory import AgentLLMFactory
from backend.core.llm_config import AgentLLMConfigManager
from pathlib import Path

logger = logging.getLogger("agent.your_agent_name")

# INITIALIZATION (in __init__)
class YourAgent:
    def __init__(self, agent_name: str, workspace_path: str):
        logger.info(f"🤖 Initializing {agent_name}...")
        
        # Initialize config (once per app startup)
        config_path = Path("backend/config/agent_llm_config.json")
        AgentLLMConfigManager.initialize(config_path)
        
        # Get provider from factory
        self.llm_provider = AgentLLMFactory.get_provider_for_agent(agent_name)
        logger.info(f"   ✅ Provider: {self.llm_provider.get_provider_name()}")
        logger.info(f"   ✅ Model: {self.llm_provider.model}")
        logger.info(f"   ✅ Temperature: {self.llm_provider.temperature}")
        logger.info(f"   ✅ Timeout: {self.llm_provider.timeout_seconds}s")
        
        self.agent_name = agent_name
        self.workspace_path = workspace_path

# LLM CALLS (use async/await)
async def make_decision(self, prompt: str) -> str:
    logger.info(f"📤 Calling LLM for {self.agent_name}...")
    logger.debug(f"   Prompt: {prompt[:100]}...")
    
    try:
        # Use provider with retries
        response = await self.llm_provider.generate_text_with_retries(
            prompt=prompt,
            system_prompt="Your system prompt here",
            max_retries=3,
        )
        
        logger.info(f"✅ {self.agent_name} LLM Response")
        logger.info(f"   Tokens: {response.total_tokens}")
        logger.info(f"   Time: {response.response_time_ms}ms")
        logger.info(f"   Provider: {response.provider}:{response.model}")
        logger.debug(f"   Content preview: {response.content[:200]}...")
        
        return response.content
        
    except Exception as e:
        logger.error(f"❌ {self.agent_name} LLM call failed")
        logger.error(f"   Error: {str(e)}")
        logger.debug(f"   Details: {type(e).__name__}", exc_info=True)
        raise
```

**Key Points for Phase 3:**
- ✅ Initialize config ONCE at app startup (not per agent)
- ✅ Get provider using agent name from factory
- ✅ Use `await provider.generate_text_with_retries()` not `.invoke()`
- ✅ Log EVERYTHING: init, provider, tokens, timing, errors
- ✅ Use structured logging with emoji markers (🤖, 📤, ✅, ❌)
- ✅ Never log API keys or secrets
- ✅ All LLM calls must be `async def` functions
- ❌ Don't hard-code models, temperatures, or timeouts
- ❌ Don't use ChatOpenAI/ChatAnthropic directly

### Debugging

**Check which provider is active:**
```python
provider = AgentLLMFactory.get_provider_for_agent("supervisor")
print(f"Provider: {provider.get_provider_name()}")
print(f"Model: {provider.model}")
print(f"Temperature: {provider.temperature}")
print(f"Max tokens: {provider.max_tokens}")
```

**Check logs for Phase 3 agents:**
```bash
tail -f ~/.ki_autoagent/logs/server.log | grep -E "🤖|📤|✅|❌"
```

**Test provider API key:**
```python
import asyncio
provider = OpenAIProvider(model="gpt-4o")
valid = await provider.validate_api_key()
print(f"API key valid: {valid}")
```

**Test LLM call from agent:**
```python
import asyncio
from backend.core.llm_factory import AgentLLMFactory
from backend.core.llm_config import AgentLLMConfigManager

async def test():
    config_path = Path("backend/config/agent_llm_config.json")
    AgentLLMConfigManager.initialize(config_path)
    
    provider = AgentLLMFactory.get_provider_for_agent("supervisor")
    response = await provider.generate_text_with_retries(
        prompt="Say 'test'",
        system_prompt="You are helpful",
        max_retries=1
    )
    print(f"✅ Response: {response.content}")
    print(f"✅ Tokens: {response.total_tokens}")

asyncio.run(test())
```

---

## 🎯 Phase 3b: Ultra-Logging Framework (NEW)

**All LLM calls are now monitored automatically with:**
- Token counting (input, output, total)
- Cost calculation per provider
- Memory tracking (with psutil when available)
- Performance metrics (latency, tokens/sec)
- Structured JSON export

### Using Ultra-Logging

```python
from backend.core.llm_monitoring import LLMMonitor

# Automatically tracked - no extra code needed!
response = await provider.generate_text(
    prompt="Hello",
    system_prompt="You are helpful",
)

# Later: Get monitoring data
summary = LLMMonitor.get_summary()
print(f"✅ Total calls: {summary['total_calls']}")
print(f"💰 Total cost: {summary['total_cost']}")
print(f"📊 Total tokens: {summary['total_tokens']:,}")

# Export metrics to JSON
LLMMonitor.export_metrics("/tmp/metrics.json")
```

### Monitoring Output Example

```
🤖 ReviewerGPT Agent
├─ 🏗️  Requesting structured output
├─ Provider: openai | Model: gpt-4o-mini
├─ Request ID: reviewer-001
└─ Memory: RSS=245.5MB | Available=1024.0MB

✅ LLM Call Complete: SUCCESS
├─ ⏱️  Latency: 150.00ms (API) + 50.00ms (overhead) = 200.00ms total
├─ 📊 Tokens: Input=536 | Output=134 | Total=670 tokens (0.299ms/token)
├─ 💰 Cost: $0.00016080
├─ 💾 Memory: Start=245.5MB | End=257.6MB | Change=+12.1MB (RSS)
└─ ✅ Success
```

### Monitoring Files

- **Framework:** `backend/core/llm_monitoring.py` (468 lines)
- **Tests:** `backend/tests/test_llm_monitoring_simple.py` (12 tests)
- **Demo:** `backend/tests/test_reviewer_agent_phase3b_demo.py`
- **Docs:** `PHASE_3B_ULTRA_LOGGING_COMPLETE.md`

### Token Pricing Configuration

Edit `TokenPricingConfig` in `llm_monitoring.py` to update provider pricing:

```python
OPENAI_PRICING = {
    "gpt-4o": {
        "input": Decimal("5.00"),      # per 1M tokens
        "output": Decimal("15.00"),
    },
    "gpt-4o-mini": {
        "input": Decimal("0.15"),
        "output": Decimal("0.60"),
    },
    # ... more models
}
```

---

## 🎯 Phase 3c: Prometheus Real-Time Monitoring (NEW)

**All LLM monitoring is now exported to Prometheus for real-time dashboards:**

### 9 Real-Time Metrics

**Counters (only increase):**
- `llm_calls_total{agent_name, provider, model, status}` - Total API calls
- `llm_tokens_total{agent_name, provider, model}` - Total tokens used
- `llm_cost_usd_total{agent_name, provider, model}` - Cumulative cost

**Gauges (can go up/down):**
- `llm_memory_rss_mb{agent_name}` - Memory usage per agent
- `llm_memory_available_mb` - System available memory
- `llm_active_calls{agent_name}` - Running calls per agent

**Histograms (with percentiles):**
- `llm_latency_seconds{agent_name, provider, model}` - Total latency
- `llm_api_latency_seconds{agent_name, provider}` - API latency only
- Last-call gauges: `llm_input_tokens_last_call`, `llm_output_tokens_last_call`

### FastAPI Integration (Ready)

```python
from fastapi import FastAPI
from backend.core.llm_monitoring import LLMMonitor

app = FastAPI()

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    prometheus_data = LLMMonitor.get_prometheus_metrics()
    return Response(prometheus_data, media_type="text/plain; version=0.0.4")
```

### Grafana Queries (Ready)

```promql
# Total calls per agent (rate: 5min)
sum(rate(llm_calls_total[5m])) by (agent_name)

# Token usage trend (1h increase)
increase(llm_tokens_total[1h]) by (agent_name)

# P95 Latency by agent
histogram_quantile(0.95, rate(llm_latency_seconds_bucket[5m])) by (agent_name)

# Success rate
sum(rate(llm_calls_total{status="success"}[5m])) /
sum(rate(llm_calls_total[5m])) by (agent_name)
```

### Prometheus Framework Files

- **Core:** `backend/core/llm_monitoring.py` (extended with Prometheus)
- **Tests:** `backend/tests/test_prometheus_integration.py` (7 tests, 100% passing)
- **Docs:** `PHASE_3C_PROMETHEUS_INTEGRATION.md`
- **Config:** Updated `backend/requirements.txt` with prometheus-client

### Test Results

```
✅ Test 1: Prometheus Availability
✅ Test 2: Metrics Export Format
✅ Test 3: Counter Increments
✅ Test 4: Gauge Updates
✅ Test 5: Histogram Buckets
✅ Test 6: Label Correctness
✅ Test 7: Multiple Agents

📊 Result: 7/7 TESTS PASSING ✅
```

---

## Phase 3c.1: Error Recovery & Resilience Framework ⚠️ CRITICAL

**Status:** ✅ COMPLETE - All 8 tests passing  
**Date:** 2025-11-10  
**Focus:** Fehlerbehandlung & Robustheit  

### What Was Built

**Error Recovery Framework** - Comprehensive resilience layer for LLM API calls:
- Automatic retry with exponential backoff (tenacity library)
- Circuit Breaker pattern to prevent cascading failures
- Timeout handling for slow/unresponsive APIs
- Smart error classification (transient vs permanent)
- Graceful degradation strategies
- Detailed logging for debugging

### Core Components

**`backend/core/error_recovery.py`** (+520 lines)
```python
from backend.core.error_recovery import (
    ErrorRecoveryManager,
    ErrorRecoveryConfig,
    PermanentError,
    TransientError,
)

# Setup
manager = ErrorRecoveryManager()

# Use with retry
result = await manager.execute_with_retry(
    api_call_fn,
    context="code_review",
    timeout_seconds=30
)
```

### Error Classification

**Transient Errors** (Retried automatically):
- TIMEOUT - "timed out", TimeoutError
- RATE_LIMIT - 429, "rate limit"
- CONNECTION_ERROR - ConnectionError, "connection refused"
- SERVER_ERROR - 500, 502, 503

**Permanent Errors** (Fail immediately, no retry):
- AUTH_ERROR - 401, "invalid api key"
- INVALID_REQUEST - 400, "malformed"
- MODEL_NOT_FOUND - 404, "model not found"

### Test Results

```
✅ Test 1: Error Classification (10/10 cases)
✅ Test 2: Circuit Breaker Pattern
✅ Test 3: Sync Retry - Transient Errors
✅ Test 4: Sync Retry - Permanent Errors
✅ Test 5: Async Retry
✅ Test 6: Timeout Handling
✅ Test 7: Circuit Breaker Open State
✅ Test 8: Multiple Concurrent Requests

📊 Result: 8/8 TESTS PASSING ✅
```

### Key Features

1. **Exponential Backoff**
   ```
   Retry 1: wait 100ms
   Retry 2: wait 200ms
   Retry 3: wait 400ms (capped at max)
   ```

2. **Circuit Breaker**
   - Tracks failure rate
   - Opens after N failures
   - Resets after timeout
   - Prevents cascading failures

3. **Timeout Per Attempt**
   - Each retry has own timeout
   - Doesn't count retries toward total time
   - Configurable per call

4. **Smart Error Handling**
   - Specific exception types (not bare `except:`)
   - Status classification (transient vs permanent)
   - Detailed logging for debugging
   - NO secrets in logs

### Improvements vs Phase 3c

**Phase 3c (Monitoring):**
- Tracked metrics AFTER API calls succeeded/failed
- No retry logic

**Phase 3c.1 (Error Recovery):**
- PREVENTS failures before they happen
- AUTO-RETRIES transient errors
- Fast-fails permanent errors
- Protects system with circuit breaker
- Handles timeouts gracefully

### Related Files

- **Implementation:** `backend/core/error_recovery.py`
- **Tests:** `backend/tests/test_error_recovery_framework.py`
- **Documentation:** `PHASE_3C1_ERROR_RECOVERY.md`
- **Best Practices:** `/PYTHON_BEST_PRACTICES.md`

### Production Checklist

- [x] 8/8 error recovery tests passing
- [x] 7/7 prometheus tests still passing (no regression)
- [x] Specific exception handling (no bare `except:`)
- [x] Error classifications validated
- [x] Circuit breaker tested
- [x] Timeout handling tested
- [x] Concurrent requests safe
- [x] Detailed logging
- [x] No secrets in logs

### Next Integration Points

1. Integrate into ReviewerGPT Agent ✅ DONE (Phase 3c.2)
2. Integrate into CodesmithAgent
3. Integrate into ResearchAgent
4. Add error metrics to Prometheus
5. Dashboard for circuit breaker status

---

## Phase 3c.2: ReviewerGPT Agent - Error Recovery Integration ✅ COMPLETE

**Status:** ✅ COMPLETE - All 8 tests passing  
**Date:** 2025-11-10  
**Focus:** Agent integration with error recovery  

### What Was Built

**ReviewerGPTWithErrorRecovery** (`backend/agents/integration/reviewer_with_error_recovery.py`):
- Wraps ReviewerGPT execute() with error recovery
- Automatic retry on transient errors
- Circuit breaker protection
- Error classification (transient/permanent)
- Singleton pattern support
- Circuit breaker status API

### Test Results

```
✅ Test 1: ReviewerGPT Initialization
✅ Test 2: Successful Code Review
✅ Test 3: Circuit Breaker Status Tracking
✅ Test 4: Error Classification (10 types)
✅ Test 5: Monitoring Integration
✅ Test 6: Singleton Pattern
✅ Test 7: Configuration Flexibility
✅ Test 8: Error Recovery Configuration

📊 Result: 8/8 TESTS PASSING ✅

No Regressions:
- Error Recovery: 8/8 ✅
- Prometheus: 7/7 ✅
- Total: 23/23 ✅
```

### Usage Example

```python
from backend.agents.integration.reviewer_with_error_recovery import (
    ReviewerGPTWithErrorRecovery,
    get_reviewer_with_error_recovery,
)

# Create agent with error recovery
agent = ReviewerGPTWithErrorRecovery(
    max_retries=3,
    timeout_seconds=60,
    circuit_breaker_threshold=5,
)

# Or use singleton
agent = get_reviewer_with_error_recovery()

# Execute with automatic retry
result = await agent.execute(request)

# Check circuit breaker status
status = agent.get_circuit_breaker_status()
```

### Key Features

**Error Classification:**
- Transient: timeout, 429, 503 → AUTO-RETRY ✅
- Permanent: 401, 404, 400 → FAIL FAST ❌

**Circuit Breaker:**
- Opens after N failures
- Resets after timeout
- Prevents cascading failures

**Per-Attempt Timeout:**
- Each retry gets full timeout
- Not cumulative
- Configurable per call

### Files

- **Implementation:** `backend/agents/integration/reviewer_with_error_recovery.py` (150 lines)
- **Tests:** `backend/tests/test_reviewer_error_recovery_integration.py` (500 lines)
- **Docs:** `PHASE_3C2_REVIEWER_INTEGRATION.md` (comprehensive)
- **Pattern:** Use for CodesmithAgent, ResearchAgent, etc.

### Production Checklist

- [x] 8/8 integration tests passing
- [x] 8/8 error recovery tests (no regression)
- [x] 7/7 prometheus tests (no regression)
- [x] Error classification validated
- [x] Circuit breaker tested
- [x] Configuration flexible
- [x] Singleton pattern working
- [x] Monitoring integrated
- [x] Documentation complete
- [x] API backward compatible

### Integration Pattern (For Other Agents)

```python
class MyAgentWithErrorRecovery(MyAgent):
    def __init__(self):
        super().__init__()
        self.error_recovery = ErrorRecoveryManager()
    
    async def execute(self, request):
        try:
            result = await self.error_recovery.execute_with_retry(
                super().execute,
                request,
                context="agent_task",
            )
            return result
        except PermanentError as e:
            return TaskResult(status="error", error=str(e))
        except TransientError as e:
            return TaskResult(status="error", error=str(e))
```

### Next Steps

1. CodesmithAgent integration (same pattern)
2. ResearchAgent integration
3. Add error metrics to Prometheus
4. Dashboard visualization


---

## Phase 3c.3: CodeSmithAgent & ResearchAgent Error Recovery Integration ✅ COMPLETE

**Status:** ✅ COMPLETE - All 24 tests passing  
**Date:** 2025-11-12  
**Focus:** Agent integration with error recovery (CodeSmith & Research)  

### What Was Built

**CodeSmithAgentWithErrorRecovery** (`backend/agents/integration/codesmith_with_error_recovery.py`):
- Wraps CodeSmithAgent execute() with error recovery
- Automatic retry on transient errors (API timeouts, rate limits)
- Circuit breaker protection
- Error classification (transient/permanent)
- Singleton pattern support
- Timeout: 120s (optimized for code generation)
- Circuit breaker status API

**ResearchAgentWithErrorRecovery** (`backend/agents/integration/research_with_error_recovery.py`):
- Wraps ResearchAgent execute() with error recovery
- Automatic retry on transient errors (web search timeouts, connection errors)
- Circuit breaker protection
- Error classification (transient/permanent)
- Singleton pattern support
- Timeout: 90s (optimized for web search)
- Circuit breaker status API

### Test Results

```
✅ CodeSmithAgent Integration Tests: 8/8 ✅
✅ ResearchAgent Integration Tests: 8/8 ✅
✅ Error Recovery Framework: 8/8 ✅

📊 Total: 24/24 TESTS PASSING ✅

No Regressions:
- All previous tests still passing
- 100% backward compatibility
```

### Usage Example

```python
# CodeSmithAgent with Error Recovery
from backend.agents.integration.codesmith_with_error_recovery import (
    CodeSmithAgentWithErrorRecovery,
    get_codesmith_with_error_recovery,
)

agent = CodeSmithAgentWithErrorRecovery(
    max_retries=3,
    timeout_seconds=120,  # Longer for code generation
    circuit_breaker_threshold=5,
)

request = TaskRequest(
    prompt="Create a Python REST API",
    context={"language": "python"},
)

result = await agent.execute(request)

# ResearchAgent with Error Recovery
from backend.agents.integration.research_with_error_recovery import (
    ResearchAgentWithErrorRecovery,
    get_research_with_error_recovery,
)

agent = ResearchAgentWithErrorRecovery(
    max_retries=3,
    timeout_seconds=90,  # Optimized for web search
    circuit_breaker_threshold=5,
)

request = TaskRequest(
    prompt="Research Python best practices",
    context={"topic": "python"},
)

result = await agent.execute(request)
```

### Key Features

1. **Automatic Retry**: Transient errors (timeouts, rate limits) automatically retried with exponential backoff
2. **Circuit Breaker**: Protects against cascading failures by opening after threshold
3. **Error Classification**: Distinguishes transient vs permanent errors for smart retry decisions
4. **Per-Attempt Timeout**: Each retry gets independent timeout window
5. **Monitoring Integration**: Integrated with Prometheus for metrics
6. **Thread-Safe**: Concurrent requests handled safely
7. **Backward Compatible**: 100% compatible with existing agent interfaces

### Configuration Recommendations

**CodeSmithAgent:**
- Production: `max_retries=2, timeout=180s, threshold=5`
- Development: `max_retries=3, timeout=120s, threshold=5`
- Testing: `max_retries=1, timeout=60s, threshold=3`

**ResearchAgent:**
- Production: `max_retries=3, timeout=90s, threshold=5`
- Development: `max_retries=3, timeout=90s, threshold=5`
- Testing: `max_retries=1, timeout=30s, threshold=3`

### Testing

```bash
# Run all integration tests
cd /Users/dominikfoert/git/KI_AutoAgent
source venv/bin/activate

# CodeSmithAgent (8 tests)
python3 backend/tests/test_codesmith_error_recovery_integration.py

# ResearchAgent (8 tests)
python3 backend/tests/test_research_error_recovery_integration.py

# Error Recovery Framework (8 tests)
python3 backend/tests/test_error_recovery_framework.py

# Total: 24/24 tests passing ✅
```

### Next Steps

1. Integrate ArchitectAgent with error recovery
2. Integrate ResponderAgent with error recovery
3. Add error metrics to Prometheus (retry counts, circuit breaker events)
4. Performance load testing with concurrent requests
5. Dashboard visualization for circuit breaker status

### Documentation

- **Main Doc**: `PHASE_3C3_AGENT_INTEGRATIONS.md`
- **Implementation**: `backend/agents/integration/codesmith_with_error_recovery.py`
- **Implementation**: `backend/agents/integration/research_with_error_recovery.py`
- **Tests**: `backend/tests/test_codesmith_error_recovery_integration.py`
- **Tests**: `backend/tests/test_research_error_recovery_integration.py`

---

## 🧪 E2E TESTING STRATEGY FOR AI DEVELOPERS

**Version:** 1.0.0  
**Last Updated:** 2025-11-12  
**Status:** Active Development Framework

### CRITICAL: Workspace Isolation Rule

```
🚨 NEVER run E2E tests in the development repository!
   Test workspace MUST be: ~/TestApps/e2e_test_run/
   NOT in: /Users/.../git/KI_AutoAgent/
```

**Why?** Claude CLI subprocess inherits CWD. If old test artifacts exist in dev repo, Claude finds them and crashes.

### E2E Test Workflow

#### 1. **Prepare Workspace**
```python
import shutil
from pathlib import Path

TEST_WORKSPACE = Path.home() / "TestApps" / "e2e_test_run"

print(f"🧹 [E2E] Cleaning old workspace...")
if TEST_WORKSPACE.exists():
    shutil.rmtree(TEST_WORKSPACE)

TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
print(f"✅ [E2E] Workspace ready: {TEST_WORKSPACE}")

# Verify isolation
assert not (TEST_WORKSPACE / "old-app").exists()
print(f"✅ [E2E] Workspace verified clean")
```

#### 2. **Start Backend (with cwd parameter)**
```python
process = await asyncio.create_subprocess_exec(
    "python", "backend/workflow_v7_mcp.py",
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
    cwd=str(TEST_WORKSPACE),  # 🎯 CRITICAL!
)
print(f"✅ [E2E] Backend started (PID: {process.pid})")
```

#### 3. **Connect Client & Send Task**
```python
async with websockets.connect("ws://localhost:8002/ws/chat") as ws:
    print(f"✅ [E2E] WebSocket connected")
    
    task = {
        "type": "task",
        "content": "Create task manager app",
        "workspace_path": str(TEST_WORKSPACE)
    }
    
    print(f"📤 [E2E] Sending task...")
    await ws.send(json.dumps(task))
    print(f"✅ [E2E] Task sent")
```

#### 4. **Monitor Progress**
```python
while True:
    message = await ws.recv()
    data = json.loads(message)
    
    if data.get("type") == "progress":
        progress = data.get("progress", 0)
        print(f"⏳ [E2E] Progress: {progress}%")
    
    elif data.get("type") == "complete":
        print(f"✅ [E2E] Task complete")
        return data
    
    elif data.get("type") == "error":
        print(f"❌ [E2E] Error: {data.get('error')}")
        raise Exception(data.get("error"))
```

#### 5. **Validate Results**
```python
print(f"🔍 [E2E] Running validations...")

# Check files in correct location
expected_files = ["README.md", "package.json", "src/"]
for file in expected_files:
    path = TEST_WORKSPACE / file
    assert path.exists(), f"Missing: {file}"
    print(f"✅ [E2E] File found: {file}")

# Check no old artifacts
assert not (TEST_WORKSPACE / "old-app").exists()
print(f"✅ [E2E] No old artifacts")

# Check structure
assert (TEST_WORKSPACE / "README.md").is_file()
assert (TEST_WORKSPACE / "src").is_dir()
print(f"✅ [E2E] Structure correct")

print(f"✅ [E2E] ALL VALIDATIONS PASSED")
```

#### 6. **Cleanup**
```python
# Keep on success for inspection (optional)
if test_passed:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TEST_WORKSPACE.parent / f"test_success_{timestamp}"
    shutil.copytree(TEST_WORKSPACE, backup)
    print(f"📦 [E2E] Backup: {backup}")
else:
    # Clean on failure
    if TEST_WORKSPACE.exists():
        shutil.rmtree(TEST_WORKSPACE)
    print(f"✅ [E2E] Workspace cleaned")
```

### STDOUT Logging Standard

```python
# Format: [PHASE] [STATUS] Message

print(f"🚀 [INIT] Loading configuration...")
print(f"📡 [CONN] WebSocket connecting...")
print(f"📤 [REQ]  Sending task...")
print(f"⏳ [WAIT] Waiting for response...")
print(f"✅ [OK]   Validation passed")
print(f"❌ [ERR]  Error occurred: {error}")
print(f"📊 [LOG]  Debug info: {info}")
```

### Common Debugging

| ❌ Problem | 🔍 Debug | ✅ Fix |
|-----------|---------|-------|
| "App already exists" | Check CWD in logs | Set `cwd=workspace_path` |
| Old files found | Check workspace isolation | Clean old artifacts |
| Claude CLI crashes | Check subprocess output | Fix workspace path |
| Test hangs | Monitor progress logs | Check timeout values |
| Files in dev repo | Check git status | Add to .gitignore |

### Checklist Before E2E Test

- [ ] Test workspace is OUTSIDE dev repo
- [ ] Workspace is clean (no old artifacts)
- [ ] Backend `cwd` parameter is set
- [ ] WebSocket client passes `workspace_path`
- [ ] All logging is in place
- [ ] Backend ready on port 8002

### Checklist After E2E Test

- [ ] Files in correct workspace ✅
- [ ] No old artifacts found ✅
- [ ] Subprocess CWD correct ✅
- [ ] No stdout/stderr errors ✅
- [ ] backend has workspace_path ✅
- [ ] Logs analyzed for issues ✅

### Key Learning

**Bug discovered 2025-10-11:**
- Codesmith crashed after 5 minutes
- Root cause: Wrong subprocess CWD
- Claude found old test app in dev repo
- Fix: Set `cwd=self.workspace_path` in subprocess

**This is why E2E testing is critical!** 🎯

### Documentation Reference

- **Full Strategy**: `DEVELOPMENT_AI_ASSISTANT_STRATEGY.md`
- **Test Architecture (4 Layers)**: `TEST_ARCHITECTURE_LAYERS.md` ⭐ NEW
- **E2E Guide**: `E2E_TESTING_GUIDE.md`
- **Critical Failures**: `CRITICAL_FAILURE_INSTRUCTIONS.md`
- **Python Best Practices**: `PYTHON_BEST_PRACTICES.md`

---

## 🏗️ TEST ARCHITECTURE OVERVIEW (4 Layers)

**See: `TEST_ARCHITECTURE_LAYERS.md` for complete documentation**

### Quick Reference

```
Layer 2: Backend Tests (backend/tests/)
  ↓ My unit tests during development
  ↓ pytest framework
  ↓ Run: pytest backend/tests/
  
Layer 3a: Start KI_Agent Backend
  ↓ python backend/workflow_v7_mcp.py
  
Layer 3b: E2E WebSocket Tests (test_e2e_*.py)
  ↓ My tests AFTER development
  ↓ websockets framework
  ↓ Run: python3 test_e2e_app_creation.py
  
Layer 4: E2E Testing Framework (backend/e2e_testing/)
  ↓ Agent uses automatically
  ↓ Playwright framework
  ↓ Tests generated apps
```

### What to Use When

| Scenario | Layer | Command | Time |
|----------|-------|---------|------|
| Develop new feature | 2 | `pytest backend/tests/` | 2 min |
| Test feature in Agent | 3b | `python3 test_e2e_*.py` | 10 min |
| Test generated apps | 4 | Automatic (Agent) | 10 min |

