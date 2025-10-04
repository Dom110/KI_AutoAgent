#!/usr/bin/env python3
"""
Send approval to continue workflow
"""
import asyncio
import websockets
import json
import sys

async def send_approval():
    uri = "ws://localhost:8001/ws/chat"
    workspace = "/Users/dominikfoert/TestApp"

    print(f"🔌 Connecting to {uri}...")

    async with websockets.connect(uri) as websocket:
        # 1. Wait for connection message
        msg = await websocket.recv()
        print(f"📨 Connected: {json.loads(msg)['message']}")

        # 2. Send init message
        init_msg = {"type": "init", "workspace_path": workspace}
        await websocket.send(json.dumps(init_msg))
        msg = await websocket.recv()
        print(f"✅ Initialized: {json.loads(msg)['message']}")

        # 3. Send approval
        approval_msg = {
            "type": "architecture_approval",
            "approved": True,
            "message": "Architecture approved - proceed with implementation"
        }
        print(f"\n✅ Sending approval...")
        await websocket.send(json.dumps(approval_msg))
        print(f"📤 Sent: {approval_msg}")

        print("\n📡 Monitoring workflow continuation...")
        print("=" * 80)

        # Monitor for 120 seconds
        try:
            async with asyncio.timeout(120):
                while True:
                    response = await websocket.recv()
                    data = json.loads(response)

                    msg_type = data.get("type", "")
                    agent = data.get("agent", "")
                    content = data.get("content", "")

                    if msg_type == "agent_progress":
                        print(f"⚙️  [{agent}] {content}")
                    elif msg_type == "agent_tool_start":
                        tool = data.get("tool", "")
                        print(f"🔧 [{agent}] Starting: {tool}")
                    elif msg_type == "agent_tool_complete":
                        tool = data.get("tool", "")
                        status = data.get("tool_status", "")
                        print(f"✅ [{agent}] {tool}: {status}")
                    elif "codesmith" in agent.lower() and "writing" in content.lower():
                        print(f"📝 [{agent}] {content}")
                    elif msg_type == "chat":
                        print(f"💬 {content[:150]}")
                    elif msg_type == "workflow_complete":
                        print(f"\n🎉 WORKFLOW COMPLETE!")
                        break
                    elif msg_type == "error":
                        print(f"❌ ERROR: {content}")

        except asyncio.TimeoutError:
            print("\n⏱️  Timeout (120s)")

if __name__ == "__main__":
    asyncio.run(send_approval())
