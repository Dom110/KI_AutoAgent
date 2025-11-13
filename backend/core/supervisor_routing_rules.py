"""
🏗️ SUPERVISOR ROUTING RULES v7.0 (PURE MCP)

This module implements the decision-making logic for the Supervisor Agent
in the Create/Develop App workflow.

Key Functions:
- Route to correct agent based on state
- Validate state transitions
- Generate instructions for each agent
- Handle error conditions and loops

Author: KI AutoAgent v7.0
Date: 2025-11-03
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Constants
# ============================================================================

class WorkflowMode(str, Enum):
    """Workflow modes for Create/Develop App."""
    CREATE = "create"  # New app from scratch
    DEVELOP = "develop"  # Extend existing app
    REFACTOR = "refactor"  # Improve architecture
    FIX = "fix"  # Fix issues
    ANALYZE = "analyze"  # Analyze only


class ArchitectureState(str, Enum):
    """Architecture lifecycle states."""
    NONE = "none"  # No architecture exists
    PARTIAL = "partial"  # Incomplete architecture
    COMPLETE = "complete"  # Full architecture
    NEEDS_REVIEW = "needs_review"  # Ready for HITL


class CodeState(str, Enum):
    """Code generation states."""
    NONE = "none"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    NEEDS_FIX = "needs_fix"


class ValidationState(str, Enum):
    """Code validation states."""
    NOT_RUN = "not_run"
    PASSED = "passed"
    FAILED = "failed"
    WARNINGS = "warnings"


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class RoutingDecision:
    """Decision output from routing logic."""
    next_agent: str  # "architect", "research", "codesmith", "reviewfix", "responder", "hitl", or "end"
    instructions: str  # Specific instructions for the next agent
    state_updates: Dict[str, Any]  # State fields to update
    confidence: float  # 0.0 to 1.0
    reasoning: str  # Explanation of the decision
    alternatives: Optional[List[str]] = None  # Alternative paths considered


@dataclass
class WorkflowContext:
    """Current workflow context."""
    mode: WorkflowMode
    user_query: str
    workspace_path: str
    last_agent: Optional[str]
    iteration: int
    
    # Architecture
    architecture: Optional[Dict[str, Any]]
    arch_state: ArchitectureState
    
    # Code
    generated_files: Optional[List[str]]
    code_state: CodeState
    
    # Validation
    validation_results: Optional[Dict[str, Any]]
    validation_state: ValidationState
    
    # Research
    research_context: Optional[Dict[str, Any]]
    needs_research: bool
    
    # History
    errors: List[str]
    agent_call_count: Dict[str, int]  # Track how many times each agent called


# ============================================================================
# Supervisor Routing Logic
# ============================================================================

class SupervisorRoutingRules:
    """
    ⚠️ MCP BLEIBT: Supervisor routing decision logic.
    
    This class implements all routing rules for the Create/Develop App workflow.
    """

    def __init__(self):
        """Initialize routing rules."""
        self.max_agent_calls = 3  # Max times same agent can be called
        self.max_iterations = 20  # Max total iterations
        self.loop_threshold = 3  # Iterations before HITL on loop

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def decide_next_agent(self, context: WorkflowContext) -> RoutingDecision:
        """
        Main decision function: Determine which agent to call next.
        
        Args:
            context: Current workflow context
            
        Returns:
            RoutingDecision with next agent and instructions
        """
        
        logger.info(f"🤔 Supervisor deciding next agent (iteration {context.iteration})")
        
        # Check termination conditions first
        if self._should_terminate(context):
            return self._decision_end(context, "Workflow terminated: check conditions")
        
        # Route based on workflow state
        if context.last_agent is None:
            # First agent always ARCHITECT
            return self._route_to_architect_initial(context)
        
        # Route based on last agent completed
        if context.last_agent == "architect":
            return self._decide_after_architect(context)
        
        elif context.last_agent == "research":
            return self._decide_after_research(context)
        
        elif context.last_agent == "codesmith":
            return self._decide_after_codesmith(context)
        
        elif context.last_agent == "reviewfix":
            return self._decide_after_reviewfix(context)
        
        elif context.last_agent == "hitl":
            return self._decide_after_hitl(context)
        
        else:
            return self._decision_error(context, f"Unknown last_agent: {context.last_agent}")

    # ========================================================================
    # TERMINATION LOGIC
    # ========================================================================

    def _should_terminate(self, context: WorkflowContext) -> bool:
        """Check if workflow should terminate."""
        
        # Check max iterations
        if context.iteration > self.max_iterations:
            logger.warning(f"⚠️ Max iterations ({self.max_iterations}) exceeded")
            return True
        
        # Check too many errors
        if len(context.errors) > 3:
            logger.error(f"❌ Too many errors ({len(context.errors)})")
            return True
        
        # Check response ready (after responder)
        # This would be checked in state dict, not here
        
        return False

    def _decision_end(
        self,
        context: WorkflowContext,
        reason: str
    ) -> RoutingDecision:
        """Create decision to end workflow."""
        return RoutingDecision(
            next_agent="end",
            instructions=reason,
            state_updates={"response_ready": True},
            confidence=1.0,
            reasoning=f"Workflow termination: {reason}"
        )

    def _decision_error(
        self,
        context: WorkflowContext,
        error_msg: str
    ) -> RoutingDecision:
        """Create decision to handle error."""
        return RoutingDecision(
            next_agent="responder",
            instructions=f"Error occurred: {error_msg}",
            state_updates={
                "response_ready": True,
                "error": error_msg,
                "error_count": len(context.errors) + 1
            },
            confidence=0.5,
            reasoning=f"Error handling: {error_msg}"
        )

    # ========================================================================
    # ARCHITECT ROUTING
    # ========================================================================

    def _route_to_architect_initial(
        self,
        context: WorkflowContext
    ) -> RoutingDecision:
        """Route to architect for initial architecture design."""
        
        instructions = f"""You are the Architect. Your task: Design the architecture for this app.

User Request: {context.user_query}
Workspace: {context.workspace_path}

Steps:
1. Check if architecture files already exist in the workspace
2. If NOT: Design new architecture from scratch
   - Choose appropriate framework and database
   - Design layers and components
   - Create mermaid diagram
3. If YES: Analyze existing architecture
   - Does the request ask for improvements?
   - If yes: Plan improvements (might need research)
   - If no: Use existing as-is

Provide: architecture.json with complete design details
"""
        
        return RoutingDecision(
            next_agent="architect",
            instructions=instructions,
            state_updates={"last_agent": "architect", "iteration": context.iteration + 1},
            confidence=1.0,
            reasoning="Initial workflow: Always start with Architect"
        )

    def _decide_after_architect(
        self,
        context: WorkflowContext
    ) -> RoutingDecision:
        """Decide next agent after Architect completes."""
        
        # Check if architect requested research
        if context.needs_research:
            return self._route_to_research(
                context,
                research_request=context.research_context.get("request") if context.research_context else None
            )
        
        # Check if HITL needed (complex refactor)
        if context.arch_state == ArchitectureState.NEEDS_REVIEW:
            return self._route_to_hitl(context, "Architect has proposed architecture changes for review")
        
        # Architecture complete, go to Codesmith
        if context.arch_state == ArchitectureState.COMPLETE:
            return self._route_to_codesmith(context)
        
        # Unexpected state
        return self._decision_error(context, f"Unexpected architecture state: {context.arch_state}")

    # ========================================================================
    # RESEARCH ROUTING
    # ========================================================================

    def _route_to_research(
        self,
        context: WorkflowContext,
        research_request: str
    ) -> RoutingDecision:
        """Route to Research Agent."""
        
        instructions = f"""You are the Research Agent. Research the following topic:

Topic: {research_request}
Context: {context.user_query}

Find:
1. Best practices for the topic
2. Popular tools/frameworks
3. Common patterns and anti-patterns
4. Performance considerations

Return: research_context with findings and recommendations
"""
        
        return RoutingDecision(
            next_agent="research",
            instructions=instructions,
            state_updates={"last_agent": "research"},
            confidence=0.9,
            reasoning=f"Architect requested research: {research_request}"
        )

    def _decide_after_research(
        self,
        context: WorkflowContext
    ) -> RoutingDecision:
        """Decide next agent after Research completes."""
        
        # Always route back to Architect with research context
        instructions = f"""You are the Architect. Re-design with research findings.

Research Findings:
{self._format_research_context(context.research_context)}

Original Request: {context.user_query}

Now design/improve the architecture considering these research findings:
1. Update technology choices based on findings
2. Improve architecture design
3. Create updated mermaid diagram
4. Provide architecture.json

Output: Complete, research-informed architecture
"""
        
        return RoutingDecision(
            next_agent="architect",
            instructions=instructions,
            state_updates={"last_agent": "architect"},
            confidence=0.9,
            reasoning="Research complete: Back to Architect to apply findings"
        )

    # ========================================================================
    # CODESMITH ROUTING
    # ========================================================================

    def _route_to_codesmith(self, context: WorkflowContext) -> RoutingDecision:
        """Route to Codesmith for code generation."""
        
        if not context.architecture:
            return self._decision_error(context, "No architecture provided to Codesmith")
        
        instructions = f"""You are the Codesmith. Generate code based on architecture.

Original Request: {context.user_query}
Workspace: {context.workspace_path}

Architecture: {self._format_architecture(context.architecture)}

Your Task:
1. Follow the architecture design exactly
2. Create all files specified in architecture.files
3. Implement all CRUD operations as designed
4. Use correct imports and dependencies
5. Write clean, well-documented code
6. Handle errors gracefully

Output: Write all files to workspace, list generated_files
"""
        
        return RoutingDecision(
            next_agent="codesmith",
            instructions=instructions,
            state_updates={"last_agent": "codesmith"},
            confidence=0.95,
            reasoning="Architecture complete: Time to generate code"
        )

    def _decide_after_codesmith(
        self,
        context: WorkflowContext
    ) -> RoutingDecision:
        """Decide next agent after Codesmith completes."""
        
        if context.code_state != CodeState.COMPLETE:
            return self._decision_error(context, f"Code generation failed: {context.code_state}")
        
        # Go to ReviewFix for validation
        return self._route_to_reviewfix(context)

    # ========================================================================
    # REVIEWFIX ROUTING
    # ========================================================================

    def _route_to_reviewfix(self, context: WorkflowContext) -> RoutingDecision:
        """Route to ReviewFix for code validation."""
        
        if not context.generated_files:
            return self._decision_error(context, "No generated files to validate")
        
        instructions = f"""You are ReviewFix. Validate the generated code.

Architecture Reference:
{self._format_architecture(context.architecture)}

Generated Files: {', '.join(context.generated_files) if context.generated_files else 'None'}
Workspace: {context.workspace_path}

Validation Checklist:
1. ✅ Do generated files match architecture design?
2. ✅ Are all CRUD operations implemented?
3. ✅ Error handling present?
4. ✅ No syntax errors?
5. ✅ Dependencies correct?
6. ✅ Would the app run and work?

Output: validation_results with:
- passed: true/false
- issues: list of problems found (if any)
- suggestions: improvements (if any)
"""
        
        return RoutingDecision(
            next_agent="reviewfix",
            instructions=instructions,
            state_updates={"last_agent": "reviewfix"},
            confidence=0.95,
            reasoning="Code generation complete: Validate implementation"
        )

    def _decide_after_reviewfix(
        self,
        context: WorkflowContext
    ) -> RoutingDecision:
        """Decide next agent after ReviewFix completes."""
        
        if context.validation_state == ValidationState.PASSED:
            # Code is good, go to Responder
            return self._route_to_responder(context, validation_passed=True)
        
        elif context.validation_state == ValidationState.FAILED:
            # Check how many times Codesmith already tried
            if context.agent_call_count.get("codesmith", 0) >= self.max_agent_calls:
                # Too many attempts, go to Responder with error
                return self._route_to_responder(
                    context,
                    validation_passed=False,
                    error_msg="Code generation failed after multiple attempts"
                )
            else:
                # Route back to Codesmith to fix issues
                issues_text = self._format_validation_issues(context.validation_results)
                instructions = f"""You are Codesmith. Fix the code issues.

Issues to fix:
{issues_text}

Original Architecture:
{self._format_architecture(context.architecture)}

Workspace: {context.workspace_path}

Re-generate the code fixing these specific issues.
"""
                
                return RoutingDecision(
                    next_agent="codesmith",
                    instructions=instructions,
                    state_updates={
                        "last_agent": "codesmith",
                        "code_state": CodeState.IN_PROGRESS
                    },
                    confidence=0.8,
                    reasoning=f"Code validation failed with issues: {len(context.validation_results.get('issues', []))} issues"
                )
        
        elif context.validation_state == ValidationState.WARNINGS:
            # Warnings but acceptable, go to Responder
            return self._route_to_responder(context, validation_passed=True)
        
        else:
            return self._decision_error(context, f"Invalid validation state: {context.validation_state}")

    # ========================================================================
    # HITL (Human-in-the-Loop) ROUTING
    # ========================================================================

    def _route_to_hitl(
        self,
        context: WorkflowContext,
        reason: str
    ) -> RoutingDecision:
        """Route to HITL for human review/approval."""
        
        instructions = f"""Present architecture proposal to user for review.

Reason for Review: {reason}

Current Architecture:
{self._format_architecture(context.architecture)}

Mermaid Diagram:
{context.architecture.get('mermaid_diagram', 'N/A') if context.architecture else 'N/A'}

Research Context (if applicable):
{self._format_research_context(context.research_context)}

Ask user:
1. "Does this architecture look good?"
2. "Any changes you'd like?"

Return: User response (approve/decline + feedback)
"""
        
        return RoutingDecision(
            next_agent="hitl",
            instructions=instructions,
            state_updates={
                "last_agent": "hitl",
                "awaiting_human": True
            },
            confidence=0.9,
            reasoning=reason
        )

    def _decide_after_hitl(
        self,
        context: WorkflowContext
    ) -> RoutingDecision:
        """Decide next agent after HITL response."""
        
        hitl_response = context.research_context.get("hitl_response", "").lower() if context.research_context else ""
        
        if "approve" in hitl_response or "yes" in hitl_response or "ok" in hitl_response:
            # User approved, go to Codesmith
            return self._route_to_codesmith(context)
        
        else:
            # User wants changes, route back to Architect with feedback
            instructions = f"""You are Architect. User has feedback on the architecture.

User Feedback:
{context.research_context.get('hitl_response', 'No specific feedback')}

Current Architecture:
{self._format_architecture(context.architecture)}

Revise the architecture based on user feedback:
1. Address user's concerns
2. Update design accordingly
3. Create new mermaid diagram
4. Provide updated architecture.json

Output: Revised architecture
"""
            
            return RoutingDecision(
                next_agent="architect",
                instructions=instructions,
                state_updates={
                    "last_agent": "architect",
                    "awaiting_human": False
                },
                confidence=0.85,
                reasoning="User feedback received: Back to Architect to revise"
            )

    # ========================================================================
    # RESPONDER ROUTING
    # ========================================================================

    def _route_to_responder(
        self,
        context: WorkflowContext,
        validation_passed: bool = True,
        error_msg: Optional[str] = None
    ) -> RoutingDecision:
        """Route to Responder for user communication."""
        
        instructions = f"""You are Responder. Communicate results to user.

Validation Passed: {validation_passed}
{f"Error: {error_msg}" if error_msg else ""}

Architecture:
{self._format_architecture(context.architecture)}

Generated Files: {', '.join(context.generated_files) if context.generated_files else 'None'}

Validation Results:
{self._format_validation_results(context.validation_results)}

Format your response:
1. ✅ Summary: What was created/improved
2. 📋 Architecture: Show the design (use mermaid if available)
3. 📁 Files: List what was created
4. 🧪 Testing: How to test the app
5. 🚀 Next Steps: What comes next

Make it beautiful and clear for the user!
"""
        
        return RoutingDecision(
            next_agent="responder",
            instructions=instructions,
            state_updates={
                "last_agent": "responder",
                "response_ready": True
            },
            confidence=0.95,
            reasoning="All processing complete: Communicate to user"
        )

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _format_architecture(self, architecture: Optional[Dict]) -> str:
        """Format architecture dict to readable string."""
        if not architecture:
            return "No architecture available"
        
        text = f"""
Framework: {architecture.get('framework', 'N/A')}
Database: {architecture.get('database', 'N/A')}
Layers: {', '.join(architecture.get('layers', {}).keys())}
Key Files: {', '.join([f.get('path', '?') for f in architecture.get('files', [])[:3]])}
"""
        return text.strip()

    def _format_research_context(self, research_context: Optional[Dict]) -> str:
        """Format research context to readable string."""
        if not research_context:
            return "No research context available"
        
        findings = research_context.get('findings', [])
        return f"""
Findings ({len(findings)} items):
{chr(10).join([f"- {f.get('summary', '?')[:100]}" for f in findings[:3]])}
"""

    def _format_validation_results(self, validation_results: Optional[Dict]) -> str:
        """Format validation results to readable string."""
        if not validation_results:
            return "No validation results available"
        
        issues = validation_results.get('issues', [])
        return f"Issues: {len(issues)}\n" + \
               "\n".join([f"- {issue}" for issue in issues[:5]])

    def _format_validation_issues(self, validation_results: Optional[Dict]) -> str:
        """Format validation issues for Codesmith fix."""
        if not validation_results:
            return "No specific issues found"
        
        issues = validation_results.get('issues', [])
        return "\n".join([f"{i+1}. {issue}" for i, issue in enumerate(issues)])


# ============================================================================
# Singleton Instance
# ============================================================================

_routing_rules_instance: Optional[SupervisorRoutingRules] = None


def get_supervisor_routing_rules() -> SupervisorRoutingRules:
    """Get singleton instance of routing rules."""
    global _routing_rules_instance
    if _routing_rules_instance is None:
        _routing_rules_instance = SupervisorRoutingRules()
    return _routing_rules_instance