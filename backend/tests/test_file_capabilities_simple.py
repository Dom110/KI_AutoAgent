#!/usr/bin/env python3
"""
Simple test for agent file capabilities (no pytest required)
"""

import asyncio
import os
import shutil
import sys
import tempfile

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.tools.file_tools import FileSystemTools
from config.capabilities_loader import get_capabilities_loader


async def test_file_tools():
    """Test basic file tools functionality"""
    print("\n🧪 Testing FileSystemTools...")

    # Create temp workspace
    temp_dir = tempfile.mkdtemp()
    print(f"   Created temp workspace: {temp_dir}")

    try:
        tools = FileSystemTools(temp_dir)

        # Test 1: Write a file
        print("   Testing file write...")
        result = await tools.write_file(
            path="test.py",
            content="print('Hello from test')",
            agent_name="TestAgent",
            allowed_paths=["*.py"],
        )

        if result["status"] == "success":
            print(f"   ✅ File written successfully to {result['path']}")
            # Verify file exists
            file_path = os.path.join(temp_dir, "test.py")
            if os.path.exists(file_path):
                print(f"   ✅ File exists at {file_path}")
                with open(file_path) as f:
                    content = f.read()
                print(f"   ✅ Content verified: {len(content)} bytes")
            else:
                print(f"   ❌ File not found at {file_path}")
        else:
            print(f"   ❌ Write failed: {result['error']}")

        # Test 2: Permission check
        print("\n   Testing permission check...")
        result = await tools.write_file(
            path="test.txt",
            content="Should fail",
            agent_name="TestAgent",
            allowed_paths=["*.py"],  # Only .py files allowed
        )

        if result["status"] == "error":
            print(f"   ✅ Permission correctly denied: {result['error']}")
        else:
            print("   ❌ Permission check failed - file was written!")

        # Test 3: Audit log
        print("\n   Testing audit log...")
        audit_log = tools.get_audit_log()
        print(f"   ✅ Audit log has {len(audit_log)} entries")
        for entry in audit_log:
            print(
                f"      - {entry['agent_name']}: {entry['operation']} {entry['file_path']} - {'✅' if entry['success'] else '❌'}"
            )

    finally:
        # Clean up
        shutil.rmtree(temp_dir)
        print("\n   Cleaned up temp workspace")


async def test_capabilities_loader():
    """Test capabilities loader"""
    print("\n🧪 Testing Capabilities Loader...")

    loader = get_capabilities_loader()

    # Test loading capabilities
    agents_to_test = [
        ("CodeSmithClaude", True),
        ("ArchitectAgent", True),
        ("ReviewerGPT", False),
        ("ResearchBot", False),
    ]

    for agent_name, should_write in agents_to_test:
        caps = loader.get_agent_capabilities(agent_name)
        can_write = caps.get("file_write", False)
        print(
            f"   {agent_name}: write={'✅' if can_write else '❌'} (expected: {'✅' if should_write else '❌'})"
        )

        if can_write != should_write:
            print(f"   ❌ Capability mismatch for {agent_name}!")

    # Test path checking
    print("\n   Testing path permissions...")
    tests = [
        ("CodeSmithClaude", "backend/test.py", True),
        ("CodeSmithClaude", "frontend/test.js", False),
        ("ArchitectAgent", "redis.config", True),
        ("ReviewerGPT", "any_file.py", False),
    ]

    for agent, path, expected in tests:
        can_write = loader.can_agent_write(agent, path)
        result = "✅" if can_write == expected else "❌"
        print(f"   {result} {agent} + {path} = {'allowed' if can_write else 'denied'}")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Agent File Capabilities Test Suite")
    print("=" * 60)

    try:
        await test_file_tools()
        await test_capabilities_loader()

        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
