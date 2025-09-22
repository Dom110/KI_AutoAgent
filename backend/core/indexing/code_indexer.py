"""
Central Code Indexing Engine for KI_AutoAgent

Coordinates multiple indexing and analysis tools to build
comprehensive system understanding.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from .tree_sitter_indexer import TreeSitterIndexer

logger = logging.getLogger(__name__)

class CodeIndexer:
    """
    Central code indexing engine that coordinates all analysis tools

    Features:
    - Multi-language support
    - Cross-reference analysis
    - Performance metrics
    - Security analysis
    - Architecture extraction
    """

    def __init__(self):
        self.tree_sitter = TreeSitterIndexer()
        self.index = {}
        self.cache = {}
        self.patterns = {}
        self.architecture = {}

    async def build_full_index(self, root_path: str = '.') -> Dict:
        """
        Build complete system index

        Args:
            root_path: Root directory to index

        Returns:
            Comprehensive system index
        """
        logger.info("Building complete system index...")

        # Phase 1: AST Indexing
        logger.info("Phase 1: AST Indexing with Tree-sitter")
        ast_index = await self.tree_sitter.index_codebase(root_path)

        # Phase 2: Cross-reference analysis
        logger.info("Phase 2: Building cross-references")
        cross_refs = await self._build_cross_references(ast_index)

        # Phase 3: Architecture extraction
        logger.info("Phase 3: Extracting architecture patterns")
        architecture = await self._extract_architecture_patterns(ast_index)

        # Phase 4: Call graph construction
        logger.info("Phase 4: Building call graph")
        call_graph = await self._build_call_graph(ast_index)

        # Phase 5: Import graph
        logger.info("Phase 5: Building import graph")
        import_graph = await self._build_import_graph(ast_index)

        # Phase 6: Pattern detection
        logger.info("Phase 6: Detecting code patterns")
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
        return self.index

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

        # Find all references
        for symbol_name in cross_refs['definitions'].keys():
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

    async def _build_call_graph(self, ast_index: Dict) -> Dict:
        """Build function call graph"""
        call_graph = {}

        for file_path, file_info in ast_index['files'].items():
            for func in file_info.get('functions', []):
                func_name = func['name']
                content = file_info.get('content', '')

                # Find function calls within this function
                # Simplified - in production would use proper AST walking
                calls = []

                for other_func in ast_index['functions'].keys():
                    other_name = other_func.split(':')[-1]
                    if other_name != func_name and other_name in content:
                        calls.append(other_name)

                if calls:
                    call_graph[f"{file_path}:{func_name}"] = calls

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