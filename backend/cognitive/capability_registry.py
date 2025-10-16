"""
Capability Registry - Central Agent Capability Management

This module provides a centralized registry of all agent capabilities,
enabling intelligent routing, self-discovery, and dynamic orchestration.

Key Features:
- Agent capability definitions with cost/latency estimates
- Mode-specific capabilities per agent
- Intelligent agent selection for tasks
- Dynamic capability discovery

Integration:
- Used by Dynamic Router for agent selection
- Used by Agents for self-calling decisions
- Used by Workflow Planner for cost estimation

Author: KI AutoAgent Team
Version: 6.4.0-beta
Python: 3.13+
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Available agents in the system."""

    RESEARCH = "research"
    ARCHITECT = "architect"
    CODESMITH = "codesmith"
    REVIEWFIX = "reviewfix"


class RiskLevel(str, Enum):
    """Risk levels for agent operations."""

    READ_ONLY = "read_only"         # No modifications
    WRITES_FILES = "writes_files"    # Modifies workspace
    NETWORKED = "networked"          # External API calls
    CRITICAL = "critical"            # Irreversible actions


@dataclass(slots=True, frozen=True)
class AgentMode:
    """Defines a specific operational mode for an agent."""

    name: str
    description: str
    inputs: list[str]
    outputs: list[str]
    cost_estimate: float  # $ per execution
    latency_estimate: float  # seconds
    risk_level: RiskLevel
    requires_approval: bool = False


@dataclass(slots=True, frozen=True)
class AgentCapability:
    """Complete capability definition for an agent."""

    agent_type: AgentType
    description: str
    modes: dict[str, AgentMode]
    default_mode: str
    max_depth: int = 3  # Max recursion depth for self-calling
    max_fanout: int = 5  # Max parallel subgraphs


class CapabilityRegistry:
    """
    Central registry of agent capabilities.

    Provides:
    - Capability lookup by agent/mode
    - Intelligent agent selection for tasks
    - Cost and latency estimation
    - Self-calling rules and limits
    """

    # ========================================================================
    # CAPABILITY DEFINITIONS
    # ========================================================================

    _CAPABILITIES: dict[AgentType, AgentCapability] = {
        # RESEARCH AGENT
        AgentType.RESEARCH: AgentCapability(
            agent_type=AgentType.RESEARCH,
            description="Information gathering, codebase analysis, and debugging",
            default_mode="research",
            modes={
                "research": AgentMode(
                    name="research",
                    description="Web search with Perplexity for new information",
                    inputs=["query", "user_query"],
                    outputs=["findings", "sources", "research_results"],
                    cost_estimate=0.02,
                    latency_estimate=5.0,
                    risk_level=RiskLevel.NETWORKED
                ),
                "explain": AgentMode(
                    name="explain",
                    description="Analyze and explain existing codebase structure",
                    inputs=["workspace_path", "query"],
                    outputs=["analysis", "structure", "explanation"],
                    cost_estimate=0.01,
                    latency_estimate=3.0,
                    risk_level=RiskLevel.READ_ONLY
                ),
                "analyze": AgentMode(
                    name="analyze",
                    description="Deep code analysis, debugging, security scan",
                    inputs=["workspace_path", "focus_area"],
                    outputs=["issues", "recommendations", "security_report"],
                    cost_estimate=0.03,
                    latency_estimate=10.0,
                    risk_level=RiskLevel.READ_ONLY
                ),
                "index": AgentMode(
                    name="index",
                    description="Index codebase for semantic search",
                    inputs=["workspace_path"],
                    outputs=["embeddings", "index_complete"],
                    cost_estimate=0.05,
                    latency_estimate=15.0,
                    risk_level=RiskLevel.READ_ONLY
                )
            }
        ),

        # ARCHITECT AGENT
        AgentType.ARCHITECT: AgentCapability(
            agent_type=AgentType.ARCHITECT,
            description="System architecture design and documentation",
            default_mode="design",
            modes={
                "design": AgentMode(
                    name="design",
                    description="Design new system architecture from requirements",
                    inputs=["requirements", "research_results"],
                    outputs=["architecture", "tech_stack", "diagrams"],
                    cost_estimate=0.04,
                    latency_estimate=8.0,
                    risk_level=RiskLevel.WRITES_FILES
                ),
                "scan": AgentMode(
                    name="scan",
                    description="Reverse-engineer architecture from existing code",
                    inputs=["workspace_path"],
                    outputs=["architecture", "components", "dependencies"],
                    cost_estimate=0.03,
                    latency_estimate=6.0,
                    risk_level=RiskLevel.WRITES_FILES
                ),
                "post_build_scan": AgentMode(
                    name="post_build_scan",
                    description="Document generated code after creation",
                    inputs=["workspace_path", "generated_files"],
                    outputs=["documentation", "architecture"],
                    cost_estimate=0.02,
                    latency_estimate=4.0,
                    risk_level=RiskLevel.WRITES_FILES
                ),
                "re_scan": AgentMode(
                    name="re_scan",
                    description="Update architecture after code modifications",
                    inputs=["workspace_path", "modified_files"],
                    outputs=["updated_architecture", "change_summary"],
                    cost_estimate=0.02,
                    latency_estimate=3.0,
                    risk_level=RiskLevel.WRITES_FILES
                )
            }
        ),

        # CODESMITH AGENT
        AgentType.CODESMITH: AgentCapability(
            agent_type=AgentType.CODESMITH,
            description="Code generation with Claude CLI",
            default_mode="default",
            modes={
                "default": AgentMode(
                    name="default",
                    description="Generate code from architecture and requirements",
                    inputs=["architecture", "instructions", "workspace_path"],
                    outputs=["generated_files", "code"],
                    cost_estimate=0.15,
                    latency_estimate=30.0,
                    risk_level=RiskLevel.WRITES_FILES,
                    requires_approval=True  # File writes need approval
                )
            }
        ),

        # REVIEWFIX AGENT
        AgentType.REVIEWFIX: AgentCapability(
            agent_type=AgentType.REVIEWFIX,
            description="Code review and iterative fixing (Critic pattern)",
            default_mode="default",
            modes={
                "default": AgentMode(
                    name="default",
                    description="Review code quality, run tests, apply fixes",
                    inputs=["workspace_path", "generated_files"],
                    outputs=["quality_score", "feedback", "fixed_files"],
                    cost_estimate=0.08,
                    latency_estimate=20.0,
                    risk_level=RiskLevel.WRITES_FILES
                )
            }
        )
    }

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    @classmethod
    def get_capability(cls, agent: AgentType) -> AgentCapability:
        """
        Get capability definition for an agent.

        Args:
            agent: Agent type

        Returns:
            AgentCapability instance

        Raises:
            KeyError: If agent not found
        """
        if agent not in cls._CAPABILITIES:
            raise KeyError(f"Unknown agent type: {agent}")

        return cls._CAPABILITIES[agent]

    @classmethod
    def get_mode(cls, agent: AgentType, mode: str | None = None) -> AgentMode:
        """
        Get specific mode for an agent.

        Args:
            agent: Agent type
            mode: Mode name (None for default)

        Returns:
            AgentMode instance

        Raises:
            KeyError: If agent or mode not found
        """
        capability = cls.get_capability(agent)

        if mode is None:
            mode = capability.default_mode

        if mode not in capability.modes:
            raise KeyError(f"Unknown mode '{mode}' for agent {agent}")

        return capability.modes[mode]

    @classmethod
    def estimate_cost(cls, agent: AgentType, mode: str | None = None) -> float:
        """
        Estimate cost for agent execution.

        Args:
            agent: Agent type
            mode: Mode name (None for default)

        Returns:
            Estimated cost in USD
        """
        agent_mode = cls.get_mode(agent, mode)
        return agent_mode.cost_estimate

    @classmethod
    def estimate_latency(cls, agent: AgentType, mode: str | None = None) -> float:
        """
        Estimate latency for agent execution.

        Args:
            agent: Agent type
            mode: Mode name (None for default)

        Returns:
            Estimated latency in seconds
        """
        agent_mode = cls.get_mode(agent, mode)
        return agent_mode.latency_estimate

    @classmethod
    def requires_approval(cls, agent: AgentType, mode: str | None = None) -> bool:
        """
        Check if agent/mode requires user approval.

        Args:
            agent: Agent type
            mode: Mode name (None for default)

        Returns:
            True if approval required
        """
        agent_mode = cls.get_mode(agent, mode)
        return agent_mode.requires_approval

    @classmethod
    def get_all_capabilities(cls) -> dict[AgentType, AgentCapability]:
        """
        Get all registered capabilities.

        Returns:
            Dictionary of agent capabilities
        """
        return cls._CAPABILITIES.copy()

    @classmethod
    def list_agents(cls) -> list[AgentType]:
        """
        List all available agents.

        Returns:
            List of agent types
        """
        return list(cls._CAPABILITIES.keys())

    @classmethod
    def list_modes(cls, agent: AgentType) -> list[str]:
        """
        List all available modes for an agent.

        Args:
            agent: Agent type

        Returns:
            List of mode names
        """
        capability = cls.get_capability(agent)
        return list(capability.modes.keys())

    @classmethod
    def find_agent_for_task(
        cls,
        task_description: str,
        available_agents: list[AgentType] | None = None
    ) -> tuple[AgentType, str]:
        """
        Find best agent/mode for a task description.

        Uses simple keyword matching. Can be enhanced with embeddings/LLM.

        Args:
            task_description: Natural language task description
            available_agents: List of agents to consider (None = all)

        Returns:
            Tuple of (agent_type, mode_name)
        """
        if available_agents is None:
            available_agents = cls.list_agents()

        task_lower = task_description.lower()

        # Simple keyword matching (can be enhanced with AI)
        keywords_to_agent_mode = {
            # Research keywords
            "search": (AgentType.RESEARCH, "research"),
            "find information": (AgentType.RESEARCH, "research"),
            "research": (AgentType.RESEARCH, "research"),
            "explain": (AgentType.RESEARCH, "explain"),
            "what does": (AgentType.RESEARCH, "explain"),
            "how does": (AgentType.RESEARCH, "explain"),
            "analyze": (AgentType.RESEARCH, "analyze"),
            "debug": (AgentType.RESEARCH, "analyze"),
            "debugging": (AgentType.RESEARCH, "analyze"),
            "untersuche": (AgentType.RESEARCH, "analyze"),
            "analysiere": (AgentType.RESEARCH, "analyze"),
            "security": (AgentType.RESEARCH, "analyze"),

            # Architect keywords
            "design": (AgentType.ARCHITECT, "design"),
            "architecture": (AgentType.ARCHITECT, "design"),
            "plan": (AgentType.ARCHITECT, "design"),
            "scan": (AgentType.ARCHITECT, "scan"),
            "document": (AgentType.ARCHITECT, "scan"),
            "reverse engineer": (AgentType.ARCHITECT, "scan"),

            # Codesmith keywords
            "create": (AgentType.CODESMITH, "default"),
            "build": (AgentType.CODESMITH, "default"),
            "generate": (AgentType.CODESMITH, "default"),
            "implement": (AgentType.CODESMITH, "default"),
            "develop": (AgentType.CODESMITH, "default"),

            # ReviewFix keywords
            "review": (AgentType.REVIEWFIX, "default"),
            "fix": (AgentType.REVIEWFIX, "default"),
            "improve": (AgentType.REVIEWFIX, "default"),
            "test": (AgentType.REVIEWFIX, "default"),
        }

        # Find matching keywords
        for keyword, (agent, mode) in keywords_to_agent_mode.items():
            if keyword in task_lower and agent in available_agents:
                logger.info(f"🎯 Matched task to {agent}:{mode} via keyword '{keyword}'")
                return (agent, mode)

        # Default: Research in explain mode for analysis tasks
        logger.info("🎯 No keyword match, defaulting to research:explain")
        return (AgentType.RESEARCH, "explain")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_agent_capability(agent: AgentType) -> AgentCapability:
    """Convenience function to get capability."""
    return CapabilityRegistry.get_capability(agent)


def get_agent_mode(agent: AgentType, mode: str | None = None) -> AgentMode:
    """Convenience function to get mode."""
    return CapabilityRegistry.get_mode(agent, mode)


def find_best_agent(task: str) -> tuple[AgentType, str]:
    """Convenience function to find agent for task."""
    return CapabilityRegistry.find_agent_for_task(task)
