#!/usr/bin/env python3
"""
v6.6 LLM-Based Routing - WebSocket Test

Tests the new LLM-based routing system that uses GPT-4o-mini
to evaluate which agents can help with a task.

Critical: This tests TRUE semantic understanding, not keyword matching!
"""

import asyncio
import json
from pathlib import Path

import websockets


async def test_llm_routing(query: str, workspace_path: str, test_name: str):
    """Test LLM-based routing for a specific query."""
    print(f"\n{'=' * 80}")
    print(f"🧪 TEST: {test_name}")
    print(f"{'=' * 80}")
    print(f"📝 Query: {query}")
    print(f"📁 Workspace: {workspace_path}")
    print(f"{'=' * 80}\n")

    uri = "ws://localhost:8002/ws/chat"

    try:
        async with websockets.connect(uri) as websocket:
            # Wait for connection
            response = await websocket.recv()
            conn_data = json.loads(response)
            print(f"🔌 Connected: {conn_data.get('message', 'N/A')}\n")

            # Send INIT
            await websocket.send(json.dumps({
                "type": "init",
                "workspace_path": workspace_path
            }))

            init_response = await websocket.recv()
            init_data = json.loads(init_response)
            print(f"✅ Initialized: {init_data.get('message', 'N/A')}\n")

            # Send query
            await websocket.send(json.dumps({
                "type": "chat",
                "content": query
            }))
            print(f"📤 Query sent!\n")

            # Collect routing logs
            llm_routing_logs = []
            agent_proposals = []
            routing_decision = None
            agent_started = None

            message_count = 0
            max_messages = 100  # Stop after 100 messages to prevent infinite loop

            while message_count < max_messages:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(response)
                    message_count += 1

                    if data.get("type") == "log":
                        log_msg = data.get("message", "")

                        # Capture LLM routing logs
                        if "LLM-based routing" in log_msg:
                            print(f"🔍 {log_msg}")
                            llm_routing_logs.append(log_msg)

                        # Capture agent proposals
                        if "CAN HELP" in log_msg or "CANNOT HELP" in log_msg:
                            print(f"  {log_msg}")
                            agent_proposals.append(log_msg)

                        # Capture routing decision
                        if "Routing decision:" in log_msg:
                            print(f"🎯 {log_msg}")
                            routing_decision = log_msg

                        if "Agents:" in log_msg and routing_decision:
                            print(f"   {log_msg}")

                        if "Reasoning:" in log_msg and routing_decision:
                            print(f"   {log_msg}")

                        if "Confidence:" in log_msg and routing_decision:
                            print(f"   {log_msg}")

                        # Agent execution started
                        if "Agent executing" in log_msg or "executing" in log_msg.lower():
                            print(f"🚀 {log_msg}")
                            agent_started = log_msg

                    elif data.get("type") == "result":
                        print(f"\n✅ Result received!")
                        break

                    elif data.get("type") == "error":
                        print(f"\n❌ Error: {data.get('message')}")
                        break

                except asyncio.TimeoutError:
                    # No more messages
                    if agent_proposals and routing_decision:
                        break
                    continue

            # Summary
            print(f"\n{'=' * 80}")
            print(f"📊 LLM ROUTING ANALYSIS - {test_name}")
            print(f"{'=' * 80}")
            print(f"LLM Routing Detected: {'✅ YES' if llm_routing_logs else '❌ NO'}")
            print(f"Agent Proposals: {len(agent_proposals)}")
            print(f"Routing Decision: {'✅ YES' if routing_decision else '❌ NO'}")
            print(f"Agent Started: {'✅ YES' if agent_started else '❌ NO'}")
            print(f"{'=' * 80}\n")

            return {
                "test_name": test_name,
                "llm_routing": len(llm_routing_logs) > 0,
                "proposals_count": len(agent_proposals),
                "routing_decision": routing_decision is not None,
                "agent_started": agent_started is not None,
                "success": (len(llm_routing_logs) > 0 and
                           routing_decision is not None and
                           agent_started is not None)
            }

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "test_name": test_name,
            "error": str(e),
            "success": False
        }


async def main():
    """Run v6.6 LLM routing tests."""
    print("\n" + "=" * 80)
    print("🎯 v6.6 LLM-BASED ROUTING - WEBSOCKET TESTS")
    print("=" * 80)
    print("Testing TRUE semantic understanding with GPT-4o-mini")
    print("=" * 80 + "\n")

    workspace_path = str(Path.home() / "TestApps" / "v6_6_llm_routing_test")

    # Test 1: German query that failed in v6.5
    test1 = await test_llm_routing(
        query="Untersuche die App im Workspace und erkläre mir die Architektur",
        workspace_path=workspace_path,
        test_name="german_explain_query"
    )

    await asyncio.sleep(2)

    # Test 2: CREATE workflow
    test2 = await test_llm_routing(
        query="Create a simple REST API for managing tasks with FastAPI",
        workspace_path=workspace_path,
        test_name="create_api_workflow"
    )

    # Final Summary
    print("\n" + "=" * 80)
    print("📊 v6.6 LLM ROUTING TEST RESULTS")
    print("=" * 80)

    tests = [test1, test2]
    passed = sum(1 for t in tests if t['success'])
    total = len(tests)

    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print("=" * 80)

    for test in tests:
        status = "✅ PASS" if test['success'] else "❌ FAIL"
        print(f"{status} | {test['test_name']}")
        if test.get('error'):
            print(f"        Error: {test['error']}")

    print("=" * 80 + "\n")

    # Critical checks
    print("🔍 CRITICAL CHECKS:")
    print("=" * 80)
    print(f"1. LLM Routing Detected: {test1['llm_routing']} (Test 1)")
    print(f"2. Multiple Agent Proposals: {test1['proposals_count']} proposals (Test 1)")
    print(f"3. Routing Decision Made: {test1['routing_decision']} (Test 1)")
    print(f"4. Agent Execution Started: {test1['agent_started']} (Test 1)")
    print("=" * 80 + "\n")

    if all([test1['llm_routing'],
            test1['proposals_count'] >= 4,  # Should have 4 agent proposals
            test1['routing_decision'],
            test1['agent_started']]):
        print("🎉 v6.6 LLM-BASED ROUTING: ✅ PRODUCTION READY!\n")
    else:
        print("⚠️  v6.6 LLM-BASED ROUTING: ❌ ISSUES DETECTED\n")


if __name__ == "__main__":
    asyncio.run(main())
