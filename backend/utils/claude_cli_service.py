"""
Claude CLI Service - Integration with Claude CLI

Uses the `claude` command-line tool for code generation.
Supports Read, Edit, Bash tools but NOT Write.

Requirements:
- Claude CLI installed: npm install -g @anthropic-ai/claude-cli
- ANTHROPIC_API_KEY set in environment

Author: KI AutoAgent Team
Version: 7.0.0
Date: 2025-10-23
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import AsyncGenerator

from backend.utils.ai_factory import AIProvider, AIRequest, AIResponse
from backend.utils.rate_limiter import wait_for_provider

logger = logging.getLogger(__name__)


class ClaudeCLIService(AIProvider):
    """
    AI Provider that uses Claude CLI for code generation.

    Claude CLI is better for code because:
    - Direct file access (Read, Edit tools)
    - Can run shell commands (Bash tool)
    - Better at following architecture
    - No token limits for file reading
    """

    def __init__(self, model: str | None = None):
        """Initialize Claude CLI Service."""
        super().__init__(model=model)

        # Check if claude CLI is available
        self.cli_path = shutil.which("claude")
        if not self.cli_path:
            logger.warning("⚠️ Claude CLI not found in PATH")
            logger.warning("   Install: npm install -g @anthropic-ai/claude-cli")
            self.cli_available = False
        else:
            self.cli_available = True
            logger.info(f"   ✅ Claude CLI found at: {self.cli_path}")

    def _get_provider_name(self) -> str:
        return "claude-cli"

    def _get_default_model(self) -> str:
        return os.getenv("CLAUDE_CLI_MODEL", "claude-sonnet-4-20250514")

    async def validate_connection(self) -> tuple[bool, str]:
        """
        Validate Claude CLI is available and configured.

        Returns:
            (success, message)
        """
        if not self.cli_available:
            return (
                False,
                "Claude CLI binary not found. Install: npm install -g @anthropic-ai/claude-cli"
            )

        # Try to run claude --version
        try:
            result = subprocess.run(
                [self.cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                # Claude Code authenticates via its own config
                # No need for ANTHROPIC_API_KEY in .env
                return (True, f"Claude CLI {version}")
            else:
                return (False, f"Claude CLI error: {result.stderr}")
        except Exception as e:
            return (False, f"Claude CLI validation failed: {e}")

    async def complete(self, request: AIRequest) -> AIResponse:
        """
        Get completion from Claude CLI.

        Args:
            request: AI request with prompt, context, workspace_path, tools

        Returns:
            AI response with generated content
        """
        if not self.cli_available:
            return AIResponse(
                content="",
                provider=self.provider_name,
                model=self.model,
                success=False,
                error="Claude CLI not available"
            )

        # Rate limiting
        await wait_for_provider("claude-cli")

        # Build prompt
        full_prompt = self._build_prompt(request)

        # Build claude CLI command
        # Use --print for non-interactive mode
        cmd = [
            self.cli_path,
            "--print",  # Non-interactive output
            "--model", self.model,
        ]

        # Add allowed tools (space-separated list)
        if request.tools:
            tools_str = " ".join(request.tools)
            cmd.extend(["--allowed-tools", tools_str])
        else:
            # Default tools for code generation
            cmd.extend(["--allowed-tools", "Read Edit Bash"])

        # Add system prompt if provided
        if request.system_prompt:
            cmd.extend(["--system-prompt", request.system_prompt])

        # Add prompt as final argument
        cmd.append(full_prompt)

        # Set working directory to workspace_path
        workspace = request.workspace_path or os.getcwd()

        try:
            logger.debug(f"🔨 Running Claude CLI in {workspace}")
            logger.debug(f"   Command: claude --print --model {self.model} --allowed-tools 'Read Edit Bash'")
            logger.debug(f"   Prompt length: {len(full_prompt)} chars")

            # Run claude CLI with workspace as cwd
            # CRITICAL FIX: Close stdin to prevent Claude CLI from waiting for input
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.DEVNULL,  # Close stdin - Claude CLI shouldn't wait for input
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workspace
            )

            logger.debug(f"   📡 Process started (PID: {process.pid})")

            # Wait for completion with timeout
            # Reduced timeout from 5 min to 2 min (should be enough for code gen)
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=120.0  # 2 minute timeout
            )

            logger.debug(f"   📡 Process completed (returncode: {process.returncode})")

            if process.returncode == 0:
                content = stdout.decode('utf-8').strip()
                logger.info(f"✅ Claude CLI completed ({len(content)} chars)")

                return AIResponse(
                    content=content,
                    provider=self.provider_name,
                    model=self.model,
                    success=True,
                    metadata={
                        "returncode": process.returncode,
                        "workspace": request.workspace_path
                    }
                )
            else:
                error = stderr.decode('utf-8').strip()
                logger.error(f"❌ Claude CLI failed: {error}")

                return AIResponse(
                    content="",
                    provider=self.provider_name,
                    model=self.model,
                    success=False,
                    error=error
                )

        except asyncio.TimeoutError:
            logger.error("❌ Claude CLI timed out after 2 minutes")
            logger.error(f"   Workspace: {workspace}")
            logger.error(f"   Prompt: {full_prompt[:200]}...")

            # Try to kill the process if it's still running
            try:
                if process and process.returncode is None:
                    process.kill()
                    logger.warning("   🔪 Killed hanging Claude CLI process")
            except Exception as kill_err:
                logger.warning(f"   Failed to kill process: {kill_err}")

            return AIResponse(
                content="",
                provider=self.provider_name,
                model=self.model,
                success=False,
                error="Claude CLI timeout (2 minutes)"
            )
        except Exception as e:
            logger.error(f"❌ Claude CLI exception: {e}")
            return AIResponse(
                content="",
                provider=self.provider_name,
                model=self.model,
                success=False,
                error=str(e)
            )

    async def stream_complete(self, request: AIRequest) -> AsyncGenerator[str, None]:
        """
        Claude CLI doesn't support streaming easily.
        Fall back to regular complete and yield the result.
        """
        response = await self.complete(request)
        if response.success:
            yield response.content
        else:
            yield f"Error: {response.error}"

    def _build_prompt(self, request: AIRequest) -> str:
        """
        Build the user prompt for Claude CLI.

        System prompt is passed via --system-prompt flag, not in user message.
        """
        parts = []

        # Context (architecture, research, etc.)
        if request.context:
            parts.append("<context>")
            for key, value in request.context.items():
                if value:
                    parts.append(f"\n## {key.title()}")
                    if isinstance(value, dict):
                        parts.append(json.dumps(value, indent=2))
                    elif isinstance(value, list):
                        for item in value:
                            parts.append(f"- {item}")
                    else:
                        parts.append(str(value))
            parts.append("</context>\n")

        # User prompt (instructions)
        parts.append(f"<task>\n{request.prompt}\n</task>")

        # Workspace hint
        if request.workspace_path:
            parts.append(f"\nWorking directory: {request.workspace_path}")

        return "\n".join(parts)


# ============================================================================
# Register with Factory
# ============================================================================

from backend.utils.ai_factory import AIFactory

AIFactory.register_provider("claude-cli", ClaudeCLIService)

logger.info("✅ Claude CLI provider registered")
