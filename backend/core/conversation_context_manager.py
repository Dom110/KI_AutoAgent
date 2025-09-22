"""
ConversationContextManager - Manages conversation context and history
Ensures agents can access and build upon previous outputs
"""

import json
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConversationEntry:
    """Individual conversation entry"""
    timestamp: str
    agent: str
    step: str
    input: str
    output: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    tokens_used: int = 0
    execution_time: float = 0.0

class ConversationContextManager:
    """
    Manages conversation context across multiple agent interactions
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, max_history_size: int = 50):
        """Initialize conversation context manager"""
        if self._initialized:
            return

        self.conversation_history: List[ConversationEntry] = []
        self.max_history_size = max_history_size
        self.current_conversation_id: Optional[str] = None

        # Statistics
        self.total_entries = 0
        self.total_tokens = 0

        self._initialized = True
        logger.info(f"ConversationContextManager initialized with max history: {max_history_size}")

    def add_entry(
        self,
        agent: str,
        step: str,
        input_text: str,
        output_text: str,
        metadata: Optional[Dict] = None,
        tokens_used: int = 0,
        execution_time: float = 0.0
    ) -> ConversationEntry:
        """Add a new entry to conversation history"""
        entry = ConversationEntry(
            timestamp=datetime.now().isoformat(),
            agent=agent,
            step=step,
            input=input_text,
            output=output_text,
            metadata=metadata or {},
            tokens_used=tokens_used,
            execution_time=execution_time
        )

        self.conversation_history.append(entry)
        self.total_entries += 1
        self.total_tokens += tokens_used

        # Trim history if exceeds max size
        if len(self.conversation_history) > self.max_history_size:
            self.conversation_history = self.conversation_history[-self.max_history_size:]

        logger.debug(f"Added entry from {agent} ({step}), history size: {len(self.conversation_history)}")
        return entry

    def get_recent_history(self, limit: int = 10) -> List[ConversationEntry]:
        """Get recent conversation history"""
        return self.conversation_history[-limit:] if self.conversation_history else []

    def get_agent_history(
        self,
        agent_name: str,
        limit: int = 5
    ) -> List[ConversationEntry]:
        """Get conversation history for specific agent"""
        agent_entries = [
            entry for entry in self.conversation_history
            if entry.agent == agent_name
        ]
        return agent_entries[-limit:] if agent_entries else []

    def get_formatted_context(
        self,
        limit: int = 10,
        max_input_length: int = 200,
        max_output_length: int = 500
    ) -> str:
        """Get formatted conversation context for prompts"""
        recent = self.get_recent_history(limit)

        if not recent:
            return ""

        context_lines = ["## Conversation History:"]

        for entry in recent:
            context_lines.append(f"\n### {entry.agent} ({entry.step}) - {entry.timestamp}:")

            # Truncate input if needed
            input_text = entry.input
            if len(input_text) > max_input_length:
                input_text = input_text[:max_input_length] + "..."

            # Truncate output if needed
            output_text = entry.output
            if len(output_text) > max_output_length:
                output_text = output_text[:max_output_length] + "..."

            context_lines.append(f"**Input:** {input_text}")
            context_lines.append(f"**Output:** {output_text}")

            # Add metadata if present
            if entry.metadata:
                context_lines.append(f"**Metadata:** {entry.metadata}")

        return "\n".join(context_lines)

    def get_compact_context(self, limit: int = 5) -> Dict[str, Any]:
        """Get compact context as dictionary for API calls"""
        recent = self.get_recent_history(limit)

        return {
            "conversation_id": self.current_conversation_id,
            "entries": [
                {
                    "agent": entry.agent,
                    "step": entry.step,
                    "input": entry.input[:100],  # Abbreviated
                    "output": entry.output[:200],  # Abbreviated
                    "timestamp": entry.timestamp
                }
                for entry in recent
            ]
        }

    def get_last_output(self) -> Optional[str]:
        """Get the last output from any agent"""
        if self.conversation_history:
            return self.conversation_history[-1].output
        return None

    def get_last_agent_output(self, agent_name: str) -> Optional[str]:
        """Get the last output from specific agent"""
        for entry in reversed(self.conversation_history):
            if entry.agent == agent_name:
                return entry.output
        return None

    def find_related_entries(
        self,
        keywords: List[str],
        limit: int = 10
    ) -> List[ConversationEntry]:
        """Find entries containing specific keywords"""
        results = []

        for entry in self.conversation_history:
            text = f"{entry.input} {entry.output}".lower()
            if any(keyword.lower() in text for keyword in keywords):
                results.append(entry)

        return results[-limit:] if len(results) > limit else results

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the conversation"""
        if not self.conversation_history:
            return {
                "total_entries": 0,
                "agents_involved": [],
                "total_tokens": 0,
                "average_execution_time": 0
            }

        agents = list(set(entry.agent for entry in self.conversation_history))
        total_time = sum(entry.execution_time for entry in self.conversation_history)
        avg_time = total_time / len(self.conversation_history)

        return {
            "total_entries": len(self.conversation_history),
            "agents_involved": agents,
            "total_tokens": self.total_tokens,
            "average_execution_time": avg_time,
            "first_entry": self.conversation_history[0].timestamp,
            "last_entry": self.conversation_history[-1].timestamp
        }

    def start_new_conversation(self, conversation_id: Optional[str] = None):
        """Start a new conversation (clear history)"""
        self.conversation_history.clear()
        self.current_conversation_id = conversation_id or f"conv_{int(time.time())}"
        self.total_entries = 0
        self.total_tokens = 0
        logger.info(f"Started new conversation: {self.current_conversation_id}")

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
        self.total_entries = 0
        self.total_tokens = 0
        logger.info("Conversation history cleared")

    def export_history(self) -> str:
        """Export conversation history as JSON"""
        export_data = {
            "conversation_id": self.current_conversation_id,
            "timestamp": datetime.now().isoformat(),
            "total_entries": self.total_entries,
            "total_tokens": self.total_tokens,
            "history": [
                {
                    "timestamp": entry.timestamp,
                    "agent": entry.agent,
                    "step": entry.step,
                    "input": entry.input,
                    "output": entry.output,
                    "metadata": entry.metadata,
                    "tokens_used": entry.tokens_used,
                    "execution_time": entry.execution_time
                }
                for entry in self.conversation_history
            ]
        }

        return json.dumps(export_data, indent=2)

    def import_history(self, json_data: str) -> bool:
        """Import conversation history from JSON"""
        try:
            data = json.loads(json_data)

            self.current_conversation_id = data.get("conversation_id")
            self.total_entries = data.get("total_entries", 0)
            self.total_tokens = data.get("total_tokens", 0)

            self.conversation_history.clear()

            for entry_data in data.get("history", []):
                entry = ConversationEntry(
                    timestamp=entry_data["timestamp"],
                    agent=entry_data["agent"],
                    step=entry_data["step"],
                    input=entry_data["input"],
                    output=entry_data["output"],
                    metadata=entry_data.get("metadata", {}),
                    tokens_used=entry_data.get("tokens_used", 0),
                    execution_time=entry_data.get("execution_time", 0.0)
                )
                self.conversation_history.append(entry)

            logger.info(f"Imported {len(self.conversation_history)} conversation entries")
            return True

        except Exception as e:
            logger.error(f"Failed to import history: {e}")
            return False

    def get_context_for_agent(
        self,
        agent_name: str,
        include_self: bool = False,
        limit: int = 10
    ) -> str:
        """Get context specifically formatted for an agent"""
        entries = []

        for entry in self.get_recent_history(limit):
            # Skip own entries unless requested
            if not include_self and entry.agent == agent_name:
                continue
            entries.append(entry)

        if not entries:
            return ""

        context_lines = ["## Previous Agent Outputs:"]

        for entry in entries:
            context_lines.append(f"\n**{entry.agent}** ({entry.step}):")
            context_lines.append(f"Input: {entry.input[:150]}...")
            context_lines.append(f"Output: {entry.output[:300]}...")

        return "\n".join(context_lines)

    def merge_conversation(self, other_history: List[ConversationEntry]):
        """Merge another conversation history into current"""
        for entry in other_history:
            self.conversation_history.append(entry)

        # Sort by timestamp and trim
        self.conversation_history.sort(key=lambda e: e.timestamp)

        if len(self.conversation_history) > self.max_history_size:
            self.conversation_history = self.conversation_history[-self.max_history_size:]

        logger.info(f"Merged conversations, total entries: {len(self.conversation_history)}")

# Global singleton instance
def get_conversation_context() -> ConversationContextManager:
    """Get the singleton ConversationContextManager instance"""
    return ConversationContextManager()