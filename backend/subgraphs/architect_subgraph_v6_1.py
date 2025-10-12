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

# Use ClaudeCLISimple for v6.1 consistency
from adapters.claude_cli_simple import ClaudeCLISimple as ChatAnthropic
from state_v6 import ArchitectState
from memory.memory_system_v6 import MemorySystem
from utils.architect_parser import parse_architect_response

# NEW v6.2: Tree-Sitter Code Analysis
from utils.tree_sitter_analyzer import TreeSitterAnalyzer, TREE_SITTER_AVAILABLE

logger = logging.getLogger(__name__)


def create_architect_subgraph(
    workspace_path: str,
    memory: MemorySystem | None = None,
    hitl_callback: Any = None
) -> Any:
    """
    Create Architect Subgraph with custom implementation (v6.1).

    Args:
        workspace_path: Path to user workspace
        memory: Optional Memory System (for reading Research, storing Design)
        hitl_callback: Optional HITL callback for debug info

    Returns:
        Compiled StateGraph (ArchitectSubgraph)

    Architecture:
        1. Entry: architect_node (custom logic)
        2. Read research from Memory
        3. Analyze codebase (Tree-Sitter integration: v6.2)
        4. Generate design with Claude Sonnet 4
        5. Parse architecture (tech_stack, patterns, components)
        6. Generate Mermaid diagram
        7. Store design in Memory
        8. Exit: return design + diagram
    """
    logger.debug("Creating Architect subgraph v6.1 (custom node)...")

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
            # Step 1: Read research findings from Memory
            print(f"  Step 1: Reading research from Memory...")
            research_context = {}
            if memory:
                logger.debug("Reading research findings from Memory...")
                research_results = await memory.search(
                    query=state["user_requirements"],
                    k=5,
                    filters={"agent": "research"}
                )
                research_context = {
                    "findings": [r["content"] for r in research_results],
                    "sources": [r.get("metadata", {}) for r in research_results]
                }
                print(f"  Step 1: Found {len(research_results)} research items")
                logger.debug(f"Found {len(research_results)} research items")
            else:
                print(f"  Step 1: No Memory System, skipping")
                logger.debug("No Memory System provided, skipping research lookup")

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

            # Step 3: Generate architecture design with Claude
            print(f"  Step 3: Creating Claude LLM...")
            logger.info("🤖 Generating architecture design with Claude Sonnet 4...")

            llm = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                temperature=0.3,
                max_tokens=4096,
                agent_name="architect",
                agent_description="Expert software architect specializing in modern system design",
                agent_tools=["Read", "Bash"],  # Read for codebase analysis, Bash for utilities
                permission_mode="acceptEdits",
                hitl_callback=hitl_callback,  # Pass HITL callback for debug info
                workspace_path=workspace_path  # 🎯 FIX (2025-10-11): Set CWD for subprocess!
            )
            print(f"  Step 3: LLM created, calling Claude CLI...")

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

            logger.info("🤖 Invoking Claude CLI for architecture design...")
            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            print(f"  Step 3: Claude returned {type(response)}")

            design_text = response.content if hasattr(response, 'content') else str(response)
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

            # Step 7: Store design in Memory
            print(f"  Step 6: Storing design in Memory...")
            if memory:
                logger.debug("Storing architecture design in Memory...")
                await memory.store(
                    content=design_text,
                    metadata={
                        "agent": "architect",
                        "type": "design",
                        "requirements": state["user_requirements"],
                        "timestamp": datetime.now().isoformat()
                    }
                )
                print(f"  Step 6: Design stored")
                logger.debug("✅ Design stored in Memory")
            else:
                print(f"  Step 6: No Memory, skipping")

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

    logger.debug("✅ Architect subgraph v6.1 compiled")
    return graph.compile()


# Convenience export
__all__ = ["create_architect_subgraph"]
