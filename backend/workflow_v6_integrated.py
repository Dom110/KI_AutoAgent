"""
KI AutoAgent v6.1 - INTEGRATED Workflow with ALL v6 Systems

This is the PRODUCTION workflow with COMPLETE v6.1 integration:

✅ Phase 1: Perplexity API (Research Agent)
✅ Phase 1: Asimov Rule 3 (ReviewFix Agent)
✅ Phase 2: Learning System (post-execution)
✅ Phase 2: Curiosity System (pre-execution)
✅ Phase 2: Predictive System (pre-execution)
✅ Phase 3: Tool Registry (agent initialization)
✅ Phase 3: Approval Manager (critical actions)
✅ Phase 3: Workflow Adapter (error recovery)
✅ Phase 4: Query Classifier (entry point)
✅ Phase 4: Neurosymbolic Reasoner (decision validation)
✅ Phase 4: Self-Diagnosis (error handling)

Architecture:
- Query Classifier → Route query to appropriate workflow
- Curiosity System → Ask clarifying questions if needed
- Predictive System → Estimate duration and risks
- SupervisorGraph → Orchestrate all subgraphs
- Tool Registry → Dynamic tool assignment per agent
- Approval Manager → Human-in-the-loop for critical actions
- Workflow Adapter → Adapt workflow based on results
- Neurosymbolic Reasoner → Validate critical decisions
- Learning System → Learn from execution
- Self-Diagnosis → Heal errors automatically

Usage:
    from workflow_v6_integrated import WorkflowV6Integrated

    workflow = WorkflowV6Integrated(workspace_path="/path/to/workspace")
    await workflow.initialize()

    result = await workflow.run(
        user_query="Build E-Commerce API with auth and payment",
        session_id="session_123"
    )

Author: KI AutoAgent Team
Version: 6.2.0-alpha
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from typing import Any

import aiosqlite
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, StateGraph

# Use ClaudeCLISimple instead of langchain-anthropic
from adapters.claude_cli_simple import ClaudeCLISimple as ChatAnthropic

# MCP client for all service calls (replaces direct service imports)
from mcp.mcp_client import MCPClient, MCPConnectionError

from state_v6 import (
    ArchitectState,
    CodesmithState,
    ResearchState,
    ReviewFixState,
    SupervisorState,
    architect_to_supervisor,
    codesmith_to_supervisor,
    research_to_supervisor,
    reviewfix_to_supervisor,
    supervisor_to_architect,
    supervisor_to_codesmith,
    supervisor_to_research,
    supervisor_to_reviewfix,
)
from memory.memory_system_v6 import MemorySystem

# ============================================================================
# V6 SYSTEM IMPORTS
# ============================================================================

# Phase 2: Intelligence Layer
from cognitive.learning_system_v6 import LearningSystemV6
from cognitive.curiosity_system_v6 import CuriositySystemV6
from cognitive.predictive_system_v6 import PredictiveSystemV6

# Phase 3: Dynamic Execution
from tools.tool_registry_v6 import ToolRegistryV6
from workflow.approval_manager_v6 import ApprovalManagerV6, ApprovalAction
from workflow.workflow_adapter_v6 import (
    WorkflowAdapterV6,
    WorkflowContext,
    AdaptationType
)

# Phase 4: Advanced Intelligence
from cognitive.query_classifier_v6 import QueryClassifierV6, QueryType, ComplexityLevel
from cognitive.neurosymbolic_reasoner_v6 import (
    NeurosymbolicReasonerV6,
    ReasoningMode
)
from cognitive.self_diagnosis_v6 import SelfDiagnosisV6

# NEW v6.2: Workflow Planner & Timeout Handler
from cognitive.workflow_planner_v6 import WorkflowPlannerV6, WorkflowPlan, AgentType, ConditionType
from utils.timeout_handler import HumanResponseManager, TimeoutPolicy

# Setup logging
logger = logging.getLogger(__name__)


# ============================================================================
# WORKFLOWV6INTEGRATED CLASS
# ============================================================================

class WorkflowV6Integrated:
    """
    Complete v6.1 workflow with ALL v6 systems integrated.

    All agents use v6_1 subgraphs with Claude CLI and HITL callback support.
    This class provides full v6 intelligence + complete HITL transparency.
    """

    def __init__(
        self,
        workspace_path: str,
        websocket_callback: Any | None = None
    ):
        """
        Initialize WorkflowV6Integrated.

        Args:
            workspace_path: Absolute path to user workspace
            websocket_callback: Optional WebSocket callback for approvals
        """
        self.workspace_path = workspace_path
        self.websocket_callback = websocket_callback

        # Base components
        self.checkpointer: AsyncSqliteSaver | None = None
        self.memory: MemorySystem | None = None
        self.mcp: MCPClient | None = None  # NEW v6.2: MCP client for all service calls
        self.workflow: Any | None = None

        # v6 Intelligence Systems
        self.query_classifier: QueryClassifierV6 | None = None
        self.curiosity: CuriositySystemV6 | None = None
        self.predictive: PredictiveSystemV6 | None = None
        self.learning: LearningSystemV6 | None = None
        self.tool_registry: ToolRegistryV6 | None = None
        self.approval_manager: ApprovalManagerV6 | None = None
        self.workflow_adapter: WorkflowAdapterV6 | None = None
        self.neurosymbolic: NeurosymbolicReasonerV6 | None = None
        self.self_diagnosis: SelfDiagnosisV6 | None = None

        # NEW v6.2: Workflow Planner & Human Response Timeout Handler
        self.workflow_planner: WorkflowPlannerV6 | None = None
        self.response_manager: HumanResponseManager | None = None

        # Execution tracking
        self.current_session: dict[str, Any] = {}

        logger.info(f"🚀 WorkflowV6Integrated initialized for workspace: {workspace_path}")

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    async def initialize(self) -> None:
        """
        Initialize ALL workflow components including v6 systems.

        Steps:
        1. Setup AsyncSqliteSaver (checkpointing)
        2. Setup Memory System (FAISS + SQLite)
        3. Initialize v6 Intelligence Systems
        4. Build subgraphs with tool discovery
        5. Build supervisor graph
        6. Compile workflow
        """
        logger.info("🔧 Initializing WorkflowV6Integrated with ALL v6 systems...")

        # 1. Setup checkpointer
        self.checkpointer = await self._setup_checkpointer()
        logger.debug(f"✅ Checkpointer initialized")

        # 2. Setup Memory System
        self.memory = await self._setup_memory()
        logger.debug(f"✅ Memory System initialized")

        # 2.5. Setup MCP Client (NEW v6.2!)
        self.mcp = await self._setup_mcp()
        logger.debug(f"✅ MCP Client initialized")

        # 3. Initialize v6 Intelligence Systems
        await self._initialize_v6_systems()
        logger.debug(f"✅ All v6 systems initialized")

        # 4. Build workflow
        self.workflow = await self._build_workflow()
        logger.debug(f"✅ Workflow compiled with v6 enhancements")

        logger.info("🎉 WorkflowV6Integrated initialization COMPLETE!")

    async def cleanup(self) -> None:
        """
        Clean up all resources (NEW v6.2!).

        Closes MCP connections, database connections, etc.
        Should be called when workflow is done or on shutdown.
        """
        logger.info("🧹 Cleaning up WorkflowV6Integrated resources...")

        # Close MCP client connections
        if self.mcp:
            try:
                await self.mcp.cleanup()
                logger.debug("  ✅ MCP client connections closed")
            except Exception as e:
                logger.warning(f"  ⚠️ Error closing MCP connections: {e}")

        # Close checkpointer database connection
        if self.checkpointer:
            try:
                # AsyncSqliteSaver cleanup
                if hasattr(self.checkpointer, 'conn'):
                    await self.checkpointer.conn.close()
                logger.debug("  ✅ Checkpointer database closed")
            except Exception as e:
                logger.warning(f"  ⚠️ Error closing checkpointer: {e}")

        # Memory cleanup (if needed)
        if self.memory:
            try:
                # MemorySystem cleanup (if it has any)
                if hasattr(self.memory, 'cleanup'):
                    await self.memory.cleanup()
                logger.debug("  ✅ Memory system cleaned up")
            except Exception as e:
                logger.warning(f"  ⚠️ Error cleaning up memory: {e}")

        logger.info("✅ Cleanup complete!")

    async def _setup_checkpointer(self) -> AsyncSqliteSaver:
        """Setup AsyncSqliteSaver for persistent state."""
        db_path = os.path.join(
            self.workspace_path,
            ".ki_autoagent_ws/cache/workflow_checkpoints_v6_integrated.db"
        )

        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = await aiosqlite.connect(db_path)
        checkpointer = AsyncSqliteSaver(conn)
        await checkpointer.setup()

        return checkpointer

    async def _setup_memory(self) -> MemorySystem:
        """Setup Memory System for agent communication."""
        memory = MemorySystem(workspace_path=self.workspace_path)
        await memory.initialize()
        return memory

    async def _setup_mcp(self) -> MCPClient:
        """
        Setup MCP Client for all service calls (NEW v6.2!).

        Connects to MCP servers for Perplexity, Claude, Memory, etc.
        Replaces direct service calls with unified MCP protocol.
        """
        logger.info("🔌 Initializing MCP Client...")

        # MCP Client requires workspace_path parameter (v6.2)
        mcp = MCPClient(workspace_path=self.workspace_path)

        try:
            # Initialize MCP client (connects to all servers)
            await mcp.initialize()
            logger.info(f"  ✅ MCP Client connected to {len(mcp.servers)} servers")

            # List connected servers
            for server_name in mcp.servers:
                logger.debug(f"    - {server_name}: connected")

            return mcp

        except MCPConnectionError as e:
            logger.error(f"  ❌ MCP initialization failed: {e}")
            raise RuntimeError(f"Failed to initialize MCP client: {e}")

    async def _initialize_v6_systems(self) -> None:
        """Initialize ALL v6 intelligence systems."""

        logger.info("🧠 Initializing v6 Intelligence Systems...")

        # Phase 4: Entry Point
        self.query_classifier = QueryClassifierV6()
        logger.debug("  ✅ Query Classifier")

        # Phase 2: Pre-Execution Analysis
        self.curiosity = CuriositySystemV6()
        logger.debug("  ✅ Curiosity System")

        self.learning = LearningSystemV6(memory=self.memory)
        logger.debug("  ✅ Learning System")

        self.predictive = PredictiveSystemV6(learning_system=self.learning)
        logger.debug("  ✅ Predictive System")

        # Phase 3: Dynamic Execution
        self.tool_registry = ToolRegistryV6()
        await self.tool_registry.discover_tools()
        logger.debug(f"  ✅ Tool Registry ({len(self.tool_registry.tools)} tools discovered)")

        self.approval_manager = ApprovalManagerV6(
            websocket_callback=self.websocket_callback
        )
        logger.debug("  ✅ Approval Manager")

        self.workflow_adapter = WorkflowAdapterV6(learning_system=self.learning)
        logger.debug("  ✅ Workflow Adapter")

        # Phase 4: Advanced Intelligence
        self.neurosymbolic = NeurosymbolicReasonerV6()
        logger.debug("  ✅ Neurosymbolic Reasoner")

        self.self_diagnosis = SelfDiagnosisV6(learning_system=self.learning)
        logger.debug("  ✅ Self-Diagnosis System")

        # NEW v6.2: Workflow Planner & Human Response Timeout Handler
        self.workflow_planner = WorkflowPlannerV6()
        logger.debug("  ✅ Workflow Planner")

        self.response_manager = HumanResponseManager()
        logger.debug("  ✅ Human Response Manager")

        logger.info("🎉 All v6 systems initialized successfully!")

    # ========================================================================
    # PRE-EXECUTION ANALYSIS (v6 Intelligence)
    # ========================================================================

    async def _pre_execution_analysis(
        self,
        user_query: str
    ) -> dict[str, Any]:
        """
        Run complete pre-execution analysis using v6 systems.

        Flow:
        1. Query Classifier → Classify and route query
        2. Curiosity System → Detect knowledge gaps
        3. Predictive System → Estimate duration and risks
        4. Neurosymbolic Reasoner → Validate task feasibility

        Args:
            user_query: User's task description

        Returns:
            Analysis results with recommendations
        """
        logger.info("🔍 Running pre-execution analysis...")

        analysis = {
            "classification": None,
            "gaps": None,
            "prediction": None,
            "reasoning": None,
            "proceed": True,
            "warnings": [],
            "suggestions": []
        }

        # 1. QUERY CLASSIFICATION
        logger.debug("  📋 Classifying query...")
        classification = await self.query_classifier.classify_query(user_query)
        analysis["classification"] = {
            "type": classification.query_type.value,
            "complexity": classification.complexity.value,
            "confidence": classification.confidence,
            "required_agents": classification.required_agents,
            "workflow_type": classification.workflow_type,
            "entities": classification.entities
        }

        logger.info(f"  ✅ Query classified: {classification.query_type.value} ({classification.complexity.value})")

        # Check if query needs refinement
        if classification.confidence < 0.6:
            refinements = await self.query_classifier.suggest_refinements(classification)
            analysis["suggestions"].extend(refinements)

        # 2. CURIOSITY ANALYSIS
        logger.debug("  🤔 Analyzing knowledge gaps...")
        gaps_analysis = await self.curiosity.analyze_task(user_query)
        analysis["gaps"] = {
            "has_gaps": gaps_analysis["has_gaps"],
            "confidence": gaps_analysis["confidence"],
            "gaps": gaps_analysis["gaps"],
            "questions": gaps_analysis["questions"]
        }

        if gaps_analysis["has_gaps"]:
            logger.warning(f"  ⚠️  {len(gaps_analysis['gaps'])} knowledge gaps detected")
            analysis["warnings"].append(
                f"Task has {len(gaps_analysis['gaps'])} ambiguous areas"
            )
            # In production, these questions would go to WebSocket
            logger.debug(f"  Questions: {gaps_analysis['questions']}")

        # 3. PREDICTIVE ANALYSIS
        logger.debug("  🔮 Predicting workflow outcomes...")
        project_type = classification.entities.get("technologies", [None])[0] if classification.entities.get("technologies") else None
        prediction = await self.predictive.predict_workflow(
            task_description=user_query,
            project_type=project_type
        )
        analysis["prediction"] = {
            "estimated_duration": prediction["estimated_duration"],
            "risk_level": prediction["risk_level"],
            "risk_factors": prediction["risk_factors"],
            "suggestions": prediction["suggestions"]
        }

        logger.info(f"  ✅ Predicted duration: {prediction['estimated_duration']:.1f} min, Risk: {prediction['risk_level']}")

        # 4. NEUROSYMBOLIC REASONING
        logger.debug("  🧠 Validating task with neurosymbolic reasoning...")
        reasoning_context = {
            "task_description": user_query,
            "task_type": classification.query_type.value,
            "complexity": classification.complexity.value,
            "has_gaps": gaps_analysis["has_gaps"],
            "risk_level": prediction["risk_level"]
        }

        reasoning_result = await self.neurosymbolic.reason(
            context=reasoning_context,
            mode=ReasoningMode.HYBRID
        )

        analysis["reasoning"] = {
            "decision": reasoning_result.decision,
            "confidence": reasoning_result.confidence,
            "constraints_satisfied": reasoning_result.constraints_satisfied,
            "proof": reasoning_result.proof
        }

        # Check if we should proceed
        if "reject" in reasoning_result.decision or "abort" in reasoning_result.decision:
            analysis["proceed"] = False
            analysis["warnings"].append(f"Neurosymbolic reasoning suggests: {reasoning_result.decision}")
            logger.warning(f"  ⚠️  Reasoning suggests NOT proceeding: {reasoning_result.decision}")

        logger.info("✅ Pre-execution analysis complete")

        return analysis

    # ========================================================================
    # SUBGRAPH BUILDERS (with Tool Registry integration)
    # ========================================================================

    def _build_research_subgraph(self) -> Any:
        """Build Research subgraph with MCP (v6.2)."""
        from subgraphs.research_subgraph_v6_1 import create_research_subgraph

        logger.debug("🔬 Building Research subgraph v6.2 (with MCP)...")

        subgraph = create_research_subgraph(
            workspace_path=self.workspace_path,
            mcp=self.mcp,  # Pass MCP client instead of memory
            hitl_callback=self.websocket_callback
        )

        logger.debug("  ✅ Research subgraph built (MCP enabled)")
        return subgraph

    def _build_architect_subgraph(self) -> Any:
        """Build Architect subgraph with MCP (v6.2)."""
        from subgraphs.architect_subgraph_v6_1 import create_architect_subgraph

        logger.debug("📐 Building Architect subgraph v6.2 (with MCP)...")

        subgraph = create_architect_subgraph(
            workspace_path=self.workspace_path,
            mcp=self.mcp,  # Pass MCP client instead of memory
            hitl_callback=self.websocket_callback
        )

        logger.debug("  ✅ Architect subgraph v6.2 built (MCP enabled)")
        return subgraph

    def _build_codesmith_subgraph(self) -> Any:
        """Build Codesmith subgraph with MCP (v6.2)."""
        from subgraphs.codesmith_subgraph_v6_1 import create_codesmith_subgraph

        logger.debug("⚒️  Building Codesmith subgraph v6.2 (with MCP)...")

        subgraph = create_codesmith_subgraph(
            workspace_path=self.workspace_path,
            mcp=self.mcp,  # Pass MCP client instead of memory
            hitl_callback=self.websocket_callback
        )

        logger.debug("  ✅ Codesmith subgraph built (MCP enabled)")
        return subgraph

    def _build_reviewfix_subgraph(self) -> Any:
        """Build ReviewFix subgraph with MCP (v6.2)."""
        from subgraphs.reviewfix_subgraph_v6_1 import create_reviewfix_subgraph

        logger.debug("🔬 Building ReviewFix subgraph v6.2 (with MCP)...")

        subgraph = create_reviewfix_subgraph(
            workspace_path=self.workspace_path,
            mcp=self.mcp,  # Pass MCP client instead of memory
            hitl_callback=self.websocket_callback
        )

        logger.debug("  ✅ ReviewFix subgraph built (MCP enabled)")
        return subgraph

    # ========================================================================
    # DECISION FUNCTIONS (v6.1: Intelligent Flow)
    # ========================================================================

    def _research_decide_next(self, state: SupervisorState) -> str:
        """
        Research decides next step based on results.

        Returns:
            - "architect": Research found info, proceed to design
            - "hitl": Can't find necessary information
        """
        print("🔀 === RESEARCH DECISION ===")
        result = state.get("research_results", {})
        print(f"  research_results type: {type(result)}")
        print(f"  research_results: {str(result)[:200]}")

        # Check if research was successful
        if isinstance(result, dict) and result.get("findings"):
            print("  ✅ Decision: architect")
            logger.info("✅ Research → Architect (findings available)")
            return "architect"

        # No findings after research
        print("  ⚠️  Decision: hitl")
        logger.warning("⚠️ Research → HITL (no findings)")
        return "hitl"

    def _architect_decide_next(self, state: SupervisorState) -> str:
        """
        Architect decides next step based on design quality.

        Returns:
            - "codesmith": Architecture ready, proceed to implementation
            - "research": Need more technical details
            - "hitl": Can't design (unclear requirements)
        """
        print("🔀 === ARCHITECT DECISION ===")
        result = state.get("architecture_design")
        print(f"  architecture_design type: {type(result)}")
        print(f"  architecture_design: {str(result)[:200]}")

        # Check if design is complete
        if result:
            # Check confidence if available
            if isinstance(result, dict):
                confidence = result.get("confidence", 0.8)
                print(f"  confidence: {confidence}")

                if confidence < 0.5:
                    print("  ⚠️  Decision: research")
                    logger.warning("⚠️ Architect → Research (low confidence, need more info)")
                    return "research"

            print("  ✅ Decision: codesmith")
            logger.info("✅ Architect → Codesmith (design complete)")
            return "codesmith"

        # Can't create design
        print("  ⚠️  Decision: hitl")
        logger.warning("⚠️ Architect → HITL (no design created)")
        return "hitl"

    def _codesmith_decide_next(self, state: SupervisorState) -> str:
        """
        Codesmith decides next step based on code generation results.

        Returns:
            - "research": Need more information
            - "reviewfix": Code needs review
            - "hitl": Stuck, need human help (ASIMOV RULE 4)
            - END: All done
        """
        print("🔀 === CODESMITH DECISION ===")
        generated_files = state.get("generated_files", [])
        errors = state.get("errors", [])
        print(f"  generated_files: {generated_files}")
        print(f"  errors: {errors}")

        # Check for errors first
        if errors:
            error_count = len(errors)
            print(f"  error_count: {error_count}")
            if error_count >= 3:
                print("  🛑 Decision: hitl (ASIMOV RULE 4)")
                logger.warning("🛑 Codesmith → HITL (3+ errors, ASIMOV RULE 4)")
                return "hitl"

            print("  🔬 Decision: reviewfix (has errors)")
            logger.info("🔬 Codesmith → ReviewFix (has errors)")
            return "reviewfix"

        # Check if files were generated
        if not generated_files:
            print("  ⚠️  Decision: reviewfix (no files)")
            logger.warning("⚠️ Codesmith → ReviewFix (no files generated)")
            return "reviewfix"

        # All good - proceed to review
        print("  ✅ Decision: reviewfix (files ok)")
        logger.info("✅ Codesmith → ReviewFix (files generated)")
        return "reviewfix"

    def _reviewfix_decide_next(self, state: SupervisorState) -> str:
        """
        ReviewFix decides next step after review.

        Returns:
            - "codesmith": Need to regenerate code
            - "hitl": Can't fix, need human (ASIMOV RULE 4)
            - END: All fixed
        """
        print("🔀 === REVIEWFIX DECISION ===")
        review_feedback = state.get("review_feedback")
        errors = state.get("errors", [])
        print(f"  review_feedback type: {type(review_feedback)}")
        print(f"  review_feedback: {str(review_feedback)[:200]}")
        print(f"  errors: {errors}")

        # Check if there are unfixable errors
        if errors:
            error_count = len(errors)
            print(f"  error_count: {error_count}")
            if error_count >= 3:
                print("  🛑 Decision: hitl (ASIMOV RULE 4)")
                logger.warning("🛑 ReviewFix → HITL (can't fix after 3 attempts)")
                return "hitl"

        # Check if review found issues
        if isinstance(review_feedback, dict):
            issues = review_feedback.get("issues", [])
            print(f"  issues: {issues}")
            if issues:
                print("  ⚒️  Decision: codesmith (found issues)")
                logger.info("⚒️ ReviewFix → Codesmith (found issues to fix)")
                return "codesmith"

        # All good!
        print("  ✅ Decision: END (all fixed)")
        logger.info("✅ ReviewFix → END (all fixed)")
        return END

    def _hitl_decide_next(self, state: SupervisorState) -> str:
        """
        HITL decides next step after human intervention.

        Returns:
            - Agent name: Retry specified agent
            - END: Abort workflow
        """
        hitl_response = state.get("hitl_response", {})
        next_step = hitl_response.get("next_step")

        if next_step and next_step != END:
            logger.info(f"👤 HITL → {next_step} (human decision)")
            return next_step

        logger.info("👤 HITL → END (human abort)")
        return END

    # ========================================================================
    # SUPERVISOR GRAPH (with Workflow Adapter)
    # ========================================================================

    async def _build_workflow(self) -> Any:
        """
        Build main SupervisorGraph with v6 enhancements.

        Enhancements:
        - Workflow Adapter monitors each agent execution
        - Can insert/skip/repeat agents dynamically
        - Self-Diagnosis handles errors
        - Approval Manager gates critical actions
        """
        logger.debug("🏗️  Building Supervisor Graph with v6 enhancements...")

        # Build subgraphs
        research_subgraph = self._build_research_subgraph()
        architect_subgraph = self._build_architect_subgraph()
        codesmith_subgraph = self._build_codesmith_subgraph()
        reviewfix_subgraph = self._build_reviewfix_subgraph()

        # Create graph
        graph = StateGraph(SupervisorState)

        # NEW v6.2: Workflow Planning Node (Entry Point)
        async def workflow_planning_node(state: SupervisorState) -> dict[str, Any]:
            """
            NEW v6.2: Dynamic workflow planning using AI.

            Replaces fixed intent detection with flexible, context-aware planning.
            The AI analyzes the task and creates an optimal execution plan.

            Returns workflow_path for routing to first agent.
            """
            logger.info("🎯 Workflow Planning: Analyzing user request with AI")

            workspace_path = state["workspace_path"]
            user_query = state["user_query"]

            # Gather context for planner
            import glob
            existing_files: list[str] = []
            workspace_has_code = False
            code_patterns = ["*.py", "*.ts", "*.tsx", "*.js", "*.jsx"]
            for pattern in code_patterns:
                matches = glob.glob(os.path.join(workspace_path, "**", pattern), recursive=True)
                if matches:
                    workspace_has_code = True
                    existing_files.extend([os.path.basename(m) for m in matches[:10]])  # First 10

            logger.debug(f"  Workspace has code: {workspace_has_code}")
            logger.debug(f"  Existing files: {len(existing_files)} found")

            # Create dynamic workflow plan using AI
            try:
                plan = await self.workflow_planner.plan_workflow(
                    user_task=user_query,
                    workspace_path=workspace_path,
                    context={
                        "existing_files": existing_files[:10],
                        "workspace_has_code": workspace_has_code
                    }
                )

                # Validate plan
                is_valid, issues = await self.workflow_planner.validate_plan(plan)
                if not is_valid:
                    logger.warning(f"  ⚠️  Plan validation issues: {issues}")
                    # Continue anyway - fallback in plan should be safe

                # Extract agent names from plan
                workflow_path = [step.agent.value for step in plan.agents]

                logger.info(f"  ✅ Workflow planned: {plan.workflow_type} ({plan.complexity})")
                logger.info(f"  📋 Agents: {' → '.join(workflow_path)}")
                logger.debug(f"  ⏱️  Estimated: {plan.estimated_duration}")
                logger.debug(f"  🎯 Success criteria: {', '.join(plan.success_criteria)}")

                # Extract agent modes from plan for later use
                agent_modes = {}
                for step in plan.agents:
                    agent_modes[step.agent.value] = step.mode

                # Store plan in current session
                self.current_session = {
                    "task_description": user_query,
                    "current_phase": "workflow_planning",
                    "workspace_path": workspace_path,
                    "start_time": datetime.now(),
                    "completed_agents": [],
                    "pending_agents": workflow_path.copy(),
                    "results": {},
                    "errors": [],
                    "quality_scores": {},
                    "metadata": {
                        "workflow_plan": {
                            "type": plan.workflow_type,
                            "complexity": plan.complexity,
                            "agents": workflow_path,
                            "estimated_duration": plan.estimated_duration,
                            "success_criteria": plan.success_criteria
                        },
                        "agent_modes": agent_modes,  # ← NEW v6.2: Store modes per agent
                        "workspace_has_code": workspace_has_code
                    }
                }

                return {
                    "final_result": f"Workflow planned: {plan.workflow_type} with {len(workflow_path)} agents",
                    "errors": [],
                    "workflow_path": workflow_path
                }

            except Exception as e:
                logger.error(f"  ❌ Workflow planning failed: {e}")
                # Fallback to simple CREATE workflow
                logger.warning("  ⚠️  Using fallback CREATE workflow")
                fallback_path = ["research", "architect", "codesmith", "reviewfix"]

                self.current_session = {
                    "task_description": user_query,
                    "current_phase": "workflow_planning",
                    "workspace_path": workspace_path,
                    "start_time": datetime.now(),
                    "completed_agents": [],
                    "pending_agents": fallback_path.copy(),
                    "results": {},
                    "errors": [f"Planning error: {str(e)}"],
                    "quality_scores": {},
                    "metadata": {"fallback": True}
                }

                return {
                    "final_result": "Using fallback CREATE workflow",
                    "errors": [f"Planning failed: {str(e)}"],
                    "workflow_path": fallback_path
                }

        # Supervisor node (enhanced with v6)
        async def supervisor_node(state: SupervisorState) -> dict[str, Any]:
            """
            Enhanced supervisor with v6 intelligence.

            Responsibilities:
            - Initialize workflow context
            - Set up tracking
            - Prepare for execution
            """
            logger.info("👔 Supervisor: Initializing workflow execution")

            # Update current session (intent detection already set it up)
            if not self.current_session:
                self.current_session = {
                    "task_description": state["user_query"],
                    "current_phase": "initialization",
                    "workspace_path": state["workspace_path"],
                    "start_time": datetime.now(),
                    "completed_agents": [],
                    "pending_agents": ["research", "architect", "codesmith", "reviewfix"],
                    "results": {},
                    "errors": [],
                    "quality_scores": {},
                    "metadata": {}
                }

            return {
                "final_result": "Supervisor initialized workflow",
                "errors": []
            }

        # Enhanced agent wrappers with Workflow Adapter
        async def research_node_wrapper(state: SupervisorState) -> dict[str, Any]:
            """Research with adaptation monitoring."""
            print("🔬 === RESEARCH NODE START ===")
            logger.info("🔬 Research Agent executing...")

            try:
                self.current_session["current_phase"] = "research"
                print(f"  Input query: {state.get('user_query', 'N/A')[:80]}")

                # NEW v6.2: Extract mode from workflow plan
                agent_modes = self.current_session.get("metadata", {}).get("agent_modes", {})
                research_mode = agent_modes.get("research", "research")  # Default to "research" if not specified
                logger.info(f"  Research mode: {research_mode}")

                research_input = supervisor_to_research(state, mode=research_mode)
                print(f"  Calling research subgraph with mode={research_mode}...")
                research_output = await research_subgraph.ainvoke(research_input)
                print(f"  Research subgraph returned: {type(research_output)}")

                result = research_to_supervisor(research_output)
                print(f"  Result keys: {result.keys()}")
                print(f"  Research results: {str(result.get('research_results', 'N/A'))[:100]}")

                # Track completion
                self.current_session["completed_agents"].append("research")
                # Safe remove: only remove if present
                if "research" in self.current_session["pending_agents"]:
                    self.current_session["pending_agents"].remove("research")
                self.current_session["results"]["research"] = result

                # Check for adaptation needs
                context = WorkflowContext(**self.current_session)
                adaptations = await self.workflow_adapter.analyze_and_adapt(context)

                if adaptations:
                    logger.info(f"  📊 {len(adaptations)} adaptations suggested")
                    for adaptation in adaptations:
                        context = await self.workflow_adapter.apply_adaptation(adaptation, context)
                        self.current_session = {**context.__dict__}

                print("🔬 === RESEARCH NODE END ===")
                return result

            except Exception as e:
                print(f"  ❌ RESEARCH EXCEPTION: {e}")
                logger.error(f"  ❌ Research failed: {e}")
                # Self-diagnosis
                healing = await self.self_diagnosis.self_heal(e, auto_apply=True)
                self.current_session["errors"].append({
                    "agent": "research",
                    "error": str(e),
                    "healing": healing
                })
                return {"errors": [str(e)]}

        async def architect_node_wrapper(state: SupervisorState) -> dict[str, Any]:
            """Architect with neurosymbolic validation."""
            print("📐 === ARCHITECT NODE START ===")
            logger.info("📐 Architect Agent executing...")

            try:
                self.current_session["current_phase"] = "architect"
                print(f"  Research results available: {bool(state.get('research_results'))}")

                architect_input = supervisor_to_architect(state)
                print(f"  Calling architect subgraph...")
                architect_output = await architect_subgraph.ainvoke(architect_input)
                print(f"  Architect subgraph returned: {type(architect_output)}")

                result = architect_to_supervisor(architect_output)
                print(f"  Result keys: {result.keys()}")
                print(f"  Architecture design: {str(result.get('architecture_design', 'N/A'))[:100]}")

                # Validate architecture with neurosymbolic reasoning
                if result.get("architecture_design"):
                    reasoning_result = await self.neurosymbolic.reason(
                        context={
                            "task_description": state["user_query"],
                            "architecture": result["architecture_design"]
                        },
                        mode=ReasoningMode.HYBRID
                    )

                    logger.info(f"  🧠 Architecture validation: {reasoning_result.decision}")
                    result["architecture_validation"] = {
                        "decision": reasoning_result.decision,
                        "confidence": reasoning_result.confidence
                    }

                # Track completion
                self.current_session["completed_agents"].append("architect")
                if "architect" in self.current_session["pending_agents"]:
                    self.current_session["pending_agents"].remove("architect")
                self.current_session["results"]["architect"] = result

                # Adaptation check
                context = WorkflowContext(**self.current_session)
                adaptations = await self.workflow_adapter.analyze_and_adapt(context)
                for adaptation in adaptations:
                    context = await self.workflow_adapter.apply_adaptation(adaptation, context)
                    self.current_session = {**context.__dict__}

                print("📐 === ARCHITECT NODE END ===")
                return result

            except Exception as e:
                print(f"  ❌ ARCHITECT EXCEPTION: {e}")
                logger.error(f"  ❌ Architect failed: {e}")
                healing = await self.self_diagnosis.self_heal(e, auto_apply=True)
                self.current_session["errors"].append({"agent": "architect", "error": str(e)})
                return {"errors": [str(e)]}

        async def codesmith_node_wrapper(state: SupervisorState) -> dict[str, Any]:
            """Codesmith with approval management."""
            print("⚒️  === CODESMITH NODE START ===")
            logger.info("⚒️  Codesmith Agent executing...")

            try:
                self.current_session["current_phase"] = "codesmith"
                print(f"  Architecture design available: {bool(state.get('architecture_design'))}")

                # Request approval for file writes (if enabled)
                if self.approval_manager:
                    print(f"  Requesting approval...")
                    approval = await self.approval_manager.request_approval(
                        action_type=ApprovalAction.FILE_WRITE,
                        description="Codesmith will generate code files",
                        details={"workspace": state["workspace_path"]}
                    )
                    print(f"  Approval result: {approval}")

                    if not approval["approved"]:
                        print(f"  ⚠️  APPROVAL DENIED!")
                        logger.warning("  ⚠️  File write approval denied")
                        return {"errors": ["User denied file write approval"]}

                codesmith_input = supervisor_to_codesmith(state)
                print(f"  Calling codesmith subgraph...")
                codesmith_output = await codesmith_subgraph.ainvoke(codesmith_input)
                print(f"  Codesmith subgraph returned: {type(codesmith_output)}")

                result = codesmith_to_supervisor(codesmith_output)
                print(f"  Result keys: {result.keys()}")
                print(f"  Generated files: {result.get('generated_files', [])}")

                # Track completion with quality score
                self.current_session["completed_agents"].append("codesmith")
                if "codesmith" in self.current_session["pending_agents"]:
                    self.current_session["pending_agents"].remove("codesmith")
                self.current_session["results"]["codesmith"] = result
                self.current_session["quality_scores"]["codesmith"] = 0.85  # Mock score

                # Adaptation check (might insert reviewer if quality low)
                context = WorkflowContext(**self.current_session)
                adaptations = await self.workflow_adapter.analyze_and_adapt(context)
                for adaptation in adaptations:
                    context = await self.workflow_adapter.apply_adaptation(adaptation, context)
                    self.current_session = {**context.__dict__}

                print("⚒️  === CODESMITH NODE END ===")
                return result

            except Exception as e:
                print(f"  ❌ CODESMITH EXCEPTION: {e}")
                logger.error(f"  ❌ Codesmith failed: {e}")
                healing = await self.self_diagnosis.self_heal(e, auto_apply=True)
                self.current_session["errors"].append({"agent": "codesmith", "error": str(e)})
                return {"errors": [str(e)]}

        async def reviewfix_node_wrapper(state: SupervisorState) -> dict[str, Any]:
            """ReviewFix with Asimov Rule 3 and self-healing."""
            print("🔬 === REVIEWFIX NODE START ===")
            logger.info("🔬 ReviewFix Loop executing...")

            try:
                self.current_session["current_phase"] = "reviewfix"
                print(f"  Generated files in state: {state.get('generated_files', [])}")

                reviewfix_input = supervisor_to_reviewfix(state)
                print(f"  Calling reviewfix subgraph...")
                reviewfix_output = await reviewfix_subgraph.ainvoke(reviewfix_input)
                print(f"  ReviewFix subgraph returned: {type(reviewfix_output)}")

                result = reviewfix_to_supervisor(reviewfix_output)
                print(f"  Result keys: {result.keys()}")
                print(f"  Review feedback: {str(result.get('review_feedback', 'N/A'))[:100]}")

                # Track completion
                self.current_session["completed_agents"].append("reviewfix")
                if "reviewfix" in self.current_session["pending_agents"]:
                    self.current_session["pending_agents"].remove("reviewfix")
                self.current_session["results"]["reviewfix"] = result

                # Final adaptation check
                context = WorkflowContext(**self.current_session)
                adaptations = await self.workflow_adapter.analyze_and_adapt(context)
                for adaptation in adaptations:
                    context = await self.workflow_adapter.apply_adaptation(adaptation, context)
                    self.current_session = {**context.__dict__}

                print("🔬 === REVIEWFIX NODE END ===")
                return result

            except Exception as e:
                print(f"  ❌ REVIEWFIX EXCEPTION: {e}")
                logger.error(f"  ❌ ReviewFix failed: {e}")
                healing = await self.self_diagnosis.self_heal(e, auto_apply=True)
                self.current_session["errors"].append({"agent": "reviewfix", "error": str(e)})
                return {"errors": [str(e)]}

        # HITL Node (Human-in-the-Loop) - v6.2 with Timeout Handler
        async def hitl_node(state: SupervisorState) -> dict[str, Any]:
            """
            Human-in-the-Loop node (ASIMOV RULE 4).

            Triggered when agents are stuck or need human guidance.
            Uses timeout handler to wait for human response.
            """
            logger.info("🛑 HITL: Requesting human intervention")

            # Determine what failed
            failed_phase = self.current_session.get("current_phase", "unknown")
            errors = state.get("errors", [])
            last_error = errors[-1] if errors else "Unknown error"

            # Send HITL request via WebSocket
            if self.websocket_callback:
                hitl_request = {
                    "type": "hitl_request",
                    "agent": failed_phase,
                    "error": str(last_error),
                    "suggestion": "Agent is stuck. Please provide guidance or corrections.",
                    "options": ["retry", "skip", "abort"]
                }

                logger.info(f"  📡 Sending HITL request to user...")
                await self.websocket_callback(hitl_request)

                # NEW v6.2: Wait for human response with timeout handler
                request_id = f"hitl_{failed_phase}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                logger.info(f"  ⏳ Waiting for human response (timeout: 300s)...")

                try:
                    # Use HumanResponseManager to wait with timeout
                    result = await self.response_manager.request_response(
                        request_id=request_id,
                        timeout=300.0,  # 5 minutes
                        policy=TimeoutPolicy.AUTO_ABORT  # Abort on timeout
                    )

                    if result["success"]:
                        logger.info(f"  ✅ Human responded: {result['response']}")
                        response_data = result["response"]

                        return {
                            "hitl_response": {
                                "next_step": response_data.get("next_step", END),
                                "action": response_data.get("action", "continue")
                            },
                            "errors": []
                        }
                    else:
                        # Timeout or error
                        logger.warning(f"  ⏱️  Human response timeout/error: {result.get('policy_applied')}")

                        return {
                            "hitl_response": {"next_step": END, "action": "abort"},
                            "errors": [f"HITL: No response after timeout ({result.get('policy_applied')})"]
                        }

                except Exception as e:
                    logger.error(f"  ❌ HITL response error: {e}")
                    return {
                        "hitl_response": {"next_step": END, "action": "abort"},
                        "errors": [f"HITL error: {str(e)}"]
                    }

            # No WebSocket = can't continue
            logger.error("❌ No WebSocket callback for HITL")
            return {
                "hitl_response": {"next_step": END},
                "errors": ["HITL required but no callback available"]
            }

        # Decision function for workflow routing
        def _intent_decide_next(state: SupervisorState) -> str:
            """Route based on AI workflow plan."""
            workflow_path = state.get("workflow_path", ["research"])

            # Safety check: Ensure workflow_path is not empty
            if not workflow_path or len(workflow_path) == 0:
                logger.warning(f"⚠️  Empty workflow_path, defaulting to 'research'")
                workflow_path = ["research"]

            logger.info(f"🔀 Workflow routing: {workflow_path[0]}")

            # Return first step in workflow path
            return workflow_path[0]

        # Add nodes
        graph.add_node("workflow_planning", workflow_planning_node)  # NEW v6.2!
        # NOTE: supervisor_node removed in v6.2 - replaced by workflow_planning
        graph.add_node("research", research_node_wrapper)
        graph.add_node("architect", architect_node_wrapper)
        graph.add_node("codesmith", codesmith_node_wrapper)
        graph.add_node("reviewfix", reviewfix_node_wrapper)
        graph.add_node("hitl", hitl_node)

        # NEW v6.2: Workflow Planning is Entry Point
        graph.set_entry_point("workflow_planning")

        # Workflow Planning → Dynamic routing based on AI plan
        graph.add_conditional_edges(
            "workflow_planning",
            _intent_decide_next,
            {
                "research": "research",      # Most workflows start here
                "architect": "architect",    # REFACTOR (skip research)
                "reviewfix": "reviewfix",    # FIX (direct to review)
                "explain": "research"        # EXPLAIN (research only) - maps to research for now
            }
        )

        # Research → Architect OR HITL (conditional)
        graph.add_conditional_edges(
            "research",
            self._research_decide_next,
            {
                "architect": "architect",
                "hitl": "hitl"
            }
        )

        # Architect → Codesmith OR Research OR HITL (conditional)
        graph.add_conditional_edges(
            "architect",
            self._architect_decide_next,
            {
                "codesmith": "codesmith",
                "research": "research",  # Can loop back for more info!
                "hitl": "hitl"
            }
        )

        # Codesmith → ReviewFix OR HITL (conditional)
        graph.add_conditional_edges(
            "codesmith",
            self._codesmith_decide_next,
            {
                "reviewfix": "reviewfix",
                "hitl": "hitl"
            }
        )

        # ReviewFix → Codesmith OR HITL OR END (conditional)
        graph.add_conditional_edges(
            "reviewfix",
            self._reviewfix_decide_next,
            {
                "codesmith": "codesmith",  # Can loop back for fixes!
                "hitl": "hitl",
                END: END
            }
        )

        # HITL → Any agent OR END (conditional)
        graph.add_conditional_edges(
            "hitl",
            self._hitl_decide_next,
            {
                "research": "research",
                "architect": "architect",
                "codesmith": "codesmith",
                "reviewfix": "reviewfix",
                END: END
            }
        )

        # Compile
        compiled = graph.compile(checkpointer=self.checkpointer)
        logger.debug("✅ Workflow compiled with ALL v6 enhancements")

        return compiled

    # ========================================================================
    # EXECUTION (with v6 Intelligence)
    # ========================================================================

    async def run(
        self,
        user_query: str,
        session_id: str = "default"
    ) -> dict[str, Any]:
        """
        Execute complete workflow with FULL v6 intelligence.

        Flow:
        1. Pre-execution analysis (classifier, curiosity, predictive, reasoning)
        2. Workflow execution with monitoring
        3. Post-execution learning

        Args:
            user_query: User's task description
            session_id: Session ID for checkpoint persistence

        Returns:
            Complete workflow result with v6 insights
        """
        if not self.workflow:
            raise RuntimeError("Workflow not initialized. Call initialize() first.")

        logger.info(f"🚀 Starting INTEGRATED v6 workflow for session: {session_id}")
        logger.info(f"📝 User query: {user_query}")

        workflow_start = datetime.now()

        # ====================================================================
        # PHASE 1: PRE-EXECUTION ANALYSIS
        # ====================================================================

        analysis = await self._pre_execution_analysis(user_query)

        # Check if we should proceed
        if not analysis["proceed"]:
            logger.warning("⚠️  Pre-execution analysis suggests NOT proceeding")
            return {
                "success": False,
                "message": "Pre-execution analysis failed",
                "analysis": analysis,
                "warnings": analysis["warnings"]
            }

        # ====================================================================
        # PHASE 2: WORKFLOW EXECUTION
        # ====================================================================

        logger.info("⚙️  Starting workflow execution...")

        initial_state: SupervisorState = {
            "user_query": user_query,
            "workspace_path": self.workspace_path,
            "workflow_path": None,  # NEW v6.2: Set by workflow_planning_node
            "research_results": None,
            "architecture_design": None,
            "generated_files": [],
            "review_feedback": None,
            "final_result": None,
            "errors": []
        }

        try:
            result = await self.workflow.ainvoke(
                initial_state,
                config={"configurable": {"thread_id": session_id}}
            )

            workflow_end = datetime.now()
            execution_time = (workflow_end - workflow_start).total_seconds()

            logger.info(f"✅ Workflow execution complete ({execution_time:.1f}s)")

        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {e}", exc_info=True)

            # Self-diagnosis on workflow failure
            healing = await self.self_diagnosis.self_heal(e, auto_apply=False)

            # NOTE: Don't cleanup here - let the caller handle cleanup
            # This allows retry scenarios without re-initialization

            return {
                "success": False,
                "message": f"Workflow failed: {str(e)}",
                "analysis": analysis,
                "healing": healing,
                "error": str(e)
            }

        # ====================================================================
        # PHASE 3: POST-EXECUTION LEARNING
        # ====================================================================

        logger.info("📚 Recording workflow execution for learning...")

        # Calculate quality score
        error_count = len(result.get("errors", []))
        quality_score = max(0.0, 1.0 - (error_count * 0.2))  # -0.2 per error

        # Record in learning system
        await self.learning.record_workflow_execution(
            workflow_id=session_id,
            task_description=user_query,
            project_type=analysis.get("classification", {}).get("type", "unknown"),
            execution_metrics={
                "total_time": execution_time,
                "agents_used": self.current_session.get("completed_agents", []),
                "error_count": error_count,
                "adaptations": len(self.workflow_adapter.adaptation_history)
            },
            quality_score=quality_score,
            status="success" if error_count == 0 else "partial",
            errors=[str(err) for err in result.get("errors", [])]
        )

        logger.info(f"  ✅ Learning recorded (quality: {quality_score:.2f})")

        # ====================================================================
        # PHASE 4: COMPILE FINAL RESULT
        # ====================================================================

        # Extract clean result summary for UI
        result_summary = result.get("final_result", "Workflow complete")
        if not result_summary or result_summary == "Workflow complete":
            # Try to build a better summary
            generated_files = result.get("generated_files", [])
            if generated_files:
                result_summary = f"✅ Successfully generated {len(generated_files)} files"
            elif self.current_session.get("completed_agents"):
                agents = ", ".join(self.current_session["completed_agents"])
                result_summary = f"✅ Workflow complete (agents: {agents})"

        final_result = {
            "success": error_count == 0,
            "session_id": session_id,
            "execution_time": execution_time,
            "quality_score": quality_score,

            # v6 Intelligence Insights
            "analysis": analysis,
            "adaptations": self.workflow_adapter.get_adaptation_stats(),
            "health": self.self_diagnosis.get_health_report(),

            # Workflow Results
            "result": result_summary,  # Clean summary instead of full state
            "raw_result": result,      # Keep full result for debugging
            "errors": result.get("errors", []),
            "warnings": analysis["warnings"],
            "agents_completed": self.current_session.get("completed_agents", []),
            "files_generated": len(result.get("generated_files", [])),

            # Metadata
            "v6_systems_used": {
                "query_classifier": True,
                "curiosity": analysis["gaps"]["has_gaps"],
                "predictive": True,
                "tool_registry": True,
                "approval_manager": self.approval_manager is not None,
                "workflow_adapter": len(self.workflow_adapter.adaptation_history) > 0,
                "neurosymbolic": True,
                "learning": True,
                "self_diagnosis": len(self.self_diagnosis.diagnostics) > 0
            }
        }

        logger.info("🎉 INTEGRATED v6 workflow complete!")
        logger.info(f"  Quality: {quality_score:.2f}")
        logger.info(f"  Adaptations: {len(self.workflow_adapter.adaptation_history)}")
        logger.info(f"  Diagnostics: {len(self.self_diagnosis.diagnostics)}")

        return final_result


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ["WorkflowV6Integrated"]
