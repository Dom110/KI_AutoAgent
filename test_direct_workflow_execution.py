#!/usr/bin/env python3
"""
Direct test of workflow execution without WebSocket
"""

import asyncio
import logging
import sys

sys.path.insert(0, '/Users/dominikfoert/git/KI_AutoAgent')

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import workflow directly
from backend.workflow_v7_mcp import execute_supervisor_workflow_streaming_mcp


async def main():
    """Execute workflow directly"""
    logger.info("=" * 70)
    logger.info("DIRECT WORKFLOW TEST")
    logger.info("=" * 70)
    
    try:
        logger.info("🚀 Starting workflow...")
        
        message_count = 0
        async for event in execute_supervisor_workflow_streaming_mcp(
            user_query="Create a new app with a todo list feature",
            workspace_path="/tmp/test_workspace",
            session_id="test_session_123"
        ):
            message_count += 1
            event_type = event.get("type")
            logger.info(f"\n📨 Event #{message_count} [{event_type}]")
            
            if event_type == "workflow_event":
                node = event.get("node")
                logger.info(f"   Node: {node}")
                logger.info(f"   State: {list(event.get('state_update', {}).keys())}")
            
            elif event_type == "agent_event":
                agent = event.get("agent", "unknown")
                status = event.get("status", "")
                logger.info(f"   Agent: {agent}")
                logger.info(f"   Status: {status}")
            
            elif event_type == "error":
                error = event.get("error", "unknown")
                logger.error(f"   ERROR: {error}")
                logger.error(f"   Stack: {event.get('traceback', 'N/A')}")
            
            elif event_type == "workflow_complete":
                logger.info("   ✅ WORKFLOW COMPLETE!")
                result = event.get("result", {})
                logger.info(f"   Result keys: {list(result.keys())}")
            
            # Limit iterations for safety
            if message_count > 100:
                logger.warning("⚠️ Too many events, stopping...")
                break
        
        logger.info("\n" + "=" * 70)
        logger.info(f"Workflow finished after {message_count} events")
    
    except Exception as e:
        logger.error(f"❌ Workflow failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())