#!/usr/bin/env python3
"""
🔍 DEBUG: Exact Prompts Sent to Claude

This tool captures and analyzes the EXACT prompts (system + combined)
that ReviewFix sends to Claude CLI to verify the instructions are correct.
"""

import sys
import os
from pathlib import Path

# Setup paths
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root / "backend"))

# Monkey-patch to capture prompts
captured_prompts = []

original_call_cli_sync = None

def capture_call_cli_sync(self, messages):
    """Intercept _call_cli_sync to capture prompts."""
    system_prompt, user_prompt = self._extract_system_and_user_prompts(messages)
    combined_prompt = f"{system_prompt}\n\n{user_prompt}"
    
    captured_prompts.append({
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "combined_prompt": combined_prompt
    })
    
    print("\n" + "=" * 100)
    print("🔍 CAPTURED PROMPTS BEING SENT TO CLAUDE CLI")
    print("=" * 100)
    
    print(f"\n📋 SYSTEM PROMPT ({len(system_prompt)} chars):")
    print("-" * 100)
    print(system_prompt)
    print("-" * 100)
    
    print(f"\n📋 USER PROMPT ({len(user_prompt)} chars):")
    print("-" * 100)
    print(user_prompt)
    print("-" * 100)
    
    print(f"\n📋 COMBINED PROMPT ({len(combined_prompt)} chars):")
    print("-" * 100)
    print(combined_prompt[:2000])
    if len(combined_prompt) > 2000:
        print(f"\n... ({len(combined_prompt) - 2000} more chars) ...\n")
        print(combined_prompt[-1000:])
    print("-" * 100)
    
    print("\n⚠️ KEY OBSERVATIONS:")
    
    # Check for validation instructions
    if "validation_passed" in system_prompt:
        print("✅ System prompt contains 'validation_passed' instruction")
    else:
        print("❌ System prompt MISSING 'validation_passed' instruction!")
    
    if "true/false" in system_prompt or "validation_passed" in system_prompt:
        print("✅ System prompt specifies JSON response format")
    else:
        print("❌ System prompt might not clearly specify JSON format!")
    
    if "```json" in system_prompt:
        print("✅ System prompt shows example ```json format")
    else:
        print("⚠️ System prompt might not show markdown JSON format")
    
    # Call original
    return original_call_cli_sync(self, messages)


# Apply monkey-patch
from backend.adapters.claude_cli_simple import ClaudeCLISimple
original_call_cli_sync = ClaudeCLISimple._call_cli_sync
ClaudeCLISimple._call_cli_sync = capture_call_cli_sync

# Now import and test
import asyncio
import tempfile
from backend.utils.mcp_manager import get_mcp_manager


async def test_review_with_prompt_capture():
    """Test ReviewFix to capture prompts."""
    workspace = tempfile.mkdtemp(prefix="prompt_debug_")
    
    # Create simple test
    Path(workspace).joinpath("test.py").write_text("def hello(): return 'world'")
    
    print("\n" + "=" * 100)
    print("🚀 Triggering ReviewFix to capture prompts...")
    print("=" * 100)
    
    mcp = get_mcp_manager(workspace_path=workspace)
    if not mcp._initialized:
        await mcp.initialize()
    
    try:
        result = await mcp.call(
            server="reviewfix",
            tool="review_and_fix",
            arguments={
                "instructions": "Review this code",
                "generated_files": [{"path": "test.py", "content": "def hello(): return 'world'"}],
                "validation_errors": [],
                "workspace_path": workspace,
                "iteration": 1
            },
            timeout=60.0
        )
        print("\n✅ ReviewFix call completed")
    except Exception as e:
        print(f"\n⚠️ ReviewFix call failed (might be timeout): {e}")
    
    # Print captured prompts
    if captured_prompts:
        print("\n" + "=" * 100)
        print("📝 ANALYSIS OF CAPTURED PROMPTS")
        print("=" * 100)
        
        for i, prompt_set in enumerate(captured_prompts, 1):
            print(f"\n📊 Prompt Set {i}:")
            print(f"   System prompt length: {len(prompt_set['system_prompt'])} chars")
            print(f"   User prompt length: {len(prompt_set['user_prompt'])} chars")
            print(f"   Combined length: {len(prompt_set['combined_prompt'])} chars")


if __name__ == "__main__":
    print("🔍 Debugging ReviewFix prompts sent to Claude CLI...")
    print("\nNote: This will attempt to start ReviewFix and capture the prompts.")
    print("It might timeout, but we'll still capture the prompts before execution.\n")
    
    try:
        asyncio.run(test_review_with_prompt_capture())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")