from __future__ import annotations

"""
Radon Metrics - Code complexity and maintainability metrics
Real implementation using radon library
"""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    from radon.complexity import cc_visit
    from radon.metrics import mi_visit
    from radon.raw import analyze

    RADON_AVAILABLE = True
except ImportError:
    RADON_AVAILABLE = False
    logger.warning("⚠️ Radon not available - install with: pip install radon")


class RadonMetrics:
    """
    Code complexity and maintainability metrics using Radon

    Metrics:
    - Cyclomatic Complexity (CC): Measures code complexity
    - Maintainability Index (MI): Measures code maintainability (0-100)
    - Halstead Metrics: Measures code volume and difficulty
    - Raw Metrics: LOC, SLOC, comments, etc.
    """

    def __init__(self):
        self.radon_available = RADON_AVAILABLE
        if self.radon_available:
            logger.info("✅ Radon library found")
        else:
            logger.warning(
                "⚠️ Radon library not found - install with: pip install radon"
            )

    async def calculate_all_metrics(
        self, root_path: str, progress_callback: Callable | None = None
    ) -> dict[str, Any]:
        """
        Calculate all code metrics for codebase

        Args:
            root_path: Root directory to analyze
            progress_callback: Optional callback for progress updates

        Returns:
            {
                'summary': {
                    'average_complexity': 5.2,
                    'average_maintainability': 75.3,
                    'quality_score': 82.5,
                    'total_loc': 15432,
                    'total_sloc': 12234
                },
                'files': [
                    {
                        'file': 'app.py',
                        'complexity': 8.5,
                        'maintainability': 65.2,
                        'loc': 234,
                        'sloc': 189,
                        'comments': 45,
                        'functions': [...]
                    }
                ]
            }
        """
        if progress_callback:
            await progress_callback("📊 Calculating code metrics...")

        if not self.radon_available:
            logger.warning("Radon library not available - returning stub results")
            return {
                "summary": {
                    "average_complexity": 0.0,
                    "average_maintainability": 0.0,
                    "quality_score": 0.0,
                },
                "files": [],
                "note": "Radon library not installed - install with: pip install radon",
            }

        try:
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

            logger.info(f"📊 Analyzing metrics for {len(python_files)} Python files...")

            files_metrics = []
            total_complexity = 0
            total_maintainability = 0
            total_loc = 0
            total_sloc = 0
            files_with_metrics = 0

            for py_file in python_files:
                try:
                    with open(py_file, encoding="utf-8") as f:
                        code = f.read()

                    # Skip empty files
                    if not code.strip():
                        continue

                    # Cyclomatic Complexity
                    cc_results = cc_visit(code)
                    avg_complexity = (
                        sum(r.complexity for r in cc_results) / len(cc_results)
                        if cc_results
                        else 0
                    )

                    # Maintainability Index
                    mi_result = mi_visit(code, multi=True)
                    maintainability = (
                        mi_result if isinstance(mi_result, (int, float)) else 0
                    )

                    # Raw Metrics
                    raw = analyze(code)

                    # Halstead Metrics (optional, can be heavy)
                    # h_results = h_visit(code)

                    file_metrics = {
                        "file": str(py_file),
                        "complexity": round(avg_complexity, 2),
                        "maintainability": round(maintainability, 2),
                        "loc": raw.loc,
                        "sloc": raw.sloc,
                        "comments": raw.comments,
                        "multi": raw.multi,
                        "blank": raw.blank,
                        "single_comments": raw.single_comments,
                        "functions": [
                            {
                                "name": func.name,
                                "complexity": func.complexity,
                                "line": func.lineno,
                                "endline": func.endline,
                                "rank": self._complexity_rank(func.complexity),
                            }
                            for func in cc_results
                        ],
                    }

                    files_metrics.append(file_metrics)

                    # Accumulate for averages
                    total_complexity += avg_complexity
                    total_maintainability += maintainability
                    total_loc += raw.loc
                    total_sloc += raw.sloc
                    files_with_metrics += 1

                except Exception as e:
                    logger.warning(f"Failed to analyze {py_file}: {e}")
                    continue

            # Calculate summary
            avg_complexity = (
                total_complexity / files_with_metrics if files_with_metrics > 0 else 0
            )
            avg_maintainability = (
                total_maintainability / files_with_metrics
                if files_with_metrics > 0
                else 0
            )

            # Quality score (weighted combination)
            # Lower complexity is better, higher maintainability is better
            quality_score = self._calculate_quality_score(
                avg_complexity, avg_maintainability
            )

            summary = {
                "average_complexity": round(avg_complexity, 2),
                "average_maintainability": round(avg_maintainability, 2),
                "quality_score": round(quality_score, 2),
                "total_loc": total_loc,
                "total_sloc": total_sloc,
                "total_files": len(files_metrics),
            }

            if progress_callback:
                await progress_callback(
                    f"📊 Metrics complete: Complexity {summary['average_complexity']}, "
                    f"Maintainability {summary['average_maintainability']}"
                )

            logger.info(
                f"✅ Radon metrics complete: "
                f"Avg Complexity={avg_complexity:.2f}, "
                f"Avg Maintainability={avg_maintainability:.2f}"
            )

            return {
                "summary": summary,
                "files": files_metrics,
                "total_files": len(files_metrics),
            }

        except Exception as e:
            logger.error(f"Radon metrics calculation failed: {e}")
            return {
                "summary": {
                    "average_complexity": 0.0,
                    "average_maintainability": 0.0,
                    "quality_score": 0.0,
                },
                "files": [],
                "error": str(e),
            }

    def _complexity_rank(self, complexity: int) -> str:
        """Map complexity score to rank (A-F)"""
        if complexity <= 5:
            return "A"
        elif complexity <= 10:
            return "B"
        elif complexity <= 20:
            return "C"
        elif complexity <= 30:
            return "D"
        elif complexity <= 40:
            return "E"
        else:
            return "F"

    def _calculate_quality_score(
        self, avg_complexity: float, avg_maintainability: float
    ) -> float:
        """
        Calculate overall quality score (0-100)

        Formula:
        - Maintainability contributes 60% (already 0-100)
        - Complexity contributes 40% (inversely, capped at 20)
        """
        # Normalize complexity (lower is better, cap at 20)
        complexity_score = max(0, 100 - (avg_complexity / 20 * 100))

        # Weighted combination
        quality = (avg_maintainability * 0.6) + (complexity_score * 0.4)

        return max(0, min(100, quality))
