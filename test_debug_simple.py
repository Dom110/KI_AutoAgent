#!/usr/bin/env python
"""
Simple debug test to understand what's happening in the server.
Tests with a very simple task and maximum logging.
"""

import asyncio
import json
import sys
from pathlib import Path
import websockets
import time

# Test configuration
BACKEND_WS_URL = "ws://localhost:8002/ws/chat"
TEST_WORKSPACE = Path.home() / "TestApps" / "debug_test"
TEST_TIMEOUT = 120  # 2 minutes

# Very simple task
SIMPLE_TASK = """Write a simple Python function that adds two numbers together.
Include a docstring and type hints."""


async def run_debug_test():
    """Run simple debug test."""
    print("="*60)
    print("🔍 DEBUG TEST - Simple Task with Maximum Logging")
    print("="*60)
    print(f"Backend: {BACKEND_WS_URL}")
    print(f"Workspace: {TEST_WORKSPACE}")
    print("="*60)

    # Create fresh workspace
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    print(f"✅ Workspace created: {TEST_WORKSPACE}")

    # Connect to backend
    print(f"\n🔌 Connecting to {BACKEND_WS_URL}...")

    try:
        ws = await websockets.connect(BACKEND_WS_URL, ping_interval=10)
        print("✅ Connected to WebSocket")

        # Send init message
        init_msg = {
            "type": "init",
            "workspace_path": str(TEST_WORKSPACE)
        }
        print(f"\n📤 Sending init message: {json.dumps(init_msg, indent=2)}")
        await ws.send(json.dumps(init_msg))

        # Wait for init confirmation (with short timeout)
        print("\n⏳ Waiting for init response (5s timeout)...")
        try:
            response = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(response)
            print(f"📥 Init response: {json.dumps(data, indent=2)}")
        except asyncio.TimeoutError:
            print("⚠️ No init response received within 5s")

        # Send simple task
        print("\n" + "="*40)
        print("📋 SENDING SIMPLE TASK")
        print("="*40)
        print(f"Task: {SIMPLE_TASK}")

        task_msg = {
            "type": "task",
            "task": SIMPLE_TASK
        }
        print(f"\n📤 Sending task message: {json.dumps(task_msg, indent=2)}")
        await ws.send(json.dumps(task_msg))

        # Receive messages with aggressive timeouts
        print("\n" + "="*40)
        print("📥 MONITORING MESSAGES (2s timeouts)")
        print("="*40)

        start_time = time.time()
        message_count = 0
        no_message_count = 0
        all_messages = []

        while True:
            elapsed = time.time() - start_time
            if elapsed > TEST_TIMEOUT:
                print(f"\n⏱️ Test timeout after {TEST_TIMEOUT}s")
                break

            try:
                # NO TIMEOUT! With streaming, messages come continuously
                message = await ws.recv()
            except Exception as e:
                print(f"\n❌ Error receiving message: {e}")
                break

            message_count += 1

            try:
                data = json.loads(message)
                msg_type = data.get("type", "unknown")
                all_messages.append((elapsed, msg_type, data))

                # Show every single message
                print(f"\n[{elapsed:.1f}s] Message #{message_count}:")
                print(f"  Type: {msg_type}")
                print(f"  Full data: {json.dumps(data, indent=2)[:500]}...")  # First 500 chars

                # Break on completion or error
                if msg_type == "workflow_complete":
                    print("\n✅ WORKFLOW COMPLETE!")
                    break
                elif msg_type == "error":
                    print(f"\n❌ ERROR: {data.get('error', 'Unknown')}")
                    break

            except json.JSONDecodeError as e:
                print(f"\n⚠️ Invalid JSON received: {message[:100]}")
                print(f"  Error: {e}")

        await ws.close()
        print("\n🔌 Connection closed")

        # Summary
        print("\n" + "="*60)
        print("📊 DEBUG SUMMARY")
        print("="*60)
        print(f"Total time: {elapsed:.2f}s")
        print(f"Messages received: {message_count}")
        print(f"\nAll message types received:")
        msg_types = {}
        for t, msg_type, _ in all_messages:
            if msg_type not in msg_types:
                msg_types[msg_type] = []
            msg_types[msg_type].append(t)

        for msg_type, times in msg_types.items():
            print(f"  {msg_type}: {len(times)} times at {[f'{t:.1f}s' for t in times[:3]]}")

        if message_count == 0:
            print("\n⚠️ NO MESSAGES RECEIVED AT ALL!")
            print("Possible issues:")
            print("  1. Server not processing tasks")
            print("  2. WebSocket connection issue")
            print("  3. Message routing problem")
            return 1

        return 0

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    try:
        exit_code = asyncio.run(run_debug_test())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted")
        sys.exit(130)


if __name__ == "__main__":
    main()