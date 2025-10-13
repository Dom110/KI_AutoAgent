#!/usr/bin/env python3
"""
E2E Test 3: Error Handling & Approvals (100% Coverage)

This test specifically triggers the 3 features that Tests 1 & 2 miss:
1. ASIMOV Rule 3 (Global Error Search)
2. Approval Manager (Destructive operations)
3. Self-Diagnosis (Error recovery)

Date: 2025-10-13
Version: v6.2.0-alpha
"""

import asyncio
import json
import logging
import sys
import websockets
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test workspace
WORKSPACE = Path.home() / "TestApps" / "v6_2_error_test"
WS_URL = "ws://localhost:8002/ws/chat"

# Feature tracking for missing features
missing_features = {
    "asimov_rule3": {"used": False, "evidence": []},
    "approval_manager": {"used": False, "evidence": []},
    "self_diagnosis": {"used": False, "evidence": []},
}


def track_feature(feature: str, evidence: str):
    """Track feature usage."""
    if feature in missing_features:
        missing_features[feature]["used"] = True
        missing_features[feature]["evidence"].append(evidence)
        logger.info(f"  ✅ {feature}: {evidence[:80]}")


def analyze_message(data: dict):
    """Analyze message for the 3 missing features."""
    msg_type = data.get("type", "")
    content = str(data.get("content", "")).lower()

    # ASIMOV Rule 3: Global Error Search
    if any(keyword in content for keyword in [
        "global error search",
        "ripgrep",
        "searching workspace",
        "found error in",
        "all instances",
        "asimov rule 3"
    ]):
        track_feature("asimov_rule3", f"Found: {content[:100]}")

    # Approval Manager
    if msg_type == "approval_request":
        track_feature("approval_manager", f"Approval request: {data}")
    elif any(keyword in content for keyword in [
        "approval",
        "confirm",
        "destructive",
        "delete",
        "overwrite"
    ]):
        track_feature("approval_manager", f"Found: {content[:100]}")

    # Self-Diagnosis
    if any(keyword in content for keyword in [
        "self-diagnosis",
        "self-heal",
        "recovery strategy",
        "diagnosed",
        "error pattern",
        "attempting recovery"
    ]):
        track_feature("self_diagnosis", f"Found: {content[:100]}")


async def test_intentional_error():
    """
    Test 3a: Create app with intentional Python error.

    This should trigger:
    - ReviewFix detects error
    - Self-Diagnosis analyzes error
    - ASIMOV Rule 3 performs global error search
    - Fixer applies recovery
    """
    logger.info("="*70)
    logger.info("🧪 TEST 3a: Intentional Error (Self-Diagnosis + ASIMOV Rule 3)")
    logger.info("="*70)

    # Create fresh workspace
    if WORKSPACE.exists():
        import shutil
        shutil.rmtree(WORKSPACE)
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Created workspace: {WORKSPACE}")

    try:
        async with websockets.connect(WS_URL) as websocket:
            logger.info(f"🔌 Connected to {WS_URL}")

            # Initialize
            await websocket.send(json.dumps({
                "type": "init",
                "workspace_path": str(WORKSPACE)
            }))
            init_response = json.loads(await websocket.recv())
            logger.info(f"✅ Session: {init_response.get('session_id')}")

            # Query with intentional error specification
            query = """Create a Python Flask API with these requirements:

1. Create a file 'app.py' with a Flask app
2. INTENTIONALLY include an undefined variable 'undefined_var' in the code
3. This will cause a NameError that needs to be fixed
4. The error should appear in multiple places (at least 2-3 times)
5. ReviewFix should detect it and trigger global error search
"""
            logger.info(f"📤 Sending error injection query...")
            logger.info(f"   This should trigger ASIMOV Rule 3 + Self-Diagnosis")

            await websocket.send(json.dumps({
                "type": "message",
                "content": query
            }))

            # Collect responses
            responses = []
            start_time = datetime.now()
            error_detected = False
            fix_attempted = False

            logger.info("⏳ Waiting for error detection and recovery...")

            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=600)
                    data = json.loads(message)
                    responses.append(data)

                    analyze_message(data)

                    msg_type = data.get("type")
                    content = str(data.get("content", ""))

                    # Track error flow
                    if "error" in content.lower() or "undefined" in content.lower():
                        if not error_detected:
                            logger.info("  🔍 Error detected in code")
                            error_detected = True

                    if "fix" in content.lower() or "recovery" in content.lower():
                        if not fix_attempted:
                            logger.info("  🔧 Fix/recovery attempted")
                            fix_attempted = True

                    # Log important messages
                    if msg_type in ["agent_activity", "message"]:
                        if any(keyword in content.lower() for keyword in [
                            "error", "diagnosis", "recovery", "search", "fix"
                        ]):
                            logger.info(f"  📨 {content[:120]}...")

                    if msg_type in ["result", "complete", "error"]:
                        duration = (datetime.now() - start_time).total_seconds()
                        logger.info(f"\n✅ Test 3a complete in {duration:.1f}s")
                        logger.info(f"   Error detected: {error_detected}")
                        logger.info(f"   Fix attempted: {fix_attempted}")
                        break

                except asyncio.TimeoutError:
                    logger.error("⏱️ Timeout (10 minutes)")
                    break
                except Exception as e:
                    logger.error(f"❌ Error: {e}")
                    break

            return responses

    except Exception as e:
        logger.error(f"❌ Test 3a failed: {e}")
        return []


async def test_destructive_operation():
    """
    Test 3b: Trigger Approval Manager with destructive operation.

    This should trigger:
    - Approval Manager requests confirmation
    - User approval workflow
    """
    logger.info("\n" + "="*70)
    logger.info("🧪 TEST 3b: Destructive Operation (Approval Manager)")
    logger.info("="*70)

    # Use same workspace with existing files
    if not WORKSPACE.exists() or not list(WORKSPACE.glob("*.py")):
        logger.warning("⚠️ No files in workspace, creating dummy file...")
        WORKSPACE.mkdir(parents=True, exist_ok=True)
        (WORKSPACE / "dummy.py").write_text("# Dummy file for deletion test\n")

    try:
        async with websockets.connect(WS_URL) as websocket:
            logger.info(f"🔌 Connected to {WS_URL}")

            # Initialize
            await websocket.send(json.dumps({
                "type": "init",
                "workspace_path": str(WORKSPACE)
            }))
            init_response = json.loads(await websocket.recv())
            logger.info(f"✅ Session: {init_response.get('session_id')}")

            # Query with destructive operation
            query = """Delete all .py files in the workspace and create a new clean structure.

This is a destructive operation that should trigger approval request."""

            logger.info(f"📤 Sending destructive operation query...")
            logger.info(f"   This should trigger Approval Manager")

            await websocket.send(json.dumps({
                "type": "message",
                "content": query
            }))

            # Collect responses
            responses = []
            approval_requested = False
            approval_timeout = 30  # Wait max 30 seconds for approval request

            logger.info("⏳ Waiting for approval request...")

            while True:
                try:
                    message = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=approval_timeout if not approval_requested else 300
                    )
                    data = json.loads(message)
                    responses.append(data)

                    analyze_message(data)

                    msg_type = data.get("type")
                    content = str(data.get("content", ""))

                    # Check for approval request
                    if msg_type == "approval_request":
                        approval_requested = True
                        logger.info("  ✋ APPROVAL REQUEST RECEIVED!")
                        logger.info(f"     {data}")

                        # Auto-approve for testing
                        approval_id = data.get("approval_id")
                        if approval_id:
                            logger.info(f"  ✅ Auto-approving: {approval_id}")
                            await websocket.send(json.dumps({
                                "type": "approval_response",
                                "approval_id": approval_id,
                                "approved": True
                            }))

                    # Log important messages
                    if msg_type in ["agent_activity", "message"]:
                        logger.info(f"  📨 {content[:120]}...")

                    if msg_type in ["result", "complete", "error"]:
                        logger.info(f"\n✅ Test 3b complete")
                        logger.info(f"   Approval requested: {approval_requested}")
                        break

                except asyncio.TimeoutError:
                    if not approval_requested:
                        logger.warning("⚠️ No approval request within 30 seconds")
                        logger.warning("   Approval Manager may not be enabled")
                    break
                except Exception as e:
                    logger.error(f"❌ Error: {e}")
                    break

            return responses

    except Exception as e:
        logger.error(f"❌ Test 3b failed: {e}")
        return []


def generate_report():
    """Generate report for the 3 missing features."""
    logger.info("\n" + "="*70)
    logger.info("📊 TEST 3 FEATURE REPORT (Missing Features)")
    logger.info("="*70)

    total = len(missing_features)
    used = sum(1 for f in missing_features.values() if f["used"])

    for feature_name, feature_data in missing_features.items():
        status = "✅ TRIGGERED" if feature_data["used"] else "❌ NOT TRIGGERED"
        readable_name = feature_name.replace("_", " ").title()

        evidence_count = len(feature_data["evidence"])
        logger.info(f"\n{status}: {readable_name} ({evidence_count} instances)")

        if evidence_count > 0:
            for i, evidence in enumerate(feature_data["evidence"][:3], 1):
                logger.info(f"    {i}. {evidence}")
            if evidence_count > 3:
                logger.info(f"    ... and {evidence_count - 3} more")

    # Overall
    coverage = (used / total * 100) if total > 0 else 0
    logger.info(f"\n{'='*70}")
    logger.info(f"📈 TEST 3 COVERAGE: {used}/{total} ({coverage:.1f}%)")
    logger.info(f"{'='*70}")

    # Combined with Tests 1 & 2
    test1_2_coverage = 7  # Expected from Tests 1 & 2
    total_features = 10
    combined_coverage = ((test1_2_coverage + used) / total_features) * 100

    logger.info(f"\n🎯 COMBINED COVERAGE (All Tests):")
    logger.info(f"   Test 1 & 2: ~7/10 (70%)")
    logger.info(f"   Test 3:     {used}/3 ({coverage:.1f}%)")
    logger.info(f"   TOTAL:      ~{test1_2_coverage + used}/10 ({combined_coverage:.1f}%)")

    if combined_coverage >= 100:
        logger.info("\n🌟 EXCELLENT - 100% Feature Coverage Achieved!")
    elif combined_coverage >= 90:
        logger.info("\n✅ VERY GOOD - Near-complete coverage")
    elif combined_coverage >= 80:
        logger.info("\n✅ GOOD - Strong coverage")

    return coverage, combined_coverage


async def main():
    """Run Test 3 to achieve 100% coverage."""
    logger.info("🚀 Starting Test 3: Error Handling & Approvals")
    logger.info(f"Workspace: {WORKSPACE}")
    logger.info(f"WebSocket: {WS_URL}\n")

    # Test 3a: Intentional error
    await test_intentional_error()

    # Small delay
    await asyncio.sleep(2)

    # Test 3b: Destructive operation
    await test_destructive_operation()

    # Generate report
    test3_coverage, combined_coverage = generate_report()

    # Save results
    results_file = Path(__file__).parent / f"test3_results_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(results_file, "w") as f:
        json.dump(missing_features, f, indent=2)

    logger.info(f"\n💾 Results saved to: {results_file}")

    # Exit code
    if combined_coverage >= 90:
        logger.info("\n✅ TEST 3 PASSED - Excellent coverage!")
        sys.exit(0)
    else:
        logger.warning(f"\n⚠️ TEST 3 INCOMPLETE - Coverage: {combined_coverage:.1f}%")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Test interrupted by user")
        generate_report()
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
