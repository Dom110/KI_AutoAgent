"""
Unit Tests for memory_system_v6.py - Base Memory Functionality

Tests:
- Memory initialization
- Store operations
- Search operations
- Filters
- Statistics
"""

import asyncio
import os
import tempfile

import pytest

from memory.memory_system_v6 import MemorySystem


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
async def temp_workspace():
    """Create temporary workspace directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
async def memory(temp_workspace):
    """Create and initialize MemorySystem instance."""
    mem = MemorySystem(workspace_path=temp_workspace)
    await mem.initialize()
    yield mem
    await mem.close()


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_memory_initialization(memory):
    """Test that memory system initializes correctly."""
    assert memory.index is not None, "FAISS index not initialized"
    assert memory.db_conn is not None, "SQLite connection not initialized"
    assert memory.openai_client is not None, "OpenAI client not initialized"


@pytest.mark.asyncio
async def test_memory_directories_created(memory):
    """Test that memory directories are created."""
    from pathlib import Path

    vector_dir = Path(memory.vector_store_path).parent
    assert vector_dir.exists(), "Memory directory not created"


# ============================================================================
# STORE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_store_single_item(memory):
    """Test storing a single memory item."""
    vector_id = await memory.store(
        content="Test content",
        metadata={"agent": "test", "type": "test_data"}
    )

    assert isinstance(vector_id, int)
    assert vector_id >= 0

    # Check count
    count = await memory.count()
    assert count == 1


@pytest.mark.asyncio
async def test_store_multiple_items(memory):
    """Test storing multiple memory items."""
    # Store 3 items
    id1 = await memory.store("Item 1", {"agent": "research", "type": "finding"})
    id2 = await memory.store("Item 2", {"agent": "architect", "type": "design"})
    id3 = await memory.store("Item 3", {"agent": "codesmith", "type": "code"})

    assert id1 == 0
    assert id2 == 1
    assert id3 == 2

    # Check count
    count = await memory.count()
    assert count == 3


# ============================================================================
# SEARCH TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_search_basic(memory):
    """Test basic semantic search without filters."""
    # Store test data
    await memory.store(
        "React is a popular frontend framework",
        {"agent": "research", "type": "technology"}
    )

    await memory.store(
        "Vue is another frontend framework",
        {"agent": "research", "type": "technology"}
    )

    # Search
    results = await memory.search("frontend framework", k=2)

    assert len(results) == 2
    assert all("frontend framework" in r["content"] for r in results)
    assert all("similarity" in r for r in results)
    assert all(r["similarity"] > 0 for r in results)


@pytest.mark.asyncio
async def test_search_with_filters(memory):
    """Test search with metadata filters."""
    # Store data from different agents
    await memory.store("Research finding 1", {"agent": "research", "type": "finding"})
    await memory.store("Research finding 2", {"agent": "research", "type": "finding"})
    await memory.store("Architecture design", {"agent": "architect", "type": "design"})

    # Search with filter
    results = await memory.search(
        "finding",
        filters={"agent": "research"},
        k=5
    )

    # Should only return research results
    assert len(results) == 2
    assert all(r["metadata"]["agent"] == "research" for r in results)


@pytest.mark.asyncio
async def test_search_empty_memory(memory):
    """Test search on empty memory."""
    results = await memory.search("anything", k=5)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_semantic_similarity(memory):
    """Test that semantic search works (similar meanings match)."""
    # Store
    await memory.store(
        "Use Vite for fast frontend development",
        {"agent": "research", "type": "tool"}
    )

    # Search with synonym
    results = await memory.search("build tools for web apps", k=1)

    # Should find the Vite recommendation (semantic similarity)
    assert len(results) > 0
    assert "Vite" in results[0]["content"]


# ============================================================================
# STATISTICS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_stats_empty(memory):
    """Test statistics on empty memory."""
    stats = await memory.get_stats()

    assert stats["total_items"] == 0
    assert stats["by_agent"] == {}
    assert stats["by_type"] == {}


@pytest.mark.asyncio
async def test_stats_with_data(memory):
    """Test statistics with data."""
    # Store data
    await memory.store("Item 1", {"agent": "research", "type": "finding"})
    await memory.store("Item 2", {"agent": "research", "type": "finding"})
    await memory.store("Item 3", {"agent": "architect", "type": "design"})

    stats = await memory.get_stats()

    assert stats["total_items"] == 3
    assert stats["by_agent"]["research"] == 2
    assert stats["by_agent"]["architect"] == 1
    assert stats["by_type"]["finding"] == 2
    assert stats["by_type"]["design"] == 1


# ============================================================================
# PERSISTENCE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_persistence(temp_workspace):
    """Test that memory persists across instances."""
    # First instance: Store data
    async with MemorySystem(temp_workspace) as mem1:
        await mem1.store("Persisted item", {"agent": "test"})
        count1 = await mem1.count()
        assert count1 == 1

    # Second instance: Should load existing data
    async with MemorySystem(temp_workspace) as mem2:
        count2 = await mem2.count()
        assert count2 == 1, "Memory not persisted between instances"

        # Search should find the persisted item
        results = await mem2.search("Persisted", k=1)
        assert len(results) == 1
        assert "Persisted item" in results[0]["content"]


# ============================================================================
# CLEAR TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_clear(memory):
    """Test clearing all memory."""
    # Store data
    await memory.store("Item 1", {"agent": "test"})
    await memory.store("Item 2", {"agent": "test"})
    assert await memory.count() == 2

    # Clear
    await memory.clear()

    # Should be empty
    assert await memory.count() == 0

    # Search should return nothing
    results = await memory.search("Item", k=5)
    assert len(results) == 0


# ============================================================================
# CONTEXT MANAGER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_context_manager(temp_workspace):
    """Test async context manager usage."""
    async with MemorySystem(temp_workspace) as mem:
        # Should be initialized
        assert mem.index is not None

        # Should work
        await mem.store("Context manager test", {"agent": "test"})
        count = await mem.count()
        assert count == 1

    # After exiting, connection should be closed
    # (We can't easily test this without accessing private attributes)


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
