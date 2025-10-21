#!/usr/bin/env python3
"""
v6.6 Comprehensive E2E Tests via WebSocket

Tests all major workflows with LLM-based routing:
1. CREATE: Build new app from scratch
2. EXTEND: Add features to existing app
3. FIX: Analyze and fix broken app

These are REAL end-to-end tests that verify the complete system.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime

import websockets


class E2ETest:
    """E2E test runner for v6.6 LLM routing"""

    def __init__(self):
        self.uri = "ws://localhost:8002/ws/chat"
        self.results = []

    async def run_test(
        self,
        test_name: str,
        query: str,
        workspace_path: str,
        expected_agents: list[str],
        timeout: int = 300
    ):
        """Run a single E2E test"""
        print(f"\n{'=' * 100}")
        print(f"🧪 E2E TEST: {test_name}")
        print(f"{'=' * 100}")
        print(f"📝 Query: {query}")
        print(f"📁 Workspace: {workspace_path}")
        print(f"🎯 Expected Agents: {' → '.join(expected_agents)}")
        print(f"{'=' * 100}\n")

        start_time = datetime.now()

        try:
            async with websockets.connect(self.uri) as websocket:
                # Connection
                conn_msg = await websocket.recv()
                print(f"🔌 Connected\n")

                # Initialize
                await websocket.send(json.dumps({
                    "type": "init",
                    "workspace_path": workspace_path
                }))
                init_msg = await websocket.recv()
                print(f"✅ Initialized\n")

                # Send query
                await websocket.send(json.dumps({
                    "type": "chat",
                    "content": query
                }))
                print(f"📤 Query sent!\n")

                # Track test progress
                routing_detected = False
                agent_proposals = []
                routing_decision = None
                agents_executed = []
                errors = []
                completed = False

                message_count = 0
                max_messages = 500  # Increased for long workflows

                while message_count < max_messages:
                    try:
                        response = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=5.0
                        )
                        data = json.loads(response)
                        message_count += 1

                        if data.get("type") == "log":
                            log_msg = data.get("message", "")

                            # LLM routing
                            if "LLM-based routing" in log_msg:
                                routing_detected = True
                                print(f"🔍 {log_msg}")

                            # Agent proposals
                            if "CAN HELP" in log_msg or "CANNOT HELP" in log_msg:
                                agent_proposals.append(log_msg)
                                print(f"  {log_msg[:100]}")

                            # Routing decision
                            if "Routing decision:" in log_msg:
                                routing_decision = log_msg
                                print(f"\n🎯 {log_msg}")

                            # Agent execution
                            if "Agent executing" in log_msg or "executing..." in log_msg:
                                # Extract agent name
                                for agent in ["research", "architect", "codesmith", "reviewfix"]:
                                    if agent in log_msg.lower():
                                        if agent not in agents_executed:
                                            agents_executed.append(agent)
                                            print(f"🚀 Agent Started: {agent}")

                            # Errors
                            if "ERROR" in log_msg or "FAIL" in log_msg:
                                errors.append(log_msg)
                                print(f"⚠️  {log_msg[:100]}")

                        elif data.get("type") == "result":
                            completed = True
                            print(f"\n✅ Workflow completed!")
                            break

                        elif data.get("type") == "error":
                            errors.append(data.get("message", "Unknown error"))
                            print(f"\n❌ Error: {data.get('message')}")
                            break

                    except asyncio.TimeoutError:
                        # Check if we've made progress
                        if completed or (routing_decision and len(agents_executed) > 0):
                            break
                        continue

                # Calculate duration
                duration = (datetime.now() - start_time).total_seconds()

                # Verify results
                success = (
                    routing_detected and
                    routing_decision is not None and
                    len(agents_executed) > 0 and
                    len(errors) == 0
                )

                # Agent match check
                agents_match = all(agent in agents_executed for agent in expected_agents)

                # Summary
                print(f"\n{'=' * 100}")
                print(f"📊 TEST SUMMARY: {test_name}")
                print(f"{'=' * 100}")
                print(f"Duration: {duration:.1f}s")
                print(f"LLM Routing: {'✅' if routing_detected else '❌'}")
                print(f"Proposals: {len(agent_proposals)}")
                print(f"Decision: {'✅' if routing_decision else '❌'}")
                print(f"Agents Executed: {', '.join(agents_executed) if agents_executed else 'None'}")
                print(f"Expected: {', '.join(expected_agents)}")
                print(f"Match: {'✅' if agents_match else '❌'}")
                print(f"Errors: {len(errors)}")
                print(f"Status: {'✅ PASS' if success and agents_match else '❌ FAIL'}")
                print(f"{'=' * 100}\n")

                result = {
                    "test_name": test_name,
                    "query": query,
                    "workspace": workspace_path,
                    "duration": duration,
                    "routing_detected": routing_detected,
                    "routing_decision": routing_decision is not None,
                    "agents_executed": agents_executed,
                    "expected_agents": expected_agents,
                    "agents_match": agents_match,
                    "errors": errors,
                    "success": success and agents_match
                }

                self.results.append(result)
                return result

        except Exception as e:
            print(f"\n❌ Test FAILED with exception: {e}")
            import traceback
            traceback.print_exc()

            result = {
                "test_name": test_name,
                "error": str(e),
                "success": False
            }
            self.results.append(result)
            return result

    async def run_all_tests(self):
        """Run all E2E tests"""
        print("\n" + "=" * 100)
        print("🎯 v6.6 COMPREHENSIVE E2E TESTS - LLM-BASED ROUTING")
        print("=" * 100)
        print("Testing: CREATE, EXTEND, FIX workflows with real WebSocket communication")
        print("=" * 100 + "\n")

        home = Path.home()

        # Test 1: CREATE - Build new app
        await self.run_test(
            test_name="CREATE_NEW_APP",
            query="Create a simple task manager API with FastAPI. Include endpoints for creating, listing, updating, and deleting tasks. Each task should have an id, title, description, and done status.",
            workspace_path=str(home / "TestApps" / "e2e_test_create"),
            expected_agents=["architect", "codesmith", "reviewfix"],
            timeout=300
        )

        await asyncio.sleep(3)

        # Test 2: EXTEND - Add features to existing app
        await self.run_test(
            test_name="EXTEND_EXISTING_APP",
            query="Erweitere die Flask App um eine /increment und /decrement Route. Der Counter soll persistent in einer JSON-Datei gespeichert werden.",
            workspace_path=str(home / "TestApps" / "e2e_test_extend"),
            expected_agents=["research", "architect", "codesmith", "reviewfix"],
            timeout=300
        )

        await asyncio.sleep(3)

        # Test 3: FIX - Analyze and fix broken app
        await self.run_test(
            test_name="FIX_BROKEN_APP",
            query="Untersuche broken_app.py und behebe alle Bugs. Die App sollte keine NameErrors, ZeroDivisionErrors oder fehlende Input-Validierung mehr haben.",
            workspace_path=str(home / "TestApps" / "e2e_test_broken"),
            expected_agents=["research", "codesmith", "reviewfix"],
            timeout=300
        )

        # Final summary
        self.print_final_summary()

    def print_final_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 100)
        print("📊 FINAL E2E TEST RESULTS - v6.6 LLM ROUTING")
        print("=" * 100)

        total = len(self.results)
        passed = sum(1 for r in self.results if r.get('success', False))
        failed = total - passed

        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total)*100:.1f}%\n")

        print("=" * 100)
        print("INDIVIDUAL TEST RESULTS:")
        print("=" * 100)

        for result in self.results:
            status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
            test_name = result.get('test_name', 'Unknown')
            duration = result.get('duration', 0)

            print(f"\n{status} | {test_name} ({duration:.1f}s)")

            if result.get('success'):
                agents = result.get('agents_executed', [])
                expected = result.get('expected_agents', [])
                print(f"  Agents: {', '.join(agents)}")
                print(f"  Expected: {', '.join(expected)}")
                print(f"  Match: {'✅' if result.get('agents_match', False) else '❌'}")
            else:
                if 'error' in result:
                    print(f"  Error: {result['error']}")
                if result.get('errors'):
                    print(f"  Workflow Errors: {len(result['errors'])}")

        print("\n" + "=" * 100)
        print("LLM ROUTING VERIFICATION:")
        print("=" * 100)

        routing_success = sum(1 for r in self.results if r.get('routing_detected', False))
        print(f"LLM Routing Detected: {routing_success}/{total} tests")
        print(f"Routing Success Rate: {(routing_success/total)*100:.1f}%")

        print("\n" + "=" * 100)

        if passed == total and routing_success == total:
            print("🎉 ALL E2E TESTS PASSED! v6.6 IS PRODUCTION READY!")
        elif passed >= total * 0.8:
            print("✅ MOST TESTS PASSED! Minor issues to address.")
        else:
            print("⚠️  SIGNIFICANT ISSUES DETECTED! Review failures.")

        print("=" * 100 + "\n")


async def main():
    """Run comprehensive E2E tests"""
    tester = E2ETest()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
