"""
Direct Anthropic SDK Integration - LangChain Compatible

This module provides a LangChain-compatible ChatAnthropic replacement
that uses the Anthropic SDK directly, bypassing the broken langchain-anthropic package.

Workaround for: ImportError: cannot import 'is_data_content_block' from 'langchain_core.messages'

Author: KI AutoAgent Team
Python: 3.13+
"""

from __future__ import annotations

import os
from typing import Any, AsyncIterator, Iterator

from anthropic import AsyncAnthropic, Anthropic
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)


class ChatAnthropicDirect:
    """
    Direct Anthropic SDK integration for LangChain.

    This is a drop-in replacement for langchain_anthropic.ChatAnthropic
    that uses the Anthropic SDK directly.

    Does NOT inherit from BaseChatModel to avoid Pydantic issues.
    Implements only the methods needed for LangGraph compatibility.

    Usage:
        from adapters.chat_anthropic_direct import ChatAnthropicDirect

        llm = ChatAnthropicDirect(model="claude-sonnet-4-20250514")
        response = await llm.ainvoke([HumanMessage(content="Hello!")])
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        api_key: str | None = None,
        **kwargs: Any
    ):
        """Initialize with model parameters."""
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        self._client: Anthropic | None = None
        self._async_client: AsyncAnthropic | None = None

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment or parameters")

    def _get_client(self) -> Anthropic:
        """Lazy initialization of sync client."""
        if self._client is None:
            self._client = Anthropic(api_key=self.api_key)
        return self._client

    def _get_async_client(self) -> AsyncAnthropic:
        """Lazy initialization of async client."""
        if self._async_client is None:
            self._async_client = AsyncAnthropic(api_key=self.api_key)
        return self._async_client

    def _format_messages(self, messages: list[BaseMessage]) -> tuple[str | None, list[dict[str, Any]]]:
        """
        Format LangChain messages into Anthropic API format.

        Returns:
            (system_prompt, anthropic_messages)
        """
        system_prompt: str | None = None
        anthropic_messages: list[dict[str, Any]] = []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                # Anthropic uses separate system parameter
                system_prompt = str(msg.content)
            elif isinstance(msg, HumanMessage):
                anthropic_messages.append({
                    "role": "user",
                    "content": str(msg.content)
                })
            elif isinstance(msg, AIMessage):
                anthropic_messages.append({
                    "role": "assistant",
                    "content": str(msg.content)
                })
            else:
                # Fallback for other message types
                anthropic_messages.append({
                    "role": "user",
                    "content": str(msg.content)
                })

        return system_prompt, anthropic_messages

    def invoke(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> AIMessage:
        """Synchronous generation (for LangGraph compatibility)."""
        client = self._get_client()
        system_prompt, anthropic_messages = self._format_messages(messages)

        # Prepare API call parameters
        params = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        if system_prompt:
            params["system"] = system_prompt

        if stop:
            params["stop_sequences"] = stop

        # Call Anthropic API
        response = client.messages.create(**params)

        # Extract text content
        content = ""
        for block in response.content:
            if hasattr(block, 'text'):
                content += block.text

        # Return AIMessage directly (simpler than ChatResult)
        return AIMessage(content=content)

    async def ainvoke(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> AIMessage:
        """Asynchronous generation."""
        client = self._get_async_client()
        system_prompt, anthropic_messages = self._format_messages(messages)

        # Prepare API call parameters
        params = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        if system_prompt:
            params["system"] = system_prompt

        if stop:
            params["stop_sequences"] = stop

        # Call Anthropic API asynchronously
        response = await client.messages.create(**params)

        # Extract text content
        content = ""
        for block in response.content:
            if hasattr(block, 'text'):
                content += block.text

        # Return AIMessage directly (simpler than ChatResult)
        return AIMessage(content=content)


def patch_langchain_anthropic():
    """
    Monkey-patch langchain_anthropic module to use our direct implementation.

    Usage:
        from adapters.chat_anthropic_direct import patch_langchain_anthropic
        patch_langchain_anthropic()

        # Now imports work:
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model="claude-sonnet-4-20250514")
    """
    import sys
    from unittest.mock import Mock

    # Create mock module
    mock_anthropic = Mock()
    mock_anthropic.ChatAnthropic = ChatAnthropicDirect
    mock_anthropic.ChatAnthropicMessages = ChatAnthropicDirect

    # Replace in sys.modules
    sys.modules['langchain_anthropic'] = mock_anthropic

    print("✅ langchain_anthropic patched with direct Anthropic SDK")
    print("   ChatAnthropic now uses anthropic.AsyncAnthropic directly")
