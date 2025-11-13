#!/usr/bin/env python3
"""Check WebSocket status and monitor workflow progress."""

import asyncio
import websockets
import json
from datetime import datetime

async def monitor_workflow():
    """Monitor the workflow progress via WebSocket."""
    uri = "ws://localhost:8002/ws/chat"

    try:
        async with websockets.connect(uri) as ws:
            print("✅ Connected to WebSocket")

            # Send init message
            init_msg = {
                "type": "init",
                "workspace_path": "/Users/dominikfoert/TestApps/test_status_check"
            }
            await ws.send(json.dumps(init_msg))
            print("📤 Sent INIT message")

            # Send status query
            query_msg = {
                "type": "status"
            }
            await ws.send(json.dumps(query_msg))
            print("📤 Sent STATUS query")

            # Listen for events
            print("\n📥 Receiving events:")
            print("-" * 50)

            event_count = 0
            start_time = datetime.now()

            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    event = json.loads(msg)
                    event_count += 1

                    elapsed = (datetime.now() - start_time).total_seconds()

                    print(f"[{event_count}] {elapsed:.1f}s - Type: {event.get('type')}")

                    # Show relevant details
                    if event.get('type') == 'workflow_event':
                        print(f"    Node: {event.get('node')}")
                        if 'state_update' in event:
                            update = event['state_update']
                            if 'last_agent' in update:
                                print(f"    Agent: {update['last_agent']}")
                    elif event.get('type') == 'mcp_progress':
                        print(f"    Server: {event.get('server')}")
                        print(f"    Message: {event.get('message')}")
                        print(f"    Progress: {event.get('progress', 0) * 100:.1f}%")
                    elif event.get('type') == 'credit_update':
                        usage = event.get('usage', {})
                        print(f"    Session: ${usage.get('session_total', 0):.4f}")
                        print(f"    Credits used: ${usage.get('total_cost', 0):.4f}")
                    elif event.get('type') == 'error':
                        print(f"    ❌ Error: {event.get('error', event.get('message'))}")
                        break
                    elif event.get('type') == 'workflow_complete':
                        print(f"    ✅ Workflow completed!")
                        break

                    # Limit to 20 events
                    if event_count >= 20:
                        print("\n⚠️ Reached 20 events limit")
                        break

                except asyncio.TimeoutError:
                    print("\n⏱️ No events received for 5 seconds")
                    break
                except Exception as e:
                    print(f"\n❌ Error: {e}")
                    break

            print("-" * 50)
            print(f"Total events: {event_count}")

    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(monitor_workflow())