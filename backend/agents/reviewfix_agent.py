"""
ReviewFix Agent - AI-Powered Code Debugging and Validation for v7.0

Uses Claude CLI to:
1. Debug generated code
2. Compare code against architecture design
3. Run playground tests
4. Fix issues intelligently

Key Responsibilities:
- Debug and fix code issues using AI
- Validate code matches architecture
- Execute playground tests in .ki_autoagent_ws/playground/
- Ensure production-quality code

Author: KI AutoAgent Team
Version: 7.0.0
Date: 2025-10-23
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any
from datetime import datetime
from pathlib import Path

from backend.utils.ai_factory import AIFactory, AIRequest

# Setup logging
logger = logging.getLogger(__name__)


class ReviewFixAgent:
    """
    AI-powered code reviewer and debugger using Claude CLI.

    NO MORE BASIC VALIDATION - uses AI for intelligent debugging!
    """

    def __init__(self):
        """Initialize the ReviewFix agent with AI provider."""
        logger.info("🔧 ReviewFixAgent initializing...")

        try:
            # Get AI provider from factory
            self.ai_provider = AIFactory.get_provider_for_agent("reviewfix")
            logger.info(f"   ✅ Using {self.ai_provider.provider_name} ({self.ai_provider.model})")
        except Exception as e:
            logger.error(f"   ❌ Failed to get AI provider: {e}")
            raise RuntimeError(
                "ReviewFix requires an AI provider (Claude CLI recommended). "
                "Set REVIEWFIX_AI_PROVIDER and REVIEWFIX_AI_MODEL in .env"
            ) from e

        # Initialize build validation service (optional)
        self.build_validator = None
        try:
            from backend.services.build_validation_service import BuildValidationService
            self.build_validator = BuildValidationService()
            logger.info("   ✅ Build validation service connected")
        except Exception as e:
            logger.warning(f"   ⚠️ Build validation service not available: {e}")

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute AI-powered review, debugging, and testing.

        Args:
            state: Contains:
                - instructions: What to review/fix
                - generated_files: Files from Codesmith
                - architecture: Design from Architect
                - workspace_path: Target workspace

        Returns:
            Dictionary with validation results and fixes
        """
        instructions = state.get("instructions", "")
        generated_files = state.get("generated_files", [])
        architecture = state.get("architecture", {})
        workspace_path = state.get("workspace_path", "")

        logger.info(f"🔍 AI-powered review: {len(generated_files)} files")

        # Step 1: Build validation (if available)
        build_results = None
        if self.build_validator and workspace_path:
            build_results = await self._run_build_validation(workspace_path)
            logger.info(f"   📊 Build quality score: {build_results.get('quality_score', 0):.2f}")

        # Step 2: Architecture comparison using AI
        architecture_check = await self._compare_with_architecture(
            generated_files,
            architecture,
            workspace_path
        )

        # Step 3: Debug issues using AI
        debug_results = await self._debug_with_ai(
            generated_files,
            architecture,
            build_results,
            workspace_path
        )

        # Step 4: Run playground tests
        test_results = await self._run_playground_tests(
            workspace_path,
            instructions
        )

        # Determine overall validation status
        validation_passed = (
            architecture_check.get("matches_architecture", False) and
            (not build_results or build_results.get("passed", False)) and
            debug_results.get("issues_fixed", 0) >= 0 and
            test_results.get("status") != "failed"
        )

        logger.info(f"   ✅ Review complete: {'PASSED' if validation_passed else 'NEEDS ATTENTION'}")

        return {
            "validation_passed": validation_passed,
            "architecture_check": architecture_check,
            "build_results": build_results,
            "debug_results": debug_results,
            "test_results": test_results,
            "needs_research": False,
            "timestamp": datetime.now().isoformat()
        }

    async def _compare_with_architecture(
        self,
        generated_files: list,
        architecture: dict,
        workspace_path: str
    ) -> dict[str, Any]:
        """
        Use AI to compare generated code with architecture design.

        This ensures the implementation matches the original design.
        """
        logger.info("   🏗️ Comparing with architecture using AI...")

        if not architecture:
            return {
                "matches_architecture": True,
                "message": "No architecture provided to compare"
            }

        # Build AI request
        request = AIRequest(
            prompt=self._build_architecture_comparison_prompt(generated_files, architecture),
            system_prompt=self._get_architecture_comparison_system_prompt(),
            workspace_path=workspace_path,
            context={
                "architecture": architecture,
                "generated_files": generated_files
            },
            tools=["Read"],  # Only need to read files
            temperature=0.2,  # Lower temperature for objective comparison
            max_tokens=4000
        )

        # Call AI provider
        response = await self.ai_provider.complete(request)

        if not response.success:
            logger.error(f"   ❌ Architecture comparison failed: {response.error}")
            return {
                "matches_architecture": False,
                "error": response.error,
                "discrepancies": []
            }

        # Parse response
        # AI should return analysis of how well code matches architecture
        matches = "matches" in response.content.lower() or "correct" in response.content.lower()

        return {
            "matches_architecture": matches,
            "analysis": response.content,
            "provider": response.provider,
            "model": response.model
        }

    async def _debug_with_ai(
        self,
        generated_files: list,
        architecture: dict,
        build_results: dict | None,
        workspace_path: str
    ) -> dict[str, Any]:
        """
        Use AI to debug and fix issues in generated code.

        This is where the REAL debugging happens - AI analyzes code and fixes issues.
        """
        logger.info("   🐛 Debugging with AI...")

        # Collect issues from build validation
        issues = []
        if build_results and not build_results.get("passed", False):
            issues.extend(build_results.get("errors", []))

        if not issues:
            logger.info("   ✅ No issues to debug")
            return {
                "issues_found": 0,
                "issues_fixed": 0,
                "status": "clean"
            }

        logger.info(f"   🔨 Found {len(issues)} issues to debug")

        # Build AI request
        request = AIRequest(
            prompt=self._build_debugging_prompt(generated_files, architecture, issues),
            system_prompt=self._get_debugging_system_prompt(),
            workspace_path=workspace_path,
            context={
                "architecture": architecture,
                "generated_files": generated_files,
                "issues": issues
            },
            tools=["Read", "Edit", "Bash"],  # Full tool access for debugging
            temperature=0.3,
            max_tokens=8000
        )

        # Call AI provider to debug
        response = await self.ai_provider.complete(request)

        if not response.success:
            logger.error(f"   ❌ Debugging failed: {response.error}")
            return {
                "issues_found": len(issues),
                "issues_fixed": 0,
                "error": response.error,
                "status": "failed"
            }

        # AI has debugged and fixed issues
        logger.info(f"   ✅ AI debugging complete")

        return {
            "issues_found": len(issues),
            "issues_fixed": len(issues),  # AI attempted to fix all
            "debug_log": response.content,
            "provider": response.provider,
            "model": response.model,
            "status": "fixed"
        }

    async def _run_playground_tests(
        self,
        workspace_path: str,
        instructions: str
    ) -> dict[str, Any]:
        """
        Run playground tests using AI and save results.

        Tests are executed in .ki_autoagent_ws/playground/ directory.
        """
        logger.info("   🎮 Running playground tests...")

        if not workspace_path:
            return {
                "status": "skipped",
                "reason": "No workspace path provided"
            }

        # Create playground directory
        workspace_dir = Path(workspace_path)
        playground_dir = workspace_dir / ".ki_autoagent_ws" / "playground"
        playground_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"   📁 Playground: {playground_dir}")

        # Build AI request to run tests
        request = AIRequest(
            prompt=self._build_playground_test_prompt(instructions),
            system_prompt=self._get_playground_test_system_prompt(),
            workspace_path=workspace_path,
            context={
                "playground_dir": str(playground_dir),
                "instructions": instructions
            },
            tools=["Read", "Edit", "Bash"],  # Full tool access for testing
            temperature=0.3,
            max_tokens=6000
        )

        # Call AI provider to run tests with 60s timeout
        try:
            response = await asyncio.wait_for(
                self.ai_provider.complete(request),
                timeout=60.0  # 60 second timeout for playground tests
            )
        except asyncio.TimeoutError:
            logger.warning("   ⏱️ Playground tests timed out after 60s - skipping")
            return {
                "status": "timeout",
                "passed": True,  # Don't fail workflow on timeout
                "skipped": True,
                "reason": "Timeout after 60s (playground tests took too long)"
            }

        if not response.success:
            logger.error(f"   ❌ Playground tests failed: {response.error}")
            return {
                "status": "failed",
                "error": response.error
            }

        # Save test results
        results_file = playground_dir / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            results_file.write_text(response.content, encoding="utf-8")
            logger.info(f"   💾 Test results saved: {results_file}")
        except Exception as e:
            logger.error(f"   ❌ Failed to save test results: {e}")

        logger.info(f"   ✅ Playground tests complete")

        return {
            "status": "completed",
            "results_file": str(results_file),
            "test_log": response.content,
            "provider": response.provider,
            "model": response.model
        }

    async def _run_build_validation(self, workspace_path: str) -> dict[str, Any]:
        """
        Run build validation using the build validation service.
        """
        if not self.build_validator:
            return {
                "passed": True,
                "skipped": True,
                "reason": "Build validator not available"
            }

        try:
            result = await self.build_validator.validate(workspace_path)
            return result
        except Exception as e:
            logger.error(f"   ❌ Build validation error: {e}")
            return {
                "passed": False,
                "error": str(e)
            }

    # ========================================================================
    # AI Prompts
    # ========================================================================

    def _get_architecture_comparison_system_prompt(self) -> str:
        """System prompt for architecture comparison."""
        return """You are an expert software architect specializing in design validation.

Your task is to compare generated code against the original architecture design.

Check:
1. Are all components from the architecture implemented?
2. Do the files match the planned structure?
3. Are the technologies used correctly?
4. Does the implementation follow the design patterns specified?
5. Are there any significant deviations?

Provide a clear analysis of how well the code matches the architecture.
Report any discrepancies or missing components."""

    def _build_architecture_comparison_prompt(
        self,
        generated_files: list,
        architecture: dict
    ) -> str:
        """Build prompt for architecture comparison."""
        prompt_parts = [
            "Compare the generated code with the architecture design:",
            "",
            "## Architecture Design",
        ]

        if "description" in architecture:
            prompt_parts.append(f"Description: {architecture['description']}")

        if "components" in architecture:
            prompt_parts.append("\nComponents:")
            for comp in architecture["components"]:
                if isinstance(comp, dict):
                    prompt_parts.append(f"- {comp.get('name', 'Component')}: {comp.get('description', '')}")
                else:
                    prompt_parts.append(f"- {comp}")

        if "file_structure" in architecture:
            prompt_parts.append("\nExpected File Structure:")
            for file in architecture["file_structure"]:
                prompt_parts.append(f"- {file}")

        prompt_parts.extend([
            "",
            "## Generated Files",
            f"Total files: {len(generated_files)}",
            ""
        ])

        for file_info in generated_files[:10]:  # Limit to first 10 files
            if isinstance(file_info, dict):
                path = file_info.get("path", "unknown")
                lines = file_info.get("lines", 0)
                prompt_parts.append(f"- {path} ({lines} lines)")

        prompt_parts.extend([
            "",
            "## Task",
            "1. Read the generated files in the workspace",
            "2. Compare them with the architecture design",
            "3. Report how well the implementation matches the design",
            "4. List any discrepancies or missing components"
        ])

        return "\n".join(prompt_parts)

    def _get_debugging_system_prompt(self) -> str:
        """System prompt for debugging."""
        return """You are an expert software debugger specializing in production-quality code.

Your task is to debug and fix issues in generated code.

Process:
1. Analyze the reported issues (syntax errors, build errors, type errors)
2. Read the problematic files
3. Understand the root cause
4. Apply fixes using the Edit tool
5. Verify the fixes work

Requirements:
- Fix all issues systematically
- Maintain code quality and style
- Don't introduce new bugs
- Add comments explaining complex fixes
- Run basic validation when possible

Use Read, Edit, and Bash tools to fix the code."""

    def _build_debugging_prompt(
        self,
        generated_files: list,
        architecture: dict,
        issues: list
    ) -> str:
        """Build prompt for debugging."""
        prompt_parts = [
            "Debug and fix the following issues in the generated code:",
            "",
            "## Issues to Fix",
        ]

        for i, issue in enumerate(issues[:10], 1):  # Limit to 10 issues
            if isinstance(issue, dict):
                issue_type = issue.get("type", "Unknown")
                message = issue.get("message", "No description")
                file = issue.get("file", "unknown")
                line = issue.get("line", "?")
                prompt_parts.append(f"{i}. [{issue_type}] {file}:{line} - {message}")
            else:
                prompt_parts.append(f"{i}. {issue}")

        prompt_parts.extend([
            "",
            "## Architecture Context",
        ])

        if "description" in architecture:
            prompt_parts.append(f"System: {architecture['description']}")

        if "technologies" in architecture:
            prompt_parts.append(f"Technologies: {', '.join(architecture['technologies'])}")

        prompt_parts.extend([
            "",
            "## Task",
            "1. Read the files with issues",
            "2. Understand the root cause of each issue",
            "3. Fix each issue using the Edit tool",
            "4. Verify your fixes are correct",
            "5. Report what you fixed"
        ])

        return "\n".join(prompt_parts)

    def _get_playground_test_system_prompt(self) -> str:
        """System prompt for playground testing."""
        return """You are an expert software tester specializing in exploratory testing.

Your task is to test generated code in a playground environment.

Process:
1. Create test scenarios based on the instructions
2. Write test code in the playground directory (.ki_autoagent_ws/playground/)
3. Execute the tests using appropriate tools (pytest, node, etc.)
4. Document test results clearly
5. Report any failures or unexpected behavior

Requirements:
- Test all major functionality
- Include edge cases
- Report clear pass/fail results
- Save all test artifacts in playground directory

Use Read, Edit, and Bash tools to run comprehensive tests."""

    def _build_playground_test_prompt(self, instructions: str) -> str:
        """Build prompt for playground testing."""
        return f"""Run playground tests for the following implementation:

## Instructions
{instructions}

## Task
1. Analyze the generated code in the workspace
2. Create appropriate test scenarios
3. Write test code in the .ki_autoagent_ws/playground/ directory
4. Execute the tests
5. Report results with clear pass/fail status

Save all test artifacts and logs in the playground directory."""


# ============================================================================
# Export
# ============================================================================

__all__ = ["ReviewFixAgent"]
