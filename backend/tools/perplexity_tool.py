"""
Perplexity API Tool for Research Agent

Provides web search capabilities using Perplexity Sonar API.
Fallback: Uses Anthropic Claude if Perplexity API key not available.

Documentation:
- Perplexity API: https://docs.perplexity.ai/
- LangChain Tool: https://python.langchain.com/docs/modules/tools/

Integration:
- Research Subgraph: Used by create_react_agent()
- Asimov: Requires can_web_search permission (TODO: Phase 8)
"""

from __future__ import annotations

import logging
import os
from typing import Any

from langchain_core.tools import tool
# Use ClaudeCLISimple instead of langchain-anthropic (broken)
from adapters.claude_cli_simple import ClaudeCLISimple as ChatAnthropic

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

        if perplexity_key:
            # TODO: Implement actual Perplexity API call
            # For now: Use placeholder
            logger.warning("⚠️ Perplexity API not yet implemented, using fallback")
            return await _fallback_search(query)
        else:
            # Fallback: Use Anthropic Claude
            logger.info("ℹ️ No Perplexity API key, using Claude fallback")
            return await _fallback_search(query)

    except Exception as e:
        logger.error(f"❌ Perplexity search failed: {e}", exc_info=True)
        return {
            "answer": f"Search failed: {e}",
            "sources": [],
            "success": False
        }


async def _fallback_search(query: str) -> dict[str, Any]:
    """
    Fallback search using Claude (when Perplexity not available).

    Note: This is NOT a real web search, just an LLM response.
    For production, implement actual Perplexity API integration.
    """
    logger.info("🔄 Using Claude fallback for search")

    llm = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        temperature=0.3,
        max_tokens=2048
    )

    from langchain_core.messages import HumanMessage

    prompt = f"""You are a research assistant. Answer this query based on your knowledge:

Query: {query}

Provide:
1. A concise answer (2-3 paragraphs)
2. Key points
3. Relevant considerations

Format your response as structured information."""

    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        answer = response.content if hasattr(response, 'content') else str(response)

        logger.info(f"✅ Claude fallback response: {answer[:100]}...")

        return {
            "answer": answer,
            "sources": ["(Claude knowledge base - not real-time web search)"],
            "success": True
        }

    except Exception as e:
        logger.error(f"❌ Claude fallback failed: {e}", exc_info=True)
        return {
            "answer": f"Fallback search failed: {e}",
            "sources": [],
            "success": False
        }


# Export
__all__ = ["perplexity_search"]
