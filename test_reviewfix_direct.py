#!/usr/bin/env python3
"""
Direct test of ReviewFix agent - test what it actually returns.
"""

import asyncio
import subprocess
import sys
import time
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.utils.mcp_manager import MCPManager

async def test_reviewfix():
    """Test ReviewFix directly."""
    
    print("=" * 80)
    print("🧪 DIRECT REVIEWFIX TEST")
    print("=" * 80)
    
    # Initialize MCPManager
    mcp = MCPManager(workspace_path="/tmp/test_workspace")
    
    try:
        print("\n1️⃣ Initializing MCPManager...")
        await mcp.initialize()
        print("   ✅ MCPManager initialized")
        
        print("\n2️⃣ Calling ReviewFix with test data...")
        result = await mcp.call(
            server="reviewfix_agent",
            tool="review_and_fix",
            arguments={
                "instructions": "Create a simple Hello World function in Python",
                "generated_files": [
                    {
                        "path": "hello.py",
                        "description": "Hello World function",
                        "content": "def hello():\n    print('Hello, World!')"
                    }
                ],
                "validation_errors": [],
                "iteration": 1
            },
            timeout=30.0  # 30 second timeout for testing
        )
        
        print("\n3️⃣ ReviewFix Result:")
        print(json.dumps(result, indent=2))
        
        print("\n4️⃣ Analyzing result...")
        
        # Parse the result
        if "content" in result and len(result["content"]) > 0:
            content = result["content"][0]
            if "text" in content:
                text = content["text"]
                try:
                    review_data = json.loads(text)
                    print(f"   ✅ Parsed JSON from ReviewFix")
                    print(f"   validation_passed: {review_data.get('validation_passed')}")
                    print(f"   fixed_files: {review_data.get('fixed_files', [])}")
                    print(f"   remaining_errors: {review_data.get('remaining_errors', [])}")
                except json.JSONDecodeError as e:
                    print(f"   ❌ Failed to parse JSON: {e}")
                    print(f"   Raw text: {text[:500]}")
        
        if "metadata" in result:
            print(f"\n   Metadata:")
            print(json.dumps(result["metadata"], indent=4))
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n5️⃣ Cleaning up...")
        await mcp.close()
        print("   ✅ Done")

if __name__ == "__main__":
    asyncio.run(test_reviewfix())