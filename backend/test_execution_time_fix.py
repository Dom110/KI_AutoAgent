#!/usr/bin/env python3
"""
Direct test for execution_time fix in backend directory
"""

import asyncio
import os
import sys

# Ensure we're in the backend directory
if not os.path.exists("agents"):
    print("❌ Error: Must run from backend directory")
    sys.exit(1)

from agents.agent_registry import AgentRegistry, TaskRequest


async def test_execution_time():
    """Test that execution_time is properly set even on errors"""
    print("🧪 Testing execution_time fix...")
    print("-" * 60)

    # Initialize registry
    registry = AgentRegistry()

    # Try to register OrchestratorAgentV2
    try:
        from agents.specialized.orchestrator_agent_v2 import \
            OrchestratorAgentV2

        orchestrator = OrchestratorAgentV2()
        await registry.register_agent(orchestrator)
        print("✅ OrchestratorAgentV2 registered")
    except Exception as e:
        print(f"⚠️  Could not register OrchestratorAgentV2: {e}")

    # Try to register ArchitectAgent
    try:
        from agents.specialized.architect_agent import ArchitectAgent

        architect = ArchitectAgent()
        await registry.register_agent(architect)
        print("✅ ArchitectAgent registered")
    except Exception as e:
        print(f"⚠️  Could not register ArchitectAgent: {e}")

    print(f"\n📦 Registered agents: {list(registry.agents.keys())}")
    print("-" * 60)

    # Test 1: Simple valid request
    print("\n🔹 Test 1: Valid request to existing agent")
    if "orchestrator" in registry.agents:
        request = TaskRequest(
            prompt="What agents are available in the system?", context={}
        )

        result = await registry.dispatch_task("orchestrator", request)
        print(f"  Status: {result.status}")
        print(f"  Execution time: {result.execution_time}")
        assert hasattr(result, "execution_time"), "Missing execution_time!"
        assert result.execution_time >= 0, "Invalid execution_time!"
        print("  ✅ execution_time properly set")
    else:
        print("  ⚠️  Skipped - orchestrator not available")

    # Test 2: Request to non-existent agent (should fallback)
    print("\n🔹 Test 2: Request to non-existent agent")
    request = TaskRequest(prompt="Test fallback behavior", context={})

    result = await registry.dispatch_task("non_existent_agent", request)
    print(f"  Status: {result.status}")
    print(f"  Execution time: {result.execution_time}")
    assert hasattr(result, "execution_time"), "Missing execution_time!"
    assert result.execution_time >= 0, "Invalid execution_time!"
    print("  ✅ execution_time properly set even with fallback")

    # Test 3: Infrastructure analysis (if architect available)
    if "architect" in registry.agents:
        print("\n🔹 Test 3: Infrastructure analysis request")
        request = TaskRequest(
            prompt="Was kann an der Infrastruktur verbessert werden?",
            context={"project_root": os.path.dirname(os.path.dirname(__file__))},
        )

        result = await registry.dispatch_task("architect", request)
        print(f"  Status: {result.status}")
        print(f"  Execution time: {result.execution_time}")
        assert hasattr(result, "execution_time"), "Missing execution_time!"
        assert result.execution_time >= 0, "Invalid execution_time!"
        print("  ✅ execution_time properly set for infrastructure analysis")

        if result.status == "success":
            print("\n  📊 Sample output (first 500 chars):")
            print(f"  {result.content[:500]}...")
    else:
        print("\n🔹 Test 3: Infrastructure analysis")
        print("  ⚠️  Skipped - architect not available")

    print("\n" + "=" * 60)
    print("✅ All execution_time tests passed!")
    print("The fixes are working correctly.")
    print("=" * 60)


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Execution Time Fix Test")
    print("=" * 60)
    asyncio.run(test_execution_time())
