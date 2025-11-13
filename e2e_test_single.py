#!/usr/bin/env python3
"""
Single E2E Test Runner
Führt nur EINEN E2E Test aus für schnelles Debugging.
"""

import asyncio
import json
import shutil
from datetime import datetime
from pathlib import Path
import websockets
import sys

# Configuration
TEST_WORKSPACE = Path.home() / "TestApps" / "e2e_single_test"
SERVER_URL = "ws://localhost:8002/ws/chat"
TIMEOUT = 180  # 3 minutes for Claude


async def run_single_e2e_test():
    """Run a single E2E test."""

    print("="*100)
    print("🧪 SINGLE E2E TEST - Temperature Converter")
    print("="*100)
    print(f"📁 Workspace: {TEST_WORKSPACE}")
    print(f"🌐 Server: {SERVER_URL}")
    print(f"⏱️  Timeout: {TIMEOUT}s")
    print("="*100)

    # Clean workspace
    if TEST_WORKSPACE.exists():
        shutil.rmtree(TEST_WORKSPACE)
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    print("✅ Workspace cleaned")

    start_time = datetime.now()
    events_received = []
    routing_path = []
    credits_used = 0.0
    error = None
    workflow_complete = False

    try:
        # Connect to WebSocket
        async with websockets.connect(SERVER_URL) as ws:
            print("✅ Connected to server")

            # Initialize session
            init_msg = {"type": "init", "workspace_path": str(TEST_WORKSPACE)}
            await ws.send(json.dumps(init_msg))
            print("📤 Sent INIT message")

            # Wait for connection confirmation
            conn_response = await asyncio.wait_for(ws.recv(), timeout=5)
            conn_data = json.loads(conn_response)
            print(f"📥 Connection: {conn_data.get('type')}")

            # Wait for initialization response
            init_response = await asyncio.wait_for(ws.recv(), timeout=5)
            init_data = json.loads(init_response)
            if init_data.get("type") == "initialized":
                print("✅ Session initialized")
                session_id = init_data.get("session_id")
                print(f"   Session ID: {session_id}")
            else:
                print(f"❌ Initialization failed: {init_data}")
                return False

            # Send task
            task = "Create a Python CLI tool that converts temperatures between Celsius, Fahrenheit, and Kelvin. Include input validation and error handling."
            task_msg = {"type": "chat", "query": task}
            await ws.send(json.dumps(task_msg))
            print(f"📤 Sent TASK: {task[:80]}...")

            # Monitor workflow
            print("\n" + "="*100)
            print("MONITORING WORKFLOW PROGRESS:")
            print("-"*100)

            event_count = 0
            last_update = datetime.now()

            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=10)
                    event = json.loads(msg)
                    event_count += 1
                    events_received.append(event)

                    event_type = event.get("type")
                    elapsed = (datetime.now() - start_time).total_seconds()

                    # Display event
                    print(f"[{event_count:3d}] {elapsed:6.1f}s | {event_type:20s}", end="")

                    # Process event types
                    if event_type == "workflow_event":
                        node = event.get("node")
                        state = event.get("state_update", {})
                        if "last_agent" in state:
                            agent = state["last_agent"]
                            routing_path.append(agent)
                            print(f" | Node: {node:12s} | Agent: {agent}")
                        else:
                            print(f" | Node: {node}")

                    elif event_type == "mcp_progress":
                        server = event.get("server")
                        message = event.get("message", "")[:50]
                        progress = event.get("progress", 0) * 100
                        print(f" | {server:15s} | {progress:5.1f}% | {message}")

                    elif event_type == "credit_update":
                        usage = event.get("usage", {})
                        credits_used = usage.get("session_total", 0)
                        print(f" | Credits: ${credits_used:.4f}")

                    elif event_type == "status":
                        status = event.get("status")
                        message = event.get("message", "")[:50]
                        print(f" | Status: {status} | {message}")

                    elif event_type == "error":
                        error = event.get("error") or event.get("message")
                        print(f" | ❌ ERROR: {error}")
                        break

                    elif event_type == "workflow_complete":
                        workflow_complete = True
                        print(f" | ✅ WORKFLOW COMPLETE!")
                        break

                    else:
                        print(f" | {str(event)[:50]}")

                    last_update = datetime.now()

                except asyncio.TimeoutError:
                    idle_time = (datetime.now() - last_update).total_seconds()
                    print(f"\n⏳ No events for 10s (idle: {idle_time:.0f}s)")

                    # Check if stuck too long
                    if idle_time > 60:
                        print("❌ Workflow appears stuck (>60s idle)")
                        error = "Workflow timeout - no progress"
                        break

            print("-"*100)

    except Exception as e:
        error = str(e)
        print(f"\n❌ Connection error: {e}")

    duration = (datetime.now() - start_time).total_seconds()

    # Check results
    print("\n" + "="*100)
    print("CHECKING GENERATED FILES:")
    print("-"*100)

    expected_files = ["temp_converter.py", "README.md", "requirements.txt"]
    found_files = []

    for file_name in expected_files:
        file_path = TEST_WORKSPACE / file_name
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"  ✅ {file_name:20s} ({size:,} bytes)")
            found_files.append(file_name)
        else:
            print(f"  ❌ {file_name:20s} (not found)")

    # List all generated files
    all_files = list(TEST_WORKSPACE.glob("**/*"))
    if all_files:
        print("\nAll generated files:")
        for f in all_files:
            if f.is_file():
                rel_path = f.relative_to(TEST_WORKSPACE)
                print(f"  - {rel_path}")

    # Final summary
    print("\n" + "="*100)
    print("TEST SUMMARY:")
    print("-"*100)
    print(f"  Duration:    {duration:.1f}s")
    print(f"  Events:      {event_count}")
    print(f"  Credits:     ${credits_used:.4f}")
    print(f"  Routing:     {' → '.join(routing_path[:10])}")
    print(f"  Files:       {len(found_files)}/{len(expected_files)}")

    success = workflow_complete and not error and len(found_files) >= 1

    if success:
        print(f"  Result:      ✅ PASSED")
    else:
        print(f"  Result:      ❌ FAILED")
        if error:
            print(f"  Error:       {error}")

    print("="*100)

    return success


if __name__ == "__main__":
    success = asyncio.run(run_single_e2e_test())
    sys.exit(0 if success else 1)