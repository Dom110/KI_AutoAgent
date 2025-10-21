#!/usr/bin/env python3
"""
WebSocket Test Script for Multi-Agent Routing v6.5

Tests:
1. "Untersuche die App im Workspace" → Should route to Research (explain mode)
2. "Create a todo app" → Should route to Architect (design mode)
"""

import asyncio
import json
import os
from pathlib import Path

import websockets


async def test_routing(query: str, workspace_path: str, test_name: str):
    """Test routing for a specific query."""
    print(f"\n{'=' * 80}")
    print(f"🧪 TEST: {test_name}")
    print(f"{'=' * 80}")
    print(f"📝 Query: {query}")
    print(f"📁 Workspace: {workspace_path}")
    print(f"{'=' * 80}\n")

    uri = "ws://localhost:8002/ws/chat"

    try:
        async with websockets.connect(uri) as websocket:
            # Wait for connection confirmation
            response = await websocket.recv()
            print(f"🔌 Connection: {response}\n")

            # Send INIT message with workspace (REQUIRED!)
            init_msg = {
                "type": "init",
                "workspace_path": workspace_path
            }
            await websocket.send(json.dumps(init_msg))
            print(f"📤 Sent init message\n")

            # Wait for initialization confirmation
            init_response = await websocket.recv()
            print(f"✅ Initialized: {json.loads(init_response).get('message', 'N/A')}\n")

            # Send query (type can be "chat", "message", or "task")
            query_msg = {
                "type": "chat",
                "content": query
            }
            await websocket.send(json.dumps(query_msg))
            print(f"📤 Sent query: {query}\n")

            # Collect responses
            routing_decision = None
            agent_started = None
            messages = []

            timeout_counter = 0
            max_timeout = 60  # 60 seconds max

            while timeout_counter < max_timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    messages.append(data)

                    # Extract routing information
                    if data.get("type") == "log":
                        log_msg = data.get("message", "")

                        # Check for routing decision
                        if "Routing:" in log_msg or "Multi-Agent Routing:" in log_msg:
                            print(f"🎯 {log_msg}")
                            routing_decision = log_msg

                        # Check for agent start
                        if "Agent executing" in log_msg or "agent_start" in str(data):
                            print(f"🚀 {log_msg}")
                            agent_started = log_msg

                        # Check for mode information
                        if "mode=" in log_msg:
                            print(f"📋 {log_msg}")

                        # General important logs
                        if any(keyword in log_msg for keyword in ["confidence", "reasoning", "Agents:", "strategy"]):
                            print(f"ℹ️  {log_msg}")

                    elif data.get("type") == "agent_start":
                        agent = data.get("agent", "unknown")
                        print(f"🚀 Agent Started: {agent}")
                        agent_started = agent

                    elif data.get("type") == "result":
                        print(f"\n✅ Result received!")
                        print(f"📄 {json.dumps(data, indent=2)[:500]}...")
                        break

                    elif data.get("type") == "error":
                        print(f"\n❌ Error: {data.get('message')}")
                        break

                except asyncio.TimeoutError:
                    timeout_counter += 1
                    if timeout_counter % 10 == 0:
                        print(f"⏳ Waiting... ({timeout_counter}s)")
                except Exception as e:
                    print(f"❌ Error receiving message: {e}")
                    break

            # Summary
            print(f"\n{'=' * 80}")
            print(f"📊 TEST SUMMARY: {test_name}")
            print(f"{'=' * 80}")
            print(f"Routing Decision: {routing_decision if routing_decision else '❌ NOT DETECTED'}")
            print(f"Agent Started: {agent_started if agent_started else '❌ NOT DETECTED'}")
            print(f"Total Messages: {len(messages)}")
            print(f"{'=' * 80}\n")

            return {
                "test_name": test_name,
                "query": query,
                "routing_decision": routing_decision,
                "agent_started": agent_started,
                "success": routing_decision is not None and agent_started is not None
            }

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "test_name": test_name,
            "query": query,
            "error": str(e),
            "success": False
        }


async def main():
    """Run all routing tests."""
    print("\n" + "=" * 80)
    print("🧪 MULTI-AGENT ROUTING V6.5 - WEBSOCKET TESTS")
    print("=" * 80 + "\n")

    workspace_path = str(Path.home() / "TestApps" / "routing_test_v6_5")

    # Test 1: German query that was failing before
    test1 = await test_routing(
        query="Untersuche die App im Workspace",
        workspace_path=workspace_path,
        test_name="german_explain_query"
    )

    await asyncio.sleep(2)  # Pause between tests

    # Test 2: CREATE workflow
    test2 = await test_routing(
        query="Create a simple todo app with FastAPI",
        workspace_path=workspace_path,
        test_name="create_workflow"
    )

    # Final Summary
    print("\n" + "=" * 80)
    print("📊 FINAL TEST RESULTS")
    print("=" * 80)
    print(f"Test 1 (German Explain): {'✅ PASSED' if test1['success'] else '❌ FAILED'}")
    print(f"Test 2 (CREATE workflow): {'✅ PASSED' if test2['success'] else '❌ FAILED'}")
    print("=" * 80 + "\n")

    # Check expected routing
    print("\n📋 EXPECTED ROUTING:")
    print("=" * 80)
    print("Test 1: 'Untersuche die App' → Research (explain mode)")
    print(f"  Actual: {test1.get('agent_started', 'UNKNOWN')}")
    print()
    print("Test 2: 'Create a todo app' → Architect (design mode)")
    print(f"  Actual: {test2.get('agent_started', 'UNKNOWN')}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
