"""
Human Response Timeout Handler

Handles timeout for human-in-the-loop requests with configurable policies.

Author: KI AutoAgent Team
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any
from enum import Enum

logger = logging.getLogger(__name__)


class TimeoutPolicy(Enum):
    """Timeout handling policies."""
    AUTO_APPROVE = "auto_approve"  # Auto-approve on timeout
    AUTO_REJECT = "auto_reject"    # Auto-reject on timeout
    AUTO_ABORT = "auto_abort"      # Abort workflow on timeout
    RETRY = "retry"                # Retry request


async def wait_for_human_response(
    request_id: str,
    response_getter: Any,
    timeout: float = 300.0,
    policy: TimeoutPolicy = TimeoutPolicy.AUTO_ABORT
) -> dict[str, Any]:
    """
    Wait for human response with timeout handling.

    Args:
        request_id: Unique request ID
        response_getter: Async callable that returns the response
        timeout: Timeout in seconds (default: 5 minutes)
        policy: What to do on timeout

    Returns:
        {
            "success": bool,
            "response": Any | None,
            "timed_out": bool,
            "policy_applied": str | None
        }
    """
    logger.debug(f"Waiting for human response (request: {request_id}, timeout: {timeout}s)")
    start_time = datetime.now()

    try:
        # Wait for response with timeout
        response = await asyncio.wait_for(
            response_getter(request_id),
            timeout=timeout
        )

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Human responded in {elapsed:.1f}s")

        return {
            "success": True,
            "response": response,
            "timed_out": False,
            "policy_applied": None,
            "elapsed_time": elapsed
        }

    except asyncio.TimeoutError:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.warning(f"⏰ Human response timeout after {elapsed:.1f}s")

        # Apply timeout policy
        if policy == TimeoutPolicy.AUTO_APPROVE:
            logger.info("  📋 Policy: AUTO_APPROVE - Approving request")
            return {
                "success": True,
                "response": {"approved": True, "reason": "auto_approved_timeout"},
                "timed_out": True,
                "policy_applied": "auto_approve",
                "elapsed_time": elapsed
            }

        elif policy == TimeoutPolicy.AUTO_REJECT:
            logger.info("  📋 Policy: AUTO_REJECT - Rejecting request")
            return {
                "success": False,
                "response": {"approved": False, "reason": "auto_rejected_timeout"},
                "timed_out": True,
                "policy_applied": "auto_reject",
                "elapsed_time": elapsed
            }

        elif policy == TimeoutPolicy.AUTO_ABORT:
            logger.info("  📋 Policy: AUTO_ABORT - Aborting workflow")
            return {
                "success": False,
                "response": {"action": "abort", "reason": "timeout"},
                "timed_out": True,
                "policy_applied": "auto_abort",
                "elapsed_time": elapsed
            }

        elif policy == TimeoutPolicy.RETRY:
            logger.info("  📋 Policy: RETRY - Will retry request")
            return {
                "success": False,
                "response": None,
                "timed_out": True,
                "policy_applied": "retry",
                "elapsed_time": elapsed
            }

    except Exception as e:
        logger.error(f"❌ Error waiting for response: {e}")
        return {
            "success": False,
            "response": None,
            "timed_out": False,
            "policy_applied": None,
            "error": str(e)
        }


class HumanResponseManager:
    """
    Manager for human-in-the-loop responses with timeout handling.
    """

    def __init__(self):
        self.pending_requests: dict[str, asyncio.Future] = {}
        self.responses: dict[str, Any] = {}
        self.timeouts: dict[str, float] = {}

    async def request_response(
        self,
        request_id: str,
        timeout: float = 300.0,
        policy: TimeoutPolicy = TimeoutPolicy.AUTO_ABORT
    ) -> dict[str, Any]:
        """
        Request a human response with timeout.

        Args:
            request_id: Unique request ID
            timeout: Timeout in seconds
            policy: Timeout handling policy

        Returns:
            Response result dictionary
        """
        logger.debug(f"Requesting human response: {request_id}")

        # Create future for this request
        future = asyncio.Future()
        self.pending_requests[request_id] = future
        self.timeouts[request_id] = timeout

        # Wait for response
        result = await wait_for_human_response(
            request_id=request_id,
            response_getter=self._get_response,
            timeout=timeout,
            policy=policy
        )

        # Cleanup
        if request_id in self.pending_requests:
            del self.pending_requests[request_id]
        if request_id in self.timeouts:
            del self.timeouts[request_id]

        return result

    async def _get_response(self, request_id: str) -> Any:
        """Wait for response to be provided."""
        if request_id in self.pending_requests:
            return await self.pending_requests[request_id]
        raise ValueError(f"Unknown request: {request_id}")

    def provide_response(self, request_id: str, response: Any) -> bool:
        """
        Provide a response for a pending request.

        Args:
            request_id: Request ID
            response: Response data

        Returns:
            True if request was pending, False otherwise
        """
        if request_id in self.pending_requests:
            future = self.pending_requests[request_id]
            if not future.done():
                future.set_result(response)
                logger.info(f"✅ Response provided for {request_id}")
                return True

        logger.warning(f"⚠️  No pending request for {request_id}")
        return False

    def cancel_request(self, request_id: str) -> bool:
        """
        Cancel a pending request.

        Args:
            request_id: Request ID

        Returns:
            True if request was cancelled, False otherwise
        """
        if request_id in self.pending_requests:
            future = self.pending_requests[request_id]
            if not future.done():
                future.cancel()
                logger.info(f"🚫 Request cancelled: {request_id}")
                del self.pending_requests[request_id]
                return True

        return False

    def get_pending_requests(self) -> list[str]:
        """Get list of pending request IDs."""
        return list(self.pending_requests.keys())


# Convenience exports
__all__ = [
    "wait_for_human_response",
    "HumanResponseManager",
    "TimeoutPolicy"
]
