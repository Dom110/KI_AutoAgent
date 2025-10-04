"""
Code Indexer - Orchestrates file indexing and builds comprehensive code index
"""

import os
import asyncio
from typing import Dict, List, Any, Callable, Optional
from pathlib import Path
import logging

from .tree_sitter_indexer import TreeSitterIndexer

logger = logging.getLogger(__name__)


class CodeIndexer:
    """
    Orchestrates code indexing across the entire project
    Builds comprehensive index with AST, functions, classes, and imports
    """

    def __init__(self):
        self.tree_sitter = TreeSitterIndexer()
        self.excluded_dirs = {
            'node_modules', 'venv', '__pycache__', '.git',
            'dist', 'build', '.vscode', '.idea', 'coverage'
        }
        self.excluded_extensions = {'.pyc', '.pyo', '.so', '.dylib'}

    async def build_full_index(
        self,
        root_path: str,
        progress_callback: Optional[Callable] = None,
        request_type: str = 'general'
    ) -> Dict[str, Any]:
        """
        Build comprehensive index of entire codebase

        Args:
            root_path: Root directory to index
            progress_callback: Optional callback for progress updates
            request_type: Type of analysis (general, infrastructure, etc.)

        Returns:
            {
                'ast': {'files': {file_path: {functions, classes, imports, calls}}},
                'import_graph': {file: [dependencies]},
                'statistics': {total_files, total_functions, total_classes, ...}
            }
        """
        logger.info(f"Starting full code indexing for: {root_path}")
        if progress_callback:
            await progress_callback("📂 Scanning project files...")

        # Find all Python files
        python_files = self._find_python_files(root_path)
        total_files = len(python_files)

        logger.info(f"Found {total_files} Python files to index")

        # Index all files
        ast_data = {}
        import_graph = {}
        all_functions = []
        all_classes = []

        for i, file_path in enumerate(python_files):
            if progress_callback and i % 10 == 0:
                await progress_callback(f"📂 Indexing file {i + 1}/{total_files}: {os.path.basename(file_path)}")

            file_data = await self.tree_sitter.index_file(file_path)
            relative_path = os.path.relpath(file_path, root_path)

            ast_data[relative_path] = file_data

            # Build import graph
            imports = [imp.get('module', '') for imp in file_data.get('imports', [])]
            import_graph[relative_path] = imports

            # Collect all functions and classes
            for func in file_data.get('functions', []):
                func['file'] = relative_path
                all_functions.append(func)

            for cls in file_data.get('classes', []):
                cls['file'] = relative_path
                all_classes.append(cls)

        # Calculate statistics
        statistics = {
            'total_files': total_files,
            'total_functions': len(all_functions),
            'total_classes': len(all_classes),
            'total_imports': sum(len(imports) for imports in import_graph.values()),
            'lines_of_code': self._count_total_lines(python_files)
        }

        logger.info(f"Indexing complete: {statistics}")

        return {
            'ast': {'files': ast_data},
            'import_graph': import_graph,
            'statistics': statistics,
            'all_functions': all_functions,
            'all_classes': all_classes
        }

    def _find_python_files(self, root_path: str) -> List[str]:
        """Find all Python files in the project"""
        python_files = []

        for root, dirs, files in os.walk(root_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    python_files.append(file_path)

        return python_files

    def _count_total_lines(self, files: List[str]) -> int:
        """Count total lines of code"""
        total = 0
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    total += len(f.readlines())
            except Exception:
                pass
        return total
