#!/usr/bin/env python3
"""Test Research Subgraph directly"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
env_path = Path.home() / ".ki_autoagent" / "config" / ".env"
load_dotenv(env_path)

from adapters.use_claude_cli import use_claude_cli
use_claude_cli()

from subgraphs.research_subgraph_v6_1 import create_research_subgraph

async def main():
    print("🧪 Testing Research Subgraph directly...")

    # Create subgraph WITHOUT memory (memory might be the problem)
    print("\n1️⃣ Creating subgraph without memory...")
    subgraph = create_research_subgraph(
        workspace_path="/tmp/test",
        memory=None  # NO MEMORY!
    )
    print("  ✅ Subgraph created")

    print("\n2️⃣ Calling subgraph (40s timeout)...")
    try:
        result = await asyncio.wait_for(
            subgraph.ainvoke({
                "query": "Python async best practices",
                "findings": None,
                "report": None,
                "completed": False,
                "errors": []
            }),
            timeout=40.0
        )

        print(f"  ✅ SUCCESS!")
        print(f"  Completed: {result.get('completed')}")
        print(f"  Has findings: {bool(result.get('findings'))}")
        print(f"  Errors: {result.get('errors', [])}")

    except asyncio.TimeoutError:
        print("  ❌ TIMEOUT after 40s!")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
