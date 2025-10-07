"""
Test Real Agent Integration
Tests actual agent responses via WebSocket
"""

import asyncio
import json
import sys

import aiohttp

WS_URL = "ws://localhost:8000/ws/chat"


async def test_real_agent():
    """Test real agent response"""
    print("\n🧪 Testing Real Agent Integration")
    print("=" * 50)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.ws_connect(WS_URL) as ws:
                # Wait for welcome message
                msg = await ws.receive()
                data = json.loads(msg.data)
                print(f"✅ Connected: {data['message']}")

                # Test Orchestrator Agent
                print("\n📤 Testing OrchestratorAgent...")
                await ws.send_json(
                    {
                        "type": "chat",
                        "content": "Create a simple hello world function",
                        "agent": "orchestrator",
                    }
                )

                # Receive thinking message
                msg = await ws.receive()
                data = json.loads(msg.data)
                print(f"🤔 {data.get('message', 'Processing...')}")

                # Receive response
                msg = await asyncio.wait_for(ws.receive(), timeout=30.0)
                data = json.loads(msg.data)
                print("\n📨 Agent Response:")
                print(f"Status: {data.get('status', 'unknown')}")
                print(f"Content Preview: {data.get('content', '')[:200]}...")

                # Test Architect Agent
                print("\n\n📤 Testing ArchitectAgent...")
                await ws.send_json(
                    {
                        "type": "chat",
                        "content": "Design a simple REST API architecture",
                        "agent": "architect",
                    }
                )

                # Skip thinking message
                await ws.receive()

                # Receive response
                msg = await asyncio.wait_for(ws.receive(), timeout=30.0)
                data = json.loads(msg.data)
                print("\n📨 Architect Response:")
                print(f"Status: {data.get('status', 'unknown')}")

                # Check for architecture elements in response
                response_content = data.get("content", "")
                if (
                    "architecture" in response_content.lower()
                    or "design" in response_content.lower()
                ):
                    print("✅ Architecture design elements found in response")
                else:
                    print("⚠️ Response may need API key configuration")

                await ws.close()
                print("\n✅ Test completed successfully!")
                return True

        except asyncio.TimeoutError:
            print("\n❌ Timeout waiting for agent response")
            print("This may happen if API keys are not configured")
            return False
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False


if __name__ == "__main__":
    success = asyncio.run(test_real_agent())
    sys.exit(0 if success else 1)
