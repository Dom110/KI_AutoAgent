"""
AgentCommunicationBus - Event-driven communication system for inter-agent messaging
Enables agents to collaborate, share knowledge, and request help
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Types of inter-agent messages"""
    REQUEST = "request"              # Request for collaboration
    RESPONSE = "response"            # Response to request
    BROADCAST = "broadcast"          # Broadcast to all agents
    HELP_REQUEST = "help_request"    # Request for help
    KNOWLEDGE_SHARE = "knowledge_share"  # Share knowledge/patterns
    STATUS_UPDATE = "status_update"  # Status update
    CONFLICT = "conflict"            # Conflict notification
    VOTE = "vote"                    # Voting on decision

@dataclass
class AgentMessage:
    """Message between agents"""
    id: str
    from_agent: str
    to_agent: str  # 'all' for broadcast
    message_type: MessageType
    content: Any
    timestamp: float = field(default_factory=time.time)
    correlation_id: Optional[str] = None
    priority: int = 0  # Higher is more important
    expires_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MessageHandler:
    """Handler for messages"""
    agent_id: str
    callback: Callable
    filter: Optional[Callable] = None
    message_types: Optional[List[MessageType]] = None

@dataclass
class CollaborationSession:
    """Active collaboration between agents"""
    id: str
    initiator: str
    participants: List[str]
    topic: str
    started_at: float
    messages: List[AgentMessage]
    status: str  # 'active', 'completed', 'failed'

class AgentCommunicationBus:
    """
    Central communication bus for inter-agent messaging
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize communication bus"""
        if self._initialized:
            return

        # Message routing
        self.handlers: Dict[str, List[MessageHandler]] = defaultdict(list)
        self.topics: Dict[str, Set[str]] = defaultdict(set)  # topic -> subscribers

        # Message storage
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.message_history: List[AgentMessage] = []
        self.pending_responses: Dict[str, asyncio.Future] = {}

        # Collaboration sessions
        self.collaboration_sessions: Dict[str, CollaborationSession] = {}

        # Statistics
        self.total_messages = 0
        self.messages_by_type = defaultdict(int)
        self.messages_by_agent = defaultdict(int)

        # Background task for message processing
        self.processing_task = None

        self._initialized = True
        logger.info("AgentCommunicationBus initialized")

    async def start(self):
        """Start the message processing loop"""
        if not self.processing_task:
            self.processing_task = asyncio.create_task(self._process_messages())
            logger.info("Communication bus started")

    async def stop(self):
        """Stop the message processing loop"""
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
            self.processing_task = None
            logger.info("Communication bus stopped")

    async def register_agent(
        self,
        agent_id: str,
        handler: Callable,
        message_types: Optional[List[MessageType]] = None,
        topics: Optional[List[str]] = None
    ):
        """Register an agent with the communication bus"""
        # Register message handler
        message_handler = MessageHandler(
            agent_id=agent_id,
            callback=handler,
            message_types=message_types
        )

        self.handlers[agent_id].append(message_handler)

        # Subscribe to topics
        if topics:
            for topic in topics:
                self.topics[topic].add(agent_id)

        logger.info(f"Agent {agent_id} registered with communication bus")

    async def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        # Remove handlers
        if agent_id in self.handlers:
            del self.handlers[agent_id]

        # Remove from topics
        for topic_agents in self.topics.values():
            topic_agents.discard(agent_id)

        logger.info(f"Agent {agent_id} unregistered from communication bus")

    async def send_message(
        self,
        from_agent: str,
        to_agent: str,
        message_type: MessageType,
        content: Any,
        correlation_id: Optional[str] = None,
        priority: int = 0,
        timeout: Optional[float] = None
    ) -> Optional[Any]:
        """Send a message from one agent to another"""
        message_id = self._generate_id()

        message = AgentMessage(
            id=message_id,
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            correlation_id=correlation_id or message_id,
            priority=priority,
            expires_at=time.time() + timeout if timeout else None
        )

        # Add to queue
        await self.message_queue.put(message)
        self.total_messages += 1
        self.messages_by_type[message_type] += 1
        self.messages_by_agent[from_agent] += 1

        # If expecting response, create future
        if message_type == MessageType.REQUEST:
            future = asyncio.Future()
            self.pending_responses[message.correlation_id] = future

            try:
                # Wait for response with timeout
                response = await asyncio.wait_for(
                    future,
                    timeout=timeout or 30.0
                )
                return response
            except asyncio.TimeoutError:
                del self.pending_responses[message.correlation_id]
                logger.warning(f"Request from {from_agent} to {to_agent} timed out")
                return None

        return message_id

    async def broadcast(
        self,
        from_agent: str,
        message_type: MessageType,
        content: Any,
        topic: Optional[str] = None
    ):
        """Broadcast a message to all agents or topic subscribers"""
        message = AgentMessage(
            id=self._generate_id(),
            from_agent=from_agent,
            to_agent="all",
            message_type=message_type,
            content=content,
            metadata={"topic": topic} if topic else {}
        )

        await self.message_queue.put(message)
        self.total_messages += 1
        self.messages_by_type[message_type] += 1
        self.messages_by_agent[from_agent] += 1

        logger.debug(f"Broadcast from {from_agent}: {message_type.value}")

    async def request_help(
        self,
        from_agent: str,
        task_description: str,
        required_capabilities: Optional[List[str]] = None
    ) -> List[Tuple[str, Any]]:
        """Request help from other agents"""
        help_id = self._generate_id()

        content = {
            "task": task_description,
            "required_capabilities": required_capabilities or [],
            "help_id": help_id
        }

        # Broadcast help request
        await self.broadcast(
            from_agent=from_agent,
            message_type=MessageType.HELP_REQUEST,
            content=content
        )

        # Wait for responses
        await asyncio.sleep(2.0)  # Give agents time to respond

        # Collect responses
        responses = []
        for message in self.message_history[-20:]:  # Check recent messages
            if (message.message_type == MessageType.RESPONSE and
                message.correlation_id == help_id):
                responses.append((message.from_agent, message.content))

        logger.info(f"Agent {from_agent} received {len(responses)} help responses")
        return responses

    async def start_collaboration(
        self,
        initiator: str,
        participants: List[str],
        topic: str
    ) -> str:
        """Start a collaboration session"""
        session_id = self._generate_id()

        session = CollaborationSession(
            id=session_id,
            initiator=initiator,
            participants=participants,
            topic=topic,
            started_at=time.time(),
            messages=[],
            status="active"
        )

        self.collaboration_sessions[session_id] = session

        # Notify participants
        for participant in participants:
            await self.send_message(
                from_agent=initiator,
                to_agent=participant,
                message_type=MessageType.REQUEST,
                content={
                    "action": "join_collaboration",
                    "session_id": session_id,
                    "topic": topic
                }
            )

        logger.info(f"Collaboration session {session_id} started: {topic}")
        return session_id

    async def end_collaboration(self, session_id: str, status: str = "completed"):
        """End a collaboration session"""
        if session_id in self.collaboration_sessions:
            session = self.collaboration_sessions[session_id]
            session.status = status

            # Notify participants
            for participant in session.participants:
                await self.send_message(
                    from_agent=session.initiator,
                    to_agent=participant,
                    message_type=MessageType.STATUS_UPDATE,
                    content={
                        "action": "collaboration_ended",
                        "session_id": session_id,
                        "status": status
                    }
                )

            logger.info(f"Collaboration session {session_id} ended: {status}")

    async def share_knowledge(
        self,
        from_agent: str,
        knowledge_type: str,
        knowledge_content: Any,
        recipients: Optional[List[str]] = None
    ):
        """Share knowledge with other agents"""
        content = {
            "knowledge_type": knowledge_type,
            "content": knowledge_content,
            "shared_by": from_agent,
            "timestamp": time.time()
        }

        if recipients:
            # Send to specific agents
            for recipient in recipients:
                await self.send_message(
                    from_agent=from_agent,
                    to_agent=recipient,
                    message_type=MessageType.KNOWLEDGE_SHARE,
                    content=content
                )
        else:
            # Broadcast to all
            await self.broadcast(
                from_agent=from_agent,
                message_type=MessageType.KNOWLEDGE_SHARE,
                content=content
            )

    async def vote_on_decision(
        self,
        topic: str,
        options: List[Any],
        voters: List[str],
        timeout: float = 10.0
    ) -> Dict[Any, int]:
        """Conduct a vote among agents"""
        vote_id = self._generate_id()

        # Send vote request to all voters
        for voter in voters:
            await self.send_message(
                from_agent="system",
                to_agent=voter,
                message_type=MessageType.VOTE,
                content={
                    "vote_id": vote_id,
                    "topic": topic,
                    "options": options
                },
                correlation_id=vote_id
            )

        # Wait for votes
        await asyncio.sleep(timeout)

        # Count votes
        votes = defaultdict(int)
        for message in self.message_history[-50:]:
            if (message.message_type == MessageType.RESPONSE and
                message.correlation_id == vote_id):
                vote = message.content.get("vote")
                if vote in options:
                    votes[vote] += 1

        logger.info(f"Vote on '{topic}' completed: {dict(votes)}")
        return dict(votes)

    async def _process_messages(self):
        """Background task to process messages"""
        while True:
            try:
                # Get message from queue
                message = await self.message_queue.get()

                # Check if expired
                if message.expires_at and time.time() > message.expires_at:
                    logger.debug(f"Message {message.id} expired")
                    continue

                # Store in history
                self.message_history.append(message)
                if len(self.message_history) > 1000:
                    self.message_history = self.message_history[-500:]

                # Route message
                await self._route_message(message)

                # Handle collaboration sessions
                if message.correlation_id in self.collaboration_sessions:
                    session = self.collaboration_sessions[message.correlation_id]
                    session.messages.append(message)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    async def _route_message(self, message: AgentMessage):
        """Route message to appropriate handlers"""
        # Handle broadcast
        if message.to_agent == "all":
            # Send to all agents except sender
            for agent_id, handlers in self.handlers.items():
                if agent_id != message.from_agent:
                    await self._deliver_to_handlers(message, handlers)

        # Handle topic broadcast
        elif message.metadata.get("topic"):
            topic = message.metadata["topic"]
            if topic in self.topics:
                for agent_id in self.topics[topic]:
                    if agent_id != message.from_agent and agent_id in self.handlers:
                        await self._deliver_to_handlers(message, self.handlers[agent_id])

        # Handle direct message
        elif message.to_agent in self.handlers:
            await self._deliver_to_handlers(message, self.handlers[message.to_agent])

        # Handle response to pending request
        if message.message_type == MessageType.RESPONSE and message.correlation_id:
            if message.correlation_id in self.pending_responses:
                future = self.pending_responses[message.correlation_id]
                if not future.done():
                    future.set_result(message.content)
                del self.pending_responses[message.correlation_id]

    async def _deliver_to_handlers(
        self,
        message: AgentMessage,
        handlers: List[MessageHandler]
    ):
        """Deliver message to handlers"""
        for handler in handlers:
            # Check if handler wants this message type
            if handler.message_types and message.message_type not in handler.message_types:
                continue

            # Apply filter if present
            if handler.filter and not handler.filter(message):
                continue

            # Deliver message
            try:
                if asyncio.iscoroutinefunction(handler.callback):
                    await handler.callback(message)
                else:
                    handler.callback(message)
            except Exception as e:
                logger.error(f"Error in message handler: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get communication statistics"""
        return {
            "total_messages": self.total_messages,
            "messages_by_type": dict(self.messages_by_type),
            "messages_by_agent": dict(self.messages_by_agent),
            "active_collaborations": len([
                s for s in self.collaboration_sessions.values()
                if s.status == "active"
            ]),
            "pending_responses": len(self.pending_responses),
            "registered_agents": len(self.handlers)
        }

    def _generate_id(self) -> str:
        """Generate unique ID"""
        return f"msg_{uuid.uuid4().hex[:8]}"

# Global instance
def get_communication_bus() -> AgentCommunicationBus:
    """Get singleton AgentCommunicationBus instance"""
    return AgentCommunicationBus()