"""
Model Discovery Service - Automatically discovers available AI models from providers
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class ModelDiscoveryService:
    """Service to discover and cache available AI models from various providers"""

    def __init__(self):
        self.cache_file = os.path.join(os.path.expanduser("~/.ki_autoagent"), "available_models.json")
        self.cache_duration = timedelta(hours=24)  # Cache for 24 hours
        self.discovered_models = {}
        self.last_discovery = None
        self.model_descriptions = self._init_model_descriptions()

    async def discover_all_models(self, force_refresh: bool = False) -> Dict[str, List[str]]:
        """
        Discover all available models from all providers
        Returns dict with provider names as keys and model lists as values
        """
        # Check cache first
        if not force_refresh and self._is_cache_valid():
            logger.info("📦 Using cached model discovery results")
            return self.discovered_models

        logger.info("🔍 Starting model discovery from all providers...")

        results = {}

        # Discover OpenAI models
        openai_models = await self.discover_openai_models()
        if openai_models:
            results["openai"] = openai_models

        # Discover Anthropic models
        anthropic_models = await self.discover_anthropic_models()
        if anthropic_models:
            results["anthropic"] = anthropic_models

        # Discover Perplexity models
        perplexity_models = await self.discover_perplexity_models()
        if perplexity_models:
            results["perplexity"] = perplexity_models

        # Save to cache
        self.discovered_models = results
        self.last_discovery = datetime.now()
        self._save_cache()

        return results

    async def discover_openai_models(self) -> List[str]:
        """Discover available OpenAI models"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("⚠️ OPENAI_API_KEY not set - cannot discover OpenAI models")
            return self._get_default_openai_models()

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=api_key)
            models = await client.models.list()

            # Filter for GPT models and sort by version
            gpt_models = []
            for model in models.data:
                if "gpt" in model.id.lower():
                    gpt_models.append(model.id)

            gpt_models.sort(reverse=True)

            # Log discovery
            logger.info(f"✅ Discovered {len(gpt_models)} OpenAI GPT models")

            # Check for GPT-5 specifically
            gpt5_models = [m for m in gpt_models if "gpt-5" in m.lower()]
            if gpt5_models:
                logger.info(f"🎉 GPT-5 models available: {', '.join(gpt5_models)}")

            return gpt_models[:20]  # Return top 20 models

        except Exception as e:
            logger.error(f"❌ Failed to discover OpenAI models: {e}")
            return self._get_default_openai_models()

    async def discover_anthropic_models(self) -> List[str]:
        """Discover available Anthropic/Claude models"""

        # First try Claude CLI
        cli_models = await self._discover_claude_cli_models()
        if cli_models:
            logger.info(f"✅ Discovered {len(cli_models)} models via Claude CLI")
            return cli_models

        # Fall back to API discovery
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("⚠️ ANTHROPIC_API_KEY not set - cannot discover Anthropic models")
            return self._get_default_anthropic_models()

        # Test known models since Anthropic doesn't have a list endpoint
        test_models = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20241022",
            "claude-3.5-sonnet-20241022",
            "claude-4-sonnet-20250514",
            "claude-4.1-sonnet-20250920",
            "claude-opus-4-1-20250805",
            "claude-4.1-opus-20250915",
            "claude-5-opus-latest",
            "claude-5-sonnet-latest"
        ]

        available_models = []

        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=api_key)

            # Test each model with a minimal request
            for model_id in test_models:
                try:
                    await asyncio.wait_for(
                        client.messages.create(
                            model=model_id,
                            max_tokens=1,
                            messages=[{"role": "user", "content": "test"}]
                        ),
                        timeout=2.0
                    )
                    available_models.append(model_id)
                    logger.info(f"✅ Claude model available: {model_id}")
                except asyncio.TimeoutError:
                    # Timeout might mean it's available but slow
                    available_models.append(model_id)
                except Exception:
                    pass  # Model not available

            if not available_models:
                return self._get_default_anthropic_models()

            return available_models

        except ImportError:
            logger.warning("⚠️ Anthropic library not installed")
            return self._get_default_anthropic_models()
        except Exception as e:
            logger.error(f"❌ Failed to discover Anthropic models: {e}")
            return self._get_default_anthropic_models()

    async def discover_perplexity_models(self) -> List[str]:
        """Discover available Perplexity models"""
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            logger.warning("⚠️ PERPLEXITY_API_KEY not set - cannot discover Perplexity models")
            return self._get_default_perplexity_models()

        # Known Perplexity models to test
        test_models = [
            "llama-3.1-sonar-small-128k-online",
            "llama-3.1-sonar-large-128k-online",
            "llama-3.1-sonar-huge-128k-online",
            "perplexity-llama-3.1-sonar-huge-128k"
        ]

        available_models = []

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=api_key,
                base_url="https://api.perplexity.ai"
            )

            for model_id in test_models:
                try:
                    await asyncio.wait_for(
                        client.chat.completions.create(
                            model=model_id,
                            messages=[{"role": "user", "content": "test"}],
                            max_tokens=1
                        ),
                        timeout=2.0
                    )
                    available_models.append(model_id)
                    logger.info(f"✅ Perplexity model available: {model_id}")
                except:
                    pass  # Model not available

            if not available_models:
                return self._get_default_perplexity_models()

            return available_models

        except Exception as e:
            logger.error(f"❌ Failed to discover Perplexity models: {e}")
            return self._get_default_perplexity_models()

    def get_latest_models(self, provider: str, count: int = 3) -> List[str]:
        """Get the latest N models for a provider"""
        if provider not in self.discovered_models:
            return []

        models = self.discovered_models[provider]
        return models[:count]

    def get_recommended_model(self, provider: str, capability: str = "general") -> Optional[str]:
        """Get recommended model for a specific capability"""
        models = self.discovered_models.get(provider, [])
        if not models:
            return None

        # Capability-based recommendations
        if provider == "openai":
            if capability == "code":
                # Prefer GPT-4o or GPT-5 for code
                for model in models:
                    if "gpt-5" in model.lower() or "gpt-4o" in model.lower():
                        return model
            elif capability == "fast":
                # Prefer mini models for speed
                for model in models:
                    if "mini" in model.lower():
                        return model

        elif provider == "anthropic":
            if capability == "reasoning":
                # Prefer Opus for complex reasoning
                for model in models:
                    if "opus" in model.lower():
                        return model
            elif capability == "code":
                # Prefer Sonnet for code
                for model in models:
                    if "sonnet" in model.lower():
                        return model

        # Default to first/latest model
        return models[0] if models else None

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if not os.path.exists(self.cache_file):
            return False

        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)

            cache_time = datetime.fromisoformat(cache_data.get("timestamp", "2000-01-01"))
            if datetime.now() - cache_time > self.cache_duration:
                return False

            self.discovered_models = cache_data.get("models", {})
            self.last_discovery = cache_time
            return True

        except Exception:
            return False

    def _save_cache(self):
        """Save discovered models to cache file"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)

            cache_data = {
                "timestamp": self.last_discovery.isoformat(),
                "models": self.discovered_models
            }

            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)

            logger.info(f"💾 Model discovery results cached to {self.cache_file}")

        except Exception as e:
            logger.error(f"Failed to save model cache: {e}")

    def _get_default_openai_models(self) -> List[str]:
        """Return default OpenAI models when discovery fails"""
        return [
            "gpt-4o-2024-11-20",
            "gpt-4o-mini-2024-07-18",
            "gpt-4-turbo-preview",
            "gpt-4-1106-preview",
            "gpt-3.5-turbo-1106"
        ]

    def _get_default_anthropic_models(self) -> List[str]:
        """Return default Anthropic models when discovery fails"""
        return [
            "claude-3.5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]

    def _get_default_perplexity_models(self) -> List[str]:
        """Return default Perplexity models when discovery fails"""
        return [
            "llama-3.1-sonar-huge-128k-online",
            "llama-3.1-sonar-large-128k-online",
            "llama-3.1-sonar-small-128k-online"
        ]

    def _init_model_descriptions(self) -> Dict[str, Dict[str, str]]:
        """Initialize model descriptions for all known models"""
        return {
            # OpenAI Models
            "gpt-5": {
                "name": "GPT-5",
                "description": "Latest flagship model with superior reasoning",
                "capabilities": "Complex reasoning, multi-step planning, code generation",
                "context": "128K tokens",
                "speed": "Medium"
            },
            "gpt-5-turbo": {
                "name": "GPT-5 Turbo",
                "description": "Optimized GPT-5 for faster responses",
                "capabilities": "Balance of speed and capability",
                "context": "128K tokens",
                "speed": "Fast"
            },
            "gpt-5-mini": {
                "name": "GPT-5 Mini",
                "description": "Lightweight GPT-5 for cost-effective operations",
                "capabilities": "Fast, affordable, good for simple tasks",
                "context": "32K tokens",
                "speed": "Very Fast"
            },
            "gpt-realtime": {
                "name": "GPT Realtime",
                "description": "Ultra-low latency model for real-time interactions",
                "capabilities": "Sub-second responses, streaming, live collaboration",
                "context": "32K tokens",
                "speed": "Ultra Fast"
            },
            "gpt-realtime-2025-08-28": {
                "name": "GPT Realtime (August 2025)",
                "description": "Latest realtime model with enhanced capabilities",
                "capabilities": "Live coding, pair programming, instant feedback",
                "context": "32K tokens",
                "speed": "Ultra Fast"
            },
            "gpt-audio": {
                "name": "GPT Audio",
                "description": "Multimodal model for audio understanding",
                "capabilities": "Speech recognition, voice synthesis, audio analysis",
                "context": "32K tokens",
                "speed": "Fast"
            },
            "gpt-audio-2025-08-28": {
                "name": "GPT Audio (August 2025)",
                "description": "Latest audio model with voice capabilities",
                "capabilities": "Real-time voice conversations, music analysis",
                "context": "32K tokens",
                "speed": "Fast"
            },
            "gpt-image-1": {
                "name": "GPT Image",
                "description": "Advanced image understanding and generation",
                "capabilities": "Image analysis, OCR, code screenshots, diagrams",
                "context": "32K tokens",
                "speed": "Medium"
            },
            "gpt-4o-2024-11-20": {
                "name": "GPT-4 Optimized",
                "description": "Optimized GPT-4 with improved speed and cost",
                "capabilities": "Excellent code generation, reliable for production",
                "context": "128K tokens",
                "speed": "Fast"
            },
            "gpt-4o-mini-2024-07-18": {
                "name": "GPT-4 Mini",
                "description": "Small, fast, affordable GPT-4 variant",
                "capabilities": "Quick responses, code review, simple tasks",
                "context": "128K tokens",
                "speed": "Very Fast"
            },
            # Claude Models
            "claude-3.5-sonnet-20241022": {
                "name": "Claude 3.5 Sonnet",
                "description": "Latest Claude model with excellent coding ability",
                "capabilities": "Superior code generation, complex reasoning",
                "context": "200K tokens",
                "speed": "Fast"
            },
            "claude-3-opus-20240229": {
                "name": "Claude 3 Opus",
                "description": "Most capable Claude model for complex tasks",
                "capabilities": "Deep reasoning, complex analysis, arbitration",
                "context": "200K tokens",
                "speed": "Slow"
            },
            "claude-3-sonnet-20240229": {
                "name": "Claude 3 Sonnet",
                "description": "Balanced Claude model for general use",
                "capabilities": "Good balance of speed and capability",
                "context": "200K tokens",
                "speed": "Medium"
            },
            "claude-3-haiku-20240307": {
                "name": "Claude 3 Haiku",
                "description": "Fast, lightweight Claude model",
                "capabilities": "Quick responses, simple tasks",
                "context": "200K tokens",
                "speed": "Very Fast"
            },
            # Perplexity Models
            "llama-3.1-sonar-huge-128k-online": {
                "name": "Perplexity Sonar Huge",
                "description": "Most capable web search model",
                "capabilities": "Real-time web search, current information",
                "context": "128K tokens",
                "speed": "Medium"
            },
            "llama-3.1-sonar-large-128k-online": {
                "name": "Perplexity Sonar Large",
                "description": "Large web search model",
                "capabilities": "Web search, good balance",
                "context": "128K tokens",
                "speed": "Fast"
            },
            "llama-3.1-sonar-small-128k-online": {
                "name": "Perplexity Sonar Small",
                "description": "Fast web search model",
                "capabilities": "Quick web searches",
                "context": "128K tokens",
                "speed": "Very Fast"
            }
        }

    def get_model_description(self, model_id: str) -> Dict[str, str]:
        """Get detailed description for a model"""
        return self.model_descriptions.get(model_id, {
            "name": model_id,
            "description": "AI Model",
            "capabilities": "General AI capabilities",
            "context": "Unknown",
            "speed": "Unknown"
        })

    async def _discover_claude_cli_models(self) -> List[str]:
        """Discover Claude models via Claude Code CLI"""
        try:
            import subprocess

            # Check if Claude CLI is installed
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return []

            # Claude CLI doesn't have a list models command yet,
            # but we can try known models with a test query
            known_models = [
                "claude-3-opus-20240229",
                "claude-3.5-sonnet-20241022",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ]

            available_models = []
            for model in known_models:
                try:
                    # Test if model works with minimal query
                    test_result = subprocess.run(
                        ["claude", "-m", model, "Say 'ok' if this model works"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )

                    if test_result.returncode == 0 and "ok" in test_result.stdout.lower():
                        available_models.append(model)
                        logger.info(f"✅ Claude CLI model available: {model}")
                except Exception:
                    continue

            return available_models

        except Exception as e:
            logger.debug(f"Claude CLI discovery failed: {e}")
            return []

# Global instance
_model_discovery_service = None

def get_model_discovery_service() -> ModelDiscoveryService:
    """Get or create the global model discovery service"""
    global _model_discovery_service
    if _model_discovery_service is None:
        _model_discovery_service = ModelDiscoveryService()
    return _model_discovery_service

async def discover_models_on_startup():
    """Discover models during application startup"""
    service = get_model_discovery_service()
    models = await service.discover_all_models()

    logger.info("=" * 80)
    logger.info("🤖 MODEL DISCOVERY RESULTS")
    logger.info("=" * 80)

    for provider, model_list in models.items():
        logger.info(f"\n{provider.upper()} ({len(model_list)} models):")
        for i, model in enumerate(model_list[:5]):  # Show top 5
            logger.info(f"  {i+1}. {model}")

    logger.info("=" * 80)
    return models