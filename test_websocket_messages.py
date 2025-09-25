#!/usr/bin/env python3
"""
Simple WebSocket test to show all messages received
"""

import asyncio
import json
import websockets
from datetime import datetime

async def test_progress_messages():
    """Test that progress messages are being received"""
    uri = "ws://localhost:8000/ws/chat"
    messages = []

    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to {uri}")

            # Send a test message
            request = {
                "type": "chat",
                "agent": "auto",
                "message": "What agents are available in the system?",
                "mode": "auto",
                "stream": False
            }

            await websocket.send(json.dumps(request))
            print(f"📤 Sent: {request['message']}")
            print("\n🔄 Receiving messages (10 second timeout)...")
            print("-" * 60)

            # Receive messages for 10 seconds
            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < 10:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    data = json.loads(response)
                    messages.append(data)

                    # Display message based on type
                    msg_type = data.get('type', 'unknown')
                    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

                    if msg_type == 'agent_progress':
                        content = data.get('content', data.get('message', ''))
                        agent = data.get('agent', 'unknown')
                        print(f"[{timestamp}] 📊 PROGRESS ({agent}): {content}")
                    elif msg_type == 'agent_thinking':
                        agent = data.get('agent', 'unknown')
                        message = data.get('message', '')
                        print(f"[{timestamp}] 🤔 THINKING ({agent}): {message}")
                    elif msg_type == 'agent_response':
                        content = data.get('content', '')[:100] + '...' if len(data.get('content', '')) > 100 else data.get('content', '')
                        print(f"[{timestamp}] 💬 RESPONSE: {content}")
                    else:
                        print(f"[{timestamp}] 🔷 {msg_type}: {json.dumps(data)[:100]}...")

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"❌ Error receiving: {e}")
                    break

            print("-" * 60)
            print(f"\n📊 Summary:")
            print(f"Total messages received: {len(messages)}")

            # Count by type
            type_counts = {}
            for msg in messages:
                msg_type = msg.get('type', 'unknown')
                type_counts[msg_type] = type_counts.get(msg_type, 0) + 1

            print("\nMessage types:")
            for msg_type, count in sorted(type_counts.items()):
                emoji = {
                    'agent_progress': '📊',
                    'agent_thinking': '🤔',
                    'agent_response': '💬'
                }.get(msg_type, '🔷')
                print(f"  {emoji} {msg_type}: {count}")

            # Save to file for inspection
            with open('test_websocket_messages.json', 'w') as f:
                json.dump(messages, f, indent=2)
            print(f"\n💾 All messages saved to test_websocket_messages.json")

    except Exception as e:
        print(f"❌ Connection error: {e}")
        return

    return messages

if __name__ == "__main__":
    print("🚀 WebSocket Progress Message Test")
    print("=" * 60)
    messages = asyncio.run(test_progress_messages())
    print("\n✅ Test complete!")