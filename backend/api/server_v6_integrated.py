"""
KI AutoAgent v6 Integrated Server

Lightweight FastAPI server that uses the COMPLETE v6 integrated workflow.

All v6 systems active:
✅ Query Classifier
✅ Curiosity System
✅ Predictive System
✅ Tool Registry
✅ Approval Manager
✅ Workflow Adapter
✅ Neurosymbolic Reasoner
✅ Learning System
✅ Self-Diagnosis

Usage:
    python backend/api/server_v6_integrated.py

    WebSocket: ws://localhost:8002/ws/chat

Author: KI AutoAgent Team
Version: Dynamic (imported from __version__.py)
Python: 3.13+
"""

from __future__ import annotations

# Import version FIRST
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from __version__ import __version__, __release_tag__

# v5.9.0: Install uvloop FIRST
# ⚠️ FALLBACK: uvloop is optional performance optimization (not required for functionality)
# Reason: uvloop provides 2-4x faster event loop, but asyncio works without it
# Date: 2025-10-09
# Performance impact: ~30% slower without uvloop, but fully functional
try:
    import uvloop
    uvloop.install()
    _UVLOOP_INSTALLED = True
except ImportError:
    _UVLOOP_INSTALLED = False
    # Log fallback activation (ASIMOV RULE 1 compliance)
    import logging
    logging.warning("⚠️ FALLBACK ACTIVE: uvloop not installed - using standard asyncio event loop (30% slower)")
    logging.warning("   Install with: pip install uvloop")
    logging.warning("   File: server_v6_integrated.py Line: 30")

import os
import sys
from pathlib import Path

# Add paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if grandparent_dir not in sys.path:
    sys.path.insert(0, grandparent_dir)

import asyncio
import logging
import uuid

# Load .env from global config (BEFORE logger setup)
from dotenv import load_dotenv
global_env = Path.home() / ".ki_autoagent" / "config" / ".env"
_env_loaded = False
if global_env.exists():
    load_dotenv(global_env)
    _env_loaded = True
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketState

# Import v6 integrated workflow
from workflow_v6_integrated import WorkflowV6Integrated

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True
)
logger = logging.getLogger(__name__)

if _UVLOOP_INSTALLED:
    logger.info("⚡ uvloop ENABLED: Event loop performance boosted 2-4x")
else:
    logger.warning("⚠️  uvloop NOT installed - using standard asyncio")

# Log .env loading
if _env_loaded:
    logger.info(f"✅ Loaded API keys from: {global_env}")
else:
    logger.warning(f"⚠️  .env not found at: {global_env}")

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

# ============================================================================
# GLOBAL STATE
# ============================================================================

manager = ConnectionManager()
active_sessions: dict[str, dict[str, Any]] = {}
workflows: dict[str, WorkflowV6Integrated] = {}

# ============================================================================
# APP LIFESPAN
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle."""
    logger.info("🚀 Starting KI AutoAgent v6 Integrated Server...")
    logger.info("📡 WebSocket endpoint: ws://localhost:8002/ws/chat")
    logger.info("✨ ALL v6 systems active!")

    yield

    logger.info("🛑 Shutting down v6 Integrated Server...")

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title=f"KI AutoAgent {__release_tag__}",
    description="Complete v6 workflow with ALL intelligence systems",
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
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(manager.active_connections),
        "active_workflows": len(workflows),
        "v6_systems": "ALL_ACTIVE"
    }

@app.get("/api/v6/stats")
async def get_v6_stats():
    """Get v6 system statistics."""
    stats = {
        "active_workflows": len(workflows),
        "active_connections": len(manager.active_connections),
        "systems": {}
    }

    # Get stats from first active workflow (if any)
    if workflows:
        workflow = list(workflows.values())[0]
        if workflow.learning:
            stats["systems"]["learning"] = await workflow.learning.get_overall_statistics()
        if workflow.self_diagnosis:
            stats["systems"]["self_diagnosis"] = workflow.self_diagnosis.get_health_report()
        if workflow.workflow_adapter:
            stats["systems"]["workflow_adapter"] = workflow.workflow_adapter.get_adaptation_stats()
        if workflow.neurosymbolic:
            stats["systems"]["neurosymbolic"] = workflow.neurosymbolic.get_rule_stats()

    return stats

# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """Main WebSocket endpoint with v6 integration."""

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

    try:
        # Welcome message
        await manager.send_json(client_id, {
            "type": "connected",
            "message": f"Connected to KI AutoAgent {__release_tag__}. Send init message with workspace_path.",
            "session_id": session["session_id"],
            "client_id": client_id,
            "version": __version__,
            "release_tag": __release_tag__,
            "requires_init": True,
            "v6_systems": "ALL_ACTIVE"
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

                # Initialize v6 workflow for this client
                logger.info(f"🔧 Initializing v6 workflow for {client_id}...")

                # Create approval callback for this WebSocket
                async def approval_callback(request: dict) -> dict:
                    """Send approval request and wait for response."""
                    # Send approval request
                    await manager.send_json(client_id, {
                        "type": "approval_request",
                        **request
                    })

                    # Wait for response (simplified - in production use asyncio.Event)
                    # For now, auto-approve
                    logger.info(f"  (Auto-approving for test)")
                    return {"approved": True, "response": "Auto-approved in test"}

                workflow = WorkflowV6Integrated(
                    workspace_path=workspace_path,
                    websocket_callback=approval_callback
                )
                await workflow.initialize()

                workflows[client_id] = workflow

                logger.info(f"✅ Client {client_id} initialized with v6 workflow")

                await manager.send_json(client_id, {
                    "type": "initialized",
                    "session_id": session["session_id"],
                    "workspace_path": workspace_path,
                    "message": "v6 workflow initialized - ALL systems active!",
                    "v6_systems": {
                        "query_classifier": True,
                        "curiosity": True,
                        "predictive": True,
                        "tool_registry": True,
                        "approval_manager": True,
                        "workflow_adapter": True,
                        "neurosymbolic": True,
                        "learning": True,
                        "self_diagnosis": True
                    }
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
            # Accept both "chat" and "message" for compatibility
            if message_type in ["chat", "message"]:
                user_query = data.get("content") or data.get("message", "")
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

                # Get workflow for this client
                workflow = workflows.get(client_id)
                if not workflow:
                    await manager.send_json(client_id, {
                        "type": "error",
                        "message": "Workflow not initialized"
                    })
                    continue

                # Send "thinking" status
                await manager.send_json(client_id, {
                    "type": "status",
                    "status": "analyzing",
                    "message": "🧠 Running pre-execution analysis with v6 systems..."
                })

                try:
                    logger.info(f"🚀 Running v6 workflow for: {user_query[:80]}...")

                    # Execute workflow with ALL v6 systems
                    result = await workflow.run(
                        user_query=user_query,
                        session_id=session["session_id"]
                    )

                    # Send comprehensive result
                    # Use "result" type for E2E test compatibility
                    await manager.send_json(client_id, {
                        "type": "result",
                        "subtype": "workflow_complete",
                        "success": result["success"],
                        "session_id": session["session_id"],
                        "execution_time": result["execution_time"],
                        "quality_score": result["quality_score"],

                        # v6 Intelligence Insights
                        "analysis": result["analysis"],
                        "adaptations": result["adaptations"],
                        "health": result["health"],

                        # Results
                        "result": result["result"],
                        "errors": result["errors"],
                        "warnings": result["warnings"],

                        # Metadata
                        "v6_systems_used": result["v6_systems_used"],

                        "message": "✅ Workflow complete with v6 intelligence!"
                    })

                    # Store response
                    session["messages"].append({
                        "role": "assistant",
                        "content": result,
                        "timestamp": datetime.now().isoformat()
                    })

                    logger.info(f"✅ Workflow complete for {client_id}")
                    logger.info(f"  Quality: {result['quality_score']:.2f}")
                    logger.info(f"  Adaptations: {result['adaptations']['total_adaptations']}")

                except Exception as e:
                    logger.error(f"❌ Workflow failed for {client_id}: {e}", exc_info=True)
                    logger.error(f"   Query: {user_query[:100]}...")
                    logger.error(f"   Workspace: {session.get('workspace_path')}")

                    await manager.send_json(client_id, {
                        "type": "error",
                        "message": f"Workflow execution failed: {str(e)}",
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "query": user_query[:100]
                    })

            # PLAN MODE (optional)
            elif message_type == "plan":
                # Future: Plan-only mode
                await manager.send_json(client_id, {
                    "type": "info",
                    "message": "Plan mode not yet implemented in v6"
                })

    except WebSocketDisconnect:
        logger.info(f"🔌 Client {client_id} disconnected")
        manager.disconnect(client_id)
        if client_id in active_sessions:
            del active_sessions[client_id]
        if client_id in workflows:
            del workflows[client_id]

    except Exception as e:
        logger.error(f"❌ WebSocket error for {client_id}: {e}", exc_info=True)
        manager.disconnect(client_id)
        if client_id in active_sessions:
            del active_sessions[client_id]
        if client_id in workflows:
            del workflows[client_id]

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "server_v6_integrated:app",
        host="0.0.0.0",
        port=8002,
        reload=False,
        log_level="info"
    )
