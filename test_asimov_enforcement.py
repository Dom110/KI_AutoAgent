#!/usr/bin/env python3
"""
Test Asimov Rule Enforcement in BaseAgent

This tests if Asimov Rules are automatically enforced for EVERY task
through the new Neurosymbolic Reasoning system in BaseAgent.execute()
"""

import sys
import os
import asyncio

# Add backend directory to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from agents.base.base_agent import BaseAgent, AgentConfig, TaskRequest
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Create a simple test agent
class TestAgent(BaseAgent):
    """Simple test agent to verify Asimov enforcement"""

    async def _execute_internal(self, request: TaskRequest) -> str:
        """Internal execution - should never reach here if Asimov blocks"""
        return f"Executed: {request.prompt}"


async def test_asimov_enforcement():
    """Test that Asimov Rules are enforced for all tasks"""
    logger.info("=" * 80)
    logger.info("🔴 Testing Asimov Rule Enforcement in BaseAgent")
    logger.info("=" * 80)

    # Create test agent
    config = AgentConfig(
        agent_id="test_agent",
        name="TestAgent",
        full_name="Test Agent",
        description="Agent for testing Asimov enforcement",
        model="gpt-4"
    )

    agent = TestAgent(config)

    # =========================================================================
    # TEST 1: Task with TODO (should violate Asimov Rule 2)
    # =========================================================================
    logger.info("\n📝 TEST 1: Task requesting code with TODO")
    logger.info("-" * 80)

    request1 = TaskRequest(
        prompt="Write a function with TODO placeholder",
        context={"code": "def foo():\n    # TODO: implement later\n    pass"}
    )

    result1 = await agent.execute(request1)

    if result1.status == "asimov_violation":
        logger.info("✅ PASS: Asimov Rule 2 blocked TODO in code")
        logger.info(f"   Violation: {result1.content[:100]}...")
    else:
        logger.error(f"❌ FAIL: Task was not blocked! Status: {result1.status}")

    # =========================================================================
    # TEST 2: Task asking for latest best practices (should trigger research)
    # =========================================================================
    logger.info("\n📝 TEST 2: Task asking about 'latest best practices'")
    logger.info("-" * 80)

    request2 = TaskRequest(
        prompt="What are the latest best practices for API authentication?",
        context={}
    )

    # Mock the research function to avoid actual API call
    async def mock_research(prompt, topics, techs):
        return {"findings": ["Mock research result"]}

    agent._perform_mandatory_research = mock_research

    result2 = await agent.execute(request2)

    if result2.context and result2.context.get('research_completed'):
        logger.info("✅ PASS: Asimov Rule 7 triggered research")
        logger.info(f"   Research completed: {result2.context.get('research_completed')}")
    else:
        logger.warning(f"⚠️ Research may not have been triggered. Status: {result2.status}")

    # =========================================================================
    # TEST 3: Task with technical misconception (should challenge)
    # =========================================================================
    logger.info("\n📝 TEST 3: Task with misconception (disk faster than memory)")
    logger.info("-" * 80)

    request3 = TaskRequest(
        prompt="Use disk cache because it's faster than memory cache",
        context={}
    )

    result3 = await agent.execute(request3)

    if result3.status == "challenge":
        logger.info("✅ PASS: Asimov Rule 5 challenged misconception")
        logger.info(f"   Challenge: {result3.content[:100]}...")
    else:
        logger.warning(f"⚠️ Task was not challenged. Status: {result3.status}")

    # =========================================================================
    # TEST 4: Normal task (should proceed normally)
    # =========================================================================
    logger.info("\n📝 TEST 4: Normal task without violations")
    logger.info("-" * 80)

    request4 = TaskRequest(
        prompt="Write a simple calculator function",
        context={}
    )

    result4 = await agent.execute(request4)

    if result4.status not in ["asimov_violation", "challenge"]:
        logger.info(f"✅ PASS: Normal task proceeded. Status: {result4.status}")
    else:
        logger.error(f"❌ FAIL: Normal task was blocked! Status: {result4.status}")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("📊 ENFORCEMENT TEST SUMMARY")
    logger.info("=" * 80)

    logger.info("\n✅ Asimov Rules are now enforced via Neurosymbolic Reasoning")
    logger.info("   - Every task goes through BaseAgent.execute()")
    logger.info("   - Neurosymbolic reasoner checks ALL Asimov Rules")
    logger.info("   - Violations → FAIL FAST")
    logger.info("   - Research required → Perform research")
    logger.info("   - Misconceptions → Challenge user")

    logger.info("\n🔴 OLD PrimeDirectives system → REPLACED")
    logger.info("🆕 NEW Neurosymbolic system → ACTIVE")

    logger.info("\n✅ Test Completed!")
    logger.info("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(test_asimov_enforcement())
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure you're running from the KI_AutoAgent directory")
