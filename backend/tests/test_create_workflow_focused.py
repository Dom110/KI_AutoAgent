#!/usr/bin/env python3
"""
FOCUSED E2E Test: CREATE Workflow Only

Single test for CREATE workflow with EXTENDED timeout.
Stays with test until completion.

Run:
    # Terminal 1: Start backend
    source venv/bin/activate
    python backend/api/server_v6_integrated.py

    # Terminal 2: Run this test
    python backend/tests/test_create_workflow_focused.py
"""

import asyncio
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

import websockets

# Configuration
BACKEND_URL = "ws://localhost:8002/ws/chat"
TEST_WORKSPACE = Path.home() / "TestApps" / "create_workflow_test"
TEST_TIMEOUT = 1800  # 30 minutes (was 15min before - too short!)

print("\n" + "="*80)
print("FOCUSED E2E TEST: CREATE Workflow")
print("="*80)
print(f"📁 Workspace: {TEST_WORKSPACE}")
print(f"🔌 Backend: {BACKEND_URL}")
print(f"⏱️  Timeout: {TEST_TIMEOUT}s ({TEST_TIMEOUT//60} minutes)")
print("="*80 + "\n")


async def run_create_test():
    """Run CREATE workflow test with detailed monitoring."""

    # Clean workspace
    if TEST_WORKSPACE.exists():
        print(f"🧹 Cleaning workspace: {TEST_WORKSPACE}")
        shutil.rmtree(TEST_WORKSPACE)
    TEST_WORKSPACE.mkdir(parents=True)
    print(f"✅ Clean workspace created\n")

    # Connect
    print(f"🔌 Connecting to {BACKEND_URL}...")
    ws = await websockets.connect(BACKEND_URL)
    print("✅ Connected!\n")

    # Initialize session
    print("📤 Sending init message...")
    init_msg = {"type": "init", "workspace_path": str(TEST_WORKSPACE)}
    await ws.send(json.dumps(init_msg))

    # Wait for connected
    resp1 = await asyncio.wait_for(ws.recv(), timeout=10)
    data1 = json.loads(resp1)
    print(f"📥 {data1.get('type')}: {data1.get('message', '')[:50]}")

    # Wait for initialized
    resp2 = await asyncio.wait_for(ws.recv(), timeout=60)
    data2 = json.loads(resp2)
    session_id = data2.get("session_id")
    print(f"✅ Session initialized: {session_id}\n")

    # Send query
    query = "Create a simple TODO app with Python FastAPI. Include basic CRUD operations and data persistence."
    print(f"📤 Query: {query}")
    print(f"🕐 Start: {datetime.now().strftime('%H:%M:%S')}\n")

    chat_msg = {"type": "chat", "content": query}
    await ws.send(json.dumps(chat_msg))

    # Monitor responses
    start = asyncio.get_event_loop().time()
    message_count = 0
    status_messages = []
    approval_count = 0
    result_received = False

    print("="*80)
    print("MONITORING WORKFLOW EXECUTION")
    print("="*80 + "\n")

    while asyncio.get_event_loop().time() - start < TEST_TIMEOUT:
        try:
            response = await asyncio.wait_for(ws.recv(), timeout=10)
            data = json.loads(response)
            message_count += 1

            msg_type = data.get("type")
            elapsed = int(asyncio.get_event_loop().time() - start)
            timestamp = f"[{elapsed:4d}s]"

            if msg_type == "status":
                msg = data.get('message', data.get('content', ''))
                status_messages.append(msg)
                print(f"{timestamp} 📊 {msg[:100]}")

            elif msg_type == "approval_request":
                approval_count += 1
                content = data.get('content', '')[:80]
                print(f"{timestamp} 🔐 Approval #{approval_count}: {content}")
                # Auto-approve
                approval_resp = {"type": "approval_response", "approved": True}
                await ws.send(json.dumps(approval_resp))
                print(f"{timestamp}    ✅ Auto-approved")

            elif msg_type == "model_selection":
                model = data.get('model', {})
                if isinstance(model, dict):
                    print(f"{timestamp} 🤖 Model: {model.get('name')} (think={model.get('think_mode')})")
                else:
                    print(f"{timestamp} 🤖 Model: {model}")

            elif msg_type == "result":
                result_received = True
                success = data.get('success')
                quality = data.get('quality_score', 'N/A')
                print(f"\n{timestamp} 🎯 RESULT RECEIVED!")
                print(f"{timestamp}    Success: {success}")
                print(f"{timestamp}    Quality: {quality}")
                break

            elif msg_type == "error":
                error_msg = data.get('message', '')
                print(f"\n{timestamp} ❌ ERROR: {error_msg}")
                break

        except asyncio.TimeoutError:
            elapsed = int(asyncio.get_event_loop().time() - start)
            if elapsed % 60 == 0:  # Every minute
                print(f"[{elapsed:4d}s] ⏳ Waiting... ({message_count} messages so far)")
            continue

    await ws.close()

    # Analysis
    elapsed_total = int(asyncio.get_event_loop().time() - start)
    print("\n" + "="*80)
    print("TEST RESULTS")
    print("="*80)
    print(f"⏱️  Duration: {elapsed_total}s ({elapsed_total//60}min {elapsed_total%60}s)")
    print(f"📨 Messages received: {message_count}")
    print(f"🔐 Approvals: {approval_count}")
    print(f"✅ Result received: {result_received}")

    # Check generated files
    print(f"\n📁 Checking workspace: {TEST_WORKSPACE}")
    py_files = list(TEST_WORKSPACE.rglob("*.py"))
    all_files = list(TEST_WORKSPACE.rglob("*"))
    all_files = [f for f in all_files if f.is_file()]

    print(f"   Python files: {len(py_files)}")
    print(f"   Total files: {len(all_files)}")

    if py_files:
        print(f"\n   📄 Sample files:")
        for f in sorted(py_files)[:10]:
            rel_path = f.relative_to(TEST_WORKSPACE)
            size = f.stat().st_size
            print(f"      - {rel_path} ({size} bytes)")

    # Check architecture
    arch_dir = TEST_WORKSPACE / ".ki_autoagent" / "architecture"
    if arch_dir.exists():
        arch_files = list(arch_dir.glob("*"))
        print(f"\n   📐 Architecture files: {len(arch_files)}")
        for f in arch_files:
            print(f"      - {f.name}")

    # Final verdict
    print("\n" + "="*80)
    if result_received and len(py_files) > 0:
        print("✅ TEST PASSED - Code generated and result received!")
    elif len(py_files) > 0:
        print("⚠️  TEST PARTIAL - Code generated but timeout/no result")
    else:
        print("❌ TEST FAILED - No code generated")
    print("="*80 + "\n")

    return result_received and len(py_files) > 0


if __name__ == "__main__":
    try:
        success = asyncio.run(run_create_test())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
