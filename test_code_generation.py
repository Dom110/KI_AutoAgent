#!/usr/bin/env python3
"""Test full code generation with corrected Claude CLI"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from adapters.use_claude_cli import use_claude_cli
use_claude_cli()

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

async def test():
    print("🧪 Testing Code Generation with Claude CLI...")
    print()

    # Change to test workspace
    test_workspace = "/Users/dominikfoert/TestApps/cliTest"
    os.makedirs(test_workspace, exist_ok=True)
    os.chdir(test_workspace)
    print(f"📁 Workspace: {test_workspace}")
    print()

    llm = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        temperature=0.2,
        max_tokens=4096,
        agent_name="codesmith",
        agent_description="Expert code generator following best practices",
        agent_tools=["Read", "Edit", "Bash"],
        permission_mode="acceptEdits"
    )

    system_prompt = """You are an expert code generator.

Generate clean, working code files.

CRITICAL: Use Edit tool to create files. Output exact file paths."""

    user_prompt = """Create a simple Python calculator:

Files to create:
1. calculator.py - Calculator class with add, subtract, multiply, divide
2. main.py - CLI interface to use the calculator
3. test_calculator.py - Basic tests

Use Edit tool to create each file."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    print("📤 Generating code...")
    response = await llm.ainvoke(messages)

    print(f"\n📥 Response received: {len(response.content)} chars")
    print(f"\n{response.content[:500]}...")
    print()

    # Check what files were created
    print("📂 Files created:")
    files = list(Path(test_workspace).glob("*.py"))
    if files:
        for f in files:
            print(f"   ✅ {f.name} ({f.stat().st_size} bytes)")
    else:
        print("   ❌ No files created")
    print()

    print("✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(test())
