"""
E2E Tests for Approval Manager v6

Tests:
1. Auto-approval by rule (requires_approval=False)
2. Auto-approval by pattern match
3. Auto-rejection by pattern match
4. Human approval (simulated WebSocket)
5. Human rejection (simulated WebSocket)
6. Timeout scenario
7. Multiple pending requests
8. Approval statistics

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

from workflow.approval_manager_v6 import (
    ApprovalAction,
    ApprovalManagerV6,
    ApprovalRule,
    ApprovalStatus,
)


async def test_1_auto_approval_by_rule():
    """Test 1: Auto-approval when rule.requires_approval = False"""
    print("\n" + "=" * 80)
    print("TEST 1: Auto-approval by rule")
    print("=" * 80)

    manager = ApprovalManagerV6()

    # Add rule that doesn't require approval
    manager.add_rule(ApprovalRule(
        action_type=ApprovalAction.CUSTOM,
        requires_approval=False,
        timeout_seconds=60.0,
        description="Custom action (auto-approve)"
    ))

    result = await manager.request_approval(
        action_type=ApprovalAction.CUSTOM,
        description="Test custom action",
        details={"target": "test.py"}
    )

    print(f"✅ Result: {result}")

    assert result["approved"] is True, "Should be auto-approved"
    assert result["auto_decision"] is True, "Should be auto-decision"
    assert result["status"] == ApprovalStatus.APPROVED

    print("✅ Test 1 PASSED: Auto-approval by rule works")
    return True


async def test_2_auto_approval_by_pattern():
    """Test 2: Auto-approval by pattern match"""
    print("\n" + "=" * 80)
    print("TEST 2: Auto-approval by pattern")
    print("=" * 80)

    manager = ApprovalManagerV6()

    result = await manager.request_approval(
        action_type=ApprovalAction.FILE_WRITE,
        description="Write test file",
        details={"file_path": "test_example.py"}
    )

    print(f"✅ Result: {result}")

    assert result["approved"] is True, "Test file should be auto-approved"
    assert result["auto_decision"] is True, "Should be auto-decision"
    assert "pattern" in result["response"].lower()

    print("✅ Test 2 PASSED: Auto-approval by pattern works")
    return True


async def test_3_auto_rejection_by_pattern():
    """Test 3: Auto-rejection by pattern match"""
    print("\n" + "=" * 80)
    print("TEST 3: Auto-rejection by pattern")
    print("=" * 80)

    manager = ApprovalManagerV6()

    result = await manager.request_approval(
        action_type=ApprovalAction.FILE_DELETE,
        description="Delete .env file",
        details={"file_path": ".env"}
    )

    print(f"✅ Result: {result}")

    assert result["approved"] is False, ".env deletion should be auto-rejected"
    assert result["auto_decision"] is True, "Should be auto-decision"
    assert result["status"] == ApprovalStatus.REJECTED
    assert "pattern" in result["response"].lower()

    print("✅ Test 3 PASSED: Auto-rejection by pattern works")
    return True


async def test_4_human_approval():
    """Test 4: Human approval via simulated WebSocket"""
    print("\n" + "=" * 80)
    print("TEST 4: Human approval (simulated)")
    print("=" * 80)

    # Simulated WebSocket callback (approves after 0.5s)
    async def mock_websocket_approve(request: dict) -> dict:
        print(f"📤 WebSocket prompt sent: {request['description']}")
        await asyncio.sleep(0.5)  # Simulate user thinking
        print("✅ User approved!")
        return {
            "approved": True,
            "response": "User approved the action"
        }

    manager = ApprovalManagerV6(websocket_callback=mock_websocket_approve)

    result = await manager.request_approval(
        action_type=ApprovalAction.FILE_WRITE,
        description="Write critical file",
        details={"file_path": "critical.py"}
    )

    print(f"✅ Result: {result}")

    assert result["approved"] is True, "Should be approved by user"
    assert result["auto_decision"] is False, "Should be human decision"
    assert result["status"] == ApprovalStatus.APPROVED

    print("✅ Test 4 PASSED: Human approval works")
    return True


async def test_5_human_rejection():
    """Test 5: Human rejection via simulated WebSocket"""
    print("\n" + "=" * 80)
    print("TEST 5: Human rejection (simulated)")
    print("=" * 80)

    # Simulated WebSocket callback (rejects after 0.5s)
    async def mock_websocket_reject(request: dict) -> dict:
        print(f"📤 WebSocket prompt sent: {request['description']}")
        await asyncio.sleep(0.5)
        print("❌ User rejected!")
        return {
            "approved": False,
            "response": "User rejected the action"
        }

    manager = ApprovalManagerV6(websocket_callback=mock_websocket_reject)

    result = await manager.request_approval(
        action_type=ApprovalAction.DEPLOYMENT,
        description="Deploy to production",
        details={"target": "production"}
    )

    print(f"✅ Result: {result}")

    assert result["approved"] is False, "Should be rejected by user"
    assert result["auto_decision"] is False, "Should be human decision"
    assert result["status"] == ApprovalStatus.REJECTED

    print("✅ Test 5 PASSED: Human rejection works")
    return True


async def test_6_timeout():
    """Test 6: Timeout when no response"""
    print("\n" + "=" * 80)
    print("TEST 6: Timeout scenario")
    print("=" * 80)

    # Simulated WebSocket callback that takes too long
    async def mock_websocket_slow(request: dict) -> dict:
        print(f"📤 WebSocket prompt sent: {request['description']}")
        await asyncio.sleep(5.0)  # Too long!
        return {"approved": True, "response": "Too late!"}

    manager = ApprovalManagerV6(websocket_callback=mock_websocket_slow)

    # Override timeout to 1 second for faster test
    manager.update_rule(
        action_type=ApprovalAction.SHELL_COMMAND,
        timeout_seconds=1.0
    )

    result = await manager.request_approval(
        action_type=ApprovalAction.SHELL_COMMAND,
        description="Run dangerous command",
        details={"command": "rm file.py"}
    )

    print(f"✅ Result: {result}")

    assert result["approved"] is False, "Timeout should result in rejection"
    assert result["status"] == ApprovalStatus.TIMEOUT
    assert "timeout" in result["response"].lower()

    print("✅ Test 6 PASSED: Timeout handling works")
    return True


async def test_7_multiple_requests():
    """Test 7: Multiple pending requests"""
    print("\n" + "=" * 80)
    print("TEST 7: Multiple pending requests")
    print("=" * 80)

    # Callback that waits for respond_to_request()
    pending_responses: dict[str, dict] = {}

    async def mock_websocket_manual(request: dict) -> dict:
        request_id = request["request_id"]
        print(f"📤 Request {request_id} sent, waiting for manual response...")

        # Wait for manual response
        while request_id not in pending_responses:
            await asyncio.sleep(0.1)

        return pending_responses[request_id]

    manager = ApprovalManagerV6(websocket_callback=mock_websocket_manual)

    # Start 3 approval requests concurrently
    task1 = asyncio.create_task(manager.request_approval(
        action_type=ApprovalAction.FILE_WRITE,
        description="Write file 1",
        details={"file_path": "file1.py"}
    ))

    task2 = asyncio.create_task(manager.request_approval(
        action_type=ApprovalAction.FILE_WRITE,
        description="Write file 2",
        details={"file_path": "file2.py"}
    ))

    task3 = asyncio.create_task(manager.request_approval(
        action_type=ApprovalAction.FILE_DELETE,
        description="Delete file 3",
        details={"file_path": "file3.py"}
    ))

    # Wait for all to be pending
    await asyncio.sleep(0.5)

    # Check pending
    pending = manager.get_pending_requests()
    print(f"✅ Pending requests: {len(pending)}")

    assert len(pending) == 3, "Should have 3 pending requests"

    # Respond to each
    for req in pending:
        request_id = req["request_id"]
        print(f"✅ Responding to {request_id}...")

        # Approve first two, reject third
        approved = req["description"] != "Delete file 3"
        pending_responses[request_id] = {
            "approved": approved,
            "response": "Manual response"
        }
        manager.respond_to_request(request_id, approved, "Manual response")

    # Wait for all tasks
    results = await asyncio.gather(task1, task2, task3)

    print(f"✅ Results: {results}")

    assert results[0]["approved"] is True, "File 1 should be approved"
    assert results[1]["approved"] is True, "File 2 should be approved"
    assert results[2]["approved"] is False, "File 3 should be rejected"

    # Check pending is now empty
    pending_after = manager.get_pending_requests()
    assert len(pending_after) == 0, "All requests should be resolved"

    print("✅ Test 7 PASSED: Multiple requests work")
    return True


async def test_8_statistics():
    """Test 8: Approval statistics"""
    print("\n" + "=" * 80)
    print("TEST 8: Approval statistics")
    print("=" * 80)

    # Create fresh manager with no WebSocket callback (auto-approves)
    manager = ApprovalManagerV6(websocket_callback=None)

    # Make several requests with different outcomes
    print("📊 Making approval requests...")

    # 1. Auto-approve by pattern
    result1 = await manager.request_approval(
        action_type=ApprovalAction.FILE_WRITE,
        description="Test file",
        details={"file_path": "test_stats.py"}
    )
    print(f"   Request 1 (test file): {result1['status'].value}")

    # 2. Auto-reject by pattern
    result2 = await manager.request_approval(
        action_type=ApprovalAction.FILE_DELETE,
        description="Delete .env",
        details={"file_path": ".env"}
    )
    print(f"   Request 2 (.env delete): {result2['status'].value}")

    # 3. Auto-approve (no approval needed)
    manager.add_rule(ApprovalRule(
        action_type=ApprovalAction.CUSTOM,
        requires_approval=False,
        timeout_seconds=60.0
    ))
    result3 = await manager.request_approval(
        action_type=ApprovalAction.CUSTOM,
        description="Custom action",
        details={}
    )
    print(f"   Request 3 (custom): {result3['status'].value}")

    # Get stats
    stats = manager.get_approval_stats()
    print(f"\n✅ Statistics: {stats}")

    # Get history first for debugging
    history = manager.get_history()
    print(f"✅ History entries: {len(history)}")
    for entry in history:
        print(f"   - {entry['action_type']}: {entry['status']}")

    assert stats["total_requests"] == 3, f"Should have 3 requests, got {stats['total_requests']}"
    assert stats["approved"] == 2, f"Should have 2 approved, got {stats['approved']}"
    assert stats["rejected"] == 1, f"Should have 1 rejected, got {stats['rejected']}"
    assert 0.66 <= stats["approval_rate"] <= 0.67, f"Approval rate should be ~2/3, got {stats['approval_rate']}"

    assert len(history) == 3, f"History should have 3 entries, got {len(history)}"

    print("✅ Test 8 PASSED: Statistics work")
    return True


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("🧪 APPROVAL MANAGER V6 E2E TESTS")
    print("=" * 80)

    tests = [
        test_1_auto_approval_by_rule,
        test_2_auto_approval_by_pattern,
        test_3_auto_rejection_by_pattern,
        test_4_human_approval,
        test_5_human_rejection,
        test_6_timeout,
        test_7_multiple_requests,
        test_8_statistics,
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
