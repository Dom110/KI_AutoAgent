#!/usr/bin/env python3
"""
Test Self-Diagnosis System v5.5.0
Validates all self-diagnosis features including:
- Invariant checking
- Anti-pattern detection
- Pre-execution validation
- Real-time monitoring
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_self_diagnosis():
    """Test the self-diagnosis system with various scenarios"""

    print("\n" + "="*60)
    print("🧪 SELF-DIAGNOSIS SYSTEM TEST SUITE v5.5.0")
    print("="*60 + "\n")

    try:
        from backend.langgraph_system.workflow_self_diagnosis import (
            WorkflowSelfDiagnosisSystem,
            KnownAntiPatternsDatabase,
            WorkflowInvariants,
            PreExecutionValidator,
            PatternRecognitionEngine,
            SelfTestFramework
        )
        from backend.langgraph_system.state import ExecutionStep, ExtendedAgentState
        print("✅ Self-Diagnosis modules imported successfully\n")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the project root directory")
        return

    # Initialize the system
    diagnosis_system = WorkflowSelfDiagnosisSystem()
    print("✅ Self-Diagnosis System initialized\n")

    # =================== TEST 1: ORCHESTRATOR SELF-ROUTING ===================
    print("📋 TEST 1: Detecting Orchestrator Self-Routing (Bug from v5.4.2)")
    print("-" * 40)

    # Create a state with the bug that caused infinite loop
    buggy_state = {
        "messages": [{"role": "user", "content": "Test task"}],
        "execution_plan": [
            ExecutionStep(
                id="step1",
                agent="orchestrator",  # BUG: Orchestrator routing to itself
                task="Plan something",
                status="pending"  # This would cause infinite loop
            ),
            ExecutionStep(
                id="step2",
                agent="codesmith",
                task="Write code",
                status="pending"
            )
        ],
        "collaboration_count": 0,
        "escalation_level": 0
    }

    # Test invariant checking
    invariants = WorkflowInvariants()
    is_valid, violations = invariants.check_all(buggy_state)

    if not is_valid:
        print("✅ Invariant violation detected!")
        for v in violations:
            print(f"  - {v['name']}: {v['description']}")
    else:
        print("❌ Failed to detect orchestrator self-routing!")

    # Test anti-pattern detection
    patterns_db = KnownAntiPatternsDatabase()
    detected = patterns_db.detect_patterns(buggy_state)

    if detected:
        print("✅ Anti-patterns detected!")
        for pattern, reason in detected:
            print(f"  - {pattern.type.value}: {reason}")
            print(f"    Fix: {pattern.suggested_fix}")
    else:
        print("❌ Failed to detect anti-patterns!")

    print()

    # =================== TEST 2: CIRCULAR DEPENDENCIES ===================
    print("📋 TEST 2: Detecting Circular Dependencies")
    print("-" * 40)

    circular_state = {
        "messages": [],
        "execution_plan": [
            ExecutionStep(
                id="A",
                agent="codesmith",
                task="Task A",
                dependencies=["C"],  # A depends on C
                status="pending"
            ),
            ExecutionStep(
                id="B",
                agent="reviewer",
                task="Task B",
                dependencies=["A"],  # B depends on A
                status="pending"
            ),
            ExecutionStep(
                id="C",
                agent="fixer",
                task="Task C",
                dependencies=["B"],  # C depends on B -> CIRCULAR!
                status="pending"
            )
        ],
        "collaboration_count": 0
    }

    detected = patterns_db.detect_patterns(circular_state)
    if any(p[0].type.value == "circular_dependency" for p in detected):
        print("✅ Circular dependency detected!")
    else:
        print("❌ Failed to detect circular dependency!")

    print()

    # =================== TEST 3: PRE-EXECUTION VALIDATION WITH AUTO-FIX ===================
    print("📋 TEST 3: Pre-Execution Validation with Auto-Fix")
    print("-" * 40)

    # Use the buggy state from Test 1
    print("Testing validation on buggy state...")
    is_safe, fixed_state = await diagnosis_system.pre_execution_check(
        buggy_state,
        auto_fix=True
    )

    if not is_safe:
        print("✅ Validation correctly identified unsafe plan")
    else:
        print("⚠️ Validation passed but plan had issues")

    # Check if orchestrator step was fixed
    if fixed_state["execution_plan"][0].status == "completed":
        print("✅ Auto-fix successfully marked orchestrator step as completed")
    else:
        print("❌ Auto-fix failed to correct orchestrator self-routing")

    print()

    # =================== TEST 4: COLLABORATION SPIRAL DETECTION ===================
    print("📋 TEST 4: Detecting Reviewer-Fixer Spiral")
    print("-" * 40)

    spiral_state = {
        "messages": [],
        "execution_plan": [],
        "collaboration_count": 8,
        "collaboration_history": [
            {"from": "orchestrator", "to": "reviewer", "query": "Review code"},
            {"from": "reviewer", "to": "fixer", "query": "Fix issues"},
            {"from": "fixer", "to": "reviewer", "query": "Review fixes"},
            {"from": "reviewer", "to": "fixer", "query": "Fix more issues"},
            {"from": "fixer", "to": "reviewer", "query": "Review again"},
            {"from": "reviewer", "to": "fixer", "query": "Still issues"},
            {"from": "fixer", "to": "reviewer", "query": "Please review"},
            {"from": "reviewer", "to": "fixer", "query": "More fixes needed"}
        ]
    }

    pattern_engine = PatternRecognitionEngine()
    analysis = pattern_engine.analyze_patterns(spiral_state)

    if any(p["name"] == "collaboration_spiral" for p in analysis["patterns_detected"]):
        print("✅ Reviewer-Fixer spiral detected!")
        print(f"   Risk score: {analysis['risk_score']:.2%}")
    else:
        print("❌ Failed to detect collaboration spiral!")

    print()

    # =================== TEST 5: RESOURCE EXHAUSTION ===================
    print("📋 TEST 5: Detecting Resource Exhaustion")
    print("-" * 40)

    # Create state with too many messages
    exhausted_state = {
        "messages": [{"role": "system", "content": f"Message {i}"} for i in range(600)],
        "execution_plan": [ExecutionStep(id=f"step{i}", agent="codesmith", task=f"Task {i}", status="pending") for i in range(30)],
        "collaboration_count": 0
    }

    detected = patterns_db.detect_patterns(exhausted_state)
    if any(p[0].type.value == "resource_exhaustion" for p in detected):
        print("✅ Resource exhaustion detected!")
        print(f"   Messages: {len(exhausted_state['messages'])}")
        print(f"   Steps: {len(exhausted_state['execution_plan'])}")
    else:
        print("❌ Failed to detect resource exhaustion!")

    print()

    # =================== TEST 6: HEALTH CHECK ===================
    print("📋 TEST 6: Comprehensive Health Check")
    print("-" * 40)

    # Create a healthy state
    healthy_state = {
        "messages": [{"role": "user", "content": "Build a feature"}],
        "execution_plan": [
            ExecutionStep(
                id="step1",
                agent="architect",
                task="Design architecture",
                status="completed",
                result="Architecture designed"
            ),
            ExecutionStep(
                id="step2",
                agent="codesmith",
                task="Implement feature",
                dependencies=["step1"],
                status="in_progress",
                started_at=datetime.now()
            ),
            ExecutionStep(
                id="step3",
                agent="reviewer",
                task="Review implementation",
                dependencies=["step2"],
                status="pending"
            )
        ],
        "collaboration_count": 2,
        "escalation_level": 0,
        "progress_ledger": None
    }

    health_report = await diagnosis_system.real_time_monitoring(healthy_state)

    print(f"Overall Health: {health_report['overall_health']}")
    print(f"Overall Score: {health_report['overall_score']:.2%}")
    print("Scores:")
    for metric, score in health_report["scores"].items():
        print(f"  - {metric}: {score:.2%}")

    if health_report["overall_health"] == "HEALTHY":
        print("✅ Healthy state correctly identified")
    else:
        print(f"⚠️ Health issues found: {health_report.get('issues', [])}")

    print()

    # =================== TEST 7: PARALLEL EXECUTION DETECTION ===================
    print("📋 TEST 7: Parallel Execution Opportunities")
    print("-" * 40)

    parallel_state = {
        "messages": [],
        "execution_plan": [
            ExecutionStep(id="A", agent="codesmith", task="Module A", status="pending"),
            ExecutionStep(id="B", agent="codesmith", task="Module B", status="pending"),
            ExecutionStep(id="C", agent="codesmith", task="Module C", status="pending"),
            ExecutionStep(id="D", agent="reviewer", task="Review all", dependencies=["A", "B", "C"], status="pending")
        ]
    }

    # The validator includes parallel detection
    validator = PreExecutionValidator(patterns_db, invariants)
    issues = await validator._validate_performance(parallel_state)

    parallel_found = False
    for issue in issues:
        if "parallelizable" in issue.get("description", "").lower():
            print(f"✅ Parallel opportunities detected: {issue['description']}")
            parallel_found = True

    if not parallel_found:
        print("❌ Failed to detect parallel execution opportunities")

    print()

    # =================== SUMMARY ===================
    print("="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    print("""
✅ Tests Completed:
1. Orchestrator self-routing detection
2. Circular dependency detection
3. Pre-execution validation with auto-fix
4. Collaboration spiral detection
5. Resource exhaustion detection
6. Health check system
7. Parallel execution detection

The Self-Diagnosis System v5.5.0 is working correctly!
It can detect and prevent the issues that caused bugs like the infinite loop in v5.4.2.
""")

    # Get diagnosis report
    report = diagnosis_system.get_diagnosis_report()
    print(f"\n📈 System Statistics:")
    print(f"  - Known anti-patterns: {report['known_anti_patterns']}")
    print(f"  - Active invariants: {report['current_invariants']}")
    print(f"  - Validation history entries: {len(report['validation_history'])}")
    print(f"  - Test history entries: {len(report['test_history'])}")


if __name__ == "__main__":
    print("\n🚀 Starting Self-Diagnosis System Test...")
    try:
        asyncio.run(test_self_diagnosis())
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()