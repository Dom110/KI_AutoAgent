#!/usr/bin/env python3
"""
Quick test for architecture approval workflow
"""
import asyncio
import websockets
import json
import sys

async def test_approval():
    uri = "ws://localhost:8002/ws/chat"

    try:
        async with websockets.connect(uri) as ws:
            print("✅ Connected to backend")

            # Receive connection message
            msg = await ws.recv()
            data = json.loads(msg)
            print(f"📨 {data.get('type')}: session_id={data.get('session_id')}")
            session_id = data.get('session_id')

            # Set workspace
            await ws.send(json.dumps({
                "type": "setWorkspace",
                "workspacePath": "/Users/dominikfoert/git/KI_AutoAgent"
            }))

            # Send task
            await ws.send(json.dumps({
                "type": "chat",
                "message": "Erstelle eine Tetris App mit TypeScript"
            }))
            print("📤 Sent task request")

            # Listen for messages
            message_count = 0
            while message_count < 10:  # Limit to 10 messages
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=30.0)
                    data = json.loads(msg)
                    msg_type = data.get('type')
                    message_count += 1

                    print(f"\n📨 Message #{message_count}: {msg_type}")

                    if msg_type == "agent_thinking":
                        agent = data.get('agent')
                        print(f"   💭 {agent} is thinking...")

                    elif msg_type == "architecture_proposal":
                        print("   🏛️  ARCHITECTURE PROPOSAL RECEIVED!")
                        proposal = data.get('proposal', {})
                        print(f"   Summary: {proposal.get('summary', '')[:100]}")

                        # Send approval
                        await ws.send(json.dumps({
                            "type": "architecture_approval",
                            "session_id": session_id,
                            "decision": "approved",
                            "feedback": "Looks good!"
                        }))
                        print("   ✅ Sent approval")

                    elif msg_type == "architectureApprovalProcessed":
                        print("   ✅ APPROVAL PROCESSED!")

                    elif msg_type == "response":
                        content = data.get('content', '')
                        if content:
                            print(f"   📝 Response: {str(content)[:100]}...")
                        else:
                            print(f"   📝 Response: (empty)")
                        metadata = data.get('metadata', {})
                        if metadata.get('status') == 'completed':
                            print("   🎉 WORKFLOW COMPLETED!")
                            break

                    elif msg_type == "error":
                        print(f"   ❌ ERROR: {data.get('message')}")
                        break

                except asyncio.TimeoutError:
                    print("\n⏱️  Timeout waiting for message")
                    break

            print(f"\n📊 Total messages: {message_count}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_approval())
