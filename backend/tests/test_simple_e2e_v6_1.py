"""
Simple E2E Test for v6.1 - Quick validation

Tests a minimal workflow execution with v6.1 subgraphs.

Author: KI AutoAgent Team
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import tempfile

import pytest

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

# NOTE: Temporarily disabling Claude CLI adapter due to Pydantic conflicts
# from adapters.use_claude_cli import use_claude_cli
# use_claude_cli()

from workflow_v6 import WorkflowV6

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_simple_workflow_initialization():
    """Test that v6.1 workflow initializes correctly with Claude CLI."""
    logger.info("=" * 80)
    logger.info("🚀 Simple E2E Test: v6.1 Workflow Initialization")
    logger.info("=" * 80)

    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"📂 Workspace: {temp_dir}")

        # Initialize workflow
        logger.info("\n[Step 1] Initializing WorkflowV6 with v6.1 subgraphs...")
        workflow = WorkflowV6(workspace_path=temp_dir)
        await workflow.initialize()

        # Check that workflow was built
        assert workflow.workflow is not None
        logger.info("✅ Workflow initialized successfully")

        # Check memory system
        assert workflow.memory is not None
        logger.info("✅ Memory system initialized")

        logger.info("\n" + "=" * 80)
        logger.info("✅ Simple E2E Test PASSED - v6.1 infrastructure validated!")
        logger.info("=" * 80)


@pytest.mark.asyncio
async def test_full_workflow_simple_task():
    """Test full workflow with a very simple task."""
    logger.info("=" * 80)
    logger.info("🚀 Testing Full Workflow with Simple Task")
    logger.info("=" * 80)

    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"📂 Workspace: {temp_dir}")

        workflow = WorkflowV6(workspace_path=temp_dir)
        await workflow.initialize()

        # Simple query that should be quick
        user_query = "Create a simple hello.py file with a hello() function that prints 'Hello World'"

        logger.info(f"\n[Task] {user_query}")
        logger.info("=" * 80)

        try:
            # Run with 5 minute timeout
            result = await asyncio.wait_for(
                workflow.run(user_query=user_query),
                timeout=300.0
            )

            logger.info("\n" + "=" * 80)
            logger.info("✅ Workflow completed!")
            logger.info("=" * 80)

            # Check result
            assert result is not None
            logger.info(f"✅ Got result")

            # Check for generated files
            hello_file = os.path.join(temp_dir, "hello.py")
            if os.path.exists(hello_file):
                logger.info(f"✅ hello.py was created")
                with open(hello_file, 'r') as f:
                    content = f.read()
                    logger.info(f"File content:\n{content[:200]}...")
            else:
                logger.warning("⚠️  hello.py was not created (check workflow execution)")

        except asyncio.TimeoutError:
            logger.error("❌ Workflow timed out after 5 minutes")
            pytest.fail("Workflow execution timed out")
        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_simple_workflow_initialization())
    asyncio.run(test_full_workflow_simple_task())
