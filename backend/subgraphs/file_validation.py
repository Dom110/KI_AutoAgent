"""
File Validation Module for Codesmith Agent

Validates that all required files are generated based on app type.
Provides retry mechanism for incomplete generation.

Author: KI AutoAgent Team
Date: 2025-10-11
Python: 3.13+
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


# ============================================================================
# REQUIRED FILES DEFINITIONS
# ============================================================================

REQUIRED_FILES_BY_TYPE: Dict[str, List[str]] = {
    "react_vite_ts": [
        # Entry files (CRITICAL)
        "src/main.tsx",
        "src/App.tsx",
        "src/index.css",

        # Configuration (CRITICAL)
        "package.json",
        "tsconfig.json",
        "vite.config.ts",
        "index.html",

        # Optional but recommended
        "tailwind.config.js",
        "postcss.config.js",
        "README.md",
    ],

    "react_vite_js": [
        "src/main.jsx",
        "src/App.jsx",
        "src/index.css",
        "package.json",
        "vite.config.js",
        "index.html",
    ],

    "nextjs_ts": [
        "app/page.tsx",
        "app/layout.tsx",
        "app/globals.css",
        "package.json",
        "tsconfig.json",
        "next.config.js",
        "README.md",
    ],

    "python_fastapi": [
        "main.py",
        "requirements.txt",
        "README.md",
    ],

    "python_flask": [
        "app.py",
        "requirements.txt",
        "README.md",
    ],

    "generic": [
        "README.md",
    ]
}


# Critical files that MUST exist (app won't run without them)
CRITICAL_FILES_BY_TYPE: Dict[str, List[str]] = {
    "react_vite_ts": [
        "src/main.tsx",
        "src/App.tsx",
        "src/index.css",
        "package.json",
        "index.html",
    ],

    "react_vite_js": [
        "src/main.jsx",
        "src/App.jsx",
        "package.json",
        "index.html",
    ],

    "nextjs_ts": [
        "app/page.tsx",
        "app/layout.tsx",
        "package.json",
    ],

    "python_fastapi": [
        "main.py",
        "requirements.txt",
    ],

    "python_flask": [
        "app.py",
        "requirements.txt",
    ],
}


# ============================================================================
# APP TYPE DETECTION
# ============================================================================

def detect_app_type(design: str, generated_files: List[Dict]) -> str:
    """
    Detect app type from design document and generated files.

    Args:
        design: Architecture design document
        generated_files: List of generated files with paths

    Returns:
        App type identifier (e.g., "react_vite_ts")
    """
    design_lower = design.lower()

    # Check file extensions
    file_paths = [f.get("path", "") for f in generated_files]
    has_tsx = any(p.endswith(".tsx") for p in file_paths)
    has_jsx = any(p.endswith(".jsx") for p in file_paths)
    has_py = any(p.endswith(".py") for p in file_paths)

    # Detect by design keywords and files
    if "react" in design_lower and "vite" in design_lower:
        if has_tsx or "typescript" in design_lower:
            return "react_vite_ts"
        elif has_jsx:
            return "react_vite_js"

    if "next" in design_lower or "nextjs" in design_lower:
        return "nextjs_ts"

    if "fastapi" in design_lower and has_py:
        return "python_fastapi"

    if "flask" in design_lower and has_py:
        return "python_flask"

    # Default to generic if can't determine
    logger.warning("⚠️ Could not determine specific app type, using 'generic'")
    return "generic"


# ============================================================================
# FILE VALIDATION
# ============================================================================

def validate_generated_files(
    workspace_path: str,
    generated_files: List[Dict],
    app_type: str | None = None,
    design: str = ""
) -> Dict[str, any]:
    """
    Validate that all required files were generated.

    Args:
        workspace_path: Path to workspace
        generated_files: List of generated file dicts with 'path' key
        app_type: Optional app type override
        design: Design document (for app type detection)

    Returns:
        {
            "valid": bool,
            "app_type": str,
            "missing_files": List[str],
            "missing_critical": List[str],
            "generated_count": int,
            "required_count": int,
            "completeness": float  # 0.0 to 1.0
        }
    """
    logger.info("🔍 Validating generated files...")

    # Detect app type if not provided
    if not app_type:
        app_type = detect_app_type(design, generated_files)

    logger.info(f"📋 App type detected: {app_type}")

    # Get required files for this app type
    required_files = REQUIRED_FILES_BY_TYPE.get(app_type, REQUIRED_FILES_BY_TYPE["generic"])
    critical_files = CRITICAL_FILES_BY_TYPE.get(app_type, [])

    # Extract generated file paths
    generated_paths = {f.get("path", "").strip() for f in generated_files}

    # Check which files exist on filesystem
    workspace = Path(workspace_path)
    existing_files = set()

    for file_path in required_files:
        full_path = workspace / file_path
        if full_path.exists():
            existing_files.add(file_path)

    # Find missing files
    required_set = set(required_files)
    missing_files = required_set - existing_files

    # Find missing critical files
    critical_set = set(critical_files)
    missing_critical = critical_set - existing_files

    # Calculate completeness
    if required_files:
        completeness = len(existing_files) / len(required_files)
    else:
        completeness = 1.0

    # Validation passes if all CRITICAL files exist
    valid = len(missing_critical) == 0

    result = {
        "valid": valid,
        "app_type": app_type,
        "missing_files": sorted(missing_files),
        "missing_critical": sorted(missing_critical),
        "generated_count": len(existing_files),
        "required_count": len(required_files),
        "completeness": completeness,
        "generated_paths": list(generated_paths),
        "existing_files": sorted(existing_files)
    }

    # Log results
    if valid:
        logger.info(f"✅ File validation PASSED")
        logger.info(f"   Generated: {len(existing_files)}/{len(required_files)} files ({completeness*100:.1f}%)")

        if missing_files:
            logger.warning(f"   Missing optional files: {', '.join(missing_files)}")
    else:
        logger.error(f"❌ File validation FAILED")
        logger.error(f"   Generated: {len(existing_files)}/{len(required_files)} files ({completeness*100:.1f}%)")
        logger.error(f"   Missing CRITICAL files: {', '.join(missing_critical)}")

        if missing_files - critical_set:
            logger.warning(f"   Missing optional files: {', '.join(missing_files - critical_set)}")

    return result


# ============================================================================
# MISSING FILES PROMPT GENERATOR
# ============================================================================

def generate_completion_prompt(validation_result: Dict, design: str) -> str:
    """
    Generate prompt to complete missing files.

    Args:
        validation_result: Result from validate_generated_files()
        design: Original design document

    Returns:
        Prompt string for Claude to generate missing files
    """
    missing = validation_result["missing_files"]
    missing_critical = validation_result["missing_critical"]
    app_type = validation_result["app_type"]

    if not missing:
        return ""  # Nothing to complete

    prompt = f"""Your previous generation was incomplete. You generated {validation_result['generated_count']}/{validation_result['required_count']} files.

## Missing CRITICAL Files
These files are REQUIRED for the app to run:
"""

    for file in missing_critical:
        prompt += f"- {file}\n"

    if missing - set(missing_critical):
        prompt += f"""
## Missing Optional Files
These files are recommended but not critical:
"""
        for file in (missing - set(missing_critical)):
            prompt += f"- {file}\n"

    prompt += f"""

## Task
Generate ONLY the missing files listed above.

Use the same FILE: format as before:

FILE: <path>
```<language>
<code>
```

Remember the context from the original design:
{design[:500]}...

Generate complete, production-ready code for the missing files.
START YOUR RESPONSE WITH "FILE:" - Nothing else!"""

    return prompt


# ============================================================================
# RETRY LOGIC
# ============================================================================

async def retry_incomplete_generation(
    llm: any,
    validation_result: Dict,
    design: str,
    workspace_path: str,
    write_file_func: any,
    max_retries: int = 2
) -> Dict:
    """
    Retry generation for missing files.

    Args:
        llm: LLM instance for code generation
        validation_result: Result from validate_generated_files()
        design: Original design document
        workspace_path: Workspace path
        write_file_func: Function to write files
        max_retries: Maximum retry attempts

    Returns:
        Updated validation result after retries
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    for attempt in range(max_retries):
        if validation_result["valid"]:
            logger.info(f"✅ All critical files present after {attempt} retries")
            return validation_result

        logger.warning(f"🔄 Retry {attempt + 1}/{max_retries} - Generating missing files...")
        logger.info(f"   Missing: {', '.join(validation_result['missing_critical'])}")

        # Generate prompt for missing files
        completion_prompt = generate_completion_prompt(validation_result, design)

        if not completion_prompt:
            break  # Nothing to complete

        # Call LLM to generate missing files
        try:
            system_prompt = """You are completing a partially generated application.
Generate ONLY the missing files requested. Use the exact FILE: format."""

            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=completion_prompt)
            ])

            code_output = response.content if hasattr(response, 'content') else str(response)

            # Parse and write missing files (simplified - reuse codesmith parser)
            # For now, just log that we attempted
            logger.info(f"📝 Generated completion response: {len(code_output)} chars")

            # Re-validate after retry
            # (In production, this would parse and write files, then re-validate)
            # For now, we'll just return the result

        except Exception as e:
            logger.error(f"❌ Retry {attempt + 1} failed: {e}")
            continue

    logger.error(f"❌ Failed to complete generation after {max_retries} retries")
    return validation_result
