#!/usr/bin/env python3
"""
WebSocket Test Client for KI_AutoAgent
Tests chat functionality and monitors all messages
"""

import asyncio
import json
import websockets
import sys
from datetime import datetime


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


async def test_chat():
    uri = "ws://localhost:8001/ws/chat"
    workspace_path = "/Users/dominikfoert/TestApps/CalculatorApp"

    print(f"\n{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}🧪 KI_AutoAgent Chat Test Client{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

    print(f"{Colors.CYAN}Connecting to: {uri}{Colors.ENDC}")
    print(f"{Colors.CYAN}Workspace: {workspace_path}{Colors.ENDC}\n")

    try:
        async with websockets.connect(uri) as websocket:
            # Step 1: Initial connection
            print(f"{Colors.GREEN}✅ Connected to WebSocket{Colors.ENDC}")

            # Receive connected message
            connected_msg = await websocket.recv()
            msg = json.loads(connected_msg)
            print(f"{Colors.BLUE}← Server: {msg}{Colors.ENDC}\n")

            # Step 2: Send init message
            init_msg = {
                "type": "init",
                "workspace_path": workspace_path
            }
            print(f"{Colors.YELLOW}→ Client: {init_msg}{Colors.ENDC}")
            await websocket.send(json.dumps(init_msg))

            # Receive initialized message
            init_response = await websocket.recv()
            msg = json.loads(init_response)
            print(f"{Colors.BLUE}← Server: {msg}{Colors.ENDC}\n")

            # Step 3: Send actual chat message
            chat_request = """Create a simple desktop calculator app.

Requirements:
- Python with tkinter for GUI
- Basic operations: +, -, *, /
- Modern, clean interface
- Keyboard shortcuts (Enter to calculate, Escape to clear)
- Error handling for invalid input
- Include comprehensive tests
- Generate complete, working code

Please show me your thinking process and what tools you're using!"""

            chat_msg = {
                "type": "chat",
                "content": chat_request,
                "mode": "chat"
            }

            print(f"{Colors.BOLD}{'='*80}{Colors.ENDC}")
            print(f"{Colors.HEADER}📝 Sending Chat Request:{Colors.ENDC}")
            print(f"{Colors.BOLD}{'='*80}{Colors.ENDC}")
            print(f"{chat_request}\n")
            print(f"{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

            await websocket.send(json.dumps(chat_msg))

            # Step 4: Receive all responses
            print(f"{Colors.HEADER}📨 Receiving Responses:{Colors.ENDC}\n")

            message_count = 0
            thinking_count = 0
            tool_use_count = 0
            agent_messages = {}

            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=180.0)
                    msg = json.loads(response)
                    message_count += 1

                    msg_type = msg.get("type", "unknown")

                    # Color code by message type
                    if msg_type == "thinking":
                        thinking_count += 1
                        print(f"{Colors.CYAN}💭 [THINKING #{thinking_count}]{Colors.ENDC}")
                        print(f"   Agent: {msg.get('agent', 'unknown')}")
                        print(f"   Content: {msg.get('content', '')[:200]}...\n")

                    elif msg_type == "tool_use":
                        tool_use_count += 1
                        print(f"{Colors.YELLOW}🔧 [TOOL USE #{tool_use_count}]{Colors.ENDC}")
                        print(f"   Agent: {msg.get('agent', 'unknown')}")
                        print(f"   Tool: {msg.get('tool_name', 'unknown')}")
                        print(f"   Input: {str(msg.get('tool_input', {}))[:200]}...\n")

                    elif msg_type == "agent_message":
                        agent = msg.get('agent', 'unknown')
                        if agent not in agent_messages:
                            agent_messages[agent] = 0
                        agent_messages[agent] += 1
                        print(f"{Colors.GREEN}🤖 [AGENT: {agent}]{Colors.ENDC}")
                        print(f"   Content: {msg.get('content', '')[:300]}...\n")

                    elif msg_type == "result":
                        print(f"{Colors.BOLD}{Colors.GREEN}✅ [FINAL RESULT]{Colors.ENDC}")
                        print(f"{msg.get('content', '')}\n")

                    elif msg_type == "error":
                        print(f"{Colors.RED}❌ [ERROR]{Colors.ENDC}")
                        print(f"   {msg.get('content', msg.get('error', 'Unknown error'))}\n")
                        break

                    elif msg_type == "complete":
                        print(f"{Colors.BOLD}{Colors.GREEN}✅ [WORKFLOW COMPLETE]{Colors.ENDC}\n")
                        break

                    else:
                        print(f"{Colors.BLUE}📩 [MSG #{message_count}] Type: {msg_type}{Colors.ENDC}")
                        print(f"   {json.dumps(msg, indent=2)[:300]}...\n")

                except asyncio.TimeoutError:
                    print(f"{Colors.YELLOW}⏱️  Timeout waiting for response (180s){Colors.ENDC}")
                    break
                except json.JSONDecodeError as e:
                    print(f"{Colors.RED}❌ JSON decode error: {e}{Colors.ENDC}")
                    continue

            # Summary
            print(f"\n{Colors.BOLD}{'='*80}{Colors.ENDC}")
            print(f"{Colors.HEADER}📊 Test Summary:{Colors.ENDC}")
            print(f"{Colors.BOLD}{'='*80}{Colors.ENDC}")
            print(f"Total Messages: {message_count}")
            print(f"Thinking Messages: {thinking_count}")
            print(f"Tool Use Messages: {tool_use_count}")
            print(f"Agents Involved: {len(agent_messages)}")
            for agent, count in agent_messages.items():
                print(f"  - {agent}: {count} messages")
            print(f"{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

    except websockets.exceptions.WebSocketException as e:
        print(f"{Colors.RED}❌ WebSocket error: {e}{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print(f"\n{Colors.CYAN}Starting WebSocket test...{Colors.ENDC}")
    asyncio.run(test_chat())
    print(f"{Colors.GREEN}✅ Test completed!{Colors.ENDC}\n")
