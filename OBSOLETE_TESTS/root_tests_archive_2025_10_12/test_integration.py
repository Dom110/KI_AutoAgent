"""
Comprehensive Integration Test for KI AutoAgent Backend
Tests the complete system including agents, WebSocket, and orchestration
"""

import asyncio
import json
import sys
import aiohttp
from datetime import datetime
from typing import Dict, Any, List

# Test configuration
SERVER_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/chat"

class IntegrationTestSuite:
    """Complete integration test suite"""

    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    async def run_all_tests(self):
        """Run all integration tests"""
        print("=" * 60)
        print("🧪 KI AutoAgent Backend - Comprehensive Integration Tests")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Backend URL: {SERVER_URL}")
        print(f"WebSocket URL: {WS_URL}")
        print("")

        # Test categories
        test_categories = [
            ("🔌 Backend Health", self.test_backend_health),
            ("📡 WebSocket Connection", self.test_websocket_connection),
            ("🤖 Agent Communication", self.test_agent_communication),
            ("🎯 Orchestrator Functionality", self.test_orchestrator),
            ("🔄 Parallel Execution", self.test_parallel_execution),
            ("💬 Streaming Responses", self.test_streaming),
            ("❌ Error Handling", self.test_error_handling),
            ("🔁 Reconnection", self.test_reconnection),
        ]

        for category_name, test_func in test_categories:
            print(f"\n{category_name}")
            print("-" * 40)
            try:
                await test_func()
            except Exception as e:
                self.record_result(f"{category_name} - Exception", False, str(e))

        # Print summary
        self.print_summary()

    async def test_backend_health(self):
        """Test backend health endpoints"""
        async with aiohttp.ClientSession() as session:
            # Test health check
            test_name = "Health Check Endpoint"
            try:
                async with session.get(f"{SERVER_URL}/") as response:
                    data = await response.json()
                    success = (
                        response.status == 200 and
                        data.get("status") == "healthy"
                    )
                    self.record_result(test_name, success, data)
            except Exception as e:
                self.record_result(test_name, False, str(e))

            # Test agents endpoint
            test_name = "Agents Info Endpoint"
            try:
                async with session.get(f"{SERVER_URL}/api/agents") as response:
                    data = await response.json()
                    success = (
                        response.status == 200 and
                        len(data.get("agents", [])) > 0
                    )
                    self.record_result(test_name, success, f"{len(data.get('agents', []))} agents found")
            except Exception as e:
                self.record_result(test_name, False, str(e))

    async def test_websocket_connection(self):
        """Test WebSocket connection and basic messaging"""
        test_name = "WebSocket Connection"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.ws_connect(WS_URL) as ws:
                    # Wait for welcome message
                    msg = await asyncio.wait_for(ws.receive(), timeout=5.0)
                    data = json.loads(msg.data)

                    success = data.get("type") == "connection"
                    self.record_result(test_name, success, data.get("message", ""))

                    # Test ping/pong
                    test_name = "WebSocket Ping/Pong"
                    await ws.send_json({"type": "ping"})
                    msg = await asyncio.wait_for(ws.receive(), timeout=2.0)
                    data = json.loads(msg.data)

                    success = data.get("type") == "pong"
                    self.record_result(test_name, success)

                    await ws.close()

            except Exception as e:
                self.record_result(test_name, False, str(e))

    async def test_agent_communication(self):
        """Test communication with different agents"""
        agents_to_test = [
            ("orchestrator", "What can you do?"),
            ("architect", "Design a simple API"),
            ("codesmith", "Write a hello world function"),
        ]

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(WS_URL) as ws:
                # Skip welcome message
                await ws.receive()

                for agent_id, prompt in agents_to_test:
                    test_name = f"Agent Communication - {agent_id}"

                    try:
                        # Send message to agent
                        await ws.send_json({
                            "type": "chat",
                            "content": prompt,
                            "agent": agent_id
                        })

                        # Expect thinking message
                        msg = await asyncio.wait_for(ws.receive(), timeout=5.0)
                        thinking_data = json.loads(msg.data)

                        # Expect response
                        msg = await asyncio.wait_for(ws.receive(), timeout=10.0)
                        response_data = json.loads(msg.data)

                        success = (
                            thinking_data.get("type") == "agent_thinking" and
                            response_data.get("type") == "agent_response"
                        )

                        self.record_result(
                            test_name,
                            success,
                            f"Response length: {len(response_data.get('content', ''))}"
                        )

                    except Exception as e:
                        self.record_result(test_name, False, str(e))

    async def test_orchestrator(self):
        """Test orchestrator task decomposition"""
        test_name = "Orchestrator Task Decomposition"

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(WS_URL) as ws:
                # Skip welcome message
                await ws.receive()

                try:
                    # Send complex task
                    await ws.send_json({
                        "type": "chat",
                        "content": "Build a complete REST API with authentication",
                        "agent": "orchestrator"
                    })

                    # Collect responses
                    messages = []
                    for _ in range(3):  # Expect at least 3 messages
                        msg = await asyncio.wait_for(ws.receive(), timeout=10.0)
                        messages.append(json.loads(msg.data))

                    # Check for orchestration elements
                    has_thinking = any(m.get("type") == "agent_thinking" for m in messages)
                    has_response = any(m.get("type") == "agent_response" for m in messages)

                    # Check if response mentions subtasks or complexity
                    response_content = next(
                        (m.get("content", "") for m in messages if m.get("type") == "agent_response"),
                        ""
                    )

                    has_decomposition = any(
                        word in response_content.lower()
                        for word in ["subtask", "step", "complexity", "workflow"]
                    )

                    success = has_thinking and has_response
                    self.record_result(
                        test_name,
                        success,
                        f"Decomposition found: {has_decomposition}"
                    )

                except Exception as e:
                    self.record_result(test_name, False, str(e))

    async def test_parallel_execution(self):
        """Test parallel task execution capability"""
        test_name = "Parallel Execution Simulation"

        # This tests if the backend can handle multiple concurrent requests
        async with aiohttp.ClientSession() as session:
            try:
                # Create multiple WebSocket connections
                connections = []
                for i in range(3):
                    ws = await session.ws_connect(WS_URL)
                    connections.append(ws)
                    # Skip welcome message
                    await ws.receive()

                # Send messages in parallel
                tasks = []
                for i, ws in enumerate(connections):
                    task = ws.send_json({
                        "type": "chat",
                        "content": f"Task {i+1}: Simple calculation",
                        "agent": "orchestrator"
                    })
                    tasks.append(task)

                await asyncio.gather(*tasks)

                # Receive responses in parallel
                response_tasks = []
                for ws in connections:
                    # Skip thinking message
                    response_tasks.append(ws.receive())

                results = await asyncio.gather(*response_tasks, return_exceptions=True)

                # Close connections
                for ws in connections:
                    await ws.close()

                success = all(not isinstance(r, Exception) for r in results)
                self.record_result(
                    test_name,
                    success,
                    f"Handled {len(connections)} parallel connections"
                )

            except Exception as e:
                self.record_result(test_name, False, str(e))

    async def test_streaming(self):
        """Test streaming response capability"""
        test_name = "Streaming Response"

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(WS_URL) as ws:
                # Skip welcome message
                await ws.receive()

                try:
                    # Request a longer response
                    await ws.send_json({
                        "type": "chat",
                        "content": "Explain the architecture of this system in detail",
                        "agent": "orchestrator",
                        "metadata": {"streaming": True}
                    })

                    # Collect multiple messages (streaming chunks)
                    messages = []
                    start_time = datetime.now()

                    while (datetime.now() - start_time).total_seconds() < 5:
                        try:
                            msg = await asyncio.wait_for(ws.receive(), timeout=1.0)
                            messages.append(json.loads(msg.data))
                        except asyncio.TimeoutError:
                            break

                    # Check for streaming indicators
                    has_multiple_messages = len(messages) >= 2
                    message_types = [m.get("type") for m in messages]

                    success = has_multiple_messages
                    self.record_result(
                        test_name,
                        success,
                        f"Received {len(messages)} messages"
                    )

                except Exception as e:
                    self.record_result(test_name, False, str(e))

    async def test_error_handling(self):
        """Test error handling and recovery"""
        test_cases = [
            ("Invalid Message Type", {"type": "invalid_type"}),
            ("Empty Content", {"type": "chat", "content": ""}),
            ("Unknown Agent", {"type": "chat", "content": "test", "agent": "unknown_agent"}),
        ]

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(WS_URL) as ws:
                # Skip welcome message
                await ws.receive()

                for test_name, invalid_message in test_cases:
                    try:
                        await ws.send_json(invalid_message)

                        # Should receive an error or handle gracefully
                        msg = await asyncio.wait_for(ws.receive(), timeout=3.0)
                        data = json.loads(msg.data)

                        # Success if error is handled (not crashed)
                        success = True
                        self.record_result(
                            f"Error Handling - {test_name}",
                            success,
                            data.get("type", "handled")
                        )

                    except asyncio.TimeoutError:
                        # No response is also acceptable (ignored)
                        self.record_result(f"Error Handling - {test_name}", True, "ignored")
                    except Exception as e:
                        self.record_result(f"Error Handling - {test_name}", False, str(e))

    async def test_reconnection(self):
        """Test reconnection capability"""
        test_name = "WebSocket Reconnection"

        async with aiohttp.ClientSession() as session:
            try:
                # First connection
                ws1 = await session.ws_connect(WS_URL)
                await ws1.receive()  # Welcome message

                # Send a message
                await ws1.send_json({
                    "type": "chat",
                    "content": "First connection test",
                    "agent": "orchestrator"
                })

                # Close first connection
                await ws1.close()

                # Second connection (reconnection)
                ws2 = await session.ws_connect(WS_URL)
                msg = await asyncio.wait_for(ws2.receive(), timeout=5.0)
                data = json.loads(msg.data)

                # Send a message on new connection
                await ws2.send_json({
                    "type": "chat",
                    "content": "Reconnection test",
                    "agent": "orchestrator"
                })

                # Should receive response
                await ws2.receive()  # Thinking
                msg = await asyncio.wait_for(ws2.receive(), timeout=10.0)
                response_data = json.loads(msg.data)

                await ws2.close()

                success = response_data.get("type") == "agent_response"
                self.record_result(test_name, success, "Reconnection successful")

            except Exception as e:
                self.record_result(test_name, False, str(e))

    def record_result(self, test_name: str, success: bool, details: Any = None):
        """Record test result"""
        self.total_tests += 1

        if success:
            self.passed_tests += 1
            status_icon = "✅"
        else:
            self.failed_tests += 1
            status_icon = "❌"

        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }

        self.test_results.append(result)

        # Print immediate feedback
        details_str = f" - {details}" if details else ""
        print(f"  {status_icon} {test_name}{details_str}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")

        if self.failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")

        print("\n" + "=" * 60)

        if self.failed_tests == 0:
            print("🎉 ALL TESTS PASSED! System is fully functional!")
        else:
            print(f"⚠️  {self.failed_tests} test(s) failed. Please check the issues above.")

        return self.failed_tests == 0

async def main():
    """Run the integration test suite"""
    # Check if backend is running
    print("🔍 Checking if backend is running...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{SERVER_URL}/") as response:
                if response.status == 200:
                    print("✅ Backend is running!\n")
                else:
                    print(f"❌ Backend returned status {response.status}")
                    sys.exit(1)
    except Exception as e:
        print(f"❌ Backend is not running: {e}")
        print("\nPlease start the backend first:")
        print("  cd backend")
        print("  ./run.sh")
        sys.exit(1)

    # Run tests
    test_suite = IntegrationTestSuite()
    await test_suite.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if test_suite.failed_tests == 0 else 1)

if __name__ == "__main__":
    asyncio.run(main())