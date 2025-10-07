"""
Lightweight Code Search Service
Fast text-based code searching without heavy dependencies
"""

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SearchResult:
    """Single search result"""

    def __init__(
        self,
        file_path: str,
        line_number: int,
        line_content: str,
        context_before: list[str] = None,
        context_after: list[str] = None,
    ):
        self.file_path = file_path
        self.line_number = line_number
        self.line_content = line_content
        self.context_before = context_before or []
        self.context_after = context_after or []

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "line_content": self.line_content,
            "context_before": self.context_before,
            "context_after": self.context_after,
        }


class LightweightCodeSearch:
    """
    Fast code search using regex patterns
    No external dependencies required

    v5.8.0: Optional cache_dir parameter for consistency (not used, search is always live)
    """

    def __init__(self, project_root: str, cache_dir: str | None = None):
        """
        Initialize code search

        Args:
            project_root: Root directory to search
            cache_dir: Optional cache directory (for API consistency, not used in this implementation)
        """
        self.project_root = Path(project_root)
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.default_ignore_patterns = {
            ".git",
            "__pycache__",
            "node_modules",
            ".venv",
            "venv",
            "dist",
            "build",
            ".pytest_cache",
            ".mypy_cache",
            ".tox",
            "*.pyc",
            "*.pyo",
            "*.so",
            "*.dylib",
            "*.dll",
        }
        logger.info(f"🔍 LightweightCodeSearch initialized for: {self.project_root}")

    def search(
        self,
        pattern: str,
        file_pattern: str = "**/*.py",
        case_sensitive: bool = False,
        context_lines: int = 2,
        max_results: int = 100,
    ) -> list[SearchResult]:
        """
        Search for pattern in files

        Args:
            pattern: Regex pattern to search for
            file_pattern: Glob pattern for files to search
            case_sensitive: Whether search is case-sensitive
            context_lines: Number of context lines before/after match
            max_results: Maximum number of results to return

        Returns:
            List of SearchResult objects
        """
        results = []
        flags = 0 if case_sensitive else re.IGNORECASE

        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            logger.error(f"Invalid regex pattern: {pattern} - {e}")
            return []

        # Find matching files
        matching_files = self._find_files(file_pattern)

        for file_path in matching_files:
            if len(results) >= max_results:
                break

            try:
                results.extend(
                    self._search_file(
                        file_path, regex, context_lines, max_results - len(results)
                    )
                )
            except Exception as e:
                logger.warning(f"Error searching {file_path}: {e}")

        logger.info(f"🔍 Found {len(results)} matches for pattern: {pattern}")
        return results

    def search_definition(
        self, symbol_name: str, symbol_type: str = "any", file_pattern: str = "**/*.py"
    ) -> list[SearchResult]:
        """
        Search for symbol definition (class, function, variable)

        Args:
            symbol_name: Name of symbol to find
            symbol_type: Type of symbol (class, function, variable, any)
            file_pattern: Files to search

        Returns:
            List of SearchResult objects
        """
        patterns = {
            "class": rf"^\s*class\s+{symbol_name}\s*[:\(]",
            "function": rf"^\s*def\s+{symbol_name}\s*\(",
            "variable": rf"^\s*{symbol_name}\s*[=:]",
            "any": rf"(^\s*class\s+{symbol_name}\s*[:\(]|^\s*def\s+{symbol_name}\s*\(|^\s*{symbol_name}\s*[=:])",
        }

        pattern = patterns.get(symbol_type, patterns["any"])
        return self.search(pattern, file_pattern, case_sensitive=True, context_lines=5)

    def search_usage(
        self, symbol_name: str, file_pattern: str = "**/*.py"
    ) -> list[SearchResult]:
        """
        Search for usages of a symbol

        Args:
            symbol_name: Symbol name to find usages of
            file_pattern: Files to search

        Returns:
            List of SearchResult objects
        """
        # Match word boundaries to avoid partial matches
        pattern = rf"\b{re.escape(symbol_name)}\b"
        return self.search(pattern, file_pattern, case_sensitive=True, context_lines=2)

    def _find_files(self, file_pattern: str) -> list[Path]:
        """Find files matching pattern"""
        matching_files = []

        for file_path in self.project_root.glob(file_pattern):
            # Check if file should be ignored
            if self._should_ignore(file_path):
                continue

            if file_path.is_file():
                matching_files.append(file_path)

        return matching_files

    def _should_ignore(self, file_path: Path) -> bool:
        """Check if file/directory should be ignored"""
        parts = file_path.parts

        for ignore_pattern in self.default_ignore_patterns:
            if "*" in ignore_pattern:
                # Wildcard pattern
                if file_path.match(ignore_pattern):
                    return True
            else:
                # Exact match in path
                if ignore_pattern in parts:
                    return True

        return False

    def _search_file(
        self, file_path: Path, regex: re.Pattern, context_lines: int, max_results: int
    ) -> list[SearchResult]:
        """Search single file for pattern"""
        results = []

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                if len(results) >= max_results:
                    break

                if regex.search(line):
                    # Get context
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)

                    context_before = [l.rstrip() for l in lines[start:i]]
                    context_after = [l.rstrip() for l in lines[i + 1 : end]]

                    result = SearchResult(
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=i + 1,
                        line_content=line.rstrip(),
                        context_before=context_before,
                        context_after=context_after,
                    )
                    results.append(result)

        except Exception as e:
            logger.warning(f"Error reading {file_path}: {e}")

        return results

    def add_ignore_pattern(self, pattern: str) -> None:
        """Add pattern to ignore list"""
        self.default_ignore_patterns.add(pattern)

    def remove_ignore_pattern(self, pattern: str) -> None:
        """Remove pattern from ignore list"""
        self.default_ignore_patterns.discard(pattern)
