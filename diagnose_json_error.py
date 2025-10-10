#!/usr/bin/env python3
"""
Diagnose Claude CLI JSON parsing error
"""

import json
import sys
from pathlib import Path

def analyze_json_error(file_path):
    """Analyze JSON parsing error in detail"""

    file_path = Path(file_path)
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False

    with open(file_path, 'rb') as f:
        raw_bytes = f.read()

    print(f"📁 File: {file_path.name}")
    print(f"📊 File size: {len(raw_bytes)} bytes")

    print(f"\n🔍 First 200 bytes (raw):")
    print(raw_bytes[:200])

    print(f"\n🔍 First 500 chars (decoded):")
    raw_str = raw_bytes.decode('utf-8', errors='replace')
    print(raw_str[:500])

    print(f"\n🔍 Last 500 chars:")
    print(raw_str[-500:])

    # Try to parse
    try:
        data = json.loads(raw_str)
        print(f"\n✅ JSON is VALID!")
        print(f"Keys: {list(data.keys())}")

        if 'result' in data:
            result_len = len(data.get('result', ''))
            print(f"Result field length: {result_len} chars")
            print(f"Result preview (first 200 chars):")
            print(data['result'][:200])

        return True

    except json.JSONDecodeError as e:
        print(f"\n❌ JSON is INVALID!")
        print(f"Error: {e}")
        print(f"Error position: line {e.lineno}, column {e.colno}, char {e.pos}")

        # Show context around error
        if e.pos and e.pos < len(raw_str):
            start = max(0, e.pos - 100)
            end = min(len(raw_str), e.pos + 100)
            context = raw_str[start:end]

            print(f"\n🔍 Context around error (±100 chars):")
            print(repr(context))

            # Show pointer to error position
            pointer_pos = e.pos - start
            print(" " * pointer_pos + "^ ERROR HERE")

            # Analyze the error position
            error_char = raw_str[e.pos] if e.pos < len(raw_str) else "EOF"
            print(f"\n🔍 Character at error position: {repr(error_char)}")

            # Check surrounding characters
            if e.pos > 0:
                print(f"Previous 10 chars: {repr(raw_str[max(0, e.pos-10):e.pos])}")
            if e.pos < len(raw_str) - 1:
                print(f"Next 10 chars: {repr(raw_str[e.pos:min(len(raw_str), e.pos+10)])}")

        # Check if result field exists
        if '"result"' in raw_str:
            result_start = raw_str.find('"result"')
            result_colon = raw_str.find(':', result_start)
            result_quote = raw_str.find('"', result_colon)

            print(f"\n🔍 Result field found at position {result_start}")
            print(f"Result value starts at position {result_quote}")
            print(f"Context: {repr(raw_str[result_start:result_start+200])}")

            # Count newlines in result field (estimate)
            # Find closing of JSON (rough estimate)
            result_section = raw_str[result_quote+1:]
            newline_count = result_section.count('\n')
            print(f"\n🔍 Estimated newlines after result field: {newline_count}")

        # Check JSON structure
        open_braces = raw_str.count('{')
        close_braces = raw_str.count('}')
        open_brackets = raw_str.count('[')
        close_brackets = raw_str.count(']')

        print(f"\n🔍 JSON structure:")
        print(f"   Open braces: {open_braces}, Close braces: {close_braces}")
        print(f"   Open brackets: {open_brackets}, Close brackets: {close_brackets}")

        if open_braces != close_braces:
            print(f"   ⚠️ UNBALANCED BRACES!")
        if open_brackets != close_brackets:
            print(f"   ⚠️ UNBALANCED BRACKETS!")

        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: diagnose_json_error.py <json_file>")
        sys.exit(1)

    success = analyze_json_error(sys.argv[1])
    sys.exit(0 if success else 1)
