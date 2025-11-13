#!/usr/bin/env python3
"""
E2E Test: CREATE - First agent test with detailed logging
Runs: Supervisor → Research → Architect → Codesmith → ReviewFix → Responder

Timeout Strategy:
- Per message: 10s (MCP may be slow)
- Total test: 300s (5 minutes)
- Max silent messages: 20 (allow many retries)
"""

import asyncio
import json
import websockets
import sys
from datetime import datetime
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================

WORKSPACE = "/Users/dominikfoert/TestApps/e2e_v7_create"
SERVER_URL = "ws://localhost:8002/ws/chat"

# Timeouts
MESSAGE_TIMEOUT = 10.0  # Per message
TOTAL_TIMEOUT = 300.0   # 5 minutes
MAX_SILENT = 20         # Allow 20 silent cycles

# Create workspace
Path(WORKSPACE).mkdir(parents=True, exist_ok=True)

# ============================================================================
# Logging
# ============================================================================

def log_section(title: str, char="="):
    """Print formatted section header"""
    print(f"\n{char * 80}")
    print(f"{title:^80}")
    print(f"{char * 80}\n")

def log_message(level: str, msg: str):
    """Log with timestamp"""
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{ts}] {level:12} {msg}")

def log_state(title: str, data: dict):
    """Log state data as JSON"""
    print(f"\n{title}:")
    print(json.dumps(data, indent=2))

def log_event(data: dict):
    """Log WebSocket event"""
    msg_type = data.get("type", "unknown")
    
    if msg_type == "status":
        log_message("📊 STATUS", data.get("message", ""))
    elif msg_type == "agent_event":
        agent = data.get("agent", "?")
        event = data.get("event_type", "?")
        msg = data.get("message", "")
        log_message("🤖 AGENT", f"{agent}.{event}: {msg}")
    elif msg_type == "supervisor_event":
        event = data.get("event_type", "?")
        msg = data.get("message", "")
        next_agent = data.get("next_agent", "?")
        log_message("👔 SUPERVISOR", f"{event} → {next_agent}: {msg}")
    elif msg_type == "progress":
        node = data.get("node", "?")
        msg = data.get("message", "")
        log_message("📈 PROGRESS", f"{node}: {msg}")
    elif msg_type == "error":
        msg = data.get("message", "unknown")
        log_message("❌ ERROR", msg)
    elif msg_type == "initialized":
        log_message("✅ INIT", "Workflow ready")
    else:
        log_message("💬 MESSAGE", msg_type)

# ============================================================================
# Test
# ============================================================================

async def run_test():
    """Run first CREATE test"""
    
    log_section("TEST_1_CREATE", "=")
    
    query = "Create a simple REST API with FastAPI that manages a todo list. Include CRUD operations."
    print(f"Query: {query}\n")
    print(f"Workspace: {WORKSPACE}\n")
    
    start_time = datetime.now()
    message_count = 0
    silent_count = 0
    session_id = None
    
    try:
        async with websockets.connect(SERVER_URL) as ws:
            log_message("✅ CONNECT", f"Connected to {SERVER_URL}")
            
            # ====================================================================
            # MESSAGE 1: Receive initial connection
            # ====================================================================
            log_message("⏳ RECV", "Waiting for CONNECTED message...")
            msg = await asyncio.wait_for(ws.recv(), timeout=MESSAGE_TIMEOUT)
            data = json.loads(msg)
            message_count += 1
            log_message(f"📨 MSG#{message_count}", f"type={data.get('type')}")
            log_event(data)
            
            if data.get("type") != "connected":
                raise ValueError(f"Expected 'connected', got {data.get('type')}")
            
            session_id = data.get("session_id")
            if not session_id:
                raise ValueError("No session_id in connected message!")
            
            log_message("ℹ️  SESSION", session_id)
            
            # ====================================================================
            # MESSAGE 2: Send INIT
            # ====================================================================
            init_msg = {
                "type": "init",
                "workspace_path": WORKSPACE
            }
            log_message("📤 SEND", "Sending INIT message...")
            await ws.send(json.dumps(init_msg))
            
            # ====================================================================
            # MESSAGE 3: Receive INITIALIZED
            # ====================================================================
            log_message("⏳ RECV", "Waiting for INITIALIZED message...")
            msg = await asyncio.wait_for(ws.recv(), timeout=MESSAGE_TIMEOUT)
            data = json.loads(msg)
            message_count += 1
            log_message(f"📨 MSG#{message_count}", f"type={data.get('type')}")
            log_event(data)
            
            if data.get("type") != "initialized":
                raise ValueError(f"Expected 'initialized', got {data.get('type')}")
            
            mcp_servers = data.get("mcp_servers_available", [])
            log_message("ℹ️  MCP_SERVERS", f"{len(mcp_servers)} servers available")
            
            # ====================================================================
            # MESSAGE 4: Send CHAT (query)
            # ====================================================================
            chat_msg = {
                "type": "chat",
                "content": query
            }
            log_message("📤 SEND", "Sending CHAT message with query...")
            await ws.send(json.dumps(chat_msg))
            
            # ====================================================================
            # MESSAGES 5+: Collect responses until complete
            # ====================================================================
            log_message("⏳ COLLECT", "Listening for workflow messages (timeout: 10s/msg)...")
            print()
            
            last_event_time = datetime.now()
            final_response = None
            
            while True:
                elapsed = (datetime.now() - start_time).total_seconds()
                
                # Check total timeout
                if elapsed > TOTAL_TIMEOUT:
                    log_message("❌ TIMEOUT", f"Total timeout after {elapsed:.1f}s")
                    break
                
                # Try to receive message with timeout
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=MESSAGE_TIMEOUT)
                    data = json.loads(msg)
                    message_count += 1
                    silent_count = 0  # Reset on successful receive
                    
                    log_message(f"📨 MSG#{message_count}", f"type={data.get('type')}")
                    log_event(data)
                    
                    last_event_time = datetime.now()
                    
                    # Check for completion
                    if data.get("type") == "complete":
                        log_message("✅ COMPLETE", "Workflow finished successfully!")
                        final_response = data
                        break
                    
                    if data.get("type") == "error":
                        log_message("❌ ERROR", f"Workflow error: {data.get('message')}")
                        final_response = data
                        break
                    
                except asyncio.TimeoutError:
                    silent_count += 1
                    elapsed = (datetime.now() - start_time).total_seconds()
                    
                    log_message(f"⏱️  TIMEOUT#{silent_count}", 
                               f"No message for {MESSAGE_TIMEOUT}s (total: {elapsed:.1f}s)")
                    
                    if silent_count >= MAX_SILENT:
                        log_message("❌ MAX_TIMEOUTS", f"Reached {MAX_SILENT} silent cycles")
                        break
        
        # ====================================================================
        # Report Results
        # ====================================================================
        elapsed = (datetime.now() - start_time).total_seconds()
        
        log_section("TEST RESULTS", "=")
        
        print(f"Duration:       {elapsed:.1f}s")
        print(f"Messages:       {message_count}")
        print(f"Silent cycles:  {silent_count}")
        print(f"Session ID:     {session_id}\n")
        
        if final_response and final_response.get("type") == "complete":
            print("✅ TEST PASSED - Workflow completed successfully!\n")
            return 0
        else:
            print(f"❌ TEST FAILED - Workflow did not complete\n")
            if final_response:
                print(f"Final state: {final_response.get('type')}")
            return 1
    
    except Exception as e:
        log_message("❌ EXCEPTION", str(e))
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n❌ TEST FAILED after {elapsed:.1f}s")
        print(f"Error: {type(e).__name__}: {e}")
        return 1

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(run_test())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user")
        sys.exit(130)
