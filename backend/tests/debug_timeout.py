"""Debug timeout issue"""
import asyncio
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from workflow_v6 import WorkflowV6


async def debug():
    print("1. Creating temp workspace...")
    tmpdir = tempfile.mkdtemp()
    print(f"   Workspace: {tmpdir}")

    print("2. Creating WorkflowV6 instance...")
    workflow = WorkflowV6(workspace_path=tmpdir)
    print("   ✅ Instance created")

    print("3. Starting initialization...")
    print("   3a. Setup checkpointer...")
    await workflow._setup_checkpointer()
    print("   ✅ Checkpointer done")

    print("   3b. Setup memory...")
    await workflow._setup_memory()
    print("   ✅ Memory done")

    print("   3c. Build workflow graph...")
    # This is where it likely hangs
    print("      Calling workflow._build_workflow()...")
    import sys
    sys.stdout.flush()

    # Add timeout protection
    import signal

    def timeout_handler(signum, frame):
        print("      ⚠️ TIMEOUT in _build_workflow()!")
        raise TimeoutError("_build_workflow() hung")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(5)  # 5 second timeout

    try:
        workflow.workflow = workflow._build_workflow()
        signal.alarm(0)  # Cancel alarm
        print("      ✅ Workflow built!")
    except TimeoutError:
        print("      ❌ Timeout confirmed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(debug())
