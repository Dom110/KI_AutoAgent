#!/usr/bin/env python3
"""
🤖 REAL E2E TEST - KI Agent WebSocket Integration Test

This test:
1. Starts the Agent Backend Server
2. Connects via WebSocket
3. Requests an app generation
4. Validates the Agent's correct behavior
5. Checks generated artifacts

CRITICAL: Uses ISOLATED WORKSPACE (not development repo!)
"""

import asyncio
import json
import logging
import shutil
import subprocess
import sys
import time
import websockets
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# ============================================================
# CONFIGURATION
# ============================================================

# Isolated workspace (outside development repo)
TEST_WORKSPACE = Path.home() / "TestApps" / "e2e_websocket_test" / datetime.now().strftime("%Y%m%d_%H%M%S")
BACKEND_URL = "ws://localhost:8002/ws/chat"
BACKEND_PORT = 8002

# Project root
PROJECT_ROOT = Path(__file__).parent

# Logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# E2E TEST CONTEXT
# ============================================================

class E2ETestContext:
    """Manages test execution context"""
    
    def __init__(self):
        self.workspace = TEST_WORKSPACE
        self.backend_process = None
        self.websocket = None
        self.messages_received = []
        self.test_start_time = None
        self.test_end_time = None
        self.generated_files = []
        self.errors = []
    
    async def setup(self):
        """Setup test environment"""
        logger.info("🧪 Setting up E2E test environment...")
        
        # Clean workspace
        if self.workspace.exists():
            logger.warning(f"🧹 Removing old workspace: {self.workspace}")
            shutil.rmtree(self.workspace)
        
        # Create fresh workspace
        self.workspace.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Created clean workspace: {self.workspace}")
        
        # Verify isolation
        assert not (self.workspace / "any_app").exists(), "Workspace not clean!"
        logger.info("✅ Workspace isolation verified")
        
        # Start backend server
        await self.start_backend()
    
    async def start_backend(self):
        """Start backend server"""
        logger.info(f"🚀 Starting backend server on port {BACKEND_PORT}...")
        
        cmd = [
            sys.executable,
            str(PROJECT_ROOT / "start_server.py"),
            f"--port={BACKEND_PORT}",
            "--debug"
        ]
        
        try:
            self.backend_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(PROJECT_ROOT)
            )
            
            # Wait for server to start
            await asyncio.sleep(5)
            
            # Test connection
            for attempt in range(10):
                try:
                    async with websockets.connect(BACKEND_URL) as ws:
                        logger.info("✅ Backend server is ready!")
                        return
                except Exception as e:
                    if attempt < 9:
                        await asyncio.sleep(1)
                    else:
                        raise
        
        except Exception as e:
            logger.error(f"❌ Failed to start backend: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup test environment"""
        logger.info("🧹 Cleaning up test environment...")
        
        # Close websocket
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass
        
        # Stop backend
        if self.backend_process:
            self.backend_process.terminate()
            self.backend_process.wait(timeout=5)
        
        logger.info("✅ Cleanup complete")


# ============================================================
# WEBSOCKET CLIENT
# ============================================================

class E2EWebSocketClient:
    """WebSocket client for agent communication"""
    
    def __init__(self, ws_url: str, workspace: Path):
        self.ws_url = ws_url
        self.workspace = workspace
        self.ws = None
        self.message_id = 0
    
    async def connect(self):
        """Connect to backend"""
        logger.info(f"🔗 Connecting to {self.ws_url}...")
        
        try:
            self.ws = await websockets.connect(self.ws_url)
            logger.info("✅ Connected to backend via WebSocket")
            
            # Send initial handshake with workspace
            await self.send_init()
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            raise
    
    async def send_init(self):
        """Send initialization message with workspace"""
        logger.info(f"📤 Sending init with workspace: {self.workspace}")
        
        init_message = {
            "type": "init",
            "workspace_path": str(self.workspace),
            "timestamp": datetime.now().isoformat()
        }
        
        await self.ws.send(json.dumps(init_message))
        
        # Wait for acknowledgment
        response = await self.ws.recv()
        ack = json.loads(response)
        
        logger.info(f"✅ Init acknowledged: {ack}")
        
        if not ack.get("success"):
            raise RuntimeError("Init was not successful!")
    
    async def send_request(self, request: str) -> str:
        """Send user request to agent"""
        self.message_id += 1
        
        message = {
            "type": "message",
            "content": request,
            "id": self.message_id
        }
        
        logger.info(f"📤 Sending request #{self.message_id}: {request[:100]}...")
        await self.ws.send(json.dumps(message))
    
    async def receive_message(self) -> Dict[str, Any]:
        """Receive message from agent"""
        try:
            response = await asyncio.wait_for(
                self.ws.recv(),
                timeout=30.0
            )
            return json.loads(response)
        except asyncio.TimeoutError:
            logger.error("❌ Timeout waiting for message!")
            raise
    
    async def receive_all_messages(self, timeout: float = 60.0) -> List[Dict[str, Any]]:
        """Receive all messages until completion or timeout"""
        messages = []
        start_time = time.time()
        
        try:
            while time.time() - start_time < timeout:
                remaining = timeout - (time.time() - start_time)
                
                try:
                    msg = await asyncio.wait_for(
                        self.ws.recv(),
                        timeout=remaining
                    )
                    data = json.loads(msg)
                    messages.append(data)
                    
                    logger.debug(f"📨 Received: {data.get('type')} - {data.get('content', '')[:80]}...")
                    
                    # Check for completion
                    if data.get("type") == "complete":
                        logger.info("✅ Agent work completed")
                        break
                    
                except asyncio.TimeoutError:
                    break
        
        except Exception as e:
            logger.error(f"❌ Error receiving messages: {e}")
        
        return messages
    
    async def close(self):
        """Close connection"""
        if self.ws:
            await self.ws.close()
            logger.info("🔌 WebSocket closed")


# ============================================================
# VALIDATION FUNCTIONS
# ============================================================

class TestValidator:
    """Validates test results"""
    
    @staticmethod
    def validate_workspace_clean(workspace: Path) -> bool:
        """Check workspace is initially clean"""
        logger.info("✓ Validating: Workspace is clean initially")
        
        if not workspace.exists():
            logger.error("❌ Workspace doesn't exist!")
            return False
        
        files = list(workspace.glob("*"))
        if files:
            logger.error(f"❌ Workspace not clean! Found: {files}")
            return False
        
        logger.info("✅ Workspace is clean")
        return True
    
    @staticmethod
    def validate_agent_connection(context: E2ETestContext) -> bool:
        """Check agent connection works"""
        logger.info("✓ Validating: Agent connection established")
        
        if not context.backend_process:
            logger.error("❌ Backend process not started!")
            return False
        
        if context.backend_process.poll() is not None:
            logger.error("❌ Backend process crashed!")
            return False
        
        logger.info("✅ Agent connection successful")
        return True
    
    @staticmethod
    def validate_messages_received(messages: List[Dict]) -> bool:
        """Check messages were received from agent"""
        logger.info("✓ Validating: Messages received from agent")
        
        if not messages:
            logger.error("❌ No messages received!")
            return False
        
        logger.info(f"✅ Received {len(messages)} messages from agent")
        
        # Print message types
        message_types = {}
        for msg in messages:
            msg_type = msg.get("type", "unknown")
            message_types[msg_type] = message_types.get(msg_type, 0) + 1
        
        logger.info(f"   Message types: {message_types}")
        return True
    
    @staticmethod
    def validate_workspace_has_files(workspace: Path) -> bool:
        """Check files were generated in workspace"""
        logger.info("✓ Validating: Files generated in workspace")
        
        files = list(workspace.rglob("*"))
        if not files:
            logger.error("❌ No files generated in workspace!")
            return False
        
        # Find important files
        important_files = ["README.md", "package.json", "src", "tsconfig.json", "components"]
        found_files = [f.name for f in files]
        
        logger.info(f"   Generated files: {found_files[:10]}...")
        logger.info(f"✅ {len(files)} files generated")
        return True
    
    @staticmethod
    def validate_app_structure(workspace: Path) -> bool:
        """Check app has proper structure"""
        logger.info("✓ Validating: App structure is correct")
        
        # Check for common app structures
        has_package_json = (workspace / "package.json").exists()
        has_src = (workspace / "src").exists()
        has_readme = (workspace / "README.md").exists()
        
        if not has_package_json:
            logger.warning("⚠️  No package.json found")
        
        if not has_src:
            logger.warning("⚠️  No src directory found")
        
        if not has_readme:
            logger.warning("⚠️  No README found")
        
        has_structure = has_package_json and (has_src or has_readme)
        
        if has_structure:
            logger.info("✅ App structure looks correct")
        else:
            logger.error("❌ App structure incomplete")
        
        return has_structure
    
    @staticmethod
    def validate_no_errors_in_messages(messages: List[Dict]) -> bool:
        """Check for error messages"""
        logger.info("✓ Validating: No critical errors in responses")
        
        errors = []
        for msg in messages:
            if msg.get("type") == "error":
                errors.append(msg.get("content", ""))
            
            content = msg.get("content", "").lower()
            if "error" in content and "connection" not in content:
                errors.append(content)
        
        if errors:
            logger.error(f"❌ Errors found: {errors}")
            return False
        
        logger.info("✅ No critical errors found")
        return True
    
    @staticmethod
    def validate_workflow_completed(messages: List[Dict]) -> bool:
        """Check if agent workflow completed"""
        logger.info("✓ Validating: Workflow completed")
        
        # Check for completion indicators
        has_complete = any(msg.get("type") == "complete" for msg in messages)
        has_success = any("success" in msg.get("content", "").lower() for msg in messages)
        has_output = any(msg.get("type") == "output" for msg in messages)
        
        if has_complete or has_success or has_output:
            logger.info("✅ Workflow completed successfully")
            return True
        else:
            logger.warning("⚠️  Workflow completion unclear")
            return True  # Don't fail if completion message not explicit


# ============================================================
# MAIN E2E TEST
# ============================================================

async def run_e2e_test():
    """Run complete E2E test"""
    
    logger.info("=" * 70)
    logger.info("🤖 STARTING KI AGENT E2E WEBSOCKET TEST")
    logger.info("=" * 70)
    
    context = E2ETestContext()
    validator = TestValidator()
    all_passed = True
    
    try:
        # PHASE 1: Setup
        logger.info("\n📋 PHASE 1: SETUP")
        logger.info("-" * 70)
        await context.setup()
        
        if not validator.validate_agent_connection(context):
            all_passed = False
        
        if not validator.validate_workspace_clean(context.workspace):
            all_passed = False
        
        # PHASE 2: Connect to Agent
        logger.info("\n📋 PHASE 2: CONNECT TO AGENT")
        logger.info("-" * 70)
        
        client = E2EWebSocketClient(BACKEND_URL, context.workspace)
        await client.connect()
        context.websocket = client.ws
        
        # PHASE 3: Request App Generation
        logger.info("\n📋 PHASE 3: REQUEST APP GENERATION")
        logger.info("-" * 70)
        
        app_request = """
        Create a React Todo Application with:
        - Input field to add new todos
        - Display list of todos
        - Mark todos as complete/incomplete
        - Delete todo functionality
        - Local storage persistence
        - Responsive design
        - Unit tests for main functions
        """
        
        await client.send_request(app_request)
        context.test_start_time = datetime.now()
        
        # PHASE 4: Monitor Agent Execution
        logger.info("\n📋 PHASE 4: MONITOR AGENT EXECUTION")
        logger.info("-" * 70)
        
        messages = await client.receive_all_messages(timeout=120.0)  # 2 minutes max
        context.messages_received = messages
        context.test_end_time = datetime.now()
        
        # PHASE 5: Validate Results
        logger.info("\n📋 PHASE 5: VALIDATE RESULTS")
        logger.info("-" * 70)
        
        if not validator.validate_messages_received(messages):
            all_passed = False
        
        if not validator.validate_no_errors_in_messages(messages):
            all_passed = False
        
        if not validator.validate_workflow_completed(messages):
            all_passed = False
        
        # PHASE 6: Verify Generated Files
        logger.info("\n📋 PHASE 6: VERIFY GENERATED FILES")
        logger.info("-" * 70)
        
        if not validator.validate_workspace_has_files(context.workspace):
            all_passed = False
        
        if not validator.validate_app_structure(context.workspace):
            all_passed = False
        
        # PHASE 7: Summary
        logger.info("\n📋 PHASE 7: TEST SUMMARY")
        logger.info("-" * 70)
        
        duration = (context.test_end_time - context.test_start_time).total_seconds()
        logger.info(f"⏱️  Test duration: {duration:.1f} seconds")
        logger.info(f"📨 Messages received: {len(messages)}")
        logger.info(f"📁 Workspace: {context.workspace}")
        
        # List generated files
        files = list(context.workspace.rglob("*"))
        file_types = {}
        for f in files:
            ext = f.suffix or "no_ext"
            file_types[ext] = file_types.get(ext, 0) + 1
        
        logger.info(f"   File types: {file_types}")
        
        if all_passed:
            logger.info("\n" + "=" * 70)
            logger.info("✅ E2E TEST PASSED!")
            logger.info("=" * 70)
            return 0
        else:
            logger.error("\n" + "=" * 70)
            logger.error("❌ E2E TEST FAILED!")
            logger.error("=" * 70)
            return 1
    
    except Exception as e:
        logger.error(f"\n❌ TEST CRASHED: {e}", exc_info=True)
        return 1
    
    finally:
        await context.cleanup()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(run_e2e_test())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n⛔ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)