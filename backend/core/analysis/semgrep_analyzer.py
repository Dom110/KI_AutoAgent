"""
Semgrep-based semantic code analysis

Provides pattern-based code analysis for:
- Security vulnerabilities
- Performance anti-patterns
- Best practice violations
- Custom rule enforcement
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class SemgrepAnalyzer:
    """
    Semantic code analyzer using Semgrep patterns

    Features:
    - Security vulnerability detection
    - Performance analysis
    - Best practices enforcement
    - Custom rule creation
    """

    def __init__(self):
        self.rules_dir = Path(__file__).parent / 'semgrep_rules'
        self.results_cache = {}
        self.custom_rules = []

    async def run_analysis(self, target_path: str = '.', rules: Optional[List[str]] = None, progress_callback=None) -> Dict:
        """
        Run Semgrep analysis on codebase

        Args:
            target_path: Path to analyze
            rules: Specific rules to run (default: all)

        Returns:
            Analysis results with findings
        """
        logger.info(f"Running Semgrep analysis on {target_path}")

        results = {
            'security': [],
            'performance': [],
            'best_practices': [],
            'bugs': [],
            'summary': {}
        }

        # Try to run actual semgrep if available
        if await self._is_semgrep_available():
            if progress_callback:
                await progress_callback("🔒 Running Semgrep security analysis...")
            results = await self._run_semgrep_cli(target_path, rules, progress_callback)
        else:
            # Fallback to pattern-based analysis
            if progress_callback:
                await progress_callback("🔒 Running pattern-based security analysis...")
            results = await self._run_pattern_analysis(target_path, progress_callback)

        # Categorize and prioritize findings
        results = await self._categorize_findings(results)

        return results

    async def _is_semgrep_available(self) -> bool:
        """Check if semgrep CLI is installed"""
        try:
            result = subprocess.run(['semgrep', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    async def _run_semgrep_cli(self, target_path: str, rules: Optional[List[str]], progress_callback=None) -> Dict:
        """Run actual Semgrep CLI"""
        cmd = ['semgrep', '--json', '--config=auto']

        if rules:
            for rule in rules:
                cmd.extend(['--config', rule])

        cmd.append(target_path)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.warning(f"Semgrep failed: {result.stderr}")
                return {}
        except Exception as e:
            logger.error(f"Error running Semgrep: {e}")
            return {}

    async def _run_pattern_analysis(self, target_path: str, progress_callback=None) -> Dict:
        """Fallback pattern-based analysis without Semgrep CLI"""
        results = {
            'security': [],
            'performance': [],
            'best_practices': [],
            'bugs': []
        }

        import asyncio

        # Define common vulnerability patterns
        security_patterns = {
            'sql_injection': [
                r'f".*SELECT.*{.*}.*FROM',
                r'f".*INSERT.*{.*}.*INTO',
                r'".*SELECT.*" \+ \w+',
                r'\.format\(.*SELECT.*FROM'
            ],
            'hardcoded_secrets': [
                r'(password|secret|api_key|token)\s*=\s*["\'][^"\']+["\']',
                r'AWS_SECRET_KEY\s*=',
                r'PRIVATE_KEY\s*='
            ],
            'unsafe_deserialization': [
                r'pickle\.loads\(',
                r'eval\(',
                r'exec\(',
                r'__import__\('
            ],
            'path_traversal': [
                r'open\([^,)]*\+[^,)]*\)',
                r'\.\./',
                r'os\.path\.join\([^,)]*user'
            ]
        }

        performance_patterns = {
            'nested_loops_db': [
                r'for .*:\n.*for .*:\n.*\.(find|query|select)',
                r'while .*:\n.*while .*:'
            ],
            'sync_in_async': [
                r'async def.*\n.*time\.sleep',
                r'async def.*\n.*requests\.'
            ],
            'inefficient_string_concat': [
                r'for .*:\n.*\+= ["\']'
            ]
        }

        best_practices_patterns = {
            'broad_exception': [
                r'except:',
                r'except Exception:',
                r'except BaseException:'
            ],
            'mutable_defaults': [
                r'def \w+\([^)]*=\[\][^)]*\)',
                r'def \w+\([^)]*=\{\}[^)]*\)'
            ],
            'missing_type_hints': [
                r'def \w+\([^:)]+\)[^:]*:',
                r'def \w+\(\) *:'
            ]
        }

        # Directories to always exclude
        exclude_dirs = {
            'node_modules', '__pycache__', 'venv', '.venv', 'env', '.env',
            'dist', 'build', '.git', '.pytest_cache', '.tox', 'htmlcov',
            'site-packages', '.mypy_cache', '.ruff_cache', 'migrations'
        }

        # Count total files first (excluding common directories)
        path = Path(target_path)
        py_files = []
        excluded_count = 0
        for py_file in path.rglob('*.py'):
            should_exclude = False
            for part in py_file.parts:
                if part in exclude_dirs or part.startswith('.'):
                    should_exclude = True
                    excluded_count += 1
                    break
            if not should_exclude:
                py_files.append(py_file)

        total_files = len(py_files)
        # No limits - analyze ALL PROJECT files
        logger.info(f"Analyzing {total_files} Python files for security patterns (excluded {excluded_count} files)")

        if progress_callback:
            await progress_callback(f"🔒 Analyzing {total_files} Python files for security patterns...")

        # Scan files for patterns
        for i, py_file in enumerate(py_files, 1):
            # More frequent progress updates for better feedback
            if progress_callback:
                # Update every file for first 20, then every 5 files
                if i <= 20 or i % 5 == 0 or i == total_files:
                    await progress_callback(f"🔒 Security scan: {i}/{total_files} files...")
            try:
                # Add timeout for file reading
                content = await asyncio.wait_for(
                    asyncio.to_thread(py_file.read_text, encoding='utf-8'),
                    timeout=2.0
                )

                # Limit content size for regex to prevent ReDoS
                import re
                truncated_content = content[:100000] if len(content) > 100000 else content

                # Check security patterns
                for vuln_type, patterns in security_patterns.items():
                    for pattern in patterns:
                        try:
                            matches = re.finditer(pattern, truncated_content, re.MULTILINE)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                results['security'].append({
                                    'type': vuln_type,
                                    'file': str(py_file),
                                    'line': line_num,
                                    'severity': 'high' if 'injection' in vuln_type else 'medium',
                                    'message': f"Potential {vuln_type.replace('_', ' ')} vulnerability",
                                    'code': truncated_content[match.start():match.end()]
                                })
                        except re.error:
                            logger.warning(f"Regex error for pattern {pattern} in {py_file}")

                # Check performance patterns
                for perf_type, patterns in performance_patterns.items():
                    for pattern in patterns:
                        try:
                            matches = re.finditer(pattern, truncated_content, re.MULTILINE)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                results['performance'].append({
                                    'type': perf_type,
                                    'file': str(py_file),
                                    'line': line_num,
                                    'severity': 'medium',
                                    'message': f"Performance issue: {perf_type.replace('_', ' ')}",
                                    'code': truncated_content[match.start():match.end()]
                                })
                        except re.error:
                            logger.warning(f"Regex error for pattern {pattern} in {py_file}")

                # Check best practices
                for practice_type, patterns in best_practices_patterns.items():
                    for pattern in patterns:
                        try:
                            matches = re.finditer(pattern, truncated_content, re.MULTILINE)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                results['best_practices'].append({
                                    'type': practice_type,
                                    'file': str(py_file),
                                    'line': line_num,
                                    'severity': 'low',
                                    'message': f"Best practice violation: {practice_type.replace('_', ' ')}",
                                    'code': truncated_content[match.start():match.end()]
                                })
                        except re.error:
                            logger.warning(f"Regex error for pattern {pattern} in {py_file}")

            except asyncio.TimeoutError:
                logger.warning(f"Timeout reading {py_file}")
            except Exception as e:
                logger.warning(f"Failed to analyze {py_file}: {e}")

            # Yield control frequently to prevent blocking
            if i % 2 == 0:  # Every 2 files for better responsiveness
                await asyncio.sleep(0)

        if progress_callback:
            total_issues = len(results['security']) + len(results['performance']) + len(results['best_practices'])
            await progress_callback(f"🔒 Security analysis complete: {total_issues} total issues found")

        return results

    async def _categorize_findings(self, results: Dict) -> Dict:
        """Categorize and prioritize findings"""
        # Add summary
        results['summary'] = {
            'total_issues': sum(len(v) for v in results.values() if isinstance(v, list)),
            'critical': len([i for v in results.values() if isinstance(v, list)
                           for i in v if i.get('severity') == 'critical']),
            'high': len([i for v in results.values() if isinstance(v, list)
                        for i in v if i.get('severity') == 'high']),
            'medium': len([i for v in results.values() if isinstance(v, list)
                         for i in v if i.get('severity') == 'medium']),
            'low': len([i for v in results.values() if isinstance(v, list)
                       for i in v if i.get('severity') == 'low'])
        }

        # Sort by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}

        for category in ['security', 'performance', 'best_practices', 'bugs']:
            if category in results and isinstance(results[category], list):
                results[category].sort(
                    key=lambda x: severity_order.get(x.get('severity', 'low'), 3)
                )

        return results

    async def create_custom_rule(self, rule_definition: Dict) -> str:
        """
        Create custom Semgrep rule

        Args:
            rule_definition: Rule specification

        Returns:
            Rule ID
        """
        rule_id = f"custom_{len(self.custom_rules)}"

        rule = {
            'id': rule_id,
            'pattern': rule_definition.get('pattern'),
            'message': rule_definition.get('message', 'Custom rule violation'),
            'severity': rule_definition.get('severity', 'warning'),
            'languages': rule_definition.get('languages', ['python'])
        }

        self.custom_rules.append(rule)
        return rule_id

    async def check_security_best_practices(self, code_index: Dict) -> List[Dict]:
        """
        Check for security best practices

        Args:
            code_index: Code index from CodeIndexer

        Returns:
            List of security recommendations
        """
        recommendations = []

        # Check for authentication
        has_auth = any('auth' in str(f).lower() or 'login' in str(f).lower()
                       for f in code_index.get('ast', {}).get('files', {}))

        if not has_auth:
            recommendations.append({
                'type': 'missing_authentication',
                'severity': 'high',
                'recommendation': 'Implement proper authentication mechanism',
                'details': 'No authentication module detected in the codebase'
            })

        # Check for input validation
        has_validation = any('validate' in str(f).lower() or 'sanitize' in str(f).lower()
                            for f in code_index.get('ast', {}).get('files', {}))

        if not has_validation:
            recommendations.append({
                'type': 'missing_input_validation',
                'severity': 'high',
                'recommendation': 'Add input validation and sanitization',
                'details': 'No input validation detected'
            })

        # Check for encryption
        has_encryption = any('encrypt' in str(f).lower() or 'crypto' in str(f).lower()
                            for f in code_index.get('ast', {}).get('files', {}))

        if not has_encryption:
            recommendations.append({
                'type': 'missing_encryption',
                'severity': 'medium',
                'recommendation': 'Implement encryption for sensitive data',
                'details': 'No encryption utilities found'
            })

        # Check for rate limiting
        has_rate_limit = any('rate' in str(f).lower() and 'limit' in str(f).lower()
                            for f in code_index.get('ast', {}).get('api_endpoints', {}))

        if not has_rate_limit:
            recommendations.append({
                'type': 'missing_rate_limiting',
                'severity': 'medium',
                'recommendation': 'Add rate limiting to API endpoints',
                'details': 'API endpoints lack rate limiting'
            })

        return recommendations

    async def generate_fix_suggestions(self, findings: List[Dict]) -> List[Dict]:
        """
        Generate fix suggestions for findings

        Args:
            findings: List of security/performance findings

        Returns:
            List of fix suggestions with code
        """
        fixes = []

        for finding in findings:
            fix = {
                'finding': finding,
                'suggestion': '',
                'code_fix': ''
            }

            if finding.get('type') == 'sql_injection':
                fix['suggestion'] = 'Use parameterized queries'
                fix['code_fix'] = """
# Instead of:
query = f"SELECT * FROM users WHERE id = {user_id}"

# Use:
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
"""

            elif finding.get('type') == 'hardcoded_secrets':
                fix['suggestion'] = 'Use environment variables'
                fix['code_fix'] = """
# Instead of:
API_KEY = "hardcoded_key_here"

# Use:
import os
API_KEY = os.environ.get('API_KEY')
"""

            elif finding.get('type') == 'broad_exception':
                fix['suggestion'] = 'Catch specific exceptions'
                fix['code_fix'] = """
# Instead of:
try:
    risky_operation()
except Exception:
    pass

# Use:
try:
    risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    # Handle specific error
"""

            elif finding.get('type') == 'sync_in_async':
                fix['suggestion'] = 'Use async alternatives'
                fix['code_fix'] = """
# Instead of:
async def fetch_data():
    time.sleep(1)  # Blocking!
    response = requests.get(url)  # Blocking!

# Use:
async def fetch_data():
    await asyncio.sleep(1)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
"""

            fixes.append(fix)

        return fixes

    def get_severity_score(self, findings: Dict) -> int:
        """
        Calculate overall severity score

        Args:
            findings: Analysis findings

        Returns:
            Severity score (0-100)
        """
        score = 100  # Start with perfect score

        # Deduct points based on findings
        severity_weights = {
            'critical': 20,
            'high': 10,
            'medium': 5,
            'low': 2
        }

        for category in findings.values():
            if isinstance(category, list):
                for finding in category:
                    severity = finding.get('severity', 'low')
                    score -= severity_weights.get(severity, 1)

        return max(0, score)  # Don't go below 0