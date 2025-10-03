"""
KI AutoAgent Backend Server with LangGraph Integration
FastAPI with WebSocket support for LangGraph workflow
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional, Set
from datetime import datetime
import uvicorn
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import LangGraph system
from langgraph_system import (
    create_agent_workflow,
    ExtendedAgentState,
    ToolRegistry,
    ApprovalManager,
    PersistentAgentMemory,
    DynamicWorkflowManager
)

# Import Models Endpoint
from .models_endpoint import router as models_router

# Import Settings Endpoint
from .settings_endpoint import router as settings_router

# Import version information
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from __version__ import __version__, __version_display__, __release_tag__

# Configure logging with detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s',
    force=True  # Force reconfiguration (Python 3.8+)
)
logger = logging.getLogger(__name__)

# Add debug message on startup
logger.info(f"🔍 DEBUG: Starting LangGraph server {__version_display__} on port 8001")
logger.info(f"🔍 DEBUG: This is the ACTIVE server for {__release_tag__}")
logger.info("🔍 DEBUG: WebSocket endpoint: ws://localhost:8001/ws/chat")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_info: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_info[client_id] = {
            "connected_at": datetime.now(),
            "last_activity": datetime.now()
        }
        logger.info(f"✅ Client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            del self.connection_info[client_id]
            logger.info(f"❌ Client {client_id} disconnected")

    async def send_json(self, client_id: str, data: dict):
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                logger.info(f"🔌 WebSocket DEBUG: Attempting to send to {client_id}, websocket state: {websocket.client_state if hasattr(websocket, 'client_state') else 'unknown'}")
                await websocket.send_json(data)
                self.connection_info[client_id]["last_activity"] = datetime.now()
                logger.info(f"✅ WebSocket DEBUG: Successfully sent message to {client_id}")
            except Exception as e:
                import traceback
                logger.error(f"Error sending to {client_id}: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                self.disconnect(client_id)
        else:
            logger.error(f"❌ WebSocket DEBUG: Client {client_id} not in active_connections!")

    async def broadcast_json(self, data: dict):
        disconnected = []
        for client_id in list(self.active_connections.keys()):
            try:
                await self.active_connections[client_id].send_json(data)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected.append(client_id)

        for client_id in disconnected:
            self.disconnect(client_id)

# Global instances
manager = ConnectionManager()
workflow_system = None
active_sessions: Dict[str, Dict[str, Any]] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI"""
    global workflow_system

    try:
        # Startup
        logger.info("=" * 80)
        logger.info(f"🚀 Starting KI AutoAgent LangGraph Backend {__version_display__}...")
        logger.info("🔍 DEBUG: Initializing LangGraph StateGraph workflow system")
        logger.info("🔍 DEBUG: Using port 8001 (NOT 8000)")

        # Initialize LangGraph workflow system
        logger.info("📦 Creating agent workflow...")
        global workflow_system
        workflow_system = await create_agent_workflow(
            websocket_manager=manager,
            db_path="langgraph_state.db",
            memory_db_path="agent_memories.db"
        )

        if workflow_system is None:
            logger.error("❌ CRITICAL: create_agent_workflow returned None!")
            raise RuntimeError("Failed to create workflow system")

        logger.info("✅ LangGraph workflow system initialized")
        logger.info(f"✅ workflow_system type: {type(workflow_system).__name__}")

        # Initialize tool registry
        tool_registry = workflow_system.tool_registry
        logger.info(f"🔧 Tool registry initialized with {len(tool_registry.tools)} tools")

        # Initialize approval manager
        approval_manager = workflow_system.approval_manager
        logger.info("✅ Approval manager initialized")

        logger.info("=" * 80)
        logger.info("🎉 STARTUP COMPLETE - Ready to accept connections!")
        logger.info("=" * 80)

        yield

        # Cleanup
        logger.info("👋 Shutting down KI AutoAgent Backend...")

    except Exception as e:
        import traceback
        logger.error(f"❌ FATAL ERROR during startup: {e}")
        logger.error(f"📍 Traceback:\n{traceback.format_exc()}")
        raise

# Create FastAPI app
app = FastAPI(
    title="KI AutoAgent LangGraph Backend",
    version=__version__,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Models API Router
app.include_router(models_router)
logger.info("✅ Models API endpoint registered at /api/models")

# Include Settings API Router
app.include_router(settings_router)
logger.info("✅ Settings API endpoint registered at /api/settings")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "workflow_ready": workflow_system is not None
    }

# Tool discovery endpoint
@app.get("/api/tools")
async def get_tools(agent: Optional[str] = None):
    """Get available tools, optionally filtered by agent"""
    if not workflow_system:
        raise HTTPException(status_code=503, detail="Workflow system not initialized")

    tool_registry = workflow_system.tool_registry

    if agent:
        tools = tool_registry.discover_tools_for_agent(agent)
        return {
            "agent": agent,
            "tools": [tool_registry.get_tool_schema(t.name) for t in tools]
        }
    else:
        return {
            "tools": tool_registry.list_all_tools()
        }

# Memory stats endpoint
@app.get("/api/memory/stats")
async def get_memory_stats(agent: Optional[str] = None):
    """Get memory statistics for agents"""
    if not workflow_system:
        raise HTTPException(status_code=503, detail="Workflow system not initialized")

    if agent:
        if agent in workflow_system.agent_memories:
            memory = workflow_system.agent_memories[agent]
            return {
                "agent": agent,
                "stats": memory.get_memory_stats()
            }
        else:
            raise HTTPException(status_code=404, detail=f"Agent {agent} not found")
    else:
        stats = {}
        for agent_name, memory in workflow_system.agent_memories.items():
            stats[agent_name] = memory.get_memory_stats()
        return {"memory_stats": stats}

# Workflow info endpoint
@app.get("/api/workflow/info")
async def get_workflow_info():
    """Get current workflow structure information"""
    if not workflow_system:
        raise HTTPException(status_code=503, detail="Workflow system not initialized")

    dynamic_manager = workflow_system.dynamic_manager
    return dynamic_manager.get_graph_info()

# Workflow visualization endpoint
@app.get("/api/workflow/visualize")
async def visualize_workflow(format: str = "mermaid"):
    """Get workflow visualization in specified format"""
    if not workflow_system:
        raise HTTPException(status_code=503, detail="Workflow system not initialized")

    dynamic_manager = workflow_system.dynamic_manager
    try:
        visualization = dynamic_manager.visualize_graph(format=format)
        return {
            "format": format,
            "visualization": visualization
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Approval handling endpoint
@app.post("/api/approval/{approval_id}")
async def handle_approval(approval_id: str, response: dict):
    """Handle user response to approval request"""
    if not workflow_system:
        raise HTTPException(status_code=503, detail="Workflow system not initialized")

    approval_manager = workflow_system.approval_manager
    success = await approval_manager.handle_user_response(approval_id, response)

    if success:
        return {"status": "accepted", "approval_id": approval_id}
    else:
        raise HTTPException(status_code=404, detail="Approval request not found or expired")

# WebSocket endpoint
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """Main WebSocket endpoint for chat communication"""
    client_id = f"client_{uuid.uuid4().hex[:8]}"

    await manager.connect(websocket, client_id)

    # Create session
    session = {
        "client_id": client_id,
        "session_id": str(uuid.uuid4()),
        "created_at": datetime.now(),
        "messages": [],
        "plan_first_mode": False,
        "workspace_path": None
    }
    active_sessions[client_id] = session

    try:
        # Send welcome message
        logger.info(f"🔍 DEBUG: New client connected: {client_id}")
        await manager.send_json(client_id, {
            "type": "connected",
            "message": f"Connected to KI AutoAgent LangGraph System {__version_display__}",
            "session_id": session["session_id"],
            "client_id": client_id,
            "version": __release_tag__
        })
        logger.info(f"🔍 DEBUG: Welcome message sent to {client_id}")

        # Message handling loop
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type", "chat")

            logger.info(f"🔍 DEBUG: Received {message_type} from {client_id}")
            logger.info(f"🔍 DEBUG: Using LangGraph {__version_display__} - Port 8001")
            logger.info(f"🔍 DEBUG: Message data keys: {list(data.keys())}")
            if message_type == "chat":
                content = data.get("content") or data.get("message") or ""
                logger.info(f"🔍 DEBUG: Chat message content: {content[:100]}...")

            if message_type == "chat":
                await handle_chat_message(client_id, data, session)

            elif message_type == "architecture_approval":
                # v5.2.0: Handle architecture proposal approval
                session_id = data.get("session_id")
                decision = data.get("decision")  # "approved", "rejected", "modified"
                feedback = data.get("feedback", "")

                logger.info(f"📋 Architecture approval received: {decision} (session: {session_id})")

                if not session_id:
                    logger.error("❌ No session_id in architecture_approval message")
                    await manager.send_json(client_id, {
                        "type": "error",
                        "message": "Missing session_id"
                    })
                    return

                if decision not in ["approved", "rejected", "modified"]:
                    logger.error(f"❌ Invalid decision: {decision}")
                    await manager.send_json(client_id, {
                        "type": "error",
                        "message": f"Invalid decision: {decision}"
                    })
                    return

                # Find the session (in active_sessions or workflow state)
                # For now, update session state and resume workflow
                if workflow_system and hasattr(workflow_system, 'active_workflows'):
                    # Find the workflow state
                    workflow_state = None
                    for ws_session_id, ws_state in workflow_system.active_workflows.items():
                        if ws_session_id == session_id:
                            workflow_state = ws_state
                            break

                    if workflow_state:
                        logger.info(f"✅ Found workflow state for session {session_id}")

                        # Send acknowledgment to client
                        await manager.send_json(client_id, {
                            "type": "architectureApprovalProcessed",
                            "session_id": session_id,
                            "decision": decision,
                            "message": f"Architecture proposal {decision}"
                        })

                        # Update checkpoint with approval decision
                        logger.info(f"🔄 Processing approval decision: {decision}")
                        try:
                            config = {"configurable": {"thread_id": session_id}}

                            # v5.5.3: Alternative approach - pass approval decision as input to resume
                            # Instead of updating state and resuming with None,
                            # we pass the approval data directly to the workflow
                            approval_input = {
                                "proposal_status": decision,
                                "user_feedback_on_proposal": feedback,
                                "status": "executing" if decision == "approved" else "failed",
                                "needs_approval": False,
                                "waiting_for_approval": False,
                                "resume_from_approval": True  # Signal that this is a resume
                            }

                            logger.info(f"📋 Passing approval decision to workflow: {decision}")

                            # Resume workflow with the approval input
                            logger.info(f"🔄 Resuming workflow with approval input...")
                            final_state = await workflow_system.workflow.ainvoke(
                                approval_input,  # Pass approval as input instead of None
                                config=config
                            )

                            # Update the stored state
                            workflow_system.active_workflows[session_id] = final_state

                            # Send completion message
                            await manager.send_json(client_id, {
                                "type": "response",
                                "agent": "orchestrator",
                                "content": final_state.get("final_result", "Workflow completed after approval"),
                                "metadata": {
                                    "status": final_state.get("status"),
                                    "completion_time": datetime.now().isoformat()
                                }
                            })

                            logger.info(f"✅ Workflow resumed and completed for session {session_id}")

                        except Exception as e:
                            logger.error(f"❌ Error resuming workflow: {e}", exc_info=True)
                            await manager.send_json(client_id, {
                                "type": "error",
                                "message": f"Failed to resume workflow: {str(e)}"
                            })
                    else:
                        logger.error(f"❌ Workflow state not found for session {session_id}")
                        await manager.send_json(client_id, {
                            "type": "error",
                            "message": f"Workflow not found for session {session_id}"
                        })
                else:
                    logger.error("❌ workflow_system not available or missing active_workflows")
                    await manager.send_json(client_id, {
                        "type": "error",
                        "message": "Workflow system not available"
                    })

            elif message_type == "setWorkspace":
                # Set workspace path (handle both camelCase and snake_case)
                session["workspace_path"] = data.get("workspacePath") or data.get("workspace_path")
                logger.info(f"📁 Workspace set for {client_id}: {session['workspace_path']}")

            elif message_type == "stop":
                # Stop current workflow
                # TODO: Implement workflow cancellation
                await manager.send_json(client_id, {
                    "type": "stopped",
                    "message": "Workflow stopped"
                })

            elif message_type == "ping":
                await manager.send_json(client_id, {"type": "pong"})

            else:
                await manager.send_json(client_id, {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        if client_id in active_sessions:
            del active_sessions[client_id]
        logger.info(f"Client {client_id} disconnected")

    except Exception as e:
        logger.error(f"Error in WebSocket handler: {e}")
        manager.disconnect(client_id)
        if client_id in active_sessions:
            del active_sessions[client_id]


async def handle_chat_message(client_id: str, data: dict, session: dict):
    """Handle chat messages using LangGraph workflow"""
    content = data.get("content") or data.get("message") or ""

    # Use client-provided session_id if available, otherwise use server-generated
    if "session_id" in data and data["session_id"]:
        session["session_id"] = data["session_id"]
        logger.info(f"📌 Using client-provided session_id: {session['session_id']}")

    if not content:
        await manager.send_json(client_id, {
            "type": "error",
            "message": "Empty message received"
        })
        return

    # Check if workflow is waiting for architecture approval
    session_id = session["session_id"]
    logger.info(f"🔌 WebSocket DEBUG: Checking for approval state - session_id: {session_id}")

    # First check the WebSocket manager's active_workflows
    if manager and hasattr(manager, 'active_workflows'):
        logger.info(f"🔌 WebSocket DEBUG: Found manager.active_workflows with {len(getattr(manager, 'active_workflows', {}))} sessions")
        workflow_state = manager.active_workflows.get(session_id, {})
        if workflow_state.get("waiting_for_chat_approval"):
            logger.info(f"📋 Chat approval detected in manager for session {session_id}")
    # Then check workflow_system's active_workflows
    elif workflow_system and hasattr(workflow_system, 'active_workflows'):
        logger.info(f"🔌 WebSocket DEBUG: Found workflow_system.active_workflows with {len(workflow_system.active_workflows)} sessions")
        workflow_state = workflow_system.active_workflows.get(session_id, {})
    else:
        logger.info(f"🔌 WebSocket DEBUG: No active_workflows found in manager or workflow_system")
        workflow_state = {}

    # Check if waiting for chat-based approval
    if workflow_state.get("waiting_for_chat_approval"):
        logger.info(f"📋 Chat approval detected for session {session_id}")

        # Parse user response as approval decision
        content_lower = content.lower().strip()

        if "approve" in content_lower or "yes" in content_lower or "ok" in content_lower or "proceed" in content_lower:
            decision = "approved"
            feedback = content if len(content) > 10 else "Approved via chat"
        elif "reject" in content_lower or "no" in content_lower or "stop" in content_lower:
            decision = "rejected"
            feedback = content if len(content) > 10 else "Rejected via chat"
        else:
            decision = "modified"
            feedback = content  # User's feedback for modification

        logger.info(f"📋 User decision: {decision} - '{content}'")

        # Send approval acknowledgment
        await manager.send_json(client_id, {
            "type": "agent_response",
            "agent": "system",
            "content": f"📋 Architecture {decision}. {'Continuing workflow...' if decision == 'approved' else 'Stopping workflow.'}"
        })

        # Process the approval like architecture_approval message
        approval_input = {
            "proposal_status": decision,
            "user_feedback_on_proposal": feedback,
            "status": "executing" if decision == "approved" else "failed",
            "needs_approval": False,
            "waiting_for_approval": False,
            "waiting_for_chat_approval": False,
            "resume_from_approval": True
        }

        logger.info(f"🔄 Resuming workflow with {decision} decision...")

        try:
            config = {"configurable": {"thread_id": session_id}}
            final_state = await workflow_system.workflow.ainvoke(
                approval_input,
                config=config
            )

            # Update stored state
            workflow_system.active_workflows[session_id] = final_state

            # Send completion message
            await manager.send_json(client_id, {
                "type": "response",
                "agent": "orchestrator",
                "content": final_state.get("final_result", "Workflow completed after approval"),
                "metadata": {
                    "status": final_state.get("status"),
                    "approval_processed": True
                }
            })

            return  # Don't continue with normal chat processing
        except Exception as e:
            logger.error(f"Error processing chat approval: {e}")
            await manager.send_json(client_id, {
                "type": "error",
                "message": f"Error processing approval: {str(e)}"
            })
            return

    if not workflow_system:
        logger.error("❌ CRITICAL: workflow_system is None! Server may not have initialized correctly.")
        await manager.send_json(client_id, {
            "type": "error",
            "message": "Workflow system not initialized"
        })
        return

    logger.info(f"✅ workflow_system available: {type(workflow_system).__name__}")

    # Send thinking message
    logger.info(f"🔍 DEBUG: Starting LangGraph workflow for: {content[:100]}...")
    logger.info(f"🔍 DEBUG: Session state - plan_first_mode: {session.get('plan_first_mode')}, workspace: {session.get('workspace_path')}")
    logger.info(f"🔍 DEBUG: Plan-First mode: {session.get('plan_first_mode', False)}")
    await manager.send_json(client_id, {
        "type": "agent_thinking",
        "agent": "orchestrator",
        "message": f"🤔 Processing your request using LangGraph {__version_display__}..."
    })

    try:
        # Execute workflow
        logger.info(f"🔍 DEBUG: Executing LangGraph workflow")
        logger.info(f"🔍 DEBUG: Session ID: {session['session_id']}")
        logger.info(f"🔍 DEBUG: Workspace: {session.get('workspace_path', 'None')}")
        final_state = await workflow_system.execute(
            task=content,
            session_id=session["session_id"],
            client_id=client_id,
            workspace_path=session.get("workspace_path"),
            plan_first_mode=session.get("plan_first_mode", False),
            config={
                "debug_mode": data.get("debug", False)
            }
        )

        # Send progress updates during execution
        if final_state.get("execution_plan"):
            for step in final_state["execution_plan"]:
                if step.status == "completed":
                    await manager.send_json(client_id, {
                        "type": "step_completed",
                        "agent": step.agent,
                        "task": step.task,
                        "result": step.result
                    })

        # Send final result
        await manager.send_json(client_id, {
            "type": "response",
            "agent": "orchestrator",
            "content": final_state.get("final_result", "Task completed"),
            "metadata": {
                "execution_time": (
                    final_state["end_time"] - final_state["start_time"]
                ).total_seconds() if final_state.get("end_time") else None,
                "token_usage": final_state.get("token_usage"),
                "cost": final_state.get("cost"),
                "status": final_state.get("status")
            }
        })

        # Add to session messages
        session["messages"].append({
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        session["messages"].append({
            "role": "assistant",
            "content": final_state.get("final_result", "Task completed"),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        import traceback
        logger.error(f"❌ Error executing workflow: {e}")
        logger.error(f"📍 Full traceback:\n{traceback.format_exc()}")
        await manager.send_json(client_id, {
            "type": "error",
            "message": f"Error executing workflow: {str(e)}",
            "traceback": traceback.format_exc()
        })


# Dynamic workflow management endpoints
@app.post("/api/workflow/add_node")
async def add_workflow_node(name: str, node_type: str = "standard", description: str = ""):
    """Add a new node to the workflow dynamically"""
    if not workflow_system:
        raise HTTPException(status_code=503, detail="Workflow system not initialized")

    # This would need the actual node function
    # For now, return success
    return {
        "status": "success",
        "message": f"Node {name} added to workflow"
    }

@app.post("/api/workflow/add_edge")
async def add_workflow_edge(source: str, target: str):
    """Add an edge between workflow nodes"""
    if not workflow_system:
        raise HTTPException(status_code=503, detail="Workflow system not initialized")

    dynamic_manager = workflow_system.dynamic_manager
    success = dynamic_manager.add_edge(source, target)

    if success:
        return {
            "status": "success",
            "message": f"Edge added: {source} -> {target}"
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to add edge")

@app.post("/shutdown")
async def shutdown():
    """Gracefully shut down the server"""
    logger.info("📤 Received shutdown request - initiating graceful shutdown...")
    asyncio.create_task(shutdown_server())
    return {"status": "success", "message": "Shutdown initiated"}

async def shutdown_server():
    """Perform graceful shutdown"""
    await asyncio.sleep(0.5)  # Give time for response to be sent
    logger.info("👋 Gracefully shutting down KI AutoAgent Backend...")
    os._exit(0)


def main():
    """Main entry point"""
    import socket
    import requests
    import time

    # Check if KI Agent is already running
    def check_server_running(port):
        """Check if server is running on port"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0

    def graceful_shutdown(port):
        """Attempt graceful shutdown of running server"""
        try:
            # Try to send shutdown signal via HTTP
            response = requests.post(f"http://127.0.0.1:{port}/shutdown", timeout=2)
            if response.status_code == 200:
                logger.info(f"✅ Gracefully shut down server on port {port}")
                time.sleep(1)  # Give it time to shut down
                return True
        except:
            pass
        return False

    # Primary port for KI Agent
    primary_port = 8001

    # Check if server is already running
    if check_server_running(primary_port):
        logger.info(f"⚠️  KI Agent already running on port {primary_port}")
        logger.info("🔄 Attempting graceful shutdown...")

        if graceful_shutdown(primary_port):
            logger.info("✅ Previous instance shut down successfully")
        else:
            logger.warning("⚠️  Could not gracefully shut down. Using fallback port.")
            # Find alternative port if graceful shutdown failed
            for p in range(8002, 8010):
                if not check_server_running(p):
                    primary_port = p
                    logger.info(f"📍 Using fallback port {primary_port}")
                    break
            else:
                logger.error("❌ No available ports found (8001-8009 all in use)")
                sys.exit(1)

    port = primary_port
    logger.info(f"🚀 Starting server on port {port}")

    # Run the server
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level="info",
        reload=False,  # Disable reload for production
        log_config=None  # Use our basicConfig instead of uvicorn's default
    )


if __name__ == "__main__":
    main()