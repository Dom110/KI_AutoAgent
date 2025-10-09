#!/usr/bin/env python3
"""
Live Test for v6 System
Tests actual running server with real task
"""
import asyncio
import aiohttp
import json
from pathlib import Path
import time
import os
import shutil

WORKSPACE = Path.home() / "TestApps" / "CalculatorApp"
SERVER_URL = "ws://localhost:8001/ws/chat"

TASK = """Create a simple Python calculator app with the following features:
1. A Calculator class with methods: add, subtract, multiply, divide
2. Input validation (no division by zero)
3. A main() function that demonstrates usage
4. Type hints and docstrings
5. Save as calculator.py

Keep it simple and well-documented."""


async def test_live():
    """Test v6 system with live command"""
    print("="*80)
    print("🧪 v6 LIVE TEST - Calculator App")
    print("="*80)

    # Clean workspace
    if WORKSPACE.exists():
        shutil.rmtree(WORKSPACE)
    WORKSPACE.mkdir(parents=True, exist_ok=True)

    print(f"\n📁 Workspace: {WORKSPACE}")
    print(f"🔗 Server: {SERVER_URL}")
    print(f"\n📝 Task: {TASK[:100]}...")

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(SERVER_URL) as ws:
            print("\n🔌 Connected to server")

            # 1. Wait for connected
            msg = await ws.receive_json()
            print(f"✅ {msg['type']}: {msg.get('message', '')}")

            # 2. Send init
            await ws.send_json({
                "type": "init",
                "workspace_path": str(WORKSPACE)
            })

            msg = await ws.receive_json()
            print(f"✅ {msg['type']}: {msg.get('message', '')}")

            # 3. Send task
            print(f"\n🚀 Sending task...")
            await ws.send_json({
                "type": "chat",
                "content": TASK
            })

            # 4. Collect responses
            print(f"\n📊 Receiving responses:\n")
            start_time = time.time()

            while True:
                try:
                    msg = await asyncio.wait_for(ws.receive_json(), timeout=300)

                    elapsed = time.time() - start_time
                    msg_type = msg.get("type", "unknown")

                    if msg_type == "result":
                        print(f"\n✅ COMPLETED in {elapsed:.1f}s")
                        print(f"\nResult: {json.dumps(msg.get('result', {}), indent=2)}")
                        break

                    elif msg_type == "error":
                        print(f"\n❌ ERROR: {msg.get('error', 'Unknown error')}")
                        break

                    else:
                        print(f"[{elapsed:6.1f}s] {msg_type}: {str(msg)[:100]}")

                except asyncio.TimeoutError:
                    print(f"\n⏱️  Timeout after 5 minutes")
                    break

    # 5. Check results
    print("\n" + "="*80)
    print("📊 RESULTS")
    print("="*80)

    files_created = list(WORKSPACE.rglob("*"))
    print(f"\n📁 Files created: {len(files_created)}")
    for f in files_created:
        if f.is_file():
            size = f.stat().st_size
            print(f"  - {f.relative_to(WORKSPACE)} ({size} bytes)")

    # Check calculator.py
    calc_file = WORKSPACE / "calculator.py"
    if calc_file.exists():
        print(f"\n✅ calculator.py exists!")
        with open(calc_file) as f:
            content = f.read()
        print(f"\n📄 Content ({len(content)} chars):")
        print("-"*80)
        print(content[:500])
        if len(content) > 500:
            print("...")
        print("-"*80)
    else:
        print(f"\n❌ calculator.py NOT created!")

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_live())
