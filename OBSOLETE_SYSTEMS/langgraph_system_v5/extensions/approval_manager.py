"""
Approval Manager for Human-in-the-Loop workflows
Handles Plan-First mode with user approval
"""

import asyncio
import uuid
import logging
from typing import Dict, Any, Literal, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ApprovalRequest:
    """Represents an approval request"""
    approval_id: str
    client_id: str
    plan: Any
    created_at: datetime
    expires_at: datetime
    status: Literal["pending", "approved", "rejected", "modified", "expired"]
    response: Optional[Dict[str, Any]] = None
    feedback: Optional[str] = None
    modifications: Optional[Dict[str, Any]] = None


class ApprovalManager:
    """
    Manages approval requests for Plan-First mode
    Handles communication with frontend for user approval
    """

    def __init__(self, websocket_manager=None, timeout_seconds: int = 300):
        """
        Initialize approval manager

        Args:
            websocket_manager: WebSocket connection manager for UI communication
            timeout_seconds: Default timeout for approval requests (default: 5 minutes)
        """
        self.websocket_manager = websocket_manager
        self.timeout_seconds = timeout_seconds
        self.pending_approvals: Dict[str, asyncio.Future] = {}
        self.approval_requests: Dict[str, ApprovalRequest] = {}
        self.approval_history: List[ApprovalRequest] = []

    async def request_approval(
        self,
        client_id: str,
        plan: Any,
        timeout: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ApprovalRequest:
        """
        Request approval from user for an execution plan

        Args:
            client_id: WebSocket client ID for communication
            plan: Execution plan to be approved
            timeout: Custom timeout in seconds (overrides default)
            metadata: Additional metadata for the approval request

        Returns:
            ApprovalRequest with status and user response
        """
        approval_id = str(uuid.uuid4())
        timeout = timeout or self.timeout_seconds

        # Create approval request
        request = ApprovalRequest(
            approval_id=approval_id,
            client_id=client_id,
            plan=plan,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=timeout),
            status="pending"
        )

        # Store request
        self.approval_requests[approval_id] = request

        # Create future for async waiting
        future = asyncio.Future()
        self.pending_approvals[approval_id] = future

        # Send to frontend if websocket available
        if self.websocket_manager:
            await self._send_approval_request_to_ui(request, metadata)

        try:
            # Wait for user response with timeout
            response = await asyncio.wait_for(future, timeout=timeout)

            # Update request with response
            request.response = response
            request.status = response.get("action", "approved")
            request.feedback = response.get("feedback")
            request.modifications = response.get("modifications")

        except asyncio.TimeoutError:
            logger.warning(f"Approval request {approval_id} timed out")
            request.status = "expired"

        except Exception as e:
            logger.error(f"Error in approval request {approval_id}: {str(e)}")
            request.status = "rejected"

        finally:
            # Clean up
            if approval_id in self.pending_approvals:
                del self.pending_approvals[approval_id]

            # Add to history
            self.approval_history.append(request)

        return request

    async def _send_approval_request_to_ui(
        self,
        request: ApprovalRequest,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Send approval request to UI via WebSocket"""
        message = {
            "type": "approval_request",
            "approval_id": request.approval_id,
            "plan": self._format_plan_for_ui(request.plan),
            "metadata": metadata or {},
            "expires_at": request.expires_at.isoformat(),
            "actions": [
                {
                    "id": "approve",
                    "label": "✅ Approve",
                    "style": "primary"
                },
                {
                    "id": "reject",
                    "label": "❌ Reject",
                    "style": "danger"
                },
                {
                    "id": "modify",
                    "label": "✏️ Modify",
                    "style": "warning"
                }
            ]
        }

        if self.websocket_manager:
            await self.websocket_manager.send_json(request.client_id, message)

    def _format_plan_for_ui(self, plan: Any) -> Dict[str, Any]:
        """Format execution plan for UI display"""
        if isinstance(plan, list):
            # Format list of execution steps
            return {
                "type": "execution_steps",
                "steps": [self._format_step(step) for step in plan]
            }
        elif hasattr(plan, '__dict__'):
            # Format object with attributes
            return {
                "type": "structured_plan",
                "content": asdict(plan) if hasattr(plan, '__dataclass_fields__') else vars(plan)
            }
        else:
            # Return as-is
            return {
                "type": "raw",
                "content": str(plan)
            }

    def _format_step(self, step: Any) -> Dict[str, Any]:
        """Format individual execution step"""
        if hasattr(step, '__dict__'):
            step_dict = asdict(step) if hasattr(step, '__dataclass_fields__') else vars(step)
            return {
                "id": step_dict.get("id", "unknown"),
                "agent": step_dict.get("agent", "unknown"),
                "task": step_dict.get("task", ""),
                "expected_output": step_dict.get("expected_output", ""),
                "dependencies": step_dict.get("dependencies", []),
                "status": step_dict.get("status", "pending")
            }
        return {"content": str(step)}

    async def handle_user_response(
        self,
        approval_id: str,
        response: Dict[str, Any]
    ) -> bool:
        """
        Handle user response to approval request

        Args:
            approval_id: ID of the approval request
            response: User response containing action and optional feedback

        Returns:
            True if response was processed successfully
        """
        if approval_id not in self.pending_approvals:
            logger.warning(f"No pending approval found for ID: {approval_id}")
            return False

        # Resolve the future with the response
        future = self.pending_approvals[approval_id]
        if not future.done():
            future.set_result(response)
            logger.info(f"Approval {approval_id} resolved with action: {response.get('action')}")
            return True

        return False

    def get_approval_status(self, approval_id: str) -> Optional[str]:
        """Get the status of an approval request"""
        if approval_id in self.approval_requests:
            return self.approval_requests[approval_id].status
        return None

    def get_approval_history(
        self,
        client_id: Optional[str] = None,
        limit: int = 10
    ) -> List[ApprovalRequest]:
        """Get approval history, optionally filtered by client"""
        history = self.approval_history

        if client_id:
            history = [r for r in history if r.client_id == client_id]

        # Sort by created_at descending and limit
        history.sort(key=lambda x: x.created_at, reverse=True)
        return history[:limit]

    async def auto_approve(self, approval_id: str) -> bool:
        """Auto-approve a pending request (for testing or automation)"""
        return await self.handle_user_response(
            approval_id,
            {"action": "approved", "auto": True}
        )

    async def auto_reject(self, approval_id: str, reason: str = "") -> bool:
        """Auto-reject a pending request"""
        return await self.handle_user_response(
            approval_id,
            {"action": "rejected", "feedback": reason, "auto": True}
        )

    def cleanup_expired(self):
        """Clean up expired approval requests"""
        now = datetime.now()
        expired_ids = []

        for approval_id, request in self.approval_requests.items():
            if request.status == "pending" and request.expires_at < now:
                request.status = "expired"
                expired_ids.append(approval_id)

                # Cancel the future if still pending
                if approval_id in self.pending_approvals:
                    future = self.pending_approvals[approval_id]
                    if not future.done():
                        future.cancel()

        # Clean up
        for approval_id in expired_ids:
            if approval_id in self.pending_approvals:
                del self.pending_approvals[approval_id]

        logger.info(f"Cleaned up {len(expired_ids)} expired approval requests")

    def get_pending_approvals(self, client_id: Optional[str] = None) -> List[ApprovalRequest]:
        """Get all pending approval requests"""
        pending = [
            r for r in self.approval_requests.values()
            if r.status == "pending"
        ]

        if client_id:
            pending = [r for r in pending if r.client_id == client_id]

        return pending

    async def modify_plan(
        self,
        approval_id: str,
        modifications: Dict[str, Any],
        feedback: str = ""
    ) -> bool:
        """Handle plan modification request from user"""
        response = {
            "action": "modified",
            "modifications": modifications,
            "feedback": feedback
        }
        return await self.handle_user_response(approval_id, response)