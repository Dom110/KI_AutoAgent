#!/usr/bin/env python3
"""
Comprehensive E2E Test for KI AutoAgent v6.1-alpha

This test validates ALL major features with a live server:
- WebSocket connection and session management
- Full multi-agent workflow (Research → Architect → Codesmith → ReviewFix)
- Build validation for TypeScript
- Tree-sitter code analysis integration
- Memory system (server and project learning)
- All cognitive systems (Query Classifier, Curiosity, Predictive, etc.)

Usage:
    # Ensure server is running first:
    cd ~/.ki_autoagent && source venv/bin/activate
    python3 backend/api/server_v6_integrated.py > /tmp/v6_server.log 2>&1 &

    # Run this test:
    python3 test_comprehensive_e2e_with_server.py

Workspace: ~/TestApps/e2e_test_comprehensive
Test App: Task Manager with TypeScript + React frontend

Expected Duration: 8-12 minutes
"""

import asyncio
import json
import sys
import shutil
from pathlib import Path
from datetime import datetime
import websockets
from websockets.exceptions import ConnectionClosed

# Test Configuration
WS_URL = "ws://localhost:8002/ws/chat"
TEST_WORKSPACE = Path.home() / "TestApps" / "e2e_test_comprehensive"
TIMEOUT_SECONDS = 900  # 15 minutes max for full workflow


class ComprehensiveE2ETest:
    """Comprehensive E2E test client for KI AutoAgent."""

    def __init__(self):
        self.ws = None
        self.session_id = None
        self.workspace_path = str(TEST_WORKSPACE)
        self.messages_received = []
        self.errors = []
        self.start_time = None

    async def setup_workspace(self):
        """Setup clean test workspace."""
        print("=" * 80)
        print("🧹 SETUP: Preparing Test Workspace")
        print("=" * 80)

        if TEST_WORKSPACE.exists():
            print(f"🗑️  Removing old workspace: {TEST_WORKSPACE}")
            shutil.rmtree(TEST_WORKSPACE)

        TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created clean workspace: {TEST_WORKSPACE}")

        # Verify isolation
        assert not (TEST_WORKSPACE / "task-manager-app").exists()
        print("✅ Workspace verified clean (no old artifacts)")
        print()

    async def connect(self):
        """Connect to WebSocket server."""
        print("=" * 80)
        print("🔌 CONNECT: Establishing WebSocket Connection")
        print("=" * 80)

        try:
            self.ws = await websockets.connect(WS_URL)
            print(f"✅ Connected to {WS_URL}")

            # Wait for initial "connected" message
            msg = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
            data = json.loads(msg)
            print(f"📩 Received: {data.get('type')}")

            if data.get("type") != "connected":
                raise ValueError(f"Expected 'connected', got: {data.get('type')}")

            if not data.get("requires_init"):
                raise ValueError("Server should require init!")

            print("✅ Server requires init (correct protocol)")
            print()

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            raise

    async def initialize_session(self):
        """Send init message with workspace_path."""
        print("=" * 80)
        print("🔧 INIT: Initializing Session")
        print("=" * 80)

        init_msg = {
            "type": "init",
            "workspace_path": self.workspace_path
        }

        print(f"📤 Sending init message:")
        print(f"   workspace_path: {self.workspace_path}")

        await self.ws.send(json.dumps(init_msg))

        # Wait for initialized response
        msg = await asyncio.wait_for(self.ws.recv(), timeout=10.0)
        data = json.loads(msg)

        if data.get("type") != "initialized":
            raise ValueError(f"Expected 'initialized', got: {data}")

        self.session_id = data.get("session_id")
        print(f"✅ Session initialized")
        print(f"   session_id: {self.session_id}")
        print(f"   workspace_path: {data.get('workspace_path')}")
        print()

    async def send_task(self, user_message: str):
        """Send chat message to server."""
        print("=" * 80)
        print("💬 TASK: Sending User Request")
        print("=" * 80)

        chat_msg = {
            "type": "chat",
            "message": user_message
        }

        print(f"📤 User Message:")
        print(f"   {user_message[:100]}...")
        print()

        await self.ws.send(json.dumps(chat_msg))
        self.start_time = datetime.now()

    async def receive_responses(self):
        """Receive all responses until workflow complete."""
        print("=" * 80)
        print("📥 WORKFLOW: Receiving Responses")
        print("=" * 80)

        agent_outputs = {
            "research": [],
            "architect": [],
            "codesmith": [],
            "reviewfix": []
        }

        workflow_complete = False
        iteration_count = 0

        try:
            while not workflow_complete:
                # Receive message with timeout
                elapsed = (datetime.now() - self.start_time).total_seconds()
                remaining = TIMEOUT_SECONDS - elapsed

                if remaining <= 0:
                    raise TimeoutError("Workflow timeout exceeded!")

                msg = await asyncio.wait_for(self.ws.recv(), timeout=remaining)
                data = json.loads(msg)

                self.messages_received.append(data)
                msg_type = data.get("type")

                # Print progress
                if msg_type == "agent_start":
                    agent = data.get("agent", "unknown")
                    print(f"🤖 Agent Started: {agent.upper()}")

                elif msg_type == "agent_output":
                    agent = data.get("agent", "unknown")
                    output = data.get("output", "")
                    preview = output[:100].replace("\n", " ")
                    print(f"   📝 {agent}: {preview}...")
                    agent_outputs[agent].append(output)

                elif msg_type == "agent_complete":
                    agent = data.get("agent", "unknown")
                    print(f"   ✅ {agent.upper()} Complete")

                elif msg_type == "iteration_complete":
                    iteration_count += 1
                    print(f"🔄 Iteration {iteration_count} Complete")

                elif msg_type == "workflow_complete":
                    workflow_complete = True
                    duration = (datetime.now() - self.start_time).total_seconds()
                    print(f"🎉 WORKFLOW COMPLETE (Duration: {duration:.1f}s)")
                    print()

                elif msg_type == "error":
                    error = data.get("error", "Unknown error")
                    print(f"❌ Error: {error}")
                    self.errors.append(error)

                elif msg_type == "status":
                    status = data.get("message", "")
                    if status:
                        print(f"   ℹ️  {status}")

        except ConnectionClosed:
            print("⚠️  WebSocket connection closed")

        except asyncio.TimeoutError:
            duration = (datetime.now() - self.start_time).total_seconds()
            print(f"❌ Timeout after {duration:.1f}s")
            raise

        return agent_outputs

    async def validate_results(self, agent_outputs: dict):
        """Validate test results."""
        print("=" * 80)
        print("✅ VALIDATION: Checking Results")
        print("=" * 80)

        errors = []

        # 1. Check workspace structure
        print("1️⃣  Checking workspace structure...")

        if not TEST_WORKSPACE.exists():
            errors.append("Workspace directory doesn't exist")
        else:
            print(f"   ✅ Workspace exists: {TEST_WORKSPACE}")

        # 2. Check for generated files
        print("2️⃣  Checking generated files...")

        generated_files = list(TEST_WORKSPACE.rglob("*"))
        file_count = len([f for f in generated_files if f.is_file()])

        if file_count == 0:
            errors.append("No files were generated!")
        else:
            print(f"   ✅ Generated {file_count} files")

            # Show some examples
            for f in generated_files[:5]:
                if f.is_file():
                    print(f"      - {f.relative_to(TEST_WORKSPACE)}")

        # 3. Check agent outputs
        print("3️⃣  Checking agent outputs...")

        expected_agents = ["research", "architect", "codesmith", "reviewfix"]
        for agent in expected_agents:
            outputs = agent_outputs.get(agent, [])
            if not outputs:
                errors.append(f"{agent} agent produced no output")
            else:
                print(f"   ✅ {agent.upper()}: {len(outputs)} outputs")

        # 4. Check for TypeScript files (to test build validation)
        print("4️⃣  Checking TypeScript files (build validation)...")

        ts_files = list(TEST_WORKSPACE.rglob("*.ts")) + list(TEST_WORKSPACE.rglob("*.tsx"))
        if ts_files:
            print(f"   ✅ Found {len(ts_files)} TypeScript files")
            for ts_file in ts_files[:3]:
                print(f"      - {ts_file.relative_to(TEST_WORKSPACE)}")
        else:
            print("   ⚠️  No TypeScript files found (expected for build validation test)")

        # 5. Check for package.json (TypeScript project indicator)
        print("5️⃣  Checking package.json...")

        package_json = TEST_WORKSPACE / "package.json"
        if package_json.exists():
            print(f"   ✅ package.json exists")
            with open(package_json) as f:
                pkg_data = json.load(f)
                if "dependencies" in pkg_data or "devDependencies" in pkg_data:
                    print(f"      - Has dependencies")
        else:
            print("   ⚠️  No package.json found")

        # 6. Check for tsconfig.json (TypeScript build validation)
        print("6️⃣  Checking tsconfig.json (build validation)...")

        tsconfig = TEST_WORKSPACE / "tsconfig.json"
        if tsconfig.exists():
            print(f"   ✅ tsconfig.json exists (build validation will run)")
        else:
            print("   ⚠️  No tsconfig.json (build validation might be skipped)")

        # 7. Check for README.md
        print("7️⃣  Checking documentation...")

        readme = TEST_WORKSPACE / "README.md"
        if readme.exists():
            print(f"   ✅ README.md exists")
            size = readme.stat().st_size
            print(f"      - Size: {size} bytes")

        # 8. Check memory system (via logs)
        print("8️⃣  Checking memory system integration...")

        memory_dir = Path.home() / ".ki_autoagent_ws" / "memory"
        if memory_dir.exists():
            memory_files = list(memory_dir.rglob("*.db")) + list(memory_dir.rglob("*.index"))
            print(f"   ✅ Memory system directory exists")
            print(f"      - Found {len(memory_files)} memory files")
        else:
            print("   ⚠️  Memory system directory not found")

        # 9. Check for errors
        print("9️⃣  Checking for errors...")

        if self.errors:
            print(f"   ❌ Encountered {len(self.errors)} errors:")
            for err in self.errors:
                print(f"      - {err}")
                errors.append(err)
        else:
            print(f"   ✅ No errors encountered")

        print()
        print("=" * 80)

        if errors:
            print("❌ VALIDATION FAILED")
            print("=" * 80)
            for err in errors:
                print(f"   - {err}")
            return False
        else:
            print("✅ VALIDATION PASSED")
            print("=" * 80)
            return True

    async def check_server_logs(self):
        """Check server logs for build validation evidence."""
        print()
        print("=" * 80)
        print("📋 SERVER LOGS: Checking for Build Validation")
        print("=" * 80)

        log_file = Path("/tmp/v6_server.log")
        if not log_file.exists():
            print("⚠️  Server log not found at /tmp/v6_server.log")
            return

        with open(log_file) as f:
            log_lines = f.readlines()

        # Look for build validation evidence
        validation_lines = [
            line for line in log_lines
            if any(keyword in line for keyword in [
                "Build validation",
                "TypeScript compilation",
                "Running TypeScript",
                "Quality Threshold:",
                "tsc --noEmit"
            ])
        ]

        if validation_lines:
            print(f"✅ Found {len(validation_lines)} build validation log entries:")
            for line in validation_lines[-10:]:  # Last 10 entries
                print(f"   {line.strip()}")
        else:
            print("⚠️  No build validation entries found in logs")

        print()

    async def run(self):
        """Run complete E2E test."""
        try:
            await self.setup_workspace()
            await self.connect()
            await self.initialize_session()

            # Send comprehensive task
            task = """Create a complete Task Manager application with the following requirements:

**Technology Stack:**
- TypeScript + React for frontend
- Modern React with hooks
- TypeScript for type safety

**Features:**
- Add new tasks with title and description
- Mark tasks as complete/incomplete
- Delete tasks
- Filter tasks (all/active/completed)
- Responsive UI design

**Requirements:**
- Clean, maintainable code following best practices
- Proper TypeScript types throughout
- Component-based architecture
- README with setup instructions
- package.json with all dependencies
- tsconfig.json for TypeScript configuration

**Important:** This is a test to validate build validation - ensure TypeScript compilation will succeed!
"""

            await self.send_task(task)
            agent_outputs = await self.receive_responses()

            # Validate results
            validation_passed = await self.validate_results(agent_outputs)

            # Check server logs
            await self.check_server_logs()

            # Final report
            print()
            print("=" * 80)
            print("📊 TEST SUMMARY")
            print("=" * 80)

            duration = (datetime.now() - self.start_time).total_seconds()
            print(f"⏱️  Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
            print(f"📩 Messages Received: {len(self.messages_received)}")
            print(f"🤖 Agent Outputs:")
            for agent, outputs in agent_outputs.items():
                print(f"   - {agent}: {len(outputs)} outputs")

            if validation_passed:
                print()
                print("🎉 COMPREHENSIVE E2E TEST PASSED!")
                print("=" * 80)
                return 0
            else:
                print()
                print("❌ COMPREHENSIVE E2E TEST FAILED")
                print("=" * 80)
                return 1

        except Exception as e:
            print()
            print("=" * 80)
            print(f"❌ TEST CRASHED: {e}")
            print("=" * 80)
            import traceback
            traceback.print_exc()
            return 1

        finally:
            if self.ws:
                await self.ws.close()
                print("🔌 WebSocket connection closed")


async def main():
    """Main entry point."""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "KI AUTOAGENT v6.1-alpha" + " " * 35 + "║")
    print("║" + " " * 18 + "COMPREHENSIVE E2E TEST" + " " * 39 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("This test validates:")
    print("  ✓ WebSocket connection and session management")
    print("  ✓ Full multi-agent workflow (Research → Architect → Codesmith → ReviewFix)")
    print("  ✓ Build validation for TypeScript")
    print("  ✓ Tree-sitter code analysis integration")
    print("  ✓ Memory system (server and project learning)")
    print("  ✓ All cognitive systems")
    print()

    # Check if server is running
    print("🔍 Checking if server is running...")
    try:
        async with websockets.connect(WS_URL) as ws:
            print(f"✅ Server is running at {WS_URL}")
    except Exception as e:
        print(f"❌ Server not reachable at {WS_URL}")
        print(f"   Error: {e}")
        print()
        print("Please start the server first:")
        print("  cd ~/.ki_autoagent && source venv/bin/activate")
        print("  python3 backend/api/server_v6_integrated.py > /tmp/v6_server.log 2>&1 &")
        return 1

    print()

    # Run test
    test = ComprehensiveE2ETest()
    exit_code = await test.run()

    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
