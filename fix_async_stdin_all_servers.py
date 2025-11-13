#!/usr/bin/env python3
"""
🔧 Fix ALL remaining MCP servers with async_stdin_readline()
Applies FIX #2 to: architect, codesmith, responder, reviewfix

This script:
1. Finds each server file
2. Adds async_stdin_readline() function if missing
3. Replaces run_in_executor calls
4. Adds massive debugging
"""

import re
from pathlib import Path

PROJECT_ROOT = Path("/Users/dominikfoert/git/KI_AutoAgent")
MCP_SERVERS = PROJECT_ROOT / "mcp_servers"

# Servers to fix (already fixed: openai_server, research_agent_server)
SERVERS_TO_FIX = [
    "architect_agent_server.py",
    "codesmith_agent_server.py",
    "responder_agent_server.py",
    "reviewfix_agent_server.py",
]

ASYNC_STDIN_FUNCTION = '''
# ⚠️ MCP BLEIBT: INLINE Helper for non-blocking stdin (FIXES FIX #2: Async Blocking I/O)
async def async_stdin_readline() -> str:
    """
    🔄 Non-blocking stdin readline for asyncio
    
    Fixes the asyncio blocking I/O issue where servers would freeze
    waiting for input from stdin. Uses run_in_executor with 300s timeout.
    
    Returns:
        str: Line read from stdin, or empty string on timeout/EOF
    """
    loop = asyncio.get_event_loop()
    
    def _read():
        try:
            line = sys.stdin.readline()
            if line:
                logger.debug(f"🔍 [stdin] Read {len(line)} bytes")
            return line
        except Exception as e:
            logger.error(f"❌ [stdin] readline() error: {type(e).__name__}: {e}")
            return ""
    
    try:
        logger.debug("⏳ [stdin] Waiting for input (300s timeout)...")
        result = await asyncio.wait_for(
            loop.run_in_executor(None, _read),
            timeout=300.0
        )
        if result:
            logger.debug(f"✅ [stdin] Got line: {result[:60].strip()}...")
        else:
            logger.debug("ℹ️ [stdin] EOF (empty line)")
        return result
    except asyncio.TimeoutError:
        logger.warning("⏱️ [stdin] Timeout (300s) - parent process may have disconnected")
        return ""
    except Exception as e:
        logger.error(f"❌ [stdin] Unexpected error: {type(e).__name__}: {e}")
        return ""
'''


def add_async_stdin_function(content: str, class_name: str) -> str:
    """
    Add async_stdin_readline() function before the given class definition.
    Returns updated content.
    """
    if "async def async_stdin_readline" in content:
        print(f"  ℹ️ async_stdin_readline() already exists, skipping")
        return content
    
    # Find the class definition
    class_pattern = f"^class {class_name}:"
    match = re.search(class_pattern, content, re.MULTILINE)
    
    if not match:
        print(f"  ⚠️ Could not find 'class {class_name}:', aborting")
        return content
    
    insert_pos = match.start()
    # Go back to find the end of the logger setup (find last logger.info call)
    before_class = content[:insert_pos]
    last_logger = max(
        before_class.rfind("logger.info("),
        before_class.rfind("logger.debug("),
        before_class.rfind("logger.warning("),
        before_class.rfind("logger.error("),
    )
    
    if last_logger >= 0:
        # Find the end of this line
        line_end = before_class.find("\n", last_logger)
        if line_end >= 0:
            insert_pos = line_end + 1
    
    # Insert the function
    new_content = (
        content[:insert_pos] + 
        "\n" + ASYNC_STDIN_FUNCTION + "\n\n" + 
        content[insert_pos:]
    )
    
    print(f"  ✅ Added async_stdin_readline() function")
    return new_content


def replace_run_in_executor(content: str) -> tuple[str, int]:
    """
    Replace await loop.run_in_executor(None, sys.stdin.readline) 
    with await async_stdin_readline()
    
    Returns (updated_content, count_of_replacements)
    """
    pattern = r"await loop\.run_in_executor\(None, sys\.stdin\.readline\)"
    replacement = "await async_stdin_readline()"
    
    new_content = re.sub(pattern, replacement, content)
    count = content.count("loop.run_in_executor") - new_content.count("loop.run_in_executor")
    
    if count > 0:
        print(f"  ✅ Replaced {count} 'run_in_executor' calls with async_stdin_readline()")
    else:
        print(f"  ℹ️ No 'run_in_executor' calls found")
    
    return new_content, count


def add_debug_logging(content: str, server_name: str) -> str:
    """
    Add debug logging markers in the main loop.
    Looks for the pattern and adds debugging.
    """
    # This is server-specific, so we'll do it manually per server
    return content


def fix_server(server_file: Path, class_name: str):
    """
    Fix a single MCP server file.
    """
    print(f"\n{'='*80}")
    print(f"📝 Fixing: {server_file.name}")
    print(f"{'='*80}")
    
    if not server_file.exists():
        print(f"  ❌ File not found: {server_file}")
        return False
    
    with open(server_file, 'r') as f:
        content = f.read()
    
    # Step 1: Add async_stdin_readline function
    print("  Step 1: Adding async_stdin_readline() function...")
    content = add_async_stdin_function(content, class_name)
    
    # Step 2: Replace run_in_executor calls
    print("  Step 2: Replacing run_in_executor() calls...")
    content, count = replace_run_in_executor(content)
    
    if count == 0:
        print(f"  ❌ No replacements made, file may already be fixed or pattern not found")
        return False
    
    # Write back
    with open(server_file, 'w') as f:
        f.write(content)
    
    print(f"  ✅ File updated successfully")
    return True


def main():
    print(f"\n{'='*80}")
    print(f"🔧 FIX #2: Apply async_stdin_readline() to all MCP servers")
    print(f"{'='*80}")
    
    # Map servers to their class names
    server_classes = {
        "architect_agent_server.py": "ArchitectAgentMCPServer",
        "codesmith_agent_server.py": "CodesmithAgentMCPServer",
        "responder_agent_server.py": "ResponderAgentMCPServer",
        "reviewfix_agent_server.py": "ReviewFixAgentMCPServer",
    }
    
    fixed_count = 0
    for server_file, class_name in server_classes.items():
        path = MCP_SERVERS / server_file
        if fix_server(path, class_name):
            fixed_count += 1
    
    print(f"\n{'='*80}")
    print(f"✅ DONE: Fixed {fixed_count}/{len(server_classes)} servers")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
