"""
Multi-Agent Orchestrator - LLM-Based Capability Routing System v6.6

This module implements intelligent, LLM-based routing that replaces
keyword-matching with TRUE semantic understanding using GPT-4o-mini.

CRITICAL DIFFERENCES from v6.5:
- v6.5: Keyword matching with weights (fancy pattern matching)
- v6.6: LLM evaluates each agent's capabilities (true semantics)

Key Principles:
1. Agents evaluate using LLM (GPT-4o-mini)
2. TRUE semantic understanding (no keywords!)
3. Parallel agent evaluation for speed (~500ms per agent, 4 parallel = 500ms total)
4. Best strategy selection based on confidence
5. Reasoning transparency for every decision

Architecture:
- Each agent has capabilities JSON definition
- LLM evaluates: "Can this agent help with the task?"
- Returns: JSON with confidence, mode, dependencies, reasoning
- Orchestrator combines proposals into routing decision

Cost Analysis:
- GPT-4o-mini: $0.15/1M input tokens, $0.60/1M output tokens
- Per routing: ~800 tokens = $0.00012 per request
- 1000 requests/day = $0.12/day = $3.60/month

Author: KI AutoAgent Team
Python: 3.13+
Version: v6.6.0-alpha (LLM-based)
Date: 2025-10-20
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path

# Python 3.13: Native types only (no typing imports)
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

# Load environment variables
global_env = Path.home() / ".ki_autoagent" / "config" / ".env"
if global_env.exists():
    load_dotenv(global_env)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class AgentProposal:
    """
    An agent's LLM-based self-evaluation of whether it can help with a task.

    Attributes:
        agent: Agent name (research, architect, codesmith, reviewfix, hitl)
        can_help: Whether this agent believes it can help
        confidence: Confidence level (0.0-1.0) from LLM
        approach: How the agent would tackle the task
        capabilities_match: Which capabilities match the task
        mode: Agent execution mode (if applicable)
        estimated_duration: Estimated time in minutes
        dependencies: Other agents this agent depends on
        parallel_possible: Agents that could run in parallel
        reasoning: WHY the agent thinks it can/cannot help (from LLM)
    """
    agent: str
    can_help: bool
    confidence: float  # 0.0-1.0
    approach: str
    capabilities_match: list[str]
    mode: str | None
    estimated_duration: float
    dependencies: list[str]
    parallel_possible: list[str]
    reasoning: str


@dataclass
class RoutingDecision:
    """
    The orchestrator's decision on which agents to run.

    Attributes:
        strategy: Execution strategy (single, parallel, sequential, clarification)
        agents: List of (agent_name, mode) tuples to execute
        confidence: Overall confidence in this routing decision
        reasoning: WHY this routing was chosen
    """
    strategy: str  # "single" | "parallel" | "sequential" | "clarification"
    agents: list[tuple[str, str | None]]  # [(agent, mode), ...]
    confidence: float
    reasoning: str


# ============================================================================
# AGENT CAPABILITIES DEFINITIONS
# ============================================================================

AGENT_CAPABILITIES = {
    "research": {
        "name": "Research Agent",
        "description": "Gathers information, analyzes code, and performs research tasks",
        "capabilities": [
            "Web search using Perplexity API (research mode)",
            "Analyze and explain existing codebase (explain mode)",
            "Deep code quality and security analysis (analyze mode)",
            "Code structure indexing with tree-sitter (index mode)"
        ],
        "modes": {
            "research": "Search web for new information, best practices, technologies",
            "explain": "Analyze existing code and explain architecture, components, implementation",
            "analyze": "Deep code analysis: quality assessment, security audit, pattern detection",
            "index": "Index code structure for fast lookups"
        },
        "when_to_use": [
            "User wants to UNDERSTAND existing code ('explain', 'show me', 'how does', 'untersuche')",
            "User wants DEEP ANALYSIS ('analyze', 'audit', 'review', 'assess')",
            "User needs NEW INFORMATION from web ('search', 'find', 'best practices')"
        ],
        "when_NOT_to_use": [
            "Creating new projects (use Architect)",
            "Generating code (use Codesmith)",
            "Reviewing generated code (use ReviewFix)"
        ]
    },
    "architect": {
        "name": "Architect Agent",
        "description": "Designs system architecture, creates file structure, plans implementation",
        "capabilities": [
            "Scan existing architecture and verify consistency (scan mode)",
            "Design new architecture from requirements (design mode)",
            "Document system after code generation (post_build_scan mode)",
            "Update architecture after modifications (re_scan mode)"
        ],
        "modes": {
            "scan": "Load existing architecture, verify consistency",
            "design": "Design new architecture or propose updates",
            "post_build_scan": "Document system after code generation",
            "re_scan": "Update architecture after modifications"
        },
        "when_to_use": [
            "User wants to CREATE new project ('create', 'build', 'develop', 'make')",
            "User wants to UPDATE existing project ('update', 'modify', 'add', 'extend')",
            "Explicit architecture requests ('architect', 'design', 'structure', 'plan')"
        ],
        "when_NOT_to_use": [
            "Explaining code (use Research with explain mode)",
            "Analyzing code quality (use Research with analyze mode)",
            "Generating code (use Codesmith)",
            "Fixing bugs (use Codesmith after Research analysis)"
        ]
    },
    "codesmith": {
        "name": "Codesmith Agent",
        "description": "Generates code based on architecture and requirements",
        "capabilities": [
            "Generate code from architecture design",
            "Implement new features based on requirements",
            "Fix bugs identified by Research agent",
            "Automatic model selection (Sonnet 4/4.5/Opus based on complexity)"
        ],
        "modes": {
            "default": "Standard code generation"
        },
        "when_to_use": [
            "User wants code IMPLEMENTATION ('implement', 'code', 'generate', 'write')",
            "Architecture is ready and code needs to be generated",
            "Bug analysis is complete and fix needs implementation"
        ],
        "when_NOT_to_use": [
            "No architecture available (need Architect first)",
            "User wants explanation (use Research)",
            "User wants analysis (use Research)",
            "User wants design (use Architect)"
        ],
        "dependencies": {
            "required": ["architect"],
            "optional": ["research"]
        }
    },
    "reviewfix": {
        "name": "ReviewFix Agent",
        "description": "Reviews code quality, runs build validation, fixes issues",
        "capabilities": [
            "Code quality review using GPT-4o-mini",
            "Multi-language build validation (TypeScript, Python, JavaScript)",
            "Apply fixes automatically",
            "Quality scoring and improvement suggestions"
        ],
        "modes": {
            "default": "Review and fix code"
        },
        "when_to_use": [
            "Code was just generated (MANDATORY by Asimov Rule 1)",
            "Explicit review request ('review', 'check', 'validate', 'test', 'quality')",
            "Build validation needed"
        ],
        "when_NOT_to_use": [
            "No code has been generated yet",
            "User wants explanation (use Research)",
            "User wants new features (use Architect + Codesmith)"
        ],
        "asimov_rule": "MANDATORY after Codesmith generates code (Rule 1)"
    },
    "hitl": {
        "name": "Human-in-the-Loop Agent",
        "description": "Asks user for clarification when confidence is low",
        "capabilities": [
            "Request user clarification",
            "Present options for user to choose",
            "Gather additional requirements"
        ],
        "modes": {
            "default": "Ask user for input"
        },
        "when_to_use": [
            "No agents can help with the query (confidence < 0.5 for all)",
            "Multiple agents have equal confidence",
            "Task is ambiguous or unclear"
        ],
        "when_NOT_to_use": [
            "Clear task with high-confidence agent match",
            "User query is specific and unambiguous"
        ]
    }
}


# ============================================================================
# MULTI-AGENT ORCHESTRATOR
# ============================================================================

class MultiAgentOrchestrator:
    """
    Orchestrates multi-agent routing using LLM-based capability evaluation.

    Each agent is evaluated using GPT-4o-mini which determines:
    - Can this agent help?
    - What's the confidence level?
    - Which mode should be used?
    - What dependencies exist?
    - Can it run in parallel?

    This provides TRUE semantic understanding, not keyword matching!
    """

    def __init__(
        self,
        research_agent,
        architect_agent,
        codesmith_agent,
        reviewfix_agent,
        hitl_agent=None
    ):
        """
        Initialize orchestrator with agent references.

        Args:
            research_agent: Research subgraph instance
            architect_agent: Architect subgraph instance
            codesmith_agent: Codesmith subgraph instance
            reviewfix_agent: ReviewFix subgraph instance
            hitl_agent: HITL subgraph instance (optional)
        """
        self.agents = {
            "research": research_agent,
            "architect": architect_agent,
            "codesmith": codesmith_agent,
            "reviewfix": reviewfix_agent
        }

        if hitl_agent:
            self.agents["hitl"] = hitl_agent

        # Initialize LLM for capability evaluation
        # Python 3.13: No Optional[], just | None
        self.llm: ChatOpenAI | None = None

        try:
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.2,  # Low temperature for consistent evaluations
                max_tokens=500,   # Short responses (JSON only)
                cache=None        # Disable caching (Pydantic v2 compatibility)
            )
            logger.info("🎯 MultiAgentOrchestrator initialized with LLM-based routing (GPT-4o-mini)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM for routing: {e}")
            logger.warning("⚠️  Falling back to capability-less routing")

    async def route_request(
        self,
        user_query: str,
        workspace_path: str,
        context: dict | None = None
    ) -> RoutingDecision:
        """
        Route user request using LLM-based agent evaluation.

        Flow:
        1. Ask ALL agents (via LLM): "Can you help with this task?"
        2. Collect proposals in parallel (~500ms total)
        3. Analyze proposals and determine best strategy
        4. Return routing decision

        Args:
            user_query: User's task description
            workspace_path: Path to workspace
            context: Additional context (existing files, etc.)

        Returns:
            RoutingDecision with strategy and agent list
        """
        logger.info(f"🔍 LLM-based routing for: '{user_query[:100]}'...")

        # Initialize context
        context = context or {}

        # Step 1: Collect proposals from all agents (parallel!)
        logger.info("📞 Asking all agents (via LLM) if they can help...")
        proposals = await self._collect_proposals(user_query, workspace_path, context)

        # Log proposals
        for proposal in proposals:
            status = "✅ CAN HELP" if proposal.can_help else "❌ CANNOT HELP"
            logger.info(
                f"  {status} | {proposal.agent:12s} | "
                f"confidence={proposal.confidence:.2f} | "
                f"mode={proposal.mode or 'N/A':15s} | "
                f"{proposal.reasoning[:60]}"
            )

        # Step 2: Determine routing strategy
        decision = self._determine_routing(proposals, user_query)

        logger.info(f"🎯 Routing decision: {decision.strategy}")
        logger.info(f"   Agents: {' → '.join([f'{a}({m or 'default'})' for a, m in decision.agents])}")
        logger.info(f"   Confidence: {decision.confidence:.2f}")
        logger.info(f"   Reasoning: {decision.reasoning}")

        return decision

    async def _collect_proposals(
        self,
        user_query: str,
        workspace_path: str,
        context: dict
    ) -> list[AgentProposal]:
        """
        Collect LLM-based proposals from all agents in parallel.

        Args:
            user_query: User's task
            workspace_path: Workspace path
            context: Additional context

        Returns:
            List of agent proposals (from LLM)
        """
        # Create evaluation tasks for all agents
        tasks = []
        for agent_name in self.agents.keys():
            task = self._evaluate_agent_with_llm(agent_name, user_query, workspace_path, context)
            tasks.append(task)

        # Run evaluations in parallel (asyncio.gather)
        proposals = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_proposals: list[AgentProposal] = []
        for i, proposal in enumerate(proposals):
            if isinstance(proposal, Exception):
                agent_name = list(self.agents.keys())[i]
                logger.warning(f"  ⚠️  {agent_name} evaluation failed: {proposal}")
            else:
                valid_proposals.append(proposal)

        return valid_proposals

    async def _evaluate_agent_with_llm(
        self,
        agent_name: str,
        user_query: str,
        workspace_path: str,
        context: dict
    ) -> AgentProposal:
        """
        Use LLM (GPT-4o-mini) to evaluate if agent can help.

        This is the KEY DIFFERENCE from v6.5:
        - v6.5: Keyword matching in agent code
        - v6.6: LLM evaluates capabilities

        Args:
            agent_name: Name of the agent
            user_query: User's task
            workspace_path: Workspace path
            context: Additional context

        Returns:
            AgentProposal from LLM evaluation
        """
        # Get agent capabilities
        capabilities = AGENT_CAPABILITIES.get(agent_name)
        if not capabilities:
            logger.warning(f"⚠️  No capabilities defined for {agent_name}")
            return AgentProposal(
                agent=agent_name,
                can_help=False,
                confidence=0.0,
                approach="",
                capabilities_match=[],
                mode=None,
                estimated_duration=0.0,
                dependencies=[],
                parallel_possible=[],
                reasoning=f"No capabilities defined for {agent_name}"
            )

        # Build system prompt
        system_prompt = f"""You are evaluating if the {capabilities['name']} can help with a user's task.

CAPABILITIES:
{json.dumps(capabilities['capabilities'], indent=2)}

MODES:
{json.dumps(capabilities.get('modes', {}), indent=2)}

WHEN TO USE:
{json.dumps(capabilities.get('when_to_use', []), indent=2)}

WHEN NOT TO USE:
{json.dumps(capabilities.get('when_NOT_to_use', []), indent=2)}

Your job: Evaluate if this agent can help with the task.

Return ONLY valid JSON matching this schema:
{{
    "can_help": true/false,
    "confidence": 0.0-1.0,
    "mode": "mode_name or null",
    "approach": "how agent would tackle the task",
    "capabilities_match": ["list", "of", "matching", "capabilities"],
    "dependencies": ["list", "of", "required", "agents"],
    "parallel_possible": ["list", "of", "agents", "can", "run", "parallel"],
    "reasoning": "explain WHY you can/cannot help (be specific!)"
}}

CRITICAL:
- Be honest about capabilities
- If task doesn't match, return can_help=false
- Choose correct mode based on task intent
- Explain reasoning clearly"""

        # Build user prompt
        user_prompt = f"""Task: {user_query}

Workspace: {workspace_path}
Context: {json.dumps(context, indent=2)}

Can {capabilities['name']} help with this task?"""

        # Call LLM
        # Python 3.13 Best Practices: Initialize variables BEFORE try
        response_content: str | None = None
        proposal_data: dict | None = None

        try:
            if not self.llm:
                raise RuntimeError("LLM not initialized")

            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            response_content = response.content.strip()

            # Extract JSON (handle markdown code blocks)
            if "```json" in response_content:
                json_start = response_content.find("```json") + 7
                json_end = response_content.find("```", json_start)
                if json_end != -1:
                    response_content = response_content[json_start:json_end].strip()
            elif "```" in response_content:
                json_start = response_content.find("```") + 3
                json_end = response_content.find("```", json_start)
                if json_end != -1:
                    response_content = response_content[json_start:json_end].strip()

            # Parse JSON
            proposal_data = json.loads(response_content)

            # Convert to AgentProposal
            return AgentProposal(
                agent=agent_name,
                can_help=proposal_data.get("can_help", False),
                confidence=float(proposal_data.get("confidence", 0.0)),
                approach=proposal_data.get("approach", ""),
                capabilities_match=proposal_data.get("capabilities_match", []),
                mode=proposal_data.get("mode"),
                estimated_duration=float(proposal_data.get("estimated_duration", 5.0)),
                dependencies=proposal_data.get("dependencies", []),
                parallel_possible=proposal_data.get("parallel_possible", []),
                reasoning=proposal_data.get("reasoning", "No reasoning provided")
            )

        except json.JSONDecodeError as e:
            logger.error(f"❌ {agent_name}: Invalid JSON from LLM: {e}")
            logger.error(f"   Response: {response_content[:200] if response_content else 'None'}")
            return AgentProposal(
                agent=agent_name,
                can_help=False,
                confidence=0.0,
                approach="",
                capabilities_match=[],
                mode=None,
                estimated_duration=0.0,
                dependencies=[],
                parallel_possible=[],
                reasoning=f"LLM returned invalid JSON: {str(e)}"
            )

        except Exception as e:
            logger.error(f"❌ {agent_name}: LLM evaluation failed: {e}")
            return AgentProposal(
                agent=agent_name,
                can_help=False,
                confidence=0.0,
                approach="",
                capabilities_match=[],
                mode=None,
                estimated_duration=0.0,
                dependencies=[],
                parallel_possible=[],
                reasoning=f"Evaluation error: {str(e)}"
            )

    def _determine_routing(
        self,
        proposals: list[AgentProposal],
        user_query: str
    ) -> RoutingDecision:
        """
        Analyze LLM proposals and determine best routing strategy.

        Logic:
        1. If NO agents can help → HITL for clarification
        2. If ONE agent can help → single agent
        3. If MULTIPLE agents can help:
           - Check dependencies → sequential if needed
           - Check parallel_possible → parallel if possible
           - Otherwise → sequential by confidence

        Args:
            proposals: Agent proposals from LLM
            user_query: Original query

        Returns:
            RoutingDecision
        """
        # Filter agents that can help
        helpful_agents = [p for p in proposals if p.can_help]

        if len(helpful_agents) == 0:
            # No agents can help - route to HITL
            logger.warning("⚠️  No agents can help, routing to HITL for clarification")
            return RoutingDecision(
                strategy="clarification",
                agents=[("hitl", None)],
                confidence=0.0,
                reasoning="No agents matched task requirements. Requesting user clarification via HITL."
            )

        if len(helpful_agents) == 1:
            # Single agent routing
            agent = helpful_agents[0]
            logger.info(f"✅ Single agent routing: {agent.agent}")
            return RoutingDecision(
                strategy="single",
                agents=[(agent.agent, agent.mode)],
                confidence=agent.confidence,
                reasoning=f"{agent.agent} is the best match: {agent.reasoning}"
            )

        # Multiple agents - determine strategy
        logger.info(f"🔀 Multiple agents can help ({len(helpful_agents)}), determining strategy...")

        # Sort by confidence
        helpful_agents.sort(key=lambda p: p.confidence, reverse=True)

        # Check for parallelization
        top_agent = helpful_agents[0]
        parallel_candidates: list[AgentProposal] = []

        for other_agent in helpful_agents[1:]:
            if (top_agent.agent in other_agent.parallel_possible or
                other_agent.agent in top_agent.parallel_possible):
                parallel_candidates.append(other_agent)

        if parallel_candidates:
            # Parallel execution
            agents_to_run = [(top_agent.agent, top_agent.mode)]
            agents_to_run.extend([(p.agent, p.mode) for p in parallel_candidates])

            avg_confidence = sum([top_agent.confidence] + [p.confidence for p in parallel_candidates]) / len(agents_to_run)

            return RoutingDecision(
                strategy="parallel",
                agents=agents_to_run,
                confidence=avg_confidence,
                reasoning=f"Running {len(agents_to_run)} agents in parallel: {', '.join([a for a, _ in agents_to_run])}"
            )

        # Sequential execution (dependencies)
        ordered_agents = self._order_by_dependencies(helpful_agents)

        return RoutingDecision(
            strategy="sequential",
            agents=[(p.agent, p.mode) for p in ordered_agents],
            confidence=sum(p.confidence for p in ordered_agents) / len(ordered_agents),
            reasoning=f"Sequential execution: {' → '.join([p.agent for p in ordered_agents])}"
        )

    def _order_by_dependencies(self, proposals: list[AgentProposal]) -> list[AgentProposal]:
        """
        Order agents by dependencies (topological sort).

        Args:
            proposals: List of agent proposals

        Returns:
            Ordered list of proposals
        """
        # Track processed
        ordered: list[AgentProposal] = []
        processed: set[str] = set()

        # Agents with no dependencies first
        for proposal in proposals:
            if not proposal.dependencies:
                ordered.append(proposal)
                processed.add(proposal.agent)

        # Remaining agents
        remaining = [p for p in proposals if p.agent not in processed]
        max_iterations = len(remaining) + 1
        iteration = 0

        while remaining and iteration < max_iterations:
            iteration += 1
            made_progress = False

            for proposal in remaining[:]:
                deps_satisfied = all(dep in processed for dep in proposal.dependencies)

                if deps_satisfied:
                    ordered.append(proposal)
                    processed.add(proposal.agent)
                    remaining.remove(proposal)
                    made_progress = True

            if not made_progress:
                # Circular dependencies - add by confidence
                logger.warning("⚠️  Circular dependencies detected")
                remaining.sort(key=lambda p: p.confidence, reverse=True)
                ordered.extend(remaining)
                break

        return ordered


# Export
__all__ = ["AgentProposal", "RoutingDecision", "MultiAgentOrchestrator", "AGENT_CAPABILITIES"]
