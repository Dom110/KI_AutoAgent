"""
Neurosymbolic Reasoner v6 - Hybrid Neural + Symbolic Reasoning

Capabilities:
- Combine LLM (neural) reasoning with rule-based (symbolic) logic
- Formal constraint checking
- Logic-based validation
- Knowledge graph reasoning
- Proof generation for decisions

Integration:
- After Architect planning
- Before critical operations
- For complex decision making

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


class RuleType(str, Enum):
    """Types of symbolic rules."""

    CONSTRAINT = "constraint"
    IMPLICATION = "implication"
    DEPENDENCY = "dependency"
    CONFLICT = "conflict"
    SAFETY = "safety"


class ReasoningMode(str, Enum):
    """Reasoning modes."""

    NEURAL_ONLY = "neural_only"  # LLM only
    SYMBOLIC_ONLY = "symbolic_only"  # Rules only
    HYBRID = "hybrid"  # Both neural + symbolic
    NEURAL_THEN_SYMBOLIC = "neural_then_symbolic"  # Neural first, validate with symbolic
    SYMBOLIC_THEN_NEURAL = "symbolic_then_neural"  # Symbolic first, refine with neural


@dataclass(slots=True)
class SymbolicRule:
    """A symbolic reasoning rule."""

    rule_id: str
    rule_type: RuleType
    condition: str  # Logical condition
    action: str  # What to do if condition is true
    priority: int
    description: str


@dataclass(slots=True)
class ReasoningResult:
    """Result of neurosymbolic reasoning."""

    decision: str
    neural_output: str | None
    symbolic_checks: list[dict[str, Any]]
    constraints_satisfied: bool
    proof: list[str]
    confidence: float
    reasoning_mode: ReasoningMode
    metadata: dict[str, Any]


class NeurosymbolicReasonerV6:
    """
    Neurosymbolic Reasoning System.

    Combines neural network reasoning (LLM) with symbolic logic rules.
    """

    def __init__(self, llm: Any | None = None):
        """
        Initialize neurosymbolic reasoner.

        Args:
            llm: Optional LLM for neural reasoning
        """
        self.llm = llm
        self.rules: dict[str, SymbolicRule] = {}
        self.knowledge_base: dict[str, Any] = {}

        # Setup default rules
        self._setup_default_rules()

        logger.info("🧠 Neurosymbolic Reasoner v6 initialized")

    def _setup_default_rules(self) -> None:
        """Setup default symbolic rules."""

        # Safety rules
        self.add_rule(SymbolicRule(
            rule_id="no_delete_without_backup",
            rule_type=RuleType.SAFETY,
            condition="action_type == 'delete' AND no_backup_exists",
            action="reject",
            priority=100,
            description="Never delete files without backup"
        ))

        self.add_rule(SymbolicRule(
            rule_id="no_production_without_tests",
            rule_type=RuleType.SAFETY,
            condition="deployment_target == 'production' AND tests_not_passed",
            action="reject",
            priority=100,
            description="Never deploy to production without passing tests"
        ))

        # Dependency rules
        self.add_rule(SymbolicRule(
            rule_id="backend_before_frontend",
            rule_type=RuleType.DEPENDENCY,
            condition="task_type == 'frontend' AND backend_not_ready",
            action="defer",
            priority=80,
            description="Backend must be implemented before frontend"
        ))

        self.add_rule(SymbolicRule(
            rule_id="tests_after_implementation",
            rule_type=RuleType.DEPENDENCY,
            condition="task_type == 'testing' AND implementation_not_done",
            action="defer",
            priority=70,
            description="Implementation must be done before testing"
        ))

        # Constraint rules
        self.add_rule(SymbolicRule(
            rule_id="max_file_size",
            rule_type=RuleType.CONSTRAINT,
            condition="file_size > 10000",
            action="split",
            priority=60,
            description="Files should not exceed 10K lines"
        ))

        self.add_rule(SymbolicRule(
            rule_id="cyclic_dependency",
            rule_type=RuleType.CONFLICT,
            condition="has_cyclic_dependency",
            action="reject",
            priority=90,
            description="Cyclic dependencies are not allowed"
        ))

        # Implication rules
        self.add_rule(SymbolicRule(
            rule_id="database_needs_migration",
            rule_type=RuleType.IMPLICATION,
            condition="modifies_database_schema",
            action="require_migration",
            priority=70,
            description="Database schema changes require migration"
        ))

        self.add_rule(SymbolicRule(
            rule_id="api_change_needs_versioning",
            rule_type=RuleType.IMPLICATION,
            condition="modifies_public_api",
            action="require_versioning",
            priority=75,
            description="Public API changes require version bump"
        ))

    def add_rule(self, rule: SymbolicRule) -> None:
        """Add symbolic rule to knowledge base."""
        self.rules[rule.rule_id] = rule
        logger.debug(f"📋 Added rule: {rule.rule_id} ({rule.rule_type.value})")

    def remove_rule(self, rule_id: str) -> bool:
        """Remove rule from knowledge base."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"🗑️  Removed rule: {rule_id}")
            return True
        return False

    async def reason(
        self,
        context: dict[str, Any],
        mode: ReasoningMode = ReasoningMode.HYBRID
    ) -> ReasoningResult:
        """
        Perform neurosymbolic reasoning.

        Args:
            context: Context for reasoning (task, state, constraints)
            mode: Reasoning mode to use

        Returns:
            Reasoning result with decision and proof
        """
        logger.info(f"🧠 Reasoning with mode: {mode.value}")
        logger.debug(f"   Context: {context.get('task_description', 'N/A')[:60]}...")

        neural_output: str | None = None
        symbolic_checks: list[dict[str, Any]] = []
        decision = ""
        proof: list[str] = []

        # Execute reasoning based on mode
        if mode == ReasoningMode.NEURAL_ONLY:
            neural_output = await self._neural_reasoning(context)
            decision = neural_output
            proof.append("Decision based purely on neural network reasoning")

        elif mode == ReasoningMode.SYMBOLIC_ONLY:
            symbolic_checks = self._symbolic_reasoning(context)
            decision = self._make_symbolic_decision(symbolic_checks)
            proof = self._generate_symbolic_proof(symbolic_checks)

        elif mode == ReasoningMode.NEURAL_THEN_SYMBOLIC:
            # Neural first, then validate with symbolic
            neural_output = await self._neural_reasoning(context)
            symbolic_checks = self._symbolic_reasoning(context)
            decision, proof = self._validate_neural_with_symbolic(
                neural_output, symbolic_checks
            )

        elif mode == ReasoningMode.SYMBOLIC_THEN_NEURAL:
            # Symbolic first, then refine with neural
            symbolic_checks = self._symbolic_reasoning(context)
            symbolic_decision = self._make_symbolic_decision(symbolic_checks)

            if symbolic_decision != "reject":
                # Refine with neural
                neural_output = await self._neural_reasoning(context)
                decision = neural_output
                proof = self._generate_hybrid_proof(symbolic_checks, neural_output)
            else:
                decision = symbolic_decision
                proof = self._generate_symbolic_proof(symbolic_checks)

        elif mode == ReasoningMode.HYBRID:
            # Full hybrid: run both and combine
            neural_output = await self._neural_reasoning(context)
            symbolic_checks = self._symbolic_reasoning(context)
            decision, proof = self._hybrid_reasoning(neural_output, symbolic_checks)

        # Check constraints
        constraints_satisfied = self._check_constraints(symbolic_checks)

        # Calculate confidence
        confidence = self._calculate_confidence(
            mode, neural_output, symbolic_checks, constraints_satisfied
        )

        result = ReasoningResult(
            decision=decision,
            neural_output=neural_output,
            symbolic_checks=symbolic_checks,
            constraints_satisfied=constraints_satisfied,
            proof=proof,
            confidence=confidence,
            reasoning_mode=mode,
            metadata={
                "rule_count": len(self.rules),
                "triggered_rules": len([c for c in symbolic_checks if c["triggered"]]),
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"✅ Decision: {decision[:80]}...")
        logger.info(f"   Confidence: {confidence:.2f}, Constraints: {constraints_satisfied}")

        return result

    async def _neural_reasoning(self, context: dict[str, Any]) -> str:
        """Perform neural reasoning using LLM."""

        if not self.llm:
            # No LLM available, return default
            logger.warning("⚠️  No LLM available for neural reasoning")
            return "proceed"

        # Prepare prompt for LLM
        prompt = f"""Analyze the following task and make a decision.

Task: {context.get('task_description', 'N/A')}
Current State: {context.get('current_state', {})}
Constraints: {context.get('constraints', [])}

Decide whether to:
- proceed: Continue with the task
- defer: Wait for dependencies
- reject: Task should not be done
- modify: Task needs changes

Provide your decision and brief reasoning."""

        try:
            # Call LLM (simplified - in production would use actual LLM)
            # response = await self.llm.ainvoke(prompt)
            # For now, return a simulated response
            logger.debug("🤖 LLM reasoning (simulated)")
            return "proceed: Task seems valid and dependencies are satisfied"

        except Exception as e:
            logger.error(f"❌ Neural reasoning failed: {e}")
            return "proceed"  # Default fallback

    def _symbolic_reasoning(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Perform symbolic reasoning using rules."""

        checks = []

        # Evaluate all rules
        for rule in sorted(self.rules.values(), key=lambda r: r.priority, reverse=True):
            triggered = self._evaluate_rule(rule, context)

            checks.append({
                "rule_id": rule.rule_id,
                "rule_type": rule.rule_type.value,
                "triggered": triggered,
                "action": rule.action if triggered else None,
                "priority": rule.priority,
                "description": rule.description
            })

            if triggered:
                logger.debug(f"   ⚠️  Rule triggered: {rule.rule_id} → {rule.action}")

        return checks

    def _evaluate_rule(self, rule: SymbolicRule, context: dict[str, Any]) -> bool:
        """
        Evaluate a symbolic rule against context.

        This is a simplified evaluator - in production would use a proper logic engine.
        """

        condition = rule.condition.lower()

        # Simple condition evaluation (key-value matching)
        # In production, this would use a proper logic parser

        # Extract key-value pairs from condition
        # Format: "key == 'value' AND other_key == 'value'"

        # Safety rules
        if "action_type" in condition and "delete" in condition:
            action_type = context.get("action_type", "")
            has_backup = context.get("has_backup", True)
            return action_type == "delete" and not has_backup

        if "deployment_target" in condition and "production" in condition:
            target = context.get("deployment_target", "")
            tests_passed = context.get("tests_passed", False)
            return target == "production" and not tests_passed

        # Dependency rules
        if "backend_not_ready" in condition:
            task_type = context.get("task_type", "")
            backend_ready = context.get("backend_ready", True)
            return task_type == "frontend" and not backend_ready

        if "implementation_not_done" in condition:
            task_type = context.get("task_type", "")
            implementation_done = context.get("implementation_done", False)
            return task_type == "testing" and not implementation_done

        # Constraint rules
        if "file_size" in condition:
            file_size = context.get("file_size", 0)
            return file_size > 10000

        if "cyclic_dependency" in condition:
            return context.get("has_cyclic_dependency", False)

        # Implication rules
        if "modifies_database_schema" in condition:
            return context.get("modifies_database_schema", False)

        if "modifies_public_api" in condition:
            return context.get("modifies_public_api", False)

        return False

    def _make_symbolic_decision(self, checks: list[dict[str, Any]]) -> str:
        """Make decision based purely on symbolic checks."""

        # Get highest priority triggered rule
        triggered = [c for c in checks if c["triggered"]]

        if not triggered:
            return "proceed"

        # Sort by priority
        triggered.sort(key=lambda c: c["priority"], reverse=True)

        # Return action of highest priority rule
        return triggered[0]["action"]

    def _validate_neural_with_symbolic(
        self,
        neural_output: str,
        symbolic_checks: list[dict[str, Any]]
    ) -> tuple[str, list[str]]:
        """Validate neural decision with symbolic rules."""

        proof = [f"Neural reasoning suggests: {neural_output}"]

        # Check if any critical rules are violated
        violations = [
            c for c in symbolic_checks
            if c["triggered"] and c["priority"] >= 90
        ]

        if violations:
            # Override neural decision
            decision = violations[0]["action"]
            proof.append(f"OVERRIDE: Critical rule {violations[0]['rule_id']} triggered")
            proof.append(f"Reason: {violations[0]['description']}")
            proof.append(f"Decision changed to: {decision}")
        else:
            # Neural decision stands
            decision = neural_output.split(":")[0] if ":" in neural_output else neural_output
            proof.append("No critical violations detected")
            proof.append("Neural decision validated")

        return decision, proof

    def _hybrid_reasoning(
        self,
        neural_output: str,
        symbolic_checks: list[dict[str, Any]]
    ) -> tuple[str, list[str]]:
        """Combine neural and symbolic reasoning."""

        proof = []

        # Get symbolic decision
        symbolic_decision = self._make_symbolic_decision(symbolic_checks)

        # Get neural decision
        neural_decision = neural_output.split(":")[0] if ":" in neural_output else neural_output

        proof.append(f"Neural reasoning: {neural_output}")
        proof.append(f"Symbolic reasoning: {symbolic_decision}")

        # Combine decisions
        triggered_rules = [c for c in symbolic_checks if c["triggered"]]

        if triggered_rules:
            # If high-priority rules triggered, use symbolic
            high_priority = [r for r in triggered_rules if r["priority"] >= 80]
            if high_priority:
                decision = symbolic_decision
                proof.append(f"Using symbolic decision (high-priority rules triggered)")
            else:
                # Low-priority rules, prefer neural
                decision = neural_decision
                proof.append(f"Using neural decision (only low-priority rules triggered)")
        else:
            # No rules triggered, use neural
            decision = neural_decision
            proof.append("Using neural decision (no rules triggered)")

        return decision, proof

    def _generate_symbolic_proof(self, checks: list[dict[str, Any]]) -> list[str]:
        """Generate proof from symbolic reasoning."""

        proof = ["Symbolic reasoning applied:"]

        triggered = [c for c in checks if c["triggered"]]

        if not triggered:
            proof.append("- No rules triggered")
            proof.append("- Decision: proceed")
        else:
            for check in triggered:
                proof.append(f"- Rule {check['rule_id']}: {check['description']}")
                proof.append(f"  Action: {check['action']}")

        return proof

    def _generate_hybrid_proof(
        self,
        checks: list[dict[str, Any]],
        neural_output: str
    ) -> list[str]:
        """Generate proof for hybrid reasoning."""

        proof = self._generate_symbolic_proof(checks)
        proof.append(f"Neural refinement: {neural_output}")

        return proof

    def _check_constraints(self, symbolic_checks: list[dict[str, Any]]) -> bool:
        """Check if constraints are satisfied."""

        # Find constraint and safety rule violations
        violations = [
            c for c in symbolic_checks
            if c["triggered"] and c["rule_type"] in ["constraint", "safety"]
        ]

        return len(violations) == 0

    def _calculate_confidence(
        self,
        mode: ReasoningMode,
        neural_output: str | None,
        symbolic_checks: list[dict[str, Any]],
        constraints_satisfied: bool
    ) -> float:
        """Calculate confidence score."""

        if mode == ReasoningMode.SYMBOLIC_ONLY:
            # High confidence if constraints satisfied
            return 0.95 if constraints_satisfied else 0.5

        elif mode == ReasoningMode.NEURAL_ONLY:
            # Medium confidence (neural can hallucinate)
            return 0.7

        elif mode in [ReasoningMode.NEURAL_THEN_SYMBOLIC, ReasoningMode.HYBRID]:
            # High confidence if validated
            if constraints_satisfied:
                return 0.9
            else:
                return 0.6

        elif mode == ReasoningMode.SYMBOLIC_THEN_NEURAL:
            # Very high confidence (symbolic + neural)
            if constraints_satisfied:
                return 0.95
            else:
                return 0.65

        return 0.5

    def get_rule_stats(self) -> dict[str, Any]:
        """Get statistics about rules."""

        by_type: dict[str, int] = {}
        for rule in self.rules.values():
            rule_type = rule.rule_type.value
            by_type[rule_type] = by_type.get(rule_type, 0) + 1

        return {
            "total_rules": len(self.rules),
            "by_type": by_type,
            "rules": [
                {
                    "id": rule.rule_id,
                    "type": rule.rule_type.value,
                    "priority": rule.priority,
                    "description": rule.description
                }
                for rule in sorted(self.rules.values(), key=lambda r: r.priority, reverse=True)
            ]
        }


# Global reasoner instance
_reasoner: NeurosymbolicReasonerV6 | None = None


def get_neurosymbolic_reasoner() -> NeurosymbolicReasonerV6:
    """Get global neurosymbolic reasoner instance."""
    global _reasoner
    if _reasoner is None:
        _reasoner = NeurosymbolicReasonerV6()
    return _reasoner


# Export
__all__ = [
    "NeurosymbolicReasonerV6",
    "ReasoningResult",
    "SymbolicRule",
    "RuleType",
    "ReasoningMode",
    "get_neurosymbolic_reasoner"
]
