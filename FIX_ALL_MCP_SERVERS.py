#!/usr/bin/env python3
"""
🔧 FIX: Patch all MCP servers to use non-blocking stdin

This script fixes the critical asyncio blocking I/O issue in all MCP servers.

Problem: All MCP servers used loop.run_in_executor() which blocks the event
loop when stdin has no data, causing infinite restart cycles.

Solution: Replace with async_stdin_readline() for non-blocking reads.
"""

import sys
from pathlib import Path
import re

def fix_mcp_server(filepath: Path) -> bool:
    """Fix one MCP server file"""
    print(f"\n🔧 Processing: {filepath.name}")

    try:
        content = filepath.read_text()

        # Check if already fixed
        if "from async_stdin import" in content:
            print(f"   ✅ Already fixed")
            return True

        # 1. Add import
        import_pattern = r"(from datetime import datetime)"
        import_replacement = r"1\n\n# ⚠️ MCP BLEIBT: Import async stdin helper (FIXES blocking I/O issue)\nfrom async_stdin import async_stdin_readline"

        if not re.search(import_pattern, content):
            print(f"   ⚠️  Could not find import location - skipping")
            return False

        content = re.sub(
            import_pattern,
            import_replacement,
            content,
            count=1
        )

        # 2. Fix the run() method - find and replace
        old_loop_pattern = r"loop = asyncio\.get_event_loop\(\)\s+while True:\s+line = await loop\.run_in_executor\(None, sys\.stdin\.readline\)"

        if not re.search(old_loop_pattern, content, re.MULTILINE):
            print(f"   ⚠️  Could not find blocking I/O pattern - might already be fixed")

        # Replace the blocking executor call
        new_code = """while True:
                # ⚠️ FIXED: Use non-blocking async stdin
                line = await async_stdin_readline()"""

        old_code = """loop = asyncio.get_event_loop()

            while True:
                line = await loop.run_in_executor(None, sys.stdin.readline)"""

        if old_code in content:
            content = content.replace(old_code, new_code)
            print(f"   ✅ Fixed blocking I/O pattern")
        else:
            print(f"   ⚠️  Pattern not found (might use different formatting)")

        # 3. Write back
        filepath.write_text(content)
        print(f"   ✅ PATCHED!")
        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    print("=" * 80)
    print("🔧 PATCHING ALL MCP SERVERS")
    print("=" * 80)

    mcp_dir = Path("/Users/dominikfoert/git/KI_AutoAgent/mcp_servers")

    # Find all *_server.py files
    servers = [
        "research_agent_server.py",  # Already partially fixed, but let's verify
        "architect_agent_server.py",
        "codesmith_agent_server.py",
        "openai_server.py",
        "responder_agent_server.py",
        "reviewfix_agent_server.py",
    ]

    success_count = 0
    for server_name in servers:
        filepath = mcp_dir / server_name
        if filepath.exists():
            if fix_mcp_server(filepath):
                success_count += 1
        else:
            print(f"⚠️ {server_name} not found")

    print("\n" + "=" * 80)
    print(f"✅ PATCHING COMPLETE: {success_count}/{len(servers)} servers patched")
    print("=" * 80)

    print("\n🧪 NEXT: Run E2E tests to verify the fix")
    print("   bash run_e2e_complete.sh")


if __name__ == "__main__":
    main()
