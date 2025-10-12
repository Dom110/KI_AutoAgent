#!/usr/bin/env python3
"""
Direct test to see if agents can actually write files
"""

import asyncio
import sys
import os
sys.path.append('backend')

async def test_direct_file_write():
    """Test if CodeSmithAgent can write files directly"""
    from agents.specialized.codesmith_agent import CodeSmithAgent

    print("=" * 60)
    print("🧪 Testing Direct File Writing Capability")
    print("=" * 60)

    try:
        # Create agent
        agent = CodeSmithAgent()
        print(f"✅ Agent created: {agent.name}")
        print(f"   Can write: {agent.can_write}")
        print(f"   Allowed paths: {agent.allowed_paths}")

        # Test direct file writing
        spec = """
        Create a simple Python function that:
        1. Takes two numbers as input
        2. Returns their sum
        3. Has a docstring
        """

        file_path = "backend/tests/test_output_sum.py"

        print(f"\n📝 Attempting to write to: {file_path}")
        result = await agent.implement_code_to_file(spec, file_path)

        print(f"\n📊 Result:")
        print(f"   Status: {result.get('status')}")
        print(f"   Error: {result.get('error', 'None')}")

        if result.get('status') == 'success':
            print(f"   File: {result.get('file')}")
            print(f"   Lines: {result.get('lines')}")
            print(f"\n✅ SUCCESS! File was written!")

            # Check if file actually exists
            if os.path.exists(file_path):
                print(f"✅ File exists at: {file_path}")
                with open(file_path, 'r') as f:
                    content = f.read()
                print(f"\n📄 File content ({len(content)} chars):")
                print("-" * 40)
                print(content[:500] if len(content) > 500 else content)
                print("-" * 40)

                # Clean up test file
                os.remove(file_path)
                print(f"🧹 Cleaned up test file")
            else:
                print(f"❌ File does NOT exist at: {file_path}")
        else:
            print(f"\n❌ FAILED! Agent could not write file")
            if 'traceback' in result:
                print(f"\n📋 Traceback:")
                print(result['traceback'])

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_file_write())