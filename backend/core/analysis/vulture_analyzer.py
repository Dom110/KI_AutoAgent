from __future__ import annotations

"""
Vulture Analyzer - Dead code detection
Real implementation using vulture library
"""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    from vulture import Vulture

    VULTURE_AVAILABLE = True
except ImportError:
    VULTURE_AVAILABLE = False
    logger.warning("⚠️ Vulture not available - install with: pip install vulture")


class VultureAnalyzer:
    """
    Dead code detection using Vulture
    Finds unused functions, classes, variables, imports, and attributes
    """

    def __init__(self):
        self.vulture_available = VULTURE_AVAILABLE
        if self.vulture_available:
            logger.info("✅ Vulture library found")
        else:
            logger.warning(
                "⚠️ Vulture library not found - install with: pip install vulture"
            )

    async def find_dead_code(
        self,
        root_path: str,
        progress_callback: Callable | None = None,
        min_confidence: int = 60,
    ) -> dict[str, Any]:
        """
        Find dead code in codebase using Vulture

        Args:
            root_path: Root directory to analyze
            progress_callback: Optional callback for progress updates
            min_confidence: Minimum confidence level (0-100) for reporting dead code

        Returns:
            {
                'files': [
                    {
                        'file': 'app.py',
                        'items': [
                            {
                                'name': 'unused_function',
                                'type': 'function',
                                'line': 42,
                                'confidence': 100,
                                'message': 'unused function ...'
                            }
                        ]
                    }
                ],
                'summary': {
                    'total_dead_code': 15,
                    'unused_functions': 5,
                    'unused_classes': 2,
                    'unused_variables': 8,
                    'unused_imports': 0,
                    'unused_attributes': 0
                }
            }
        """
        if progress_callback:
            await progress_callback("🧹 Running Vulture dead code detection...")

        if not self.vulture_available:
            logger.warning("Vulture library not available - returning stub results")
            return {
                "files": [],
                "summary": {
                    "total_dead_code": 0,
                    "unused_functions": 0,
                    "unused_classes": 0,
                    "unused_variables": 0,
                    "unused_imports": 0,
                    "unused_attributes": 0,
                },
                "note": "Vulture library not installed - install with: pip install vulture",
            }

        try:
            # v5.8.1: Vulture 2.11+ doesn't accept min_confidence in __init__
            vulture = Vulture(verbose=False)
            vulture.min_confidence = min_confidence

            # Find all Python files
            root = Path(root_path)
            python_files = list(root.rglob("*.py"))

            # Exclude common directories
            excluded_dirs = {
                ".git",
                "__pycache__",
                "venv",
                "env",
                ".venv",
                "node_modules",
                ".tox",
            }
            python_files = [
                f
                for f in python_files
                if not any(excluded in f.parts for excluded in excluded_dirs)
            ]

            logger.info(
                f"🔍 Analyzing {len(python_files)} Python files for dead code..."
            )

            # Scan files
            vulture.scavenge([str(f) for f in python_files])

            # Group findings by file
            files_data = {}
            type_counts = {
                "function": 0,
                "class": 0,
                "variable": 0,
                "import": 0,
                "attribute": 0,
                "property": 0,
            }

            for item in vulture.get_unused_code():
                file_path = str(item.filename)

                if file_path not in files_data:
                    files_data[file_path] = {"file": file_path, "items": []}

                item_type = (
                    item.typ
                )  # 'function', 'class', 'variable', 'import', 'attribute', 'property'
                type_counts[item_type] = type_counts.get(item_type, 0) + 1

                files_data[file_path]["items"].append(
                    {
                        "name": item.name,
                        "type": item_type,
                        "line": item.first_lineno,
                        "confidence": item.confidence,
                        "message": str(item),
                    }
                )

            # Convert to list
            files_list = list(files_data.values())

            # Create summary
            total_dead_code = sum(type_counts.values())
            summary = {
                "total_dead_code": total_dead_code,
                "unused_functions": type_counts.get("function", 0),
                "unused_classes": type_counts.get("class", 0),
                "unused_variables": type_counts.get("variable", 0),
                "unused_imports": type_counts.get("import", 0),
                "unused_attributes": type_counts.get("attribute", 0)
                + type_counts.get("property", 0),
            }

            if progress_callback:
                await progress_callback(
                    f"🧹 Dead code detection complete: {total_dead_code} issues found"
                )

            logger.info(
                f"✅ Vulture analysis complete: {total_dead_code} dead code items found"
            )

            return {
                "files": files_list,
                "summary": summary,
                "total_items": total_dead_code,
            }

        except Exception as e:
            logger.error(f"Vulture analysis failed: {e}")
            return {
                "files": [],
                "summary": {
                    "total_dead_code": 0,
                    "unused_functions": 0,
                    "unused_classes": 0,
                    "unused_variables": 0,
                    "unused_imports": 0,
                    "unused_attributes": 0,
                },
                "error": str(e),
            }
