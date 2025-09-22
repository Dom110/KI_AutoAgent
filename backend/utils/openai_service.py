"""
OpenAI Service Integration
Handles all OpenAI API calls for GPT-5 models
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class OpenAIConfig:
    """OpenAI configuration"""
    api_key: str
    model: str = "gpt-4o-2024-11-20"  # Updated to actual available model
    temperature: float = 0.7
    max_tokens: int = 4000
    streaming: bool = True

class OpenAIService:
    """
    OpenAI Service for GPT-4 models
    Used by: OrchestratorAgent, ArchitectAgent, DocuBot
    """

    def __init__(self, config: Optional[OpenAIConfig] = None):
        if config is None:
            config = OpenAIConfig(
                api_key=os.getenv("OPENAI_API_KEY", "")
            )

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
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
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
                    max_tokens or self.config.max_tokens
                )
            else:
                response = await self.client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    temperature=temperature or self.config.temperature,
                    max_tokens=max_tokens or self.config.max_tokens
                )

                return response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"Error calling OpenAI API: {str(e)}"

    async def _stream_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
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
                stream=True
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield f"Error: {str(e)}"

    async def analyze_task_complexity(
        self,
        task: str
    ) -> Dict[str, Any]:
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
        except:
            # Fallback to simple heuristic
            return {
                "complexity": "moderate",
                "subtask_count": 3,
                "required_agents": ["architect", "codesmith"],
                "parallelizable": True,
                "estimated_duration": 10,
                "reasoning": "Could not parse AI response"
            }

    async def generate_code(
        self,
        specification: str,
        language: str = "python",
        context: Optional[str] = None
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
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
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
            stream=False
        )

    def is_available(self) -> bool:
        """Check if service is available"""
        return self.client is not None