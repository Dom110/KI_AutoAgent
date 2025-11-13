"""
🤖 Automation Script: Apply FIX #2 V2 (No Timeout) to All MCP Servers

This script applies the timeout-free stdin handling to all MCP servers.

Servers to update:
1. architect_agent_server.py ✓
2. codesmith_agent_server.py
3. research_agent_server.py
4. responder_agent_server.py
5. reviewfix_agent_server.py
(openai_server.py - already updated manually)

Changes per server:
1. Replace async_stdin_readline() function body (remove timeout=300.0)
2. Update logging: [stdin] → [stdin_v2]
3. Update comments: "with 300s timeout" → "WITHOUT timeout"
4. Update main loop logging messages
"""

import re
import sys
from pathlib import Path

# The new async_stdin_readline function body (no timeout)
NEW_FUNCTION = '''async def async_stdin_readline() -> str:
    """
    🔧 FIX #2 V2: Non-blocking stdin readline WITHOUT arbitrary timeout
    
    Solves the asyncio blocking I/O issue while avoiding 300s timeout problems.
    
    Key improvements:
    - NO timeout → Operations complete fully, no interruptions at 300s
    - EOF detection → Natural shutdown when parent closes connection
    - Signal handling ready → Can add graceful shutdown handlers
    - Scales → Works for any operation duration
    
    How it works:
    - Uses run_in_executor() to keep event loop responsive
    - Waits indefinitely for stdin data or EOF from parent
    - Parent process controls server lifetime via connection
    - Signal handlers provide additional graceful shutdown control
    
    Returns:
        str: Line read from stdin, or empty string on EOF
        
    Logging:
        [stdin_v2] - All stdin operations prefixed with this tag
    """
    loop = asyncio.get_event_loop()
    
    def _read():
        """Blocking read - runs in executor thread, non-blocking to event loop"""
        try:
            logger.debug("[stdin_v2] sys.stdin.readline() called (blocking in executor)")
            line = sys.stdin.readline()
            
            if line:
                logger.debug(f"[stdin_v2] Read {len(line)} bytes")
            else:
                logger.info("[stdin_v2] EOF detected (empty line from stdin)")
            
            return line
            
        except Exception as e:
            logger.error(f"[stdin_v2] Read error: {type(e).__name__}: {e}")
            return ""
    
    try:
        logger.debug("[stdin_v2] Waiting for input (NO timeout - waits for EOF or data)")
        
        # KEY CHANGE: NO timeout!
        # The old code used: await asyncio.wait_for(..., timeout=300.0)
        # This interrupted operations after 300s arbitrarily.
        # New approach: Just await the executor directly.
        # Server lifetime is controlled by parent process closing stdin.
        result = await loop.run_in_executor(None, _read)
        
        return result
        
    except Exception as e:
        logger.error(f"[stdin_v2] Unexpected error: {type(e).__name__}: {e}")
        return ""'''

def update_server(filepath: str) -> bool:
    """
    Updates a single server file with FIX #2 V2
    
    Args:
        filepath: Path to the MCP server file
        
    Returns:
        bool: True if update successful, False otherwise
    """
    print(f"\n📝 Processing: {Path(filepath).name}")
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Pattern to find the old async_stdin_readline function
        # This is complex because the function has different lengths
        pattern = r'async def async_stdin_readline\(\) -> str:.*?(?=\n\nclass |\n\nasync def |\n\ndef )'
        
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            print(f"  ❌ Could not find async_stdin_readline in {filepath}")
            return False
        
        old_function = match.group(0)
        print(f"  ✅ Found old function (length: {len(old_function)} chars)")
        
        # Replace the function
        new_content = content[:match.start()] + NEW_FUNCTION + "\n" + content[match.end():]
        
        # Additional replacements for comments and logging
        replacements = [
            # Update function header comments
            ("FIX #2: Uses async_stdin_readline() with 300s timeout", 
             "FIX #2 V2: Uses async_stdin_readline() WITHOUT timeout"),
            ("timeout: 300s)", 
             "NO timeout - waits for EOF)"),
            ("Timeout (300s) - parent process may have disconnected",
             "No timeout - waiting for EOF or signal"),
        ]
        
        for old_text, new_text in replacements:
            new_content = new_content.replace(old_text, new_text)
        
        # Write updated file
        with open(filepath, 'w') as f:
            f.write(new_content)
        
        print(f"  ✅ Successfully updated {Path(filepath).name}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error updating {filepath}: {type(e).__name__}: {e}")
        return False


def main():
    """Main script runner"""
    mcp_servers_dir = Path("/Users/dominikfoert/git/KI_AutoAgent/mcp_servers")
    
    servers_to_update = [
        "architect_agent_server.py",
        "codesmith_agent_server.py",
        "research_agent_server.py",
        "responder_agent_server.py",
        "reviewfix_agent_server.py",
    ]
    
    print("=" * 80)
    print("🤖 FIX #2 V2: Applying Timeout-Free Stdin Handling")
    print("=" * 80)
    print(f"📁 Target directory: {mcp_servers_dir}")
    print(f"🎯 Servers to update: {len(servers_to_update)}")
    
    results = {}
    for server in servers_to_update:
        filepath = mcp_servers_dir / server
        if filepath.exists():
            results[server] = update_server(str(filepath))
        else:
            print(f"\n❌ File not found: {filepath}")
            results[server] = False
    
    print("\n" + "=" * 80)
    print("📊 SUMMARY:")
    print("=" * 80)
    
    success_count = sum(1 for v in results.values() if v)
    for server, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {status}: {server}")
    
    print(f"\nTotal: {success_count}/{len(servers_to_update)} servers updated")
    
    if success_count == len(servers_to_update):
        print("\n🎉 All servers updated successfully!")
        print("\nNext steps:")
        print("1. Review changes in git diff")
        print("2. Test each server with: python mcp_servers/<server>.py")
        print("3. Run E2E tests to verify no regressions")
        print("4. Commit changes")
    else:
        print(f"\n⚠️ {len(servers_to_update) - success_count} servers failed to update")
        print("Please review the errors above")
        sys.exit(1)


if __name__ == "__main__":
    main()
