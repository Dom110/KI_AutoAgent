"""
Simple Claude CLI Wrapper

A lightweight wrapper around `claude --print` that mimics the ChatAnthropic
interface without complex Pydantic dependencies.

Usage:
    from adapters.claude_cli_simple import ClaudeCLISimple

    llm = ClaudeCLISimple(model="claude-sonnet-4-20250514")
    response = await llm.ainvoke([HumanMessage(content="Hello")])

Author: KI AutoAgent Team
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, List

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)

logger = logging.getLogger(__name__)


class ClaudeCLISimple:
    """
    Simple wrapper for Claude CLI that mimics ChatAnthropic interface.

    This is a lightweight alternative that doesn't inherit from BaseChatModel,
    avoiding Pydantic issues while still providing the same ainvoke() interface.
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        cli_path: str = "claude"
    ):
        """
        Initialize Claude CLI wrapper.

        Args:
            model: Claude model name
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            cli_path: Path to claude CLI binary
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.cli_path = cli_path

    def _format_messages(self, messages: List[BaseMessage]) -> str:
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

    async def _call_cli(self, prompt: str) -> dict[str, Any]:
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

        logger.debug(f"Calling Claude CLI with model: {self.model}")

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

            logger.debug(f"CLI response type: {response.get('type')}")

            return response

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse CLI JSON: {e}")
            raise RuntimeError(f"Invalid JSON from Claude CLI: {e}")
        except Exception as e:
            logger.error(f"Claude CLI error: {e}", exc_info=True)
            raise

    async def ainvoke(
        self,
        messages: List[BaseMessage],
        **kwargs: Any,
    ) -> AIMessage:
        """
        Async invoke - main entry point (compatible with ChatAnthropic).

        Args:
            messages: List of messages
            **kwargs: Additional arguments (ignored)

        Returns:
            AIMessage with response
        """
        # Format messages into prompt
        prompt = self._format_messages(messages)

        # Call CLI
        response = await self._call_cli(prompt)

        # Extract result
        if response.get("is_error"):
            error_msg = response.get("result", "Unknown error")
            raise RuntimeError(f"Claude CLI error: {error_msg}")

        content = response.get("result", "")

        # Return AI message
        return AIMessage(content=content)

    def _call_cli_sync(self, prompt: str) -> dict[str, Any]:
        """
        Call Claude CLI synchronously.

        Args:
            prompt: Formatted prompt string

        Returns:
            Parsed JSON response from CLI
        """
        cmd = [
            self.cli_path,
            "--print",
            "--output-format", "json",
            "--model", self.model,
            prompt
        ]

        logger.debug(f"Calling Claude CLI sync with model: {self.model}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            response = json.loads(result.stdout)
            logger.debug(f"CLI sync response type: {response.get('type')}")

            return response

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else "Unknown error"
            raise RuntimeError(f"Claude CLI failed: {error_msg}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse CLI JSON: {e}")
            raise RuntimeError(f"Invalid JSON from Claude CLI: {e}")
        except Exception as e:
            logger.error(f"Claude CLI error: {e}", exc_info=True)
            raise

    def invoke(self, messages: List[BaseMessage], **kwargs: Any) -> AIMessage:
        """
        Sync invoke (for LangGraph compatibility).

        Args:
            messages: List of messages
            **kwargs: Additional arguments

        Returns:
            AIMessage with response
        """
        # Format messages into prompt
        prompt = self._format_messages(messages)

        # Call CLI synchronously
        response = self._call_cli_sync(prompt)

        # Extract result
        if response.get("is_error"):
            error_msg = response.get("result", "Unknown error")
            raise RuntimeError(f"Claude CLI error: {error_msg}")

        content = response.get("result", "")

        # Return AI message
        return AIMessage(content=content)
