"""
KI AutoAgent v6.0 - State Schemas

This module defines ALL state schemas for the v6.0 LangGraph workflow.

Architecture:
- SupervisorState: Main orchestrator state
- ResearchState: Research subgraph state
- ArchitectState: Architect subgraph state
- CodesmithState: Codesmith subgraph state
- ReviewFixState: ReviewFix loop state

Best Practices:
- TypedDict for type safety (Python 3.13)
- Annotated fields for reducers (operator.add for lists)
- Flat structure where possible
- Clear field names and types

Reference:
- LangGraph State docs: https://langchain-ai.github.io/langgraph/concepts/low_level/#state
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


# ============================================================================
# SUPERVISOR STATE (Main Orchestrator)
# ============================================================================

class SupervisorState(TypedDict):
    """
    Main state for the SupervisorGraph (Orchestrator).

    This state is passed between all subgraphs and accumulates results
    from each agent in the workflow.

    Flow:
    1. User sends query → user_query, workspace_path set
    2. Research → populates research_results
    3. Architect → populates architecture_design
    4. Codesmith → populates generated_files
    5. ReviewFix → populates review_feedback
    6. Supervisor → populates final_result

    Errors are accumulated across all agents using operator.add.
    """

    # Input from user
    user_query: str
    workspace_path: str

    # NEW v6.2: Intent Detection
    intent: str | None  # "create", "fix", "refactor", "explain"
    workflow_path: list[str] | None  # ["research", "architect", ...] or ["reviewfix"]

    # Results from each subgraph
    research_results: dict[str, Any] | None
    architecture_design: dict[str, Any] | None
    generated_files: list[dict[str, Any]]
    review_feedback: dict[str, Any] | None

    # Final output
    final_result: Any | None

    # Accumulated errors (using reducer)
    errors: Annotated[list[dict[str, Any]], operator.add]


# ============================================================================
# RESEARCH STATE (Research Subgraph)
# ============================================================================

class ResearchState(TypedDict):
    """
    State for ResearchSubgraph (create_react_agent with Perplexity tools).

    Agent: Research Agent
    Model: Perplexity Sonar Huge 128k
    Implementation: create_react_agent()

    Responsibilities:
    - Web search for best practices
    - Documentation gathering
    - Technology research

    Memory Integration:
    - Stores findings with tags: ["research", "documentation", "technology"]

    Asimov:
    - Permission: can_web_search
    """

    # Input
    query: str
    workspace_path: str

    # Research results
    findings: dict[str, Any]
    sources: list[str]

    # Generated report (Markdown)
    report: str

    # Errors
    errors: Annotated[list[dict[str, Any]], operator.add]


# ============================================================================
# ARCHITECT STATE (Architect Subgraph)
# ============================================================================

class ArchitectState(TypedDict):
    """
    State for ArchitectSubgraph (custom implementation).

    Agent: Architect Agent
    Model: GPT-4o
    Implementation: Custom (too specialized for create_react_agent)

    Responsibilities:
    - System design and architecture
    - Technology stack selection
    - Design pattern recommendations
    - Diagram generation (Mermaid, GraphViz)

    Memory Integration:
    - Reads: Research results
    - Stores: Architecture design with tags ["architecture", "design", "patterns"]

    Tree-Sitter:
    - Analyzes existing codebase structure

    Asimov:
    - Permission: can_analyze_codebase
    """

    # Input
    workspace_path: str
    user_requirements: str

    # Context from previous agents (via Memory)
    research_context: dict[str, Any]

    # Architecture outputs
    design: dict[str, Any]
    tech_stack: list[str]
    patterns: list[dict[str, Any]]

    # Generated artifacts
    diagram: str  # Mermaid diagram
    adr: str  # Architecture Decision Record (Markdown)

    # Errors
    errors: Annotated[list[dict[str, Any]], operator.add]


# ============================================================================
# CODESMITH STATE (Codesmith Subgraph)
# ============================================================================

class CodesmithState(TypedDict):
    """
    State for CodesmithSubgraph (create_react_agent with file tools).

    Agent: Codesmith Agent
    Model: Claude Sonnet 4.1
    Implementation: create_react_agent()

    Responsibilities:
    - Code generation (multi-language)
    - File creation/editing
    - Test generation
    - API documentation generation

    Memory Integration:
    - Reads: Architect design, Research best practices
    - Stores: Implementation with tags ["implementation", "code", "files"]

    Tree-Sitter:
    - Validates own generated code BEFORE writing
    - Parses code for documentation generation

    Asimov:
    - Permission: can_write_files
    - Validates: Workspace boundaries, no overwrites without permission
    """

    # Input
    workspace_path: str
    requirements: str

    # Context from previous agents (via Memory)
    design: dict[str, Any]
    research: dict[str, Any]
    past_successes: list[dict[str, Any]]  # From Learning System

    # Implementation outputs
    generated_files: list[dict[str, Any]]
    """
    Format:
    {
        "path": str,
        "content": str,
        "language": str,
        "validated": bool  # Tree-Sitter validation result
    }
    """

    tests: list[dict[str, Any]]
    """
    Format:
    {
        "path": str,
        "content": str,
        "framework": str  # "pytest", "jest", etc.
    }
    """

    # Generated documentation (Markdown)
    api_docs: str

    # Errors
    errors: Annotated[list[dict[str, Any]], operator.add]


# ============================================================================
# REVIEWFIX STATE (ReviewFix Loop Subgraph)
# ============================================================================

class ReviewFixState(TypedDict):
    """
    State for ReviewFixSubgraph (custom loop with Reviewer + Fixer).

    Agents: Reviewer Agent + Fixer Agent
    Models: GPT-4o-mini (Reviewer), Claude Sonnet 4.1 (Fixer)
    Implementation: Custom loop subgraph

    Loop Logic:
    1. Reviewer analyzes code → quality_score
    2. If quality_score < threshold (0.75):
       - Fixer fixes issues
       - GOTO step 1 (max 3 iterations)
    3. If quality_score >= threshold:
       - Accept implementation
       - Store success in Learning System

    Reviewer Responsibilities:
    - Code quality analysis
    - Security vulnerability detection
    - Asimov rule enforcement (ENFORCER role)
    - Best practices validation

    Fixer Responsibilities:
    - Bug analysis and fixing
    - Code optimization
    - Error correction

    Memory Integration:
    - Reviewer reads: Implementation, Design
    - Reviewer stores: Review feedback with tags ["review", "quality", "security"]
    - Fixer reads: Review feedback
    - Fixer stores: Fix history with tags ["fix", "debugging", "optimization"]

    Tree-Sitter:
    - Reviewer: Deep code analysis
    - Fixer: Bug location via AST

    Asimov:
    - Reviewer: ENFORCES all rules (validates ALL agent actions)
    - Fixer: Validates write permissions
    """

    # Input
    workspace_path: str
    generated_files: list[dict[str, Any]]
    files_to_review: list[str]  # ← NEW! File paths extracted for review
    design: dict[str, Any]  # From Memory

    # Review results
    quality_score: float  # 0.0 - 1.0
    review_feedback: dict[str, Any]
    """
    Format:
    {
        "issues": list[dict],  # Security, quality, style issues
        "asimov_validation": dict,  # Asimov compliance check
        "suggestions": list[str],
        "critical_errors": list[str]
    }
    """

    # Fix results
    fixes_applied: list[dict[str, Any]]
    """
    Format:
    {
        "file": str,
        "issue": str,
        "fix_type": str,
        "old_code": str,
        "new_code": str
    }
    """

    # Loop control
    iteration: int  # Current iteration (max 3)
    should_continue: bool  # Continue loop or finish

    # Errors
    errors: Annotated[list[dict[str, Any]], operator.add]


# ============================================================================
# STATE TRANSFORMATIONS (Supervisor ↔ Subgraphs)
# ============================================================================

def supervisor_to_research(state: SupervisorState) -> ResearchState:
    """
    Transform SupervisorState to ResearchState.

    Called when Supervisor invokes Research subgraph.
    """
    return {
        "query": state["user_query"],
        "workspace_path": state["workspace_path"],
        "findings": {},
        "sources": [],
        "report": "",
        "errors": []
    }


def research_to_supervisor(research_state: ResearchState) -> dict[str, Any]:
    """
    Transform ResearchState back to SupervisorState fields.

    Called after Research subgraph completes.
    Returns dict to merge into SupervisorState.
    """
    return {
        "research_results": {
            "findings": research_state["findings"],
            "sources": research_state["sources"],
            "report": research_state["report"]
        }
    }


def supervisor_to_architect(state: SupervisorState) -> ArchitectState:
    """
    Transform SupervisorState to ArchitectState.

    Called when Supervisor invokes Architect subgraph.
    Note: research_context will be populated from Memory, not state.
    """
    return {
        "workspace_path": state["workspace_path"],
        "user_requirements": state["user_query"],
        "research_context": {},  # Populated from Memory in agent
        "design": {},
        "tech_stack": [],
        "patterns": [],
        "diagram": "",
        "adr": "",
        "errors": []
    }


def architect_to_supervisor(architect_state: ArchitectState) -> dict[str, Any]:
    """
    Transform ArchitectState back to SupervisorState fields.

    Called after Architect subgraph completes.
    """
    return {
        "architecture_design": {
            "design": architect_state["design"],
            "tech_stack": architect_state["tech_stack"],
            "patterns": architect_state["patterns"],
            "diagram": architect_state["diagram"],
            "adr": architect_state["adr"]
        }
    }


def supervisor_to_codesmith(state: SupervisorState) -> CodesmithState:
    """
    Transform SupervisorState to CodesmithState.

    Called when Supervisor invokes Codesmith subgraph.
    Note: design, research, past_successes populated from Memory.
    """
    return {
        "workspace_path": state["workspace_path"],
        "requirements": state["user_query"],
        "design": {},  # Populated from Memory in agent
        "research": {},  # Populated from Memory in agent
        "past_successes": [],  # Populated from Learning System in agent
        "generated_files": [],
        "tests": [],
        "api_docs": "",
        "errors": []
    }


def codesmith_to_supervisor(codesmith_state: CodesmithState) -> dict[str, Any]:
    """
    Transform CodesmithState back to SupervisorState fields.

    Called after Codesmith subgraph completes.
    """
    return {
        "generated_files": codesmith_state["generated_files"]
    }


def supervisor_to_reviewfix(state: SupervisorState) -> ReviewFixState:
    """
    Transform SupervisorState to ReviewFixState.

    Called when Supervisor invokes ReviewFix subgraph.
    Note: design populated from Memory.
    """
    # Extract file paths from generated_files for ReviewFix
    generated_files = state["generated_files"]
    files_to_review = []

    for file_info in generated_files:
        if isinstance(file_info, dict):
            # Try different possible keys for file path
            file_path = file_info.get("path") or file_info.get("file_path") or file_info.get("filepath")
            if file_path:
                files_to_review.append(file_path)
        elif isinstance(file_info, str):
            # If it's just a string, use it directly
            files_to_review.append(file_info)

    return {
        "workspace_path": state["workspace_path"],
        "generated_files": state["generated_files"],
        "files_to_review": files_to_review,  # ← NEW! Extract file paths for ReviewFix
        "design": {},  # Populated from Memory in agent
        "quality_score": 0.0,
        "review_feedback": {},
        "fixes_applied": [],
        "iteration": 0,
        "should_continue": True,
        "errors": []
    }


def reviewfix_to_supervisor(reviewfix_state: ReviewFixState) -> dict[str, Any]:
    """
    Transform ReviewFixState back to SupervisorState fields.

    Called after ReviewFix subgraph completes.
    """
    return {
        "review_feedback": {
            "quality_score": reviewfix_state["quality_score"],
            "feedback": reviewfix_state["review_feedback"],
            "fixes_applied": reviewfix_state["fixes_applied"],
            "iterations": reviewfix_state["iteration"]
        }
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_error(
    agent: str,
    error_type: str,
    message: str,
    context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Create standardized error dict for state.errors list.

    Usage:
        errors.append(create_error(
            agent="codesmith",
            error_type="FileWriteError",
            message="Permission denied: /etc/passwd",
            context={"file_path": "/etc/passwd"}
        ))
    """
    from datetime import datetime

    return {
        "agent": agent,
        "type": error_type,
        "message": message,
        "context": context or {},
        "timestamp": datetime.now().isoformat()
    }


def merge_errors(
    state_errors: list[dict[str, Any]],
    new_errors: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Merge errors using operator.add reducer.

    This is automatically handled by Annotated[list, operator.add],
    but provided as helper for manual merging if needed.
    """
    return state_errors + new_errors


# ============================================================================
# TYPE EXPORTS
# ============================================================================

__all__ = [
    # State types
    "SupervisorState",
    "ResearchState",
    "ArchitectState",
    "CodesmithState",
    "ReviewFixState",

    # Transformations
    "supervisor_to_research",
    "research_to_supervisor",
    "supervisor_to_architect",
    "architect_to_supervisor",
    "supervisor_to_codesmith",
    "codesmith_to_supervisor",
    "supervisor_to_reviewfix",
    "reviewfix_to_supervisor",

    # Helpers
    "create_error",
    "merge_errors"
]
