"""
OpenAI Provider - Wrapper for OpenAI Service

Wraps the existing OpenAI Service to conform to AIProvider interface.

Author: KI AutoAgent Team
Version: 7.0.0
Date: 2025-10-23
"""

from __future__ import annotations

import logging
import os
from typing import AsyncGenerator

from backend.utils.ai_factory import AIProvider, AIRequest, AIResponse
from backend.utils.openai_service import OpenAIService, OpenAIConfig

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """
    AI Provider that wraps OpenAI Service.

    Used for: Supervisor, Architect
    """

    def __init__(self, model: str | None = None):
        """Initialize OpenAI Provider."""
        super().__init__(model=model)

        # Create OpenAI service
        config = OpenAIConfig(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=self.model
        )
        self.service = OpenAIService(config=config)

    def _get_provider_name(self) -> str:
        return "openai"

    def _get_default_model(self) -> str:
        return os.getenv("OPENAI_MODEL", "gpt-4o-2024-11-20")

    async def validate_connection(self) -> tuple[bool, str]:
        """
        Validate OpenAI API key and connection.

        Returns:
            (success, message)
        """
        if not self.service.client:
            return (False, "OpenAI API key not configured")

        # Try a simple API call
        try:
            response = await self.service.complete(
                prompt="Test",
                system_prompt="Respond with 'OK'",
                max_tokens=10
            )
            if response and "OK" in response.upper():
                return (True, f"OpenAI {self.model}")
            else:
                return (False, "OpenAI API test failed")
        except Exception as e:
            return (False, f"OpenAI API error: {str(e)[:100]}")

    async def complete(self, request: AIRequest) -> AIResponse:
        """
        Get completion from OpenAI.

        Args:
            request: AI request

        Returns:
            AI response
        """
        try:
            content = await self.service.complete(
                prompt=request.prompt,
                system_prompt=request.system_prompt,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=False
            )

            return AIResponse(
                content=content,
                provider=self.provider_name,
                model=self.model,
                success=True
            )

        except Exception as e:
            logger.error(f"❌ OpenAI completion failed: {e}")
            return AIResponse(
                content="",
                provider=self.provider_name,
                model=self.model,
                success=False,
                error=str(e)
            )

    async def stream_complete(self, request: AIRequest) -> AsyncGenerator[str, None]:
        """
        Get streaming completion from OpenAI.

        Args:
            request: AI request

        Yields:
            Response chunks
        """
        try:
            async for chunk in self.service.stream_complete(
                prompt=request.prompt,
                system_prompt=request.system_prompt,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            ):
                yield chunk

        except Exception as e:
            logger.error(f"❌ OpenAI streaming failed: {e}")
            yield f"Error: {e}"


# ============================================================================
# Register with Factory
# ============================================================================

from backend.utils.ai_factory import AIFactory

AIFactory.register_provider("openai", OpenAIProvider)

logger.info("✅ OpenAI provider registered")
