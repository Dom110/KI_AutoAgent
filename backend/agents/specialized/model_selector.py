"""
Model Selector v1.0 - Complexity-Based Model Selection

This module assesses task complexity and selects the appropriate AI model
for code generation, including Think mode activation for complex tasks.

Author: KI AutoAgent Team
Python: 3.13+
Version: v1.0.0
Date: 2025-10-15
"""

from __future__ import annotations

import logging
from typing import Any
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# MODEL CONFIGURATIONS
# ============================================================================

class ModelConfig:
    """Configuration for an AI model."""

    def __init__(
        self,
        model_id: str,
        name: str,
        think_mode: bool,
        temperature: float,
        max_tokens: int,
        description: str
    ):
        self.model_id = model_id
        self.name = name
        self.think_mode = think_mode
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.description = description

    def __repr__(self) -> str:
        return f"ModelConfig({self.name}, think={self.think_mode})"


# Available models (v6.2)
MODELS = {
    "sonnet_4": ModelConfig(
        model_id="claude-sonnet-4-20250514",
        name="Claude Sonnet 4",
        think_mode=False,
        temperature=0.3,
        max_tokens=4096,
        description="Fast, efficient for simple tasks"
    ),
    "sonnet_4_5": ModelConfig(
        model_id="claude-sonnet-4-5-20250929",
        name="Claude Sonnet 4.5",
        think_mode=False,
        temperature=0.3,
        max_tokens=8192,
        description="Balanced performance for moderate complexity"
    ),
    "sonnet_4_5_think": ModelConfig(
        model_id="claude-sonnet-4-5-20250929",
        name="Claude Sonnet 4.5 + Think",
        think_mode=True,
        temperature=0.3,
        max_tokens=8192,
        description="Enhanced reasoning for complex tasks"
    ),
    "opus_3": ModelConfig(
        model_id="claude-opus-3-5-20250620",
        name="Claude Opus 3.5",
        think_mode=False,
        temperature=0.3,
        max_tokens=16384,
        description="Maximum capability for very complex tasks"
    ),
    "opus_3_think": ModelConfig(
        model_id="claude-opus-3-5-20250620",
        name="Claude Opus 3.5 + Think",
        think_mode=True,
        temperature=0.3,
        max_tokens=16384,
        description="Maximum reasoning for extremely complex tasks"
    )
}


# ============================================================================
# COMPLEXITY ASSESSMENT
# ============================================================================

class ComplexityLevel:
    """Task complexity levels."""
    TRIVIAL = "trivial"          # Single file, <50 LOC
    SIMPLE = "simple"            # 1-3 files, <200 LOC total
    MODERATE = "moderate"        # 4-10 files, <1000 LOC total
    COMPLEX = "complex"          # 11-20 files, <5000 LOC total
    VERY_COMPLEX = "very_complex"  # 20+ files or >5000 LOC


def _extract_keywords_from_context(
    design_context: dict[str, Any] | None,
    research_context: dict[str, Any] | None,
    codebase_context: dict[str, Any] | None
) -> tuple[int, list[str]]:
    """
    Extract complexity indicators from design, research, and codebase context.

    Args:
        design_context: Architect design output (components, patterns, tech_stack)
        research_context: Research findings (technologies, best practices)
        codebase_context: Existing codebase analysis (files, structure)

    Returns:
        Tuple of (additional_complexity_score, reasons_list)
    """
    score = 0
    reasons = []
    combined_text = ""

    # Extract text from design context
    if design_context:
        if "description" in design_context:
            combined_text += " " + str(design_context["description"])
        if "components" in design_context:
            components = design_context["components"]
            score += min(len(components) // 5, 2)  # +1 per 5 components, max +2
            if len(components) >= 10:
                reasons.append(f"{len(components)} components (high)")
        if "patterns" in design_context:
            patterns = design_context["patterns"]
            if len(patterns) >= 3:
                score += 1
                reasons.append(f"{len(patterns)} design patterns")

    # Extract text from research context
    if research_context:
        if "findings" in research_context:
            findings = research_context["findings"]
            if isinstance(findings, list):
                combined_text += " " + " ".join(str(f) for f in findings)
            else:
                combined_text += " " + str(findings)
        if "sources" in research_context and len(research_context["sources"]) >= 5:
            score += 1
            reasons.append(f"{len(research_context['sources'])} research sources")

    # Extract from codebase context
    if codebase_context:
        if "files" in codebase_context:
            file_count = codebase_context["files"]
            if isinstance(file_count, int) and file_count >= 20:
                score += 1
                reasons.append(f"{file_count} existing files")
        if "complexity" in codebase_context:
            if codebase_context["complexity"] == "high":
                score += 2
                reasons.append("High existing codebase complexity")

    # Keyword detection in combined context
    text_lower = combined_text.lower()

    complexity_keywords = {
        "microservice": ("Microservices architecture", 2),
        "distributed": ("Distributed system", 2),
        "real-time": ("Real-time processing", 1),
        "websocket": ("WebSocket communication", 1),
        "event-driven": ("Event-driven architecture", 1),
        "message queue": ("Message queue system", 1),
        "kafka": ("Apache Kafka", 1),
        "rabbitmq": ("RabbitMQ", 1),
        "redis": ("Redis caching", 1),
        "graphql": ("GraphQL API", 1),
        "grpc": ("gRPC communication", 1),
        "kubernetes": ("Kubernetes orchestration", 2),
        "docker": ("Docker containerization", 1),
        "ci/cd": ("CI/CD pipeline", 1),
        "terraform": ("Infrastructure as Code", 1),
        "monitoring": ("Monitoring/observability", 1),
        "logging": ("Logging infrastructure", 1),
        "authentication": ("Authentication system", 2),
        "authorization": ("Authorization system", 1),
        "oauth": ("OAuth integration", 2),
        "jwt": ("JWT authentication", 1),
        "encryption": ("Encryption/security", 1),
        "blockchain": ("Blockchain integration", 2),
        "machine learning": ("ML/AI integration", 2),
        "tensorflow": ("TensorFlow", 2),
        "pytorch": ("PyTorch", 2),
    }

    detected_keywords = set()
    for keyword, (reason, points) in complexity_keywords.items():
        if keyword in text_lower and keyword not in detected_keywords:
            score += points
            reasons.append(reason)
            detected_keywords.add(keyword)

    return score, reasons


def assess_complexity(
    requirements: str,
    file_count: int = 0,
    estimated_loc: int = 0,
    tech_stack: list[str] | None = None,
    has_api: bool = False,
    has_database: bool = False,
    has_auth: bool = False,
    multi_language: bool = False,
    design_context: dict[str, Any] | None = None,
    research_context: dict[str, Any] | None = None,
    codebase_context: dict[str, Any] | None = None
) -> tuple[str, dict[str, Any]]:
    """
    Assess task complexity based on multiple factors.

    Args:
        requirements: User requirements text
        file_count: Estimated number of files
        estimated_loc: Estimated lines of code
        tech_stack: List of technologies to use
        has_api: Whether task involves API development
        has_database: Whether task involves database
        has_auth: Whether task involves authentication
        multi_language: Whether task involves multiple programming languages
        design_context: Architect design output (NEW v6.2)
        research_context: Research findings (NEW v6.2)
        codebase_context: Existing codebase analysis (NEW v6.2)

    Returns:
        Tuple of (complexity_level, metrics_dict)

    Complexity Scoring:
    - File count: 0 (trivial), 1-3 (simple), 4-10 (moderate), 11-20 (complex), 20+ (very_complex)
    - LOC: 0-50 (trivial), 51-200 (simple), 201-1000 (moderate), 1001-5000 (complex), 5000+ (very_complex)
    - Tech stack: +1 complexity per additional technology beyond 2
    - Features: +1 complexity for API, database, auth
    - Multi-language: +1 complexity
    - Design context: Extracted from architect proposal (components, patterns, tech stack)
    - Research context: Extracted from research findings (technologies, patterns detected)
    - Codebase context: Extracted from existing code analysis
    """
    complexity_score = 0
    reasons = []

    # File count scoring
    if file_count == 0:
        # Estimate from requirements
        req_words = len(requirements.split())
        if req_words < 50:
            file_count = 1
        elif req_words < 150:
            file_count = 3
        elif req_words < 300:
            file_count = 7
        else:
            file_count = 15

    if file_count >= 20:
        complexity_score += 4
        reasons.append(f"{file_count} files (very high)")
    elif file_count >= 11:
        complexity_score += 3
        reasons.append(f"{file_count} files (high)")
    elif file_count >= 4:
        complexity_score += 2
        reasons.append(f"{file_count} files (moderate)")
    elif file_count >= 2:
        complexity_score += 1
        reasons.append(f"{file_count} files (low)")

    # LOC scoring
    if estimated_loc >= 5000:
        complexity_score += 4
        reasons.append(f"~{estimated_loc} LOC (very high)")
    elif estimated_loc >= 1000:
        complexity_score += 3
        reasons.append(f"~{estimated_loc} LOC (high)")
    elif estimated_loc >= 200:
        complexity_score += 2
        reasons.append(f"~{estimated_loc} LOC (moderate)")
    elif estimated_loc >= 50:
        complexity_score += 1
        reasons.append(f"~{estimated_loc} LOC (low)")

    # Tech stack scoring
    if tech_stack and len(tech_stack) > 2:
        extra_tech = len(tech_stack) - 2
        complexity_score += extra_tech
        reasons.append(f"{len(tech_stack)} technologies (diverse)")

    # Feature scoring
    if has_api:
        complexity_score += 1
        reasons.append("API development")

    if has_database:
        complexity_score += 1
        reasons.append("Database integration")

    if has_auth:
        complexity_score += 2
        reasons.append("Authentication system")

    if multi_language:
        complexity_score += 1
        reasons.append("Multi-language codebase")

    # Keyword detection in requirements
    req_lower = requirements.lower()

    if "microservice" in req_lower or "distributed" in req_lower:
        complexity_score += 2
        reasons.append("Microservices/distributed architecture")

    if "real-time" in req_lower or "websocket" in req_lower:
        complexity_score += 1
        reasons.append("Real-time features")

    if "security" in req_lower or "encryption" in req_lower:
        complexity_score += 1
        reasons.append("Security requirements")

    if "test" in req_lower or "testing" in req_lower:
        complexity_score += 1
        reasons.append("Testing requirements")

    # NEW v6.2: Extract complexity from design, research, and codebase context
    context_score, context_reasons = _extract_keywords_from_context(
        design_context, research_context, codebase_context
    )
    complexity_score += context_score
    reasons.extend(context_reasons)

    # Determine complexity level
    if complexity_score == 0:
        level = ComplexityLevel.TRIVIAL
    elif complexity_score <= 2:
        level = ComplexityLevel.SIMPLE
    elif complexity_score <= 5:
        level = ComplexityLevel.MODERATE
    elif complexity_score <= 8:
        level = ComplexityLevel.COMPLEX
    else:
        level = ComplexityLevel.VERY_COMPLEX

    metrics = {
        "complexity_score": complexity_score,
        "complexity_level": level,
        "file_count": file_count,
        "estimated_loc": estimated_loc,
        "reasons": reasons,
        "timestamp": datetime.now().isoformat()
    }

    logger.info(
        f"🎯 Complexity assessment: {level} (score={complexity_score}, "
        f"files={file_count}, loc={estimated_loc})"
    )

    return level, metrics


# ============================================================================
# MODEL SELECTION
# ============================================================================

class ModelSelector:
    """
    Selects appropriate AI model based on task complexity.

    Usage:
        selector = ModelSelector()
        model, notification = selector.select_model(
            requirements="Build a React app...",
            file_count=5,
            estimated_loc=800
        )
    """

    def __init__(self):
        """Initialize ModelSelector."""
        self.selection_history: list[dict[str, Any]] = []

    def select_model(
        self,
        requirements: str,
        file_count: int = 0,
        estimated_loc: int = 0,
        tech_stack: list[str] | None = None,
        has_api: bool = False,
        has_database: bool = False,
        has_auth: bool = False,
        multi_language: bool = False,
        design_context: dict[str, Any] | None = None,
        research_context: dict[str, Any] | None = None,
        codebase_context: dict[str, Any] | None = None,
        force_model: str | None = None
    ) -> tuple[ModelConfig, str]:
        """
        Select model based on complexity assessment.

        Args:
            requirements: User requirements
            file_count: Estimated file count
            estimated_loc: Estimated lines of code
            tech_stack: Technologies to use
            has_api: API development needed
            has_database: Database integration needed
            has_auth: Authentication needed
            multi_language: Multiple languages
            design_context: Architect design output (NEW v6.2)
            research_context: Research findings (NEW v6.2)
            codebase_context: Existing codebase analysis (NEW v6.2)
            force_model: Force specific model ("sonnet_4", "sonnet_4_5", "opus_3", etc.)

        Returns:
            Tuple of (ModelConfig, user_notification_text)

        Selection Rules:
        - Trivial/Simple → Sonnet 4 (no Think)
        - Moderate → Sonnet 4.5 (no Think)
        - Complex → Sonnet 4.5 + Think
        - Very Complex / 20+ files → Opus 3.5 + Think
        """
        # Assess complexity
        complexity, metrics = assess_complexity(
            requirements=requirements,
            file_count=file_count,
            estimated_loc=estimated_loc,
            tech_stack=tech_stack,
            has_api=has_api,
            has_database=has_database,
            has_auth=has_auth,
            multi_language=multi_language,
            design_context=design_context,
            research_context=research_context,
            codebase_context=codebase_context
        )

        # Force model if specified
        if force_model:
            if force_model not in MODELS:
                logger.warning(f"⚠️  Unknown model: {force_model}, falling back to auto-selection")
            else:
                model = MODELS[force_model]
                notification = self._format_notification(model, complexity, metrics, forced=True)
                self._record_selection(model, complexity, metrics, forced=True)
                return model, notification

        # Select model based on complexity
        if complexity == ComplexityLevel.TRIVIAL or complexity == ComplexityLevel.SIMPLE:
            model = MODELS["sonnet_4"]
        elif complexity == ComplexityLevel.MODERATE:
            model = MODELS["sonnet_4_5"]
        elif complexity == ComplexityLevel.COMPLEX:
            model = MODELS["sonnet_4_5_think"]
        else:  # VERY_COMPLEX
            model = MODELS["opus_3_think"]

        # Generate user notification
        notification = self._format_notification(model, complexity, metrics, forced=False)

        # Record selection
        self._record_selection(model, complexity, metrics, forced=False)

        logger.info(f"✅ Selected: {model.name} (think={model.think_mode})")
        return model, notification

    def _format_notification(
        self,
        model: ModelConfig,
        complexity: str,
        metrics: dict[str, Any],
        forced: bool
    ) -> str:
        """Format user notification message."""
        reasons_text = "\n".join([f"  - {r}" for r in metrics["reasons"]])

        if forced:
            notification = f"""🤖 **Model Selection** (Manual Override)

**Selected Model:** {model.name}
**Think Mode:** {"✅ Enabled" if model.think_mode else "❌ Disabled"}
**Description:** {model.description}

This model was manually selected (override).
"""
        else:
            notification = f"""🤖 **Model Selection** (Automatic)

**Task Complexity:** {complexity.upper()}
**Complexity Score:** {metrics['complexity_score']}/10
**Selected Model:** {model.name}
**Think Mode:** {"✅ Enabled" if model.think_mode else "❌ Disabled"}

**Complexity Factors:**
{reasons_text}

**Why this model:**
{model.description}

**Estimated Task:**
- Files: ~{metrics['file_count']}
- Lines of Code: ~{metrics['estimated_loc']}
"""

        return notification

    def _record_selection(
        self,
        model: ModelConfig,
        complexity: str,
        metrics: dict[str, Any],
        forced: bool
    ) -> None:
        """Record model selection for analytics."""
        self.selection_history.append({
            "model": model.name,
            "model_id": model.model_id,
            "think_mode": model.think_mode,
            "complexity": complexity,
            "complexity_score": metrics["complexity_score"],
            "forced": forced,
            "timestamp": metrics["timestamp"]
        })

    def get_selection_history(self) -> list[dict[str, Any]]:
        """Get model selection history."""
        return self.selection_history.copy()

    def get_statistics(self) -> dict[str, Any]:
        """Get selection statistics."""
        if not self.selection_history:
            return {
                "total_selections": 0,
                "model_distribution": {},
                "think_mode_usage": 0,
                "avg_complexity_score": 0.0
            }

        total = len(self.selection_history)
        models = {}
        think_count = 0
        total_complexity = 0

        for entry in self.selection_history:
            model_name = entry["model"]
            models[model_name] = models.get(model_name, 0) + 1

            if entry["think_mode"]:
                think_count += 1

            total_complexity += entry["complexity_score"]

        return {
            "total_selections": total,
            "model_distribution": models,
            "think_mode_usage": think_count,
            "think_mode_percentage": round((think_count / total) * 100, 1),
            "avg_complexity_score": round(total_complexity / total, 2)
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def select_model_for_task(requirements: str, **kwargs) -> tuple[ModelConfig, str]:
    """
    Convenience function for one-off model selection.

    Args:
        requirements: User requirements
        **kwargs: Additional parameters for assess_complexity()

    Returns:
        Tuple of (ModelConfig, notification_text)
    """
    selector = ModelSelector()
    return selector.select_model(requirements, **kwargs)


def get_model_by_id(model_key: str) -> ModelConfig | None:
    """
    Get model configuration by key.

    Args:
        model_key: Model key ("sonnet_4", "opus_3_think", etc.)

    Returns:
        ModelConfig or None if not found
    """
    return MODELS.get(model_key)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "ModelConfig",
    "ModelSelector",
    "ComplexityLevel",
    "assess_complexity",
    "select_model_for_task",
    "get_model_by_id",
    "MODELS"
]
