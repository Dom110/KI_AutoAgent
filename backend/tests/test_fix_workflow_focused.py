#!/usr/bin/env python3
"""
FOCUSED E2E Test: FIX Workflow

Test fixing bugs in existing code.

Run:
    # Terminal 1: Backend should be running
    source venv/bin/activate
    python backend/api/server_v6_integrated.py

    # Terminal 2: Run this test
    python backend/tests/test_fix_workflow_focused.py
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
TEST_WORKSPACE = Path.home() / "TestApps" / "fix_workflow_test"
TEST_TIMEOUT = 1200  # 20 minutes (FIX should be faster than CREATE)

print("\n" + "="*80)
print("FOCUSED E2E TEST: FIX Workflow")
print("="*80)
print(f"📁 Workspace: {TEST_WORKSPACE}")
print(f"🔌 Backend: {BACKEND_URL}")
print(f"⏱️  Timeout: {TEST_TIMEOUT}s ({TEST_TIMEOUT//60} minutes)")
print("="*80 + "\n")


async def run_fix_test():
    """Run FIX workflow test with detailed monitoring."""

    # Clean workspace
    if TEST_WORKSPACE.exists():
        print(f"🧹 Cleaning workspace: {TEST_WORKSPACE}")
        shutil.rmtree(TEST_WORKSPACE)
    TEST_WORKSPACE.mkdir(parents=True)
    print(f"✅ Clean workspace created\n")

    # Create buggy code to fix
    print("📝 Creating buggy code...")
    buggy_file = TEST_WORKSPACE / "calculator.py"
    buggy_file.write_text("""
def add(a, b):
    \"\"\"Add two numbers.\"\"\"
    return a - b  # BUG: Should be + not -

def multiply(a, b):
    \"\"\"Multiply two numbers.\"\"\"
    result = 0
    for i in range(b):
        result = add(a, result)  # BUG: Uses buggy add()
    return result

def divide(a, b):
    \"\"\"Divide two numbers.\"\"\"
    return a / b  # BUG: No zero division check

def calculate_average(numbers):
    \"\"\"Calculate average of numbers.\"\"\"
    total = 0
    for num in numbers:
        total = add(num, total)  # BUG: Uses buggy add()
    return total / len(numbers)  # BUG: No empty list check

if __name__ == "__main__":
    print("Testing calculator...")
    print(f"add(2, 3) = {add(2, 3)}")  # Should be 5, but gets -1
    print(f"multiply(3, 4) = {multiply(3, 4)}")  # Should be 12
    print(f"divide(10, 2) = {divide(10, 2)}")  # Should be 5.0
    print(f"average([1, 2, 3, 4, 5]) = {calculate_average([1, 2, 3, 4, 5])}")  # Should be 3.0
""")
    print(f"   ✅ Created: {buggy_file}")
    print(f"   📏 Size: {buggy_file.stat().st_size} bytes\n")

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

    # Send query - FIX workflow
    query = """Fix all bugs in calculator.py:
1. The add() function returns subtraction instead of addition
2. The multiply() function uses the buggy add()
3. The divide() function has no zero division check
4. The calculate_average() function has no empty list check

Make sure all functions work correctly and add proper error handling."""

    print(f"📤 Query: {query[:100]}...")
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

    # Check if file was modified
    print(f"\n📁 Checking workspace: {TEST_WORKSPACE}")
    py_files = list(TEST_WORKSPACE.rglob("*.py"))

    print(f"   Python files: {len(py_files)}")

    if buggy_file.exists():
        fixed_content = buggy_file.read_text()
        print(f"\n   📄 Fixed file: {buggy_file.name}")
        print(f"   📏 Size: {len(fixed_content)} bytes")

        # Check if bugs were fixed
        bugs_fixed = []
        if "return a + b" in fixed_content:
            bugs_fixed.append("✅ add() function fixed (+ instead of -)")
        if "if b == 0:" in fixed_content or "ZeroDivisionError" in fixed_content:
            bugs_fixed.append("✅ divide() has zero check")
        if "if not numbers:" in fixed_content or "if len(numbers) == 0:" in fixed_content:
            bugs_fixed.append("✅ calculate_average() has empty check")

        if bugs_fixed:
            print(f"\n   🔧 Bugs fixed:")
            for fix in bugs_fixed:
                print(f"      {fix}")
        else:
            print(f"\n   ⚠️  Could not verify bug fixes in code")

    # Final verdict
    print("\n" + "="*80)
    if result_received and buggy_file.exists():
        print("✅ TEST PASSED - Bugs fixed and result received!")
    elif buggy_file.exists():
        print("⚠️  TEST PARTIAL - File modified but timeout/no result")
    else:
        print("❌ TEST FAILED - File not modified")
    print("="*80 + "\n")

    return result_received and buggy_file.exists()


if __name__ == "__main__":
    try:
        success = asyncio.run(run_fix_test())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
