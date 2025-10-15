"""
Debug: Workflow Initialization

Find out EXACTLY where Test 1 hangs.
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import logging
import time

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

TEST_WORKSPACE = Path.home() / "TestApps" / "e2e_v6.3_test"


async def debug_init():
    """Debug workflow initialization step by step."""

    logger.info("=" * 80)
    logger.info("STEP 1: Import WorkflowV6Integrated")
    logger.info("=" * 80)

    start = time.time()
    from workflow_v6_integrated import WorkflowV6Integrated
    logger.info(f"✅ Import took {time.time() - start:.2f}s")

    logger.info("")
    logger.info("=" * 80)
    logger.info("STEP 2: Create WorkflowV6Integrated instance")
    logger.info("=" * 80)

    start = time.time()
    workflow = WorkflowV6Integrated(
        workspace_path=str(TEST_WORKSPACE),
        websocket_callback=None
    )
    logger.info(f"✅ Constructor took {time.time() - start:.2f}s")

    logger.info("")
    logger.info("=" * 80)
    logger.info("STEP 3: Initialize workflow")
    logger.info("=" * 80)
    logger.info("This is where it likely hangs...")

    start = time.time()

    # Set a timeout for initialization
    try:
        await asyncio.wait_for(workflow.initialize(), timeout=30.0)
        logger.info(f"✅ Initialize took {time.time() - start:.2f}s")
    except asyncio.TimeoutError:
        logger.error(f"❌ TIMEOUT after 30s!")
        logger.error(f"   Workflow was still initializing after {time.time() - start:.2f}s")
        logger.error("")
        logger.error("🔍 This means workflow.initialize() is HANGING!")
        return False
    except Exception as e:
        logger.error(f"❌ FAILED with exception: {e}")
        logger.error("", exc_info=True)
        return False

    logger.info("")
    logger.info("=" * 80)
    logger.info("STEP 4: Cleanup")
    logger.info("=" * 80)

    start = time.time()
    await workflow.cleanup()
    logger.info(f"✅ Cleanup took {time.time() - start:.2f}s")

    logger.info("")
    logger.info("🎉 SUCCESS - Workflow can initialize!")
    return True


if __name__ == "__main__":
    print("\n" + "="*80)
    print("Debug: Workflow Initialization")
    print("="*80 + "\n")

    success = asyncio.run(debug_init())

    sys.exit(0 if success else 1)
