# 🔬 AI Agent Implementation Plan: Zencoder Support (v7.1)

**Date:** 2025-11-10  
**Status:** Phase 1 - Research Complete ✅  
**Goal:** Add Zencoder as flexible LLM provider in KI AutoAgent v7.0

---

## 📊 Research Findings

### What is Zencoder?

**Zencoder is NOT a traditional LLM API provider.**

Instead, Zencoder is:
- ✅ An IDE plugin (VS Code, JetBrains)
- ✅ A Chrome browser extension
- ✅ An MCP **CLIENT** (not server) that wraps multiple LLM providers
- ❌ NOT available as a Python SDK/library
- ❌ NOT available as a REST API
- ❌ NOT installable via `pip`

**What Zencoder Abstracts:**
```
┌─────────────────────────────────────┐
│     Zencoder IDE Plugin             │
├─────────────────────────────────────┤
│  Model Selector (Auto, Auto+, etc)  │
├─────────────────────────────────────┤
│  Backend Routing & Load Balancing   │
├─────────────────────────────────────┤
│  OpenAI  │ Anthropic │ Google │ xAI │
└─────────────────────────────────────┘
```

---

## 🔄 Available Models in Zencoder

| Model | Provider | Use Case |
|-------|----------|----------|
| **Auto** | Zencoder Managed | Default - best balance |
| **Auto+** | Zencoder Managed | Higher quality, 2.5× cost |
| Sonnet 4.5 Parallel | Anthropic | Spec-driven dev ⭐ |
| GPT-5 | OpenAI | General coding |
| Gemini 2.5 Pro | Google | Cost-efficient |
| Grok Code Fast 1 | xAI | Cheapest option |

**IMPORTANT:** Zencoder does NOT expose its routing logic or API for external integration!

---

## ❌ Why We CANNOT Use Zencoder Directly in KI AutoAgent

### Problem 1: No Python SDK/API
```python
# ❌ DOESN'T EXIST
from zencoder import ZencoderClient
client = ZencoderClient(api_key="...")
response = client.generate_code("...")
```

### Problem 2: No REST API
```bash
# ❌ DOESN'T EXIST
curl https://api.zencoder.ai/v1/generate \
  -H "Authorization: Bearer TOKEN" \
  -d '{"prompt": "..."}'
```

### Problem 3: Zencoder is IDE-Only
- Zencoder runs as an IDE plugin
- Cannot be called from standalone Python scripts
- Cannot be integrated into LangGraph workflows

### Problem 4: Architectural Mismatch
- Zencoder = IDE chatbot for developers
- KI AutoAgent = Headless multi-agent system
- These are fundamentally different use cases

---

## ✅ Three Possible Integration Paths

### Path 1: Use Zencoder as "Inspiration" - Implement Provider Flexibility ⭐ RECOMMENDED

**What:** Build LLMFactory that supports OpenAI + Anthropic + Custom Providers  
**Why:** 
- Zencoder's model abstraction is smart (Auto, Auto+, etc)
- We can implement similar abstraction ourselves
- Requires NO external dependency on Zencoder

**How:**
```python
# backend/core/llm_factory.py
class LLMFactory:
    @classmethod
    def get_provider(cls, provider: str, model: str) -> LLMProvider:
        if provider == "openai":
            return OpenAIProvider(model="gpt-4o-2024-11-20")
        elif provider == "anthropic":
            return AnthropicProvider(model="claude-sonnet-4-20250514")
        elif provider == "zencoder_cli":  # See Path 2
            return ZencoderCLIWrapper(model="auto")
        else:
            raise ValueError(f"Unknown provider: {provider}")
```

**Effort:** ⭐⭐ (2-3 days)  
**Result:** Full LLM flexibility, works today

---

### Path 2: Zencoder CLI Wrapper MCP Server (If Zencoder CLI Exists)

**What:** Wrap Zencoder command-line tool in MCP server (like we do with Claude CLI)  
**Why:** Reuses existing Codesmith pattern

**How:**
```bash
# Installation prerequisite
which zencoder  # Must be available in PATH
zencoder --version  # Must work from terminal
```

**Questions to Answer:**
- [ ] Does Zencoder have a CLI tool?
- [ ] Can it be used non-interactively (like Claude CLI)?
- [ ] Does it support model selection via flag?
- [ ] Is it available for macOS/Linux/Windows?

**Effort:** ⭐⭐⭐ (3-5 days, depends on CLI availability)  
**Result:** Zencoder as one of many MCP servers

---

### Path 3: Zencoder API Reverse Engineering (NOT RECOMMENDED)

**What:** Figure out Zencoder's internal API by inspecting IDE plugin  
**Why:** ❌ Too risky, violates ToS, unmaintainable

**Effort:** ⭐⭐⭐⭐⭐ (10+ days, fragile)  
**Result:** Fragile, likely to break

---

## 🎯 RECOMMENDATION: Hybrid Approach

**Implement Path 1 + Path 2 (in that order):**

### Phase 1 (Week 1): Build LLMFactory (Path 1)
- ✅ Create abstraction for OpenAI + Anthropic
- ✅ Support environment-based configuration
- ✅ Unit tests for all providers
- ✅ Works immediately with existing APIs

### Phase 2 (Week 2): Add Zencoder CLI Support (Path 2)
- ❓ Research Zencoder CLI availability
- ❓ If CLI exists: Create `ZencoderCLIWrapper` MCP server
- ❓ If CLI doesn't exist: Skip this phase

### Phase 3 (Week 3): Documentation
- ✅ Document how to select providers
- ✅ Performance benchmarks
- ✅ Cost analysis

---

## 📋 Implementation Checklist

### Phase 1: LLMFactory (DEFINITE)

**Files to Create:**
- [ ] `backend/core/llm_factory.py` (180 lines)
- [ ] `backend/core/llm_config.py` (80 lines)
- [ ] `backend/tests/test_llm_factory.py` (150 lines)

**Files to Modify:**
- [ ] `backend/core/supervisor_mcp.py` (use factory instead of ChatOpenAI)
- [ ] `backend/requirements.txt` (no new dependencies!)
- [ ] `.env.example` (add LLM_PROVIDER, LLM_MODEL)

**Result:** 
```bash
LLM_PROVIDER=openai LLM_MODEL=gpt-4o-2024-11-20 python start_server.py
LLM_PROVIDER=anthropic LLM_MODEL=claude-sonnet-4-20250514 python start_server.py
```

---

### Phase 2: Zencoder CLI Wrapper (CONDITIONAL)

**Prerequisites:**
```bash
# Must answer YES to all:
which zencoder                    # ✅ or ❌
zencoder --help                   # ✅ or ❌
zencoder --model=auto "test"      # ✅ or ❌
```

**Files to Create (if CLI exists):**
- [ ] `mcp_servers/zencoder_cli_wrapper_server.py` (300 lines)
- [ ] `backend/tests/test_zencoder_cli_wrapper.py` (150 lines)

**Files to Modify:**
- [ ] `backend/utils/mcp_manager.py` (register zencoder_cli_wrapper)
- [ ] `backend/core/supervisor_mcp.py` (optional: use zencoder)

**Result:**
```bash
LLM_PROVIDER=zencoder_cli LLM_MODEL=auto python start_server.py
```

---

## 🔬 Current blockers

### Blocker 1: Zencoder CLI Availability
**Question:** Is Zencoder available as a CLI tool?

**How to Find Out:**
```bash
# On Zencoder docs website - CLI Installation section
# Or: Try to find it in PATH
which zencoder
zencoder --version
```

**Status:** 🤔 UNKNOWN

---

### Blocker 2: Zencoder API Key Management
**Question:** How does Zencoder auth work without Python SDK?

**Possible Answers:**
1. API key in environment variable → `ZENCODER_API_KEY`
2. Config file stored in ~/.zencoder/config
3. Requires IDE login (won't work for headless)

**Status:** 🤔 UNKNOWN

---

## 📌 Next Steps for AI Developer

### Step 1: Answer Blocker Questions (1 hour)
```bash
# In your terminal on your dev machine:

# 1. Is Zencoder CLI installed?
which zencoder
zencoder --version

# 2. Can you call it non-interactively?
zencoder --help | head -20

# 3. Does it show model selection options?
zencoder --model help
```

### Step 2: Report Findings (30 minutes)
Update this file with YES/NO answers to:
- [ ] Zencoder CLI exists and works?
- [ ] Can be called non-interactively?
- [ ] Supports model selection?
- [ ] Works with API key auth?

### Step 3: Implement Path 1 (3 hours)
- Create `llm_factory.py` (OpenAI + Anthropic support)
- Create unit tests
- Update supervisor to use factory

### Step 4: Conditionally Implement Path 2 (3 hours, only if Path 3 = YES)
- If Zencoder CLI works: Create CLI wrapper
- Test with MCP communication
- Add to supervisor

---

## 💡 Key Insights

### Insight 1: Zencoder is "Model Agnostic" Not "API Agnostic"
- Zencoder **abstracts LLM selection** (Auto, Sonnet, GPT-5, etc)
- Zencoder does NOT provide an API for external systems
- We must build our own abstraction layer

### Insight 2: Pattern Similarity
```
Zencoder's Architecture:
  IDE Plugin → [Model Router] → {OpenAI, Anthropic, Google, xAI}

Our Architecture (after LLMFactory):
  Supervisor → [LLMFactory] → {OpenAI, Anthropic, Custom}
```

### Insight 3: Cost/Complexity Trade-off
- **Path 1 (LLMFactory):** 20% effort, 100% value
- **Path 2 (CLI Wrapper):** 40% effort, depends on CLI existence
- **Path 3 (Reverse Engineering):** 500% effort, 0% value

---

## 📚 Documentation References

**Zencoder Docs Read:**
- ✅ Models Overview
- ✅ Integrations and MCP
- ✅ MCP Protocol Support
- ❓ CLI Documentation (didn't find this!)

**Zencoder Docs NOT Found:**
- ❌ Python SDK documentation
- ❌ REST API documentation
- ❌ CLI documentation
- ❌ Authentication methods for non-IDE use

---

## 🎬 Final Recommendation

**DO THIS (Immediate, 100% confident):**
1. Implement LLMFactory with OpenAI + Anthropic support
2. Update Supervisor to use LLMFactory
3. Environment variable configuration
4. Unit tests + E2E tests
5. Documentation

**THEN ASK (After Phase 1 is done):**
- "Is Zencoder CLI available and can we use it?"
- If YES → Add Zencoder CLI wrapper
- If NO → Stop here, we have full flexibility with OpenAI + Anthropic

**AVOID (Never):**
- Trying to use Zencoder as a Python library (doesn't exist)
- Trying to call Zencoder API (no public API)
- Trying to reverse-engineer Zencoder plugin (fragile, ToS violation)

---

## 📝 Status Summary

| Item | Status | Evidence |
|------|--------|----------|
| Zencoder Python SDK | ❌ DOESN'T EXIST | Checked docs, no SDK found |
| Zencoder REST API | ❌ DOESN'T EXIST | Checked docs, no API found |
| Zencoder CLI | 🤔 UNKNOWN | Need to test locally |
| Zencoder MCP Support | ✅ YES | As MCP CLIENT only |
| OpenAI Python Support | ✅ YES | `langchain-openai` exists |
| Anthropic Python Support | ✅ YES | `langchain-anthropic` exists |
| LLMFactory Implementation | ✅ READY | Can start immediately |

---

**Last Updated:** 2025-11-10  
**Phase:** ✅ Research Complete  
**Next Phase:** 🚀 Implementation (pending CLI discovery)
