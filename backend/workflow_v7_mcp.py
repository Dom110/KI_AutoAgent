"""
⚠️ MCP BLEIBT: LangGraph Workflow with Pure MCP Architecture v7.0
⚠️ WICHTIG: MCP BLEIBT! Alle Agent-Calls ausschließlich via MCPManager!

This module implements the supervisor-based workflow using Pure MCP architecture
where ALL agent communication goes through MCP servers.

Key Changes from workflow_v7_supervisor.py:
- NO direct agent instantiation (ResearchAgent(), ArchitectAgent(), etc.)
- ALL agent calls via mcp.call()
- Progress callback wired to forward $/progress notifications
- SupervisorMCP instead of Supervisor
- Pure JSON-RPC communication with agents

Key Principles:
- Single supervisor makes ALL routing decisions
- Agents are MCP servers executed via mcp.call()
- Research is a support agent (not user-facing)
- Dynamic instructions instead of modes
- Command-based routing with goto
- ⚠️ MCP BLEIBT: 100% MCP protocol communication!

Author: KI AutoAgent v7.0
Date: 2025-10-30
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langgraph.checkpoint.sqlite import SqliteSaver

# ⚠️ MCP BLEIBT: Import MCP-aware supervisor
from backend.core.supervisor_mcp import SupervisorMCP, AgentType, create_supervisor_mcp

# ⚠️ MCP BLEIBT: Import MCPManager for all agent calls!
from backend.utils.mcp_manager import get_mcp_manager, MCPConnectionError, MCPToolError

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
    session_id: str  # For event streaming

    # Agent tracking
    last_agent: str | None
    iteration: int
    is_self_invocation: bool

    # Instructions from supervisor
    instructions: str

    # Research context (from Research Agent MCP)
    research_context: dict | None
    needs_research: bool
    research_request: str | None

    # Architecture (from Architect Agent MCP)
    architecture: dict | None
    architecture_complete: bool

    # Generated code (from Codesmith Agent MCP)
    generated_files: list | None
    code_complete: bool

    # Validation results (from ReviewFix Agent MCP)
    validation_results: dict | None
    validation_passed: bool
    issues: list | None

    # User response (from Responder Agent MCP)
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
# Agent Nodes (MCP-based)
# ============================================================================

async def supervisor_node(state: SupervisorState) -> Command:
    """
    ⚠️ MCP BLEIBT: Supervisor decision node using SupervisorMCP

    This is the ONLY node that makes routing decisions.
    All other nodes execute via MCP and return to supervisor.
    """
    logger.info("="*50)
    logger.info("🎯 SUPERVISOR NODE (MCP) - Making routing decision")
    logger.info("="*50)

    # Get or create MCP-aware supervisor instance
    if not hasattr(supervisor_node, "_supervisor"):
        workspace_path = state.get("workspace_path", "")
        session_id = state.get("session_id", "unknown")
        supervisor_node._supervisor = create_supervisor_mcp(
            workspace_path=workspace_path,
            session_id=session_id
        )

    supervisor = supervisor_node._supervisor

    # Make routing decision
    command = await supervisor.decide_next(state)

    # Log the decision
    logger.info(f"   Decision: Route to {command.goto if hasattr(command, 'goto') else 'END'}")
    if hasattr(command, 'update') and command.update:
        logger.info(f"   Instructions: {command.update.get('instructions', 'None')}")
        logger.info(f"   ⚠️ MCP BLEIBT: Will be executed via mcp.call()")
    else:
        logger.info(f"   Instructions: None (workflow complete)")

    return command


async def research_node(state: SupervisorState) -> Command:
    """
    ⚠️ MCP BLEIBT: Research agent execution via MCP

    Research is a SUPPORT agent - gathers context for other agents.
    Executes via: mcp.call("research_agent", "research", {...})
    """
    logger.info("🔬 RESEARCH NODE (MCP) - Gathering context via MCP")

    instructions = state.get("instructions", "")
    workspace_path = state.get("workspace_path", "")

    logger.info(f"   Instructions: {instructions[:200]}")
    logger.info(f"   Workspace: {workspace_path}")
    logger.info(f"   ⚠️ MCP BLEIBT: Calling research_agent MCP server...")

    try:
        # ⚠️ MCP BLEIBT: Get MCPManager instance
        mcp = get_mcp_manager(workspace_path=workspace_path)

        # Ensure MCP is initialized
        if not mcp._initialized:
            logger.info("   📡 Initializing MCP connections...")
            await mcp.initialize()
            logger.info("   ✅ MCP initialized")

        # ⚠️ MCP BLEIBT: Execute via MCP call!
        logger.info("   🔧 Calling mcp.call('research_agent', 'research', ...)")
        start_time = asyncio.get_event_loop().time()

        result = await mcp.call(
            server="research_agent",
            tool="research",
            arguments={
                "instructions": instructions,
                "workspace_path": workspace_path,
                "error_info": state.get("errors", [])
            }
        )

        execution_time = asyncio.get_event_loop().time() - start_time
        logger.info(f"   ✅ Research execution completed via MCP in {execution_time:.2f}s")

        # ⚠️ MCP BLEIBT: Extract result from MCP response
        # MCP returns: {"content": [{"type": "text", "text": "..."}], "metadata": {...}}
        content = result.get("content", [])
        if content and len(content) > 0:
            import json
            research_data = json.loads(content[0].get("text", "{}"))
        else:
            logger.error("   ❌ Research returned empty MCP result!")
            research_data = {}

        logger.info(f"   Research result keys: {list(research_data.keys())}")

        # Update state and return to supervisor
        update = {
            "research_context": research_data,
            "last_agent": "research"
        }

        # Always go back to supervisor
        logger.info("   Returning to Supervisor for next decision")
        return Command(goto="supervisor", update=update)

    except (MCPConnectionError, MCPToolError) as e:
        logger.error(f"   ❌ MCP CALL FAILED: {e}", exc_info=True)
        # Return error to supervisor for handling
        return Command(
            goto="supervisor",
            update={
                "last_agent": "research",
                "errors": state.get("errors", []) + [f"Research MCP call failed: {str(e)}"],
                "error_count": state.get("error_count", 0) + 1
            }
        )
    except Exception as e:
        logger.error(f"   ❌ RESEARCH NODE FAILED: {e}", exc_info=True)
        return Command(
            goto="supervisor",
            update={
                "last_agent": "research",
                "errors": state.get("errors", []) + [f"Research failed: {str(e)}"],
                "error_count": state.get("error_count", 0) + 1
            }
        )


async def architect_node(state: SupervisorState) -> Command:
    """
    ⚠️ MCP BLEIBT: Architect agent execution via MCP

    Designs system architecture using research context.
    Executes via: mcp.call("architect_agent", "design", {...})
    """
    logger.info("📐 ARCHITECT NODE (MCP) - Designing architecture via MCP")

    instructions = state.get("instructions", "")
    context = state.get("research_context", {})
    workspace_path = state.get("workspace_path", "")

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

    try:
        # ⚠️ MCP BLEIBT: Get MCPManager instance
        mcp = get_mcp_manager(workspace_path=workspace_path)

        # ⚠️ MCP BLEIBT: Execute via MCP call!
        logger.info("   🔧 Calling mcp.call('architect_agent', 'design', ...)")

        result = await mcp.call(
            server="architect_agent",
            tool="design",
            arguments={
                "instructions": instructions,
                "research_context": context,
                "workspace_path": workspace_path
            }
        )

        # ⚠️ MCP BLEIBT: Extract result from MCP response
        content = result.get("content", [])
        if content and len(content) > 0:
            import json
            arch_data = json.loads(content[0].get("text", "{}"))
        else:
            arch_data = {}

        # Check if agent needs research
        if arch_data.get("needs_research"):
            return Command(
                goto="supervisor",
                update={
                    "needs_research": True,
                    "research_request": arch_data.get("research_request", "Need more context"),
                    "last_agent": "architect"
                }
            )

        # Update state and return to supervisor
        update = {
            "architecture": arch_data,
            "architecture_complete": arch_data.get("architecture_complete", False),
            "last_agent": "architect"
        }

        logger.info("   ✅ Architecture complete via MCP")
        logger.info("   Returning to Supervisor for next decision")
        return Command(goto="supervisor", update=update)

    except (MCPConnectionError, MCPToolError) as e:
        logger.error(f"   ❌ MCP CALL FAILED: {e}", exc_info=True)
        return Command(
            goto="supervisor",
            update={
                "last_agent": "architect",
                "errors": state.get("errors", []) + [f"Architect MCP call failed: {str(e)}"],
                "error_count": state.get("error_count", 0) + 1
            }
        )


async def codesmith_node(state: SupervisorState) -> Command:
    """
    ⚠️ MCP BLEIBT: Codesmith agent execution via MCP

    Generates code based on architecture and context.
    Executes via: mcp.call("codesmith_agent", "generate", {...})
    """
    logger.info("⚒️ CODESMITH NODE (MCP) - Generating code via MCP")

    instructions = state.get("instructions", "")
    architecture = state.get("architecture")
    context = state.get("research_context", {})
    workspace_path = state.get("workspace_path", "")

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

    try:
        # ⚠️ MCP BLEIBT: Get MCPManager instance
        mcp = get_mcp_manager(workspace_path=workspace_path)

        # ⚠️ MCP BLEIBT: Execute via MCP call!
        logger.info("   🔧 Calling mcp.call('codesmith_agent', 'generate', ...)")
        logger.info("   ⚠️ Note: Codesmith via Claude CLI MCP can take several minutes!")

        result = await mcp.call(
            server="codesmith_agent",
            tool="generate",
            arguments={
                "instructions": instructions,
                "architecture": architecture,
                "research_context": context,
                "workspace_path": workspace_path
            },
            timeout=300.0  # 5 minutes for code generation
        )

        # ⚠️ MCP BLEIBT: Extract result from MCP response
        content = result.get("content", [])
        if content and len(content) > 0:
            import json
            code_data = json.loads(content[0].get("text", "{}"))
        else:
            code_data = {}

        # Update state and return to supervisor
        update = {
            "generated_files": code_data.get("generated_files", []),
            "code_complete": code_data.get("code_complete", False),
            "last_agent": "codesmith"
        }

        logger.info(f"   ✅ Code generation complete via MCP ({len(update['generated_files'])} files)")
        logger.info("   Returning to Supervisor for next decision")
        return Command(goto="supervisor", update=update)

    except (MCPConnectionError, MCPToolError) as e:
        logger.error(f"   ❌ MCP CALL FAILED: {e}", exc_info=True)
        return Command(
            goto="supervisor",
            update={
                "last_agent": "codesmith",
                "errors": state.get("errors", []) + [f"Codesmith MCP call failed: {str(e)}"],
                "error_count": state.get("error_count", 0) + 1
            }
        )


async def reviewfix_node(state: SupervisorState) -> Command:
    """
    ⚠️ MCP BLEIBT: ReviewFix agent execution via MCP

    Reviews code quality and fixes issues.
    MANDATORY after code generation (Asimov Rule 1).
    Executes via: mcp.call("reviewfix_agent", "review_and_fix", {...})
    """
    logger.info("🔧 REVIEWFIX NODE (MCP) - Validating and fixing via MCP")

    instructions = state.get("instructions", "")
    generated_files = state.get("generated_files", [])
    workspace_path = state.get("workspace_path", "")

    try:
        # ⚠️ MCP BLEIBT: Get MCPManager instance
        mcp = get_mcp_manager(workspace_path=workspace_path)

        # ⚠️ MCP BLEIBT: Execute via MCP call!
        logger.info("   🔧 Calling mcp.call('reviewfix_agent', 'review_and_fix', ...)")

        result = await mcp.call(
            server="reviewfix_agent",
            tool="review_and_fix",
            arguments={
                "instructions": instructions,
                "generated_files": generated_files,
                "workspace_path": workspace_path
            },
            timeout=300.0  # 5 minutes for review and fixes
        )

        # ⚠️ MCP BLEIBT: Extract result from MCP response
        content = result.get("content", [])
        if content and len(content) > 0:
            import json
            review_data = json.loads(content[0].get("text", "{}"))
        else:
            review_data = {}

        # Check if research is needed for fixes
        if review_data.get("needs_research"):
            return Command(
                goto="supervisor",
                update={
                    "needs_research": True,
                    "research_request": review_data.get("research_request", "Need help with error analysis"),
                    "validation_results": review_data.get("validation_results"),
                    "issues": review_data.get("issues", []),
                    "last_agent": "reviewfix"
                }
            )

        # Update state and return to supervisor
        update = {
            "validation_results": review_data.get("validation_results"),
            "validation_passed": review_data.get("validation_passed", False),
            "issues": review_data.get("issues", []),
            "last_agent": "reviewfix"
        }

        logger.info(f"   ✅ Review complete via MCP (passed={update['validation_passed']})")
        logger.info("   Returning to Supervisor for next decision")
        return Command(goto="supervisor", update=update)

    except (MCPConnectionError, MCPToolError) as e:
        logger.error(f"   ❌ MCP CALL FAILED: {e}", exc_info=True)
        return Command(
            goto="supervisor",
            update={
                "last_agent": "reviewfix",
                "errors": state.get("errors", []) + [f"ReviewFix MCP call failed: {str(e)}"],
                "error_count": state.get("error_count", 0) + 1
            }
        )


async def responder_node(state: SupervisorState) -> Command:
    """
    ⚠️ MCP BLEIBT: Responder agent execution via MCP

    The ONLY agent that formats responses for users!
    Executes via: mcp.call("responder_agent", "format_response", {...})
    """
    logger.info("💬 RESPONDER NODE (MCP) - Formatting user response via MCP")

    instructions = state.get("instructions", "")

    # Gather all results
    all_results = {
        "research_context": state.get("research_context"),
        "architecture": state.get("architecture"),
        "generated_files": state.get("generated_files"),
        "validation_results": state.get("validation_results"),
        "issues": state.get("issues", [])
    }

    try:
        # ⚠️ MCP BLEIBT: Get MCPManager instance
        mcp = get_mcp_manager(workspace_path=state.get("workspace_path", ""))

        # ⚠️ MCP BLEIBT: Execute via MCP call!
        logger.info("   🔧 Calling mcp.call('responder_agent', 'format_response', ...)")

        result = await mcp.call(
            server="responder_agent",
            tool="format_response",
            arguments={
                "workflow_result": all_results,
                "status": "success" if state.get("validation_passed") else "partial"
            }
        )

        # ⚠️ MCP BLEIBT: Extract result from MCP response
        content = result.get("content", [])
        if content and len(content) > 0:
            user_response = content[0].get("text", "")
        else:
            user_response = "Response formatting failed"

        # Update state and return to supervisor
        update = {
            "user_response": user_response,
            "response_ready": True,  # Signal workflow completion
            "last_agent": "responder"
        }

        logger.info("   ✅ Response formatted via MCP - workflow ready to complete")
        logger.info("   Returning to Supervisor for termination")
        return Command(goto="supervisor", update=update)

    except (MCPConnectionError, MCPToolError) as e:
        logger.error(f"   ❌ MCP CALL FAILED: {e}", exc_info=True)
        # Still return something to user
        return Command(
            goto="supervisor",
            update={
                "user_response": f"⚠️ Response formatting failed: {str(e)}",
                "response_ready": True,
                "last_agent": "responder"
            }
        )


async def hitl_node(state: SupervisorState) -> Command:
    """
    Human-in-the-loop node.

    Requests clarification from user when confidence is low.
    Note: HITL is NOT an MCP agent - it's a special UI interaction.
    """
    logger.info("👤 HITL NODE - Requesting user input")

    instructions = state.get("instructions", "")

    # For now, we'll use a simple stub
    # TODO: Implement actual HITL mechanism via WebSocket/SSE

    logger.warning("   ⚠️ HITL not yet implemented - returning to supervisor")

    update = {
        "hitl_response": "User clarification needed (HITL not implemented)",
        "awaiting_human": False,
        "last_agent": "hitl"
    }

    return Command(goto="supervisor", update=update)


# ============================================================================
# Workflow Builder
# ============================================================================

def build_supervisor_workflow_mcp() -> StateGraph:
    """
    ⚠️ MCP BLEIBT: Build the Pure MCP supervisor-based workflow graph

    All agent nodes call mcp.call() instead of direct agent instantiation.

    This is a RADICAL simplification from v6.6:
    - Only ONE edge defined: START → supervisor
    - Supervisor uses Command(goto=...) for ALL routing
    - Agents execute via MCP and return to supervisor
    - No conditional edges!
    - No hardcoded workflows!

    Returns:
        Compiled LangGraph workflow
    """
    logger.info("🏗️ Building Supervisor Workflow v7.0 (PURE MCP)")
    logger.info("⚠️ MCP BLEIBT: All agents are MCP servers!")

    # Create state graph
    graph = StateGraph(SupervisorState)

    # ⚠️ MCP BLEIBT: Add nodes (all MCP-based)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("research", research_node)  # Calls research_agent MCP
    graph.add_node("architect", architect_node)  # Calls architect_agent MCP
    graph.add_node("codesmith", codesmith_node)  # Calls codesmith_agent MCP
    graph.add_node("reviewfix", reviewfix_node)  # Calls reviewfix_agent MCP
    graph.add_node("responder", responder_node)  # Calls responder_agent MCP
    graph.add_node("hitl", hitl_node)  # Special UI node (not MCP)

    # ONLY ONE EDGE! Everything starts at supervisor
    graph.add_edge(START, "supervisor")

    # NO MORE EDGES!
    # Supervisor controls everything with Command(goto=...)
    # Agents return to supervisor with Command(goto="supervisor")

    logger.info("   ✅ Graph structure:")
    logger.info("      START → supervisor")
    logger.info("      supervisor → [any MCP agent] via Command")
    logger.info("      [any MCP agent] → supervisor via Command")
    logger.info("      supervisor → END via Command")
    logger.info("   ⚠️ MCP BLEIBT: All agent nodes use mcp.call()!")

    # Compile workflow
    app = graph.compile()

    logger.info("   ✅ Workflow compiled successfully")
    logger.info("   📊 Recursion limit: 25 (LangGraph default)")
    logger.info("   ⚠️ MCP BLEIBT: Pure MCP architecture active!")

    return app


# ============================================================================
# Workflow Execution
# ============================================================================

async def execute_supervisor_workflow_streaming_mcp(
    user_query: str,
    workspace_path: str,
    session_id: str = "unknown"
):
    """
    ⚠️ MCP BLEIBT: Execute Pure MCP workflow with streaming

    Yields workflow events as they occur for real-time client feedback.
    Progress notifications from MCP servers are forwarded via event stream.

    Args:
        user_query: The user's request
        workspace_path: Path to the workspace
        session_id: Session ID for event streaming

    Yields:
        Dict events with type and data
    """
    logger.info("="*60)
    logger.info("🚀 EXECUTING SUPERVISOR WORKFLOW v7.0 (PURE MCP + STREAMING)")
    logger.info("="*60)
    logger.info(f"Query: {user_query}")
    logger.info(f"Workspace: {workspace_path}")
    logger.info("⚠️ MCP BLEIBT: All agents execute via MCP protocol!")

    # ⚠️ MCP BLEIBT: Initialize MCPManager with progress callback
    from backend.utils.event_stream import get_event_manager
    event_manager = get_event_manager()

    def progress_callback(server: str, message: str, progress: float):
        """
        ⚠️ MCP BLEIBT: Forward MCP $/progress notifications to event stream

        Note: This is a sync callback called from MCPManager.
        We use asyncio.create_task to send events asynchronously.
        """
        try:
            # Create async task to send event (don't await - we're in sync context)
            asyncio.create_task(event_manager._send_event(session_id, {
                "type": "mcp_progress",
                "server": server,
                "message": message,
                "progress": progress,
                "timestamp": datetime.now().isoformat()
            }))
            logger.debug(f"📊 MCP Progress ({server}): {message}")
        except Exception as e:
            logger.warning(f"Progress callback error: {e}")

    # ⚠️ MCP BLEIBT: Get or create MCPManager with callback
    mcp = get_mcp_manager(
        workspace_path=workspace_path,
        progress_callback=progress_callback
    )

    # Initialize MCP connections
    try:
        logger.info("📡 Initializing MCP connections...")
        await mcp.initialize()
        logger.info("✅ All MCP servers connected")
    except Exception as e:
        logger.error(f"❌ MCP initialization failed: {e}")
        yield {
            "type": "error",
            "error": f"MCP initialization failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        return

    # Build workflow
    app = build_supervisor_workflow_mcp()

    # Initialize state
    initial_state = {
        "messages": [{"role": "user", "content": user_query}],
        "goal": user_query,
        "user_query": user_query,
        "workspace_path": workspace_path,
        "session_id": session_id,
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
        "error_count": 0,
        "errors": [],
        "confidence": 1.0,
        "requires_clarification": False,
        "hitl_response": None,
        "awaiting_human": False
    }

    # Configure recursion limit
    config = RunnableConfig(recursion_limit=150)
    logger.info(f"   📊 Recursion limit set to: 150")

    # Execute workflow with streaming
    try:
        logger.info("\n📊 Starting workflow execution with streaming...")

        # Subscribe to event stream for this session
        event_queue = event_manager.subscribe(session_id)

        # Create task to stream workflow events
        async def stream_workflow_events():
            """Stream LangGraph workflow events + MCP progress."""
            async for event in app.astream(initial_state, config=config, stream_mode="updates"):
                # Each event is {node_name: state_update}
                for node_name, state_update in event.items():
                    # Send event to client
                    await event_queue.put({
                        "type": "workflow_event",
                        "node": node_name,
                        "state_update": state_update,
                        "timestamp": datetime.now().isoformat(),
                        "architecture": "pure_mcp"  # ⚠️ MCP BLEIBT!
                    })

                    # Log progress
                    logger.info(f"\n   📥 Event from: {node_name}")
                    if isinstance(state_update, dict) and "last_agent" in state_update:
                        logger.info(f"      Agent: {state_update['last_agent']}")
                        logger.info(f"      ⚠️ MCP BLEIBT: Executed via mcp.call()")

            # Send completion event
            await event_queue.put({
                "type": "workflow_complete",
                "message": "✅ Workflow completed successfully (Pure MCP)",
                "timestamp": datetime.now().isoformat()
            })

        # Start workflow streaming in background
        workflow_task = asyncio.create_task(stream_workflow_events())

        # Yield events from queue (includes workflow + MCP progress events)
        try:
            while True:
                event = await event_queue.get()
                yield event

                # Break on completion/error
                if event.get("type") in ("workflow_complete", "error"):
                    break
        finally:
            # Clean up
            workflow_task.cancel()
            event_manager.unsubscribe(session_id)

        logger.info("\n✅ Workflow execution complete (Pure MCP)!")

    except Exception as e:
        logger.error(f"❌ Workflow execution failed: {e}", exc_info=True)
        yield {
            "type": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    finally:
        # Close MCP connections
        logger.info("🔌 Closing MCP connections...")
        await mcp.close()
        logger.info("✅ MCP connections closed")


async def execute_supervisor_workflow_mcp(
    user_query: str,
    workspace_path: str
) -> dict[str, Any]:
    """
    ⚠️ MCP BLEIBT: Execute the Pure MCP supervisor workflow

    This is the main entry point for v7.0 MCP workflows.

    Args:
        user_query: The user's request
        workspace_path: Path to the workspace

    Returns:
        Final workflow state with results
    """
    logger.info("="*60)
    logger.info("🚀 EXECUTING SUPERVISOR WORKFLOW v7.0 (PURE MCP)")
    logger.info("="*60)
    logger.info(f"Query: {user_query}")
    logger.info(f"Workspace: {workspace_path}")
    logger.info("⚠️ MCP BLEIBT: All agents execute via MCP protocol!")

    # ⚠️ MCP BLEIBT: Initialize MCPManager
    mcp = get_mcp_manager(workspace_path=workspace_path)

    try:
        logger.info("📡 Initializing MCP connections...")
        await mcp.initialize()
        logger.info("✅ All MCP servers connected")
    except Exception as e:
        logger.error(f"❌ MCP initialization failed: {e}")
        raise

    # Build workflow
    app = build_supervisor_workflow_mcp()

    # Initialize state
    initial_state = {
        "messages": [{"role": "user", "content": user_query}],
        "goal": user_query,
        "user_query": user_query,
        "workspace_path": workspace_path,
        "session_id": "non-streaming",
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

    # Configure recursion limit
    config = RunnableConfig(recursion_limit=150)
    logger.info(f"   📊 Recursion limit set to: 150")

    # Execute workflow
    try:
        logger.info("\n📊 Starting workflow execution...")

        # Track the final state by accumulating updates
        final_state = dict(initial_state)

        # Run with streaming for visibility
        async for output in app.astream(initial_state, config=config):
            # Log each step
            for node, state_update in output.items():
                logger.info(f"\n   Step: {node}")
                if isinstance(state_update, dict):
                    # Update final state with changes
                    final_state.update(state_update)

                    if "last_agent" in state_update:
                        logger.info(f"   Last Agent: {state_update['last_agent']}")
                        logger.info(f"   ⚠️ MCP BLEIBT: Executed via mcp.call()")
                    if "instructions" in state_update:
                        logger.info(f"   Instructions: {state_update['instructions'][:100]}...")
                    if "response_ready" in state_update and state_update["response_ready"]:
                        logger.info(f"   ✅ Response ready from Responder MCP!")

        logger.info("\n✅ Workflow execution complete (Pure MCP)!")

        # Return final state with accumulated updates
        return final_state

    except Exception as e:
        logger.error(f"❌ Workflow execution failed: {e}", exc_info=True)
        raise
    finally:
        # Close MCP connections
        logger.info("🔌 Closing MCP connections...")
        await mcp.close()
        logger.info("✅ MCP connections closed")


# ============================================================================
# Export
# ============================================================================

__all__ = [
    "SupervisorState",
    "build_supervisor_workflow_mcp",
    "execute_supervisor_workflow_mcp",
    "execute_supervisor_workflow_streaming_mcp"
]
