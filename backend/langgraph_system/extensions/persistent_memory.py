"""
Persistent Memory System for Agents
Combines SQLite for long-term storage with FAISS for semantic search
"""

import json
import sqlite3
import logging
import pickle
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

try:
    import faiss
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import FAISS
    VECTOR_SEARCH_AVAILABLE = True
except ImportError:
    VECTOR_SEARCH_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("FAISS not available - vector search disabled")

from ..state import MemoryEntry

logger = logging.getLogger(__name__)


class PersistentAgentMemory:
    """
    Advanced memory system with persistence and semantic search
    """

    def __init__(
        self,
        agent_name: str,
        db_path: str = "agent_memories.db",
        vector_store_path: Optional[str] = None,
        embedding_model: str = "text-embedding-ada-002"
    ):
        """
        Initialize persistent memory for an agent

        Args:
            agent_name: Name of the agent
            db_path: Path to SQLite database
            vector_store_path: Path to save/load FAISS index
            embedding_model: OpenAI embedding model to use
        """
        self.agent_name = agent_name
        self.db_path = db_path
        self.vector_store_path = vector_store_path or f"vector_stores/{agent_name}"

        # Initialize SQLite
        self._init_sqlite()

        # Initialize vector search if available
        self.vector_store = None
        if VECTOR_SEARCH_AVAILABLE:
            try:
                self.embeddings = OpenAIEmbeddings(model=embedding_model)
                self._init_vector_store()
            except Exception as e:
                logger.warning(f"Could not initialize vector store: {e}")

        # Memory buffers
        self.short_term_buffer = []
        self.working_memory = {}

    def _init_sqlite(self):
        """Initialize SQLite database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Main memories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                importance REAL DEFAULT 0.5,
                metadata TEXT,
                session_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                accessed_count INTEGER DEFAULT 0,
                last_accessed DATETIME
            )
        ''')

        # Learning patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                pattern_hash TEXT UNIQUE,
                pattern TEXT NOT NULL,
                solution TEXT NOT NULL,
                success_rate REAL DEFAULT 0.0,
                usage_count INTEGER DEFAULT 0,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_used DATETIME,
                metadata TEXT
            )
        ''')

        # Agent interactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_agent TEXT NOT NULL,
                to_agent TEXT NOT NULL,
                interaction_type TEXT,
                content TEXT,
                result TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT
            )
        ''')

        # Create indexes for performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_memories_agent_type
            ON memories(agent_name, memory_type)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_patterns_agent
            ON learned_patterns(agent_name, success_rate DESC)
        ''')

        conn.commit()
        conn.close()

    def _init_vector_store(self):
        """Initialize or load FAISS vector store"""
        if not VECTOR_SEARCH_AVAILABLE:
            return

        vector_path = Path(self.vector_store_path)

        if vector_path.exists():
            # Load existing vector store
            try:
                self.vector_store = FAISS.load_local(
                    str(vector_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info(f"Loaded vector store for {self.agent_name}")
            except Exception as e:
                logger.error(f"Could not load vector store: {e}")
                self._create_new_vector_store()
        else:
            self._create_new_vector_store()

    def _create_new_vector_store(self):
        """Create a new FAISS vector store"""
        if not VECTOR_SEARCH_AVAILABLE:
            return

        try:
            # Create with initial dummy document
            self.vector_store = FAISS.from_texts(
                ["Initial memory"],
                self.embeddings,
                metadatas=[{"type": "init", "timestamp": str(datetime.now())}]
            )
            logger.info(f"Created new vector store for {self.agent_name}")
        except Exception as e:
            logger.error(f"Could not create vector store: {e}")
            self.vector_store = None

    def store(
        self,
        content_or_type: Any,
        content_or_metadata: Optional[Any] = None,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> int:
        """
        Flexible store method for compatibility with different calling conventions
        """
        # Check if first arg looks like a MemoryType enum (has .value attribute)
        if hasattr(content_or_type, 'value'):
            # Legacy format: store(MemoryType, dict)
            memory_type_map = {
                'WORKING': 'procedural',
                'EPISODIC': 'episodic',
                'SEMANTIC': 'semantic',
                'ENTITY': 'entity'
            }

            memory_type = memory_type_map.get(content_or_type.name, 'episodic')

            # Convert dict to string content
            if isinstance(content_or_metadata, dict):
                content = json.dumps(content_or_metadata)
                actual_metadata = content_or_metadata
            else:
                content = str(content_or_metadata)
                actual_metadata = {}

            return self.store_memory(
                content=content,
                memory_type=memory_type,
                importance=importance or 0.5,
                metadata=actual_metadata,
                session_id=session_id
            )
        else:
            # New format: store(content, memory_type, ...)
            return self.store_memory(
                content=str(content_or_type),
                memory_type=content_or_metadata or "episodic",
                importance=importance,
                metadata=metadata,
                session_id=session_id
            )

    def store_memory(
        self,
        content: str,
        memory_type: Literal["episodic", "semantic", "procedural", "entity"],
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> int:
        """
        Store a memory persistently

        Returns:
            Memory ID from database
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO memories
            (agent_name, memory_type, content, importance, metadata, session_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            self.agent_name,
            memory_type,
            content,
            importance,
            json.dumps(metadata or {}),
            session_id
        ))

        memory_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Add to vector store if semantic
        if memory_type == "semantic" and self.vector_store:
            try:
                self.vector_store.add_texts(
                    [content],
                    metadatas=[{
                        "memory_id": memory_id,
                        "type": memory_type,
                        "importance": importance,
                        "timestamp": str(datetime.now()),
                        **(metadata or {})
                    }]
                )
                self._save_vector_store()
            except Exception as e:
                logger.error(f"Could not add to vector store: {e}")

        # Update short-term buffer
        self.short_term_buffer.append({
            "id": memory_id,
            "content": content,
            "type": memory_type,
            "timestamp": datetime.now()
        })

        # Keep buffer size limited
        if len(self.short_term_buffer) > 100:
            self.short_term_buffer.pop(0)

        return memory_id

    def recall_similar(
        self,
        query: str,
        k: int = 5,
        memory_types: Optional[List[str]] = None,
        min_importance: float = 0.0
    ) -> List[MemoryEntry]:
        """
        Recall similar memories using semantic search

        Args:
            query: Query string
            k: Number of memories to retrieve
            memory_types: Filter by memory types
            min_importance: Minimum importance threshold

        Returns:
            List of relevant MemoryEntry objects
        """
        memories = []

        # Try vector search first
        if self.vector_store:
            try:
                docs = self.vector_store.similarity_search_with_score(query, k=k * 2)

                for doc, score in docs:
                    # Filter by type and importance
                    metadata = doc.metadata
                    if memory_types and metadata.get("type") not in memory_types:
                        continue
                    if metadata.get("importance", 0) < min_importance:
                        continue

                    memories.append(MemoryEntry(
                        content=doc.page_content,
                        memory_type=metadata.get("type", "unknown"),
                        timestamp=datetime.fromisoformat(metadata.get("timestamp", str(datetime.now()))),
                        importance=metadata.get("importance", 0.5),
                        metadata=metadata,
                        session_id=metadata.get("session_id", "")
                    ))

                    if len(memories) >= k:
                        break

            except Exception as e:
                logger.error(f"Vector search failed: {e}")

        # Fallback to SQL search if needed
        if len(memories) < k:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query_parts = ["agent_name = ?"]
            params = [self.agent_name]

            if memory_types:
                placeholders = ','.join('?' * len(memory_types))
                query_parts.append(f"memory_type IN ({placeholders})")
                params.extend(memory_types)

            query_parts.append("importance >= ?")
            params.append(min_importance)

            cursor.execute(f'''
                SELECT content, memory_type, timestamp, importance, metadata, session_id
                FROM memories
                WHERE {' AND '.join(query_parts)}
                ORDER BY importance DESC, timestamp DESC
                LIMIT ?
            ''', params + [k - len(memories)])

            for row in cursor.fetchall():
                memories.append(MemoryEntry(
                    content=row[0],
                    memory_type=row[1],
                    timestamp=datetime.fromisoformat(row[2]),
                    importance=row[3],
                    metadata=json.loads(row[4]),
                    session_id=row[5] or ""
                ))

            conn.close()

        # Update access counts
        self._update_access_counts([m.metadata.get("memory_id") for m in memories if "memory_id" in m.metadata])

        return memories

    async def search(
        self,
        query: str,
        memory_type: Optional[str] = None,
        agent_id: Optional[str] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar memories (compatibility wrapper for OrchestratorAgent)

        Args:
            query: Query string
            memory_type: Optional memory type filter
            agent_id: Optional agent ID filter (unused, for compatibility)
            k: Number of results to return

        Returns:
            List of dictionaries with memory information
        """
        # Call the existing recall_similar method
        memory_types = [memory_type] if memory_type else None
        memories = self.recall_similar(query, k=k, memory_types=memory_types)

        # Convert MemoryEntry objects to dicts for compatibility
        results = []
        for memory in memories:
            results.append({
                "content": memory.content,
                "type": memory.memory_type,
                "importance": memory.importance,
                "metadata": memory.metadata,
                "timestamp": memory.timestamp.isoformat() if memory.timestamp else None,
                "complexity": memory.metadata.get("complexity", "moderate") if memory.metadata else "moderate"
            })

        return results

    def learn_pattern(
        self,
        pattern: str,
        solution: str,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Learn a pattern-solution pair for future use

        Returns:
            True if pattern was learned/updated successfully
        """
        import hashlib
        pattern_hash = hashlib.md5(pattern.encode()).hexdigest()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if pattern exists
        cursor.execute('''
            SELECT id, success_rate, usage_count
            FROM learned_patterns
            WHERE agent_name = ? AND pattern_hash = ?
        ''', (self.agent_name, pattern_hash))

        existing = cursor.fetchone()

        if existing:
            # Update existing pattern
            pattern_id, old_rate, usage_count = existing
            new_rate = (old_rate * usage_count + (1.0 if success else 0.0)) / (usage_count + 1)

            cursor.execute('''
                UPDATE learned_patterns
                SET solution = ?, success_rate = ?, usage_count = ?, last_used = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (solution, new_rate, usage_count + 1, pattern_id))

        else:
            # Insert new pattern
            cursor.execute('''
                INSERT INTO learned_patterns
                (agent_name, pattern_hash, pattern, solution, success_rate, usage_count, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.agent_name,
                pattern_hash,
                pattern,
                solution,
                1.0 if success else 0.0,
                1,
                json.dumps(metadata or {})
            ))

        conn.commit()
        conn.close()
        return True

    def get_learned_solution(
        self,
        pattern: str,
        min_success_rate: float = 0.7
    ) -> Optional[str]:
        """Get a previously learned solution for a pattern"""
        import hashlib
        pattern_hash = hashlib.md5(pattern.encode()).hexdigest()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT solution, success_rate, usage_count
            FROM learned_patterns
            WHERE agent_name = ? AND pattern_hash = ? AND success_rate >= ?
        ''', (self.agent_name, pattern_hash, min_success_rate))

        result = cursor.fetchone()
        conn.close()

        if result:
            solution, rate, count = result
            logger.info(f"Found learned pattern with {rate:.2%} success rate ({count} uses)")
            return solution

        return None

    def record_agent_interaction(
        self,
        to_agent: str,
        interaction_type: str,
        content: str,
        result: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Record an interaction with another agent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO agent_interactions
            (from_agent, to_agent, interaction_type, content, result, session_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.agent_name, to_agent, interaction_type, content, result, session_id))

        conn.commit()
        conn.close()

    def get_interaction_history(
        self,
        with_agent: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get history of agent interactions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if with_agent:
            cursor.execute('''
                SELECT from_agent, to_agent, interaction_type, content, result, timestamp, session_id
                FROM agent_interactions
                WHERE (from_agent = ? AND to_agent = ?) OR (from_agent = ? AND to_agent = ?)
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (self.agent_name, with_agent, with_agent, self.agent_name, limit))
        else:
            cursor.execute('''
                SELECT from_agent, to_agent, interaction_type, content, result, timestamp, session_id
                FROM agent_interactions
                WHERE from_agent = ? OR to_agent = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (self.agent_name, self.agent_name, limit))

        interactions = []
        for row in cursor.fetchall():
            interactions.append({
                "from_agent": row[0],
                "to_agent": row[1],
                "type": row[2],
                "content": row[3],
                "result": row[4],
                "timestamp": row[5],
                "session_id": row[6]
            })

        conn.close()
        return interactions

    def _update_access_counts(self, memory_ids: List[int]):
        """Update access counts for retrieved memories"""
        if not memory_ids:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for memory_id in memory_ids:
            if memory_id:
                cursor.execute('''
                    UPDATE memories
                    SET accessed_count = accessed_count + 1,
                        last_accessed = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (memory_id,))

        conn.commit()
        conn.close()

    def _save_vector_store(self):
        """Save FAISS vector store to disk"""
        if self.vector_store and self.vector_store_path:
            try:
                Path(self.vector_store_path).parent.mkdir(parents=True, exist_ok=True)
                self.vector_store.save_local(str(self.vector_store_path))
            except Exception as e:
                logger.error(f"Could not save vector store: {e}")

    def consolidate_memories(self, max_age_days: int = 30):
        """Consolidate old memories to save space"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        # Delete low-importance old memories
        cursor.execute('''
            DELETE FROM memories
            WHERE agent_name = ?
            AND timestamp < ?
            AND importance < 0.3
            AND accessed_count < 2
        ''', (self.agent_name, cutoff_date))

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"Consolidated memories: deleted {deleted} low-importance old memories")

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about agent's memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # Total memories by type
        cursor.execute('''
            SELECT memory_type, COUNT(*), AVG(importance)
            FROM memories
            WHERE agent_name = ?
            GROUP BY memory_type
        ''', (self.agent_name,))

        stats["memories_by_type"] = {}
        for row in cursor.fetchall():
            stats["memories_by_type"][row[0]] = {
                "count": row[1],
                "avg_importance": row[2]
            }

        # Learned patterns
        cursor.execute('''
            SELECT COUNT(*), AVG(success_rate), MAX(success_rate)
            FROM learned_patterns
            WHERE agent_name = ?
        ''', (self.agent_name,))

        patterns = cursor.fetchone()
        stats["learned_patterns"] = {
            "count": patterns[0],
            "avg_success_rate": patterns[1],
            "best_success_rate": patterns[2]
        }

        # Recent interactions
        cursor.execute('''
            SELECT COUNT(*)
            FROM agent_interactions
            WHERE from_agent = ? OR to_agent = ?
        ''', (self.agent_name, self.agent_name))

        stats["total_interactions"] = cursor.fetchone()[0]

        conn.close()

        # Add vector store stats if available
        if self.vector_store:
            try:
                stats["vector_store_size"] = self.vector_store.index.ntotal
            except:
                stats["vector_store_size"] = 0

        stats["short_term_buffer_size"] = len(self.short_term_buffer)

        return stats