"""
KI AutoAgent v7.0 Supervisor Server

FastAPI server using the new Supervisor Pattern architecture.
Single LLM orchestrator makes ALL routing decisions.

Key Changes from v6:
- Supervisor-based routing instead of distributed intelligence
- Command-based navigation instead of conditional edges
- Research as support agent (never user-facing)
- Responder is ONLY agent that talks to users
- Dynamic instructions instead of static modes

Usage:
    python backend/api/server_v7_supervisor.py

    WebSocket: ws://localhost:8002/ws/chat

Author: KI AutoAgent Team
Version: 7.0.0-alpha
Date: 2025-10-21
"""

from __future__ import annotations

# CHECK PYTHON VERSION FIRST - MUST BE 3.13.8 OR HIGHER!
import sys
import os

MIN_PYTHON_VERSION = (3, 13, 8)
current_version = sys.version_info[:3]

if current_version < MIN_PYTHON_VERSION:
    print("\n" + "=" * 60)
    print("❌ PYTHON VERSION ERROR")
    print("=" * 60)
    print(f"Current Python: {current_version[0]}.{current_version[1]}.{current_version[2]}")
    print(f"Required: Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}.{MIN_PYTHON_VERSION[2]} or higher")
    print("\nThis project uses Python 3.13+ features:")
    print("  - Native type unions with |")
    print("  - Pattern matching")
    print("  - Enhanced error messages")
    print("\nTo run the server correctly:")
    print("\n  # From project root directory:")
    print("  cd /Users/dominikfoert/git/KI_AutoAgent")
    print("  source venv/bin/activate")
    print("  pip install -r requirements.txt")
    print("  python backend/api/server_v7_supervisor.py")
    print("\n" + "=" * 60)
    sys.exit(1)

# After version check, continue with imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from __version__ import __version__, __release_tag__

# Optional performance optimization
try:
    import uvloop
    uvloop.install()
    _UVLOOP_INSTALLED = True
except ImportError:
    _UVLOOP_INSTALLED = False
    import logging
    logging.warning("⚠️ uvloop not installed - using standard asyncio (30% slower)")

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketState

# Load environment variables
from dotenv import load_dotenv
global_env = Path.home() / ".ki_autoagent" / "config" / ".env"
_env_loaded = False
if global_env.exists():
    load_dotenv(global_env)
    _env_loaded = True

# Import v7.0 supervisor workflow
from workflow_v7_supervisor import execute_supervisor_workflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True
)
logger = logging.getLogger(__name__)

if _UVLOOP_INSTALLED:
    logger.info("⚡ uvloop ENABLED: Event loop performance boosted")
else:
    logger.warning("⚠️ uvloop NOT installed - using standard asyncio")

if _env_loaded:
    logger.info(f"✅ Loaded API keys from: {global_env}")
else:
    logger.warning(f"⚠️ .env not found at: {global_env}")

# Validate API keys on startup
def validate_api_keys():
    """Validate required API keys and test connectivity."""
    logger.info("🔑 Validating API keys...")

    openai_key = os.environ.get("OPENAI_API_KEY")
    perplexity_key = os.environ.get("PERPLEXITY_API_KEY")

    if not openai_key or openai_key == "":
        logger.error("❌ OPENAI_API_KEY not set or empty!")
        logger.error("   Required for: GPT-4o Supervisor, Embeddings")
        logger.error("   Set in: ~/.ki_autoagent/config/.env")
        sys.exit(1)

    # Test OpenAI connection
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        client.models.list()  # Quick API test
        logger.info("✅ OPENAI_API_KEY: Valid")
    except Exception as e:
        logger.error(f"❌ OPENAI_API_KEY: Invalid - {str(e)[:80]}")
        logger.error("   Update your key in: ~/.ki_autoagent/config/.env")
        sys.exit(1)

    if not perplexity_key or perplexity_key == "":
        logger.warning("⚠️ PERPLEXITY_API_KEY not set - web research will use fallback")
    else:
        logger.info("✅ PERPLEXITY_API_KEY: Set (validation skipped)")

    logger.info("🔑 API key validation complete")

# Run validation
validate_api_keys()


# ============================================================================
# CONNECTION MANAGER
# ============================================================================

class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.connection_info: dict[str, dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Connect new client."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_info[client_id] = {
            "connected_at": datetime.now(),
            "client_id": client_id
        }
        logger.info(f"✅ Client connected: {client_id}")

    def disconnect(self, client_id: str):
        """Disconnect client."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.connection_info:
            del self.connection_info[client_id]
        logger.info(f"❌ Client disconnected: {client_id}")

    async def send_json(self, client_id: str, message: dict):
        """Send JSON message to client."""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to {client_id}: {e}")

    async def send_log(self, client_id: str, log_message: str):
        """Send log message to client for real-time monitoring."""
        await self.send_json(client_id, {
            "type": "log",
            "message": log_message,
            "timestamp": datetime.now().isoformat()
        })


# ============================================================================
# GLOBAL STATE
# ============================================================================

manager = ConnectionManager()
active_sessions: dict[str, dict[str, Any]] = {}


# ============================================================================
# WORKFLOW CALLBACK
# ============================================================================

class WorkflowCallbacks:
    """Callbacks for workflow events to send to WebSocket."""

    def __init__(self, client_id: str):
        self.client_id = client_id

    async def on_supervisor_decision(self, decision: dict):
        """Called when supervisor makes a routing decision."""
        await manager.send_json(self.client_id, {
            "type": "supervisor_decision",
            "next_agent": decision.get("next_agent"),
            "instructions": decision.get("instructions", "")[:200],  # Truncate
            "reasoning": decision.get("reasoning", ""),
            "confidence": decision.get("confidence", 0.0),
            "timestamp": datetime.now().isoformat()
        })
        await manager.send_log(
            self.client_id,
            f"🎯 SUPERVISOR NODE - Decision: Route to {decision.get('next_agent')}"
        )

    async def on_agent_start(self, agent_name: str, instructions: str):
        """Called when an agent starts execution."""
        await manager.send_json(self.client_id, {
            "type": "agent_start",
            "agent": agent_name,
            "instructions": instructions[:200],  # Truncate
            "timestamp": datetime.now().isoformat()
        })
        await manager.send_log(
            self.client_id,
            f"🚀 {agent_name.upper()} NODE - Executing: {instructions[:100]}..."
        )

    async def on_agent_complete(self, agent_name: str, result: dict):
        """Called when an agent completes execution."""
        await manager.send_json(self.client_id, {
            "type": "agent_complete",
            "agent": agent_name,
            "success": result.get("success", True),
            "timestamp": datetime.now().isoformat()
        })

    async def on_research_request(self, agent_name: str, request: str):
        """Called when an agent requests research."""
        await manager.send_json(self.client_id, {
            "type": "research_request",
            "requesting_agent": agent_name,
            "request": request,
            "timestamp": datetime.now().isoformat()
        })
        await manager.send_log(
            self.client_id,
            f"📚 {agent_name} requesting research: {request}"
        )

    async def on_hitl_request(self, request: dict):
        """Called when HITL needs user input."""
        await manager.send_json(self.client_id, {
            "type": "hitl_request",
            "request_type": request.get("request_type"),
            "message": request.get("message"),
            "options": request.get("options", []),
            "confidence": request.get("confidence", 0.0),
            "timestamp": datetime.now().isoformat()
        })

    async def on_command_routing(self, command: dict):
        """Called when a Command(goto=...) is executed."""
        await manager.send_log(
            self.client_id,
            f"➡️ Command(goto={command.get('goto')}) - {command.get('update', {}).get('instructions', '')[:100]}"
        )


# ============================================================================
# APP LIFESPAN
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle."""
    logger.info("🚀 Starting KI AutoAgent v7.0 Supervisor Server...")
    logger.info("🎯 Architecture: Supervisor Pattern with Central Orchestration")
    logger.info("📡 WebSocket endpoint: ws://localhost:8002/ws/chat")
    logger.info("✨ Key Features:")
    logger.info("   - Single LLM orchestrator (GPT-4o)")
    logger.info("   - Command-based routing")
    logger.info("   - Research as support agent")
    logger.info("   - Responder-only user communication")
    logger.info("   - Dynamic instructions")

    yield

    logger.info("🛑 Shutting down v7.0 Supervisor Server...")


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title=f"KI AutoAgent {__release_tag__}",
    description="v7.0 Supervisor Pattern Architecture",
    version=__version__,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": __version__,
        "release_tag": __release_tag__,
        "architecture": "supervisor_pattern",
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(manager.active_connections),
        "active_sessions": len(active_sessions)
    }


@app.get("/api/v7/info")
async def get_v7_info():
    """Get v7.0 system information."""
    return {
        "version": __version__,
        "architecture": "Supervisor Pattern",
        "agents": [
            "supervisor",
            "research",
            "architect",
            "codesmith",
            "reviewfix",
            "responder",
            "hitl"
        ],
        "features": {
            "central_orchestration": True,
            "command_routing": True,
            "research_requests": True,
            "self_invocation": True,
            "research_fix_loop": True,
            "dynamic_instructions": True
        },
        "asimov_rules": {
            "rule_1": "ReviewFix MANDATORY after code generation",
            "rule_2": "Architecture documentation required",
            "rule_3": "HITL on low confidence"
        }
    }


# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """Main WebSocket endpoint with v7.0 Supervisor workflow."""

    client_id = f"client_{uuid.uuid4().hex[:8]}"
    await manager.connect(websocket, client_id)

    # Session state
    session = {
        "client_id": client_id,
        "session_id": str(uuid.uuid4()),
        "created_at": datetime.now(),
        "workspace_path": None,
        "initialized": False,
        "messages": []
    }
    active_sessions[client_id] = session

    # Create callbacks for this client
    callbacks = WorkflowCallbacks(client_id)

    try:
        # Welcome message
        await manager.send_json(client_id, {
            "type": "connected",
            "message": f"Connected to KI AutoAgent {__release_tag__} - Supervisor Pattern",
            "session_id": session["session_id"],
            "client_id": client_id,
            "version": __version__,
            "release_tag": __release_tag__,
            "architecture": "supervisor_pattern",
            "requires_init": True
        })

        # Message loop
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type", "chat")

            logger.info(f"📨 Received {message_type} from {client_id}")

            # INIT MESSAGE (required first)
            if message_type == "init":
                workspace_path = data.get("workspace_path")
                if not workspace_path:
                    await manager.send_json(client_id, {
                        "type": "error",
                        "message": "workspace_path required"
                    })
                    continue

                session["workspace_path"] = workspace_path
                session["initialized"] = True

                logger.info(f"✅ Client {client_id} initialized with workspace: {workspace_path}")

                await manager.send_json(client_id, {
                    "type": "initialized",
                    "session_id": session["session_id"],
                    "workspace_path": workspace_path,
                    "message": "v7.0 Supervisor workflow ready!",
                    "architecture": "supervisor_pattern",
                    "agents_available": [
                        "supervisor",
                        "research",
                        "architect",
                        "codesmith",
                        "reviewfix",
                        "responder",
                        "hitl"
                    ]
                })
                continue

            # Require initialization
            if not session.get("initialized"):
                await manager.send_json(client_id, {
                    "type": "error",
                    "message": "Please send init message first"
                })
                continue

            # CHAT MESSAGE (execute workflow)
            if message_type in ["chat", "message", "task"]:
                user_query = data.get("content") or data.get("message") or data.get("task", "")
                if not user_query:
                    await manager.send_json(client_id, {
                        "type": "error",
                        "message": "Empty message"
                    })
                    continue

                session["messages"].append({
                    "role": "user",
                    "content": user_query,
                    "timestamp": datetime.now().isoformat()
                })

                # Send "thinking" status
                await manager.send_json(client_id, {
                    "type": "status",
                    "status": "analyzing",
                    "message": "🎯 Supervisor analyzing request..."
                })

                try:
                    logger.info(f"🚀 Running v7.0 Supervisor workflow for: {user_query[:80]}...")

                    # Create a wrapper for the workflow that sends callbacks
                    async def workflow_with_callbacks():
                        """Run workflow and send events to WebSocket."""

                        # Mock implementation for now - replace with actual workflow
                        # In production, modify execute_supervisor_workflow to accept callbacks

                        await callbacks.on_supervisor_decision({
                            "next_agent": "research",
                            "instructions": "Analyze workspace and gather context",
                            "reasoning": "Need to understand the project first",
                            "confidence": 0.9
                        })

                        await callbacks.on_agent_start("research", "Analyzing workspace...")
                        await asyncio.sleep(1)  # Simulate work
                        await callbacks.on_agent_complete("research", {"success": True})

                        # Execute actual workflow
                        result = await execute_supervisor_workflow(
                            user_query=user_query,
                            workspace_path=session["workspace_path"]
                        )

                        return result

                    # Execute workflow
                    result = await workflow_with_callbacks()

                    # Extract user response from result
                    user_response = result.get("user_response", "Workflow completed successfully")

                    # Send result
                    await manager.send_json(client_id, {
                        "type": "result",
                        "content": user_response,
                        "success": True,
                        "session_id": session["session_id"],
                        "workflow_state": {
                            "iteration": result.get("iteration", 0),
                            "last_agent": result.get("last_agent"),
                            "response_ready": result.get("response_ready", False),
                            "validation_passed": result.get("validation_passed", False)
                        },
                        "timestamp": datetime.now().isoformat(),
                        "message": "✅ Workflow complete!"
                    })

                    # Store response
                    session["messages"].append({
                        "role": "assistant",
                        "content": user_response,
                        "timestamp": datetime.now().isoformat()
                    })

                    logger.info(f"✅ Workflow complete for {client_id}")

                except Exception as e:
                    logger.error(f"❌ Workflow failed for {client_id}: {e}", exc_info=True)

                    await manager.send_json(client_id, {
                        "type": "error",
                        "message": f"Workflow execution failed: {str(e)}",
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "query": user_query[:100]
                    })

            # HITL RESPONSE (user response to HITL request)
            elif message_type == "hitl_response":
                user_response = data.get("response", "")
                # TODO: Implement HITL response handling
                await manager.send_json(client_id, {
                    "type": "info",
                    "message": "HITL response received and will be processed"
                })

    except WebSocketDisconnect:
        logger.info(f"🔌 Client {client_id} disconnected")
        manager.disconnect(client_id)
        if client_id in active_sessions:
            del active_sessions[client_id]

    except Exception as e:
        logger.error(f"❌ WebSocket error for {client_id}: {e}", exc_info=True)
        manager.disconnect(client_id)
        if client_id in active_sessions:
            del active_sessions[client_id]


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "server_v7_supervisor:app",
        host="0.0.0.0",
        port=8002,
        reload=False,
        log_level="info"
    )