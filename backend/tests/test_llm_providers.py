import asyncio
import logging
import importlib.util
from pathlib import Path

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("test_llm_providers")

base_path = Path("/Users/dominikfoert/git/KI_AutoAgent/backend/core/llm_providers/base.py")
spec = importlib.util.spec_from_file_location("base", base_path)
base_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_module)

LLMProvider = base_module.LLMProvider
LLMResponse = base_module.LLMResponse

openai_path = Path("/Users/dominikfoert/git/KI_AutoAgent/backend/core/llm_providers/openai_provider.py")
spec = importlib.util.spec_from_file_location("openai_provider", openai_path)
openai_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(openai_module)

OpenAIProvider = openai_module.OpenAIProvider

anthropic_path = Path("/Users/dominikfoert/git/KI_AutoAgent/backend/core/llm_providers/anthropic_provider.py")
spec = importlib.util.spec_from_file_location("anthropic_provider", anthropic_path)
anthropic_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(anthropic_module)

AnthropicProvider = anthropic_module.AnthropicProvider

llm_config_path = Path("/Users/dominikfoert/git/KI_AutoAgent/backend/core/llm_config.py")
spec = importlib.util.spec_from_file_location("llm_config", llm_config_path)
llm_config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(llm_config_module)

AgentLLMSettings = llm_config_module.AgentLLMSettings
AgentLLMConfigManager = llm_config_module.AgentLLMConfigManager

factory_path = Path("/Users/dominikfoert/git/KI_AutoAgent/backend/core/llm_factory.py")
spec = importlib.util.spec_from_file_location("llm_factory", factory_path)
factory_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factory_module)

AgentLLMFactory = factory_module.AgentLLMFactory


def test_llm_response():
    """Test LLMResponse dataclass."""
    logger.info("Testing LLMResponse...")
    
    response = LLMResponse(
        content="Test response",
        provider="openai",
        model="gpt-4o",
        completion_tokens=10,
        prompt_tokens=5,
        total_tokens=15,
        response_time_ms=100.5,
    )
    
    assert response.content == "Test response"
    assert response.provider == "openai"
    assert response.total_content_length == len("Test response")
    
    logger.info(f"   ✅ LLMResponse created: {response}")


def test_openai_provider_creation():
    """Test creating OpenAI provider."""
    logger.info("Testing OpenAI provider creation...")
    
    provider = OpenAIProvider(
        model="gpt-4o",
        temperature=0.3,
        max_tokens=3000,
        timeout_seconds=45,
    )
    
    assert provider.model == "gpt-4o"
    assert provider.temperature == 0.3
    assert provider.max_tokens == 3000
    assert provider.timeout_seconds == 45
    assert provider.get_provider_name() == "openai"
    
    logger.info(f"   ✅ OpenAI provider created: {provider.model}")


def test_anthropic_provider_creation():
    """Test creating Anthropic provider."""
    logger.info("Testing Anthropic provider creation...")
    
    provider = AnthropicProvider(
        model="claude-sonnet-4",
        temperature=0.2,
        max_tokens=4000,
        timeout_seconds=60,
    )
    
    assert provider.model == "claude-sonnet-4"
    assert provider.temperature == 0.2
    assert provider.max_tokens == 4000
    assert provider.timeout_seconds == 60
    assert provider.get_provider_name() == "anthropic"
    
    logger.info(f"   ✅ Anthropic provider created: {provider.model}")


async def test_openai_provider_api_key_validation():
    """Test OpenAI provider API key validation."""
    logger.info("Testing OpenAI API key validation...")
    
    provider = OpenAIProvider(model="gpt-4o")
    result = await provider.validate_api_key()
    
    if result:
        logger.info(f"   ✅ OpenAI API key is valid")
    else:
        logger.warning(f"   ⚠️  OpenAI API key not found (expected in test env)")


async def test_anthropic_provider_api_key_validation():
    """Test Anthropic provider API key validation."""
    logger.info("Testing Anthropic API key validation...")
    
    provider = AnthropicProvider(model="claude-sonnet-4")
    result = await provider.validate_api_key()
    
    if result:
        logger.info(f"   ✅ Anthropic API key is valid")
    else:
        logger.warning(f"   ⚠️  Anthropic API key not found (expected in test env)")


def test_agent_llm_settings():
    """Test AgentLLMSettings."""
    logger.info("Testing AgentLLMSettings...")
    
    settings = AgentLLMSettings(
        provider="openai",
        model="gpt-4o",
        temperature=0.4,
        max_tokens=2000,
        timeout_seconds=30,
    )
    
    assert settings.provider == "openai"
    assert settings.model == "gpt-4o"
    
    logger.info(f"   ✅ Settings created: {settings}")


def test_agent_llm_factory_creation():
    """Test factory creating providers from settings."""
    logger.info("Testing AgentLLMFactory...")
    
    settings_openai = AgentLLMSettings(
        provider="openai",
        model="gpt-4o",
    )
    provider_openai = AgentLLMFactory.create_provider(settings_openai)
    assert isinstance(provider_openai, OpenAIProvider)
    logger.info(f"   ✅ Factory created OpenAI provider")
    
    settings_anthropic = AgentLLMSettings(
        provider="anthropic",
        model="claude-sonnet-4",
    )
    provider_anthropic = AgentLLMFactory.create_provider(settings_anthropic)
    assert isinstance(provider_anthropic, AnthropicProvider)
    logger.info(f"   ✅ Factory created Anthropic provider")


def test_agent_llm_factory_supported_providers():
    """Test factory supported providers."""
    logger.info("Testing factory supported providers...")
    
    supported = AgentLLMFactory.get_supported_providers()
    assert "openai" in supported
    assert "anthropic" in supported
    
    logger.info(f"   ✅ Supported providers: {supported}")
    
    info = AgentLLMFactory.get_provider_info()
    logger.info(f"   ✅ Provider info: {info}")


def test_agent_llm_factory_with_config():
    """Test factory with actual config file."""
    logger.info("Testing factory with config file...")
    
    config_path = Path(
        "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.json"
    )
    
    if config_path.exists():
        AgentLLMConfigManager.initialize(config_path)
        
        provider = AgentLLMFactory.get_provider_for_agent("supervisor")
        assert provider.get_provider_name() == "openai"
        logger.info(f"   ✅ Supervisor provider: {provider.get_provider_name()}:{provider.model}")
        
        provider = AgentLLMFactory.get_provider_for_agent("codesmith")
        assert provider.get_provider_name() == "anthropic"
        logger.info(f"   ✅ Codesmith provider: {provider.get_provider_name()}:{provider.model}")
    else:
        logger.warning(f"   ⚠️  Config file not found, skipping")


if __name__ == "__main__":
    logger.info("🔬 Starting LLM provider tests...\n")
    
    test_llm_response()
    logger.info("---")
    test_openai_provider_creation()
    logger.info("---")
    test_anthropic_provider_creation()
    logger.info("---")
    asyncio.run(test_openai_provider_api_key_validation())
    logger.info("---")
    asyncio.run(test_anthropic_provider_api_key_validation())
    logger.info("---")
    test_agent_llm_settings()
    logger.info("---")
    test_agent_llm_factory_creation()
    logger.info("---")
    test_agent_llm_factory_supported_providers()
    logger.info("---")
    test_agent_llm_factory_with_config()
    logger.info("\n✅ All LLM provider tests passed!")
