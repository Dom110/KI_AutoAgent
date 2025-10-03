#!/usr/bin/env python3
"""
ECHTER TEST - Whiteboard App generieren lassen
"""

import asyncio
import websockets
import json
from datetime import datetime

async def generate_real_app():
    ws_url = "ws://localhost:8003/ws/chat"
    
    print("🚀 WHITEBOARD APP GENERIERUNG")
    print("=" * 50)
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ Verbunden zu KI AutoAgent v5.5.2")
            
            # Welcome
            welcome = await websocket.recv()
            client_data = json.loads(welcome)
            
            # Sende Request
            message = {
                "type": "chat",
                "content": """Erstelle eine Whiteboard Web-App mit:
                - Canvas zum Zeichnen
                - Farbauswahl
                - Export als PNG
                Implementiere als einzelne HTML Datei.""",
                "session_id": f"wb_{datetime.now().strftime('%H%M%S')}"
            }
            
            print("📤 Sende Whiteboard-Request...")
            await websocket.send(json.dumps(message))
            
            # Sammle Responses
            print("\n🤖 AGENTEN-AKTIVITÄT:")
            print("-" * 40)
            
            agents_seen = set()
            timeout = 60  # 1 Minute
            start = datetime.now()
            
            while (datetime.now() - start).seconds < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    
                    msg_type = data.get('type', '')
                    
                    if 'agent' in data:
                        agent = data['agent']
                        agents_seen.add(agent)
                        print(f"   {agent.upper()} arbeitet...")
                    
                    if msg_type == 'architecture_proposal':
                        print("\n📋 ARCHITECTURE PROPOSAL erhalten!")
                        # Auto-approve
                        approval = {
                            "type": "architecture_approval",
                            "session_id": message["session_id"],
                            "decision": "approved",
                            "feedback": "Go ahead!"
                        }
                        await websocket.send(json.dumps(approval))
                        print("✅ Approved!")
                    
                    elif msg_type == 'code_generated':
                        print(f"📝 CODE GENERIERT!")
                    
                    elif msg_type == 'error':
                        print(f"❌ ERROR: {data.get('message', '')}")
                    
                except asyncio.TimeoutError:
                    print(".", end="", flush=True)
            
            print(f"\n\n✅ Agenten die gearbeitet haben: {', '.join(agents_seen)}")
            
            if 'reviewer' in agents_seen:
                print("🎉 REVIEWER HAT GETESTET!")
            else:
                print("⚠️  Reviewer war nicht aktiv")
            
            return len(agents_seen) > 0
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

if __name__ == "__main__":
    if asyncio.run(generate_real_app()):
        print("\n✅ ERFOLG! Die Agenten arbeiten!")
    else:
        print("\n❌ Die Agenten arbeiten noch nicht richtig")
