#!/usr/bin/env python3
"""
REAL Extension Test - Following Testing Lessons Learned

This test does what I SHOULD have done from the start:
1. Simulates COMPLETE Extension behavior with ALL message types
2. Verifies FILES are created in workspace
3. Verifies FILE CONTENT is valid
4. Checks for "undefined" in ALL messages
5. Tests COMPLETE agent flow with intermediate messages

TESTING LESSONS APPLIED:
- ASIMOV TESTING RULE 1: Verify Outputs, Not Just Status
- ASIMOV TESTING RULE 2: Test Complete User Journey
- ASIMOV TESTING RULE 3: Global Impact Verification
- ASIMOV TESTING RULE 4: Never Ignore Warnings
- ASIMOV TESTING RULE 5: Measure Real Success Criteria
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
import websockets

WS_URL = "ws://localhost:8002/ws/chat"
WORKSPACE = "/Users/dominikfoert/TestApps/manualTest"

class RealExtensionTest:
    """Real Extension Test with complete verification"""

    def __init__(self):
        self.messages_received = []
        self.errors_found = []
        self.warnings_found = []
        self.agent_messages = {
            "research": [],
            "architect": [],
            "codesmith": [],
            "reviewfix": []
        }
        self.workspace = Path(WORKSPACE)

    def log(self, msg: str):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {msg}")

    def check_for_undefined(self, obj: dict, path: str = ""):
        """Recursively check for undefined/null values"""
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key

            if value is None:
                self.warnings_found.append(f"NULL value at {current_path}")
            elif value == "undefined":
                self.warnings_found.append(f"UNDEFINED at {current_path}")
            elif isinstance(value, dict):
                self.check_for_undefined(value, current_path)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        self.check_for_undefined(item, f"{current_path}[{i}]")

    def verify_workspace_outputs(self) -> dict:
        """Verify files created in workspace"""
        self.log("")
        self.log("=" * 80)
        self.log("WORKSPACE VERIFICATION")
        self.log("=" * 80)

        if not self.workspace.exists():
            self.errors_found.append(f"Workspace doesn't exist: {self.workspace}")
            return {"success": False, "files": []}

        # List all files
        files = []
        for file in self.workspace.rglob("*"):
            if file.is_file() and not file.name.startswith('.'):
                files.append(str(file.relative_to(self.workspace)))

        self.log(f"📁 Files in workspace: {len(files)}")

        if len(files) == 0:
            self.errors_found.append("NO FILES CREATED!")
            self.log("❌ NO FILES CREATED IN WORKSPACE!")
            return {"success": False, "files": []}

        # Verify each file
        for file_rel in files:
            file_path = self.workspace / file_rel
            self.log(f"   📄 {file_rel}")

            # Check file size
            size = file_path.stat().st_size
            self.log(f"      Size: {size} bytes")

            if size == 0:
                self.errors_found.append(f"File is empty: {file_rel}")
                continue

            # Check content
            try:
                content = file_path.read_text()

                # Check for TODOs (ASIMOV RULE 2)
                if "TODO" in content or "FIXME" in content:
                    self.errors_found.append(f"File has TODOs: {file_rel}")
                    self.log(f"      ❌ Has TODO/FIXME!")

                # Check for placeholders
                if "..." in content or "pass" in content:
                    self.warnings_found.append(f"File may have placeholders: {file_rel}")

                self.log(f"      ✅ Content OK ({len(content)} chars)")

            except Exception as e:
                self.warnings_found.append(f"Can't read {file_rel}: {e}")

        return {"success": len(files) > 0, "files": files, "count": len(files)}

    async def run_test(self):
        """Run complete test"""

        self.log("=" * 80)
        self.log("REAL Extension Test - Complete Verification")
        self.log("=" * 80)
        self.log("")

        # Clean workspace first
        self.log("🧹 Cleaning workspace...")
        if self.workspace.exists():
            for file in self.workspace.rglob("*"):
                if file.is_file() and not str(file).endswith('.ki_autoagent_ws'):
                    file.unlink()
                    self.log(f"   Deleted: {file.name}")

        try:
            self.log(f"🔗 Connecting to {WS_URL}...")
            async with websockets.connect(WS_URL) as websocket:
                self.log("✅ Connected!")
                self.log("")

                # Step 1: Welcome
                welcome = json.loads(await websocket.recv())
                self.messages_received.append(welcome)
                self.check_for_undefined(welcome)
                self.log(f"📨 Welcome: {welcome.get('type')}")

                # Step 2: Init
                init_msg = {"type": "init", "workspace_path": WORKSPACE}
                await websocket.send(json.dumps(init_msg))
                self.log(f"📤 Init sent")

                # Step 3: Initialized
                initialized = json.loads(await websocket.recv())
                self.messages_received.append(initialized)
                self.check_for_undefined(initialized)
                session_id = initialized.get("session_id")
                self.log(f"📨 Initialized: {session_id}")
                self.log("")

                # Step 4: Send REAL task
                task = "Create a simple calculator app in Python with:\n" \
                       "1. add, subtract, multiply, divide functions\n" \
                       "2. tests for all functions\n" \
                       "3. README with usage instructions"

                chat_msg = {
                    "type": "chat",
                    "message": task,
                    "session_id": session_id,
                    "mode": "auto"
                }
                await websocket.send(json.dumps(chat_msg))
                self.log(f"📤 Task sent: {task[:50]}...")
                self.log("")
                self.log("=" * 80)
                self.log("MONITORING WORKFLOW")
                self.log("=" * 80)

                # Step 5: Monitor ALL messages
                start_time = asyncio.get_event_loop().time()
                timeout = 300  # 5 minutes
                received_types = set()

                while True:
                    try:
                        remaining = timeout - (asyncio.get_event_loop().time() - start_time)
                        if remaining <= 0:
                            self.log("\n⏱️  Timeout!")
                            break

                        msg_raw = await asyncio.wait_for(websocket.recv(), timeout=min(15, remaining))
                        msg = json.loads(msg_raw)
                        self.messages_received.append(msg)
                        self.check_for_undefined(msg)

                        msg_type = msg.get("type")
                        received_types.add(msg_type)

                        # Log based on type
                        if msg_type == "status":
                            self.log(f"📊 Status: {msg.get('status')} - {msg.get('message')}")

                        elif msg_type == "agent_thinking":
                            agent = msg.get("agent", "unknown")
                            content = msg.get("content", "")[:100]
                            self.log(f"🤔 {agent} thinking: {content}...")
                            self.agent_messages.get(agent, []).append(msg)

                        elif msg_type == "agent_progress":
                            agent = msg.get("agent", "unknown")
                            progress = msg.get("message", "")
                            self.log(f"📊 {agent} progress: {progress}")
                            self.agent_messages.get(agent, []).append(msg)

                        elif msg_type == "agent_response":
                            agent = msg.get("agent", "unknown")
                            self.log(f"💬 {agent} response received")
                            self.agent_messages.get(agent, []).append(msg)

                        elif msg_type == "approval_request":
                            action = msg.get("action_type")
                            desc = msg.get("description")
                            req_id = msg.get("request_id")
                            self.log(f"🔐 Approval: {action} - {desc}")

                            # Check for undefined
                            if action is None or action == "undefined":
                                self.errors_found.append("action_type is undefined!")

                            # Auto-approve
                            await websocket.send(json.dumps({
                                "type": "approval_response",
                                "request_id": req_id,
                                "approved": True
                            }))
                            self.log("   ✅ Approved")

                        elif msg_type == "workflow_complete":
                            success = msg.get("success")
                            quality = msg.get("quality_score")
                            exec_time = msg.get("execution_time")

                            self.log("")
                            self.log("🎉 Workflow Complete!")
                            self.log(f"   Success: {success}")
                            self.log(f"   Quality: {quality}")
                            self.log(f"   Time: {exec_time}s")

                            # Check for undefined
                            if success is None or success == "undefined":
                                self.errors_found.append("success is undefined!")
                            if quality is None or quality == "undefined":
                                self.errors_found.append("quality_score is undefined!")

                            break

                        elif msg_type == "error":
                            error_msg = msg.get("message", "Unknown")
                            self.log(f"❌ Error: {error_msg}")
                            self.errors_found.append(f"Workflow error: {error_msg}")
                            break

                    except asyncio.TimeoutError:
                        self.log("⏳ Still waiting...")
                        continue

                # Verify workspace
                workspace_result = self.verify_workspace_outputs()

                # Final summary
                self.log("")
                self.log("=" * 80)
                self.log("TEST RESULTS")
                self.log("=" * 80)

                self.log(f"Messages received: {len(self.messages_received)}")
                self.log(f"Message types: {sorted(received_types)}")
                self.log(f"Files created: {workspace_result.get('count', 0)}")

                # Agent coverage
                self.log("")
                self.log("Agent Message Coverage:")
                for agent, msgs in self.agent_messages.items():
                    self.log(f"  {agent}: {len(msgs)} messages")

                # Errors and warnings
                self.log("")
                if self.errors_found:
                    self.log(f"❌ {len(self.errors_found)} ERRORS:")
                    for err in self.errors_found:
                        self.log(f"   - {err}")
                else:
                    self.log("✅ No errors")

                if self.warnings_found:
                    self.log(f"⚠️  {len(self.warnings_found)} WARNINGS:")
                    for warn in self.warnings_found:
                        self.log(f"   - {warn}")
                else:
                    self.log("✅ No warnings")

                # Success criteria
                self.log("")
                self.log("Success Criteria:")
                self.log(f"  Files created: {'✅' if workspace_result['success'] else '❌'}")
                self.log(f"  No errors: {'✅' if not self.errors_found else '❌'}")
                self.log(f"  No undefined: {'✅' if not self.warnings_found else '❌'}")
                self.log(f"  All agents ran: {'✅' if all(len(msgs) > 0 for msgs in self.agent_messages.values()) else '❌'}")

                success = (
                    workspace_result['success'] and
                    not self.errors_found and
                    not self.warnings_found
                )

                return success

        except Exception as e:
            self.log(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

async def main():
    test = RealExtensionTest()
    success = await test.run_test()
    return 0 if success else 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
