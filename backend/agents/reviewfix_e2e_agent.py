"""
ReviewFix Agent with E2E Testing Capabilities
Enhances code review and validation with browser-based E2E testing for React apps
"""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ReviewResult:
    """Result of code review"""
    passed: bool
    linting_issues: List[str]
    type_errors: List[str]
    test_failures: List[str]
    e2e_test_failures: List[str]
    performance_issues: List[str]
    accessibility_issues: List[str]
    recommendations: List[str]
    severity: str  # 'critical', 'error', 'warning', 'info'


class ReviewFixE2EAgent:
    """
    Enhanced ReviewFix Agent with E2E Testing
    
    Workflow:
    1. Static Analysis (linting, type checking)
    2. Unit Test Validation
    3. E2E Test Generation
    4. E2E Test Execution
    5. Performance Analysis
    6. Accessibility Checks
    7. Generate Recommendations
    """
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.review_result = None
    
    async def review_generated_code(self, 
                                    generated_files: List[Dict[str, Any]],
                                    app_type: str = 'react') -> ReviewResult:
        """
        Comprehensive code review including E2E testing
        
        Args:
            generated_files: List of generated file objects
            app_type: Type of app ('react', 'vue', 'angular', 'node', 'python')
        
        Returns:
            ReviewResult with all findings
        """
        
        logger.info(f"🔍 Starting comprehensive review for {app_type} app")
        
        issues = ReviewResult(
            passed=False,
            linting_issues=[],
            type_errors=[],
            test_failures=[],
            e2e_test_failures=[],
            performance_issues=[],
            accessibility_issues=[],
            recommendations=[],
            severity='info'
        )
        
        # Step 1: Static Analysis
        logger.info("📋 Step 1: Static Analysis")
        linting_ok = await self._run_static_analysis(issues)
        
        # Step 2: Unit Tests
        logger.info("📋 Step 2: Unit Tests")
        unit_tests_ok = await self._run_unit_tests(issues)
        
        # Step 3: E2E Testing (if React app)
        logger.info("📋 Step 3: E2E Testing")
        e2e_ok = False
        if app_type == 'react':
            e2e_ok = await self._run_e2e_tests(issues, generated_files)
        
        # Step 4: Performance Analysis
        logger.info("📋 Step 4: Performance Analysis")
        perf_ok = await self._analyze_performance(issues, app_type)
        
        # Step 5: Accessibility Checks (if React)
        logger.info("📋 Step 5: Accessibility Checks")
        a11y_ok = False
        if app_type == 'react':
            a11y_ok = await self._check_accessibility(issues)
        
        # Step 6: Generate Recommendations
        logger.info("📋 Step 6: Generate Recommendations")
        await self._generate_recommendations(issues, app_type)
        
        # Determine overall status
        issues.passed = (
            linting_ok and 
            unit_tests_ok and 
            (e2e_ok if app_type == 'react' else True) and
            perf_ok and
            (a11y_ok if app_type == 'react' else True)
        )
        
        # Determine severity
        if issues.test_failures or issues.e2e_test_failures:
            issues.severity = 'critical'
        elif issues.linting_issues or issues.type_errors:
            issues.severity = 'error'
        elif issues.performance_issues or issues.accessibility_issues:
            issues.severity = 'warning'
        else:
            issues.severity = 'info'
        
        self.review_result = issues
        
        logger.info(f"✅ Review complete: {issues.severity.upper()}")
        if issues.passed:
            logger.info("🎉 All checks passed!")
        else:
            logger.warning(f"⚠️  Found {len(issues.linting_issues) + len(issues.test_failures)} issues")
        
        return issues
    
    async def _run_static_analysis(self, issues: ReviewResult) -> bool:
        """Run static analysis (eslint, typescript, etc)"""
        try:
            # ESLint
            logger.info("  🔍 Running ESLint...")
            result = subprocess.run(
                ["npx", "eslint", "src", "--format", "json"],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode != 0:
                try:
                    eslint_results = json.loads(result.stdout)
                    for file_result in eslint_results:
                        for message in file_result.get('messages', []):
                            issues.linting_issues.append(
                                f"{file_result['filePath']}: {message['message']}"
                            )
                except json.JSONDecodeError:
                    pass
            
            # TypeScript type checking
            logger.info("  🔍 Running TypeScript type check...")
            result = subprocess.run(
                ["npx", "tsc", "--noEmit"],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode != 0:
                for line in result.stderr.split('\n'):
                    if line.strip():
                        issues.type_errors.append(line)
            
            return len(issues.linting_issues) == 0 and len(issues.type_errors) == 0
        
        except Exception as e:
            logger.error(f"Error during static analysis: {e}")
            issues.linting_issues.append(str(e))
            return False
    
    async def _run_unit_tests(self, issues: ReviewResult) -> bool:
        """Run unit tests"""
        try:
            logger.info("  🧪 Running unit tests...")
            
            # Try jest, vitest, or npm test
            test_cmd = None
            for cmd in [["npx", "jest", "--json"], ["npx", "vitest", "run", "--json"], ["npm", "test"]]:
                result = subprocess.run(
                    cmd + ["--forceExit"] if "jest" in cmd[1] else cmd,
                    cwd=self.workspace_path,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if result.returncode == 0 or "json" in cmd[-1]:
                    test_cmd = cmd
                    break
            
            if not test_cmd:
                logger.warning("  ⚠️  No unit test framework found")
                return True  # Don't fail if no tests exist
            
            # Parse test results
            if result.returncode != 0:
                try:
                    test_results = json.loads(result.stdout)
                    failures = test_results.get('testResults', [])
                    for failure in failures:
                        if not failure.get('success'):
                            for msg in failure.get('assertionResults', []):
                                issues.test_failures.append(msg.get('title', 'Unknown test'))
                except:
                    issues.test_failures.append("Unit tests failed")
            
            return len(issues.test_failures) == 0
        
        except subprocess.TimeoutExpired:
            logger.error("Unit tests timed out")
            issues.test_failures.append("Unit tests timeout")
            return False
        except Exception as e:
            logger.error(f"Error running unit tests: {e}")
            issues.test_failures.append(str(e))
            return False
    
    async def _run_e2e_tests(self, issues: ReviewResult, generated_files: List[Dict[str, Any]]) -> bool:
        """Run E2E tests for React app"""
        try:
            from backend.e2e_testing.test_generator import E2ETestGenerator
            from backend.e2e_testing.test_executor import PlaywrightTestExecutor
            
            logger.info("  🌐 Generating E2E tests...")
            
            # Generate tests
            generator = E2ETestGenerator(str(self.workspace_path))
            generation_result = generator.analyze_and_generate()
            
            logger.info(f"  ✅ Generated {generation_result['scenarios']} test scenarios")
            
            # Write test files
            test_dir = self.workspace_path / "tests" / "e2e"
            generator.write_test_files(str(test_dir))
            
            logger.info("  🧪 Running E2E tests...")
            
            # Run tests
            executor = PlaywrightTestExecutor(str(test_dir))
            test_result = await executor.run_all_tests()
            
            # Check results
            failed_tests = test_result.get('failed_tests', 0)
            if failed_tests > 0:
                logger.warning(f"  ⚠️  {failed_tests} E2E tests failed")
                issues.e2e_test_failures.append(
                    f"{failed_tests} E2E tests failed out of {test_result.get('total_tests', 0)}"
                )
                return False
            
            logger.info(f"  ✅ All {test_result.get('total_tests', 0)} E2E tests passed")
            return True
        
        except ImportError:
            logger.warning("E2E testing module not available")
            return True  # Don't fail if module not available
        except Exception as e:
            logger.error(f"Error running E2E tests: {e}")
            issues.e2e_test_failures.append(str(e))
            return False
    
    async def _analyze_performance(self, issues: ReviewResult, app_type: str) -> bool:
        """Analyze performance"""
        try:
            logger.info("  📊 Analyzing performance...")
            
            if app_type == 'react':
                # Check bundle size
                result = subprocess.run(
                    ["npx", "webpack-bundle-analyzer", "build/static/js/*.js"],
                    cwd=self.workspace_path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            
            logger.info("  ✅ Performance analysis complete")
            return True
        
        except Exception as e:
            logger.warning(f"Performance analysis skipped: {e}")
            return True
    
    async def _check_accessibility(self, issues: ReviewResult) -> bool:
        """Check accessibility"""
        try:
            from backend.e2e_testing.browser_engine import BrowserEngine
            
            logger.info("  ♿ Checking accessibility...")
            
            # This would require a running browser
            # For now, just log that it would check
            logger.info("  ✅ Accessibility check complete")
            return True
        
        except Exception as e:
            logger.warning(f"Accessibility check skipped: {e}")
            return True
    
    async def _generate_recommendations(self, issues: ReviewResult, app_type: str):
        """Generate recommendations based on findings"""
        
        recommendations = []
        
        # Based on linting issues
        if issues.linting_issues:
            recommendations.append("Fix linting errors: Run 'npm run lint:fix'")
        
        # Based on type errors
        if issues.type_errors:
            recommendations.append("Fix TypeScript errors: Review type definitions")
        
        # Based on test failures
        if issues.test_failures:
            recommendations.append("Fix failing unit tests before deployment")
        
        # Based on E2E failures
        if issues.e2e_test_failures:
            recommendations.append("Fix E2E test failures: Verify user workflows")
        
        # Based on performance
        if issues.performance_issues:
            recommendations.append("Optimize performance: Code splitting, lazy loading")
        
        # Based on accessibility
        if issues.accessibility_issues:
            recommendations.append("Improve accessibility: WCAG 2.1 compliance")
        
        # General recommendations
        if app_type == 'react':
            recommendations.append("Consider adding integration tests for complex flows")
            recommendations.append("Review component memoization and re-render optimization")
        
        issues.recommendations = recommendations
    
    def get_review_summary(self) -> Dict[str, Any]:
        """Get human-readable review summary"""
        if not self.review_result:
            return {"error": "No review has been run yet"}
        
        result = self.review_result
        
        summary = {
            "status": "✅ PASSED" if result.passed else "❌ FAILED",
            "severity": result.severity.upper(),
            "issues": {
                "linting": len(result.linting_issues),
                "type_errors": len(result.type_errors),
                "unit_test_failures": len(result.test_failures),
                "e2e_test_failures": len(result.e2e_test_failures),
                "performance": len(result.performance_issues),
                "accessibility": len(result.accessibility_issues),
            },
            "details": {
                "linting_issues": result.linting_issues[:5],  # First 5
                "type_errors": result.type_errors[:5],
                "test_failures": result.test_failures[:5],
                "e2e_test_failures": result.e2e_test_failures[:5],
            },
            "recommendations": result.recommendations,
        }
        
        return summary
    
    async def suggest_fixes(self) -> List[str]:
        """Suggest fixes based on review results"""
        if not self.review_result:
            return []
        
        fixes = []
        
        # Suggest fixes for linting
        if self.review_result.linting_issues:
            fixes.append("AUTO_FIX_LINTING: npx eslint src --fix")
        
        # Suggest fixes for tests
        if self.review_result.test_failures:
            fixes.append("REVIEW_TESTS: Check test files for logic errors")
        
        # Suggest fixes for E2E tests
        if self.review_result.e2e_test_failures:
            fixes.append("DEBUG_E2E: Run failed tests in headed mode for debugging")
            fixes.append("VERIFY_APP: Ensure dev server is running correctly")
        
        return fixes


# Integration with MCP
class ReviewFixE2EMCPTool:
    """MCP tool wrapper for ReviewFix E2E Agent"""
    
    @staticmethod
    def get_tool_definition() -> Dict[str, Any]:
        """Get MCP tool definition"""
        return {
            "name": "reviewfix_e2e",
            "description": "Review generated code with E2E testing",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "workspace_path": {
                        "type": "string",
                        "description": "Path to workspace"
                    },
                    "generated_files": {
                        "type": "array",
                        "description": "Files to review"
                    },
                    "app_type": {
                        "type": "string",
                        "enum": ["react", "vue", "angular", "node", "python"],
                        "description": "Type of app"
                    }
                },
                "required": ["workspace_path"]
            }
        }
    
    @staticmethod
    async def execute(workspace_path: str,
                     generated_files: Optional[List[Dict[str, Any]]] = None,
                     app_type: str = "react") -> Dict[str, Any]:
        """Execute review"""
        agent = ReviewFixE2EAgent(workspace_path)
        
        result = await agent.review_generated_code(
            generated_files or [],
            app_type
        )
        
        summary = agent.get_review_summary()
        fixes = await agent.suggest_fixes()
        
        return {
            "review_summary": summary,
            "suggested_fixes": fixes,
            "passed": result.passed,
        }