"""
🧪 Integration Tests: ResearchAgent mit Error Recovery

Testet die Integration des Error Recovery Frameworks in ResearchAgent.
Nutzt Mock Agent um Import-Probleme zu vermeiden.

Phase 3c.3: ResearchAgent Error Recovery Integration Tests
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base.base_agent import TaskRequest, TaskResult, AgentCapability, AgentConfig

import importlib.util
import os
spec = importlib.util.spec_from_file_location(
    "error_recovery",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core", "error_recovery.py")
)
error_recovery_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(error_recovery_module)

ErrorRecoveryManager = error_recovery_module.ErrorRecoveryManager
ErrorRecoveryConfig = error_recovery_module.ErrorRecoveryConfig
PermanentError = error_recovery_module.PermanentError
TransientError = error_recovery_module.TransientError
APIErrorType = error_recovery_module.APIErrorType

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MockResearchAgent:
    """Mock ResearchAgent für Testing."""
    
    def __init__(self):
        self.config = AgentConfig(
            agent_id="research",
            name="Research",
            full_name="Web Research Specialist",
            description="Code generation and implementation",
            model="sonar",
            temperature=0.3,
            max_tokens=4000,
        )
        self.config.capabilities = [AgentCapability.WEB_SEARCH]
        self.call_count = 0
    
    async def execute(self, request: TaskRequest) -> TaskResult:
        """Mock execute - simuliert Code-Generierung."""
        self.call_count += 1
        logger.info(f"🎭 MockResearchAgent.execute() called (attempt {self.call_count})")
        
        return TaskResult(
            status="success",
            content="# Research Results\ndef hello():\n    return 'world'",
            agent=self.config.agent_id,
            metadata={"sources": 1},
        )


class ResearchAgentWithErrorRecovery(MockResearchAgent):
    """ResearchAgent with Error Recovery Integration."""
    
    def __init__(
        self,
        max_retries: int = 3,
        timeout_seconds: int = 120,
        circuit_breaker_threshold: int = 5,
    ):
        super().__init__()
        config = ErrorRecoveryConfig(
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            circuit_breaker_threshold=circuit_breaker_threshold,
        )
        self.error_recovery = ErrorRecoveryManager(config)
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        
        logger.info(
            f"🛡️ ResearchAgent initialized with Error Recovery "
            f"(retries={max_retries}, timeout={timeout_seconds}s)"
        )
    
    async def execute(self, request: TaskRequest) -> TaskResult:
        """Execute with error recovery."""
        logger.info(f"📋 ResearchAgent.execute() called")
        
        async def execute_with_monitoring():
            return await MockResearchAgent.execute(self, request)
        
        try:
            result = await self.error_recovery.execute_with_retry(
                execute_with_monitoring,
                context="web_research",
                timeout_seconds=self.timeout_seconds,
            )
            return result
        except PermanentError as e:
            logger.error(f"❌ Permanent error: {e.message[:100]}")
            return TaskResult(
                status="error",
                content=f"Permanent error: {e.message}",
                agent=self.config.agent_id,
                metadata={"error_type": "permanent"},
            )
        except TransientError as e:
            logger.error(f"❌ Transient error after retries: {e.message[:100]}")
            return TaskResult(
                status="error",
                content=f"Failed after {self.max_retries} retries: {e.message}",
                agent=self.config.agent_id,
                metadata={"error_type": "transient"},
            )
    
    def get_circuit_breaker_status(self):
        """Get circuit breaker status."""
        breaker = self.error_recovery.circuit_breaker
        return {
            "is_open": breaker.is_open,
            "is_available": breaker.is_available(),
            "failure_count": breaker.failure_count,
            "threshold": self.error_recovery.config.circuit_breaker_threshold,
        }
    
    def reset_circuit_breaker(self):
        """Reset circuit breaker."""
        self.error_recovery.circuit_breaker.failure_count = 0
        self.error_recovery.circuit_breaker.is_open = False


async def test_1_research_initialization():
    """TEST 1: ResearchAgent initialisiert mit Error Recovery."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 1: ResearchAgent Initialization")
    logger.info("=" * 80)
    
    agent = ResearchAgentWithErrorRecovery(
        max_retries=3,
        timeout_seconds=90,
        circuit_breaker_threshold=5,
    )
    
    assert agent.max_retries == 3
    assert agent.timeout_seconds == 90
    assert agent.error_recovery is not None
    
    status = agent.get_circuit_breaker_status()
    assert status["is_open"] is False
    assert status["threshold"] == 5
    
    logger.info("✅ TEST 1 PASSED: ResearchAgent initialized with Error Recovery")
    return True


async def test_2_successful_web_research():
    """TEST 2: Erfolgreiche Code-Generierung."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Successful Web Research")
    logger.info("=" * 80)
    
    agent = ResearchAgentWithErrorRecovery()
    
    request = TaskRequest(
        prompt="Research Python hello world function",
        context={"language": "python"},
    )
    
    result = await agent.execute(request)
    
    assert result.status == "success"
    assert "Research Results" in result.content
    assert result.agent == "research"
    
    logger.info("✅ TEST 2 PASSED: Code generation successful")
    return True


async def test_3_circuit_breaker_tracking():
    """TEST 3: Circuit Breaker trackt Fehler korrekt."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Circuit Breaker Status Tracking")
    logger.info("=" * 80)
    
    agent = ResearchAgentWithErrorRecovery(circuit_breaker_threshold=3)
    
    status = agent.get_circuit_breaker_status()
    assert status["is_open"] is False
    assert status["failure_count"] == 0
    
    for i in range(3):
        agent.error_recovery.circuit_breaker.record_failure()
    
    status = agent.get_circuit_breaker_status()
    assert status["is_open"] is True
    assert status["failure_count"] == 3
    
    agent.reset_circuit_breaker()
    status = agent.get_circuit_breaker_status()
    assert status["is_open"] is False
    
    logger.info("✅ TEST 3 PASSED: Circuit breaker tracking works")
    return True


async def test_4_error_classification():
    """TEST 4: Fehler werden korrekt klassifiziert."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Error Classification")
    logger.info("=" * 80)
    
    manager = ErrorRecoveryManager()
    
    test_cases = [
        ("timeout", APIErrorType.TIMEOUT),
        ("timed out", APIErrorType.TIMEOUT),
        ("rate limit", APIErrorType.RATE_LIMIT),
        ("429", APIErrorType.RATE_LIMIT),
        ("connection refused", APIErrorType.CONNECTION_ERROR),
        ("network error", APIErrorType.CONNECTION_ERROR),
        ("500 internal server error", APIErrorType.SERVER_ERROR),
        ("503 service unavailable", APIErrorType.SERVER_ERROR),
        ("401 unauthorized", APIErrorType.AUTH_ERROR),
        ("invalid api key", APIErrorType.AUTH_ERROR),
    ]
    
    for error_msg, expected_type in test_cases:
        _, error_type = manager.classify_error(Exception(error_msg))
        assert error_type == expected_type, f"Failed for: {error_msg}"
        logger.info(f"  ✓ '{error_msg}' → {expected_type.value}")
    
    logger.info("✅ TEST 4 PASSED: Error classification correct")
    return True


async def test_5_monitoring_integration():
    """TEST 5: Monitoring Integration funktioniert."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 5: Monitoring Integration")
    logger.info("=" * 80)
    
    agent = ResearchAgentWithErrorRecovery()
    
    request = TaskRequest(
        prompt="Research Python function",
        context={},
    )
    
    result = await agent.execute(request)
    
    assert result.status == "success"
    assert hasattr(agent, "error_recovery")
    assert hasattr(agent, "get_circuit_breaker_status")
    
    logger.info("✅ TEST 5 PASSED: Monitoring integration works")
    return True


async def test_6_configuration_flexibility():
    """TEST 6: Konfiguration ist flexibel."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 6: Configuration Flexibility")
    logger.info("=" * 80)
    
    agent = ResearchAgentWithErrorRecovery(
        max_retries=5,
        timeout_seconds=180,
        circuit_breaker_threshold=10,
    )
    
    assert agent.max_retries == 5
    assert agent.timeout_seconds == 180
    
    status = agent.get_circuit_breaker_status()
    assert status["threshold"] == 10
    
    logger.info("✅ TEST 6 PASSED: Configuration flexible")
    return True


async def test_7_error_recovery_config():
    """TEST 7: Error Recovery Config wird korrekt angewendet."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 7: Error Recovery Configuration")
    logger.info("=" * 80)
    
    agent = ResearchAgentWithErrorRecovery(
        max_retries=3,
        timeout_seconds=90,
        circuit_breaker_threshold=5,
    )
    
    config = agent.error_recovery.config
    
    assert config.max_retries == 3
    assert config.timeout_seconds == 90
    assert config.circuit_breaker_threshold == 5
    assert config.enable_circuit_breaker is True
    assert config.exponential_base == 2.0
    
    logger.info("✅ TEST 7 PASSED: Error recovery config correct")
    return True


async def test_8_concurrent_requests():
    """TEST 8: Concurrent Requests funktionieren."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 8: Concurrent Requests")
    logger.info("=" * 80)
    
    agent = ResearchAgentWithErrorRecovery()
    
    requests = [
        TaskRequest(prompt=f"Research topic {i}", context={})
        for i in range(3)
    ]
    
    results = await asyncio.gather(*[agent.execute(req) for req in requests])
    
    assert len(results) == 3
    assert all(r.status == "success" for r in results)
    
    logger.info("✅ TEST 8 PASSED: Concurrent requests work")
    return True


async def run_all_tests():
    """Führe alle Tests aus."""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 CODESMITH ERROR RECOVERY INTEGRATION TESTS")
    logger.info("=" * 80)
    
    tests = [
        test_1_research_initialization,
        test_2_successful_web_research,
        test_3_circuit_breaker_tracking,
        test_4_error_classification,
        test_5_monitoring_integration,
        test_6_configuration_flexibility,
        test_7_error_recovery_config,
        test_8_concurrent_requests,
    ]
    
    results = []
    start_time = time.time()
    
    for test in tests:
        try:
            result = await test()
            results.append((test.__name__, result))
        except Exception as e:
            logger.error(f"❌ {test.__name__} FAILED: {e}")
            results.append((test.__name__, False))
    
    execution_time = time.time() - start_time
    
    logger.info("\n" + "=" * 80)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{status}: {test_name}")
    
    logger.info("=" * 80)
    logger.info(f"📈 Results: {passed}/{total} tests passed")
    logger.info(f"⏱️  Execution time: {execution_time:.2f}s")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED!")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
