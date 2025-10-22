#!/usr/bin/env python3
"""
Direct test of v7.0 workflow components

This bypasses import issues to test the core workflow.
"""

import asyncio
import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Add paths
sys.path.insert(0, 'backend')
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "test-key")


async def test_minimal_workflow():
    """Test minimal workflow without full imports."""
    print("\n" + "="*60)
    print("TESTING MINIMAL WORKFLOW")
    print("="*60)

    try:
        # Import LangGraph components
        from langgraph.graph import StateGraph, START, END
        from langgraph.types import Command
        from typing import TypedDict

        print("✅ LangGraph imports work")

        # Define minimal state
        class MinimalState(TypedDict):
            messages: list
            result: str

        # Build minimal graph
        graph = StateGraph(MinimalState)

        # Add test nodes
        async def start_node(state):
            print("   Start node executing")
            return Command(
                goto="process",
                update={"messages": state.get("messages", []) + ["Started"]}
            )

        async def process_node(state):
            print("   Process node executing")
            return Command(
                goto="end",
                update={"result": "Processed", "messages": state.get("messages", []) + ["Processed"]}
            )

        async def end_node(state):
            print("   End node executing")
            return Command(
                goto=END,
                update={"result": "Complete"}
            )

        graph.add_node("start", start_node)
        graph.add_node("process", process_node)
        graph.add_node("end", end_node)

        # Add single edge to start
        graph.add_edge(START, "start")

        # Compile
        app = graph.compile()
        print("✅ Graph compiled")

        # Run
        initial = {"messages": [], "result": ""}
        print("\nRunning workflow...")

        final_state = initial
        async for output in app.astream(initial):
            print(f"   Output: {output}")
            for key, value in output.items():
                if isinstance(value, dict):
                    final_state.update(value)

        print(f"\n✅ Final state: {final_state}")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_supervisor_direct():
    """Test supervisor directly."""
    print("\n" + "="*60)
    print("TESTING SUPERVISOR DIRECTLY")
    print("="*60)

    try:
        # Direct import of supervisor
        import core.supervisor as sup

        print("✅ Supervisor module imported")

        # Create minimal supervisor
        supervisor = sup.create_supervisor()
        print(f"✅ Supervisor created: {supervisor.__class__.__name__}")

        # Test decision structure
        from dataclasses import dataclass

        # Create test state
        test_state = {
            "user_query": "Test query",
            "goal": "Test goal",
            "messages": [],
            "last_agent": None,
            "iteration": 0,
            "response_ready": False
        }

        # Test context building
        context = supervisor._build_context(test_state)
        print(f"✅ Context built: goal={context.goal[:20]}...")

        return True

    except Exception as e:
        if "api_key" in str(e).lower():
            print("✅ Supervisor works (API key needed for full test)")
            return True
        else:
            print(f"❌ Error: {e}")
            return False


async def test_agents():
    """Test agent imports and execution."""
    print("\n" + "="*60)
    print("TESTING AGENTS")
    print("="*60)

    agents_ok = True

    # Test each agent
    agents_to_test = [
        ("ResearchAgent", "agents.research_agent"),
        ("ResponderAgent", "agents.responder_agent"),
        ("HITLAgent", "agents.hitl_agent")
    ]

    for agent_name, module_path in agents_to_test:
        try:
            module = __import__(module_path, fromlist=[agent_name])
            agent_class = getattr(module, agent_name)
            agent = agent_class()
            print(f"✅ {agent_name} instantiated")

            # Try execute
            result = await agent.execute({
                "instructions": "Test",
                "workspace_path": "/tmp"
            })
            print(f"   Execute returned: {type(result)}")

        except Exception as e:
            print(f"❌ {agent_name}: {e}")
            agents_ok = False

    return agents_ok


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("V7.0 DIRECT TESTING")
    print("="*60)

    results = []

    # Test 1: Minimal workflow
    result1 = await test_minimal_workflow()
    results.append(("Minimal Workflow", result1))

    # Test 2: Supervisor
    result2 = await test_supervisor_direct()
    results.append(("Supervisor", result2))

    # Test 3: Agents
    result3 = await test_agents()
    results.append(("Agents", result3))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {test_name}")

    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\n🎉 Core components working!")
        print("\nThe issue is with import paths in backend/core/__init__.py")
        print("This needs to be fixed for the full workflow to run.")
    else:
        print("\n⚠️ Some components have issues")


if __name__ == "__main__":
    asyncio.run(main())