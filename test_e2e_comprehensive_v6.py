#!/usr/bin/env python3
"""
Comprehensive E2E Test for KI AutoAgent v6.1

Tests the complete workflow:
1. WebSocket connection
2. Init with workspace
3. Send app creation request
4. Monitor execution
5. Validate generated files
6. Collect logs and errors
7. Generate test report

Workspace: ~/TestApps/e2e_test_<timestamp>
Server: ws://localhost:8002/ws/chat

Author: KI AutoAgent Team
Date: 2025-10-11
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict, List

import websockets

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"/tmp/e2e_test_{datetime.now():%Y%m%d_%H%M%S}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# TEST CONFIGURATION
# ============================================================================

TEST_CONFIG = {
    "ws_url": "ws://localhost:8002/ws/chat",
    "workspace_base": Path.home() / "TestApps",
    "timeout": 900,  # 15 minutes for complex app generation
    "test_query": """Create a Task Manager web application with the following features:

Requirements:
- Modern React frontend with TypeScript
- Task CRUD operations (Create, Read, Update, Delete)
- Task categories and priorities
- Due date tracking
- Search and filter functionality
- Responsive design
- Local storage for data persistence

Technical Stack:
- React 18+ with TypeScript
- Vite for build tooling
- TailwindCSS for styling
- Modern component architecture

Please generate complete, production-ready code with:
- All necessary files (package.json, tsconfig.json, etc.)
- Clean code structure
- Type safety
- Error handling
- Comments and documentation

Generate files at the workspace root."""
}

# ============================================================================
# E2E TEST CLIENT
# ============================================================================

class E2ETestClient:
    """Comprehensive E2E test client for v6 workflow."""

    def __init__(self, ws_url: str, workspace_path: str):
        self.ws_url = ws_url
        self.workspace_path = workspace_path
        self.ws = None
        self.messages_received = []
        self.errors = []
        self.warnings = []
        self.test_results = {
            "start_time": datetime.now(),
            "end_time": None,
            "success": False,
            "connection_established": False,
            "initialization_success": False,
            "workflow_executed": False,
            "files_generated": False,
            "files_list": [],
            "agent_executions": {},
            "errors": [],
            "warnings": [],
            "execution_time": 0,
            "quality_score": 0.0,
            "v6_systems": {}
        }

    async def connect(self) -> bool:
        """Connect to WebSocket server."""
        try:
            logger.info(f"🔌 Connecting to {self.ws_url}...")
            self.ws = await websockets.connect(
                self.ws_url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            )
            logger.info("✅ WebSocket connected")
            self.test_results["connection_established"] = True
            return True
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            self.errors.append(f"Connection error: {e}")
            return False

    async def receive_message(self, timeout: float = 60) -> Optional[Dict]:
        """Receive and parse WebSocket message."""
        try:
            message = await asyncio.wait_for(
                self.ws.recv(),
                timeout=timeout
            )
            data = json.loads(message)
            self.messages_received.append(data)

            # Log message
            msg_type = data.get("type", "unknown")
            logger.info(f"📨 Received: {msg_type}")

            # Track agent executions
            if msg_type == "agent_message":
                agent = data.get("agent", "unknown")
                if agent not in self.test_results["agent_executions"]:
                    self.test_results["agent_executions"][agent] = []
                self.test_results["agent_executions"][agent].append(data)
                logger.info(f"   Agent: {agent} - {data.get('content', '')[:80]}...")

            return data

        except asyncio.TimeoutError:
            logger.warning(f"⏱️  Message timeout after {timeout}s")
            return None
        except Exception as e:
            logger.error(f"❌ Receive error: {e}")
            self.errors.append(f"Receive error: {e}")
            return None

    async def send_init(self) -> bool:
        """Send initialization message."""
        try:
            init_msg = {
                "type": "init",
                "workspace_path": self.workspace_path
            }
            logger.info(f"📤 Sending init: {self.workspace_path}")
            await self.ws.send(json.dumps(init_msg))

            # Wait for initialized response
            response = await self.receive_message(timeout=30)
            if response and response.get("type") == "initialized":
                logger.info("✅ Initialization successful")
                self.test_results["initialization_success"] = True
                self.test_results["v6_systems"] = response.get("v6_systems", {})
                return True
            else:
                logger.error(f"❌ Init failed: {response}")
                self.errors.append(f"Init failed: {response}")
                return False

        except Exception as e:
            logger.error(f"❌ Init error: {e}")
            self.errors.append(f"Init error: {e}")
            return False

    async def send_task(self, query: str) -> bool:
        """Send task/query to workflow."""
        try:
            task_msg = {
                "type": "chat",
                "message": query
            }
            logger.info(f"📤 Sending task: {query[:80]}...")
            await self.ws.send(json.dumps(task_msg))

            logger.info("⏳ Waiting for workflow execution...")
            logger.info("   This may take 10-15 minutes for complex apps...")

            # Monitor execution
            workflow_complete = False
            start_time = datetime.now()

            while not workflow_complete:
                msg = await self.receive_message(timeout=120)  # 2 min timeout per message

                if not msg:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed > TEST_CONFIG["timeout"]:
                        logger.error("❌ Workflow timeout!")
                        self.errors.append("Workflow timeout")
                        return False
                    continue

                msg_type = msg.get("type")

                # Track different message types
                if msg_type == "status":
                    logger.info(f"   Status: {msg.get('message', '')}")

                elif msg_type == "agent_message":
                    agent = msg.get("agent", "unknown")
                    content = msg.get("content", "")
                    logger.info(f"   [{agent}] {content[:100]}...")

                elif msg_type == "result":
                    # Workflow complete!
                    logger.info("✅ Workflow execution complete!")
                    workflow_complete = True
                    self.test_results["workflow_executed"] = True

                    # Extract results
                    self.test_results["success"] = msg.get("success", False)
                    self.test_results["execution_time"] = msg.get("execution_time", 0)
                    self.test_results["quality_score"] = msg.get("quality_score", 0.0)

                    result_data = msg.get("result", {})
                    logger.info(f"   Success: {msg.get('success')}")
                    logger.info(f"   Quality: {self.test_results['quality_score']:.2f}")
                    logger.info(f"   Time: {self.test_results['execution_time']:.1f}s")

                    # Check for errors in result
                    errors = msg.get("errors", [])
                    if errors:
                        logger.warning(f"   Errors: {len(errors)}")
                        self.test_results["errors"].extend(errors)

                    warnings = msg.get("warnings", [])
                    if warnings:
                        logger.warning(f"   Warnings: {len(warnings)}")
                        self.test_results["warnings"].extend(warnings)

                    return msg.get("success", False)

                elif msg_type == "error":
                    error_msg = msg.get("message", "Unknown error")
                    logger.error(f"❌ Error from server: {error_msg}")
                    self.errors.append(error_msg)
                    return False

                # Check for connection close
                try:
                    if self.ws.state.name == 'CLOSED':
                        logger.error("❌ Connection closed unexpectedly")
                        self.errors.append("Connection closed")
                        return False
                except:
                    pass  # Connection still open

            return False

        except Exception as e:
            logger.error(f"❌ Task execution error: {e}", exc_info=True)
            self.errors.append(f"Task error: {e}")
            return False

    async def validate_files(self) -> bool:
        """Validate generated files in workspace."""
        try:
            logger.info(f"🔍 Validating files in: {self.workspace_path}")

            workspace = Path(self.workspace_path)
            if not workspace.exists():
                logger.error(f"❌ Workspace not found: {workspace}")
                self.errors.append("Workspace not found")
                return False

            # Find all generated files
            generated_files = []
            for ext in ["*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.json", "*.html", "*.css", "*.md"]:
                files = list(workspace.rglob(ext))
                generated_files.extend(files)

            # Exclude system files
            generated_files = [
                f for f in generated_files
                if ".ki_autoagent_ws" not in str(f) and "node_modules" not in str(f)
            ]

            self.test_results["files_list"] = [str(f.relative_to(workspace)) for f in generated_files]

            logger.info(f"📁 Found {len(generated_files)} files:")
            for f in generated_files:
                logger.info(f"   - {f.relative_to(workspace)}")

            if generated_files:
                self.test_results["files_generated"] = True
                logger.info("✅ Files generated successfully")
                return True
            else:
                logger.error("❌ No files generated!")
                self.errors.append("No files generated")
                return False

        except Exception as e:
            logger.error(f"❌ File validation error: {e}")
            self.errors.append(f"File validation error: {e}")
            return False

    async def close(self):
        """Close WebSocket connection."""
        if self.ws and not self.ws.closed:
            await self.ws.close()
            logger.info("🔌 Connection closed")

    def generate_report(self) -> str:
        """Generate comprehensive test report."""
        self.test_results["end_time"] = datetime.now()
        total_time = (self.test_results["end_time"] - self.test_results["start_time"]).total_seconds()

        report = f"""
{'='*80}
KI AUTOAGENT v6.1 - E2E TEST REPORT
{'='*80}

Test Date: {self.test_results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}
Total Test Time: {total_time:.1f} seconds

WORKSPACE: {self.workspace_path}

{'='*80}
CONNECTION & INITIALIZATION
{'='*80}
✓ Connection Established: {self.test_results['connection_established']}
✓ Initialization Success: {self.test_results['initialization_success']}

v6 Systems Active:
"""
        for system, status in self.test_results["v6_systems"].items():
            report += f"  - {system}: {'✓' if status else '✗'}\n"

        report += f"""
{'='*80}
WORKFLOW EXECUTION
{'='*80}
✓ Workflow Executed: {self.test_results['workflow_executed']}
✓ Files Generated: {self.test_results['files_generated']}
✓ Overall Success: {self.test_results['success']}

Execution Time: {self.test_results['execution_time']:.1f} seconds
Quality Score: {self.test_results['quality_score']:.2f}

{'='*80}
AGENT EXECUTIONS
{'='*80}
"""
        for agent, executions in self.test_results["agent_executions"].items():
            report += f"\n{agent.upper()}: {len(executions)} messages\n"
            for msg in executions[:3]:  # Show first 3 messages
                content = msg.get("content", "")[:100]
                report += f"  - {content}...\n"

        report += f"""
{'='*80}
GENERATED FILES ({len(self.test_results['files_list'])})
{'='*80}
"""
        for file in self.test_results["files_list"]:
            report += f"  - {file}\n"

        if self.test_results["errors"]:
            report += f"""
{'='*80}
ERRORS ({len(self.test_results['errors'])})
{'='*80}
"""
            for error in self.test_results["errors"]:
                report += f"  ❌ {error}\n"

        if self.test_results["warnings"]:
            report += f"""
{'='*80}
WARNINGS ({len(self.test_results['warnings'])})
{'='*80}
"""
            for warning in self.test_results["warnings"]:
                report += f"  ⚠️  {warning}\n"

        report += f"""
{'='*80}
TEST SUMMARY
{'='*80}
Overall Result: {'✅ PASS' if self.test_results['success'] and self.test_results['files_generated'] else '❌ FAIL'}
Total Messages Received: {len(self.messages_received)}
Errors: {len(self.test_results['errors'])}
Warnings: {len(self.test_results['warnings'])}

{'='*80}
"""
        return report

# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================

async def run_e2e_test():
    """Run comprehensive E2E test."""

    print("="*80)
    print("KI AUTOAGENT v6.1 - COMPREHENSIVE E2E TEST")
    print("="*80)
    print()

    # Create test workspace
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    workspace = TEST_CONFIG["workspace_base"] / f"e2e_test_{timestamp}"
    workspace.mkdir(parents=True, exist_ok=True)

    logger.info(f"📂 Test workspace: {workspace}")
    logger.info(f"🌐 Server: {TEST_CONFIG['ws_url']}")
    logger.info(f"⏱️  Timeout: {TEST_CONFIG['timeout']}s")
    print()

    # Initialize client
    client = E2ETestClient(
        ws_url=TEST_CONFIG["ws_url"],
        workspace_path=str(workspace)
    )

    try:
        # Step 1: Connect
        logger.info("STEP 1: Connecting to WebSocket server...")
        if not await client.connect():
            logger.error("❌ Connection failed - aborting test")
            return

        # Wait for welcome message
        welcome = await client.receive_message(timeout=10)
        if not welcome or welcome.get("type") != "connected":
            logger.error(f"❌ No welcome message: {welcome}")
            return

        logger.info("✅ Server connection established")
        print()

        # Step 2: Initialize
        logger.info("STEP 2: Initializing workflow...")
        if not await client.send_init():
            logger.error("❌ Initialization failed - aborting test")
            return

        logger.info("✅ Workflow initialized")
        print()

        # Step 3: Execute task
        logger.info("STEP 3: Executing app generation task...")
        logger.info("⏳ This will take 10-15 minutes...")
        print()

        success = await client.send_task(TEST_CONFIG["test_query"])

        if not success:
            logger.error("❌ Task execution failed")
        else:
            logger.info("✅ Task execution completed")

        print()

        # Step 4: Validate files
        logger.info("STEP 4: Validating generated files...")
        await client.validate_files()
        print()

        # Step 5: Generate report
        logger.info("STEP 5: Generating test report...")
        report = client.generate_report()

        # Save report
        report_path = workspace / "E2E_TEST_REPORT.md"
        report_path.write_text(report)

        # Also save to project root
        project_report = Path.cwd() / f"E2E_TEST_RESULTS_{timestamp}.md"
        project_report.write_text(report)

        logger.info(f"📄 Report saved to: {report_path}")
        logger.info(f"📄 Report saved to: {project_report}")
        print()

        # Print report
        print(report)

        # Final result
        if client.test_results["success"] and client.test_results["files_generated"]:
            logger.info("🎉 E2E TEST PASSED!")
            print()
            print("✅ ALL TESTS PASSED")
            print(f"✅ Workspace: {workspace}")
            print(f"✅ Files generated: {len(client.test_results['files_list'])}")
            return 0
        else:
            logger.error("❌ E2E TEST FAILED!")
            print()
            print("❌ TEST FAILED")
            print(f"❌ Errors: {len(client.test_results['errors'])}")
            print(f"❌ Check logs for details")
            return 1

    except Exception as e:
        logger.error(f"❌ Test exception: {e}", exc_info=True)
        print()
        print(f"❌ FATAL ERROR: {e}")
        return 1

    finally:
        await client.close()

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    print()
    print("Starting E2E test...")
    print("Make sure server is running: python backend/api/server_v6_integrated.py")
    print()

    exit_code = asyncio.run(run_e2e_test())
    sys.exit(exit_code)
