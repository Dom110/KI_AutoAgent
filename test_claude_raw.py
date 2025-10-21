#!/usr/bin/env python3
"""
Test Claude MCP server directly to see raw output format.
"""

import asyncio
import subprocess
import json

async def test_claude_raw():
    """Call Claude MCP server directly via stdio."""

    # Simple test prompt
    system_prompt = """You are a code generator. Output ONLY in this format:

FILE: <path>
```<language>
<code>
```

START with FILE: - no other text!"""

    user_prompt = """Add a docstring to this Python file:

```python
# Simple Python app
print('Hello, World!')
```

Generate the complete updated file."""

    # Prepare MCP request
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "claude_generate",
            "arguments": {
                "prompt": user_prompt,
                "system_prompt": system_prompt,
                "workspace_path": "/Users/dominikfoert/TestApps/ProgressTest",
                "agent_name": "codesmith",
                "temperature": 0.2,
                "max_tokens": 1000,
                "tools": ["Read", "Edit", "Bash"]
            }
        },
        "id": 1
    }

    print("📤 Request to Claude MCP server:")
    print(json.dumps(request, indent=2))
    print("\n" + "="*80 + "\n")

    # Call the MCP server
    process = await asyncio.create_subprocess_exec(
        "/opt/homebrew/bin/python3.13",
        "/Users/dominikfoert/.ki_autoagent/mcp_servers/claude_cli_server.py",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Send request
    stdin_data = json.dumps(request) + "\n"
    stdout, stderr = await process.communicate(input=stdin_data.encode())

    if stderr:
        print("⚠️ Stderr:")
        print(stderr.decode())
        print()

    print("📥 Raw stdout response:")
    print("="*80)
    print(stdout.decode())
    print("="*80)

    # Try to parse response
    try:
        # MCP servers output JSON-RPC responses line by line
        for line in stdout.decode().strip().split('\n'):
            if line.strip() and line.startswith('{'):
                response = json.loads(line)

                if "result" in response:
                    result = response["result"]
                    print("\n📊 Result structure:")
                    print(f"  Type: {type(result)}")
                    if isinstance(result, dict):
                        print(f"  Keys: {list(result.keys())}")

                        # Check different possible formats
                        if "content" in result:
                            content = result["content"]
                            print(f"\n📄 'content' field ({type(content)}):")
                            if isinstance(content, list):
                                print(f"  List with {len(content)} items")
                                for i, item in enumerate(content):
                                    print(f"  Item {i}: {type(item)} - {list(item.keys()) if isinstance(item, dict) else str(item)[:100]}")
                                    if isinstance(item, dict) and "text" in item:
                                        text = item["text"]
                                        print(f"\n  Text content ({len(text)} chars):")
                                        print("  " + "-"*40)
                                        print(text[:500])
                                        if len(text) > 500:
                                            print(f"  ... ({len(text)-500} more chars)")
                            else:
                                print(f"  Direct content: {str(content)[:500]}")

                        if "files_created" in result:
                            print(f"\n📁 files_created: {result['files_created']}")

                elif "error" in response:
                    print(f"\n❌ Error: {response['error']}")

    except json.JSONDecodeError as e:
        print(f"\n⚠️ Could not parse JSON: {e}")

if __name__ == "__main__":
    asyncio.run(test_claude_raw())