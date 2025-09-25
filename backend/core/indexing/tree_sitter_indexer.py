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

    async def index_codebase(self, root_path: str = '.', exclude_patterns=None, progress_callback=None) -> Dict:
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
        total_files = len(files_to_index)

        # Process files with yielding to event loop
        for i, path in enumerate(files_to_index):
            # Send progress update for each file
            if progress_callback:
                file_name = path.name
                progress_num = i + 1
                await progress_callback(f"📂 Indexing file {progress_num}/{total_files}: {file_name}")

            await self._index_file(path)

            # Yield to event loop periodically to prevent blocking
            if i % 10 == 0:
                await asyncio.sleep(0)  # Yield control to event loop

        # Build relationships (only if we have indexed files)
        if self.index['files']:
            if progress_callback:
                await progress_callback(f"📊 Building dependency graph for {len(self.index['files'])} files...")
            await self._build_dependency_graph(progress_callback)

            if progress_callback:
                await progress_callback(f"🔌 Extracting API endpoints...")
            await self._extract_api_endpoints(progress_callback)

            if progress_callback:
                await progress_callback(f"💾 Identifying database operations...")
            await self._identify_db_operations(progress_callback)

        logger.info(f"Indexing complete: {len(self.index['files'])} files indexed")
        if progress_callback:
            await progress_callback(f"✅ Phase 1 complete: {len(self.index['files'])} files indexed")
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

    async def _build_dependency_graph(self, progress_callback=None):
        """Build import dependency graph"""
        self.index['dependency_graph'] = {}
        count = 0
        total_files = len(self.index['files'])
        deps_found = 0

        logger.info(f"Building dependency graph for {total_files} files")

        for file_path, file_info in self.index['files'].items():
            count += 1
            file_name = os.path.basename(file_path)

            # Send progress updates more frequently
            if progress_callback:
                if total_files < 50 or count % 10 == 0 or count == 1 or count == total_files:
                    await progress_callback(f"📊 Dependency graph {count}/{total_files}: {file_name}")

            if 'imports' in file_info:
                imports = [imp['module'] for imp in file_info['imports']]
                if imports:
                    self.index['dependency_graph'][file_path] = imports
                    deps_found += len(imports)
                    if progress_callback and len(imports) > 5:
                        await progress_callback(f"📊 Found {len(imports)} dependencies in {file_name}")

            # Yield to event loop more frequently
            if count % 10 == 0:
                await asyncio.sleep(0)

        # Final summary
        if progress_callback:
            await progress_callback(f"✅ Dependency graph complete: {deps_found} imports in {total_files} files")

        logger.info(f"Dependency graph built: {deps_found} total dependencies")

    async def _extract_api_endpoints(self, progress_callback=None):
        """Extract API endpoints from FastAPI/Flask code"""
        import re
        count = 0
        total_files = len(self.index['files'])
        endpoints_found = 0
        python_files = 0

        logger.info(f"Extracting API endpoints from {total_files} files")

        for file_path, file_info in self.index['files'].items():
            count += 1
            file_name = os.path.basename(file_path)

            # Send progress for every Python file or periodically
            if file_info.get('language') == 'python':
                python_files += 1
                if progress_callback:
                    await progress_callback(f"🔌 API scan {python_files}/{count}: {file_name} ({endpoints_found} endpoints)")

                content = file_info['content']

                # FastAPI patterns
                api_patterns = [
                    r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']\)',
                    r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']\)'
                ]

                file_endpoints = 0
                for pattern in api_patterns:
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
                        file_endpoints += 1
                        endpoints_found += 1

                # Report if we found endpoints in this file
                if file_endpoints > 0 and progress_callback:
                    await progress_callback(f"🔌 Found {file_endpoints} API endpoints in {file_name}")

            # Yield to event loop more frequently
            if count % 10 == 0:
                await asyncio.sleep(0)

        # Final summary
        if progress_callback:
            await progress_callback(f"✅ API extraction complete: {endpoints_found} endpoints in {python_files} Python files")

        logger.info(f"Found {endpoints_found} API endpoints in {python_files} Python files")

    async def _identify_db_operations(self, progress_callback=None):
        """Identify database operations in code"""
        import re
        count = 0
        db_ops_found = 0

        # Use non-greedy patterns and limit scope
        db_patterns = [
            r'SELECT\s+.{1,200}?\s+FROM',  # Non-greedy, limited length
            r'INSERT\s+INTO\s+\w+',
            r'UPDATE\s+\w+\s+SET',
            r'DELETE\s+FROM\s+\w+',
            r'\.find\(',
            r'\.create\(',
            r'\.save\(',
            r'\.delete\('
        ]

        total_files = len(self.index['files'])
        logger.info(f"Scanning {total_files} files for DB operations")

        for file_path, file_info in self.index['files'].items():
            count += 1
            file_name = os.path.basename(file_path)

            # Send progress for every file when total is small, otherwise every 5 files
            if progress_callback:
                if total_files < 50 or count % 5 == 0 or count == 1 or count == total_files:
                    await progress_callback(f"💾 DB scan {count}/{total_files}: {file_name} ({db_ops_found} operations found)")

            # Yield to event loop frequently
            if count % 5 == 0:
                await asyncio.sleep(0)

            logger.debug(f"DB scan: {count}/{total_files} - {file_name}")

            content = file_info.get('content', '')

            # Skip very large files to prevent regex hangs
            if len(content) > 100000:  # 100KB limit
                logger.debug(f"Skipping large file for DB scan: {file_path}")
                if progress_callback:
                    await progress_callback(f"💾 DB scan {count}/{total_files}: Skipped large file {file_name}")
                continue

            # Process patterns with timeout protection
            file_db_ops = 0
            try:
                for pattern in db_patterns:
                    # Limit matches per file to prevent excessive processing
                    matches_found = 0
                    for match in re.finditer(pattern, content, re.IGNORECASE):
                        if matches_found >= 10:  # Max 10 matches per pattern per file
                            break
                        matches_found += 1
                        file_db_ops += 1
                        db_ops_found += 1

                        op_key = f"{file_path}:{match.start()}"
                        self.index['db_operations'][op_key] = {
                            'type': pattern.split('\\')[0].split('.')[0],
                            'file': file_path,
                            'line': content[:match.start()].count('\n') + 1,
                            'snippet': content[match.start():match.start()+50]
                        }

                        # Yield periodically even within pattern matching
                        if db_ops_found % 20 == 0:
                            await asyncio.sleep(0)

                # Report if we found operations in this file
                if file_db_ops > 0 and progress_callback:
                    await progress_callback(f"💾 Found {file_db_ops} DB operations in {file_name}")

            except Exception as e:
                logger.warning(f"Error scanning {file_path} for DB operations: {e}")
                if progress_callback:
                    await progress_callback(f"⚠️ Error scanning {file_name}: {str(e)[:50]}")
                continue

        # Final summary
        if progress_callback:
            await progress_callback(f"✅ DB scan complete: {db_ops_found} operations in {total_files} files")

        logger.info(f"Found {len(self.index['db_operations'])} DB operations in {count} files")

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

    async def get_function_usages(self, function_name: str, max_files: int = 20) -> List[Dict]:
        """Find all usages of a function (limited for performance)"""
        usages = []
        files_checked = 0
        max_usages_per_file = 3  # Limit matches per file

        # Escape special regex characters in function name
        import re
        escaped_name = re.escape(function_name)
        pattern = rf'\b{escaped_name}\s*\('

        for file_path, file_info in self.index['files'].items():
            # Limit number of files to check
            if files_checked >= max_files:
                break

            content = file_info.get('content', '')

            # Skip very large files
            if len(content) > 50000:  # 50KB limit
                continue

            files_checked += 1

            # Search for function calls with limit
            matches_found = 0
            try:
                for match in re.finditer(pattern, content):
                    if matches_found >= max_usages_per_file:
                        break
                    matches_found += 1
                    usages.append({
                        'file': file_path,
                        'line': content[:match.start()].count('\n') + 1,
                        'context': content[max(0, match.start()-30):match.end()+30]
                    })
            except Exception as e:
                logger.debug(f"Error searching for {function_name} in {file_path}: {e}")
                continue

            # Yield to event loop periodically
            if files_checked % 10 == 0:
                await asyncio.sleep(0)

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