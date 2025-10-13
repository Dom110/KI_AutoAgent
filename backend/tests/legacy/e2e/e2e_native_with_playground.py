#!/usr/bin/env python3
"""
Native E2E Test with Playground Review

Complete end-to-end test with 4 phases:
1. Automatic workflow execution via WebSocket
2. Automatic build validation (backend + frontend)
3. Manual review with Claude Code playground
4. Comprehensive validation

Test App: Full-Stack Todo App
- Backend: FastAPI + SQLite
- Frontend: React 18 + TypeScript + Vite
- Styling: Tailwind CSS

Run:
    cd /Users/dominikfoert/git/KI_AutoAgent/backend
    ./venv_v6/bin/python tests/e2e_native_with_playground.py

Author: KI AutoAgent Team
Version: 6.2.0
Date: 2025-10-12
"""

import asyncio
import json
import logging
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import websockets

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Test workspace (ISOLATED from development repo!)
TEST_WORKSPACE = Path.home() / "TestApps" / "todo_app_native_e2e"

# Backend WebSocket URL
WS_URL = "ws://localhost:8002/ws/chat"

# Test configuration
TEST_CONFIG = {
    "app_name": "Todo App",
    "description": "Full-stack todo application with authentication",
    "features": [
        "User authentication (register, login, logout)",
        "CRUD operations for todos (create, read, update, delete)",
        "Filter by status (all, active, completed)",
        "Mark todos as complete/incomplete",
        "Responsive design (mobile, tablet, desktop)",
        "Persistent storage (SQLite)"
    ],
    "tech_stack": {
        "backend": "FastAPI + SQLite + SQLAlchemy",
        "frontend": "React 18 + TypeScript + Vite",
        "styling": "Tailwind CSS",
        "testing": "pytest (backend), vitest (frontend)"
    },
    "success_criteria": {
        "quality_score_min": 0.85,
        "tests_passing": True,
        "build_successful": True,
        "typescript_errors": 0,
        "no_critical_issues": True
    }
}

# Expected files
EXPECTED_FILES = [
    # Backend
    "backend/main.py",
    "backend/models.py",
    "backend/database.py",
    "backend/schemas.py",
    "backend/auth.py",
    "backend/routers/todos.py",
    "backend/routers/auth.py",
    "backend/requirements.txt",
    "backend/tests/test_todos.py",
    "backend/tests/test_auth.py",

    # Frontend
    "frontend/src/App.tsx",
    "frontend/src/main.tsx",
    "frontend/src/components/TodoList.tsx",
    "frontend/src/components/TodoItem.tsx",
    "frontend/src/components/TodoForm.tsx",
    "frontend/src/components/Login.tsx",
    "frontend/src/services/api.ts",
    "frontend/package.json",
    "frontend/tsconfig.json",
    "frontend/vite.config.ts",
    "frontend/tailwind.config.js",
    "frontend/index.html",

    # Root
    "README.md",
    ".gitignore"
]


# ============================================================================
# WEBSOCKET CLIENT
# ============================================================================

class E2ETestClient:
    """WebSocket client for E2E testing."""

    def __init__(self, ws_url: str, workspace_path: Path):
        self.ws_url = ws_url
        self.workspace_path = workspace_path
        self.websocket = None
        self.messages = []
        self.workflow_result = None

    async def connect(self) -> None:
        """Connect to WebSocket server."""
        logger.info(f"🔌 Connecting to {self.ws_url}...")

        try:
            self.websocket = await websockets.connect(self.ws_url)
            logger.info("✅ WebSocket connected")

            # Wait for initial connection message
            msg = await self.websocket.recv()
            data = json.loads(msg)
            logger.info(f"📨 Server: {data.get('type')}")

            # Send init message with workspace
            init_msg = {
                "type": "init",
                "workspace_path": str(self.workspace_path)
            }
            await self.websocket.send(json.dumps(init_msg))
            logger.info(f"📤 Sent init message (workspace: {self.workspace_path})")

            # Wait for initialized confirmation
            msg = await self.websocket.recv()
            data = json.loads(msg)

            if data.get("type") == "initialized":
                logger.info(f"✅ Session initialized: {data.get('session_id')}")
            else:
                logger.warning(f"⚠️  Unexpected message: {data}")

        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            raise

    async def send_task(self, task: str) -> None:
        """Send task to server."""
        if not self.websocket:
            raise RuntimeError("Not connected. Call connect() first.")

        message = {
            "type": "message",
            "content": task
        }

        logger.info("📤 Sending task...")
        logger.info(f"   Task: {task[:100]}...")

        await self.websocket.send(json.dumps(message))

    async def wait_for_completion(self, timeout: int = 900) -> dict[str, Any]:
        """
        Wait for workflow completion.

        Args:
            timeout: Timeout in seconds (default: 15 minutes)

        Returns:
            Workflow result dict
        """
        if not self.websocket:
            raise RuntimeError("Not connected")

        logger.info(f"⏳ Waiting for workflow completion (timeout: {timeout}s)...")

        start_time = time.time()
        message_count = 0

        try:
            while True:
                # Check timeout
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Workflow did not complete within {timeout}s")

                # Receive message with timeout
                try:
                    msg = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=30.0
                    )
                except asyncio.TimeoutError:
                    logger.info("⏳ Still waiting...")
                    continue

                data = json.loads(msg)
                self.messages.append(data)
                message_count += 1

                msg_type = data.get("type")

                # Log progress
                if msg_type == "agent_start":
                    agent = data.get("agent", "unknown")
                    logger.info(f"🤖 Agent started: {agent}")

                elif msg_type == "agent_complete":
                    agent = data.get("agent", "unknown")
                    duration = data.get("duration_ms", 0) / 1000
                    logger.info(f"✅ Agent complete: {agent} ({duration:.1f}s)")

                elif msg_type == "workflow_complete":
                    logger.info("✅ Workflow complete!")
                    self.workflow_result = data
                    break

                elif msg_type == "error":
                    error_msg = data.get("error", "Unknown error")
                    logger.error(f"❌ Error: {error_msg}")
                    raise RuntimeError(f"Workflow error: {error_msg}")

                elif msg_type == "message":
                    content = data.get("content", "")
                    if content:
                        logger.info(f"💬 {content[:100]}...")

                # Progress indicator every 10 messages
                if message_count % 10 == 0:
                    elapsed = time.time() - start_time
                    logger.info(f"📊 Progress: {message_count} messages, {elapsed:.1f}s elapsed")

        except Exception as e:
            logger.error(f"❌ Error during wait: {e}")
            raise

        finally:
            elapsed = time.time() - start_time
            logger.info(f"⏱️  Total wait time: {elapsed:.1f}s")
            logger.info(f"📊 Total messages: {message_count}")

        return self.workflow_result

    async def close(self) -> None:
        """Close WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
            logger.info("🔌 WebSocket closed")


# ============================================================================
# TEST PHASES
# ============================================================================

async def phase_1_workflow_execution() -> dict[str, Any]:
    """
    Phase 1: Automatic workflow execution via WebSocket.

    Steps:
    1. Setup test workspace
    2. Connect to backend WebSocket
    3. Send task to create Todo app
    4. Wait for workflow completion
    5. Validate generated files

    Returns:
        Workflow result dict
    """
    print("\n" + "="*80)
    print("PHASE 1: AUTOMATIC WORKFLOW EXECUTION")
    print("="*80)

    # Step 1: Setup workspace
    print("\n🏗️  Step 1: Setup test workspace")

    if TEST_WORKSPACE.exists():
        logger.info(f"🧹 Cleaning existing workspace: {TEST_WORKSPACE}")
        shutil.rmtree(TEST_WORKSPACE)

    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    logger.info(f"✅ Created workspace: {TEST_WORKSPACE}")

    # Step 2: Connect to backend
    print("\n🔌 Step 2: Connect to backend WebSocket")

    client = E2ETestClient(WS_URL, TEST_WORKSPACE)
    await client.connect()

    # Step 3: Send task
    print("\n📤 Step 3: Send task")

    task = f"""Create a full-stack Todo application with the following requirements:

## Features
{chr(10).join([f"- {feature}" for feature in TEST_CONFIG['features']])}

## Tech Stack
- **Backend:** {TEST_CONFIG['tech_stack']['backend']}
- **Frontend:** {TEST_CONFIG['tech_stack']['frontend']}
- **Styling:** {TEST_CONFIG['tech_stack']['styling']}
- **Testing:** {TEST_CONFIG['tech_stack']['testing']}

## Project Structure
Create a clear directory structure:
- `backend/` - FastAPI application
- `frontend/` - React + TypeScript application
- `README.md` - Setup and usage instructions

## Requirements
- Complete backend with RESTful API
- Complete frontend with responsive UI
- User authentication with JWT
- Comprehensive tests (backend + frontend)
- Production-ready build configuration
- Clear documentation

Please implement a fully functional application with all features working.
"""

    await client.send_task(task)

    # Step 4: Wait for completion
    print("\n⏳ Step 4: Wait for workflow completion")
    print("   This may take 10-15 minutes...")

    try:
        result = await client.wait_for_completion(timeout=900)  # 15 minutes
    except Exception as e:
        logger.error(f"❌ Workflow failed: {e}")
        await client.close()
        raise

    await client.close()

    # Step 5: Validate files
    print("\n📁 Step 5: Validate generated files")

    missing_files = []
    present_files = []

    for file_path in EXPECTED_FILES:
        full_path = TEST_WORKSPACE / file_path
        if full_path.exists():
            present_files.append(file_path)
            logger.info(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            logger.warning(f"❌ {file_path} - MISSING")

    print(f"\n📊 File Validation:")
    print(f"   Present: {len(present_files)}/{len(EXPECTED_FILES)}")
    print(f"   Missing: {len(missing_files)}")

    if missing_files:
        logger.warning(f"⚠️  Missing {len(missing_files)} files (continuing anyway)")
        logger.warning(f"   Missing files: {missing_files[:5]}")  # Show first 5

    # Extract result metadata
    result_metadata = {
        "status": result.get("status", "unknown"),
        "duration_ms": result.get("duration_ms", 0),
        "quality_score": result.get("metrics", {}).get("quality_score", 0.0),
        "files_generated": len(present_files),
        "files_missing": len(missing_files)
    }

    print("\n✅ Phase 1: COMPLETE")
    print(f"   Status: {result_metadata['status']}")
    print(f"   Duration: {result_metadata['duration_ms'] / 1000:.1f}s")
    print(f"   Quality Score: {result_metadata['quality_score']:.2f}")

    return result_metadata


async def phase_2_build_validation() -> dict[str, Any]:
    """
    Phase 2: Automatic build validation.

    Steps:
    1. Validate backend (install deps, run tests)
    2. Validate frontend (install deps, TypeScript, build)
    3. Report results

    Returns:
        Validation results dict
    """
    print("\n" + "="*80)
    print("PHASE 2: AUTOMATIC BUILD VALIDATION")
    print("="*80)

    validation_results = {
        "backend": {
            "dependencies_installed": False,
            "tests_passed": False,
            "test_output": ""
        },
        "frontend": {
            "dependencies_installed": False,
            "typescript_passed": False,
            "build_passed": False,
            "typescript_errors": [],
            "build_output": ""
        }
    }

    # Backend validation
    print("\n🐍 Step 1: Backend Validation")

    backend_dir = TEST_WORKSPACE / "backend"

    if not backend_dir.exists():
        logger.error("❌ Backend directory not found!")
        validation_results["backend"]["error"] = "Backend directory missing"
    else:
        # Check requirements.txt
        requirements_file = backend_dir / "requirements.txt"

        if not requirements_file.exists():
            logger.warning("⚠️  requirements.txt not found - skipping dependency install")
        else:
            # Install dependencies
            print("   📦 Installing dependencies...")

            try:
                result = subprocess.run(
                    ["pip", "install", "-q", "-r", "requirements.txt"],
                    cwd=backend_dir,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes
                )

                if result.returncode == 0:
                    validation_results["backend"]["dependencies_installed"] = True
                    logger.info("   ✅ Dependencies installed")
                else:
                    logger.error(f"   ❌ pip install failed: {result.stderr[:200]}")
                    validation_results["backend"]["pip_error"] = result.stderr

            except subprocess.TimeoutExpired:
                logger.error("   ❌ pip install timeout")
            except Exception as e:
                logger.error(f"   ❌ pip install error: {e}")

        # Run tests
        tests_dir = backend_dir / "tests"

        if not tests_dir.exists():
            logger.warning("   ⚠️  tests/ directory not found - skipping tests")
        else:
            print("   🧪 Running tests...")

            try:
                result = subprocess.run(
                    ["pytest", "tests/", "-v", "--tb=short"],
                    cwd=backend_dir,
                    capture_output=True,
                    text=True,
                    timeout=120  # 2 minutes
                )

                validation_results["backend"]["test_output"] = result.stdout

                if result.returncode == 0:
                    validation_results["backend"]["tests_passed"] = True
                    logger.info("   ✅ All tests passed")
                else:
                    logger.error(f"   ❌ Tests failed (exit code: {result.returncode})")
                    logger.error(f"   Output: {result.stdout[:300]}")

            except subprocess.TimeoutExpired:
                logger.error("   ❌ Tests timeout")
            except FileNotFoundError:
                logger.warning("   ⚠️  pytest not found - skipping tests")
            except Exception as e:
                logger.error(f"   ❌ Test error: {e}")

    # Frontend validation
    print("\n📦 Step 2: Frontend Validation")

    frontend_dir = TEST_WORKSPACE / "frontend"

    if not frontend_dir.exists():
        logger.error("❌ Frontend directory not found!")
        validation_results["frontend"]["error"] = "Frontend directory missing"
    else:
        # Install dependencies
        print("   📦 Installing dependencies (npm install)...")

        try:
            result = subprocess.run(
                ["npm", "install"],
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes
            )

            if result.returncode == 0:
                validation_results["frontend"]["dependencies_installed"] = True
                logger.info("   ✅ npm install successful")
            else:
                logger.error(f"   ❌ npm install failed: {result.stderr[:200]}")
                validation_results["frontend"]["npm_error"] = result.stderr

        except subprocess.TimeoutExpired:
            logger.error("   ❌ npm install timeout")
        except Exception as e:
            logger.error(f"   ❌ npm install error: {e}")

        # TypeScript compilation check
        print("   🔍 TypeScript compilation check...")

        try:
            result = subprocess.run(
                ["npx", "tsc", "--noEmit"],
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                validation_results["frontend"]["typescript_passed"] = True
                logger.info("   ✅ TypeScript compilation passed")
            else:
                logger.error(f"   ❌ TypeScript errors found")

                # Parse errors
                errors = result.stdout.split("\n")
                validation_results["frontend"]["typescript_errors"] = errors[:10]  # First 10

                for error in errors[:5]:
                    if error.strip():
                        logger.error(f"      {error}")

        except subprocess.TimeoutExpired:
            logger.error("   ❌ TypeScript check timeout")
        except Exception as e:
            logger.error(f"   ❌ TypeScript check error: {e}")

        # Build
        print("   🏗️  Building production bundle...")

        try:
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=120
            )

            validation_results["frontend"]["build_output"] = result.stdout

            if result.returncode == 0:
                validation_results["frontend"]["build_passed"] = True
                logger.info("   ✅ Build successful")

                # Check dist/ directory
                dist_dir = frontend_dir / "dist"
                if dist_dir.exists():
                    files = list(dist_dir.rglob("*"))
                    logger.info(f"   📦 Build output: {len(files)} files")
            else:
                logger.error(f"   ❌ Build failed: {result.stderr[:200]}")

        except subprocess.TimeoutExpired:
            logger.error("   ❌ Build timeout")
        except Exception as e:
            logger.error(f"   ❌ Build error: {e}")

    # Summary
    print("\n📊 Phase 2 Summary:")
    print(f"\n   Backend:")
    print(f"     Dependencies: {'✅' if validation_results['backend']['dependencies_installed'] else '❌'}")
    print(f"     Tests: {'✅' if validation_results['backend']['tests_passed'] else '❌'}")

    print(f"\n   Frontend:")
    print(f"     Dependencies: {'✅' if validation_results['frontend']['dependencies_installed'] else '❌'}")
    print(f"     TypeScript: {'✅' if validation_results['frontend']['typescript_passed'] else '❌'}")
    print(f"     Build: {'✅' if validation_results['frontend']['build_passed'] else '❌'}")

    all_passed = (
        validation_results['backend']['dependencies_installed'] and
        validation_results['backend']['tests_passed'] and
        validation_results['frontend']['dependencies_installed'] and
        validation_results['frontend']['typescript_passed'] and
        validation_results['frontend']['build_passed']
    )

    if all_passed:
        print("\n✅ Phase 2: COMPLETE - All validations passed!")
    else:
        print("\n⚠️  Phase 2: COMPLETE - Some validations failed")

    return validation_results


def phase_3_manual_review() -> dict[str, Any]:
    """
    Phase 3: Manual review with Claude Code playground.

    This phase is interactive - requires human interaction.

    Steps:
    1. Display instructions for starting the app
    2. Display manual testing checklist
    3. Display Claude Code playground review instructions
    4. Wait for user to complete review
    5. Collect user feedback

    Returns:
        Review results dict
    """
    print("\n" + "="*80)
    print("PHASE 3: MANUAL REVIEW WITH PLAYGROUND")
    print("="*80)

    print(f"\n📂 Project Location: {TEST_WORKSPACE}")
    print(f"\n   Backend:  {TEST_WORKSPACE / 'backend'}")
    print(f"   Frontend: {TEST_WORKSPACE / 'frontend'}")

    # Step 1: Start application
    print("\n🚀 Step 1: Start Application")
    print("\n   Open 2 terminals and run:")
    print(f"\n   Terminal 1 (Backend):")
    print(f"   $ cd {TEST_WORKSPACE}/backend")
    print(f"   $ uvicorn main:app --reload")
    print(f"\n   Terminal 2 (Frontend):")
    print(f"   $ cd {TEST_WORKSPACE}/frontend")
    print(f"   $ npm run dev")
    print(f"\n   Then open: http://localhost:5173")

    # Step 2: Manual testing checklist
    print("\n🧪 Step 2: Manual Testing Checklist")
    print("\n   Test the following features:")

    checklist = [
        "User can register a new account",
        "User can login with credentials",
        "User can add new todos",
        "User can mark todos as complete/incomplete",
        "User can edit todo text",
        "User can delete todos",
        "Filter works (all, active, completed)",
        "UI is responsive (test on mobile, tablet, desktop)",
        "API endpoints work correctly (check Network tab)",
        "Error handling is user-friendly",
        "Loading states are shown",
        "Authentication persists after page reload"
    ]

    for i, item in enumerate(checklist, 1):
        print(f"   [ ] {i}. {item}")

    # Step 3: Claude Code playground review
    print("\n📝 Step 3: Claude Code Playground Review")
    print("\n   1. Open the project in VS Code:")
    print(f"      $ code {TEST_WORKSPACE}")
    print("\n   2. Open Claude Code (Cmd+Shift+P → 'Claude Code: Open')")
    print("\n   3. Ask Claude to review the app:")
    print("      - 'Review this Todo App code'")
    print("      - 'Run all tests and show results'")
    print("      - 'Are there any bugs or issues?'")
    print("      - 'Suggest improvements for code quality'")
    print("      - 'Check for security vulnerabilities'")

    # Step 4: Wait for user
    print("\n⏸️  Test Paused - Please complete the manual review")
    print("   (This may take 15-30 minutes)")
    print("\n   Press Enter when you have completed the manual review...")

    input()

    # Step 5: Collect feedback
    print("\n📊 Step 5: Review Feedback")

    review_results = {
        "completed": True,
        "timestamp": datetime.now().isoformat(),
        "manual_tests_passed": None,
        "claude_review_done": None,
        "issues_found": [],
        "improvements_suggested": []
    }

    # Ask for results
    print("\n   Did all manual tests pass? (yes/no): ", end="")
    manual_tests = input().strip().lower()
    review_results["manual_tests_passed"] = (manual_tests == "yes")

    print("\n   Did you complete Claude Code playground review? (yes/no): ", end="")
    claude_review = input().strip().lower()
    review_results["claude_review_done"] = (claude_review == "yes")

    if claude_review == "yes":
        print("\n   Did Claude find any critical issues? (yes/no): ", end="")
        issues = input().strip().lower()

        if issues == "yes":
            print("   Please describe the issues (press Enter twice when done):")
            issue_lines = []
            while True:
                line = input("   > ")
                if not line:
                    break
                issue_lines.append(line)
            review_results["issues_found"] = issue_lines

    print("\n✅ Phase 3: COMPLETE")
    print(f"   Manual Tests: {'✅ PASSED' if review_results['manual_tests_passed'] else '❌ FAILED'}")
    print(f"   Claude Review: {'✅ DONE' if review_results['claude_review_done'] else '⏭️  SKIPPED'}")

    if review_results["issues_found"]:
        print(f"   Issues Found: {len(review_results['issues_found'])}")

    return review_results


async def phase_4_comprehensive_validation(
    phase_1_results: dict[str, Any],
    phase_2_results: dict[str, Any],
    phase_3_results: dict[str, Any]
) -> dict[str, Any]:
    """
    Phase 4: Comprehensive validation.

    Combines all previous results and evaluates against success criteria.

    Args:
        phase_1_results: Results from Phase 1
        phase_2_results: Results from Phase 2
        phase_3_results: Results from Phase 3

    Returns:
        Final validation results
    """
    print("\n" + "="*80)
    print("PHASE 4: COMPREHENSIVE VALIDATION")
    print("="*80)

    # Collect all metrics
    validation = {
        "timestamp": datetime.now().isoformat(),
        "workspace": str(TEST_WORKSPACE),
        "success_criteria": TEST_CONFIG["success_criteria"],
        "results": {
            "quality_score": phase_1_results.get("quality_score", 0.0),
            "files_generated": phase_1_results.get("files_generated", 0),
            "backend_tests_passed": phase_2_results["backend"]["tests_passed"],
            "frontend_typescript_passed": phase_2_results["frontend"]["typescript_passed"],
            "frontend_build_passed": phase_2_results["frontend"]["build_passed"],
            "manual_tests_passed": phase_3_results.get("manual_tests_passed", False),
            "claude_review_done": phase_3_results.get("claude_review_done", False),
            "critical_issues_count": len(phase_3_results.get("issues_found", []))
        },
        "passed": False
    }

    # Evaluate against success criteria
    criteria = TEST_CONFIG["success_criteria"]

    checks = {
        "Quality Score": validation["results"]["quality_score"] >= criteria["quality_score_min"],
        "Backend Tests": validation["results"]["backend_tests_passed"] == criteria["tests_passing"],
        "TypeScript": validation["results"]["frontend_typescript_passed"],
        "Build": validation["results"]["frontend_build_passed"] == criteria["build_successful"],
        "Manual Tests": validation["results"]["manual_tests_passed"],
        "No Critical Issues": validation["results"]["critical_issues_count"] == 0
    }

    validation["checks"] = checks
    validation["passed"] = all(checks.values())

    # Print results
    print("\n📊 Validation Results:")
    print("\n   Success Criteria:")

    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"     {status} {check}")

    print("\n   Detailed Metrics:")
    print(f"     Quality Score: {validation['results']['quality_score']:.2f} (min: {criteria['quality_score_min']})")
    print(f"     Files Generated: {validation['results']['files_generated']}")
    print(f"     Backend Tests: {'PASSED' if validation['results']['backend_tests_passed'] else 'FAILED'}")
    print(f"     TypeScript: {'PASSED' if validation['results']['frontend_typescript_passed'] else 'FAILED'}")
    print(f"     Frontend Build: {'PASSED' if validation['results']['frontend_build_passed'] else 'FAILED'}")
    print(f"     Manual Tests: {'PASSED' if validation['results']['manual_tests_passed'] else 'FAILED'}")
    print(f"     Critical Issues: {validation['results']['critical_issues_count']}")

    # Final verdict
    print("\n" + "="*80)
    if validation["passed"]:
        print("✅ COMPREHENSIVE VALIDATION: PASSED")
        print("="*80)
        print("\n🎉 All success criteria met!")
    else:
        print("⚠️  COMPREHENSIVE VALIDATION: PARTIAL SUCCESS")
        print("="*80)
        print("\n⚠️  Some success criteria not met")

        failed_checks = [check for check, passed in checks.items() if not passed]
        print(f"\n   Failed checks: {', '.join(failed_checks)}")

    print(f"\n📂 Application Location: {TEST_WORKSPACE}")
    print("   You can continue to use and test the application.")

    return validation


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def run_native_e2e_test():
    """Run complete native E2E test with all 4 phases."""

    print("\n" + "="*80)
    print("NATIVE E2E TEST: TODO APP WITH PLAYGROUND REVIEW")
    print("="*80)
    print(f"\nTest Configuration:")
    print(f"  App: {TEST_CONFIG['app_name']}")
    print(f"  Workspace: {TEST_WORKSPACE}")
    print(f"  Backend: {TEST_CONFIG['tech_stack']['backend']}")
    print(f"  Frontend: {TEST_CONFIG['tech_stack']['frontend']}")

    start_time = datetime.now()

    test_results = {
        "start_time": start_time.isoformat(),
        "test_config": TEST_CONFIG,
        "workspace": str(TEST_WORKSPACE),
        "phases": {}
    }

    try:
        # Phase 1: Workflow execution
        print("\n🚀 Starting Phase 1...")
        phase_1_results = await phase_1_workflow_execution()
        test_results["phases"]["phase_1"] = phase_1_results

        # Phase 2: Build validation
        print("\n🚀 Starting Phase 2...")
        phase_2_results = await phase_2_build_validation()
        test_results["phases"]["phase_2"] = phase_2_results

        # Phase 3: Manual review
        print("\n🚀 Starting Phase 3...")
        phase_3_results = phase_3_manual_review()
        test_results["phases"]["phase_3"] = phase_3_results

        # Phase 4: Comprehensive validation
        print("\n🚀 Starting Phase 4...")
        phase_4_results = await phase_4_comprehensive_validation(
            phase_1_results,
            phase_2_results,
            phase_3_results
        )
        test_results["phases"]["phase_4"] = phase_4_results

        # Final summary
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        test_results["end_time"] = end_time.isoformat()
        test_results["duration_seconds"] = elapsed
        test_results["success"] = phase_4_results["passed"]

        print("\n" + "="*80)
        print("E2E TEST COMPLETE")
        print("="*80)
        print(f"\n⏱️  Total Duration: {elapsed / 60:.1f} minutes")
        print(f"📂 Application: {TEST_WORKSPACE}")

        if test_results["success"]:
            print("\n✅ SUCCESS: All phases completed successfully!")
        else:
            print("\n⚠️  PARTIAL SUCCESS: Some phases had issues")

        # Save results
        results_file = Path(__file__).parent / "e2e_native_results.json"
        with open(results_file, "w") as f:
            json.dump(test_results, f, indent=2)

        print(f"\n📄 Detailed results saved to: {results_file}")

        return test_results

    except Exception as e:
        print("\n" + "="*80)
        print("❌ E2E TEST FAILED")
        print("="*80)
        print(f"\nError: {e}")

        import traceback
        traceback.print_exc()

        test_results["error"] = str(e)
        test_results["success"] = False

        return test_results


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    print("\n🧪 Native E2E Test with Playground Review")
    print("   Version: 6.2.0")
    print("   Date: 2025-10-12")

    # Check if backend is running
    print("\n🔍 Checking backend status...")
    print(f"   Expected: Backend running at {WS_URL}")

    # Check if --auto flag is provided
    import sys
    auto_mode = "--auto" in sys.argv

    if not auto_mode:
        print("\n   If backend is not running, start it with:")
        print("   $ cd ~/.ki_autoagent")
        print("   $ ./start.sh")
        print("\n   Press Enter to continue (or run with --auto flag)...")
        input()
    else:
        print("   Running in automatic mode (--auto flag)")

    # Run test
    results = asyncio.run(run_native_e2e_test())

    # Exit code
    exit(0 if results.get("success") else 1)
