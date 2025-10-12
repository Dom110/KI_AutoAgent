#!/usr/bin/env python3
"""
Test Memory Manager v6.2

Tests all Memory Manager features:
- Store (short_term, long_term, working)
- Search with priority scoring
- Working memory LRU eviction
- Context window management
- Legacy compatibility

Run:
    cd /Users/dominikfoert/git/KI_AutoAgent/backend
    ./venv_v6/bin/python tests/test_memory_manager_v6_2.py

Author: KI AutoAgent Team
Version: 6.2.0 (Phase 4.1)
"""

import asyncio
import logging
import os
import shutil
import sys
import tempfile
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import MemoryManager
from core.memory_manager import get_memory_manager, MemoryType


async def test_initialization():
    """Test MemoryManager initialization."""
    print("\n" + "="*80)
    print("TEST 1: Initialization")
    print("="*80)

    # Create temporary workspace
    workspace = tempfile.mkdtemp(prefix="test_memory_")
    print(f"📂 Test workspace: {workspace}")

    # Get singleton instance
    manager = get_memory_manager()
    assert manager is not None

    # Initialize
    await manager.initialize(workspace)
    print("✅ MemoryManager initialized successfully")

    # Check stats
    stats = await manager.get_stats()
    print(f"📊 Initial stats: {stats}")

    return manager, workspace


async def test_store_and_search():
    """Test store and search with priority scoring."""
    print("\n" + "="*80)
    print("TEST 2: Store and Search")
    print("="*80)

    manager, workspace = await test_initialization()

    # Store memories with different importance levels
    print("\n📝 Storing memories...")

    # Important memory (should rank high)
    await manager.store(
        content="Vite + React 18 recommended for 2025 frontend development",
        memory_type=MemoryType.LONG_TERM,
        importance=0.9,
        metadata={"agent": "research", "type": "technology"}
    )
    print("✅ Stored high-importance memory (0.9)")

    # Medium importance
    await manager.store(
        content="FastAPI is a modern Python web framework",
        memory_type=MemoryType.LONG_TERM,
        importance=0.6,
        metadata={"agent": "research", "type": "technology"}
    )
    print("✅ Stored medium-importance memory (0.6)")

    # Low importance
    await manager.store(
        content="User asked about weather API",
        memory_type=MemoryType.SHORT_TERM,
        importance=0.3,
        metadata={"agent": "supervisor", "type": "task"}
    )
    print("✅ Stored low-importance memory (0.3)")

    # Search for frontend frameworks
    print("\n🔍 Searching for 'frontend frameworks'...")
    results = await manager.search(
        query="frontend frameworks",
        k=5
    )

    print(f"\n📊 Search Results ({len(results)} found):")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Priority: {result['priority_score']:.3f}")
        print(f"   Similarity: {result.get('similarity', 0):.3f}")
        print(f"   Importance: {result.get('metadata', {}).get('importance', 0):.3f}")
        print(f"   Content: {result['content'][:60]}...")

    # Cleanup
    shutil.rmtree(workspace)
    print("\n✅ Test passed: Store and Search")


async def test_working_memory_lru():
    """Test working memory LRU eviction."""
    print("\n" + "="*80)
    print("TEST 3: Working Memory LRU Eviction")
    print("="*80)

    manager, workspace = await test_initialization()

    # Store more than MAX_WORKING_MEMORY (20) items
    print(f"\n📝 Storing 25 items in working memory (max: {manager.MAX_WORKING_MEMORY})...")

    for i in range(25):
        importance = 0.5 if i < 20 else 0.8  # Last 5 are important
        await manager.store(
            content=f"Working memory item {i}",
            memory_type=MemoryType.WORKING,
            importance=importance,
            metadata={"agent": "test", "type": "working"}
        )

    # Check working memory size
    stats = await manager.get_stats()
    working_count = stats["working_memory_count"]

    print(f"\n📊 Working memory count: {working_count}")
    print(f"   Expected: {manager.MAX_WORKING_MEMORY}")

    assert working_count == manager.MAX_WORKING_MEMORY, \
        f"Expected {manager.MAX_WORKING_MEMORY}, got {working_count}"

    # Check if important items were promoted to long-term
    storage_stats = stats["storage_stats"]
    total_items = storage_stats.get("total_items", 0)
    print(f"   Promoted to long-term: {total_items} items")

    # Cleanup
    shutil.rmtree(workspace)
    print("\n✅ Test passed: Working Memory LRU")


async def test_context_window_management():
    """Test context window management."""
    print("\n" + "="*80)
    print("TEST 4: Context Window Management")
    print("="*80)

    manager, workspace = await test_initialization()

    # Store multiple memories
    print("\n📝 Storing 10 memories for architect...")

    for i in range(10):
        await manager.store(
            content=f"Architecture decision {i}: " + ("x" * 200),  # 200 chars each
            memory_type=MemoryType.LONG_TERM,
            importance=0.5 + (i * 0.05),  # Increasing importance
            metadata={"agent": "architect", "type": "design"}
        )

    # Get context with token limit
    print("\n🔍 Getting context for architect (max 500 tokens)...")

    context = await manager.get_context_for_agent(
        agent_id="architect",
        max_tokens=500
    )

    print(f"\n📊 Context:")
    print(f"   Memories: {len(context['memories'])}")
    print(f"   Total tokens: {context['total_tokens']}")
    print(f"   Truncated: {context['truncated']}")

    assert context["total_tokens"] <= 500, \
        f"Token limit exceeded: {context['total_tokens']} > 500"

    # Cleanup
    shutil.rmtree(workspace)
    print("\n✅ Test passed: Context Window Management")


async def test_priority_scoring():
    """Test priority score calculation."""
    print("\n" + "="*80)
    print("TEST 5: Priority Score Calculation")
    print("="*80)

    manager, workspace = await test_initialization()

    # Store memories with different characteristics
    print("\n📝 Storing memories with different characteristics...")

    # Recent + important + relevant
    await manager.store(
        content="React 18 concurrent rendering features",
        memory_type=MemoryType.LONG_TERM,
        importance=0.9,
        metadata={"agent": "research", "type": "technology"}
    )

    # Old but important
    await asyncio.sleep(0.1)  # Simulate time passing
    await manager.store(
        content="Vue 3 composition API",
        memory_type=MemoryType.LONG_TERM,
        importance=0.9,
        metadata={"agent": "research", "type": "technology"}
    )

    # Recent but less important
    await manager.store(
        content="Angular signals API",
        memory_type=MemoryType.LONG_TERM,
        importance=0.5,
        metadata={"agent": "research", "type": "technology"}
    )

    # Search
    print("\n🔍 Searching for 'React'...")
    results = await manager.search(
        query="React rendering",
        k=3
    )

    print(f"\n📊 Priority Scores:")
    for i, result in enumerate(results, 1):
        priority = result["priority_score"]
        importance = result.get("metadata", {}).get("importance", 0)
        similarity = result.get("similarity", 0)

        print(f"\n{i}. {result['content'][:40]}...")
        print(f"   Priority: {priority:.3f}")
        print(f"   Similarity: {similarity:.3f}")
        print(f"   Importance: {importance:.3f}")

        # Verify priority formula
        # priority = (similarity * 0.5) + (importance * 0.3) + (recency * 0.2)
        expected_min = (similarity * 0.5) + (importance * 0.3)  # Without recency
        assert priority >= expected_min, \
            f"Priority {priority} below expected minimum {expected_min}"

    # Cleanup
    shutil.rmtree(workspace)
    print("\n✅ Test passed: Priority Scoring")


async def test_legacy_compatibility():
    """Test legacy API compatibility."""
    print("\n" + "="*80)
    print("TEST 6: Legacy API Compatibility")
    print("="*80)

    manager, workspace = await test_initialization()

    print("\n🔍 Testing legacy methods...")

    # Test retrieve (should return empty and warn)
    result = manager.retrieve(MemoryType.LONG_TERM)
    assert result == [], "retrieve() should return empty list"
    print("✅ retrieve() - backwards compatible")

    # Test store_code_pattern (should not crash)
    manager.store_code_pattern(
        name="test_pattern",
        description="Test pattern",
        language="python",
        code="print('test')",
        use_cases=["testing"]
    )
    print("✅ store_code_pattern() - backwards compatible")

    # Test store_learning (should not crash)
    learning_id = manager.store_learning(
        description="Test learning",
        lesson="Test lesson",
        context="Test context",
        impact="high"
    )
    print("✅ store_learning() - backwards compatible")

    # Test get_relevant_learnings
    learnings = manager.get_relevant_learnings("test", limit=5)
    assert learnings == [], "get_relevant_learnings() should return empty list"
    print("✅ get_relevant_learnings() - backwards compatible")

    # Test get_relevant_patterns
    patterns = await manager.get_relevant_patterns("test", limit=3)
    assert patterns == [], "get_relevant_patterns() should return empty list"
    print("✅ get_relevant_patterns() - backwards compatible")

    # Test learning_entries property
    entries = manager.learning_entries
    assert entries == [], "learning_entries should return empty list"
    print("✅ learning_entries property - backwards compatible")

    # Cleanup
    shutil.rmtree(workspace)
    print("\n✅ Test passed: Legacy Compatibility")


async def run_all_tests():
    """Run all tests."""
    print("\n" + "="*80)
    print("MEMORY MANAGER v6.2 - COMPREHENSIVE TESTS")
    print("="*80)

    start_time = datetime.now()

    try:
        # Run tests
        await test_initialization()
        await test_store_and_search()
        await test_working_memory_lru()
        await test_context_window_management()
        await test_priority_scoring()
        await test_legacy_compatibility()

        # Summary
        elapsed = (datetime.now() - start_time).total_seconds()

        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        print(f"⏱️  Duration: {elapsed:.2f}s")
        print("\nMemory Manager v6.2 Features Validated:")
        print("  ✅ Initialization with workspace")
        print("  ✅ Store (short_term, long_term, working)")
        print("  ✅ Search with priority scoring")
        print("  ✅ Working memory LRU eviction")
        print("  ✅ Context window management")
        print("  ✅ Priority score calculation")
        print("  ✅ Legacy API compatibility")

        return True

    except Exception as e:
        print("\n" + "="*80)
        print("❌ TEST FAILED")
        print("="*80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
