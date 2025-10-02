"""
Tetris Workflow Test - Real Execution
"""
import asyncio
import sys
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.langgraph_system.workflow import create_agent_workflow

async def main():
    print("=" * 80)
    print("🎮 TETRIS WORKFLOW - LIVE TEST")
    print("=" * 80)

    # Create workflow
    workflow = create_agent_workflow()

    # Execute
    workspace_path = os.path.join(os.getcwd(), "agent_projects", "tetris_live")
    print("\n🚀 Starting workflow...")
    print("Task: Entwickle eine Tetris Webapplikation mit HTML5 Canvas")
    print(f"Workspace: {workspace_path}")
    print()

    try:
        final_state = await workflow.execute(
            task="Entwickle eine Tetris Webapplikation mit HTML5 Canvas",
            session_id="tetris_live",
            workspace_path=workspace_path
        )

        # Print execution plan
        print("\n" + "=" * 80)
        print("📊 EXECUTION PLAN")
        print("=" * 80)

        for i, step in enumerate(final_state.get('execution_plan', []), 1):
            status_emoji = {
                "completed": "✅",
                "failed": "❌",
                "in_progress": "⏳",
                "pending": "⏸️"
            }.get(step.status, "❓")

            print(f"\n{i}. [{status_emoji}] {step.agent.upper()}: {step.status}")
            print(f"   Task: {step.task[:100]}")

            if step.result:
                result_preview = str(step.result)[:200]
                print(f"   Result: {result_preview}...")

            if step.error:
                print(f"   ❌ Error: {step.error}")

        # Check for files
        print("\n" + "=" * 80)
        print("📁 FILES CREATED")
        print("=" * 80)

        workspace = workspace_path
        if os.path.exists(workspace):
            files_found = []
            for root, dirs, files in os.walk(workspace):
                for file in files:
                    full_path = os.path.join(root, file)
                    size = os.path.getsize(full_path)
                    files_found.append((full_path, size))

            if files_found:
                for path, size in files_found:
                    print(f"  ✅ {path} ({size} bytes)")
            else:
                print("  ❌ No files created!")
        else:
            print(f"  ❌ Workspace {workspace} doesn't exist!")

        # Summary
        print("\n" + "=" * 80)
        print("📈 SUMMARY")
        print("=" * 80)

        workflow_status = final_state.get("status", "unknown")
        total_steps = len(final_state.get('execution_plan', []))
        completed_steps = sum(1 for s in final_state.get('execution_plan', []) if s.status == "completed")
        failed_steps = sum(1 for s in final_state.get('execution_plan', []) if s.status == "failed")

        print(f"Workflow Status: {workflow_status}")
        print(f"Total Steps: {total_steps}")
        print(f"Completed: {completed_steps}")
        print(f"Failed: {failed_steps}")
        print(f"Files Created: {len(files_found) if 'files_found' in locals() else 0}")

        # Agent sequence
        agent_sequence = [s.agent for s in final_state.get('execution_plan', [])]
        print(f"\nAgent Sequence: {' → '.join(agent_sequence)}")

        # Check for collaboration
        has_reviewer = "reviewer" in agent_sequence
        has_fixer = "fixer" in agent_sequence

        if has_reviewer and has_fixer:
            print("\n🤝 COLLABORATION DETECTED!")
            print(f"  Reviewer executed: {agent_sequence.count('reviewer')} time(s)")
            print(f"  Fixer executed: {agent_sequence.count('fixer')} time(s)")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
