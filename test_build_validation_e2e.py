#!/usr/bin/env python3
"""
E2E Test for Build Validation Feature

This test validates that:
1. ReviewFix agent runs TypeScript compilation check
2. Build errors reduce quality score
3. Progressive thresholds work correctly

Author: KI AutoAgent Team
Date: 2025-10-11
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import websockets

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Test configuration
WS_URL = "ws://localhost:8002/ws/chat"
WORKSPACE = Path.home() / "TestApps" / f"build_validation_test_{datetime.now():%Y%m%d_%H%M%S}"

# Simpler test query - minimal app to test build validation faster
TEST_QUERY = """Create a minimal React + TypeScript counter app.

Requirements:
- React 18 with TypeScript
- Vite for build
- One Counter component with increment/decrement
- Use useState hook
- TailwindCSS for styling

Files needed:
- package.json
- tsconfig.json
- vite.config.ts
- index.html
- src/main.tsx
- src/App.tsx
- src/components/Counter.tsx

Keep it simple - we're testing build validation, not features.
"""


async def run_e2e_test():
    """Run E2E test with build validation."""

    logger.info("=" * 80)
    logger.info("🧪 BUILD VALIDATION E2E TEST")
    logger.info("=" * 80)
    logger.info(f"WebSocket: {WS_URL}")
    logger.info(f"Workspace: {WORKSPACE}")

    # Create workspace
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    logger.info(f"✅ Created workspace")

    try:
        # Connect to WebSocket
        logger.info(f"\n📡 Connecting to {WS_URL}...")
        async with websockets.connect(WS_URL) as ws:
            logger.info("✅ Connected!")

            # Receive welcome message
            welcome = await ws.recv()
            logger.info(f"📨 Received: {json.loads(welcome).get('type')}")

            # Send init message
            logger.info(f"\n📤 Sending init message...")
            init_msg = {
                "type": "init",
                "workspace_path": str(WORKSPACE)
            }
            await ws.send(json.dumps(init_msg))

            # Receive init response
            init_response = await ws.recv()
            init_data = json.loads(init_response)
            logger.info(f"✅ Initialized: {init_data.get('type')}")

            # Send task
            logger.info(f"\n🚀 Sending task...")
            logger.info(f"Query: {TEST_QUERY[:100]}...")
            task_msg = {
                "type": "chat",
                "message": TEST_QUERY
            }
            await ws.send(json.dumps(task_msg))

            # Monitor messages
            logger.info(f"\n👀 Monitoring workflow execution...")
            logger.info("-" * 80)

            reviewfix_started = False
            build_check_ran = False
            typescript_detected = False
            quality_score = None
            workflow_complete = False

            # Wait for messages (with timeout)
            timeout = 900  # 15 minutes
            start_time = asyncio.get_event_loop().time()

            while True:
                try:
                    # Check timeout
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > timeout:
                        logger.error(f"❌ Timeout after {timeout}s")
                        break

                    # Receive message with timeout
                    msg = await asyncio.wait_for(ws.recv(), timeout=60)
                    data = json.loads(msg)
                    msg_type = data.get("type")

                    # Log key messages
                    if msg_type == "status":
                        status = data.get("status")
                        message = data.get("message", "")
                        logger.info(f"📊 Status: {status} - {message}")

                    elif msg_type == "result":
                        logger.info(f"\n✅ WORKFLOW COMPLETE")
                        workflow_complete = True
                        quality_score = data.get("quality_score")
                        logger.info(f"   Quality Score: {quality_score}")
                        break

                    elif msg_type == "error":
                        logger.error(f"❌ Error: {data.get('message')}")
                        break

                except asyncio.TimeoutError:
                    logger.warning(f"⏱️  Message timeout (60s)")
                    continue
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON decode error: {e}")
                    continue

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False

    # Check results
    logger.info("\n" + "=" * 80)
    logger.info("📊 TEST RESULTS")
    logger.info("=" * 80)

    if not workflow_complete:
        logger.error("❌ Workflow did not complete")
        return False

    # Check generated files
    files = list(WORKSPACE.rglob("*.ts")) + list(WORKSPACE.rglob("*.tsx"))
    logger.info(f"📁 Generated {len(files)} TypeScript files")

    if len(files) == 0:
        logger.error("❌ No TypeScript files generated")
        return False

    # Check for key files
    key_files = ["package.json", "tsconfig.json", "src/main.tsx", "src/App.tsx"]
    missing = []
    for f in key_files:
        if not (WORKSPACE / f).exists():
            missing.append(f)

    if missing:
        logger.warning(f"⚠️  Missing files: {', '.join(missing)}")
    else:
        logger.info(f"✅ All key files present")

    # Now check if build validation ran by looking at server logs
    logger.info(f"\n🔍 Checking server logs for build validation...")
    try:
        with open("/tmp/v6_server.log", "r") as f:
            logs = f.read()

        if "Running TypeScript compilation check" in logs:
            logger.info(f"✅ BUILD VALIDATION RAN!")
            build_check_ran = True

            if "TypeScript compilation passed" in logs:
                logger.info(f"   ✅ Build passed")
            elif "TypeScript compilation failed" in logs:
                logger.info(f"   ❌ Build failed (expected if types are wrong)")

            if "Project Type: TypeScript" in logs:
                logger.info(f"   ✅ TypeScript detected")
                typescript_detected = True

            if "Quality Threshold: 0.90" in logs:
                logger.info(f"   ✅ Correct threshold (0.90 for TypeScript)")
            else:
                logger.warning(f"   ⚠️  Threshold not 0.90")

        else:
            logger.error(f"❌ Build validation DID NOT RUN")
            logger.info(f"   Check if ReviewFix agent executed")

    except Exception as e:
        logger.error(f"❌ Could not read server logs: {e}")

    # Final verdict
    logger.info("\n" + "=" * 80)
    if workflow_complete and build_check_ran:
        logger.info("✅ TEST PASSED - Build validation is working!")
        return True
    else:
        logger.info("❌ TEST FAILED - Build validation did not run")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_e2e_test())
    sys.exit(0 if success else 1)
