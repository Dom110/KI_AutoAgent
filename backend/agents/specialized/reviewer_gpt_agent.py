from __future__ import annotations

"""
ReviewerGPT Agent - Code Review and Security Analysis Expert
Performs thorough code reviews and security audits
"""

import logging
import os
from collections.abc import Callable
from typing import Any, override

from utils.openai_service import OpenAIService

from ..base.base_agent import (AgentCapability, AgentConfig, TaskRequest,
                               TaskResult)
from ..base.chat_agent import ChatAgent
from ..base.prime_directives import PrimeDirectives

logger = logging.getLogger(__name__)

# Import BrowserTester for HTML/JS app testing
try:
    from ..tools.browser_tester import PLAYWRIGHT_AVAILABLE, BrowserTester
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("BrowserTester not available - HTML app testing disabled")


class ReviewerGPTAgent(ChatAgent):
    """
    Code Review and Security Expert
    - Code quality analysis
    - Security vulnerability detection
    - Performance optimization suggestions
    - Best practices enforcement
    - Bug detection
    """

    def __init__(self):
        config = AgentConfig(
            agent_id="reviewer",
            name="ReviewerGPT",
            full_name="Code Review & Security Expert",
            description="Specialized in code review, security analysis, and bug detection",
            model="gpt-4o-mini-2024-07-18",  # GPT-4 mini for validation
            capabilities=[
                AgentCapability.CODE_REVIEW,
                AgentCapability.SECURITY_ANALYSIS,
            ],
            temperature=0.3,  # Lower temperature for consistent reviews
            max_tokens=3000,
            icon="🔍",
            instructions_path=".ki_autoagent/instructions/reviewergpt-instructions.md",
        )
        super().__init__(config)
        self.ai_service = OpenAIService(model=self.config.model)
        self.browser_tester = None  # Will be initialized on-demand

    async def _get_architect_analysis(self) -> dict[str, Any] | None:
        """
        Get Architect's system analysis from shared_context (v5.8.2)
        Returns system_knowledge with metrics, dead_code, security, etc.
        """
        if not self.shared_context:
            logger.warning("⚠️ Reviewer: shared_context not available")
            return None

        try:
            analysis = self.shared_context.get("architect:system_knowledge")
            if analysis:
                logger.info("✅ Reviewer: Got Architect analysis from shared_context")
                return analysis
            else:
                logger.info("ℹ️ Reviewer: No Architect analysis available yet")
                return None
        except Exception as e:
            logger.error(f"❌ Reviewer: Failed to get Architect analysis: {e}")
            return None

    @override
    async def execute(self, request: TaskRequest) -> TaskResult:
        """
        Execute code review task - ENFORCER OF ASIMOV RULES

        Strategy:
        1. Check if this is HTML/JS app to test with Playwright
        2. Otherwise use AI-powered code review
        """
        try:
            # PRIORITY: Check if this is HTML/JS app that needs browser testing
            task_lower = request.prompt.lower()
            context = request.context or {}

            is_html_task = any(
                keyword in task_lower
                for keyword in [
                    "html",
                    "tetris",
                    "webapp",
                    "web app",
                    "browser",
                    "canvas",
                    "game",
                ]
            )

            contains_test_keyword = any(
                keyword in task_lower
                for keyword in ["test", "review", "playwright", "browser"]
            )

            # Check if previous step (CodeSmith) created HTML files
            previous_result = context.get("previous_step_result")
            html_file = None

            # v5.5.3: Handle both string and dict previous_result
            if previous_result:
                # Try to extract from metadata if available in context
                if "metadata" in context and isinstance(context["metadata"], dict):
                    metadata = context["metadata"]
                    # Check both 'files_created' (plural) and 'file_created' (singular)
                    files_created = metadata.get("files_created", [])
                    if not files_created and "file_created" in metadata:
                        # Convert singular to list
                        files_created = [metadata["file_created"]]

                    for file_path in files_created:
                        if file_path.endswith(".html"):
                            html_file = file_path
                            logger.info(f"📄 Found HTML file in metadata: {html_file}")
                            break

                # Fallback: Parse from string result if it's a string
                if not html_file and isinstance(previous_result, str):
                    # Look for .html file paths in the result text
                    import re

                    html_matches = re.findall(r"([^\s]+\.html)", previous_result)
                    if html_matches:
                        # Use the first .html file found
                        html_file = html_matches[0]
                        logger.info(f"📄 Found HTML file in result text: {html_file}")

            # Use Playwright testing if this is HTML app
            if (is_html_task or contains_test_keyword) and html_file:
                logger.info(
                    f"🌐 Reviewer detected HTML app - using Playwright testing: {html_file}"
                )

                # Determine app type
                app_type = "tetris" if "tetris" in task_lower else "generic"

                # Run Playwright test
                test_result = await self.test_html_application(
                    html_file, app_type=app_type
                )

                # v5.8.6 Fix 4: Save Playwright report to disk for debugging
                try:
                    import json
                    from datetime import datetime

                    workspace_path = context.get("workspace_path", ".")
                    report_dir = os.path.join(workspace_path, "playwright-reports")
                    os.makedirs(report_dir, exist_ok=True)

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    report_file = os.path.join(
                        report_dir, f"test-report-{timestamp}.json"
                    )

                    with open(report_file, "w") as f:
                        json.dump(test_result, f, indent=2, default=str)

                    logger.info(f"💾 Saved Playwright report to: {report_file}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to save Playwright report: {e}")

                if test_result["success"]:
                    logger.info(
                        f"✅ Playwright test PASSED - Quality: {test_result['quality_score']:.2f}"
                    )
                    return TaskResult(
                        status="success",
                        content=f"""✅ PLAYWRIGHT BROWSER TEST PASSED

**Quality Score:** {test_result['quality_score']:.2f}/1.0
**Recommendation:** {test_result['recommendation']}

**Metrics:**
{self._format_metrics(test_result['metrics'])}

**Screenshots:**
{chr(10).join(f'- {s}' for s in test_result['screenshots'])}

All browser tests passed successfully!""",
                        agent=self.config.agent_id,
                        metadata=test_result,
                    )
                else:
                    logger.warning(
                        f"❌ Playwright test FAILED - Errors found: {len(test_result['errors'])}"
                    )

                    # v5.8.6 Fix 2: Create structured errors for Fixer
                    structured_errors = []
                    for error in test_result["errors"]:
                        structured_errors.append(
                            {
                                "description": error,
                                "severity": "high",
                                "source": "playwright",
                                "type": "browser_test",
                                "file": html_file,
                            }
                        )

                    # Add warnings as lower severity issues
                    for warning in test_result.get("warnings", []):
                        structured_errors.append(
                            {
                                "description": warning,
                                "severity": "medium",
                                "source": "playwright",
                                "type": "browser_warning",
                                "file": html_file,
                            }
                        )

                    logger.info(
                        f"📋 Created {len(structured_errors)} structured errors for Fixer"
                    )

                    return TaskResult(
                        status="needs_fixes",
                        content=f"""❌ PLAYWRIGHT BROWSER TEST FAILED

**Quality Score:** {test_result['quality_score']:.2f}/1.0
**Recommendation:** {test_result['recommendation']}

**Errors Found:**
{chr(10).join(f'- {e}' for e in test_result['errors'])}

**Warnings:**
{chr(10).join(f'- {w}' for w in test_result['warnings'])}

**Screenshots:**
{chr(10).join(f'- {s}' for s in test_result['screenshots'])}

Please fix these issues and re-test.""",
                        agent=self.config.agent_id,
                        metadata={
                            **test_result,
                            "structured_errors": structured_errors,  # v5.8.6 Fix 2
                        },
                    )

            # Fallback to AI-powered code review for non-HTML tasks
            logger.info("📝 Using AI-powered code review")

            # v5.8.2: Get Architect's analysis for enhanced review
            architect_analysis = await self._get_architect_analysis()

            # Build context from Architect's analysis
            analysis_context = ""
            if architect_analysis:
                # Add Quality Score context
                metrics = architect_analysis.get("metrics", {})
                metrics_summary = metrics.get("summary", {})
                quality_score = metrics_summary.get("quality_score", 0)
                avg_complexity = metrics_summary.get("average_complexity", 0)

                analysis_context += f"""
📊 ARCHITECT ANALYSIS AVAILABLE:
- Quality Score: {quality_score:.1f}/100
- Average Complexity: {avg_complexity:.1f}
"""

                # Add Dead Code context (prioritize review on these)
                dead_code = architect_analysis.get("dead_code", {})
                dead_code_summary = dead_code.get("summary", {})
                total_dead = dead_code_summary.get("total_dead_code", 0)
                if total_dead > 0:
                    analysis_context += f"""
🧹 DEAD CODE DETECTED: {total_dead} unused items found
Priority: Review if these should be removed or are false positives
"""
                    # Show top 5 dead code items
                    dead_items = dead_code.get("items", [])[:5]
                    if dead_items:
                        analysis_context += "Top dead code items:\n"
                        for item in dead_items:
                            analysis_context += f"  - {item.get('name')} ({item.get('type')}) at {item.get('file')}:{item.get('line')}\n"

                # Add Security context
                security = architect_analysis.get("security", {})
                security_summary = security.get("summary", {})
                critical_count = security_summary.get("critical", 0)
                high_count = security_summary.get("high", 0)
                if critical_count > 0 or high_count > 0:
                    analysis_context += f"""
🔒 SECURITY ISSUES FOUND:
- Critical: {critical_count}
- High: {high_count}
Priority: Review these security findings first!
"""

                # Add high complexity functions
                if quality_score < 70:
                    analysis_context += f"""
⚠️ LOW QUALITY SCORE ({quality_score:.1f}/100)
Focus review on improving maintainability and reducing complexity.
"""

            system_prompt = f"""
            You are ReviewerGPT, the ENFORCER OF ASIMOV RULES and code quality.

            🔴 ASIMOV RULES (ABSOLUTE - BLOCK ANY VIOLATIONS):
            1. NO FALLBACKS without documented user reason - Check for any fallback patterns
            2. COMPLETE IMPLEMENTATION - No TODOs, no partial work, no 'later'
            3. GLOBAL ERROR SEARCH - When finding an error, search ENTIRE project for same pattern

            Analyze code for:
            1. ⚡ ASIMOV RULE VIOLATIONS (HIGHEST PRIORITY)
            2. 🐛 Bugs and logical errors
            3. 🔒 Security vulnerabilities (XSS, SQL injection, etc.)
            4. ⚡ Performance issues
            5. 📝 Code quality and readability
            6. 🎯 Best practices violations

            ENFORCEMENT ACTIONS:
            - 🔴 BLOCK: Any code with Asimov violations
            - 🔴 REJECT: Fallbacks without documented reason
            - 🔴 FAIL: Incomplete implementations or TODOs

            {analysis_context}

            Provide actionable feedback with specific line references.
            Rate severity: ASIMOV VIOLATION 🔴🔴🔴, Critical 🔴, High 🟠, Medium 🟡, Low 🔵
            """

            response = await self.ai_service.get_completion(
                system_prompt=system_prompt,
                user_prompt=f"Review this: {request.prompt}",
                temperature=0.3,
            )

            # NO FALLBACK - ASIMOV RULE 1
            # If API fails, we fail fast
            if "error" in response.lower() and "api" in response.lower():
                raise Exception("API error - no fallback allowed per Asimov Rule 1")

            return TaskResult(
                status="success",
                content=response,
                agent=self.config.agent_id,
                metadata={
                    "model": self.config.model,
                    "review_type": "comprehensive",
                    "timestamp": datetime.now().isoformat(),
                },
            )

        except Exception as e:
            # NO FALLBACK - FAIL FAST (ASIMOV RULE 1)
            logger.error(f"ReviewerGPT execution error: {e}")
            return TaskResult(
                status="error",
                content=f"REVIEW FAILED: {str(e)}\n\nNo fallback review allowed per Asimov Rule 1.\nFix the error and retry.",
                agent=self.config.agent_id,
                metadata={"asimov_enforcement": "No fallbacks allowed"},
            )

    def check_asimov_violations(self, code: str) -> list[dict[str, Any]]:
        """
        Check for Asimov Rule violations in code
        This is the PRIMARY enforcement mechanism
        """
        violations = []

        # Check for fallback patterns (Asimov Rule 1)
        fallback_patterns = [
            (r"if.*not.*available.*:", "Potential fallback without documented reason"),
            (r"except.*pass", "Silent error handling - violates fail-fast principle"),
            (r"fallback|default.*=|or\s+\w+\(\)", "Fallback pattern detected"),
            (r"try:.*except:.*return.*None", "Silent fallback to None"),
        ]

        # Check for incomplete implementation (Asimov Rule 2)
        incomplete_patterns = [
            (r"#\s*TODO", "TODO found - incomplete implementation"),
            (r"#\s*FIXME", "FIXME found - incomplete implementation"),
            (r"#\s*HACK", "HACK found - improper implementation"),
            (r"pass\s*$", "Empty implementation with pass"),
            (r"raise\s+NotImplementedError", "Not implemented"),
            (r"return\s+None\s*#.*later", "Deferred implementation"),
        ]

        import re

        code_lower = code.lower()

        for pattern, description in fallback_patterns:
            if re.search(pattern, code_lower):
                violations.append(
                    {
                        "rule": "ASIMOV RULE 1",
                        "severity": "ASIMOV_VIOLATION",
                        "description": description,
                        "action": "BLOCK",
                        "fix": "Remove fallback or add documented reason with user confirmation",
                    }
                )

        for pattern, description in incomplete_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                violations.append(
                    {
                        "rule": "ASIMOV RULE 2",
                        "severity": "ASIMOV_VIOLATION",
                        "description": description,
                        "action": "BLOCK",
                        "fix": "Complete the implementation before submission",
                    }
                )

        return violations

    async def find_bugs(self, code: str, file_path: str = None) -> list[dict[str, Any]]:
        """
        Actively hunt for bugs in code
        """
        # This would use AI to find bugs
        bugs = []

        # First check for Asimov violations
        asimov_violations = self.check_asimov_violations(code)
        if asimov_violations:
            for violation in asimov_violations:
                bugs.append(
                    {
                        "type": "ASIMOV_VIOLATION",
                        "severity": "BLOCKER",
                        "rule": violation["rule"],
                        "description": violation["description"],
                        "action": violation["action"],
                        "fix": violation["fix"],
                    }
                )

                # ASIMOV RULE 3: If error found, search globally
                if (
                    "RULE 3" not in violation["rule"]
                ):  # Don't search for Rule 3 violations
                    global_search = await self.enforce_global_error_search(
                        violation["description"], file_path or "unknown"
                    )
                    if global_search.get("additional_occurrences", 0) > 0:
                        bugs.append(
                            {
                                "type": "ASIMOV_RULE_3_ENFORCEMENT",
                                "severity": "CRITICAL",
                                "rule": "ASIMOV RULE 3",
                                "description": f"Found {global_search['additional_occurrences']} MORE files with same error",
                                "files": global_search["files_found"],
                                "action": "MUST FIX ALL INSTANCES",
                                "fix": "Fix all occurrences across the entire project",
                            }
                        )

        # Then check for regular bugs
        if "onclick=" in code.lower():
            bugs.append(
                {
                    "type": "event_handler",
                    "severity": "medium",
                    "description": "onclick handlers might not work in VS Code webviews",
                    "suggestion": "Use addEventListener instead",
                }
            )

        return bugs

    async def enforce_global_error_search(
        self, error_pattern: str, initial_file: str
    ) -> dict[str, Any]:
        """
        ASIMOV RULE 3: Search entire project for error pattern
        """
        # Use PrimeDirectives global search
        search_result = await PrimeDirectives.perform_global_error_search(
            error_pattern, file_type="py"  # Can be extended to other types
        )

        # Add enforcement metadata
        search_result["asimov_rule"] = "RULE 3 - Global Error Search"
        search_result["initial_file"] = initial_file

        if search_result.get("files_found"):
            # Remove the initial file from the list
            search_result["files_found"] = [
                f for f in search_result["files_found"] if f != initial_file
            ]
            search_result["additional_occurrences"] = len(search_result["files_found"])

        return search_result

    async def execute_global_fix(
        self, error_pattern: str, fix_function: Callable
    ) -> dict[str, Any]:
        """
        ASIMOV RULE 3: Apply fix to all instances of an error
        """
        search_result = await self.enforce_global_error_search(
            error_pattern, "batch_fix"
        )

        fixed_files = []
        failed_files = []

        for file_path in search_result.get("files_found", []):
            try:
                # Apply fix to each file
                await fix_function(file_path)
                fixed_files.append(file_path)
            except Exception as e:
                failed_files.append({"file": file_path, "error": str(e)})

        return {
            "asimov_rule_3": True,
            "pattern": error_pattern,
            "total_files": len(search_result.get("files_found", [])),
            "fixed": len(fixed_files),
            "failed": len(failed_files),
            "fixed_files": fixed_files,
            "failed_files": failed_files,
            "enforcement": "NO PARTIAL FIXES - all instances must be addressed",
        }

    async def test_html_application(
        self, html_file: str, app_type: str = "generic"
    ) -> dict[str, Any]:
        """
        Test HTML/JS application using Playwright browser automation

        Args:
            html_file: Path to HTML file
            app_type: Type of app ('tetris', 'generic')

        Returns:
            {
                'success': True/False,
                'errors': [],
                'warnings': [],
                'screenshots': [],
                'metrics': {},
                'quality_score': 0.0-1.0,
                'recommendation': 'APPROVE/NEEDS_FIXES/REJECT'
            }
        """
        logger.info(f"Testing HTML application: {html_file} (type: {app_type})")

        if not PLAYWRIGHT_AVAILABLE:
            return {
                "success": False,
                "errors": [
                    "Playwright not available - install with: pip install playwright && playwright install"
                ],
                "warnings": [],
                "screenshots": [],
                "metrics": {},
                "quality_score": 0.0,
                "recommendation": "CANNOT_TEST",
            }

        if not os.path.exists(html_file):
            return {
                "success": False,
                "errors": [f"HTML file not found: {html_file}"],
                "warnings": [],
                "screenshots": [],
                "metrics": {},
                "quality_score": 0.0,
                "recommendation": "REJECT",
            }

        try:
            async with BrowserTester() as tester:
                # Run appropriate test based on app type
                if app_type == "tetris":
                    test_result = await tester.test_tetris_app(html_file)
                else:
                    test_result = await tester.test_generic_html_app(html_file)

                # Calculate quality score
                quality_score = self._calculate_html_app_quality_score(test_result)

                # Add quality score and recommendation
                test_result["quality_score"] = quality_score
                test_result["recommendation"] = self._get_recommendation(
                    quality_score, test_result
                )

                logger.info(
                    f"HTML app test complete: Quality = {quality_score:.2f}, Recommendation = {test_result['recommendation']}"
                )

                return test_result

        except Exception as e:
            logger.error(f"HTML app testing failed: {e}")
            return {
                "success": False,
                "errors": [f"Test exception: {str(e)}"],
                "warnings": [],
                "screenshots": [],
                "metrics": {},
                "quality_score": 0.0,
                "recommendation": "REJECT",
            }

    def _calculate_html_app_quality_score(self, test_result: dict[str, Any]) -> float:
        """
        Calculate quality score for HTML app based on test results

        Scoring:
        - No errors: +0.5
        - Canvas/elements found: +0.2
        - No JS errors: +0.2
        - Functional controls: +0.1
        """
        score = 0.0

        # Base score: No errors
        if not test_result.get("errors"):
            score += 0.5

        # Metrics scoring
        metrics = test_result.get("metrics", {})

        if metrics.get("canvas_found"):
            score += 0.1
        if metrics.get("no_js_errors"):
            score += 0.2
        if metrics.get("controls_tested"):
            score += 0.1
        if metrics.get("game_starts"):
            score += 0.1

        # Warnings reduce score slightly
        warnings_count = len(test_result.get("warnings", []))
        score -= warnings_count * 0.05

        return max(0.0, min(1.0, score))  # Clamp to 0.0-1.0

    def _get_recommendation(
        self, quality_score: float, test_result: dict[str, Any]
    ) -> str:
        """
        Get recommendation based on quality score and test results
        """
        errors_count = len(test_result.get("errors", []))

        if errors_count > 0:
            return "NEEDS_FIXES"
        elif quality_score >= 0.8:
            return "APPROVE"
        elif quality_score >= 0.5:
            return "NEEDS_IMPROVEMENTS"
        else:
            return "REJECT"

    def _format_metrics(self, metrics: dict[str, Any]) -> str:
        """Format metrics for display"""
        lines = []
        for key, value in metrics.items():
            if isinstance(value, bool):
                emoji = "✅" if value else "❌"
                lines.append(f"{emoji} {key}: {value}")
            else:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    async def _process_agent_request(self, message: Any) -> Any:
        """Process request from another agent"""
        request = TaskRequest(
            prompt=message.get("prompt", ""), context=message.get("context", {})
        )
        result = await self.execute(request)
        return result.content
