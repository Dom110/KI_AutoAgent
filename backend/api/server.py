"""
KI AutoAgent Backend Server
FastAPI with WebSocket support for real-time agent communication
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
import logging
import hashlib
import uuid
from typing import Dict, Any, Optional, Set
from datetime import datetime
import uvicorn
import sys
import os
import traceback

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import agents and services
from agents.agent_registry import get_agent_registry
from agents.base.base_agent import TaskRequest
from core.cancellation import CancelToken, TaskCancelledException

# Import persistence services (will check availability after logger is initialized)
from services.conversation_persistence import ConversationPersistence
from services.model_discovery_service import get_model_discovery_service, discover_models_on_startup

# Import API routers
from api.models_endpoint import router as models_router

async def _discover_models_async():
    """Background task to discover models without blocking startup"""
    try:
        await asyncio.sleep(2)  # Wait a bit for server to be fully ready
        discovered_models = await discover_models_on_startup()
        logger.info(f"✅ Background model discovery complete: {sum(len(m) for m in discovered_models.values())} models found")
    except Exception as e:
        logger.warning(f"⚠️ Background model discovery failed: {e}")

# Import core systems
from core.memory_manager import get_memory_manager, MemoryType
from core.shared_context_manager import get_shared_context
from core.conversation_context_manager import get_conversation_context
from core.workflow_engine import get_workflow_engine, WorkflowNode, NodeType
from core.agent_communication_bus import get_communication_bus, MessageType
from core.validation_workflow import get_validation_workflow, ValidationConfig
from core.startup_check import StartupChecker
from core.exceptions import DependencyError
from agents.specialized.orchestrator_agent_v2 import OrchestratorAgentV2
from agents.specialized.architect_agent import ArchitectAgent
from agents.specialized.codesmith_agent import CodeSmithAgent
from agents.specialized.docubot_agent import DocuBotAgent
from agents.specialized.reviewer_gpt_agent import ReviewerGPTAgent
from agents.specialized.fixerbot_agent import FixerBotAgent
from agents.specialized.research_agent import ResearchAgent
from agents.specialized.tradestrat_agent import TradeStratAgent
from agents.specialized.opus_arbitrator_agent import OpusArbitratorAgent
from agents.specialized.performance_bot import PerformanceBot

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

    # Run dependency checks first - fail fast if anything is missing
    try:
        logger.info("🔍 Checking system dependencies...")
        await StartupChecker.check_all_dependencies()
    except DependencyError as e:
        logger.error(str(e))
        logger.error("❌ Cannot start system due to missing dependencies")
        sys.exit(1)  # Exit with error code
    except Exception as e:
        logger.error(f"❌ Unexpected error during startup check: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

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

    # Initialize conversation persistence
    global conversation_persistence
    try:
        conversation_persistence = ConversationPersistence()
        logger.info("✅ Conversation persistence initialized")
    except Exception as e:
        logger.warning(f"⚠️ Conversation persistence not available: {e}")
        conversation_persistence = None

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
    await registry.register_agent(PerformanceBot())

    logger.info(f"✅ Registered {len(registry.agents)} agents")

    # Optional: Discover available AI models (non-blocking)
    logger.info("🔍 Starting optional model discovery (non-blocking)...")
    try:
        # Run model discovery in background - don't block startup
        import asyncio
        asyncio.create_task(_discover_models_async())
    except Exception as e:
        logger.warning(f"⚠️ Model discovery skipped: {e}")

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
    version="4.0.6",
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

# Include API routers
app.include_router(models_router)

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

# Global variable for conversation persistence (will be initialized in lifespan)
conversation_persistence = None

# Task tracking for cancellation
active_agent_tasks: Dict[str, Set[asyncio.Task]] = {}
client_cancel_tokens: Dict[str, CancelToken] = {}

# Track active agent instances for pause/resume functionality
active_agents: Dict[str, Any] = {}

# Session management for reconnection support
class SessionManager:
    """Manages sessions that persist across WebSocket reconnects"""
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, workspace_id: str, task_info: Dict[str, Any]):
        """Create a new session for a workspace"""
        self.sessions[workspace_id] = {
            'status': 'running',
            'started_at': datetime.now().isoformat(),
            'task': task_info,
            'progress': [],
            'result': None
        }

    def update_progress(self, workspace_id: str, message: str):
        """Add progress update to session"""
        if workspace_id in self.sessions:
            self.sessions[workspace_id]['progress'].append({
                'time': datetime.now().isoformat(),
                'message': message
            })

    def complete_session(self, workspace_id: str, result: Any):
        """Mark session as complete"""
        if workspace_id in self.sessions:
            self.sessions[workspace_id]['status'] = 'completed'
            self.sessions[workspace_id]['completed_at'] = datetime.now().isoformat()
            self.sessions[workspace_id]['result'] = result

    def get_session(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        """Get session for workspace"""
        return self.sessions.get(workspace_id)

    def clear_session(self, workspace_id: str):
        """Clear session after it's been retrieved"""
        if workspace_id in self.sessions:
            del self.sessions[workspace_id]

# Global session manager
session_manager = SessionManager()

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
async def get_conversation_history(limit: int = 20, project_path: str = None):
    """Get recent conversation history - from persistent storage if available"""

    # Try to get from persistent storage first
    if conversation_persistence and project_path:
        try:
            history = await conversation_persistence.load_history(project_path, limit)
            return {
                "history": history,
                "source": "persistent",
                "project": project_path
            }
        except Exception as e:
            logger.error(f"Failed to load persistent history: {e}")

    # Fallback to in-memory history
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
        "summary": conversation.get_conversation_summary(),
        "source": "memory"
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

# Model discovery endpoints
@app.get("/api/models")
async def get_available_models():
    """Return all discovered AI models from all providers"""
    service = get_model_discovery_service()
    return service.discovered_models

@app.get("/api/models/{provider}")
async def get_provider_models(provider: str):
    """Return available models for a specific provider with detailed descriptions"""
    service = get_model_discovery_service()
    models = service.discovered_models.get(provider, [])

    # Add descriptions for each model
    models_with_descriptions = []
    for model_id in models:
        model_info = service.get_model_description(model_id)
        models_with_descriptions.append({
            "id": model_id,
            "name": model_info.get("name", model_id),
            "description": model_info.get("description", ""),
            "capabilities": model_info.get("capabilities", ""),
            "context": model_info.get("context", ""),
            "speed": model_info.get("speed", "")
        })

    return {
        "provider": provider,
        "models": models,
        "models_detailed": models_with_descriptions,
        "latest": service.get_latest_models(provider, 3),
        "recommended": {
            "general": service.get_recommended_model(provider, "general"),
            "code": service.get_recommended_model(provider, "code"),
            "fast": service.get_recommended_model(provider, "fast"),
            "reasoning": service.get_recommended_model(provider, "reasoning")
        }
    }

@app.post("/api/models/refresh")
async def refresh_models():
    """Force refresh model discovery"""
    service = get_model_discovery_service()
    models = await service.discover_all_models(force_refresh=True)
    return {
        "status": "success",
        "models_discovered": sum(len(m) for m in models.values()),
        "providers": list(models.keys())
    }

# WebSocket Chat Endpoint
@app.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    workspace: Optional[str] = Query(default=None)
):
    """Main WebSocket endpoint for chat communication"""
    # Generate deterministic client_id based on workspace
    if workspace:
        # Use workspace path to generate consistent ID
        workspace_hash = hashlib.md5(workspace.encode()).hexdigest()[:12]
        client_id = f"ws_{workspace_hash}"
        logger.info(f"🔑 Using workspace-based ID: {client_id} for {workspace}")
    else:
        # Fallback to random ID if no workspace provided
        client_id = f"client_{uuid.uuid4().hex[:8]}"
        logger.warning("⚠️ No workspace provided, using random client ID")

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

        # Check for existing session (reconnection scenario)
        if workspace:
            session = session_manager.get_session(client_id)
            if session:
                if session['status'] == 'running':
                    # Notify about running task
                    await manager.send_json(client_id, {
                        "type": "session_restore",
                        "status": "running",
                        "message": "🔄 You have a task still running in the background",
                        "task": session['task'],
                        "progress": session['progress'][-10:]  # Last 10 progress messages
                    })
                    logger.info(f"📢 Restored running session for {client_id}")
                elif session['status'] == 'completed':
                    # Notify about completed task
                    await manager.send_json(client_id, {
                        "type": "session_restore",
                        "status": "completed",
                        "message": "✅ Your previous task has completed while you were away",
                        "task": session['task'],
                        "result": session['result']
                    })
                    logger.info(f"📢 Restored completed session for {client_id}")
                    # Clear session after delivering result
                    session_manager.clear_session(client_id)

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
            elif message_type == "stop":
                # Cancel all running tasks for this client
                if client_id in active_agent_tasks:
                    for task in active_agent_tasks[client_id]:
                        if not task.done():
                            task.cancel()
                    active_agent_tasks.pop(client_id, None)

                # Clear cancel token
                if client_id in client_cancel_tokens:
                    await client_cancel_tokens[client_id].cancel()

                await manager.send_json(client_id, {
                    "type": "stopped",
                    "message": "All tasks cancelled successfully"
                })
                logger.info(f"⏹️ Stopped all tasks for client {client_id}")

            elif message_type == "pause":
                # Handle pause request
                current_agent = active_agents.get(client_id)
                if current_agent:
                    # Set WebSocket callback for pause notifications
                    current_agent.set_websocket_callback(
                        lambda msg: asyncio.create_task(manager.send_json(client_id, msg))
                    )

                    result = await current_agent.pause_current_task()
                    await manager.send_json(client_id, {
                        "type": "pauseActivated",
                        "data": result
                    })
                    logger.info(f"⏸️ Paused task for client {client_id}")
                else:
                    await manager.send_json(client_id, {
                        "type": "error",
                        "message": "No active agent to pause"
                    })

            elif message_type == "resume":
                # Handle resume request
                current_agent = active_agents.get(client_id)
                if current_agent:
                    additional_instructions = data.get("additionalInstructions")
                    result = await current_agent.resume_task(additional_instructions)

                    if result.get("status") == "clarification_needed":
                        await manager.send_json(client_id, {
                            "type": "clarificationNeeded",
                            "data": result
                        })
                    else:
                        await manager.send_json(client_id, {
                            "type": "resumed",
                            "data": result
                        })
                    logger.info(f"▶️ Resumed task for client {client_id}")
                else:
                    await manager.send_json(client_id, {
                        "type": "error",
                        "message": "No active agent to resume"
                    })

            elif message_type == "stopAndRollback":
                # Handle stop and rollback request
                current_agent = active_agents.get(client_id)
                if current_agent:
                    result = await current_agent.stop_and_rollback()
                    await manager.send_json(client_id, {
                        "type": "stoppedAndRolledBack",
                        "data": result
                    })
                    logger.info(f"🔄 Stopped and rolled back task for client {client_id}")

                    # Clear active agent
                    active_agents.pop(client_id, None)
                else:
                    await manager.send_json(client_id, {
                        "type": "error",
                        "message": "No active agent to stop and rollback"
                    })

            elif message_type == "clarificationResponse":
                # Handle user's response to clarification request
                current_agent = active_agents.get(client_id)
                if current_agent:
                    response = data.get("response", {})
                    result = await current_agent.handle_clarification(response)
                    await manager.send_json(client_id, {
                        "type": "clarificationResolved",
                        "data": result
                    })

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
    # Map 'auto' to 'orchestrator' for backward compatibility
    if agent_id == "auto":
        agent_id = "orchestrator"
    metadata = data.get("metadata", {})
    stream = data.get("stream", False)

    # Get project path for persistence
    project_path = metadata.get('project_path', os.getcwd())

    # Save user message to persistent history
    if conversation_persistence:
        await conversation_persistence.save_message(project_path, {
            'role': 'user',
            'content': content,
            'agent': agent_id,
            'metadata': metadata
        })

    # Get context managers
    conversation = get_conversation_context()
    shared_ctx = get_shared_context()
    memory = get_memory_manager()

    # Add conversation context to request
    context_str = conversation.get_formatted_context(limit=5)
    shared_data = shared_ctx.get_context()

    # Send thinking message
    # Log the request for debugging
    logger.info(f"📨 Processing request from {client_id} for agent {agent_id}")
    logger.debug(f"Request content: {content[:100]}..." if len(content) > 100 else f"Request content: {content}")

    await manager.send_json(client_id, {
        "type": "agent_thinking",
        "agent": agent_id,
        "message": f"🤔 {agent_id} is processing..."
    })

    try:
        # Get agent from registry
        registry = get_agent_registry()

        # Store agent instance for pause/resume
        agent_instance = registry.get_agent(agent_id)
        if agent_instance:
            active_agents[client_id] = agent_instance
            # Set WebSocket callback for pause notifications
            agent_instance.set_websocket_callback(
                lambda msg: asyncio.create_task(manager.send_json(client_id, msg))
            )

        # Create enhanced task request with context
        request = TaskRequest(
            prompt=content,
            context={
                **metadata.get("context", {}),
                "conversation_history": context_str,
                "shared_context": shared_data,
                "client_id": client_id,
                "manager": manager  # Pass the manager instance for progress messages
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
            # Normal response with cancellation support
            cancel_token = CancelToken()
            client_cancel_tokens[client_id] = cancel_token

            # Create task with tracking
            task = asyncio.create_task(
                registry.dispatch_task(agent_id, request, cancel_token)
            )

            # Track task
            if client_id not in active_agent_tasks:
                active_agent_tasks[client_id] = set()
            active_agent_tasks[client_id].add(task)

            try:
                result = await task
            finally:
                # Clean up task tracking
                if client_id in active_agent_tasks:
                    active_agent_tasks[client_id].discard(task)

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
            if result.status == "error":
                logger.error(f"❌ Agent error: {result.content[:500]}" if len(result.content) > 500 else f"❌ Agent error: {result.content}")

            # Save agent response to persistent history
            if conversation_persistence and result.content:
                await conversation_persistence.save_message(project_path, {
                    'role': 'assistant',
                    'content': result.content,
                    'agent': agent_id,
                    'metadata': result.metadata
                })

            # Send response
            await manager.send_json(client_id, {
                "type": "agent_response",
                "agent": agent_id,
                "content": result.content,
                "status": result.status,
                "metadata": result.metadata,
                "timestamp": datetime.now().isoformat()
            })

            # Complete session
            session_manager.complete_session(client_id, {
                'content': result.content,
                'status': result.status,
                'metadata': result.metadata
            })

            return

        # This code is now handled in the if/else block above

    except Exception as e:
        import traceback
        logger.error(f"Error processing chat message: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        await manager.send_json(client_id, {
            "type": "error",
            "message": f"Error: {str(e)}",
            "agent": agent_id,
            "details": traceback.format_exc()
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
    # Try to find an available port
    import socket
    import time
    import subprocess

    # First, try to kill any existing processes on our ports
    for p in range(8000, 8011):
        try:
            result = subprocess.run(['lsof', '-ti', f':{p}'], capture_output=True, text=True)
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    try:
                        subprocess.run(['kill', '-9', pid], check=False)
                        logger.info(f"Killed process {pid} on port {p}")
                    except:
                        pass
        except:
            pass

    # Small delay to ensure ports are released
    time.sleep(0.5)

    port = 8000
    max_port = 8010

    while port <= max_port:
        try:
            # Test if port is available
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if hasattr(socket, 'SO_REUSEPORT'):
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            sock.bind(('127.0.0.1', port))
            sock.close()

            # Wait a bit to ensure socket is fully closed
            time.sleep(0.1)

            logger.info(f"🚀 Starting server on port {port}")
            break
        except OSError as e:
            logger.warning(f"Port {port} is in use ({e}), trying next port...")
            port += 1
    else:
        logger.error(f"No available ports found between 8000 and {max_port}")
        exit(1)

    # Run the server
    uvicorn.run(
        app,  # Use the app object directly instead of "server:app" to avoid double import
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload to avoid port conflicts
        log_level="info"
    )