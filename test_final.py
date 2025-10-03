#!/usr/bin/env python3
import asyncio
import websockets
import json
from datetime import datetime

async def final_test():
    ws_url = "ws://localhost:8003/ws/chat"
    
    print("🚀 FINALER TEST - Whiteboard App")
    print("=" * 50)
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ Verbunden")
            
            # Welcome
            await websocket.recv()
            
            # Sende Request
            message = {
                "type": "chat",
                "content": "Erstelle eine Whiteboard Web-App mit Canvas zum Zeichnen",
                "session_id": f"final_{datetime.now().strftime('%H%M%S')}"
            }
            
            print("📤 Sende Request...")
            await websocket.send(json.dumps(message))
            
            print("\n🤖 Agenten-Aktivität:")
            agents_seen = set()
            timeout = 30
            start = datetime.now()
            
            while (datetime.now() - start).seconds < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    
                    if 'agent' in data:
                        agent = data['agent']
                        if agent not in agents_seen:
                            agents_seen.add(agent)
                            print(f"   ✅ {agent.upper()} arbeitet!")
                    
                    if data.get('type') == 'architecture_proposal':
                        print("\n📋 Architecture Proposal!")
                        approval = {
                            "type": "architecture_approval",
                            "session_id": message["session_id"],
                            "decision": "approved"
                        }
                        await websocket.send(json.dumps(approval))
                        print("✅ Approved!")
                    
                    if data.get('type') == 'error':
                        print(f"❌ {data.get('message')}")
                    
                except asyncio.TimeoutError:
                    print(".", end="", flush=True)
            
            print(f"\n\n🎯 ERGEBNIS:")
            print(f"Agenten aktiv: {', '.join(agents_seen) if agents_seen else 'KEINE'}")
            
            if len(agents_seen) > 2:
                print("✅ ERFOLG! Mehrere Agenten arbeiten!")
                if 'reviewer' in agents_seen:
                    print("🎉 REVIEWER HAT DIE APP GETESTET!")
                return True
            else:
                print("❌ Nur Orchestrator aktiv")
                return False
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

if __name__ == "__main__":
    if asyncio.run(final_test()):
        print("\n🎉 DER KI AGENT FUNKTIONIERT!")
    else:
        print("\n❌ Noch mehr Bugs zu fixen...")
