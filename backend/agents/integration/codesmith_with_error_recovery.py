"""
🛡️ CodeSmithAgent mit Error Recovery Integration

Erweitert CodeSmithAgent mit:
- Automatisches Retry bei transienten Fehlern (API timeouts, rate limits)
- Circuit Breaker zur Fehlerprävention bei hohen Fehlerraten
- Detailliertes Logging für Debugging
- Monitoring von Fehlern und Recovery-Metriken

Phase 3c.3: CodeSmithAgent Error Recovery Integration
"""

import logging
from typing import Any, Optional

from backend.agents.specialized.codesmith_agent import CodeSmithAgent
from backend.agents.base.base_agent import TaskRequest, TaskResult
from backend.core.error_recovery import (
    ErrorRecoveryManager,
    ErrorRecoveryConfig,
    PermanentError,
    TransientError,
)
from backend.core.llm_monitoring import monitor_llm_call

logger = logging.getLogger(__name__)


class CodeSmithAgentWithErrorRecovery(CodeSmithAgent):
    """
    CodeSmithAgent mit integrierten Error Recovery Fähigkeiten.
    
    Features:
    - Automatisches Retry auf API Fehler (Claude API)
    - Circuit Breaker bei hohen Fehlerraten
    - Timeout-Management per Attempt (wichtig für lange Code-Generierung)
    - Umfassendes Logging für Debugging
    - Monitoring und Metriken Integration
    
    Use Cases:
    - Code-Generierung mit Claude API (kann timeout bei großen Projekten)
    - File-Writing Operations (können fehlschlagen bei I/O Problemen)
    - Multi-File Project Creation (braucht Resilience bei Partial Failures)
    
    Beispiel:
        agent = CodeSmithAgentWithErrorRecovery(
            max_retries=3,
            timeout_seconds=120,  # Längerer Timeout für Code-Generierung
        )
        result = await agent.execute(request)
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        timeout_seconds: int = 120,
        circuit_breaker_threshold: int = 5,
    ):
        """
        Initialize CodeSmithAgent with Error Recovery.
        
        Args:
            max_retries: Max retry attempts for transient errors
            timeout_seconds: Timeout per attempt (120s für Code-Generierung)
            circuit_breaker_threshold: Failures before circuit opens
        """
        super().__init__()
        
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
            f"🛡️  CodeSmithAgent initialized with Error Recovery "
            f"(retries={max_retries}, timeout={timeout_seconds}s, "
            f"circuit_threshold={circuit_breaker_threshold})"
        )
    
    async def execute(self, request: TaskRequest) -> TaskResult:
        """
        Execute code generation mit Error Recovery.
        
        Strategy:
        1. Überprüfe Circuit Breaker Status
        2. Führe Code-Generierung mit Error Recovery aus
        3. Klassifiziere Fehler (transient vs permanent)
        4. Retry bei transienten Fehlern (API timeout, rate limit)
        5. Fail fast bei permanenten Fehlern (auth error, invalid request)
        6. Monitore Performanz und Fehlerraten
        
        Args:
            request: TaskRequest mit Code-Generierungs-Anfrage
            
        Returns:
            TaskResult mit generiertem Code oder Fehler
        """
        
        logger.info(
            f"📋 CodeSmithAgent.execute() called "
            f"(prompt_len={len(request.prompt)}, request_id={request.request_id})"
        )
        
        async def execute_with_monitoring():
            """Führe Parent execute aus mit Monitoring."""
            with monitor_llm_call(
                agent_name="CodeSmithAgent",
                provider="anthropic",
                model=self.config.model,
                request_id=request.request_id,
            ):
                return await super(CodeSmithAgentWithErrorRecovery, self).execute(request)
        
        try:
            logger.info(
                f"🔄 Starting code generation with error recovery "
                f"(max_retries={self.max_retries}, timeout={self.timeout_seconds}s)"
            )
            
            result = await self.error_recovery.execute_with_retry(
                execute_with_monitoring,
                context=f"code_generation_{request.request_id}",
                timeout_seconds=self.timeout_seconds,
            )
            
            logger.info(
                f"✅ CodeSmithAgent.execute() succeeded "
                f"(result_len={len(result.content)}, request_id={request.request_id})"
            )
            
            return result
        
        except PermanentError as e:
            logger.error(
                f"❌ CodeSmithAgent permanent error (not retrying): "
                f"error_type={e.error_type.value}, message={e.message[:100]}"
            )
            return TaskResult(
                status="error",
                content=f"Permanent error: {e.message}",
                agent=self.config.agent_id,
                error=str(e),
                metadata={
                    "error_type": "permanent",
                    "error_classification": e.error_type.value,
                    "model": self.config.model,
                    "request_id": request.request_id,
                },
            )
        
        except TransientError as e:
            logger.error(
                f"❌ CodeSmithAgent transient error after {self.max_retries} retries: "
                f"error_type={e.error_type.value}, message={e.message[:100]}"
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
            logger.error(
                f"❌ CodeSmithAgent unexpected error: "
                f"type={type(e).__name__}, message={str(e)[:100]}"
            )
            return TaskResult(
                status="error",
                content=f"Unexpected error: {str(e)}",
                agent=self.config.agent_id,
                error=str(e),
                metadata={
                    "error_type": "unexpected",
                    "exception_type": type(e).__name__,
                    "model": self.config.model,
                    "request_id": request.request_id,
                },
            )
    
    def get_circuit_breaker_status(self) -> dict[str, Any]:
        """
        Hole Circuit Breaker Status für Debugging und Monitoring.
        
        Returns:
            Dict mit Circuit Breaker Status:
            - is_open: Circuit ist offen (keine Requests erlaubt)
            - is_available: Circuit ist verfügbar
            - failure_count: Anzahl Fehler
            - threshold: Schwellwert für Circuit Open
            - last_failure_time: Zeitpunkt letzter Fehler
        """
        breaker = self.error_recovery.circuit_breaker
        return {
            "is_open": breaker.is_open,
            "is_available": breaker.is_available(),
            "failure_count": breaker.failure_count,
            "threshold": self.error_recovery.config.circuit_breaker_threshold,
            "last_failure_time": breaker.last_failure_time,
        }
    
    def reset_circuit_breaker(self) -> None:
        """
        Reset Circuit Breaker (für Debugging/Testing).
        
        WARNUNG: Nur für Development/Testing verwenden!
        In Production sollte Circuit Breaker automatisch recovern.
        """
        logger.warning("🔄 Resetting Circuit Breaker (manual override)")
        self.error_recovery.circuit_breaker.failure_count = 0
        self.error_recovery.circuit_breaker.is_open = False


_codesmith_with_recovery: Optional[CodeSmithAgentWithErrorRecovery] = None


def get_codesmith_with_error_recovery(
    max_retries: int = 3,
    timeout_seconds: int = 120,
    circuit_breaker_threshold: int = 5,
) -> CodeSmithAgentWithErrorRecovery:
    """
    Hole oder erstelle globale CodeSmithAgent Instanz mit Error Recovery.
    
    Singleton Pattern für konsistente Circuit Breaker State.
    
    Args:
        max_retries: Max retry attempts (default: 3)
        timeout_seconds: Timeout per attempt (default: 120s für Code-Gen)
        circuit_breaker_threshold: Failures before circuit opens (default: 5)
        
    Returns:
        CodeSmithAgent mit Error Recovery
    """
    global _codesmith_with_recovery
    
    if _codesmith_with_recovery is None:
        _codesmith_with_recovery = CodeSmithAgentWithErrorRecovery(
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            circuit_breaker_threshold=circuit_breaker_threshold,
        )
        logger.info("🏭 Created singleton CodeSmithAgent with Error Recovery")
    
    return _codesmith_with_recovery


def reset_singleton() -> None:
    """
    Reset Singleton für Testing.
    
    WARNUNG: Nur für Tests verwenden!
    """
    global _codesmith_with_recovery
    _codesmith_with_recovery = None
    logger.warning("🔄 Reset CodeSmithAgent singleton (testing only)")
