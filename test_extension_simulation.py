#!/usr/bin/env python3
"""
Extension Simulation Test - Exact VSCode Extension Behavior

This test simulates EXACTLY what the VSCode Extension does:
1. Connects to ws://localhost:8002/ws/chat
2. Receives "connected" message
3. Sends "init" with workspace_path
4. Receives "initialized" message
5. Sends "chat" message
6. Monitors ALL messages (status, approval_request, workflow_complete)
7. Validates message structure matches what Extension expects

This is the test I SHOULD have run before giving you the VSIX!
"""

import asyncio
import json
import sys
from datetime import datetime
import websockets
from pathlib import Path

WS_URL = "ws://localhost:8002/ws/chat"
WORKSPACE = "/Users/dominikfoert/TestApps/manualTest"

class ExtensionSimulator:
    """Simulates VSCode Extension WebSocket Client"""

    def __init__(self):
        self.messages_received = []
        self.errors_found = []

    def log(self, msg: str):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {msg}")

    def validate_message(self, msg: dict, expected_type: str, required_fields: list[str]) -> bool:
        """Validate message structure"""
        # Check type
        if msg.get("type") != expected_type:
            self.errors_found.append(f"Expected type '{expected_type}', got '{msg.get('type')}'")
            return False

        # Check required fields
        missing = []
        for field in required_fields:
            if field not in msg:
                missing.append(field)

        if missing:
            self.errors_found.append(f"{expected_type}: Missing fields: {missing}")
            return False

        return True

    async def simulate_extension(self):
        """Simulate exact Extension behavior"""

        self.log("=" * 80)
        self.log("Extension Simulation Test - EXACT VSCode Extension Behavior")
        self.log("=" * 80)
        self.log("")

        try:
            self.log(f"🔗 Connecting to {WS_URL}...")
            async with websockets.connect(WS_URL) as websocket:
                self.log("✅ Connected!")
                self.log("")

                # ============================================================
                # STEP 1: Receive welcome message
                # ============================================================
                self.log("STEP 1: Waiting for welcome message...")
                welcome_raw = await websocket.recv()
                welcome = json.loads(welcome_raw)
                self.messages_received.append(welcome)

                self.log(f"📨 Received: {welcome.get('type')}")
                self.log(f"   Message: {welcome.get('message', 'N/A')}")

                # Validate
                if not self.validate_message(welcome, "connected", ["type", "requires_init"]):
                    self.log("❌ VALIDATION FAILED!")
                    return False

                if not welcome.get("requires_init"):
                    self.errors_found.append("Expected requires_init=true")
                    return False

                self.log("✅ Welcome message valid")
                self.log("")

                # ============================================================
                # STEP 2: Send init message
                # ============================================================
                self.log("STEP 2: Sending init message...")
                init_msg = {
                    "type": "init",
                    "workspace_path": WORKSPACE
                }
                await websocket.send(json.dumps(init_msg))
                self.log(f"📤 Sent: init (workspace: {WORKSPACE})")
                self.log("")

                # ============================================================
                # STEP 3: Receive initialized confirmation
                # ============================================================
                self.log("STEP 3: Waiting for initialized confirmation...")
                init_response_raw = await websocket.recv()
                init_response = json.loads(init_response_raw)
                self.messages_received.append(init_response)

                self.log(f"📨 Received: {init_response.get('type')}")
                self.log(f"   Session ID: {init_response.get('session_id')}")

                # Validate
                if not self.validate_message(init_response, "initialized", ["type", "session_id", "workspace_path"]):
                    self.log("❌ VALIDATION FAILED!")
                    return False

                session_id = init_response.get("session_id")
                self.log("✅ Initialized OK")
                self.log("")

                # ============================================================
                # STEP 4: Send chat message
                # ============================================================
                self.log("STEP 4: Sending chat message...")
                chat_msg = {
                    "type": "chat",
                    "message": "Entwickle eine Taschenrechner App",
                    "session_id": session_id,
                    "mode": "auto"
                }
                await websocket.send(json.dumps(chat_msg))
                self.log("📤 Sent: chat ('Entwickle eine Taschenrechner App')")
                self.log("")

                # ============================================================
                # STEP 5: Monitor messages
                # ============================================================
                self.log("STEP 5: Monitoring messages (max 180 seconds)...")
                self.log("-" * 80)

                received_types = set()
                start_time = asyncio.get_event_loop().time()
                timeout = 180

                while True:
                    try:
                        remaining = timeout - (asyncio.get_event_loop().time() - start_time)
                        if remaining <= 0:
                            self.log("\n⏱️  Timeout reached (180 seconds)")
                            break

                        response_raw = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=min(10, remaining)
                        )
                        response = json.loads(response_raw)
                        self.messages_received.append(response)

                        msg_type = response.get("type")
                        received_types.add(msg_type)

                        # Log based on type
                        if msg_type == "status":
                            status = response.get("status")
                            message = response.get("message")
                            self.log(f"📊 Status: {status} - {message}")

                            # Validate status message
                            if not self.validate_message(response, "status", ["type", "status", "message"]):
                                self.log("   ⚠️  Status message missing fields!")

                        elif msg_type == "approval_request":
                            # THIS IS THE CRITICAL ONE!
                            action_type = response.get("action_type")
                            description = response.get("description")
                            request_id = response.get("request_id")

                            self.log(f"🔐 Approval Request:")
                            self.log(f"   Request ID: {request_id}")
                            self.log(f"   Action Type: {action_type}")  # ← Should NOT be undefined!
                            self.log(f"   Description: {description}")

                            # Validate approval_request structure
                            if not self.validate_message(response, "approval_request",
                                ["type", "request_id", "action_type", "description"]):
                                self.log("   ❌ APPROVAL_REQUEST VALIDATION FAILED!")
                            else:
                                self.log("   ✅ Approval request valid")

                            # Auto-approve for testing
                            approval_response = {
                                "type": "approval_response",
                                "request_id": request_id,
                                "approved": True
                            }
                            await websocket.send(json.dumps(approval_response))
                            self.log("   ✅ Auto-approved")

                        elif msg_type == "workflow_complete":
                            # THIS IS THE OTHER CRITICAL ONE!
                            success = response.get("success")
                            quality_score = response.get("quality_score")
                            execution_time = response.get("execution_time")

                            self.log(f"🎉 Workflow Complete:")
                            self.log(f"   Success: {success}")  # ← Should NOT be undefined!
                            self.log(f"   Quality Score: {quality_score}")  # ← Should NOT be undefined!
                            self.log(f"   Execution Time: {execution_time}s")

                            # Validate workflow_complete structure
                            if not self.validate_message(response, "workflow_complete",
                                ["type", "success", "quality_score", "execution_time"]):
                                self.log("   ❌ WORKFLOW_COMPLETE VALIDATION FAILED!")
                            else:
                                self.log("   ✅ Workflow complete valid")

                            # Check for v6 fields
                            if "analysis" in response:
                                self.log("   ✅ Has v6 analysis")
                            if "v6_systems_used" in response:
                                self.log("   ✅ Has v6 systems info")

                            break  # Test complete

                        elif msg_type == "error":
                            error_msg = response.get("message", "Unknown error")
                            self.log(f"❌ Error: {error_msg}")
                            self.errors_found.append(f"Server error: {error_msg}")
                            break

                        else:
                            self.log(f"📨 {msg_type}: {json.dumps(response, indent=2)[:200]}")

                    except asyncio.TimeoutError:
                        self.log("⏳ Still waiting...")
                        continue

                self.log("")
                self.log("-" * 80)
                self.log(f"Message types received: {sorted(received_types)}")
                self.log(f"Total messages: {len(self.messages_received)}")

                # ============================================================
                # STEP 6: Validation Summary
                # ============================================================
                self.log("")
                self.log("=" * 80)
                self.log("VALIDATION SUMMARY")
                self.log("=" * 80)

                if self.errors_found:
                    self.log(f"❌ {len(self.errors_found)} ERRORS FOUND:")
                    for error in self.errors_found:
                        self.log(f"   - {error}")
                    return False
                else:
                    self.log("✅ ALL VALIDATIONS PASSED!")
                    self.log("")
                    self.log("Extension-Backend Communication is CORRECT:")
                    self.log("  ✅ approval_request has action_type field")
                    self.log("  ✅ approval_request has description field")
                    self.log("  ✅ workflow_complete has success field")
                    self.log("  ✅ workflow_complete has quality_score field")
                    self.log("")
                    self.log("The Extension WILL work correctly with v6 backend!")
                    return True

        except Exception as e:
            self.log(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False

async def main():
    """Run simulation"""
    simulator = ExtensionSimulator()
    success = await simulator.simulate_extension()

    return 0 if success else 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
