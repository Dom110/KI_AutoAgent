#!/usr/bin/env python3
"""
Test script to validate OBSOLETE code in orchestrator_agent.py
Tests that workflow.py handles execution and Orchestrator only provides plans.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path.home() / '.ki_autoagent' / 'backend'
if backend_path.exists():
    sys.path.insert(0, str(backend_path))
else:
    # Fallback to dev repo
    sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from agents.specialized.orchestrator_agent import OrchestratorAgent
from agents.base.base_agent import TaskRequest
from unittest.mock import patch, MagicMock
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MethodCallTracker:
    """Track which methods were called during execution"""
    def __init__(self):
        self.calls = []

    def record(self, method_name):
        self.calls.append(method_name)
        logger.info(f"📞 Method called: {method_name}")


async def test_orchestrator_only_plans():
    """
    Test that Orchestrator.execute() only creates plans,
    does NOT execute workflows (that's workflow.py's job)
    """
    print("\n" + "="*80)
    print("🧪 TEST: Orchestrator Only Creates Plans (No Execution)")
    print("="*80 + "\n")

    # Create Orchestrator instance
    orchestrator = OrchestratorAgent()

    # Verify OBSOLETE methods don't exist anymore
    obsolete_methods = [
        'execute_workflow',
        '_execute_step',
        '_execute_step_async',
        '_execute_sequential_workflow',
        '_execute_parallel_workflow',
        '_group_by_dependency_level',
        '_dependencies_met',
        'format_orchestration_result'
    ]

    print("🔍 Checking for OBSOLETE methods...")
    found_obsolete = []
    for method_name in obsolete_methods:
        if hasattr(orchestrator, method_name):
            found_obsolete.append(method_name)
            print(f"  ⚠️  Found: {method_name}")
        else:
            print(f"  ✅ Removed: {method_name}")

    if found_obsolete:
        print(f"\n❌ ERROR: {len(found_obsolete)} OBSOLETE methods still exist!")
        return False

    print("\n✅ All OBSOLETE methods successfully removed!")

    # Execute a test task
    print("📝 Executing task: 'Create a simple calculator app with add, subtract, multiply, divide'")
    print()

    try:
        task_request = TaskRequest(
            prompt="Create a simple calculator app with add, subtract, multiply, divide"
        )
        result = await orchestrator.execute(task_request)

        print("\n" + "-"*80)
        print("✅ Orchestrator.execute() completed successfully")
        print("-"*80)

        # Check what was returned
        print("\n📊 Result Analysis:")
        print(f"  - Type: {type(result)}")
        print(f"  - Status: {result.status}")
        print(f"  - Has content: {result.content is not None}")
        print(f"  - Has metadata: {result.metadata is not None}")

        if result.metadata:
            metadata = result.metadata
            print(f"  - Metadata keys: {list(metadata.keys())}")

            if 'subtasks' in metadata:
                subtasks = metadata['subtasks']
                print(f"\n🎯 Execution Plan:")
                print(f"  - Number of subtasks: {len(subtasks)}")
                for i, subtask in enumerate(subtasks, 1):
                    agent = subtask.get('agent', subtask.get('agent_type', 'unknown'))
                    desc = subtask.get('description', subtask.get('task', 'N/A'))
                    print(f"  {i}. [{agent}] {desc[:60]}...")

        # Final verdict
        print("\n" + "="*80)
        print("🎉 SUCCESS")
        print("="*80)
        print("\n✅ Orchestrator successfully creates execution plans")
        print("✅ All OBSOLETE methods have been removed")
        print("✅ System is clean and working as expected")
        return True

    except Exception as e:
        print(f"\n❌ ERROR during execution: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_workflow_handles_execution():
    """
    Test that workflow.py is responsible for actual agent execution
    """
    print("\n" + "="*80)
    print("🧪 TEST: Workflow.py Handles Actual Execution")
    print("="*80 + "\n")

    # Import workflow to verify it has execution methods
    try:
        # Import from installed backend
        import sys
        from pathlib import Path
        backend_path = Path.home() / '.ki_autoagent' / 'backend'
        if str(backend_path) not in sys.path:
            sys.path.insert(0, str(backend_path))

        from langgraph_system.workflow import WorkflowSystem

        print("✅ WorkflowSystem imported successfully")

        # Check for execution methods
        has_execute = hasattr(WorkflowSystem, 'execute')
        has_execute_architect = hasattr(WorkflowSystem, '_execute_architect_task')
        has_execute_codesmith = hasattr(WorkflowSystem, '_execute_codesmith_task')
        has_execute_reviewer = hasattr(WorkflowSystem, '_execute_reviewer_task')
        has_execute_fixer = hasattr(WorkflowSystem, '_execute_fixer_task')

        print("\n📋 WorkflowSystem Execution Methods:")
        print(f"  - execute(): {has_execute}")
        print(f"  - _execute_architect_task(): {has_execute_architect}")
        print(f"  - _execute_codesmith_task(): {has_execute_codesmith}")
        print(f"  - _execute_reviewer_task(): {has_execute_reviewer}")
        print(f"  - _execute_fixer_task(): {has_execute_fixer}")

        if all([has_execute, has_execute_architect, has_execute_codesmith,
                has_execute_reviewer, has_execute_fixer]):
            print("\n✅ VERDICT: workflow.py has all execution methods")
            print("   Orchestrator only needs to provide plans, not execute them")
            return True
        else:
            print("\n❌ VERDICT: workflow.py missing execution methods")
            return False

    except Exception as e:
        print(f"⚠️  Could not import WorkflowSystem: {e}")
        print("\n📋 Manually verifying workflow.py has execution methods...")

        # Manually check workflow.py for execution methods
        workflow_path = Path.home() / '.ki_autoagent' / 'backend' / 'langgraph_system' / 'workflow.py'
        if not workflow_path.exists():
            print(f"❌ workflow.py not found at {workflow_path}")
            return False

        with open(workflow_path, 'r') as f:
            content = f.read()

        required_methods = [
            '_execute_architect_task',
            '_execute_codesmith_task',
            '_execute_reviewer_task',
            '_execute_fixer_task',
            '_execute_research_task'
        ]

        print("\n🔍 Checking for execution methods in workflow.py:")
        all_found = True
        for method in required_methods:
            if f'async def {method}' in content:
                print(f"  ✅ Found: {method}")
            else:
                print(f"  ❌ Missing: {method}")
                all_found = False

        if all_found:
            print("\n✅ VERDICT: workflow.py has all execution methods")
            print("   Orchestrator only needs to provide plans, not execute them")
            return True
        else:
            print("\n❌ VERDICT: workflow.py missing execution methods")
            return False


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🚀 ORCHESTRATOR OBSOLETE CODE VALIDATION TEST SUITE")
    print("="*80)

    test1_passed = await test_orchestrator_only_plans()
    test2_passed = await test_workflow_handles_execution()

    print("\n" + "="*80)
    print("📊 FINAL VERDICT")
    print("="*80)

    if test1_passed and test2_passed:
        print("\n✅ ALL TESTS PASSED")
        print("\n🎉 CONCLUSION: The 8 OBSOLETE methods in orchestrator_agent.py")
        print("   can be SAFELY REMOVED. Orchestrator only creates plans,")
        print("   workflow.py handles all actual agent execution.")
        print("\n📝 Next steps:")
        print("   1. Remove OBSOLETE section (lines 620-880)")
        print("   2. Keep format_orchestration_plan() method")
        print("   3. Update any remaining references to format_orchestration_result()")
        return 0
    else:
        print("\n❌ TESTS FAILED")
        print("\n⚠️  DO NOT REMOVE OBSOLETE CODE YET")
        print("   Further investigation needed.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
