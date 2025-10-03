#!/usr/bin/env python3
"""
Test: Analysiere welche Agents im aktuellen Workflow aktiviert werden
Prüft: Research, Architect (Architecture Doc), Reviewer (Architecture Validation)
"""

import asyncio
import websockets
import json
from datetime import datetime
import time

async def test_workflow():
    ws_url = "ws://localhost:8001/ws/chat"

    print("🔍 WORKFLOW ANALYSIS TEST")
    print("=" * 70)
    print("Testing: Calculator App Creation")
    print("Checking for: Research → Architect Doc → Reviewer Validation")
    print("=" * 70)

    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ Connected to Backend\n")

            # Welcome message
            await websocket.recv()

            # Send request with explicit output directory
            session_id = f"workflow_test_{datetime.now().strftime('%H%M%S')}"
            message = {
                "type": "chat",
                "content": "Create a simple calculator web app with basic operations (+, -, *, /). Save it in agent_projects/calculator/",
                "session_id": session_id
            }

            print("📤 Sending Calculator App Request...")
            print(f"   Session ID: {session_id}\n")
            await websocket.send(json.dumps(message))

            # Tracking variables
            agents_activated = []
            research_called = False
            architect_created_doc = False
            reviewer_validated_arch = False
            workflow_completed = False

            # Timeout: 5 minutes
            timeout = 300
            start_time = time.time()

            print("🤖 AGENT ACTIVITY LOG:")
            print("-" * 70)

            while time.time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(response)

                    # Track agent activation
                    if 'agent' in data:
                        agent = data['agent']
                        if agent not in agents_activated:
                            agents_activated.append(agent)
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            print(f"[{timestamp}] ✅ {agent.upper()} activated")

                            # Check for Research agent
                            if agent == 'research':
                                research_called = True
                                print(f"           → Research Agent CALLED ✅")

                    # Check message content for clues
                    if 'content' in data and data.get('content'):
                        content = str(data.get('content', '')).lower()

                        # Check for architecture document creation
                        if 'architecture' in content and any(word in content for word in ['document', 'design', 'created', 'spec']):
                            if not architect_created_doc:
                                architect_created_doc = True
                                timestamp = datetime.now().strftime('%H:%M:%S')
                                print(f"[{timestamp}] 📐 Architecture Document detected")

                        # Check for architecture validation
                        if 'architecture' in content and any(word in content for word in ['validation', 'compliance', 'review', 'validated']):
                            if not reviewer_validated_arch:
                                reviewer_validated_arch = True
                                timestamp = datetime.now().strftime('%H:%M:%S')
                                print(f"[{timestamp}] 🔍 Architecture Validation detected")

                        # Check for research results
                        if 'research' in content and any(word in content for word in ['results', 'findings', 'best practices']):
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            print(f"[{timestamp}] 🔬 Research Results detected")

                    # Check for workflow completion
                    if data.get('type') == 'workflow_completed' or 'workflow_completed' in str(data):
                        workflow_completed = True
                        print(f"\n{'='*70}")
                        print(f"✅ Workflow completed after {time.time() - start_time:.1f}s")
                        break

                except asyncio.TimeoutError:
                    # No message received, continue waiting
                    continue
                except json.JSONDecodeError:
                    continue

            print("\n" + "=" * 70)
            print("📊 WORKFLOW ANALYSIS RESULTS")
            print("=" * 70)

            print(f"\n🤖 Agents Activated ({len(agents_activated)}):")
            for i, agent in enumerate(agents_activated, 1):
                print(f"   {i}. {agent}")

            print(f"\n🔍 Feature Detection:")
            print(f"   ✅ Research Agent Called:           {'YES ✅' if research_called else 'NO ❌'}")
            print(f"   ✅ Architect Created Document:      {'YES ✅' if architect_created_doc else 'NO ❌'}")
            print(f"   ✅ Reviewer Validated Architecture: {'YES ✅' if reviewer_validated_arch else 'NO ❌'}")
            print(f"   ✅ Workflow Completed:              {'YES ✅' if workflow_completed else 'NO ❌'}")

            print(f"\n📋 Expected vs. Actual:")
            print(f"   Expected: orchestrator → research → architect → codesmith → reviewer → fixer")
            print(f"   Actual:   {' → '.join(agents_activated)}")

            # Conclusion
            print(f"\n🎯 CONCLUSION:")
            if research_called and architect_created_doc and reviewer_validated_arch:
                print("   ✅ FULL WORKFLOW IMPLEMENTED - All features present!")
            elif research_called:
                print("   ⚠️  PARTIAL - Research works, but architecture doc/validation missing")
            else:
                print("   ❌ NOT IMPLEMENTED - Research, Architecture Doc, Validation missing")
                print("   💡 This confirms the planned features are NOT YET implemented")

            print("=" * 70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workflow())
