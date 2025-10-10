#!/usr/bin/env python3
"""Test Codesmith Subgraph directly"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
env_path = Path.home() / ".ki_autoagent" / "config" / ".env"
load_dotenv(env_path)

from adapters.use_claude_cli import use_claude_cli
use_claude_cli()

from subgraphs.codesmith_subgraph_v6_1 import create_codesmith_subgraph

async def main():
    print("🧪 Testing Codesmith Subgraph directly...")

    # Create test directory
    test_workspace = "/tmp/test_codesmith"
    Path(test_workspace).mkdir(exist_ok=True)

    print(f"\n1️⃣ Creating subgraph (workspace: {test_workspace})...")
    subgraph = create_codesmith_subgraph(
        workspace_path=test_workspace,
        memory=None  # NO MEMORY for testing
    )
    print("  ✅ Subgraph created")

    print("\n2️⃣ Calling subgraph (60s timeout)...")

    # Simple design for testing
    design = """# Simple Calculator App

## Architecture
- Single Python file: calculator.py
- Simple command-line calculator
- Functions: add, subtract, multiply, divide

## Implementation Requirements
- Use Python 3.13+
- Include type hints
- Add docstrings
- Handle division by zero
"""

    try:
        result = await asyncio.wait_for(
            subgraph.ainvoke({
                "design": design,
                "generated_files": [],
                "implementation_summary": None,
                "completed": False,
                "errors": []
            }),
            timeout=60.0
        )

        print(f"  ✅ SUCCESS!")
        print(f"  Completed: {result.get('completed')}")
        print(f"  Files: {len(result.get('generated_files', []))}")
        print(f"  Errors: {result.get('errors', [])}")

        # Show generated files
        if result.get('generated_files'):
            print("\n📁 Generated Files:")
            for file_info in result['generated_files']:
                print(f"  - {file_info['path']} ({file_info['size']} bytes)")

    except asyncio.TimeoutError:
        print("  ❌ TIMEOUT after 60s!")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
