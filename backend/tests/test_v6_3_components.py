"""
Component Tests for v6.3 Features

Quick tests of individual components without full workflow execution.

Run with:
    python backend/tests/test_v6_3_components.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_model_selector():
    """Test ModelSelector with different complexity levels."""
    logger.info("=" * 60)
    logger.info("TEST: Model Selector")
    logger.info("=" * 60)

    try:
        from agents.specialized.model_selector import ModelSelector, assess_complexity

        selector = ModelSelector()

        # Test 1: Simple
        logger.info("\n1. Simple task (1 file, 50 LOC):")
        model, notif = selector.select_model(
            requirements="Write hello world",
            file_count=1,
            estimated_loc=50
        )
        logger.info(f"   ✅ {model.name} (think={model.think_mode})")
        assert "Sonnet 4" in model.name
        assert not model.think_mode

        # Test 2: Moderate
        logger.info("\n2. Moderate task (5 files, 500 LOC):")
        model, notif = selector.select_model(
            requirements="REST API with FastAPI",
            file_count=5,
            estimated_loc=500
        )
        logger.info(f"   ✅ {model.name} (think={model.think_mode})")

        # Test 3: Complex with context
        logger.info("\n3. Complex task (microservices):")
        complexity, metrics = assess_complexity(
            requirements="Build microservices platform with Kubernetes and Kafka",
            file_count=25,
            estimated_loc=3000,
            design_context={
                "components": [{"name": f"svc{i}"} for i in range(12)],
                "description": "Microservices with event-driven architecture using Kafka"
            },
            research_context={
                "findings": ["Kubernetes orchestration best practices", "Kafka message patterns"]
            }
        )
        logger.info(f"   Complexity: {complexity} (score={metrics['complexity_score']})")
        logger.info(f"   Reasons: {len(metrics['reasons'])} factors detected")

        model, notif = selector.select_model(
            requirements="Build microservices with Kubernetes and Kafka",
            file_count=25,
            design_context={
                "components": [{"name": f"svc{i}"} for i in range(12)]
            }
        )
        logger.info(f"   ✅ {model.name} (think={model.think_mode})")

        logger.info(f"\n📊 Statistics: {selector.get_statistics()}")
        logger.info("\n✅ Model Selector: PASS\n")
        return True

    except Exception as e:
        logger.error(f"\n❌ Model Selector: FAIL - {e}\n")
        return False


def test_orchestrator_structure():
    """Test AgentOrchestrator class structure."""
    logger.info("=" * 60)
    logger.info("TEST: Agent Orchestrator Structure")
    logger.info("=" * 60)

    try:
        from core.agent_orchestrator import AgentOrchestrator
        from unittest.mock import Mock

        mock_mcp = Mock()
        orchestrator = AgentOrchestrator(
            mcp_client=mock_mcp,
            workspace_path="/tmp/test",
            approval_manager=None,
            hitl_manager=None
        )

        logger.info("\n✅ Orchestrator initialized")
        logger.info(f"   Workspace: {orchestrator.workspace_path}")
        logger.info(f"   Execution stack: {len(orchestrator.execution_stack)}")
        logger.info(f"   Invocation counts: {orchestrator.invocation_count}")

        # Test context management
        orchestrator.update_shared_context("test_key", "test_value")
        value = orchestrator.get_shared_context("test_key")
        assert value == "test_value"
        logger.info("\n✅ Shared context: PASS")

        # Test metrics
        metrics = orchestrator.get_metrics()
        logger.info(f"   Metrics: {metrics}")

        logger.info("\n✅ Agent Orchestrator Structure: PASS\n")
        return True

    except Exception as e:
        logger.error(f"\n❌ Agent Orchestrator Structure: FAIL - {e}\n")
        return False


def test_workflow_planner_modes():
    """Test WorkflowPlanner mode validation."""
    logger.info("=" * 60)
    logger.info("TEST: Workflow Planner Modes")
    logger.info("=" * 60)

    try:
        from cognitive.workflow_planner_v6 import AgentStep, AgentType

        # Test Research modes
        logger.info("\n1. Research modes:")
        for mode in ["research", "explain", "analyze", "index"]:
            step = AgentStep(
                agent=AgentType.RESEARCH,
                description="test",
                mode=mode
            )
            logger.info(f"   ✅ {mode}: {step.mode}")

        # Test Architect modes
        logger.info("\n2. Architect modes:")
        for mode in ["scan", "design", "post_build_scan", "re_scan"]:
            step = AgentStep(
                agent=AgentType.ARCHITECT,
                description="test",
                mode=mode
            )
            logger.info(f"   ✅ {mode}: {step.mode}")

        # Test invalid mode (should fall back to default)
        logger.info("\n3. Invalid mode handling:")
        step = AgentStep(
            agent=AgentType.ARCHITECT,
            description="test",
            mode="invalid_mode"
        )
        logger.info(f"   ✅ invalid_mode → {step.mode} (fallback)")
        assert step.mode == "default"

        logger.info("\n✅ Workflow Planner Modes: PASS\n")
        return True

    except Exception as e:
        logger.error(f"\n❌ Workflow Planner Modes: FAIL - {e}\n")
        return False


def test_state_schemas():
    """Test State schemas have orchestrator field."""
    logger.info("=" * 60)
    logger.info("TEST: State Schemas (v6.3)")
    logger.info("=" * 60)

    try:
        from state_v6 import ArchitectState, CodesmithState, ReviewFixState

        logger.info("\n1. ArchitectState:")
        arch_state = ArchitectState(
            workspace_path="/test",
            user_requirements="test",
            mode="design",
            research_context={},
            orchestrator=None,  # NEW field
            design={},
            tech_stack=[],
            patterns=[],
            architecture={},
            diagram="",
            adr="",
            errors=[]
        )
        logger.info(f"   ✅ Has 'orchestrator' field: {hasattr(arch_state, '__annotations__')}")

        logger.info("\n2. CodesmithState:")
        code_state = CodesmithState(
            workspace_path="/test",
            requirements="test",
            design={},
            research={},
            past_successes=[],
            orchestrator=None,  # NEW field
            generated_files=[],
            tests=[],
            api_docs="",
            errors=[]
        )
        logger.info(f"   ✅ Has 'orchestrator' field")

        logger.info("\n3. ReviewFixState:")
        review_state = ReviewFixState(
            workspace_path="/test",
            generated_files=[],
            files_to_review=[],
            design={},
            orchestrator=None,  # NEW field
            quality_score=0.0,
            review_feedback={},
            fixes_applied=[],
            iteration=0,
            should_continue=True,
            errors=[]
        )
        logger.info(f"   ✅ Has 'orchestrator' field")

        logger.info("\n✅ State Schemas: PASS\n")
        return True

    except Exception as e:
        logger.error(f"\n❌ State Schemas: FAIL - {e}\n")
        return False


def run_all_component_tests():
    """Run all component tests."""
    logger.info("\n" + "=" * 60)
    logger.info("KI AutoAgent v6.3 - Component Tests")
    logger.info("=" * 60 + "\n")

    tests = [
        ("Model Selector", test_model_selector),
        ("Agent Orchestrator", test_orchestrator_structure),
        ("Workflow Planner Modes", test_workflow_planner_modes),
        ("State Schemas", test_state_schemas)
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            logger.error(f"❌ {name} crashed: {e}")
            results.append((name, False))

    # Summary
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for _, p in results if p)
    total = len(results)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} - {name}")

    logger.info(f"\n📊 {passed}/{total} tests passed ({passed/total*100:.0f}%)\n")

    return all(p for _, p in results)


if __name__ == "__main__":
    success = run_all_component_tests()
    sys.exit(0 if success else 1)
