"""
Main workflow creation for KI AutoAgent using LangGraph
Integrates all agents with extended features
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
# Try to import async checkpointer for better asyncio support
try:
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    ASYNC_CHECKPOINTER_AVAILABLE = True
except ImportError:
    from langgraph.checkpoint.sqlite import SqliteSaver
    ASYNC_CHECKPOINTER_AVAILABLE = False
    logger.warning("AsyncSqliteSaver not available, using sync version")

from .state import ExtendedAgentState, create_initial_state, ExecutionStep, TaskLedger, ProgressLedger
from .extensions import (
    ToolRegistry,
    ApprovalManager,
    PersistentAgentMemory,
    DynamicWorkflowManager,
    get_tool_registry
)
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)

# v5.5.1: Import Intelligent Query Handler
try:
    from .intelligent_query_handler import IntelligentQueryHandler
    INTELLIGENT_HANDLER_AVAILABLE = True
    logger.info("✅ Intelligent Query Handler loaded")
except ImportError as e:
    logger.warning(f"⚠️ Intelligent Query Handler not available: {e}")
    INTELLIGENT_HANDLER_AVAILABLE = False
    IntelligentQueryHandler = None

# v5.5.0: Import Self-Diagnosis System
try:
    from .workflow_self_diagnosis import WorkflowSelfDiagnosisSystem
    SELF_DIAGNOSIS_AVAILABLE = True
    logger.info("✅ Self-Diagnosis System loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Self-Diagnosis System not available: {e}")
    SELF_DIAGNOSIS_AVAILABLE = False
    WorkflowSelfDiagnosisSystem = None

# v5.5.2: Import Safe Orchestrator Executor
try:
    from .safe_orchestrator_executor import SafeOrchestratorExecutor
    from .query_classifier import EnhancedQueryClassifier
    from .development_query_handler import DevelopmentQueryHandler
    SAFE_EXECUTOR_AVAILABLE = True
    logger.info("✅ Safe Orchestrator Executor loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Safe Orchestrator Executor not available: {e}")
    SAFE_EXECUTOR_AVAILABLE = False
    SafeOrchestratorExecutor = None
    EnhancedQueryClassifier = None
    DevelopmentQueryHandler = None

# Import real agents
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REAL_AGENTS_AVAILABLE = False
ORCHESTRATOR_AVAILABLE = False
RESEARCH_AVAILABLE = False
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

# Import Orchestrator for complex task decomposition
try:
    from agents.specialized.orchestrator_agent import OrchestratorAgent
    ORCHESTRATOR_AVAILABLE = True
    logger.info("✅ Orchestrator agent imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Could not import Orchestrator: {e}")
    logger.warning(f"⚠️ Complex task decomposition will use fallback logic")

# Import ResearchAgent for web research
try:
    from agents.specialized.research_agent import ResearchAgent
    RESEARCH_AVAILABLE = True
    logger.info("✅ Research agent imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Could not import ResearchAgent: {e}")
    logger.warning(f"⚠️ Web research will not be available")

# Import DocuBotAgent for documentation generation
try:
    from agents.specialized.docubot_agent import DocuBotAgent
    DOCBOT_AVAILABLE = True
    logger.info("✅ DocuBot agent imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Could not import DocuBotAgent: {e}")
    logger.warning(f"⚠️ Documentation generation will use stub")

# Import PerformanceBot for performance optimization
try:
    from agents.specialized.performance_bot import PerformanceBot
    PERFORMANCE_AVAILABLE = True
    logger.info("✅ Performance agent imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Could not import PerformanceBot: {e}")
    logger.warning(f"⚠️ Performance optimization will use stub")

# Import TradeStratAgent for trading strategies
try:
    from agents.specialized.tradestrat_agent import TradeStratAgent
    TRADESTRAT_AVAILABLE = True
    logger.info("✅ TradeStrat agent imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Could not import TradeStratAgent: {e}")
    logger.warning(f"⚠️ Trading strategies will use stub")

# Import OpusArbitratorAgent for conflict resolution
try:
    from agents.specialized.opus_arbitrator_agent import OpusArbitratorAgent
    OPUS_AVAILABLE = True
    logger.info("✅ OpusArbitrator agent imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Could not import OpusArbitratorAgent: {e}")
    logger.warning(f"⚠️ Conflict resolution will use stub")


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

        # Initialize active workflows tracking (v5.3.1 bugfix)
        # This allows architecture approval to be processed correctly
        self.active_workflows = {}

        # v5.5.0: Initialize Self-Diagnosis System
        self.self_diagnosis = None
        if SELF_DIAGNOSIS_AVAILABLE:
            try:
                self.self_diagnosis = WorkflowSelfDiagnosisSystem()
                logger.info("🏥 Self-Diagnosis System initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Self-Diagnosis System: {e}")
                self.self_diagnosis = None

        # v5.5.1: Initialize Intelligent Query Handler
        self.intelligent_handler = None
        if INTELLIGENT_HANDLER_AVAILABLE:
            try:
                self.intelligent_handler = IntelligentQueryHandler()
                logger.info("🧠 Intelligent Query Handler initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Intelligent Query Handler: {e}")
                self.intelligent_handler = None

        # v5.5.2: Initialize Safe Orchestrator Executor
        self.safe_executor = None
        self.query_classifier = None
        self.dev_handler = None
        if SAFE_EXECUTOR_AVAILABLE:
            try:
                self.safe_executor = SafeOrchestratorExecutor()
                self.query_classifier = EnhancedQueryClassifier()
                self.dev_handler = DevelopmentQueryHandler()
                logger.info("🛡️ Safe Orchestrator Executor initialized (v5.5.2)")
            except Exception as e:
                logger.error(f"Failed to initialize Safe Orchestrator Executor: {e}")
                self.safe_executor = None

        # Initialize workflow
        self.workflow = None

        # Initialize checkpointer for workflow state persistence (v5.4.0)
        # v5.5.3: Use AsyncSqliteSaver for better asyncio support when available
        # This fixes "no running event loop" errors in human-in-the-loop workflows
        self.checkpointer = None  # Will be initialized in async context
        self.checkpointer_path = db_path  # Store for async init

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

            # Add Orchestrator for complex task decomposition (Phase 2)
            if ORCHESTRATOR_AVAILABLE:
                try:
                    orchestrator = OrchestratorAgent()
                    # Connect to memory system
                    if "orchestrator" in self.agent_memories:
                        orchestrator.memory_manager = self.agent_memories["orchestrator"]
                    self.real_agents["orchestrator"] = orchestrator
                    logger.info("✅ Orchestrator initialized with AI decomposition")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to initialize Orchestrator: {e}")

            # Add ResearchAgent for web research
            if RESEARCH_AVAILABLE:
                try:
                    research = ResearchAgent()
                    # Connect to memory system
                    if "research" in self.agent_memories:
                        research.memory_manager = self.agent_memories["research"]
                    self.real_agents["research"] = research
                    logger.info("✅ ResearchAgent initialized with Perplexity API")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to initialize ResearchAgent: {e}")

            # Add DocuBotAgent for documentation
            if DOCBOT_AVAILABLE:
                try:
                    docbot = DocuBotAgent()
                    if "docbot" in self.agent_memories:
                        docbot.memory_manager = self.agent_memories["docbot"]
                    self.real_agents["docbot"] = docbot
                    logger.info("✅ DocuBotAgent initialized")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to initialize DocuBotAgent: {e}")

            # Add PerformanceBot for optimization
            if PERFORMANCE_AVAILABLE:
                try:
                    performance = PerformanceBot()
                    if "performance" in self.agent_memories:
                        performance.memory_manager = self.agent_memories["performance"]
                    self.real_agents["performance"] = performance
                    logger.info("✅ PerformanceBot initialized")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to initialize PerformanceBot: {e}")

            # Add TradeStratAgent for trading strategies
            if TRADESTRAT_AVAILABLE:
                try:
                    tradestrat = TradeStratAgent()
                    if "tradestrat" in self.agent_memories:
                        tradestrat.memory_manager = self.agent_memories["tradestrat"]
                    self.real_agents["tradestrat"] = tradestrat
                    logger.info("✅ TradeStratAgent initialized")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to initialize TradeStratAgent: {e}")

            # Add OpusArbitratorAgent for conflict resolution
            if OPUS_AVAILABLE:
                try:
                    opus = OpusArbitratorAgent()
                    if "opus_arbitrator" in self.agent_memories:
                        opus.memory_manager = self.agent_memories["opus_arbitrator"]
                    self.real_agents["opus_arbitrator"] = opus
                    logger.info("✅ OpusArbitratorAgent initialized")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to initialize OpusArbitratorAgent: {e}")

            logger.info(f"✅ Initialized {len(self.real_agents)} real agents")
        except Exception as e:
            logger.error(f"❌ Failed to initialize real agents: {e}")
            logger.exception(e)
            self.real_agents = {}

    # =================== v5.4.3: Enhanced Workflow Management ===================

    def create_task_ledger(self, task: str, steps: List[ExecutionStep]) -> TaskLedger:
        """
        v5.4.3: Create a Task Ledger for tracking task decomposition
        """
        now = datetime.now()
        completion_criteria = self.extract_success_criteria(task)

        # Estimate duration based on step count and agent types
        estimated_duration = 0
        for step in steps:
            # Rough estimates per agent type
            agent_durations = {
                "orchestrator": 5,
                "architect": 120,
                "codesmith": 180,
                "reviewer": 60,
                "fixer": 120,
                "research": 90,
                "docbot": 60,
                "performance": 90,
                "tradestrat": 60
            }
            estimated_duration += agent_durations.get(step.agent, 60)

        return TaskLedger(
            original_task=task,
            decomposed_steps=steps,
            completion_criteria=completion_criteria,
            progress_summary="Task decomposition complete, ready for execution",
            created_at=now,
            last_updated=now,
            total_estimated_duration=estimated_duration
        )

    def extract_success_criteria(self, task: str) -> List[str]:
        """
        v5.4.3: Extract success criteria from task description
        """
        criteria = []

        # Common success patterns
        if any(word in task.lower() for word in ["fix", "repair", "solve"]):
            criteria.append("Issue resolved and verified")
        if any(word in task.lower() for word in ["implement", "create", "build"]):
            criteria.append("Feature implemented and tested")
        if any(word in task.lower() for word in ["optimize", "improve", "speed up"]):
            criteria.append("Performance improved and measured")
        if any(word in task.lower() for word in ["review", "analyze", "check"]):
            criteria.append("Analysis complete with findings documented")
        if any(word in task.lower() for word in ["document", "write", "explain"]):
            criteria.append("Documentation complete and clear")

        # Default if no specific criteria found
        if not criteria:
            criteria.append("Task completed successfully")

        return criteria

    def create_progress_ledger(self, steps: List[ExecutionStep]) -> ProgressLedger:
        """
        v5.4.3: Create a Progress Ledger for tracking workflow progress
        """
        ledger = ProgressLedger(
            total_steps=len(steps),
            completed_steps=0,
            failed_steps=0,
            in_progress_steps=0,
            blocked_steps=0,
            current_phase="planning",
            estimated_completion=None,
            overall_progress_percentage=0.0
        )
        ledger.update_from_steps(steps)
        return ledger

    async def check_and_handle_timeouts(self, state: ExtendedAgentState) -> ExtendedAgentState:
        """
        v5.4.3: Check for timed-out steps and handle retries
        """
        steps_modified = False

        for step in state["execution_plan"]:
            # Check timeout for in_progress steps
            if step.status == "in_progress" and step.is_timeout():
                logger.warning(f"⏱️ Step {step.id} ({step.agent}) timed out after {step.timeout_seconds}s")

                # Record the attempt
                step.attempts.append({
                    "attempt": step.retry_count + 1,
                    "status": "timeout",
                    "duration": step.timeout_seconds,
                    "timestamp": datetime.now().isoformat()
                })

                # Check if can retry
                if step.can_retry():
                    delay = step.get_retry_delay()
                    logger.info(f"🔄 Retrying step {step.id} after {delay}s delay (attempt {step.retry_count + 1}/{step.max_retries})")
                    step.status = "pending"  # Reset to pending for retry
                    step.retry_count += 1
                    step.started_at = None
                    steps_modified = True

                    # Add retry message
                    state["messages"].append({
                        "role": "system",
                        "content": f"Step {step.id} timed out. Retrying (attempt {step.retry_count}/{step.max_retries})"
                    })
                else:
                    # Max retries reached, mark as failed
                    logger.error(f"❌ Step {step.id} failed after {step.max_retries} retries")
                    step.status = "failed"
                    step.error = f"Timeout after {step.max_retries} attempts"
                    step.end_time = datetime.now()
                    steps_modified = True

        if steps_modified:
            state["execution_plan"] = list(state["execution_plan"])  # Trigger state update

        return state

    def identify_parallel_groups(self, steps: List[ExecutionStep]) -> Dict[str, List[ExecutionStep]]:
        """
        v5.4.3: Identify steps that can run in parallel
        Groups steps with no dependencies on each other
        """
        parallel_groups = {}
        group_counter = 0

        # Track which steps are processed
        processed = set()

        for step in steps:
            if step.id in processed:
                continue

            # Find all steps that can run in parallel with this one
            parallel_candidates = [step]

            for other in steps:
                if other.id == step.id or other.id in processed:
                    continue

                # Check if they have no dependencies on each other
                if not self._has_dependency_conflict(step, other, steps):
                    parallel_candidates.append(other)
                    processed.add(other.id)

            # Create parallel group if more than one step
            if len(parallel_candidates) > 1:
                group_id = f"parallel_group_{group_counter}"
                parallel_groups[group_id] = parallel_candidates
                group_counter += 1

                # Mark steps with parallel group
                for s in parallel_candidates:
                    s.can_run_parallel = True
                    s.parallel_group = group_id

            processed.add(step.id)

        return parallel_groups

    def _has_dependency_conflict(self, step1: ExecutionStep, step2: ExecutionStep, all_steps: List[ExecutionStep]) -> bool:
        """
        Check if two steps have dependency conflicts preventing parallel execution
        """
        # Direct dependency check
        if step1.id in step2.dependencies or step2.id in step1.dependencies:
            return True

        # Transitive dependency check (simplified)
        step1_deps = self._get_all_dependencies(step1, all_steps)
        step2_deps = self._get_all_dependencies(step2, all_steps)

        # Check if either depends on the other transitively
        if step1.id in step2_deps or step2.id in step1_deps:
            return True

        return False

    def _get_all_dependencies(self, step: ExecutionStep, all_steps: List[ExecutionStep]) -> set:
        """
        Get all transitive dependencies of a step
        """
        deps = set(step.dependencies)
        to_process = list(step.dependencies)

        while to_process:
            dep_id = to_process.pop()
            dep_step = next((s for s in all_steps if s.id == dep_id), None)
            if dep_step:
                for sub_dep in dep_step.dependencies:
                    if sub_dep not in deps:
                        deps.add(sub_dep)
                        to_process.append(sub_dep)

        return deps

    # =================== End v5.4.3 Enhancements ===================

    # =================== v5.8.1: Agent Activity Visualization ===================

    async def _send_agent_activity(
        self,
        state: ExtendedAgentState,
        activity_type: str,
        agent: str,
        content: str = "",
        tool: str = "",
        tool_status: str = "",
        tool_result: Any = None
    ):
        """
        Send agent activity messages to UI for visualization

        Args:
            state: Current workflow state
            activity_type: "thinking" | "tool_start" | "tool_complete" | "progress" | "complete"
            agent: Agent name (architect, codesmith, etc.)
            content: Activity description
            tool: Tool name (if tool-related)
            tool_status: "running" | "success" | "error"
            tool_result: Tool execution result
        """
        if not self.websocket_manager or not state.get("client_id"):
            return

        try:
            message = {
                "type": f"agent_{activity_type}",
                "agent": agent,
                "timestamp": datetime.now().isoformat()
            }

            if content:
                message["content"] = content

            if tool:
                message["tool"] = tool
                message["tool_status"] = tool_status

                if tool_result is not None:
                    # Truncate large results
                    result_str = str(tool_result)
                    if len(result_str) > 500:
                        result_str = result_str[:500] + "..."
                    message["tool_result"] = result_str

            await self.websocket_manager.send_json(state["client_id"], message)
            logger.debug(f"📤 Sent {agent} activity: {activity_type}")

        except Exception as e:
            logger.error(f"Failed to send agent activity: {e}")

    # =================== End Agent Activity Visualization ===================

    async def orchestrator_node(self, state: ExtendedAgentState) -> ExtendedAgentState:
        """
        Orchestrator node - plans and decomposes tasks
        Handles both initial planning and dynamic re-planning for agent collaboration
        """
        logger.info("🎯 Orchestrator node executing")
        state["current_agent"] = "orchestrator"

        # 🔄 CHECK: Is this a re-planning request from an agent?
        if state.get("needs_replan"):
            logger.info("🔄 RE-PLANNING MODE: Agent requested collaboration")
            suggested_agent = state.get("suggested_agent", "unknown")
            suggested_query = state.get("suggested_query", "Continue work")
            current_agent = state.get("current_agent", "unknown")

            # 📊 TRACK COLLABORATION (v5.1.0: Information-First Escalation)
            collab_count = state.get("collaboration_count", 0) + 1
            state["collaboration_count"] = collab_count

            # Track agent sequence pattern
            last_agents = list(state.get("last_collaboration_agents", []))
            last_agents.append(current_agent)
            last_agents.append(suggested_agent)
            state["last_collaboration_agents"] = last_agents[-10:]  # Keep last 10

            # Track Reviewer↔Fixer specific cycles
            if current_agent == "reviewer" and suggested_agent == "fixer":
                rf_cycles = state.get("reviewer_fixer_cycles", 0) + 1
                state["reviewer_fixer_cycles"] = rf_cycles

            # Log detailed collaboration history
            history = list(state.get("collaboration_history", []))
            history.append({
                "from": current_agent,
                "to": suggested_agent,
                "query": suggested_query[:100],
                "count": collab_count,
                "timestamp": datetime.now().isoformat()
            })
            state["collaboration_history"] = history

            logger.info(f"📊 Collaboration #{collab_count}: {current_agent} → {suggested_agent}")
            logger.info(f"📊 Reviewer↔Fixer cycles: {state.get('reviewer_fixer_cycles', 0)}")

            # 🚨 CHECK ESCALATION NEEDED (v5.1.0)
            escalation_result = self._check_escalation_needed(state, suggested_agent, suggested_query)
            if escalation_result["escalate"]:
                # Override suggested agent based on escalation logic
                suggested_agent = escalation_result["new_agent"]
                suggested_query = escalation_result["new_query"]
                state["escalation_level"] = escalation_result["level"]
                logger.warning(f"⚠️ ESCALATION LEVEL {escalation_result['level']}: {escalation_result['reason']}")

            # Create new step for the suggested agent
            existing_plan = state.get("execution_plan", [])
            next_step_id = len(existing_plan) + 1

            new_step = ExecutionStep(
                id=next_step_id,
                agent=suggested_agent,
                task=suggested_query,
                status="pending",
                dependencies=[]  # No dependencies, can execute immediately
            )

            # Add to execution plan
            existing_plan.append(new_step)
            state["execution_plan"] = list(existing_plan)  # Trigger state update

            # Clear replan flags
            state["needs_replan"] = False
            state["suggested_agent"] = None
            state["suggested_query"] = None

            logger.info(f"  ✅ Added Step {next_step_id}: {suggested_agent} - {suggested_query[:50]}")
            state["status"] = "executing"
            return state

        # 🔄 CHECK: Are we resuming from approval?
        if state.get("resume_from_approval"):
            logger.info("✅ RESUMING FROM APPROVAL - Skipping planning, using existing execution plan")
            logger.info(f"📋 Existing execution plan has {len(state.get('execution_plan', []))} steps")

            # Clear the resume flag
            state["resume_from_approval"] = False

            # Log the execution plan status
            if state.get("execution_plan"):
                for i, step in enumerate(state["execution_plan"][:5]):  # First 5 steps
                    logger.info(f"   Step {i+1}: {step.agent} - {step.status} - {step.task[:50]}...")

            # Set status to executing
            state["status"] = "executing"
            return state

        # 📋 INITIAL PLANNING MODE
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

        # v5.4.3: Create Task Ledger for tracking
        if state["messages"]:
            original_task = state["messages"][-1]["content"]
            task_ledger = self.create_task_ledger(original_task, plan)
            state["task_ledger"] = task_ledger
            logger.info(f"📖 Created Task Ledger with {len(task_ledger.completion_criteria)} success criteria")

        # v5.4.3: Create Progress Ledger
        progress_ledger = self.create_progress_ledger(plan)
        state["progress_ledger"] = progress_ledger
        logger.info(f"📊 Created Progress Ledger - {progress_ledger.total_steps} total steps")

        # v5.4.3: Identify parallel execution opportunities
        parallel_groups = self.identify_parallel_groups(plan)
        if parallel_groups:
            logger.info(f"⚡ Identified {len(parallel_groups)} parallel execution groups")
            for group_id, steps in parallel_groups.items():
                step_ids = [s.id for s in steps]
                logger.info(f"   {group_id}: Steps {step_ids} can run in parallel")

        # v5.5.0: COMPREHENSIVE PRE-EXECUTION VALIDATION
        if self.self_diagnosis:
            logger.info("🔍 Running Pre-Execution Validation (v5.5.0)")
            try:
                # Run comprehensive validation with auto-fix
                is_safe, validated_state = await self.self_diagnosis.pre_execution_check(
                    state,
                    auto_fix=True  # Allow automatic fixes for critical issues
                )

                if not is_safe:
                    logger.error("❌ Pre-Execution Validation FAILED - Plan is NOT safe to execute")

                    # Add error message to state
                    state["messages"].append({
                        "role": "system",
                        "content": "⚠️ Pre-execution validation failed. The execution plan has critical issues that need review. Please check the logs for details."
                    })

                    # Mark workflow as failed
                    state["status"] = "validation_failed"

                    # Create a simple fallback plan
                    fallback_step = ExecutionStep(
                        id="fallback_1",
                        agent="orchestrator",
                        task="Validation failed - please review and fix the issues",
                        status="completed",
                        result="Pre-execution validation detected critical issues. Manual intervention required."
                    )
                    state["execution_plan"] = [fallback_step]

                    logger.error("🔄 Created fallback plan due to validation failure")
                    return state
                else:
                    logger.info("✅ Pre-Execution Validation PASSED - Plan is safe to execute")
                    # Use the validated (potentially fixed) state
                    state = validated_state

            except Exception as e:
                logger.error(f"Error during pre-execution validation: {e}")
                # Continue without validation on error
                logger.warning("⚠️ Continuing without validation due to error")
        else:
            logger.warning("⚠️ Self-Diagnosis System not available - skipping validation")

        # Set default approval type to none
        # This will be overridden to "architecture_proposal" by architect_node if needed
        if not state.get("approval_type") or state.get("approval_type") == "execution_plan":
            state["approval_type"] = "none"
            logger.info("📋 Set approval_type to 'none' (no approval needed)")

        # Set status to executing
        state["status"] = "executing"

        # Mark all steps as pending (keep completed/failed as is)
        for step in plan:
            if step.status != "failed" and step.status != "completed":
                step.status = "pending"
        state["execution_plan"] = list(plan)

        logger.info(f"📋 Orchestrator created {len(plan)}-step execution plan")

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
        Approval node for Architecture Proposals (v5.4.0)

        Simplified: Only handles architecture_proposal approval
        Plan-First mode removed for simplicity
        """
        logger.info("✅ Approval node executing")

        # Check if this is an architecture proposal
        approval_type = state.get("approval_type", "none")

        if approval_type == "architecture_proposal":
            proposal_status = state.get("proposal_status", "none")

            if proposal_status == "pending":
                # Pause workflow - wait for user approval
                logger.info("📋 Architecture proposal pending - workflow will pause here")
                state["status"] = "waiting_architecture_approval"
                state["waiting_for_approval"] = True
                logger.info("⏸️  Workflow pausing - user must approve via WebSocket")
                return state

            elif proposal_status == "approved":
                # Continue workflow
                logger.info("✅ Architecture proposal approved - continuing workflow")
                state["needs_approval"] = False
                state["waiting_for_approval"] = False
                state["approval_status"] = "approved"
                state["approval_type"] = "none"
                state["status"] = "executing"
                return state

            elif proposal_status == "rejected":
                # End workflow
                logger.info("❌ Architecture proposal rejected - ending workflow")
                state["needs_approval"] = False
                state["waiting_for_approval"] = False
                state["approval_status"] = "rejected"
                state["status"] = "failed"
                return state

            elif proposal_status == "modified":
                # Route back to architect for revision
                logger.info("🔄 Architecture proposal needs modifications")
                state["needs_approval"] = True
                state["waiting_for_approval"] = False
                state["approval_status"] = "modified"
                return state

            logger.warning(f"⚠️  Unexpected proposal_status: {proposal_status}")
            return state

        # Check if first step is architect - if so, let it create proposal
        first_step = None
        execution_plan = state.get("execution_plan", [])
        logger.info(f"🔌 WebSocket DEBUG: Checking execution plan with {len(execution_plan)} steps")
        for step in execution_plan:
            logger.info(f"🔌 WebSocket DEBUG: Step {step.id}: agent={step.agent}, status={step.status}")
            if step.status == "pending" and self._dependencies_met(step, state["execution_plan"]):
                first_step = step
                logger.info(f"🔌 WebSocket DEBUG: Found first pending step: {step.agent}")
                break

        if first_step and first_step.agent == "architect":
            # Don't auto-approve - let architect create proposal first
            logger.info("🏗️ First step is architect - allowing proposal creation")
            logger.info(f"🔌 WebSocket DEBUG: Architect will create proposal for client_id: {state.get('client_id')}")
            logger.info(f"🔌 WebSocket DEBUG: Current session_id: {state.get('session_id')}")
            logger.info(f"🔌 WebSocket DEBUG: WebSocket manager available: {self.websocket_manager is not None}")
            state["approval_status"] = "approved"  # Allow workflow to continue to architect
            state["waiting_for_approval"] = False
            first_step.status = "in_progress"
            state["current_step_id"] = first_step.id
            state["execution_plan"] = list(state["execution_plan"])
            logger.info(f"📍 Set current_step_id to: {first_step.id} for agent: architect")
        else:
            # No architecture proposal needed - auto-approve
            logger.info("📌 Auto-approving - no architecture proposal needed")
            state["approval_status"] = "approved"
            state["waiting_for_approval"] = False

            # Set first pending step to in_progress
            if first_step:
                first_step.status = "in_progress"
                state["current_step_id"] = first_step.id
                state["execution_plan"] = list(state["execution_plan"])
                logger.info(f"📍 Set current_step_id to: {first_step.id} for agent: {first_step.agent}")

        return state

    async def architect_node(self, state: ExtendedAgentState) -> ExtendedAgentState:
        """
        Architect agent node - system design and architecture

        v5.2.0: Now includes Architecture Proposal System
        Flow:
        1. Do research (existing behavior)
        2. Create proposal and wait for user approval
        3. If approved: finalize architecture
        4. If rejected/modified: revise and re-submit
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

        try:
            # ============================================================
            # v5.2.0: PHASE 1 - Check proposal status
            # ============================================================
            proposal_status = state.get("proposal_status", "none")

            # CASE 1: Proposal approved → Finalize architecture
            if proposal_status == "approved":
                logger.info("✅ Proposal approved - finalizing architecture")
                final_result = await self._finalize_architecture(state)
                current_step.result = final_result
                current_step.status = "completed"
                state["execution_plan"] = list(state["execution_plan"])

                # Store in memory
                memory.store_memory(
                    content=f"Approved architecture: {current_step.task}",
                    memory_type="procedural",
                    importance=0.9,
                    metadata={"result": final_result, "user_approved": True},
                    session_id=state.get("session_id")
                )

                logger.info("✅ Architecture finalized after approval")
                return state

            # CASE 2: Proposal rejected/modified → Revise
            if proposal_status in ["rejected", "modified"]:
                logger.info(f"✏️ Proposal {proposal_status} - revising based on feedback")
                user_feedback = state.get("user_feedback_on_proposal", "")

                revised_proposal = await self._revise_proposal(state, user_feedback)
                state["architecture_proposal"] = revised_proposal
                state["proposal_status"] = "pending"
                state["needs_approval"] = True
                state["approval_type"] = "architecture_proposal"

                # Format for user
                formatted_msg = self._format_proposal_for_user(revised_proposal)

                # Send to user
                state["messages"].append({
                    "role": "assistant",
                    "content": formatted_msg,
                    "type": "architecture_proposal_revised",
                    "proposal": revised_proposal
                })

                # Send via WebSocket (v5.8.1: ensure consistent format)
                if self.websocket_manager:
                    await self.websocket_manager.send_json(state["client_id"], {
                        "type": "architecture_proposal_revised",
                        "proposal": revised_proposal,
                        "content": formatted_msg,  # v5.8.1: use 'content' for consistency
                        "session_id": state.get("session_id"),
                        "metadata": {
                            "waiting_for_approval": True,
                            "approval_type": "architecture_proposal"
                        }
                    })

                logger.info("📋 Revised proposal sent to user")
                return state

            # ============================================================
            # v5.2.0: PHASE 2 - No proposal yet → Do research & create proposal
            # ============================================================
            if not state.get("architecture_proposal"):
                logger.info("📋 No proposal exists - performing research and creating proposal")

                # v5.8.1: Send thinking message
                await self._send_agent_activity(
                    state,
                    "thinking",
                    "architect",
                    content="Analyzing requirements and researching best practices..."
                )

                # Step 1: Do research (existing behavior)
                research_result = await self._execute_architect_task(state, current_step)
                logger.info(f"🔍 Research completed: {research_result[:200]}...")

                # v5.8.1: Send progress message
                await self._send_agent_activity(
                    state,
                    "progress",
                    "architect",
                    content="Creating architecture proposal..."
                )

                # Step 2: Create proposal based on research
                proposal = await self._create_architecture_proposal(state, research_result)
                state["architecture_proposal"] = proposal
                state["proposal_status"] = "pending"
                state["needs_approval"] = True
                state["approval_type"] = "architecture_proposal"

                # Step 3: Format for user
                formatted_msg = self._format_proposal_for_user(proposal)

                # Step 4: Send to user
                state["messages"].append({
                    "role": "assistant",
                    "content": formatted_msg,
                    "type": "architecture_proposal",
                    "proposal": proposal
                })

                # Send as regular chat message so user sees it
                if self.websocket_manager:
                    logger.info(f"🔌 WebSocket DEBUG: Sending architecture proposal to client_id: {state.get('client_id')}")
                    logger.info(f"🔌 WebSocket DEBUG: Session ID: {state.get('session_id')}")
                    logger.info(f"🔌 WebSocket DEBUG: Proposal size: {len(str(proposal))} chars")

                    # Send as architecture_proposal (v5.8.1 fix: UI expects this type!)
                    message_to_send = {
                        "type": "architecture_proposal",
                        "agent": "architect",
                        "content": formatted_msg,
                        "proposal": proposal,
                        "session_id": state.get("session_id"),
                        "metadata": {
                            "waiting_for_approval": True,
                            "approval_type": "architecture_proposal"
                        }
                    }

                    try:
                        await self.websocket_manager.send_json(state["client_id"], message_to_send)
                        logger.info("✅ WebSocket DEBUG: Architecture proposal sent successfully")

                        # Mark in state that we're waiting for chat approval
                        state["waiting_for_chat_approval"] = True

                        # Store in active workflows for later retrieval
                        if not hasattr(self.websocket_manager, 'active_workflows'):
                            self.websocket_manager.active_workflows = {}
                        self.websocket_manager.active_workflows[state.get("session_id")] = state
                        logger.info(f"📝 WebSocket DEBUG: Stored state in websocket_manager.active_workflows for session: {state.get('session_id')}")
                    except Exception as e:
                        logger.error(f"❌ WebSocket DEBUG: Failed to send proposal: {e}")
                        import traceback
                        logger.error(f"📍 Traceback: {traceback.format_exc()}")
                else:
                    logger.warning("⚠️ WebSocket DEBUG: No websocket_manager available!")

                # Update step status to pending (waiting for approval)
                current_step.status = "in_progress"
                state["execution_plan"] = list(state["execution_plan"])

                # Store research in memory
                memory.store_memory(
                    content=f"Architecture research: {current_step.task}",
                    memory_type="procedural",
                    importance=0.7,
                    metadata={"research": research_result[:500], "proposal_created": True},
                    session_id=state.get("session_id")
                )

                logger.info("📋 Architecture proposal created and sent to user")
                return state

            # ============================================================
            # FALLBACK: Should not reach here
            # ============================================================
            logger.warning("⚠️ Unexpected architect_node state - falling back to old behavior")
            result = await self._execute_architect_task(state, current_step)
            current_step.result = result
            current_step.status = "completed"
            state["execution_plan"] = list(state["execution_plan"])

            memory.store_memory(
                content=f"Architecture design: {current_step.task}",
                memory_type="procedural",
                importance=0.8,
                metadata={"result": result},
                session_id=state.get("session_id")
            )

        except Exception as e:
            logger.error(f"❌ Architect execution failed: {e}", exc_info=True)
            current_step.status = "failed"
            current_step.error = str(e)
            state["errors"].append({
                "agent": "architect",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
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

        # v5.2.2 BUG FIX #6: Find in_progress step for THIS agent
        # (routing functions can't modify state, so current_step_id is unreliable)
        current_step = next(
            (s for s in state["execution_plan"] if s.agent == "codesmith" and s.status == "in_progress"),
            None
        )
        if not current_step:
            logger.error("❌ No in_progress codesmith step found!")
            return state

        logger.info(f"💻 Executing step {current_step.id}: {current_step.task[:100]}...")

        # v5.8.1: Send thinking message
        await self._send_agent_activity(
            state,
            "thinking",
            "codesmith",
            content=f"Implementing: {current_step.task[:100]}..."
        )

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
            logger.info(f"✅ CodeSmith node set step {current_step.id} to completed")

            # v5.8.1: Send completion message
            await self._send_agent_activity(
                state,
                "complete",
                "codesmith",
                content=f"✅ Implementation completed"
            )

            # ✅ FIX: Create NEW list to trigger LangGraph state update
            state["execution_plan"] = list(state["execution_plan"])
            logger.info(f"✅ CodeSmith node updated execution_plan state")

            # 🔍 ANALYZE RESULT: Check if research needed
            # TODO: Enable when research_node is implemented
            # result_text = str(result).lower()
            # needs_research = any(keyword in result_text for keyword in [
            #     "need more information", "requires research", "unclear",
            #     "need to research", "look up", "find documentation",
            #     "need details about", "requires additional information"
            # ])
            #
            # if needs_research:
            #     logger.warning("📚 CodeSmith needs additional research - requesting ResearchBot collaboration")
            #     state["needs_replan"] = True
            #     state["suggested_agent"] = "research"
            #     state["suggested_query"] = f"Research information needed for: {current_step.task[:150]}"
            #     logger.info(f"  🔄 Set needs_replan=True, suggested_agent=research")
            needs_research = False  # Disabled until research_node implemented

            # Store code pattern
            memory.store_memory(
                content=f"Generated code for: {current_step.task}",
                memory_type="procedural",
                importance=0.7,
                metadata={"code_size": len(str(result)), "needs_research": needs_research},
                session_id=state.get("session_id")
            )

        except Exception as e:
            logger.error(f"CodeSmith execution failed: {e}")
            current_step.status = "failed"
            current_step.error = str(e)
            # ✅ FIX: Create NEW list even on failure
            state["execution_plan"] = list(state["execution_plan"])

        return state

    async def reviewer_node(self, state: ExtendedAgentState) -> ExtendedAgentState:
        """
        Reviewer agent node - code review and validation
        """
        logger.info("🔎 Reviewer node executing")
        state["current_agent"] = "reviewer"

        memory = self.agent_memories["reviewer"]

        # v5.2.2 BUG FIX #6: Find in_progress step for THIS agent
        current_step = next(
            (s for s in state["execution_plan"] if s.agent == "reviewer" and s.status == "in_progress"),
            None
        )
        if not current_step:
            logger.error("❌ No in_progress reviewer step found!")
            return state

        logger.info(f"🔎 Executing step {current_step.id}: {current_step.task[:100]}...")

        try:
            # Perform review
            review_result = await self._execute_reviewer_task(state, current_step)
            current_step.result = review_result
            current_step.status = "completed"

            # ✅ FIX: Create NEW list to trigger LangGraph state update
            state["execution_plan"] = list(state["execution_plan"])

            # 🔍 ANALYZE REVIEW: Check if critical issues found
            review_text = str(review_result).lower() if isinstance(review_result, str) else str(review_result.get("review", "")).lower()
            has_critical_issues = any(keyword in review_text for keyword in [
                "critical", "bug", "error", "vulnerability", "security issue",
                "fix needed", "must fix", "requires fix", "issue found"
            ])

            if has_critical_issues:
                logger.warning("⚠️ Critical issues found in review - requesting FixerBot collaboration")
                state["needs_replan"] = True
                state["suggested_agent"] = "fixer"
                state["suggested_query"] = f"Fix the issues found in code review: {review_text[:200]}"
                logger.info(f"  🔄 Set needs_replan=True, suggested_agent=fixer")

            # Store review patterns
            if isinstance(review_result, dict) and review_result.get("issues"):
                for issue in review_result["issues"]:
                    memory.store_memory(
                        content=f"Found issue: {issue}",
                        memory_type="semantic",
                        importance=0.8 if has_critical_issues else 0.6,
                        session_id=state.get("session_id")
                    )
            else:
                # Store text review
                memory.store_memory(
                    content=f"Code review: {current_step.task}",
                    memory_type="episodic",
                    importance=0.8 if has_critical_issues else 0.6,
                    metadata={"review": review_result, "has_critical_issues": has_critical_issues},
                    session_id=state.get("session_id")
                )

        except Exception as e:
            logger.error(f"Reviewer execution failed: {e}")
            current_step.status = "failed"
            current_step.error = str(e)
            # ✅ FIX: Create NEW list even on failure
            state["execution_plan"] = list(state["execution_plan"])

        return state

    async def fixer_node(self, state: ExtendedAgentState) -> ExtendedAgentState:
        """
        Fixer agent node - bug fixing and optimization
        """
        logger.info("🔧 Fixer node executing")
        state["current_agent"] = "fixer"

        memory = self.agent_memories["fixer"]

        # v5.2.2 BUG FIX #6: Find in_progress step for THIS agent
        current_step = next(
            (s for s in state["execution_plan"] if s.agent == "fixer" and s.status == "in_progress"),
            None
        )
        if not current_step:
            logger.error("❌ No in_progress fixer step found!")
            return state

        logger.info(f"🔧 Executing step {current_step.id}: {current_step.task[:100]}...")

        # Get previous review results
        review_step = self._get_step_by_agent(state, "reviewer")
        # Handle both dict and string results from reviewer
        if review_step and review_step.result:
            if isinstance(review_step.result, dict):
                issues = review_step.result.get("issues", [])
            else:
                # If result is a string, treat it as a single issue
                issues = [{"description": str(review_step.result), "severity": "unknown"}]
        else:
            issues = []

        try:
            # Fix issues
            fix_result = await self._execute_fixer_task(state, current_step, issues)
            current_step.result = fix_result
            current_step.status = "completed"

            # ✅ FIX: Create NEW list to trigger LangGraph state update
            state["execution_plan"] = list(state["execution_plan"])

            # Learn fix patterns
            # v5.5.3: Handle both dict and string fix_result
            fixes = []
            if isinstance(fix_result, dict):
                fixes = fix_result.get("fixes", [])
            # If fix_result is a string, skip pattern learning (no structured fixes to learn from)

            for issue, fix in zip(issues, fixes):
                memory.learn_pattern(
                    pattern=issue,
                    solution=fix,
                    success=True
                )

        except Exception as e:
            logger.error(f"Fixer execution failed: {e}")
            current_step.status = "failed"
            current_step.error = str(e)
            # ✅ FIX: Create NEW list even on failure
            state["execution_plan"] = list(state["execution_plan"])

        return state

    async def research_node(self, state: ExtendedAgentState) -> ExtendedAgentState:
        """
        Research agent node - information gathering using Perplexity
        v5.1.0: Key part of information-first escalation
        """
        logger.info("🔍 Research node executing")
        state["current_agent"] = "research"

        # v5.2.2 BUG FIX #6: Find in_progress step for THIS agent
        current_step = next(
            (s for s in state["execution_plan"] if s.agent == "research" and s.status == "in_progress"),
            None
        )
        if not current_step:
            logger.error("❌ No in_progress research step found!")
            return state

        logger.info(f"🔍 Executing step {current_step.id}: {current_step.task[:100]}...")

        try:
            # Get research query from task
            research_query = current_step.task

            # Execute research using ResearchAgent
            if RESEARCH_AVAILABLE and "research" in self.real_agents:
                research_agent = self.real_agents["research"]

                task_request = TaskRequest(
                    prompt=research_query,
                    context={"session_id": state["session_id"]}
                )

                result = await research_agent.execute(task_request)
                research_result = result.content

                logger.info(f"✅ Research completed: {len(research_result)} characters")
            else:
                # Fallback if research not available
                logger.warning("⚠️ ResearchAgent not available - using placeholder")
                research_result = f"Research placeholder for: {research_query}"

            # Store result
            current_step.result = research_result
            current_step.status = "completed"
            state["execution_plan"] = list(state["execution_plan"])

            # Track research in information_gathered
            info_gathered = list(state.get("information_gathered", []))
            info_gathered.append({
                "level": state.get("escalation_level", 0),
                "query": research_query,
                "result": research_result,
                "summary": research_result[:200],
                "timestamp": datetime.now().isoformat()
            })
            state["information_gathered"] = info_gathered

            logger.info(f"📚 Information gathered: {len(info_gathered)} total research results")

        except Exception as e:
            logger.error(f"Research execution failed: {e}")
            current_step.status = "failed"
            current_step.error = str(e)
            state["execution_plan"] = list(state["execution_plan"])

        return state

    async def fixer_gpt_node(self, state: ExtendedAgentState) -> ExtendedAgentState:
        """
        Alternative Fixer node using GPT (v5.1.0)
        Provides fresh perspective when Claude FixerBot fails
        """
        logger.info("🔧🔄 FixerGPT node executing (ALTERNATIVE FIXER)")
        state["current_agent"] = "fixer_gpt"

        # v5.2.2 BUG FIX #6: Find in_progress step for THIS agent
        current_step = next(
            (s for s in state["execution_plan"] if s.agent == "fixer_gpt" and s.status == "in_progress"),
            None
        )
        if not current_step:
            logger.error("❌ No in_progress fixer_gpt step found!")
            return state

        logger.info(f"🔧 Executing step {current_step.id}: {current_step.task[:100]}...")

        try:
            # Import FixerGPTAgent
            from agents.specialized.fixer_gpt_agent import FixerGPTAgent

            # Get context for alternative fixer
            previous_attempts = [
                h for h in state.get("collaboration_history", [])
                if h.get("to") in ["fixer", "fixer_gpt"]
            ]
            research_results = state.get("information_gathered", [])

            # Initialize FixerGPT
            fixer_gpt = FixerGPTAgent()

            # Execute with full context
            task_request = TaskRequest(
                prompt=current_step.task,
                context={
                    "previous_attempts": previous_attempts,
                    "research_results": research_results,
                    "issue": current_step.task,
                    "session_id": state["session_id"],
                    "workspace_path": state["workspace_path"]
                }
            )

            result = await fixer_gpt.execute(task_request)
            fix_result = result.content

            logger.info(f"✅ FixerGPT completed: {len(fix_result)} characters")

            # Store result
            current_step.result = fix_result
            current_step.status = "completed"
            state["execution_plan"] = list(state["execution_plan"])

            # Request re-review
            state["needs_replan"] = True
            state["suggested_agent"] = "reviewer"
            state["suggested_query"] = f"Re-review after FixerGPT fix: {fix_result[:100]}"

            logger.info("🔄 Requesting re-review after FixerGPT")

        except Exception as e:
            logger.error(f"FixerGPT execution failed: {e}")
            current_step.status = "failed"
            current_step.error = str(e)
            state["execution_plan"] = list(state["execution_plan"])

        return state

    async def docbot_node(self, state: ExtendedAgentState) -> ExtendedAgentState:
        """
        DocBot node - generates documentation
        """
        logger.info("📚 DocBot node executing")
        state["current_agent"] = "docbot"

        # v5.2.2 BUG FIX #6: Find in_progress step for THIS agent
        current_step = next(
            (s for s in state["execution_plan"] if s.agent == "docbot" and s.status == "in_progress"),
            None
        )
        if not current_step:
            logger.error("❌ No in_progress docbot step found!")
            return state

        logger.info(f"📚 Executing step {current_step.id}: {current_step.task[:100]}...")

        try:
            # Check if real agent is available
            if "docbot" in self.real_agents:
                agent = self.real_agents["docbot"]

                # Get context from previous steps
                code_context = []
                for step in state["execution_plan"]:
                    if step.status == "completed" and step.agent in ["codesmith", "fixer", "fixer_gpt"]:
                        code_context.append(step.result)

                # Create task request
                task_request = TaskRequest(
                    prompt=current_step.task,
                    context={
                        "code_context": code_context,
                        "session_id": state["session_id"],
                        "workspace_path": state["workspace_path"],
                        "collaboration_history": state.get("collaboration_history", [])
                    }
                )

                # Execute documentation generation
                result = await agent.execute(task_request)
                doc_result = result.content

                logger.info(f"✅ DocBot completed: {len(doc_result)} characters")

                # Store result
                current_step.result = doc_result
                current_step.status = "completed"
                state["execution_plan"] = list(state["execution_plan"])

                # Add to collaboration history
                state["collaboration_history"].append({
                    "from": "docbot",
                    "to": current_step.dependencies[0] if current_step.dependencies else "orchestrator",
                    "message": doc_result,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                # Fallback to stub
                logger.warning("⚠️ DocBot agent not available - using stub")
                current_step.result = "📚 Documentation stub: Would generate comprehensive docs here"
                current_step.status = "completed"
                state["execution_plan"] = list(state["execution_plan"])

        except Exception as e:
            logger.error(f"DocBot execution failed: {e}")
            current_step.status = "failed"
            current_step.error = str(e)
            state["execution_plan"] = list(state["execution_plan"])

        return state

    async def performance_node(self, state: ExtendedAgentState) -> ExtendedAgentState:
        """
        Performance node - optimizes code performance
        """
        logger.info("⚡ Performance node executing")
        state["current_agent"] = "performance"

        # v5.2.2 BUG FIX #6: Find in_progress step for THIS agent
        current_step = next(
            (s for s in state["execution_plan"] if s.agent == "performance" and s.status == "in_progress"),
            None
        )
        if not current_step:
            logger.error("❌ No in_progress performance step found!")
            return state

        logger.info(f"⚡ Executing step {current_step.id}: {current_step.task[:100]}...")

        try:
            # Check if real agent is available
            if "performance" in self.real_agents:
                agent = self.real_agents["performance"]

                # Get code to optimize
                code_to_optimize = []
                for step in state["execution_plan"]:
                    if step.status == "completed" and step.agent in ["codesmith", "fixer", "fixer_gpt"]:
                        code_to_optimize.append(step.result)

                # Create task request
                task_request = TaskRequest(
                    prompt=current_step.task,
                    context={
                        "code_to_optimize": code_to_optimize,
                        "session_id": state["session_id"],
                        "workspace_path": state["workspace_path"],
                        "performance_metrics": state.get("performance_metrics", {})
                    }
                )

                # Execute performance optimization
                result = await agent.execute(task_request)
                perf_result = result.content

                logger.info(f"✅ Performance optimization completed: {len(perf_result)} characters")

                # Store result
                current_step.result = perf_result
                current_step.status = "completed"
                state["execution_plan"] = list(state["execution_plan"])

                # Add to collaboration history
                state["collaboration_history"].append({
                    "from": "performance",
                    "to": current_step.dependencies[0] if current_step.dependencies else "orchestrator",
                    "message": perf_result,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                # Fallback to stub
                logger.warning("⚠️ Performance agent not available - using stub")
                current_step.result = "⚡ Performance stub: Would optimize performance here"
                current_step.status = "completed"
                state["execution_plan"] = list(state["execution_plan"])

        except Exception as e:
            logger.error(f"Performance optimization failed: {e}")
            current_step.status = "failed"
            current_step.error = str(e)
            state["execution_plan"] = list(state["execution_plan"])

        return state

    async def tradestrat_node(self, state: ExtendedAgentState) -> ExtendedAgentState:
        """
        TradeStrat node - develops trading strategies
        """
        logger.info("📈 TradeStrat node executing")
        state["current_agent"] = "tradestrat"

        # v5.2.2 BUG FIX #6: Find in_progress step for THIS agent
        current_step = next(
            (s for s in state["execution_plan"] if s.agent == "tradestrat" and s.status == "in_progress"),
            None
        )
        if not current_step:
            logger.error("❌ No in_progress tradestrat step found!")
            return state

        logger.info(f"📈 Executing step {current_step.id}: {current_step.task[:100]}...")

        try:
            # Check if real agent is available
            if "tradestrat" in self.real_agents:
                agent = self.real_agents["tradestrat"]

                # Get market data and research results
                research_results = state.get("information_gathered", [])
                market_context = {
                    "research": research_results,
                    "requirements": current_step.task
                }

                # Create task request
                task_request = TaskRequest(
                    prompt=current_step.task,
                    context={
                        "market_context": market_context,
                        "session_id": state["session_id"],
                        "workspace_path": state["workspace_path"],
                        "trading_parameters": state.get("trading_parameters", {})
                    }
                )

                # Execute strategy development
                result = await agent.execute(task_request)
                strategy_result = result.content

                logger.info(f"✅ Trading strategy developed: {len(strategy_result)} characters")

                # Store result
                current_step.result = strategy_result
                current_step.status = "completed"
                state["execution_plan"] = list(state["execution_plan"])

                # Add to collaboration history
                state["collaboration_history"].append({
                    "from": "tradestrat",
                    "to": current_step.dependencies[0] if current_step.dependencies else "orchestrator",
                    "message": strategy_result,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                # Fallback to stub
                logger.warning("⚠️ TradeStrat agent not available - using stub")
                current_step.result = "📈 Trading strategy stub: Would develop strategy here"
                current_step.status = "completed"
                state["execution_plan"] = list(state["execution_plan"])

        except Exception as e:
            logger.error(f"Trading strategy development failed: {e}")
            current_step.status = "failed"
            current_step.error = str(e)
            state["execution_plan"] = list(state["execution_plan"])

        return state

    async def opus_arbitrator_node(self, state: ExtendedAgentState) -> ExtendedAgentState:
        """
        OpusArbitrator node - resolves conflicts between agents
        """
        logger.info("⚖️ OpusArbitrator node executing")
        state["current_agent"] = "opus_arbitrator"

        # v5.2.2 BUG FIX #6: Find in_progress step for THIS agent
        current_step = next(
            (s for s in state["execution_plan"] if s.agent == "opus_arbitrator" and s.status == "in_progress"),
            None
        )
        if not current_step:
            logger.error("❌ No in_progress opus_arbitrator step found!")
            return state

        logger.info(f"⚖️ Executing step {current_step.id}: {current_step.task[:100]}...")

        try:
            # Check if real agent is available
            if "opus_arbitrator" in self.real_agents:
                agent = self.real_agents["opus_arbitrator"]

                # Gather all conflicting opinions
                conflicts = []
                for hist in state.get("collaboration_history", [])[-10:]:  # Last 10 interactions
                    if hist.get("from") in ["reviewer", "fixer", "architect", "codesmith"]:
                        conflicts.append({
                            "agent": hist["from"],
                            "opinion": hist["message"][:500]  # First 500 chars
                        })

                # Create task request
                task_request = TaskRequest(
                    prompt=current_step.task,
                    context={
                        "conflicts": conflicts,
                        "session_id": state["session_id"],
                        "workspace_path": state["workspace_path"],
                        "escalation_level": state.get("escalation_level", 0),
                        "collaboration_count": state.get("collaboration_count", 0)
                    }
                )

                # Execute arbitration
                result = await agent.execute(task_request)
                arbitration_result = result.content

                logger.info(f"✅ Arbitration completed: {len(arbitration_result)} characters")

                # Store result
                current_step.result = arbitration_result
                current_step.status = "completed"
                state["execution_plan"] = list(state["execution_plan"])

                # Add to collaboration history
                state["collaboration_history"].append({
                    "from": "opus_arbitrator",
                    "to": "orchestrator",  # Usually goes back to orchestrator for re-planning
                    "message": arbitration_result,
                    "timestamp": datetime.now().isoformat()
                })

                # Set re-planning flag based on arbitration result
                if "REPLAN" in arbitration_result or "REDESIGN" in arbitration_result:
                    state["needs_replan"] = True
                    state["replan_reason"] = "OpusArbitrator recommended re-planning"
            else:
                # Fallback to stub
                logger.warning("⚠️ OpusArbitrator agent not available - using stub")
                current_step.result = "⚖️ Arbitration stub: Would resolve conflicts here"
                current_step.status = "completed"
                state["execution_plan"] = list(state["execution_plan"])

        except Exception as e:
            logger.error(f"Arbitration failed: {e}")
            current_step.status = "failed"
            current_step.error = str(e)
            state["execution_plan"] = list(state["execution_plan"])

        return state

    async def route_after_approval(self, state: ExtendedAgentState) -> str:
        """
        Route after approval node - intelligently routes to first pending agent
        Validates that the agent has a workflow node, fallback to orchestrator if not
        """
        # Available workflow nodes (agents with implemented nodes)
        AVAILABLE_NODES = {
            "orchestrator", "architect", "codesmith", "reviewer", "fixer",
            "research", "fixer_gpt", "docbot", "performance", "tradestrat", "opus_arbitrator"
        }

        # v5.2.0: Check if waiting for architecture approval
        if state.get("status") == "waiting_architecture_approval":
            logger.info("⏸️  Workflow waiting for architecture approval - routing to END")
            return "end"

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

    async def route_from_architect(self, state: ExtendedAgentState) -> str:
        """
        v5.2.0: Special routing for architect node
        Routes to approval_node if architecture proposal was just created
        Otherwise uses standard route_to_next_agent logic
        """
        # Check if we just created an architecture proposal that needs approval
        if state.get("needs_approval") and state.get("approval_type") == "architecture_proposal":
            proposal_status = state.get("proposal_status")

            if proposal_status == "pending":
                # Just created proposal - route to approval node
                logger.info("🏛️ Architecture proposal created - routing to approval node")
                return "approval"
            elif proposal_status == "approved":
                # Proposal was approved - mark step as completed and continue
                logger.info("✅ Architecture proposal approved - marking step complete")
                for step in state["execution_plan"]:
                    if step.agent == "architect" and step.status == "in_progress":
                        step.status = "completed"
                        step.result = "Architecture proposal approved by user"
                        state["execution_plan"] = list(state["execution_plan"])
                        break
                # Continue with standard routing
                return await self.route_to_next_agent(state)

        # Standard routing for non-proposal cases
        return await self.route_to_next_agent(state)

    async def route_to_next_agent(self, state: ExtendedAgentState) -> str:
        """
        Determine next agent based on execution plan
        Validates that the agent has a workflow node, fallback to orchestrator if not
        v5.5.3: Made async to support background tasks
        """
        # Available workflow nodes (agents with implemented nodes)
        AVAILABLE_NODES = {
            "orchestrator", "architect", "codesmith", "reviewer", "fixer",
            "research", "fixer_gpt", "docbot", "performance", "tradestrat", "opus_arbitrator"
        }

        logger.info(f"🔀 Routing to next agent...")
        logger.info(f"📋 Execution plan has {len(state['execution_plan'])} steps")

        # v5.4.3: Check for timeouts first
        asyncio.create_task(self.check_and_handle_timeouts(state))

        # v5.4.3: Update progress ledger
        if state.get("progress_ledger"):
            state["progress_ledger"].update_from_steps(state["execution_plan"])
            progress = state["progress_ledger"]
            logger.info(f"📊 Progress: {progress.completed_steps}/{progress.total_steps} ({progress.overall_progress_percentage:.1f}%)")

        # v5.5.0: Real-time health monitoring
        if self.self_diagnosis and state.get("collaboration_count", 0) % 5 == 0:
            # Check health every 5 collaborations
            async def run_health_check():
                try:
                    health_report = await self.self_diagnosis.real_time_monitoring(state)
                    if health_report["overall_health"] in ["CRITICAL", "UNHEALTHY"]:
                        logger.error(f"🚨 Workflow health is {health_report['overall_health']}")
                        logger.error(f"   Risk factors: {health_report.get('recommendations', [])}")
                except Exception as e:
                    logger.warning(f"Health monitoring error: {e}")

            # Run health check in background
            asyncio.create_task(run_health_check())

        # 🔄 CHECK 1: Agent collaboration/re-planning needed?
        if state.get("needs_replan"):
            logger.info("🔄 Re-planning needed - routing back to orchestrator")
            return "orchestrator"

        # 🐛 CHECK 2: Any steps still in_progress? (validation only)
        # If a step is in_progress, it means the node is currently executing
        # We should NOT route back to it - instead wait for it to complete
        has_in_progress = any(s.status == "in_progress" for s in state["execution_plan"])
        if has_in_progress:
            logger.warning("⚠️ Found in_progress steps!")
            for step in state["execution_plan"]:
                if step.status == "in_progress":
                    logger.warning(f"  📍 Step {step.id} ({step.agent}) is in_progress")
            # Don't route back - let the current node finish
            # Continue to check for pending steps

        # CHECK 3: Find next pending step
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
                    # v5.4.3: Track execution start time for timeout management
                    step.started_at = datetime.now()
                    step.start_time = datetime.now()  # Also set start_time for compatibility
                    state["current_step_id"] = step.id
                    logger.info(f"✅ Routing to {agent} for step {step.id}")
                    return agent
                else:
                    logger.info(f"⏸️ Step {step.id} waiting for dependencies")

        # v5.2.2 BUG FIX #8: Check for stuck in_progress steps before declaring "complete"
        stuck_steps = [s for s in state["execution_plan"] if s.status == "in_progress"]
        if stuck_steps:
            logger.error("❌ CRITICAL: Found in_progress steps but no more routing possible!")
            logger.error("   This indicates a step failed to mark itself as completed.")
            for step in stuck_steps:
                logger.error(f"   ⚠️ Stuck step: {step.id} ({step.agent}): {step.task[:100]}")
                # Force mark as failed
                step.status = "failed"
                step.error = "Step execution completed but status was not updated to 'completed'"
            state["execution_plan"] = list(state["execution_plan"])
            # Now check if there are any more pending steps
            has_pending = any(s.status == "pending" for s in state["execution_plan"])
            if has_pending:
                # Recurse to route to next pending step
                logger.info("🔄 Retrying routing after fixing stuck steps...")
                return await self.route_to_next_agent(state)

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

    def _check_escalation_needed(
        self,
        state: ExtendedAgentState,
        suggested_agent: str,
        suggested_query: str
    ) -> Dict[str, Any]:
        """
        v5.1.0: Information-First Escalation System

        Check if escalation is needed based on collaboration count.
        Returns escalation decision with new agent/query if needed.

        Levels:
        0-1: Normal retries (1-4 iterations)
        2: BROAD research (5-6 iterations)
        3: TARGETED research (7-8 iterations)
        4: ALTERNATIVE approach (9-10 iterations)
        4.5: ALTERNATIVE FIXER KI (11-12 iterations)
        5: USER QUESTION (13+ iterations)
        6: OPUS ARBITRATOR (if user approved)
        7: HUMAN (final)
        """
        try:
            from config.settings import Settings
        except ImportError:
            # Fallback for different import contexts
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from config.settings import Settings

        collab_count = state.get("collaboration_count", 0)
        rf_cycles = state.get("reviewer_fixer_cycles", 0)
        last_agents = state.get("last_collaboration_agents", [])

        # Check for Reviewer↔Fixer loop pattern
        is_rf_loop = (
            suggested_agent in ["reviewer", "fixer"] and
            len(last_agents) >= 4 and
            (last_agents[-4:] == ["reviewer", "fixer", "reviewer", "fixer"] or
             last_agents[-4:] == ["fixer", "reviewer", "fixer", "reviewer"])
        )

        # LEVEL 0-1: Normal retries (1-4 iterations)
        if collab_count <= 4:
            return {
                "escalate": False,
                "level": 0,
                "new_agent": suggested_agent,
                "new_query": suggested_query,
                "reason": "Normal operation"
            }

        # LEVEL 2: BROAD research (5-6 iterations)
        if 5 <= collab_count <= 6 and is_rf_loop:
            research_query = f"""Research how to solve this type of issue:

Issue: {suggested_query[:300]}

Find:
1. Best practices for this issue type
2. Common solutions with code examples
3. Official documentation references
4. Known pitfalls to avoid

Focus on practical, working solutions."""

            return {
                "escalate": True,
                "level": 2,
                "new_agent": "research",
                "new_query": research_query,
                "reason": "Broad information gathering - general best practices"
            }

        # LEVEL 3: TARGETED research (7-8 iterations)
        if 7 <= collab_count <= 8 and rf_cycles >= 3:
            # Get error details from history
            history = state.get("collaboration_history", [])
            failed_fixes = [h for h in history if h.get("to") == "fixer"][-3:]

            research_query = f"""Deep-dive research for SPECIFIC solution:

Problem: {suggested_query[:200]}

Previous failed attempts:
{chr(10).join(f"- Attempt {i+1}: {h.get('query', 'unknown')[:80]}..." for i, h in enumerate(failed_fixes))}

Find SPECIFICALLY:
1. Solutions for this EXACT error/issue
2. GitHub issues or Stack Overflow with this problem
3. Working code examples for THIS specific case
4. Version-specific fixes or migrations"""

            return {
                "escalate": True,
                "level": 3,
                "new_agent": "research",
                "new_query": research_query,
                "reason": "Targeted information gathering - specific solutions"
            }

        # LEVEL 4: ALTERNATIVE approach (9-10 iterations)
        if 9 <= collab_count <= 10 and rf_cycles >= 4:
            research_query = f"""DIAGNOSTIC research - Is current approach correct?

Current approach (failing): {suggested_query[:200]}

Research:
1. Is this implementation approach fundamentally correct?
2. What alternative approaches exist for this problem?
3. Are there known issues with the current approach?
4. What do experts/docs recommend for this scenario?
5. Should we re-implement with different architecture?"""

            return {
                "escalate": True,
                "level": 4,
                "new_agent": "research",
                "new_query": research_query,
                "reason": "Alternative approach research - rethink strategy"
            }

        # LEVEL 4.5: ALTERNATIVE FIXER KI (11-12 iterations)
        if 11 <= collab_count <= 12:
            # Check if alternative fixer enabled
            if not Settings.ALTERNATIVE_FIXER_ENABLED:
                logger.info("⚠️ Alternative Fixer disabled - skipping to next level")
                collab_count = 13  # Force to Level 5

            # Check if we already tried alternative fixer
            tried_fixer_gpt = any(
                h.get("to") == "fixer_gpt"
                for h in state.get("collaboration_history", [])
            )

            if not tried_fixer_gpt and Settings.ALTERNATIVE_FIXER_ENABLED:
                return {
                    "escalate": True,
                    "level": 4.5,
                    "new_agent": "fixer_gpt",
                    "new_query": f"Fix with alternative AI perspective: {suggested_query}",
                    "reason": f"Alternative Fixer KI ({Settings.ALTERNATIVE_FIXER_MODEL}) - fresh perspective"
                }

        # LEVEL 5: Safety net - max iterations
        max_iterations = getattr(Settings, 'LANGGRAPH_MAX_ITERATIONS', 20)
        if collab_count >= max_iterations:
            logger.error(f"🚨 SAFETY STOP: {collab_count} collaborations exceeds max {max_iterations}")
            return {
                "escalate": True,
                "level": 7,
                "new_agent": "end",
                "new_query": f"Exceeded maximum iterations ({max_iterations})",
                "reason": "Safety net - preventing infinite loop"
            }

        # DEFAULT: No escalation
        return {
            "escalate": False,
            "level": 0,
            "new_agent": suggested_agent,
            "new_query": suggested_query,
            "reason": "Normal operation"
        }

    async def _create_execution_plan(self, state: ExtendedAgentState) -> List[ExecutionStep]:
        """
        Create execution plan based on task

        Phase 2: HYBRID ROUTING
        - Simple tasks → Keyword routing (fast)
        - Complex tasks → Orchestrator AI decomposition (intelligent)
        - Moderate tasks → Standard workflow patterns

        v5.5.2: Enhanced with Safe Orchestrator Executor
        """
        task = state.get("current_task", "")

        # ============================================
        # v5.5.2: SAFE ORCHESTRATOR EXECUTION CHECK
        # ============================================
        if self.safe_executor and self.safe_executor.should_use_safe_execution(task, state):
            logger.info("🛡️ Using Safe Orchestrator Executor (v5.5.2)")

            # Create safe execution plan without actual orchestrator call
            try:
                safe_plan = await self.safe_executor.create_safe_execution_plan(task, state)
                if safe_plan:
                    logger.info(f"✅ Created safe execution plan with {len(safe_plan)} steps")
                    return safe_plan
            except Exception as e:
                logger.error(f"Safe executor failed: {e}, falling back to standard routing")

        # ============================================
        # PHASE 2: AI-BASED ROUTING (Fast routing disabled)
        # ============================================
        # Complexity detection removed - all tasks go through AI
        # This ensures consistent, intelligent routing without keyword matching

        # v5.5.2: Check for problematic queries that need special handling
        if self.query_classifier:
            classification = self.query_classifier.classify_query(task, state)

            # Handle special query types
            if classification.is_greeting:
                logger.info("👋 Greeting detected - returning friendly response")
                return [ExecutionStep(
                    id="step1",
                    agent="orchestrator",
                    task="Greeting",
                    expected_output="Greeting response",
                    dependencies=[],
                    status="completed",
                    result=classification.prefilled_response or "Hallo! Ich bin der KI AutoAgent. Wie kann ich Ihnen bei der Entwicklung helfen?"
                )]

            if classification.is_nonsense:
                logger.info("❓ Nonsensical query detected - asking for clarification")
                return [ExecutionStep(
                    id="step1",
                    agent="orchestrator",
                    task="Clarification needed",
                    expected_output="Clarification request",
                    dependencies=[],
                    status="completed",
                    result=classification.prefilled_response or "Könnten Sie Ihre Anfrage bitte umformulieren?"
                )]

            # Handle development queries with special handlers
            # BUT: Only for VAGUE queries, not concrete implementation requests!
            is_concrete_request = any(word in task.lower() for word in [
                'erstelle', 'create', 'build', 'implement', 'baue', 'entwickle',
                'generiere', 'generate', 'make', 'code'
            ])

            if classification.is_development_query and classification.dev_type and self.dev_handler and not is_concrete_request:
                # Only provide guidance for vague requests like "make it faster" or "fix bugs"
                response, agents = self.dev_handler.handle_development_query(
                    task, classification.dev_type, state
                )
                if not agents:  # No agents needed, just return informative response
                    return [ExecutionStep(
                        id="step1",
                        agent="orchestrator",
                        task=f"Development guidance for {classification.dev_type}",
                        expected_output="Development guidance",
                        dependencies=[],
                        status="completed",
                        result=response
                    )]

        # ============================================
        # SKIP FAST ROUTING - GO DIRECTLY TO AI
        # ============================================
        # User requested: "Nur hierfür deaktivieren" (fast routing for simple tasks)
        # We keep SafeExecutor and QueryClassifier but skip keyword-based routing

        if ORCHESTRATOR_AVAILABLE:
            logger.info("🧠 DIRECT AI ROUTING → Using Orchestrator for all tasks")
            # Always treat as "complex" since we want full AI analysis
            orchestrator_plan = await self._use_orchestrator_for_planning(task, "complex")
            if orchestrator_plan and len(orchestrator_plan) > 0:
                return orchestrator_plan

        # Fallback to intelligent handler
        if self.intelligent_handler:
            logger.info("🧠 Using Intelligent Query Handler")
            return self.intelligent_handler.create_intelligent_execution_plan(task)

        # Ultimate fallback
        return self._create_single_agent_step("orchestrator", task)

        # ============================================
        # DEACTIVATED FAST ROUTING BELOW (preserved for reference)
        # ============================================
        return []  # This return prevents execution of code below

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

        # For application/system questions (but NOT development tasks!)
        # Only match if it's a question ABOUT the system, not a request to CREATE something
        task_check = task.lower()
        is_system_question = (
            ("was" in task_check or "what" in task_check or "wie" in task_check or "how" in task_check or
             "beschreibe" in task_check or "describe" in task_check or
             "zeige" in task_check or "show" in task_check or "details" in task_check)
            and ("system" in task_check or "workspace" in task_check or "projekt" in task_check or "project" in task_check or "autoagent" in task_check)
        )
        # Exclude development tasks - they should not match this pattern
        is_development = any(keyword in task_check for keyword in [
            'entwickle', 'erstelle', 'baue', 'build', 'create', 'implement'
        ])

        if is_system_question and not is_development:
            return [
                ExecutionStep(
                    id="step1",
                    agent="orchestrator",
                    task="Describe the KI AutoAgent system",
                    expected_output="System description",
                    dependencies=[],
                    status="completed",  # ← FIX: Mark as completed since we have the result
                    result="KI AutoAgent v5.5.1 - Multi-Agent AI Development System mit Intelligent Query Handler\n\nDies ist ein fortschrittliches Multi-Agent-System für die Softwareentwicklung:\n\n🏗️ ARCHITEKTUR:\n• VS Code Extension (TypeScript) - User Interface\n• Python Backend mit LangGraph (Port 8001)\n• WebSocket-basierte Kommunikation\n• 10 spezialisierte KI-Agenten\n• Self-Diagnosis System für automatische Fehlererkennung\n• Intelligent Query Handler für sinnvolle Antworten\n\n🤖 HAUPT-FEATURES:\n• Agent-to-Agent Kommunikation\n• Plan-First Mode mit Approval\n• Persistent Memory\n• Dynamic Workflow Modification\n• Pre-Execution Validation (v5.5.0)\n• Intelligent Query Understanding (v5.5.1)\n• IMMER sinnvolle Antworten - keine generischen Nachrichten\n\n🧠 INTELLIGENT QUERY HANDLER (NEU v5.5.1):\n• Analysiert JEDE Anfrage intelligent\n• Erkennt Intent, Domain und Query-Typ\n• Wählt automatisch den besten Agenten\n• Generiert immer hilfreiche Antworten\n• Keine leeren oder generischen Ergebnisse mehr\n\n🔍 SELF-DIAGNOSIS (v5.5.0):\n• 8 Invarianten-Regeln die immer gelten müssen\n• 9 bekannte Anti-Patterns aus Internet-Recherche\n• 3-Pass Validierungssystem vor Ausführung\n• Automatische Reparatur kritischer Fehler\n• Real-Time Health Monitoring\n\n💡 VERWENDUNG:\nDas System versteht JEDE Ihrer Anfragen und gibt immer sinnvolle Antworten. Es kann Software entwickeln, analysieren und optimieren - und dabei seine eigenen Fehler erkennen und beheben!"
                )
            ]

        # 🎯 HYBRID INTELLIGENT ROUTING: Priority-based keyword matching with confidence scoring
        # ACTION verbs (high priority) override DOMAIN nouns (low priority)
        task_lower = task.lower()

        # 🏗️ SPECIAL CASE: Development/Implementation tasks always get multi-agent workflow
        # This ensures proper architecture → code → review flow
        is_development_task = any(keyword in task_lower for keyword in [
            'entwickle', 'erstelle', 'baue', 'build', 'create', 'implement',
            'write', 'code', 'app', 'application', 'webapp', 'website', 'game'
        ])

        is_html_task = any(keyword in task_lower for keyword in [
            'html', 'web', 'browser', 'tetris', 'game', 'canvas'
        ])

        if is_development_task or is_html_task:
            logger.info(f"🏗️ DEVELOPMENT TASK detected - creating multi-agent workflow (architect → codesmith → reviewer → fixer)")

            steps = [
                ExecutionStep(
                    id="step1",
                    agent="architect",
                    task=f"Design system architecture for: {task}",
                    expected_output="Architecture design and technology recommendations",
                    dependencies=[],
                    status="pending",
                    result=None
                ),
                ExecutionStep(
                    id="step2",
                    agent="codesmith",
                    task=f"GENERATE ACTUAL WORKING CODE (NOT DOCUMENTATION): {task}. Create complete, functional code that is ready to run. DO NOT create architecture documentation or specifications - only create the actual working implementation.",
                    expected_output="Complete working code implementation",
                    dependencies=["step1"],
                    status="pending",
                    result=None
                ),
                ExecutionStep(
                    id="step3",
                    agent="reviewer",
                    task=f"Review and test implementation",
                    expected_output="Test results with quality score and recommendations",
                    dependencies=["step2"],
                    status="pending",
                    result=None
                ),
                ExecutionStep(
                    id="step4",
                    agent="fixer",
                    task="Fix any issues found by reviewer",
                    expected_output="All issues resolved",
                    dependencies=["step3"],
                    status="pending",
                    result=None
                )
            ]

            logger.info(f"✅ Created {len(steps)}-step development workflow")
            return steps

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

        # No keyword matches or low confidence - use intelligent handler
        logger.info(f"🤔 No clear keyword match - using intelligent query analysis")

        # v5.5.1: Use intelligent handler to create a meaningful execution plan
        if self.intelligent_handler:
            logger.info("🧠 Using Intelligent Query Handler to create execution plan")
            intelligent_plan = self.intelligent_handler.create_intelligent_execution_plan(task)

            # If the plan suggests a non-orchestrator agent, use it
            if intelligent_plan and intelligent_plan[0].agent != "orchestrator":
                logger.info(f"✨ Intelligent routing to {intelligent_plan[0].agent}")
                return intelligent_plan

            # Otherwise, create orchestrator step with intelligent response
            return self._create_single_agent_step("orchestrator", task)
        else:
            # Fallback to original behavior if intelligent handler not available
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
            'codesmith': ['implement', 'implementiere', 'write', 'schreibe', 'erstelle', 'create', 'baue', 'build',
                         'create code', 'erstelle code', 'generate code', 'create a', 'write a', 'implement a',
                         'build a', 'baue eine', 'erstelle eine', 'develop', 'entwickle'],
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

        v5.5.1: Enhanced with intelligent responses - NEVER returns empty results
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

        # FIX v5.4.2: Orchestrator can't be a destination node, mark as completed
        # to prevent infinite loop when routing back to orchestrator
        step_status = "completed" if agent == "orchestrator" else "pending"

        # v5.5.1: For orchestrator steps, generate intelligent response immediately
        step_result = None
        if agent == "orchestrator" and self.intelligent_handler:
            # Generate intelligent response for this query
            step_result = self.intelligent_handler.get_intelligent_response(task)
            logger.info(f"🧠 Generated intelligent response for orchestrator step ({len(step_result)} chars)")

        # Return single agent step
        step = ExecutionStep(
            id="step1",
            agent=agent,
            task=task,
            expected_output=output_map.get(agent, "Task result"),
            dependencies=[],
            status=step_status,
            result=step_result  # Will be None for non-orchestrator or filled with intelligent response
        )

        # v5.5.1: Additional enhancement - ensure step has meaningful content
        if self.intelligent_handler and agent == "orchestrator":
            step = self.intelligent_handler.enhance_orchestrator_step(step, task)

        return [step]

    def _detect_task_complexity(self, task: str) -> str:
        """
        Detect if a task is simple, moderate, or complex

        Returns:
            "simple" | "moderate" | "complex"
        """
        task_lower = task.lower()

        # Complex indicators (use Orchestrator AI)
        complex_indicators = [
            # Multi-objective tasks
            len(task.split(" und ")) > 2,  # "Implement X und Y und Z"
            len(task.split(" and ")) > 2,

            # Multi-component integration
            any(word in task_lower for word in [
                "integriere", "integrate", "verbinde", "connect",
                "kombiniere", "combine"
            ]) and len(task.split()) > 8,

            # Complex requirements
            any(word in task_lower for word in [
                "komplex", "complex", "advanced", "comprehensive",
                "enterprise", "production", "scalable"
            ]),

            # Multiple agents likely needed (research + design + implement + test + document)
            task.count(",") > 2,

            # Explicitly asks for optimization + documentation
            ("optimiere" in task_lower or "optimize" in task_lower) and
            ("dokumentiere" in task_lower or "document" in task_lower),

            # Long task description (>15 words)
            len(task.split()) > 15
        ]

        if any(complex_indicators):
            logger.info(f"🎯 Task classified as COMPLEX (will use Orchestrator AI)")
            return "complex"

        # Simple indicators (use direct keyword routing)
        simple_indicators = [
            # Single-word commands
            len(task.split()) <= 3,

            # Direct agent targeting
            any(word in task_lower for word in [
                "fix", "review", "explain", "list", "show", "tell"
            ]),

            # Simple questions
            task.strip().endswith("?") and len(task.split()) < 10
        ]

        if any(simple_indicators):
            logger.info(f"🎯 Task classified as SIMPLE (will use keyword routing)")
            return "simple"

        # Default: moderate complexity
        logger.info(f"🎯 Task classified as MODERATE (will use standard workflow)")
        return "moderate"

    async def _use_orchestrator_for_planning(self, task: str, complexity: str) -> List[ExecutionStep]:
        """
        Use Orchestrator AI to decompose complex tasks

        Phase 2.3: Orchestrator Integration
        """
        if not ORCHESTRATOR_AVAILABLE or "orchestrator" not in self.real_agents:
            logger.warning("⚠️ Orchestrator not available - falling back to keyword routing")
            return self._create_single_agent_step("orchestrator", task)

        logger.info(f"🤖 Using Orchestrator AI for task decomposition (complexity: {complexity})")

        try:
            orchestrator = self.real_agents["orchestrator"]

            # Use Orchestrator's execute method
            request = TaskRequest(prompt=task, context={"complexity": complexity})
            result = await orchestrator.execute(request)

            # Extract execution plan from result metadata
            if result.metadata and "subtasks" in result.metadata:
                subtasks = result.metadata["subtasks"]

                # Convert to ExecutionSteps
                steps = []
                for subtask in subtasks:
                    steps.append(ExecutionStep(
                        id=subtask.get("id", f"step_{len(steps)+1}"),
                        agent=subtask.get("agent", "codesmith"),
                        task=subtask.get("description", subtask.get("task", "")),
                        expected_output=subtask.get("expected_output", "Task completion"),
                        dependencies=subtask.get("dependencies", []),
                        status="pending",
                        result=None,
                        # Removed metadata field as ExecutionStep doesn't support it
                        # Could use timeout_seconds for duration if needed
                        timeout_seconds=int(subtask.get("estimated_duration", 5.0) * 60) if subtask.get("estimated_duration") else 300
                    ))

                logger.info(f"✅ Orchestrator created {len(steps)}-step plan with parallelization")
                return steps

        except Exception as e:
            logger.error(f"❌ Orchestrator planning failed: {e}")
            logger.warning("⚠️ Falling back to default development workflow")

        # Fallback: For development tasks, create default multi-agent workflow
        task_lower = task.lower()
        if any(keyword in task_lower for keyword in ['create', 'build', 'develop', 'app', 'web', 'calculator']):
            logger.info("🏗️ Creating default development workflow (architect → codesmith → reviewer → fixer)")
            return [
                ExecutionStep(
                    id="step1",
                    agent="architect",
                    task=f"Design system architecture for: {task}",
                    expected_output="Architecture design",
                    dependencies=[],
                    status="pending",
                    result=None
                ),
                ExecutionStep(
                    id="step2",
                    agent="codesmith",
                    task=f"Implement the code for: {task}",
                    expected_output="Working code implementation",
                    dependencies=["step1"],
                    status="pending",
                    result=None
                ),
                ExecutionStep(
                    id="step3",
                    agent="reviewer",
                    task="Review and test the implementation",
                    expected_output="Code review and test results",
                    dependencies=["step2"],
                    status="pending",
                    result=None
                ),
                ExecutionStep(
                    id="step4",
                    agent="fixer",
                    task="Fix any issues found by reviewer",
                    expected_output="All issues resolved",
                    dependencies=["step3"],
                    status="pending",
                    result=None
                )
            ]

        # For non-development tasks, use intelligent handler
        if self.intelligent_handler:
            return self.intelligent_handler.create_intelligent_execution_plan(task)

        # Ultimate fallback
        return self._create_single_agent_step("orchestrator", task)

    async def _store_execution_for_learning(
        self,
        task: str,
        final_state: ExtendedAgentState,
        success: bool
    ):
        """
        Store execution results for future learning

        Phase 3.2: Success/Failure Tracking
        """
        try:
            # Extract execution plan decomposition
            execution_plan = final_state.get("execution_plan", [])

            if not execution_plan:
                return

            # Convert execution plan to decomposition format
            subtasks = []
            for step in execution_plan:
                subtasks.append({
                    "id": step.id,
                    "description": step.task,
                    "agent": step.agent,
                    "dependencies": step.dependencies if hasattr(step, 'dependencies') else [],
                    "estimated_duration": step.metadata.get('estimated_duration', 5.0) if hasattr(step, 'metadata') and step.metadata else 5.0,
                    "status": step.status
                })

            # Determine if parallel execution was used
            parallelizable = any(
                len(step.dependencies if hasattr(step, 'dependencies') else []) == 0
                for step in execution_plan[1:]  # Skip first step
            )

            decomposition = {
                "subtasks": subtasks,
                "parallelizable": parallelizable,
                "step_count": len(subtasks),
                "agents_used": list(set(step.agent for step in execution_plan))
            }

            # Calculate execution time
            start_time = final_state.get("start_time")
            end_time = final_state.get("end_time")
            execution_time = None
            if start_time and end_time:
                try:
                    execution_time = (end_time - start_time).total_seconds() / 60.0  # minutes
                except:
                    pass

            # Store in Orchestrator memory for learning
            if "orchestrator" in self.agent_memories:
                memory = self.agent_memories["orchestrator"]
                memory.store_memory(
                    content=f"Task execution: {task}",
                    memory_type="procedural",
                    importance=0.8 if success else 0.5,
                    metadata={
                        "task": task,
                        "success": success,
                        "decomposition": decomposition,
                        "execution_time": execution_time,
                        "errors": final_state.get("errors", []),
                        "timestamp": datetime.now().isoformat()
                    },
                    session_id=final_state.get("session_id")
                )

                status_emoji = "✅" if success else "❌"
                logger.info(f"{status_emoji} Stored execution result for learning (success={success})")

        except Exception as e:
            logger.warning(f"⚠️ Failed to store execution for learning: {e}")

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
                    prompt=step.task,
                    context={
                        "step_id": step.id,
                        "task_type": "architecture",
                        "workspace_path": state.get("workspace_path"),
                        "session_id": state.get("session_id")
                    }
                )
                result = await agent.execute(task_request)
                return result.content if hasattr(result, 'content') else str(result)
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

    # ============================================================================
    # v5.2.0: Architecture Proposal System - Helper Functions
    # ============================================================================

    async def _create_architecture_proposal(
        self,
        state: ExtendedAgentState,
        research_results: str
    ) -> Dict[str, Any]:
        """
        Create architecture proposal with improvements based on research

        Args:
            state: Current workflow state
            research_results: Research findings from architect's initial analysis

        Returns:
            Dict with proposal sections: summary, improvements, tech_stack, structure, risks, research_insights
        """
        logger.info("📋 Creating architecture proposal...")

        original_request = state.get("task_description", "")
        current_step = self._get_current_step(state)
        task = current_step.task if current_step else original_request

        # Build prompt for architect to create proposal
        prompt = f"""Based on your research, create a comprehensive ARCHITECTURE PROPOSAL for user approval.

**Original User Request:**
{original_request}

**Architect Task:**
{task}

**Research Findings:**
{research_results}

Create a detailed proposal in JSON format with these sections:

1. **summary**: High-level architecture overview (2-3 paragraphs)
2. **improvements**: Suggested improvements to user's original idea based on research findings (bulleted list)
3. **tech_stack**: Recommended technologies with justifications (including alternatives considered)
4. **structure**: Folder/module structure with explanations
5. **risks**: Potential challenges and mitigation strategies
6. **research_insights**: Key findings from research that influenced design decisions

**IMPORTANT:**
- Be specific and actionable
- Explain WHY each decision was made
- Reference research findings that support decisions
- Suggest improvements even if not explicitly requested
- Consider scalability, maintainability, testability

Return ONLY valid JSON with these exact keys."""

        # Call architect agent to create proposal
        if "architect" in self.real_agents:
            try:
                agent = self.real_agents["architect"]
                task_request = TaskRequest(
                    prompt=prompt,
                    context={
                        "task_type": "architecture_proposal",
                        "workspace_path": state.get("workspace_path"),
                        "session_id": state.get("session_id"),
                        "research_results": research_results
                    }
                )
                result = await agent.execute(task_request)
                content = result.content if hasattr(result, 'content') else str(result)

                # v5.7.0: Enhanced debug logging for empty responses
                logger.info(f"🔍 Architect response length: {len(content)} characters")
                if not content or not content.strip():
                    logger.error(f"❌ Architect returned empty response! Result type: {type(result)}")
                    logger.error(f"❌ Result attributes: {dir(result)}")
                    raise ValueError("Architect returned empty response")

                # v5.7.1: Log full response for debugging JSON issues
                logger.info(f"📝 Architect FULL RESPONSE:\n{'='*80}\n{content}\n{'='*80}")
                logger.info(f"📝 First 100 chars: {repr(content[:100])}")
                logger.info(f"📝 Last 100 chars: {repr(content[-100:])}")

                # Try to parse JSON
                import json
                import re

                # Extract JSON if wrapped in markdown code blocks
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
                    logger.info("✅ Extracted JSON from markdown code block")
                else:
                    logger.warning("⚠️ No JSON markdown block found, trying direct parse")

                # Try to parse the JSON
                try:
                    proposal = json.loads(content)
                except json.JSONDecodeError as je:
                    logger.error(f"❌ JSON decode error at position {je.pos}: {je.msg}")
                    logger.error(f"❌ Content around error: {repr(content[max(0, je.pos-50):je.pos+50])}")
                    raise

                # Validate required keys
                required_keys = ["summary", "improvements", "tech_stack", "structure", "risks", "research_insights"]
                if not all(key in proposal for key in required_keys):
                    raise ValueError(f"Missing required keys in proposal. Got: {list(proposal.keys())}")

                logger.info("✅ Architecture proposal created successfully")
                return proposal

            except Exception as e:
                logger.error(f"❌ Failed to create structured proposal: {e}")
                logger.warning("⚠️ Falling back to text-based proposal")

                # Fallback: Create basic structured proposal from text
                return {
                    "summary": f"Architecture for: {task}",
                    "improvements": "- Research-backed design decisions\n- Scalable architecture\n- Best practices applied",
                    "tech_stack": research_results[:500] if research_results else "Modern tech stack",
                    "structure": "Standard modular architecture",
                    "risks": "Standard implementation risks - will be addressed during development",
                    "research_insights": research_results[:500] if research_results else "Based on research findings"
                }

        # Stub fallback if no real agent
        logger.warning("⚠️ No real architect agent available - using stub proposal")
        return {
            "summary": f"Proposed architecture for: {task}",
            "improvements": "- Modern best practices\n- Scalable design\n- Maintainable structure",
            "tech_stack": "Modern technology stack based on requirements",
            "structure": "Modular architecture with clear separation of concerns",
            "risks": "Implementation complexity, integration challenges",
            "research_insights": "Based on industry best practices and research"
        }

    def _format_proposal_for_user(self, proposal: Dict[str, Any]) -> str:
        """
        Format architecture proposal for user display (markdown)

        Args:
            proposal: Proposal dict from _create_architecture_proposal

        Returns:
            Formatted markdown string for display
        """
        return f"""
# 🏛️ Architecture Proposal

## 📊 Summary
{proposal.get('summary', 'No summary available')}

## ✨ Suggested Improvements
*(Based on research findings)*

{proposal.get('improvements', 'No improvements suggested')}

## 🛠️ Recommended Tech Stack
{proposal.get('tech_stack', 'No tech stack specified')}

## 📁 Project Structure
{proposal.get('structure', 'No structure defined')}

## ⚠️ Risks & Mitigations
{proposal.get('risks', 'No risks identified')}

## 🔍 Research Insights
{proposal.get('research_insights', 'No research insights available')}

---
**Please review this architecture proposal and choose:**
- ✅ **Approve** - Proceed with this design
- ✏️ **Modify** - Request changes (provide feedback)
- ❌ **Reject** - Start over with different approach
"""

    async def _finalize_architecture(self, state: ExtendedAgentState) -> str:
        """
        Finalize architecture design after proposal approval

        Args:
            state: Current workflow state with approved proposal

        Returns:
            Finalized architecture document
        """
        logger.info("✅ Finalizing approved architecture...")

        proposal = state.get("architecture_proposal", {})
        user_feedback = state.get("user_feedback_on_proposal", "")

        # Build final architecture document
        final_doc = f"""# 🏗️ FINALIZED ARCHITECTURE

## Status
✅ **APPROVED BY USER**

{f"## User Feedback{chr(10)}{user_feedback}{chr(10)}" if user_feedback else ""}

## Architecture Summary
{proposal.get('summary', '')}

## Technology Stack
{proposal.get('tech_stack', '')}

## Project Structure
{proposal.get('structure', '')}

## Risk Management
{proposal.get('risks', '')}

## Implementation Notes
Based on research insights:
{proposal.get('research_insights', '')}

---
**Next Steps:**
1. CodeSmith will implement the core structure
2. Components will be developed according to this architecture
3. Reviewer will validate implementation matches design
"""

        logger.info("✅ Architecture finalized")
        return final_doc

    async def _revise_proposal(
        self,
        state: ExtendedAgentState,
        user_feedback: str
    ) -> Dict[str, Any]:
        """
        Revise architecture proposal based on user feedback

        Args:
            state: Current workflow state
            user_feedback: User's comments/requested changes

        Returns:
            Revised proposal dict
        """
        logger.info(f"✏️ Revising proposal based on feedback: {user_feedback[:100]}...")

        original_proposal = state.get("architecture_proposal", {})
        original_request = state.get("task_description", "")

        # Build revision prompt
        prompt = f"""Revise the architecture proposal based on user feedback.

**Original Proposal:**
{json.dumps(original_proposal, indent=2)}

**User Feedback:**
{user_feedback}

**Original Request:**
{original_request}

Create a REVISED proposal that addresses the user's feedback while maintaining the original goals.

Return ONLY valid JSON with the same structure: summary, improvements, tech_stack, structure, risks, research_insights.

**Important:**
- Address ALL points in user feedback
- Explain what changed and why
- Maintain coherence with original research
"""

        # Call architect agent to revise
        if "architect" in self.real_agents:
            try:
                agent = self.real_agents["architect"]
                task_request = TaskRequest(
                    prompt=prompt,
                    context={
                        "task_type": "proposal_revision",
                        "workspace_path": state.get("workspace_path"),
                        "session_id": state.get("session_id"),
                        "user_feedback": user_feedback
                    }
                )
                result = await agent.execute(task_request)
                content = result.content if hasattr(result, 'content') else str(result)

                # Parse JSON
                import json
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)

                revised_proposal = json.loads(content)
                logger.info("✅ Proposal revised successfully")
                return revised_proposal

            except Exception as e:
                logger.error(f"❌ Failed to revise proposal: {e}")
                logger.warning("⚠️ Returning original proposal with feedback note")

                # Fallback: Add feedback note to original
                original_proposal["improvements"] = f"USER FEEDBACK: {user_feedback}\n\n" + original_proposal.get("improvements", "")
                return original_proposal

        # Stub fallback
        logger.warning("⚠️ No real architect agent - returning original with note")
        original_proposal["improvements"] = f"**User requested:** {user_feedback}\n\n" + original_proposal.get("improvements", "")
        return original_proposal

    # ============================================================================
    # End of v5.2.0 Helper Functions
    # ============================================================================

    async def _execute_codesmith_task(self, state: ExtendedAgentState, step: ExecutionStep, patterns: List) -> Any:
        """Execute codesmith task with real agent or stub"""

        # Use real codesmith agent if available
        if "codesmith" in self.real_agents:
            logger.info("💻 Executing with real CodeSmithAgent...")
            try:
                agent = self.real_agents["codesmith"]

                # Build context from previous steps
                context = {
                    "step_id": step.id,
                    "workspace_path": state.get("workspace_path"),
                    "session_id": state.get("session_id"),
                    "previous_results": []
                }

                # Get architect's design if available (as reference only)
                for prev_step in state["execution_plan"]:
                    if prev_step.agent == "architect" and prev_step.result:
                        # Mark as reference only - CodeSmith should generate code, not copy design docs
                        context["architecture_reference"] = f"REFERENCE ONLY (DO NOT COPY): {prev_step.result[:500]}"
                        context["previous_results"].append({
                            "agent": "architect",
                            "type": "reference_only",
                            "result": prev_step.result[:500]
                        })
                        break

                task_request = TaskRequest(
                    prompt=step.task,
                    context=context
                )
                result = await agent.execute(task_request)

                # v5.5.3: Store metadata in step for later use by Reviewer
                if hasattr(result, 'metadata') and hasattr(step, '__dict__'):
                    step.metadata = result.metadata
                    logger.info(f"💾 Stored CodeSmith metadata: {list(result.metadata.keys())}")

                return result.content if hasattr(result, 'content') else str(result)
            except Exception as e:
                logger.error(f"❌ Real codesmith agent failed: {e}")
                return f"CodeSmith task completed with error: {str(e)}"

        # Fallback to stub
        logger.warning("⚠️ Using stub for codesmith task")
        await asyncio.sleep(1)

        # Return comprehensive code implementation for testing
        return f"""💻 CODE IMPLEMENTATION (STUB)

**Task:** {step.task}

⚠️ STUB response - real CodeSmith would provide actual implementation with files."""

    async def _execute_reviewer_task(self, state: ExtendedAgentState, step: ExecutionStep) -> Any:
        """Execute reviewer task with real agent or stub"""

        # Use real reviewer agent if available
        if "reviewer" in self.real_agents:
            logger.info("📝 Executing with real ReviewerGPTAgent...")
            try:
                agent = self.real_agents["reviewer"]

                # Build context from previous steps
                context = {
                    "step_id": step.id,
                    "workspace_path": state.get("workspace_path"),
                    "session_id": state.get("session_id"),
                    "previous_step_result": None,
                    "previous_results": []
                }

                # Get codesmith's implementation
                for prev_step in state["execution_plan"]:
                    if prev_step.agent == "codesmith" and prev_step.result:
                        context["previous_step_result"] = prev_step.result
                        context["implementation"] = prev_step.result
                        # v5.5.3: Pass metadata separately for Reviewer to access
                        if hasattr(prev_step, 'metadata') and prev_step.metadata:
                            context["metadata"] = prev_step.metadata
                            logger.info(f"📦 Passing CodeSmith metadata to Reviewer: {list(prev_step.metadata.keys())}")
                    context["previous_results"].append({
                        "agent": prev_step.agent,
                        "result": prev_step.result
                    })

                task_request = TaskRequest(
                    prompt=step.task,
                    context=context
                )
                result = await agent.execute(task_request)
                return result.content if hasattr(result, 'content') else str(result)
            except Exception as e:
                logger.error(f"❌ Real reviewer agent failed: {e}")
                return f"Reviewer task completed with error: {str(e)}"

        # Fallback to stub
        logger.warning("⚠️ Using stub for reviewer task")
        await asyncio.sleep(1)

        return f"""📝 CODE REVIEW REPORT (STUB)

**Task:** {step.task}

⚠️ STUB response - real Reviewer would provide detailed analysis."""

    async def _execute_fixer_task(self, state: ExtendedAgentState, step: ExecutionStep, issues: List) -> Any:
        """Execute fixer task with real agent or stub"""

        # Use real fixer agent if available
        if "fixer" in self.real_agents:
            logger.info("🔧 Executing with real FixerBotAgent...")
            try:
                agent = self.real_agents["fixer"]

                # Build context from previous steps
                context = {
                    "step_id": step.id,
                    "workspace_path": state.get("workspace_path"),
                    "session_id": state.get("session_id"),
                    "errors_to_fix": [],
                    "previous_results": []
                }

                # Get reviewer's findings
                for prev_step in state["execution_plan"]:
                    if prev_step.agent == "reviewer" and prev_step.result:
                        context["review_result"] = prev_step.result
                        # Try to extract errors from review
                        if "error" in str(prev_step.result).lower() or "issue" in str(prev_step.result).lower():
                            context["errors_to_fix"].append(prev_step.result)
                    context["previous_results"].append({
                        "agent": prev_step.agent,
                        "result": prev_step.result
                    })

                task_request = TaskRequest(
                    prompt=step.task,
                    context=context
                )
                result = await agent.execute(task_request)
                return result.content if hasattr(result, 'content') else str(result)
            except Exception as e:
                logger.error(f"❌ Real fixer agent failed: {e}")
                return f"Fixer task completed with error: {str(e)}"

        # Fallback to stub
        logger.warning("⚠️ Using stub for fixer task")
        await asyncio.sleep(1)

        return f"""🔧 BUG FIX REPORT (STUB)

**Task:** {step.task}

⚠️ STUB response - real FixerBot would provide actual fixes.
✓ Edge cases covered

**💡 Additional Recommendations:**
- Add input validation at function entry
- Consider using collections.defaultdict for safer access
- Add logging for debugging

**Status:** ✅ FIXED & VERIFIED

⚠️ STUB response - real FixerBot would provide detailed line-by-line fixes with git diffs."""

    async def _execute_research_task(self, state: ExtendedAgentState, step: ExecutionStep) -> Any:
        """Execute research task with real ResearchAgent"""
        # Use real research agent if available
        if "research" in self.real_agents:
            logger.info("🔍 Executing with real ResearchAgent...")
            try:
                research_agent = self.real_agents["research"]

                # Create task request
                request = TaskRequest(
                    prompt=step.task,
                    context=state
                )

                # Execute research
                result = await research_agent.execute(request)

                if result.status == "success":
                    logger.info(f"✅ ResearchAgent completed: {step.task[:60]}...")
                    return result.content
                else:
                    logger.error(f"❌ ResearchAgent failed: {result.content}")
                    return f"Research failed: {result.content}"

            except Exception as e:
                logger.error(f"❌ ResearchAgent execution error: {e}")
                return f"Research error: {str(e)}"

        # Stub fallback
        logger.warning("⚠️ Using stub for research task")
        await asyncio.sleep(1)

        return f"""🔍 WEB RESEARCH REPORT

**Query:** {step.task}

**📚 Key Findings:**

1. **Best Practices (2025)**
   - Modern approach emphasizes microservices architecture
   - Containerization with Docker/Kubernetes is standard
   - CI/CD pipelines are essential for production

2. **Technology Stack**
   - Frontend: React 18+ with TypeScript
   - Backend: FastAPI or Node.js with Express
   - Database: PostgreSQL for relational, MongoDB for document store
   - Caching: Redis for session management and caching

3. **Security Considerations**
   - Use JWT for authentication
   - Implement rate limiting
   - Enable CORS properly
   - Regular security audits

**🌐 Sources Consulted:**
- Stack Overflow Developer Survey 2025
- GitHub Trending Repositories
- Official Documentation
- Tech Blog Posts

**💡 Recommendations:**
✓ Follow established patterns
✓ Use well-maintained libraries
✓ Implement proper error handling
✓ Add comprehensive tests

**Status:** ✅ RESEARCH COMPLETE

⚠️ STUB response - real ResearchAgent would provide actual Perplexity API results with citations."""

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
        workflow.add_node("research", self.research_node)  # v5.1.0
        workflow.add_node("fixer_gpt", self.fixer_gpt_node)  # v5.1.0
        workflow.add_node("docbot", self.docbot_node)  # v5.7.0
        workflow.add_node("performance", self.performance_node)  # v5.7.0
        workflow.add_node("tradestrat", self.tradestrat_node)  # v5.7.0
        workflow.add_node("opus_arbitrator", self.opus_arbitrator_node)  # v5.7.0

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
                "orchestrator": "orchestrator",  # For re-planning when modified
                "architect": "architect",
                "codesmith": "codesmith",
                "reviewer": "reviewer",
                "fixer": "fixer",
                "research": "research",  # v5.1.0
                "fixer_gpt": "fixer_gpt",  # v5.1.0
                "docbot": "docbot",  # v5.7.0
                "performance": "performance",  # v5.7.0
                "tradestrat": "tradestrat",  # v5.7.0
                "opus_arbitrator": "opus_arbitrator",  # v5.7.0
                "end": END
            }
        )

        # Dynamic routing based on execution plan
        # Each agent (except orchestrator) can route to next agent or end
        # v5.2.0: Architect has special routing for architecture proposals
        workflow.add_conditional_edges(
            "architect",
            self.route_from_architect,
            {
                "approval": "approval",  # v5.2.0: Route to approval for architecture proposal
                "orchestrator": "orchestrator",
                "architect": "architect",
                "codesmith": "codesmith",
                "reviewer": "reviewer",
                "fixer": "fixer",
                "research": "research",
                "fixer_gpt": "fixer_gpt",
                "docbot": "docbot",  # v5.7.0
                "performance": "performance",  # v5.7.0
                "tradestrat": "tradestrat",  # v5.7.0
                "opus_arbitrator": "opus_arbitrator",  # v5.7.0
                "end": END
            }
        )

        for agent in ["codesmith", "reviewer", "fixer", "research", "fixer_gpt", "docbot", "performance", "tradestrat", "opus_arbitrator"]:
            workflow.add_conditional_edges(
                agent,
                self.route_to_next_agent,
                {
                    "orchestrator": "orchestrator",  # v5.1.0: Re-planning support
                    "architect": "architect",
                    "codesmith": "codesmith",
                    "reviewer": "reviewer",
                    "fixer": "fixer",
                    "research": "research",  # v5.1.0
                    "fixer_gpt": "fixer_gpt",  # v5.1.0
                    "docbot": "docbot",  # v5.7.0
                    "performance": "performance",  # v5.7.0
                    "tradestrat": "tradestrat",  # v5.7.0
                    "opus_arbitrator": "opus_arbitrator",  # v5.7.0
                    "end": END
                }
            )

        return workflow

    async def compile_workflow(self):
        """
        Compile the workflow with checkpointer (v5.4.0)
        v5.5.3: Made async to support AsyncSqliteSaver for better event loop handling
        Enables workflow persistence and resumption for approval flows
        """
        workflow = self.create_workflow()

        # Initialize checkpointer if not already done
        if self.checkpointer is None:
            # v5.5.3: Fixed checkpointer initialization
            # Use MemorySaver for simplicity - SqliteSaver has complex async requirements
            # The event loop issue was not from the checkpointer type, but from mixing sync/async
            self.checkpointer = MemorySaver()
            logger.info("✅ Using MemorySaver for workflow checkpointing")

        # Compile with checkpointer to enable state persistence and resumption
        # The checkpointer automatically saves state at each step
        # When route_after_approval returns "end" for waiting_architecture_approval,
        # the workflow pauses and can be resumed later with the same thread_id
        self.workflow = workflow.compile(
            checkpointer=self.checkpointer
        )
        logger.info("✅ Workflow compiled with checkpointer support")

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
                config={
                    "configurable": {"thread_id": session_id},
                    "recursion_limit": 100  # Increase limit to see more of the loop
                }
            )

            # v5.2.0: Check if workflow is waiting for architecture approval
            if final_state.get("status") == "waiting_architecture_approval":
                # Store state for resumption after approval
                if not hasattr(self, 'active_workflows'):
                    self.active_workflows = {}
                self.active_workflows[session_id] = final_state
                logger.info(f"⏸️  Workflow paused - stored state for session {session_id}")
                logger.info(f"📋 Waiting for architecture proposal approval via WebSocket")
                return final_state

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
                    # v5.5.1: NEVER return generic message - generate intelligent response
                    if self.intelligent_handler:
                        logger.info("🧠 No results found - generating intelligent response")
                        intelligent_response = self.intelligent_handler.get_intelligent_response(task)
                        final_state["final_result"] = intelligent_response
                    else:
                        # Fallback with more context
                        final_state["final_result"] = f"""Ihre Anfrage wurde bearbeitet: {task}

Das System hat die Aufgabe analysiert und verarbeitet.
Für genauere Ergebnisse können Sie gerne eine spezifischere Frage stellen oder einen der folgenden Agenten direkt ansprechen:
• CodeSmith - für Code-Erstellung
• Reviewer - für Code-Analyse
• Architect - für System-Design
• Research - für Informationssuche"""
            else:
                # v5.5.1: Even if no plan created, provide helpful response
                if self.intelligent_handler:
                    logger.info("🧠 No execution plan - generating helpful response")
                    helpful_response = self.intelligent_handler.get_intelligent_response(task)
                    final_state["final_result"] = helpful_response
                else:
                    final_state["final_result"] = "Keine Ausführungsplan erstellt. Bitte präzisieren Sie Ihre Anfrage."

            # PHASE 3.2: Store execution result for learning
            await self._store_execution_for_learning(
                task=task,
                final_state=final_state,
                success=True
            )

            logger.info(f"✅ Workflow completed for session {session_id}")
            return final_state

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            logger.exception(e)  # Print full traceback
            initial_state["status"] = "failed"
            initial_state["errors"].append({
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

            # PHASE 3.2: Store failure for learning
            await self._store_execution_for_learning(
                task=task,
                final_state=initial_state,
                success=False
            )

            return initial_state


async def create_agent_workflow(
    websocket_manager=None,
    db_path: str = "langgraph_state.db",
    memory_db_path: str = "agent_memories.db"
) -> AgentWorkflow:
    """
    Create and return configured agent workflow
    v5.5.3: Made async to support AsyncSqliteSaver initialization

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

    # Compile the workflow (now async)
    await workflow.compile_workflow()

    return workflow