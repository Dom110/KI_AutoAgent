#!/usr/bin/env python3
"""
Detailed E2E Test with Extended Timeouts and Diagnostics
Tracks every message and timeout to identify where the system hangs
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
import time


async def run_detailed_e2e_test():
    """Run E2E test with detailed diagnostics."""
    
    print("\n" + "="*100)
    print("🧪 DETAILED E2E TEST - Extended Diagnostics")
    print("="*100)
    print(f"⏱️  Started: {datetime.now().isoformat()}")
    
    import websockets
    
    uri = "ws://localhost:8002/ws/chat"
    workspace_path = str(Path.home() / "Tests" / "e2e_test_detailed")
    
    # Create workspace
    Path(workspace_path).mkdir(parents=True, exist_ok=True)
    
    print(f"\n📁 Workspace: {workspace_path}")
    print(f"🌐 Backend: {uri}")
    print(f"⏱️  Message Timeout: 10 seconds per message")
    print(f"📊 Max Messages: 200")
    
    try:
        async with websockets.connect(uri) as ws:
            print("\n✅ [CONNECT] WebSocket connected")
            
            # Initial message
            initial = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(initial)
            print(f"✅ [INITIAL] {data.get('type')}")
            
            # Init workspace
            await ws.send(json.dumps({
                "type": "init",
                "workspace_path": workspace_path
            }))
            
            init_resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
            init_data = json.loads(init_resp)
            print(f"✅ [INIT] {init_data.get('type')}")
            
            # Send simple query
            query = "List files in current directory"
            print(f"\n📤 Sending query: {query}")
            print("   Waiting for workflow execution...")
            print("   " + "-"*96)
            
            await ws.send(json.dumps({
                "type": "chat",
                "content": query
            }))
            
            # Track execution timeline
            message_count = 0
            last_message_time = time.time()
            result_received = False
            messages_by_type = {}
            agent_nodes = set()
            
            while message_count < 200:
                try:
                    # Longer timeout per message (10 seconds)
                    response = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    data = json.loads(response)
                    message_count += 1
                    
                    msg_type = data.get('type', 'unknown')
                    messages_by_type[msg_type] = messages_by_type.get(msg_type, 0) + 1
                    
                    # Timestamp for this message
                    elapsed_total = time.time() - last_message_time
                    
                    # Log all messages
                    if message_count <= 50:  # Show first 50 messages
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        print(f"   [{message_count:3d}] {timestamp} | {msg_type:20} | {str(data)[:70]}...")
                    
                    # Detailed tracking
                    if msg_type == "progress":
                        node = data.get("node", "unknown")
                        agent_nodes.add(node)
                        print(f"       └─> [PROGRESS] node={node}")
                    
                    elif msg_type == "agent_event":
                        agent = data.get("agent", "unknown")
                        agent_nodes.add(agent)
                        event_type = data.get("event_type", "unknown")
                        print(f"       └─> [AGENT] agent={agent} event={event_type}")
                    
                    elif msg_type == "supervisor_event":
                        dec_type = data.get("event_type", "unknown")
                        print(f"       └─> [SUPERVISOR] event={dec_type}")
                    
                    elif msg_type == "result":
                        result_received = True
                        elapsed = time.time() - last_message_time
                        print(f"       └─> [RESULT] received after {elapsed:.1f}s")
                        print(f"           Content: {data.get('content', '')[:100]}")
                        
                    elif msg_type == "error":
                        print(f"       └─> [ERROR] {data.get('message', 'unknown')}")
                    
                    last_message_time = time.time()
                    
                except asyncio.TimeoutError:
                    elapsed = time.time() - last_message_time
                    print(f"\n   [{message_count:3d}] ⏱️  TIMEOUT - No message for 10 seconds")
                    print(f"           Last message was {elapsed:.1f}s ago")
                    
                    # Decision: break or continue?
                    if result_received:
                        print(f"           Result already received - breaking")
                        break
                    elif message_count < 5:
                        print(f"           Too few messages - connection may be broken")
                        break
                    else:
                        print(f"           Workflow may be stuck - waiting one more time...")
                        try:
                            print(f"           Trying one more message with 15s timeout...")
                            response = await asyncio.wait_for(ws.recv(), timeout=15.0)
                            data = json.loads(response)
                            message_count += 1
                            print(f"           ✅ Got message: {data.get('type')}")
                            continue
                        except asyncio.TimeoutError:
                            print(f"           Still no message - giving up")
                            break
                
                except json.JSONDecodeError as e:
                    print(f"   [{message_count}] ❌ JSON ERROR: {e}")
                    break
            
            # Summary
            total_time = time.time() - last_message_time
            print("\n" + "="*100)
            print("📊 DETAILED TEST SUMMARY")
            print("="*100)
            print(f"Messages received: {message_count}")
            print(f"Message types: {dict(messages_by_type)}")
            print(f"Agent nodes touched: {sorted(agent_nodes)}")
            print(f"Result received: {'✅ YES' if result_received else '❌ NO'}")
            print(f"Total execution time: {total_time:.1f}s")
            
            # Analysis
            print(f"\n🔍 ANALYSIS:")
            if message_count < 5:
                print(f"   ❌ CRITICAL: Only {message_count} messages - connection problem")
            elif not result_received and message_count > 10:
                print(f"   ❌ CRITICAL: Workflow stalled after {message_count} messages")
                print(f"   Possible causes:")
                print(f"      - Agent nodes blocking (MCPManager.call() hangs)")
                print(f"      - Supervisor decision not being routed")
                print(f"      - Agent node not implemented")
            elif result_received:
                print(f"   ✅ SUCCESS: Workflow completed successfully")
            else:
                print(f"   ⚠️  UNKNOWN: {message_count} messages but unclear state")
            
            print("="*100)
            return result_received
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_detailed_e2e_test())
    exit(0 if success else 1)
