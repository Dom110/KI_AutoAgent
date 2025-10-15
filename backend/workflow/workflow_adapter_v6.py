"""
Workflow Adapter v6 - Dynamic Workflow Adaptation

Capabilities:
- Adapt workflow based on intermediate results
- Insert/skip/reorder agents dynamically
- Context-aware decision making
- Error-driven adaptation
- Quality-driven optimization

Integration:
- After each agent execution
- Before final workflow completion
- On error/quality issues

Author: KI AutoAgent Team
Version: 6.0.0
Python: 3.13+
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AdaptationType(str, Enum):
    """Types of workflow adaptations."""

    INSERT_AGENT = "insert_agent"
    SKIP_AGENT = "skip_agent"
    REORDER_AGENTS = "reorder_agents"
    REPEAT_AGENT = "repeat_agent"
    CHANGE_PARAMETERS = "change_parameters"
    ABORT_WORKFLOW = "abort_workflow"


class AdaptationReason(str, Enum):
    """Reasons for adaptation."""

    ERROR_DETECTED = "error_detected"
    QUALITY_ISSUE = "quality_issue"
    MISSING_DEPENDENCY = "missing_dependency"
    OPTIMIZATION = "optimization"
    USER_FEEDBACK = "user_feedback"
    RESOURCE_CONSTRAINT = "resource_constraint"


@dataclass
class WorkflowContext:
    """Context for workflow execution."""

    task_description: str
    current_phase: str
    completed_agents: list[str]
    pending_agents: list[str]
    results: dict[str, Any]
    errors: list[dict[str, Any]]
    quality_scores: dict[str, float]
    metadata: dict[str, Any]

    # Essential for multi-workspace support
    workspace_path: str
    start_time: Any  # datetime object


@dataclass
class AdaptationDecision:
    """Decision to adapt workflow."""

    adaptation_type: AdaptationType
    reason: AdaptationReason
    agent_id: str | None
    details: dict[str, Any]
    confidence: float
    timestamp: datetime


class WorkflowAdapterV6:
    """
    Dynamic Workflow Adaptation System.

    Analyzes intermediate results and adapts workflow execution.
    """

    def __init__(self, learning_system: Any | None = None):
        """
        Initialize workflow adapter.

        Args:
            learning_system: Optional learning system for historical data
        """
        self.learning_system = learning_system
        self.adaptation_history: list[AdaptationDecision] = []
        self.rules: dict[str, Any] = {}

        # Default adaptation rules
        self._setup_default_rules()

        logger.info("🔄 Workflow Adapter v6 initialized")

    def _setup_default_rules(self) -> None:
        """Setup default adaptation rules."""

        self.rules = {
            # If Architect finds missing dependencies, insert Research
            "missing_dependency": {
                "trigger": "dependency_not_found",
                "adaptation": AdaptationType.INSERT_AGENT,
                "agent": "research",
                "before": "codesmith"
            },

            # If Codesmith produces low quality, insert ReviewFix
            "low_quality_code": {
                "trigger": "quality_score < 0.7",
                "adaptation": AdaptationType.INSERT_AGENT,
                "agent": "reviewer",
                "after": "codesmith"
            },

            # If multiple errors detected, repeat Fixer
            "persistent_errors": {
                "trigger": "error_count > 3",
                "adaptation": AdaptationType.REPEAT_AGENT,
                "agent": "fixer",
                "max_repeats": 2
            },

            # If tests fail, skip Deployment
            "tests_failing": {
                "trigger": "test_status == failed",
                "adaptation": AdaptationType.SKIP_AGENT,
                "agent": "deployment"
            },

            # If critical error, abort workflow
            "critical_error": {
                "trigger": "error_severity == critical",
                "adaptation": AdaptationType.ABORT_WORKFLOW,
                "reason": "Critical error detected"
            }
        }

    async def analyze_and_adapt(
        self,
        context: WorkflowContext
    ) -> list[AdaptationDecision]:
        """
        Analyze workflow context and suggest adaptations.

        Args:
            context: Current workflow context

        Returns:
            List of adaptation decisions
        """
        logger.info(f"🔍 Analyzing workflow: {context.current_phase}")
        logger.debug(f"   Completed: {context.completed_agents}")
        logger.debug(f"   Pending: {context.pending_agents}")
        logger.debug(f"   Errors: {len(context.errors)}")

        decisions: list[AdaptationDecision] = []

        # Check for errors
        error_decisions = await self._check_for_errors(context)
        decisions.extend(error_decisions)

        # Check for quality issues
        quality_decisions = await self._check_quality(context)
        decisions.extend(quality_decisions)

        # Check for missing dependencies
        dependency_decisions = await self._check_dependencies(context)
        decisions.extend(dependency_decisions)

        # Check for optimization opportunities
        if self.learning_system:
            optimization_decisions = await self._check_optimizations(context)
            decisions.extend(optimization_decisions)

        # Log decisions
        if decisions:
            logger.info(f"✅ Generated {len(decisions)} adaptation decisions")
            for decision in decisions:
                logger.debug(f"   {decision.adaptation_type.value}: {decision.reason.value}")
        else:
            logger.debug("   No adaptations needed")

        return decisions

    async def _check_for_errors(
        self,
        context: WorkflowContext
    ) -> list[AdaptationDecision]:
        """Check for errors and suggest adaptations."""
        decisions = []

        if not context.errors:
            return decisions

        # Count errors
        error_count = len(context.errors)

        # Check for critical errors
        critical_errors = [
            err for err in context.errors
            if err.get("severity") == "critical"
        ]

        if critical_errors:
            logger.warning(f"⚠️  Critical errors detected: {len(critical_errors)}")
            decisions.append(AdaptationDecision(
                adaptation_type=AdaptationType.ABORT_WORKFLOW,
                reason=AdaptationReason.ERROR_DETECTED,
                agent_id=None,
                details={"errors": critical_errors},
                confidence=1.0,
                timestamp=datetime.now()
            ))
            return decisions

        # Check for persistent errors (need to repeat Fixer)
        if error_count > 3 and "fixer" in context.completed_agents:
            # Count how many times fixer has run
            fixer_runs = context.completed_agents.count("fixer")

            if fixer_runs < 2:
                logger.info(f"🔁 Persistent errors ({error_count}), repeating Fixer")
                decisions.append(AdaptationDecision(
                    adaptation_type=AdaptationType.REPEAT_AGENT,
                    reason=AdaptationReason.ERROR_DETECTED,
                    agent_id="fixer",
                    details={"error_count": error_count, "current_runs": fixer_runs},
                    confidence=0.9,
                    timestamp=datetime.now()
                ))

        return decisions

    async def _check_quality(
        self,
        context: WorkflowContext
    ) -> list[AdaptationDecision]:
        """Check quality scores and suggest improvements."""
        decisions = []

        if not context.quality_scores:
            return decisions

        # Check if Codesmith produced low quality code
        codesmith_quality = context.quality_scores.get("codesmith")
        if codesmith_quality is not None and codesmith_quality < 0.7:
            # Check if reviewer is already in the pipeline
            if "reviewer" not in context.completed_agents and "reviewer" not in context.pending_agents:
                logger.info(f"⚠️  Low quality code ({codesmith_quality:.2f}), inserting Reviewer")
                decisions.append(AdaptationDecision(
                    adaptation_type=AdaptationType.INSERT_AGENT,
                    reason=AdaptationReason.QUALITY_ISSUE,
                    agent_id="reviewer",
                    details={
                        "quality_score": codesmith_quality,
                        "insert_after": "codesmith"
                    },
                    confidence=0.85,
                    timestamp=datetime.now()
                ))

        return decisions

    async def _check_dependencies(
        self,
        context: WorkflowContext
    ) -> list[AdaptationDecision]:
        """Check for missing dependencies."""
        decisions = []

        # Check if Architect mentioned missing dependencies
        architect_result = context.results.get("architect", {})

        if isinstance(architect_result, dict):
            dependencies = architect_result.get("dependencies", [])
            missing_deps = [dep for dep in dependencies if dep.get("status") == "missing"]

            if missing_deps and "research" not in context.completed_agents:
                logger.info(f"🔍 Missing dependencies detected: {len(missing_deps)}, inserting Research")
                decisions.append(AdaptationDecision(
                    adaptation_type=AdaptationType.INSERT_AGENT,
                    reason=AdaptationReason.MISSING_DEPENDENCY,
                    agent_id="research",
                    details={
                        "missing_dependencies": [dep.get("name") for dep in missing_deps],
                        "insert_before": "codesmith"
                    },
                    confidence=0.95,
                    timestamp=datetime.now()
                ))

        return decisions

    async def _check_optimizations(
        self,
        context: WorkflowContext
    ) -> list[AdaptationDecision]:
        """Check for optimization opportunities using learning system."""
        decisions = []

        if not self.learning_system:
            return decisions

        try:
            # Get suggestions from learning system
            suggestions = await self.learning_system.suggest_optimizations(
                task_description=context.task_description,
                project_type=context.metadata.get("project_type")
            )

            # Parse suggestions - handle both string and dict formats
            for suggestion in suggestions.get("suggestions", []):
                # Current learning_system returns strings, not structured dicts
                if isinstance(suggestion, str):
                    # Log informational suggestion, skip structured parsing
                    logger.debug(f"💡 Optimization suggestion: {suggestion}")
                    continue

                # Future format: structured dict with type, agent, confidence
                if isinstance(suggestion, dict) and suggestion.get("type") == "skip_agent":
                    agent_to_skip = suggestion.get("agent")
                    if agent_to_skip in context.pending_agents:
                        logger.info(f"⚡ Optimization: Skipping {agent_to_skip}")
                        decisions.append(AdaptationDecision(
                            adaptation_type=AdaptationType.SKIP_AGENT,
                            reason=AdaptationReason.OPTIMIZATION,
                            agent_id=agent_to_skip,
                            details={"suggestion": suggestion},
                            confidence=suggestion.get("confidence", 0.7),
                            timestamp=datetime.now()
                        ))

        except Exception as e:
            logger.warning(f"⚠️  Failed to check optimizations: {e}")

        return decisions

    async def apply_adaptation(
        self,
        decision: AdaptationDecision,
        context: WorkflowContext
    ) -> WorkflowContext:
        """
        Apply adaptation decision to workflow context.

        Args:
            decision: Adaptation decision to apply
            context: Current workflow context

        Returns:
            Updated workflow context
        """
        logger.info(f"🔄 Applying adaptation: {decision.adaptation_type.value}")

        # Record in history
        self.adaptation_history.append(decision)

        # Apply based on type
        if decision.adaptation_type == AdaptationType.INSERT_AGENT:
            context = self._insert_agent(decision, context)

        elif decision.adaptation_type == AdaptationType.SKIP_AGENT:
            context = self._skip_agent(decision, context)

        elif decision.adaptation_type == AdaptationType.REPEAT_AGENT:
            context = self._repeat_agent(decision, context)

        elif decision.adaptation_type == AdaptationType.REORDER_AGENTS:
            context = self._reorder_agents(decision, context)

        elif decision.adaptation_type == AdaptationType.ABORT_WORKFLOW:
            context.metadata["aborted"] = True
            context.metadata["abort_reason"] = decision.details

        elif decision.adaptation_type == AdaptationType.CHANGE_PARAMETERS:
            context.metadata["parameters"] = decision.details

        return context

    def _insert_agent(
        self,
        decision: AdaptationDecision,
        context: WorkflowContext
    ) -> WorkflowContext:
        """Insert agent into workflow."""
        agent_id = decision.agent_id

        if not agent_id:
            logger.warning("⚠️  No agent_id provided for INSERT_AGENT")
            return context

        # Determine position
        insert_before = decision.details.get("insert_before")
        insert_after = decision.details.get("insert_after")

        if insert_before and insert_before in context.pending_agents:
            idx = context.pending_agents.index(insert_before)
            context.pending_agents.insert(idx, agent_id)
            logger.info(f"✅ Inserted {agent_id} before {insert_before}")

        elif insert_after:
            # Insert at beginning of pending
            context.pending_agents.insert(0, agent_id)
            logger.info(f"✅ Inserted {agent_id} at beginning")

        else:
            # Append to end
            context.pending_agents.append(agent_id)
            logger.info(f"✅ Appended {agent_id} to end")

        return context

    def _skip_agent(
        self,
        decision: AdaptationDecision,
        context: WorkflowContext
    ) -> WorkflowContext:
        """Skip agent in workflow."""
        agent_id = decision.agent_id

        if agent_id and agent_id in context.pending_agents:
            context.pending_agents.remove(agent_id)
            logger.info(f"✅ Skipped {agent_id}")
        else:
            logger.warning(f"⚠️  Agent {agent_id} not in pending list")

        return context

    def _repeat_agent(
        self,
        decision: AdaptationDecision,
        context: WorkflowContext
    ) -> WorkflowContext:
        """Repeat agent execution."""
        agent_id = decision.agent_id

        if agent_id:
            # Insert at beginning of pending
            context.pending_agents.insert(0, agent_id)
            logger.info(f"✅ Scheduled repeat of {agent_id}")

        return context

    def _reorder_agents(
        self,
        decision: AdaptationDecision,
        context: WorkflowContext
    ) -> WorkflowContext:
        """Reorder agents in workflow."""
        new_order = decision.details.get("order", [])

        if new_order:
            context.pending_agents = new_order
            logger.info(f"✅ Reordered agents: {new_order}")

        return context

    def get_adaptation_stats(self) -> dict[str, Any]:
        """Get adaptation statistics."""
        if not self.adaptation_history:
            return {
                "total_adaptations": 0,
                "by_type": {},
                "by_reason": {}
            }

        # Count by type
        by_type: dict[str, int] = {}
        for decision in self.adaptation_history:
            adaptation_type = decision.adaptation_type.value
            by_type[adaptation_type] = by_type.get(adaptation_type, 0) + 1

        # Count by reason
        by_reason: dict[str, int] = {}
        for decision in self.adaptation_history:
            reason = decision.reason.value
            by_reason[reason] = by_reason.get(reason, 0) + 1

        return {
            "total_adaptations": len(self.adaptation_history),
            "by_type": by_type,
            "by_reason": by_reason,
            "recent": [
                {
                    "type": d.adaptation_type.value,
                    "reason": d.reason.value,
                    "agent": d.agent_id,
                    "timestamp": d.timestamp.isoformat()
                }
                for d in self.adaptation_history[-5:]
            ]
        }


# Global adapter instance
_adapter: WorkflowAdapterV6 | None = None


def get_workflow_adapter() -> WorkflowAdapterV6:
    """Get global workflow adapter instance."""
    global _adapter
    if _adapter is None:
        _adapter = WorkflowAdapterV6()
    return _adapter


# Export
__all__ = [
    "WorkflowAdapterV6",
    "WorkflowContext",
    "AdaptationDecision",
    "AdaptationType",
    "AdaptationReason",
    "get_workflow_adapter"
]
