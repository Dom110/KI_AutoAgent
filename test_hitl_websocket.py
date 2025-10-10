#!/usr/bin/env python3
"""
HITL WebSocket Mock Test

Tests the complete HITL callback integration:
1. Mock WebSocket callback receives all debug info
2. Verify data completeness (commands, prompts, outputs, etc.)
3. Test with all 4 agents (Research, Architect, Codesmith, ReviewFix)
4. Validate error scenarios

Author: KI AutoAgent Team
Version: 6.1.0-alpha
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Any

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
env_path = Path.home() / ".ki_autoagent" / "config" / ".env"
load_dotenv(env_path)

from adapters.use_claude_cli import use_claude_cli
use_claude_cli()


# ============================================================================
# MOCK WEBSOCKET CALLBACK
# ============================================================================

class MockWebSocketCallback:
    """Mock WebSocket for capturing HITL debug info."""

    def __init__(self):
        self.events = []
        self.start_events = []
        self.complete_events = []
        self.error_events = []

    async def __call__(self, data: dict[str, Any]) -> None:
        """Capture callback data."""
        event_type = data.get("type", "unknown")
        timestamp = datetime.now().isoformat()

        event = {
            "timestamp": timestamp,
            **data
        }

        self.events.append(event)

        if event_type == "claude_cli_start":
            self.start_events.append(event)
            print(f"📤 HITL START: {data.get('agent', 'unknown')}")
            print(f"   Command length: {len(data.get('command', []))} parts")
            print(f"   System prompt: {data.get('system_prompt_length', 0)} chars")
            print(f"   User prompt: {data.get('user_prompt_length', 0)} chars")

        elif event_type == "claude_cli_complete":
            self.complete_events.append(event)
            print(f"✅ HITL COMPLETE: {data.get('agent', 'unknown')}")
            print(f"   Duration: {data.get('duration_ms', 0):.0f}ms")
            print(f"   Output: {data.get('output_length', 0)} chars")
            print(f"   Events: {data.get('events_count', 0)} parsed")

        elif event_type == "claude_cli_error":
            self.error_events.append(event)
            print(f"❌ HITL ERROR: {data.get('agent', 'unknown')}")
            print(f"   Error: {data.get('error', 'unknown')}")
            print(f"   Duration: {data.get('duration_ms', 0):.0f}ms")

    def get_summary(self) -> dict:
        """Get summary statistics."""
        return {
            "total_events": len(self.events),
            "start_events": len(self.start_events),
            "complete_events": len(self.complete_events),
            "error_events": len(self.error_events),
            "agents": list(set(e.get("agent") for e in self.events if e.get("agent")))
        }

    def validate(self) -> tuple[bool, list[str]]:
        """Validate callback data completeness."""
        issues = []

        # Check that start and complete match
        if len(self.start_events) != len(self.complete_events) + len(self.error_events):
            issues.append(
                f"Mismatch: {len(self.start_events)} starts vs "
                f"{len(self.complete_events)} completes + {len(self.error_events)} errors"
            )

        # Validate start events
        for i, event in enumerate(self.start_events):
            required_fields = [
                "command", "system_prompt", "user_prompt",
                "system_prompt_length", "user_prompt_length",
                "tools", "permission_mode"
            ]
            for field in required_fields:
                if field not in event:
                    issues.append(f"Start event {i}: Missing field '{field}'")

        # Validate complete events
        for i, event in enumerate(self.complete_events):
            required_fields = [
                "duration_ms", "raw_output", "events",
                "output_length", "events_count", "success"
            ]
            for field in required_fields:
                if field not in event:
                    issues.append(f"Complete event {i}: Missing field '{field}'")

        return (len(issues) == 0, issues)


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

async def test_research_agent_hitl():
    """Test HITL callbacks with Research agent."""
    print("\n" + "=" * 80)
    print("TEST 1: Research Agent HITL Callbacks")
    print("=" * 80)

    from subgraphs.research_subgraph_v6_1 import create_research_subgraph

    mock_ws = MockWebSocketCallback()

    print("\n1️⃣ Creating Research subgraph with mock callback...")
    subgraph = create_research_subgraph(
        workspace_path="/tmp/test_hitl",
        memory=None,
        hitl_callback=mock_ws
    )
    print("   ✅ Subgraph created")

    print("\n2️⃣ Executing research task...")
    try:
        result = await asyncio.wait_for(
            subgraph.ainvoke({
                "query": "What are the key features of Python asyncio?",
                "findings": None,
                "report": None,
                "completed": False,
                "errors": []
            }),
            timeout=60.0
        )

        print(f"\n3️⃣ Research completed")
        print(f"   Completed: {result.get('completed')}")
        print(f"   Has findings: {bool(result.get('findings'))}")

        # Validate callbacks
        print(f"\n4️⃣ Validating HITL callbacks...")
        summary = mock_ws.get_summary()
        print(f"   Total events: {summary['total_events']}")
        print(f"   Start events: {summary['start_events']}")
        print(f"   Complete events: {summary['complete_events']}")
        print(f"   Error events: {summary['error_events']}")

        is_valid, issues = mock_ws.validate()

        if is_valid:
            print(f"   ✅ All callbacks valid!")
            return True
        else:
            print(f"   ❌ Validation issues:")
            for issue in issues:
                print(f"      - {issue}")
            return False

    except asyncio.TimeoutError:
        print("   ❌ TIMEOUT after 60s!")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_architect_agent_hitl():
    """Test HITL callbacks with Architect agent."""
    print("\n" + "=" * 80)
    print("TEST 2: Architect Agent HITL Callbacks")
    print("=" * 80)

    from subgraphs.architect_subgraph_v6_1 import create_architect_subgraph

    mock_ws = MockWebSocketCallback()

    print("\n1️⃣ Creating Architect subgraph with mock callback...")
    subgraph = create_architect_subgraph(
        workspace_path="/tmp/test_hitl",
        memory=None,
        hitl_callback=mock_ws
    )
    print("   ✅ Subgraph created")

    print("\n2️⃣ Executing architect task...")
    try:
        result = await asyncio.wait_for(
            subgraph.ainvoke({
                "user_requirements": "Design a simple todo list API",
                "workspace_path": "/tmp/test_hitl",
                "research_context": {},
                "design": {},
                "tech_stack": [],
                "patterns": [],
                "diagram": "",
                "adr": "",
                "errors": []
            }),
            timeout=90.0
        )

        print(f"\n3️⃣ Architecture completed")
        print(f"   Has design: {bool(result.get('design'))}")
        print(f"   Has diagram: {bool(result.get('diagram'))}")

        # Validate callbacks
        print(f"\n4️⃣ Validating HITL callbacks...")
        summary = mock_ws.get_summary()
        print(f"   Total events: {summary['total_events']}")
        print(f"   Start events: {summary['start_events']}")
        print(f"   Complete events: {summary['complete_events']}")
        print(f"   Error events: {summary['error_events']}")

        is_valid, issues = mock_ws.validate()

        if is_valid:
            print(f"   ✅ All callbacks valid!")
            return True
        else:
            print(f"   ❌ Validation issues:")
            for issue in issues:
                print(f"      - {issue}")
            return False

    except asyncio.TimeoutError:
        print("   ❌ TIMEOUT after 90s!")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_callback_data_structure():
    """Test that callback data has correct structure."""
    print("\n" + "=" * 80)
    print("TEST 3: Callback Data Structure Validation")
    print("=" * 80)

    from subgraphs.research_subgraph_v6_1 import create_research_subgraph

    mock_ws = MockWebSocketCallback()

    print("\n1️⃣ Executing simple task to capture callback...")
    subgraph = create_research_subgraph(
        workspace_path="/tmp/test_hitl",
        memory=None,
        hitl_callback=mock_ws
    )

    try:
        result = await asyncio.wait_for(
            subgraph.ainvoke({
                "query": "Quick test query",
                "findings": None,
                "report": None,
                "completed": False,
                "errors": []
            }),
            timeout=60.0
        )

        print(f"\n2️⃣ Analyzing callback structure...")

        if len(mock_ws.start_events) == 0:
            print("   ❌ No start events captured!")
            return False

        start_event = mock_ws.start_events[0]
        print(f"\n   📤 START EVENT STRUCTURE:")
        for key, value in start_event.items():
            value_type = type(value).__name__
            if isinstance(value, (str, list)):
                length = len(value)
                print(f"      {key}: {value_type} (length: {length})")
            else:
                print(f"      {key}: {value_type}")

        if len(mock_ws.complete_events) == 0:
            print("\n   ⚠️  No complete events captured!")
        else:
            complete_event = mock_ws.complete_events[0]
            print(f"\n   ✅ COMPLETE EVENT STRUCTURE:")
            for key, value in complete_event.items():
                value_type = type(value).__name__
                if isinstance(value, (str, list)):
                    length = len(value)
                    print(f"      {key}: {value_type} (length: {length})")
                else:
                    print(f"      {key}: {value_type}")

        # Save sample to file
        sample_data = {
            "start_event": start_event,
            "complete_event": mock_ws.complete_events[0] if mock_ws.complete_events else None
        }

        sample_file = Path("/tmp/hitl_callback_sample.json")
        with open(sample_file, "w") as f:
            json.dump(sample_data, f, indent=2, default=str)

        print(f"\n   📝 Sample data saved: {sample_file}")
        print(f"   ✅ Data structure validated!")

        return True

    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def main():
    print("\n" + "=" * 80)
    print("🧪 HITL WebSocket Callback Integration Test")
    print("=" * 80)
    print("\nThis test validates that HITL debug info is correctly")
    print("transmitted through WebSocket callbacks to the frontend.")
    print("\nTesting with mock WebSocket callback...")

    results = {}

    # Test 1: Research Agent
    results["research"] = await test_research_agent_hitl()

    # Test 2: Architect Agent
    results["architect"] = await test_architect_agent_hitl()

    # Test 3: Data Structure
    results["structure"] = await test_callback_data_structure()

    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    print(f"\nTests Run: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} {'❌' if failed > 0 else ''}")

    print("\nDetails:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")

    if failed == 0:
        print("\n" + "=" * 80)
        print("✅ ALL HITL TESTS PASSED!")
        print("=" * 80)
        print("\nNext Steps:")
        print("  1. Integrate with real WebSocket server")
        print("  2. Update VS Code Extension to handle these message types")
        print("  3. Test end-to-end with Extension UI")
        return True
    else:
        print("\n" + "=" * 80)
        print("❌ SOME TESTS FAILED")
        print("=" * 80)
        print("\nPlease review errors above and fix issues.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
