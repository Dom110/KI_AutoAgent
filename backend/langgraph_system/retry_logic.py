"""
Retry Logic with Exponential Backoff
v5.8.4: Add resilience to agent execution
"""

import asyncio
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class RetryExhaustedError(Exception):
    """Raised when retry attempts are exhausted"""


async def retry_with_backoff(
    func: Callable,
    *args,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    retry_on: tuple[type[Exception], ...] = (Exception,),
    **kwargs,
) -> Any:
    """
    Retry an async function with exponential backoff

    Args:
        func: The async function to retry
        *args: Positional arguments for func
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff (2 = double each time)
        retry_on: Tuple of exception types to retry on
        **kwargs: Keyword arguments for func

    Returns:
        The result of func

    Raises:
        RetryExhaustedError: If all retry attempts fail
    """
    last_exception = None

    for attempt in range(max_attempts):
        try:
            result = await func(*args, **kwargs)
            if attempt > 0:
                logger.info(f"✅ Retry successful on attempt {attempt + 1}")
            return result

        except retry_on as e:
            last_exception = e

            if attempt == max_attempts - 1:
                # Last attempt failed
                logger.error(f"❌ All {max_attempts} retry attempts failed")
                raise RetryExhaustedError(
                    f"Failed after {max_attempts} attempts: {str(e)}"
                ) from e

            # Calculate delay with exponential backoff
            delay = min(base_delay * (exponential_base**attempt), max_delay)

            logger.warning(
                f"⚠️ Attempt {attempt + 1}/{max_attempts} failed: {type(e).__name__}: {str(e)[:100]}"
            )
            logger.info(f"🔄 Retrying in {delay:.1f}s...")

            await asyncio.sleep(delay)

        except Exception as e:
            # Non-retryable exception
            logger.error(f"❌ Non-retryable exception: {type(e).__name__}: {str(e)}")
            raise

    # Should never reach here, but just in case
    raise RetryExhaustedError(f"Unexpected retry loop exit: {last_exception}")


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    retry_on: tuple[type[Exception], ...] = (Exception,),
):
    """
    Decorator for async functions to add retry logic

    Example:
        @with_retry(max_attempts=3, base_delay=2.0)
        async def my_function():
            # ... might fail ...
            pass
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_backoff(
                func,
                *args,
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                retry_on=retry_on,
                **kwargs,
            )

        return wrapper

    return decorator


# Predefined retry strategies for common cases


def quick_retry(func: Callable):
    """Quick retry strategy: 3 attempts, 1s base delay"""
    return with_retry(max_attempts=3, base_delay=1.0)(func)


def patient_retry(func: Callable):
    """Patient retry strategy: 5 attempts, 2s base delay"""
    return with_retry(max_attempts=5, base_delay=2.0)(func)


def network_retry(func: Callable):
    """Network retry strategy: Retry on common network errors"""
    import aiohttp

    return with_retry(
        max_attempts=3,
        base_delay=1.0,
        retry_on=(
            aiohttp.ClientError,
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
        ),
    )(func)
