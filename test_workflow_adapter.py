"""
E2E Tests for Workflow Adapter v6

Tests:
1. Insert agent (missing dependency)
2. Skip agent (optimization)
3. Repeat agent (persistent errors)
4. Abort workflow (critical error)
5. Quality-driven adaptation (low quality code)
6. Multiple adaptations
7. Adaptation statistics

Author: KI AutoAgent Team
Version: 6.0.0
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from workflow.workflow_adapter_v6 import (
    AdaptationReason,
    AdaptationType,
    WorkflowAdapterV6,
    WorkflowContext,
)


async def test_1_insert_agent_missing_dependency():
    """Test 1: Insert Research agent when dependencies are missing"""
    print("\n" + "=" * 80)
    print("TEST 1: Insert agent (missing dependency)")
    print("=" * 80)

    adapter = WorkflowAdapterV6()

    context = WorkflowContext(
        task_description="Build web app with React",
        current_phase="architect",
        completed_agents=["architect"],
        pending_agents=["codesmith", "reviewer"],
        results={
            "architect": {
                "dependencies": [
                    {"name": "react", "status": "missing"},
                    {"name": "webpack", "status": "missing"}
                ]
            }
        },
        errors=[],
        quality_scores={},
        metadata={}
    )

    decisions = await adapter.analyze_and_adapt(context)

    print(f"✅ Decisions: {len(decisions)}")
    for decision in decisions:
        print(f"   - {decision.adaptation_type.value}: {decision.agent_id}")

    assert len(decisions) > 0, "Should have adaptation decisions"
    assert decisions[0].adaptation_type == AdaptationType.INSERT_AGENT
    assert decisions[0].agent_id == "research"
    assert decisions[0].reason == AdaptationReason.MISSING_DEPENDENCY

    # Apply adaptation
    updated_context = await adapter.apply_adaptation(decisions[0], context)

    print(f"✅ Updated pending agents: {updated_context.pending_agents}")

    assert "research" in updated_context.pending_agents, "Research should be inserted"

    print("✅ Test 1 PASSED: Missing dependency adaptation works")
    return True


async def test_2_skip_agent_optimization():
    """Test 2: Skip agent based on optimization suggestion"""
    print("\n" + "=" * 80)
    print("TEST 2: Skip agent (optimization)")
    print("=" * 80)

    # Mock learning system that suggests skipping reviewer
    class MockLearningSystem:
        async def suggest_optimizations(self, task_description: str, project_type: str | None):
            return {
                "suggestions": [
                    {
                        "type": "skip_agent",
                        "agent": "reviewer",
                        "reason": "Simple task, high historical success rate without review",
                        "confidence": 0.85
                    }
                ]
            }

    adapter = WorkflowAdapterV6(learning_system=MockLearningSystem())

    context = WorkflowContext(
        task_description="Add simple getter method",
        current_phase="codesmith",
        completed_agents=["architect", "codesmith"],
        pending_agents=["reviewer", "fixer"],
        results={},
        errors=[],
        quality_scores={"codesmith": 0.9},
        metadata={"project_type": "python"}
    )

    decisions = await adapter.analyze_and_adapt(context)

    print(f"✅ Decisions: {len(decisions)}")

    assert len(decisions) > 0, "Should have optimization decisions"
    assert decisions[0].adaptation_type == AdaptationType.SKIP_AGENT
    assert decisions[0].agent_id == "reviewer"
    assert decisions[0].reason == AdaptationReason.OPTIMIZATION

    # Apply adaptation
    updated_context = await adapter.apply_adaptation(decisions[0], context)

    print(f"✅ Updated pending agents: {updated_context.pending_agents}")

    assert "reviewer" not in updated_context.pending_agents, "Reviewer should be skipped"

    print("✅ Test 2 PASSED: Optimization-based skip works")
    return True


async def test_3_repeat_agent_persistent_errors():
    """Test 3: Repeat Fixer when errors persist"""
    print("\n" + "=" * 80)
    print("TEST 3: Repeat agent (persistent errors)")
    print("=" * 80)

    adapter = WorkflowAdapterV6()

    context = WorkflowContext(
        task_description="Fix compilation errors",
        current_phase="fixer",
        completed_agents=["architect", "codesmith", "fixer"],
        pending_agents=["reviewer"],
        results={},
        errors=[
            {"message": "NameError: x not defined", "severity": "high"},
            {"message": "ImportError: module not found", "severity": "high"},
            {"message": "SyntaxError: invalid syntax", "severity": "medium"},
            {"message": "TypeError: wrong type", "severity": "medium"}
        ],
        quality_scores={},
        metadata={}
    )

    decisions = await adapter.analyze_and_adapt(context)

    print(f"✅ Decisions: {len(decisions)}")

    assert len(decisions) > 0, "Should suggest repeating fixer"
    assert decisions[0].adaptation_type == AdaptationType.REPEAT_AGENT
    assert decisions[0].agent_id == "fixer"
    assert decisions[0].reason == AdaptationReason.ERROR_DETECTED

    # Apply adaptation
    updated_context = await adapter.apply_adaptation(decisions[0], context)

    print(f"✅ Updated pending agents: {updated_context.pending_agents}")

    assert updated_context.pending_agents[0] == "fixer", "Fixer should be at beginning"

    print("✅ Test 3 PASSED: Persistent error repeat works")
    return True


async def test_4_abort_workflow_critical_error():
    """Test 4: Abort workflow on critical error"""
    print("\n" + "=" * 80)
    print("TEST 4: Abort workflow (critical error)")
    print("=" * 80)

    adapter = WorkflowAdapterV6()

    context = WorkflowContext(
        task_description="Deploy application",
        current_phase="deployment",
        completed_agents=["architect", "codesmith", "reviewer"],
        pending_agents=["deployment"],
        results={},
        errors=[
            {"message": "Database connection failed", "severity": "critical"},
            {"message": "Authentication service unavailable", "severity": "critical"}
        ],
        quality_scores={},
        metadata={}
    )

    decisions = await adapter.analyze_and_adapt(context)

    print(f"✅ Decisions: {len(decisions)}")

    assert len(decisions) > 0, "Should abort on critical errors"
    assert decisions[0].adaptation_type == AdaptationType.ABORT_WORKFLOW
    assert decisions[0].reason == AdaptationReason.ERROR_DETECTED

    # Apply adaptation
    updated_context = await adapter.apply_adaptation(decisions[0], context)

    print(f"✅ Workflow aborted: {updated_context.metadata.get('aborted')}")

    assert updated_context.metadata.get("aborted") is True, "Workflow should be aborted"

    print("✅ Test 4 PASSED: Critical error abort works")
    return True


async def test_5_quality_driven_adaptation():
    """Test 5: Insert Reviewer when code quality is low"""
    print("\n" + "=" * 80)
    print("TEST 5: Quality-driven adaptation")
    print("=" * 80)

    adapter = WorkflowAdapterV6()

    context = WorkflowContext(
        task_description="Implement authentication",
        current_phase="codesmith",
        completed_agents=["architect", "codesmith"],
        pending_agents=["fixer"],
        results={},
        errors=[],
        quality_scores={"codesmith": 0.55},  # Low quality
        metadata={}
    )

    decisions = await adapter.analyze_and_adapt(context)

    print(f"✅ Decisions: {len(decisions)}")

    assert len(decisions) > 0, "Should insert reviewer for low quality"
    assert decisions[0].adaptation_type == AdaptationType.INSERT_AGENT
    assert decisions[0].agent_id == "reviewer"
    assert decisions[0].reason == AdaptationReason.QUALITY_ISSUE

    # Apply adaptation
    updated_context = await adapter.apply_adaptation(decisions[0], context)

    print(f"✅ Updated pending agents: {updated_context.pending_agents}")

    assert "reviewer" in updated_context.pending_agents, "Reviewer should be inserted"

    print("✅ Test 5 PASSED: Quality-driven adaptation works")
    return True


async def test_6_multiple_adaptations():
    """Test 6: Handle multiple adaptations in sequence"""
    print("\n" + "=" * 80)
    print("TEST 6: Multiple adaptations")
    print("=" * 80)

    adapter = WorkflowAdapterV6()

    context = WorkflowContext(
        task_description="Complex feature",
        current_phase="codesmith",
        completed_agents=["architect", "codesmith"],
        pending_agents=["fixer"],  # No reviewer yet
        results={
            "architect": {
                "dependencies": [
                    {"name": "unknown_lib", "status": "missing"}
                ]
            }
        },
        errors=[],
        quality_scores={"codesmith": 0.6},  # Low quality (<0.7)
        metadata={}
    )

    decisions = await adapter.analyze_and_adapt(context)

    print(f"✅ Decisions: {len(decisions)}")
    for i, decision in enumerate(decisions, 1):
        print(f"   {i}. {decision.adaptation_type.value}: {decision.agent_id} ({decision.reason.value})")

    # Should have both missing dependency (research) and low quality (reviewer)
    assert len(decisions) >= 2, f"Should have multiple adaptation decisions, got {len(decisions)}"

    # Check decision types
    decision_types = [d.adaptation_type for d in decisions]
    assert AdaptationType.INSERT_AGENT in decision_types, "Should insert agent"

    # Apply all adaptations
    for decision in decisions:
        context = await adapter.apply_adaptation(decision, context)

    print(f"✅ Final pending agents: {context.pending_agents}")

    # Should have inserted research and/or reviewer
    has_research = "research" in context.pending_agents
    has_reviewer = "reviewer" in context.pending_agents

    assert has_research or has_reviewer, "Should have inserted at least one agent"

    print("✅ Test 6 PASSED: Multiple adaptations work")
    return True


async def test_7_adaptation_statistics():
    """Test 7: Adaptation statistics tracking"""
    print("\n" + "=" * 80)
    print("TEST 7: Adaptation statistics")
    print("=" * 80)

    adapter = WorkflowAdapterV6()

    # Make several adaptations
    context = WorkflowContext(
        task_description="Test workflow",
        current_phase="test",
        completed_agents=[],
        pending_agents=["architect", "codesmith"],
        results={},
        errors=[],
        quality_scores={},
        metadata={}
    )

    # Adaptation 1: Insert agent
    from workflow.workflow_adapter_v6 import AdaptationDecision
    decision1 = AdaptationDecision(
        adaptation_type=AdaptationType.INSERT_AGENT,
        reason=AdaptationReason.MISSING_DEPENDENCY,
        agent_id="research",
        details={"insert_before": "codesmith"},
        confidence=0.9,
        timestamp=datetime.now()
    )
    context = await adapter.apply_adaptation(decision1, context)

    # Adaptation 2: Skip agent
    decision2 = AdaptationDecision(
        adaptation_type=AdaptationType.SKIP_AGENT,
        reason=AdaptationReason.OPTIMIZATION,
        agent_id="reviewer",
        details={},
        confidence=0.8,
        timestamp=datetime.now()
    )
    await adapter.apply_adaptation(decision2, context)

    # Adaptation 3: Repeat agent
    decision3 = AdaptationDecision(
        adaptation_type=AdaptationType.REPEAT_AGENT,
        reason=AdaptationReason.ERROR_DETECTED,
        agent_id="fixer",
        details={},
        confidence=0.95,
        timestamp=datetime.now()
    )
    await adapter.apply_adaptation(decision3, context)

    # Get statistics
    stats = adapter.get_adaptation_stats()

    print(f"✅ Statistics: {stats}")

    assert stats["total_adaptations"] == 3, "Should have 3 adaptations"
    assert "insert_agent" in stats["by_type"], "Should track INSERT_AGENT"
    assert "skip_agent" in stats["by_type"], "Should track SKIP_AGENT"
    assert "repeat_agent" in stats["by_type"], "Should track REPEAT_AGENT"

    assert stats["by_type"]["insert_agent"] == 1
    assert stats["by_type"]["skip_agent"] == 1
    assert stats["by_type"]["repeat_agent"] == 1

    assert "missing_dependency" in stats["by_reason"]
    assert "optimization" in stats["by_reason"]
    assert "error_detected" in stats["by_reason"]

    print("✅ Test 7 PASSED: Statistics tracking works")
    return True


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("🧪 WORKFLOW ADAPTER V6 E2E TESTS")
    print("=" * 80)

    tests = [
        test_1_insert_agent_missing_dependency,
        test_2_skip_agent_optimization,
        test_3_repeat_agent_persistent_errors,
        test_4_abort_workflow_critical_error,
        test_5_quality_driven_adaptation,
        test_6_multiple_adaptations,
        test_7_adaptation_statistics,
    ]

    results = []

    for i, test in enumerate(tests, 1):
        try:
            result = await test()
            results.append(("PASS", test.__name__))
            print(f"\n✅ Test {i}/{len(tests)} PASSED")
        except AssertionError as e:
            results.append(("FAIL", test.__name__, str(e)))
            print(f"\n❌ Test {i}/{len(tests)} FAILED: {e}")
        except Exception as e:
            results.append(("ERROR", test.__name__, str(e)))
            print(f"\n💥 Test {i}/{len(tests)} ERROR: {e}")

    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for r in results if r[0] == "PASS")
    failed = sum(1 for r in results if r[0] == "FAIL")
    errors = sum(1 for r in results if r[0] == "ERROR")

    for result in results:
        status = result[0]
        name = result[1]
        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "💥"
        print(f"{icon} {name}: {status}")
        if len(result) > 2:
            print(f"   {result[2]}")

    print(f"\n{'='*80}")
    print(f"Total: {len(tests)} | Passed: {passed} | Failed: {failed} | Errors: {errors}")
    print(f"{'='*80}")

    if passed == len(tests):
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return True
    else:
        print(f"\n❌ {failed + errors} TEST(S) FAILED")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
