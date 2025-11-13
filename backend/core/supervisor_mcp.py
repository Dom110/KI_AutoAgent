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
import sys
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal
from pathlib import Path

# 🔒 STARTUP GUARD - Enforce proper startup
try:
    from backend.utils.startup_guard import check_startup_method, check_virtual_environment, check_project_root
    check_virtual_environment()
    check_project_root()
    check_startup_method()
except ImportError:
    pass  # Allow fallback if import fails

from langgraph.types import Command
from langgraph.graph import END
from pydantic import BaseModel, Field

from backend.utils.rate_limiter import wait_for_provider

# ⚠️ MCP BLEIBT: Import MCPManager for all agent calls!
from backend.utils.mcp_manager import get_mcp_manager, MCPConnectionError, MCPToolError

# 🔧 Error handling with user guidance
from backend.utils.error_handler import handle_api_error

# ✨ Phase 3: Factory-based LLM Configuration
from backend.core.llm_factory import AgentLLMFactory
from backend.core.llm_config import AgentLLMConfigManager

# Setup logging
logger = logging.getLogger(__name__)

# 🔍 OpenAI Call Counter for debugging rate limits
openai_call_count = 0
openai_call_timestamps = []


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
        session_id: str | None = None
    ):
        """
        ✨ Phase 3: Initialize Supervisor with Factory-based LLM Configuration
        ⚠️ MCP BLEIBT: All agent communication via MCP!

        Args:
            workspace_path: Workspace path for MCPManager
            session_id: Session ID for event streaming
            
        Note:
            LLM configuration is now centralized in:
            backend/config/agent_llm_config.json (supervisor section)
            
            Previously hardcoded parameters (model, temperature, max_tokens)
            are now loaded from config for flexibility and reusability.
        """
        logger.info("🤖 Initializing SupervisorMCP...")
        
        self.workspace_path = workspace_path
        self.session_id = session_id
        
        # ✨ Phase 3: Initialize LLM Config (once per app startup)
        config_path = Path("backend/config/agent_llm_config.json")
        if not config_path.exists():
            logger.error(f"❌ Config file not found: {config_path}")
            raise FileNotFoundError(f"LLM config not found at {config_path}")
        
        logger.info(f"📂 Loading LLM config from: {config_path}")
        AgentLLMConfigManager.initialize(config_path)
        logger.info("   ✅ Config loaded")
        
        # ✨ Phase 3: Get LLM provider from factory
        try:
            self.llm_provider = AgentLLMFactory.get_provider_for_agent("supervisor")
            logger.info(f"   ✅ LLM Provider: {self.llm_provider.get_provider_name()}")
            logger.info(f"   ✅ Model: {self.llm_provider.model}")
            logger.info(f"   ✅ Temperature: {self.llm_provider.temperature}")
            logger.info(f"   ✅ Max tokens: {self.llm_provider.max_tokens}")
            logger.info(f"   ✅ Timeout: {self.llm_provider.timeout_seconds}s")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM provider: {e}")
            raise
        
        # Track workflow history for learning
        self.workflow_history: list[dict] = []
        
        # ⚠️ MCP BLEIBT: Get MCPManager instance
        # Progress callback will be set by workflow
        self.mcp = get_mcp_manager(workspace_path=workspace_path)
        
        logger.info("✅ SupervisorMCP initialized successfully")
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

        # ⚠️ DEBUG: Log termination check
        from backend.workflow_v7_mcp import DEBUG_WORKFLOW
        if DEBUG_WORKFLOW:
            logger.info(f"🔍 DEBUG TERMINATION CHECK:")
            logger.info(f"   response_ready: {state.get('response_ready', False)}")
            logger.info(f"   error_count: {state.get('error_count', 0)}")
            logger.info(f"   iteration: {state.get('iteration', 0)}")

        # Condition 1: Response is ready (Responder completed)
        if state.get("response_ready", False):
            logger.info("✅ Response ready - workflow complete!")
            if DEBUG_WORKFLOW:
                logger.info(f"🔍 DEBUG: Routing to END (response_ready=True)")
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
        # Increased from 20 to 50 to allow research-heavy workflows
        iteration = state.get("iteration", 0)
        if iteration > 50:
            logger.warning(f"⚠️ Max iterations ({iteration}) reached - terminating workflow!")
            return Command(goto=END, update={
                "user_response": f"⚠️ Workflow exceeded maximum iterations ({iteration}). Partial results may be available.",
                "response_ready": True
            })

        # ========================================================================
        # NORMAL ROUTING LOGIC
        # ========================================================================

        # 🚨 ENFORCE MANDATORY WORKFLOW SEQUENCE (Asimov Rule 1)
        # After Codesmith: MUST go to ReviewFix (quality gate)
        if context.last_agent == "codesmith" and context.generated_files:
            logger.info("🚨 MANDATORY ROUTING: Code generated → ReviewFix (quality gate)")
            logger.info(f"   Generated files: {len(context.generated_files)}")
            logger.info("⚠️ MCP BLEIBT: ReviewFix will be called via mcp.call()")
            return self._route_to_reviewfix(context)

        # After ReviewFix: MUST go to Responder (user communication)
        if context.last_agent == "reviewfix" and context.validation_results:
            logger.info("🚨 MANDATORY ROUTING: Validation complete → Responder (user response)")
            logger.info("⚠️ MCP BLEIBT: Responder will be called via mcp.call()")
            return self._route_to_responder(context)

        # After Responder: END workflow
        if context.last_agent == "responder":
            logger.info("✅ Responder completed → Ending workflow")
            return Command(goto=END, update={"response_ready": True})

        # Check if any agent requested research
        if context.needs_research and context.research_request:
            logger.info(f"📚 Agent requested research: {context.research_request}")
            logger.info("⚠️ MCP BLEIBT: Research will be called via mcp.call()")
            return self._route_to_research(context)

        # Build decision prompt
        prompt = self._build_decision_prompt(context)

        # ✨ Phase 3: Get structured decision from Factory-based LLM provider
        try:
            logger.info("🏗️ Requesting structured decision from LLM...")
            logger.debug(f"   Provider: {self.llm_provider.get_provider_name()}")
            logger.debug(f"   Model: {self.llm_provider.model}")
            logger.debug(f"   System prompt ({len(self._get_system_prompt())} chars)")
            logger.debug(f"   User prompt ({len(prompt)} chars)")
            
            # Call LLM with automatic retries and JSON parsing
            decision = await self.llm_provider.generate_structured_output(
                prompt=prompt,
                output_model=SupervisorDecision,
                system_prompt=self._get_system_prompt(),
                max_retries=3
            )
            
            # Log successful decision
            logger.info("✅ Structured decision received")
            logger.info(f"   Action: {decision.action.value if hasattr(decision.action, 'value') else decision.action}")
            logger.info(f"   Reasoning: {decision.reasoning[:80]}...")
            logger.info(f"   Confidence: {decision.confidence:.2f}")
            
        except (ValueError, json.JSONDecodeError) as e:
            # JSON parsing failed
            logger.error(f"❌ Failed to parse LLM response as SupervisorDecision")
            logger.error(f"   Error type: {type(e).__name__}")
            logger.error(f"   Message: {str(e)}")
            logger.debug(f"   Details:", exc_info=True)
            
            error_msg = f"Supervisor failed to parse decision: {str(e)}"
            return Command(
                goto="responder",
                update={
                    "response_ready": True,
                    "response": error_msg,
                    "error": str(e),
                    "last_agent": "supervisor"
                }
            )
            
        except Exception as e:
            # Other errors (API, timeout, etc.)
            logger.error(f"❌ Unexpected error in supervisor decision")
            logger.error(f"   Error type: {type(e).__name__}")
            logger.error(f"   Message: {str(e)}")
            logger.debug(f"   Details:", exc_info=True)
            
            error_msg = f"Supervisor encountered unexpected error: {str(e)}"
            return Command(
                goto="responder",
                update={
                    "response_ready": True,
                    "response": error_msg,
                    "error": str(e),
                    "last_agent": "supervisor"
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
        return self._decision_to_command(decision, context, state)

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

    def _route_to_reviewfix(self, context: SupervisorContext) -> Command:
        """
        ⚠️ MCP BLEIBT: Route to reviewfix agent via MCP

        The actual call will be: mcp.call("reviewfix_agent", "review_and_fix", {...})
        """
        logger.info("⚠️ MCP BLEIBT: Routing to reviewfix_agent MCP server")
        return Command(
            goto="reviewfix",
            update={
                "instructions": f"Review and validate the generated code. Run tests and fix any issues.",
            }
        )

    def _route_to_responder(self, context: SupervisorContext) -> Command:
        """
        ⚠️ MCP BLEIBT: Route to responder agent via MCP

        The actual call will be: mcp.call("responder_agent", "format_response", {...})
        """
        logger.info("⚠️ MCP BLEIBT: Routing to responder_agent MCP server")
        return Command(
            goto="responder",
            update={
                "instructions": f"Format the final response for the user summarizing the work completed.",
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
- Parallel execution ONLY for multiple RESEARCH agents (web searches)
- All other agents MUST run sequentially (dependencies!)

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
        # FIX: Handle None errors list
        if context.errors and isinstance(context.errors, list):
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

🚨 MANDATORY WORKFLOW SEQUENCE:
1. **After Codesmith** (code generated): MUST route to ReviewFix for validation
2. **After ReviewFix** (validation complete): MUST route to Responder for user response
3. **After Responder**: Workflow ends (set response_ready=True)

⚠️ NEVER skip ReviewFix after code generation - this is a CRITICAL quality gate!
⚠️ NEVER return to Research after code is generated - move forward in the workflow!

Based on the current state, decide the next action following the mandatory sequence above.

Important considerations:
1. If code was just generated (✅ Code generated) → Route to REVIEWFIX (mandatory)
2. If validation is complete (✅ Validation passed) → Route to RESPONDER (mandatory)
3. If no code yet and no architecture → Route to RESEARCH or ARCHITECT
4. If task complete and user response ready → END workflow

Return your decision as structured JSON."""

        return prompt

    def _decision_to_command(
        self,
        decision: SupervisorDecision,
        context: SupervisorContext,
        state: dict[str, Any]
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
            logger.info(f"⚠️ Low confidence ({decision.confidence:.2f}) - proceeding with best guess")
            logger.info("⚠️ MCP BLEIBT: HITL not implemented, proceeding with next_agent anyway")
            # Instead of HITL (which is unimplemented), proceed with next_agent
            if decision.next_agent:
                agent_name = decision.next_agent.value if hasattr(decision.next_agent, 'value') else str(decision.next_agent).lower()
                logger.info(f"➡️ Routing to: {agent_name}")
                return Command(
                    goto=agent_name,
                    update={
                        "instructions": decision.instructions,
                        "iteration": context.iteration + 1,
                        "last_agent": agent_name,
                        "confidence": decision.confidence
                    }
                )
            else:
                # No next agent specified, go to responder
                logger.info("➡️ No next agent, routing to responder")
                return Command(
                    goto="responder",
                    update={
                        "response_ready": True,
                        "response": decision.instructions or "Unable to determine next step",
                        "confidence": decision.confidence
                    }
                )

        # Handle PARALLEL action
        if decision.action == SupervisorAction.PARALLEL and decision.parallel_agents:
            logger.info(f"⚡ Parallel execution via MCP: {decision.parallel_agents}")

            # ⚠️ VALIDATION: Only RESEARCH agents allowed in parallel!
            # All other agents MUST run sequentially (dependencies!)
            non_research_agents = [
                agent for agent in decision.parallel_agents
                if agent != AgentType.RESEARCH
            ]

            if non_research_agents:
                logger.warning(f"🚫 PARALLEL BLOCKED: Non-research agents requested: {non_research_agents}")
                logger.warning(f"   Only RESEARCH agents can run in parallel!")
                logger.warning(f"   Forcing sequential execution instead.")

                # Force sequential execution by using CONTINUE action
                decision.action = SupervisorAction.CONTINUE
                decision.next_agent = decision.parallel_agents[0]
                # Fall through to CONTINUE handler below
            else:
                # Valid parallel research - allow it
                logger.info("⚠️ MCP BLEIBT: Will use mcp.call_multiple() for parallel RESEARCH calls")
                # Note: LangGraph parallel execution requires special handling
                # For now, we'll execute sequentially
                return Command(
                    goto=decision.parallel_agents[0].value if hasattr(decision.parallel_agents[0], 'value') else str(decision.parallel_agents[0]),
                    update={
                        "instructions": decision.instructions,
                        "parallel_queue": decision.parallel_agents[1:],
                        "iteration": context.iteration + 1,
                        "last_agent": decision.parallel_agents[0].value if hasattr(decision.parallel_agents[0], 'value') else str(decision.parallel_agents[0])
                    }
                )

        # Handle CONTINUE action (normal flow)
        if decision.action == SupervisorAction.CONTINUE and decision.next_agent:
            # Convert enum to string
            agent_name = decision.next_agent.value if hasattr(decision.next_agent, 'value') else str(decision.next_agent).lower()

            # Check for self-invocation
            is_self_invocation = (agent_name == context.last_agent)

            # 🚨 PREVENT UNNECESSARY SELF-INVOCATIONS AND DETECT ERRORS
            # Track agent call history from state
            agent_history = state.get("agent_history", [])

            # Count recent calls to this agent (last 5 decisions)
            recent_calls = [a for a in agent_history[-5:] if a == agent_name]
            repeated_calls = len(recent_calls)

            if is_self_invocation or repeated_calls >= 2:
                # Check if agent already produced results or is failing repeatedly
                agent_has_results = False
                agent_is_failing = repeated_calls >= 2

                if agent_name == "research" and context.research_context:
                    agent_has_results = True
                    logger.warning(f"⚠️ Preventing self-invocation: Research already has context")
                elif agent_name == "architect" and context.architecture:
                    agent_has_results = True
                    logger.warning(f"⚠️ Preventing self-invocation: Architecture already complete")
                elif agent_name == "codesmith":
                    if context.generated_files:
                        agent_has_results = True
                        logger.warning(f"⚠️ Preventing self-invocation: Code already generated")
                    elif repeated_calls >= 2:
                        # Codesmith called multiple times without success
                        agent_is_failing = True
                        logger.error(f"❌ Codesmith failed {repeated_calls} times - likely has errors!")
                elif agent_name == "reviewfix" and context.validation_results:
                    agent_has_results = True
                    logger.warning(f"⚠️ Preventing self-invocation: Validation already complete")

                if agent_has_results or agent_is_failing:
                    # Either agent already has results, or it's failing repeatedly
                    if agent_has_results:
                        logger.info(f"🚫 Blocking self-invocation of {agent_name} - already has results")
                    elif agent_is_failing:
                        logger.error(f"❌ Blocking repeated calls to {agent_name} - failed {repeated_calls} times")
                        # Add error to state
                        context.errors.append(f"{agent_name} failed {repeated_calls} times")

                    logger.info(f"   Forcing progress to next stage...")

                    # Determine next agent based on workflow
                    if agent_name == "research":
                        next_agent = "architect"
                    elif agent_name == "architect":
                        next_agent = "codesmith"
                    elif agent_name == "codesmith":
                        # If codesmith is failing, skip directly to responder with error
                        if agent_is_failing:
                            logger.error("❌ Codesmith repeatedly failing - going directly to responder")
                            return Command(
                                goto="responder",
                                update={
                                    "instructions": f"Code generation failed after {repeated_calls} attempts. Report error to user.",
                                    "iteration": context.iteration + 1,
                                    "last_agent": agent_name,
                                    "error_count": state.get("error_count", 0) + 1,
                                    "response_ready": True,
                                    "response": f"❌ Code generation failed after multiple attempts. The Codesmith agent appears to have errors."
                                }
                            )
                        else:
                            next_agent = "reviewfix"
                    elif agent_name == "reviewfix":
                        next_agent = "responder"
                    else:
                        next_agent = "responder"

                    logger.info(f"➡️ Redirecting to: {next_agent}")

                    # Track agent history
                    new_agent_history = agent_history + [agent_name]

                    return Command(
                        goto=next_agent,
                        update={
                            "instructions": f"Continue workflow after {agent_name} {'completion' if agent_has_results else 'failure'}",
                            "iteration": context.iteration + 1,
                            "last_agent": agent_name,
                            "is_self_invocation": False,
                            "agent_history": new_agent_history
                        }
                    )
                else:
                    logger.info(f"🔄 Self-invocation via MCP: {agent_name} (iteration {context.iteration + 1})")
            else:
                logger.info(f"➡️ Routing to MCP agent: {agent_name}")

            logger.info(f"⚠️ MCP BLEIBT: Workflow will call mcp.call('{agent_name}_agent', ...)")

            # Track agent history for all normal routing
            new_agent_history = state.get("agent_history", []) + [agent_name]

            return Command(
                goto=agent_name,
                update={
                    "instructions": decision.instructions,
                    "iteration": context.iteration + 1,
                    "last_agent": agent_name,
                    "is_self_invocation": is_self_invocation,
                    "agent_history": new_agent_history
                }
            )

        # Fallback to responder if decision is unclear (HITL not implemented)
        logger.warning("⚠️ Unclear decision - routing to responder with status")
        return Command(
            goto="responder",
            update={
                "response_ready": True,
                "response": "Unable to make clear routing decision. Please try again with a more specific request.",
                "decision": decision.dict() if hasattr(decision, 'dict') else {}
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
    ✨ Phase 3: Factory function to create Supervisor with Factory-based LLM

    Args:
        workspace_path: Workspace path for MCPManager
        session_id: Session ID for event streaming

    Returns:
        SupervisorMCP instance configured with Factory-based LLM
        
    Note:
        ✨ Phase 3 Update: model and temperature parameters removed!
        LLM configuration is now loaded from:
        backend/config/agent_llm_config.json (supervisor section)
        
        This enables centralized configuration management and allows
        easy switching between different LLM providers without code changes.
    """
    logger.info("✨ Phase 3: Creating SupervisorMCP with Factory-based LLM")
    return SupervisorMCP(
        workspace_path=workspace_path,
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
