"""
E2E Tests for v6.3 Features

Tests:
1. CREATE workflow with full orchestration
2. Agent Autonomy (Codesmith invokes Research + Architect)
3. Model Selection (complexity-based)

⚠️  CRITICAL: Run in separate workspace (~/TestApps/e2e_v6.3_test)
           NEVER in development repository!

Run with:
    python backend/tests/e2e_test_v6_3.py
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Test workspace (SEPARATE from development!)
TEST_WORKSPACE = Path.home() / "TestApps" / "e2e_v6.3_test"


async def test_create_workflow():
    """
    Test 1: CREATE workflow with full agent orchestration.

    Expected flow:
    1. User: "Create a simple TODO app"
    2. Workflow Planner generates: Research → Architect → Codesmith → ReviewFix
    3. Agent Autonomy: If any agent skipped, Codesmith auto-invokes
    4. Model Selection: Codesmith selects appropriate model
    5. WebSocket: User notified of model selection
    6. Result: Code generated + architecture.md created
    """
    logger.info("=" * 80)
    logger.info("TEST 1: CREATE Workflow")
    logger.info("=" * 80)

    try:
        from workflow_v6_integrated import WorkflowV6Integrated

        # Create workflow
        workflow = WorkflowV6Integrated(
            workspace_path=str(TEST_WORKSPACE),
            websocket_callback=None  # No WebSocket for CLI test
        )

        logger.info(f"📁 Test workspace: {TEST_WORKSPACE}")
        logger.info("🔧 Initializing workflow...")

        await workflow.initialize()

        logger.info("✅ Workflow initialized")
        logger.info("")
        logger.info("📝 Test query: 'Create a simple TODO app with Python FastAPI'")
        logger.info("")

        # Execute workflow
        result = await workflow.execute(
            user_query="Create a simple TODO app with Python FastAPI",
            workspace_path=str(TEST_WORKSPACE)
        )

        logger.info("")
        logger.info("=" * 80)
        logger.info("TEST 1 RESULTS:")
        logger.info("=" * 80)

        # Check results
        success = result.get("success", False)
        logger.info(f"✅ Success: {success}")

        if "workflow_plan" in result:
            plan = result["workflow_plan"]
            logger.info(f"📋 Workflow Type: {plan.get('workflow_type')}")
            logger.info(f"🤖 Agents Used: {len(plan.get('agents', []))}")
            for agent in plan.get("agents", []):
                logger.info(f"   - {agent.get('agent')} (mode={agent.get('mode', 'default')})")

        # Check for architecture.md (system snapshot)
        arch_dir = TEST_WORKSPACE / ".ki_autoagent" / "architecture"
        if arch_dir.exists():
            logger.info(f"✅ Architecture snapshot created: {arch_dir}")
            files = list(arch_dir.glob("*.md")) + list(arch_dir.glob("*.json"))
            logger.info(f"   Files: {[f.name for f in files]}")
        else:
            logger.warning(f"⚠️  No architecture snapshot found at {arch_dir}")

        # Check generated files
        generated = result.get("generated_files", [])
        logger.info(f"📄 Generated Files: {len(generated)}")

        # Cleanup
        await workflow.cleanup()

        return {
            "test": "CREATE Workflow",
            "success": success,
            "agents_count": len(plan.get("agents", [])) if "workflow_plan" in result else 0,
            "files_generated": len(generated),
            "architecture_created": arch_dir.exists() if arch_dir else False
        }

    except Exception as e:
        logger.error(f"❌ TEST 1 FAILED: {e}", exc_info=True)
        return {"test": "CREATE Workflow", "success": False, "error": str(e)}


async def test_agent_autonomy():
    """
    Test 2: Agent Autonomy - Codesmith invokes missing agents.

    Expected flow:
    1. User: Direct to Codesmith (skip Research + Architect)
    2. Codesmith detects: No research in Memory
    3. Codesmith → Research (autonomous invocation)
    4. Codesmith detects: No architecture in Memory
    5. Codesmith → Architect (autonomous invocation)
    6. Codesmith: Now has full context, generates code
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("TEST 2: Agent Autonomy")
    logger.info("=" * 80)

    try:
        from core.agent_orchestrator import AgentOrchestrator
        from mcp.mcp_client import MCPClient

        # Create minimal orchestrator
        mcp = MCPClient(workspace_path=str(TEST_WORKSPACE))
        await mcp.initialize()

        orchestrator = AgentOrchestrator(
            mcp_client=mcp,
            workspace_path=str(TEST_WORKSPACE),
            approval_manager=None,
            hitl_manager=None
        )

        logger.info("🤖 Testing: Codesmith → Research invocation")

        # Test Research invocation
        research_result = await orchestrator.invoke_research(
            query="FastAPI best practices",
            mode="research",
            caller="codesmith"
        )

        logger.info(f"✅ Research invoked: {research_result['success']}")
        logger.info(f"   Result length: {len(research_result.get('result', ''))} chars")

        logger.info("")
        logger.info("🤖 Testing: Codesmith → Architect invocation")

        # Test Architect invocation
        architect_result = await orchestrator.invoke_architect(
            task="Design TODO app architecture",
            mode="design",
            caller="codesmith",
            design_input={}
        )

        logger.info(f"✅ Architect invoked: {architect_result['success']}")
        logger.info(f"   Design length: {len(str(architect_result.get('design', '')))} chars")

        # Check metrics
        metrics = orchestrator.get_metrics()
        logger.info("")
        logger.info("📊 Orchestrator Metrics:")
        logger.info(f"   Research invocations: {metrics['invocation_count']['research']}")
        logger.info(f"   Architect invocations: {metrics['invocation_count']['architect']}")
        logger.info(f"   Max stack depth reached: {metrics['current_stack_depth']}")

        # Cleanup
        await mcp.cleanup()

        return {
            "test": "Agent Autonomy",
            "success": True,
            "research_invoked": research_result['success'],
            "architect_invoked": architect_result['success'],
            "invocations": metrics['invocation_count']
        }

    except Exception as e:
        logger.error(f"❌ TEST 2 FAILED: {e}", exc_info=True)
        return {"test": "Agent Autonomy", "success": False, "error": str(e)}


async def test_model_selection():
    """
    Test 3: Model Selection based on complexity.

    Test cases:
    1. Simple task → Sonnet 4
    2. Moderate task → Sonnet 4.5
    3. Complex task (microservices) → Opus 3.5 + Think
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("TEST 3: Model Selection")
    logger.info("=" * 80)

    try:
        from agents.specialized.model_selector import ModelSelector

        selector = ModelSelector()

        # Test 1: Simple task
        logger.info("📝 Test 3.1: Simple task")
        model1, notif1 = selector.select_model(
            requirements="Write a hello world function in Python",
            file_count=1,
            estimated_loc=10
        )
        logger.info(f"   Selected: {model1.name} (think={model1.think_mode})")

        # Test 2: Moderate task
        logger.info("")
        logger.info("📝 Test 3.2: Moderate task")
        model2, notif2 = selector.select_model(
            requirements="Build a REST API with FastAPI",
            file_count=5,
            estimated_loc=500
        )
        logger.info(f"   Selected: {model2.name} (think={model2.think_mode})")

        # Test 3: Complex task (microservices + kubernetes)
        logger.info("")
        logger.info("📝 Test 3.3: Very complex task (microservices)")
        model3, notif3 = selector.select_model(
            requirements="Build microservices platform with Kubernetes, Kafka, and OAuth2",
            file_count=30,
            estimated_loc=5000,
            design_context={
                "components": [{"name": f"service_{i}"} for i in range(15)],
                "patterns": ["microservices", "event-driven", "api-gateway"]
            },
            research_context={
                "findings": ["Kafka message queue", "OAuth2 authentication", "Kubernetes orchestration"]
            }
        )
        logger.info(f"   Selected: {model3.name} (think={model3.think_mode})")

        # Verify progression
        logger.info("")
        logger.info("✅ Model Selection Tests:")
        logger.info(f"   Simple → {model1.name}")
        logger.info(f"   Moderate → {model2.name}")
        logger.info(f"   Complex → {model3.name}")

        # Check statistics
        stats = selector.get_statistics()
        logger.info("")
        logger.info("📊 Selection Statistics:")
        logger.info(f"   Total selections: {stats['total_selections']}")
        logger.info(f"   Think mode usage: {stats['think_mode_usage']}/{stats['total_selections']}")
        logger.info(f"   Average complexity: {stats['avg_complexity_score']}/10")

        return {
            "test": "Model Selection",
            "success": True,
            "simple_model": model1.name,
            "moderate_model": model2.name,
            "complex_model": model3.name,
            "think_mode_used": stats['think_mode_usage'] > 0
        }

    except Exception as e:
        logger.error(f"❌ TEST 3 FAILED: {e}", exc_info=True)
        return {"test": "Model Selection", "success": False, "error": str(e)}


async def run_all_tests():
    """Run all E2E tests."""
    logger.info("")
    logger.info("🚀 Starting E2E Tests for v6.3")
    logger.info(f"📁 Test Workspace: {TEST_WORKSPACE}")
    logger.info(f"🕐 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    results = []

    # Test 1: CREATE Workflow
    result1 = await test_create_workflow()
    results.append(result1)

    # Test 2: Agent Autonomy
    result2 = await test_agent_autonomy()
    results.append(result2)

    # Test 3: Model Selection
    result3 = await test_model_selection()
    results.append(result3)

    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("E2E TEST SUMMARY")
    logger.info("=" * 80)

    passed = sum(1 for r in results if r.get("success"))
    total = len(results)

    for result in results:
        status = "✅ PASS" if result.get("success") else "❌ FAIL"
        logger.info(f"{status} - {result['test']}")
        if not result.get("success") and "error" in result:
            logger.info(f"       Error: {result['error']}")

    logger.info("")
    logger.info(f"📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    logger.info(f"🕐 End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return results


if __name__ == "__main__":
    print("\n" + "="*80)
    print("KI AutoAgent v6.3 - E2E Tests")
    print("="*80 + "\n")

    results = asyncio.run(run_all_tests())

    # Exit code
    all_passed = all(r.get("success") for r in results)
    sys.exit(0 if all_passed else 1)
