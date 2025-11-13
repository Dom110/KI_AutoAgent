#!/usr/bin/env python3
"""
🔬 DETAILED ReviewFix Validation Logic Analyzer

This script investigates WHY Claude always returns validation_passed: false
by examining:
1. The exact prompts sent to Claude
2. The HITL events (what tools Claude actually used)
3. The JSON response structure
4. Whether the "validation_passed" decision logic is working
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime
import tempfile

# Setup paths
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root / "backend"))
sys.path.insert(0, str(repo_root))

# ENABLE DEBUG MODE
os.environ["DEBUG_MODE"] = "true"

# Setup logging to both console and file
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/reviewfix_validation_debug.log')
    ]
)
logger = logging.getLogger("validation_debug")

# Import after setup
from backend.utils.mcp_manager import get_mcp_manager


async def create_minimal_test_workspace():
    """Create the SIMPLEST possible test workspace."""
    workspace = tempfile.mkdtemp(prefix="reviewfix_validation_test_")
    logger.info(f"📁 Test workspace: {workspace}")
    
    # SIMPLEST possible code - just a function
    code_file = Path(workspace) / "simple.py"
    code_file.write_text('''def add(a, b):
    """Add two numbers."""
    return a + b
''')
    
    # SIMPLEST possible test
    test_file = Path(workspace) / "test_simple.py"
    test_file.write_text('''def test_add():
    from simple import add
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    print("✅ All tests passed!")
''')
    
    logger.info(f"✅ Created minimal code and test")
    return workspace


async def analyze_reviewfix_response():
    """Analyze ReviewFix response in detail."""
    logger.info("\n" + "=" * 100)
    logger.info("🔬 VALIDATION LOGIC ANALYSIS")
    logger.info("=" * 100)
    
    # Create workspace
    workspace = await create_minimal_test_workspace()
    
    # Get MCP manager
    mcp = get_mcp_manager(workspace_path=workspace)
    if not mcp._initialized:
        await mcp.initialize()
    
    # Prepare ReviewFix call with VERY CLEAR instructions
    instruction = """
TASK: Validate this simple Python code.

The code has NO errors - it's already correct.
Just:
1. Read the files
2. Run the test
3. Confirm test passes
4. Return validation_passed: true

This is a PASSING validation scenario."""
    
    generated_files = [
        {
            "path": "simple.py",
            "content": (Path(workspace) / "simple.py").read_text()
        }
    ]
    
    logger.info("\n" + "=" * 100)
    logger.info("📤 SENDING TO REVIEWFIX")
    logger.info("=" * 100)
    logger.info(f"\n✅ Instruction (very clear):")
    logger.info(f"   {instruction}")
    logger.info(f"\n✅ File to review:")
    logger.info(f"   simple.py ({len(generated_files[0]['content'])} chars)")
    
    try:
        # Call ReviewFix
        result = await mcp.call(
            server="reviewfix",
            tool="review_and_fix",
            arguments={
                "instructions": instruction,
                "generated_files": generated_files,
                "validation_errors": [],
                "workspace_path": workspace,
                "iteration": 1
            },
            timeout=300.0
        )
        
        logger.info("\n" + "=" * 100)
        logger.info("📥 REVIEWFIX RESPONSE ANALYSIS")
        logger.info("=" * 100)
        
        # Extract content
        result_content = result.get("content", "")
        if isinstance(result_content, list) and len(result_content) > 0:
            result_text = result_content[0].get("text", "") if isinstance(result_content[0], dict) else str(result_content[0])
        else:
            result_text = str(result_content)
        
        logger.info(f"\n📊 Response size: {len(result_text)} characters")
        
        # Parse JSON
        try:
            parsed = json.loads(result_text)
            
            logger.info(f"\n✅ JSON PARSED SUCCESSFULLY")
            logger.info(f"\n🔍 KEY FIELDS:")
            logger.info(f"   validation_passed: {parsed.get('validation_passed')}")
            logger.info(f"   fixed_files: {len(parsed.get('fixed_files', []))} files")
            logger.info(f"   remaining_errors: {len(parsed.get('remaining_errors', []))} errors")
            logger.info(f"   tests_passing: {parsed.get('tests_passing', [])}")
            logger.info(f"   fix_summary: {parsed.get('fix_summary', '')[:100]}...")
            
            # CRITICAL ANALYSIS
            logger.info(f"\n🎯 CRITICAL ANALYSIS:")
            
            validation_result = parsed.get('validation_passed', False)
            remaining_errors = parsed.get('remaining_errors', [])
            tests_passing = parsed.get('tests_passing', [])
            
            if not validation_result and len(remaining_errors) == 0:
                logger.warning(f"\n⚠️ ANOMALY DETECTED!")
                logger.warning(f"   validation_passed = false")
                logger.warning(f"   BUT remaining_errors is EMPTY")
                logger.warning(f"   This suggests validation is conservatively failing")
                logger.warning(f"   even though there are no errors!")
            
            if not validation_result and len(tests_passing) > 0:
                logger.warning(f"\n⚠️ CONTRADICTION DETECTED!")
                logger.warning(f"   validation_passed = false")
                logger.warning(f"   BUT tests_passing = {tests_passing}")
                logger.warning(f"   Tests passed but validation still failed?")
            
            if validation_result:
                logger.info(f"\n✅ VALIDATION PASSED - Expected behavior")
            else:
                logger.error(f"\n❌ VALIDATION FAILED - UNEXPECTED for simple code!")
                logger.error(f"   This needs investigation!")
            
        except json.JSONDecodeError as e:
            logger.error(f"\n❌ Failed to parse JSON: {e}")
            logger.error(f"\nRaw response (first 2000 chars):")
            logger.error(f"{result_text[:2000]}")
            logger.error(f"\nRaw response (last 500 chars):")
            logger.error(f"{result_text[-500:]}")
        
        # Check for HITL events
        logger.info(f"\n" + "=" * 100)
        logger.info(f"🎯 HITL EVENTS FROM CLAUDE CLI")
        logger.info(f"=" * 100)
        
        if "hitl_events_from_claude" in result:
            events = result.get("hitl_events_from_claude", [])
            logger.info(f"\n✅ Found {len(events)} HITL events:")
            
            for event_info in events[:10]:  # Show first 10
                idx = event_info.get("index")
                event_type = event_info.get("type")
                logger.info(f"   [{idx}] {event_type}")
        else:
            logger.warning(f"\n❌ No HITL events captured!")
        
        # Show full response for inspection
        logger.info(f"\n" + "=" * 100)
        logger.info(f"📋 FULL RESPONSE (for inspection)")
        logger.info(f"=" * 100)
        logger.info(f"\n{json.dumps(parsed, indent=2) if isinstance(result_text, str) and result_text.startswith('{') else result_text[:1000]}")
        
    except Exception as e:
        logger.error(f"❌ ReviewFix call failed: {e}", exc_info=True)
    
    logger.info(f"\n" + "=" * 100)
    logger.info(f"📝 Debug log: /tmp/reviewfix_validation_debug.log")
    logger.info(f"=" * 100)


if __name__ == "__main__":
    asyncio.run(analyze_reviewfix_response())