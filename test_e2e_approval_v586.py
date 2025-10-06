#!/usr/bin/env python3
"""
v5.8.6 End-to-End Test: Hybrid Orchestrator + Approval Flow
Tests complete workflow including validation and approval
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime

# Test workspace
WORKSPACE = "/Users/dominikfoert/git/KI_AutoAgent/test_workspace_e2e_v586"

# Test task
TEST_TASK = "Create a simple Calculator app with React and TypeScript. It should support add, subtract, multiply, and divide operations."

async def test_e2e_approval():
    """
    End-to-end test with complete approval flow
    """
    uri = "ws://localhost:8001/ws/chat"

    print("\n" + "="*80)
    print("🧪 v5.8.6 E2E TEST: Hybrid Orchestrator + Approval Flow")
    print("="*80)
    print(f"\n📝 Task: {TEST_TASK}")
    print(f"📁 Workspace: {WORKSPACE}")
    print(f"🔗 Connecting to: {uri}")
    print("\n" + "-"*80)

    # Track events
    agent_activities = []
    orchestrator_count = 0
    architect_count = 0
    validation_detected = False
    proposal_received = False
    approval_sent = False
    workflow_complete = False

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to backend\n")

            # Wait for connected message
            connected_msg = await websocket.recv()
            print(f"📨 Received: {json.loads(connected_msg)['type']}")

            # Send init
            init_msg = {
                "type": "init",
                "workspace_path": WORKSPACE
            }
            await websocket.send(json.dumps(init_msg))
            print(f"📤 Sent init message")

            # Wait for initialized
            init_response = await websocket.recv()
            init_data = json.loads(init_response)
            session_id = init_data.get('session_id', 'N/A')
            print(f"✅ Session initialized: {session_id[:8]}...\n")

            # Send chat message
            print(f"📤 Sending task request...\n")
            chat_msg = {
                "type": "chat",
                "content": TEST_TASK,
                "plan_first": True
            }
            await websocket.send(json.dumps(chat_msg))

            # Monitor messages
            print("="*80)
            print("📊 WORKFLOW EXECUTION - Monitoring All Events")
            print("="*80 + "\n")

            message_count = 0

            while not workflow_complete:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=180.0)
                    data = json.loads(message)
                    message_type = data.get("type")
                    message_count += 1

                    timestamp = datetime.now().strftime("%H:%M:%S")

                    # Track ALL agent activity types (agent_thinking, agent_complete, etc.)
                    if message_type and message_type.startswith("agent_"):
                        agent = data.get("agent", "unknown")
                        content = data.get("content", "")
                        activity_type = message_type.replace("agent_", "")

                        agent_activities.append({
                            "timestamp": timestamp,
                            "agent": agent,
                            "activity": activity_type,
                            "content": content
                        })

                        # Count by agent
                        if agent == "orchestrator":
                            orchestrator_count += 1
                            print(f"\n[{timestamp}] 🎯 ORCHESTRATOR #{orchestrator_count}")
                            print(f"           Activity: {activity_type}")
                            print(f"           Content: {content[:80]}...")

                            # Detect validation
                            if "validat" in content.lower():
                                validation_detected = True
                                print(f"           🔍 VALIDATION DETECTED!")

                        elif agent == "architect":
                            architect_count += 1
                            print(f"\n[{timestamp}] 🏗️  ARCHITECT #{architect_count}")
                            print(f"           Activity: {activity_type}")
                            print(f"           Content: {content[:80]}...")

                        else:
                            print(f"[{timestamp}] {agent}: {activity_type} - {content[:60]}")

                    # Architecture proposal
                    elif message_type == "architecture_proposal":
                        proposal_received = True
                        print(f"\n[{timestamp}] 🏛️  ARCHITECTURE PROPOSAL RECEIVED")
                        print(f"           ⏸️  Workflow waiting for approval...")

                        # Auto-approve for testing
                        print(f"           ✅ Auto-approving...")
                        approve_msg = {
                            "type": "approval_response",
                            "approved": True,
                            "feedback": None
                        }
                        await websocket.send(json.dumps(approve_msg))
                        approval_sent = True
                        print(f"           📤 Approval sent")

                    # Progress updates
                    elif message_type == "progress":
                        step = data.get("current_step", 0)
                        total = data.get("total_steps", 0)
                        agent = data.get("agent", "")
                        print(f"[{timestamp}] 📊 Progress: {step}/{total} ({agent})")

                    # Workflow complete
                    elif message_type == "workflow_complete":
                        print(f"\n[{timestamp}] ✅ WORKFLOW COMPLETE")
                        workflow_complete = True

                    # Errors
                    elif message_type == "error":
                        error_msg = data.get("message", "Unknown error")
                        print(f"\n[{timestamp}] ❌ ERROR: {error_msg}")

                except asyncio.TimeoutError:
                    print("\n⏱️  Timeout waiting for messages")
                    break
                except websockets.exceptions.ConnectionClosed:
                    print("\n🔌 Connection closed")
                    break

            # Analysis
            print("\n" + "="*80)
            print("📊 E2E TEST RESULTS")
            print("="*80)

            print(f"\n📈 Message Statistics:")
            print(f"  - Total messages: {message_count}")
            print(f"  - Agent activities: {len(agent_activities)}")
            print(f"  - Orchestrator calls: {orchestrator_count}")
            print(f"  - Architect calls: {architect_count}")

            print(f"\n🔍 Hybrid Orchestrator Validation:")
            if validation_detected:
                print(f"  ✅ Validation detected in orchestrator messages")
            else:
                print(f"  ❌ No validation detected")

            print(f"\n📋 Approval Flow:")
            if proposal_received:
                print(f"  ✅ Architecture proposal received")
            else:
                print(f"  ❌ No architecture proposal received")

            if approval_sent:
                print(f"  ✅ Approval response sent")
            else:
                print(f"  ❌ No approval sent")

            print(f"\n🎯 Workflow Completion:")
            if workflow_complete:
                print(f"  ✅ Workflow completed successfully")
            else:
                print(f"  ❌ Workflow did not complete")

            # Detailed activity log
            if agent_activities:
                print(f"\n📜 Agent Activity Timeline:")
                for i, activity in enumerate(agent_activities[:15], 1):  # First 15
                    print(f"  {i}. [{activity['timestamp']}] {activity['agent']}: {activity['activity']}")
                    print(f"     → {activity['content'][:70]}...")

            # Overall verdict
            print(f"\n" + "="*80)
            print(f"🎯 FINAL VERDICT:")
            all_checks_passed = (
                validation_detected and
                proposal_received and
                approval_sent and
                orchestrator_count >= 2 and  # At least planning + validation
                architect_count >= 1
            )

            if all_checks_passed:
                print(f"  ✅ ALL CHECKS PASSED - v5.8.6 Working Correctly!")
                return 0
            else:
                print(f"  ❌ SOME CHECKS FAILED - Review Results Above")
                if not validation_detected:
                    print(f"     - Validation not detected")
                if not proposal_received:
                    print(f"     - Proposal not received")
                if orchestrator_count < 2:
                    print(f"     - Orchestrator only called {orchestrator_count}x (expected ≥2)")
                return 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


async def main():
    """Run E2E test"""
    import os
    os.makedirs(WORKSPACE, exist_ok=True)
    print(f"✅ Test workspace ready: {WORKSPACE}\n")

    exit_code = await test_e2e_approval()
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
