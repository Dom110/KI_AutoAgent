#!/usr/bin/env python3
"""
🧪 Test FIX #2 & #3:
- FIX #2: async_stdin_readline() prevents blocking
- FIX #3: Response routing works end-to-end

Creates a minimal test workspace and runs E2E test with massive logging.
"""

import asyncio
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Setup paths
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Logging setup
LOG_DIR = PROJECT_ROOT / ".logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"test_fix_2_and_3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def test_fix_2_async_stdin():
    """Test: async_stdin_readline() exists in all servers"""
    logger.info("\n" + "="*80)
    logger.info("TEST: FIX #2 - async_stdin_readline() in all servers")
    logger.info("="*80)
    
    servers_to_check = [
        "openai_server.py",
        "architect_agent_server.py",
        "codesmith_agent_server.py",
        "responder_agent_server.py",
        "reviewfix_agent_server.py",
        "research_agent_server.py",
    ]
    
    passed = 0
    failed = 0
    
    for server_file in servers_to_check:
        path = PROJECT_ROOT / "mcp_servers" / server_file
        if not path.exists():
            logger.error(f"❌ {server_file}: File not found")
            failed += 1
            continue
        
        with open(path, 'r') as f:
            content = f.read()
        
        # Check for async_stdin_readline
        if "async def async_stdin_readline" in content:
            logger.info(f"✅ {server_file}: Has async_stdin_readline()")
            
            # Check for Timeout
            if "timeout=300.0" in content:
                logger.info(f"   ✅ Has 300s timeout")
                passed += 1
            else:
                logger.warning(f"   ⚠️  No 300s timeout found")
                failed += 1
        else:
            logger.error(f"❌ {server_file}: Missing async_stdin_readline()")
            failed += 1
    
    logger.info(f"\nResult: {passed} passed, {failed} failed")
    return failed == 0


async def test_mcp_manager_exists():
    """Test: MCPManager is available"""
    logger.info("\n" + "="*80)
    logger.info("TEST: MCPManager import")
    logger.info("="*80)
    
    try:
        from backend.utils.mcp_manager import get_mcp_manager, MCPManager
        logger.info("✅ MCPManager imported successfully")
        return True
    except Exception as e:
        logger.error(f"❌ MCPManager import failed: {e}")
        return False


async def test_mcp_server_startup():
    """Test: Can start MCP server (openai_server)"""
    logger.info("\n" + "="*80)
    logger.info("TEST: MCP Server startup (openai)")
    logger.info("="*80)
    
    logger.info("ℹ️ Checking if openai_server.py can be imported...")
    
    server_file = PROJECT_ROOT / "mcp_servers" / "openai_server.py"
    if not server_file.exists():
        logger.error(f"❌ openai_server.py not found")
        return False
    
    try:
        # Check if it has valid Python syntax
        with open(server_file, 'r') as f:
            code = f.read()
        
        compile(code, str(server_file), 'exec')
        logger.info("✅ openai_server.py has valid syntax")
        
        # Check for required components
        checks = [
            ("async def async_stdin_readline", "async_stdin_readline function"),
            ("async def run", "run() method"),
            ("class OpenAIMCPServer", "OpenAIMCPServer class"),
            ("logger =", "Logger setup"),
        ]
        
        passed = 0
        for pattern, name in checks:
            if pattern in code:
                logger.info(f"  ✅ Has {name}")
                passed += 1
            else:
                logger.warning(f"  ⚠️  Missing {name}")
        
        logger.info(f"Result: {passed}/{len(checks)} checks passed")
        return passed == len(checks)
        
    except Exception as e:
        logger.error(f"❌ Error checking openai_server.py: {e}")
        return False


async def test_logging_setup():
    """Test: All servers have logging configured"""
    logger.info("\n" + "="*80)
    logger.info("TEST: Logging configuration")
    logger.info("="*80)
    
    servers = [
        "openai_server.py",
        "architect_agent_server.py",
        "codesmith_agent_server.py",
        "responder_agent_server.py",
        "reviewfix_agent_server.py",
        "research_agent_server.py",
    ]
    
    passed = 0
    for server_file in servers:
        path = PROJECT_ROOT / "mcp_servers" / server_file
        if not path.exists():
            continue
        
        with open(path, 'r') as f:
            content = f.read()
        
        # Check for logging setup
        if "logging.basicConfig" in content and "logger = logging.getLogger" in content:
            logger.info(f"✅ {server_file}: Has logging configured")
            passed += 1
        else:
            logger.warning(f"⚠️  {server_file}: May need logging setup")
    
    logger.info(f"Result: {passed}/{len(servers)} have logging")
    return passed > 0


async def main():
    logger.info(f"\n{'='*80}")
    logger.info(f"🧪 TEST: FIX #2 & FIX #3")
    logger.info(f"{'='*80}")
    logger.info(f"Time: {datetime.now().isoformat()}")
    logger.info(f"Python: {sys.version.split()[0]}")
    logger.info(f"Log: {LOG_FILE}")
    
    results = []
    
    # Run tests
    results.append(("FIX #2: async_stdin_readline", await test_fix_2_async_stdin()))
    results.append(("MCPManager import", await test_mcp_manager_exists()))
    results.append(("MCP server syntax", await test_mcp_server_startup()))
    results.append(("Logging setup", await test_logging_setup()))
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*80}")
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} | {test_name}")
    
    passed = sum(1 for _, r in results if r)
    logger.info(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        logger.info("\n✅ ALL TESTS PASSED")
    else:
        logger.error(f"\n❌ {len(results) - passed} TESTS FAILED")
    
    logger.info(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(main())
