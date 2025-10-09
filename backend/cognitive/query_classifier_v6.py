"""
Query Classifier v6 - Intelligent Query Routing

Capabilities:
- Classify user queries by type
- Route to appropriate workflow
- Detect complexity level
- Identify required agents
- Extract key entities and intents

Integration:
- Before workflow initialization
- At workflow entry point

Author: KI AutoAgent Team
Version: 6.0.0
Python: 3.13+
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class QueryType(str, Enum):
    """Types of user queries."""

    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    BUG_FIX = "bug_fix"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    RESEARCH = "research"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    OPTIMIZATION = "optimization"
    EXPLANATION = "explanation"
    GENERAL = "general"


class ComplexityLevel(str, Enum):
    """Complexity levels for queries."""

    TRIVIAL = "trivial"      # < 1 min, single action
    SIMPLE = "simple"        # 1-5 min, single agent
    MODERATE = "moderate"    # 5-15 min, 2-3 agents
    COMPLEX = "complex"      # 15-60 min, full workflow
    VERY_COMPLEX = "very_complex"  # > 60 min, multi-phase


@dataclass(slots=True)
class QueryClassification:
    """Classification result for a query."""

    query_type: QueryType
    complexity: ComplexityLevel
    confidence: float
    required_agents: list[str]
    workflow_type: str
    entities: dict[str, list[str]]
    metadata: dict[str, Any]


class QueryClassifierV6:
    """
    Intelligent Query Classification System.

    Analyzes user queries to determine routing and execution strategy.
    """

    def __init__(self):
        """Initialize query classifier."""

        # Keyword patterns for query types
        self.type_patterns = {
            QueryType.CODE_GENERATION: [
                r"(create|build|implement|generate|write|develop|add)\s+(a\s+)?(new\s+)?(\w+)",
                r"i\s+need\s+(a\s+)?(\w+)",
                r"make\s+(a\s+)?(\w+)",
            ],
            QueryType.CODE_REVIEW: [
                r"(review|check|analyze|audit|inspect)\s+(\w+)",
                r"is\s+this\s+(\w+)\s+(good|correct|ok)",
                r"look\s+at\s+(\w+)",
            ],
            QueryType.BUG_FIX: [
                r"(fix|repair|solve|debug|resolve)\s+(the\s+)?(\w+)\s+(bug|error|issue|problem)",
                r"(bug|error|issue|problem)\s+in\s+(\w+)",
                r"not\s+working",
                r"broken",
                r"fails?",
            ],
            QueryType.REFACTORING: [
                r"(refactor|restructure|reorganize|improve|clean)\s+(\w+)",
                r"better\s+way\s+to",
                r"optimize\s+structure",
            ],
            QueryType.DOCUMENTATION: [
                r"(document|explain|describe)\s+(\w+)",
                r"(write|add|generate)\s+(docs?|documentation|comments)",
                r"what\s+does\s+(\w+)\s+do",
            ],
            QueryType.RESEARCH: [
                r"(research|investigate|find|search|look\s+up)\s+(\w+)",
                r"(what|how)\s+(is|are)\s+(\w+)",
                r"best\s+(practices|way|approach)",
                r"(learn|understand)\s+about",
            ],
            QueryType.ARCHITECTURE: [
                r"(architect|design|plan|structure)\s+(\w+)",
                r"system\s+design",
                r"architecture\s+for",
                r"how\s+should\s+i\s+structure",
            ],
            QueryType.TESTING: [
                r"(test|testing|tests)\s+(\w+)",
                r"(write|create|generate)\s+tests",
                r"unit\s+tests?",
                r"integration\s+tests?",
            ],
            QueryType.DEPLOYMENT: [
                r"(deploy|deployment|release)\s+(\w+)",
                r"push\s+to\s+(production|staging)",
                r"go\s+live",
            ],
            QueryType.OPTIMIZATION: [
                r"(optimize|improve|speed\s+up|faster)\s+(\w+)",
                r"performance",
                r"slow",
                r"bottleneck",
            ],
            QueryType.EXPLANATION: [
                r"(explain|why|how\s+does)\s+(\w+)",
                r"what\s+is\s+(\w+)",
                r"tell\s+me\s+about",
            ],
        }

        # Complexity indicators
        self.complexity_indicators = {
            ComplexityLevel.TRIVIAL: [
                "simple", "quick", "small", "tiny", "basic", "just"
            ],
            ComplexityLevel.SIMPLE: [
                "single", "one", "function", "method"
            ],
            ComplexityLevel.MODERATE: [
                "module", "component", "feature", "few"
            ],
            ComplexityLevel.COMPLEX: [
                "system", "application", "project", "full", "complete", "entire"
            ],
            ComplexityLevel.VERY_COMPLEX: [
                "complex", "large", "enterprise", "distributed", "scalable", "microservices"
            ],
        }

        # Agent requirements per query type
        self.agent_requirements = {
            QueryType.CODE_GENERATION: ["architect", "codesmith"],
            QueryType.CODE_REVIEW: ["reviewer"],
            QueryType.BUG_FIX: ["reviewer", "fixer"],
            QueryType.REFACTORING: ["architect", "codesmith", "reviewer"],
            QueryType.DOCUMENTATION: ["docubot"],
            QueryType.RESEARCH: ["research"],
            QueryType.ARCHITECTURE: ["architect"],
            QueryType.TESTING: ["codesmith"],
            QueryType.DEPLOYMENT: ["deployment"],
            QueryType.OPTIMIZATION: ["architect", "codesmith"],
            QueryType.EXPLANATION: ["research"],
            QueryType.GENERAL: ["architect", "codesmith"],
        }

        # Workflow routing
        self.workflow_routes = {
            QueryType.CODE_GENERATION: "iteration",
            QueryType.CODE_REVIEW: "review_only",
            QueryType.BUG_FIX: "fix_workflow",
            QueryType.REFACTORING: "iteration",
            QueryType.DOCUMENTATION: "doc_workflow",
            QueryType.RESEARCH: "research_workflow",
            QueryType.ARCHITECTURE: "design_workflow",
            QueryType.TESTING: "test_workflow",
            QueryType.DEPLOYMENT: "deploy_workflow",
            QueryType.OPTIMIZATION: "iteration",
            QueryType.EXPLANATION: "research_workflow",
            QueryType.GENERAL: "iteration",
        }

        logger.info("🧠 Query Classifier v6 initialized")

    async def classify_query(self, query: str) -> QueryClassification:
        """
        Classify a user query.

        Args:
            query: User query string

        Returns:
            Classification result
        """
        logger.info(f"🔍 Classifying query: {query[:100]}...")

        query_lower = query.lower()

        # Determine query type
        query_type, type_confidence = self._determine_type(query_lower)

        # Determine complexity
        complexity, complexity_confidence = self._determine_complexity(query_lower, query)

        # Extract entities
        entities = self._extract_entities(query)

        # Get required agents
        required_agents = self.agent_requirements.get(query_type, ["architect", "codesmith"])

        # Get workflow route
        workflow_type = self.workflow_routes.get(query_type, "iteration")

        # Overall confidence (average of type and complexity confidence)
        confidence = (type_confidence + complexity_confidence) / 2.0

        classification = QueryClassification(
            query_type=query_type,
            complexity=complexity,
            confidence=confidence,
            required_agents=required_agents,
            workflow_type=workflow_type,
            entities=entities,
            metadata={
                "query_length": len(query),
                "word_count": len(query.split()),
                "type_confidence": type_confidence,
                "complexity_confidence": complexity_confidence,
            }
        )

        logger.info(f"✅ Classification: {query_type.value} ({complexity.value}) - confidence: {confidence:.2f}")
        logger.debug(f"   Agents: {required_agents}")
        logger.debug(f"   Workflow: {workflow_type}")

        return classification

    def _determine_type(self, query_lower: str) -> tuple[QueryType, float]:
        """Determine query type using pattern matching."""

        scores: dict[QueryType, float] = {}

        # Score each type based on pattern matches
        for query_type, patterns in self.type_patterns.items():
            score = 0.0

            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 1.0

            if score > 0:
                scores[query_type] = score

        # If no matches, default to GENERAL
        if not scores:
            return QueryType.GENERAL, 0.5

        # Get highest scoring type
        best_type = max(scores.items(), key=lambda x: x[1])

        # Normalize confidence (cap at 1.0)
        confidence = min(best_type[1] / 2.0, 1.0)  # Divide by 2 because most types have 2-3 patterns

        return best_type[0], confidence

    def _determine_complexity(self, query_lower: str, query_original: str) -> tuple[ComplexityLevel, float]:
        """Determine complexity level."""

        scores: dict[ComplexityLevel, int] = {level: 0 for level in ComplexityLevel}

        # Check complexity indicators
        for level, indicators in self.complexity_indicators.items():
            for indicator in indicators:
                if indicator in query_lower:
                    scores[level] += 1

        # Heuristics based on query characteristics
        word_count = len(query_original.split())
        line_count = query_original.count("\n") + 1

        # Length-based complexity
        if word_count < 5:
            scores[ComplexityLevel.TRIVIAL] += 2
        elif word_count < 15:
            scores[ComplexityLevel.SIMPLE] += 2
        elif word_count < 30:
            scores[ComplexityLevel.MODERATE] += 2
        elif word_count < 60:
            scores[ComplexityLevel.COMPLEX] += 2
        else:
            scores[ComplexityLevel.VERY_COMPLEX] += 2

        # Multi-line queries are usually more complex
        if line_count > 3:
            scores[ComplexityLevel.COMPLEX] += 1
        if line_count > 10:
            scores[ComplexityLevel.VERY_COMPLEX] += 1

        # Get highest scoring complexity
        if max(scores.values()) == 0:
            # No indicators, default to SIMPLE
            return ComplexityLevel.SIMPLE, 0.5

        best_complexity = max(scores.items(), key=lambda x: x[1])

        # Calculate confidence based on score strength
        total_score = sum(scores.values())
        confidence = best_complexity[1] / total_score if total_score > 0 else 0.5

        return best_complexity[0], confidence

    def _extract_entities(self, query: str) -> dict[str, list[str]]:
        """Extract entities from query."""

        entities: dict[str, list[str]] = {
            "technologies": [],
            "file_types": [],
            "actions": [],
            "languages": [],
        }

        query_lower = query.lower()

        # Common technologies
        technologies = [
            "react", "vue", "angular", "python", "javascript", "typescript",
            "java", "c++", "rust", "go", "node", "express", "django", "flask",
            "fastapi", "docker", "kubernetes", "aws", "azure", "gcp",
            "postgresql", "mysql", "mongodb", "redis"
        ]

        for tech in technologies:
            if tech in query_lower:
                entities["technologies"].append(tech)

        # File types
        file_extensions = re.findall(r"\.(py|js|ts|jsx|tsx|java|cpp|rs|go|md|txt|json|yaml|yml|html|css)", query_lower)
        entities["file_types"] = list(set(file_extensions))

        # Programming languages
        languages = ["python", "javascript", "typescript", "java", "c++", "rust", "go", "ruby", "php"]
        for lang in languages:
            if lang in query_lower:
                entities["languages"].append(lang)

        # Actions (verbs)
        action_patterns = [
            r"(create|build|implement|generate|write|develop|add)",
            r"(review|check|analyze|audit)",
            r"(fix|repair|solve|debug)",
            r"(refactor|restructure|improve)",
            r"(deploy|release)",
            r"(test|testing)",
        ]

        for pattern in action_patterns:
            matches = re.findall(pattern, query_lower)
            entities["actions"].extend(matches)

        # Deduplicate
        entities["actions"] = list(set(entities["actions"]))

        return entities

    async def suggest_refinements(
        self,
        classification: QueryClassification
    ) -> list[str]:
        """
        Suggest query refinements for better clarity.

        Args:
            classification: Query classification

        Returns:
            List of suggested refinements
        """
        suggestions = []

        # Low confidence suggestions
        if classification.confidence < 0.6:
            suggestions.append(
                "Your query could be more specific. Consider adding details about:\n"
                "- What technology/language you're using\n"
                "- What you want to achieve\n"
                "- Any constraints or requirements"
            )

        # Missing technology context
        if not classification.entities["technologies"] and not classification.entities["languages"]:
            suggestions.append(
                "Specify the programming language or technology stack you're working with"
            )

        # Complex query without clear structure
        if classification.complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.VERY_COMPLEX]:
            if classification.metadata["word_count"] > 50:
                suggestions.append(
                    "For complex tasks, consider breaking it down into smaller steps"
                )

        return suggestions


# Global classifier instance
_classifier: QueryClassifierV6 | None = None


def get_query_classifier() -> QueryClassifierV6:
    """Get global query classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = QueryClassifierV6()
    return _classifier


# Export
__all__ = [
    "QueryClassifierV6",
    "QueryClassification",
    "QueryType",
    "ComplexityLevel",
    "get_query_classifier"
]
