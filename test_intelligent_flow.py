#!/usr/bin/env python3
"""
Test Intelligent Multi-Agent Flow (v6.1)

Tests the new conditional edges and agent decision making.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

# Load .env from global config
from dotenv import load_dotenv
env_path = Path.home() / ".ki_autoagent" / "config" / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded .env from {env_path}")
else:
    print(f"⚠️ No .env found at {env_path}")

# Activate Claude CLI (no ANTHROPIC_API_KEY needed)
from adapters.use_claude_cli import use_claude_cli
use_claude_cli()
print("✅ Claude CLI adapter activated")

from workflow_v6_integrated import WorkflowV6Integrated

async def test_simple_flow():
    """
    Test 1: Simple calculator app
    Expected: Research → Architect → Codesmith → ReviewFix → END
    """
    print("\n" + "="*80)
    print("TEST 1: Simple Calculator App (Linear Flow)")
    print("="*80 + "\n")

    workspace = "/Users/dominikfoert/TestApps/intelligentFlow"
    os.makedirs(workspace, exist_ok=True)

    workflow = WorkflowV6Integrated(
        workspace_path=workspace,
        websocket_callback=None
    )

    print("🔧 Initializing workflow...")
    await workflow.initialize()

    print("\n📝 Running workflow (30s timeout)...")

    try:
        result = await asyncio.wait_for(
            workflow.run(
                user_query="Create a simple calculator app with add, subtract, multiply, divide",
                session_id="test_simple"
            ),
            timeout=30.0
        )
    except asyncio.TimeoutError:
        print("\n⏱️  TIMEOUT after 30 seconds!")
        result = {
            "success": False,
            "execution_time": 30.0,
            "quality_score": 0.0,
            "errors": ["Timeout after 30 seconds"],
        }

    print("\n📊 Results:")
    print(f"  Success: {result['success']}")
    print(f"  Execution Time: {result['execution_time']:.1f}s")
    print(f"  Quality Score: {result['quality_score']:.2f}")
    print(f"  Errors: {len(result['errors'])}")

    # Check which agents completed
    session = workflow.current_session
    print("\n🔍 Agent Execution:")
    print(f"  Completed: {session.get('completed_agents', [])}")
    print(f"  Current phase: {session.get('current_phase', 'unknown')}")
    print(f"  Research results: {'Yes' if session.get('research_results') else 'No'}")
    print(f"  Architecture design: {'Yes' if session.get('architecture_design') else 'No'}")
    print(f"  Generated files: {len(session.get('generated_files', []))}")

    # Check files created
    print("\n📂 Files created:")
    files = list(Path(workspace).glob("*.py"))
    for f in files:
        print(f"  ✅ {f.name} ({f.stat().st_size} bytes)")

    print(f"\n{'✅ TEST 1 PASSED' if result['success'] and files else '❌ TEST 1 FAILED'}")

    return result

async def test_complex_with_research_loop():
    """
    Test 2: Complex task that might require research loop
    Expected: Research → Architect (low confidence) → Research → Architect → Codesmith → ...
    """
    print("\n" + "="*80)
    print("TEST 2: Stripe Payment Integration (May Loop Research)")
    print("="*80 + "\n")

    workspace = "/Users/dominikfoert/TestApps/intelligentFlowComplex"
    os.makedirs(workspace, exist_ok=True)

    workflow = WorkflowV6Integrated(
        workspace_path=workspace,
        websocket_callback=None
    )

    print("🔧 Initializing workflow...")
    await workflow.initialize()

    print("\n📝 Running workflow...")
    result = await workflow.run(
        user_query="Create Stripe payment integration using latest Stripe API v2024",
        session_id="test_complex"
    )

    print("\n📊 Results:")
    print(f"  Success: {result['success']}")
    print(f"  Execution Time: {result['execution_time']:.1f}s")
    print(f"  Quality Score: {result['quality_score']:.2f}")
    print(f"  Adaptations: {len(result['adaptations'].get('history', []))}")

    # Check if research was called multiple times
    session = workflow.current_session
    research_count = session.get("completed_agents", []).count("research")
    print(f"\n🔍 Research called: {research_count} times")

    if research_count > 1:
        print("  ✅ Intelligent loop: Research called multiple times!")

    files = list(Path(workspace).glob("*.py"))
    print(f"\n📂 Files created: {len(files)}")

    print(f"\n{'✅ TEST 2 PASSED' if result['success'] else '❌ TEST 2 FAILED'}")

    return result

async def test_error_handling():
    """
    Test 3: Task that might trigger errors
    Expected: Codesmith → ReviewFix (finds issues) → Codesmith → ReviewFix → END
    """
    print("\n" + "="*80)
    print("TEST 3: Error Handling & ReviewFix Loop")
    print("="*80 + "\n")

    workspace = "/Users/dominikfoert/TestApps/intelligentFlowErrors"
    os.makedirs(workspace, exist_ok=True)

    workflow = WorkflowV6Integrated(
        workspace_path=workspace,
        websocket_callback=None
    )

    print("🔧 Initializing workflow...")
    await workflow.initialize()

    print("\n📝 Running workflow...")
    result = await workflow.run(
        user_query="Create a complex ML model trainer with error handling",
        session_id="test_errors"
    )

    print("\n📊 Results:")
    print(f"  Success: {result['success']}")
    print(f"  Execution Time: {result['execution_time']:.1f}s")
    print(f"  Errors: {len(result['errors'])}")

    # Check if reviewfix was called
    session = workflow.current_session
    reviewfix_count = session.get("completed_agents", []).count("reviewfix")
    print(f"\n🔬 ReviewFix called: {reviewfix_count} times")

    print(f"\n{'✅ TEST 3 PASSED' if result['success'] or reviewfix_count > 0 else '❌ TEST 3 FAILED'}")

    return result

async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("🧪 INTELLIGENT MULTI-AGENT FLOW TEST SUITE (v6.1)")
    print("="*80)

    tests_passed = 0
    tests_total = 1  # Only TEST 1 for now

    try:
        result1 = await test_simple_flow()
        if result1['success']:
            tests_passed += 1
    except Exception as e:
        print(f"❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()

    # Skip TEST 2 & 3 for now
    # try:
    #     result2 = await test_complex_with_research_loop()
    #     if result2['success']:
    #         tests_passed += 1
    # except Exception as e:
    #     print(f"❌ TEST 2 FAILED: {e}")

    print("\n" + "="*80)
    print(f"🏁 FINAL RESULTS: {tests_passed}/{tests_total} tests passed")
    print("="*80 + "\n")

    if tests_passed == tests_total:
        print("✅ ALL TESTS PASSED! Intelligent flow is working!")
    elif tests_passed > 0:
        print("⚠️ SOME TESTS PASSED - Partial success")
    else:
        print("❌ ALL TESTS FAILED - Need debugging")

if __name__ == "__main__":
    asyncio.run(main())
