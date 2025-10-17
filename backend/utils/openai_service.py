from __future__ import annotations

"""
OpenAI Service Integration
Handles all OpenAI API calls for GPT-5 models
"""

import logging
import os
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass()
class OpenAIConfig:
    """OpenAI configuration"""

    api_key: str
    model: str = "gpt-4o-2024-11-20"  # Default model, agents should override
    temperature: float = 0.7
    max_tokens: int = 4000
    streaming: bool = True


class OpenAIService:
    """
    OpenAI Service for GPT-4 models
    Used by: OrchestratorAgent, ArchitectAgent, DocuBot
    """

    def __init__(self, config: OpenAIConfig | None = None, model: str | None = None):
        if config is None:
            config = OpenAIConfig(
                api_key=os.getenv("OPENAI_API_KEY", ""),
                model=model if model else "gpt-4o-2024-11-20",
            )
        elif model:
            config.model = model

        self.config = config

        if not self.config.api_key:
            logger.warning("OpenAI API key not found in environment variables")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=self.config.api_key)
            logger.info(f"✅ OpenAI Service initialized with model: {self.config.model}")

    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
        timeout: float | None = None,
        response_format: dict[str, str] | None = None,
    ) -> str:
        """
        Get completion from OpenAI
        """
        if not self.client:
            return "Error: OpenAI API key not configured"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            if stream:
                return await self._stream_completion(
                    messages,
                    temperature or self.config.temperature,
                    max_tokens or self.config.max_tokens,
                )
            else:
                import asyncio

                # Use configurable timeout (default 120s for normal tasks, up to 300s for complex ones)
                api_timeout = timeout or 120.0  # Increased default from 30s to 120s

                # Retry mechanism with exponential backoff
                max_retries = 3
                last_error = None

                for attempt in range(max_retries):
                    try:
                        if attempt > 0:
                            wait_time = (
                                2**attempt
                            )  # Exponential backoff: 2, 4, 8 seconds
                            logger.info(
                                f"Retry attempt {attempt + 1}/{max_retries} after {wait_time}s wait..."
                            )
                            await asyncio.sleep(wait_time)
                            # Increase timeout for retries
                            api_timeout = min(api_timeout * 1.5, 300.0)

                        api_params = {
                            "model": self.config.model,
                            "messages": messages,
                            "temperature": temperature or self.config.temperature,
                            "max_tokens": max_tokens or self.config.max_tokens,
                        }
                        if response_format:
                            api_params["response_format"] = response_format

                        response = await asyncio.wait_for(
                            self.client.chat.completions.create(**api_params),
                            timeout=api_timeout,
                        )
                        content = response.choices[0].message.content
                        if not content:
                            logger.warning(
                                f"OpenAI returned empty response for model {self.config.model}"
                            )
                            logger.debug(f"Full response: {response}")
                        return content or ""

                    except asyncio.TimeoutError as e:
                        last_error = e
                        if attempt < max_retries - 1:
                            logger.warning(
                                f"OpenAI API call timed out after {api_timeout}s (attempt {attempt + 1}/{max_retries})"
                            )
                            continue
                        else:
                            logger.error(
                                f"OpenAI API call failed after {max_retries} attempts"
                            )
                            return f"Error: OpenAI API call timed out after {max_retries} attempts. The task may be too complex. Consider breaking it into smaller parts."
                    except Exception as e:
                        last_error = e
                        logger.error(f"OpenAI API error on attempt {attempt + 1}: {e}")
                        if "rate_limit" in str(e).lower():
                            # For rate limit errors, wait longer
                            await asyncio.sleep(10 * (attempt + 1))
                            continue
                        else:
                            # For other errors, fail immediately
                            break

                # If we get here, all retries failed
                return f"Error calling OpenAI API after {max_retries} attempts: {str(last_error)}"

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"Error calling OpenAI API: {str(e)}"

    async def _stream_completion(
        self, messages: list[dict[str, str]], temperature: float, max_tokens: int
    ) -> AsyncGenerator[str, None]:
        """
        Stream completion from OpenAI
        """
        try:
            stream = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield f"Error: {str(e)}"

    async def analyze_task_complexity(self, task: str) -> dict[str, Any]:
        """
        Analyze task complexity using GPT-5
        """
        system_prompt = """
        Analyze the following task and determine:
        1. Complexity level (simple, moderate, complex)
        2. Estimated subtask count
        3. Required agent types
        4. Whether tasks can be parallelized
        5. Estimated duration in minutes

        Return as JSON format.
        """

        prompt = f"""
        Task: {task}

        Provide analysis in this JSON format:
        {{
            "complexity": "simple|moderate|complex",
            "subtask_count": number,
            "required_agents": ["agent1", "agent2"],
            "parallelizable": true/false,
            "estimated_duration": number,
            "reasoning": "explanation"
        }}
        """

        response = await self.complete(prompt, system_prompt)

        try:
            import json

            return json.loads(response)
        except (json.JSONDecodeError, TypeError) as e:
            logger.debug(f"Could not parse complexity analysis response: {e}")
            # Fallback to simple heuristic
            return {
                "complexity": "moderate",
                "subtask_count": 3,
                "required_agents": ["architect", "codesmith"],
                "parallelizable": True,
                "estimated_duration": 10,
                "reasoning": "Could not parse AI response",
            }

    async def generate_code(
        self, specification: str, language: str = "python", context: str | None = None
    ) -> str:
        """
        Generate code based on specification
        """
        system_prompt = f"""
        You are an expert {language} programmer.
        Generate clean, well-documented code.
        Follow best practices and include error handling.
        """

        prompt = f"""
        Language: {language}

        Specification:
        {specification}

        {"Context: " + context if context else ""}

        Generate the complete code:
        """

        return await self.complete(prompt, system_prompt)

    async def get_completion(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> str:
        """
        Get completion from OpenAI (alias for complete method)
        This method matches the interface used by OrchestratorAgentV2
        """
        return await self.complete(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
            timeout=timeout,
        )

    def is_available(self) -> bool:
        """Check if service is available"""
        return self.client is not None
