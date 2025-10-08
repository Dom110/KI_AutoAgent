"""
Real API Test for Memory System

Tests with actual OpenAI API calls (requires API key).
"""

import asyncio
import os
import sys
import tempfile

# Load API keys from .env file
env_file = os.path.expanduser("~/.ki_autoagent/config/.env")
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
    print(f"✅ Loaded API keys from {env_file}")
else:
    print(f"⚠️  No .env file found at {env_file}")

sys.path.insert(0, 'backend')

from memory.memory_system_v6 import MemorySystem


async def test_memory_store_and_search():
    """Test memory store and search with real OpenAI embeddings."""
    print("\n" + "="*70)
    print("REAL API TEST: Memory Store + Search")
    print("="*70 + "\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        async with MemorySystem(tmpdir) as memory:
            # Test 1: Store
            print("1. Storing item with OpenAI embedding...")
            vector_id = await memory.store(
                content="Python is a programming language",
                metadata={"agent": "test", "type": "tech"}
            )
            print(f"   ✅ Stored with vector_id: {vector_id}")

            # Test 2: Count
            count = await memory.count()
            print(f"2. Count after store: {count}")
            assert count == 1, f"Expected 1, got {count}"
            print(f"   ✅ Count correct")

            # Test 3: Search (semantic similarity)
            print("3. Searching for 'coding language'...")
            results = await memory.search("coding language", k=1)
            print(f"   Found {len(results)} results")

            if results:
                result = results[0]
                print(f"   Content: {result['content']}")
                print(f"   Similarity: {result['similarity']:.3f}")
                print(f"   Metadata: {result['metadata']}")
                assert result['similarity'] > 0.3, f"Similarity too low: {result['similarity']}"
                print(f"   ✅ Semantic search working! (similarity: {result['similarity']:.3f})")
            else:
                print(f"   ❌ No results found!")
                return False

            # Test 4: Search with filters
            print("4. Searching with filters (agent='test')...")
            results = await memory.search(
                "programming",
                filters={"agent": "test"},
                k=1
            )
            print(f"   Found {len(results)} results")
            assert len(results) == 1
            print(f"   ✅ Filters working!")

            # Test 5: Stats
            stats = await memory.get_stats()
            print(f"5. Stats: {stats}")
            assert stats["total_items"] == 1
            assert stats["by_agent"]["test"] == 1
            print(f"   ✅ Stats correct!")

    print("\n" + "="*70)
    print("ALL TESTS PASSED! ✅")
    print("="*70 + "\n")
    return True


async def main():
    try:
        success = await test_memory_store_and_search()
        return success
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
