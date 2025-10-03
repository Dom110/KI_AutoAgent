#!/usr/bin/env python3
"""
Test OHNE Architecture Proposal - Direkter Task für CodeSmith
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_direct():
    ws_url = "ws://localhost:8001/ws/chat"

    print("🚀 TEST OHNE ARCHITECTURE PROPOSAL")
    print("=" * 50)

    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ Verbunden zu Backend v5.5.2")

            # Welcome
            await websocket.recv()

            # Sende einen DIREKTEN Code-Request (sollte Architecture Proposal überspringen)
            message = {
                "type": "chat",
                "content": "Write a Python function that calculates the factorial of a number",
                "session_id": f"direct_{datetime.now().strftime('%H%M%S')}"
            }

            print("📤 Sende direkten Code-Request...")
            await websocket.send(json.dumps(message))

            print("\n🤖 AGENTEN-AKTIVITÄT:")
            print("-" * 40)

            agents_seen = set()
            timeout = 45
            start = datetime.now()
            code_found = False

            while (datetime.now() - start).seconds < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)

                    # Track agents
                    if 'agent' in data:
                        agent = data['agent']
                        if agent not in agents_seen:
                            agents_seen.add(agent)
                            print(f"   ✅ {agent.upper()} aktiviert!")

                    # Check for code
                    content = str(data.get('content', ''))
                    if 'def factorial' in content or 'def ' in content:
                        code_found = True
                        print("   📝 Code generiert!")

                    # Track specific agents
                    if 'codesmith' in str(data).lower():
                        print("   💻 CodeSmith arbeitet!")
                    if 'reviewer' in str(data).lower():
                        print("   🔍 Reviewer analysiert!")

                    # Error
                    if data.get('type') == 'error':
                        print(f"   ❌ ERROR: {data.get('message')}")

                except asyncio.TimeoutError:
                    print(".", end="", flush=True)

            print(f"\n\n{'='*50}")
            print("📊 ERGEBNIS:")
            print(f"   Aktive Agenten: {', '.join(sorted(agents_seen))}")
            print(f"   Anzahl: {len(agents_seen)}")
            print(f"   Code generiert: {'✅' if code_found else '❌'}")

            success = len(agents_seen) >= 2

            if success:
                print("\n🎉 ERFOLG! Mehrere Agenten arbeiten!")
                for agent in ['orchestrator', 'architect', 'codesmith', 'reviewer', 'fixer']:
                    if agent in agents_seen:
                        print(f"   ✅ {agent.capitalize()} war aktiv")
            else:
                print(f"\n❌ Nur {len(agents_seen)} Agent(en) - System funktioniert nicht korrekt!")

            return success

    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_direct())
    print("\n" + "="*50)
    if success:
        print("🎯 AGENTEN ARBEITEN ZUSAMMEN!")
    else:
        print("❌ AGENTEN-KOLLABORATION FEHLGESCHLAGEN")
