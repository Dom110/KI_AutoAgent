"""
Perplexity API Tool for Research Agent

Provides web search capabilities using Perplexity Sonar API.

Documentation:
- Perplexity API: https://docs.perplexity.ai/
- LangChain Tool: https://python.langchain.com/docs/modules/tools/

Integration:
- Research Subgraph: Used by research_subgraph_v6_1.py
- Asimov: Requires can_web_search permission (TODO: Phase 8)

Important: NO AUTO FALLBACKS
- If PERPLEXITY_API_KEY not set → Fail
- If Perplexity API call fails → Fail
- User requirement: "NIEMALS auto Fallbacks für gar nichts"

Author: KI AutoAgent Team
Python: 3.13+
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

from langchain_core.tools import tool

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

# ASIMOV RULE 1: NO FALLBACK - Import PerplexityService directly
# If import fails, let the system fail explicitly
from utils.perplexity_service import PerplexityService


@tool
async def perplexity_search(query: str) -> dict[str, Any]:
    """
    Search the web using Perplexity Sonar API.

    Args:
        query: Search query (e.g., "React best practices 2025")

    Returns:
        dict with:
            - content: str (search result summary with citations)
            - answer: str (same as content for backwards compatibility)
            - citations: list[str] (cited URLs)
            - sources: list[str] (same as citations for backwards compatibility)
            - success: bool
            - model: str (Perplexity model used)
            - timestamp: str (ISO format timestamp)

    Example:
        result = await perplexity_search("Python async patterns")
        print(result["answer"])

    Raises:
        ValueError: If PERPLEXITY_API_KEY not set
        Exception: If Perplexity API call fails
    """
    logger.info(f"🔍 Perplexity search: {query}")

    # ASIMOV RULE 1: NO FALLBACK - Check API key and fail fast
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")
    if not perplexity_key:
        logger.error("❌ PERPLEXITY_API_KEY not set in environment")
        error_msg = "Perplexity API key not configured. Please set PERPLEXITY_API_KEY in ~/.ki_autoagent/config/.env"
        # Return error in result dict (don't raise, so workflow can handle gracefully)
        return {
            "content": error_msg,
            "answer": error_msg,  # Backwards compatibility
            "citations": [],
            "sources": [],  # Backwards compatibility
            "success": False,
            "error": "missing_api_key"
        }

    try:
        # Initialize PerplexityService (raises ValueError if key missing)
        service = PerplexityService(model="sonar")

        # Perform web search
        logger.debug(f"📡 Calling Perplexity API for: {query}")
        result = await service.search_web(
            query=query,
            recency="month",  # Focus on recent information
            max_results=5
        )

        # Extract data from result
        content = result.get("answer", "")
        citations = result.get("citations", [])

        # Format citations as strings if they're dicts
        formatted_citations = []
        for citation in citations:
            if isinstance(citation, dict):
                formatted_citations.append(citation.get("url", str(citation)))
            else:
                formatted_citations.append(str(citation))

        logger.info(f"✅ Perplexity search successful: {len(content)} chars, {len(formatted_citations)} citations")

        # Return structured result
        return {
            "content": content,
            "answer": content,  # Backwards compatibility
            "citations": formatted_citations,
            "sources": formatted_citations,  # Backwards compatibility
            "success": True,
            "model": result.get("model", "sonar"),
            "timestamp": result.get("timestamp", "")
        }

    except Exception as e:
        # ASIMOV RULE 1: NO FALLBACK - Let errors bubble up
        logger.error(f"❌ Perplexity search failed: {e}", exc_info=True)
        error_msg = f"Perplexity API error: {str(e)}"
        return {
            "content": error_msg,
            "answer": error_msg,
            "citations": [],
            "sources": [],
            "success": False,
            "error": "api_error",
            "error_details": str(e)
        }


# Export
__all__ = ["perplexity_search"]
