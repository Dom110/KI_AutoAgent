from __future__ import annotations

"""
Code Indexer - Orchestrates file indexing and builds comprehensive code index
"""

import logging
import os
from collections.abc import Callable
from typing import Any

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
            "node_modules",
            "venv",
            "__pycache__",
            ".git",
            "dist",
            "build",
            ".vscode",
            ".idea",
            "coverage",
        }
        self.excluded_extensions = {".pyc", ".pyo", ".so", ".dylib"}

    async def build_full_index(
        self,
        root_path: str,
        progress_callback: Callable | None = None,
        request_type: str = "general",
    ) -> dict[str, Any]:
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
        # v5.8.4: Count instead of storing full lists to reduce memory usage
        total_functions_count = 0
        total_classes_count = 0

        for i, file_path in enumerate(python_files):
            if progress_callback and i % 10 == 0:
                await progress_callback(
                    f"📂 Indexing file {i + 1}/{total_files}: {os.path.basename(file_path)}"
                )

            file_data = await self.tree_sitter.index_file(file_path)
            relative_path = os.path.relpath(file_path, root_path)

            ast_data[relative_path] = file_data

            # Build import graph
            imports = [imp.get("module", "") for imp in file_data.get("imports", [])]
            import_graph[relative_path] = imports

            # v5.8.4: Count functions and classes instead of duplicating them
            # Functions and classes are already stored in ast_data[relative_path]
            total_functions_count += len(file_data.get("functions", []))
            total_classes_count += len(file_data.get("classes", []))

        # Calculate statistics
        statistics = {
            "total_files": total_files,
            "total_functions": total_functions_count,
            "total_classes": total_classes_count,
            "total_imports": sum(len(imports) for imports in import_graph.values()),
            "lines_of_code": self._count_total_lines(python_files),
        }

        logger.info(f"Indexing complete: {statistics}")

        # v5.8.4: Removed all_functions and all_classes to eliminate duplication
        # All function/class data is already in ast.files, saving ~300KB per analysis
        return {
            "ast": {"files": ast_data},
            "import_graph": import_graph,
            "statistics": statistics,
        }

    def _find_python_files(self, root_path: str) -> list[str]:
        """Find all Python files in the project"""
        all_files = []  # v5.8.2: Renamed from python_files

        for root, dirs, files in os.walk(root_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]

            for file in files:
                # v5.8.2: Support HTML/CSS/JS files for frontend projects
                if file.endswith(
                    (".py", ".html", ".css", ".js", ".jsx", ".ts", ".tsx", ".vue")
                ):
                    file_path = os.path.join(root, file)
                    all_files.append(file_path)

        return all_files

    def _count_total_lines(self, files: list[str]) -> int:
        """Count total lines of code"""
        total = 0
        for file_path in files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    total += len(f.readlines())
            except Exception:
                pass
        return total
