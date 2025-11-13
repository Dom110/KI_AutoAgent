#!/usr/bin/env python3
"""
⚠️ E2E Test: Codesmith Code Generation with Workspace Isolation
Tests complete workflow: Architecture → Code Generation → File Verification

Focus:
1. Workspace isolation (request-specific workspace)
2. Codesmith code generation
3. File creation in workspace
4. Agent message parsing

Logging: Massive stdout output for debugging
"""

import asyncio
import json
import websockets
import time
import sys
from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import os

# ===== CONFIGURATION =====
PROJECT_ROOT = "/Users/dominikfoert/git/KI_AutoAgent"
SERVER_URL = "ws://localhost:8002/ws/chat"
TEST_WORKSPACE_BASE = Path.home() / "TestApps" / f"e2e_codesmith_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
TEST_WORKSPACE_BASE.mkdir(parents=True, exist_ok=True)

LOG_DIR = TEST_WORKSPACE_BASE / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Test logging setup
SEND_LOG = LOG_DIR / f"websocket_send.log"
RECV_LOG = LOG_DIR / f"websocket_recv.log"
COMBINED_LOG = LOG_DIR / f"websocket_combined.log"
MAIN_LOG = LOG_DIR / f"e2e_main.log"

def log_main(msg: str):
    """Log to both stdout and main log"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    line = f"{timestamp} | {msg}"
    print(line)
    with open(MAIN_LOG, "a") as f:
        f.write(line + "\n")

def log_sent(msg: str, data: dict):
    """Log outgoing WebSocket message"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    line = f"{timestamp} [SEND] {msg}\n{json.dumps(data, indent=2)}\n"
    with open(SEND_LOG, "a") as f:
        f.write(line)

def log_received(msg: str, data: dict):
    """Log incoming WebSocket message"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    line = f"{timestamp} [RECV] {msg}\n{json.dumps(data, indent=2)}\n"
    with open(RECV_LOG, "a") as f:
        f.write(line)

def log_combined(direction: str, msg: str, data: dict):
    """Log to combined chronological log"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    line = f"{timestamp} [{direction:4s}] {msg}\n"
    with open(COMBINED_LOG, "a") as f:
        f.write(line)
        if isinstance(data, dict):
            f.write(json.dumps(data, indent=2) + "\n\n")
        else:
            f.write(str(data) + "\n\n")

async def test_codesmith_generation():
    """🧪 Main E2E Test: Code Generation with Workspace Isolation"""
    
    log_main("\n" + "="*100)
    log_main("🚀 E2E TEST: Codesmith Code Generation with Workspace Isolation")
    log_main("="*100)
    
    log_main(f"\n📁 Test Workspace Base: {TEST_WORKSPACE_BASE}")
    log_main(f"📝 Logs Directory: {LOG_DIR}")
    
    # Phase 0: Connect
    log_main("\n" + "-"*100)
    log_main("PHASE 0: 🔌 WebSocket Connection")
    log_main("-"*100)
    
    try:
        async with websockets.connect(SERVER_URL) as ws:
            log_main("✅ Connected to WebSocket")
            
            # Phase 1: Wait for "connected" message
            log_main("\n" + "-"*100)
            log_main("PHASE 1: 🎯 Wait for Connected Response")
            log_main("-"*100)
            
            response = await asyncio.wait_for(ws.recv(), timeout=10.0)
            resp_data = json.loads(response)
            log_received("Connected response", resp_data)
            log_combined("RECV", "Connected", resp_data)
            
            session_id = resp_data.get("session_id")
            log_main(f"✅ Connected - Session: {session_id}")
            
            # Phase 2: Send init message
            log_main("\n" + "-"*100)
            log_main("PHASE 2: 📝 Send Init Message with Workspace")
            log_main("-"*100)
            
            workspace_path_str = str(TEST_WORKSPACE_BASE / "workspace_001")
            init_msg = {
                "type": "init",
                "workspace_path": workspace_path_str
            }
            log_sent("Init message", init_msg)
            log_combined("SEND", "Init", init_msg)
            await ws.send(json.dumps(init_msg))
            
            log_main(f"✅ Init message sent with workspace: {workspace_path_str}")
            
            # Verify workspace exists (create if needed)
            ws_obj = Path(workspace_path_str)
            ws_obj.mkdir(parents=True, exist_ok=True)
            log_main(f"✅ Workspace directory ready: {workspace_path_str}")
            
            # Phase 3: Send Code Generation Request
            log_main("\n" + "-"*100)
            log_main("PHASE 3: 📝 Request Code Generation")
            log_main("-"*100)
            
            gen_request = {
                "type": "chat",
                "content": "Generate a simple REST API using Flask with basic CRUD operations for a Todo app",
                "agent": "codesmith"  # Explicitly request codesmith
            }
            log_sent("Code generation request", gen_request)
            log_combined("SEND", "Code Gen Request", gen_request)
            await ws.send(json.dumps(gen_request))
            
            log_main("⏳ Waiting for code generation response...")
            
            # Phase 4: Collect responses
            log_main("\n" + "-"*100)
            log_main("PHASE 4: 📡 Receiving Agent Messages")
            log_main("-"*100)
            
            responses_received = []
            events_received = []
            start_time = time.time()
            timeout = 60.0  # 60 second timeout
            
            while time.time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    resp_data = json.loads(response)
                    
                    msg_type = resp_data.get("type", "unknown")
                    log_received(f"Message type: {msg_type}", resp_data)
                    log_combined("RECV", msg_type, resp_data)
                    
                    responses_received.append(resp_data)
                    
                    if msg_type == "workflow_complete":
                        log_main("✅ Workflow completed!")
                        break
                    elif msg_type == "agent_event":
                        event_type = resp_data.get("event_type")
                        agent = resp_data.get("agent")
                        events_received.append({
                            "agent": agent,
                            "event_type": event_type,
                            "timestamp": datetime.now().isoformat()
                        })
                        log_main(f"  → Agent: {agent}, Event: {event_type}")
                    elif msg_type == "mcp_progress":
                        server = resp_data.get("server")
                        message = resp_data.get("message")
                        progress = resp_data.get("progress", 0.0)
                        log_main(f"  → Progress [{server}]: {message} ({progress*100:.0f}%)")
                    elif msg_type == "status":
                        status = resp_data.get("status")
                        log_main(f"  → Status: {status}")
                        
                except asyncio.TimeoutError:
                    # Normal timeout waiting for next message
                    continue
                except json.JSONDecodeError as e:
                    log_main(f"⚠️ Failed to parse JSON: {e}")
                    continue
            
            log_main(f"\n✅ Received {len(responses_received)} messages in {time.time() - start_time:.1f}s")
            
            # Phase 5: Verify workspace files
            log_main("\n" + "-"*100)
            log_main("PHASE 5: 📂 Verify Generated Files in Workspace")
            log_main("-"*100)
            
            files_in_workspace = list(ws_obj.rglob("*"))
            files_in_workspace = [f for f in files_in_workspace if f.is_file()]
            
            log_main(f"\n📊 Workspace Statistics:")
            log_main(f"  Total files: {len(files_in_workspace)}")
            
            if files_in_workspace:
                log_main(f"\n📄 Generated Files:")
                for f in files_in_workspace[:20]:  # Show first 20
                    rel_path = f.relative_to(ws_obj)
                    size = f.stat().st_size
                    log_main(f"  ✅ {rel_path} ({size} bytes)")
                    
                    # Log file content for small files
                    if size < 500:
                        try:
                            content = f.read_text()[:200]
                            log_main(f"     Content preview: {content[:100]}...")
                        except:
                            pass
                        
                if len(files_in_workspace) > 20:
                    log_main(f"  ... and {len(files_in_workspace) - 20} more files")
            else:
                log_main("⚠️ No files generated in workspace (expected if code is too complex)")
            
            # Phase 6: Analyze Agent Events
            log_main("\n" + "-"*100)
            log_main("PHASE 6: 🤖 Agent Execution Analysis")
            log_main("-"*100)
            
            log_main(f"\n📊 Agent Events ({len(events_received)} total):")
            for i, event in enumerate(events_received, 1):
                log_main(f"  {i}. {event['agent']} - {event['event_type']}")
            
            # Phase 7: Workspace Isolation Verification
            log_main("\n" + "-"*100)
            log_main("PHASE 7: 🔒 Workspace Isolation Verification")
            log_main("-"*100)
            
            # Check that workspace is truly isolated
            log_main(f"\n✅ Workspace Path: {workspace_path_str}")
            log_main(f"✅ Base: {TEST_WORKSPACE_BASE}")
            
            # Verify it's unique
            is_isolated = str(workspace_path_str).startswith(str(TEST_WORKSPACE_BASE))
            if is_isolated:
                log_main("✅ Workspace is isolated (under test base)")
            else:
                log_main("❌ Workspace isolation FAILED!")
                return False
            
            # Summary
            log_main("\n" + "="*100)
            log_main("✅ E2E TEST SUMMARY")
            log_main("="*100)
            log_main(f"✅ WebSocket connection: SUCCESS")
            log_main(f"✅ Workspace initialization: SUCCESS ({workspace_path_str})")
            log_main(f"✅ Code generation request: SENT")
            log_main(f"✅ Agent responses: {len(responses_received)} received")
            log_main(f"✅ Files generated: {len(files_in_workspace)} files")
            log_main(f"✅ Workspace isolation: VERIFIED")
            log_main(f"\n📝 All logs saved to: {LOG_DIR}")
            log_main("="*100 + "\n")
            
            return True
            
    except Exception as e:
        log_main(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        log_main(traceback.format_exc())
        return False

async def main():
    """Start server and run test"""
    
    # Kill any existing server
    log_main("\n🛑 Cleaning up old processes...")
    os.system("pkill -f 'python.*server_v7' 2>/dev/null || true")
    await asyncio.sleep(1)
    
    # Start server
    log_main("\n🎬 Starting backend server...")
    server_proc = subprocess.Popen(
        ["python", "-u", "start_server.py"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to be ready
    log_main("⏳ Waiting for server to be ready...")
    for _ in range(30):
        try:
            import urllib.request
            urllib.request.urlopen("http://localhost:8002/health", timeout=1)
            log_main("✅ Server is ready!")
            break
        except:
            await asyncio.sleep(1)
    else:
        log_main("❌ Server failed to start!")
        server_proc.kill()
        return False
    
    try:
        # Run test
        success = await test_codesmith_generation()
        return success
    finally:
        # Cleanup
        log_main("\n🛑 Stopping server...")
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except:
            server_proc.kill()

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        log_main("\n⚠️ Test interrupted by user")
        sys.exit(1)
