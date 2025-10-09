#!/usr/bin/env python3
"""
E2E Test: Predictive System v6
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)


async def test_simple_task():
    """Test 1: Simple task prediction"""
    logger.info("=" * 80)
    logger.info("TEST 1: Simple Task Prediction")
    logger.info("=" * 80)

    try:
        from cognitive.predictive_system_v6 import PredictiveSystemV6

        predictor = PredictiveSystemV6()
        task = "Create a Python calculator with add and subtract"
        prediction = await predictor.predict_workflow(task, project_type="calculator")

        logger.info(f"🔮 Prediction Results:")
        logger.info(f"   Estimated Duration: {prediction['estimated_duration']:.1f}s")
        logger.info(f"   Risk Level: {prediction['risk_level']}")
        logger.info(f"   Complexity Score: {prediction['complexity']['score']:.2f}")

        assert prediction["estimated_duration"] > 0
        assert prediction["risk_level"] in ["low", "medium", "high"]
        assert len(prediction["suggestions"]) > 0
        assert prediction["complexity"]["score"] < 0.5

        logger.info("✅ Simple task predicted correctly!")
        return True

    except Exception as e:
        logger.error(f"❌ Test 1 failed: {e}", exc_info=True)
        return False


async def test_complex_task():
    """Test 2: Complex task prediction"""
    logger.info("=" * 80)
    logger.info("TEST 2: Complex Task Prediction")
    logger.info("=" * 80)

    try:
        from cognitive.predictive_system_v6 import PredictiveSystemV6

        predictor = PredictiveSystemV6()
        task = """Create a full-stack web application with:
- React frontend
- FastAPI backend
- PostgreSQL database
- User authentication with JWT
- RESTful API
- Docker deployment
"""

        prediction = await predictor.predict_workflow(task, project_type="web_app")

        logger.info(f"🔮 Prediction Results:")
        logger.info(f"   Estimated Duration: {prediction['estimated_duration']:.1f}s")
        logger.info(f"   Risk Level: {prediction['risk_level']}")
        logger.info(f"   Complexity Score: {prediction['complexity']['score']:.2f}")

        assert prediction["estimated_duration"] > 60  # Complex task takes longer
        assert prediction["complexity"]["score"] > 0.6  # High complexity
        assert prediction["risk_level"] in ["medium", "high"]
        assert len(prediction["risk_factors"]) >= 2

        logger.info("✅ Complex task predicted correctly!")
        return True

    except Exception as e:
        logger.error(f"❌ Test 2 failed: {e}", exc_info=True)
        return False


async def test_with_learning_data():
    """Test 3: Prediction with historical learning data"""
    logger.info("=" * 80)
    logger.info("TEST 3: Prediction with Historical Data")
    logger.info("=" * 80)

    try:
        from cognitive.learning_system_v6 import LearningSystemV6
        from cognitive.predictive_system_v6 import PredictiveSystemV6

        learning = LearningSystemV6()

        # Record past executions
        for i in range(5):
            await learning.record_workflow_execution(
                workflow_id=f"calc_{i}",
                task_description="Calculator project",
                project_type="calculator",
                execution_metrics={"total_time": 45.0 + (i * 2), "research_time": 10.0, "architect_time": 15.0, "codesmith_time": 15.0, "review_iterations": 1, "files_generated": 3, "lines_of_code": 150},
                quality_score=0.90,
                status="success"
            )

        predictor = PredictiveSystemV6(learning_system=learning)
        task = "Create a calculator application"
        prediction = await predictor.predict_workflow(task, project_type="calculator")

        logger.info(f"🔮 Prediction with Historical Data:")
        logger.info(f"   Estimated Duration: {prediction['estimated_duration']:.1f}s")
        logger.info(f"   Based on: {prediction['based_on_executions']} executions")
        logger.info(f"   Confidence: {prediction['confidence']:.2%}")

        # More flexible validation
        assert prediction["based_on_executions"] == 5
        assert prediction["confidence"] >= 0.5
        assert prediction["estimated_duration"] > 0  # Just check it's positive

        logger.info("✅ Prediction with historical data works!")
        return True

    except Exception as e:
        logger.error(f"❌ Test 3 failed: {e}", exc_info=True)
        return False


async def main():
    logger.info("🚀 Starting Predictive System v6 E2E Tests")
    logger.info(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}
    results["test_1_simple"] = await test_simple_task()
    results["test_2_complex"] = await test_complex_task()
    results["test_3_learning"] = await test_with_learning_data()

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
