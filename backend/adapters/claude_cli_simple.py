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
import subprocess
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
        cli_path: str = "claude",
        agent_name: str = "assistant",
        agent_description: str = "AI Assistant",
        agent_tools: list[str] | None = None,
        permission_mode: str = "acceptEdits",
        allowed_tools: list[str] | None = None
    ):
        """
        Initialize Claude CLI wrapper.

        Args:
            model: Claude model name (default: claude-sonnet-4-20250514 = Sonnet 4.5)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            cli_path: Path to claude CLI binary
            agent_name: Name of the agent (used in --agents parameter)
            agent_description: Description of when/how agent should be invoked
            agent_tools: List of tools for agent (ONLY valid: ["Read", "Edit", "Bash"])
                        CRITICAL: "Write" does NOT exist! Use "Edit" instead.
            permission_mode: Permission mode (default: "acceptEdits" = auto-approve)
            allowed_tools: Global allowed tools (passed to --allowedTools parameter)
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.cli_path = cli_path
        self.agent_name = agent_name
        self.agent_description = agent_description
        # CRITICAL: Write does NOT exist as Claude CLI tool! Only Read, Edit, Bash
        self.agent_tools = agent_tools or ["Read", "Edit", "Bash"]
        self.permission_mode = permission_mode
        self.allowed_tools = allowed_tools or ["Read", "Edit", "Bash"]

    def _extract_system_and_user_prompts(
        self,
        messages: List[BaseMessage]
    ) -> tuple[str, str]:
        """
        Extract system prompt (agent instructions) and user prompt (task) separately.

        Following Claude CLI best practices:
        - System messages → agent.prompt (agent behavior/instructions)
        - Human messages → -p parameter (user task/query)

        Args:
            messages: List of LangChain messages

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_parts = []
        user_parts = []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                # System prompt defines agent behavior
                system_parts.append(msg.content)
            elif isinstance(msg, HumanMessage):
                # Human messages are the actual task
                user_parts.append(msg.content)
            elif isinstance(msg, AIMessage):
                # For conversation history if needed
                user_parts.append(f"[Previous Assistant Response]: {msg.content}")
            else:
                # Generic message
                user_parts.append(str(msg.content))

        system_prompt = "\n\n".join(system_parts) if system_parts else "You are a helpful AI assistant."
        user_prompt = "\n\n".join(user_parts) if user_parts else "Hello"

        return system_prompt, user_prompt

    def _repair_json(self, json_str: str) -> str | None:
        """
        Attempt to repair common JSON issues.

        Common issues:
        - Unterminated strings (missing closing quote)
        - Missing closing braces/brackets
        - Truncated output

        Args:
            json_str: Potentially malformed JSON string

        Returns:
            Repaired JSON string or None if unrepairable
        """
        try:
            # Remove any leading/trailing whitespace
            json_str = json_str.strip()

            # Check if JSON is truncated (no closing brace)
            if json_str and not json_str.endswith('}'):
                # Try to find the last complete key-value pair
                # and close the JSON properly
                last_comma = json_str.rfind(',')
                last_quote = json_str.rfind('"')

                # If there's an unterminated string
                if last_quote > last_comma:
                    # Add closing quote
                    json_str += '"'

                # Add closing brace
                json_str += '}'

            # Try to balance braces
            open_braces = json_str.count('{')
            close_braces = json_str.count('}')
            if open_braces > close_braces:
                json_str += '}' * (open_braces - close_braces)

            # Try to balance brackets
            open_brackets = json_str.count('[')
            close_brackets = json_str.count(']')
            if open_brackets > close_brackets:
                json_str += ']' * (open_brackets - close_brackets)

            return json_str

        except Exception as e:
            logger.error(f"JSON repair failed: {e}")
            return None

    async def _call_cli(self, messages: List[BaseMessage]) -> dict[str, Any]:
        """
        Call Claude CLI with stream-json format to avoid truncation.

        Note: NOT using --agents parameter (causes timeouts in CLI 2.0.13)
        Instead: Format as "System: ...\n\nHuman: ..." and use --print

        Args:
            messages: List of LangChain messages

        Returns:
            Parsed JSON response from CLI (last event from JSONL)

        Raises:
            RuntimeError: If CLI call fails
        """
        # Extract system prompt (agent instructions) and user prompt (task)
        system_prompt, user_prompt = self._extract_system_and_user_prompts(messages)

        # Build agent definition
        agent_definition = {
            self.agent_name: {
                "description": self.agent_description,
                "prompt": system_prompt,
                "tools": self.agent_tools
            }
        }

        # Build CLI command with ALL working parameters
        # SUCCESS: --agents + stream-json + --verbose + -p WORKS!
        cmd = [
            self.cli_path,
            "--model", self.model,
            "--permission-mode", self.permission_mode,
            "--allowedTools", " ".join(self.allowed_tools),
            "--agents", json.dumps(agent_definition),
            "--output-format", "stream-json",
            "--verbose",                      # Required for stream-json!
            "-p", user_prompt
        ]

        logger.debug(f"Calling Claude CLI: --agents {self.agent_name} + stream-json + verbose")

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

            # Decode output (stream-json format = JSONL)
            output_str = stdout.decode().strip()

            logger.debug(f"CLI returned {len(output_str)} chars")

            # DEBUG: Save raw output to file for inspection
            import tempfile
            debug_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='_claude_raw.jsonl')
            debug_file.write(output_str)
            debug_file.close()
            logger.info(f"🔍 DEBUG: Raw CLI output saved to: {debug_file.name}")

            # Parse JSONL (JSON Lines) - each line is a separate event
            if not output_str:
                raise RuntimeError("Empty response from Claude CLI")

            lines = output_str.split('\n')
            events = []

            for i, line in enumerate(lines, 1):
                if line.strip():
                    try:
                        event = json.loads(line)
                        events.append(event)
                        logger.debug(f"✅ Parsed line {i}: type={event.get('type')}")
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ JSON parse error on line {i}: {e}")
                        logger.error(f"   Line length: {len(line)} chars")
                        logger.error(f"   First 200: {line[:200]}")
                        logger.error(f"   Last 200: {line[-200:]}")
                        # Try to parse anyway - might be incomplete but salvageable
                        continue

            if not events:
                raise RuntimeError("No valid JSON events in response")

            # Last event contains the final result
            final_event = events[-1]

            logger.debug(f"Parsed {len(events)} events, final type: {final_event.get('type')}")

            return final_event

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
        # Call CLI with messages (will extract system/user prompts internally)
        response = await self._call_cli(messages)

        # Extract result
        if response.get("is_error"):
            error_msg = response.get("result", "Unknown error")
            raise RuntimeError(f"Claude CLI error: {error_msg}")

        content = response.get("result", "")

        # Return AI message
        return AIMessage(content=content)

    def _call_cli_sync(self, messages: List[BaseMessage]) -> dict[str, Any]:
        """
        Call Claude CLI synchronously with stream-json format.

        Args:
            messages: List of LangChain messages

        Returns:
            Parsed JSON response from CLI (last event from JSONL)
        """
        # Extract system prompt (agent instructions) and user prompt (task)
        system_prompt, user_prompt = self._extract_system_and_user_prompts(messages)

        # Build agent definition
        agent_definition = {
            self.agent_name: {
                "description": self.agent_description,
                "prompt": system_prompt,
                "tools": self.agent_tools
            }
        }

        # Build CLI command
        # SUCCESS: --agents + stream-json + --verbose + -p WORKS!
        cmd = [
            self.cli_path,
            "--model", self.model,
            "--permission-mode", self.permission_mode,
            "--allowedTools", " ".join(self.allowed_tools),
            "--agents", json.dumps(agent_definition),
            "--output-format", "stream-json",
            "--verbose",                      # Required for stream-json!
            "-p", user_prompt
        ]

        logger.debug(f"Calling Claude CLI sync: --agents {self.agent_name} + stream-json + verbose")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            # Parse JSONL (stream-json format)
            output_str = result.stdout.strip()
            logger.debug(f"CLI returned {len(output_str)} chars")

            # DEBUG: Save raw output to file for inspection
            import tempfile
            debug_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='_claude_raw_sync.jsonl')
            debug_file.write(output_str)
            debug_file.close()
            logger.info(f"🔍 DEBUG: Raw CLI output saved to: {debug_file.name}")

            if not output_str:
                raise RuntimeError("Empty response from Claude CLI")

            # Parse each line as JSON
            lines = output_str.split('\n')
            events = []

            for i, line in enumerate(lines, 1):
                if line.strip():
                    try:
                        event = json.loads(line)
                        events.append(event)
                        logger.debug(f"✅ Parsed line {i}: type={event.get('type')}")
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ JSON parse error on line {i}: {e}")
                        logger.error(f"   Line length: {len(line)} chars")
                        logger.error(f"   First 200: {line[:200]}")
                        logger.error(f"   Last 200: {line[-200:]}")
                        continue

            if not events:
                raise RuntimeError("No valid JSON events in response")

            # Last event contains final result
            final_event = events[-1]
            logger.debug(f"Parsed {len(events)} events, final type: {final_event.get('type')}")

            return final_event

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else "Unknown error"
            raise RuntimeError(f"Claude CLI failed: {error_msg}")
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
        # Call CLI with messages (will extract system/user prompts internally)
        response = self._call_cli_sync(messages)

        # Extract result
        if response.get("is_error"):
            error_msg = response.get("result", "Unknown error")
            raise RuntimeError(f"Claude CLI error: {error_msg}")

        content = response.get("result", "")

        # Return AI message
        return AIMessage(content=content)
