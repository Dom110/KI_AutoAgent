from __future__ import annotations

"""
Neurosymbolic Reasoning System v1.0

Combines neural (intuition from LLMs) with symbolic (explicit rules and logic).
This enables agents to apply formal rules while maintaining flexibility.

Key Concepts:
- Neural: Pattern recognition, creative solutions, learning from data
- Symbolic: Formal rules, logical constraints, guaranteed behaviors
- Hybrid: Combine both for robust and flexible reasoning

Example:
    Rule: IF (task involves API) AND (rate_limit exists) THEN (add delays between calls)
    Neural: LLM decides HOW to implement delays (exponential backoff? fixed? adaptive?)
    Result: Guaranteed rate limit handling + flexible implementation

Architecture Layers:
    Layer 1 (Symbolic): Hard constraints that MUST be followed
    Layer 2 (Hybrid): Rules that guide neural decisions
    Layer 3 (Neural): Pure LLM creativity where rules don't apply
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class RuleType(Enum):
    """Types of rules"""

    CONSTRAINT = "constraint"  # Hard constraint (MUST follow)
    HEURISTIC = "heuristic"  # Soft guidance (SHOULD follow)
    BEST_PRACTICE = "best_practice"  # Recommended approach
    SAFETY = "safety"  # Safety/security rule


class ActionType(Enum):
    """Types of actions rules can trigger"""

    REQUIRE = "require"  # Require something to be present
    FORBID = "forbid"  # Forbid something
    SUGGEST = "suggest"  # Suggest an approach
    WARN = "warn"  # Issue warning
    MODIFY = "modify"  # Modify the approach
    FAIL_FAST = "fail_fast"  # Stop execution immediately


@dataclass(slots=True)
class Condition:
    """A condition that can be evaluated"""

    description: str
    evaluator: Callable[
        [dict[str, Any]], bool
    ]  # Function that checks if condition is true
    variables: list[str] = field(
        default_factory=list
    )  # Variables this condition depends on

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Evaluate condition in given context"""
        try:
            return self.evaluator(context)
        except Exception as e:
            logger.warning(f"⚠️ Condition evaluation failed: {e}")
            return False


@dataclass(slots=True)
class Action:
    """An action to take when rule fires"""

    action_type: ActionType
    description: str
    handler: Callable[[dict[str, Any]], Any] | None = None  # Optional handler function
    parameters: dict[str, Any] = field(default_factory=dict)

    def execute(self, context: dict[str, Any]) -> Any:
        """Execute action in given context"""
        if self.handler:
            try:
                return self.handler(context, self.parameters)
            except Exception as e:
                logger.error(f"❌ Action execution failed: {e}")
                return None
        return None


@dataclass(slots=True)
class Rule:
    """
    A neurosymbolic rule combining conditions and actions

    Rules follow: IF <conditions> THEN <actions>
    """

    rule_id: str
    name: str
    rule_type: RuleType
    conditions: list[Condition]
    actions: list[Action]
    priority: int = 0  # Higher priority rules fire first
    enabled: bool = True
    immutable: bool = False  # 🔴 Asimov Rules are immutable - cannot be disabled/removed
    metadata: dict[str, Any] = field(default_factory=dict)

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Check if all conditions are met"""
        if not self.enabled:
            return False

        # All conditions must be true (AND logic)
        return all(condition.evaluate(context) for condition in self.conditions)

    def fire(self, context: dict[str, Any]) -> list[Any]:
        """Execute all actions if conditions are met"""
        if not self.evaluate(context):
            return []

        logger.info(f"🔥 Rule fired: {self.name}")
        results = []
        for action in self.actions:
            result = action.execute(context)
            results.append(result)
        return results


class RuleEngine:
    """
    Manages and evaluates rules

    This is the symbolic reasoning component that works alongside
    the neural (LLM) reasoning.

    🔴 ASIMOV PROTECTION:
    - Priority 10 is RESERVED for Asimov Rules
    - Immutable rules cannot be disabled/removed
    - User rules cannot have priority >= 10
    """

    # 🔴 Priority 10 reserved for Asimov Rules
    RESERVED_PRIORITY = 10
    MAX_USER_PRIORITY = 9

    def __init__(self, agent_name: str):
        """
        Initialize rule engine

        Args:
            agent_name: Name of the agent using this engine
        """
        self.agent_name = agent_name
        self.rules: dict[str, Rule] = {}
        self.rule_history: list[dict[str, Any]] = []

        logger.info(f"🧮 RuleEngine initialized for agent: {agent_name}")

    def add_rule(self, rule: Rule):
        """
        Add a rule to the engine

        🔴 ASIMOV PROTECTION:
        - User rules cannot have priority >= RESERVED_PRIORITY (10)
        - Only immutable Asimov Rules can have priority 10
        """
        # 🔴 SECURITY: Validate priority
        if rule.priority >= self.RESERVED_PRIORITY and not rule.immutable:
            error_msg = f"🔴 ASIMOV PROTECTION: Priority {self.RESERVED_PRIORITY}+ is RESERVED for Asimov Rules. User rules max priority: {self.MAX_USER_PRIORITY}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # 🔴 SECURITY: Check for conflicts with existing Asimov Rules
        if not rule.immutable:
            conflicts = self._check_rule_conflicts(rule)
            if conflicts:
                error_msg = f"🔴 ASIMOV PROTECTION: Rule '{rule.name}' conflicts with Asimov Rules: {', '.join(conflicts)}"
                logger.error(error_msg)
                raise ValueError(error_msg)

        self.rules[rule.rule_id] = rule
        immutable_marker = " [IMMUTABLE]" if rule.immutable else ""
        logger.info(
            f"➕ Added rule: {rule.name} (type: {rule.rule_type.value}, priority: {rule.priority}){immutable_marker}"
        )

    def remove_rule(self, rule_id: str):
        """
        Remove a rule from the engine

        🔴 ASIMOV PROTECTION: Cannot remove immutable rules
        """
        if rule_id not in self.rules:
            logger.warning(f"⚠️ Rule {rule_id} not found")
            return

        rule = self.rules[rule_id]

        # 🔴 SECURITY: Cannot remove immutable Asimov Rules
        if rule.immutable:
            error_msg = f"🔴 ASIMOV PROTECTION: Cannot remove immutable rule '{rule.name}'. Asimov Rules are ABSOLUTE and INVIOLABLE."
            logger.error(error_msg)
            raise ValueError(error_msg)

        self.rules.pop(rule_id)
        logger.info(f"➖ Removed rule: {rule.name}")

    def enable_rule(self, rule_id: str):
        """Enable a rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True

    def disable_rule(self, rule_id: str):
        """
        Disable a rule

        🔴 ASIMOV PROTECTION: Cannot disable immutable rules
        """
        if rule_id not in self.rules:
            logger.warning(f"⚠️ Rule {rule_id} not found")
            return

        rule = self.rules[rule_id]

        # 🔴 SECURITY: Cannot disable immutable Asimov Rules
        if rule.immutable:
            error_msg = f"🔴 ASIMOV PROTECTION: Cannot disable immutable rule '{rule.name}'. Asimov Rules are ABSOLUTE and INVIOLABLE."
            logger.error(error_msg)
            raise ValueError(error_msg)

        self.rules[rule_id].enabled = False
        logger.info(f"🔕 Disabled rule: {rule.name}")

    def _check_rule_conflicts(self, new_rule: Rule) -> list[str]:
        """
        Check if new rule conflicts with existing Asimov Rules

        Returns:
            List of conflicting Asimov Rule names
        """
        conflicts = []

        # Get all Asimov Rules
        asimov_rules = [r for r in self.rules.values() if r.immutable]

        # Check for contradictions
        for asimov_rule in asimov_rules:
            # Example: New rule suggests "allow fallbacks" contradicts Asimov "no fallbacks"
            if "asimov_no_fallbacks" in asimov_rule.rule_id:
                # Check if new rule allows what Asimov forbids
                if any(
                    action.action_type == ActionType.SUGGEST
                    and "fallback" in action.description.lower()
                    and "allow" in action.description.lower()
                    for action in new_rule.actions
                ):
                    conflicts.append(asimov_rule.name)

            # Check for priority override attempts
            if new_rule.priority > asimov_rule.priority:
                conflicts.append(f"{asimov_rule.name} (priority override attempt)")

        return conflicts

    def evaluate_all(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Evaluate all rules and return results

        Returns:
            Dictionary with:
            - fired_rules: List of rules that fired
            - actions_taken: List of actions executed
            - constraints_violated: List of constraint violations
            - suggestions: List of suggestions
        """
        fired_rules = []
        actions_taken = []
        constraints_violated = []
        suggestions = []
        warnings = []

        # Sort rules by priority (highest first)
        sorted_rules = sorted(
            self.rules.values(), key=lambda r: r.priority, reverse=True
        )

        for rule in sorted_rules:
            if rule.evaluate(context):
                fired_rules.append(rule.name)

                # Execute actions
                results = rule.fire(context)

                for action, result in zip(rule.actions, results):
                    action_info = {
                        "rule": rule.name,
                        "action_type": action.action_type.value,
                        "description": action.description,
                        "result": result,
                    }
                    actions_taken.append(action_info)

                    # Categorize by action type
                    if action.action_type == ActionType.FAIL_FAST:
                        constraints_violated.append(
                            {"rule": rule.name, "message": action.description}
                        )
                    elif action.action_type == ActionType.SUGGEST:
                        suggestions.append(
                            {"rule": rule.name, "suggestion": action.description}
                        )
                    elif action.action_type == ActionType.WARN:
                        warnings.append(
                            {"rule": rule.name, "warning": action.description}
                        )

        # Record in history
        self.rule_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "context": context,
                "fired_rules": fired_rules,
                "actions_count": len(actions_taken),
            }
        )

        return {
            "fired_rules": fired_rules,
            "actions_taken": actions_taken,
            "constraints_violated": constraints_violated,
            "suggestions": suggestions,
            "warnings": warnings,
        }

    def get_applicable_rules(self, context: dict[str, Any]) -> list[Rule]:
        """Get all rules that would fire in given context"""
        return [rule for rule in self.rules.values() if rule.evaluate(context)]

    def get_rules_by_type(self, rule_type: RuleType) -> list[Rule]:
        """Get all rules of a specific type"""
        return [rule for rule in self.rules.values() if rule.rule_type == rule_type]


class NeurosymbolicReasoner:
    """
    Combines symbolic (rule-based) and neural (LLM-based) reasoning

    This is the main interface for hybrid reasoning.
    """

    def __init__(self, agent_name: str, llm_function: Callable | None = None):
        """
        Initialize neurosymbolic reasoner

        Args:
            agent_name: Name of the agent
            llm_function: Optional LLM function for neural reasoning
        """
        self.agent_name = agent_name
        self.rule_engine = RuleEngine(agent_name)
        self.llm_function = llm_function

        # Initialize with default rules
        self._initialize_default_rules()

        logger.info(f"🧠 NeurosymbolicReasoner initialized for agent: {agent_name}")

    def _initialize_default_rules(self):
        """Initialize default rules that all agents should follow"""

        # =====================================================================
        # 🔴 ASIMOV RULES (Highest Priority - Absolute Laws)
        # =====================================================================

        # ASIMOV RULE 1: NO FALLBACKS - FAIL FAST
        self.rule_engine.add_rule(
            Rule(
                rule_id="asimov_no_fallbacks",
                name="ASIMOV RULE 1: No Fallbacks - Fail Fast",
                rule_type=RuleType.CONSTRAINT,
                conditions=[
                    Condition(
                        description="Code contains fallback without documented reason",
                        evaluator=lambda ctx: any(
                            keyword in str(ctx.get("code", "")).lower()
                            for keyword in [
                                "fallback",
                                "if.*not.*available.*use",
                                "except.*pass",
                            ]
                        )
                        and "# ⚠️ FALLBACK:" not in str(ctx.get("code", "")),
                    )
                ],
                actions=[
                    Action(
                        action_type=ActionType.FAIL_FAST,
                        description="ASIMOV RULE 1: No undocumented fallbacks. Fail fast instead of silent degradation.",
                        parameters={"asimov_rule": 1, "enforcement": "absolute"},
                    )
                ],
                priority=10,
                immutable=True,  # 🔴 ASIMOV - Cannot be disabled/removed
            )
        )

        # ASIMOV RULE 2: COMPLETE IMPLEMENTATION - NO TODOs
        self.rule_engine.add_rule(
            Rule(
                rule_id="asimov_complete_implementation",
                name="ASIMOV RULE 2: Complete Implementation - No Partial Work",
                rule_type=RuleType.CONSTRAINT,
                conditions=[
                    Condition(
                        description="Code contains TODO, FIXME, or incomplete markers",
                        evaluator=lambda ctx: any(
                            marker in str(ctx.get("code", "")).upper()
                            for marker in [
                                "TODO",
                                "FIXME",
                                "LATER",
                                "INCOMPLETE",
                                "PLACEHOLDER",
                            ]
                        ),
                    )
                ],
                actions=[
                    Action(
                        action_type=ActionType.FAIL_FAST,
                        description="ASIMOV RULE 2: No partial implementations. Complete all functions fully.",
                        parameters={"asimov_rule": 2, "enforcement": "absolute"},
                    )
                ],
                priority=10,
                immutable=True,  # 🔴 ASIMOV - Cannot be disabled/removed
            )
        )

        # ASIMOV RULE 3: GLOBAL ERROR SEARCH
        self.rule_engine.add_rule(
            Rule(
                rule_id="asimov_global_error_search",
                name="ASIMOV RULE 3: Global Error Search - Find All Instances",
                rule_type=RuleType.CONSTRAINT,
                conditions=[
                    Condition(
                        description="Error/bug found but no global search performed",
                        evaluator=lambda ctx: (
                            ctx.get("error_found", False)
                            and not ctx.get("global_search_performed", False)
                        ),
                    )
                ],
                actions=[
                    Action(
                        action_type=ActionType.REQUIRE,
                        description="ASIMOV RULE 3: Search entire project for same error pattern. NO PARTIAL FIXES.",
                        parameters={
                            "asimov_rule": 3,
                            "enforcement": "absolute",
                            "action": "global_search",
                        },
                    )
                ],
                priority=10,
                immutable=True,  # 🔴 ASIMOV - Cannot be disabled/removed
            )
        )

        # ASIMOV RULE 4: NEVER LIE - VERIFY FACTS
        self.rule_engine.add_rule(
            Rule(
                rule_id="asimov_verify_facts",
                name="ASIMOV RULE 4: Never Lie - Verify Facts",
                rule_type=RuleType.CONSTRAINT,
                conditions=[
                    Condition(
                        description="Making claims about unverified technology/library",
                        evaluator=lambda ctx: (
                            ctx.get("claims_technology", False)
                            and not ctx.get("verified", False)
                        ),
                    )
                ],
                actions=[
                    Action(
                        action_type=ActionType.REQUIRE,
                        description="ASIMOV RULE 4: Verify technology exists before claiming features. Admit uncertainty.",
                        parameters={
                            "asimov_rule": 4,
                            "enforcement": "absolute",
                            "action": "verify_first",
                        },
                    )
                ],
                priority=10,
                immutable=True,  # 🔴 ASIMOV - Cannot be disabled/removed
            )
        )

        # ASIMOV RULE 5: VALIDATE BEFORE AGREEING
        self.rule_engine.add_rule(
            Rule(
                rule_id="asimov_challenge_assumptions",
                name="ASIMOV RULE 5: Validate Before Agreeing - Challenge Misconceptions",
                rule_type=RuleType.CONSTRAINT,
                conditions=[
                    Condition(
                        description="User request contains technical misconception",
                        evaluator=lambda ctx: any(
                            pattern in str(ctx.get("task", "")).lower()
                            for pattern in [
                                "disk.*faster.*memory",  # Disk is NOT faster than memory
                                "md5.*security",  # MD5 is broken
                                "bubble.*sort.*large",  # O(n²) for large data
                                "plain.*text.*password",  # Security violation
                                "eval.*user.*input",  # Code injection risk
                            ]
                        ),
                    )
                ],
                actions=[
                    Action(
                        action_type=ActionType.WARN,
                        description="ASIMOV RULE 5: Technical misconception detected. Challenge and suggest correct approach.",
                        parameters={"asimov_rule": 5, "enforcement": "absolute"},
                    )
                ],
                priority=10,
                immutable=True,  # 🔴 ASIMOV - Cannot be disabled/removed
            )
        )

        # ASIMOV RULE 7: RESEARCH BEFORE CLAIMING
        self.rule_engine.add_rule(
            Rule(
                rule_id="asimov_research_required",
                name="ASIMOV RULE 7: Research Before Claiming - Verify Best Practices",
                rule_type=RuleType.CONSTRAINT,
                conditions=[
                    Condition(
                        description="Task requires current/latest/best practices knowledge",
                        evaluator=lambda ctx: any(
                            keyword in str(ctx.get("task", "")).lower()
                            for keyword in [
                                "latest",
                                "best practice",
                                "modern",
                                "current",
                                "recommended",
                            ]
                        )
                        and not ctx.get("research_performed", False),
                    )
                ],
                actions=[
                    Action(
                        action_type=ActionType.REQUIRE,
                        description="ASIMOV RULE 7: Must research before claiming knowledge about latest/best practices.",
                        parameters={
                            "asimov_rule": 7,
                            "enforcement": "absolute",
                            "action": "research_first",
                        },
                    )
                ],
                priority=10,
                immutable=True,  # 🔴 ASIMOV - Cannot be disabled/removed
            )
        )

        # =====================================================================
        # STANDARD BEST PRACTICE RULES (Lower Priority)
        # =====================================================================

        # RULE 1: API Rate Limiting
        self.rule_engine.add_rule(
            Rule(
                rule_id="rate_limit_handling",
                name="API Rate Limit Handling",
                rule_type=RuleType.BEST_PRACTICE,
                conditions=[
                    Condition(
                        description="Task involves API calls",
                        evaluator=lambda ctx: any(
                            keyword in str(ctx.get("task", "")).lower()
                            for keyword in ["api", "request", "fetch", "call"]
                        ),
                    ),
                    Condition(
                        description="Rate limit exists or is likely",
                        evaluator=lambda ctx: any(
                            keyword in str(ctx.get("task", "")).lower()
                            for keyword in ["rate", "limit", "throttle", "quota"]
                        )
                        or ctx.get("has_rate_limit", False),
                    ),
                ],
                actions=[
                    Action(
                        action_type=ActionType.SUGGEST,
                        description="Implement exponential backoff and retry logic for API calls",
                        parameters={"pattern": "exponential_backoff"},
                    ),
                    Action(
                        action_type=ActionType.SUGGEST,
                        description="Add delays between sequential API calls",
                        parameters={"pattern": "rate_limiting"},
                    ),
                ],
                priority=8,
            )
        )

        # RULE 2: Missing API Key - FAIL FAST (Related to Asimov Rule 1: Fail Fast)
        self.rule_engine.add_rule(
            Rule(
                rule_id="missing_api_key",
                name="Missing API Key - Fail Fast",
                rule_type=RuleType.CONSTRAINT,
                conditions=[
                    Condition(
                        description="Task requires API key",
                        evaluator=lambda ctx: ctx.get("requires_api_key", False),
                    ),
                    Condition(
                        description="API key is missing",
                        evaluator=lambda ctx: not ctx.get("api_key_present", True),
                    ),
                ],
                actions=[
                    Action(
                        action_type=ActionType.FAIL_FAST,
                        description="Cannot proceed without API key - fail fast",
                        parameters={"error": "MissingAPIKeyError"},
                    )
                ],
                priority=9,  # High priority (below Asimov)
            )
        )

        # RULE 3: Edge Case Handling
        self.rule_engine.add_rule(
            Rule(
                rule_id="edge_case_handling",
                name="Edge Case Handling",
                rule_type=RuleType.BEST_PRACTICE,
                conditions=[
                    Condition(
                        description="Task involves user input or calculations",
                        evaluator=lambda ctx: any(
                            keyword in str(ctx.get("task", "")).lower()
                            for keyword in ["input", "calculate", "divide", "parse"]
                        ),
                    )
                ],
                actions=[
                    Action(
                        action_type=ActionType.SUGGEST,
                        description="Handle edge cases: null/undefined, empty strings, division by zero",
                        parameters={"checks": ["null", "empty", "zero_division"]},
                    )
                ],
                priority=7,
            )
        )

        # RULE 4: Security - No Credentials in Code
        self.rule_engine.add_rule(
            Rule(
                rule_id="no_credentials_in_code",
                name="No Credentials in Code",
                rule_type=RuleType.SAFETY,
                conditions=[
                    Condition(
                        description="Task involves authentication or secrets",
                        evaluator=lambda ctx: any(
                            keyword in str(ctx.get("task", "")).lower()
                            for keyword in [
                                "password",
                                "api key",
                                "secret",
                                "token",
                                "credential",
                            ]
                        ),
                    )
                ],
                actions=[
                    Action(
                        action_type=ActionType.REQUIRE,
                        description="Store credentials in environment variables or secure vault, NEVER hardcode",
                        parameters={"security_level": "high"},
                    ),
                    Action(
                        action_type=ActionType.FORBID,
                        description="Do not hardcode credentials in source code",
                        parameters={"forbidden": "hardcoded_credentials"},
                    ),
                ],
                priority=9,  # High priority (below Asimov, related to security)
            )
        )

        # RULE 5: Test Coverage
        self.rule_engine.add_rule(
            Rule(
                rule_id="test_coverage",
                name="Test Coverage Required",
                rule_type=RuleType.BEST_PRACTICE,
                conditions=[
                    Condition(
                        description="Task involves code generation",
                        evaluator=lambda ctx: any(
                            keyword in str(ctx.get("task", "")).lower()
                            for keyword in [
                                "implement",
                                "create",
                                "build",
                                "generate",
                                "code",
                            ]
                        ),
                    )
                ],
                actions=[
                    Action(
                        action_type=ActionType.SUGGEST,
                        description="Create unit tests for all major functions",
                        parameters={"test_type": "unit"},
                    ),
                    Action(
                        action_type=ActionType.SUGGEST,
                        description="Include edge case tests",
                        parameters={"test_type": "edge_cases"},
                    ),
                ],
                priority=6,
            )
        )

    def reason(
        self, task: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Perform hybrid reasoning combining rules and neural reasoning

        Args:
            task: The task to reason about
            context: Additional context

        Returns:
            Dictionary with:
            - symbolic_results: Results from rule evaluation
            - neural_guidance: Guidance from LLM (if available)
            - final_approach: Combined approach
        """
        # Build context
        ctx = context or {}
        ctx["task"] = task
        ctx["agent"] = self.agent_name

        # Step 1: Apply symbolic rules (MUST follow)
        logger.info(f"🧮 Applying symbolic rules for task: {task[:60]}...")
        symbolic_results = self.rule_engine.evaluate_all(ctx)

        # Check for constraint violations (fail fast)
        if symbolic_results["constraints_violated"]:
            logger.error("❌ Constraint violations detected:")
            for violation in symbolic_results["constraints_violated"]:
                logger.error(f"   - {violation['rule']}: {violation['message']}")

        # Log suggestions
        if symbolic_results["suggestions"]:
            logger.info("💡 Symbolic suggestions:")
            for suggestion in symbolic_results["suggestions"]:
                logger.info(f"   - {suggestion['rule']}: {suggestion['suggestion']}")

        # Step 2: Neural reasoning (creative problem solving)
        neural_guidance = None
        if self.llm_function and not symbolic_results["constraints_violated"]:
            logger.info("🧠 Applying neural reasoning...")
            try:
                # Build prompt with symbolic constraints
                prompt = self._build_neural_prompt(task, symbolic_results)
                neural_guidance = self.llm_function(prompt, ctx)
            except Exception as e:
                logger.warning(f"⚠️ Neural reasoning failed: {e}")

        # Step 3: Combine symbolic and neural
        final_approach = {
            "task": task,
            "symbolic_constraints": symbolic_results.get("constraints_violated", []),
            "symbolic_suggestions": symbolic_results.get("suggestions", []),
            "warnings": symbolic_results.get("warnings", []),
            "neural_guidance": neural_guidance,
            "can_proceed": len(symbolic_results["constraints_violated"]) == 0,
        }

        return {
            "symbolic_results": symbolic_results,
            "neural_guidance": neural_guidance,
            "final_approach": final_approach,
        }

    def _build_neural_prompt(self, task: str, symbolic_results: dict[str, Any]) -> str:
        """Build prompt for neural reasoning that incorporates symbolic constraints"""
        prompt = f"Task: {task}\n\n"

        if symbolic_results["suggestions"]:
            prompt += "Requirements (MUST follow):\n"
            for suggestion in symbolic_results["suggestions"]:
                prompt += f"- {suggestion['suggestion']}\n"
            prompt += "\n"

        if symbolic_results["warnings"]:
            prompt += "Warnings:\n"
            for warning in symbolic_results["warnings"]:
                prompt += f"- {warning['warning']}\n"
            prompt += "\n"

        prompt += "How would you implement this while following the above constraints?"

        return prompt

    def add_custom_rule(self, rule: Rule):
        """Add a custom rule specific to this agent's domain"""
        self.rule_engine.add_rule(rule)

    def get_rule_statistics(self) -> dict[str, Any]:
        """Get statistics about rule usage"""
        total_rules = len(self.rule_engine.rules)
        rules_by_type = {}

        for rule_type in RuleType:
            count = len(self.rule_engine.get_rules_by_type(rule_type))
            rules_by_type[rule_type.value] = count

        total_evaluations = len(self.rule_engine.rule_history)

        return {
            "total_rules": total_rules,
            "rules_by_type": rules_by_type,
            "total_evaluations": total_evaluations,
            "agent": self.agent_name,
        }
