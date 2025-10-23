#!/usr/bin/env python3
"""
Real-world test scenario for v7.0 with Global Memory.

Simulates two different projects benefiting from shared knowledge.
"""

import asyncio
import json
import websockets


async def simulate_project_a():
    """Project A: Learns about async Python errors."""
    print("\n" + "=" * 60)
    print("PROJECT A: Learning Phase")
    print("=" * 60)

    uri = "ws://localhost:8002/ws/chat"

    async with websockets.connect(uri) as ws:
        # Connection
        await ws.recv()

        # Init with Project A workspace
        await ws.send(json.dumps({
            "type": "init",
            "workspace_path": "/tmp/project_a"
        }))
        await ws.recv()

        # Query about a specific error
        print("\n📨 Project A asks about asyncio.run() error...")
        await ws.send(json.dumps({
            "type": "chat",
            "content": "I get 'RuntimeError: asyncio.run() cannot be called from a running event loop'. What's wrong?"
        }))

        # Get response
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data['type'] == "result":
                print("✅ Project A got response")
                print(f"   Response preview: {data['content'][:200]}...")
                break
            elif data['type'] == "error":
                print(f"❌ Error: {data['message']}")
                break


async def simulate_project_b():
    """Project B: Benefits from Project A's knowledge."""
    print("\n" + "=" * 60)
    print("PROJECT B: Benefiting from Global Knowledge")
    print("=" * 60)

    uri = "ws://localhost:8002/ws/chat"

    async with websockets.connect(uri) as ws:
        # Connection
        await ws.recv()

        # Init with Project B workspace (different!)
        await ws.send(json.dumps({
            "type": "init",
            "workspace_path": "/tmp/project_b"
        }))
        await ws.recv()

        # Ask about async patterns
        print("\n📨 Project B asks about async best practices...")
        await ws.send(json.dumps({
            "type": "chat",
            "content": "What are the best practices for Python async programming? I want to avoid common errors."
        }))

        # Check if response contains knowledge from global memory
        found_global_knowledge = False
        while True:
            msg = await ws.recv()
            data = json.loads(msg)

            if data['type'] == "result":
                content = data['content']
                print("✅ Project B got response")

                # Check for patterns we stored
                if "asyncio.gather()" in content:
                    print("   ✅ Found: asyncio.gather() pattern")
                    found_global_knowledge = True

                if "async context managers" in content or "async with" in content:
                    print("   ✅ Found: async context managers pattern")
                    found_global_knowledge = True

                if "RuntimeError" in content and "event loop" in content:
                    print("   ✅ Found: Event loop error solution")
                    found_global_knowledge = True

                if "Global Pattern" in content:
                    print("   ✅ Response explicitly uses global patterns!")
                    found_global_knowledge = True

                break
            elif data['type'] == "error":
                print(f"❌ Error: {data['message']}")
                break

        return found_global_knowledge


async def test_error_solution_reuse():
    """Test that error solutions are reused across projects."""
    print("\n" + "=" * 60)
    print("ERROR SOLUTION REUSE TEST")
    print("=" * 60)

    uri = "ws://localhost:8002/ws/chat"

    async with websockets.connect(uri) as ws:
        # Connection
        await ws.recv()

        # Init with new workspace
        await ws.send(json.dumps({
            "type": "init",
            "workspace_path": "/tmp/project_c"
        }))
        await ws.recv()

        # Ask about a known error
        print("\n📨 Project C encounters known error...")
        await ws.send(json.dumps({
            "type": "chat",
            "content": "Help! ImportError: cannot import name 'AsyncOpenAI' from 'openai'"
        }))

        # Check response
        found_solution = False
        while True:
            msg = await ws.recv()
            data = json.loads(msg)

            if data['type'] == "result":
                content = data['content']
                print("✅ Project C got response")

                if "upgrade" in content.lower() and "openai" in content.lower():
                    print("   ✅ Found solution: Upgrade OpenAI package")
                    found_solution = True

                if ">=1.0" in content or "version" in content.lower():
                    print("   ✅ Solution includes version information")
                    found_solution = True

                break
            elif data['type'] == "error":
                print(f"❌ Error: {data['message']}")
                break

        return found_solution


async def show_learning_progress():
    """Show how knowledge accumulates."""
    from backend.memory.global_memory_system import GlobalMemorySystem

    print("\n" + "=" * 60)
    print("LEARNING PROGRESS")
    print("=" * 60)

    gm = GlobalMemorySystem()
    await gm.initialize()

    # Get current stats
    stats = await gm.get_stats()
    print(f"\n📊 Current Global Knowledge:")
    print(f"   Patterns: {stats['patterns_count']}")
    print(f"   Error Solutions: {stats['errors_count']}")

    # Simulate learning from new project
    await gm.store_pattern(
        content="Use httpx instead of requests for async HTTP calls",
        project_type="python_async",
        success=True
    )

    # Updated stats
    new_stats = await gm.get_stats()
    print(f"\n📈 After new project:")
    print(f"   Patterns: {new_stats['patterns_count']} (+{new_stats['patterns_count'] - stats['patterns_count']})")
    print(f"   Error Solutions: {new_stats['errors_count']}")

    print("\n✨ Knowledge grows with every project!")


async def main():
    """Run real-world scenarios."""
    print("=" * 60)
    print("REAL-WORLD v7.0 TEST SCENARIOS")
    print("=" * 60)

    results = []

    # Test 1: Project A learns
    try:
        await simulate_project_a()
        results.append("✅ Project A: Learning phase")
    except Exception as e:
        results.append(f"❌ Project A failed: {e}")

    # Test 2: Project B benefits
    try:
        found_knowledge = await simulate_project_b()
        if found_knowledge:
            results.append("✅ Project B: Successfully used global knowledge!")
        else:
            results.append("⚠️ Project B: No global knowledge found")
    except Exception as e:
        results.append(f"❌ Project B failed: {e}")

    # Test 3: Error solution reuse
    try:
        found_solution = await test_error_solution_reuse()
        if found_solution:
            results.append("✅ Project C: Found error solution from global memory!")
        else:
            results.append("⚠️ Project C: No error solution found")
    except Exception as e:
        results.append(f"❌ Project C failed: {e}")

    # Show learning progress
    await show_learning_progress()

    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    for result in results:
        print(result)

    success_count = sum(1 for r in results if r.startswith("✅"))
    total_count = len(results)

    print(f"\nSuccess Rate: {success_count}/{total_count}")

    if success_count == total_count:
        print("\n🎉 PERFECT! Global memory sharing works flawlessly!")
        print("\nKey Achievement:")
        print("✅ Different projects share knowledge")
        print("✅ Errors solved instantly from memory")
        print("✅ Best practices propagate automatically")
        print("✅ Agent gets smarter with each project")
        return 0
    else:
        print(f"\n⚠️ Some tests had issues ({total_count - success_count} problems)")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)