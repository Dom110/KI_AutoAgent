"""
Demo Workflow Execution with Full Logging

Runs a simple workflow and shows all agent communications.

Usage:
    python demo_workflow.py
"""

import asyncio
import logging
import os
import sys
import tempfile

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

from workflow_v6 import WorkflowV6

# Setup comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/workflow_demo.log', mode='w')
    ]
)

# Set specific loggers to INFO to reduce noise
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('anthropic').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def main():
    """Run demo workflow with full logging."""
    print("=" * 80)
    print("🚀 KI AutoAgent v6.1 - Demo Workflow")
    print("=" * 80)
    print()

    # Create temp workspace
    with tempfile.TemporaryDirectory() as workspace:
        print(f"📂 Workspace: {workspace}")
        print()

        # Simple task
        user_query = """Create a simple Python greeter app:
1. A Greeter class with a greet(name) method
2. The method should return "Hello, {name}!"
3. A main() function that demonstrates usage
4. Save as greeter.py

Keep it very simple."""

        print("📝 User Query:")
        print("-" * 80)
        print(user_query)
        print("-" * 80)
        print()

        # Initialize workflow
        print("[Step 1] Initializing workflow...")
        workflow = WorkflowV6(workspace_path=workspace)
        await workflow.initialize()
        print("✅ Workflow initialized")
        print()

        # Run workflow
        print("[Step 2] Running workflow...")
        print("=" * 80)

        result = await workflow.run(user_query=user_query)

        print()
        print("=" * 80)
        print("✅ Workflow completed!")
        print()

        # Check results
        print("[Step 3] Checking generated files...")
        print("-" * 80)

        for root, dirs, files in os.walk(workspace):
            for file in files:
                if not file.startswith('.'):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, workspace)

                    print(f"\n📄 {rel_path}:")
                    print("=" * 80)

                    with open(filepath, 'r') as f:
                        content = f.read()

                    print(content)
                    print("=" * 80)

        print()
        print("🎉 Demo Complete!")
        print()
        print("💾 Full logs saved to: /tmp/workflow_demo.log")


if __name__ == "__main__":
    asyncio.run(main())
