"""
Learning System v6 - Learn from workflow outcomes and adapt strategies

Capabilities:
- Pattern learning from workflow execution
- Strategy adaptation based on success/failure
- Performance tracking (execution time, quality scores)
- Project-type-specific learnings
- Improvement suggestions based on history

Integration:
- Post-workflow analysis (after ReviewFix completion)
- Memory System v6 for persistent storage
- Workflow metrics tracking

Author: KI AutoAgent Team
Version: 6.0.0
Python: 3.13+
"""

from __future__ import annotations

import logging
import statistics
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class LearningSystemV6:
    """
    Adaptive learning system that improves from experience.

    Tracks workflow outcomes, identifies patterns, and suggests
    optimizations for future executions.
    """

    def __init__(self, memory: Any | None = None):
        """
        Initialize Learning System.

        Args:
            memory: Memory system instance for persistent storage
        """
        self.memory = memory
        self.session_history: list[dict[str, Any]] = []
        logger.info("🧠 Learning System v6 initialized")

    async def record_workflow_execution(
        self,
        workflow_id: str,
        task_description: str,
        project_type: str | None,
        execution_metrics: dict[str, Any],
        quality_score: float,
        status: str,
        errors: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Record a workflow execution for learning.

        Args:
            workflow_id: Unique workflow execution ID
            task_description: Description of the task
            project_type: Type of project (e.g., "calculator", "web_app", "api")
            execution_metrics: Metrics dict with:
                - total_time: float (seconds)
                - research_time: float (seconds)
                - architect_time: float (seconds)
                - codesmith_time: float (seconds)
                - review_iterations: int
                - files_generated: int
                - lines_of_code: int
            quality_score: Quality score from ReviewFix (0.0-1.0)
            status: "success" or "error"
            errors: List of error messages (if any)

        Returns:
            Learning record dict
        """
        logger.info(f"📝 Recording workflow execution: {workflow_id}")

        # Create learning record
        record = {
            "workflow_id": workflow_id,
            "timestamp": datetime.now().isoformat(),
            "task_description": task_description[:500],  # Limit length
            "project_type": project_type or "unknown",
            "execution_metrics": execution_metrics,
            "quality_score": quality_score,
            "status": status,
            "errors": errors or [],
            "success": status == "success" and quality_score >= 0.75
        }

        # Add to session history
        self.session_history.append(record)

        # Store in Memory if available
        if self.memory:
            await self._store_in_memory(record)

        # Analyze for patterns
        if record["success"]:
            pattern = await self._extract_success_pattern(record)
            logger.debug(f"✅ Success pattern extracted: {pattern}")

        logger.info(f"✅ Workflow execution recorded (quality: {quality_score:.2f}, status: {status})")
        return record

    async def suggest_optimizations(
        self,
        task_description: str,
        project_type: str | None = None
    ) -> dict[str, Any]:
        """
        Suggest optimizations based on learned patterns.

        Args:
            task_description: Description of upcoming task
            project_type: Type of project

        Returns:
            dict with:
                - suggestions: list[str] (actionable suggestions)
                - expected_duration: float (seconds, estimated)
                - confidence: float (0.0-1.0)
                - based_on: int (number of similar executions)
        """
        logger.info(f"💡 Generating suggestions for project_type: {project_type}")

        # Find similar successful executions
        similar_executions = await self._find_similar_executions(
            task_description,
            project_type
        )

        if not similar_executions:
            logger.debug("No similar executions found - returning default suggestions")
            return {
                "suggestions": [
                    "This is a new type of task - no historical data available",
                    "Workflow will run with default settings"
                ],
                "expected_duration": None,
                "confidence": 0.0,
                "based_on": 0
            }

        # Calculate statistics from similar executions
        execution_times = [e["execution_metrics"]["total_time"] for e in similar_executions]
        quality_scores = [e["quality_score"] for e in similar_executions]
        review_iterations = [e["execution_metrics"].get("review_iterations", 1) for e in similar_executions]

        avg_duration = statistics.mean(execution_times)
        avg_quality = statistics.mean(quality_scores)
        avg_reviews = statistics.mean(review_iterations)

        # Generate suggestions
        suggestions = []

        # Suggestion 1: Duration estimate
        suggestions.append(
            f"Expected duration: ~{int(avg_duration)}s (based on {len(similar_executions)} similar tasks)"
        )

        # Suggestion 2: Quality insights
        if avg_quality > 0.9:
            suggestions.append(
                f"Similar {project_type} projects typically achieve high quality (avg: {avg_quality:.2f})"
            )
        elif avg_quality < 0.8:
            suggestions.append(
                f"⚠️ Similar tasks average {avg_quality:.2f} quality - consider extra review"
            )

        # Suggestion 3: Review iterations
        if avg_reviews > 2:
            suggestions.append(
                f"Similar tasks required {avg_reviews:.1f} review iterations on average - plan accordingly"
            )

        # Suggestion 4: Common issues
        common_errors = self._extract_common_errors(similar_executions)
        if common_errors:
            suggestions.append(
                f"⚠️ Common issues in {project_type}: {', '.join(common_errors[:3])}"
            )

        # Suggestion 5: Best practices
        if project_type:
            best_practices = await self._get_best_practices(project_type)
            if best_practices:
                suggestions.extend(best_practices)

        confidence = min(len(similar_executions) / 10.0, 1.0)  # Max confidence at 10+ executions

        result = {
            "suggestions": suggestions,
            "expected_duration": avg_duration,
            "confidence": confidence,
            "based_on": len(similar_executions),
            "avg_quality": avg_quality
        }

        logger.info(f"✅ Generated {len(suggestions)} suggestions (confidence: {confidence:.2f})")
        return result

    async def get_project_type_statistics(
        self,
        project_type: str
    ) -> dict[str, Any]:
        """
        Get statistics for a specific project type.

        Args:
            project_type: Type of project (e.g., "calculator", "web_app")

        Returns:
            Statistics dict with success rate, avg time, etc.
        """
        logger.debug(f"📊 Getting statistics for project_type: {project_type}")

        # Load from memory if available
        if self.memory:
            records = await self._load_from_memory(project_type=project_type)
        else:
            records = [r for r in self.session_history if r["project_type"] == project_type]

        if not records:
            return {
                "project_type": project_type,
                "total_executions": 0,
                "success_rate": 0.0,
                "avg_duration": 0.0,
                "avg_quality": 0.0
            }

        total = len(records)
        successes = sum(1 for r in records if r["success"])
        durations = [r["execution_metrics"]["total_time"] for r in records]
        qualities = [r["quality_score"] for r in records]

        return {
            "project_type": project_type,
            "total_executions": total,
            "success_rate": successes / total,
            "avg_duration": statistics.mean(durations),
            "avg_quality": statistics.mean(qualities),
            "last_execution": records[-1]["timestamp"] if records else None
        }

    async def get_overall_statistics(self) -> dict[str, Any]:
        """
        Get overall learning system statistics.

        Returns:
            Overall statistics dict
        """
        # Load all records
        if self.memory:
            all_records = await self._load_all_from_memory()
        else:
            all_records = self.session_history

        if not all_records:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "avg_duration": 0.0,
                "avg_quality": 0.0,
                "project_types": {}
            }

        total = len(all_records)
        successes = sum(1 for r in all_records if r["success"])
        durations = [r["execution_metrics"]["total_time"] for r in all_records]
        qualities = [r["quality_score"] for r in all_records]

        # Group by project type
        project_types = {}
        for record in all_records:
            pt = record["project_type"]
            if pt not in project_types:
                project_types[pt] = {"count": 0, "successes": 0}
            project_types[pt]["count"] += 1
            if record["success"]:
                project_types[pt]["successes"] += 1

        # Calculate success rates per type
        for pt, stats in project_types.items():
            stats["success_rate"] = stats["successes"] / stats["count"]

        return {
            "total_executions": total,
            "success_rate": successes / total,
            "avg_duration": statistics.mean(durations),
            "avg_quality": statistics.mean(qualities),
            "project_types": project_types,
            "last_updated": datetime.now().isoformat()
        }

    # ========================================================================
    # PRIVATE METHODS
    # ========================================================================

    async def _store_in_memory(self, record: dict[str, Any]) -> None:
        """Store learning record in Memory system."""
        if not self.memory:
            return

        try:
            await self.memory.store(
                content=f"Workflow execution: {record['task_description']}",
                metadata={
                    "type": "learning_record",
                    "workflow_id": record["workflow_id"],
                    "project_type": record["project_type"],
                    "quality_score": record["quality_score"],
                    "status": record["status"],
                    "timestamp": record["timestamp"],
                    "execution_time": record["execution_metrics"]["total_time"]
                }
            )
            logger.debug(f"💾 Learning record stored in Memory")
        except Exception as e:
            logger.warning(f"⚠️  Failed to store in Memory: {e}")

    async def _load_from_memory(
        self,
        project_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Load learning records from Memory."""
        if not self.memory:
            return []

        try:
            # Search for learning records
            query = f"project_type: {project_type}" if project_type else "type: learning_record"
            results = await self.memory.search(
                query=query,
                filters={"type": "learning_record"},
                k=100
            )

            records = []
            for result in results:
                metadata = result.get("metadata", {})
                # Reconstruct record from metadata
                record = {
                    "workflow_id": metadata.get("workflow_id", ""),
                    "timestamp": metadata.get("timestamp", ""),
                    "task_description": result.get("content", ""),
                    "project_type": metadata.get("project_type", "unknown"),
                    "execution_metrics": {"total_time": metadata.get("execution_time", 0.0)},
                    "quality_score": metadata.get("quality_score", 0.0),
                    "status": metadata.get("status", "unknown"),
                    "success": metadata.get("status") == "success"
                }
                records.append(record)

            return records

        except Exception as e:
            logger.warning(f"⚠️  Failed to load from Memory: {e}")
            return []

    async def _load_all_from_memory(self) -> list[dict[str, Any]]:
        """Load ALL learning records from Memory."""
        return await self._load_from_memory(project_type=None)

    async def _find_similar_executions(
        self,
        task_description: str,
        project_type: str | None
    ) -> list[dict[str, Any]]:
        """Find executions similar to the given task."""
        # Load records
        if self.memory:
            all_records = await self._load_from_memory(project_type=project_type)
        else:
            all_records = self.session_history

        # Filter successful executions of same type
        similar = [
            r for r in all_records
            if r["success"] and (not project_type or r["project_type"] == project_type)
        ]

        # Sort by quality score (best first)
        similar.sort(key=lambda r: r["quality_score"], reverse=True)

        return similar[:10]  # Return top 10

    async def _extract_success_pattern(
        self,
        record: dict[str, Any]
    ) -> dict[str, Any]:
        """Extract success pattern from a successful execution."""
        return {
            "project_type": record["project_type"],
            "quality_score": record["quality_score"],
            "execution_time": record["execution_metrics"]["total_time"],
            "review_iterations": record["execution_metrics"].get("review_iterations", 1),
            "pattern": "success"
        }

    def _extract_common_errors(
        self,
        executions: list[dict[str, Any]]
    ) -> list[str]:
        """Extract common errors from execution history."""
        error_counts: dict[str, int] = {}

        for execution in executions:
            for error in execution.get("errors", []):
                # Extract error type (first 50 chars)
                error_key = error[:50]
                error_counts[error_key] = error_counts.get(error_key, 0) + 1

        # Sort by frequency
        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)

        # Return top 3 most common
        return [error for error, count in sorted_errors[:3] if count > 1]

    async def _get_best_practices(
        self,
        project_type: str
    ) -> list[str]:
        """Get best practices for a project type based on successful executions."""
        # This would be enhanced with actual analysis
        # For now, return project-type-specific tips
        best_practices_db = {
            "calculator": [
                "Include input validation for all operations",
                "Consider adding history tracking",
                "Implement error handling for division by zero"
            ],
            "web_app": [
                "Implement proper error handling for all routes",
                "Add input validation and sanitization",
                "Consider adding logging for debugging"
            ],
            "api": [
                "Include request validation",
                "Implement rate limiting",
                "Add comprehensive error responses"
            ]
        }

        return best_practices_db.get(project_type, [])


# Export
__all__ = ["LearningSystemV6"]
