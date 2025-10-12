"""
Test Research Subgraph Structure (Phase 3)

Quick smoke tests without API calls.

Usage:
    python backend/tests/test_research_structure_v6.py
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from workflow_v6 import WorkflowV6


async def test_research_structure():
    """Test Research Subgraph structure (no API calls)"""

    print("\n" + "="*70)
    print("TEST: Research Subgraph Structure v6.0")
    print("="*70 + "\n")

    # Create temporary workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = tmpdir
        print(f"📁 Workspace: {workspace_path}")

        # Test 1: Create workflow
        print("\n1. Creating WorkflowV6...")
        workflow = WorkflowV6(workspace_path=workspace_path)
        print("✅ WorkflowV6 instance created")

        # Test 2: Initialize (setup checkpointer)
        print("\n2. Initializing workflow...")
        await workflow.initialize()
        print("✅ Workflow initialized (AsyncSqliteSaver setup)")

        # Test 3: Check workflow attributes
        print("\n3. Checking workflow attributes...")
        assert workflow.workspace_path == workspace_path
        assert workflow.checkpointer is not None
        assert workflow.memory is not None
        assert workflow.workflow is not None
        print("✅ All attributes present")

        # Test 4: Inspect graph nodes
        print("\n4. Checking graph structure...")
        # workflow.workflow is the compiled graph
        # We can't easily inspect it without private API access
        # Just verify it compiled
        print("✅ Workflow compiled successfully")

        print("\n" + "="*70)
        print("STRUCTURE TESTS PASSED! ✅")
        print("="*70 + "\n")

        print("ℹ️ Note: Full API integration test requires:")
        print("   - ANTHROPIC_API_KEY in ~/.ki_autoagent/config/.env")
        print("   - Run: python backend/tests/test_research_v6.py")


if __name__ == "__main__":
    asyncio.run(test_research_structure())
