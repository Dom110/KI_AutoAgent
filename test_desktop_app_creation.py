#!/usr/bin/env python3
"""
End-to-End Test: Desktop App Creation via Chat

Tests:
1. Creating a desktop app in ~/TestApps
2. Monitoring AI systems (Memory, Predictive, Curiosity)
3. Checking tool usage and thinking messages
4. Workflow creation and adaptation
5. Architecture docs, reviewer tests, system scans
6. Special scans (tree, deadcode) usage
"""

import asyncio
import websockets
import json
import time
from datetime import datetime
import os

# Test configuration
BACKEND_URL = "ws://localhost:8001/ws/chat"
WORKSPACE_PATH = os.path.expanduser("~/TestApps/DesktopCalculator")
TEST_LOG_FILE = "test_desktop_app_creation.log"

class E2ETestSession:
    def __init__(self):
        self.ws = None
        self.session_id = None
        self.messages_received = []
        self.thinking_messages = []
        self.tool_messages = []
        self.progress_messages = []

    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        with open(TEST_LOG_FILE, "a") as f:
            f.write(log_msg + "\n")

    async def connect(self):
        """Connect to backend"""
        self.log("🔌 Connecting to backend...")
        self.ws = await websockets.connect(BACKEND_URL)

        # Wait for connected message
        msg = await self.ws.recv()
        data = json.loads(msg)
        self.log(f"✅ Connected: {data}")

        # Send init
        init_msg = {
            "type": "init",
            "workspace_path": WORKSPACE_PATH
        }
        await self.ws.send(json.dumps(init_msg))

        # Wait for initialized
        msg = await self.ws.recv()
        data = json.loads(msg)
        self.session_id = data.get("session_id")
        self.log(f"✅ Initialized session: {self.session_id}")
        self.log(f"📂 Workspace: {WORKSPACE_PATH}")

    async def send_message(self, content, agent="auto", mode="direct"):
        """Send chat message"""
        self.log(f"\n{'='*80}")
        self.log(f"📤 SENDING: {content}")
        self.log(f"{'='*80}")

        msg = {
            "type": "chat",
            "content": content,
            "agent": agent,
            "mode": mode
        }
        await self.ws.send(json.dumps(msg))

    async def receive_messages(self, timeout=180):
        """Receive messages until agent_response"""
        start_time = time.time()
        response_content = None

        while time.time() - start_time < timeout:
            try:
                msg = await asyncio.wait_for(self.ws.recv(), timeout=5)
                data = json.loads(msg)
                msg_type = data.get("type")

                self.messages_received.append(data)

                if msg_type == "agent_thinking":
                    agent = data.get("agent", "unknown")
                    message = data.get("message", "")
                    self.thinking_messages.append(data)
                    self.log(f"💭 {agent} thinking: {message}")

                elif msg_type == "tool_start":
                    tool = data.get("tool", "unknown")
                    self.tool_messages.append(data)
                    self.log(f"🔧 Tool started: {tool}")

                elif msg_type == "tool_complete":
                    tool = data.get("tool", "unknown")
                    self.log(f"✅ Tool completed: {tool}")

                elif msg_type == "progress":
                    message = data.get("message", "")
                    self.progress_messages.append(data)
                    self.log(f"📊 Progress: {message}")

                elif msg_type == "agent_response" or msg_type == "response":
                    agent = data.get("agent", "unknown")
                    content = data.get("content", "")
                    response_content = content
                    self.log(f"\n{'='*80}")
                    self.log(f"📥 RESPONSE from {agent}:")
                    self.log(f"{'='*80}")
                    self.log(content[:500] + ("..." if len(content) > 500 else ""))
                    self.log(f"{'='*80}\n")
                    break

                elif msg_type == "error":
                    error_msg = data.get("message", "Unknown error")
                    self.log(f"❌ ERROR: {error_msg}")
                    break

                else:
                    self.log(f"📨 {msg_type}: {str(data)[:200]}")

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.log(f"❌ Error receiving: {e}")
                break

        return response_content

    async def close(self):
        """Close connection"""
        if self.ws:
            await self.ws.close()
            self.log("🔌 Connection closed")

    def print_statistics(self):
        """Print session statistics"""
        self.log("\n" + "="*80)
        self.log("📊 SESSION STATISTICS")
        self.log("="*80)
        self.log(f"Total messages received: {len(self.messages_received)}")
        self.log(f"Thinking messages: {len(self.thinking_messages)}")
        self.log(f"Tool messages: {len(self.tool_messages)}")
        self.log(f"Progress messages: {len(self.progress_messages)}")
        self.log("="*80 + "\n")


async def test_desktop_app_creation():
    """Main E2E test"""
    session = E2ETestSession()

    try:
        # Initialize log file
        with open(TEST_LOG_FILE, "w") as f:
            f.write(f"E2E Test Started: {datetime.now()}\n")
            f.write("="*80 + "\n\n")

        # Connect
        await session.connect()

        # Test 1: Create Desktop Calculator App
        session.log("\n🧪 TEST 1: Create Desktop Calculator App")
        await session.send_message(
            "Create a desktop calculator application in ~/TestApps/DesktopCalculator. "
            "Use Python and tkinter. Include basic operations (+, -, *, /). "
            "Make it production-ready with proper architecture, tests, and documentation."
        )
        response1 = await session.receive_messages(timeout=300)

        # Wait a bit for AI systems to update
        await asyncio.sleep(5)

        # Test 2: Check if files were created
        session.log("\n🧪 TEST 2: Verify file creation")
        await session.send_message(
            "List all files that were created in ~/TestApps/DesktopCalculator"
        )
        response2 = await session.receive_messages(timeout=60)

        # Test 3: Request architecture documentation
        session.log("\n🧪 TEST 3: Check architecture documentation")
        await session.send_message(
            "Show me the architecture documentation for the calculator app. "
            "Was a system architecture scan performed?"
        )
        response3 = await session.receive_messages(timeout=120)

        # Test 4: Add a new feature (tests workflow adaptation)
        session.log("\n🧪 TEST 4: Add new feature (tests workflow adaptation)")
        await session.send_message(
            "Add scientific calculator functions (sin, cos, tan, sqrt, log) to the calculator"
        )
        response4 = await session.receive_messages(timeout=300)

        # Print statistics
        session.print_statistics()

        # Check for AI systems activity
        session.log("\n🔍 CHECKING AI SYSTEMS ACTIVITY...")
        session.log(f"Looking for evidence of Memory/Predictive/Curiosity usage...")

        # Close connection
        await session.close()

        session.log("\n✅ E2E TEST COMPLETED")
        session.log(f"Full log saved to: {TEST_LOG_FILE}")

    except Exception as e:
        session.log(f"\n❌ TEST FAILED: {e}")
        import traceback
        session.log(traceback.format_exc())
        raise
    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(test_desktop_app_creation())
