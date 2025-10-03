#!/usr/bin/env python3
"""
Test mit gefixtem Validation System - sollte jetzt mehrere Agenten aktivieren
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_multi_agents():
    ws_url = "ws://localhost:8001/ws/chat"  # Port 8001 - primary port!

    print("🚀 TEST NACH VALIDATION FIX")
    print("=" * 50)

    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ Verbunden zu Backend v5.5.2")

            # Welcome
            await websocket.recv()

            # Sende Request
            message = {
                "type": "chat",
                "content": "Erstelle eine komplexe Whiteboard Web-App mit Canvas zum Zeichnen, Farbauswahl, Pinselgrößen, Undo/Redo und Export als PNG",
                "session_id": f"test_{datetime.now().strftime('%H%M%S')}"
            }

            print("📤 Sende Whiteboard Request...")
            await websocket.send(json.dumps(message))

            print("\n🤖 AGENTEN-AKTIVITÄT:")
            print("-" * 40)

            agents_seen = set()
            timeout = 60  # 1 Minute
            start = datetime.now()
            code_generated = False
            review_done = False

            while (datetime.now() - start).seconds < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)

                    # Track agents
                    if 'agent' in data:
                        agent = data['agent']
                        if agent not in agents_seen:
                            agents_seen.add(agent)
                            print(f"   ✅ {agent.upper()} arbeitet!")

                    # Handle architecture proposal
                    if data.get('type') == 'architecture_proposal':
                        print("\n📋 ARCHITECTURE PROPOSAL erhalten!")
                        approval = {
                            "type": "architecture_approval",
                            "session_id": message["session_id"],
                            "decision": "approved"
                        }
                        await websocket.send(json.dumps(approval))
                        print("✅ Approved!")

                    # Track code generation
                    if 'codesmith' in str(data).lower() and 'code' in str(data).lower():
                        code_generated = True
                        print("📝 CodeSmith generiert Code!")

                    # Track review
                    if 'reviewer' in str(data).lower():
                        review_done = True
                        print("🔍 Reviewer testet die App!")

                    # Error handling
                    if data.get('type') == 'error':
                        print(f"❌ ERROR: {data.get('message')}")

                except asyncio.TimeoutError:
                    print(".", end="", flush=True)

            print(f"\n\n{'='*50}")
            print("📊 ERGEBNIS:")
            print(f"   Aktive Agenten: {', '.join(sorted(agents_seen))}")
            print(f"   Anzahl: {len(agents_seen)}")
            print(f"   Code generiert: {'✅' if code_generated else '❌'}")
            print(f"   Review durchgeführt: {'✅' if review_done else '❌'}")

            success = len(agents_seen) >= 3  # Mindestens Orchestrator, Architect, CodeSmith

            if success:
                print("\n🎉 ERFOLG! Mehrere Agenten arbeiten zusammen!")
                if 'architect' in agents_seen:
                    print("   ✅ Architect hat Design erstellt")
                if 'codesmith' in agents_seen:
                    print("   ✅ CodeSmith hat Code generiert")
                if 'reviewer' in agents_seen:
                    print("   ✅ Reviewer hat getestet")
                if 'fixer' in agents_seen:
                    print("   ✅ Fixer hat Bugs behoben")
            else:
                print(f"\n❌ Nur {len(agents_seen)} Agent(en) aktiv - Validation blockiert noch!")

            return success

    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_multi_agents())
    print("\n" + "="*50)
    if success:
        print("🎯 DER VALIDATION FIX FUNKTIONIERT!")
    else:
        print("❌ Weitere Debugging nötig...")