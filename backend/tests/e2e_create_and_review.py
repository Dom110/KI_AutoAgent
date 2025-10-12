#!/usr/bin/env python3
"""
E2E Test: CREATE Workflow + REVIEW Workflow

Tests:
1. WebSocket connection to backend
2. CREATE workflow: Generate a simple app
3. REVIEW workflow: Review generated code
4. Verify both workflows complete successfully

IMPORTANT: Runs in isolated test workspace (NOT development repo!)
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from datetime import datetime
import websockets

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test workspace (isolated from development repo)
TEST_WORKSPACE = Path.home() / "TestApps" / f"e2e_test_{datetime.now():%Y%m%d_%H%M%S}"

# Backend WebSocket URL
WS_URL = "ws://localhost:8002/ws/chat"


class E2ETestClient:
    """E2E Test Client for WebSocket communication"""

    def __init__(self, ws_url: str, workspace_path: str):
        self.ws_url = ws_url
        self.workspace_path = workspace_path
        self.websocket = None
        self.session_id = None
        self.responses = []

    async def connect(self):
        """Connect to WebSocket and initialize session"""
        logger.info(f"🔌 Connecting to {self.ws_url}")
        self.websocket = await websockets.connect(self.ws_url)

        # Wait for connected message
        msg = await self.websocket.recv()
        data = json.loads(msg)
        logger.info(f"✅ Connected: {data}")

        # Send init message with workspace
        init_msg = {
            "type": "init",
            "workspace_path": self.workspace_path
        }
        await self.websocket.send(json.dumps(init_msg))
        logger.info(f"📤 Sent init with workspace: {self.workspace_path}")

        # Wait for initialized confirmation
        msg = await self.websocket.recv()
        data = json.loads(msg)

        if data.get("type") == "initialized":
            self.session_id = data.get("session_id")
            logger.info(f"✅ Session initialized: {self.session_id}")
            logger.info(f"   Workspace: {data.get('workspace_path')}")
            return True
        else:
            logger.error(f"❌ Init failed: {data}")
            return False

    async def send_task(self, task: str):
        """Send task to backend and collect responses"""
        logger.info(f"📤 Sending task: {task[:100]}...")

        # Send task message
        task_msg = {
            "type": "message",
            "content": task
        }
        await self.websocket.send(json.dumps(task_msg))

        # Collect responses
        self.responses = []
        workflow_complete = False

        logger.info("⏳ Waiting for responses...")

        while not workflow_complete:
            try:
                msg = await asyncio.wait_for(self.websocket.recv(), timeout=300.0)
                data = json.loads(msg)

                msg_type = data.get("type")

                if msg_type == "agent_response":
                    content = data.get("content", "")
                    logger.info(f"📨 Agent response: {content[:150]}...")
                    self.responses.append(data)

                elif msg_type == "workflow_complete":
                    logger.info("✅ Workflow complete!")
                    logger.info(f"   Final output: {data.get('final_output', {})}")
                    self.responses.append(data)
                    workflow_complete = True

                elif msg_type == "error":
                    logger.error(f"❌ Error: {data.get('error')}")
                    self.responses.append(data)
                    workflow_complete = True

                elif msg_type == "status":
                    status = data.get("status")
                    logger.info(f"📊 Status: {status}")

                else:
                    logger.debug(f"📬 Received: {msg_type}")
                    self.responses.append(data)

            except asyncio.TimeoutError:
                logger.error("⏱️ Timeout waiting for response (5 minutes)")
                break
            except Exception as e:
                logger.error(f"❌ Error receiving message: {e}")
                break

        return self.responses

    async def close(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            logger.info("🔌 Connection closed")

    def get_workflow_result(self) -> dict | None:
        """Extract final workflow result from responses"""
        for response in reversed(self.responses):
            if response.get("type") == "workflow_complete":
                return response.get("final_output")
        return None


async def setup_test_workspace():
    """Setup clean test workspace"""
    logger.info(f"🧪 Setting up test workspace: {TEST_WORKSPACE}")

    # Create workspace
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)

    # Verify it's clean
    existing_files = list(TEST_WORKSPACE.glob("*"))
    if existing_files:
        logger.warning(f"⚠️ Workspace not empty: {len(existing_files)} files found")
    else:
        logger.info("✅ Workspace is clean")

    return str(TEST_WORKSPACE)


async def test_create_workflow(client: E2ETestClient):
    """Test CREATE workflow - generate a simple app"""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: CREATE WORKFLOW - Generate Simple App")
    logger.info("="*60)

    task = """
Create a simple Task Manager web application with the following features:

**Backend (Python):**
- FastAPI server with CORS
- REST API endpoints:
  - GET /tasks - List all tasks
  - POST /tasks - Create new task
  - PUT /tasks/{id} - Update task
  - DELETE /tasks/{id} - Delete task
- In-memory storage (list)
- Task model: id, title, description, completed

**Frontend (HTML/JS):**
- Simple single-page HTML interface
- Display tasks in a list
- Form to add new tasks
- Buttons to complete/delete tasks
- Vanilla JavaScript (no frameworks)

**Files to create:**
- backend/main.py (FastAPI server)
- backend/models.py (Task model)
- frontend/index.html (UI)
- README.md (setup instructions)

Keep it simple and functional. Generate all files.
"""

    start_time = time.time()
    responses = await client.send_task(task)
    duration = time.time() - start_time

    logger.info(f"⏱️ CREATE workflow completed in {duration:.1f}s")
    logger.info(f"📊 Received {len(responses)} responses")

    # Verify result
    result = client.get_workflow_result()

    if result:
        logger.info("✅ CREATE workflow succeeded!")
        logger.info(f"   Result: {result}")
        return True
    else:
        logger.error("❌ CREATE workflow failed - no result")
        return False


async def test_review_workflow(client: E2ETestClient):
    """Test REVIEW workflow - review generated code"""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: REVIEW WORKFLOW - Review Generated Code")
    logger.info("="*60)

    task = """
Review the generated Task Manager application code.

Check for:
- Code quality and best practices
- Security issues
- Error handling
- API design
- Frontend UX

Provide a detailed review with suggestions for improvement.
"""

    start_time = time.time()
    responses = await client.send_task(task)
    duration = time.time() - start_time

    logger.info(f"⏱️ REVIEW workflow completed in {duration:.1f}s")
    logger.info(f"📊 Received {len(responses)} responses")

    # Verify result
    result = client.get_workflow_result()

    if result:
        logger.info("✅ REVIEW workflow succeeded!")
        logger.info(f"   Result: {result}")
        return True
    else:
        logger.error("❌ REVIEW workflow failed - no result")
        return False


async def verify_generated_files():
    """Verify that files were actually created"""
    logger.info("\n" + "="*60)
    logger.info("VERIFICATION: Check Generated Files")
    logger.info("="*60)

    expected_files = [
        "backend/main.py",
        "backend/models.py",
        "frontend/index.html",
        "README.md"
    ]

    found_files = []
    missing_files = []

    for file_path in expected_files:
        full_path = TEST_WORKSPACE / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            found_files.append((file_path, size))
            logger.info(f"✅ Found: {file_path} ({size} bytes)")
        else:
            missing_files.append(file_path)
            logger.warning(f"❌ Missing: {file_path}")

    # List all files in workspace
    all_files = list(TEST_WORKSPACE.rglob("*"))
    all_files = [f for f in all_files if f.is_file()]

    logger.info(f"\n📁 Total files in workspace: {len(all_files)}")
    for file in all_files:
        rel_path = file.relative_to(TEST_WORKSPACE)
        logger.info(f"   - {rel_path}")

    success = len(missing_files) == 0

    if success:
        logger.info(f"\n✅ All {len(expected_files)} expected files generated!")
    else:
        logger.warning(f"\n⚠️ {len(missing_files)} files missing: {missing_files}")

    return success


async def main():
    """Main E2E test flow"""
    logger.info("\n" + "="*80)
    logger.info("E2E TEST: CREATE + REVIEW WORKFLOWS")
    logger.info("="*80)

    try:
        # Setup test workspace
        workspace_path = await setup_test_workspace()

        # Create client
        client = E2ETestClient(WS_URL, workspace_path)

        # Connect
        connected = await client.connect()
        if not connected:
            logger.error("❌ Failed to connect to backend")
            return False

        # Test CREATE workflow
        create_success = await test_create_workflow(client)

        if not create_success:
            logger.error("❌ CREATE workflow failed - aborting")
            await client.close()
            return False

        # Verify files were created
        files_ok = await verify_generated_files()

        if not files_ok:
            logger.warning("⚠️ File verification failed")

        # Test REVIEW workflow
        review_success = await test_review_workflow(client)

        # Close connection
        await client.close()

        # Final summary
        logger.info("\n" + "="*80)
        logger.info("E2E TEST SUMMARY")
        logger.info("="*80)
        logger.info(f"✅ CREATE workflow: {'PASSED' if create_success else 'FAILED'}")
        logger.info(f"✅ File generation: {'PASSED' if files_ok else 'FAILED'}")
        logger.info(f"✅ REVIEW workflow: {'PASSED' if review_success else 'FAILED'}")

        overall_success = create_success and files_ok and review_success

        if overall_success:
            logger.info("\n🎉 ALL TESTS PASSED!")
            logger.info(f"📁 Test workspace: {TEST_WORKSPACE}")
            return True
        else:
            logger.error("\n❌ SOME TESTS FAILED")
            logger.info(f"📁 Test workspace: {TEST_WORKSPACE}")
            return False

    except Exception as e:
        logger.error(f"❌ E2E test failed with exception: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
