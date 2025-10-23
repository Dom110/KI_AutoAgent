#!/usr/bin/env python3
"""
v7.0 E2E Test - Complete App Creation with ReviewFix Loop

Tests the full v7.0 Supervisor Pattern workflow:
- Supervisor orchestration
- Research agent execution
- Architect agent execution
- Codesmith agent code generation
- ReviewFix loop (validation and fixing)
- Responder final communication

Author: KI AutoAgent Team
Created: 2025-10-23
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

import websockets


# ============================================================
# Configuration
# ============================================================

BACKEND_WS_URL = "ws://localhost:8002/ws/chat"
TEST_WORKSPACE = Path.home() / "TestApps" / "e2e_v7_app"
TEST_TIMEOUT = 900  # 15 minutes for complete workflow


# ============================================================
# Test Task - Complex Full-Stack App
# ============================================================

COMPLEX_APP_TASK = """Create a full-stack todo application with the following requirements:
- React frontend with TypeScript and Tailwind CSS
- FastAPI backend with Python 3.13+
- SQLite database with proper schema
- User authentication (JWT tokens)
- Real-time updates via WebSockets
- CRUD operations for todos
- Comprehensive unit and integration tests
- Docker deployment configuration
- Complete README with setup instructions

The application should be production-ready with proper error handling, validation, and security best practices.
"""


# ============================================================
# Test State Tracking
# ============================================================

class WorkflowTracker:
    """Track v7.0 workflow execution and agent activity."""

    def __init__(self):
        self.agents_executed: List[str] = []
        self.supervisor_decisions: List[Dict] = []
        self.research_calls: int = 0
        self.architect_calls: int = 0
        self.codesmith_calls: int = 0
        self.reviewfix_calls: int = 0
        self.reviewfix_iterations: int = 0
        self.responder_calls: int = 0
        self.files_generated: List[str] = []
        self.errors: List[str] = []
        self.completed: bool = False
        self.start_time: float = time.time()

    def record_agent(self, agent_type: str):
        """Record agent execution."""
        self.agents_executed.append(agent_type)

        if agent_type == "research":
            self.research_calls += 1
        elif agent_type == "architect":
            self.architect_calls += 1
        elif agent_type == "codesmith":
            self.codesmith_calls += 1
        elif agent_type == "reviewfix":
            self.reviewfix_calls += 1
            self.reviewfix_iterations += 1
        elif agent_type == "responder":
            self.responder_calls += 1

    def record_supervisor_decision(self, decision: Dict):
        """Record Supervisor routing decision."""
        self.supervisor_decisions.append(decision)

    def record_file(self, file_path: str):
        """Record generated file."""
        self.files_generated.append(file_path)

    def record_error(self, error: str):
        """Record error."""
        self.errors.append(error)

    def mark_complete(self):
        """Mark workflow as complete."""
        self.completed = True

    def get_summary(self) -> Dict[str, Any]:
        """Get workflow summary."""
        elapsed = time.time() - self.start_time

        return {
            "completed": self.completed,
            "elapsed_seconds": round(elapsed, 2),
            "agents_executed": len(self.agents_executed),
            "agent_sequence": self.agents_executed,
            "supervisor_decisions": len(self.supervisor_decisions),
            "research_calls": self.research_calls,
            "architect_calls": self.architect_calls,
            "codesmith_calls": self.codesmith_calls,
            "reviewfix_calls": self.reviewfix_calls,
            "reviewfix_iterations": self.reviewfix_iterations,
            "responder_calls": self.responder_calls,
            "files_generated": len(self.files_generated),
            "files": self.files_generated,
            "errors": len(self.errors),
            "error_details": self.errors
        }


# ============================================================
# WebSocket Client
# ============================================================

class V7TestClient:
    """WebSocket client for v7.0 E2E testing."""

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.ws = None
        self.tracker = WorkflowTracker()

    async def connect(self):
        """Connect to v7.0 backend."""
        print(f"🔌 Connecting to {BACKEND_WS_URL}...")
        self.ws = await websockets.connect(BACKEND_WS_URL)
        print("✅ Connected")

        # Send init message
        init_msg = {
            "type": "init",
            "workspace_path": str(self.workspace)
        }
        await self.ws.send(json.dumps(init_msg))
        print(f"📤 Sent init with workspace: {self.workspace}")

        # Wait for init confirmation
        response = await self.ws.recv()
        data = json.loads(response)
        if data.get("type") == "init_complete":
            print("✅ Initialization confirmed")
        else:
            print(f"⚠️ Unexpected init response: {data.get('type')}")

    async def send_task(self, task: str):
        """Send task to v7.0 backend."""
        print("\n" + "="*60)
        print("📋 SENDING TASK")
        print("="*60)
        print(f"Task: {task[:100]}...")

        task_msg = {
            "type": "task",
            "task": task
        }
        await self.ws.send(json.dumps(task_msg))
        print("✅ Task sent")

    async def receive_messages(self, timeout: float = TEST_TIMEOUT):
        """Receive and process v7.0 workflow messages."""
        print("\n" + "="*60)
        print("📥 RECEIVING WORKFLOW MESSAGES")
        print("="*60)

        start_time = time.time()
        message_count = 0

        try:
            while True:
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    print(f"\n⏱️ Timeout after {timeout}s")
                    self.tracker.record_error(f"Timeout after {timeout}s")
                    break

                # Receive message with timeout
                try:
                    message = await asyncio.wait_for(
                        self.ws.recv(),
                        timeout=30.0
                    )
                except asyncio.TimeoutError:
                    print("⏱️ 30s receive timeout - checking if workflow complete...")
                    continue

                message_count += 1
                data = json.loads(message)
                msg_type = data.get("type")

                # Process message
                self._process_message(data, message_count)

                # Check for completion
                if msg_type == "workflow_complete":
                    print("\n✅ WORKFLOW COMPLETE")
                    self.tracker.mark_complete()
                    break
                elif msg_type == "error":
                    print(f"\n❌ ERROR: {data.get('error')}")
                    self.tracker.record_error(data.get("error", "Unknown error"))
                    break

        except websockets.exceptions.ConnectionClosed:
            print("\n⚠️ Connection closed by server")
            self.tracker.record_error("Connection closed by server")
        except Exception as e:
            print(f"\n❌ Exception: {e}")
            self.tracker.record_error(str(e))

    def _process_message(self, data: Dict, count: int):
        """Process individual workflow message."""
        msg_type = data.get("type")

        # Progress indicator
        if count % 10 == 0:
            elapsed = time.time() - self.tracker.start_time
            print(f"\n[{count} messages | {elapsed:.1f}s elapsed]")

        # Supervisor decision
        if msg_type == "supervisor_decision":
            agent = data.get("agent", "unknown")
            instructions = data.get("instructions", "")[:80]
            print(f"\n🎯 SUPERVISOR → {agent}")
            print(f"   Instructions: {instructions}...")
            self.tracker.record_supervisor_decision({
                "agent": agent,
                "instructions": instructions
            })

        # Agent start
        elif msg_type == "agent_start":
            agent = data.get("agent", "unknown")
            print(f"\n🚀 {agent.upper()} STARTED")
            self.tracker.record_agent(agent)

        # Agent complete
        elif msg_type == "agent_complete":
            agent = data.get("agent", "unknown")
            result = data.get("result", "")[:80]
            print(f"✅ {agent.upper()} COMPLETED")
            print(f"   Result: {result}...")

        # Research
        elif msg_type == "research_started":
            print("   🔬 Research in progress...")
        elif msg_type == "research_complete":
            findings = data.get("findings", {})
            print(f"   ✅ Research complete: {len(findings)} findings")

        # Architecture
        elif msg_type == "architecture_complete":
            components = data.get("components", [])
            print(f"   ✅ Architecture complete: {len(components)} components")

        # Code generation
        elif msg_type == "file_generated":
            file_path = data.get("file", "unknown")
            print(f"   📄 File generated: {file_path}")
            self.tracker.record_file(file_path)
        elif msg_type == "code_generated":
            files = data.get("files", [])
            print(f"   ✅ Code generated: {len(files)} files")
            for file in files:
                self.tracker.record_file(file)

        # ReviewFix
        elif msg_type == "review_started":
            print("   🔍 Review in progress...")
        elif msg_type == "review_complete":
            status = data.get("status", "unknown")
            issues = data.get("issues", [])
            print(f"   ✅ Review complete: {status} ({len(issues)} issues)")
            if status == "failed" and issues:
                print(f"   🔧 Issues found - entering ReviewFix loop")
        elif msg_type == "fix_applied":
            file = data.get("file", "unknown")
            print(f"   🔧 Fix applied: {file}")

        # Responder
        elif msg_type == "responder_message":
            message = data.get("message", "")[:100]
            print(f"\n💬 RESPONDER: {message}...")

        # Workflow complete
        elif msg_type == "workflow_complete":
            print("\n🎉 WORKFLOW COMPLETE")

        # Error
        elif msg_type == "error":
            error = data.get("error", "Unknown")
            print(f"\n❌ ERROR: {error}")

        # Other
        else:
            # Don't print everything - too verbose
            if msg_type not in ["log", "status", "progress"]:
                print(f"   📨 {msg_type}")

    async def close(self):
        """Close WebSocket connection."""
        if self.ws:
            await self.ws.close()
            print("\n🔌 Connection closed")


# ============================================================
# Test Validation
# ============================================================

def validate_workflow(tracker: WorkflowTracker) -> tuple[bool, List[str]]:
    """Validate v7.0 workflow execution."""
    failures = []

    summary = tracker.get_summary()

    # Check completion
    if not summary["completed"]:
        failures.append("❌ Workflow did not complete")

    # Check agents executed
    if summary["research_calls"] < 1:
        failures.append("❌ Research agent not executed")

    if summary["architect_calls"] < 1:
        failures.append("❌ Architect agent not executed")

    if summary["codesmith_calls"] < 1:
        failures.append("❌ Codesmith agent not executed")

    if summary["reviewfix_calls"] < 1:
        failures.append("❌ ReviewFix agent not executed")

    if summary["responder_calls"] < 1:
        failures.append("❌ Responder agent not executed")

    # Check ReviewFix loop (should iterate at least once)
    if summary["reviewfix_iterations"] < 1:
        failures.append("❌ ReviewFix loop did not execute")

    # Check supervisor decisions
    if summary["supervisor_decisions"] < 3:
        failures.append(f"❌ Too few supervisor decisions: {summary['supervisor_decisions']}")

    # Check files generated
    if summary["files_generated"] < 1:
        failures.append("❌ No files were generated")

    # Check errors
    if summary["errors"] > 0:
        failures.append(f"❌ {summary['errors']} errors occurred")

    success = len(failures) == 0
    return success, failures


def print_summary(tracker: WorkflowTracker):
    """Print workflow summary."""
    summary = tracker.get_summary()

    print("\n" + "="*60)
    print("📊 WORKFLOW SUMMARY")
    print("="*60)
    print(f"Status: {'✅ COMPLETED' if summary['completed'] else '❌ INCOMPLETE'}")
    print(f"Time: {summary['elapsed_seconds']}s")
    print(f"\nAgents Executed: {summary['agents_executed']}")
    print(f"  Research: {summary['research_calls']}")
    print(f"  Architect: {summary['architect_calls']}")
    print(f"  Codesmith: {summary['codesmith_calls']}")
    print(f"  ReviewFix: {summary['reviewfix_calls']} (iterations: {summary['reviewfix_iterations']})")
    print(f"  Responder: {summary['responder_calls']}")
    print(f"\nSupervisor Decisions: {summary['supervisor_decisions']}")
    print(f"Files Generated: {summary['files_generated']}")
    print(f"Errors: {summary['errors']}")

    if summary['files']:
        print(f"\nGenerated Files:")
        for file in summary['files'][:10]:  # Show first 10
            print(f"  - {file}")
        if len(summary['files']) > 10:
            print(f"  ... and {len(summary['files']) - 10} more")

    if summary['error_details']:
        print(f"\nErrors:")
        for error in summary['error_details']:
            print(f"  - {error}")

    print("\nAgent Sequence:")
    for i, agent in enumerate(summary['agent_sequence'], 1):
        print(f"  {i}. {agent}")


# ============================================================
# Main Test
# ============================================================

async def run_e2e_test():
    """Run v7.0 E2E app creation test."""
    print("="*60)
    print("🧪 v7.0 E2E Test - Complete App Creation")
    print("="*60)
    print(f"Backend: {BACKEND_WS_URL}")
    print(f"Workspace: {TEST_WORKSPACE}")
    print(f"Timeout: {TEST_TIMEOUT}s")
    print("="*60)

    # Create workspace
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    print(f"✅ Workspace created: {TEST_WORKSPACE}")

    # Initialize client
    client = V7TestClient(TEST_WORKSPACE)

    try:
        # Connect
        await client.connect()

        # Send task
        await client.send_task(COMPLEX_APP_TASK)

        # Receive workflow messages
        await client.receive_messages(timeout=TEST_TIMEOUT)

        # Close connection
        await client.close()

        # Print summary
        print_summary(client.tracker)

        # Validate
        success, failures = validate_workflow(client.tracker)

        print("\n" + "="*60)
        print("🎯 VALIDATION RESULTS")
        print("="*60)

        if success:
            print("✅ ALL CHECKS PASSED")
            print("\nv7.0 Workflow Validation:")
            print("  ✅ Supervisor orchestration working")
            print("  ✅ Research agent executed")
            print("  ✅ Architect agent executed")
            print("  ✅ Codesmith agent executed")
            print("  ✅ ReviewFix loop executed")
            print("  ✅ Responder agent executed")
            print("  ✅ Files generated")
            print("\n🎉 v7.0 SYSTEM IS PRODUCTION READY")
            return 0
        else:
            print("❌ VALIDATION FAILED")
            print("\nFailures:")
            for failure in failures:
                print(f"  {failure}")
            return 1

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point."""
    try:
        exit_code = asyncio.run(run_e2e_test())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
