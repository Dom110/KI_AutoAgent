"""
Research Capability System for All Agents
Allows any agent to request research during execution

This module provides unified research capability:
- Any agent can request research via MCP
- GPT-4o-mini determines if research is needed (intelligent mode)
- User can force research (explicit mode)
- Integrates with research_subgraph_v6_1.py
- Returns structured research results

Author: KI AutoAgent Team
Version: 1.0.0
Date: 2025-10-14
"""

from __future__ import annotations

import logging
from typing import Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ResearchCapability:
    """
    Provides research capability to all agents.

    Usage:
        research = ResearchCapability()

        # Check if research needed
        should_research = await research.should_research(
            task="Build authentication system",
            agent="codesmith",
            mcp_client=mcp
        )

        # Perform research
        if should_research:
            result = await research.perform_research(
                query="Best practices for JWT authentication in FastAPI",
                mcp_client=mcp
            )
    """

    def __init__(self):
        """Initialize Research Capability."""
        logger.debug("🔬 ResearchCapability initialized")

    async def should_research(
        self,
        task: str,
        agent: str,
        context: dict[str, Any] | None = None,
        forced: bool = False,
        mcp_client: Any = None
    ) -> dict[str, Any]:
        """
        Determine if research is needed for a task.

        Args:
            task: Task description
            agent: Agent requesting research
            context: Additional context (workspace, existing knowledge, etc.)
            forced: User explicitly requested research
            mcp_client: MCP client for calling GPT-4o-mini

        Returns:
            {
                "should_research": bool,
                "confidence": 0.0-1.0,
                "reasons": ["reason1", "reason2"],
                "suggested_queries": ["query1", "query2"],
                "mode": "forced|intelligent|skip"
            }
        """
        logger.info(f"🤔 Evaluating research need for {agent} task...")

        # If user forced research, skip analysis
        if forced:
            return {
                "should_research": True,
                "confidence": 1.0,
                "reasons": ["User explicitly requested research"],
                "suggested_queries": [task],
                "mode": "forced"
            }

        # Use GPT-4o-mini to intelligently determine need
        if mcp_client is None:
            logger.warning("⚠️  No MCP client provided, using heuristic detection")
            return await self._heuristic_research_check(task, agent)

        try:
            analysis_prompt = self._build_research_analysis_prompt(
                task=task,
                agent=agent,
                context=context
            )

            result = await mcp_client.call(
                server="claude",
                tool="claude_generate",
                arguments={
                    "prompt": analysis_prompt,
                    "system_prompt": self._get_research_system_prompt(),
                    "workspace_path": context.get("workspace_path", "") if context else "",
                    "agent_name": "research_evaluator",
                    "temperature": 0.2,
                    "max_tokens": 512,
                    "tools": [],
                    "model": "gpt-4o-mini"
                },
                timeout=20.0
            )

            # Parse result
            decision = self._parse_research_decision(result)
            decision["mode"] = "intelligent"

            logger.info(
                f"✅ Research decision: should_research={decision['should_research']}, "
                f"confidence={decision['confidence']:.2f}"
            )

            return decision

        except Exception as e:
            logger.error(f"❌ Research evaluation failed: {e}")
            return await self._heuristic_research_check(task, agent)

    async def perform_research(
        self,
        query: str,
        context: dict[str, Any] | None = None,
        mcp_client: Any = None
    ) -> dict[str, Any]:
        """
        Perform research using research subgraph.

        Args:
            query: Research query
            context: Additional context
            mcp_client: MCP client

        Returns:
            {
                "success": bool,
                "results": {
                    "perplexity": {...},
                    "analysis": "..."
                },
                "sources": ["url1", "url2"],
                "summary": "...",
                "duration_ms": 12345
            }
        """
        logger.info(f"🔬 Starting research: {query[:100]}...")

        if mcp_client is None:
            logger.error("❌ Cannot perform research without MCP client")
            return {
                "success": False,
                "error": "No MCP client provided",
                "results": {},
                "sources": [],
                "summary": "",
                "duration_ms": 0
            }

        try:
            start = datetime.now()

            # Import research subgraph
            from backend.subgraphs.research_subgraph_v6_1 import research_subgraph

            # Prepare state
            from backend.state.state_v6 import ResearchState

            state = ResearchState(
                query=query,
                mode="research",  # Research mode for web search
                context=context or {},
                workspace_path=context.get("workspace_path", "") if context else ""
            )

            # Run research
            result_state = await research_subgraph(state, mcp_client)

            duration_ms = (datetime.now() - start).total_seconds() * 1000

            # Extract results
            perplexity_result = result_state.get("perplexity_result", {})
            claude_analysis = result_state.get("claude_analysis", "")
            sources = result_state.get("sources", [])

            # Generate summary
            summary = self._generate_summary(perplexity_result, claude_analysis)

            logger.info(f"✅ Research complete: {len(sources)} sources, {duration_ms:.0f}ms")

            return {
                "success": True,
                "results": {
                    "perplexity": perplexity_result,
                    "analysis": claude_analysis
                },
                "sources": sources,
                "summary": summary,
                "duration_ms": int(duration_ms)
            }

        except Exception as e:
            logger.error(f"❌ Research failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": {},
                "sources": [],
                "summary": "",
                "duration_ms": 0
            }

    async def batch_research(
        self,
        queries: list[str],
        context: dict[str, Any] | None = None,
        mcp_client: Any = None
    ) -> list[dict[str, Any]]:
        """
        Perform multiple research queries in parallel.

        Args:
            queries: List of research queries
            context: Additional context
            mcp_client: MCP client

        Returns:
            List of research results (same format as perform_research)
        """
        logger.info(f"🔬 Batch research: {len(queries)} queries")

        import asyncio

        # Run all queries in parallel
        tasks = [
            self.perform_research(query, context, mcp_client)
            for query in queries
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error dicts
        formatted_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                formatted_results.append({
                    "success": False,
                    "error": str(result),
                    "results": {},
                    "sources": [],
                    "summary": "",
                    "duration_ms": 0,
                    "query": queries[i]
                })
            else:
                result["query"] = queries[i]
                formatted_results.append(result)

        success_count = sum(1 for r in formatted_results if r.get("success"))
        logger.info(f"✅ Batch research complete: {success_count}/{len(queries)} successful")

        return formatted_results

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _get_research_system_prompt(self) -> str:
        """Get system prompt for research need evaluation."""
        return """You are a research need evaluator analyzing if a task requires web research.

Your task: Determine if research would be helpful for completing this task.

Consider:
1. **Novelty**: Is this about new/emerging technology?
2. **Best Practices**: Are there evolving best practices to check?
3. **Unfamiliar Domain**: Is this outside common programming knowledge?
4. **Security/Performance**: Does this involve security or performance-critical decisions?
5. **Library/API Choice**: Does this require choosing between multiple options?

Research is NOT needed for:
- Basic CRUD operations
- Standard patterns (MVC, REST, etc.)
- Well-known algorithms
- Simple data structures
- Common language features

Return JSON:
{
    "should_research": true/false,
    "confidence": 0.0-1.0,
    "reasons": ["reason1", "reason2"],
    "suggested_queries": ["specific query1", "specific query2"]
}

Be conservative. Only suggest research if it would materially improve the outcome."""

    def _build_research_analysis_prompt(
        self,
        task: str,
        agent: str,
        context: dict[str, Any] | None
    ) -> str:
        """Build prompt for research need analysis."""
        prompt = f"""Should we perform web research for this task?

AGENT: {agent}

TASK:
{task}
"""

        if context:
            prompt += f"\n\nCONTEXT:\n"
            if "tech_stack" in context:
                prompt += f"Tech Stack: {', '.join(context['tech_stack'])}\n"
            if "existing_system" in context:
                prompt += f"Existing System: {context['existing_system']}\n"
            if "workspace_path" in context:
                prompt += f"Workspace: {context['workspace_path']}\n"

        prompt += "\n\nProvide decision in JSON format."

        return prompt

    def _parse_research_decision(self, result: dict[str, Any]) -> dict[str, Any]:
        """Parse GPT-4o-mini research decision."""
        try:
            # Extract response text
            response_text = result.get("response", {}).get("content", [{}])[0].get("text", "")

            # Try to extract JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "{" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_text = response_text[json_start:json_end]
            else:
                raise ValueError("No JSON found in response")

            decision = json.loads(json_text)

            # Validate structure
            if "should_research" not in decision:
                decision["should_research"] = False

            if "confidence" not in decision:
                decision["confidence"] = 0.5

            if "reasons" not in decision:
                decision["reasons"] = []

            if "suggested_queries" not in decision:
                decision["suggested_queries"] = []

            return decision

        except Exception as e:
            logger.error(f"❌ Failed to parse research decision: {e}")
            return {
                "should_research": False,
                "confidence": 0.0,
                "reasons": ["Failed to parse decision"],
                "suggested_queries": [],
                "error": str(e)
            }

    async def _heuristic_research_check(
        self,
        task: str,
        agent: str
    ) -> dict[str, Any]:
        """
        Fallback heuristic research check (no AI).

        Simple keyword matching for research-worthy topics.
        """
        logger.debug("Using heuristic research check")

        research_keywords = [
            # Technology-specific
            "kubernetes", "docker", "aws", "azure", "gcp",
            "react", "vue", "angular", "svelte",
            "tensorflow", "pytorch", "machine learning",
            "blockchain", "web3", "nft",

            # Patterns suggesting research
            "best practice", "best way", "optimal",
            "latest", "newest", "current",
            "comparison", "vs", "versus", "compare",
            "security", "vulnerability", "exploit",
            "performance", "optimization", "benchmark",
            "scalability", "architecture pattern",

            # Uncertainty phrases
            "how to", "what is", "which",
            "recommend", "suggestion", "advice"
        ]

        task_lower = task.lower()

        matches = []
        for keyword in research_keywords:
            if keyword in task_lower:
                matches.append(keyword)

        should_research = len(matches) >= 2  # Need at least 2 matches
        confidence = min(1.0, len(matches) * 0.3)  # 0.3 per match, max 1.0

        return {
            "should_research": should_research,
            "confidence": confidence,
            "reasons": [f"Found research keyword: '{kw}'" for kw in matches[:3]],
            "suggested_queries": [task] if should_research else [],
            "mode": "heuristic"
        }

    def _generate_summary(
        self,
        perplexity_result: dict[str, Any],
        claude_analysis: str
    ) -> str:
        """Generate concise summary of research results."""
        # Extract key points from Claude analysis
        if claude_analysis:
            lines = claude_analysis.split("\n")
            # Take first 3 non-empty lines
            summary_lines = [line.strip() for line in lines if line.strip()][:3]
            return " ".join(summary_lines)

        # Fallback to perplexity summary
        if perplexity_result:
            return perplexity_result.get("summary", "Research completed")

        return "Research completed"
