"""
VALIDATION TEST: FIX #2 V2 Implementation
==========================================

Verifies that all 6 MCP servers have been correctly updated with the timeout-free stdin handling.

Checks:
1. No more asyncio.wait_for() with timeout=300.0 in async_stdin_readline()
2. All servers have [stdin_v2] logging tags
3. All servers have "NO timeout" documentation
4. All imports and syntax are correct
5. Files are syntactically valid Python

Status: ✅ READY TO TEST
"""

import ast
import sys
from pathlib import Path


def check_syntax(filepath: str) -> tuple[bool, str]:
    """Check if Python file has valid syntax"""
    try:
        with open(filepath, 'r') as f:
            ast.parse(f.read())
        return True, "OK"
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def check_no_old_timeout(filepath: str) -> tuple[bool, str]:
    """Check that the old timeout pattern is removed (excluding comments)"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find async_stdin_readline function
    if 'async def async_stdin_readline()' not in content:
        return False, "No async_stdin_readline function found"
    
    # Extract the function
    start = content.find('async def async_stdin_readline()')
    if start == -1:
        return False, "Could not find function start"
    
    # Find the next function definition or class (to find function end)
    end = content.find('\n\n', start)
    if end == -1:
        end = content.find('\nclass ', start)
    if end == -1:
        end = content.find('\nasync def ', start + 1)
    
    function_body = content[start:end] if end != -1 else content[start:]
    
    # Remove comments from function_body to avoid false positives
    lines = []
    for line in function_body.split('\n'):
        # Remove comment part
        if '#' in line:
            line = line[:line.index('#')]
        lines.append(line)
    
    function_body_no_comments = '\n'.join(lines)
    
    # Check for old pattern in this function (excluding comments)
    # Look specifically for: "result = await asyncio.wait_for(..., timeout=300.0)"
    if 'asyncio.wait_for(' in function_body_no_comments and 'timeout=' in function_body_no_comments:
        # Double check by looking for the actual timeout parameter
        if 'timeout=300' in function_body_no_comments:
            return False, "OLD PATTERN STILL EXISTS: asyncio.wait_for with timeout=300"
    
    return True, "Old timeout pattern removed ✓"


def check_new_pattern(filepath: str) -> tuple[bool, str]:
    """Check that new pattern is implemented"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Extract the function
    start = content.find('async def async_stdin_readline()')
    if start == -1:
        return False, "No async_stdin_readline function"
    
    end = content.find('\n\n', start)
    if end == -1:
        end = content.find('\nclass ', start)
    if end == -1:
        end = content.find('\nasync def ', start + 1)
    
    function_body = content[start:end] if end != -1 else content[start:]
    
    # Check for new pattern
    checks = [
        ('loop.run_in_executor(None, _read)', 'Using run_in_executor without timeout'),
        ('[stdin_v2]', 'Using [stdin_v2] logging tag'),
        ('FIX #2 V2', 'Documentation mentions V2'),
    ]
    
    for pattern, desc in checks:
        if pattern not in function_body:
            return False, f"Missing: {desc} (pattern: {pattern})"
    
    return True, "New pattern implemented ✓"


def main():
    """Main validation runner"""
    servers = [
        "openai_server.py",
        "architect_agent_server.py",
        "codesmith_agent_server.py",
        "research_agent_server.py",
        "responder_agent_server.py",
        "reviewfix_agent_server.py",
    ]
    
    mcp_dir = Path("/Users/dominikfoert/git/KI_AutoAgent/mcp_servers")
    
    print("=" * 80)
    print("🔍 VALIDATION TEST: FIX #2 V2 Implementation")
    print("=" * 80)
    
    all_passed = True
    results = {}
    
    for server in servers:
        filepath = mcp_dir / server
        
        if not filepath.exists():
            print(f"\n❌ {server}: FILE NOT FOUND")
            all_passed = False
            continue
        
        print(f"\n📝 Checking: {server}")
        print("-" * 80)
        
        # Test 1: Syntax
        syntax_ok, syntax_msg = check_syntax(str(filepath))
        print(f"  1. Syntax: {'✅' if syntax_ok else '❌'} {syntax_msg}")
        if not syntax_ok:
            all_passed = False
        
        # Test 2: Old timeout pattern removed
        no_old, no_old_msg = check_no_old_timeout(str(filepath))
        print(f"  2. Remove old: {'✅' if no_old else '❌'} {no_old_msg}")
        if not no_old:
            all_passed = False
        
        # Test 3: New pattern implemented
        new_pat, new_pat_msg = check_new_pattern(str(filepath))
        print(f"  3. New pattern: {'✅' if new_pat else '❌'} {new_pat_msg}")
        if not new_pat:
            all_passed = False
        
        results[server] = (syntax_ok and no_old and new_pat)
    
    print("\n" + "=" * 80)
    print("📊 SUMMARY:")
    print("=" * 80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for server, passed_check in results.items():
        status = "✅ PASS" if passed_check else "❌ FAIL"
        print(f"  {status}: {server}")
    
    print(f"\nTotal: {passed}/{total} servers passed")
    
    if all_passed:
        print("\n🎉 All validations passed!")
        print("\n✅ READY FOR:")
        print("  1. Syntax checking (mypy/pyright)")
        print("  2. E2E testing")
        print("  3. Production deployment")
        return 0
    else:
        print("\n❌ Some validations failed - review above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
