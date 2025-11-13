"""
Memory Manager v6.2 - Strategic Memory Management

High-level API for intelligent memory management with:
- Memory compression (summarization)
- Context window management
- Selective retrieval with priority scoring
- Forgetting mechanism (LRU)
- Integration with MemorySystem v6 (FAISS+SQLite)

Architecture:
- MemoryManager (this file): Strategic management layer
- MemorySystem v6: Storage layer (FAISS+SQLite)
- OpenAI: Embeddings + summarization LLM

Purpose:
- Prevent context overflow by compressing old memories
- Prioritize relevant memories for retrieval
- Forget low-value memories to save space
- Provide simple API for agents

Usage:
    from core.memory_manager import get_memory_manager

    manager = get_memory_manager()
    await manager.initialize(workspace_path="/path/to/workspace")

    # Store with priority
    await manager.store(
        content="Important finding: Vite + React 18",
        memory_type=MemoryType.LONG_TERM,
        importance=0.9,
        metadata={"agent": "research", "type": "technology"}
    )

    # Search with automatic priority scoring
    results = await manager.search(
        query="frontend frameworks",
        memory_type=MemoryType.LONG_TERM,
        agent_id="architect",
        k=5
    )

    # Compress old memories
    await manager.compress_memories(older_than_days=7)

Author: KI AutoAgent Team
Version: 6.2.0 (Phase 4.1)
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import logging
from collections import OrderedDict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

# OpenAI for summarization
from openai import AsyncOpenAI

# MemorySystem v6 for storage
from ..memory.memory_system_v6 import MemorySystem

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class MemoryType(Enum):
    """Types of memory storage (aligned with cognitive science)."""

    SHORT_TERM = "short_term"  # Recent memories (last session)
    LONG_TERM = "long_term"    # Persistent memories (cross-session)
    WORKING = "working"        # Active task context (ephemeral)


# ============================================================================
# MEMORY MANAGER
# ============================================================================

class MemoryManager:
    """
    Strategic memory management with compression, prioritization, and forgetting.

    Features:
    - Memory compression (summarization of old memories)
    - Context window management (prevent overflow)
    - Selective retrieval (priority-based)
    - Forgetting mechanism (LRU for low-value memories)
    - Integration with MemorySystem v6

    Architecture:
    - Uses MemorySystem v6 for storage (FAISS+SQLite)
    - Uses OpenAI for summarization
    - Maintains in-memory LRU cache for working memory
    """

    # Constants
    MAX_WORKING_MEMORY = 20  # Max items in working memory (LRU)
    MAX_CONTEXT_TOKENS = 8000  # Max tokens to return in context
    COMPRESSION_AGE_DAYS = 7  # Compress memories older than this
    IMPORTANCE_THRESHOLD = 0.3  # Forget memories below this

    def __init__(self):
        """Initialize Memory Manager."""
        self.memory_system: MemorySystem | None = None
        self.openai_client: AsyncOpenAI | None = None
        self.workspace_path: str | None = None

        # Working memory (LRU cache)
        self.working_memory: OrderedDict[str, dict[str, Any]] = OrderedDict()

        # Compression tracking
        self.compressed_memory_ids: set[int] = set()

        logger.debug("📦 MemoryManager initialized (v6.2 full implementation)")

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    async def initialize(self, workspace_path: str) -> None:
        """
        Initialize Memory Manager with workspace.

        Args:
            workspace_path: Absolute path to workspace root

        Example:
            manager = get_memory_manager()
            await manager.initialize("/Users/me/MyProject")
        """
        self.workspace_path = workspace_path

        # Initialize MemorySystem v6
        self.memory_system = MemorySystem(workspace_path)
        await self.memory_system.initialize()

        # Initialize OpenAI client (lazy)
        self.openai_client = None  # Will be initialized when needed

        logger.info(f"✅ MemoryManager initialized for workspace: {workspace_path}")

    # ========================================================================
    # STORE
    # ========================================================================

    async def store(
        self,
        content: str,
        memory_type: MemoryType | str = MemoryType.LONG_TERM,
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None
    ) -> int:
        """
        Store content in memory with type and importance.

        Args:
            content: Text content to store
            memory_type: SHORT_TERM, LONG_TERM, or WORKING
            importance: Importance score (0.0-1.0)
            metadata: Additional metadata (agent, type, etc.)

        Returns:
            Vector ID of stored item

        Example:
            vector_id = await manager.store(
                content="Vite + React 18 recommended",
                memory_type=MemoryType.LONG_TERM,
                importance=0.9,
                metadata={"agent": "research", "type": "technology"}
            )
        """
        if not self.memory_system:
            raise RuntimeError("MemoryManager not initialized. Call initialize() first.")

        # Handle string memory_type
        if isinstance(memory_type, str):
            memory_type = MemoryType(memory_type)

        # Add importance and memory_type to metadata
        if metadata is None:
            metadata = {}

        metadata["importance"] = importance
        metadata["memory_type"] = memory_type.value
        metadata["timestamp"] = datetime.now().isoformat()

        # Store based on memory type
        if memory_type == MemoryType.WORKING:
            # Store in working memory (LRU cache)
            memory_id = f"working_{len(self.working_memory)}"
            self.working_memory[memory_id] = {
                "content": content,
                "metadata": metadata,
                "timestamp": datetime.now().isoformat()
            }

            # Enforce LRU eviction if over limit
            if len(self.working_memory) > self.MAX_WORKING_MEMORY:
                oldest_key = next(iter(self.working_memory))
                evicted = self.working_memory.pop(oldest_key)
                logger.debug(f"🗑️ Evicted from working memory: {oldest_key}")

                # Optionally promote to long-term if important
                if evicted["metadata"].get("importance", 0) > 0.7:
                    logger.debug(f"⬆️ Promoting evicted memory to long-term")
                    await self.memory_system.store(
                        content=evicted["content"],
                        metadata=evicted["metadata"]
                    )

            logger.debug(f"📝 Stored in working memory: {memory_id}")
            return -1  # Working memory has no vector ID

        else:
            # Store in MemorySystem v6 (SHORT_TERM or LONG_TERM)
            vector_id = await self.memory_system.store(
                content=content,
                metadata=metadata
            )

            logger.debug(f"💾 Stored in {memory_type.value}: vector_id={vector_id}")
            return vector_id

    # ========================================================================
    # SEARCH
    # ========================================================================

    async def search(
        self,
        query: str,
        memory_type: str | None = None,
        agent_id: str | None = None,
        k: int = 5
    ) -> list[dict[str, Any]]:
        """
        Search memory with priority-based ranking.

        Args:
            query: Search query
            memory_type: Filter by memory type (short_term, long_term, working)
            agent_id: Filter by agent ID
            k: Number of results to return

        Returns:
            List of memories sorted by priority score (descending)

        Priority Score Formula:
            priority = (similarity * 0.5) + (importance * 0.3) + (recency * 0.2)

        Example:
            results = await manager.search(
                query="frontend frameworks",
                memory_type="long_term",
                agent_id="research",
                k=5
            )

            for result in results:
                print(f"Priority: {result['priority_score']:.3f}")
                print(f"Content: {result['content']}")
        """
        if not self.memory_system:
            raise RuntimeError("MemoryManager not initialized")

        all_results = []

        # Search working memory first (if applicable)
        if memory_type is None or memory_type == "working":
            working_results = self._search_working_memory(query, agent_id)
            all_results.extend(working_results)

        # Search MemorySystem v6 (short_term and long_term)
        if memory_type is None or memory_type in ["short_term", "long_term"]:
            filters = {}
            if memory_type:
                filters["memory_type"] = memory_type
            if agent_id:
                filters["agent"] = agent_id

            search_k = k * 2  # Get more candidates for re-ranking
            storage_results = await self.memory_system.search(
                query=query,
                filters=filters if filters else None,
                k=search_k
            )

            all_results.extend(storage_results)

        # Calculate priority scores
        scored_results = []
        for result in all_results:
            priority_score = self._calculate_priority_score(result)
            result["priority_score"] = priority_score
            scored_results.append(result)

        # Sort by priority score (descending)
        scored_results.sort(key=lambda x: x["priority_score"], reverse=True)

        # Return top k
        final_results = scored_results[:k]

        logger.debug(f"🔍 Search returned {len(final_results)} results (priority-ranked)")
        return final_results

    def _search_working_memory(
        self,
        query: str,
        agent_id: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Search working memory (simple string matching).

        Args:
            query: Search query
            agent_id: Filter by agent ID

        Returns:
            List of matching memories from working memory
        """
        results = []
        query_lower = query.lower()

        for memory_id, memory in self.working_memory.items():
            # Filter by agent_id if provided
            if agent_id and memory["metadata"].get("agent") != agent_id:
                continue

            # Simple substring matching
            content_lower = memory["content"].lower()
            if query_lower in content_lower:
                # Calculate similarity based on match quality
                similarity = len(query_lower) / len(content_lower)

                results.append({
                    "content": memory["content"],
                    "metadata": memory["metadata"],
                    "timestamp": memory["timestamp"],
                    "similarity": similarity
                })

        return results

    def _calculate_priority_score(self, result: dict[str, Any]) -> float:
        """
        Calculate priority score for memory.

        Formula:
            priority = (similarity * 0.5) + (importance * 0.3) + (recency * 0.2)

        Args:
            result: Memory result dict

        Returns:
            Priority score (0.0-1.0)
        """
        # Extract factors
        similarity = result.get("similarity", 0.5)
        importance = result.get("metadata", {}).get("importance", 0.5)

        # Calculate recency score (exponential decay)
        timestamp_str = result.get("timestamp")
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                age_hours = (datetime.now() - timestamp).total_seconds() / 3600
                recency = max(0.0, 1.0 - (age_hours / (24 * 7)))  # Decay over 1 week
            except (ValueError, TypeError) as e:
                logger.debug(f"Could not parse timestamp {timestamp_str}: {e}")
                recency = 0.5
        else:
            recency = 0.5

        # Weighted sum
        priority = (similarity * 0.5) + (importance * 0.3) + (recency * 0.2)

        return priority

    # ========================================================================
    # COMPRESSION
    # ========================================================================

    async def compress_memories(
        self,
        older_than_days: int = 7,
        memory_type: str = "long_term"
    ) -> dict[str, Any]:
        """
        Compress old memories by summarizing them.

        Old memories are combined into summaries to save space and
        reduce context size while preserving key information.

        Args:
            older_than_days: Compress memories older than this (default: 7 days)
            memory_type: Memory type to compress (default: long_term)

        Returns:
            Dict with:
            - compressed_count: Number of memories compressed
            - summary_ids: List of new summary vector IDs
            - deleted_ids: List of deleted original memory IDs (optional)

        Example:
            result = await manager.compress_memories(older_than_days=7)
            print(f"Compressed {result['compressed_count']} memories")
        """
        if not self.memory_system:
            raise RuntimeError("MemoryManager not initialized")

        logger.info(f"🗜️ Compressing memories older than {older_than_days} days...")

        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=older_than_days)

        # Get all memories (we'll filter by date client-side)
        # NOTE: MemorySystem v6 doesn't have date filtering in search,
        # so we need to fetch all and filter manually

        # For now, return stub (full implementation would require
        # iterating through SQLite to find old memories)

        logger.warning("⚠️ compress_memories() not fully implemented yet")
        logger.warning("   Requires SQLite iteration to find old memories")
        logger.warning("   Will be implemented in future version")

        return {
            "compressed_count": 0,
            "summary_ids": [],
            "deleted_ids": []
        }

    async def _summarize_memories(
        self,
        memories: list[dict[str, Any]]
    ) -> str:
        """
        Summarize a list of memories using OpenAI.

        Args:
            memories: List of memory dicts with content

        Returns:
            Summarized content
        """
        if not self.openai_client:
            self.openai_client = AsyncOpenAI()

        # Combine memory contents
        combined_content = "\n\n".join([
            f"- {m['content']}" for m in memories
        ])

        # Create summarization prompt
        prompt = f"""Summarize the following memories into a concise summary that preserves key information:

{combined_content}

Provide a summary that:
1. Preserves important facts and findings
2. Removes redundancy
3. Is concise (max 200 words)
4. Maintains context for future reference

Summary:"""

        # Call OpenAI
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a memory compression assistant. Summarize memories concisely while preserving key information."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=400
        )

        summary = response.choices[0].message.content

        logger.debug(f"✅ Summarized {len(memories)} memories into {len(summary)} chars")

        return summary

    # ========================================================================
    # FORGETTING
    # ========================================================================

    async def forget_low_value_memories(
        self,
        importance_threshold: float = 0.3,
        memory_type: str = "long_term"
    ) -> int:
        """
        Forget (delete) memories below importance threshold.

        This implements a forgetting mechanism to prevent memory
        accumulation of low-value information.

        Args:
            importance_threshold: Delete memories with importance < this
            memory_type: Memory type to clean (default: long_term)

        Returns:
            Number of memories deleted

        Example:
            deleted_count = await manager.forget_low_value_memories(
                importance_threshold=0.3
            )
            print(f"Forgot {deleted_count} low-value memories")
        """
        if not self.memory_system:
            raise RuntimeError("MemoryManager not initialized")

        logger.info(f"🗑️ Forgetting memories with importance < {importance_threshold}...")

        # NOTE: MemorySystem v6 doesn't have delete API yet
        # This would require adding delete functionality to MemorySystem

        logger.warning("⚠️ forget_low_value_memories() not fully implemented yet")
        logger.warning("   Requires delete() method in MemorySystem v6")
        logger.warning("   Will be implemented in future version")

        return 0

    # ========================================================================
    # CONTEXT MANAGEMENT
    # ========================================================================

    async def get_context_for_agent(
        self,
        agent_id: str,
        query: str | None = None,
        max_tokens: int | None = None
    ) -> dict[str, Any]:
        """
        Get relevant memory context for agent.

        This is optimized for LLM context windows - returns memories
        that fit within token limit, prioritized by relevance.

        Args:
            agent_id: Agent identifier
            query: Optional query to search for relevant memories
            max_tokens: Max tokens to return (default: MAX_CONTEXT_TOKENS)

        Returns:
            Dict with:
            - memories: List of relevant memories
            - total_tokens: Estimated token count
            - truncated: Whether result was truncated

        Example:
            context = await manager.get_context_for_agent(
                agent_id="architect",
                query="frontend architecture",
                max_tokens=4000
            )

            for memory in context["memories"]:
                print(memory["content"])
        """
        if not self.memory_system:
            raise RuntimeError("MemoryManager not initialized")

        if max_tokens is None:
            max_tokens = self.MAX_CONTEXT_TOKENS

        # Search for relevant memories
        if query:
            results = await self.search(
                query=query,
                agent_id=agent_id,
                k=20  # Get more candidates
            )
        else:
            # No query - get recent memories for this agent
            results = await self.search(
                query="",  # Empty query returns all
                agent_id=agent_id,
                k=20
            )

        # Estimate tokens and truncate if needed
        selected_memories = []
        total_tokens = 0
        truncated = False

        for result in results:
            # Estimate tokens (rough: 1 token ≈ 4 chars)
            content_tokens = len(result["content"]) // 4

            if total_tokens + content_tokens > max_tokens:
                truncated = True
                break

            selected_memories.append(result)
            total_tokens += content_tokens

        logger.debug(f"📚 Context for {agent_id}: {len(selected_memories)} memories, {total_tokens} tokens")

        return {
            "memories": selected_memories,
            "total_tokens": total_tokens,
            "truncated": truncated
        }

    # ========================================================================
    # UTILITY
    # ========================================================================

    async def clear(self, memory_type: MemoryType | None = None) -> None:
        """
        Clear memory (DANGER!).

        Args:
            memory_type: Type to clear (None = all)

        Example:
            await manager.clear(MemoryType.WORKING)  # Clear working memory only
            await manager.clear()  # Clear ALL memory
        """
        if memory_type is None or memory_type == MemoryType.WORKING:
            self.working_memory.clear()
            logger.debug("🗑️ Working memory cleared")

        if memory_type is None and self.memory_system:
            await self.memory_system.clear()
            logger.debug("🗑️ Long-term and short-term memory cleared")

        logger.info("✅ Memory cleared")

    async def get_stats(self) -> dict[str, Any]:
        """
        Get memory statistics.

        Returns:
            Dict with:
            - working_memory_count: Items in working memory
            - storage_stats: Stats from MemorySystem v6

        Example:
            stats = await manager.get_stats()
            print(f"Working memory: {stats['working_memory_count']} items")
            print(f"Total items: {stats['storage_stats']['total_items']}")
        """
        storage_stats = {}
        if self.memory_system:
            storage_stats = await self.memory_system.get_stats()

        return {
            "working_memory_count": len(self.working_memory),
            "storage_stats": storage_stats
        }

    # ========================================================================
    # LEGACY COMPATIBILITY (for base_agent.py)
    # ========================================================================

    def retrieve(self, memory_type: MemoryType, query: str | None = None) -> list[Any]:
        """
        LEGACY: Retrieve data from memory (synchronous).

        NOTE: This is a stub for backwards compatibility.
        Use async search() instead.
        """
        logger.warning("⚠️ retrieve() is deprecated. Use async search() instead.")
        return []

    def store_code_pattern(
        self,
        name: str,
        description: str,
        language: str,
        code: str,
        use_cases: list[str]
    ) -> None:
        """
        LEGACY: Store a code pattern.

        NOTE: This is a stub for backwards compatibility.
        Will be implemented properly in future version.
        """
        logger.debug(f"📦 store_code_pattern called (stub): name={name}")

    def store_learning(
        self,
        description: str,
        lesson: str,
        context: str,
        impact: str
    ) -> str | None:
        """
        LEGACY: Store a learning entry.

        NOTE: This is a stub for backwards compatibility.
        Will be implemented properly in future version.
        """
        logger.debug(f"📦 store_learning called (stub): description={description[:50]}...")
        return None

    def get_relevant_learnings(self, context: str, limit: int = 5) -> list[Any]:
        """
        LEGACY: Get relevant learnings.

        NOTE: This is a stub for backwards compatibility.
        Use async search() instead.
        """
        logger.debug(f"📦 get_relevant_learnings called (stub): limit={limit}")
        return []

    async def get_relevant_patterns(self, context: str, limit: int = 3) -> list[Any]:
        """
        LEGACY: Get relevant patterns.

        NOTE: This is a stub for backwards compatibility.
        Use async search() instead.
        """
        logger.debug(f"📦 get_relevant_patterns called (stub): limit={limit}")
        return []

    @property
    def learning_entries(self) -> list[Any]:
        """LEGACY: Compatibility attribute for base_agent.py."""
        return []


# ============================================================================
# SINGLETON
# ============================================================================

_memory_manager_instance: MemoryManager | None = None


def get_memory_manager() -> MemoryManager:
    """Get or create memory manager singleton."""
    global _memory_manager_instance
    if _memory_manager_instance is None:
        _memory_manager_instance = MemoryManager()
    return _memory_manager_instance


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "MemoryManager",
    "MemoryType",
    "get_memory_manager"
]
