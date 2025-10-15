#!/usr/bin/env python3
"""
E2E Tests for v6.3 Features - WebSocket Client (CORRECT ARCHITECTURE)

Tests v6.3 features by connecting to backend via WebSocket.
This follows the E2E_TESTING_GUIDE.md best practices.

Tests:
1. CREATE workflow with full orchestration
2. Agent Autonomy (Codesmith invokes Research + Architect)
3. Model Selection (complexity-based)

⚠️  CRITICAL:
- Backend must be running: python backend/api/server_v6_integrated.py
- Test workspace: ~/TestApps/e2e_v6.3_test (ISOLATED from dev repo!)
- NO direct imports from backend!
- Connection via WebSocket only!

Run:
    # Terminal 1: Start backend
    cd /Users/dominikfoert/git/KI_AutoAgent
    source venv/bin/activate
    python backend/api/server_v6_integrated.py

    # Terminal 2: Run tests
    python backend/tests/e2e_test_v6_3_websocket.py
"""

import asyncio
import json
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path

import websockets

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Test configuration
BACKEND_URL = "ws://localhost:8002/ws/chat"
TEST_WORKSPACE = Path.home() / "TestApps" / "e2e_v6.3_test"
TEST_TIMEOUT = 900  # 15 minutes per test


class WebSocketTestClient:
    """WebSocket client for E2E testing."""

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.websocket = None
        self.session_id = None
        self.messages = []

    async def connect(self):
        """Connect to backend and initialize session."""
        logger.info(f"🔌 Connecting to {BACKEND_URL}")
        self.websocket = await websockets.connect(BACKEND_URL)
        logger.info("✅ Connected!")

        # Send init message
        init_msg = {
            "type": "init",
            "workspace_path": str(self.workspace_path)
        }
        await self.websocket.send(json.dumps(init_msg))
        logger.info(f"📤 Sent init: workspace={self.workspace_path}")

        # Wait for "connected" message
        response1 = await asyncio.wait_for(self.websocket.recv(), timeout=10)
        data1 = json.loads(response1)
        logger.debug(f"📥 Welcome: {data1.get('type')}")

        # Wait for "initialized" message
        response2 = await asyncio.wait_for(self.websocket.recv(), timeout=60)
        data2 = json.loads(response2)

        if data2.get("type") != "initialized":
            raise RuntimeError(f"Expected 'initialized', got: {data2.get('type')}")

        self.session_id = data2.get("session_id")
        logger.info(f"✅ Session initialized: {self.session_id}")

    async def send_query(self, query: str) -> dict:
        """Send query and wait for result."""
        logger.info(f"📤 Query: {query}")

        # Send chat message
        msg = {
            "type": "chat",
            "content": query
        }
        await self.websocket.send(json.dumps(msg))

        # Collect responses until "result" or "error"
        start = asyncio.get_event_loop().time()
        response_count = 0

        while asyncio.get_event_loop().time() - start < TEST_TIMEOUT:
            try:
                response = await asyncio.wait_for(self.websocket.recv(), timeout=5)
                data = json.loads(response)
                response_count += 1
                self.messages.append(data)

                msg_type = data.get("type")
                logger.debug(f"📥 [{response_count}] {msg_type}")

                # Handle different message types
                if msg_type == "status":
                    status_msg = data.get('message', data.get('content', ''))
                    logger.info(f"   Status: {status_msg[:100]}")

                elif msg_type == "approval_request":
                    logger.info(f"   Approval: {data.get('content', '')[:80]}")
                    # Auto-approve
                    approval = {
                        "type": "approval_response",
                        "approved": True
                    }
                    await self.websocket.send(json.dumps(approval))
                    logger.info("   ✅ Auto-approved")

                elif msg_type == "result":
                    logger.info(f"   ✅ RESULT received!")
                    logger.info(f"   Success: {data.get('success')}")
                    logger.info(f"   Quality: {data.get('quality_score', 'N/A')}")
                    return data

                elif msg_type == "error":
                    logger.error(f"   ❌ ERROR: {data.get('message')}")
                    return data

            except asyncio.TimeoutError:
                elapsed = int(asyncio.get_event_loop().time() - start)
                logger.debug(f"   ⏱️  Waiting... ({elapsed}s, {response_count} msgs)")
                continue

        logger.error(f"❌ Timeout after {TEST_TIMEOUT}s ({response_count} messages)")
        return {"type": "error", "message": "Test timeout"}

    async def disconnect(self):
        """Close WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
            logger.info("🔌 Disconnected")


async def test_create_workflow():
    """
    Test 1: CREATE workflow with full agent orchestration.

    Expected:
    - Workflow Planner generates: Research → Architect → Codesmith → ReviewFix
    - Agent Autonomy: If any agent skipped, Codesmith auto-invokes
    - Model Selection: Codesmith selects appropriate model
    - Result: Code generated + architecture.md created
    """
    logger.info("=" * 80)
    logger.info("TEST 1: CREATE Workflow with Agent Autonomy")
    logger.info("=" * 80)

    try:
        # Setup clean workspace
        workspace = TEST_WORKSPACE / "test1_create"
        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True)
        logger.info(f"📁 Workspace: {workspace}")

        # Connect and run test
        client = WebSocketTestClient(workspace)
        await client.connect()

        # Send CREATE query
        result = await client.send_query(
            "Create a simple TODO app with Python FastAPI. "
            "Include basic CRUD operations and data persistence."
        )

        await client.disconnect()

        # Verify results
        success = result.get("success", False)
        logger.info("")
        logger.info("=" * 80)
        logger.info("TEST 1 RESULTS:")
        logger.info("=" * 80)
        logger.info(f"✅ Success: {success}")

        # Check for generated files
        files = list(workspace.rglob("*.py"))
        logger.info(f"📄 Generated Python files: {len(files)}")
        for f in files[:5]:  # Show first 5
            logger.info(f"   - {f.relative_to(workspace)}")

        # Check for architecture snapshot
        arch_dir = workspace / ".ki_autoagent" / "architecture"
        if arch_dir.exists():
            arch_files = list(arch_dir.glob("*"))
            logger.info(f"📐 Architecture files: {len(arch_files)}")

        return {
            "test": "CREATE Workflow",
            "success": success,
            "files_generated": len(files),
            "architecture_created": arch_dir.exists() if arch_dir else False,
            "messages_received": len(client.messages)
        }

    except Exception as e:
        logger.error(f"❌ TEST 1 FAILED: {e}", exc_info=True)
        return {"test": "CREATE Workflow", "success": False, "error": str(e)}


async def test_agent_autonomy():
    """
    Test 2: Agent Autonomy - Codesmith invokes missing agents.

    Expected:
    - Direct query to implement feature (skip Research + Architect)
    - Codesmith detects missing context
    - Codesmith → Research (autonomous invocation)
    - Codesmith → Architect (autonomous invocation)
    - Codesmith generates code with full context
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("TEST 2: Agent Autonomy (Codesmith invokes Research + Architect)")
    logger.info("=" * 80)

    try:
        # Setup clean workspace
        workspace = TEST_WORKSPACE / "test2_autonomy"
        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True)
        logger.info(f"📁 Workspace: {workspace}")

        # Connect and run test
        client = WebSocketTestClient(workspace)
        await client.connect()

        # Send direct CODE query (skips Research + Architect)
        # This should trigger agent autonomy
        result = await client.send_query(
            "CODE: Implement user authentication with JWT tokens for the TODO app. "
            "Use bcrypt for password hashing."
        )

        await client.disconnect()

        # Verify results
        success = result.get("success", False)
        logger.info("")
        logger.info("=" * 80)
        logger.info("TEST 2 RESULTS:")
        logger.info("=" * 80)
        logger.info(f"✅ Success: {success}")

        # Check if Research was invoked (look for research context in messages)
        research_invoked = any(
            "research" in msg.get("content", "").lower()
            for msg in client.messages
            if msg.get("type") == "status"
        )
        logger.info(f"🔍 Research invoked: {research_invoked}")

        # Check if Architect was invoked
        architect_invoked = any(
            "architect" in msg.get("content", "").lower()
            for msg in client.messages
            if msg.get("type") == "status"
        )
        logger.info(f"🏗️  Architect invoked: {architect_invoked}")

        # Check for generated files
        files = list(workspace.rglob("*.py"))
        logger.info(f"📄 Generated files: {len(files)}")

        return {
            "test": "Agent Autonomy",
            "success": success,
            "research_invoked": research_invoked,
            "architect_invoked": architect_invoked,
            "files_generated": len(files),
            "messages_received": len(client.messages)
        }

    except Exception as e:
        logger.error(f"❌ TEST 2 FAILED: {e}", exc_info=True)
        return {"test": "Agent Autonomy", "success": False, "error": str(e)}


async def test_model_selection():
    """
    Test 3: Model Selection based on complexity.

    This test verifies model selection notifications via WebSocket.
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("TEST 3: Model Selection (WebSocket Notifications)")
    logger.info("=" * 80)

    try:
        # Setup clean workspace
        workspace = TEST_WORKSPACE / "test3_model"
        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True)
        logger.info(f"📁 Workspace: {workspace}")

        # Connect and run test
        client = WebSocketTestClient(workspace)
        await client.connect()

        # Send complex query to trigger model selection
        result = await client.send_query(
            "Create a microservices platform with Kubernetes orchestration, "
            "Kafka message queue, Redis caching, PostgreSQL database, "
            "OAuth2 authentication, and API gateway with rate limiting."
        )

        await client.disconnect()

        # Check for model selection notifications
        model_notifications = [
            msg for msg in client.messages
            if msg.get("type") == "model_selection"
        ]

        logger.info("")
        logger.info("=" * 80)
        logger.info("TEST 3 RESULTS:")
        logger.info("=" * 80)
        logger.info(f"📊 Model selection notifications: {len(model_notifications)}")

        for notif in model_notifications:
            model = notif.get("model", {})
            logger.info(f"   Model: {model.get('name')}")
            logger.info(f"   Think mode: {model.get('think_mode')}")
            logger.info(f"   Reason: {notif.get('reason', '')[:80]}")

        success = len(model_notifications) > 0 and result.get("success", False)

        return {
            "test": "Model Selection",
            "success": success,
            "model_notifications": len(model_notifications),
            "messages_received": len(client.messages)
        }

    except Exception as e:
        logger.error(f"❌ TEST 3 FAILED: {e}", exc_info=True)
        return {"test": "Model Selection", "success": False, "error": str(e)}


async def run_all_tests():
    """Run all E2E tests."""
    logger.info("")
    logger.info("🚀 Starting E2E Tests for v6.3 (WebSocket Client)")
    logger.info(f"📁 Test Workspace: {TEST_WORKSPACE}")
    logger.info(f"🔌 Backend URL: {BACKEND_URL}")
    logger.info(f"🕐 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    # Clean test workspace
    if TEST_WORKSPACE.exists():
        logger.info(f"🧹 Cleaning old workspace: {TEST_WORKSPACE}")
        shutil.rmtree(TEST_WORKSPACE)
    TEST_WORKSPACE.mkdir(parents=True)

    results = []

    # Test 1: CREATE Workflow
    result1 = await test_create_workflow()
    results.append(result1)

    # Test 2: Agent Autonomy
    result2 = await test_agent_autonomy()
    results.append(result2)

    # Test 3: Model Selection
    result3 = await test_model_selection()
    results.append(result3)

    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("E2E TEST SUMMARY (WebSocket Client)")
    logger.info("=" * 80)

    passed = sum(1 for r in results if r.get("success"))
    total = len(results)

    for result in results:
        status = "✅ PASS" if result.get("success") else "❌ FAIL"
        logger.info(f"{status} - {result['test']}")
        if not result.get("success") and "error" in result:
            logger.info(f"       Error: {result['error']}")

    logger.info("")
    logger.info(f"📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    logger.info(f"🕐 End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return results


if __name__ == "__main__":
    print("\n" + "="*80)
    print("KI AutoAgent v6.3 - E2E Tests (WebSocket Client)")
    print("="*80 + "\n")

    try:
        results = asyncio.run(run_all_tests())

        # Exit code
        all_passed = all(r.get("success") for r in results)
        sys.exit(0 if all_passed else 1)

    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Tests crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
