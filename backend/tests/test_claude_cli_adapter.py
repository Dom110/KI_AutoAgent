"""
Test Claude CLI Adapter

Tests the ClaudeCLI wrapper to ensure it works as a LangChain-compatible
drop-in replacement for ChatAnthropic.

Author: KI AutoAgent Team
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_core.messages import HumanMessage, SystemMessage
from adapters.claude_cli_simple import ClaudeCLISimple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_basic_invocation():
    """Test basic Claude CLI invocation."""
    logger.info("=" * 70)
    logger.info("TEST 1: Basic Invocation")
    logger.info("=" * 70)

    try:
        # Create Claude CLI instance
        llm = ClaudeCLISimple(model="claude-sonnet-4-20250514", temperature=0.3)

        logger.info("✅ ClaudeCLI instance created")

        # Test simple query
        logger.info("\n🔄 Testing simple query...")
        response = await llm.ainvoke([
            HumanMessage(content="What is 2+2? Answer with just the number.")
        ])

        logger.info(f"✅ Response: {response.content}")

        # Verify response
        assert response.content.strip() in ["4", "4."], f"Unexpected response: {response.content}"

        logger.info("\n" + "=" * 70)
        logger.info("✅ TEST 1 PASSED")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        raise


async def test_system_message():
    """Test with system message."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: System Message")
    logger.info("=" * 70)

    try:
        llm = ClaudeCLISimple(model="claude-sonnet-4-20250514", temperature=0.3)

        logger.info("🔄 Testing with system message...")
        response = await llm.ainvoke([
            SystemMessage(content="You are a helpful assistant that always responds in uppercase."),
            HumanMessage(content="Say hello")
        ])

        logger.info(f"✅ Response: {response.content}")

        # Verify uppercase (most words should be uppercase)
        uppercase_count = sum(1 for c in response.content if c.isupper())
        assert uppercase_count > 0, "Response should contain uppercase letters"

        logger.info("\n" + "=" * 70)
        logger.info("✅ TEST 2 PASSED")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        raise


async def test_longer_response():
    """Test longer, more complex response."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Longer Response")
    logger.info("=" * 70)

    try:
        llm = ClaudeCLISimple(model="claude-sonnet-4-20250514", temperature=0.3)

        logger.info("🔄 Testing longer response...")
        response = await llm.ainvoke([
            HumanMessage(content="Explain in one sentence what a RESTful API is.")
        ])

        logger.info(f"✅ Response ({len(response.content)} chars): {response.content[:100]}...")

        # Verify we got a response
        assert len(response.content) > 20, "Response too short"
        assert "API" in response.content or "api" in response.content.lower(), "Response should mention API"

        logger.info("\n" + "=" * 70)
        logger.info("✅ TEST 3 PASSED")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        raise


async def test_langchain_compatibility():
    """Test that it works like ChatAnthropic would."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: LangChain Compatibility")
    logger.info("=" * 70)

    try:
        # This tests the same interface as ChatAnthropic
        from langchain_core.messages import AIMessage

        llm = ClaudeCLISimple(model="claude-sonnet-4-20250514", temperature=0.3)

        logger.info("🔄 Testing LangChain message interface...")
        messages = [
            SystemMessage(content="You are a math tutor."),
            HumanMessage(content="What is 5 * 7?"),
        ]

        response = await llm.ainvoke(messages)

        logger.info(f"✅ Response type: {type(response).__name__}")
        logger.info(f"✅ Response content: {response.content}")

        # Verify it's an AIMessage
        assert isinstance(response, AIMessage), "Should return AIMessage"
        assert "35" in response.content, "Should contain correct answer"

        logger.info("\n" + "=" * 70)
        logger.info("✅ TEST 4 PASSED")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        raise


async def main():
    """Run all tests."""
    logger.info("\n" + "=" * 80)
    logger.info("🚀 CLAUDE CLI ADAPTER TESTS")
    logger.info("=" * 80)
    logger.info("\nTesting ClaudeCLI as drop-in replacement for ChatAnthropic")
    logger.info("\n" + "=" * 80 + "\n")

    try:
        # Test 1: Basic invocation
        await test_basic_invocation()

        # Test 2: System message
        await test_system_message()

        # Test 3: Longer response
        await test_longer_response()

        # Test 4: LangChain compatibility
        await test_langchain_compatibility()

        logger.info("\n" + "=" * 80)
        logger.info("🎉 ALL CLAUDE CLI ADAPTER TESTS PASSED!")
        logger.info("=" * 80)
        logger.info("\n✅ ClaudeCLI is ready to use as ChatAnthropic replacement")
        logger.info("✅ All LangChain interfaces working correctly")
        logger.info("\n" + "=" * 80 + "\n")

    except Exception as e:
        logger.error(f"\n❌ Tests failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
