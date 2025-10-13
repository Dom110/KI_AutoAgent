#!/usr/bin/env python3
"""
E2E Test: Complex Task Manager App (Backend + Frontend)

Tests CREATE workflow with a multi-file, full-stack application.
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TEST_WORKSPACE = Path.home() / "TestApps" / f"task_manager_{datetime.now():%Y%m%d_%H%M%S}"
WS_URL = "ws://localhost:8002/ws/chat"


async def test_complex_task_manager():
    """Test complex Task Manager app generation"""
    logger.info("=" * 80)
    logger.info("E2E TEST: Complex Task Manager App (Backend + Frontend)")
    logger.info("=" * 80)

    # Setup workspace
    logger.info(f"📁 Creating test workspace: {TEST_WORKSPACE}")
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)

    try:
        # Connect
        logger.info(f"🔌 Connecting to {WS_URL}...")
        websocket = await websockets.connect(WS_URL)
        logger.info("✅ WebSocket connected!")

        # Wait for connected message
        msg = await websocket.recv()
        data = json.loads(msg)
        logger.info(f"📨 Connected: {data.get('type')}")

        # Send init
        init_msg = {
            "type": "init",
            "workspace_path": str(TEST_WORKSPACE)
        }
        await websocket.send(json.dumps(init_msg))

        # Wait for initialized
        msg = await websocket.recv()
        data = json.loads(msg)
        session_id = data.get("session_id")
        logger.info(f"✅ Session initialized: {session_id}")

        # Send complex task
        task = """
Create a complete Task Manager web application with the following features:

**Backend (Python FastAPI):**
- REST API with full CRUD operations:
  - GET /tasks - List all tasks (with filtering by status)
  - POST /tasks - Create new task
  - GET /tasks/{id} - Get single task
  - PUT /tasks/{id} - Update task
  - DELETE /tasks/{id} - Delete task
- Task model: id (UUID), title, description, completed (bool), priority (low/medium/high), created_at, updated_at
- In-memory storage with data persistence to JSON file
- CORS middleware for frontend
- Input validation with Pydantic models
- Error handling with proper HTTP status codes
- API documentation with OpenAPI/Swagger

**Frontend (HTML/CSS/JavaScript):**
- Single-page application with modern UI
- Task list with filtering by status (all/active/completed)
- Task creation form with title, description, priority
- Edit task inline or in modal
- Delete task with confirmation
- Mark task as complete/incomplete
- Priority color coding (red=high, yellow=medium, green=low)
- Responsive design (mobile-friendly)
- Loading indicators for API calls
- Error messages for failed operations

**File Structure:**
```
backend/
  main.py          (FastAPI server)
  models.py        (Pydantic models)
  storage.py       (JSON file storage)
  tasks.json       (data file)
frontend/
  index.html       (UI)
  style.css        (styling)
  app.js           (JavaScript logic)
README.md          (setup instructions)
requirements.txt   (Python dependencies)
```

**Requirements:**
- Clean, production-ready code
- Comprehensive error handling
- Type hints in Python
- Comments for complex logic
- Professional UI design
- No external frameworks (vanilla JS, no React/Vue)

Generate all files with complete implementations.
"""

        logger.info("📤 Sending complex Task Manager creation task...")
        task_msg = {
            "type": "message",
            "content": task
        }
        await websocket.send(json.dumps(task_msg))

        # Collect responses
        logger.info("⏳ Waiting for responses (max 10 minutes for complex app)...")
        workflow_complete = False
        response_count = 0
        start_time = time.time()
        last_update = start_time

        while not workflow_complete:
            try:
                msg = await asyncio.wait_for(websocket.recv(), timeout=600.0)
                data = json.loads(msg)
                response_count += 1

                msg_type = data.get("type")
                current_time = time.time()

                # Log every 10 seconds or on important events
                if current_time - last_update > 10 or msg_type in ["workflow_complete", "error", "agent_response"]:
                    elapsed = current_time - start_time
                    logger.info(f"📨 [{response_count}] {msg_type} (elapsed: {elapsed:.0f}s)")
                    last_update = current_time

                if msg_type == "agent_response":
                    content = data.get("content", "")
                    logger.info(f"   Agent: {content[:100]}...")

                elif msg_type == "workflow_complete":
                    logger.info("✅ Workflow complete!")
                    final_output = data.get("final_output", {})
                    logger.info(f"   Final: {final_output}")
                    workflow_complete = True

                elif msg_type == "error":
                    error_msg = data.get("error", "Unknown")
                    logger.error(f"❌ Error: {error_msg}")
                    workflow_complete = True

            except asyncio.TimeoutError:
                logger.error("⏱️ Timeout after 10 minutes")
                break

        duration = time.time() - start_time
        logger.info(f"⏱️ Total duration: {duration:.1f}s ({duration/60:.1f} minutes)")
        logger.info(f"📊 Total responses: {response_count}")

        # Close
        await websocket.close()

        # Verify files
        logger.info("\n" + "=" * 80)
        logger.info("FILE VERIFICATION")
        logger.info("=" * 80)

        expected_files = [
            "backend/main.py",
            "backend/models.py",
            "backend/storage.py",
            "frontend/index.html",
            "frontend/style.css",
            "frontend/app.js",
            "README.md",
            "requirements.txt",
        ]

        found_files = []
        missing_files = []

        for file_path in expected_files:
            full_path = TEST_WORKSPACE / file_path
            if full_path.exists():
                size = full_path.stat().st_size
                found_files.append((file_path, size))
                logger.info(f"✅ {file_path} ({size} bytes)")
            else:
                missing_files.append(file_path)
                logger.warning(f"❌ Missing: {file_path}")

        # List all files
        all_files = list(TEST_WORKSPACE.rglob("*"))
        all_files = [f for f in all_files if f.is_file() and not f.name.startswith('.')]

        logger.info(f"\n📁 Total files generated: {len(all_files)}")
        for file in sorted(all_files):
            rel_path = file.relative_to(TEST_WORKSPACE)
            size = file.stat().st_size
            logger.info(f"   {rel_path} ({size} bytes)")

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"✅ Duration: {duration:.1f}s ({duration/60:.1f} min)")
        logger.info(f"✅ Files generated: {len(all_files)}")
        logger.info(f"✅ Expected files found: {len(found_files)}/{len(expected_files)}")

        if missing_files:
            logger.warning(f"⚠️  Missing files: {missing_files}")

        success = workflow_complete and len(missing_files) == 0

        if success:
            logger.info(f"\n🎉 COMPLEX APP TEST PASSED!")
        else:
            logger.error(f"\n❌ COMPLEX APP TEST FAILED")

        logger.info(f"📁 Test workspace: {TEST_WORKSPACE}")

        return success

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_complex_task_manager())
    sys.exit(0 if success else 1)
