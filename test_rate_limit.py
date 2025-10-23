#!/usr/bin/env python3
"""
Quick test to verify Rate Limiter is working

This should show rate limit delays in the logs.
"""

import asyncio
import json
import websockets


async def quick_test():
    """Test rate limiter with simple workflow."""
    print("🧪 Testing Rate Limiter...")
    print("=" * 60)

    uri = "ws://localhost:8002/ws/chat"
    workspace = "/Users/dominikfoert/TestApps/rate_limit_test"

    async with websockets.connect(uri) as ws:
        # Init
        await ws.send(json.dumps({
            "type": "init",
            "workspace_path": workspace
        }))
        await ws.recv()  # init_complete

        # Simple task (should trigger multiple AI calls with delays)
        await ws.send(json.dumps({
            "type": "task",
            "task": "Explain what a hello world program does"
        }))

        print("📨 Task sent, waiting for responses...")
        print("🔍 Watch for rate limit messages in server logs:")
        print("   - '⏸️ Rate limit: waited...'")
        print("=" * 60)

        # Collect messages
        messages = 0
        while messages < 10:  # Collect some messages
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=30)
                data = json.loads(msg)
                msg_type = data.get("type")
                print(f"📥 {msg_type}")

                if msg_type == "workflow_complete":
                    print("✅ Workflow complete!")
                    break

                messages += 1
            except asyncio.TimeoutError:
                print("⏱️ Timeout")
                break

    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("📋 Check server logs for rate limit messages")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(quick_test())
