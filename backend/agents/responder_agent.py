"""
Responder Agent - The ONLY User-Facing Agent in v7.0

This agent is responsible for formatting ALL responses that go to users.
No other agent should ever communicate directly with users!

Key Responsibilities:
- Collect results from all agents
- Format into readable responses
- Create markdown output
- Summarize complex technical details
- Present errors in user-friendly way

Author: KI AutoAgent Team
Version: 7.0.0-alpha
Date: 2025-10-20
"""

from __future__ import annotations

import json
import logging
from typing import Any

# Setup logging
logger = logging.getLogger(__name__)


class ResponderAgent:
    """
    The ONLY agent that formats responses for users.

    This ensures consistent, readable output regardless of
    which agents were involved in the workflow.
    """

    def __init__(self):
        """Initialize the Responder agent."""
        logger.info("💬 ResponderAgent initialized")

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute responder to format user response.

        Args:
            state: Contains:
                - instructions: What to respond about
                - all_results: Accumulated results from all agents

        Returns:
            Dictionary with user_response field
        """
        instructions = state.get("instructions", "")
        all_results = state.get("all_results", {})

        logger.info(f"📝 Formatting response: {instructions[:100]}...")

        # Extract results from different agents
        research_context = all_results.get("research_context", {})
        architecture = all_results.get("architecture", {})
        generated_files = all_results.get("generated_files", [])
        validation_results = all_results.get("validation_results", {})
        issues = all_results.get("issues", [])

        # Determine what type of response to create
        response = self._format_response(
            instructions,
            research_context,
            architecture,
            generated_files,
            validation_results,
            issues
        )

        logger.info("✅ Response formatted successfully")

        return {
            "user_response": response,
            "response_ready": True
        }

    def _format_response(
        self,
        instructions: str,
        research_context: dict,
        architecture: dict,
        generated_files: list,
        validation_results: dict,
        issues: list
    ) -> str:
        """
        Format the response based on available data.

        This method determines what kind of response to create
        based on what data is available.
        """
        response_parts = []

        # Add header based on instructions
        if "explain" in instructions.lower() or "analyze" in instructions.lower():
            response_parts.append(self._format_explanation_header())
        elif "create" in instructions.lower() or "implement" in instructions.lower():
            response_parts.append(self._format_creation_header())
        elif "fix" in instructions.lower() or "debug" in instructions.lower():
            response_parts.append(self._format_fix_header())
        else:
            response_parts.append("## Task Completed\n")

        # Add research findings if available
        if research_context:
            response_parts.append(self._format_research(research_context))

        # Add architecture description if available
        if architecture:
            response_parts.append(self._format_architecture(architecture))

        # Add generated files summary if available
        if generated_files:
            response_parts.append(self._format_generated_files(generated_files))

        # Add validation results if available
        if validation_results:
            response_parts.append(self._format_validation(validation_results))

        # Add issues/warnings if any
        if issues:
            response_parts.append(self._format_issues(issues))

        # Combine all parts
        response = "\n\n".join(filter(None, response_parts))

        # Add footer
        response += self._format_footer()

        return response

    def _format_explanation_header(self) -> str:
        """Format header for explanation responses."""
        return """## 📊 Analysis Complete

I've analyzed your request and here are my findings:
"""

    def _format_creation_header(self) -> str:
        """Format header for creation responses."""
        return """## ✅ Implementation Complete

I've successfully created the requested implementation:
"""

    def _format_fix_header(self) -> str:
        """Format header for fix/debug responses."""
        return """## 🔧 Fix Applied

I've identified and addressed the issues:
"""

    def _format_research(self, context: dict) -> str:
        """Format research findings."""
        parts = ["### 🔍 Research Findings\n"]

        if "workspace_analysis" in context:
            analysis = context["workspace_analysis"]
            parts.append("**Workspace Analysis:**")
            parts.append(f"- Files found: {analysis.get('file_count', 'Unknown')}")
            parts.append(f"- Project type: {analysis.get('project_type', 'Unknown')}")
            parts.append(f"- Languages: {', '.join(analysis.get('languages', ['Unknown']))}")

        if "web_results" in context:
            results = context["web_results"]
            parts.append("\n**Web Research:**")
            for result in results[:3]:  # Top 3 results
                parts.append(f"- {result.get('title', 'Untitled')}")
                parts.append(f"  {result.get('summary', '')[:100]}...")

        if "error_analysis" in context:
            analysis = context["error_analysis"]
            parts.append("\n**Error Analysis:**")
            parts.append(f"- Root cause: {analysis.get('root_cause', 'Unknown')}")
            parts.append(f"- Suggested fix: {analysis.get('suggested_fix', 'None')}")

        return "\n".join(parts) if len(parts) > 1 else ""

    def _format_architecture(self, architecture: dict) -> str:
        """Format architecture description."""
        parts = ["### 📐 System Architecture\n"]

        if "description" in architecture:
            parts.append(f"**Overview:** {architecture['description']}")

        if "components" in architecture:
            parts.append("\n**Components:**")
            components = architecture["components"]
            # Handle both list of dicts and list of strings
            for component in components:
                if isinstance(component, dict):
                    name = component.get('name', 'Unknown')
                    desc = component.get('description', '')
                    parts.append(f"- **{name}**: {desc}")
                elif isinstance(component, str):
                    parts.append(f"- {component}")
                else:
                    parts.append(f"- {str(component)}")

        if "file_structure" in architecture:
            parts.append("\n**File Structure:**")
            parts.append("```")
            for file in architecture["file_structure"]:
                parts.append(file)
            parts.append("```")

        if "technologies" in architecture:
            parts.append(f"\n**Technologies:** {', '.join(architecture['technologies'])}")

        return "\n".join(parts) if len(parts) > 1 else ""

    def _format_generated_files(self, files: list) -> str:
        """Format generated files summary."""
        if not files:
            return ""

        parts = ["### 📁 Generated Files\n"]
        parts.append(f"Successfully generated **{len(files)} files**:\n")

        for file in files[:10]:  # Show max 10 files
            if isinstance(file, dict):
                path = file.get("path", "unknown")
                lines = file.get("lines", 0)
                parts.append(f"- `{path}` ({lines} lines)")
            else:
                parts.append(f"- `{file}`")

        if len(files) > 10:
            parts.append(f"- ... and {len(files) - 10} more files")

        return "\n".join(parts)

    def _format_validation(self, results: dict) -> str:
        """Format validation results."""
        parts = ["### ✔️ Validation Results\n"]

        passed = results.get("passed", False)
        score = results.get("quality_score", 0.0)

        if passed:
            parts.append(f"✅ **All checks passed!** (Quality Score: {score:.2f}/1.0)")
        else:
            parts.append(f"⚠️ **Some checks need attention** (Quality Score: {score:.2f}/1.0)")

        if "checks" in results:
            parts.append("\n**Checks performed:**")
            for check in results["checks"]:
                status = "✅" if check.get("passed") else "❌"
                parts.append(f"- {status} {check.get('name', 'Unknown check')}")

        if "suggestions" in results:
            parts.append("\n**Suggestions:**")
            for suggestion in results["suggestions"][:5]:
                parts.append(f"- {suggestion}")

        return "\n".join(parts) if len(parts) > 1 else ""

    def _format_issues(self, issues: list) -> str:
        """Format issues/warnings."""
        if not issues:
            return ""

        parts = ["### ⚠️ Issues to Note\n"]

        for i, issue in enumerate(issues[:5], 1):
            if isinstance(issue, dict):
                parts.append(f"{i}. **{issue.get('type', 'Issue')}**: {issue.get('message', 'No description')}")
                if "fix" in issue:
                    parts.append(f"   - Suggested fix: {issue['fix']}")
            else:
                parts.append(f"{i}. {issue}")

        if len(issues) > 5:
            parts.append(f"\n*Plus {len(issues) - 5} more issues...*")

        return "\n".join(parts)

    def _format_footer(self) -> str:
        """Add footer to response."""
        return """

---

*This response was generated by the KI AutoAgent v7.0 Supervisor System.*
*For questions or issues, please provide more details or clarification.*"""


# ============================================================================
# Export
# ============================================================================

__all__ = ["ResponderAgent"]