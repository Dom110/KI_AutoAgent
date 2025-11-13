"""
Credit Tracking and Safety System

CRITICAL: Prevents runaway credit consumption!
- Tracks API usage across all agents
- Enforces hard limits
- Single Claude instance lock
- Emergency shutdown on limit exceed

Author: KI AutoAgent v7.0
Date: 2025-11-08
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class AgentUsage:
    """Track usage per agent."""
    agent_name: str
    api_calls: int = 0
    tokens_used: int = 0
    cost_usd: float = 0.0
    last_call: Optional[datetime] = None
    errors: int = 0


@dataclass
class CreditLimits:
    """Safety limits to prevent runaway costs."""
    max_cost_per_session: float = 5.0  # $5 per session
    max_cost_per_hour: float = 10.0    # $10 per hour
    max_cost_per_day: float = 50.0     # $50 per day
    max_claude_instances: int = 1       # ONLY 1 Claude at a time!
    max_calls_per_minute: int = 10     # Rate limit
    emergency_shutdown_cost: float = 100.0  # Emergency stop at $100


class CreditTracker:
    """
    Global credit tracking and safety system.

    CRITICAL FEATURES:
    1. Tracks all API usage
    2. Enforces hard limits
    3. Claude instance lock (singleton)
    4. Emergency shutdown
    5. Real-time WebSocket reporting
    """

    # API Pricing (approximate, in USD)
    PRICING = {
        "gpt-4o": {"input": 0.005, "output": 0.015},  # per 1K tokens
        "claude-sonnet-4": {"input": 0.003, "output": 0.015},  # per 1K tokens
        "perplexity": {"per_call": 0.005},  # per search
    }

    def __init__(self, limits: Optional[CreditLimits] = None):
        """Initialize credit tracker with safety limits."""
        self.limits = limits or CreditLimits()
        self.usage: Dict[str, AgentUsage] = {}
        self.session_start = datetime.now()
        self.total_cost = 0.0
        self.hourly_costs: list[tuple[datetime, float]] = []
        self.daily_cost = 0.0

        # Claude instance lock
        self._claude_lock = asyncio.Lock()
        self._claude_running = False
        self._claude_pid: Optional[int] = None

        # Emergency flags
        self.emergency_shutdown = False
        self.shutdown_reason = ""

        # Persistence
        self.usage_file = Path.home() / ".ki_autoagent" / "usage" / "credit_usage.json"
        self._load_usage()

        logger.warning("💰 CREDIT TRACKER INITIALIZED")
        logger.warning(f"   Max per session: ${self.limits.max_cost_per_session:.2f}")
        logger.warning(f"   Max per hour: ${self.limits.max_cost_per_hour:.2f}")
        logger.warning(f"   Max per day: ${self.limits.max_cost_per_day:.2f}")
        logger.warning(f"   EMERGENCY STOP: ${self.limits.emergency_shutdown_cost:.2f}")

    async def track_api_call(
        self,
        agent: str,
        api: str,
        tokens_in: int = 0,
        tokens_out: int = 0,
        error: bool = False
    ) -> Dict[str, any]:
        """
        Track an API call and check limits.

        Returns:
            Dict with usage info and any warnings
        """
        # Check emergency shutdown
        if self.emergency_shutdown:
            raise Exception(f"🚨 EMERGENCY SHUTDOWN: {self.shutdown_reason}")

        # Get or create agent usage
        if agent not in self.usage:
            self.usage[agent] = AgentUsage(agent_name=agent)

        agent_usage = self.usage[agent]
        agent_usage.api_calls += 1
        agent_usage.last_call = datetime.now()

        if error:
            agent_usage.errors += 1

        # Calculate cost
        cost = self._calculate_cost(api, tokens_in, tokens_out)
        agent_usage.tokens_used += tokens_in + tokens_out
        agent_usage.cost_usd += cost
        self.total_cost += cost

        # Track hourly
        self.hourly_costs.append((datetime.now(), cost))
        self._cleanup_hourly()

        # Check all limits
        warnings = self._check_limits()

        # Prepare response
        usage_info = {
            "agent": agent,
            "api": api,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost": cost,
            "total_cost": self.total_cost,
            "session_cost": self._get_session_cost(),
            "hourly_cost": self._get_hourly_cost(),
            "warnings": warnings,
            "limits": {
                "session": self.limits.max_cost_per_session,
                "hourly": self.limits.max_cost_per_hour,
                "daily": self.limits.max_cost_per_day
            }
        }

        # Log warning if approaching limits
        if warnings:
            logger.warning(f"⚠️ CREDIT WARNING: {warnings}")

        # Persist usage
        self._save_usage()

        return usage_info

    async def acquire_claude_lock(self, timeout: float = 30.0) -> bool:
        """
        Acquire exclusive lock for Claude instance.

        CRITICAL: Only ONE Claude process allowed at a time!
        """
        try:
            logger.info("🔒 Attempting to acquire Claude lock...")

            # Try to acquire with timeout
            acquired = await asyncio.wait_for(
                self._claude_lock.acquire(),
                timeout=timeout
            )

            if acquired or self._claude_lock.locked():
                self._claude_running = True
                logger.info("✅ Claude lock acquired - instance can start")
                return True

            return False

        except asyncio.TimeoutError:
            logger.error(f"❌ CLAUDE LOCK TIMEOUT after {timeout}s")
            logger.error("   Another Claude instance is running!")
            return False

    async def release_claude_lock(self):
        """Release Claude instance lock."""
        if self._claude_lock.locked():
            self._claude_lock.release()
            self._claude_running = False
            self._claude_pid = None
            logger.info("🔓 Claude lock released")

    def _calculate_cost(self, api: str, tokens_in: int, tokens_out: int) -> float:
        """Calculate cost for API call."""
        if "gpt-4" in api.lower():
            pricing = self.PRICING["gpt-4o"]
            cost = (tokens_in / 1000 * pricing["input"]) + (tokens_out / 1000 * pricing["output"])
        elif "claude" in api.lower():
            pricing = self.PRICING["claude-sonnet-4"]
            cost = (tokens_in / 1000 * pricing["input"]) + (tokens_out / 1000 * pricing["output"])
        elif "perplexity" in api.lower():
            cost = self.PRICING["perplexity"]["per_call"]
        else:
            cost = 0.01  # Default cost for unknown APIs

        return round(cost, 4)

    def _check_limits(self) -> list[str]:
        """Check all safety limits."""
        warnings = []

        # Session limit
        session_cost = self._get_session_cost()
        if session_cost > self.limits.max_cost_per_session * 0.8:
            warnings.append(f"Session cost ${session_cost:.2f} approaching limit ${self.limits.max_cost_per_session:.2f}")
        if session_cost > self.limits.max_cost_per_session:
            self._trigger_shutdown(f"Session cost ${session_cost:.2f} exceeded limit ${self.limits.max_cost_per_session:.2f}")

        # Hourly limit
        hourly_cost = self._get_hourly_cost()
        if hourly_cost > self.limits.max_cost_per_hour * 0.8:
            warnings.append(f"Hourly cost ${hourly_cost:.2f} approaching limit ${self.limits.max_cost_per_hour:.2f}")
        if hourly_cost > self.limits.max_cost_per_hour:
            self._trigger_shutdown(f"Hourly cost ${hourly_cost:.2f} exceeded limit ${self.limits.max_cost_per_hour:.2f}")

        # Daily limit
        if self.daily_cost > self.limits.max_cost_per_day * 0.8:
            warnings.append(f"Daily cost ${self.daily_cost:.2f} approaching limit ${self.limits.max_cost_per_day:.2f}")
        if self.daily_cost > self.limits.max_cost_per_day:
            self._trigger_shutdown(f"Daily cost ${self.daily_cost:.2f} exceeded limit ${self.limits.max_cost_per_day:.2f}")

        # Emergency limit
        if self.total_cost > self.limits.emergency_shutdown_cost:
            self._trigger_shutdown(f"EMERGENCY: Total cost ${self.total_cost:.2f} exceeded emergency limit ${self.limits.emergency_shutdown_cost:.2f}")

        return warnings

    def _trigger_shutdown(self, reason: str):
        """Trigger emergency shutdown."""
        self.emergency_shutdown = True
        self.shutdown_reason = reason
        logger.critical(f"🚨🚨🚨 EMERGENCY SHUTDOWN: {reason}")
        raise Exception(f"EMERGENCY SHUTDOWN: {reason}")

    def _get_session_cost(self) -> float:
        """Get total cost for current session."""
        return sum(u.cost_usd for u in self.usage.values())

    def _get_hourly_cost(self) -> float:
        """Get cost for last hour."""
        cutoff = datetime.now() - timedelta(hours=1)
        return sum(cost for timestamp, cost in self.hourly_costs if timestamp > cutoff)

    def _cleanup_hourly(self):
        """Remove old hourly entries."""
        cutoff = datetime.now() - timedelta(hours=24)
        self.hourly_costs = [(t, c) for t, c in self.hourly_costs if t > cutoff]

    def _save_usage(self):
        """Save usage to file."""
        try:
            self.usage_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "timestamp": datetime.now().isoformat(),
                "total_cost": self.total_cost,
                "daily_cost": self.daily_cost,
                "session_cost": self._get_session_cost(),
                "agents": {
                    name: {
                        "calls": u.api_calls,
                        "tokens": u.tokens_used,
                        "cost": u.cost_usd,
                        "errors": u.errors
                    }
                    for name, u in self.usage.items()
                }
            }

            with open(self.usage_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save usage: {e}")

    def _load_usage(self):
        """Load usage from file."""
        try:
            if self.usage_file.exists():
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)

                # Check if same day
                saved_time = datetime.fromisoformat(data["timestamp"])
                if saved_time.date() == datetime.now().date():
                    self.daily_cost = data.get("daily_cost", 0.0)
                    logger.info(f"   Loaded daily cost: ${self.daily_cost:.2f}")

        except Exception as e:
            logger.warning(f"Could not load usage history: {e}")

    def get_usage_summary(self) -> Dict:
        """Get usage summary for WebSocket."""
        return {
            "total_cost": round(self.total_cost, 2),
            "session_cost": round(self._get_session_cost(), 2),
            "hourly_cost": round(self._get_hourly_cost(), 2),
            "daily_cost": round(self.daily_cost, 2),
            "limits": {
                "session": self.limits.max_cost_per_session,
                "hourly": self.limits.max_cost_per_hour,
                "daily": self.limits.max_cost_per_day,
                "emergency": self.limits.emergency_shutdown_cost
            },
            "agents": {
                name: {
                    "calls": u.api_calls,
                    "cost": round(u.cost_usd, 2),
                    "errors": u.errors
                }
                for name, u in self.usage.items()
            },
            "claude_locked": self._claude_running,
            "emergency_shutdown": self.emergency_shutdown
        }


# Global instance
_credit_tracker: Optional[CreditTracker] = None


def get_credit_tracker() -> CreditTracker:
    """Get global credit tracker instance."""
    global _credit_tracker
    if _credit_tracker is None:
        _credit_tracker = CreditTracker()
    return _credit_tracker