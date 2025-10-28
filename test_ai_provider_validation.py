#!/usr/bin/env python
"""
Test AI Provider Validation

Tests the AI Factory provider validation without starting the full server.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
global_env = Path.home() / ".ki_autoagent" / "config" / ".env"
if global_env.exists():
    load_dotenv(global_env)
    print(f"✅ Loaded .env from: {global_env}")
else:
    print(f"❌ No .env found at: {global_env}")
    sys.exit(1)


async def test_provider_validation():
    """Test all configured AI providers."""
    print("\n" + "=" * 60)
    print("AI PROVIDER VALIDATION TEST")
    print("=" * 60)

    # Import AI Factory
    from backend.utils.ai_factory import AIFactory

    # Define agent configurations
    agent_configs = {
        "research": os.getenv("RESEARCH_AI_PROVIDER"),
        "architect": os.getenv("ARCHITECT_AI_PROVIDER"),
        "codesmith": os.getenv("CODESMITH_AI_PROVIDER"),
        "reviewfix": os.getenv("REVIEWFIX_AI_PROVIDER")
    }

    # Validate each configured agent
    validation_failed = False
    for agent_name, provider_name in agent_configs.items():
        print(f"\n🔍 Testing {agent_name.upper()}...")

        if not provider_name:
            print(f"  ❌ {agent_name.upper()}_AI_PROVIDER not configured!")
            validation_failed = True
            continue

        # Get model config
        model_key = f"{agent_name.upper()}_AI_MODEL"
        model = os.getenv(model_key)

        if not model:
            print(f"  ⚠️ {model_key} not set - using provider default")

        # Validate provider
        try:
            provider = AIFactory.get_provider_for_agent(agent_name)
            print(f"  ✅ Provider: {provider.provider_name} ({provider.model})")

            # Run validation check
            is_valid, message = await provider.validate_connection()

            if not is_valid:
                print(f"  ❌ Validation failed: {message}")
                validation_failed = True
            else:
                print(f"  ✅ Validation passed: {message}")

        except Exception as e:
            print(f"  ❌ Failed to initialize provider: {e}")
            validation_failed = True

    print("\n" + "=" * 60)
    if validation_failed:
        print("❌ VALIDATION FAILED - Some providers are not working")
        print("=" * 60)
        return False
    else:
        print("✅ ALL PROVIDERS VALIDATED SUCCESSFULLY")
        print("=" * 60)
        return True


if __name__ == "__main__":
    # Register providers first
    print("🏭 Registering AI providers...")
    try:
        from backend.utils import openai_provider
        from backend.utils import claude_cli_service
        from backend.utils import perplexity_provider
        print("✅ AI providers registered")
    except Exception as e:
        print(f"❌ Failed to register AI providers: {e}")
        sys.exit(1)

    # Run validation
    success = asyncio.run(test_provider_validation())
    sys.exit(0 if success else 1)
