#!/usr/bin/env python3
"""Test ReviewFix Subgraph directly"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
env_path = Path.home() / ".ki_autoagent" / "config" / ".env"
load_dotenv(env_path)

from adapters.use_claude_cli import use_claude_cli
use_claude_cli()

from subgraphs.reviewfix_subgraph_v6_1 import create_reviewfix_subgraph
import os

async def main():
    print("🧪 Testing ReviewFix Subgraph directly...")

    # Use test workspace with generated calculator
    test_workspace = "/tmp/test_codesmith"

    print(f"\n1️⃣ Creating subgraph (workspace: {test_workspace})...")
    subgraph = create_reviewfix_subgraph(
        workspace_path=test_workspace,
        memory=None  # NO MEMORY for testing
    )
    print("  ✅ Subgraph created")

    print("\n2️⃣ Calling subgraph (120s timeout for review loop)...")

    # Check if calculator.py exists
    calc_path = os.path.join(test_workspace, "calculator.py")
    if not os.path.exists(calc_path):
        print(f"  ⚠️  WARNING: {calc_path} doesn't exist!")
        print("  Run test_codesmith_subgraph_direct.py first!")
        return

    try:
        result = await asyncio.wait_for(
            subgraph.ainvoke({
                "generated_files": [{"path": "calculator.py"}],
                "files_to_review": ["calculator.py"],
                "quality_score": 0.0,
                "feedback": None,
                "iteration": 0,
                "fixes_applied": None,
                "fixed_files": [],
                "errors": []
            }),
            timeout=120.0
        )

        print(f"  ✅ SUCCESS!")
        print(f"  Quality Score: {result.get('quality_score')}")
        print(f"  Iterations: {result.get('iteration')}")
        print(f"  Fixed Files: {len(result.get('fixed_files', []))}")
        print(f"  Errors: {result.get('errors', [])}")

        # Show feedback
        if result.get('feedback'):
            print("\n📝 Reviewer Feedback (first 500 chars):")
            print(result['feedback'][:500])

    except asyncio.TimeoutError:
        print("  ❌ TIMEOUT after 120s!")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
