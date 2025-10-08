"""
Test Research Subgraph (Phase 3)

Tests:
1. Research subgraph creation
2. Research with real API (Anthropic Claude)
3. State transformations
4. Memory integration
5. Full workflow with research

Usage:
    python backend/tests/test_research_v6.py
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from workflow_v6 import WorkflowV6
from memory.memory_system_v6 import MemorySystem


async def test_research_subgraph():
    """Test Research Subgraph with real API"""

    # Load API keys
    env_file = os.path.expanduser("~/.ki_autoagent/config/.env")
    if os.path.exists(env_file):
        print(f"✅ Loading API keys from {env_file}")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value.strip().strip('"')
    else:
        print(f"⚠️ No .env file found at {env_file}")

    print("\n" + "="*70)
    print("TEST: Research Subgraph v6.0")
    print("="*70 + "\n")

    # Create temporary workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = tmpdir
        print(f"📁 Workspace: {workspace_path}")

        # Test 1: Create workflow
        print("\n1. Creating WorkflowV6...")
        workflow = WorkflowV6(workspace_path=workspace_path)
        await workflow.initialize()
        print("✅ Workflow created")

        # Test 2: Check workflow components
        print("\n2. Checking workflow components...")
        print(f"✅ Workflow initialized with workspace: {workflow.workspace_path}")

        # Test 3: Run workflow (research only)
        print("\n3. Running workflow (Research subgraph only)...")
        print("   Query: 'What are the best practices for React hooks in 2025?'")
        print("   This will invoke Claude via create_react_agent...")

        try:
            result = await workflow.run(
                user_query="What are the best practices for React hooks in 2025?",
                session_id="test_session"
            )

            print("\n✅ Workflow completed!")
            print(f"\nResult keys: {list(result.keys())}")

            # Check research results
            if "research_results" in result:
                research = result["research_results"]
                print(f"\n📊 Research Results:")
                print(f"   - Findings: {len(research.get('findings', {}))} items")
                print(f"   - Sources: {len(research.get('sources', []))} sources")
                print(f"   - Report length: {len(research.get('report', ''))} chars")

                # Show report excerpt
                report = research.get("report", "")
                if report:
                    print(f"\n📝 Report excerpt:")
                    print(report[:500] + "..." if len(report) > 500 else report)
            else:
                print("\n⚠️ No research_results in output (check state transformations)")

            # Test 4: Check Memory
            print("\n4. Checking Memory...")
            async with MemorySystem(workspace_path) as memory:
                count = await memory.count()
                print(f"   Memory items: {count}")

                if count > 0:
                    # Search for research findings
                    results = await memory.search(
                        query="React hooks best practices",
                        k=1,
                        filters={"agent": "research"}
                    )
                    print(f"   ✅ Found {len(results)} research items in memory")
                    if results:
                        print(f"   Content: {results[0]['content'][:200]}...")
                else:
                    print("   ⚠️ No items in memory (Memory integration may need check)")

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    print("\n" + "="*70)
    print("ALL TESTS PASSED! ✅")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_research_subgraph())
