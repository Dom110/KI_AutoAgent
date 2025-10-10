#!/usr/bin/env python3
"""Test Perplexity API directly"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
env_path = Path.home() / ".ki_autoagent" / "config" / ".env"
load_dotenv(env_path)

from utils.perplexity_service import PerplexityService

async def main():
    print("🧪 Testing Perplexity API directly...")

    try:
        service = PerplexityService(model="sonar")
        print("  ✅ Service created")

        print("\n📡 Making API call (30s timeout)...")
        result = await asyncio.wait_for(
            service.search_web("Python async"),
            timeout=30.0
        )

        print(f"  ✅ SUCCESS! Got {len(result['answer'])} chars")
        print(f"  Answer preview: {result['answer'][:200]}")

    except asyncio.TimeoutError:
        print("  ❌ TIMEOUT after 30s!")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
