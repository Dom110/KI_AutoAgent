#!/usr/bin/env python3
"""
Test script for Perplexity API integration
Tests the ResearchAgent with actual Perplexity API calls
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent / "backend" / ".env"
load_dotenv(env_path)
print(f"📁 Loading environment from: {env_path}")

async def test_perplexity_service():
    """Test PerplexityService directly"""
    print("\n" + "="*60)
    print("🧪 Testing PerplexityService directly")
    print("="*60)

    # Check if API key is set
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("❌ PERPLEXITY_API_KEY not set in environment")
        print("\n📝 To fix this, add to your environment:")
        print("export PERPLEXITY_API_KEY='your_api_key_here'")
        return False

    print(f"✅ PERPLEXITY_API_KEY found: {api_key[:10]}...")

    try:
        from backend.utils.perplexity_service import PerplexityService

        # Initialize service
        service = PerplexityService(model="sonar")
        print("✅ PerplexityService initialized")

        # Test connection
        if service.test_connection():
            print("✅ Connection test passed")
        else:
            print("❌ Connection test failed")
            return False

        # Test simple search
        print("\n🔍 Testing web search...")
        result = await service.search_web("What is Claude AI latest features 2025")

        if result and "answer" in result:
            print("✅ Web search successful!")
            print(f"📄 Response length: {len(result['answer'])} chars")
            print(f"📚 Citations: {len(result.get('citations', []))}")
            print(f"\n🔍 Sample response (first 200 chars):")
            print(result['answer'][:200] + "...")
            return True
        else:
            print("❌ Web search failed - no answer in result")
            return False

    except Exception as e:
        print(f"❌ Error testing PerplexityService: {e}")
        return False

async def test_research_agent():
    """Test ResearchAgent with Perplexity integration"""
    print("\n" + "="*60)
    print("🤖 Testing ResearchAgent with Perplexity")
    print("="*60)

    try:
        from backend.agents.specialized.research_agent import ResearchAgent
        from backend.agents.base.base_agent import TaskRequest

        # Initialize agent
        print("🔄 Initializing ResearchAgent...")
        agent = ResearchAgent()
        print("✅ ResearchAgent initialized")

        # Create test request
        request = TaskRequest(
            prompt="What are the latest best practices for Python async programming in 2025?",
            context={}
        )

        print("\n🔍 Executing research request...")
        result = await agent.execute(request)

        if result.status == "success":
            print("✅ Research completed successfully!")
            print(f"📄 Response length: {len(result.content)} chars")
            print(f"\n📝 Sample response (first 300 chars):")
            print(result.content[:300] + "...")
            return True
        else:
            print(f"❌ Research failed: {result.content}")
            return False

    except Exception as e:
        print(f"❌ Error testing ResearchAgent: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("\n🚀 Perplexity Integration Test Suite")
    print("="*60)

    # Test 1: PerplexityService
    service_test = await test_perplexity_service()

    # Test 2: ResearchAgent (only if service test passed)
    agent_test = False
    if service_test:
        agent_test = await test_research_agent()
    else:
        print("\n⏩ Skipping ResearchAgent test (PerplexityService failed)")

    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    print(f"PerplexityService: {'✅ PASSED' if service_test else '❌ FAILED'}")
    print(f"ResearchAgent: {'✅ PASSED' if agent_test else '❌ FAILED' if service_test else '⏩ SKIPPED'}")

    if service_test and agent_test:
        print("\n🎉 All tests passed! Perplexity integration is working.")
    else:
        print("\n⚠️ Some tests failed. Please check the error messages above.")
        if not os.getenv("PERPLEXITY_API_KEY"):
            print("\n💡 Tip: Make sure to set PERPLEXITY_API_KEY environment variable")

if __name__ == "__main__":
    asyncio.run(main())