#!/usr/bin/env python3
"""Test Claude CLI directly"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from adapters.claude_cli_simple import ClaudeCLISimple
from langchain_core.messages import HumanMessage, SystemMessage

async def main():
    print("🧪 Testing Claude CLI directly...")

    try:
        llm = ClaudeCLISimple(
            model="claude-sonnet-4-20250514",
            temperature=0.3,
            max_tokens=1024,
            agent_name="test",
            agent_description="Test agent",
            agent_tools=["Read", "Bash"],
            permission_mode="acceptEdits"
        )
        print("  ✅ LLM created")

        print("\n📡 Making Claude CLI call (10s timeout)...")
        result = await asyncio.wait_for(
            llm.ainvoke([
                SystemMessage(content="You are a helpful assistant."),
                HumanMessage(content="Say hello in exactly 3 words.")
            ]),
            timeout=10.0
        )

        print(f"  ✅ SUCCESS!")
        print(f"  Response: {result.content}")

    except asyncio.TimeoutError:
        print("  ❌ TIMEOUT after 10s!")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
