#!/usr/bin/env python3
"""
Test script to send Dashboard App creation request via WebSocket
"""
import asyncio
import websockets
import json
import sys

async def send_dashboard_request():
    uri = "ws://localhost:8001/ws/chat"
    workspace = "/Users/dominikfoert/TestApp"
    session_id = None  # Will be populated from connection

    print(f"🔌 Connecting to {uri}...")

    async with websockets.connect(uri) as websocket:
        # 1. Wait for connection message
        msg = await websocket.recv()
        conn_data = json.loads(msg)
        session_id = conn_data.get("session_id")
        print(f"📨 Received: {msg}")
        print(f"🔑 Session ID: {session_id}")

        # 2. Send init message with workspace
        init_msg = {
            "type": "init",
            "workspace_path": workspace
        }
        print(f"📤 Sending init: {json.dumps(init_msg, indent=2)}")
        await websocket.send(json.dumps(init_msg))

        # 3. Wait for initialized confirmation
        msg = await websocket.recv()
        print(f"📨 Received: {msg}")

        # 4. Send chat message
        chat_msg = {
            "type": "chat",
            "content": "Erstelle eine Dashboard App mit React und Chart.js"
        }
        print(f"\n📤 Sending chat request: {json.dumps(chat_msg, indent=2)}")
        await websocket.send(json.dumps(chat_msg))

        print("\n✅ Request sent! Monitoring responses...")
        print("=" * 80)

        # 5. Monitor responses for 180 seconds (3 minutes)
        try:
            async with asyncio.timeout(180):
                while True:
                    response = await websocket.recv()
                    data = json.loads(response)

                    msg_type = data.get("type", "unknown")
                    agent = data.get("agent", "")
                    content = data.get("content", "")

                    # Print ALL messages for debugging
                    print(f"\n🔍 DEBUG - Message Type: {msg_type}")
                    if len(str(data)) < 300:
                        print(f"   Full data: {data}")

                    # Format output based on message type
                    if msg_type == "agent_thinking":
                        print(f"💭 [{agent}] Thinking: {content[:100]}...")
                    elif msg_type == "agent_progress":
                        print(f"⚙️  [{agent}] Progress: {content}")
                    elif msg_type == "agent_tool_start":
                        tool = data.get("tool", "")
                        print(f"🔧 [{agent}] Tool: {tool}")
                    elif msg_type == "agent_tool_complete":
                        tool = data.get("tool", "")
                        status = data.get("tool_status", "")
                        print(f"✅ [{agent}] Tool {tool}: {status}")
                    elif msg_type == "approval_request" or msg_type == "architecture_proposal":
                        print(f"\n🚨 APPROVAL/PROPOSAL MESSAGE:")
                        print(f"   Type: {msg_type}")
                        print(f"   Approval Type: {data.get('approval_type', 'N/A')}")
                        print(f"   Content: {content[:300]}...")
                        print(f"\n   ⚠️  Need to send approval response!\n")

                        # AUTO-APPROVE for testing (correct format!)
                        approval_response = {
                            "type": "architecture_approval",
                            "session_id": session_id,
                            "decision": "approved",
                            "feedback": "Auto-approved for testing"
                        }
                        print(f"📤 AUTO-APPROVING with session {session_id}: {approval_response}")
                        await websocket.send(json.dumps(approval_response))
                    elif msg_type == "chat":
                        print(f"💬 {content[:200]}")
                    elif msg_type == "error":
                        print(f"❌ ERROR: {content}")
                    elif msg_type == "workflow_complete":
                        print(f"\n🎉 WORKFLOW COMPLETE!")
                        print(f"   Final message: {content[:200]}")
                    else:
                        print(f"📨 Other: {str(data)[:200]}")

        except asyncio.TimeoutError:
            print("\n⏱️  Timeout reached (60s)")
        except KeyboardInterrupt:
            print("\n⏹️  Stopped by user")

if __name__ == "__main__":
    print("🚀 KI AutoAgent - Dashboard App Test")
    print("=" * 80)
    asyncio.run(send_dashboard_request())
