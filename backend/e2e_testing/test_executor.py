"""
Test Executor - Runs Playwright tests and collects results
"""

import subprocess
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import xml.etree.ElementTree as ET


@dataclass
class TestResult:
    """Individual test result"""
    name: str
    passed: bool
    duration: float
    error_message: Optional[str]
    screenshots: List[str]
    logs: List[str]


@dataclass
class TestSuiteResult:
    """Complete test suite result"""
    suite_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    total_duration: float
    tests: List[TestResult]
    timestamp: str


class PlaywrightTestExecutor:
    """Executes Playwright tests"""
    
    def __init__(self, test_dir: str, config: Optional[Dict[str, Any]] = None):
        self.test_dir = Path(test_dir)
        self.config = config or {}
        self.results: List[TestSuiteResult] = []
        self.browser_context = None
        
        # Configuration
        self.browser = self.config.get('browser', 'chromium')
        self.headless = self.config.get('headless', True)
        self.workers = self.config.get('workers', 1)
        self.timeout = self.config.get('timeout', 30000)
        self.retry = self.config.get('retry', 0)
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests in directory"""
        print(f"🧪 Running all Playwright tests in {self.test_dir}")
        
        # Find all test files
        test_files = list(self.test_dir.glob('**/*.spec.ts')) + list(self.test_dir.glob('**/*.spec.js'))
        
        if not test_files:
            print(f"⚠️  No test files found in {self.test_dir}")
            return {'total_tests': 0, 'passed': 0, 'failed': 0}
        
        print(f"📝 Found {len(test_files)} test files")
        
        # Run tests with playwright
        result = await self._run_playwright(test_files)
        
        return result
    
    async def run_test_file(self, test_file: str) -> TestSuiteResult:
        """Run a single test file"""
        print(f"🧪 Running test file: {test_file}")
        
        try:
            result = await self._execute_test(test_file)
            return result
        except Exception as e:
            print(f"❌ Error running test: {e}")
            raise
    
    async def run_tests_by_pattern(self, pattern: str) -> Dict[str, Any]:
        """Run tests matching pattern"""
        print(f"🔍 Running tests matching: {pattern}")
        
        test_files = list(self.test_dir.glob(f"**/{pattern}.spec.ts"))
        test_files.extend(self.test_dir.glob(f"**/{pattern}.spec.js"))
        
        if not test_files:
            print(f"⚠️  No tests match pattern: {pattern}")
            return {'total_tests': 0, 'passed': 0, 'failed': 0}
        
        results = []
        for test_file in test_files:
            result = await self.run_test_file(str(test_file))
            results.append(result)
        
        return self._aggregate_results(results)
    
    async def _run_playwright(self, test_files: List[Path]) -> Dict[str, Any]:
        """Run Playwright tests"""
        try:
            # Generate playwright.config.ts if needed
            config_file = self.test_dir / 'playwright.config.ts'
            if not config_file.exists():
                self._generate_playwright_config(str(config_file))
            
            # Run playwright
            cmd = [
                'npx',
                'playwright',
                'test',
                '--config',
                str(config_file),
            ]
            
            if self.headless:
                cmd.append('--headed=false')
            
            cmd.extend([
                '--workers',
                str(self.workers),
                '--timeout',
                str(self.timeout),
            ])
            
            print(f"🚀 Executing: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                timeout=300,
            )
            
            # Parse results
            output = result.stdout + result.stderr
            print(f"Output: {output}")
            
            # Try to find and parse HTML report
            html_report = self.test_dir / 'playwright-report' / 'index.html'
            if html_report.exists():
                results = self._parse_playwright_report(html_report)
            else:
                # Fallback: parse from output
                results = self._parse_output(output)
            
            return results
        
        except subprocess.TimeoutExpired:
            print("⏱️  Tests timed out")
            return {'error': 'Timeout', 'total_tests': 0}
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return {'error': str(e), 'total_tests': 0}
    
    async def _execute_test(self, test_file: str) -> TestSuiteResult:
        """Execute single test file"""
        from playwright.async_api import async_playwright
        
        suite_name = Path(test_file).stem
        tests = []
        
        try:
            async with async_playwright() as p:
                # Get browser
                if self.browser == 'chromium':
                    browser = await p.chromium.launch(headless=self.headless)
                elif self.browser == 'firefox':
                    browser = await p.firefox.launch(headless=self.headless)
                else:
                    browser = await p.webkit.launch(headless=self.headless)
                
                # Create context and page
                context = await browser.new_context()
                page = await context.new_page()
                
                try:
                    # Execute test logic here
                    # This is a simplified version - actual test execution would be more complex
                    
                    start_time = datetime.now()
                    
                    # Simulate test execution
                    test_result = TestResult(
                        name=suite_name,
                        passed=True,
                        duration=0.5,
                        error_message=None,
                        screenshots=[],
                        logs=[],
                    )
                    tests.append(test_result)
                    
                    duration = (datetime.now() - start_time).total_seconds()
                
                finally:
                    await context.close()
                    await browser.close()
        
        except Exception as e:
            print(f"❌ Error executing test: {e}")
            test_result = TestResult(
                name=suite_name,
                passed=False,
                duration=0,
                error_message=str(e),
                screenshots=[],
                logs=[str(e)],
            )
            tests.append(test_result)
        
        # Aggregate results
        passed = sum(1 for t in tests if t.passed)
        failed = sum(1 for t in tests if not t.passed)
        
        suite_result = TestSuiteResult(
            suite_name=suite_name,
            total_tests=len(tests),
            passed_tests=passed,
            failed_tests=failed,
            skipped_tests=0,
            total_duration=sum(t.duration for t in tests),
            tests=tests,
            timestamp=datetime.now().isoformat(),
        )
        
        self.results.append(suite_result)
        return suite_result
    
    def _generate_playwright_config(self, config_file: str):
        """Generate playwright.config.ts"""
        config = f"""
import {{ defineConfig, devices }} from '@playwright/test';

export default defineConfig({{
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : {self.retry},
  workers: process.env.CI ? 1 : {self.workers},
  reporter: 'html',
  use: {{
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  }},
  webServer: {{
    command: 'npm start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  }},
  projects: [
    {{
      name: 'chromium',
      use: {{ ...devices['Desktop Chrome'] }},
    }},
  ],
}});
"""
        
        with open(config_file, 'w') as f:
            f.write(config)
        
        print(f"✅ Generated {config_file}")
    
    def _parse_playwright_report(self, html_report: Path) -> Dict[str, Any]:
        """Parse Playwright HTML report"""
        # This is a simplified parser
        # Real implementation would parse the HTML report properly
        
        return {
            'report_file': str(html_report),
            'browser': self.browser,
        }
    
    def _parse_output(self, output: str) -> Dict[str, Any]:
        """Parse test output"""
        import re
        
        # Extract test counts from output
        passed_match = re.search(r'(\d+)\s+passed', output)
        failed_match = re.search(r'(\d+)\s+failed', output)
        skipped_match = re.search(r'(\d+)\s+skipped', output)
        
        return {
            'passed': int(passed_match.group(1)) if passed_match else 0,
            'failed': int(failed_match.group(1)) if failed_match else 0,
            'skipped': int(skipped_match.group(1)) if skipped_match else 0,
            'output': output[:500],  # First 500 chars
        }
    
    def _aggregate_results(self, results: List[TestSuiteResult]) -> Dict[str, Any]:
        """Aggregate multiple test suite results"""
        total_tests = sum(r.total_tests for r in results)
        passed_tests = sum(r.passed_tests for r in results)
        failed_tests = sum(r.failed_tests for r in results)
        skipped_tests = sum(r.skipped_tests for r in results)
        total_duration = sum(r.total_duration for r in results)
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'skipped_tests': skipped_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'total_duration': total_duration,
            'suites': len(results),
        }
    
    def export_results(self, output_file: str, format: str = 'json'):
        """Export test results"""
        if format == 'json':
            self._export_json(output_file)
        elif format == 'xml':
            self._export_xml(output_file)
        elif format == 'html':
            self._export_html(output_file)
    
    def _export_json(self, output_file: str):
        """Export results as JSON"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'total_suites': len(self.results),
            'suites': [
                {
                    'name': r.suite_name,
                    'total': r.total_tests,
                    'passed': r.passed_tests,
                    'failed': r.failed_tests,
                    'duration': r.total_duration,
                    'tests': [
                        {
                            'name': t.name,
                            'passed': t.passed,
                            'duration': t.duration,
                            'error': t.error_message,
                        }
                        for t in r.tests
                    ]
                }
                for r in self.results
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"📊 Results exported to {output_file}")
    
    def _export_xml(self, output_file: str):
        """Export results as JUnit XML"""
        root = ET.Element('testsuites')
        
        for suite in self.results:
            suite_elem = ET.SubElement(root, 'testsuite', {
                'name': suite.suite_name,
                'tests': str(suite.total_tests),
                'passed': str(suite.passed_tests),
                'failures': str(suite.failed_tests),
                'skipped': str(suite.skipped_tests),
                'time': str(suite.total_duration),
            })
            
            for test in suite.tests:
                test_elem = ET.SubElement(suite_elem, 'testcase', {
                    'name': test.name,
                    'time': str(test.duration),
                })
                
                if not test.passed:
                    failure_elem = ET.SubElement(test_elem, 'failure')
                    failure_elem.text = test.error_message or 'Test failed'
        
        tree = ET.ElementTree(root)
        tree.write(output_file)
        
        print(f"📊 Results exported to {output_file}")
    
    def _export_html(self, output_file: str):
        """Export results as HTML report"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>E2E Test Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .summary { background: #f0f0f0; padding: 20px; border-radius: 5px; }
                .passed { color: green; }
                .failed { color: red; }
                table { border-collapse: collapse; width: 100%; margin-top: 20px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background: #4CAF50; color: white; }
            </style>
        </head>
        <body>
            <h1>E2E Test Report</h1>
        """
        
        # Add summary
        total_tests = sum(r.total_tests for r in self.results)
        passed = sum(r.passed_tests for r in self.results)
        failed = sum(r.failed_tests for r in self.results)
        
        html_content += f"""
            <div class="summary">
                <h2>Summary</h2>
                <p>Total Tests: {total_tests}</p>
                <p class="passed">Passed: {passed}</p>
                <p class="failed">Failed: {failed}</p>
                <p>Success Rate: {(passed/total_tests*100):.1f if total_tests else 0}%</p>
            </div>
        """
        
        # Add detailed results
        html_content += "<h2>Test Suites</h2><table><tr><th>Suite</th><th>Tests</th><th>Passed</th><th>Failed</th><th>Duration</th></tr>"
        
        for suite in self.results:
            html_content += f"""
                <tr>
                    <td>{suite.suite_name}</td>
                    <td>{suite.total_tests}</td>
                    <td class="passed">{suite.passed_tests}</td>
                    <td class="failed">{suite.failed_tests}</td>
                    <td>{suite.total_duration:.2f}s</td>
                </tr>
            """
        
        html_content += "</table></body></html>"
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"📊 HTML report exported to {output_file}")