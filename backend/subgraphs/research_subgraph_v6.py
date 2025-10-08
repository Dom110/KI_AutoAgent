"""
v6.0 Research Subgraph

Purpose: Web research, documentation gathering using Perplexity API
Architecture: create_react_agent() with perplexity_search tool
Documentation: V6_0_ARCHITECTURE.md, V6_0_MIGRATION_PLAN.md

Integration:
- Memory: Stores findings with tags ["research", "documentation"]
- Asimov: Permission can_web_search (TODO: Phase 8)
- Learning: Stores successful search queries (TODO: Phase 8)
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from datetime import datetime

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, END

from state_v6 import ResearchState
from memory.memory_system_v6 import MemorySystem
from tools.perplexity_tool import perplexity_search

logger = logging.getLogger(__name__)


def create_research_subgraph(
    workspace_path: str,
    memory: MemorySystem | None = None
) -> StateGraph:
    """
    Create Research Subgraph using create_react_agent().

    Args:
        workspace_path: Path to user workspace
        memory: Optional Memory System (for storing findings)

    Returns:
        Compiled StateGraph (ResearchSubgraph)

    Architecture:
        1. Entry: research_node (create_react_agent wrapper)
        2. Agent uses perplexity_search tool
        3. Results stored in Memory
        4. Exit: report generated
    """

    # LLM and Tools will be lazily initialized in node
    # (Avoids API key validation at graph compile time)
    tools = [perplexity_search]

    # System prompt for Research Agent
    state_modifier_content = """You are a research agent specialized in web research and documentation gathering.

Your responsibilities:
1. Conduct thorough web research using the perplexity_search tool
2. Find best practices, documentation, and recent information
3. Synthesize findings into a structured report
4. Cite all sources

Output format:
- Findings: Key insights as structured dict
- Sources: List of URLs cited
- Report: Markdown-formatted research summary

Be thorough but concise. Focus on actionable insights."""

    # Wrap agent with pre/post hooks
    async def research_node(state: ResearchState) -> ResearchState:
        """
        Research node with Memory integration.

        Flow:
        1. Create LLM and ReAct agent (lazy)
        2. Invoke ReAct agent with query
        3. Extract findings from agent response
        4. Store in Memory (if provided)
        5. Return updated state
        """
        logger.info(f"🔍 Research node executing: {state['query']}")

        try:
            # Lazy initialize LLM and agent (only when actually invoked)
            logger.debug("Initializing LLM and ReAct agent...")
            llm = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                temperature=0.3,
                max_tokens=4096
            )

            react_agent = create_react_agent(
                model=llm,
                tools=tools,
                state_modifier=SystemMessage(content=state_modifier_content)
            )
            logger.debug("✅ ReAct agent created")

            # Prepare input for ReAct agent
            agent_input = {
                "messages": [
                    HumanMessage(content=f"Research: {state['query']}")
                ]
            }

            # Invoke agent
            logger.info("🤖 Invoking create_react_agent...")
            result = await react_agent.ainvoke(agent_input)

            # Extract findings from agent response
            # Agent returns: {"messages": [...]}
            last_message = result["messages"][-1]
            response_text = last_message.content if hasattr(last_message, 'content') else str(last_message)

            logger.info(f"✅ Agent response: {response_text[:200]}...")

            # Parse response (TODO: improve parsing)
            findings = {
                "raw_response": response_text,
                "timestamp": datetime.now().isoformat()
            }

            sources = []  # TODO: Extract from tool calls

            # Generate report
            report = f"""# Research Report

**Query:** {state['query']}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Findings

{response_text}

## Sources

{chr(10).join(f'- {src}' for src in sources) if sources else 'No sources cited'}
"""

            # Store in Memory (if provided)
            if memory:
                logger.info("💾 Storing findings in Memory...")
                await memory.store(
                    content=response_text,
                    metadata={
                        "agent": "research",
                        "type": "findings",
                        "query": state["query"],
                        "timestamp": datetime.now().isoformat()
                    }
                )
                logger.info("✅ Stored in Memory")

            # Update state
            return {
                **state,
                "findings": findings,
                "sources": sources,
                "report": report,
                "errors": state.get("errors", [])
            }

        except Exception as e:
            logger.error(f"❌ Research node failed: {e}", exc_info=True)
            return {
                **state,
                "findings": {},
                "sources": [],
                "report": "",
                "errors": [
                    *state.get("errors", []),
                    {
                        "node": "research",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            }

    # Build subgraph
    subgraph = StateGraph(ResearchState)
    subgraph.add_node("research", research_node)
    subgraph.set_entry_point("research")
    subgraph.add_edge("research", END)

    return subgraph.compile()


# Convenience export
__all__ = ["create_research_subgraph"]
