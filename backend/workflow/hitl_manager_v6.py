"""
HITL Manager v6 - Human-in-the-Loop Collaboration System

Implements interaction patterns for optimal Human-AI collaboration.

Based on: HITL_WORKFLOW_RULES.md
Features:
- Autonomous mode detection
- Progress tracking with non-blocking failures
- Output on demand
- Systematic documentation
- Smart escalation

Integration:
- workflow_v6_integrated.py - Main workflow orchestration
- approval_manager_v6.py - Critical action approvals
- BackendClient (Extension) - WebSocket communication

Author: KI AutoAgent Team
Version: 6.0.0
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class HITLMode(str, Enum):
    """Human-in-the-Loop interaction modes."""

    INTERACTIVE = "interactive"        # User present, ask questions
    AUTONOMOUS = "autonomous"          # User away, don't block
    DEBUG = "debug"                    # Show everything (user debugging)
    PRODUCTION = "production"          # Minimal output


class TaskStatus(str, Enum):
    """Status of individual tasks."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"
    DEFERRED = "deferred"


class EscalationLevel(str, Enum):
    """Levels of issue escalation."""

    NONE = "none"                      # Continue without intervention
    WARNING = "warning"                # Note but continue
    DEFER = "defer"                    # Skip for now, handle later
    BLOCK = "block"                    # Stop and ask for help


@dataclass(slots=True)
class Task:
    """Individual task in workflow."""

    task_id: str
    description: str
    action: Callable
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str | None = None
    duration_ms: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    escalation: EscalationLevel = EscalationLevel.NONE
    recommendation: str | None = None


@dataclass(slots=True)
class SessionReport:
    """Report of HITL session."""

    session_id: str
    mode: HITLMode
    started_at: datetime
    completed_at: datetime | None
    tasks: list[Task]
    total_duration_ms: float = 0.0
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    deferred_count: int = 0
    user_interventions: int = 0
    autonomous_time_ms: float = 0.0
    waiting_time_ms: float = 0.0


class HITLManagerV6:
    """
    Human-in-the-Loop Collaboration Manager.

    Implements optimal interaction patterns between Human and AI Agent.
    """

    def __init__(
        self,
        websocket_callback: Callable | None = None,
        default_mode: HITLMode = HITLMode.INTERACTIVE
    ):
        """
        Initialize HITL manager.

        Args:
            websocket_callback: Async function to send messages via WebSocket
            default_mode: Default interaction mode
        """
        self.websocket_callback = websocket_callback
        self.mode = default_mode
        self.tasks: list[Task] = []
        self.current_task: Task | None = None
        self.session_start = datetime.now()
        self.user_last_seen = datetime.now()
        self._task_counter = 0

        logger.info(f"🤝 HITL Manager v6 initialized (mode: {default_mode.value})")

    def detect_mode(self, user_message: str) -> HITLMode:
        """
        Detect HITL mode from user message.

        Patterns:
        - "nicht da" / "away" → AUTONOMOUS
        - "zeig mir" / "show me" → DEBUG
        - "ULTRATHINK" → DEBUG
        - Default → INTERACTIVE

        Args:
            user_message: Message from user

        Returns:
            Detected HITL mode
        """
        message_lower = user_message.lower()

        # Autonomous mode signals
        autonomous_patterns = [
            "nicht da",
            "away",
            "bin weg",
            "ohne unterbrechung",
            "mach alles",
            "autonom"
        ]

        for pattern in autonomous_patterns:
            if pattern in message_lower:
                logger.info("🤖 Detected AUTONOMOUS mode")
                return HITLMode.AUTONOMOUS

        # Debug mode signals
        debug_patterns = [
            "zeig mir",
            "show me",
            "ultrathink",
            "debug",
            "output",
            "genauen"
        ]

        for pattern in debug_patterns:
            if pattern in message_lower:
                logger.info("🔍 Detected DEBUG mode")
                return HITLMode.DEBUG

        # Default: Interactive
        return HITLMode.INTERACTIVE

    def set_mode(self, mode: HITLMode) -> None:
        """Set HITL interaction mode."""
        old_mode = self.mode
        self.mode = mode

        logger.info(f"🔄 HITL mode changed: {old_mode.value} → {mode.value}")

        # Send mode change via WebSocket
        if self.websocket_callback:
            asyncio.create_task(self._notify_mode_change(mode))

    async def _notify_mode_change(self, mode: HITLMode) -> None:
        """Notify user of mode change via WebSocket."""
        try:
            await self.websocket_callback({
                "type": "hitl_mode_change",
                "mode": mode.value,
                "description": self._get_mode_description(mode),
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to notify mode change: {e}")

    def _get_mode_description(self, mode: HITLMode) -> str:
        """Get human-readable mode description."""
        descriptions = {
            HITLMode.INTERACTIVE: "Agent will ask for clarification when needed",
            HITLMode.AUTONOMOUS: "Agent working independently, minimal interruptions",
            HITLMode.DEBUG: "Detailed output enabled for troubleshooting",
            HITLMode.PRODUCTION: "Production mode, minimal output"
        }
        return descriptions.get(mode, "Unknown mode")

    def add_task(
        self,
        description: str,
        action: Callable,
        timeout_ms: float = 60000.0
    ) -> Task:
        """
        Add task to execution queue.

        Args:
            description: Task description
            action: Async callable to execute
            timeout_ms: Timeout in milliseconds

        Returns:
            Created task
        """
        self._task_counter += 1
        task = Task(
            task_id=f"task_{self._task_counter}",
            description=description,
            action=action
        )

        self.tasks.append(task)
        logger.debug(f"📋 Added task {task.task_id}: {description}")

        return task

    async def execute_tasks(
        self,
        skip_on_error: bool | None = None
    ) -> SessionReport:
        """
        Execute all queued tasks.

        Behavior depends on current HITL mode:
        - INTERACTIVE: Stop on errors, ask for guidance
        - AUTONOMOUS: Skip failures, document and continue
        - DEBUG: Show all output, continue on errors
        - PRODUCTION: Minimal output, stop on critical errors

        Args:
            skip_on_error: Override mode-based skip behavior

        Returns:
            Session report
        """
        logger.info(f"🚀 Executing {len(self.tasks)} tasks (mode: {self.mode.value})")

        # Determine skip behavior
        if skip_on_error is None:
            skip_on_error = self.mode in [HITLMode.AUTONOMOUS, HITLMode.DEBUG]

        session_start = datetime.now()

        for task in self.tasks:
            if task.status != TaskStatus.PENDING:
                continue

            try:
                result = await self._execute_task(task, skip_on_error)

                if result is False and not skip_on_error:
                    # Critical failure in non-skip mode
                    logger.warning(f"⚠️  Stopping execution due to critical failure")
                    break

            except KeyboardInterrupt:
                logger.info("🛑 User interrupted execution")
                task.status = TaskStatus.FAILED
                task.error = "User interrupted"
                break

        session_end = datetime.now()
        duration_ms = (session_end - session_start).total_seconds() * 1000

        # Generate report
        report = self._generate_report(session_start, session_end, duration_ms)

        # Send report via WebSocket (if not in production mode)
        if self.mode != HITLMode.PRODUCTION and self.websocket_callback:
            await self._send_report(report)

        return report

    async def _execute_task(
        self,
        task: Task,
        skip_on_error: bool
    ) -> bool:
        """
        Execute single task.

        Args:
            task: Task to execute
            skip_on_error: Whether to skip on error

        Returns:
            True if task succeeded or was skipped, False if critical failure
        """
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()
        self.current_task = task

        # Notify start (if interactive or debug)
        if self.mode in [HITLMode.INTERACTIVE, HITLMode.DEBUG]:
            logger.info(f"⏳ Starting: {task.description}")
            if self.websocket_callback:
                await self._notify_task_start(task)

        try:
            # Execute task action
            result = await task.action()

            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.duration_ms = (task.completed_at - task.started_at).total_seconds() * 1000

            logger.info(f"✅ Completed: {task.description} ({task.duration_ms:.0f}ms)")

            # Notify completion
            if self.mode in [HITLMode.INTERACTIVE, HITLMode.DEBUG]:
                if self.websocket_callback:
                    await self._notify_task_complete(task)

            return True

        except asyncio.TimeoutError:
            task.status = TaskStatus.DEFERRED if skip_on_error else TaskStatus.FAILED
            task.error = "Timeout"
            task.completed_at = datetime.now()
            task.duration_ms = (task.completed_at - task.started_at).total_seconds() * 1000
            task.escalation = EscalationLevel.DEFER if skip_on_error else EscalationLevel.BLOCK
            task.recommendation = "Increase timeout or profile for bottlenecks"

            logger.warning(f"⏱️  Timeout: {task.description} (deferred)" if skip_on_error else f"❌ Timeout: {task.description}")

            return skip_on_error

        except Exception as e:
            task.status = TaskStatus.SKIPPED if skip_on_error else TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            task.duration_ms = (task.completed_at - task.started_at).total_seconds() * 1000

            # Analyze error for escalation level
            task.escalation = self._analyze_error_escalation(e)
            task.recommendation = self._suggest_fix(task, e)

            if skip_on_error:
                logger.warning(f"⏸️  Skipped: {task.description} - {str(e)[:100]}")
                return True
            else:
                logger.error(f"❌ Failed: {task.description} - {str(e)}")
                return False

    def _analyze_error_escalation(self, error: Exception) -> EscalationLevel:
        """
        Analyze error to determine escalation level.

        Args:
            error: Exception that occurred

        Returns:
            Escalation level
        """
        error_str = str(error).lower()

        # Critical errors - BLOCK
        critical_patterns = [
            "permission denied",
            "access denied",
            "authentication failed",
            "corruption",
            "integrity"
        ]

        for pattern in critical_patterns:
            if pattern in error_str:
                return EscalationLevel.BLOCK

        # Slow operations - DEFER
        if "timeout" in error_str or "too slow" in error_str:
            return EscalationLevel.DEFER

        # Common errors - WARNING
        if any(p in error_str for p in ["not found", "missing", "invalid"]):
            return EscalationLevel.WARNING

        # Default - NONE (continue)
        return EscalationLevel.NONE

    def _suggest_fix(self, task: Task, error: Exception) -> str:
        """
        Suggest fix for task error.

        Args:
            task: Failed task
            error: Exception that occurred

        Returns:
            Suggested fix
        """
        error_str = str(error).lower()

        # Timeout suggestions
        if "timeout" in error_str:
            return "Increase timeout, profile for bottlenecks, or test components individually"

        # File not found
        if "not found" in error_str:
            return "Check file path, ensure dependencies are installed"

        # Permission errors
        if "permission" in error_str:
            return "Check file permissions, run with appropriate privileges"

        # API errors
        if "api" in error_str or "connection" in error_str:
            return "Check API keys, network connection, service status"

        # Default
        return "Review error logs, check configuration, retry with debug output"

    def _generate_report(
        self,
        start_time: datetime,
        end_time: datetime,
        duration_ms: float
    ) -> SessionReport:
        """Generate session report."""
        success_count = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        failed_count = sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)
        skipped_count = sum(1 for t in self.tasks if t.status == TaskStatus.SKIPPED)
        deferred_count = sum(1 for t in self.tasks if t.status == TaskStatus.DEFERRED)

        return SessionReport(
            session_id=f"session_{start_time.strftime('%Y%m%d_%H%M%S')}",
            mode=self.mode,
            started_at=start_time,
            completed_at=end_time,
            tasks=self.tasks.copy(),
            total_duration_ms=duration_ms,
            success_count=success_count,
            failed_count=failed_count,
            skipped_count=skipped_count,
            deferred_count=deferred_count,
            user_interventions=0,  # TODO: Track from approval manager
            autonomous_time_ms=duration_ms,  # TODO: Calculate actual autonomous time
            waiting_time_ms=0.0  # TODO: Calculate actual waiting time
        )

    async def _notify_task_start(self, task: Task) -> None:
        """Notify user of task start via WebSocket."""
        try:
            await self.websocket_callback({
                "type": "task_start",
                "task_id": task.task_id,
                "description": task.description,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.debug(f"Failed to notify task start: {e}")

    async def _notify_task_complete(self, task: Task) -> None:
        """Notify user of task completion via WebSocket."""
        try:
            await self.websocket_callback({
                "type": "task_complete",
                "task_id": task.task_id,
                "description": task.description,
                "status": task.status.value,
                "duration_ms": task.duration_ms,
                "error": task.error,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.debug(f"Failed to notify task complete: {e}")

    async def _send_report(self, report: SessionReport) -> None:
        """Send session report via WebSocket."""
        try:
            await self.websocket_callback({
                "type": "session_report",
                "session_id": report.session_id,
                "mode": report.mode.value,
                "duration_ms": report.total_duration_ms,
                "tasks_total": len(report.tasks),
                "tasks_completed": report.success_count,
                "tasks_failed": report.failed_count,
                "tasks_skipped": report.skipped_count,
                "tasks_deferred": report.deferred_count,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.debug(f"Failed to send report: {e}")

    def format_report_markdown(self, report: SessionReport) -> str:
        """
        Format session report as Markdown.

        Args:
            report: Session report

        Returns:
            Markdown formatted report
        """
        duration_s = report.total_duration_ms / 1000
        success_rate = (report.success_count / len(report.tasks) * 100) if report.tasks else 0

        md = f"""# HITL Session Report - {report.started_at.strftime('%Y-%m-%d %H:%M')}

## Summary
**Mode:** {report.mode.value}
**Duration:** {duration_s:.1f}s
**Tasks:** {len(report.tasks)} total
**Success Rate:** {success_rate:.1f}%

## Task Breakdown
- ✅ Completed: {report.success_count}
- ❌ Failed: {report.failed_count}
- ⏸️  Skipped: {report.skipped_count}
- ⏳ Deferred: {report.deferred_count}

## Tasks Detail

"""

        for task in report.tasks:
            status_emoji = {
                TaskStatus.COMPLETED: "✅",
                TaskStatus.FAILED: "❌",
                TaskStatus.SKIPPED: "⏸️",
                TaskStatus.DEFERRED: "⏳",
                TaskStatus.PENDING: "⏱️",
                TaskStatus.IN_PROGRESS: "🔄"
            }.get(task.status, "❓")

            duration = f" ({task.duration_ms:.0f}ms)" if task.duration_ms > 0 else ""

            md += f"### {status_emoji} {task.description}{duration}\n"

            if task.error:
                md += f"**Error:** `{task.error[:200]}`\n\n"

            if task.escalation != EscalationLevel.NONE:
                md += f"**Escalation:** {task.escalation.value}\n"

            if task.recommendation:
                md += f"**Recommendation:** {task.recommendation}\n"

            md += "\n"

        # Deferred items
        deferred = [t for t in report.tasks if t.status == TaskStatus.DEFERRED]
        if deferred:
            md += "## ⏳ Deferred Items (Needs Attention)\n\n"
            for task in deferred:
                md += f"- **{task.description}**\n"
                md += f"  - Reason: {task.error}\n"
                md += f"  - Recommendation: {task.recommendation}\n\n"

        return md

    def get_status_summary(self) -> dict[str, Any]:
        """Get current HITL status summary."""
        return {
            "mode": self.mode.value,
            "session_duration_s": (datetime.now() - self.session_start).total_seconds(),
            "tasks_total": len(self.tasks),
            "tasks_pending": sum(1 for t in self.tasks if t.status == TaskStatus.PENDING),
            "tasks_in_progress": sum(1 for t in self.tasks if t.status == TaskStatus.IN_PROGRESS),
            "tasks_completed": sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED),
            "tasks_failed": sum(1 for t in self.tasks if t.status == TaskStatus.FAILED),
            "tasks_skipped": sum(1 for t in self.tasks if t.status == TaskStatus.SKIPPED),
            "tasks_deferred": sum(1 for t in self.tasks if t.status == TaskStatus.DEFERRED),
            "current_task": self.current_task.description if self.current_task else None
        }


# Global HITL manager instance
_hitl_manager: HITLManagerV6 | None = None


def get_hitl_manager() -> HITLManagerV6:
    """Get global HITL manager instance."""
    global _hitl_manager
    if _hitl_manager is None:
        _hitl_manager = HITLManagerV6()
    return _hitl_manager


def set_websocket_callback(callback: Callable) -> None:
    """Set WebSocket callback for HITL manager."""
    manager = get_hitl_manager()
    manager.websocket_callback = callback
    logger.info("✅ WebSocket callback registered for HITL manager")


# Export
__all__ = [
    "HITLManagerV6",
    "HITLMode",
    "TaskStatus",
    "EscalationLevel",
    "Task",
    "SessionReport",
    "get_hitl_manager",
    "set_websocket_callback"
]
