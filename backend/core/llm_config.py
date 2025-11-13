import json
import logging
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Literal, Any
from functools import lru_cache

logger = logging.getLogger("agent.llm_config")

type LLMProvider = Literal["openai", "anthropic"]


@dataclass
class AgentLLMSettings:
    """
    Configuration for a single agent's LLM settings.
    
    Example:
        AgentLLMSettings(
            provider="openai",
            model="gpt-4o-2024-11-20",
            temperature=0.4,
            max_tokens=2000,
            timeout_seconds=30
        )
    """
    provider: LLMProvider
    model: str
    temperature: float = 0.4
    max_tokens: int = 2000
    timeout_seconds: int = 30
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return asdict(self)

    def __str__(self) -> str:
        return f"{self.provider}:{self.model} (temp={self.temperature})"

    def __repr__(self) -> str:
        return (
            f"AgentLLMSettings(provider={self.provider!r}, model={self.model!r}, "
            f"temperature={self.temperature}, max_tokens={self.max_tokens}, "
            f"timeout_seconds={self.timeout_seconds})"
        )


@dataclass
class DefaultLLMSettings:
    """Default settings for all agents."""
    temperature: float = 0.4
    max_tokens: int = 2000
    timeout_seconds: int = 30

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AgentLLMConfig:
    """
    Centralized configuration for all agents' LLM settings.
    Loaded from agent_llm_config.json.
    """
    version: str
    agents: dict[str, AgentLLMSettings] = field(default_factory=dict)
    defaults: DefaultLLMSettings = field(default_factory=DefaultLLMSettings)

    @classmethod
    def load_from_file(cls, config_path: str | Path) -> "AgentLLMConfig":
        """
        Load configuration from JSON file.
        
        Args:
            config_path: Path to agent_llm_config.json
            
        Returns:
            AgentLLMConfig instance
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If JSON is invalid
            ValueError: If required fields are missing
        """
        config_path = Path(config_path)
        
        logger.info(f"🔧 Loading LLM config from: {config_path}")
        
        if not config_path.exists():
            logger.error(f"❌ Config file not found: {config_path}")
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
            logger.debug(f"✅ Loaded config JSON ({len(json.dumps(data))} bytes)")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in config: {e}")
            raise ValueError(f"Invalid JSON in config: {e}") from e
        
        if "version" not in data:
            logger.error("❌ Config missing 'version' field")
            raise ValueError("Config missing 'version' field")
        
        if "agents" not in data:
            logger.warning("⚠️  Config missing 'agents' field, using empty dict")
            data["agents"] = {}
        
        defaults = DefaultLLMSettings(
            temperature=data.get("defaults", {}).get("temperature", 0.4),
            max_tokens=data.get("defaults", {}).get("max_tokens", 2000),
            timeout_seconds=data.get("defaults", {}).get("timeout_seconds", 30),
        )
        
        agents: dict[str, AgentLLMSettings] = {}
        for agent_name, agent_config in data.get("agents", {}).items():
            try:
                settings = AgentLLMSettings(
                    provider=agent_config["provider"],
                    model=agent_config["model"],
                    temperature=agent_config.get("temperature", defaults.temperature),
                    max_tokens=agent_config.get("max_tokens", defaults.max_tokens),
                    timeout_seconds=agent_config.get("timeout_seconds", defaults.timeout_seconds),
                    description=agent_config.get("description", ""),
                )
                agents[agent_name] = settings
                logger.debug(f"   ✅ {agent_name}: {settings}")
            except KeyError as e:
                logger.warning(f"⚠️  Agent '{agent_name}' missing required field: {e}")
                continue
        
        config = cls(
            version=data["version"],
            agents=agents,
            defaults=defaults,
        )
        
        logger.info(f"✅ Config loaded: {len(agents)} agents configured")
        return config

    def get_agent_settings(self, agent_name: str) -> AgentLLMSettings | None:
        """Get LLM settings for a specific agent."""
        return self.agents.get(agent_name)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "version": self.version,
            "agents": {
                name: settings.to_dict()
                for name, settings in self.agents.items()
            },
            "defaults": self.defaults.to_dict(),
        }

    def __str__(self) -> str:
        agent_list = ", ".join(self.agents.keys())
        return f"AgentLLMConfig(v{self.version}, agents=[{agent_list}])"


class AgentLLMConfigManager:
    """
    Singleton manager for LLM configuration.
    Handles config loading, caching, and access.
    """
    _instance: "AgentLLMConfigManager | None" = None
    _config: AgentLLMConfig | None = None
    _config_path: Path | None = None

    def __new__(cls) -> "AgentLLMConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, config_path: str | Path | None = None) -> "AgentLLMConfigManager":
        """
        Initialize the singleton with a config file.
        
        Args:
            config_path: Path to agent_llm_config.json
                        If None, looks for it in default locations
        """
        instance = cls()
        
        if config_path is None:
            config_path = cls._find_config_file()
        
        config_path = Path(config_path)
        instance._config_path = config_path
        instance._config = AgentLLMConfig.load_from_file(config_path)
        
        logger.info(f"🎯 LLM Config Manager initialized: {instance._config}")
        return instance

    @staticmethod
    def _find_config_file() -> Path:
        """Find config file in default locations."""
        candidates = [
            Path("/Users/dominikfoert/git/KI_AutoAgent/backend/config/agent_llm_config.json"),
            Path.cwd() / "backend" / "config" / "agent_llm_config.json",
            Path.cwd() / "config" / "agent_llm_config.json",
            Path(__file__).parent.parent / "config" / "agent_llm_config.json",
        ]
        
        for path in candidates:
            if path.exists():
                logger.debug(f"🔍 Found config at: {path}")
                return path
        
        default = candidates[0]
        logger.warning(f"⚠️  No config found, using default path: {default}")
        return default

    @classmethod
    def get(cls) -> AgentLLMConfig:
        """Get the singleton config instance."""
        instance = cls()
        if instance._config is None:
            logger.warning("⚠️  Config not initialized, initializing now...")
            instance.initialize()
        return instance._config

    @classmethod
    def get_agent_settings(cls, agent_name: str) -> AgentLLMSettings:
        """Get settings for a specific agent."""
        config = cls.get()
        settings = config.get_agent_settings(agent_name)
        if settings is None:
            logger.warning(f"⚠️  No settings for agent '{agent_name}', using defaults")
            return AgentLLMSettings(
                provider="openai",
                model="gpt-4o",
                temperature=config.defaults.temperature,
                max_tokens=config.defaults.max_tokens,
                timeout_seconds=config.defaults.timeout_seconds,
            )
        return settings

    @classmethod
    def reload(cls, config_path: str | Path | None = None) -> None:
        """Reload configuration from file."""
        instance = cls()
        logger.info("🔄 Reloading LLM configuration...")
        if config_path is None:
            config_path = instance._config_path or cls._find_config_file()
        instance.initialize(config_path)
        logger.info("✅ Configuration reloaded")


def get_llm_settings_for_agent(agent_name: str) -> AgentLLMSettings:
    """Convenience function to get LLM settings for an agent."""
    return AgentLLMConfigManager.get_agent_settings(agent_name)
