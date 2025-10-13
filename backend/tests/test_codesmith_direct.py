#!/usr/bin/env python3
"""
Direct Codesmith Test - Minimal reproduction to find the bug
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging - MORE verbose
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG level!
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("/tmp/codesmith_direct.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def test_codesmith_minimal():
    """
    Minimal test: Just run Codesmith node directly.

    This bypasses all the workflow machinery to isolate the bug.
    """
    logger.info("🧪 Starting minimal Codesmith test...")

    try:
        from subgraphs.codesmith_subgraph_v6_1 import create_codesmith_subgraph
        from state_v6 import CodesmithState

        workspace = Path.home() / "TestApps" / "codesmith_direct_test"
        workspace.mkdir(parents=True, exist_ok=True)

        logger.info(f"📁 Workspace: {workspace}")

        # Create minimal state
        state: CodesmithState = {
            "user_query": "Create a simple Python calculator with add/subtract",
            "design": "Simple calculator module with add() and subtract() functions",
            "workspace_path": str(workspace),
            "generated_files": [],
            "implementation_summary": "",
            "completed": False,
            "errors": []
        }

        logger.info("🔧 Creating Codesmith subgraph...")
        subgraph = create_codesmith_subgraph(
            workspace_path=str(workspace),
            memory=None,  # No memory for this test
            hitl_callback=None
        )

        logger.info("⚙️  Invoking Codesmith node...")
        logger.info("⏱️  This will call Claude CLI subprocess - may take 5-10 minutes")

        # This is where the bug happens!
        result = await subgraph.ainvoke(state)

        logger.info("✅ Codesmith completed!")
        logger.info(f"   Files generated: {len(result.get('generated_files', []))}")
        logger.info(f"   Completed: {result.get('completed', False)}")

        if result.get('errors'):
            logger.error(f"   Errors: {result['errors']}")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ Test FAILED: {e}", exc_info=True)
        return False


async def main():
    """Run the minimal test."""
    print("\n" + "=" * 80)
    print("🚀 MINIMAL CODESMITH TEST")
    print("=" * 80)
    print()
    print("This test runs ONLY the Codesmith node to isolate the bug.")
    print("Expected: Should take 5-10 minutes to generate code.")
    print()
    print("=" * 80 + "\n")

    success = await test_codesmith_minimal()

    print("\n" + "=" * 80)
    if success:
        print("✅ TEST PASSED - Codesmith works!")
    else:
        print("❌ TEST FAILED - Check /tmp/codesmith_direct.log")
    print("=" * 80 + "\n")

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
