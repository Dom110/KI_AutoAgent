"""
Code Verification Tests
Verifies that all code changes are in place without running workflows
"""
import os
import re

def test_routing_replan_check():
    """Verify route_to_next_agent checks needs_replan flag"""
    print("TEST 1: Routing replan check")
    print("-" * 60)

    with open('/Users/dominikfoert/git/KI_AutoAgent/backend/langgraph_system/workflow.py', 'r') as f:
        content = f.read()

    # Check for needs_replan check
    has_replan_check = 'if state.get("needs_replan")' in content
    has_orchestrator_return = 'return "orchestrator"' in content

    print(f"  ✓ Has needs_replan check: {has_replan_check}")
    print(f"  ✓ Routes to orchestrator: {has_orchestrator_return}")

    success = has_replan_check and has_orchestrator_return
    print(f"  {'✅ PASSED' if success else '❌ FAILED'}\n")
    return success

def test_routing_in_progress_check():
    """Verify route_to_next_agent checks for in_progress steps"""
    print("TEST 2: Routing in_progress bug fix")
    print("-" * 60)

    with open('/Users/dominikfoert/git/KI_AutoAgent/backend/langgraph_system/workflow.py', 'r') as f:
        content = f.read()

    # Check for in_progress detection
    has_in_progress_check = 'any(s.status == "in_progress"' in content
    has_warning = 'Found in_progress steps' in content

    print(f"  ✓ Checks for in_progress steps: {has_in_progress_check}")
    print(f"  ✓ Has warning log: {has_warning}")

    success = has_in_progress_check and has_warning
    print(f"  {'✅ PASSED' if success else '❌ FAILED'}\n")
    return success

def test_orchestrator_replan_logic():
    """Verify orchestrator_node handles re-planning"""
    print("TEST 3: Orchestrator re-planning logic")
    print("-" * 60)

    with open('/Users/dominikfoert/git/KI_AutoAgent/backend/langgraph_system/workflow.py', 'r') as f:
        content = f.read()

    # Check for re-planning mode
    has_replan_mode = 'RE-PLANNING MODE' in content
    has_suggested_agent = 'suggested_agent = state.get("suggested_agent"' in content
    has_new_step_creation = 'new_step = ExecutionStep(' in content
    has_flag_clear = 'state["needs_replan"] = False' in content

    print(f"  ✓ Has RE-PLANNING MODE: {has_replan_mode}")
    print(f"  ✓ Reads suggested_agent: {has_suggested_agent}")
    print(f"  ✓ Creates new ExecutionStep: {has_new_step_creation}")
    print(f"  ✓ Clears replan flags: {has_flag_clear}")

    success = all([has_replan_mode, has_suggested_agent, has_new_step_creation, has_flag_clear])
    print(f"  {'✅ PASSED' if success else '❌ FAILED'}\n")
    return success

def test_reviewer_collaboration():
    """Verify reviewer_node sets collaboration flags"""
    print("TEST 4: Reviewer collaboration detection")
    print("-" * 60)

    with open('/Users/dominikfoert/git/KI_AutoAgent/backend/langgraph_system/workflow.py', 'r') as f:
        content = f.read()

    # Check for issue detection
    has_critical_check = 'has_critical_issues = any(keyword in review_text' in content
    has_keywords = '"critical", "bug", "error"' in content
    has_replan_set = 'state["suggested_agent"] = "fixer"' in content

    print(f"  ✓ Analyzes for critical issues: {has_critical_check}")
    print(f"  ✓ Checks critical keywords: {has_keywords}")
    print(f"  ✓ Sets suggested_agent=fixer: {has_replan_set}")

    success = all([has_critical_check, has_keywords, has_replan_set])
    print(f"  {'✅ PASSED' if success else '❌ FAILED'}\n")
    return success

def test_conditional_edges():
    """Verify conditional edges include orchestrator loop-back"""
    print("TEST 5: Conditional edges orchestrator loop-back")
    print("-" * 60)

    with open('/Users/dominikfoert/git/KI_AutoAgent/backend/langgraph_system/workflow.py', 'r') as f:
        content = f.read()

    # Find add_conditional_edges for approval node
    # Should have "orchestrator": "orchestrator" mapping
    has_orchestrator_edge = '"orchestrator": "orchestrator"' in content

    print(f"  ✓ Has orchestrator loop-back edge: {has_orchestrator_edge}")

    success = has_orchestrator_edge
    print(f"  {'✅ PASSED' if success else '❌ FAILED'}\n")
    return success

def test_settings_sync_code():
    """Verify settings → .env sync code in TypeScript"""
    print("TEST 6: Settings → .env sync implementation")
    print("-" * 60)

    ext_file = '/Users/dominikfoert/git/KI_AutoAgent/vscode-extension/src/extension.ts'

    if not os.path.exists(ext_file):
        print("  ❌ extension.ts not found")
        return False

    with open(ext_file, 'r') as f:
        content = f.read()

    has_sync_function = 'async function syncSettingsToEnv' in content
    has_watch_function = 'function watchSettingsChanges' in content
    has_sync_call = 'await syncSettingsToEnv' in content

    print(f"  ✓ Has syncSettingsToEnv function: {has_sync_function}")
    print(f"  ✓ Has watchSettingsChanges function: {has_watch_function}")
    print(f"  ✓ Calls sync on activation: {has_sync_call}")

    success = all([has_sync_function, has_watch_function, has_sync_call])
    print(f"  {'✅ PASSED' if success else '❌ FAILED'}\n")
    return success

def test_instruction_files():
    """Verify collaboration instruction files exist"""
    print("TEST 7: Collaboration instruction files")
    print("-" * 60)

    files = [
        '.kiautoagent/instructions/reviewer-collaboration-instructions.md',
        '.kiautoagent/instructions/fixer-collaboration-instructions.md',
        '.kiautoagent/instructions/orchestrator-replanning-instructions.md'
    ]

    base_path = '/Users/dominikfoert/git/KI_AutoAgent'
    results = []

    for file in files:
        full_path = os.path.join(base_path, file)
        exists = os.path.exists(full_path)
        results.append(exists)
        print(f"  ✓ {file}: {'✅' if exists else '❌'}")

    success = all(results)
    print(f"  {'✅ PASSED' if success else '❌ FAILED'}\n")
    return success

def main():
    print("=" * 80)
    print("CODE VERIFICATION TESTS")
    print("=" * 80)
    print()

    tests = [
        test_routing_replan_check,
        test_routing_in_progress_check,
        test_orchestrator_replan_logic,
        test_reviewer_collaboration,
        test_conditional_edges,
        test_settings_sync_code,
        test_instruction_files
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"  ❌ Test failed with error: {e}\n")
            results.append(False)

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    passed = sum(results)
    total = len(results)

    print(f"\n📊 {passed}/{total} tests passed")

    if passed == total:
        print("✅ ALL CODE CHANGES VERIFIED!")
    elif passed > total * 0.7:
        print("⚠️ MOST CODE CHANGES VERIFIED")
    else:
        print("❌ SOME CODE CHANGES MISSING")

    # List specific results
    test_names = [
        "Routing replan check",
        "Routing in_progress fix",
        "Orchestrator re-planning",
        "Reviewer collaboration",
        "Conditional edges",
        "Settings sync",
        "Instruction files"
    ]

    print("\nDetailed Results:")
    for name, passed in zip(test_names, results):
        print(f"  {'✅' if passed else '❌'} {name}")

if __name__ == "__main__":
    main()
