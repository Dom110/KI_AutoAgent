"""
File Tools for Codesmith Agent

Provides file system operations for code generation.
Follows Asimov safety rules (TODO: Phase 8).

Documentation:
- LangChain Tool: https://python.langchain.com/docs/modules/tools/
- File Operations: Safe, workspace-scoped only

Integration:
- Codesmith Subgraph: Used by create_react_agent()
- Asimov: Requires can_write_files permission (TODO: Phase 8)
"""

from __future__ import annotations

import logging
import os
from typing import Any

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
async def read_file(file_path: str, workspace_path: str) -> dict[str, Any]:
    """
    Read a file from the workspace.

    Args:
        file_path: Relative path to file (e.g., "src/App.tsx")
        workspace_path: Absolute path to workspace root

    Returns:
        dict with:
            - content: str (file contents)
            - path: str (absolute path)
            - success: bool

    Example:
        result = await read_file("src/App.tsx", "/Users/me/project")
        print(result["content"])

    Safety:
        - Only reads files within workspace_path
        - Returns error if file outside workspace
        - TODO Phase 8: Asimov permission check
    """
    logger.info(f"📖 Reading file: {file_path}")

    try:
        # Safety: Ensure file is within workspace
        abs_path = os.path.abspath(os.path.join(workspace_path, file_path))
        abs_workspace = os.path.abspath(workspace_path)

        if not abs_path.startswith(abs_workspace):
            logger.error(f"❌ File outside workspace: {file_path}")
            return {
                "content": "",
                "path": file_path,
                "success": False,
                "error": "File path outside workspace (security violation)"
            }

        # Read file
        if not os.path.exists(abs_path):
            logger.warning(f"⚠️ File not found: {file_path}")
            return {
                "content": "",
                "path": file_path,
                "success": False,
                "error": "File not found"
            }

        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()

        logger.info(f"✅ Read {len(content)} chars from {file_path}")

        return {
            "content": content,
            "path": file_path,
            "success": True
        }

    except Exception as e:
        logger.error(f"❌ Read file failed: {e}", exc_info=True)
        return {
            "content": "",
            "path": file_path,
            "success": False,
            "error": str(e)
        }


@tool
async def write_file(
    file_path: str,
    content: str,
    workspace_path: str
) -> dict[str, Any]:
    """
    Write a file to the workspace.

    Args:
        file_path: Relative path to file (e.g., "src/App.tsx")
        content: File content to write
        workspace_path: Absolute path to workspace root

    Returns:
        dict with:
            - path: str (file path)
            - bytes_written: int
            - success: bool

    Example:
        result = await write_file(
            "src/App.tsx",
            "import React from 'react'...",
            "/Users/me/project"
        )

    Safety:
        - Only writes files within workspace_path
        - Creates parent directories automatically
        - Returns error if file outside workspace
        - TODO Phase 8: Asimov permission check
    """
    logger.info(f"✍️ Writing file: {file_path} ({len(content)} chars)")

    try:
        # Safety: Ensure file is within workspace
        abs_path = os.path.abspath(os.path.join(workspace_path, file_path))
        abs_workspace = os.path.abspath(workspace_path)

        if not abs_path.startswith(abs_workspace):
            logger.error(f"❌ File outside workspace: {file_path}")
            return {
                "path": file_path,
                "bytes_written": 0,
                "success": False,
                "error": "File path outside workspace (security violation)"
            }

        # Create parent directories if needed
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        # Write file
        with open(abs_path, 'w', encoding='utf-8') as f:
            bytes_written = f.write(content)

        logger.info(f"✅ Wrote {bytes_written} chars to {file_path}")

        return {
            "path": file_path,
            "bytes_written": bytes_written,
            "success": True
        }

    except Exception as e:
        logger.error(f"❌ Write file failed: {e}", exc_info=True)
        return {
            "path": file_path,
            "bytes_written": 0,
            "success": False,
            "error": str(e)
        }


@tool
async def edit_file(
    file_path: str,
    old_content: str,
    new_content: str,
    workspace_path: str
) -> dict[str, Any]:
    """
    Edit a file by replacing old_content with new_content.

    Args:
        file_path: Relative path to file
        old_content: String to find and replace
        new_content: Replacement string
        workspace_path: Absolute path to workspace root

    Returns:
        dict with:
            - path: str
            - replacements: int (number of replacements made)
            - success: bool

    Example:
        result = await edit_file(
            "src/App.tsx",
            "console.log('old')",
            "console.log('new')",
            "/Users/me/project"
        )

    Safety:
        - Only edits files within workspace_path
        - Returns error if old_content not found
        - TODO Phase 8: Asimov permission check
    """
    logger.info(f"✏️ Editing file: {file_path}")

    try:
        # Safety: Ensure file is within workspace
        abs_path = os.path.abspath(os.path.join(workspace_path, file_path))
        abs_workspace = os.path.abspath(workspace_path)

        if not abs_path.startswith(abs_workspace):
            logger.error(f"❌ File outside workspace: {file_path}")
            return {
                "path": file_path,
                "replacements": 0,
                "success": False,
                "error": "File path outside workspace (security violation)"
            }

        # Read current content
        if not os.path.exists(abs_path):
            logger.error(f"❌ File not found: {file_path}")
            return {
                "path": file_path,
                "replacements": 0,
                "success": False,
                "error": "File not found"
            }

        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if old_content exists
        if old_content not in content:
            logger.warning(f"⚠️ Old content not found in {file_path}")
            return {
                "path": file_path,
                "replacements": 0,
                "success": False,
                "error": "Old content not found in file"
            }

        # Replace
        new_file_content = content.replace(old_content, new_content)
        replacements = content.count(old_content)

        # Write back
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(new_file_content)

        logger.info(f"✅ Edited {file_path}: {replacements} replacements")

        return {
            "path": file_path,
            "replacements": replacements,
            "success": True
        }

    except Exception as e:
        logger.error(f"❌ Edit file failed: {e}", exc_info=True)
        return {
            "path": file_path,
            "replacements": 0,
            "success": False,
            "error": str(e)
        }


# Export
__all__ = ["read_file", "write_file", "edit_file"]
