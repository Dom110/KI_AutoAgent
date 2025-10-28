#!/usr/bin/env python
"""
Test 2: Extend existing calculator app

Tests adding new functionality (multiply/divide) to existing calculator.
"""

import asyncio
import json
import sys
from pathlib import Path
import websockets
import time

# Test configuration
BACKEND_WS_URL = "ws://localhost:8002/ws/chat"
TEST_WORKSPACE = Path.home() / "TestApps" / "ai_factory_test"
TEST_TIMEOUT = 300  # 5 minutes

# Extension task
EXTEND_TASK = """Extend the calculator module with two new functions:
- multiply(a, b): Multiply two numbers
- divide(a, b): Divide two numbers (with zero division check)

Keep the same code quality standards:
- Type hints
- Comprehensive docstrings
- Error handling
- Add tests for the new functions"""


async def run_extend_test():
    """Run calculator extension test."""
    print("="*60)
    print("🧪 Test 2: Extend Calculator App")
    print("="*60)
    print(f"Backend: {BACKEND_WS_URL}")
    print(f"Workspace: {TEST_WORKSPACE}")
    print("="*60)

    if not TEST_WORKSPACE.exists():
        print("❌ Workspace doesn't exist! Run Test 1 first.")
        return 1

    print(f"✅ Workspace exists: {TEST_WORKSPACE}")

    # Connect to backend
    print(f"\n🔌 Connecting to {BACKEND_WS_URL}...")

    try:
        ws = await websockets.connect(BACKEND_WS_URL, ping_interval=30)
        print("✅ Connected")

        # Send init message
        init_msg = {
            "type": "init",
            "workspace_path": str(TEST_WORKSPACE)
        }
        await ws.send(json.dumps(init_msg))
        print(f"📤 Sent init with workspace: {TEST_WORKSPACE}")

        # Wait for init confirmation
        response = await ws.recv()
        data = json.loads(response)
        if data.get("type") == "init_complete":
            print("✅ Initialization confirmed")
        elif data.get("type") == "connected":
            print("✅ Connected (legacy response)")

        # Send extension task
        print("\n" + "="*60)
        print("📋 SENDING EXTENSION TASK")
        print("="*60)
        print(f"Task: {EXTEND_TASK[:100]}...")

        task_msg = {
            "type": "task",
            "task": EXTEND_TASK
        }
        await ws.send(json.dumps(task_msg))
        print("✅ Task sent")

        # Receive messages
        print("\n" + "="*60)
        print("📥 RECEIVING WORKFLOW MESSAGES")
        print("="*60)

        start_time = time.time()
        message_count = 0
        completed = False
        agents_executed = []
        files_generated = []
        errors = []

        while True:
            elapsed = time.time() - start_time
            if elapsed > TEST_TIMEOUT:
                print(f"\n⏱️ Timeout after {TEST_TIMEOUT}s")
                errors.append(f"Timeout after {TEST_TIMEOUT}s")
                break

            try:
                message = await asyncio.wait_for(ws.recv(), timeout=30.0)
            except asyncio.TimeoutError:
                print("⏱️ 30s receive timeout - checking if workflow complete...")
                continue

            message_count += 1
            data = json.loads(message)
            msg_type = data.get("type")

            if message_count % 5 == 0:
                print(f"\n[{message_count} messages | {elapsed:.1f}s elapsed]")

            if msg_type == "supervisor_decision":
                agent = data.get("agent", "unknown")
                print(f"\n🎯 SUPERVISOR → {agent.upper()}")

            elif msg_type == "agent_start":
                agent = data.get("agent", "unknown")
                print(f"🚀 {agent.upper()} STARTED")
                agents_executed.append(agent)

            elif msg_type == "agent_complete":
                agent = data.get("agent", "unknown")
                print(f"✅ {agent.upper()} COMPLETED")

            elif msg_type == "file_generated":
                file_path = data.get("file", "unknown")
                print(f"   📄 File: {file_path}")
                files_generated.append(file_path)

            elif msg_type == "code_generated":
                files = data.get("files", [])
                print(f"   ✅ Code: {len(files)} files")
                files_generated.extend(files)

            elif msg_type == "workflow_complete":
                print("\n✅ WORKFLOW COMPLETE")
                completed = True
                break

            elif msg_type == "error":
                error = data.get("error", "Unknown")
                print(f"\n❌ ERROR: {error}")
                errors.append(error)
                break

        await ws.close()
        print("\n🔌 Connection closed")

        # Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"Status: {'✅ COMPLETED' if completed else '❌ INCOMPLETE'}")
        print(f"Time: {elapsed:.2f}s")
        print(f"Messages: {message_count}")
        print(f"\nAgents: {len(agents_executed)}")
        for agent in agents_executed:
            print(f"  - {agent}")
        print(f"\nFiles: {len(files_generated)}")
        for file in files_generated:
            print(f"  - {file}")
        print(f"\nErrors: {len(errors)}")
        for error in errors:
            print(f"  - {error}")

        # Validation
        print("\n" + "="*60)
        print("🎯 VALIDATION RESULTS")
        print("="*60)

        failures = []

        if not completed:
            failures.append("❌ Workflow incomplete")

        if "codesmith" not in agents_executed:
            failures.append("❌ Codesmith not executed")

        if len(errors) > 0:
            failures.append(f"❌ {len(errors)} errors occurred")

        if len(failures) == 0:
            print("✅ ALL CHECKS PASSED")
            print("\nExtension successful!")
            return 0
        else:
            print("❌ VALIDATION FAILED")
            for failure in failures:
                print(f"  {failure}")
            return 1

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    try:
        exit_code = asyncio.run(run_extend_test())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted")
        sys.exit(130)


if __name__ == "__main__":
    main()
