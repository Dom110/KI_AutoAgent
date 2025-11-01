"""Test MCPManager initialization and basic functionality"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.utils.mcp_manager import get_mcp_manager, close_mcp_manager

async def test_initialization():
    print("🧪 Test 1: MCPManager Initialization")

    mcp = get_mcp_manager(workspace_path="/tmp/test_workspace")

    try:
        await mcp.initialize()
        print("✅ MCPManager initialized successfully")

        # Check connected servers
        connected_count = 0
        for server in mcp.servers:
            if server in mcp._processes:
                print(f"✅ Server '{server}' connected")
                connected_count += 1
            else:
                print(f"❌ Server '{server}' NOT connected")

        print(f"📊 {connected_count}/{len(mcp.servers)} servers connected")
        return connected_count == len(mcp.servers)
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await close_mcp_manager()

async def test_singleton():
    print("\n🧪 Test 2: Singleton Pattern")

    # Reset global instance for testing
    import backend.utils.mcp_manager as mcp_mod
    mcp_mod._global_mcp_manager = None

    mcp1 = get_mcp_manager(workspace_path="/tmp/test1")
    mcp2 = get_mcp_manager(workspace_path="/tmp/test2")

    if mcp1 is mcp2:
        print("✅ Singleton pattern works (same instance returned)")
        return True
    else:
        print("❌ Singleton pattern broken (different instances)")
        return False

async def main():
    print("=" * 60)
    print("⚠️ MCP BLEIBT: Testing Pure MCP Architecture")
    print("=" * 60)

    results = []

    results.append(await test_singleton())
    results.append(await test_initialization())

    print("\n" + "=" * 60)
    print(f"📊 Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)

    return all(results)

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
