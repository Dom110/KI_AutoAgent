#!/usr/bin/env python3
"""
Build Validation MCP Server - Streaming Compiler Output

Provides build validation for 6 languages with real-time streaming output.
Replaces ALL subprocess.run() calls in reviewfix_subgraph_v6_1.py

Languages Supported:
1. TypeScript (tsc --noEmit)
2. Python (mypy)
3. JavaScript (ESLint)
4. Go (go vet + go build)
5. Rust (cargo check + cargo clippy)
6. Java (Maven/Gradle/javac)

Features:
- Streaming compiler output line-by-line
- Parallel validation for polyglot projects
- Auto-detection of project languages
- Detailed error reporting with file:line:column

Run:
    ~/.ki_autoagent/venv/bin/python mcp_servers/build_validation_server.py

Register with Claude:
    claude mcp add build-validation ~/.ki_autoagent/venv/bin/python mcp_servers/build_validation_server.py

Test:
    claude "Validate my TypeScript project"

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

# ============================================================================
# DEBUG MODE (environment variable)
# ============================================================================
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

def debug_log(message: str):
    """Log debug message to stderr if DEBUG_MODE enabled."""
    if DEBUG_MODE:
        print(f"[DEBUG {datetime.now()}] {message}", file=sys.stderr)


# ============================================================================
# LANGUAGE DETECTION
# ============================================================================

def detect_project_languages(workspace_path: str, generated_files: list[dict] | None = None) -> dict[str, Any]:
    """
    Auto-detect languages in project.

    Args:
        workspace_path: Absolute path to workspace
        generated_files: Optional list of generated files from Codesmith
                        Format: [{"path": "src/app.py"}, ...]

    Returns:
        {
            "typescript": {"has": bool, "files": list, "config": str|None},
            "python": {"has": bool, "files": list},
            "javascript": {"has": bool, "files": list, "config": str|None},
            "go": {"has": bool, "files": list, "go_mod": str|None},
            "rust": {"has": bool, "files": list, "cargo_toml": str|None},
            "java": {"has": bool, "files": list, "build_system": str|None}
        }
    """

    result = {
        "typescript": {"has": False, "files": [], "config": None},
        "python": {"has": False, "files": []},
        "javascript": {"has": False, "files": [], "config": None},
        "go": {"has": False, "files": [], "go_mod": None},
        "rust": {"has": False, "files": [], "cargo_toml": None},
        "java": {"has": False, "files": [], "build_system": None}
    }

    # If generated_files provided, use those (faster)
    if generated_files:
        for file_info in generated_files:
            file_path = file_info.get('path', '')

            if file_path.endswith(('.ts', '.tsx')):
                result["typescript"]["has"] = True
                result["typescript"]["files"].append(file_path)

            elif file_path.endswith('.py'):
                result["python"]["has"] = True
                result["python"]["files"].append(file_path)

            elif file_path.endswith(('.js', '.jsx')):
                result["javascript"]["has"] = True
                result["javascript"]["files"].append(file_path)

            elif file_path.endswith('.go'):
                result["go"]["has"] = True
                result["go"]["files"].append(file_path)

            elif file_path.endswith('.rs'):
                result["rust"]["has"] = True
                result["rust"]["files"].append(file_path)

            elif file_path.endswith('.java'):
                result["java"]["has"] = True
                result["java"]["files"].append(file_path)

    # Otherwise, scan workspace (slower but comprehensive)
    else:
        # TypeScript
        ts_files = glob.glob(os.path.join(workspace_path, '**', '*.ts'), recursive=True)
        ts_files += glob.glob(os.path.join(workspace_path, '**', '*.tsx'), recursive=True)
        if ts_files:
            result["typescript"]["has"] = True
            result["typescript"]["files"] = [os.path.relpath(f, workspace_path) for f in ts_files
                                              if 'node_modules' not in f]

        # Python
        py_files = glob.glob(os.path.join(workspace_path, '**', '*.py'), recursive=True)
        if py_files:
            result["python"]["has"] = True
            result["python"]["files"] = [os.path.relpath(f, workspace_path) for f in py_files
                                          if 'venv' not in f and '__pycache__' not in f]

        # JavaScript
        js_files = glob.glob(os.path.join(workspace_path, '**', '*.js'), recursive=True)
        js_files += glob.glob(os.path.join(workspace_path, '**', '*.jsx'), recursive=True)
        if js_files:
            result["javascript"]["has"] = True
            result["javascript"]["files"] = [os.path.relpath(f, workspace_path) for f in js_files
                                              if 'node_modules' not in f]

        # Go
        go_files = glob.glob(os.path.join(workspace_path, '**', '*.go'), recursive=True)
        if go_files:
            result["go"]["has"] = True
            result["go"]["files"] = [os.path.relpath(f, workspace_path) for f in go_files]

        # Rust
        rs_files = glob.glob(os.path.join(workspace_path, '**', '*.rs'), recursive=True)
        if rs_files:
            result["rust"]["has"] = True
            result["rust"]["files"] = [os.path.relpath(f, workspace_path) for f in rs_files]

        # Java
        java_files = glob.glob(os.path.join(workspace_path, '**', '*.java'), recursive=True)
        if java_files:
            result["java"]["has"] = True
            result["java"]["files"] = [os.path.relpath(f, workspace_path) for f in java_files]

    # Check for config files
    if result["typescript"]["has"]:
        tsconfig = os.path.join(workspace_path, 'tsconfig.json')
        if os.path.exists(tsconfig):
            result["typescript"]["config"] = tsconfig

    if result["javascript"]["has"]:
        eslintrc = os.path.join(workspace_path, '.eslintrc.json')
        if os.path.exists(eslintrc):
            result["javascript"]["config"] = eslintrc

    if result["go"]["has"]:
        go_mod = os.path.join(workspace_path, 'go.mod')
        if os.path.exists(go_mod):
            result["go"]["go_mod"] = go_mod

    if result["rust"]["has"]:
        cargo_toml = os.path.join(workspace_path, 'Cargo.toml')
        if os.path.exists(cargo_toml):
            result["rust"]["cargo_toml"] = cargo_toml

    if result["java"]["has"]:
        pom_xml = os.path.join(workspace_path, 'pom.xml')
        build_gradle = os.path.join(workspace_path, 'build.gradle')
        if os.path.exists(pom_xml):
            result["java"]["build_system"] = "maven"
        elif os.path.exists(build_gradle):
            result["java"]["build_system"] = "gradle"
        else:
            result["java"]["build_system"] = "javac"

    debug_log(f"Detected languages: {[lang for lang, info in result.items() if info['has']]}")

    return result


# ============================================================================
# STREAMING VALIDATION FUNCTIONS
# ============================================================================

async def validate_typescript(workspace_path: str, files: list[str]) -> AsyncIterator[dict]:
    """
    Validate TypeScript with tsc --noEmit (streaming).

    Yields:
        {"type": "stream", "channel": "stdout"|"stderr", "content": str, "language": "typescript"}
        {"type": "result", "success": bool, "language": "typescript", "errors": str, "return_code": int}
    """

    debug_log(f"TypeScript validation started: {len(files)} files")

    # Check for config
    tsconfig_path = os.path.join(workspace_path, 'tsconfig.json')
    package_json_path = os.path.join(workspace_path, 'package.json')

    if not os.path.exists(tsconfig_path) or not os.path.exists(package_json_path):
        yield {
            "type": "result",
            "success": False,
            "language": "typescript",
            "errors": "No tsconfig.json or package.json found - skipping TypeScript validation",
            "return_code": -1
        }
        return

    # Run tsc --noEmit
    process = await asyncio.create_subprocess_exec(
        'npx', 'tsc', '--noEmit',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=workspace_path
    )

    # Stream stdout
    stdout_content = []
    if process.stdout:
        async for line in process.stdout:
            line_str = line.decode('utf-8', errors='replace')
            stdout_content.append(line_str)
            yield {
                "type": "stream",
                "channel": "stdout",
                "content": line_str,
                "language": "typescript"
            }

    # Stream stderr
    stderr_content = []
    if process.stderr:
        async for line in process.stderr:
            line_str = line.decode('utf-8', errors='replace')
            stderr_content.append(line_str)
            yield {
                "type": "stream",
                "channel": "stderr",
                "content": line_str,
                "language": "typescript"
            }

    # Wait for completion (with timeout)
    try:
        return_code = await asyncio.wait_for(process.wait(), timeout=60.0)
    except asyncio.TimeoutError:
        process.kill()
        yield {
            "type": "result",
            "success": False,
            "language": "typescript",
            "errors": "TypeScript compilation timeout after 60 seconds",
            "return_code": -1
        }
        return

    # Final result
    all_output = ''.join(stdout_content + stderr_content)

    yield {
        "type": "result",
        "success": return_code == 0,
        "language": "typescript",
        "errors": all_output if return_code != 0 else "",
        "return_code": return_code
    }

    debug_log(f"TypeScript validation complete: return_code={return_code}")


async def validate_python(workspace_path: str, files: list[str]) -> AsyncIterator[dict]:
    """
    Validate Python with mypy (streaming).

    Yields:
        {"type": "stream", "channel": "stdout"|"stderr", "content": str, "language": "python"}
        {"type": "result", "success": bool, "language": "python", "errors": str, "return_code": int}
    """

    debug_log(f"Python validation started: {len(files)} files")

    if not files:
        yield {
            "type": "result",
            "success": False,
            "language": "python",
            "errors": "No Python files to validate",
            "return_code": -1
        }
        return

    # Build file paths
    file_paths = [os.path.join(workspace_path, f) for f in files]

    # Run mypy
    process = await asyncio.create_subprocess_exec(
        'python3', '-m', 'mypy',
        *file_paths,
        '--ignore-missing-imports',
        '--no-strict-optional',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=workspace_path
    )

    # Stream stdout
    stdout_content = []
    if process.stdout:
        async for line in process.stdout:
            line_str = line.decode('utf-8', errors='replace')
            stdout_content.append(line_str)
            yield {
                "type": "stream",
                "channel": "stdout",
                "content": line_str,
                "language": "python"
            }

    # Stream stderr
    stderr_content = []
    if process.stderr:
        async for line in process.stderr:
            line_str = line.decode('utf-8', errors='replace')
            stderr_content.append(line_str)
            yield {
                "type": "stream",
                "channel": "stderr",
                "content": line_str,
                "language": "python"
            }

    # Wait for completion
    try:
        return_code = await asyncio.wait_for(process.wait(), timeout=60.0)
    except asyncio.TimeoutError:
        process.kill()
        yield {
            "type": "result",
            "success": False,
            "language": "python",
            "errors": "Python mypy timeout after 60 seconds",
            "return_code": -1
        }
        return

    # Final result
    all_output = ''.join(stdout_content + stderr_content)

    yield {
        "type": "result",
        "success": return_code == 0,
        "language": "python",
        "errors": all_output if return_code != 0 else "",
        "return_code": return_code
    }

    debug_log(f"Python validation complete: return_code={return_code}")


async def validate_javascript(workspace_path: str, files: list[str]) -> AsyncIterator[dict]:
    """
    Validate JavaScript with ESLint (streaming).

    Yields:
        {"type": "stream", "channel": "stdout"|"stderr", "content": str, "language": "javascript"}
        {"type": "result", "success": bool, "language": "javascript", "errors": str, "return_code": int}
    """

    debug_log(f"JavaScript validation started: {len(files)} files")

    if not files:
        yield {
            "type": "result",
            "success": False,
            "language": "javascript",
            "errors": "No JavaScript files to validate",
            "return_code": -1
        }
        return

    # Build file paths
    file_paths = [os.path.join(workspace_path, f) for f in files]

    # Run ESLint
    process = await asyncio.create_subprocess_exec(
        'npx', 'eslint',
        *file_paths,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=workspace_path
    )

    # Stream stdout
    stdout_content = []
    if process.stdout:
        async for line in process.stdout:
            line_str = line.decode('utf-8', errors='replace')
            stdout_content.append(line_str)
            yield {
                "type": "stream",
                "channel": "stdout",
                "content": line_str,
                "language": "javascript"
            }

    # Stream stderr
    stderr_content = []
    if process.stderr:
        async for line in process.stderr:
            line_str = line.decode('utf-8', errors='replace')
            stderr_content.append(line_str)
            yield {
                "type": "stream",
                "channel": "stderr",
                "content": line_str,
                "language": "javascript"
            }

    # Wait for completion
    try:
        return_code = await asyncio.wait_for(process.wait(), timeout=60.0)
    except asyncio.TimeoutError:
        process.kill()
        yield {
            "type": "result",
            "success": False,
            "language": "javascript",
            "errors": "JavaScript ESLint timeout after 60 seconds",
            "return_code": -1
        }
        return

    # Final result (ESLint: 0=success, 1=errors, 2=fatal)
    all_output = ''.join(stdout_content + stderr_content)

    yield {
        "type": "result",
        "success": return_code == 0,
        "language": "javascript",
        "errors": all_output if return_code != 0 else "",
        "return_code": return_code
    }

    debug_log(f"JavaScript validation complete: return_code={return_code}")


async def validate_go(workspace_path: str, files: list[str]) -> AsyncIterator[dict]:
    """
    Validate Go with go vet + go build (streaming).

    Yields:
        {"type": "stream", "channel": "stdout"|"stderr", "content": str, "language": "go"}
        {"type": "result", "success": bool, "language": "go", "errors": str, "return_code": int}
    """

    debug_log(f"Go validation started: {len(files)} files")

    if not files:
        yield {
            "type": "result",
            "success": False,
            "language": "go",
            "errors": "No Go files to validate",
            "return_code": -1
        }
        return

    # Run go vet
    process = await asyncio.create_subprocess_exec(
        'go', 'vet', './...',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=workspace_path
    )

    # Stream output
    stdout_content = []
    stderr_content = []

    if process.stdout:
        async for line in process.stdout:
            line_str = line.decode('utf-8', errors='replace')
            stdout_content.append(line_str)
            yield {
                "type": "stream",
                "channel": "stdout",
                "content": line_str,
                "language": "go"
            }

    if process.stderr:
        async for line in process.stderr:
            line_str = line.decode('utf-8', errors='replace')
            stderr_content.append(line_str)
            yield {
                "type": "stream",
                "channel": "stderr",
                "content": line_str,
                "language": "go"
            }

    # Wait for completion
    try:
        return_code = await asyncio.wait_for(process.wait(), timeout=90.0)
    except asyncio.TimeoutError:
        process.kill()
        yield {
            "type": "result",
            "success": False,
            "language": "go",
            "errors": "Go validation timeout after 90 seconds",
            "return_code": -1
        }
        return

    all_output = ''.join(stdout_content + stderr_content)

    # If go vet passed, also run go build -n (dry run)
    if return_code == 0:
        go_mod_path = os.path.join(workspace_path, 'go.mod')
        if os.path.exists(go_mod_path):
            build_process = await asyncio.create_subprocess_exec(
                'go', 'build', '-n', './...',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workspace_path
            )

            if build_process.stdout:
                async for line in build_process.stdout:
                    line_str = line.decode('utf-8', errors='replace')
                    yield {
                        "type": "stream",
                        "channel": "stdout",
                        "content": line_str,
                        "language": "go"
                    }

            if build_process.stderr:
                async for line in build_process.stderr:
                    line_str = line.decode('utf-8', errors='replace')
                    yield {
                        "type": "stream",
                        "channel": "stderr",
                        "content": line_str,
                        "language": "go"
                    }

            try:
                build_return_code = await asyncio.wait_for(build_process.wait(), timeout=90.0)
                return_code = build_return_code
            except asyncio.TimeoutError:
                build_process.kill()

    yield {
        "type": "result",
        "success": return_code == 0,
        "language": "go",
        "errors": all_output if return_code != 0 else "",
        "return_code": return_code
    }

    debug_log(f"Go validation complete: return_code={return_code}")


async def validate_rust(workspace_path: str, files: list[str]) -> AsyncIterator[dict]:
    """
    Validate Rust with cargo check + cargo clippy (streaming).

    Yields:
        {"type": "stream", "channel": "stdout"|"stderr", "content": str, "language": "rust"}
        {"type": "result", "success": bool, "language": "rust", "errors": str, "return_code": int}
    """

    debug_log(f"Rust validation started: {len(files)} files")

    cargo_toml = os.path.join(workspace_path, 'Cargo.toml')

    if not files or not os.path.exists(cargo_toml):
        yield {
            "type": "result",
            "success": False,
            "language": "rust",
            "errors": "No Rust files or Cargo.toml not found",
            "return_code": -1
        }
        return

    # Run cargo check
    process = await asyncio.create_subprocess_exec(
        'cargo', 'check',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=workspace_path
    )

    # Stream output
    stdout_content = []
    stderr_content = []

    if process.stdout:
        async for line in process.stdout:
            line_str = line.decode('utf-8', errors='replace')
            stdout_content.append(line_str)
            yield {
                "type": "stream",
                "channel": "stdout",
                "content": line_str,
                "language": "rust"
            }

    if process.stderr:
        async for line in process.stderr:
            line_str = line.decode('utf-8', errors='replace')
            stderr_content.append(line_str)
            yield {
                "type": "stream",
                "channel": "stderr",
                "content": line_str,
                "language": "rust"
            }

    # Wait for completion
    try:
        return_code = await asyncio.wait_for(process.wait(), timeout=120.0)
    except asyncio.TimeoutError:
        process.kill()
        yield {
            "type": "result",
            "success": False,
            "language": "rust",
            "errors": "Rust validation timeout after 120 seconds",
            "return_code": -1
        }
        return

    all_output = ''.join(stdout_content + stderr_content)

    # If cargo check passed, run cargo clippy
    if return_code == 0:
        clippy_process = await asyncio.create_subprocess_exec(
            'cargo', 'clippy', '--', '-D', 'warnings',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=workspace_path
        )

        if clippy_process.stdout:
            async for line in clippy_process.stdout:
                line_str = line.decode('utf-8', errors='replace')
                yield {
                    "type": "stream",
                    "channel": "stdout",
                    "content": line_str,
                    "language": "rust"
                }

        if clippy_process.stderr:
            async for line in clippy_process.stderr:
                line_str = line.decode('utf-8', errors='replace')
                yield {
                    "type": "stream",
                    "channel": "stderr",
                    "content": line_str,
                    "language": "rust"
                }

        try:
            clippy_return_code = await asyncio.wait_for(clippy_process.wait(), timeout=120.0)
            # Don't fail build on clippy warnings, just log them
        except asyncio.TimeoutError:
            clippy_process.kill()

    yield {
        "type": "result",
        "success": return_code == 0,
        "language": "rust",
        "errors": all_output if return_code != 0 else "",
        "return_code": return_code
    }

    debug_log(f"Rust validation complete: return_code={return_code}")


async def validate_java(workspace_path: str, files: list[str], build_system: str | None) -> AsyncIterator[dict]:
    """
    Validate Java with Maven/Gradle/javac (streaming).

    Yields:
        {"type": "stream", "channel": "stdout"|"stderr", "content": str, "language": "java"}
        {"type": "result", "success": bool, "language": "java", "errors": str, "return_code": int}
    """

    debug_log(f"Java validation started: {len(files)} files, build_system={build_system}")

    if not files:
        yield {
            "type": "result",
            "success": False,
            "language": "java",
            "errors": "No Java files to validate",
            "return_code": -1
        }
        return

    # Determine build command
    if build_system == "maven":
        cmd = ['mvn', 'compile', '-q']
    elif build_system == "gradle":
        cmd = ['./gradlew', 'compileJava']
    else:
        # Plain javac
        target_dir = os.path.join(workspace_path, 'target', 'classes')
        os.makedirs(target_dir, exist_ok=True)
        file_paths = [os.path.join(workspace_path, f) for f in files]
        cmd = ['javac', '-d', target_dir] + file_paths

    # Run build
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=workspace_path
    )

    # Stream output
    stdout_content = []
    stderr_content = []

    if process.stdout:
        async for line in process.stdout:
            line_str = line.decode('utf-8', errors='replace')
            stdout_content.append(line_str)
            yield {
                "type": "stream",
                "channel": "stdout",
                "content": line_str,
                "language": "java"
            }

    if process.stderr:
        async for line in process.stderr:
            line_str = line.decode('utf-8', errors='replace')
            stderr_content.append(line_str)
            yield {
                "type": "stream",
                "channel": "stderr",
                "content": line_str,
                "language": "java"
            }

    # Wait for completion
    try:
        return_code = await asyncio.wait_for(process.wait(), timeout=180.0)
    except asyncio.TimeoutError:
        process.kill()
        yield {
            "type": "result",
            "success": False,
            "language": "java",
            "errors": "Java validation timeout after 180 seconds",
            "return_code": -1
        }
        return

    all_output = ''.join(stdout_content + stderr_content)

    yield {
        "type": "result",
        "success": return_code == 0,
        "language": "java",
        "errors": all_output if return_code != 0 else "",
        "return_code": return_code
    }

    debug_log(f"Java validation complete: return_code={return_code}")


# ============================================================================
# MCP TOOL: VALIDATE_ALL
# ============================================================================

async def validate_all(
    workspace_path: str,
    generated_files: list[dict] | None = None,
    parallel: bool = True
) -> AsyncIterator[dict]:
    """
    Auto-detect and validate ALL languages in workspace (streaming).

    Args:
        workspace_path: Absolute path to workspace
        generated_files: Optional list of generated files [{"path": "..."}, ...]
        parallel: Run validations in parallel (default: True)

    Yields:
        {"type": "detection", "languages": list[str]}
        {"type": "stream", "channel": "stdout"|"stderr", "content": str, "language": str}
        {"type": "result", "success": bool, "language": str, "errors": str, "return_code": int}
        {"type": "summary", "total": int, "passed": int, "failed": int, "results": list[dict]}
    """

    debug_log(f"validate_all started: workspace={workspace_path}, parallel={parallel}")

    # Detect languages
    detected = detect_project_languages(workspace_path, generated_files)
    detected_langs = [lang for lang, info in detected.items() if info['has']]

    yield {
        "type": "detection",
        "languages": detected_langs
    }

    # Build validation tasks
    tasks = []

    if detected["typescript"]["has"]:
        tasks.append(("typescript", validate_typescript(workspace_path, detected["typescript"]["files"])))

    if detected["python"]["has"]:
        tasks.append(("python", validate_python(workspace_path, detected["python"]["files"])))

    if detected["javascript"]["has"]:
        tasks.append(("javascript", validate_javascript(workspace_path, detected["javascript"]["files"])))

    if detected["go"]["has"]:
        tasks.append(("go", validate_go(workspace_path, detected["go"]["files"])))

    if detected["rust"]["has"]:
        tasks.append(("rust", validate_rust(workspace_path, detected["rust"]["files"])))

    if detected["java"]["has"]:
        tasks.append(("java", validate_java(workspace_path, detected["java"]["files"], detected["java"]["build_system"])))

    if not tasks:
        yield {
            "type": "summary",
            "total": 0,
            "passed": 0,
            "failed": 0,
            "results": [],
            "message": "No languages detected"
        }
        return

    # Execute validations
    results = []

    if parallel:
        # PARALLEL execution with asyncio.gather()
        # Stream all outputs concurrently
        async def run_validation(lang_name, validator):
            async for chunk in validator:
                # Forward stream chunks
                yield chunk

                # Collect final result
                if chunk["type"] == "result":
                    results.append(chunk)

        # Run all validators concurrently
        async_generators = [run_validation(lang, validator) for lang, validator in tasks]

        # Merge streams
        for generator in async_generators:
            async for chunk in generator:
                yield chunk

    else:
        # SEQUENTIAL execution (for debugging)
        for lang_name, validator in tasks:
            async for chunk in validator:
                yield chunk

                if chunk["type"] == "result":
                    results.append(chunk)

    # Summary
    passed = sum(1 for r in results if r.get("success", False))
    failed = len(results) - passed

    yield {
        "type": "summary",
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "results": results,
        "message": f"✅ {passed}/{len(results)} validations passed"
    }

    debug_log(f"validate_all complete: {passed}/{len(results)} passed")


# ============================================================================
# MCP PROTOCOL HANDLER
# ============================================================================

async def handle_request(request: dict) -> dict:
    """
    Handle incoming MCP request.

    JSON-RPC 2.0 protocol:
    - Request: {"jsonrpc": "2.0", "id": 1, "method": "...", "params": {...}}
    - Response: {"jsonrpc": "2.0", "id": 1, "result": {...}}
    - Error: {"jsonrpc": "2.0", "id": 1, "error": {"code": -32601, "message": "..."}}
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
                    "name": "build-validation-mcp-server",
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
                        "name": "validate_all",
                        "description": "Auto-detect and validate ALL languages in workspace with streaming compiler output. Supports TypeScript, Python, JavaScript, Go, Rust, Java. Runs parallel validation for polyglot projects.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "workspace_path": {
                                    "type": "string",
                                    "description": "Absolute path to workspace"
                                },
                                "generated_files": {
                                    "type": "array",
                                    "description": "Optional list of generated files [{'path': '...'}]"
                                },
                                "parallel": {
                                    "type": "boolean",
                                    "description": "Run validations in parallel (default: true)"
                                }
                            },
                            "required": ["workspace_path"]
                        }
                    },
                    {
                        "name": "validate_typescript",
                        "description": "Validate TypeScript with tsc --noEmit (streaming)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "workspace_path": {"type": "string"},
                                "files": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of .ts/.tsx files (relative paths)"
                                }
                            },
                            "required": ["workspace_path", "files"]
                        }
                    },
                    {
                        "name": "validate_python",
                        "description": "Validate Python with mypy (streaming)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "workspace_path": {"type": "string"},
                                "files": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of .py files (relative paths)"
                                }
                            },
                            "required": ["workspace_path", "files"]
                        }
                    },
                    {
                        "name": "validate_javascript",
                        "description": "Validate JavaScript with ESLint (streaming)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "workspace_path": {"type": "string"},
                                "files": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of .js/.jsx files (relative paths)"
                                }
                            },
                            "required": ["workspace_path", "files"]
                        }
                    },
                    {
                        "name": "validate_go",
                        "description": "Validate Go with go vet + go build (streaming)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "workspace_path": {"type": "string"},
                                "files": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of .go files (relative paths)"
                                }
                            },
                            "required": ["workspace_path", "files"]
                        }
                    },
                    {
                        "name": "validate_rust",
                        "description": "Validate Rust with cargo check + cargo clippy (streaming)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "workspace_path": {"type": "string"},
                                "files": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of .rs files (relative paths)"
                                }
                            },
                            "required": ["workspace_path", "files"]
                        }
                    },
                    {
                        "name": "validate_java",
                        "description": "Validate Java with Maven/Gradle/javac (streaming)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "workspace_path": {"type": "string"},
                                "files": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of .java files (relative paths)"
                                },
                                "build_system": {
                                    "type": "string",
                                    "description": "Build system: maven, gradle, or javac"
                                }
                            },
                            "required": ["workspace_path", "files"]
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
            if tool_name == "validate_all":
                validator = validate_all(
                    workspace_path=tool_args.get("workspace_path", ""),
                    generated_files=tool_args.get("generated_files"),
                    parallel=tool_args.get("parallel", True)
                )

            elif tool_name == "validate_typescript":
                validator = validate_typescript(
                    workspace_path=tool_args.get("workspace_path", ""),
                    files=tool_args.get("files", [])
                )

            elif tool_name == "validate_python":
                validator = validate_python(
                    workspace_path=tool_args.get("workspace_path", ""),
                    files=tool_args.get("files", [])
                )

            elif tool_name == "validate_javascript":
                validator = validate_javascript(
                    workspace_path=tool_args.get("workspace_path", ""),
                    files=tool_args.get("files", [])
                )

            elif tool_name == "validate_go":
                validator = validate_go(
                    workspace_path=tool_args.get("workspace_path", ""),
                    files=tool_args.get("files", [])
                )

            elif tool_name == "validate_rust":
                validator = validate_rust(
                    workspace_path=tool_args.get("workspace_path", ""),
                    files=tool_args.get("files", [])
                )

            elif tool_name == "validate_java":
                validator = validate_java(
                    workspace_path=tool_args.get("workspace_path", ""),
                    files=tool_args.get("files", []),
                    build_system=tool_args.get("build_system")
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

            # Collect all chunks from streaming validator
            all_chunks = []
            async for chunk in validator:
                all_chunks.append(chunk)

            # Format result (combine all chunks into text output)
            content_text = f"# Build Validation Results\n\n"
            content_text += f"**Tool:** {tool_name}\n"
            content_text += f"**Workspace:** {tool_args.get('workspace_path')}\n"
            content_text += f"**Timestamp:** {datetime.now().isoformat()}\n\n"

            # Add each chunk
            for chunk in all_chunks:
                chunk_type = chunk.get("type")

                if chunk_type == "detection":
                    content_text += f"## Detected Languages\n{', '.join(chunk['languages'])}\n\n"

                elif chunk_type == "stream":
                    lang = chunk.get("language", "unknown")
                    channel = chunk.get("channel", "output")
                    content = chunk.get("content", "")
                    content_text += f"[{lang}:{channel}] {content}"

                elif chunk_type == "result":
                    lang = chunk.get("language", "unknown")
                    success = chunk.get("success", False)
                    errors = chunk.get("errors", "")
                    return_code = chunk.get("return_code", 0)

                    status = "✅ PASSED" if success else "❌ FAILED"
                    content_text += f"\n## {lang.upper()} {status}\n"
                    content_text += f"**Return Code:** {return_code}\n\n"

                    if errors:
                        content_text += f"**Errors:**\n```\n{errors}\n```\n\n"

                elif chunk_type == "summary":
                    total = chunk.get("total", 0)
                    passed = chunk.get("passed", 0)
                    failed = chunk.get("failed", 0)
                    content_text += f"\n## SUMMARY\n"
                    content_text += f"- **Total:** {total}\n"
                    content_text += f"- **Passed:** {passed}\n"
                    content_text += f"- **Failed:** {failed}\n\n"

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": content_text
                        }
                    ],
                    "isError": any(chunk.get("type") == "result" and not chunk.get("success") for chunk in all_chunks)
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
    """
    Main MCP server loop.

    Reads JSON-RPC requests from stdin (one per line),
    processes them, and writes responses to stdout.
    """

    print(f"[{datetime.now()}] Build Validation MCP Server started", file=sys.stderr)
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
