"""
Approval Manager v6 - Human-in-the-Loop Approval System

Capabilities:
- WebSocket approval prompts
- Async approval wait with timeout
- Configurable approval rules
- File write approvals
- Deployment approvals
- Action history tracking

Integration:
- Before write_file operations
- Before deployment commands
- Before destructive actions
- Configurable per action type

Author: KI AutoAgent Team
Version: 6.0.0
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class ApprovalAction(str, Enum):
    """Types of actions requiring approval."""

    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    DEPLOYMENT = "deployment"
    API_CALL = "api_call"
    DATABASE_MODIFY = "database_modify"
    SHELL_COMMAND = "shell_command"
    CUSTOM = "custom"


class ApprovalStatus(str, Enum):
    """Status of approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class ApprovalRule:
    """Configuration for approval requirements."""

    action_type: ApprovalAction
    requires_approval: bool
    timeout_seconds: float
    auto_approve_patterns: list[str] | None = None  # e.g., ["*.test.py"]
    auto_reject_patterns: list[str] | None = None   # e.g., ["*.env", "/etc/*"]
    description: str = ""


@dataclass(slots=True)
class ApprovalRequest:
    """Request for human approval."""

    request_id: str
    action_type: ApprovalAction
    description: str
    details: dict[str, Any]
    timeout_seconds: float
    created_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    response: str | None = None
    responded_at: datetime | None = None


class ApprovalManagerV6:
    """
    Human-in-the-Loop Approval System.

    Manages approval requests for critical actions with WebSocket integration.
    """

    def __init__(self, websocket_callback: Callable | None = None):
        """
        Initialize approval manager.

        Args:
            websocket_callback: Async function to send approval prompts via WebSocket
                                Signature: async def(request: dict) -> dict
        """
        self.websocket_callback = websocket_callback
        self.rules: dict[ApprovalAction, ApprovalRule] = {}
        self.pending_requests: dict[str, ApprovalRequest] = {}
        self.history: list[ApprovalRequest] = []
        self._request_counter = 0

        # Default rules
        self._setup_default_rules()

        logger.info("🔐 Approval Manager v6 initialized")

    def _setup_default_rules(self) -> None:
        """Setup default approval rules."""

        # File operations
        self.add_rule(ApprovalRule(
            action_type=ApprovalAction.FILE_WRITE,
            requires_approval=True,
            timeout_seconds=300.0,  # 5 minutes
            auto_approve_patterns=["*.test.py", "*.md", "test_*.py"],
            auto_reject_patterns=["*.env", ".git/*", "venv/*"],
            description="File write operations"
        ))

        self.add_rule(ApprovalRule(
            action_type=ApprovalAction.FILE_DELETE,
            requires_approval=True,
            timeout_seconds=300.0,
            auto_reject_patterns=["*.env", ".git/*", "venv/*", "*.db"],
            description="File deletion operations"
        ))

        # Deployment
        self.add_rule(ApprovalRule(
            action_type=ApprovalAction.DEPLOYMENT,
            requires_approval=True,
            timeout_seconds=600.0,  # 10 minutes
            description="Deployment operations"
        ))

        # Shell commands
        self.add_rule(ApprovalRule(
            action_type=ApprovalAction.SHELL_COMMAND,
            requires_approval=True,
            timeout_seconds=300.0,
            auto_approve_patterns=["npm test", "pytest", "git status"],
            auto_reject_patterns=["rm -rf", "sudo", "dd if="],
            description="Shell command execution"
        ))

        # Database
        self.add_rule(ApprovalRule(
            action_type=ApprovalAction.DATABASE_MODIFY,
            requires_approval=True,
            timeout_seconds=300.0,
            description="Database modification operations"
        ))

        # API calls (less critical)
        self.add_rule(ApprovalRule(
            action_type=ApprovalAction.API_CALL,
            requires_approval=False,  # Auto-approve by default
            timeout_seconds=60.0,
            description="External API calls"
        ))

    def add_rule(self, rule: ApprovalRule) -> None:
        """Add or update approval rule."""
        self.rules[rule.action_type] = rule
        logger.debug(f"📋 Added approval rule: {rule.action_type.value}")

    def update_rule(
        self,
        action_type: ApprovalAction,
        requires_approval: bool | None = None,
        timeout_seconds: float | None = None
    ) -> bool:
        """
        Update existing rule.

        Args:
            action_type: Type of action
            requires_approval: Whether approval is required
            timeout_seconds: Timeout in seconds

        Returns:
            True if rule was updated
        """
        if action_type not in self.rules:
            logger.warning(f"⚠️  No rule found for {action_type.value}")
            return False

        rule = self.rules[action_type]

        if requires_approval is not None:
            rule.requires_approval = requires_approval
        if timeout_seconds is not None:
            rule.timeout_seconds = timeout_seconds

        logger.info(f"✅ Updated rule for {action_type.value}")
        return True

    async def request_approval(
        self,
        action_type: ApprovalAction,
        description: str,
        details: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Request approval for an action.

        Args:
            action_type: Type of action requiring approval
            description: Human-readable description
            details: Action details (file path, command, etc.)

        Returns:
            Dict with approval result:
            {
                "approved": bool,
                "status": ApprovalStatus,
                "response": str | None,
                "auto_decision": bool
            }
        """
        logger.info(f"🔐 Approval requested: {action_type.value} - {description}")

        # Helper to record auto-decision
        def record_auto_decision(approved: bool, status: ApprovalStatus, response: str) -> dict[str, Any]:
            request = ApprovalRequest(
                request_id=self._generate_request_id(),
                action_type=action_type,
                description=description,
                details=details,
                timeout_seconds=0.0,
                created_at=datetime.now(),
                status=status,
                response=response,
                responded_at=datetime.now()
            )
            self.history.append(request)
            return {
                "approved": approved,
                "status": status,
                "response": response,
                "auto_decision": True
            }

        # Get rule for this action type
        rule = self.rules.get(action_type)
        if not rule:
            # No rule = auto-approve
            logger.warning(f"⚠️  No rule for {action_type.value}, auto-approving")
            return record_auto_decision(
                True,
                ApprovalStatus.APPROVED,
                "No rule configured, auto-approved"
            )

        # Check if approval is required
        if not rule.requires_approval:
            logger.debug(f"✅ Auto-approved: {action_type.value} (rule disabled)")
            return record_auto_decision(
                True,
                ApprovalStatus.APPROVED,
                "Auto-approved by rule"
            )

        # Check auto-approve patterns
        target = details.get("target", details.get("file_path", details.get("command", "")))

        if rule.auto_approve_patterns:
            for pattern in rule.auto_approve_patterns:
                if self._matches_pattern(target, pattern):
                    logger.debug(f"✅ Auto-approved by pattern: {pattern}")
                    return record_auto_decision(
                        True,
                        ApprovalStatus.APPROVED,
                        f"Auto-approved by pattern: {pattern}"
                    )

        # Check auto-reject patterns
        if rule.auto_reject_patterns:
            for pattern in rule.auto_reject_patterns:
                if self._matches_pattern(target, pattern):
                    logger.warning(f"❌ Auto-rejected by pattern: {pattern}")
                    return record_auto_decision(
                        False,
                        ApprovalStatus.REJECTED,
                        f"Auto-rejected by pattern: {pattern}"
                    )

        # Need human approval
        request = ApprovalRequest(
            request_id=self._generate_request_id(),
            action_type=action_type,
            description=description,
            details=details,
            timeout_seconds=rule.timeout_seconds,
            created_at=datetime.now()
        )

        self.pending_requests[request.request_id] = request

        try:
            # Send approval prompt via WebSocket
            if self.websocket_callback:
                result = await self._wait_for_approval(request)
            else:
                # No WebSocket callback = auto-approve (development mode)
                logger.warning("⚠️  No WebSocket callback, auto-approving")
                result = {
                    "approved": True,
                    "status": ApprovalStatus.APPROVED,
                    "response": "Auto-approved (no WebSocket callback)",
                    "auto_decision": True
                }

            # Update request
            request.status = result["status"]
            request.response = result.get("response")
            request.responded_at = datetime.now()

            # Move to history
            self.history.append(request)
            del self.pending_requests[request.request_id]

            return result

        except Exception as e:
            logger.error(f"❌ Approval request failed: {e}")
            request.status = ApprovalStatus.TIMEOUT
            self.history.append(request)
            del self.pending_requests[request.request_id]

            return {
                "approved": False,
                "status": ApprovalStatus.TIMEOUT,
                "response": f"Error: {str(e)}",
                "auto_decision": False
            }

    async def _wait_for_approval(self, request: ApprovalRequest) -> dict[str, Any]:
        """
        Wait for approval response via WebSocket.

        Args:
            request: Approval request

        Returns:
            Approval result
        """
        # Send approval prompt
        prompt_data = {
            "type": "approval_request",
            "request_id": request.request_id,
            "action_type": request.action_type.value,
            "description": request.description,
            "details": request.details,
            "timeout_seconds": request.timeout_seconds
        }

        try:
            # Call WebSocket callback
            response = await asyncio.wait_for(
                self.websocket_callback(prompt_data),
                timeout=request.timeout_seconds
            )

            # Parse response
            approved = response.get("approved", False)
            user_response = response.get("response", "")

            logger.info(f"{'✅' if approved else '❌'} Approval {'granted' if approved else 'denied'}: {request.request_id}")

            return {
                "approved": approved,
                "status": ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED,
                "response": user_response,
                "auto_decision": False
            }

        except asyncio.TimeoutError:
            logger.warning(f"⏱️  Approval timeout: {request.request_id}")
            return {
                "approved": False,
                "status": ApprovalStatus.TIMEOUT,
                "response": f"Timeout after {request.timeout_seconds}s",
                "auto_decision": False
            }

    def respond_to_request(
        self,
        request_id: str,
        approved: bool,
        response: str | None = None
    ) -> bool:
        """
        Respond to pending approval request (called by WebSocket handler).

        Args:
            request_id: Request ID
            approved: Whether approved
            response: Optional response message

        Returns:
            True if request was found and updated
        """
        request = self.pending_requests.get(request_id)
        if not request:
            logger.warning(f"⚠️  Request not found: {request_id}")
            return False

        request.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        request.response = response
        request.responded_at = datetime.now()

        logger.info(f"✅ Request {request_id} {'approved' if approved else 'rejected'}")
        return True

    def cancel_request(self, request_id: str) -> bool:
        """Cancel pending approval request."""
        request = self.pending_requests.get(request_id)
        if not request:
            return False

        request.status = ApprovalStatus.CANCELLED
        self.history.append(request)
        del self.pending_requests[request_id]

        logger.info(f"🚫 Request cancelled: {request_id}")
        return True

    def get_pending_requests(self) -> list[dict[str, Any]]:
        """Get all pending approval requests."""
        return [
            {
                "request_id": req.request_id,
                "action_type": req.action_type.value,
                "description": req.description,
                "details": req.details,
                "created_at": req.created_at.isoformat(),
                "timeout_seconds": req.timeout_seconds
            }
            for req in self.pending_requests.values()
        ]

    def get_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get approval history."""
        return [
            {
                "request_id": req.request_id,
                "action_type": req.action_type.value,
                "description": req.description,
                "status": req.status.value,
                "response": req.response,
                "created_at": req.created_at.isoformat(),
                "responded_at": req.responded_at.isoformat() if req.responded_at else None
            }
            for req in self.history[-limit:]
        ]

    def get_approval_stats(self) -> dict[str, Any]:
        """Get approval statistics."""
        total = len(self.history)

        if total == 0:
            return {
                "total_requests": 0,
                "approved": 0,
                "rejected": 0,
                "timeout": 0,
                "cancelled": 0,
                "approval_rate": 0.0
            }

        approved = sum(1 for req in self.history if req.status == ApprovalStatus.APPROVED)
        rejected = sum(1 for req in self.history if req.status == ApprovalStatus.REJECTED)
        timeout = sum(1 for req in self.history if req.status == ApprovalStatus.TIMEOUT)
        cancelled = sum(1 for req in self.history if req.status == ApprovalStatus.CANCELLED)

        return {
            "total_requests": total,
            "approved": approved,
            "rejected": rejected,
            "timeout": timeout,
            "cancelled": cancelled,
            "approval_rate": approved / total if total > 0 else 0.0
        }

    def _matches_pattern(self, target: str, pattern: str) -> bool:
        """
        Simple pattern matching.

        Supports:
        - Exact match: "file.py"
        - Wildcard: "*.py"
        - Prefix: "/etc/*"
        """
        if pattern == target:
            return True

        if "*" in pattern:
            # Simple wildcard matching
            if pattern.startswith("*"):
                # Suffix match
                return target.endswith(pattern[1:])
            elif pattern.endswith("*"):
                # Prefix match
                return target.startswith(pattern[:-1])
            else:
                # Contains match
                parts = pattern.split("*")
                return target.startswith(parts[0]) and target.endswith(parts[-1])

        return False

    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        self._request_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"approval_{timestamp}_{self._request_counter}"


# Global approval manager instance
_approval_manager: ApprovalManagerV6 | None = None


def get_approval_manager() -> ApprovalManagerV6:
    """Get global approval manager instance."""
    global _approval_manager
    if _approval_manager is None:
        _approval_manager = ApprovalManagerV6()
    return _approval_manager


def set_websocket_callback(callback: Callable) -> None:
    """Set WebSocket callback for approval prompts."""
    manager = get_approval_manager()
    manager.websocket_callback = callback
    logger.info("✅ WebSocket callback registered for approval manager")


# Export
__all__ = [
    "ApprovalManagerV6",
    "ApprovalAction",
    "ApprovalStatus",
    "ApprovalRule",
    "ApprovalRequest",
    "get_approval_manager",
    "set_websocket_callback"
]
