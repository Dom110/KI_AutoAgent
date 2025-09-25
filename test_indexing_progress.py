#!/usr/bin/env python3
"""
Test indexing progress messages directly
"""

import asyncio
import json
import websockets
from datetime import datetime

async def test_indexing_progress():
    """Test indexing with detailed progress tracking"""
    uri = "ws://localhost:8000/ws/chat"

    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to {uri}")

            # Send a request that triggers indexing
            request = {
                "type": "chat",
                "agent": "architect",
                "content": "Was kann an der Infrastruktur verbessert werden?",  # This triggers understand_system
                "mode": "single",
                "stream": False,
                "metadata": {
                    "workspace_path": "/Users/dominikfoert/git/KI_AutoAgent"
                }
            }

            await websocket.send(json.dumps(request))
            print(f"📤 Sent: {request['content']}")
            print("\n🔄 Monitoring indexing progress...")
            print("-" * 80)

            start_time = asyncio.get_event_loop().time()
            progress_messages = []
            file_progress_count = 0
            db_operations_count = 0
            dependency_count = 0
            api_count = 0

            while asyncio.get_event_loop().time() - start_time < 90:  # 90 second timeout
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)

                    if data.get('type') == 'agent_progress':
                        content = data.get('content', '')
                        ts = datetime.now().strftime('%H:%M:%S')

                        # Track different types of progress
                        if 'Indexing file' in content:
                            file_progress_count += 1
                            # Show every 10th file or first/last
                            if file_progress_count == 1 or file_progress_count % 10 == 0:
                                print(f"[{ts}] 📂 {content}")
                        elif 'DB scan' in content or 'DB operations' in content:
                            db_operations_count += 1
                            if db_operations_count <= 5 or 'complete' in content.lower():
                                print(f"[{ts}] 💾 {content}")
                        elif 'Dependency graph' in content:
                            dependency_count += 1
                            if dependency_count <= 5 or 'complete' in content.lower():
                                print(f"[{ts}] 📊 {content}")
                        elif 'API scan' in content or 'API extraction' in content:
                            api_count += 1
                            if api_count <= 5 or 'complete' in content.lower():
                                print(f"[{ts}] 🔌 {content}")
                        elif 'Phase' in content:
                            print(f"[{ts}] 🎯 {content}")
                        elif any(x in content for x in ['Building', 'Extracting', 'Identifying', 'complete']):
                            print(f"[{ts}] ⚡ {content}")

                        progress_messages.append(content)

                    elif data.get('type') == 'agent_response':
                        print(f"\n✅ Analysis complete!")
                        break

                    elif data.get('type') == 'error':
                        print(f"\n❌ Error: {data.get('message', 'Unknown error')}")
                        break

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"Error: {e}")
                    break

            print("-" * 80)
            print("\n📊 PROGRESS TRACKING SUMMARY:")
            print(f"• Total progress messages: {len(progress_messages)}")
            print(f"• File indexing messages: {file_progress_count}")
            print(f"• DB operations messages: {db_operations_count}")
            print(f"• Dependency graph messages: {dependency_count}")
            print(f"• API extraction messages: {api_count}")

            if file_progress_count > 0:
                print(f"\n✅ SUCCESS: Detailed file-by-file progress tracking is working!")
            else:
                print(f"\n⚠️ WARNING: No file-by-file progress messages received")

    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    print("🚀 Indexing Progress Test")
    print("=" * 80)
    asyncio.run(test_indexing_progress())