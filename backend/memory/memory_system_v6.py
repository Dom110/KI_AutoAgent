"""
KI AutoAgent v6.0 - Memory System

FAISS + SQLite hybrid memory system for agent communication and learning.

Architecture:
- FAISS: Vector similarity search (semantic search)
- SQLite: Metadata storage (structured queries)
- OpenAI embeddings: text-embedding-3-small (1536 dimensions)

Purpose:
- Inter-agent communication (ALL agents read/write)
- Cross-session learning
- Context accumulation

Storage:
- Vectors: $WORKSPACE/.ki_autoagent_ws/memory/vectors.faiss
- Metadata: $WORKSPACE/.ki_autoagent_ws/memory/metadata.db

Usage:
    from memory.memory_system_v6 import MemorySystem

    # Initialize
    memory = MemorySystem(workspace_path="/path/to/workspace")
    await memory.initialize()

    # Store
    await memory.store(
        content="Vite + React 18 recommended for 2025",
        metadata={"agent": "research", "type": "technology"}
    )

    # Search
    results = await memory.search(
        query="modern frontend frameworks",
        filters={"agent": "research"}
    )

Author: KI AutoAgent Team
Version: 6.0.0-alpha.1
Python: 3.13+
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any

import aiosqlite
import faiss
import numpy as np
from openai import AsyncOpenAI

# Setup logging
logger = logging.getLogger(__name__)


# ============================================================================
# MEMORY SYSTEM CLASS
# ============================================================================

class MemorySystem:
    """
    FAISS + SQLite hybrid memory system.

    Responsibilities:
    - Vector storage and similarity search (FAISS)
    - Metadata storage and filtering (SQLite)
    - Embedding generation (OpenAI)
    - Persistence (save/load indexes)

    Best Practices:
    - Always initialize() before use
    - Always close() after use (or use as async context manager)
    - Use filters for structured queries
    - Use semantic search for fuzzy matching
    """

    # Embedding model configuration
    EMBEDDING_MODEL = "text-embedding-3-small"
    EMBEDDING_DIMENSION = 1536

    def __init__(self, workspace_path: str):
        """
        Initialize MemorySystem.

        Args:
            workspace_path: Absolute path to user workspace
        """
        self.workspace_path = workspace_path

        # Storage paths
        self.vector_store_path = os.path.join(
            workspace_path,
            ".ki_autoagent_ws/memory/vectors.faiss"
        )
        self.metadata_db_path = os.path.join(
            workspace_path,
            ".ki_autoagent_ws/memory/metadata.db"
        )

        # Components (initialized in initialize())
        self.index: faiss.IndexFlatL2 | None = None
        self.db_conn: aiosqlite.Connection | None = None
        self.openai_client: AsyncOpenAI | None = None

        logger.info(f"MemorySystem created for workspace: {workspace_path}")

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    async def initialize(self) -> None:
        """
        Initialize all memory components.

        Steps:
        1. Create directories
        2. Initialize/load FAISS index
        3. Initialize/load SQLite database
        4. Initialize OpenAI client
        """
        logger.info("Initializing MemorySystem...")

        # 1. Create directories
        os.makedirs(os.path.dirname(self.vector_store_path), exist_ok=True)
        logger.debug(f"Memory directory: {os.path.dirname(self.vector_store_path)}")

        # 2. Initialize FAISS
        await self._initialize_faiss()

        # 3. Initialize SQLite
        await self._initialize_sqlite()

        # 4. OpenAI client (lazy initialization - only when needed)
        self.openai_client: AsyncOpenAI | None = None
        logger.debug("OpenAI client will be initialized on first use (lazy)")

        logger.info("MemorySystem initialization complete")

    async def _initialize_faiss(self) -> None:
        """
        Initialize or load FAISS index.

        If index file exists: Load it
        Else: Create new IndexFlatL2
        """
        if os.path.exists(self.vector_store_path):
            # Load existing index
            self.index = faiss.read_index(self.vector_store_path)
            logger.debug(f"FAISS index loaded: {self.index.ntotal} vectors")
        else:
            # Create new index
            self.index = faiss.IndexFlatL2(self.EMBEDDING_DIMENSION)
            logger.debug(f"New FAISS index created ({self.EMBEDDING_DIMENSION}D)")

    async def _initialize_sqlite(self) -> None:
        """
        Initialize or load SQLite database.

        Creates memory_items table if not exists.
        """
        self.db_conn = await aiosqlite.connect(self.metadata_db_path)

        # ⚠️ FIX: Ensure DB file has write permissions (Bug found 2025-10-11)
        # Without this, memory.store() fails with "attempt to write a readonly database"
        if os.path.exists(self.metadata_db_path):
            os.chmod(self.metadata_db_path, 0o664)  # rw-rw-r--
            logger.debug(f"SQLite permissions set: {self.metadata_db_path}")

        # Also ensure parent directory is writable
        db_dir = os.path.dirname(self.metadata_db_path)
        if os.path.exists(db_dir):
            os.chmod(db_dir, 0o775)  # rwxrwxr-x
            logger.debug(f"Memory directory permissions set: {db_dir}")

        # Create table
        await self.db_conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vector_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                UNIQUE(vector_id)
            )
        """)

        # Create indexes for common queries
        await self.db_conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON memory_items(timestamp)
        """)

        await self.db_conn.commit()
        logger.debug("SQLite database initialized")

    # ========================================================================
    # STORE
    # ========================================================================

    async def store(
        self,
        content: str,
        metadata: dict[str, Any]
    ) -> int:
        """
        Store content in memory with metadata.

        Steps:
        1. Generate embedding (OpenAI)
        2. Add vector to FAISS
        3. Store metadata in SQLite
        4. Persist FAISS index to disk

        Args:
            content: Text content to store
            metadata: Metadata dict (agent, type, etc.)

        Returns:
            Vector ID of stored item

        Example:
            vector_id = await memory.store(
                content="Vite + React 18 recommended",
                metadata={"agent": "research", "type": "technology"}
            )
        """
        if not self.index or not self.db_conn:
            raise RuntimeError("MemorySystem not initialized. Call initialize() first.")

        # Lazy initialize OpenAI client
        if not self.openai_client:
            self.openai_client = AsyncOpenAI()
            logger.debug("OpenAI client initialized (lazy)")

        logger.debug(f"Storing memory: {content[:50]}...")

        # 1. Generate embedding
        embedding = await self._get_embedding(content)

        # 2. Add to FAISS
        vector_id = self.index.ntotal
        self.index.add(np.array([embedding], dtype=np.float32))
        logger.debug(f"Vector added to FAISS: ID={vector_id}")

        # 3. Store metadata in SQLite
        timestamp = datetime.now().isoformat()
        await self.db_conn.execute(
            """
            INSERT INTO memory_items (vector_id, content, metadata, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (vector_id, content, json.dumps(metadata), timestamp)
        )
        await self.db_conn.commit()
        logger.debug(f"Metadata stored in SQLite: ID={vector_id}")

        # 4. Persist FAISS index
        faiss.write_index(self.index, self.vector_store_path)
        logger.debug(f"FAISS index persisted: {self.index.ntotal} vectors")

        return vector_id

    async def _get_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for text using OpenAI.

        Args:
            text: Text to embed

        Returns:
            Numpy array of shape (1536,)
        """
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")

        response = await self.openai_client.embeddings.create(
            model=self.EMBEDDING_MODEL,
            input=text
        )

        embedding = np.array(response.data[0].embedding, dtype=np.float32)
        logger.debug(f"Embedding generated: {embedding.shape}")

        return embedding

    # ========================================================================
    # SEARCH
    # ========================================================================

    async def search(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        k: int = 5
    ) -> list[dict[str, Any]]:
        """
        Search memory using semantic similarity.

        Steps:
        1. Generate query embedding
        2. Search FAISS for k nearest vectors
        3. Retrieve metadata from SQLite
        4. Apply filters
        5. Return results sorted by similarity

        Args:
            query: Search query text
            filters: Metadata filters (e.g., {"agent": "research"})
            k: Number of results to return

        Returns:
            List of dicts with content, metadata, timestamp, similarity

        Example:
            results = await memory.search(
                query="frontend frameworks",
                filters={"agent": "research", "type": "technology"},
                k=5
            )

            for result in results:
                print(f"{result['similarity']:.3f}: {result['content']}")
        """
        if not self.index or not self.db_conn:
            raise RuntimeError("MemorySystem not initialized. Call initialize() first.")

        # Lazy initialize OpenAI client
        if not self.openai_client:
            self.openai_client = AsyncOpenAI()
            logger.debug("OpenAI client initialized (lazy)")

        if self.index.ntotal == 0:
            logger.debug("FAISS index is empty, returning no results")
            return []

        logger.debug(f"Searching memory: query='{query[:50]}...', k={k}, filters={filters}")

        # 1. Generate query embedding
        query_embedding = await self._get_embedding(query)

        # 2. Search FAISS (get more candidates if we have filters)
        search_k = k * 3 if filters else k
        search_k = min(search_k, self.index.ntotal)  # Don't search more than we have

        distances, indices = self.index.search(
            np.array([query_embedding], dtype=np.float32),
            search_k
        )

        logger.debug(f"FAISS search returned {len(indices[0])} candidates")

        # 3. Retrieve metadata from SQLite
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            # Skip invalid indices (FAISS returns -1 for missing)
            if idx < 0:
                continue

            cursor = await self.db_conn.execute(
                """
                SELECT content, metadata, timestamp
                FROM memory_items
                WHERE vector_id = ?
                """,
                (int(idx),)
            )
            row = await cursor.fetchone()

            if row:
                content, metadata_json, timestamp = row
                metadata = json.loads(metadata_json)

                # 4. Apply filters
                if filters:
                    # Check if all filter conditions match
                    if not all(metadata.get(k) == v for k, v in filters.items()):
                        continue

                # Calculate similarity score (convert L2 distance to similarity)
                similarity = 1.0 / (1.0 + float(distance))

                results.append({
                    "content": content,
                    "metadata": metadata,
                    "timestamp": timestamp,
                    "similarity": similarity
                })

                # Stop if we have enough results
                if len(results) >= k:
                    break

        logger.debug(f"Memory search returned {len(results)} results")

        # 5. Results are already sorted by similarity (FAISS returns nearest first)
        return results

    # ========================================================================
    # UTILITY
    # ========================================================================

    async def count(self) -> int:
        """
        Get total number of memory items.

        Returns:
            Total count of stored items
        """
        if not self.index:
            return 0

        return self.index.ntotal

    async def clear(self) -> None:
        """
        Clear all memory (DANGER!).

        Deletes all vectors and metadata.
        """
        if not self.index or not self.db_conn:
            raise RuntimeError("MemorySystem not initialized")

        logger.warning("Clearing ALL memory!")

        # Clear FAISS
        self.index = faiss.IndexFlatL2(self.EMBEDDING_DIMENSION)
        faiss.write_index(self.index, self.vector_store_path)

        # Clear SQLite
        await self.db_conn.execute("DELETE FROM memory_items")
        await self.db_conn.commit()

        logger.info("Memory cleared")

    async def get_stats(self) -> dict[str, Any]:
        """
        Get memory system statistics.

        Returns:
            Dict with stats (total_items, by_agent, by_type, etc.)
        """
        if not self.db_conn:
            return {"total_items": 0}

        # Total items
        cursor = await self.db_conn.execute(
            "SELECT COUNT(*) FROM memory_items"
        )
        total = (await cursor.fetchone())[0]

        # By agent
        cursor = await self.db_conn.execute("""
            SELECT
                json_extract(metadata, '$.agent') as agent,
                COUNT(*) as count
            FROM memory_items
            WHERE json_extract(metadata, '$.agent') IS NOT NULL
            GROUP BY agent
        """)
        by_agent = {row[0]: row[1] for row in await cursor.fetchall()}

        # By type
        cursor = await self.db_conn.execute("""
            SELECT
                json_extract(metadata, '$.type') as type,
                COUNT(*) as count
            FROM memory_items
            WHERE json_extract(metadata, '$.type') IS NOT NULL
            GROUP BY type
        """)
        by_type = {row[0]: row[1] for row in await cursor.fetchall()}

        return {
            "total_items": total,
            "by_agent": by_agent,
            "by_type": by_type
        }

    # ========================================================================
    # CLEANUP
    # ========================================================================

    async def close(self) -> None:
        """
        Close connections and cleanup resources.
        """
        if self.db_conn:
            await self.db_conn.close()
            logger.debug("SQLite connection closed")

        # FAISS index is already persisted, no cleanup needed
        # OpenAI client is stateless, no cleanup needed

        logger.info("MemorySystem closed")

    # ========================================================================
    # CONTEXT MANAGER
    # ========================================================================

    async def __aenter__(self) -> MemorySystem:
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def main():
    """
    Example usage of MemorySystem.

    Demonstrates:
    1. Initialization
    2. Storing memories
    3. Searching with filters
    4. Statistics
    5. Cleanup
    """
    import logging

    # Setup logging
    logging.basicConfig(level=logging.DEBUG)

    # Use as async context manager
    async with MemorySystem("/tmp/test-workspace-v6") as memory:
        # Store some memories
        print("Storing memories...")
        await memory.store(
            content="Vite + React 18 recommended for 2025 frontend development",
            metadata={"agent": "research", "type": "technology", "confidence": 0.9}
        )

        await memory.store(
            content="Use FastAPI with Python 3.13 for backend APIs",
            metadata={"agent": "research", "type": "technology", "confidence": 0.95}
        )

        await memory.store(
            content="Architecture: Microservices with Docker containers",
            metadata={"agent": "architect", "type": "design", "pattern": "microservices"}
        )

        # Search without filters
        print("\nSearch 1: 'frontend frameworks' (no filters)")
        results = await memory.search("frontend frameworks", k=2)
        for r in results:
            print(f"  {r['similarity']:.3f}: {r['content'][:60]}... ({r['metadata']['agent']})")

        # Search with filters
        print("\nSearch 2: 'technology' (filter: agent=research)")
        results = await memory.search(
            "technology recommendations",
            filters={"agent": "research"},
            k=5
        )
        for r in results:
            print(f"  {r['similarity']:.3f}: {r['content'][:60]}...")

        # Stats
        print("\nMemory Stats:")
        stats = await memory.get_stats()
        print(f"  Total items: {stats['total_items']}")
        print(f"  By agent: {stats['by_agent']}")
        print(f"  By type: {stats['by_type']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
