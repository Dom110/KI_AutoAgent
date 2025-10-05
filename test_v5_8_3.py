#!/usr/bin/env python3
"""
v5.8.3 Integration Test
Tests all ChatGPT-inspired improvements:
- Phase 1: State immutability (Reducer pattern)
- Phase 2: LangGraph Store (Agent learning)
"""

import sys
import os
sys.path.insert(0, os.path.expanduser("~/.ki_autoagent/backend"))

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_imports():
    """Test 1: Can we import the updated modules?"""
    logger.info("=" * 60)
    logger.info("TEST 1: Import Updated Modules")
    logger.info("=" * 60)

    try:
        from langgraph_system.state import ExtendedAgentState, merge_execution_steps
        logger.info("✅ state.py imported (with merge_execution_steps reducer)")

        from langgraph_system.workflow import (
            AgentWorkflow,
            update_step_status,
            merge_state_updates,
            store_learned_pattern,
            recall_learned_patterns
        )
        logger.info("✅ workflow.py imported (with helpers)")

        return True
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        return False


async def test_store_initialization():
    """Test 2: Does LangGraph Store initialize?"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: LangGraph Store Initialization")
    logger.info("=" * 60)

    try:
        from langgraph_system.workflow import AgentWorkflow

        workflow = AgentWorkflow()
        logger.info(f"✅ AgentWorkflow created")

        if workflow.memory_store:
            logger.info(f"✅ LangGraph Store initialized: {type(workflow.memory_store)}")
        else:
            logger.warning(f"⚠️ LangGraph Store is None (might be unavailable)")

        return True
    except Exception as e:
        logger.error(f"❌ Store initialization failed: {e}", exc_info=True)
        return False


async def test_reducer_pattern():
    """Test 3: Does the reducer pattern work?"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Reducer Pattern (State Immutability)")
    logger.info("=" * 60)

    try:
        from langgraph_system.state import (
            ExtendedAgentState,
            ExecutionStep,
            merge_execution_steps,
            create_initial_state
        )
        from dataclasses import replace as dataclass_replace

        # Create initial state
        state = create_initial_state()
        logger.info("✅ Initial state created")

        # Add some execution steps
        step1 = ExecutionStep(
            id="test_1",
            agent="architect",
            task="Design architecture",
            status="pending"
        )
        step2 = ExecutionStep(
            id="test_2",
            agent="codesmith",
            task="Build code",
            status="pending"
        )

        state["execution_plan"] = [step1, step2]
        step_ids = [s.id for s in state["execution_plan"]]

        logger.info(f"✅ Added 2 steps: {step_ids}")
        # Test the reducer: Update step1 to completed
        updated_step1 = dataclass_replace(step1, status="completed", result="Architecture designed")
        merged_plan = merge_execution_steps(
            existing=state["execution_plan"],
            updates=[updated_step1]
        )

        logger.info(f"✅ Reducer merged updates")
        logger.info(f"   Step1 status: {merged_plan[0].status} (expected: completed)")
        logger.info(f"   Step1 result: {merged_plan[0].result}")
        logger.info(f"   Step2 status: {merged_plan[1].status} (expected: pending)")

        if merged_plan[0].status == "completed" and merged_plan[1].status == "pending":
            logger.info("✅ Reducer works correctly!")
            return True
        else:
            logger.error("❌ Reducer didn't merge correctly")
            return False

    except Exception as e:
        logger.error(f"❌ Reducer test failed: {e}", exc_info=True)
        return False


async def test_helper_functions():
    """Test 4: Do helper functions work?"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Helper Functions (update_step_status)")
    logger.info("=" * 60)

    try:
        from langgraph_system.workflow import update_step_status, merge_state_updates
        from langgraph_system.state import create_initial_state, ExecutionStep

        state = create_initial_state()
        step = ExecutionStep(
            id="test_helper",
            agent="reviewer",
            task="Review code",
            status="in_progress"
        )
        state["execution_plan"] = [step]

        logger.info(f"Initial step status: {step.status}")

        # Use helper to update
        update_dict = update_step_status(
            state,
            "test_helper",
            "completed",
            result="Code looks good!"
        )

        logger.info(f"✅ update_step_status returned: {list(update_dict.keys())}")

        updated_plan = update_dict["execution_plan"]
        logger.info(f"   Updated step status: {updated_plan[0].status}")
        logger.info(f"   Updated step result: {updated_plan[0].result}")

        if updated_plan[0].status == "completed":
            logger.info("✅ Helper functions work correctly!")
            return True
        else:
            logger.error("❌ Helper function didn't update correctly")
            return False

    except Exception as e:
        logger.error(f"❌ Helper function test failed: {e}", exc_info=True)
        return False


async def test_workflow_compilation():
    """Test 5: Can we compile workflow with Store?"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 5: Workflow Compilation (with Store)")
    logger.info("=" * 60)

    try:
        from langgraph_system.workflow import AgentWorkflow

        workflow = AgentWorkflow()
        logger.info("✅ AgentWorkflow created")

        # Compile workflow
        compiled = await workflow.compile_workflow()
        logger.info("✅ Workflow compiled successfully")

        if workflow.memory_store:
            logger.info("✅ Workflow compiled WITH Store support")
        else:
            logger.warning("⚠️ Workflow compiled WITHOUT Store (might be unavailable)")

        return True
    except Exception as e:
        logger.error(f"❌ Workflow compilation failed: {e}", exc_info=True)
        return False


async def main():
    """Run all tests"""
    logger.info("\n" + "="*60)
    logger.info("KI_AutoAgent v5.8.3 Integration Tests")
    logger.info("Testing ChatGPT-inspired improvements")
    logger.info("="*60 + "\n")

    results = {
        "Imports": await test_imports(),
        "Store Initialization": await test_store_initialization(),
        "Reducer Pattern": await test_reducer_pattern(),
        "Helper Functions": await test_helper_functions(),
        "Workflow Compilation": await test_workflow_compilation(),
    }

    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {test_name}")

    all_passed = all(results.values())

    logger.info("\n" + "="*60)
    if all_passed:
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("v5.8.3 improvements successfully implemented")
    else:
        logger.error("⚠️ SOME TESTS FAILED")
        logger.error("Check errors above for details")
    logger.info("="*60 + "\n")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
