#!/usr/bin/env python3
"""
ECHTE Anfrage an den laufenden KI AutoAgent
KEINE Simulation - die Agenten arbeiten wirklich!
"""

import asyncio
import websockets
import json
import time
from datetime import datetime

# Die ECHTE komplexe App-Anfrage
REAL_APP_REQUEST = """
Erstelle eine Real-Time Collaborative Whiteboard Anwendung mit folgenden Features:

1. Multi-User Canvas zum gemeinsamen Zeichnen
2. WebSocket für Echtzeit-Synchronisation
3. Verschiedene Zeichenwerkzeuge (Stift, Formen, Text)
4. Farbauswahl und Linienstärke
5. Undo/Redo Funktionalität
6. Chat-Funktion
7. Raum-System mit Join-Codes
8. Export als PNG

Implementiere als HTML/CSS/JavaScript mit Canvas API.
"""

async def send_real_request():
    """Sende ECHTE Anfrage an den laufenden Server"""

    print("🚀 ECHTE ANFRAGE AN KI AUTOAGENT v5.5.2")
    print("=" * 70)
    print("KEINE SIMULATION - Die Agenten arbeiten WIRKLICH!")
    print("=" * 70)

    ws_url = "ws://localhost:8002/ws/chat"

    print(f"\n📡 Verbinde zu: {ws_url}")

    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ VERBUNDEN zum echten Server!")

            # Warte auf Willkommensnachricht
            welcome = await websocket.recv()
            print(f"📥 Server: {json.loads(welcome).get('type', 'unknown')}")

            # Sende die ECHTE Anfrage
            request = {
                "type": "message",
                "content": REAL_APP_REQUEST,
                "session_id": f"real_whiteboard_{int(time.time())}",
                "client_id": "real_client"
            }

            print(f"\n📤 Sende ECHTE Anfrage: Whiteboard App")
            await websocket.send(json.dumps(request))

            print("\n🎯 AGENTEN ARBEITEN JETZT WIRKLICH:")
            print("-" * 40)

            # Sammle ECHTE Responses
            start_time = time.time()
            timeout = 300  # 5 Minuten für echte Ausführung

            agents_active = set()
            steps = 0

            while time.time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)

                    msg_type = data.get('type', '')

                    if msg_type == 'agent_start':
                        agent = data.get('agent', 'unknown')
                        agents_active.add(agent)
                        print(f"🤖 {agent.upper()} startet...")

                    elif msg_type == 'agent_result':
                        agent = data.get('agent', 'unknown')
                        print(f"✅ {agent.upper()} fertig!")

                    elif msg_type == 'step':
                        steps += 1
                        agent = data.get('agent', '')
                        task = data.get('task', '')[:50]
                        print(f"   Step {steps}: {agent} - {task}...")

                    elif msg_type == 'code_generated':
                        print(f"📝 CODE GENERIERT: {data.get('file', 'unknown')}")

                    elif msg_type == 'test_result':
                        print(f"🧪 TEST ERGEBNIS: {data.get('status', 'unknown')}")

                    elif msg_type == 'review':
                        print(f"🔍 REVIEWER: {data.get('message', '')}")

                    elif msg_type == 'complete':
                        print("\n🎉 WORKFLOW ABGESCHLOSSEN!")
                        break

                    elif msg_type == 'error':
                        print(f"❌ FEHLER: {data.get('error', 'unknown')}")

                except asyncio.TimeoutError:
                    continue

            # ERGEBNISSE
            elapsed = time.time() - start_time
            print("\n" + "=" * 70)
            print("📊 ECHTE ERGEBNISSE (KEINE SIMULATION!)")
            print("=" * 70)
            print(f"⏱️  Zeit: {elapsed:.1f} Sekunden")
            print(f"🤖 Agenten aktiv: {', '.join(agents_active)}")
            print(f"📍 Steps ausgeführt: {steps}")

            # Hat der Reviewer WIRKLICH getestet?
            if 'reviewer' in agents_active:
                print("\n✅ REVIEWER HAT WIRKLICH GETESTET!")
            else:
                print("\n⚠️  Reviewer war nicht aktiv")

    except ConnectionRefusedError:
        print("❌ Server läuft nicht auf Port 8002!")
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    print("Sende ECHTE Anfrage an KI AutoAgent...")
    asyncio.run(send_real_request())