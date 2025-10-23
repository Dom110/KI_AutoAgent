"""
Architect Agent - System Design Specialist for v7.0

This agent designs system architecture based on research context.
It can request additional research when needed.

Key Responsibilities:
- Design system architecture
- Create file structures
- Select appropriate technologies
- Document design decisions
- Request research when context is insufficient

Author: KI AutoAgent Team
Version: 7.0.0-alpha
Date: 2025-10-21
"""

from __future__ import annotations

import json
import logging
from typing import Any
from datetime import datetime
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)


class ArchitectAgent:
    """
    System architect that designs based on research context.

    This agent creates comprehensive system designs but can
    request additional research through the supervisor when
    the context is insufficient.
    """

    def __init__(self):
        """Initialize the Architect agent with AI provider."""
        logger.info("📐 ArchitectAgent initializing...")

        try:
            # Get AI provider from factory
            from backend.utils.ai_factory import AIFactory
            self.ai_provider = AIFactory.get_provider_for_agent("architect")
            logger.info(f"   ✅ Using {self.ai_provider.provider_name} ({self.ai_provider.model})")
        except Exception as e:
            logger.error(f"   ❌ Failed to get AI provider: {e}")
            raise RuntimeError(
                "Architect requires an AI provider (OpenAI recommended). "
                "Set ARCHITECT_AI_PROVIDER and ARCHITECT_AI_MODEL in .env"
            ) from e

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute architecture design based on supervisor instructions.

        Args:
            state: Contains:
                - instructions: What to design
                - research_context: Context from Research agent
                - workspace_path: Target workspace

        Returns:
            Dictionary with architecture or research request
        """
        instructions = state.get("instructions", "")
        research_context = state.get("research_context", {})
        workspace_path = state.get("workspace_path", "")

        logger.info(f"🏗️ Designing architecture: {instructions[:100]}...")

        # Check if we have sufficient context
        if self._needs_more_research(instructions, research_context):
            logger.info("   📚 Requesting additional research")
            return {
                "needs_research": True,
                "research_request": self._formulate_research_request(instructions, research_context),
                "architecture_complete": False
            }

        # Design the architecture
        architecture = await self._design_architecture(
            instructions,
            research_context,
            workspace_path
        )

        logger.info(f"   ✅ Architecture designed: {len(architecture.get('components', []))} components")

        return {
            "architecture": architecture,
            "architecture_complete": True,
            "needs_research": False,
            "timestamp": datetime.now().isoformat()
        }

    def _needs_more_research(
        self,
        instructions: str,
        research_context: dict
    ) -> bool:
        """
        Determine if more research is needed before design.

        CRITICAL FIX: Only request research ONCE when context is empty.
        Otherwise we get infinite loops (recursion limit 25).

        The Research agent returns generic results, not specific keys
        like "tech_verification". Checking for specific keys causes loops.
        """
        # Only request research if we have NO context at all
        if not research_context or len(research_context) == 0:
            return True

        # If we have ANY research context, proceed with architecture
        # Don't check for specific keys - research agent doesn't guarantee them
        return False

    def _formulate_research_request(
        self,
        instructions: str,
        research_context: dict
    ) -> str:
        """
        Formulate specific research request based on what's missing.
        """
        requests = []

        if not research_context:
            requests.append("Analyze workspace structure and existing code")

        if "modify" in instructions.lower() and "workspace_analysis" not in research_context:
            requests.append("Analyze existing project structure and dependencies")

        if "fastapi" in instructions.lower() and "tech_verification" not in research_context:
            requests.append("Research FastAPI best practices and patterns")

        if "security" in instructions.lower() and "security_analysis" not in research_context:
            requests.append("Research security best practices for the requested features")

        return " AND ".join(requests) if requests else "Gather more context for architecture design"

    async def _design_architecture(
        self,
        instructions: str,
        research_context: dict,
        workspace_path: str
    ) -> dict[str, Any]:
        """
        Design the system architecture based on context.
        """
        logger.info("   🎨 Creating architecture design")

        architecture = {
            "description": "",
            "components": [],
            "file_structure": [],
            "technologies": [],
            "patterns": [],
            "data_flow": [],
            "created_at": datetime.now().isoformat()
        }

        # Extract insights from research context
        workspace_analysis = research_context.get("workspace_analysis", {})
        web_results = research_context.get("web_results", [])
        tech_verification = research_context.get("tech_verification", {})

        # Generate architecture with AI
        architecture = await self._generate_with_ai(
            instructions,
            research_context,
            workspace_analysis
        )

        # Add workspace-specific adjustments
        if workspace_analysis:
            architecture = self._adjust_for_workspace(
                architecture,
                workspace_analysis
            )

        return architecture

    async def _generate_with_ai(
        self,
        instructions: str,
        research_context: dict,
        workspace_analysis: dict
    ) -> dict[str, Any]:
        """
        Generate architecture using AI provider (OpenAI GPT-4o by default).
        """
        logger.info("   🤖 Generating architecture with AI...")

        # Build AI request
        from backend.utils.ai_factory import AIRequest

        request = AIRequest(
            prompt=self._build_architecture_prompt(instructions, research_context, workspace_analysis),
            system_prompt=self._get_architecture_system_prompt(),
            context={
                "instructions": instructions,
                "research_context": research_context,
                "workspace_analysis": workspace_analysis
            },
            temperature=0.4,  # Balanced between creativity and consistency
            max_tokens=4000
        )

        # Call AI provider
        response = await self.ai_provider.complete(request)

        if not response.success:
            logger.error(f"   ❌ AI architecture generation failed: {response.error}")
            raise RuntimeError(f"Architecture generation failed: {response.error}")

        # Parse response as JSON
        try:
            if "```json" in response.content:
                json_str = response.content.split("```json")[1].split("```")[0]
            else:
                json_str = response.content

            architecture = json.loads(json_str)
            architecture["provider"] = response.provider
            architecture["model"] = response.model
            return architecture

        except json.JSONDecodeError as e:
            logger.error(f"   ❌ Failed to parse architecture JSON: {e}")
            # Return minimal valid architecture
            return {
                "description": f"Architecture for: {instructions[:100]}",
                "components": [{"name": "Main Component", "description": "Core functionality"}],
                "file_structure": ["src/", "tests/"],
                "technologies": ["Python"],
                "patterns": ["MVC"],
                "data_flow": [],
                "provider": response.provider,
                "model": response.model,
                "parse_error": str(e)
            }

    def _get_architecture_system_prompt(self) -> str:
        """Get system prompt for architecture generation."""
        return """You are an expert software architect specializing in system design.

Your task is to design comprehensive system architectures based on:
- User instructions (what to build)
- Research context (best practices, patterns, documentation)
- Workspace analysis (existing code structure)

Requirements:
1. Design scalable, maintainable architectures
2. Select appropriate technologies and patterns
3. Create clear component structure
4. Define file organization
5. Document data flow between components
6. Follow modern best practices

Output Format (JSON):
{
  "description": "Overall system description",
  "components": [{"name": "...", "description": "..."}],
  "file_structure": ["path/to/file", ...],
  "technologies": ["Technology1", "Technology2", ...],
  "patterns": ["Pattern1", "Pattern2", ...],
  "data_flow": [{"from": "ComponentA", "to": "ComponentB", "description": "..."}]
}

Design production-ready, well-structured architectures."""

    def _build_architecture_prompt(
        self,
        instructions: str,
        research_context: dict,
        workspace_analysis: dict
    ) -> str:
        """Build detailed prompt for architecture generation."""
        prompt_parts = [
            "Design a system architecture based on the following:",
            "",
            "## Instructions",
            instructions,
            "",
            "## Workspace Context",
        ]

        if workspace_analysis:
            prompt_parts.append(f"- Project Type: {workspace_analysis.get('project_type', 'Unknown')}")
            prompt_parts.append(f"- Languages: {', '.join(workspace_analysis.get('languages', []))}")
            prompt_parts.append(f"- Existing Files: {workspace_analysis.get('file_count', 0)}")
            prompt_parts.append(f"- Has Tests: {workspace_analysis.get('has_tests', False)}")
            if workspace_analysis.get('frameworks'):
                prompt_parts.append(f"- Frameworks: {', '.join(workspace_analysis['frameworks'])}")

        prompt_parts.extend([
            "",
            "## Research Context",
            json.dumps(research_context, indent=2)[:1000],  # Truncate for token limits
            "",
            "## Task",
            "Design a comprehensive architecture with:",
            "1. Overall system description",
            "2. Core components and their responsibilities",
            "3. File structure (be specific with paths)",
            "4. Technology stack",
            "5. Design patterns to use",
            "6. Data flow between components",
            "",
            "Output ONLY valid JSON in the specified format."
        ])

        return "\n".join(prompt_parts)

    def _adjust_for_workspace(
        self,
        architecture: dict,
        workspace_analysis: dict
    ) -> dict:
        """
        Adjust architecture based on existing workspace.
        """
        if not workspace_analysis:
            return architecture

        # If workspace already has structure, preserve it
        if workspace_analysis.get("file_count", 0) > 10:
            architecture["description"] += "\n\nNote: Architecture adjusted to fit existing project structure"

        # Add detected frameworks
        existing_frameworks = workspace_analysis.get("frameworks", [])
        if existing_frameworks:
            architecture["technologies"].extend(existing_frameworks)
            architecture["technologies"] = list(set(architecture["technologies"]))

        # Adjust for test presence
        if workspace_analysis.get("has_tests"):
            # Ensure test directory is in file structure
            if not any("test" in str(f).lower() for f in architecture["file_structure"]):
                architecture["file_structure"].append("tests/")

        return architecture


# ============================================================================
# Export
# ============================================================================

__all__ = ["ArchitectAgent"]