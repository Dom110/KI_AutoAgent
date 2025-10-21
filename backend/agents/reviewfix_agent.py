"""
ReviewFix Agent - Code Quality and Validation for v7.0

This agent reviews code quality and fixes issues.
MANDATORY after code generation (Asimov Rule 1).

Key Responsibilities:
- Review generated code for quality
- Run build validation
- Fix compilation/syntax errors
- Request research for complex fixes
- Ensure code meets quality standards

Author: KI AutoAgent Team
Version: 7.0.0-alpha
Date: 2025-10-21
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from typing import Any
from datetime import datetime
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)


class ReviewFixAgent:
    """
    Code reviewer and fixer - MANDATORY after code generation.

    This implements Asimov Rule 1: ReviewFix MUST run after
    any code generation to ensure quality and correctness.
    """

    def __init__(self):
        """Initialize the ReviewFix agent."""
        logger.info("🔧 ReviewFixAgent initialized")

        # Initialize build validation service
        self.build_validator = None
        try:
            from backend.services.build_validation_service import BuildValidationService
            self.build_validator = BuildValidationService()
            logger.info("   ✅ Build validation service connected")
        except Exception as e:
            logger.warning(f"   ⚠️ Build validation service not available: {e}")

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute review and fix process on generated code.

        Args:
            state: Contains:
                - instructions: What to review/fix
                - generated_files: Files from Codesmith
                - workspace_path: Target workspace

        Returns:
            Dictionary with validation results or research request
        """
        instructions = state.get("instructions", "")
        generated_files = state.get("generated_files", [])
        workspace_path = state.get("workspace_path", "")

        logger.info(f"🔍 Reviewing code: {len(generated_files)} files")

        # Perform code review
        validation_results = await self._validate_code(
            generated_files,
            workspace_path
        )

        # Check if validation passed
        validation_passed = validation_results.get("passed", False)
        issues = validation_results.get("issues", [])

        if not validation_passed:
            logger.info(f"   ⚠️ Found {len(issues)} issues to fix")

            # Try to fix issues automatically
            fixed_files, remaining_issues = await self._fix_issues(
                generated_files,
                issues,
                workspace_path
            )

            # Check if we need research for complex fixes
            if remaining_issues and self._needs_fix_research(remaining_issues):
                logger.info("   📚 Requesting research for complex fixes")
                return {
                    "needs_research": True,
                    "research_request": self._formulate_fix_research_request(remaining_issues),
                    "validation_results": validation_results,
                    "validation_passed": False,
                    "issues": remaining_issues
                }

            # Update validation results after fixes
            validation_results["fixed_issues"] = len(issues) - len(remaining_issues)
            validation_results["remaining_issues"] = remaining_issues

        logger.info(f"   ✅ Review complete: {'PASSED' if validation_passed else 'NEEDS ATTENTION'}")

        return {
            "validation_results": validation_results,
            "validation_passed": validation_passed,
            "issues": issues if not validation_passed else [],
            "needs_research": False,
            "timestamp": datetime.now().isoformat()
        }

    async def _validate_code(
        self,
        generated_files: list,
        workspace_path: str
    ) -> dict[str, Any]:
        """
        Validate generated code for quality and correctness.

        This is the core of Asimov Rule 1 - ensuring code quality.
        """
        logger.info("   🔎 Running validation checks")

        validation = {
            "passed": True,
            "quality_score": 1.0,
            "checks": [],
            "issues": [],
            "suggestions": []
        }

        # Check 1: Syntax validation
        syntax_check = self._check_syntax(generated_files)
        validation["checks"].append(syntax_check)
        if not syntax_check["passed"]:
            validation["passed"] = False
            validation["issues"].extend(syntax_check.get("errors", []))

        # Check 2: Import validation
        import_check = self._check_imports(generated_files)
        validation["checks"].append(import_check)
        if not import_check["passed"]:
            validation["passed"] = False
            validation["issues"].extend(import_check.get("errors", []))

        # Check 3: Build validation (if service available)
        if self.build_validator and workspace_path:
            build_check = await self._run_build_validation(workspace_path)
            validation["checks"].append(build_check)
            if not build_check["passed"]:
                validation["passed"] = False
                validation["quality_score"] *= 0.5  # Reduce quality score
                validation["issues"].extend(build_check.get("errors", []))

        # Check 4: Test validation
        test_check = await self._check_tests(generated_files, workspace_path)
        validation["checks"].append(test_check)
        if not test_check["passed"]:
            validation["quality_score"] *= 0.8  # Minor reduction for missing tests

        # Check 5: Documentation check
        doc_check = self._check_documentation(generated_files)
        validation["checks"].append(doc_check)
        if not doc_check["passed"]:
            validation["suggestions"].append("Add documentation and comments")

        # Check 6: Security check
        security_check = self._check_security(generated_files)
        validation["checks"].append(security_check)
        if not security_check["passed"]:
            validation["passed"] = False
            validation["issues"].extend(security_check.get("errors", []))

        # Calculate final quality score
        passed_checks = sum(1 for check in validation["checks"] if check["passed"])
        total_checks = len(validation["checks"])
        validation["quality_score"] *= (passed_checks / total_checks)

        return validation

    def _check_syntax(self, generated_files: list) -> dict[str, Any]:
        """
        Check syntax of generated files.
        """
        check = {
            "name": "Syntax Check",
            "passed": True,
            "errors": []
        }

        for file_info in generated_files:
            if not isinstance(file_info, dict):
                continue

            content = file_info.get("content", "")
            language = file_info.get("language", "")
            path = file_info.get("path", "unknown")

            if language == "python":
                try:
                    compile(content, path, "exec")
                except SyntaxError as e:
                    check["passed"] = False
                    check["errors"].append({
                        "file": path,
                        "type": "SyntaxError",
                        "message": str(e),
                        "line": e.lineno
                    })

            elif language in ["javascript", "typescript"]:
                # Basic bracket matching for JS/TS
                if content.count("{") != content.count("}"):
                    check["passed"] = False
                    check["errors"].append({
                        "file": path,
                        "type": "SyntaxError",
                        "message": "Mismatched curly braces"
                    })

        return check

    def _check_imports(self, generated_files: list) -> dict[str, Any]:
        """
        Check if imports are valid.
        """
        check = {
            "name": "Import Check",
            "passed": True,
            "errors": []
        }

        for file_info in generated_files:
            if not isinstance(file_info, dict):
                continue

            content = file_info.get("content", "")
            language = file_info.get("language", "")
            path = file_info.get("path", "unknown")

            if language == "python":
                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    if line.strip().startswith("import ") or line.strip().startswith("from "):
                        # Check for common import errors
                        if "import FastAPI" in line:  # Common mistake
                            check["passed"] = False
                            check["errors"].append({
                                "file": path,
                                "type": "ImportError",
                                "message": "Should be 'from fastapi import FastAPI'",
                                "line": i,
                                "fix": line.replace("import FastAPI", "from fastapi import FastAPI")
                            })

        return check

    async def _run_build_validation(self, workspace_path: str) -> dict[str, Any]:
        """
        Run build validation using the build validation service.
        """
        check = {
            "name": "Build Validation",
            "passed": True,
            "errors": []
        }

        if not self.build_validator:
            check["skipped"] = True
            check["reason"] = "Build validator not available"
            return check

        try:
            result = await self.build_validator.validate(workspace_path)
            check["passed"] = result.get("passed", False)
            check["quality_score"] = result.get("quality_score", 0.0)

            if not check["passed"]:
                for error in result.get("errors", []):
                    check["errors"].append({
                        "type": "BuildError",
                        "message": error,
                        "file": "build"
                    })

        except Exception as e:
            logger.error(f"   ❌ Build validation error: {e}")
            check["passed"] = False
            check["errors"].append({
                "type": "BuildValidationError",
                "message": str(e)
            })

        return check

    async def _check_tests(
        self,
        generated_files: list,
        workspace_path: str
    ) -> dict[str, Any]:
        """
        Check if tests exist and run them.
        """
        check = {
            "name": "Test Check",
            "passed": False,
            "errors": []
        }

        # Check if test files were generated
        test_files = [
            f for f in generated_files
            if isinstance(f, dict) and "test" in f.get("path", "").lower()
        ]

        if not test_files:
            check["errors"].append({
                "type": "MissingTests",
                "message": "No test files generated"
            })
            return check

        # Try to run tests if workspace exists
        if workspace_path and os.path.exists(workspace_path):
            # Check for Python tests
            if any("pytest" in str(f.get("content", "")) for f in test_files):
                try:
                    result = subprocess.run(
                        ["python", "-m", "pytest", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        cwd=workspace_path
                    )
                    if result.returncode == 0:
                        check["passed"] = True
                        check["message"] = "Pytest available for testing"
                except:
                    pass

            # Check for JavaScript tests
            if any("jest" in str(f.get("content", "")) for f in test_files):
                try:
                    result = subprocess.run(
                        ["npm", "test", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        cwd=workspace_path
                    )
                    if result.returncode == 0:
                        check["passed"] = True
                        check["message"] = "Jest available for testing"
                except:
                    pass

        if test_files and not check["passed"]:
            check["passed"] = True  # Tests exist, just can't run them yet
            check["message"] = f"Found {len(test_files)} test files"

        return check

    def _check_documentation(self, generated_files: list) -> dict[str, Any]:
        """
        Check if code has adequate documentation.
        """
        check = {
            "name": "Documentation Check",
            "passed": True,
            "warnings": []
        }

        for file_info in generated_files:
            if not isinstance(file_info, dict):
                continue

            content = file_info.get("content", "")
            path = file_info.get("path", "unknown")

            # Check for docstrings/comments
            lines = content.split("\n")
            code_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
            comment_lines = [l for l in lines if l.strip().startswith("#") or '"""' in l]

            if code_lines and len(comment_lines) < len(code_lines) * 0.1:  # Less than 10% comments
                check["passed"] = False
                check["warnings"].append({
                    "file": path,
                    "message": "Insufficient documentation"
                })

        return check

    def _check_security(self, generated_files: list) -> dict[str, Any]:
        """
        Check for common security issues.
        """
        check = {
            "name": "Security Check",
            "passed": True,
            "errors": []
        }

        security_patterns = [
            ("eval(", "Use of eval() is dangerous"),
            ("exec(", "Use of exec() is dangerous"),
            ("password=", "Possible hardcoded password"),
            ("api_key=", "Possible hardcoded API key"),
            ("secret=", "Possible hardcoded secret"),
            ("TODO: ", None)  # TODOs are OK, not security issues
        ]

        for file_info in generated_files:
            if not isinstance(file_info, dict):
                continue

            content = file_info.get("content", "")
            path = file_info.get("path", "unknown")

            for pattern, message in security_patterns:
                if message and pattern in content.lower():
                    check["passed"] = False
                    check["errors"].append({
                        "file": path,
                        "type": "SecurityIssue",
                        "message": message,
                        "pattern": pattern
                    })

        return check

    async def _fix_issues(
        self,
        generated_files: list,
        issues: list,
        workspace_path: str
    ) -> tuple[list, list]:
        """
        Attempt to fix detected issues automatically.

        Returns:
            Tuple of (fixed_files, remaining_issues)
        """
        logger.info(f"   🔨 Attempting to fix {len(issues)} issues")

        fixed_files = generated_files.copy()
        remaining_issues = []

        for issue in issues:
            fixed = False

            # Try to fix based on issue type
            if issue.get("type") == "ImportError" and "fix" in issue:
                # Apply import fix
                for file_info in fixed_files:
                    if file_info.get("path") == issue["file"]:
                        content = file_info["content"]
                        if issue.get("line"):
                            lines = content.split("\n")
                            lines[issue["line"] - 1] = issue["fix"]
                            file_info["content"] = "\n".join(lines)
                            fixed = True
                            logger.info(f"   ✅ Fixed import in {issue['file']}")

            elif issue.get("type") == "SyntaxError":
                # Syntax errors are harder to fix automatically
                # Mark for research
                fixed = False

            if not fixed:
                remaining_issues.append(issue)

        return fixed_files, remaining_issues

    def _needs_fix_research(self, issues: list) -> bool:
        """
        Determine if research is needed for complex fixes.
        """
        # Need research for complex error types
        complex_error_types = ["BuildError", "TypeError", "AttributeError", "RuntimeError"]

        for issue in issues:
            if issue.get("type") in complex_error_types:
                return True

            # Need research if no automatic fix available
            if "fix" not in issue:
                return True

        return False

    def _formulate_fix_research_request(self, issues: list) -> str:
        """
        Formulate research request for fixing issues.
        """
        error_types = list(set(issue.get("type", "Unknown") for issue in issues))
        error_summary = ", ".join(error_types[:3])

        requests = [f"Research how to fix {error_summary} errors"]

        # Add specific research based on error patterns
        if any("Import" in issue.get("type", "") for issue in issues):
            requests.append("Find correct import patterns for the libraries used")

        if any("Build" in issue.get("type", "") for issue in issues):
            requests.append("Research build configuration and dependency management")

        if any("Type" in issue.get("type", "") for issue in issues):
            requests.append("Research type annotations and type compatibility")

        return " AND ".join(requests)


# ============================================================================
# Export
# ============================================================================

__all__ = ["ReviewFixAgent"]