"""
Curiosity System v6 - Identify knowledge gaps and ask clarifying questions

Capabilities:
- Detect ambiguous or incomplete task descriptions
- Identify missing requirements
- Generate clarifying questions
- Memory-based context analysis
- Proactive requirement gathering

Integration:
- Before Architect design phase
- Prevents poor outcomes from unclear requirements
- Improves workflow quality through better initial context

Author: KI AutoAgent Team
Version: 6.0.0
Python: 3.13+
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class CuriositySystemV6:
    """
    Curiosity-driven system that identifies knowledge gaps.

    Analyzes task descriptions to find missing information and
    generates clarifying questions to improve workflow outcomes.
    """

    def __init__(self, memory: Any | None = None):
        """
        Initialize Curiosity System.

        Args:
            memory: Memory system instance for context analysis
        """
        self.memory = memory
        logger.info("🤔 Curiosity System v6 initialized")

    async def analyze_task(
        self,
        task_description: str,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Analyze a task for knowledge gaps and ambiguities.

        Args:
            task_description: The user's task description
            context: Optional context from previous interactions

        Returns:
            dict with:
                - has_gaps: bool (whether gaps were found)
                - confidence: float (0.0-1.0, how clear the task is)
                - gaps: list[dict] (identified knowledge gaps)
                - questions: list[str] (clarifying questions)
                - severity: str ("low", "medium", "high")
        """
        logger.info(f"🔍 Analyzing task for knowledge gaps...")
        logger.debug(f"   Task: {task_description[:100]}...")

        gaps = []
        questions = []

        # Check 1: Task length (too short = likely ambiguous)
        word_count = len(task_description.split())
        if word_count < 5:
            gaps.append({
                "type": "vague_description",
                "description": "Task description is very brief",
                "severity": "high"
            })
            questions.append("Can you provide more details about what you want to build?")

        # Check 2: Missing project type
        project_types = ["web app", "api", "cli", "library", "script", "mobile app", "desktop app"]
        has_project_type = any(pt in task_description.lower() for pt in project_types)
        if not has_project_type and word_count < 20:
            gaps.append({
                "type": "missing_project_type",
                "description": "Project type not specified",
                "severity": "high"
            })
            questions.append("What type of application are you building? (web app, CLI tool, API, etc.)")

        # Check 3: Missing programming language
        languages = ["python", "javascript", "typescript", "java", "go", "rust", "c++", "c#"]
        has_language = any(lang in task_description.lower() for lang in languages)
        if not has_language:
            gaps.append({
                "type": "missing_language",
                "description": "Programming language not specified",
                "severity": "medium"
            })
            questions.append("What programming language should I use?")

        # Check 4: Too generic keywords
        generic_patterns = [
            r"\bbuild an? app\b",
            r"\bcreate something\b",
            r"\bmake a? project\b",
            r"\bhelp me\b",
            r"\bwrite code\b"
        ]
        is_generic = any(re.search(pattern, task_description.lower()) for pattern in generic_patterns)
        if is_generic:
            gaps.append({
                "type": "generic_request",
                "description": "Request is too generic",
                "severity": "high"
            })
            if "What is the primary purpose or main functionality?" not in questions:
                questions.append("What is the primary purpose or main functionality?")

        # Check 5: Missing features/requirements
        has_features = any(word in task_description.lower() for word in ["with", "include", "support", "feature"])
        if not has_features and word_count < 15:
            gaps.append({
                "type": "missing_features",
                "description": "No specific features mentioned",
                "severity": "medium"
            })
            questions.append("What specific features or functionality should it have?")

        # Check 6: Missing tech stack (for web/api projects)
        if any(term in task_description.lower() for term in ["web", "api", "backend", "frontend"]):
            frameworks = ["react", "vue", "angular", "express", "flask", "django", "fastapi", "nest"]
            has_framework = any(fw in task_description.lower() for fw in frameworks)
            if not has_framework:
                gaps.append({
                    "type": "missing_tech_stack",
                    "description": "Web/API tech stack not specified",
                    "severity": "low"
                })
                questions.append("What framework or tech stack would you like to use?")

        # Check 7: Check Memory for similar projects (if available)
        if self.memory:
            similar_context = await self._check_memory_for_context(task_description)
            if similar_context:
                logger.debug(f"📚 Found similar context in Memory: {len(similar_context)} items")

        # Calculate confidence score
        max_severity_score = {
            "high": 0.3,
            "medium": 0.6,
            "low": 0.8
        }

        if not gaps:
            confidence = 1.0
            severity = "none"
        else:
            # Confidence is inversely related to gap severity
            severities = [gap["severity"] for gap in gaps]
            worst_severity = "high" if "high" in severities else "medium" if "medium" in severities else "low"
            confidence = max_severity_score[worst_severity]
            severity = worst_severity

        has_gaps = len(gaps) > 0

        result = {
            "has_gaps": has_gaps,
            "confidence": confidence,
            "gaps": gaps,
            "questions": questions,
            "severity": severity,
            "gap_count": len(gaps)
        }

        if has_gaps:
            logger.info(f"⚠️  Knowledge gaps detected:")
            logger.info(f"   Gaps: {len(gaps)} ({severity} severity)")
            logger.info(f"   Confidence: {confidence:.2f}")
            logger.info(f"   Questions: {len(questions)}")
        else:
            logger.info(f"✅ Task is clear (confidence: {confidence:.2f})")

        return result

    async def generate_clarification_message(
        self,
        task_description: str,
        gaps: list[dict[str, Any]],
        questions: list[str]
    ) -> dict[str, Any]:
        """
        Generate a WebSocket message to request clarifications.

        Args:
            task_description: Original task description
            gaps: List of identified gaps
            questions: List of questions to ask

        Returns:
            WebSocket message dict ready to send
        """
        logger.info(f"💬 Generating clarification message with {len(questions)} questions")

        # Limit to 5 most important questions
        priority_questions = questions[:5]

        message = {
            "type": "clarification_needed",
            "task": task_description[:200],  # Preview
            "gaps_detected": len(gaps),
            "questions": priority_questions,
            "timeout": 300,  # 5 minutes
            "skip_option": True  # User can skip and proceed with defaults
        }

        logger.debug(f"   Message: {message}")
        return message

    async def incorporate_answers(
        self,
        original_task: str,
        answers: dict[str, str]
    ) -> str:
        """
        Incorporate user answers into the task description.

        Args:
            original_task: Original task description
            answers: Dict of {question: answer}

        Returns:
            Enhanced task description with clarifications
        """
        logger.info(f"📝 Incorporating {len(answers)} clarifications into task")

        # Build enhanced description
        enhanced_parts = [
            "# Task Description",
            original_task,
            "",
            "# Clarifications"
        ]

        for question, answer in answers.items():
            enhanced_parts.append(f"- {question}")
            enhanced_parts.append(f"  → {answer}")

        enhanced_task = "\n".join(enhanced_parts)

        logger.debug(f"   Enhanced task length: {len(enhanced_task)} chars")
        return enhanced_task

    async def suggest_default_assumptions(
        self,
        task_description: str,
        gaps: list[dict[str, Any]]
    ) -> dict[str, str]:
        """
        Suggest default assumptions when user skips clarifications.

        Args:
            task_description: Original task description
            gaps: Identified knowledge gaps

        Returns:
            Dict of {gap_type: default_assumption}
        """
        logger.info(f"🎯 Generating default assumptions for {len(gaps)} gaps")

        assumptions = {}

        for gap in gaps:
            gap_type = gap["type"]

            if gap_type == "missing_project_type":
                # Infer from keywords
                if "api" in task_description.lower():
                    assumptions[gap_type] = "REST API"
                elif "web" in task_description.lower():
                    assumptions[gap_type] = "Web Application"
                else:
                    assumptions[gap_type] = "CLI Application"

            elif gap_type == "missing_language":
                # Default to Python (most versatile)
                assumptions[gap_type] = "Python"

            elif gap_type == "missing_tech_stack":
                if "api" in task_description.lower() or "backend" in task_description.lower():
                    assumptions[gap_type] = "FastAPI (Python)"
                elif "web" in task_description.lower() or "frontend" in task_description.lower():
                    assumptions[gap_type] = "React + FastAPI"
                else:
                    assumptions[gap_type] = "Standard library"

            elif gap_type == "missing_features":
                assumptions[gap_type] = "Basic CRUD operations"

            elif gap_type in ["vague_description", "generic_request"]:
                assumptions[gap_type] = "Simple implementation with core functionality only"

        logger.debug(f"   Assumptions: {assumptions}")
        return assumptions

    async def _check_memory_for_context(
        self,
        task_description: str
    ) -> list[dict[str, Any]]:
        """
        Check Memory for similar past projects to inform questions.

        Args:
            task_description: Current task description

        Returns:
            List of similar project contexts
        """
        if not self.memory:
            return []

        try:
            # Search Memory for similar tasks
            results = await self.memory.search(
                query=task_description,
                k=5
            )

            similar_contexts = []
            for result in results:
                metadata = result.get("metadata", {})
                if metadata.get("type") in ["learning_record", "workflow_execution"]:
                    similar_contexts.append({
                        "project_type": metadata.get("project_type"),
                        "quality": metadata.get("quality_score"),
                        "content": result.get("content", "")[:200]
                    })

            return similar_contexts

        except Exception as e:
            logger.warning(f"⚠️  Failed to check Memory: {e}")
            return []

    async def should_ask_questions(
        self,
        analysis: dict[str, Any]
    ) -> bool:
        """
        Decide whether to ask clarifying questions.

        Args:
            analysis: Result from analyze_task()

        Returns:
            True if questions should be asked, False otherwise
        """
        # Ask questions if:
        # 1. Gaps exist AND
        # 2. Severity is high or medium AND
        # 3. Confidence is low (< 0.7)
        should_ask = (
            analysis["has_gaps"] and
            analysis["severity"] in ["high", "medium"] and
            analysis["confidence"] < 0.7
        )

        logger.debug(f"   Should ask questions: {should_ask}")
        return should_ask


# Export
__all__ = ["CuriositySystemV6"]
