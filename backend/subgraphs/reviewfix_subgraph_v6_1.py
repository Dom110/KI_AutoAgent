"""
ReviewFix Subgraph v6.2 - Pure MCP Implementation

This is a fully MCP-based version with NO subprocess.run() or direct service calls.

Changes from v6.1:
- ALL build validation via build_validation MCP server (streaming support)
- File operations via file_tools MCP server (NO direct imports)
- Parallel build validation with asyncio.gather()
- Real-time compiler output streaming (DEBUG_MODE)
- NO backwards compatibility (pure MCP or fail)
- NO fallbacks (crash on error, don't hide problems)

Migration to v6.2:
- Replaced 300+ lines of subprocess.run() with single MCP call
- Removed direct file_tools import
- Added streaming support for build validation
- Reviewer still uses GPT-4o-mini (cost-effective)

Author: KI AutoAgent Team
Python: 3.13+
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
# MCP client for all service calls (NO direct imports!)
from mcp.mcp_client import MCPClient
from langgraph.graph import END, StateGraph

from state_v6 import ReviewFixState

logger = logging.getLogger(__name__)


def create_reviewfix_subgraph(
    workspace_path: str,
    mcp: MCPClient,
    hitl_callback: Any | None = None
) -> Any:
    """
    Create ReviewFix loop subgraph with MCP integration (v6.2).

    Uses MCP protocol for all service calls (Claude, Memory).

    Args:
        workspace_path: Path to workspace
        mcp: MCP client for all service calls
        hitl_callback: Optional HITL callback for debug info

    Returns:
        Compiled reviewfix subgraph
    """
    logger.debug("Creating ReviewFix subgraph v6.2 (MCP)...")

    # Reviewer node (unchanged - uses GPT-4o-mini)
    async def reviewer_node(state: ReviewFixState) -> ReviewFixState:
        """
        Review generated code and provide feedback.

        Uses GPT-4o-mini for cost-effective code review.
        """
        logger.info(f"🔬 Reviewer analyzing iteration {state['iteration']}...")

        try:
            # Read generated files from Codesmith
            generated_files = state.get('generated_files', [])

            # NEW v6.2: If no generated_files (FIX intent bypass), discover workspace files
            if not generated_files:
                logger.info("🔍 No generated_files in state, discovering workspace files...")

                import glob

                # Discover code files in workspace
                code_patterns = ['*.py', '*.ts', '*.tsx', '*.js', '*.jsx', '*.go', '*.rs', '*.java', '*.c', '*.cpp', '*.h']
                discovered_files = []

                for pattern in code_patterns:
                    matches = glob.glob(os.path.join(workspace_path, '**', pattern), recursive=True)
                    for match in matches:
                        # Skip node_modules, venv, build dirs
                        if any(skip in match for skip in ['node_modules', 'venv', 'dist', 'build', '__pycache__', '.git']):
                            continue

                        # Make path relative to workspace
                        rel_path = os.path.relpath(match, workspace_path)
                        discovered_files.append({"path": rel_path})

                if not discovered_files:
                    logger.warning("⚠️  No code files found in workspace")
                    return {
                        **state,
                        "quality_score": 0.0,
                        "feedback": "No code files found in workspace",
                        "iteration": state.get('iteration', 0) + 1
                    }

                logger.info(f"  ✅ Discovered {len(discovered_files)} code files in workspace")
                generated_files = discovered_files

            # Collect file contents
            file_contents = {}

            for file_info in generated_files:
                file_path = file_info.get('path')
                if not file_path:
                    continue
                full_path = os.path.join(workspace_path, file_path)

                if os.path.exists(full_path):
                    try:
                        # Read via file_tools MCP server (v6.2)
                        result = await mcp.call(
                            server="file_tools",
                            tool="read_file",
                            arguments={
                                "file_path": file_path,
                                "workspace_path": workspace_path
                            }
                        )
                        # Extract content from MCP response
                        content_blocks = result.get("content", [])
                        file_content = ""
                        for block in content_blocks:
                            if block.get("type") == "text":
                                file_content = block.get("text", "")
                        file_contents[file_path] = file_content
                    except Exception as e:
                        logger.error(f"Failed to read {file_path}: {e}")
                        file_contents[file_path] = f"[Error reading file: {e}]"

            # Review with GPT-4o-mini
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=2048
            )

            system_prompt = """You are a senior code reviewer.

Your task:
1. Review code for quality, correctness, and best practices
2. Check for errors, bugs, and security issues
3. Assess code style and documentation
4. Provide actionable feedback
5. Assign a quality score (0.0 to 1.0)

Output format:
QUALITY_SCORE: <0.0 to 1.0>

FEEDBACK:
- Issue 1: ...
- Issue 2: ...
- Suggestion 1: ...

SUMMARY: Overall assessment"""

            files_text = "\n\n".join([
                f"FILE: {path}\n```\n{content}\n```"
                for path, content in file_contents.items()
            ])

            user_prompt = f"""Review the following code:

{files_text}

Provide quality score and detailed feedback."""

            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            review_output = response.content if hasattr(response, 'content') else str(response)

            # Parse quality score
            quality_score = 0.5  # Default

            for line in review_output.split('\n'):
                if line.startswith('QUALITY_SCORE:'):
                    try:
                        score_str = line.replace('QUALITY_SCORE:', '').strip()
                        quality_score = float(score_str)
                        quality_score = max(0.0, min(1.0, quality_score))  # Clamp
                    except ValueError:
                        logger.warning(f"Failed to parse quality score: {line}")

            logger.info(f"✅ Review complete - Quality: {quality_score:.2f}")

            # ================================================================
            # BUILD VALIDATION - Via MCP Server (v6.2 PURE MCP)
            # ================================================================
            # Replaces 300+ lines of subprocess.run() code with single MCP call!
            # Benefits:
            # - Streaming compiler output in real-time (DEBUG_MODE)
            # - Parallel validation for polyglot projects (asyncio.gather)
            # - Auto-detection of 6 languages (TS, Python, JS, Go, Rust, Java)
            # - NO fallbacks (crash on error - fail loudly!)
            # ================================================================
            logger.info("🔬 Running build validation via MCP (v6.2)...")

            build_validation_passed = True
            build_errors = []

            try:
                # Call build_validation MCP server with generated_files
                validation_result = await mcp.call(
                    server="build_validation",
                    tool="validate_all",
                    arguments={
                        "workspace_path": workspace_path,
                        "generated_files": generated_files,
                        "parallel": True  # Run all language checks in parallel!
                    },
                    timeout=300.0  # 5 minutes for complex projects
                )

                # Extract validation results from MCP response
                content_blocks = validation_result.get("content", [])
                validation_output = ""
                for block in content_blocks:
                    if block.get("type") == "text":
                        validation_output = block.get("text", "")

                # Parse validation output
                # Format: {"detected_languages": [...], "results": {...}, "summary": {...}}
                import json
                try:
                    # Extract JSON from markdown code block
                    if "```json" in validation_output:
                        json_str = validation_output.split("```json\n")[1].split("\n```")[0]
                        validation_data = json.loads(json_str)
                    else:
                        validation_data = json.loads(validation_output)

                    detected_languages = validation_data.get("detected_languages", [])
                    results = validation_data.get("results", {})
                    summary = validation_data.get("summary", {})

                    logger.info(f"📊 Detected languages: {', '.join(detected_languages)}")

                    # Check if any validation failed
                    total_checks = summary.get("total_checks", 0)
                    passed_checks = summary.get("passed", 0)
                    failed_checks = summary.get("failed", 0)

                    logger.info(f"📊 Build validation: {passed_checks}/{total_checks} passed")

                    if failed_checks > 0:
                        build_validation_passed = False
                        logger.error(f"❌ Build validation FAILED: {failed_checks} checks failed")

                        # Collect all errors
                        for lang, lang_result in results.items():
                            if not lang_result.get("success", False):
                                build_errors.append({
                                    "type": f"{lang}_validation",
                                    "errors": lang_result.get("output", "")
                                })
                    else:
                        logger.info("✅ Build validation PASSED - all checks successful!")

                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse validation results: {e}")
                    logger.error(f"   Raw output: {validation_output}")
                    build_validation_passed = False
                    build_errors.append({
                        "type": "validation_parse_error",
                        "errors": f"Failed to parse validation results: {e}"
                    })

            except Exception as e:
                logger.error(f"❌ Build validation MCP call failed: {e}")
                build_validation_passed = False
                build_errors.append({
                    "type": "mcp_validation_error",
                    "errors": f"MCP validation call failed: {e}"
                })

            # ================================================================
            # LEGACY CODE REMOVED (v6.1 → v6.2 migration)
            # ================================================================
            # The following 300+ lines of subprocess.run() code have been
            # DELETED and replaced with the single MCP call above:
            #
            # - TypeScript compilation check (lines 212-258)
            # - Python mypy type check (lines 260-316)
            # - JavaScript ESLint check (lines 318-384)
            # - Go validation with go vet (lines 386-468)
            # - Rust validation with cargo check (lines 470-551)
            # - Java validation with Maven/Gradle/javac (lines 553-667)
            #
            # ALL replaced by build_validation_server.py via MCP!
            # ================================================================

            # Adjust quality score based on build validation
            if not build_validation_passed:
                logger.warning("⚠️  Build validation FAILED - reducing quality score to 0.50")
                logger.warning(f"   Original quality score: {quality_score:.2f}")
                quality_score = 0.50  # Force another iteration
                logger.warning(f"   New quality score: {quality_score:.2f}")

                # Append build errors to review feedback
                build_error_text = "\n\n## BUILD VALIDATION ERRORS\n\n"
                for err in build_errors:
                    build_error_text += f"**{err['type']}:**\n```\n{err['errors']}\n```\n\n"

                review_output += build_error_text

            else:
                logger.info("✅ Build validation PASSED")

            # Store review in Memory (via MCP!)
            try:
                await mcp.call(
                    server="memory",
                    tool="store_memory",
                    arguments={
                        "workspace_path": workspace_path,
                        "content": review_output,
                        "metadata": {
                            "agent": "reviewer",
                            "type": "review",
                            "iteration": state.get('iteration', 0) + 1,
                            "quality_score": quality_score,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to store review in memory: {e}")

            # Extract file paths for fixer
            file_paths_to_fix = [f.get('path') for f in generated_files if f.get('path')]

            return {
                **state,
                "quality_score": quality_score,
                "feedback": review_output,
                "files_to_review": file_paths_to_fix,  # NEW v6.2: For FIX intent workflow
                "iteration": state.get('iteration', 0) + 1
            }

        except Exception as e:
            logger.error(f"❌ Reviewer failed: {e}", exc_info=True)

            return {
                **state,
                "quality_score": 0.0,
                "feedback": f"Review failed: {str(e)}",
                "iteration": state.get('iteration', 0) + 1,
                "errors": state.get('errors', []) + [{"error": str(e), "node": "reviewer"}]
            }

    # Fixer node (REFACTORED - custom implementation, no create_react_agent)
    async def fixer_node(state: ReviewFixState) -> ReviewFixState:
        """
        Apply fixes based on reviewer feedback.

        Uses direct Claude LLM calls with manual file operations.
        """
        logger.info(f"🔧 Fixer applying fixes (iteration {state['iteration']})...")

        try:
            feedback = state.get('feedback', '')
            files_to_fix = state.get('files_to_review', [])

            if not feedback or not files_to_fix:
                logger.warning("⚠️  No feedback or files to fix")
                return state

            # Read current file contents
            file_contents = {}

            for file_path in files_to_fix:
                full_path = os.path.join(workspace_path, file_path)

                if os.path.exists(full_path):
                    try:
                        # Read via file_tools MCP server (v6.2)
                        result = await mcp.call(
                            server="file_tools",
                            tool="read_file",
                            arguments={
                                "file_path": file_path,
                                "workspace_path": workspace_path
                            }
                        )
                        # Extract content from MCP response
                        content_blocks = result.get("content", [])
                        file_content = ""
                        for block in content_blocks:
                            if block.get("type") == "text":
                                file_content = block.get("text", "")
                        file_contents[file_path] = file_content
                    except Exception as e:
                        logger.error(f"Failed to read {file_path}: {e}")

            if not file_contents:
                logger.warning("⚠️  No files could be read")
                return state

            # Apply fixes with Claude (via MCP!)
            logger.info("🤖 Generating fixes with Claude via MCP...")

            system_prompt = """You are an expert code fixer.

Your task:
1. Read the reviewer's feedback
2. Apply fixes to the code
3. Maintain code style and structure
4. Fix all identified issues
5. Output the complete fixed files

Output format:
For each file:

FILE: <relative_path>
```<language>
<complete fixed code>
```

Example:
FILE: src/app.py
```python
# Fixed code here
```"""

            files_text = "\n\n".join([
                f"FILE: {path}\n```\n{content}\n```"
                for path, content in file_contents.items()
            ])

            user_prompt = f"""Apply fixes based on the following review:

## Review Feedback
{feedback}

## Current Files
{files_text}

Generate complete fixed versions of all files."""

            # Call Claude via MCP
            claude_result = await mcp.call(
                server="claude",
                tool="claude_generate",
                arguments={
                    "prompt": user_prompt,
                    "system_prompt": system_prompt,
                    "workspace_path": workspace_path,
                    "agent_name": "fixer",
                    "temperature": 0.2,
                    "max_tokens": 8192,
                    "tools": ["Read", "Edit", "Bash"]
                }
            )

            # Extract fixes from MCP response
            fixes_output = ""
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
                                fixes_output = data.get("content", "")
                            except:
                                fixes_output = text
                        else:
                            fixes_output = text

            if not fixes_output:
                raise Exception(f"Fixes generation failed: {claude_result.get('error', 'Unknown error')}")

            logger.info(f"✅ Fixes generated: {len(fixes_output)} chars")

            # Parse and write fixed files
            logger.info("📝 Writing fixed files...")

            fixed_files = []

            # Simple parser for FILE: <path> format
            lines = fixes_output.split('\n')
            current_file = None
            current_code = []
            in_code_block = False

            for line in lines:
                if line.startswith('FILE:'):
                    # Save previous file
                    if current_file and current_code:
                        file_path = os.path.join(workspace_path, current_file.strip())
                        file_content = '\n'.join(current_code).strip()

                        try:
                            # Write via file_tools MCP server (v6.2)
                            await mcp.call(
                                server="file_tools",
                                tool="write_file",
                                arguments={
                                    "file_path": file_path,
                                    "content": file_content,
                                    "workspace_path": workspace_path
                                }
                            )

                            fixed_files.append(current_file.strip())
                            logger.debug(f"✅ Fixed {current_file.strip()}")
                        except Exception as e:
                            logger.error(f"❌ Failed to write {current_file}: {e}")

                    # Start new file
                    current_file = line.replace('FILE:', '').strip()
                    current_code = []
                    in_code_block = False

                elif line.startswith('```'):
                    if in_code_block:
                        in_code_block = False
                    else:
                        in_code_block = True

                elif in_code_block and current_file:
                    current_code.append(line)

            # Save last file
            if current_file and current_code:
                file_path = os.path.join(workspace_path, current_file.strip())
                file_content = '\n'.join(current_code).strip()

                try:
                    # Write via file_tools MCP server (v6.2)
                    await mcp.call(
                        server="file_tools",
                        tool="write_file",
                        arguments={
                            "file_path": file_path,
                            "content": file_content,
                            "workspace_path": workspace_path
                        }
                    )

                    fixed_files.append(current_file.strip())
                    logger.debug(f"✅ Fixed {current_file.strip()}")
                except Exception as e:
                    logger.error(f"❌ Failed to write {current_file}: {e}")

            logger.info(f"✅ Fixed {len(fixed_files)} files")

            # Store fixes in Memory (via MCP!)
            try:
                await mcp.call(
                    server="memory",
                    tool="store_memory",
                    arguments={
                        "workspace_path": workspace_path,
                        "content": fixes_output,
                        "metadata": {
                            "agent": "fixer",
                            "type": "fixes",
                            "iteration": state.get('iteration', 0),
                            "files_count": len(fixed_files),
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to store fixes in memory: {e}")

            return {
                **state,
                "fixes_applied": fixes_output,
                "fixed_files": fixed_files
            }

        except Exception as e:
            logger.error(f"❌ Fixer failed: {e}", exc_info=True)

            return {
                **state,
                "fixes_applied": f"Fixing failed: {str(e)}",
                "errors": state.get('errors', []) + [{"error": str(e), "node": "fixer"}]
            }

    # Conditional routing function
    def should_continue_fixing(state: ReviewFixState) -> Literal["continue", "end"]:
        """
        Decide whether to continue fixing or stop.

        Stop conditions:
        1. Quality score >= 0.75 (good enough)
        2. Iteration >= 3 (max iterations reached)

        Returns:
            "continue" to keep fixing, "end" to stop
        """
        quality = state.get("quality_score", 0.0)
        iteration = state.get("iteration", 0)

        if quality >= 0.75:
            logger.info(f"✅ Quality target reached: {quality:.2f}")
            return "end"

        if iteration >= 3:
            logger.info(f"⚠️  Max iterations reached: {iteration}")
            return "end"

        logger.info(f"🔄 Continue fixing (quality: {quality:.2f}, iteration: {iteration})")
        return "continue"

    # Build subgraph
    graph = StateGraph(ReviewFixState)

    # Add nodes
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("fixer", fixer_node)

    # Set entry point
    graph.set_entry_point("reviewer")

    # Add conditional routing from reviewer
    graph.add_conditional_edges(
        "reviewer",
        should_continue_fixing,
        {
            "continue": "fixer",
            "end": END
        }
    )

    # Add loop edge from fixer back to reviewer
    graph.add_edge("fixer", "reviewer")

    # Compile and return
    logger.debug("✅ ReviewFix subgraph v6.2 compiled (MCP)")
    return graph.compile()
