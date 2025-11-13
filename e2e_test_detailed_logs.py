#!/usr/bin/env python3
"""
E2E Test 1 with DETAILED Output
Shows ALL events, routing decisions, and credit usage.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def run_detailed_test():
    """Run E2E Test 1 with full detailed output."""
    import aiohttp

    workspace_path = "/Users/dominikfoert/TestApps/e2e_test_1_new_app"
    ws_url = "ws://localhost:8002/ws/chat"

    print("\n" + "="*100)
    print("🧪 E2E TEST 1: Temperature Converter with DETAILED MONITORING")
    print("="*100)
    print(f"🏠 Workspace: {workspace_path}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100 + "\n")

    # Tracking variables
    events = []
    routing_decisions = []
    credit_info = {"updates": [], "total_cost": 0.0, "session_cost": 0.0}
    errors = []

    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url, timeout=aiohttp.ClientTimeout(total=600)) as ws:
                print("✅ Connected to WebSocket\n")

                # Send initialization
                await ws.send_json({"type": "init", "workspace_path": workspace_path})
                print("📤 Sent INIT message")

                # Send task
                task = "Create a Python CLI tool that converts temperatures between Celsius, Fahrenheit, and Kelvin."
                await ws.send_json({"type": "chat", "query": task})
                print(f"📤 Sent TASK: {task}\n")

                # Process events
                start_time = asyncio.get_event_loop().time()
                timeout_seconds = 300  # 5 minutes

                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        event = json.loads(msg.data)
                        events.append(event)
                        event_type = event.get("type", "unknown")

                        # Print event
                        print(f"\n[Event #{len(events)}] Type: {event_type}")
                        
                        if event_type == "credit_update":
                            usage = event.get("usage", {})
                            print(f"💰 Session: ${usage.get('session_cost', 0):.4f}, Total: ${usage.get('total_cost', 0):.4f}")
                            credit_info["total_cost"] = usage.get("total_cost", 0)
                            credit_info["session_cost"] = usage.get("session_cost", 0)
                            
                        elif event_type == "supervisor_event":
                            message = event.get("message", "")
                            if "routing to:" in message.lower():
                                agent = message.split(":")[-1].strip()
                                routing_decisions.append(agent)
                                print(f"🎯 ROUTING TO: {agent}")
                                
                        elif event_type == "mcp_progress":
                            server = event.get("server", "")
                            message = event.get("message", "")
                            if "Claude" in message or "Error" in message:
                                print(f"   {server}: {message}")
                                
                        elif event_type == "error":
                            errors.append(event.get("error", ""))
                            print(f"❌ ERROR: {event.get('error', '')}")
                            
                        elif event_type == "workflow_complete":
                            print("✅ WORKFLOW COMPLETE!")
                            break
                            
                        elif event_type == "response":
                            print(f"✅ Got response ({len(event.get('response', ''))} chars)")

                    # Check timeout
                    if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                        print(f"\n⏰ TIMEOUT")
                        break

    except Exception as e:
        print(f"\n❌ Exception: {e}")
        errors.append(str(e))

    # Summary
    print("\n" + "="*50)
    print("📊 SUMMARY")
    print(f"Events: {len(events)}")
    print(f"Routing: {' → '.join(routing_decisions)}")
    print(f"Cost: ${credit_info['session_cost']:.4f}")
    print(f"Errors: {len(errors)}")
    
    # Check files
    workspace = Path(workspace_path)
    if workspace.exists():
        py_files = list(workspace.rglob("*.py"))
        print(f"Files created: {len(py_files)}")
        
    success = len(errors) == 0 and len(py_files) > 0
    print(f"\n{'✅ PASSED' if success else '❌ FAILED'}")
    return success

if __name__ == "__main__":
    # Clean workspace
    from pathlib import Path
    import shutil
    workspace = Path("/Users/dominikfoert/TestApps/e2e_test_1_new_app")
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    
    # Run test
    asyncio.run(run_detailed_test())
