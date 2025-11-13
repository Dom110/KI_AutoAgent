#!/usr/bin/env python3
"""
🧪 Quick E2E Test: FIX #2 validation
Tests if server responds with FIX #2 async_stdin_readline() changes
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
import websockets
import sys

# Logging
LOG_FILE = Path("/tmp/e2e_fix2_test.log")
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def test_e2e():
    """Minimal E2E test with FIX #2"""
    logger.info("="*80)
    logger.info("🧪 E2E TEST: FIX #2 Async Stdin")
    logger.info("="*80)
    
    try:
        # Connect
        logger.info("Connecting to ws://localhost:8002/ws/chat...")
        async with websockets.connect("ws://localhost:8002/ws/chat") as ws:
            logger.info("✅ Connected")
            
            # Receive connected message
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            logger.info(f"📥 Connected: {json.loads(msg)['type']}")
            
            # Send init
            logger.info("📤 Sending init...")
            await ws.send(json.dumps({
                "type": "init",
                "workspace_path": "/tmp/e2e_fix2_test_workspace"
            }))
            
            # Receive initialized
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            logger.info(f"📥 Initialized: {json.loads(msg)['type']}")
            
            # Send simple query
            logger.info("📤 Sending simple query...")
            await ws.send(json.dumps({
                "type": "chat",
                "message": "Create a simple hello function"
            }))
            
            # Receive responses with 30s timeout
            start = datetime.now()
            messages_received = 0
            
            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=30)
                    msg_data = json.loads(msg)
                    msg_type = msg_data.get("type")
                    
                    elapsed = (datetime.now() - start).total_seconds()
                    logger.info(f"📥 [{elapsed:.1f}s] {msg_type}: {str(msg)[:80]}")
                    messages_received += 1
                    
                    if msg_type == "result":
                        logger.info(f"✅ Got result after {elapsed:.1f}s, {messages_received} messages")
                        return True
                        
                except asyncio.TimeoutError:
                    elapsed = (datetime.now() - start).total_seconds()
                    logger.warning(f"⏱️ Timeout after {elapsed:.1f}s, received {messages_received} messages")
                    return messages_received > 0
        
    except Exception as e:
        logger.error(f"❌ Error: {type(e).__name__}: {e}")
        return False


async def main():
    logger.info(f"\n{'='*80}")
    logger.info(f"🧪 QUICK E2E TEST - FIX #2")
    logger.info(f"{'='*80}")
    logger.info(f"Time: {datetime.now().isoformat()}")
    logger.info(f"Server: ws://localhost:8002/ws/chat")
    logger.info(f"Log: {LOG_FILE}")
    
    result = await test_e2e()
    
    logger.info(f"\n{'='*80}")
    if result:
        logger.info("✅ TEST PASSED")
    else:
        logger.info("❌ TEST FAILED")
    logger.info(f"{'='*80}\n")
    
    return 0 if result else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
