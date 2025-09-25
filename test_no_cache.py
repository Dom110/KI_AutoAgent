#!/usr/bin/env python3
"""
Test indexing without cache to see all progress messages
"""

import asyncio
import json
import websockets
from datetime import datetime

async def test_no_cache():
    """Force fresh indexing by using unique message"""
    uri = "ws://localhost:8000/ws/chat"

    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to {uri}")

            # Use a unique message to bypass cache
            timestamp = datetime.now().isoformat()
            request = {
                "type": "chat",
                "agent": "architect",
                "message": f"Analyze system infrastructure and improvements. Timestamp: {timestamp}",
                "mode": "single",
                "stream": False,
                "workspace_path": "/Users/dominikfoert/git/KI_AutoAgent"
            }

            await websocket.send(json.dumps(request))
            print(f"📤 Sent: {request['message'][:50]}...")
            print("\n🔄 Monitoring progress (60 second timeout)...")
            print("-" * 80)

            start_time = asyncio.get_event_loop().time()
            phase_tracker = {}
            file_count = 0
            db_scan_seen = False

            while asyncio.get_event_loop().time() - start_time < 60:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    data = json.loads(response)

                    if data.get('type') == 'agent_progress':
                        content = data.get('content', '')
                        ts = datetime.now().strftime('%H:%M:%S')

                        # Track different stages
                        if 'Indexing file' in content:
                            file_count += 1
                            # Show milestones
                            if file_count in [1, 50, 100, 137]:
                                print(f"[{ts}] 📂 {content}")
                        elif 'Building dependency graph' in content:
                            print(f"[{ts}] 📊 {content}")
                            phase_tracker['dependency'] = True
                        elif 'Extracting API' in content:
                            print(f"[{ts}] 🔌 {content}")
                            phase_tracker['api'] = True
                        elif 'Identifying database' in content or 'Scanning for DB' in content:
                            print(f"[{ts}] 💾 {content}")
                            phase_tracker['db_start'] = True
                            db_scan_seen = True
                        elif 'DB operations' in content and '/' in content:
                            # Show DB scan progress
                            print(f"[{ts}] 💾 {content}")
                        elif 'Phase 1 complete' in content:
                            print(f"[{ts}] ✅ {content}")
                            phase_tracker['phase1_complete'] = True
                        elif 'Phase' in content:
                            print(f"[{ts}] 🎯 {content}")
                        elif 'Building' in content or 'Running' in content or 'Calculating' in content:
                            print(f"[{ts}] ⚡ {content}")

                    elif data.get('type') == 'agent_thinking':
                        print(f"\n🤔 Agent is thinking...")

                    elif data.get('type') == 'agent_response':
                        print(f"\n💬 Response received")
                        # Continue to catch any trailing progress messages

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"❌ Error: {e}")
                    break

            print("-" * 80)
            print("\n📊 ANALYSIS SUMMARY:")
            print(f"• Files indexed: {file_count}")
            print(f"• Dependency graph: {'✅' if phase_tracker.get('dependency') else '❌'}")
            print(f"• API extraction: {'✅' if phase_tracker.get('api') else '❌'}")
            print(f"• DB operations scan: {'✅ Started' if phase_tracker.get('db_start') else '❌ Not started'}")
            print(f"• Phase 1 complete: {'✅' if phase_tracker.get('phase1_complete') else '❌ Did not complete!'}")

            if not phase_tracker.get('phase1_complete'):
                print("\n⚠️ WARNING: Phase 1 did not complete successfully!")
                print("The process likely hung during DB operations scanning.")

    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    print("🚀 No-Cache Indexing Test")
    print("=" * 80)
    asyncio.run(test_no_cache())