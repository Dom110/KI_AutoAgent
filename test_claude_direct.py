#!/usr/bin/env python3
"""Direct test of Claude CLI adapter to debug JSONL parsing"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

# Activate Claude CLI adapter
from adapters.use_claude_cli import use_claude_cli
use_claude_cli()

# Now import ChatAnthropic (will use ClaudeCLISimple)
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

async def test_direct():
    """Test Claude CLI adapter directly"""
    print("🧪 Testing Claude CLI adapter directly...")

    llm = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        temperature=0.2,
        max_tokens=4096,
        agent_name="test_agent",
        agent_description="Test agent for debugging",
        agent_tools=["Read", "Write", "Bash"]
    )

    # Test with Codesmith-style prompt that generates multiple files
    system_prompt = """You are an expert code generator specializing in clean, maintainable code.

Your responsibilities:
1. Generate code based on architectural design
2. Follow best practices and design patterns
3. Write clean, well-documented code
4. Include error handling and type hints
5. Generate complete, runnable files

CRITICAL: You MUST follow this EXACT output format. Do NOT add any explanation or commentary.
Do NOT say "I've generated..." or "Here is the code...". ONLY output the format below:

FILE: <relative_path>
```<language>
<code content>
```

FILE: <next_file_path>
```<language>
<code content>
```

Example (this is the ONLY format allowed):
FILE: src/app.py
```python
def hello():
    print("Hello")
```

FILE: src/utils.py
```python
def helper():
    return 42
```

START YOUR RESPONSE WITH "FILE:" - Nothing else!"""

    user_prompt = """Generate code for a simple Task Manager app:

Requirements:
- Task class with id, title, description, completed status
- TaskManager class to add, remove, list, complete tasks
- Simple CLI interface (main.py)

Generate at least 3 files."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    print("📤 Invoking Claude CLI...")
    response = await llm.ainvoke(messages)

    print(f"\n📥 Response received:")
    print(f"   Content length: {len(response.content)} chars")
    print(f"   Content preview: {response.content[:500]}")

    return response

if __name__ == "__main__":
    asyncio.run(test_direct())
