"""
Global Rate Limiter for AI API Calls

Prevents hitting rate limits by enforcing delays between API calls.
Supports per-provider configuration for different AI services.

Author: KI AutoAgent Team
Version: 7.0.0
Date: 2025-10-23
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Any

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration for an AI provider."""

    min_delay: float  # Minimum seconds between calls
    max_calls_per_minute: int  # Maximum calls per minute
    burst_size: int  # How many calls can happen in quick succession


class RateLimiter:
    """
    Global rate limiter that tracks API calls across all providers.

    Uses token bucket algorithm for smooth rate limiting with burst support.
    """

    # Singleton instance
    _instance: RateLimiter | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the rate limiter (only once)."""
        if self._initialized:
            return

        self._initialized = True

        # Track last call time per provider
        self._last_call: dict[str, float] = {}

        # Track call history for per-minute limits
        self._call_history: dict[str, list[float]] = defaultdict(list)

        # Load configuration from environment
        self.configs = self._load_configs()

        logger.info("⏱️ Rate Limiter initialized")
        for provider, config in self.configs.items():
            logger.info(
                f"   {provider}: {config.min_delay}s delay, "
                f"{config.max_calls_per_minute} calls/min, "
                f"burst={config.burst_size}"
            )

    def _load_configs(self) -> dict[str, RateLimitConfig]:
        """Load rate limit configs from environment variables."""

        # Default configs for known providers
        defaults = {
            "openai": RateLimitConfig(
                min_delay=float(os.getenv("OPENAI_MIN_DELAY", "1.5")),
                max_calls_per_minute=int(os.getenv("OPENAI_MAX_CALLS_PER_MIN", "30")),
                burst_size=int(os.getenv("OPENAI_BURST_SIZE", "3"))
            ),
            "claude-cli": RateLimitConfig(
                min_delay=float(os.getenv("CLAUDE_CLI_MIN_DELAY", "2.0")),
                max_calls_per_minute=int(os.getenv("CLAUDE_CLI_MAX_CALLS_PER_MIN", "20")),
                burst_size=int(os.getenv("CLAUDE_CLI_BURST_SIZE", "2"))
            ),
            "perplexity": RateLimitConfig(
                min_delay=float(os.getenv("PERPLEXITY_MIN_DELAY", "1.0")),
                max_calls_per_minute=int(os.getenv("PERPLEXITY_MAX_CALLS_PER_MIN", "40")),
                burst_size=int(os.getenv("PERPLEXITY_BURST_SIZE", "5"))
            ),
            "anthropic": RateLimitConfig(
                min_delay=float(os.getenv("ANTHROPIC_MIN_DELAY", "1.5")),
                max_calls_per_minute=int(os.getenv("ANTHROPIC_MAX_CALLS_PER_MIN", "30")),
                burst_size=int(os.getenv("ANTHROPIC_BURST_SIZE", "3"))
            ),
        }

        return defaults

    async def wait_if_needed(self, provider: str) -> float:
        """
        Wait if necessary to respect rate limits.

        Args:
            provider: AI provider name (openai, claude-cli, perplexity, etc.)

        Returns:
            Actual wait time in seconds
        """
        if provider not in self.configs:
            logger.warning(f"⚠️ No rate limit config for provider '{provider}', using defaults")
            # Use conservative defaults
            config = RateLimitConfig(min_delay=2.0, max_calls_per_minute=20, burst_size=2)
        else:
            config = self.configs[provider]

        current_time = time.time()

        # Clean up old history (older than 1 minute)
        if provider in self._call_history:
            self._call_history[provider] = [
                t for t in self._call_history[provider]
                if current_time - t < 60
            ]

        # Check per-minute limit
        recent_calls = len(self._call_history[provider])
        if recent_calls >= config.max_calls_per_minute:
            # Wait until oldest call is > 1 minute old
            oldest_call = self._call_history[provider][0]
            wait_time = 60 - (current_time - oldest_call) + 0.1  # +0.1s safety margin

            if wait_time > 0:
                logger.warning(
                    f"⏸️ Rate limit: {provider} hit {config.max_calls_per_minute} calls/min, "
                    f"waiting {wait_time:.1f}s"
                )
                await asyncio.sleep(wait_time)
                current_time = time.time()

        # Check minimum delay between calls
        if provider in self._last_call:
            time_since_last = current_time - self._last_call[provider]

            # Allow burst if we haven't used it recently
            is_burst_available = recent_calls < config.burst_size

            if not is_burst_available and time_since_last < config.min_delay:
                wait_time = config.min_delay - time_since_last
                logger.debug(
                    f"⏸️ Rate limit: {provider} min delay {config.min_delay}s, "
                    f"waiting {wait_time:.2f}s"
                )
                await asyncio.sleep(wait_time)
                current_time = time.time()
                actual_wait = wait_time
            else:
                actual_wait = 0.0
        else:
            actual_wait = 0.0

        # Record this call
        self._last_call[provider] = current_time
        self._call_history[provider].append(current_time)

        return actual_wait

    async def execute_with_limit(
        self,
        provider: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a function with rate limiting.

        Args:
            provider: AI provider name
            func: Async function to execute
            *args, **kwargs: Arguments for the function

        Returns:
            Result from the function
        """
        await self.wait_if_needed(provider)

        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    def get_stats(self, provider: str) -> dict[str, Any]:
        """
        Get rate limiting statistics for a provider.

        Args:
            provider: AI provider name

        Returns:
            Dictionary with stats
        """
        config = self.configs.get(provider)
        if not config:
            return {"error": f"Unknown provider: {provider}"}

        current_time = time.time()

        # Clean old history
        if provider in self._call_history:
            recent_calls = [
                t for t in self._call_history[provider]
                if current_time - t < 60
            ]
        else:
            recent_calls = []

        last_call = self._last_call.get(provider)
        time_since_last = current_time - last_call if last_call else None

        return {
            "provider": provider,
            "calls_last_minute": len(recent_calls),
            "max_calls_per_minute": config.max_calls_per_minute,
            "min_delay": config.min_delay,
            "burst_size": config.burst_size,
            "time_since_last_call": time_since_last,
            "can_call_now": (
                len(recent_calls) < config.max_calls_per_minute and
                (time_since_last is None or time_since_last >= config.min_delay)
            )
        }


# ============================================================================
# Singleton Access
# ============================================================================

def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return RateLimiter()


# ============================================================================
# Convenience Functions
# ============================================================================

async def wait_for_provider(provider: str) -> float:
    """
    Wait if needed to respect rate limits for a provider.

    Args:
        provider: AI provider name

    Returns:
        Actual wait time in seconds
    """
    limiter = get_rate_limiter()
    return await limiter.wait_if_needed(provider)


async def execute_with_rate_limit(
    provider: str,
    func: Callable,
    *args,
    **kwargs
) -> Any:
    """
    Execute a function with rate limiting.

    Args:
        provider: AI provider name
        func: Async function to execute
        *args, **kwargs: Arguments for the function

    Returns:
        Result from the function
    """
    limiter = get_rate_limiter()
    return await limiter.execute_with_limit(provider, func, *args, **kwargs)


# ============================================================================
# Export
# ============================================================================

__all__ = [
    "RateLimiter",
    "RateLimitConfig",
    "get_rate_limiter",
    "wait_for_provider",
    "execute_with_rate_limit"
]
