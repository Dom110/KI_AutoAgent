"""
Central Code Indexing Engine for KI_AutoAgent

Coordinates multiple indexing and analysis tools to build
comprehensive system understanding.
"""

import asyncio
import logging
import os
import time
import json
import re
import fnmatch
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from datetime import datetime, timedelta

from .tree_sitter_indexer import TreeSitterIndexer

logger = logging.getLogger(__name__)

class CodeIndexer:
    """
    Central code indexing engine with smart analysis depth detection

    Features:
    - Multi-language support
    - Cross-reference analysis
    - Performance metrics
    - Security analysis
    - Architecture extraction
    - Smart analysis depth based on project size and request type
    - Caching for repeated requests
    - Priority-based file selection
    """

    def __init__(self):
        self.tree_sitter = TreeSitterIndexer()
        self.index = {}
        self.cache = {}
        self.patterns = {}
        self.architecture = {}
        self.last_analysis_path = None
        self.last_analysis_time = None
        self.cached_results = None
        self.cache_validity = timedelta(minutes=15)  # Cache valid for 15 minutes

        # Default exclusion patterns (common directories/files to skip)
        self.default_exclude_patterns = {
            # Version control
            '.git', '.svn', '.hg', '.bzr',
            # Dependencies
            'node_modules', 'bower_components', 'jspm_packages',
            # Python
            '__pycache__', '*.pyc', '*.pyo', '*.pyd', '.Python',
            'venv', '.venv', 'env', '.env', 'ENV', 'pip-log.txt',
            'pip-delete-this-directory.txt', '.tox', '.coverage',
            '.pytest_cache', '.mypy_cache', '.ruff_cache',
            # JavaScript/TypeScript
            'dist', 'build', 'out', '.next', '.nuxt', '.cache',
            '*.log', 'npm-debug.log*', 'yarn-debug.log*',
            'yarn-error.log*', '.npm', '.yarn',
            # IDE
            '.vscode', '.idea', '*.swp', '*.swo', '*~', '.DS_Store',
            # Testing
            'coverage', 'htmlcov', '.nyc_output',
            # Documentation
            'docs/_build', 'site-packages',
            # Temporary files
            'tmp', 'temp', '*.tmp', '*.temp', '.tmp.*',
            # Build outputs
            'target', '*.egg-info', '*.egg', 'wheels',
            # VS Code extension specific
            '*.vsix', 'out/',
            # Other
            'vendor', 'third_party', 'external'
        }
        self.gitignore_patterns = set()

    def _load_gitignore(self, root_path: str) -> Set[str]:
        """
        Load patterns from .gitignore file if it exists
        """
        gitignore_path = os.path.join(root_path, '.gitignore')
        patterns = set()

        if os.path.exists(gitignore_path):
            logger.info(f"Loading .gitignore from {gitignore_path}")
            try:
                with open(gitignore_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        # Skip empty lines and comments
                        if line and not line.startswith('#'):
                            patterns.add(line)
                logger.info(f"Loaded {len(patterns)} patterns from .gitignore")
            except Exception as e:
                logger.warning(f"Failed to read .gitignore: {e}")
        else:
            logger.info("No .gitignore found, using default exclusion patterns")

        return patterns

    def _should_exclude_path(self, path: str, root_path: str) -> bool:
        """
        Check if a path should be excluded based on gitignore and default patterns
        """
        # Convert to relative path for pattern matching
        if os.path.isabs(path):
            try:
                rel_path = os.path.relpath(path, root_path)
            except ValueError:
                # Path is on different drive (Windows)
                return True
        else:
            rel_path = path

        # Check against gitignore patterns
        for pattern in self.gitignore_patterns:
            if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(os.path.basename(rel_path), pattern):
                return True

        # Check against default patterns
        for pattern in self.default_exclude_patterns:
            if '*' in pattern:
                # It's a glob pattern
                if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(os.path.basename(rel_path), pattern):
                    return True
            else:
                # It's a direct match
                parts = rel_path.split(os.sep)
                if pattern in parts or os.path.basename(rel_path) == pattern:
                    return True

        return False

    def _count_project_files(self, root_path: str) -> int:
        """
        Count actual project files (excluding gitignore and default patterns)
        """
        # Load gitignore patterns
        self.gitignore_patterns = self._load_gitignore(root_path)

        total_files = 0
        excluded_count = 0

        for root, dirs, files in os.walk(root_path):
            # Filter out excluded directories
            dirs_to_check = []
            for d in dirs:
                dir_path = os.path.join(root, d)
                if not self._should_exclude_path(dir_path, root_path):
                    dirs_to_check.append(d)
                else:
                    excluded_count += 1
            dirs[:] = dirs_to_check

            # Count non-excluded source files
            for f in files:
                if f.endswith(('.py', '.js', '.ts', '.jsx', '.tsx')):
                    file_path = os.path.join(root, f)
                    if not self._should_exclude_path(file_path, root_path):
                        total_files += 1
                    else:
                        excluded_count += 1

        logger.info(f"Project files: {total_files} to analyze, {excluded_count} excluded")
        return total_files


    async def build_full_index(self, root_path: str = '.', progress_callback=None, request_type: str = 'general') -> Dict:
        """
        Build complete system index with full analysis

        Args:
            root_path: Root directory to index
            progress_callback: Optional callback for progress updates
            request_type: Type of request (for logging purposes)

        Returns:
            Comprehensive system index
        """
        # Check cache first
        if self._is_cache_valid(root_path):
            logger.info("Using cached analysis results")
            if progress_callback:
                await progress_callback("📦 Using cached analysis (still fresh)")
            return self.cached_results

        # Count files to analyze
        file_count = self._count_project_files(root_path)
        logger.info(f"Starting FULL analysis of {file_count} project files")
        logger.info(f"Request type: {request_type}")

        # Phase 1: AST Indexing with exclusion patterns
        logger.info("Phase 1: AST Indexing with Tree-sitter")
        if progress_callback:
            await progress_callback(f"📂 Phase 1/6: Indexing {file_count} files (using .gitignore + defaults)...")

        # Let tree-sitter use our exclusion logic
        original_index_method = self.tree_sitter.index_codebase

        async def index_with_exclusions(path):
            """Wrapper to add exclusion logic to tree-sitter indexing"""
            result = await original_index_method(path)
            # Filter out excluded files
            filtered_files = {}
            for file_path, file_data in result.get('files', {}).items():
                if not self._should_exclude_path(file_path, root_path):
                    filtered_files[file_path] = file_data
            result['files'] = filtered_files
            logger.info(f"Indexed {len(filtered_files)} files after exclusions")
            return result

        self.tree_sitter.index_codebase = index_with_exclusions
        ast_index = await self.tree_sitter.index_codebase(root_path)
        self.tree_sitter.index_codebase = original_index_method  # Restore

        actual_files = len(ast_index.get('files', {}))
        if progress_callback:
            await progress_callback(f"📂 Phase 1/6: Indexed {actual_files} files successfully")

        # Phase 2: Cross-reference analysis (FULL - no limits)
        logger.info(f"Phase 2: Building cross-references for ALL {actual_files} files")
        if progress_callback:
            await progress_callback(f"🔗 Phase 2/6: Building cross-references for {actual_files} files...")
        cross_refs = await self._build_cross_references(ast_index)

        # Phase 3: Architecture extraction
        logger.info("Phase 3: Extracting architecture patterns")
        if progress_callback:
            await progress_callback("🏗️ Phase 3/6: Extracting architecture patterns...")
        architecture = await self._extract_architecture_patterns(ast_index)

        # Phase 4: Call graph construction
        logger.info("Phase 4: Building call graph")
        if progress_callback:
            await progress_callback("📊 Phase 4/6: Building call graph...")
        call_graph = await self._build_call_graph(ast_index, progress_callback)

        # Phase 5: Import graph
        logger.info("Phase 5: Building import graph")
        if progress_callback:
            await progress_callback("📦 Phase 5/6: Building import graph...")
        import_graph = await self._build_import_graph(ast_index)

        # Phase 6: Pattern detection
        logger.info("Phase 6: Detecting code patterns")
        if progress_callback:
            await progress_callback("🔍 Phase 6/6: Detecting code patterns...")
        patterns = await self._detect_code_patterns(ast_index)

        # Combine all indexes
        self.index = {
            'ast': ast_index,
            'cross_references': cross_refs,
            'architecture': architecture,
            'call_graph': call_graph,
            'import_graph': import_graph,
            'patterns': patterns,
            'statistics': self._calculate_statistics(ast_index)
        }

        logger.info(f"Index complete: {len(ast_index['files'])} files processed")

        # Cache the results
        self._cache_results(root_path, self.index)

        return self.index

    def _is_cache_valid(self, root_path: str) -> bool:
        """Check if cached results are still valid"""
        if not self.cached_results or self.last_analysis_path != root_path:
            return False

        if not self.last_analysis_time:
            return False

        age = datetime.now() - self.last_analysis_time
        return age < self.cache_validity

    def _cache_results(self, root_path: str, results: Dict):
        """Cache analysis results"""
        self.last_analysis_path = root_path
        self.last_analysis_time = datetime.now()
        self.cached_results = results
        logger.info(f"Cached analysis results for {root_path}")


    async def _build_cross_references(self, ast_index: Dict) -> Dict:
        """Build cross-reference index for symbols"""
        cross_refs = {
            'definitions': {},
            'references': {},
            'call_sites': {}
        }

        # Index all definitions
        for file_path, file_info in ast_index['files'].items():
            for func in file_info.get('functions', []):
                symbol = f"{file_path}:{func['name']}"
                cross_refs['definitions'][func['name']] = {
                    'type': 'function',
                    'file': file_path,
                    'line': func['line'],
                    'async': func.get('async', False)
                }

            for cls in file_info.get('classes', []):
                symbol = f"{file_path}:{cls['name']}"
                cross_refs['definitions'][cls['name']] = {
                    'type': 'class',
                    'file': file_path,
                    'line': cls['line'],
                    'methods': cls.get('methods', [])
                }

        # Limit reference search to avoid timeout - only process first 100 symbols
        # For large codebases, full reference search can take too long
        symbol_names = list(cross_refs['definitions'].keys())[:100]
        logger.info(f"Building references for {len(symbol_names)} symbols (limited from {len(cross_refs['definitions'])} total)")

        # Find references for limited set
        for symbol_name in symbol_names:
            usages = await self.tree_sitter.get_function_usages(symbol_name)
            cross_refs['references'][symbol_name] = usages

        return cross_refs

    async def _extract_architecture_patterns(self, ast_index: Dict) -> Dict:
        """Extract architectural patterns from code"""
        architecture = {
            'layers': {},
            'components': {},
            'patterns': [],
            'style': None
        }

        # Detect layers (presentation, business, data)
        for file_path in ast_index['files']:
            if 'api' in file_path or 'routes' in file_path or 'endpoints' in file_path:
                architecture['layers'].setdefault('presentation', []).append(file_path)
            elif 'service' in file_path or 'business' in file_path or 'agents' in file_path:
                architecture['layers'].setdefault('business', []).append(file_path)
            elif 'db' in file_path or 'repository' in file_path or 'model' in file_path:
                architecture['layers'].setdefault('data', []).append(file_path)
            elif 'utils' in file_path or 'helpers' in file_path:
                architecture['layers'].setdefault('utilities', []).append(file_path)

        # Detect architectural patterns
        patterns_found = []

        # Check for MVC pattern
        if ('controller' in str(ast_index['files']) or 'routes' in str(ast_index['files'])) and \
           ('model' in str(ast_index['files'])) and \
           ('view' in str(ast_index['files']) or 'template' in str(ast_index['files'])):
            patterns_found.append('MVC')

        # Check for Repository pattern
        if 'repository' in str(ast_index['files']):
            patterns_found.append('Repository')

        # Check for Service pattern
        if 'service' in str(ast_index['files']):
            patterns_found.append('Service Layer')

        # Check for Factory pattern
        for file_info in ast_index['files'].values():
            for func in file_info.get('functions', []):
                if 'create' in func['name'].lower() or 'factory' in func['name'].lower():
                    patterns_found.append('Factory')
                    break

        # Check for Singleton pattern
        for file_info in ast_index['files'].values():
            content = file_info.get('content', '')
            if '__instance' in content or '_instance' in content:
                patterns_found.append('Singleton')
                break

        architecture['patterns'] = list(set(patterns_found))

        # Determine architectural style
        if ast_index.get('api_endpoints'):
            if 'graphql' in str(ast_index['api_endpoints']).lower():
                architecture['style'] = 'GraphQL API'
            else:
                architecture['style'] = 'REST API'

        # Extract components
        components = {}
        for file_path, file_info in ast_index['files'].items():
            if file_info.get('classes'):
                for cls in file_info['classes']:
                    component_type = self._classify_component(cls['name'], file_path)
                    components.setdefault(component_type, []).append({
                        'name': cls['name'],
                        'file': file_path,
                        'methods': len(cls.get('methods', []))
                    })

        architecture['components'] = components

        return architecture

    async def _build_call_graph(self, ast_index: Dict, progress_callback=None) -> Dict:
        """Build function call graph for ALL files with progress tracking"""
        call_graph = {}
        total_files = len(ast_index['files'])

        logger.info(f"Building call graph for ALL {total_files} files")

        # Create a set of all function names for reference
        all_functions = set()
        for file_info in ast_index['files'].values():
            for func in file_info.get('functions', []):
                all_functions.add(func['name'])

        logger.info(f"Found {len(all_functions)} unique function names")

        # Process each file with progress updates
        processed = 0
        for file_path, file_info in ast_index['files'].items():
            processed += 1

            # Update progress every 10 files or for small projects every file
            if progress_callback and (processed % 10 == 0 or total_files < 50):
                await progress_callback(f"📊 Phase 4/6: Building call graph ({processed}/{total_files} files)...")

            for func in file_info.get('functions', []):
                func_name = func['name']
                content = file_info.get('content', '')

                # Find function calls in content
                calls = []
                for other_name in all_functions:
                    if other_name != func_name and f"{other_name}(" in content:
                        calls.append(other_name)

                if calls:
                    call_graph[f"{file_path}:{func_name}"] = calls

        logger.info(f"Call graph complete with {len(call_graph)} entries from {total_files} files")
        return call_graph

    async def _build_import_graph(self, ast_index: Dict) -> Dict:
        """Build module import graph"""
        import_graph = {}

        for file_path, file_info in ast_index['files'].items():
            imports = []

            for imp in file_info.get('imports', []):
                module = imp.get('module', '')
                name = imp.get('name', '')

                if module:
                    imports.append(module)
                if name:
                    imports.append(f"{module}.{name}" if module else name)

            if imports:
                import_graph[file_path] = list(set(imports))

        return import_graph

    async def _detect_code_patterns(self, ast_index: Dict) -> Dict:
        """Detect common code patterns and anti-patterns"""
        patterns = {
            'design_patterns': [],
            'anti_patterns': [],
            'code_smells': [],
            'best_practices': [],
            'performance_issues': []
        }

        for file_path, file_info in ast_index['files'].items():
            content = file_info.get('content', '')

            # Detect anti-patterns
            if 'except:' in content or 'except Exception:' in content:
                patterns['anti_patterns'].append({
                    'type': 'Broad exception handling',
                    'file': file_path,
                    'severity': 'medium'
                })

            if 'global ' in content:
                patterns['code_smells'].append({
                    'type': 'Global variable usage',
                    'file': file_path,
                    'severity': 'low'
                })

            # Detect nested loops (performance issue)
            if content.count('for ') > 2:
                loop_depth = self._check_loop_nesting(content)
                if loop_depth > 2:
                    patterns['performance_issues'].append({
                        'type': f'Deeply nested loops (depth: {loop_depth})',
                        'file': file_path,
                        'severity': 'high'
                    })

            # Check for async best practices
            if 'async def' in content:
                if 'time.sleep' in content:
                    patterns['anti_patterns'].append({
                        'type': 'Blocking sleep in async function',
                        'file': file_path,
                        'severity': 'high'
                    })

                if 'await asyncio.gather' in content:
                    patterns['best_practices'].append({
                        'type': 'Concurrent execution with gather',
                        'file': file_path
                    })

            # Detect design patterns
            for cls in file_info.get('classes', []):
                class_name = cls['name']

                # Observer pattern
                if 'observer' in class_name.lower() or 'listener' in class_name.lower():
                    patterns['design_patterns'].append({
                        'type': 'Observer',
                        'class': class_name,
                        'file': file_path
                    })

                # Strategy pattern
                if 'strategy' in class_name.lower():
                    patterns['design_patterns'].append({
                        'type': 'Strategy',
                        'class': class_name,
                        'file': file_path
                    })

                # Decorator pattern
                for method in cls.get('methods', []):
                    if method['name'].startswith('wrap_') or method['name'] == '__call__':
                        patterns['design_patterns'].append({
                            'type': 'Decorator',
                            'class': class_name,
                            'file': file_path
                        })
                        break

        return patterns

    def _classify_component(self, class_name: str, file_path: str) -> str:
        """Classify component type based on name and location"""
        class_lower = class_name.lower()
        path_lower = file_path.lower()

        if 'agent' in class_lower:
            return 'agent'
        elif 'service' in class_lower:
            return 'service'
        elif 'manager' in class_lower:
            return 'manager'
        elif 'controller' in class_lower or 'handler' in class_lower:
            return 'controller'
        elif 'repository' in class_lower or 'dao' in class_lower:
            return 'repository'
        elif 'model' in class_lower or 'entity' in class_lower:
            return 'model'
        elif 'view' in path_lower or 'ui' in path_lower:
            return 'view'
        elif 'util' in class_lower or 'helper' in class_lower:
            return 'utility'
        else:
            return 'other'

    def _check_loop_nesting(self, content: str) -> int:
        """Check maximum loop nesting depth"""
        lines = content.split('\n')
        max_depth = 0
        current_depth = 0

        for line in lines:
            if 'for ' in line or 'while ' in line:
                # Count indentation to estimate nesting
                indent = len(line) - len(line.lstrip())
                depth = indent // 4 + 1
                max_depth = max(max_depth, depth)

        return max_depth

    def _calculate_statistics(self, ast_index: Dict) -> Dict:
        """Calculate comprehensive statistics"""
        stats = self.tree_sitter.get_statistics()

        # Add more detailed stats
        stats.update({
            'complexity': self._calculate_complexity(ast_index),
            'coupling': self._calculate_coupling(ast_index),
            'cohesion': self._calculate_cohesion(ast_index)
        })

        return stats

    def _calculate_complexity(self, ast_index: Dict) -> Dict:
        """Calculate code complexity metrics"""
        complexity = {
            'cyclomatic': 0,
            'cognitive': 0,
            'halstead': 0
        }

        for file_info in ast_index['files'].values():
            content = file_info.get('content', '')

            # Simplified cyclomatic complexity
            complexity['cyclomatic'] += content.count('if ') + content.count('elif ') + \
                                       content.count('for ') + content.count('while ') + \
                                       content.count('except ') + 1

        complexity['average'] = complexity['cyclomatic'] / max(len(ast_index['files']), 1)

        return complexity

    def _calculate_coupling(self, ast_index: Dict) -> Dict:
        """Calculate coupling metrics"""
        coupling = {
            'afferent': {},  # Incoming dependencies
            'efferent': {}   # Outgoing dependencies
        }

        for file_path, file_info in ast_index['files'].items():
            imports = file_info.get('imports', [])
            coupling['efferent'][file_path] = len(imports)

            # Count incoming (who imports this file)
            for imp in imports:
                module = imp.get('module', '')
                if module in ast_index['files']:
                    coupling['afferent'].setdefault(module, 0)
                    coupling['afferent'][module] += 1

        return coupling

    def _calculate_cohesion(self, ast_index: Dict) -> float:
        """Calculate cohesion metric"""
        # Simplified cohesion: ratio of internal calls to total calls
        internal_calls = 0
        total_calls = 0

        for file_path, file_info in ast_index['files'].items():
            functions = file_info.get('functions', [])
            total_calls += len(functions)

            # Check how many functions call each other within the same file
            for func in functions:
                # Simplified check
                internal_calls += 1 if len(functions) > 1 else 0

        return internal_calls / max(total_calls, 1)

    async def search(self, query: str) -> List[Dict]:
        """Search indexed codebase"""
        return await self.tree_sitter.search_pattern(query)

    async def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get detailed information about a symbol"""
        if not self.index:
            return None

        cross_refs = self.index.get('cross_references', {})
        definitions = cross_refs.get('definitions', {})

        if symbol in definitions:
            info = definitions[symbol].copy()
            info['references'] = cross_refs.get('references', {}).get(symbol, [])
            return info

        return None

    async def suggest_improvements(self) -> List[Dict]:
        """Suggest codebase improvements based on analysis"""
        if not self.index:
            return []

        improvements = []
        patterns = self.index.get('patterns', {})

        # Check for anti-patterns
        for anti_pattern in patterns.get('anti_patterns', []):
            improvements.append({
                'type': 'anti_pattern',
                'priority': 'high' if anti_pattern['severity'] == 'high' else 'medium',
                'title': f"Fix {anti_pattern['type']}",
                'file': anti_pattern['file'],
                'description': f"Anti-pattern detected: {anti_pattern['type']}"
            })

        # Check for performance issues
        for perf_issue in patterns.get('performance_issues', []):
            improvements.append({
                'type': 'performance',
                'priority': 'high' if perf_issue['severity'] == 'high' else 'medium',
                'title': f"Optimize {perf_issue['type']}",
                'file': perf_issue['file'],
                'description': f"Performance issue: {perf_issue['type']}"
            })

        # Check complexity
        stats = self.index.get('statistics', {})
        complexity = stats.get('complexity', {})

        if complexity.get('average', 0) > 10:
            improvements.append({
                'type': 'complexity',
                'priority': 'medium',
                'title': 'Reduce code complexity',
                'description': f"Average cyclomatic complexity is {complexity.get('average', 0):.1f} (should be < 10)"
            })

        return improvements