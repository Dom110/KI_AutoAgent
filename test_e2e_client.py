#!/usr/bin/env python3
"""
E2E Test Client for Pure MCP Architecture
Tests WebSocket communication and all workflows
"""
import asyncio
import json
import websockets
import sys
from typing import AsyncIterator
from datetime import datetime

class E2ETestClient:
    def __init__(self, workspace_path: str):
        self.ws_url = "ws://localhost:8002/ws/chat"
        self.workspace_path = workspace_path
        self.session_id = None
        self.ws = None

    async def connect(self) -> bool:
        """Connect to WebSocket server"""
        try:
            self.ws = await websockets.connect(self.ws_url)
            print(f"✅ Connected to {self.ws_url}")

            # Send init message
            init_msg = {
                "type": "init",
                "workspace_path": self.workspace_path
            }
            await self.ws.send(json.dumps(init_msg))
            print(f"📤 Sent init: {self.workspace_path}")

            # Wait for init response
            response = await self.ws.recv()
            data = json.loads(response)

            if data.get("type") == "init":
                self.session_id = data.get("session_id")
                print(f"✅ Session initialized: {self.session_id}")
                return True
            else:
                print(f"❌ Unexpected init response: {data}")
                return False

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    async def send_query(self, query: str) -> AsyncIterator[dict]:
        """Send query and stream responses"""
        if not self.ws:
            raise RuntimeError("Not connected")

        # Send query
        query_msg = {
            "type": "query",
            "query": query
        }
        await self.ws.send(json.dumps(query_msg))
        print(f"\n{'='*80}")
        print(f"📤 QUERY: {query}")
        print(f"{'='*80}\n")

        # Stream responses
        while True:
            try:
                response = await asyncio.wait_for(self.ws.recv(), timeout=300)
                data = json.loads(response)
                yield data

                # Stop on final response
                if data.get("type") == "final_response":
                    break

            except asyncio.TimeoutError:
                print("⏱️  Timeout waiting for response")
                break
            except Exception as e:
                print(f"❌ Error receiving: {e}")
                break

    async def close(self):
        """Close connection"""
        if self.ws:
            await self.ws.close()
            print("✅ Connection closed")


async def test_1_create_new_app(workspace: str):
    """Test 1: Create new app from scratch"""
    print("\n" + "="*80)
    print("🧪 TEST 1: Create New App from Scratch")
    print("="*80)

    client = E2ETestClient(workspace)

    if not await client.connect():
        print("❌ TEST 1 FAILED: Connection failed")
        return False

    query = """Create a new Python CLI todo app with the following features:
- Add tasks
- List tasks
- Mark tasks as done
- Delete tasks
- Save tasks to JSON file

Use argparse for CLI. Keep it simple and production-ready."""

    event_count = 0
    mcp_progress_count = 0
    final_response = None

    async for event in client.send_query(query):
        event_type = event.get("type")
        event_count += 1

        if event_type == "status":
            print(f"📊 Status: {event.get('status')} - {event.get('message', '')}")

        elif event_type == "mcp_progress":
            mcp_progress_count += 1
            server = event.get("server", "unknown")
            message = event.get("message", "")
            progress = event.get("progress", 0.0)
            print(f"⚡ MCP Progress [{server}]: {message} ({progress:.1%})")

        elif event_type == "agent_step":
            agent = event.get("agent", "unknown")
            action = event.get("action", "")
            print(f"🤖 Agent: {agent} - {action}")

        elif event_type == "final_response":
            final_response = event.get("response", "")
            print(f"\n{'='*80}")
            print(f"✅ FINAL RESPONSE:")
            print(f"{'='*80}")
            print(final_response[:500] + "..." if len(final_response) > 500 else final_response)

        elif event_type == "error":
            print(f"❌ ERROR: {event.get('message', 'Unknown error')}")
            await client.close()
            return False

    await client.close()

    print(f"\n📊 Test 1 Statistics:")
    print(f"   - Total events: {event_count}")
    print(f"   - MCP progress events: {mcp_progress_count}")
    print(f"   - Final response: {'✅ Received' if final_response else '❌ Missing'}")

    success = event_count > 0 and final_response is not None
    print(f"\n{'✅ TEST 1 PASSED' if success else '❌ TEST 1 FAILED'}")
    return success


async def test_2_extend_app(workspace: str):
    """Test 2: Extend existing app"""
    print("\n" + "="*80)
    print("🧪 TEST 2: Extend Existing App")
    print("="*80)

    # First create a simple app
    print("📝 Step 1: Creating base app...")
    client = E2ETestClient(workspace)

    if not await client.connect():
        print("❌ TEST 2 FAILED: Connection failed")
        return False

    # Create simple counter app
    query1 = """Create a simple Python counter app:
- count.py with increment() and get_count() functions
- Store count in a variable"""

    async for event in client.send_query(query1):
        if event.get("type") == "final_response":
            print("✅ Base app created")
            break

    await client.close()

    # Now extend it
    print("\n📝 Step 2: Extending app...")
    client2 = E2ETestClient(workspace)

    if not await client2.connect():
        print("❌ TEST 2 FAILED: Connection failed")
        return False

    query2 = """Extend the counter app with:
- Decrement function
- Reset function
- Save/load count to JSON file
- Add tests"""

    event_count = 0
    final_response = None

    async for event in client2.send_query(query2):
        event_type = event.get("type")
        event_count += 1

        if event_type == "mcp_progress":
            server = event.get("server", "unknown")
            message = event.get("message", "")
            print(f"⚡ MCP [{server}]: {message}")

        elif event_type == "final_response":
            final_response = event.get("response", "")
            print("✅ Extension complete")

    await client2.close()

    success = event_count > 0 and final_response is not None
    print(f"\n{'✅ TEST 2 PASSED' if success else '❌ TEST 2 FAILED'}")
    return success


async def test_3_analyze_non_ki_app(workspace: str):
    """Test 3: Analyze and extend non-KI app"""
    print("\n" + "="*80)
    print("🧪 TEST 3: Analyze Non-KI App")
    print("="*80)

    client = E2ETestClient(workspace)

    if not await client.connect():
        print("❌ TEST 3 FAILED: Connection failed")
        return False

    query = """Analyze this workspace and explain:
1. What programming languages are used
2. What the project structure is
3. What the main components are
4. Suggest improvements

Then add a README.md with project documentation."""

    event_count = 0
    final_response = None

    async for event in client.send_query(query):
        event_type = event.get("type")
        event_count += 1

        if event_type == "mcp_progress":
            server = event.get("server", "unknown")
            message = event.get("message", "")
            print(f"⚡ MCP [{server}]: {message}")

        elif event_type == "final_response":
            final_response = event.get("response", "")
            print("✅ Analysis complete")

    await client.close()

    success = event_count > 0 and final_response is not None
    print(f"\n{'✅ TEST 3 PASSED' if success else '❌ TEST 3 FAILED'}")
    return success


async def test_4_research_task(workspace: str):
    """Test 4: General research task"""
    print("\n" + "="*80)
    print("🧪 TEST 4: General Research Task")
    print("="*80)

    client = E2ETestClient(workspace)

    if not await client.connect():
        print("❌ TEST 4 FAILED: Connection failed")
        return False

    query = """Research the current best practices for FastAPI production deployment in 2024.
Include:
- Performance optimization techniques
- Security best practices
- Monitoring and logging
- Docker deployment

Summarize the findings in a markdown document."""

    event_count = 0
    mcp_progress_count = 0
    perplexity_called = False
    final_response = None

    async for event in client.send_query(query):
        event_type = event.get("type")
        event_count += 1

        if event_type == "mcp_progress":
            mcp_progress_count += 1
            server = event.get("server", "unknown")
            message = event.get("message", "")

            if server == "perplexity":
                perplexity_called = True
                print(f"🔍 Perplexity: {message}")
            else:
                print(f"⚡ MCP [{server}]: {message}")

        elif event_type == "final_response":
            final_response = event.get("response", "")
            print("✅ Research complete")

    await client.close()

    print(f"\n📊 Test 4 Statistics:")
    print(f"   - Total events: {event_count}")
    print(f"   - MCP progress events: {mcp_progress_count}")
    print(f"   - Perplexity called: {'✅ Yes' if perplexity_called else '❌ No'}")
    print(f"   - Final response: {'✅ Received' if final_response else '❌ Missing'}")

    success = event_count > 0 and final_response is not None and perplexity_called
    print(f"\n{'✅ TEST 4 PASSED' if success else '❌ TEST 4 FAILED'}")
    return success


async def main():
    print("="*80)
    print("🧪 E2E TESTS - Pure MCP Architecture")
    print("="*80)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results = {}

    # Test 1: Create new app
    results["test_1"] = await test_1_create_new_app("~/TestApps/test_new_app")
    await asyncio.sleep(2)

    # Test 2: Extend app
    results["test_2"] = await test_2_extend_app("~/TestApps/test_extend_app")
    await asyncio.sleep(2)

    # Test 3: Analyze non-KI app
    # For this test, copy some sample code first
    results["test_3"] = await test_3_analyze_non_ki_app("~/TestApps/test_non_ki_app")
    await asyncio.sleep(2)

    # Test 4: Research task
    results["test_4"] = await test_4_research_task("~/TestApps/test_research")

    # Summary
    print("\n" + "="*80)
    print("📊 E2E TEST SUMMARY")
    print("="*80)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")

    total = len(results)
    passed = sum(results.values())

    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print(f"⏰ Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return all(results.values())


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
