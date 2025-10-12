"""
Multi-Agent Message Bus for v6 Communication System

Implements pub/sub messaging infrastructure for inter-agent communication.

Features:
- Topic-based subscriptions
- Direct agent-to-agent messaging
- Broadcast messaging to all agents
- Message filtering based on content
- Priority queues for urgent messages
- Async/await support

Author: KI AutoAgent Team
Date: 2025-10-12
Version: v6.1
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


class Message:
    """
    Generic message structure for message bus.

    Attributes:
        topic: Message topic (e.g., "agent.architect", "agent.broadcast")
        payload: Message payload (can be any type, typically dict or AgentMessage)
        priority: Message priority level
        sender: Optional sender identifier
        timestamp: Message creation timestamp
        metadata: Additional message metadata
    """

    def __init__(
        self,
        topic: str,
        payload: Any,
        priority: MessagePriority = MessagePriority.NORMAL,
        sender: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.topic = topic
        self.payload = payload
        self.priority = priority
        self.sender = sender
        self.timestamp = datetime.now()
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return f"<Message topic={self.topic} priority={self.priority.name} sender={self.sender}>"


class MessageBus:
    """
    Multi-agent message bus with pub/sub pattern.

    Features:
    - Topic-based subscriptions (wildcards supported)
    - Priority queues (urgent messages processed first)
    - Message filtering based on custom predicates
    - Direct messaging (agent-to-agent)
    - Broadcast messaging (to all subscribers)
    - Async/await support for all operations

    Usage:
        bus = MessageBus()

        # Subscribe to topic
        async def handle_message(message):
            print(f"Received: {message.payload}")

        await bus.subscribe("agent.architect", handle_message)

        # Publish message
        await bus.publish("agent.architect", {"task": "Design API"})

        # Broadcast to all
        await bus.broadcast({"announcement": "System update"})

        # Start processing messages
        await bus.start()
    """

    def __init__(self, max_queue_size: int = 1000):
        """
        Initialize message bus.

        Args:
            max_queue_size: Maximum messages per priority queue (default: 1000)
        """
        # Topic subscriptions (topic -> list of handlers)
        self._subscriptions: dict[str, list[Callable]] = defaultdict(list)

        # Message queues (one per priority level)
        self._queues: dict[MessagePriority, asyncio.Queue] = {
            priority: asyncio.Queue(maxsize=max_queue_size)
            for priority in MessagePriority
        }

        # Message filters (predicates that must pass)
        self._filters: list[Callable[[Message], bool]] = []

        # Processing task
        self._processor_task: asyncio.Task | None = None
        self._running = False

        # Stats
        self.stats = {
            "messages_published": 0,
            "messages_delivered": 0,
            "messages_filtered": 0,
            "messages_dropped": 0,
        }

        logger.info("✅ MessageBus initialized")

    async def subscribe(
        self,
        topic: str,
        handler: Callable[[Any], Any],
    ) -> None:
        """
        Subscribe to a topic.

        Args:
            topic: Topic to subscribe to (e.g., "agent.architect", "agent.*")
            handler: Async function to handle messages (receives payload)

        Example:
            async def my_handler(payload):
                print(f"Received: {payload}")

            await bus.subscribe("agent.architect", my_handler)
        """
        if handler not in self._subscriptions[topic]:
            self._subscriptions[topic].append(handler)
            logger.info(f"📢 Subscribed to topic: {topic}")
        else:
            logger.warning(f"⚠️ Handler already subscribed to: {topic}")

    async def unsubscribe(
        self,
        topic: str,
        handler: Callable[[Any], Any],
    ) -> bool:
        """
        Unsubscribe from a topic.

        Args:
            topic: Topic to unsubscribe from
            handler: Handler to remove

        Returns:
            True if unsubscribed, False if handler not found
        """
        if topic in self._subscriptions and handler in self._subscriptions[topic]:
            self._subscriptions[topic].remove(handler)
            logger.info(f"🔇 Unsubscribed from topic: {topic}")
            return True
        return False

    async def publish(
        self,
        topic: str,
        payload: Any,
        priority: MessagePriority = MessagePriority.NORMAL,
        sender: str | None = None,
    ) -> bool:
        """
        Publish message to a topic.

        Args:
            topic: Topic to publish to
            payload: Message payload
            priority: Message priority (default: NORMAL)
            sender: Optional sender identifier

        Returns:
            True if published, False if dropped/filtered

        Example:
            await bus.publish("agent.architect", {"task": "Design API"})
        """
        message = Message(
            topic=topic,
            payload=payload,
            priority=priority,
            sender=sender,
        )

        # Apply filters
        if not self._passes_filters(message):
            self.stats["messages_filtered"] += 1
            logger.debug(f"🚫 Message filtered: {topic}")
            return False

        # Add to priority queue
        try:
            self._queues[priority].put_nowait(message)
            self.stats["messages_published"] += 1
            logger.debug(f"📤 Published to {topic} (priority: {priority.name})")
            return True
        except asyncio.QueueFull:
            self.stats["messages_dropped"] += 1
            logger.warning(f"⚠️ Queue full - dropped message to {topic}")
            return False

    async def broadcast(
        self,
        payload: Any,
        priority: MessagePriority = MessagePriority.NORMAL,
        sender: str | None = None,
    ) -> int:
        """
        Broadcast message to all subscribers.

        Args:
            payload: Message payload
            priority: Message priority (default: NORMAL)
            sender: Optional sender identifier

        Returns:
            Number of topics message was published to

        Example:
            await bus.broadcast({"announcement": "System update"})
        """
        count = 0
        for topic in self._subscriptions.keys():
            if await self.publish(topic, payload, priority, sender):
                count += 1

        logger.info(f"📢 Broadcasted to {count} topics")
        return count

    def add_filter(self, filter_fn: Callable[[Message], bool]) -> None:
        """
        Add message filter (predicate).

        Args:
            filter_fn: Function that returns True to allow message, False to filter

        Example:
            # Only allow messages from specific sender
            bus.add_filter(lambda msg: msg.sender == "architect")
        """
        self._filters.append(filter_fn)
        logger.info("🔍 Added message filter")

    def remove_filter(self, filter_fn: Callable[[Message], bool]) -> bool:
        """
        Remove message filter.

        Args:
            filter_fn: Filter function to remove

        Returns:
            True if removed, False if not found
        """
        if filter_fn in self._filters:
            self._filters.remove(filter_fn)
            logger.info("🔍 Removed message filter")
            return True
        return False

    def _passes_filters(self, message: Message) -> bool:
        """Check if message passes all filters"""
        return all(filter_fn(message) for filter_fn in self._filters)

    def _match_topic(self, subscription_topic: str, message_topic: str) -> bool:
        """
        Match topic with wildcard support.

        Examples:
            "agent.*" matches "agent.architect", "agent.codesmith"
            "agent.architect" matches only "agent.architect"
            "*" matches everything
        """
        if subscription_topic == "*":
            return True

        if "*" in subscription_topic:
            # Simple wildcard matching (suffix only)
            prefix = subscription_topic.replace("*", "")
            return message_topic.startswith(prefix)

        return subscription_topic == message_topic

    async def _process_messages(self):
        """Background task to process messages from priority queues"""
        logger.info("🔄 Message processor started")

        while self._running:
            try:
                # Process in priority order (URGENT -> HIGH -> NORMAL -> LOW)
                for priority in reversed(list(MessagePriority)):
                    queue = self._queues[priority]

                    # Process all messages at this priority level
                    while not queue.empty():
                        try:
                            message = queue.get_nowait()
                            await self._deliver_message(message)
                        except asyncio.QueueEmpty:
                            break
                        except Exception as e:
                            logger.error(f"❌ Error processing message: {e}", exc_info=True)

                # Small sleep to prevent busy loop
                await asyncio.sleep(0.01)

            except asyncio.CancelledError:
                logger.info("🛑 Message processor cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Message processor error: {e}", exc_info=True)

    async def _deliver_message(self, message: Message):
        """Deliver message to all matching subscribers"""
        delivered_count = 0

        for topic, handlers in self._subscriptions.items():
            if self._match_topic(topic, message.topic):
                for handler in handlers:
                    try:
                        # Call handler with payload
                        if asyncio.iscoroutinefunction(handler):
                            await handler(message.payload)
                        else:
                            handler(message.payload)

                        delivered_count += 1
                        self.stats["messages_delivered"] += 1

                    except Exception as e:
                        logger.error(
                            f"❌ Handler error for topic {topic}: {e}",
                            exc_info=True
                        )

        if delivered_count > 0:
            logger.debug(f"✅ Delivered message to {delivered_count} handlers")

    async def start(self):
        """Start message processing"""
        if self._running:
            logger.warning("⚠️ MessageBus already running")
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._process_messages())
        logger.info("▶️ MessageBus started")

    async def stop(self):
        """Stop message processing"""
        if not self._running:
            return

        self._running = False

        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
            self._processor_task = None

        logger.info("⏹️ MessageBus stopped")

    def get_stats(self) -> dict[str, Any]:
        """
        Get message bus statistics.

        Returns:
            Dictionary with:
            - messages_published: Total messages published
            - messages_delivered: Total messages delivered
            - messages_filtered: Messages blocked by filters
            - messages_dropped: Messages dropped (queue full)
            - subscriptions: Number of active subscriptions
            - queue_sizes: Current size of each priority queue
        """
        return {
            **self.stats,
            "subscriptions": len(self._subscriptions),
            "queue_sizes": {
                priority.name: self._queues[priority].qsize()
                for priority in MessagePriority
            },
        }

    def clear_queues(self):
        """Clear all message queues (for testing/reset)"""
        for queue in self._queues.values():
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

        logger.info("🧹 Cleared all message queues")

    def __repr__(self) -> str:
        return f"<MessageBus subscriptions={len(self._subscriptions)} running={self._running}>"


# Global singleton
_message_bus_instance: MessageBus | None = None


def get_message_bus() -> MessageBus:
    """
    Get global MessageBus instance (singleton).

    Returns:
        Global MessageBus instance
    """
    global _message_bus_instance

    if _message_bus_instance is None:
        _message_bus_instance = MessageBus()

    return _message_bus_instance
