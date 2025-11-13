#!/usr/bin/env python3
"""
Simple WebSocket test client for KI AutoAgent
Sends init, then a simple request, and monitors responses
"""
import asyncio
import websockets
import json
import sys

async def test():
    uri = 'ws://localhost:8002/ws/chat'

    print(f"Connecting to {uri}...")
    async with websockets.connect(uri) as ws:
        # Wait for connected message
        msg = await ws.recv()
        print(f"[RECEIVED] {msg}")

        # Send INIT message first!
        print("\n[SENDING] init message...")
        await ws.send(json.dumps({
            'type': 'init',
            'workspace_path': '/Users/dominikfoert/TestApps/claude_safety_test'
        }))

        # Wait for initialized response
        msg = await ws.recv()
        data = json.loads(msg)
        print(f"[RECEIVED] {data.get('type')}: {data.get('message', '')}")

        # Send simple request
        print("\n[SENDING] message: Create hello.py...")
        await ws.send(json.dumps({
            'type': 'message',
            'content': 'Create a simple hello.py file that prints Hello World'
        }))

        print("\nWaiting for responses (60 seconds)...")
        print("=" * 80)

        # Receive responses for 60 seconds
        import time
        start = time.time()
        while time.time() - start < 60:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(msg)
                msg_type = data.get("type", "unknown")
                content = data.get("content", data.get("message", data.get("agent", "")))

                if isinstance(content, str):
                    content_preview = content[:150]
                else:
                    content_preview = str(content)[:150]

                print(f"[{msg_type.upper():15s}] {content_preview}")

                if msg_type == "complete":
                    print("\n✅ Workflow complete!")
                    break

            except asyncio.TimeoutError:
                print("... waiting ...")
            except Exception as e:
                print(f"❌ Error: {e}")
                break

        print("=" * 80)
        print("Test finished")

if __name__ == "__main__":
    asyncio.run(test())
