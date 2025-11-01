#!/usr/bin/env python3
"""Simple test query to verify MCP backend works"""
import asyncio
import json
import websockets
import sys

async def test_simple():
    ws_url = "ws://localhost:8002/ws/chat"
    workspace = "/Users/dominikfoert/TestApps/test_new_app"

    print(f"🔌 Connecting to {ws_url}...")

    try:
        async with websockets.connect(ws_url) as ws:
            print("✅ Connected")

            # Send init
            init_msg = {"type": "init", "workspace_path": workspace}
            await ws.send(json.dumps(init_msg))
            print(f"📤 Sent init: {workspace}")

            # Wait for init response
            response = await ws.recv()
            data = json.loads(response)
            print(f"📥 Init response: {data.get('type')}, session: {data.get('session_id')}")

            # Send simple query
            query = "Create a simple hello.py file that prints 'Hello, World!'"
            query_msg = {"type": "chat", "content": query}  # Changed: type="chat", content=query
            await ws.send(json.dumps(query_msg))
            print(f"📤 Sent query: {query}")

            # Receive responses
            event_count = 0
            mcp_events = 0

            while True:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=120)
                    data = json.loads(response)
                    event_type = data.get("type")
                    event_count += 1

                    if event_type == "status":
                        print(f"📊 Status: {data.get('message', '')}")

                    elif event_type == "mcp_progress":
                        mcp_events += 1
                        server = data.get("server", "")
                        message = data.get("message", "")
                        print(f"⚡ MCP [{server}]: {message}")

                    elif event_type == "agent_step":
                        agent = data.get("agent", "")
                        print(f"🤖 Agent: {agent}")

                    elif event_type == "result" or event_type == "final_response":
                        response_text = data.get("content") or data.get("response", "")
                        print(f"\n✅ FINAL RESPONSE ({len(response_text)} chars):")
                        print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
                        break

                    elif event_type == "error":
                        print(f"❌ ERROR: {data.get('message', '')}")
                        return False

                except asyncio.TimeoutError:
                    print("⏱️  Timeout!")
                    return False

            print(f"\n📊 Summary:")
            print(f"   Events: {event_count}")
            print(f"   MCP progress events: {mcp_events}")
            print(f"   Result: ✅ SUCCESS")

            return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple())
    sys.exit(0 if success else 1)
