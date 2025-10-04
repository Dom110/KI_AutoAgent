#!/usr/bin/env python3
"""
Test: Dashboard App Creation via WebSocket
Tests the new v5.8.2 Generic CodeSmith Agent
"""

import asyncio
import json
import websockets
from datetime import datetime

async def test_dashboard_creation():
    """Send Dashboard App creation request to backend"""

    uri = "ws://localhost:8001/ws/chat"
    workspace_path = "/Users/dominikfoert/TestApp"

    print("━" * 80)
    print("🚀 Testing Dashboard App Creation - v5.8.2 Generic CodeSmith")
    print("━" * 80)
    print(f"📡 Connecting to: {uri}")
    print(f"📂 Workspace: {workspace_path}")
    print()

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected!")

            # 1. Receive welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"📨 Welcome: {welcome_data.get('type')}")

            # 2. Send init message with workspace
            init_message = {
                "type": "init",
                "workspace_path": workspace_path
            }
            await websocket.send(json.dumps(init_message))
            print(f"📤 Sent init with workspace: {workspace_path}")

            # 3. Wait for init confirmation
            init_response = await websocket.recv()
            init_data = json.loads(init_response)
            print(f"✅ Initialized: {init_data.get('type')}")

            if init_data.get('type') == 'initialized':
                session_id = init_data.get('session_id')
                print(f"🎫 Session ID: {session_id}")

            # 4. Send the actual request
            request_message = {
                "type": "chat",
                "content": "Create a Dashboard App with React and Chart.js"
            }

            print()
            print("━" * 80)
            print("📨 SENDING REQUEST:")
            print("   Create a Dashboard App with React and Chart.js")
            print("━" * 80)
            print()

            start_time = datetime.now()
            await websocket.send(json.dumps(request_message))

            # 5. Receive all responses
            message_count = 0
            agent_responses = []

            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=180.0)
                    data = json.loads(response)
                    message_count += 1

                    msg_type = data.get('type')

                    if msg_type == 'agent_thinking':
                        agent = data.get('agent', 'unknown')
                        thinking = data.get('thinking', '')
                        print(f"🤔 {agent}: {thinking[:100]}...")

                    elif msg_type == 'agent_activity':
                        agent = data.get('agent', 'unknown')
                        activity = data.get('activity', {})
                        status = activity.get('status', '')
                        step = activity.get('current_step', '')
                        print(f"🔄 {agent}: {status} - {step}")

                    elif msg_type == 'agent_tool_use':
                        agent = data.get('agent', 'unknown')
                        tool = data.get('tool_name', '')
                        print(f"🔧 {agent}: Using tool '{tool}'")

                    elif msg_type == 'agent_response':
                        agent = data.get('agent', 'unknown')
                        content = data.get('content', '')
                        print()
                        print(f"✅ {agent} Response:")
                        print(f"   {content[:200]}...")
                        agent_responses.append({
                            'agent': agent,
                            'content': content
                        })

                    elif msg_type == 'architecture_proposal':
                        print()
                        print("━" * 80)
                        print("⏸️  ARCHITECTURE PROPOSAL (Approval Required)")
                        print("━" * 80)
                        agent = data.get('agent', 'unknown')
                        content = data.get('content', '')
                        proposal = data.get('proposal', {})
                        proposal_session_id = data.get('session_id')
                        print(f"From: {agent}")
                        print(f"Content: {content[:300]}...")
                        print(f"Proposal: {str(proposal)[:200]}...")
                        print(f"Session ID: {proposal_session_id}")
                        print()

                        # Auto-approve for test
                        approval = {
                            "type": "architecture_approval",
                            "session_id": proposal_session_id,
                            "decision": "approved",
                            "feedback": "Test: Auto-approved"
                        }
                        await websocket.send(json.dumps(approval))
                        print("✅ AUTO-APPROVED (test mode)")
                        print()

                    elif msg_type == 'workflow_complete':
                        print()
                        print("━" * 80)
                        print("🎉 WORKFLOW COMPLETE!")
                        print("━" * 80)
                        result = data.get('result', {})
                        print(f"Status: {result.get('status')}")
                        print(f"Content: {result.get('content', '')[:300]}...")

                        if result.get('metadata'):
                            metadata = result['metadata']
                            print()
                            print("📊 Metadata:")
                            print(f"   Project Type: {metadata.get('project_type')}")
                            print(f"   Framework: {metadata.get('framework')}")
                            print(f"   Language: {metadata.get('language')}")
                            print(f"   Files Created: {len(metadata.get('files_created', []))}")
                            print(f"   Files Failed: {len(metadata.get('files_failed', []))}")

                        break

                    elif msg_type == 'error':
                        print()
                        print(f"❌ ERROR: {data.get('message', '')}")
                        break

                except asyncio.TimeoutError:
                    print()
                    print("⏱️  Timeout waiting for response")
                    break

            elapsed = (datetime.now() - start_time).total_seconds()

            print()
            print("━" * 80)
            print("📊 TEST SUMMARY")
            print("━" * 80)
            print(f"⏱️  Duration: {elapsed:.2f}s")
            print(f"📨 Messages received: {message_count}")
            print(f"🤖 Agent responses: {len(agent_responses)}")
            print()

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_dashboard_creation())
