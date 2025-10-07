"""
BaseAgent - Modern base class for all agents with Memory, SharedContext, and Communication
Inspired by the TypeScript implementation with all advanced features
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging
import json
import os
import sys
from enum import Enum

# Import custom exceptions
from core.exceptions import (
    AgentError,
    WorkflowError,
    ParsingError,
    DataValidationError
)

if TYPE_CHECKING:
    from agents.tools.file_tools import FileSystemTools

# Import Settings for German language support
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
try:
    from config.settings import settings
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False
    logging.warning("Settings not available - using defaults")

# Import core systems
try:
    from core.memory_manager import get_memory_manager
    from core.shared_context_manager import get_shared_context
    from core.conversation_context_manager import get_conversation_context
    CORE_SYSTEMS_AVAILABLE = True
except ImportError:
    CORE_SYSTEMS_AVAILABLE = False
    logging.warning("Core systems (Memory, Context) not available")

# Import Prime Directives
try:
    from .prime_directives import PrimeDirectives
    PRIME_DIRECTIVES_AVAILABLE = True
except ImportError:
    PRIME_DIRECTIVES_AVAILABLE = False
    logging.warning("Prime Directives not available")

# Import Pause and Git managers
try:
    from core.pause_handler import PauseHandler, PauseAction
    from core.git_checkpoint_manager import GitCheckpointManager
    PAUSE_AVAILABLE = True
except ImportError:
    PAUSE_AVAILABLE = False
    logging.warning("Pause and Git checkpoint systems not available")

# Import File System Tools
try:
    from agents.tools.file_tools import FileSystemTools
    FILE_TOOLS_AVAILABLE = True
except ImportError:
    FILE_TOOLS_AVAILABLE = False
    logging.warning("File system tools not available")

# Setup logging
logger = logging.getLogger(__name__)

class AgentCapability(Enum):
    """Agent capabilities enum"""
    TASK_DECOMPOSITION = "task_decomposition"
    PARALLEL_EXECUTION = "parallel_execution"
    CODE_GENERATION = "code_generation"
    ARCHITECTURE_DESIGN = "architecture_design"
    CONFLICT_RESOLUTION = "conflict_resolution"
    WEB_RESEARCH = "web_research"
    CODE_REVIEW = "code_review"
    DOCUMENTATION = "documentation"
    BUG_FIXING = "bug_fixing"
    SECURITY_ANALYSIS = "security_analysis"
    WEB_SEARCH = "web_search"
    RESEARCH = "research"

@dataclass
class AgentConfig:
    """Agent configuration"""
    agent_id: str
    name: str
    full_name: str
    description: str
    model: str
    capabilities: list[AgentCapability] = field(default_factory=list)
    temperature: float = 0.7
    max_tokens: int = 4000
    instructions_path: str | None = None
    icon: str = "🤖"

@dataclass
class TaskRequest:
    """Task request structure"""
    prompt: str
    context: dict[str, Any] = field(default_factory=dict)
    command: str | None = None
    project_type: str | None = None
    global_context: str | None = None
    conversation_history: list[dict[str, Any]] = field(default_factory=list)
    thinking_mode: bool = False
    mode: str = "auto"
    agent: str | None = None

@dataclass
class TaskResult:
    """Task execution result"""
    status: str  # 'success', 'error', 'partial_success'
    content: str
    agent: str
    suggestions: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    tokens_used: int = 0

@dataclass
class AgentMessage:
    """Inter-agent communication message"""
    from_agent: str
    to_agent: str
    message_type: str  # 'request', 'response', 'broadcast', 'help_request'
    content: Any
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: str | None = None

class BaseAgent(ABC):
    """
    Modern base class for all agents with advanced features:
    - Memory management (episodic, semantic, procedural)
    - Shared context for collaboration
    - Inter-agent communication bus
    - Pattern recognition and learning
    - Streaming support
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.name = config.name
        self.role = config.description  # Add role attribute
        self.model = config.model
        self.instructions = self._load_instructions()

        # Add German language directive to all prompts
        self.language_directive = self._get_language_directive()

        # Execution tracking
        self.execution_count = 0
        self.total_tokens_used = 0
        self.last_execution_time = None

        # Cancellation support
        self.cancel_token = None

        # v5.8.1: Track current request for workspace context
        self._current_request = None

        # Initialize core systems if available
        if CORE_SYSTEMS_AVAILABLE:
            self.memory_manager = get_memory_manager()
            self.shared_context = get_shared_context()
            self.conversation = get_conversation_context()
        else:
            self.memory_manager = None
            self.shared_context = None
            self.conversation = None

        # v5.9.0: Initialize Predictive Learning System
        try:
            from langgraph_system.extensions.predictive_learning import PredictiveMemory
            storage_path = os.path.join(os.path.expanduser("~/.ki_autoagent/data/predictive"), f"{config.name}_predictions.json")
            os.makedirs(os.path.dirname(storage_path), exist_ok=True)
            self.predictive_memory = PredictiveMemory(agent_name=config.name, storage_path=storage_path)
            self.predictive_memory.load_from_disk()
            logging.info(f"✨ Predictive Learning enabled for {config.name}")
        except Exception as e:
            self.predictive_memory = None
            logging.warning(f"⚠️ Predictive Learning not available: {e}")

        # v5.9.0: Initialize Curiosity-Driven Exploration System
        try:
            from langgraph_system.extensions.curiosity_system import CuriosityModule
            storage_path = os.path.join(os.path.expanduser("~/.ki_autoagent/data/curiosity"), f"{config.name}_curiosity.json")
            os.makedirs(os.path.dirname(storage_path), exist_ok=True)
            # Pass embedding function if available
            embedding_fn = None
            if hasattr(self, 'openai') and hasattr(self.openai, 'get_embedding'):
                embedding_fn = self.openai.get_embedding
            self.curiosity_module = CuriosityModule(
                agent_name=config.name,
                storage_path=storage_path,
                embedding_function=embedding_fn
            )
            self.curiosity_module.load_from_disk()
            logging.info(f"🔍 Curiosity-Driven Exploration enabled for {config.name}")
        except Exception as e:
            self.curiosity_module = None
            logging.warning(f"⚠️ Curiosity-Driven Exploration not available: {e}")

        # v5.9.0: Initialize Neurosymbolic Reasoning System
        try:
            from langgraph_system.extensions.neurosymbolic_reasoning import NeurosymbolicReasoner
            # Pass LLM function if available (for neural reasoning)
            llm_fn = None
            if hasattr(self, 'openai') and hasattr(self.openai, 'complete'):
                llm_fn = lambda prompt, ctx: self.openai.complete(prompt)
            self.neurosymbolic_reasoner = NeurosymbolicReasoner(
                agent_name=config.name,
                llm_function=llm_fn
            )
            logging.info(f"🧠 Neurosymbolic Reasoning enabled for {config.name}")
        except Exception as e:
            self.neurosymbolic_reasoner = None
            logging.warning(f"⚠️ Neurosymbolic Reasoning not available: {e}")

        # v5.9.0: Initialize Framework Comparison System (for Architect mainly)
        try:
            from langgraph_system.extensions.framework_comparison import FrameworkComparator
            self.framework_comparator = FrameworkComparator()
            logging.info(f"🔍 Framework Comparison (Systemvergleich) enabled for {config.name}")
        except Exception as e:
            self.framework_comparator = None
            logging.warning(f"⚠️ Framework Comparison not available: {e}")

        # Communication bus (will be initialized separately)
        self.communication_bus = None

        # Collaboration
        self.collaboration_sessions: set[str] = set()
        self.active_help_requests: dict[str, AgentMessage] = {}

        # Initialize pause and git checkpoint systems if available
        if PAUSE_AVAILABLE:
            from pathlib import Path
            project_path = str(Path.cwd())
            self.pause_handler = PauseHandler(project_path)
            self.git_manager = GitCheckpointManager(project_path)
        else:
            self.pause_handler = None
            self.git_manager = None

        # Initialize File System Tools if available
        if FILE_TOOLS_AVAILABLE:
            workspace_path = getattr(config, 'workspace_path', os.getcwd())
            self.file_tools = FileSystemTools(workspace_path)

            # Get write capabilities from config
            # Handle both list and dict format for capabilities
            if hasattr(config, 'capabilities'):
                if isinstance(config.capabilities, dict):
                    self.can_write = config.capabilities.get('file_write', False)
                    self.allowed_paths = config.capabilities.get('allowed_paths', [])
                else:
                    # capabilities is a list (old format)
                    self.can_write = False
                    self.allowed_paths = []
            else:
                self.can_write = False
                self.allowed_paths = []
        else:
            self.file_tools = None
            self.can_write = False
            self.allowed_paths = []

        # WebSocket callback for pause notifications (will be set by server)
        self.websocket_callback = None

        # Pattern library
        self.code_patterns: list[dict[str, Any]] = []
        self.architecture_patterns: list[dict[str, Any]] = []

        # Initialize pause and git managers if available
        if PAUSE_AVAILABLE:
            self.pause_handler = PauseHandler()
            self.git_manager = GitCheckpointManager()
        else:
            self.pause_handler = None
            self.git_manager = None

        logger.info(f"🤖 {self.config.icon} {self.name} initialized (Model: {self.model})")

    def _load_instructions(self) -> str:
        """
        Load agent instructions with two-tier system (v5.8.0).

        1. Base instructions (required) from $HOME/.ki_autoagent/config/instructions/
           - Agent identity, core capabilities, base behavior
        2. Project instructions (optional) from $WORKSPACE/.ki_autoagent_ws/instructions/
           - Project-specific rules, style guides, custom behavior

        Returns merged instructions: Base + Project (if available)
        """
        if not self.config.instructions_path:
            return ""

        # Extract filename from instructions_path
        # e.g. ".ki_autoagent/instructions/architect-v2-instructions.md" → "architect-v2-instructions.md"
        instructions_filename = os.path.basename(self.config.instructions_path)

        # 1. Load base instructions from global config
        home_dir = os.path.expanduser("~")

        # Try both .ki_autoagent (new) and .ki-autoagent (legacy for backwards compatibility)
        base_instructions_paths = [
            os.path.join(home_dir, ".ki_autoagent", "config", "instructions", instructions_filename),
            os.path.join(home_dir, ".ki-autoagent", "config", "instructions", instructions_filename),
        ]

        base_instructions = None
        base_path_used = None

        for base_path in base_instructions_paths:
            if os.path.exists(base_path):
                try:
                    with open(base_path, 'r', encoding='utf-8') as f:
                        base_instructions = f.read()
                        base_path_used = base_path
                        logger.info(f"✅ Base instructions loaded: {base_path}")
                        break
                except Exception as e:
                    logger.warning(f"Error reading base instructions from {base_path}: {e}")

        if not base_instructions:
            logger.warning(
                f"Base instructions not found for {self.name}. "
                f"Tried: {base_instructions_paths}"
            )
            return ""

        # 2. Try to load project-specific instructions (optional)
        workspace_path = os.getenv("KI_WORKSPACE_PATH")

        if workspace_path:
            # Extract agent ID from filename
            # e.g. "architect-v2-instructions.md" → "architect"
            agent_id = instructions_filename.split('-')[0]

            project_instructions_paths = [
                os.path.join(workspace_path, ".ki_autoagent_ws", "instructions", f"{agent_id}-custom.md"),
                os.path.join(workspace_path, ".kiautoagent", "instructions", f"{agent_id}-custom.md"),  # Legacy
            ]

            for project_path in project_instructions_paths:
                if os.path.exists(project_path):
                    try:
                        with open(project_path, 'r', encoding='utf-8') as f:
                            project_instructions = f.read()
                            logger.info(f"✅ Project instructions loaded: {project_path}")

                            # Merge: Base + Project
                            return (
                                f"{base_instructions}\n\n"
                                f"{'='*80}\n"
                                f"# PROJECT-SPECIFIC INSTRUCTIONS\n"
                                f"{'='*80}\n\n"
                                f"{project_instructions}"
                            )
                    except Exception as e:
                        logger.warning(f"Error reading project instructions from {project_path}: {e}")

        # Return base instructions only (no project-specific found)
        return base_instructions

    def _get_language_directive(self) -> str:
        """Get language directive based on settings"""
        if SETTINGS_AVAILABLE:
            return settings.get_language_directive()
        else:
            # Default to German if settings not available
            return """
🇩🇪 KRITISCHE REGEL:
Du MUSST IMMER auf Deutsch antworten, egal in welcher Sprache die Frage gestellt wird.
Dies gilt für ALLE Antworten, Erklärungen, Fehlermeldungen und Ausgaben.
"""

    def get_system_prompt(self) -> str:
        """Get complete system prompt with language directive"""
        base_prompt = self.instructions if self.instructions else f"Du bist {self.name}, ein {self.role}."
        return f"{self.language_directive}\n\n{base_prompt}"

    async def initialize_systems(self, memory_manager=None, shared_context=None, communication_bus=None):
        """Initialize external systems after construction"""
        self.memory_manager = memory_manager
        self.shared_context = shared_context
        self.communication_bus = communication_bus

        if self.communication_bus:
            await self._register_communication_handlers()

    async def _register_communication_handlers(self):
        """Register handlers for inter-agent communication"""
        if not self.communication_bus:
            return

        # Subscribe to messages for this agent
        await self.communication_bus.subscribe(
            f"agent.{self.config.agent_id}",
            self._handle_agent_message
        )

        # Subscribe to broadcast messages
        await self.communication_bus.subscribe(
            "agent.broadcast",
            self._handle_broadcast
        )

        # Subscribe to help requests
        await self.communication_bus.subscribe(
            "agent.help_request",
            self._handle_help_request
        )

    async def _handle_agent_message(self, message: AgentMessage):
        """Handle direct message from another agent"""
        logger.info(f"📨 {self.name} received message from {message.from_agent}")

        if message.message_type == "request":
            response = await self._process_agent_request(message)
            await self.send_response(message.from_agent, response, message.correlation_id)
        elif message.message_type == "response":
            await self._process_agent_response(message)

    async def _handle_broadcast(self, message: AgentMessage):
        """Handle broadcast message"""
        logger.info(f"📢 {self.name} received broadcast from {message.from_agent}")
        await self._process_broadcast(message)

    async def _handle_help_request(self, message: AgentMessage):
        """Handle help request from another agent"""
        if message.from_agent == self.config.agent_id:
            return  # Don't respond to own help requests

        logger.info(f"🆘 {self.name} received help request from {message.from_agent}")

        # Check if we can help
        if await self._can_help_with(message.content):
            await self.send_response(
                message.from_agent,
                await self._provide_help(message.content),
                message.correlation_id
            )

    @abstractmethod
    async def execute(self, request: TaskRequest) -> TaskResult:
        """Execute a task - must be implemented by subclasses"""
        pass

    async def execute_with_memory(self, request: TaskRequest) -> TaskResult:
        """Execute task with memory enhancement, context integration, and PRIME DIRECTIVES"""
        start_time = datetime.now()
        execution_time = 0  # Initialize to prevent UnboundLocalError

        # v5.8.1: Store current request for workspace context access
        self._current_request = request

        # 🔴 APPLY ASIMOV RULES (via Neurosymbolic Reasoning) - These override everything
        if self.neurosymbolic_reasoner:
            # Build context for rule evaluation
            reasoning_context = {
                'task': request.prompt,
                'agent': self.name,
                'context': request.context or {}
            }

            # Apply Neurosymbolic Reasoning (includes Asimov Rules)
            reasoning_result = self.neurosymbolic_reasoner.reason(
                task=request.prompt,
                context=reasoning_context
            )

            # 🔴 ASIMOV CONSTRAINT VIOLATIONS - FAIL FAST
            if reasoning_result['symbolic_results']['constraints_violated']:
                logger.error(f"🔴 ASIMOV RULE VIOLATION detected for {self.name}")
                violations_text = "\n".join([
                    f"❌ {v['rule']}: {v['message']}"
                    for v in reasoning_result['symbolic_results']['constraints_violated']
                ])

                execution_time = (datetime.now() - start_time).total_seconds()
                return TaskResult(
                    agent_id=self.config.agent_id,
                    agent=self.name,
                    content=f"🔴 ASIMOV RULE VIOLATION:\n\n{violations_text}\n\nTask cannot proceed. Asimov Rules are ABSOLUTE and INVIOLABLE.",
                    status='asimov_violation',
                    metadata={'asimov_violation': True, 'violations': reasoning_result['symbolic_results']['constraints_violated']},
                    execution_time=execution_time
                )

            # 🔴 RESEARCH REQUIRED (Asimov Rule 7)
            research_required = any(
                action.get('action_type') == 'require' and 'research' in str(action.get('description', '')).lower()
                for action in reasoning_result['symbolic_results'].get('actions_taken', [])
            )

            if research_required and not reasoning_context['context'].get('research_performed'):
                logger.info(f"📚 ASIMOV RULE 7: Research required before claiming knowledge")

                # Perform mandatory research
                research_results = await self._perform_mandatory_research(
                    request.prompt,
                    topics=['latest_practices', 'verify_technology'],
                    technologies_to_verify=[]
                )

                # Add research to context
                if not request.context:
                    request.context = {}
                request.context['research_completed'] = True
                request.context['research_results'] = research_results
                logger.info(f"✅ Research completed. Found {len(research_results.get('findings', []))} relevant findings")

            # ⚠️ WARNINGS (e.g., Asimov Rule 5: Challenge Misconceptions)
            if reasoning_result['symbolic_results'].get('warnings'):
                warnings_text = "\n".join([
                    f"⚠️ {w['rule']}: {w['warning']}"
                    for w in reasoning_result['symbolic_results']['warnings']
                ])
                logger.warning(f"⚠️ Asimov Rule Warnings:\n{warnings_text}")

                # Return challenge to user
                execution_time = (datetime.now() - start_time).total_seconds()
                return TaskResult(
                    agent_id=self.config.agent_id,
                    agent=self.name,
                    content=f"🤔 I need to clarify before proceeding:\n\n{warnings_text}\n\nCould you please confirm or provide more details?",
                    status='challenge',
                    metadata={'asimov_challenge': True, 'warnings': reasoning_result['symbolic_results']['warnings']},
                    execution_time=execution_time
                )

        # Check for cancellation at start
        if self.cancel_token and self.cancel_token.is_cancelled:
            logger.info(f"Task cancelled for {self.name}")
            return TaskResult(
                agent=self.name,
                content="Task was cancelled by user",
                status="cancelled",
                execution_time=0
            )

        # Search memory for similar tasks
        if self.memory_manager:
            similar_tasks = await self.memory_manager.search(
                request.prompt,
                memory_type="episodic",
                agent_id=self.config.agent_id,
                k=5
            )
            request.context["similar_tasks"] = [
                {"content": task.entry.content, "relevance": task.relevance}
                for task in similar_tasks
            ]

            # Get relevant patterns
            patterns = await self.memory_manager.get_relevant_patterns(
                context=request.prompt,
                limit=3
            )
            if patterns:
                request.context["patterns"] = patterns

        # Get conversation context
        if self.conversation:
            conv_context = self.conversation.get_context_for_agent(
                self.config.agent_id,
                include_self=False,
                limit=5
            )
            if conv_context:
                request.context["conversation"] = conv_context

        # Update shared context
        if self.shared_context:
            await self.shared_context.update_context(
                self.config.agent_id,
                "agent_status",
                {"status": "executing", "task": request.prompt[:100]},
                metadata={"timestamp": datetime.now().isoformat()}
            )

        # Check cancellation before execution
        if self.cancel_token and self.cancel_token.is_cancelled:
            logger.info(f"Task cancelled for {self.name} before execution")
            return TaskResult(
                agent=self.name,
                content="Task was cancelled by user",
                status="cancelled",
                execution_time=(datetime.now() - start_time).total_seconds()
            )

        # Execute the task
        try:
            result = await self.execute(request)

            # Check if pause was requested during execution
            if self.pause_handler and self.pause_handler.is_paused():
                # Wait for user action (resume/stop/add instructions)
                user_action = await self.pause_handler.wait_for_user_action()

                if user_action == PauseAction.STOP_AND_ROLLBACK:
                    # Stop and rollback
                    rollback_result = await self.pause_handler.stop_and_rollback()
                    return TaskResult(
                        agent=self.name,
                        content=f"Task stopped and rolled back: {rollback_result['message']}",
                        status="stopped",
                        execution_time=(datetime.now() - start_time).total_seconds()
                    )
                elif user_action == PauseAction.RESUME_WITH_INSTRUCTIONS:
                    # Get updated task with additional instructions
                    pause_state = self.pause_handler.pause_state
                    if pause_state.additional_instructions:
                        # Update the task with new instructions
                        request.prompt = pause_state.task_description  # Updated task
                        # Continue execution with updated task
                        result = await self.execute(request)
        except asyncio.CancelledError:
            logger.info(f"Task cancelled during execution for {self.name}")
            return TaskResult(
                agent=self.name,
                content="Task was cancelled during execution",
                status="cancelled",
                execution_time=(datetime.now() - start_time).total_seconds()
            )

        # Calculate execution time IMMEDIATELY after execution
        execution_time = (datetime.now() - start_time).total_seconds()
        result.execution_time = execution_time

        # Store in memory
        # v5.5.3: Wrap in try/except to prevent corrupting results
        if self.memory_manager:
            try:
                # Modern signature: store(content, memory_type, ...)
                memory_data = {
                    "agent": self.config.agent_id,
                    "task": request.prompt,
                    "result": result.content[:2000],
                    "status": result.status,
                    "importance": 0.7 if result.status == "success" else 0.5,
                    "tags": ["task_result", self.config.agent_id]
                }
                self.memory_manager.store(
                    content=json.dumps(memory_data),
                    memory_type="procedural",  # WORKING → procedural
                    importance=0.7 if result.status == "success" else 0.5,
                    metadata=memory_data
                )
            except Exception as mem_error:
                logger.warning(f"⚠️ Memory storage failed (non-critical): {mem_error}")

            # Store successful patterns
            if result.status == "success" and "code" in result.content.lower():
                # Extract and store code patterns if applicable
                self.memory_manager.store_code_pattern(
                    name=f"Pattern_{self.config.agent_id}_{self.execution_count}",
                    description=request.prompt[:100],
                    language="python",  # Default, could be detected
                    code=result.content[:1000],
                    use_cases=[request.prompt[:50]]
                )

        # Update conversation context
        if self.conversation:
            self.conversation.add_entry(
                agent=self.config.agent_id,
                step="execute",
                input_text=request.prompt,
                output_text=result.content,
                metadata=result.metadata,
                tokens_used=result.tokens_used,
                execution_time=execution_time
            )

        # Update shared context with result
        if self.shared_context:
            await self.shared_context.update_context(
                self.config.agent_id,
                f"agent_output_{self.config.agent_id}",
                {
                    "result": result.content[:500],  # Store summary
                    "status": result.status,
                    "timestamp": datetime.now().isoformat()
                },
                metadata={"execution_time": execution_time}
            )

        # Update tracking
        self.execution_count += 1
        self.total_tokens_used += result.tokens_used
        self.last_execution_time = datetime.now()

        # Create Git checkpoint if task completed successfully
        if self.git_manager and result.status == "success":
            try:
                checkpoint_result = await self.git_manager.create_checkpoint(
                    task_description=request.prompt[:200],  # Limit description length
                    task_id=f"{self.config.agent_id}_{self.execution_count}"
                )
                if checkpoint_result['status'] == 'success':
                    logger.info(f"✅ Git checkpoint created: {checkpoint_result['commit_hash'][:8]}")
                    result.metadata['git_checkpoint'] = checkpoint_result['commit_hash']
            except Exception as e:
                logger.warning(f"Could not create Git checkpoint: {e}")
                # ASIMOV RULE 1: No silent failure - log but continue
                # Task completed successfully, checkpoint is optional safety

        return result

    def calculate_dynamic_timeout(self, prompt: str, context: dict[str, Any | None] = None) -> float:
        """
        Calculate dynamic timeout based on task complexity and keywords
        Returns timeout in seconds
        """
        # Default timeout
        timeout = 60.0

        # Keywords that indicate complex tasks needing more time
        complex_keywords = {
            'analyze': 180.0,
            'analyse': 180.0,  # German variant
            'architecture': 180.0,
            'infrastructure': 240.0,
            'improve': 180.0,
            'verbessern': 180.0,  # German: improve
            'system': 150.0,
            'complex': 180.0,
            'komplex': 180.0,  # German: complex
            'comprehensive': 240.0,
            'umfassend': 240.0,  # German: comprehensive
            'refactor': 180.0,
            'optimize': 180.0,
            'optimieren': 180.0,  # German: optimize
            'research': 150.0,
            'forschen': 150.0,  # German: research
            'understand': 180.0,
            'verstehen': 180.0,  # German: understand
            'debug': 150.0,
            'security': 180.0,
            'sicherheit': 180.0,  # German: security
            'review': 150.0,
            'überprüfen': 150.0,  # German: review
        }

        # Keywords for simpler tasks
        simple_keywords = {
            'list': 30.0,
            'show': 30.0,
            'zeigen': 30.0,  # German: show
            'get': 30.0,
            'holen': 30.0,  # German: get
            'check': 45.0,
            'prüfen': 45.0,  # German: check
            'status': 30.0,
            'count': 30.0,
            'zählen': 30.0,  # German: count
        }

        prompt_lower = prompt.lower()

        # Check for complex keywords (take the maximum timeout found)
        for keyword, keyword_timeout in complex_keywords.items():
            if keyword in prompt_lower:
                timeout = max(timeout, keyword_timeout)

        # If no complex keywords, check for simple keywords (take the minimum)
        if timeout == 60.0:
            for keyword, keyword_timeout in simple_keywords.items():
                if keyword in prompt_lower:
                    timeout = min(timeout, keyword_timeout)

        # Consider prompt length
        if len(prompt) > 1000:
            timeout = max(timeout, 180.0)
        elif len(prompt) > 500:
            timeout = max(timeout, 120.0)

        # Consider context size if available
        if context and 'files' in context and len(context.get('files', [])) > 10:
            timeout = max(timeout, 180.0)

        # Apply minimum and maximum bounds
        timeout = max(30.0, min(timeout, 300.0))

        logger.info(f"⏱️ Dynamic timeout calculated: {timeout}s for prompt length {len(prompt)}")
        return timeout

    def _get_workspace_from_request(self) -> str | None:
        """
        Get workspace_path from current request context (v5.8.1)

        Returns:
            Workspace path from request.context or None
        """
        if self._current_request and self._current_request.context:
            return self._current_request.context.get('workspace_path')
        return None

    def _get_file_tools_for_current_workspace(self) -> 'FileSystemTools | None':
        """
        Get FileSystemTools instance with correct workspace from request context (v5.8.1)

        Returns:
            FileSystemTools with workspace from request.context, or default self.file_tools
        """
        workspace = self._get_workspace_from_request()
        if workspace and FILE_TOOLS_AVAILABLE:
            from agents.tools.file_tools import FileSystemTools
            logger.info(f"📂 Using workspace from request.context: {workspace}")
            return FileSystemTools(workspace)
        return self.file_tools

    async def write_implementation(self, file_path: str, content: str, create_dirs: bool = True) -> dict[str, Any]:
        """
        Write implementation to file with proper validation and error handling

        Args:
            file_path: Path to file (relative to workspace)
            content: Content to write
            create_dirs: Create parent directories if needed

        Returns:
            Dict with status and details
        """
        # v5.8.1: Use workspace-aware file tools
        file_tools = self._get_file_tools_for_current_workspace()

        if not file_tools:
            error_msg = f"❌ File system tools not available for {self.name}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "agent": self.name
            }

        if not self.can_write:
            error_msg = f"❌ Agent {self.name} has no write permissions"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "agent": self.name
            }

        try:
            # v5.8.1: Use workspace-aware file tools (not self.file_tools!)
            result = await file_tools.write_file(
                path=file_path,
                content=content,
                agent_name=self.name,
                allowed_paths=self.allowed_paths,
                create_dirs=create_dirs
            )

            if result.get('status') == 'success':
                logger.info(f"✅ {self.name} successfully wrote to {file_path}")
                # Track in memory if available
                # v5.5.3: Wrap memory storage in try/except to not corrupt the result
                if self.memory_manager:
                    try:
                        # Modern signature: store(content, memory_type, ...)
                        memory_data = {
                            "action": "file_write",
                            "path": file_path,
                            "size": result.get('size', 0),
                            "agent": self.config.agent_id,
                            "timestamp": datetime.now().isoformat()
                        }
                        self.memory_manager.store(
                            content=json.dumps(memory_data),
                            memory_type="procedural",  # WORKING → procedural
                            importance=0.6,
                            metadata=memory_data
                        )
                    except Exception as mem_error:
                        logger.warning(f"⚠️ Memory storage failed (non-critical): {mem_error}")
            else:
                logger.error(f"❌ {self.name} failed to write to {file_path}: {result.get('error')}")

            return result

        except Exception as e:
            error_msg = f"Exception during file write: {str(e)}"
            logger.error(f"❌ {self.name} - {error_msg}")
            return {
                "status": "error",
                "error": error_msg,
                "agent": self.name,
                "path": file_path
            }

    async def create_file(self, file_path: str, content: str, overwrite: bool = False) -> dict[str, Any]:
        """
        Create a new file with content

        Args:
            file_path: Path to file (relative to workspace)
            content: Content to write
            overwrite: Allow overwriting existing file

        Returns:
            Dict with status and details
        """
        # v5.8.1: Use workspace-aware file tools
        file_tools = self._get_file_tools_for_current_workspace()

        if not file_tools:
            return {
                "status": "error",
                "error": "File system tools not available",
                "agent": self.name
            }

        if not self.can_write:
            return {
                "status": "error",
                "error": f"Agent {self.name} has no write permissions",
                "agent": self.name
            }

        try:
            # v5.8.1: Use workspace-aware file tools (not self.file_tools!)
            result = await file_tools.create_file(
                path=file_path,
                content=content,
                agent_name=self.name,
                allowed_paths=self.allowed_paths,
                overwrite=overwrite
            )
            return result
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "agent": self.name,
                "path": file_path
            }

    async def _perform_mandatory_research(self, prompt: str, topics: list, technologies: list) -> dict[str, Any]:
        """
        Perform mandatory research as required by Prime Directive 4
        This method calls the ResearchAgent to gather information
        """
        try:
            # Import research agent
            from agents.specialized.research_agent import ResearchAgent
            research_agent = ResearchAgent()

            findings = []

            # Research each topic
            for topic in topics:
                logger.info(f"🔍 Researching topic: {topic}")

                if topic == 'latest_practices':
                    # Get latest best practices
                    result = await research_agent.get_latest_best_practices(prompt)
                    findings.append({
                        'type': 'best_practices',
                        'data': result
                    })

                elif topic == 'verify_technologies':
                    # Verify each technology
                    for tech in technologies:
                        verification = await research_agent.verify_technology_exists(tech)
                        findings.append({
                            'type': 'technology_verification',
                            'technology': tech,
                            'data': verification
                        })

                elif topic in ['comparison', 'technology_choice']:
                    # Research comparison
                    research = await research_agent.research_for_agent(
                        self.config.agent_id,
                        f"Compare options for: {prompt}"
                    )
                    findings.append({
                        'type': 'comparison',
                        'data': research
                    })

                elif topic in ['security', 'security_practices']:
                    # Security research
                    research = await research_agent.research_for_agent(
                        self.config.agent_id,
                        f"Security best practices for: {prompt}"
                    )
                    findings.append({
                        'type': 'security',
                        'data': research
                    })

                elif topic == 'performance':
                    # Performance research
                    research = await research_agent.research_for_agent(
                        self.config.agent_id,
                        f"Performance optimization for: {prompt}"
                    )
                    findings.append({
                        'type': 'performance',
                        'data': research
                    })

                else:
                    # General research
                    research = await research_agent.research_for_agent(
                        self.config.agent_id,
                        prompt
                    )
                    findings.append({
                        'type': 'general',
                        'topic': topic,
                        'data': research
                    })

            # Compile research results
            research_summary = self._compile_research_summary(findings)

            return {
                'findings': findings,
                'summary': research_summary,
                'topics_researched': topics,
                'technologies_verified': technologies,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to perform mandatory research: {e}")
            return {
                'error': str(e),
                'findings': [],
                'summary': "Research could not be completed",
                'timestamp': datetime.now().isoformat()
            }

    def _compile_research_summary(self, findings: list) -> str:
        """Compile research findings into a summary"""
        summary_parts = []

        # Check for technology verifications
        unverified_techs = []
        for finding in findings:
            if finding['type'] == 'technology_verification':
                if finding['data'].get('exists') == 'uncertain':
                    unverified_techs.append(finding['technology'])

        if unverified_techs:
            summary_parts.append(f"⚠️ Could not verify existence of: {', '.join(unverified_techs)}")

        # Check for security warnings
        security_warnings = []
        for finding in findings:
            if finding['type'] == 'security':
                warnings = finding['data'].get('warnings', [])
                security_warnings.extend(warnings)

        if security_warnings:
            summary_parts.append(f"🔒 Security considerations: {'; '.join(security_warnings[:3])}")

        # Check for best practices
        practices = []
        for finding in findings:
            if finding['type'] == 'best_practices':
                practices.extend(finding['data'].get('practices', [])[:3])

        if practices:
            summary_parts.append(f"✅ Best practices: {'; '.join(practices)}")

        return " | ".join(summary_parts) if summary_parts else "Research completed successfully"

    async def collaborate_with(self, agent_id: str, task: str) -> Any:
        """Request collaboration from another agent"""
        if not self.communication_bus:
            logger.warning("Communication bus not initialized")
            return None

        correlation_id = f"{self.config.agent_id}_{datetime.now().timestamp()}"

        message = AgentMessage(
            from_agent=self.config.agent_id,
            to_agent=agent_id,
            message_type="request",
            content={"task": task, "requesting_collaboration": True},
            correlation_id=correlation_id
        )

        # Send request
        await self.communication_bus.publish(f"agent.{agent_id}", message)

        # Wait for response (with timeout)
        try:
            response = await asyncio.wait_for(
                self._wait_for_response(correlation_id),
                timeout=30.0
            )
            return response
        except asyncio.TimeoutError:
            logger.warning(f"Collaboration request to {agent_id} timed out")
            return None

    async def request_help(self, task: str) -> list[Any]:
        """Broadcast help request to all agents"""
        if not self.communication_bus:
            return []

        correlation_id = f"help_{self.config.agent_id}_{datetime.now().timestamp()}"

        message = AgentMessage(
            from_agent=self.config.agent_id,
            to_agent="all",
            message_type="help_request",
            content={"task": task, "capabilities_needed": []},
            correlation_id=correlation_id
        )

        # Store help request
        self.active_help_requests[correlation_id] = message

        # Broadcast request
        await self.communication_bus.publish("agent.help_request", message)

        # Wait for responses
        await asyncio.sleep(2)  # Give agents time to respond

        # Collect responses
        # TODO: Implement response collection
        return []

    async def send_response(self, to_agent: str, content: Any, correlation_id: str | None = None):
        """Send response to another agent"""
        if not self.communication_bus:
            return

        message = AgentMessage(
            from_agent=self.config.agent_id,
            to_agent=to_agent,
            message_type="response",
            content=content,
            correlation_id=correlation_id
        )

        await self.communication_bus.publish(f"agent.{to_agent}", message)

    async def _wait_for_response(self, correlation_id: str) -> Any:
        """Wait for response with specific correlation ID"""
        # TODO: Implement response waiting mechanism
        await asyncio.sleep(1)
        return None

    @abstractmethod
    async def _process_agent_request(self, message: AgentMessage) -> Any:
        """Process request from another agent"""
        pass

    async def _process_agent_response(self, message: AgentMessage):
        """Process response from another agent"""
        logger.info(f"Received response from {message.from_agent}: {message.content}")

    async def _process_broadcast(self, message: AgentMessage):
        """Process broadcast message"""
        logger.info(f"Processing broadcast from {message.from_agent}")

    async def _can_help_with(self, task: dict[str, Any]) -> bool:
        """Check if agent can help with a task"""
        # Check if task matches agent capabilities
        # TODO: Implement capability matching
        return False

    async def _provide_help(self, task: dict[str, Any]) -> Any:
        """Provide help for a task"""
        # TODO: Implement help provision
        return {"help": "Generic help from " + self.name}

    # ============ PAUSE/RESUME/STOP METHODS ============
    async def pause_current_task(self, task_id: str = None, task_description: str = None) -> dict[str, Any]:
        """
        Pause the current task
        ASIMOV RULE 1: Must work, no silent failures
        """
        if not self.pause_handler:
            raise Exception("Pause functionality not available - PauseHandler not initialized")

        if not task_id:
            task_id = f"{self.config.agent_id}_{self.execution_count}"
        if not task_description:
            task_description = f"Task {task_id}"

        return await self.pause_handler.pause_task(task_id, task_description)

    async def resume_task(self, additional_instructions: str = None) -> dict[str, Any]:
        """Resume the paused task with optional additional instructions"""
        if not self.pause_handler:
            raise Exception("Pause functionality not available - PauseHandler not initialized")

        return await self.pause_handler.resume_task(additional_instructions)

    async def stop_and_rollback(self) -> dict[str, Any]:
        """
        Stop task and rollback to checkpoint
        ASIMOV RULE 2: Complete rollback, no partial
        """
        if not self.pause_handler:
            raise Exception("Pause functionality not available - PauseHandler not initialized")

        return await self.pause_handler.stop_and_rollback()

    async def handle_clarification(self, response: dict[str, Any]) -> dict[str, Any]:
        """Handle user's response to clarification request"""
        if not self.pause_handler:
            raise Exception("Pause functionality not available - PauseHandler not initialized")

        return await self.pause_handler.handle_clarification_response(response)

    def set_websocket_callback(self, callback: Callable):
        """Set WebSocket callback for sending pause notifications to UI"""
        self.websocket_callback = callback
        if self.pause_handler:
            self.pause_handler.set_websocket_callback(callback)

    def get_status(self) -> dict[str, Any]:
        """Get agent status"""
        status = {
            "agent_id": self.config.agent_id,
            "name": self.name,
            "model": self.model,
            "status": "ready",
            "execution_count": self.execution_count,
            "total_tokens_used": self.total_tokens_used,
            "last_execution": self.last_execution_time.isoformat() if self.last_execution_time else None,
            "active_collaborations": len(self.collaboration_sessions),
            "capabilities": [cap.value for cap in self.config.capabilities]
        }

        # Add pause state if available
        if self.pause_handler:
            status["pause_state"] = self.pause_handler.get_pause_state()

        return status

    async def learn_from_task(self, task: str, result: Any, success: bool, context: str = None) -> str:
        """
        Learn from task execution results
        Integrates with MemoryManager to store learning entries
        """
        if not self.memory_manager:
            logger.warning(f"{self.name}: No memory manager available for learning")
            return None

        # Determine impact based on success and task complexity
        impact = "high" if not success else "medium"
        if success and len(task) > 200:  # Complex successful tasks
            impact = "high"

        # Create learning description
        description = f"{self.name} {'succeeded' if success else 'failed'} at: {task[:100]}..."

        # Extract lesson
        if success:
            lesson = f"Successful approach for {type(result).__name__} tasks"
        else:
            lesson = f"Avoid this approach: {str(result)[:200]}"

        # Add context
        full_context = f"Agent: {self.name}, Model: {self.model}"
        if context:
            full_context += f", Additional: {context}"

        # Store learning
        learning_id = self.memory_manager.store_learning(
            description=description,
            lesson=lesson,
            context=full_context,
            impact=impact
        )

        logger.info(f"✅ {self.name} learned from task: {learning_id}")
        return learning_id

    async def apply_learnings(self, task: str) -> list[Any]:
        """
        Retrieve and apply relevant learnings to current task
        """
        if not self.memory_manager:
            return []

        # Get relevant learnings
        learnings = self.memory_manager.get_relevant_learnings(
            context=task,
            limit=5
        )

        if learnings:
            logger.info(f"📚 {self.name} applying {len(learnings)} learnings to task")

            # Track applied learnings
            for learning in learnings:
                learning.applied_count += 1

        return learnings

    async def save_learnings_to_disk(self, scope: str = "auto") -> bool:
        """
        Persist learning entries to disk (DUAL LEARNING SYSTEM)

        Args:
            scope: "global" | "workspace" | "auto" (default)
                   auto = separate by context (global vs workspace)

        Saves to:
        - Global: ~/.ki_autoagent/data/learning/global/{agent_id}.json
        - Workspace: $WORKSPACE/.ki_autoagent_ws/learning/{agent_id}.json
        """
        import json
        import os

        if not self.memory_manager or not self.memory_manager.learning_entries:
            return False

        workspace_path = os.getenv("KI_WORKSPACE_PATH")
        home_dir = os.path.expanduser("~")

        # Filter learnings for this agent
        agent_learnings = [
            learning for learning in self.memory_manager.learning_entries
            if self.config.agent_id in learning.context
        ]

        # Separate learnings by scope
        global_learnings = []
        workspace_learnings = []

        for learning in agent_learnings:
            context_str = learning.context if isinstance(learning.context, str) else str(learning.context)

            # Check if learning is global or workspace-specific
            if "global" in context_str or "best-practice" in context_str or "security" in context_str:
                global_learnings.append(learning)
            elif workspace_path and ("workspace" in context_str or "project" in context_str):
                workspace_learnings.append(learning)
            else:
                # Default: based on scope parameter
                if scope == "global":
                    global_learnings.append(learning)
                elif scope == "workspace" and workspace_path:
                    workspace_learnings.append(learning)
                else:
                    # Auto: prefer workspace if available
                    if workspace_path:
                        workspace_learnings.append(learning)
                    else:
                        global_learnings.append(learning)

        # Save global learnings
        if global_learnings:
            global_learning_dir = os.path.join(home_dir, '.ki_autoagent', 'data', 'learning', 'global')
            os.makedirs(global_learning_dir, exist_ok=True)
            global_file = os.path.join(global_learning_dir, f"{self.config.agent_id}.json")

            with open(global_file, 'w') as f:
                json.dump([
                    {
                        'id': l.id,
                        'timestamp': l.timestamp,
                        'description': l.description,
                        'lesson': l.lesson,
                        'context': l.context,
                        'impact': l.impact,
                        'applied_count': l.applied_count
                    }
                    for l in global_learnings
                ], f, indent=2)

            logger.info(f"💾 Saved {len(global_learnings)} GLOBAL learnings for {self.name}")

        # Save workspace learnings
        if workspace_learnings and workspace_path:
            workspace_learning_dir = os.path.join(workspace_path, '.ki_autoagent_ws', 'learning')
            os.makedirs(workspace_learning_dir, exist_ok=True)
            workspace_file = os.path.join(workspace_learning_dir, f"{self.config.agent_id}.json")

            with open(workspace_file, 'w') as f:
                json.dump([
                    {
                        'id': l.id,
                        'timestamp': l.timestamp,
                        'description': l.description,
                        'lesson': l.lesson,
                        'context': l.context,
                        'impact': l.impact,
                        'applied_count': l.applied_count
                    }
                    for l in workspace_learnings
                ], f, indent=2)

            logger.info(f"💾 Saved {len(workspace_learnings)} WORKSPACE learnings for {self.name}")

        return True

    async def load_learnings_from_disk(self) -> int:
        """
        Load learning entries from disk (DUAL LEARNING SYSTEM)

        Loads BOTH global AND workspace learnings:
        - Global: ~/.ki_autoagent/data/learning/global/{agent_id}.json (always)
        - Workspace: $WORKSPACE/.ki_autoagent_ws/learning/{agent_id}.json (if in workspace)

        Returns:
            Total number of learnings loaded
        """
        import json
        import os

        if not self.memory_manager:
            logger.warning(f"{self.name}: No memory manager available to load learnings")
            return 0

        workspace_path = os.getenv("KI_WORKSPACE_PATH")
        home_dir = os.path.expanduser("~")
        total_loaded = 0

        # Helper function to load from file
        def load_from_file(file_path: str, source_name: str) -> int:
            if not os.path.exists(file_path):
                return 0

            try:
                with open(file_path, 'r') as f:
                    learnings_data = json.load(f)

                # Convert to LearningEntry objects
                from core.memory_manager import LearningEntry

                loaded = 0
                for data in learnings_data:
                    learning = LearningEntry(
                        id=data['id'],
                        timestamp=data['timestamp'],
                        description=data['description'],
                        lesson=data['lesson'],
                        context=data['context'],
                        impact=data['impact'],
                        applied_count=data.get('applied_count', 0)
                    )

                    # Check if not already in memory (avoid duplicates)
                    if not any(l.id == learning.id for l in self.memory_manager.learning_entries):
                        self.memory_manager.learning_entries.append(learning)
                        loaded += 1

                if loaded > 0:
                    logger.info(f"📚 Loaded {loaded} {source_name} learnings for {self.name}")
                return loaded

            except Exception as e:
                logger.error(f"Failed to load {source_name} learnings: {e}")
                return 0

        # 1. Load GLOBAL learnings (always)
        global_learning_dir = os.path.join(home_dir, '.ki_autoagent', 'data', 'learning', 'global')
        global_file = os.path.join(global_learning_dir, f"{self.config.agent_id}.json")
        total_loaded += load_from_file(global_file, "GLOBAL")

        # 2. Load WORKSPACE learnings (if in workspace)
        if workspace_path:
            workspace_learning_dir = os.path.join(workspace_path, '.ki_autoagent_ws', 'learning')
            workspace_file = os.path.join(workspace_learning_dir, f"{self.config.agent_id}.json")
            total_loaded += load_from_file(workspace_file, "WORKSPACE")

        if total_loaded > 0:
            logger.info(f"📖 Total learnings loaded for {self.name}: {total_loaded}")

        return total_loaded

    # ========================================================================
    # v5.9.0: PREDICTIVE LEARNING METHODS
    # ========================================================================

    def make_prediction(
        self,
        task_id: str,
        action: str,
        expected_outcome: str,
        confidence: float,
        context: dict[str, Any | None] = None
    ):
        """
        Make a prediction before taking action

        This enables the agent to learn from prediction errors by comparing
        what it expected to happen vs. what actually happened.

        Args:
            task_id: Unique identifier for this task
            action: What the agent is about to do
            expected_outcome: What the agent expects will happen
            confidence: How confident (0.0 to 1.0)
            context: Additional context

        Example:
            agent.make_prediction(
                task_id="task_123",
                action="Write calculator code",
                expected_outcome="Code will pass tests",
                confidence=0.9
            )
        """
        if not self.predictive_memory:
            return

        self.predictive_memory.make_prediction(
            task_id=task_id,
            action=action,
            expected_outcome=expected_outcome,
            confidence=confidence,
            context=context
        )

    def record_reality(
        self,
        task_id: str,
        actual_outcome: str,
        success: bool,
        metadata: dict[str, Any | None] = None
    ):
        """
        Record what actually happened after action execution

        This completes the prediction cycle and enables learning from errors.

        Args:
            task_id: Task identifier (same as in make_prediction)
            actual_outcome: What actually happened
            success: Did the action succeed?
            metadata: Additional outcome data

        Example:
            agent.record_reality(
                task_id="task_123",
                actual_outcome="Tests failed - edge case not handled",
                success=False
            )
        """
        if not self.predictive_memory:
            return

        error = self.predictive_memory.record_reality(
            task_id=task_id,
            actual_outcome=actual_outcome,
            success=success,
            metadata=metadata
        )

        # Save predictions to disk after each reality recording
        if error:
            self.predictive_memory.save_to_disk()

    def adjust_confidence_based_on_history(self, action: str, base_confidence: float) -> float:
        """
        Adjust confidence based on historical prediction accuracy

        Args:
            action: The action being considered
            base_confidence: Initial confidence level

        Returns:
            Adjusted confidence based on learned patterns
        """
        if not self.predictive_memory:
            return base_confidence

        adjustment = self.predictive_memory.get_prediction_confidence_adjustment(action)
        adjusted = base_confidence * adjustment

        if adjustment < 0.8:
            logger.info(f"⚠️ Confidence adjusted from {base_confidence:.2f} to {adjusted:.2f} based on history")

        return adjusted

    def get_prediction_summary(self) -> dict[str, Any]:
        """Get summary of agent's prediction history"""
        if not self.predictive_memory:
            return {"error": "Predictive memory not available"}

        return self.predictive_memory.get_error_summary()

    # ========================================================================
    # v5.9.0: CURIOSITY-DRIVEN EXPLORATION METHODS
    # ========================================================================

    def record_task_encounter(
        self,
        task_id: str,
        task_description: str,
        task_embedding: list[float | None] = None,
        outcome: str | None = None,
        category: str | None = None
    ):
        """
        Record that agent encountered a task

        This enables curiosity-driven exploration by tracking which tasks
        the agent has worked on before.

        Args:
            task_id: Unique task identifier
            task_description: Human-readable task description
            task_embedding: Optional embedding for semantic comparison
            outcome: "success", "failure", or None if in progress
            category: Optional task category (e.g., "authentication", "database")

        Example:
            agent.record_task_encounter(
                task_id="task_123",
                task_description="Build authentication system",
                outcome="success",
                category="authentication"
            )
        """
        if not self.curiosity_module:
            return

        self.curiosity_module.record_task_encounter(
            task_id=task_id,
            task_description=task_description,
            task_embedding=task_embedding,
            outcome=outcome,
            category=category
        )

        # Save curiosity data to disk
        self.curiosity_module.save_to_disk()

    def calculate_task_priority_with_curiosity(
        self,
        task_description: str,
        base_priority: float,
        task_embedding: list[float | None] = None,
        category: str | None = None
    ) -> float:
        """
        Calculate final task priority considering both importance and novelty

        This balances exploitation (doing important tasks) with exploration
        (trying novel tasks to learn).

        Args:
            task_description: The task to evaluate
            base_priority: Base priority from task importance (0.0-1.0)
            task_embedding: Optional pre-computed embedding
            category: Optional task category

        Returns:
            Final priority with novelty bonus applied

        Example:
            priority = agent.calculate_task_priority_with_curiosity(
                task_description="Implement WebRTC video chat",
                base_priority=0.7  # Important task
            )
            # If agent never did WebRTC before, priority might boost to 0.85
        """
        if not self.curiosity_module:
            return base_priority

        final_priority, novelty_score = self.curiosity_module.calculate_task_priority(
            task_description=task_description,
            base_priority=base_priority,
            task_embedding=task_embedding,
            category=category
        )

        return final_priority

    def get_exploration_summary(self) -> dict[str, Any]:
        """Get summary of agent's exploration history"""
        if not self.curiosity_module:
            return {"error": "Curiosity module not available"}

        return self.curiosity_module.get_exploration_summary()

    def set_exploration_weight(self, weight: float):
        """
        Adjust exploration vs exploitation balance

        Args:
            weight: 0.0 = pure exploitation (ignore novelty),
                   1.0 = pure exploration (maximize novelty)
                   default = 0.3 (30% curiosity, 70% importance)

        Example:
            # Make agent more curious
            agent.set_exploration_weight(0.5)  # 50/50 balance
        """
        if not self.curiosity_module:
            logger.warning(f"⚠️ Curiosity module not available for {self.name}")
            return

        self.curiosity_module.set_exploration_weight(weight)

    # ========================================================================
    # v5.9.0: NEUROSYMBOLIC REASONING METHODS
    # ========================================================================

    def apply_neurosymbolic_reasoning(
        self,
        task: str,
        context: dict[str, Any | None] = None
    ) -> dict[str, Any]:
        """
        Apply hybrid reasoning combining rules (symbolic) and AI (neural)

        This enables the agent to follow explicit rules while maintaining
        creative flexibility for implementation.

        Args:
            task: The task to reason about
            context: Additional context (e.g., has_rate_limit, requires_api_key)

        Returns:
            Dictionary with:
            - symbolic_results: Results from rule evaluation
            - neural_guidance: Guidance from LLM
            - final_approach: Combined approach
            - can_proceed: Whether constraints allow proceeding

        Example:
            result = agent.apply_neurosymbolic_reasoning(
                task="Implement API client with rate limiting",
                context={"has_rate_limit": True}
            )

            if not result["final_approach"]["can_proceed"]:
                # Handle constraint violations
                ...

            # Follow symbolic suggestions + neural creativity
            suggestions = result["final_approach"]["symbolic_suggestions"]
        """
        if not self.neurosymbolic_reasoner:
            logger.warning(f"⚠️ Neurosymbolic reasoner not available for {self.name}")
            return {
                "symbolic_results": {},
                "neural_guidance": None,
                "final_approach": {"can_proceed": True}
            }

        return self.neurosymbolic_reasoner.reason(task, context)

    def add_custom_rule(self, rule):
        """
        Add a custom reasoning rule for this agent

        Args:
            rule: Rule object (from neurosymbolic_reasoning module)

        Example:
            from langgraph_system.extensions.neurosymbolic_reasoning import (
                Rule, RuleType, Condition, Action, ActionType
            )

            rule = Rule(
                rule_id="custom_db_check",
                name="Database Connection Check",
                rule_type=RuleType.CONSTRAINT,
                conditions=[
                    Condition(
                        description="Task requires database",
                        evaluator=lambda ctx: "database" in ctx.get("task", "").lower()
                    )
                ],
                actions=[
                    Action(
                        action_type=ActionType.REQUIRE,
                        description="Verify database connection before proceeding"
                    )
                ],
                priority=9
            )

            agent.add_custom_rule(rule)
        """
        if not self.neurosymbolic_reasoner:
            logger.warning(f"⚠️ Neurosymbolic reasoner not available for {self.name}")
            return

        self.neurosymbolic_reasoner.add_custom_rule(rule)

    def get_reasoning_statistics(self) -> dict[str, Any]:
        """Get statistics about rule-based reasoning"""
        if not self.neurosymbolic_reasoner:
            return {"error": "Neurosymbolic reasoner not available"}

        return self.neurosymbolic_reasoner.get_rule_statistics()

    # ========================================================================
    # v5.9.0: FRAMEWORK COMPARISON METHODS (Systemvergleich)
    # ========================================================================

    def compare_architecture_with_frameworks(
        self,
        decision: str,
        context: dict[str, Any | None] = None
    ) -> dict[str, Any]:
        """
        Compare an architecture decision with other agent frameworks

        This is META-LEVEL analysis that helps understand if the proposed
        architecture aligns with best practices from successful frameworks.

        Args:
            decision: The architecture decision to analyze
            context: Additional context about the project

        Returns:
            Analysis with:
            - similar_patterns: Patterns from other frameworks
            - recommendations: Suggestions based on comparison
            - best_practices: Industry best practices
            - risk_assessment: Potential issues

        Example:
            analysis = agent.compare_architecture_with_frameworks(
                decision="Use multiple specialized agents for software development",
                context={"project_type": "web_app", "complexity": "medium"}
            )

            # See what AutoGen, CrewAI, ChatDev do
            for pattern in analysis["similar_patterns"]:
                print(f"Pattern: {pattern['pattern']}")
                for approach in pattern["approaches"]:
                    print(f"  {approach['framework']}: {approach['approach']}")
        """
        if not self.framework_comparator:
            logger.warning(f"⚠️ Framework comparator not available for {self.name}")
            return {
                "similar_patterns": [],
                "recommendations": [],
                "best_practices": [],
                "risk_assessment": []
            }

        return self.framework_comparator.compare_architecture_decision(
            decision=decision,
            context=context or {}
        )

    def get_framework_profile(self, framework_name: str) -> dict[str, Any | None]:
        """
        Get detailed profile of a specific agent framework

        Args:
            framework_name: Name of framework (e.g., "autogen", "crewai", "babyagi")

        Returns:
            Framework profile or None if not found

        Example:
            profile = agent.get_framework_profile("autogen")
            print(f"Strengths: {profile.strengths}")
            print(f"Best for: {profile.best_for}")
        """
        if not self.framework_comparator:
            return None

        profile = self.framework_comparator.get_framework_profile(framework_name)
        if not profile:
            return None

        # Convert to dict for easier consumption
        return {
            "name": profile.name,
            "category": profile.category.value,
            "description": profile.description,
            "strengths": profile.strengths,
            "weaknesses": profile.weaknesses,
            "best_for": profile.best_for,
            "architecture_pattern": profile.architecture_pattern,
            "popularity_score": profile.popularity_score
        }

    def list_known_frameworks(self) -> list[str]:
        """List all agent frameworks in the knowledge base"""
        if not self.framework_comparator:
            return []

        return self.framework_comparator.list_frameworks()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name} ({self.model})>"