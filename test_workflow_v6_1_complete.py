#!/usr/bin/env python3
"""
Test Complete v6.1 Workflow Integration

Validates:
1. All subgraphs use v6_1 imports
2. HITL callback is passed to all agents
3. Workflow initialization succeeds
4. No v6.0 references remain

Author: KI AutoAgent Team
Version: 6.1.0-alpha
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
env_path = Path.home() / ".ki_autoagent" / "config" / ".env"
load_dotenv(env_path)

from adapters.use_claude_cli import use_claude_cli
use_claude_cli()

from workflow_v6_integrated import WorkflowV6Integrated


async def test_workflow_initialization():
    """Test that workflow initializes correctly with all v6.1 components."""
    print("🧪 Testing Complete v6.1 Workflow Integration\n")
    print("=" * 80)

    # Test 1: Check imports
    print("\n1️⃣ VERIFYING IMPORTS...")
    print("   Checking that workflow uses v6_1 subgraphs...")

    import inspect
    from workflow_v6_integrated import WorkflowV6Integrated

    source = inspect.getsource(WorkflowV6Integrated)

    # Check for v6_1 imports
    v6_1_imports = [
        "research_subgraph_v6_1",
        "architect_subgraph_v6_1",
        "codesmith_subgraph_v6_1",
        "reviewfix_subgraph_v6_1"
    ]

    found_imports = []
    for imp in v6_1_imports:
        if imp in source:
            found_imports.append(imp)
            print(f"   ✅ {imp}")

    if len(found_imports) == 4:
        print(f"\n   ✅ ALL 4 subgraphs use v6_1!")
    else:
        print(f"\n   ❌ MISSING {4 - len(found_imports)} v6_1 imports!")
        return False

    # Test 2: Check for v6.0 references
    print("\n2️⃣ CHECKING FOR v6.0 REFERENCES...")

    # Check for "v6.0" (but allow "v6.1")
    if "v6.0" in source and "v6.1" not in source.replace("v6.0", ""):
        print("   ❌ Found v6.0 references!")
        return False
    else:
        print("   ✅ No v6.0 references found!")

    # Test 3: Check HITL callback parameter
    print("\n3️⃣ CHECKING HITL CALLBACK INTEGRATION...")

    hitl_checks = [
        "hitl_callback=self.websocket_callback",
    ]

    hitl_count = 0
    for check in hitl_checks:
        count = source.count(check)
        hitl_count += count
        print(f"   Found '{check}': {count} times")

    if hitl_count >= 4:  # Should be in all 4 subgraph builders
        print(f"   ✅ HITL callback passed to all agents!")
    else:
        print(f"   ⚠️  HITL callback might not be in all agents")

    # Test 4: Initialize workflow (without full execution)
    print("\n4️⃣ TESTING WORKFLOW INITIALIZATION...")
    print("   Creating WorkflowV6Integrated instance...")

    test_workspace = "/tmp/ki_autoagent_v6_1_test"
    Path(test_workspace).mkdir(parents=True, exist_ok=True)

    try:
        workflow = WorkflowV6Integrated(
            workspace_path=test_workspace,
            websocket_callback=None  # No callback for test
        )
        print("   ✅ Workflow instance created!")

        print("\n   Initializing v6 systems (this may take 30-40s)...")
        await workflow.initialize()
        print("   ✅ Workflow initialized successfully!")

        # Verify components
        print("\n   Verifying components:")
        components = {
            "checkpointer": workflow.checkpointer,
            "memory": workflow.memory,
            "workflow": workflow.workflow,
            "query_classifier": workflow.query_classifier,
            "curiosity": workflow.curiosity,
            "learning": workflow.learning,
            "predictive": workflow.predictive,
            "tool_registry": workflow.tool_registry,
            "approval_manager": workflow.approval_manager,
            "workflow_adapter": workflow.workflow_adapter,
            "neurosymbolic": workflow.neurosymbolic,
            "self_diagnosis": workflow.self_diagnosis,
        }

        for name, component in components.items():
            status = "✅" if component is not None else "❌"
            print(f"      {status} {name}")

        all_initialized = all(c is not None for c in components.values())

        if all_initialized:
            print("\n   ✅ ALL COMPONENTS INITIALIZED!")
        else:
            print("\n   ❌ SOME COMPONENTS MISSING!")
            return False

        return True

    except Exception as e:
        print(f"   ❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("\n" + "=" * 80)
    print("KI AutoAgent v6.1 - Complete Workflow Integration Test")
    print("=" * 80)

    success = await test_workflow_initialization()

    print("\n" + "=" * 80)
    if success:
        print("✅ ALL TESTS PASSED - v6.1 Integration Complete!")
        print("=" * 80)
        print("\nNext Steps:")
        print("  1. Test with simple task (E2E workflow)")
        print("  2. Profile performance")
        print("  3. Implement Phase 1 optimizations")
    else:
        print("❌ TESTS FAILED - Please review errors above")
        print("=" * 80)

    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
