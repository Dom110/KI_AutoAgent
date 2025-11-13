---
description: Complete API Key Validation Guide for KI AutoAgent v7.0
alwaysApply: true
---

# 🔑 API Key Validation Guide

**Version:** 1.0.0  
**Date:** 2025-11-02  
**Python Version:** 3.13.8+  
**Related:** `PYTHON_BEST_PRACTICES.md`, `server_v7_mcp.py`

---

## 📌 Overview

KI AutoAgent v7.0 requires **TWO mandatory API keys**:
1. **OpenAI API Key** - For GPT-4o Supervisor & embeddings
2. **Perplexity API Key** - For Research Agent web search

> ⚠️ **CRITICAL**: Without Perplexity, the Research Agent cannot function!

---

## 🔍 Validation Strategy

### Why Both Keys Are Required

| Key | Purpose | Used By | Impact |
|-----|---------|---------|--------|
| **OpenAI** | GPT-4o Supervisor, task orchestration | `supervisor_mcp.py` | Core system fails without it |
| **Perplexity** | Web search, real-time data, research | `research_agent_server.py` | Research workflows fail without it |

### Previous Bug ❌

**BEFORE (server_v7_mcp.py line 140-142)**:
```python
if not perplexity_key or perplexity_key == "":
    logger.warning("⚠️ PERPLEXITY_API_KEY not set - web research will use fallback")
else:
    logger.info("✅ PERPLEXITY_API_KEY: Set (validation skipped)")  # ← BUG: Ignored!
```

**Problem**: Perplexity was optional with **no validation** → Research Agent fails at runtime

---

## 🛠️ Current Implementation

### File: `backend/api/server_v7_mcp.py`

**Location**: Lines 114-228 (validate_api_keys function)

```python
def validate_api_keys() -> None:
    """Validate required API keys and test connectivity.
    
    Follows Python Best Practices from PYTHON_BEST_PRACTICES.md:
    - Specific exception handling (not bare Exception)
    - Minimal try block scope
    - Clear error messages for debugging
    """
```

### Validation Flow

```
1. Load API keys from ~/.ki_autoagent/config/.env
   ↓
2. Validate OpenAI Key
   ├─ Check: Is key set and non-empty?
   ├─ Test: client.models.list() - actual API call
   └─ Exit if: Missing, empty, or invalid
   ↓
3. Validate Perplexity Key (NEW!)
   ├─ Check: Is key set and non-empty?
   ├─ Check: Format valid (len >= 10)?
   ├─ Test: HEAD request to API endpoint (3s timeout)
   ├─ Fallback: POST request with minimal payload (8s timeout)
   ├─ Handle: Timeouts gracefully (format check = pass)
   └─ Exit if: Missing, empty, or auth fails (401)
   ↓
4. Continue to MCP Server startup
```

---

## 🔧 Implementation Details

### OpenAI Validation

```python
# ✅ Check existence
if not openai_key or openai_key == "":
    logger.error("❌ OPENAI_API_KEY not set or empty!")
    sys.exit(1)

# ✅ Test connectivity (specific exception handling)
try:
    from openai import OpenAI
    client = OpenAI(api_key=openai_key)
    client.models.list()  # Quick API test
    logger.info("✅ OPENAI_API_KEY: Valid")
except (ImportError, ModuleNotFoundError) as e:
    logger.error(f"❌ OpenAI package not installed: {e}")
    sys.exit(1)
except Exception as e:  # Fallback for unexpected errors
    logger.error(f"❌ OPENAI_API_KEY: Invalid - {str(e)[:80]}")
    sys.exit(1)
```

### Perplexity Validation (NEW)

**Why Multiple Test Methods?**

1. **HEAD Request (3s timeout)**
   - Fastest check
   - Just validates endpoint reachability
   - Returns headers only (no body)

2. **POST Fallback (8s timeout)**
   - If HEAD fails/times out
   - Minimal payload to avoid costs
   - Tests actual API logic

3. **Graceful Timeout Handling**
   - If both timeout → key format looks OK → ACCEPT
   - Assumes slow API, not bad credentials

```python
# ✅ HEAD request (fast)
try:
    response = requests.head(
        "https://api.perplexity.ai/chat/completions",
        headers=headers,
        timeout=3,
        allow_redirects=True
    )
except (requests.Timeout, requests.ConnectionError):
    # ✅ Fallback to POST (minimal data)
    payload = {
        "model": "sonar",
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 1
    }
    response = requests.post(
        "https://api.perplexity.ai/chat/completions",
        json=payload,
        headers=headers,
        timeout=8
    )

# ✅ Status code interpretation
if response.status_code in (200, 400, 429):
    logger.info("✅ PERPLEXITY_API_KEY: Valid")
elif response.status_code == 401:
    raise RuntimeError("Authentication failed - invalid API key")
```

**Status Codes**:
- `200` = Success (ideal)
- `400` = Invalid parameter (auth works!)
- `401` = Invalid credentials → FAIL
- `429` = Rate limited (auth works!)

---

## 📋 Best Practices Applied

### 1. Specific Exception Handling ✅

**Bad** ❌:
```python
try:
    openai_client = OpenAI(api_key=openai_key)
except Exception as e:  # Too broad!
    logger.error(f"Error: {e}")
```

**Good** ✅:
```python
try:
    openai_client = OpenAI(api_key=openai_key)
except (ImportError, ModuleNotFoundError) as e:
    logger.error(f"Package not installed: {e}")
except Exception as e:  # Fallback for unexpected
    logger.error(f"API error: {e}")
```

### 2. Minimal Try Block Scope ✅

**Bad** ❌:
```python
try:
    validate_openai()
    validate_perplexity()
    start_server()
except Exception as e:
    logger.error(f"Failed: {e}")  # Which step failed?
```

**Good** ✅:
```python
try:
    validate_openai()
except Exception as e:
    logger.error(f"OpenAI validation failed: {e}")
    sys.exit(1)

try:
    validate_perplexity()
except Exception as e:
    logger.error(f"Perplexity validation failed: {e}")
    sys.exit(1)
```

### 3. Type Hints ✅

```python
def validate_api_keys() -> None:  # Clear return type
    """Validate required API keys and test connectivity."""
```

### 4. Clear Error Messages ✅

Each error message includes:
- **What**: What was being validated
- **Why**: Why it's required
- **How**: How to fix it

```python
logger.error("❌ PERPLEXITY_API_KEY not set or empty!")
logger.error("   Required for: Research Agent (web search & real-time data)")
logger.error("   Set in: ~/.ki_autoagent/config/.env")
logger.error("   Get your key from: https://www.perplexity.ai/api")
```

### 5. Fallback Strategies ✅

**Fast API Timeout Handling**:
```python
try:
    response = requests.head(..., timeout=3)
except requests.Timeout:
    # Fallback with longer timeout
    response = requests.post(..., timeout=8)
```

**Graceful Degradation**:
```python
except requests.Timeout:
    logger.warning("⚠️ PERPLEXITY_API_KEY: Validation timed out (API slow)")
    logger.info("✅ PERPLEXITY_API_KEY: Accepted (format valid)")
    # Don't fail - assume key is OK
```

---

## 🚀 Testing the Validation

### Test 1: Valid Keys (Normal Case)

```bash
cd /Users/dominikfoert/git/KI_AutoAgent
source venv/bin/activate
python backend/api/server_v7_mcp.py
```

**Expected Output**:
```
✅ OPENAI_API_KEY: Valid
✅ PERPLEXITY_API_KEY: Valid (status: ok)
🔑 API key validation complete
🚀 Starting KI AutoAgent v7.0 Pure MCP Server...
```

### Test 2: Missing OpenAI Key

```bash
# Temporarily remove OpenAI key
unset OPENAI_API_KEY
python backend/api/server_v7_mcp.py
```

**Expected Output**:
```
❌ OPENAI_API_KEY not set or empty!
   Required for: GPT-4o Supervisor, Embeddings
   Set in: ~/.ki_autoagent/config/.env
```

### Test 3: Missing Perplexity Key

```bash
# Temporarily remove Perplexity key
unset PERPLEXITY_API_KEY
python backend/api/server_v7_mcp.py
```

**Expected Output**:
```
❌ PERPLEXITY_API_KEY not set or empty!
   Required for: Research Agent (web search & real-time data)
   Get your key from: https://www.perplexity.ai/api
```

### Test 4: Invalid Perplexity Key

```bash
export PERPLEXITY_API_KEY="invalid_key_12345"
python backend/api/server_v7_mcp.py
```

**Expected Output**:
```
❌ PERPLEXITY_API_KEY: Invalid - Authentication failed - invalid API key
   Update your key in: ~/.ki_autoagent/config/.env
```

---

## 📖 Setup Instructions

### 1. Get API Keys

**OpenAI (GPT-4o)**:
1. Go to https://platform.openai.com/api/keys
2. Create new secret key
3. Save it (can't view again!)

**Perplexity (Research)**:
1. Go to https://www.perplexity.ai/api
2. Create API key
3. Save it

### 2. Set Environment Variables

Create/edit `~/.ki_autoagent/config/.env`:

```bash
# Required API Keys
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxx
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxx
```

### 3. Test Validation

```bash
cd /Users/dominikfoert/git/KI_AutoAgent
source venv/bin/activate
python backend/api/server_v7_mcp.py
```

Look for:
```
✅ OPENAI_API_KEY: Valid
✅ PERPLEXITY_API_KEY: Valid
```

---

## 🔍 Troubleshooting

### Error: "Timeout - Check internet connection"

**Causes**:
- Perplexity API is slow
- Network connectivity issue
- API temporarily unavailable

**Solution**:
- Check internet connection: `ping api.perplexity.ai`
- Wait a few seconds and retry
- Check Perplexity API status page

### Error: "Authentication failed - invalid API key"

**Causes**:
- Wrong/expired Perplexity API key
- Key not copied correctly (spaces/typos)
- Key doesn't have necessary permissions

**Solution**:
1. Verify key at https://www.perplexity.ai/api
2. Regenerate new key if needed
3. Copy-paste carefully to ~/.ki_autoagent/config/.env
4. Restart server

### Error: "OpenAI package not installed"

**Solution**:
```bash
source venv/bin/activate
pip install -r backend/requirements.txt
```

---

## 📊 Performance Notes

**Validation Time**:
- OpenAI: ~1 second (API call + response)
- Perplexity: ~0.5-2 seconds
  - Normal: 300-500ms (HEAD request)
  - Slow: 3-8s (fallback to POST)
- **Total**: ~2-10 seconds on startup

This is acceptable because validation runs **only once at startup**, not per request.

---

## 🔐 Security Notes

1. **Never** commit API keys to git
2. **Never** log API key values (only validation status)
3. Store keys in `~/.ki_autoagent/config/.env` (user home only)
4. Regenerate keys if you suspect compromise
5. Use `.env.example` template for setup

---

## 📝 Maintenance

### When to Update This Guide

- [ ] New API validation added
- [ ] New required keys introduced
- [ ] Validation logic changes
- [ ] Error messages updated
- [ ] Status codes or endpoints change

### Related Files

- `backend/api/server_v7_mcp.py` (Main validation)
- `PYTHON_BEST_PRACTICES.md` (Error handling patterns)
- `backend/config/settings.py` (Configuration)
- `.env.example` (Template)

---

## ✅ Validation Checklist

Before deploying to production:

- [ ] Both API keys required and validated
- [ ] Specific exception handling (not bare `Exception`)
- [ ] Type hints on all functions
- [ ] Clear error messages with remediation steps
- [ ] Graceful handling of slow APIs (timeouts)
- [ ] Tests pass for valid/invalid keys
- [ ] Documentation updated
- [ ] No API keys logged in production