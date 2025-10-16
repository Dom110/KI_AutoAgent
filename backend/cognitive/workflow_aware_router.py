"""
Workflow-Aware Router - Intelligent Dynamic Routing

This module provides intelligent routing logic that respects the AI-generated
workflow plan while maintaining compatibility with LangGraph's fixed edges.

The solution: Hybrid routing that checks:
1. Is there a next agent in the workflow_path?
2. If yes, route to it
3. If no, use default logic or END

This allows dynamic workflows within LangGraph's constraints.

Author: KI AutoAgent Team
Version: 6.4.0-beta
Python: 3.13+
"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END

logger = logging.getLogger(__name__)


class WorkflowAwareRouter:
    """
    Intelligent router that respects workflow plans.

    This router bridges the gap between:
    - Fixed LangGraph edges (static graph structure)
    - Dynamic AI-generated workflow plans

    The key insight: We keep the fixed edges but make the decision
    functions intelligent enough to follow the plan OR fallback to
    sensible defaults.
    """

    def __init__(self):
        """Initialize router."""
        # Track workflow execution
        self.workflow_plan: list[str] = []
        self.completed_agents: list[str] = []
        self.agent_modes: dict[str, str] = {}

        logger.info("🧠 Workflow-Aware Router initialized")

    def set_workflow_plan(
        self,
        workflow_path: list[str],
        agent_modes: dict[str, str] | None = None
    ):
        """
        Set the workflow plan from AI planner.

        Args:
            workflow_path: Ordered list of agent names
            agent_modes: Optional mode per agent
        """
        self.workflow_plan = workflow_path.copy()
        self.agent_modes = agent_modes or {}
        self.completed_agents = []

        logger.info(f"📋 Workflow plan set: {' → '.join(workflow_path)}")
        if agent_modes:
            logger.debug(f"   Agent modes: {agent_modes}")

    def mark_completed(self, agent: str):
        """
        Mark an agent as completed.

        Args:
            agent: Agent name
        """
        if agent not in self.completed_agents:
            self.completed_agents.append(agent)
            logger.debug(f"   ✓ {agent} marked complete")

    def get_next_in_plan(self, current_agent: str) -> str | None:
        """
        Get the next agent in the workflow plan.

        Args:
            current_agent: Current agent name

        Returns:
            Next agent name or None if end of plan
        """
        # Find current agent's position in plan
        try:
            current_index = self.workflow_plan.index(current_agent)

            # Check if there's a next agent
            if current_index + 1 < len(self.workflow_plan):
                next_agent = self.workflow_plan[current_index + 1]
                logger.info(f"🔀 Plan says: {current_agent} → {next_agent}")
                return next_agent
            else:
                logger.info(f"🔀 Plan says: {current_agent} → END (last in plan)")
                return END

        except ValueError:
            # Current agent not in plan - shouldn't happen
            logger.warning(f"⚠️ {current_agent} not in workflow plan")
            return None

    def should_skip_to_end(self, agent_type: str, state: dict[str, Any]) -> bool:
        """
        Check if we should skip remaining agents and end.

        This handles EXPLAIN/ANALYZE workflows that don't need all agents.

        Args:
            agent_type: Current agent type
            state: Current state

        Returns:
            True if should end workflow
        """
        # Get workflow metadata
        workflow_type = state.get("workflow_type", "CREATE")

        # EXPLAIN workflow: Research only
        if workflow_type == "EXPLAIN":
            if agent_type == "research" and "analyze" in self.agent_modes.get("research", ""):
                logger.info("🏁 EXPLAIN workflow complete after research:analyze")
                return True

        # ANALYZE workflow: Research + optional ReviewFix
        if workflow_type == "ANALYZE":
            if agent_type == "research" and self.completed_agents.count("research") >= 1:
                # Check if we found issues that need review
                research_results = state.get("research_results", {})
                if not research_results.get("issues"):
                    logger.info("🏁 ANALYZE workflow complete (no issues found)")
                    return True

        return False

    # ========================================================================
    # INTELLIGENT DECISION FUNCTIONS
    # ========================================================================

    def research_decide_next(
        self,
        state: dict[str, Any],
        fallback_logic: callable | None = None
    ) -> str:
        """
        Intelligent routing for Research agent.

        Args:
            state: Current workflow state
            fallback_logic: Original decision function

        Returns:
            Next agent name or END
        """
        logger.info("🔬 === RESEARCH ROUTING ===")

        # Check if we should end (EXPLAIN/ANALYZE workflows)
        if self.should_skip_to_end("research", state):
            return END

        # Check workflow plan
        next_in_plan = self.get_next_in_plan("research")
        if next_in_plan:
            return next_in_plan

        # Fallback to original logic if no plan
        if fallback_logic:
            return fallback_logic(state)

        # Default: architect for CREATE, END for others
        workflow_type = state.get("workflow_type", "CREATE")
        if workflow_type == "CREATE":
            return "architect"

        return END

    def architect_decide_next(
        self,
        state: dict[str, Any],
        fallback_logic: callable | None = None
    ) -> str:
        """
        Intelligent routing for Architect agent.

        Args:
            state: Current workflow state
            fallback_logic: Original decision function

        Returns:
            Next agent name or END
        """
        logger.info("📐 === ARCHITECT ROUTING ===")

        # Check workflow plan
        next_in_plan = self.get_next_in_plan("architect")
        if next_in_plan:
            return next_in_plan

        # Fallback to original logic
        if fallback_logic:
            return fallback_logic(state)

        # Default: codesmith for CREATE
        return "codesmith"

    def codesmith_decide_next(
        self,
        state: dict[str, Any],
        fallback_logic: callable | None = None
    ) -> str:
        """
        Intelligent routing for Codesmith agent.

        Args:
            state: Current workflow state
            fallback_logic: Original decision function

        Returns:
            Next agent name or END
        """
        logger.info("⚒️ === CODESMITH ROUTING ===")

        # Check workflow plan
        next_in_plan = self.get_next_in_plan("codesmith")
        if next_in_plan:
            return next_in_plan

        # Fallback to original logic
        if fallback_logic:
            return fallback_logic(state)

        # Default: reviewfix
        return "reviewfix"

    def reviewfix_decide_next(
        self,
        state: dict[str, Any],
        fallback_logic: callable | None = None
    ) -> str:
        """
        Intelligent routing for ReviewFix agent.

        Args:
            state: Current workflow state
            fallback_logic: Original decision function

        Returns:
            Next agent name or END
        """
        logger.info("🔬 === REVIEWFIX ROUTING ===")

        # Check if quality is good enough
        review_feedback = state.get("review_feedback", {})
        if isinstance(review_feedback, dict):
            quality_score = review_feedback.get("quality_score", 0)
            if quality_score >= 0.75:
                logger.info(f"✅ Quality good ({quality_score:.2f}), ending workflow")
                return END

        # Check workflow plan
        next_in_plan = self.get_next_in_plan("reviewfix")
        if next_in_plan:
            return next_in_plan

        # Fallback to original logic
        if fallback_logic:
            return fallback_logic(state)

        # Default: END
        return END

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_progress_report(self) -> dict[str, Any]:
        """
        Get workflow progress report.

        Returns:
            Progress information
        """
        total_agents = len(self.workflow_plan)
        completed = len(self.completed_agents)

        return {
            "workflow_plan": self.workflow_plan,
            "completed_agents": self.completed_agents,
            "progress": f"{completed}/{total_agents}",
            "percent_complete": (completed / total_agents * 100) if total_agents > 0 else 0,
            "next_agent": self.workflow_plan[completed] if completed < total_agents else None
        }

    def reset(self):
        """Reset router state."""
        self.workflow_plan = []
        self.completed_agents = []
        self.agent_modes = {}
        logger.info("🔄 Router reset")


# ============================================================================
# INTEGRATION HELPER
# ============================================================================

def create_workflow_aware_decisions(router: WorkflowAwareRouter):
    """
    Create decision functions that use the workflow-aware router.

    This returns drop-in replacements for the existing decision functions
    that respect the AI-generated workflow plan.

    Args:
        router: WorkflowAwareRouter instance

    Returns:
        Dict of decision functions
    """

    def research_decide(state: dict[str, Any]) -> str:
        """Research decision with workflow awareness."""
        router.mark_completed("research")

        # Original logic (simplified)
        result = state.get("research_results", {})
        if isinstance(result, dict) and result.get("findings"):
            fallback = lambda s: "architect"
        else:
            fallback = lambda s: "hitl"

        return router.research_decide_next(state, fallback)

    def architect_decide(state: dict[str, Any]) -> str:
        """Architect decision with workflow awareness."""
        router.mark_completed("architect")

        # Original logic
        result = state.get("architecture_design")
        if result:
            fallback = lambda s: "codesmith"
        else:
            fallback = lambda s: "hitl"

        return router.architect_decide_next(state, fallback)

    def codesmith_decide(state: dict[str, Any]) -> str:
        """Codesmith decision with workflow awareness."""
        router.mark_completed("codesmith")

        # Original logic
        generated_files = state.get("generated_files", [])
        errors = state.get("errors", [])

        if errors and len(errors) >= 3:
            fallback = lambda s: "hitl"
        elif generated_files:
            fallback = lambda s: "reviewfix"
        else:
            fallback = lambda s: "reviewfix"

        return router.codesmith_decide_next(state, fallback)

    def reviewfix_decide(state: dict[str, Any]) -> str:
        """ReviewFix decision with workflow awareness."""
        router.mark_completed("reviewfix")

        # Original logic
        review_feedback = state.get("review_feedback")
        errors = state.get("errors", [])

        if errors and len(errors) >= 3:
            fallback = lambda s: "hitl"
        elif isinstance(review_feedback, dict) and review_feedback.get("issues"):
            fallback = lambda s: "codesmith"
        else:
            fallback = lambda s: END

        return router.reviewfix_decide_next(state, fallback)

    return {
        "research_decide_next": research_decide,
        "architect_decide_next": architect_decide,
        "codesmith_decide_next": codesmith_decide,
        "reviewfix_decide_next": reviewfix_decide
    }