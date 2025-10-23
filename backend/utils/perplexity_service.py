from __future__ import annotations

"""
PerplexityService - Service for Perplexity API integration
Handles web search and research queries using Perplexity's AI models
"""

import json
import logging
import os
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

import aiohttp

from backend.utils.rate_limiter import wait_for_provider

logger = logging.getLogger(__name__)


class PerplexityService:
    """
    Service for Perplexity API integration
    Provides web search and research capabilities
    """

    def __init__(self, model: str = "sonar"):
        """
        Initialize PerplexityService

        Args:
            model: Perplexity model to use
                - sonar-small-online (8B params, faster)
                - sonar-medium-online (70B params, balanced)
                - sonar (Latest/largest model, best quality)
        """
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not found in environment variables")

        self.model = model
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.info(f"✅ PerplexityService initialized with model: {model}")

    async def send_message(
        self,
        prompt: str,
        temperature: float = 0.5,
        max_tokens: int = 4000,
        stream: bool = False,
        search_domain_filter: list | None = None,
        return_citations: bool = True,
        search_recency_filter: str | None = None,
    ) -> dict[str, Any]:
        """
        Send a message to Perplexity API for web search

        Args:
            prompt: The search query or question
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            stream: Whether to stream the response
            search_domain_filter: List of domains to search within
            return_citations: Whether to return source citations
            search_recency_filter: Time filter ('hour', 'day', 'week', 'month', 'year')

        Returns:
            Response from Perplexity API with web search results
        """
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful research assistant that provides accurate, up-to-date information from web searches. Always cite sources when available.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
            "return_citations": return_citations,
        }

        # Add optional filters
        if search_domain_filter:
            payload["search_domain_filter"] = search_domain_filter
        if search_recency_filter:
            payload["search_recency_filter"] = search_recency_filter

        try:
            # ⏱️ RATE LIMITING: Wait if needed to respect rate limits
            wait_time = await wait_for_provider("perplexity")
            if wait_time > 0:
                logger.debug(f"⏸️ Rate limit: waited {wait_time:.2f}s for Perplexity")

            timeout = aiohttp.ClientTimeout(total=30.0)  # 30 second timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                ) as response:
                    if response.status == 200:
                        result = await response.json()

                        # Extract the response
                        content = (
                            result.get("choices", [{}])[0]
                            .get("message", {})
                            .get("content", "")
                        )
                        citations = result.get("citations", [])

                        return {
                            "content": content,
                            "citations": citations,
                            "model": self.model,
                            "usage": result.get("usage", {}),
                            "timestamp": datetime.now().isoformat(),
                        }
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Perplexity API error: {response.status} - {error_text}"
                        )
                        raise Exception(
                            f"Perplexity API error: {response.status} - {error_text}"
                        )

        except Exception as e:
            logger.error(f"Error calling Perplexity API: {e}")
            raise

    async def stream_message(
        self,
        prompt: str,
        temperature: float = 0.5,
        max_tokens: int = 4000,
        search_domain_filter: list | None = None,
        return_citations: bool = True,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a message response from Perplexity API

        Yields:
            Chunks of the response as they arrive
        """
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful research assistant that provides accurate, up-to-date information from web searches.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            "return_citations": return_citations,
        }

        if search_domain_filter:
            payload["search_domain_filter"] = search_domain_filter

        try:
            # ⏱️ RATE LIMITING: Wait if needed to respect rate limits
            wait_time = await wait_for_provider("perplexity")
            if wait_time > 0:
                logger.debug(f"⏸️ Rate limit: waited {wait_time:.2f}s for Perplexity streaming")

            timeout = aiohttp.ClientTimeout(total=30.0)  # 30 second timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                ) as response:
                    if response.status == 200:
                        async for line in response.content:
                            if line:
                                line = line.decode("utf-8").strip()
                                if line.startswith("data: "):
                                    data = line[6:]  # Remove "data: " prefix
                                    if data != "[DONE]":
                                        try:
                                            chunk = json.loads(data)
                                            content = (
                                                chunk.get("choices", [{}])[0]
                                                .get("delta", {})
                                                .get("content", "")
                                            )
                                            if content:
                                                yield content
                                        except json.JSONDecodeError:
                                            continue
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Perplexity API streaming error: {response.status} - {error_text}"
                        )
                        raise Exception(f"Perplexity API error: {response.status}")

        except Exception as e:
            logger.error(f"Error streaming from Perplexity API: {e}")
            raise

    async def search_web(
        self,
        query: str,
        domains: list | None = None,
        recency: str | None = None,
        max_results: int = 5,
    ) -> dict[str, Any]:
        """
        Perform a focused web search

        Args:
            query: Search query
            domains: Optional list of domains to search
            recency: Time filter ('hour', 'day', 'week', 'month', 'year')
            max_results: Maximum number of results to return

        Returns:
            Structured search results with citations
        """
        prompt = f"""Search the web for: {query}

Please provide:
1. A comprehensive answer based on current web information
2. Key findings organized by relevance
3. Source citations for all information
4. Latest trends or updates if applicable

Focus on returning the {max_results} most relevant and recent results."""

        result = await self.send_message(
            prompt=prompt,
            search_domain_filter=domains,
            search_recency_filter=recency,
            return_citations=True,
        )

        return {
            "query": query,
            "answer": result["content"],
            "citations": result.get("citations", []),
            "timestamp": result["timestamp"],
            "model": self.model,
            "filters": {"domains": domains, "recency": recency},
        }

    async def research_technology(
        self, technology: str, aspects: list = None
    ) -> dict[str, Any]:
        """
        Research a specific technology or library

        Args:
            technology: Name of the technology/library
            aspects: Specific aspects to research (e.g., ['performance', 'security', 'best practices'])

        Returns:
            Comprehensive research results
        """
        if not aspects:
            aspects = [
                "overview",
                "best practices",
                "common issues",
                "alternatives",
                "recent updates",
            ]

        prompt = f"""Research {technology} and provide information on:
{chr(10).join(f'- {aspect}' for aspect in aspects)}

Include:
- Official documentation insights
- Community best practices
- Recent developments (last 6 months)
- Common pitfalls and solutions
- Comparison with alternatives if relevant"""

        result = await self.send_message(
            prompt=prompt, search_recency_filter="month", return_citations=True
        )

        return {
            "technology": technology,
            "aspects": aspects,
            "research": result["content"],
            "citations": result.get("citations", []),
            "timestamp": result["timestamp"],
        }

    async def get_latest_best_practices(self, topic: str) -> dict[str, Any]:
        """
        Get latest best practices for a specific topic

        Args:
            topic: The topic to research best practices for

        Returns:
            Latest best practices with sources
        """
        prompt = f"""What are the latest best practices for {topic}?

Focus on:
1. Current industry standards (2024-2025)
2. Recommended approaches by experts
3. Tools and frameworks currently preferred
4. Security considerations
5. Performance optimizations
6. Common mistakes to avoid

Cite authoritative sources like official documentation, major tech blogs, and recognized experts."""

        result = await self.send_message(
            prompt=prompt, search_recency_filter="month", return_citations=True
        )

        return {
            "topic": topic,
            "best_practices": result["content"],
            "citations": result.get("citations", []),
            "timestamp": result["timestamp"],
            "recency": "last_month",
        }

    def test_connection(self) -> bool:
        """
        Test if Perplexity API connection works

        Returns:
            True if connection successful, False otherwise
        """
        try:
            import requests

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1,
                },
                timeout=5,
            )
            if response.status_code != 200:
                logger.error(
                    f"Connection test failed with status {response.status_code}: {response.text}"
                )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection test failed with exception: {e}")
            return False
