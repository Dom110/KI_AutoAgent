"""
AI Factory - Abstraction Layer for Multiple AI Providers

Allows easy switching between different AI providers (OpenAI, Claude CLI, Perplexity, etc.)
per agent via configuration.

Author: KI AutoAgent Team
Version: 7.0.0
Date: 2025-10-23
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncGenerator

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


# ============================================================================
# Base Provider Interface
# ============================================================================

@dataclass
class AIRequest:
    """Unified request structure for all AI providers."""

    prompt: str
    system_prompt: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4000
    workspace_path: str | None = None
    context: dict[str, Any] | None = None
    tools: list[str] | None = None  # For Claude CLI: ["Read", "Edit", "Bash"]
    stream: bool = False


@dataclass
class AIResponse:
    """Unified response structure from all AI providers."""

    content: str
    provider: str
    model: str
    success: bool = True
    error: str | None = None
    metadata: dict[str, Any] | None = None


class AIProvider(ABC):
    """
    Abstract base class for all AI providers.

    Each provider (OpenAI, Claude CLI, Perplexity, etc.) implements this interface.
    """

    def __init__(self, model: str | None = None):
        """
        Initialize the AI provider.

        Args:
            model: Model name (optional, uses default from config if not provided)
        """
        self.model = model or self._get_default_model()
        self.provider_name = self._get_provider_name()
        logger.info(f"✅ {self.provider_name} Provider initialized with model: {self.model}")

    @abstractmethod
    def _get_provider_name(self) -> str:
        """Return the provider name (e.g., 'openai', 'claude-cli')."""
        pass

    @abstractmethod
    def _get_default_model(self) -> str:
        """Return the default model from environment config."""
        pass

    @abstractmethod
    async def complete(self, request: AIRequest) -> AIResponse:
        """
        Get completion from the AI provider.

        Args:
            request: Unified AI request

        Returns:
            Unified AI response
        """
        pass

    @abstractmethod
    async def stream_complete(self, request: AIRequest) -> AsyncGenerator[str, None]:
        """
        Get streaming completion from the AI provider.

        Args:
            request: Unified AI request

        Yields:
            Response chunks as strings
        """
        pass

    @abstractmethod
    async def validate_connection(self) -> tuple[bool, str]:
        """
        Validate that the provider is available and configured correctly.

        Returns:
            Tuple of (success: bool, message: str)
        """
        pass


# ============================================================================
# AI Factory
# ============================================================================

class AIFactory:
    """
    Factory for creating AI provider instances.

    Supports multiple providers and makes it easy to add new ones.
    """

    # Registry of available providers
    _providers: dict[str, type[AIProvider]] = {}

    @classmethod
    def register_provider(cls, name: str, provider_class: type[AIProvider]):
        """
        Register a new AI provider.

        Args:
            name: Provider name (e.g., 'openai', 'claude-cli')
            provider_class: Provider class implementing AIProvider interface
        """
        cls._providers[name] = provider_class
        logger.debug(f"📝 Registered AI provider: {name}")

    @classmethod
    def create_provider(
        cls,
        provider_name: str,
        model: str | None = None
    ) -> AIProvider:
        """
        Create an AI provider instance.

        Args:
            provider_name: Name of the provider (openai, claude-cli, etc.)
            model: Optional model override

        Returns:
            AI provider instance

        Raises:
            ValueError: If provider is not registered
        """
        if provider_name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(
                f"Unknown AI provider: '{provider_name}'. "
                f"Available providers: {available}"
            )

        provider_class = cls._providers[provider_name]
        return provider_class(model=model)

    @classmethod
    def get_provider_for_agent(cls, agent_name: str) -> AIProvider:
        """
        Get the configured AI provider for a specific agent.

        Args:
            agent_name: Agent name (research, architect, codesmith, reviewfix)

        Returns:
            AI provider instance configured for this agent

        Example:
            >>> provider = AIFactory.get_provider_for_agent("codesmith")
            >>> # Returns Claude CLI provider if CODESMITH_AI_PROVIDER=claude-cli
        """
        # Get provider name from config
        provider_key = f"{agent_name.upper()}_AI_PROVIDER"
        provider_name = os.getenv(provider_key)

        if not provider_name:
            raise ValueError(
                f"No AI provider configured for agent '{agent_name}'. "
                f"Set {provider_key} in .env file"
            )

        # Get agent-specific model (PREFERRED - each agent gets its own model!)
        agent_model_key = f"{agent_name.upper()}_AI_MODEL"
        model = os.getenv(agent_model_key)

        # Fallback to provider-specific model if agent model not set
        if not model:
            provider_model_key = f"{provider_name.upper().replace('-', '_')}_MODEL"
            model = os.getenv(provider_model_key)

        logger.info(
            f"🎯 Agent '{agent_name}' → Provider: {provider_name}, "
            f"Model: {model or 'default'}"
        )

        return cls.create_provider(provider_name, model=model)

    @classmethod
    def list_providers(cls) -> list[str]:
        """Get list of registered provider names."""
        return list(cls._providers.keys())

    @classmethod
    async def validate_all_active_providers(cls) -> dict[str, tuple[bool, str]]:
        """
        Validate all AI providers that are currently configured for agents.

        Returns:
            Dictionary mapping provider names to (success, message) tuples
        """
        # Get all active providers from agent configs
        agent_names = ["research", "architect", "codesmith", "reviewfix"]
        active_providers = set()

        for agent in agent_names:
            config_key = f"{agent.upper()}_AI_PROVIDER"
            provider = os.getenv(config_key)
            if provider:
                active_providers.add(provider)

        # Validate each active provider
        results = {}
        for provider_name in active_providers:
            try:
                provider = cls.create_provider(provider_name)
                success, message = await provider.validate_connection()
                results[provider_name] = (success, message)
            except Exception as e:
                results[provider_name] = (False, str(e))

        return results


# ============================================================================
# Export
# ============================================================================

__all__ = [
    "AIProvider",
    "AIRequest",
    "AIResponse",
    "AIFactory",
]
