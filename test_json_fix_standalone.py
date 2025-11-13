#!/usr/bin/env python3
"""
Standalone Test: JSON Markdown block extraction fix
Keine Imports - nur die Logik testen
"""

import json
from pydantic import BaseModel

class TestDecision(BaseModel):
    action: str
    confidence: float

def extract_and_parse_json(content: str) -> dict:
    """Repliziert die JSON Parsing Logik aus base.py"""
    content_to_parse = content
    
    # Try direct parse first
    try:
        json_data = json.loads(content_to_parse)
        return json_data
    except json.JSONDecodeError:
        pass
    
    # Try extraction from Markdown blocks
    if "```" in content_to_parse:
        # Find the opening {
        json_start = content_to_parse.find('{')
        if json_start != -1:
            # Find the matching closing }
            json_end = content_to_parse.rfind('}') + 1
            if json_end > json_start:
                content_to_parse = content_to_parse[json_start:json_end]
                
                # Try parsing the extracted JSON
                try:
                    json_data = json.loads(content_to_parse)
                    return json_data
                except json.JSONDecodeError as e:
                    raise ValueError(f"Extracted JSON is not valid: {str(e)}")
            else:
                raise ValueError("No JSON braces found")
        else:
            raise ValueError("No opening brace found")
    else:
        raise ValueError("No Markdown blocks and invalid JSON")

def main():
    print("="*80)
    print("🧪 Standalone Test: JSON Markdown Extraction Fix")
    print("="*80 + "\n")
    
    # Test Case 1: Markdown code block (wie OpenAI zurückgibt)
    test_case_1 = '''```json
{
  "action": "CONTINUE",
  "confidence": 0.95
}
```'''
    
    # Test Case 2: Reines JSON
    test_case_2 = '''{
  "action": "END",
  "confidence": 0.98
}'''
    
    # Test Case 3: JSON mit umgebender Text
    test_case_3 = '''Here's my decision:

```json
{
  "action": "RETRY",
  "confidence": 0.87
}
```

Hope this helps!'''
    
    test_cases = [
        ("Markdown code block", test_case_1, "CONTINUE"),
        ("Pure JSON", test_case_2, "END"),
        ("JSON with surrounding text", test_case_3, "RETRY"),
    ]
    
    successes = 0
    
    for test_name, content, expected_action in test_cases:
        print(f"Test Case: {test_name}")
        print(f"Input: {content[:50]}...")
        
        try:
            json_data = extract_and_parse_json(content)
            print(f"  ✓ JSON extracted and parsed")
            
            # Validate with Pydantic
            result = TestDecision(**json_data)
            if result.action == expected_action:
                print(f"  ✅ SUCCESS: Parsed as '{result.action}'")
                print(f"     Confidence: {result.confidence}")
                successes += 1
            else:
                print(f"  ❌ Wrong action: {result.action} != {expected_action}")
        except Exception as e:
            print(f"  ❌ FAILED: {str(e)}")
        
        print()
    
    print("="*80)
    print(f"📊 RESULT: {successes}/{len(test_cases)} tests passed")
    print("="*80)
    
    if successes == len(test_cases):
        print("✅ All tests PASSED - JSON Markdown extraction works!")
        return True
    else:
        print("❌ Some tests FAILED")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
