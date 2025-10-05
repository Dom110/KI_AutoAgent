#!/usr/bin/env python3
"""
Manuell RE-ANALYZE für TestApp4 triggern
"""

import asyncio
import websockets
import json

async def reanalyze():
    uri = "ws://localhost:8001/ws/chat"
    workspace = "/Users/dominikfoert/TestApp4"

    print("🔍 Triggering RE-ANALYZE for TestApp4...")

    async with websockets.connect(uri) as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "init", "workspace_path": workspace}))
        await ws.recv()

        # Simple analyze request
        await ws.send(json.dumps({
            "type": "chat",
            "message": "Analyze the TestApp4 codebase",
            "mode": "auto"
        }))

        session_id = None
        while True:
            try:
                resp = await asyncio.wait_for(ws.recv(), timeout=120.0)
                data = json.loads(resp)

                if 'session_id' in data:
                    session_id = data['session_id']

                if data.get('type') == 'architecture_proposal':
                    await ws.send(json.dumps({
                        "type": "architecture_approval",
                        "session_id": session_id,
                        "decision": "approved"
                    }))
                    print("✅ Approved")

                elif data.get('type') == 'workflow_complete':
                    print("✅ Analysis complete")
                    break

            except asyncio.TimeoutError:
                break

    # Show results
    import os
    analysis_file = os.path.join(workspace, ".ki_autoagent_ws", "system_analysis.json")
    if os.path.exists(analysis_file):
        data = json.load(open(analysis_file))
        stats = data['code_index']['statistics']
        print(f"\n📊 RESULTS:")
        print(f"   Timestamp: {data['timestamp']}")
        print(f"   Files: {stats['total_files']}")
        print(f"   Functions: {stats['total_functions']}")
        print(f"   Classes: {stats['total_classes']}")
        print(f"   LOC: {stats['lines_of_code']}")
        print(f"   Quality: {data['metrics']['summary']['quality_score']}/100")

asyncio.run(reanalyze())
