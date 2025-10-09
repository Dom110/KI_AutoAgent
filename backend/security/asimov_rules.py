"""
Asimov Security Rules for KI AutoAgent v6.0

Enforces the three fundamental Asimov Rules:
1. NO FALLBACKS without documented reason
2. COMPLETE IMPLEMENTATION (no TODOs, no partial work)
3. GLOBAL ERROR SEARCH (fix ALL instances, not just one)

These rules are enforced by:
- File Tools (write_file, edit_file)
- ReviewFix Agent (ENFORCER role)
- Codesmith Agent (validation before writing)

Author: KI AutoAgent Team
Version: 6.0.0
Python: 3.13+
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================================
# ASIMOV RULE 1: NO FALLBACKS WITHOUT DOCUMENTED REASON
# ============================================================================

def check_fallback_violations(code: str, file_path: str) -> list[dict[str, Any]]:
    """
    Check for fallback patterns without proper documentation.

    Violation patterns:
    - try/except with generic Exception
    - if/else fallbacks without comments
    - default values without explanation

    Args:
        code: Code content to check
        file_path: File path for context

    Returns:
        List of violations with line numbers and descriptions
    """
    violations = []
    lines = code.split('\n')

    # Pattern 1: Generic except without comment
    for i, line in enumerate(lines, 1):
        if re.search(r'except\s+(Exception|BaseException):', line):
            # Check if previous line has FALLBACK comment
            if i > 1:
                prev_line = lines[i-2]
                if '# ⚠️ FALLBACK:' not in prev_line and '# FALLBACK:' not in prev_line:
                    violations.append({
                        "rule": "ASIMOV-1",
                        "line": i,
                        "type": "undocumented_fallback",
                        "description": f"Generic exception handler without FALLBACK documentation",
                        "severity": "warning"
                    })

    # Pattern 2: Fallback to default without reason
    fallback_patterns = [
        r'or\s+\w+_fallback',
        r'if\s+not\s+\w+:\s*\w+\s*=\s*\w+_fallback',
        r'\.get\([^,]+,\s*["\'].*fallback.*["\']',
    ]

    for pattern in fallback_patterns:
        for i, line in enumerate(lines, 1):
            if re.search(pattern, line, re.IGNORECASE):
                # Check for documentation
                context_start = max(0, i-3)
                context = '\n'.join(lines[context_start:i])
                if '# ⚠️ FALLBACK:' not in context and '# FALLBACK:' not in context:
                    violations.append({
                        "rule": "ASIMOV-1",
                        "line": i,
                        "type": "undocumented_fallback",
                        "description": "Fallback pattern detected without documentation",
                        "severity": "warning"
                    })

    return violations


# ============================================================================
# ASIMOV RULE 2: COMPLETE IMPLEMENTATION (NO TODOs)
# ============================================================================

def check_incomplete_implementation(code: str, file_path: str) -> list[dict[str, Any]]:
    """
    Check for incomplete implementations.

    Violation patterns:
    - TODO comments
    - FIXME comments
    - NotImplementedError
    - pass in function bodies
    - ... (ellipsis) in function bodies

    Args:
        code: Code content to check
        file_path: File path for context

    Returns:
        List of violations
    """
    violations = []
    lines = code.split('\n')

    incomplete_patterns = [
        (r'#\s*TODO', "TODO comment found - implement before committing"),
        (r'#\s*FIXME', "FIXME comment found - fix before committing"),
        (r'raise\s+NotImplementedError', "NotImplementedError - function not implemented"),
        (r'^\s+pass\s*$', "Empty pass statement - implement functionality"),
        (r'^\s+\.\.\.\s*$', "Ellipsis placeholder - implement functionality"),
    ]

    for pattern, description in incomplete_patterns:
        for i, line in enumerate(lines, 1):
            if re.search(pattern, line):
                violations.append({
                    "rule": "ASIMOV-2",
                    "line": i,
                    "type": "incomplete_implementation",
                    "description": description,
                    "severity": "error"  # Hard error for incomplete code
                })

    return violations


# ============================================================================
# ASIMOV RULE 3: GLOBAL ERROR SEARCH
# ============================================================================
# Rule 3 is enforced at the workflow level by ReviewFix agent
# It requires project-wide analysis to find ALL instances of an error

async def perform_global_error_search(
    workspace_path: str,
    error_pattern: str,
    file_extensions: list[str] | None = None
) -> dict[str, Any]:
    """
    Search entire workspace for all instances of an error pattern.

    When an error is found, this function searches the ENTIRE workspace
    to find ALL instances, not just the one that was reported.

    Args:
        workspace_path: Path to workspace root
        error_pattern: Pattern to search for (regex or literal string)
        file_extensions: List of file extensions to search (e.g., ['.py', '.js'])
                        If None, searches all text files

    Returns:
        dict with:
            - total_matches: int (total number of matches found)
            - files: list[str] (files containing matches)
            - matches: list[dict] with:
                - file: str (file path relative to workspace)
                - line: int (line number)
                - content: str (line content)
                - match: str (matched text)
            - search_pattern: str (pattern that was searched)
            - workspace: str (workspace path)

    Example:
        # Error found: "databse_connection" (typo)
        result = await perform_global_error_search(
            workspace_path="/path/to/project",
            error_pattern="databse_connection",
            file_extensions=[".py"]
        )
        # Returns: {"total_matches": 3, "files": ["api.py", "models.py", "utils.py"], ...}
    """
    import asyncio
    import subprocess
    from pathlib import Path

    logger.info(f"🔍 ASIMOV RULE 3: Global search for pattern: {error_pattern}")

    workspace = Path(workspace_path)
    if not workspace.exists():
        logger.error(f"❌ Workspace not found: {workspace_path}")
        return {
            "total_matches": 0,
            "files": [],
            "matches": [],
            "search_pattern": error_pattern,
            "workspace": workspace_path,
            "error": "workspace_not_found"
        }

    # Build ripgrep command
    rg_cmd = ["rg", "--json", "--line-number", error_pattern]

    # Add file type filters if specified
    if file_extensions:
        for ext in file_extensions:
            # Remove leading dot if present
            ext_clean = ext.lstrip('.')
            rg_cmd.extend(["-t", ext_clean])

    logger.debug(f"📡 Running command: {' '.join(rg_cmd)}")
    logger.debug(f"   In directory: {workspace_path}")

    try:
        # Run ripgrep asynchronously
        process = await asyncio.create_subprocess_exec(
            *rg_cmd,
            cwd=workspace_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        # Parse ripgrep JSON output
        matches = []
        files_set = set()

        for line in stdout.decode().splitlines():
            if not line.strip():
                continue

            try:
                import json
                entry = json.loads(line)

                # ripgrep JSON format: {"type": "match", "data": {...}}
                if entry.get("type") == "match":
                    data = entry.get("data", {})
                    path = data.get("path", {}).get("text", "")
                    line_number = data.get("line_number", 0)
                    line_content = data.get("lines", {}).get("text", "").rstrip()

                    # Extract the actual matched text
                    submatches = data.get("submatches", [])
                    match_text = submatches[0].get("match", {}).get("text", "") if submatches else error_pattern

                    matches.append({
                        "file": path,
                        "line": line_number,
                        "content": line_content,
                        "match": match_text
                    })

                    files_set.add(path)

            except json.JSONDecodeError:
                logger.warning(f"⚠️  Failed to parse ripgrep JSON line: {line[:100]}")
                continue

        total_matches = len(matches)
        files = sorted(list(files_set))

        logger.info(f"✅ Global search complete:")
        logger.info(f"   Pattern: '{error_pattern}'")
        logger.info(f"   Matches: {total_matches}")
        logger.info(f"   Files: {len(files)}")

        if total_matches > 0:
            logger.info(f"   Files with matches:")
            for file in files:
                file_matches = [m for m in matches if m["file"] == file]
                logger.info(f"      - {file} ({len(file_matches)} matches)")

        return {
            "total_matches": total_matches,
            "files": files,
            "matches": matches,
            "search_pattern": error_pattern,
            "workspace": workspace_path
        }

    except FileNotFoundError:
        # ripgrep not installed - fallback to Python implementation
        logger.warning("⚠️  ripgrep not found - using Python fallback")
        return await _python_global_search(workspace_path, error_pattern, file_extensions)

    except Exception as e:
        logger.error(f"❌ Global search failed: {e}", exc_info=True)
        return {
            "total_matches": 0,
            "files": [],
            "matches": [],
            "search_pattern": error_pattern,
            "workspace": workspace_path,
            "error": str(e)
        }


async def _python_global_search(
    workspace_path: str,
    error_pattern: str,
    file_extensions: list[str] | None = None
) -> dict[str, Any]:
    """
    Python fallback for global search when ripgrep is not available.

    Uses pathlib and regex to search files.
    """
    import re
    from pathlib import Path

    logger.debug("🐍 Using Python fallback for global search")

    workspace = Path(workspace_path)
    matches = []
    files_set = set()

    # Compile regex pattern
    try:
        pattern = re.compile(error_pattern)
    except re.error:
        # If not valid regex, treat as literal string
        pattern = re.compile(re.escape(error_pattern))

    # Determine which files to search
    if file_extensions:
        extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in file_extensions]
        search_patterns = [f"**/*{ext}" for ext in extensions]
    else:
        # Search common text file extensions
        search_patterns = ["**/*.py", "**/*.js", "**/*.ts", "**/*.jsx", "**/*.tsx",
                          "**/*.html", "**/*.css", "**/*.json", "**/*.md", "**/*.txt"]

    # Search files
    for search_pattern in search_patterns:
        for file_path in workspace.glob(search_pattern):
            if not file_path.is_file():
                continue

            # Skip common ignore patterns
            if any(part.startswith('.') for part in file_path.parts):
                continue
            if 'node_modules' in file_path.parts or 'venv' in file_path.parts:
                continue

            try:
                content = file_path.read_text()
                for line_num, line in enumerate(content.splitlines(), 1):
                    if pattern.search(line):
                        match = pattern.search(line)
                        matches.append({
                            "file": str(file_path.relative_to(workspace)),
                            "line": line_num,
                            "content": line.strip(),
                            "match": match.group(0) if match else error_pattern
                        })
                        files_set.add(str(file_path.relative_to(workspace)))

            except (UnicodeDecodeError, PermissionError):
                # Skip binary files or files we can't read
                continue

    total_matches = len(matches)
    files = sorted(list(files_set))

    logger.info(f"✅ Python search complete: {total_matches} matches in {len(files)} files")

    return {
        "total_matches": total_matches,
        "files": files,
        "matches": matches,
        "search_pattern": error_pattern,
        "workspace": workspace_path
    }


# ============================================================================
# MAIN VALIDATOR
# ============================================================================

def validate_asimov_rules(
    code: str,
    file_path: str,
    strict: bool = False
) -> dict[str, Any]:
    """
    Validate code against all Asimov Rules.

    Args:
        code: Code content to validate
        file_path: File path for context
        strict: If True, warnings are treated as errors

    Returns:
        dict with:
        - valid: bool (True if no violations)
        - violations: list of violation dicts
        - summary: dict with counts by severity
    """
    violations = []

    # Rule 1: No Fallbacks
    violations.extend(check_fallback_violations(code, file_path))

    # Rule 2: Complete Implementation
    violations.extend(check_incomplete_implementation(code, file_path))

    # Count by severity
    errors = [v for v in violations if v["severity"] == "error"]
    warnings = [v for v in violations if v["severity"] == "warning"]

    # In strict mode, warnings are errors
    if strict:
        errors.extend(warnings)
        warnings = []

    is_valid = len(errors) == 0

    summary = {
        "total": len(violations),
        "errors": len(errors),
        "warnings": len(warnings)
    }

    return {
        "valid": is_valid,
        "violations": violations,
        "summary": summary
    }


def format_violations_report(
    validation_result: dict[str, Any],
    file_path: str
) -> str:
    """
    Format validation result as human-readable report.

    Args:
        validation_result: Result from validate_asimov_rules()
        file_path: File path for header

    Returns:
        Formatted report string
    """
    violations = validation_result["violations"]
    summary = validation_result["summary"]

    if validation_result["valid"]:
        return f"✅ {file_path}: No Asimov violations"

    report = [
        f"🔴 ASIMOV VIOLATIONS in {file_path}",
        f"Total: {summary['total']} ({summary['errors']} errors, {summary['warnings']} warnings)",
        ""
    ]

    for v in violations:
        icon = "❌" if v["severity"] == "error" else "⚠️"
        report.append(f"{icon} Line {v['line']}: [{v['rule']}] {v['description']}")

    return '\n'.join(report)


# Export
__all__ = [
    "validate_asimov_rules",
    "check_fallback_violations",
    "check_incomplete_implementation",
    "format_violations_report",
    "perform_global_error_search"
]
