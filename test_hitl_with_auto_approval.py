#!/usr/bin/env python3
"""
Test: Auto-approve HITL and trace workflow execution

This test:
1. Connects to the running server via WebSocket
2. Sends a request (Create a new app)
3. When HITL is triggered, auto-approves with "ok"
4. Traces the complete workflow execution
5. Checks if responder receives output
"""

import asyncio
import json
import logging
import sys
from datetime import datetime

# Add repo to path
sys.path.insert(0, '/Users/dominikfoert/git/KI_AutoAgent')

import websockets
from websockets.client import WebSocketClientProtocol

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WorkflowTracer:
    """Trace workflow execution via WebSocket with HITL auto-approval"""
    
    def __init__(self):
        self.websocket: WebSocketClientProtocol | None = None
        self.session_id = f"test_hitl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.message_count = 0
        self.hitl_count = 0
        self.supervisor_count = 0
        self.agent_calls = []
        self.last_message_time = None
        self.timeout_seconds = 60
        
    async def connect(self, url: str = "ws://localhost:8002/ws/chat"):
        """Connect to WebSocket endpoint"""
        try:
            logger.info(f"🔗 Connecting to {url}...")
            self.websocket = await websockets.connect(url)
            logger.info("✅ Connected!")
            return True
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    async def send_init(self, workspace_path: str = "/tmp/test_workspace"):
        """Send initialization message"""
        init_msg = {
            "type": "init",
            "data": {
                "session_id": self.session_id,
                "user_id": "test_user",
                "workspace_path": workspace_path
            }
        }
        await self.websocket.send(json.dumps(init_msg))
        logger.info(f"📤 Sent: init (workspace: {workspace_path})")
    
    async def send_request(self, goal: str):
        """Send chat request"""
        request = {
            "type": "chat",
            "content": goal,
            "message": goal,
            "session_id": self.session_id
        }
        await self.websocket.send(json.dumps(request))
        logger.info(f"📤 Sent: chat request - '{goal}'")
    
    async def send_hitl_response(self, approval: str = "ok"):
        """Send HITL approval response"""
        response = {
            "type": "hitl_response",
            "data": {
                "user_response": approval,
                "session_id": self.session_id
            }
        }
        await self.websocket.send(json.dumps(response))
        logger.info(f"📤 Sent: HITL approval - '{approval}'")
    
    def process_message(self, msg: dict):
        """Process incoming message"""
        self.message_count += 1
        self.last_message_time = datetime.now()
        
        msg_type = msg.get("type")
        data = msg.get("data", {})
        
        # Log message
        logger.info(f"\n📨 Message #{self.message_count} [{msg_type}]")
        
        if msg_type == "progress":
            agent = data.get("agent", "unknown")
            status = data.get("status", "")
            logger.info(f"   Agent: {agent}")
            logger.info(f"   Status: {status}")
            
            if "supervisor" in agent.lower():
                self.supervisor_count += 1
                logger.info(f"   → Supervisor invocation #{self.supervisor_count}")
            
            if agent not in ["supervisor", "hitl"]:
                if agent not in self.agent_calls:
                    self.agent_calls.append(agent)
                    logger.info(f"   ✨ NEW AGENT DETECTED: {agent}")
        
        elif msg_type == "hitl_request":
            self.hitl_count += 1
            instructions = data.get("instructions", "")
            logger.warning(f"   ⚠️ HITL REQUEST #{self.hitl_count}")
            logger.warning(f"   Instructions: {instructions}")
            return "HITL"
        
        elif msg_type == "agent_complete":
            agent = data.get("agent", "unknown")
            logger.info(f"   ✅ {agent} completed")
            logger.info(f"   Output keys: {list(data.get('output', {}).keys())}")
        
        elif msg_type == "workflow_complete":
            logger.info("   🎉 WORKFLOW COMPLETE")
            response = data.get("user_response", "")
            logger.info(f"   Response length: {len(response)} chars")
            if response:
                logger.info(f"   Response preview: {response[:200]}...")
            return "COMPLETE"
        
        elif msg_type == "error":
            error = data.get("error", "")
            logger.error(f"   ❌ ERROR: {error}")
            return "ERROR"
        
        elif msg_type == "thinking":
            thinking = data.get("thinking", "")
            logger.info(f"   💭 {thinking}")
        
        else:
            logger.info(f"   Data: {data}")
        
        return None
    
    async def receive_loop(self):
        """Receive messages from WebSocket"""
        try:
            timeout_task = asyncio.create_task(asyncio.sleep(self.timeout_seconds))
            receive_task = asyncio.create_task(self._receive_messages())
            
            done, pending = await asyncio.wait(
                [timeout_task, receive_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            if timeout_task in done:
                logger.error(f"❌ TIMEOUT after {self.timeout_seconds}s")
                receive_task.cancel()
                for task in pending:
                    task.cancel()
                return "TIMEOUT"
            
            result = receive_task.result()
            timeout_task.cancel()
            return result
        
        except asyncio.CancelledError:
            logger.info("Receive loop cancelled")
            return None
        except Exception as e:
            logger.error(f"❌ Receive error: {e}")
            import traceback
            traceback.print_exc()
            return "ERROR"
    
    async def _receive_messages(self):
        """Internal: receive messages"""
        while True:
            try:
                msg_str = await self.websocket.recv()
                msg = json.loads(msg_str)
                
                result = self.process_message(msg)
                
                # Auto-respond to HITL
                if result == "HITL":
                    await asyncio.sleep(0.5)  # Small delay
                    await self.send_hitl_response("ok")
                    continue
                
                # Workflow complete
                if result == "COMPLETE":
                    await asyncio.sleep(0.5)
                    return "COMPLETE"
                
                # Error
                if result == "ERROR":
                    await asyncio.sleep(0.5)
                    return "ERROR"
            
            except json.JSONDecodeError:
                logger.warning(f"⚠️ Invalid JSON: {msg_str[:100]}")
            except websockets.exceptions.ConnectionClosed:
                logger.warning("⚠️ Connection closed by server")
                return "CLOSED"
            except Exception as e:
                logger.error(f"❌ Message processing error: {e}")
                await asyncio.sleep(0.5)


async def main():
    """Main test"""
    logger.info("=" * 70)
    logger.info("TEST: Auto-approve HITL and trace workflow")
    logger.info("=" * 70)
    
    tracer = WorkflowTracer()
    
    # Connect
    if not await tracer.connect():
        return
    
    try:
        # Initialize
        await tracer.send_init()
        await asyncio.sleep(0.5)
        
        # Send request
        await tracer.send_request("Create a new app with a todo list feature")
        
        # Receive and auto-approve HITL
        logger.info("\n⏳ Listening for workflow messages...")
        result = await tracer.receive_loop()
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("TEST SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Result: {result}")
        logger.info(f"Messages received: {tracer.message_count}")
        logger.info(f"HITL requests: {tracer.hitl_count}")
        logger.info(f"Supervisor invocations: {tracer.supervisor_count}")
        logger.info(f"Agents called: {tracer.agent_calls}")
        
        if tracer.supervisor_count > 20:
            logger.error(f"⚠️ SUSPICIOUS: Supervisor called {tracer.supervisor_count} times!")
            logger.error("    → Likely stuck in loop with HITL")
        
        if not tracer.agent_calls:
            logger.error("❌ NO AGENTS CALLED!")
            logger.error("    → Workflow is stuck before reaching agents")
        else:
            logger.info(f"✅ Agents executed: {', '.join(tracer.agent_calls)}")
        
    finally:
        if tracer.websocket:
            await tracer.websocket.close()
            logger.info("🔌 Disconnected")


if __name__ == "__main__":
    asyncio.run(main())