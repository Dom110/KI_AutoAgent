#!/usr/bin/env python3
"""
SCHNELLER TEST nach Bug Fix
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_after_fix():
    ws_url = "ws://localhost:8003/ws/chat"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ Verbunden!")
            
            # Welcome
            welcome = await websocket.recv()
            
            # Sende Request
            message = {
                "type": "chat",
                "content": "Erstelle eine Todo App",
                "session_id": "fix_test"
            }
            
            print("📤 Sende...")
            await websocket.send(json.dumps(message))
            
            # Warte 5 Sekunden
            for _ in range(5):
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    print(f"📥 {data.get('type', 'unknown')}")
                    
                    if data.get('type') == 'error':
                        print(f"❌ ERROR: {data.get('message', '')}")
                        return False
                        
                except asyncio.TimeoutError:
                    pass
                    
            return True
            
    except Exception as e:
        print(f"❌ {e}")
        return False

if __name__ == "__main__":
    if asyncio.run(test_after_fix()):
        print("✅ Kein Crash mehr!")
    else:
        print("❌ Immer noch Probleme")
