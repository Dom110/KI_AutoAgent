"""
v5.8.3 Phase 3: Supervisor Pattern for Agent Orchestration

LangGraph Best Practice: Formal Supervisor-Worker Pattern
- Supervisor (Orchestrator) delegates tasks to specialized workers
- Workers report back to Supervisor with results
- Supervisor makes routing decisions based on worker outputs

This is a "light" implementation compatible with existing workflow.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

logger = logging.getLogger(__name__)


@dataclass
class WorkerReport:
    """Report from worker agent back to supervisor"""

    agent: str
    task_id: str
    status: Literal["completed", "failed", "needs_help"]
    result: Any
    error: str | None = None
    next_suggestion: str | None = None  # Worker can suggest next agent
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SupervisorOrchestrator:
    """
    Supervisor Pattern Implementation

    Coordinates worker agents using structured communication protocol.
    Workers are specialized agents (architect, codesmith, reviewer, etc.)
    Supervisor analyzes worker reports and routes to next appropriate worker.
    """

    def __init__(self, available_workers: list[str]):
        """
        Initialize Supervisor

        Args:
            available_workers: List of worker agent names
        """
        self.available_workers = available_workers
        self.task_history: list[dict[str, Any]] = []
        self.worker_performance: dict[str, dict[str, int]] = {
            worker: {"completed": 0, "failed": 0, "total": 0}
            for worker in available_workers
        }

    def delegate_task(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """
        Supervisor decides which worker to delegate task to

        Returns:
            Dict with assigned_worker and delegation_message
        """
        # Analyze task to determine best worker
        task_lower = task.lower()

        # Task patterns (ChatGPT-inspired: Pattern recognition)
        if any(
            word in task_lower
            for word in ["design", "architecture", "structure", "analyze"]
        ):
            assigned = "architect"
        elif any(
            word in task_lower for word in ["build", "code", "implement", "create"]
        ):
            assigned = "codesmith"
        elif any(
            word in task_lower for word in ["review", "check", "quality", "validate"]
        ):
            assigned = "reviewer"
        elif any(word in task_lower for word in ["fix", "debug", "repair", "solve"]):
            assigned = "fixer"
        elif any(
            word in task_lower for word in ["research", "find", "search", "investigate"]
        ):
            assigned = "research"
        elif any(
            word in task_lower for word in ["document", "doc", "readme", "explain"]
        ):
            assigned = "docbot"
        else:
            # Default: architect for analysis
            assigned = "architect"

        logger.info(f"🎯 Supervisor delegating to {assigned}: {task[:100]}...")

        return {
            "assigned_worker": assigned,
            "delegation_message": f"Task assigned to {assigned}: {task}",
            "timestamp": datetime.now().isoformat(),
        }

    def process_worker_report(self, report: WorkerReport) -> dict[str, Any]:
        """
        Supervisor processes worker report and decides next action

        Returns:
            Dict with routing decision (next_worker, action, message)
        """
        # Update performance tracking
        self.worker_performance[report.agent]["total"] += 1
        if report.status == "completed":
            self.worker_performance[report.agent]["completed"] += 1
        elif report.status == "failed":
            self.worker_performance[report.agent]["failed"] += 1

        # Record in history
        self.task_history.append(
            {
                "agent": report.agent,
                "task_id": report.task_id,
                "status": report.status,
                "timestamp": datetime.now().isoformat(),
                "next_suggestion": report.next_suggestion,
            }
        )

        # Routing logic based on report
        if report.status == "completed":
            # Check if worker suggested next agent
            if report.next_suggestion:
                logger.info(
                    f"📍 Worker {report.agent} suggests next: {report.next_suggestion}"
                )
                return {
                    "next_worker": report.next_suggestion,
                    "action": "delegate",
                    "message": f"Proceeding to {report.next_suggestion} based on {report.agent}'s suggestion",
                }

            # Default workflow progression
            workflow_sequence = {
                "architect": "codesmith",  # After design → build
                "research": "architect",  # After research → design
                "codesmith": "reviewer",  # After build → review
                "reviewer": "fixer",  # If issues → fix
                "fixer": "reviewer",  # After fix → re-review
                "docbot": None,  # Documentation is final
            }

            next_worker = workflow_sequence.get(report.agent)
            if next_worker:
                return {
                    "next_worker": next_worker,
                    "action": "delegate",
                    "message": f"Workflow: {report.agent} → {next_worker}",
                }
            else:
                return {
                    "next_worker": None,
                    "action": "complete",
                    "message": "Workflow complete",
                }

        elif report.status == "failed":
            # Failure handling
            logger.warning(f"⚠️ Worker {report.agent} failed: {report.error}")

            # Try alternative worker or escalate
            alternatives = {
                "codesmith": "fixer",  # If build fails → try fixer
                "fixer": "opus_arbitrator",  # If fixer fails → escalate to Opus
                "reviewer": "architect",  # If review fails → re-analyze
            }

            alternative = alternatives.get(report.agent)
            if alternative:
                return {
                    "next_worker": alternative,
                    "action": "escalate",
                    "message": f"Escalating from {report.agent} to {alternative}",
                }
            else:
                return {
                    "next_worker": None,
                    "action": "fail",
                    "message": f"Workflow failed at {report.agent}",
                }

        elif report.status == "needs_help":
            # Worker requests assistance
            logger.info(f"🆘 Worker {report.agent} needs help")

            # Route to research for information gathering
            if report.agent != "research":
                return {
                    "next_worker": "research",
                    "action": "assist",
                    "message": f"Providing research assistance to {report.agent}",
                }
            else:
                # If research itself needs help → escalate
                return {
                    "next_worker": "opus_arbitrator",
                    "action": "escalate",
                    "message": "Escalating to Opus for complex decision",
                }

        return {
            "next_worker": None,
            "action": "unknown",
            "message": f"Unknown status: {report.status}",
        }

    def get_performance_summary(self) -> dict[str, Any]:
        """Get worker performance statistics"""
        return {
            "worker_performance": self.worker_performance,
            "total_tasks": len(self.task_history),
            "last_tasks": self.task_history[-10:] if self.task_history else [],
        }


def create_supervisor(available_workers: list[str]) -> SupervisorOrchestrator:
    """
    Factory function to create supervisor

    Example usage in workflow:
        supervisor = create_supervisor([
            "architect", "codesmith", "reviewer",
            "fixer", "research", "docbot"
        ])

        # Delegate task
        delegation = supervisor.delegate_task(
            "Design a dashboard application",
            context={"workspace": "/path/to/project"}
        )

        # Process report
        report = WorkerReport(
            agent="architect",
            task_id="task_1",
            status="completed",
            result=architecture_data,
            next_suggestion="codesmith"
        )
        routing = supervisor.process_worker_report(report)
    """
    return SupervisorOrchestrator(available_workers)
