import logging
import os
import time
from typing import Any

from .base import LLMProvider, LLMResponse

logger = logging.getLogger("agent.llm_provider")


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider implementation."""
    
    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.4,
        max_tokens: int = 2000,
        timeout_seconds: int = 30,
    ):
        """
        Initialize Anthropic provider.
        
        Args:
            model: Anthropic model name (e.g., 'claude-sonnet-4-20250514')
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
        return "anthropic"
    
    async def validate_api_key(self) -> bool:
        """
        Validate that Anthropic API key is present.
        
        Returns:
            True if API key is set
        """
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("❌ ANTHROPIC_API_KEY not set in environment")
            return False
        
        if not api_key.startswith("sk-ant-"):
            logger.warning(f"⚠️  ANTHROPIC_API_KEY doesn't start with 'sk-ant-' (starts with '{api_key[:7]}...')")
        
        logger.info("✅ ANTHROPIC_API_KEY is set")
        return True
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """
        Generate text using Anthropic API.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            
        Returns:
            LLMResponse with generated text
        """
        self._log_request(prompt, system_prompt)
        
        try:
            import anthropic
        except ImportError:
            logger.error("❌ Anthropic library not installed: pip install anthropic")
            raise
        
        if not await self.validate_api_key():
            raise ValueError("ANTHROPIC_API_KEY not set or invalid")
        
        client = anthropic.Anthropic()
        
        logger.debug(f"📤 Calling Anthropic with system_prompt: {system_prompt is not None}")
        
        start_time = time.time()
        try:
            response = await self._with_timeout(
                asyncio_wrapper=self._call_anthropic_async(
                    client=client,
                    model=self.model,
                    system=system_prompt,
                    prompt=prompt,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            content = response.get("content", "")
            
            llm_response = LLMResponse(
                content=content,
                provider="anthropic",
                model=self.model,
                completion_tokens=response.get("completion_tokens", 0),
                prompt_tokens=response.get("prompt_tokens", 0),
                total_tokens=response.get("total_tokens", 0),
                response_time_ms=elapsed_ms,
            )
            
            logger.info(f"✅ Anthropic response: {llm_response}")
            return llm_response
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"❌ Anthropic API error after {elapsed_ms}ms: {type(e).__name__}: {e}")
            raise
    
    async def _call_anthropic_async(
        self,
        client: Any,
        model: str,
        system: str | None,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """
        Call Anthropic API (convert sync call to async).
        
        Args:
            client: Anthropic client
            model: Model name
            system: System prompt
            prompt: User prompt
            temperature: Sampling temperature
            max_tokens: Max tokens
            
        Returns:
            Response dict with content and token counts
        """
        import asyncio
        
        def sync_call():
            try:
                response = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system if system else None,
                    messages=[{"role": "user", "content": prompt}],
                )
                
                content = response.content[0].text if response.content else ""
                
                return {
                    "content": content,
                    "completion_tokens": response.usage.output_tokens,
                    "prompt_tokens": response.usage.input_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                }
            except Exception as e:
                logger.error(f"❌ Sync Anthropic call failed: {e}")
                raise
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_call)
