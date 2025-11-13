#!/usr/bin/env python3
"""
E2E Test 1: Build New App from Scratch

Tests the complete workflow:
- Research agent analyzes empty workspace
- Architect designs the app structure
- Codesmith generates all files
- ReviewFix validates and fixes issues
- Responder formats result

IMPORTANT: Runs in ~/TestApps/e2e_test_1_new_app (separate from dev repo)
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
import websockets

# Test configuration
BACKEND_URL = "ws://localhost:8002/ws/chat"
TEST_WORKSPACE = str(Path.home() / "TestApps" / "e2e_test_1_new_app")
TEST_QUERY = """
Create a Python CLI tool for converting temperatures between Celsius, Fahrenheit, and Kelvin.

Requirements:
- Support bidirectional conversion (any to any)
- Accept input via command line arguments
- Display results with 2 decimal places
- Include help text
- Add comprehensive tests
"""

# Test tracking
test_results = {
    "test_name": "E2E Test 1: Build New App",
    "start_time": datetime.now().isoformat(),
    "workspace": TEST_WORKSPACE,
    "query": TEST_QUERY,
    "events_received": 0,
    "mcp_progress_events": 0,
    "workflow_events": 0,
    "agents_executed": [],
    "files_created": [],
    "success": False,
    "errors": []
}


async def run_test():
    """Execute E2E test via WebSocket."""
    print("=" * 80)
    print("🧪 E2E Test 1: Build New App from Scratch")
    print("=" * 80)
    print(f"Workspace: {TEST_WORKSPACE}")
    print(f"Backend: {BACKEND_URL}")
    print()

    # Create fresh workspace
    os.makedirs(TEST_WORKSPACE, exist_ok=True)
    print(f"✅ Created test workspace: {TEST_WORKSPACE}\n")

    try:
        async with websockets.connect(BACKEND_URL) as websocket:
            print("✅ WebSocket connected\n")

            # Wait for connection message
            response = await websocket.recv()
            connect_response = json.loads(response)
            print(f"📥 Connect response: {connect_response}\n")

            if connect_response.get("type") != "connected":
                raise Exception(f"Connection failed: {connect_response}")

            session_id = connect_response.get("session_id")
            print(f"✅ Session ID: {session_id}\n")

            # Send initialization message
            init_msg = {
                "type": "init",
                "workspace_path": TEST_WORKSPACE
            }
            await websocket.send(json.dumps(init_msg))
            print(f"📤 Sent init: {init_msg}\n")

            # Wait for init success
            response = await websocket.recv()
            init_response = json.loads(response)
            print(f"📥 Init success: {init_response}\n")

            if init_response.get("type") != "initialized":
                raise Exception(f"Init failed: {init_response}")

            # Send user query
            query_msg = {
                "type": "message",
                "content": TEST_QUERY,
                "session_id": session_id
            }
            await websocket.send(json.dumps(query_msg))
            print(f"📤 Sent query: {TEST_QUERY[:100]}...\n")

            print("=" * 80)
            print("📊 Receiving Events...")
            print("=" * 80)

            # Receive events
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=600.0)
                    event = json.loads(message)
                    test_results["events_received"] += 1

                    event_type = event.get("type")
                    print(f"\n{'='*80}")
                    print(f"[Event #{test_results['events_received']}] Type: {event_type}")
                    print(f"{'='*80}")

                    # Print FULL event as pretty JSON (no truncation)
                    print(json.dumps(event, indent=2))
                    print(f"{'='*80}\n")

                    # Track different event types
                    if event_type == "mcp_progress":
                        test_results["mcp_progress_events"] += 1
                        server = event.get("server", "unknown")
                        msg = event.get("message", "")
                        progress = event.get("progress", 0.0)
                        print(f"   📊 MCP Progress ({server}): {msg} [{progress:.0%}]")

                    elif event_type == "workflow_event":
                        test_results["workflow_events"] += 1
                        node = event.get("node", "unknown")
                        state_update = event.get("state_update", {})
                        agent = state_update.get("last_agent")

                        print(f"   🔄 Workflow: {node}")
                        if agent:
                            print(f"      Agent: {agent}")
                            if agent not in test_results["agents_executed"]:
                                test_results["agents_executed"].append(agent)

                        # Track files
                        if "generated_files" in state_update:
                            files = state_update["generated_files"]
                            if files:
                                print(f"      Files: {len(files)} generated")
                                for f in files:
                                    path = f.get("path", "unknown")
                                    if path not in test_results["files_created"]:
                                        test_results["files_created"].append(path)

                    elif event_type == "workflow_complete":
                        print("   ✅ Workflow complete!")
                        test_results["success"] = True
                        break

                    elif event_type == "error":
                        error_msg = event.get("error", "Unknown error")
                        print(f"   ❌ Error: {error_msg}")
                        test_results["errors"].append(error_msg)
                        break

                except asyncio.TimeoutError:
                    print("\n❌ Timeout waiting for events (10 minutes)")
                    test_results["errors"].append("Timeout after 10 minutes")
                    break

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        test_results["errors"].append(str(e))
        import traceback
        traceback.print_exc()

    finally:
        test_results["end_time"] = datetime.now().isoformat()

        # Print summary
        print("\n" + "=" * 80)
        print("📊 Test Summary")
        print("=" * 80)
        print(f"Success: {test_results['success']}")
        print(f"Events received: {test_results['events_received']}")
        print(f"  - MCP progress events: {test_results['mcp_progress_events']}")
        print(f"  - Workflow events: {test_results['workflow_events']}")
        print(f"Agents executed: {test_results['agents_executed']}")
        print(f"Files created: {len(test_results['files_created'])}")
        if test_results['files_created']:
            for f in test_results['files_created']:
                print(f"   - {f}")
        if test_results['errors']:
            print(f"\nErrors: {len(test_results['errors'])}")
            for err in test_results['errors']:
                print(f"   - {err}")

        # Check workspace
        print(f"\n📁 Workspace contents:")
        if os.path.exists(TEST_WORKSPACE):
            for root, dirs, files in os.walk(TEST_WORKSPACE):
                level = root.replace(TEST_WORKSPACE, '').count(os.sep)
                indent = ' ' * 2 * level
                print(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 2 * (level + 1)
                for file in files:
                    print(f"{subindent}{file}")

        # Write report
        report_path = Path(__file__).parent / "E2E_TEST_1_REPORT.md"
        with open(report_path, "w") as f:
            f.write("# E2E Test 1: Build New App - Report\n\n")
            f.write(f"**Date:** {test_results['start_time']}\n\n")
            f.write(f"**Workspace:** `{TEST_WORKSPACE}`\n\n")
            f.write(f"**Query:**\n```\n{TEST_QUERY}\n```\n\n")
            f.write(f"## Results\n\n")
            f.write(f"- **Success:** {'✅' if test_results['success'] else '❌'}\n")
            f.write(f"- **Events:** {test_results['events_received']}\n")
            f.write(f"  - MCP Progress: {test_results['mcp_progress_events']}\n")
            f.write(f"  - Workflow: {test_results['workflow_events']}\n")
            f.write(f"- **Agents:** {', '.join(test_results['agents_executed'])}\n")
            f.write(f"- **Files:** {len(test_results['files_created'])}\n\n")

            if test_results['files_created']:
                f.write("### Generated Files\n\n")
                for file in test_results['files_created']:
                    f.write(f"- `{file}`\n")
                f.write("\n")

            if test_results['errors']:
                f.write("### Errors\n\n")
                for err in test_results['errors']:
                    f.write(f"- {err}\n")
                f.write("\n")

            f.write(f"**End Time:** {test_results.get('end_time', 'N/A')}\n")

        print(f"\n📄 Report saved: {report_path}")

        # Exit code
        sys.exit(0 if test_results['success'] else 1)


if __name__ == "__main__":
    asyncio.run(run_test())
