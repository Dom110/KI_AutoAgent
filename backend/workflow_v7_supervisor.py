"""
LangGraph Workflow with Supervisor Pattern v7.0

This module implements the new supervisor-based workflow where
a single LLM orchestrator makes ALL routing decisions.

Key Changes from v6.6:
- No more distributed intelligence (evaluate_task removed)
- No more conditional edges (only supervisor decides)
- Research is a support agent (not user-facing)
- Dynamic instructions instead of modes
- Command-based routing with goto

Author: KI AutoAgent Team
Version: 7.0.0-alpha
Date: 2025-10-20
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langgraph.checkpoint.sqlite import SqliteSaver

# Import our new supervisor
from backend.core.supervisor import Supervisor, AgentType, create_supervisor

# Import simplified agents (to be refactored)
from backend.agents.research_agent import ResearchAgent
from backend.agents.architect_agent import ArchitectAgent
from backend.agents.codesmith_agent import CodesmithAgent
from backend.agents.reviewfix_agent import ReviewFixAgent
from backend.agents.responder_agent import ResponderAgent
from backend.agents.hitl_agent import HITLAgent

# Setup logging
logger = logging.getLogger(__name__)


# ============================================================================
# State Definition
# ============================================================================

class SupervisorState(TypedDict):
    """
    Shared state for the supervisor workflow.

    This state is passed between all nodes in the graph.
    The supervisor reads and updates this state to make decisions.
    """

    # Core workflow data
    messages: list[dict]
    goal: str
    user_query: str
    workspace_path: str

    # Agent tracking
    last_agent: str | None
    iteration: int
    is_self_invocation: bool

    # Instructions from supervisor
    instructions: str

    # Research context (from Research Agent)
    research_context: dict | None
    needs_research: bool
    research_request: str | None

    # Architecture (from Architect Agent)
    architecture: dict | None
    architecture_complete: bool

    # Generated code (from Codesmith Agent)
    generated_files: list | None
    code_complete: bool

    # Validation results (from ReviewFix Agent)
    validation_results: dict | None
    validation_passed: bool
    issues: list | None

    # User response (from Responder Agent)
    user_response: str | None
    response_ready: bool

    # Error tracking
    errors: list[str]
    error_count: int

    # Confidence tracking
    confidence: float
    requires_clarification: bool

    # HITL interaction
    hitl_response: str | None
    awaiting_human: bool


# ============================================================================
# Agent Nodes
# ============================================================================

async def supervisor_node(state: SupervisorState) -> Command:
    """
    Supervisor decision node.

    This is the ONLY node that makes routing decisions.
    All other nodes just execute and return to supervisor.
    """
    logger.info("="*50)
    logger.info("🎯 SUPERVISOR NODE - Making routing decision")
    logger.info("="*50)

    # Get or create supervisor instance
    if not hasattr(supervisor_node, "_supervisor"):
        supervisor_node._supervisor = create_supervisor()

    supervisor = supervisor_node._supervisor

    # Make routing decision
    command = await supervisor.decide_next(state)

    # Log the decision
    logger.info(f"   Decision: Route to {command.goto if hasattr(command, 'goto') else 'END'}")
    if hasattr(command, 'update') and command.update:
        logger.info(f"   Instructions: {command.update.get('instructions', 'None')}")
    else:
        logger.info(f"   Instructions: None (workflow complete)")

    return command


async def research_node(state: SupervisorState) -> Command:
    """
    Research agent execution node.

    Research is a SUPPORT agent - gathers context for other agents.
    Never provides direct user responses!
    """
    logger.info("🔬 RESEARCH NODE - Gathering context")

    instructions = state.get("instructions", "")
    workspace_path = state.get("workspace_path", "")

    # Initialize agent with workspace path for memory access
    agent = ResearchAgent(workspace_path=workspace_path)

    # Execute with supervisor instructions
    result = await agent.execute({
        "instructions": instructions,
        "workspace_path": workspace_path,
        "error_info": state.get("errors", [])
    })

    # Update state and return to supervisor
    update = {
        "research_context": result.get("research_context", {}),
        "last_agent": "research"
    }

    # Always go back to supervisor
    logger.info("   Returning to Supervisor for next decision")
    return Command(goto="supervisor", update=update)


async def architect_node(state: SupervisorState) -> Command:
    """
    Architect agent execution node.

    Designs system architecture using research context.
    """
    logger.info("📐 ARCHITECT NODE - Designing architecture")

    instructions = state.get("instructions", "")
    context = state.get("research_context", {})

    # Check if research context is available
    if not context and not state.get("is_self_invocation"):
        logger.warning("   No research context available!")
        return Command(
            goto="supervisor",
            update={
                "needs_research": True,
                "research_request": "Need workspace analysis before architecture design",
                "last_agent": "architect"
            }
        )

    # Initialize agent
    agent = ArchitectAgent()

    # Execute with supervisor instructions
    result = await agent.execute({
        "instructions": instructions,
        "research_context": context,
        "workspace_path": state.get("workspace_path", "")
    })

    # Check if agent needs research
    if result.get("needs_research"):
        return Command(
            goto="supervisor",
            update={
                "needs_research": True,
                "research_request": result.get("research_request", "Need more context"),
                "last_agent": "architect"
            }
        )

    # Update state and return to supervisor
    update = {
        "architecture": result.get("architecture"),
        "architecture_complete": result.get("architecture_complete", False),
        "last_agent": AgentType.ARCHITECT
    }

    logger.info("   Returning to Supervisor for next decision")
    return Command(goto="supervisor", update=update)


async def codesmith_node(state: SupervisorState) -> Command:
    """
    Codesmith agent execution node.

    Generates code based on architecture and context.
    """
    logger.info("⚒️ CODESMITH NODE - Generating code")

    instructions = state.get("instructions", "")
    architecture = state.get("architecture")
    context = state.get("research_context", {})

    # Check dependencies
    if not architecture and not state.get("is_self_invocation"):
        logger.warning("   No architecture available!")
        return Command(
            goto="supervisor",
            update={
                "needs_research": True,
                "research_request": "Need architecture before code generation",
                "last_agent": "codesmith"
            }
        )

    # Initialize agent
    agent = CodesmithAgent()

    # Execute with supervisor instructions
    result = await agent.execute({
        "instructions": instructions,
        "architecture": architecture,
        "research_context": context,
        "workspace_path": state.get("workspace_path", "")
    })

    # Update state and return to supervisor
    update = {
        "generated_files": result.get("generated_files", []),
        "code_complete": result.get("code_complete", False),
        "last_agent": AgentType.CODESMITH
    }

    logger.info("   Returning to Supervisor for next decision")
    return Command(goto="supervisor", update=update)


async def reviewfix_node(state: SupervisorState) -> Command:
    """
    ReviewFix agent execution node.

    Reviews code quality and fixes issues.
    MANDATORY after code generation (Asimov Rule 1).
    """
    logger.info("🔧 REVIEWFIX NODE - Validating and fixing")

    instructions = state.get("instructions", "")
    generated_files = state.get("generated_files", [])

    # Initialize agent
    agent = ReviewFixAgent()

    # Execute with supervisor instructions
    result = await agent.execute({
        "instructions": instructions,
        "generated_files": generated_files,
        "workspace_path": state.get("workspace_path", "")
    })

    # Check if research is needed for fixes
    if result.get("needs_research"):
        return Command(
            goto="supervisor",
            update={
                "needs_research": True,
                "research_request": result.get("research_request", "Need help with error analysis"),
                "validation_results": result.get("validation_results"),
                "issues": result.get("issues", []),
                "last_agent": "reviewfix"
            }
        )

    # Update state and return to supervisor
    update = {
        "validation_results": result.get("validation_results"),
        "validation_passed": result.get("validation_passed", False),
        "issues": result.get("issues", []),
        "last_agent": AgentType.REVIEWFIX
    }

    logger.info("   Returning to Supervisor for next decision")
    return Command(goto="supervisor", update=update)


async def responder_node(state: SupervisorState) -> Command:
    """
    Responder agent execution node.

    The ONLY agent that formats responses for users!
    Collects all results and creates readable output.
    """
    logger.info("💬 RESPONDER NODE - Formatting user response")

    instructions = state.get("instructions", "")

    # Initialize agent
    agent = ResponderAgent()

    # Gather all results
    all_results = {
        "research_context": state.get("research_context"),
        "architecture": state.get("architecture"),
        "generated_files": state.get("generated_files"),
        "validation_results": state.get("validation_results"),
        "issues": state.get("issues", [])
    }

    # Execute with supervisor instructions
    result = await agent.execute({
        "instructions": instructions,
        "all_results": all_results
    })

    # Update state and return to supervisor
    update = {
        "user_response": result.get("user_response"),
        "response_ready": True,
        "last_agent": "responder"
    }

    logger.info("   Response ready, returning to Supervisor")
    return Command(goto="supervisor", update=update)


async def hitl_node(state: SupervisorState) -> Command:
    """
    Human-in-the-loop node.

    Requests clarification from user when confidence is low.
    """
    logger.info("👤 HITL NODE - Requesting user input")

    instructions = state.get("instructions", "")

    # Initialize agent
    agent = HITLAgent()

    # Execute with supervisor instructions
    result = await agent.execute({
        "instructions": instructions,
        "context": {
            "goal": state.get("goal"),
            "confidence": state.get("confidence", 0.0),
            "errors": state.get("errors", [])
        }
    })

    # Update state and return to supervisor
    update = {
        "hitl_response": result.get("user_input"),
        "awaiting_human": False,
        "last_agent": "hitl"
    }

    logger.info("   User input received, returning to Supervisor")
    return Command(goto="supervisor", update=update)


# ============================================================================
# Workflow Builder
# ============================================================================

def build_supervisor_workflow() -> StateGraph:
    """
    Build the supervisor-based workflow graph.

    This is a RADICAL simplification from v6.6:
    - Only ONE edge defined: START → supervisor
    - Supervisor uses Command(goto=...) for ALL routing
    - No conditional edges!
    - No hardcoded workflows!

    Returns:
        Compiled LangGraph workflow
    """
    logger.info("🏗️ Building Supervisor Workflow v7.0")

    # Create state graph
    graph = StateGraph(SupervisorState)

    # Add nodes (agents)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("research", research_node)
    graph.add_node("architect", architect_node)
    graph.add_node("codesmith", codesmith_node)
    graph.add_node("reviewfix", reviewfix_node)
    graph.add_node("responder", responder_node)
    graph.add_node("hitl", hitl_node)

    # ONLY ONE EDGE! Everything starts at supervisor
    graph.add_edge(START, "supervisor")

    # NO MORE EDGES!
    # Supervisor controls everything with Command(goto=...)
    # Agents return to supervisor with Command(goto="supervisor")

    logger.info("   ✅ Graph structure:")
    logger.info("      START → supervisor")
    logger.info("      supervisor → [any agent] via Command")
    logger.info("      [any agent] → supervisor via Command")
    logger.info("      supervisor → END via Command")

    # Compile workflow without checkpointer for now
    # TODO: Fix checkpointer initialization
    app = graph.compile()

    logger.info("   ✅ Workflow compiled successfully")

    return app


# ============================================================================
# Workflow Execution
# ============================================================================

async def execute_supervisor_workflow(
    user_query: str,
    workspace_path: str
) -> dict[str, Any]:
    """
    Execute the supervisor workflow for a user query.

    This is the main entry point for v7.0 workflows.

    Args:
        user_query: The user's request
        workspace_path: Path to the workspace

    Returns:
        Final workflow state with results
    """
    logger.info("="*60)
    logger.info("🚀 EXECUTING SUPERVISOR WORKFLOW v7.0")
    logger.info("="*60)
    logger.info(f"Query: {user_query}")
    logger.info(f"Workspace: {workspace_path}")

    # Build workflow
    app = build_supervisor_workflow()

    # Initialize state
    initial_state = {
        "messages": [{"role": "user", "content": user_query}],
        "goal": user_query,
        "user_query": user_query,
        "workspace_path": workspace_path,
        "iteration": 0,
        "last_agent": None,
        "is_self_invocation": False,
        "instructions": "",
        "research_context": None,
        "needs_research": False,
        "research_request": None,
        "architecture": None,
        "architecture_complete": False,
        "generated_files": None,
        "code_complete": False,
        "validation_results": None,
        "validation_passed": False,
        "issues": None,
        "user_response": None,
        "response_ready": False,
        "errors": [],
        "error_count": 0,
        "confidence": 1.0,
        "requires_clarification": False,
        "hitl_response": None,
        "awaiting_human": False
    }

    # Execute workflow
    try:
        logger.info("\n📊 Starting workflow execution...")

        # Track the final state by accumulating updates
        final_state = dict(initial_state)

        # Run with streaming for visibility
        async for output in app.astream(initial_state):
            # Log each step
            for node, state_update in output.items():
                logger.info(f"\n   Step: {node}")
                if isinstance(state_update, dict):
                    # Update final state with changes
                    final_state.update(state_update)

                    if "last_agent" in state_update:
                        logger.info(f"   Last Agent: {state_update['last_agent']}")
                    if "instructions" in state_update:
                        logger.info(f"   Instructions: {state_update['instructions'][:100]}...")
                    if "response_ready" in state_update and state_update["response_ready"]:
                        logger.info(f"   ✅ Response ready from Responder!")

        logger.info("\n✅ Workflow execution complete!")

        # Return final state with accumulated updates
        return final_state

    except Exception as e:
        logger.error(f"❌ Workflow execution failed: {e}", exc_info=True)
        raise


# ============================================================================
# Export
# ============================================================================

__all__ = [
    "SupervisorState",
    "build_supervisor_workflow",
    "execute_supervisor_workflow"
]