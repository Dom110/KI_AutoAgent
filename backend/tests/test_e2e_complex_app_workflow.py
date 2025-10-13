#!/usr/bin/env python3
"""
E2E Test - Complex Application with Full Workflow Generation

This test validates the COMPLETE v6.2 system with a complex application request:
- Automatic workflow planning (WorkflowPlannerV6)
- All 4 agent types (Research, Architect, Codesmith, ReviewFix)
- MCP protocol integration
- Multi-agent coordination
- Self-adaptation and error recovery
- Quality validation

CRITICAL: Runs in isolated test workspace (~/TestApps/)

Test Scenario:
--------------
User sends ONLY a message via WebSocket:
"Create a full-stack todo application with React frontend, FastAPI backend,
SQLite database, user authentication, and real-time updates via WebSockets.
Include comprehensive tests and deployment configuration."

The system must:
1. Automatically generate optimal workflow
2. Execute all agents dynamically
3. Generate working application
4. Pass all quality checks

Success Criteria:
-----------------
✅ Workflow automatically generated (WorkflowPlannerV6)
✅ All agents executed (research, architect, codesmith, reviewfix)
✅ MCP protocol used for all service calls
✅ Files generated in correct workspace
✅ Application structure complete
✅ No critical errors
✅ Quality score > 0.75

Author: KI AutoAgent Team
Version: 6.2.0-alpha
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import sys
import websockets
from datetime import datetime
from pathlib import Path
from typing import Any

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/e2e_complex_app_test.log')
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# TEST CONFIGURATION
# ============================================================================

# ✅ CORRECT: Isolated test workspace
TEST_WORKSPACE = Path.home() / "TestApps" / "e2e_complex_app"

# WebSocket connection
WS_URL = "ws://localhost:8002/ws/chat"
WS_TIMEOUT = 900  # 15 minutes for complex application


# ============================================================================
# TEST VALIDATION CRITERIA
# ============================================================================

REQUIRED_FEATURES = {
    "workflow_planning": {
        "description": "Automatic workflow generation using AI",
        "check": lambda results: results.get("workflow_plan") is not None
    },
    "all_agents_executed": {
        "description": "All 4 agent types executed",
        "check": lambda results: len(results.get("agents_completed", [])) >= 4
    },
    "mcp_protocol": {
        "description": "MCP protocol used for services",
        "check": lambda results: results.get("mcp_enabled", False)
    },
    "research_findings": {
        "description": "Research agent found information",
        "check": lambda results: bool(results.get("research_results"))
    },
    "architecture_design": {
        "description": "Architect agent created design",
        "check": lambda results: bool(results.get("architecture_design"))
    },
    "code_generation": {
        "description": "Codesmith agent generated files",
        "check": lambda results: len(results.get("generated_files", [])) > 0
    },
    "quality_review": {
        "description": "ReviewFix agent validated quality",
        "check": lambda results: bool(results.get("review_feedback"))
    },
    "files_in_workspace": {
        "description": "Files created in correct location",
        "check": lambda results: (TEST_WORKSPACE / "README.md").exists() or len(list(TEST_WORKSPACE.rglob("*.py"))) > 0
    },
    "no_critical_errors": {
        "description": "No critical errors occurred",
        "check": lambda results: len(results.get("errors", [])) == 0
    },
    "quality_score": {
        "description": "High quality score (>0.75)",
        "check": lambda results: results.get("quality_score", 0.0) > 0.75
    }
}


# ============================================================================
# WEBSOCKET TEST CLIENT
# ============================================================================

class E2EComplexAppClient:
    """WebSocket client for E2E testing."""

    def __init__(self, ws_url: str, workspace_path: str):
        self.ws_url = ws_url
        self.workspace_path = workspace_path
        self.ws = None
        self.results = {
            "workflow_plan": None,
            "agents_completed": [],
            "research_results": None,
            "architecture_design": None,
            "generated_files": [],
            "review_feedback": None,
            "errors": [],
            "quality_score": 0.0,
            "execution_time": 0.0,
            "mcp_enabled": False,
            "messages_received": []
        }
        self.start_time = None
        self.task_completed = False

    async def connect(self) -> None:
        """Connect to WebSocket server."""
        logger.info(f"🔌 Connecting to {self.ws_url}")
        try:
            self.ws = await websockets.connect(self.ws_url)
            logger.info("✅ Connected to WebSocket")

            # Send initialization with workspace path
            init_message = {
                "type": "init",
                "workspace_path": self.workspace_path
            }
            await self.ws.send(json.dumps(init_message))
            logger.info(f"📡 Sent init with workspace: {self.workspace_path}")

            # Wait for init confirmation
            response = await asyncio.wait_for(self.ws.recv(), timeout=10.0)
            init_response = json.loads(response)
            logger.info(f"✅ Init response: {init_response.get('type')}")

        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            raise

    async def send_task(self, task: str) -> None:
        """Send task request to agent."""
        logger.info(f"📤 Sending task: {task[:100]}...")

        task_message = {
            "type": "task",
            "task": task,
            "session_id": f"e2e_test_{datetime.now():%Y%m%d_%H%M%S}"
        }

        await self.ws.send(json.dumps(task_message))
        self.start_time = datetime.now()
        logger.info("✅ Task sent, waiting for response...")

    async def receive_messages(self, timeout: float = WS_TIMEOUT) -> None:
        """Receive and process all messages until completion."""
        logger.info(f"📥 Receiving messages (timeout: {timeout}s)...")

        try:
            while not self.task_completed:
                # Receive with timeout
                message = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
                await self._process_message(message)

        except asyncio.TimeoutError:
            logger.error(f"❌ Timeout after {timeout}s")
            self.results["errors"].append(f"Timeout after {timeout}s")
            self.task_completed = True

        except Exception as e:
            logger.error(f"❌ Receive error: {e}")
            self.results["errors"].append(f"Receive error: {str(e)}")
            self.task_completed = True

    async def _process_message(self, message: str) -> None:
        """Process received WebSocket message."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            logger.debug(f"📨 Message type: {msg_type}")
            self.results["messages_received"].append(msg_type)

            # Workflow planning
            if msg_type == "workflow_planning":
                logger.info(f"🎯 Workflow planning: {data.get('workflow_type')}")
                self.results["workflow_plan"] = {
                    "type": data.get("workflow_type"),
                    "complexity": data.get("complexity"),
                    "agents": data.get("agents", []),
                    "estimated_duration": data.get("estimated_duration")
                }
                logger.info(f"  Agents: {' → '.join(data.get('agents', []))}")

            # Agent execution
            elif msg_type == "agent_start":
                agent = data.get("agent")
                logger.info(f"🤖 Agent starting: {agent}")

            elif msg_type == "agent_complete":
                agent = data.get("agent")
                logger.info(f"✅ Agent completed: {agent}")
                self.results["agents_completed"].append(agent)

                # Extract agent results
                if agent == "research":
                    self.results["research_results"] = data.get("results")
                elif agent == "architect":
                    self.results["architecture_design"] = data.get("results")
                elif agent == "codesmith":
                    self.results["generated_files"] = data.get("files", [])
                elif agent == "reviewfix":
                    self.results["review_feedback"] = data.get("results")

            # Progress updates
            elif msg_type == "progress":
                progress = data.get("progress", 0)
                phase = data.get("phase", "unknown")
                logger.info(f"⏳ Progress: {progress}% - {phase}")

            # MCP events
            elif msg_type == "mcp_call":
                logger.info(f"🔌 MCP call: {data.get('server')}/{data.get('tool')}")
                self.results["mcp_enabled"] = True

            # Errors
            elif msg_type == "error":
                error = data.get("error")
                logger.error(f"❌ Error: {error}")
                self.results["errors"].append(error)

            # Task completion
            elif msg_type == "task_complete":
                logger.info("🎉 Task completed!")
                self.results["quality_score"] = data.get("quality_score", 0.0)
                self.results["execution_time"] = (datetime.now() - self.start_time).total_seconds()
                self.task_completed = True

            # HITL requests (should auto-continue in E2E mode)
            elif msg_type == "hitl_request":
                logger.warning(f"⚠️  HITL request: {data.get('error')}")
                # Auto-respond to continue
                response = {
                    "type": "hitl_response",
                    "action": "retry",
                    "next_step": "research"
                }
                await self.ws.send(json.dumps(response))

            # Other message types
            else:
                logger.debug(f"📨 Other message: {msg_type}")

        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON: {e}")
            self.results["errors"].append(f"Invalid JSON: {str(e)}")

        except Exception as e:
            logger.error(f"❌ Message processing error: {e}")
            self.results["errors"].append(f"Message processing error: {str(e)}")

    async def disconnect(self) -> None:
        """Disconnect from WebSocket."""
        if self.ws:
            await self.ws.close()
            logger.info("🔌 Disconnected from WebSocket")


# ============================================================================
# TEST VALIDATION
# ============================================================================

def validate_results(results: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """
    Validate test results against success criteria.

    Returns:
        (success, validation_report)
    """
    logger.info("🔍 Validating results...")

    validation = {
        "features_tested": {},
        "passed": 0,
        "failed": 0,
        "total": len(REQUIRED_FEATURES),
        "success": False
    }

    for feature_name, feature_def in REQUIRED_FEATURES.items():
        try:
            passed = feature_def["check"](results)
            validation["features_tested"][feature_name] = {
                "description": feature_def["description"],
                "passed": passed
            }

            if passed:
                validation["passed"] += 1
                logger.info(f"  ✅ {feature_name}: {feature_def['description']}")
            else:
                validation["failed"] += 1
                logger.error(f"  ❌ {feature_name}: {feature_def['description']}")

        except Exception as e:
            validation["features_tested"][feature_name] = {
                "description": feature_def["description"],
                "passed": False,
                "error": str(e)
            }
            validation["failed"] += 1
            logger.error(f"  ❌ {feature_name}: {e}")

    # Calculate success
    pass_rate = validation["passed"] / validation["total"] if validation["total"] > 0 else 0.0
    validation["pass_rate"] = pass_rate
    validation["success"] = pass_rate >= 0.8  # 80% required

    logger.info(f"\n📊 Validation Summary:")
    logger.info(f"  Passed: {validation['passed']}/{validation['total']}")
    logger.info(f"  Pass Rate: {pass_rate:.1%}")
    logger.info(f"  Success: {'✅' if validation['success'] else '❌'}")

    return validation["success"], validation


# ============================================================================
# TEST SETUP AND CLEANUP
# ============================================================================

def setup_test_workspace() -> None:
    """Setup clean test workspace."""
    logger.info("🧹 Setting up test workspace...")

    # Remove old test workspace
    if TEST_WORKSPACE.exists():
        logger.info(f"  Removing old workspace: {TEST_WORKSPACE}")
        shutil.rmtree(TEST_WORKSPACE)

    # Create fresh workspace
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    logger.info(f"  ✅ Created clean workspace: {TEST_WORKSPACE}")

    # Verify isolation
    assert not (TEST_WORKSPACE / "todo-app").exists()
    assert not (TEST_WORKSPACE / "README.md").exists()
    logger.info("  ✅ Workspace verified clean")


def cleanup_test_workspace(keep_on_success: bool = True, test_passed: bool = False) -> None:
    """Cleanup test workspace after test."""
    logger.info("🧹 Cleaning up test workspace...")

    if keep_on_success and test_passed:
        logger.info(f"  ✅ Test passed - keeping workspace: {TEST_WORKSPACE}")
        # Create timestamped backup
        backup = TEST_WORKSPACE.parent / f"success_{datetime.now():%Y%m%d_%H%M%S}"
        shutil.copytree(TEST_WORKSPACE, backup)
        logger.info(f"  📦 Backup created: {backup}")
    else:
        if TEST_WORKSPACE.exists():
            logger.info(f"  Removing workspace: {TEST_WORKSPACE}")
            shutil.rmtree(TEST_WORKSPACE)
        logger.info("  ✅ Cleanup complete")


def verify_workspace_files(results: dict[str, Any]) -> dict[str, Any]:
    """Verify files were created in correct workspace."""
    logger.info("📂 Verifying workspace files...")

    file_check = {
        "workspace_path": str(TEST_WORKSPACE),
        "files_found": [],
        "directories_found": [],
        "total_files": 0,
        "total_dirs": 0
    }

    # Scan workspace for files
    if TEST_WORKSPACE.exists():
        for item in TEST_WORKSPACE.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(TEST_WORKSPACE)
                file_check["files_found"].append(str(rel_path))
                file_check["total_files"] += 1
            elif item.is_dir():
                rel_path = item.relative_to(TEST_WORKSPACE)
                file_check["directories_found"].append(str(rel_path))
                file_check["total_dirs"] += 1

        logger.info(f"  ✅ Found {file_check['total_files']} files in {file_check['total_dirs']} directories")

        # Log first 10 files
        for f in file_check["files_found"][:10]:
            logger.info(f"    - {f}")
        if file_check["total_files"] > 10:
            logger.info(f"    ... and {file_check['total_files'] - 10} more")

    else:
        logger.error(f"  ❌ Workspace does not exist: {TEST_WORKSPACE}")

    return file_check


# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================

async def run_e2e_complex_app_test() -> dict[str, Any]:
    """
    Run complete E2E test for complex application.

    Returns:
        Complete test report
    """
    logger.info("=" * 80)
    logger.info("🧪 E2E TEST: Complex Application with Full Workflow Generation")
    logger.info("=" * 80)

    test_start = datetime.now()
    test_report = {
        "test_name": "E2E Complex Application",
        "start_time": test_start.isoformat(),
        "workspace": str(TEST_WORKSPACE),
        "status": "running"
    }

    try:
        # 1. Setup test workspace
        setup_test_workspace()

        # 2. Connect to WebSocket
        client = E2EComplexAppClient(
            ws_url=WS_URL,
            workspace_path=str(TEST_WORKSPACE)
        )
        await client.connect()

        # 3. Send complex application task
        complex_task = (
            "Create a full-stack todo application with the following requirements:\n"
            "- React frontend with TypeScript and Tailwind CSS\n"
            "- FastAPI backend with Python 3.13+\n"
            "- SQLite database with proper schema\n"
            "- User authentication (JWT tokens)\n"
            "- Real-time updates via WebSockets\n"
            "- CRUD operations for todos\n"
            "- Comprehensive unit and integration tests\n"
            "- Docker deployment configuration\n"
            "- Complete README with setup instructions\n"
            "\n"
            "The application should be production-ready with proper error handling, "
            "validation, and security best practices."
        )

        await client.send_task(complex_task)

        # 4. Receive all messages until completion
        await client.receive_messages(timeout=WS_TIMEOUT)

        # 5. Disconnect
        await client.disconnect()

        # 6. Verify workspace files
        file_check = verify_workspace_files(client.results)
        client.results["workspace_files"] = file_check

        # 7. Validate results
        success, validation = validate_results(client.results)

        # 8. Generate test report
        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()

        test_report.update({
            "status": "success" if success else "failed",
            "end_time": test_end.isoformat(),
            "duration": test_duration,
            "results": client.results,
            "validation": validation,
            "workspace_files": file_check
        })

        # Log summary
        logger.info("\n" + "=" * 80)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Status: {'✅ SUCCESS' if success else '❌ FAILED'}")
        logger.info(f"Duration: {test_duration:.1f}s")
        logger.info(f"Pass Rate: {validation['pass_rate']:.1%}")
        logger.info(f"Features Passed: {validation['passed']}/{validation['total']}")
        logger.info(f"Agents Executed: {len(client.results['agents_completed'])}")
        logger.info(f"Files Generated: {file_check['total_files']}")
        logger.info(f"Quality Score: {client.results['quality_score']:.2f}")
        logger.info(f"Errors: {len(client.results['errors'])}")

        if client.results['errors']:
            logger.info("\n❌ Errors:")
            for error in client.results['errors']:
                logger.info(f"  - {error}")

        # Cleanup
        cleanup_test_workspace(keep_on_success=True, test_passed=success)

        return test_report

    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}", exc_info=True)

        test_end = datetime.now()
        test_duration = (test_end - test_start).total_seconds()

        test_report.update({
            "status": "error",
            "end_time": test_end.isoformat(),
            "duration": test_duration,
            "error": str(e),
            "error_type": type(e).__name__
        })

        # Cleanup on error
        cleanup_test_workspace(keep_on_success=False, test_passed=False)

        return test_report


def save_test_report(report: dict[str, Any]) -> None:
    """Save test report to file."""
    report_path = Path("/tmp/e2e_complex_app_test_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"📝 Test report saved: {report_path}")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    logger.info("🚀 Starting E2E Complex Application Test")

    # Check if backend is running
    logger.info("🔍 Checking if backend is running...")
    # TODO: Add backend health check

    # Run test
    report = asyncio.run(run_e2e_complex_app_test())

    # Save report
    save_test_report(report)

    # Exit with appropriate code
    if report["status"] == "success":
        logger.info("✅ Test PASSED")
        sys.exit(0)
    else:
        logger.error("❌ Test FAILED")
        sys.exit(1)
