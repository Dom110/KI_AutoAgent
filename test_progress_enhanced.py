#!/usr/bin/env python3
"""
Test enhanced progress messages with detailed file-by-file updates
"""

import asyncio
import json
import websockets
from datetime import datetime

async def test_infrastructure_progress():
    """Test infrastructure analysis with detailed progress"""
    uri = "ws://localhost:8000/ws/chat"
    progress_messages = []

    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to {uri}")

            # Send infrastructure analysis request that triggers all phases
            request = {
                "type": "chat",
                "agent": "auto",
                "message": "Was kann an der Infrastruktur des Systems verbessert werden?",
                "mode": "auto",
                "stream": False,
                "workspace_path": "/Users/dominikfoert/git/KI_AutoAgent"
            }

            await websocket.send(json.dumps(request))
            print(f"📤 Sent: {request['message'][:50]}...")
            print("\n🔄 Collecting progress messages (30 second timeout)...")
            print("-" * 80)

            # Receive messages for 30 seconds
            start_time = asyncio.get_event_loop().time()
            last_phase = None
            phase_counts = {}

            while asyncio.get_event_loop().time() - start_time < 30:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    data = json.loads(response)

                    # Focus on progress messages
                    msg_type = data.get('type', 'unknown')

                    if msg_type == 'agent_progress':
                        content = data.get('content', data.get('message', ''))
                        agent = data.get('agent', 'unknown')
                        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                        progress_messages.append(content)

                        # Detect phase changes
                        if 'Phase' in content:
                            # Extract phase info
                            if 'Phase 1' in content:
                                current_phase = 'Phase 1: Indexing'
                            elif 'Phase 2' in content:
                                current_phase = 'Phase 2: Cross-references'
                            elif 'Phase 3' in content:
                                current_phase = 'Phase 3: Architecture'
                            elif 'Phase 4' in content:
                                current_phase = 'Phase 4: Call graph'
                            elif 'Phase 5' in content:
                                current_phase = 'Phase 5: Import graph'
                            elif 'Phase 6' in content:
                                current_phase = 'Phase 6: Patterns'
                            else:
                                current_phase = 'Other'

                            if current_phase != last_phase:
                                print(f"\n🎯 {current_phase}")
                                last_phase = current_phase
                                phase_counts[current_phase] = 0

                        # Show detailed progress
                        if '/' in content and ('file' in content.lower() or 'indexing' in content.lower()):
                            # This is a file-by-file progress update
                            print(f"  [{timestamp}] {content}")
                            if last_phase:
                                phase_counts[last_phase] = phase_counts.get(last_phase, 0) + 1
                        elif 'Phase' in content:
                            print(f"[{timestamp}] 📊 {content}")
                        else:
                            # Other progress messages
                            if len(content) < 100:
                                print(f"[{timestamp}] ➜ {content}")

                    elif msg_type == 'agent_thinking':
                        agent = data.get('agent', 'unknown')
                        print(f"\n🤔 {agent} is thinking...")

                    elif msg_type == 'agent_response':
                        # Just note that we got the final response
                        print(f"\n💬 Final response received (truncated)")
                        break

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"❌ Error: {e}")
                    break

            print("-" * 80)
            print(f"\n📊 Progress Summary:")
            print(f"Total progress messages: {len(progress_messages)}")

            # Show phase statistics
            if phase_counts:
                print("\nDetailed updates per phase:")
                for phase, count in phase_counts.items():
                    print(f"  {phase}: {count} updates")

            # Show sample of file-level updates
            file_updates = [msg for msg in progress_messages if '/' in msg and 'file' in msg.lower()]
            if file_updates:
                print(f"\nFile-level updates captured: {len(file_updates)}")
                print("Sample file updates:")
                for update in file_updates[:5]:
                    print(f"  • {update}")
                if len(file_updates) > 5:
                    print(f"  ... and {len(file_updates) - 5} more")

    except Exception as e:
        print(f"❌ Connection error: {e}")
        return progress_messages

    return progress_messages

if __name__ == "__main__":
    print("🚀 Enhanced Progress Message Test")
    print("=" * 80)
    print("This test will trigger a full infrastructure analysis")
    print("and show detailed progress for each phase and file.")
    print("=" * 80)

    messages = asyncio.run(test_infrastructure_progress())

    print("\n✅ Test complete!")
    print(f"Captured {len(messages)} progress messages total")