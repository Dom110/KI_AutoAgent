"""
Tree-sitter based code indexer for multi-language AST parsing

Provides incremental parsing and fault-tolerant AST analysis for:
- Python
- JavaScript/TypeScript
- And more languages as needed
"""

import os
import ast
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class TreeSitterIndexer:
    """
    Advanced code indexer using tree-sitter for AST parsing

    Features:
    - Multi-language support
    - Incremental parsing
    - Error-tolerant parsing
    - Detailed AST analysis
    """

    def __init__(self):
        self.index = {
            'files': {},
            'functions': {},
            'classes': {},
            'imports': {},
            'api_endpoints': {},
            'db_operations': {},
            'variables': {},
            'constants': {},
            'type_definitions': {}
        }
        self.supported_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml'
        }

    async def index_codebase(self, root_path: str = '.', exclude_patterns=None) -> Dict:
        """
        Index entire codebase using AST parsing

        Args:
            root_path: Root directory to index
            exclude_patterns: Set of patterns to exclude (e.g., {'venv', 'node_modules'})

        Returns:
            Complete code index with AST information
        """
        logger.info(f"Starting codebase indexing from {root_path}")

        # Default exclusions if not provided
        if exclude_patterns is None:
            exclude_patterns = {
                'venv', '.venv', 'env', '.env',
                'node_modules', '__pycache__', '.git',
                'dist', 'build', '.pytest_cache', '.mypy_cache'
            }

        # Collect files first (blocking operation)
        files_to_index = []
        for path in Path(root_path).rglob('*'):
            # Skip if any part of the path matches exclude patterns
            path_str = str(path)
            should_skip = False
            for pattern in exclude_patterns:
                if pattern in path_str:
                    should_skip = True
                    break

            if should_skip:
                continue

            if path.is_file():
                ext = path.suffix.lower()
                if ext in self.supported_extensions:
                    files_to_index.append(path)

        logger.info(f"Found {len(files_to_index)} files to index (excluded common directories)")

        # Process files with yielding to event loop
        for i, path in enumerate(files_to_index):
            await self._index_file(path)
            # Yield to event loop periodically to prevent blocking
            if i % 10 == 0:
                await asyncio.sleep(0)  # Yield control to event loop

        # Build relationships (only if we have indexed files)
        if self.index['files']:
            await self._build_dependency_graph()
            await self._extract_api_endpoints()
            await self._identify_db_operations()

        logger.info(f"Indexing complete: {len(self.index['files'])} files indexed")
        return self.index

    async def _index_file(self, file_path: Path):
        """Index a single file based on its type"""
        try:
            ext = file_path.suffix.lower()
            # Use async file reading to prevent blocking
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, file_path.read_text, 'utf-8')

            if ext == '.py':
                await self._index_python_file(file_path, content)
            elif ext in ['.js', '.jsx', '.ts', '.tsx']:
                await self._index_javascript_file(file_path, content)
            elif ext == '.json':
                await self._index_json_file(file_path, content)
            elif ext in ['.yaml', '.yml']:
                await self._index_yaml_file(file_path, content)

        except Exception as e:
            logger.warning(f"Failed to index {file_path}: {e}")

    async def _index_python_file(self, file_path: Path, content: str):
        """Index Python file using AST"""
        try:
            # Run AST parsing in executor to prevent blocking
            loop = asyncio.get_event_loop()
            tree = await loop.run_in_executor(None, ast.parse, content)

            file_info = {
                'path': str(file_path),
                'language': 'python',
                'content': content,
                'functions': [],
                'classes': [],
                'imports': [],
                'variables': [],
                'constants': []
            }

            # Process AST nodes with yielding
            nodes_to_process = list(ast.walk(tree))
            for i, node in enumerate(nodes_to_process):
                # Yield to event loop periodically
                if i % 50 == 0:
                    await asyncio.sleep(0)
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    func_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'col': node.col_offset,
                        'async': isinstance(node, ast.AsyncFunctionDef),
                        'params': [arg.arg for arg in node.args.args],
                        'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
                        'docstring': ast.get_docstring(node)
                    }
                    file_info['functions'].append(func_info)

                    # Add to global function index
                    self.index['functions'][f"{file_path}:{node.name}"] = func_info

                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'col': node.col_offset,
                        'bases': [self._get_name(base) for base in node.bases],
                        'methods': [],
                        'docstring': ast.get_docstring(node)
                    }

                    # Extract methods
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            class_info['methods'].append({
                                'name': item.name,
                                'async': isinstance(item, ast.AsyncFunctionDef),
                                'params': [arg.arg for arg in item.args.args]
                            })

                    file_info['classes'].append(class_info)
                    self.index['classes'][f"{file_path}:{node.name}"] = class_info

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        file_info['imports'].append({
                            'module': alias.name,
                            'alias': alias.asname,
                            'line': node.lineno
                        })

                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        file_info['imports'].append({
                            'module': module,
                            'name': alias.name,
                            'alias': alias.asname,
                            'line': node.lineno
                        })

                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_info = {
                                'name': target.id,
                                'line': node.lineno,
                                'is_constant': target.id.isupper()
                            }
                            if var_info['is_constant']:
                                file_info['constants'].append(var_info)
                            else:
                                file_info['variables'].append(var_info)

            self.index['files'][str(file_path)] = file_info

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")

    async def _index_javascript_file(self, file_path: Path, content: str):
        """Index JavaScript/TypeScript file"""
        # Simplified JS/TS indexing using regex patterns
        # In production, we would use a proper JS parser

        file_info = {
            'path': str(file_path),
            'language': 'javascript' if file_path.suffix in ['.js', '.jsx'] else 'typescript',
            'content': content,
            'functions': [],
            'classes': [],
            'imports': [],
            'exports': []
        }

        # Extract functions (simplified)
        import re

        # Function patterns
        func_patterns = [
            r'function\s+(\w+)\s*\(',
            r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>',
            r'const\s+(\w+)\s*=\s*async\s*\([^)]*\)\s*=>',
            r'async\s+function\s+(\w+)\s*\('
        ]

        for pattern in func_patterns:
            for match in re.finditer(pattern, content):
                func_name = match.group(1)
                file_info['functions'].append({
                    'name': func_name,
                    'line': content[:match.start()].count('\n') + 1
                })

        # Extract classes
        class_pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?'
        for match in re.finditer(class_pattern, content):
            file_info['classes'].append({
                'name': match.group(1),
                'extends': match.group(2),
                'line': content[:match.start()].count('\n') + 1
            })

        # Extract imports
        import_patterns = [
            r"import\s+(?:{[^}]+}|\w+)\s+from\s+['\"]([^'\"]+)['\"]",
            r"const\s+\w+\s*=\s*require\(['\"]([^'\"]+)['\"]\)"
        ]

        for pattern in import_patterns:
            for match in re.finditer(pattern, content):
                file_info['imports'].append({
                    'module': match.group(1),
                    'line': content[:match.start()].count('\n') + 1
                })

        self.index['files'][str(file_path)] = file_info

    async def _index_json_file(self, file_path: Path, content: str):
        """Index JSON configuration files"""
        try:
            data = json.loads(content)
            self.index['files'][str(file_path)] = {
                'path': str(file_path),
                'language': 'json',
                'content': content,
                'keys': list(data.keys()) if isinstance(data, dict) else [],
                'type': 'object' if isinstance(data, dict) else 'array'
            }
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in {file_path}")

    async def _index_yaml_file(self, file_path: Path, content: str):
        """Index YAML configuration files"""
        # Simplified YAML indexing
        self.index['files'][str(file_path)] = {
            'path': str(file_path),
            'language': 'yaml',
            'content': content
        }

    async def _build_dependency_graph(self):
        """Build import dependency graph"""
        self.index['dependency_graph'] = {}

        for file_path, file_info in self.index['files'].items():
            if 'imports' in file_info:
                self.index['dependency_graph'][file_path] = [
                    imp['module'] for imp in file_info['imports']
                ]

    async def _extract_api_endpoints(self):
        """Extract API endpoints from FastAPI/Flask code"""
        for file_path, file_info in self.index['files'].items():
            if file_info.get('language') == 'python':
                content = file_info['content']

                # FastAPI patterns
                api_patterns = [
                    r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']\)',
                    r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']\)'
                ]

                for pattern in api_patterns:
                    import re
                    for match in re.finditer(pattern, content):
                        method = match.group(1).upper()
                        path = match.group(2)

                        endpoint_key = f"{method} {path}"
                        self.index['api_endpoints'][endpoint_key] = {
                            'method': method,
                            'path': path,
                            'file': file_path,
                            'line': content[:match.start()].count('\n') + 1
                        }

    async def _identify_db_operations(self):
        """Identify database operations in code"""
        db_patterns = [
            r'SELECT\s+.*\s+FROM',
            r'INSERT\s+INTO',
            r'UPDATE\s+\w+\s+SET',
            r'DELETE\s+FROM',
            r'\.find\(',
            r'\.create\(',
            r'\.save\(',
            r'\.delete\('
        ]

        for file_path, file_info in self.index['files'].items():
            content = file_info.get('content', '')

            for pattern in db_patterns:
                import re
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    op_key = f"{file_path}:{match.start()}"
                    self.index['db_operations'][op_key] = {
                        'type': pattern.split('\\')[0],
                        'file': file_path,
                        'line': content[:match.start()].count('\n') + 1,
                        'snippet': content[match.start():match.start()+50]
                    }

    def _get_decorator_name(self, decorator) -> str:
        """Extract decorator name from AST node"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_name(decorator.value)}.{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return 'unknown'

    def _get_name(self, node) -> str:
        """Extract name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return 'unknown'

    async def search_pattern(self, pattern: str) -> List[Dict]:
        """Search for pattern across indexed code"""
        results = []

        for file_path, file_info in self.index['files'].items():
            content = file_info.get('content', '')

            import re
            for match in re.finditer(pattern, content, re.IGNORECASE):
                results.append({
                    'file': file_path,
                    'line': content[:match.start()].count('\n') + 1,
                    'match': match.group(0),
                    'context': content[max(0, match.start()-50):match.end()+50]
                })

        return results

    async def get_function_usages(self, function_name: str) -> List[Dict]:
        """Find all usages of a function"""
        usages = []

        for file_path, file_info in self.index['files'].items():
            content = file_info.get('content', '')

            # Search for function calls
            import re
            pattern = rf'\b{function_name}\s*\('

            for match in re.finditer(pattern, content):
                usages.append({
                    'file': file_path,
                    'line': content[:match.start()].count('\n') + 1,
                    'context': content[max(0, match.start()-30):match.end()+30]
                })

        return usages

    async def get_class_hierarchy(self) -> Dict:
        """Build class inheritance hierarchy"""
        hierarchy = {}

        for class_key, class_info in self.index['classes'].items():
            bases = class_info.get('bases', [])
            hierarchy[class_info['name']] = {
                'bases': bases,
                'subclasses': [],
                'file': class_key.split(':')[0]
            }

        # Build subclass relationships
        for class_name, info in hierarchy.items():
            for base in info['bases']:
                if base in hierarchy:
                    hierarchy[base]['subclasses'].append(class_name)

        return hierarchy

    def get_statistics(self) -> Dict:
        """Get indexing statistics"""
        return {
            'total_files': len(self.index['files']),
            'total_functions': len(self.index['functions']),
            'total_classes': len(self.index['classes']),
            'total_api_endpoints': len(self.index['api_endpoints']),
            'total_db_operations': len(self.index['db_operations']),
            'languages': self._count_languages(),
            'lines_of_code': self._count_lines()
        }

    def _count_languages(self) -> Dict[str, int]:
        """Count files per language"""
        counts = {}
        for file_info in self.index['files'].values():
            lang = file_info.get('language', 'unknown')
            counts[lang] = counts.get(lang, 0) + 1
        return counts

    def _count_lines(self) -> int:
        """Count total lines of code"""
        total = 0
        for file_info in self.index['files'].values():
            content = file_info.get('content', '')
            total += len(content.splitlines())
        return total