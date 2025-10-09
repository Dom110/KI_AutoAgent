#!/usr/bin/env python3
"""
WebSocket Test: Direct connection to v6 backend

Simulates what VSCode Extension does:
1. Connect to ws://localhost:8002/ws/chat
2. Send init message with workspace_path
3. Send chat message
4. Receive and print all responses

This verifies v6 backend protocol works correctly.
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime

WS_URL = "ws://localhost:8002/ws/chat"
WORKSPACE = "/Users/dominikfoert/TestApps/manualTest"

def print_header(text: str):
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")

def print_msg(direction: str, msg_type: str, data: dict):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {direction} {msg_type}")
    print(f"  {json.dumps(data, indent=2)}")
    print()

async def test_websocket():
    print_header("WebSocket Connection Test: v6 Backend")

    try:
        print(f"🔗 Connecting to {WS_URL}...")
        async with websockets.connect(WS_URL) as websocket:
            print("✅ Connected!\n")

            # Step 1: Receive welcome message
            print("📨 Waiting for welcome message...")
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print_msg("⬇️  RECV", welcome_data.get("type", "unknown"), welcome_data)

            if welcome_data.get("type") != "connected":
                print(f"❌ Expected 'connected', got '{welcome_data.get('type')}'")
                return 1

            if not welcome_data.get("requires_init"):
                print("❌ Expected requires_init=true")
                return 1

            print("✅ Welcome message OK - requires_init=true")

            # Step 2: Send init message
            print("📤 Sending init message...")
            init_msg = {
                "type": "init",
                "workspace_path": WORKSPACE
            }
            await websocket.send(json.dumps(init_msg))
            print_msg("⬆️  SENT", "init", init_msg)

            # Step 3: Receive initialized confirmation
            print("📨 Waiting for initialized confirmation...")
            init_response = await websocket.recv()
            init_data = json.loads(init_response)
            print_msg("⬇️  RECV", init_data.get("type", "unknown"), init_data)

            if init_data.get("type") != "initialized":
                print(f"❌ Expected 'initialized', got '{init_data.get('type')}'")
                return 1

            session_id = init_data.get("session_id")
            if not session_id:
                print("❌ No session_id in initialized message")
                return 1

            print(f"✅ Initialized OK - session_id: {session_id}")

            # Step 4: Send chat message
            print("📤 Sending chat message...")
            chat_msg = {
                "type": "chat",
                "message": "Erstelle eine einfache Hello World App",
                "session_id": session_id,
                "mode": "auto"
            }
            await websocket.send(json.dumps(chat_msg))
            print_msg("⬆️  SENT", "chat", chat_msg)

            # Step 5: Receive responses
            print("📨 Waiting for responses (max 120 seconds)...")
            print("=" * 80)

            response_count = 0
            start_time = asyncio.get_event_loop().time()
            timeout = 120  # 2 minutes

            while True:
                try:
                    # Wait for message with timeout
                    remaining = timeout - (asyncio.get_event_loop().time() - start_time)
                    if remaining <= 0:
                        print("\n⏱️  Timeout reached (120 seconds)")
                        break

                    response = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=min(10, remaining)
                    )
                    response_data = json.loads(response)
                    response_count += 1

                    msg_type = response_data.get("type", "unknown")
                    print_msg("⬇️  RECV", msg_type, response_data)

                    # Check for completion
                    if msg_type == "workflow_complete":
                        print("✅ Workflow completed!")
                        print(f"   Success: {response_data.get('success')}")
                        print(f"   Quality: {response_data.get('quality_score')}")
                        print(f"   Files: {len(response_data.get('files_generated', []))}")
                        print(f"   v6 Systems: {response_data.get('v6_insights', {})}")
                        break

                    elif msg_type == "error":
                        print(f"❌ Error: {response_data.get('message')}")
                        break

                except asyncio.TimeoutError:
                    print("⏳ Still waiting...")
                    continue

            print("\n" + "=" * 80)
            print(f"  Received {response_count} messages")
            print("=" * 80)

            return 0

    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}")
        return 1

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    try:
        return asyncio.run(test_websocket())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 1

if __name__ == "__main__":
    sys.exit(main())
