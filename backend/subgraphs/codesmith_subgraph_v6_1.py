"""
Codesmith Subgraph v6.1 - Custom Node Implementation

This is a refactored version that doesn't use create_react_agent,
allowing it to work with Claude CLI adapter.

Changes from v6.0:
- Removed create_react_agent (incompatible with async-only LLMs)
- Direct LLM.ainvoke() calls (like Architect pattern)
- Manual tool calling for file operations
- Works with ClaudeCLISimple adapter

Author: KI AutoAgent Team
Python: 3.13+
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from state_v6 import CodesmithState
from tools.file_tools import write_file, read_file

logger = logging.getLogger(__name__)


def create_codesmith_subgraph(
    workspace_path: str,
    memory: Any | None = None
) -> Any:
    """
    Create Codesmith subgraph with custom node implementation.

    This version uses direct LLM calls instead of create_react_agent,
    making it compatible with async-only LLMs like ClaudeCLISimple.

    Args:
        workspace_path: Path to workspace
        memory: Memory system instance (optional)

    Returns:
        Compiled codesmith subgraph
    """
    logger.debug("Creating Codesmith subgraph v6.1 (custom node)...")

    # Codesmith node function
    async def codesmith_node(state: CodesmithState) -> CodesmithState:
        """
        Execute code generation with custom implementation.

        Flow:
        1. Read design from Memory
        2. Use Claude to generate code based on design
        3. Write files to workspace using file tools
        4. Store implementation in Memory
        5. Return results
        """
        logger.info(f"⚙️ Codesmith node v6.1 executing: {state['design'][:60]}...")

        try:
            # Step 1: Read from Memory (design + research)
            design_content = state.get('design', '')
            context_from_memory = ""

            if memory:
                logger.info("🔍 Reading context from Memory...")

                # Get research findings
                research_results = await memory.search(
                    query="research findings",
                    filters={"agent": "research"},
                    limit=2
                )

                # Get architecture design
                architect_results = await memory.search(
                    query="architecture design",
                    filters={"agent": "architect"},
                    limit=2
                )

                # Build context
                context_parts = []

                if research_results:
                    context_parts.append("## Research Findings\n")
                    for result in research_results:
                        context_parts.append(result.get("content", ""))

                if architect_results:
                    context_parts.append("\n## Architecture Design\n")
                    for result in architect_results:
                        context_parts.append(result.get("content", ""))

                context_from_memory = "\n".join(context_parts)
                logger.info(f"✅ Loaded context: {len(context_from_memory)} chars")

            # Step 2: Generate code with Claude
            logger.info("🤖 Generating code with Claude...")

            llm = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                temperature=0.2,
                max_tokens=8192
            )

            system_prompt = """You are an expert code generator specializing in clean, maintainable code.

Your responsibilities:
1. Generate code based on architectural design
2. Follow best practices and design patterns
3. Write clean, well-documented code
4. Include error handling and type hints
5. Generate complete, runnable files

Output format:
For each file to create, output:

FILE: <relative_path>
```<language>
<code content>
```

Example:
FILE: src/app.py
```python
def hello():
    print("Hello")
```

FILE: src/utils.py
```python
def helper():
    return 42
```"""

            user_prompt = f"""Generate code based on the following design:

## Architecture Design
{design_content}

## Additional Context
{context_from_memory if context_from_memory else "No additional context available"}

Generate complete, production-ready code files."""

            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            code_output = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"✅ Code generated: {len(code_output)} chars")

            # Step 3: Parse and write files
            logger.info("📝 Writing files to workspace...")

            generated_files = []

            # Simple parser for FILE: <path> format
            lines = code_output.split('\n')
            current_file = None
            current_code = []
            in_code_block = False

            for line in lines:
                if line.startswith('FILE:'):
                    # Save previous file
                    if current_file and current_code:
                        file_path = os.path.join(workspace_path, current_file.strip())
                        file_content = '\n'.join(current_code).strip()

                        # Ensure directory exists
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)

                        # Write file
                        try:
                            await write_file.ainvoke({
                                "file_path": file_path,
                                "content": file_content
                            })

                            generated_files.append({
                                "path": current_file.strip(),
                                "size": len(file_content),
                                "timestamp": datetime.now().isoformat()
                            })

                            logger.debug(f"✅ Wrote {current_file.strip()}")
                        except Exception as e:
                            logger.error(f"❌ Failed to write {current_file}: {e}")

                    # Start new file
                    current_file = line.replace('FILE:', '').strip()
                    current_code = []
                    in_code_block = False

                elif line.startswith('```'):
                    if in_code_block:
                        # End code block
                        in_code_block = False
                    else:
                        # Start code block
                        in_code_block = True

                elif in_code_block and current_file:
                    current_code.append(line)

            # Save last file
            if current_file and current_code:
                file_path = os.path.join(workspace_path, current_file.strip())
                file_content = '\n'.join(current_code).strip()

                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                try:
                    await write_file.ainvoke({
                        "file_path": file_path,
                        "content": file_content
                    })

                    generated_files.append({
                        "path": current_file.strip(),
                        "size": len(file_content),
                        "timestamp": datetime.now().isoformat()
                    })

                    logger.debug(f"✅ Wrote {current_file.strip()}")
                except Exception as e:
                    logger.error(f"❌ Failed to write {current_file}: {e}")

            logger.info(f"✅ Generated {len(generated_files)} files")

            # Step 4: Create implementation summary
            implementation_summary = f"""# Implementation Summary

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Files Generated:** {len(generated_files)}

## Generated Files

"""
            for file_info in generated_files:
                implementation_summary += f"- `{file_info['path']}` ({file_info['size']} bytes)\n"

            implementation_summary += f"""

## Code Generation Output

{code_output[:1000]}...

---
*Generated by Codesmith Agent v6.1*
"""

            # Step 5: Store in Memory (if available)
            if memory:
                logger.info("💾 Storing implementation in Memory...")
                await memory.store(
                    content=implementation_summary,
                    metadata={
                        "agent": "codesmith",
                        "type": "implementation",
                        "files_count": len(generated_files),
                        "timestamp": datetime.now().isoformat()
                    }
                )
                logger.debug("✅ Implementation stored in Memory")

            # Return updated state
            return {
                **state,
                "generated_files": generated_files,
                "implementation_summary": implementation_summary,
                "completed": True,
                "errors": []
            }

        except Exception as e:
            logger.error(f"❌ Codesmith node failed: {e}", exc_info=True)

            return {
                **state,
                "generated_files": [],
                "implementation_summary": f"Code generation failed: {str(e)}",
                "completed": False,
                "errors": [{"error": str(e), "node": "codesmith"}]
            }

    # Build subgraph
    graph = StateGraph(CodesmithState)

    # Add codesmith node
    graph.add_node("codesmith", codesmith_node)

    # Set entry and exit points
    graph.set_entry_point("codesmith")
    graph.set_finish_point("codesmith")

    # Compile and return
    logger.debug("✅ Codesmith subgraph v6.1 compiled")
    return graph.compile()
