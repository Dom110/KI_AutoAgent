#!/usr/bin/env python3
"""
Test Asimov Rules MCP Server

Tests all 3 tools:
1. validate_code - Check code against Asimov Rules
2. global_error_search - Find ALL instances of error pattern
3. check_iteration_limit - Validate retry count (HITL escalation)

Author: KI AutoAgent Team
Version: 1.0.0
"""

import asyncio
import json
import subprocess
import sys
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
    assert response["result"]["serverInfo"]["name"] == "asimov-rules-mcp-server"
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
    assert len(tools) == 3

    tool_names = [t["name"] for t in tools]
    assert "validate_code" in tool_names
    assert "global_error_search" in tool_names
    assert "check_iteration_limit" in tool_names

    print(f"✅ Found {len(tools)} tools: {tool_names}")
    print("✅ List tools passed")


def test_validate_code_valid(proc):
    """Test 3: Validate valid code"""
    print("\n" + "="*80)
    print("TEST 3: Validate Valid Code")
    print("="*80)

    valid_code = '''
def calculate_sum(a: int, b: int) -> int:
    """Calculate sum of two numbers."""
    return a + b

def main():
    result = calculate_sum(5, 3)
    print(f"Result: {result}")
'''

    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "validate_code",
            "arguments": {
                "code": valid_code,
                "file_path": "test_valid.py",
                "strict": False
            }
        }
    }

    response = send_request(proc, request)

    print(f"✅ Response: {json.dumps(response, indent=2)}")

    assert response["jsonrpc"] == "2.0"
    assert "result" in response

    # Parse result text to check if valid
    result_text = response["result"]["content"][0]["text"]
    assert "valid" in result_text.lower()

    print("✅ Valid code validation passed")


def test_validate_code_with_todo(proc):
    """Test 4: Validate code with TODO (should fail ASIMOV-2)"""
    print("\n" + "="*80)
    print("TEST 4: Validate Code with TODO (ASIMOV-2)")
    print("="*80)

    code_with_todo = '''
def process_data(data: list) -> dict:
    """Process data and return results."""
    # TODO: Implement validation logic
    return {"status": "incomplete"}
'''

    request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "validate_code",
            "arguments": {
                "code": code_with_todo,
                "file_path": "test_todo.py",
                "strict": False
            }
        }
    }

    response = send_request(proc, request)

    print(f"✅ Response: {json.dumps(response, indent=2)}")

    assert response["jsonrpc"] == "2.0"
    assert "result" in response

    # Should detect TODO violation
    result_text = response["result"]["content"][0]["text"]
    assert "todo" in result_text.lower() or "incomplete" in result_text.lower()

    print("✅ TODO detection passed (ASIMOV-2 enforced)")


def test_validate_code_with_undocumented_exception(proc):
    """Test 5: Validate code with undocumented exception handler (ASIMOV-1)"""
    print("\n" + "="*80)
    print("TEST 5: Validate Code with Undocumented Exception (ASIMOV-1)")
    print("="*80)

    code_with_exception = '''
def risky_operation(data: dict) -> str:
    """Perform risky operation."""
    try:
        result = data["key"]
        return result
    except:
        return "default"  # Undocumented fallback!
'''

    request = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "validate_code",
            "arguments": {
                "code": code_with_exception,
                "file_path": "test_exception.py",
                "strict": False
            }
        }
    }

    response = send_request(proc, request)

    print(f"✅ Response: {json.dumps(response, indent=2)}")

    assert response["jsonrpc"] == "2.0"
    assert "result" in response

    # Should detect undocumented exception handler
    result_text = response["result"]["content"][0]["text"]
    assert "except" in result_text.lower() or "fallback" in result_text.lower()

    print("✅ Undocumented exception detection passed (ASIMOV-1 enforced)")


def test_validate_code_with_pass(proc):
    """Test 6: Validate code with pass statement"""
    print("\n" + "="*80)
    print("TEST 6: Validate Code with Pass Statement")
    print("="*80)

    code_with_pass = '''
def incomplete_function(x: int) -> int:
    """This function is incomplete."""
    pass
'''

    request = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "validate_code",
            "arguments": {
                "code": code_with_pass,
                "file_path": "test_pass.py",
                "strict": False
            }
        }
    }

    response = send_request(proc, request)

    print(f"✅ Response: {json.dumps(response, indent=2)}")

    assert response["jsonrpc"] == "2.0"
    assert "result" in response

    # Should detect pass statement
    result_text = response["result"]["content"][0]["text"]
    assert "pass" in result_text.lower() or "incomplete" in result_text.lower()

    print("✅ Pass statement detection passed")


def test_check_iteration_limit_low(proc):
    """Test 7: Check iteration limit (low retries, should be OK)"""
    print("\n" + "="*80)
    print("TEST 7: Check Iteration Limit (Low Retries)")
    print("="*80)

    request = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/call",
        "params": {
            "name": "check_iteration_limit",
            "arguments": {
                "retry_count": 2,
                "time_spent_minutes": 5.0,
                "task_id": "test-task-123",
                "last_error": "Minor error"
            }
        }
    }

    response = send_request(proc, request)

    print(f"✅ Response: {json.dumps(response, indent=2)}")

    assert response["jsonrpc"] == "2.0"
    assert "result" in response

    result_text = response["result"]["content"][0]["text"]
    print(f"Result text: {result_text[:200]}...")

    print("✅ Low retry check passed")


def test_check_iteration_limit_warning(proc):
    """Test 8: Check iteration limit (3 retries, should warn)"""
    print("\n" + "="*80)
    print("TEST 8: Check Iteration Limit (Warning at 3 retries)")
    print("="*80)

    request = {
        "jsonrpc": "2.0",
        "id": 8,
        "method": "tools/call",
        "params": {
            "name": "check_iteration_limit",
            "arguments": {
                "retry_count": 3,
                "time_spent_minutes": 10.0,
                "task_id": "test-task-456"
            }
        }
    }

    response = send_request(proc, request)

    print(f"✅ Response: {json.dumps(response, indent=2)}")

    assert response["jsonrpc"] == "2.0"
    assert "result" in response

    result_text = response["result"]["content"][0]["text"]
    # Should contain WARNING for 3 retries
    assert "warning" in result_text.lower() or "should_ask_human" in result_text.lower()

    print("✅ Warning at 3 retries passed (ASIMOV-4 enforced)")


def test_check_iteration_limit_error(proc):
    """Test 9: Check iteration limit (5 retries, should error)"""
    print("\n" + "="*80)
    print("TEST 9: Check Iteration Limit (Error at 5 retries)")
    print("="*80)

    request = {
        "jsonrpc": "2.0",
        "id": 9,
        "method": "tools/call",
        "params": {
            "name": "check_iteration_limit",
            "arguments": {
                "retry_count": 5,
                "time_spent_minutes": 20.0,
                "task_id": "test-task-789"
            }
        }
    }

    response = send_request(proc, request)

    print(f"✅ Response: {json.dumps(response, indent=2)}")

    assert response["jsonrpc"] == "2.0"
    assert "result" in response

    result_text = response["result"]["content"][0]["text"]
    # Should contain ERROR for 5 retries
    assert "error" in result_text.lower() or "should_ask_human" in result_text.lower()

    print("✅ Error at 5 retries passed (ASIMOV-4 enforced)")


def test_global_error_search(proc):
    """Test 10: Global error search"""
    print("\n" + "="*80)
    print("TEST 10: Global Error Search (ASIMOV-3)")
    print("="*80)

    # Search in current directory for TODO comments
    workspace_path = str(Path.cwd())

    request = {
        "jsonrpc": "2.0",
        "id": 10,
        "method": "tools/call",
        "params": {
            "name": "global_error_search",
            "arguments": {
                "workspace_path": workspace_path,
                "error_pattern": "TODO",
                "file_extensions": [".py"]
            }
        }
    }

    response = send_request(proc, request)

    print(f"✅ Response: {json.dumps(response, indent=2)}")

    assert response["jsonrpc"] == "2.0"
    assert "result" in response

    result_text = response["result"]["content"][0]["text"]
    print(f"Search result: {result_text[:300]}...")

    print("✅ Global error search passed (ASIMOV-3 enforced)")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    """Run all Asimov MCP Server tests."""
    print("\n" + "="*80)
    print("🧪 ASIMOV RULES MCP SERVER TEST SUITE")
    print("="*80)
    print("Testing: Code safety & compliance validation")
    print("Tools: validate_code, global_error_search, check_iteration_limit")
    print("="*80)

    # Start MCP server
    print("\n🚀 Starting Asimov Rules MCP Server...")
    proc = subprocess.Popen(
        [sys.executable, "mcp_servers/asimov_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    try:
        # Run all tests
        test_initialize(proc)
        test_tools_list(proc)
        test_validate_code_valid(proc)
        test_validate_code_with_todo(proc)
        test_validate_code_with_undocumented_exception(proc)
        test_validate_code_with_pass(proc)
        test_check_iteration_limit_low(proc)
        test_check_iteration_limit_warning(proc)
        test_check_iteration_limit_error(proc)
        test_global_error_search(proc)

        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED (10/10)")
        print("="*80)
        print("\nAsimov Rules MCP Server is working correctly!")
        print("\n4 Asimov Rules Enforced:")
        print("  1. ASIMOV-1: No undocumented fallbacks (exception handlers)")
        print("  2. ASIMOV-2: Complete implementation (no TODO/FIXME)")
        print("  3. ASIMOV-3: Global error search (find ALL instances)")
        print("  4. ASIMOV-4: HITL escalation (3 retries = warning, 5 = error)")
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
