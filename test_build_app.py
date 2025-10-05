#!/usr/bin/env python3
"""
Test: Lasse KI_Agent FREI eine Dashboard App bauen
Keine Einschränkungen - schauen was passiert
"""

import asyncio
import websockets
import json
import sys

async def test_free_agent():
    """Let the agent build freely and see what happens"""

    uri = "ws://localhost:8001/ws/chat"
    workspace_path = "/Users/dominikfoert/TestApp2"

    print("=" * 80)
    print("🧪 FREIER TEST: Agent baut Dashboard App SELBSTSTÄNDIG")
    print("=" * 80)

    async with websockets.connect(uri) as websocket:
        print(f"\n✅ Connected to {uri}")

        # Step 1: Receive connection message
        connection_msg = await websocket.recv()
        print(f"\n📨 Server: {json.loads(connection_msg)['message']}")

        # Step 2: Send init message
        init_message = {
            "type": "init",
            "workspace_path": workspace_path
        }
        await websocket.send(json.dumps(init_message))
        init_response = await websocket.recv()
        print(f"✅ Workspace: {workspace_path}")

        # Step 3: Send FREE request - Agent entscheidet ALLES
        request = {
            "type": "chat",
            "message": """Erstelle eine moderne Analytics Dashboard Anwendung für TestApp2.

Die App soll:
- Echtzeit-Metriken anzeigen (Users, Revenue, Sessions, Conversion Rate)
- Interaktive Charts haben
- Responsive Design nutzen
- Modern und professionell aussehen

Erstelle alle notwendigen Dateien und dokumentiere die Architektur.""",
            "mode": "auto"
        }
        print(f"\n📤 Anfrage: Agent soll FREI arbeiten...")
        print(f"   Workspace: {workspace_path}")
        print(f"   Status: LEER - Agent baut von Grund auf")
        await websocket.send(json.dumps(request))

        print("\n" + "=" * 80)
        print("📊 AGENT ARBEITET:")
        print("=" * 80)

        session_id = None
        response_count = 0

        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=300.0)
                response_data = json.loads(response)
                response_count += 1

                msg_type = response_data.get('type', 'unknown')

                if 'session_id' in response_data:
                    session_id = response_data['session_id']

                if msg_type == 'architecture_proposal':
                    print(f"\n📋 Architecture Proposal received")
                    proposal = response_data.get('proposal', {})

                    # Show summary
                    if isinstance(proposal, dict):
                        print(f"   Tasks: {len(proposal.get('tasks', []))}")
                        print(f"   Stack: {proposal.get('technology_stack', 'N/A')}")

                    # AUTO-APPROVE
                    approval = {
                        "type": "architecture_approval",
                        "session_id": session_id,
                        "decision": "approved"
                    }
                    await websocket.send(json.dumps(approval))
                    print("   ✅ AUTO-APPROVED")

                elif msg_type == 'agent_response':
                    agent = response_data.get('agent', 'unknown')
                    content = response_data.get('content', '')
                    print(f"\n🤖 {agent.upper()}:")
                    print(f"   {content[:200]}..." if len(content) > 200 else f"   {content}")

                elif msg_type == 'agent_progress':
                    agent = response_data.get('agent', 'unknown')
                    progress = response_data.get('content', '')
                    print(f"⏳ {agent}: {progress[:100]}...")

                elif msg_type == 'workflow_complete':
                    print("\n" + "=" * 80)
                    print("✅ WORKFLOW COMPLETE!")
                    print("=" * 80)
                    final = response_data.get('final_response', '')
                    print(f"\n{final[:500]}..." if len(final) > 500 else final)
                    break

                elif msg_type == 'error':
                    error = response_data.get('error', 'Unknown')
                    print(f"\n❌ Error: {error}")
                    break

            except asyncio.TimeoutError:
                print("\n⏱️  Timeout - checking workspace...")
                break
            except websockets.exceptions.ConnectionClosed:
                print("\n🔌 Connection closed")
                break

        print(f"\n📊 Total responses: {response_count}")

        # Check what was created
        import os
        print("\n" + "=" * 80)
        print("📁 ERGEBNIS - Was wurde erstellt?")
        print("=" * 80)

        for root, dirs, files in os.walk(workspace_path):
            # Skip hidden dirs
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            level = root.replace(workspace_path, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                if not file.startswith('.'):
                    size = os.path.getsize(os.path.join(root, file))
                    print(f'{subindent}{file} ({size:,} bytes)')

        # Show analysis results if exist
        analysis_file = os.path.join(workspace_path, ".ki_autoagent_ws", "system_analysis.json")
        if os.path.exists(analysis_file):
            print("\n" + "=" * 80)
            print("📊 ANALYSE-ERGEBNISSE:")
            print("=" * 80)
            with open(analysis_file) as f:
                analysis = json.load(f)
                stats = analysis.get('code_index', {}).get('statistics', {})
                print(f"   Files analyzed: {stats.get('total_files', 0)}")
                print(f"   Functions found: {stats.get('total_functions', 0)}")
                print(f"   Classes found: {stats.get('total_classes', 0)}")
                print(f"   Lines of code: {stats.get('lines_of_code', 0)}")

                quality = analysis.get('metrics', {}).get('summary', {}).get('quality_score', 0)
                print(f"   Quality Score: {quality}/100")

        print("\n" + "=" * 80)
        print("🏁 TEST COMPLETE!")
        print("=" * 80)

if __name__ == "__main__":
    try:
        asyncio.run(test_free_agent())
    except KeyboardInterrupt:
        print("\n\n⛔ Interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
