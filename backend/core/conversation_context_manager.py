"""
Conversation Context Manager for v6 Multi-Turn Conversations

Manages conversation history with context window management and summarization.

Features:
- Multi-turn conversation tracking
- Context window management (token limits)
- Conversation summarization
- History pruning
- Context relevance scoring

Author: KI AutoAgent Team
Date: 2025-10-12
Version: v6.1
"""

import asyncio
import logging
from datetime import datetime
from typing import Any
from collections import deque

# LangChain imports for summarization
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class ConversationContextManager:
    """
    Manages multi-turn conversation context with window management.

    Features:
    - Track conversation history per session
    - Automatic context window management (token limits)
    - Conversation summarization when context exceeds limits
    - Message relevance scoring
    - History pruning strategies
    - Context compression

    Usage:
        manager = ConversationContextManager(max_tokens=4000)

        # Add messages
        await manager.add_message(
            conversation_id="session_123",
            role="user",
            content="Create a Todo app"
        )

        await manager.add_message(
            conversation_id="session_123",
            role="assistant",
            content="I'll create a Todo app..."
        )

        # Get conversation history (auto-managed)
        history = await manager.get_conversation(
            conversation_id="session_123"
        )

        # Summarize if needed
        summary = await manager.summarize_conversation(
            conversation_id="session_123"
        )
    """

    def __init__(
        self,
        max_tokens: int = 8000,
        summarize_threshold: float = 0.8,
        summary_model: str = "gpt-4o-mini"
    ):
        """
        Initialize Conversation Context Manager.

        Args:
            max_tokens: Maximum tokens to keep in context window
            summarize_threshold: Trigger summarization at this % of max_tokens
            summary_model: Model to use for summarization
        """
        # Conversations (conversation_id -> deque of messages)
        self._conversations: dict[str, deque[dict[str, Any]]] = {}

        # Conversation metadata (conversation_id -> metadata)
        self._metadata: dict[str, dict[str, Any]] = {}

        # Summaries (conversation_id -> list of summaries)
        self._summaries: dict[str, list[dict[str, Any]]] = {}

        # Configuration
        self.max_tokens = max_tokens
        self.summarize_threshold = summarize_threshold
        self.summary_model = summary_model

        # Token counter (approximate: 4 chars ≈ 1 token)
        self.chars_per_token = 4

        # Lock for thread safety
        self._lock = asyncio.Lock()

        logger.info("✅ ConversationContextManager initialized")
        logger.info(f"   Max tokens: {max_tokens}")
        logger.info(f"   Summarize threshold: {summarize_threshold * 100}%")

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None
    ) -> None:
        """
        Add message to conversation.

        Args:
            conversation_id: Conversation identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Additional metadata
        """
        async with self._lock:
            # Initialize conversation if needed
            if conversation_id not in self._conversations:
                self._conversations[conversation_id] = deque()
                self._metadata[conversation_id] = {
                    "created_at": datetime.now().isoformat(),
                    "message_count": 0,
                    "total_tokens": 0,
                    "summarized_count": 0
                }
                self._summaries[conversation_id] = []

            # Create message
            message = {
                "role": role,
                "content": content,
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat(),
                "tokens": len(content) // self.chars_per_token
            }

            # Add to conversation
            self._conversations[conversation_id].append(message)

            # Update metadata
            self._metadata[conversation_id]["message_count"] += 1
            self._metadata[conversation_id]["total_tokens"] += message["tokens"]
            self._metadata[conversation_id]["last_message_at"] = message["timestamp"]

            logger.debug(f"📨 Message added to {conversation_id} (role: {role}, tokens: {message['tokens']})")

            # Check if context window exceeded
            if self._should_summarize(conversation_id):
                await self._auto_summarize(conversation_id)

    async def get_conversation(
        self,
        conversation_id: str,
        include_summaries: bool = True,
        max_messages: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Get conversation history.

        Args:
            conversation_id: Conversation identifier
            include_summaries: Include summaries at the beginning
            max_messages: Limit number of messages (most recent)

        Returns:
            List of messages (with summaries if requested)
        """
        async with self._lock:
            if conversation_id not in self._conversations:
                return []

            messages = list(self._conversations[conversation_id])

            # Limit messages
            if max_messages:
                messages = messages[-max_messages:]

            # Add summaries at beginning
            result = []

            if include_summaries and conversation_id in self._summaries:
                for summary in self._summaries[conversation_id]:
                    result.append({
                        "role": "system",
                        "content": f"[Summary of previous conversation]\n{summary['summary']}",
                        "metadata": {"is_summary": True, "created_at": summary["created_at"]},
                        "timestamp": summary["created_at"],
                        "tokens": summary["tokens"]
                    })

            result.extend(messages)

            return result

    async def get_metadata(
        self,
        conversation_id: str
    ) -> dict[str, Any] | None:
        """
        Get conversation metadata.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Metadata dictionary or None
        """
        async with self._lock:
            return self._metadata.get(conversation_id)

    async def summarize_conversation(
        self,
        conversation_id: str,
        force: bool = False
    ) -> str | None:
        """
        Summarize conversation.

        Args:
            conversation_id: Conversation identifier
            force: Force summarization even if not needed

        Returns:
            Summary text or None if no summarization needed
        """
        async with self._lock:
            if conversation_id not in self._conversations:
                return None

            messages = list(self._conversations[conversation_id])

            if not messages:
                return None

            # Check if summarization needed
            if not force and not self._should_summarize(conversation_id):
                return None

            # Create summary
            summary_text = await self._create_summary(messages)

            if summary_text:
                # Store summary
                summary = {
                    "summary": summary_text,
                    "created_at": datetime.now().isoformat(),
                    "message_count": len(messages),
                    "tokens": len(summary_text) // self.chars_per_token
                }

                self._summaries[conversation_id].append(summary)

                # Prune old messages (keep recent ones)
                self._conversations[conversation_id] = deque(list(messages)[-10:])

                # Update metadata
                self._metadata[conversation_id]["summarized_count"] += 1
                self._metadata[conversation_id]["total_tokens"] = sum(
                    m["tokens"] for m in self._conversations[conversation_id]
                )

                logger.info(f"📝 Conversation summarized: {conversation_id}")
                logger.info(f"   Messages: {len(messages)} → {len(self._conversations[conversation_id])}")
                logger.info(f"   Summary tokens: {summary['tokens']}")

                return summary_text

            return None

    async def clear_conversation(
        self,
        conversation_id: str
    ) -> bool:
        """
        Clear conversation history.

        Args:
            conversation_id: Conversation identifier

        Returns:
            True if cleared, False if not found
        """
        async with self._lock:
            if conversation_id in self._conversations:
                del self._conversations[conversation_id]
                self._metadata.pop(conversation_id, None)
                self._summaries.pop(conversation_id, None)

                logger.info(f"🗑️  Conversation cleared: {conversation_id}")
                return True

            return False

    async def list_conversations(self) -> list[dict[str, Any]]:
        """
        List all conversations.

        Returns:
            List of conversation metadata
        """
        async with self._lock:
            return [
                {
                    "conversation_id": cid,
                    **metadata
                }
                for cid, metadata in self._metadata.items()
            ]

    async def prune_old_messages(
        self,
        conversation_id: str,
        keep_count: int = 20
    ) -> int:
        """
        Prune old messages, keeping only recent ones.

        Args:
            conversation_id: Conversation identifier
            keep_count: Number of messages to keep

        Returns:
            Number of messages pruned
        """
        async with self._lock:
            if conversation_id not in self._conversations:
                return 0

            messages = self._conversations[conversation_id]
            original_count = len(messages)

            if original_count <= keep_count:
                return 0

            # Keep only recent messages
            self._conversations[conversation_id] = deque(list(messages)[-keep_count:])

            pruned_count = original_count - keep_count

            # Update metadata
            self._metadata[conversation_id]["total_tokens"] = sum(
                m["tokens"] for m in self._conversations[conversation_id]
            )

            logger.info(f"✂️  Pruned {pruned_count} messages from {conversation_id}")

            return pruned_count

    async def get_context_window_usage(
        self,
        conversation_id: str
    ) -> dict[str, Any]:
        """
        Get context window usage statistics.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Usage statistics
        """
        async with self._lock:
            if conversation_id not in self._conversations:
                return {
                    "total_tokens": 0,
                    "max_tokens": self.max_tokens,
                    "usage_percent": 0.0,
                    "available_tokens": self.max_tokens
                }

            metadata = self._metadata[conversation_id]
            total_tokens = metadata["total_tokens"]

            return {
                "total_tokens": total_tokens,
                "max_tokens": self.max_tokens,
                "usage_percent": (total_tokens / self.max_tokens) * 100,
                "available_tokens": self.max_tokens - total_tokens,
                "should_summarize": self._should_summarize(conversation_id)
            }

    def _should_summarize(
        self,
        conversation_id: str
    ) -> bool:
        """Check if conversation should be summarized."""
        metadata = self._metadata.get(conversation_id)

        if not metadata:
            return False

        total_tokens = metadata["total_tokens"]
        threshold = self.max_tokens * self.summarize_threshold

        return total_tokens > threshold

    async def _auto_summarize(
        self,
        conversation_id: str
    ):
        """Automatically summarize conversation when threshold reached."""
        logger.info(f"🔄 Auto-summarizing conversation: {conversation_id}")
        await self.summarize_conversation(conversation_id, force=True)

    async def _create_summary(
        self,
        messages: list[dict[str, Any]]
    ) -> str | None:
        """
        Create summary of messages using LLM.

        Args:
            messages: List of messages to summarize

        Returns:
            Summary text or None if failed
        """
        try:
            # Prepare conversation text
            conversation_text = []

            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                conversation_text.append(f"{role.upper()}: {content}")

            text = "\n\n".join(conversation_text)

            # Summarize with LLM
            llm = ChatOpenAI(
                model=self.summary_model,
                temperature=0.3,
                max_tokens=500
            )

            response = await llm.ainvoke([
                SystemMessage(content="You are a conversation summarizer. Create a concise summary of the following conversation, capturing key points, decisions, and context."),
                HumanMessage(content=f"Summarize this conversation:\n\n{text}")
            ])

            summary = response.content

            logger.debug(f"✅ Summary created ({len(summary)} chars)")

            return summary

        except Exception as e:
            logger.error(f"❌ Failed to create summary: {e}", exc_info=True)
            return None


# Global singleton
_conversation_context_instance: ConversationContextManager | None = None


def get_conversation_context(
    max_tokens: int | None = None
) -> ConversationContextManager:
    """
    Get global ConversationContextManager instance (singleton).

    Args:
        max_tokens: Max tokens (first call only)

    Returns:
        Global ConversationContextManager instance
    """
    global _conversation_context_instance

    if _conversation_context_instance is None:
        _conversation_context_instance = ConversationContextManager(
            max_tokens=max_tokens or 8000
        )

    return _conversation_context_instance
