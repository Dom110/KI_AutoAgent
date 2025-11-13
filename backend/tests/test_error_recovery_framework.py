"""
🧪 Test Suite für Error Recovery Framework

Tests:
1. Klasifikation von verschiedenen Fehlertypen
2. Retry-Logik mit exponential backoff
3. Circuit Breaker Pattern
4. Async/Sync Execution
5. Permanent Error Detection
6. Transient Error Handling
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.error_recovery import (
    APIErrorType,
    CircuitBreaker,
    ErrorRecoveryConfig,
    ErrorRecoveryManager,
    ErrorStatus,
    PermanentError,
    TransientError,
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_error_recovery")


def print_test_header(test_num: int, title: str) -> None:
    """Print test header."""
    print(f"\n{'=' * 70}")
    print(f"🧪 TEST {test_num}: {title}")
    print('=' * 70)


def print_section(title: str) -> None:
    """Print section header."""
    print(f"\n📍 {title}")


# ============================================================================
# TEST 1: Error Klassifizierung
# ============================================================================

def test_1_error_classification():
    """Teste Error-Klassifizierung."""
    print_test_header(1, "Error Classification")
    
    manager = ErrorRecoveryManager()
    
    test_cases = [
        # (exception, message, expected_status, expected_type)
        (TimeoutError("Operation timed out"), "", ErrorStatus.TRANSIENT, APIErrorType.TIMEOUT),
        (Exception("timeout after 30s"), "", ErrorStatus.TRANSIENT, APIErrorType.TIMEOUT),
        (Exception("429 Too Many Requests"), "", ErrorStatus.TRANSIENT, APIErrorType.RATE_LIMIT),
        (Exception("rate limit exceeded"), "", ErrorStatus.TRANSIENT, APIErrorType.RATE_LIMIT),
        (ConnectionError("Connection refused"), "", ErrorStatus.TRANSIENT, APIErrorType.CONNECTION_ERROR),
        (Exception("503 Service Unavailable"), "", ErrorStatus.TRANSIENT, APIErrorType.SERVER_ERROR),
        (Exception("401 Unauthorized"), "", ErrorStatus.PERMANENT, APIErrorType.AUTH_ERROR),
        (Exception("Invalid API key"), "", ErrorStatus.PERMANENT, APIErrorType.AUTH_ERROR),
        (Exception("404 Not Found"), "", ErrorStatus.PERMANENT, APIErrorType.MODEL_NOT_FOUND),
        (Exception("400 Bad Request"), "", ErrorStatus.PERMANENT, APIErrorType.INVALID_REQUEST),
    ]
    
    passed = 0
    for exception, message, expected_status, expected_type in test_cases:
        status, error_type = manager.classify_error(exception, message)
        
        if status == expected_status and error_type == expected_type:
            print(f"   ✅ {type(exception).__name__} → {status.value}/{error_type.value}")
            passed += 1
        else:
            print(
                f"   ❌ {type(exception).__name__} → "
                f"Got {status.value}/{error_type.value}, "
                f"Expected {expected_status.value}/{expected_type.value}"
            )
    
    print(f"\n📊 Results: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


# ============================================================================
# TEST 2: Circuit Breaker Pattern
# ============================================================================

def test_2_circuit_breaker():
    """Teste Circuit Breaker Pattern."""
    print_test_header(2, "Circuit Breaker Pattern")
    
    config = ErrorRecoveryConfig(circuit_breaker_threshold=3)
    breaker = CircuitBreaker(config)
    
    print_section("Initial State")
    print(f"   Is available: {breaker.is_available()}")
    print(f"   Is open: {breaker.is_open}")
    print(f"   Failure count: {breaker.failure_count}")
    
    print_section("Record 3 Failures (threshold=3)")
    for i in range(3):
        breaker.record_failure()
        print(f"   Failure {i+1}: open={breaker.is_open}, count={breaker.failure_count}")
    
    print_section("After Threshold")
    available = breaker.is_available()
    print(f"   Is available: {available} (should be False)")
    
    print_section("Record Success")
    breaker.record_success()
    print(f"   After success: open={breaker.is_open}, available={breaker.is_available()}")
    
    success = (
        not available and
        breaker.is_open == False and
        breaker.failure_count == 0
    )
    
    print(f"\n✅ PASS" if success else f"\n❌ FAIL")
    return success


# ============================================================================
# TEST 3: Sync Retry with Transient Error
# ============================================================================

def test_3_sync_retry_transient():
    """Teste Sync Retry mit transienten Fehlern."""
    print_test_header(3, "Sync Retry - Transient Errors")
    
    config = ErrorRecoveryConfig(max_retries=3, initial_wait_ms=10)
    manager = ErrorRecoveryManager(config)
    
    attempt_count = 0
    
    def failing_fn():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            print(f"   Attempt {attempt_count}: Raising rate limit error")
            raise Exception("429 Too Many Requests")
        print(f"   Attempt {attempt_count}: Success!")
        return "success"
    
    print_section("Executing function that fails 2x then succeeds")
    try:
        result = manager.execute_with_retry_sync(
            failing_fn,
            context="test_transient_error"
        )
        print(f"   Result: {result}")
        print(f"   Total attempts: {attempt_count}")
        success = result == "success" and attempt_count == 3
        print(f"\n✅ PASS" if success else f"\n❌ FAIL")
        return success
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


# ============================================================================
# TEST 4: Sync Retry with Permanent Error
# ============================================================================

def test_4_sync_permanent_error():
    """Teste Sync Retry mit permanenten Fehlern."""
    print_test_header(4, "Sync Retry - Permanent Errors (should not retry)")
    
    config = ErrorRecoveryConfig(max_retries=3)
    manager = ErrorRecoveryManager(config)
    
    attempt_count = 0
    
    def auth_failing_fn():
        nonlocal attempt_count
        attempt_count += 1
        print(f"   Attempt {attempt_count}: Raising auth error")
        raise Exception("401 Unauthorized - Invalid API key")
    
    print_section("Executing function with permanent auth error")
    try:
        result = manager.execute_with_retry_sync(
            auth_failing_fn,
            context="test_permanent_error"
        )
        print(f"   ❌ Should have raised PermanentError")
        return False
    except PermanentError as e:
        print(f"   ✅ Caught PermanentError: {e.message[:50]}")
        print(f"   Attempts: {attempt_count} (should be 1)")
        success = attempt_count == 1
        print(f"\n✅ PASS" if success else f"\n❌ FAIL")
        return success
    except Exception as e:
        print(f"   ❌ Unexpected error type: {type(e).__name__}")
        return False


# ============================================================================
# TEST 5: Async Retry
# ============================================================================

async def test_5_async_retry():
    """Teste Async Retry."""
    print_test_header(5, "Async Retry - Transient Errors")
    
    config = ErrorRecoveryConfig(max_retries=2, initial_wait_ms=10)
    manager = ErrorRecoveryManager(config)
    
    attempt_count = 0
    
    async def async_failing_fn():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            print(f"   Attempt {attempt_count}: Raising connection error")
            raise ConnectionError("Connection refused")
        print(f"   Attempt {attempt_count}: Success!")
        return "async_success"
    
    print_section("Executing async function that fails then succeeds")
    try:
        result = await manager.execute_with_retry(
            async_failing_fn,
            context="test_async_retry"
        )
        print(f"   Result: {result}")
        print(f"   Total attempts: {attempt_count}")
        success = result == "async_success" and attempt_count == 2
        print(f"\n✅ PASS" if success else f"\n❌ FAIL")
        return success
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


# ============================================================================
# TEST 6: Timeout Handling
# ============================================================================

async def test_6_timeout_handling():
    """Teste Timeout-Handling."""
    print_test_header(6, "Timeout Handling")
    
    config = ErrorRecoveryConfig(max_retries=2, timeout_seconds=1)
    manager = ErrorRecoveryManager(config)
    
    async def slow_fn():
        print(f"   Sleeping for 2 seconds (timeout=1s)...")
        await asyncio.sleep(2)
        return "should_not_reach"
    
    print_section("Executing function that exceeds timeout")
    try:
        result = await manager.execute_with_retry(
            slow_fn,
            context="test_timeout",
            timeout_seconds=1
        )
        print(f"   ❌ Should have timed out")
        return False
    except TransientError as e:
        print(f"   ✅ Caught TransientError after timeout: {e.error_type.value}")
        print(f"\n✅ PASS")
        return True
    except Exception as e:
        print(f"   ⚠️  Caught {type(e).__name__}: {str(e)[:50]}")
        # Timeout ist auch akzeptabel
        if "timeout" in str(e).lower():
            print(f"✅ PASS (timeout detected)")
            return True
        return False


# ============================================================================
# TEST 7: Circuit Breaker Open State
# ============================================================================

def test_7_circuit_breaker_open():
    """Teste Circuit Breaker Open State (sollte requests ablehnen)."""
    print_test_header(7, "Circuit Breaker - Open State Rejection")
    
    config = ErrorRecoveryConfig(
        max_retries=1,
        circuit_breaker_threshold=2,
    )
    manager = ErrorRecoveryManager(config)
    
    print_section("Recording 2 failures to open circuit breaker")
    manager.circuit_breaker.record_failure()
    manager.circuit_breaker.record_failure()
    print(f"   Circuit breaker open: {manager.circuit_breaker.is_open}")
    
    print_section("Attempting to execute with open circuit breaker")
    def dummy_fn():
        return "should_not_reach"
    
    try:
        result = manager.execute_with_retry_sync(
            dummy_fn,
            context="test_circuit_open"
        )
        print(f"   ❌ Should have raised error")
        return False
    except PermanentError as e:
        if "Circuit Breaker open" in e.message:
            print(f"   ✅ Correctly rejected with: {e.message[:50]}")
            print(f"\n✅ PASS")
            return True
        else:
            print(f"   ❌ Wrong error message: {e.message}")
            return False


# ============================================================================
# TEST 8: Multiple Concurrent Requests
# ============================================================================

async def test_8_concurrent_requests():
    """Teste mehrere concurrent requests."""
    print_test_header(8, "Multiple Concurrent Requests")
    
    config = ErrorRecoveryConfig(max_retries=2, initial_wait_ms=5)
    manager = ErrorRecoveryManager(config)
    
    attempt_counts = [0, 0, 0]
    
    async def request_fn(request_id: int):
        attempt_counts[request_id] += 1
        if attempt_counts[request_id] < 2:
            raise Exception("503 Service Unavailable")
        return f"result_{request_id}"
    
    print_section("Executing 3 concurrent requests")
    try:
        results = await asyncio.gather(
            manager.execute_with_retry(
                request_fn, 0, context="request_1"
            ),
            manager.execute_with_retry(
                request_fn, 1, context="request_2"
            ),
            manager.execute_with_retry(
                request_fn, 2, context="request_3"
            ),
        )
        
        print(f"   Results: {results}")
        print(f"   Attempts: {attempt_counts}")
        
        success = (
            results == ["result_0", "result_1", "result_2"] and
            all(count == 2 for count in attempt_counts)
        )
        print(f"\n✅ PASS" if success else f"\n❌ FAIL")
        return success
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


# ============================================================================
# Main Test Runner
# ============================================================================

async def run_async_tests():
    """Führe alle async Tests aus."""
    tests = [
        ("5", await test_5_async_retry()),
        ("6", await test_6_timeout_handling()),
        ("8", await test_8_concurrent_requests()),
    ]
    return tests


def main():
    """Haupttest-Funktion."""
    print("\n" + "=" * 70)
    print("🧪 ERROR RECOVERY FRAMEWORK TEST SUITE (Phase 3c.1)")
    print("=" * 70)
    
    results = []
    
    # Synchrone Tests
    results.append(("1", test_1_error_classification()))
    results.append(("2", test_2_circuit_breaker()))
    results.append(("3", test_3_sync_retry_transient()))
    results.append(("4", test_4_sync_permanent_error()))
    results.append(("7", test_7_circuit_breaker_open()))
    
    # Async Tests
    async_results = asyncio.run(run_async_tests())
    results.extend(async_results)
    
    # Zusammenfassung
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_num, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   Test {test_num}: {status}")
    
    print(f"\n📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
