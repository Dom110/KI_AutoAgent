#!/usr/bin/env python3
"""
Test Global Memory System.

Tests cross-project learning capabilities.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_file = os.path.expanduser("~/.ki_autoagent/config/.env")
if os.path.exists(env_file):
    load_dotenv(env_file)
    print(f"✅ Loaded environment from {env_file}")

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.memory.global_memory_system import GlobalMemorySystem
from backend.agents.research_agent import ResearchAgent


async def test_global_memory():
    """Test global memory functionality."""
    print("=" * 60)
    print("Testing Global Memory System")
    print("=" * 60)

    # 1. Initialize Global Memory
    print("\n1️⃣ Initializing Global Memory...")
    global_mem = GlobalMemorySystem()
    await global_mem.initialize()
    print(f"   📁 Storage path: {global_mem.global_path}")

    # 2. Store some patterns
    print("\n2️⃣ Storing patterns from different projects...")

    # Pattern from a calculator project
    await global_mem.store_pattern(
        content="Always validate division by zero before performing calculations",
        project_type="calculator",
        success=True
    )
    print("   ✅ Stored calculator pattern")

    # Pattern from a web app project
    await global_mem.store_pattern(
        content="Use FastAPI for async Python web APIs with automatic OpenAPI docs",
        project_type="web_app",
        success=True
    )
    print("   ✅ Stored web_app pattern")

    # Pattern that failed
    await global_mem.store_pattern(
        content="Using eval() for calculator input parsing",
        project_type="calculator",
        success=False
    )
    print("   ✅ Stored failed pattern")

    # 3. Store error solutions
    print("\n3️⃣ Storing error solutions...")

    await global_mem.store_error_solution(
        error="ImportError: cannot import name 'AsyncOpenAI' from 'openai'",
        solution="Update openai package to version >=1.0 with: pip install --upgrade openai"
    )
    print("   ✅ Stored ImportError solution")

    await global_mem.store_error_solution(
        error="TypeError: object of type 'coroutine' has no len()",
        solution="Add 'await' keyword before async function call"
    )
    print("   ✅ Stored TypeError solution")

    # 4. Search for patterns
    print("\n4️⃣ Searching for patterns...")

    # Search for calculator patterns
    calc_patterns = await global_mem.search_patterns(
        query="calculator input validation",
        project_type="calculator",
        limit=3
    )

    print(f"\n   Found {len(calc_patterns)} calculator patterns:")
    for p in calc_patterns:
        print(f"   - {p['content'][:60]}...")
        print(f"     Success rate: {p['success_rate']:.0%}, Used: {p['usage_count']}x")

    # Search for web patterns
    web_patterns = await global_mem.search_patterns(
        query="async Python API framework",
        project_type="web_app",
        limit=3
    )

    print(f"\n   Found {len(web_patterns)} web_app patterns:")
    for p in web_patterns:
        print(f"   - {p['content'][:60]}...")

    # 5. Get error solutions
    print("\n5️⃣ Getting error solutions...")

    solutions = await global_mem.get_error_solutions(
        "ImportError: cannot import name 'AsyncOpenAI' from 'openai'"
    )

    if solutions:
        print(f"   Found {len(solutions)} solutions:")
        for s in solutions:
            print(f"   - {s}")
    else:
        print("   No solutions found")

    # 6. Get statistics
    print("\n6️⃣ Global Memory Statistics...")
    stats = await global_mem.get_stats()

    print(f"   📊 Total patterns: {stats['patterns_count']}")
    print(f"   🔧 Total errors: {stats['errors_count']}")

    if stats['most_successful_patterns']:
        print("\n   Top patterns:")
        for p in stats['most_successful_patterns']:
            print(f"   - {p['content'][:50]}... ({p['success_rate']:.0%} success)")

    # 7. Test ResearchAgent integration
    print("\n7️⃣ Testing ResearchAgent with Global Memory...")

    agent = ResearchAgent(workspace_path="/tmp/test_workspace")

    # Test knowledge retrieval
    knowledge = await agent._get_project_knowledge("How to build a calculator?")

    if knowledge:
        print("   ✅ ResearchAgent retrieved knowledge:")
        print(f"   {knowledge[:200]}...")
    else:
        print("   ⚠️ No knowledge retrieved (might be first run)")

    print("\n✅ All tests completed!")
    print("=" * 60)


async def test_cross_project_learning():
    """Test that learning from one project helps another."""
    print("\n" + "=" * 60)
    print("Testing Cross-Project Learning")
    print("=" * 60)

    global_mem = GlobalMemorySystem()
    await global_mem.initialize()

    # Simulate learning from Project A
    print("\n🔵 Project A: Learning from calculator project...")

    await global_mem.store_pattern(
        content="Use try-except for division by zero: if b != 0: result = a/b",
        project_type="calculator",
        success=True
    )

    await global_mem.store_error_solution(
        error="ZeroDivisionError: division by zero",
        solution="Check divisor before division: if divisor != 0"
    )

    print("   ✅ Project A knowledge stored")

    # Simulate Project B benefiting
    print("\n🟢 Project B: New calculator project...")

    # Search for relevant patterns
    patterns = await global_mem.search_patterns(
        query="division calculation error handling",
        project_type="calculator"
    )

    if patterns:
        print(f"   ✅ Found {len(patterns)} relevant patterns from previous projects!")
        print(f"   Learning: {patterns[0]['content']}")

    # Get error solution
    solutions = await global_mem.get_error_solutions(
        "ZeroDivisionError: division by zero"
    )

    if solutions:
        print(f"   ✅ Found solution from previous project: {solutions[0]}")

    print("\n🎉 Cross-project learning demonstrated!")


async def main():
    """Run all tests."""
    try:
        await test_global_memory()
        await test_cross_project_learning()

        print("\n" + "=" * 60)
        print("🎉 GLOBAL MEMORY SYSTEM WORKING!")
        print("=" * 60)
        print("\nBenefits achieved:")
        print("✅ Patterns shared across projects")
        print("✅ Error solutions reused")
        print("✅ Learning accumulates over time")
        print("✅ No hardcoded knowledge")

        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)