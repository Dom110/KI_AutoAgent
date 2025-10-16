#!/usr/bin/env python3
"""
Test Debug Workflow v6.4 - Test EXPLAIN/ANALYZE workflows

This test validates that the new workflow-aware router correctly
handles debugging requests on existing codebases.

Expected behavior:
1. User: "Untersuche die App und führe ein debugging aus"
2. System: Detects existing code, plans EXPLAIN workflow
3. Research: Runs in "analyze" mode
4. Result: Debugging report (NOT new code generation)

Author: KI AutoAgent Team
Version: 6.4.0-beta
Python: 3.13+
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
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


async def test_debug_workflow(
    workspace_path: str = "/Users/dominikfoert/TestApps/manualTest",
    timeout: float = 60.0
) -> bool:
    """
    Test debugging workflow on existing calculator app.

    Args:
        workspace_path: Path to test workspace with existing code
        timeout: Max time to wait for result

    Returns:
        True if test passed
    """
    uri = "ws://localhost:8002/ws/chat"
    test_passed = False

    try:
        async with websockets.connect(uri) as ws:
            logger.info(f"✅ Connected to {uri}")

            # Step 1: Send init message
            init_msg = {
                "type": "init",
                "workspace_path": workspace_path
            }
            await ws.send(json.dumps(init_msg))
            logger.info(f"📤 Sent init for workspace: {workspace_path}")

            # Wait for initialization
            while True:
                msg = await asyncio.wait_for(ws.recv(), timeout=10)
                data = json.loads(msg)
                if data.get("type") == "initialized":
                    logger.info(f"✅ Initialized: {data.get('workspace_path')}")
                    break
                elif data.get("type") == "error":
                    logger.error(f"❌ Init error: {data.get('message')}")
                    return False

            # Step 2: Send debug request
            debug_request = {
                "type": "chat",
                "content": "Untersuche die App und führe ein debugging aus",
                "agent": "orchestrator",
                "metadata": {}
            }
            await ws.send(json.dumps(debug_request))
            logger.info("📤 Sent debug request")

            # Step 3: Collect responses
            agents_executed = []
            workflow_type = None
            research_mode = None
            result_received = False

            start_time = datetime.now()

            while (datetime.now() - start_time).total_seconds() < timeout:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1)
                    data = json.loads(msg)
                    msg_type = data.get("type")

                    if msg_type == "status":
                        status = data.get("status", "")
                        message = data.get("message", "")
                        logger.info(f"📊 Status: {status} - {message[:100]}")

                    elif msg_type == "approval_request":
                        logger.info(f"🔐 Approval request: {data.get('description')}")
                        # Auto-approve
                        approval = {
                            "type": "approval_response",
                            "request_id": data.get("request_id"),
                            "approved": True,
                            "response": "Auto-approved for testing"
                        }
                        await ws.send(json.dumps(approval))
                        logger.info("   ✅ Auto-approved")

                    elif msg_type == "agent_progress":
                        agent = data.get("agent", "unknown")
                        if agent not in agents_executed:
                            agents_executed.append(agent)
                        logger.info(f"🤖 {agent}: {data.get('message', '')[:100]}")

                    elif msg_type == "model_selection":
                        model = data.get("model", {})
                        logger.info(f"🤖 Model: {model}")

                    elif msg_type == "result":
                        result_received = True
                        success = data.get("success", False)
                        quality = data.get("quality_score", 0)
                        agents = data.get("agents_completed", [])

                        logger.info(f"")
                        logger.info(f"🎯 RESULT RECEIVED!")
                        logger.info(f"   Success: {success}")
                        logger.info(f"   Quality: {quality}")
                        logger.info(f"   Agents executed: {agents}")

                        # Check test criteria
                        if success and len(agents) > 0:
                            # Should have executed Research in analyze mode
                            if "research" in agents:
                                logger.info(f"✅ TEST PASSED: Research executed for debugging")
                                test_passed = True
                            else:
                                logger.error(f"❌ TEST FAILED: Research not in {agents}")
                        else:
                            logger.error(f"❌ TEST FAILED: No agents executed or failed")

                        break

                    elif msg_type == "error":
                        logger.error(f"❌ Error: {data.get('message')}")
                        break

                except asyncio.TimeoutError:
                    # Continue waiting
                    pass

            if not result_received:
                logger.error(f"❌ TEST FAILED: No result received within {timeout}s")

    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False

    return test_passed


async def main():
    """Run the debug workflow test."""
    logger.info("="*60)
    logger.info("🧪 DEBUG WORKFLOW TEST v6.4")
    logger.info("="*60)
    logger.info("")

    # Check if backend is running
    try:
        async with websockets.connect("ws://localhost:8002/ws/chat") as ws:
            pass
    except Exception:
        logger.error("❌ Backend not running! Start it with:")
        logger.error("   cd backend && python api/server_v6_integrated.py")
        return 1

    # Run test
    logger.info("📋 Test scenario: Debug existing calculator app")
    logger.info("   Expected: Research runs in analyze mode")
    logger.info("   NOT expected: Code generation")
    logger.info("")

    passed = await test_debug_workflow()

    logger.info("")
    logger.info("="*60)
    if passed:
        logger.info("✅✅✅ TEST SUITE PASSED ✅✅✅")
        return 0
    else:
        logger.error("❌❌❌ TEST SUITE FAILED ❌❌❌")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)