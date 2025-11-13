#!/usr/bin/env python3
"""
Run a single E2E test for v7.0 Supervisor Pattern

Usage:
    python run_single_test.py CREATE_WITH_SUPERVISOR
    python run_single_test.py EXPLAIN_WITH_RESEARCH
    python run_single_test.py FIX_WITH_RESEARCH_LOOP
    python run_single_test.py COMPLEX_WITH_SELF_INVOCATION
"""

import asyncio
import sys
from pathlib import Path
from e2e_test_v7_0_supervisor import E2ETestV7, prepare_test_workspaces

# Test configurations
TESTS = {
    "CREATE_WITH_SUPERVISOR": {
        "query": "Create a simple REST API with FastAPI that manages a todo list. Include CRUD operations.",
        "workspace_path": str(Path.home() / "TestApps" / "e2e_v7_create"),
        "expected_features": {
            "supervisor_decisions": 4,
            "agents_used": ["research", "architect", "codesmith", "reviewfix", "responder"],
            "research_requests": False,
            "responder_output": True,
            "hitl_activation": False,
        }
    },
    "EXPLAIN_WITH_RESEARCH": {
        "query": "Explain how async/await works in Python and provide best practices.",
        "workspace_path": str(Path.home() / "TestApps" / "e2e_v7_explain"),
        "expected_features": {
            "supervisor_decisions": 2,
            "agents_used": ["research", "responder"],
            "research_requests": False,
            "responder_output": True,
            "hitl_activation": False,
        }
    },
    "FIX_WITH_RESEARCH_LOOP": {
        "query": "Fix the ImportError in main.py. The FastAPI import is not working correctly.",
        "workspace_path": str(Path.home() / "TestApps" / "e2e_v7_fix"),
        "expected_features": {
            "supervisor_decisions": 5,
            "agents_used": ["research", "codesmith", "reviewfix"],
            "research_requests": True,
            "responder_output": True,
            "hitl_activation": False,
        }
    },
    "COMPLEX_WITH_SELF_INVOCATION": {
        "query": "Refactor the existing codebase to use proper design patterns, add comprehensive error handling, and improve performance.",
        "workspace_path": str(Path.home() / "TestApps" / "e2e_v7_complex"),
        "expected_features": {
            "supervisor_decisions": 6,
            "agents_used": ["research", "architect", "codesmith", "reviewfix", "responder"],
            "research_requests": True,
            "responder_output": True,
            "hitl_activation": False,
        }
    }
}


async def main():
    """Run a single E2E test"""
    if len(sys.argv) < 2:
        print("Usage: python run_single_test.py <TEST_NAME>")
        print(f"Available tests: {', '.join(TESTS.keys())}")
        sys.exit(1)

    test_name = sys.argv[1]
    if test_name not in TESTS:
        print(f"❌ Unknown test: {test_name}")
        print(f"Available tests: {', '.join(TESTS.keys())}")
        sys.exit(1)

    # Prepare test workspaces
    print("✅ Test workspaces prepared\n")
    await prepare_test_workspaces()

    # Run the single test
    test_config = TESTS[test_name]
    tester = E2ETestV7()

    await tester.run_test(
        test_name=test_name,
        query=test_config["query"],
        workspace_path=test_config["workspace_path"],
        expected_features=test_config["expected_features"],
        timeout=120  # 2 minutes max per test
    )

    # Print result
    if tester.results:
        result = tester.results[0]
        print(f"\n{'=' * 100}")
        print(f"📊 TEST RESULT: {test_name}")
        print(f"{'=' * 100}")
        print(f"Duration: {result['duration']:.1f}s")
        print(f"Status: {'✅ PASS' if result['passed'] else '❌ FAIL'}")
        print(f"Supervisor Decisions: {result['supervisor_decisions']}")
        print(f"Agents Invoked: {', '.join(result['agents_invoked'])}")
        print(f"Errors: {result['errors']}")
        if result['error_message']:
            print(f"Error Message: {result['error_message']}")
        print(f"{'=' * 100}\n")

        # Exit with proper code
        sys.exit(0 if result['passed'] else 1)
    else:
        print("❌ No test results!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
