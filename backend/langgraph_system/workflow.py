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
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)

# Import real agents
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REAL_AGENTS_AVAILABLE = False
try:
    from agents.specialized.architect_agent import ArchitectAgent
    from agents.specialized.codesmith_agent import CodeSmithAgent
    from agents.specialized.reviewer_gpt_agent import ReviewerGPTAgent
    from agents.specialized.fixerbot_agent import FixerBotAgent
    from agents.base.base_agent import TaskRequest, TaskResult
    REAL_AGENTS_AVAILABLE = True
    logger.info("✅ Real agents imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Could not import real agents: {e}")
    # This is OK - we'll use stubs


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

        # Initialize real agent instances
        self.real_agents = {}
        self._init_real_agents()

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

    def _init_real_agents(self):
        """Initialize real agent instances"""
        if not REAL_AGENTS_AVAILABLE:
            logger.warning("⚠️ Real agents not available - using stubs")
            return

        logger.info("🤖 Initializing real agent instances...")

        try:
            self.real_agents = {
                "architect": ArchitectAgent(),
                "codesmith": CodeSmithAgent(),
                "reviewer": ReviewerGPTAgent(),
                "fixer": FixerBotAgent()
            }
            logger.info(f"✅ Initialized {len(self.real_agents)} real agents")
        except Exception as e:
            logger.error(f"❌ Failed to initialize real agents: {e}")
            logger.exception(e)
            self.real_agents = {}

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

        # DON'T mark as completed here - let the agent nodes execute
        # We want the workflow to actually call the agent nodes
        # even for simple queries

        # Check if Plan-First mode
        if state.get("plan_first_mode"):
            state["status"] = "awaiting_approval"
            state["waiting_for_approval"] = True
        else:
            state["status"] = "executing"
            # Keep completed steps completed, mark others as pending
            for step in plan:
                if step.status != "failed" and step.status != "completed":
                    step.status = "pending"

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
            logger.info("📌 Auto-approving (not in Plan-First mode)")
            state["approval_status"] = "approved"
            state["waiting_for_approval"] = False

            # ✅ FIX: Set current_step_id to first pending step HERE (node can modify state)
            for step in state["execution_plan"]:
                if step.status == "pending" and self._dependencies_met(step, state["execution_plan"]):
                    step.status = "in_progress"
                    state["current_step_id"] = step.id
                    state["execution_plan"] = list(state["execution_plan"])  # Trigger state update
                    logger.info(f"📍 Set current_step_id to: {step.id} for agent: {step.agent}")
                    break

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
        logger.info(f"🔍 Architect: current_step_id={state.get('current_step_id')}, current_step={current_step}")
        if not current_step:
            logger.warning(f"⚠️ Architect: No current step found, returning early")
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

            # ✅ FIX: Create NEW list to trigger LangGraph state update
            state["execution_plan"] = list(state["execution_plan"])

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
            # ✅ FIX: Create NEW list even on failure
            state["execution_plan"] = list(state["execution_plan"])

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
        Route after approval node - intelligently routes to first pending agent
        Validates that the agent has a workflow node, fallback to orchestrator if not
        """
        # Available workflow nodes (agents with implemented nodes)
        AVAILABLE_NODES = {"orchestrator", "architect", "codesmith", "reviewer", "fixer"}

        status = state.get("approval_status")
        logger.info(f"🔀 Route after approval - Status: {status}")
        logger.info(f"📋 Execution plan has {len(state['execution_plan'])} steps:")
        for i, step in enumerate(state["execution_plan"]):
            logger.info(f"   Step {i+1}: agent={step.agent}, status={step.status}, task={step.task[:50]}...")

        if status == "approved":
            # Find first in_progress step (set by approval node) and route to that agent
            for step in state["execution_plan"]:
                if step.status == "in_progress":
                    agent = step.agent
                    # Validate agent has a workflow node
                    if agent not in AVAILABLE_NODES:
                        logger.warning(f"⚠️ Agent '{agent}' has no workflow node - marking as completed with stub")
                        step.status = "completed"
                        step.result = f"⚠️ Agent '{agent}' not yet implemented - stub response for: {step.task}"
                        state["execution_plan"] = list(state["execution_plan"])  # Trigger state update
                        return "end"  # Skip execution, go to end
                    logger.info(f"✅ Routing to in_progress agent: {agent} (step_id: {step.id})")
                    return agent

            # No in_progress steps - check for pending (fallback)
            for step in state["execution_plan"]:
                if step.status == "pending" and self._dependencies_met(step, state["execution_plan"]):
                    agent = step.agent
                    # Validate agent has a workflow node
                    if agent not in AVAILABLE_NODES:
                        logger.warning(f"⚠️ Agent '{agent}' has no workflow node - marking as completed with stub")
                        step.status = "completed"
                        step.result = f"⚠️ Agent '{agent}' not yet implemented - stub response for: {step.task}"
                        state["execution_plan"] = list(state["execution_plan"])  # Trigger state update
                        return "end"  # Skip execution, go to end
                    logger.info(f"✅ Routing to pending agent: {agent} (step_id: {step.id})")
                    return agent

            # No steps to execute - routing to END
            logger.info("🏁 All steps completed or no pending steps - routing to END")
            return "end"

        elif status == "modified":
            logger.info("🔄 Routing back to orchestrator for re-planning")
            return "orchestrator"  # Re-plan with modifications
        else:
            logger.info("🛑 Routing to END")
            return "end"

    def route_to_next_agent(self, state: ExtendedAgentState) -> str:
        """
        Determine next agent based on execution plan
        Validates that the agent has a workflow node, fallback to orchestrator if not
        """
        # Available workflow nodes (agents with implemented nodes)
        AVAILABLE_NODES = {"orchestrator", "architect", "codesmith", "reviewer", "fixer"}

        logger.info(f"🔀 Routing to next agent...")
        logger.info(f"📋 Execution plan has {len(state['execution_plan'])} steps")

        # Find next pending step
        for step in state["execution_plan"]:
            logger.info(f"  Step {step.id} ({step.agent}): {step.status}")
            if step.status == "pending":
                # Check dependencies
                if self._dependencies_met(step, state["execution_plan"]):
                    agent = step.agent
                    # Validate agent has a workflow node
                    if agent not in AVAILABLE_NODES:
                        logger.warning(f"⚠️ Agent '{agent}' has no workflow node - marking as completed with stub")
                        step.status = "completed"
                        step.result = f"⚠️ Agent '{agent}' not yet implemented - stub response for: {step.task}"
                        state["execution_plan"] = list(state["execution_plan"])  # Trigger state update
                        # Continue to check for next step
                        continue
                    step.status = "in_progress"
                    state["current_step_id"] = step.id
                    logger.info(f"✅ Routing to {agent} for step {step.id}")
                    return agent
                else:
                    logger.info(f"⏸️ Step {step.id} waiting for dependencies")

        # All steps complete
        logger.info("🏁 All steps complete - routing to END")
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
        # Simple response for testing
        task = state.get("current_task", "")

        # For agent list queries - return pre-computed result
        # (This is OK since it's just static info, not an action)
        if "agenten" in task.lower() or "agents" in task.lower():
            result_text = """System Agents:
1. Orchestrator - Task decomposition
2. Architect - System design
3. CodeSmith - Code generation
4. Reviewer - Code review
5. Fixer - Bug fixing
6. DocBot - Documentation
7. Research - Web research
8. TradeStrat - Trading strategies
9. OpusArbitrator - Conflict resolution
10. Performance - Performance optimization"""

            return [
                ExecutionStep(
                    id="step1",
                    agent="orchestrator",
                    task="List available agents",
                    expected_output="List of all agents in the system",
                    dependencies=[],
                    status="completed",  # Mark as completed since no execution needed
                    result=result_text
                )
            ]

        # For cache SYSTEM questions - EXECUTE real actions (not code implementation!)
        # Only match if specifically about filling/setting up caches, not implementing cache code
        task_lower_check = task.lower()
        if ("fülle" in task_lower_check or "fill" in task_lower_check or "setup" in task_lower_check) and ("cache" in task_lower_check or "caches" in task_lower_check):
            return [
                ExecutionStep(
                    id="step1",
                    agent="architect",  # Architect handles system setup
                    task="Setup and fill all cache systems",
                    expected_output="Cache setup completed with status report",
                    dependencies=[],
                    status="pending",
                    result=None  # Will be filled by actual execution
                )
            ]

        # For application/system questions
        if "applikation" in task.lower() or "application" in task.lower() or "system" in task.lower() or "workspace" in task.lower() or "was" in task.lower():
            return [
                ExecutionStep(
                    id="step1",
                    agent="orchestrator",
                    task="Describe the KI AutoAgent system",
                    expected_output="System description",
                    dependencies=[],
                    status="pending",
                    result="KI AutoAgent v5.0.0 - Multi-Agent AI Development System\n\nDies ist ein fortschrittliches Multi-Agent-System für die Softwareentwicklung:\n\n🏗️ ARCHITEKTUR:\n• VS Code Extension (TypeScript) - User Interface\n• Python Backend mit LangGraph (Port 8001)\n• WebSocket-basierte Kommunikation\n• 10 spezialisierte KI-Agenten\n\n🤖 HAUPT-FEATURES:\n• Agent-to-Agent Kommunikation\n• Plan-First Mode mit Approval\n• Persistent Memory\n• Dynamic Workflow Modification\n• Automatische Code-Analyse\n\n💡 VERWENDUNG:\nDas System hilft bei der Entwicklung von Software durch intelligente Agenten, die zusammenarbeiten um Code zu generieren, zu reviewen und zu optimieren."
                )
            ]

        # 🎯 HYBRID INTELLIGENT ROUTING: Priority-based keyword matching with confidence scoring
        # ACTION verbs (high priority) override DOMAIN nouns (low priority)
        task_lower = task.lower()

        # Calculate confidence scores for each agent
        scores = self._calculate_agent_confidence(task_lower)

        # If we have a clear winner (confidence > 1.5), route to that agent
        if scores:
            best_agent = max(scores.items(), key=lambda x: x[1])
            agent_name, confidence = best_agent

            # High confidence (>= 2.0) - direct routing
            if confidence >= 2.0:
                logger.info(f"🎯 High-confidence routing: {agent_name} (score: {confidence})")
                return self._create_single_agent_step(agent_name, task)

            # Medium confidence (1.5-2.0) - check for conflicts
            elif confidence >= 1.5:
                # Check if another agent has similar score (ambiguous case)
                sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                if len(sorted_scores) > 1 and sorted_scores[1][1] >= 1.0:
                    # Ambiguous - multiple agents could handle this
                    logger.info(f"⚠️ Ambiguous routing: {sorted_scores[0][0]}={sorted_scores[0][1]}, {sorted_scores[1][0]}={sorted_scores[1][1]}")
                    # Fallback to orchestrator for intelligent decision
                    return self._create_single_agent_step("orchestrator", task)
                else:
                    logger.info(f"🎯 Medium-confidence routing: {agent_name} (score: {confidence})")
                    return self._create_single_agent_step(agent_name, task)

        # No keyword matches or low confidence - use orchestrator
        logger.info(f"🤔 No clear keyword match - routing to orchestrator for intelligent analysis")
        return self._create_single_agent_step("orchestrator", task)

    def _calculate_agent_confidence(self, task_lower: str) -> Dict[str, float]:
        """Calculate confidence score for each agent based on task content

        Priority System:
        - ACTION VERBS (high priority): weight 2.0 (review, fix, implement, optimize)
        - DOMAIN NOUNS (low priority): weight 1.0 (architecture, code, bug, performance)

        This ensures:
        - "Review the architecture" → Reviewer (2.0) beats Architect (1.0)
        - "Fix the microservices bug" → Fixer (4.0) beats Architect (1.0)
        - "Optimize algorithm" → Performance (2.0) beats CodeSmith (1.0)
        """
        scores = {}

        # ACTION VERBS (high priority - weight 2.0)
        action_patterns = {
            'reviewer': ['review', 'analyse', 'analyze', 'prüfe', 'check', 'validiere', 'validate'],
            'fixer': ['fix', 'fixe', 'behebe', 'repair', 'löse', 'solve'],
            'codesmith': ['implement', 'implementiere', 'write', 'schreibe', 'create code', 'erstelle code',
                         'generate code', 'create a', 'write a', 'implement a'],
            'performance': ['optimize', 'optimiere', 'speed up', 'improve performance', 'make faster'],
            'architect': ['design architecture', 'design system', 'design microservice', 'create architecture'],
            'docbot': ['document', 'dokumentiere', 'write documentation', 'create readme'],
            'research': ['research', 'recherche', 'search for', 'suche nach', 'find information'],
        }

        # DOMAIN NOUNS (lower priority - weight 1.0)
        domain_patterns = {
            'architect': ['architecture', 'architektur', 'microservice', 'system design', 'infrastructure'],
            'codesmith': ['function', 'funktion', 'class', 'klasse', 'algorithm', 'algorithmus'],
            'reviewer': ['security', 'sicherheit', 'quality', 'qualität'],
            'fixer': ['bug', 'error', 'fehler', 'exception', 'problem', 'crash'],
            'performance': ['performance', 'efficiency', 'speed', 'faster', 'schneller', 'slow'],
            'docbot': ['readme', 'docstring', 'comments', 'kommentare'],
            'research': ['latest', 'neuesten', 'web', 'what are', 'was sind'],
            'tradestrat': ['trading', 'strategy', 'strategie', 'crypto', 'stock', 'backtest'],
        }

        # Calculate action scores (high priority)
        for agent, patterns in action_patterns.items():
            for pattern in patterns:
                if pattern in task_lower:
                    scores[agent] = scores.get(agent, 0) + 2.0
                    logger.debug(f"  Action match: {agent} +2.0 for '{pattern}'")

        # Calculate domain scores (lower priority)
        for agent, patterns in domain_patterns.items():
            for pattern in patterns:
                if pattern in task_lower:
                    scores[agent] = scores.get(agent, 0) + 1.0
                    logger.debug(f"  Domain match: {agent} +1.0 for '{pattern}'")

        return scores

    def _create_single_agent_step(self, agent: str, task: str) -> List[ExecutionStep]:
        """Helper to create a single execution step for an agent

        For orchestrator, returns a completed step with stub response since orchestrator
        can't be a destination node in the workflow (only the entry point).
        """
        output_map = {
            'architect': 'System architecture design',
            'codesmith': 'Code implementation',
            'reviewer': 'Code review and analysis',
            'fixer': 'Bug fix and solution',
            'docbot': 'Documentation',
            'research': 'Research results',
            'tradestrat': 'Trading strategy',
            'performance': 'Performance optimization',
            'orchestrator': 'Intelligent task analysis and routing'
        }

        # If orchestrator, mark as completed with stub response
        # (can't route back to orchestrator node - it's only the entry point)
        if agent == "orchestrator":
            return [
                ExecutionStep(
                    id="step1",
                    agent="orchestrator",
                    task=task,
                    expected_output="Intelligent analysis and response",
                    dependencies=[],
                    status="completed",
                    result=f"""🎯 ORCHESTRATOR RESPONSE

**Query:** {task}

Based on my analysis, this query requires contextual understanding. As the orchestrator, I'm routing this to the appropriate specialist.

⚠️ STUB RESPONSE - Real orchestrator would provide detailed analysis."""
                )
            ]

        return [
            ExecutionStep(
                id="step1",
                agent=agent,
                task=task,
                expected_output=output_map.get(agent, "Task result"),
                dependencies=[],
                status="pending",
                result=None
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

    # Real agent execution methods
    async def _execute_architect_task(self, state: ExtendedAgentState, step: ExecutionStep) -> Any:
        """Execute architect task with real ArchitectAgent"""
        # Check if this is a cache setup task
        if "cache" in step.task.lower():
            logger.info("🔧 Executing cache setup task...")
            cache_manager = CacheManager()
            result = cache_manager.fill_caches()
            return result["summary"]

        # Use real architect agent if available
        if "architect" in self.real_agents:
            logger.info("🏗️ Executing with real ArchitectAgent...")
            try:
                agent = self.real_agents["architect"]
                task_request = TaskRequest(
                    task_id=step.id,
                    task_type="architecture",
                    content=step.task,
                    context={
                        "workspace_path": state.get("workspace_path"),
                        "session_id": state.get("session_id")
                    }
                )
                result = await agent.execute_task(task_request)
                return result.result if hasattr(result, 'result') else str(result)
            except Exception as e:
                logger.error(f"❌ Real architect agent failed: {e}")
                return f"Architect task completed with error: {str(e)}"

        # Fallback to stub
        logger.warning("⚠️ Using stub for architect task")
        await asyncio.sleep(1)

        # Return a comprehensive architecture response for testing
        return f"""🏗️ SYSTEM ARCHITECTURE DESIGN

**Task:** {step.task}

**1. HIGH-LEVEL ARCHITECTURE:**
- API Gateway (Kong/Nginx)
- Service Mesh (Istio)
- Microservices (Node.js/Python)
- Message Broker (Kafka/RabbitMQ)
- Database Layer (PostgreSQL/MongoDB)

**2. KEY DESIGN DECISIONS:**
- Event-driven architecture for loose coupling
- CQRS for read/write separation
- Saga pattern for distributed transactions
- Circuit breaker for resilience

**3. TECHNOLOGY STACK:**
- Container Orchestration: Kubernetes
- Service Discovery: Consul/Eureka
- Monitoring: Prometheus + Grafana
- Logging: ELK Stack

**4. SCALABILITY CONSIDERATIONS:**
- Horizontal pod autoscaling
- Database sharding
- Caching layer (Redis)
- CDN integration

⚠️ This is a STUB response - real ArchitectAgent would provide more detailed analysis."""

    async def _execute_codesmith_task(self, state: ExtendedAgentState, step: ExecutionStep, patterns: List) -> Any:
        """Execute codesmith task with comprehensive code stub"""
        logger.warning("⚠️ Using stub for codesmith task")
        await asyncio.sleep(1)

        # Return comprehensive code implementation for testing
        return f"""💻 CODE IMPLEMENTATION

**Task:** {step.task}

```python
from collections import OrderedDict
from threading import RLock

class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.lock = RLock()

    def get(self, key: int) -> int:
        with self.lock:
            if key not in self.cache:
                return -1
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key: int, value: int) -> None:
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.capacity:
                oldest = next(iter(self.cache))
                del self.cache[oldest]
```

**Features:** Thread-safety (RLock), Capacity limit, LRU eviction, O(1) operations

⚠️ STUB response - real CodeSmith would provide more detailed implementation."""

    async def _execute_reviewer_task(self, state: ExtendedAgentState, step: ExecutionStep) -> Any:
        """Execute reviewer task with comprehensive review stub"""
        logger.warning("⚠️ Using stub for reviewer task")
        await asyncio.sleep(1)

        return f"""📝 CODE REVIEW REPORT

**Task:** {step.task}

**🔍 Security Analysis:**
✓ No SQL injection vulnerabilities detected
✓ No XSS vulnerabilities
⚠️ Consider input validation for user-provided data

**🎯 Code Quality:**
✓ Follows PEP 8 style guidelines
✓ Good function naming conventions
⚠️ Missing type hints in some functions
⚠️ Could benefit from more comprehensive docstrings

**⚡ Performance:**
✓ No obvious performance bottlenecks
✓ Efficient data structures used
💡 Suggestion: Consider caching for frequently accessed data

**🧪 Testing:**
⚠️ Missing unit tests for edge cases
💡 Recommendation: Add tests for error handling

**📊 Overall Assessment:**
- Code Quality: 7/10
- Security: 8/10
- Performance: 8/10
- Maintainability: 7/10

**✅ Approved with minor recommendations**

⚠️ STUB response - real Reviewer would provide line-specific analysis."""

    async def _execute_fixer_task(self, state: ExtendedAgentState, step: ExecutionStep, issues: List) -> Any:
        """Execute fixer task with comprehensive fix stub"""
        logger.warning("⚠️ Using stub for fixer task")
        await asyncio.sleep(1)

        return f"""🔧 BUG FIX REPORT

**Task:** {step.task}

**🐛 Issues Identified:**
1. IndexError: list index out of range
   - Location: Attempting to access users[0] on empty list
   - Severity: HIGH

**✅ Applied Fixes:**

```python
# Before (buggy code):
users = []
users[0] = 'admin'  # IndexError!

# After (fixed code):
users = []
if len(users) == 0:
    users.append('admin')
else:
    users[0] = 'admin'

# Or better:
users = ['admin']  # Direct initialization
```

**📋 Changes Made:**
- Added bounds checking before list access
- Replaced direct indexing with append() for empty lists
- Added defensive programming practices

**🧪 Test Results:**
✓ Fix verified with unit tests
✓ No regressions detected
✓ Edge cases covered

**💡 Additional Recommendations:**
- Add input validation at function entry
- Consider using collections.defaultdict for safer access
- Add logging for debugging

**Status:** ✅ FIXED & VERIFIED

⚠️ STUB response - real FixerBot would provide detailed line-by-line fixes with git diffs."""

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
        # Orchestrator ONLY goes to approval (no conditional edges to avoid conflicts)
        workflow.add_edge("orchestrator", "approval")

        # Conditional routing after approval - supports all agents
        workflow.add_conditional_edges(
            "approval",
            self.route_after_approval,
            {
                "architect": "architect",
                "codesmith": "codesmith",
                "reviewer": "reviewer",
                "fixer": "fixer",
                "end": END
            }
        )

        # Dynamic routing based on execution plan
        # Each agent (except orchestrator) can route to next agent or end
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

            # Extract result from execution plan
            if final_state.get("execution_plan"):
                results = []
                for step in final_state["execution_plan"]:
                    if step.result:
                        results.append(step.result)
                if results:
                    final_state["final_result"] = "\n".join(str(r) for r in results)
                else:
                    final_state["final_result"] = "Task completed but no specific results available."
            else:
                final_state["final_result"] = "No execution plan was created."

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