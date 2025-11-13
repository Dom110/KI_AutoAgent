#!/usr/bin/env python3
"""
🔍 WEBSOCKET STATE TRACING TEST

This test connects to the running server via WebSocket and traces
what state data flows through the workflow in real-time.

Requires: server running on ws://localhost:8002/ws/chat
"""

import asyncio
import json
import sys
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("websocket_trace")

sys.path.insert(0, str(Path(__file__).parent))

import websockets


async def test_websocket_trace():
    """Connect to server and trace workflow state"""
    
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*15 + "WEBSOCKET STATE TRACING TEST" + " "*25 + "║")
    print("║" + " "*18 + "Trace data flow via WebSocket" + " "*21 + "║")
    print("╚" + "="*68 + "╝\n")
    
    try:
        # Connect to server
        uri = "ws://localhost:8002/ws/chat"
        logger.info(f"🔌 Connecting to {uri}...")
        
        async with websockets.connect(uri) as ws:
            logger.info("✅ Connected to server")
            
            # Connection message
            conn_msg = await ws.recv()
            logger.info(f"📨 Connection message received")
            
            # Initialize
            logger.info(f"📤 Sending init message...")
            await ws.send(json.dumps({
                "type": "init",
                "workspace_path": "/tmp/test_ws"
            }))
            init_msg = await ws.recv()
            logger.info(f"✅ Initialized")
            
            # Send query
            request = {
                "type": "chat",
                "content": "Create a simple calculator API with FastAPI"
            }
            
            logger.info(f"📤 Sending query...")
            await ws.send(json.dumps(request))
            
            # Track state changes
            step = 0
            last_agent = None
            received_data = {
                "research": False,
                "architect": False,
                "codesmith": False,
                "reviewfix": False,
                "responder": False
            }
            
            # Receive messages
            print("\n" + "="*70)
            print("📊 WORKFLOW EXECUTION TRACE")
            print("="*70 + "\n")
            
            while True:
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=120)
                    data = json.loads(message)
                    
                    step += 1
                    msg_type = data.get("type", "unknown")
                    
                    # Log different message types
                    if msg_type == "progress":
                        agent = data.get("agent", "unknown")
                        stage = data.get("stage", "")
                        progress_msg = data.get("message", "")
                        
                        if agent != last_agent:
                            print(f"\n👤 AGENT: {agent.upper()}")
                            last_agent = agent
                        
                        print(f"   ⏳ {stage}: {progress_msg[:60]}")
                        
                        # Track what agents are producing
                        if "research" in agent.lower():
                            received_data["research"] = True
                        elif "architect" in agent.lower():
                            received_data["architect"] = True
                        elif "codesmith" in agent.lower():
                            received_data["codesmith"] = True
                        elif "reviewfix" in agent.lower() or "review" in agent.lower():
                            received_data["reviewfix"] = True
                        elif "responder" in agent.lower():
                            received_data["responder"] = True
                    
                    elif msg_type == "response":
                        print(f"\n✅ RESPONSE RECEIVED")
                        content = data.get("content", "")
                        print(f"   Length: {len(content)} chars")
                        print(f"   First 200 chars: {content[:200]}")
                    
                    elif msg_type == "error":
                        print(f"\n❌ ERROR: {data.get('message', 'Unknown error')}")
                    
                    elif msg_type == "complete":
                        print(f"\n✅ WORKFLOW COMPLETE")
                        break
                    
                    elif msg_type == "state_update":
                        # This might contain state information
                        print(f"\n📊 STATE UPDATE:")
                        state = data.get("state", {})
                        for key in ["research_context", "architecture", "generated_files", "validation_results"]:
                            if key in state:
                                value = state[key]
                                if value is None:
                                    print(f"   ❌ {key}: None")
                                elif isinstance(value, dict):
                                    print(f"   ✅ {key}: dict({len(value)} keys)")
                                elif isinstance(value, list):
                                    print(f"   ✅ {key}: list({len(value)} items)")
                                else:
                                    print(f"   ✅ {key}: {type(value).__name__}")
                    
                    # Safety check
                    if step > 100:
                        logger.warning("⚠️ Stopping after 100 messages")
                        break
                        
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Timeout waiting for message")
                    break
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ Failed to parse JSON: {e}")
                    continue
            
            # Summary
            print("\n" + "="*70)
            print("📊 TRACE SUMMARY")
            print("="*70)
            
            for agent, received in received_data.items():
                status = "✅ Executed" if received else "❌ Not executed"
                print(f"  {status}: {agent}")
            
    except Exception as e:
        logger.error(f"❌ WebSocket test failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(test_websocket_trace())