#!/usr/bin/env python3
"""
Live WebSocket Monitor for E2E Test
Shows ALL WebSocket messages in real-time.
"""

import asyncio
import json
import shutil
from datetime import datetime
from pathlib import Path
import websockets
import sys

# Configuration
TEST_WORKSPACE = Path.home() / "TestApps" / "e2e_live_test"
SERVER_URL = "ws://localhost:8002/ws/chat"
TIMEOUT = 300  # 5 minutes max


async def run_live_e2e_test():
    """Run E2E test with live WebSocket monitoring."""

    print("\n" + "="*120)
    print("🔴 LIVE WEBSOCKET MONITOR - E2E TEST")
    print("="*120)
    print(f"📁 Workspace: {TEST_WORKSPACE}")
    print(f"🌐 Server: {SERVER_URL}")
    print(f"⏱️  Timeout: {TIMEOUT}s")
    print("="*120)
    print()

    # Clean workspace
    if TEST_WORKSPACE.exists():
        shutil.rmtree(TEST_WORKSPACE)
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)

    start_time = datetime.now()
    event_count = 0

    try:
        print("🔌 Connecting to WebSocket...")
        async with websockets.connect(SERVER_URL) as ws:
            print("✅ WebSocket connected\n")
            print("-"*120)
            print("📡 LIVE WEBSOCKET STREAM:")
            print("-"*120)

            # Send INIT
            init_msg = {"type": "init", "workspace_path": str(TEST_WORKSPACE)}
            await ws.send(json.dumps(init_msg))
            print(f"\n📤 SENT: {json.dumps(init_msg)}")

            # Get connection response
            msg = await ws.recv()
            event = json.loads(msg)
            event_count += 1
            print(f"\n📥 [{event_count:03d}] RECEIVED:")
            print(json.dumps(event, indent=2))

            # Get initialization response
            msg = await ws.recv()
            event = json.loads(msg)
            event_count += 1
            print(f"\n📥 [{event_count:03d}] RECEIVED:")
            print(json.dumps(event, indent=2))

            # Send task
            task = "Create a simple Python function that adds two numbers and returns the result."
            task_msg = {"type": "chat", "query": task}
            await ws.send(json.dumps(task_msg))
            print(f"\n📤 SENT: {json.dumps(task_msg)}")

            print("\n" + "-"*120)
            print("📊 WORKFLOW EVENTS:")
            print("-"*120)

            # Monitor all events
            workflow_complete = False
            error_occurred = False
            last_event_time = datetime.now()

            while not workflow_complete and not error_occurred:
                try:
                    # Wait for message with timeout
                    msg = await asyncio.wait_for(ws.recv(), timeout=30)
                    event = json.loads(msg)
                    event_count += 1

                    elapsed = (datetime.now() - start_time).total_seconds()
                    event_type = event.get("type")

                    # Print full event
                    print(f"\n📥 [{event_count:03d}] {elapsed:6.1f}s - {event_type}")
                    print("-"*80)

                    # Pretty print the full event
                    print(json.dumps(event, indent=2))

                    # Track special events
                    if event_type == "workflow_complete":
                        workflow_complete = True
                        print("\n✅ WORKFLOW COMPLETE!")
                    elif event_type == "error":
                        error_occurred = True
                        print(f"\n❌ ERROR: {event.get('error', event.get('message'))}")

                    last_event_time = datetime.now()

                except asyncio.TimeoutError:
                    idle = (datetime.now() - last_event_time).total_seconds()
                    print(f"\n⏳ No events for 30s (idle: {idle:.0f}s total)")

                    if idle > 120:
                        print("❌ Timeout - no activity for 2 minutes")
                        break

            print("\n" + "="*120)
            print("📊 FINAL SUMMARY:")
            print("-"*120)
            print(f"  Total Events: {event_count}")
            print(f"  Duration: {(datetime.now() - start_time).total_seconds():.1f}s")
            print(f"  Status: {'✅ SUCCESS' if workflow_complete else '❌ FAILED'}")

            # Check files
            print(f"\n📂 Files in workspace:")
            files = list(TEST_WORKSPACE.glob("**/*"))
            if files:
                for f in files:
                    if f.is_file():
                        print(f"  - {f.relative_to(TEST_WORKSPACE)}")
            else:
                print("  (empty)")

            print("="*120)

    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()

    return event_count > 0


if __name__ == "__main__":
    success = asyncio.run(run_live_e2e_test())
    sys.exit(0 if success else 1)