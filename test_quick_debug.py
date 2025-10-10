#!/usr/bin/env python3
"""
Quick Debug Test - Minimal test to see where it hangs
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

# Load .env from global config
from dotenv import load_dotenv
env_path = Path.home() / ".ki_autoagent" / "config" / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded .env from {env_path}")
else:
    print(f"⚠️ No .env found at {env_path}")

# Activate Claude CLI (no ANTHROPIC_API_KEY needed)
from adapters.use_claude_cli import use_claude_cli
use_claude_cli()
print("✅ Claude CLI adapter activated")

from workflow_v6_integrated import WorkflowV6Integrated

async def main():
    """Quick minimal test."""
    print("\n" + "="*80)
    print("🔍 QUICK DEBUG TEST")
    print("="*80)

    workspace = "/Users/dominikfoert/TestApps/debugQuick"
    os.makedirs(workspace, exist_ok=True)

    print("\n1️⃣ Creating workflow...")
    workflow = WorkflowV6Integrated(
        workspace_path=workspace,
        websocket_callback=None
    )
    print("  ✅ Workflow object created")

    print("\n2️⃣ Initializing workflow (may take time)...")
    try:
        await asyncio.wait_for(workflow.initialize(), timeout=15.0)
        print("  ✅ Initialization complete")
    except asyncio.TimeoutError:
        print("  ❌ TIMEOUT during initialization!")
        return

    print("\n3️⃣ Running workflow (10s timeout)...")
    try:
        result = await asyncio.wait_for(
            workflow.run(
                user_query="Create hello.py that prints Hello World",
                session_id="test_quick"
            ),
            timeout=10.0
        )
        print(f"  ✅ Workflow returned: success={result.get('success')}")
    except asyncio.TimeoutError:
        print("  ❌ TIMEOUT during execution!")
        print(f"  Last completed agents: {workflow.current_session.get('completed_agents', [])}")
        print(f"  Current phase: {workflow.current_session.get('current_phase', 'unknown')}")
        return

    print("\n4️⃣ Done!")

if __name__ == "__main__":
    asyncio.run(main())
