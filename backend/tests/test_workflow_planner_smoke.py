#!/usr/bin/env python3
"""
Smoke Test for Workflow Planner Integration
============================================

Quick smoke test to verify the workflow planner integration works
without running full E2E workflows.

Tests:
1. WorkflowPlannerV6 can be imported and initialized
2. Plan validation works
3. Workflow can be initialized with planner
4. Graph structure is correct

Author: KI AutoAgent Team
Date: 2025-10-12
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test 1: Can we import everything?"""
    print("🧪 Test 1: Importing modules...")

    try:
        from cognitive.workflow_planner_v6 import (
            WorkflowPlannerV6,
            WorkflowPlan,
            AgentType,
            AgentStep,
            ConditionType
        )
        print("  ✅ workflow_planner_v6 imported")

        from workflow_v6_integrated import WorkflowV6Integrated
        print("  ✅ WorkflowV6Integrated imported")

        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False


async def test_planner_init():
    """Test 2: Can we initialize the planner?"""
    print("\n🧪 Test 2: Initializing WorkflowPlanner...")

    try:
        from cognitive.workflow_planner_v6 import WorkflowPlannerV6

        planner = WorkflowPlannerV6()
        print("  ✅ WorkflowPlannerV6 initialized")

        # Check agent capabilities
        print(f"  ℹ️  Agent capabilities: {len(planner.agent_capabilities)} agents")

        return True
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_fallback_plan():
    """Test 3: Can we get a fallback plan?"""
    print("\n🧪 Test 3: Getting fallback plan...")

    try:
        from cognitive.workflow_planner_v6 import WorkflowPlannerV6

        planner = WorkflowPlannerV6()
        plan = planner._get_fallback_plan("Test task")

        print(f"  ✅ Fallback plan created")
        print(f"     Type: {plan.workflow_type}")
        print(f"     Agents: {[s.agent.value for s in plan.agents]}")
        print(f"     Complexity: {plan.complexity}")

        # Validate plan
        is_valid, issues = await planner.validate_plan(plan)
        print(f"  ✅ Plan validation: {is_valid}")

        if issues:
            print(f"     Issues: {issues}")

        return is_valid
    except Exception as e:
        print(f"  ❌ Fallback plan failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_workflow_init():
    """Test 4: Can we initialize WorkflowV6Integrated with planner?"""
    print("\n🧪 Test 4: Initializing WorkflowV6Integrated...")

    try:
        from workflow_v6_integrated import WorkflowV6Integrated

        workspace = Path("/tmp/test_workspace_smoke")
        workspace.mkdir(exist_ok=True)

        workflow = WorkflowV6Integrated(workspace_path=str(workspace))
        print("  ✅ WorkflowV6Integrated created")

        # Initialize (this will init planner)
        await workflow.initialize()
        print("  ✅ Workflow initialized")

        # Check if planner was initialized
        if workflow.workflow_planner is not None:
            print("  ✅ Workflow planner is initialized")
        else:
            print("  ❌ Workflow planner is None!")
            return False

        # Check workflow structure
        if workflow.workflow is not None:
            print("  ✅ Workflow graph is compiled")
        else:
            print("  ❌ Workflow graph is None!")
            return False

        return True
    except Exception as e:
        print(f"  ❌ Workflow initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_summary(results):
    """Print test summary."""
    total = len(results)
    passed = sum(results.values())
    failed = total - passed

    print("\n" + "=" * 60)
    print("📊 SMOKE TEST RESULTS")
    print("=" * 60)
    print(f"Total: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print("=" * 60)

    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name}: {status}")

    print("=" * 60)

    if failed == 0:
        print("🎉 ALL SMOKE TESTS PASSED!")
        print("✅ Workflow Planner integration is working correctly.")
        return True
    else:
        print("⚠️  SOME SMOKE TESTS FAILED!")
        print("❌ There are integration issues that need to be fixed.")
        return False


async def main():
    """Run all smoke tests."""
    print("🚀 WORKFLOW PLANNER SMOKE TESTS")
    print("=" * 60)

    results = {}

    # Test 1: Imports
    results["Imports"] = test_imports()

    # Test 2: Planner init
    results["Planner Init"] = await test_planner_init()

    # Test 3: Fallback plan
    results["Fallback Plan"] = await test_fallback_plan()

    # Test 4: Workflow init
    results["Workflow Init"] = await test_workflow_init()

    # Summary
    all_passed = print_summary(results)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
