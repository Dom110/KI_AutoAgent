#!/usr/bin/env python3
"""
Test: Verbesserter Workflow mit RE-ANALYZE
"""

import asyncio
import websockets
import json
import sys

async def test_improved_workflow():
    uri = "ws://localhost:8001/ws/chat"
    workspace_path = "/Users/dominikfoert/TestApp4"  # NEUER Ordner

    print("=" * 80)
    print("🧪 TEST: Verbesserter Workflow mit RE-ANALYZE")
    print("=" * 80)

    async with websockets.connect(uri) as websocket:
        print(f"\n✅ Connected to {uri}")

        # Init
        await websocket.recv()
        await websocket.send(json.dumps({
            "type": "init",
            "workspace_path": workspace_path
        }))
        await websocket.recv()
        print(f"✅ Workspace: {workspace_path}")

        # Besserer Request mit explizitem Workflow
        request = {
            "type": "chat",
            "message": """Erstelle eine Dashboard Anwendung mit Frontend und Backend.

WICHTIG: Nach dem Build MUSS Architect den Code RE-ANALYSIEREN!

Features:
- Frontend: HTML/CSS/JavaScript Dashboard mit Echtzeit-Metriken
- Backend: Python REST API (optional)
- Dokumentation: ARCHITECTURE.md

Workflow:
1. Architect: Design Architecture
2. Research: Best Practices für Dashboards
3. CodeSmith: Build Application
4. Architect: RE-ANALYZE built code (Metrics, Quality Score, Diagrams) ← CRITICAL!
5. Reviewer: Review Code Quality
6. DocuBot: Generate ARCHITECTURE.md

Erstelle MINDESTENS eine HTML-Datei mit Dashboard UI.""",
            "mode": "auto"
        }

        print(f"\n📤 Request gesendet:")
        print("   - Frontend: HTML Dashboard")
        print("   - Backend: Optional")
        print("   - Workflow: 6 Steps mit RE-ANALYZE")

        await websocket.send(json.dumps(request))

        session_id = None
        tasks_seen = []

        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=600.0)
                data = json.loads(response)
                msg_type = data.get('type')

                if 'session_id' in data:
                    session_id = data['session_id']

                if msg_type == 'architecture_proposal':
                    # Zeige Tasks
                    proposal = data.get('proposal', {})
                    if isinstance(proposal, dict):
                        tasks = proposal.get('tasks', [])
                        print(f"\n📋 Orchestrator hat {len(tasks)} Tasks erstellt:")
                        for i, task in enumerate(tasks, 1):
                            agent = task.get('agent', 'unknown')
                            desc = task.get('task', 'N/A')
                            print(f"   {i}. {agent}: {desc[:60]}...")
                            tasks_seen.append({'agent': agent, 'task': desc})

                    # Auto-approve
                    await websocket.send(json.dumps({
                        "type": "architecture_approval",
                        "session_id": session_id,
                        "decision": "approved"
                    }))
                    print("   ✅ APPROVED")

                elif msg_type == 'agent_progress':
                    agent = data.get('agent', 'unknown')
                    content = data.get('content', '')
                    print(f"⏳ {agent}: {content[:80]}...")

                elif msg_type == 'workflow_complete':
                    print("\n" + "=" * 80)
                    print("✅ WORKFLOW COMPLETE!")
                    print("=" * 80)
                    break

                elif msg_type == 'error':
                    print(f"\n❌ {data.get('error')}")
                    break

            except asyncio.TimeoutError:
                print("\n⏱️  Timeout")
                break

        # Validate workflow
        print("\n" + "=" * 80)
        print("🔍 WORKFLOW VALIDATION:")
        print("=" * 80)

        architect_count = sum(1 for t in tasks_seen if t['agent'] == 'architect')
        has_research = any(t['agent'] == 'research' for t in tasks_seen)
        has_reviewer = any(t['agent'] == 'reviewer' for t in tasks_seen)
        has_docbot = any(t['agent'] == 'docbot' for t in tasks_seen)

        print(f"Architect calls: {architect_count} (erwartet: 2) {'✅' if architect_count >= 2 else '❌'}")
        print(f"Research included: {has_research} {'✅' if has_research else '❌'}")
        print(f"Reviewer included: {has_reviewer} {'✅' if has_reviewer else '❌'}")
        print(f"DocBot included: {has_docbot} {'✅' if has_docbot else '❌'}")

        # Check files
        import os
        if os.path.exists(workspace_path):
            analysis_file = os.path.join(workspace_path, ".ki_autoagent_ws", "system_analysis.json")
            if os.path.exists(analysis_file):
                with open(analysis_file) as f:
                    analysis = json.load(f)
                    stats = analysis.get('code_index', {}).get('statistics', {})
                    print(f"\n📊 ANALYSIS RESULTS:")
                    print(f"   Files: {stats.get('total_files', 0)}")
                    print(f"   Functions: {stats.get('total_functions', 0)}")
                    print(f"   Classes: {stats.get('total_classes', 0)}")
                    print(f"   Quality: {analysis.get('metrics', {}).get('summary', {}).get('quality_score', 0)}/100")

        print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test_improved_workflow())
