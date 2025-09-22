"""
BaseAgent - Modern base class for all agents with Memory, SharedContext, and Communication
Inspired by the TypeScript implementation with all advanced features
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging
import json
from enum import Enum

# Import core systems
try:
    from core.memory_manager import get_memory_manager, MemoryType
    from core.shared_context_manager import get_shared_context
    from core.conversation_context_manager import get_conversation_context
    CORE_SYSTEMS_AVAILABLE = True
except ImportError:
    CORE_SYSTEMS_AVAILABLE = False
    logging.warning("Core systems (Memory, Context) not available")

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
    capabilities: List[AgentCapability] = field(default_factory=list)
    temperature: float = 0.7
    max_tokens: int = 4000
    instructions_path: Optional[str] = None
    icon: str = "🤖"

@dataclass
class TaskRequest:
    """Task request structure"""
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    command: Optional[str] = None
    project_type: Optional[str] = None
    global_context: Optional[str] = None
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    thinking_mode: bool = False
    mode: str = "auto"
    agent: Optional[str] = None

@dataclass
class TaskResult:
    """Task execution result"""
    status: str  # 'success', 'error', 'partial_success'
    content: str
    agent: str
    suggestions: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
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
    correlation_id: Optional[str] = None

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

        # Execution tracking
        self.execution_count = 0
        self.total_tokens_used = 0
        self.last_execution_time = None

        # Initialize core systems if available
        if CORE_SYSTEMS_AVAILABLE:
            self.memory_manager = get_memory_manager()
            self.shared_context = get_shared_context()
            self.conversation = get_conversation_context()
        else:
            self.memory_manager = None
            self.shared_context = None
            self.conversation = None

        # Communication bus (will be initialized separately)
        self.communication_bus = None

        # Collaboration
        self.collaboration_sessions: set[str] = set()
        self.active_help_requests: Dict[str, AgentMessage] = {}

        # Pattern library
        self.code_patterns: List[Dict[str, Any]] = []
        self.architecture_patterns: List[Dict[str, Any]] = []

        logger.info(f"🤖 {self.config.icon} {self.name} initialized (Model: {self.model})")

    def _load_instructions(self) -> str:
        """Load agent instructions from file if available"""
        if self.config.instructions_path:
            try:
                with open(self.config.instructions_path, 'r') as f:
                    return f.read()
            except FileNotFoundError:
                logger.warning(f"Instructions file not found: {self.config.instructions_path}")
        return ""

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
        """Execute task with memory enhancement and context integration"""
        start_time = datetime.now()

        # Search memory for similar tasks
        if self.memory_manager:
            similar_tasks = await self.memory_manager.search(
                request.prompt,
                memory_type=MemoryType.EPISODIC,
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

        # Execute the task
        result = await self.execute(request)

        # Store in memory
        if self.memory_manager:
            await self.memory_manager.store(
                agent_id=self.config.agent_id,
                content={
                    "task": request.prompt,
                    "result": result.content[:2000],
                    "status": result.status
                },
                memory_type=MemoryType.EPISODIC,
                metadata={
                    "importance": 0.7 if result.status == "success" else 0.5,
                    "tags": ["task_result", self.config.agent_id]
                }
            )

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

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        result.execution_time = execution_time

        # Update tracking
        self.execution_count += 1
        self.total_tokens_used += result.tokens_used
        self.last_execution_time = datetime.now()

        return result

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

    async def request_help(self, task: str) -> List[Any]:
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

    async def send_response(self, to_agent: str, content: Any, correlation_id: Optional[str] = None):
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

    async def _can_help_with(self, task: Dict[str, Any]) -> bool:
        """Check if agent can help with a task"""
        # Check if task matches agent capabilities
        # TODO: Implement capability matching
        return False

    async def _provide_help(self, task: Dict[str, Any]) -> Any:
        """Provide help for a task"""
        # TODO: Implement help provision
        return {"help": "Generic help from " + self.name}

    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
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

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name} ({self.model})>"