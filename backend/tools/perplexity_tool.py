"""
Perplexity API Tool for Research Agent

Provides web search capabilities using Perplexity Sonar API.

Documentation:
- Perplexity API: https://docs.perplexity.ai/
- LangChain Tool: https://python.langchain.com/docs/modules/tools/

Integration:
- Research Subgraph: Used by create_react_agent()
- Asimov: Requires can_web_search permission (TODO: Phase 8)

Important: NO AUTO FALLBACKS
- If PERPLEXITY_API_KEY not set → Fail
- If Perplexity API not implemented → Fail
- User requirement: "NIEMALS auto Fallbacks für gar nichts"
"""

from __future__ import annotations

import logging
import os
from typing import Any

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
async def perplexity_search(query: str) -> dict[str, Any]:
    """
    Search the web using Perplexity Sonar API.

    Args:
        query: Search query (e.g., "React best practices 2025")

    Returns:
        dict with:
            - answer: str (search result summary)
            - sources: list[str] (cited URLs)
            - success: bool

    Example:
        result = await perplexity_search("Python async patterns")
        print(result["answer"])
    """
    logger.info(f"🔍 Perplexity search: {query}")

    try:
        # Check for Perplexity API key
        perplexity_key = os.getenv("PERPLEXITY_API_KEY")

        if not perplexity_key:
            # NO AUTO FALLBACK: Fail if key not configured
            logger.error("❌ PERPLEXITY_API_KEY not set in environment")
            return {
                "answer": "Perplexity API key not configured. Please set PERPLEXITY_API_KEY in ~/.ki_autoagent/config/.env",
                "sources": [],
                "success": False,
                "error": "missing_api_key"
            }

        # TODO: Implement actual Perplexity API call
        # For now: Return error (NO AUTO FALLBACK)
        logger.error("❌ Perplexity API not yet implemented")
        return {
            "answer": "Perplexity API integration pending. See backend/tools/perplexity_tool.py",
            "sources": [],
            "success": False,
            "error": "not_implemented"
        }

    except Exception as e:
        logger.error(f"❌ Perplexity search failed: {e}", exc_info=True)
        return {
            "answer": f"Search failed: {e}",
            "sources": [],
            "success": False,
            "error": "exception"
        }


# Export
__all__ = ["perplexity_search"]
