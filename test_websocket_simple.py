#!/usr/bin/env python3
"""
Einfacher WebSocket Test - Prüft ob ReviewFix Build Validation läuft
"""
import asyncio
import json
import sys
from pathlib import Path

try:
    import websockets
except ImportError:
    print("❌ websockets nicht installiert")
    print("   Installiere mit: pip install websockets")
    sys.exit(1)

WS_URL = "ws://localhost:8002/ws/chat"
WORKSPACE = Path.home() / "TestApps" / "ws_test_build_validation"

async def test_websocket():
    """Teste WebSocket und Build Validation"""

    print("=" * 80)
    print("🧪 WEBSOCKET BUILD VALIDATION TEST")
    print("=" * 80)
    print(f"Server: {WS_URL}")
    print(f"Workspace: {WORKSPACE}")

    # Create workspace
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    print("✅ Workspace erstellt")

    try:
        print(f"\n📡 Verbinde mit {WS_URL}...")
        async with websockets.connect(WS_URL, ping_timeout=None) as ws:
            print("✅ Verbindung erfolgreich!")

            # 1. Welcome message
            msg = await ws.recv()
            data = json.loads(msg)
            print(f"📨 {data.get('type')}: {data.get('message', '')[:60]}...")

            # 2. Init
            print(f"\n📤 Sende Init-Message...")
            await ws.send(json.dumps({
                "type": "init",
                "workspace_path": str(WORKSPACE)
            }))

            msg = await ws.recv()
            data = json.loads(msg)
            print(f"✅ Init erfolgreich: {data.get('type')}")

            # 3. Simple task
            print(f"\n🚀 Sende Mini-Task (Counter App)...")
            await ws.send(json.dumps({
                "type": "chat",
                "message": """Create a minimal React TypeScript counter app.

Files needed:
- package.json (React 18, TypeScript, Vite)
- tsconfig.json
- index.html
- src/main.tsx (with ErrorBoundary)
- src/App.tsx (simple counter with useState)

Keep it minimal - just testing build validation."""
            }))

            print(f"👀 Warte auf Antworten...")
            print("-" * 80)

            workflow_complete = False
            timeout = 600  # 10 minutes
            start = asyncio.get_event_loop().time()

            while True:
                try:
                    # Check timeout
                    if asyncio.get_event_loop().time() - start > timeout:
                        print(f"\n⏰ Timeout nach {timeout}s")
                        break

                    # Receive message
                    msg = await asyncio.wait_for(ws.recv(), timeout=60)
                    data = json.loads(msg)
                    msg_type = data.get("type")

                    # Log important messages
                    if msg_type == "status":
                        status = data.get("status", "")
                        message = data.get("message", "")
                        print(f"📊 Status: {status} - {message[:80]}")

                    elif msg_type == "result":
                        print(f"\n✅ WORKFLOW COMPLETE!")
                        quality = data.get("quality_score", "N/A")
                        exec_time = data.get("execution_time", "N/A")
                        print(f"   Quality Score: {quality}")
                        print(f"   Execution Time: {exec_time}s")
                        workflow_complete = True
                        break

                    elif msg_type == "error":
                        print(f"❌ Error: {data.get('message')}")
                        break

                except asyncio.TimeoutError:
                    print(f"⏱️  60s vergangen, warte weiter...")
                    continue

        # Check server logs for build validation
        print(f"\n" + "=" * 80)
        print(f"🔍 PRÜFE SERVER LOGS FÜR BUILD VALIDATION")
        print("=" * 80)

        import subprocess
        result = subprocess.run(
            ['tail', '-100', '/tmp/v6_server.log'],
            capture_output=True,
            text=True
        )

        logs = result.stdout

        # Check for build validation markers
        checks = {
            "ReviewFix START": "🔬 === REVIEWFIX AGENT START ===" in logs,
            "TypeScript Check": "Running TypeScript compilation check" in logs,
            "Build Status": "TypeScript compilation" in logs,
            "Project Type": "Project Type: TypeScript" in logs,
            "Quality Threshold": "Quality Threshold: 0.90" in logs,
            "ReviewFix END": "🔬 === REVIEWFIX AGENT END" in logs
        }

        print(f"\nBuild Validation Checks:")
        for check, passed in checks.items():
            icon = "✅" if passed else "❌"
            print(f"   {icon} {check}")

        # Summary
        print(f"\n" + "=" * 80)
        print(f"📊 TEST ERGEBNIS")
        print("=" * 80)

        if workflow_complete:
            print(f"✅ WebSocket-Kommunikation: ERFOLGREICH")
        else:
            print(f"⚠️  WebSocket-Kommunikation: TIMEOUT")

        validation_ran = checks["TypeScript Check"] or checks["Build Status"]
        if validation_ran:
            print(f"✅ Build Validation: LÄUFT")
        else:
            print(f"❌ Build Validation: NICHT ERKANNT")

        # Check generated files
        files = list(WORKSPACE.rglob("*.ts")) + list(WORKSPACE.rglob("*.tsx"))
        print(f"\n📁 Generierte TypeScript-Dateien: {len(files)}")
        for f in files[:10]:
            rel = f.relative_to(WORKSPACE)
            print(f"   - {rel}")

        # Final verdict
        print(f"\n" + "=" * 80)
        if workflow_complete and validation_ran:
            print(f"🎉 TEST ERFOLGREICH!")
            print(f"   ✅ Server läuft")
            print(f"   ✅ WebSocket funktioniert")
            print(f"   ✅ Build Validation läuft")
            return True
        else:
            print(f"⚠️  TEST TEILWEISE ERFOLGREICH")
            if not workflow_complete:
                print(f"   ⚠️  Workflow nicht vollständig")
            if not validation_ran:
                print(f"   ⚠️  Build Validation nicht erkannt")
            return False

    except Exception as e:
        print(f"\n❌ TEST FEHLGESCHLAGEN: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_websocket())
    sys.exit(0 if success else 1)
