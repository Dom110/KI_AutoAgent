#!/usr/bin/env python3
"""
Sequential E2E Test Runner
Führt E2E Tests nacheinander aus, nicht parallel.
Jeder Test läuft nur, wenn der vorherige erfolgreich war.
"""

import asyncio
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import websockets

# Test workspace base directory
TEST_BASE = Path.home() / "TestApps"
SERVER_URL = "ws://localhost:8002/ws/chat"


class E2ETestCase:
    """Single E2E test case."""

    def __init__(self, name: str, workspace_name: str, task: str,
                 expected_files: List[str], timeout: int = 120):
        self.name = name
        self.workspace_name = workspace_name
        self.workspace_path = TEST_BASE / workspace_name
        self.task = task
        self.expected_files = expected_files
        self.timeout = timeout
        self.passed = False
        self.error = None
        self.events = []
        self.generated_files = []
        self.credit_used = 0.0
        self.duration = 0.0


class SequentialE2ERunner:
    """Runs E2E tests sequentially."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.test_cases: List[E2ETestCase] = []
        self.results = []

    def add_test(self, test_case: E2ETestCase):
        """Add a test case to the runner."""
        self.test_cases.append(test_case)

    async def run_single_test(self, test: E2ETestCase) -> bool:
        """
        Run a single E2E test case.
        Returns True if successful, False otherwise.
        """
        print("\n" + "="*100)
        print(f"🧪 TEST: {test.name}")
        print("="*100)
        print(f"📁 Workspace: {test.workspace_path}")
        print(f"📝 Task: {test.task[:80]}...")
        print(f"⏱️  Timeout: {test.timeout}s")
        print("-"*100)

        start_time = datetime.now()

        # Clean and create workspace
        if test.workspace_path.exists():
            shutil.rmtree(test.workspace_path)
        test.workspace_path.mkdir(parents=True, exist_ok=True)

        try:
            # Connect to WebSocket
            async with websockets.connect(SERVER_URL) as ws:
                print("✅ Connected to server")

                # Initialize session
                init_msg = {
                    "type": "init",
                    "workspace_path": str(test.workspace_path)
                }
                await ws.send(json.dumps(init_msg))

                # Wait for initialization
                init_response = await asyncio.wait_for(ws.recv(), timeout=5)
                init_data = json.loads(init_response)
                if init_data.get("type") != "initialized":
                    raise Exception(f"Init failed: {init_data}")

                print("✅ Session initialized")

                # Send task
                task_msg = {
                    "type": "chat",
                    "query": test.task  # Using "query" field as discovered
                }
                await ws.send(json.dumps(task_msg))
                print("📤 Task sent to server")

                # Collect events
                event_count = 0
                routing_decisions = []
                last_agent = None
                workflow_complete = False

                print("\n📥 Receiving events:")
                print("-"*50)

                try:
                    while True:
                        msg = await asyncio.wait_for(ws.recv(), timeout=test.timeout)
                        event = json.loads(msg)
                        event_count += 1
                        test.events.append(event)

                        event_type = event.get("type")

                        # Progress tracking
                        if self.verbose:
                            print(f"  [{event_count:3d}] {event_type}", end="")

                        if event_type == "workflow_event":
                            node = event.get("node")
                            update = event.get("state_update", {})
                            if "last_agent" in update:
                                last_agent = update["last_agent"]
                                routing_decisions.append(last_agent)
                                if self.verbose:
                                    print(f" -> {last_agent}", end="")

                        elif event_type == "credit_update":
                            usage = event.get("usage", {})
                            test.credit_used = usage.get("session_total", 0)
                            if self.verbose:
                                print(f" [${test.credit_used:.4f}]", end="")

                        elif event_type == "error":
                            test.error = event.get("error") or event.get("message")
                            print(f"\n❌ ERROR: {test.error}")
                            break

                        elif event_type == "workflow_complete":
                            workflow_complete = True
                            print(f"\n✅ Workflow completed!")
                            break

                        if self.verbose:
                            print()  # Newline after event info

                except asyncio.TimeoutError:
                    print(f"\n⏱️ Timeout after {test.timeout}s")
                    test.error = f"Timeout after {test.timeout}s"

                print("-"*50)

        except Exception as e:
            test.error = str(e)
            print(f"❌ Connection error: {e}")

        test.duration = (datetime.now() - start_time).total_seconds()

        # Check generated files
        print("\n📂 Checking generated files:")
        for expected_file in test.expected_files:
            file_path = test.workspace_path / expected_file
            if file_path.exists():
                test.generated_files.append(expected_file)
                print(f"  ✅ {expected_file}")
            else:
                print(f"  ❌ {expected_file} (missing)")

        # Determine success
        test.passed = (
            workflow_complete and
            not test.error and
            len(test.generated_files) >= len(test.expected_files) * 0.8  # 80% threshold
        )

        # Summary
        print("\n" + "="*100)
        print(f"📊 TEST RESULT: {test.name}")
        print("-"*100)
        print(f"  Status: {'✅ PASSED' if test.passed else '❌ FAILED'}")
        print(f"  Duration: {test.duration:.1f}s")
        print(f"  Events: {len(test.events)}")
        print(f"  Routing: {' → '.join(routing_decisions[:5])}")
        print(f"  Credits: ${test.credit_used:.4f}")
        print(f"  Files: {len(test.generated_files)}/{len(test.expected_files)}")
        if test.error:
            print(f"  Error: {test.error}")
        print("="*100)

        return test.passed

    async def run_all_tests(self):
        """Run all tests sequentially."""
        print("\n" + "🚀 "*20)
        print("SEQUENTIAL E2E TEST RUNNER")
        print("🚀 "*20)
        print(f"Tests to run: {len(self.test_cases)}")
        print(f"Server: {SERVER_URL}")
        print(f"Base directory: {TEST_BASE}")

        passed = 0
        failed = 0
        skipped = 0

        for i, test in enumerate(self.test_cases, 1):
            print(f"\n\n{'#'*100}")
            print(f"# TEST {i}/{len(self.test_cases)}")
            print(f"{'#'*100}")

            success = await self.run_single_test(test)

            if success:
                passed += 1
                print(f"\n✅ Test {i} passed - continuing to next test")
            else:
                failed += 1
                print(f"\n❌ Test {i} failed - stopping test suite")
                # Skip remaining tests
                skipped = len(self.test_cases) - i
                break

            # Wait between tests
            if i < len(self.test_cases):
                print("\n⏳ Waiting 5 seconds before next test...")
                await asyncio.sleep(5)

        # Final report
        print("\n\n" + "="*100)
        print("📊 FINAL TEST REPORT")
        print("="*100)
        print(f"  ✅ Passed: {passed}")
        print(f"  ❌ Failed: {failed}")
        print(f"  ⏭️  Skipped: {skipped}")
        print(f"  📈 Total: {len(self.test_cases)}")
        print(f"  💰 Total Credits: ${sum(t.credit_used for t in self.test_cases):.4f}")
        print("="*100)

        # Detailed results
        print("\nDETAILED RESULTS:")
        print("-"*100)
        for i, test in enumerate(self.test_cases, 1):
            status = "✅" if test.passed else ("❌" if test.error else "⏭️")
            print(f"{status} Test {i}: {test.name}")
            if test.error:
                print(f"   Error: {test.error[:100]}")
            if test.duration > 0:
                print(f"   Duration: {test.duration:.1f}s, Credits: ${test.credit_used:.4f}")

        return passed == len(self.test_cases)


async def main():
    """Main test execution."""
    runner = SequentialE2ERunner(verbose=True)

    # Define test cases - ONE AT A TIME!

    # Test 1: Simple temperature converter
    runner.add_test(E2ETestCase(
        name="Temperature Converter",
        workspace_name="e2e_test_1_temp_converter",
        task="Create a Python CLI tool that converts temperatures between Celsius, Fahrenheit, and Kelvin.",
        expected_files=["temp_converter.py", "README.md"],
        timeout=120
    ))

    # Test 2: Todo List App
    runner.add_test(E2ETestCase(
        name="Todo List CLI",
        workspace_name="e2e_test_2_todo_app",
        task="Create a Python CLI todo list application with add, remove, list, and mark complete functions.",
        expected_files=["todo.py", "README.md"],
        timeout=120
    ))

    # Test 3: Calculator
    runner.add_test(E2ETestCase(
        name="Calculator",
        workspace_name="e2e_test_3_calculator",
        task="Create a Python calculator with basic operations (add, subtract, multiply, divide).",
        expected_files=["calculator.py", "README.md"],
        timeout=120
    ))

    # Test 4: File Organizer
    runner.add_test(E2ETestCase(
        name="File Organizer",
        workspace_name="e2e_test_4_file_organizer",
        task="Create a Python script that organizes files in a directory by their extensions.",
        expected_files=["organizer.py", "README.md"],
        timeout=120
    ))

    # Test 5: Password Generator
    runner.add_test(E2ETestCase(
        name="Password Generator",
        workspace_name="e2e_test_5_password_gen",
        task="Create a Python password generator with customizable length and character types.",
        expected_files=["password_gen.py", "README.md"],
        timeout=120
    ))

    # Run all tests sequentially
    success = await runner.run_all_tests()

    # Exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())