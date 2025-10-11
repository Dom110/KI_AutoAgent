#!/usr/bin/env python3
"""
Test Build Validation in ReviewFix

This script tests the new TypeScript compilation check feature
by running it against the generated app from the E2E test.

Author: KI AutoAgent Team
Date: 2025-10-11
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path.home() / ".ki_autoagent" / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from subgraphs.reviewfix_subgraph_v6_1 import create_reviewfix_subgraph
from state_v6 import ReviewFixState

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_build_validation():
    """Test build validation on generated app."""

    # Use the E2E test workspace
    workspace_path = str(Path.home() / "TestApps" / "e2e_test_20251011_220807")

    logger.info("=" * 80)
    logger.info("🧪 Testing Build Validation Feature")
    logger.info("=" * 80)
    logger.info(f"Workspace: {workspace_path}")

    # Check workspace exists
    if not os.path.exists(workspace_path):
        logger.error(f"❌ Workspace not found: {workspace_path}")
        return False

    # List all TypeScript files in workspace
    ts_files = []
    for root, dirs, files in os.walk(workspace_path):
        # Skip node_modules and hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
        for file in files:
            if file.endswith(('.ts', '.tsx')):
                rel_path = os.path.relpath(os.path.join(root, file), workspace_path)
                ts_files.append(rel_path)

    logger.info(f"\n📁 Found {len(ts_files)} TypeScript files:")
    for f in ts_files[:10]:
        logger.info(f"   - {f}")
    if len(ts_files) > 10:
        logger.info(f"   ... and {len(ts_files) - 10} more")

    # Create ReviewFix subgraph
    logger.info("\n🔧 Creating ReviewFix subgraph...")
    reviewfix_subgraph = create_reviewfix_subgraph(
        workspace_path=workspace_path,
        memory=None
    )

    # Create initial state
    logger.info("\n📊 Creating test state...")
    initial_state: ReviewFixState = {
        "files_to_review": ts_files,
        "quality_score": 0.0,
        "feedback": "",
        "iteration": 0,
        "fixes_applied": "",
        "fixed_files": [],
        "errors": []
    }

    # Run reviewer node
    logger.info("\n🚀 Running ReviewFix agent with build validation...")
    logger.info("-" * 80)

    try:
        result = await reviewfix_subgraph.ainvoke(initial_state)

        logger.info("\n" + "=" * 80)
        logger.info("📊 TEST RESULTS")
        logger.info("=" * 80)

        logger.info(f"✅ ReviewFix completed successfully")
        logger.info(f"   Quality Score: {result.get('quality_score', 0):.2f}")
        logger.info(f"   Iteration: {result.get('iteration', 0)}")
        logger.info(f"   Errors: {len(result.get('errors', []))}")

        # Check if feedback mentions TypeScript errors
        feedback = result.get('feedback', '')
        if 'TypeScript Compilation Errors' in feedback:
            logger.info(f"\n✅ Build validation DETECTED TypeScript errors (as expected)")
            logger.info(f"   Quality score should be capped at 0.50 due to build errors")

            # Count errors in feedback
            error_count = feedback.count('error TS')
            logger.info(f"   Found {error_count} TypeScript errors in feedback")

            return True
        elif 'TypeScript compilation passed' in feedback:
            logger.info(f"\n⚠️  Build validation PASSED - no errors found")
            logger.info(f"   This means the app compiles successfully!")
            return True
        else:
            logger.warning(f"\n⚠️  Build validation may not have run")
            logger.info(f"   Check logs above for 'Running TypeScript compilation check'")
            return False

    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logger.info("\n" + "=" * 80)
    logger.info("🧪 BUILD VALIDATION TEST")
    logger.info("=" * 80)

    success = asyncio.run(test_build_validation())

    logger.info("\n" + "=" * 80)
    if success:
        logger.info("✅ TEST PASSED - Build validation is working!")
    else:
        logger.info("❌ TEST FAILED - Check logs above")
    logger.info("=" * 80)

    sys.exit(0 if success else 1)
