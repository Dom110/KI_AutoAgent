#!/usr/bin/env python3
"""
Diagnostic test to see EXACTLY what Claude CLI returns when given JSON requirement
"""
import asyncio
import json
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from adapters.claude_cli_simple import ClaudeCLISimple
from langchain_core.messages import SystemMessage, HumanMessage


async def test_claude_json_output():
    """Test what Claude actually returns when asked for JSON"""
    
    # Create workspace
    import tempfile
    workspace_path = tempfile.mkdtemp(prefix="claude_test_")
    print(f"\n✓ Created test workspace: {workspace_path}")
    
    system_prompt = """You are an expert code reviewer.

Your task is to review code.

CRITICAL: After reviewing, return a JSON response with this structure:
```json
{
  "validation_passed": true,
  "fixed_files": ["list of files"],
  "remaining_errors": [],
  "tests_passing": ["list of tests"],
  "fix_summary": "summary"
}
```

Return ONLY the JSON. No other text."""

    user_prompt = """Please review this simple Python function:

```python
def add(a, b):
    return a + b
```

Is it valid? Return JSON."""

    # Create Claude instance
    llm = ClaudeCLISimple(
        model="claude-sonnet-4-20250514",
        temperature=0.3,
        max_tokens=2048,
        agent_name="test_json",
        agent_tools=["Read", "Edit", "Bash"],
        workspace_path=workspace_path
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    print("\n" + "="*80)
    print("SENDING TO CLAUDE:")
    print("="*80)
    print(f"System prompt:\n{system_prompt}")
    print(f"\nUser prompt:\n{user_prompt}")
    print("\n" + "="*80)
    print("CLAUDE RESPONSE:")
    print("="*80)

    try:
        response = await llm.ainvoke(messages)
        
        print(f"\nResponse type: {type(response)}")
        print(f"Response attributes: {dir(response)}")
        
        if hasattr(response, 'content'):
            content = response.content
        else:
            content = str(response)
        
        print(f"\nRaw content ({len(content)} chars):")
        print(f">>> {content}")
        
        print("\n" + "="*80)
        print("PARSING ATTEMPT:")
        print("="*80)
        
        # Try to extract JSON
        if "```json" in content:
            print("✓ Found markdown JSON block")
            json_str = content.split("```json\n")[1].split("\n```")[0]
            print(f"Extracted: {json_str[:200]}...")
            parsed = json.loads(json_str)
            print(f"✓ JSON parsed successfully!")
            print(f"✓ validation_passed = {parsed.get('validation_passed')}")
        else:
            print("✗ No markdown JSON block found")
            
            # Try direct parsing
            try:
                parsed = json.loads(content)
                print(f"✓ Direct JSON parse successful!")
                print(f"✓ validation_passed = {parsed.get('validation_passed')}")
            except json.JSONDecodeError as e:
                print(f"✗ Direct JSON parse failed: {e}")
                print(f"First 500 chars: {content[:500]}")
                
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_claude_json_output())