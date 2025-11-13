#!/usr/bin/env python3
"""
🔍 COMPLETE KI AutoAgent v7.0 WORKFLOW DEBUGGER
================================================================================
WebSocket Client für vollständiges Debugging aller Agenten.

Beobachtet:
- Supervisor Decisions
- Agent Input/Output
- Tool Ausführung
- ReviewFix Validierung
- HITL Anfragen
- Fehler

Zeigt ALLES was passiert im System!

Verwendung:
    python debug_full_workflow.py
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
except ImportError:
    print("❌ websockets nicht installiert!")
    print("   pip install websockets")
    sys.exit(1)


# ============================================================================
# COLORS FOR TERMINAL OUTPUT
# ============================================================================

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Foreground
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Background
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"


# ============================================================================
# LOGGER CLASS
# ============================================================================

class WorkflowLogger:
    """Structured logging for workflow debugging."""

    def __init__(self):
        self.events = []
        self.start_time = datetime.now()

    def log(self, level: str, message: str, **kwargs):
        """Log with timestamp."""
        timestamp = (datetime.now() - self.start_time).total_seconds()
        event = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            **kwargs
        }
        self.events.append(event)

        # Print to console
        symbols = {
            "info": "ℹ️ ",
            "debug": "🔍",
            "success": "✅",
            "warning": "⚠️ ",
            "error": "❌",
            "supervisor": "🎯",
            "research": "📚",
            "architect": "📐",
            "codesmith": "💻",
            "reviewfix": "✅",
            "responder": "💬",
            "tool": "🔧",
            "progress": "➡️ ",
        }

        symbol = symbols.get(level, "•")
        color = {
            "info": Colors.CYAN,
            "debug": Colors.DIM,
            "success": Colors.GREEN,
            "warning": Colors.YELLOW,
            "error": Colors.RED + Colors.BOLD,
            "supervisor": Colors.MAGENTA + Colors.BOLD,
            "research": Colors.BLUE,
            "architect": Colors.MAGENTA,
            "codesmith": Colors.CYAN,
            "reviewfix": Colors.GREEN,
            "responder": Colors.YELLOW,
            "tool": Colors.BLUE,
            "progress": Colors.WHITE + Colors.DIM,
        }.get(level, Colors.WHITE)

        print(f"{color}{symbol} [{timestamp:6.2f}s] {message}{Colors.RESET}")

        # Print additional data if present
        if "data" in kwargs:
            data = kwargs["data"]
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, str) and len(v) > 100:
                        print(f"    {k}: {v[:100]}...")
                    else:
                        print(f"    {k}: {v}")

    def info(self, msg, **kwargs):
        self.log("info", msg, **kwargs)

    def debug(self, msg, **kwargs):
        self.log("debug", msg, **kwargs)

    def success(self, msg, **kwargs):
        self.log("success", msg, **kwargs)

    def warning(self, msg, **kwargs):
        self.log("warning", msg, **kwargs)

    def error(self, msg, **kwargs):
        self.log("error", msg, **kwargs)

    def agent(self, agent_name: str, msg: str, **kwargs):
        levels = {
            "supervisor": "supervisor",
            "research": "research",
            "architect": "architect",
            "codesmith": "codesmith",
            "reviewfix": "reviewfix",
            "responder": "responder",
        }
        level = levels.get(agent_name, "info")
        self.log(level, f"{agent_name.upper()}: {msg}", **kwargs)

    def tool(self, tool_name: str, msg: str, **kwargs):
        self.log("tool", f"{tool_name}: {msg}", **kwargs)

    def progress(self, msg: str, **kwargs):
        self.log("progress", msg, **kwargs)

    def summary(self):
        """Print event summary."""
        print("\n" + "=" * 80)
        print(Colors.BOLD + "📊 WORKFLOW EVENT SUMMARY" + Colors.RESET)
        print("=" * 80)

        # Count event types
        event_types = {}
        for event in self.events:
            level = event["level"]
            event_types[level] = event_types.get(level, 0) + 1

        for level, count in sorted(event_types.items()):
            print(f"  {level.ljust(15)}: {count} events")

        print(f"\n  Total duration: {(datetime.now() - self.start_time).total_seconds():.2f}s")
        print()


logger = WorkflowLogger()


# ============================================================================
# WEBSOCKET CLIENT
# ============================================================================

class WorkflowDebugClient:
    """WebSocket client for debugging KI AutoAgent workflow."""

    def __init__(self, uri: str = "ws://localhost:8002/ws/chat"):
        self.uri = uri
        self.websocket = None
        self.session_id = None
        self.client_id = None

    async def connect(self) -> bool:
        """Connect to WebSocket server."""
        try:
            logger.info(f"🔌 Connecting to {self.uri}...")
            self.websocket = await websockets.connect(self.uri)
            logger.success("Connected to KI AutoAgent!")

            # Receive welcome message
            welcome = await self.websocket.recv()
            msg = json.loads(welcome)
            logger.debug("Welcome received", data=msg)

            self.session_id = msg.get("session_id")
            self.client_id = msg.get("client_id")

            logger.info(f"Session ID: {self.session_id}")
            logger.info(f"Client ID: {self.client_id}")

            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False

    async def initialize(self, workspace_path: str) -> bool:
        """Initialize session with workspace."""
        try:
            logger.info(f"📁 Initializing workspace: {workspace_path}")

            init_msg = {
                "type": "init",
                "workspace_path": workspace_path
            }
            await self.websocket.send(json.dumps(init_msg))

            # Receive initialization response
            response = await self.websocket.recv()
            msg = json.loads(response)
            logger.debug("Init response", data=msg)

            if msg.get("type") == "initialized":
                logger.success("Workspace initialized!")
                return True
            else:
                logger.error(f"Unexpected response: {msg}")
                return False
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False

    async def send_request(self, user_query: str) -> bool:
        """Send task request to workflow."""
        try:
            logger.info(f"📝 Sending request: {user_query}")

            request = {
                "type": "chat",
                "content": user_query
            }
            await self.websocket.send(json.dumps(request))
            logger.debug("Request sent")

            return True
        except Exception as e:
            logger.error(f"Failed to send request: {e}")
            return False

    async def receive_events(self) -> None:
        """Receive and process workflow events."""
        event_count = 0
        while True:
            try:
                message = await asyncio.wait_for(self.websocket.recv(), timeout=300)
                event = json.loads(message)
                event_count += 1

                event_type = event.get("type")
                logger.debug(f"Event #{event_count}: {event_type}")

                # Process different event types
                if event_type == "connected":
                    self._handle_connected(event)

                elif event_type == "initialized":
                    self._handle_initialized(event)

                elif event_type == "status":
                    self._handle_status(event)

                elif event_type == "progress":
                    self._handle_progress(event)

                elif event_type == "mcp_progress":
                    self._handle_mcp_progress(event)

                elif event_type == "supervisor_decision":
                    self._handle_supervisor_decision(event)

                elif event_type == "supervisor_event":
                    self._handle_supervisor_event(event)

                elif event_type == "agent_event":
                    self._handle_agent_event(event)

                elif event_type == "agent_start":
                    self._handle_agent_start(event)

                elif event_type == "agent_complete":
                    self._handle_agent_complete(event)

                elif event_type == "agent_input":
                    self._handle_agent_input(event)

                elif event_type == "agent_output":
                    self._handle_agent_output(event)

                elif event_type == "agent_tool_call":
                    self._handle_tool_call(event)

                elif event_type == "agent_think":
                    self._handle_think(event)

                elif event_type == "hitl_request":
                    self._handle_hitl_request(event)

                elif event_type == "research_request":
                    self._handle_research_request(event)

                elif event_type == "log":
                    self._handle_log(event)

                elif event_type == "workflow_complete":
                    self._handle_workflow_complete(event)
                    break

                elif event_type == "error":
                    self._handle_error(event)
                    break

                else:
                    logger.debug(f"Unknown event type: {event_type}", data=event)

            except asyncio.TimeoutError:
                logger.warning("⏰ No events received for 300 seconds - timeout")
                break
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {e}")
            except websockets.exceptions.ConnectionClosed:
                logger.warning("🔌 Connection closed by server")
                break

        logger.success(f"✅ Received {event_count} total events")

    # ========================================================================
    # EVENT HANDLERS
    # ========================================================================

    def _handle_connected(self, event: dict):
        logger.progress("Connected to KI AutoAgent", data=event)

    def _handle_initialized(self, event: dict):
        logger.success("✅ Workspace initialized")

    def _handle_status(self, event: dict):
        status = event.get("status")
        message = event.get("message", "")
        logger.progress(f"Status: {status} - {message}")

    def _handle_progress(self, event: dict):
        node = event.get("node", "unknown")
        message = event.get("message", "")
        logger.progress(f"Node: {node} - {message}")

    def _handle_mcp_progress(self, event: dict):
        server = event.get("server", "unknown")
        message = event.get("message", "")
        logger.progress(f"MCP Server {server}: {message}")

    def _handle_supervisor_decision(self, event: dict):
        next_agent = event.get("next_agent")
        confidence = event.get("confidence", 0)
        reasoning = event.get("reasoning", "")

        logger.agent("supervisor", f"Decision: Route to {next_agent} (confidence: {confidence:.2f})")
        if reasoning:
            logger.debug(f"Reasoning: {reasoning[:200]}")

    def _handle_supervisor_event(self, event: dict):
        logger.agent("supervisor", "Event received", data=event)

    def _handle_agent_event(self, event: dict):
        agent = event.get("agent", "unknown")
        message = event.get("message", "")
        logger.agent(agent, message, data=event)

    def _handle_agent_start(self, event: dict):
        agent = event.get("agent", "unknown")
        instructions = event.get("instructions", "")
        logger.agent(agent, f"Started", data={"instructions": instructions[:150]})

    def _handle_agent_complete(self, event: dict):
        agent = event.get("agent", "unknown")
        success = event.get("success", True)
        status = "✅ Success" if success else "❌ Failed"
        logger.agent(agent, f"Complete - {status}")

    def _handle_agent_input(self, event: dict):
        agent = event.get("agent", "unknown")
        input_data = event.get("input", {})
        logger.agent(agent, f"Input received", data=input_data)

    def _handle_agent_output(self, event: dict):
        agent = event.get("agent", "unknown")
        output = event.get("output", {})
        logger.agent(agent, f"Output generated", data=output)

    def _handle_tool_call(self, event: dict):
        agent = event.get("agent", "unknown")
        tool = event.get("tool", "unknown")
        args = event.get("arguments", {})
        logger.tool(f"{agent}/{tool}", f"Calling with args", data=args)

    def _handle_think(self, event: dict):
        agent = event.get("agent", "unknown")
        thinking = event.get("thinking", "")
        logger.agent(agent, f"Thinking: {thinking[:200]}")

    def _handle_hitl_request(self, event: dict):
        req_type = event.get("request_type")
        message = event.get("message", "")
        logger.warning(f"👤 HITL Required - {req_type}: {message}")
        logger.debug("HITL Details", data=event)

    def _handle_research_request(self, event: dict):
        agent = event.get("requesting_agent", "unknown")
        request = event.get("request", "")
        logger.agent("research", f"Requested by {agent}: {request[:150]}")

    def _handle_log(self, event: dict):
        message = event.get("message", "")
        logger.info(f"Server: {message}")

    def _handle_workflow_complete(self, event: dict):
        logger.success("🎉 WORKFLOW COMPLETE!")
        logger.debug("Final event", data=event)

    def _handle_error(self, event: dict):
        error = event.get("error", "Unknown error")
        logger.error(f"Workflow error: {error}")

    async def close(self):
        """Close WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
            logger.info("Connection closed")


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Run the workflow debugger."""

    print("\n" + "=" * 80)
    print(Colors.BOLD + Colors.MAGENTA + "🔍 KI AUTOAGENT v7.0 - COMPLETE WORKFLOW DEBUGGER" + Colors.RESET)
    print("=" * 80)

    # Create client
    client = WorkflowDebugClient()

    # Connect
    if not await client.connect():
        logger.error("Failed to connect to server")
        return

    # Initialize workspace
    workspace = "/tmp/ki_autoagent_debug_workspace"
    Path(workspace).mkdir(parents=True, exist_ok=True)

    if not await client.initialize(workspace):
        logger.error("Failed to initialize workspace")
        return

    # Send request
    request = "Create a simple React counter app with increment and decrement buttons. Include tests."
    if not await client.send_request(request):
        logger.error("Failed to send request")
        return

    # Receive events
    logger.info("👀 Listening for workflow events...")
    print("-" * 80)
    await client.receive_events()
    print("-" * 80)

    # Close connection
    await client.close()

    # Print summary
    logger.summary()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)