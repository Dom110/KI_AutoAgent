from __future__ import annotations

"""
Anthropic Service Integration
Handles all Anthropic API calls for Claude 4.1 models
"""

import logging
import os
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

from anthropic import AsyncAnthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass()
class AnthropicConfig:
    """Anthropic configuration"""

    api_key: str
    model: str = "claude-4.1-sonnet-20250920"
    temperature: float = 0.7
    max_tokens: int = 4000
    streaming: bool = True


class AnthropicService:
    """
    Anthropic Service for Claude 4.1 models
    Used by: CodeSmithAgent, OpusArbitrator, TradeStrat
    """

    def __init__(self, config: AnthropicConfig | None = None):
        if config is None:
            config = AnthropicConfig(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

        self.config = config

        if not self.config.api_key:
            logger.warning("Anthropic API key not found in environment variables")
            self.client = None
        else:
            self.client = AsyncAnthropic(api_key=self.config.api_key)
            logger.info(
                f"✅ Anthropic Service initialized with model: {self.config.model}"
            )

    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> str:
        """
        Get completion from Claude
        """
        if not self.client:
            return "Error: Anthropic API key not configured"

        messages = [{"role": "user", "content": prompt}]

        try:
            if stream:
                return await self._stream_completion(
                    messages,
                    system_prompt,
                    temperature or self.config.temperature,
                    max_tokens or self.config.max_tokens,
                )
            else:
                response = await self.client.messages.create(
                    model=self.config.model,
                    system=system_prompt or "",
                    messages=messages,
                    temperature=temperature or self.config.temperature,
                    max_tokens=max_tokens or self.config.max_tokens,
                )

                # Extract text from response
                if response.content:
                    if isinstance(response.content, list):
                        return response.content[0].text if response.content else ""
                    return response.content

                return ""

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return f"Error calling Anthropic API: {str(e)}"

    async def _stream_completion(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]:
        """
        Stream completion from Claude
        """
        try:
            stream = await self.client.messages.create(
                model=self.config.model,
                system=system_prompt or "",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.type == "content_block_delta":
                    if hasattr(chunk, "delta") and hasattr(chunk.delta, "text"):
                        yield chunk.delta.text

        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            yield f"Error: {str(e)}"

    async def generate_code(
        self, specification: str, language: str = "python", context: str | None = None
    ) -> str:
        """
        Generate code using Claude's superior coding abilities
        """
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

    async def review_code(self, code: str, language: str = "python") -> dict[str, Any]:
        """
        Review code for issues and improvements
        """
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
            "has_issues": "critical" in response.lower() or "bug" in response.lower(),
        }

    async def resolve_conflict(
        self, outputs: list[dict[str, Any]], context: str = ""
    ) -> dict[str, Any]:
        """
        Use Opus for conflict resolution between agents
        """
        # Switch to Opus for conflict resolution
        original_model = self.config.model
        self.config.model = "claude-4.1-opus-20250915"

        system_prompt = """
        You are the Opus Arbitrator, the supreme decision maker.
        Your role is to resolve conflicts between AI agents objectively.
        Analyze all positions, consider their merits, and make a final binding decision.
        Your decision must be clear, well-reasoned, and actionable.
        """

        prompt = f"""
        Context: {context}

        Conflicting Agent Outputs:
        {self._format_outputs(outputs)}

        Please:
        1. Analyze each agent's position
        2. Identify the core conflict
        3. Evaluate the merits of each approach
        4. Make a final decision with clear reasoning
        5. Provide actionable next steps

        Your decision is final and binding.
        """

        response = await self.complete(prompt, system_prompt)

        # Restore original model
        self.config.model = original_model

        return {
            "decision": response,
            "arbitrator": "OpusArbitrator",
            "model": "claude-4.1-opus-20250915",
            "binding": True,
        }

    def _format_outputs(self, outputs: list[dict[str, Any]]) -> str:
        """Format agent outputs for display"""
        formatted = []
        for i, output in enumerate(outputs, 1):
            formatted.append(
                f"""
Agent {i}: {output.get('agent', 'Unknown')}
Output: {output.get('content', 'No content')}
---"""
            )
        return "\n".join(formatted)

    def is_available(self) -> bool:
        """Check if service is available"""
        return self.client is not None
