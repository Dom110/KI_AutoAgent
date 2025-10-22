#!/usr/bin/env python3
"""
Simple WebSocket test for v7.0 server

This tests basic connectivity and workflow execution.
"""

import asyncio
import json
import websockets
from pathlib import Path


async def test_simple_query():
    """Test a simple query through WebSocket."""

    uri = "ws://localhost:8002/ws/chat"

    print("="*60)
    print("V7.0 WEBSOCKET TEST")
    print("="*60)
    print(f"Connecting to: {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            # Receive connection message
            conn_msg = await websocket.recv()
            data = json.loads(conn_msg)
            print(f"\n✅ Connected!")
            print(f"   Version: {data.get('version')}")
            print(f"   Architecture: {data.get('architecture')}")
            print(f"   Session: {data.get('session_id')}")

            # Send init message
            workspace_path = str(Path.home() / "TestApps" / "v7_test")
            print(f"\n📤 Sending init with workspace: {workspace_path}")
            await websocket.send(json.dumps({
                "type": "init",
                "workspace_path": workspace_path
            }))

            # Receive init response
            init_msg = await websocket.recv()
            init_data = json.loads(init_msg)
            print(f"✅ Initialized!")
            print(f"   Agents available: {init_data.get('agents_available', [])}")

            # Send test query
            test_query = "Explain what is Python async/await in simple terms"
            print(f"\n📤 Sending query: {test_query}")
            await websocket.send(json.dumps({
                "type": "chat",
                "content": test_query
            }))

            # Receive responses
            print("\n📥 Receiving responses:")
            print("-"*40)

            message_count = 0
            max_messages = 50
            supervisor_decisions = 0
            agents_invoked = []

            while message_count < max_messages:
                try:
                    response = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=5.0
                    )
                    data = json.loads(response)
                    message_count += 1

                    msg_type = data.get("type")

                    if msg_type == "log":
                        log_msg = data.get("message", "")
                        if "SUPERVISOR" in log_msg:
                            supervisor_decisions += 1
                            print(f"🎯 Supervisor decision #{supervisor_decisions}")
                        elif any(agent in log_msg.upper() for agent in ["RESEARCH", "ARCHITECT", "CODESMITH", "REVIEWFIX", "RESPONDER", "HITL"]):
                            for agent in ["research", "architect", "codesmith", "reviewfix", "responder", "hitl"]:
                                if agent.upper() in log_msg.upper() and agent not in agents_invoked:
                                    agents_invoked.append(agent)
                                    print(f"   🚀 Agent invoked: {agent}")

                    elif msg_type == "supervisor_decision":
                        print(f"   Decision: Route to {data.get('next_agent')}")
                        print(f"   Confidence: {data.get('confidence', 0):.2f}")

                    elif msg_type == "agent_start":
                        print(f"   ▶️ {data.get('agent')} starting")

                    elif msg_type == "status":
                        print(f"   Status: {data.get('message')}")

                    elif msg_type == "result":
                        print("-"*40)
                        print("\n✅ WORKFLOW COMPLETE!")
                        print(f"\nResponse from Responder:")
                        content = data.get("content") or ""
                        print(content[:500] if content else "(No content)")  # First 500 chars

                        if data.get("workflow_state"):
                            state = data["workflow_state"]
                            print(f"\nWorkflow State:")
                            print(f"   Last agent: {state.get('last_agent')}")
                            print(f"   Response ready: {state.get('response_ready')}")
                            print(f"   Validation passed: {state.get('validation_passed')}")
                        break

                    elif msg_type == "error":
                        print(f"\n❌ ERROR: {data.get('message')}")
                        break

                except asyncio.TimeoutError:
                    if agents_invoked:  # Got some progress
                        print("\n⏱️ Timeout waiting for response")
                    break

            # Summary
            print("\n" + "="*60)
            print("TEST SUMMARY")
            print("="*60)
            print(f"Supervisor decisions: {supervisor_decisions}")
            print(f"Agents invoked: {', '.join(agents_invoked) if agents_invoked else 'None'}")
            print(f"Messages received: {message_count}")

            if agents_invoked and "responder" in agents_invoked:
                print("\n✅ TEST PASSED - Responder provided output")
            else:
                print("\n⚠️ TEST INCOMPLETE - Check server logs")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Starting v7.0 WebSocket test...")
    asyncio.run(test_simple_query())
    print("\nTest complete!")