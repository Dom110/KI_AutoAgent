#!/usr/bin/env python3
"""
Simple workflow test - just verify basic connection and workflow execution
"""
import asyncio
import websockets
import json
from datetime import datetime

async def test_workflow():
    uri = "ws://localhost:8001/ws/chat"

    def log(msg, emoji="📝"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {emoji} {msg}")

    try:
        log("Connecting to backend...", "🔌")
        async with websockets.connect(uri) as ws:
            log("Connected!", "✅")

            # Receive connection message
            msg = await ws.recv()
            data = json.loads(msg)
            session_id = data.get('session_id')
            log(f"Session: {session_id[:8]}...", "🔑")

            # Set workspace
            await ws.send(json.dumps({
                "type": "setWorkspace",
                "workspacePath": "/Users/dominikfoert/git/KI_AutoAgent"
            }))
            log("Workspace set", "📁")

            # Send simple task
            await ws.send(json.dumps({
                "type": "chat",
                "message": "Create a simple Python hello world function"
            }))
            log("Task sent: Create hello world function", "📤")

            # Listen for messages (timeout after 60 seconds)
            start_time = asyncio.get_event_loop().time()
            timeout = 60
            proposal_received = False
            workflow_completed = False

            while (asyncio.get_event_loop().time() - start_time) < timeout:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    data = json.loads(msg)
                    msg_type = data.get('type')

                    if msg_type == "agent_thinking":
                        agent = data.get('agent', 'unknown')
                        log(f"{agent} thinking...", "💭")

                    elif msg_type == "architecture_proposal":
                        proposal_received = True
                        log("ARCHITECTURE PROPOSAL RECEIVED!", "🏛️")
                        # Auto-approve
                        await ws.send(json.dumps({
                            "type": "architecture_approval",
                            "session_id": session_id,
                            "decision": "approved",
                            "feedback": "Approved for test"
                        }))
                        log("Approval sent", "✅")

                    elif msg_type == "architectureApprovalProcessed":
                        log("Approval processed - workflow continuing...", "🔄")

                    elif msg_type == "response":
                        metadata = data.get('metadata', {})
                        status = metadata.get('status')
                        agent = data.get('agent', 'unknown')
                        log(f"Response from {agent} (status: {status})", "📨")

                        if status == 'completed':
                            workflow_completed = True
                            log("WORKFLOW COMPLETED!", "🎉")
                            break

                    elif msg_type == "error":
                        log(f"ERROR: {data.get('message')}", "❌")
                        break

                except asyncio.TimeoutError:
                    log("No message received in 10s...", "⏱️")
                    continue

            # Summary
            print("\n" + "="*60)
            print("📊 TEST SUMMARY")
            print("="*60)
            print(f"Proposal received: {proposal_received}")
            print(f"Workflow completed: {workflow_completed}")

            if workflow_completed:
                print("\n✅ TEST PASSED")
            elif proposal_received:
                print("\n⚠️  TEST PARTIAL - Got proposal but workflow didn't complete")
            else:
                print("\n❌ TEST FAILED - No proposal received")
            print("="*60 + "\n")

    except Exception as e:
        log(f"Test error: {e}", "❌")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workflow())
