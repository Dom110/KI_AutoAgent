import logging
import os
import time
from typing import Any

from .base import LLMProvider, LLMResponse

logger = logging.getLogger("agent.llm_provider")


class OpenAIProvider(LLMProvider):
    """OpenAI API provider implementation."""
    
    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.4,
        max_tokens: int = 2000,
        timeout_seconds: int = 30,
    ):
        """
        Initialize OpenAI provider.
        
        Args:
            model: OpenAI model name (e.g., 'gpt-4o-2024-11-20')
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            timeout_seconds: Timeout for API calls
        """
        super().__init__(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_seconds=timeout_seconds,
        )
        self._api_key = None
        self._client = None
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return "openai"
    
    async def validate_api_key(self) -> bool:
        """
        Validate that OpenAI API key is present.
        
        Returns:
            True if API key is set
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("❌ OPENAI_API_KEY not set in environment")
            return False
        
        if not api_key.startswith("sk-"):
            logger.error("❌ OPENAI_API_KEY doesn't look like a valid key (should start with 'sk-')")
            return False
        
        logger.info("✅ OPENAI_API_KEY is set")
        return True
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """
        Generate text using OpenAI API.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            
        Returns:
            LLMResponse with generated text
        """
        self._log_request(prompt, system_prompt)
        
        try:
            from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError
        except ImportError:
            logger.error("❌ OpenAI library not installed: pip install openai")
            raise
        
        if not await self.validate_api_key():
            raise ValueError("OPENAI_API_KEY not set or invalid")
        
        client = AsyncOpenAI()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        logger.debug(f"📤 Calling OpenAI with {len(messages)} messages")
        
        start_time = time.time()
        try:
            response = await self._with_timeout(
                client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            content = response.choices[0].message.content or ""
            
            llm_response = LLMResponse(
                content=content,
                provider="openai",
                model=self.model,
                completion_tokens=response.usage.completion_tokens,
                prompt_tokens=response.usage.prompt_tokens,
                total_tokens=response.usage.total_tokens,
                response_time_ms=elapsed_ms,
            )
            
            logger.info(f"✅ OpenAI response: {llm_response}")
            return llm_response
            
        except RateLimitError as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"❌ Rate limit exceeded after {elapsed_ms}ms: {e}")
            raise
        except APIConnectionError as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"❌ Connection error after {elapsed_ms}ms: {e}")
            raise
        except APIError as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"❌ OpenAI API error after {elapsed_ms}ms: {e}")
            raise
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"❌ Unexpected error after {elapsed_ms}ms: {type(e).__name__}: {e}")
            raise
