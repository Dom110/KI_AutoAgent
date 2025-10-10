#!/usr/bin/env python3
"""Test Architect Subgraph v6.1 directly"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
env_path = Path.home() / ".ki_autoagent" / "config" / ".env"
load_dotenv(env_path)

from adapters.use_claude_cli import use_claude_cli
use_claude_cli()

from subgraphs.architect_subgraph_v6_1 import create_architect_subgraph

async def main():
    print("🧪 Testing Architect Subgraph v6.1 directly...")

    # Create subgraph WITHOUT memory (memory might be the problem)
    print("\n1️⃣ Creating subgraph without memory...")
    subgraph = create_architect_subgraph(
        workspace_path="/tmp/test",
        memory=None  # NO MEMORY!
    )
    print("  ✅ Subgraph created")

    print("\n2️⃣ Calling subgraph (120s timeout)...")
    try:
        result = await asyncio.wait_for(
            subgraph.ainvoke({
                "user_requirements": "Create a simple REST API for task management with user authentication",
                "workspace_path": "/tmp/test",
                "research_context": {},
                "design": {},
                "tech_stack": [],
                "patterns": [],
                "diagram": "",
                "adr": "",
                "errors": []
            }),
            timeout=120.0
        )

        print(f"  ✅ SUCCESS!")
        print(f"  Has design: {bool(result.get('design'))}")
        print(f"  Has diagram: {bool(result.get('diagram'))}")
        print(f"  Has ADR: {bool(result.get('adr'))}")
        print(f"  Errors: {result.get('errors', [])}")

        # Print design preview
        design = result.get('design', {})
        if design and isinstance(design, dict):
            desc = design.get('description', '')
            if desc:
                print(f"\n  📝 Design preview (first 200 chars):")
                print(f"  {desc[:200]}...")

    except asyncio.TimeoutError:
        print("  ❌ TIMEOUT after 120s!")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
