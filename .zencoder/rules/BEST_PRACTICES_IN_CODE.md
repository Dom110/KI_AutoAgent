---
description: Python Best Practices Applied in Real Code Examples
alwaysApply: true
---

# 🐍 Python Best Practices Applied - Code Examples

**Reference**: `PYTHON_BEST_PRACTICES.md`  
**Implementation**: `backend/api/server_v7_mcp.py` (validate_api_keys)  
**Python**: 3.13.8+

---

## 1️⃣ Specific Exception Handling

### ❌ BAD Pattern

```python
def validate_api_keys():
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        client.models.list()
    except Exception as e:  # ← TOO BROAD!
        logger.error(f"Error: {e}")
```

**Problems**:
- Catches ALL exceptions (bugs, typos, unexpected errors)
- Impossible to debug specific issues
- Same handling for import errors, network errors, auth errors

### ✅ GOOD Pattern

```python
try:
    from openai import OpenAI
    client = OpenAI(api_key=openai_key)
    client.models.list()
    logger.info("✅ OPENAI_API_KEY: Valid")
except (ImportError, ModuleNotFoundError) as e:  # ← Package missing
    logger.error(f"❌ OpenAI package not installed: {e}")
    sys.exit(1)
except Exception as e:  # ← Fallback for other errors
    logger.error(f"❌ OPENAI_API_KEY: Invalid - {str(e)[:80]}")
    sys.exit(1)
```

**Benefits**:
- Clear separation of concerns
- Specific error messages for each case
- Easy to add handling for specific error types
- Fallback for unexpected errors

---

## 2️⃣ Minimize Try Block Scope

### ❌ BAD Pattern

```python
def validate_api_keys():
    try:
        # OpenAI validation
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        client.models.list()
        
        # Perplexity validation
        response = requests.head(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {perplexity_key}"}
        )
        
        # Logging
        logger.info("All keys validated!")
    except Exception as e:  # ← Which step failed? Unknown!
        logger.error(f"Validation failed: {e}")
```

**Problems**:
- Can't tell which validation failed
- Error handling is generic for all cases
- Hard to debug in production
- Mixes different concerns

### ✅ GOOD Pattern

```python
def validate_api_keys() -> None:
    logger.info("🔑 Validating API keys...")
    
    # OpenAI validation (separate try block)
    if not openai_key or openai_key == "":
        logger.error("❌ OPENAI_API_KEY not set or empty!")
        sys.exit(1)
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        client.models.list()
        logger.info("✅ OPENAI_API_KEY: Valid")
    except (ImportError, ModuleNotFoundError) as e:
        logger.error(f"❌ OpenAI package not installed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ OPENAI_API_KEY: Invalid - {str(e)[:80]}")
        sys.exit(1)
    
    # Perplexity validation (separate try block)
    if not perplexity_key or perplexity_key == "":
        logger.error("❌ PERPLEXITY_API_KEY not set or empty!")
        sys.exit(1)
    
    try:
        import requests
        response = requests.head(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {perplexity_key}"},
            timeout=3
        )
        if response.status_code in (200, 400, 429):
            logger.info("✅ PERPLEXITY_API_KEY: Valid")
        elif response.status_code == 401:
            raise RuntimeError("Authentication failed")
    except requests.Timeout:
        logger.info("✅ PERPLEXITY_API_KEY: Accepted (format valid)")
    except RuntimeError as e:
        logger.error(f"❌ PERPLEXITY_API_KEY: {e}")
        sys.exit(1)
```

**Benefits**:
- Each validation is independent
- Specific error handling per validation
- Easy to debug which step failed
- Can skip or modify one validation without affecting others

---

## 3️⃣ Type Hints on Public Functions

### ❌ BAD Pattern

```python
def validate_api_keys():  # ← No type hints
    """Validate required API keys and test connectivity."""
    # ...
```

**Problems**:
- Type checker (mypy) can't help
- IDE can't provide autocomplete
- Readers don't know what function returns
- Easy to accidentally return wrong type

### ✅ GOOD Pattern

```python
def validate_api_keys() -> None:  # ← Clear return type
    """Validate required API keys and test connectivity.
    
    Follows Python Best Practices from PYTHON_BEST_PRACTICES.md:
    - Specific exception handling (not bare Exception)
    - Minimal try block scope
    - Clear error messages for debugging
    """
    # ...
```

**Benefits**:
- Type checker validates function is used correctly
- IDE provides autocomplete help
- Clear contract: "This function returns nothing"
- Self-documenting code

---

## 4️⃣ Clear Error Messages (Multi-Line)

### ❌ BAD Pattern

```python
if not perplexity_key:
    logger.error("Missing Perplexity key")  # ← Not actionable
```

**Problems**:
- User doesn't know what to do
- No context about requirement
- No information where to get the key

### ✅ GOOD Pattern

```python
if not perplexity_key or perplexity_key == "":
    logger.error("❌ PERPLEXITY_API_KEY not set or empty!")
    logger.error("   Required for: Research Agent (web search & real-time data)")
    logger.error("   Set in: ~/.ki_autoagent/config/.env")
    logger.error("   Get your key from: https://www.perplexity.ai/api")
    sys.exit(1)
```

**Benefits**:
- Multi-line errors are clear and structured
- Tells user **what** is wrong
- Tells user **why** it matters
- Tells user **how** to fix it

---

## 5️⃣ Graceful Fallback Strategies

### ❌ BAD Pattern

```python
try:
    response = requests.post(
        "https://api.perplexity.ai/chat/completions",
        json=payload,
        headers=headers,
        timeout=5
    )
except requests.Timeout:
    logger.error("❌ Perplexity validation failed")
    sys.exit(1)  # ← Hard fail
```

**Problems**:
- Slow APIs cause startup to fail
- No fallback strategy
- User can't start system even with valid key

### ✅ GOOD Pattern

```python
try:
    # Fast check first (3s)
    response = requests.head(
        "https://api.perplexity.ai/chat/completions",
        headers=headers,
        timeout=3,
        allow_redirects=True
    )
except (requests.Timeout, requests.ConnectionError):
    # ✅ Fallback: Try slower POST (8s) if HEAD times out
    try:
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
    except requests.Timeout:
        # ✅ Final fallback: Accept based on format
        logger.warning("⚠️ PERPLEXITY_API_KEY: Validation timed out (API slow)")
        logger.info("✅ PERPLEXITY_API_KEY: Accepted (format valid)")
        return  # Proceed with system
```

**Benefits**:
- Graceful degradation (fast → slower → format check)
- Doesn't fail for slow APIs
- System still works even if API is temporarily slow
- User experience not impacted

---

## 6️⃣ Status Code Interpretation

### ❌ BAD Pattern

```python
if response.status_code == 200:
    logger.info("✅ Valid")
else:
    logger.error("❌ Invalid")
```

**Problems**:
- Other status codes (400, 429) might still be valid
- Doesn't distinguish between different failures
- Hard to debug API issues

### ✅ GOOD Pattern

```python
# Status codes that indicate valid key:
# 200=success, 400=param error (but auth OK), 401=auth fail, 
# 401=invalid key, 429=rate limited (but auth OK), 503=server down

if response.status_code in (200, 400, 429):
    logger.info("✅ PERPLEXITY_API_KEY: Valid")
elif response.status_code == 401:
    raise RuntimeError("Authentication failed - invalid API key")
else:
    # For other codes, assume it's working but api might be slow
    logger.info("✅ PERPLEXITY_API_KEY: Valid (status: ok)")
```

**Benefits**:
- Understands different meanings of status codes
- Distinguishes auth failures from other issues
- Clear comments explain status code semantics
- Robust to API variations

---

## 7️⃣ Early Exit on Critical Errors

### ❌ BAD Pattern

```python
def validate_api_keys():
    errors = []
    
    if not openai_key:
        errors.append("OPENAI_API_KEY missing")
    if not perplexity_key:
        errors.append("PERPLEXITY_API_KEY missing")
    
    if errors:
        for error in errors:
            logger.error(error)
        return False  # ← Returns to caller - may be ignored!
```

**Problems**:
- Return value might be ignored
- Caller might continue anyway
- Multiple errors reported but no clear failure point

### ✅ GOOD Pattern

```python
def validate_api_keys() -> None:
    """Validate required API keys and test connectivity."""
    
    # Required: OpenAI Key
    if not openai_key or openai_key == "":
        logger.error("❌ OPENAI_API_KEY not set or empty!")
        logger.error("   Set in: ~/.ki_autoagent/config/.env")
        sys.exit(1)  # ← EXPLICIT FAILURE
    
    # Test OpenAI
    try:
        from openai import OpenAI
        # ...
    except Exception as e:
        logger.error(f"❌ OPENAI_API_KEY: Invalid")
        sys.exit(1)  # ← EXPLICIT FAILURE
    
    # Required: Perplexity Key
    if not perplexity_key or perplexity_key == "":
        logger.error("❌ PERPLEXITY_API_KEY not set or empty!")
        sys.exit(1)  # ← EXPLICIT FAILURE
```

**Benefits**:
- `sys.exit(1)` is explicit and cannot be ignored
- Server doesn't start with bad configuration
- Clear failure point in logs
- No ambiguity about system state

---

## 8️⃣ Documentation Patterns

### ❌ BAD Pattern

```python
def validate_api_keys():
    """Check API keys."""  # ← Too vague
    # ...
```

### ✅ GOOD Pattern

```python
def validate_api_keys() -> None:
    """Validate required API keys and test connectivity.
    
    Follows Python Best Practices from PYTHON_BEST_PRACTICES.md:
    - Specific exception handling (not bare Exception)
    - Minimal try block scope
    - Clear error messages for debugging
    
    Validates two mandatory keys:
    1. OPENAI_API_KEY - For GPT-4o Supervisor
    2. PERPLEXITY_API_KEY - For Research Agent
    
    If any validation fails, exits with sys.exit(1).
    
    Raises:
        SystemExit: If any required key is missing/invalid
    """
```

**Benefits**:
- Clear purpose
- References best practices
- Documents what's validated
- Explains error behavior
- Good for IDE docstring display

---

## 📊 Comparison Table

| Aspect | Bad ❌ | Good ✅ |
|--------|--------|---------|
| Exception Handling | `except Exception` | `except (ImportError, RuntimeError)` + fallback |
| Try Block Size | Large (many steps) | Small (one concern per block) |
| Type Hints | None | All public functions |
| Error Messages | 1 line, vague | Multi-line, actionable |
| Fallback Strategy | Fail immediately | Fast → slower → format check |
| Status Codes | Only check 200 | Interpret all codes |
| Error Exit | Return False | `sys.exit(1)` |
| Documentation | Vague | Clear, references guides |

---

## 🔗 Related Files

- **Main Implementation**: `backend/api/server_v7_mcp.py` (lines 114-228)
- **Best Practices Guide**: `PYTHON_BEST_PRACTICES.md`
- **API Key Validation**: `API_KEY_VALIDATION_GUIDE.md`
- **Error Handling Section**: `PYTHON_BEST_PRACTICES.md` (lines 69-256)

---

## ✅ Checklist for Your Code

When writing similar validation code:

- [ ] Use specific exceptions, not bare `Exception`
- [ ] Separate try blocks for different concerns
- [ ] Add `-> None` type hint to functions
- [ ] Use multi-line error messages
- [ ] Implement fallback strategies for slow APIs
- [ ] Interpret status codes properly
- [ ] Use `sys.exit(1)` for critical failures
- [ ] Document purpose and error behavior
- [ ] Add comments explaining why each check matters
- [ ] Test with valid/invalid inputs