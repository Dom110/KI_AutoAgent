#!/usr/bin/env python3
"""
E2E Test: Tool Registry v6

Tests dynamic tool discovery and management:
1. Auto-discover tools from filesystem
2. Register tools manually
3. Query tools by capability
4. Get tools for specific agent types
5. Compose tools for tasks

Expected behavior:
- Discovers all tools in tools/ directory
- Extracts metadata (parameters, description, capabilities)
- Matches tools to agent needs
- Composes optimal tool sets for tasks

Debug mode: All logs enabled

Author: KI AutoAgent Team
Created: 2025-10-09
Phase: 3.1 - Dynamic Tool Discovery
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)


async def test_tool_discovery():
    """Test 1: Auto-discover tools"""
    logger.info("=" * 80)
    logger.info("TEST 1: Tool Auto-Discovery")
    logger.info("=" * 80)

    try:
        from tools.tool_registry_v6 import ToolRegistryV6

        registry = ToolRegistryV6()
        discovered = await registry.discover_tools()

        logger.info(f"🔍 Discovery Results:")
        logger.info(f"   Tools found: {len(discovered)}")
        logger.info(f"   Tool names: {list(discovered.keys())}")

        # Should find at least perplexity_search and file tools
        assert len(discovered) >= 3, f"Expected at least 3 tools, got {len(discovered)}"
        
        # Check specific tools exist
        tool_names = list(discovered.keys())
        assert "perplexity_search" in tool_names, "Should find perplexity_search"
        
        logger.info("✅ Tool discovery works!")
        return True

    except Exception as e:
        logger.error(f"❌ Test 1 failed: {e}", exc_info=True)
        return False


async def test_tool_metadata():
    """Test 2: Tool metadata extraction"""
    logger.info("=" * 80)
    logger.info("TEST 2: Tool Metadata Extraction")
    logger.info("=" * 80)

    try:
        from tools.tool_registry_v6 import initialize_tool_registry

        registry = await initialize_tool_registry()
        
        # Get perplexity tool
        perplexity = registry.get_tool("perplexity_search")
        
        if perplexity:
            logger.info(f"🔧 Perplexity Tool Metadata:")
            logger.info(f"   Name: {perplexity.name}")
            logger.info(f"   Description: {perplexity.description[:100]}...")
            logger.info(f"   Parameters: {list(perplexity.parameters.keys())}")
            logger.info(f"   Capabilities: {perplexity.capabilities}")
            logger.info(f"   Async: {perplexity.async_tool}")
            
            # Validate
            assert perplexity.name == "perplexity_search"
            assert "query" in perplexity.parameters
            assert perplexity.async_tool is True
            assert "web_search" in perplexity.capabilities
        
        logger.info("✅ Metadata extraction works!")
        return True

    except Exception as e:
        logger.error(f"❌ Test 2 failed: {e}", exc_info=True)
        return False


async def test_tools_by_capability():
    """Test 3: Get tools by capability"""
    logger.info("=" * 80)
    logger.info("TEST 3: Query Tools by Capability")
    logger.info("=" * 80)

    try:
        from tools.tool_registry_v6 import get_tool_registry

        registry = get_tool_registry()
        await registry.discover_tools()
        
        # Get web search tools
        web_tools = registry.get_tools_by_capability("web_search")
        
        logger.info(f"🔍 Web Search Tools:")
        for tool in web_tools:
            logger.info(f"   - {tool.name}: {tool.description[:60]}...")
        
        assert len(web_tools) >= 1, "Should have at least one web search tool"
        
        # Get file write tools
        file_tools = registry.get_tools_by_capability("file_write")
        
        logger.info(f"📝 File Write Tools:")
        for tool in file_tools:
            logger.info(f"   - {tool.name}: {tool.description[:60]}...")
        
        logger.info("✅ Capability filtering works!")
        return True

    except Exception as e:
        logger.error(f"❌ Test 3 failed: {e}", exc_info=True)
        return False


async def test_tools_for_agent():
    """Test 4: Get tools for specific agent type"""
    logger.info("=" * 80)
    logger.info("TEST 4: Tools for Agent Types")
    logger.info("=" * 80)

    try:
        from tools.tool_registry_v6 import get_tool_registry

        registry = get_tool_registry()
        await registry.discover_tools()
        
        # Get tools for research agent
        research_tools = registry.get_tools_for_agent("research")
        
        logger.info(f"🔬 Research Agent Tools:")
        for tool in research_tools:
            logger.info(f"   - {tool.name}")
        
        assert len(research_tools) >= 1, "Research agent needs tools"
        
        # Get tools for codesmith agent
        codesmith_tools = registry.get_tools_for_agent("codesmith")
        
        logger.info(f"⚙️  Codesmith Agent Tools:")
        for tool in codesmith_tools:
            logger.info(f"   - {tool.name}")
        
        assert len(codesmith_tools) >= 1, "Codesmith agent needs tools"
        
        logger.info("✅ Agent-specific tool assignment works!")
        return True

    except Exception as e:
        logger.error(f"❌ Test 4 failed: {e}", exc_info=True)
        return False


async def test_task_composition():
    """Test 5: Compose tools for specific task"""
    logger.info("=" * 80)
    logger.info("TEST 5: Task-Specific Tool Composition")
    logger.info("=" * 80)

    try:
        from tools.tool_registry_v6 import get_tool_registry

        registry = get_tool_registry()
        await registry.discover_tools()
        
        # Task 1: Research task
        task1 = "Research the best Python web frameworks for 2025"
        tools1 = await registry.compose_tools_for_task(task1)
        
        logger.info(f"🔍 Tools for research task:")
        logger.info(f"   Task: {task1}")
        logger.info(f"   Tools: {[t.name for t in tools1]}")
        
        # Should include web search
        assert any("search" in t.name for t in tools1), "Research task needs search tool"
        
        # Task 2: Code generation task
        task2 = "Create a Python calculator application"
        tools2 = await registry.compose_tools_for_task(task2)
        
        logger.info(f"⚙️  Tools for code generation task:")
        logger.info(f"   Task: {task2}")
        logger.info(f"   Tools: {[t.name for t in tools2]}")
        
        # Should include file write
        tool_names2 = [t.name for t in tools2]
        assert any("write" in name for name in tool_names2), "Code task needs write tool"
        
        logger.info("✅ Task-specific composition works!")
        return True

    except Exception as e:
        logger.error(f"❌ Test 5 failed: {e}", exc_info=True)
        return False


async def main():
    logger.info("🚀 Starting Tool Registry v6 E2E Tests")
    logger.info(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}
    results["test_1_discovery"] = await test_tool_discovery()
    results["test_2_metadata"] = await test_tool_metadata()
    results["test_3_capability"] = await test_tools_by_capability()
    results["test_4_agent"] = await test_tools_for_agent()
    results["test_5_composition"] = await test_task_composition()

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
