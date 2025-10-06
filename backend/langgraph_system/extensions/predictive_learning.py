"""
Predictive Error Learning System v1.0

Enables agents to learn from prediction errors by comparing expected outcomes
with actual results. This is inspired by predictive processing in neuroscience.

Key Concepts:
- Prediction: Agent predicts outcome before action
- Reality: Actual outcome after action execution
- Error: Difference between prediction and reality
- Learning: Update internal model based on error

Example:
    Agent predicts: "Code will pass tests with 90% confidence"
    Reality: Tests fail due to edge case
    Error: 0.9 - 0.0 = 0.9 (large error)
    Learning: Update model to better predict edge case failures
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


@dataclass
class Prediction:
    """A prediction made by an agent before taking action"""
    task_id: str
    agent_name: str
    action: str  # What the agent is about to do
    expected_outcome: str  # What the agent expects to happen
    confidence: float  # How confident (0.0 to 1.0)
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "action": self.action,
            "expected_outcome": self.expected_outcome,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context
        }


@dataclass
class Reality:
    """The actual outcome after action execution"""
    task_id: str
    actual_outcome: str  # What actually happened
    success: bool  # Did it succeed?
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "actual_outcome": self.actual_outcome,
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class PredictionError:
    """The error between prediction and reality"""
    task_id: str
    agent_name: str
    prediction: Prediction
    reality: Reality
    error_magnitude: float  # How wrong was the prediction (0.0 = perfect, 1.0 = completely wrong)
    surprise_factor: float  # How unexpected was the outcome
    learning_opportunity: str  # What can be learned
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "prediction": self.prediction.to_dict(),
            "reality": self.reality.to_dict(),
            "error_magnitude": self.error_magnitude,
            "surprise_factor": self.surprise_factor,
            "learning_opportunity": self.learning_opportunity,
            "timestamp": self.timestamp.isoformat()
        }


class PredictiveMemory:
    """
    Manages predictions, reality tracking, and learning from errors

    This system enables agents to:
    1. Make predictions before actions
    2. Record actual outcomes
    3. Calculate prediction errors
    4. Learn patterns from repeated errors
    5. Improve future predictions
    """

    def __init__(self, agent_name: str, storage_path: Optional[str] = None):
        """
        Initialize predictive memory for an agent

        Args:
            agent_name: Name of the agent using this memory
            storage_path: Optional path to persist predictions/errors
        """
        self.agent_name = agent_name
        self.storage_path = storage_path

        # Active predictions waiting for reality
        self.pending_predictions: Dict[str, Prediction] = {}

        # Historical prediction errors for learning
        self.error_history: List[PredictionError] = []

        # Learned patterns from repeated errors
        self.learned_patterns: Dict[str, Any] = {}

        logger.info(f"✨ PredictiveMemory initialized for agent: {agent_name}")

    def make_prediction(
        self,
        task_id: str,
        action: str,
        expected_outcome: str,
        confidence: float,
        context: Optional[Dict[str, Any]] = None
    ) -> Prediction:
        """
        Agent makes a prediction before taking action

        Args:
            task_id: Unique identifier for this task
            action: What the agent is about to do
            expected_outcome: What the agent expects to happen
            confidence: How confident (0.0 to 1.0)
            context: Additional context

        Returns:
            Prediction object
        """
        prediction = Prediction(
            task_id=task_id,
            agent_name=self.agent_name,
            action=action,
            expected_outcome=expected_outcome,
            confidence=confidence,
            context=context or {}
        )

        self.pending_predictions[task_id] = prediction

        logger.info(f"🔮 [{self.agent_name}] Prediction made for task {task_id}")
        logger.info(f"   Expected: {expected_outcome[:100]}")
        logger.info(f"   Confidence: {confidence:.2f}")

        return prediction

    def record_reality(
        self,
        task_id: str,
        actual_outcome: str,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[PredictionError]:
        """
        Record what actually happened and calculate prediction error

        Args:
            task_id: Task identifier
            actual_outcome: What actually happened
            success: Did the action succeed?
            metadata: Additional outcome data

        Returns:
            PredictionError if prediction existed, None otherwise
        """
        # Check if we had a prediction for this task
        prediction = self.pending_predictions.pop(task_id, None)
        if not prediction:
            logger.warning(f"⚠️ No prediction found for task {task_id} - cannot calculate error")
            return None

        # Create reality record
        reality = Reality(
            task_id=task_id,
            actual_outcome=actual_outcome,
            success=success,
            metadata=metadata or {}
        )

        # Calculate prediction error
        error = self._calculate_error(prediction, reality)

        # Store in history
        self.error_history.append(error)

        # Learn from error
        self._learn_from_error(error)

        logger.info(f"📊 [{self.agent_name}] Reality recorded for task {task_id}")
        logger.info(f"   Actual: {actual_outcome[:100]}")
        logger.info(f"   Success: {success}")
        logger.info(f"   Error Magnitude: {error.error_magnitude:.2f}")
        logger.info(f"   Surprise Factor: {error.surprise_factor:.2f}")

        if error.error_magnitude > 0.5:
            logger.warning(f"⚠️ Large prediction error detected!")
            logger.warning(f"   Learning opportunity: {error.learning_opportunity}")

        return error

    def _calculate_error(self, prediction: Prediction, reality: Reality) -> PredictionError:
        """
        Calculate the prediction error

        Error magnitude = how wrong was the prediction
        Surprise factor = how unexpected given confidence level
        """
        # Simple heuristic: if success != expected, high error
        # In production, use more sophisticated comparison (embeddings, etc.)

        expected_success = "success" in prediction.expected_outcome.lower() or \
                          "pass" in prediction.expected_outcome.lower() or \
                          "work" in prediction.expected_outcome.lower()

        outcome_matches = (expected_success == reality.success)

        # Error magnitude: 0.0 if perfect prediction, 1.0 if completely wrong
        if outcome_matches:
            error_magnitude = 0.0  # Perfect prediction
        else:
            error_magnitude = 1.0  # Wrong prediction

        # Surprise factor: high confidence + wrong = high surprise
        if not outcome_matches:
            surprise_factor = prediction.confidence
        else:
            surprise_factor = 0.0

        # Learning opportunity
        if error_magnitude > 0.5:
            learning_opportunity = f"Expected '{prediction.expected_outcome}' but got '{reality.actual_outcome}'. " \
                                 f"Context: {prediction.context}"
        else:
            learning_opportunity = "Prediction was accurate, no learning needed"

        return PredictionError(
            task_id=prediction.task_id,
            agent_name=self.agent_name,
            prediction=prediction,
            reality=reality,
            error_magnitude=error_magnitude,
            surprise_factor=surprise_factor,
            learning_opportunity=learning_opportunity
        )

    def _learn_from_error(self, error: PredictionError):
        """
        Learn patterns from prediction errors

        This updates internal learned_patterns to improve future predictions
        """
        # Extract pattern key from error
        action_type = error.prediction.action[:50]  # First 50 chars

        if action_type not in self.learned_patterns:
            self.learned_patterns[action_type] = {
                "total_predictions": 0,
                "total_errors": 0,
                "error_sum": 0.0,
                "common_failures": []
            }

        pattern = self.learned_patterns[action_type]
        pattern["total_predictions"] += 1

        if error.error_magnitude > 0.5:
            pattern["total_errors"] += 1
            pattern["error_sum"] += error.error_magnitude

            # Track common failure modes
            failure_desc = error.reality.actual_outcome[:100]
            pattern["common_failures"].append(failure_desc)

            # Keep only last 10 failures
            if len(pattern["common_failures"]) > 10:
                pattern["common_failures"] = pattern["common_failures"][-10:]

        # Calculate accuracy rate
        accuracy = 1.0 - (pattern["total_errors"] / pattern["total_predictions"])
        pattern["accuracy"] = accuracy

        logger.info(f"📚 Learning pattern for '{action_type[:30]}...'")
        logger.info(f"   Accuracy: {accuracy:.2%} ({pattern['total_predictions']} predictions)")

    def get_prediction_confidence_adjustment(self, action: str) -> float:
        """
        Get confidence adjustment based on learned patterns

        Args:
            action: The action being considered

        Returns:
            Confidence multiplier (1.0 = no adjustment, <1.0 = reduce confidence)
        """
        action_type = action[:50]

        if action_type not in self.learned_patterns:
            return 1.0  # No historical data, use original confidence

        pattern = self.learned_patterns[action_type]
        accuracy = pattern.get("accuracy", 1.0)

        # If historical accuracy is low, reduce confidence
        return accuracy

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of prediction errors for analysis"""
        if not self.error_history:
            return {
                "total_predictions": 0,
                "total_errors": 0,
                "average_error": 0.0,
                "average_surprise": 0.0
            }

        total = len(self.error_history)
        errors_count = sum(1 for e in self.error_history if e.error_magnitude > 0.5)
        avg_error = sum(e.error_magnitude for e in self.error_history) / total
        avg_surprise = sum(e.surprise_factor for e in self.error_history) / total

        return {
            "total_predictions": total,
            "total_errors": errors_count,
            "error_rate": errors_count / total if total > 0 else 0.0,
            "average_error": avg_error,
            "average_surprise": avg_surprise,
            "learned_patterns": len(self.learned_patterns)
        }

    def save_to_disk(self):
        """Persist predictions and errors to disk"""
        if not self.storage_path:
            return

        data = {
            "agent_name": self.agent_name,
            "error_history": [e.to_dict() for e in self.error_history],
            "learned_patterns": self.learned_patterns,
            "summary": self.get_error_summary()
        }

        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"💾 Saved predictive memory to {self.storage_path}")

    def load_from_disk(self):
        """Load predictions and errors from disk"""
        if not self.storage_path:
            return

        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)

            self.learned_patterns = data.get("learned_patterns", {})
            logger.info(f"📂 Loaded predictive memory from {self.storage_path}")
            logger.info(f"   Learned patterns: {len(self.learned_patterns)}")
        except FileNotFoundError:
            logger.info(f"📂 No existing predictive memory found at {self.storage_path}")
