#!/usr/bin/env python
"""
Test 3: Real-World App Creation

Tests creating a complete TODO app with frontend and backend.
"""

import asyncio
import json
import sys
from pathlib import Path
import websockets
import time

# Test configuration
BACKEND_WS_URL = "ws://localhost:8002/ws/chat"
TEST_WORKSPACE = Path.home() / "TestApps" / "todo_app_test"
TEST_TIMEOUT = 600  # 10 minutes

# Complex task
TODO_APP_TASK = """Create a simple TODO application with:
1. Python backend (FastAPI)
2. HTML/CSS/JS frontend
3. Features:
   - Add new todos
   - Mark todos as complete
   - Delete todos
   - List all todos
4. Use SQLite for persistence
5. Include proper error handling
6. Add basic CSS styling
7. Write tests for the backend API"""


async def run_todo_app_test():
    """Run TODO app creation test."""
    print("="*60)
    print("🧪 Test 3: Real-World TODO App Creation")
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

        # Send TODO app task
        print("\n" + "="*60)
        print("📋 SENDING TODO APP CREATION TASK")
        print("="*60)
        print("Task: Create complete TODO application...")

        task_msg = {
            "type": "task",
            "task": TODO_APP_TASK
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
                message = await asyncio.wait_for(ws.recv(), timeout=5.0)
            except asyncio.TimeoutError:
                print(f"⏱️ 5s timeout at {elapsed:.1f}s - Messages so far: {message_count}")
                # Check if we're stuck
                if elapsed > 30 and message_count < 5:
                    print("⚠️ Warning: Very few messages received, may be stuck!")
                if elapsed > 60 and len(agents_executed) == 0:
                    print("⚠️ Warning: No agents executed after 60s!")
                continue

            message_count += 1
            data = json.loads(message)
            msg_type = data.get("type")

            # Debug: Show all message types
            print(f"[{elapsed:.1f}s] Received: {msg_type}")

            if message_count % 10 == 0:
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
        for file in files_generated[:10]:  # Show first 10 files
            print(f"  - {file}")
        if len(files_generated) > 10:
            print(f"  ... and {len(files_generated) - 10} more")
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

        # Check for essential agents
        expected_agents = {"research", "codesmith"}
        missing_agents = expected_agents - set(agents_executed)
        if missing_agents:
            failures.append(f"❌ Missing agents: {', '.join(missing_agents)}")

        # Check for essential files
        essential_patterns = ["main.py", "app.py", ".html", ".js", ".css", "test"]
        found_patterns = {
            pattern: any(pattern in str(f).lower() for f in files_generated)
            for pattern in essential_patterns
        }
        missing_patterns = [p for p, found in found_patterns.items() if not found]
        if missing_patterns:
            failures.append(f"❌ Missing file types: {', '.join(missing_patterns)}")

        if len(errors) > 0:
            failures.append(f"❌ {len(errors)} errors occurred")

        if len(failures) == 0:
            print("✅ ALL CHECKS PASSED")
            print("\nTODO app creation successful!")
            print(f"Check your app at: {TEST_WORKSPACE}")
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
        exit_code = asyncio.run(run_todo_app_test())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted")
        sys.exit(130)


if __name__ == "__main__":
    main()