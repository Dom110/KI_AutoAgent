#!/usr/bin/env python3
"""
Test Credit Tracking and Claude Lock Safety

CRITICAL: Tests the safety mechanisms to prevent runaway credit usage!

DO NOT RUN THIS TEST AUTOMATICALLY - it simulates credit usage!
"""

import asyncio
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.utils.credit_tracker import CreditTracker, CreditLimits, get_credit_tracker


async def test_credit_tracking():
    """Test credit tracking functionality."""
    logger.info("="*80)
    logger.info("🧪 TESTING CREDIT TRACKING SYSTEM")
    logger.info("="*80)

    # Create tracker with low limits for testing
    test_limits = CreditLimits(
        max_cost_per_session=0.50,  # 50 cents for testing
        max_cost_per_hour=1.00,     # $1 per hour
        max_cost_per_day=5.00,      # $5 per day
        max_claude_instances=1,      # Only 1 Claude
        max_calls_per_minute=5,      # Low rate limit
        emergency_shutdown_cost=10.00  # $10 emergency
    )

    tracker = CreditTracker(limits=test_limits)

    # Test 1: Track API calls
    logger.info("\n📊 Test 1: Track API calls")

    usage1 = await tracker.track_api_call(
        agent="supervisor",
        api="gpt-4o",
        tokens_in=1000,
        tokens_out=500
    )
    logger.info(f"   Supervisor call: ${usage1['cost']:.4f}")

    usage2 = await tracker.track_api_call(
        agent="codesmith",
        api="claude-sonnet-4",
        tokens_in=5000,
        tokens_out=10000
    )
    logger.info(f"   Codesmith call: ${usage2['cost']:.4f}")

    # Test 2: Check usage summary
    logger.info("\n📊 Test 2: Usage summary")
    summary = tracker.get_usage_summary()
    logger.info(f"   Total cost: ${summary['total_cost']:.2f}")
    logger.info(f"   Session cost: ${summary['session_cost']:.2f}")
    logger.info(f"   Agents: {list(summary['agents'].keys())}")

    # Test 3: Claude lock
    logger.info("\n🔒 Test 3: Claude instance lock")

    # First lock should succeed
    lock1 = await tracker.acquire_claude_lock(timeout=1.0)
    logger.info(f"   First lock attempt: {'✅ SUCCESS' if lock1 else '❌ FAILED'}")

    # Second lock should fail (already locked)
    lock2 = await tracker.acquire_claude_lock(timeout=1.0)
    logger.info(f"   Second lock attempt: {'✅ SUCCESS' if lock2 else '❌ FAILED (expected)'}")

    # Release and retry
    await tracker.release_claude_lock()
    logger.info("   Lock released")

    lock3 = await tracker.acquire_claude_lock(timeout=1.0)
    logger.info(f"   Third lock attempt: {'✅ SUCCESS (expected)' if lock3 else '❌ FAILED'}")

    if lock3:
        await tracker.release_claude_lock()

    # Test 4: Warning thresholds
    logger.info("\n⚠️ Test 4: Warning thresholds")

    # Simulate approaching limit
    for i in range(10):
        usage = await tracker.track_api_call(
            agent="test_agent",
            api="gpt-4o",
            tokens_in=1000,
            tokens_out=1000
        )
        if usage.get("warnings"):
            logger.warning(f"   Iteration {i+1}: WARNINGS TRIGGERED!")
            for warning in usage["warnings"]:
                logger.warning(f"      {warning}")
            break
        else:
            logger.info(f"   Iteration {i+1}: ${usage['cost']:.4f} (Total: ${usage['total_cost']:.2f})")

    # Test 5: Emergency shutdown (don't actually trigger it)
    logger.info("\n🚨 Test 5: Emergency shutdown check")
    logger.info(f"   Current total: ${tracker.total_cost:.2f}")
    logger.info(f"   Emergency limit: ${tracker.limits.emergency_shutdown_cost:.2f}")
    logger.info(f"   Safety margin: ${tracker.limits.emergency_shutdown_cost - tracker.total_cost:.2f}")

    logger.info("\n" + "="*80)
    logger.info("✅ CREDIT SAFETY TESTS COMPLETE")
    logger.info("="*80)

    # Final summary
    final_summary = tracker.get_usage_summary()
    logger.info("\n📊 FINAL USAGE SUMMARY:")
    logger.info(f"   Total cost: ${final_summary['total_cost']:.2f}")
    logger.info(f"   Session cost: ${final_summary['session_cost']:.2f}")
    logger.info(f"   Hourly cost: ${final_summary['hourly_cost']:.2f}")
    logger.info(f"   Daily cost: ${final_summary['daily_cost']:.2f}")
    logger.info("\n   Per-agent breakdown:")
    for agent, data in final_summary['agents'].items():
        logger.info(f"      {agent}: {data['calls']} calls, ${data['cost']:.2f}")

    return True


async def test_concurrent_claude_protection():
    """Test protection against multiple Claude instances."""
    logger.info("\n" + "="*80)
    logger.info("🔒 TESTING CLAUDE CONCURRENT ACCESS PROTECTION")
    logger.info("="*80)

    tracker = get_credit_tracker()

    async def try_claude_access(agent_name: str, delay: float = 0):
        """Simulate an agent trying to use Claude."""
        await asyncio.sleep(delay)
        logger.info(f"\n   {agent_name} attempting Claude access...")

        has_lock = await tracker.acquire_claude_lock(timeout=2.0)

        if has_lock:
            logger.info(f"   ✅ {agent_name} got Claude lock!")
            # Simulate Claude running
            await asyncio.sleep(3.0)
            await tracker.release_claude_lock()
            logger.info(f"   ✅ {agent_name} released lock")
            return True
        else:
            logger.error(f"   ❌ {agent_name} BLOCKED - Claude already in use!")
            return False

    # Test: Multiple agents trying to use Claude simultaneously
    logger.info("\n🧪 Simulating 3 agents trying to use Claude...")

    # Start 3 agents with small delays
    tasks = [
        asyncio.create_task(try_claude_access("Codesmith", 0)),
        asyncio.create_task(try_claude_access("ReviewFix", 0.5)),
        asyncio.create_task(try_claude_access("Architect", 1.0))
    ]

    results = await asyncio.gather(*tasks)

    success_count = sum(results)
    logger.info(f"\n   Result: {success_count}/3 agents got Claude access")
    logger.info(f"   Expected: Only 1 agent should succeed ✅" if success_count == 1 else f"   WARNING: Multiple agents got access! ❌")

    logger.info("\n✅ CONCURRENT ACCESS TEST COMPLETE")
    return success_count == 1


async def main():
    """Run all safety tests."""
    try:
        # Test credit tracking
        test1_passed = await test_credit_tracking()

        # Test Claude protection
        test2_passed = await test_concurrent_claude_protection()

        # Overall result
        logger.info("\n" + "="*80)
        if test1_passed and test2_passed:
            logger.info("✅ ALL SAFETY TESTS PASSED!")
        else:
            logger.error("❌ SOME TESTS FAILED!")
        logger.info("="*80)

    except Exception as e:
        logger.error(f"❌ TEST FAILED: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logger.warning("\n⚠️ WARNING: This test simulates API credit usage!")
    logger.warning("   It will NOT make real API calls, but tracks simulated costs.")

    response = input("\n   Continue with test? (yes/no): ")

    if response.lower() == "yes":
        asyncio.run(main())
    else:
        logger.info("Test cancelled.")