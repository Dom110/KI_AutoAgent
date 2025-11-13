import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

logger = logging.getLogger("agent.llm_provider")

T = TypeVar('T')


@dataclass
class LLMResponse:
    """Response from LLM provider."""
    
    content: str
    provider: str
    model: str
    completion_tokens: int = 0
    prompt_tokens: int = 0
    total_tokens: int = 0
    response_time_ms: float = 0.0
    
    @property
    def total_content_length(self) -> int:
        """Get total content length."""
        return len(self.content)
    
    def __str__(self) -> str:
        return (
            f"LLMResponse({self.provider}:{self.model}, "
            f"content_len={self.total_content_length}, "
            f"tokens={self.total_tokens}, "
            f"time={self.response_time_ms}ms)"
        )


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    Each provider (OpenAI, Anthropic, etc.) must implement:
    - generate_text(): Generate text completion
    - validate_api_key(): Check if API key is valid
    """
    
    def __init__(
        self,
        model: str,
        temperature: float = 0.4,
        max_tokens: int = 2000,
        timeout_seconds: int = 30,
    ):
        """
        Initialize LLM provider.
        
        Args:
            model: Model name/ID
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            timeout_seconds: Timeout for API calls
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        
        logger.debug(
            f"🔧 Initializing {self.__class__.__name__}: "
            f"model={model}, temp={temperature}, tokens={max_tokens}"
        )
    
    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """
        Generate text completion.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            
        Returns:
            LLMResponse with generated text
            
        Raises:
            ValueError: If API key is invalid
            TimeoutError: If request times out
            Exception: For other API errors
        """
        pass
    
    @abstractmethod
    async def validate_api_key(self) -> bool:
        """
        Validate that API key is present and valid.
        
        Returns:
            True if valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider name (e.g., 'openai', 'anthropic')."""
        pass
    
    async def _with_timeout(
        self,
        coro,
        timeout_seconds: int | None = None,
    ):
        """
        Execute async function with timeout.
        
        Args:
            coro: Coroutine to execute
            timeout_seconds: Timeout in seconds (uses self.timeout_seconds if None)
            
        Returns:
            Result of coroutine
            
        Raises:
            asyncio.TimeoutError: If timeout exceeded
        """
        timeout = timeout_seconds or self.timeout_seconds
        logger.debug(f"⏳ Setting timeout to {timeout}s")
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"❌ API call timed out after {timeout}s")
            raise
    
    def _log_request(self, prompt: str, system_prompt: str | None = None) -> None:
        """Log the LLM request."""
        logger.debug(f"📤 LLM Request to {self.get_provider_name()}:{self.model}")
        logger.debug(f"   Prompt ({len(prompt)} chars): {prompt[:100]}...")
        if system_prompt:
            logger.debug(f"   System prompt ({len(system_prompt)} chars): {system_prompt[:100]}...")
    
    def _log_response(self, response: LLMResponse) -> None:
        """Log the LLM response."""
        logger.info(f"✅ {response}")
        logger.debug(f"   Content: {response.content[:200]}...")
    
    async def generate_text_with_retries(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_retries: int = 3,
        retry_delay_seconds: float = 1.0,
    ) -> LLMResponse:
        """
        Generate text with automatic retry on rate limit.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            max_retries: Maximum number of retries
            retry_delay_seconds: Delay between retries
            
        Returns:
            LLMResponse with generated text
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"📤 Calling {self.get_provider_name()} (attempt {attempt + 1}/{max_retries})")
                response = await self.generate_text(prompt, system_prompt)
                self._log_response(response)
                return response
            except Exception as e:
                last_error = e
                error_name = type(e).__name__
                logger.warning(f"⚠️  Attempt {attempt + 1} failed: {error_name}: {str(e)}")
                
                if attempt < max_retries - 1:
                    wait_time = retry_delay_seconds * (2 ** attempt)
                    logger.info(f"⏳ Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
        
        logger.error(f"❌ All {max_retries} attempts failed")
        raise last_error
    
    async def generate_structured_output(
        self,
        prompt: str,
        output_model: type[T],
        system_prompt: str | None = None,
        max_retries: int = 3,
    ) -> T:
        """
        Generate text and parse as structured Pydantic model.
        
        ✨ Phase 3 Pattern: Use this for agents that need structured outputs
        (like Supervisor routing decisions).
        
        Args:
            prompt: The user prompt
            output_model: Pydantic BaseModel class to parse into
            system_prompt: Optional system prompt
            max_retries: Maximum number of retries
            
        Returns:
            Instance of output_model with parsed response
            
        Raises:
            json.JSONDecodeError: If response is not valid JSON
            ValueError: If parsed JSON doesn't match model
            
        Example:
            ```python
            from pydantic import BaseModel
            
            class Decision(BaseModel):
                action: str
                confidence: float
            
            decision = await provider.generate_structured_output(
                prompt="Decide what to do",
                output_model=Decision,
                system_prompt="You are a decision maker"
            )
            print(decision.action)  # Type-safe!
            ```
        """
        logger.info(f"🏗️ Generating structured output: {output_model.__name__}")
        logger.debug(f"   Provider: {self.get_provider_name()}")
        logger.debug(f"   Model: {self.model}")
        
        # Build JSON schema from Pydantic model
        schema = output_model.model_json_schema()
        logger.debug(f"   Schema fields: {list(schema.get('properties', {}).keys())}")
        
        # Build schema instruction
        schema_instruction = (
            f"You MUST respond with ONLY valid JSON matching this schema:\n\n"
            f"```json\n{json.dumps(schema, indent=2)}\n```\n\n"
            f"CRITICAL: Respond with ONLY valid JSON. No explanations, no markdown, no text."
        )
        
        # Enhance system prompt
        if system_prompt:
            enhanced_system = f"{system_prompt}\n\n{schema_instruction}"
        else:
            enhanced_system = f"You are a JSON generator. Always respond with valid JSON.\n\n{schema_instruction}"
        
        logger.debug(f"📝 Enhanced system prompt ({len(enhanced_system)} chars)")
        
        # Call LLM with retries
        logger.info(f"📤 Requesting structured output...")
        response = await self.generate_text_with_retries(
            prompt=prompt,
            system_prompt=enhanced_system,
            max_retries=max_retries
        )
        
        logger.debug(f"✅ Got response: {response.total_tokens} tokens in {response.response_time_ms}ms")
        
        # Parse JSON response
        logger.info(f"🔍 Parsing JSON response...")
        
        # 🔧 FIX: Extract JSON from various formats (Markdown code blocks, wrapped text, etc.)
        content_to_parse = response.content
        
        # Try to parse directly first
        try:
            json_data = json.loads(content_to_parse)
            logger.debug(f"✅ Valid JSON parsed directly")
            logger.debug(f"   Keys: {list(json_data.keys())}")
        except json.JSONDecodeError:
            # Direct parse failed - try extraction from Markdown blocks
            logger.debug(f"🔧 Direct parse failed - attempting Markdown extraction...")
            
            # Look for ```json...``` blocks or just ```...```
            if "```" in content_to_parse:
                logger.debug(f"🔧 Detected Markdown code block - extracting JSON...")
                # Find the opening {
                json_start = content_to_parse.find('{')
                if json_start != -1:
                    # Find the matching closing } (should be the last one)
                    json_end = content_to_parse.rfind('}') + 1
                    if json_end > json_start:
                        content_to_parse = content_to_parse[json_start:json_end]
                        logger.debug(f"✅ Extracted JSON from Markdown blocks")
                        logger.debug(f"   Cleaned content ({len(content_to_parse)} chars): {content_to_parse[:100]}...")
                        
                        # Try parsing the extracted JSON
                        try:
                            json_data = json.loads(content_to_parse)
                            logger.debug(f"✅ Extracted JSON is valid")
                            logger.debug(f"   Keys: {list(json_data.keys())}")
                        except json.JSONDecodeError as e:
                            logger.error(f"❌ Extracted JSON is not valid")
                            logger.error(f"   Error: {str(e)}")
                            raise
                    else:
                        raise json.JSONDecodeError("No JSON braces found", content_to_parse, 0)
                else:
                    raise json.JSONDecodeError("No opening brace found", content_to_parse, 0)
            else:
                # No Markdown blocks, re-raise original error
                raise json.JSONDecodeError("Response is not valid JSON", content_to_parse, 0)
        
        # Validate with Pydantic model
        logger.info(f"✔️ Validating against {output_model.__name__}...")
        try:
            result = output_model(**json_data)
            logger.info(f"✅ Successfully parsed {output_model.__name__}")
            logger.debug(f"   Instance: {result}")
            return result
        except Exception as e:
            logger.error(f"❌ Validation failed: {type(e).__name__}")
            logger.error(f"   Error: {str(e)}")
            logger.debug(f"   JSON data: {json.dumps(json_data, indent=2)}")
            raise ValueError(f"Failed to parse response as {output_model.__name__}: {str(e)}")
