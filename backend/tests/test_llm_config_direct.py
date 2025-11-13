import sys
import logging
import importlib.util
from pathlib import Path

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("test_llm_config_direct")

llm_config_path = Path("/Users/dominikfoert/git/KI_AutoAgent/backend/core/llm_config.py")
spec = importlib.util.spec_from_file_location("llm_config", llm_config_path)
llm_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(llm_config)

AgentLLMSettings = llm_config.AgentLLMSettings
DefaultLLMSettings = llm_config.DefaultLLMSettings
AgentLLMConfig = llm_config.AgentLLMConfig
AgentLLMConfigManager = llm_config.AgentLLMConfigManager


def test_agent_llm_settings():
    """Test AgentLLMSettings dataclass."""
    logger.info("Testing AgentLLMSettings...")
    
    settings = AgentLLMSettings(
        provider="openai",
        model="gpt-4o",
        temperature=0.3,
        max_tokens=3000,
        timeout_seconds=45,
        description="Test",
    )
    
    assert settings.provider == "openai"
    assert settings.model == "gpt-4o"
    assert settings.temperature == 0.3
    assert settings.max_tokens == 3000
    assert settings.timeout_seconds == 45
    
    logger.info(f"   ✅ Created settings: {settings}")
    
    data = settings.to_dict()
    assert isinstance(data, dict)
    logger.info(f"   ✅ to_dict() works: {data}")


def test_default_llm_settings():
    """Test DefaultLLMSettings dataclass."""
    logger.info("Testing DefaultLLMSettings...")
    
    defaults = DefaultLLMSettings()
    assert defaults.temperature == 0.4
    assert defaults.max_tokens == 2000
    assert defaults.timeout_seconds == 30
    
    logger.info(f"   ✅ Created defaults: {defaults.to_dict()}")


def test_agent_llm_config_load():
    """Test AgentLLMConfig loading."""
    logger.info("Testing AgentLLMConfig.load_from_file()...")
    
    config_path = Path(
        "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.json"
    )
    
    config = AgentLLMConfig.load_from_file(config_path)
    
    assert config.version == "1.0"
    assert len(config.agents) == 6
    logger.info(f"   ✅ Loaded config: {config}")
    
    for agent_name in ["supervisor", "codesmith", "architect", "research", "reviewfix", "responder"]:
        assert agent_name in config.agents
        logger.info(f"      ✅ {agent_name}: {config.agents[agent_name]}")


def test_agent_llm_config_get_settings():
    """Test getting agent settings from config."""
    logger.info("Testing AgentLLMConfig.get_agent_settings()...")
    
    config_path = Path(
        "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.json"
    )
    
    config = AgentLLMConfig.load_from_file(config_path)
    
    supervisor = config.get_agent_settings("supervisor")
    assert supervisor is not None
    assert supervisor.provider == "openai"
    assert supervisor.model == "gpt-4o-2024-11-20"
    logger.info(f"   ✅ Supervisor settings: {supervisor}")
    
    codesmith = config.get_agent_settings("codesmith")
    assert codesmith is not None
    assert codesmith.provider == "anthropic"
    logger.info(f"   ✅ Codesmith settings: {codesmith}")


def test_agent_llm_config_manager():
    """Test AgentLLMConfigManager singleton."""
    logger.info("Testing AgentLLMConfigManager...")
    
    config_path = Path(
        "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.json"
    )
    
    manager = AgentLLMConfigManager.initialize(config_path)
    logger.info(f"   ✅ Manager initialized: {manager}")
    
    config = AgentLLMConfigManager.get()
    assert config is not None
    logger.info(f"   ✅ Got config from manager: {config}")
    
    supervisor = AgentLLMConfigManager.get_agent_settings("supervisor")
    assert supervisor is not None
    logger.info(f"   ✅ Got agent settings: {supervisor}")


if __name__ == "__main__":
    logger.info("🔬 Starting direct LLM config tests...\n")
    test_agent_llm_settings()
    logger.info("---")
    test_default_llm_settings()
    logger.info("---")
    test_agent_llm_config_load()
    logger.info("---")
    test_agent_llm_config_get_settings()
    logger.info("---")
    test_agent_llm_config_manager()
    logger.info("✅ All direct config tests passed!")
