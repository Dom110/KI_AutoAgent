#!/usr/bin/env python3
"""
Minimal test script for v7.0 Supervisor Pattern

This script tests the core components without the full server.
It bypasses import issues to validate the architecture.
"""

import sys
import os
import asyncio
import logging

# Add backend to path
sys.path.insert(0, 'backend')
os.environ["OPENAI_API_KEY"] = "test-key-for-import"  # Mock key for testing

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def test_imports():
    """Test that all v7.0 components can import."""
    print("\n" + "="*60)
    print("TESTING V7.0 IMPORTS")
    print("="*60)

    # Test agent imports
    try:
        from agents.research_agent import ResearchAgent
        print("✅ ResearchAgent imports")
    except Exception as e:
        print(f"❌ ResearchAgent: {e}")

    try:
        from agents.architect_agent import ArchitectAgent
        print("✅ ArchitectAgent imports")
    except Exception as e:
        print(f"❌ ArchitectAgent: {e}")

    try:
        from agents.codesmith_agent import CodesmithAgent
        print("✅ CodesmithAgent imports")
    except Exception as e:
        print(f"❌ CodesmithAgent: {e}")

    try:
        from agents.reviewfix_agent import ReviewFixAgent
        print("✅ ReviewFixAgent imports")
    except Exception as e:
        print(f"❌ ReviewFixAgent: {e}")

    try:
        from agents.responder_agent import ResponderAgent
        print("✅ ResponderAgent imports")
    except Exception as e:
        print(f"❌ ResponderAgent: {e}")

    try:
        from agents.hitl_agent import HITLAgent
        print("✅ HITLAgent imports")
    except Exception as e:
        print(f"❌ HITLAgent: {e}")


async def test_supervisor():
    """Test supervisor creation and basic functionality."""
    print("\n" + "="*60)
    print("TESTING SUPERVISOR")
    print("="*60)

    try:
        # Direct import to bypass __init__.py
        import core.supervisor as sup
        print("✅ Supervisor module imports")

        # Check classes exist
        print(f"   AgentType enum: {sup.AgentType}")
        print(f"   SupervisorAction enum: {sup.SupervisorAction}")
        print(f"   SupervisorDecision model: {sup.SupervisorDecision}")

        # Try to create supervisor (will fail without real API key)
        try:
            supervisor = sup.create_supervisor()
            print("✅ Supervisor created (unexpected - no API key)")
        except Exception as e:
            if "api_key" in str(e).lower() or "openai" in str(e).lower():
                print("✅ Supervisor creation fails as expected (needs API key)")
            else:
                print(f"❌ Unexpected error: {e}")

    except Exception as e:
        print(f"❌ Supervisor test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_workflow_structure():
    """Test workflow structure without running it."""
    print("\n" + "="*60)
    print("TESTING WORKFLOW STRUCTURE")
    print("="*60)

    try:
        # Try to import workflow components
        from langgraph.graph import StateGraph, START, END
        from langgraph.types import Command
        print("✅ LangGraph imports work")

        # Check if we can build a minimal graph
        from typing import TypedDict

        class TestState(TypedDict):
            test: str

        graph = StateGraph(TestState)

        async def test_node(state):
            return {"test": "updated"}

        graph.add_node("test", test_node)
        graph.add_edge(START, "test")
        graph.add_edge("test", END)

        print("✅ Can build LangGraph workflow")

    except Exception as e:
        print(f"❌ Workflow structure test failed: {e}")


async def test_agent_execution():
    """Test individual agent execution."""
    print("\n" + "="*60)
    print("TESTING AGENT EXECUTION")
    print("="*60)

    # Test ResearchAgent
    try:
        from agents.research_agent import ResearchAgent
        agent = ResearchAgent()
        print("✅ ResearchAgent instantiated")

        # Test execute method signature
        import inspect
        sig = inspect.signature(agent.execute)
        print(f"   Execute signature: {sig}")

        # Try basic execution
        result = await agent.execute({
            "instructions": "Test research",
            "workspace_path": "/tmp/test"
        })
        print(f"   Result keys: {result.keys()}")
        print("✅ ResearchAgent executes")

    except Exception as e:
        print(f"❌ ResearchAgent execution: {e}")

    # Test ResponderAgent
    try:
        from agents.responder_agent import ResponderAgent
        agent = ResponderAgent()
        print("✅ ResponderAgent instantiated")

        result = await agent.execute({
            "instructions": "Format test response",
            "all_results": {
                "research_context": {"test": "data"},
                "architecture": {"components": []},
                "generated_files": [],
                "validation_results": {"passed": True}
            }
        })
        print(f"   Response length: {len(result.get('user_response', ''))}")
        print("✅ ResponderAgent executes")

    except Exception as e:
        print(f"❌ ResponderAgent execution: {e}")


async def test_server_import():
    """Test if server can import."""
    print("\n" + "="*60)
    print("TESTING SERVER IMPORT")
    print("="*60)

    try:
        # Set required env vars for server
        os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "test-key")

        from api.server_v7_supervisor import app, manager, WorkflowCallbacks
        print("✅ Server imports successfully")
        print(f"   FastAPI app: {app.title}")
        print(f"   Manager: {manager.__class__.__name__}")
        print(f"   Callbacks: {WorkflowCallbacks.__name__}")

    except Exception as e:
        print(f"❌ Server import failed: {e}")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("V7.0 SUPERVISOR PATTERN - MINIMAL TEST SUITE")
    print("="*60)

    await test_imports()
    await test_supervisor()
    await test_workflow_structure()
    await test_agent_execution()
    await test_server_import()

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print("""
Next steps:
1. Fix any import errors shown above
2. Set OPENAI_API_KEY environment variable
3. Start server: python backend/api/server_v7_supervisor.py
4. Run E2E tests: python e2e_test_v7_0_supervisor.py
""")


if __name__ == "__main__":
    asyncio.run(main())