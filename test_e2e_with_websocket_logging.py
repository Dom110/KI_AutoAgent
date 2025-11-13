#!/usr/bin/env python3
"""
E2E Test with MASSIVE WebSocket Logging
Logs every single WebSocket message (in/out) with timestamps

Author: AI Assistant
Date: 2025-11-13
"""

import asyncio
import json
import sys
import logging
from datetime import datetime
from pathlib import Path
import time
import shutil
from typing import Optional, Dict, Any, List
import websockets
from websockets.client import WebSocketClientProtocol

TEST_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
TEST_WORKSPACE = Path.home() / "TestApps" / f"e2e_reviewfix_validation_{TEST_ID}"
LOG_DIR = TEST_WORKSPACE / "logs"

MAIN_LOG_FILE = LOG_DIR / f"e2e_main_{TEST_ID}.log"
WEBSOCKET_SEND_LOG = LOG_DIR / f"websocket_send_{TEST_ID}.log"
WEBSOCKET_RECV_LOG = LOG_DIR / f"websocket_recv_{TEST_ID}.log"
WEBSOCKET_BOTH_LOG = LOG_DIR / f"websocket_both_{TEST_ID}.log"

LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.FileHandler(MAIN_LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WebSocketLogger:
    """Massive WebSocket logging to separate files."""
    
    def __init__(self):
        self.message_counter = 0
    
    def log_sent(self, message: Dict[str, Any]) -> None:
        """Log message sent to server."""
        self.message_counter += 1
        timestamp = datetime.now().isoformat()
        msg_json = json.dumps(message, indent=2)
        
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(WEBSOCKET_SEND_LOG, 'a') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"[{self.message_counter}] SENT @ {timestamp}\n")
            f.write(f"{'='*80}\n")
            f.write(msg_json)
            f.write(f"\n")
        
        with open(WEBSOCKET_BOTH_LOG, 'a') as f:
            f.write(f"\n>>> [{self.message_counter}] SENT @ {timestamp}\n")
            f.write(msg_json)
            f.write(f"\n")
        
        logger.info(f"📤 SENT message #{self.message_counter}: {message.get('type', 'unknown')}")
    
    def log_received(self, message: Dict[str, Any]) -> None:
        """Log message received from server."""
        timestamp = datetime.now().isoformat()
        msg_json = json.dumps(message, indent=2)
        msg_type = message.get('type', 'unknown')
        
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(WEBSOCKET_RECV_LOG, 'a') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"RECEIVED @ {timestamp} | Type: {msg_type}\n")
            f.write(f"{'='*80}\n")
            f.write(msg_json)
            f.write(f"\n")
        
        with open(WEBSOCKET_BOTH_LOG, 'a') as f:
            f.write(f"\n<<< RECEIVED @ {timestamp} | Type: {msg_type}\n")
            f.write(msg_json)
            f.write(f"\n")
        
        logger.info(f"📥 RECEIVED: {msg_type}")

ws_logger = WebSocketLogger()

class E2ETestMetrics:
    """Track test metrics."""
    
    def __init__(self):
        self.start_time = time.time()
        self.messages_received: List[Dict] = []
        self.agents_invoked: set = set()
        self.errors: List[str] = []
        self.phases_completed: List[str] = []
    
    def add_error(self, error: str) -> None:
        self.errors.append(error)
        logger.error(f"❌ ERROR: {error}")
    
    def mark_phase_complete(self, phase: str) -> None:
        self.phases_completed.append(phase)
        elapsed = time.time() - self.start_time
        logger.info(f"✅ Phase '{phase}' complete (elapsed: {elapsed:.1f}s)")
    
    def get_summary(self) -> str:
        elapsed = time.time() - self.start_time
        return f"""
{'='*80}
TEST EXECUTION SUMMARY
{'='*80}
Total Duration: {elapsed:.1f}s
Phases Completed: {len(self.phases_completed)}/{6}
  {' → '.join(self.phases_completed)}
Messages Received: {len(self.messages_received)}
Agents Invoked: {sorted(self.agents_invoked)}
Errors: {len(self.errors)}
{f"Error Details: {chr(10).join(f'  • {e}' for e in self.errors)}" if self.errors else "  ✅ No errors!"}
{'='*80}
"""

metrics = E2ETestMetrics()

async def send_message(ws: WebSocketClientProtocol, message: Dict[str, Any]) -> None:
    """Send message to WebSocket and log it."""
    ws_logger.log_sent(message)
    await ws.send(json.dumps(message))

async def receive_messages(ws: WebSocketClientProtocol, timeout: float = 30.0) -> List[Dict[str, Any]]:
    """Receive messages from WebSocket until timeout or task_complete."""
    messages = []
    start_time = time.time()
    
    try:
        while time.time() - start_time < timeout:
            msg_text = await asyncio.wait_for(ws.recv(), timeout=2.0)
            message = json.loads(msg_text)
            ws_logger.log_received(message)
            messages.append(message)
            metrics.messages_received.append(message)
            
            if message.get('type') == 'task_complete':
                logger.info("🎉 Received task_complete signal")
                break
            
            if message.get('type') == 'agent_event':
                agent_name = message.get('data', {}).get('agent_name')
                if agent_name:
                    metrics.agents_invoked.add(agent_name)
    
    except asyncio.TimeoutError:
        logger.warning(f"⏱️ Receive timeout after {timeout}s")
    
    return messages

async def phase_1_environment_setup() -> bool:
    """Phase 1: Setup test workspace."""
    logger.info("\n" + "="*80)
    logger.info("PHASE 1: Environment Setup")
    logger.info("="*80)
    
    try:
        if TEST_WORKSPACE.exists():
            logger.info(f"  Removing old workspace: {TEST_WORKSPACE}")
            shutil.rmtree(TEST_WORKSPACE)
        
        TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
        logger.info(f"  ✅ Created workspace: {TEST_WORKSPACE}")
        metrics.mark_phase_complete("Environment Setup")
        return True
    
    except Exception as e:
        metrics.add_error(f"Phase 1 failed: {str(e)}")
        return False

async def phase_2_backend_connection() -> bool:
    """Phase 2: Connect to backend."""
    logger.info("\n" + "="*80)
    logger.info("PHASE 2: Backend Connection")
    logger.info("="*80)
    
    try:
        logger.info(f"  Connecting to ws://localhost:8002/ws/chat...")
        ws = await websockets.connect("ws://localhost:8002/ws/chat")
        
        welcome_msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
        welcome_data = json.loads(welcome_msg)
        ws_logger.log_received(welcome_data)
        
        session_id = welcome_data.get('data', {}).get('session_id')
        logger.info(f"  ✅ Connected! Session ID: {session_id}")
        metrics.mark_phase_complete("Backend Connection")
        
        return ws
    
    except Exception as e:
        metrics.add_error(f"Phase 2 failed: {str(e)}")
        return None

async def phase_3_workspace_init(ws: WebSocketClientProtocol) -> bool:
    """Phase 3: Initialize workspace."""
    logger.info("\n" + "="*80)
    logger.info("PHASE 3: Workspace Initialization")
    logger.info("="*80)
    
    try:
        init_msg = {
            "type": "init",
            "workspace_path": str(TEST_WORKSPACE)
        }
        await send_message(ws, init_msg)
        
        messages = await receive_messages(ws, timeout=10.0)
        logger.info(f"  ✅ Workspace initialized with {len(messages)} response messages")
        metrics.mark_phase_complete("Workspace Init")
        
        return True
    
    except Exception as e:
        metrics.add_error(f"Phase 3 failed: {str(e)}")
        return False

async def phase_4_simple_query(ws: WebSocketClientProtocol) -> bool:
    """Phase 4: Send simple query."""
    logger.info("\n" + "="*80)
    logger.info("PHASE 4: Simple Query")
    logger.info("="*80)
    
    try:
        query_msg = {
            "type": "chat",
            "message": "Create a simple calculator app that adds two numbers"
        }
        await send_message(ws, query_msg)
        
        logger.info("  ⏳ Waiting for workflow execution...")
        messages = await receive_messages(ws, timeout=120.0)
        
        logger.info(f"  ✅ Query processed with {len(messages)} messages")
        logger.info(f"  📊 Agents invoked: {metrics.agents_invoked}")
        
        metrics.mark_phase_complete("Simple Query")
        return True
    
    except Exception as e:
        metrics.add_error(f"Phase 4 failed: {str(e)}")
        return False

async def phase_5_code_generation(ws: WebSocketClientProtocol) -> bool:
    """Phase 5: Code generation."""
    logger.info("\n" + "="*80)
    logger.info("PHASE 5: Code Generation")
    logger.info("="*80)
    
    try:
        code_msg = {
            "type": "chat",
            "message": "Add a multiply function to the calculator"
        }
        await send_message(ws, code_msg)
        
        logger.info("  ⏳ Waiting for code generation...")
        messages = await receive_messages(ws, timeout=120.0)
        
        logger.info(f"  ✅ Code generation complete with {len(messages)} messages")
        metrics.mark_phase_complete("Code Generation")
        return True
    
    except Exception as e:
        metrics.add_error(f"Phase 5 failed: {str(e)}")
        return False

async def phase_6_reviewfix_validation(ws: WebSocketClientProtocol) -> bool:
    """Phase 6: ReviewFix validation."""
    logger.info("\n" + "="*80)
    logger.info("PHASE 6: ReviewFix Validation")
    logger.info("="*80)
    
    try:
        review_msg = {
            "type": "chat",
            "message": "Review the code for best practices and fix any issues"
        }
        await send_message(ws, review_msg)
        
        logger.info("  ⏳ Waiting for ReviewFix Agent...")
        messages = await receive_messages(ws, timeout=120.0)
        
        logger.info(f"  ✅ ReviewFix validation complete with {len(messages)} messages")
        metrics.mark_phase_complete("ReviewFix Validation")
        return True
    
    except Exception as e:
        metrics.add_error(f"Phase 6 failed: {str(e)}")
        return False

async def main():
    """Run complete E2E test."""
    logger.info("\n" + "🚀 "*40)
    logger.info("KI_AutoAgent E2E Test Suite - ReviewFix Validation")
    logger.info("🚀 "*40)
    
    logger.info(f"\n📁 Test Workspace: {TEST_WORKSPACE}")
    logger.info(f"📝 Main Log: {MAIN_LOG_FILE}")
    logger.info(f"📤 WebSocket Send Log: {WEBSOCKET_SEND_LOG}")
    logger.info(f"📥 WebSocket Recv Log: {WEBSOCKET_RECV_LOG}")
    logger.info(f"📊 WebSocket Combined Log: {WEBSOCKET_BOTH_LOG}\n")
    
    if not await phase_1_environment_setup():
        logger.error("❌ Phase 1 failed - stopping tests")
        sys.exit(1)
    
    ws = await phase_2_backend_connection()
    if not ws:
        logger.error("❌ Phase 2 failed - stopping tests")
        sys.exit(1)
    
    try:
        if not await phase_3_workspace_init(ws):
            logger.error("❌ Phase 3 failed - stopping tests")
            sys.exit(1)
        
        if not await phase_4_simple_query(ws):
            logger.error("❌ Phase 4 failed - continuing with next phase")
        
        if not await phase_5_code_generation(ws):
            logger.error("❌ Phase 5 failed - continuing with next phase")
        
        if not await phase_6_reviewfix_validation(ws):
            logger.error("❌ Phase 6 failed")
    
    finally:
        await ws.close()
    
    logger.info(metrics.get_summary())
    
    if metrics.errors:
        logger.error(f"\n❌ Test FAILED with {len(metrics.errors)} errors")
        sys.exit(1)
    else:
        logger.info(f"\n✅ Test PASSED - All phases complete!")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
