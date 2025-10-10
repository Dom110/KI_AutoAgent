#!/usr/bin/env python3
"""Simple test of corrected Claude CLI integration"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from adapters.use_claude_cli import use_claude_cli
use_claude_cli()

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

async def test():
    print("🧪 Testing corrected Claude CLI integration...")
    print(f"   Model: claude-sonnet-4-20250514")
    print(f"   Tools: Read, Edit, Bash (NO Write!)")
    print(f"   Permission: acceptEdits")
    print()

    llm = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        temperature=0.2,
        max_tokens=2048,
        agent_name="test_codesmith",
        agent_description="Test code generator",
        agent_tools=["Read", "Edit", "Bash"],  # NO Write!
        permission_mode="acceptEdits"
    )

    messages = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content="Just say 'Hello, testing Claude CLI!' and nothing else.")
    ]

    print("📤 Invoking...")
    response = await llm.ainvoke(messages)

    print(f"\n📥 Response:")
    print(f"   Length: {len(response.content)} chars")
    print(f"   Content: {response.content}")
    print()
    print("✅ Test passed!")

if __name__ == "__main__":
    asyncio.run(test())
