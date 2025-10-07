from __future__ import annotations

"""
Agent Capabilities Loader
Loads and applies file write permissions from configuration
"""

import logging
import os
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class CapabilitiesLoader:
    """Load and manage agent capabilities"""

    def __init__(self, config_path: str = None):
        """
        Initialize capabilities loader

        Args:
            config_path: Path to capabilities config file
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "agent_capabilities.yaml"
            )
        self.config_path = config_path
        self.capabilities = self._load_capabilities()

    def _load_capabilities(self) -> dict[str, Any]:
        """Load capabilities from YAML config"""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"Capabilities config not found: {self.config_path}")
                return {}

            with open(self.config_path) as f:
                config = yaml.safe_load(f)

            logger.info(
                f"✅ Loaded capabilities for {len(config.get('agents', {}))} agents"
            )
            return config

        except Exception as e:
            logger.error(f"❌ Failed to load capabilities config: {e}")
            return {}

    def get_agent_capabilities(self, agent_name: str) -> dict[str, Any]:
        """
        Get capabilities for a specific agent

        Args:
            agent_name: Name of the agent

        Returns:
            Dict with agent capabilities
        """
        if not self.capabilities:
            return {"file_write": False, "allowed_paths": []}

        agents = self.capabilities.get("agents", {})

        # Try exact match first
        if agent_name in agents:
            return agents[agent_name].get("capabilities", {})

        # Try without 'Agent' suffix
        agent_base = agent_name.replace("Agent", "")
        if agent_base in agents:
            return agents[agent_base].get("capabilities", {})

        # Default to no write permissions
        logger.info(
            f"No capabilities defined for {agent_name}, defaulting to read-only"
        )
        return {"file_write": False, "allowed_paths": []}

    def apply_to_config(self, agent_config: Any) -> Any:
        """
        Apply capabilities to an agent config object

        Args:
            agent_config: Agent configuration object

        Returns:
            Modified config with capabilities
        """
        agent_name = getattr(agent_config, "name", None)
        if not agent_name:
            return agent_config

        capabilities = self.get_agent_capabilities(agent_name)

        # Add capabilities to config
        # Store the old capabilities if they exist (for compatibility)
        old_capabilities = getattr(agent_config, "capabilities", [])

        # Set new capabilities dict
        agent_config.capabilities = capabilities

        # If there were old capabilities in list format, preserve them
        if isinstance(old_capabilities, list) and old_capabilities:
            agent_config.old_capabilities = old_capabilities

        logger.debug(
            f"Applied capabilities to {agent_name}: write={capabilities.get('file_write', False)}"
        )
        return agent_config

    def can_agent_write(self, agent_name: str, file_path: str = None) -> bool:
        """
        Check if an agent can write files

        Args:
            agent_name: Name of the agent
            file_path: Optional specific file path to check

        Returns:
            True if agent can write (to the specific path if provided)
        """
        capabilities = self.get_agent_capabilities(agent_name)

        # Check general write permission
        if not capabilities.get("file_write", False):
            return False

        # If no specific path, just return write permission
        if not file_path:
            return True

        # Check if path is allowed
        allowed_paths = capabilities.get("allowed_paths", [])
        if not allowed_paths:
            return False

        # Convert to absolute path
        abs_path = os.path.abspath(file_path)

        # Check each allowed path pattern
        for pattern in allowed_paths:
            # Handle glob patterns
            if "**" in pattern or "*" in pattern:
                import fnmatch

                # Normalize pattern
                norm_pattern = pattern
                if norm_pattern.startswith("./"):
                    norm_pattern = norm_pattern[2:]

                # Check different matching strategies
                if "**" in norm_pattern:
                    # Handle recursive glob
                    # Convert ./backend/**/*.py to check if path matches
                    parts = norm_pattern.split("**")
                    if len(parts) == 2:
                        prefix = parts[0].rstrip("/")
                        suffix = parts[1].lstrip("/")

                        # Check if path starts with prefix and matches suffix pattern
                        if file_path.startswith(prefix):
                            remaining = file_path[len(prefix) :].lstrip("/")
                            if fnmatch.fnmatch(remaining, suffix.lstrip("/")):
                                return True
                else:
                    # Simple glob pattern
                    if fnmatch.fnmatch(file_path, norm_pattern):
                        return True
            else:
                # Direct path check
                abs_allowed = os.path.abspath(pattern)
                if abs_path.startswith(abs_allowed):
                    return True

        return False

    def get_all_capabilities(self) -> dict[str, dict[str, Any]]:
        """Get capabilities for all agents"""
        return self.capabilities.get("agents", {})


# Singleton instance
_capabilities_loader = None


def get_capabilities_loader() -> CapabilitiesLoader:
    """Get or create the singleton capabilities loader"""
    global _capabilities_loader
    if _capabilities_loader is None:
        _capabilities_loader = CapabilitiesLoader()
    return _capabilities_loader


def apply_capabilities_to_agent(agent_config: Any) -> Any:
    """
    Convenience function to apply capabilities to an agent config

    Args:
        agent_config: Agent configuration

    Returns:
        Config with capabilities applied
    """
    loader = get_capabilities_loader()
    return loader.apply_to_config(agent_config)
