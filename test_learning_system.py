#!/usr/bin/env python3
"""
E2E Test: Learning System v6

Tests the learning system capabilities:
1. Record workflow executions
2. Extract success patterns
3. Suggest optimizations based on history
4. Track project-type-specific statistics
5. Overall performance metrics

Expected behavior:
- Learns from successful and failed executions
- Provides suggestions based on historical data
- Tracks quality scores and execution times
- Adapts recommendations based on project type

Debug mode: All logs enabled for troubleshooting

Author: KI AutoAgent Team
Created: 2025-10-09
Phase: 2.1 - Learning System Implementation
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


async def test_record_execution():
    """Test 1: Record workflow execution"""
    logger.info("=" * 80)
    logger.info("TEST 1: Record Workflow Execution")
    logger.info("=" * 80)

    try:
        from cognitive.learning_system_v6 import LearningSystemV6

        # Create learning system
        learning = LearningSystemV6()

        # Record a successful execution
        execution_metrics = {
            "total_time": 45.5,
            "research_time": 10.0,
            "architect_time": 15.0,
            "codesmith_time": 15.5,
            "review_iterations": 1,
            "files_generated": 3,
            "lines_of_code": 150
        }

        record = await learning.record_workflow_execution(
            workflow_id="test_001",
            task_description="Create a simple calculator app",
            project_type="calculator",
            execution_metrics=execution_metrics,
            quality_score=0.92,
            status="success",
            errors=[]
        )

        # Validate record
        assert record["workflow_id"] == "test_001"
        assert record["project_type"] == "calculator"
        assert record["quality_score"] == 0.92
        assert record["status"] == "success"
        assert record["success"] is True  # quality >= 0.75

        # Check session history
        assert len(learning.session_history) == 1

        logger.info(f"✅ Execution recorded successfully")
        logger.info(f"   Workflow ID: {record['workflow_id']}")
        logger.info(f"   Quality: {record['quality_score']}")
        logger.info(f"   Success: {record['success']}")

        return True

    except Exception as e:
        logger.error(f"❌ Test 1 failed: {e}", exc_info=True)
        return False


async def test_multiple_executions():
    """Test 2: Record multiple executions and track patterns"""
    logger.info("=" * 80)
    logger.info("TEST 2: Multiple Executions Pattern Learning")
    logger.info("=" * 80)

    try:
        from cognitive.learning_system_v6 import LearningSystemV6

        learning = LearningSystemV6()

        # Simulate 3 calculator project executions
        executions = [
            {
                "workflow_id": "calc_001",
                "task_description": "Create basic calculator with add/subtract",
                "project_type": "calculator",
                "execution_metrics": {
                    "total_time": 42.0,
                    "research_time": 8.0,
                    "architect_time": 14.0,
                    "codesmith_time": 15.0,
                    "review_iterations": 1,
                    "files_generated": 2,
                    "lines_of_code": 100
                },
                "quality_score": 0.88,
                "status": "success"
            },
            {
                "workflow_id": "calc_002",
                "task_description": "Create calculator with multiply/divide",
                "project_type": "calculator",
                "execution_metrics": {
                    "total_time": 48.0,
                    "research_time": 10.0,
                    "architect_time": 16.0,
                    "codesmith_time": 17.0,
                    "review_iterations": 2,
                    "files_generated": 3,
                    "lines_of_code": 150
                },
                "quality_score": 0.91,
                "status": "success"
            },
            {
                "workflow_id": "calc_003",
                "task_description": "Create scientific calculator",
                "project_type": "calculator",
                "execution_metrics": {
                    "total_time": 55.0,
                    "research_time": 12.0,
                    "architect_time": 18.0,
                    "codesmith_time": 20.0,
                    "review_iterations": 2,
                    "files_generated": 4,
                    "lines_of_code": 200
                },
                "quality_score": 0.94,
                "status": "success"
            }
        ]

        # Record all executions
        for exec_data in executions:
            await learning.record_workflow_execution(**exec_data)

        # Validate session history
        assert len(learning.session_history) == 3

        logger.info(f"✅ Recorded {len(learning.session_history)} executions")

        # Get project type statistics
        stats = await learning.get_project_type_statistics("calculator")

        logger.info(f"📊 Calculator Project Statistics:")
        logger.info(f"   Total Executions: {stats['total_executions']}")
        logger.info(f"   Success Rate: {stats['success_rate']:.2%}")
        logger.info(f"   Avg Duration: {stats['avg_duration']:.1f}s")
        logger.info(f"   Avg Quality: {stats['avg_quality']:.2f}")

        assert stats["total_executions"] == 3
        assert stats["success_rate"] == 1.0  # All successful
        assert 40 < stats["avg_duration"] < 60  # Avg around 48s
        assert stats["avg_quality"] > 0.85

        return True

    except Exception as e:
        logger.error(f"❌ Test 2 failed: {e}", exc_info=True)
        return False


async def test_suggestions():
    """Test 3: Get optimization suggestions based on history"""
    logger.info("=" * 80)
    logger.info("TEST 3: Optimization Suggestions")
    logger.info("=" * 80)

    try:
        from cognitive.learning_system_v6 import LearningSystemV6

        learning = LearningSystemV6()

        # Record multiple calculator executions
        executions = [
            {"workflow_id": "c1", "project_type": "calculator", "quality_score": 0.90, "time": 45.0, "reviews": 1},
            {"workflow_id": "c2", "project_type": "calculator", "quality_score": 0.92, "time": 48.0, "reviews": 1},
            {"workflow_id": "c3", "project_type": "calculator", "quality_score": 0.88, "time": 50.0, "reviews": 2},
        ]

        for exec_data in executions:
            await learning.record_workflow_execution(
                workflow_id=exec_data["workflow_id"],
                task_description="Calculator project",
                project_type=exec_data["project_type"],
                execution_metrics={
                    "total_time": exec_data["time"],
                    "research_time": 10.0,
                    "architect_time": 15.0,
                    "codesmith_time": 15.0,
                    "review_iterations": exec_data["reviews"],
                    "files_generated": 3,
                    "lines_of_code": 150
                },
                quality_score=exec_data["quality_score"],
                status="success",
                errors=[]
            )

        # Get suggestions for new calculator project
        suggestions = await learning.suggest_optimizations(
            task_description="Create a new calculator app",
            project_type="calculator"
        )

        logger.info(f"💡 Optimization Suggestions:")
        logger.info(f"   Based on: {suggestions['based_on']} similar executions")
        logger.info(f"   Expected duration: {suggestions['expected_duration']:.1f}s")
        logger.info(f"   Confidence: {suggestions['confidence']:.2%}")
        logger.info(f"   Suggestions:")
        for i, suggestion in enumerate(suggestions["suggestions"], 1):
            logger.info(f"      {i}. {suggestion}")

        # Validate suggestions
        assert suggestions["based_on"] == 3
        assert 40 < suggestions["expected_duration"] < 55
        assert suggestions["confidence"] > 0.0
        assert len(suggestions["suggestions"]) > 0

        logger.info("✅ Suggestions generated successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Test 3 failed: {e}", exc_info=True)
        return False


async def test_no_history_suggestions():
    """Test 4: Suggestions when no history available"""
    logger.info("=" * 80)
    logger.info("TEST 4: Suggestions With No History")
    logger.info("=" * 80)

    try:
        from cognitive.learning_system_v6 import LearningSystemV6

        learning = LearningSystemV6()

        # No executions recorded - get suggestions
        suggestions = await learning.suggest_optimizations(
            task_description="Create a web app",
            project_type="web_app"
        )

        logger.info(f"💡 Suggestions (no history):")
        logger.info(f"   Based on: {suggestions['based_on']} executions")
        logger.info(f"   Confidence: {suggestions['confidence']:.2%}")
        logger.info(f"   Suggestions:")
        for i, suggestion in enumerate(suggestions["suggestions"], 1):
            logger.info(f"      {i}. {suggestion}")

        # Validate
        assert suggestions["based_on"] == 0
        assert suggestions["expected_duration"] is None
        assert suggestions["confidence"] == 0.0
        assert len(suggestions["suggestions"]) > 0
        assert "no historical data" in suggestions["suggestions"][0].lower()

        logger.info("✅ Correctly handles no history case!")
        return True

    except Exception as e:
        logger.error(f"❌ Test 4 failed: {e}", exc_info=True)
        return False


async def test_overall_statistics():
    """Test 5: Overall learning system statistics"""
    logger.info("=" * 80)
    logger.info("TEST 5: Overall Statistics")
    logger.info("=" * 80)

    try:
        from cognitive.learning_system_v6 import LearningSystemV6

        learning = LearningSystemV6()

        # Record different project types
        executions = [
            {"project_type": "calculator", "quality": 0.90, "time": 45.0, "success": True},
            {"project_type": "calculator", "quality": 0.85, "time": 48.0, "success": True},
            {"project_type": "web_app", "quality": 0.95, "time": 60.0, "success": True},
            {"project_type": "web_app", "quality": 0.70, "time": 55.0, "success": False},  # Failed (< 0.75)
            {"project_type": "api", "quality": 0.88, "time": 40.0, "success": True},
        ]

        for i, exec_data in enumerate(executions):
            await learning.record_workflow_execution(
                workflow_id=f"test_{i:03d}",
                task_description=f"Test project {i}",
                project_type=exec_data["project_type"],
                execution_metrics={
                    "total_time": exec_data["time"],
                    "research_time": 10.0,
                    "architect_time": 15.0,
                    "codesmith_time": 15.0,
                    "review_iterations": 1,
                    "files_generated": 3,
                    "lines_of_code": 150
                },
                quality_score=exec_data["quality"],
                status="success" if exec_data["success"] else "error",
                errors=[] if exec_data["success"] else ["Quality too low"]
            )

        # Get overall statistics
        stats = await learning.get_overall_statistics()

        logger.info(f"📊 Overall Statistics:")
        logger.info(f"   Total Executions: {stats['total_executions']}")
        logger.info(f"   Success Rate: {stats['success_rate']:.2%}")
        logger.info(f"   Avg Duration: {stats['avg_duration']:.1f}s")
        logger.info(f"   Avg Quality: {stats['avg_quality']:.2f}")
        logger.info(f"   Project Types:")
        for pt, pt_stats in stats["project_types"].items():
            logger.info(f"      - {pt}: {pt_stats['count']} executions, "
                       f"{pt_stats['success_rate']:.2%} success rate")

        # Validate
        assert stats["total_executions"] == 5
        assert stats["success_rate"] == 4 / 5  # 4 successful, 1 failed
        assert len(stats["project_types"]) == 3  # calculator, web_app, api

        # Check project type stats
        assert stats["project_types"]["calculator"]["count"] == 2
        assert stats["project_types"]["web_app"]["count"] == 2
        assert stats["project_types"]["api"]["count"] == 1

        logger.info("✅ Overall statistics correct!")
        return True

    except Exception as e:
        logger.error(f"❌ Test 5 failed: {e}", exc_info=True)
        return False


async def test_error_tracking():
    """Test 6: Track and analyze common errors"""
    logger.info("=" * 80)
    logger.info("TEST 6: Error Tracking")
    logger.info("=" * 80)

    try:
        from cognitive.learning_system_v6 import LearningSystemV6

        learning = LearningSystemV6()

        # Record executions with errors
        executions = [
            {
                "workflow_id": "err_001",
                "errors": ["Syntax error in generated code", "Missing import statement"]
            },
            {
                "workflow_id": "err_002",
                "errors": ["Syntax error in generated code", "Invalid function call"]
            },
            {
                "workflow_id": "err_003",
                "errors": ["Syntax error in generated code", "Type mismatch"]
            }
        ]

        for exec_data in executions:
            await learning.record_workflow_execution(
                workflow_id=exec_data["workflow_id"],
                task_description="Test with errors",
                project_type="test",
                execution_metrics={
                    "total_time": 30.0,
                    "research_time": 5.0,
                    "architect_time": 10.0,
                    "codesmith_time": 10.0,
                    "review_iterations": 3,
                    "files_generated": 2,
                    "lines_of_code": 100
                },
                quality_score=0.60,  # Failed
                status="error",
                errors=exec_data["errors"]
            )

        # Extract common errors
        common_errors = learning._extract_common_errors(learning.session_history)

        logger.info(f"⚠️  Common Errors Detected:")
        for i, error in enumerate(common_errors, 1):
            logger.info(f"   {i}. {error}")

        # Validate
        assert len(common_errors) > 0
        assert any("Syntax error" in err for err in common_errors)

        logger.info("✅ Error tracking works!")
        return True

    except Exception as e:
        logger.error(f"❌ Test 6 failed: {e}", exc_info=True)
        return False


async def main():
    """Run all tests"""
    logger.info("🚀 Starting Learning System v6 E2E Tests")
    logger.info(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run tests
    results = {}

    results["test_1_record"] = await test_record_execution()
    results["test_2_multiple"] = await test_multiple_executions()
    results["test_3_suggestions"] = await test_suggestions()
    results["test_4_no_history"] = await test_no_history_suggestions()
    results["test_5_overall_stats"] = await test_overall_statistics()
    results["test_6_errors"] = await test_error_tracking()

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
