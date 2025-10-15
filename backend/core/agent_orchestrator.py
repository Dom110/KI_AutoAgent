"""Agent Orchestrator - Agent-to-Agent Communication System

This module implements the core orchestration system that allows agents to invoke
other agents dynamically, pass context, and integrate with HITL (Human-in-the-Loop).

Version: v6.2.0-alpha
Created: 2025-10-15

Key Features:
- Dynamic agent invocation (Research, Architect, Code Indexer)
- Shared context management between agents
- Execution stack tracking (prevents infinite loops)
- HITL integration for approval decisions
- MCP-based communication
"""

import logging
from typing import Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class AgentInvocationError(Exception):
    """Raised when agent invocation fails"""
    pass


class CircularInvocationError(Exception):
    """Raised when circular agent invocation detected"""
    pass


class AgentOrchestrator:
    """
    Central orchestration system for agent-to-agent communication.

    Responsibilities:
    1. Dynamic agent invocation (Research, Architect, Code Indexer)
    2. Context sharing between agents
    3. Execution tracking (prevent infinite loops)
    4. HITL integration
    5. Result aggregation

    Usage:
        orchestrator = AgentOrchestrator(
            mcp_client=mcp_client,
            workspace_path="/path/to/workspace",
            approval_manager=approval_manager,
            hitl_manager=hitl_manager
        )

        # Architect invokes Research
        result = await orchestrator.invoke_research(
            query="How to implement OAuth2?",
            mode="research",
            caller="architect"
        )
    """

    def __init__(
        self,
        mcp_client,
        workspace_path: str,
        approval_manager=None,
        hitl_manager=None
    ):
        """
        Initialize agent orchestrator.

        Args:
            mcp_client: MCPClient instance for external tool calls
            workspace_path: Path to workspace directory
            approval_manager: ApprovalManager for file write approvals
            hitl_manager: HITLManager for human collaboration
        """
        self.mcp = mcp_client
        self.workspace_path = workspace_path
        self.approval_manager = approval_manager
        self.hitl_manager = hitl_manager

        # Execution tracking
        self.execution_stack: list[dict] = []  # Track call chain
        self.agent_results: dict[str, Any] = {}  # Store results by agent_name
        self.shared_context: dict[str, Any] = {}  # Shared data between agents

        # Metrics
        self.invocation_count: dict[str, int] = {
            "research": 0,
            "architect": 0,
            "code_indexer": 0,
            "hitl_approvals": 0
        }

        logger.info(f"AgentOrchestrator initialized for workspace: {workspace_path}")

    def _check_circular_invocation(self, agent_name: str, caller: str) -> None:
        """
        Check for circular agent invocations (A calls B calls A).

        Args:
            agent_name: Agent being invoked
            caller: Agent doing the invocation

        Raises:
            CircularInvocationError: If circular invocation detected
        """
        # Build call chain
        call_chain = [entry["agent_name"] for entry in self.execution_stack]
        call_chain.append(agent_name)

        # Check for simple cycles (A → B → A)
        if len(call_chain) >= 2:
            if call_chain[-1] == call_chain[-2]:
                raise CircularInvocationError(
                    f"Circular invocation detected: {' → '.join(call_chain[-3:])}"
                )

        # Check for deeper cycles (A → B → C → A)
        if len(call_chain) >= 3:
            if call_chain[-1] in call_chain[:-1]:
                cycle_start = call_chain.index(call_chain[-1])
                cycle = call_chain[cycle_start:]
                raise CircularInvocationError(
                    f"Circular invocation detected: {' → '.join(cycle)}"
                )

        # Limit stack depth (max 5 levels)
        if len(self.execution_stack) >= 5:
            raise AgentInvocationError(
                f"Maximum invocation depth exceeded (5 levels). "
                f"Call chain: {' → '.join(call_chain)}"
            )

    def _push_execution(self, agent_name: str, caller: str, params: dict) -> None:
        """Push agent invocation to execution stack"""
        self.execution_stack.append({
            "agent_name": agent_name,
            "caller": caller,
            "params": params,
            "timestamp": datetime.now().isoformat(),
            "depth": len(self.execution_stack)
        })
        logger.debug(
            f"Execution stack push: {caller} → {agent_name} "
            f"(depth={len(self.execution_stack)})"
        )

    def _pop_execution(self) -> dict:
        """Pop agent invocation from execution stack"""
        if self.execution_stack:
            entry = self.execution_stack.pop()
            logger.debug(
                f"Execution stack pop: {entry['caller']} ← {entry['agent_name']} "
                f"(depth={len(self.execution_stack)})"
            )
            return entry
        return {}

    async def invoke_research(
        self,
        query: str,
        mode: str,
        caller: str,
        context: Optional[dict] = None
    ) -> dict:
        """
        Invoke Research agent dynamically.

        Args:
            query: Research query or task description
            mode: Research mode ("research", "explain", "analyze", "index")
            caller: Name of calling agent
            context: Additional context to pass to research agent

        Returns:
            dict with keys:
                - success: bool
                - result: str (research output)
                - sources: list[dict] (optional)
                - metrics: dict (execution metrics)

        Raises:
            CircularInvocationError: If circular invocation detected
            AgentInvocationError: If invocation fails
        """
        # Validate mode
        valid_modes = ["research", "explain", "analyze", "index"]
        if mode not in valid_modes:
            raise AgentInvocationError(
                f"Invalid research mode: {mode}. Valid modes: {valid_modes}"
            )

        # Check for circular invocation
        self._check_circular_invocation("research", caller)

        # Track invocation
        self._push_execution("research", caller, {
            "query": query,
            "mode": mode,
            "context_keys": list(context.keys()) if context else []
        })
        self.invocation_count["research"] += 1

        try:
            logger.info(f"🔬 {caller} → Research (mode={mode})")
            logger.debug(f"Research query: {query[:100]}...")

            # Import research subgraph
            from backend.subgraphs.research_subgraph_v6_1 import (
                create_research_subgraph,
                ResearchState
            )

            # Prepare state
            state = ResearchState(
                query=query,
                mode=mode,
                context=json.dumps(context) if context else "{}",
                workspace_path=self.workspace_path,
                research_result="",
                sources=[],
                retry_count=0
            )

            # Create and execute subgraph
            subgraph = create_research_subgraph(self.mcp)
            result_state = await subgraph.ainvoke(state)

            # Store result
            result = {
                "success": True,
                "result": result_state.get("research_result", ""),
                "sources": result_state.get("sources", []),
                "mode": mode,
                "metrics": {
                    "query_length": len(query),
                    "result_length": len(result_state.get("research_result", "")),
                    "source_count": len(result_state.get("sources", [])),
                    "retry_count": result_state.get("retry_count", 0)
                }
            }

            # Store in shared context
            self.agent_results[f"research_{mode}_{len(self.execution_stack)}"] = result
            self.shared_context[f"last_research_{mode}"] = result["result"]

            logger.info(
                f"✅ Research completed: {len(result['result'])} chars, "
                f"{len(result['sources'])} sources"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Research invocation failed: {e}")
            raise AgentInvocationError(f"Research invocation failed: {e}") from e

        finally:
            self._pop_execution()

    async def invoke_architect(
        self,
        task: str,
        mode: str,
        caller: str,
        design_input: Optional[dict] = None
    ) -> dict:
        """
        Invoke Architect agent dynamically.

        Args:
            task: Architecture task description
            mode: Architect mode ("scan", "design", "post_build_scan", "re_scan")
            caller: Name of calling agent
            design_input: Design input for architecture generation

        Returns:
            dict with keys:
                - success: bool
                - design: dict (architecture design)
                - system_snapshot: str (path to architecture.md, if saved)
                - metrics: dict (execution metrics)

        Raises:
            CircularInvocationError: If circular invocation detected
            AgentInvocationError: If invocation fails
        """
        # Validate mode
        valid_modes = ["scan", "design", "post_build_scan", "re_scan"]
        if mode not in valid_modes:
            raise AgentInvocationError(
                f"Invalid architect mode: {mode}. Valid modes: {valid_modes}"
            )

        # Check for circular invocation
        self._check_circular_invocation("architect", caller)

        # Track invocation
        self._push_execution("architect", caller, {
            "task": task,
            "mode": mode,
            "design_input_keys": list(design_input.keys()) if design_input else []
        })
        self.invocation_count["architect"] += 1

        try:
            logger.info(f"🏗️  {caller} → Architect (mode={mode})")
            logger.debug(f"Architecture task: {task[:100]}...")

            # Import architect subgraph
            from backend.subgraphs.architect_subgraph_v6_3 import (
                create_architect_subgraph,
                ArchitectState
            )

            # Prepare state
            state = ArchitectState(
                mode=mode,
                user_query=task,
                workspace_path=self.workspace_path,
                design_input=design_input or {},
                design="",
                retry_count=0
            )

            # Create and execute subgraph
            subgraph = create_architect_subgraph(self.mcp)
            result_state = await subgraph.ainvoke(state)

            # Store result
            result = {
                "success": True,
                "design": result_state.get("design", ""),
                "system_snapshot": result_state.get("system_snapshot_path"),
                "mode": mode,
                "metrics": {
                    "task_length": len(task),
                    "design_length": len(result_state.get("design", "")),
                    "retry_count": result_state.get("retry_count", 0)
                }
            }

            # Store in shared context
            self.agent_results[f"architect_{mode}_{len(self.execution_stack)}"] = result
            self.shared_context[f"last_architect_{mode}"] = result["design"]

            logger.info(
                f"✅ Architect completed: {len(result['design'])} chars, "
                f"mode={mode}"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Architect invocation failed: {e}")
            raise AgentInvocationError(f"Architect invocation failed: {e}") from e

        finally:
            self._pop_execution()

    async def invoke_code_indexer(
        self,
        caller: str,
        file_patterns: Optional[list[str]] = None
    ) -> dict:
        """
        Invoke Code Indexer using tree-sitter MCP.

        This uses Research agent in "index" mode for code analysis.

        Args:
            caller: Name of calling agent
            file_patterns: Optional file patterns to index (e.g., ["**/*.py"])

        Returns:
            dict with keys:
                - success: bool
                - index: dict (code structure)
                - metrics: dict (file counts, LOC, etc.)

        Raises:
            AgentInvocationError: If indexing fails
        """
        # Track invocation
        self.invocation_count["code_indexer"] += 1

        try:
            logger.info(f"📑 {caller} → Code Indexer")

            # Use Research agent with mode="index"
            patterns_str = json.dumps(file_patterns) if file_patterns else "default"

            result = await self.invoke_research(
                query=f"Index code structure for workspace: {self.workspace_path}",
                mode="index",
                caller=caller,
                context={"file_patterns": file_patterns or []}
            )

            logger.info("✅ Code indexing completed")
            return result

        except Exception as e:
            logger.error(f"❌ Code indexer invocation failed: {e}")
            raise AgentInvocationError(f"Code indexer invocation failed: {e}") from e

    async def request_hitl_approval(
        self,
        agent_name: str,
        decision: str,
        context: dict,
        timeout_seconds: int = 300
    ) -> dict:
        """
        Request Human-in-the-Loop approval for a decision.

        Args:
            agent_name: Name of agent requesting approval
            decision: Decision description (e.g., "Generate 15 files", "Refactor module X")
            context: Context data for the decision
            timeout_seconds: Timeout in seconds (default: 5 minutes)

        Returns:
            dict with keys:
                - approved: bool
                - feedback: str (optional human feedback)
                - auto_approved: bool (if auto-approval triggered)

        Raises:
            AgentInvocationError: If HITL manager not available
        """
        if not self.hitl_manager:
            raise AgentInvocationError(
                "HITL Manager not available. Cannot request approval."
            )

        # Track invocation
        self.invocation_count["hitl_approvals"] += 1

        try:
            logger.info(f"👤 {agent_name} → HITL Approval: {decision}")

            # Request approval via HITLManager
            approval_result = await self.hitl_manager.request_approval(
                task_id=f"{agent_name}_{len(self.execution_stack)}",
                agent_name=agent_name,
                decision=decision,
                context=context,
                timeout_seconds=timeout_seconds
            )

            if approval_result["approved"]:
                logger.info("✅ HITL Approval granted")
            else:
                logger.warning("❌ HITL Approval denied")

            return approval_result

        except Exception as e:
            logger.error(f"❌ HITL approval request failed: {e}")
            raise AgentInvocationError(f"HITL approval request failed: {e}") from e

    def update_shared_context(self, key: str, value: Any) -> None:
        """
        Update shared context available to all agents.

        Args:
            key: Context key
            value: Context value
        """
        self.shared_context[key] = value
        logger.debug(f"Shared context updated: {key}")

    def get_shared_context(self, key: str, default: Any = None) -> Any:
        """
        Get value from shared context.

        Args:
            key: Context key
            default: Default value if key not found

        Returns:
            Context value or default
        """
        return self.shared_context.get(key, default)

    def get_execution_history(self) -> list[dict]:
        """
        Get execution history (call chain).

        Returns:
            List of execution entries (oldest to newest)
        """
        return self.execution_stack.copy()

    def get_metrics(self) -> dict:
        """
        Get orchestrator metrics.

        Returns:
            dict with invocation counts, stack depth, etc.
        """
        return {
            "invocation_count": self.invocation_count.copy(),
            "current_stack_depth": len(self.execution_stack),
            "agent_results_count": len(self.agent_results),
            "shared_context_keys": list(self.shared_context.keys())
        }

    def reset(self) -> None:
        """Reset orchestrator state (clear stacks, results, context)"""
        self.execution_stack.clear()
        self.agent_results.clear()
        self.shared_context.clear()
        self.invocation_count = {
            "research": 0,
            "architect": 0,
            "code_indexer": 0,
            "hitl_approvals": 0
        }
        logger.info("Orchestrator state reset")
