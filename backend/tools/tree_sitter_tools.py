"""
Tree-sitter Code Analysis Tools for v6.0

Multi-language code parsing and analysis using Tree-sitter.
Supports: Python, JavaScript, TypeScript

Author: KI AutoAgent Team
Version: 6.0.0
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from tree_sitter import Language, Parser, Node

logger = logging.getLogger(__name__)


# ============================================================================
# LANGUAGE SETUP
# ============================================================================

def _setup_parsers() -> dict[str, Parser]:
    """Setup Tree-sitter parsers for supported languages"""
    parsers = {}

    try:
        # Python
        import tree_sitter_python
        python_language = Language(tree_sitter_python.language())
        python_parser = Parser(python_language)
        parsers["python"] = python_parser
        logger.debug("✅ Python parser loaded")
    except Exception as e:
        logger.warning(f"Failed to load Python parser: {e}")

    try:
        # JavaScript
        import tree_sitter_javascript
        js_language = Language(tree_sitter_javascript.language())
        js_parser = Parser(js_language)
        parsers["javascript"] = js_parser
        logger.debug("✅ JavaScript parser loaded")
    except Exception as e:
        logger.warning(f"Failed to load JavaScript parser: {e}")

    try:
        # TypeScript
        import tree_sitter_typescript
        ts_language = Language(tree_sitter_typescript.language_typescript())
        ts_parser = Parser(ts_language)
        parsers["typescript"] = ts_parser
        logger.debug("✅ TypeScript parser loaded")
    except Exception as e:
        logger.warning(f"Failed to load TypeScript parser: {e}")

    return parsers


# Global parsers (initialized once)
_PARSERS = _setup_parsers()


# ============================================================================
# TREE-SITTER ANALYZER
# ============================================================================

class TreeSitterAnalyzer:
    """
    Multi-language code analysis using Tree-sitter.

    Capabilities:
    - Parse files and extract AST
    - Extract functions, classes, imports
    - Validate syntax
    - Find specific code patterns
    - Locate issues in code
    """

    def __init__(self):
        self.parsers = _PARSERS
        logger.info(f"TreeSitterAnalyzer initialized with {len(self.parsers)} languages")

    def detect_language(self, file_path: str) -> str | None:
        """Detect programming language from file extension"""
        ext = Path(file_path).suffix.lower()

        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
        }

        return lang_map.get(ext)

    def parse_file(self, file_path: str) -> dict[str, Any] | None:
        """
        Parse file and return AST + metadata.

        Args:
            file_path: Path to file to parse

        Returns:
            {
                "language": str,
                "tree": Tree,
                "functions": list[dict],
                "classes": list[dict],
                "imports": list[str],
                "syntax_valid": bool
            }
        """
        # Detect language
        language = self.detect_language(file_path)
        if not language:
            logger.warning(f"Unknown language for: {file_path}")
            return None

        parser = self.parsers.get(language)
        if not parser:
            logger.warning(f"No parser for language: {language}")
            return None

        # Read file
        try:
            with open(file_path, "rb") as f:
                code = f.read()
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return None

        # Parse
        try:
            tree = parser.parse(code)
            root = tree.root_node

            # Extract metadata
            result = {
                "language": language,
                "file_path": file_path,
                "tree": tree,
                "root_node": root,
                "functions": self._extract_functions(root, code, language),
                "classes": self._extract_classes(root, code, language),
                "imports": self._extract_imports(root, code, language),
                "syntax_valid": not root.has_error,
                "error_nodes": self._find_error_nodes(root) if root.has_error else []
            }

            return result

        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return None

    def parse_directory(self, dir_path: str, extensions: list[str] | None = None) -> dict[str, Any]:
        """
        Parse entire directory recursively.

        Args:
            dir_path: Directory to scan
            extensions: File extensions to include (default: [".py", ".js", ".ts"])

        Returns:
            {
                "total_files": int,
                "parsed_files": int,
                "failed_files": int,
                "files": dict[str, parse_result],
                "summary": {
                    "total_functions": int,
                    "total_classes": int,
                    "syntax_errors": int
                }
            }
        """
        if extensions is None:
            extensions = [".py", ".js", ".jsx", ".ts", ".tsx"]

        results = {
            "total_files": 0,
            "parsed_files": 0,
            "failed_files": 0,
            "files": {},
            "summary": {
                "total_functions": 0,
                "total_classes": 0,
                "syntax_errors": 0
            }
        }

        # Find all matching files
        for root, dirs, files in os.walk(dir_path):
            # Skip hidden and node_modules
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']

            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    results["total_files"] += 1

                    # Parse
                    parse_result = self.parse_file(file_path)

                    if parse_result:
                        results["parsed_files"] += 1
                        results["files"][file_path] = parse_result

                        # Update summary
                        results["summary"]["total_functions"] += len(parse_result["functions"])
                        results["summary"]["total_classes"] += len(parse_result["classes"])
                        if not parse_result["syntax_valid"]:
                            results["summary"]["syntax_errors"] += 1
                    else:
                        results["failed_files"] += 1

        logger.info(f"Parsed directory {dir_path}: {results['parsed_files']}/{results['total_files']} files")
        return results

    def validate_syntax(self, code: str, language: str) -> bool:
        """
        Validate code syntax.

        Args:
            code: Code string to validate
            language: Programming language

        Returns:
            True if syntax is valid, False otherwise
        """
        parser = self.parsers.get(language)
        if not parser:
            logger.warning(f"No parser for language: {language}")
            return False

        try:
            tree = parser.parse(code.encode())
            return not tree.root_node.has_error
        except Exception as e:
            logger.error(f"Syntax validation failed: {e}")
            return False

    def _extract_functions(self, node: Node, code: bytes, language: str) -> list[dict]:
        """Extract all function definitions"""
        functions = []

        # Language-specific node types
        func_types = {
            "python": ["function_definition"],
            "javascript": ["function_declaration", "function_expression", "arrow_function"],
            "typescript": ["function_declaration", "function_expression", "arrow_function", "method_definition"]
        }

        target_types = func_types.get(language, [])

        def visit(n: Node):
            if n.type in target_types:
                func_info = {
                    "name": self._get_function_name(n, code),
                    "start_line": n.start_point[0] + 1,
                    "end_line": n.end_point[0] + 1,
                    "node_type": n.type
                }
                functions.append(func_info)

            for child in n.children:
                visit(child)

        visit(node)
        return functions

    def _extract_classes(self, node: Node, code: bytes, language: str) -> list[dict]:
        """Extract all class definitions"""
        classes = []

        class_types = {
            "python": ["class_definition"],
            "javascript": ["class_declaration"],
            "typescript": ["class_declaration"]
        }

        target_types = class_types.get(language, [])

        def visit(n: Node):
            if n.type in target_types:
                class_info = {
                    "name": self._get_class_name(n, code),
                    "start_line": n.start_point[0] + 1,
                    "end_line": n.end_point[0] + 1
                }
                classes.append(class_info)

            for child in n.children:
                visit(child)

        visit(node)
        return classes

    def _extract_imports(self, node: Node, code: bytes, language: str) -> list[str]:
        """Extract all imports"""
        imports = []

        import_types = {
            "python": ["import_statement", "import_from_statement"],
            "javascript": ["import_statement"],
            "typescript": ["import_statement"]
        }

        target_types = import_types.get(language, [])

        def visit(n: Node):
            if n.type in target_types:
                import_text = code[n.start_byte:n.end_byte].decode('utf-8')
                imports.append(import_text.strip())

            for child in n.children:
                visit(child)

        visit(node)
        return imports

    def _get_function_name(self, node: Node, code: bytes) -> str:
        """Extract function name from node"""
        for child in node.children:
            if child.type == "identifier":
                return code[child.start_byte:child.end_byte].decode('utf-8')
        return "<anonymous>"

    def _get_class_name(self, node: Node, code: bytes) -> str:
        """Extract class name from node"""
        for child in node.children:
            if child.type == "identifier":
                return code[child.start_byte:child.end_byte].decode('utf-8')
        return "<anonymous>"

    def _find_error_nodes(self, node: Node) -> list[dict]:
        """Find all error nodes in AST"""
        errors = []

        def visit(n: Node):
            if n.has_error:
                if n.type == "ERROR":
                    errors.append({
                        "line": n.start_point[0] + 1,
                        "column": n.start_point[1],
                        "type": "syntax_error"
                    })

            for child in n.children:
                visit(child)

        visit(node)
        return errors


# ============================================================================
# TOOL FUNCTIONS (for LangChain agents)
# ============================================================================

# Global analyzer instance
_analyzer = TreeSitterAnalyzer()


def analyze_codebase(path: str) -> dict[str, Any]:
    """
    Analyze entire codebase with Tree-sitter.

    Tool for agents to understand code structure.

    Args:
        path: Directory path to analyze

    Returns:
        Complete codebase analysis with functions, classes, imports
    """
    return _analyzer.parse_directory(path)


def validate_code_syntax(code: str, language: str) -> bool:
    """
    Validate code syntax.

    Tool for agents to check if generated code is syntactically valid.

    Args:
        code: Code string to validate
        language: Programming language (python, javascript, typescript)

    Returns:
        True if syntax is valid
    """
    return _analyzer.validate_syntax(code, language)


def parse_single_file(file_path: str) -> dict[str, Any] | None:
    """
    Parse single file and extract metadata.

    Tool for agents to analyze specific files.

    Args:
        file_path: Path to file

    Returns:
        File analysis with functions, classes, imports
    """
    return _analyzer.parse_file(file_path)
