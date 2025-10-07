"""
Test FastAPI Server and WebSocket Connection
Run this to verify the server is working correctly
"""

import asyncio
import json
import sys

import aiohttp

# Test configuration
SERVER_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/chat"


async def test_health_check():
    """Test the health check endpoint"""
    print("\n🔍 Testing Health Check Endpoint...")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{SERVER_URL}/") as response:
                data = await response.json()
                print(f"✅ Health Check Response: {json.dumps(data, indent=2)}")
                assert data["status"] == "healthy"
                assert data["service"] == "KI AutoAgent Backend"
                return True
        except Exception as e:
            print(f"❌ Health Check Failed: {e}")
            return False


async def test_agents_endpoint():
    """Test the agents info endpoint"""
    print("\n🔍 Testing Agents Endpoint...")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{SERVER_URL}/api/agents") as response:
                data = await response.json()
                print("✅ Available Agents:")
                for agent in data["agents"]:
                    print(f"  - {agent['name']} ({agent['model']})")
                assert len(data["agents"]) > 0
                return True
        except Exception as e:
            print(f"❌ Agents Endpoint Failed: {e}")
            return False


async def test_websocket_connection():
    """Test WebSocket connection and messaging"""
    print("\n🔍 Testing WebSocket Connection...")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.ws_connect(WS_URL) as ws:
                # Wait for welcome message
                msg = await ws.receive()
                data = json.loads(msg.data)
                print(f"✅ Connected: {data['message']}")

                # Test chat message
                print("\n📤 Sending test chat message...")
                await ws.send_json(
                    {
                        "type": "chat",
                        "content": "Hello, this is a test message!",
                        "agent": "orchestrator",
                    }
                )

                # Receive thinking message
                msg = await ws.receive()
                data = json.loads(msg.data)
                print(f"🤔 Agent Thinking: {data['message']}")

                # Receive response
                msg = await ws.receive()
                data = json.loads(msg.data)
                print(f"💬 Agent Response: {data['content']}")

                # Test command
                print("\n📤 Sending test command...")
                await ws.send_json({"type": "command", "command": "test_command"})

                msg = await ws.receive()
                data = json.loads(msg.data)
                print(f"⚡ Command Result: {data['result']}")

                # Test ping/pong
                print("\n📤 Testing ping/pong...")
                await ws.send_json({"type": "ping"})

                msg = await ws.receive()
                data = json.loads(msg.data)
                assert data["type"] == "pong"
                print("✅ Ping/Pong successful")

                await ws.close()
                return True

        except Exception as e:
            print(f"❌ WebSocket Test Failed: {e}")
            return False


async def run_all_tests():
    """Run all tests"""
    print("=" * 50)
    print("🧪 KI AutoAgent Backend Test Suite")
    print("=" * 50)

    results = []

    # Test health check
    results.append(await test_health_check())

    # Test agents endpoint
    results.append(await test_agents_endpoint())

    # Test WebSocket
    results.append(await test_websocket_connection())

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"  Total Tests: {len(results)}")
    print(f"  Passed: {sum(results)}")
    print(f"  Failed: {len(results) - sum(results)}")

    if all(results):
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    # Check if server is running
    print("⚠️  Make sure the server is running first!")
    print("Run: cd backend && python -m uvicorn api.server:app --reload")
    print("\nPress Enter to start tests...")
    input()

    # Run tests
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
