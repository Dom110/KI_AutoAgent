#!/usr/bin/env python3
"""
E2E Test for Dynamic Workflow Planner v6.2
==========================================

Tests the new AI-based workflow planning system that replaces
the old pattern-based intent detection.

Test Scenarios:
1. CREATE workflow - Simple app generation
2. EXPLAIN workflow - German language ("Untersuche die App")
3. FIX workflow - Bug fixing
4. REFACTOR workflow - Code improvement

Author: KI AutoAgent Team
Date: 2025-10-12
Version: v6.2-alpha
"""

import asyncio
import json
import logging
import os
import shutil
import signal
import sys
import traceback
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/tmp/workflow_planner_e2e_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# 🎯 SIGNAL HANDLERS TO DEBUG WHY PROCESS DIES
def signal_handler(signum, frame):
    """Log all signals that the process receives."""
    signal_name = signal.Signals(signum).name
    logger.critical(f"\n{'='*80}")
    logger.critical(f"🚨 SIGNAL RECEIVED: {signal_name} ({signum})")
    logger.critical(f"{'='*80}")
    logger.critical(f"Process ID: {os.getpid()}")
    logger.critical(f"Timestamp: {datetime.now().isoformat()}")
    logger.critical(f"\n📍 Stack Trace:")
    for line in traceback.format_stack(frame):
        logger.critical(line.strip())
    logger.critical(f"{'='*80}\n")

    # Don't exit immediately - let logging flush
    sys.stdout.flush()
    sys.stderr.flush()

    # Re-raise to let Python handle it
    if signum in [signal.SIGTERM, signal.SIGINT]:
        logger.critical(f"⚠️  Process will now terminate due to {signal_name}")
        sys.exit(128 + signum)


# Install signal handlers for ALL catchable signals
SIGNALS_TO_CATCH = [
    signal.SIGTERM,  # Kill -15 (graceful)
    signal.SIGINT,   # Ctrl+C
    signal.SIGHUP,   # Terminal closed
    signal.SIGQUIT,  # Quit signal
    signal.SIGUSR1,  # User-defined
    signal.SIGUSR2,  # User-defined
]

for sig in SIGNALS_TO_CATCH:
    try:
        signal.signal(sig, signal_handler)
        logger.debug(f"✅ Installed signal handler for {signal.Signals(sig).name}")
    except (OSError, ValueError) as e:
        logger.warning(f"⚠️  Could not install handler for signal {sig}: {e}")

# Test workspace (isolated from development repo!)
TEST_WORKSPACE = Path.home() / "TestApps" / f"workflow_planner_test_{datetime.now():%Y%m%d_%H%M%S}"


class TestResults:
    """Store test results for final reporting."""

    def __init__(self):
        self.tests = []
        self.start_time = datetime.now()

    def add_test(self, name: str, success: bool, duration: float, details: dict):
        """Add test result."""
        self.tests.append({
            "name": name,
            "success": success,
            "duration": duration,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def report(self):
        """Generate final test report."""
        total_duration = (datetime.now() - self.start_time).total_seconds()
        passed = sum(1 for t in self.tests if t["success"])
        failed = len(self.tests) - passed

        print("\n" + "=" * 80)
        print("🧪 WORKFLOW PLANNER E2E TEST RESULTS")
        print("=" * 80)
        print(f"Total Tests: {len(self.tests)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏱️  Total Duration: {total_duration:.1f}s")
        print("=" * 80)

        for i, test in enumerate(self.tests, 1):
            status = "✅ PASS" if test["success"] else "❌ FAIL"
            print(f"\n{i}. {test['name']}: {status} ({test['duration']:.1f}s)")

            if test["details"]:
                print("   Details:")
                for key, value in test["details"].items():
                    if isinstance(value, list) and len(value) > 3:
                        print(f"     {key}: {len(value)} items")
                    else:
                        print(f"     {key}: {value}")

        print("\n" + "=" * 80)
        print(f"📊 Success Rate: {(passed/len(self.tests)*100):.1f}%")
        print("=" * 80 + "\n")

        return passed == len(self.tests)


def setup_test_workspace():
    """Setup clean test workspace."""
    logger.info(f"🧹 Setting up test workspace: {TEST_WORKSPACE}")

    # Remove old workspace if exists
    if TEST_WORKSPACE.exists():
        shutil.rmtree(TEST_WORKSPACE)

    # Create fresh workspace
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)

    logger.info("✅ Test workspace ready")


async def test_create_workflow(results: TestResults):
    """
    Test 1: CREATE workflow - Simple calculator app.

    Expected: AI should plan workflow with research → architect → codesmith → reviewfix
    """
    test_name = "CREATE Workflow - Simple Calculator"
    logger.info(f"\n{'='*60}")
    logger.info(f"🧪 Test 1: {test_name}")
    logger.info(f"{'='*60}")

    start = datetime.now()

    try:
        from workflow_v6_integrated import WorkflowV6Integrated

        workspace = TEST_WORKSPACE / "calculator_app"
        workspace.mkdir(exist_ok=True)

        workflow = WorkflowV6Integrated(workspace_path=str(workspace))
        await workflow.initialize()

        result = await workflow.run(
            user_query="Create a simple calculator app in Python with add, subtract, multiply, divide functions",
            session_id="test_create"
        )

        duration = (datetime.now() - start).total_seconds()

        # Verify results
        success = all([
            result.get("success") is not False,
            "agents_completed" in result,
            len(result.get("agents_completed", [])) >= 3,  # At least 3 agents
            result.get("files_generated", 0) > 0
        ])

        details = {
            "workflow_type": result.get("analysis", {}).get("classification", {}).get("workflow_type"),
            "agents_used": result.get("agents_completed", []),
            "files_generated": result.get("files_generated", 0),
            "quality_score": result.get("quality_score", 0),
            "execution_time": result.get("execution_time", 0)
        }

        if not success:
            details["errors"] = result.get("errors", [])[:3]  # First 3 errors

        results.add_test(test_name, success, duration, details)

        if success:
            logger.info(f"✅ CREATE workflow PASSED")
        else:
            logger.error(f"❌ CREATE workflow FAILED: {details.get('errors')}")

    except Exception as e:
        duration = (datetime.now() - start).total_seconds()
        logger.error(f"❌ CREATE workflow CRASHED: {e}", exc_info=True)
        results.add_test(test_name, False, duration, {"error": str(e)})


async def test_explain_workflow_german(results: TestResults):
    """
    Test 2: EXPLAIN workflow - German language.

    Expected: AI should recognize German "Untersuche" and plan research → explain workflow
    """
    test_name = "EXPLAIN Workflow - German Language"
    logger.info(f"\n{'='*60}")
    logger.info(f"🧪 Test 2: {test_name}")
    logger.info(f"{'='*60}")

    start = datetime.now()

    try:
        from workflow_v6_integrated import WorkflowV6Integrated

        # Use calculator app from previous test
        workspace = TEST_WORKSPACE / "calculator_app"
        if not workspace.exists():
            workspace.mkdir(parents=True)
            # Create dummy file for analysis
            (workspace / "main.py").write_text("def add(a, b): return a + b\n")

        workflow = WorkflowV6Integrated(workspace_path=str(workspace))
        await workflow.initialize()

        result = await workflow.run(
            user_query="Untersuche die App und erkläre mir die Architektur",
            session_id="test_explain"
        )

        duration = (datetime.now() - start).total_seconds()

        # Verify results
        agents_completed = result.get("agents_completed", [])
        success = all([
            result.get("success") is not False,
            "research" in agents_completed,  # Should use research
            "codesmith" not in agents_completed  # Should NOT generate code
        ])

        details = {
            "workflow_type": result.get("analysis", {}).get("classification", {}).get("workflow_type"),
            "agents_used": agents_completed,
            "german_recognized": "explain" in str(result).lower() or len(agents_completed) <= 2
        }

        results.add_test(test_name, success, duration, details)

        if success:
            logger.info(f"✅ EXPLAIN workflow (German) PASSED")
        else:
            logger.error(f"❌ EXPLAIN workflow (German) FAILED")

    except Exception as e:
        duration = (datetime.now() - start).total_seconds()
        logger.error(f"❌ EXPLAIN workflow CRASHED: {e}", exc_info=True)
        results.add_test(test_name, False, duration, {"error": str(e)})


async def test_fix_workflow(results: TestResults):
    """
    Test 3: FIX workflow - Fix existing code.

    Expected: AI should plan workflow with research → reviewfix (maybe skip architect/codesmith)
    """
    test_name = "FIX Workflow - Bug Fixing"
    logger.info(f"\n{'='*60}")
    logger.info(f"🧪 Test 3: {test_name}")
    logger.info(f"{'='*60}")

    start = datetime.now()

    try:
        from workflow_v6_integrated import WorkflowV6Integrated

        workspace = TEST_WORKSPACE / "buggy_app"
        workspace.mkdir(exist_ok=True)

        # Create buggy code
        (workspace / "buggy.py").write_text("""
def divide(a, b):
    return a / b  # Bug: No zero check!

print(divide(10, 0))  # Will crash
""")

        workflow = WorkflowV6Integrated(workspace_path=str(workspace))
        await workflow.initialize()

        result = await workflow.run(
            user_query="Fix the division by zero bug in buggy.py",
            session_id="test_fix"
        )

        duration = (datetime.now() - start).total_seconds()

        # Verify results
        agents_completed = result.get("agents_completed", [])
        success = all([
            result.get("success") is not False,
            "reviewfix" in agents_completed or "codesmith" in agents_completed,  # Should fix code
            result.get("files_generated", 0) > 0  # Should have modified files
        ])

        details = {
            "workflow_type": result.get("analysis", {}).get("classification", {}).get("workflow_type"),
            "agents_used": agents_completed,
            "files_modified": result.get("files_generated", 0)
        }

        results.add_test(test_name, success, duration, details)

        if success:
            logger.info(f"✅ FIX workflow PASSED")
        else:
            logger.error(f"❌ FIX workflow FAILED")

    except Exception as e:
        duration = (datetime.now() - start).total_seconds()
        logger.error(f"❌ FIX workflow CRASHED: {e}", exc_info=True)
        results.add_test(test_name, False, duration, {"error": str(e)})


async def test_refactor_workflow(results: TestResults):
    """
    Test 4: REFACTOR workflow - Code improvement.

    Expected: AI should plan workflow with architect → codesmith → reviewfix (maybe skip research)
    """
    test_name = "REFACTOR Workflow - Code Improvement"
    logger.info(f"\n{'='*60}")
    logger.info(f"🧪 Test 4: {test_name}")
    logger.info(f"{'='*60}")

    start = datetime.now()

    try:
        from workflow_v6_integrated import WorkflowV6Integrated

        workspace = TEST_WORKSPACE / "refactor_app"
        workspace.mkdir(exist_ok=True)

        # Create code to refactor
        (workspace / "messy.py").write_text("""
def calc(x, y, op):
    if op == 'add':
        return x + y
    elif op == 'sub':
        return x - y
    elif op == 'mul':
        return x * y
    elif op == 'div':
        return x / y
# Very messy, needs refactoring!
""")

        workflow = WorkflowV6Integrated(workspace_path=str(workspace))
        await workflow.initialize()

        result = await workflow.run(
            user_query="Refactor messy.py to use better design patterns and add type hints",
            session_id="test_refactor"
        )

        duration = (datetime.now() - start).total_seconds()

        # Verify results
        agents_completed = result.get("agents_completed", [])
        success = all([
            result.get("success") is not False,
            "architect" in agents_completed or "codesmith" in agents_completed,
            result.get("files_generated", 0) > 0
        ])

        details = {
            "workflow_type": result.get("analysis", {}).get("classification", {}).get("workflow_type"),
            "agents_used": agents_completed,
            "files_modified": result.get("files_generated", 0)
        }

        results.add_test(test_name, success, duration, details)

        if success:
            logger.info(f"✅ REFACTOR workflow PASSED")
        else:
            logger.error(f"❌ REFACTOR workflow FAILED")

    except Exception as e:
        duration = (datetime.now() - start).total_seconds()
        logger.error(f"❌ REFACTOR workflow CRASHED: {e}", exc_info=True)
        results.add_test(test_name, False, duration, {"error": str(e)})


async def test_workflow_planner_unit():
    """
    Test 5: Unit test for WorkflowPlanner.

    Tests the planner directly without full workflow execution.
    """
    test_name = "Workflow Planner Unit Test"
    logger.info(f"\n{'='*60}")
    logger.info(f"🧪 Test 5: {test_name}")
    logger.info(f"{'='*60}")

    results = TestResults()
    start = datetime.now()

    try:
        from cognitive.workflow_planner_v6 import WorkflowPlannerV6

        planner = WorkflowPlannerV6()

        # Test various tasks
        test_cases = [
            ("Create a task manager app", "CREATE"),
            ("Fix the authentication bug", "FIX"),
            ("Explain how the API works", "EXPLAIN"),
            ("Refactor the database code", "REFACTOR"),
            ("Untersuche die App", "EXPLAIN")  # German
        ]

        all_passed = True
        for task, expected_type in test_cases:
            logger.info(f"  Testing: '{task}' → Expected: {expected_type}")

            plan = await planner.plan_workflow(
                user_task=task,
                workspace_path=str(TEST_WORKSPACE)
            )

            # Validate plan
            is_valid, issues = await planner.validate_plan(plan)

            logger.info(f"    Planned: {plan.workflow_type} ({plan.complexity})")
            logger.info(f"    Agents: {[s.agent.value for s in plan.agents]}")
            logger.info(f"    Valid: {is_valid}")

            if not is_valid:
                logger.warning(f"    Issues: {issues}")

            # Check if matches expected type
            matches = expected_type.lower() in plan.workflow_type.lower()
            logger.info(f"    Match: {'✅' if matches else '❌'}")

            if not matches and not is_valid:
                all_passed = False

        duration = (datetime.now() - start).total_seconds()

        details = {
            "test_cases": len(test_cases),
            "all_valid": all_passed
        }

        results.add_test(test_name, all_passed, duration, details)

        if all_passed:
            logger.info(f"✅ Workflow Planner unit tests PASSED")
        else:
            logger.warning(f"⚠️  Some workflow plans had issues")

    except Exception as e:
        duration = (datetime.now() - start).total_seconds()
        logger.error(f"❌ Workflow Planner unit test CRASHED: {e}", exc_info=True)
        results.add_test(test_name, False, duration, {"error": str(e)})

    return results


def cleanup_test_workspace():
    """Cleanup test workspace."""
    logger.info(f"\n🧹 Cleaning up test workspace: {TEST_WORKSPACE}")

    try:
        if TEST_WORKSPACE.exists():
            shutil.rmtree(TEST_WORKSPACE)
        logger.info("✅ Cleanup complete")
    except Exception as e:
        logger.warning(f"⚠️  Cleanup failed: {e}")


async def main():
    """Run all E2E tests."""
    print("\n" + "=" * 80)
    print("🚀 STARTING WORKFLOW PLANNER E2E TESTS")
    print("=" * 80)

    # Setup
    setup_test_workspace()

    # Run tests
    results = TestResults()

    # Test 1: CREATE workflow
    await test_create_workflow(results)

    # Test 2: EXPLAIN workflow (German)
    await test_explain_workflow_german(results)

    # Test 3: FIX workflow
    await test_fix_workflow(results)

    # Test 4: REFACTOR workflow
    await test_refactor_workflow(results)

    # Test 5: Planner unit test
    planner_results = await test_workflow_planner_unit()
    results.tests.extend(planner_results.tests)

    # Report results
    all_passed = results.report()

    # Cleanup
    cleanup_test_workspace()

    # Exit code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())
