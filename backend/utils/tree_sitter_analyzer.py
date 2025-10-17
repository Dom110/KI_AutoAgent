"""
Tree-Sitter Code Analyzer v6.2

Provides Abstract Syntax Tree (AST) analysis for code intelligence.

Features:
- Parse multiple programming languages (Python, JavaScript, TypeScript, etc.)
- Extract code structure (classes, functions, imports)
- Identify dependencies and relationships
- Analyze code complexity
- Support for incremental parsing

Integration:
- Architect Agent: Codebase analysis for architecture design
- Research Agent: Code understanding for research
- Codesmith Agent: Context-aware code generation

Dependencies:
    pip install tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-typescript

Author: KI AutoAgent Team
Version: 6.2.0
Python: 3.13+
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Tree-sitter will be imported conditionally
TREE_SITTER_AVAILABLE = False
LANGUAGE_LOADERS = {}

try:
    import tree_sitter
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
    logger.debug("✅ tree-sitter available")

    # Import modern tree-sitter language packages (v0.23+)
    try:
        from tree_sitter_python import language as python_language
        LANGUAGE_LOADERS["python"] = python_language
        logger.debug("✅ tree-sitter-python loaded")
    except ImportError:
        logger.debug("⚠️  tree-sitter-python not available")

    try:
        from tree_sitter_javascript import language as javascript_language
        LANGUAGE_LOADERS["javascript"] = javascript_language
        logger.debug("✅ tree-sitter-javascript loaded")
    except ImportError:
        logger.debug("⚠️  tree-sitter-javascript not available")

    try:
        from tree_sitter_typescript import language_typescript as typescript_language
        LANGUAGE_LOADERS["typescript"] = typescript_language
        logger.debug("✅ tree-sitter-typescript loaded")
    except ImportError:
        logger.debug("⚠️  tree-sitter-typescript not available")

except ImportError:
    logger.warning("⚠️  tree-sitter not installed - install with: pip install tree-sitter")
    # Define stubs for type hints
    Language = Any
    Parser = Any


@dataclass()
class CodeStructure:
    """Parsed code structure from Tree-Sitter analysis."""

    file_path: str
    language: str
    classes: list[dict[str, Any]] = field(default_factory=list)
    functions: list[dict[str, Any]] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    complexity_score: float = 0.0
    line_count: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass()
class AnalysisResult:
    """Complete codebase analysis result."""

    workspace_path: str
    total_files: int
    analyzed_files: int
    skipped_files: int
    languages: dict[str, int]  # language -> file count
    structures: list[CodeStructure]
    total_classes: int = 0
    total_functions: int = 0
    total_lines: int = 0
    avg_complexity: float = 0.0
    errors: list[str] = field(default_factory=list)


class TreeSitterAnalyzer:
    """
    Tree-Sitter based code analyzer.

    Provides AST parsing and code structure extraction for multiple languages.
    """

    # Supported languages and their file extensions
    LANGUAGE_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp"
    }

    def __init__(self, workspace_path: str):
        """
        Initialize Tree-Sitter analyzer.

        Args:
            workspace_path: Path to workspace to analyze
        """
        self.workspace_path = Path(workspace_path)
        self.parsers: dict[str, Parser] = {}
        self.languages: dict[str, Language] = {}

        if not TREE_SITTER_AVAILABLE:
            logger.error("❌ tree-sitter not available - analysis disabled")
            return

        logger.info(f"🌳 Tree-Sitter Analyzer initialized for: {workspace_path}")

    def _load_language(self, language: str) -> Language | None:
        """
        Load Tree-Sitter language parser (modern v0.23+ method).

        Args:
            language: Language name

        Returns:
            Language object or None if unavailable
        """
        if not TREE_SITTER_AVAILABLE:
            return None

        if language in self.languages:
            return self.languages[language]

        # Check if language loader is available
        if language not in LANGUAGE_LOADERS:
            logger.warning(f"⚠️  Cannot load language: {language}")
            return None

        try:
            # Load language using modern package method
            lang_loader = LANGUAGE_LOADERS[language]
            lang_capsule = lang_loader()  # Returns PyCapsule
            lang = Language(lang_capsule)  # Wrap in Language object for v0.23+ API
            self.languages[language] = lang

            # Create parser
            parser = Parser()
            parser.language = lang  # v0.23+ property-based API
            self.parsers[language] = parser

            logger.debug(f"✅ Loaded language: {language}")
            return lang

        except Exception as e:
            logger.error(f"❌ Failed to load {language}: {e}")
            return None

    def analyze_file(self, file_path: str | Path) -> CodeStructure:
        """
        Analyze a single file with Tree-Sitter.

        Args:
            file_path: Path to file

        Returns:
            CodeStructure with analysis results
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()

        # Determine language
        language = self.LANGUAGE_MAP.get(extension)
        if not language:
            return CodeStructure(
                file_path=str(file_path),
                language="unknown",
                errors=[f"Unsupported file extension: {extension}"]
            )

        # Load language parser
        lang = self._load_language(language)
        if not lang or language not in self.parsers:
            return CodeStructure(
                file_path=str(file_path),
                language=language,
                errors=[f"Language parser not available: {language}"]
            )

        # Read file
        try:
            with open(file_path, "rb") as f:
                source_code = f.read()
        except Exception as e:
            return CodeStructure(
                file_path=str(file_path),
                language=language,
                errors=[f"Failed to read file: {e}"]
            )

        # Parse with Tree-Sitter
        parser = self.parsers[language]
        tree = parser.parse(source_code)
        root_node = tree.root_node

        # Extract structure
        structure = CodeStructure(
            file_path=str(file_path),
            language=language,
            line_count=source_code.count(b'\n') + 1
        )

        # Extract classes, functions, imports based on language
        if language == "python":
            self._extract_python_structure(root_node, source_code, structure)
        elif language in ["javascript", "typescript"]:
            self._extract_js_structure(root_node, source_code, structure)
        else:
            logger.debug(f"⚠️  Language-specific extraction not implemented: {language}")

        # Calculate complexity
        structure.complexity_score = self._calculate_complexity(root_node)

        logger.debug(f"✅ Analyzed {file_path.name}: "
                    f"{len(structure.classes)} classes, "
                    f"{len(structure.functions)} functions")

        return structure

    def _extract_python_structure(
        self,
        root_node: Any,
        source_code: bytes,
        structure: CodeStructure
    ) -> None:
        """
        Extract Python-specific code structure.

        Args:
            root_node: Tree-Sitter root node
            source_code: Source code bytes
            structure: CodeStructure to populate
        """
        def traverse(node: Any) -> None:
            """Recursively traverse AST."""
            if node.type == "class_definition":
                class_name_node = node.child_by_field_name("name")
                if class_name_node:
                    class_name = source_code[class_name_node.start_byte:class_name_node.end_byte].decode("utf-8")
                    structure.classes.append({
                        "name": class_name,
                        "line": node.start_point[0] + 1,
                        "type": "class"
                    })

            elif node.type == "function_definition":
                func_name_node = node.child_by_field_name("name")
                if func_name_node:
                    func_name = source_code[func_name_node.start_byte:func_name_node.end_byte].decode("utf-8")
                    structure.functions.append({
                        "name": func_name,
                        "line": node.start_point[0] + 1,
                        "type": "function"
                    })

            elif node.type == "import_statement" or node.type == "import_from_statement":
                import_text = source_code[node.start_byte:node.end_byte].decode("utf-8")
                structure.imports.append(import_text)

            # Recurse to children
            for child in node.children:
                traverse(child)

        traverse(root_node)

    def _extract_js_structure(
        self,
        root_node: Any,
        source_code: bytes,
        structure: CodeStructure
    ) -> None:
        """
        Extract JavaScript/TypeScript code structure.

        Args:
            root_node: Tree-Sitter root node
            source_code: Source code bytes
            structure: CodeStructure to populate
        """
        def traverse(node: Any) -> None:
            """Recursively traverse AST."""
            if node.type == "class_declaration":
                class_name_node = node.child_by_field_name("name")
                if class_name_node:
                    class_name = source_code[class_name_node.start_byte:class_name_node.end_byte].decode("utf-8")
                    structure.classes.append({
                        "name": class_name,
                        "line": node.start_point[0] + 1,
                        "type": "class"
                    })

            elif node.type in ["function_declaration", "arrow_function", "function"]:
                # Try to extract function name
                func_name = "anonymous"
                name_node = node.child_by_field_name("name")
                if name_node:
                    func_name = source_code[name_node.start_byte:name_node.end_byte].decode("utf-8")

                structure.functions.append({
                    "name": func_name,
                    "line": node.start_point[0] + 1,
                    "type": "function"
                })

            elif node.type == "import_statement":
                import_text = source_code[node.start_byte:node.end_byte].decode("utf-8")
                structure.imports.append(import_text)

            elif node.type == "export_statement":
                export_text = source_code[node.start_byte:node.end_byte].decode("utf-8")
                structure.exports.append(export_text)

            # Recurse to children
            for child in node.children:
                traverse(child)

        traverse(root_node)

    def _calculate_complexity(self, node: Any) -> float:
        """
        Calculate code complexity score.

        Simple heuristic based on:
        - Nesting depth
        - Number of branches
        - Number of loops

        Args:
            node: Tree-Sitter root node

        Returns:
            Complexity score (0-100)
        """
        complexity = 0.0

        def traverse(node: Any, depth: int = 0) -> None:
            nonlocal complexity

            # Penalize deep nesting
            if depth > 3:
                complexity += (depth - 3) * 2

            # Count control flow structures
            if node.type in ["if_statement", "else_clause", "elif_clause"]:
                complexity += 1
            elif node.type in ["for_statement", "while_statement"]:
                complexity += 2
            elif node.type in ["try_statement", "except_clause"]:
                complexity += 1

            # Recurse
            for child in node.children:
                traverse(child, depth + 1)

        traverse(node)

        # Normalize to 0-100 scale
        return min(complexity, 100.0)

    def analyze_workspace(
        self,
        max_files: int = 100,
        exclude_dirs: list[str] | None = None
    ) -> AnalysisResult:
        """
        Analyze entire workspace.

        Args:
            max_files: Maximum files to analyze
            exclude_dirs: Directories to exclude (e.g., node_modules, venv)

        Returns:
            AnalysisResult with complete analysis
        """
        if exclude_dirs is None:
            exclude_dirs = [
                "node_modules",
                "venv",
                ".venv",
                ".git",
                "__pycache__",
                "dist",
                "build",
                ".next",
                ".nuxt"
            ]

        logger.info(f"🔍 Analyzing workspace: {self.workspace_path}")

        structures: list[CodeStructure] = []
        languages: dict[str, int] = {}
        total_files = 0
        analyzed_files = 0
        skipped_files = 0

        # Walk workspace
        for root, dirs, files in os.walk(self.workspace_path):
            # Remove excluded directories from traversal
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                file_path = Path(root) / file
                extension = file_path.suffix.lower()

                total_files += 1

                # Check if supported
                if extension not in self.LANGUAGE_MAP:
                    skipped_files += 1
                    continue

                # Check max files limit
                if analyzed_files >= max_files:
                    logger.warning(f"⚠️  Reached max files limit: {max_files}")
                    break

                # Analyze file
                structure = self.analyze_file(file_path)
                structures.append(structure)

                # Track language
                if structure.language != "unknown":
                    languages[structure.language] = languages.get(structure.language, 0) + 1
                    analyzed_files += 1
                else:
                    skipped_files += 1

        # Calculate aggregate metrics
        total_classes = sum(len(s.classes) for s in structures)
        total_functions = sum(len(s.functions) for s in structures)
        total_lines = sum(s.line_count for s in structures)
        avg_complexity = (
            sum(s.complexity_score for s in structures) / len(structures)
            if structures else 0.0
        )

        result = AnalysisResult(
            workspace_path=str(self.workspace_path),
            total_files=total_files,
            analyzed_files=analyzed_files,
            skipped_files=skipped_files,
            languages=languages,
            structures=structures,
            total_classes=total_classes,
            total_functions=total_functions,
            total_lines=total_lines,
            avg_complexity=avg_complexity
        )

        logger.info(f"✅ Analysis complete:")
        logger.info(f"  Files: {analyzed_files}/{total_files} analyzed")
        logger.info(f"  Languages: {', '.join(f'{k}({v})' for k, v in languages.items())}")
        logger.info(f"  Classes: {total_classes}, Functions: {total_functions}")
        logger.info(f"  Lines: {total_lines}, Avg Complexity: {avg_complexity:.1f}")

        return result

    def get_codebase_summary(self, analysis: AnalysisResult) -> str:
        """
        Generate human-readable codebase summary.

        Args:
            analysis: Analysis result

        Returns:
            Markdown formatted summary
        """
        summary = f"""# Codebase Analysis Summary

## Overview
**Workspace:** `{analysis.workspace_path}`
**Files Analyzed:** {analysis.analyzed_files} / {analysis.total_files}
**Total Lines:** {analysis.total_lines:,}

## Languages
"""
        for lang, count in sorted(analysis.languages.items(), key=lambda x: x[1], reverse=True):
            summary += f"- **{lang}**: {count} files\n"

        summary += f"""
## Code Structure
- **Classes:** {analysis.total_classes}
- **Functions:** {analysis.total_functions}
- **Average Complexity:** {analysis.avg_complexity:.1f}/100

## Top Files
"""
        # Sort by complexity
        top_files = sorted(
            analysis.structures,
            key=lambda s: s.complexity_score,
            reverse=True
        )[:5]

        for structure in top_files:
            summary += f"- `{Path(structure.file_path).name}` ({structure.language}): "
            summary += f"{len(structure.classes)} classes, "
            summary += f"{len(structure.functions)} functions, "
            summary += f"complexity {structure.complexity_score:.0f}\n"

        return summary


# Convenience exports
__all__ = [
    "TreeSitterAnalyzer",
    "CodeStructure",
    "AnalysisResult",
    "TREE_SITTER_AVAILABLE"
]
