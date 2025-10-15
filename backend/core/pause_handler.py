"""
Pause Handler for v6 Workflow System

Handles pausing and resuming workflow execution with state checkpointing.

Features:
- Pause/resume workflow execution
- Save workflow state to checkpoint
- Resume from last checkpoint
- Timeout handling for paused workflows
- Checkpoint cleanup

Author: KI AutoAgent Team
Date: 2025-10-12
Version: v6.1
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PauseAction(Enum):
    """Actions available during pause"""
    RESUME = "resume"
    RESUME_WITH_INSTRUCTIONS = "resume_with_instructions"
    STOP_AND_ROLLBACK = "stop_and_rollback"
    REQUEST_CLARIFICATION = "request_clarification"


class PauseReason:
    """Reasons for pausing workflow."""
    USER_REQUESTED = "user_requested"
    TIMEOUT = "timeout"
    ERROR = "error"
    HITL_REQUIRED = "hitl_required"
    RESOURCE_LIMIT = "resource_limit"
    MANUAL_INTERVENTION = "manual_intervention"


class CheckpointStatus:
    """Checkpoint status values."""
    ACTIVE = "active"
    PAUSED = "paused"
    RESUMED = "resumed"
    EXPIRED = "expired"
    CORRUPTED = "corrupted"


class PauseHandler:
    """
    Handles pausing and resuming workflow execution.

    Features:
    - Save workflow state to checkpoint file
    - Resume from checkpoint
    - Automatic checkpoint expiration
    - Checkpoint validation
    - Timeout handling for paused workflows

    Usage:
        handler = PauseHandler(workspace_path="/path/to/workspace")

        # Pause workflow
        checkpoint_id = await handler.pause_workflow(
            workflow_id="abc123",
            state=current_state,
            reason=PauseReason.HITL_REQUIRED
        )

        # Resume workflow
        state = await handler.resume_workflow(checkpoint_id)
    """

    def __init__(
        self,
        workspace_path: str,
        checkpoint_dir: str | None = None,
        max_checkpoint_age_hours: int = 24,
        cleanup_interval_seconds: int = 3600
    ):
        """
        Initialize Pause Handler.

        Args:
            workspace_path: Path to workspace
            checkpoint_dir: Directory for checkpoint files (default: workspace/.ki_autoagent_ws/checkpoints)
            max_checkpoint_age_hours: Maximum age for checkpoints before expiration
            cleanup_interval_seconds: How often to run cleanup (default: 1 hour)
        """
        self.workspace_path = Path(workspace_path)

        if checkpoint_dir:
            self.checkpoint_dir = Path(checkpoint_dir)
        else:
            self.checkpoint_dir = self.workspace_path / ".ki_autoagent_ws" / "checkpoints"

        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.max_checkpoint_age = timedelta(hours=max_checkpoint_age_hours)
        self.cleanup_interval = cleanup_interval_seconds

        # Active checkpoints (checkpoint_id -> checkpoint_data)
        self.active_checkpoints: dict[str, dict[str, Any]] = {}

        # Cleanup task
        self._cleanup_task: asyncio.Task | None = None

        logger.info(f"✅ PauseHandler initialized")
        logger.info(f"   Checkpoint dir: {self.checkpoint_dir}")
        logger.info(f"   Max age: {max_checkpoint_age_hours}h")

    async def start(self):
        """Start background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("🔄 Started checkpoint cleanup task")

    async def stop(self):
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("🛑 Stopped checkpoint cleanup task")

    async def pause_workflow(
        self,
        workflow_id: str,
        state: dict[str, Any],
        reason: str = PauseReason.USER_REQUESTED,
        metadata: dict[str, Any] | None = None
    ) -> str:
        """
        Pause workflow and save state to checkpoint.

        Args:
            workflow_id: Unique workflow identifier
            state: Current workflow state to save
            reason: Reason for pausing
            metadata: Additional metadata to save

        Returns:
            Checkpoint ID for resuming

        Raises:
            ValueError: If workflow_id or state is invalid
            IOError: If checkpoint cannot be written
        """
        if not workflow_id:
            raise ValueError("workflow_id is required")

        if not state:
            raise ValueError("state is required")

        # Generate checkpoint ID
        checkpoint_id = f"{workflow_id}_{int(time.time())}"

        # Create checkpoint data
        checkpoint_data = {
            "checkpoint_id": checkpoint_id,
            "workflow_id": workflow_id,
            "status": CheckpointStatus.PAUSED,
            "reason": reason,
            "state": state,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + self.max_checkpoint_age).isoformat(),
            "resumed_at": None,
            "resume_count": 0
        }

        # Save to disk
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"

        try:
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)

            # Store in memory
            self.active_checkpoints[checkpoint_id] = checkpoint_data

            logger.info(f"⏸️  Workflow paused: {workflow_id}")
            logger.info(f"   Checkpoint ID: {checkpoint_id}")
            logger.info(f"   Reason: {reason}")
            logger.info(f"   Expires: {checkpoint_data['expires_at']}")

            return checkpoint_id

        except Exception as e:
            logger.error(f"❌ Failed to save checkpoint: {e}", exc_info=True)
            raise IOError(f"Failed to save checkpoint: {e}") from e

    async def resume_workflow(
        self,
        checkpoint_id: str
    ) -> dict[str, Any]:
        """
        Resume workflow from checkpoint.

        Args:
            checkpoint_id: Checkpoint ID to resume from

        Returns:
            Restored workflow state

        Raises:
            ValueError: If checkpoint_id is invalid or checkpoint not found
            RuntimeError: If checkpoint is expired or corrupted
        """
        if not checkpoint_id:
            raise ValueError("checkpoint_id is required")

        # Try to load from memory first
        checkpoint_data = self.active_checkpoints.get(checkpoint_id)

        # If not in memory, load from disk
        if not checkpoint_data:
            checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"

            if not checkpoint_file.exists():
                raise ValueError(f"Checkpoint not found: {checkpoint_id}")

            try:
                with open(checkpoint_file, 'r') as f:
                    checkpoint_data = json.load(f)
            except Exception as e:
                logger.error(f"❌ Failed to load checkpoint: {e}", exc_info=True)
                raise RuntimeError(f"Failed to load checkpoint: {e}") from e

        # Validate checkpoint
        if checkpoint_data["status"] == CheckpointStatus.EXPIRED:
            raise RuntimeError(f"Checkpoint expired: {checkpoint_id}")

        if checkpoint_data["status"] == CheckpointStatus.CORRUPTED:
            raise RuntimeError(f"Checkpoint corrupted: {checkpoint_id}")

        # Check expiration
        expires_at = datetime.fromisoformat(checkpoint_data["expires_at"])
        if datetime.now() > expires_at:
            checkpoint_data["status"] = CheckpointStatus.EXPIRED
            await self._update_checkpoint(checkpoint_id, checkpoint_data)
            raise RuntimeError(f"Checkpoint expired: {checkpoint_id}")

        # Update checkpoint
        checkpoint_data["status"] = CheckpointStatus.RESUMED
        checkpoint_data["resumed_at"] = datetime.now().isoformat()
        checkpoint_data["resume_count"] += 1

        await self._update_checkpoint(checkpoint_id, checkpoint_data)

        logger.info(f"▶️  Workflow resumed: {checkpoint_data['workflow_id']}")
        logger.info(f"   Checkpoint ID: {checkpoint_id}")
        logger.info(f"   Resume count: {checkpoint_data['resume_count']}")

        # Return restored state
        return checkpoint_data["state"]

    async def get_checkpoint(
        self,
        checkpoint_id: str
    ) -> dict[str, Any] | None:
        """
        Get checkpoint data without resuming.

        Args:
            checkpoint_id: Checkpoint ID

        Returns:
            Checkpoint data or None if not found
        """
        # Try memory first
        checkpoint_data = self.active_checkpoints.get(checkpoint_id)

        if checkpoint_data:
            return checkpoint_data

        # Try disk
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"

        if not checkpoint_file.exists():
            return None

        try:
            with open(checkpoint_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Failed to load checkpoint: {e}")
            return None

    async def list_checkpoints(
        self,
        workflow_id: str | None = None,
        status: str | None = None
    ) -> list[dict[str, Any]]:
        """
        List all checkpoints.

        Args:
            workflow_id: Filter by workflow ID (optional)
            status: Filter by status (optional)

        Returns:
            List of checkpoint summaries
        """
        checkpoints = []

        # Scan checkpoint directory
        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            try:
                with open(checkpoint_file, 'r') as f:
                    data = json.load(f)

                # Apply filters
                if workflow_id and data.get("workflow_id") != workflow_id:
                    continue

                if status and data.get("status") != status:
                    continue

                # Return summary (without full state)
                checkpoints.append({
                    "checkpoint_id": data["checkpoint_id"],
                    "workflow_id": data["workflow_id"],
                    "status": data["status"],
                    "reason": data["reason"],
                    "created_at": data["created_at"],
                    "expires_at": data["expires_at"],
                    "resumed_at": data.get("resumed_at"),
                    "resume_count": data.get("resume_count", 0)
                })

            except Exception as e:
                logger.error(f"❌ Failed to load checkpoint {checkpoint_file}: {e}")
                continue

        # Sort by created_at (newest first)
        checkpoints.sort(key=lambda x: x["created_at"], reverse=True)

        return checkpoints

    async def delete_checkpoint(
        self,
        checkpoint_id: str
    ) -> bool:
        """
        Delete checkpoint.

        Args:
            checkpoint_id: Checkpoint ID to delete

        Returns:
            True if deleted, False if not found
        """
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"

        if not checkpoint_file.exists():
            return False

        try:
            checkpoint_file.unlink()

            # Remove from memory
            self.active_checkpoints.pop(checkpoint_id, None)

            logger.info(f"🗑️  Deleted checkpoint: {checkpoint_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to delete checkpoint: {e}")
            return False

    async def cleanup_expired_checkpoints(self) -> int:
        """
        Clean up expired checkpoints.

        Returns:
            Number of checkpoints deleted
        """
        deleted_count = 0
        now = datetime.now()

        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            try:
                with open(checkpoint_file, 'r') as f:
                    data = json.load(f)

                expires_at = datetime.fromisoformat(data["expires_at"])

                if now > expires_at:
                    checkpoint_file.unlink()
                    self.active_checkpoints.pop(data["checkpoint_id"], None)
                    deleted_count += 1
                    logger.debug(f"🗑️  Deleted expired checkpoint: {data['checkpoint_id']}")

            except Exception as e:
                logger.error(f"❌ Failed to cleanup checkpoint {checkpoint_file}: {e}")
                continue

        if deleted_count > 0:
            logger.info(f"🧹 Cleaned up {deleted_count} expired checkpoints")

        return deleted_count

    async def _update_checkpoint(
        self,
        checkpoint_id: str,
        checkpoint_data: dict[str, Any]
    ):
        """Update checkpoint on disk and in memory."""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"

        try:
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)

            self.active_checkpoints[checkpoint_id] = checkpoint_data

        except Exception as e:
            logger.error(f"❌ Failed to update checkpoint: {e}")

    async def _cleanup_loop(self):
        """Background task to cleanup expired checkpoints."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_expired_checkpoints()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Cleanup loop error: {e}", exc_info=True)


# Global singleton
_pause_handler_instance: PauseHandler | None = None


def get_pause_handler(workspace_path: str | None = None) -> PauseHandler:
    """
    Get global PauseHandler instance (singleton).

    Args:
        workspace_path: Workspace path (required on first call)

    Returns:
        Global PauseHandler instance

    Raises:
        ValueError: If workspace_path not provided on first call
    """
    global _pause_handler_instance

    if _pause_handler_instance is None:
        if workspace_path is None:
            raise ValueError("workspace_path required for first call")

        _pause_handler_instance = PauseHandler(workspace_path)

    return _pause_handler_instance
