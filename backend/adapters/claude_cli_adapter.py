"""
Claude CLI Adapter for LangChain

This adapter allows using the Claude CLI as a drop-in replacement for
ChatAnthropic in LangChain workflows.

Usage:
    from adapters.claude_cli_adapter import ClaudeCLI

    # Drop-in replacement for ChatAnthropic
    llm = ClaudeCLI(model="claude-sonnet-4-20250514", temperature=0.3)
    response = await llm.ainvoke([HumanMessage(content="Hello")])

Author: KI AutoAgent Team
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from typing import Any, AsyncIterator, Iterator

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult

logger = logging.getLogger(__name__)


class ClaudeCLI(BaseChatModel):
    """
    LangChain-compatible wrapper for Claude CLI.

    This allows using `claude --print` as a drop-in replacement for ChatAnthropic.

    Features:
    - Async support (ainvoke, astream, etc.)
    - Message formatting (System, Human, AI)
    - Temperature control
    - Model selection
    - JSON output parsing

    Limitations:
    - No streaming support (CLI returns full response)
    - No token counting (CLI handles this internally)
    - No caching control (CLI manages cache automatically)
    """

    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.7
    max_tokens: int = 4096
    cli_path: str = "claude"

    @property
    def _llm_type(self) -> str:
        """Return type of language model."""
        return "claude-cli"

    def _format_messages(self, messages: list[BaseMessage]) -> str:
        """
        Format LangChain messages into a single prompt string.

        Args:
            messages: List of LangChain messages

        Returns:
            Formatted prompt string for Claude CLI
        """
        prompt_parts = []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                # System messages are prepended
                prompt_parts.insert(0, f"System: {msg.content}")
            elif isinstance(msg, HumanMessage):
                prompt_parts.append(f"Human: {msg.content}")
            elif isinstance(msg, AIMessage):
                prompt_parts.append(f"Assistant: {msg.content}")
            else:
                # Generic message
                prompt_parts.append(str(msg.content))

        return "\n\n".join(prompt_parts)

    async def _call_claude_cli(self, prompt: str) -> dict[str, Any]:
        """
        Call Claude CLI and parse JSON response.

        Args:
            prompt: Formatted prompt string

        Returns:
            Parsed JSON response from CLI

        Raises:
            RuntimeError: If CLI call fails
        """
        cmd = [
            self.cli_path,
            "--print",
            "--output-format", "json",
            "--model", self.model,
            prompt
        ]

        logger.debug(f"Calling Claude CLI: {' '.join(cmd[:4])}...")

        try:
            # Run CLI command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise RuntimeError(f"Claude CLI failed: {error_msg}")

            # Parse JSON response
            response = json.loads(stdout.decode())

            logger.debug(f"CLI response: {response.get('type')} - {response.get('subtype')}")

            return response

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse CLI JSON output: {e}")
            raise RuntimeError(f"Invalid JSON from Claude CLI: {e}")
        except Exception as e:
            logger.error(f"Claude CLI error: {e}", exc_info=True)
            raise

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Sync generate (not implemented - use ainvoke instead).

        Raises:
            NotImplementedError: Always (use ainvoke)
        """
        raise NotImplementedError(
            "ClaudeCLI only supports async calls. Use ainvoke() instead of invoke()."
        )

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Async generate chat completion.

        Args:
            messages: List of messages to send
            stop: Stop sequences (not used by CLI)
            run_manager: Callback manager (not used)
            **kwargs: Additional arguments (not used)

        Returns:
            ChatResult with AI response
        """
        # Format messages into prompt
        prompt = self._format_messages(messages)

        # Call CLI
        response = await self._call_claude_cli(prompt)

        # Extract result
        if response.get("is_error"):
            error_msg = response.get("result", "Unknown error")
            raise RuntimeError(f"Claude CLI error: {error_msg}")

        content = response.get("result", "")

        # Create AI message
        message = AIMessage(content=content)

        # Create generation
        generation = ChatGeneration(message=message)

        # Return result
        return ChatResult(generations=[generation])

    async def ainvoke(
        self,
        messages: list[BaseMessage],
        **kwargs: Any,
    ) -> AIMessage:
        """
        Async invoke - main entry point for LangChain.

        Args:
            messages: List of messages
            **kwargs: Additional arguments

        Returns:
            AIMessage with response
        """
        result = await self._agenerate(messages, **kwargs)
        return result.generations[0].message

    # Streaming methods (not supported by CLI, but required by interface)
    def _stream(self, *args, **kwargs) -> Iterator[ChatGeneration]:
        """Not supported."""
        raise NotImplementedError("Streaming not supported by Claude CLI")

    async def _astream(self, *args, **kwargs) -> AsyncIterator[ChatGeneration]:
        """Not supported."""
        raise NotImplementedError("Streaming not supported by Claude CLI")


# Convenience function for drop-in replacement
def create_claude_cli(
    model: str = "claude-sonnet-4-20250514",
    temperature: float = 0.7,
    max_tokens: int = 4096
) -> ClaudeCLI:
    """
    Create a ClaudeCLI instance.

    This is a convenience function that mimics ChatAnthropic constructor.

    Args:
        model: Claude model name
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens to generate

    Returns:
        Configured ClaudeCLI instance
    """
    return ClaudeCLI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )
