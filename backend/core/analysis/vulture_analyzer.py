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

    async def find_dead_code(self, target_path: str = '.', progress_callback=None) -> Dict:
        """
        Find all dead/unused code in project

        Args:
            target_path: Path to analyze
            progress_callback: Optional callback for progress updates

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
            if progress_callback:
                await progress_callback("🧹 Running Vulture dead code analysis...")
            results = await self._run_vulture_cli(target_path)
        else:
            # Fallback to manual detection
            if progress_callback:
                await progress_callback("🧹 Analyzing code for unused elements...")
            results = await self._manual_dead_code_detection(target_path, progress_callback)

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

    async def _manual_dead_code_detection(self, target_path: str, progress_callback=None) -> Dict:
        """Manual dead code detection without Vulture"""
        import asyncio
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

        # Directories to always exclude
        exclude_dirs = {
            'node_modules', '__pycache__', 'venv', '.venv', 'env', '.env',
            'dist', 'build', '.git', '.pytest_cache', '.tox', 'htmlcov',
            'site-packages', '.mypy_cache', '.ruff_cache', 'migrations'
        }

        # Count total files first (excluding common directories)
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
        logger.info(f"Analyzing {total_files} Python files for dead code (excluded {excluded_count} files)")

        if progress_callback:
            await progress_callback(f"🧹 Analyzing {total_files} Python files for unused code...")

        # First pass: collect all definitions
        for i, py_file in enumerate(py_files, 1):
            # More frequent progress updates for better feedback
            if progress_callback:
                # Update every file for first 20, then every 5 files
                if i <= 20 or i % 5 == 0 or i == total_files:
                    await progress_callback(f"🧹 Scanning definitions: {i}/{total_files} files...")
            try:
                # Add timeout for file reading
                content = await asyncio.wait_for(
                    asyncio.to_thread(py_file.read_text, encoding='utf-8'),
                    timeout=2.0
                )

                # Find function definitions (with timeout for regex operations)
                import re
                # Use simpler, non-backtracking regex for performance
                func_pattern = r'^\s*def\s+(\w+)\s*\('
                try:
                    # Limit content size for regex to prevent ReDoS
                    truncated_content = content[:50000] if len(content) > 50000 else content
                    for match in re.finditer(func_pattern, truncated_content, re.MULTILINE):
                        func_name = match.group(1)
                        if not func_name.startswith('_'):  # Skip private
                            line = content[:match.start()].count('\n') + 1
                            all_definitions[func_name] = {
                                'type': 'function',
                                'file': str(py_file),
                                'line': line
                            }
                except re.error:
                    logger.warning(f"Regex error processing {py_file}")

                # Find class definitions (with safer regex)
                class_pattern = r'^\s*class\s+(\w+)'
                try:
                    truncated_content = content[:50000] if len(content) > 50000 else content
                    for match in re.finditer(class_pattern, truncated_content, re.MULTILINE):
                        class_name = match.group(1)
                        line = content[:match.start()].count('\n') + 1
                        all_definitions[class_name] = {
                            'type': 'class',
                            'file': str(py_file),
                            'line': line
                        }
                except re.error:
                    logger.warning(f"Regex error processing classes in {py_file}")

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

            except asyncio.TimeoutError:
                logger.warning(f"Timeout reading {py_file}")
            except Exception as e:
                logger.warning(f"Failed to analyze {py_file}: {e}")

            # Yield control periodically for better responsiveness
            # More frequent yields for better UI responsiveness
            if i % 2 == 0:  # Every 2 files
                await asyncio.sleep(0)  # Just yield, no delay needed

        if progress_callback:
            await progress_callback(f"🧹 Checking usages in {total_files} files...")

        # Second pass: find usages (analyze ALL files)
        for i, py_file in enumerate(py_files, 1):
            # More frequent progress updates
            if progress_callback:
                if i <= 20 or i % 5 == 0 or i == total_files:
                    await progress_callback(f"🧹 Checking usages: {i}/{total_files} files...")
            try:
                # Add timeout for file reading
                content = await asyncio.wait_for(
                    asyncio.to_thread(py_file.read_text, encoding='utf-8'),
                    timeout=2.0
                )

                # Limit content size for searching
                truncated_content = content[:50000] if len(content) > 50000 else content

                # Process definitions in batches to avoid blocking
                def_keys = list(all_definitions.keys())
                for j in range(0, len(def_keys), 10):  # Process 10 at a time
                    batch = def_keys[j:j+10]
                    for name in batch:
                        # Skip checking in definition file
                        if ':' not in name:  # Not an import
                            if name in truncated_content:
                                # Use simpler count for performance
                                all_usages[name] = all_usages.get(name, 0) + truncated_content.count(name)

            except asyncio.TimeoutError:
                logger.warning(f"Timeout reading {py_file}")
            except Exception:
                pass

            # Yield control periodically
            if i % 2 == 0:
                await asyncio.sleep(0)

        if progress_callback:
            await progress_callback(f"🧹 Analyzing unused items...")

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

        if progress_callback:
            await progress_callback(f"🧹 Checking for unreachable code...")

        # Check for unreachable code (analyze ALL files)
        for i, py_file in enumerate(py_files, 1):
            # More frequent progress updates
            if progress_callback:
                if i <= 20 or i % 10 == 0 or i == total_files:
                    await progress_callback(f"🧹 Checking unreachable code: {i}/{total_files} files...")
            try:
                # Add timeout for file reading
                content = await asyncio.wait_for(
                    asyncio.to_thread(py_file.read_text, encoding='utf-8'),
                    timeout=2.0
                )

                # Find code after return/raise/break/continue (with safer regex)
                # Use simpler pattern to avoid catastrophic backtracking
                unreachable_pattern = r'^\s*(return|raise|break|continue)[^\n]*\n\s+\S'
                try:
                    truncated_content = content[:50000] if len(content) > 50000 else content
                    for match in re.finditer(unreachable_pattern, truncated_content, re.MULTILINE):
                        line = content[:match.start()].count('\n') + 1
                        results['unreachable_code'].append({
                            'file': str(py_file),
                            'line': line + 1,
                            'confidence': 90
                        })
                except re.error:
                    logger.warning(f"Regex error checking unreachable code in {py_file}")

            except asyncio.TimeoutError:
                logger.warning(f"Timeout reading {py_file}")
            except Exception:
                pass

            # Yield control periodically
            if i % 3 == 0:
                await asyncio.sleep(0)

        if progress_callback:
            await progress_callback(f"🧹 Dead code analysis complete")

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