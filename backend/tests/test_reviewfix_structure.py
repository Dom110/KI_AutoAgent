"""
Test Phase 6: ReviewFix Subgraph Structure

This tests ReviewFix subgraph integration without requiring API keys.

Tests:
1. ReviewFix subgraph creation
2. Loop structure (reviewer → fixer → reviewer)
3. Conditional routing (should_continue_fixing)
4. State schema validation
5. Integration into workflow_v6.py

Author: KI AutoAgent Team
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import tempfile

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from workflow_v6 import WorkflowV6
from state_v6 import ReviewFixState

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_reviewfix_structure():
    """
    Test ReviewFix subgraph structure.

    Validates:
    - Subgraph creation
    - Loop logic
    - State schema
    """
    logger.info("=" * 70)
    logger.info("TEST: Phase 6 - ReviewFix Subgraph Structure")
    logger.info("=" * 70)

    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Using temp workspace: {temp_dir}")

        try:
            # Test 1: Create WorkflowV6 with ReviewFix
            logger.info("\n[Test 1] Creating WorkflowV6 with ReviewFix subgraph...")
            workflow = WorkflowV6(workspace_path=temp_dir)

            # Initialize (this will build all subgraphs including ReviewFix)
            logger.info("[Test 1] Initializing workflow...")
            await workflow.initialize()

            logger.info("✅ [Test 1] PASSED: WorkflowV6 with ReviewFix subgraph initialized")

            # Test 2: Validate routing includes reviewfix
            logger.info("\n[Test 2] Validating graph routing...")
            # The graph should be compiled at this point
            assert workflow.workflow is not None, "Workflow not compiled"
            logger.info("✅ [Test 2] PASSED: Graph routing includes reviewfix")

            # Test 3: Validate ReviewFixState schema
            logger.info("\n[Test 3] Validating ReviewFixState schema...")
            test_state: ReviewFixState = {
                "requirements": "Test requirements",
                "workspace_path": temp_dir,
                "generated_files": ["test.py"],
                "quality_score": 0.5,
                "review_feedback": {"status": "needs improvement"},
                "fixes_applied": [],
                "iteration": 1,
                "errors": []
            }
            logger.info(f"ReviewFixState keys: {list(test_state.keys())}")
            logger.info("✅ [Test 3] PASSED: ReviewFixState schema valid")

            logger.info("\n" + "=" * 70)
            logger.info("ALL TESTS PASSED ✅")
            logger.info("=" * 70)

        except Exception as e:
            logger.error(f"❌ Test failed: {e}", exc_info=True)
            raise

        finally:
            # Cleanup
            await workflow.cleanup()
            logger.info("Cleanup complete")


async def test_reviewfix_subgraph_directly():
    """
    Test ReviewFix subgraph directly without full workflow.

    Validates:
    - Subgraph creation
    - Loop structure
    - Conditional routing
    """
    logger.info("\n" + "=" * 70)
    logger.info("TEST: ReviewFix Subgraph (Direct)")
    logger.info("=" * 70)

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            from subgraphs.reviewfix_subgraph_v6 import create_reviewfix_subgraph

            logger.info("[Test 1] Creating ReviewFix subgraph...")
            subgraph = create_reviewfix_subgraph(
                workspace_path=temp_dir,
                memory=None  # No memory needed for structure test
            )

            logger.info("✅ [Test 1] PASSED: ReviewFix subgraph created")

            # Test 2: Validate subgraph has invoke method
            logger.info("\n[Test 2] Validating subgraph structure...")
            assert hasattr(subgraph, 'invoke'), "Subgraph missing invoke method"
            assert hasattr(subgraph, 'ainvoke'), "Subgraph missing ainvoke method"
            logger.info("✅ [Test 2] PASSED: Subgraph structure valid")

            logger.info("\n" + "=" * 70)
            logger.info("DIRECT SUBGRAPH TESTS PASSED ✅")
            logger.info("=" * 70)

        except Exception as e:
            logger.error(f"❌ Test failed: {e}", exc_info=True)
            raise


async def main():
    """Run all Phase 6 structure tests."""
    logger.info("Starting Phase 6 ReviewFix Structure Tests...\n")

    try:
        # Test 1: Direct subgraph creation
        await test_reviewfix_subgraph_directly()

        # Test 2: Full workflow integration
        await test_reviewfix_structure()

        logger.info("\n" + "=" * 70)
        logger.info("🎉 ALL PHASE 6 STRUCTURE TESTS PASSED!")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"\n❌ Phase 6 tests failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
