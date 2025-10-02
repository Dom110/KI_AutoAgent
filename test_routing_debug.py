"""
Debug test to trace routing flow
"""

import asyncio
import sys
import os
import logging

# Setup logging to see all INFO messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def main():
    from langgraph_system.workflow import create_agent_workflow

    print("Creating workflow...")
    workflow = create_agent_workflow()

    print("\nTesting task: 'Entwickle eine Tetris Webapplikation'")
    print("=" * 80)

    # Just test the execution plan creation
    from langgraph_system.state import create_initial_state

    state = create_initial_state(
        session_id="debug_test",
        workspace_path="/tmp/debug_test"
    )
    state["messages"].append({
        "role": "user",
        "content": "Entwickle eine Tetris Webapplikation",
        "timestamp": "2025-10-02T00:00:00"
    })
    state["current_task"] = "Entwickle eine Tetris Webapplikation"

    # Test execution plan creation
    print("\n1. Creating execution plan...")
    plan = await workflow._create_execution_plan(state)

    print(f"\n✅ Plan created with {len(plan)} steps:")
    for i, step in enumerate(plan, 1):
        print(f"   {i}. {step.agent}: {step.task[:60]}... (status: {step.status})")

    print("\n" + "=" * 80)
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
