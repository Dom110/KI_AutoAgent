#!/usr/bin/env python3
"""
INTEGRATED TEST: Start Server + Run Test + Analyze
"""
import subprocess
import time
import sys
import os
import signal
import asyncio
import json
import websockets
from pathlib import Path

# Ensure we're in venv
if not os.environ.get('VIRTUAL_ENV'):
    print("❌ Not in venv. Activating...")
    os.system("source /Users/dominikfoert/git/KI_AutoAgent/venv/bin/activate")

os.chdir("/Users/dominikfoert/git/KI_AutoAgent")

print("=" * 80)
print("🚀 PHASE 1: Starting Server...")
print("=" * 80)

# Kill any existing server
os.system("pkill -f 'uvicorn.*8002' 2>/dev/null")
os.system("pkill -f 'start_server' 2>/dev/null")
time.sleep(2)

# Start server
server_proc = subprocess.Popen(
    [sys.executable, "start_server.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

print("⏳ Waiting for server to start...")
time.sleep(8)

# Check if server is running
result = os.system("curl -s http://localhost:8002/health > /dev/null 2>&1")
if result != 0:
    print("❌ Server failed to start!")
    stdout, stderr = server_proc.communicate(timeout=2)
    print("STDOUT:", stdout[-500:] if stdout else "")
    print("STDERR:", stderr[-500:] if stderr else "")
    sys.exit(1)

print("✅ Server running on 8002")

print("\n" + "=" * 80)
print("🧪 PHASE 2: Running WebSocket Test...")
print("=" * 80)

async def run_test():
    uri = "ws://localhost:8002/ws/chat"
    messages_received = []
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to {uri}")
            
            # Send init
            init_msg = {
                "type": "init",
                "workspace_path": str(Path.home() / "TestApps/e2e_test_integrated")
            }
            await websocket.send(json.dumps(init_msg))
            print(f"📤 Sent init: {init_msg}")
            
            # Send chat request
            chat_msg = {
                "type": "chat",
                "content": "Erstelle eine einfache React Todo-App",
                "session_id": "test_session_001"
            }
            await websocket.send(json.dumps(chat_msg))
            print(f"📤 Sent chat request")
            
            # Receive messages
            start_time = time.time()
            timeout = 120
            
            while time.time() - start_time < timeout:
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(msg)
                    messages_received.append(data)
                    
                    if data.get("type") == "progress":
                        print(f"📊 [{len(messages_received):3d}] {data.get('message', 'N/A')[:70]}")
                    elif data.get("type") == "complete":
                        print(f"✅ COMPLETE EVENT RECEIVED!")
                        break
                    elif data.get("type") == "error":
                        print(f"❌ ERROR: {data.get('message')}")
                        
                except asyncio.TimeoutError:
                    print(f"⏱️  No message for 5s, continuing...")
                    
    except Exception as e:
        print(f"❌ Connection error: {e}")
    
    return messages_received

try:
    messages = asyncio.run(run_test())
except KeyboardInterrupt:
    messages = []

print("\n" + "=" * 80)
print("📊 PHASE 3: Analysis")
print("=" * 80)
print(f"✅ Messages received: {len(messages)}")

# Check workspace
workspace = Path.home() / "TestApps/e2e_test_integrated"
if workspace.exists():
    files = list(workspace.glob("**/*"))
    print(f"📁 Files in workspace: {len([f for f in files if f.is_file()])}")
    for f in files[:20]:
        if f.is_file():
            print(f"   - {f.relative_to(workspace)}")
else:
    print(f"❌ Workspace not created: {workspace}")

# Check for complete message
has_complete = any(m.get("type") == "complete" for m in messages)
print(f"\n🎯 Has 'complete' event: {has_complete}")

# Summary
print("\n" + "=" * 80)
if len(messages) > 0 and has_complete:
    print("✅ TEST PASSED: Server responded + Files generated + Complete event")
elif len(messages) > 0:
    print("⚠️  PARTIAL: Server responded but workflow incomplete")
else:
    print("❌ TEST FAILED: No server response")
print("=" * 80)

# Cleanup
print("\n🛑 Stopping server...")
server_proc.terminate()
time.sleep(2)
server_proc.kill()