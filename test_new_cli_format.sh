#!/bin/bash

echo "Testing NEW Claude CLI format with --agents"

claude --model claude-sonnet-4-20250514 \
  --agents '{
    "codesmith": {
      "description": "Expert code generator specializing in clean, maintainable code",
      "prompt": "You are an expert code generator. Generate clean, well-documented Python code with proper error handling and type hints.",
      "tools": ["Write"]
    }
  }' \
  --output-format json \
  -p "Create a simple hello.py file that prints Hello World" > /tmp/test_new_format.json 2>&1

echo "Exit code: $?"
echo "Output length: $(wc -c < /tmp/test_new_format.json) bytes"
echo ""
echo "Is valid JSON:"
python3 -m json.tool /tmp/test_new_format.json > /dev/null 2>&1 && echo "✅ YES" || echo "❌ NO"

if python3 -m json.tool /tmp/test_new_format.json > /dev/null 2>&1; then
    echo ""
    echo "JSON structure:"
    python3 -c "import json; data=json.load(open('/tmp/test_new_format.json')); print('Keys:', list(data.keys())); print('Result length:', len(data.get('result', '')))"
    echo ""
    echo "Result preview (first 500 chars):"
    python3 -c "import json; data=json.load(open('/tmp/test_new_format.json')); print(data.get('result', '')[:500])"
fi
