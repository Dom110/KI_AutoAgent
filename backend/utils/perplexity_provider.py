"""
Perplexity Provider - Wrapper for Perplexity Service

Wraps the existing Perplexity Service to conform to AIProvider interface.

Author: KI AutoAgent Team
Version: 7.0.0
Date: 2025-10-23
"""

from __future__ import annotations

import logging
import os
from typing import AsyncGenerator

from backend.utils.ai_factory import AIProvider, AIRequest, AIResponse
from backend.utils.perplexity_service import PerplexityService

logger = logging.getLogger(__name__)


class PerplexityProvider(AIProvider):
    """
    AI Provider that wraps Perplexity Service.

    Used for: Research Agent (web search)
    """

    def __init__(self, model: str | None = None):
        """Initialize Perplexity Provider."""
        super().__init__(model=model)

        # Create Perplexity service
        try:
            self.service = PerplexityService(model=self.model)
        except ValueError as e:
            logger.error(f"❌ Perplexity initialization failed: {e}")
            self.service = None

    def _get_provider_name(self) -> str:
        return "perplexity"

    def _get_default_model(self) -> str:
        return os.getenv("PERPLEXITY_MODEL", "sonar")

    async def validate_connection(self) -> tuple[bool, str]:
        """
        Validate Perplexity API key and connection.

        Returns:
            (success, message)
        """
        if not self.service:
            return (False, "Perplexity API key not configured")

        # Try a simple search
        try:
            result = await self.service.search_web("test query")
            if result and "answer" in result:
                return (True, f"Perplexity {self.model}")
            else:
                return (False, "Perplexity API test failed")
        except Exception as e:
            return (False, f"Perplexity API error: {str(e)[:100]}")

    async def complete(self, request: AIRequest) -> AIResponse:
        """
        Get completion from Perplexity (web search).

        Args:
            request: AI request

        Returns:
            AI response with search results
        """
        if not self.service:
            return AIResponse(
                content="",
                provider=self.provider_name,
                model=self.model,
                success=False,
                error="Perplexity service not available"
            )

        try:
            result = await self.service.search_web(request.prompt)

            # Extract answer and citations
            answer = result.get("answer", "")
            citations = result.get("citations", [])

            # Format response with citations
            content_parts = [answer]
            if citations:
                content_parts.append("\n\nSources:")
                for i, citation in enumerate(citations[:5], 1):  # Top 5 sources
                    content_parts.append(f"{i}. {citation}")

            content = "\n".join(content_parts)

            return AIResponse(
                content=content,
                provider=self.provider_name,
                model=self.model,
                success=True,
                metadata={
                    "citations": citations,
                    "raw_result": result
                }
            )

        except Exception as e:
            logger.error(f"❌ Perplexity search failed: {e}")
            return AIResponse(
                content="",
                provider=self.provider_name,
                model=self.model,
                success=False,
                error=str(e)
            )

    async def stream_complete(self, request: AIRequest) -> AsyncGenerator[str, None]:
        """
        Get streaming completion from Perplexity.

        Args:
            request: AI request

        Yields:
            Response chunks
        """
        if not self.service:
            yield "Error: Perplexity service not available"
            return

        try:
            async for chunk in self.service.stream_search(request.prompt):
                yield chunk

        except Exception as e:
            logger.error(f"❌ Perplexity streaming failed: {e}")
            yield f"Error: {e}"


# ============================================================================
# Register with Factory
# ============================================================================

from backend.utils.ai_factory import AIFactory

AIFactory.register_provider("perplexity", PerplexityProvider)

logger.info("✅ Perplexity provider registered")
