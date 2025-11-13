#!/usr/bin/env python3
"""
Test: Workspace Isolation
==========================

This test verifies that the server REJECTS client requests that try to
initialize a workspace within the server's own workspace directory.

This is a SECURITY feature to prevent:
1. Accidental test execution within server workspace
2. Potential recursive issues
3. Server self-modification

Test Scenarios:
1. ✅ Client workspace OUTSIDE server workspace → ALLOWED
2. ❌ Client workspace INSIDE server workspace → BLOCKED
3. ❌ Client workspace = server workspace → BLOCKED
4. ✅ Client workspace in /tmp or other locations → ALLOWED
"""

import asyncio
import json
import websockets
import sys
from pathlib import Path
from datetime import datetime

# Get the server root from start_server.py location
SERVER_ROOT = Path(__file__).parent  # /Users/dominikfoert/git/KI_AutoAgent
TEST_RESULTS = []

# Color codes for output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'


def print_header():
    """Print test header"""
    print("\n" + "=" * 80)
    print(f"{Colors.CYAN}{Colors.BOLD}🔒 WORKSPACE ISOLATION TEST{Colors.RESET}")
    print("=" * 80)
    print(f"\nServer Root: {SERVER_ROOT}")
    print(f"Test Start: {datetime.now().isoformat()}\n")


def print_test_case(num: int, name: str, workspace: str, should_allow: bool):
    """Print test case header"""
    expected = "✅ ALLOWED" if should_allow else "❌ BLOCKED"
    print(f"\n{Colors.BOLD}Test {num}: {name}{Colors.RESET}")
    print(f"  Server Root: {SERVER_ROOT}")
    print(f"  Client Workspace: {workspace}")
    print(f"  Expected: {expected}")
    print(f"  Status: ", end="", flush=True)


async def test_workspace_init(workspace_path: str, should_allow: bool) -> bool:
    """
    Test if workspace initialization is allowed/blocked correctly
    
    Returns: True if test passed (behavior matched expectation)
    """
    try:
        uri = "ws://localhost:8002/ws/chat"
        async with websockets.connect(uri, ping_interval=None) as websocket:
            # Wait for connection message
            msg = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            data = json.loads(msg)
            
            # Send init message with workspace
            init_msg = {
                "type": "init",
                "workspace_path": workspace_path
            }
            await websocket.send(json.dumps(init_msg))
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            response_data = json.loads(response)
            
            # Check response
            is_error = response_data.get("type") == "error"
            is_initialized = response_data.get("type") == "initialized"
            
            if should_allow:
                # Should be initialized, not error
                if is_initialized:
                    print(f"{Colors.GREEN}✅ PASS{Colors.RESET}")
                    print(f"     Response: {response_data.get('message', 'Initialized')}")
                    return True
                else:
                    print(f"{Colors.RED}❌ FAIL{Colors.RESET}")
                    print(f"     Expected: Initialization success")
                    print(f"     Got: {response_data.get('message', response_data.get('type'))}")
                    return False
            else:
                # Should be blocked with error
                if is_error:
                    error_msg = response_data.get("message", "")
                    # Check if error mentions workspace isolation
                    if "workspace" in error_msg.lower() or "isolation" in error_msg.lower():
                        print(f"{Colors.GREEN}✅ PASS{Colors.RESET}")
                        print(f"     Error: {error_msg}")
                        return True
                    else:
                        print(f"{Colors.YELLOW}⚠️  PARTIAL{Colors.RESET}")
                        print(f"     Blocked but message unclear: {error_msg}")
                        return True  # Still blocked, just message could be better
                else:
                    print(f"{Colors.RED}❌ FAIL{Colors.RESET}")
                    print(f"     Expected: Rejection")
                    print(f"     Got: {response_data.get('type')} - {response_data.get('message', '')}")
                    return False
                    
    except asyncio.TimeoutError:
        print(f"{Colors.RED}❌ TIMEOUT{Colors.RESET}")
        print(f"     No response from server (server not running?)")
        return False
    except ConnectionRefusedError:
        print(f"{Colors.RED}❌ CONNECTION FAILED{Colors.RESET}")
        print(f"     Cannot connect to ws://localhost:8002/ws/chat")
        print(f"     Start server with: python start_server.py")
        return False
    except Exception as e:
        print(f"{Colors.RED}❌ ERROR{Colors.RESET}")
        print(f"     {str(e)}")
        return False


async def main():
    """Run all workspace isolation tests"""
    print_header()
    
    # Determine test cases
    test_cases = [
        # (name, workspace_path, should_allow)
        (
            "Outside server - /tmp location",
            "/tmp/e2e_test_workspace",
            True  # Should be allowed
        ),
        (
            "Outside server - home directory",
            str(Path.home() / "TestApps" / "test_workspace"),
            True  # Should be allowed
        ),
        (
            "INSIDE server - direct subdirectory",
            str(SERVER_ROOT / "test_workspace"),
            False  # Should be BLOCKED
        ),
        (
            "INSIDE server - nested subdirectory",
            str(SERVER_ROOT / "backend" / "test_workspace"),
            False  # Should be BLOCKED
        ),
        (
            "INSIDE server - TestApps subdirectory",
            str(SERVER_ROOT / "TestApps"),
            False  # Should be BLOCKED
        ),
        (
            "IDENTICAL to server root",
            str(SERVER_ROOT),
            False  # Should be BLOCKED
        ),
        (
            "INSIDE server - parent path traversal",
            str(SERVER_ROOT / ".." / "KI_AutoAgent" / "test"),
            False  # Should be BLOCKED (even with parent traversal)
        ),
    ]
    
    # Run tests
    results = []
    for i, (name, workspace, should_allow) in enumerate(test_cases, 1):
        # Resolve workspace path to normalize it
        try:
            resolved_workspace = str(Path(workspace).resolve())
        except:
            resolved_workspace = workspace
        
        print_test_case(i, name, resolved_workspace, should_allow)
        passed = await test_workspace_init(resolved_workspace, should_allow)
        results.append((i, name, passed))
        
        # Small delay between tests
        await asyncio.sleep(0.5)
    
    # Summary
    print("\n\n" + "=" * 80)
    print(f"{Colors.CYAN}{Colors.BOLD}📊 TEST SUMMARY{Colors.RESET}")
    print("=" * 80 + "\n")
    
    passed_count = sum(1 for _, _, p in results if p)
    total_count = len(results)
    
    for test_num, name, passed in results:
        status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if passed else f"{Colors.RED}❌ FAIL{Colors.RESET}"
        print(f"  {status}  Test {test_num}: {name}")
    
    print(f"\n{Colors.BOLD}Results: {passed_count}/{total_count} tests passed{Colors.RESET}")
    
    if passed_count == total_count:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ ALL TESTS PASSED - WORKSPACE ISOLATION WORKING!{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ SOME TESTS FAILED - ISOLATION NOT FULLY IMPLEMENTED{Colors.RESET}\n")
        return 1


if __name__ == "__main__":
    print("\n⚠️  This test requires:")
    print("  1. Server running: python start_server.py")
    print("  2. No active clients connected")
    print("\nPress ENTER to start tests, or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.\n")
        sys.exit(0)
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)