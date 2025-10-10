#!/usr/bin/env python3
"""
Tree-sitter MCP Server - Code Analysis Tools

Provides multi-language code analysis capabilities via MCP protocol.

Supported Languages:
- Python (.py)
- JavaScript (.js, .jsx)
- TypeScript (.ts, .tsx)

Tools:
1. validate_syntax - Validate code syntax
2. parse_code - Parse code and extract AST metadata
3. analyze_file - Analyze a single file
4. analyze_directory - Analyze entire directory

Run:
    python mcp_servers/tree_sitter_server.py

Register with Claude:
    claude mcp add tree-sitter python mcp_servers/tree_sitter_server.py

Test:
    claude "Validate this Python code: print('hello')"

Author: KI AutoAgent Team
Version: 1.0.0 (MCP Protocol)
"""

import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Direct import to avoid circular dependencies
import importlib.util
spec = importlib.util.spec_from_file_location(
    "tree_sitter_tools",
    backend_path / "tools" / "tree_sitter_tools.py"
)
tree_sitter_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tree_sitter_module)
TreeSitterAnalyzer = tree_sitter_module.TreeSitterAnalyzer


# ============================================================================
# GLOBAL ANALYZER
# ============================================================================

analyzer = TreeSitterAnalyzer()


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================

async def validate_syntax(code: str, language: str) -> dict:
    """
    Validate code syntax.

    Args:
        code: Code string to validate
        language: Programming language (python, javascript, typescript)

    Returns:
        {
            "valid": bool,
            "language": str,
            "errors": list[dict] (if invalid)
        }
    """
    try:
        # Validate
        is_valid = analyzer.validate_syntax(code, language)

        if is_valid:
            return {
                "valid": True,
                "language": language,
                "message": f"✅ Code is syntactically valid ({language})"
            }
        else:
            # Parse to get error details
            tree = analyzer.parsers[language].parse(code.encode())
            errors = analyzer._find_error_nodes(tree.root_node)

            return {
                "valid": False,
                "language": language,
                "errors": errors,
                "message": f"❌ Syntax errors found ({len(errors)} error(s))"
            }

    except Exception as e:
        return {
            "valid": False,
            "language": language,
            "error": str(e),
            "message": f"❌ Validation failed: {str(e)}"
        }


async def parse_code(code: str, language: str) -> dict:
    """
    Parse code and extract AST metadata.

    Args:
        code: Code string to parse
        language: Programming language

    Returns:
        {
            "language": str,
            "syntax_valid": bool,
            "functions": list[dict],
            "classes": list[dict],
            "imports": list[str],
            "errors": list[dict] (if invalid)
        }
    """
    try:
        parser = analyzer.parsers.get(language)
        if not parser:
            return {
                "error": f"Unsupported language: {language}",
                "supported_languages": list(analyzer.parsers.keys())
            }

        # Parse
        code_bytes = code.encode()
        tree = parser.parse(code_bytes)
        root = tree.root_node

        # Extract metadata
        result = {
            "language": language,
            "syntax_valid": not root.has_error,
            "functions": analyzer._extract_functions(root, code_bytes, language),
            "classes": analyzer._extract_classes(root, code_bytes, language),
            "imports": analyzer._extract_imports(root, code_bytes, language),
            "timestamp": datetime.now().isoformat()
        }

        # Add errors if present
        if root.has_error:
            result["errors"] = analyzer._find_error_nodes(root)

        return result

    except Exception as e:
        return {
            "error": str(e),
            "language": language
        }


async def analyze_file(file_path: str) -> dict:
    """
    Analyze a single file.

    Args:
        file_path: Path to file

    Returns:
        Complete file analysis with functions, classes, imports
    """
    try:
        result = analyzer.parse_file(file_path)

        if not result:
            return {
                "error": f"Failed to parse file: {file_path}",
                "file_path": file_path
            }

        # Convert to JSON-serializable format
        return {
            "file_path": result["file_path"],
            "language": result["language"],
            "syntax_valid": result["syntax_valid"],
            "functions": result["functions"],
            "classes": result["classes"],
            "imports": result["imports"],
            "errors": result["error_nodes"] if not result["syntax_valid"] else [],
            "summary": {
                "functions_count": len(result["functions"]),
                "classes_count": len(result["classes"]),
                "imports_count": len(result["imports"])
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "error": str(e),
            "file_path": file_path
        }


async def analyze_directory(dir_path: str, extensions: list[str] | None = None) -> dict:
    """
    Analyze entire directory recursively.

    Args:
        dir_path: Directory path
        extensions: File extensions to include (default: [".py", ".js", ".ts"])

    Returns:
        Complete directory analysis with summary
    """
    try:
        result = analyzer.parse_directory(dir_path, extensions)

        # Convert to JSON-serializable format (remove tree objects)
        json_files = {}
        for file_path, file_result in result["files"].items():
            json_files[file_path] = {
                "language": file_result["language"],
                "syntax_valid": file_result["syntax_valid"],
                "functions": file_result["functions"],
                "classes": file_result["classes"],
                "imports": file_result["imports"],
                "errors": file_result["error_nodes"] if not file_result["syntax_valid"] else []
            }

        return {
            "directory": dir_path,
            "total_files": result["total_files"],
            "parsed_files": result["parsed_files"],
            "failed_files": result["failed_files"],
            "summary": result["summary"],
            "files": json_files,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "error": str(e),
            "directory": dir_path
        }


# ============================================================================
# MCP PROTOCOL HANDLER
# ============================================================================

async def handle_request(request: dict) -> dict:
    """
    Handle incoming MCP request.

    MCP uses JSON-RPC 2.0 protocol:
    - Request: {"jsonrpc": "2.0", "id": 1, "method": "...", "params": {...}}
    - Response: {"jsonrpc": "2.0", "id": 1, "result": {...}}
    - Error: {"jsonrpc": "2.0", "id": 1, "error": {"code": -32601, "message": "..."}}
    """

    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    # Initialize: Return server capabilities
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "tree-sitter-mcp-server",
                    "version": "1.0.0"
                }
            }
        }

    # List available tools
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {
                        "name": "validate_syntax",
                        "description": "Validate code syntax for Python, JavaScript, or TypeScript. Returns whether the code is syntactically valid and any errors found.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "code": {
                                    "type": "string",
                                    "description": "Code string to validate"
                                },
                                "language": {
                                    "type": "string",
                                    "description": "Programming language (python, javascript, typescript)",
                                    "enum": ["python", "javascript", "typescript"]
                                }
                            },
                            "required": ["code", "language"]
                        }
                    },
                    {
                        "name": "parse_code",
                        "description": "Parse code and extract AST metadata including functions, classes, and imports. Returns detailed code structure analysis.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "code": {
                                    "type": "string",
                                    "description": "Code string to parse"
                                },
                                "language": {
                                    "type": "string",
                                    "description": "Programming language (python, javascript, typescript)",
                                    "enum": ["python", "javascript", "typescript"]
                                }
                            },
                            "required": ["code", "language"]
                        }
                    },
                    {
                        "name": "analyze_file",
                        "description": "Analyze a single file and extract complete metadata including functions, classes, imports, and syntax validation.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Path to file to analyze"
                                }
                            },
                            "required": ["file_path"]
                        }
                    },
                    {
                        "name": "analyze_directory",
                        "description": "Analyze entire directory recursively. Returns summary of all code files with functions, classes, and syntax errors.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "dir_path": {
                                    "type": "string",
                                    "description": "Directory path to analyze"
                                },
                                "extensions": {
                                    "type": "array",
                                    "description": "File extensions to include (default: ['.py', '.js', '.ts'])",
                                    "items": {
                                        "type": "string"
                                    }
                                }
                            },
                            "required": ["dir_path"]
                        }
                    }
                ]
            }
        }

    # Execute tool
    elif method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})

        try:
            # Call appropriate tool
            if tool_name == "validate_syntax":
                result = await validate_syntax(
                    code=tool_args.get("code", ""),
                    language=tool_args.get("language", "python")
                )

            elif tool_name == "parse_code":
                result = await parse_code(
                    code=tool_args.get("code", ""),
                    language=tool_args.get("language", "python")
                )

            elif tool_name == "analyze_file":
                result = await analyze_file(
                    file_path=tool_args.get("file_path", "")
                )

            elif tool_name == "analyze_directory":
                result = await analyze_directory(
                    dir_path=tool_args.get("dir_path", ""),
                    extensions=tool_args.get("extensions")
                )

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }

            # Format result
            content_text = f"# Tree-sitter Analysis Result\n\n"
            content_text += f"**Tool:** {tool_name}\n\n"
            content_text += f"**Result:**\n```json\n{json.dumps(result, indent=2)}\n```\n\n"
            content_text += f"**Timestamp:** {datetime.now().isoformat()}\n"

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": content_text
                        }
                    ]
                }
            }

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Tool execution failed: {str(e)}"
                }
            }

    # Unknown method
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }


# ============================================================================
# MAIN SERVER LOOP
# ============================================================================

async def main():
    """
    Main MCP server loop.

    Reads JSON-RPC requests from stdin (one per line),
    processes them, and writes responses to stdout.
    """

    # Log to stderr (stdout is reserved for MCP protocol)
    print(f"[{datetime.now()}] Tree-sitter MCP Server started", file=sys.stderr)
    print(f"[{datetime.now()}] Supported languages: {list(analyzer.parsers.keys())}", file=sys.stderr)
    print(f"[{datetime.now()}] Waiting for requests on stdin...", file=sys.stderr)

    # Main loop: read requests, send responses
    while True:
        try:
            # Read one line from stdin
            line = sys.stdin.readline()

            # End of input
            if not line:
                print(f"[{datetime.now()}] EOF reached, shutting down", file=sys.stderr)
                break

            line = line.strip()
            if not line:
                continue

            # Parse JSON-RPC request
            request = json.loads(line)
            print(f"[{datetime.now()}] Request: {request.get('method')}", file=sys.stderr)

            # Handle request
            response = await handle_request(request)

            # Write JSON-RPC response to stdout
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

            print(f"[{datetime.now()}] Response sent", file=sys.stderr)

        except json.JSONDecodeError as e:
            # Invalid JSON
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()
            print(f"[{datetime.now()}] JSON parse error: {e}", file=sys.stderr)

        except Exception as e:
            # Internal error
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()
            print(f"[{datetime.now()}] Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] Interrupted by user", file=sys.stderr)
    except Exception as e:
        print(f"[{datetime.now()}] Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
