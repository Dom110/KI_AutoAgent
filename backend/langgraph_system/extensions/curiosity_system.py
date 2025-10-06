"""
Curiosity-Driven Task Selection System v1.0

Enables agents to prioritize novel and unexplored tasks over familiar ones.
Inspired by curiosity-driven learning in neuroscience and reinforcement learning.

Key Concepts:
- Novelty: How different is this task from previously encountered tasks?
- Exploration: Agents prefer novel tasks to avoid getting stuck in familiar patterns
- Exploitation: Agents still execute familiar tasks, but with lower priority
- Learning Rate: As agents encounter similar tasks, novelty decreases

Example:
    Task A: "Build authentication system" (done 10 times) → Low novelty (0.1)
    Task B: "Implement WebRTC video chat" (never done) → High novelty (0.95)
    Agent prioritizes Task B because it's novel and offers learning opportunity
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import json
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class TaskEncounter:
    """Records when an agent encountered a type of task"""
    task_id: str
    task_description: str
    timestamp: datetime = field(default_factory=datetime.now)
    task_embedding: Optional[List[float]] = None
    outcome: Optional[str] = None  # "success", "failure", "in_progress"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_description": self.task_description,
            "timestamp": self.timestamp.isoformat(),
            "task_embedding": self.task_embedding,
            "outcome": self.outcome
        }


@dataclass
class NoveltyScore:
    """Novelty assessment for a task"""
    task_description: str
    novelty: float  # 0.0 = completely familiar, 1.0 = completely novel
    closest_match: Optional[str]  # Most similar previous task
    similarity_score: float  # How similar to closest match
    exploration_priority: float  # Final priority considering novelty + other factors
    reasoning: str  # Why this novelty score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_description": self.task_description,
            "novelty": self.novelty,
            "closest_match": self.closest_match,
            "similarity_score": self.similarity_score,
            "exploration_priority": self.exploration_priority,
            "reasoning": self.reasoning
        }


class NoveltyCalculator:
    """
    Calculates how novel a task is based on agent's history

    Uses semantic similarity (embeddings) to compare tasks
    """

    def __init__(self, embedding_function=None):
        """
        Initialize novelty calculator

        Args:
            embedding_function: Function to convert text to embeddings (e.g., OpenAI embeddings)
        """
        self.embedding_function = embedding_function
        self.novelty_threshold = 0.7  # Below this similarity = novel task

    def calculate_novelty(
        self,
        task_description: str,
        task_embedding: Optional[List[float]],
        history: List[TaskEncounter]
    ) -> NoveltyScore:
        """
        Calculate how novel a task is compared to history

        Args:
            task_description: The task to evaluate
            task_embedding: Pre-computed embedding (optional)
            history: Previous task encounters

        Returns:
            NoveltyScore with novelty assessment
        """
        if not history:
            # No history = completely novel
            return NoveltyScore(
                task_description=task_description,
                novelty=1.0,
                closest_match=None,
                similarity_score=0.0,
                exploration_priority=1.0,
                reasoning="No previous task history - completely novel"
            )

        # If no embeddings available, fall back to keyword matching
        if task_embedding is None or not any(h.task_embedding for h in history):
            return self._calculate_keyword_novelty(task_description, history)

        # Calculate semantic similarity with all previous tasks
        similarities = []
        for encounter in history:
            if encounter.task_embedding:
                similarity = self._cosine_similarity(task_embedding, encounter.task_embedding)
                similarities.append((similarity, encounter))

        if not similarities:
            # No embeddings in history
            return self._calculate_keyword_novelty(task_description, history)

        # Find most similar previous task
        max_similarity, closest_encounter = max(similarities, key=lambda x: x[0])

        # Novelty = 1 - similarity (higher similarity = lower novelty)
        novelty = 1.0 - max_similarity

        # Adjust novelty based on outcome of similar tasks
        # If agent failed similar tasks, increase novelty slightly (still challenging)
        if closest_encounter.outcome == "failure":
            novelty = min(1.0, novelty * 1.2)
            reasoning = f"Similar to failed task '{closest_encounter.task_description[:50]}...' - still challenging"
        elif max_similarity > 0.9:
            reasoning = f"Very similar to '{closest_encounter.task_description[:50]}...' - routine task"
        elif max_similarity > self.novelty_threshold:
            reasoning = f"Somewhat similar to '{closest_encounter.task_description[:50]}...' - familiar pattern"
        else:
            reasoning = f"Different from previous tasks - novel territory"

        # Exploration priority = novelty with bonus for completely new domains
        exploration_priority = novelty
        if novelty > 0.8:
            exploration_priority = min(1.0, novelty * 1.1)  # Bonus for very novel tasks

        return NoveltyScore(
            task_description=task_description,
            novelty=novelty,
            closest_match=closest_encounter.task_description,
            similarity_score=max_similarity,
            exploration_priority=exploration_priority,
            reasoning=reasoning
        )

    def _calculate_keyword_novelty(
        self,
        task_description: str,
        history: List[TaskEncounter]
    ) -> NoveltyScore:
        """
        Fallback: Calculate novelty using keyword overlap

        Less accurate than embeddings but works without embedding service
        """
        task_keywords = set(task_description.lower().split())

        max_overlap = 0.0
        closest_match = None

        for encounter in history:
            history_keywords = set(encounter.task_description.lower().split())

            # Jaccard similarity
            intersection = task_keywords & history_keywords
            union = task_keywords | history_keywords

            if union:
                similarity = len(intersection) / len(union)
                if similarity > max_overlap:
                    max_overlap = similarity
                    closest_match = encounter.task_description

        novelty = 1.0 - max_overlap

        if max_overlap > 0.7:
            reasoning = f"Many shared keywords with '{closest_match[:50]}...' - familiar task"
        elif max_overlap > 0.3:
            reasoning = f"Some shared keywords with '{closest_match[:50]}...' - related task"
        else:
            reasoning = "Few shared keywords - novel task type"

        return NoveltyScore(
            task_description=task_description,
            novelty=novelty,
            closest_match=closest_match,
            similarity_score=max_overlap,
            exploration_priority=novelty,
            reasoning=reasoning
        )

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0

        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)

        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))


class CuriosityModule:
    """
    Manages curiosity-driven exploration for an agent

    Tracks task history and calculates novelty scores to prioritize
    unexplored areas of the problem space
    """

    def __init__(
        self,
        agent_name: str,
        storage_path: Optional[str] = None,
        embedding_function=None
    ):
        """
        Initialize curiosity module

        Args:
            agent_name: Name of the agent
            storage_path: Optional path to persist exploration history
            embedding_function: Function to generate embeddings
        """
        self.agent_name = agent_name
        self.storage_path = storage_path

        # Task encounter history
        self.task_history: List[TaskEncounter] = []

        # Task category statistics
        self.category_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "successes": 0,
            "failures": 0,
            "last_encounter": None
        })

        # Novelty calculator
        self.novelty_calculator = NoveltyCalculator(embedding_function)

        # Exploration vs exploitation balance (0.0 = pure exploitation, 1.0 = pure exploration)
        self.exploration_weight = 0.3  # 30% curiosity, 70% task importance

        logger.info(f"🔍 CuriosityModule initialized for agent: {agent_name}")

    def record_task_encounter(
        self,
        task_id: str,
        task_description: str,
        task_embedding: Optional[List[float]] = None,
        outcome: Optional[str] = None,
        category: Optional[str] = None
    ):
        """
        Record that agent encountered a task

        Args:
            task_id: Unique task identifier
            task_description: Human-readable task description
            task_embedding: Optional embedding for semantic comparison
            outcome: "success", "failure", or None if in progress
            category: Optional task category (e.g., "authentication", "database")
        """
        encounter = TaskEncounter(
            task_id=task_id,
            task_description=task_description,
            task_embedding=task_embedding,
            outcome=outcome
        )

        self.task_history.append(encounter)

        # Update category statistics
        if category:
            stats = self.category_stats[category]
            stats["count"] += 1
            stats["last_encounter"] = datetime.now().isoformat()

            if outcome == "success":
                stats["successes"] += 1
            elif outcome == "failure":
                stats["failures"] += 1

        logger.info(f"📝 [{self.agent_name}] Recorded task encounter: {task_description[:50]}...")
        if outcome:
            logger.info(f"   Outcome: {outcome}")

    def calculate_task_priority(
        self,
        task_description: str,
        base_priority: float,
        task_embedding: Optional[List[float]] = None,
        category: Optional[str] = None
    ) -> Tuple[float, NoveltyScore]:
        """
        Calculate final task priority considering both importance and novelty

        Args:
            task_description: The task to evaluate
            base_priority: Base priority from task importance (0.0-1.0)
            task_embedding: Optional pre-computed embedding
            category: Optional task category

        Returns:
            (final_priority, novelty_score)
        """
        # Calculate novelty
        novelty_score = self.novelty_calculator.calculate_novelty(
            task_description,
            task_embedding,
            self.task_history
        )

        # Combine base priority with exploration priority
        # exploration_weight determines how much we favor novel tasks
        final_priority = (
            (1 - self.exploration_weight) * base_priority +
            self.exploration_weight * novelty_score.exploration_priority
        )

        logger.info(f"🎯 [{self.agent_name}] Task priority calculation:")
        logger.info(f"   Task: {task_description[:60]}...")
        logger.info(f"   Base priority: {base_priority:.2f}")
        logger.info(f"   Novelty: {novelty_score.novelty:.2f}")
        logger.info(f"   Final priority: {final_priority:.2f}")
        logger.info(f"   Reasoning: {novelty_score.reasoning}")

        return final_priority, novelty_score

    def get_exploration_summary(self) -> Dict[str, Any]:
        """Get summary of exploration history"""
        if not self.task_history:
            return {
                "total_tasks": 0,
                "unique_categories": 0,
                "exploration_breadth": 0.0
            }

        total = len(self.task_history)
        categories = len(self.category_stats)

        # Exploration breadth = how evenly distributed across categories
        if categories > 0:
            category_counts = [stats["count"] for stats in self.category_stats.values()]
            # Standard deviation of category counts (normalized)
            breadth = 1.0 - (np.std(category_counts) / (np.mean(category_counts) + 1e-6))
            breadth = max(0.0, min(1.0, breadth))
        else:
            breadth = 0.0

        return {
            "total_tasks": total,
            "unique_categories": categories,
            "exploration_breadth": breadth,
            "category_stats": dict(self.category_stats)
        }

    def set_exploration_weight(self, weight: float):
        """
        Adjust exploration vs exploitation balance

        Args:
            weight: 0.0 = pure exploitation (ignore novelty),
                   1.0 = pure exploration (maximize novelty)
        """
        self.exploration_weight = max(0.0, min(1.0, weight))
        logger.info(f"🔄 [{self.agent_name}] Exploration weight set to {self.exploration_weight:.2f}")

    def save_to_disk(self):
        """Persist exploration history to disk"""
        if not self.storage_path:
            return

        data = {
            "agent_name": self.agent_name,
            "task_history": [e.to_dict() for e in self.task_history],
            "category_stats": dict(self.category_stats),
            "exploration_weight": self.exploration_weight,
            "summary": self.get_exploration_summary()
        }

        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"💾 Saved curiosity module to {self.storage_path}")

    def load_from_disk(self):
        """Load exploration history from disk"""
        if not self.storage_path:
            return

        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)

            # Restore task history (without reconstructing full objects)
            # We only need the essential fields for novelty calculation
            for task_data in data.get("task_history", []):
                encounter = TaskEncounter(
                    task_id=task_data["task_id"],
                    task_description=task_data["task_description"],
                    task_embedding=task_data.get("task_embedding"),
                    outcome=task_data.get("outcome")
                )
                self.task_history.append(encounter)

            self.category_stats = defaultdict(lambda: {
                "count": 0,
                "successes": 0,
                "failures": 0,
                "last_encounter": None
            }, data.get("category_stats", {}))

            self.exploration_weight = data.get("exploration_weight", 0.3)

            logger.info(f"📂 Loaded curiosity module from {self.storage_path}")
            logger.info(f"   Task history: {len(self.task_history)} tasks")
            logger.info(f"   Categories: {len(self.category_stats)}")
        except FileNotFoundError:
            logger.info(f"📂 No existing curiosity data found at {self.storage_path}")
