"""
Asimov Rules for KI AutoAgent v6.4-beta

These are HARD CONSTRAINTS that cannot be violated by any agent.
Similar to Asimov's Three Laws of Robotics, these rules ensure:
- Code quality and safety
- Architecture documentation
- Human oversight

The Three Laws of KI AutoAgent:

Rule 1: Code Safety
    - Any code change MUST be validated by ReviewFix
    - ReviewFix MUST debug and test (e.g. with playground)
    - No code reaches production without review

Rule 2: Architecture Documentation
    - Architect MUST scan final architecture before completion
    - ARCHITECTURE.md is required for all projects
    - System state must be documented

Rule 3: Human Involvement
    - Uncertainty (confidence < 0.5) → HITL
    - Important decisions → HITL
    - Final summary → HITL
    - Human has ultimate authority

Author: KI AutoAgent Team
Python: 3.13+
Version: 6.4.0-beta-asimov
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class AsimovRules:
    """
    Enforce Asimov Rules for workflow integrity.

    These rules OVERRIDE all agent decisions and cannot be violated.
    They ensure quality, documentation, and human oversight.

    Usage:
        asimov = AsimovRules()
        override = asimov.enforce_all_rules(state)
        if override:
            # Rule violation detected - override agent decision
            state.update(override)
            next_agent = override["next_agent"]
    """

    def __init__(self):
        """Initialize Asimov Rules enforcer."""
        self.rules_violated = []
        logger.info("⚖️  Asimov Rules initialized")

    def check_code_safety(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Rule 1: Code Safety

        If code was changed (generated or modified), ReviewFix MUST run.
        This ensures all code changes are validated before proceeding.

        Args:
            state: Current workflow state

        Returns:
            Routing override if rule violated, empty dict otherwise
        """
        files_generated = state.get("files_generated", [])
        files_modified = state.get("files_modified", [])
        executed_agents = state.get("executed_agents", [])

        # Check if code was changed
        code_changed = bool(files_generated or files_modified)

        # Check if ReviewFix already ran
        reviewfix_ran = "reviewfix" in executed_agents

        if code_changed and not reviewfix_ran:
            # RULE VIOLATION: Code changed but not reviewed
            logger.warning("⚠️  ASIMOV RULE 1 VIOLATION DETECTED!")
            logger.warning("   Code changes detected without ReviewFix validation")
            logger.warning(f"   Files generated: {len(files_generated)}")
            logger.warning(f"   Files modified: {len(files_modified)}")

            self.rules_violated.append("Rule 1: Code Safety")

            return {
                "next_agent": "reviewfix",
                "routing_confidence": 1.0,
                "routing_reason": "ASIMOV RULE 1: Code changes require ReviewFix validation",
                "asimov_rule_enforced": "Rule 1: Code Safety",
                "asimov_override": True
            }

        return {}

    def check_architecture_documentation(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Rule 2: Architecture Documentation

        Before workflow END, Architect MUST run post_build_scan to document
        final architecture state.

        Args:
            state: Current workflow state

        Returns:
            Routing override if rule violated, empty dict otherwise
        """
        next_agent = state.get("next_agent")
        can_end = state.get("can_end_workflow", False)
        architect_modes = state.get("architect_modes_executed", [])

        # Check if workflow is trying to end
        trying_to_end = (next_agent == "END" or can_end)

        # Check if post_build_scan was done
        post_scan_done = "post_build_scan" in architect_modes

        if trying_to_end and not post_scan_done:
            # RULE VIOLATION: Trying to end without architecture scan
            logger.warning("⚠️  ASIMOV RULE 2 VIOLATION DETECTED!")
            logger.warning("   Workflow attempting to end without architecture documentation")
            logger.warning(f"   Architect modes executed: {architect_modes}")

            self.rules_violated.append("Rule 2: Architecture Documentation")

            return {
                "next_agent": "architect",
                "architect_mode": "post_build_scan",
                "routing_confidence": 1.0,
                "routing_reason": "ASIMOV RULE 2: Architecture scan required before completion",
                "asimov_rule_enforced": "Rule 2: Architecture Documentation",
                "asimov_override": True
            }

        return {}

    def check_human_involvement(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Rule 3: Human Involvement

        Ensures human oversight in critical situations:
        - Low confidence decisions require HITL
        - Final summary must be shown to user
        - Important decisions need human approval

        Args:
            state: Current workflow state

        Returns:
            Routing override if rule triggered, empty dict otherwise
        """
        confidence = state.get("routing_confidence", 1.0)
        next_agent = state.get("next_agent")
        can_end = state.get("can_end_workflow", False)
        user_summary_shown = state.get("user_summary_shown", False)

        # Rule 3a: Low confidence → HITL
        if confidence < 0.5:
            logger.warning("⚠️  ASIMOV RULE 3a TRIGGERED!")
            logger.warning(f"   Low confidence detected: {confidence:.2f}")
            logger.warning("   Human input required for decision")

            return {
                "next_agent": "hitl",
                "hitl_type": "low_confidence_decision",
                "routing_confidence": 1.0,
                "routing_reason": f"ASIMOV RULE 3: Low confidence ({confidence:.2f}), human input needed",
                "asimov_rule_enforced": "Rule 3: Human Involvement (Low Confidence)",
                "asimov_override": True
            }

        # Rule 3b: Final summary → HITL
        trying_to_end = (next_agent == "END" or can_end)
        if trying_to_end and not user_summary_shown:
            logger.info("✅ ASIMOV RULE 3b TRIGGERED!")
            logger.info("   Workflow complete - final summary required")

            return {
                "next_agent": "hitl",
                "hitl_type": "final_summary",
                "routing_confidence": 1.0,
                "routing_reason": "ASIMOV RULE 3: Final summary for user approval",
                "asimov_rule_enforced": "Rule 3: Human Involvement (Final Summary)",
                "asimov_override": True
            }

        return {}

    def enforce_all_rules(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Check all Asimov Rules and enforce if needed.

        Rules are checked in priority order:
        1. Code Safety (highest priority)
        2. Architecture Documentation
        3. Human Involvement

        Args:
            state: Current workflow state

        Returns:
            Routing override if any rule is violated, empty dict if all rules satisfied
        """
        # Rule 1: Code Safety (HIGHEST PRIORITY)
        override = self.check_code_safety(state)
        if override:
            logger.warning("🚨 ASIMOV RULE 1 ENFORCED: Routing to ReviewFix")
            return override

        # Rule 2: Architecture Documentation
        override = self.check_architecture_documentation(state)
        if override:
            logger.warning("🚨 ASIMOV RULE 2 ENFORCED: Routing to Architect post_build_scan")
            return override

        # Rule 3: Human Involvement
        override = self.check_human_involvement(state)
        if override:
            logger.info("✅ ASIMOV RULE 3 ENFORCED: Routing to HITL")
            return override

        # All rules satisfied
        return {}

    def get_violations(self) -> list[str]:
        """
        Get list of rule violations detected.

        Returns:
            List of rule violation messages
        """
        return self.rules_violated

    def reset_violations(self) -> None:
        """Reset violations list."""
        self.rules_violated = []
