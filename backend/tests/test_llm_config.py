import json
import logging
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from core.llm_config import (
    AgentLLMSettings,
    DefaultLLMSettings,
    AgentLLMConfig,
    AgentLLMConfigManager,
    get_llm_settings_for_agent,
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_llm_config")


class TestAgentLLMSettings:
    """Test individual agent LLM settings."""

    def test_create_settings_with_defaults(self):
        """Test creating settings with default values."""
        settings = AgentLLMSettings(
            provider="openai",
            model="gpt-4o",
        )
        assert settings.provider == "openai"
        assert settings.model == "gpt-4o"
        assert settings.temperature == 0.4
        assert settings.max_tokens == 2000
        assert settings.timeout_seconds == 30

    def test_create_settings_with_custom_values(self):
        """Test creating settings with custom values."""
        settings = AgentLLMSettings(
            provider="anthropic",
            model="claude-sonnet-4",
            temperature=0.2,
            max_tokens=4000,
            timeout_seconds=60,
            description="Test agent",
        )
        assert settings.provider == "anthropic"
        assert settings.model == "claude-sonnet-4"
        assert settings.temperature == 0.2
        assert settings.max_tokens == 4000
        assert settings.timeout_seconds == 60
        assert settings.description == "Test agent"

    def test_settings_to_dict(self):
        """Test converting settings to dictionary."""
        settings = AgentLLMSettings(
            provider="openai",
            model="gpt-4o",
        )
        data = settings.to_dict()
        assert isinstance(data, dict)
        assert data["provider"] == "openai"
        assert data["model"] == "gpt-4o"

    def test_settings_string_representation(self):
        """Test string representation."""
        settings = AgentLLMSettings(
            provider="openai",
            model="gpt-4o",
        )
        assert "openai:gpt-4o" in str(settings)


class TestAgentLLMConfig:
    """Test agent LLM configuration loading and management."""

    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        config_path = Path(
            "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.json"
        )
        if config_path.exists():
            config = AgentLLMConfig.load_from_file(config_path)
            assert config.version == "1.0"
            assert len(config.agents) > 0
            logger.info(f"✅ Loaded config with {len(config.agents)} agents")

    def test_load_config_with_missing_file(self):
        """Test loading config from non-existent file."""
        with pytest.raises(FileNotFoundError):
            AgentLLMConfig.load_from_file("/nonexistent/path/config.json")

    def test_load_config_with_invalid_json(self):
        """Test loading config with invalid JSON."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text("{ invalid json }")
            with pytest.raises(ValueError):
                AgentLLMConfig.load_from_file(config_path)

    def test_config_with_missing_version(self):
        """Test loading config with missing version field."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps({"agents": {}}))
            with pytest.raises(ValueError):
                AgentLLMConfig.load_from_file(config_path)

    def test_config_with_missing_agents(self):
        """Test loading config with missing agents field."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps({"version": "1.0"}))
            config = AgentLLMConfig.load_from_file(config_path)
            assert config.agents == {}
            logger.info("✅ Config with missing agents field handled correctly")

    def test_config_get_agent_settings(self):
        """Test retrieving agent settings."""
        config_path = Path(
            "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.json"
        )
        if config_path.exists():
            config = AgentLLMConfig.load_from_file(config_path)
            settings = config.get_agent_settings("supervisor")
            if settings:
                assert settings.provider in ["openai", "anthropic"]
                assert settings.model
                logger.info(f"✅ Retrieved supervisor settings: {settings}")

    def test_config_get_nonexistent_agent(self):
        """Test retrieving non-existent agent settings."""
        config_path = Path(
            "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.json"
        )
        if config_path.exists():
            config = AgentLLMConfig.load_from_file(config_path)
            settings = config.get_agent_settings("nonexistent_agent")
            assert settings is None


class TestAgentLLMConfigManager:
    """Test singleton config manager."""

    def test_manager_initialization(self):
        """Test initializing the config manager."""
        config_path = Path(
            "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.json"
        )
        if config_path.exists():
            manager = AgentLLMConfigManager.initialize(config_path)
            assert manager is not None
            logger.info("✅ Config manager initialized successfully")

    def test_manager_get_instance(self):
        """Test getting config manager instance."""
        config_path = Path(
            "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.json"
        )
        if config_path.exists():
            AgentLLMConfigManager.initialize(config_path)
            instance = AgentLLMConfigManager()
            assert instance is not None
            logger.info("✅ Config manager instance retrieved")

    def test_manager_get_agent_settings(self):
        """Test getting agent settings through manager."""
        config_path = Path(
            "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.json"
        )
        if config_path.exists():
            AgentLLMConfigManager.initialize(config_path)
            settings = AgentLLMConfigManager.get_agent_settings("supervisor")
            assert settings is not None
            assert settings.provider in ["openai", "anthropic"]
            logger.info(f"✅ Retrieved agent settings via manager: {settings}")

    def test_manager_get_nonexistent_agent_uses_defaults(self):
        """Test that getting non-existent agent returns defaults."""
        config_path = Path(
            "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.json"
        )
        if config_path.exists():
            AgentLLMConfigManager.initialize(config_path)
            settings = AgentLLMConfigManager.get_agent_settings("nonexistent")
            assert settings is not None
            assert settings.temperature == 0.4
            logger.info(f"✅ Non-existent agent returns defaults: {settings}")


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_get_llm_settings_for_agent(self):
        """Test convenience function for getting agent settings."""
        config_path = Path(
            "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.json"
        )
        if config_path.exists():
            AgentLLMConfigManager.initialize(config_path)
            settings = get_llm_settings_for_agent("supervisor")
            assert settings is not None
            logger.info(f"✅ Convenience function works: {settings}")


class TestDefaultSettings:
    """Test default settings behavior."""

    def test_default_settings_creation(self):
        """Test creating default settings."""
        defaults = DefaultLLMSettings(
            temperature=0.5,
            max_tokens=3000,
            timeout_seconds=45,
        )
        assert defaults.temperature == 0.5
        assert defaults.max_tokens == 3000
        assert defaults.timeout_seconds == 45

    def test_default_settings_to_dict(self):
        """Test converting defaults to dictionary."""
        defaults = DefaultLLMSettings()
        data = defaults.to_dict()
        assert isinstance(data, dict)
        assert "temperature" in data
        assert "max_tokens" in data
        assert "timeout_seconds" in data


class TestConfigIntegration:
    """Integration tests for config system."""

    def test_config_with_all_agents(self):
        """Test that config loads all expected agents."""
        config_path = Path(
            "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.json"
        )
        if config_path.exists():
            config = AgentLLMConfig.load_from_file(config_path)
            expected_agents = [
                "supervisor",
                "codesmith",
                "architect",
                "research",
                "reviewfix",
                "responder",
            ]
            for agent_name in expected_agents:
                assert agent_name in config.agents, f"Agent '{agent_name}' not found"
                logger.info(f"   ✅ {agent_name} configured: {config.agents[agent_name]}")

    def test_config_to_dict_roundtrip(self):
        """Test converting config to dict and back."""
        config_path = Path(
            "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.json"
        )
        if config_path.exists():
            config = AgentLLMConfig.load_from_file(config_path)
            data = config.to_dict()
            assert isinstance(data, dict)
            assert "version" in data
            assert "agents" in data
            logger.info(f"✅ Config to_dict works: {len(json.dumps(data))} bytes")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
