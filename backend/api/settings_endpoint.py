from __future__ import annotations

"""
Settings API Endpoint
Allows VS Code extension to sync settings with backend
"""

import logging
import os
import sys
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsUpdateRequest(BaseModel):
    """Request model for updating settings"""

    settings: dict[str, Any]


@router.get("/current")
async def get_current_settings():
    """
    Get current backend settings.

    Returns:
        Dictionary with all v5.0 settings organized by category
    """
    try:
        return {"success": True, "settings": Settings.to_dict()}
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update")
async def update_settings(request: SettingsUpdateRequest):
    """
    Update backend settings from VS Code extension.

    Expected format:
    {
        "settings": {
            "langgraph.enabled": true,
            "agents.qualityThreshold": 0.75,
            ...
        }
    }

    Returns:
        Updated settings
    """
    try:
        # Update settings from VS Code
        Settings.update_from_vscode(request.settings)

        logger.info(
            f"✅ Settings updated from VS Code: {len(request.settings)} settings"
        )

        return {
            "success": True,
            "message": f"Updated {len(request.settings)} settings",
            "settings": Settings.to_dict(),
        }
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_setting_categories():
    """
    Get available setting categories and their keys.

    Useful for VS Code extension to know which settings are supported.

    Returns:
        Dictionary with category -> setting keys mapping
    """
    return {
        "success": True,
        "categories": {
            "langgraph": [
                "enabled",
                "checkpointInterval",
                "maxIterations",
                "parallelExecution",
                "stateManagement",
            ],
            "agents": [
                "qualityThreshold",
                "maxRetries",
                "reviewerIterations",
                "fixerIterations",
            ],
            "routing": [
                "strategy",
                "confidenceThreshold",
                "fallbackAgent",
                "enableKeywordMatching",
                "enableSemanticMatching",
            ],
            "monitoring": [
                "enabled",
                "logAgentMetrics",
                "trackRoutingSuccess",
                "alertOnFailures",
            ],
            "context": ["maxTokensPerAgent", "includeHistory", "historyDepth"],
            "memory": ["enabled", "storageBackend"],
            "cost": [
                "trackUsage",
                "monthlyBudget",
                "alertOnThreshold",
                "preferCheaperModels",
            ],
        },
    }


@router.post("/reset")
async def reset_to_defaults():
    """
    Reset all settings to default values.

    Returns:
        Default settings
    """
    try:
        # Reset by re-instantiating (uses class defaults)
        Settings.LANGGRAPH_ENABLED = True
        Settings.LANGGRAPH_CHECKPOINT_INTERVAL = 5
        Settings.LANGGRAPH_MAX_ITERATIONS = 20
        Settings.LANGGRAPH_PARALLEL_EXECUTION = False
        Settings.LANGGRAPH_STATE_MANAGEMENT = "sqlite"

        Settings.AGENT_QUALITY_THRESHOLD = 0.75
        Settings.AGENT_MAX_RETRIES = 3
        Settings.AGENT_REVIEWER_ITERATIONS = 2
        Settings.AGENT_FIXER_ITERATIONS = 3

        Settings.ROUTING_STRATEGY = "hybrid"
        Settings.ROUTING_CONFIDENCE_THRESHOLD = 0.8
        Settings.ROUTING_FALLBACK_AGENT = "orchestrator"
        Settings.ROUTING_ENABLE_KEYWORD_MATCHING = True
        Settings.ROUTING_ENABLE_SEMANTIC_MATCHING = True

        Settings.MONITORING_ENABLED = True
        Settings.MONITORING_LOG_AGENT_METRICS = False
        Settings.MONITORING_TRACK_ROUTING_SUCCESS = True
        Settings.MONITORING_ALERT_ON_FAILURES = True

        Settings.CONTEXT_MAX_TOKENS_PER_AGENT = 8000
        Settings.CONTEXT_INCLUDE_HISTORY = True
        Settings.CONTEXT_HISTORY_DEPTH = 10

        Settings.MEMORY_ENABLED = False
        Settings.MEMORY_STORAGE_BACKEND = "sqlite"

        Settings.COST_TRACK_USAGE = True
        Settings.COST_MONTHLY_BUDGET = 100.0
        Settings.COST_ALERT_ON_THRESHOLD = 0.8
        Settings.COST_PREFER_CHEAPER_MODELS = False

        logger.info("✅ Settings reset to defaults")

        return {
            "success": True,
            "message": "Settings reset to defaults",
            "settings": Settings.to_dict(),
        }
    except Exception as e:
        logger.error(f"Error resetting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate")
async def validate_settings():
    """
    Validate current settings for consistency.

    Checks:
    - Value ranges are valid
    - Enum values are correct
    - Dependencies are satisfied

    Returns:
        Validation result with warnings/errors
    """
    warnings = []
    errors = []

    # LangGraph validations
    if Settings.LANGGRAPH_CHECKPOINT_INTERVAL < 1:
        errors.append("langgraph.checkpointInterval must be >= 1")
    if Settings.LANGGRAPH_MAX_ITERATIONS < 5:
        warnings.append(
            "langgraph.maxIterations < 5 may cause premature workflow termination"
        )

    # Agent quality validations
    if not (0.5 <= Settings.AGENT_QUALITY_THRESHOLD <= 0.95):
        errors.append("agents.qualityThreshold must be between 0.5 and 0.95")
    if Settings.AGENT_MAX_RETRIES < 1:
        errors.append("agents.maxRetries must be >= 1")

    # Alternative Fixer validations (v5.1.0)
    if Settings.ALTERNATIVE_FIXER_ENABLED:
        valid_models = [
            "gpt-4o",
            "gpt-5",
            "gpt-5-mini",
            "claude-opus-4",
            "claude-sonnet-4",
        ]
        if Settings.ALTERNATIVE_FIXER_MODEL not in valid_models:
            errors.append(
                f"alternativeFixer.model must be one of: {', '.join(valid_models)}"
            )

        # Warn if using same model as primary fixer
        if Settings.ALTERNATIVE_FIXER_MODEL == "claude-sonnet-4":
            warnings.append(
                "alternativeFixer.model is same as primary fixer (Claude Sonnet) - no benefit!"
            )

        # Validate trigger iteration
        if Settings.ALTERNATIVE_FIXER_TRIGGER_ITERATION < 5:
            warnings.append(
                "alternativeFixer.triggerAfterIterations < 5 may trigger too early (before research)"
            )
        if Settings.ALTERNATIVE_FIXER_TRIGGER_ITERATION > 15:
            warnings.append(
                "alternativeFixer.triggerAfterIterations > 15 may be too late (after many failures)"
            )

        # Validate temperature
        if not (0.0 <= Settings.ALTERNATIVE_FIXER_TEMPERATURE <= 1.0):
            errors.append("alternativeFixer.temperature must be between 0.0 and 1.0")

    # Routing validations
    if Settings.ROUTING_STRATEGY not in ["keyword", "confidence", "hybrid"]:
        errors.append("routing.strategy must be one of: keyword, confidence, hybrid")
    if not (0.5 <= Settings.ROUTING_CONFIDENCE_THRESHOLD <= 0.95):
        errors.append("routing.confidenceThreshold must be between 0.5 and 0.95")

    # Context validations
    if Settings.CONTEXT_MAX_TOKENS_PER_AGENT < 1000:
        warnings.append("context.maxTokensPerAgent < 1000 may cause context truncation")
    if Settings.CONTEXT_HISTORY_DEPTH > 50:
        warnings.append(
            "context.historyDepth > 50 may cause high token usage and costs"
        )

    # Cost validations
    if Settings.COST_MONTHLY_BUDGET > 0 and Settings.COST_MONTHLY_BUDGET < 10:
        warnings.append(
            "cost.monthlyBudget < $10 may be too low for active development"
        )

    return {
        "success": len(errors) == 0,
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "settings": Settings.to_dict(),
    }
