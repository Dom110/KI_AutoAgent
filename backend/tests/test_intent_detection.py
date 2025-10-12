#!/usr/bin/env python3
"""
Quick test for Intent Detection integration

Tests if "Fix TypeScript errors" request properly routes to ReviewFix
instead of going through full CREATE workflow.
"""

import asyncio
import json
import websockets


WS_URL = "ws://localhost:8002/ws/chat"
WORKSPACE = "/Users/dominikfoert/TestApps/todo_app_v6_1_test"

TASKS = [
    ("CREATE Test", "Create a simple calculator app"),
    ("FIX Test", "Fix the TypeScript compilation errors in this application"),
    ("REFACTOR Test", "Refactor the authentication module"),
    ("EXPLAIN Test", "Explain how the todo list works")
]


async def test_intent_detection():
    """Test intent detection for different request types."""

    print("🧪 Testing Intent Detection")
    print("=" * 80)

    for test_name, task in TASKS:
        print(f"\n📋 {test_name}")
        print(f"   Task: \"{task}\"")
        print()

        try:
            async with websockets.connect(WS_URL) as ws:
                # Receive connected message
                await ws.recv()

                # Send init
                await ws.send(json.dumps({
                    "type": "init",
                    "workspace_path": WORKSPACE
                }))

                # Wait for initialized
                await ws.recv()

                # Send task
                await ws.send(json.dumps({
                    "type": "message",
                    "content": task
                }))

                # Wait for first few messages to see workflow routing
                print("   Waiting for workflow start messages...")
                for _ in range(10):
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                        data = json.loads(msg)

                        if data.get("type") == "workflow_started":
                            print(f"   ✅ Workflow started: {data.get('workflow_type')}")

                        elif data.get("type") == "agent_start":
                            agent = data.get("agent", "unknown")
                            print(f"   🤖 Agent: {agent}")

                            # For FIX test, we expect reviewfix first!
                            if "FIX" in test_name and agent == "reviewfix":
                                print(f"   🎯 SUCCESS! FIX routed directly to ReviewFix!")
                            elif "FIX" in test_name and agent == "research":
                                print(f"   ❌ FAIL! FIX still going through Research (wrong workflow)!")

                            # For CREATE test, we expect research first
                            if "CREATE" in test_name and agent == "research":
                                print(f"   ✅ CREATE correctly routed through Research")

                        elif data.get("type") == "error":
                            print(f"   ❌ Error: {data.get('message')}")
                            break

                    except asyncio.TimeoutError:
                        break

                # Close connection (don't wait for full workflow)
                await ws.close()

        except Exception as e:
            print(f"   ❌ Test failed: {e}")

        print()

    print("=" * 80)
    print("✅ Intent Detection Test Complete")


if __name__ == "__main__":
    asyncio.run(test_intent_detection())
