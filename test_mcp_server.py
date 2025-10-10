#!/usr/bin/env python3
"""
Test MCP Server Directly

Tests the MCP server by sending JSON-RPC requests via stdin/stdout.

Usage:
    python test_mcp_server.py
"""

import subprocess
import json
import sys


def test_mcp_server():
    """Test the minimal hello MCP server."""

    print("🧪 Testing Minimal Hello MCP Server\n")
    print("=" * 80)

    # Start the MCP server
    print("\n1️⃣ Starting MCP server...")
    proc = subprocess.Popen(
        ["python3", "mcp_servers/minimal_hello_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    print("   ✅ Server started (PID: {})".format(proc.pid))

    tests_passed = 0
    tests_failed = 0

    # Test 1: Initialize
    print("\n2️⃣ Test 1: Initialize")
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }

    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()

    response_line = proc.stdout.readline()
    response = json.loads(response_line)

    if response.get("result", {}).get("serverInfo", {}).get("name") == "minimal-hello-server":
        print("   ✅ Initialize successful")
        print(f"      Server: {response['result']['serverInfo']['name']}")
        print(f"      Version: {response['result']['serverInfo']['version']}")
        tests_passed += 1
    else:
        print("   ❌ Initialize failed")
        print(f"      Response: {response}")
        tests_failed += 1

    # Test 2: List tools
    print("\n3️⃣ Test 2: List Tools")
    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }

    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()

    response_line = proc.stdout.readline()
    response = json.loads(response_line)

    tools = response.get("result", {}).get("tools", [])
    if len(tools) > 0 and tools[0].get("name") == "say_hello":
        print("   ✅ Tools listed successfully")
        print(f"      Found {len(tools)} tool(s):")
        for tool in tools:
            print(f"        - {tool['name']}: {tool['description']}")
        tests_passed += 1
    else:
        print("   ❌ List tools failed")
        print(f"      Response: {response}")
        tests_failed += 1

    # Test 3: Call tool
    print("\n4️⃣ Test 3: Call say_hello Tool")
    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "say_hello",
            "arguments": {
                "name": "Claude"
            }
        }
    }

    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()

    response_line = proc.stdout.readline()
    response = json.loads(response_line)

    content = response.get("result", {}).get("content", [])
    if content and "Hello, Claude" in content[0].get("text", ""):
        print("   ✅ Tool call successful")
        result_data = json.loads(content[0]["text"])
        print(f"      Greeting: {result_data.get('greeting')}")
        print(f"      Timestamp: {result_data.get('timestamp')}")
        tests_passed += 1
    else:
        print("   ❌ Tool call failed")
        print(f"      Response: {response}")
        tests_failed += 1

    # Test 4: Call with different name
    print("\n5️⃣ Test 4: Call say_hello with 'World'")
    request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "say_hello",
            "arguments": {
                "name": "World"
            }
        }
    }

    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()

    response_line = proc.stdout.readline()
    response = json.loads(response_line)

    content = response.get("result", {}).get("content", [])
    if content and "Hello, World" in content[0].get("text", ""):
        print("   ✅ Tool call successful")
        result_data = json.loads(content[0]["text"])
        print(f"      Greeting: {result_data.get('greeting')}")
        tests_passed += 1
    else:
        print("   ❌ Tool call failed")
        tests_failed += 1

    # Cleanup
    print("\n6️⃣ Cleaning up...")
    proc.terminate()
    proc.wait(timeout=5)
    print("   ✅ Server stopped")

    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"\nTests passed: {tests_passed} ✅")
    print(f"Tests failed: {tests_failed} {'❌' if tests_failed > 0 else ''}")
    print(f"\nTotal: {tests_passed + tests_failed}")

    if tests_failed == 0:
        print("\n✅ ALL TESTS PASSED!")
        print("\nNext steps:")
        print("  1. Register with Claude CLI: claude mcp add hello python mcp_servers/minimal_hello_server.py")
        print("  2. Test with Claude: claude \"Say hello to Test\"")
        return True
    else:
        print("\n❌ SOME TESTS FAILED")
        print("\nPlease review errors above.")
        return False


if __name__ == "__main__":
    success = test_mcp_server()
    sys.exit(0 if success else 1)
