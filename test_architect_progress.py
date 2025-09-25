#!/usr/bin/env python3
"""
Test progress messages by calling architect agent directly
"""

import asyncio
import json
import websockets
from datetime import datetime

async def test_architect_progress():
    """Test architect agent with infrastructure analysis"""
    uri = "ws://localhost:8000/ws/chat"
    progress_messages = []

    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to {uri}")

            # Send directly to architect agent to trigger system analysis
            request = {
                "type": "chat",
                "agent": "architect",  # Direct to architect
                "message": "Analyze the infrastructure and suggest improvements",
                "mode": "single",
                "stream": False,
                "workspace_path": "/Users/dominikfoert/git/KI_AutoAgent"
            }

            await websocket.send(json.dumps(request))
            print(f"📤 Sent to architect: {request['message']}")
            print("\n🔄 Collecting progress messages (40 second timeout)...")
            print("-" * 80)

            # Receive messages for 40 seconds
            start_time = asyncio.get_event_loop().time()
            file_count = 0

            while asyncio.get_event_loop().time() - start_time < 40:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    data = json.loads(response)

                    msg_type = data.get('type', 'unknown')

                    if msg_type == 'agent_progress':
                        content = data.get('content', data.get('message', ''))
                        agent = data.get('agent', 'unknown')
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        progress_messages.append(content)

                        # Track file indexing
                        if 'Indexing file' in content and '/' in content:
                            file_count += 1
                            # Show every 10th file or first 5
                            if file_count <= 5 or file_count % 10 == 0:
                                # Extract just the filename
                                parts = content.split(':')
                                if len(parts) >= 2:
                                    file_info = parts[-1].strip()
                                    progress_part = parts[0] if len(parts) > 1 else content
                                    print(f"[{timestamp}] {progress_part}: {file_info}")
                        elif 'Phase' in content:
                            # Phase changes
                            print(f"\n[{timestamp}] 🎯 {content}")
                        elif any(keyword in content for keyword in ['Building', 'Running', 'Analyzing', 'Detecting', 'Calculating']):
                            # Other important progress
                            print(f"[{timestamp}] ➜ {content}")

                    elif msg_type == 'agent_thinking':
                        print(f"\n🤔 {data.get('agent', 'unknown')} is processing...")

                    elif msg_type == 'agent_response':
                        print(f"\n💬 Analysis complete!")
                        # Don't break, wait for more progress messages

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"❌ Error: {e}")
                    break

            print("-" * 80)
            print(f"\n📊 Progress Summary:")
            print(f"Total progress messages: {len(progress_messages)}")
            print(f"Files indexed: {file_count}")

            # Analyze phases
            phases = {}
            for msg in progress_messages:
                if 'Phase 1' in msg:
                    phases['Phase 1: Indexing'] = phases.get('Phase 1: Indexing', 0) + 1
                elif 'Phase 2' in msg:
                    phases['Phase 2: Cross-references'] = phases.get('Phase 2: Cross-references', 0) + 1
                elif 'Phase 3' in msg:
                    phases['Phase 3: Architecture'] = phases.get('Phase 3: Architecture', 0) + 1
                elif 'Phase 4' in msg:
                    phases['Phase 4: Call graph'] = phases.get('Phase 4: Call graph', 0) + 1
                elif 'Phase 5' in msg:
                    phases['Phase 5: Import graph'] = phases.get('Phase 5: Import graph', 0) + 1
                elif 'Phase 6' in msg:
                    phases['Phase 6: Patterns'] = phases.get('Phase 6: Patterns', 0) + 1

            if phases:
                print("\nPhases detected:")
                for phase, count in phases.items():
                    print(f"  • {phase}: {count} messages")

    except Exception as e:
        print(f"❌ Connection error: {e}")

    return progress_messages

if __name__ == "__main__":
    print("🚀 Architect Agent Progress Test")
    print("=" * 80)
    print("Testing detailed progress messages from architect agent")
    print("=" * 80)

    messages = asyncio.run(test_architect_progress())
    print(f"\n✅ Test complete! Total messages: {len(messages)}")