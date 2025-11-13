"""
Supervisor Pattern Implementation for KI AutoAgent v7.0

This module implements the central orchestrator using GPT-4o that makes
ALL routing decisions in the system. No more distributed intelligence!

Key Principles:
1. Single decision maker - only the Supervisor decides routing
2. Agents are "dumb" tools - they only execute instructions
3. Research is a support agent - never user-facing
4. Dynamic instructions - no hardcoded modes
5. Self-invocation possible - agents can be called multiple times

Author: KI AutoAgent Team
Version: 7.0.0-alpha
Date: 2025-10-20
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

# Setup logging
logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class AgentType(str, Enum):
    """Available agents in the system."""
    RESEARCH = "research"
    ARCHITECT = "architect"
    CODESMITH = "codesmith"
    REVIEWFIX = "reviewfix"
    RESPONDER = "responder"
    HITL = "hitl"


class SupervisorAction(str, Enum):
    """Possible supervisor actions."""
    CONTINUE = "CONTINUE"  # Continue with next agent
    PARALLEL = "PARALLEL"  # Run multiple agents in parallel
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
        description="Agents to run in parallel (for PARALLEL action)"
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

class Supervisor:
    """
    Central orchestrator using GPT-4o for all routing decisions.

    This is the ONLY decision maker in the v7.0 architecture.
    All agents are subordinate tools that execute instructions.
    """

    def __init__(self, model: str = "gpt-4o-2024-11-20", temperature: float = 0.3):
        """
        Initialize the Supervisor.

        Args:
            model: OpenAI model to use for decisions
            temperature: Creativity level (0.0-1.0), lower = more deterministic
        """
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=1500
        )

        # Track workflow history for learning
        self.workflow_history: list[dict] = []

        logger.info(f"🎯 Supervisor initialized with {model}")

    async def decide_next(self, state: dict[str, Any]) -> Command:
        """
        Main decision function that analyzes state and decides next action.

        This is the core of the Supervisor Pattern - ALL routing decisions
        happen here, not in individual agents.

        Args:
            state: Current workflow state

        Returns:
            Command object with routing decision
        """
        # Get session_id for event streaming
        session_id = state.get("session_id", "unknown")

        # Import event streaming utilities
        from backend.utils.event_stream import send_supervisor_decision, send_agent_think

        # Send thinking event
        await send_agent_think(
            session_id=session_id,
            agent="supervisor",
            thinking="Analyzing current state and making routing decision...",
            details={
                "iteration": state.get("iteration", 0),
                "last_agent": state.get("last_agent")
            }
        )

        # Build context from state
        context = self._build_context(state)

        # ========================================================================
        # EXPLICIT TERMINATION CONDITIONS (Pattern C - Hybrid)
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

        # Condition 4: Explicit supervisor FINISH decision (checked later in _decision_to_command)
        # This happens when the supervisor LLM decides the task is complete

        # ========================================================================
        # NORMAL ROUTING LOGIC
        # ========================================================================

        # Check if any agent requested research
        if context.needs_research and context.research_request:
            logger.info(f"📚 Agent requested research: {context.research_request}")
            return self._route_to_research(context)

        # Build decision prompt
        prompt = self._build_decision_prompt(context)

        # Get structured decision from LLM
        try:
            # ⏱️ RATE LIMITING: Wait if needed to respect rate limits
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
                goto="hitl",  # Use string node name
                update={
                    "instructions": f"Supervisor error: {str(e)}. Please provide guidance.",
                    "error": str(e)
                }
            )

        # Log decision
        logger.info(f"🤔 Supervisor decision: {decision.action}")
        logger.info(f"   Reasoning: {decision.reasoning}")
        logger.info(f"   Confidence: {decision.confidence:.2f}")

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
        """Route to research agent when requested by another agent."""
        return Command(
            goto="research",  # Use string node name, not enum
            update={
                "instructions": f"Research requested: {context.research_request}",
                "needs_research": False,  # Reset flag
                "research_request": None
            }
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the Supervisor."""
        return """You are the Supervisor, the ONLY decision maker in a multi-agent system.

Your job is to orchestrate agents to complete tasks. You decide:
- Which agent to call next
- What instructions to give them
- When to call the same agent again (self-invocation)
- When the task is complete

Available agents and their capabilities:

1. RESEARCH - Support agent (NOT user-facing):
   - Analyzes workspace and codebase
   - Searches web for best practices
   - Gathers context for other agents
   - Analyzes errors and suggests fixes

2. ARCHITECT - System designer:
   - Designs system architecture
   - Creates file structures
   - Documents systems
   - Needs research context first

3. CODESMITH - Code generator:
   - Implements code from architecture
   - Fixes bugs
   - Needs architecture first

4. REVIEWFIX - Quality assurance:
   - Reviews code quality
   - Runs build validation
   - Fixes issues
   - MANDATORY after code generation (Asimov Rule 1)

5. RESPONDER - User interface (ONLY agent that talks to users):
   - Formats final responses
   - Summarizes results for users
   - Creates readable output

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

WORKFLOW PATTERNS:
- CREATE: research → architect → codesmith → reviewfix → responder
- EXPLAIN: research → responder
- FIX: research → (architect) → codesmith → reviewfix → responder

Remember: You are the ONLY decision maker. Agents don't decide routing!"""

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
            progress.append("✅ Research complete (context collected)")
        else:
            progress.append("⏳ Research pending (no context yet)")

        if context.architecture:
            progress.append("✅ Architecture complete")
        else:
            progress.append("⏳ Architecture pending")

        if context.generated_files:
            progress.append(f"✅ Code generated ({len(context.generated_files)} files)")
        else:
            progress.append("⏳ Code generation pending")

        if context.validation_results:
            passed = context.validation_results.get("passed", False)
            if passed:
                progress.append("✅ Validation passed")
            else:
                progress.append("❌ Validation failed (needs fixes)")
        else:
            progress.append("⏳ Validation pending")

        # Add errors if any
        error_info = ""
        # FIX: Handle None errors list
        if context.errors and isinstance(context.errors, list):
            error_info = f"\n\n⚠️ Errors detected:\n" + "\n".join(f"- {e}" for e in context.errors[-3:])

        # Build final prompt
        prompt = f"""Current task: {context.goal}

Workflow Progress:
{chr(10).join(progress)}

Context:
{chr(10).join(context_parts)}
{error_info}

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
        """Convert supervisor decision to LangGraph Command."""

        # Handle FINISH action
        if decision.action == SupervisorAction.FINISH:
            logger.info("✅ Workflow complete")
            return Command(goto=END)

        # Handle CLARIFY action (low confidence)
        if decision.action == SupervisorAction.CLARIFY or decision.confidence < 0.5:
            logger.info("❓ Requesting user clarification")
            return Command(
                goto="hitl",  # Use string node name
                update={
                    "instructions": decision.instructions or "Low confidence - please clarify the request",
                    "confidence": decision.confidence
                }
            )

        # Handle PARALLEL action
        if decision.action == SupervisorAction.PARALLEL and decision.parallel_agents:
            logger.info(f"⚡ Parallel execution: {decision.parallel_agents}")
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
            # Convert enum to string if needed
            agent_name = decision.next_agent.value if hasattr(decision.next_agent, 'value') else str(decision.next_agent).lower()

            # Check for self-invocation
            is_self_invocation = (agent_name == context.last_agent)
            if is_self_invocation:
                logger.info(f"🔄 Self-invocation: {agent_name} (iteration {context.iteration + 1})")
            else:
                logger.info(f"➡️ Routing to: {agent_name}")

            return Command(
                goto=agent_name,  # Use string node name
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
            goto="hitl",  # Use string node name
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
            "success": success
        })

        # TODO: Implement learning mechanism
        # - Store successful patterns
        # - Adjust confidence thresholds
        # - Optimize instruction templates

        logger.info(f"📊 Workflow outcome recorded (success={success})")


# ============================================================================
# Helper Functions
# ============================================================================

def create_supervisor() -> Supervisor:
    """Factory function to create a configured Supervisor instance."""
    return Supervisor(
        model="gpt-4o-2024-11-20",
        temperature=0.3
    )


# ============================================================================
# Export
# ============================================================================

__all__ = [
    "Supervisor",
    "SupervisorDecision",
    "SupervisorContext",
    "SupervisorAction",
    "AgentType",
    "create_supervisor"
]