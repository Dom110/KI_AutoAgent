#!/usr/bin/env python3
"""
v7.0 E2E Tests for Supervisor Pattern via WebSocket

Tests the new supervisor-based architecture:
1. CREATE: Test supervisor orchestration for new app
2. EXPLAIN: Test research → responder flow
3. FIX WITH RESEARCH-FIX LOOP: Test iterative fixing
4. LOW CONFIDENCE: Test HITL activation

These tests verify the Supervisor Pattern is working correctly.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime

import websockets


class E2ETestV7:
    """E2E test runner for v7.0 Supervisor Pattern"""

    def __init__(self):
        self.uri = "ws://localhost:8002/ws/chat"
        self.results = []

    async def run_test(
        self,
        test_name: str,
        query: str,
        workspace_path: str,
        expected_features: dict,
        timeout: int = 300
    ):
        """
        Run a single E2E test for v7.0

        expected_features: {
            "supervisor_decisions": int,  # Min number of supervisor decisions
            "agents_used": list[str],     # Agents that should be invoked
            "research_requests": bool,    # Should research be requested?
            "responder_output": bool,     # Should responder format output?
            "hitl_activation": bool,      # Should HITL be activated?
        }
        """
        print(f"\n{'=' * 100}")
        print(f"🧪 v7.0 E2E TEST: {test_name}")
        print(f"{'=' * 100}")
        print(f"📝 Query: {query}")
        print(f"📁 Workspace: {workspace_path}")
        print(f"🎯 Expected Features: {expected_features}")
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

                # Track test progress for v7.0
                supervisor_decisions = 0
                agents_invoked = []
                research_requests = []
                responder_output = False
                hitl_activated = False
                errors = []
                completed = False
                command_routing = []  # Track Command(goto=...) calls

                message_count = 0
                max_messages = 500
                silent_count = 0
                max_silent = 10  # Allow 10 consecutive timeouts before giving up

                while message_count < max_messages:
                    try:
                        response = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=3.0  # Reduced timeout but more retries
                        )
                        data = json.loads(response)
                        message_count += 1
                        silent_count = 0  # Reset silent counter when we get a message

                        # DEBUG: Show all messages for first 20 messages
                        if message_count <= 20:
                            print(f"[MSG #{message_count}] Type: {data.get('type')} | Content: {str(data)[:150]}...")

                        if data.get("type") == "log":
                            log_msg = data.get("message", "")

                            # Supervisor decisions
                            if "SUPERVISOR NODE" in log_msg or "Supervisor decision" in log_msg:
                                supervisor_decisions += 1
                                print(f"🎯 Supervisor Decision #{supervisor_decisions}: {log_msg[:100]}")

                            # Command routing (v7.0 specific)
                            if "Command(goto=" in log_msg or "Route to" in log_msg:
                                command_routing.append(log_msg)
                                print(f"  ➡️ {log_msg[:100]}")

                            # Agent execution (from logs)
                            for agent in ["research", "architect", "codesmith", "reviewfix", "responder", "hitl"]:
                                if f"{agent.upper()} NODE" in log_msg or f"{agent}Agent" in log_msg:
                                    if agent not in agents_invoked:
                                        agents_invoked.append(agent)
                                        print(f"🚀 Agent Started: {agent}")
                        
                        # FIX: Also detect agent_event messages (v7.0 MCP events)
                        elif data.get("type") == "agent_event":
                            agent_name = data.get("agent", "")
                            if agent_name:
                                if agent_name not in agents_invoked:
                                    agents_invoked.append(agent_name)
                                    print(f"🚀 Agent Started (MCP Event): {agent_name}")
                        
                        # FIX: Detect supervisor_event messages for decisions
                        elif data.get("type") == "supervisor_event":
                            supervisor_decisions += 1
                            decision = data.get("decision", "")
                            print(f"🎯 Supervisor Decision #{supervisor_decisions}: {decision[:100]}")
                        
                        # FIX: Detect agents from progress messages (node field)
                        elif data.get("type") == "progress":
                            node_name = data.get("node", "")
                            if node_name and node_name not in agents_invoked:
                                agents_invoked.append(node_name)
                                print(f"🚀 Agent Started (Progress): {node_name}")
                        
                        # Continue with log type checks for other metrics
                        if data.get("type") == "log":
                            log_msg = data.get("message", "")
                            
                            # Research requests (v7.0 feature)
                            if "needs_research: True" in log_msg or "Requesting research" in log_msg:
                                research_requests.append(log_msg)
                                print(f"  📚 Research Request: {log_msg[:100]}")

                            # Research-Fix Loop detection
                            if "Research-Fix Loop" in log_msg or ("reviewfix" in agents_invoked and "research" in research_requests):
                                print(f"  🔄 Research-Fix Loop detected!")

                            # Responder output
                            if "RESPONDER NODE" in log_msg or "Formatting user response" in log_msg:
                                responder_output = True
                                print(f"  💬 Responder formatting output")

                            # HITL activation
                            if "HITL NODE" in log_msg or "Low confidence" in log_msg:
                                hitl_activated = True
                                print(f"  👤 HITL activated (low confidence)")

                            # Self-invocation detection (v7.0 feature)
                            if "Self-invocation" in log_msg:
                                print(f"  🔄 Self-invocation detected: {log_msg[:100]}")

                            # Errors
                            if "ERROR" in log_msg or "FAIL" in log_msg:
                                errors.append(log_msg)
                                print(f"⚠️  {log_msg[:100]}")

                        elif data.get("type") == "result":
                            completed = True
                            print(f"\n✅ Workflow completed!")

                            # Check if result was formatted by responder
                            result_content = data.get("content", "")
                            if "Generated with Claude Code" in result_content or "KI AutoAgent v7.0" in result_content:
                                print(f"  ✅ Response formatted by Responder")
                            # DON'T break yet - wait for more messages (especially progress updates)

                        elif data.get("type") == "error":
                            errors.append(data.get("message", "Unknown error"))
                            print(f"\n❌ Error: {data.get('message')}")
                            # Keep collecting messages after error too

                    except asyncio.TimeoutError:
                        silent_count += 1
                        # Only exit after multiple consecutive timeouts
                        if completed and silent_count >= max_silent:
                            break
                        if not completed and silent_count >= max_silent:
                            break
                        continue

                # Calculate duration
                duration = (datetime.now() - start_time).total_seconds()

                # Verify v7.0 features
                features_verified = {
                    "supervisor_decisions": supervisor_decisions >= expected_features.get("supervisor_decisions", 1),
                    "agents_match": all(agent in agents_invoked for agent in expected_features.get("agents_used", [])),
                    "research_requests": (len(research_requests) > 0) == expected_features.get("research_requests", False),
                    "responder_output": responder_output == expected_features.get("responder_output", True),
                    "hitl_activation": hitl_activated == expected_features.get("hitl_activation", False),
                    "command_routing": len(command_routing) > 0,  # v7.0 uses Command routing
                }

                success = all(features_verified.values()) and len(errors) == 0

                # Summary
                print(f"\n{'=' * 100}")
                print(f"📊 v7.0 TEST SUMMARY: {test_name}")
                print(f"{'=' * 100}")
                print(f"Duration: {duration:.1f}s")
                print(f"Supervisor Decisions: {supervisor_decisions} (expected ≥{expected_features.get('supervisor_decisions', 1)})")
                print(f"Command Routings: {len(command_routing)}")
                print(f"Agents Invoked: {', '.join(agents_invoked) if agents_invoked else 'None'}")
                print(f"Expected Agents: {', '.join(expected_features.get('agents_used', []))}")
                print(f"Research Requests: {len(research_requests)} {'✅' if features_verified['research_requests'] else '❌'}")
                print(f"Responder Output: {'✅' if responder_output else '❌'}")
                print(f"HITL Activated: {'✅' if hitl_activated else '❌' if expected_features.get('hitl_activation') else 'N/A'}")
                print(f"Errors: {len(errors)}")
                print(f"\nFeature Verification:")
                for feature, verified in features_verified.items():
                    print(f"  {feature}: {'✅' if verified else '❌'}")
                print(f"\nStatus: {'✅ PASS' if success else '❌ FAIL'}")
                print(f"{'=' * 100}\n")

                result = {
                    "test_name": test_name,
                    "query": query,
                    "workspace": workspace_path,
                    "duration": duration,
                    "supervisor_decisions": supervisor_decisions,
                    "agents_invoked": agents_invoked,
                    "research_requests": len(research_requests),
                    "command_routing": len(command_routing),
                    "responder_output": responder_output,
                    "hitl_activated": hitl_activated,
                    "features_verified": features_verified,
                    "errors": errors,
                    "success": success
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
        """Run all v7.0 E2E tests"""
        print("\n" + "=" * 100)
        print("🎯 v7.0 E2E TESTS - SUPERVISOR PATTERN")
        print("=" * 100)
        print("Testing: Supervisor orchestration, Research-Fix Loop, HITL activation")
        print("Key Features: Command-based routing, needs_research flag, self-invocation")
        print("=" * 100 + "\n")

        home = Path.home()

        # Test 1: CREATE with full workflow
        await self.run_test(
            test_name="CREATE_WITH_SUPERVISOR",
            query="Create a simple REST API with FastAPI that manages a todo list. Include CRUD operations.",
            workspace_path=str(home / "TestApps" / "e2e_v7_create"),
            expected_features={
                "supervisor_decisions": 4,  # supervisor → research → architect → codesmith → reviewfix → responder
                "agents_used": ["research", "architect", "codesmith", "reviewfix", "responder"],
                "research_requests": False,  # Initial research from supervisor, not agent request
                "responder_output": True,
                "hitl_activation": False
            },
            timeout=300
        )

        await asyncio.sleep(3)

        # Test 2: EXPLAIN with research → responder flow
        await self.run_test(
            test_name="EXPLAIN_WITH_RESEARCH",
            query="Explain how async/await works in Python and provide best practices.",
            workspace_path=str(home / "TestApps" / "e2e_v7_explain"),
            expected_features={
                "supervisor_decisions": 2,  # supervisor → research → responder
                "agents_used": ["research", "responder"],
                "research_requests": False,
                "responder_output": True,
                "hitl_activation": False
            },
            timeout=180
        )

        await asyncio.sleep(3)

        # Test 3: FIX with Research-Fix Loop
        await self.run_test(
            test_name="FIX_WITH_RESEARCH_LOOP",
            query="Fix the ImportError in main.py. The FastAPI import is not working correctly.",
            workspace_path=str(home / "TestApps" / "e2e_v7_fix"),
            expected_features={
                "supervisor_decisions": 5,  # More decisions due to research-fix loop
                "agents_used": ["research", "codesmith", "reviewfix"],
                "research_requests": True,  # ReviewFix should request research for import fix
                "responder_output": True,
                "hitl_activation": False
            },
            timeout=300
        )

        await asyncio.sleep(3)

        # Test 4: Complex task with self-invocation
        await self.run_test(
            test_name="COMPLEX_WITH_SELF_INVOCATION",
            query="Refactor the existing codebase to use proper design patterns, add comprehensive error handling, and improve performance.",
            workspace_path=str(home / "TestApps" / "e2e_v7_complex"),
            expected_features={
                "supervisor_decisions": 6,  # Multiple iterations expected
                "agents_used": ["research", "architect", "codesmith", "reviewfix", "responder"],
                "research_requests": True,  # Multiple research requests expected
                "responder_output": True,
                "hitl_activation": False  # Unless confidence drops
            },
            timeout=400
        )

        # Final summary
        self.print_final_summary()

    def print_final_summary(self):
        """Print comprehensive test summary for v7.0"""
        print("\n" + "=" * 100)
        print("📊 FINAL v7.0 E2E TEST RESULTS - SUPERVISOR PATTERN")
        print("=" * 100)

        total = len(self.results)
        passed = sum(1 for r in self.results if r.get('success', False))
        failed = total - passed

        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total)*100:.1f}%" if total > 0 else "N/A")

        print("\n" + "=" * 100)
        print("SUPERVISOR PATTERN VERIFICATION:")
        print("=" * 100)

        # v7.0 specific metrics
        avg_supervisor_decisions = sum(r.get('supervisor_decisions', 0) for r in self.results) / total if total > 0 else 0
        avg_command_routings = sum(r.get('command_routing', 0) for r in self.results) / total if total > 0 else 0
        research_request_tests = sum(1 for r in self.results if r.get('research_requests', 0) > 0)
        responder_success = sum(1 for r in self.results if r.get('responder_output', False))

        print(f"Average Supervisor Decisions: {avg_supervisor_decisions:.1f}")
        print(f"Average Command Routings: {avg_command_routings:.1f}")
        print(f"Tests with Research Requests: {research_request_tests}/{total}")
        print(f"Responder Output Success: {responder_success}/{total}")

        print("\n" + "=" * 100)
        print("INDIVIDUAL TEST RESULTS:")
        print("=" * 100)

        for result in self.results:
            status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
            test_name = result.get('test_name', 'Unknown')
            duration = result.get('duration', 0)

            print(f"\n{status} | {test_name} ({duration:.1f}s)")

            if result.get('success'):
                print(f"  Supervisor Decisions: {result.get('supervisor_decisions', 0)}")
                print(f"  Agents: {', '.join(result.get('agents_invoked', []))}")
                print(f"  Command Routings: {result.get('command_routing', 0)}")
                print(f"  Research Requests: {result.get('research_requests', 0)}")

                features = result.get('features_verified', {})
                if features:
                    print("  Features Verified:")
                    for feature, verified in features.items():
                        print(f"    - {feature}: {'✅' if verified else '❌'}")
            else:
                if 'error' in result:
                    print(f"  Error: {result['error']}")
                if result.get('errors'):
                    print(f"  Workflow Errors: {len(result['errors'])}")

        print("\n" + "=" * 100)

        if passed == total:
            print("🎉 ALL v7.0 E2E TESTS PASSED! SUPERVISOR PATTERN IS WORKING!")
        elif passed >= total * 0.8:
            print("✅ MOST TESTS PASSED! Minor issues to address.")
        else:
            print("⚠️  SIGNIFICANT ISSUES DETECTED! Review supervisor implementation.")

        print("=" * 100 + "\n")


async def prepare_test_workspaces():
    """Prepare test workspaces with initial files"""
    import os
    home = Path.home()
    test_dir = home / "TestApps"
    test_dir.mkdir(exist_ok=True)

    # Prepare workspace for FIX test with broken import
    fix_workspace = test_dir / "e2e_v7_fix"
    fix_workspace.mkdir(exist_ok=True)

    broken_file = fix_workspace / "main.py"
    broken_file.write_text("""# Broken FastAPI import
import FastAPI  # This is wrong!

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
""")

    # Prepare workspace for COMPLEX test
    complex_workspace = test_dir / "e2e_v7_complex"
    complex_workspace.mkdir(exist_ok=True)

    legacy_file = complex_workspace / "legacy_app.py"
    legacy_file.write_text("""# Legacy code that needs refactoring
def process_data(data):
    result = []
    for item in data:
        try:
            # No error handling
            value = int(item)
            result.append(value * 2)
        except:
            pass  # Silent failure
    return result

# Global state - bad practice
counter = 0

def increment():
    global counter
    counter = counter + 1  # Could use +=
    return counter

# No input validation
def divide(a, b):
    return a / b  # No zero check!
""")

    print("✅ Test workspaces prepared\n")


async def main():
    """Run v7.0 E2E tests"""
    # Prepare test workspaces
    await prepare_test_workspaces()

    # Run tests
    tester = E2ETestV7()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())