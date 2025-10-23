"""
Codesmith Agent - Code Generation Specialist for v7.0

Uses AI Factory to generate code with Claude CLI or other providers.
NO MORE TEMPLATE FALLBACK - if AI is not available, we FAIL FAST!

Key Responsibilities:
- Generate code from architecture designs
- Implement business logic using Claude CLI
- Create tests
- Fix bugs
- Request research for implementation details

Author: KI AutoAgent Team
Version: 7.0.0
Date: 2025-10-23
"""

from __future__ import annotations

import logging
from typing import Any
from datetime import datetime

from backend.utils.ai_factory import AIFactory, AIRequest

# Setup logging
logger = logging.getLogger(__name__)


class CodesmithAgent:
    """
    Code generator that implements based on architecture.

    Uses AI Factory (Claude CLI by default) for code generation.
    NO TEMPLATE FALLBACK - production-quality code only!
    """

    def __init__(self):
        """Initialize the Codesmith agent with AI provider."""
        logger.info("⚒️ CodesmithAgent initializing...")

        try:
            # Get AI provider from factory
            self.ai_provider = AIFactory.get_provider_for_agent("codesmith")
            logger.info(f"   ✅ Using {self.ai_provider.provider_name} ({self.ai_provider.model})")
        except Exception as e:
            logger.error(f"   ❌ Failed to get AI provider: {e}")
            raise RuntimeError(
                "Codesmith requires an AI provider (Claude CLI recommended). "
                "Set CODESMITH_AI_PROVIDER and CODESMITH_AI_MODEL in .env"
            ) from e

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute code generation based on supervisor instructions.

        Args:
            state: Contains:
                - instructions: What to implement
                - architecture: System design from Architect
                - research_context: Context from Research
                - workspace_path: Target workspace

        Returns:
            Dictionary with generated files or research request
        """
        instructions = state.get("instructions", "")
        architecture = state.get("architecture", {})
        research_context = state.get("research_context", {})
        workspace_path = state.get("workspace_path", "")

        logger.info(f"🔨 Generating code: {instructions[:100]}...")

        # Check if we need more research for implementation
        if self._needs_implementation_research(instructions, architecture, research_context):
            logger.info("   📚 Requesting implementation research")
            return {
                "needs_research": True,
                "research_request": self._formulate_research_request(
                    instructions, architecture, research_context
                ),
                "code_complete": False
            }

        # Generate the code using AI
        try:
            generated_files = await self._generate_code_with_ai(
                instructions,
                architecture,
                research_context,
                workspace_path
            )

            logger.info(f"   ✅ Generated {len(generated_files)} files")

            return {
                "generated_files": generated_files,
                "code_complete": True,
                "needs_research": False,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"   ❌ Code generation failed: {e}")
            return {
                "generated_files": [],
                "code_complete": False,
                "needs_research": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _needs_implementation_research(
        self,
        instructions: str,
        architecture: dict,
        research_context: dict
    ) -> bool:
        """
        Determine if more research is needed for implementation.

        CRITICAL FIX: Only request research ONCE, when architecture is missing.
        Otherwise we get infinite loops (recursion limit 25).
        """
        # Need architecture first - but ONLY request this once
        if not architecture:
            # Check if we already have any research context
            if research_context and len(research_context) > 0:
                # We have research but no architecture - Architect should run next
                # Don't request more research - let Supervisor route to Architect
                return False
            return True  # First time - need initial research

        # If we have architecture, we're ready to generate code
        # No more research requests - prevents infinite loops
        return False

    def _formulate_research_request(
        self,
        instructions: str,
        architecture: dict,
        research_context: dict
    ) -> str:
        """
        Formulate research request for implementation details.
        """
        if not architecture:
            return "Need architecture design before code generation"

        # If we have architecture, no research needed
        return ""

    async def _generate_code_with_ai(
        self,
        instructions: str,
        architecture: dict,
        research_context: dict,
        workspace_path: str
    ) -> list[dict[str, Any]]:
        """
        Generate code using AI provider (Claude CLI).

        This is the ONLY code generation method - no template fallback!
        """
        logger.info("   🤖 Generating code with AI...")

        # Build the AI request
        request = AIRequest(
            prompt=self._build_code_generation_prompt(instructions, architecture),
            system_prompt=self._get_system_prompt(),
            workspace_path=workspace_path,
            context={
                "architecture": architecture,
                "research_context": research_context,
                "instructions": instructions
            },
            tools=["Read", "Edit", "Bash"],  # Claude CLI tools
            temperature=0.3,  # Lower temperature for code generation
            max_tokens=8000
        )

        # Call AI provider
        response = await self.ai_provider.complete(request)

        if not response.success:
            raise RuntimeError(f"AI code generation failed: {response.error}")

        # Parse generated files from response
        # For now, return a simple structure
        # TODO: Parse actual file operations from Claude CLI output
        generated_files = [
            {
                "path": "generated_code.py",
                "content": response.content,
                "language": "python",
                "lines": len(response.content.splitlines()),
                "description": "AI-generated code",
                "provider": response.provider,
                "model": response.model
            }
        ]

        return generated_files

    def _get_system_prompt(self) -> str:
        """Get system prompt for code generation."""
        return """You are an expert software engineer specializing in code generation.

Your task is to generate high-quality, production-ready code based on:
- Architecture design (component structure, technologies, file organization)
- Research context (best practices, patterns, documentation)
- Specific instructions from the supervisor

Requirements:
1. Follow the architecture design exactly
2. Use modern best practices for the technology stack
3. Include proper error handling and validation
4. Add comprehensive docstrings and comments
5. Generate tests alongside implementation
6. Use the Read, Edit, and Bash tools to create actual files in the workspace
7. Follow security best practices

DO NOT:
- Create placeholder or TODO code
- Skip error handling
- Ignore the architecture design
- Generate code without tests

Generate production-ready, fully functional code."""

    def _build_code_generation_prompt(
        self,
        instructions: str,
        architecture: dict
    ) -> str:
        """Build the detailed prompt for code generation."""
        prompt_parts = [
            "Generate code based on the following:",
            "",
            "## Instructions",
            instructions,
            "",
            "## Architecture",
        ]

        # Add architecture details
        if "description" in architecture:
            prompt_parts.append(f"Description: {architecture['description']}")

        if "components" in architecture:
            prompt_parts.append("\nComponents:")
            for comp in architecture["components"]:
                if isinstance(comp, dict):
                    prompt_parts.append(f"- {comp.get('name', 'Component')}: {comp.get('description', '')}")
                else:
                    prompt_parts.append(f"- {comp}")

        if "technologies" in architecture:
            prompt_parts.append(f"\nTechnologies: {', '.join(architecture['technologies'])}")

        if "file_structure" in architecture:
            prompt_parts.append("\nFile Structure:")
            for file in architecture["file_structure"]:
                prompt_parts.append(f"- {file}")

        prompt_parts.extend([
            "",
            "## Task",
            "1. Create the file structure using the Edit tool",
            "2. Implement each component with production-quality code",
            "3. Add comprehensive tests",
            "4. Ensure all error handling is in place",
            "5. Verify the code with basic syntax checks if possible",
            "",
            "Use the Read, Edit, and Bash tools to create actual files in the workspace."
        ])

        return "\n".join(prompt_parts)


# ============================================================================
# Export
# ============================================================================

__all__ = ["CodesmithAgent"]
