#!/usr/bin/env python3
"""
Test Client for v5.8.5 Hybrid Orchestrator - Calculator App
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime

# Test workspace
WORKSPACE = "/Users/dominikfoert/git/KI_AutoAgent/test_workspace_calculator_v585"

# Test task
TEST_TASK = "Create a simple Calculator app with React and TypeScript. It should support add, subtract, multiply, and divide operations."

async def create_test_app():
    """
    Connect to backend and create test app
    Monitor for hybrid orchestrator validation
    """
    uri = "ws://localhost:8001/ws/chat"

    print("\n" + "="*80)
    print("🧪 TEST: v5.8.5 Hybrid Orchestrator - Calculator App")
    print("="*80)
    print(f"\n📝 Task: {TEST_TASK}")
    print(f"📁 Workspace: {WORKSPACE}")
    print(f"🔗 Connecting to: {uri}")
    print("\n" + "-"*80)

    validation_events = []
    orchestrator_calls = 0
    architect_calls = 0
    codesmith_calls = 0

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
            print(f"✅ Session initialized: {init_data.get('session_id', 'N/A')[:8]}...\n")

            # Send chat message
            print(f"📤 Sending task request...\n")
            chat_msg = {
                "type": "chat",
                "content": TEST_TASK,
                "plan_first": True  # Enable plan-first mode
            }
            await websocket.send(json.dumps(chat_msg))

            # Monitor messages
            print("="*80)
            print("📊 WORKFLOW EXECUTION - Monitoring for Hybrid Orchestrator")
            print("="*80 + "\n")

            message_count = 0
            workflow_complete = False

            while not workflow_complete:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=120.0)
                    data = json.loads(message)
                    message_type = data.get("type")
                    message_count += 1

                    timestamp = datetime.now().strftime("%H:%M:%S")

                    # Track agent activities
                    if message_type == "agent_activity":
                        agent = data.get("agent", "unknown")
                        activity = data.get("activity_type", "unknown")
                        task_desc = data.get("task", "")[:60]

                        # Count orchestrator calls
                        if agent == "orchestrator":
                            orchestrator_calls += 1
                            print(f"\n[{timestamp}] 🎯 ORCHESTRATOR #{orchestrator_calls}")

                            # Check for validation mode
                            if "validat" in task_desc.lower() or "validat" in activity.lower():
                                validation_events.append({
                                    "timestamp": timestamp,
                                    "type": "orchestrator_validation",
                                    "task": task_desc
                                })
                                print(f"           🔍 VALIDATION MODE DETECTED")
                                print(f"           Task: {task_desc}")

                        elif agent == "architect":
                            architect_calls += 1
                            print(f"\n[{timestamp}] 🏗️  ARCHITECT #{architect_calls}")
                            print(f"           Activity: {activity}")
                            print(f"           Task: {task_desc}")

                        elif agent == "codesmith":
                            codesmith_calls += 1
                            print(f"\n[{timestamp}] 💻 CODESMITH #{codesmith_calls}")
                            print(f"           Activity: {activity}")
                            print(f"           Task: {task_desc}")

                        else:
                            print(f"[{timestamp}] {agent}: {activity}")

                    # Approval needed
                    elif message_type == "approval_needed":
                        approval_type = data.get("approval_type", "unknown")
                        print(f"\n[{timestamp}] ⏸️  APPROVAL NEEDED: {approval_type}")

                        # Auto-approve for testing
                        print(f"           ✅ Auto-approving...")
                        approve_msg = {
                            "type": "approval_response",
                            "approved": True,
                            "feedback": None
                        }
                        await websocket.send(json.dumps(approve_msg))

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
            print("📊 EXECUTION ANALYSIS")
            print("="*80)

            print(f"\n📈 Agent Call Counts:")
            print(f"  - Orchestrator: {orchestrator_calls} calls")
            print(f"  - Architect: {architect_calls} calls")
            print(f"  - CodeSmith: {codesmith_calls} calls")

            print(f"\n🔍 Hybrid Orchestrator Validation:")
            print(f"  - Validation events detected: {len(validation_events)}")

            if validation_events:
                print(f"\n  Validation Events:")
                for i, event in enumerate(validation_events, 1):
                    print(f"    {i}. [{event['timestamp']}] {event['task']}")
            else:
                print(f"  ⚠️  NO VALIDATION EVENTS DETECTED!")
                print(f"  Expected: Orchestrator should validate architecture after Architect")

            # Expected behavior for v5.8.5
            print(f"\n📋 Expected v5.8.5 Behavior:")
            print(f"  ✅ Orchestrator call 1: Initial planning")
            print(f"  ✅ Architect call 1: Create architecture")
            print(f"  🔍 Orchestrator call 2: Validate architecture ← HYBRID PATTERN")
            print(f"  ✅ CodeSmith call 1: Implement (if validation passed)")

            print(f"\n🎯 Actual Behavior:")
            if orchestrator_calls >= 2:
                print(f"  ✅ Orchestrator called {orchestrator_calls}x (includes validation)")
            else:
                print(f"  ❌ Orchestrator only called {orchestrator_calls}x (expected ≥2)")

            if len(validation_events) > 0:
                print(f"  ✅ Validation detected: {len(validation_events)} event(s)")
            else:
                print(f"  ❌ No validation detected (Hybrid pattern may not be working)")

            return {
                "orchestrator_calls": orchestrator_calls,
                "architect_calls": architect_calls,
                "codesmith_calls": codesmith_calls,
                "validation_events": validation_events,
                "message_count": message_count
            }

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Run test"""
    print("\n" + "="*80)
    print("🚀 V5.8.5 HYBRID ORCHESTRATOR TEST - Calculator App")
    print("="*80)

    # Create test workspace
    import os
    os.makedirs(WORKSPACE, exist_ok=True)
    print(f"✅ Test workspace created: {WORKSPACE}")

    # Run test
    result = await create_test_app()

    if result:
        print("\n" + "="*80)
        print("✅ TEST COMPLETE")
        print("="*80)
        print(f"\nCheck logs for detailed validation messages:")
        print(f"  tail -f ~/.ki_autoagent/logs/backend.log | grep -i 'validat\\|hybrid'")
        return 0
    else:
        print("\n❌ TEST FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
