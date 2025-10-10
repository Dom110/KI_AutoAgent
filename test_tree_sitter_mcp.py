#!/usr/bin/env python3
"""
Test Tree-sitter MCP Server

Tests the Tree-sitter MCP server functionality with various code analysis operations.

Usage:
    python test_tree_sitter_mcp.py
"""

import subprocess
import json
import sys
import time


def test_tree_sitter_mcp():
    """Test the Tree-sitter MCP server."""

    print("🧪 Testing Tree-sitter MCP Server\n")
    print("=" * 80)

    # Start the MCP server (use venv Python for dependencies)
    print("\n1️⃣ Starting Tree-sitter MCP server...")
    proc = subprocess.Popen(
        ["backend/venv_v6/bin/python", "mcp_servers/tree_sitter_server.py"],
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

    if response.get("result", {}).get("serverInfo", {}).get("name") == "tree-sitter-mcp-server":
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
    expected_tools = ["validate_syntax", "parse_code", "analyze_file", "analyze_directory"]

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

    # Test 3: validate_syntax with VALID Python code
    print("\n4️⃣ Test 3: Validate Syntax (Valid Python)")

    valid_code = """
def greet(name):
    return f"Hello, {name}!"

result = greet("World")
print(result)
"""

    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "validate_syntax",
            "arguments": {
                "code": valid_code,
                "language": "python"
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
            # Check if result contains "valid": true
            if '"valid": true' in text:
                print("   ✅ Valid code recognized correctly")
                print("      Code passed syntax validation")
                tests_passed += 1
            else:
                print("   ❌ Valid code marked as invalid")
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

    # Test 4: validate_syntax with INVALID Python code
    print("\n5️⃣ Test 4: Validate Syntax (Invalid Python)")

    invalid_code = """
def broken_function(
    print("Missing closing parenthesis"
    return "This won't work"
"""

    request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "validate_syntax",
            "arguments": {
                "code": invalid_code,
                "language": "python"
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
            # Check if result contains "valid": false
            if '"valid": false' in text:
                print("   ✅ Invalid code detected correctly")
                print("      Syntax errors found as expected")
                tests_passed += 1
            else:
                print("   ❌ Invalid code marked as valid")
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

    # Test 5: parse_code
    print("\n6️⃣ Test 5: Parse Code (Extract Functions & Classes)")

    code_to_parse = """
class Calculator:
    def __init__(self):
        self.result = 0

    def add(self, x, y):
        return x + y

    def subtract(self, x, y):
        return x - y

def main():
    calc = Calculator()
    print(calc.add(5, 3))
"""

    request = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "parse_code",
            "arguments": {
                "code": code_to_parse,
                "language": "python"
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
            # Check if we found classes and functions
            has_classes = '"classes":' in text and "Calculator" in text
            has_functions = '"functions":' in text and ("add" in text or "main" in text)

            if has_classes and has_functions:
                print("   ✅ Code parsed successfully")
                print("      Found classes and functions")
                # Try to extract counts
                if '"classes":' in text:
                    try:
                        # Simple extraction
                        classes_section = text.split('"classes":')[1].split(']')[0]
                        class_count = classes_section.count('"name":')
                        print(f"      Classes detected: {class_count}")
                    except:
                        pass
                tests_passed += 1
            else:
                print("   ❌ Parsing incomplete")
                print(f"      Has classes: {has_classes}")
                print(f"      Has functions: {has_functions}")
                print(f"      Response preview: {text[:300]}...")
                tests_failed += 1
        else:
            print("   ❌ Empty response")
            tests_failed += 1
    else:
        print("   ❌ Tool call failed")
        error = response.get("error", {})
        print(f"      Error: {error.get('message', 'Unknown error')}")
        tests_failed += 1

    # Test 6: Validate JavaScript code
    print("\n7️⃣ Test 6: Validate JavaScript Code")

    js_code = """
function greet(name) {
    return `Hello, ${name}!`;
}

const result = greet("World");
console.log(result);
"""

    request = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "validate_syntax",
            "arguments": {
                "code": js_code,
                "language": "javascript"
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
            if '"valid": true' in text and '"language": "javascript"' in text:
                print("   ✅ JavaScript code validated successfully")
                tests_passed += 1
            else:
                print("   ❌ JavaScript validation failed")
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

    # Cleanup
    print("\n8️⃣ Cleaning up...")
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
        print("     claude mcp add tree-sitter python mcp_servers/tree_sitter_server.py")
        print("\n  2. Verify registration:")
        print("     claude mcp list")
        print("\n  3. Test with Claude:")
        print('     claude "Validate this Python code: print(\'hello\')"')
        print('     claude "Parse this code and show me the functions"')
        print("\n  4. Claude will automatically use tree-sitter tools when appropriate!")
        print("\n📚 Available Tools:")
        print("   - validate_syntax: Check if code is syntactically valid")
        print("   - parse_code: Extract functions, classes, imports from code")
        print("   - analyze_file: Analyze a single file")
        print("   - analyze_directory: Analyze entire codebase")
        return True
    else:
        print("\n❌ SOME TESTS FAILED")
        print("\nPlease review errors above.")
        return False


if __name__ == "__main__":
    success = test_tree_sitter_mcp()
    sys.exit(0 if success else 1)
