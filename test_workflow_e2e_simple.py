#!/usr/bin/env python3
"""Simple E2E Workflow Test - Research → Architect → Codesmith → ReviewFix"""

import asyncio
import sys
from pathlib import Path
import shutil

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
env_path = Path.home() / ".ki_autoagent" / "config" / ".env"
load_dotenv(env_path)

from adapters.use_claude_cli import use_claude_cli
use_claude_cli()

from workflow_v6_integrated import WorkflowV6Integrated

async def main():
    print("🧪 Testing FULL E2E Workflow (INTEGRATED v6)...")

    # Create fresh test workspace
    test_workspace = "/tmp/test_workflow_e2e"
    print(f"\n1️⃣ Setting up test workspace: {test_workspace}")

    # Clean up previous test
    if Path(test_workspace).exists():
        print("  🧹 Cleaning old test directory...")
        shutil.rmtree(test_workspace)

    Path(test_workspace).mkdir(parents=True)
    print("  ✅ Workspace created")

    print("\n2️⃣ Initializing WorkflowV6Integrated...")
    workflow = WorkflowV6Integrated(
        workspace_path=test_workspace,
        websocket_callback=None  # No WebSocket for test
    )

    print("  ⏳ Initializing all systems (this takes a moment)...")
    await workflow.initialize()
    print("  ✅ Workflow initialized")

    print("\n3️⃣ Running workflow (300s timeout)...")
    print("  Task: Build a simple calculator with tests")

    user_query = """Build a simple Python calculator with the following features:
- Basic operations: add, subtract, multiply, divide
- Handle division by zero
- Include unit tests
- Use Python 3.13+ with type hints
- Follow best practices"""

    try:
        result = await asyncio.wait_for(
            workflow.run(
                user_query=user_query,
                session_id="test_e2e_001"
            ),
            timeout=300.0  # 5 minutes
        )

        print("\n" + "="*80)
        print("✅ E2E WORKFLOW COMPLETE!")
        print("="*80)
        print(f"  Success: {result.get('success')}")
        print(f"  Execution Time: {result.get('execution_time', 0):.1f}s")
        print(f"  Quality Score: {result.get('quality_score', 0):.2f}")
        print(f"  Errors: {len(result.get('errors', []))}")

        # Show analysis
        if result.get('analysis'):
            analysis = result['analysis']
            print(f"\n📊 Analysis:")
            if analysis.get('classification'):
                c = analysis['classification']
                print(f"  Query Type: {c.get('type')}")
                print(f"  Complexity: {c.get('complexity')}")
                print(f"  Required Agents: {c.get('required_agents')}")

            if analysis.get('prediction'):
                p = analysis['prediction']
                print(f"  Predicted Duration: {p.get('estimated_duration', 0):.1f} min")
                print(f"  Risk Level: {p.get('risk_level')}")

        # Show generated files
        if result.get('result', {}).get('generated_files'):
            files = result['result']['generated_files']
            print(f"\n📁 Generated {len(files)} Files:")
            for file_info in files:
                print(f"  - {file_info.get('path')} ({file_info.get('size', 0)} bytes)")

        # Show adaptations
        if result.get('adaptations'):
            print(f"\n🔄 Workflow Adaptations:")
            for key, value in result['adaptations'].items():
                print(f"  {key}: {value}")

        # Show v6 systems usage
        if result.get('v6_systems_used'):
            active = [k for k, v in result['v6_systems_used'].items() if v]
            print(f"\n🧠 Active v6 Systems ({len(active)}):")
            for system in active:
                print(f"  ✓ {system}")

    except asyncio.TimeoutError:
        print("\n❌ TIMEOUT after 300s!")
        print("  E2E workflow took too long")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
