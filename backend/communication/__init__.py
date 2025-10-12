"""
Communication module for multi-agent messaging

Provides message bus infrastructure for inter-agent communication.
"""

from communication.message_bus_v6 import (
    MessageBus,
    Message,
    MessagePriority,
    get_message_bus,
)

__all__ = [
    "MessageBus",
    "Message",
    "MessagePriority",
    "get_message_bus",
]
