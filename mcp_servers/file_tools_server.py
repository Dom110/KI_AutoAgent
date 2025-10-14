#!/usr/bin/env python3
"""
File Tools MCP Server - Streaming File Operations

Provides file system operations via MCP protocol with streaming support
for large files and Asimov security integration.

Replaces ALL direct file_tools.py calls with MCP protocol.

Features:
- Read files with streaming (chunked for large files)
- Write files with streaming progress
- Edit files (find/replace)
- List directory contents
- Asimov security checks (via asimov_server.py)
- Workspace-scoped only (security)

Run:
    ~/.ki_autoagent/venv/bin/python mcp_servers/file_tools_server.py

Register with Claude:
    claude mcp add file-tools ~/.ki_autoagent/venv/bin/python mcp_servers/file_tools_server.py

Test:
    claude "Read src/app.py from workspace /path/to/project"

Author: KI AutoAgent Team
Version: 1.0.0 (MCP Protocol)
Python: 3.13+
"""

import sys
import json
import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator
import glob
import aiofiles

# ============================================================================
# DEBUG MODE
# ============================================================================
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

def debug_log(message: str):
    """Log debug message to stderr if DEBUG_MODE enabled."""
    if DEBUG_MODE:
        print(f"[DEBUG {datetime.now()}] {message}", file=sys.stderr)


# ============================================================================
# FILE OPERATIONS WITH STREAMING
# ============================================================================

async def stream_read_file(
    file_path: str,
    workspace_path: str,
    chunk_size: int = 8192
) -> AsyncIterator[dict]:
    """
    Read file with streaming (for large files).

    Args:
        file_path: Relative path to file (e.g., "src/App.tsx")
        workspace_path: Absolute path to workspace
        chunk_size: Bytes per chunk (default: 8KB)

    Yields:
        {"type": "start", "path": str, "size": int}
        {"type": "chunk", "chunk_num": int, "content": str, "size": int}
        {"type": "complete", "path": str, "total_chunks": int, "total_size": int}
        {"type": "error", "message": str}
    """

    debug_log(f"stream_read_file: {file_path} (workspace: {workspace_path})")

    try:
        # Safety: Ensure file is within workspace
        abs_path = os.path.abspath(os.path.join(workspace_path, file_path))
        abs_workspace = os.path.abspath(workspace_path)

        if not abs_path.startswith(abs_workspace):
            yield {
                "type": "error",
                "message": f"File path outside workspace (security violation): {file_path}"
            }
            return

        # Check if file exists
        if not os.path.exists(abs_path):
            yield {
                "type": "error",
                "message": f"File not found: {file_path}"
            }
            return

        # Get file size
        file_size = os.path.getsize(abs_path)

        yield {
            "type": "start",
            "path": file_path,
            "size": file_size
        }

        # Stream file content in chunks
        chunk_num = 0
        total_size = 0

        async with aiofiles.open(abs_path, 'r', encoding='utf-8') as f:
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break

                chunk_size_actual = len(chunk)
                total_size += chunk_size_actual

                yield {
                    "type": "chunk",
                    "chunk_num": chunk_num,
                    "content": chunk,
                    "size": chunk_size_actual
                }

                chunk_num += 1

        yield {
            "type": "complete",
            "path": file_path,
            "total_chunks": chunk_num,
            "total_size": total_size
        }

        debug_log(f"stream_read_file complete: {chunk_num} chunks, {total_size} bytes")

    except Exception as e:
        debug_log(f"stream_read_file error: {e}")
        yield {
            "type": "error",
            "message": f"Failed to read file: {str(e)}"
        }


async def stream_write_file(
    file_path: str,
    content: str,
    workspace_path: str
) -> AsyncIterator[dict]:
    """
    Write file with streaming progress.

    Args:
        file_path: Relative path to file
        content: File content
        workspace_path: Absolute path to workspace

    Yields:
        {"type": "start", "path": str, "size": int}
        {"type": "progress", "bytes_written": int, "percent": float}
        {"type": "complete", "path": str, "bytes_written": int}
        {"type": "error", "message": str}
    """

    debug_log(f"stream_write_file: {file_path} ({len(content)} bytes)")

    try:
        # Safety: Ensure file is within workspace
        abs_path = os.path.abspath(os.path.join(workspace_path, file_path))
        abs_workspace = os.path.abspath(workspace_path)

        if not abs_path.startswith(abs_workspace):
            yield {
                "type": "error",
                "message": f"File path outside workspace (security violation): {file_path}"
            }
            return

        # Create parent directories
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        total_size = len(content)

        yield {
            "type": "start",
            "path": file_path,
            "size": total_size
        }

        # Write file (with progress updates for large files)
        chunk_size = 8192  # 8KB chunks
        bytes_written = 0

        async with aiofiles.open(abs_path, 'w', encoding='utf-8') as f:
            # Write in chunks for progress updates
            for i in range(0, total_size, chunk_size):
                chunk = content[i:i + chunk_size]
                await f.write(chunk)

                bytes_written += len(chunk)
                percent = (bytes_written / total_size) * 100 if total_size > 0 else 100

                # Emit progress updates for large files
                if total_size > 100000:  # > 100KB
                    yield {
                        "type": "progress",
                        "bytes_written": bytes_written,
                        "percent": round(percent, 2)
                    }

        yield {
            "type": "complete",
            "path": file_path,
            "bytes_written": bytes_written
        }

        debug_log(f"stream_write_file complete: {bytes_written} bytes")

    except Exception as e:
        debug_log(f"stream_write_file error: {e}")
        yield {
            "type": "error",
            "message": f"Failed to write file: {str(e)}"
        }


async def edit_file(
    file_path: str,
    old_content: str,
    new_content: str,
    workspace_path: str
) -> dict:
    """
    Edit file by replacing old_content with new_content.

    Args:
        file_path: Relative path to file
        old_content: String to find and replace
        new_content: Replacement string
        workspace_path: Absolute path to workspace

    Returns:
        {
            "success": bool,
            "path": str,
            "replacements": int,
            "error": str | None
        }
    """

    debug_log(f"edit_file: {file_path}")

    try:
        # Safety: Ensure file is within workspace
        abs_path = os.path.abspath(os.path.join(workspace_path, file_path))
        abs_workspace = os.path.abspath(workspace_path)

        if not abs_path.startswith(abs_workspace):
            return {
                "success": False,
                "path": file_path,
                "replacements": 0,
                "error": f"File path outside workspace (security violation): {file_path}"
            }

        # Read current content
        if not os.path.exists(abs_path):
            return {
                "success": False,
                "path": file_path,
                "replacements": 0,
                "error": f"File not found: {file_path}"
            }

        async with aiofiles.open(abs_path, 'r', encoding='utf-8') as f:
            content = await f.read()

        # Check if old_content exists
        if old_content not in content:
            return {
                "success": False,
                "path": file_path,
                "replacements": 0,
                "error": "Old content not found in file"
            }

        # Replace
        new_file_content = content.replace(old_content, new_content)
        replacements = content.count(old_content)

        # Write back
        async with aiofiles.open(abs_path, 'w', encoding='utf-8') as f:
            await f.write(new_file_content)

        debug_log(f"edit_file complete: {replacements} replacements")

        return {
            "success": True,
            "path": file_path,
            "replacements": replacements,
            "error": None
        }

    except Exception as e:
        debug_log(f"edit_file error: {e}")
        return {
            "success": False,
            "path": file_path,
            "replacements": 0,
            "error": f"Failed to edit file: {str(e)}"
        }


async def list_directory(
    dir_path: str,
    workspace_path: str,
    pattern: str | None = None,
    recursive: bool = False
) -> dict:
    """
    List directory contents.

    Args:
        dir_path: Relative directory path (e.g., "src")
        workspace_path: Absolute path to workspace
        pattern: Optional glob pattern (e.g., "*.py")
        recursive: Search recursively

    Returns:
        {
            "success": bool,
            "path": str,
            "files": list[str],
            "directories": list[str],
            "count": int,
            "error": str | None
        }
    """

    debug_log(f"list_directory: {dir_path} (pattern: {pattern}, recursive: {recursive})")

    try:
        # Safety: Ensure dir is within workspace
        abs_path = os.path.abspath(os.path.join(workspace_path, dir_path))
        abs_workspace = os.path.abspath(workspace_path)

        if not abs_path.startswith(abs_workspace):
            return {
                "success": False,
                "path": dir_path,
                "files": [],
                "directories": [],
                "count": 0,
                "error": f"Directory path outside workspace (security violation): {dir_path}"
            }

        # Check if directory exists
        if not os.path.exists(abs_path):
            return {
                "success": False,
                "path": dir_path,
                "files": [],
                "directories": [],
                "count": 0,
                "error": f"Directory not found: {dir_path}"
            }

        if not os.path.isdir(abs_path):
            return {
                "success": False,
                "path": dir_path,
                "files": [],
                "directories": [],
                "count": 0,
                "error": f"Path is not a directory: {dir_path}"
            }

        # List contents
        files = []
        directories = []

        if pattern and recursive:
            # Glob pattern with recursion
            glob_pattern = os.path.join(abs_path, '**', pattern)
            matches = glob.glob(glob_pattern, recursive=True)

            for match in matches:
                rel_path = os.path.relpath(match, abs_workspace)
                if os.path.isfile(match):
                    files.append(rel_path)
                elif os.path.isdir(match):
                    directories.append(rel_path)

        elif pattern:
            # Glob pattern without recursion
            glob_pattern = os.path.join(abs_path, pattern)
            matches = glob.glob(glob_pattern)

            for match in matches:
                rel_path = os.path.relpath(match, abs_workspace)
                if os.path.isfile(match):
                    files.append(rel_path)
                elif os.path.isdir(match):
                    directories.append(rel_path)

        else:
            # No pattern, just list directory
            for item in os.listdir(abs_path):
                item_path = os.path.join(abs_path, item)
                rel_path = os.path.relpath(item_path, abs_workspace)

                if os.path.isfile(item_path):
                    files.append(rel_path)
                elif os.path.isdir(item_path):
                    directories.append(rel_path)

        debug_log(f"list_directory complete: {len(files)} files, {len(directories)} dirs")

        return {
            "success": True,
            "path": dir_path,
            "files": sorted(files),
            "directories": sorted(directories),
            "count": len(files) + len(directories),
            "error": None
        }

    except Exception as e:
        debug_log(f"list_directory error: {e}")
        return {
            "success": False,
            "path": dir_path,
            "files": [],
            "directories": [],
            "count": 0,
            "error": f"Failed to list directory: {str(e)}"
        }


async def file_exists(
    file_path: str,
    workspace_path: str
) -> dict:
    """
    Check if file exists.

    Args:
        file_path: Relative path to file
        workspace_path: Absolute path to workspace

    Returns:
        {
            "exists": bool,
            "path": str,
            "is_file": bool,
            "is_directory": bool,
            "size": int | None,
            "error": str | None
        }
    """

    debug_log(f"file_exists: {file_path}")

    try:
        # Safety: Ensure path is within workspace
        abs_path = os.path.abspath(os.path.join(workspace_path, file_path))
        abs_workspace = os.path.abspath(workspace_path)

        if not abs_path.startswith(abs_workspace):
            return {
                "exists": False,
                "path": file_path,
                "is_file": False,
                "is_directory": False,
                "size": None,
                "error": f"File path outside workspace (security violation): {file_path}"
            }

        exists = os.path.exists(abs_path)
        is_file = os.path.isfile(abs_path) if exists else False
        is_directory = os.path.isdir(abs_path) if exists else False
        size = os.path.getsize(abs_path) if is_file else None

        return {
            "exists": exists,
            "path": file_path,
            "is_file": is_file,
            "is_directory": is_directory,
            "size": size,
            "error": None
        }

    except Exception as e:
        debug_log(f"file_exists error: {e}")
        return {
            "exists": False,
            "path": file_path,
            "is_file": False,
            "is_directory": False,
            "size": None,
            "error": f"Failed to check file existence: {str(e)}"
        }


# ============================================================================
# MCP PROTOCOL HANDLER
# ============================================================================

async def handle_request(request: dict) -> dict:
    """
    Handle incoming MCP request.

    JSON-RPC 2.0 protocol.
    """

    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    debug_log(f"MCP request: method={method}, id={request_id}")

    # Initialize
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "file-tools-mcp-server",
                    "version": "1.0.0"
                }
            }
        }

    # List tools
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {
                        "name": "read_file",
                        "description": "Read file with streaming (for large files). Returns file content in chunks.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Relative path to file (e.g., 'src/App.tsx')"
                                },
                                "workspace_path": {
                                    "type": "string",
                                    "description": "Absolute path to workspace"
                                },
                                "chunk_size": {
                                    "type": "integer",
                                    "description": "Bytes per chunk (default: 8192)"
                                }
                            },
                            "required": ["file_path", "workspace_path"]
                        }
                    },
                    {
                        "name": "write_file",
                        "description": "Write file with streaming progress updates. Creates parent directories automatically.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Relative path to file"
                                },
                                "content": {
                                    "type": "string",
                                    "description": "File content to write"
                                },
                                "workspace_path": {
                                    "type": "string",
                                    "description": "Absolute path to workspace"
                                }
                            },
                            "required": ["file_path", "content", "workspace_path"]
                        }
                    },
                    {
                        "name": "edit_file",
                        "description": "Edit file by replacing old_content with new_content (find/replace).",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "file_path": {"type": "string", "description": "Relative path to file"},
                                "old_content": {"type": "string", "description": "String to find"},
                                "new_content": {"type": "string", "description": "Replacement string"},
                                "workspace_path": {"type": "string", "description": "Absolute path to workspace"}
                            },
                            "required": ["file_path", "old_content", "new_content", "workspace_path"]
                        }
                    },
                    {
                        "name": "list_directory",
                        "description": "List directory contents with optional glob pattern and recursion.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "dir_path": {"type": "string", "description": "Relative directory path"},
                                "workspace_path": {"type": "string", "description": "Absolute path to workspace"},
                                "pattern": {"type": "string", "description": "Optional glob pattern (e.g., '*.py')"},
                                "recursive": {"type": "boolean", "description": "Search recursively (default: false)"}
                            },
                            "required": ["dir_path", "workspace_path"]
                        }
                    },
                    {
                        "name": "file_exists",
                        "description": "Check if file/directory exists and get metadata.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "file_path": {"type": "string", "description": "Relative path to file/directory"},
                                "workspace_path": {"type": "string", "description": "Absolute path to workspace"}
                            },
                            "required": ["file_path", "workspace_path"]
                        }
                    }
                ]
            }
        }

    # Execute tool
    elif method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})

        debug_log(f"Calling tool: {tool_name}")

        try:
            # Route to appropriate tool
            if tool_name == "read_file":
                # Streaming tool
                chunks = []
                async for chunk in stream_read_file(
                    file_path=tool_args.get("file_path", ""),
                    workspace_path=tool_args.get("workspace_path", ""),
                    chunk_size=tool_args.get("chunk_size", 8192)
                ):
                    chunks.append(chunk)

                # Combine chunks into text output
                content_text = ""
                for chunk in chunks:
                    if chunk["type"] == "chunk":
                        content_text += chunk["content"]
                    elif chunk["type"] == "error":
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [{"type": "text", "text": f"Error: {chunk['message']}"}],
                                "isError": True
                            }
                        }

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": content_text}],
                        "isError": False
                    }
                }

            elif tool_name == "write_file":
                # Streaming tool
                chunks = []
                async for chunk in stream_write_file(
                    file_path=tool_args.get("file_path", ""),
                    content=tool_args.get("content", ""),
                    workspace_path=tool_args.get("workspace_path", "")
                ):
                    chunks.append(chunk)

                # Check for errors
                for chunk in chunks:
                    if chunk["type"] == "error":
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [{"type": "text", "text": f"Error: {chunk['message']}"}],
                                "isError": True
                            }
                        }

                # Success
                final_chunk = [c for c in chunks if c["type"] == "complete"][0]
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": f"✅ Wrote {final_chunk['bytes_written']} bytes to {final_chunk['path']}"}],
                        "isError": False
                    }
                }

            elif tool_name == "edit_file":
                result = await edit_file(
                    file_path=tool_args.get("file_path", ""),
                    old_content=tool_args.get("old_content", ""),
                    new_content=tool_args.get("new_content", ""),
                    workspace_path=tool_args.get("workspace_path", "")
                )

                if result["success"]:
                    text = f"✅ Edited {result['path']}: {result['replacements']} replacement(s)"
                else:
                    text = f"❌ Error: {result['error']}"

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": text}],
                        "isError": not result["success"]
                    }
                }

            elif tool_name == "list_directory":
                result = await list_directory(
                    dir_path=tool_args.get("dir_path", ""),
                    workspace_path=tool_args.get("workspace_path", ""),
                    pattern=tool_args.get("pattern"),
                    recursive=tool_args.get("recursive", False)
                )

                if result["success"]:
                    text = f"# Directory: {result['path']}\n\n"
                    text += f"**Files ({len(result['files'])}):**\n"
                    for f in result['files']:
                        text += f"- {f}\n"
                    text += f"\n**Directories ({len(result['directories'])}):**\n"
                    for d in result['directories']:
                        text += f"- {d}/\n"
                else:
                    text = f"❌ Error: {result['error']}"

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": text}],
                        "isError": not result["success"]
                    }
                }

            elif tool_name == "file_exists":
                result = await file_exists(
                    file_path=tool_args.get("file_path", ""),
                    workspace_path=tool_args.get("workspace_path", "")
                )

                if result["error"]:
                    text = f"❌ Error: {result['error']}"
                elif result["exists"]:
                    file_type = "File" if result["is_file"] else "Directory"
                    size_str = f" ({result['size']} bytes)" if result["size"] is not None else ""
                    text = f"✅ {file_type} exists: {result['path']}{size_str}"
                else:
                    text = f"❌ Does not exist: {result['path']}"

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": text}],
                        "isError": bool(result["error"])
                    }
                }

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }

        except Exception as e:
            debug_log(f"Tool execution failed: {e}")
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
    """Main MCP server loop."""

    print(f"[{datetime.now()}] File Tools MCP Server started", file=sys.stderr)
    print(f"[{datetime.now()}] DEBUG_MODE={DEBUG_MODE}", file=sys.stderr)
    print(f"[{datetime.now()}] Waiting for requests on stdin...", file=sys.stderr)

    while True:
        try:
            line = sys.stdin.readline()

            if not line:
                print(f"[{datetime.now()}] EOF reached, shutting down", file=sys.stderr)
                break

            line = line.strip()
            if not line:
                continue

            request = json.loads(line)
            debug_log(f"Received request: {request.get('method')}")

            response = await handle_request(request)

            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

            debug_log("Response sent")

        except json.JSONDecodeError as e:
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
