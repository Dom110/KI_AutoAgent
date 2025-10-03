#!/usr/bin/env python3
"""
ECHTER Request an KI AutoAgent - Whiteboard App generieren lassen
Korrekte Message-Format für den Server
"""

import asyncio
import websockets
import json
from datetime import datetime

async def generate_whiteboard_app():
    """Lass die Agenten WIRKLICH eine Whiteboard App generieren"""

    print("🚀 KI AUTOAGENT v5.5.2 - ECHTE APP GENERIERUNG")
    print("=" * 70)
    print("Die Agenten werden JETZT eine Whiteboard-App erstellen!")
    print("=" * 70)

    # WebSocket URL auf Port 8002 (wie im Log gesehen)
    ws_url = "ws://localhost:8002/ws/chat"

    session_id = f"whiteboard_{datetime.now().strftime('%H%M%S')}"

    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"\n✅ Verbunden zu: {ws_url}")

            # Warte auf Welcome Message
            welcome = await websocket.recv()
            data = json.loads(welcome)
            client_id = data.get('client_id', 'unknown')
            print(f"✅ Client ID: {client_id}")

            # Sende die ECHTE Anfrage im richtigen Format
            message = {
                "type": "chat",  # WICHTIG: "chat" nicht "message"!
                "content": """Erstelle eine Collaborative Whiteboard Web-App mit:
                - Multi-User Canvas zum gemeinsamen Zeichnen
                - WebSocket für Echtzeit-Sync
                - Zeichenwerkzeuge (Stift, Formen, Text)
                - Farbauswahl und Chat-Funktion
                - Export als PNG

                Implementiere als HTML/CSS/JS mit Canvas API.""",
                "session_id": session_id
            }

            print(f"\n📤 Sende Anfrage (Session: {session_id})")
            await websocket.send(json.dumps(message))
            print("✅ Anfrage gesendet!")

            # Empfange und zeige Agenten-Aktivität
            print("\n🤖 AGENTEN-AKTIVITÄT:")
            print("-" * 40)

            timeout = 180  # 3 Minuten
            start_time = datetime.now()

            while (datetime.now() - start_time).seconds < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(response)

                    msg_type = data.get('type', '')
                    agent = data.get('agent', '')
                    content = data.get('content', '')

                    # Zeige verschiedene Message-Typen
                    if msg_type == 'status':
                        print(f"📊 Status: {data.get('status', '')}")

                    elif msg_type == 'agent_start':
                        print(f"\n🚀 {agent.upper()} startet...")

                    elif msg_type == 'response':
                        if content:
                            print(f"✅ {agent.upper()}: {content[:100]}...")

                    elif msg_type == 'architecture_proposal':
                        print("\n📋 ARCHITECTURE PROPOSAL erhalten!")
                        print("   Sende Approval...")

                        # Auto-approve für Test
                        approval = {
                            "type": "architecture_approval",
                            "session_id": session_id,
                            "decision": "approved",
                            "feedback": "Looks good, proceed!"
                        }
                        await websocket.send(json.dumps(approval))
                        print("✅ Approved!")

                    elif msg_type == 'code':
                        print(f"📝 CODE generiert: {data.get('file', 'unknown')}")

                    elif msg_type == 'error':
                        print(f"❌ ERROR: {data.get('message', content)}")

                    elif msg_type == 'complete':
                        print("\n🎉 FERTIG! App wurde generiert!")
                        break

                except asyncio.TimeoutError:
                    print(".", end="", flush=True)

            print("\n\n" + "=" * 70)
            print("📊 ZUSAMMENFASSUNG")
            print("=" * 70)
            duration = (datetime.now() - start_time).seconds
            print(f"⏱️  Dauer: {duration} Sekunden")
            print(f"📁 Generierte Files sollten im Projekt-Ordner sein")

    except ConnectionRefusedError:
        print("\n❌ FEHLER: Server läuft nicht auf Port 8002!")
        print("   Der Server sollte bereits laufen (wurde im Hintergrund gestartet)")

    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starte ECHTE App-Generierung durch KI AutoAgent...")
    print("KEINE Simulation - die Agenten arbeiten WIRKLICH!\n")
    asyncio.run(generate_whiteboard_app())