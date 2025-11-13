import asyncio
import logging
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("test_llm_providers")


def test_provider_files_exist():
    """Test that all provider files exist."""
    logger.info("Testing provider files...")
    
    files = [
        "/Users/dominikfoert/git/KI_AutoAgent/backend/core/llm_providers/base.py",
        "/Users/dominikfoert/git/KI_AutoAgent/backend/core/llm_providers/openai_provider.py",
        "/Users/dominikfoert/git/KI_AutoAgent/backend/core/llm_providers/anthropic_provider.py",
        "/Users/dominikfoert/git/KI_AutoAgent/backend/core/llm_providers/__init__.py",
    ]
    
    for file in files:
        path = Path(file)
        assert path.exists(), f"File not found: {file}"
        logger.info(f"   ✅ {path.name} exists ({path.stat().st_size} bytes)")


def test_factory_file_exists():
    """Test that factory file exists."""
    logger.info("Testing factory file...")
    
    factory_path = Path("/Users/dominikfoert/git/KI_AutoAgent/backend/core/llm_factory.py")
    assert factory_path.exists(), "Factory file not found"
    logger.info(f"   ✅ llm_factory.py exists ({factory_path.stat().st_size} bytes)")


def test_config_file_exists():
    """Test that config file exists."""
    logger.info("Testing config file...")
    
    config_path = Path(
        "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.json"
    )
    assert config_path.exists(), "Config file not found"
    
    with open(config_path) as f:
        config = json.load(f)
    
    logger.info(f"   ✅ agent_llm_config.json exists with {len(config['agents'])} agents")


def test_provider_implementations():
    """Test that provider classes are implemented."""
    logger.info("Testing provider implementations...")
    
    base_path = Path("/Users/dominikfoert/git/KI_AutoAgent/backend/core/llm_providers/base.py")
    with open(base_path) as f:
        base_content = f.read()
    
    assert "class LLMProvider(ABC)" in base_content
    assert "async def generate_text" in base_content
    assert "class LLMResponse" in base_content
    logger.info(f"   ✅ Base class has LLMProvider, generate_text, LLMResponse")
    
    openai_path = Path("/Users/dominikfoert/git/KI_AutoAgent/backend/core/llm_providers/openai_provider.py")
    with open(openai_path) as f:
        openai_content = f.read()
    
    assert "class OpenAIProvider(LLMProvider)" in openai_content
    assert "get_provider_name" in openai_content
    assert "validate_api_key" in openai_content
    logger.info(f"   ✅ OpenAI provider has required methods")
    
    anthropic_path = Path("/Users/dominikfoert/git/KI_AutoAgent/backend/core/llm_providers/anthropic_provider.py")
    with open(anthropic_path) as f:
        anthropic_content = f.read()
    
    assert "class AnthropicProvider(LLMProvider)" in anthropic_content
    assert "get_provider_name" in anthropic_content
    assert "validate_api_key" in anthropic_content
    logger.info(f"   ✅ Anthropic provider has required methods")


def test_factory_implementation():
    """Test that factory is implemented."""
    logger.info("Testing factory implementation...")
    
    factory_path = Path("/Users/dominikfoert/git/KI_AutoAgent/backend/core/llm_factory.py")
    with open(factory_path) as f:
        factory_content = f.read()
    
    assert "class AgentLLMFactory" in factory_content
    assert "get_provider_for_agent" in factory_content
    assert "create_provider" in factory_content
    assert "register_provider" in factory_content
    assert "get_supported_providers" in factory_content
    logger.info(f"   ✅ Factory has all required methods")


def test_provider_syntax():
    """Test that all Python files have valid syntax."""
    logger.info("Testing Python syntax...")
    
    import py_compile
    
    files = [
        "/Users/dominikfoert/git/KI_AutoAgent/backend/core/llm_config.py",
        "/Users/dominikfoert/git/KI_AutoAgent/backend/core/llm_factory.py",
        "/Users/dominikfoert/git/KI_AutoAgent/backend/core/llm_providers/base.py",
        "/Users/dominikfoert/git/KI_AutoAgent/backend/core/llm_providers/openai_provider.py",
        "/Users/dominikfoert/git/KI_AutoAgent/backend/core/llm_providers/anthropic_provider.py",
        "/Users/dominikfoert/git/KI_AutoAgent/backend/core/llm_providers/__init__.py",
    ]
    
    for file in files:
        try:
            py_compile.compile(file, doraise=True)
            logger.info(f"   ✅ {Path(file).name} has valid syntax")
        except py_compile.PyCompileError as e:
            logger.error(f"   ❌ {Path(file).name} has syntax error: {e}")
            raise


if __name__ == "__main__":
    logger.info("🔬 Starting provider implementation tests...\n")
    
    test_provider_files_exist()
    logger.info("---")
    test_factory_file_exists()
    logger.info("---")
    test_config_file_exists()
    logger.info("---")
    test_provider_implementations()
    logger.info("---")
    test_factory_implementation()
    logger.info("---")
    test_provider_syntax()
    logger.info("\n✅ All provider implementation tests passed!")
