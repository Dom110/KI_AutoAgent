#!/usr/bin/env python3
"""
WebSocket Connection Debug Test
Diagnoses connection issues step-by-step
"""

import asyncio
import json
import sys
from datetime import datetime


async def test_websocket_connection():
    """Test WebSocket connection with detailed diagnostics."""
    
    print("\n" + "="*100)
    print("🔍 WEBSOCKET DEBUG TEST - v7.0 MCP Architecture")
    print("="*100)
    
    # Step 1: Import check
    print("\n[STEP 1/5] Importing websockets library...")
    try:
        import websockets
        print("✅ websockets imported successfully")
    except ImportError as e:
        print(f"❌ FAILED: {e}")
        return
    
    # Step 2: Connection attempt
    print("\n[STEP 2/5] Attempting WebSocket connection...")
    uri = "ws://localhost:8002/ws/chat"
    print(f"  URI: {uri}")
    print(f"  Timeout: 5 seconds")
    
    try:
        ws = await asyncio.wait_for(
            websockets.connect(uri),
            timeout=5.0
        )
        print("✅ WebSocket connected successfully")
    except asyncio.TimeoutError:
        print("❌ TIMEOUT: WebSocket connection took >5 seconds")
        return
    except ConnectionRefusedError:
        print("❌ REFUSED: Cannot connect to backend (not running?)")
        return
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {e}")
        return
    
    # Step 3: Initial message
    print("\n[STEP 3/5] Waiting for initial connection message...")
    try:
        initial = await asyncio.wait_for(ws.recv(), timeout=5.0)
        data = json.loads(initial)
        print(f"✅ Received: {data.get('type', 'unknown')}")
        print(f"   Content: {json.dumps(data, indent=2)[:200]}")
    except asyncio.TimeoutError:
        print("❌ TIMEOUT: No initial message after 5 seconds")
        await ws.close()
        return
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {e}")
        await ws.close()
        return
    
    # Step 4: Send init message
    print("\n[STEP 4/5] Sending init message...")
    init_msg = {
        "type": "init",
        "workspace_path": "/Users/dominikfoert/Tests/e2e_workspace_1762965084"
    }
    try:
        await ws.send(json.dumps(init_msg))
        print(f"✅ Init message sent: {json.dumps(init_msg)[:100]}")
    except Exception as e:
        print(f"❌ FAILED to send: {type(e).__name__}: {e}")
        await ws.close()
        return
    
    # Step 5: Wait for init response
    print("\n[STEP 5/5] Waiting for init response...")
    try:
        response = await asyncio.wait_for(ws.recv(), timeout=5.0)
        data = json.loads(response)
        print(f"✅ Received init response: {data.get('type', 'unknown')}")
        print(f"   Content: {json.dumps(data, indent=2)[:300]}")
    except asyncio.TimeoutError:
        print("❌ TIMEOUT: No init response after 5 seconds")
        await ws.close()
        return
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {e}")
        await ws.close()
        return
    
    # Success
    print("\n" + "="*100)
    print("✅ WebSocket connection is WORKING!")
    print("="*100)
    
    await ws.close()


if __name__ == "__main__":
    asyncio.run(test_websocket_connection())
