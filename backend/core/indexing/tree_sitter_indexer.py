from __future__ import annotations

"""
Tree-sitter based AST indexing for code analysis
Provides fast, accurate parsing of Python, JavaScript, and TypeScript code
"""

import ast
import logging
from typing import Any

logger = logging.getLogger(__name__)


class TreeSitterIndexer:
    """
    AST-based code indexer using Python's built-in ast module
    For production: Replace with tree-sitter for multi-language support
    """

    def __init__(self):
        self.supported_languages = ["python"]
        logger.info("TreeSitterIndexer initialized (using Python ast module)")

    async def index_file(self, file_path: str) -> dict[str, Any]:
        """
        Index a single file and extract functions, classes, imports

        Returns:
            {
                'functions': [{'name': 'foo', 'line': 10, 'calls': ['bar', 'baz']}],
                'classes': [{'name': 'MyClass', 'methods': [...]}],
                'imports': [{'module': 'os', 'names': ['path']}],
                'calls': [{'function': 'bar', 'line': 15}]
            }
        """
        # v5.8.2: Support HTML/CSS/JS files with basic parsing
        if file_path.endswith((".html", ".css", ".js", ".jsx", ".ts", ".tsx")):
            return await self._index_web_file(file_path)

        if not file_path.endswith(".py"):
            return {"functions": [], "classes": [], "imports": [], "calls": []}

        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source, filename=file_path)

            functions = []
            classes = []
            imports = []
            calls = []

            # Extract functions and their calls
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_calls = self._extract_function_calls(node)
                    functions.append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "async": isinstance(node, ast.AsyncFunctionDef),
                            "calls": func_calls,
                            "parameters": [arg.arg for arg in node.args.args],
                            "decorators": [
                                self._get_decorator_name(d) for d in node.decorator_list
                            ],
                        }
                    )

                elif isinstance(node, ast.ClassDef):
                    methods = [
                        n.name for n in ast.walk(node) if isinstance(n, ast.FunctionDef)
                    ]
                    classes.append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "methods": methods,
                            "bases": [self._get_name(base) for base in node.bases],
                        }
                    )

                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.append(self._extract_import(node))

                elif isinstance(node, ast.Call):
                    func_name = self._get_call_name(node)
                    if func_name:
                        calls.append({"function": func_name, "line": node.lineno})

            return {
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "calls": calls,
            }

        except Exception as e:
            logger.error(f"Failed to index {file_path}: {e}")
            return {"functions": [], "classes": [], "imports": [], "calls": []}

    def _extract_function_calls(self, func_node: ast.FunctionDef) -> list[str]:
        """Extract all function calls within a function"""
        calls = []
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                call_name = self._get_call_name(node)
                if call_name:
                    calls.append(call_name)
        return list(set(calls))  # Remove duplicates

    def _get_call_name(self, call_node: ast.Call) -> str | None:
        """Get the name of a function call"""
        func = call_node.func
        if isinstance(func, ast.Name):
            return func.id
        elif isinstance(func, ast.Attribute):
            return func.attr
        return None

    def _get_name(self, node: ast.expr) -> str:
        """Get name from ast node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_attribute_path(node)
        return str(node)

    def _get_attribute_path(self, node: ast.Attribute) -> str:
        """Get full attribute path like 'os.path.join'"""
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))

    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Get decorator name"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            return self._get_call_name(decorator)
        return str(decorator)

    def _extract_import(self, node) -> dict[str, Any]:
        """Extract import information"""
        if isinstance(node, ast.Import):
            return {
                "type": "import",
                "module": node.names[0].name,
                "names": [alias.name for alias in node.names],
                "line": node.lineno,
            }
        elif isinstance(node, ast.ImportFrom):
            return {
                "type": "from_import",
                "module": node.module or "",
                "names": [alias.name for alias in node.names],
                "line": node.lineno,
            }
        return {}

    async def _index_web_file(self, file_path: str) -> dict[str, Any]:
        """
        Basic parsing for HTML/CSS/JS files (v5.8.2)
        Uses regex-based extraction (not a full AST parser)
        """
        import re

        functions = []
        classes = []
        imports = []

        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()

            # JavaScript/TypeScript function detection
            if file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
                # Match: function name(...) or const name = (...) => or async function name
                func_pattern = (
                    r"(?:async\s+)?(?:function|const|let|var)\s+(\w+)\s*[=\(]"
                )
                for match in re.finditer(func_pattern, source):
                    line_num = source[: match.start()].count("\n") + 1
                    functions.append(
                        {
                            "name": match.group(1),
                            "line": line_num,
                            "async": "async" in match.group(0),
                            "calls": [],
                            "parameters": [],
                            "decorators": [],
                        }
                    )

                # Match: class ClassName
                class_pattern = r"class\s+(\w+)"
                for match in re.finditer(class_pattern, source):
                    line_num = source[: match.start()].count("\n") + 1
                    classes.append(
                        {
                            "name": match.group(1),
                            "line": line_num,
                            "methods": [],
                            "bases": [],
                        }
                    )

                # Match: import/require statements
                import_pattern = r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]|require\([\'"]([^\'"]+)[\'"]\)'
                for match in re.finditer(import_pattern, source):
                    module = match.group(1) or match.group(2)
                    line_num = source[: match.start()].count("\n") + 1
                    imports.append(
                        {
                            "type": "import",
                            "module": module,
                            "names": [],
                            "line": line_num,
                        }
                    )

            # HTML: Extract IDs and script tags
            elif file_path.endswith(".html"):
                # Count script tags as "functions"
                script_pattern = r"<script[^>]*>(.*?)</script>"
                for i, match in enumerate(
                    re.finditer(script_pattern, source, re.DOTALL)
                ):
                    line_num = source[: match.start()].count("\n") + 1
                    functions.append(
                        {
                            "name": f"script_block_{i+1}",
                            "line": line_num,
                            "async": False,
                            "calls": [],
                            "parameters": [],
                            "decorators": [],
                        }
                    )

                # Find element IDs (useful for AI diagram generation)
                id_pattern = r'id=[\'"]([^\'"]+)[\'"]'
                for match in re.finditer(id_pattern, source):
                    line_num = source[: match.start()].count("\n") + 1
                    classes.append(
                        {
                            "name": f"#{match.group(1)}",
                            "line": line_num,
                            "methods": [],
                            "bases": [],
                        }
                    )

            # CSS: Extract selectors as "classes"
            elif file_path.endswith(".css"):
                # Match CSS selectors
                selector_pattern = r"([\.#]?[\w-]+)\s*\{"
                for match in re.finditer(selector_pattern, source):
                    line_num = source[: match.start()].count("\n") + 1
                    classes.append(
                        {
                            "name": match.group(1),
                            "line": line_num,
                            "methods": [],
                            "bases": [],
                        }
                    )

            logger.info(
                f"Web file indexed: {file_path} - {len(functions)} functions, {len(classes)} classes/selectors"
            )

            return {
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "calls": [],
            }

        except Exception as e:
            logger.error(f"Failed to index web file {file_path}: {e}")
            return {"functions": [], "classes": [], "imports": [], "calls": []}

    async def search_pattern(self, pattern: str) -> list[dict[str, Any]]:
        """Search for pattern in indexed code (stub for compatibility)"""
        return []
