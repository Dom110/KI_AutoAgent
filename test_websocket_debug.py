#!/usr/bin/env python3
"""
Test WebSocket Communication and Debug Logging

This test simulates a real user task to verify:
1. WebSocket connection establishment
2. Message flow from client to server
3. Agent processing and response
4. Debug logging throughout the pipeline
"""

import asyncio
import json
import logging
import websockets
import sys
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_websocket_debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class WebSocketTestClient:
    def __init__(self):
        self.uri = "ws://localhost:8000/ws/chat"
        self.websocket = None
        self.client_id = None
        self.received_messages = []
        
    async def connect(self):
        """Establish WebSocket connection"""
        try:
            logger.info(f"🔌 Connecting to {self.uri}")
            self.websocket = await websockets.connect(self.uri)
            
            # Wait for connection message with client_id
            message = await self.websocket.recv()
            data = json.loads(message)
            
            if data.get('type') == 'connection':
                self.client_id = data.get('client_id')
                logger.info(f"✅ Connected! Client ID: {self.client_id}")
                return True
            else:
                logger.error(f"❌ Unexpected connection message: {data}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    async def send_task(self, task_description):
        """Send a task to the server"""
        message = {
            "type": "chat",
            "content": task_description,
            "agent": "auto",  # Use orchestrator
            "mode": "auto"
        }
        
        logger.info(f"📤 Sending task: {task_description[:100]}...")
        logger.debug(f"Full message: {json.dumps(message, indent=2)}")
        
        await self.websocket.send(json.dumps(message))
    
    async def receive_messages(self, timeout=30):
        """Receive and log all messages from server"""
        start_time = time.time()
        
        try:
            while time.time() - start_time < timeout:
                # Set a shorter timeout for each receive
                message = await asyncio.wait_for(
                    self.websocket.recv(), 
                    timeout=1.0
                )
                
                data = json.loads(message)
                self.received_messages.append(data)
                
                msg_type = data.get('type', 'unknown')
                agent = data.get('agent', 'system')
                
                # Log different message types
                if msg_type == 'agent_thinking':
                    logger.info(f"💭 Agent thinking: {agent}")
                    
                elif msg_type == 'agent_progress':
                    progress = data.get('content', '')
                    logger.info(f"📊 Progress from {agent}: {progress[:100]}")
                    
                elif msg_type == 'agent_response':
                    content = data.get('content', '')
                    status = data.get('status', 'unknown')
                    logger.info(f"📥 Response from {agent} (status: {status})")
                    logger.info(f"Content preview: {content[:200]}...")
                    
                    # If we got a final response, we can stop
                    if status == 'success':
                        logger.info("✅ Task completed successfully!")
                        break
                        
                elif msg_type == 'error':
                    error = data.get('content', 'Unknown error')
                    logger.error(f"❌ Error: {error}")
                    break
                    
                else:
                    logger.debug(f"📨 Message type: {msg_type}, Agent: {agent}")
                    
        except asyncio.TimeoutError:
            # This is expected when no more messages are coming
            pass
        except Exception as e:
            logger.error(f"❌ Error receiving messages: {e}")
    
    async def close(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            logger.info("🔌 Connection closed")

async def run_test():
    """Run the complete test scenario"""
    logger.info("="*60)
    logger.info("🚀 Starting WebSocket Debug Test")
    logger.info("="*60)
    
    client = WebSocketTestClient()
    
    # Test 1: Connection
    logger.info("\n📋 Test 1: Establishing Connection")
    connected = await client.connect()
    if not connected:
        logger.error("Failed to connect. Is the server running on port 8001?")
        return
    
    # Test 2: Simple Query
    logger.info("\n📋 Test 2: Simple Query")
    await client.send_task("What agents are available in the system?")
    await client.receive_messages(timeout=10)
    
    # Test 3: Complex Task (triggers agent thinking)
    logger.info("\n📋 Test 3: Complex Task")
    await client.send_task("Analyze the WebSocket communication in backend/api/server.py and identify any potential issues")
    await client.receive_messages(timeout=30)
    
    # Close connection
    await client.close()
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 Test Summary")
    logger.info("="*60)
    logger.info(f"Total messages received: {len(client.received_messages)}")
    
    # Count message types
    message_types = {}
    for msg in client.received_messages:
        msg_type = msg.get('type', 'unknown')
        message_types[msg_type] = message_types.get(msg_type, 0) + 1
    
    logger.info("Message type breakdown:")
    for msg_type, count in message_types.items():
        logger.info(f"  - {msg_type}: {count}")
    
    # Check for specific debug indicators
    has_thinking = any(msg.get('type') == 'agent_thinking' for msg in client.received_messages)
    has_progress = any(msg.get('type') == 'agent_progress' for msg in client.received_messages)
    has_response = any(msg.get('type') == 'agent_response' for msg in client.received_messages)
    
    logger.info("\n✅ Debug Features Verified:")
    logger.info(f"  - Agent thinking messages: {'✓' if has_thinking else '✗'}")
    logger.info(f"  - Progress updates: {'✓' if has_progress else '✗'}")
    logger.info(f"  - Final responses: {'✓' if has_response else '✗'}")
    
    # Save full log for analysis
    with open('test_websocket_messages.json', 'w') as f:
        json.dump(client.received_messages, f, indent=2)
    logger.info("\n📁 Full message log saved to test_websocket_messages.json")
    logger.info("📁 Debug log saved to test_websocket_debug.log")

if __name__ == "__main__":
    logger.info(f"🕐 Test started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        logger.info("\n⚠️ Test interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}")
    
    logger.info(f"\n🕐 Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")