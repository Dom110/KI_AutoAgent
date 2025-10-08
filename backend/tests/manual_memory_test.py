"""
Manual Memory System Test (ohne OpenAI API Key)

Testet:
- FAISS Index Creation
- SQLite Database Creation
- Basic Structure
"""

import asyncio
import sys
import tempfile

sys.path.insert(0, 'backend')

from memory.memory_system_v6 import MemorySystem


async def test_memory_init():
    """Test memory system initialization ohne API calls."""
    print("=" * 70)
    print("TEST 1: Memory System Initialization")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Workspace: {tmpdir}")

        # Create memory system
        memory = MemorySystem(workspace_path=tmpdir)

        # Initialize
        await memory.initialize()

        # Check components
        print(f"✅ FAISS index created: {memory.index is not None}")
        print(f"✅ FAISS dimension: {memory.index.ntotal if memory.index else 'N/A'} vectors")
        print(f"✅ SQLite connection: {memory.db_conn is not None}")
        print(f"✅ OpenAI client: {memory.openai_client is not None}")

        # Check database schema
        cursor = await memory.db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = await cursor.fetchall()
        print(f"✅ Database tables: {[t[0] for t in tables]}")

        # Cleanup
        await memory.close()
        print("✅ Cleanup successful")

    print("\n" + "=" * 70)
    print("TEST 1: PASSED ✅")
    print("=" * 70 + "\n")


async def test_memory_count():
    """Test memory count on empty database."""
    print("=" * 70)
    print("TEST 2: Memory Count (Empty)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        async with MemorySystem(tmpdir) as memory:
            count = await memory.count()
            print(f"✅ Empty count: {count}")
            assert count == 0, f"Expected 0, got {count}"

    print("\n" + "=" * 70)
    print("TEST 2: PASSED ✅")
    print("=" * 70 + "\n")


async def test_memory_stats():
    """Test memory statistics on empty database."""
    print("=" * 70)
    print("TEST 3: Memory Stats (Empty)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        async with MemorySystem(tmpdir) as memory:
            stats = await memory.get_stats()
            print(f"✅ Stats: {stats}")
            assert stats["total_items"] == 0
            assert stats["by_agent"] == {}
            assert stats["by_type"] == {}

    print("\n" + "=" * 70)
    print("TEST 3: PASSED ✅")
    print("=" * 70 + "\n")


async def main():
    """Run all tests."""
    print("\n" + "🧪 " * 35)
    print("MEMORY SYSTEM MANUAL TESTS (No OpenAI API)")
    print("🧪 " * 35 + "\n")

    try:
        await test_memory_init()
        await test_memory_count()
        await test_memory_stats()

        print("\n" + "🎉 " * 35)
        print("ALL TESTS PASSED!")
        print("🎉 " * 35 + "\n")

        print("Note: Tests that require OpenAI API (store, search) skipped.")
        print("      Those need real API key or mocking.")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
