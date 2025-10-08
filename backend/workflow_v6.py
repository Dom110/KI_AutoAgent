"""
KI AutoAgent v6.0 - Main Workflow Implementation

This is the PRODUCTION workflow implementation following LangGraph best practices.

Architecture:
- SupervisorGraph orchestrates all subgraphs
- AsyncSqliteSaver for persistent checkpointing
- Declarative routing (graph edges, not imperative code)
- State transformations between subgraphs

Usage:
    from workflow_v6 import WorkflowV6

    # Initialize
    workflow = WorkflowV6(workspace_path="/path/to/workspace")
    await workflow.initialize()

    # Execute
    result = await workflow.run(
        user_query="Create a calculator app",
        session_id="session_123"
    )

Author: KI AutoAgent Team
Version: 6.0.0-alpha.1
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import aiosqlite
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import create_react_agent

# Use ClaudeCLISimple instead of langchain-anthropic (which is broken)
from adapters.claude_cli_simple import ClaudeCLISimple as ChatAnthropic

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

# Setup logging
logger = logging.getLogger(__name__)


# ============================================================================
# WORKFLOWV6 CLASS
# ============================================================================

class WorkflowV6:
    """
    Main v6.0 workflow class.

    Manages the complete LangGraph workflow with:
    - AsyncSqliteSaver for persistent state
    - Subgraphs for each agent
    - Memory system integration
    - Error handling and recovery
    """

    def __init__(self, workspace_path: str):
        """
        Initialize WorkflowV6.

        Args:
            workspace_path: Absolute path to user workspace
        """
        self.workspace_path = workspace_path
        self.checkpointer: AsyncSqliteSaver | None = None
        self.memory: MemorySystem | None = None
        self.workflow: Any | None = None

        logger.info(f"WorkflowV6 initialized for workspace: {workspace_path}")

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    async def initialize(self) -> None:
        """
        Initialize workflow components.

        Steps:
        1. Setup AsyncSqliteSaver (persistent checkpointing)
        2. Setup Memory System (FAISS + SQLite)
        3. Build all subgraphs
        4. Build supervisor graph
        5. Compile workflow with checkpointer
        """
        logger.info("Initializing WorkflowV6...")

        # 1. Setup checkpointer
        self.checkpointer = await self._setup_checkpointer()
        logger.debug(f"Checkpointer initialized: {self.checkpointer is not None}")

        # 2. Setup Memory System
        self.memory = await self._setup_memory()
        logger.debug(f"Memory System initialized: {self.memory is not None}")

        # 3. Build workflow
        self.workflow = self._build_workflow()
        logger.debug(f"Workflow compiled: {self.workflow is not None}")

        logger.info("WorkflowV6 initialization complete")

    async def _setup_checkpointer(self) -> AsyncSqliteSaver:
        """
        Setup AsyncSqliteSaver for persistent state.

        Returns:
            Initialized AsyncSqliteSaver instance

        Storage:
            $WORKSPACE/.ki_autoagent_ws/cache/workflow_checkpoints_v6.db
        """
        db_path = os.path.join(
            self.workspace_path,
            ".ki_autoagent_ws/cache/workflow_checkpoints_v6.db"
        )

        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        logger.debug(f"Checkpoint database path: {db_path}")

        # Create connection
        conn = await aiosqlite.connect(db_path)
        logger.debug("SQLite connection established")

        # Create checkpointer
        checkpointer = AsyncSqliteSaver(conn)

        # Initialize tables
        await checkpointer.setup()
        logger.debug("AsyncSqliteSaver setup complete")

        return checkpointer

    async def _setup_memory(self) -> MemorySystem:
        """
        Setup Memory System for agent communication.

        Returns:
            Initialized MemorySystem instance

        Storage:
            $WORKSPACE/.ki_autoagent_ws/memory/metadata.db (SQLite metadata)
            $WORKSPACE/.ki_autoagent_ws/memory/vectors.faiss (FAISS index)
        """
        logger.debug("Setting up Memory System...")

        # Memory System expects workspace root, creates its own subdirectories
        memory = MemorySystem(workspace_path=self.workspace_path)
        await memory.initialize()

        logger.debug(f"Memory System initialized for workspace: {self.workspace_path}")

        return memory

    # ========================================================================
    # SUBGRAPH BUILDERS
    # ========================================================================

    def _build_research_subgraph(self) -> Any:
        """
        Build Research subgraph with custom implementation (v6.1).

        v6.1: Uses direct LLM calls instead of create_react_agent
        for compatibility with Claude CLI adapter.

        Agent: Research Agent
        Model: Claude Sonnet 4 (with Perplexity tool)
        Implementation: Custom node (v6.1) ✅

        Returns:
            Compiled research agent
        """
        from subgraphs.research_subgraph_v6_1 import create_research_subgraph

        logger.debug("Building Research subgraph v6.1 (custom node)...")

        # Pass workspace_path and memory to research subgraph
        subgraph = create_research_subgraph(
            workspace_path=self.workspace_path,
            memory=self.memory
        )

        logger.debug("✅ Research subgraph v6.1 built")

        return subgraph

    def _build_architect_subgraph(self) -> Any:
        """
        Build Architect subgraph with custom implementation.

        Agent: Architect Agent
        Model: GPT-4o
        Implementation: Custom (too specialized for create_react_agent) - Phase 4 ✅

        Returns:
            Compiled architect subgraph
        """
        from subgraphs.architect_subgraph_v6 import create_architect_subgraph

        logger.debug("Building Architect subgraph (custom implementation)...")

        # Pass workspace_path and memory to architect subgraph
        subgraph = create_architect_subgraph(
            workspace_path=self.workspace_path,
            memory=self.memory
        )

        logger.debug("✅ Architect subgraph built")

        return subgraph

    def _build_codesmith_subgraph(self) -> Any:
        """
        Build Codesmith subgraph with custom implementation (v6.1).

        v6.1: Uses direct LLM calls instead of create_react_agent
        for compatibility with Claude CLI adapter.

        Agent: Codesmith Agent
        Model: Claude Sonnet 4
        Implementation: Custom node with file tools (v6.1) ✅

        Returns:
            Compiled codesmith agent
        """
        from subgraphs.codesmith_subgraph_v6_1 import create_codesmith_subgraph

        logger.debug("Building Codesmith subgraph v6.1 (custom node with file tools)...")

        # Pass workspace_path and memory to codesmith subgraph
        subgraph = create_codesmith_subgraph(
            workspace_path=self.workspace_path,
            memory=self.memory
        )

        logger.debug("✅ Codesmith subgraph v6.1 built")

        return subgraph

    def _build_reviewfix_subgraph(self) -> Any:
        """
        Build ReviewFix loop subgraph with custom Fixer (v6.1).

        v6.1: Fixer uses direct LLM calls instead of create_react_agent
        for compatibility with Claude CLI adapter.

        Agents: Reviewer + Fixer
        Models: GPT-4o-mini (Reviewer), Claude Sonnet 4 (Fixer)
        Implementation: Custom loop with conditional routing (v6.1) ✅

        Returns:
            Compiled reviewfix loop subgraph
        """
        from subgraphs.reviewfix_subgraph_v6_1 import create_reviewfix_subgraph

        logger.debug("Building ReviewFix subgraph v6.1 (custom Fixer node)...")

        # Pass workspace_path and memory to reviewfix subgraph
        subgraph = create_reviewfix_subgraph(
            workspace_path=self.workspace_path,
            memory=self.memory
        )

        logger.debug("✅ ReviewFix subgraph v6.1 built")

        return subgraph

    # ========================================================================
    # SUPERVISOR GRAPH
    # ========================================================================

    def _build_workflow(self) -> Any:
        """
        Build main SupervisorGraph.

        This orchestrates all subgraphs with declarative routing.

        Returns:
            Compiled workflow with checkpointer
        """
        logger.debug("Building SupervisorGraph...")

        # Build subgraphs (Phase-by-phase - only build what we use!)
        # Phase 3: Research
        research_subgraph = self._build_research_subgraph()

        # Phase 4: Architect
        architect_subgraph = self._build_architect_subgraph()

        # Phase 5: Codesmith
        codesmith_subgraph = self._build_codesmith_subgraph()

        # Phase 6: ReviewFix
        reviewfix_subgraph = self._build_reviewfix_subgraph()

        logger.debug("Research + Architect + Codesmith + ReviewFix subgraphs built (Phase 3-6)")

        # Supervisor node
        def supervisor_node(state: SupervisorState) -> SupervisorState:
            """
            Supervisor orchestration logic (Phase 7).

            This orchestrates the full workflow:
            1. Research: Web search + knowledge gathering
            2. Architect: Design architecture based on research
            3. Codesmith: Generate code based on design
            4. ReviewFix: Review code quality + apply fixes

            Phase 7: Sequential flow (all tasks go through all agents)
            Phase 8+: Could add conditional routing based on task type
            """
            logger.info(f"🎯 Supervisor starting workflow: {state['user_query'][:60]}...")
            logger.info(f"📂 Workspace: {state['workspace_path']}")
            logger.info("🔄 Workflow: Research → Architect → Codesmith → ReviewFix")

            return state

        # Build graph
        graph = StateGraph(SupervisorState)

        # Add supervisor
        graph.add_node("supervisor", supervisor_node)

        # Add subgraphs with state transformation wrappers (Phase 3 ✅)
        # Import state transformations
        from state_v6 import (
            supervisor_to_research,
            research_to_supervisor,
            supervisor_to_architect,
            architect_to_supervisor,
            supervisor_to_codesmith,
            codesmith_to_supervisor,
            supervisor_to_reviewfix,
            reviewfix_to_supervisor
        )

        # Research node with state transformation (v6.1: async)
        async def research_node_wrapper(state: SupervisorState) -> dict[str, Any]:
            """Transform SupervisorState → ResearchState → call subgraph → transform back"""
            logger.debug("🔍 Research node (with state transformation)")
            research_input = supervisor_to_research(state)
            research_output = await research_subgraph.ainvoke(research_input)
            return research_to_supervisor(research_output)

        # Architect node with state transformation (v6.1: async)
        async def architect_node_wrapper(state: SupervisorState) -> dict[str, Any]:
            """Transform SupervisorState → ArchitectState → call subgraph → transform back"""
            logger.debug("🏗️ Architect node (with state transformation)")
            architect_input = supervisor_to_architect(state)
            architect_output = await architect_subgraph.ainvoke(architect_input)
            return architect_to_supervisor(architect_output)

        # Codesmith node with state transformation (v6.1: async)
        async def codesmith_node_wrapper(state: SupervisorState) -> dict[str, Any]:
            """Transform SupervisorState → CodesmithState → call subgraph → transform back"""
            logger.debug("⚙️ Codesmith node (with state transformation)")
            codesmith_input = supervisor_to_codesmith(state)
            codesmith_output = await codesmith_subgraph.ainvoke(codesmith_input)
            return codesmith_to_supervisor(codesmith_output)

        # ReviewFix node with state transformation (v6.1: async)
        async def reviewfix_node_wrapper(state: SupervisorState) -> dict[str, Any]:
            """Transform SupervisorState → ReviewFixState → call subgraph → transform back"""
            logger.debug("🔬 ReviewFix node (with state transformation)")
            reviewfix_input = supervisor_to_reviewfix(state)
            reviewfix_output = await reviewfix_subgraph.ainvoke(reviewfix_input)
            return reviewfix_to_supervisor(reviewfix_output)

        # Phase 3-6: Add research + architect + codesmith + reviewfix nodes
        graph.add_node("research", research_node_wrapper)
        graph.add_node("architect", architect_node_wrapper)
        graph.add_node("codesmith", codesmith_node_wrapper)
        graph.add_node("reviewfix", reviewfix_node_wrapper)

        # Declarative routing (NOT imperative!)
        graph.set_entry_point("supervisor")

        # Phase 7: Full workflow - All subgraphs connected in sequence
        # supervisor → research → architect → codesmith → reviewfix → END
        graph.add_edge("supervisor", "research")
        graph.add_edge("research", "architect")
        graph.add_edge("architect", "codesmith")
        graph.add_edge("codesmith", "reviewfix")
        graph.add_edge("reviewfix", END)

        logger.debug("✅ Phase 7 routing complete: All subgraphs connected")

        # Compile with checkpointer
        compiled = graph.compile(checkpointer=self.checkpointer)
        logger.debug("Workflow compiled with checkpointer")

        return compiled

    # ========================================================================
    # EXECUTION
    # ========================================================================

    async def run(
        self,
        user_query: str,
        session_id: str = "default"
    ) -> dict[str, Any]:
        """
        Execute the complete workflow.

        Args:
            user_query: User's task description
            session_id: Session ID for checkpoint persistence

        Returns:
            Final workflow state with results

        Raises:
            RuntimeError: If workflow not initialized
        """
        if not self.workflow:
            raise RuntimeError("Workflow not initialized. Call initialize() first.")

        logger.info(f"Starting workflow execution for session: {session_id}")
        logger.debug(f"User query: {user_query}")

        # Initial state
        initial_state: SupervisorState = {
            "user_query": user_query,
            "workspace_path": self.workspace_path,
            "research_results": None,
            "architecture_design": None,
            "generated_files": [],
            "review_feedback": None,
            "final_result": None,
            "errors": []
        }

        # Execute with checkpointing
        try:
            result = await self.workflow.ainvoke(
                initial_state,
                config={"configurable": {"thread_id": session_id}}
            )

            logger.info(f"Workflow execution complete for session: {session_id}")
            logger.debug(f"Result errors: {len(result.get('errors', []))}")

            return result

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            raise

    async def resume(self, session_id: str) -> dict[str, Any]:
        """
        Resume workflow from last checkpoint.

        Args:
            session_id: Session ID to resume

        Returns:
            Final workflow state

        Raises:
            RuntimeError: If workflow not initialized
        """
        if not self.workflow:
            raise RuntimeError("Workflow not initialized. Call initialize() first.")

        logger.info(f"Resuming workflow from checkpoint: {session_id}")

        try:
            # Empty input = resume from last checkpoint
            result = await self.workflow.ainvoke(
                {},
                config={"configurable": {"thread_id": session_id}}
            )

            logger.info(f"Workflow resume complete for session: {session_id}")
            return result

        except Exception as e:
            logger.error(f"Workflow resume failed: {e}", exc_info=True)
            raise

    # ========================================================================
    # CLEANUP
    # ========================================================================

    async def cleanup(self) -> None:
        """
        Cleanup resources.

        Closes SQLite connection.
        """
        if self.checkpointer and self.checkpointer.conn:
            await self.checkpointer.conn.close()
            logger.debug("Checkpointer connection closed")

        logger.info("WorkflowV6 cleanup complete")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def main():
    """
    Example usage of WorkflowV6.

    This demonstrates:
    1. Initialization
    2. Workflow execution
    3. Checkpoint persistence
    4. Cleanup
    """
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create workflow
    workflow = WorkflowV6(workspace_path="/tmp/test-workspace-v6")

    try:
        # Initialize
        await workflow.initialize()

        # Execute workflow
        result = await workflow.run(
            user_query="Create a React calculator app with TypeScript",
            session_id="test_session_1"
        )

        # Print results
        print("\n" + "="*70)
        print("WORKFLOW RESULTS")
        print("="*70)
        print(f"User Query: {result['user_query']}")
        print(f"Research: {result.get('research_results')}")
        print(f"Architecture: {result.get('architecture_design')}")
        print(f"Generated Files: {len(result.get('generated_files', []))}")
        print(f"Review: {result.get('review_feedback')}")
        print(f"Errors: {len(result.get('errors', []))}")
        print("="*70 + "\n")

    finally:
        # Cleanup
        await workflow.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
