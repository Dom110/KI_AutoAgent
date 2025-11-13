#!/usr/bin/env python3
"""
Test: JSON Markdown block extraction fix
Testet, ob JSON aus ```json...``` blocks korrekt extrahiert wird
"""
import json
import re

def test_markdown_json_extraction():
    """Testet die Markdown JSON Extraction"""
    
    # Test Case 1: Mit Markdown code blocks (wie OpenAI zurückgibt)
    test_response_1 = '''```json
{
  "action": "CONTINUE",
  "next_agent": "research",
  "parallel_agents": null,
  "instructions": "Analyze the workspace..."
}
```'''
    
    # Test Case 2: Reines JSON (ideal)
    test_response_2 = '''{
  "action": "CONTINUE",
  "next_agent": "research",
  "parallel_agents": null,
  "instructions": "Analyze the workspace..."
}'''
    
    # Test Case 3: JSON mit extra Text vorher
    test_response_3 = '''Here is the JSON response:

```json
{
  "action": "END",
  "next_agent": null,
  "parallel_agents": null,
  "instructions": "Task complete"
}
```

That's my decision.'''
    
    print("="*80)
    print("🧪 TEST: JSON Markdown Block Extraction")
    print("="*80 + "\n")
    
    test_cases = [
        ("Markdown code block (OpenAI default)", test_response_1),
        ("Pure JSON", test_response_2),
        ("JSON with surrounding text", test_response_3),
    ]
    
    for test_name, content in test_cases:
        print(f"Test Case: {test_name}")
        print(f"Input: {content[:50]}..." if len(content) > 50 else f"Input: {content}")
        
        # Apply IMPROVED extraction logic
        content_to_parse = content
        
        # Try to parse directly first
        try:
            json_data = json.loads(content_to_parse)
            print(f"  ✅ SUCCESS: Parsed directly as JSON")
            print(f"     Keys: {list(json_data.keys())}")
            print(f"     Action: {json_data.get('action', 'N/A')}")
        except json.JSONDecodeError:
            # Direct parse failed - try extraction from Markdown blocks
            print(f"  ℹ️  Direct parse failed - attempting extraction...")
            
            if "```" in content_to_parse:
                print("  ✓ Detected Markdown code block")
                # Find the opening {
                json_start = content_to_parse.find('{')
                if json_start != -1:
                    # Find the matching closing }
                    json_end = content_to_parse.rfind('}') + 1
                    if json_end > json_start:
                        content_to_parse = content_to_parse[json_start:json_end]
                        print(f"  ✓ Extracted JSON ({len(content_to_parse)} chars)")
                        
                        try:
                            json_data = json.loads(content_to_parse)
                            print(f"  ✅ SUCCESS: Extracted JSON parsed correctly")
                            print(f"     Keys: {list(json_data.keys())}")
                            print(f"     Action: {json_data.get('action', 'N/A')}")
                        except json.JSONDecodeError as e:
                            print(f"  ❌ FAILED: Extracted JSON is invalid: {str(e)}")
                    else:
                        print(f"  ❌ FAILED: No JSON braces found")
                else:
                    print(f"  ❌ FAILED: No opening brace found")
            else:
                print(f"  ❌ FAILED: No Markdown blocks and invalid JSON")
        
        print()
    
    print("="*80)
    print("✅ All extraction tests completed!")
    print("="*80)

if __name__ == "__main__":
    test_markdown_json_extraction()
