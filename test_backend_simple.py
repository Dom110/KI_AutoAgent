#!/usr/bin/env python3
"""
Einfacher E2E Test - Testet ob Backend funktioniert
"""

import asyncio
import json
from pathlib import Path
import websockets
from datetime import datetime


async def test_backend_connection():
    """Test basic WebSocket connection to backend"""
    
    print("\n" + "=" * 100)
    print("🧪 SIMPLE BACKEND TEST - WebSocket Connection")
    print("=" * 100)
    print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}\n")
    
    try:
        # Test workspace
        test_workspace = Path.home() / "TestApps" / "simple_test"
        test_workspace.mkdir(parents=True, exist_ok=True)
        
        uri = "ws://localhost:8002/ws/chat"
        print(f"📡 Connecting to: {uri}")
        print(f"📁 Workspace: {test_workspace}\n")
        
        async with websockets.connect(uri, ping_interval=None) as websocket:
            print("✅ Connected!\n")
            
            # Wait for initial message
            initial_msg = await asyncio.wait_for(websocket.recv(), timeout=5)
            print(f"📥 Initial message: {initial_msg}\n")
            
            # Send init
            print("📤 Sending init...")
            await websocket.send(json.dumps({
                "type": "init",
                "workspace_path": str(test_workspace)
            }))
            
            init_response = await asyncio.wait_for(websocket.recv(), timeout=5)
            print(f"✅ Init response: {init_response}\n")
            
            # Send simple query
            query = "Hallo! Kannst du mir einen Überblick geben?"
            print(f"📤 Sending query: {query}\n")
            await websocket.send(json.dumps({
                "type": "chat",
                "content": query
            }))
            
            # Collect responses
            responses = []
            print("⏳ Collecting responses...\n")
            
            for i in range(30):  # Max 30 messages
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    data = json.loads(response)
                    responses.append(data)
                    
                    if data.get("type") == "completion":
                        print(f"✅ Completion received!")
                        break
                    elif data.get("type") == "error":
                        print(f"❌ Error: {data.get('content')}")
                        break
                    elif data.get("type") in ["message", "progress"]:
                        msg_preview = str(data.get("content", ""))[:60]
                        print(f"   [{i+1}] {data['type']}: {msg_preview}...")
                        
                except asyncio.TimeoutError:
                    print(f"   [{i+1}] Timeout (waiting for response)")
                    continue
                except json.JSONDecodeError as e:
                    print(f"   [{i+1}] JSON Error: {e}")
                    continue
            
            print(f"\n" + "=" * 100)
            print(f"📊 RESULTS:")
            print(f"   • Total messages received: {len(responses)}")
            if responses:
                print(f"   • Last message type: {responses[-1].get('type')}")
            print("=" * 100 + "\n")
            
            if len(responses) > 0:
                print("✅ BACKEND IS WORKING!")
                return True
            else:
                print("❌ NO RESPONSES FROM BACKEND")
                return False
                
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        print("=" * 100)
        print("Troubleshooting:")
        print("1. Is the backend running?  python start_server.py")
        print("2. Is port 8002 available?")
        print("3. Check backend logs for errors")
        print("=" * 100 + "\n")
        return False


async def main():
    result = await test_backend_connection()
    exit(0 if result else 1)


if __name__ == "__main__":
    asyncio.run(main())
