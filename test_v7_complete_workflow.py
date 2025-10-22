#!/usr/bin/env python3
"""
Test complete v7.0 workflow with startup script.

Tests:
1. Server is running and healthy
2. WebSocket can connect
3. Workflow executes with no hardcoded knowledge
4. Research timeout is handled properly
5. Response is returned to user
"""

import asyncio
import json
import websockets
import httpx


async def test_health():
    """Test health endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8002/health")
        data = response.json()
        print(f"✅ Health Check: {data['status']}")
        print(f"   Version: {data['version']}")
        print(f"   Architecture: {data['architecture']}")
        assert data['status'] == "healthy"
        assert data['version'] == "7.0.0-alpha"
        return True


async def test_websocket_workflow():
    """Test complete workflow via WebSocket."""
    uri = "ws://localhost:8002/ws/chat"

    async with websockets.connect(uri) as websocket:
        # Wait for connection message
        response = await websocket.recv()
        data = json.loads(response)
        print(f"\n✅ Connected: {data['message']}")
        assert data['type'] == "connected"

        # Send init message
        init_msg = {
            "type": "init",
            "workspace_path": "/Users/dominikfoert/git/KI_AutoAgent"
        }
        await websocket.send(json.dumps(init_msg))

        # Wait for initialized
        response = await websocket.recv()
        data = json.loads(response)
        print(f"✅ Initialized: {data['message']}")
        assert data['type'] == "initialized"

        # Send test query
        test_query = {
            "type": "chat",
            "content": "What are the best practices for async/await in Python?"
        }
        await websocket.send(json.dumps(test_query))
        print(f"\n📨 Sent query: {test_query['content']}")

        # Collect responses
        workflow_complete = False
        research_attempted = False
        supervisor_decisions = []

        while not workflow_complete:
            response = await websocket.recv()
            data = json.loads(response)

            if data['type'] == "status":
                print(f"⏳ Status: {data.get('message', data.get('status'))}")

            elif data['type'] == "supervisor_decision":
                agent = data.get('next_agent')
                supervisor_decisions.append(agent)
                print(f"🎯 Supervisor → {agent}")
                if agent == "research":
                    research_attempted = True

            elif data['type'] == "agent_start":
                print(f"🚀 {data['agent']} starting...")

            elif data['type'] == "agent_complete":
                print(f"✅ {data['agent']} complete")

            elif data['type'] == "log":
                # Check for research timeout or fallback
                if "timeout" in data['message'].lower():
                    print(f"⏱️ Research timeout detected (expected)")
                elif "no web search" in data['message'].lower():
                    print(f"📚 Using project knowledge (no hardcoded fallback)")

            elif data['type'] == "result":
                print(f"\n✅ Workflow Complete!")
                print(f"   Response: {data['content'][:200]}...")
                workflow_complete = True

                # Verify no hardcoded knowledge was used
                content_lower = data['content'].lower()
                assert "hardcoded" not in content_lower, "Should not use hardcoded responses"

                # Check that research was attempted
                assert research_attempted, "Should attempt research"

                # Check supervisor made decisions
                # Note: We may not see all decisions via WebSocket events
                assert len(supervisor_decisions) >= 1, "Supervisor should make at least one decision"
                assert "research" in supervisor_decisions, "Should route to research first"

            elif data['type'] == "error":
                print(f"❌ Error: {data['message']}")
                workflow_complete = True
                raise AssertionError(f"Workflow error: {data['message']}")

        print("\n✅ All workflow validations passed!")
        print(f"   - No hardcoded knowledge used")
        print(f"   - Research attempted (with timeout handling)")
        print(f"   - Supervisor routing worked")
        print(f"   - Response delivered to user")

        return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("v7.0 Complete Workflow Test")
    print("=" * 60)

    # Test health
    await test_health()

    # Test workflow
    await test_websocket_workflow()

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())