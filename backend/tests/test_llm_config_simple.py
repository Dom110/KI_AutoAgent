import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_llm_config")


def test_config_file_exists():
    """Test that config file exists."""
    config_path = Path(
        "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.json"
    )
    assert config_path.exists(), f"Config file not found: {config_path}"
    logger.info(f"✅ Config file exists: {config_path}")


def test_config_is_valid_json():
    """Test that config is valid JSON."""
    config_path = Path(
        "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.json"
    )
    with open(config_path) as f:
        data = json.load(f)
    assert isinstance(data, dict)
    logger.info(f"✅ Config is valid JSON: {len(json.dumps(data))} bytes")


def test_config_has_required_fields():
    """Test that config has required fields."""
    config_path = Path(
        "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.json"
    )
    with open(config_path) as f:
        data = json.load(f)
    
    assert "version" in data, "Missing 'version' field"
    assert "agents" in data, "Missing 'agents' field"
    logger.info(f"✅ Config has required fields")


def test_config_has_all_agents():
    """Test that config has all expected agents."""
    config_path = Path(
        "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.json"
    )
    with open(config_path) as f:
        data = json.load(f)
    
    expected_agents = [
        "supervisor",
        "codesmith",
        "architect",
        "research",
        "reviewfix",
        "responder",
    ]
    
    for agent_name in expected_agents:
        assert agent_name in data["agents"], f"Agent '{agent_name}' not configured"
        agent_config = data["agents"][agent_name]
        assert "provider" in agent_config, f"Agent '{agent_name}' missing 'provider'"
        assert "model" in agent_config, f"Agent '{agent_name}' missing 'model'"
        logger.info(
            f"   ✅ {agent_name}: {agent_config['provider']} - {agent_config['model']}"
        )


def test_config_agent_providers_are_valid():
    """Test that all agent providers are valid."""
    config_path = Path(
        "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.json"
    )
    with open(config_path) as f:
        data = json.load(f)
    
    valid_providers = {"openai", "anthropic"}
    for agent_name, agent_config in data["agents"].items():
        provider = agent_config.get("provider")
        assert provider in valid_providers, f"Invalid provider '{provider}' for {agent_name}"
        logger.info(f"   ✅ {agent_name}: valid provider '{provider}'")


def test_config_agent_settings_are_valid():
    """Test that agent settings are within valid ranges."""
    config_path = Path(
        "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.json"
    )
    with open(config_path) as f:
        data = json.load(f)
    
    for agent_name, agent_config in data["agents"].items():
        temperature = agent_config.get("temperature", 0.4)
        max_tokens = agent_config.get("max_tokens", 2000)
        timeout_seconds = agent_config.get("timeout_seconds", 30)
        
        assert 0 <= temperature <= 2.0, f"Invalid temperature for {agent_name}"
        assert max_tokens > 0, f"Invalid max_tokens for {agent_name}"
        assert timeout_seconds > 0, f"Invalid timeout_seconds for {agent_name}"
        
        logger.info(
            f"   ✅ {agent_name}: temp={temperature}, tokens={max_tokens}, timeout={timeout_seconds}s"
        )


def test_schema_file_exists():
    """Test that schema file exists."""
    schema_path = Path(
        "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.schema.json"
    )
    assert schema_path.exists(), f"Schema file not found: {schema_path}"
    logger.info(f"✅ Schema file exists: {schema_path}")


def test_schema_is_valid_json():
    """Test that schema is valid JSON."""
    schema_path = Path(
        "/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.schema.json"
    )
    with open(schema_path) as f:
        data = json.load(f)
    assert isinstance(data, dict)
    logger.info(f"✅ Schema is valid JSON: {len(json.dumps(data))} bytes")


if __name__ == "__main__":
    test_config_file_exists()
    test_config_is_valid_json()
    test_config_has_required_fields()
    test_config_has_all_agents()
    test_config_agent_providers_are_valid()
    test_config_agent_settings_are_valid()
    test_schema_file_exists()
    test_schema_is_valid_json()
    print("\n✅ All configuration tests passed!")
