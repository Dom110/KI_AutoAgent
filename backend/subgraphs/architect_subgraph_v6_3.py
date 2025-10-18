"""
Architect Subgraph v6.3 - Multi-Mode Architecture Management

This version implements ASIMOV RULE 5: System Understanding Protocol
with four distinct modes for architecture management.

Changes from v6.1:
- Added mode parameter: "scan" | "design" | "post_build_scan" | "re_scan"
- Integrated architecture_manager.py for documentation
- Scan mode loads existing architecture (UPDATE workflows)
- Post-build scan documents generated code (CREATE workflows)
- Re-scan updates architecture after modifications (UPDATE workflows)
- Design mode creates new architecture or proposes updates

Author: KI AutoAgent Team
Python: 3.13+
Version: v6.3-alpha
Date: 2025-10-14
"""

from __future__ import annotations

import logging
from typing import Any
from datetime import datetime

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

# MCP client for all service calls
from mcp.mcp_client import MCPClient
from state_v6 import ArchitectState
from utils.architect_parser import parse_architect_response
from utils.architecture_manager import ArchitectureManager

# Tree-Sitter Code Analysis
from utils.tree_sitter_analyzer import TreeSitterAnalyzer, TREE_SITTER_AVAILABLE

logger = logging.getLogger(__name__)


def create_architect_subgraph(
    workspace_path: str,
    mcp: MCPClient,
    hitl_callback: Any = None,
    orchestrator: Any = None
) -> Any:
    """
    Create Architect Subgraph with multi-mode support (v6.3).

    Args:
        workspace_path: Path to user workspace
        mcp: MCP client for all service calls
        hitl_callback: Optional HITL callback for debug info
        orchestrator: AgentOrchestrator for agent autonomy (v6.3)

    Returns:
        Compiled StateGraph (ArchitectSubgraph)

    Modes:
        1. "scan": Load existing architecture, verify consistency
        2. "design": Design new architecture or propose updates
        3. "post_build_scan": Document system after code generation
        4. "re_scan": Update architecture after modifications

    Architecture (v6.3):
        1. Entry: architect_node (mode-dependent logic)
        2. Mode dispatch:
           - scan: Load architecture → Tree-Sitter → Verify consistency
           - design: Read research → Tree-Sitter → Generate design → Parse → Store
           - post_build_scan: Tree-Sitter → Generate architecture → Save
           - re_scan: Load architecture → Tree-Sitter → Update → Save
        3. Exit: return architecture + diagram
    """
    logger.debug(f"Creating Architect subgraph v6.3 (MCP, mode-aware)...")

    # Initialize architecture manager
    arch_manager = ArchitectureManager(workspace_path=workspace_path)

    async def architect_node(state: ArchitectState) -> ArchitectState:
        """
        Architect node with mode-dependent behavior.

        Modes:
        - scan: Load and verify existing architecture
        - design: Create new architecture design
        - post_build_scan: Document generated code
        - re_scan: Update architecture after changes
        """
        mode = state.get("mode", "design")
        print(f"🏗️  === ARCHITECT SUBGRAPH START (mode={mode}) ===")
        logger.info(f"🏗️  Architect node v6.3 executing: mode={mode}")

        try:
            if mode == "scan":
                return await _scan_mode(state, mcp, arch_manager, workspace_path)
            elif mode == "post_build_scan":
                return await _post_build_scan_mode(state, mcp, arch_manager, workspace_path)
            elif mode == "re_scan":
                return await _re_scan_mode(state, mcp, arch_manager, workspace_path)
            else:  # "design" (default)
                return await _design_mode(state, mcp, arch_manager, workspace_path, orchestrator)

        except Exception as e:
            logger.error(f"❌ Architect node failed: {e}", exc_info=True)
            print(f"❌ ARCHITECT ERROR: {e}")
            return {
                **state,
                "research_context": {},
                "design": {},
                "tech_stack": [],
                "patterns": [],
                "architecture": {},
                "diagram": "",
                "adr": "",
                "errors": [
                    *state.get("errors", []),
                    {
                        "node": "architect",
                        "mode": mode,
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

    logger.debug("✅ Architect subgraph v6.3 compiled (MCP, multi-mode)")
    return graph.compile()


# ============================================================================
# MODE IMPLEMENTATIONS
# ============================================================================

async def _scan_mode(
    state: ArchitectState,
    mcp: MCPClient,
    arch_manager: ArchitectureManager,
    workspace_path: str
) -> ArchitectState:
    """
    SCAN MODE: Load existing architecture and verify consistency.

    Used in UPDATE workflows to understand the system before modifications.

    Steps:
    1. Load existing architecture from .ki_autoagent/architecture/
    2. Run Tree-Sitter analysis on current codebase
    3. Verify consistency between docs and code
    4. Return architecture + consistency report
    """
    print(f"  📖 SCAN MODE: Loading existing architecture...")
    logger.info("📖 Scan mode: Loading existing architecture")

    # Step 1: Load architecture
    architecture = await arch_manager.load_architecture()

    if not architecture:
        logger.warning("⚠️  No existing architecture found!")
        print(f"  ⚠️  No architecture documentation found")
        # This is OK for first UPDATE - we'll generate it
        architecture = {
            "overview": "No existing architecture documentation",
            "components": [],
            "tech_stack": {},
            "patterns": []
        }

    print(f"  ✅ Loaded: {len(architecture.get('components', []))} components")

    # Step 2: Tree-Sitter analysis
    print(f"  🌳 Running Tree-Sitter analysis...")
    tree_sitter_analysis = await _run_tree_sitter_analysis(state["workspace_path"])

    # Step 3: Verify consistency
    print(f"  🔍 Verifying consistency...")
    consistency = await arch_manager.verify_consistency(tree_sitter_analysis)

    print(f"  📊 Consistency score: {consistency['score']:.2f}")
    if not consistency["consistent"]:
        print(f"  ⚠️  {len(consistency['discrepancies'])} discrepancies found")

    # Step 4: Return state with loaded architecture
    print(f"🏗️  === ARCHITECT SUBGRAPH END (scan) ===")
    return {
        **state,
        "architecture": architecture,
        "design": architecture,  # For backward compatibility
        "tech_stack": architecture.get("tech_stack", {}).get("languages", []),
        "patterns": architecture.get("patterns", []),
        "diagram": "",  # Could generate from architecture
        "adr": f"""# Architecture Scan Report

**Date:** {datetime.now().strftime('%Y-%m-%d')}
**Consistency Score:** {consistency['score']:.2f}
**Status:** {"✅ Consistent" if consistency['consistent'] else "⚠️  Inconsistent"}

## Existing Architecture

- **Components:** {len(architecture.get('components', []))}
- **Tech Stack:** {', '.join(architecture.get('tech_stack', {}).get('languages', []))}
- **Patterns:** {len(architecture.get('patterns', []))}

## Consistency Check

{_format_consistency(consistency)}

**Architecture loaded and ready for update planning.**
""",
        "research_context": {"consistency": consistency},
        "errors": state.get("errors", [])
    }


async def _design_mode(
    state: ArchitectState,
    mcp: MCPClient,
    arch_manager: ArchitectureManager,
    workspace_path: str,
    orchestrator: Any = None
) -> ArchitectState:
    """
    DESIGN MODE: Create new architecture or propose updates.

    Used in both CREATE and UPDATE workflows.

    Steps:
    1. Read research findings from Memory
    2. Run Tree-Sitter analysis
    3. Generate design with Claude
    4. Parse architecture
    5. Store in Memory
    6. Return design
    """
    print(f"  🎨 DESIGN MODE: Creating architecture design...")
    logger.info("🎨 Design mode: Creating architecture")

    # Step 1: Read research from Memory
    print(f"  Step 1: Reading research from Memory...")
    research_context = await _read_research_from_memory(mcp, workspace_path, state["user_requirements"])
    print(f"  ✅ Found {len(research_context.get('findings', []))} research items")

    # Step 1.5: NEW v6.3 - Invoke Research agent if no research found (agent autonomy!)
    if orchestrator and len(research_context.get('findings', [])) == 0:
        print(f"  🔬 No research in memory - invoking Research agent...")
        try:
            research_result = await orchestrator.invoke_research(
                query=f"Best practices and technologies for: {state['user_requirements'][:200]}",
                mode="research",
                caller="architect"
            )
            if research_result["success"]:
                print(f"  ✅ Research agent returned {len(research_result['result'])} chars")
                research_context = {
                    "findings": [research_result["result"]],
                    "sources": research_result.get("sources", [])
                }
        except Exception as e:
            logger.warning(f"  ⚠️  Research agent invocation failed: {e}")
            print(f"  ⚠️  Research agent failed: {e}")

    # Step 2: Tree-Sitter analysis
    print(f"  Step 2: Analyzing codebase structure...")
    codebase_structure = await _run_tree_sitter_analysis(state["workspace_path"])

    # Step 3: Generate design with Claude
    print(f"  Step 3: Calling Claude for design...")
    design_text = await _generate_design_with_claude(
        mcp=mcp,
        workspace_path=workspace_path,
        requirements=state["user_requirements"],
        research_summary=research_context.get('findings', [''])[0][:1000] if research_context.get('findings') else "No research available",
        codebase_summary=codebase_structure.get("analysis", "No codebase analysis")
    )
    print(f"  ✅ Design complete: {len(design_text)} chars")

    # Step 4: Parse design
    print(f"  Step 4: Parsing architecture...")
    parsed_architecture = parse_architect_response(design_text)
    print(f"  ✅ Parsed: {len(parsed_architecture['tech_stack'])} tech items, {len(parsed_architecture['components'])} components")

    design = {
        "description": design_text,
        "timestamp": datetime.now().isoformat(),
        "requirements": state["user_requirements"],
        **parsed_architecture
    }

    # Step 5: Generate diagram
    diagram = _generate_placeholder_diagram(design_text)

    # Step 6: Generate ADR
    adr = _generate_adr(state["user_requirements"], design_text)

    # Step 7: Store in Memory
    print(f"  Step 5: Storing design in Memory...")
    await _store_design_in_memory(mcp, workspace_path, design_text, state["user_requirements"])

    # Step 8: Return state
    print(f"🏗️  === ARCHITECT SUBGRAPH END (design) ===")
    return {
        **state,
        "research_context": research_context,
        "design": design,
        "tech_stack": parsed_architecture["tech_stack"],
        "patterns": parsed_architecture["patterns"],
        "architecture": design,  # Full architecture for later stages
        "diagram": diagram,
        "adr": adr,
        "errors": state.get("errors", [])
    }


async def _post_build_scan_mode(
    state: ArchitectState,
    mcp: MCPClient,
    arch_manager: ArchitectureManager,
    workspace_path: str
) -> ArchitectState:
    """
    POST-BUILD SCAN MODE: Document system after code generation.

    Used in CREATE workflows after Codesmith completes.

    Steps:
    1. Run Tree-Sitter analysis on generated code
    2. Generate architecture documentation from code
    3. Save to .ki_autoagent/architecture/
    4. Return architecture
    """
    print(f"  📝 POST-BUILD SCAN MODE: Documenting generated code...")
    logger.info("📝 Post-build scan: Documenting system")

    # Step 1: Tree-Sitter analysis
    print(f"  Step 1: Analyzing generated code...")
    tree_sitter_analysis = await _run_tree_sitter_analysis(state["workspace_path"])
    print(f"  ✅ Analyzed {tree_sitter_analysis.get('files', 0)} files")

    # Step 2: Generate architecture from code
    print(f"  Step 2: Generating architecture documentation...")
    architecture = await arch_manager.generate_architecture_from_code(tree_sitter_analysis)
    print(f"  ✅ Generated: {len(architecture.get('components', []))} components")

    # Step 3: Save architecture
    print(f"  Step 3: Saving architecture to .ki_autoagent/architecture/...")
    await arch_manager.save_architecture(architecture)
    print(f"  ✅ Architecture saved")

    # Step 4: Generate diagrams
    print(f"  Step 4: Generating diagrams...")
    diagrams = await arch_manager.export_diagrams()
    diagram = diagrams.get("component_diagram", "")

    # Step 5: Return state
    print(f"🏗️  === ARCHITECT SUBGRAPH END (post_build_scan) ===")
    return {
        **state,
        "architecture": architecture,
        "design": architecture,
        "tech_stack": architecture.get("tech_stack", {}).get("languages", []),
        "patterns": architecture.get("patterns", []),
        "diagram": diagram,
        "adr": f"""# Post-Build Architecture Documentation

**Date:** {datetime.now().strftime('%Y-%m-%d')}
**Status:** System documented

## Generated Architecture

- **Components:** {len(architecture.get('components', []))}
- **Tech Stack:** {', '.join(architecture.get('tech_stack', {}).get('languages', []))}
- **Patterns:** {len(architecture.get('patterns', []))}
- **Files Analyzed:** {tree_sitter_analysis.get('files', 0)}

## Overview

{architecture.get('overview', 'No overview available')}

**Architecture documentation saved to `.ki_autoagent/architecture/`**
""",
        "research_context": {},
        "errors": state.get("errors", [])
    }


async def _re_scan_mode(
    state: ArchitectState,
    mcp: MCPClient,
    arch_manager: ArchitectureManager,
    workspace_path: str
) -> ArchitectState:
    """
    RE-SCAN MODE: Update architecture after modifications.

    Used in UPDATE workflows after ReviewFix completes.

    Steps:
    1. Load existing architecture
    2. Run Tree-Sitter analysis on modified code
    3. Update architecture documentation
    4. Save updates
    5. Return updated architecture
    """
    print(f"  🔄 RE-SCAN MODE: Updating architecture documentation...")
    logger.info("🔄 Re-scan mode: Updating architecture")

    # Step 1: Load existing architecture
    print(f"  Step 1: Loading existing architecture...")
    existing_architecture = await arch_manager.load_architecture()

    # Step 2: Tree-Sitter analysis
    print(f"  Step 2: Analyzing modified code...")
    tree_sitter_analysis = await _run_tree_sitter_analysis(state["workspace_path"])
    print(f"  ✅ Analyzed {tree_sitter_analysis.get('files', 0)} files")

    # Step 3: Generate updated architecture
    print(f"  Step 3: Generating architecture updates...")
    new_architecture = await arch_manager.generate_architecture_from_code(tree_sitter_analysis)

    # Step 4: Update architecture (merge)
    print(f"  Step 4: Updating architecture documentation...")
    await arch_manager.update_architecture(new_architecture)
    print(f"  ✅ Architecture updated")

    # Step 5: Verify consistency
    print(f"  Step 5: Verifying consistency...")
    consistency = await arch_manager.verify_consistency(tree_sitter_analysis)
    print(f"  📊 Consistency score: {consistency['score']:.2f}")

    # Step 6: Generate diagrams
    diagrams = await arch_manager.export_diagrams()
    diagram = diagrams.get("component_diagram", "")

    # Step 7: Generate change summary
    discrepancies = consistency.get('discrepancies', [])[:5]
    changes_text = "\n".join([f"- {disc.get('message', str(disc))}" for disc in discrepancies])
    if not changes_text:
        changes_text = "No significant changes detected"

    # Step 8: Return state
    print(f"🏗️  === ARCHITECT SUBGRAPH END (re_scan) ===")
    return {
        **state,
        "architecture": new_architecture,
        "design": new_architecture,
        "tech_stack": new_architecture.get("tech_stack", {}).get("languages", []),
        "patterns": new_architecture.get("patterns", []),
        "diagram": diagram,
        "adr": f"""# Architecture Update Report

**Date:** {datetime.now().strftime('%Y-%m-%d')}
**Status:** Architecture updated
**Consistency Score:** {consistency['score']:.2f}

## Updated Architecture

- **Components:** {len(new_architecture.get('components', []))}
- **Tech Stack:** {', '.join(new_architecture.get('tech_stack', {}).get('languages', []))}
- **Patterns:** {len(new_architecture.get('patterns', []))}
- **Files Analyzed:** {tree_sitter_analysis.get('files', 0)}

## Changes

{changes_text}

**Architecture documentation updated in `.ki_autoagent/architecture/`**
""",
        "research_context": {"consistency": consistency},
        "errors": state.get("errors", [])
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _run_tree_sitter_analysis(workspace_path: str) -> dict:
    """Run Tree-Sitter analysis and return results."""
    if not TREE_SITTER_AVAILABLE:
        logger.warning("⚠️  Tree-Sitter not available")
        return {
            "workspace": workspace_path,
            "analysis": "Tree-Sitter not installed",
            "files": 0,
            "languages": []
        }

    try:
        analyzer = TreeSitterAnalyzer(workspace_path)
        analysis_result = analyzer.analyze_workspace(
            max_files=50,
            exclude_dirs=["node_modules", "venv", ".git", "__pycache__", ".ki_autoagent"]
        )

        codebase_summary = analyzer.get_codebase_summary(analysis_result)

        return {
            "workspace": workspace_path,
            "analysis": codebase_summary,
            "files": analysis_result.analyzed_files,
            "languages": list(analysis_result.languages.keys()),
            "total_classes": analysis_result.total_classes,
            "total_functions": analysis_result.total_functions,
            "total_lines": analysis_result.total_lines,
            "avg_complexity": analysis_result.avg_complexity
        }
    except Exception as e:
        logger.warning(f"⚠️  Tree-Sitter analysis failed: {e}")
        return {
            "workspace": workspace_path,
            "analysis": f"Analysis failed: {str(e)}",
            "files": 0,
            "languages": []
        }


async def _read_research_from_memory(mcp: MCPClient, workspace_path: str, query: str) -> dict:
    """Read research findings from Memory."""
    try:
        memory_result = await mcp.call(
            server="memory",
            tool="search_memory",
            arguments={
                "workspace_path": workspace_path,
                "query": query,
                "k": 5,
                "filters": {"agent": "research"}
            }
        )

        research_results = []
        if memory_result.get("content"):
            for block in memory_result.get("content", []):
                if block.get("type") == "text":
                    text = block.get("text", "")
                    if text:
                        research_results.append({"content": text, "metadata": {}})

        return {
            "findings": [r["content"] for r in research_results],
            "sources": [r.get("metadata", {}) for r in research_results]
        }
    except Exception as e:
        logger.warning(f"Memory search failed: {e}")
        return {"findings": [], "sources": []}


async def _generate_design_with_claude(
    mcp: MCPClient,
    workspace_path: str,
    requirements: str,
    research_summary: str,
    codebase_summary: str
) -> str:
    """Generate architecture design with Claude."""
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

    user_prompt = f"""Design a software architecture for:

**Requirements:**
{requirements}

**Research Context:**
{research_summary}

**Existing Codebase:**
{codebase_summary}

Provide a comprehensive architecture design."""

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
        },
        timeout=300  # 5 min timeout for architecture design
    )

    # Extract text from response
    design_text = ""
    if claude_result.get("content"):
        for block in claude_result.get("content", []):
            if block.get("type") == "text":
                text = block.get("text", "")
                if "content" in text and "success" in text:
                    try:
                        import json
                        data = json.loads(text.split("```json\n")[1].split("\n```")[0])
                        design_text = data.get("content", "")
                    except (json.JSONDecodeError, IndexError, KeyError) as e:
                        logger.debug(f"Could not parse JSON from response: {e}")
                        design_text = text
                else:
                    design_text = text

    if not design_text:
        raise Exception(f"Design generation failed: {claude_result.get('error', 'Unknown error')}")

    return design_text


async def _store_design_in_memory(mcp: MCPClient, workspace_path: str, design_text: str, requirements: str):
    """Store design in Memory."""
    try:
        await mcp.call(
            server="memory",
            tool="store_memory",
            arguments={
                "workspace_path": workspace_path,
                "content": design_text,
                "metadata": {
                    "agent": "architect",
                    "type": "design",
                    "requirements": requirements,
                    "timestamp": datetime.now().isoformat()
                }
            }
        )
    except Exception as e:
        logger.warning(f"Memory storage failed: {e}")


def _generate_placeholder_diagram(design_text: str) -> str:
    """Generate placeholder Mermaid diagram."""
    return f"""```mermaid
graph TD
    A[User Request] --> B[System Design]
    B --> C[Architecture Components]
    C --> D[Implementation]

    style A fill:#e1f5ff
    style B fill:#fff3cd
    style C fill:#d4edda
    style D fill:#f8d7da
```

**Note:** Full diagram generation pending
**Design Preview:** {design_text[:200]}..."""


def _generate_adr(requirements: str, design_text: str) -> str:
    """Generate Architecture Decision Record."""
    return f"""# Architecture Decision Record

**Date:** {datetime.now().strftime('%Y-%m-%d')}
**Status:** Proposed
**Context:** {requirements[:200]}...

## Decision

{design_text[:500]}...

## Consequences

- Chosen architecture aligns with requirements
- Technology stack supports scalability
- Patterns enable maintainability

**Full design available in memory store.**
"""


def _format_consistency(consistency: dict) -> str:
    """Format consistency check results."""
    if consistency["consistent"]:
        return "✅ All checks passed - architecture matches code"

    output = ""
    for disc in consistency.get("discrepancies", []):
        output += f"- {disc.get('type', 'unknown')}: {disc.get('message', str(disc))}\n"

    if consistency.get("suggestions"):
        output += "\n**Suggestions:**\n"
        for sug in consistency["suggestions"]:
            output += f"- {sug}\n"

    return output


# Convenience export
__all__ = ["create_architect_subgraph"]
