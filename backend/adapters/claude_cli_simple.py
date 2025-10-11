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

# DEBUG_OUTPUT: Set to True to enable detailed output during development
DEBUG_OUTPUT = True  # Set to False in production


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
        allowed_tools: list[str] | None = None,
        hitl_callback: Any = None,
        workspace_path: str | None = None
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
            hitl_callback: Async callback for HITL debug info
                          Signature: async def(debug_info: dict) -> None
            workspace_path: Working directory for Claude CLI subprocess
                          CRITICAL: Must be set to target workspace to avoid confusion!
                          Bug found 2025-10-11: Without this, CLI runs from dev repo
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
        self.hitl_callback = hitl_callback
        self.workspace_path = workspace_path  # 🎯 FIX: Set CWD for subprocess

        # HITL Debug Info (captured during execution)
        self.last_command: list[str] | None = None
        self.last_system_prompt: str | None = None
        self.last_user_prompt: str | None = None
        self.last_combined_prompt: str | None = None
        self.last_raw_output: str | None = None
        self.last_events: list[dict] | None = None
        self.last_duration_ms: float = 0.0
        self.last_error: str | None = None

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

    def extract_file_paths_from_events(self, events: list[dict]) -> list[dict[str, Any]]:
        """
        Extract file paths from Claude CLI Edit tool use events.

        Claude CLI uses Edit tool to create/modify files. These operations
        are logged in JSONL events. This method extracts the file paths from
        those tool_use events.

        Args:
            events: List of JSONL events from Claude CLI

        Returns:
            List of file info dicts with format:
            [{"path": "src/file.ts", "size": 1234, "validated": True, ...}, ...]
        """
        import os

        files = []
        file_paths_seen = set()

        for event in events:
            event_type = event.get("type")

            # Look for assistant messages with tool use
            if event_type == "assistant":
                message = event.get("message", {})
                content = message.get("content", [])

                # Content can be a list of content blocks
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            tool_name = block.get("name")
                            tool_input = block.get("input", {})

                            # Edit tool creates/modifies files
                            if tool_name == "Edit":
                                file_path = tool_input.get("file_path") or tool_input.get("path")

                                if file_path and file_path not in file_paths_seen:
                                    file_paths_seen.add(file_path)

                                    # Check if file actually exists in workspace
                                    full_path = os.path.join(self.workspace_path, file_path) if self.workspace_path else file_path
                                    file_exists = os.path.isfile(full_path)

                                    if file_exists:
                                        size = os.path.getsize(full_path)
                                        files.append({
                                            "path": file_path,
                                            "size": size,
                                            "validated": True,  # Edit tool was used
                                            "tool": "Edit"
                                        })
                                        logger.info(f"📄 Extracted file from Edit tool: {file_path} ({size} bytes)")
                                    else:
                                        # File mentioned but not found (might be error case)
                                        logger.warning(f"⚠️  Edit tool mentioned {file_path} but file not found")

        logger.info(f"✅ Extracted {len(files)} files from {len(events)} Claude CLI events")
        return files

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
        import time
        start_time = time.time()

        # Extract system prompt (agent instructions) and user prompt (task)
        system_prompt, user_prompt = self._extract_system_and_user_prompts(messages)

        # 🎯 FIX (2025-10-11): Special handling for Codesmith (needs strict format!)
        # Problem: Long combined prompts → Format instructions get lost
        # Solution: For codesmith, use short focused prompt in agent.prompt
        if self.agent_name == "codesmith":
            agent_prompt = """You are a code generator.
CRITICAL: START YOUR RESPONSE WITH 'FILE:' immediately!
Format: FILE: path
```language
code
```
NO explanations!"""
            combined_prompt = user_prompt  # Only user task in -p
        else:
            # For other agents: Original strategy (works, no timeout issues)
            agent_prompt = "You are a helpful assistant."
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"

        # HITL: Capture prompts
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        self.last_combined_prompt = combined_prompt

        # Build agent definition
        agent_definition = {
            self.agent_name: {
                "description": self.agent_description,
                "prompt": agent_prompt,  # 🎯 Conditional: focused for codesmith, minimal for others
                "tools": self.agent_tools  # MUST be non-empty! Empty = timeout
            }
        }

        # Build CLI command with ALL working parameters
        # SUCCESS: --agents + stream-json + --verbose + combined prompt in -p!
        cmd = [
            self.cli_path,
            "--model", self.model,
            "--permission-mode", self.permission_mode,
            "--allowedTools", " ".join(self.allowed_tools),
            "--agents", json.dumps(agent_definition),
            "--output-format", "stream-json",
            "--verbose",                      # REQUIRED with stream-json!
            "-p", combined_prompt             # System + User COMBINED!
        ]

        # HITL: Capture command
        self.last_command = cmd.copy()

        # LOG COMPLETE COMMAND FOR USER
        with open("/tmp/claude_cli_command.txt", "w") as f:
            f.write(f"# Complete Claude CLI command\n\n")
            f.write(f"# Command as list:\n{cmd}\n\n")
            f.write(f"# Command as shell (for manual testing):\n")
            f.write(f"claude \\\n")
            f.write(f'  --model {self.model} \\\n')
            f.write(f'  --permission-mode {self.permission_mode} \\\n')
            f.write(f'  --allowedTools "{" ".join(self.allowed_tools)}" \\\n')
            f.write(f"  --agents '{json.dumps(agent_definition)}' \\\n")
            f.write(f'  --output-format stream-json \\\n')
            f.write(f'  --verbose \\\n')
            f.write(f'  -p "$(cat /tmp/claude_user_prompt.txt)"\n')
        logger.info(f"📝 Complete command saved to /tmp/claude_cli_command.txt")

        # DEBUG: Show exact command
        if DEBUG_OUTPUT:
            print("\n" + "="*80)
            print("🚀 EXECUTING CLAUDE CLI")
            print("="*80)
            print(f"Command parts:")
            for i, arg in enumerate(cmd):
                if arg.startswith("--"):
                    print(f"  [{i}] {arg}")
                elif i > 0 and cmd[i-1].startswith("--"):
                    preview = arg[:150] + "..." if len(arg) > 150 else arg
                    print(f"       → {preview}")
            print("="*80 + "\n")

        logger.debug(f"Calling Claude CLI: --agents {self.agent_name} + stream-json + verbose")

        # HITL: Send debug info BEFORE execution
        if self.hitl_callback:
            try:
                await self.hitl_callback({
                    "type": "claude_cli_start",
                    "agent": self.agent_name,
                    "model": self.model,
                    "command": cmd,
                    "system_prompt": system_prompt,
                    "system_prompt_length": len(system_prompt),
                    "user_prompt": user_prompt,
                    "user_prompt_length": len(user_prompt),
                    "combined_prompt_length": len(combined_prompt),
                    "tools": self.agent_tools,
                    "permission_mode": self.permission_mode,
                    "timestamp": start_time
                })
            except Exception as e:
                logger.warning(f"HITL callback failed (start): {e}")

        try:
            # Run CLI command
            if DEBUG_OUTPUT:
                print("⏳ Starting subprocess...")
                if self.workspace_path:
                    print(f"   CWD: {self.workspace_path}")

            # 🎯 FIX (2025-10-11): Set correct working directory!
            # Bug: Without cwd, subprocess runs from wherever Python started
            # → Claude finds old test artifacts in dev repo
            # → Gets confused, crashes after 5 minutes
            # Solution: Explicit CWD to target workspace
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL,  # Prevent CLI from waiting on stdin
                cwd=self.workspace_path  # 🎯 USE WORKSPACE AS WORKING DIRECTORY!
            )
            if DEBUG_OUTPUT:
                print(f"✅ Process started, PID: {process.pid}")

            if DEBUG_OUTPUT:
                print("⏳ Waiting for response...")
            stdout, stderr = await process.communicate()
            if DEBUG_OUTPUT:
                print(f"✅ Process completed, returncode: {process.returncode}")

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                if DEBUG_OUTPUT:
                    print(f"❌ ERROR: {error_msg[:500]}")
                raise RuntimeError(f"Claude CLI failed: {error_msg}")

            # Decode output (stream-json format = JSONL)
            output_str = stdout.decode().strip()

            if DEBUG_OUTPUT:
                print(f"\n📦 Received {len(output_str)} chars of output")
            logger.debug(f"CLI returned {len(output_str)} chars")

            # DEBUG: Save raw output to file for inspection
            import tempfile
            debug_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='_claude_raw.jsonl')
            debug_file.write(output_str)
            debug_file.close()
            if DEBUG_OUTPUT:
                print(f"💾 Raw output saved to: {debug_file.name}")
            logger.info(f"🔍 DEBUG: Raw CLI output saved to: {debug_file.name}")

            # Parse JSONL (JSON Lines) - each line is a separate event
            if not output_str:
                if DEBUG_OUTPUT:
                    print("❌ ERROR: Empty response!")
                raise RuntimeError("Empty response from Claude CLI")

            lines = output_str.split('\n')
            events = []

            if DEBUG_OUTPUT:
                print(f"\n📊 Parsing {len(lines)} lines...")
                print("="*80)

            for i, line in enumerate(lines, 1):
                if line.strip():
                    try:
                        event = json.loads(line)
                        events.append(event)

                        # Show event details
                        if DEBUG_OUTPUT:
                            event_type = event.get('type', 'unknown')
                            event_subtype = event.get('subtype', '')

                            if event_type == "system":
                                print(f"  [{i}] 🔧 SYSTEM: {event_subtype}")
                            elif event_type == "assistant":
                                message = event.get('message', {})
                                content_preview = str(message)[:100]
                                print(f"  [{i}] 🤖 ASSISTANT: {content_preview}...")
                            elif event_type == "user":
                                print(f"  [{i}] 👤 USER")
                            elif event_type == "result":
                                result_preview = str(event.get('result', ''))[:100]
                                print(f"  [{i}] ✅ RESULT: {result_preview}...")
                            else:
                                print(f"  [{i}] ❓ {event_type}: {str(event)[:100]}...")

                        logger.debug(f"✅ Parsed line {i}: type={event.get('type')}")
                    except json.JSONDecodeError as e:
                        if DEBUG_OUTPUT:
                            print(f"  [{i}] ❌ JSON PARSE ERROR")
                            print(f"        Length: {len(line)} chars")
                            print(f"        Preview: {line[:200]}...")
                        logger.error(f"❌ JSON parse error on line {i}: {e}")
                        logger.error(f"   Line length: {len(line)} chars")
                        logger.error(f"   First 200: {line[:200]}")
                        logger.error(f"   Last 200: {line[-200:]}")
                        # Try to parse anyway - might be incomplete but salvageable
                        continue

            if DEBUG_OUTPUT:
                print("="*80)
                print(f"✅ Parsed {len(events)} events total\n")

            if not events:
                if DEBUG_OUTPUT:
                    print("❌ ERROR: No valid events!")
                raise RuntimeError("No valid JSON events in response")

            # Last event contains the final result
            final_event = events[-1]

            logger.debug(f"Parsed {len(events)} events, final type: {final_event.get('type')}")

            # Calculate duration
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000

            # HITL: Capture execution info
            self.last_raw_output = output_str
            self.last_events = events
            self.last_duration_ms = duration_ms
            self.last_error = None

            # HITL: Send debug info AFTER successful execution
            if self.hitl_callback:
                try:
                    await self.hitl_callback({
                        "type": "claude_cli_complete",
                        "agent": self.agent_name,
                        "model": self.model,
                        "duration_ms": duration_ms,
                        "output_length": len(output_str),
                        "raw_output": output_str,
                        "events_count": len(events),
                        "events": events,
                        "final_event_type": final_event.get('type'),
                        "result_preview": str(final_event.get('result', ''))[:500],
                        "success": True,
                        "timestamp": end_time
                    })
                except Exception as e:
                    logger.warning(f"HITL callback failed (complete): {e}")

            return final_event

        except Exception as e:
            # Calculate duration even on error
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000

            # HITL: Capture error info
            self.last_error = str(e)
            self.last_duration_ms = duration_ms

            # HITL: Send debug info AFTER error
            if self.hitl_callback:
                try:
                    await self.hitl_callback({
                        "type": "claude_cli_error",
                        "agent": self.agent_name,
                        "model": self.model,
                        "duration_ms": duration_ms,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "success": False,
                        "timestamp": end_time
                    })
                except Exception as callback_error:
                    logger.warning(f"HITL callback failed (error): {callback_error}")

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

        # CRITICAL: Based on testing (2025-10-10):
        # - System prompt in agent.prompt ALONE causes timeout!
        # - MUST combine system + user in -p parameter
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"

        # Build agent definition with MINIMAL prompt
        agent_definition = {
            self.agent_name: {
                "description": self.agent_description,
                "prompt": "You are a helpful assistant.",  # Minimal! System goes in -p
                "tools": self.agent_tools  # MUST be non-empty!
            }
        }

        # Build CLI command
        # SUCCESS: --agents + stream-json + --verbose + combined prompt!
        cmd = [
            self.cli_path,
            "--model", self.model,
            "--permission-mode", self.permission_mode,
            "--allowedTools", " ".join(self.allowed_tools),
            "--agents", json.dumps(agent_definition),
            "--output-format", "stream-json",
            "--verbose",                      # REQUIRED with stream-json!
            "-p", combined_prompt             # System + User COMBINED!
        ]

        logger.debug(f"Calling Claude CLI sync: --agents {self.agent_name} + stream-json + verbose")

        try:
            # 🎯 FIX (2025-10-11): Set correct working directory!
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=self.workspace_path  # 🎯 USE WORKSPACE AS WORKING DIRECTORY!
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
