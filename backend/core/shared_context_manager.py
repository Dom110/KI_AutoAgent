"""
SharedContextManager - Manages shared context between agents for collaboration
Enables agents to share knowledge, decisions, and intermediate results in real-time
"""

import asyncio
import time
import json
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class ContextUpdate:
    """Context update event"""
    agent_id: str
    timestamp: float
    key: str
    value: Any
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ContextLock:
    """Lock information for context keys"""
    agent_id: str
    key: str
    acquired_at: float
    timeout: float

class SharedContextManager:
    """
    Manages shared context between agents for real-time collaboration
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the shared context manager"""
        if self._initialized:
            return

        # Core context storage
        self.context: Dict[str, Any] = {}
        self.context_history: List[ContextUpdate] = []

        # Subscribers for real-time updates
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.filters: Dict[str, Callable] = {}

        # Locking mechanism
        self.locks: Dict[str, ContextLock] = {}
        self.lock_timeout_default = 5.0  # seconds

        # Versioning
        self.version = 0

        # Statistics
        self.total_updates = 0
        self.total_conflicts = 0

        # Initialize default context structure
        self._initialize_context()

        self._initialized = True
        logger.info("SharedContextManager initialized")

    def _initialize_context(self):
        """Initialize with default context structure"""
        self.context = {
            "project_structure": {},
            "architecture_decisions": {},
            "code_patterns": {},
            "research_findings": {},
            "validation_results": {},
            "current_workflow": None,
            "global_memories": [],
            "agent_outputs": {},
            "conversation_context": [],
            "active_tasks": {},
            "shared_learnings": []
        }

    async def update_context(
        self,
        agent_id: str,
        key: str,
        value: Any,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Update context with new information"""
        # Check if key is locked by another agent
        if await self._check_lock(key, agent_id):
            logger.warning(f"Context key '{key}' is locked by another agent")
            self.total_conflicts += 1
            return False

        # Create update record
        update = ContextUpdate(
            agent_id=agent_id,
            timestamp=time.time(),
            key=key,
            value=value,
            metadata={
                **(metadata or {}),
                "version": self.version + 1
            }
        )

        # Update the context
        self.context[key] = value
        self.version += 1
        self.total_updates += 1

        # Store in history
        self.context_history.append(update)

        # Trim history if too long
        if len(self.context_history) > 1000:
            self.context_history = self.context_history[-500:]

        # Notify subscribers
        await self._notify_subscribers(update)

        logger.debug(f"Agent {agent_id} updated context key '{key}'")
        return True

    def get_context(self, key: Optional[str] = None) -> Any:
        """Get current context value"""
        if key:
            return self.context.get(key)
        return dict(self.context)

    def get_context_with_history(
        self,
        key: str,
        limit: int = 10
    ) -> List[ContextUpdate]:
        """Get context with history of updates"""
        history = [
            update for update in self.context_history
            if update.key == key
        ]
        return history[-limit:] if history else []

    def subscribe(
        self,
        agent_id: str,
        callback: Callable[[ContextUpdate], None],
        filter_fn: Optional[Callable[[ContextUpdate], bool]] = None
    ):
        """Subscribe to context updates"""
        self.subscribers[agent_id].append(callback)

        if filter_fn:
            self.filters[agent_id] = filter_fn

        logger.debug(f"Agent {agent_id} subscribed to context updates")

    def unsubscribe(self, agent_id: str):
        """Unsubscribe from context updates"""
        if agent_id in self.subscribers:
            del self.subscribers[agent_id]

        if agent_id in self.filters:
            del self.filters[agent_id]

        logger.debug(f"Agent {agent_id} unsubscribed from context updates")

    async def acquire_lock(
        self,
        agent_id: str,
        key: str,
        timeout: Optional[float] = None
    ) -> bool:
        """Acquire a lock on a context key for atomic updates"""
        if timeout is None:
            timeout = self.lock_timeout_default

        start_time = time.time()

        while key in self.locks:
            lock = self.locks[key]

            # Check if lock has expired
            if time.time() - lock.acquired_at > lock.timeout:
                # Lock expired, remove it
                del self.locks[key]
                logger.debug(f"Expired lock on '{key}' removed")
                break

            # Check if same agent already holds the lock
            if lock.agent_id == agent_id:
                return True

            # Check if we've exceeded timeout
            if time.time() - start_time > timeout:
                logger.warning(f"Timeout acquiring lock for key '{key}'")
                return False

            # Wait a bit before retrying
            await asyncio.sleep(0.1)

        # Acquire the lock
        self.locks[key] = ContextLock(
            agent_id=agent_id,
            key=key,
            acquired_at=time.time(),
            timeout=timeout
        )

        logger.debug(f"Agent {agent_id} acquired lock on '{key}'")
        return True

    def release_lock(self, agent_id: str, key: str) -> bool:
        """Release a lock on a context key"""
        if key in self.locks:
            lock = self.locks[key]

            if lock.agent_id != agent_id:
                logger.warning(f"Agent {agent_id} cannot release lock held by {lock.agent_id}")
                return False

            del self.locks[key]
            logger.debug(f"Agent {agent_id} released lock on '{key}'")
            return True

        return False

    async def merge_contexts(
        self,
        agent_id: str,
        updates: Dict[str, Any],
        strategy: str = "overwrite"
    ) -> bool:
        """Merge multiple context updates atomically"""
        # Try to acquire locks for all keys
        locked_keys = []

        try:
            for key in updates.keys():
                if await self.acquire_lock(agent_id, key):
                    locked_keys.append(key)
                else:
                    # Failed to acquire a lock, release all and fail
                    for locked_key in locked_keys:
                        self.release_lock(agent_id, locked_key)
                    return False

            # Apply updates based on strategy
            for key, value in updates.items():
                if strategy == "overwrite":
                    await self.update_context(agent_id, key, value)
                elif strategy == "merge" and isinstance(self.context.get(key), dict):
                    # Deep merge for dictionaries
                    current = self.context.get(key, {})
                    merged = {**current, **value} if isinstance(value, dict) else value
                    await self.update_context(agent_id, key, merged)
                elif strategy == "append" and isinstance(self.context.get(key), list):
                    # Append for lists
                    current = self.context.get(key, [])
                    updated = current + value if isinstance(value, list) else current + [value]
                    await self.update_context(agent_id, key, updated)
                else:
                    await self.update_context(agent_id, key, value)

            return True

        finally:
            # Release all locks
            for key in locked_keys:
                self.release_lock(agent_id, key)

    def get_agent_contributions(self, agent_id: str) -> List[ContextUpdate]:
        """Get all context updates made by a specific agent"""
        return [
            update for update in self.context_history
            if update.agent_id == agent_id
        ]

    def get_recent_updates(self, limit: int = 20) -> List[ContextUpdate]:
        """Get most recent context updates"""
        return self.context_history[-limit:] if self.context_history else []

    def clear_context(self, key: Optional[str] = None):
        """Clear context (specific key or all)"""
        if key:
            if key in self.context:
                del self.context[key]
                logger.debug(f"Cleared context key: {key}")
        else:
            self._initialize_context()
            self.context_history.clear()
            self.version = 0
            logger.info("Cleared all context")

    async def _notify_subscribers(self, update: ContextUpdate):
        """Notify all subscribers of a context update"""
        tasks = []

        for agent_id, callbacks in self.subscribers.items():
            # Skip the agent that made the update
            if agent_id == update.agent_id:
                continue

            # Apply filter if exists
            if agent_id in self.filters:
                if not self.filters[agent_id](update):
                    continue

            # Create async tasks for all callbacks
            for callback in callbacks:
                tasks.append(asyncio.create_task(
                    self._safe_callback(callback, update, agent_id)
                ))

        # Wait for all notifications to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_callback(
        self,
        callback: Callable,
        update: ContextUpdate,
        agent_id: str
    ):
        """Safely execute a callback"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(update)
            else:
                callback(update)
        except Exception as e:
            logger.error(f"Error notifying agent {agent_id}: {e}")

    async def _check_lock(self, key: str, agent_id: str) -> bool:
        """Check if a key is locked by another agent"""
        if key in self.locks:
            lock = self.locks[key]

            # Check if lock expired
            if time.time() - lock.acquired_at > lock.timeout:
                del self.locks[key]
                return False

            # Check if same agent
            if lock.agent_id == agent_id:
                return False

            return True  # Locked by another agent

        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the shared context"""
        return {
            "version": self.version,
            "total_updates": self.total_updates,
            "total_conflicts": self.total_conflicts,
            "history_size": len(self.context_history),
            "active_locks": len(self.locks),
            "subscribers": len(self.subscribers),
            "context_keys": list(self.context.keys())
        }

    def export_context(self) -> str:
        """Export context to JSON"""
        export_data = {
            "version": self.version,
            "timestamp": time.time(),
            "context": self.context,
            "history": [
                {
                    "agent_id": u.agent_id,
                    "timestamp": u.timestamp,
                    "key": u.key,
                    "value": u.value
                }
                for u in self.context_history[-100:]  # Last 100 updates
            ]
        }

        return json.dumps(export_data, indent=2, default=str)

    def import_context(self, data: str):
        """Import context from JSON"""
        import_data = json.loads(data)

        self.context = import_data.get("context", {})
        self.version = import_data.get("version", 0)

        # Rebuild history
        self.context_history.clear()
        for hist in import_data.get("history", []):
            self.context_history.append(ContextUpdate(
                agent_id=hist["agent_id"],
                timestamp=hist["timestamp"],
                key=hist["key"],
                value=hist["value"]
            ))

        logger.info(f"Imported context with version {self.version}")

# Global singleton instance
def get_shared_context() -> SharedContextManager:
    """Get the singleton SharedContextManager instance"""
    return SharedContextManager()