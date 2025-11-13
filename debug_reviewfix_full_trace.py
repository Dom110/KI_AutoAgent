#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE ReviewFix Debug Trace

This script debugs the entire ReviewFix → Claude CLI chain to understand:
1. What ReviewFix sends to Claude CLI
2. What Claude CLI's raw response is
3. What validation Claude returns
4. Why validation always fails

Enables:
- DEBUG_MODE in claude_cli_server
- Enhanced logging in reviewfix_agent_server
- Temp file capture and display
- Full event tracing
"""

import asyncio
import json
import sys
import os
import tempfile
import logging
from pathlib import Path
from datetime import datetime

# Setup paths
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root / "backend"))
sys.path.insert(0, str(repo_root))

# ENABLE DEBUG MODE FOR CLAUDE CLI
os.environ["DEBUG_MODE"] = "true"

# Setup comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/reviewfix_debug.log')
    ]
)
logger = logging.getLogger("reviewfix_debug")

# Import after setting up paths
from backend.utils.mcp_manager import get_mcp_manager


async def create_test_workspace():
    """Create a minimal test workspace with simple code."""
    workspace = tempfile.mkdtemp(prefix="reviewfix_test_")
    logger.info(f"📁 Created test workspace: {workspace}")
    
    # Create a simple Python file with intentional "issues" that shouldn't fail validation
    test_file = Path(workspace) / "hello.py"
    test_file.write_text("""
def greet(name):
    '''Simple greeting function.'''
    return f"Hello, {name}!"

def main():
    print(greet("World"))

if __name__ == "__main__":
    main()
""")
    logger.info(f"✅ Created test file: {test_file}")
    
    # Create a simple test file
    test_runner = Path(workspace) / "test_hello.py"
    test_runner.write_text("""
import pytest
from hello import greet

def test_greet():
    assert greet("Alice") == "Hello, Alice!"
    assert greet("Bob") == "Hello, Bob!"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
""")
    logger.info(f"✅ Created test file: {test_runner}")
    
    return workspace


async def debug_reviewfix_call(workspace_path: str):
    """Call ReviewFix and capture all debug information."""
    logger.info("=" * 80)
    logger.info("🚀 Starting ReviewFix Debug Trace")
    logger.info("=" * 80)
    
    # Get MCP manager
    mcp = get_mcp_manager(workspace_path=workspace_path)
    
    if not mcp._initialized:
        logger.info("⏳ Initializing MCP manager...")
        await mcp.initialize()
    
    # Prepare ReviewFix request
    instruction = """
    Review and validate the code:
    1. Read all files
    2. Run tests to check for errors
    3. Report validation result
    4. Return validation_passed as boolean based on test results
    """
    
    generated_files = [
        {
            "path": "hello.py",
            "content": (Path(workspace_path) / "hello.py").read_text()
        }
    ]
    
    logger.info(f"📤 Calling ReviewFix with:")
    logger.info(f"   - Workspace: {workspace_path}")
    logger.info(f"   - Generated files: {len(generated_files)}")
    logger.info(f"   - Instructions: {instruction[:100]}...")
    
    try:
        # Call ReviewFix via MCP
        result = await mcp.call(
            server="reviewfix",
            tool="review_and_fix",
            arguments={
                "instructions": instruction,
                "generated_files": generated_files,
                "validation_errors": [],
                "workspace_path": workspace_path,
                "iteration": 1
            },
            timeout=300.0
        )
        
        logger.info("=" * 80)
        logger.info("✅ ReviewFix Call Completed")
        logger.info("=" * 80)
        
        # Parse result
        result_content = result.get("content", "")
        if isinstance(result_content, list) and len(result_content) > 0:
            result_text = result_content[0].get("text", "") if isinstance(result_content[0], dict) else str(result_content[0])
        else:
            result_text = str(result_content)
        
        logger.info(f"\n📊 Raw Result ({len(result_text)} chars):")
        logger.info(f"\n{result_text}")
        
        # Parse JSON result
        try:
            parsed = json.loads(result_text)
            logger.info(f"\n✅ Parsed JSON successfully")
            logger.info(f"\n🔍 Result breakdown:")
            logger.info(f"   - validation_passed: {parsed.get('validation_passed')}")
            logger.info(f"   - fixed_files: {len(parsed.get('fixed_files', []))} files")
            logger.info(f"   - remaining_errors: {len(parsed.get('remaining_errors', []))} errors")
            logger.info(f"   - tests_passing: {parsed.get('tests_passing', [])}")
            logger.info(f"   - fix_summary: {parsed.get('fix_summary', '')[:200]}")
            
            if parsed.get('remaining_errors'):
                logger.warning(f"\n⚠️ Remaining errors:")
                for err in parsed.get('remaining_errors', []):
                    logger.warning(f"   - {err}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse result JSON: {e}")
        
    except Exception as e:
        logger.error(f"❌ ReviewFix call failed: {e}", exc_info=True)
    
    # Look for temp files created by Claude CLI
    logger.info("\n" + "=" * 80)
    logger.info("🔍 Checking for Claude CLI temp files")
    logger.info("=" * 80)
    
    tmp_dir = Path(tempfile.gettempdir())
    claude_files = list(tmp_dir.glob("*claude*"))
    
    if claude_files:
        logger.info(f"\nFound {len(claude_files)} Claude temp files:")
        # Get most recent ones
        claude_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        for i, filepath in enumerate(claude_files[:5]):  # Show last 5
            logger.info(f"\n📄 File {i+1}: {filepath.name}")
            logger.info(f"   Size: {filepath.stat().st_size} bytes")
            logger.info(f"   Modified: {datetime.fromtimestamp(filepath.stat().st_mtime)}")
            
            # Try to read and display
            try:
                content = filepath.read_text()
                if len(content) > 2000:
                    logger.info(f"   Content (first 1000 chars):\n{content[:1000]}")
                    logger.info(f"   Content (last 500 chars):\n{content[-500:]}")
                else:
                    logger.info(f"   Content:\n{content}")
            except Exception as e:
                logger.error(f"   ❌ Failed to read: {e}")
    else:
        logger.warning("\n❌ No Claude temp files found!")
    
    logger.info("\n" + "=" * 80)
    logger.info("📋 Debug log saved to: /tmp/reviewfix_debug.log")
    logger.info("=" * 80)


async def main():
    """Main debug function."""
    try:
        # Create test workspace
        workspace = await create_test_workspace()
        
        # Run debug trace
        await debug_reviewfix_call(workspace)
        
        logger.info("\n✅ Debug trace complete!")
        
    except Exception as e:
        logger.error(f"❌ Debug failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())