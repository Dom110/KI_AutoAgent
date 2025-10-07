#!/usr/bin/env python3
"""
Integration test to verify agents can actually write files
Tests the full chain: Request → Agent → File Write
"""

import asyncio
import os
import shutil
import sys
import tempfile

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.specialized.architect_agent import ArchitectAgent
from agents.specialized.codesmith_agent import CodeSmithAgent


async def test_architect_creates_redis_config():
    """Test that ArchitectAgent can actually create a Redis config file"""
    print("\n🧪 Testing ArchitectAgent Redis Config Creation...")

    # Create temp workspace
    temp_dir = tempfile.mkdtemp()
    print(f"   Working in: {temp_dir}")

    try:
        # Create and configure agent
        agent = ArchitectAgent()

        # Override workspace path AND allowed paths for testing
        if agent.file_tools:
            agent.file_tools.workspace_path = temp_dir
            # Allow writing to temp dir for testing
            agent.allowed_paths = [f"{temp_dir}/**"]
            agent.can_write = True

        # Try to create Redis config
        result = await agent.create_redis_config(
            {"maxmemory": "2gb", "policy": "volatile-lru"}
        )

        print(f"   Result: {result.get('status')}")

        if result["status"] == "success":
            # Check if file was created
            config_path = os.path.join(temp_dir, "redis.config")
            if os.path.exists(config_path):
                print(f"   ✅ File created at: {config_path}")

                # Verify content
                with open(config_path) as f:
                    content = f.read()
                if "maxmemory 2gb" in content:
                    print("   ✅ Configuration correctly written")
                else:
                    print("   ❌ Configuration content incorrect")
            else:
                print(f"   ❌ File not found at {config_path}")
        else:
            print(f"   ❌ Agent error: {result.get('error')}")

    finally:
        shutil.rmtree(temp_dir)
        print("   Cleaned up temp workspace")


async def test_codesmith_writes_code():
    """Test that CodeSmithAgent can write Python code"""
    print("\n🧪 Testing CodeSmithAgent Code Writing...")

    # Create temp workspace
    temp_dir = tempfile.mkdtemp()
    print(f"   Working in: {temp_dir}")

    try:
        # Create and configure agent
        agent = CodeSmithAgent()

        # Override workspace path AND allowed paths for testing
        if agent.file_tools:
            agent.file_tools.workspace_path = temp_dir
            # Allow writing to temp dir for testing
            agent.allowed_paths = [f"{temp_dir}/**"]
            agent.can_write = True

        # Try to implement code
        result = await agent.implement_code_to_file(
            spec="Create a function that returns 'Hello World'", file_path="hello.py"
        )

        print(f"   Result: {result.get('status')}")

        if result["status"] == "success":
            # Check if file was created
            code_path = os.path.join(temp_dir, "hello.py")
            if os.path.exists(code_path):
                print(f"   ✅ File created at: {code_path}")

                # Verify content
                with open(code_path) as f:
                    content = f.read()
                if "def" in content or "return" in content:
                    print(f"   ✅ Code generated ({len(content)} bytes)")
                    print(f"   Preview: {content[:100]}...")
                else:
                    print("   ❌ Code content looks wrong")
            else:
                print(f"   ❌ File not found at {code_path}")
        else:
            print(f"   ❌ Agent error: {result.get('error')}")

    finally:
        shutil.rmtree(temp_dir)
        print("   Cleaned up temp workspace")


async def test_agent_via_api():
    """Test agent file write via API endpoint"""
    print("\n🧪 Testing Agent File Write via API...")

    import aiohttp

    async with aiohttp.ClientSession() as session:
        # Test if backend is running
        try:
            async with session.get("http://localhost:8000/agents") as resp:
                agents = await resp.json()
                print(f"   ✅ Backend running with {len(agents)} agents")

        except Exception as e:
            print(f"   ❌ Backend not accessible: {e}")
            return

        # Send a request to create Redis config via WebSocket
        # (This would normally be done via the WebSocket interface)
        print("   Note: Full WebSocket test requires frontend integration")


async def main():
    """Run all integration tests"""
    print("=" * 60)
    print("🚀 Agent File Write Integration Tests")
    print("=" * 60)

    try:
        await test_architect_creates_redis_config()
        await test_codesmith_writes_code()
        await test_agent_via_api()

        print("\n" + "=" * 60)
        print("✅ Integration tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
