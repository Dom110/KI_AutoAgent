"""
Main workflow creation for KI AutoAgent using LangGraph
Integrates all agents with extended features
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from .state import ExtendedAgentState, create_initial_state, ExecutionStep
from .extensions import (
    ToolRegistry,
    ApprovalManager,
    PersistentAgentMemory,
    DynamicWorkflowManager,
    get_tool_registry
)

logger = logging.getLogger(__name__)


class AgentWorkflow:
    """
    Main workflow orchestrator for the KI AutoAgent system
    """

    def __init__(
        self,
        websocket_manager=None,
        db_path: str = "langgraph_state.db",
        memory_db_path: str = "agent_memories.db"
    ):
        """
        Initialize the agent workflow system

        Args:
            websocket_manager: WebSocket manager for UI communication
            db_path: Path for LangGraph checkpointer database
            memory_db_path: Path for agent memory database
        """
        self.websocket_manager = websocket_manager
        self.db_path = db_path
        self.memory_db_path = memory_db_path

        # Initialize extensions
        self.tool_registry = get_tool_registry()
        self.approval_manager = ApprovalManager(websocket_manager)
        self.dynamic_manager = DynamicWorkflowManager()

        # Initialize memory for each agent
        self.agent_memories = {}
        self._init_agent_memories()

        # Initialize workflow
        self.workflow = None
        self.checkpointer = None

    def _init_agent_memories(self):
        """Initialize persistent memory for each agent"""
        agents = [
            "orchestrator",
            "architect",
            "codesmith",
            "reviewer",
            "fixer",
            "docbot",
            "research",
            "tradestrat",
            "opus_arbitrator",
            "performance"
        ]

        for agent in agents:
            self.agent_memories[agent] = PersistentAgentMemory(
                agent_name=agent,
                db_path=self.memory_db_path
            )

    async def orchestrator_node(self, state: ExtendedAgentState) -> ExtendedAgentState:
        """
        Orchestrator node - plans and decomposes tasks
        """
        logger.info("🎯 Orchestrator node executing")
        state["current_agent"] = "orchestrator"
        state["status"] = "planning"

        # Recall similar past tasks
        memory = self.agent_memories["orchestrator"]
        if state["messages"]:
            last_message = state["messages"][-1]["content"]
            similar_memories = memory.recall_similar(last_message, k=3)
            state["recalled_memories"] = similar_memories

            # Check for learned patterns
            learned = memory.get_learned_solution(last_message)
            if learned:
                logger.info("📚 Found learned solution from past experience")
                state["learned_patterns"].append({
                    "pattern": last_message,
                    "solution": learned
                })

        # Create execution plan
        plan = await self._create_execution_plan(state)
        state["execution_plan"] = plan

        # Check if Plan-First mode
        if state.get("plan_first_mode"):
            state["status"] = "awaiting_approval"
            state["waiting_for_approval"] = True
        else:
            state["status"] = "executing"

        # Store this planning in memory
        memory.store_memory(
            content=f"Created plan for: {last_message}",
            memory_type="episodic",
            importance=0.7,
            metadata={"plan_size": len(plan)},
            session_id=state.get("session_id")
        )

        return state

    async def approval_node(self, state: ExtendedAgentState) -> ExtendedAgentState:
        """
        Approval node for Plan-First mode
        """
        logger.info("✅ Approval node executing")

        if not state.get("plan_first_mode"):
            # Auto-approve if not in Plan-First mode
            state["approval_status"] = "approved"
            state["waiting_for_approval"] = False
            return state

        # Request approval from user
        request = await self.approval_manager.request_approval(
            client_id=state["client_id"],
            plan=state["execution_plan"],
            metadata={
                "task": state["current_task"],
                "agent_count": len(set(step.agent for step in state["execution_plan"]))
            }
        )

        state["approval_status"] = request.status
        state["approval_feedback"] = request.feedback
        state["waiting_for_approval"] = False

        if request.status == "modified" and request.modifications:
            # Apply modifications to plan
            state["execution_plan"] = self._apply_plan_modifications(
                state["execution_plan"],
                request.modifications
            )

        return state

    async def architect_node(self, state: ExtendedAgentState) -> ExtendedAgentState:
        """
        Architect agent node - system design and architecture
        """
        logger.info("🏗️ Architect node executing")
        state["current_agent"] = "architect"

        # Get memory and tools
        memory = self.agent_memories["architect"]
        tools = self.tool_registry.discover_tools_for_agent("architect")
        state["available_tools"] = tools

        # Find current task
        current_step = self._get_current_step(state)
        if not current_step:
            return state

        # Recall relevant memories
        similar = memory.recall_similar(current_step.task, k=5, memory_types=["semantic", "procedural"])
        state["recalled_memories"].extend(similar)

        # Execute architecture task
        try:
            # This would call the actual architect agent
            result = await self._execute_architect_task(state, current_step)
            current_step.result = result
            current_step.status = "completed"

            # Store successful result in memory
            memory.store_memory(
                content=f"Architecture design: {current_step.task}",
                memory_type="procedural",
                importance=0.8,
                metadata={"result": result},
                session_id=state.get("session_id")
            )

            # Learn from this execution
            memory.learn_pattern(
                pattern=current_step.task,
                solution=result,
                success=True
            )

        except Exception as e:
            logger.error(f"Architect execution failed: {e}")
            current_step.status = "failed"
            current_step.error = str(e)
            state["errors"].append({
                "agent": "architect",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

        return state

    async def codesmith_node(self, state: ExtendedAgentState) -> ExtendedAgentState:
        """
        CodeSmith agent node - code generation and implementation
        """
        logger.info("💻 CodeSmith node executing")
        state["current_agent"] = "codesmith"

        memory = self.agent_memories["codesmith"]
        tools = self.tool_registry.discover_tools_for_agent("codesmith")
        state["available_tools"] = tools

        current_step = self._get_current_step(state)
        if not current_step:
            return state

        # Check for code patterns
        patterns = memory.recall_similar(
            current_step.task,
            k=5,
            memory_types=["procedural"]
        )

        try:
            # Execute code generation
            result = await self._execute_codesmith_task(state, current_step, patterns)
            current_step.result = result
            current_step.status = "completed"

            # Store code pattern
            memory.store_memory(
                content=f"Generated code for: {current_step.task}",
                memory_type="procedural",
                importance=0.7,
                metadata={"code_size": len(str(result))},
                session_id=state.get("session_id")
            )

        except Exception as e:
            logger.error(f"CodeSmith execution failed: {e}")
            current_step.status = "failed"
            current_step.error = str(e)

        return state

    async def reviewer_node(self, state: ExtendedAgentState) -> ExtendedAgentState:
        """
        Reviewer agent node - code review and validation
        """
        logger.info("🔎 Reviewer node executing")
        state["current_agent"] = "reviewer"

        memory = self.agent_memories["reviewer"]
        current_step = self._get_current_step(state)

        if not current_step:
            return state

        try:
            # Perform review
            review_result = await self._execute_reviewer_task(state, current_step)
            current_step.result = review_result
            current_step.status = "completed"

            # Store review patterns
            if review_result.get("issues"):
                for issue in review_result["issues"]:
                    memory.store_memory(
                        content=f"Found issue: {issue}",
                        memory_type="semantic",
                        importance=0.6,
                        session_id=state.get("session_id")
                    )

        except Exception as e:
            logger.error(f"Reviewer execution failed: {e}")
            current_step.status = "failed"
            current_step.error = str(e)

        return state

    async def fixer_node(self, state: ExtendedAgentState) -> ExtendedAgentState:
        """
        Fixer agent node - bug fixing and optimization
        """
        logger.info("🔧 Fixer node executing")
        state["current_agent"] = "fixer"

        memory = self.agent_memories["fixer"]
        current_step = self._get_current_step(state)

        if not current_step:
            return state

        # Get previous review results
        review_step = self._get_step_by_agent(state, "reviewer")
        issues = review_step.result.get("issues", []) if review_step else []

        try:
            # Fix issues
            fix_result = await self._execute_fixer_task(state, current_step, issues)
            current_step.result = fix_result
            current_step.status = "completed"

            # Learn fix patterns
            for issue, fix in zip(issues, fix_result.get("fixes", [])):
                memory.learn_pattern(
                    pattern=issue,
                    solution=fix,
                    success=True
                )

        except Exception as e:
            logger.error(f"Fixer execution failed: {e}")
            current_step.status = "failed"
            current_step.error = str(e)

        return state

    def route_after_approval(self, state: ExtendedAgentState) -> str:
        """
        Route after approval node
        """
        status = state.get("approval_status")

        if status == "approved":
            return "execute"
        elif status == "modified":
            return "orchestrator"  # Re-plan with modifications
        else:
            return "end"

    def route_to_next_agent(self, state: ExtendedAgentState) -> str:
        """
        Determine next agent based on execution plan
        """
        # Find next pending step
        for step in state["execution_plan"]:
            if step.status == "pending":
                # Check dependencies
                if self._dependencies_met(step, state["execution_plan"]):
                    step.status = "in_progress"
                    state["current_step_id"] = step.id
                    return step.agent

        # All steps complete
        return "end"

    def _dependencies_met(self, step: ExecutionStep, all_steps: List[ExecutionStep]) -> bool:
        """Check if all dependencies for a step are met"""
        for dep_id in step.dependencies:
            dep_step = next((s for s in all_steps if s.id == dep_id), None)
            if not dep_step or dep_step.status != "completed":
                return False
        return True

    def _get_current_step(self, state: ExtendedAgentState) -> Optional[ExecutionStep]:
        """Get the current execution step"""
        step_id = state.get("current_step_id")
        if step_id:
            return next((s for s in state["execution_plan"] if s.id == step_id), None)
        return None

    def _get_step_by_agent(self, state: ExtendedAgentState, agent: str) -> Optional[ExecutionStep]:
        """Get the most recent step for an agent"""
        for step in reversed(state["execution_plan"]):
            if step.agent == agent and step.status == "completed":
                return step
        return None

    async def _create_execution_plan(self, state: ExtendedAgentState) -> List[ExecutionStep]:
        """Create execution plan based on task"""
        # This would use the orchestrator to create a plan
        # For now, return a simple plan
        return [
            ExecutionStep(
                id="step1",
                agent="architect",
                task="Design system architecture",
                expected_output="Architecture diagram and design docs",
                dependencies=[],
                status="pending"
            ),
            ExecutionStep(
                id="step2",
                agent="codesmith",
                task="Implement core functionality",
                expected_output="Working code implementation",
                dependencies=["step1"],
                status="pending"
            ),
            ExecutionStep(
                id="step3",
                agent="reviewer",
                task="Review implementation",
                expected_output="Review report with issues",
                dependencies=["step2"],
                status="pending"
            ),
            ExecutionStep(
                id="step4",
                agent="fixer",
                task="Fix identified issues",
                expected_output="Fixed code",
                dependencies=["step3"],
                status="pending"
            )
        ]

    def _apply_plan_modifications(
        self,
        plan: List[ExecutionStep],
        modifications: Dict[str, Any]
    ) -> List[ExecutionStep]:
        """Apply user modifications to execution plan"""
        # This would apply the modifications
        # For now, return the plan as-is
        return plan

    # Placeholder methods for actual agent execution
    async def _execute_architect_task(self, state: ExtendedAgentState, step: ExecutionStep) -> Any:
        """Execute architect task"""
        # This would call the actual architect agent
        await asyncio.sleep(1)  # Simulate work
        return {"design": "System architecture created"}

    async def _execute_codesmith_task(self, state: ExtendedAgentState, step: ExecutionStep, patterns: List) -> Any:
        """Execute codesmith task"""
        await asyncio.sleep(1)
        return {"code": "Implementation complete"}

    async def _execute_reviewer_task(self, state: ExtendedAgentState, step: ExecutionStep) -> Any:
        """Execute reviewer task"""
        await asyncio.sleep(1)
        return {"issues": ["Minor bug in line 42"]}

    async def _execute_fixer_task(self, state: ExtendedAgentState, step: ExecutionStep, issues: List) -> Any:
        """Execute fixer task"""
        await asyncio.sleep(1)
        return {"fixes": ["Bug fixed"]}

    def create_workflow(self) -> StateGraph:
        """
        Create the main LangGraph workflow
        """
        workflow = StateGraph(ExtendedAgentState)

        # Add nodes
        workflow.add_node("orchestrator", self.orchestrator_node)
        workflow.add_node("approval", self.approval_node)
        workflow.add_node("architect", self.architect_node)
        workflow.add_node("codesmith", self.codesmith_node)
        workflow.add_node("reviewer", self.reviewer_node)
        workflow.add_node("fixer", self.fixer_node)

        # Set entry point
        workflow.set_entry_point("orchestrator")

        # Add edges
        workflow.add_edge("orchestrator", "approval")

        # Conditional routing after approval
        workflow.add_conditional_edges(
            "approval",
            self.route_after_approval,
            {
                "execute": "architect",  # Start execution
                "orchestrator": "orchestrator",  # Re-plan
                "end": END
            }
        )

        # Dynamic routing based on execution plan
        for agent in ["architect", "codesmith", "reviewer", "fixer"]:
            workflow.add_conditional_edges(
                agent,
                self.route_to_next_agent,
                {
                    "architect": "architect",
                    "codesmith": "codesmith",
                    "reviewer": "reviewer",
                    "fixer": "fixer",
                    "end": END
                }
            )

        return workflow

    def compile_workflow(self):
        """
        Compile the workflow with checkpointing
        """
        workflow = self.create_workflow()

        # For now, compile without checkpointer to simplify testing
        # TODO: Fix checkpointer implementation
        self.workflow = workflow.compile()
        logger.info("✅ Workflow compiled")

        return self.workflow

    async def execute(
        self,
        task: str,
        session_id: Optional[str] = None,
        client_id: Optional[str] = None,
        workspace_path: Optional[str] = None,
        plan_first_mode: bool = False,
        config: Optional[Dict[str, Any]] = None
    ) -> ExtendedAgentState:
        """
        Execute the workflow for a task

        Args:
            task: Task description
            session_id: Session ID for continuity
            client_id: Client ID for WebSocket communication
            workspace_path: Workspace path
            plan_first_mode: Whether to use Plan-First mode
            config: Additional configuration

        Returns:
            Final state after execution
        """
        # Create initial state
        initial_state = create_initial_state(
            session_id=session_id,
            client_id=client_id,
            workspace_path=workspace_path,
            plan_first_mode=plan_first_mode,
            debug_mode=config.get("debug_mode", False) if config else False
        )

        # Add task to messages
        initial_state["messages"].append({
            "role": "user",
            "content": task,
            "timestamp": datetime.now().isoformat()
        })
        initial_state["current_task"] = task

        # Compile workflow if not done
        if not self.workflow:
            self.compile_workflow()

        # Execute workflow
        try:
            # Run the workflow
            final_state = await self.workflow.ainvoke(
                initial_state,
                config={"configurable": {"thread_id": session_id}}
            )

            final_state["status"] = "completed"
            final_state["end_time"] = datetime.now()

            logger.info(f"✅ Workflow completed for session {session_id}")
            return final_state

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            initial_state["status"] = "failed"
            initial_state["errors"].append({
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return initial_state


def create_agent_workflow(
    websocket_manager=None,
    db_path: str = "langgraph_state.db",
    memory_db_path: str = "agent_memories.db"
) -> AgentWorkflow:
    """
    Create and return configured agent workflow

    Args:
        websocket_manager: WebSocket manager for UI communication
        db_path: Path for LangGraph checkpointer database
        memory_db_path: Path for agent memory database

    Returns:
        Configured AgentWorkflow instance
    """
    workflow = AgentWorkflow(
        websocket_manager=websocket_manager,
        db_path=db_path,
        memory_db_path=memory_db_path
    )

    # Compile the workflow
    workflow.compile_workflow()

    return workflow