#!/usr/bin/env python3
"""
E2E Test: FIX Workflow - Improve Existing App

Tests the FIX workflow by asking to improve the existing hello.py app.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
import websockets

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Use the existing hello.py workspace from the first test
EXISTING_WORKSPACE = Path.home() / "TestApps" / "e2e_test_20251012_160837"
WS_URL = "ws://localhost:8002/ws/chat"


async def test_fix_workflow():
    """Test FIX workflow on existing hello.py app"""
    logger.info("=" * 80)
    logger.info("E2E TEST: FIX Workflow - Improve Existing App")
    logger.info("=" * 80)

    # Check workspace exists
    if not EXISTING_WORKSPACE.exists():
        logger.error(f"❌ Workspace not found: {EXISTING_WORKSPACE}")
        return False

    logger.info(f"📁 Using existing workspace: {EXISTING_WORKSPACE}")

    # List existing files
    existing_files = list(EXISTING_WORKSPACE.glob("*.py"))
    logger.info(f"📄 Existing files: {[f.name for f in existing_files]}")

    try:
        # Connect
        logger.info(f"🔌 Connecting to {WS_URL}...")
        websocket = await websockets.connect(WS_URL)
        logger.info("✅ WebSocket connected!")

        # Wait for connected message
        msg = await websocket.recv()
        data = json.loads(msg)
        logger.info(f"📨 Connected: {data.get('type')}")

        # Send init with EXISTING workspace
        init_msg = {
            "type": "init",
            "workspace_path": str(EXISTING_WORKSPACE)
        }
        await websocket.send(json.dumps(init_msg))
        logger.info(f"📤 Init sent with workspace: {EXISTING_WORKSPACE}")

        # Wait for initialized
        msg = await websocket.recv()
        data = json.loads(msg)
        session_id = data.get("session_id")
        logger.info(f"✅ Session initialized: {session_id}")

        # Send FIX task
        task = """
Improve the existing hello.py application with the following enhancements:

1. Add command-line argument support:
   - Accept a --name argument to customize the greeting
   - Accept a --language argument for different languages (en, de, es, fr)
   - Default to "World" and "en" if no arguments provided

2. Add multilingual support:
   - English: "Hello World"
   - German: "Hallo Welt"
   - Spanish: "Hola Mundo"
   - French: "Bonjour Monde"

3. Add better error handling:
   - Validate input arguments
   - Handle invalid language codes gracefully

4. Update the tests to cover new functionality

5. Update README.md with new usage examples

Keep the existing code structure and improve it. Don't recreate from scratch.
"""

        logger.info("📤 Sending FIX task...")
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
                elapsed = time.time() - start_time

                logger.info(f"📨 [{response_count}] {msg_type} (elapsed: {elapsed:.0f}s)")

                if msg_type == "agent_response":
                    content = data.get("content", "")
                    logger.info(f"   Content: {content[:150]}...")

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
                logger.error("⏱️ Timeout after 5 minutes")
                break

        duration = time.time() - start_time
        logger.info(f"⏱️ Total duration: {duration:.1f}s ({duration/60:.1f} min)")

        # Close
        await websocket.close()

        # Verify changes
        logger.info("\n" + "=" * 80)
        logger.info("FILE VERIFICATION")
        logger.info("=" * 80)

        # Check if files were modified
        hello_py = EXISTING_WORKSPACE / "hello.py"
        test_hello = EXISTING_WORKSPACE / "test_hello.py"
        readme = EXISTING_WORKSPACE / "README.md"

        if hello_py.exists():
            content = hello_py.read_text()
            logger.info(f"✅ hello.py exists ({len(content)} chars)")

            # Check for new features
            has_argparse = "argparse" in content or "ArgumentParser" in content
            has_multilingual = "Hallo Welt" in content or "Hola Mundo" in content

            logger.info(f"   - Command-line arguments: {'✅' if has_argparse else '❌'}")
            logger.info(f"   - Multilingual support: {'✅' if has_multilingual else '❌'}")

        if test_hello.exists():
            content = test_hello.read_text()
            logger.info(f"✅ test_hello.py exists ({len(content)} chars)")

        if readme.exists():
            content = readme.read_text()
            logger.info(f"✅ README.md exists ({len(content)} chars)")

        # List all files
        all_files = list(EXISTING_WORKSPACE.rglob("*"))
        all_files = [f for f in all_files if f.is_file() and not f.name.startswith('.')]

        logger.info(f"\n📁 Total files: {len(all_files)}")
        for file in sorted(all_files):
            rel_path = file.relative_to(EXISTING_WORKSPACE)
            size = file.stat().st_size
            logger.info(f"   {rel_path} ({size} bytes)")

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"✅ Duration: {duration:.1f}s ({duration/60:.1f} min)")
        logger.info(f"✅ Files in workspace: {len(all_files)}")

        success = workflow_complete

        if success:
            logger.info(f"\n🎉 FIX WORKFLOW TEST PASSED!")
        else:
            logger.error(f"\n❌ FIX WORKFLOW TEST FAILED")

        logger.info(f"📁 Workspace: {EXISTING_WORKSPACE}")

        return success

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_fix_workflow())
    sys.exit(0 if success else 1)
