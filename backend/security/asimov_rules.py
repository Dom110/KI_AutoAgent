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
# ASIMOV RULE 3: GLOBAL ERROR SEARCH (not applicable to single-file checks)
# ============================================================================
# Rule 3 is enforced at the workflow level by ReviewFix agent
# It requires project-wide analysis, not single-file validation


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
    "format_violations_report"
]
