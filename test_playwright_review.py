#!/usr/bin/env python3
"""
Test: Validiert ob ReviewerGPT tatsächlich Playwright Browser-Testing ausführt
v5.5.3 - Mit verlängertem Timeout und Playwright-Validierung
"""

import asyncio
import websockets
import json
from datetime import datetime
import os
import time

async def test_playwright_review():
    ws_url = "ws://localhost:8001/ws/chat"

    print("🎬 PLAYWRIGHT REVIEW TEST - v5.5.3")
    print("=" * 70)

    # Clean up old test file
    test_file = "whiteboard.html"
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"🗑️  Removed old {test_file}")

    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ Connected to Backend v5.5.3\n")

            # Welcome message
            await websocket.recv()

            # Send request
            session_id = f"playwright_test_{datetime.now().strftime('%H%M%S')}"
            message = {
                "type": "chat",
                "content": "Erstelle eine komplexe Whiteboard Web-App mit Canvas zum Zeichnen, Farbauswahl, Pinselgrößen, Undo/Redo und Export als PNG",
                "session_id": session_id
            }

            print("📤 Sending Whiteboard App Request...")
            print(f"   Session ID: {session_id}\n")
            await websocket.send(json.dumps(message))

            # Tracking variables
            agents_active = set()
            workflow_completed = False
            codesmith_done = False
            reviewer_started = False
            playwright_detected = False
            html_file_created = False

            # Extended timeout for full pipeline
            timeout = 300  # 5 minutes
            start_time = time.time()

            print("🤖 AGENT ACTIVITY LOG:")
            print("-" * 70)

            while time.time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(response)

                    # Track active agent
                    if 'agent' in data:
                        agent = data['agent']
                        if agent not in agents_active:
                            agents_active.add(agent)
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            print(f"[{timestamp}] ✅ {agent.upper()} activated")

                    # Handle architecture proposal
                    if data.get('type') == 'architecture_proposal':
                        print(f"\n📋 Architecture Proposal received - Auto-approving...")
                        approval = {
                            "type": "architecture_approval",
                            "session_id": session_id,
                            "decision": "approved"
                        }
                        await websocket.send(json.dumps(approval))
                        print("   ✅ Approved!\n")

                    # Detect CodeSmith completion
                    content = str(data).lower()
                    if 'codesmith' in content and ('created file' in content or 'successfully' in content):
                        if not codesmith_done:
                            codesmith_done = True
                            print(f"\n💻 CodeSmith completed - checking for HTML file...")
                            # Give file system time to sync
                            await asyncio.sleep(1)
                            if os.path.exists(test_file):
                                file_size = os.path.getsize(test_file)
                                html_file_created = True
                                print(f"   ✅ {test_file} created ({file_size} bytes)\n")

                    # Detect Reviewer start
                    if 'reviewer' in content and not reviewer_started:
                        reviewer_started = True
                        print(f"\n🔍 Reviewer activated - looking for Playwright execution...")

                    # Detect Playwright execution
                    if 'playwright' in content or 'browser' in content:
                        if 'test' in content or 'detected' in content:
                            playwright_detected = True
                            print(f"   🎭 PLAYWRIGHT DETECTED in message!")

                    # Detect workflow completion
                    if data.get('type') == 'workflow_completed' or data.get('status') == 'completed':
                        workflow_completed = True
                        print(f"\n✅ Workflow completed!")
                        break

                    # Error handling
                    if data.get('type') == 'error':
                        print(f"\n❌ ERROR: {data.get('message')}")

                except asyncio.TimeoutError:
                    # Print progress indicator every 2 seconds
                    elapsed = int(time.time() - start_time)
                    if elapsed % 10 == 0:  # Every 10 seconds
                        print(f"⏳ Waiting... ({elapsed}s elapsed, {len(agents_active)} agents active)")
                except Exception as e:
                    print(f"⚠️ Message handling error: {e}")

            # Final analysis
            print("\n" + "=" * 70)
            print("📊 TEST RESULTS:")
            print("-" * 70)

            print(f"\n🤖 Agents Activated: {len(agents_active)}")
            for agent in sorted(agents_active):
                print(f"   ✅ {agent}")

            print(f"\n📝 Pipeline Status:")
            print(f"   CodeSmith completed: {'✅' if codesmith_done else '❌'}")
            print(f"   HTML file created: {'✅' if html_file_created else '❌'}")
            print(f"   Reviewer started: {'✅' if reviewer_started else '❌'}")
            print(f"   Playwright detected: {'✅' if playwright_detected else '❌'}")
            print(f"   Workflow completed: {'✅' if workflow_completed else '❌ (timeout)'}")

            # Check file details if created
            if html_file_created:
                file_size = os.path.getsize(test_file)
                with open(test_file, 'r') as f:
                    lines = len(f.readlines())
                print(f"\n📄 {test_file} Details:")
                print(f"   Size: {file_size} bytes")
                print(f"   Lines: {lines}")

            # Success criteria
            print(f"\n🎯 SUCCESS CRITERIA:")

            criteria = {
                "Multi-agent execution": len(agents_active) >= 4,
                "CodeSmith generated file": html_file_created,
                "Reviewer activated": reviewer_started,
                "Playwright testing": playwright_detected
            }

            all_passed = all(criteria.values())

            for criterion, passed in criteria.items():
                icon = "✅" if passed else "❌"
                print(f"   {icon} {criterion}")

            print("\n" + "=" * 70)
            if all_passed:
                print("🎉 ALL TESTS PASSED - Playwright Review System Working!")
            else:
                print("⚠️  PARTIAL SUCCESS - Some criteria not met")
                print("\nℹ️  Note: Playwright detection requires:")
                print("   1. HTML file generated by CodeSmith")
                print("   2. Metadata passed to Reviewer")
                print("   3. Reviewer detects HTML and triggers browser test")

            return all_passed

    except Exception as e:
        print(f"\n❌ Connection Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n⏳ Starting test in 2 seconds...\n")
    time.sleep(2)

    success = asyncio.run(test_playwright_review())

    print("\n" + "=" * 70)
    if success:
        print("✅ PLAYWRIGHT REVIEW SYSTEM FULLY FUNCTIONAL")
    else:
        print("⚠️  CHECK SERVER LOGS FOR DETAILS")
    print("=" * 70)
