"""
Dead code detection using Vulture

Identifies:
- Unused functions
- Unused variables
- Unused imports
- Unreachable code
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class VultureAnalyzer:
    """
    Dead code analyzer to identify unused code

    Features:
    - Find unused functions and methods
    - Detect unused variables
    - Identify unused imports
    - Report unreachable code
    """

    def __init__(self):
        self.whitelist = []
        self.min_confidence = 60

    async def find_dead_code(self, target_path: str = '.') -> Dict:
        """
        Find all dead/unused code in project

        Args:
            target_path: Path to analyze

        Returns:
            Dead code findings
        """
        logger.info(f"Searching for dead code in {target_path}")

        results = {
            'unused_functions': [],
            'unused_variables': [],
            'unused_imports': [],
            'unused_classes': [],
            'unreachable_code': [],
            'summary': {}
        }

        # Try to use vulture CLI if available
        if await self._is_vulture_available():
            results = await self._run_vulture_cli(target_path)
        else:
            # Fallback to manual detection
            results = await self._manual_dead_code_detection(target_path)

        # Calculate statistics
        results['summary'] = self._calculate_summary(results)

        return results

    async def _is_vulture_available(self) -> bool:
        """Check if vulture CLI is installed"""
        try:
            result = subprocess.run(['vulture', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    async def _run_vulture_cli(self, target_path: str) -> Dict:
        """Run actual Vulture CLI"""
        cmd = ['vulture', target_path, '--min-confidence', str(self.min_confidence)]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return await self._parse_vulture_output(result.stdout)
        except Exception as e:
            logger.error(f"Error running Vulture: {e}")
            return {}

    async def _parse_vulture_output(self, output: str) -> Dict:
        """Parse Vulture CLI output"""
        results = {
            'unused_functions': [],
            'unused_variables': [],
            'unused_imports': [],
            'unused_classes': [],
            'unreachable_code': []
        }

        for line in output.split('\n'):
            if not line.strip():
                continue

            # Parse vulture output format: file:line: unused item 'name' (confidence%)
            import re
            match = re.match(r'(.+):(\d+): unused (\w+) \'(.+)\' \((\d+)%', line)
            if match:
                file_path, line_num, item_type, name, confidence = match.groups()

                finding = {
                    'file': file_path,
                    'line': int(line_num),
                    'name': name,
                    'confidence': int(confidence)
                }

                if 'function' in item_type or 'method' in item_type:
                    results['unused_functions'].append(finding)
                elif 'variable' in item_type or 'attribute' in item_type:
                    results['unused_variables'].append(finding)
                elif 'import' in item_type:
                    results['unused_imports'].append(finding)
                elif 'class' in item_type:
                    results['unused_classes'].append(finding)
                else:
                    results['unreachable_code'].append(finding)

        return results

    async def _manual_dead_code_detection(self, target_path: str) -> Dict:
        """Manual dead code detection without Vulture"""
        results = {
            'unused_functions': [],
            'unused_variables': [],
            'unused_imports': [],
            'unused_classes': [],
            'unreachable_code': []
        }

        path = Path(target_path)
        all_definitions = {}
        all_usages = {}

        # First pass: collect all definitions
        for py_file in path.rglob('*.py'):
            try:
                content = py_file.read_text(encoding='utf-8')

                # Find function definitions
                import re
                func_pattern = r'def\s+(\w+)\s*\('
                for match in re.finditer(func_pattern, content):
                    func_name = match.group(1)
                    if not func_name.startswith('_'):  # Skip private
                        line = content[:match.start()].count('\n') + 1
                        all_definitions[func_name] = {
                            'type': 'function',
                            'file': str(py_file),
                            'line': line
                        }

                # Find class definitions
                class_pattern = r'class\s+(\w+)'
                for match in re.finditer(class_pattern, content):
                    class_name = match.group(1)
                    line = content[:match.start()].count('\n') + 1
                    all_definitions[class_name] = {
                        'type': 'class',
                        'file': str(py_file),
                        'line': line
                    }

                # Find imports
                import_patterns = [
                    r'from\s+\S+\s+import\s+(\w+)',
                    r'import\s+(\w+)'
                ]
                for pattern in import_patterns:
                    for match in re.finditer(pattern, content):
                        import_name = match.group(1)
                        line = content[:match.start()].count('\n') + 1
                        key = f"{py_file}:{import_name}"
                        all_definitions[key] = {
                            'type': 'import',
                            'file': str(py_file),
                            'line': line,
                            'name': import_name
                        }

            except Exception as e:
                logger.warning(f"Failed to analyze {py_file}: {e}")

        # Second pass: find usages
        for py_file in path.rglob('*.py'):
            try:
                content = py_file.read_text(encoding='utf-8')

                for name in all_definitions.keys():
                    # Skip checking in definition file
                    if ':' not in name:  # Not an import
                        if name in content:
                            all_usages[name] = all_usages.get(name, 0) + content.count(name)

            except Exception:
                pass

        # Find unused items
        for name, definition in all_definitions.items():
            if ':' not in name:  # Not an import
                usage_count = all_usages.get(name, 0)
                if usage_count <= 1:  # Only the definition itself
                    if definition['type'] == 'function':
                        results['unused_functions'].append({
                            'file': definition['file'],
                            'line': definition['line'],
                            'name': name,
                            'confidence': 80
                        })
                    elif definition['type'] == 'class':
                        results['unused_classes'].append({
                            'file': definition['file'],
                            'line': definition['line'],
                            'name': name,
                            'confidence': 80
                        })

        # Check for unreachable code
        for py_file in path.rglob('*.py'):
            try:
                content = py_file.read_text(encoding='utf-8')

                # Find code after return/raise/break/continue
                unreachable_pattern = r'(return|raise|break|continue).*\n\s+\S'
                for match in re.finditer(unreachable_pattern, content):
                    line = content[:match.start()].count('\n') + 1
                    results['unreachable_code'].append({
                        'file': str(py_file),
                        'line': line + 1,
                        'confidence': 90
                    })

            except Exception:
                pass

        return results

    def _calculate_summary(self, results: Dict) -> Dict:
        """Calculate summary statistics"""
        total_dead_code = 0
        for category in ['unused_functions', 'unused_variables', 'unused_imports',
                        'unused_classes', 'unreachable_code']:
            if category in results:
                total_dead_code += len(results[category])

        summary = {
            'total_dead_code': total_dead_code,
            'unused_functions': len(results.get('unused_functions', [])),
            'unused_variables': len(results.get('unused_variables', [])),
            'unused_imports': len(results.get('unused_imports', [])),
            'unused_classes': len(results.get('unused_classes', [])),
            'unreachable_code': len(results.get('unreachable_code', []))
        }

        # Calculate potential size reduction
        # Rough estimate: each unused item ~5 lines average
        summary['estimated_lines_to_remove'] = total_dead_code * 5
        summary['cleanup_priority'] = 'high' if total_dead_code > 50 else 'medium' if total_dead_code > 20 else 'low'

        return summary

    async def generate_cleanup_script(self, findings: Dict) -> str:
        """
        Generate script to clean up dead code

        Args:
            findings: Dead code findings

        Returns:
            Cleanup script
        """
        script = """#!/usr/bin/env python
'''
Dead Code Cleanup Script
Generated by VultureAnalyzer

WARNING: Review each change before applying!
'''

import os

def cleanup_dead_code():
    \"\"\"Remove identified dead code\"\"\"

    # Files to modify
    modifications = [
"""

        # Add each file and lines to remove
        files_to_modify = {}

        for category in ['unused_functions', 'unused_variables', 'unused_imports',
                        'unused_classes', 'unreachable_code']:
            for item in findings.get(category, []):
                file_path = item['file']
                if file_path not in files_to_modify:
                    files_to_modify[file_path] = []
                files_to_modify[file_path].append(item['line'])

        for file_path, lines in files_to_modify.items():
            script += f"        ('{file_path}', {sorted(lines)}),\n"

        script += """    ]

    for file_path, lines_to_remove in modifications:
        print(f"Processing {file_path}...")

        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Remove lines (in reverse order to maintain line numbers)
        for line_num in sorted(lines_to_remove, reverse=True):
            if 0 < line_num <= len(lines):
                print(f"  Removing line {line_num}: {lines[line_num-1].strip()}")
                # Comment out instead of removing for safety
                lines[line_num-1] = f"# REMOVED: {lines[line_num-1]}"

        # Write back
        with open(file_path, 'w') as f:
            f.writelines(lines)

    print("Cleanup complete! Review changes with 'git diff'")

if __name__ == '__main__':
    cleanup_dead_code()
"""

        return script

    async def create_whitelist(self, patterns: List[str]) -> None:
        """
        Create whitelist for false positives

        Args:
            patterns: Patterns to whitelist
        """
        self.whitelist.extend(patterns)

    def calculate_code_coverage_estimate(self, findings: Dict, total_lines: int) -> float:
        """
        Estimate code coverage based on dead code

        Args:
            findings: Dead code findings
            total_lines: Total lines of code

        Returns:
            Estimated coverage percentage
        """
        dead_lines = findings['summary'].get('estimated_lines_to_remove', 0)
        live_lines = total_lines - dead_lines

        if total_lines > 0:
            return (live_lines / total_lines) * 100
        return 0.0