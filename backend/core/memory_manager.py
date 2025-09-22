"""
MemoryManager - Vector-based memory system for agents
Provides semantic search, pattern extraction, and learning capabilities
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import defaultdict
import asyncio
import logging

logger = logging.getLogger(__name__)

class MemoryType(Enum):
    """Types of memory"""
    EPISODIC = "episodic"      # Specific events and experiences
    SEMANTIC = "semantic"       # General knowledge and facts
    PROCEDURAL = "procedural"   # How to do things
    WORKING = "working"         # Temporary, current context

@dataclass
class MemoryMetadata:
    """Metadata for memory entries"""
    importance: float = 0.5
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    source: str = ""
    confidence: float = 1.0

@dataclass
class MemoryEntry:
    """Individual memory entry"""
    id: str
    agent_id: str
    timestamp: float
    content: Any
    embedding: Optional[List[float]]
    type: MemoryType
    metadata: MemoryMetadata

@dataclass
class MemorySearchResult:
    """Search result with relevance"""
    entry: MemoryEntry
    similarity: float
    relevance: float

@dataclass
class CodePattern:
    """Reusable code pattern"""
    id: str
    name: str
    description: str
    language: str
    code: str
    use_cases: List[str]
    success_rate: float
    usage_count: int
    last_used: float

@dataclass
class ArchitecturePattern:
    """Reusable architecture pattern"""
    id: str
    name: str
    description: str
    components: List[str]
    use_cases: List[str]
    pros: List[str]
    cons: List[str]
    examples: List[str]

@dataclass
class LearningEntry:
    """Learning from past experiences"""
    id: str
    timestamp: float
    description: str
    lesson: str
    context: str
    impact: str  # high, medium, low
    applied_count: int = 0

class MemoryManager:
    """
    Vector-based memory system for agent collaboration and learning
    """

    def __init__(
        self,
        max_memories: int = 10000,
        similarity_threshold: float = 0.7,
        auto_forget: bool = True,
        forget_threshold: float = 0.3
    ):
        # Core storage
        self.memories: Dict[str, MemoryEntry] = {}
        self.embeddings: Dict[str, np.ndarray] = {}

        # Pattern storage
        self.code_patterns: Dict[str, CodePattern] = {}
        self.architecture_patterns: Dict[str, ArchitecturePattern] = {}
        self.learning_entries: List[LearningEntry] = []

        # Indexes for fast lookup
        self.memory_index: Dict[MemoryType, Set[str]] = defaultdict(set)
        self.agent_memories: Dict[str, Set[str]] = defaultdict(set)
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)

        # Configuration
        self.max_memories = max_memories
        self.similarity_threshold = similarity_threshold
        self.auto_forget = auto_forget
        self.forget_threshold = forget_threshold

        # Statistics
        self.total_stored = 0
        self.total_searches = 0
        self.total_forgotten = 0

        logger.info(f"MemoryManager initialized with capacity: {max_memories}")

    async def store(
        self,
        agent_id: str,
        content: Any,
        memory_type: MemoryType,
        metadata: Optional[Dict] = None
    ) -> str:
        """Store a new memory with automatic embedding generation"""
        memory_id = self._generate_memory_id()

        # Generate embedding
        embedding = await self._generate_embedding(content)

        # Create metadata
        meta = MemoryMetadata(
            importance=metadata.get('importance', 0.5) if metadata else 0.5,
            tags=metadata.get('tags', []) if metadata else [],
            source=metadata.get('source', agent_id) if metadata else agent_id
        )

        # Create memory entry
        memory = MemoryEntry(
            id=memory_id,
            agent_id=agent_id,
            timestamp=time.time(),
            content=content,
            embedding=embedding,
            type=memory_type,
            metadata=meta
        )

        # Store memory
        self.memories[memory_id] = memory
        if embedding:
            self.embeddings[memory_id] = np.array(embedding)

        # Update indexes
        self.memory_index[memory_type].add(memory_id)
        self.agent_memories[agent_id].add(memory_id)

        for tag in meta.tags:
            self.tag_index[tag].add(memory_id)

        self.total_stored += 1

        # Auto-forget if needed
        if self.auto_forget and len(self.memories) > self.max_memories:
            await self._forget_old_memories()

        logger.debug(f"Stored memory {memory_id} for agent {agent_id}")
        return memory_id

    async def search(
        self,
        query: Any,
        k: int = 10,
        memory_type: Optional[MemoryType] = None,
        agent_id: Optional[str] = None,
        min_similarity: Optional[float] = None
    ) -> List[MemorySearchResult]:
        """Retrieve memories by semantic similarity"""
        if min_similarity is None:
            min_similarity = self.similarity_threshold

        # Generate query embedding
        query_embedding = await self._generate_embedding(query)
        if not query_embedding:
            return []

        query_vec = np.array(query_embedding)

        # Filter candidate memories
        candidates = self._filter_memories(memory_type, agent_id)

        # Calculate similarities and rank
        results = []
        for memory_id in candidates:
            memory = self.memories[memory_id]
            if memory_id in self.embeddings:
                similarity = self._cosine_similarity(
                    query_vec,
                    self.embeddings[memory_id]
                )

                if similarity >= min_similarity:
                    relevance = self._calculate_relevance(memory, similarity)

                    # Update access metadata
                    memory.metadata.access_count += 1
                    memory.metadata.last_accessed = time.time()

                    results.append(MemorySearchResult(
                        entry=memory,
                        similarity=similarity,
                        relevance=relevance
                    ))

        # Sort by relevance and limit
        results.sort(key=lambda x: x.relevance, reverse=True)
        self.total_searches += 1

        return results[:k]

    async def get_relevant_patterns(
        self,
        context: str,
        language: Optional[str] = None,
        limit: int = 5
    ) -> List[CodePattern]:
        """Get relevant code patterns for context"""
        patterns = list(self.code_patterns.values())

        # Filter by language if specified
        if language:
            patterns = [p for p in patterns if p.language == language]

        # Sort by relevance (success rate * recency)
        now = time.time()
        patterns.sort(
            key=lambda p: p.success_rate * (1 / (1 + (now - p.last_used) / 86400)),
            reverse=True
        )

        return patterns[:limit]

    def store_code_pattern(
        self,
        name: str,
        description: str,
        language: str,
        code: str,
        use_cases: List[str] = None
    ) -> str:
        """Store a reusable code pattern"""
        pattern_id = self._generate_memory_id()

        pattern = CodePattern(
            id=pattern_id,
            name=name,
            description=description,
            language=language,
            code=code,
            use_cases=use_cases or [],
            success_rate=1.0,
            usage_count=0,
            last_used=time.time()
        )

        self.code_patterns[pattern_id] = pattern
        logger.debug(f"Stored code pattern: {name}")
        return pattern_id

    def store_architecture_pattern(
        self,
        name: str,
        description: str,
        components: List[str],
        use_cases: List[str]
    ) -> str:
        """Store an architecture pattern"""
        pattern_id = self._generate_memory_id()

        pattern = ArchitecturePattern(
            id=pattern_id,
            name=name,
            description=description,
            components=components,
            use_cases=use_cases,
            pros=[],
            cons=[],
            examples=[]
        )

        self.architecture_patterns[pattern_id] = pattern
        logger.debug(f"Stored architecture pattern: {name}")
        return pattern_id

    def store_learning(
        self,
        description: str,
        lesson: str,
        context: str,
        impact: str = "medium"
    ) -> str:
        """Store a learning entry"""
        learning_id = self._generate_memory_id()

        learning = LearningEntry(
            id=learning_id,
            timestamp=time.time(),
            description=description,
            lesson=lesson,
            context=context,
            impact=impact
        )

        self.learning_entries.append(learning)
        logger.debug(f"Stored learning: {description}")
        return learning_id

    def get_relevant_learnings(
        self,
        context: str,
        limit: int = 5
    ) -> List[LearningEntry]:
        """Get learnings relevant to context"""
        # Simple keyword matching for now
        keywords = context.lower().split()

        scored_learnings = []
        for learning in self.learning_entries:
            score = 0
            learning_text = f"{learning.description} {learning.lesson}".lower()

            for keyword in keywords:
                if keyword in learning_text:
                    score += 1

            # Boost by impact
            if learning.impact == "high":
                score *= 3
            elif learning.impact == "medium":
                score *= 2

            # Boost by recency
            age_days = (time.time() - learning.timestamp) / 86400
            recency_boost = 1 / (1 + age_days / 30)
            score *= recency_boost

            if score > 0:
                scored_learnings.append((score, learning))

        # Sort and return top results
        scored_learnings.sort(key=lambda x: x[0], reverse=True)
        return [learning for _, learning in scored_learnings[:limit]]

    def get_agent_memories(
        self,
        agent_id: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 100
    ) -> List[MemoryEntry]:
        """Get memories for specific agent"""
        agent_memory_ids = self.agent_memories.get(agent_id, set())

        memories = []
        for memory_id in agent_memory_ids:
            memory = self.memories.get(memory_id)
            if memory:
                if memory_type is None or memory.type == memory_type:
                    memories.append(memory)

        # Sort by timestamp (most recent first)
        memories.sort(key=lambda m: m.timestamp, reverse=True)
        return memories[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        type_counts = {
            memory_type: len(ids)
            for memory_type, ids in self.memory_index.items()
        }

        agent_counts = {
            agent_id: len(ids)
            for agent_id, ids in self.agent_memories.items()
        }

        # Find most accessed memories
        most_accessed = sorted(
            self.memories.values(),
            key=lambda m: m.metadata.access_count,
            reverse=True
        )[:10]

        return {
            "total_memories": len(self.memories),
            "by_type": type_counts,
            "by_agent": agent_counts,
            "total_patterns": len(self.code_patterns) + len(self.architecture_patterns),
            "total_learnings": len(self.learning_entries),
            "most_accessed": [
                {"id": m.id, "count": m.metadata.access_count}
                for m in most_accessed
            ],
            "total_searches": self.total_searches,
            "total_forgotten": self.total_forgotten
        }

    async def _generate_embedding(self, content: Any) -> Optional[List[float]]:
        """
        Generate embedding for content
        TODO: Integrate with real embedding model (OpenAI, etc.)
        """
        # For now, use a simple hash-based approach
        text = json.dumps(content) if not isinstance(content, str) else content
        text = text.lower()

        # Create 384-dimensional embedding (matching typical embedding size)
        embedding = [0.0] * 384

        # Simple feature extraction
        for i, char in enumerate(text[:1000]):  # Limit to first 1000 chars
            idx = (ord(char) * (i + 1)) % 384
            embedding[idx] += 1.0

        # Normalize
        magnitude = np.sqrt(sum(v * v for v in embedding))
        if magnitude > 0:
            embedding = [v / magnitude for v in embedding]

        return embedding

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(a) != len(b) or len(a) == 0:
            return 0.0

        dot_product = np.dot(a, b)
        magnitude_a = np.linalg.norm(a)
        magnitude_b = np.linalg.norm(b)

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return float(dot_product / (magnitude_a * magnitude_b))

    def _calculate_relevance(
        self,
        memory: MemoryEntry,
        similarity: float
    ) -> float:
        """Calculate relevance score combining similarity, recency, importance"""
        # Recency factor (decay over time)
        age_days = (time.time() - memory.timestamp) / 86400
        recency = 1.0 / (1.0 + age_days / 7)  # Weekly decay

        # Importance from metadata
        importance = memory.metadata.importance

        # Access frequency (normalized)
        access_freq = min(1.0, memory.metadata.access_count / 100)

        # Combined relevance score
        relevance = (
            similarity * 0.4 +
            recency * 0.2 +
            importance * 0.3 +
            access_freq * 0.1
        )

        return relevance

    def _filter_memories(
        self,
        memory_type: Optional[MemoryType] = None,
        agent_id: Optional[str] = None
    ) -> Set[str]:
        """Filter memories by type and/or agent"""
        if memory_type and agent_id:
            type_memories = self.memory_index.get(memory_type, set())
            agent_mems = self.agent_memories.get(agent_id, set())
            return type_memories.intersection(agent_mems)
        elif memory_type:
            return self.memory_index.get(memory_type, set())
        elif agent_id:
            return self.agent_memories.get(agent_id, set())
        else:
            return set(self.memories.keys())

    async def _forget_old_memories(self):
        """Remove old, unimportant memories to maintain capacity"""
        memories_to_forget = []
        now = time.time()

        for memory_id, memory in self.memories.items():
            # Calculate retention score
            age_days = (now - memory.timestamp) / 86400
            access_rate = memory.metadata.access_count / max(1, age_days)
            importance = memory.metadata.importance

            retention_score = (
                access_rate * 0.4 +
                importance * 0.6
            )

            if retention_score < self.forget_threshold:
                memories_to_forget.append((retention_score, memory_id))

        # Sort by retention score (lowest first)
        memories_to_forget.sort(key=lambda x: x[0])

        # Forget enough to get below 80% capacity
        target_size = int(self.max_memories * 0.8)
        num_to_forget = max(0, len(self.memories) - target_size)

        for _, memory_id in memories_to_forget[:num_to_forget]:
            memory = self.memories.get(memory_id)
            if memory:
                # Remove from all indexes
                del self.memories[memory_id]
                if memory_id in self.embeddings:
                    del self.embeddings[memory_id]

                self.memory_index[memory.type].discard(memory_id)
                self.agent_memories[memory.agent_id].discard(memory_id)

                for tag in memory.metadata.tags:
                    self.tag_index[tag].discard(memory_id)

                self.total_forgotten += 1

        if num_to_forget > 0:
            logger.info(f"Forgot {num_to_forget} old memories")

    def _generate_memory_id(self) -> str:
        """Generate unique memory ID"""
        timestamp = str(time.time())
        random_str = hashlib.md5(timestamp.encode()).hexdigest()[:8]
        return f"mem_{timestamp}_{random_str}"

    def export_memories(self) -> str:
        """Export all memories to JSON"""
        export_data = {
            "memories": [
                {
                    "id": m.id,
                    "agent_id": m.agent_id,
                    "timestamp": m.timestamp,
                    "content": m.content,
                    "type": m.type.value,
                    "metadata": {
                        "importance": m.metadata.importance,
                        "access_count": m.metadata.access_count,
                        "tags": m.metadata.tags
                    }
                }
                for m in self.memories.values()
            ],
            "code_patterns": [
                {
                    "id": p.id,
                    "name": p.name,
                    "language": p.language,
                    "code": p.code
                }
                for p in self.code_patterns.values()
            ],
            "learnings": [
                {
                    "id": l.id,
                    "description": l.description,
                    "lesson": l.lesson,
                    "impact": l.impact
                }
                for l in self.learning_entries
            ],
            "timestamp": time.time()
        }

        return json.dumps(export_data, indent=2)

    def import_memories(self, data: str):
        """Import memories from JSON"""
        import_data = json.loads(data)

        # Clear existing data
        self.memories.clear()
        self.embeddings.clear()
        self.code_patterns.clear()
        self.learning_entries.clear()

        # Import memories
        for mem_data in import_data.get("memories", []):
            memory = MemoryEntry(
                id=mem_data["id"],
                agent_id=mem_data["agent_id"],
                timestamp=mem_data["timestamp"],
                content=mem_data["content"],
                embedding=None,  # Will regenerate if needed
                type=MemoryType(mem_data["type"]),
                metadata=MemoryMetadata(
                    importance=mem_data["metadata"]["importance"],
                    access_count=mem_data["metadata"]["access_count"],
                    tags=mem_data["metadata"]["tags"]
                )
            )
            self.memories[memory.id] = memory

        # Rebuild indexes
        self._rebuild_indexes()

        logger.info(f"Imported {len(self.memories)} memories")

    def _rebuild_indexes(self):
        """Rebuild all indexes after import"""
        self.memory_index.clear()
        self.agent_memories.clear()
        self.tag_index.clear()

        for memory_id, memory in self.memories.items():
            self.memory_index[memory.type].add(memory_id)
            self.agent_memories[memory.agent_id].add(memory_id)

            for tag in memory.metadata.tags:
                self.tag_index[tag].add(memory_id)

# Singleton instance
_memory_manager_instance = None

def get_memory_manager() -> MemoryManager:
    """Get singleton MemoryManager instance"""
    global _memory_manager_instance
    if _memory_manager_instance is None:
        _memory_manager_instance = MemoryManager()
    return _memory_manager_instance