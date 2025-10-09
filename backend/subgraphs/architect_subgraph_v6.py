"""
v6.0 Architect Subgraph

Purpose: System design, architecture planning, codebase analysis
Architecture: CUSTOM implementation (too specialized for create_react_agent)
Documentation: V6_0_ARCHITECTURE.md, V6_0_MIGRATION_PLAN.md

Integration:
- Memory: Reads Research findings, stores Design
- Tree-Sitter: Analyzes codebase structure (TODO: Phase 4.2)
- Asimov: Permission can_analyze_codebase (TODO: Phase 8)
- Learning: Stores design patterns (TODO: Phase 8)
"""

from __future__ import annotations

import logging
from typing import Any
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

from state_v6 import ArchitectState
from memory.memory_system_v6 import MemorySystem

logger = logging.getLogger(__name__)

# Lazy LLM initialization to avoid Pydantic issues
_llm_cache: ChatOpenAI | None = None

def _get_llm() -> ChatOpenAI:
    """Get or create LLM instance (lazy initialization)."""
    global _llm_cache
    if _llm_cache is None:
        try:
            _llm_cache = ChatOpenAI(
                model="gpt-4o",
                temperature=0.3,
                max_tokens=4096
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChatOpenAI: {e}")
            # Try with minimal parameters
            _llm_cache = ChatOpenAI(model="gpt-4o")
    return _llm_cache


def create_architect_subgraph(
    workspace_path: str,
    memory: MemorySystem | None = None
) -> StateGraph:
    """
    Create Architect Subgraph with custom implementation.

    Args:
        workspace_path: Path to user workspace
        memory: Optional Memory System (for reading Research, storing Design)

    Returns:
        Compiled StateGraph (ArchitectSubgraph)

    Architecture:
        1. Entry: architect_node (custom logic)
        2. Read research from Memory
        3. Analyze codebase (TODO: Tree-Sitter)
        4. Generate design with LLM
        5. Generate Mermaid diagram
        6. Store design in Memory
        7. Exit: return design + diagram
    """

    async def architect_node(state: ArchitectState) -> ArchitectState:
        """
        Architect node with Memory + Tree-Sitter integration.

        Flow:
        1. Read research findings from Memory
        2. Analyze codebase structure (TODO: Tree-Sitter)
        3. Generate architecture design with LLM (GPT-4o)
        4. Generate Mermaid diagram
        5. Generate ADR (Architecture Decision Record)
        6. Store design in Memory
        7. Return updated state
        """
        logger.info(f"🏗️ Architect node executing: {state['user_requirements'][:50]}...")

        try:
            # 1. Read research findings from Memory
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
                logger.debug(f"Found {len(research_results)} research items")
            else:
                logger.debug("No Memory System provided, skipping research lookup")

            # 2. Analyze codebase structure (TODO: Tree-Sitter integration)
            # For Phase 4.1: Placeholder
            codebase_structure = {
                "workspace": state["workspace_path"],
                "analysis": "Tree-Sitter integration pending (Phase 4.2)",
                "files": [],
                "languages": []
            }
            logger.debug("Codebase analysis: Tree-Sitter TODO")

            # 3. Generate architecture design with LLM
            logger.debug("Initializing GPT-4o for architecture design...")
            llm = _get_llm()

            system_prompt = """You are an expert software architect specializing in modern web development.

Your responsibilities:
1. Design clean, scalable system architectures
2. Choose appropriate technology stacks
3. Identify architectural patterns
4. Create clear technical documentation

Output a structured JSON design with:
- tech_stack: List of technologies (frameworks, libraries, tools)
- patterns: List of architectural patterns to use
- components: Key system components and their responsibilities
- data_flow: How data flows through the system
- rationale: Why these choices were made

Be specific, practical, and consider modern best practices."""

            user_prompt = f"""Design a software architecture for:

**Requirements:**
{state['user_requirements']}

**Research Context:**
{research_context.get('findings', ['No research available'])[0] if research_context.get('findings') else 'No research available'}

**Existing Codebase:**
{codebase_structure['analysis']}

Provide a comprehensive architecture design."""

            logger.info("🤖 Invoking GPT-4o for architecture design...")
            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            design_text = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"✅ Architecture design generated: {len(design_text)} chars")

            # Parse design (simplified for Phase 4.1)
            design = {
                "description": design_text,
                "timestamp": datetime.now().isoformat(),
                "requirements": state["user_requirements"]
            }

            # 4. Generate Mermaid diagram (simplified for Phase 4.1)
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
**Design:** {design_text[:200]}..."""

            # 5. Generate ADR (Architecture Decision Record)
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

            # 6. Store design in Memory
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
                logger.debug("✅ Design stored in Memory")

            # 7. Return updated state
            return {
                **state,
                "research_context": research_context,
                "design": design,
                "tech_stack": [],  # TODO: Parse from LLM response
                "patterns": [],    # TODO: Parse from LLM response
                "diagram": diagram,
                "adr": adr,
                "errors": state.get("errors", [])
            }

        except Exception as e:
            logger.error(f"❌ Architect node failed: {e}", exc_info=True)
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
    subgraph = StateGraph(ArchitectState)
    subgraph.add_node("architect", architect_node)
    subgraph.set_entry_point("architect")
    subgraph.add_edge("architect", END)

    return subgraph.compile()


# Convenience export
__all__ = ["create_architect_subgraph"]
