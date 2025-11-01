"""
⚠️ MCP BLEIBT: Supervisor Pattern for v7.0 Pure MCP Architecture
⚠️ WICHTIG: MCP BLEIBT! Supervisor orchestriert Agents AUSSCHLIESSLICH via MCP!

This module implements the central orchestrator using GPT-4o that makes
ALL routing decisions in the system, using Pure MCP architecture for all
agent communication.

Key Changes from v6.6:
- ALL agent calls go through MCPManager
- Progress notifications forwarded from MCP servers
- No direct agent instantiation
- Pure JSON-RPC communication

Key Principles:
1. Single decision maker - only the Supervisor decides routing
2. Agents are MCP servers - they execute via mcp.call()
3. Research is a support agent - never user-facing
4. Dynamic instructions - no hardcoded modes
5. Self-invocation possible - agents can be called multiple times
6. ⚠️ MCP BLEIBT: All communication via MCPManager!

Author: KI AutoAgent v7.0
Date: 2025-10-30
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.types import Command
from langgraph.graph import END
from pydantic import BaseModel, Field

from backend.utils.rate_limiter import wait_for_provider

# ⚠️ MCP BLEIBT: Import MCPManager for all agent calls!
from backend.utils.mcp_manager import get_mcp_manager, MCPConnectionError, MCPToolError

# Setup logging
logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class AgentType(str, Enum):
    """
    ⚠️ MCP BLEIBT: Available MCP agent servers in the system.

    Each agent is a separate MCP server process.
    """
    RESEARCH = "research"
    ARCHITECT = "architect"
    CODESMITH = "codesmith"
    REVIEWFIX = "reviewfix"
    RESPONDER = "responder"
    HITL = "hitl"


class SupervisorAction(str, Enum):
    """Possible supervisor actions."""
    CONTINUE = "CONTINUE"  # Continue with next agent
    PARALLEL = "PARALLEL"  # Run multiple agents in parallel (via MCP)
    FINISH = "FINISH"      # Complete workflow
    CLARIFY = "CLARIFY"    # Need user clarification


class SupervisorDecision(BaseModel):
    """Structured output from supervisor LLM."""

    action: SupervisorAction = Field(
        description="What action to take next"
    )

    next_agent: AgentType | None = Field(
        default=None,
        description="Next agent to execute (for CONTINUE action)"
    )

    parallel_agents: list[AgentType] | None = Field(
        default=None,
        description="Agents to run in parallel (for PARALLEL action) - ⚠️ MCP BLEIBT: via mcp.call_multiple()"
    )

    instructions: str = Field(
        description="Specific instructions for the agent(s)"
    )

    reasoning: str = Field(
        description="Why this decision was made"
    )

    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in this decision (0.0-1.0)"
    )

    needs_research: bool = Field(
        default=False,
        description="Whether research is needed before proceeding"
    )


@dataclass
class SupervisorContext:
    """Context for supervisor decision-making."""

    goal: str
    messages: list[dict]
    workspace_path: str
    iteration: int = 0
    last_agent: str | None = None
    research_context: dict | None = None
    architecture: dict | None = None
    generated_files: list | None = None
    validation_results: dict | None = None
    errors: list[str] | None = None
    needs_research: bool = False
    research_request: str | None = None


# ============================================================================
# Supervisor Class
# ============================================================================

class SupervisorMCP:
    """
    ⚠️ MCP BLEIBT: Central orchestrator using Pure MCP Architecture.

    This is the ONLY decision maker in the v7.0 architecture.
    All agents are MCP servers that execute via mcp.call().

    Key Difference from v6.6:
    - NO direct agent instantiation
    - ALL agent calls via MCPManager
    - Progress notifications forwarded from MCP servers
    - Pure JSON-RPC communication
    """

    def __init__(
        self,
        workspace_path: str,
        model: str = "gpt-4o-2024-11-20",
        temperature: float = 0.3,
        session_id: str | None = None
    ):
        """
        ⚠️ MCP BLEIBT: Initialize Supervisor with MCP Manager

        Args:
            workspace_path: Workspace path for MCPManager
            model: OpenAI model for decisions
            temperature: Creativity level (0.0-1.0)
            session_id: Session ID for event streaming
        """
        self.workspace_path = workspace_path
        self.session_id = session_id

        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=1500
        )

        # Track workflow history for learning
        self.workflow_history: list[dict] = []

        # ⚠️ MCP BLEIBT: Get MCPManager instance
        # Progress callback will be set by workflow
        self.mcp = get_mcp_manager(workspace_path=workspace_path)

        logger.info(f"🎯 SupervisorMCP initialized with {model}")
        logger.info("⚠️ MCP BLEIBT: Pure MCP architecture active!")

    async def decide_next(self, state: dict[str, Any]) -> Command:
        """
        ⚠️ MCP BLEIBT: Main decision function using MCP architecture

        This is the core of the Supervisor Pattern - ALL routing decisions
        happen here, not in individual agents.

        Key Change: Instead of routing to agent nodes in LangGraph, we now
        document the MCP-based communication pattern.

        Args:
            state: Current workflow state

        Returns:
            Command object with routing decision
        """
        # Get session_id for event streaming
        session_id = state.get("session_id", self.session_id or "unknown")

        # Import event streaming utilities
        from backend.utils.event_stream import send_supervisor_decision, send_agent_think

        # Send thinking event
        await send_agent_think(
            session_id=session_id,
            agent="supervisor",
            thinking="Analyzing current state and making routing decision...",
            details={
                "iteration": state.get("iteration", 0),
                "last_agent": state.get("last_agent"),
                "mcp_architecture": "pure"  # ⚠️ MCP BLEIBT!
            }
        )

        # Build context from state
        context = self._build_context(state)

        # ========================================================================
        # EXPLICIT TERMINATION CONDITIONS
        # ========================================================================

        # Condition 1: Response is ready (Responder completed)
        if state.get("response_ready", False):
            logger.info("✅ Response ready - workflow complete!")
            return Command(goto=END)

        # Condition 2: Too many errors (safety limit)
        error_count = state.get("error_count", 0)
        if error_count > 3:
            logger.error(f"❌ Too many errors ({error_count}) - terminating workflow!")
            return Command(goto=END, update={
                "user_response": f"❌ Workflow failed after {error_count} errors. Please check logs.",
                "response_ready": True
            })

        # Condition 3: Max iterations reached (prevent infinite loops)
        iteration = state.get("iteration", 0)
        if iteration > 20:
            logger.warning(f"⚠️ Max iterations ({iteration}) reached - terminating workflow!")
            return Command(goto=END, update={
                "user_response": f"⚠️ Workflow exceeded maximum iterations ({iteration}). Partial results may be available.",
                "response_ready": True
            })

        # ========================================================================
        # NORMAL ROUTING LOGIC
        # ========================================================================

        # Check if any agent requested research
        if context.needs_research and context.research_request:
            logger.info(f"📚 Agent requested research: {context.research_request}")
            logger.info("⚠️ MCP BLEIBT: Research will be called via mcp.call()")
            return self._route_to_research(context)

        # Build decision prompt
        prompt = self._build_decision_prompt(context)

        # Get structured decision from LLM
        try:
            # ⏱️ RATE LIMITING: Wait if needed
            wait_time = await wait_for_provider("openai")
            if wait_time > 0:
                logger.debug(f"⏸️ Rate limit: waited {wait_time:.2f}s for Supervisor decision")

            decision = await self.llm.with_structured_output(
                SupervisorDecision
            ).ainvoke([
                SystemMessage(content=self._get_system_prompt()),
                HumanMessage(content=prompt)
            ])
        except Exception as e:
            logger.error(f"❌ Supervisor decision failed: {e}")
            # Fallback to HITL on error
            return Command(
                goto="hitl",
                update={
                    "instructions": f"Supervisor error: {str(e)}. Please provide guidance.",
                    "error": str(e)
                }
            )

        # Log decision
        logger.info(f"🤔 Supervisor decision: {decision.action}")
        logger.info(f"   Reasoning: {decision.reasoning}")
        logger.info(f"   Confidence: {decision.confidence:.2f}")
        if decision.next_agent:
            logger.info(f"   ⚠️ MCP BLEIBT: Next agent will be called via mcp.call('{decision.next_agent.value}_agent', ...)")

        # Stream detailed decision to client
        next_agent_str = decision.next_agent.value if decision.next_agent and hasattr(decision.next_agent, 'value') else str(decision.next_agent) if decision.next_agent else "END"
        await send_supervisor_decision(
            session_id=session_id,
            reasoning=decision.reasoning,
            next_agent=next_agent_str,
            confidence=decision.confidence,
            instructions=decision.instructions
        )

        # Convert decision to Command
        return self._decision_to_command(decision, context)

    def _build_context(self, state: dict[str, Any]) -> SupervisorContext:
        """Build context object from state dictionary."""
        return SupervisorContext(
            goal=state.get("goal", state.get("user_query", "")),
            messages=state.get("messages", []),
            workspace_path=state.get("workspace_path", ""),
            iteration=state.get("iteration", 0),
            last_agent=state.get("last_agent"),
            research_context=state.get("research_context"),
            architecture=state.get("architecture"),
            generated_files=state.get("generated_files"),
            validation_results=state.get("validation_results"),
            errors=state.get("errors", []),
            needs_research=state.get("needs_research", False),
            research_request=state.get("research_request")
        )

    def _route_to_research(self, context: SupervisorContext) -> Command:
        """
        ⚠️ MCP BLEIBT: Route to research agent via MCP

        The actual call will be: mcp.call("research_agent", "research", {...})
        """
        logger.info("⚠️ MCP BLEIBT: Routing to research_agent MCP server")
        return Command(
            goto="research",
            update={
                "instructions": f"Research requested: {context.research_request}",
                "needs_research": False,
                "research_request": None
            }
        )

    def _get_system_prompt(self) -> str:
        """
        ⚠️ MCP BLEIBT: System prompt for Supervisor (MCP-aware)
        """
        return """You are the Supervisor, the ONLY decision maker in a Pure MCP multi-agent system.

Your job is to orchestrate MCP agent servers to complete tasks. You decide:
- Which MCP agent to call next
- What instructions to give them
- When to call the same agent again (self-invocation)
- When the task is complete

⚠️ IMPORTANT: All agents are MCP servers that communicate via JSON-RPC protocol!

Available MCP agents and their capabilities:

1. RESEARCH - Support agent (NOT user-facing):
   - Analyzes workspace and codebase
   - Searches web for best practices via Perplexity MCP
   - Gathers context for other agents
   - Analyzes errors and suggests fixes
   - Tool: "research"

2. ARCHITECT - System designer:
   - Designs system architecture
   - Creates file structures
   - Documents systems
   - Needs research context first
   - Uses OpenAI via MCP
   - Tool: "design"

3. CODESMITH - Code generator:
   - Implements code from architecture
   - Fixes bugs
   - Needs architecture first
   - Uses Claude CLI via MCP
   - Tool: "generate"

4. REVIEWFIX - Quality assurance:
   - Reviews code quality
   - Runs build validation
   - Fixes issues
   - MANDATORY after code generation (Asimov Rule 1)
   - Uses Claude CLI via MCP
   - Tool: "review_and_fix"

5. RESPONDER - User interface (ONLY agent that talks to users):
   - Formats final responses
   - Summarizes results for users
   - Creates readable output
   - Pure formatting (no AI)
   - Tool: "format_response"

6. HITL - Human in the loop:
   - Asks for user clarification
   - Gets additional requirements
   - Handles low confidence situations

CRITICAL RULES:
1. Research MUST run before important decisions (workspace analysis)
2. Architect needs research context before designing
3. Codesmith needs architecture before coding
4. ReviewFix is MANDATORY after code generation
5. ONLY Responder talks to users (formats final responses)
6. Agents CAN be called multiple times (refinement/iteration)
7. When confidence < 0.5, use HITL for clarification

⚠️ MCP ARCHITECTURE:
- All agents are MCP servers (separate processes)
- Communication via JSON-RPC over stdin/stdout
- Progress notifications via $/progress
- Parallel execution possible via mcp.call_multiple()

WORKFLOW PATTERNS:
- CREATE: research → architect → codesmith → reviewfix → responder
- EXPLAIN: research → responder
- FIX: research → (architect) → codesmith → reviewfix → responder

Remember: You are the ONLY decision maker. Agents don't decide routing!
⚠️ MCP BLEIBT: All communication via MCP protocol!"""

    def _build_decision_prompt(self, context: SupervisorContext) -> str:
        """Build the decision prompt based on current context."""
        # Build context summary
        context_parts = [
            f"Goal: {context.goal}",
            f"Iteration: {context.iteration}",
            f"Last Agent: {context.last_agent or 'None'}",
        ]

        # Add workflow progress
        progress = []
        if context.research_context:
            progress.append("✅ Research complete (context collected via MCP)")
        else:
            progress.append("⏳ Research pending (no context yet)")

        if context.architecture:
            progress.append("✅ Architecture complete (designed via MCP)")
        else:
            progress.append("⏳ Architecture pending")

        if context.generated_files:
            progress.append(f"✅ Code generated via MCP ({len(context.generated_files)} files)")
        else:
            progress.append("⏳ Code generation pending")

        if context.validation_results:
            passed = context.validation_results.get("passed", False)
            if passed:
                progress.append("✅ Validation passed (reviewed via MCP)")
            else:
                progress.append("❌ Validation failed (needs fixes via MCP)")
        else:
            progress.append("⏳ Validation pending")

        # Add errors if any
        error_info = ""
        if context.errors:
            error_info = f"\n\n⚠️ Errors detected:\n" + "\n".join(f"- {e}" for e in context.errors[-3:])

        # Build final prompt
        prompt = f"""Current task: {context.goal}

Workflow Progress (Pure MCP Architecture):
{chr(10).join(progress)}

Context:
{chr(10).join(context_parts)}
{error_info}

⚠️ Note: All agents are MCP servers. When you route to an agent, the workflow will call:
- mcp.call("research_agent", "research", {{...}})
- mcp.call("architect_agent", "design", {{...}})
- mcp.call("codesmith_agent", "generate", {{...}})
- etc.

Based on the current state, decide the next action.

Important considerations:
1. Has research been done to understand the workspace?
2. Is architecture needed for this task?
3. Has code been generated that needs validation?
4. Are there errors that need investigation?
5. Is the task complete and ready for user response?

Return your decision as structured JSON."""

        return prompt

    def _decision_to_command(
        self,
        decision: SupervisorDecision,
        context: SupervisorContext
    ) -> Command:
        """
        ⚠️ MCP BLEIBT: Convert supervisor decision to LangGraph Command

        The Command will route to MCP agent nodes that call mcp.call().
        """

        # Handle FINISH action
        if decision.action == SupervisorAction.FINISH:
            logger.info("✅ Workflow complete (MCP architecture)")
            return Command(goto=END)

        # Handle CLARIFY action (low confidence)
        if decision.action == SupervisorAction.CLARIFY or decision.confidence < 0.5:
            logger.info("❓ Requesting user clarification (low confidence)")
            return Command(
                goto="hitl",
                update={
                    "instructions": decision.instructions or "Low confidence - please clarify the request",
                    "confidence": decision.confidence
                }
            )

        # Handle PARALLEL action
        if decision.action == SupervisorAction.PARALLEL and decision.parallel_agents:
            logger.info(f"⚡ Parallel execution via MCP: {decision.parallel_agents}")
            logger.info("⚠️ MCP BLEIBT: Will use mcp.call_multiple() for parallel agent calls")
            # Note: LangGraph parallel execution requires special handling
            # For now, we'll execute sequentially
            return Command(
                goto=decision.parallel_agents[0],
                update={
                    "instructions": decision.instructions,
                    "parallel_queue": decision.parallel_agents[1:],
                    "iteration": context.iteration + 1,
                    "last_agent": decision.parallel_agents[0]
                }
            )

        # Handle CONTINUE action (normal flow)
        if decision.action == SupervisorAction.CONTINUE and decision.next_agent:
            # Convert enum to string
            agent_name = decision.next_agent.value if hasattr(decision.next_agent, 'value') else str(decision.next_agent).lower()

            # Check for self-invocation
            is_self_invocation = (agent_name == context.last_agent)
            if is_self_invocation:
                logger.info(f"🔄 Self-invocation via MCP: {agent_name} (iteration {context.iteration + 1})")
            else:
                logger.info(f"➡️ Routing to MCP agent: {agent_name}")

            logger.info(f"⚠️ MCP BLEIBT: Workflow will call mcp.call('{agent_name}_agent', ...)")

            return Command(
                goto=agent_name,
                update={
                    "instructions": decision.instructions,
                    "iteration": context.iteration + 1,
                    "last_agent": agent_name,
                    "is_self_invocation": is_self_invocation
                }
            )

        # Fallback to HITL if decision is unclear
        logger.warning("⚠️ Unclear decision, routing to HITL")
        return Command(
            goto="hitl",
            update={
                "instructions": "Supervisor decision unclear - please provide guidance",
                "decision": decision.dict()
            }
        )

    async def learn_from_outcome(
        self,
        workflow: dict,
        outcome: dict,
        success: bool
    ):
        """
        Learn from workflow outcomes to improve future decisions.

        This enables the supervisor to adapt and improve over time.

        Args:
            workflow: The workflow that was executed
            outcome: The final outcome/results
            success: Whether the workflow was successful
        """
        self.workflow_history.append({
            "workflow": workflow,
            "outcome": outcome,
            "success": success,
            "architecture": "pure_mcp"  # ⚠️ MCP BLEIBT!
        })

        # TODO: Implement learning mechanism
        # - Store successful MCP patterns
        # - Adjust confidence thresholds
        # - Optimize instruction templates
        # - Track MCP server performance

        logger.info(f"📊 Workflow outcome recorded (success={success}, architecture=pure_mcp)")


# ============================================================================
# Helper Functions
# ============================================================================

def create_supervisor_mcp(workspace_path: str, session_id: str | None = None) -> SupervisorMCP:
    """
    ⚠️ MCP BLEIBT: Factory function to create Pure MCP Supervisor

    Args:
        workspace_path: Workspace path for MCPManager
        session_id: Session ID for event streaming

    Returns:
        SupervisorMCP instance configured for Pure MCP architecture
    """
    logger.info("⚠️ MCP BLEIBT: Creating SupervisorMCP with Pure MCP architecture")
    return SupervisorMCP(
        workspace_path=workspace_path,
        model="gpt-4o-2024-11-20",
        temperature=0.3,
        session_id=session_id
    )


# ============================================================================
# Export
# ============================================================================

__all__ = [
    "SupervisorMCP",
    "SupervisorDecision",
    "SupervisorContext",
    "SupervisorAction",
    "AgentType",
    "create_supervisor_mcp"
]
