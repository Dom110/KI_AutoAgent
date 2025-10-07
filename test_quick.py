#!/usr/bin/env python3
"""Quick test to verify fixes"""
import asyncio
import websockets
import json

async def quick_test():
    ws = await websockets.connect("ws://localhost:8001/ws/chat")

    # Connect
    msg = await ws.recv()
    print("Connected:", json.loads(msg)["type"])

    # Init
    await ws.send(json.dumps({
        "type": "init",
        "workspace_path": "/Users/dominikfoert/TestApps/DesktopCalculator"
    }))
    msg = await ws.recv()
    print("Initialized:", json.loads(msg).get("session_id"))

    # Send request
    await ws.send(json.dumps({
        "type": "chat",
        "content": "Create a simple Python hello.py file that prints 'Hello World'",
        "agent": "auto",
        "mode": "direct"
    }))

    # Receive messages
    timeout_counter = 0
    while timeout_counter < 120:
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=1)
            data = json.loads(msg)
            msg_type = data.get("type")

            print(f"[{msg_type}]", end=" ")

            if msg_type in ["agent_response", "response"]:
                content = data.get("content", "")
                print(f"\n\nRESPONSE:\n{content[:300]}\n")
                break
            elif msg_type == "error":
                print(f"\n\nERROR: {data.get('message')}\n")
                break

        except asyncio.TimeoutError:
            timeout_counter += 1
            print(".", end="", flush=True)

    await ws.close()
    print("\n✅ Test complete")

if __name__ == "__main__":
    asyncio.run(quick_test())
