#!/usr/bin/env python3
"""
Quick test - start server in separate process and test WebSocket connection
"""

import subprocess
import sys
import asyncio
import time
import json
from pathlib import Path

try:
    import websockets
except ImportError:
    print("Installing websockets...")
    subprocess.run([sys.executable, "-m", "pip", "install", "websockets", "-q"], check=True)
    import websockets


async def test_websocket():
    """Test WebSocket connection"""
    
    print("⏳ Waiting for server to start...")
    await asyncio.sleep(3)
    
    print("🔌 Attempting WebSocket connection...")
    
    try:
        uri = "ws://127.0.0.1:8002/ws/chat"
        print(f"   URI: {uri}")
        
        async with websockets.connect(uri, ping_interval=20) as websocket:
            print("✅ Connected!")
            
            # Receive welcome
            msg = await websocket.recv()
            data = json.loads(msg)
            print(f"✅ Welcome: {data.get('message', 'No message')}")
            print(f"   Session ID: {data.get('session_id')}")
            print(f"   Client ID: {data.get('client_id')}")
            
            # Initialize
            print("\n📁 Initializing workspace...")
            workspace = "/tmp/ki_test_workspace"
            Path(workspace).mkdir(parents=True, exist_ok=True)
            
            init_msg = {
                "type": "init",
                "workspace_path": workspace
            }
            await websocket.send(json.dumps(init_msg))
            
            response = await websocket.recv()
            data = json.loads(response)
            print(f"✅ Initialized: {data.get('type')}")
            
            # Send request
            print("\n📝 Sending request...")
            request = {
                "type": "chat",
                "content": "Create a simple React counter app"
            }
            await websocket.send(json.dumps(request))
            
            # Receive events for 30 seconds
            print("\n👀 Listening for events (30 seconds)...")
            start = time.time()
            event_count = 0
            
            while time.time() - start < 30:
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=5)
                    event_count += 1
                    data = json.loads(msg)
                    event_type = data.get("type")
                    
                    print(f"  [{event_count}] {event_type}")
                    
                    if event_type == "workflow_complete":
                        print("✅ Workflow complete!")
                        break
                    elif event_type == "error":
                        print(f"❌ Error: {data.get('error')}")
                        break
                        
                except asyncio.TimeoutError:
                    pass
                except json.JSONDecodeError:
                    pass
            
            print(f"\n✅ Received {event_count} events")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    # Start server in background
    print("=" * 80)
    print("🚀 Starting KI AutoAgent v7.0 Server...")
    print("=" * 80)
    
    server_process = subprocess.Popen(
        ["./venv/bin/python", "backend/api/server_v7_mcp.py"],
        cwd="/Users/dominikfoert/git/KI_AutoAgent",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Test WebSocket
        success = asyncio.run(test_websocket())
        
        if success:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Tests failed!")
            
    finally:
        print("\n🛑 Stopping server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("Done")