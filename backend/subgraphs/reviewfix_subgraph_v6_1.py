"""
ReviewFix Subgraph v6.1 - Custom Node Implementation

This is a refactored version where the Fixer node uses direct LLM calls
instead of create_react_agent.

Changes from v6.0:
- Fixer node: Direct LLM.ainvoke() calls (no create_react_agent)
- Manual file operations instead of tool-calling agent
- Works with ClaudeCLISimple adapter
- Reviewer still uses GPT-4o-mini (unchanged)

Author: KI AutoAgent Team
Python: 3.13+
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
# MCP client for all service calls (replaces direct service imports)
from mcp.mcp_client import MCPClient
from langgraph.graph import END, StateGraph

from state_v6 import ReviewFixState
from tools.file_tools import read_file, write_file

logger = logging.getLogger(__name__)


def create_reviewfix_subgraph(
    workspace_path: str,
    mcp: MCPClient,
    hitl_callback: Any | None = None
) -> Any:
    """
    Create ReviewFix loop subgraph with MCP integration (v6.2).

    Uses MCP protocol for all service calls (Claude, Memory).

    Args:
        workspace_path: Path to workspace
        mcp: MCP client for all service calls
        hitl_callback: Optional HITL callback for debug info

    Returns:
        Compiled reviewfix subgraph
    """
    logger.debug("Creating ReviewFix subgraph v6.2 (MCP)...")

    # Reviewer node (unchanged - uses GPT-4o-mini)
    async def reviewer_node(state: ReviewFixState) -> ReviewFixState:
        """
        Review generated code and provide feedback.

        Uses GPT-4o-mini for cost-effective code review.
        """
        logger.info(f"🔬 Reviewer analyzing iteration {state['iteration']}...")

        try:
            # Read generated files from Codesmith
            generated_files = state.get('generated_files', [])

            # NEW v6.2: If no generated_files (FIX intent bypass), discover workspace files
            if not generated_files:
                logger.info("🔍 No generated_files in state, discovering workspace files...")

                import glob

                # Discover code files in workspace
                code_patterns = ['*.py', '*.ts', '*.tsx', '*.js', '*.jsx', '*.go', '*.rs', '*.java', '*.c', '*.cpp', '*.h']
                discovered_files = []

                for pattern in code_patterns:
                    matches = glob.glob(os.path.join(workspace_path, '**', pattern), recursive=True)
                    for match in matches:
                        # Skip node_modules, venv, build dirs
                        if any(skip in match for skip in ['node_modules', 'venv', 'dist', 'build', '__pycache__', '.git']):
                            continue

                        # Make path relative to workspace
                        rel_path = os.path.relpath(match, workspace_path)
                        discovered_files.append({"path": rel_path})

                if not discovered_files:
                    logger.warning("⚠️  No code files found in workspace")
                    return {
                        **state,
                        "quality_score": 0.0,
                        "feedback": "No code files found in workspace",
                        "iteration": state.get('iteration', 0) + 1
                    }

                logger.info(f"  ✅ Discovered {len(discovered_files)} code files in workspace")
                generated_files = discovered_files

            # Collect file contents
            file_contents = {}

            for file_info in generated_files:
                file_path = file_info.get('path')
                if not file_path:
                    continue
                full_path = os.path.join(workspace_path, file_path)

                if os.path.exists(full_path):
                    try:
                        result = await read_file.ainvoke({
                            "file_path": file_path,
                            "workspace_path": workspace_path,
                            "agent_id": "reviewer"  # 🔧 FIX: Pass agent_id for Asimov permissions
                        })
                        file_contents[file_path] = result.get("content", "")
                    except Exception as e:
                        logger.error(f"Failed to read {file_path}: {e}")
                        file_contents[file_path] = f"[Error reading file: {e}]"

            # Review with GPT-4o-mini
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=2048
            )

            system_prompt = """You are a senior code reviewer.

Your task:
1. Review code for quality, correctness, and best practices
2. Check for errors, bugs, and security issues
3. Assess code style and documentation
4. Provide actionable feedback
5. Assign a quality score (0.0 to 1.0)

Output format:
QUALITY_SCORE: <0.0 to 1.0>

FEEDBACK:
- Issue 1: ...
- Issue 2: ...
- Suggestion 1: ...

SUMMARY: Overall assessment"""

            files_text = "\n\n".join([
                f"FILE: {path}\n```\n{content}\n```"
                for path, content in file_contents.items()
            ])

            user_prompt = f"""Review the following code:

{files_text}

Provide quality score and detailed feedback."""

            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            review_output = response.content if hasattr(response, 'content') else str(response)

            # Parse quality score
            quality_score = 0.5  # Default

            for line in review_output.split('\n'):
                if line.startswith('QUALITY_SCORE:'):
                    try:
                        score_str = line.replace('QUALITY_SCORE:', '').strip()
                        quality_score = float(score_str)
                        quality_score = max(0.0, min(1.0, quality_score))  # Clamp
                    except ValueError:
                        logger.warning(f"Failed to parse quality score: {line}")

            logger.info(f"✅ Review complete - Quality: {quality_score:.2f}")

            # ================================================================
            # BUILD VALIDATION - Run actual build checks (TypeScript/Python)
            # ================================================================
            logger.info("🔬 Running build validation checks...")

            # Detect project type from generated files
            has_typescript = any(
                f.get('path', '').endswith(('.ts', '.tsx'))
                for f in generated_files
            )
            has_python = any(
                f.get('path', '').endswith('.py')
                for f in generated_files
            )
            has_javascript = any(
                f.get('path', '').endswith(('.js', '.jsx'))
                and not f.get('path', '').endswith(('.ts', '.tsx'))
                for f in generated_files
            )

            build_validation_passed = True
            build_errors = []

            #================================================================
            # IMPORTANT: Changed from elif to if for polyglot project support!
            # This allows running MULTIPLE validation checks for projects
            # with mixed languages (e.g., TypeScript + Python backend).
            # Sequential execution (parallel: asyncio.gather() in v6.2+)
            #================================================================

            # TypeScript compilation check
            if has_typescript:
                logger.info("📘 Project Type: TypeScript")
                logger.info("   Quality Threshold: 0.90 (highest)")

                tsconfig_path = os.path.join(workspace_path, 'tsconfig.json')
                package_json_path = os.path.join(workspace_path, 'package.json')

                if os.path.exists(tsconfig_path) and os.path.exists(package_json_path):
                    logger.info("🔬 Running TypeScript compilation check (tsc --noEmit)...")

                    try:
                        import subprocess
                        result = subprocess.run(
                            ['npx', 'tsc', '--noEmit'],
                            cwd=workspace_path,
                            capture_output=True,
                            text=True,
                            timeout=60
                        )

                        if result.returncode == 0:
                            logger.info("✅ TypeScript compilation passed!")
                        else:
                            logger.error("❌ TypeScript compilation failed!")
                            logger.error(f"   Errors:\n{result.stdout}\n{result.stderr}")
                            build_validation_passed = False
                            build_errors.append({
                                "type": "typescript_compilation",
                                "errors": result.stdout + result.stderr
                            })

                    except subprocess.TimeoutExpired:
                        logger.error("❌ TypeScript compilation timeout (60s)")
                        build_validation_passed = False
                        build_errors.append({
                            "type": "typescript_compilation",
                            "errors": "Compilation timeout after 60 seconds"
                        })
                    except Exception as e:
                        logger.error(f"❌ TypeScript compilation check failed: {e}")
                        build_validation_passed = False
                        build_errors.append({
                            "type": "typescript_compilation",
                            "errors": str(e)
                        })
                else:
                    logger.warning("⚠️  No tsconfig.json or package.json found - skipping TS compilation check")

            # Python type checking with mypy
            if has_python:
                logger.info("🐍 Project Type: Python")
                logger.info("   Quality Threshold: 0.85")

                # Check if mypy is available and there are .py files
                python_files = [
                    f.get('path') for f in generated_files
                    if f.get('path', '').endswith('.py')
                ]

                if python_files:
                    logger.info(f"🔬 Running Python mypy type check ({len(python_files)} files)...")

                    try:
                        import subprocess

                        # Run mypy on all Python files
                        result = subprocess.run(
                            ['python3', '-m', 'mypy'] + [
                                os.path.join(workspace_path, f) for f in python_files
                            ] + ['--ignore-missing-imports', '--no-strict-optional'],
                            capture_output=True,
                            text=True,
                            timeout=60
                        )

                        if result.returncode == 0:
                            logger.info("✅ Python mypy type check passed!")
                        else:
                            logger.error("❌ Python mypy type check failed!")
                            logger.error(f"   Errors:\n{result.stdout}\n{result.stderr}")
                            build_validation_passed = False
                            build_errors.append({
                                "type": "python_mypy",
                                "errors": result.stdout + result.stderr
                            })

                    except subprocess.TimeoutExpired:
                        logger.error("❌ Python mypy timeout (60s)")
                        build_validation_passed = False
                        build_errors.append({
                            "type": "python_mypy",
                            "errors": "Mypy type check timeout after 60 seconds"
                        })
                    except FileNotFoundError:
                        logger.warning("⚠️  mypy not installed - skipping Python type check")
                        logger.warning("   Install with: pip install mypy")
                    except Exception as e:
                        logger.error(f"❌ Python mypy check failed: {e}")
                        build_validation_passed = False
                        build_errors.append({
                            "type": "python_mypy",
                            "errors": str(e)
                        })
                else:
                    logger.warning("⚠️  No Python files found - skipping mypy check")

            # JavaScript linting with ESLint
            if has_javascript:
                logger.info("📙 Project Type: JavaScript")
                logger.info("   Quality Threshold: 0.75")

                # Check if ESLint is available
                eslint_config_path = os.path.join(workspace_path, '.eslintrc.json')
                package_json_path = os.path.join(workspace_path, 'package.json')

                javascript_files = [
                    f.get('path') for f in generated_files
                    if f.get('path', '').endswith(('.js', '.jsx'))
                ]

                if javascript_files:
                    logger.info(f"🔬 Running JavaScript ESLint check ({len(javascript_files)} files)...")

                    try:
                        import subprocess

                        # Run ESLint on all JavaScript files
                        result = subprocess.run(
                            ['npx', 'eslint'] + [
                                os.path.join(workspace_path, f) for f in javascript_files
                            ],
                            cwd=workspace_path,
                            capture_output=True,
                            text=True,
                            timeout=60
                        )

                        # ESLint returns 0 for no errors, 1 for errors, 2 for fatal errors
                        if result.returncode == 0:
                            logger.info("✅ JavaScript ESLint check passed!")
                        elif result.returncode == 1:
                            logger.error("❌ JavaScript ESLint check failed!")
                            logger.error(f"   Errors:\n{result.stdout}\n{result.stderr}")
                            build_validation_passed = False
                            build_errors.append({
                                "type": "javascript_eslint",
                                "errors": result.stdout + result.stderr
                            })
                        else:
                            logger.error(f"❌ JavaScript ESLint fatal error (code {result.returncode})")
                            logger.error(f"   Output:\n{result.stdout}\n{result.stderr}")
                            # Don't fail build on configuration issues
                            logger.warning("   Continuing without ESLint check")

                    except subprocess.TimeoutExpired:
                        logger.error("❌ JavaScript ESLint timeout (60s)")
                        build_validation_passed = False
                        build_errors.append({
                            "type": "javascript_eslint",
                            "errors": "ESLint check timeout after 60 seconds"
                        })
                    except FileNotFoundError:
                        logger.warning("⚠️  ESLint not found - skipping JavaScript linting")
                        logger.warning("   Install with: npm install --save-dev eslint")
                    except Exception as e:
                        logger.error(f"❌ JavaScript ESLint check failed: {e}")
                        build_validation_passed = False
                        build_errors.append({
                            "type": "javascript_eslint",
                            "errors": str(e)
                        })
                else:
                    logger.warning("⚠️  No JavaScript files found - skipping ESLint check")

            # Go validation with go vet
            has_go = any(
                f.get('path', '').endswith('.go')
                for f in generated_files
            )

            if has_go:
                logger.info("🔵 Project Type: Go")
                logger.info("   Quality Threshold: 0.85")

                go_mod_path = os.path.join(workspace_path, 'go.mod')
                go_files = [
                    f.get('path') for f in generated_files
                    if f.get('path', '').endswith('.go')
                ]

                if go_files:
                    logger.info(f"🔬 Running Go validation ({len(go_files)} files)...")

                    try:
                        import subprocess

                        # Run go vet (linting/static analysis)
                        result = subprocess.run(
                            ['go', 'vet', './...'],
                            cwd=workspace_path,
                            capture_output=True,
                            text=True,
                            timeout=90
                        )

                        if result.returncode == 0:
                            logger.info("✅ Go vet passed!")

                            # Also run go build -n (dry run compilation check)
                            if os.path.exists(go_mod_path):
                                logger.info("🔬 Running Go build check...")
                                build_result = subprocess.run(
                                    ['go', 'build', '-n', './...'],
                                    cwd=workspace_path,
                                    capture_output=True,
                                    text=True,
                                    timeout=90
                                )

                                if build_result.returncode == 0:
                                    logger.info("✅ Go build check passed!")
                                else:
                                    logger.error("❌ Go build check failed!")
                                    logger.error(f"   Errors:\n{build_result.stdout}\n{build_result.stderr}")
                                    build_validation_passed = False
                                    build_errors.append({
                                        "type": "go_build",
                                        "errors": build_result.stdout + build_result.stderr
                                    })
                        else:
                            logger.error("❌ Go vet failed!")
                            logger.error(f"   Errors:\n{result.stdout}\n{result.stderr}")
                            build_validation_passed = False
                            build_errors.append({
                                "type": "go_vet",
                                "errors": result.stdout + result.stderr
                            })

                    except subprocess.TimeoutExpired:
                        logger.error("❌ Go validation timeout (90s)")
                        build_validation_passed = False
                        build_errors.append({
                            "type": "go_validation",
                            "errors": "Go validation timeout after 90 seconds"
                        })
                    except FileNotFoundError:
                        logger.warning("⚠️  Go not installed - skipping Go validation")
                        logger.warning("   Install from: https://golang.org/dl/")
                    except Exception as e:
                        logger.error(f"❌ Go validation failed: {e}")
                        build_validation_passed = False
                        build_errors.append({
                            "type": "go_validation",
                            "errors": str(e)
                        })
                else:
                    logger.warning("⚠️  No Go files found - skipping Go validation")

            # Rust validation with cargo check
            has_rust = any(
                f.get('path', '').endswith('.rs')
                for f in generated_files
            )

            if has_rust:
                logger.info("🦀 Project Type: Rust")
                logger.info("   Quality Threshold: 0.85")

                cargo_toml_path = os.path.join(workspace_path, 'Cargo.toml')
                rust_files = [
                    f.get('path') for f in generated_files
                    if f.get('path', '').endswith('.rs')
                ]

                if rust_files and os.path.exists(cargo_toml_path):
                    logger.info(f"🔬 Running Rust validation ({len(rust_files)} files)...")

                    try:
                        import subprocess

                        # Run cargo check (fast compilation check)
                        logger.info("🔬 Running cargo check...")
                        result = subprocess.run(
                            ['cargo', 'check'],
                            cwd=workspace_path,
                            capture_output=True,
                            text=True,
                            timeout=120
                        )

                        if result.returncode == 0:
                            logger.info("✅ Cargo check passed!")

                            # Optionally run cargo clippy (linting)
                            logger.info("🔬 Running cargo clippy (linting)...")
                            clippy_result = subprocess.run(
                                ['cargo', 'clippy', '--', '-D', 'warnings'],
                                cwd=workspace_path,
                                capture_output=True,
                                text=True,
                                timeout=120
                            )

                            if clippy_result.returncode == 0:
                                logger.info("✅ Cargo clippy passed!")
                            else:
                                logger.warning("⚠️  Cargo clippy found warnings")
                                logger.warning(f"   Warnings:\n{clippy_result.stdout}\n{clippy_result.stderr}")
                                # Don't fail build on clippy warnings, just log them
                        else:
                            logger.error("❌ Cargo check failed!")
                            logger.error(f"   Errors:\n{result.stdout}\n{result.stderr}")
                            build_validation_passed = False
                            build_errors.append({
                                "type": "rust_cargo_check",
                                "errors": result.stdout + result.stderr
                            })

                    except subprocess.TimeoutExpired:
                        logger.error("❌ Rust validation timeout (120s)")
                        build_validation_passed = False
                        build_errors.append({
                            "type": "rust_validation",
                            "errors": "Rust validation timeout after 120 seconds"
                        })
                    except FileNotFoundError:
                        logger.warning("⚠️  Cargo not installed - skipping Rust validation")
                        logger.warning("   Install from: https://www.rust-lang.org/tools/install")
                    except Exception as e:
                        logger.error(f"❌ Rust validation failed: {e}")
                        build_validation_passed = False
                        build_errors.append({
                            "type": "rust_validation",
                            "errors": str(e)
                        })
                else:
                    if not os.path.exists(cargo_toml_path):
                        logger.warning("⚠️  No Cargo.toml found - skipping Rust validation")
                    else:
                        logger.warning("⚠️  No Rust files found - skipping Rust validation")

            # Java validation with javac/Maven/Gradle
            has_java = any(
                f.get('path', '').endswith('.java')
                for f in generated_files
            )

            if has_java:
                logger.info("☕ Project Type: Java")
                logger.info("   Quality Threshold: 0.80")

                pom_xml_path = os.path.join(workspace_path, 'pom.xml')
                build_gradle_path = os.path.join(workspace_path, 'build.gradle')
                java_files = [
                    f.get('path') for f in generated_files
                    if f.get('path', '').endswith('.java')
                ]

                if java_files:
                    logger.info(f"🔬 Running Java validation ({len(java_files)} files)...")

                    try:
                        import subprocess

                        # Try Maven first
                        if os.path.exists(pom_xml_path):
                            logger.info("🔬 Running Maven compile...")
                            result = subprocess.run(
                                ['mvn', 'compile', '-q'],
                                cwd=workspace_path,
                                capture_output=True,
                                text=True,
                                timeout=180
                            )

                            if result.returncode == 0:
                                logger.info("✅ Maven compile passed!")
                            else:
                                logger.error("❌ Maven compile failed!")
                                logger.error(f"   Errors:\n{result.stdout}\n{result.stderr}")
                                build_validation_passed = False
                                build_errors.append({
                                    "type": "java_maven_compile",
                                    "errors": result.stdout + result.stderr
                                })

                        # Try Gradle if Maven not available
                        elif os.path.exists(build_gradle_path):
                            logger.info("🔬 Running Gradle compileJava...")
                            result = subprocess.run(
                                ['./gradlew', 'compileJava'],
                                cwd=workspace_path,
                                capture_output=True,
                                text=True,
                                timeout=180
                            )

                            if result.returncode == 0:
                                logger.info("✅ Gradle compileJava passed!")
                            else:
                                logger.error("❌ Gradle compileJava failed!")
                                logger.error(f"   Errors:\n{result.stdout}\n{result.stderr}")
                                build_validation_passed = False
                                build_errors.append({
                                    "type": "java_gradle_compile",
                                    "errors": result.stdout + result.stderr
                                })

                        # Fallback to plain javac
                        else:
                            logger.info("🔬 Running javac (plain Java compilation)...")
                            target_dir = os.path.join(workspace_path, 'target', 'classes')
                            os.makedirs(target_dir, exist_ok=True)

                            java_file_paths = [
                                os.path.join(workspace_path, f) for f in java_files
                            ]

                            result = subprocess.run(
                                ['javac', '-d', target_dir] + java_file_paths,
                                cwd=workspace_path,
                                capture_output=True,
                                text=True,
                                timeout=180
                            )

                            if result.returncode == 0:
                                logger.info("✅ javac compilation passed!")
                            else:
                                logger.error("❌ javac compilation failed!")
                                logger.error(f"   Errors:\n{result.stdout}\n{result.stderr}")
                                build_validation_passed = False
                                build_errors.append({
                                    "type": "java_javac_compile",
                                    "errors": result.stdout + result.stderr
                                })

                    except subprocess.TimeoutExpired:
                        logger.error("❌ Java validation timeout (180s)")
                        build_validation_passed = False
                        build_errors.append({
                            "type": "java_validation",
                            "errors": "Java validation timeout after 180 seconds"
                        })
                    except FileNotFoundError as e:
                        logger.warning(f"⚠️  Java build tool not found: {e}")
                        logger.warning("   Install Java Development Kit (JDK)")
                    except Exception as e:
                        logger.error(f"❌ Java validation failed: {e}")
                        build_validation_passed = False
                        build_errors.append({
                            "type": "java_validation",
                            "errors": str(e)
                        })
                else:
                    logger.warning("⚠️  No Java files found - skipping Java validation")

            # Adjust quality score based on build validation
            if not build_validation_passed:
                logger.warning("⚠️  Build validation FAILED - reducing quality score to 0.50")
                logger.warning(f"   Original quality score: {quality_score:.2f}")
                quality_score = 0.50  # Force another iteration
                logger.warning(f"   New quality score: {quality_score:.2f}")

                # Append build errors to review feedback
                build_error_text = "\n\n## BUILD VALIDATION ERRORS\n\n"
                for err in build_errors:
                    build_error_text += f"**{err['type']}:**\n```\n{err['errors']}\n```\n\n"

                review_output += build_error_text

            else:
                logger.info("✅ Build validation PASSED")

            # Store review in Memory (via MCP!)
            try:
                await mcp.call(
                    server="memory",
                    tool="store_memory",
                    arguments={
                        "workspace_path": workspace_path,
                        "content": review_output,
                        "metadata": {
                            "agent": "reviewer",
                            "type": "review",
                            "iteration": state.get('iteration', 0) + 1,
                            "quality_score": quality_score,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to store review in memory: {e}")

            # Extract file paths for fixer
            file_paths_to_fix = [f.get('path') for f in generated_files if f.get('path')]

            return {
                **state,
                "quality_score": quality_score,
                "feedback": review_output,
                "files_to_review": file_paths_to_fix,  # NEW v6.2: For FIX intent workflow
                "iteration": state.get('iteration', 0) + 1
            }

        except Exception as e:
            logger.error(f"❌ Reviewer failed: {e}", exc_info=True)

            return {
                **state,
                "quality_score": 0.0,
                "feedback": f"Review failed: {str(e)}",
                "iteration": state.get('iteration', 0) + 1,
                "errors": state.get('errors', []) + [{"error": str(e), "node": "reviewer"}]
            }

    # Fixer node (REFACTORED - custom implementation, no create_react_agent)
    async def fixer_node(state: ReviewFixState) -> ReviewFixState:
        """
        Apply fixes based on reviewer feedback.

        Uses direct Claude LLM calls with manual file operations.
        """
        logger.info(f"🔧 Fixer applying fixes (iteration {state['iteration']})...")

        try:
            feedback = state.get('feedback', '')
            files_to_fix = state.get('files_to_review', [])

            if not feedback or not files_to_fix:
                logger.warning("⚠️  No feedback or files to fix")
                return state

            # Read current file contents
            file_contents = {}

            for file_path in files_to_fix:
                full_path = os.path.join(workspace_path, file_path)

                if os.path.exists(full_path):
                    try:
                        result = await read_file.ainvoke({
                            "file_path": file_path,
                            "workspace_path": workspace_path,
                            "agent_id": "fixer"  # 🔧 FIX: Pass agent_id for Asimov permissions
                        })
                        file_contents[file_path] = result.get("content", "")
                    except Exception as e:
                        logger.error(f"Failed to read {file_path}: {e}")

            if not file_contents:
                logger.warning("⚠️  No files could be read")
                return state

            # Apply fixes with Claude (via MCP!)
            logger.info("🤖 Generating fixes with Claude via MCP...")

            system_prompt = """You are an expert code fixer.

Your task:
1. Read the reviewer's feedback
2. Apply fixes to the code
3. Maintain code style and structure
4. Fix all identified issues
5. Output the complete fixed files

Output format:
For each file:

FILE: <relative_path>
```<language>
<complete fixed code>
```

Example:
FILE: src/app.py
```python
# Fixed code here
```"""

            files_text = "\n\n".join([
                f"FILE: {path}\n```\n{content}\n```"
                for path, content in file_contents.items()
            ])

            user_prompt = f"""Apply fixes based on the following review:

## Review Feedback
{feedback}

## Current Files
{files_text}

Generate complete fixed versions of all files."""

            # Call Claude via MCP
            claude_result = await mcp.call(
                server="claude",
                tool="claude_generate",
                arguments={
                    "prompt": user_prompt,
                    "system_prompt": system_prompt,
                    "workspace_path": workspace_path,
                    "agent_name": "fixer",
                    "temperature": 0.2,
                    "max_tokens": 8192,
                    "tools": ["Read", "Edit", "Bash"]
                }
            )

            # Extract fixes from MCP response
            fixes_output = ""
            if claude_result.get("content"):
                content_blocks = claude_result.get("content", [])
                for block in content_blocks:
                    if block.get("type") == "text":
                        text = block.get("text", "")
                        # Extract actual content from JSON response format
                        if "content" in text and "success" in text:
                            import json
                            try:
                                data = json.loads(text.split("```json\n")[1].split("\n```")[0])
                                fixes_output = data.get("content", "")
                            except:
                                fixes_output = text
                        else:
                            fixes_output = text

            if not fixes_output:
                raise Exception(f"Fixes generation failed: {claude_result.get('error', 'Unknown error')}")

            logger.info(f"✅ Fixes generated: {len(fixes_output)} chars")

            # Parse and write fixed files
            logger.info("📝 Writing fixed files...")

            fixed_files = []

            # Simple parser for FILE: <path> format
            lines = fixes_output.split('\n')
            current_file = None
            current_code = []
            in_code_block = False

            for line in lines:
                if line.startswith('FILE:'):
                    # Save previous file
                    if current_file and current_code:
                        file_path = os.path.join(workspace_path, current_file.strip())
                        file_content = '\n'.join(current_code).strip()

                        try:
                            await write_file.ainvoke({
                                "file_path": file_path,
                                "content": file_content,
                                "workspace_path": workspace_path,
                                "agent_id": "fixer"  # 🔧 FIX: Pass agent_id for Asimov permissions
                            })

                            fixed_files.append(current_file.strip())
                            logger.debug(f"✅ Fixed {current_file.strip()}")
                        except Exception as e:
                            logger.error(f"❌ Failed to write {current_file}: {e}")

                    # Start new file
                    current_file = line.replace('FILE:', '').strip()
                    current_code = []
                    in_code_block = False

                elif line.startswith('```'):
                    if in_code_block:
                        in_code_block = False
                    else:
                        in_code_block = True

                elif in_code_block and current_file:
                    current_code.append(line)

            # Save last file
            if current_file and current_code:
                file_path = os.path.join(workspace_path, current_file.strip())
                file_content = '\n'.join(current_code).strip()

                try:
                    await write_file.ainvoke({
                        "file_path": file_path,
                        "content": file_content,
                        "workspace_path": workspace_path,
                        "agent_id": "fixer"  # 🔧 FIX: Pass agent_id for Asimov permissions
                    })

                    fixed_files.append(current_file.strip())
                    logger.debug(f"✅ Fixed {current_file.strip()}")
                except Exception as e:
                    logger.error(f"❌ Failed to write {current_file}: {e}")

            logger.info(f"✅ Fixed {len(fixed_files)} files")

            # Store fixes in Memory (via MCP!)
            try:
                await mcp.call(
                    server="memory",
                    tool="store_memory",
                    arguments={
                        "workspace_path": workspace_path,
                        "content": fixes_output,
                        "metadata": {
                            "agent": "fixer",
                            "type": "fixes",
                            "iteration": state.get('iteration', 0),
                            "files_count": len(fixed_files),
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to store fixes in memory: {e}")

            return {
                **state,
                "fixes_applied": fixes_output,
                "fixed_files": fixed_files
            }

        except Exception as e:
            logger.error(f"❌ Fixer failed: {e}", exc_info=True)

            return {
                **state,
                "fixes_applied": f"Fixing failed: {str(e)}",
                "errors": state.get('errors', []) + [{"error": str(e), "node": "fixer"}]
            }

    # Conditional routing function
    def should_continue_fixing(state: ReviewFixState) -> Literal["continue", "end"]:
        """
        Decide whether to continue fixing or stop.

        Stop conditions:
        1. Quality score >= 0.75 (good enough)
        2. Iteration >= 3 (max iterations reached)

        Returns:
            "continue" to keep fixing, "end" to stop
        """
        quality = state.get("quality_score", 0.0)
        iteration = state.get("iteration", 0)

        if quality >= 0.75:
            logger.info(f"✅ Quality target reached: {quality:.2f}")
            return "end"

        if iteration >= 3:
            logger.info(f"⚠️  Max iterations reached: {iteration}")
            return "end"

        logger.info(f"🔄 Continue fixing (quality: {quality:.2f}, iteration: {iteration})")
        return "continue"

    # Build subgraph
    graph = StateGraph(ReviewFixState)

    # Add nodes
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("fixer", fixer_node)

    # Set entry point
    graph.set_entry_point("reviewer")

    # Add conditional routing from reviewer
    graph.add_conditional_edges(
        "reviewer",
        should_continue_fixing,
        {
            "continue": "fixer",
            "end": END
        }
    )

    # Add loop edge from fixer back to reviewer
    graph.add_edge("fixer", "reviewer")

    # Compile and return
    logger.debug("✅ ReviewFix subgraph v6.2 compiled (MCP)")
    return graph.compile()
