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

            logger.info(f"✅ Initialized {len(self.real_agents)} real agents")
        except Exception as e:
            logger.error(f"❌ Failed to initialize real agents: {e}")
            logger.exception(e)
            self.real_agents = {}

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

        # Set approval type for execution plan (default for non-architecture proposals)
        # This will be overridden to "architecture_proposal" by architect_node if needed
        if not state.get("approval_type") or state.get("approval_type") == "none":
            state["approval_type"] = "execution_plan"
            logger.info("📋 Set approval_type to 'execution_plan' (default)")

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
        Approval node for Plan-First mode and Architecture Proposals (v5.2.0)

        Handles two types of approvals:
        1. execution_plan approval (Plan-First mode)
        2. architecture_proposal approval (v5.2.0)
        """
        logger.info("✅ Approval node executing")

        # ============================================================
        # v5.2.0: Check approval type
        # ============================================================
        approval_type = state.get("approval_type", "execution_plan")

        # CASE 1: Architecture Proposal Approval (v5.2.0)
        if approval_type == "architecture_proposal":
            proposal_status = state.get("proposal_status")

            if proposal_status == "pending":
                # First time seeing proposal - wait for user approval
                logger.info("📋 Architecture proposal pending - workflow will pause here")
                state["status"] = "waiting_architecture_approval"
                state["waiting_for_approval"] = True
                logger.info("⏸️  Workflow pausing - user must approve via WebSocket")
                # Don't change proposal_status - leave as "pending"
                return state

            elif proposal_status == "approved":
                # User approved - continue workflow
                logger.info("✅ Architecture proposal approved - continuing workflow")
                state["needs_approval"] = False
                state["waiting_for_approval"] = False
                state["approval_status"] = "approved"
                state["approval_type"] = "none"  # Reset for next approvals
                return state

            elif proposal_status == "rejected":
                # User rejected - end workflow
                logger.info("❌ Architecture proposal rejected - ending workflow")
                state["needs_approval"] = False
                state["waiting_for_approval"] = False
                state["approval_status"] = "rejected"
                state["status"] = "failed"
                return state

            elif proposal_status == "modified":
                # User requested changes - route back to architect for revision
                logger.info("🔄 Architecture proposal needs modifications")
                state["needs_approval"] = True
                state["waiting_for_approval"] = False
                state["approval_status"] = "modified"
                return state

            # Fallback - shouldn't reach here
            logger.warning(f"⚠️  Unexpected proposal_status: {proposal_status}")
            return state

        # CASE 2: Execution Plan Approval (existing Plan-First mode)
        if approval_type == "execution_plan":
            logger.info("📋 Execution plan approval flow")

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

        # FALLBACK: Unknown approval type
        logger.warning(f"⚠️ Unknown approval_type: {approval_type}")
        state["waiting_for_approval"] = False
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

                # Send via WebSocket
                if self.websocket_manager:
                    await self.websocket_manager.send_json(state["client_id"], {
                        "type": "architecture_proposal_revised",
                        "proposal": revised_proposal,
                        "formatted_message": formatted_msg,
                        "session_id": state.get("session_id")
                    })

                logger.info("📋 Revised proposal sent to user")
                return state

            # ============================================================
            # v5.2.0: PHASE 2 - No proposal yet → Do research & create proposal
            # ============================================================
            if not state.get("architecture_proposal"):
                logger.info("📋 No proposal exists - performing research and creating proposal")

                # Step 1: Do research (existing behavior)
                research_result = await self._execute_architect_task(state, current_step)
                logger.info(f"🔍 Research completed: {research_result[:200]}...")

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

                # Send via WebSocket
                if self.websocket_manager:
                    await self.websocket_manager.send_json(state["client_id"], {
                        "type": "architecture_proposal",
                        "proposal": proposal,
                        "formatted_message": formatted_msg,
                        "session_id": state.get("session_id")
                    })

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
        issues = review_step.result.get("issues", []) if review_step else []

        try:
            # Fix issues
            fix_result = await self._execute_fixer_task(state, current_step, issues)
            current_step.result = fix_result
            current_step.status = "completed"

            # ✅ FIX: Create NEW list to trigger LangGraph state update
            state["execution_plan"] = list(state["execution_plan"])

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

    def route_after_approval(self, state: ExtendedAgentState) -> str:
        """
        Route after approval node - intelligently routes to first pending agent
        Validates that the agent has a workflow node, fallback to orchestrator if not
        """
        # Available workflow nodes (agents with implemented nodes)
        AVAILABLE_NODES = {"orchestrator", "architect", "codesmith", "reviewer", "fixer", "research", "fixer_gpt"}

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

    def route_from_architect(self, state: ExtendedAgentState) -> str:
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
                return self.route_to_next_agent(state)

        # Standard routing for non-proposal cases
        return self.route_to_next_agent(state)

    def route_to_next_agent(self, state: ExtendedAgentState) -> str:
        """
        Determine next agent based on execution plan
        Validates that the agent has a workflow node, fallback to orchestrator if not
        """
        # Available workflow nodes (agents with implemented nodes)
        AVAILABLE_NODES = {"orchestrator", "architect", "codesmith", "reviewer", "fixer", "research", "fixer_gpt"}

        logger.info(f"🔀 Routing to next agent...")
        logger.info(f"📋 Execution plan has {len(state['execution_plan'])} steps")

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
                return self.route_to_next_agent(state)

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
        """
        task = state.get("current_task", "")

        # ============================================
        # PHASE 2: HYBRID COMPLEXITY-BASED ROUTING
        # ============================================

        # Detect task complexity
        complexity = self._detect_task_complexity(task)

        # Complex tasks → Use Orchestrator AI
        if complexity == "complex" and ORCHESTRATOR_AVAILABLE:
            logger.info("🧠 COMPLEX TASK → Using Orchestrator AI decomposition")
            orchestrator_plan = await self._use_orchestrator_for_planning(task, complexity)
            if orchestrator_plan and len(orchestrator_plan) > 1:
                # Orchestrator successfully created multi-step plan
                return orchestrator_plan
            # Otherwise fall through to standard routing

        # Simple tasks → Fast keyword routing
        if complexity == "simple":
            logger.info("⚡ SIMPLE TASK → Using fast keyword routing")
            # Fall through to keyword routing below

        # Moderate tasks → Standard workflow patterns
        # Continue with existing logic below
        # ============================================

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
            ("was" in task_check or "what" in task_check or "wie" in task_check or "how" in task_check or "beschreibe" in task_check or "describe" in task_check)
            and ("system" in task_check or "workspace" in task_check)
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
            # Detect if this is a development/implementation task
            task_lower = task.lower()
            is_development_task = any(keyword in task_lower for keyword in [
                'entwickle', 'erstelle', 'baue', 'build', 'create', 'implement',
                'write', 'code', 'app', 'application', 'webapp', 'website'
            ])

            is_html_task = any(keyword in task_lower for keyword in [
                'html', 'web', 'browser', 'tetris', 'game', 'canvas'
            ])

            if is_development_task or is_html_task:
                # Multi-agent workflow for development tasks
                logger.info(f"🎯 Orchestrator detected DEVELOPMENT task - creating multi-agent workflow")

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
                        task=f"GENERATE ACTUAL WORKING CODE (NOT DOCUMENTATION): Create a complete, functional Tetris game as a single HTML file with embedded CSS and JavaScript. Use HTML5 Canvas for rendering. The file must be ready to open in a browser and play immediately. DO NOT create architecture documentation or specifications - only create the actual playable game code: {task}",
                        expected_output="Complete working HTML file with embedded game code",
                        dependencies=["step1"],
                        status="pending",
                        result=None
                    ),
                    ExecutionStep(
                        id="step3",
                        agent="reviewer",
                        task=f"Review and test implementation using Playwright browser testing",
                        expected_output="Test results with quality score and recommendations",
                        dependencies=["step2"],
                        status="pending",
                        result=None
                    )
                ]

                # Add optional Fixer step (only if reviewer finds issues)
                # Note: This will be conditionally executed based on reviewer result
                steps.append(
                    ExecutionStep(
                        id="step4",
                        agent="fixer",
                        task="Fix any issues found by reviewer",
                        expected_output="All issues resolved",
                        dependencies=["step3"],
                        status="pending",
                        result=None
                    )
                )

                logger.info(f"✅ Created {len(steps)}-step development workflow")
                return steps
            else:
                # Simple orchestrator response for non-development tasks
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

⚠️ For development tasks, use keywords like: entwickle, erstelle, build, create, implement"""
                    )
                ]

        # v5.2.1: If codesmith is targeted for an app/game/website task,
        # create full development workflow (architect → codesmith → reviewer → fixer)
        if agent == "codesmith":
            task_lower = task.lower()
            is_app_task = any(keyword in task_lower for keyword in [
                'app', 'application', 'webapp', 'website', 'web', 'game',
                'spiel', 'tool', 'utility', 'portal', 'dashboard', 'interface'
            ])

            if is_app_task:
                logger.info(f"🎯 CodeSmith detected APP/GAME task - creating multi-agent development workflow")
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
                        task=f"{task}",
                        expected_output="Complete working implementation",
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
                        metadata={"estimated_duration": subtask.get("estimated_duration", 5.0)}
                    ))

                logger.info(f"✅ Orchestrator created {len(steps)}-step plan with parallelization")
                return steps

        except Exception as e:
            logger.error(f"❌ Orchestrator planning failed: {e}")
            logger.warning("⚠️ Falling back to standard routing")

        # Fallback to keyword routing
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

                # Try to parse JSON
                import json
                import re

                # Extract JSON if wrapped in markdown code blocks
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)

                proposal = json.loads(content)

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
                        if hasattr(prev_step, 'metadata'):
                            context.update(prev_step.metadata or {})
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
                "end": END
            }
        )

        for agent in ["codesmith", "reviewer", "fixer", "research", "fixer_gpt"]:
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
                    final_state["final_result"] = "Task completed but no specific results available."
            else:
                final_state["final_result"] = "No execution plan was created."

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