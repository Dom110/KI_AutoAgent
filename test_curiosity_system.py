#!/usr/bin/env python3
"""
E2E Test: Curiosity System v6

Tests curiosity-driven requirement gathering:
1. Detect ambiguous task descriptions
2. Identify knowledge gaps
3. Generate clarifying questions
4. Provide default assumptions
5. Enhance task descriptions with user answers

Expected behavior:
- Detects vague/incomplete tasks
- Generates relevant questions
- Creates WebSocket clarification messages
- Suggests sensible defaults when user skips

Debug mode: All logs enabled for troubleshooting

Author: KI AutoAgent Team
Created: 2025-10-09
Phase: 2.2 - Curiosity System Implementation
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)


async def test_clear_task():
    """Test 1: Clear, detailed task (no questions needed)"""
    logger.info("=" * 80)
    logger.info("TEST 1: Clear Task (No Gaps)")
    logger.info("=" * 80)

    try:
        from cognitive.curiosity_system_v6 import CuriositySystemV6

        curiosity = CuriositySystemV6()

        # Clear, detailed task
        task = """Create a Python CLI calculator application with the following features:
- Addition, subtraction, multiplication, and division
- History tracking of previous calculations
- Error handling for invalid inputs
- Use argparse for command-line arguments
"""

        analysis = await curiosity.analyze_task(task)

        logger.info(f"📊 Analysis Results:")
        logger.info(f"   Has gaps: {analysis['has_gaps']}")
        logger.info(f"   Confidence: {analysis['confidence']:.2f}")
        logger.info(f"   Severity: {analysis['severity']}")
        logger.info(f"   Questions: {len(analysis['questions'])}")

        # Validate
        # Clear task should have high confidence, no high-severity gaps
        assert analysis["confidence"] >= 0.8, f"Expected high confidence, got {analysis['confidence']}"
        assert analysis["severity"] in ["none", "low"], f"Expected low/no severity, got {analysis['severity']}"

        # Should not trigger questions
        should_ask = await curiosity.should_ask_questions(analysis)
        assert not should_ask, "Should not ask questions for clear task"

        logger.info("✅ Clear task correctly identified!")
        return True

    except Exception as e:
        logger.error(f"❌ Test 1 failed: {e}", exc_info=True)
        return False


async def test_vague_task():
    """Test 2: Vague task (many questions needed)"""
    logger.info("=" * 80)
    logger.info("TEST 2: Vague Task (Many Gaps)")
    logger.info("=" * 80)

    try:
        from cognitive.curiosity_system_v6 import CuriositySystemV6

        curiosity = CuriositySystemV6()

        # Very vague task
        task = "Build an app"

        analysis = await curiosity.analyze_task(task)

        logger.info(f"📊 Analysis Results:")
        logger.info(f"   Has gaps: {analysis['has_gaps']}")
        logger.info(f"   Confidence: {analysis['confidence']:.2f}")
        logger.info(f"   Severity: {analysis['severity']}")
        logger.info(f"   Gaps: {len(analysis['gaps'])}")
        logger.info(f"   Questions: {len(analysis['questions'])}")

        # Log gaps
        logger.info(f"   Identified Gaps:")
        for gap in analysis["gaps"]:
            logger.info(f"      - {gap['type']}: {gap['description']} ({gap['severity']})")

        # Log questions
        logger.info(f"   Questions to ask:")
        for i, q in enumerate(analysis["questions"], 1):
            logger.info(f"      {i}. {q}")

        # Validate
        assert analysis["has_gaps"] is True, "Should have gaps"
        assert analysis["confidence"] < 0.5, f"Expected low confidence, got {analysis['confidence']}"
        assert analysis["severity"] == "high", f"Expected high severity, got {analysis['severity']}"
        assert len(analysis["questions"]) >= 3, f"Expected at least 3 questions, got {len(analysis['questions'])}"

        # Should trigger questions
        should_ask = await curiosity.should_ask_questions(analysis)
        assert should_ask, "Should ask questions for vague task"

        logger.info("✅ Vague task correctly identified!")
        return True

    except Exception as e:
        logger.error(f"❌ Test 2 failed: {e}", exc_info=True)
        return False


async def main():
    """Run all tests"""
    logger.info("🚀 Starting Curiosity System v6 E2E Tests")
    logger.info(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run tests
    results = {}

    results["test_1_clear"] = await test_clear_task()
    results["test_2_vague"] = await test_vague_task()

    # Summary
    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")

    logger.info("-" * 80)
    logger.info(f"Total: {total_tests} tests")
    logger.info(f"Passed: {passed_tests} tests")
    logger.info(f"Failed: {failed_tests} tests")

    if failed_tests == 0:
        logger.info("🎉 ALL TESTS PASSED!")
        return 0
    else:
        logger.error(f"❌ {failed_tests} TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
