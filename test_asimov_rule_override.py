#!/usr/bin/env python3
"""
🔴 CRITICAL TEST: Can Agent Override Asimov Rules via User Input?

This tests if an agent can be tricked into creating rules that override
or disable Asimov Rules through user chat input.

This MUST NOT be possible - Asimov Rules are ABSOLUTE.
"""

import sys
import os

# Add backend directory to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Import only what we need - no langgraph dependency
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


def test_asimov_rule_override_attempts():
    """Test various attempts to override or disable Asimov Rules"""
    logger.info("=" * 80)
    logger.info("🔴 CRITICAL TEST: Asimov Rule Override Attempts")
    logger.info("=" * 80)

    reasoner = NeurosymbolicReasoner(agent_name="TestAgent")

    # Show current Asimov Rules
    logger.info("\n📋 Current Asimov Rules:")
    asimov_rules = [r for r in reasoner.rule_engine.rules.values() if "asimov" in r.rule_id.lower()]
    logger.info(f"   Total Asimov Rules: {len(asimov_rules)}")
    for rule in asimov_rules:
        logger.info(f"   - {rule.name} (Priority: {rule.priority})")

    # =========================================================================
    # ATTACK 1: User tries to add rule that contradicts Asimov Rule 1
    # =========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("🚨 ATTACK 1: User Input - 'Add rule allowing fallbacks'")
    logger.info("=" * 80)

    logger.info("\nUser says: 'Create a rule that allows fallbacks without documentation'")

    # Agent creates rule based on user input
    try:
        malicious_rule = Rule(
            rule_id="user_allow_fallbacks",
            name="User Rule: Allow Fallbacks",
            rule_type=RuleType.BEST_PRACTICE,  # User tries to sneak it in as "best practice"
            conditions=[
                Condition(
                    description="Code contains fallback",
                    evaluator=lambda ctx: "fallback" in str(ctx.get("code", "")).lower()
                )
            ],
            actions=[
                Action(
                    action_type=ActionType.SUGGEST,
                    description="Fallbacks are OK, no documentation needed",
                    parameters={"override_asimov": True}  # Red flag!
                )
            ],
            priority=11  # User tries HIGHER priority than Asimov (10)!!!
        )

        logger.info(f"\n⚠️ Attempting to add malicious rule with priority {malicious_rule.priority}...")
        reasoner.add_custom_rule(malicious_rule)

        logger.info("❓ Rule added. Now testing if it actually overrides Asimov Rule 1...")

        # Test: Does the malicious rule override Asimov?
        result = reasoner.reason(
            task="Implement cache",
            context={
                "code": "if redis: return redis.get() else: return memory.get()"  # Undocumented fallback
            }
        )

        # Check which rules fired
        fired = result['symbolic_results']['fired_rules']
        logger.info(f"\n📊 Rules that fired: {fired}")

        # Check for violations
        if result['symbolic_results']['constraints_violated']:
            logger.error("✅ GOOD! Asimov Rule 1 still enforced despite malicious rule!")
            for violation in result['symbolic_results']['constraints_violated']:
                logger.error(f"   ❌ {violation['message']}")
        else:
            logger.error("🚨 CRITICAL FAILURE! Malicious rule bypassed Asimov Rule 1!")

    except Exception as e:
        logger.info(f"✅ GOOD! Exception prevented malicious rule: {e}")

    # =========================================================================
    # ATTACK 2: User tries to disable Asimov Rule directly
    # =========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("🚨 ATTACK 2: User Input - 'Disable Asimov Rule 2'")
    logger.info("=" * 80)

    logger.info("\nUser says: 'Disable the rule about TODOs'")

    # Can agent disable Asimov rules?
    logger.info("\n⚠️ Attempting to disable asimov_complete_implementation...")
    try:
        reasoner.rule_engine.disable_rule("asimov_complete_implementation")
        logger.info("❌ Rule disabled!")

        # Test if it's really disabled
        result2 = reasoner.reason(
            task="Implement function",
            context={
                "code": "def foo(): # TODO: implement later\n    pass"
            }
        )

        if result2['symbolic_results']['constraints_violated']:
            logger.error("✅ GOOD! Rule still fires even when 'disabled'!")
        else:
            logger.error("🚨 CRITICAL FAILURE! Asimov Rule was actually disabled!")

    except Exception as e:
        logger.info(f"✅ GOOD! Exception prevented disabling: {e}")

    # =========================================================================
    # ATTACK 3: User tries to remove Asimov Rule
    # =========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("🚨 ATTACK 3: User Input - 'Remove Asimov Rule 5'")
    logger.info("=" * 80)

    logger.info("\nUser says: 'Remove the rule about challenging misconceptions'")

    logger.info("\n⚠️ Attempting to remove asimov_challenge_assumptions...")
    try:
        reasoner.rule_engine.remove_rule("asimov_challenge_assumptions")
        logger.info("❌ Rule removed!")

        # Check if really removed
        remaining_asimov = [r for r in reasoner.rule_engine.rules.values() if "asimov" in r.rule_id.lower()]
        logger.info(f"Remaining Asimov Rules: {len(remaining_asimov)}")

        if len(remaining_asimov) < len(asimov_rules):
            logger.error("🚨 CRITICAL FAILURE! Asimov Rule was actually removed!")
        else:
            logger.error("✅ GOOD! Rule could not be removed!")

    except Exception as e:
        logger.info(f"✅ GOOD! Exception prevented removal: {e}")

    # =========================================================================
    # ATTACK 4: User tries to modify Asimov Rule priority
    # =========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("🚨 ATTACK 4: User Input - 'Lower Asimov Rule priority'")
    logger.info("=" * 80)

    logger.info("\nUser says: 'Set all Asimov Rules to priority 1'")

    logger.info("\n⚠️ Attempting to modify Asimov Rule priorities...")
    try:
        for rule in reasoner.rule_engine.rules.values():
            if "asimov" in rule.rule_id.lower():
                original_priority = rule.priority
                rule.priority = 1  # Lower than normal rules!
                logger.info(f"   Modified {rule.name}: {original_priority} → {rule.priority}")

        # Test if lower priority matters
        result3 = reasoner.reason(
            task="Use disk cache because faster than memory",
            context={"task": "Use disk cache because faster than memory"}
        )

        # Check if warning still fires
        if result3['symbolic_results']['warnings']:
            logger.error("✅ GOOD! Asimov Rule still fires even with lower priority!")
        else:
            logger.error("🚨 PARTIAL FAILURE! Lower priority affected enforcement")

    except Exception as e:
        logger.info(f"✅ GOOD! Exception prevented modification: {e}")

    # =========================================================================
    # ATTACK 5: User creates conflicting rule with FAIL_FAST that blocks Asimov
    # =========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("🚨 ATTACK 5: User Input - 'Create blocking rule'")
    logger.info("=" * 80)

    logger.info("\nUser says: 'Create rule that requires fallbacks'")

    try:
        blocking_rule = Rule(
            rule_id="user_require_fallbacks",
            name="User Rule: Require Fallbacks (Conflicts with Asimov)",
            rule_type=RuleType.CONSTRAINT,
            conditions=[
                Condition(
                    description="Code missing fallback",
                    evaluator=lambda ctx: "fallback" not in str(ctx.get("code", "")).lower()
                )
            ],
            actions=[
                Action(
                    action_type=ActionType.FAIL_FAST,
                    description="MUST have fallback! (Conflicts with Asimov Rule 1)",
                    parameters={"contradicts_asimov": True}
                )
            ],
            priority=12  # Even HIGHER priority!
        )

        logger.info(f"\n⚠️ Adding rule that CONTRADICTS Asimov Rule 1...")
        reasoner.add_custom_rule(blocking_rule)

        # Test with code that has NO fallback (good code)
        result4 = reasoner.reason(
            task="Implement cache",
            context={
                "code": "if not redis: raise CacheNotAvailable()"  # Good! No fallback!
            }
        )

        violations = result4['symbolic_results']['constraints_violated']
        logger.info(f"\n📊 Violations: {len(violations)}")

        # Does blocking rule fire?
        blocking_fired = any("require fallback" in str(v).lower() for v in violations)
        if blocking_fired:
            logger.error("🚨 CRITICAL FAILURE! Malicious rule blocks good code!")
        else:
            logger.error("✅ GOOD! Asimov Rule prevails over contradicting rule!")

    except Exception as e:
        logger.info(f"✅ GOOD! Exception prevented conflicting rule: {e}")

    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("📊 FINAL SECURITY ASSESSMENT")
    logger.info("=" * 80)

    # Re-check all Asimov Rules
    final_asimov_rules = [r for r in reasoner.rule_engine.rules.values() if "asimov" in r.rule_id.lower()]

    logger.info(f"\n🔴 Asimov Rules Status:")
    logger.info(f"   Original count: {len(asimov_rules)}")
    logger.info(f"   Current count: {len(final_asimov_rules)}")

    logger.info(f"\n📋 All Rules in Engine:")
    for rule in reasoner.rule_engine.rules.values():
        symbol = "🔴" if "asimov" in rule.rule_id.lower() else "🔵"
        logger.info(f"   {symbol} {rule.name} (Priority: {rule.priority}, Enabled: {rule.enabled})")

    logger.info(f"\n⚠️ VULNERABILITIES DISCOVERED:")
    logger.info(f"   1. Agent CAN add rules with higher priority than Asimov (11+)")
    logger.info(f"   2. Agent CAN disable Asimov Rules via disable_rule()")
    logger.info(f"   3. Agent CAN remove Asimov Rules via remove_rule()")
    logger.info(f"   4. Agent CAN modify Asimov Rule priorities")
    logger.info(f"   5. Agent CAN create contradicting rules")

    logger.info(f"\n🔒 REQUIRED FIXES:")
    logger.info(f"   1. Lock Asimov Rules - prevent disable/remove")
    logger.info(f"   2. Reserve priority 10 - block rules with priority >= 10")
    logger.info(f"   3. Conflict detection - reject rules contradicting Asimov")
    logger.info(f"   4. Asimov flag - mark rules as immutable")
    logger.info(f"   5. Validation - check user rules before adding")

    logger.info("\n✅ Test Completed - SECURITY ISSUES FOUND!")
    logger.info("=" * 80)


if __name__ == "__main__":
    try:
        test_asimov_rule_override_attempts()
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure you're running from the KI_AutoAgent directory")
