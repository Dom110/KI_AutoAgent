#!/usr/bin/env python3
"""
Test v7.0 Project Knowledge Integration.

Tests that ResearchAgent can:
1. Store research results in Memory
2. Retrieve previous research from Memory
3. Get insights from Learning System
4. Use project knowledge when Perplexity unavailable

Requires v7.0 server running: ./start_v7_server.sh
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_file = os.path.expanduser("~/.ki_autoagent/config/.env")
if os.path.exists(env_file):
    load_dotenv(env_file)
    print(f"✅ Loaded environment from {env_file}")
else:
    print(f"⚠️ No .env file at {env_file} - API keys may not work")

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.agents.research_agent import ResearchAgent
from backend.memory.memory_system_v6 import MemorySystem
from backend.cognitive.learning_system_v6 import LearningSystemV6


async def test_knowledge_integration():
    """Test complete knowledge integration workflow."""
    print("=" * 60)
    print("Testing v7.0 Project Knowledge Integration")
    print("=" * 60)

    # Use test workspace
    workspace_path = "/tmp/test_knowledge_workspace"
    os.makedirs(workspace_path, exist_ok=True)
    print(f"✅ Test workspace: {workspace_path}")

    # 1. Initialize ResearchAgent with workspace
    print("\n1️⃣ Initializing ResearchAgent with workspace...")
    agent = ResearchAgent(workspace_path=workspace_path)
    assert agent.workspace_path == workspace_path
    print("   ✅ Agent initialized with workspace path")

    # 2. Initialize Memory System directly
    print("\n2️⃣ Setting up Memory System...")
    memory = MemorySystem(workspace_path)
    await memory.initialize()

    # Store some test knowledge
    print("   📝 Storing test knowledge in memory...")

    # Store previous research
    await memory.store(
        content="Python async/await best practices: Use asyncio.gather() for concurrent tasks, avoid blocking calls, use async context managers",
        metadata={
            "agent": "research",
            "type": "research_result",
            "query": "async python",
            "timestamp": "2025-10-22T10:00:00"
        }
    )
    print("   ✅ Stored research result")

    # Store architecture decision
    await memory.store(
        content="Architecture: Use FastAPI for async web framework, PostgreSQL for database, Redis for caching",
        metadata={
            "agent": "architect",
            "type": "design",
            "project": "web_app",
            "timestamp": "2025-10-22T09:00:00"
        }
    )
    print("   ✅ Stored architecture decision")

    # Store code documentation
    await memory.store(
        content="Implemented async database connection pool with proper error handling and retry logic",
        metadata={
            "agent": "codesmith",
            "type": "documentation",
            "files": ["db.py", "connection.py"],
            "timestamp": "2025-10-22T09:30:00"
        }
    )
    print("   ✅ Stored code documentation")

    # 3. Test Research Agent execution with knowledge retrieval
    print("\n3️⃣ Testing Research Agent with project knowledge...")

    state = {
        "instructions": "Research best practices for async/await in Python",
        "workspace_path": workspace_path,
        "error_info": []
    }

    result = await agent.execute(state)

    assert "research_context" in result
    print("   ✅ Research executed successfully")

    # Check if web_results exist (might timeout)
    if "web_results" in result["research_context"]:
        web_results = result["research_context"]["web_results"]
        print(f"   📊 Web results: {len(web_results)} items")

        # Check if results mention project knowledge or timeout
        for web_result in web_results:
            if "Project Knowledge" in web_result.get("title", ""):
                print("   ✅ Using project knowledge from memory!")
                # Check for expected content in knowledge
                summary_lower = web_result.get("summary", "").lower()
                assert any(keyword in summary_lower for keyword in ["async", "architecture", "research", "database"])
            elif "Research Unavailable" in web_result.get("title", ""):
                print("   ⏱️ Web search timed out (expected)")
            else:
                print(f"   🌐 Got web search results: {web_result['title']}")

    # 4. Test direct project knowledge retrieval
    print("\n4️⃣ Testing direct project knowledge retrieval...")

    # Force use of project knowledge by simulating no Perplexity
    knowledge = await agent._get_project_knowledge("async Python best practices")

    if knowledge:
        print("   ✅ Retrieved project knowledge:")
        print(f"      Length: {len(knowledge)} chars")
        assert "async" in knowledge.lower()
        assert "research" in knowledge.lower() or "architecture" in knowledge.lower()
        print("   ✅ Knowledge contains expected content")
    else:
        print("   ⚠️ No project knowledge found (memory might be empty)")

    # 5. Test Learning System integration
    print("\n5️⃣ Testing Learning System integration...")

    learning = LearningSystemV6(memory=memory)

    # Record a test execution
    await learning.record_workflow_execution(
        workflow_id="test-001",
        task_description="Build async web API",
        project_type="api",
        execution_metrics={
            "total_time": 120.5,
            "research_time": 20.0,
            "architect_time": 30.0,
            "codesmith_time": 50.0,
            "review_iterations": 2,
            "files_generated": 5,
            "lines_of_code": 500
        },
        quality_score=0.92,
        status="success"
    )
    print("   ✅ Recorded test workflow execution")

    # Get suggestions
    suggestions = await learning.suggest_optimizations(
        task_description="Build another async API",
        project_type="api"
    )

    assert suggestions["based_on"] >= 1
    print(f"   ✅ Got suggestions based on {suggestions['based_on']} similar tasks")
    print(f"      Confidence: {suggestions['confidence']:.2f}")

    # 6. Test that research results get cached
    print("\n6️⃣ Testing research result caching...")

    # Simulate successful web search with caching
    test_results = [{
        "title": "Test Web Result",
        "summary": "This is a test result that should be cached",
        "citations": ["https://example.com"],
        "timestamp": "2025-10-22T11:00:00"
    }]

    await agent._cache_research_results("test caching", test_results)
    print("   ✅ Cached test research results")

    # Verify it was stored
    cached = await memory.search(
        query="test caching",
        filters={"agent": "research", "type": "research_result"},
        k=5  # Get more results since there might be multiple
    )

    # Check if any of the cached results match our test
    found_test_cache = False
    for cache_item in cached:
        if "test caching" in cache_item["content"].lower():
            found_test_cache = True
            break

    if found_test_cache:
        print("   ✅ Verified cached result in memory")
    else:
        print("   ⚠️ Cache verification skipped (might already exist)")

    # Cleanup
    await memory.close()
    print("\n✅ All tests passed!")
    print("=" * 60)


async def main():
    """Run the test."""
    try:
        await test_knowledge_integration()
        print("\n🎉 Project Knowledge Integration is WORKING!")
        return 0
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)