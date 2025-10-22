"""
Global Memory System - Simple cross-project learning.

Stores successful patterns and error solutions across all projects.
No privacy features, just simple and effective learning.

Author: KI AutoAgent Team
Version: 7.1.0
Python: 3.13+
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Any, Optional
from datetime import datetime
import faiss
import aiosqlite
import numpy as np
import logging

logger = logging.getLogger(__name__)


class GlobalMemorySystem:
    """
    Simple global memory that learns across projects.

    Features:
    - Pattern storage with success tracking
    - Error/solution mapping
    - Semantic search via FAISS
    - SQLite for metadata
    """

    def __init__(self):
        """Initialize with fixed path in user home."""
        # ALWAYS use ~/.ki_autoagent/global_memory
        self.global_path = Path.home() / ".ki_autoagent" / "global_memory"
        self.global_path.mkdir(parents=True, exist_ok=True)

        # Simple file-based storage
        self.patterns_db = self.global_path / "patterns.db"
        self.patterns_faiss = self.global_path / "patterns.faiss"
        self.errors_db = self.global_path / "errors.db"

        self.index = None
        self.openai_client = None

        logger.info(f"🌍 Global Memory at: {self.global_path}")

    async def initialize(self):
        """Initialize storage."""
        # Create/load FAISS index
        if self.patterns_faiss.exists():
            self.index = faiss.read_index(str(self.patterns_faiss))
            logger.info(f"   📚 Loaded existing index with {self.index.ntotal} vectors")
        else:
            self.index = faiss.IndexFlatL2(1536)  # OpenAI embedding dimension
            logger.info("   📚 Created new FAISS index")

        # Create SQLite tables if needed
        await self._create_tables()

    async def _create_tables(self):
        """Create database tables if they don't exist."""
        # Patterns table
        async with aiosqlite.connect(self.patterns_db) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_hash TEXT UNIQUE,
                    content TEXT,
                    vector_id INTEGER,
                    project_type TEXT,
                    success_count INTEGER DEFAULT 1,
                    fail_count INTEGER DEFAULT 0,
                    first_seen TEXT,
                    last_seen TEXT,
                    metadata TEXT
                )
            """)
            await db.execute("CREATE INDEX IF NOT EXISTS idx_project_type ON patterns(project_type)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_pattern_hash ON patterns(pattern_hash)")
            await db.commit()

        # Errors table
        async with aiosqlite.connect(self.errors_db) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_hash TEXT UNIQUE,
                    error_text TEXT,
                    solutions TEXT,
                    occurrence_count INTEGER DEFAULT 1,
                    first_seen TEXT,
                    last_seen TEXT
                )
            """)
            await db.execute("CREATE INDEX IF NOT EXISTS idx_error_hash ON errors(error_hash)")
            await db.commit()

    async def store_pattern(
        self,
        content: str,
        project_type: str,
        success: bool = True
    ) -> bool:
        """
        Store a pattern from successful work.

        Args:
            content: Pattern description/code
            project_type: Type of project (web_app, api, etc.)
            success: Whether this pattern succeeded
        """
        # Generate unique hash
        pattern_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        async with aiosqlite.connect(self.patterns_db) as db:
            # Check if exists
            cursor = await db.execute(
                "SELECT id, success_count, fail_count FROM patterns WHERE pattern_hash = ?",
                (pattern_hash,)
            )
            existing = await cursor.fetchone()

            if existing:
                # Update counts
                if success:
                    await db.execute(
                        "UPDATE patterns SET success_count = success_count + 1, last_seen = ? WHERE id = ?",
                        (datetime.now().isoformat(), existing[0])
                    )
                else:
                    await db.execute(
                        "UPDATE patterns SET fail_count = fail_count + 1, last_seen = ? WHERE id = ?",
                        (datetime.now().isoformat(), existing[0])
                    )
            else:
                # Insert new pattern
                # Generate embedding
                vector_id = await self._add_vector(content)

                await db.execute(
                    """INSERT INTO patterns
                       (pattern_hash, content, vector_id, project_type,
                        success_count, fail_count, first_seen, last_seen, metadata)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        pattern_hash, content, vector_id, project_type,
                        1 if success else 0, 0 if success else 1,
                        datetime.now().isoformat(), datetime.now().isoformat(),
                        json.dumps({"source": "workflow"})
                    )
                )

            await db.commit()
            logger.debug(f"   💾 Stored pattern for {project_type}")

        # Save FAISS index
        if self.index:
            faiss.write_index(self.index, str(self.patterns_faiss))

        return True

    async def search_patterns(
        self,
        query: str,
        project_type: Optional[str] = None,
        limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Search for relevant patterns using semantic search.

        Args:
            query: Search query
            project_type: Optional filter by project type
            limit: Max results
        """
        if self.index is None or self.index.ntotal == 0:
            logger.debug("   No patterns in global memory yet")
            return []

        # Get query embedding
        query_vector = await self._get_embedding(query)
        if query_vector is None:
            # Fall back to simple text search without embeddings
            return await self._search_patterns_text(query, project_type, limit)

        # Search FAISS
        distances, indices = self.index.search(
            np.array([query_vector]).astype('float32'),
            min(limit * 2, self.index.ntotal)  # Get more for filtering
        )

        patterns = []
        async with aiosqlite.connect(self.patterns_db) as db:
            for idx, distance in zip(indices[0], distances[0]):
                if idx == -1:  # FAISS returns -1 for empty results
                    continue

                # Build query
                sql = "SELECT content, project_type, success_count, fail_count FROM patterns WHERE vector_id = ?"
                params = [int(idx)]

                if project_type:
                    sql += " AND project_type = ?"
                    params.append(project_type)

                cursor = await db.execute(sql, params)
                row = await cursor.fetchone()

                if row:
                    success_rate = row[2] / (row[2] + row[3]) if (row[2] + row[3]) > 0 else 0
                    patterns.append({
                        "content": row[0],
                        "project_type": row[1],
                        "success_rate": success_rate,
                        "usage_count": row[2] + row[3],
                        "similarity": float(1 / (1 + distance)),  # Convert distance to similarity
                        "source": "global_patterns"
                    })

                if len(patterns) >= limit:
                    break

        return patterns

    async def _search_patterns_text(
        self,
        query: str,
        project_type: Optional[str] = None,
        limit: int = 5
    ) -> list[dict[str, Any]]:
        """Fallback text search when embeddings not available."""
        patterns = []

        async with aiosqlite.connect(self.patterns_db) as db:
            sql = """
                SELECT content, project_type, success_count, fail_count
                FROM patterns
                WHERE content LIKE ?
            """
            params = [f"%{query}%"]

            if project_type:
                sql += " AND project_type = ?"
                params.append(project_type)

            sql += " ORDER BY success_count DESC LIMIT ?"
            params.append(limit)

            cursor = await db.execute(sql, params)
            async for row in cursor:
                success_rate = row[2] / (row[2] + row[3]) if (row[2] + row[3]) > 0 else 0
                patterns.append({
                    "content": row[0],
                    "project_type": row[1],
                    "success_rate": success_rate,
                    "usage_count": row[2] + row[3],
                    "similarity": 0.5,  # Fixed similarity for text search
                    "source": "global_patterns"
                })

        return patterns

    async def store_error_solution(
        self,
        error: str,
        solution: str
    ) -> bool:
        """
        Store an error and its solution.

        Args:
            error: Error message/description
            solution: How it was solved
        """
        # Normalize error for matching
        error_normalized = self._normalize_error(error)
        error_hash = hashlib.sha256(error_normalized.encode()).hexdigest()[:16]

        async with aiosqlite.connect(self.errors_db) as db:
            cursor = await db.execute(
                "SELECT id, solutions FROM errors WHERE error_hash = ?",
                (error_hash,)
            )
            existing = await cursor.fetchone()

            if existing:
                # Add solution if new
                solutions = json.loads(existing[1])
                if solution not in solutions:
                    solutions.append(solution)
                    await db.execute(
                        "UPDATE errors SET solutions = ?, occurrence_count = occurrence_count + 1, last_seen = ? WHERE id = ?",
                        (json.dumps(solutions), datetime.now().isoformat(), existing[0])
                    )
            else:
                # Insert new error
                await db.execute(
                    """INSERT INTO errors
                       (error_hash, error_text, solutions, occurrence_count, first_seen, last_seen)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        error_hash, error, json.dumps([solution]), 1,
                        datetime.now().isoformat(), datetime.now().isoformat()
                    )
                )

            await db.commit()
            logger.debug(f"   💾 Stored error solution")

        return True

    async def get_error_solutions(self, error: str) -> list[str]:
        """
        Get known solutions for an error.

        Args:
            error: Error message

        Returns:
            List of solution strings
        """
        error_normalized = self._normalize_error(error)
        error_hash = hashlib.sha256(error_normalized.encode()).hexdigest()[:16]

        async with aiosqlite.connect(self.errors_db) as db:
            cursor = await db.execute(
                "SELECT solutions FROM errors WHERE error_hash = ?",
                (error_hash,)
            )
            row = await cursor.fetchone()

            if row:
                return json.loads(row[0])

        return []

    def _normalize_error(self, error: str) -> str:
        """Normalize error for matching (remove line numbers, paths, etc)."""
        import re
        # Remove line numbers
        error = re.sub(r'line \d+', 'line X', error)
        # Remove file paths
        error = re.sub(r'/[^\s]+', '/PATH', error)
        # Remove memory addresses
        error = re.sub(r'0x[0-9a-fA-F]+', '0xADDR', error)
        # Lowercase
        return error.lower()

    async def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get OpenAI embedding for text."""
        try:
            if not self.openai_client:
                from openai import AsyncOpenAI
                self.openai_client = AsyncOpenAI()

            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return np.array(response.data[0].embedding)
        except Exception as e:
            logger.warning(f"   ⚠️ Embeddings not available: {e}")
            return None

    async def _add_vector(self, text: str) -> int:
        """Add vector to FAISS index and return its ID."""
        vector = await self._get_embedding(text)
        if vector is not None and self.index is not None:
            vector_id = self.index.ntotal
            self.index.add(np.array([vector]).astype('float32'))
            return vector_id
        return -1

    async def get_stats(self) -> dict[str, Any]:
        """Get statistics about global memory."""
        stats = {
            "patterns_count": 0,
            "errors_count": 0,
            "most_successful_patterns": [],
            "most_common_errors": []
        }

        # Pattern stats
        async with aiosqlite.connect(self.patterns_db) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM patterns")
            row = await cursor.fetchone()
            if row:
                stats["patterns_count"] = row[0]

            # Top patterns
            cursor = await db.execute("""
                SELECT content, success_count, fail_count, project_type
                FROM patterns
                ORDER BY success_count DESC
                LIMIT 5
            """)
            async for row in cursor:
                success_rate = row[1] / (row[1] + row[2]) if (row[1] + row[2]) > 0 else 0
                stats["most_successful_patterns"].append({
                    "content": row[0][:100],  # First 100 chars
                    "success_rate": success_rate,
                    "usage_count": row[1] + row[2],
                    "project_type": row[3]
                })

        # Error stats
        async with aiosqlite.connect(self.errors_db) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM errors")
            row = await cursor.fetchone()
            if row:
                stats["errors_count"] = row[0]

            # Top errors
            cursor = await db.execute("""
                SELECT error_text, occurrence_count, solutions
                FROM errors
                ORDER BY occurrence_count DESC
                LIMIT 5
            """)
            async for row in cursor:
                stats["most_common_errors"].append({
                    "error": row[0][:100],
                    "occurrences": row[1],
                    "solution_count": len(json.loads(row[2]))
                })

        return stats


# ============================================================================
# Export
# ============================================================================

__all__ = ["GlobalMemorySystem"]