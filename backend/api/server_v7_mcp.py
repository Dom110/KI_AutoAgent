"""
⚠️ MCP BLEIBT: KI AutoAgent v7.0 Pure MCP Server
⚠️ WICHTIG: MCP BLEIBT! Alle Agent-Calls ausschließlich via MCP Protocol!

FastAPI server using Pure MCP architecture where ALL agents
are MCP servers communicating via JSON-RPC.

Key Changes from server_v7_supervisor.py:
- ALL agents are MCP servers (separate processes)
- Communication via JSON-RPC over stdin/stdout
- MCPManager orchestrates all agent calls
- Progress notifications via $/progress
- NO direct agent instantiation
- Pure MCP architecture!

Usage:
    python backend/api/server_v7_mcp.py

    WebSocket: ws://localhost:8002/ws/chat

Author: KI AutoAgent v7.0
Date: 2025-10-30
"""

from __future__ import annotations

# ============================================================================
# LOAD ENVIRONMENT VARIABLES FIRST!
# ============================================================================
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env BEFORE any checks
global_env = Path.home() / ".ki_autoagent" / "config" / ".env"
_env_loaded = False
if global_env.exists():
    load_dotenv(global_env)
    _env_loaded = True

# ============================================================================
# CRITICAL STARTUP CHECKS - MUST RUN FIRST!
# ============================================================================

# ✅ CHECK 1: PYTHON VERSION FIRST - MUST BE 3.13.8 OR HIGHER!
MIN_PYTHON_VERSION = (3, 13, 8)
current_version = sys.version_info[:3]

if current_version < MIN_PYTHON_VERSION:
    print("\n" + "=" * 80)
    print("❌ CRITICAL ERROR: PYTHON VERSION INCOMPATIBLE")
    print("=" * 80)
    print(f"\n📍 Current Python: {current_version[0]}.{current_version[1]}.{current_version[2]}")
    print(f"📍 Required: Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}.{MIN_PYTHON_VERSION[2]} or higher")
    print("\n⚠️  This project uses Python 3.13+ features:")
    print("   • Native type unions with | (not Union[])")
    print("   • Pattern matching (match/case)")
    print("   • Enhanced error messages")
    print("   • Modern asyncio features")
    
    print("\n✅ HOW TO FIX - Run from Virtual Environment:")
    print("\n   # Step 1: Go to project root")
    print("   cd /Users/dominikfoert/git/KI_AutoAgent")
    print("\n   # Step 2: Activate virtual environment")
    print("   source venv/bin/activate")
    print("\n   # Step 3: Install dependencies")
    print("   pip install -r backend/requirements.txt")
    print("\n   # Step 4: Start the server")
    print("   python backend/api/server_v7_mcp.py")
    
    print("\n" + "=" * 80)
    print("Server startup cancelled.")
    print("=" * 80 + "\n")
    
    # Import and show help message
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from backend.utils.error_handler import print_help_message_once
        print_help_message_once()
    except ImportError:
        pass
    
    sys.exit(1)

# ✅ CHECK 1.5: SERVER MUST BE STARTED VIA start_server.py SCRIPT
# This ensures all pre-flight checks run (port cleanup, diagnostics, etc.)
if os.environ.get('KI_AUTOAGENT_STARTUP_SCRIPT') != 'true':
    print("\n" + "=" * 80)
    print("❌ CRITICAL ERROR: DIRECT STARTUP NOT ALLOWED")
    print("=" * 80)
    
    print("\n🚫 PROBLEM:")
    print("   • Server cannot be started directly")
    print("   • Critical port management checks are skipped")
    print("   • System diagnostics are not run")
    print("   • Dependencies are not validated")
    print("   • Port conflicts are not detected/resolved")
    
    print("\n✅ HOW TO FIX - Start the server using the provided script:")
    print("\n   cd /Users/dominikfoert/git/KI_AutoAgent")
    print("   python start_server.py")
    
    print("\n📋 Script options:")
    print("   python start_server.py --check-only         # Run checks without starting")
    print("   python start_server.py --port 8003          # Use different port")
    print("   python start_server.py --no-cleanup         # Don't kill existing processes")
    
    print("\n❌ STARTUP BLOCKED")
    print("   Direct execution is not supported. Please use start_server.py")
    
    print("\n" + "=" * 80)
    print("Server startup cancelled.")
    print("=" * 80 + "\n")
    
    # Import and show help message
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from backend.utils.error_handler import print_help_message_once
        print_help_message_once()
    except ImportError:
        pass
    
    sys.exit(1)

# ✅ CHECK 2: SERVER MUST ALWAYS RUN FROM PROJECT ROOT
# This prevents agents from scanning their own codebase (infinite loop)
project_root_path = Path(__file__).parent.parent.parent  # /Users/dominikfoert/git/KI_AutoAgent
current_cwd = Path.cwd()

# 🚫 CRITICAL: Server MUST start from its own workspace!
if current_cwd != project_root_path:
    print("\n" + "=" * 80)
    print("❌ CRITICAL ERROR: SERVER MUST RUN FROM PROJECT ROOT")
    print("=" * 80)
    print(f"\n📍 Current working directory: {current_cwd}")
    print(f"📍 Required: {project_root_path}")
    
    print("\n🚫 PROBLEM:")
    print("   • Server can only be started from its own workspace")
    print("   • Running from other locations causes issues")
    print("   • Architect Agent must scan OTHER projects, not itself!")
    
    print("\n✅ HOW TO FIX:")
    print("\n   # Step 1: Go to project root")
    print("   cd /Users/dominikfoert/git/KI_AutoAgent")
    print("\n   # Step 2: Activate venv")
    print("   source venv/bin/activate")
    print("\n   # Step 3: Start the server")
    print("   python backend/api/server_v7_mcp.py")
    
    print("\n📝 NOTE: E2E Tests should connect via WebSocket ONLY")
    print("   • Tests run from: ~/TestApps/e2e_test_workspace")
    print("   • Tests connect to: ws://localhost:8002/ws/chat")
    print("   • Tests do NOT start the server!")
    
    print("\n" + "=" * 80)
    print("Server startup cancelled.")
    print("=" * 80 + "\n")
    
    # Import and show help message
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from backend.utils.error_handler import print_help_message_once
        print_help_message_once()
    except ImportError:
        pass
    
    sys.exit(1)

# ✅ Server is running from correct workspace - safe to proceed
project_root = str(project_root_path)
sys.path.insert(0, project_root)

# Now safe to import from backend
from backend.__version__ import __version__, __release_tag__

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
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketState

# ⚠️ MCP BLEIBT: Import v7.0 Pure MCP workflow
from backend.workflow_v7_mcp import execute_supervisor_workflow_mcp, execute_supervisor_workflow_streaming_mcp

# ⚠️ MCP BLEIBT: Import MCPManager for lifecycle management
from backend.utils.mcp_manager import get_mcp_manager, close_mcp_manager

# Import API validator utility (decentralized validation)
from backend.utils.api_validator import validate_all_required_keys

# Import session store for persistent sessions
from backend.utils.session_store import get_session_store

# Import health check system
from backend.utils.health_check import (
    run_startup_diagnostics,
    print_startup_header,
    print_ready_message,
    print_port_status,
    SystemDiagnostics
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True
)
logger = logging.getLogger(__name__)

# Store diagnostics globally for health check endpoints
_startup_diagnostics: Optional[SystemDiagnostics] = None

if _UVLOOP_INSTALLED:
    logger.info("⚡ uvloop ENABLED: Event loop performance boosted")
else:
    logger.warning("⚠️ uvloop NOT installed - using standard asyncio")

if _env_loaded:
    logger.info(f"✅ Loaded API keys from: {global_env}")
else:
    logger.warning(f"⚠️ .env not found at: {global_env}")

# ✅ Validate API keys on startup (centralized check from utility)
validate_all_required_keys()

# ============================================================================
# WORKSPACE ISOLATION - SECURITY FEATURE
# ============================================================================

# Get server root from environment (set by start_server.py)
SERVER_ROOT = os.environ.get('KI_AUTOAGENT_SERVER_ROOT')
if SERVER_ROOT:
    SERVER_ROOT = Path(SERVER_ROOT).resolve()
    logger.info(f"🔒 Workspace Isolation Enabled - Server Root: {SERVER_ROOT}")
else:
    logger.warning("⚠️ Server Root not set - Workspace isolation may not work properly")
    SERVER_ROOT = None


def validate_workspace_isolation(workspace_path: str) -> tuple[bool, str]:
    """
    Validate that client workspace is NOT inside the server's workspace.
    
    This prevents:
    - Accidental test execution within server code
    - Recursive/self-modification issues
    - Potential security issues
    
    Args:
        workspace_path: Client workspace path
        
    Returns:
        (is_valid, error_message)
        - is_valid=True if workspace is safe to use
        - is_valid=False + error_message if workspace is blocked
    """
    if not SERVER_ROOT:
        # If server root not configured, allow (non-fatal)
        logger.warning("⚠️ Server root not configured - allowing workspace (isolation disabled)")
        return True, ""
    
    try:
        # Normalize both paths to absolute paths
        client_workspace = Path(workspace_path).resolve()
        
        # Check if client workspace is inside server root
        # Using relative_to() will raise ValueError if paths are not relative
        try:
            relative = client_workspace.relative_to(SERVER_ROOT)
            # If we get here, client_workspace IS inside SERVER_ROOT
            return False, (
                f"❌ WORKSPACE ISOLATION VIOLATION\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Client workspace cannot be inside server workspace.\n\n"
                f"📍 Server Root:\n"
                f"   {SERVER_ROOT}\n\n"
                f"📍 Client Workspace:\n"
                f"   {client_workspace}\n\n"
                f"💡 Solution:\n"
                f"   Please start Tests outside Server workspace\n"
                f"   Example: /tmp, /Users/username/TestApps, /home/user/projects/\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
        except ValueError:
            # Paths are not relative - client is NOT inside server root
            # This is what we want!
            return True, ""
            
    except Exception as e:
        logger.error(f"❌ Error validating workspace isolation: {e}")
        return False, f"Error validating workspace path: {str(e)}"


# ============================================================================
# MCP ARCHITECTURE - NO AI FACTORY NEEDED!
# ============================================================================
logger.info("⚠️ MCP BLEIBT: Pure MCP architecture - agents are MCP servers!")
logger.info("   NO AI Factory initialization needed")
logger.info("   All agents run as separate MCP server processes")
logger.info("   Communication via JSON-RPC over stdin/stdout")
logger.info("   MCPManager will start all agents on first workflow execution")


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

# ⚠️ NEW: Initialize persistent session store
session_store = get_session_store()
logger.info(f"✅ Session store initialized: {len(session_store.get_all_sessions())} existing sessions")


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
    """
    ⚠️ MCP BLEIBT: Manage app lifecycle with MCP server management
    Includes port check and automatic cleanup if another server is running
    """
    global _startup_diagnostics
    
    # Print startup header
    print_startup_header()
    
    # Check port availability FIRST - auto-cleanup if needed
    logger.info("🔍 Checking server port...")
    print_port_status(port=8002, host="localhost")
    
    # Run comprehensive startup diagnostics (includes port cleanup)
    logger.info("🔍 Running startup diagnostics...")
    _startup_diagnostics = await run_startup_diagnostics()
    
    logger.info("🚀 Starting KI AutoAgent v7.0 Pure MCP Server...")
    logger.info("⚠️ MCP BLEIBT: Pure MCP Architecture Active!")
    logger.info("🎯 Architecture: Supervisor Pattern + Pure MCP Protocol")
    logger.info("📡 WebSocket endpoint: ws://localhost:8002/ws/chat")
    logger.info("✨ Key Features:")
    logger.info("   - Single LLM orchestrator (GPT-4o)")
    logger.info("   - ALL agents as MCP servers (JSON-RPC)")
    logger.info("   - Progress streaming via $/progress")
    logger.info("   - Command-based routing")
    logger.info("   - Research as support agent")
    logger.info("   - Responder-only user communication")
    logger.info("   - Dynamic instructions")
    logger.info("")
    logger.info("📋 MCP Servers (will start on first request):")
    logger.info("   - openai_server.py (OpenAI GPT-4o wrapper)")
    logger.info("   - research_agent_server.py")
    logger.info("   - architect_agent_server.py")
    logger.info("   - codesmith_agent_server.py")
    logger.info("   - reviewfix_agent_server.py")
    logger.info("   - responder_agent_server.py")
    logger.info("   + utility servers (perplexity, memory, etc.)")
    logger.info("")
    logger.info("⚠️ MCP BLEIBT: NO direct agent instantiation!")
    logger.info("⚠️ MCP BLEIBT: All communication via MCPManager!")
    
    # Print ready message if all critical checks pass
    if not _startup_diagnostics.errors:
        print_ready_message()

    yield

    # ⚠️ MCP BLEIBT: Shutdown MCP connections
    logger.info("🛑 Shutting down v7.0 Pure MCP Server...")
    logger.info("⚠️ MCP BLEIBT: Closing all MCP server connections...")
    try:
        await close_mcp_manager()
        logger.info("✅ MCP connections closed successfully")
    except Exception as e:
        logger.error(f"❌ Error closing MCP connections: {e}")
    logger.info("👋 Server shutdown complete")


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title=f"KI AutoAgent {__release_tag__} (Pure MCP)",
    description="⚠️ MCP BLEIBT: v7.0 Pure MCP Architecture - All agents as MCP servers",
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
    """
    ⚠️ MCP BLEIBT: Health check endpoint showing MCP architecture status
    """
    global _startup_diagnostics
    
    # Determine health status based on diagnostics
    health_status = "unhealthy"
    critical_errors = []
    
    if _startup_diagnostics:
        if not _startup_diagnostics.errors:
            health_status = "healthy"
        else:
            critical_errors = _startup_diagnostics.errors
    
    return {
        "status": health_status,
        "version": __version__,
        "release_tag": __release_tag__,
        "architecture": "pure_mcp",  # ⚠️ MCP BLEIBT!
        "mcp_active": True,
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(manager.active_connections),
        "active_sessions": len(active_sessions),
        "critical_errors": critical_errors,
        "warnings": _startup_diagnostics.warnings if _startup_diagnostics else []
    }


@app.get("/diagnostics")
async def get_diagnostics():
    """
    Full system diagnostics and health report
    Shows all system checks, API key status, dependencies, etc.
    """
    global _startup_diagnostics
    
    if not _startup_diagnostics:
        return {
            "status": "error",
            "message": "Diagnostics not yet available (server still initializing)",
            "timestamp": datetime.now().isoformat()
        }
    
    return {
        "status": "ok" if not _startup_diagnostics.errors else "failed",
        "timestamp": datetime.now().isoformat(),
        "checks": _startup_diagnostics.checks,
        "errors": _startup_diagnostics.errors,
        "warnings": _startup_diagnostics.warnings,
        "server_info": {
            "version": __version__,
            "release_tag": __release_tag__,
            "active_connections": len(manager.active_connections),
            "active_sessions": len(active_sessions),
            "uptime_seconds": (datetime.now() - _startup_diagnostics.startup_time).total_seconds()
        }
    }


@app.get("/api/v7/info")
async def get_v7_info():
    """
    ⚠️ MCP BLEIBT: Get v7.0 Pure MCP system information
    """
    return {
        "version": __version__,
        "architecture": "Pure MCP (Model Context Protocol)",
        "mcp_protocol_version": "2024-11-05",
        "agents": [
            "supervisor (GPT-4o orchestrator)",
            "research (via research_agent MCP server)",
            "architect (via architect_agent MCP server)",
            "codesmith (via codesmith_agent MCP server)",
            "reviewfix (via reviewfix_agent MCP server)",
            "responder (via responder_agent MCP server)",
            "hitl (special UI interaction)"
        ],
        "mcp_servers": [
            "openai_server.py",
            "research_agent_server.py",
            "architect_agent_server.py",
            "codesmith_agent_server.py",
            "reviewfix_agent_server.py",
            "responder_agent_server.py",
            "perplexity_server.py",
            "memory_server.py",
            "build_validation_server.py"
        ],
        "features": {
            "central_orchestration": True,
            "mcp_protocol": True,  # ⚠️ MCP BLEIBT!
            "json_rpc_communication": True,
            "progress_notifications": True,
            "command_routing": True,
            "research_requests": True,
            "self_invocation": True,
            "research_fix_loop": True,
            "dynamic_instructions": True,
            "subprocess_isolation": True
        },
        "asimov_rules": {
            "rule_1": "ReviewFix MANDATORY after code generation",
            "rule_2": "Architecture documentation required",
            "rule_3": "HITL on low confidence"
        },
        "mcp_benefits": {
            "industry_standard": "Anthropic, OpenAI, Google, Microsoft",
            "composability": "Swap AI providers easily",
            "observability": "Central progress monitoring",
            "security": "Process isolation per agent"
        }
    }


# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    ⚠️ MCP BLEIBT: Main WebSocket endpoint with v7.0 Pure MCP workflow

    ALL agent calls via MCP protocol - NO direct instantiation!
    """

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
            "message": f"⚠️ MCP BLEIBT: Connected to KI AutoAgent {__release_tag__} - Pure MCP Architecture",
            "session_id": session["session_id"],
            "client_id": client_id,
            "version": __version__,
            "release_tag": __release_tag__,
            "architecture": "pure_mcp",  # ⚠️ MCP BLEIBT!
            "mcp_protocol": "2024-11-05",
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

                # ✅ WORKSPACE ISOLATION CHECK - Prevent client workspace inside server workspace
                is_valid, error_message = validate_workspace_isolation(workspace_path)
                if not is_valid:
                    logger.error(f"🚫 SECURITY: Workspace Isolation Violation from {client_id}")
                    logger.error(f"   Attempted workspace: {workspace_path}")
                    logger.error(f"   Server root: {SERVER_ROOT}")
                    await manager.send_json(client_id, {
                        "type": "error",
                        "message": error_message,
                        "error_code": "WORKSPACE_ISOLATION_VIOLATION"
                    })
                    continue

                session["workspace_path"] = workspace_path
                session["initialized"] = True

                # ⚠️ NEW: Create persistent session
                persistent_session = session_store.create_session(
                    session_id=session["session_id"],
                    workspace_path=workspace_path,
                    client_id=client_id
                )

                logger.info(f"✅ Client {client_id} initialized with workspace: {workspace_path}")
                logger.info(f"   Session persisted: {session['session_id']}")

                await manager.send_json(client_id, {
                    "type": "initialized",
                    "session_id": session["session_id"],
                    "workspace_path": workspace_path,
                    "message": "⚠️ MCP BLEIBT: v7.0 Pure MCP workflow ready!",
                    "architecture": "pure_mcp",  # ⚠️ MCP BLEIBT!
                    "mcp_servers_available": [
                        "openai_server",
                        "research_agent_server",
                        "architect_agent_server",
                        "codesmith_agent_server",
                        "reviewfix_agent_server",
                        "responder_agent_server",
                        "perplexity_server",
                        "memory_server"
                    ],
                    "agents_available": [
                        "supervisor (GPT-4o)",
                        "research (MCP)",
                        "architect (MCP)",
                        "codesmith (MCP)",
                        "reviewfix (MCP)",
                        "responder (MCP)",
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
                logger.info("🔍 DEBUG: Entering chat message handler")
                # Support multiple field names for backward compatibility
                user_query = (
                    data.get("query") or  # Add support for "query" field!
                    data.get("content") or
                    data.get("message") or
                    data.get("task", "")
                )
                logger.info(f"🔍 DEBUG: user_query extracted: {user_query[:50] if user_query else 'EMPTY'}")
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

                logger.info("🔍 DEBUG: Before persisting user message")
                # ⚠️ NEW: Persist user message
                session_store.add_message(
                    session_id=session["session_id"],
                    role="user",
                    content=user_query
                )
                logger.info("🔍 DEBUG: User message persisted")

                logger.info("🔍 DEBUG: Before sending analyzing status")
                # Send "thinking" status
                await manager.send_json(client_id, {
                    "type": "status",
                    "status": "analyzing",
                    "message": "🎯 Supervisor analyzing request..."
                })
                logger.info("🔍 DEBUG: Analyzing status sent")

                logger.info("🔍 DEBUG: About to enter try block for workflow execution...")
                try:
                    logger.info("🔍 DEBUG: Inside try block")
                    logger.info(f"🚀 Running v7.0 Pure MCP workflow for: {user_query[:80]}...")
                    logger.info("⚠️ MCP BLEIBT: All agents will execute via MCP protocol!")

                    # Add debug logging
                    logger.info(f"   Workspace: {session['workspace_path']}")
                    logger.info(f"   Session ID: {session['session_id']}")
                    logger.info(f"   Client ID: {client_id}")

                    # DEBUG: Import check
                    logger.info("🔍 DEBUG: Importing workflow module...")
                    try:
                        from backend.workflow_v7_mcp import execute_supervisor_workflow_streaming_mcp
                        logger.info("✅ DEBUG: Workflow module imported successfully")
                    except Exception as import_error:
                        logger.error(f"❌ DEBUG: Import failed: {import_error}")
                        raise

                    # ⚠️ MCP BLEIBT: Execute workflow WITH STREAMING for real-time updates
                    # This will initialize MCPManager and start all MCP servers!
                    logger.info("🔍 DEBUG: Calling execute_supervisor_workflow_streaming_mcp...")
                    final_result = {}
                    async for event in execute_supervisor_workflow_streaming_mcp(
                        user_query=user_query,
                        workspace_path=session["workspace_path"],
                        session_id=session["session_id"]  # For event streaming
                    ):
                        # Forward workflow events to WebSocket client
                        event_type = event.get("type")

                        if event_type == "workflow_event":
                            # Send progress update to client
                            node = event.get("node", "unknown")
                            await manager.send_json(client_id, {
                                "type": "progress",
                                "node": node,
                                "message": f"⚠️ MCP: Executing {node} via MCP protocol...",
                                "architecture": "pure_mcp",
                                "timestamp": event.get("timestamp")
                            })

                            # Store state updates
                            state_update = event.get("state_update") or {}
                            if state_update:
                                final_result.update(state_update)

                        elif event_type == "mcp_progress":
                            # ⚠️ MCP BLEIBT: Forward MCP $/progress notifications!
                            await manager.send_json(client_id, {
                                "type": "mcp_progress",
                                "server": event.get("server"),
                                "message": event.get("message"),
                                "progress": event.get("progress"),
                                "timestamp": event.get("timestamp")
                            })

                        elif event_type == "agent_event":
                            # Forward agent event (think, progress, result, decision)
                            await manager.send_json(client_id, event)

                        elif event_type == "supervisor_event":
                            # Forward supervisor event (decision, routing, analysis)
                            await manager.send_json(client_id, event)

                        elif event_type == "workflow_complete":
                            # ⚠️ MCP BLEIBT: Workflow complete via Pure MCP!
                            await manager.send_json(client_id, {
                                "type": "workflow_complete",
                                "message": "✅ Pure MCP workflow completed successfully!",
                                "architecture": "pure_mcp",
                                "timestamp": event.get("timestamp")
                            })

                        elif event_type == "error":
                            # Handle error
                            error_msg = event.get("error", "Unknown error")
                            await manager.send_json(client_id, {
                                "type": "error",
                                "error": error_msg,
                                "timestamp": event.get("timestamp")
                            })
                            raise Exception(error_msg)

                    # Use final result
                    result = final_result

                    # Log what we got back
                    logger.info(f"   Workflow returned: {type(result)}")
                    if isinstance(result, dict):
                        logger.info(f"   Keys in result: {list(result.keys())}")
                        logger.info(f"   Response ready: {result.get('response_ready', False)}")
                        logger.info(f"   Last agent: {result.get('last_agent', 'None')}")

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

                    # ⚠️ NEW: Persist assistant message and workflow state
                    session_store.add_message(
                        session_id=session["session_id"],
                        role="assistant",
                        content=user_response
                    )
                    session_store.update_session(
                        session_id=session["session_id"],
                        updates={
                            "conversation_state": {
                                "last_agent": result.get("last_agent"),
                                "response_ready": result.get("response_ready", False),
                                "validation_passed": result.get("validation_passed", False),
                                "iteration": result.get("iteration", 0)
                            }
                        }
                    )

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
    logger.info("="*60)
    logger.info("⚠️ MCP BLEIBT: Starting Pure MCP Server")
    logger.info("="*60)
    uvicorn.run(
        "server_v7_mcp:app",  # ⚠️ MCP BLEIBT: Changed module name!
        host="0.0.0.0",
        port=8002,
        reload=False,
        log_level="info"
    )