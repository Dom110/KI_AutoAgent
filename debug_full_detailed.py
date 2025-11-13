#!/usr/bin/env python3
"""
🔍 COMPLETE DEBUGGING - Show ALL events with full details
"""

import subprocess
import sys
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime

try:
    import websockets
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "websockets", "-q"], check=True)
    import websockets


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    WHITE = "\033[37m"


async def run_debug():
    """Main debug workflow"""
    
    print("\n" + "=" * 100)
    print(Colors.BOLD + Colors.MAGENTA + "🔍 KI AUTOAGENT v7.0 - FULL DEBUG WORKFLOW" + Colors.RESET)
    print("=" * 100 + "\n")
    
    print("⏳ Waiting for server startup...")
    await asyncio.sleep(6)  # Give server more time to start
    
    try:
        async with websockets.connect("ws://127.0.0.1:8002/ws/chat") as ws:
            print(Colors.GREEN + "✅ Connected!" + Colors.RESET + "\n")
            
            # === WELCOME ===
            print(Colors.BOLD + "📥 WELCOME MESSAGE" + Colors.RESET)
            msg = json.loads(await ws.recv())
            print(f"   Type: {msg.get('type')}")
            print(f"   Version: {msg.get('version')}")
            print(f"   Release: {msg.get('release_tag')}")
            print(f"   Session: {msg.get('session_id')}")
            print()
            
            # === INIT ===
            print(Colors.BOLD + "📁 INITIALIZING WORKSPACE" + Colors.RESET)
            workspace = "/tmp/ki_autoagent_full_debug"
            Path(workspace).mkdir(parents=True, exist_ok=True)
            
            await ws.send(json.dumps({
                "type": "init",
                "workspace_path": workspace
            }))
            
            msg = json.loads(await ws.recv())
            print(f"   Status: {msg.get('type')}")
            print(f"   Message: {msg.get('message', '')[:100]}")
            print()
            
            # === REQUEST ===
            print(Colors.BOLD + "📝 SENDING REQUEST" + Colors.RESET)
            request = "Create a simple React counter app with tests"
            print(f"   Request: {request}")
            
            await ws.send(json.dumps({
                "type": "chat",
                "content": request
            }))
            print()
            
            # === EVENTS ===
            print(Colors.BOLD + "🎬 WORKFLOW EVENTS" + Colors.RESET)
            print("-" * 100)
            
            event_count = 0
            start_time = time.time()
            events_by_type = {}
            agent_sequence = []
            
            try:
                while time.time() - start_time < 120:  # 2 minutes timeout
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=3)
                        event = json.loads(msg)
                    except asyncio.TimeoutError:
                        continue
                    
                    event_count += 1
                    event_type = event.get("type", "unknown")
                    events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
                    
                    # Format output
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    elapsed = time.time() - start_time
                    
                    print(f"\n[{event_count:3d}] {timestamp} (+{elapsed:6.2f}s) {Colors.CYAN}{event_type.upper()}{Colors.RESET}")
                    
                    # Print key fields based on event type
                    if event_type == "supervisor_event":
                        next_agent = event.get("next_agent")
                        reasoning = event.get("reasoning", "")
                        print(f"      → Next Agent: {Colors.MAGENTA}{next_agent}{Colors.RESET}")
                        if reasoning:
                            print(f"      → Reasoning: {reasoning[:150]}")
                        if next_agent and next_agent not in ["END"]:
                            agent_sequence.append(next_agent)
                    
                    elif event_type == "agent_event":
                        agent = event.get("agent")
                        msg_text = event.get("message", "")
                        print(f"      → Agent: {Colors.BLUE}{agent}{Colors.RESET}")
                        if msg_text:
                            print(f"      → Message: {msg_text[:150]}")
                    
                    elif event_type == "mcp_progress":
                        server = event.get("server")
                        msg_text = event.get("message", "")
                        progress = event.get("progress", {})
                        print(f"      → Server: {server}")
                        print(f"      → Message: {msg_text[:150]}")
                        if progress:
                            print(f"      → Progress: {progress}")
                    
                    elif event_type == "progress":
                        node = event.get("node")
                        msg_text = event.get("message", "")
                        print(f"      → Node: {node}")
                        print(f"      → Message: {msg_text[:150]}")
                    
                    elif event_type == "status":
                        status = event.get("status")
                        msg_text = event.get("message", "")
                        print(f"      → Status: {status}")
                        print(f"      → Message: {msg_text[:100]}")
                    
                    elif event_type == "workflow_complete":
                        print(f"      {Colors.GREEN}✅ Workflow completed!{Colors.RESET}")
                        break
                    
                    elif event_type == "error":
                        error = event.get("error", "Unknown error")
                        print(f"      {Colors.RED}❌ Error: {error}{Colors.RESET}")
                        break
                    
                    else:
                        # Print all keys for unknown events
                        for key, value in event.items():
                            if isinstance(value, str) and len(value) > 100:
                                print(f"      → {key}: {value[:100]}...")
                            elif not isinstance(value, (dict, list)):
                                print(f"      → {key}: {value}")
                    
            except Exception as e:
                print(f"{Colors.RED}Error receiving events: {e}{Colors.RESET}")
            
            print("\n" + "-" * 100)
            
            # === SUMMARY ===
            print(Colors.BOLD + "\n📊 SUMMARY" + Colors.RESET)
            print(f"   Total Events: {event_count}")
            print(f"   Duration: {time.time() - start_time:.2f}s")
            print(f"\n   Events by Type:")
            for event_type, count in sorted(events_by_type.items(), key=lambda x: x[1], reverse=True):
                print(f"      {event_type.ljust(20)}: {count:3d}")
            
            if agent_sequence:
                print(f"\n   Agent Sequence:")
                for i, agent in enumerate(agent_sequence, 1):
                    print(f"      {i}. {agent}")
            
            print()
            
    except Exception as e:
        print(f"{Colors.RED}❌ Connection error: {e}{Colors.RESET}")
        return False
    
    return True


def main():
    """Start server and run debug"""
    
    print("🚀 Starting server...")
    
    server_proc = subprocess.Popen(
        ["./venv/bin/python", "backend/api/server_v7_mcp.py"],
        cwd="/Users/dominikfoert/git/KI_AutoAgent",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        success = asyncio.run(run_debug())
        print(f"\n{'✅ Success!' if success else '❌ Failed!'}")
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Interrupted by user{Colors.RESET}")
    finally:
        print("\n🛑 Stopping server...")
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_proc.kill()
        print("Done")


if __name__ == "__main__":
    main()