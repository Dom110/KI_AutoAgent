from __future__ import annotations

"""
ChatAgent - Base class for agents with chat and streaming capabilities
Extends BaseAgent with WebSocket streaming support
"""

import asyncio
import logging
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .base_agent import AgentConfig, BaseAgent, TaskRequest

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class StreamMessage:
    """Message for streaming responses"""

    type: str  # 'text', 'thinking', 'tool_use', 'error', 'complete'
    content: str
    agent: str
    timestamp: datetime = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "content": self.content,
            "agent": self.agent,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class ChatAgent(BaseAgent):
    """
    Chat-enabled agent with streaming support
    Provides WebSocket streaming capabilities for real-time responses
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.active_streams: dict[str, asyncio.Queue] = {}
        self.stream_handlers: dict[str, Callable] = {}

    async def handle_chat_stream(
        self,
        request: TaskRequest,
        stream_callback: Callable[[StreamMessage], None] | None = None,
    ) -> AsyncGenerator[StreamMessage, None]:
        """
        Handle chat request with streaming response
        Yields StreamMessage objects for real-time updates
        """
        f"stream_{self.config.agent_id}_{datetime.now().timestamp()}"

        try:
            # Send initial thinking message
            thinking_msg = StreamMessage(
                type="thinking",
                content=f"{self.config.icon} {self.name} is thinking...",
                agent=self.config.agent_id,
            )
            if stream_callback:
                await stream_callback(thinking_msg)
            yield thinking_msg

            # Process with memory if available
            if self.memory_manager:
                # Search for similar conversations
                similar = await self.memory_manager.search(
                    request.prompt, memory_type="episodic", k=3
                )

                if similar:
                    context_msg = StreamMessage(
                        type="text",
                        content="Found relevant context from previous conversations...",
                        agent=self.config.agent_id,
                        metadata={"similar_count": len(similar)},
                    )
                    if stream_callback:
                        await stream_callback(context_msg)
                    yield context_msg

            # Execute the main task with streaming
            async for chunk in self._execute_streaming(request):
                if stream_callback:
                    await stream_callback(chunk)
                yield chunk

            # Send completion message
            complete_msg = StreamMessage(
                type="complete",
                content=f"✅ {self.name} completed the task",
                agent=self.config.agent_id,
                metadata={
                    "execution_count": self.execution_count,
                    "tokens_used": self.total_tokens_used,
                },
            )
            if stream_callback:
                await stream_callback(complete_msg)
            yield complete_msg

        except Exception as e:
            error_msg = StreamMessage(
                type="error", content=f"❌ Error: {str(e)}", agent=self.config.agent_id
            )
            if stream_callback:
                await stream_callback(error_msg)
            yield error_msg
            logger.error(f"Stream error in {self.name}: {e}")

    async def _execute_streaming(
        self, request: TaskRequest
    ) -> AsyncGenerator[StreamMessage, None]:
        """
        Execute task with streaming output
        Override in subclasses for specific streaming behavior
        """
        # Default implementation - non-streaming execution
        result = await self.execute(request)

        # Convert result to stream messages
        if result.status == "success":
            yield StreamMessage(
                type="text",
                content=result.content,
                agent=self.config.agent_id,
                metadata={"status": result.status},
            )
        else:
            yield StreamMessage(
                type="error",
                content=result.content,
                agent=self.config.agent_id,
                metadata={"status": result.status},
            )

    async def handle_websocket(self, websocket, client_id: str):
        """
        Handle WebSocket connection for this agent
        Manages bidirectional streaming communication
        """
        logger.info(f"🔌 {self.name} connected to client {client_id}")

        try:
            while True:
                # Receive message from client
                data = await websocket.receive_json()

                message_type = data.get("type", "chat")

                if message_type == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue

                # Create task request
                request = TaskRequest(
                    prompt=data.get("content", ""),
                    context=data.get("context", {}),
                    command=data.get("command"),
                    thinking_mode=data.get("thinking_mode", False),
                    mode=data.get("mode", "auto"),
                )

                # Stream response
                async for msg in self.handle_chat_stream(request):
                    await websocket.send_json(msg.to_dict())

        except Exception as e:
            logger.error(f"WebSocket error in {self.name}: {e}")
            await websocket.send_json(
                {"type": "error", "content": str(e), "agent": self.config.agent_id}
            )

    async def broadcast_to_streams(self, message: StreamMessage):
        """Broadcast message to all active streams"""
        for stream_id, queue in self.active_streams.items():
            await queue.put(message)

    def format_response(self, content: str, status: str = "success") -> str:
        """
        Format response with agent-specific styling
        Can be overridden by subclasses for custom formatting
        """
        if status == "success":
            return f"### {self.config.icon} {self.name}\n\n{content}"
        else:
            return f"### ❌ {self.name} Error\n\n{content}"

    def get_chat_status(self) -> dict[str, Any]:
        """Get chat-specific status information"""
        base_status = self.get_status()
        base_status.update(
            {
                "active_streams": len(self.active_streams),
                "streaming_enabled": True,
                "chat_capabilities": [
                    "streaming",
                    "websocket",
                    "real-time",
                    "memory-enhanced",
                ],
            }
        )
        return base_status
