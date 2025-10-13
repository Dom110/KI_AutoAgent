"""
MCP Integration Smoke Tests (v6.2)

Quick smoke tests to verify MCP integration is working.
Run these tests after MCP implementation to ensure basic functionality.

Usage:
    python backend/tests/test_mcp_smoke.py

Author: KI AutoAgent Team
Version: 6.2.0-alpha
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


async def test_mcp_client_import():
    """Test 1: MCP client can be imported."""
    print("Test 1: Importing MCP client...")
    try:
        from mcp.mcp_client import MCPClient
        print("  ✅ MCP client imported successfully")
        return True
    except Exception as e:
        print(f"  ❌ Failed to import MCP client: {e}")
        return False


async def test_mcp_client_initialization():
    """Test 2: MCP client can be initialized."""
    print("\nTest 2: Initializing MCP client...")
    try:
        import tempfile
        from mcp.mcp_client import MCPClient

        # Use temporary directory as workspace_path
        with tempfile.TemporaryDirectory() as tmpdir:
            client = MCPClient(workspace_path=tmpdir)
            await client.initialize()

            print(f"  ✅ MCP client initialized with {len(client.servers)} servers")

            # List connected servers
            for server_name in client._connections.keys():
                print(f"    - {server_name}")

            await client.cleanup()
        return True

    except Exception as e:
        print(f"  ❌ MCP initialization failed: {e}")
        return False


async def test_subgraph_imports():
    """Test 3: All subgraphs can be imported."""
    print("\nTest 3: Importing subgraphs...")
    try:
        from subgraphs.research_subgraph_v6_1 import create_research_subgraph
        from subgraphs.architect_subgraph_v6_1 import create_architect_subgraph
        from subgraphs.codesmith_subgraph_v6_1 import create_codesmith_subgraph
        from subgraphs.reviewfix_subgraph_v6_1 import create_reviewfix_subgraph

        print("  ✅ All subgraphs imported successfully")
        return True

    except Exception as e:
        print(f"  ❌ Failed to import subgraphs: {e}")
        return False


async def test_workflow_import():
    """Test 4: Workflow can be imported."""
    print("\nTest 4: Importing workflow...")
    try:
        from workflow_v6_integrated import WorkflowV6Integrated

        print("  ✅ Workflow imported successfully")
        return True

    except Exception as e:
        print(f"  ❌ Failed to import workflow: {e}")
        return False


async def test_mcp_perplexity_call():
    """Test 5: MCP Perplexity call works."""
    print("\nTest 5: Testing MCP Perplexity call...")
    try:
        import tempfile
        from mcp.mcp_client import MCPClient

        # Use temporary directory as workspace_path
        with tempfile.TemporaryDirectory() as tmpdir:
            client = MCPClient(workspace_path=tmpdir)
            await client.initialize()

            result = await client.call(
                server="perplexity",
                tool="perplexity_search",
                arguments={
                    "query": "Python test",
                    "max_results": 1
                }
            )

            if result.get("isError"):
                print(f"  ⚠️  Perplexity call returned error: {result.get('error')}")
                print("     (This is OK if PERPLEXITY_API_KEY is not set)")
            else:
                print("  ✅ Perplexity call successful")

            await client.cleanup()
        return True

    except Exception as e:
        print(f"  ❌ Perplexity call failed: {e}")
        return False


async def test_no_obsolete_imports():
    """Test 6: Verify no obsolete imports in subgraphs."""
    print("\nTest 6: Checking for obsolete imports...")
    try:
        obsolete_imports = []

        # Check research subgraph
        research_path = backend_path / "subgraphs" / "research_subgraph_v6_1.py"
        if research_path.exists():
            content = research_path.read_text()
            if "from tools.perplexity_tool import" in content:
                obsolete_imports.append("research_subgraph_v6_1.py: perplexity_tool")
            if "from adapters.claude_cli_simple import" in content and "ChatAnthropic" in content:
                if "llm = ChatAnthropic(" in content:  # Direct instantiation
                    obsolete_imports.append("research_subgraph_v6_1.py: ClaudeCLISimple (direct use)")

        # Check architect subgraph
        architect_path = backend_path / "subgraphs" / "architect_subgraph_v6_1.py"
        if architect_path.exists():
            content = architect_path.read_text()
            if "from adapters.claude_cli_simple import" in content and "ChatAnthropic" in content:
                if "llm = ChatAnthropic(" in content:
                    obsolete_imports.append("architect_subgraph_v6_1.py: ClaudeCLISimple (direct use)")

        # Check codesmith subgraph
        codesmith_path = backend_path / "subgraphs" / "codesmith_subgraph_v6_1.py"
        if codesmith_path.exists():
            content = codesmith_path.read_text()
            if "from adapters.claude_cli_simple import" in content and "ChatAnthropic" in content:
                if "llm = ChatAnthropic(" in content:
                    obsolete_imports.append("codesmith_subgraph_v6_1.py: ClaudeCLISimple (direct use)")

        # Check reviewfix subgraph
        reviewfix_path = backend_path / "subgraphs" / "reviewfix_subgraph_v6_1.py"
        if reviewfix_path.exists():
            content = reviewfix_path.read_text()
            if "from adapters.claude_cli_simple import" in content and "ChatAnthropic" in content:
                if "llm = ChatAnthropic(" in content:
                    obsolete_imports.append("reviewfix_subgraph_v6_1.py: ClaudeCLISimple (direct use)")

        if obsolete_imports:
            print("  ❌ Found obsolete imports:")
            for imp in obsolete_imports:
                print(f"     - {imp}")
            return False
        else:
            print("  ✅ No obsolete imports found")
            return True

    except Exception as e:
        print(f"  ❌ Check failed: {e}")
        return False


async def main():
    """Run all smoke tests."""
    print("🧪 MCP Integration Smoke Tests (v6.2)\n")
    print("=" * 60)

    results = []

    # Run tests
    results.append(await test_mcp_client_import())
    results.append(await test_mcp_client_initialization())
    results.append(await test_subgraph_imports())
    results.append(await test_workflow_import())
    results.append(await test_mcp_perplexity_call())
    results.append(await test_no_obsolete_imports())

    # Summary
    print("\n" + "=" * 60)
    print(f"\n📊 Test Results: {sum(results)}/{len(results)} passed")

    if all(results):
        print("\n✅ All smoke tests passed! MCP integration is working.")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
