#!/usr/bin/env python3
"""
MCPManager Direct Test
Tests MCPManager functionality without full server
"""

import asyncio
import sys
from pathlib import Path


async def test_mcp_manager():
    """Test MCPManager directly."""
    
    print("\n" + "="*100)
    print("🧪 MCP MANAGER DIRECT TEST")
    print("="*100)
    
    sys.path.insert(0, str(Path(__file__).parent))
    
    from backend.utils.mcp_manager import get_mcp_manager
    
    workspace_path = "/tmp/test_mcp_workspace"
    
    # Test 1: Get MCPManager
    print("\n[TEST 1] Getting MCPManager instance...")
    try:
        mcp = get_mcp_manager(workspace_path=workspace_path)
        print(f"✅ MCPManager obtained")
        print(f"   Workspace: {workspace_path}")
        print(f"   Servers registry: {mcp.servers if hasattr(mcp, 'servers') else 'Unknown'}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Test 2: Initialize MCP
    print("\n[TEST 2] Initializing MCPManager...")
    try:
        await mcp.initialize()
        print(f"✅ MCPManager initialized")
        print(f"   Active processes: {len(mcp.processes) if hasattr(mcp, 'processes') else 'Unknown'}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Check server status
    print("\n[TEST 3] Checking server status...")
    try:
        if hasattr(mcp, 'processes'):
            print(f"   Total processes: {len(mcp.processes)}")
            for server_name, proc in mcp.processes.items():
                status = "✅ RUNNING" if proc else "❌ DEAD"
                print(f"      {server_name}: {status}")
        else:
            print("   Cannot check processes (not available)")
    except Exception as e:
        print(f"⚠️  Could not check status: {e}")
    
    # Test 4: List available tools
    print("\n[TEST 4] Listing available tools from responder...")
    try:
        if hasattr(mcp, 'get_available_tools'):
            tools = await mcp.get_available_tools("responder_agent")
            print(f"✅ Tools available: {tools}")
        else:
            print("   get_available_tools not available")
    except Exception as e:
        print(f"⚠️  Could not list tools: {e}")
    
    # Test 5: Try responder.format_response (no AI needed)
    print("\n[TEST 5] Testing responder tool (no AI)...")
    try:
        result = await asyncio.wait_for(
            mcp.call(
                server="responder_agent",
                tool="format_response",
                arguments={
                    "user_query": "Test",
                    "context": {},
                    "workspace_path": workspace_path
                }
            ),
            timeout=5.0
        )
        print(f"✅ Tool call successful")
        print(f"   Result type: {type(result)}")
        print(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        
    except asyncio.TimeoutError:
        print(f"❌ Tool call TIMEOUT after 5 seconds")
        print(f"   This suggests responder_agent is blocked or not responding")
        
    except Exception as e:
        print(f"❌ Tool call FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 6: Shutdown
    print("\n[TEST 6] Shutdown MCPManager...")
    try:
        if hasattr(mcp, 'shutdown'):
            await mcp.shutdown()
            print(f"✅ MCPManager shutdown complete")
        else:
            print("   shutdown method not available")
    except Exception as e:
        print(f"⚠️  Shutdown error: {e}")
    
    print("\n" + "="*100)
    print("✅ MCP MANAGER TEST COMPLETE")
    print("="*100)
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_mcp_manager())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
