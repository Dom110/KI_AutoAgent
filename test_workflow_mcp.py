#!/usr/bin/env python3
"""
Test Workflow MCP Server

Tests workflow integration tools (excluding long-running execute_workflow).

Tools tested:
1. classify_query - Fast query classification
2. get_system_health - Health check
3. get_learning_history - Learning history access

NOTE: execute_workflow is NOT tested here as it takes 5-15 minutes.
      Use test_workflow_v6_1_complete.py for full E2E testing.

Author: KI AutoAgent Team
Version: 1.0.0
"""

import asyncio
import json
import subprocess
import sys
import os
from pathlib import Path

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def send_request(proc, request: dict) -> dict:
    """Send JSON-RPC request and get response."""
    # Send request
    request_line = json.dumps(request) + "\n"
    proc.stdin.write(request_line)
    proc.stdin.flush()

    # Read response
    response_line = proc.stdout.readline()
    return json.loads(response_line)


def test_initialize(proc):
    """Test 1: Initialize"""
    print("\n" + "="*80)
    print("TEST 1: Initialize")
    print("="*80)

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }

    response = send_request(proc, request)

    print(f"✅ Response: {json.dumps(response, indent=2)}")

    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    assert "result" in response
    assert response["result"]["serverInfo"]["name"] == "workflow-mcp-server"
    assert response["result"]["serverInfo"]["version"] == "1.0.0"

    print("✅ Initialize passed")


def test_tools_list(proc):
    """Test 2: List tools"""
    print("\n" + "="*80)
    print("TEST 2: List Tools")
    print("="*80)

    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }

    response = send_request(proc, request)

    print(f"✅ Response: {json.dumps(response, indent=2)}")

    assert response["jsonrpc"] == "2.0"
    assert "result" in response
    assert "tools" in response["result"]

    tools = response["result"]["tools"]
    assert len(tools) == 4

    tool_names = [t["name"] for t in tools]
    assert "execute_workflow" in tool_names
    assert "classify_query" in tool_names
    assert "get_system_health" in tool_names
    assert "get_learning_history" in tool_names

    print(f"✅ Found {len(tools)} tools: {tool_names}")
    print("✅ List tools passed")


def test_classify_query_simple(proc):
    """Test 3: Classify simple query"""
    print("\n" + "="*80)
    print("TEST 3: Classify Query (Simple)")
    print("="*80)

    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "classify_query",
            "arguments": {
                "user_query": "Build a todo app with React"
            }
        }
    }

    response = send_request(proc, request)

    print(f"✅ Response: {json.dumps(response, indent=2)}")

    assert response["jsonrpc"] == "2.0"
    assert "result" in response

    result_text = response["result"]["content"][0]["text"]
    assert "classification" in result_text.lower()

    print("✅ Simple query classification passed")


def test_classify_query_complex(proc):
    """Test 4: Classify complex query"""
    print("\n" + "="*80)
    print("TEST 4: Classify Query (Complex)")
    print("="*80)

    request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "classify_query",
            "arguments": {
                "user_query": "Refactor legacy Express.js API to NestJS microservices with Redis caching",
                "include_suggestions": True
            }
        }
    }

    response = send_request(proc, request)

    print(f"✅ Response: {json.dumps(response, indent=2)}")

    assert response["jsonrpc"] == "2.0"
    assert "result" in response

    result_text = response["result"]["content"][0]["text"]
    assert "classification" in result_text.lower()
    # Complex query should have high complexity
    assert "complex" in result_text.lower() or "moderate" in result_text.lower()

    print("✅ Complex query classification passed")


def test_get_system_health(proc):
    """Test 5: Get system health"""
    print("\n" + "="*80)
    print("TEST 5: Get System Health")
    print("="*80)

    # Use a test workspace
    workspace = str(Path.cwd())

    request = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "get_system_health",
            "arguments": {
                "workspace_path": workspace
            }
        }
    }

    response = send_request(proc, request)

    print(f"✅ Response: {json.dumps(response, indent=2)}")

    assert response["jsonrpc"] == "2.0"
    assert "result" in response

    result_text = response["result"]["content"][0]["text"]
    # Should return health info (even if no workflow has run yet)
    assert "health" in result_text.lower() or "diagnostics" in result_text.lower()

    print("✅ System health check passed")


def test_get_learning_history_empty(proc):
    """Test 6: Get learning history (empty initially)"""
    print("\n" + "="*80)
    print("TEST 6: Get Learning History (Empty)")
    print("="*80)

    workspace = str(Path.cwd())

    request = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "get_learning_history",
            "arguments": {
                "workspace_path": workspace,
                "limit": 5
            }
        }
    }

    response = send_request(proc, request)

    print(f"✅ Response: {json.dumps(response, indent=2)}")

    assert response["jsonrpc"] == "2.0"
    assert "result" in response

    result_text = response["result"]["content"][0]["text"]
    # Should return history structure (even if empty)
    assert "history" in result_text.lower() or "executions" in result_text.lower()

    print("✅ Learning history access passed")


def test_classify_debugging_query(proc):
    """Test 7: Classify debugging query"""
    print("\n" + "="*80)
    print("TEST 7: Classify Query (Debugging)")
    print("="*80)

    request = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/call",
        "params": {
            "name": "classify_query",
            "arguments": {
                "user_query": "Fix memory leak in Node.js server"
            }
        }
    }

    response = send_request(proc, request)

    print(f"✅ Response: {json.dumps(response, indent=2)}")

    assert response["jsonrpc"] == "2.0"
    assert "result" in response

    result_text = response["result"]["content"][0]["text"]
    # Debugging queries should be classified accordingly
    assert "debug" in result_text.lower() or "fix" in result_text.lower()

    print("✅ Debugging query classification passed")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    """Run all Workflow MCP Server tests."""
    print("\n" + "="*80)
    print("🧪 WORKFLOW MCP SERVER TEST SUITE")
    print("="*80)
    print("Testing: Workflow integration tools")
    print("Tools: classify_query, get_system_health, get_learning_history")
    print("NOTE: execute_workflow NOT tested (takes 5-15 min)")
    print("="*80)

    # Load environment variables
    print("\n📦 Loading environment variables...")
    env_file = Path.home() / ".ki_autoagent" / "config" / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value.strip('"').strip("'")
        print("  ✅ Environment variables loaded")
    else:
        print(f"  ⚠️  Warning: {env_file} not found")

    # Get venv Python
    venv_python = Path.cwd() / "backend" / "venv_v6" / "bin" / "python"
    if not venv_python.exists():
        print(f"❌ Error: {venv_python} not found!")
        print("Run: cd backend && python3 -m venv venv_v6 && venv_v6/bin/pip install -r requirements_v6.txt")
        sys.exit(1)

    print(f"  ✅ Using venv Python: {venv_python}")

    # Start MCP server
    print("\n🚀 Starting Workflow MCP Server...")
    proc = subprocess.Popen(
        [str(venv_python), "mcp_servers/workflow_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=os.environ.copy()
    )

    try:
        # Run all tests
        test_initialize(proc)
        test_tools_list(proc)
        test_classify_query_simple(proc)
        test_classify_query_complex(proc)
        test_get_system_health(proc)
        test_get_learning_history_empty(proc)
        test_classify_debugging_query(proc)

        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED (7/7)")
        print("="*80)
        print("\nWorkflow MCP Server is working correctly!")
        print("\n4 Tools Available:")
        print("  1. execute_workflow - Execute full v6 workflow (5-15 min)")
        print("  2. classify_query - Fast query classification (< 1 sec)")
        print("  3. get_system_health - Health check and diagnostics")
        print("  4. get_learning_history - View past workflow executions")
        print("\n⚠️  NOTE: execute_workflow not tested here (too long)")
        print("   Use test_workflow_v6_1_complete.py for full E2E testing")
        print("="*80)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("\nServer stderr:")
        stderr = proc.stderr.read()
        print(stderr)
        raise

    finally:
        # Cleanup
        proc.terminate()
        proc.wait(timeout=5)


if __name__ == "__main__":
    main()
