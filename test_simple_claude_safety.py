#!/usr/bin/env python3
"""
Test Claude safety mechanisms - single simple task
"""

import asyncio
import websockets
import json
import time

async def test_simple_task():
    """Test a single simple task with Claude safety"""

    print("=" * 80)
    print("🧪 TESTING CLAUDE SAFETY MECHANISMS")
    print("=" * 80)

    uri = "ws://localhost:8002/ws/chat"
    workspace = "/Users/dominikfoert/TestApps/claude_safety_test"

    async with websockets.connect(uri) as websocket:
        # Send init message
        await websocket.send(json.dumps({
            "type": "init",
            "workspace_path": workspace
        }))

        # Wait for connection confirmation
        response = await websocket.recv()
        data = json.loads(response)
        if data.get("status") == "connected":
            print(f"✅ Connected to server")

        # Send simple task
        task = "Create a simple Python function that returns 'Hello World'"
        print(f"\n📤 Task: {task}")

        await websocket.send(json.dumps({
            "type": "chat",
            "query": task
        }))

        # Monitor events
        start_time = time.time()
        events = []
        claude_started = False
        claude_completed = False

        try:
            while True:
                response = await asyncio.wait_for(websocket.recv(), timeout=300)
                event = json.loads(response)
                events.append(event)

                event_type = event.get("type", "unknown")
                elapsed = time.time() - start_time

                # Print key events
                if event_type == "agent_event":
                    agent = event.get("data", {}).get("agent", "unknown")
                    print(f"[{elapsed:5.1f}s] Agent: {agent}")

                elif event_type == "mcp_progress":
                    server = event.get("server", "")
                    message = event.get("message", "")
                    if "claude" in server.lower() or "CLAUDE" in message:
                        if "STARTING CLAUDE" in message:
                            claude_started = True
                            print(f"[{elapsed:5.1f}s] ⚠️ CLAUDE STARTING: {message}")
                        elif "CLAUDE EXECUTION COMPLETE" in message:
                            claude_completed = True
                            print(f"[{elapsed:5.1f}s] ✅ CLAUDE COMPLETE: {message}")
                        elif "KILLING" in message or "FOUND EXISTING CLAUDE" in message:
                            print(f"[{elapsed:5.1f}s] 🚨 SAFETY: {message}")

                elif event_type == "workflow_complete":
                    print(f"[{elapsed:5.1f}s] ✅ Workflow complete!")
                    break

                elif event_type == "error":
                    print(f"[{elapsed:5.1f}s] ❌ Error: {event.get('message', 'Unknown error')}")
                    break

        except asyncio.TimeoutError:
            print(f"⏰ Timeout after 300 seconds")

        print("\n" + "=" * 80)
        print("📊 ANALYSIS:")
        print("-" * 80)

        # Count Claude-related events
        claude_events = [e for e in events if "claude" in str(e).lower()]
        kill_events = [e for e in events if "KILLING" in str(e) or "KILL" in str(e)]

        print(f"Total events: {len(events)}")
        print(f"Claude-related events: {len(claude_events)}")
        print(f"Kill/safety events: {len(kill_events)}")
        print(f"Claude started: {claude_started}")
        print(f"Claude completed: {claude_completed}")

        # Check for multiple Claude instances
        claude_starts = sum(1 for e in events if "STARTING CLAUDE" in str(e))
        print(f"\n⚠️ Claude start attempts: {claude_starts}")

        if claude_starts > 1:
            print("❌ MULTIPLE CLAUDE INSTANCES DETECTED!")
        elif claude_starts == 1 and claude_completed:
            print("✅ SINGLE CLAUDE INSTANCE - SAFETY WORKING!")
        elif claude_starts == 0:
            print("⚠️ No Claude instance started")

        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_simple_task())