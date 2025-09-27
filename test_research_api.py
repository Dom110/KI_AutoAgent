#!/usr/bin/env python3
"""
Test ResearchAgent through the backend API
"""

import asyncio
import websockets
import json

async def test_research_agent():
    """Test ResearchAgent via WebSocket"""
    uri = "ws://localhost:8000/ws/chat"

    test_query = "What are the latest features of Claude AI in 2025?"

    async with websockets.connect(uri) as websocket:
        # Send research request
        request = {
            "message": test_query,
            "agent": "research",
            "mode": "single",
            "context": {}
        }

        print(f"🔍 Sending query: {test_query}")
        await websocket.send(json.dumps(request))

        # Receive responses
        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)

                if data.get("type") == "response":
                    print(f"\n✅ Research Response:")
                    print("-" * 60)
                    print(data.get("content", "")[:500])
                    if len(data.get("content", "")) > 500:
                        print("... [truncated]")
                    print("-" * 60)
                    break
                elif data.get("type") == "error":
                    print(f"\n❌ Error: {data.get('content')}")
                    break
                elif data.get("type") == "stream_chunk":
                    print(".", end="", flush=True)
                else:
                    print(f"\n📝 {data.get('type', 'unknown')}: {data.get('content', '')[:100]}")

            except asyncio.TimeoutError:
                print("\n⏱️ Timeout waiting for response")
                break
            except websockets.exceptions.ConnectionClosed:
                print("\n🔌 Connection closed")
                break

if __name__ == "__main__":
    print("🧪 Testing ResearchAgent via Backend API")
    print("=" * 60)
    asyncio.run(test_research_agent())
    print("\n✅ Test complete!")