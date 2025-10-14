"""
Research Subgraph v6.2 - Multi-Modal Research Agent

Changes from v6.1:
- Added mode parameter: "research" | "explain" | "analyze"
- Mode dispatcher for different research behaviors
- research_search_mode(): Perplexity web search (original v6.1 behavior)
- research_explain_mode(): Analyze and explain existing codebase
- research_analyze_mode(): Deep code analysis and quality assessment

Mode Selection:
- "research" (default): Web search with Perplexity for new information
- "explain": Analyze existing code structure and explain architecture
- "analyze": Deep analysis of code quality, security, patterns

Author: KI AutoAgent Team
Python: 3.13+
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

# MCP client for all service calls (replaces direct service imports)
from mcp.mcp_client import MCPClient
from state_v6 import ResearchState

logger = logging.getLogger(__name__)


# ============================================================================
# MODE FUNCTIONS - Research Agent Behaviors (v6.2+)
# ============================================================================

async def research_search_mode(
    state: ResearchState,
    workspace_path: str,
    mcp: MCPClient,
    hitl_callback: Any | None
) -> dict[str, Any]:
    """
    Research Mode: Web search with Perplexity via MCP.

    Use case: CREATE workflows - search for best practices, technologies, patterns

    Flow:
    1. Search with Perplexity (via MCP)
    2. Analyze findings with Claude (via MCP)
    3. Store in Memory (via MCP)
    4. Return structured results
    """
    logger.info(f"🌐 Research mode: web search for '{state['query']}'")

    # Step 1: Search with Perplexity (via MCP!)
    logger.info("🌐 Searching with Perplexity via MCP...")
    search_result = await mcp.call(
        server="perplexity",
        tool="perplexity_search",
        arguments={
            "query": state['query'],
            "max_results": 5
        }
    )

    # Extract content from MCP response
    search_findings = ""
    if search_result.get("content"):
        content_blocks = search_result.get("content", [])
        for block in content_blocks:
            if block.get("type") == "text":
                search_findings += block.get("text", "")

    if not search_findings:
        search_findings = "No results found"

    logger.info(f"✅ Perplexity results: {len(search_findings)} chars")

    # Step 2: Analyze with Claude (via MCP!)
    logger.info("🤖 Analyzing findings with Claude via MCP...")

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

    # Call Claude via MCP (no tools - just text analysis)
    # Note: Tools disabled to avoid MCP stdin/stdout blocking issues
    # Research agent only needs to analyze Perplexity results (no file access needed)
    claude_result = await mcp.call(
        server="claude",
        tool="claude_generate",
        arguments={
            "prompt": user_prompt,
            "system_prompt": system_prompt,
            "workspace_path": workspace_path,
            "agent_name": "research",
            "temperature": 0.3,
            "max_tokens": 4096,
            "tools": []  # No tools - pure text analysis
        },
        timeout=60.0  # 1 min timeout sufficient for text-only analysis
    )

    analysis = ""
    if claude_result.get("content"):
        content_blocks = claude_result.get("content", [])
        for block in content_blocks:
            if block.get("type") == "text":
                text = block.get("text", "")
                # Extract actual content from JSON response format
                if "content" in text and "success" in text:
                    import json
                    try:
                        data = json.loads(text.split("```json\n")[1].split("\n```")[0])
                        analysis = data.get("content", "")
                    except:
                        analysis = text
                else:
                    analysis = text

    if not analysis:
        analysis = f"Analysis failed: {claude_result.get('error', 'Unknown error')}"

    logger.info(f"✅ Analysis complete: {len(analysis)} chars")

    # Step 3: Create research report
    report = f"""# Research Report

**Query:** {state['query']}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Mode:** research (web search)

## Analysis

{analysis}

## Raw Search Results

{search_findings[:500]}...

---
*Generated by Research Agent v6.2 (research mode)*
"""

    findings = {
        "analysis": analysis,
        "raw_results": search_findings,
        "timestamp": datetime.now().isoformat(),
        "mode": "research"
    }

    # Step 4: Store in Memory (via MCP!)
    logger.info("💾 Storing findings in Memory via MCP...")
    try:
        await mcp.call(
            server="memory",
            tool="store_memory",
            arguments={
                "workspace_path": workspace_path,
                "content": analysis,
                "metadata": {
                    "agent": "research",
                    "type": "findings",
                    "mode": "research",
                    "query": state['query'],
                    "timestamp": findings["timestamp"]
                }
            }
        )
    except Exception as e:
        logger.warning(f"⚠️ Failed to store in memory: {e}")

    return {"findings": findings, "report": report}


async def research_explain_mode(
    state: ResearchState,
    workspace_path: str,
    mcp: MCPClient,
    hitl_callback: Any | None
) -> dict[str, Any]:
    """
    Explain Mode: Analyze and explain existing codebase via MCP.

    Use case: EXPLAIN workflows - user wants to understand existing code

    Flow:
    1. Analyze workspace structure with Claude (Read tool) via MCP
    2. Explain architecture and key components
    3. Store explanation in Memory via MCP
    4. Return structured explanation
    """
    logger.info(f"📖 Explain mode: analyzing codebase for '{state['query']}'")

    system_prompt = """You are a code analyst specializing in explaining software architecture.

Your responsibilities:
1. Analyze the codebase structure (files, directories, key components)
2. Explain the overall architecture and design patterns used
3. Identify main features and how they're implemented
4. Describe data flow and component interactions
5. Highlight interesting or notable implementation details

Tools available:
- Read: Read any file in the workspace
- Bash: Run commands like 'ls', 'find', 'wc', 'grep' for analysis

Output format:
# Architecture Overview
- High-level architecture description
- Main components and their responsibilities

# Key Features
- Feature 1: Description and implementation
- Feature 2: Description and implementation

# Technology Stack
- Languages, frameworks, libraries used

# Code Organization
- Directory structure
- Important files and their purposes

# Implementation Highlights
- Notable patterns or techniques
- Interesting code snippets"""

    user_prompt = f"""Analyze the codebase in the current workspace and explain:

**User Question:** {state['query']}

**Workspace Path:** {workspace_path}

Please:
1. First, explore the workspace structure (use Bash: ls, find, etc.)
2. Then, read key files to understand the implementation
3. Finally, provide a comprehensive explanation answering the user's question

Focus on providing clear, actionable explanations that help the user understand the codebase."""

    # Step 1: Analyze codebase with Claude (via MCP!)
    logger.info("🤖 Analyzing codebase with Claude via MCP...")
    claude_result = await mcp.call(
        server="claude",
        tool="claude_generate",
        arguments={
            "prompt": user_prompt,
            "system_prompt": system_prompt,
            "workspace_path": workspace_path,
            "agent_name": "research_explainer",
            "temperature": 0.2,
            "max_tokens": 8192,
            "tools": ["Read", "Bash"]
        },
        timeout=300.0  # 5 min timeout for tool-enabled Claude calls
    )

    explanation = ""
    if claude_result.get("content"):
        content_blocks = claude_result.get("content", [])
        for block in content_blocks:
            if block.get("type") == "text":
                text = block.get("text", "")
                # Extract actual content from JSON response format
                if "content" in text and "success" in text:
                    import json
                    try:
                        data = json.loads(text.split("```json\n")[1].split("\n```")[0])
                        explanation = data.get("content", "")
                    except:
                        explanation = text
                else:
                    explanation = text

    if not explanation:
        explanation = f"Explanation failed: {claude_result.get('error', 'Unknown error')}"

    logger.info(f"✅ Explanation complete: {len(explanation)} chars")

    # Step 2: Create explanation report
    report = f"""# Codebase Explanation

**Query:** {state['query']}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Mode:** explain (codebase analysis)

{explanation}

---
*Generated by Research Agent v6.2 (explain mode)*
"""

    findings = {
        "explanation": explanation,
        "workspace_analyzed": workspace_path,
        "timestamp": datetime.now().isoformat(),
        "mode": "explain"
    }

    # Step 3: Store in Memory (via MCP!)
    logger.info("💾 Storing explanation in Memory via MCP...")
    try:
        await mcp.call(
            server="memory",
            tool="store_memory",
            arguments={
                "workspace_path": workspace_path,
                "content": explanation,
                "metadata": {
                    "agent": "research",
                    "type": "explanation",
                    "mode": "explain",
                    "query": state['query'],
                    "workspace": workspace_path,
                    "timestamp": findings["timestamp"]
                }
            }
        )
    except Exception as e:
        logger.warning(f"⚠️ Failed to store in memory: {e}")

    return {"findings": findings, "report": report}


async def research_analyze_mode(
    state: ResearchState,
    workspace_path: str,
    mcp: MCPClient,
    hitl_callback: Any | None
) -> dict[str, Any]:
    """
    Analyze Mode: Deep code analysis and quality assessment via MCP.

    Use case: ANALYZE workflows - code quality, security, patterns

    Flow:
    1. Deep code analysis with Claude (Read tool + Bash for metrics) via MCP
    2. Quality assessment (security, performance, maintainability)
    3. Store analysis in Memory via MCP
    4. Return structured analysis report
    """
    logger.info(f"🔬 Analyze mode: deep analysis for '{state['query']}'")

    system_prompt = """You are a code auditor specializing in comprehensive code analysis.

Your responsibilities:
1. Assess code quality (readability, maintainability, documentation)
2. Identify security vulnerabilities and potential issues
3. Analyze performance characteristics
4. Evaluate architecture and design patterns
5. Suggest improvements and best practices

Tools available:
- Read: Read any file in the workspace
- Bash: Run analysis commands (grep, find, wc, etc.)

Output format:
# Quality Assessment
- Code Quality Score: X/10
- Strengths: What's done well
- Weaknesses: Areas for improvement

# Security Analysis
- Potential Vulnerabilities: List of security concerns
- Recommendations: How to fix them

# Performance Analysis
- Performance Characteristics: Observations
- Optimization Opportunities: Suggestions

# Architecture Evaluation
- Design Patterns Used: List patterns
- Architecture Quality: Assessment
- Suggested Refactorings: Improvements

# Action Items
Priority-ordered list of improvements"""

    user_prompt = f"""Perform a deep analysis of the codebase:

**Analysis Request:** {state['query']}

**Workspace Path:** {workspace_path}

Please:
1. Explore the codebase structure
2. Read and analyze key files
3. Identify patterns, issues, and opportunities
4. Provide a comprehensive analysis report

Focus on actionable insights and concrete recommendations."""

    # Step 1: Deep analysis with Claude (via MCP!)
    logger.info("🤖 Performing deep code analysis with Claude via MCP...")
    claude_result = await mcp.call(
        server="claude",
        tool="claude_generate",
        arguments={
            "prompt": user_prompt,
            "system_prompt": system_prompt,
            "workspace_path": workspace_path,
            "agent_name": "research_analyzer",
            "temperature": 0.1,
            "max_tokens": 8192,
            "tools": ["Read", "Bash"]
        },
        timeout=300.0  # 5 min timeout for tool-enabled Claude calls
    )

    analysis = ""
    if claude_result.get("content"):
        content_blocks = claude_result.get("content", [])
        for block in content_blocks:
            if block.get("type") == "text":
                text = block.get("text", "")
                # Extract actual content from JSON response format
                if "content" in text and "success" in text:
                    import json
                    try:
                        data = json.loads(text.split("```json\n")[1].split("\n```")[0])
                        analysis = data.get("content", "")
                    except:
                        analysis = text
                else:
                    analysis = text

    if not analysis:
        analysis = f"Analysis failed: {claude_result.get('error', 'Unknown error')}"

    logger.info(f"✅ Deep analysis complete: {len(analysis)} chars")

    # Step 2: Create analysis report
    report = f"""# Code Analysis Report

**Query:** {state['query']}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Mode:** analyze (deep code analysis)

{analysis}

---
*Generated by Research Agent v6.2 (analyze mode)*
"""

    findings = {
        "analysis": analysis,
        "workspace_analyzed": workspace_path,
        "timestamp": datetime.now().isoformat(),
        "mode": "analyze"
    }

    # Step 3: Store in Memory (via MCP!)
    logger.info("💾 Storing analysis in Memory via MCP...")
    try:
        await mcp.call(
            server="memory",
            tool="store_memory",
            arguments={
                "workspace_path": workspace_path,
                "content": analysis,
                "metadata": {
                    "agent": "research",
                    "type": "analysis",
                    "mode": "analyze",
                    "query": state['query'],
                    "workspace": workspace_path,
                    "timestamp": findings["timestamp"]
                }
            }
        )
    except Exception as e:
        logger.warning(f"⚠️ Failed to store in memory: {e}")

    return {"findings": findings, "report": report}


# ============================================================================
# RESEARCH SUBGRAPH - Mode Dispatcher (v6.2+)
# ============================================================================

def create_research_subgraph(
    workspace_path: str,
    mcp: MCPClient,
    hitl_callback: Any | None = None
) -> Any:
    """
    Create Research subgraph with multi-modal implementation via MCP.

    v6.2 Changes:
    - Mode dispatcher for different research behaviors
    - "research" mode: Web search with Perplexity via MCP
    - "explain" mode: Analyze and explain existing codebase via MCP
    - "analyze" mode: Deep code analysis via MCP
    - ALL service calls go through MCP protocol (no direct calls)

    Args:
        workspace_path: Path to workspace
        mcp: MCP client for all service calls
        hitl_callback: Optional HITL callback for debug info

    Returns:
        Compiled research subgraph
    """
    logger.debug("Creating Research subgraph v6.2 (multi-modal with MCP)...")

    # Research node function with mode dispatcher
    async def research_node(state: ResearchState) -> ResearchState:
        """
        Execute research with mode-specific behavior.

        Mode Dispatcher:
        - "research": Web search with Perplexity
        - "explain": Analyze and explain codebase
        - "analyze": Deep code analysis

        Flow:
        1. Read mode from state
        2. Dispatch to appropriate mode function
        3. Handle errors
        4. Return results
        """
        mode = state.get("mode", "research")  # Default to "research" if not specified
        logger.info(f"🔍 Research node v6.2 executing [mode={mode}]: {state['query']}")

        try:
            # Mode dispatcher
            if mode == "research":
                # Web search mode (via MCP)
                result = await research_search_mode(
                    state=state,
                    workspace_path=workspace_path,
                    mcp=mcp,
                    hitl_callback=hitl_callback
                )

            elif mode == "explain":
                # Explain codebase mode (via MCP)
                result = await research_explain_mode(
                    state=state,
                    workspace_path=workspace_path,
                    mcp=mcp,
                    hitl_callback=hitl_callback
                )

            elif mode == "analyze":
                # Deep analysis mode (via MCP)
                result = await research_analyze_mode(
                    state=state,
                    workspace_path=workspace_path,
                    mcp=mcp,
                    hitl_callback=hitl_callback
                )

            else:
                # Invalid mode - log warning and fall back to research mode
                logger.warning(f"⚠️ Invalid research mode '{mode}', falling back to 'research'")
                result = await research_search_mode(
                    state=state,
                    workspace_path=workspace_path,
                    mcp=mcp,
                    hitl_callback=hitl_callback
                )

            # Return updated state
            logger.info(f"✅ Research completed [mode={mode}]")
            return {
                **state,
                "findings": result["findings"],
                "report": result["report"],
                "sources": result.get("sources", []),
                "errors": []
            }

        except Exception as e:
            logger.error(f"❌ Research node failed [mode={mode}]: {e}", exc_info=True)

            return {
                **state,
                "findings": {},
                "report": f"Research failed [{mode} mode]: {str(e)}",
                "sources": [],
                "errors": [{"error": str(e), "node": "research", "mode": mode}]
            }

    # Build subgraph
    graph = StateGraph(ResearchState)

    # Add research node
    graph.add_node("research", research_node)

    # Set entry and exit points
    graph.set_entry_point("research")
    graph.set_finish_point("research")

    # Compile and return
    logger.debug("✅ Research subgraph v6.2 compiled (multi-modal with MCP)")
    return graph.compile()
