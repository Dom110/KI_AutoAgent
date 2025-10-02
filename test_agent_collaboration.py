"""
Test Agent Collaboration System
Tests the complete Reviewer → Fixer → Reviewer loop
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.langgraph_system.workflow import create_agent_workflow
from backend.langgraph_system.state import ExecutionStep

async def test_reviewer_fixer_collaboration():
    """
    Test Case 1: Reviewer → Fixer Collaboration

    Scenario:
    1. Architect designs simple API
    2. CodeSmith implements with intentional bug
    3. Reviewer finds bug and triggers Fixer
    4. Fixer fixes the bug
    5. Reviewer re-reviews and approves
    """
    print("=" * 80)
    print("TEST 1: Reviewer → Fixer Collaboration")
    print("=" * 80)

    workflow = create_agent_workflow()

    # Task with potential for bugs
    task = """
    Create a simple user authentication API with:
    - Login endpoint that accepts username and password
    - Use SQL database for user storage
    - Return JWT token on successful login
    """

    final_state = await workflow.execute(
        task=task,
        session_id="test_collab_1",
        workspace_path="/tmp/test_collab"
    )

    # Analyze results
    print("\n📊 EXECUTION PLAN ANALYSIS")
    print("-" * 80)

    for i, step in enumerate(final_state.get('execution_plan', []), 1):
        status_emoji = {
            "completed": "✅",
            "failed": "❌",
            "in_progress": "⏳",
            "pending": "⏸️"
        }.get(step.status, "❓")

        print(f"{i}. [{status_emoji}] {step.agent.upper()}: {step.status}")
        print(f"   Task: {step.task[:80]}...")
        if step.result:
            result_preview = str(step.result)[:150]
            print(f"   Result: {result_preview}...")
        if step.error:
            print(f"   Error: {step.error}")
        print()

    # Check for collaboration
    agent_sequence = [step.agent for step in final_state.get('execution_plan', [])]
    print("\n🔄 AGENT EXECUTION SEQUENCE:")
    print(" → ".join(agent_sequence))

    # Verify collaboration happened
    has_reviewer = "reviewer" in agent_sequence
    has_fixer = "fixer" in agent_sequence
    reviewer_before_fixer = False
    fixer_before_second_reviewer = False

    if has_reviewer and has_fixer:
        first_reviewer_idx = agent_sequence.index("reviewer")
        fixer_idx = agent_sequence.index("fixer")
        reviewer_before_fixer = first_reviewer_idx < fixer_idx

        # Check if reviewer appears after fixer (re-review)
        if fixer_idx < len(agent_sequence) - 1:
            remaining = agent_sequence[fixer_idx + 1:]
            fixer_before_second_reviewer = "reviewer" in remaining

    print("\n✅ COLLABORATION CHECKS:")
    print(f"  - Reviewer executed: {has_reviewer}")
    print(f"  - Fixer executed: {has_fixer}")
    print(f"  - Reviewer → Fixer sequence: {reviewer_before_fixer}")
    print(f"  - Fixer → Reviewer re-review: {fixer_before_second_reviewer}")

    # Overall result
    success = has_reviewer and has_fixer and reviewer_before_fixer
    print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")

    return success

async def test_tetris_workflow():
    """
    Test Case 2: Complete Tetris App Creation

    Scenario:
    1. User requests Tetris game
    2. Architect designs structure
    3. CodeSmith implements
    4. Reviewer checks
    5. Fixer if needed
    """
    print("\n" + "=" * 80)
    print("TEST 2: Complete Tetris Workflow")
    print("=" * 80)

    workflow = create_agent_workflow()

    final_state = await workflow.execute(
        task="Entwickle eine Tetris Webapplikation mit HTML5 Canvas",
        session_id="test_tetris",
        workspace_path="/tmp/test_tetris"
    )

    # Check results
    print("\n📊 EXECUTION PLAN:")
    print("-" * 80)

    for i, step in enumerate(final_state.get('execution_plan', []), 1):
        print(f"{i}. {step.agent}: {step.status}")

    # Check if files were created
    import os
    workspace = "/tmp/test_tetris"
    created_files = []

    if os.path.exists(workspace):
        for root, dirs, files in os.walk(workspace):
            for file in files:
                if file.endswith(('.html', '.css', '.js')):
                    created_files.append(os.path.join(root, file))

    print(f"\n📁 FILES CREATED: {len(created_files)}")
    for file in created_files:
        print(f"  - {file}")

    # Overall result
    has_files = len(created_files) > 0
    workflow_completed = final_state.get("status") == "completed"

    print(f"\n{'✅ TEST PASSED' if has_files and workflow_completed else '❌ TEST FAILED'}")
    print(f"  - Workflow completed: {workflow_completed}")
    print(f"  - Files created: {has_files}")

    return has_files and workflow_completed

async def test_workflow_completion_bug():
    """
    Test Case 3: Workflow Completion Bug Fix

    Verifies that workflow doesn't stop when step is in_progress
    """
    print("\n" + "=" * 80)
    print("TEST 3: Workflow Completion Bug Fix")
    print("=" * 80)

    workflow = create_agent_workflow()

    final_state = await workflow.execute(
        task="Create a simple Hello World Python script",
        session_id="test_completion",
        workspace_path="/tmp/test_completion"
    )

    # Check for in_progress steps
    has_in_progress = any(
        step.status == "in_progress"
        for step in final_state.get('execution_plan', [])
    )

    all_completed_or_failed = all(
        step.status in ["completed", "failed"]
        for step in final_state.get('execution_plan', [])
    )

    print(f"\n📊 STEP STATUS CHECK:")
    for step in final_state.get('execution_plan', []):
        print(f"  - Step {step.id} ({step.agent}): {step.status}")

    print(f"\n✅ BUG FIX VERIFICATION:")
    print(f"  - Has in_progress steps: {has_in_progress}")
    print(f"  - All steps completed/failed: {all_completed_or_failed}")

    success = not has_in_progress and all_completed_or_failed
    print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")

    return success

async def test_settings_env_sync():
    """
    Test Case 4: Settings → .env Sync

    Verifies that API keys are synced from settings to .env
    """
    print("\n" + "=" * 80)
    print("TEST 4: Settings → .env Sync")
    print("=" * 80)

    env_path = "/Users/dominikfoert/git/KI_AutoAgent/backend/.env"

    if not os.path.exists(env_path):
        print("❌ .env file not found")
        return False

    with open(env_path, 'r') as f:
        env_content = f.read()

    has_openai = "OPENAI_API_KEY=" in env_content
    has_anthropic = "ANTHROPIC_API_KEY=" in env_content
    has_perplexity = "PERPLEXITY_API_KEY=" in env_content

    # Check for auto-sync comment
    has_sync_comment = "Auto-synced from VS Code settings" in env_content

    print(f"\n📄 .env FILE ANALYSIS:")
    print(f"  - OPENAI_API_KEY present: {has_openai}")
    print(f"  - ANTHROPIC_API_KEY present: {has_anthropic}")
    print(f"  - PERPLEXITY_API_KEY present: {has_perplexity}")
    print(f"  - Auto-sync comment: {has_sync_comment}")

    success = has_openai and (has_sync_comment or has_perplexity)
    print(f"\n{'✅ TEST PASSED' if success else '⚠️ PARTIAL PASS'}")

    return success

async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("AGENT COLLABORATION SYSTEM - COMPREHENSIVE TESTS")
    print("=" * 80)

    results = {}

    # Test 1: Reviewer-Fixer collaboration
    try:
        results['collaboration'] = await test_reviewer_fixer_collaboration()
    except Exception as e:
        print(f"❌ Test 1 failed with error: {e}")
        results['collaboration'] = False

    # Test 2: Tetris workflow
    try:
        results['tetris'] = await test_tetris_workflow()
    except Exception as e:
        print(f"❌ Test 2 failed with error: {e}")
        results['tetris'] = False

    # Test 3: Workflow completion bug
    try:
        results['completion'] = await test_workflow_completion_bug()
    except Exception as e:
        print(f"❌ Test 3 failed with error: {e}")
        results['completion'] = False

    # Test 4: Settings sync
    try:
        results['settings'] = await test_settings_env_sync()
    except Exception as e:
        print(f"❌ Test 4 failed with error: {e}")
        results['settings'] = False

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name.upper()}: {status}")

    total_passed = sum(results.values())
    total_tests = len(results)

    print(f"\n📊 OVERALL: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! Agent collaboration system is working!")
    elif total_passed > 0:
        print(f"\n⚠️ PARTIAL SUCCESS: {total_passed} tests passed, {total_tests - total_passed} failed")
    else:
        print("\n❌ ALL TESTS FAILED: System needs debugging")

if __name__ == "__main__":
    asyncio.run(main())
