#!/usr/bin/env python3
"""
Debug script to capture Claude's actual output from Codesmith

This script directly calls the MCP claude.claude_generate to see what it returns.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from mcp.mcp_client import MCPClient

async def debug_claude_output():
    """Call Claude directly to see what it generates."""

    workspace_path = str(Path.home() / "TestApps" / "ProgressTest")

    # Initialize MCP client
    mcp = MCPClient(workspace_path=workspace_path)
    await mcp.initialize()

    # Simple task
    task = "Add a docstring to the Python file"

    # Read the existing file
    app_file = Path(workspace_path) / "app.py"
    existing_code = app_file.read_text() if app_file.exists() else "# Simple Python app\nprint('Hello, World!')\n"

    print(f"📂 Workspace: {workspace_path}")
    print(f"📄 Existing app.py:\n{existing_code}")
    print(f"📝 Task: {task}")
    print("\n" + "="*80 + "\n")

    # Create the prompt (similar to codesmith_subgraph_v6_1.py)
    system_prompt = """You are an expert code generator for the KI AutoAgent system.

CRITICAL: You MUST follow this EXACT output format for EVERY file you generate:

FILE: <filepath>
```<language>
<file content>
```

RULES:
1. START YOUR RESPONSE WITH "FILE:" - Nothing else! No introduction, no explanation.
2. Use relative paths from workspace root (e.g., "app.py" not "/path/to/app.py")
3. Each file MUST be complete and functional
4. Multiple files are separated by exactly one blank line
5. Use appropriate language identifier (python, javascript, typescript, etc.)
6. File content must be properly indented

FORBIDDEN:
- NO explanatory text before "FILE:"
- NO comments outside code blocks
- NO markdown formatting except code blocks
- NO suggestions or alternatives after the code

START YOUR RESPONSE WITH "FILE:" - NOTHING ELSE!"""

    prompt = f"""Task: {task}

Workspace structure:
- app.py (existing file)

Current app.py content:
```python
{existing_code}
```

Generate the complete updated file(s) following the EXACT format specified."""

    print("🤖 Calling claude.claude_generate via MCP...")
    print(f"📋 System prompt length: {len(system_prompt)} chars")
    print(f"📋 User prompt length: {len(prompt)} chars")

    try:
        # Call Claude via MCP
        result = await mcp.call(
            server="claude",
            tool="claude_generate",
            arguments={
                "system_prompt": system_prompt,
                "prompt": prompt,
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 8000,
                "temperature": 0.2,
                "workspace_path": workspace_path
            }
        )

        print("\n✅ Response received!")
        print(f"📊 Response type: {type(result)}")

        if isinstance(result, dict):
            print(f"📊 Response keys: {list(result.keys())}")

            # Check for different possible response formats
            if 'content' in result:
                code_output = result['content']
                print(f"\n📄 Found 'content' key: {len(code_output)} chars")
            elif 'code' in result:
                code_output = result['code']
                print(f"\n📄 Found 'code' key: {len(code_output)} chars")
            elif 'output' in result:
                code_output = result['output']
                print(f"\n📄 Found 'output' key: {len(code_output)} chars")
            else:
                code_output = str(result)
                print(f"\n📄 Using full result as string: {len(code_output)} chars")

            if 'files_created' in result:
                print(f"📁 Files created in response: {result['files_created']}")
        else:
            code_output = str(result)
            print(f"\n📄 Response is not dict, using as string: {len(code_output)} chars")

        print("\n" + "="*80)
        print("📝 ACTUAL CLAUDE OUTPUT:")
        print("="*80)
        print(code_output[:2000])  # First 2000 chars
        if len(code_output) > 2000:
            print(f"\n... ({len(code_output) - 2000} more chars) ...")
            print(code_output[-500:])  # Last 500 chars
        print("="*80)

        # Check for FILE: markers
        file_count = code_output.count("FILE:")
        print(f"\n📊 Analysis:")
        print(f"  - Total length: {len(code_output)} chars")
        print(f"  - FILE: markers found: {file_count}")
        print(f"  - Contains 'app.py': {'app.py' in code_output}")
        print(f"  - Contains triple backticks: {'```' in code_output}")
        print(f"  - Starts with 'FILE:': {code_output.strip().startswith('FILE:')}")

        # Try to parse files
        print("\n🔍 Attempting to parse files...")
        files = []
        if "FILE:" in code_output:
            parts = code_output.split("FILE:")
            for part in parts[1:]:  # Skip first empty part
                lines = part.strip().split('\n')
                if lines:
                    file_path = lines[0].strip()
                    print(f"  Found file: {file_path}")
                    files.append(file_path)

        if not files:
            print("  ❌ No files could be parsed!")
        else:
            print(f"  ✅ Parsed {len(files)} file(s)")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await mcp.cleanup()

if __name__ == "__main__":
    asyncio.run(debug_claude_output())