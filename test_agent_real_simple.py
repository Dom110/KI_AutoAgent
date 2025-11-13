#!/usr/bin/env python3
"""
🚀 ECHTE E2E TEST - Vereinfacht und praktisch
Keine Theorie, keine Dokumentation - nur TEST DURCHFÜHREN!
"""

import asyncio
import json
import websockets
import time
import subprocess
import sys
import signal
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIG
# ============================================================================

PROJECT_ROOT = Path(__file__).parent
SERVER_PORT = 8002
BACKEND_URL = f"ws://localhost:{SERVER_PORT}/ws/chat"
WORKSPACE = Path.home() / "TestApps" / "e2e_test" / datetime.now().strftime("%Y%m%d_%H%M%S")
TIMEOUT = 90

# ============================================================================
# COLORS FOR OUTPUT
# ============================================================================

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_status(msg, status="INFO"):
    """Print colored status messages"""
    if status == "PASS":
        color = Colors.GREEN
        symbol = "✅"
    elif status == "FAIL":
        color = Colors.RED
        symbol = "❌"
    elif status == "WARN":
        color = Colors.YELLOW
        symbol = "⚠️"
    elif status == "INFO":
        color = Colors.CYAN
        symbol = "ℹ️"
    else:
        color = Colors.BLUE
        symbol = "→"
    
    print(f"{color}{symbol} {msg}{Colors.END}")

# ============================================================================
# TEST
# ============================================================================

async def run_test():
    """Run the actual E2E test"""
    
    print(f"\n{Colors.BOLD}{'='*70}")
    print(f"🤖 KI AGENT E2E TEST - REAL EXECUTION")
    print(f"{'='*70}{Colors.END}\n")
    
    # Create workspace
    print_status("PHASE 1: Setup", "INFO")
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    print_status(f"Workspace: {WORKSPACE}", "PASS")
    
    # Connect to server
    print_status("PHASE 2: Connecting to WebSocket", "INFO")
    try:
        async with websockets.connect(BACKEND_URL, ping_interval=10) as ws:
            print_status(f"Connected to {BACKEND_URL}", "PASS")
            
            # Send init message
            print_status("PHASE 3: Sending initialization", "INFO")
            init_msg = {
                "type": "init",
                "workspace_path": str(WORKSPACE)
            }
            await ws.send(json.dumps(init_msg))
            print_status(f"Init message sent", "PASS")
            
            # Get init response
            try:
                init_response = await asyncio.wait_for(ws.recv(), timeout=5)
                print_status(f"Init response received: {init_response[:80]}", "PASS")
            except asyncio.TimeoutError:
                print_status("No init response (timeout)", "WARN")
            
            # Send app request
            print_status("PHASE 4: Sending app generation request", "INFO")
            request_msg = {
                "type": "chat",  # ✅ Correct type for handler
                "content": "Create a simple React Todo app with add, delete and mark complete functionality",
                "message_id": "msg_001"
            }
            await ws.send(json.dumps(request_msg))
            print_status("Request sent", "PASS")
            
            # Collect responses
            print_status("PHASE 5: Monitoring agent responses", "INFO")
            messages = []
            errors = []
            start_time = time.time()
            complete = False
            
            try:
                while time.time() - start_time < TIMEOUT:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=3)
                        data = json.loads(msg)
                        messages.append(data)
                        
                        msg_type = data.get("type", "unknown")
                        msg_time = datetime.now().strftime("%H:%M:%S")
                        
                        # Print interesting messages
                        if msg_type == "status":
                            print_status(f"[{msg_time}] Status: {data.get('status', '?')}", "INFO")
                        elif msg_type == "progress":
                            agent = data.get("agent", "?")
                            step = data.get("step", "?")
                            print_status(f"[{msg_time}] Progress: {agent} → {step}", "INFO")
                        elif msg_type == "error":
                            error_msg = data.get("error", "unknown")
                            print_status(f"[{msg_time}] ERROR: {error_msg}", "FAIL")
                            errors.append(error_msg)
                        elif msg_type == "complete":
                            print_status(f"[{msg_time}] WORKFLOW COMPLETE!", "PASS")
                            complete = True
                        elif msg_type == "output":
                            artifacts = data.get("artifacts", [])
                            print_status(f"[{msg_time}] Output: {len(artifacts)} artifacts", "INFO")
                        
                    except asyncio.TimeoutError:
                        print_status("Waiting for more responses...", "WARN")
                        await asyncio.sleep(1)
                        continue
                    except json.JSONDecodeError as e:
                        print_status(f"Malformed message: {e}", "WARN")
                        continue
                
            except Exception as e:
                print_status(f"Connection error: {e}", "FAIL")
                return False
            
            elapsed = time.time() - start_time
            
            # Validate results
            print(f"\n{Colors.BOLD}PHASE 6: Validation{Colors.END}\n")
            
            # Check message count
            if len(messages) >= 5:
                print_status(f"Messages received: {len(messages)}", "PASS")
            else:
                print_status(f"Messages received: {len(messages)} (expected ≥5)", "FAIL")
                return False
            
            # Check for errors
            if errors:
                print_status(f"Errors found: {errors}", "FAIL")
                return False
            else:
                print_status("No errors found", "PASS")
            
            # Check completion
            if complete:
                print_status("Workflow marked as complete", "PASS")
            else:
                print_status("Workflow not marked as complete", "WARN")
            
            # Check workspace
            files = list(WORKSPACE.rglob("*"))
            file_count = len([f for f in files if f.is_file()])
            
            if file_count > 0:
                print_status(f"Files generated: {file_count}", "PASS")
                # Show file types
                file_types = {}
                for f in files:
                    if f.is_file():
                        ext = f.suffix or "no_ext"
                        file_types[ext] = file_types.get(ext, 0) + 1
                for ext, count in sorted(file_types.items()):
                    print_status(f"  {ext}: {count} files", "INFO")
            else:
                print_status(f"No files generated", "FAIL")
                return False
            
            # Check duration
            if elapsed < TIMEOUT:
                print_status(f"Total time: {elapsed:.1f}s (timeout: {TIMEOUT}s)", "PASS")
            else:
                print_status(f"Timeout exceeded!", "FAIL")
                return False
            
            # Final summary
            print(f"\n{Colors.BOLD}PHASE 7: Summary{Colors.END}\n")
            print_status(f"✅ TEST PASSED!", "PASS")
            print_status(f"  - Workspace: {WORKSPACE}", "INFO")
            print_status(f"  - Duration: {elapsed:.1f}s", "INFO")
            print_status(f"  - Messages: {len(messages)}", "INFO")
            print_status(f"  - Files: {file_count}", "INFO")
            print_status(f"  - Errors: {len(errors)}", "INFO")
            
            return True
    
    except Exception as e:
        print_status(f"Fatal error: {e}", "FAIL")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print_status("Checking if server is running...", "INFO")
    
    # Check if server is accessible
    async def check_server():
        try:
            async with websockets.connect(BACKEND_URL, ping_interval=10) as ws:
                print_status("Server is reachable!", "PASS")
                await ws.send(json.dumps({"type": "ping"}))
                return True
        except Exception as e:
            print_status(f"Server not accessible: {e}", "FAIL")
            print_status("Please start the server first:", "INFO")
            print_status("  cd /Users/dominikfoert/git/KI_AutoAgent", "INFO")
            print_status("  source venv/bin/activate", "INFO")
            print_status("  python start_server.py", "INFO")
            return False
    
    # Try to connect
    try:
        if not asyncio.run(check_server()):
            sys.exit(1)
    except Exception as e:
        print_status(f"Setup failed: {e}", "FAIL")
        sys.exit(1)
    
    # Run the test
    try:
        success = asyncio.run(run_test())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_status("Test interrupted by user", "WARN")
        sys.exit(130)
    except Exception as e:
        print_status(f"Test failed: {e}", "FAIL")
        import traceback
        traceback.print_exc()
        sys.exit(1)