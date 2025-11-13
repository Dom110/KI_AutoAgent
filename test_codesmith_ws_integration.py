#!/usr/bin/env python3
"""
🧪 INTEGRATION TEST: Codesmith Workspace Isolation in MCP Server

Tests that the CodesmithWorkspaceManager is properly integrated
into the codesmith_agent_server.py MCP server.
"""

import sys
import tempfile
import asyncio
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - [%(levelname)s] %(message)s')
logger = logging.getLogger("test_integration")

# Add mcp_servers to path
sys.path.insert(0, '/Users/dominikfoert/git/KI_AutoAgent/mcp_servers')

async def test_workspace_manager_integration():
    """Test that CodesmithWorkspaceManager is importable and works"""
    logger.info("\n" + "="*80)
    logger.info("TEST: CodesmithWorkspaceManager Integration")
    logger.info("="*80)
    
    # Import the server module
    try:
        from codesmith_agent_server import CodesmithWorkspaceManager
        logger.info("✅ CodesmithWorkspaceManager imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import: {e}")
        return False
    
    # Test with temporary workspace
    with tempfile.TemporaryDirectory(prefix="test_codesmith_integration_") as tmpdir:
        try:
            # Create manager
            manager = CodesmithWorkspaceManager(tmpdir)
            logger.info(f"✅ Manager created for {tmpdir}")
            
            # Create isolated generation
            gen_id = await manager.create_isolated_generation()
            logger.info(f"✅ Generation created: {gen_id}")
            
            # Get path
            gen_path = await manager.get_generation_path()
            logger.info(f"✅ Generation path: {gen_path}")
            
            # Verify directory exists
            gen_dir = Path(gen_path)
            if not gen_dir.exists():
                logger.error(f"❌ Generation directory doesn't exist: {gen_path}")
                return False
            
            logger.info(f"✅ Generation directory exists and is accessible")
            
            # Get info
            info = await manager.get_generation_info()
            logger.info(f"✅ Generation info: {json.dumps(info, indent=2)}")
            
            # List generations
            gens = await manager.list_generations()
            logger.info(f"✅ Listed {len(gens)} generation(s)")
            
            if gen_id not in gens:
                logger.error(f"❌ Generation ID {gen_id} not in list")
                return False
            
            logger.info(f"✅ Generation ID properly listed")
            
            logger.info("\n🎉 ALL INTEGRATION TESTS PASSED!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Integration test failed: {e}", exc_info=True)
            return False


async def test_imports_in_server():
    """Test that all necessary imports work in the server file"""
    logger.info("\n" + "="*80)
    logger.info("TEST: Required Imports in codesmith_agent_server.py")
    logger.info("="*80)
    
    try:
        import codesmith_agent_server
        logger.info("✅ codesmith_agent_server.py imports successfully")
        
        # Check for necessary components
        required = ['CodesmithWorkspaceManager', 'CodesmithAgentMCPServer']
        for req in required:
            if hasattr(codesmith_agent_server, req):
                logger.info(f"✅ {req} found in module")
            else:
                logger.error(f"❌ {req} NOT found in module")
                return False
        
        logger.info("\n✅ All required components present")
        return True
        
    except Exception as e:
        logger.error(f"❌ Import test failed: {e}", exc_info=True)
        return False


async def main():
    logger.info("\n" + "#"*80)
    logger.info("# 🧪 CODESMITH WORKSPACE ISOLATION - INTEGRATION TESTS")
    logger.info("#"*80)
    
    tests = [
        test_imports_in_server,
        test_workspace_manager_integration,
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            logger.error(f"\n❌ Test failed: {e}", exc_info=True)
            results.append(False)
    
    # Summary
    logger.info("\n" + "#"*80)
    logger.info("# 📊 INTEGRATION TEST SUMMARY")
    logger.info("#"*80)
    passed = sum(1 for r in results if r)
    total = len(results)
    logger.info(f"\n✅ Passed: {passed}/{total}")
    
    if passed == total:
        logger.info("\n🎉 INTEGRATION TESTS PASSED - Ready for E2E testing!")
    else:
        logger.error(f"\n❌ FAILURES: {total - passed} tests failed")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
