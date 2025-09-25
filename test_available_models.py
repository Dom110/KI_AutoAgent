#!/usr/bin/env python3
"""
Test which models are available from OpenAI, Anthropic, and Perplexity APIs
"""

import asyncio
import os
import json
from datetime import datetime

async def test_openai_models():
    """Get list of available OpenAI models"""
    from openai import AsyncOpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return []

    try:
        client = AsyncOpenAI(api_key=api_key)
        models = await client.models.list()

        print("\n📊 Available OpenAI Models:")
        print("-" * 80)

        gpt_models = []
        for model in models.data:
            if "gpt" in model.id.lower():
                gpt_models.append(model.id)
                created = datetime.fromtimestamp(model.created).strftime("%Y-%m-%d")
                print(f"  • {model.id} (created: {created})")

        # Sort by version/date
        gpt_models.sort(reverse=True)

        print(f"\n🎯 Latest GPT models:")
        for model in gpt_models[:5]:
            print(f"  ✅ {model}")

        # Test if GPT-5 exists
        gpt5_models = [m for m in gpt_models if "gpt-5" in m.lower()]
        if gpt5_models:
            print(f"\n🚀 GPT-5 Models Found:")
            for model in gpt5_models:
                print(f"  🎉 {model}")
        else:
            print("\n⚠️  No GPT-5 models found in available models")

        return gpt_models

    except Exception as e:
        print(f"❌ Error getting OpenAI models: {e}")
        return []

async def test_anthropic_models():
    """Get list of available Anthropic/Claude models"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n❌ ANTHROPIC_API_KEY not set")
        return []

    try:
        import anthropic

        # Anthropic doesn't have a list models endpoint, but we can try known models
        known_models = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3.5-sonnet-20241022",
            "claude-4-sonnet-20250514",
            "claude-4.1-sonnet-20250920",
            "claude-opus-4-1-20250805",
            "claude-4.1-opus-20250915",
            "claude-5-opus-20251001",  # Hypothetical
            "claude-5-sonnet-20251001"  # Hypothetical
        ]

        client = anthropic.AsyncAnthropic(api_key=api_key)

        print("\n📊 Testing Anthropic/Claude Models:")
        print("-" * 80)

        available_models = []
        for model_id in known_models:
            try:
                # Test with a minimal request
                response = await client.messages.create(
                    model=model_id,
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Hi"}]
                )
                print(f"  ✅ {model_id} - AVAILABLE")
                available_models.append(model_id)
            except anthropic.NotFoundError:
                print(f"  ❌ {model_id} - Not found")
            except anthropic.RateLimitError:
                print(f"  ⚠️  {model_id} - Rate limited (likely available)")
                available_models.append(model_id)
            except Exception as e:
                if "model_not_found" in str(e).lower() or "not found" in str(e).lower():
                    print(f"  ❌ {model_id} - Not available")
                else:
                    print(f"  ⚠️  {model_id} - Unknown status: {e}")

        return available_models

    except ImportError:
        print("\n❌ Anthropic library not installed")
        return []
    except Exception as e:
        print(f"\n❌ Error testing Anthropic models: {e}")
        return []

async def test_perplexity_models():
    """Test available Perplexity models"""
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("\n❌ PERPLEXITY_API_KEY not set")
        return []

    try:
        from openai import AsyncOpenAI

        # Perplexity uses OpenAI-compatible API
        client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.perplexity.ai"
        )

        known_models = [
            "llama-3.1-sonar-small-128k-online",
            "llama-3.1-sonar-large-128k-online",
            "llama-3.1-sonar-huge-128k-online",
            "perplexity-llama-3.1-sonar-huge-128k"
        ]

        print("\n📊 Testing Perplexity Models:")
        print("-" * 80)

        available_models = []
        for model_id in known_models:
            try:
                response = await client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=10
                )
                print(f"  ✅ {model_id} - AVAILABLE")
                available_models.append(model_id)
            except Exception as e:
                if "not found" in str(e).lower():
                    print(f"  ❌ {model_id} - Not available")
                else:
                    print(f"  ⚠️  {model_id} - Unknown status")

        return available_models

    except Exception as e:
        print(f"\n❌ Error testing Perplexity models: {e}")
        return []

async def test_gpt5_specifically():
    """Test GPT-5 models specifically"""
    from openai import AsyncOpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return

    client = AsyncOpenAI(api_key=api_key)

    # Potential GPT-5 model IDs to test
    gpt5_candidates = [
        "gpt-5",
        "gpt-5-turbo",
        "gpt-5-2025-09-12",
        "gpt-5-2025-09-20",
        "gpt-5-mini-2025-09-20",
        "gpt-5-preview",
        "gpt-5-32k"
    ]

    print("\n🔍 Testing GPT-5 Model Candidates:")
    print("-" * 80)

    for model_id in gpt5_candidates:
        try:
            response = await client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10
            )
            print(f"  🎉 {model_id} - WORKS! Response: {response.choices[0].message.content}")
        except Exception as e:
            error_str = str(e)
            if "model" in error_str.lower() and "does not exist" in error_str.lower():
                print(f"  ❌ {model_id} - Does not exist")
            elif "invalid" in error_str.lower():
                print(f"  ❌ {model_id} - Invalid model ID")
            else:
                print(f"  ⚠️  {model_id} - Error: {error_str[:100]}")

async def main():
    print("🚀 Model Availability Test")
    print("=" * 80)

    # Test all providers
    openai_models = await test_openai_models()
    await test_gpt5_specifically()
    anthropic_models = await test_anthropic_models()
    perplexity_models = await test_perplexity_models()

    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "openai": {
            "available": openai_models[:10],  # Top 10
            "gpt5_found": any("gpt-5" in m.lower() for m in openai_models)
        },
        "anthropic": {
            "available": anthropic_models
        },
        "perplexity": {
            "available": perplexity_models
        }
    }

    with open("available_models.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 80)
    print("✅ Results saved to available_models.json")

if __name__ == "__main__":
    asyncio.run(main())