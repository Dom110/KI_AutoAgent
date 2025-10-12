"""
Test Multi-Agent Message Bus v6

Tests pub/sub messaging, direct messaging, broadcast, filtering, and priority queues.
"""

import asyncio
import pytest
from communication.message_bus_v6 import (
    MessageBus,
    Message,
    MessagePriority,
    get_message_bus,
)


@pytest.fixture
def message_bus():
    """Create fresh message bus for each test"""
    bus = MessageBus()
    yield bus
    # Cleanup
    asyncio.run(bus.stop())


@pytest.mark.asyncio
async def test_subscribe_and_publish(message_bus):
    """Test basic subscribe and publish"""
    received = []

    async def handler(payload):
        received.append(payload)

    await message_bus.subscribe("test.topic", handler)
    await message_bus.publish("test.topic", {"message": "Hello"})

    # Start bus to process messages
    await message_bus.start()
    await asyncio.sleep(0.1)  # Allow processing
    await message_bus.stop()

    assert len(received) == 1
    assert received[0] == {"message": "Hello"}


@pytest.mark.asyncio
async def test_multiple_subscribers(message_bus):
    """Test multiple subscribers to same topic"""
    received1 = []
    received2 = []

    async def handler1(payload):
        received1.append(payload)

    async def handler2(payload):
        received2.append(payload)

    await message_bus.subscribe("test.topic", handler1)
    await message_bus.subscribe("test.topic", handler2)
    await message_bus.publish("test.topic", {"data": "test"})

    await message_bus.start()
    await asyncio.sleep(0.1)
    await message_bus.stop()

    assert len(received1) == 1
    assert len(received2) == 1
    assert received1[0] == received2[0] == {"data": "test"}


@pytest.mark.asyncio
async def test_wildcard_subscription(message_bus):
    """Test wildcard topic matching"""
    received = []

    async def handler(payload):
        received.append(payload)

    # Subscribe to wildcard
    await message_bus.subscribe("agent.*", handler)

    # Publish to specific topics
    await message_bus.publish("agent.architect", {"msg": "1"})
    await message_bus.publish("agent.codesmith", {"msg": "2"})
    await message_bus.publish("other.topic", {"msg": "3"})  # Should not match

    await message_bus.start()
    await asyncio.sleep(0.1)
    await message_bus.stop()

    assert len(received) == 2
    assert received[0]["msg"] == "1"
    assert received[1]["msg"] == "2"


@pytest.mark.asyncio
async def test_broadcast(message_bus):
    """Test broadcast to all subscribers"""
    received1 = []
    received2 = []

    async def handler1(payload):
        received1.append(payload)

    async def handler2(payload):
        received2.append(payload)

    await message_bus.subscribe("topic1", handler1)
    await message_bus.subscribe("topic2", handler2)

    # Broadcast to all
    count = await message_bus.broadcast({"announcement": "update"})

    await message_bus.start()
    await asyncio.sleep(0.1)
    await message_bus.stop()

    assert count == 2  # Broadcasted to 2 topics
    assert len(received1) == 1
    assert len(received2) == 1


@pytest.mark.asyncio
async def test_message_priority(message_bus):
    """Test priority queue ordering"""
    received = []

    async def handler(payload):
        received.append(payload["priority"])

    await message_bus.subscribe("test", handler)

    # Publish in reverse priority order
    await message_bus.publish("test", {"priority": "LOW"}, MessagePriority.LOW)
    await message_bus.publish("test", {"priority": "URGENT"}, MessagePriority.URGENT)
    await message_bus.publish("test", {"priority": "NORMAL"}, MessagePriority.NORMAL)
    await message_bus.publish("test", {"priority": "HIGH"}, MessagePriority.HIGH)

    await message_bus.start()
    await asyncio.sleep(0.1)
    await message_bus.stop()

    # Should be processed in priority order: URGENT, HIGH, NORMAL, LOW
    assert received == ["URGENT", "HIGH", "NORMAL", "LOW"]


@pytest.mark.asyncio
async def test_message_filtering(message_bus):
    """Test message filtering"""
    received = []

    async def handler(payload):
        received.append(payload)

    # Add filter: only allow messages from "architect"
    message_bus.add_filter(lambda msg: msg.sender == "architect")

    await message_bus.subscribe("test", handler)

    # Publish with different senders
    await message_bus.publish("test", {"msg": "1"}, sender="architect")  # Should pass
    await message_bus.publish("test", {"msg": "2"}, sender="codesmith")  # Should be filtered

    await message_bus.start()
    await asyncio.sleep(0.1)
    await message_bus.stop()

    assert len(received) == 1
    assert received[0]["msg"] == "1"


@pytest.mark.asyncio
async def test_unsubscribe(message_bus):
    """Test unsubscribe functionality"""
    received = []

    async def handler(payload):
        received.append(payload)

    await message_bus.subscribe("test", handler)
    await message_bus.publish("test", {"msg": "1"})

    await message_bus.start()
    await asyncio.sleep(0.1)

    # Unsubscribe
    result = await message_bus.unsubscribe("test", handler)
    assert result is True

    # Publish again (should not be received)
    await message_bus.publish("test", {"msg": "2"})
    await asyncio.sleep(0.1)
    await message_bus.stop()

    assert len(received) == 1  # Only first message


@pytest.mark.asyncio
async def test_stats(message_bus):
    """Test message bus statistics"""
    async def handler(payload):
        pass

    await message_bus.subscribe("test", handler)

    # Publish some messages
    await message_bus.publish("test", {"msg": "1"})
    await message_bus.publish("test", {"msg": "2"})

    # Add filter to block one message
    message_bus.add_filter(lambda msg: msg.payload.get("msg") != "3")
    await message_bus.publish("test", {"msg": "3"})  # Will be filtered

    await message_bus.start()
    await asyncio.sleep(0.1)
    await message_bus.stop()

    stats = message_bus.get_stats()

    assert stats["messages_published"] == 2  # 2 passed filters
    assert stats["messages_filtered"] == 1  # 1 blocked by filter
    assert stats["messages_delivered"] == 2  # 2 delivered
    assert stats["subscriptions"] == 1


@pytest.mark.asyncio
async def test_sync_handler(message_bus):
    """Test that sync handlers work too"""
    received = []

    def sync_handler(payload):  # Not async!
        received.append(payload)

    await message_bus.subscribe("test", sync_handler)
    await message_bus.publish("test", {"msg": "sync"})

    await message_bus.start()
    await asyncio.sleep(0.1)
    await message_bus.stop()

    assert len(received) == 1
    assert received[0]["msg"] == "sync"


@pytest.mark.asyncio
async def test_handler_error_doesnt_crash_bus(message_bus):
    """Test that handler errors don't crash the message bus"""
    received_by_good_handler = []

    async def bad_handler(payload):
        raise ValueError("Intentional error")

    async def good_handler(payload):
        received_by_good_handler.append(payload)

    await message_bus.subscribe("test", bad_handler)
    await message_bus.subscribe("test", good_handler)

    await message_bus.publish("test", {"msg": "test"})

    await message_bus.start()
    await asyncio.sleep(0.1)
    await message_bus.stop()

    # Good handler should still receive message despite bad handler error
    assert len(received_by_good_handler) == 1


def test_singleton_message_bus():
    """Test global singleton"""
    bus1 = get_message_bus()
    bus2 = get_message_bus()

    assert bus1 is bus2  # Same instance


def test_message_creation():
    """Test Message dataclass"""
    msg = Message(
        topic="test.topic",
        payload={"data": "test"},
        priority=MessagePriority.HIGH,
        sender="architect",
        metadata={"key": "value"},
    )

    assert msg.topic == "test.topic"
    assert msg.payload == {"data": "test"}
    assert msg.priority == MessagePriority.HIGH
    assert msg.sender == "architect"
    assert msg.metadata == {"key": "value"}
    assert msg.timestamp is not None


@pytest.mark.asyncio
async def test_clear_queues(message_bus):
    """Test queue clearing"""
    await message_bus.publish("test", {"msg": "1"})
    await message_bus.publish("test", {"msg": "2"})

    # Queues should have messages
    stats = message_bus.get_stats()
    assert stats["messages_published"] == 2

    # Clear queues
    message_bus.clear_queues()

    # Start bus - should not process cleared messages
    received = []

    async def handler(payload):
        received.append(payload)

    await message_bus.subscribe("test", handler)
    await message_bus.start()
    await asyncio.sleep(0.1)
    await message_bus.stop()

    assert len(received) == 0  # No messages processed


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
