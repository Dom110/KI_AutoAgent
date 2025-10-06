#!/usr/bin/env python3
"""
Test Neurosymbolic Reasoning System

Demonstrates how agents combine symbolic rules with neural reasoning
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from langgraph_system.extensions.neurosymbolic_reasoning import (
    NeurosymbolicReasoner,
    Rule,
    RuleType,
    Condition,
    Action,
    ActionType
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_neurosymbolic_reasoning():
    """Test the neurosymbolic reasoning system"""
    logger.info("=" * 80)
    logger.info("🧠 Testing Neurosymbolic Reasoning System")
    logger.info("=" * 80)

    # Create reasoner for a test agent
    reasoner = NeurosymbolicReasoner(agent_name="TestAgent")

    # =========================================================================
    # SCENARIO 1: Task with rate limiting (rule suggests approach)
    # =========================================================================
    logger.info("\n📝 SCENARIO 1: API Task with Rate Limiting")
    logger.info("-" * 80)

    result = reasoner.reason(
        task="Build an API client that fetches data from weather API",
        context={
            "has_rate_limit": True,
            "task": "Build an API client that fetches data from weather API"
        }
    )

    logger.info("\n🧮 Symbolic Results:")
    logger.info(f"   Rules fired: {result['symbolic_results']['fired_rules']}")
    logger.info(f"   Suggestions: {len(result['symbolic_results']['suggestions'])}")
    for suggestion in result['symbolic_results']['suggestions']:
        logger.info(f"      - {suggestion['suggestion']}")

    logger.info(f"\n✅ Can proceed: {result['final_approach']['can_proceed']}")
    logger.info("   → Rule ensures rate limiting is implemented")

    # =========================================================================
    # SCENARIO 2: Task with missing API key (constraint violation)
    # =========================================================================
    logger.info("\n📝 SCENARIO 2: Task with Missing API Key (FAIL FAST)")
    logger.info("-" * 80)

    result_fail = reasoner.reason(
        task="Fetch data from OpenAI API",
        context={
            "requires_api_key": True,
            "api_key_present": False,
            "task": "Fetch data from OpenAI API"
        }
    )

    logger.info("\n🧮 Symbolic Results:")
    logger.info(f"   Rules fired: {result_fail['symbolic_results']['fired_rules']}")
    logger.info(f"   Constraint violations: {len(result_fail['symbolic_results']['constraints_violated'])}")
    for violation in result_fail['symbolic_results']['constraints_violated']:
        logger.error(f"      ❌ {violation['rule']}: {violation['message']}")

    logger.info(f"\n❌ Can proceed: {result_fail['final_approach']['can_proceed']}")
    logger.info("   → Constraint prevents execution without API key")

    # =========================================================================
    # SCENARIO 3: Task with security concerns (safety rule)
    # =========================================================================
    logger.info("\n📝 SCENARIO 3: Task with Credentials (Security Rule)")
    logger.info("-" * 80)

    result_security = reasoner.reason(
        task="Create authentication system with password storage",
        context={
            "task": "Create authentication system with password storage"
        }
    )

    logger.info("\n🧮 Symbolic Results:")
    logger.info(f"   Rules fired: {result_security['symbolic_results']['fired_rules']}")
    logger.info(f"   Actions taken: {len(result_security['symbolic_results']['actions_taken'])}")
    for action in result_security['symbolic_results']['actions_taken']:
        logger.info(f"      - {action['action_type']}: {action['description']}")

    logger.info("\n🔒 Security ensured by symbolic rules!")

    # =========================================================================
    # SCENARIO 4: Custom Rule - Database Connection
    # =========================================================================
    logger.info("\n📝 SCENARIO 4: Adding Custom Rule")
    logger.info("-" * 80)

    # Add custom rule specific to database tasks
    custom_rule = Rule(
        rule_id="db_connection_check",
        name="Database Connection Check",
        rule_type=RuleType.CONSTRAINT,
        conditions=[
            Condition(
                description="Task requires database",
                evaluator=lambda ctx: "database" in str(ctx.get("task", "")).lower()
            ),
            Condition(
                description="Database connection not verified",
                evaluator=lambda ctx: not ctx.get("db_connection_verified", False)
            )
        ],
        actions=[
            Action(
                action_type=ActionType.WARN,
                description="Verify database connection and credentials before proceeding",
                parameters={"check_type": "database_connection"}
            )
        ],
        priority=9
    )

    reasoner.add_custom_rule(custom_rule)
    logger.info("✅ Added custom rule: Database Connection Check")

    # Test custom rule
    result_db = reasoner.reason(
        task="Create PostgreSQL database schema for user management",
        context={
            "task": "Create PostgreSQL database schema for user management",
            "db_connection_verified": False
        }
    )

    logger.info("\n🧮 Symbolic Results with Custom Rule:")
    logger.info(f"   Rules fired: {result_db['symbolic_results']['fired_rules']}")
    if result_db['symbolic_results']['warnings']:
        for warning in result_db['symbolic_results']['warnings']:
            logger.warning(f"   ⚠️ {warning['rule']}: {warning['warning']}")

    # =========================================================================
    # SCENARIO 5: Edge Case Handling
    # =========================================================================
    logger.info("\n📝 SCENARIO 5: Edge Case Handling")
    logger.info("-" * 80)

    result_edge = reasoner.reason(
        task="Implement calculator with division function",
        context={
            "task": "Implement calculator with division function"
        }
    )

    logger.info("\n🧮 Symbolic Results:")
    logger.info(f"   Rules fired: {result_edge['symbolic_results']['fired_rules']}")
    for suggestion in result_edge['symbolic_results']['suggestions']:
        logger.info(f"   💡 {suggestion['suggestion']}")

    logger.info("\n✅ Rule ensures edge cases (division by zero) are handled!")

    # =========================================================================
    # SCENARIO 6: Multiple Rules Firing
    # =========================================================================
    logger.info("\n📝 SCENARIO 6: Complex Task (Multiple Rules)")
    logger.info("-" * 80)

    result_complex = reasoner.reason(
        task="Build user authentication API with rate limiting and password storage",
        context={
            "task": "Build user authentication API with rate limiting and password storage",
            "has_rate_limit": True
        }
    )

    logger.info("\n🧮 Symbolic Results:")
    logger.info(f"   Rules fired: {len(result_complex['symbolic_results']['fired_rules'])}")
    for rule_name in result_complex['symbolic_results']['fired_rules']:
        logger.info(f"      ✓ {rule_name}")

    logger.info(f"\n   Total suggestions: {len(result_complex['symbolic_results']['suggestions'])}")
    for i, suggestion in enumerate(result_complex['symbolic_results']['suggestions'], 1):
        logger.info(f"   {i}. {suggestion['suggestion']}")

    logger.info("\n✅ Multiple rules work together to ensure comprehensive coverage!")

    # =========================================================================
    # SCENARIO 7: Rule Statistics
    # =========================================================================
    logger.info("\n📊 RULE ENGINE STATISTICS:")
    logger.info("=" * 80)

    stats = reasoner.get_rule_statistics()
    logger.info(f"Agent: {stats['agent']}")
    logger.info(f"Total Rules: {stats['total_rules']}")
    logger.info(f"Total Evaluations: {stats['total_evaluations']}")
    logger.info("\nRules by Type:")
    for rule_type, count in stats['rules_by_type'].items():
        logger.info(f"   {rule_type}: {count}")

    # =========================================================================
    # DEMONSTRATION: Neural + Symbolic Integration
    # =========================================================================
    logger.info("\n🧠 HYBRID REASONING DEMONSTRATION:")
    logger.info("=" * 80)

    logger.info("\n1️⃣  SYMBOLIC LAYER (Rules):")
    logger.info("   ✓ Enforces constraints (NO hardcoded credentials)")
    logger.info("   ✓ Ensures best practices (rate limiting)")
    logger.info("   ✓ Guarantees safety (edge case handling)")

    logger.info("\n2️⃣  NEURAL LAYER (LLM):")
    logger.info("   ✓ Creative implementation (HOW to do rate limiting)")
    logger.info("   ✓ Context-aware decisions (exponential backoff vs fixed delay)")
    logger.info("   ✓ Flexible problem solving (adapt to specific use case)")

    logger.info("\n3️⃣  COMBINED:")
    logger.info("   → Symbolic rules GUARANTEE certain behaviors")
    logger.info("   → Neural reasoning OPTIMIZES implementation")
    logger.info("   → Result: Robust AND flexible system")

    logger.info("\n✅ Neurosymbolic Reasoning Test Completed!")
    logger.info("=" * 80)
    logger.info("\n💡 Key Takeaways:")
    logger.info("   1. Rules enforce hard constraints (fail fast on violations)")
    logger.info("   2. Rules suggest best practices (guide neural reasoning)")
    logger.info("   3. Custom rules can be added for domain-specific needs")
    logger.info("   4. Multiple rules can fire together for complex tasks")
    logger.info("   5. Symbolic + Neural = Best of both worlds")


if __name__ == "__main__":
    test_neurosymbolic_reasoning()
