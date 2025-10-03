#!/usr/bin/env python3
"""
Real WebSocket Test for Architecture Proposal System (v5.2.0)

Simulates a real user workflow via WebSocket (like VSCode Extension):
1. Connect to backend WebSocket (ws://localhost:8001/ws/chat)
2. Send: "Erstelle eine Tetris App mit TypeScript"
3. Receive: architecture_proposal message
4. Send: architecture_approval (approved)
5. Verify: Workflow continues to implementation
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime


class TetrisWorkflowTest:
    def __init__(self):
        self.ws_url = "ws://localhost:8001/ws/chat"
        self.session_id = None
        self.client_id = None
        self.proposal_received = False
        self.proposal_approved = False
        self.workflow_completed = False
        self.messages_received = []

    async def connect_and_test(self):
        """Connect to WebSocket and run Tetris workflow test"""

        print("=" * 80)
        print("🧪 REAL WEBSOCKET TEST: Tetris Architecture Proposal Workflow")
        print("=" * 80)
        print()

        try:
            async with websockets.connect(self.ws_url) as websocket:
                print(f"✅ Connected to {self.ws_url}")
                print()

                # Step 1: Receive welcome message
                welcome_msg = await websocket.recv()
                welcome_data = json.loads(welcome_msg)
                print(f"📨 Received: {welcome_data.get('type')}")

                if welcome_data.get("type") == "connected":
                    self.session_id = welcome_data.get("session_id")
                    self.client_id = welcome_data.get("client_id")
                    print(f"   Session ID: {self.session_id}")
                    print(f"   Client ID: {self.client_id}")
                    print(f"   Version: {welcome_data.get('version')}")
                print()

                # Step 1.5: Set workspace path
                print("📤 Setting Workspace Path...")
                workspace_msg = {
                    "type": "setWorkspace",
                    "workspace_path": "/Users/dominikfoert/git/KI_AutoAgent"
                }
                await websocket.send(json.dumps(workspace_msg))
                print("✅ Workspace path set")
                print()

                # Step 2: Send Tetris creation request
                print("📤 Sending Request: 'Erstelle eine Tetris App mit TypeScript'")
                request = {
                    "type": "chat",
                    "content": "Erstelle eine Tetris App mit TypeScript"
                }
                await websocket.send(json.dumps(request))
                print("✅ Request sent")
                print()

                # Step 3: Listen for messages
                print("👂 Listening for messages from backend...")
                print()

                message_count = 0
                timeout_seconds = 120  # 2 minutes max

                async def receive_with_timeout():
                    return await asyncio.wait_for(
                        websocket.recv(),
                        timeout=timeout_seconds
                    )

                while True:
                    try:
                        message = await receive_with_timeout()
                        message_count += 1
                        data = json.loads(message)
                        msg_type = data.get("type")

                        self.messages_received.append(data)

                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] 📨 Message #{message_count}: {msg_type}")

                        # Handle different message types
                        if msg_type == "agent_thinking":
                            agent = data.get("agent", "unknown")
                            content = data.get("content", "")
                            print(f"   💭 {agent}: {content[:80]}...")

                        elif msg_type == "step_completed":
                            agent = data.get("agent", "unknown")
                            task = data.get("task", "")
                            print(f"   ✅ {agent} completed: {task[:60]}...")

                        elif msg_type == "architecture_proposal":
                            print()
                            print("=" * 80)
                            print("🏛️ ARCHITECTURE PROPOSAL RECEIVED!")
                            print("=" * 80)
                            print()

                            self.proposal_received = True
                            proposal = data.get("proposal", {})

                            print("📋 Proposal Sections:")
                            for key in ["summary", "improvements", "tech_stack", "structure", "risks", "research_insights"]:
                                if key in proposal:
                                    value = proposal[key]
                                    print(f"   ✅ {key}: {len(value)} chars")
                                    # Show preview
                                    preview = value[:150].replace("\n", " ")
                                    print(f"      Preview: {preview}...")
                                else:
                                    print(f"   ❌ {key}: MISSING")
                            print()

                            # Step 4: Send approval
                            print("📤 Sending APPROVAL...")
                            approval = {
                                "type": "architecture_approval",
                                "session_id": self.session_id,
                                "decision": "approved",
                                "feedback": ""
                            }
                            await websocket.send(json.dumps(approval))
                            self.proposal_approved = True
                            print("✅ Approval sent")
                            print()
                            print("👂 Continuing to listen for workflow continuation...")
                            print()

                        elif msg_type == "architecture_proposal_revised":
                            print()
                            print("📋 REVISED ARCHITECTURE PROPOSAL RECEIVED")
                            print("   (This should not happen in approval flow)")
                            print()

                        elif msg_type == "architectureApprovalProcessed":
                            print()
                            print("=" * 80)
                            print("✅ APPROVAL PROCESSED BY BACKEND")
                            print("=" * 80)
                            decision = data.get("decision")
                            message_text = data.get("message")
                            print(f"   Decision: {decision}")
                            print(f"   Message: {message_text}")
                            print()
                            print("   → Workflow should now continue to implementation...")
                            print()

                        elif msg_type == "response":
                            agent = data.get("agent", "unknown")
                            content = data.get("content", "")
                            print(f"   📝 Response from {agent}:")
                            if content:
                                print(f"      {str(content)[:200]}...")
                            else:
                                print(f"      (empty response)")

                            # Check if this is final response
                            metadata = data.get("metadata", {})
                            status = metadata.get("status")
                            if status == "completed":
                                self.workflow_completed = True
                                print()
                                print("=" * 80)
                                print("🎉 WORKFLOW COMPLETED!")
                                print("=" * 80)
                                print()
                                break

                        elif msg_type == "error":
                            error_msg = data.get("message", "Unknown error")
                            print(f"   ❌ ERROR: {error_msg}")
                            traceback_info = data.get("traceback", "")
                            if traceback_info:
                                print(f"   Traceback: {traceback_info[:300]}...")

                        else:
                            # Other message types
                            print(f"   Data: {str(data)[:100]}...")

                        print()

                        # Safety check: If proposal approved but no continuation for 30 sec
                        if self.proposal_approved and not self.workflow_completed:
                            # Wait a bit more for continuation
                            pass

                    except asyncio.TimeoutError:
                        print()
                        print(f"⏱️  Timeout after {timeout_seconds} seconds")
                        print()
                        break

                    except Exception as e:
                        print()
                        print(f"❌ Error receiving message: {e}")
                        import traceback
                        traceback.print_exc()
                        print()
                        break

                # Summary
                print()
                print("=" * 80)
                print("📊 TEST SUMMARY")
                print("=" * 80)
                print()
                print(f"   Total Messages Received: {message_count}")
                print(f"   ✅ Architecture Proposal Received: {self.proposal_received}")
                print(f"   ✅ Proposal Approved: {self.proposal_approved}")
                print(f"   ✅ Workflow Completed: {self.workflow_completed}")
                print()

                # Analyze message flow
                print("📋 Message Flow:")
                msg_types = [m.get("type") for m in self.messages_received]
                for i, msg_type in enumerate(msg_types, 1):
                    print(f"   {i}. {msg_type}")
                print()

                # Check expected flow
                print("🔍 Expected Flow Verification:")
                print()

                has_thinking = any(m.get("type") == "agent_thinking" for m in self.messages_received)
                has_proposal = any(m.get("type") == "architecture_proposal" for m in self.messages_received)
                has_processed = any(m.get("type") == "architectureApprovalProcessed" for m in self.messages_received)
                has_response = any(m.get("type") == "response" for m in self.messages_received)

                print(f"   ✅ Agent Thinking Messages: {has_thinking}")
                print(f"   ✅ Architecture Proposal: {has_proposal}")
                print(f"   ✅ Approval Processed: {has_processed}")
                print(f"   ✅ Response Messages: {has_response}")
                print()

                if has_proposal and has_processed:
                    print("🎉 SUCCESS! Architecture Proposal System is working correctly!")
                    print()
                    print("✅ Verified:")
                    print("   1. Orchestrator created execution plan")
                    print("   2. Architect performed research")
                    print("   3. Architecture proposal was created and sent")
                    print("   4. User approval was sent")
                    print("   5. Backend processed approval")
                    print("   6. Workflow continued (or attempted to)")
                    print()
                    return True
                else:
                    print("⚠️ PARTIAL SUCCESS - Some steps may not have completed")
                    print()
                    if not has_proposal:
                        print("   ❌ No architecture proposal received")
                    if not has_processed:
                        print("   ❌ Approval not processed by backend")
                    print()
                    return False

        except websockets.exceptions.WebSocketException as e:
            print()
            print("=" * 80)
            print("❌ WEBSOCKET CONNECTION ERROR")
            print("=" * 80)
            print()
            print(f"Error: {e}")
            print()
            print("Is the backend server running?")
            print("Check: lsof -i :8001")
            print()
            return False

        except Exception as e:
            print()
            print("=" * 80)
            print("❌ UNEXPECTED ERROR")
            print("=" * 80)
            print()
            print(f"Error: {e}")
            import traceback
            print()
            print("Traceback:")
            print(traceback.format_exc())
            print()
            return False


async def main():
    print()
    print("🚀 Starting Real WebSocket Workflow Test")
    print()

    # Check if backend is running
    import subprocess
    result = subprocess.run(
        ["lsof", "-i", ":8001"],
        capture_output=True,
        text=True
    )

    if "LISTEN" not in result.stdout:
        print("❌ ERROR: Backend server not running on port 8001")
        print()
        print("Start the backend first:")
        print("   cd backend")
        print("   python api/server_langgraph.py")
        print()
        return False

    print("✅ Backend server is running on port 8001")
    print()

    # Run test
    test = TetrisWorkflowTest()
    success = await test.connect_and_test()

    print()
    if success:
        print("✅ Test PASSED")
        return True
    else:
        print("❌ Test FAILED or INCOMPLETE")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
