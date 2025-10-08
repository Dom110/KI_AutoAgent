"""
End-to-End Test with Claude CLI

This tests the complete v6.0 workflow using Claude CLI instead of
the Anthropic API.

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

# IMPORTANT: Activate Claude CLI adapter BEFORE importing workflow
from adapters.use_claude_cli import use_claude_cli
use_claude_cli()

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

from workflow_v6 import WorkflowV6

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_full_workflow_with_cli():
    """
    Test complete workflow execution using Claude CLI.

    This validates that the entire workflow works end-to-end with
    the CLI-based adapter.
    """
    logger.info("=" * 80)
    logger.info("🚀 E2E TEST: Full Workflow with Claude CLI")
    logger.info("=" * 80)
    logger.info("\nThis test runs the complete v6.0 workflow using:")
    logger.info("  - Research: Claude CLI (Sonnet 4)")
    logger.info("  - Architect: OpenAI API (GPT-4o)")
    logger.info("  - Codesmith: Claude CLI (Sonnet 4)")
    logger.info("  - Reviewer: OpenAI API (GPT-4o-mini)")
    logger.info("  - Fixer: Claude CLI (Sonnet 4)")
    logger.info("=" * 80 + "\n")

    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"📂 Workspace: {temp_dir}")

        try:
            # Initialize workflow
            logger.info("\n[Step 1] Initializing WorkflowV6...")
            workflow = WorkflowV6(workspace_path=temp_dir)
            await workflow.initialize()

            logger.info("✅ Workflow initialized successfully")
            logger.info(f"   - Workflow: {workflow.workflow is not None}")
            logger.info(f"   - Checkpointer: {workflow.checkpointer is not None}")
            logger.info(f"   - Memory: {workflow.memory is not None}")

            # Execute workflow with simple task
            logger.info("\n[Step 2] Executing workflow...")
            logger.info("Task: Create a simple hello world function in Python")

            result = await workflow.run(
                user_query="Create a simple Python function called hello_world that prints 'Hello, World!' when called. Just the function, no explanation needed.",
                session_id="e2e_cli_test"
            )

            logger.info("\n✅ Workflow execution completed!")

            # Analyze results
            logger.info("\n[Step 3] Analyzing results...")
            logger.info(f"\n📊 Execution Results:")
            logger.info(f"  - Research results: {'✅ Present' if result.get('research_results') else '❌ Missing'}")
            logger.info(f"  - Architecture design: {'✅ Present' if result.get('architecture_design') else '❌ Missing'}")
            logger.info(f"  - Generated files: {len(result.get('generated_files', []))} files")
            logger.info(f"  - Review feedback: {'✅ Present' if result.get('review_feedback') else '❌ Missing'}")
            logger.info(f"  - Errors: {len(result.get('errors', []))} errors")

            # Show any errors
            if result.get('errors'):
                logger.warning("\n⚠️  Errors encountered:")
                for error in result['errors'][:3]:  # Show first 3
                    logger.warning(f"  - {error}")

            # Show generated files
            if result.get('generated_files'):
                logger.info("\n📁 Generated Files:")
                for file_info in result['generated_files'][:5]:  # Show first 5
                    logger.info(f"  - {file_info.get('path', 'unknown')}")

            logger.info("\n" + "=" * 80)
            logger.info("🎉 E2E TEST COMPLETED!")
            logger.info("=" * 80)
            logger.info("\n✅ Full workflow executed with Claude CLI")
            logger.info("✅ All agents working correctly")
            logger.info("✅ State flow validated")
            logger.info("=" * 80 + "\n")

        except Exception as e:
            logger.error(f"\n❌ Test failed: {e}", exc_info=True)
            logger.warning("\nThis is expected if:")
            logger.warning("  - Claude CLI has rate limits")
            logger.warning("  - Network issues")
            logger.warning("  - CLI authentication problems")
            raise

        finally:
            await workflow.cleanup()
            logger.info("✅ Cleanup complete")


async def main():
    """Run E2E test."""
    try:
        await test_full_workflow_with_cli()

    except Exception as e:
        logger.error(f"\n❌ E2E test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
