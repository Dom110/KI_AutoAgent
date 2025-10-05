#!/usr/bin/env python3
"""
WebSocket Test Client for KI AutoAgent Backend
Tests v5.8.2 improvements with TestApp2
"""

import asyncio
import websockets
import json
import sys

async def test_agent_workflow():
    """Test the complete agent workflow with TestApp2"""

    uri = "ws://localhost:8001/ws/chat"
    workspace_path = "/Users/dominikfoert/git/KI_AutoAgent/TestApp2"

    print("=" * 80)
    print("🧪 Testing KI AutoAgent v5.8.2 with TestApp2")
    print("=" * 80)

    async with websockets.connect(uri) as websocket:
        print(f"\n✅ Connected to {uri}")

        # Step 1: Receive connection message
        connection_msg = await websocket.recv()
        print(f"\n📨 Server: {connection_msg}")

        # Step 2: Send init message with workspace_path
        init_message = {
            "type": "init",
            "workspace_path": workspace_path
        }
        print(f"\n📤 Sending init: {json.dumps(init_message, indent=2)}")
        await websocket.send(json.dumps(init_message))

        # Receive init confirmation
        init_response = await websocket.recv()
        print(f"\n📨 Init response: {init_response}")

        # Step 3: Send analysis request
        analysis_request = {
            "type": "chat",
            "message": "Analyze the TestApp2 system infrastructure. Understand the code structure and generate architecture documentation.",
            "mode": "auto"
        }
        print(f"\n📤 Sending analysis request...")
        await websocket.send(json.dumps(analysis_request))

        print("\n" + "=" * 80)
        print("📊 AGENT RESPONSES:")
        print("=" * 80)

        # Step 4: Receive and display all responses
        response_count = 0
        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=120.0)
                response_data = json.loads(response)
                response_count += 1

                msg_type = response_data.get('type', 'unknown')

                if msg_type == 'agent_response':
                    agent = response_data.get('agent', 'unknown')
                    content = response_data.get('content', '')
                    print(f"\n🤖 {agent}:")
                    print(f"{content[:500]}..." if len(content) > 500 else content)

                elif msg_type == 'agent_progress':
                    agent = response_data.get('agent', 'unknown')
                    progress = response_data.get('content', '')
                    print(f"\n⏳ {agent}: {progress}")

                elif msg_type == 'workflow_complete':
                    print("\n✅ Workflow Complete!")
                    final_response = response_data.get('final_response', '')
                    print(f"\n📋 Final Response:")
                    print(final_response)
                    break

                elif msg_type == 'error':
                    error = response_data.get('error', 'Unknown error')
                    print(f"\n❌ Error: {error}")
                    break

                else:
                    print(f"\n📨 {msg_type}: {response_data}")

            except asyncio.TimeoutError:
                print("\n⏱️  Timeout waiting for response")
                break
            except websockets.exceptions.ConnectionClosed:
                print("\n🔌 Connection closed")
                break

        print(f"\n📊 Total responses: {response_count}")

        # Step 5: Check if ARCHITECTURE.md was created
        import os
        arch_file = os.path.join(workspace_path, "ARCHITECTURE.md")
        if os.path.exists(arch_file):
            print(f"\n✅ ARCHITECTURE.md created successfully!")
            with open(arch_file, 'r') as f:
                arch_content = f.read()
                print(f"\n📄 ARCHITECTURE.md Preview (first 1000 chars):")
                print("-" * 80)
                print(arch_content[:1000])
                print("-" * 80)
        else:
            print(f"\n⚠️  ARCHITECTURE.md not found at {arch_file}")

        print("\n" + "=" * 80)
        print("🏁 Test Complete!")
        print("=" * 80)

if __name__ == "__main__":
    try:
        asyncio.run(test_agent_workflow())
    except KeyboardInterrupt:
        print("\n\n⛔ Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
