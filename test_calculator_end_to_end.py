#!/usr/bin/env python3
"""
End-to-End Test for KI AutoAgent Calculator App Creation
Tests complete workflow: Request → Research → Architect → Approval → CodeSmith → Files Created

v5.8.7 - Complete workflow test including approval and code generation
"""

import asyncio
import websockets
import json
import logging
import tempfile
import shutil
import os
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CalculatorEndToEndTest:
    def __init__(self):
        self.ws = None
        self.session_id = None
        self.test_workspace = None
        self.architecture_proposal = None
        self.files_created = []
        self.messages_received = 0
        self.errors = []
        self.warnings = []

    async def setup(self):
        """Create test workspace"""
        self.test_workspace = tempfile.mkdtemp(prefix="test_calculator_e2e_")
        logger.info(f"✅ Created test workspace: {self.test_workspace}")

    async def teardown(self):
        """Cleanup test workspace"""
        if self.test_workspace and os.path.exists(self.test_workspace):
            shutil.rmtree(self.test_workspace)
            logger.info(f"🧹 Cleaned up test workspace")

    async def connect(self):
        """Connect to backend WebSocket"""
        uri = "ws://localhost:8001/ws/chat"
        logger.info(f"🔌 Connecting to backend: {uri}")
        self.ws = await websockets.connect(uri)
        logger.info("✅ Connected!")

        # Wait for connection message
        msg = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
        connection_data = json.loads(msg)
        logger.info(f"📨 Connection: {connection_data}")

        # Send init message
        init_msg = {
            "type": "init",
            "workspace_path": self.test_workspace
        }
        await self.ws.send(json.dumps(init_msg))
        logger.info("📤 Sent init message")

        # Wait for init response
        init_response = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
        init_data = json.loads(init_response)
        self.session_id = init_data.get("session_id")
        logger.info(f"📨 Init response: {init_data}")

    async def send_message(self, message: str):
        """Send chat message to backend"""
        logger.info(f"\n📤 Sending test message: '{message}'")
        msg = {
            "type": "chat",
            "content": message,
            "agent": "orchestrator"
        }
        await self.ws.send(json.dumps(msg))
        logger.info("✅ Message sent")

    async def send_approval(self):
        """Send architecture approval"""
        logger.info(f"\n📤 Sending APPROVAL for session {self.session_id}")
        approval_msg = {
            "type": "architecture_approval",
            "decision": "approved",
            "feedback": "",
            "session_id": self.session_id
        }
        await self.ws.send(json.dumps(approval_msg))
        logger.info("✅ Approval sent")

    async def collect_responses(self, timeout: int = 480):
        """Collect responses from backend until completion (v5.8.7: increased to 480s for OpenAI timeout handling)"""
        logger.info(f"\n📥 Collecting responses (timeout: {timeout}s)...")
        start_time = datetime.now()
        proposal_received = False
        approval_sent = False
        codesmith_started = False

        while True:
            elapsed = (datetime.now() - start_time).total_seconds()
            remaining = timeout - elapsed

            if remaining <= 0:
                logger.error(f"❌ Timeout after {timeout}s")
                self.errors.append(f"Test timeout after {timeout}s")
                break

            try:
                msg = await asyncio.wait_for(self.ws.recv(), timeout=10.0)
                data = json.loads(msg)
                self.messages_received += 1
                msg_type = data.get("type")

                # Log agent activity
                if msg_type == "agent_thinking":
                    agent = data.get("agent", "unknown")
                    logger.info(f"  💭 [{agent}] thinking...")

                elif msg_type == "agent_progress":
                    agent = data.get("agent", "unknown")
                    content = data.get("content", "")[:100]
                    logger.info(f"  🔄 [{agent}] {content}...")

                    # Detect CodeSmith activity
                    if agent == "codesmith" and not codesmith_started:
                        codesmith_started = True
                        logger.info(f"\n🎉 CodeSmith STARTED - Files should be created soon!")

                # Capture architecture proposal
                elif msg_type == "architecture_proposal":
                    self.architecture_proposal = data.get("proposal", data.get("content", ""))
                    proposal_received = True
                    logger.info(f"\n📋 Architecture Proposal Received!")
                    logger.info("=" * 80)

                    # Log short summary
                    if isinstance(self.architecture_proposal, dict):
                        summary = self.architecture_proposal.get("summary", "")
                        logger.info(f"Summary: {summary[:150]}...")
                    else:
                        logger.info(f"{str(self.architecture_proposal)[:200]}...")
                    logger.info("=" * 80)

                    # v5.8.7: AUTO-APPROVE after 2 seconds (simulate user approval)
                    logger.info("\n⏳ Waiting 2s before sending approval...")
                    await asyncio.sleep(2)
                    await self.send_approval()
                    approval_sent = True
                    logger.info("✅ Approval sent, waiting for CodeSmith to create files...")

                # Capture approval confirmation
                elif msg_type == "architectureApprovalProcessed":
                    logger.info(f"\n✅ Approval processed by backend")

                # Capture file creation events
                elif msg_type == "file_created" or msg_type == "file_written":
                    file_path = data.get("file_path", data.get("path", "unknown"))
                    self.files_created.append(file_path)
                    logger.info(f"\n📄 File Created: {file_path}")

                # Capture final response (workflow complete)
                elif msg_type == "response":
                    content = data.get("content", "")
                    logger.info(f"\n🎉 Final Response (Workflow Complete):")
                    logger.info("=" * 80)
                    logger.info(content[:500] if len(content) > 500 else content)
                    logger.info("=" * 80)

                    # Check if files were created
                    if approval_sent and not self.files_created:
                        logger.warning("⚠️ Workflow complete but NO files created!")
                        self.warnings.append("No files created")

                    # Success!
                    logger.info(f"\n✅ Workflow completed successfully!")
                    break

                # Error handling
                elif msg_type == "error":
                    error_msg = data.get("content", data.get("error", "Unknown error"))
                    logger.error(f"\n❌ Error: {error_msg}")
                    self.errors.append(error_msg)
                    break

            except asyncio.TimeoutError:
                logger.warning("⚠️ No response for 10s, waiting...")
            except websockets.exceptions.ConnectionClosed:
                logger.warning("🔌 Connection closed by server")
                if not approval_sent:
                    logger.error("❌ Connection closed BEFORE approval sent")
                    self.errors.append("Connection closed before approval")
                elif not self.files_created:
                    logger.error("❌ Connection closed BEFORE files created")
                    self.errors.append("Connection closed before file creation")
                break
            except Exception as e:
                logger.error(f"❌ Error receiving message: {e}")
                self.errors.append(str(e))
                break

    def validate_results(self):
        """Validate test results"""
        logger.info("\n" + "=" * 80)
        logger.info("🔍 VALIDATING RESULTS")
        logger.info("=" * 80)

        success = True

        # Check proposal received
        if not self.architecture_proposal:
            logger.error("❌ FAIL: No architecture proposal received")
            success = False
        else:
            logger.info("✅ Architecture proposal received")

        # Check files created
        if not self.files_created:
            logger.error("❌ FAIL: No files were created")
            success = False
        else:
            logger.info(f"✅ Files created: {len(self.files_created)}")
            for file_path in self.files_created:
                logger.info(f"   - {file_path}")

        # Check for errors
        if self.errors:
            logger.error(f"❌ FAIL: {len(self.errors)} errors occurred:")
            for error in self.errors:
                logger.error(f"   - {error}")
            success = False
        else:
            logger.info("✅ No errors")

        # Check for warnings
        if self.warnings:
            logger.warning(f"⚠️ {len(self.warnings)} warnings:")
            for warning in self.warnings:
                logger.warning(f"   - {warning}")

        # Check actual files on disk
        logger.info("\n🔍 Checking files on disk:")
        workspace_path = Path(self.test_workspace)
        actual_files = list(workspace_path.rglob("*"))
        actual_files = [f for f in actual_files if f.is_file()]

        if actual_files:
            logger.info(f"✅ Found {len(actual_files)} files on disk:")
            for file in actual_files:
                rel_path = file.relative_to(workspace_path)
                size = file.stat().st_size
                logger.info(f"   - {rel_path} ({size} bytes)")
        else:
            logger.error("❌ No files found on disk!")
            success = False

        return success

    def print_summary(self, success: bool):
        """Print test summary"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Messages received: {self.messages_received}")
        logger.info(f"Architecture proposal: {'✅ Received' if self.architecture_proposal else '❌ Not received'}")
        logger.info(f"Files created (events): {len(self.files_created)}")
        logger.info(f"Errors: {len(self.errors)}")
        logger.info(f"Warnings: {len(self.warnings)}")

        if self.errors:
            logger.info("\n❌ Errors:")
            for error in self.errors:
                logger.info(f"   - {error}")

        logger.info("\n" + "=" * 80)
        if success:
            logger.info("✅ RESULT: PASSED - Complete End-to-End workflow successful!")
        else:
            logger.info("❌ RESULT: FAILED - See errors above")
        logger.info("=" * 80)


async def main():
    """Run end-to-end test"""
    logger.info("=" * 80)
    logger.info("🚀 Starting Calculator End-to-End Test (v5.8.7)")
    logger.info("=" * 80)

    test = CalculatorEndToEndTest()

    try:
        # Setup
        await test.setup()

        # Connect
        await test.connect()

        # Send message
        await test.send_message("Create a simple HTML calculator app")

        # Collect responses (includes auto-approval after proposal)
        await test.collect_responses(timeout=300)  # 5 minutes max

        # Validate
        success = test.validate_results()

        # Summary
        test.print_summary(success)

        # Cleanup
        await test.teardown()

        # Exit with appropriate code
        exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("\n⚠️ Test interrupted by user")
        await test.teardown()
        exit(2)
    except Exception as e:
        logger.error(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        await test.teardown()
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
