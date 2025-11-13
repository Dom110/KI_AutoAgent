# 🔗 Phase 3: Factory Integration Guide

**Date:** 2025-11-10  
**Status:** Planning & Documentation  
**Audience:** AI Developer implementing agent integration

---

## Overview

Phase 3 involves integrating the `AgentLLMFactory` into existing agents to use the new flexible LLM configuration system instead of hard-coded model values.

---

## Current State (Before Phase 3)

### supervisor_mcp.py (Current ❌)
```python
from langchain_openai import ChatOpenAI

class SupervisorMCP:
    def __init__(self, model: str = "gpt-4o-2024-11-20", temperature: float = 0.3):
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=1500
        )
```

**Problems:**
- ❌ Model hard-coded in agent class
- ❌ Temperature hard-coded in agent class
- ❌ Can't use factory-based configuration
- ❌ Difficult to switch between OpenAI/Anthropic
- ❌ No logging of LLM provider/model

---

## Target State (After Phase 3)

### supervisor_mcp.py (After Integration ✅)
```python
from backend.core.llm_config import AgentLLMConfigManager
from backend.core.llm_factory import AgentLLMFactory
import logging

logger = logging.getLogger("agent.supervisor")

class SupervisorMCP:
    def __init__(self, workspace_path: str, session_id: str | None = None):
        """Initialize Supervisor using factory-based LLM configuration."""
        
        # Initialize config (once at startup)
        config_path = Path("backend/config/agent_llm_config.json")
        AgentLLMConfigManager.initialize(config_path)
        
        logger.info(f"🤖 Initializing SupervisorMCP...")
        
        # Get LLM provider from factory
        self.llm_provider = AgentLLMFactory.get_provider_for_agent("supervisor")
        logger.info(f"   ✅ Using LLM: {self.llm_provider.get_provider_name()}:{self.llm_provider.model}")
        
        self.workspace_path = workspace_path
        self.session_id = session_id
        self.workflow_history: list[dict] = []
        self.mcp = get_mcp_manager(workspace_path=workspace_path)
    
    async def make_decision(self, context: SupervisorContext) -> SupervisorAction:
        """Make a decision using the factory-provided LLM."""
        
        logger.info(f"📤 Calling LLM for decision (iteration {context.iteration})")
        
        prompt = self._build_decision_prompt(context)
        
        try:
            # Use the provider (with retries)
            response = await self.llm_provider.generate_text_with_retries(
                prompt=prompt,
                system_prompt=SUPERVISOR_SYSTEM_PROMPT,
                max_retries=3,
            )
            
            logger.info(f"✅ LLM response: {response.total_tokens} tokens in {response.response_time_ms}ms")
            
            # Parse response and return action
            action = self._parse_response(response.content)
            return action
            
        except Exception as e:
            logger.error(f"❌ LLM call failed: {e}")
            raise
```

**Benefits:**
- ✅ Uses factory-based configuration
- ✅ Easy to switch providers (change JSON only)
- ✅ Comprehensive logging
- ✅ Token tracking and timing
- ✅ Automatic retries on rate limits
- ✅ Consistent with all other agents

---

## Integration Steps

### Step 1: Prepare the Agent

**Before starting integration:**
1. Identify where LLM is currently instantiated
2. Note the model name being used
3. Check the current temperature/max_tokens values
4. Plan how to handle system prompts

### Step 2: Update Config (if needed)

If agent-specific configuration needs to change, update `agent_llm_config.json`:

```json
{
  "agents": {
    "supervisor": {
      "provider": "openai",
      "model": "gpt-4o-2024-11-20",
      "temperature": 0.4,
      "max_tokens": 2000,
      "timeout_seconds": 30
    }
  }
}
```

### Step 3: Integrate Factory into Agent

**Minimal integration example:**

```python
from backend.core.llm_factory import AgentLLMFactory
from backend.core.llm_config import AgentLLMConfigManager
import logging

logger = logging.getLogger("agent.supervisor")

class SupervisorMCP:
    def __init__(self, workspace_path: str):
        # Initialize config (once per application startup)
        config_path = Path("backend/config/agent_llm_config.json")
        AgentLLMConfigManager.initialize(config_path)
        
        # Get provider from factory
        self.llm_provider = AgentLLMFactory.get_provider_for_agent("supervisor")
        logger.info(f"🤖 Supervisor using: {self.llm_provider.get_provider_name()}:{self.llm_provider.model}")
        
        self.workspace_path = workspace_path
    
    async def call_llm(self, prompt: str) -> str:
        """Call LLM through factory provider."""
        logger.info("📤 Calling LLM...")
        
        try:
            response = await self.llm_provider.generate_text_with_retries(
                prompt=prompt,
                system_prompt="You are a helpful assistant.",
                max_retries=3,
            )
            
            logger.info(f"✅ Response: {response.total_tokens} tokens in {response.response_time_ms}ms")
            return response.content
            
        except Exception as e:
            logger.error(f"❌ LLM call failed: {e}")
            raise
```

---

## Agents to Integrate (Priority Order)

### Phase 3a: Core Agents (Critical)
- [ ] **Supervisor** (`backend/core/supervisor_mcp.py`)
  - Currently: `ChatOpenAI("gpt-4o-2024-11-20", temp=0.3)`
  - Target: `OpenAIProvider` via factory
  
### Phase 3b: Specialized Agents (Important)
- [ ] **Codesmith** (`backend/agents/specialized/codesmith_agent.py`)
  - Currently: `ChatAnthropic("claude-sonnet-4")`
  - Target: `AnthropicProvider` via factory
  
- [ ] **Architect** (`backend/agents/specialized/architect_agent.py`)
  - Currently: `ChatAnthropic("claude-opus-4-1")`
  - Target: `AnthropicProvider` via factory
  
- [ ] **Research** (`backend/agents/specialized/research_agent.py`)
  - Currently: `ChatAnthropic("claude-haiku-4")`
  - Target: `AnthropicProvider` via factory

### Phase 3c: Other Agents (Can Wait)
- [ ] **ReviewFix** (`backend/agents/specialized/reviewer_gpt_agent.py`)
- [ ] **Responder** (Response formatting agent)

---

## Testing After Integration

### Unit Tests
```bash
# Test that provider is correctly configured
pytest backend/tests/test_supervisor_llm_integration.py -v
```

### Integration Tests
```bash
# Test agent with factory provider
pytest backend/tests/test_mcp_integration.py -v
```

### E2E Tests
```bash
# Start server and test full workflow
python start_server.py
python backend/tests/e2e_test_llm_integration.py
```

### Manual Testing
```bash
# Check logs to verify provider and model
tail -f ~/.ki_autoagent/logs/server.log | grep -E "(LLM|Provider|Model)"
```

---

## Debugging Integration Issues

### Issue: "OPENAI_API_KEY not set"
```
❌ OPENAI_API_KEY not set in environment
```
**Solution:** Set API key in `.env`:
```bash
export OPENAI_API_KEY="sk-proj-..."
```

### Issue: "Unsupported provider: xyz"
```
❌ Unsupported provider: xyz (supported: openai, anthropic)
```
**Solution:** Check `agent_llm_config.json` for typo in provider name

### Issue: "Config not found"
```
❌ Config file not found: backend/config/agent_llm_config.json
```
**Solution:** Ensure config file exists in correct location

### Issue: "LLM call timed out"
```
❌ API call timed out after 30s
```
**Solution:** Increase `timeout_seconds` in `agent_llm_config.json`

---

## Rollback Plan

If integration causes issues:

1. **Quick Rollback:** Use feature flag
   ```python
   use_factory = os.getenv("USE_LLM_FACTORY", "true").lower() == "true"
   
   if use_factory:
       llm_provider = AgentLLMFactory.get_provider_for_agent("supervisor")
   else:
       llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
   ```

2. **Full Rollback:** Revert to previous git commit
   ```bash
   git revert <commit_hash>
   ```

---

## Success Metrics

After Phase 3 integration is complete:

- ✅ All agents use factory-based configuration
- ✅ No hard-coded model names in agent code
- ✅ All tests pass (unit, integration, E2E)
- ✅ Logs show correct LLM provider/model for each agent
- ✅ Can switch providers by updating JSON only
- ✅ Response times and token counts are tracked

---

## Next Steps (Phase 4+)

- [ ] **Phase 4**: Add monitoring dashboard for LLM costs
- [ ] **Phase 5**: A/B testing different models per agent
- [ ] **Phase 6**: Add Groq/other provider support
- [ ] **Phase 7**: Implement caching layer for repeated prompts

