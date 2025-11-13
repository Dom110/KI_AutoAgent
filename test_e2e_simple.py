#!/usr/bin/env python3
"""
Simplified E2E Test - Single Task Test
Tests a simple query flow and measures response time
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path


async def run_simple_test():
    """Run a single simple test."""
    
    print("\n" + "="*100)
    print("🧪 SIMPLIFIED E2E TEST - Single Task")
    print("="*100)
    print(f"⏱️  Started: {datetime.now().isoformat()}")
    
    import websockets
    
    uri = "ws://localhost:8002/ws/chat"
    workspace_path = str(Path.home() / "Tests" / "e2e_workspace_simple")
    
    print(f"\n📁 Workspace: {workspace_path}")
    print(f"🌐 Backend: {uri}")
    
    # Create workspace
    Path(workspace_path).mkdir(parents=True, exist_ok=True)
    
    try:
        async with websockets.connect(uri) as ws:
            print("\n[1/4] Connected")
            
            # Initial message
            initial = await asyncio.wait_for(ws.recv(), timeout=3.0)
            data = json.loads(initial)
            print(f"[2/4] Initial: {data.get('type')} (session_id: {data.get('session_id', 'N/A')[:8]}...)")
            
            # Init workspace
            await ws.send(json.dumps({
                "type": "init",
                "workspace_path": workspace_path
            }))
            
            init_resp = await asyncio.wait_for(ws.recv(), timeout=3.0)
            init_data = json.loads(init_resp)
            print(f"[3/4] Initialized: {init_data.get('type')}")
            print(f"      MCP Servers: {init_data.get('mcp_servers_available', [])[:3]}...")
            
            # Send simple query
            query = "List files in current directory"
            print(f"\n[4/4] Sending query: {query}")
            print("      Waiting for response...")
            
            await ws.send(json.dumps({
                "type": "chat",
                "content": query
            }))
            
            # Collect messages
            messages = []
            message_count = 0
            result_received = False
            error_received = False
            start_time = datetime.now()
            
            while message_count < 100:  # Max 100 messages
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=3.0)
                    data = json.loads(response)
                    message_count += 1
                    
                    msg_type = data.get('type', 'unknown')
                    messages.append(msg_type)
                    
                    if message_count <= 10:
                        print(f"  [{message_count}] {msg_type:20} | Content: {str(data)[:80]}...")
                    
                    if msg_type == "result":
                        result_received = True
                        elapsed = (datetime.now() - start_time).total_seconds()
                        print(f"\n✅ RESULT received after {elapsed:.1f}s")
                        print(f"   Content: {data.get('content', '')[:200]}")
                        
                    elif msg_type == "error":
                        error_received = True
                        print(f"\n❌ ERROR: {data.get('message', 'Unknown')}")
                        
                except asyncio.TimeoutError:
                    print(f"  [TIMEOUT] No message for 3 seconds (total messages: {message_count})")
                    break
                except json.JSONDecodeError as e:
                    print(f"  [JSON ERROR] {e}")
                    break
            
            # Summary
            elapsed = (datetime.now() - start_time).total_seconds()
            print("\n" + "="*100)
            print("📊 TEST SUMMARY")
            print("="*100)
            print(f"Total Messages Received: {message_count}")
            print(f"Total Time: {elapsed:.1f}s")
            print(f"Message Types: {set(messages)}")
            print(f"Result Received: {'✅ YES' if result_received else '❌ NO'}")
            print(f"Error Received: {'⚠️  YES' if error_received else '✅ NO'}")
            
            if result_received:
                print("\n✅ TEST PASSED - Response received successfully")
            else:
                print("\n❌ TEST FAILED - No result received")
            
            print("="*100)
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {type(e).__name__}: {e}")
        print("="*100)


if __name__ == "__main__":
    asyncio.run(run_simple_test())
