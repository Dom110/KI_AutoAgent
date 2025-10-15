from __future__ import annotations

"""
Agent Registry - Central registration and dispatch for all agents
Manages agent lifecycle and routing
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .base.base_agent import BaseAgent, TaskRequest, TaskResult
from .specialized.orchestrator_agent_v2 import OrchestratorAgentV2

# Import capabilities loader
try:
    from config.capabilities_loader import apply_capabilities_to_agent

    CAPABILITIES_AVAILABLE = True
except ImportError:
    CAPABILITIES_AVAILABLE = False
    logger.warning("Capabilities loader not available")

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Agent type enumeration"""

    ORCHESTRATOR = "orchestrator"
    ARCHITECT = "architect"
    CODESMITH = "codesmith"
    OPUS_ARBITRATOR = "opus-arbitrator"
    RESEARCH = "research"
    REVIEWER = "reviewer"
    DOCUBOT = "docubot"
    TRADESTRAT = "tradestrat"
    FIXER = "fixer"
    FIXER_GPT = "fixer_gpt"  # v5.1.0: Alternative fixer using GPT
    PERFORMANCE = "performance_bot"


@dataclass(slots=True)
class RegisteredAgent:
    """Registered agent information"""

    agent_id: str
    agent_type: AgentType
    instance: BaseAgent
    capabilities: list[str]
    model: str
    status: str = "ready"


class AgentRegistry:
    """
    Central registry for all agents
    Handles agent registration, discovery, and dispatch
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.agents: dict[str, RegisteredAgent] = {}
        self.default_agent = AgentType.ORCHESTRATOR

        logger.info("🎯 Agent Registry initialized")

    async def initialize_all_agents(self):
        """
        Initialize all available agents
        """
        logger.info("📦 Initializing all agents...")

        # Initialize core agents
        await self.register_agent(OrchestratorAgentV2())

        # Register specialized agents
        try:
            from .specialized.research_agent import ResearchAgent

            await self.register_agent(ResearchAgent())
            logger.info("✅ ResearchAgent registered")
        except Exception as e:
            logger.warning(f"⚠️  Could not register ResearchAgent: {e}")

        # Register FixerGPT (v5.1.0: Alternative fixer)
        try:
            from .specialized.fixer_gpt_agent import FixerGPTAgent

            await self.register_agent(FixerGPTAgent())
            logger.info("✅ FixerGPTAgent registered")
        except Exception as e:
            logger.warning(f"⚠️  Could not register FixerGPTAgent: {e}")

        # TODO: Register other agents as they are ported
        # await self.register_agent(ArchitectAgent())
        # await self.register_agent(CodeSmithAgent())
        # await self.register_agent(OpusArbitratorAgent())
        # await self.register_agent(ReviewerAgent())
        # await self.register_agent(DocuAgent())

        logger.info(f"✅ Initialized {len(self.agents)} agents")

    async def register_agent(self, agent: BaseAgent) -> bool:
        """
        Register an agent with the registry
        """
        try:
            # Apply capabilities from config if available
            if CAPABILITIES_AVAILABLE:
                agent.config = apply_capabilities_to_agent(agent.config)

                # Update agent's file tools settings - these attributes exist in BaseAgent
                # We need to update them after config is modified
                if isinstance(agent.config.capabilities, dict):
                    agent.can_write = agent.config.capabilities.get("file_write", False)
                    agent.allowed_paths = agent.config.capabilities.get(
                        "allowed_paths", []
                    )
                    logger.info(
                        f"✅ Applied file write permissions to {agent.config.agent_id}: can_write={agent.can_write}"
                    )
                else:
                    # Old format or no capabilities
                    agent.can_write = False
                    agent.allowed_paths = []

            agent_id = agent.config.agent_id

            if agent_id in self.agents:
                logger.warning(f"Agent {agent_id} already registered, updating...")

            # Extract capabilities list
            # Handle both old format (list of enums) and new format (dict with file_write settings)
            if isinstance(agent.config.capabilities, dict):
                # New format - extract capabilities from dict or use default list
                caps_list = []
                if agent.config.capabilities.get("file_write", False):
                    caps_list.append("file_write")
            elif isinstance(agent.config.capabilities, list):
                # Old format - list of capability enums
                caps_list = [
                    cap.value if hasattr(cap, "value") else str(cap)
                    for cap in agent.config.capabilities
                ]
            else:
                caps_list = []

            registered = RegisteredAgent(
                agent_id=agent_id,
                agent_type=AgentType(agent_id),
                instance=agent,
                capabilities=caps_list,
                model=agent.config.model,
                status="ready",
            )

            self.agents[agent_id] = registered

            logger.info(
                f"✅ Registered agent: {agent_id} "
                f"({agent.config.full_name}) "
                f"with model {agent.config.model}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
            return False

    def get_agent(self, agent_id: str) -> BaseAgent | None:
        """
        Get agent by ID
        """
        if agent_id in self.agents:
            return self.agents[agent_id].instance

        logger.warning(f"Agent {agent_id} not found")
        return None

    def get_available_agents(self) -> list[dict[str, Any]]:
        """
        Get list of available agents
        """
        agents = []
        for agent_id, registered in self.agents.items():
            agents.append(
                {
                    "id": agent_id,
                    "name": registered.instance.config.full_name,
                    "model": registered.model,
                    "capabilities": registered.capabilities,
                    "status": registered.status,
                }
            )

        return agents

    async def dispatch_task(
        self, agent_id: str, request: TaskRequest, cancel_token=None
    ) -> TaskResult:
        """
        Dispatch task to specific agent
        """
        agent = self.get_agent(agent_id)

        if not agent:
            # Fallback to orchestrator
            logger.warning(f"Agent {agent_id} not found, using orchestrator")
            agent = self.get_agent(self.default_agent.value)

            if not agent:
                return TaskResult(
                    status="error",
                    content="No agents available",
                    agent="system",
                    execution_time=0,
                )

        try:
            # Mark agent as busy
            if agent_id in self.agents:
                self.agents[agent_id].status = "busy"

            # Execute task with cancel token
            if cancel_token:
                agent.cancel_token = cancel_token
            result = await agent.execute_with_memory(request)

            # Mark agent as ready
            if agent_id in self.agents:
                self.agents[agent_id].status = "ready"

            return result

        except Exception as e:
            logger.error(
                f"Error dispatching task to {agent_id}: {e}", exc_info=True
            )  # Added stack trace

            # Mark agent as ready
            if agent_id in self.agents:
                self.agents[agent_id].status = "ready"

            return TaskResult(
                status="error",
                content=f"Agent execution failed: {str(e)}",
                agent=agent_id,
                execution_time=0,  # Ensure execution_time is set
            )

    def find_agent_by_capability(self, capability: str) -> BaseAgent | None:
        """
        Find agent with specific capability
        """
        for agent_id, registered in self.agents.items():
            if capability in registered.capabilities:
                return registered.instance

        return None

    def get_agents_by_capability(self, capability: str) -> list[BaseAgent]:
        """
        Get all agents with specific capability
        """
        agents = []
        for agent_id, registered in self.agents.items():
            if capability in registered.capabilities:
                agents.append(registered.instance)

        return agents

    async def broadcast_message(self, message: dict[str, Any]):
        """
        Broadcast message to all agents
        """
        for agent_id, registered in self.agents.items():
            try:
                # Send via communication bus if available
                if hasattr(registered.instance, "communication_bus"):
                    await registered.instance.communication_bus.publish(
                        "agent.broadcast", message
                    )
            except Exception as e:
                logger.error(f"Failed to broadcast to {agent_id}: {e}")

    def get_status(self) -> dict[str, Any]:
        """
        Get registry status
        """
        return {
            "total_agents": len(self.agents),
            "ready_agents": sum(1 for a in self.agents.values() if a.status == "ready"),
            "busy_agents": sum(1 for a in self.agents.values() if a.status == "busy"),
            "agents": self.get_available_agents(),
        }

    async def shutdown(self):
        """
        Shutdown all agents gracefully
        """
        logger.info("🛑 Shutting down all agents...")

        for agent_id, registered in self.agents.items():
            try:
                # Call agent cleanup if available
                if hasattr(registered.instance, "cleanup"):
                    await registered.instance.cleanup()

                logger.info(f"✅ Agent {agent_id} shutdown complete")

            except Exception as e:
                logger.error(f"Error shutting down {agent_id}: {e}")

        self.agents.clear()
        logger.info("✅ All agents shutdown complete")


# Global registry instance
_registry = None


def get_agent_registry() -> AgentRegistry:
    """Get global agent registry instance"""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry
