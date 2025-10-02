"""
Simple Tetris Workflow Test - Direct execution
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("=" * 80)
print("🎮 TETRIS APP CREATION TEST")
print("=" * 80)
print()

async def main():
    try:
        print("1. Importing workflow...")
        from langgraph_system.workflow import create_agent_workflow
        print("   ✅ Workflow imported")

        print("\n2. Creating workflow instance...")
        workflow = create_agent_workflow()
        print("   ✅ Workflow created")

        print("\n3. Executing task: 'Entwickle eine Tetris Webapplikation'")
        print("   This will take a few minutes...")
        print()

        import logging
        logging.basicConfig(level=logging.INFO)

        print("   [DEBUG] Calling workflow.execute()...")
        final_state = await workflow.execute(
            task="Entwickle eine Tetris Webapplikation mit HTML5 Canvas",
            session_id="tetris_test",
            workspace_path="/tmp/tetris_agents"
        )
        print(f"   [DEBUG] workflow.execute() finished with status={final_state.get('status')}")

        print("\n" + "=" * 80)
        print("📊 RESULTS")
        print("=" * 80)

        # Show status
        status = final_state.get("status", "unknown")
        print(f"\nStatus: {status}")

        # Show errors if any
        errors = final_state.get("errors", [])
        if errors:
            print(f"\n❌ Errors ({len(errors)}):")
            for err in errors:
                print(f"   • {err}")

        # Show execution plan
        plan = final_state.get("execution_plan", [])
        if plan:
            print(f"\n📋 Execution Plan ({len(plan)} steps):")
            for i, step in enumerate(plan, 1):
                print(f"   {i}. {step.agent}: {step.status}")

        # Check for files
        workspace = "/tmp/tetris_agents"
        if os.path.exists(workspace):
            print(f"\n📁 Files created:")
            for root, dirs, files in os.walk(workspace):
                for file in files:
                    filepath = os.path.join(root, file)
                    print(f"   • {filepath}")

        print("\n" + "=" * 80)

        return status == "completed"

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
