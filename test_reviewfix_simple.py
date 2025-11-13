#!/usr/bin/env python3
"""
Einfacher ReviewFix E2E Test
Testet, ob ReviewFix korrekt via claude_generate aufgerufen wird
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

import websockets


class SimpleReviewFixTest:
    def __init__(self):
        self.uri = "ws://localhost:8002/ws/chat"
        self.events = []
        self.start_time = datetime.now()

    def elapsed(self):
        return (datetime.now() - self.start_time).total_seconds()

    def log(self, msg):
        elapsed = self.elapsed()
        print(f"[{elapsed:7.2f}s] {msg}")

    async def test_reviewfix_workflow(self):
        """Test ReviewFix agent"""
        try:
            self.log("🚀 Verbinde mit Server...")
            async with websockets.connect(self.uri, timeout=10) as ws:
                self.log("✅ Connected!")

                # Wait for connection message
                msg = await ws.recv()
                data = json.loads(msg)
                self.log(f"📨 Connected: {data.get('message', data)}")

                # Initialize
                self.log("⏳ Sende init...")
                await ws.send(json.dumps({
                    "type": "init",
                    "workspace_path": str(Path(__file__).parent / "temp_test_workspace")
                }))

                msg = await ws.recv()
                data = json.loads(msg)
                self.log(f"✅ Initialized: {data.get('message', data)}")

                # Send a test query that needs fixing
                query = """Create a Python function with intentional bugs:

def calculate_sum(numbers):
    # Bug 1: Missing type check
    # Bug 2: No error handling
    result = 0
    for n in numbers
        result += n
    return result

Then ReviewFix should:
1. Read the file
2. Run tests to identify bugs
3. Fix the syntax error (missing colon)
4. Validate the fix works
"""

                self.log("📤 Sende Query...")
                await ws.send(json.dumps({
                    "type": "chat",
                    "content": query
                }))

                # Collect events
                reviewfix_called = False
                validation_passed = None
                workflow_complete = False
                timeout_counter = 0
                max_timeout = 300  # 5 minutes

                while not workflow_complete and timeout_counter < max_timeout:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                        data = json.loads(msg)
                        self.events.append(data)

                        event_type = data.get("type", "unknown")

                        if event_type == "status":
                            status = data.get("message", "")
                            self.log(f"📊 Status: {status[:80]}")

                        elif event_type == "supervisor_decision":
                            agent = data.get("next_agent", "")
                            self.log(f"🎯 Supervisor → {agent}")
                            if agent == "reviewfix":
                                reviewfix_called = True
                                self.log("✨ ReviewFix wurde aufgerufen!")

                        elif event_type == "agent_progress":
                            agent = data.get("agent", "")
                            progress = data.get("progress", {})
                            msg = progress.get("message", "")
                            self.log(f"⚙️  {agent}: {msg[:80]}")

                        elif event_type == "workflow_complete":
                            workflow_complete = True
                            result = data.get("result", {})
                            validation_passed = result.get("validation_passed")
                            self.log(f"✅ Workflow Complete!")
                            self.log(f"   Validation Passed: {validation_passed}")
                            if "summary" in result:
                                self.log(f"   Summary: {result['summary'][:100]}")

                        elif event_type == "error":
                            error = data.get("error", {})
                            self.log(f"❌ Error: {error.get('message', error)}")
                            workflow_complete = True

                        elif event_type == "mcp_progress":
                            message = data.get("message", "")
                            if "ReviewFix" in message or "reviewfix" in message or "validation" in message:
                                self.log(f"🔍 MCP: {message[:80]}")

                    except asyncio.TimeoutError:
                        timeout_counter += 1
                        self.log(f"⏳ Timeout {timeout_counter}/300...")
                        continue
                    except Exception as e:
                        self.log(f"⚠️  Parse error: {e}")
                        continue

                # Print summary
                self.log("\n" + "=" * 80)
                self.log("📊 TEST SUMMARY")
                self.log("=" * 80)
                self.log(f"Total events: {len(self.events)}")
                self.log(f"ReviewFix called: {'✅ YES' if reviewfix_called else '❌ NO'}")
                self.log(f"Validation passed: {validation_passed}")
                self.log(f"Workflow complete: {'✅ YES' if workflow_complete else '❌ NO'}")

                # Print agent timeline
                self.log("\n📈 Agent Timeline:")
                for i, event in enumerate(self.events):
                    if event.get("type") in ["supervisor_decision", "agent_progress"]:
                        agent = event.get("next_agent") or event.get("agent", "?")
                        self.log(f"  {i:3d}. {agent}")

                # Results
                if reviewfix_called and workflow_complete:
                    self.log("\n🎉 TEST PASSED - ReviewFix wurde aufgerufen!")
                    return True
                else:
                    self.log("\n❌ TEST FAILED")
                    if not reviewfix_called:
                        self.log("   - ReviewFix wurde NICHT aufgerufen")
                    if not workflow_complete:
                        self.log("   - Workflow wurde nicht abgeschlossen")
                    return False

        except Exception as e:
            self.log(f"❌ FATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    print("\n" + "=" * 80)
    print("🧪 SIMPLE REVIEWFIX E2E TEST")
    print("=" * 80 + "\n")

    test = SimpleReviewFixTest()
    result = await test.test_reviewfix_workflow()

    print("\n" + "=" * 80)
    if result:
        print("✅ TEST ERFOLGREICH")
    else:
        print("❌ TEST FEHLGESCHLAGEN")
    print("=" * 80)

    sys.exit(0 if result else 1)


if __name__ == "__main__":
    asyncio.run(main())