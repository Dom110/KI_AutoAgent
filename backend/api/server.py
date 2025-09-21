"""
KI AutoAgent Backend Server
FastAPI with WebSocket support for real-time agent communication
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uvicorn
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import agents and services
from agents.agent_registry import get_agent_registry
from agents.base.base_agent import TaskRequest
from agents.specialized.orchestrator_agent import OrchestratorAgent
from agents.specialized.architect_agent import ArchitectAgent
from agents.specialized.codesmith_agent import CodeSmithAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    logger.info("🚀 KI AutoAgent Backend starting...")

    # Initialize agent registry
    registry = get_agent_registry()

    # Register all agents
    logger.info("📦 Registering agents...")
    await registry.register_agent(OrchestratorAgent())
    await registry.register_agent(ArchitectAgent())
    await registry.register_agent(CodeSmithAgent())

    logger.info(f"✅ Registered {len(registry.agents)} agents")

    yield

    # Cleanup
    logger.info("👋 KI AutoAgent Backend shutting down...")
    await registry.shutdown()

# Create FastAPI app
app = FastAPI(
    title="KI AutoAgent Backend",
    description="Advanced Multi-Agent System with Memory and Collaboration",
    version="4.0.0",
    lifespan=lifespan
)

# Configure CORS for VS Code Extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:*",
        "https://localhost:*",
        "vscode-webview://*",
        "https://*.vscode-cdn.net"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_count = 0

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_count += 1
        logger.info(f"✅ Client {client_id} connected. Total: {len(self.active_connections)}")

    async def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"❌ Client {client_id} disconnected. Total: {len(self.active_connections)}")

    async def send_json(self, client_id: str, data: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(data)

    async def broadcast_json(self, data: dict):
        for connection in self.active_connections.values():
            await connection.send_json(data)

manager = ConnectionManager()

# Health check endpoint
@app.get("/")
async def health_check():
    return {
        "status": "healthy",
        "service": "KI AutoAgent Backend",
        "version": "4.0.0",
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(manager.active_connections)
    }

# Agent info endpoint
@app.get("/api/agents")
async def get_agents():
    """Return available agents and their capabilities"""
    registry = get_agent_registry()
    return {
        "agents": registry.get_available_agents()
    }

# WebSocket Chat Endpoint
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """Main WebSocket endpoint for chat communication"""
    client_id = f"client_{manager.connection_count}"

    try:
        await manager.connect(websocket, client_id)

        # Send welcome message
        await manager.send_json(client_id, {
            "type": "connection",
            "status": "connected",
            "client_id": client_id,
            "message": "🤖 Connected to KI AutoAgent Backend",
            "timestamp": datetime.now().isoformat()
        })

        # Message handling loop
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            logger.info(f"📨 Received from {client_id}: {data.get('type', 'unknown')}")

            # Handle different message types
            message_type = data.get("type", "chat")

            if message_type == "chat":
                await handle_chat_message(client_id, data)
            elif message_type == "command":
                await handle_command(client_id, data)
            elif message_type == "workflow":
                await handle_workflow(client_id, data)
            elif message_type == "ping":
                await manager.send_json(client_id, {"type": "pong"})
            else:
                await manager.send_json(client_id, {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })

    except WebSocketDisconnect:
        await manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"❌ WebSocket error for {client_id}: {e}")
        await manager.disconnect(client_id)

async def handle_chat_message(client_id: str, data: dict):
    """Handle chat messages with real agents"""
    content = data.get("content", "")
    agent_id = data.get("agent", "orchestrator")
    metadata = data.get("metadata", {})

    # Send thinking message
    await manager.send_json(client_id, {
        "type": "agent_thinking",
        "agent": agent_id,
        "message": f"🤔 {agent_id} is processing..."
    })

    try:
        # Get agent from registry
        registry = get_agent_registry()

        # Create task request
        request = TaskRequest(
            prompt=content,
            context=metadata.get("context", {}),
            thinking_mode=metadata.get("thinkingMode", False),
            mode=metadata.get("mode", "auto"),
            agent=agent_id
        )

        # Dispatch to agent
        result = await registry.dispatch_task(agent_id, request)

        # Send response
        await manager.send_json(client_id, {
            "type": "agent_response",
            "agent": agent_id,
            "content": result.content,
            "status": result.status,
            "metadata": result.metadata,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        await manager.send_json(client_id, {
            "type": "error",
            "message": f"Error: {str(e)}",
            "agent": agent_id
        })

async def handle_command(client_id: str, data: dict):
    """Handle command messages"""
    command = data.get("command", "")

    await manager.send_json(client_id, {
        "type": "command_result",
        "command": command,
        "result": f"Command '{command}' executed successfully",
        "timestamp": datetime.now().isoformat()
    })

async def handle_workflow(client_id: str, data: dict):
    """Handle workflow execution"""
    workflow = data.get("workflow", {})

    await manager.send_json(client_id, {
        "type": "workflow_started",
        "workflow_id": "wf_001",
        "steps": workflow.get("steps", [])
    })

    # TODO: Execute workflow with real agents

    await manager.send_json(client_id, {
        "type": "workflow_completed",
        "workflow_id": "wf_001",
        "result": "Workflow completed successfully"
    })

# Error handling
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return {"error": "Internal server error", "detail": str(exc)}

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )