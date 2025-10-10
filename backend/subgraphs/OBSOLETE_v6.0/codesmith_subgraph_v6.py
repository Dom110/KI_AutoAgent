"""
v6.0 Codesmith Subgraph

Purpose: Code implementation, file operations
Architecture: create_react_agent() with file tools (LangGraph best practice)
Documentation: V6_0_ARCHITECTURE.md, V6_0_MIGRATION_PLAN.md

Integration:
- Memory: Reads Design (architect) + Research, stores Implementation
- Tree-Sitter: Validates syntax (TODO: Phase 8)
- Asimov: Permission can_write_files (TODO: Phase 8)
- Learning: Suggests past successful approaches (TODO: Phase 8)
"""

from __future__ import annotations

import logging
from typing import Any
from datetime import datetime

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, END

from state_v6 import CodesmithState
from memory.memory_system_v6 import MemorySystem
from tools.file_tools import read_file, write_file, edit_file

logger = logging.getLogger(__name__)


def create_codesmith_subgraph(
    workspace_path: str,
    memory: MemorySystem | None = None
) -> StateGraph:
    """
    Create Codesmith Subgraph using create_react_agent().

    Args:
        workspace_path: Path to user workspace
        memory: Optional Memory System (for reading Design/Research, storing Implementation)

    Returns:
        Compiled StateGraph (CodesmithSubgraph)

    Architecture:
        1. Entry: codesmith_node (create_react_agent wrapper)
        2. Read design from Memory (architect)
        3. Read research from Memory (research)
        4. Agent uses file tools to implement code
        5. Store implementation in Memory
        6. Exit: return generated files
    """

    # Tools (with workspace_path bound)
    # NOTE: LangChain tools need workspace_path parameter
    # We'll pass it in the agent invocation context
    tools = [read_file, write_file, edit_file]

    # System prompt for Codesmith Agent
    state_modifier_content = """You are an expert software engineer specializing in clean, maintainable code.

Your responsibilities:
1. Implement features based on architecture design
2. Write production-quality code following best practices
3. Use file tools (read_file, write_file, edit_file) to create files
4. Validate syntax before writing files
5. Follow the design specifications exactly

Code Quality Standards:
- Clear, self-documenting code with meaningful names
- Proper error handling
- Type hints (for TypeScript/Python)
- Comments only where necessary
- Follow language conventions (PEP 8, ESLint, etc.)

Tools Available:
- read_file(file_path, workspace_path): Read existing files
- write_file(file_path, content, workspace_path): Create new files
- edit_file(file_path, old_content, new_content, workspace_path): Edit files

Output Format:
Return a structured summary of files created/modified."""

    async def codesmith_node(state: CodesmithState) -> CodesmithState:
        """
        Codesmith node with Memory integration.

        Flow:
        1. Read design from Memory (architect)
        2. Read research from Memory (research)
        3. Create LLM and ReAct agent (lazy)
        4. Invoke agent with design + research context
        5. Extract generated files from agent response
        6. Store implementation in Memory
        7. Return updated state
        """
        logger.info(f"⚙️ Codesmith node executing: {state['requirements'][:50]}...")

        try:
            # 1. Read design from Memory
            design_context = {}
            if memory:
                logger.debug("Reading design from Memory (architect)...")
                design_results = await memory.search(
                    query=state["requirements"],
                    k=3,
                    filters={"agent": "architect"}
                )
                design_context = {
                    "design": [r["content"] for r in design_results],
                    "metadata": [r.get("metadata", {}) for r in design_results]
                }
                logger.debug(f"Found {len(design_results)} design items")

            # 2. Read research from Memory
            research_context = {}
            if memory:
                logger.debug("Reading research from Memory...")
                research_results = await memory.search(
                    query=state["requirements"],
                    k=3,
                    filters={"agent": "research"}
                )
                research_context = {
                    "findings": [r["content"] for r in research_results]
                }
                logger.debug(f"Found {len(research_results)} research items")

            # 3. Lazy initialize LLM and agent
            logger.debug("Initializing Claude Sonnet 4 and ReAct agent...")
            llm = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                temperature=0.2,  # Lower temp for code generation
                max_tokens=4096
            )

            react_agent = create_react_agent(
                model=llm,
                tools=tools,
                state_modifier=SystemMessage(content=state_modifier_content)
            )
            logger.debug("✅ ReAct agent created")

            # 4. Prepare agent input with full context
            design_summary = design_context.get("design", ["No design available"])[0] if design_context.get("design") else "No design available"
            research_summary = research_context.get("findings", ["No research available"])[0] if research_context.get("findings") else "No research available"

            user_prompt = f"""Implement the following requirements:

**Requirements:**
{state['requirements']}

**Architecture Design:**
{design_summary[:500]}...

**Research Context:**
{research_summary[:500]}...

**Workspace Path:**
{state['workspace_path']}

Use the file tools to create the necessary files. Follow the architecture design closely."""

            agent_input = {
                "messages": [
                    HumanMessage(content=user_prompt)
                ],
                "workspace_path": state["workspace_path"]  # Pass to tools
            }

            # 5. Invoke agent
            logger.info("🤖 Invoking create_react_agent...")
            result = await react_agent.ainvoke(agent_input)

            # Extract agent response
            last_message = result["messages"][-1]
            response_text = last_message.content if hasattr(last_message, 'content') else str(last_message)

            logger.info(f"✅ Agent response: {response_text[:200]}...")

            # 6. Extract generated files (simplified for Phase 5.1)
            # TODO Phase 5.2: Parse tool calls to extract actual files created
            generated_files = [{
                "type": "implementation",
                "description": response_text[:500],
                "timestamp": datetime.now().isoformat()
            }]

            # 7. Store implementation in Memory
            if memory:
                logger.debug("Storing implementation in Memory...")
                await memory.store(
                    content=response_text,
                    metadata={
                        "agent": "codesmith",
                        "type": "implementation",
                        "requirements": state["requirements"],
                        "timestamp": datetime.now().isoformat()
                    }
                )
                logger.debug("✅ Implementation stored in Memory")

            # 8. Return updated state
            return {
                **state,
                "design": design_context,
                "research": research_context,
                "past_successes": [],  # TODO: Learning System Phase 8
                "generated_files": generated_files,
                "tests": [],  # TODO: Test generation Phase 5.2
                "api_docs": "",  # TODO: API doc generation Phase 5.2
                "errors": state.get("errors", [])
            }

        except Exception as e:
            logger.error(f"❌ Codesmith node failed: {e}", exc_info=True)
            return {
                **state,
                "design": {},
                "research": {},
                "past_successes": [],
                "generated_files": [],
                "tests": [],
                "api_docs": "",
                "errors": [
                    *state.get("errors", []),
                    {
                        "node": "codesmith",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            }

    # Build subgraph
    subgraph = StateGraph(CodesmithState)
    subgraph.add_node("codesmith", codesmith_node)
    subgraph.set_entry_point("codesmith")
    subgraph.add_edge("codesmith", END)

    return subgraph.compile()


# Convenience export
__all__ = ["create_codesmith_subgraph"]
