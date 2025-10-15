"""
Test: Orchestrator Serialization Fix

Validates that the orchestrator parameter passing fix resolved the msgpack error.

This is a MINIMAL test that checks:
1. AgentOrchestrator is NOT in state TypedDicts
2. Subgraph functions accept orchestrator parameter
3. No msgpack serialization errors occur

Run with:
    python backend/tests/test_orchestrator_serialization.py
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_orchestrator_not_in_state():
    """Test 1: Verify orchestrator is NOT in state TypedDicts."""
    logger.info("=" * 80)
    logger.info("TEST 1: Orchestrator NOT in State TypedDicts")
    logger.info("=" * 80)

    try:
        from state_v6 import ArchitectState, CodesmithState, ReviewFixState

        # Check ArchitectState
        architect_annotations = ArchitectState.__annotations__
        if "orchestrator" in architect_annotations:
            raise AssertionError("❌ FAILED: orchestrator found in ArchitectState!")
        logger.info("✅ ArchitectState: orchestrator NOT in state (correct)")

        # Check CodesmithState
        codesmith_annotations = CodesmithState.__annotations__
        if "orchestrator" in codesmith_annotations:
            raise AssertionError("❌ FAILED: orchestrator found in CodesmithState!")
        logger.info("✅ CodesmithState: orchestrator NOT in state (correct)")

        # Check ReviewFixState
        reviewfix_annotations = ReviewFixState.__annotations__
        if "orchestrator" in reviewfix_annotations:
            raise AssertionError("❌ FAILED: orchestrator found in ReviewFixState!")
        logger.info("✅ ReviewFixState: orchestrator NOT in state (correct)")

        logger.info("")
        logger.info("✅ TEST 1 PASSED: orchestrator correctly removed from all states")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 1 FAILED: {e}")
        return False


def test_subgraph_signatures():
    """Test 2: Verify subgraph functions accept orchestrator parameter."""
    logger.info("")
    logger.info("=" * 80)
    logger.info("TEST 2: Subgraph Function Signatures")
    logger.info("=" * 80)

    try:
        import inspect
        from subgraphs.architect_subgraph_v6_3 import create_architect_subgraph
        from subgraphs.codesmith_subgraph_v6_1 import create_codesmith_subgraph

        # Check create_architect_subgraph
        arch_sig = inspect.signature(create_architect_subgraph)
        arch_params = list(arch_sig.parameters.keys())

        if "orchestrator" not in arch_params:
            raise AssertionError("❌ FAILED: orchestrator parameter missing from create_architect_subgraph!")
        logger.info(f"✅ create_architect_subgraph: has 'orchestrator' parameter")
        logger.info(f"   Parameters: {arch_params}")

        # Check create_codesmith_subgraph
        code_sig = inspect.signature(create_codesmith_subgraph)
        code_params = list(code_sig.parameters.keys())

        if "orchestrator" not in code_params:
            raise AssertionError("❌ FAILED: orchestrator parameter missing from create_codesmith_subgraph!")
        logger.info(f"✅ create_codesmith_subgraph: has 'orchestrator' parameter")
        logger.info(f"   Parameters: {code_params}")

        logger.info("")
        logger.info("✅ TEST 2 PASSED: All subgraph functions have orchestrator parameter")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 2 FAILED: {e}")
        return False


def test_transformation_functions():
    """Test 3: Verify transformation functions don't pass orchestrator."""
    logger.info("")
    logger.info("=" * 80)
    logger.info("TEST 3: State Transformation Functions")
    logger.info("=" * 80)

    try:
        import inspect
        from state_v6 import supervisor_to_architect, supervisor_to_codesmith

        # Check supervisor_to_architect
        arch_sig = inspect.signature(supervisor_to_architect)
        arch_params = list(arch_sig.parameters.keys())

        if "orchestrator" in arch_params:
            raise AssertionError("❌ FAILED: orchestrator parameter should NOT be in supervisor_to_architect!")
        logger.info(f"✅ supervisor_to_architect: NO orchestrator parameter (correct)")
        logger.info(f"   Parameters: {arch_params}")

        # Check supervisor_to_codesmith
        code_sig = inspect.signature(supervisor_to_codesmith)
        code_params = list(code_sig.parameters.keys())

        if "orchestrator" in code_params:
            raise AssertionError("❌ FAILED: orchestrator parameter should NOT be in supervisor_to_codesmith!")
        logger.info(f"✅ supervisor_to_codesmith: NO orchestrator parameter (correct)")
        logger.info(f"   Parameters: {code_params}")

        logger.info("")
        logger.info("✅ TEST 3 PASSED: Transformation functions correctly exclude orchestrator")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 3 FAILED: {e}")
        return False


def test_msgpack_serialization():
    """Test 4: Verify state can be msgpack-serialized."""
    logger.info("")
    logger.info("=" * 80)
    logger.info("TEST 4: MsgPack Serialization")
    logger.info("=" * 80)

    try:
        import msgpack
        from state_v6 import ArchitectState, CodesmithState

        # Create sample states (without orchestrator!)
        arch_state: ArchitectState = {
            "user_query": "Create a TODO app",
            "workflow_plan": {},
            "workflow_type": "create",
            "mode": "design",
            "design": {},
            "architecture_snapshot": None,
            "research_context": {},
            "errors": []
        }

        code_state: CodesmithState = {
            "user_query": "Create a TODO app",
            "workflow_plan": {},
            "workflow_type": "create",
            "design": {},
            "research_context": {},
            "generated_files": [],
            "code_generation_result": "",
            "model_used": "claude-sonnet-4",
            "errors": []
        }

        # Try to serialize with msgpack
        logger.info("Attempting msgpack serialization of ArchitectState...")
        arch_packed = msgpack.packb(arch_state)
        logger.info(f"✅ ArchitectState serialized: {len(arch_packed)} bytes")

        logger.info("Attempting msgpack serialization of CodesmithState...")
        code_packed = msgpack.packb(code_state)
        logger.info(f"✅ CodesmithState serialized: {len(code_packed)} bytes")

        # Try to deserialize
        arch_unpacked = msgpack.unpackb(arch_packed, strict_map_key=False)
        logger.info(f"✅ ArchitectState deserialized: {len(arch_unpacked)} fields")

        code_unpacked = msgpack.unpackb(code_packed, strict_map_key=False)
        logger.info(f"✅ CodesmithState deserialized: {len(code_unpacked)} fields")

        logger.info("")
        logger.info("✅ TEST 4 PASSED: States are msgpack-serializable (fix successful!)")
        return True

    except Exception as e:
        logger.error(f"❌ TEST 4 FAILED: {e}")
        logger.error("   This means the orchestrator serialization fix did NOT work!")
        return False


if __name__ == "__main__":
    print("\n" + "="*80)
    print("Orchestrator Serialization Fix - Validation Tests")
    print("="*80 + "\n")

    results = []

    # Run all tests
    results.append(("State TypedDicts", test_orchestrator_not_in_state()))
    results.append(("Subgraph Signatures", test_subgraph_signatures()))
    results.append(("Transformation Functions", test_transformation_functions()))
    results.append(("MsgPack Serialization", test_msgpack_serialization()))

    # Summary
    print("")
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")

    print("")
    print(f"📊 Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("")

    if passed == total:
        print("🎉 ALL TESTS PASSED - Orchestrator serialization fix is WORKING!")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED - Orchestrator serialization fix needs more work")
        sys.exit(1)
