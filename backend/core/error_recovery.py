"""
🛡️  Error Recovery & Resilience Framework für LLM Agents

Features:
- Spezifische Exception-Handling (nicht bare except)
- Retry-Logik mit exponential backoff (tenacity)
- Circuit Breaker Pattern
- Timeout-Handling
- Graceful Degradation
- Status Classification (transient vs permanent errors)
- Detailed Logging für Debugging

Status Classification:
- transient: Retry-würdig (timeout, rate_limit, connection_error)
- permanent: Nicht retry-würdig (auth_error, invalid_request, model_not_found)
- degraded: Partial success (metrics_export_failed, logging_failed)

Beispiel:
    from backend.core.error_recovery import ErrorRecoveryManager, ErrorStatus
    
    manager = ErrorRecoveryManager(max_retries=3, backoff_factor=2.0)
    try:
        result = await manager.execute_with_retry(
            api_call,
            context="code_review_request",
            timeout_seconds=30
        )
    except PermanentError as e:
        logger.error(f"Permanent error - not retrying: {e.status}")
    except TransientError as e:
        logger.error(f"Transient error after retries: {e}")
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, Optional

from tenacity import (
    AsyncRetrying,
    RetryError,
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger("agent.error_recovery")


class ErrorStatus(Enum):
    """Status klassifikation für Fehler."""
    TRANSIENT = "transient"  # Retry-würdig
    PERMANENT = "permanent"  # Nicht retry-würdig
    DEGRADED = "degraded"    # Partial success


class APIErrorType(Enum):
    """Spezifische API-Fehlertypen."""
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    CONNECTION_ERROR = "connection_error"
    AUTH_ERROR = "auth_error"
    INVALID_REQUEST = "invalid_request"
    MODEL_NOT_FOUND = "model_not_found"
    SERVER_ERROR = "server_error"
    UNKNOWN = "unknown"


@dataclass
class ErrorRecoveryConfig:
    """Konfiguration für Error Recovery."""
    max_retries: int = 3
    initial_wait_ms: int = 100
    max_wait_ms: int = 10000
    exponential_base: float = 2.0
    timeout_seconds: int = 30
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout_seconds: int = 60


class TransientError(Exception):
    """Fehler, der nach Retries noch immer auftritt (aber retry-würdig war)."""
    def __init__(self, message: str, error_type: APIErrorType, last_exception: Exception):
        self.message = message
        self.error_type = error_type
        self.last_exception = last_exception
        super().__init__(message)


class PermanentError(Exception):
    """Fehler, der nicht retry-würdig ist."""
    def __init__(self, message: str, status: ErrorStatus):
        self.message = message
        self.status = status
        super().__init__(message)


class CircuitBreaker:
    """Einfacher Circuit Breaker für Fehlerrate-Tracking."""
    
    def __init__(self, config: ErrorRecoveryConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.is_open = False
        self.logger = logging.getLogger("agent.circuit_breaker")
    
    def record_failure(self) -> None:
        """Registriere einen Fehler."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.circuit_breaker_threshold:
            self.is_open = True
            self.logger.warning(
                f"🔴 Circuit Breaker OPEN (failures: {self.failure_count})"
            )
    
    def record_success(self) -> None:
        """Registriere einen erfolgreichen Call."""
        if self.failure_count > 0:
            self.logger.info(
                f"✅ Circuit Breaker reset (was {self.failure_count} failures)"
            )
        self.failure_count = 0
        self.is_open = False
    
    def is_available(self) -> bool:
        """Überprüfe ob Circuit Breaker verfügbar ist."""
        if not self.is_open:
            return True
        
        # Überprüfe timeout
        if self.last_failure_time is None:
            return True
        
        age_seconds = time.time() - self.last_failure_time
        if age_seconds > self.config.circuit_breaker_timeout_seconds:
            self.logger.info(f"🟢 Circuit Breaker HALF_OPEN (timeout expired)")
            self.is_open = False
            return True
        
        return False


class ErrorRecoveryManager:
    """Hauptklasse für Error Recovery Management."""
    
    def __init__(self, config: Optional[ErrorRecoveryConfig] = None):
        self.config = config or ErrorRecoveryConfig()
        self.circuit_breaker = CircuitBreaker(self.config)
        self.logger = logging.getLogger("agent.error_recovery_manager")
    
    def classify_error(
        self,
        exception: Exception,
        error_message: str = ""
    ) -> tuple[ErrorStatus, APIErrorType]:
        """Klassifiziere einen Fehler als transient oder permanent."""
        
        error_str = str(exception).lower() + error_message.lower()
        error_type_name = type(exception).__name__
        
        # Timeout-Fehler (transient)
        if any(x in error_str for x in ["timeout", "timed out"]):
            return ErrorStatus.TRANSIENT, APIErrorType.TIMEOUT
        if error_type_name in ["TimeoutError", "asyncio.TimeoutError"]:
            return ErrorStatus.TRANSIENT, APIErrorType.TIMEOUT
        
        # Rate Limit Fehler (transient)
        if any(x in error_str for x in ["rate limit", "429", "too many requests"]):
            return ErrorStatus.TRANSIENT, APIErrorType.RATE_LIMIT
        
        # Connection Fehler (transient)
        if any(x in error_str for x in ["connection", "connection refused", "network"]):
            return ErrorStatus.TRANSIENT, APIErrorType.CONNECTION_ERROR
        if error_type_name in ["ConnectionError", "ConnectionRefusedError"]:
            return ErrorStatus.TRANSIENT, APIErrorType.CONNECTION_ERROR
        
        # Auth Fehler (permanent)
        if any(x in error_str for x in ["auth", "401", "unauthorized", "invalid api key"]):
            return ErrorStatus.PERMANENT, APIErrorType.AUTH_ERROR
        
        # Invalid Request (permanent)
        if any(x in error_str for x in ["invalid", "400", "malformed", "bad request"]):
            return ErrorStatus.PERMANENT, APIErrorType.INVALID_REQUEST
        
        # Model Not Found (permanent)
        if any(x in error_str for x in ["model", "not found", "404"]):
            return ErrorStatus.PERMANENT, APIErrorType.MODEL_NOT_FOUND
        
        # Server Error (transient) - Check before connection error
        if any(x in error_str for x in ["server error", "500", "502", "503", "internal error"]):
            return ErrorStatus.TRANSIENT, APIErrorType.SERVER_ERROR
        
        return ErrorStatus.TRANSIENT, APIErrorType.UNKNOWN
    
    async def execute_with_retry(
        self,
        async_fn: Callable[..., Awaitable[Any]],
        *args,
        context: str = "api_call",
        timeout_seconds: Optional[int] = None,
        **kwargs
    ) -> Any:
        """
        Führe async Funktion mit Retry-Logik aus.
        
        Args:
            async_fn: Async Funktion zum Ausführen
            context: Kontext-Name für Logging
            timeout_seconds: Timeout für jeden Versuch
            *args, **kwargs: Argumente für die Funktion
        
        Returns:
            Ergebnis der Funktion
        
        Raises:
            PermanentError: Wenn Fehler nicht retry-würdig ist
            TransientError: Wenn nach Retries immer noch Fehler auftritt
        """
        
        timeout = timeout_seconds or self.config.timeout_seconds
        
        # Überprüfe Circuit Breaker
        if not self.circuit_breaker.is_available():
            raise PermanentError(
                f"🔴 Circuit Breaker open - rejecting request",
                ErrorStatus.DEGRADED
            )
        
        last_exception: Optional[Exception] = None
        last_error_type = APIErrorType.UNKNOWN
        
        def should_retry_exception(exc: Exception) -> bool:
            """Determine if exception should be retried."""
            if isinstance(exc, PermanentError):
                return False
            return True
        
        try:
            retry_manager = AsyncRetrying(
                wait=wait_exponential(
                    multiplier=self.config.initial_wait_ms / 1000,
                    min=0.1,
                    max=self.config.max_wait_ms / 1000
                ),
                stop=stop_after_attempt(self.config.max_retries),
                reraise=True,
                retry=retry_if_exception(should_retry_exception),
            )
            
            attempt = 0
            async for attempt in retry_manager:
                with attempt:
                    attempt_num = attempt.retry_state.attempt_number
                    self.logger.info(
                        f"🔄 Attempt {attempt_num}/{self.config.max_retries} "
                        f"for {context}"
                    )
                    
                    try:
                        # Führe mit Timeout aus
                        result = await asyncio.wait_for(
                            async_fn(*args, **kwargs),
                            timeout=timeout
                        )
                        
                        # Erfolg - Circuit Breaker zurücksetzen
                        self.circuit_breaker.record_success()
                        self.logger.info(
                            f"✅ {context} succeeded on attempt {attempt_num}"
                        )
                        return result
                    
                    except PermanentError:
                        # Never retry permanent errors
                        raise
                    
                    except Exception as e:
                        last_exception = e
                        error_status, error_type = self.classify_error(e)
                        last_error_type = error_type
                        
                        self.logger.warning(
                            f"⚠️  Attempt {attempt_num} failed ({error_type.value}): "
                            f"{str(e)[:100]}"
                        )
                        
                        # Wenn permanent Error - raise sofort
                        if error_status == ErrorStatus.PERMANENT:
                            self.circuit_breaker.record_failure()
                            raise PermanentError(
                                f"Permanent error: {str(e)[:200]}",
                                ErrorStatus.PERMANENT
                            )
                        
                        # Sonst retry
                        raise
        
        except (RetryError, asyncio.TimeoutError, TimeoutError) as e:
            self.circuit_breaker.record_failure()
            self.logger.error(
                f"❌ {context} failed after {self.config.max_retries} retries"
            )
            
            if last_exception:
                raise TransientError(
                    f"Failed after {self.config.max_retries} retries: {str(last_exception)[:200]}",
                    last_error_type,
                    last_exception
                )
            else:
                raise TransientError(
                    f"Failed after {self.config.max_retries} retries",
                    APIErrorType.TIMEOUT,
                    e
                )
        
        except PermanentError:
            self.circuit_breaker.record_failure()
            raise
        
        except Exception as e:
            self.circuit_breaker.record_failure()
            self.logger.error(f"❌ Unexpected error in {context}: {e}")
            raise PermanentError(
                f"Unexpected error: {str(e)[:200]}",
                ErrorStatus.DEGRADED
            )
    
    def execute_with_retry_sync(
        self,
        sync_fn: Callable[..., Any],
        *args,
        context: str = "api_call",
        **kwargs
    ) -> Any:
        """Synchrone Version von execute_with_retry."""
        
        # Überprüfe Circuit Breaker
        if not self.circuit_breaker.is_available():
            raise PermanentError(
                f"🔴 Circuit Breaker open - rejecting request",
                ErrorStatus.DEGRADED
            )
        
        last_exception: Optional[Exception] = None
        last_error_type = APIErrorType.UNKNOWN
        
        def should_retry_exception(exc: Exception) -> bool:
            """Determine if exception should be retried."""
            if isinstance(exc, PermanentError):
                return False
            return True
        
        try:
            for attempt in Retrying(
                wait=wait_exponential(
                    multiplier=self.config.initial_wait_ms / 1000,
                    min=0.1,
                    max=self.config.max_wait_ms / 1000
                ),
                stop=stop_after_attempt(self.config.max_retries),
                reraise=True,
                retry=retry_if_exception(should_retry_exception),
            ):
                with attempt:
                    attempt_num = attempt.retry_state.attempt_number
                    self.logger.info(
                        f"🔄 Attempt {attempt_num}/{self.config.max_retries} "
                        f"for {context}"
                    )
                    
                    try:
                        result = sync_fn(*args, **kwargs)
                        self.circuit_breaker.record_success()
                        self.logger.info(
                            f"✅ {context} succeeded on attempt {attempt_num}"
                        )
                        return result
                    
                    except PermanentError:
                        # Never retry permanent errors
                        raise
                    
                    except Exception as e:
                        last_exception = e
                        error_status, error_type = self.classify_error(e)
                        last_error_type = error_type
                        
                        self.logger.warning(
                            f"⚠️  Attempt {attempt_num} failed ({error_type.value}): "
                            f"{str(e)[:100]}"
                        )
                        
                        if error_status == ErrorStatus.PERMANENT:
                            self.circuit_breaker.record_failure()
                            raise PermanentError(
                                f"Permanent error: {str(e)[:200]}",
                                ErrorStatus.PERMANENT
                            )
                        
                        raise
        
        except (RetryError, TimeoutError) as e:
            self.circuit_breaker.record_failure()
            self.logger.error(
                f"❌ {context} failed after {self.config.max_retries} retries"
            )
            
            if last_exception:
                raise TransientError(
                    f"Failed after {self.config.max_retries} retries: {str(last_exception)[:200]}",
                    last_error_type,
                    last_exception
                )
            else:
                raise TransientError(
                    f"Failed after {self.config.max_retries} retries",
                    APIErrorType.UNKNOWN,
                    e
                )
        
        except PermanentError:
            self.circuit_breaker.record_failure()
            raise
        
        except Exception as e:
            self.circuit_breaker.record_failure()
            self.logger.error(f"❌ Unexpected error in {context}: {e}")
            raise PermanentError(
                f"Unexpected error: {str(e)[:200]}",
                ErrorStatus.DEGRADED
            )


# Global ErrorRecoveryManager instance
_error_recovery_manager: Optional[ErrorRecoveryManager] = None


def get_error_recovery_manager(
    config: Optional[ErrorRecoveryConfig] = None
) -> ErrorRecoveryManager:
    """Hole oder erstelle globale ErrorRecoveryManager Instanz."""
    global _error_recovery_manager
    if _error_recovery_manager is None:
        _error_recovery_manager = ErrorRecoveryManager(config)
    return _error_recovery_manager
