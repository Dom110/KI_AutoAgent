#!/usr/bin/env python3
"""
E2E Comprehensive Test for v6.2 - All Features
Tests all Phase 1-4 features with tracking

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
WORKSPACE = Path.home() / "TestApps" / "v6_2_comprehensive_test"
WS_URL = "ws://localhost:8002/ws/chat"

# Feature tracking matrix
features_used = {
    "phase1_production_essentials": {
        "perplexity_api": {"used": False, "evidence": []},
        "asimov_rule3": {"used": False, "evidence": []},
    },
    "phase2_intelligence": {
        "learning_system": {"used": False, "evidence": []},
        "curiosity_system": {"used": False, "evidence": []},
        "predictive_system": {"used": False, "evidence": []},
    },
    "phase3_workflow_optimization": {
        "tool_registry": {"used": False, "evidence": []},
        "approval_manager": {"used": False, "evidence": []},
        "dynamic_workflow": {"used": False, "evidence": []},
    },
    "phase4_advanced": {
        "neurosymbolic_reasoning": {"used": False, "evidence": []},
        "self_diagnosis": {"used": False, "evidence": []},
    },
}


def track_feature(phase: str, feature: str, evidence: str):
    """Track feature usage with evidence."""
    if phase in features_used and feature in features_used[phase]:
        features_used[phase][feature]["used"] = True
        features_used[phase][feature]["evidence"].append(evidence)
        logger.info(f"  ✅ Feature used: {feature} - {evidence[:60]}")


def analyze_message(data: dict):
    """Analyze message for feature usage."""
    msg_type = data.get("type", "")
    content = str(data.get("content", "")).lower()

    # Phase 1: Production Essentials
    if "perplexity" in content or "web search" in content or "citation" in content:
        track_feature("phase1_production_essentials", "perplexity_api",
                      f"Found: {content[:80]}")

    if "global error search" in content or "ripgrep" in content or "asimov rule 3" in content:
        track_feature("phase1_production_essentials", "asimov_rule3",
                      f"Found: {content[:80]}")

    # Phase 2: Intelligence Systems
    if "learning" in content or "pattern" in content or "similar project" in content:
        track_feature("phase2_intelligence", "learning_system",
                      f"Found: {content[:80]}")

    if "clarif" in content or "which framework" in content or "question" in content:
        track_feature("phase2_intelligence", "curiosity_system",
                      f"Found: {content[:80]}")

    if "predict" in content or "duration" in content or "complexity" in content or "estimated" in content:
        track_feature("phase2_intelligence", "predictive_system",
                      f"Found: {content[:80]}")

    # Phase 3: Workflow Optimization
    if "tool" in content and ("register" in content or "available" in content):
        track_feature("phase3_workflow_optimization", "tool_registry",
                      f"Found: {content[:80]}")

    if msg_type == "approval_request" or "approval" in content:
        track_feature("phase3_workflow_optimization", "approval_manager",
                      f"Type: {msg_type}, Content: {content[:60]}")

    if "workflow plan" in content or "agents:" in content or "steps:" in content:
        track_feature("phase3_workflow_optimization", "dynamic_workflow",
                      f"Found: {content[:80]}")

    # Phase 4: Advanced Features
    if "neurosymbolic" in content or "symbolic rule" in content or "reasoning" in content:
        track_feature("phase4_advanced", "neurosymbolic_reasoning",
                      f"Found: {content[:80]}")

    if "self-diagnosis" in content or "self-heal" in content or "recovery strategy" in content:
        track_feature("phase4_advanced", "self_diagnosis",
                      f"Found: {content[:80]}")


async def test_create_app():
    """
    Test 1: Create new app with intentionally ambiguous query.
    Should trigger Curiosity System and all other features.
    """
    logger.info("="*70)
    logger.info("🧪 TEST 1: New App Development with Feature Tracking")
    logger.info("="*70)

    # Create fresh workspace
    if WORKSPACE.exists():
        import shutil
        shutil.rmtree(WORKSPACE)
        logger.info(f"🧹 Cleaned old workspace: {WORKSPACE}")

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Created test workspace: {WORKSPACE}")

    try:
        async with websockets.connect(WS_URL) as websocket:
            logger.info(f"🔌 Connected to {WS_URL}")

            # Initialize session
            await websocket.send(json.dumps({
                "type": "init",
                "workspace_path": str(WORKSPACE)
            }))

            init_response = json.loads(await websocket.recv())
            session_id = init_response.get("session_id", "unknown")
            logger.info(f"✅ Session initialized: {session_id}")

            # Send intentionally ambiguous query
            query = "Create a task management app"
            logger.info(f"📤 Sending query: '{query}'")

            await websocket.send(json.dumps({
                "type": "message",
                "content": query
            }))

            # Collect all responses
            responses = []
            start_time = datetime.now()

            logger.info("⏳ Waiting for responses...")

            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=600)
                    data = json.loads(message)
                    responses.append(data)

                    msg_type = data.get("type")
                    content = str(data.get("content", ""))

                    # Analyze for features
                    analyze_message(data)

                    # Log key messages
                    if msg_type in ["agent_activity", "message"]:
                        logger.info(f"  📨 {msg_type}: {content[:100]}...")

                    # End conditions
                    if msg_type in ["result", "complete", "error"]:
                        end_time = datetime.now()
                        duration = (end_time - start_time).total_seconds()
                        logger.info(f"\n✅ Workflow complete in {duration:.1f}s")
                        logger.info(f"   Result: {content[:150]}")
                        break

                except asyncio.TimeoutError:
                    logger.error("⏱️ Timeout waiting for response (10 minutes)")
                    break
                except Exception as e:
                    logger.error(f"❌ Error receiving message: {e}")
                    break

            return responses

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return []


async def test_extend_app():
    """
    Test 2: Extend existing app.
    Should reuse Learning patterns from Test 1.
    """
    logger.info("\n" + "="*70)
    logger.info("🧪 TEST 2: Extend Existing App (Learning Reuse)")
    logger.info("="*70)

    # Reset feature tracking for learning reuse
    learning_before = dict(features_used["phase2_intelligence"]["learning_system"])

    try:
        async with websockets.connect(WS_URL) as websocket:
            logger.info(f"🔌 Connected to {WS_URL}")

            # Initialize with SAME workspace
            await websocket.send(json.dumps({
                "type": "init",
                "workspace_path": str(WORKSPACE)
            }))

            init_response = json.loads(await websocket.recv())
            logger.info(f"✅ Session initialized: {init_response.get('session_id')}")

            # Send extension query
            query = "Add user authentication to the task manager app"
            logger.info(f"📤 Sending query: '{query}'")

            await websocket.send(json.dumps({
                "type": "message",
                "content": query
            }))

            # Collect responses
            responses = []
            start_time = datetime.now()

            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=600)
                    data = json.loads(message)
                    responses.append(data)

                    analyze_message(data)

                    msg_type = data.get("type")
                    content = str(data.get("content", ""))

                    if msg_type in ["agent_activity", "message"]:
                        logger.info(f"  📨 {msg_type}: {content[:100]}...")

                    if msg_type in ["result", "complete", "error"]:
                        end_time = datetime.now()
                        duration = (end_time - start_time).total_seconds()
                        logger.info(f"\n✅ Extension complete in {duration:.1f}s")
                        break

                except asyncio.TimeoutError:
                    logger.error("⏱️ Timeout")
                    break
                except Exception as e:
                    logger.error(f"❌ Error: {e}")
                    break

            # Check learning reuse
            learning_after = features_used["phase2_intelligence"]["learning_system"]
            evidence_count = len(learning_after["evidence"])

            logger.info(f"\n📚 Learning System Evidence: {evidence_count} instances")

            return responses

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return []


def generate_report():
    """Generate comprehensive feature usage report."""
    logger.info("\n" + "="*70)
    logger.info("📊 COMPREHENSIVE FEATURE USAGE REPORT")
    logger.info("="*70)

    phase_names = {
        "phase1_production_essentials": "Phase 1: Production Essentials",
        "phase2_intelligence": "Phase 2: Intelligence Systems",
        "phase3_workflow_optimization": "Phase 3: Workflow Optimization",
        "phase4_advanced": "Phase 4: Advanced Features",
    }

    total_features = 0
    used_features = 0

    for phase, features in features_used.items():
        phase_name = phase_names.get(phase, phase)
        logger.info(f"\n{phase_name}:")

        phase_total = len(features)
        phase_used = sum(1 for f in features.values() if f["used"])

        for feature_name, feature_data in features.items():
            status = "✅ USED" if feature_data["used"] else "❌ NOT USED"
            readable_name = feature_name.replace("_", " ").title()

            evidence_count = len(feature_data["evidence"])
            logger.info(f"  {status}: {readable_name} ({evidence_count} instances)")

            if evidence_count > 0 and feature_data["used"]:
                for i, evidence in enumerate(feature_data["evidence"][:3], 1):
                    logger.info(f"      {i}. {evidence}")
                if evidence_count > 3:
                    logger.info(f"      ... and {evidence_count - 3} more")

        total_features += phase_total
        used_features += phase_used

        phase_coverage = (phase_used / phase_total * 100) if phase_total > 0 else 0
        logger.info(f"  Coverage: {phase_used}/{phase_total} ({phase_coverage:.1f}%)")

    # Overall metrics
    overall_coverage = (used_features / total_features * 100) if total_features > 0 else 0

    logger.info(f"\n{'='*70}")
    logger.info(f"📈 OVERALL COVERAGE: {used_features}/{total_features} ({overall_coverage:.1f}%)")
    logger.info(f"{'='*70}")

    # Determine result
    if overall_coverage >= 90:
        result = "🌟 EXCELLENT - All features working!"
    elif overall_coverage >= 70:
        result = "✅ GOOD - Most features validated"
    elif overall_coverage >= 50:
        result = "⚠️ ACCEPTABLE - Some features need investigation"
    else:
        result = "❌ POOR - Many features not detected"

    logger.info(f"\n{result}\n")

    # Check files created
    logger.info("📂 FILES CREATED:")
    if WORKSPACE.exists():
        files = list(WORKSPACE.rglob("*"))
        py_files = [f for f in files if f.suffix == ".py"]
        ts_files = [f for f in files if f.suffix in [".ts", ".tsx"]]
        js_files = [f for f in files if f.suffix in [".js", ".jsx"]]
        config_files = [f for f in files if f.name in ["package.json", "tsconfig.json", ".eslintrc.json"]]

        logger.info(f"  Python files: {len(py_files)}")
        logger.info(f"  TypeScript files: {len(ts_files)}")
        logger.info(f"  JavaScript files: {len(js_files)}")
        logger.info(f"  Config files: {len(config_files)}")

        logger.info("\n  File tree:")
        for file in sorted(files)[:20]:
            if file.is_file():
                logger.info(f"    ✓ {file.relative_to(WORKSPACE)}")

        if len(files) > 20:
            logger.info(f"    ... and {len(files) - 20} more files")
    else:
        logger.warning("  ⚠️ No files created!")

    return overall_coverage


async def main():
    """Run all E2E tests."""
    logger.info("🚀 Starting Comprehensive E2E Tests for v6.2")
    logger.info(f"Workspace: {WORKSPACE}")
    logger.info(f"WebSocket: {WS_URL}\n")

    # Test 1: Create new app
    await test_create_app()

    # Small delay between tests
    await asyncio.sleep(2)

    # Test 2: Extend app
    await test_extend_app()

    # Generate report
    coverage = generate_report()

    # Save results
    results_file = Path(__file__).parent / f"e2e_results_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(results_file, "w") as f:
        json.dump(features_used, f, indent=2)

    logger.info(f"\n💾 Results saved to: {results_file}")

    # Exit code based on coverage
    if coverage >= 70:
        logger.info("✅ TESTS PASSED")
        sys.exit(0)
    else:
        logger.error("❌ TESTS FAILED - Coverage too low")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Tests interrupted by user")
        generate_report()
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n❌ Tests failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
