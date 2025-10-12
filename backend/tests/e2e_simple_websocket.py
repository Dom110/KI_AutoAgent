#!/usr/bin/env python3
"""
Simple E2E Test with WebSocket

Simplified version without type hints that cause issues in Python 3.9
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from datetime import datetime

# Try to import websockets
try:
    import websockets
except ImportError:
    print("ERROR: websockets module not installed")
    print("Install with: pip3 install websockets")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test workspace
TEST_WORKSPACE = Path.home() / "TestApps" / f"e2e_test_{datetime.now():%Y%m%d_%H%M%S}"
WS_URL = "ws://localhost:8002/ws/chat"


async def test_websocket_connection():
    """Test basic WebSocket connection and CREATE workflow"""
    logger.info("=" * 80)
    logger.info("E2E TEST: WebSocket Connection + CREATE Workflow")
    logger.info("=" * 80)

    # Setup workspace
    logger.info(f"📁 Creating test workspace: {TEST_WORKSPACE}")
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    workspace_str = str(TEST_WORKSPACE)

    try:
        # Connect to WebSocket
        logger.info(f"🔌 Connecting to {WS_URL}...")
        websocket = await websockets.connect(WS_URL)
        logger.info("✅ WebSocket connected!")

        # Wait for connected message
        msg = await websocket.recv()
        data = json.loads(msg)
        logger.info(f"📨 Received: {data.get('type')}")

        if data.get("type") == "connected":
            logger.info("✅ Backend sent 'connected' message")

        # Send init message
        init_msg = {
            "type": "init",
            "workspace_path": workspace_str
        }
        logger.info(f"📤 Sending init with workspace: {workspace_str}")
        await websocket.send(json.dumps(init_msg))

        # Wait for initialized
        msg = await websocket.recv()
        data = json.loads(msg)
        logger.info(f"📨 Received: {data}")

        if data.get("type") == "initialized":
            session_id = data.get("session_id")
            logger.info(f"✅ Session initialized: {session_id}")
        else:
            logger.error(f"❌ Expected 'initialized', got: {data.get('type')}")
            await websocket.close()
            return False

        # Send task
        task = """
Create a simple Python script that prints "Hello World".

Create a file called hello.py with:
- A main() function that prints "Hello World"
- An if __name__ == "__main__": block that calls main()

Keep it simple and functional.
"""
        logger.info("📤 Sending CREATE task...")
        task_msg = {
            "type": "message",
            "content": task
        }
        await websocket.send(json.dumps(task_msg))

        # Collect responses
        logger.info("⏳ Waiting for responses (max 5 minutes)...")
        workflow_complete = False
        response_count = 0
        start_time = time.time()

        while not workflow_complete:
            try:
                msg = await asyncio.wait_for(websocket.recv(), timeout=300.0)
                data = json.loads(msg)
                response_count += 1

                msg_type = data.get("type")
                logger.info(f"📨 [{response_count}] Received: {msg_type}")

                if msg_type == "agent_response":
                    content = data.get("content", "")
                    logger.info(f"   Content: {content[:150]}...")

                elif msg_type == "workflow_complete":
                    logger.info("✅ Workflow complete!")
                    final_output = data.get("final_output", {})
                    logger.info(f"   Final output: {final_output}")
                    workflow_complete = True

                elif msg_type == "error":
                    error_msg = data.get("error", "Unknown error")
                    logger.error(f"❌ Error: {error_msg}")
                    workflow_complete = True

                elif msg_type == "status":
                    status = data.get("status", "")
                    logger.info(f"   Status: {status}")

            except asyncio.TimeoutError:
                logger.error("⏱️ Timeout after 5 minutes")
                break
            except Exception as e:
                logger.error(f"❌ Error: {e}")
                break

        duration = time.time() - start_time
        logger.info(f"⏱️ Workflow duration: {duration:.1f}s")
        logger.info(f"📊 Total responses: {response_count}")

        # Close connection
        await websocket.close()
        logger.info("🔌 WebSocket closed")

        # Check for generated files
        logger.info("\n" + "=" * 80)
        logger.info("FILE VERIFICATION")
        logger.info("=" * 80)

        all_files = list(TEST_WORKSPACE.rglob("*"))
        all_files = [f for f in all_files if f.is_file()]

        logger.info(f"📁 Files in workspace: {len(all_files)}")
        for file in all_files:
            rel_path = file.relative_to(TEST_WORKSPACE)
            size = file.stat().st_size
            logger.info(f"   ✅ {rel_path} ({size} bytes)")

        # Check for hello.py
        hello_py = TEST_WORKSPACE / "hello.py"
        if hello_py.exists():
            logger.info("\n✅ hello.py was created!")
            with open(hello_py) as f:
                content = f.read()
            logger.info(f"Content:\n{content[:500]}")
        else:
            logger.warning("\n⚠️ hello.py not found")

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"✅ WebSocket connection: PASSED")
        logger.info(f"✅ Session initialization: PASSED")
        logger.info(f"✅ Task submission: PASSED")
        logger.info(f"✅ Workflow execution: {'PASSED' if workflow_complete else 'FAILED'}")
        logger.info(f"✅ Files generated: {len(all_files)}")
        logger.info(f"📁 Test workspace: {TEST_WORKSPACE}")

        success = workflow_complete and len(all_files) > 0

        if success:
            logger.info("\n🎉 E2E TEST PASSED!")
        else:
            logger.error("\n❌ E2E TEST FAILED")

        return success

    except Exception as e:
        logger.error(f"❌ E2E test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_websocket_connection())
    sys.exit(0 if success else 1)
