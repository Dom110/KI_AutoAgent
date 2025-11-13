import logging
from typing import Literal

from .llm_config import AgentLLMConfigManager, AgentLLMSettings
from .llm_providers.base import LLMProvider
from .llm_providers.openai_provider import OpenAIProvider
from .llm_providers.anthropic_provider import AnthropicProvider

logger = logging.getLogger("agent.llm_factory")

type LLMProviderType = Literal["openai", "anthropic"]


class AgentLLMFactory:
    """
    Factory for creating LLM providers for agents.
    
    Usage:
        # Get provider for an agent
        provider = AgentLLMFactory.get_provider_for_agent("supervisor")
        
        # Or create directly
        settings = AgentLLMSettings(provider="openai", model="gpt-4o")
        provider = AgentLLMFactory.create_provider(settings)
    """
    
    _provider_mapping: dict[LLMProviderType, type[LLMProvider]] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
    }
    
    @classmethod
    def get_provider_for_agent(cls, agent_name: str) -> LLMProvider:
        """
        Get LLM provider for a specific agent.
        
        Args:
            agent_name: Name of the agent (e.g., 'supervisor', 'codesmith')
            
        Returns:
            Configured LLMProvider instance
            
        Raises:
            ValueError: If agent config is invalid or unsupported provider
        """
        logger.info(f"🏭 Creating LLM provider for agent: {agent_name}")
        
        settings = AgentLLMConfigManager.get_agent_settings(agent_name)
        logger.debug(f"   Settings: {settings}")
        
        return cls.create_provider(settings)
    
    @classmethod
    def create_provider(cls, settings: AgentLLMSettings) -> LLMProvider:
        """
        Create LLM provider from settings.
        
        Args:
            settings: AgentLLMSettings with provider and model info
            
        Returns:
            Configured LLMProvider instance
            
        Raises:
            ValueError: If provider is not supported
        """
        provider_name = settings.provider
        logger.debug(f"🔍 Looking up provider: {provider_name}")
        
        if provider_name not in cls._provider_mapping:
            supported = ", ".join(cls._provider_mapping.keys())
            logger.error(f"❌ Unsupported provider: {provider_name} (supported: {supported})")
            raise ValueError(
                f"Unsupported provider: {provider_name}. "
                f"Supported providers: {supported}"
            )
        
        provider_class = cls._provider_mapping[provider_name]
        logger.debug(f"   ✅ Using provider class: {provider_class.__name__}")
        
        try:
            provider = provider_class(
                model=settings.model,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                timeout_seconds=settings.timeout_seconds,
            )
            logger.info(f"✅ Created {provider_name} provider: {provider.model}")
            return provider
        except Exception as e:
            logger.error(f"❌ Failed to create provider: {e}")
            raise
    
    @classmethod
    def register_provider(
        cls,
        name: LLMProviderType,
        provider_class: type[LLMProvider],
    ) -> None:
        """
        Register a new provider.
        
        Args:
            name: Provider name
            provider_class: Provider class that extends LLMProvider
        """
        logger.info(f"📝 Registering provider: {name} -> {provider_class.__name__}")
        cls._provider_mapping[name] = provider_class
    
    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """Get list of supported providers."""
        return list(cls._provider_mapping.keys())
    
    @classmethod
    def get_provider_info(cls) -> dict[str, str]:
        """Get info about all registered providers."""
        return {
            name: provider_class.__name__
            for name, provider_class in cls._provider_mapping.items()
        }
