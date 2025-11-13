#!/usr/bin/env python3
"""
Simple test to identify where the supervisor hangs
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, '/Users/dominikfoert/git/KI_AutoAgent')

# Load API keys
from dotenv import load_dotenv
env_file = Path.home() / ".ki_autoagent" / "config" / ".env"
if env_file.exists():
    load_dotenv(env_file)
    logger.info(f"✅ Loaded .env from: {env_file}")
else:
    logger.warning(f"⚠️ .env file not found at: {env_file}")

async def test_supervisor_creation():
    """Test if supervisor can be created"""
    logger.info("=" * 80)
    logger.info("TEST: Supervisor Creation")
    logger.info("=" * 80)

    try:
        from backend.core.supervisor_mcp import SupervisorMCP
        
        logger.info("✅ SupervisorMCP imported successfully")
        
        logger.info("Creating supervisor...")
        supervisor = SupervisorMCP(
            workspace_path="/tmp/test_workspace",
            session_id="test_123"
        )
        
        logger.info("✅ Supervisor created successfully")
        logger.info(f"   Workspace: {supervisor.workspace_path}")
        logger.info(f"   Session: {supervisor.session_id}")
        logger.info(f"   LLM Model: {supervisor.llm.model_name}")
        
        return supervisor
        
    except Exception as e:
        logger.error(f"❌ Supervisor creation failed: {e}", exc_info=True)
        raise


async def test_supervisor_decide_next():
    """Test if supervisor can make decisions"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Supervisor decide_next()")
    logger.info("=" * 80)
    
    try:
        supervisor = await test_supervisor_creation()
        
        # Prepare minimal state
        state = {
            "goal": "Create a new app with a todo list feature",
            "user_query": "Create a new app with a todo list feature",
            "workspace_path": "/tmp/test_workspace",
            "session_id": "test_123",
            "messages": [],
            "iteration": 0,
            "last_agent": None,
            "errors": [],
            "error_count": 0
        }
        
        logger.info("\nCalling supervisor.decide_next()...")
        logger.info("⏳ Waiting for decision (timeout: 30s)...")
        
        # Set timeout
        command = await asyncio.wait_for(
            supervisor.decide_next(state),
            timeout=30.0
        )
        
        logger.info("✅ Decision received successfully!")
        logger.info(f"   Route to: {command.goto if hasattr(command, 'goto') else 'END'}")
        if hasattr(command, 'update') and command.update:
            logger.info(f"   Update keys: {list(command.update.keys())}")
        
        return command
        
    except asyncio.TimeoutError:
        logger.error("❌ TIMEOUT: Supervisor.decide_next() took too long (> 30s)")
        logger.error("   This suggests the supervisor is hanging on LLM call or something else")
        raise
    except Exception as e:
        logger.error(f"❌ Supervisor.decide_next() failed: {e}", exc_info=True)
        raise


async def main():
    """Run all tests"""
    logger.info("\n" + "=" * 80)
    logger.info("SUPERVISOR SIMPLE TEST")
    logger.info("=" * 80)
    
    try:
        await test_supervisor_decide_next()
        logger.info("\n✅ ALL TESTS PASSED!")
        
    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())