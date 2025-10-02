"""
Test Multi-Agent Workflow for Tetris App Development

This script tests the complete workflow:
Orchestrator → Architect → CodeSmith → Reviewer → Fixer

Usage:
    python test_multi_agent_workflow.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from langgraph_system.workflow import create_agent_workflow
from agents.specialized.orchestrator_agent import OrchestratorAgent
from agents.specialized.architect_agent import ArchitectAgent
from agents.specialized.codesmith_agent import CodeSmithAgent
from agents.specialized.reviewer_gpt_agent import ReviewerGPTAgent
from agents.specialized.fixerbot_agent import FixerBotAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


async def test_tetris_workflow():
    """
    Test complete multi-agent workflow for Tetris app development
    """
    logger.info("=" * 80)
    logger.info("🚀 TESTING MULTI-AGENT WORKFLOW: Tetris App Development")
    logger.info("=" * 80)

    # Create workflow
    logger.info("\n📊 Creating workflow...")
    workflow = create_agent_workflow()

    # Execute workflow
    task = "Entwickle eine Tetris Webapplikation mit HTML5 Canvas"
    logger.info(f"\n▶️  Executing task: {task}")
    logger.info("")

    try:
        final_state = await workflow.execute(
            task=task,
            session_id="test_tetris_workflow",
            workspace_path="/tmp/tetris_app"
        )

        # Final summary
        logger.info("\n" + "=" * 80)
        logger.info("📊 WORKFLOW COMPLETED - FINAL SUMMARY")
        logger.info("=" * 80)

        # Show messages
        messages = final_state.get("messages", [])
        logger.info(f"\n📨 Messages: {len(messages)}")
        for msg in messages[-3:]:  # Show last 3 messages
            role = msg.get("role", "unknown")
            content = str(msg.get("content", ""))[:150]
            logger.info(f"  [{role}] {content}...")

        # Show execution steps
        execution_steps = final_state.get("execution_steps", [])
        logger.info(f"\n📋 Execution Steps: {len(execution_steps)}")
        for step in execution_steps:
            agent = step.get("agent", "unknown")
            status = step.get("status", "unknown")
            logger.info(f"  • {agent}: {status}")

        # Check success
        if final_state.get("status") == "completed":
            logger.info("\n✅ Workflow completed successfully!")
            return True
        else:
            logger.error(f"\n❌ Workflow ended with status: {final_state.get('status')}")
            return False

    except Exception as e:
        logger.error(f"\n❌ Workflow failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_simple_orchestration():
    """
    Test simple orchestration - just check if Orchestrator creates multi-step plan
    """
    logger.info("=" * 80)
    logger.info("🧪 TEST 1: Orchestrator Multi-Step Plan Detection")
    logger.info("=" * 80)

    orchestrator = OrchestratorAgent()

    from agents.base.base_agent import TaskRequest

    request = TaskRequest(
        prompt="Entwickle eine Tetris Webapplikation mit HTML5 Canvas",
        context={}
    )

    logger.info(f"\n📨 Sending request: {request.prompt}")

    result = await orchestrator.execute(request)

    logger.info(f"\n📊 Result Status: {result.status}")
    logger.info(f"📄 Content Preview: {result.content[:200]}...")

    metadata = result.metadata or {}
    if "steps" in metadata:
        steps = metadata["steps"]
        logger.info(f"\n✅ Multi-step plan created with {len(steps)} steps:")
        for step in steps:
            logger.info(f"  • {step.get('agent', 'unknown')}: {step.get('task', 'N/A')[:60]}...")
    else:
        logger.warning("\n⚠️  No steps found in metadata - single-step response")

    logger.info("")
    return result.status == "success"


async def main():
    """
    Run all tests
    """
    logger.info("🔬 Multi-Agent Workflow Test Suite\n")

    # Test 1: Simple orchestration
    test1_passed = await test_simple_orchestration()

    # Wait a bit
    await asyncio.sleep(2)

    # Test 2: Full workflow (commented out for now - requires backend to be running)
    # test2_passed = await test_tetris_workflow()

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Test 1 (Orchestrator): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    # logger.info(f"Test 2 (Full Workflow): {'✅ PASSED' if test2_passed else '❌ FAILED'}")


if __name__ == "__main__":
    asyncio.run(main())
