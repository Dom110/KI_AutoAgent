#!/usr/bin/env python3
"""
Test Memory MCP Server

Tests the Memory MCP server functionality with various memory operations.

Usage:
    python test_memory_mcp.py
"""

import subprocess
import json
import sys
import time
import tempfile
import shutil
import os
from pathlib import Path


def test_memory_mcp():
    """Test the Memory MCP server."""

    print("🧪 Testing Memory MCP Server\n")
    print("=" * 80)

    # Load environment variables from .env
    env_file = Path.home() / ".ki_autoagent" / "config" / ".env"
    if env_file.exists():
        print(f"\n📄 Loading environment from: {env_file}")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value.strip('"').strip("'")
        print("   ✅ Environment variables loaded")
    else:
        print(f"\n⚠️  Warning: .env file not found at {env_file}")
        print("   Memory operations requiring OpenAI will fail!")

    # Create temporary workspace for testing
    temp_workspace = tempfile.mkdtemp(prefix="test_memory_workspace_")
    print(f"\n📁 Temporary workspace: {temp_workspace}")

    # Start the MCP server (use venv Python for dependencies)
    print("\n1️⃣ Starting Memory MCP server...")
    proc = subprocess.Popen(
        ["backend/venv_v6/bin/python", "mcp_servers/memory_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=os.environ.copy()  # Pass environment variables to subprocess
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

    if response.get("result", {}).get("serverInfo", {}).get("name") == "memory-mcp-server":
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
    expected_tools = ["store_memory", "search_memory", "get_memory_stats", "count_memory"]

    if len(tools) == 4:
        tool_names = [t["name"] for t in tools]
        if all(name in tool_names for name in expected_tools):
            print("   ✅ Tools listed successfully")
            print(f"      Found {len(tools)} tool(s):")
            for tool in tools:
                print(f"        - {tool['name']}")
            tests_passed += 1
        else:
            print("   ❌ Missing expected tools")
            print(f"      Expected: {expected_tools}")
            print(f"      Got: {tool_names}")
            tests_failed += 1
    else:
        print("   ❌ List tools failed")
        print(f"      Response: {response}")
        tests_failed += 1

    # Test 3: Store memory
    print("\n4️⃣ Test 3: Store Memory")

    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "store_memory",
            "arguments": {
                "workspace_path": temp_workspace,
                "content": "Vite + React 18 recommended for 2025 frontend development",
                "metadata": {
                    "agent": "research",
                    "type": "technology",
                    "confidence": 0.9
                }
            }
        }
    }

    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()

    response_line = proc.stdout.readline()
    response = json.loads(response_line)

    if "result" in response:
        content = response.get("result", {}).get("content", [])
        if content:
            text = content[0].get("text", "")
            if '"success": true' in text and '"vector_id"' in text:
                print("   ✅ Memory stored successfully")
                # Extract vector_id
                try:
                    result_json = json.loads(text.split("```json\n")[1].split("\n```")[0])
                    vector_id = result_json.get("vector_id", -1)
                    print(f"      Vector ID: {vector_id}")
                except:
                    pass
                tests_passed += 1
            else:
                print("   ❌ Store failed")
                print(f"      Response preview: {text[:200]}...")
                tests_failed += 1
        else:
            print("   ❌ Empty response")
            tests_failed += 1
    else:
        print("   ❌ Tool call failed")
        error = response.get("error", {})
        print(f"      Error: {error.get('message', 'Unknown error')}")
        tests_failed += 1

    # Test 4: Store another memory (for search test)
    print("\n5️⃣ Test 4: Store Second Memory")

    request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "store_memory",
            "arguments": {
                "workspace_path": temp_workspace,
                "content": "Use FastAPI with Python 3.13 for backend APIs",
                "metadata": {
                    "agent": "research",
                    "type": "technology",
                    "confidence": 0.95
                }
            }
        }
    }

    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()

    response_line = proc.stdout.readline()
    response = json.loads(response_line)

    if "result" in response:
        content = response.get("result", {}).get("content", [])
        if content:
            text = content[0].get("text", "")
            if '"success": true' in text:
                print("   ✅ Second memory stored successfully")
                tests_passed += 1
            else:
                print("   ❌ Store failed")
                tests_failed += 1
        else:
            print("   ❌ Empty response")
            tests_failed += 1
    else:
        print("   ❌ Tool call failed")
        tests_failed += 1

    # Test 5: Search memory
    print("\n6️⃣ Test 5: Search Memory")

    request = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "search_memory",
            "arguments": {
                "workspace_path": temp_workspace,
                "query": "frontend frameworks",
                "k": 5
            }
        }
    }

    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()

    response_line = proc.stdout.readline()
    response = json.loads(response_line)

    if "result" in response:
        content = response.get("result", {}).get("content", [])
        if content:
            text = content[0].get("text", "")
            if '"success": true' in text and '"results"' in text:
                print("   ✅ Memory search successful")
                # Check if we found results
                if '"count": 1' in text or '"count": 2' in text:
                    print("      Found results matching query")
                tests_passed += 1
            else:
                print("   ❌ Search failed")
                print(f"      Response preview: {text[:200]}...")
                tests_failed += 1
        else:
            print("   ❌ Empty response")
            tests_failed += 1
    else:
        print("   ❌ Tool call failed")
        error = response.get("error", {})
        print(f"      Error: {error.get('message', 'Unknown error')}")
        tests_failed += 1

    # Test 6: Search with filters
    print("\n7️⃣ Test 6: Search Memory with Filters")

    request = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "search_memory",
            "arguments": {
                "workspace_path": temp_workspace,
                "query": "technology",
                "filters": {
                    "agent": "research"
                },
                "k": 5
            }
        }
    }

    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()

    response_line = proc.stdout.readline()
    response = json.loads(response_line)

    if "result" in response:
        content = response.get("result", {}).get("content", [])
        if content:
            text = content[0].get("text", "")
            if '"success": true' in text and '"results"' in text:
                print("   ✅ Filtered search successful")
                tests_passed += 1
            else:
                print("   ❌ Filtered search failed")
                tests_failed += 1
        else:
            print("   ❌ Empty response")
            tests_failed += 1
    else:
        print("   ❌ Tool call failed")
        tests_failed += 1

    # Test 7: Get stats
    print("\n8️⃣ Test 7: Get Memory Stats")

    request = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/call",
        "params": {
            "name": "get_memory_stats",
            "arguments": {
                "workspace_path": temp_workspace
            }
        }
    }

    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()

    response_line = proc.stdout.readline()
    response = json.loads(response_line)

    if "result" in response:
        content = response.get("result", {}).get("content", [])
        if content:
            text = content[0].get("text", "")
            if '"success": true' in text and '"stats"' in text:
                print("   ✅ Stats retrieved successfully")
                # Check for total_items
                if '"total_items": 2' in text:
                    print("      Total items: 2 ✓")
                tests_passed += 1
            else:
                print("   ❌ Stats failed")
                print(f"      Response preview: {text[:200]}...")
                tests_failed += 1
        else:
            print("   ❌ Empty response")
            tests_failed += 1
    else:
        print("   ❌ Tool call failed")
        tests_failed += 1

    # Test 8: Count memory
    print("\n9️⃣ Test 8: Count Memory")

    request = {
        "jsonrpc": "2.0",
        "id": 8,
        "method": "tools/call",
        "params": {
            "name": "count_memory",
            "arguments": {
                "workspace_path": temp_workspace
            }
        }
    }

    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()

    response_line = proc.stdout.readline()
    response = json.loads(response_line)

    if "result" in response:
        content = response.get("result", {}).get("content", [])
        if content:
            text = content[0].get("text", "")
            if '"success": true' in text and '"count": 2' in text:
                print("   ✅ Count successful")
                print("      Total items: 2 ✓")
                tests_passed += 1
            else:
                print("   ❌ Count failed")
                print(f"      Response preview: {text[:200]}...")
                tests_failed += 1
        else:
            print("   ❌ Empty response")
            tests_failed += 1
    else:
        print("   ❌ Tool call failed")
        tests_failed += 1

    # Cleanup
    print("\n🔟 Cleaning up...")
    proc.terminate()
    proc.wait(timeout=5)
    print("   ✅ Server stopped")

    # Remove temporary workspace
    try:
        shutil.rmtree(temp_workspace)
        print(f"   ✅ Temporary workspace deleted")
    except Exception as e:
        print(f"   ⚠️  Failed to delete temp workspace: {e}")

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
        print("     claude mcp add memory python mcp_servers/memory_server.py")
        print("\n  2. Verify registration:")
        print("     claude mcp list")
        print("\n  3. Test with Claude:")
        print('     claude "Store this in memory: Vite + React 18 recommended"')
        print('     claude "Search memory for frontend frameworks"')
        print('     claude "Show me memory stats"')
        print("\n  4. Claude will automatically use memory tools when appropriate!")
        print("\n📚 Available Tools:")
        print("   - store_memory: Store content with metadata")
        print("   - search_memory: Semantic search with filters")
        print("   - get_memory_stats: Get statistics (total, by agent, by type)")
        print("   - count_memory: Get total memory count")
        print("\n⚠️  Note: Requires OPENAI_API_KEY for embeddings!")
        return True
    else:
        print("\n❌ SOME TESTS FAILED")
        print("\nPlease review errors above.")
        return False


if __name__ == "__main__":
    success = test_memory_mcp()
    sys.exit(0 if success else 1)
