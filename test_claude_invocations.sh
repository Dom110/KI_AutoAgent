#!/bin/bash

PROMPT="Generate a Python function that adds two numbers. Output should start with 'def add'"

echo "=========================================="
echo "Test 1: --print (current method - NO json flag)"
echo "=========================================="
claude --print --model claude-sonnet-4-20250514 "$PROMPT" > /tmp/test_print.txt 2>&1
echo "Exit code: $?"
echo "Output length: $(wc -c < /tmp/test_print.txt) bytes"
echo "First 200 chars:"
head -c 200 /tmp/test_print.txt
echo ""
echo "Is valid JSON: $(python3 -m json.tool /tmp/test_print.txt > /dev/null 2>&1 && echo 'YES' || echo 'NO')"

echo -e "\n\n=========================================="
echo "Test 2: --print with --output-format json"
echo "=========================================="
claude --print --output-format json --model claude-sonnet-4-20250514 "$PROMPT" > /tmp/test_json.txt 2>&1
echo "Exit code: $?"
echo "Output length: $(wc -c < /tmp/test_json.txt) bytes"
echo "Is valid JSON: $(python3 -m json.tool /tmp/test_json.txt > /dev/null 2>&1 && echo 'YES' || echo 'NO')"
if python3 -m json.tool /tmp/test_json.txt > /dev/null 2>&1; then
    echo "JSON keys:"
    python3 -c "import json; data=json.load(open('/tmp/test_json.txt')); print(list(data.keys()))"
fi

echo -e "\n\n=========================================="
echo "Test 3: -p parameter (short form)"
echo "=========================================="
claude -p --output-format json --model claude-sonnet-4-20250514 "$PROMPT" > /tmp/test_p.txt 2>&1
echo "Exit code: $?"
echo "Output length: $(wc -c < /tmp/test_p.txt) bytes"
echo "Is valid JSON: $(python3 -m json.tool /tmp/test_p.txt > /dev/null 2>&1 && echo 'YES' || echo 'NO')"

echo -e "\n\n=========================================="
echo "Test 4: --output-format text (explicit)"
echo "=========================================="
claude --print --output-format text --model claude-sonnet-4-20250514 "$PROMPT" > /tmp/test_text.txt 2>&1
echo "Exit code: $?"
echo "Output length: $(wc -c < /tmp/test_text.txt) bytes"
echo "First 200 chars:"
head -c 200 /tmp/test_text.txt

echo -e "\n\n=========================================="
echo "SUMMARY"
echo "=========================================="
echo "Test 1 (--print, no format):     $(python3 -m json.tool /tmp/test_print.txt > /dev/null 2>&1 && echo 'JSON' || echo 'PLAIN TEXT')"
echo "Test 2 (--print --output-format json): $(python3 -m json.tool /tmp/test_json.txt > /dev/null 2>&1 && echo 'JSON ✅' || echo 'INVALID')"
echo "Test 3 (-p --output-format json):      $(python3 -m json.tool /tmp/test_p.txt > /dev/null 2>&1 && echo 'JSON ✅' || echo 'INVALID')"
echo "Test 4 (--output-format text):         $(python3 -m json.tool /tmp/test_text.txt > /dev/null 2>&1 && echo 'JSON' || echo 'PLAIN TEXT ✅')"
