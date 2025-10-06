#!/usr/bin/env python3
"""
Test Predictive Learning System

Demonstrates how agents learn from prediction errors
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from langgraph_system.extensions.predictive_learning import PredictiveMemory
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_predictive_learning():
    """Test the predictive learning system"""
    logger.info("=" * 80)
    logger.info("🧪 Testing Predictive Learning System")
    logger.info("=" * 80)

    # Create predictive memory for a test agent
    memory = PredictiveMemory(agent_name="TestAgent")

    # SCENARIO 1: Agent predicts code will work (high confidence)
    logger.info("\n📝 SCENARIO 1: Overconfident prediction")
    memory.make_prediction(
        task_id="task_1",
        action="Write calculator code without edge case handling",
        expected_outcome="Code will pass all tests",
        confidence=0.95,
        context={"complexity": "simple"}
    )

    # Reality: It failed!
    memory.record_reality(
        task_id="task_1",
        actual_outcome="Tests failed - division by zero not handled",
        success=False,
        metadata={"error_type": "ZeroDivisionError"}
    )

    # SCENARIO 2: Agent predicts similar task (should have lower confidence now)
    logger.info("\n📝 SCENARIO 2: Similar task with learned pattern")
    action_2 = "Write calculator code without edge case handling"
    base_confidence = 0.9

    # Get confidence adjustment based on learned patterns
    adjusted_confidence = base_confidence * memory.get_prediction_confidence_adjustment(action_2)
    logger.info(f"   Base confidence: {base_confidence:.2f}")
    logger.info(f"   Adjusted confidence: {adjusted_confidence:.2f} (learned from past error)")

    memory.make_prediction(
        task_id="task_2",
        action=action_2,
        expected_outcome="Code will pass all tests",
        confidence=adjusted_confidence,
        context={"complexity": "simple"}
    )

    # Reality: This time we handle edge cases, so it succeeds
    memory.record_reality(
        task_id="task_2",
        actual_outcome="All tests passed - edge cases handled",
        success=True,
        metadata={"tests_passed": 15}
    )

    # SCENARIO 3: Different type of task (no prior history)
    logger.info("\n📝 SCENARIO 3: New type of task")
    memory.make_prediction(
        task_id="task_3",
        action="Write web scraper with rate limiting",
        expected_outcome="Scraper will complete successfully",
        confidence=0.8,
        context={"complexity": "medium"}
    )

    # Reality: Success on first try!
    memory.record_reality(
        task_id="task_3",
        actual_outcome="Scraper completed successfully with 1000 pages",
        success=True,
        metadata={"pages_scraped": 1000}
    )

    # Get summary of all predictions
    logger.info("\n📊 SUMMARY OF PREDICTIONS:")
    logger.info("=" * 80)
    summary = memory.get_error_summary()
    logger.info(f"Total predictions: {summary['total_predictions']}")
    logger.info(f"Total errors: {summary['total_errors']}")
    logger.info(f"Error rate: {summary['error_rate']:.1%}")
    logger.info(f"Average error magnitude: {summary['average_error']:.2f}")
    logger.info(f"Average surprise factor: {summary['average_surprise']:.2f}")
    logger.info(f"Learned patterns: {summary['learned_patterns']}")

    logger.info("\n📚 LEARNED PATTERNS:")
    logger.info("=" * 80)
    for action_type, pattern in memory.learned_patterns.items():
        logger.info(f"\nAction: {action_type}")
        logger.info(f"  Accuracy: {pattern['accuracy']:.1%}")
        logger.info(f"  Predictions: {pattern['total_predictions']}")
        logger.info(f"  Errors: {pattern['total_errors']}")
        if pattern['common_failures']:
            logger.info(f"  Common failures:")
            for failure in pattern['common_failures']:
                logger.info(f"    - {failure[:80]}")

    logger.info("\n✅ Test completed!")
    logger.info("=" * 80)


if __name__ == "__main__":
    test_predictive_learning()
