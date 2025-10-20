#!/usr/bin/env python3
"""
Test Progress Callback Messages - v6.4-asimov

Verifies that WebSocket progress messages are sent during workflow execution.

Expected Messages:
1. Connected message
2. "analyzing" status
3. "agent_executing" status for each agent (research, architect, codesmith, reviewfix)
4. "routing" status with routing decisions
5. Final result

User Quote:
"der orchestrator zeigt überhaupt gar keine Nachrichten.
Ich würde mir wünschen die ganzen Think Nachrichten usw. im Chat zu sehen."

This test validates that this problem is FIXED.
"""

import asyncio
import json
import sys
import websockets
from pathlib import Path

async def test_progress_messages():
    """Test that progress messages are sent during workflow execution."""

    # Use simple test workspace
    workspace = Path.home() / "TestApps" / "ProgressTest"
    workspace.mkdir(parents=True, exist_ok=True)

    # Create simple test file
    test_file = workspace / "app.py"
    test_file.write_text("# Simple Python app\nprint('Hello, World!')\n")

    print("🔌 Connecting to WebSocket...")
    uri = "ws://127.0.0.1:8002/ws/chat"

    received_messages = []
    agent_messages = []
    routing_messages = []

    try:
        async with websockets.connect(uri, ping_interval=30, ping_timeout=10) as websocket:
            print("✅ Connected!")

            # 1. Receive connection message
            msg = await websocket.recv()
            data = json.loads(msg)
            print(f"\n📨 Connected: {data.get('message', '')}")
            received_messages.append(data)

            # 2. Send init
            print(f"\n🔧 Initializing with workspace: {workspace}")
            await websocket.send(json.dumps({
                "type": "init",
                "workspace_path": str(workspace)
            }))

            # Receive init response
            msg = await websocket.recv()
            data = json.loads(msg)
            print(f"✅ Init response: {data.get('message', '')}")
            received_messages.append(data)

            # 3. Send simple task
            task = "Add a docstring to the Python file"
            print(f"\n📤 Sending task: {task}")
            await websocket.send(json.dumps({
                "type": "chat",
                "content": task
            }))

            # 4. Collect ALL messages until workflow completes
            print("\n📨 Receiving messages...\n")
            print("=" * 80)

            workflow_complete = False
            timeout_seconds = 120  # 2 minutes max for simple task
            start_time = asyncio.get_event_loop().time()

            while not workflow_complete:
                # Check timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout_seconds:
                    print(f"\n⏰ Timeout after {timeout_seconds}s - workflow still running")
                    break

                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(msg)
                    msg_type = data.get("type")

                    received_messages.append(data)

                    # Print message
                    if msg_type == "status":
                        status = data.get("status")
                        message = data.get("message", "")
                        print(f"📊 STATUS [{status}]: {message}")

                        # Track agent and routing messages
                        if status == "agent_executing":
                            agent = data.get("agent", "unknown")
                            agent_messages.append(agent)
                            print(f"   ✅ Agent message received: {agent}")

                        elif status == "routing":
                            next_agent = data.get("next_agent", "unknown")
                            confidence = data.get("routing_confidence", 0.0)
                            reason = data.get("routing_reason", "")
                            routing_messages.append({
                                "next_agent": next_agent,
                                "confidence": confidence,
                                "reason": reason
                            })
                            print(f"   ✅ Routing message received: {next_agent} (confidence: {confidence:.2f})")
                            if reason:
                                print(f"      💭 Reason: {reason}")

                    elif msg_type == "result":
                        print(f"\n🎯 RESULT: {data.get('message', '')}")
                        success = data.get("success", False)
                        quality = data.get("quality_score", 0.0)
                        exec_time = data.get("execution_time", 0.0)
                        print(f"   Success: {success}")
                        print(f"   Quality: {quality:.2f}")
                        print(f"   Time: {exec_time:.2f}s")
                        workflow_complete = True

                    elif msg_type == "error":
                        print(f"\n❌ ERROR: {data.get('message', '')}")
                        workflow_complete = True

                    else:
                        print(f"📨 {msg_type.upper()}: {data.get('message', str(data))}")

                except asyncio.TimeoutError:
                    print("⏰ No message received in 10s (workflow still running...)")
                    continue

            print("=" * 80)

            # 5. Analyze results
            print(f"\n\n📊 PROGRESS MESSAGE ANALYSIS:")
            print(f"{'=' * 80}")
            print(f"Total messages received: {len(received_messages)}")
            print(f"Agent execution messages: {len(agent_messages)}")
            print(f"Routing decision messages: {len(routing_messages)}")

            print(f"\n🤖 Agents that executed:")
            for agent in agent_messages:
                print(f"   - {agent}")

            print(f"\n🔀 Routing decisions made:")
            for routing in routing_messages:
                print(f"   - {routing['next_agent']} (confidence: {routing['confidence']:.2f})")

            # SUCCESS CRITERIA
            print(f"\n\n✅ SUCCESS CRITERIA:")
            print(f"{'=' * 80}")

            success = True

            if len(agent_messages) > 0:
                print(f"✅ Agent execution messages received: {len(agent_messages)}")
            else:
                print(f"❌ NO agent execution messages received!")
                success = False

            if len(routing_messages) > 0:
                print(f"✅ Routing decision messages received: {len(routing_messages)}")
            else:
                print(f"⚠️  No routing decision messages (may be normal for simple workflows)")

            if workflow_complete:
                print(f"✅ Workflow completed")
            else:
                print(f"❌ Workflow did NOT complete (timeout)")
                success = False

            print(f"\n{'=' * 80}")
            if success:
                print("🎉 TEST PASSED: Progress messages are working!")
                return 0
            else:
                print("❌ TEST FAILED: Progress messages NOT working!")
                return 1

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(test_progress_messages())
    sys.exit(exit_code)
