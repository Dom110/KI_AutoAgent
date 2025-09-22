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

# Import core systems
from core.memory_manager import get_memory_manager, MemoryType
from core.shared_context_manager import get_shared_context
from core.conversation_context_manager import get_conversation_context
from core.workflow_engine import get_workflow_engine, WorkflowNode, NodeType
from core.agent_communication_bus import get_communication_bus, MessageType
from core.validation_workflow import get_validation_workflow, ValidationConfig
from agents.specialized.orchestrator_agent_v2 import OrchestratorAgentV2
from agents.specialized.architect_agent import ArchitectAgent
from agents.specialized.codesmith_agent import CodeSmithAgent
from agents.specialized.docubot_agent import DocuBotAgent
from agents.specialized.reviewer_gpt_agent import ReviewerGPTAgent
from agents.specialized.fixerbot_agent import FixerBotAgent
from agents.specialized.research_agent import ResearchAgent
from agents.specialized.tradestrat_agent import TradeStratAgent
from agents.specialized.opus_arbitrator_agent import OpusArbitratorAgent

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

    # Initialize core systems
    memory_manager = get_memory_manager()
    shared_context = get_shared_context()
    conversation_context = get_conversation_context()
    workflow_engine = get_workflow_engine()
    communication_bus = get_communication_bus()
    validation_workflow = get_validation_workflow()

    # Start communication bus
    await communication_bus.start()

    logger.info("🧠 Core systems initialized: Memory, SharedContext, ConversationContext, Workflow, CommunicationBus, Validation")

    # Initialize agent registry
    registry = get_agent_registry()

    # Register all agents
    logger.info("📦 Registering agents...")
    await registry.register_agent(OrchestratorAgentV2())
    await registry.register_agent(ArchitectAgent())
    await registry.register_agent(CodeSmithAgent())
    await registry.register_agent(DocuBotAgent())
    await registry.register_agent(ReviewerGPTAgent())
    await registry.register_agent(FixerBotAgent())
    await registry.register_agent(ResearchAgent())
    await registry.register_agent(TradeStratAgent())
    await registry.register_agent(OpusArbitratorAgent())

    logger.info(f"✅ Registered {len(registry.agents)} agents")

    yield

    # Cleanup
    logger.info("👋 KI AutoAgent Backend shutting down...")

    # Stop communication bus
    communication_bus = get_communication_bus()
    await communication_bus.stop()

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

# Direct agents endpoint (simpler URL)
@app.get("/agents")
async def list_agents():
    """List all registered agents"""
    registry = get_agent_registry()
    agents = []
    for agent_id, registered_agent in registry.agents.items():
        agent_instance = registered_agent.instance
        agents.append({
            "id": agent_id,
            "name": agent_instance.name,
            "role": agent_instance.role,
            "model": agent_instance.model,
            "capabilities": registered_agent.capabilities
        })
    return {"agents": agents, "count": len(agents)}

@app.get("/api/memory/stats")
async def get_memory_stats():
    """Get memory system statistics"""
    memory = get_memory_manager()
    return memory.get_stats()

@app.get("/api/context/shared")
async def get_shared_context_data():
    """Get current shared context"""
    context = get_shared_context()
    return context.get_context()

@app.get("/api/conversation/history")
async def get_conversation_history(limit: int = 20):
    """Get recent conversation history"""
    conversation = get_conversation_context()
    history = conversation.get_recent_history(limit)
    return {
        "history": [
            {
                "agent": h.agent,
                "timestamp": h.timestamp,
                "input": h.input[:200],
                "output": h.output[:500]
            }
            for h in history
        ],
        "summary": conversation.get_conversation_summary()
    }

@app.get("/api/workflow/stats")
async def get_workflow_stats():
    """Get workflow engine statistics"""
    engine = get_workflow_engine()
    return {
        "total_workflows": engine.total_workflows,
        "completed_workflows": engine.completed_workflows,
        "failed_workflows": engine.failed_workflows,
        "active_workflows": len(engine.workflows),
        "templates": list(engine.templates.keys())
    }

@app.get("/api/communication/stats")
async def get_communication_stats():
    """Get communication bus statistics"""
    bus = get_communication_bus()
    return bus.get_stats()

@app.get("/api/validation/stats")
async def get_validation_stats():
    """Get validation workflow statistics"""
    validation = get_validation_workflow()
    return validation.get_validation_stats()

@app.post("/api/workflow/create")
async def create_workflow(name: str, template: Optional[str] = None):
    """Create a new workflow"""
    engine = get_workflow_engine()
    workflow = engine.create_workflow(name, template)
    return {
        "workflow_id": workflow.id,
        "name": workflow.name,
        "state": workflow.state.value
    }

@app.post("/api/validation/validate")
async def validate_code(task: str, implementation: str, agent: str = "unknown"):
    """Validate code implementation"""
    validation = get_validation_workflow()
    result = await validation.validate_implementation(
        task=task,
        implementation=implementation,
        agent=agent
    )

    return {
        "passed": result.passed,
        "issues": [
            {
                "severity": issue.severity.value,
                "category": issue.category,
                "description": issue.description
            }
            for issue in result.issues
        ],
        "scores": {
            "security": result.security_score,
            "performance": result.performance_score,
            "completeness": result.completeness_score
        }
    }

async def handle_streaming_response(client_id: str, agent_id: str, request: TaskRequest, registry):
    """Handle streaming response from agent"""
    try:
        # For now, simulate streaming by sending chunks
        # TODO: Implement real streaming from agents that support it
        result = await registry.dispatch_task(agent_id, request)

        if result.content:
            # Split content into chunks
            chunk_size = 100
            content = result.content

            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                await manager.send_json(client_id, {
                    "type": "stream_chunk",
                    "agent": agent_id,
                    "content": chunk,
                    "done": False
                })
                await asyncio.sleep(0.05)  # Small delay to simulate streaming

            # Send completion
            await manager.send_json(client_id, {
                "type": "stream_chunk",
                "agent": agent_id,
                "content": "",
                "done": True,
                "metadata": result.metadata
            })

            # Store in conversation
            conversation = get_conversation_context()
            conversation.add_entry(
                agent=agent_id,
                step="chat_stream",
                input_text=request.prompt,
                output_text=content
            )
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        await manager.send_json(client_id, {
            "type": "error",
            "message": str(e)
        })

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
    """Handle chat messages with real agents, memory, and context"""
    content = data.get("content", "")
    agent_id = data.get("agent", "orchestrator")
    metadata = data.get("metadata", {})
    stream = data.get("stream", False)

    # Get context managers
    conversation = get_conversation_context()
    shared_ctx = get_shared_context()
    memory = get_memory_manager()

    # Add conversation context to request
    context_str = conversation.get_formatted_context(limit=5)
    shared_data = shared_ctx.get_context()

    # Send thinking message
    await manager.send_json(client_id, {
        "type": "agent_thinking",
        "agent": agent_id,
        "message": f"🤔 {agent_id} is processing..."
    })

    try:
        # Get agent from registry
        registry = get_agent_registry()

        # Create enhanced task request with context
        request = TaskRequest(
            prompt=content,
            context={
                **metadata.get("context", {}),
                "conversation_history": context_str,
                "shared_context": shared_data,
                "client_id": client_id
            },
            thinking_mode=metadata.get("thinkingMode", False),
            mode=metadata.get("mode", "auto"),
            agent=agent_id
        )

        # If streaming requested, handle differently
        if stream:
            # Stream response in chunks
            await handle_streaming_response(client_id, agent_id, request, registry)
        else:
            # Normal response
            result = await registry.dispatch_task(agent_id, request)

            # Store in memory and conversation
            await memory.store(
                agent_id=agent_id,
                content={"input": content, "output": result.content},
                memory_type=MemoryType.EPISODIC,
                metadata={"client_id": client_id, "status": result.status}
            )

            conversation.add_entry(
                agent=agent_id,
                step="chat",
                input_text=content,
                output_text=result.content,
                metadata=result.metadata,
                execution_time=result.execution_time or 0
            )

            # Update shared context
            await shared_ctx.update_context(
                agent_id=agent_id,
                key="agent_outputs",
                value={agent_id: result.content},
                metadata={"timestamp": datetime.now().isoformat()}
            )

            # Debug log the result
            logger.info(f"📊 Agent result - Status: {result.status}, Content length: {len(result.content) if result.content else 0}")

            # Send response
            await manager.send_json(client_id, {
                "type": "agent_response",
                "agent": agent_id,
                "content": result.content,
                "status": result.status,
                "metadata": result.metadata,
                "timestamp": datetime.now().isoformat()
            })

            return

        # This code is now handled in the if/else block above

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
    """Handle workflow execution with real workflow engine"""
    workflow_data = data.get("workflow", {})
    name = workflow_data.get("name", "unnamed_workflow")
    template = workflow_data.get("template")
    context = workflow_data.get("context", {})

    try:
        # Get workflow engine
        engine = get_workflow_engine()

        # Create workflow
        workflow = engine.create_workflow(name, template)

        # Send workflow started message
        await manager.send_json(client_id, {
            "type": "workflow_started",
            "workflow_id": workflow.id,
            "name": workflow.name,
            "steps": len(workflow.nodes)
        })

        # Execute workflow
        results = await workflow.execute(context)

        # Send workflow completed message
        await manager.send_json(client_id, {
            "type": "workflow_completed",
            "workflow_id": workflow.id,
            "result": "Workflow completed successfully",
            "summary": {
                "total_nodes": len(workflow.nodes),
                "completed_nodes": len(workflow.completed_nodes),
                "failed_nodes": len(workflow.failed_nodes),
                "execution_time": workflow.end_time - workflow.start_time if workflow.end_time else 0
            }
        })

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        await manager.send_json(client_id, {
            "type": "workflow_failed",
            "error": str(e)
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