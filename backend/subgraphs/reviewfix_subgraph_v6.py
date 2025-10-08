"""
v6.0 ReviewFix Subgraph (Loop)

Purpose: Code review and iterative fixing
Architecture: Custom loop with Reviewer + Fixer nodes
Documentation: V6_0_ARCHITECTURE.md, V6_0_MIGRATION_PLAN.md

Integration:
- Memory: Reads Implementation (codesmith), Design (architect), stores Review + Fixes
- Tree-Sitter: Code analysis (TODO: Phase 8)
- Asimov: Permission validation (TODO: Phase 8)
- Learning: Stores successful fixes (TODO: Phase 8)
"""

from __future__ import annotations

import logging
from typing import Any, Literal
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

from state_v6 import ReviewFixState
from memory.memory_system_v6 import MemorySystem
from tools.file_tools import read_file, write_file, edit_file

logger = logging.getLogger(__name__)


def create_reviewfix_subgraph(
    workspace_path: str,
    memory: MemorySystem | None = None
) -> StateGraph:
    """
    Create ReviewFix Subgraph with Reviewer + Fixer loop.

    Args:
        workspace_path: Path to user workspace
        memory: Optional Memory System

    Returns:
        Compiled StateGraph (ReviewFixSubgraph)

    Architecture:
        1. Entry: reviewer_node
        2. Calculate quality_score (0.0-1.0)
        3. Conditional: quality >= 0.75 OR iteration >= 3 → END
        4. Else: fixer_node → reviewer_node (loop)
    """

    async def reviewer_node(state: ReviewFixState) -> ReviewFixState:
        """
        Reviewer node: Analyze code quality.

        Flow:
        1. Read implementation from Memory (codesmith)
        2. Read design from Memory (architect)
        3. Analyze code with LLM (GPT-4o-mini)
        4. Calculate quality_score (0.0-1.0)
        5. Generate review feedback
        6. Store review in Memory
        7. Return updated state
        """
        logger.info(f"🔬 Reviewer node executing (iteration {state['iteration']})")

        try:
            # 1. Read implementation from Memory
            implementation_context = {}
            if memory:
                logger.debug("Reading implementation from Memory (codesmith)...")
                impl_results = await memory.search(
                    query="code implementation",
                    k=3,
                    filters={"agent": "codesmith"}
                )
                implementation_context = {
                    "code": [r["content"] for r in impl_results]
                }
                logger.debug(f"Found {len(impl_results)} implementation items")

            # 2. Read design from Memory
            design_context = {}
            if memory:
                logger.debug("Reading design from Memory (architect)...")
                design_results = await memory.search(
                    query="architecture design",
                    k=2,
                    filters={"agent": "architect"}
                )
                design_context = {
                    "design": [r["content"] for r in design_results]
                }
                logger.debug(f"Found {len(design_results)} design items")

            # 3. Analyze code with LLM (GPT-4o-mini for speed)
            logger.debug("Initializing GPT-4o-mini for code review...")
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.2,
                max_tokens=2048
            )

            impl_summary = implementation_context.get("code", ["No implementation"])[0] if implementation_context.get("code") else "No implementation"
            design_summary = design_context.get("design", ["No design"])[0] if design_context.get("design") else "No design"

            system_prompt = """You are an expert code reviewer.

Your responsibilities:
1. Review code for quality, bugs, and best practices
2. Check alignment with architecture design
3. Provide a quality score (0.0-1.0)
4. List specific issues to fix

Output format (JSON):
{
  "quality_score": 0.85,
  "issues": [
    {"type": "bug", "description": "...", "severity": "high"},
    {"type": "style", "description": "...", "severity": "low"}
  ],
  "summary": "Overall assessment..."
}"""

            user_prompt = f"""Review this implementation:

**Implementation:**
{impl_summary[:500]}...

**Architecture Design:**
{design_summary[:300]}...

**Files to review:**
{len(state['generated_files'])} files generated

Provide quality score (0.0-1.0) and list of issues."""

            logger.info("🤖 Invoking GPT-4o-mini for review...")
            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            review_text = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"✅ Review generated: {len(review_text)} chars")

            # 4. Parse quality score (simplified for Phase 6.1)
            # TODO Phase 6.2: Parse JSON response properly
            quality_score = 0.7  # Placeholder (would parse from LLM response)

            # 5. Generate review feedback
            review_feedback = {
                "review": review_text[:500],
                "timestamp": datetime.now().isoformat(),
                "iteration": state["iteration"]
            }

            # 6. Store review in Memory
            if memory:
                logger.debug("Storing review in Memory...")
                await memory.store(
                    content=review_text,
                    metadata={
                        "agent": "reviewer",
                        "type": "review",
                        "quality_score": quality_score,
                        "iteration": state["iteration"],
                        "timestamp": datetime.now().isoformat()
                    }
                )
                logger.debug("✅ Review stored")

            # 7. Return updated state
            return {
                **state,
                "quality_score": quality_score,
                "review_feedback": review_feedback,
                "errors": state.get("errors", [])
            }

        except Exception as e:
            logger.error(f"❌ Reviewer node failed: {e}", exc_info=True)
            # Fail gracefully with low quality score
            return {
                **state,
                "quality_score": 0.0,
                "review_feedback": {"error": str(e)},
                "errors": [
                    *state.get("errors", []),
                    {
                        "node": "reviewer",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            }

    async def fixer_node(state: ReviewFixState) -> ReviewFixState:
        """
        Fixer node: Apply fixes based on review.

        Flow:
        1. Read review from Memory
        2. Generate fixes with LLM (Claude Sonnet 4)
        3. Apply fixes (file edits)
        4. Store fixes in Memory
        5. Increment iteration
        6. Return updated state
        """
        logger.info(f"🔧 Fixer node executing (iteration {state['iteration']})")

        try:
            # 1. Read review from Memory
            review_context = {}
            if memory:
                logger.debug("Reading review from Memory...")
                review_results = await memory.search(
                    query="code review issues",
                    k=1,
                    filters={"agent": "reviewer"}
                )
                review_context = {
                    "review": review_results[0]["content"] if review_results else "No review"
                }
                logger.debug("Review loaded")

            # 2. Generate fixes with LLM
            logger.debug("Initializing Claude Sonnet 4 for fixing...")
            llm = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                temperature=0.2,
                max_tokens=2048
            )

            review_summary = review_context.get("review", "No review available")

            system_prompt = """You are an expert code fixer.

Your responsibilities:
1. Read code review feedback
2. Generate specific fixes for identified issues
3. Provide clear explanations

Output format:
List fixes with:
- Issue description
- Fix strategy
- Code changes needed"""

            user_prompt = f"""Fix the issues from this review:

**Review Feedback:**
{review_summary[:500]}...

**Quality Score:** {state['quality_score']}

Provide specific fixes to improve code quality."""

            logger.info("🤖 Invoking Claude Sonnet 4 for fixes...")
            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            fixes_text = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"✅ Fixes generated: {len(fixes_text)} chars")

            # 3. Apply fixes (simplified for Phase 6.1)
            # TODO Phase 6.2: Parse fixes and actually apply them with file tools
            fixes_applied = [{
                "description": fixes_text[:200],
                "timestamp": datetime.now().isoformat()
            }]

            # 4. Store fixes in Memory
            if memory:
                logger.debug("Storing fixes in Memory...")
                await memory.store(
                    content=fixes_text,
                    metadata={
                        "agent": "fixer",
                        "type": "fix",
                        "iteration": state["iteration"],
                        "timestamp": datetime.now().isoformat()
                    }
                )
                logger.debug("✅ Fixes stored")

            # 5. Increment iteration
            new_iteration = state["iteration"] + 1

            # 6. Return updated state
            return {
                **state,
                "fixes_applied": [*state.get("fixes_applied", []), *fixes_applied],
                "iteration": new_iteration,
                "errors": state.get("errors", [])
            }

        except Exception as e:
            logger.error(f"❌ Fixer node failed: {e}", exc_info=True)
            return {
                **state,
                "fixes_applied": [],
                "iteration": state["iteration"] + 1,  # Increment to avoid infinite loop
                "errors": [
                    *state.get("errors", []),
                    {
                        "node": "fixer",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            }

    def should_continue_fixing(state: ReviewFixState) -> Literal["continue", "end"]:
        """
        Conditional routing: Continue fixing or end loop?

        Conditions to END:
        1. Quality score >= 0.75 (good enough)
        2. Iteration >= 3 (max iterations reached)

        Otherwise: Continue
        """
        logger.debug(f"Loop decision: quality={state['quality_score']}, iteration={state['iteration']}")

        if state["quality_score"] >= 0.75:
            logger.info(f"✅ Quality threshold reached: {state['quality_score']} >= 0.75")
            return "end"

        if state["iteration"] >= 3:
            logger.info(f"⚠️ Max iterations reached: {state['iteration']} >= 3")
            return "end"

        logger.info(f"🔄 Continuing to fixer (quality={state['quality_score']}, iteration={state['iteration']})")
        return "continue"

    # Build subgraph with loop
    subgraph = StateGraph(ReviewFixState)

    # Add nodes
    subgraph.add_node("reviewer", reviewer_node)
    subgraph.add_node("fixer", fixer_node)

    # Entry point: reviewer
    subgraph.set_entry_point("reviewer")

    # Conditional edge from reviewer
    subgraph.add_conditional_edges(
        "reviewer",
        should_continue_fixing,
        {
            "continue": "fixer",
            "end": END
        }
    )

    # Loop back: fixer → reviewer
    subgraph.add_edge("fixer", "reviewer")

    return subgraph.compile()


# Convenience export
__all__ = ["create_reviewfix_subgraph"]
