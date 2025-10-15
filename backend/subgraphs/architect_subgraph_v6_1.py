"""
Architect Subgraph v6.1 - Custom Node Implementation

This is a refactored version that uses ClaudeCLISimple instead of ChatOpenAI,
allowing it to work with the v6.1 architecture and HITL callbacks.

Changes from v6.0:
- Replaced langchain_openai.ChatOpenAI with ClaudeCLISimple
- Uses Claude Sonnet 4 instead of GPT-4o
- Added hitl_callback parameter for HITL debug info
- Direct LLM.ainvoke() calls (no create_react_agent)
- Improved error handling

Author: KI AutoAgent Team
Python: 3.13+
"""

from __future__ import annotations

import logging
from typing import Any
from datetime import datetime

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

# MCP client for all service calls (replaces direct service imports)
from mcp.mcp_client import MCPClient
from state_v6 import ArchitectState
from utils.architect_parser import parse_architect_response

# NEW v6.2: Tree-Sitter Code Analysis
from utils.tree_sitter_analyzer import TreeSitterAnalyzer, TREE_SITTER_AVAILABLE

logger = logging.getLogger(__name__)


def create_architect_subgraph(
    workspace_path: str,
    mcp: MCPClient,
    hitl_callback: Any = None
) -> Any:
    """
    Create Architect Subgraph with MCP integration (v6.2).

    Args:
        workspace_path: Path to user workspace
        mcp: MCP client for all service calls
        hitl_callback: Optional HITL callback for debug info

    Returns:
        Compiled StateGraph (ArchitectSubgraph)

    Architecture:
        1. Entry: architect_node (custom logic)
        2. Read research from Memory (via MCP)
        3. Analyze codebase (Tree-Sitter integration: v6.2)
        4. Generate design with Claude Sonnet 4 (via MCP)
        5. Parse architecture (tech_stack, patterns, components)
        6. Generate Mermaid diagram
        7. Store design in Memory (via MCP)
        8. Exit: return design + diagram
    """
    logger.debug("Creating Architect subgraph v6.2 (MCP)...")

    async def architect_node(state: ArchitectState) -> ArchitectState:
        """
        Architect node with Memory + Claude Sonnet 4 integration.

        Flow:
        1. Read research findings from Memory
        2. Analyze codebase structure (Tree-Sitter: v6.2)
        3. Generate architecture design with Claude
        4. Parse architecture (tech_stack, patterns, components)
        5. Generate Mermaid diagram
        6. Generate ADR (Architecture Decision Record)
        7. Store design in Memory
        8. Return updated state
        """
        print(f"🏗️  === ARCHITECT SUBGRAPH START ===")
        logger.info(f"🏗️  Architect node v6.1 executing: {state['user_requirements'][:50]}...")

        try:
            # Step 1: Read research findings from Memory (via MCP!)
            print(f"  Step 1: Reading research from Memory via MCP...")
            research_context = {}
            try:
                logger.debug("Reading research findings from Memory via MCP...")
                memory_result = await mcp.call(
                    server="memory",
                    tool="search_memory",
                    arguments={
                        "workspace_path": workspace_path,
                        "query": state["user_requirements"],
                        "k": 5,
                        "filters": {"agent": "research"}
                    }
                )

                # Extract results from MCP response
                research_results = []
                if memory_result.get("content"):
                    content_blocks = memory_result.get("content", [])
                    for block in content_blocks:
                        if block.get("type") == "text":
                            text = block.get("text", "")
                            # Parse results (MCP returns formatted text)
                            if text:
                                research_results.append({
                                    "content": text,
                                    "metadata": {}
                                })

                research_context = {
                    "findings": [r["content"] for r in research_results],
                    "sources": [r.get("metadata", {}) for r in research_results]
                }
                print(f"  Step 1: Found {len(research_results)} research items")
                logger.debug(f"Found {len(research_results)} research items")
            except Exception as e:
                print(f"  Step 1: Memory search failed: {e}")
                logger.warning(f"Memory search failed: {e}")

            # Step 2: Analyze codebase structure (Tree-Sitter v6.2)
            print(f"  Step 2: Analyzing codebase structure...")

            if TREE_SITTER_AVAILABLE:
                try:
                    logger.info("🌳 Running Tree-Sitter codebase analysis...")
                    analyzer = TreeSitterAnalyzer(state["workspace_path"])
                    analysis_result = analyzer.analyze_workspace(
                        max_files=50,  # Limit for performance
                        exclude_dirs=["node_modules", "venv", ".git", "__pycache__"]
                    )

                    # Generate summary for LLM
                    codebase_summary = analyzer.get_codebase_summary(analysis_result)

                    codebase_structure = {
                        "workspace": state["workspace_path"],
                        "analysis": codebase_summary,
                        "files": analysis_result.analyzed_files,
                        "languages": list(analysis_result.languages.keys()),
                        "total_classes": analysis_result.total_classes,
                        "total_functions": analysis_result.total_functions,
                        "total_lines": analysis_result.total_lines,
                        "avg_complexity": analysis_result.avg_complexity
                    }

                    print(f"  Step 2: Tree-Sitter analysis complete:")
                    print(f"    - {analysis_result.analyzed_files} files analyzed")
                    print(f"    - Languages: {', '.join(analysis_result.languages.keys())}")
                    print(f"    - {analysis_result.total_classes} classes, {analysis_result.total_functions} functions")
                    logger.info(f"✅ Tree-Sitter analysis: {analysis_result.analyzed_files} files")

                except Exception as e:
                    logger.warning(f"⚠️  Tree-Sitter analysis failed: {e}")
                    # Fallback to basic analysis
                    codebase_structure = {
                        "workspace": state["workspace_path"],
                        "analysis": f"Tree-Sitter analysis unavailable ({str(e)}). Using basic file analysis.",
                        "files": [],
                        "languages": []
                    }
                    print(f"  Step 2: Tree-Sitter failed, using fallback")
            else:
                logger.warning("⚠️  Tree-Sitter not available - install with: pip install tree-sitter")
                codebase_structure = {
                    "workspace": state["workspace_path"],
                    "analysis": "Tree-Sitter not installed. To enable code analysis: pip install tree-sitter tree-sitter-python tree-sitter-javascript",
                    "files": [],
                    "languages": []
                }
                print(f"  Step 2: Tree-Sitter not available (install required)")

            # Step 3: Generate architecture design with Claude (via MCP!)
            print(f"  Step 3: Calling Claude via MCP...")
            logger.info("🤖 Generating architecture design with Claude Sonnet 4 via MCP...")

            system_prompt = """You are an expert software architect specializing in modern web development.

Your responsibilities:
1. Design clean, scalable system architectures
2. Choose appropriate technology stacks
3. Identify architectural patterns
4. Create clear technical documentation

Output a structured design with:
- Tech Stack: List of technologies (frameworks, libraries, tools)
- Patterns: List of architectural patterns to use
- Components: Key system components and their responsibilities
- Data Flow: How data flows through the system
- Rationale: Why these choices were made

Be specific, practical, and consider modern best practices."""

            research_summary = "No research available"
            if research_context.get('findings'):
                research_summary = research_context['findings'][0][:1000]  # First 1000 chars

            user_prompt = f"""Design a software architecture for:

**Requirements:**
{state['user_requirements']}

**Research Context:**
{research_summary}

**Existing Codebase:**
{codebase_structure['analysis']}

Provide a comprehensive architecture design."""

            # LOG PROMPTS FOR DEBUGGING
            import json
            with open("/tmp/architect_system_prompt.txt", "w") as f:
                f.write(system_prompt)
            with open("/tmp/architect_user_prompt.txt", "w") as f:
                f.write(user_prompt)
            print(f"  📝 System prompt: /tmp/architect_system_prompt.txt ({len(system_prompt)} chars)")
            print(f"  📝 User prompt: /tmp/architect_user_prompt.txt ({len(user_prompt)} chars)")

            logger.info("🤖 Invoking Claude CLI via MCP for architecture design...")
            claude_result = await mcp.call(
                server="claude",
                tool="claude_generate",
                arguments={
                    "prompt": user_prompt,
                    "system_prompt": system_prompt,
                    "workspace_path": workspace_path,
                    "agent_name": "architect",
                    "temperature": 0.3,
                    "max_tokens": 4096,
                    "tools": ["Read", "Bash"]
                }
            )

            # Extract design from MCP response
            design_text = ""
            if claude_result.get("content"):
                content_blocks = claude_result.get("content", [])
                for block in content_blocks:
                    if block.get("type") == "text":
                        text = block.get("text", "")
                        # Extract actual content from JSON response format
                        if "content" in text and "success" in text:
                            try:
                                data = json.loads(text.split("```json\n")[1].split("\n```")[0])
                                design_text = data.get("content", "")
                            except (json.JSONDecodeError, IndexError, KeyError) as e:
                                logger.debug(f"Could not parse JSON from response: {e}")
                                design_text = text
                        else:
                            design_text = text

            if not design_text:
                raise Exception(f"Architecture design failed: {claude_result.get('error', 'Unknown error')}")

            print(f"  Step 3: Design complete: {len(design_text)} chars")
            logger.info(f"✅ Architecture design generated: {len(design_text)} chars")

            # Step 4: Parse design with architect_parser
            print(f"  Step 4: Parsing architecture design...")
            parsed_architecture = parse_architect_response(design_text)

            design = {
                "description": design_text,
                "timestamp": datetime.now().isoformat(),
                "requirements": state["user_requirements"],
                **parsed_architecture  # Add parsed fields
            }

            print(f"  Step 4: Parsed {len(parsed_architecture['tech_stack'])} tech items, "
                  f"{len(parsed_architecture['patterns'])} patterns, "
                  f"{len(parsed_architecture['components'])} components")
            logger.info(f"✅ Parsed architecture: {len(parsed_architecture['tech_stack'])} tech items")

            # Step 5: Generate Mermaid diagram (simplified for Phase 4.1)
            print(f"  Step 4: Generating Mermaid diagram...")
            diagram = f"""```mermaid
graph TD
    A[User Request] --> B[System Design]
    B --> C[Architecture Components]
    C --> D[Implementation]

    style A fill:#e1f5ff
    style B fill:#fff3cd
    style C fill:#d4edda
    style D fill:#f8d7da
```

**Note:** Full diagram generation pending (Phase 4.2)
**Design Preview:** {design_text[:200]}..."""

            # Step 6: Generate ADR (Architecture Decision Record)
            print(f"  Step 5: Generating ADR...")
            adr = f"""# Architecture Decision Record

**Date:** {datetime.now().strftime('%Y-%m-%d')}
**Status:** Proposed
**Context:** {state['user_requirements'][:200]}...

## Decision

{design_text[:500]}...

## Consequences

- Chosen architecture aligns with requirements
- Technology stack supports scalability
- Patterns enable maintainability

**Full design available in memory store.**
"""

            # Step 7: Store design in Memory (via MCP!)
            print(f"  Step 6: Storing design in Memory via MCP...")
            try:
                logger.debug("Storing architecture design in Memory via MCP...")
                await mcp.call(
                    server="memory",
                    tool="store_memory",
                    arguments={
                        "workspace_path": workspace_path,
                        "content": design_text,
                        "metadata": {
                            "agent": "architect",
                            "type": "design",
                            "requirements": state["user_requirements"],
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                )
                print(f"  Step 6: Design stored")
                logger.debug("✅ Design stored in Memory")
            except Exception as e:
                print(f"  Step 6: Memory storage failed: {e}")
                logger.warning(f"Memory storage failed: {e}")

            # Step 8: Return updated state
            print(f"  Step 7: Returning state")
            print(f"🏗️  === ARCHITECT SUBGRAPH END ===")
            return {
                **state,
                "research_context": research_context,
                "design": design,
                "tech_stack": parsed_architecture["tech_stack"],  # ✅ Parsed from LLM response
                "patterns": parsed_architecture["patterns"],      # ✅ Parsed from LLM response
                "diagram": diagram,
                "adr": adr,
                "errors": state.get("errors", [])
            }

        except Exception as e:
            logger.error(f"❌ Architect node failed: {e}", exc_info=True)
            print(f"❌ ARCHITECT ERROR: {e}")
            return {
                **state,
                "research_context": {},
                "design": {},
                "tech_stack": [],
                "patterns": [],
                "diagram": "",
                "adr": "",
                "errors": [
                    *state.get("errors", []),
                    {
                        "node": "architect",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            }

    # Build subgraph
    graph = StateGraph(ArchitectState)
    graph.add_node("architect", architect_node)
    graph.set_entry_point("architect")
    graph.add_edge("architect", END)

    logger.debug("✅ Architect subgraph v6.2 compiled (MCP)")
    return graph.compile()


# Convenience export
__all__ = ["create_architect_subgraph"]
