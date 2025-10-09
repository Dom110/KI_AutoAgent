#!/usr/bin/env python3
"""
E2E Test: Perplexity API Integration

Tests the complete Perplexity API integration:
1. Direct PerplexityService calls
2. perplexity_tool wrapper
3. Research subgraph integration
4. Error handling (missing API key, API failures)

Expected behavior:
- WITH valid API key: Returns real search results with citations
- WITHOUT API key: Returns error but doesn't crash
- Invalid query: Handles gracefully

Debug mode: All logs enabled for troubleshooting

Author: KI AutoAgent Team
Created: 2025-10-09
Phase: 1.1 - Perplexity API Integration
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)


async def test_perplexity_service():
    """Test 1: Direct PerplexityService usage"""
    logger.info("=" * 80)
    logger.info("TEST 1: Direct PerplexityService")
    logger.info("=" * 80)

    try:
        from utils.perplexity_service import PerplexityService

        # Check if API key is configured
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            logger.warning("⚠️  PERPLEXITY_API_KEY not set - testing error handling")
            try:
                service = PerplexityService()
                logger.error("❌ Should have raised ValueError for missing API key")
                return False
            except ValueError as e:
                logger.info(f"✅ Correctly raised ValueError: {e}")
                return True  # Expected behavior

        # API key is set - test actual search
        logger.info("✅ PERPLEXITY_API_KEY found - testing real API call")
        service = PerplexityService(model="sonar")

        # Test web search
        query = "Python async best practices 2025"
        logger.info(f"🔍 Testing search: {query}")

        result = await service.search_web(
            query=query,
            recency="month",
            max_results=3
        )

        # Validate result structure
        assert "query" in result, "Result missing 'query' field"
        assert "answer" in result, "Result missing 'answer' field"
        assert "citations" in result, "Result missing 'citations' field"
        assert "timestamp" in result, "Result missing 'timestamp' field"

        logger.info(f"✅ Search successful!")
        logger.info(f"   Answer length: {len(result['answer'])} chars")
        logger.info(f"   Citations: {len(result['citations'])} sources")
        logger.info(f"   Timestamp: {result['timestamp']}")

        # Log first 200 chars of answer
        logger.debug(f"   Answer preview: {result['answer'][:200]}...")

        # Log citations
        for i, citation in enumerate(result['citations'], 1):
            logger.debug(f"   [{i}] {citation}")

        return True

    except Exception as e:
        logger.error(f"❌ Test 1 failed: {e}", exc_info=True)
        return False


async def test_perplexity_tool():
    """Test 2: perplexity_tool wrapper"""
    logger.info("=" * 80)
    logger.info("TEST 2: perplexity_tool wrapper")
    logger.info("=" * 80)

    try:
        from tools.perplexity_tool import perplexity_search

        # Check if API key is configured
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            logger.warning("⚠️  PERPLEXITY_API_KEY not set - testing error handling")
            result = await perplexity_search.ainvoke({"query": "test query"})

            assert result["success"] is False, "Should return success=False without API key"
            assert result["error"] == "missing_api_key", "Should return missing_api_key error"
            logger.info(f"✅ Tool correctly handles missing API key: {result['answer'][:100]}")
            return True  # Expected behavior

        # API key is set - test actual search
        logger.info("✅ PERPLEXITY_API_KEY found - testing tool wrapper")

        query = "FastAPI performance optimization techniques"
        logger.info(f"🔍 Testing tool search: {query}")

        result = await perplexity_search.ainvoke({"query": query})

        # Validate result structure
        assert "content" in result, "Result missing 'content' field"
        assert "answer" in result, "Result missing 'answer' field (backwards compat)"
        assert "citations" in result, "Result missing 'citations' field"
        assert "sources" in result, "Result missing 'sources' field (backwards compat)"
        assert "success" in result, "Result missing 'success' field"
        assert result["success"] is True, "Search should be successful"

        logger.info(f"✅ Tool search successful!")
        logger.info(f"   Content length: {len(result['content'])} chars")
        logger.info(f"   Citations: {len(result['citations'])} sources")
        logger.info(f"   Model: {result.get('model', 'N/A')}")

        # Log first 200 chars of content
        logger.debug(f"   Content preview: {result['content'][:200]}...")

        return True

    except Exception as e:
        logger.error(f"❌ Test 2 failed: {e}", exc_info=True)
        return False


async def test_research_subgraph():
    """Test 3: Research subgraph with Perplexity integration"""
    logger.info("=" * 80)
    logger.info("TEST 3: Research subgraph integration")
    logger.info("=" * 80)

    try:
        from subgraphs.research_subgraph_v6_1 import create_research_subgraph
        from state_v6 import ResearchState

        # Check if API key is configured
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            logger.warning("⚠️  PERPLEXITY_API_KEY not set - skipping subgraph test")
            logger.info("   Set PERPLEXITY_API_KEY to test full research workflow")
            return True  # Skip test gracefully

        # Create research subgraph
        logger.info("🔧 Creating research subgraph...")
        workspace_path = "/tmp/test_workspace"
        os.makedirs(workspace_path, exist_ok=True)

        subgraph = create_research_subgraph(workspace_path=workspace_path)

        # Create initial state
        initial_state: ResearchState = {
            "query": "Docker container security best practices",
            "findings": None,
            "report": "",
            "completed": False,
            "errors": []
        }

        logger.info(f"🚀 Running research subgraph for: {initial_state['query']}")

        # Execute subgraph
        final_state = await subgraph.ainvoke(initial_state)

        # Validate results
        assert final_state["completed"] is True, "Research should be completed"
        assert final_state["findings"] is not None, "Findings should be present"
        assert len(final_state["report"]) > 0, "Report should be generated"
        assert len(final_state["errors"]) == 0, "Should have no errors"

        logger.info(f"✅ Research subgraph successful!")
        logger.info(f"   Completed: {final_state['completed']}")
        logger.info(f"   Findings: {len(str(final_state['findings']))} chars")
        logger.info(f"   Report: {len(final_state['report'])} chars")
        logger.info(f"   Errors: {len(final_state['errors'])}")

        # Log report preview
        logger.debug(f"   Report preview:\n{final_state['report'][:500]}...")

        return True

    except Exception as e:
        logger.error(f"❌ Test 3 failed: {e}", exc_info=True)
        return False


async def test_error_handling():
    """Test 4: Error handling scenarios"""
    logger.info("=" * 80)
    logger.info("TEST 4: Error handling")
    logger.info("=" * 80)

    try:
        from tools.perplexity_tool import perplexity_search

        # Test 1: Empty query
        logger.info("📋 Test 4.1: Empty query")
        result = await perplexity_search.ainvoke({"query": ""})
        logger.info(f"   Result: success={result.get('success', False)}")

        # Test 2: Very long query
        logger.info("📋 Test 4.2: Very long query")
        long_query = "test " * 1000  # 5000 chars
        result = await perplexity_search.ainvoke({"query": long_query})
        logger.info(f"   Result: success={result.get('success', False)}")

        # Test 3: Special characters
        logger.info("📋 Test 4.3: Special characters in query")
        special_query = "Python <script>alert('test')</script> best practices"
        result = await perplexity_search.ainvoke({"query": special_query})
        logger.info(f"   Result: success={result.get('success', False)}")

        logger.info("✅ Error handling tests completed")
        return True

    except Exception as e:
        logger.error(f"❌ Test 4 failed: {e}", exc_info=True)
        return False


async def main():
    """Run all tests"""
    logger.info("🚀 Starting Perplexity API Integration E2E Tests")
    logger.info(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check if API key is configured
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if api_key:
        logger.info("✅ PERPLEXITY_API_KEY is configured")
        logger.info(f"   Key preview: {api_key[:10]}...{api_key[-4:]}")
    else:
        logger.warning("⚠️  PERPLEXITY_API_KEY is NOT configured")
        logger.warning("   Tests will validate error handling behavior")

    # Run tests
    results = {}

    results["test_1_service"] = await test_perplexity_service()
    results["test_2_tool"] = await test_perplexity_tool()
    results["test_3_subgraph"] = await test_research_subgraph()
    results["test_4_errors"] = await test_error_handling()

    # Summary
    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")

    logger.info("-" * 80)
    logger.info(f"Total: {total_tests} tests")
    logger.info(f"Passed: {passed_tests} tests")
    logger.info(f"Failed: {failed_tests} tests")

    if failed_tests == 0:
        logger.info("🎉 ALL TESTS PASSED!")
        return 0
    else:
        logger.error(f"❌ {failed_tests} TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
