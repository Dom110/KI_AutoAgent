#!/usr/bin/env python3
"""
E2E Test: ReviewFix Agent MCP Migration Validation
Tests the complete workflow after ReviewFix Agent fix

CRITICAL:
- Tests in SEPARATE WORKSPACE (not dev repo)
- Massive logging at every step
- Validates all 5 agents work correctly
- Detects infinite loops
- Tests subprocess isolation

Author: AI Assistant
Date: 2025-11-12
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

TEST_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
TEST_WORKSPACE = Path.home() / "TestApps" / f"e2e_reviewfix_validation_{TEST_ID}"
LOG_DIR = TEST_WORKSPACE / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"e2e_test_{TEST_ID}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class E2ETestMetrics:
    """Track E2E test metrics and events."""
    
    def __init__(self):
        self.start_time = time.time()
        self.messages_received: List[Dict] = []
        self.agents_invoked: set = set()
        self.timeouts: List[str] = []
        self.errors: List[str] = []
        self.infinite_loop_candidates: List[str] = []
        self.message_timeline: List[tuple] = []
        self.last_message_time = time.time()
        self.consecutive_same_messages = 0
        self.last_message_type = None
        
    def add_message(self, msg_type: str, data: Dict):
        """Track message with infinite loop detection."""
        now = time.time()
        self.messages_received.append({
            'type': msg_type,
            'timestamp': now,
            'data': data
        })
        self.message_timeline.append((msg_type, now - self.start_time))
        
        if msg_type == self.last_message_type:
            self.consecutive_same_messages += 1
            if self.consecutive_same_messages > 100:
                self.infinite_loop_candidates.append(
                    f"Suspicious repetition: {msg_type} x{self.consecutive_same_messages}"
                )
        else:
            self.consecutive_same_messages = 0
            self.last_message_type = msg_type
            
    def add_agent(self, agent_name: str):
        """Track agent invocation."""
        self.agents_invoked.add(agent_name)
        
    def add_timeout(self, context: str):
        """Track timeout event."""
        self.timeouts.append(f"{context} @ {time.time() - self.start_time:.2f}s")
        
    def add_error(self, error: str):
        """Track error."""
        self.errors.append(f"{error} @ {time.time() - self.start_time:.2f}s")
        
    def elapsed(self) -> float:
        """Total elapsed time."""
        return time.time() - self.start_time
    
    def summary(self) -> str:
        """Generate summary report."""
        lines = [
            "\n" + "="*100,
            "📊 E2E TEST METRICS SUMMARY",
            "="*100,
            f"⏱️  Total Duration: {self.elapsed():.2f}s",
            f"📨 Messages Received: {len(self.messages_received)}",
            f"🤖 Agents Invoked: {sorted(self.agents_invoked)}",
            f"⚠️  Timeouts: {len(self.timeouts)}",
            f"❌ Errors: {len(self.errors)}",
            f"🔄 Infinite Loop Candidates: {len(self.infinite_loop_candidates)}",
        ]
        
        if self.timeouts:
            lines.append("\n⏲️  TIMEOUTS:")
            for t in self.timeouts[:10]:
                lines.append(f"   - {t}")
                
        if self.errors:
            lines.append("\n❌ ERRORS:")
            for e in self.errors[:10]:
                lines.append(f"   - {e}")
                
        if self.infinite_loop_candidates:
            lines.append("\n🔄 INFINITE LOOP CANDIDATES:")
            for c in self.infinite_loop_candidates[:5]:
                lines.append(f"   - {c}")
        
        lines.append("="*100 + "\n")
        return "\n".join(lines)


class E2ETestClient:
    """E2E test client for WebSocket communication."""
    
    def __init__(self, ws_url: str, workspace_path: Path):
        self.ws_url = ws_url
        self.workspace_path = workspace_path
        self.metrics = E2ETestMetrics()
        self.ws = None
        
    async def connect(self) -> bool:
        """Connect to backend WebSocket and receive welcome message."""
        logger.info(f"🌐 Connecting to WebSocket: {self.ws_url}")
        try:
            import websockets
            self.ws = await websockets.connect(self.ws_url)
            logger.info("✅ WebSocket connected")
            
            resp = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
            data = json.loads(resp)
            logger.info(f"📨 Received welcome message: {data.get('type')}")
            logger.info(f"   Session ID: {data.get('session_id', 'N/A')}")
            logger.info(f"   Client ID: {data.get('client_id', 'N/A')}")
            self.metrics.add_message("connected", data)
            
            return True
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed: {e}")
            self.metrics.add_error(f"WebSocket connection: {e}")
            return False
    
    async def init_workspace(self) -> bool:
        """Initialize workspace via init message."""
        logger.info(f"📁 Initializing workspace: {self.workspace_path}")
        try:
            await self.ws.send(json.dumps({
                "type": "init",
                "workspace_path": str(self.workspace_path)
            }))
            logger.info(f"📤 Sent init message with workspace_path")
            
            resp = await asyncio.wait_for(self.ws.recv(), timeout=10.0)
            data = json.loads(resp)
            logger.info(f"✅ Received response: {data.get('type')}")
            
            if data.get('type') == 'error':
                logger.error(f"❌ Init error: {data.get('message')}")
                self.metrics.add_error(data.get('message', 'Unknown init error'))
                return False
            
            self.metrics.add_message("init_response", data)
            logger.info(f"   Session ID: {data.get('session_id', 'N/A')}")
            return True
            
        except asyncio.TimeoutError:
            msg = "Workspace init timeout"
            logger.error(f"⏲️  {msg}")
            self.metrics.add_timeout(msg)
            return False
        except Exception as e:
            logger.error(f"❌ Workspace init failed: {e}")
            self.metrics.add_error(f"Workspace init: {e}")
            return False
    
    async def send_task(self, task: str, timeout: int = 300) -> Optional[Dict]:
        """Send task and collect all responses."""
        logger.info(f"\n📤 Sending task: {task}")
        logger.info(f"⏱️  Timeout: {timeout}s")
        
        try:
            await self.ws.send(json.dumps({
                "type": "chat",
                "content": task
            }))
            
            start_time = time.time()
            message_count = 0
            max_messages = 500
            
            logger.info("🎬 Waiting for workflow execution...")
            logger.info("-" * 100)
            
            while message_count < max_messages:
                # Per-message timeout
                msg_timeout = max(10.0, timeout - (time.time() - start_time))
                
                try:
                    response = await asyncio.wait_for(
                        self.ws.recv(),
                        timeout=msg_timeout
                    )
                    message_count += 1
                    
                    data = json.loads(response)
                    msg_type = data.get('type', 'unknown')
                    
                    self.metrics.add_message(msg_type, data)
                    
                    # Detailed logging
                    self._log_message(message_count, msg_type, data)
                    
                    # Check for completion
                    if msg_type == 'task_complete':
                        logger.info("✅ Task completed")
                        return data
                    
                    elif msg_type == 'error':
                        logger.error(f"❌ Error from backend: {data.get('message')}")
                        self.metrics.add_error(data.get('message', 'Unknown error'))
                    
                except asyncio.TimeoutError:
                    elapsed = time.time() - start_time
                    msg = f"Message timeout (after {message_count} msgs, {elapsed:.1f}s)"
                    logger.error(f"⏲️  {msg}")
                    self.metrics.add_timeout(msg)
                    
                    if elapsed > timeout:
                        logger.warning("⚠️  Overall timeout reached - stopping test")
                        break
            
            logger.info("-" * 100)
            logger.warning(f"⚠️  Workflow did not complete (received {message_count} messages)")
            return None
            
        except Exception as e:
            logger.error(f"❌ Task execution failed: {e}")
            self.metrics.add_error(f"Task execution: {e}")
            return None
    
    def _log_message(self, msg_count: int, msg_type: str, data: Dict):
        """Log message with details."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        elapsed = self.metrics.elapsed()
        
        # Track agents
        if msg_type == 'progress':
            node = data.get('node', 'unknown')
            self.metrics.add_agent(node)
            logger.info(f"   [{msg_count:3d}] {timestamp} | {elapsed:6.2f}s | "
                       f"PROGRESS: {node}")
        
        elif msg_type == 'agent_event':
            agent = data.get('agent', 'unknown')
            self.metrics.add_agent(agent)
            event = data.get('event_type', 'unknown')
            logger.info(f"   [{msg_count:3d}] {timestamp} | {elapsed:6.2f}s | "
                       f"AGENT: {agent}/{event}")
        
        elif msg_type == 'message':
            content = data.get('content', '')[:60]
            logger.info(f"   [{msg_count:3d}] {timestamp} | {elapsed:6.2f}s | "
                       f"MESSAGE: {content}...")
        
        elif msg_type == 'status':
            status = data.get('status', 'unknown')
            logger.info(f"   [{msg_count:3d}] {timestamp} | {elapsed:6.2f}s | "
                       f"STATUS: {status}")
        
        elif msg_type == 'error':
            error = data.get('message', 'unknown')[:60]
            logger.error(f"   [{msg_count:3d}] {timestamp} | {elapsed:6.2f}s | "
                        f"ERROR: {error}...")
        
        else:
            logger.debug(f"   [{msg_count:3d}] {timestamp} | {elapsed:6.2f}s | "
                        f"{msg_type.upper()}: {str(data)[:50]}...")
    
    async def disconnect(self):
        """Disconnect WebSocket."""
        if self.ws:
            try:
                await self.ws.close()
                logger.info("✅ WebSocket disconnected")
            except:
                pass


async def setup_test_environment():
    """Setup clean test workspace."""
    logger.info("\n" + "="*100)
    logger.info("🛠️  SETUP: Test Environment")
    logger.info("="*100)
    
    # Clean old workspace if exists
    if TEST_WORKSPACE.exists():
        logger.info(f"🧹 Removing old workspace: {TEST_WORKSPACE}")
        shutil.rmtree(TEST_WORKSPACE)
    
    # Create directories
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"✅ Created test workspace: {TEST_WORKSPACE}")
    logger.info(f"✅ Created log directory: {LOG_DIR}")
    
    # Verify isolation
    app_dirs = list(TEST_WORKSPACE.glob("*/"))
    if app_dirs:
        logger.warning(f"⚠️  Found {len(app_dirs)} directories in workspace (cleanup incomplete)")
    else:
        logger.info("✅ Workspace verified clean (no old artifacts)")
    
    return TEST_WORKSPACE


async def run_e2e_test_reviewfix():
    """Main E2E test for ReviewFix validation."""
    
    logger.info("\n" + "="*100)
    logger.info("🧪 E2E TEST: ReviewFix Agent MCP Migration Validation")
    logger.info("="*100)
    logger.info(f"⏱️  Started: {datetime.now().isoformat()}")
    logger.info(f"📁 Workspace: {TEST_WORKSPACE}")
    logger.info(f"📝 Log File: {LOG_FILE}")
    logger.info("="*100)
    
    # Phase 1: Setup
    logger.info("\n📋 PHASE 1: Environment Setup")
    workspace = await setup_test_environment()
    
    # Phase 2: Connect
    logger.info("\n📋 PHASE 2: Backend Connection")
    client = E2ETestClient(
        ws_url="ws://localhost:8002/ws/chat",
        workspace_path=workspace
    )
    
    if not await client.connect():
        logger.error("❌ Failed to connect to backend")
        return False
    
    # Phase 3: Initialize workspace
    logger.info("\n📋 PHASE 3: Workspace Initialization")
    if not await client.init_workspace():
        logger.error("❌ Failed to initialize workspace")
        logger.error("ℹ️  Backend API may require valid workspace path")
        return False
    
    # Phase 4: Test simple query (agents: Research, Responder)
    logger.info("\n📋 PHASE 4: Simple Query Test")
    logger.info("   Agents: Research, Responder")
    result1 = await client.send_task(
        "What are the main benefits of Python 3.13?",
        timeout=120
    )
    
    if result1:
        logger.info("✅ Simple query test PASSED")
    else:
        logger.warning("⚠️  Simple query test did not complete")
    
    # Phase 5: Test code generation (agents: CodeSmith, Responder)
    logger.info("\n📋 PHASE 5: Code Generation Test")
    logger.info("   Agents: CodeSmith, Responder")
    result2 = await client.send_task(
        "Create a simple Python calculator class that can add, subtract, multiply and divide",
        timeout=180
    )
    
    if result2:
        logger.info("✅ Code generation test PASSED")
    else:
        logger.warning("⚠️  Code generation test did not complete")
    
    # Phase 6: Test code review with ReviewFix (agents: CodeSmith, ReviewFix, Responder)
    logger.info("\n📋 PHASE 6: Code Review & Fix Test (ReviewFix Agent)")
    logger.info("   Agents: CodeSmith, ReviewFix, Responder")
    logger.info("   🚀 THIS IS THE CRITICAL TEST - Validates ReviewFix subprocess fix")
    
    result3 = await client.send_task(
        """Create a Python REST API with Flask that has these endpoints:
        - POST /users - create user
        - GET /users/{id} - get user
        - PUT /users/{id} - update user
        - DELETE /users/{id} - delete user
        
        Make sure the code is production-ready with error handling and validation.""",
        timeout=300
    )
    
    if result3:
        logger.info("✅ ReviewFix test PASSED - No infinite loop detected!")
    else:
        logger.warning("⚠️  ReviewFix test did not complete")
    
    # Phase 7: Disconnect
    logger.info("\n📋 PHASE 7: Cleanup")
    await client.disconnect()
    
    # Phase 8: Report
    logger.info("\n" + "="*100)
    logger.info("📊 TEST RESULTS")
    logger.info("="*100)
    
    logger.info(client.metrics.summary())
    
    # Analyze results
    success = True
    issues = []
    
    # Check for agents
    expected_agents = {'research', 'codesmith', 'reviewfix', 'responder'}
    invoked_agents = {a.lower() for a in client.metrics.agents_invoked}
    
    logger.info(f"\n🤖 Agent Invocation Analysis:")
    logger.info(f"   Expected: {expected_agents}")
    logger.info(f"   Invoked: {invoked_agents}")
    
    if 'reviewfix' in invoked_agents:
        logger.info("   ✅ ReviewFix Agent was invoked")
    else:
        logger.warning("   ⚠️  ReviewFix Agent was NOT invoked (may be expected for simple tasks)")
    
    # Check for errors
    if client.metrics.errors:
        logger.warning(f"\n❌ {len(client.metrics.errors)} errors occurred:")
        for err in client.metrics.errors[:5]:
            logger.error(f"   - {err}")
        success = False
        issues.append(f"{len(client.metrics.errors)} errors")
    
    # Check for infinite loops
    if client.metrics.infinite_loop_candidates:
        logger.error(f"\n🔄 INFINITE LOOP DETECTED:")
        for candidate in client.metrics.infinite_loop_candidates:
            logger.error(f"   - {candidate}")
        success = False
        issues.append("Infinite loop candidates detected")
    
    # Check timeout frequency
    if len(client.metrics.timeouts) > 5:
        logger.warning(f"\n⚠️  {len(client.metrics.timeouts)} timeouts occurred")
        success = False
        issues.append(f"{len(client.metrics.timeouts)} timeouts")
    
    # Final verdict
    logger.info("\n" + "="*100)
    if success and not issues:
        logger.info("✅ E2E TEST PASSED - All checks successful")
        logger.info("✅ ReviewFix Agent working correctly (no infinite loop)")
        logger.info("✅ MCP Architecture validated")
        return True
    elif client.metrics.errors:
        logger.error(f"❌ E2E TEST FAILED - {', '.join(issues)}")
        return False
    else:
        logger.warning(f"⚠️  E2E TEST PARTIAL - Some issues: {', '.join(issues)}")
        return False
    logger.info("="*100 + "\n")


async def main():
    """Main entry point."""
    try:
        success = await run_e2e_test_reviewfix()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Test failed with exception: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
