#!/bin/bash

echo "Testing Claude CLI JSON output..."

# Test 1: Simple prompt
echo "Test 1: Simple single-line response"
claude --print --output-format json --model claude-sonnet-4-20250514 "Say hello" > /tmp/test1.json 2>&1

echo "Raw output:"
cat /tmp/test1.json

echo -e "\nValidating JSON:"
python3 -m json.tool /tmp/test1.json > /dev/null 2>&1 && echo "✅ Valid JSON" || echo "❌ Invalid JSON"

# Test 2: Multi-line code generation
echo -e "\n\n=========================================="
echo "Test 2: Multi-line code generation"
echo "=========================================="
claude --print --output-format json --model claude-sonnet-4-20250514 "Generate a Python function that adds two numbers" > /tmp/test2.json 2>&1

echo "Raw output (first 1000 chars):"
head -c 1000 /tmp/test2.json

echo -e "\n\nValidating JSON:"
python3 -m json.tool /tmp/test2.json > /dev/null 2>&1 && echo "✅ Valid JSON" || echo "❌ Invalid JSON"

# Test 3: Large code output (like our use case)
echo -e "\n\n=========================================="
echo "Test 3: Complete file generation"
echo "=========================================="
claude --print --output-format json --model claude-sonnet-4-20250514 "Generate a complete Python calculator module with add, subtract, multiply, divide functions" > /tmp/test3.json 2>&1

echo "Raw output length:"
wc -c /tmp/test3.json

echo "Validating JSON:"
python3 -m json.tool /tmp/test3.json > /dev/null 2>&1 && echo "✅ Valid JSON" || echo "❌ Invalid JSON"

# If invalid, show the error
if ! python3 -m json.tool /tmp/test3.json > /dev/null 2>&1; then
    echo -e "\nJSON Error:"
    python3 -m json.tool /tmp/test3.json 2>&1 | head -20

    echo -e "\nRaw output around start:"
    head -c 500 /tmp/test3.json

    echo -e "\n\nRaw output around end:"
    tail -c 500 /tmp/test3.json
fi

echo -e "\n\n=========================================="
echo "Summary"
echo "=========================================="
echo "Test 1 (simple): $(python3 -m json.tool /tmp/test1.json > /dev/null 2>&1 && echo '✅ Valid' || echo '❌ Invalid')"
echo "Test 2 (function): $(python3 -m json.tool /tmp/test2.json > /dev/null 2>&1 && echo '✅ Valid' || echo '❌ Invalid')"
echo "Test 3 (module): $(python3 -m json.tool /tmp/test3.json > /dev/null 2>&1 && echo '✅ Valid' || echo '❌ Invalid')"
