#!/usr/bin/env python3
"""
E2E Test 1 with Credit Monitoring

Tests the complete workflow with credit tracking visible.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


async def run_test():
    """Run E2E Test 1 with monitoring."""
    import aiohttp

    workspace_path = "/Users/dominikfoert/TestApps/e2e_test_1_new_app"
    ws_url = "ws://localhost:8002/ws/chat"

    logger.info("="*80)
    logger.info("🧪 E2E TEST 1: Create Temperature Converter App")
    logger.info("   WITH CREDIT MONITORING & SAFETY FEATURES")
    logger.info("="*80)
    logger.info(f"Workspace: {workspace_path}")

    events_received = 0
    credit_updates = []
    agents_executed = []
    errors = []

    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url, timeout=aiohttp.ClientTimeout(total=600)) as ws:
                logger.info("✅ Connected to WebSocket")

                # Send initialization
                init_msg = {
                    "type": "init",
                    "workspace_path": workspace_path
                }
                await ws.send_json(init_msg)
                logger.info("📤 Sent init message")

                # Send task
                task_msg = {
                    "type": "chat",
                    "query": """Create a Python CLI tool that converts temperatures between Celsius, Fahrenheit, and Kelvin.
Requirements:
1. Support bidirectional conversion
2. Accept input via command line arguments
3. Display results with 2 decimal places
4. Include help text
5. Add comprehensive tests"""
                }
                await ws.send_json(task_msg)
                logger.info("📤 Sent task message")
                logger.info("")

                # Process events with timeout
                start_time = asyncio.get_event_loop().time()
                timeout_seconds = 300  # 5 minutes max

                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        event = json.loads(msg.data)
                        events_received += 1
                        event_type = event.get("type", "unknown")

                        # Track credit updates
                        if event_type == "credit_update":
                            usage = event.get("usage", {})
                            credit_updates.append(usage)

                            logger.info(f"\n💰 CREDIT UPDATE #{len(credit_updates)}:")
                            logger.info(f"   Session cost: ${usage.get('session_cost', 0):.2f}")
                            logger.info(f"   Total cost: ${usage.get('total_cost', 0):.2f}")
                            logger.info(f"   Claude locked: {usage.get('claude_locked', False)}")

                            # Check for warnings
                            if usage.get('emergency_shutdown'):
                                logger.critical("🚨 EMERGENCY SHUTDOWN TRIGGERED!")
                                break

                        # Track supervisor decisions
                        elif event_type == "supervisor_event":
                            message = event.get("message", "")
                            if "routing to:" in message.lower():
                                agent = message.split("routing to:")[-1].strip()
                                agents_executed.append(agent)
                                logger.info(f"\n🎯 ROUTING: {agent}")

                        # Track progress
                        elif event_type == "mcp_progress":
                            server = event.get("server", "")
                            message = event.get("message", "")
                            progress = event.get("progress", 0)

                            # Only log important progress
                            if "Claude" in message or "Error" in message or progress >= 1.0:
                                logger.info(f"   📊 {server}: {message} [{int(progress*100)}%]")

                        # Track errors
                        elif event_type == "error":
                            error = event.get("error", "")
                            errors.append(error)
                            logger.error(f"\n❌ ERROR: {error}")

                        # Track completion
                        elif event_type == "response":
                            response = event.get("response", "")
                            logger.info(f"\n✅ RESPONSE RECEIVED")
                            logger.info(f"   Length: {len(response)} chars")

                        elif event_type == "workflow_complete":
                            logger.info(f"\n✅ WORKFLOW COMPLETE")
                            break

                    # Check timeout
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > timeout_seconds:
                        logger.error(f"\n⏰ TIMEOUT after {timeout_seconds}s")
                        break

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        errors.append(str(e))

    # Summary
    logger.info("\n" + "="*80)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*80)
    logger.info(f"Events received: {events_received}")
    logger.info(f"Credit updates: {len(credit_updates)}")
    logger.info(f"Agents executed: {agents_executed}")
    logger.info(f"Errors: {len(errors)}")

    if credit_updates:
        final_credit = credit_updates[-1]
        logger.info(f"\n💰 FINAL CREDIT USAGE:")
        logger.info(f"   Session cost: ${final_credit.get('session_cost', 0):.2f}")
        logger.info(f"   Total cost: ${final_credit.get('total_cost', 0):.2f}")

        agents_usage = final_credit.get('agents', {})
        if agents_usage:
            logger.info(f"\n   Per-agent breakdown:")
            for agent, data in agents_usage.items():
                logger.info(f"      {agent}: {data.get('calls', 0)} calls, ${data.get('cost', 0):.2f}")

    # Check workspace
    workspace = Path(workspace_path)
    if workspace.exists():
        files = list(workspace.rglob("*.py"))
        logger.info(f"\n📁 Files created: {len(files)} Python files")
        for f in files[:5]:  # Show first 5
            logger.info(f"   - {f.name}")

    success = len(errors) == 0 and len(files) > 0
    logger.info(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")

    return success


if __name__ == "__main__":
    logger.info("🚀 Starting E2E Test with Credit Monitoring...")
    asyncio.run(run_test())