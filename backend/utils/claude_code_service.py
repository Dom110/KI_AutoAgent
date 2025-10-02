"""
Claude Code CLI Service for Python
Integrates with the Claude Code CLI application
NO FALLBACKS - Fails with clear errors if CLI not available
"""

import asyncio
import json
import logging
import subprocess
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ClaudeCodeConfig:
    """Configuration for Claude Code CLI"""
    model: str = "default"  # opus, sonnet, default
    temperature: float = 0.7
    max_tokens: int = 4000
    output_format: str = "text"  # json or text - use "text" for simple responses

class ClaudeCodeService:
    """
    Claude Code CLI Service - Uses local Claude app, NO API fallbacks

    IMPORTANT: Requires Claude Code CLI to be installed and running
    Install: npm install -g @anthropic-ai/claude-code
    """

    def __init__(self, config: Optional[ClaudeCodeConfig] = None):
        self.config = config or ClaudeCodeConfig()
        self.cli_available = False

        # Check if Claude CLI is available
        self._check_cli_availability()

    def _check_cli_availability(self) -> bool:
        """Check if Claude CLI is installed and available"""
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                self.cli_available = True
                logger.info(f"✅ Claude Code CLI found: {result.stdout.strip()}")
                return True
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.error(f"❌ Claude Code CLI not found: {e}")
            self.cli_available = False

        return False

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """
        Get completion from Claude CLI
        NO FALLBACK - Fails if CLI not available
        """
        if not self.cli_available:
            error_msg = (
                "Claude Code CLI is not available!\n"
                "Please install it with: npm install -g @anthropic-ai/claude-code\n"
                "Or configure the agent to use a different model/service."
            )
            logger.error(error_msg)
            raise Exception(error_msg)

        # Combine system and user prompts
        full_prompt = ""
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
        else:
            full_prompt = prompt

        # Build CLI command
        cmd = [
            "claude",
            "--print",  # Non-interactive mode
            "--output-format", self.config.output_format
        ]

        if self.config.model != "default":
            cmd.extend(["--model", self.config.model])

        try:
            # Run Claude CLI
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Send prompt and get response (increased timeout for complex requests)
            timeout_seconds = 300  # 5 minutes for complex code generation (Tetris, games, etc)
            logger.info(f"⏱️ Running Claude CLI with {timeout_seconds}s timeout...")

            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=full_prompt.encode()),
                timeout=timeout_seconds
            )

            if process.returncode != 0:
                error_msg = f"Claude CLI failed: {stderr.decode()}"
                logger.error(error_msg)
                raise Exception(error_msg)

            # Parse response based on format
            if self.config.output_format == "json":
                return self._parse_json_response(stdout.decode())
            else:
                return stdout.decode().strip()

        except asyncio.TimeoutError:
            error_msg = f"Claude CLI timed out after {timeout_seconds} seconds"
            logger.error(error_msg)
            logger.error("💡 Tip: Complex code generation may need more time")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Claude CLI error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def _parse_json_response(self, response: str) -> str:
        """Parse JSON response from Claude CLI"""
        lines = response.strip().split('\n')
        text_parts = []

        for line in lines:
            if not line.strip():
                continue

            try:
                data = json.loads(line)

                # Handle different event types
                if data.get('type') == 'content_block_delta':
                    if 'delta' in data and 'text' in data['delta']:
                        text_parts.append(data['delta']['text'])

                elif data.get('type') == 'text':
                    if 'text' in data:
                        text_parts.append(data['text'])

                elif data.get('type') == 'assistant':
                    if 'content' in data:
                        if isinstance(data['content'], str):
                            text_parts.append(data['content'])
                        elif isinstance(data['content'], list):
                            for item in data['content']:
                                if isinstance(item, dict) and item.get('type') == 'text':
                                    text = item.get('text', '')
                                    if isinstance(text, str):
                                        text_parts.append(text)
                                elif isinstance(item, str):
                                    text_parts.append(item)

            except json.JSONDecodeError:
                # If not JSON, treat as plain text
                if line and not line.startswith('{'):
                    text_parts.append(line)

        # Ensure all parts are strings before joining
        string_parts = []
        for part in text_parts:
            if isinstance(part, str):
                string_parts.append(part)
            else:
                logger.warning(f"Skipping non-string part: {type(part)} - {part}")

        return ''.join(string_parts)

    async def generate_code(
        self,
        specification: str,
        language: str = "python",
        context: Optional[str] = None
    ) -> str:
        """Generate code using Claude CLI"""
        system_prompt = f"""
        You are Claude, an expert {language} programmer.
        Generate clean, efficient, and well-documented code.
        Follow best practices, include comprehensive error handling.
        Consider edge cases and performance implications.
        """

        prompt = f"""
        Language: {language}

        Specification:
        {specification}

        {"Context:\n" + context if context else ""}

        Please generate the complete, production-ready code:
        """

        return await self.complete(prompt, system_prompt)

    async def review_code(
        self,
        code: str,
        language: str = "python"
    ) -> Dict[str, Any]:
        """Review code using Claude CLI"""
        system_prompt = """
        You are a senior code reviewer.
        Analyze the code for:
        1. Bugs and potential issues
        2. Performance problems
        3. Security vulnerabilities
        4. Code quality and maintainability
        5. Best practices violations

        Be thorough but constructive.
        """

        prompt = f"""
        Language: {language}

        Code to review:
        ```{language}
        {code}
        ```

        Provide a detailed review with:
        - Issues found (severity: critical/high/medium/low)
        - Suggested improvements
        - Security concerns
        - Performance optimizations
        """

        response = await self.complete(prompt, system_prompt)

        return {
            "review": response,
            "has_issues": "critical" in response.lower() or "bug" in response.lower()
        }

    def is_available(self) -> bool:
        """Check if service is available"""
        return self.cli_available

    async def test_connection(self) -> Dict[str, Any]:
        """Test CLI connection and return status"""
        if not self.cli_available:
            return {
                "available": False,
                "error": "Claude CLI not installed",
                "suggestion": "Install with: npm install -g @anthropic-ai/claude-code"
            }

        try:
            # Test with simple prompt
            response = await self.complete("Say 'test successful'")
            return {
                "available": True,
                "response": response,
                "cli_version": "claude-code CLI"
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
                "suggestion": "Check if Claude app is running"
            }