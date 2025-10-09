#!/usr/bin/env python3
"""
KI AutoAgent v6.0 Server - WebSocket API

Minimal server that creates WorkflowV6 instances per session.
Each WebSocket connection gets its own workflow instance with workspace path.

Architecture:
- FastAPI + WebSocket
- WorkflowV6 instances per session
- No global workflow (created on-demand)
- Async/await throughout

WebSocket Protocol:
1. Client connects → Server sends {"type": "connected", "requires_init": true}
2. Client sends {"type": "init", "workspace_path": "..."}
3. Server creates WorkflowV6 instance for this session
4. Client sends {"type": "chat", "content": "..."}
5. Server runs workflow and streams results

Author: KI AutoAgent Team
Version: 6.0.0
Python: 3.13+
"""

import asyncio
import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.expanduser("~/.ki_autoagent/config/.env")
load_dotenv(env_path)
logger_setup = logging.getLogger(__name__)
logger_setup.info(f"✅ Loaded environment from: {env_path}")

# Import v6 workflow
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from workflow_v6 import WorkflowV6

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for troubleshooting
    format="%(levelname)s:%(name)s:%(message)s",
    force=True,
)
logger = logging.getLogger(__name__)


# ============================================================================
# SESSION MANAGER
# ============================================================================

class SessionManager:
    """Manages active workflow sessions"""

    def __init__(self):
        self.sessions: dict[str, dict[str, Any]] = {}
        # session_id -> {"workflow": WorkflowV6, "workspace": str, "websocket": WebSocket}

    async def create_session(
        self,
        session_id: str,
        workspace_path: str,
        websocket: WebSocket
    ) -> WorkflowV6:
        """Create new workflow session"""
        logger.info(f"📦 Creating workflow for session {session_id}")
        logger.info(f"   Workspace: {workspace_path}")

        # Create workflow instance
        workflow = WorkflowV6(workspace_path=workspace_path)
        await workflow.initialize()

        # Store session
        self.sessions[session_id] = {
            "workflow": workflow,
            "workspace": workspace_path,
            "websocket": websocket,
        }

        logger.info(f"✅ Workflow created for session {session_id}")
        return workflow

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get session data"""
        return self.sessions.get(session_id)

    async def close_session(self, session_id: str):
        """Close and cleanup session"""
        session = self.sessions.get(session_id)
        if session:
            workflow = session["workflow"]
            await workflow.cleanup()
            del self.sessions[session_id]
            logger.info(f"🗑️  Session {session_id} closed")

    def list_sessions(self) -> list[str]:
        """List active session IDs"""
        return list(self.sessions.keys())


# Global session manager
session_manager = SessionManager()


# ============================================================================
# FASTAPI APP
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown"""
    logger.info("="*80)
    logger.info("🚀 KI AutoAgent v6.0 Server Starting...")
    logger.info("="*80)
    logger.info("WebSocket endpoint: ws://localhost:8001/ws/chat")
    logger.info("Sessions will be created on-demand per client")
    logger.info("="*80)

    yield

    # Cleanup all sessions
    logger.info("🛑 Shutting down...")
    for session_id in list(session_manager.sessions.keys()):
        await session_manager.close_session(session_id)
    logger.info("✅ All sessions closed")


app = FastAPI(title="KI AutoAgent v6.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "6.0.0",
        "active_sessions": len(session_manager.sessions),
        "sessions": session_manager.list_sessions(),
    }


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for chat.

    Protocol:
    1. Connect → {"type": "connected", "requires_init": true}
    2. Init → {"type": "init", "workspace_path": "..."}
    3. Chat → {"type": "chat", "content": "..."}
    """
    await websocket.accept()

    # Generate session ID
    session_id = str(uuid.uuid4())
    logger.info(f"🔌 WebSocket connected: {session_id}")

    # Send connected message
    await websocket.send_json({
        "type": "connected",
        "session_id": session_id,
        "requires_init": True,
        "message": "Connected! Please send init message with workspace_path."
    })

    workflow: WorkflowV6 | None = None

    try:
        while True:
            # Receive message
            message = await websocket.receive_json()
            msg_type = message.get("type")

            logger.info(f"📨 [{session_id}] Received: {msg_type}")

            # Handle init
            if msg_type == "init":
                workspace_path = message.get("workspace_path")

                if not workspace_path:
                    await websocket.send_json({
                        "type": "error",
                        "error": "workspace_path required in init message"
                    })
                    continue

                # Create workflow for this session
                workflow = await session_manager.create_session(
                    session_id=session_id,
                    workspace_path=workspace_path,
                    websocket=websocket
                )

                await websocket.send_json({
                    "type": "initialized",
                    "session_id": session_id,
                    "workspace_path": workspace_path,
                    "message": "Workflow initialized! Ready for chat messages."
                })

            # Handle chat
            elif msg_type == "chat":
                if not workflow:
                    await websocket.send_json({
                        "type": "error",
                        "error": "Session not initialized. Send init message first."
                    })
                    continue

                user_query = message.get("content")
                if not user_query:
                    await websocket.send_json({
                        "type": "error",
                        "error": "content required in chat message"
                    })
                    continue

                # Send status
                await websocket.send_json({
                    "type": "status",
                    "status": "Processing your request..."
                })

                try:
                    # Run workflow
                    logger.info(f"🤖 Running workflow for: {user_query[:100]}...")

                    result = await workflow.run(
                        user_query=user_query,
                        session_id=session_id
                    )

                    logger.info(f"✅ Workflow completed for session {session_id}")

                    # Send result
                    await websocket.send_json({
                        "type": "result",
                        "session_id": session_id,
                        "result": {
                            "user_query": result.get("user_query"),
                            "research": result.get("research_results"),
                            "architecture": result.get("architecture_design"),
                            "files_generated": len(result.get("generated_files", [])),
                            "review": result.get("review_feedback"),
                            "errors": result.get("errors", []),
                        },
                        "message": "Workflow completed successfully!"
                    })

                except Exception as e:
                    logger.error(f"❌ Workflow failed: {e}", exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "error": str(e),
                        "message": "Workflow execution failed"
                    })

            # Handle ping
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            # Unknown message type
            else:
                await websocket.send_json({
                    "type": "error",
                    "error": f"Unknown message type: {msg_type}"
                })

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected: {session_id}")

    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}", exc_info=True)

    finally:
        # Cleanup session
        if session_id in session_manager.sessions:
            await session_manager.close_session(session_id)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "server_v6:app",
        host="0.0.0.0",
        port=8001,
        log_level="info",
        reload=False,
    )
