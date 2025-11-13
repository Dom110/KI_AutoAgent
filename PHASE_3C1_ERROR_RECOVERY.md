# 🛡️ Phase 3c.1: Error Recovery & Resilience Framework

**Version:** 1.0.0  
**Date:** 2025-11-10  
**Status:** ✅ COMPLETE - All tests passing  
**Tests:** 8/8 ✅ | Prometheus: 7/7 ✅  

---

## 📋 Overview

Phase 3c.1 adds comprehensive **error recovery** and **resilience** to the LLM Monitoring system. The framework handles transient vs permanent errors, implements retry logic with exponential backoff, circuit breaker pattern, and timeout handling.

**Key Features:**
- 🔄 Automatic retry with exponential backoff (tenacity library)
- 🔴 Circuit Breaker pattern to prevent cascading failures
- ⏱️ Timeout handling for slow APIs
- 🎯 Error classification (transient vs permanent)
- 📊 Detailed logging for debugging
- ✨ Graceful degradation strategies

---

## 📂 Files Added

### Core Implementation
- **`backend/core/error_recovery.py`** (+520 lines)
  - `ErrorRecoveryManager` - Main orchestrator
  - `CircuitBreaker` - Prevents cascading failures
  - `ErrorStatus` enum (TRANSIENT, PERMANENT, DEGRADED)
  - `APIErrorType` enum (TIMEOUT, RATE_LIMIT, AUTH_ERROR, etc.)
  - `TransientError`, `PermanentError` exceptions

### Tests
- **`backend/tests/test_error_recovery_framework.py`** (+600 lines)
  - Test 1: Error classification (10 different scenarios)
  - Test 2: Circuit Breaker pattern
  - Test 3: Sync retry with transient errors
  - Test 4: Sync retry with permanent errors
  - Test 5: Async retry
  - Test 6: Timeout handling
  - Test 7: Circuit Breaker open state
  - Test 8: Multiple concurrent requests

---

## 🧪 Test Results

### Error Recovery Tests (8/8 ✅)

```
✅ TEST 1: Error Classification (10/10 cases)
   TimeoutError → transient/timeout
   Exception → transient/timeout
   "429 Too Many Requests" → transient/rate_limit
   ConnectionError → transient/connection_error
   "503 Service Unavailable" → transient/server_error
   "401 Unauthorized" → permanent/auth_error
   "404 Not Found" → permanent/model_not_found
   "400 Bad Request" → permanent/invalid_request

✅ TEST 2: Circuit Breaker Pattern
   Records failures and opens after threshold
   Prevents requests when open
   Resets on success

✅ TEST 3: Sync Retry - Transient Errors
   Function fails 2x with rate limit
   Succeeds on 3rd attempt
   No premature failure

✅ TEST 4: Sync Retry - Permanent Errors
   Auth error detected on 1st attempt
   Raises PermanentError immediately
   NO further retries

✅ TEST 5: Async Retry
   Connection error on attempt 1
   Success on attempt 2
   Works with async/await

✅ TEST 6: Timeout Handling
   Function takes 2 seconds (timeout=1s)
   Catches after 2 timeout retries
   Raises TransientError with proper classification

✅ TEST 7: Circuit Breaker Open State
   Circuit open after 2+ failures
   Rejects new requests with PermanentError
   Message: "Circuit Breaker open"

✅ TEST 8: Multiple Concurrent Requests
   3 concurrent requests (each fails once)
   All succeed on 2nd attempt
   Concurrent-safe

Results: 8/8 tests passed ✅
```

### Prometheus Integration (7/7 ✅)
- Metrics export working
- Counter increments correct
- Gauge updates correct
- Histogram buckets working
- Label handling correct
- Multiple agents tracked
- All tests passing

---

## 🔧 How to Use

### Basic Setup

```python
from backend.core.error_recovery import (
    ErrorRecoveryManager,
    ErrorRecoveryConfig,
    PermanentError,
    TransientError,
)

# Create manager with custom config
config = ErrorRecoveryConfig(
    max_retries=3,
    initial_wait_ms=100,
    max_wait_ms=10000,
    exponential_base=2.0,
    timeout_seconds=30,
)
manager = ErrorRecoveryManager(config)
```

### Async API Calls

```python
async def make_api_call():
    """Example async function."""
    response = await api_client.complete(...)
    return response

# Execute with automatic retry
try:
    result = await manager.execute_with_retry(
        make_api_call,
        context="code_review_request",
        timeout_seconds=30
    )
except PermanentError as e:
    logger.error(f"Not retrying - permanent error: {e.message}")
except TransientError as e:
    logger.error(f"Failed after retries: {e.message}")
    logger.info(f"Error type: {e.error_type.value}")
```

### Sync API Calls

```python
def make_sync_call():
    """Example sync function."""
    response = requests.post(...)
    return response.json()

# Execute with automatic retry
try:
    result = manager.execute_with_retry_sync(
        make_sync_call,
        context="validation_request"
    )
except PermanentError as e:
    logger.error(f"Not retrying: {e.message}")
except TransientError as e:
    logger.error(f"Failed after retries: {e.message}")
```

---

## 🎯 Error Classification

### Transient Errors (Retryable)

These errors are temporary and worth retrying:

| Error Type | Examples | Behavior |
|-----------|----------|----------|
| **TIMEOUT** | TimeoutError, "timed out" | Retry with backoff |
| **RATE_LIMIT** | 429, "rate limit" | Retry with exponential backoff |
| **CONNECTION_ERROR** | ConnectionRefusedError, "connection refused" | Retry with backoff |
| **SERVER_ERROR** | 500, 502, 503, "server error" | Retry with backoff |

### Permanent Errors (Non-Retryable)

These errors won't be fixed by retrying:

| Error Type | Examples | Behavior |
|-----------|----------|----------|
| **AUTH_ERROR** | 401, "invalid api key" | Fail immediately |
| **INVALID_REQUEST** | 400, "malformed" | Fail immediately |
| **MODEL_NOT_FOUND** | 404, "model not found" | Fail immediately |

---

## 🔄 Retry Logic with Exponential Backoff

### Default Configuration

```python
max_retries=3              # Max 3 attempts
initial_wait_ms=100       # Start with 100ms
max_wait_ms=10000         # Cap at 10 seconds
exponential_base=2.0      # Double each time

# Wait times:
# Retry 1: 100ms
# Retry 2: 200ms
# Retry 3: 400ms
# (capped at max_wait_ms)
```

### Timeline Example

```
Attempt 1: t=0ms
  ├─ Call API → Fails with 503
  ├─ Classify: transient/server_error
  └─ Wait 100ms
    
Attempt 2: t=100ms
  ├─ Call API → Fails with timeout
  ├─ Classify: transient/timeout
  └─ Wait 200ms
    
Attempt 3: t=300ms
  ├─ Call API → Success!
  ├─ Return result
  └─ ✅ Total time: 300ms
```

---

## 🔴 Circuit Breaker Pattern

Prevents cascading failures by tracking error rates:

### Configuration

```python
config = ErrorRecoveryConfig(
    circuit_breaker_threshold=5,        # Open after 5 failures
    circuit_breaker_timeout_seconds=60, # Try again after 60s
)
```

### States

```
CLOSED (Normal)
  │
  ├─ Requests pass through ✅
  ├─ Failures counted
  └─ If failures >= threshold → OPEN

OPEN (Failing)
  │
  ├─ Requests rejected immediately ❌
  ├─ Error: "Circuit Breaker open"
  └─ After timeout → HALF_OPEN

HALF_OPEN (Testing)
  │
  ├─ Single request allowed
  ├─ Success → CLOSED ✅
  └─ Failure → OPEN ❌
```

---

## ⏱️ Timeout Handling

Each retry attempt has its own timeout:

```python
# Per-attempt timeout: 30 seconds
await manager.execute_with_retry(
    api_call,
    timeout_seconds=30
)

# Function takes 2 seconds:
# Attempt 1: t=0s, waits 2s → Success by t=2s
# Attempt 1: t=0s, waits 35s → Timeout after 30s → Retry
# Attempt 2: t=wait_time, waits 2s → Success
```

---

## 📊 Logging Output

### Success Case

```
🔄 Attempt 1/3 for code_review_request
📤 Sending request...
✅ code_review_request succeeded on attempt 1
```

### Transient Error Case

```
🔄 Attempt 1/3 for code_review_request
⚠️  Attempt 1 failed (rate_limit): 429 Too Many Requests
🔄 Attempt 2/3 for code_review_request
✅ code_review_request succeeded on attempt 2
```

### Permanent Error Case

```
🔄 Attempt 1/3 for auth_check
⚠️  Attempt 1 failed (auth_error): 401 Unauthorized - Invalid API key
❌ auth_check failed after permanent error
Error: PermanentError - not retrying
```

### Circuit Breaker Case

```
🔴 Circuit Breaker OPEN (failures: 5)
❌ Circuit Breaker open - rejecting request
Error: PermanentError - Circuit Breaker is open
```

---

## 🚀 Integration with Agents

### Example: ReviewerGPT Agent

```python
from backend.core.error_recovery import ErrorRecoveryManager
from backend.core.llm_monitoring import monitor_llm_call

class ReviewerGPTAgent:
    def __init__(self):
        self.error_recovery = ErrorRecoveryManager()
    
    async def review_code(self, code: str):
        async def call_llm():
            prompt = f"Review this code:\n{code}"
            response = await self.ai_service.complete(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
            )
            return response
        
        try:
            # Execute with retry and monitoring
            response = await self.error_recovery.execute_with_retry(
                call_llm,
                context="code_review",
                timeout_seconds=60
            )
            
            # Monitor the call
            with monitor_llm_call(
                agent_name="ReviewerGPT",
                provider="openai",
                model="gpt-4o"
            ):
                return response
        
        except PermanentError as e:
            logger.error(f"Auth or validation error: {e.message}")
            raise
        except TransientError as e:
            logger.error(f"Transient error after retries: {e.message}")
            raise
```

---

## 🐛 Debugging & Troubleshooting

### Enable Debug Logging

```python
import logging

logger = logging.getLogger("agent.error_recovery_manager")
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))
logger.addHandler(handler)
```

### Check Circuit Breaker Status

```python
manager = ErrorRecoveryManager()

# Check status
print(f"Open: {manager.circuit_breaker.is_open}")
print(f"Available: {manager.circuit_breaker.is_available()}")
print(f"Failures: {manager.circuit_breaker.failure_count}")

# Manually reset
manager.circuit_breaker.failure_count = 0
manager.circuit_breaker.is_open = False
```

### Customize Retry Config

```python
config = ErrorRecoveryConfig(
    max_retries=5,              # More retries for flaky APIs
    initial_wait_ms=50,         # Faster backoff for fast APIs
    max_wait_ms=5000,          # Cap at 5s for fast recovery
    timeout_seconds=60,         # Longer timeout for slow APIs
    circuit_breaker_threshold=10,  # More tolerance before open
)
manager = ErrorRecoveryManager(config)
```

---

## 🔗 Integration Checklist

Before deploying to production:

- [ ] Error recovery tests pass (8/8)
- [ ] Prometheus tests pass (7/7)
- [ ] Agent integration complete
- [ ] Logging configured
- [ ] Circuit breaker thresholds tuned for your APIs
- [ ] Timeout values appropriate for your latency SLA
- [ ] Error classifications tested with real API errors
- [ ] No secrets in debug logs
- [ ] Production load tests completed

---

## 📝 Related Files

- **Implementation**: `backend/core/error_recovery.py`
- **Tests**: `backend/tests/test_error_recovery_framework.py`
- **Monitoring**: `backend/core/llm_monitoring.py`
- **Prometheus**: PHASE_3C_PROMETHEUS_INTEGRATION.md
- **Best Practices**: /PYTHON_BEST_PRACTICES.md

---

## ✅ Success Metrics

✅ All error types correctly classified  
✅ Transient errors retried automatically  
✅ Permanent errors fail fast without retries  
✅ Circuit breaker prevents cascading failures  
✅ Timeout handling works for slow APIs  
✅ Concurrent requests handled safely  
✅ Detailed logging for debugging  
✅ Zero security/secret leaks in logs  

---

## 🎯 Next Steps (Phase 3c.2)

- [ ] Integrate error recovery into all agents
- [ ] Add error recovery to Perplexity search
- [ ] Add error recovery to OpenAI API calls
- [ ] Add error recovery to file operations
- [ ] Implement metrics for retry success rates
- [ ] Add dashboard visualization for circuit breaker status
- [ ] Performance optimization for high-concurrency scenarios

