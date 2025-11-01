"""
Event Streaming System for v7.0 Supervisor Workflow

Provides real-time, detailed progress updates to clients.

Key Features:
- Agent "think" processes
- Detailed reasoning and decisions
- Intermediate results
- Rich, user-friendly messages

Author: KI AutoAgent Team
Version: 7.0.0
Date: 2025-10-28
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, AsyncGenerator
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ============================================================================
# Event Types
# ============================================================================

@dataclass
class AgentEvent:
    """Detailed event from an agent during execution."""

    agent: str  # Agent name (research, architect, codesmith, etc.)
    event_type: str  # think, progress, result, decision
    message: str  # User-friendly message
    details: dict[str, Any] = field(default_factory=dict)  # Additional data
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return {
            "type": "agent_event",
            "agent": self.agent,
            "event_type": self.event_type,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp
        }


@dataclass
class SupervisorEvent:
    """Detailed event from the supervisor."""

    event_type: str  # decision, routing, analysis
    message: str  # User-friendly message
    reasoning: str | None = None  # Supervisor's reasoning
    confidence: float | None = None  # Decision confidence
    next_agent: str | None = None  # Next agent to execute
    instructions: str | None = None  # Instructions for next agent
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return {
            "type": "supervisor_event",
            "event_type": self.event_type,
            "message": self.message,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "next_agent": self.next_agent,
            "instructions": self.instructions,
            "details": self.details,
            "timestamp": self.timestamp
        }


# ============================================================================
# Event Stream Manager
# ============================================================================

class EventStreamManager:
    """
    Manages event streaming from agents to clients.

    This is a singleton that collects events from all agents
    and streams them to connected WebSocket clients.
    """

    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._subscribers: dict[str, asyncio.Queue] = {}  # session_id -> queue
        self._initialized = True
        logger.info("✅ EventStreamManager initialized")

    def subscribe(self, session_id: str) -> asyncio.Queue:
        """
        Subscribe to event stream for a session.

        Args:
            session_id: Session identifier

        Returns:
            Queue that will receive events
        """
        if session_id not in self._subscribers:
            self._subscribers[session_id] = asyncio.Queue()
            logger.info(f"   📡 New subscriber: {session_id}")

        return self._subscribers[session_id]

    def unsubscribe(self, session_id: str):
        """
        Unsubscribe from event stream.

        Args:
            session_id: Session identifier
        """
        if session_id in self._subscribers:
            del self._subscribers[session_id]
            logger.info(f"   📡 Unsubscribed: {session_id}")

    async def send_agent_event(
        self,
        session_id: str,
        agent: str,
        event_type: str,
        message: str,
        details: dict[str, Any] | None = None
    ):
        """
        Send an agent event to subscribed clients.

        Args:
            session_id: Session identifier
            agent: Agent name
            event_type: Event type (think, progress, result, decision)
            message: User-friendly message
            details: Additional data
        """
        event = AgentEvent(
            agent=agent,
            event_type=event_type,
            message=message,
            details=details or {}
        )

        await self._send_event(session_id, event.to_dict())

    async def send_supervisor_event(
        self,
        session_id: str,
        event_type: str,
        message: str,
        reasoning: str | None = None,
        confidence: float | None = None,
        next_agent: str | None = None,
        instructions: str | None = None,
        details: dict[str, Any] | None = None
    ):
        """
        Send a supervisor event to subscribed clients.

        Args:
            session_id: Session identifier
            event_type: Event type (decision, routing, analysis)
            message: User-friendly message
            reasoning: Supervisor's reasoning
            confidence: Decision confidence
            next_agent: Next agent to execute
            instructions: Instructions for next agent
            details: Additional data
        """
        event = SupervisorEvent(
            event_type=event_type,
            message=message,
            reasoning=reasoning,
            confidence=confidence,
            next_agent=next_agent,
            instructions=instructions,
            details=details or {}
        )

        await self._send_event(session_id, event.to_dict())

    async def _send_event(self, session_id: str, event_dict: dict[str, Any]):
        """
        Internal method to send event to subscriber queue.

        Args:
            session_id: Session identifier
            event_dict: Event as dictionary
        """
        if session_id in self._subscribers:
            queue = self._subscribers[session_id]
            await queue.put(event_dict)
            logger.debug(f"   📤 Event sent to {session_id}: {event_dict['type']}")
        else:
            logger.warning(f"   ⚠️ No subscriber for session {session_id}")

    async def stream_events(
        self,
        session_id: str
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Stream events for a session.

        Args:
            session_id: Session identifier

        Yields:
            Event dictionaries
        """
        queue = self.subscribe(session_id)

        try:
            while True:
                # Get event from queue (blocks until event available)
                event = await queue.get()
                yield event

                # Check if this is a completion/error event
                if event.get("type") in ("workflow_complete", "error"):
                    break

        except asyncio.CancelledError:
            logger.info(f"   ⚠️ Event stream cancelled for {session_id}")
        finally:
            self.unsubscribe(session_id)


# ============================================================================
# Convenience Functions
# ============================================================================

# Global instance
_event_manager = EventStreamManager()


async def send_agent_think(
    session_id: str,
    agent: str,
    thinking: str,
    details: dict[str, Any] | None = None
):
    """Send an agent 'think' event."""
    await _event_manager.send_agent_event(
        session_id=session_id,
        agent=agent,
        event_type="think",
        message=f"🧠 {thinking}",
        details=details
    )


async def send_agent_progress(
    session_id: str,
    agent: str,
    progress: str,
    details: dict[str, Any] | None = None
):
    """Send an agent 'progress' event."""
    await _event_manager.send_agent_event(
        session_id=session_id,
        agent=agent,
        event_type="progress",
        message=f"⚙️ {progress}",
        details=details
    )


async def send_agent_result(
    session_id: str,
    agent: str,
    result: str,
    details: dict[str, Any] | None = None
):
    """Send an agent 'result' event."""
    await _event_manager.send_agent_event(
        session_id=session_id,
        agent=agent,
        event_type="result",
        message=f"✅ {result}",
        details=details
    )


async def send_supervisor_decision(
    session_id: str,
    reasoning: str,
    next_agent: str,
    confidence: float,
    instructions: str | None = None
):
    """Send a supervisor decision event."""
    await _event_manager.send_supervisor_event(
        session_id=session_id,
        event_type="decision",
        message=f"🎯 Supervisor routing to: {next_agent}",
        reasoning=reasoning,
        confidence=confidence,
        next_agent=next_agent,
        instructions=instructions
    )


def get_event_manager() -> EventStreamManager:
    """Get the global event manager instance."""
    return _event_manager


# ============================================================================
# Export
# ============================================================================

__all__ = [
    "AgentEvent",
    "SupervisorEvent",
    "EventStreamManager",
    "get_event_manager",
    "send_agent_think",
    "send_agent_progress",
    "send_agent_result",
    "send_supervisor_decision"
]
