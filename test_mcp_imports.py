"""Test that MCP files can be imported without errors"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    print("=" * 60)
    print("🧪 Testing MCP Import Integrity")
    print("=" * 60)

    tests_passed = 0
    tests_total = 0

    # Test 1: Import MCPManager
    tests_total += 1
    try:
        from backend.utils.mcp_manager import get_mcp_manager, close_mcp_manager
        print("✅ backend.utils.mcp_manager imports successfully")
        tests_passed += 1
    except Exception as e:
        print(f"❌ backend.utils.mcp_manager import failed: {e}")

    # Test 2: Import supervisor_mcp
    tests_total += 1
    try:
        from backend.core.supervisor_mcp import SupervisorMCP
        print("✅ backend.core.supervisor_mcp imports successfully")
        tests_passed += 1
    except Exception as e:
        print(f"❌ backend.core.supervisor_mcp import failed: {e}")

    # Test 3: Import workflow_v7_mcp
    tests_total += 1
    try:
        from backend.workflow_v7_mcp import (
            execute_supervisor_workflow_streaming_mcp,
            build_supervisor_workflow_mcp
        )
        print("✅ backend.workflow_v7_mcp imports successfully")
        tests_passed += 1
    except Exception as e:
        print(f"❌ backend.workflow_v7_mcp import failed: {e}")

    # Test 4: Import server_v7_mcp
    tests_total += 1
    try:
        # Don't actually import (would start FastAPI), just check file exists
        server_path = Path(__file__).parent / "backend" / "api" / "server_v7_mcp.py"
        if server_path.exists():
            print("✅ backend.api.server_v7_mcp exists")
            tests_passed += 1
        else:
            print("❌ backend.api.server_v7_mcp not found")
    except Exception as e:
        print(f"❌ backend.api.server_v7_mcp check failed: {e}")

    # Test 5: Check MCP servers exist
    tests_total += 1
    mcp_servers_dir = Path(__file__).parent / "mcp_servers"
    expected_servers = [
        "openai_server.py",
        "research_agent_server.py",
        "architect_agent_server.py",
        "codesmith_agent_server.py",
        "reviewfix_agent_server.py",
        "responder_agent_server.py"
    ]

    all_exist = True
    for server in expected_servers:
        server_path = mcp_servers_dir / server
        if not server_path.exists():
            print(f"❌ MCP server missing: {server}")
            all_exist = False

    if all_exist:
        print(f"✅ All {len(expected_servers)} MCP servers exist")
        tests_passed += 1
    else:
        print(f"❌ Some MCP servers are missing")

    # Test 6: Verify old files are deleted
    tests_total += 1
    old_files = [
        "backend/agents/architect_agent.py",
        "backend/agents/codesmith_agent.py",
        "backend/agents/research_agent.py",
        "backend/agents/responder_agent.py",
        "backend/agents/reviewfix_agent.py",
        "backend/utils/ai_factory.py",
        "backend/utils/claude_cli_service.py",
        "backend/workflow_v7_supervisor.py",
        "backend/api/server_v7_supervisor.py"
    ]

    old_files_exist = []
    for old_file in old_files:
        old_path = Path(__file__).parent / old_file
        if old_path.exists():
            old_files_exist.append(old_file)

    if not old_files_exist:
        print("✅ All old files have been deleted")
        tests_passed += 1
    else:
        print(f"❌ Old files still exist: {old_files_exist}")

    print("\n" + "=" * 60)
    print(f"📊 Results: {tests_passed}/{tests_total} tests passed")
    print("=" * 60)

    return tests_passed == tests_total

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
