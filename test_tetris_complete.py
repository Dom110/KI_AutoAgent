#!/usr/bin/env python3
"""
Complete Tetris Workflow Test
Tests full workflow: orchestrator → architect → approval → codesmith → reviewer → fixer
"""
import asyncio
import websockets
import json
import time
from datetime import datetime

class TetrisWorkflowTest:
    def __init__(self):
        self.uri = "ws://localhost:8001/ws/chat"
        self.session_id = None
        self.client_id = None
        self.messages = []

        # Track workflow steps
        self.orchestrator_completed = False
        self.architect_proposal_received = False
        self.architect_completed = False
        self.codesmith_started = False
        self.codesmith_completed = False
        self.reviewer_started = False
        self.reviewer_completed = False
        self.fixer_started = False
        self.workflow_completed = False

    def log(self, message, emoji="📝"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {emoji} {message}")

    async def run_test(self):
        print("\n" + "="*80)
        print("🎮 COMPLETE TETRIS WORKFLOW TEST")
        print("="*80 + "\n")

        try:
            async with websockets.connect(self.uri) as ws:
                self.log("Connected to backend", "✅")

                # Receive connection
                msg = await ws.recv()
                data = json.loads(msg)
                self.session_id = data.get('session_id')
                self.client_id = data.get('client_id')
                self.log(f"Session: {self.session_id[:8]}...", "🔑")

                # Set workspace
                await ws.send(json.dumps({
                    "type": "setWorkspace",
                    "workspacePath": "/Users/dominikfoert/git/KI_AutoAgent"
                }))

                # Send task
                self.log("Sending task: 'Erstelle eine Tetris App mit TypeScript'", "📤")
                await ws.send(json.dumps({
                    "type": "chat",
                    "message": "Erstelle eine Tetris App mit TypeScript"
                }))

                # Listen for messages
                start_time = time.time()
                timeout = 300  # 5 minutes

                while time.time() - start_time < timeout:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=30.0)
                        data = json.loads(msg)
                        msg_type = data.get('type')
                        self.messages.append(data)

                        # Track workflow progress
                        if msg_type == "agent_thinking":
                            agent = data.get('agent', 'unknown')
                            self.log(f"{agent.upper()} thinking...", "💭")

                        elif msg_type == "step_completed":
                            agent = data.get('agent', 'unknown')
                            task = data.get('task', '')[:50]
                            self.log(f"{agent.upper()} completed: {task}...", "✅")

                            if agent == "orchestrator":
                                self.orchestrator_completed = True
                            elif agent == "architect":
                                self.architect_completed = True
                            elif agent == "codesmith":
                                self.codesmith_completed = True
                            elif agent == "reviewer":
                                self.reviewer_completed = True
                            elif agent == "fixer":
                                self.fixer_started = True

                        elif msg_type == "architecture_proposal":
                            self.log("ARCHITECTURE PROPOSAL RECEIVED!", "🏛️")
                            self.architect_proposal_received = True
                            proposal = data.get('proposal', {})

                            # Show proposal summary
                            summary = proposal.get('summary', 'N/A')
                            self.log(f"  Summary: {summary[:100]}...", "📋")

                            # Auto-approve
                            self.log("Sending approval...", "✅")
                            await ws.send(json.dumps({
                                "type": "architecture_approval",
                                "session_id": self.session_id,
                                "decision": "approved",
                                "feedback": "Approved for testing"
                            }))

                        elif msg_type == "architectureApprovalProcessed":
                            self.log("Approval processed - workflow resuming...", "🔄")

                        elif msg_type == "response":
                            content = data.get('content', '')
                            metadata = data.get('metadata', {})
                            agent = data.get('agent', 'unknown')

                            if content:
                                self.log(f"Response from {agent}: {str(content)[:80]}...", "📨")

                            status = metadata.get('status')
                            if status == 'completed':
                                self.workflow_completed = True
                                self.log("WORKFLOW COMPLETED!", "🎉")
                                break

                        elif msg_type == "error":
                            error_msg = data.get('message', 'Unknown error')
                            self.log(f"ERROR: {error_msg}", "❌")

                    except asyncio.TimeoutError:
                        self.log("Timeout waiting for message (workflow may still be running)", "⏱️")
                        continue

        except Exception as e:
            self.log(f"Test error: {e}", "❌")
            import traceback
            traceback.print_exc()

        # Print summary
        self.print_summary()

    def print_summary(self):
        print("\n" + "="*80)
        print("📊 WORKFLOW TEST SUMMARY")
        print("="*80 + "\n")

        print(f"Total messages received: {len(self.messages)}\n")

        print("Workflow Steps:")
        print(f"  ✅ Orchestrator completed: {self.orchestrator_completed}")
        print(f"  ✅ Architecture proposal received: {self.architect_proposal_received}")
        print(f"  ✅ Architect completed (after approval): {self.architect_completed}")
        print(f"  ✅ CodeSmith started: {self.codesmith_started}")
        print(f"  ✅ CodeSmith completed: {self.codesmith_completed}")
        print(f"  ✅ Reviewer started: {self.reviewer_started}")
        print(f"  ✅ Reviewer completed: {self.reviewer_completed}")
        print(f"  ✅ Fixer started: {self.fixer_started}")
        print(f"  ✅ Workflow completed: {self.workflow_completed}\n")

        # Message types
        msg_types = {}
        for msg in self.messages:
            msg_type = msg.get('type')
            msg_types[msg_type] = msg_types.get(msg_type, 0) + 1

        print("Message Types:")
        for msg_type, count in sorted(msg_types.items()):
            print(f"  {msg_type}: {count}")

        print("\n" + "="*80)

        # Overall result
        if self.workflow_completed and self.architect_proposal_received:
            print("✅ TEST PASSED - Complete workflow executed successfully!")
        elif self.architect_proposal_received and self.codesmith_started:
            print("⚠️  TEST PARTIAL - Workflow started but not completed")
        else:
            print("❌ TEST FAILED - Workflow did not execute properly")
        print("="*80 + "\n")

if __name__ == "__main__":
    test = TetrisWorkflowTest()
    asyncio.run(test.run_test())
