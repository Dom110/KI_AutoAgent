"""
Extended Agent State for LangGraph
Defines the complete state structure for agent communication
"""

import operator
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Any, Literal, TypedDict


@dataclass
class ToolDefinition:
    """Tool definition for discovery"""

    name: str
    description: str
    parameters: dict[str, Any]
    callable: Any
    agent_owner: str
    version: str = "1.0.0"
    tags: list[str] = None


@dataclass
class MemoryEntry:
    """Memory entry for agent recall"""

    content: str
    memory_type: Literal["episodic", "semantic", "procedural", "entity"]
    timestamp: datetime
    importance: float
    metadata: dict[str, Any]
    session_id: str


def merge_execution_steps(
    existing: list["ExecutionStep"], updates: list["ExecutionStep"]
) -> list["ExecutionStep"]:
    """
    Custom reducer for execution_plan state updates

    v5.8.3: LangGraph Best Practice - State Immutability
    This reducer merges step updates by ID instead of mutating dataclasses.
    Fixes the "architect stuck in_progress" bug by ensuring checkpointer
    correctly saves state changes.

    How it works:
    - If step.id exists in existing: Replace entire step with updated version
    - If step.id is new: Append to plan
    - Preserves order of existing steps

    Args:
        existing: Current execution_plan from state
        updates: New/modified steps returned from node

    Returns:
        Merged list with updated steps

    Example:
        # Node returns partial update:
        return {"execution_plan": [dataclass_replace(step, status="completed")]}
        # Reducer merges: existing steps + this updated step
    """
    if not existing:
        return updates

    # Create lookup dict for fast ID-based updates
    steps_dict = {step.id: step for step in existing}

    # Merge updates (replace if exists, add if new)
    for update_step in updates:
        steps_dict[update_step.id] = update_step

    # Preserve original order, append new steps at end
    result = []
    seen_ids = set()

    # First: Keep existing order
    for step in existing:
        if step.id in steps_dict:
            result.append(steps_dict[step.id])
            seen_ids.add(step.id)

    # Then: Append new steps
    for update_step in updates:
        if update_step.id not in seen_ids:
            result.append(update_step)

    return result


@dataclass
class ExecutionStep:
    """
    Single execution step in the plan
    v5.4.3: Enhanced with timeout, retry, and parallel execution support
    """

    id: str
    agent: str
    task: str
    expected_output: str = ""  # Default to empty string for checkpoint deserialization
    dependencies: list[str] = None  # Default to empty list
    status: Literal[
        "pending",
        "in_progress",
        "completed",
        "failed",
        "blocked",
        "cancelled",
        "timeout",
    ] = "pending"
    result: Any | None = None
    error: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None

    # v5.4.3: Timeout Management
    timeout_seconds: int = 300  # 5 minutes default
    started_at: datetime | None = None  # Track actual execution start

    # v5.4.3: Retry Mechanism
    retry_count: int = 0
    max_retries: int = 3
    retry_delay_seconds: int = 5  # Exponential backoff base

    # v5.4.3: Parallel Execution Support
    can_run_parallel: bool = False
    parallel_group: str | None = None  # Group ID for parallel execution

    # v5.4.3: Enhanced Tracking
    attempts: list[dict[str, Any]] = None  # History of execution attempts
    completion_percentage: float = 0.0  # Progress tracking

    def __post_init__(self):
        """Initialize mutable defaults"""
        if self.dependencies is None:
            self.dependencies = []
        if self.attempts is None:
            self.attempts = []

    def is_timeout(self) -> bool:
        """Check if step has timed out"""
        if self.started_at and self.status == "in_progress":
            elapsed = (datetime.now() - self.started_at).total_seconds()
            return elapsed > self.timeout_seconds
        return False

    def can_retry(self) -> bool:
        """Check if step can be retried"""
        return self.retry_count < self.max_retries and self.status in [
            "failed",
            "timeout",
        ]

    def get_retry_delay(self) -> int:
        """Calculate exponential backoff delay"""
        return self.retry_delay_seconds * (2**self.retry_count)


@dataclass
class TaskLedger:
    """
    v5.4.3: Task Ledger for Orchestrator Planning
    Tracks original task, decomposed steps, and completion criteria
    """

    original_task: str
    decomposed_steps: list[ExecutionStep]
    completion_criteria: list[str]
    progress_summary: str
    created_at: datetime
    last_updated: datetime
    total_estimated_duration: int = 0  # seconds
    actual_duration: int = 0  # seconds
    success_metrics: dict[str, Any] = None

    def __post_init__(self):
        """Initialize defaults"""
        if self.success_metrics is None:
            self.success_metrics = {}


@dataclass
class ProgressLedger:
    """
    v5.4.3: Progress tracking for workflow execution
    Provides real-time visibility into workflow progress
    """

    total_steps: int
    completed_steps: int
    failed_steps: int
    in_progress_steps: int
    blocked_steps: int
    current_phase: str  # e.g., "planning", "execution", "validation"
    estimated_completion: datetime | None
    overall_progress_percentage: float
    bottlenecks: list[str] = None  # Identified bottlenecks
    performance_metrics: dict[str, float] = None

    def __post_init__(self):
        """Initialize defaults"""
        if self.bottlenecks is None:
            self.bottlenecks = []
        if self.performance_metrics is None:
            self.performance_metrics = {}

    def update_from_steps(self, steps: list[ExecutionStep]):
        """Update progress from execution steps"""
        self.total_steps = len(steps)
        self.completed_steps = sum(1 for s in steps if s.status == "completed")
        self.failed_steps = sum(1 for s in steps if s.status == "failed")
        self.in_progress_steps = sum(1 for s in steps if s.status == "in_progress")
        self.blocked_steps = sum(1 for s in steps if s.status == "blocked")

        if self.total_steps > 0:
            self.overall_progress_percentage = (
                self.completed_steps / self.total_steps
            ) * 100


class ExtendedAgentState(TypedDict):
    """
    Complete state for LangGraph agent workflow
    Includes all features: memory, tools, approval, etc.
    """

    # Core conversation state (using Annotated with operator.add to handle concurrent updates)
    messages: Annotated[list[dict[str, Any]], operator.add]
    current_agent: str
    current_task: str

    # Session management
    session_id: str
    client_id: str
    workspace_path: str

    # Execution plan and tracking
    # v5.8.3: Using Annotated with custom reducer for state immutability
    # This ensures LangGraph checkpointer correctly persists step status changes
    execution_plan: Annotated[list[ExecutionStep], merge_execution_steps]
    current_step_id: str | None
    execution_mode: Literal["sequential", "parallel"]

    # v5.4.3: Task and Progress Ledgers
    task_ledger: TaskLedger | None
    progress_ledger: ProgressLedger | None

    # Plan-First and approval
    plan_first_mode: bool
    approval_status: Literal["pending", "approved", "rejected", "modified", None]
    approval_feedback: str | None
    waiting_for_approval: bool

    # Tool discovery and results
    available_tools: list[ToolDefinition]
    tool_calls: list[dict[str, Any]]
    tool_results: list[Any]

    # Memory system
    short_term_memory: dict[str, Any]
    recalled_memories: list[MemoryEntry]
    learned_patterns: list[dict[str, Any]]
    memory_query: str | None

    # Agent collaboration
    agent_communications: list[dict[str, Any]]
    shared_context: dict[str, Any]
    agent_states: dict[str, dict[str, Any]]  # Individual agent states

    # v5.1.0: Information-First Escalation System
    collaboration_count: int  # Total collaborations in this workflow
    reviewer_fixer_cycles: int  # Specific Reviewer↔Fixer cycles
    last_collaboration_agents: list[
        str
    ]  # Track pattern [reviewer, fixer, reviewer, fixer]
    escalation_level: int  # 0=normal, 1=retry, 2=broad research, 3=targeted, 4=alternative approach, 4.5=alt fixer, 5=user, 6=opus, 7=human
    collaboration_history: list[dict[str, Any]]  # Detailed history with timestamps
    information_gathered: list[dict[str, Any]]  # Research results
    needs_replan: bool  # Agent requests collaboration/re-planning
    suggested_agent: str | None  # Agent to collaborate with
    suggested_query: str | None  # Query for suggested agent

    # v5.8.6 Fix 5: Review-Fix Iteration Tracking
    review_iteration: int  # Current review-fix iteration count (0-based)
    max_review_iterations: int  # Maximum iterations allowed (default: 3)
    last_quality_score: float  # Last quality score from Reviewer (0-1)
    quality_threshold: float  # Minimum quality to accept (default: 0.8)

    # v5.2.0: Architecture Proposal System
    architecture_proposal: dict[
        str, Any
    ] | None  # Draft proposal from Architect (summary, improvements, tech_stack, structure, risks, research_insights)
    proposal_status: Literal[
        "none", "pending", "approved", "rejected", "modified"
    ]  # Proposal workflow status
    user_feedback_on_proposal: str | None  # User's comments/changes on proposal
    needs_approval: bool  # Generic approval flag (replaces waiting_for_approval)
    approval_type: Literal[
        "none", "execution_plan", "architecture_proposal"
    ]  # Type of approval needed

    # v5.5.2: Safe Orchestrator Execution
    safe_execution_enabled: bool  # Whether safe execution is active
    query_classification: dict[
        str, Any
    ] | None  # Classification results for current query
    execution_depth: int  # Current depth in orchestrator execution chain
    execution_history: list[dict[str, Any]]  # History of safe execution attempts
    blocked_queries: list[str]  # Queries that were blocked for safety
    safety_score: float  # Current safety score (0-1)

    # Error handling and debugging
    errors: list[dict[str, Any]]
    debug_mode: bool
    trace_log: list[str]

    # Performance metrics
    start_time: datetime
    end_time: datetime | None
    token_usage: dict[str, int]
    cost: float

    # Dynamic workflow modifications
    workflow_modifications: list[dict[str, Any]]
    custom_nodes: dict[str, Any]
    conditional_rules: list[dict[str, Any]]

    # Final results
    final_result: Any | None
    status: Literal[
        "initializing",
        "planning",
        "awaiting_approval",
        "waiting_architecture_approval",
        "executing",
        "completed",
        "failed",
    ]


def create_initial_state(
    session_id: str | None = None,
    client_id: str | None = None,
    workspace_path: str | None = None,
    plan_first_mode: bool = False,
    debug_mode: bool = False,
) -> ExtendedAgentState:
    """
    Create initial state for a new workflow
    """
    import os

    return ExtendedAgentState(
        # Core
        messages=[],
        current_agent="orchestrator",
        current_task="",
        # Session
        session_id=session_id or str(uuid.uuid4()),
        client_id=client_id or "",
        workspace_path=workspace_path or os.getcwd(),
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
        # v5.8.6 Fix 5: Review-Fix Iteration Tracking
        review_iteration=0,
        max_review_iterations=3,
        last_quality_score=0.0,
        quality_threshold=0.8,
        # v5.2.0: Architecture Proposal System
        architecture_proposal=None,
        proposal_status="none",
        user_feedback_on_proposal=None,
        needs_approval=False,
        approval_type="none",
        # v5.5.2: Safe Orchestrator Execution
        safe_execution_enabled=True,  # Enabled by default
        query_classification=None,
        execution_depth=0,
        execution_history=[],
        blocked_queries=[],
        safety_score=1.0,  # Start with perfect safety
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
        status="initializing",
    )


# v5.5.2: Alias for compatibility
WorkflowState = ExtendedAgentState
