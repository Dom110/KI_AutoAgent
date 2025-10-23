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

        # Check API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return (
                False,
                "ANTHROPIC_API_KEY not set. Required for Claude CLI."
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
        cmd = [
            self.cli_path,
            "--model", self.model,
            "--workspace", request.workspace_path or os.getcwd(),
        ]

        # Add tools (Read, Edit, Bash)
        if request.tools:
            for tool in request.tools:
                if tool in ["Read", "Edit", "Bash"]:
                    cmd.extend(["--tool", tool])
        else:
            # Default tools for code generation
            cmd.extend(["--tool", "Read", "--tool", "Edit", "--tool", "Bash"])

        # Add prompt
        cmd.append(full_prompt)

        try:
            logger.debug(f"🔨 Running Claude CLI: {' '.join(cmd[:5])}...")

            # Run claude CLI
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=request.workspace_path or os.getcwd()
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300.0  # 5 minute timeout
            )

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
            logger.error("❌ Claude CLI timed out after 5 minutes")
            return AIResponse(
                content="",
                provider=self.provider_name,
                model=self.model,
                success=False,
                error="Claude CLI timeout (5 minutes)"
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
        Build the full prompt for Claude CLI.

        Includes system prompt, context, and user prompt.
        """
        parts = []

        # System prompt
        if request.system_prompt:
            parts.append(f"<system>\n{request.system_prompt}\n</system>")

        # Context (architecture, research, etc.)
        if request.context:
            parts.append("\n<context>")
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
            parts.append("\n</context>")

        # User prompt (instructions)
        parts.append(f"\n<task>\n{request.prompt}\n</task>")

        # Workspace hint
        if request.workspace_path:
            parts.append(f"\n<workspace>{request.workspace_path}</workspace>")

        return "\n".join(parts)


# ============================================================================
# Register with Factory
# ============================================================================

from backend.utils.ai_factory import AIFactory

AIFactory.register_provider("claude-cli", ClaudeCLIService)

logger.info("✅ Claude CLI provider registered")
