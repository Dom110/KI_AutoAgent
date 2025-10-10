#!/usr/bin/env python3
"""
Test Perplexity MCP Server

Tests the Perplexity MCP server functionality.

Usage:
    python test_perplexity_mcp.py
"""

import subprocess
import json
import sys
import time


def test_perplexity_mcp():
    """Test the Perplexity MCP server."""

    print("🧪 Testing Perplexity MCP Server\n")
    print("=" * 80)

    # Start the MCP server (use venv Python for dependencies)
    print("\n1️⃣ Starting Perplexity MCP server...")
    proc = subprocess.Popen(
        ["backend/venv_v6/bin/python", "mcp_servers/perplexity_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    print(f"   ✅ Server started (PID: {proc.pid})")
    print("   ℹ️  Using backend venv Python for dependencies")

    # Give server time to initialize
    time.sleep(1)

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

    if response.get("result", {}).get("serverInfo", {}).get("name") == "perplexity-mcp-server":
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
    if len(tools) > 0 and tools[0].get("name") == "perplexity_search":
        print("   ✅ Tools listed successfully")
        print(f"      Found {len(tools)} tool(s):")
        for tool in tools:
            print(f"        - {tool['name']}")
            print(f"          {tool['description'][:80]}...")
        tests_passed += 1
    else:
        print("   ❌ List tools failed")
        print(f"      Response: {response}")
        tests_failed += 1

    # Test 3: Call perplexity_search tool
    print("\n4️⃣ Test 3: Call perplexity_search Tool")
    print("   (This will make an actual API call, may take 10-30s)")

    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "perplexity_search",
            "arguments": {
                "query": "What is Python asyncio?",
                "max_results": 3
            }
        }
    }

    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()

    # Read response (may take a while)
    response_line = proc.stdout.readline()

    if response_line:
        response = json.loads(response_line)

        if "result" in response:
            content = response.get("result", {}).get("content", [])
            if content and len(content) > 0:
                text = content[0].get("text", "")
                print("   ✅ Tool call successful")
                print(f"      Response length: {len(text)} chars")

                # Show preview
                lines = text.split("\n")
                print("      Preview:")
                for line in lines[:5]:
                    if line.strip():
                        print(f"        {line[:70]}...")

                tests_passed += 1
            else:
                print("   ❌ Tool call returned empty content")
                tests_failed += 1
        else:
            print("   ❌ Tool call failed")
            error = response.get("error", {})
            print(f"      Error: {error.get('message', 'Unknown error')}")
            tests_failed += 1
    else:
        print("   ❌ No response received (timeout or error)")
        tests_failed += 1

    # Cleanup
    print("\n5️⃣ Cleaning up...")
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
        print("\n📋 Registration Instructions:")
        print("\n  1. Register with Claude CLI:")
        print("     claude mcp add perplexity python mcp_servers/perplexity_server.py")
        print("\n  2. Verify registration:")
        print("     claude mcp list")
        print("\n  3. Test with Claude:")
        print("     claude \"Research Python async patterns using perplexity\"")
        print("\n  4. Claude will automatically use perplexity_search when appropriate!")
        return True
    else:
        print("\n❌ SOME TESTS FAILED")
        print("\nPlease review errors above.")
        return False


if __name__ == "__main__":
    success = test_perplexity_mcp()
    sys.exit(0 if success else 1)
