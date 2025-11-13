"""
🛡️ ResearchAgent mit Error Recovery Integration

Erweitert ResearchAgent mit:
- Automatisches Retry bei transienten Fehlern (Web Search API timeouts, rate limits)
- Circuit Breaker zur Fehlerprävention bei hohen Fehlerraten
- Detailliertes Logging für Debugging
- Monitoring von Fehlern und Recovery-Metriken

Phase 3c.3: ResearchAgent Error Recovery Integration

WICHTIG: ResearchAgent nutzt Perplexity API für Web Search
- Web Search kann timeout bei langsamen Netzwerken
- Rate Limits bei zu vielen Anfragen
- Connection Errors bei Netzwerkproblemen
"""

import logging
from typing import Any, Optional

from backend.agents.specialized.research_agent import ResearchAgent
from backend.agents.base.base_agent import TaskRequest, TaskResult
from backend.core.error_recovery import (
    ErrorRecoveryManager,
    ErrorRecoveryConfig,
    PermanentError,
    TransientError,
)
from backend.core.llm_monitoring import monitor_llm_call

logger = logging.getLogger(__name__)


class ResearchAgentWithErrorRecovery(ResearchAgent):
    """
    ResearchAgent mit integrierten Error Recovery Fähigkeiten.
    
    Features:
    - Automatisches Retry auf API Fehler (Perplexity API)
    - Circuit Breaker bei hohen Fehlerraten
    - Timeout-Management per Attempt (wichtig für Web Search)
    - Umfassendes Logging für Debugging
    - Monitoring und Metriken Integration
    
    Use Cases:
    - Web Search mit Perplexity API (kann timeout bei langsamen Netzwerken)
    - Best Practices Research (braucht Resilience bei API Rate Limits)
    - Technology Verification (kann fehlschlagen bei Connection Errors)
    
    Beispiel:
        agent = ResearchAgentWithErrorRecovery(
            max_retries=3,
            timeout_seconds=90,  # Längerer Timeout für Web Search
        )
        result = await agent.execute(request)
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        timeout_seconds: int = 90,
        circuit_breaker_threshold: int = 5,
    ):
        """
        Initialize ResearchAgent with Error Recovery.
        
        Args:
            max_retries: Max retry attempts for transient errors
            timeout_seconds: Timeout per attempt (90s für Web Search)
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
            f"🛡️  ResearchAgent initialized with Error Recovery "
            f"(retries={max_retries}, timeout={timeout_seconds}s, "
            f"circuit_threshold={circuit_breaker_threshold})"
        )
    
    async def execute(self, request: TaskRequest) -> TaskResult:
        """
        Execute web research mit Error Recovery.
        
        Strategy:
        1. Überprüfe Circuit Breaker Status
        2. Führe Web Search mit Error Recovery aus
        3. Klassifiziere Fehler (transient vs permanent)
        4. Retry bei transienten Fehlern (API timeout, rate limit, connection error)
        5. Fail fast bei permanenten Fehlern (auth error, invalid request)
        6. Monitore Performanz und Fehlerraten
        
        Args:
            request: TaskRequest mit Research-Anfrage
            
        Returns:
            TaskResult mit Research-Ergebnissen oder Fehler
        """
        
        logger.info(
            f"📋 ResearchAgent.execute() called "
            f"(prompt_len={len(request.prompt)}, request_id={request.request_id})"
        )
        
        async def execute_with_monitoring():
            """Führe Parent execute aus mit Monitoring."""
            with monitor_llm_call(
                agent_name="ResearchAgent",
                provider="perplexity",
                model=self.config.model,
                request_id=request.request_id,
            ):
                return await super(ResearchAgentWithErrorRecovery, self).execute(request)
        
        try:
            logger.info(
                f"🔄 Starting web research with error recovery "
                f"(max_retries={self.max_retries}, timeout={self.timeout_seconds}s)"
            )
            
            result = await self.error_recovery.execute_with_retry(
                execute_with_monitoring,
                context=f"web_research_{request.request_id}",
                timeout_seconds=self.timeout_seconds,
            )
            
            logger.info(
                f"✅ ResearchAgent.execute() succeeded "
                f"(result_len={len(result.content)}, request_id={request.request_id})"
            )
            
            return result
        
        except PermanentError as e:
            logger.error(
                f"❌ ResearchAgent permanent error (not retrying): "
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
                f"❌ ResearchAgent transient error after {self.max_retries} retries: "
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
                f"❌ ResearchAgent unexpected error: "
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


_research_with_recovery: Optional[ResearchAgentWithErrorRecovery] = None


def get_research_with_error_recovery(
    max_retries: int = 3,
    timeout_seconds: int = 90,
    circuit_breaker_threshold: int = 5,
) -> ResearchAgentWithErrorRecovery:
    """
    Hole oder erstelle globale ResearchAgent Instanz mit Error Recovery.
    
    Singleton Pattern für konsistente Circuit Breaker State.
    
    Args:
        max_retries: Max retry attempts (default: 3)
        timeout_seconds: Timeout per attempt (default: 90s für Web Search)
        circuit_breaker_threshold: Failures before circuit opens (default: 5)
        
    Returns:
        ResearchAgent mit Error Recovery
    """
    global _research_with_recovery
    
    if _research_with_recovery is None:
        _research_with_recovery = ResearchAgentWithErrorRecovery(
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            circuit_breaker_threshold=circuit_breaker_threshold,
        )
        logger.info("🏭 Created singleton ResearchAgent with Error Recovery")
    
    return _research_with_recovery


def reset_singleton() -> None:
    """
    Reset Singleton für Testing.
    
    WARNUNG: Nur für Tests verwenden!
    """
    global _research_with_recovery
    _research_with_recovery = None
    logger.warning("🔄 Reset ResearchAgent singleton (testing only)")
