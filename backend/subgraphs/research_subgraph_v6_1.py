"""
Research Subgraph v6.1 - Custom Node Implementation

This is a refactored version that doesn't use create_react_agent,
allowing it to work with Claude CLI adapter.

Changes from v6.0:
- Removed create_react_agent (incompatible with async-only LLMs)
- Direct LLM.ainvoke() calls (like Architect pattern)
- Manual tool calling for Perplexity (simplified)
- Works with ClaudeCLISimple adapter

Author: KI AutoAgent Team
Python: 3.13+
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

# Use ClaudeCLISimple instead of langchain-anthropic (broken)
from adapters.claude_cli_simple import ClaudeCLISimple as ChatAnthropic
from state_v6 import ResearchState
from tools.perplexity_tool import perplexity_search

logger = logging.getLogger(__name__)


def create_research_subgraph(
    workspace_path: str,
    memory: Any | None = None,
    hitl_callback: Any | None = None
) -> Any:
    """
    Create Research subgraph with custom node implementation.

    This version uses direct LLM calls instead of create_react_agent,
    making it compatible with async-only LLMs like ClaudeCLISimple.

    Args:
        workspace_path: Path to workspace
        memory: Memory system instance (optional)
        hitl_callback: Optional HITL callback for debug info

    Returns:
        Compiled research subgraph
    """
    logger.debug("Creating Research subgraph v6.1 (custom node)...")

    # Research node function
    async def research_node(state: ResearchState) -> ResearchState:
        """
        Execute research with custom implementation.

        Flow:
        1. Use Perplexity to search for information
        2. Use Claude to analyze and summarize findings
        3. Store in Memory
        4. Return results
        """
        print(f"🔍 === RESEARCH SUBGRAPH START ===")
        logger.info(f"🔍 Research node v6.1 executing: {state['query']}")

        try:
            # Step 1: Search with Perplexity
            print(f"  Step 1: Calling Perplexity...")
            logger.info("🌐 Searching with Perplexity...")
            search_result = await perplexity_search.ainvoke({"query": state['query']})
            print(f"  Step 1: Perplexity returned {type(search_result)}")

            # LOG COMPLETE PERPLEXITY OUTPUT
            import json
            with open("/tmp/perplexity_output.json", "w") as f:
                json.dump(search_result, f, indent=2)
            print(f"  📝 Perplexity complete output: /tmp/perplexity_output.json")

            search_findings = search_result.get("content", "No results found")
            print(f"  Step 1: Got {len(search_findings)} chars")
            logger.info(f"✅ Perplexity results: {len(search_findings)} chars")

            # Step 2: Analyze with Claude
            print(f"  Step 2: Creating Claude LLM...")
            logger.info("🤖 Analyzing findings with Claude...")

            llm = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                temperature=0.3,
                max_tokens=4096,
                agent_name="research",
                agent_description="Research analyst specializing in software development and technology",
                agent_tools=["Read", "Bash"],  # Read for context, Bash for utilities (NOT Edit - no file creation needed)
                permission_mode="acceptEdits",  # Not strictly needed but harmless
                hitl_callback=hitl_callback  # Pass HITL callback for debug info
            )
            print(f"  Step 2: LLM created, calling Claude CLI...")

            system_prompt = """You are a research analyst specializing in software development.

Your responsibilities:
1. Analyze search results and extract key insights
2. Identify relevant technologies, patterns, and best practices
3. Summarize findings concisely
4. Provide actionable recommendations

Output format:
- Key Findings: Main insights from the research
- Technologies: Relevant tools/frameworks mentioned
- Best Practices: Recommended approaches
- Sources: Where the information came from"""

            user_prompt = f"""Analyze the following research results:

**Query:** {state['query']}

**Search Results:**
{search_findings}

Provide a structured summary of the key findings."""

            # LOG PROMPTS FOR DEBUGGING
            with open("/tmp/claude_system_prompt.txt", "w") as f:
                f.write(system_prompt)
            with open("/tmp/claude_user_prompt.txt", "w") as f:
                f.write(user_prompt)
            print(f"  📝 System prompt: /tmp/claude_system_prompt.txt ({len(system_prompt)} chars)")
            print(f"  📝 User prompt: /tmp/claude_user_prompt.txt ({len(user_prompt)} chars)")

            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            print(f"  Step 2: Claude returned {type(response)}")

            analysis = response.content if hasattr(response, 'content') else str(response)
            print(f"  Step 2: Analysis complete: {len(analysis)} chars")
            logger.info(f"✅ Analysis complete: {len(analysis)} chars")

            # Step 3: Create research report
            report = f"""# Research Report

**Query:** {state['query']}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Analysis

{analysis}

## Raw Search Results

{search_findings[:500]}...

---
*Generated by Research Agent v6.1*
"""

            findings = {
                "analysis": analysis,
                "raw_results": search_findings,
                "timestamp": datetime.now().isoformat()
            }

            # Step 4: Store in Memory (if available)
            print(f"  Step 3: Memory store...")
            if memory:
                print(f"  Step 3: Storing in memory...")
                logger.info("💾 Storing findings in Memory...")
                await memory.store(
                    content=analysis,
                    metadata={
                        "agent": "research",
                        "type": "findings",
                        "query": state['query'],
                        "timestamp": findings["timestamp"]
                    }
                )
                print(f"  Step 3: Memory stored")
                logger.debug("✅ Findings stored in Memory")
            else:
                print(f"  Step 3: No memory, skipping")

            # Return updated state
            print(f"  Step 4: Returning state")
            return {
                **state,
                "findings": findings,
                "report": report,
                "completed": True,
                "errors": []
            }

        except Exception as e:
            logger.error(f"❌ Research node failed: {e}", exc_info=True)

            return {
                **state,
                "findings": None,
                "report": f"Research failed: {str(e)}",
                "completed": False,
                "errors": [{"error": str(e), "node": "research"}]
            }

    # Build subgraph
    graph = StateGraph(ResearchState)

    # Add research node
    graph.add_node("research", research_node)

    # Set entry and exit points
    graph.set_entry_point("research")
    graph.set_finish_point("research")

    # Compile and return
    logger.debug("✅ Research subgraph v6.1 compiled")
    return graph.compile()
