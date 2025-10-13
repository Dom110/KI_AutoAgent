#!/usr/bin/env python3
"""
Simple WebSocket test to verify basic connectivity and response
"""
import asyncio
import json
import websockets
from pathlib import Path

WORKSPACE = Path.home() / "TestApps" / "simple_test"
WS_URL = "ws://localhost:8002/ws/chat"

async def test_simple_connection():
    """Test basic WebSocket connection and simple query."""
    print(f"🔌 Connecting to {WS_URL}")

    # Create workspace
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    print(f"📁 Created workspace: {WORKSPACE}")

    async with websockets.connect(WS_URL) as ws:
        print("✅ Connected!")

        # 1. Initialize session
        init_msg = {
            "type": "init",
            "workspace_path": str(WORKSPACE)
        }
        await ws.send(json.dumps(init_msg))
        print(f"📤 Sent init: {init_msg}")

        # 2. Wait for TWO responses: "connected" first, then "initialized"
        # First message: "connected" (welcome message)
        response1 = await asyncio.wait_for(ws.recv(), timeout=10)
        data1 = json.loads(response1)
        print(f"📥 Welcome message: {data1.get('type')}")

        # Second message: "initialized" (after workflow initialization)
        response2 = await asyncio.wait_for(ws.recv(), timeout=30)  # Longer timeout for initialization
        data2 = json.loads(response2)
        print(f"📥 Init response: {data2}")

        if data2.get("type") != "initialized":
            print(f"❌ Expected 'initialized', got: {data2.get('type')}")
            return False

        session_id = data2.get("session_id")
        print(f"✅ Session initialized: {session_id}")

        # 3. Send simple query (use "chat" type)
        query_msg = {
            "type": "chat",  # Server expects "chat" or "message", not "query"
            "content": "Create a simple Hello World Python script"
        }
        await ws.send(json.dumps(query_msg))
        print(f"📤 Sent query: {query_msg['content']}")

        # 4. Wait for responses
        # NOTE: Workflow can take 10-15 minutes for complete execution
        print("⏳ Waiting for responses (max 15 minutes)...")
        timeout = 900  # 15 minutes
        start = asyncio.get_event_loop().time()
        response_count = 0

        while asyncio.get_event_loop().time() - start < timeout:
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                data = json.loads(response)
                response_count += 1

                msg_type = data.get("type")
                print(f"📥 [{response_count}] Type: {msg_type}")

                # Print relevant content
                if msg_type == "status":
                    print(f"   Status: {data.get('message', data.get('content', ''))}")
                elif msg_type == "response":
                    content = data.get("content", "")
                    print(f"   Response: {content[:100]}...")
                elif msg_type == "approval_request":
                    print(f"   Approval needed: {data.get('content', '')[:100]}")
                    # Auto-approve
                    approval_msg = {
                        "type": "approval_response",
                        "approved": True
                    }
                    await ws.send(json.dumps(approval_msg))
                    print(f"   ✅ Auto-approved")
                elif msg_type == "result":
                    print(f"   ✅ RESULT received!")
                    print(f"   Success: {data.get('success')}")
                    print(f"   Quality Score: {data.get('quality_score', 'N/A')}")
                    print(f"   Message: {data.get('message', '')}")
                    return True
                elif msg_type == "error":
                    print(f"   ❌ ERROR: {data.get('message')}")
                    return False

            except asyncio.TimeoutError:
                print(f"   ⏱️  No message for 5 seconds (total: {int(asyncio.get_event_loop().time() - start)}s)")
                continue

        print(f"❌ Test timed out after {timeout} seconds")
        print(f"   Received {response_count} messages but no result")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_simple_connection())
        if result:
            print("\n✅ TEST PASSED")
        else:
            print("\n❌ TEST FAILED")
    except Exception as e:
        print(f"\n❌ TEST CRASHED: {e}")
        import traceback
        traceback.print_exc()
