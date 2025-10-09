"""
Predictive System v6 - Predict workflow duration and potential issues

Capabilities:
- Predict workflow execution time based on task complexity
- Anticipate potential issues before they occur
- Risk assessment for complex tasks
- Suggest preventive actions
- Integrate with Learning System for historical data

Integration:
- Before workflow start (in Supervisor)
- Uses Learning System's historical data
- Provides duration estimates and risk warnings

Author: KI AutoAgent Team
Version: 6.0.0
Python: 3.13+
"""

from __future__ import annotations

import logging
import re
import statistics
from typing import Any

logger = logging.getLogger(__name__)


class PredictiveSystemV6:
    """
    Predictive analysis system for workflow planning.

    Predicts execution time, identifies risks, and suggests
    preventive measures based on task complexity and history.
    """

    def __init__(self, learning_system: Any | None = None):
        """
        Initialize Predictive System.

        Args:
            learning_system: LearningSystemV6 instance for historical data
        """
        self.learning_system = learning_system
        logger.info("🔮 Predictive System v6 initialized")

    async def predict_workflow(
        self,
        task_description: str,
        project_type: str | None = None
    ) -> dict[str, Any]:
        """
        Predict workflow outcome before execution.

        Args:
            task_description: The task to predict
            project_type: Type of project (if known)

        Returns:
            dict with:
                - estimated_duration: float | None (seconds)
                - duration_range: tuple[float, float] | None (min, max)
                - risk_level: str ("low", "medium", "high")
                - risk_factors: list[str] (identified risks)
                - suggestions: list[str] (preventive actions)
                - confidence: float (0.0-1.0)
                - based_on_executions: int
        """
        logger.info(f"🔮 Predicting workflow for: {task_description[:60]}...")

        # Analyze task complexity
        complexity = self._analyze_complexity(task_description)
        logger.debug(f"   Complexity score: {complexity['score']:.2f}")

        # Get historical data from Learning System
        if self.learning_system and project_type:
            stats = await self.learning_system.get_project_type_statistics(project_type)
            historical_data = stats if stats["total_executions"] > 0 else None
        else:
            historical_data = None

        # Predict duration
        if historical_data:
            duration_pred = self._predict_duration_from_history(
                complexity,
                historical_data
            )
        else:
            duration_pred = self._predict_duration_from_complexity(complexity)

        # Assess risk
        risk_assessment = self._assess_risk(
            task_description,
            complexity,
            historical_data
        )

        # Generate suggestions
        suggestions = self._generate_suggestions(
            complexity,
            risk_assessment,
            historical_data
        )

        # Calculate confidence
        if historical_data:
            confidence = min(historical_data["total_executions"] / 10.0, 1.0)
        else:
            confidence = 0.3  # Low confidence without historical data

        result = {
            "estimated_duration": duration_pred["estimate"],
            "duration_range": duration_pred["range"],
            "risk_level": risk_assessment["level"],
            "risk_factors": risk_assessment["factors"],
            "suggestions": suggestions,
            "confidence": confidence,
            "based_on_executions": historical_data["total_executions"] if historical_data else 0,
            "complexity": complexity
        }

        logger.info(f"✅ Prediction complete:")
        logger.info(f"   Duration: {result['estimated_duration']:.1f}s (±{duration_pred.get('uncertainty', 10):.1f}s)")
        logger.info(f"   Risk: {result['risk_level']}")
        logger.info(f"   Confidence: {result['confidence']:.2%}")

        return result

    def _analyze_complexity(self, task_description: str) -> dict[str, Any]:
        """
        Analyze task complexity.

        Returns complexity score (0.0-1.0) and factors.
        """
        factors = []
        score = 0.0

        # Factor 1: Length (longer = more complex)
        word_count = len(task_description.split())
        if word_count < 10:
            length_score = 0.2
            factors.append("short_description")
        elif word_count < 30:
            length_score = 0.4
            factors.append("medium_description")
        else:
            length_score = 0.7
            factors.append("long_description")

        score += length_score * 0.2

        # Factor 2: Multiple technologies
        technologies = [
            "react", "vue", "angular",  # Frontend
            "node", "express", "fastapi", "django", "flask",  # Backend
            "postgresql", "mongodb", "redis",  # Databases
            "docker", "kubernetes",  # DevOps
            "auth", "jwt", "oauth"  # Auth
        ]

        tech_count = sum(1 for tech in technologies if tech in task_description.lower())
        tech_score = min(tech_count / 5.0, 1.0)
        if tech_count >= 3:
            factors.append(f"multiple_technologies_{tech_count}")
        score += tech_score * 0.3

        # Factor 3: Multiple features
        feature_keywords = ["with", "include", "support", "and", "plus"]
        feature_count = sum(1 for kw in feature_keywords if kw in task_description.lower())
        feature_score = min(feature_count / 5.0, 1.0)
        if feature_count >= 3:
            factors.append(f"multiple_features_{feature_count}")
        score += feature_score * 0.2

        # Factor 4: Complex patterns
        complex_patterns = [
            r"full.?stack",
            r"complete",
            r"entire",
            r"production.?ready",
            r"deployment",
            r"authentication",
            r"authorization",
            r"real.?time",
            r"microservice"
        ]

        complex_count = sum(1 for p in complex_patterns if re.search(p, task_description.lower()))
        complex_score = min(complex_count / 3.0, 1.0)
        if complex_count > 0:
            factors.extend([f"complex_requirement" for _ in range(complex_count)])
        score += complex_score * 0.3

        # Normalize score to 0.0-1.0
        score = min(score, 1.0)

        return {
            "score": score,
            "factors": factors,
            "word_count": word_count,
            "tech_count": tech_count,
            "feature_count": feature_count
        }

    def _predict_duration_from_history(
        self,
        complexity: dict[str, Any],
        historical_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Predict duration based on historical data."""
        base_duration = historical_data["avg_duration"]

        # Adjust based on complexity
        complexity_multiplier = 0.5 + (complexity["score"] * 1.5)
        estimated = base_duration * complexity_multiplier

        # Calculate range (±20% uncertainty)
        uncertainty = estimated * 0.2
        duration_range = (estimated - uncertainty, estimated + uncertainty)

        return {
            "estimate": estimated,
            "range": duration_range,
            "uncertainty": uncertainty,
            "method": "historical"
        }

    def _predict_duration_from_complexity(
        self,
        complexity: dict[str, Any]
    ) -> dict[str, Any]:
        """Predict duration based on complexity alone (no historical data)."""
        # Base duration: 30s for simple, 120s for complex
        base_duration = 30.0
        complexity_factor = complexity["score"] * 90.0  # Up to +90s
        estimated = base_duration + complexity_factor

        # Higher uncertainty without historical data
        uncertainty = estimated * 0.4
        duration_range = (estimated - uncertainty, estimated + uncertainty)

        return {
            "estimate": estimated,
            "range": duration_range,
            "uncertainty": uncertainty,
            "method": "complexity_based"
        }

    def _assess_risk(
        self,
        task_description: str,
        complexity: dict[str, Any],
        historical_data: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Assess risk level and identify risk factors."""
        risk_factors = []
        risk_score = 0.0

        # Risk 1: High complexity
        if complexity["score"] > 0.7:
            risk_factors.append("High task complexity")
            risk_score += 0.3

        # Risk 2: Multiple technologies
        if complexity["tech_count"] >= 3:
            risk_factors.append(f"Multiple technologies ({complexity['tech_count']} detected)")
            risk_score += 0.2

        # Risk 3: Historical low success rate
        if historical_data and historical_data["success_rate"] < 0.8:
            risk_factors.append(f"Low historical success rate ({historical_data['success_rate']:.0%})")
            risk_score += 0.3

        # Risk 4: Vague requirements
        if complexity["word_count"] < 10:
            risk_factors.append("Vague task description (may need clarification)")
            risk_score += 0.2

        # Risk 5: Specific high-risk keywords
        high_risk_keywords = [
            "production", "deploy", "migrate", "refactor",
            "authentication", "security", "payment", "billing"
        ]
        risky_keywords_found = [kw for kw in high_risk_keywords if kw in task_description.lower()]
        if risky_keywords_found:
            risk_factors.append(f"High-risk requirements: {', '.join(risky_keywords_found)}")
            risk_score += 0.1 * len(risky_keywords_found)

        # Determine risk level
        risk_score = min(risk_score, 1.0)
        if risk_score < 0.3:
            risk_level = "low"
        elif risk_score < 0.6:
            risk_level = "medium"
        else:
            risk_level = "high"

        return {
            "level": risk_level,
            "score": risk_score,
            "factors": risk_factors
        }

    def _generate_suggestions(
        self,
        complexity: dict[str, Any],
        risk_assessment: dict[str, Any],
        historical_data: dict[str, Any] | None
    ) -> list[str]:
        """Generate preventive suggestions."""
        suggestions = []

        # Suggestion 1: Based on complexity
        if complexity["score"] > 0.7:
            suggestions.append(
                "This is a complex task - consider breaking it into smaller iterations"
            )

        # Suggestion 2: Based on risk level
        if risk_assessment["level"] == "high":
            suggestions.append(
                "⚠️ High risk detected - review output carefully before deployment"
            )

        # Suggestion 3: Based on multiple technologies
        if complexity["tech_count"] >= 3:
            suggestions.append(
                f"Multiple technologies involved ({complexity['tech_count']}) - expect longer review time"
            )

        # Suggestion 4: Based on historical data
        if historical_data:
            if historical_data["success_rate"] < 0.8:
                suggestions.append(
                    f"Similar tasks have {historical_data['success_rate']:.0%} success rate - allow extra time for fixes"
                )

            if historical_data["avg_quality"] < 0.85:
                suggestions.append(
                    "Historical quality is moderate - plan for multiple review iterations"
                )

        # Suggestion 5: Vague requirements
        if complexity["word_count"] < 10:
            suggestions.append(
                "Task description is brief - consider using Curiosity System for clarifications"
            )

        # Default suggestion if none generated
        if not suggestions:
            suggestions.append(
                "Task appears straightforward - workflow should proceed smoothly"
            )

        return suggestions


# Export
__all__ = ["PredictiveSystemV6"]
