#!/usr/bin/env python3
"""
RE-ANALYSE: Scanne die erstellten Python Files in TestApp2
"""

import asyncio
import websockets
import json
import sys

async def analyze_testapp2():
    uri = "ws://localhost:8001/ws/chat"
    workspace_path = "/Users/dominikfoert/TestApp2"

    print("🔍 RE-ANALYSE: Scanne TestApp2 Python Files")

    async with websockets.connect(uri) as websocket:
        # Init
        await websocket.recv()
        await websocket.send(json.dumps({
            "type": "init",
            "workspace_path": workspace_path
        }))
        await websocket.recv()

        # Request ANALYSIS ONLY
        await websocket.send(json.dumps({
            "type": "chat",
            "message": "Analyze TestApp2 architecture and code quality",
            "mode": "auto"
        }))

        session_id = None
        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=180.0)
                data = json.loads(response)
                msg_type = data.get('type')

                if 'session_id' in data:
                    session_id = data['session_id']

                if msg_type == 'architecture_proposal':
                    # Auto-approve
                    await websocket.send(json.dumps({
                        "type": "architecture_approval",
                        "session_id": session_id,
                        "decision": "approved"
                    }))
                    print("✅ Approved")

                elif msg_type == 'workflow_complete':
                    print("✅ Analysis complete!")
                    break

                elif msg_type == 'error':
                    print(f"❌ {data.get('error')}")
                    break

            except asyncio.TimeoutError:
                break

        # Show results
        import os
        analysis_file = os.path.join(workspace_path, ".ki_autoagent_ws", "system_analysis.json")
        if os.path.exists(analysis_file):
            with open(analysis_file) as f:
                analysis = json.load(f)
                stats = analysis.get('code_index', {}).get('statistics', {})
                print(f"\n📊 ERGEBNIS:")
                print(f"   Files: {stats.get('total_files', 0)}")
                print(f"   Functions: {stats.get('total_functions', 0)}")
                print(f"   Classes: {stats.get('total_classes', 0)}")
                print(f"   LOC: {stats.get('lines_of_code', 0)}")

                quality = analysis.get('metrics', {}).get('summary', {}).get('quality_score', 0)
                print(f"   Quality: {quality}/100")

if __name__ == "__main__":
    asyncio.run(analyze_testapp2())
