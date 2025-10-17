"""
Dynamic Orchestrator - Intelligent Workflow Execution Engine

This module provides a dynamic orchestration layer that executes AI-generated
workflow plans with full flexibility, self-calling capabilities, and intelligent
decision making.

Key Features:
- Dynamic workflow execution based on AI plans
- Agent self-calling and inter-agent communication
- Budget and cost tracking
- Intelligent error recovery and adaptation
- Context-aware routing decisions

Architecture:
- Replaces fixed graph edges with dynamic execution
- Maintains execution state and history
- Enables agents to request other agents
- Tracks costs and enforces budgets

Author: KI AutoAgent Team
Version: 6.4.0-beta
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from cognitive.capability_registry import (
    AgentType,
    CapabilityRegistry,
    RiskLevel
)

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """Status of workflow execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    ABORTED = "aborted"


@dataclass()
class AgentExecution:
    """Record of a single agent execution."""

    agent: AgentType
    mode: str
    status: ExecutionStatus
    start_time: datetime | None = None
    end_time: datetime | None = None
    input: dict[str, Any] = field(default_factory=dict)
    output: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    cost: float = 0.0
    tokens_used: int = 0

    @property
    def duration(self) -> float:
        """Get execution duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


@dataclass()
class WorkflowExecution:
    """Complete workflow execution state."""

    plan: list[tuple[AgentType, str]]  # [(agent, mode), ...]
    executions: list[AgentExecution] = field(default_factory=list)
    current_index: int = 0
    total_cost: float = 0.0
    total_tokens: int = 0
    max_budget: float = 10.0  # $10 default budget
    workspace_path: str = ""
    user_query: str = ""

    @property
    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return self.current_index >= len(self.plan)

    @property
    def current_agent(self) -> tuple[AgentType, str] | None:
        """Get current agent to execute."""
        if self.is_complete:
            return None
        return self.plan[self.current_index]

    @property
    def remaining_budget(self) -> float:
        """Get remaining budget."""
        return max(0, self.max_budget - self.total_cost)


class DynamicOrchestrator:
    """
    Intelligent workflow orchestrator that dynamically executes AI-generated plans.

    This replaces fixed graph edges with dynamic, context-aware execution that:
    - Follows AI-generated plans
    - Allows agents to call other agents
    - Tracks costs and enforces budgets
    - Makes intelligent routing decisions
    """

    def __init__(
        self,
        workspace_path: str,
        agent_executors: dict[AgentType, Callable] | None = None,
        websocket_callback: Any | None = None,
        max_budget: float = 10.0
    ):
        """
        Initialize Dynamic Orchestrator.

        Args:
            workspace_path: Path to workspace
            agent_executors: Map of agent type to executor function
            websocket_callback: Optional WebSocket for progress updates
            max_budget: Maximum budget in USD
        """
        self.workspace_path = workspace_path
        self.agent_executors = agent_executors or {}
        self.websocket_callback = websocket_callback
        self.max_budget = max_budget

        # Execution tracking
        self.current_execution: WorkflowExecution | None = None
        self.execution_history: list[WorkflowExecution] = []

        # Self-calling requests from agents
        self.pending_agent_requests: list[tuple[AgentType, str, dict]] = []

        # Capability registry for intelligent decisions
        self.capabilities = CapabilityRegistry()

        logger.info(f"🎯 Dynamic Orchestrator initialized for {workspace_path}")
        logger.info(f"   Max budget: ${max_budget:.2f}")

    # ========================================================================
    # WORKFLOW EXECUTION
    # ========================================================================

    async def execute_workflow(
        self,
        workflow_path: list[str],
        agent_modes: dict[str, str],
        user_query: str,
        initial_state: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute a complete workflow dynamically.

        This is the main entry point that replaces fixed graph traversal.

        Args:
            workflow_path: List of agent names in order
            agent_modes: Map of agent to mode
            user_query: Original user query
            initial_state: Initial state dict

        Returns:
            Final state after all agents execute
        """
        logger.info(f"🚀 Starting dynamic workflow execution")
        logger.info(f"   Plan: {' → '.join(workflow_path)}")

        # Create execution plan
        plan = []
        for agent_name in workflow_path:
            try:
                agent_type = AgentType(agent_name)
                mode = agent_modes.get(agent_name, "default")
                plan.append((agent_type, mode))
            except ValueError:
                logger.error(f"Unknown agent type: {agent_name}")
                continue

        # Initialize execution tracking
        self.current_execution = WorkflowExecution(
            plan=plan,
            workspace_path=self.workspace_path,
            user_query=user_query,
            max_budget=self.max_budget
        )

        # Execute plan
        state = initial_state.copy()

        while not self.current_execution.is_complete:
            # Check budget
            if self.current_execution.remaining_budget <= 0:
                logger.error("💸 Budget exhausted! Aborting workflow")
                state["errors"] = state.get("errors", []) + ["Budget exhausted"]
                break

            # Get next agent
            agent_type, mode = self.current_execution.current_agent

            logger.info(f"")
            logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            logger.info(f"🤖 Executing: {agent_type.value} (mode={mode})")
            logger.info(f"   Step {self.current_execution.current_index + 1}/{len(plan)}")
            logger.info(f"   Budget remaining: ${self.current_execution.remaining_budget:.2f}")
            logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

            # Execute agent
            agent_state = await self._execute_agent(
                agent_type=agent_type,
                mode=mode,
                state=state
            )

            # Update state
            state.update(agent_state)

            # Check for agent self-call requests
            if self.pending_agent_requests:
                await self._handle_agent_requests(state)

            # Move to next agent
            self.current_execution.current_index += 1

            # Check for early termination conditions
            if self._should_terminate_early(state):
                logger.warning("⚠️ Early termination triggered")
                break

        # Finalize execution
        logger.info(f"")
        logger.info(f"═══════════════════════════════════════")
        logger.info(f"✅ Workflow execution complete!")
        logger.info(f"   Total cost: ${self.current_execution.total_cost:.2f}")
        logger.info(f"   Total tokens: {self.current_execution.total_tokens:,}")
        logger.info(f"   Agents executed: {len(self.current_execution.executions)}")
        logger.info(f"═══════════════════════════════════════")

        # Store in history
        self.execution_history.append(self.current_execution)

        return state

    # ========================================================================
    # AGENT EXECUTION
    # ========================================================================

    async def _execute_agent(
        self,
        agent_type: AgentType,
        mode: str,
        state: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute a single agent with tracking.

        Args:
            agent_type: Type of agent
            mode: Execution mode
            state: Current state

        Returns:
            Updated state from agent
        """
        # Create execution record
        execution = AgentExecution(
            agent=agent_type,
            mode=mode,
            status=ExecutionStatus.RUNNING,
            start_time=datetime.now(),
            input={"workspace_path": self.workspace_path, "mode": mode}
        )

        try:
            # Estimate cost
            estimated_cost = self.capabilities.estimate_cost(agent_type, mode)
            estimated_latency = self.capabilities.estimate_latency(agent_type, mode)

            logger.info(f"   Estimated cost: ${estimated_cost:.2f}")
            logger.info(f"   Estimated time: {estimated_latency:.1f}s")

            # Check if approval needed
            if self.capabilities.requires_approval(agent_type, mode):
                logger.info(f"🔐 Requesting approval for {agent_type.value}:{mode}")
                if not await self._request_approval(agent_type, mode):
                    logger.warning("❌ Approval denied, skipping agent")
                    execution.status = ExecutionStatus.SKIPPED
                    return state

            # Get executor
            executor = self.agent_executors.get(agent_type)
            if not executor:
                logger.error(f"No executor for {agent_type}")
                execution.status = ExecutionStatus.FAILED
                execution.errors.append(f"No executor for {agent_type}")
                return state

            # Inject mode into state for the agent
            state["agent_mode"] = mode

            # Execute agent
            result = await executor(state)

            # Track execution
            execution.end_time = datetime.now()
            execution.status = ExecutionStatus.SUCCESS
            execution.output = result
            execution.cost = estimated_cost  # TODO: Get actual cost from agent
            execution.tokens_used = 0  # TODO: Get actual tokens from agent

            # Update totals
            self.current_execution.total_cost += execution.cost
            self.current_execution.total_tokens += execution.tokens_used
            self.current_execution.executions.append(execution)

            logger.info(f"   ✅ Agent completed in {execution.duration:.1f}s")

            return result

        except Exception as e:
            logger.error(f"   ❌ Agent failed: {e}")
            execution.end_time = datetime.now()
            execution.status = ExecutionStatus.FAILED
            execution.errors.append(str(e))
            self.current_execution.executions.append(execution)

            # Add error to state
            state["errors"] = state.get("errors", []) + [f"{agent_type}: {e}"]
            return state

    # ========================================================================
    # AGENT SELF-CALLING
    # ========================================================================

    def request_agent(
        self,
        requesting_agent: AgentType,
        target_agent: AgentType,
        mode: str,
        reason: str,
        inputs: dict[str, Any] | None = None
    ):
        """
        Allow an agent to request another agent.

        This enables dynamic agent-to-agent communication.

        Args:
            requesting_agent: Agent making the request
            target_agent: Agent being requested
            mode: Mode for target agent
            reason: Why this agent is needed
            inputs: Optional inputs for target
        """
        logger.info(f"🔄 Agent request: {requesting_agent} → {target_agent}:{mode}")
        logger.info(f"   Reason: {reason}")

        self.pending_agent_requests.append((target_agent, mode, inputs or {}))

    async def _handle_agent_requests(self, state: dict[str, Any]):
        """
        Handle pending agent self-call requests.

        Args:
            state: Current state
        """
        while self.pending_agent_requests:
            agent_type, mode, inputs = self.pending_agent_requests.pop(0)

            logger.info(f"🔄 Processing agent request: {agent_type}:{mode}")

            # Check if we have budget
            if self.current_execution.remaining_budget <= 0:
                logger.warning("💸 Cannot fulfill agent request - budget exhausted")
                break

            # Execute requested agent
            request_state = {**state, **inputs}
            result = await self._execute_agent(agent_type, mode, request_state)

            # Merge results back into main state
            state.update(result)

    # ========================================================================
    # INTELLIGENT DECISIONS
    # ========================================================================

    def _should_terminate_early(self, state: dict[str, Any]) -> bool:
        """
        Determine if workflow should terminate early.

        Args:
            state: Current state

        Returns:
            True if should terminate
        """
        errors = state.get("errors", [])

        # Too many errors
        if len(errors) >= 3:
            logger.error(f"🛑 Too many errors ({len(errors)}), terminating")
            return True

        # Critical failure detected
        for error in errors:
            if "critical" in str(error).lower():
                logger.error(f"🛑 Critical error detected, terminating")
                return True

        # User requested abort
        if state.get("user_abort"):
            logger.warning("🛑 User requested abort")
            return True

        return False

    async def _request_approval(
        self,
        agent_type: AgentType,
        mode: str
    ) -> bool:
        """
        Request approval for critical actions.

        Args:
            agent_type: Agent requiring approval
            mode: Mode requiring approval

        Returns:
            True if approved
        """
        if not self.websocket_callback:
            logger.warning("No approval mechanism, auto-approving")
            return True

        # Send approval request via WebSocket
        await self.websocket_callback({
            "type": "approval_request",
            "agent": agent_type.value,
            "mode": mode,
            "description": f"{agent_type.value} wants to {mode}",
            "risk_level": RiskLevel.WRITES_FILES.value
        })

        # TODO: Wait for approval response
        # For now, auto-approve after delay
        await asyncio.sleep(0.1)
        return True

    # ========================================================================
    # BUDGET MANAGEMENT
    # ========================================================================

    def get_budget_report(self) -> dict[str, Any]:
        """
        Get detailed budget report.

        Returns:
            Budget usage details
        """
        if not self.current_execution:
            return {"message": "No active execution"}

        return {
            "total_budget": self.current_execution.max_budget,
            "spent": self.current_execution.total_cost,
            "remaining": self.current_execution.remaining_budget,
            "tokens_used": self.current_execution.total_tokens,
            "agents_executed": len(self.current_execution.executions),
            "cost_breakdown": [
                {
                    "agent": exec.agent.value,
                    "mode": exec.mode,
                    "cost": exec.cost,
                    "duration": exec.duration
                }
                for exec in self.current_execution.executions
            ]
        }

    def set_budget(self, budget: float):
        """
        Update maximum budget.

        Args:
            budget: New budget in USD
        """
        self.max_budget = budget
        if self.current_execution:
            self.current_execution.max_budget = budget
        logger.info(f"💰 Budget updated to ${budget:.2f}")

    # ========================================================================
    # EXECUTION HISTORY
    # ========================================================================

    def get_execution_history(self) -> list[dict[str, Any]]:
        """
        Get execution history.

        Returns:
            List of past executions
        """
        return [
            {
                "user_query": exec.user_query,
                "total_cost": exec.total_cost,
                "total_tokens": exec.total_tokens,
                "agents_executed": len(exec.executions),
                "success": all(e.status == ExecutionStatus.SUCCESS for e in exec.executions)
            }
            for exec in self.execution_history
        ]