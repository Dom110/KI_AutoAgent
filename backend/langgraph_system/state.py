"""
Extended Agent State for LangGraph
Defines the complete state structure for agent communication
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal, Annotated
from dataclasses import dataclass
from datetime import datetime
import uuid
import operator


@dataclass
class ToolDefinition:
    """Tool definition for discovery"""
    name: str
    description: str
    parameters: Dict[str, Any]
    callable: Any
    agent_owner: str
    version: str = "1.0.0"
    tags: List[str] = None


@dataclass
class MemoryEntry:
    """Memory entry for agent recall"""
    content: str
    memory_type: Literal["episodic", "semantic", "procedural", "entity"]
    timestamp: datetime
    importance: float
    metadata: Dict[str, Any]
    session_id: str


@dataclass
class ExecutionStep:
    """Single execution step in the plan"""
    id: str
    agent: str
    task: str
    expected_output: str
    dependencies: List[str]
    status: Literal["pending", "in_progress", "completed", "failed"]
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class ExtendedAgentState(TypedDict):
    """
    Complete state for LangGraph agent workflow
    Includes all features: memory, tools, approval, etc.
    """

    # Core conversation state (using Annotated with operator.add to handle concurrent updates)
    messages: Annotated[List[Dict[str, Any]], operator.add]
    current_agent: str
    current_task: str

    # Session management
    session_id: str
    client_id: str
    workspace_path: str

    # Execution plan and tracking
    execution_plan: List[ExecutionStep]
    current_step_id: Optional[str]
    execution_mode: Literal["sequential", "parallel"]

    # Plan-First and approval
    plan_first_mode: bool
    approval_status: Literal["pending", "approved", "rejected", "modified", None]
    approval_feedback: Optional[str]
    waiting_for_approval: bool

    # Tool discovery and results
    available_tools: List[ToolDefinition]
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Any]

    # Memory system
    short_term_memory: Dict[str, Any]
    recalled_memories: List[MemoryEntry]
    learned_patterns: List[Dict[str, Any]]
    memory_query: Optional[str]

    # Agent collaboration
    agent_communications: List[Dict[str, Any]]
    shared_context: Dict[str, Any]
    agent_states: Dict[str, Dict[str, Any]]  # Individual agent states

    # v5.1.0: Information-First Escalation System
    collaboration_count: int  # Total collaborations in this workflow
    reviewer_fixer_cycles: int  # Specific Reviewer↔Fixer cycles
    last_collaboration_agents: List[str]  # Track pattern [reviewer, fixer, reviewer, fixer]
    escalation_level: int  # 0=normal, 1=retry, 2=broad research, 3=targeted, 4=alternative approach, 4.5=alt fixer, 5=user, 6=opus, 7=human
    collaboration_history: List[Dict[str, Any]]  # Detailed history with timestamps
    information_gathered: List[Dict[str, Any]]  # Research results
    needs_replan: bool  # Agent requests collaboration/re-planning
    suggested_agent: Optional[str]  # Agent to collaborate with
    suggested_query: Optional[str]  # Query for suggested agent

    # v5.2.0: Architecture Proposal System
    architecture_proposal: Optional[Dict[str, Any]]  # Draft proposal from Architect (summary, improvements, tech_stack, structure, risks, research_insights)
    proposal_status: Literal["none", "pending", "approved", "rejected", "modified"]  # Proposal workflow status
    user_feedback_on_proposal: Optional[str]  # User's comments/changes on proposal
    needs_approval: bool  # Generic approval flag (replaces waiting_for_approval)
    approval_type: Literal["none", "execution_plan", "architecture_proposal"]  # Type of approval needed

    # Error handling and debugging
    errors: List[Dict[str, Any]]
    debug_mode: bool
    trace_log: List[str]

    # Performance metrics
    start_time: datetime
    end_time: Optional[datetime]
    token_usage: Dict[str, int]
    cost: float

    # Dynamic workflow modifications
    workflow_modifications: List[Dict[str, Any]]
    custom_nodes: Dict[str, Any]
    conditional_rules: List[Dict[str, Any]]

    # Final results
    final_result: Optional[Any]
    status: Literal["initializing", "planning", "awaiting_approval", "waiting_architecture_approval", "executing", "completed", "failed"]


def create_initial_state(
    session_id: Optional[str] = None,
    client_id: Optional[str] = None,
    workspace_path: Optional[str] = None,
    plan_first_mode: bool = False,
    debug_mode: bool = False
) -> ExtendedAgentState:
    """
    Create initial state for a new workflow
    """
    return ExtendedAgentState(
        # Core
        messages=[],
        current_agent="orchestrator",
        current_task="",

        # Session
        session_id=session_id or str(uuid.uuid4()),
        client_id=client_id or "",
        workspace_path=workspace_path or "/",

        # Execution
        execution_plan=[],
        current_step_id=None,
        execution_mode="sequential",

        # Approval
        plan_first_mode=plan_first_mode,
        approval_status=None,
        approval_feedback=None,
        waiting_for_approval=False,

        # Tools
        available_tools=[],
        tool_calls=[],
        tool_results=[],

        # Memory
        short_term_memory={},
        recalled_memories=[],
        learned_patterns=[],
        memory_query=None,

        # Collaboration
        agent_communications=[],
        shared_context={},
        agent_states={},

        # v5.1.0: Information-First Escalation
        collaboration_count=0,
        reviewer_fixer_cycles=0,
        last_collaboration_agents=[],
        escalation_level=0,
        collaboration_history=[],
        information_gathered=[],
        needs_replan=False,
        suggested_agent=None,
        suggested_query=None,

        # v5.2.0: Architecture Proposal System
        architecture_proposal=None,
        proposal_status="none",
        user_feedback_on_proposal=None,
        needs_approval=False,
        approval_type="none",

        # Debugging
        errors=[],
        debug_mode=debug_mode,
        trace_log=[],

        # Metrics
        start_time=datetime.now(),
        end_time=None,
        token_usage={"input": 0, "output": 0},
        cost=0.0,

        # Dynamic
        workflow_modifications=[],
        custom_nodes={},
        conditional_rules=[],

        # Results
        final_result=None,
        status="initializing"
    )