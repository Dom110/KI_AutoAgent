#!/usr/bin/env python
"""
Simple AI Factory Test

Tests the AI Factory system with a minimal code generation task.
This validates that all agents work with their configured providers.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
import websockets
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
global_env = Path.home() / ".ki_autoagent" / "config" / ".env"
if global_env.exists():
    load_dotenv(global_env)


# Test configuration
BACKEND_WS_URL = "ws://localhost:8002/ws/chat"
TEST_WORKSPACE = Path.home() / "TestApps" / "ai_factory_test"
TEST_TIMEOUT = 300  # 5 minutes

# Simple task for testing
SIMPLE_TASK = """Create a simple Python calculator module that can:
- Add two numbers
- Subtract two numbers
- Include docstrings and type hints
- Include a test file with pytest tests

Keep it simple - just these two functions and their tests."""


async def run_simple_test():
    """Run simple AI Factory test."""
    print("="*60)
    print("🧪 AI Factory Simple Test")
    print("="*60)
    print(f"Backend: {BACKEND_WS_URL}")
    print(f"Workspace: {TEST_WORKSPACE}")
    print("="*60)

    # Create workspace
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    print(f"✅ Workspace created: {TEST_WORKSPACE}")

    # Connect to backend
    print(f"\n🔌 Connecting to {BACKEND_WS_URL}...")

    try:
        ws = await websockets.connect(BACKEND_WS_URL, ping_interval=30)
        print("✅ Connected")

        # Send init message
        init_msg = {
            "type": "init",
            "workspace_path": str(TEST_WORKSPACE)
        }
        await ws.send(json.dumps(init_msg))
        print(f"📤 Sent init with workspace: {TEST_WORKSPACE}")

        # Wait for init confirmation
        response = await ws.recv()
        data = json.loads(response)
        if data.get("type") == "init_complete":
            print("✅ Initialization confirmed")
        else:
            print(f"⚠️ Unexpected init response: {data.get('type')}")

        # Send task
        print("\n" + "="*60)
        print("📋 SENDING TASK")
        print("="*60)
        print(f"Task: {SIMPLE_TASK[:100]}...")

        task_msg = {
            "type": "task",
            "task": SIMPLE_TASK
        }
        await ws.send(json.dumps(task_msg))
        print("✅ Task sent")

        # Receive messages
        print("\n" + "="*60)
        print("📥 RECEIVING WORKFLOW MESSAGES")
        print("="*60)

        start_time = time.time()
        message_count = 0
        completed = False
        agents_executed = []
        files_generated = []
        errors = []

        while True:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > TEST_TIMEOUT:
                print(f"\n⏱️ Timeout after {TEST_TIMEOUT}s")
                errors.append(f"Timeout after {TEST_TIMEOUT}s")
                break

            # Receive message with timeout
            try:
                message = await asyncio.wait_for(
                    ws.recv(),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                print("⏱️ 30s receive timeout - checking if workflow complete...")
                continue

            message_count += 1
            data = json.loads(message)
            msg_type = data.get("type")

            # Progress indicator
            if message_count % 5 == 0:
                print(f"\n[{message_count} messages | {elapsed:.1f}s elapsed]")

            # Process message
            if msg_type == "supervisor_decision":
                agent = data.get("agent", "unknown")
                instructions = data.get("instructions", "")[:80]
                print(f"\n🎯 SUPERVISOR → {agent.upper()}")
                print(f"   Instructions: {instructions}...")

            elif msg_type == "agent_start":
                agent = data.get("agent", "unknown")
                print(f"\n🚀 {agent.upper()} STARTED")
                agents_executed.append(agent)

            elif msg_type == "agent_complete":
                agent = data.get("agent", "unknown")
                print(f"✅ {agent.upper()} COMPLETED")

            elif msg_type == "file_generated":
                file_path = data.get("file", "unknown")
                print(f"   📄 File generated: {file_path}")
                files_generated.append(file_path)

            elif msg_type == "code_generated":
                files = data.get("files", [])
                print(f"   ✅ Code generated: {len(files)} files")
                files_generated.extend(files)

            elif msg_type == "workflow_complete":
                print("\n✅ WORKFLOW COMPLETE")
                completed = True
                break

            elif msg_type == "error":
                error = data.get("error", "Unknown")
                print(f"\n❌ ERROR: {error}")
                errors.append(error)
                break

            elif msg_type in ["research_started", "research_complete",
                            "architecture_complete", "review_started",
                            "review_complete", "responder_message"]:
                print(f"   📨 {msg_type}")

        # Close connection
        await ws.close()
        print("\n🔌 Connection closed")

        # Print summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"Status: {'✅ COMPLETED' if completed else '❌ INCOMPLETE'}")
        print(f"Time: {elapsed:.2f}s")
        print(f"Messages: {message_count}")
        print(f"\nAgents Executed: {len(agents_executed)}")
        for agent in agents_executed:
            print(f"  - {agent}")
        print(f"\nFiles Generated: {len(files_generated)}")
        for file in files_generated:
            print(f"  - {file}")
        print(f"\nErrors: {len(errors)}")
        for error in errors:
            print(f"  - {error}")

        # Validation
        print("\n" + "="*60)
        print("🎯 VALIDATION RESULTS")
        print("="*60)

        failures = []

        if not completed:
            failures.append("❌ Workflow did not complete")

        if "research" not in agents_executed:
            failures.append("❌ Research agent not executed")

        if "architect" not in agents_executed:
            failures.append("❌ Architect agent not executed")

        if "codesmith" not in agents_executed:
            failures.append("❌ Codesmith agent not executed")

        if len(files_generated) < 1:
            failures.append("❌ No files were generated")

        if len(errors) > 0:
            failures.append(f"❌ {len(errors)} errors occurred")

        if len(failures) == 0:
            print("✅ ALL CHECKS PASSED")
            print("\nAI Factory Validation:")
            print("  ✅ Research agent (Perplexity) working")
            print("  ✅ Architect agent (OpenAI) working")
            print("  ✅ Codesmith agent (Claude CLI) working")
            print("  ✅ Files generated successfully")
            print("\n🎉 AI FACTORY SYSTEM IS WORKING!")
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
        exit_code = asyncio.run(run_simple_test())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
