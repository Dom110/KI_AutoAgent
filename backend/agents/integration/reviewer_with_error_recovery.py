"""
🛡️ ReviewerGPT Agent mit Error Recovery Integration

Erweitert ReviewerGPT Agent mit:
- Automatisches Retry bei transienten Fehlern
- Circuit Breaker zur Fehlerprävention
- Detailliertes Logging
- Monitoring von Fehlern und Recovery

Phase 3c.2: Error Recovery Framework Integration
"""

import logging
from typing import Any, Optional

from backend.agents.specialized.reviewer_gpt_agent import ReviewerGPTAgent
from backend.agents.base.base_agent import TaskRequest, TaskResult
from backend.core.error_recovery import (
    ErrorRecoveryManager,
    ErrorRecoveryConfig,
    PermanentError,
    TransientError,
)
from backend.core.llm_monitoring import monitor_llm_call

logger = logging.getLogger(__name__)


class ReviewerGPTWithErrorRecovery(ReviewerGPTAgent):
    """
    ReviewerGPT Agent mit integrierten Error Recovery Fähigkeiten.
    
    Features:
    - Automatisches Retry auf API Fehler
    - Circuit Breaker bei hohen Fehlerraten
    - Timeout-Management per Attempt
    - Umfassendes Logging für Debugging
    - Monitoring und Metriken Integration
    
    Beispiel:
        agent = ReviewerGPTWithErrorRecovery()
        result = await agent.execute(request)
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        timeout_seconds: int = 60,
        circuit_breaker_threshold: int = 5,
    ):
        """
        Initialize ReviewerGPT with Error Recovery.
        
        Args:
            max_retries: Max retry attempts for transient errors
            timeout_seconds: Timeout per attempt
            circuit_breaker_threshold: Failures before circuit opens
        """
        super().__init__()
        
        # Konfiguriere Error Recovery
        config = ErrorRecoveryConfig(
            max_retries=max_retries,
            initial_wait_ms=100,
            max_wait_ms=10000,
            exponential_base=2.0,
            timeout_seconds=timeout_seconds,
            enable_circuit_breaker=True,
            circuit_breaker_threshold=circuit_breaker_threshold,
            circuit_breaker_timeout_seconds=60,
        )
        
        self.error_recovery = ErrorRecoveryManager(config)
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        
        logger.info(
            f"🛡️  ReviewerGPT initialized with Error Recovery "
            f"(retries={max_retries}, timeout={timeout_seconds}s, "
            f"circuit_threshold={circuit_breaker_threshold})"
        )
    
    async def execute(self, request: TaskRequest) -> TaskResult:
        """
        Execute code review mit Error Recovery.
        
        Strategy:
        1. Überprüfe Circuit Breaker Status
        2. Führe Review mit Error Recovery aus
        3. Klassifiziere Fehler und entscheide Retry
        4. Monitore Performanz
        
        Args:
            request: TaskRequest mit Code zum Review
            
        Returns:
            TaskResult mit Review oder Fehler
        """
        
        logger.info(
            f"📋 ReviewerGPT.execute() called "
            f"(code_len={len(request.prompt)}, request_id={request.request_id})"
        )
        
        # Erstelle async Wrapper für Parent execute
        async def execute_with_monitoring():
            """Führe Parent execute aus mit Monitoring."""
            with monitor_llm_call(
                agent_name="ReviewerGPT",
                provider="openai",
                model=self.config.model,
                request_id=request.request_id,
            ):
                return await super(ReviewerGPTWithErrorRecovery, self).execute(request)
        
        try:
            # Führe mit Error Recovery aus
            logger.info(f"🔄 Starting review with error recovery (max_retries={self.max_retries})")
            
            result = await self.error_recovery.execute_with_retry(
                execute_with_monitoring,
                context=f"code_review_{request.request_id}",
                timeout_seconds=self.timeout_seconds,
            )
            
            logger.info(
                f"✅ ReviewerGPT.execute() succeeded "
                f"(result_len={len(result.content)}, request_id={request.request_id})"
            )
            
            return result
        
        except PermanentError as e:
            logger.error(
                f"❌ ReviewerGPT permanent error (not retrying): {e.message[:100]}"
            )
            return TaskResult(
                status="error",
                content=f"Permanent error: {e.message}",
                agent=self.config.agent_id,
                error=str(e),
                metadata={
                    "error_type": "permanent",
                    "model": self.config.model,
                    "request_id": request.request_id,
                },
            )
        
        except TransientError as e:
            logger.error(
                f"❌ ReviewerGPT transient error after retries: {e.message[:100]}"
            )
            return TaskResult(
                status="error",
                content=f"Failed after {self.max_retries} retries: {e.message}",
                agent=self.config.agent_id,
                error=str(e),
                metadata={
                    "error_type": "transient",
                    "error_classification": e.error_type.value,
                    "retries": self.max_retries,
                    "model": self.config.model,
                    "request_id": request.request_id,
                },
            )
        
        except Exception as e:
            logger.error(f"❌ ReviewerGPT unexpected error: {str(e)[:100]}")
            return TaskResult(
                status="error",
                content=f"Unexpected error: {str(e)}",
                agent=self.config.agent_id,
                error=str(e),
                metadata={
                    "error_type": "unexpected",
                    "model": self.config.model,
                    "request_id": request.request_id,
                },
            )
    
    def get_circuit_breaker_status(self) -> dict[str, Any]:
        """Hole Circuit Breaker Status für Debugging."""
        breaker = self.error_recovery.circuit_breaker
        return {
            "is_open": breaker.is_open,
            "is_available": breaker.is_available(),
            "failure_count": breaker.failure_count,
            "threshold": self.error_recovery.config.circuit_breaker_threshold,
            "last_failure_time": breaker.last_failure_time,
        }
    
    def reset_circuit_breaker(self) -> None:
        """Reset Circuit Breaker (für Debugging/Testing)."""
        logger.warning("🔄 Resetting Circuit Breaker")
        self.error_recovery.circuit_breaker.failure_count = 0
        self.error_recovery.circuit_breaker.is_open = False


# Global Singleton
_reviewer_with_recovery: Optional[ReviewerGPTWithErrorRecovery] = None


def get_reviewer_with_error_recovery(
    max_retries: int = 3,
    timeout_seconds: int = 60,
    circuit_breaker_threshold: int = 5,
) -> ReviewerGPTWithErrorRecovery:
    """
    Hole oder erstelle globale ReviewerGPT Instanz mit Error Recovery.
    
    Args:
        max_retries: Max retry attempts
        timeout_seconds: Timeout per attempt
        circuit_breaker_threshold: Failures before circuit opens
        
    Returns:
        ReviewerGPT Agent mit Error Recovery
    """
    global _reviewer_with_recovery
    
    if _reviewer_with_recovery is None:
        _reviewer_with_recovery = ReviewerGPTWithErrorRecovery(
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            circuit_breaker_threshold=circuit_breaker_threshold,
        )
    
    return _reviewer_with_recovery
