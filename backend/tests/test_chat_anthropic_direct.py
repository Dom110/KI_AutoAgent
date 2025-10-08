"""
Tests for Direct Anthropic SDK Integration

Tests the ChatAnthropicDirect adapter that bypasses broken langchain-anthropic.

Author: KI AutoAgent Team
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

import pytest

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

# Patch BEFORE any langchain_anthropic imports
from adapters.chat_anthropic_direct import patch_langchain_anthropic, ChatAnthropicDirect
patch_langchain_anthropic()

# Now safe to import
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_direct_class_basic():
    """Test ChatAnthropicDirect class directly."""
    logger.info("Testing ChatAnthropicDirect basic functionality...")

    llm = ChatAnthropicDirect(
        model="claude-sonnet-4-20250514",
        temperature=0.3,
        max_tokens=100
    )

    # Simple test
    messages = [HumanMessage(content="What is 2+2? Answer with just the number.")]

    logger.info("Calling Anthropic API...")
    response = await llm.ainvoke(messages)

    logger.info(f"Response: {response.content}")

    assert response is not None
    assert isinstance(response, AIMessage)
    assert "4" in response.content

    logger.info("✅ Direct class test passed")


@pytest.mark.asyncio
async def test_patched_import():
    """Test that patched ChatAnthropic works."""
    logger.info("Testing patched langchain_anthropic import...")

    # This should now use our ChatAnthropicDirect
    llm = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        temperature=0.3,
        max_tokens=100
    )

    # Verify it's our class
    assert isinstance(llm, ChatAnthropicDirect)
    logger.info(f"✅ Patched import returns: {type(llm).__name__}")

    # Test it works
    messages = [HumanMessage(content="Say 'hello' in one word.")]

    logger.info("Calling via patched import...")
    response = await llm.ainvoke(messages)

    logger.info(f"Response: {response.content}")

    assert response is not None
    assert isinstance(response, AIMessage)

    logger.info("✅ Patched import test passed")


@pytest.mark.asyncio
async def test_system_message():
    """Test system message handling."""
    logger.info("Testing system message handling...")

    llm = ChatAnthropicDirect(
        model="claude-sonnet-4-20250514",
        temperature=0.3,
        max_tokens=100
    )

    messages = [
        SystemMessage(content="You are a helpful math tutor. Be concise."),
        HumanMessage(content="What is 5*5?")
    ]

    logger.info("Calling with system message...")
    response = await llm.ainvoke(messages)

    logger.info(f"Response: {response.content}")

    assert response is not None
    assert "25" in response.content

    logger.info("✅ System message test passed")


@pytest.mark.asyncio
async def test_sync_invoke():
    """Test synchronous invoke (for LangGraph compatibility)."""
    logger.info("Testing synchronous invoke...")

    llm = ChatAnthropicDirect(
        model="claude-sonnet-4-20250514",
        temperature=0.3,
        max_tokens=100
    )

    messages = [HumanMessage(content="What is 3+3? Just the number.")]

    logger.info("Calling sync invoke...")
    # This is sync, not async
    response = llm.invoke(messages)

    logger.info(f"Response: {response.content}")

    assert response is not None
    assert isinstance(response, AIMessage)
    assert "6" in response.content

    logger.info("✅ Sync invoke test passed")


@pytest.mark.asyncio
async def test_temperature_parameter():
    """Test that temperature parameter is respected."""
    logger.info("Testing temperature parameter...")

    # Low temperature for deterministic response
    llm = ChatAnthropicDirect(
        model="claude-sonnet-4-20250514",
        temperature=0.1,
        max_tokens=50
    )

    messages = [HumanMessage(content="What is the capital of France? One word only.")]

    logger.info("Calling with low temperature...")
    response = await llm.ainvoke(messages)

    logger.info(f"Response: {response.content}")

    assert response is not None
    assert "Paris" in response.content or "paris" in response.content.lower()

    logger.info("✅ Temperature parameter test passed")


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_direct_class_basic())
    asyncio.run(test_patched_import())
    asyncio.run(test_system_message())
    asyncio.run(test_sync_invoke())
    asyncio.run(test_temperature_parameter())
