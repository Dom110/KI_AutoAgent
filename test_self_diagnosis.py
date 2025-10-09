"""
E2E Tests for Self-Diagnosis v6

Tests:
1. Diagnose import error
2. Diagnose syntax error
3. Suggest recovery actions
4. Apply recovery (retry)
5. Apply recovery (skip)
6. Full self-healing cycle
7. Health report
8. Unknown error handling

Author: KI AutoAgent Team
Version: 6.0.0
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from cognitive.self_diagnosis_v6 import (
    DiagnosticLevel,
    RecoveryStrategy,
    SelfDiagnosisV6,
)


async def test_1_diagnose_import_error():
    """Test 1: Diagnose import error"""
    print("\n" + "=" * 80)
    print("TEST 1: Diagnose import error")
    print("=" * 80)

    diagnosis = SelfDiagnosisV6()

    error = ImportError("cannot import name 'missing_module' from 'package'")

    diagnostics = await diagnosis.diagnose(error, {"component": "importer"})

    print(f"✅ Diagnostics: {len(diagnostics)}")
    for d in diagnostics:
        print(f"   - {d.level.value}: {d.message[:60]}")
        print(f"     Root cause: {d.root_cause}")

    assert len(diagnostics) > 0, "Should generate diagnostics"
    assert diagnostics[0].level == DiagnosticLevel.ERROR, "Should be ERROR level"
    assert "import" in diagnostics[0].root_cause.lower(), "Should identify import issue"

    print("✅ Test 1 PASSED: Import error diagnosis works")
    return True


async def test_2_diagnose_syntax_error():
    """Test 2: Diagnose syntax error"""
    print("\n" + "=" * 80)
    print("TEST 2: Diagnose syntax error")
    print("=" * 80)

    diagnosis = SelfDiagnosisV6()

    error_dict = {
        "type": "SyntaxError",
        "message": "invalid syntax at line 42"
    }

    diagnostics = await diagnosis.diagnose(error_dict)

    print(f"✅ Diagnostics: {len(diagnostics)}")
    print(f"   Root cause: {diagnostics[0].root_cause}")

    assert len(diagnostics) > 0, "Should generate diagnostics"
    assert "syntax" in diagnostics[0].root_cause.lower(), "Should identify syntax issue"

    print("✅ Test 2 PASSED: Syntax error diagnosis works")
    return True


async def test_3_suggest_recovery():
    """Test 3: Suggest recovery actions"""
    print("\n" + "=" * 80)
    print("TEST 3: Suggest recovery actions")
    print("=" * 80)

    diagnosis = SelfDiagnosisV6()

    # First diagnose
    error = ModuleNotFoundError("No module named 'missing_package'")
    diagnostics = await diagnosis.diagnose(error)

    # Then suggest recovery
    actions = await diagnosis.suggest_recovery(diagnostics[0])

    print(f"✅ Recovery actions: {len(actions)}")
    for action in actions:
        print(f"   - {action.strategy.value}: {action.description}")
        print(f"     Success rate: {action.estimated_success_rate:.0%}")
        print(f"     Steps: {len(action.steps)}")

    assert len(actions) >= 2, "Should suggest multiple recovery options"

    # Should include alternative strategy
    strategies = [a.strategy for a in actions]
    assert RecoveryStrategy.ALTERNATIVE in strategies or RecoveryStrategy.RETRY in strategies, \
        "Should suggest alternative or retry"

    print("✅ Test 3 PASSED: Recovery suggestion works")
    return True


async def test_4_apply_recovery_retry():
    """Test 4: Apply retry recovery"""
    print("\n" + "=" * 80)
    print("TEST 4: Apply retry recovery")
    print("=" * 80)

    diagnosis = SelfDiagnosisV6()

    # Create a retry action
    from cognitive.self_diagnosis_v6 import RecoveryAction

    action = RecoveryAction(
        action_id="test_retry_1",
        strategy=RecoveryStrategy.RETRY,
        description="Retry failed operation",
        steps=["Wait", "Retry"],
        estimated_success_rate=0.7,
        side_effects=[],
        requires_approval=False
    )

    result = await diagnosis.apply_recovery(action)

    print(f"✅ Recovery result:")
    print(f"   Success: {result.success}")
    print(f"   Outcome: {result.outcome}")
    print(f"   Applied steps: {result.applied_steps}")

    assert result.success is True, "Retry should succeed"
    assert "retry" in result.outcome.lower(), "Outcome should mention retry"

    print("✅ Test 4 PASSED: Retry recovery works")
    return True


async def test_5_apply_recovery_skip():
    """Test 5: Apply skip recovery"""
    print("\n" + "=" * 80)
    print("TEST 5: Apply skip recovery")
    print("=" * 80)

    diagnosis = SelfDiagnosisV6()

    from cognitive.self_diagnosis_v6 import RecoveryAction

    action = RecoveryAction(
        action_id="test_skip_1",
        strategy=RecoveryStrategy.SKIP,
        description="Skip problematic operation",
        steps=["Mark as skipped"],
        estimated_success_rate=1.0,
        side_effects=["Operation not done"],
        requires_approval=True
    )

    result = await diagnosis.apply_recovery(action)

    print(f"✅ Recovery result:")
    print(f"   Success: {result.success}")
    print(f"   Outcome: {result.outcome}")

    assert result.success is True, "Skip should succeed"
    assert "skip" in result.outcome.lower(), "Outcome should mention skip"

    print("✅ Test 5 PASSED: Skip recovery works")
    return True


async def test_6_self_healing_cycle():
    """Test 6: Full self-healing cycle"""
    print("\n" + "=" * 80)
    print("TEST 6: Full self-healing cycle")
    print("=" * 80)

    diagnosis = SelfDiagnosisV6()

    error = TypeError("unsupported operand type(s) for +: 'int' and 'str'")

    # Run full self-healing cycle with auto-apply
    result = await diagnosis.self_heal(
        error=error,
        context={"operation": "addition"},
        auto_apply=True
    )

    print(f"✅ Self-healing result:")
    print(f"   Success: {result['success']}")
    print(f"   Message: {result['message']}")
    print(f"   Diagnostics: {len(result['diagnostics'])}")
    print(f"   Actions: {len(result['actions'])}")
    print(f"   Recovery applied: {result['recovery'] is not None}")

    assert len(result["diagnostics"]) > 0, "Should generate diagnostics"
    assert len(result["actions"]) > 0, "Should suggest actions"

    if result["recovery"]:
        print(f"   Recovery outcome: {result['recovery'].outcome}")

    print("✅ Test 6 PASSED: Self-healing cycle works")
    return True


async def test_7_health_report():
    """Test 7: Generate health report"""
    print("\n" + "=" * 80)
    print("TEST 7: Health report")
    print("=" * 80)

    diagnosis = SelfDiagnosisV6()

    # Generate some diagnostics and recoveries
    await diagnosis.diagnose(ImportError("test error 1"))
    await diagnosis.diagnose(SyntaxError("test error 2"))
    await diagnosis.diagnose(TypeError("test error 3"))

    # Get health report
    report = diagnosis.get_health_report()

    print(f"✅ Health report:")
    print(f"   Total diagnostics: {report['total_diagnostics']}")
    print(f"   By level: {report['by_level']}")
    print(f"   Recovery attempts: {report['recovery_attempts']}")
    print(f"   Recovery success rate: {report['recovery_success_rate']:.0%}")
    print(f"   Recent issues: {len(report['recent_issues'])}")

    assert report["total_diagnostics"] >= 3, "Should have tracked diagnostics"
    assert "error" in report["by_level"], "Should categorize by level"

    print("✅ Test 7 PASSED: Health report generation works")
    return True


async def test_8_unknown_error():
    """Test 8: Handle unknown error type"""
    print("\n" + "=" * 80)
    print("TEST 8: Unknown error handling")
    print("=" * 80)

    diagnosis = SelfDiagnosisV6()

    # Custom error that doesn't match any pattern
    error = "CustomWeirdError: Something strange happened in subsystem XYZ"

    diagnostics = await diagnosis.diagnose(error)

    print(f"✅ Diagnostics: {len(diagnostics)}")
    print(f"   Root cause: {diagnostics[0].root_cause}")

    assert len(diagnostics) > 0, "Should still generate diagnostic"
    assert diagnostics[0].root_cause == "Unknown error pattern", "Should identify as unknown"

    # Should still be able to suggest generic recovery
    actions = await diagnosis.suggest_recovery(diagnostics[0])

    print(f"✅ Generic recovery actions: {len(actions)}")

    assert len(actions) >= 2, "Should suggest generic recovery options"

    print("✅ Test 8 PASSED: Unknown error handling works")
    return True


async def test_9_multiple_errors():
    """Test 9: Diagnose multiple errors"""
    print("\n" + "=" * 80)
    print("TEST 9: Multiple errors")
    print("=" * 80)

    diagnosis = SelfDiagnosisV6()

    # Multiple errors
    errors = [
        ImportError("missing module A"),
        TypeError("type mismatch in function B"),
        NameError("undefined variable C")
    ]

    all_diagnostics = []
    for error in errors:
        diagnostics = await diagnosis.diagnose(error)
        all_diagnostics.extend(diagnostics)

    print(f"✅ Total diagnostics: {len(all_diagnostics)}")

    # Get health report
    report = diagnosis.get_health_report()

    print(f"✅ Health summary:")
    print(f"   Tracked: {report['total_diagnostics']}")
    print(f"   Errors: {report['by_level'].get('error', 0)}")

    assert len(all_diagnostics) >= 3, "Should diagnose all errors"
    assert report["total_diagnostics"] >= 3, "Should track all diagnostics"

    print("✅ Test 9 PASSED: Multiple error handling works")
    return True


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("🧪 SELF-DIAGNOSIS V6 E2E TESTS")
    print("=" * 80)

    tests = [
        test_1_diagnose_import_error,
        test_2_diagnose_syntax_error,
        test_3_suggest_recovery,
        test_4_apply_recovery_retry,
        test_5_apply_recovery_skip,
        test_6_self_healing_cycle,
        test_7_health_report,
        test_8_unknown_error,
        test_9_multiple_errors,
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
