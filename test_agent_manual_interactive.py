#!/usr/bin/env python3
"""
🤖 MANUAL INTERACTIVE E2E TEST - KI Agent WebSocket

Start this script to interactively test the KI Agent:
1. It will connect to the backend via WebSocket
2. You can type requests
3. Monitor agent responses in real-time
4. Watch files being generated

USAGE:
    python test_agent_manual_interactive.py
"""

import asyncio
import json
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import websockets

# ============================================================
# CONFIGURATION
# ============================================================

# Isolated test workspace
TEST_WORKSPACE = Path.home() / "TestApps" / "manual_interactive_test" / datetime.now().strftime("%Y%m%d_%H%M%S")
BACKEND_URL = "ws://localhost:8002/ws/chat"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)

# Color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# ============================================================
# INTERACTIVE CLIENT
# ============================================================

class InteractiveAgent:
    """Interactive WebSocket client for agent"""
    
    def __init__(self, ws_url: str, workspace: Path):
        self.ws_url = ws_url
        self.workspace = workspace
        self.ws = None
        self.message_id = 0
        self.connected = False
    
    async def setup_workspace(self):
        """Setup clean workspace"""
        print(f"\n{Colors.BLUE}📁 Setting up workspace...{Colors.ENDC}")
        
        if self.workspace.exists():
            print(f"{Colors.YELLOW}🧹 Cleaning old workspace...{Colors.ENDC}")
            shutil.rmtree(self.workspace)
        
        self.workspace.mkdir(parents=True, exist_ok=True)
        print(f"{Colors.GREEN}✅ Workspace ready: {self.workspace}{Colors.ENDC}")
    
    async def connect(self):
        """Connect to backend"""
        print(f"\n{Colors.BLUE}🔗 Connecting to agent at {self.ws_url}...{Colors.ENDC}")
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                self.ws = await websockets.connect(self.ws_url)
                
                # Send initialization
                init_msg = {
                    "type": "init",
                    "workspace_path": str(self.workspace),
                    "timestamp": datetime.now().isoformat()
                }
                
                await self.ws.send(json.dumps(init_msg))
                
                # Wait for acknowledgment
                ack = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
                ack_data = json.loads(ack)
                
                if ack_data.get("success"):
                    self.connected = True
                    print(f"{Colors.GREEN}✅ Connected and initialized!{Colors.ENDC}\n")
                    return True
                else:
                    print(f"{Colors.RED}❌ Init failed: {ack_data}{Colors.ENDC}")
            
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"{Colors.YELLOW}⏳ Retry {attempt + 1}/{max_retries}...{Colors.ENDC}")
                    await asyncio.sleep(2)
                else:
                    print(f"{Colors.RED}❌ Connection failed: {e}{Colors.ENDC}")
                    print(f"\n{Colors.YELLOW}Is the backend running?{Colors.ENDC}")
                    print(f"Start it with: {Colors.BOLD}python start_server.py --port=8002{Colors.ENDC}\n")
                    raise
    
    async def send_request(self, request: str):
        """Send user request to agent"""
        if not self.connected:
            print(f"{Colors.RED}❌ Not connected!{Colors.ENDC}")
            return
        
        self.message_id += 1
        
        message = {
            "type": "message",
            "content": request,
            "id": self.message_id
        }
        
        print(f"\n{Colors.CYAN}📤 Sending request #{self.message_id}...{Colors.ENDC}")
        await self.ws.send(json.dumps(message))
    
    async def monitor_responses(self):
        """Monitor and display agent responses"""
        if not self.connected:
            return
        
        print(f"\n{Colors.CYAN}📨 Monitoring agent responses...{Colors.ENDC}")
        print(f"{Colors.BLUE}(Press Ctrl+C to stop){Colors.ENDC}\n")
        
        message_count = 0
        
        try:
            while True:
                try:
                    response = await asyncio.wait_for(
                        self.ws.recv(),
                        timeout=60.0
                    )
                    
                    data = json.loads(response)
                    message_count += 1
                    
                    # Display message
                    msg_type = data.get("type", "unknown")
                    content = data.get("content", "")
                    
                    self._display_message(msg_type, content)
                    
                    # Check for completion
                    if msg_type == "complete":
                        print(f"\n{Colors.GREEN}✅ Agent work completed!{Colors.ENDC}")
                        break
                
                except asyncio.TimeoutError:
                    print(f"\n{Colors.YELLOW}⏱️  No response for 60 seconds...{Colors.ENDC}")
                    break
        
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}⛔ Monitoring stopped{Colors.ENDC}")
        
        print(f"\n{Colors.BLUE}📊 Received {message_count} messages{Colors.ENDC}")
    
    def _display_message(self, msg_type: str, content: str):
        """Display a message with appropriate formatting"""
        
        if msg_type == "status":
            print(f"{Colors.BLUE}ℹ️  {content}{Colors.ENDC}")
        
        elif msg_type == "progress":
            print(f"{Colors.CYAN}⏳ {content}{Colors.ENDC}")
        
        elif msg_type == "output":
            print(f"{Colors.GREEN}✓ {content}{Colors.ENDC}")
        
        elif msg_type == "error":
            print(f"{Colors.RED}✗ ERROR: {content}{Colors.ENDC}")
        
        elif msg_type == "complete":
            print(f"{Colors.GREEN}✅ COMPLETE: {content}{Colors.ENDC}")
        
        else:
            # Truncate long content
            if len(content) > 200:
                content = content[:200] + "..."
            print(f"{Colors.BLUE}{msg_type.upper()}:{Colors.ENDC} {content}")
    
    async def check_generated_files(self):
        """Check and display generated files"""
        files = list(self.workspace.rglob("*"))
        
        if not files:
            print(f"\n{Colors.YELLOW}⚠️  No files generated yet{Colors.ENDC}")
            return
        
        # Count by type
        file_types = {}
        for f in files:
            if f.is_file():
                ext = f.suffix or "no_ext"
                file_types[ext] = file_types.get(ext, 0) + 1
        
        print(f"\n{Colors.CYAN}📁 Generated Files:{Colors.ENDC}")
        print(f"{Colors.BOLD}Total: {len(files)} files{Colors.ENDC}")
        
        for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {ext:15s}: {count:3d} files")
    
    async def close(self):
        """Close connection"""
        if self.ws:
            await self.ws.close()
            self.connected = False
            print(f"\n{Colors.BLUE}🔌 Disconnected{Colors.ENDC}")


# ============================================================
# PREDEFINED TEST SCENARIOS
# ============================================================

class TestScenarios:
    """Predefined test scenarios"""
    
    SCENARIOS = {
        "1": {
            "name": "Simple React Todo App",
            "request": """
Create a React Todo Application with:
- Input field to add new todos
- Display list of todos  
- Mark todos as complete/incomplete
- Delete todo functionality
- Local storage persistence
- Clean, responsive UI
            """.strip()
        },
        "2": {
            "name": "React Dashboard",
            "request": """
Create a React Dashboard with:
- Responsive grid layout
- Display cards with data
- Line chart showing trends
- Dark mode toggle
- User statistics section
- Export button
            """.strip()
        },
        "3": {
            "name": "Contact Form",
            "request": """
Create a React Contact Form with:
- Email, name, subject, message fields
- Form validation (required fields, valid email)
- Submit button
- Success/error messages
- Clear form functionality
- Responsive design
- Unit tests for validation
            """.strip()
        },
        "4": {
            "name": "Custom Request",
            "request": None  # Will ask user
        }
    }
    
    @classmethod
    def display_menu(cls):
        """Display scenario menu"""
        print(f"\n{Colors.BOLD}═══ Test Scenarios ═══{Colors.ENDC}")
        
        for key, scenario in cls.SCENARIOS.items():
            print(f"{Colors.CYAN}{key}{Colors.ENDC}. {scenario['name']}")
    
    @classmethod
    def get_request(cls, choice: str) -> str:
        """Get request for scenario"""
        if choice not in cls.SCENARIOS:
            return None
        
        scenario = cls.SCENARIOS[choice]
        request = scenario["request"]
        
        if request is None:
            # Custom request
            print(f"\n{Colors.BLUE}Enter your request (or paste multi-line, end with empty line):{Colors.ENDC}")
            lines = []
            while True:
                try:
                    line = input()
                    if not line:
                        break
                    lines.append(line)
                except EOFError:
                    break
            request = "\n".join(lines)
        
        return request


# ============================================================
# MAIN INTERACTIVE LOOP
# ============================================================

async def main():
    """Main interactive test loop"""
    
    # Print header
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("╔════════════════════════════════════════════════════════╗")
    print("║  🤖 KI AGENT - MANUAL INTERACTIVE E2E TEST            ║")
    print("║  WebSocket Integration Test                           ║")
    print("╚════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")
    
    # Setup
    agent = InteractiveAgent(BACKEND_URL, TEST_WORKSPACE)
    
    try:
        await agent.setup_workspace()
        await agent.connect()
        
        # Main loop
        while True:
            # Display menu
            TestScenarios.display_menu()
            
            choice = input(f"\n{Colors.CYAN}Select scenario (1-4) or 'q' to quit: {Colors.ENDC}").strip()
            
            if choice.lower() == 'q':
                break
            
            # Get request
            request = TestScenarios.get_request(choice)
            if not request:
                print(f"{Colors.RED}❌ Invalid choice{Colors.ENDC}")
                continue
            
            # Send request
            await agent.send_request(request)
            
            # Monitor responses
            await agent.monitor_responses()
            
            # Show generated files
            await agent.check_generated_files()
            
            # Ask to continue
            cont = input(f"\n{Colors.CYAN}Test another scenario? (y/n): {Colors.ENDC}").strip().lower()
            if cont != 'y':
                break
        
        print(f"\n{Colors.GREEN}✅ Interactive test completed!{Colors.ENDC}")
        print(f"{Colors.BLUE}📁 Workspace: {agent.workspace}{Colors.ENDC}\n")
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⛔ Test interrupted by user{Colors.ENDC}")
    
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
    
    finally:
        await agent.close()


# ============================================================
# STARTUP INSTRUCTIONS
# ============================================================

def print_startup_instructions():
    """Print how to start the backend"""
    print(f"\n{Colors.YELLOW}{Colors.BOLD}")
    print("┌─────────────────────────────────────────────────┐")
    print("│ BACKEND NOT RUNNING!                            │")
    print("├─────────────────────────────────────────────────┤")
    print("│ Start the backend in another terminal:          │")
    print("│                                                 │")
    print("│ cd /Users/dominikfoert/git/KI_AutoAgent         │")
    print("│ python start_server.py --port=8002              │")
    print("│                                                 │")
    print("│ Then run this script again.                     │")
    print("└─────────────────────────────────────────────────┘")
    print(f"{Colors.ENDC}\n")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ConnectionRefusedError:
        print_startup_instructions()
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Goodbye!{Colors.ENDC}\n")
        sys.exit(0)