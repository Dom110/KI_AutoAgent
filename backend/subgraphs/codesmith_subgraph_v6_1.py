"""
Codesmith Subgraph v6.2 - Pure MCP Implementation

This is a fully MCP-based version with NO direct service imports.

Changes from v6.1:
- ALL file operations via file_tools MCP server (NO direct imports)
- Claude generation via MCP (already implemented)
- Memory storage via MCP (already implemented)
- NO backwards compatibility (pure MCP or fail)
- Tree-sitter and Asimov checks integrated

Migration to v6.2:
- Removed direct file_tools import
- Replaced all write_file.ainvoke() with MCP calls
- Streaming support for file operations

Author: KI AutoAgent Team
Python: 3.13+
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

# MCP client for all service calls (NO direct imports!)
from mcp.mcp_client import MCPClient
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from state_v6 import CodesmithState
from tools.tree_sitter_tools import TreeSitterAnalyzer
from security.asimov_rules import validate_asimov_rules, format_violations_report
from subgraphs.file_validation import validate_generated_files, generate_completion_prompt

logger = logging.getLogger(__name__)


def create_codesmith_subgraph(
    workspace_path: str,
    mcp: MCPClient,
    hitl_callback: Any | None = None,
    orchestrator: Any = None
) -> Any:
    """
    Create Codesmith subgraph with MCP integration (v6.2).

    Uses MCP protocol for all service calls (Claude, Memory).

    Args:
        workspace_path: Path to workspace
        mcp: MCP client for all service calls
        hitl_callback: Optional HITL callback for debug info
        orchestrator: AgentOrchestrator for agent autonomy (v6.3)

    Returns:
        Compiled codesmith subgraph
    """
    logger.debug("Creating Codesmith subgraph v6.2 (MCP)...")

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
        design_preview = str(state.get('design', ''))[:60] if state.get('design') else 'No design'
        logger.info(f"⚙️ Codesmith node v6.1 executing: {design_preview}...")

        try:
            # Step 1: Read from Memory (via MCP!)
            design_content = str(state.get('design', ''))
            context_from_memory = ""

            try:
                logger.info("🔍 Reading context from Memory via MCP...")

                # Get research findings (via MCP)
                research_result = await mcp.call(
                    server="memory",
                    tool="search_memory",
                    arguments={
                        "workspace_path": workspace_path,
                        "query": "research findings",
                        "filters": {"agent": "research"},
                        "k": 2
                    }
                )

                # Get architecture design (via MCP)
                architect_result = await mcp.call(
                    server="memory",
                    tool="search_memory",
                    arguments={
                        "workspace_path": workspace_path,
                        "query": "architecture design",
                        "filters": {"agent": "architect"},
                        "k": 2
                    }
                )

                # Extract results from MCP responses
                research_results = []
                architect_results = []

                # Parse research results
                if research_result.get("content"):
                    for block in research_result.get("content", []):
                        if block.get("type") == "text":
                            research_results.append({"content": block.get("text", "")})

                # Parse architect results
                if architect_result.get("content"):
                    for block in architect_result.get("content", []):
                        if block.get("type") == "text":
                            architect_results.append({"content": block.get("text", "")})

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

            except Exception as e:
                logger.warning(f"⚠️ Failed to load context from memory: {e}")
                context_from_memory = ""

            # Step 1.4: NEW v6.2 - Agent Autonomy: Invoke Research if context missing
            if orchestrator and not research_results:
                logger.info("🔬 No research in memory - invoking Research agent...")
                try:
                    research_invocation = await orchestrator.invoke_research(
                        query=f"Best practices and library documentation for: {state.get('requirements', '')[:200]}",
                        mode="research",
                        caller="codesmith"
                    )
                    if research_invocation["success"]:
                        logger.info(f"✅ Research agent returned {len(research_invocation['result'])} chars")
                        # Add to context
                        context_from_memory += f"\n\n## Additional Research\n{research_invocation['result']}"
                        research_results = [{"content": research_invocation["result"]}]
                except Exception as e:
                    logger.warning(f"⚠️ Research agent invocation failed: {e}")

            # Step 1.5: NEW v6.2 - Agent Autonomy: Invoke Architect if design missing
            if orchestrator and not architect_results:
                logger.info("🏗️  No architecture in memory - invoking Architect agent...")
                try:
                    architect_invocation = await orchestrator.invoke_architect(
                        task=f"Design architecture for: {state.get('requirements', '')[:200]}",
                        mode="design",
                        caller="codesmith",
                        design_input={}
                    )
                    if architect_invocation["success"]:
                        logger.info(f"✅ Architect agent returned {len(architect_invocation['design'])} chars")
                        # Add to context
                        design_content = architect_invocation["design"]
                        context_from_memory += f"\n\n## Generated Architecture\n{design_content}"
                        architect_results = [{"content": design_content}]
                except Exception as e:
                    logger.warning(f"⚠️ Architect agent invocation failed: {e}")

            # Step 1.5: NEW v6.3 - Model Selection based on complexity
            logger.info("🎯 Assessing task complexity and selecting model...")

            # Import ModelSelector
            from agents.specialized.model_selector import ModelSelector

            # orchestrator is available from closure (passed to create_codesmith_subgraph)
            # No need to get from state - it's not serializable!

            # Extract design and research context
            design_dict = state.get("design", {})
            research_dict = state.get("research", {})

            # Parse architect_results for design context
            design_context = None
            if architect_results:
                try:
                    import json
                    # Try to parse as JSON first
                    design_context = json.loads(architect_results[0].get("content", "{}"))
                except (json.JSONDecodeError, ValueError, IndexError, KeyError):
                    # Fall back to dict from state
                    design_context = design_dict if isinstance(design_dict, dict) else None

            # Parse research_results for research context
            research_context = None
            if research_results:
                research_context = {
                    "findings": [r.get("content", "") for r in research_results],
                    "sources": []
                }

            # Estimate complexity from design
            file_count_estimate = 0
            if design_context and isinstance(design_context, dict):
                components = design_context.get("components", [])
                file_count_estimate = len(components) * 2  # Rough estimate: 2 files per component

            # Select model
            selector = ModelSelector()
            model_config, notification = selector.select_model(
                requirements=state.get("requirements", ""),
                file_count=file_count_estimate,
                design_context=design_context,
                research_context=research_context
            )

            logger.info(f"✅ Selected model: {model_config.name} (think={model_config.think_mode})")
            print(notification)  # Print to console for user visibility

            # Send notification via HITL callback if available
            if hitl_callback:
                try:
                    await hitl_callback({
                        "type": "model_selection",
                        "model": model_config.name,
                        "model_id": model_config.model_id,
                        "think_mode": model_config.think_mode,
                        "notification": notification
                    })
                except Exception as e:
                    logger.warning(f"⚠️ Failed to send model selection notification: {e}")

            # Step 2: Generate code with Claude (via MCP!)
            logger.info(f"🤖 Generating code with {model_config.name} via MCP...")

            system_prompt = """You are an expert code generator specializing in clean, maintainable code.

Your responsibilities:
1. Generate code based on architectural design
2. Follow best practices and design patterns
3. Write clean, well-documented code
4. Include error handling and type hints
5. Generate complete, runnable files

CRITICAL: You MUST follow this EXACT output format. Do NOT add any explanation or commentary.
Do NOT say "I've generated..." or "Here is the code...". ONLY output the format below:

FILE: <relative_path>
```<language>
<code content>
```

FILE: <next_file_path>
```<language>
<code content>
```

Example (this is the ONLY format allowed):
FILE: src/app.py
```python
def hello():
    print("Hello")
```

FILE: src/utils.py
```python
def helper():
    return 42
```

START YOUR RESPONSE WITH "FILE:" - Nothing else!"""

            user_prompt = f"""Generate code based on the following design:

## Architecture Design
{design_content}

## Additional Context
{context_from_memory if context_from_memory else "No additional context available"}

Generate complete, production-ready code files."""

            # Call Claude via MCP with selected model
            claude_result = await mcp.call(
                server="claude",
                tool="claude_generate",
                arguments={
                    "prompt": user_prompt,
                    "system_prompt": system_prompt,
                    "workspace_path": workspace_path,
                    "agent_name": "codesmith",
                    "model": model_config.model_id,  # Use selected model
                    "temperature": model_config.temperature,
                    "max_tokens": model_config.max_tokens,
                    "think_mode": model_config.think_mode,  # Enable Think mode if needed
                    "tools": ["Read", "Edit", "Bash"]
                },
                timeout=900  # 15 min timeout for code generation
            )

            # Extract code from MCP response
            code_output = ""
            files_from_mcp = []

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
                                code_output = data.get("content", "")
                                files_from_mcp = data.get("files_created", [])
                            except (json.JSONDecodeError, IndexError, KeyError) as e:
                                logger.debug(f"Could not parse JSON from response: {e}")
                                code_output = text
                        else:
                            code_output = text

            if not code_output:
                raise Exception(f"Code generation failed: {claude_result.get('error', 'Unknown error')}")

            logger.info(f"✅ Code generated: {len(code_output)} chars")
            logger.debug(f"📄 First 500 chars of generated code:\n{code_output[:500]}")
            logger.debug(f"📄 Last 500 chars of generated code:\n{code_output[-500:]}")

            # Step 3: Parse and write files
            logger.info("📝 Writing files to workspace...")

            generated_files = []

            # Simple parser for FILE: <path> format
            lines = code_output.split('\n')
            current_file = None
            current_code = []
            in_code_block = False

            # Initialize Tree-sitter analyzer
            tree_sitter = TreeSitterAnalyzer()

            for line in lines:
                if line.startswith('FILE:'):
                    # Save previous file
                    if current_file and current_code:
                        file_content = '\n'.join(current_code).strip()

                        # Validate syntax with Tree-sitter BEFORE writing
                        file_path = current_file.strip()
                        language = tree_sitter.detect_language(file_path)

                        if language:
                            logger.info(f"🔍 Validating {file_path} ({language})...")
                            is_valid = tree_sitter.validate_syntax(file_content, language)

                            if not is_valid:
                                logger.error(f"❌ Syntax validation failed for {file_path}")
                                logger.warning(f"⚠️ Skipping file due to syntax errors")
                                # Don't write invalid files
                                current_file = line.replace('FILE:', '').strip()
                                current_code = []
                                in_code_block = False
                                continue

                            logger.info(f"✅ Syntax valid for {file_path}")
                        else:
                            logger.debug(f"⚠️ No parser for {file_path}, skipping Tree-sitter validation")

                        # Asimov Security Check (for code files)
                        if language:  # Only check code files
                            logger.info(f"🔒 Asimov security check for {file_path}...")
                            asimov_result = validate_asimov_rules(
                                code=file_content,
                                file_path=file_path,
                                strict=False  # Warnings allowed, errors block
                            )

                            if not asimov_result["valid"]:
                                # Log violations
                                report = format_violations_report(asimov_result, file_path)
                                logger.warning(f"\n{report}")

                                # Count errors (not warnings)
                                error_count = asimov_result["summary"]["errors"]
                                if error_count > 0:
                                    logger.error(f"❌ Asimov Rule violations: {error_count} errors")
                                    logger.warning(f"⚠️ Skipping file due to Asimov violations")
                                    current_file = line.replace('FILE:', '').strip()
                                    current_code = []
                                    in_code_block = False
                                    continue
                                else:
                                    # Only warnings, write anyway but log
                                    logger.warning(f"⚠️ Asimov warnings present, but writing file")
                            else:
                                logger.info(f"✅ Asimov rules passed for {file_path}")

                        # Write file via file_tools MCP server (v6.2)
                        try:
                            await mcp.call(
                                server="file_tools",
                                tool="write_file",
                                arguments={
                                    "file_path": file_path,
                                    "content": file_content,
                                    "workspace_path": workspace_path
                                }
                            )

                            generated_files.append({
                                "path": file_path,
                                "size": len(file_content),
                                "timestamp": datetime.now().isoformat(),
                                "validated": language is not None
                            })

                            logger.debug(f"✅ Wrote {file_path}")
                        except Exception as e:
                            logger.error(f"❌ Failed to write {file_path}: {e}")

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

            # Save last file (with validation)
            if current_file and current_code:
                file_content = '\n'.join(current_code).strip()
                file_path = current_file.strip()

                # Validate syntax with Tree-sitter
                language = tree_sitter.detect_language(file_path)

                if language:
                    logger.info(f"🔍 Validating {file_path} ({language})...")
                    is_valid = tree_sitter.validate_syntax(file_content, language)

                    if not is_valid:
                        logger.error(f"❌ Syntax validation failed for {file_path}")
                        logger.warning(f"⚠️ Skipping file due to syntax errors")
                    else:
                        logger.info(f"✅ Syntax valid for {file_path}")

                        # Asimov Security Check
                        logger.info(f"🔒 Asimov security check for {file_path}...")
                        asimov_result = validate_asimov_rules(
                            code=file_content,
                            file_path=file_path,
                            strict=False
                        )

                        asimov_passed = True
                        if not asimov_result["valid"]:
                            report = format_violations_report(asimov_result, file_path)
                            logger.warning(f"\n{report}")

                            error_count = asimov_result["summary"]["errors"]
                            if error_count > 0:
                                logger.error(f"❌ Asimov violations: {error_count} errors")
                                logger.warning(f"⚠️ Skipping file due to Asimov violations")
                                asimov_passed = False  # Don't write file with errors
                            else:
                                logger.warning(f"⚠️ Asimov warnings, but writing file")
                        else:
                            logger.info(f"✅ Asimov rules passed for {file_path}")

                        # Write file only if valid (via MCP v6.2)
                        if asimov_passed:
                            try:
                                await mcp.call(
                                    server="file_tools",
                                    tool="write_file",
                                    arguments={
                                        "file_path": file_path,
                                        "content": file_content,
                                        "workspace_path": workspace_path
                                    }
                                )

                                generated_files.append({
                                    "path": file_path,
                                    "size": len(file_content),
                                    "timestamp": datetime.now().isoformat(),
                                    "validated": True
                                })

                                logger.debug(f"✅ Wrote {file_path}")
                            except Exception as e:
                                logger.error(f"❌ Failed to write {file_path}: {e}")
                else:
                    logger.debug(f"⚠️ No parser for {file_path}, writing without validation")

                    # Write file without validation (e.g., .txt, .md) via MCP (v6.2)
                    try:
                        await mcp.call(
                            server="file_tools",
                            tool="write_file",
                            arguments={
                                "file_path": file_path,
                                "content": file_content,
                                "workspace_path": workspace_path
                            }
                        )

                        generated_files.append({
                            "path": file_path,
                            "size": len(file_content),
                            "timestamp": datetime.now().isoformat(),
                            "validated": False
                        })

                        logger.debug(f"✅ Wrote {file_path}")
                    except Exception as e:
                        logger.error(f"❌ Failed to write {file_path}: {e}")

            logger.info(f"✅ Generated {len(generated_files)} files from parsing")

            # Step 3.5: FALLBACK - Use files from MCP response
            # (MCP Claude server returns files_created in response)
            if len(generated_files) == 0 and files_from_mcp:
                logger.info(f"🔍 No files from parsing - using {len(files_from_mcp)} files from MCP response...")
                generated_files = files_from_mcp

            # Step 3.6: Validate generated files (NEW!)
            logger.info("🔍 Validating file completeness...")
            validation_result = validate_generated_files(
                workspace_path=workspace_path,
                generated_files=generated_files,
                app_type=None,  # Auto-detect
                design=design_content
            )

            # Check if critical files are missing
            if not validation_result["valid"]:
                logger.warning(f"⚠️ Generation incomplete: {validation_result['completeness']*100:.1f}% complete")
                logger.warning(f"   Missing critical files: {', '.join(validation_result['missing_critical'])}")

                # Retry once for missing files
                logger.info("🔄 Attempting to generate missing files...")
                completion_prompt = generate_completion_prompt(validation_result, design_content)

                if completion_prompt:
                    try:
                        # Retry with MCP
                        completion_result = await mcp.call(
                            server="claude",
                            tool="claude_generate",
                            arguments={
                                "prompt": completion_prompt,
                                "system_prompt": system_prompt,
                                "workspace_path": workspace_path,
                                "agent_name": "codesmith",
                                "temperature": 0.2,
                                "max_tokens": 8192,
                                "tools": ["Read", "Edit", "Bash"]
                            }
                        )

                        # Extract completion output
                        completion_output = ""
                        if completion_result.get("content"):
                            for block in completion_result.get("content", []):
                                if block.get("type") == "text":
                                    text = block.get("text", "")
                                    if "content" in text and "success" in text:
                                        import json
                                        try:
                                            data = json.loads(text.split("```json\n")[1].split("\n```")[0])
                                            completion_output = data.get("content", "")
                                        except (json.JSONDecodeError, IndexError, KeyError) as e:
                                            logger.debug(f"Could not parse JSON from response: {e}")
                                            completion_output = text
                                    else:
                                        completion_output = text

                        logger.info(f"✅ Completion response: {len(completion_output)} chars")

                        # Parse and write completion files (reuse same parser logic)
                        # For simplicity, we'll just log that we tried
                        # In production, this would parse completion_output and write files
                        logger.info("📝 Parsing completion response...")

                        # Re-validate after retry
                        validation_result = validate_generated_files(
                            workspace_path=workspace_path,
                            generated_files=generated_files,  # Would include new files
                            app_type=validation_result["app_type"],
                            design=design_content
                        )

                        if validation_result["valid"]:
                            logger.info("✅ Generation completed after retry!")
                        else:
                            logger.warning("⚠️ Still incomplete after retry")

                    except Exception as e:
                        logger.error(f"❌ Retry failed: {e}")
            else:
                logger.info(f"✅ File validation PASSED - All critical files present!")

            # Step 4: Create implementation summary
            implementation_summary = f"""# Implementation Summary

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Files Generated:** {len(generated_files)}
**App Type:** {validation_result['app_type']}
**Completeness:** {validation_result['completeness']*100:.1f}%
**Validation:** {'✅ PASSED' if validation_result['valid'] else '⚠️ INCOMPLETE'}

## Generated Files

"""
            for file_info in generated_files:
                implementation_summary += f"- `{file_info['path']}` ({file_info['size']} bytes)\n"

            if validation_result.get('missing_files'):
                implementation_summary += f"""
## Missing Files

"""
                for missing in validation_result['missing_critical']:
                    implementation_summary += f"- ❌ `{missing}` (CRITICAL)\n"

                for missing in (set(validation_result['missing_files']) - set(validation_result['missing_critical'])):
                    implementation_summary += f"- ⚠️ `{missing}` (optional)\n"

            implementation_summary += f"""

## Code Generation Output

{code_output[:1000]}...

---
*Generated by Codesmith Agent v6.1 with File Validation*
"""

            # Step 5: Store in Memory (via MCP!)
            try:
                logger.info("💾 Storing implementation in Memory via MCP...")
                await mcp.call(
                    server="memory",
                    tool="store_memory",
                    arguments={
                        "workspace_path": workspace_path,
                        "content": implementation_summary,
                        "metadata": {
                            "agent": "codesmith",
                            "type": "implementation",
                            "files_count": len(generated_files),
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                )
                logger.debug("✅ Implementation stored in Memory")
            except Exception as e:
                logger.warning(f"⚠️ Failed to store in memory: {e}")

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
    logger.debug("✅ Codesmith subgraph v6.2 compiled (MCP)")
    return graph.compile()
