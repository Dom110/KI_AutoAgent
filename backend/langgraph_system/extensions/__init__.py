"""
Extensions for LangGraph system
Provides Tool Discovery, Approval, Memory, and Dynamic Workflow features

v5.8.3 Extensions:
- Supervisor Pattern: Formal supervisor-worker orchestration
- Agentic RAG: Agent-controlled code search and retrieval
"""

from .tool_discovery import ToolRegistry, tool, get_tool_registry
from .approval_manager import ApprovalManager
from .persistent_memory import PersistentAgentMemory
from .dynamic_workflow import DynamicWorkflowManager

# v5.8.3: Phase 3 extensions
try:
    from .supervisor import SupervisorOrchestrator, create_supervisor, WorkerReport
    from .agentic_rag import AgenticCodeRAG, agentic_code_search, AgenticSearchPlan
    SUPERVISOR_AVAILABLE = True
    AGENTIC_RAG_AVAILABLE = True
except ImportError as e:
    import logging
    logging.warning(f"Phase 3 extensions not available: {e}")
    SUPERVISOR_AVAILABLE = False
    AGENTIC_RAG_AVAILABLE = False
    SupervisorOrchestrator = None
    create_supervisor = None
    WorkerReport = None
    AgenticCodeRAG = None
    agentic_code_search = None
    AgenticSearchPlan = None

__all__ = [
    'ToolRegistry',
    'tool',
    'get_tool_registry',
    'ApprovalManager',
    'PersistentAgentMemory',
    'DynamicWorkflowManager',
    # v5.8.3 Phase 3
    'SupervisorOrchestrator',
    'create_supervisor',
    'WorkerReport',
    'AgenticCodeRAG',
    'agentic_code_search',
    'AgenticSearchPlan',
    'SUPERVISOR_AVAILABLE',
    'AGENTIC_RAG_AVAILABLE'
]