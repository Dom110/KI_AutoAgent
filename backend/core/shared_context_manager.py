"""
Shared Context Manager for v6 Multi-Agent System

Manages shared context between agents with versioning and conflict resolution.

Features:
- Share context between agents
- Context versioning
- Context merging
- Conflict resolution
- Context snapshots
- Context pruning

Author: KI AutoAgent Team
Date: 2025-10-12
Version: v6.1
"""

import asyncio
import json
import logging
from copy import deepcopy
from datetime import datetime
from typing import Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class ConflictResolutionStrategy:
    """Strategies for resolving context conflicts."""
    LATEST_WINS = "latest_wins"  # Most recent update wins
    MERGE = "merge"  # Try to merge both values
    AGENT_PRIORITY = "agent_priority"  # Higher priority agent wins
    MANUAL = "manual"  # Require manual resolution


class SharedContextManager:
    """
    Manages shared context between multiple agents.

    Features:
    - Thread-safe context operations
    - Context versioning (track changes over time)
    - Conflict resolution when multiple agents update same key
    - Context snapshots for rollback
    - Selective context sharing (agents can see only relevant keys)

    Usage:
        manager = SharedContextManager()

        # Agent writes context
        await manager.set_context(
            "user_requirements",
            requirements_data,
            agent_id="research"
        )

        # Another agent reads context
        requirements = await manager.get_context(
            "user_requirements",
            agent_id="architect"
        )

        # Create snapshot before major operation
        snapshot_id = await manager.create_snapshot()

        # Restore if needed
        await manager.restore_snapshot(snapshot_id)
    """

    def __init__(
        self,
        conflict_strategy: str = ConflictResolutionStrategy.LATEST_WINS,
        max_versions: int = 10,
        agent_priorities: dict[str, int] | None = None
    ):
        """
        Initialize Shared Context Manager.

        Args:
            conflict_strategy: How to resolve conflicts (default: latest_wins)
            max_versions: Max versions to keep per key (default: 10)
            agent_priorities: Agent priorities for conflict resolution (default: equal)
        """
        # Current context (key -> value)
        self._context: dict[str, Any] = {}

        # Context metadata (key -> metadata)
        self._metadata: dict[str, dict[str, Any]] = {}

        # Version history (key -> list of versions)
        self._versions: dict[str, list[dict[str, Any]]] = defaultdict(list)

        # Snapshots (snapshot_id -> context state)
        self._snapshots: dict[str, dict[str, Any]] = {}

        # Configuration
        self.conflict_strategy = conflict_strategy
        self.max_versions = max_versions
        self.agent_priorities = agent_priorities or {}

        # Lock for thread safety
        self._lock = asyncio.Lock()

        logger.info("✅ SharedContextManager initialized")
        logger.info(f"   Conflict strategy: {conflict_strategy}")
        logger.info(f"   Max versions: {max_versions}")

    async def set_context(
        self,
        key: str,
        value: Any,
        agent_id: str = "unknown",
        metadata: dict[str, Any] | None = None
    ) -> bool:
        """
        Set context value.

        Args:
            key: Context key
            value: Context value
            agent_id: Agent setting the value
            metadata: Additional metadata

        Returns:
            True if set successfully, False if conflict
        """
        async with self._lock:
            # Check for conflict
            if key in self._context:
                # Resolve conflict
                should_update = await self._resolve_conflict(
                    key,
                    value,
                    agent_id
                )

                if not should_update:
                    logger.warning(f"⚠️  Context conflict: {key} (agent: {agent_id})")
                    return False

            # Save old version
            if key in self._context:
                old_value = self._context[key]
                old_metadata = self._metadata.get(key, {})

                self._versions[key].append({
                    "value": deepcopy(old_value),
                    "metadata": deepcopy(old_metadata),
                    "archived_at": datetime.now().isoformat()
                })

                # Prune old versions
                if len(self._versions[key]) > self.max_versions:
                    self._versions[key] = self._versions[key][-self.max_versions:]

            # Set new value
            self._context[key] = value

            self._metadata[key] = {
                "agent_id": agent_id,
                "updated_at": datetime.now().isoformat(),
                "version": len(self._versions[key]) + 1,
                "metadata": metadata or {}
            }

            logger.debug(f"✅ Context set: {key} (agent: {agent_id})")
            return True

    async def get_context(
        self,
        key: str,
        agent_id: str = "unknown",
        default: Any = None
    ) -> Any:
        """
        Get context value.

        Args:
            key: Context key
            agent_id: Agent requesting the value
            default: Default value if key not found

        Returns:
            Context value or default
        """
        async with self._lock:
            value = self._context.get(key, default)

            if value is not None:
                logger.debug(f"📖 Context read: {key} (agent: {agent_id})")

            return value

    async def update_context(
        self,
        context: dict[str, Any],
        agent_id: str = "unknown"
    ) -> dict[str, bool]:
        """
        Update multiple context values.

        Args:
            context: Dictionary of key-value pairs
            agent_id: Agent updating the values

        Returns:
            Dictionary of key -> success status
        """
        results = {}

        for key, value in context.items():
            success = await self.set_context(key, value, agent_id)
            results[key] = success

        return results

    async def delete_context(
        self,
        key: str,
        agent_id: str = "unknown"
    ) -> bool:
        """
        Delete context key.

        Args:
            key: Context key to delete
            agent_id: Agent deleting the key

        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            if key in self._context:
                # Archive before deleting
                if key in self._context:
                    old_value = self._context[key]
                    old_metadata = self._metadata.get(key, {})

                    self._versions[key].append({
                        "value": deepcopy(old_value),
                        "metadata": deepcopy(old_metadata),
                        "archived_at": datetime.now().isoformat(),
                        "deleted": True
                    })

                del self._context[key]
                self._metadata.pop(key, None)

                logger.info(f"🗑️  Context deleted: {key} (agent: {agent_id})")
                return True

            return False

    async def get_all_context(
        self,
        agent_id: str = "unknown",
        filter_keys: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Get all context (or filtered subset).

        Args:
            agent_id: Agent requesting context
            filter_keys: Only return these keys (optional)

        Returns:
            Dictionary of context key-value pairs
        """
        async with self._lock:
            if filter_keys:
                return {k: v for k, v in self._context.items() if k in filter_keys}

            return deepcopy(self._context)

    async def get_metadata(
        self,
        key: str
    ) -> dict[str, Any] | None:
        """
        Get metadata for context key.

        Args:
            key: Context key

        Returns:
            Metadata dictionary or None
        """
        async with self._lock:
            return deepcopy(self._metadata.get(key))

    async def get_version_history(
        self,
        key: str,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get version history for key.

        Args:
            key: Context key
            limit: Max versions to return

        Returns:
            List of version entries (newest first)
        """
        async with self._lock:
            versions = self._versions.get(key, [])
            return deepcopy(versions[-limit:][::-1])  # Newest first

    async def rollback_version(
        self,
        key: str,
        version: int,
        agent_id: str = "unknown"
    ) -> bool:
        """
        Rollback context key to specific version.

        Args:
            key: Context key
            version: Version number (1-based)
            agent_id: Agent performing rollback

        Returns:
            True if rolled back, False if version not found
        """
        async with self._lock:
            versions = self._versions.get(key, [])

            if version < 1 or version > len(versions):
                logger.error(f"❌ Invalid version: {version} for key: {key}")
                return False

            # Get version data
            version_data = versions[version - 1]

            # Restore value
            self._context[key] = deepcopy(version_data["value"])
            self._metadata[key] = {
                "agent_id": agent_id,
                "updated_at": datetime.now().isoformat(),
                "version": len(versions) + 1,
                "rolled_back_from": version,
                "metadata": version_data.get("metadata", {})
            }

            logger.info(f"⏪ Context rolled back: {key} to version {version} (agent: {agent_id})")
            return True

    async def create_snapshot(
        self,
        snapshot_id: str | None = None
    ) -> str:
        """
        Create snapshot of current context.

        Args:
            snapshot_id: Custom snapshot ID (default: auto-generate)

        Returns:
            Snapshot ID
        """
        async with self._lock:
            if snapshot_id is None:
                snapshot_id = f"snapshot_{datetime.now().timestamp()}"

            self._snapshots[snapshot_id] = {
                "context": deepcopy(self._context),
                "metadata": deepcopy(self._metadata),
                "created_at": datetime.now().isoformat()
            }

            logger.info(f"📸 Context snapshot created: {snapshot_id}")
            return snapshot_id

    async def restore_snapshot(
        self,
        snapshot_id: str,
        agent_id: str = "unknown"
    ) -> bool:
        """
        Restore context from snapshot.

        Args:
            snapshot_id: Snapshot ID to restore
            agent_id: Agent performing restore

        Returns:
            True if restored, False if snapshot not found
        """
        async with self._lock:
            if snapshot_id not in self._snapshots:
                logger.error(f"❌ Snapshot not found: {snapshot_id}")
                return False

            snapshot = self._snapshots[snapshot_id]

            self._context = deepcopy(snapshot["context"])
            self._metadata = deepcopy(snapshot["metadata"])

            logger.info(f"📸 Context restored from snapshot: {snapshot_id} (agent: {agent_id})")
            return True

    async def list_snapshots(self) -> list[dict[str, Any]]:
        """
        List all snapshots.

        Returns:
            List of snapshot info
        """
        async with self._lock:
            return [
                {
                    "snapshot_id": sid,
                    "created_at": data["created_at"],
                    "keys_count": len(data["context"])
                }
                for sid, data in self._snapshots.items()
            ]

    async def delete_snapshot(
        self,
        snapshot_id: str
    ) -> bool:
        """
        Delete snapshot.

        Args:
            snapshot_id: Snapshot ID to delete

        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            if snapshot_id in self._snapshots:
                del self._snapshots[snapshot_id]
                logger.info(f"🗑️  Snapshot deleted: {snapshot_id}")
                return True

            return False

    async def clear_context(
        self,
        agent_id: str = "unknown"
    ):
        """
        Clear all context.

        Args:
            agent_id: Agent clearing context
        """
        async with self._lock:
            self._context.clear()
            self._metadata.clear()
            logger.warning(f"🧹 All context cleared (agent: {agent_id})")

    async def _resolve_conflict(
        self,
        key: str,
        new_value: Any,
        agent_id: str
    ) -> bool:
        """
        Resolve context conflict.

        Args:
            key: Context key in conflict
            new_value: New value being set
            agent_id: Agent setting new value

        Returns:
            True to allow update, False to deny
        """
        if self.conflict_strategy == ConflictResolutionStrategy.LATEST_WINS:
            # Always allow update
            return True

        elif self.conflict_strategy == ConflictResolutionStrategy.AGENT_PRIORITY:
            # Check agent priorities
            current_agent = self._metadata[key].get("agent_id", "unknown")
            current_priority = self.agent_priorities.get(current_agent, 0)
            new_priority = self.agent_priorities.get(agent_id, 0)

            return new_priority >= current_priority

        elif self.conflict_strategy == ConflictResolutionStrategy.MERGE:
            # Try to merge values
            current_value = self._context[key]

            # If both are dicts, merge them
            if isinstance(current_value, dict) and isinstance(new_value, dict):
                merged = {**current_value, **new_value}
                self._context[key] = merged
                return False  # We already merged, don't overwrite

            # If both are lists, concatenate
            elif isinstance(current_value, list) and isinstance(new_value, list):
                merged = current_value + new_value
                self._context[key] = merged
                return False  # We already merged, don't overwrite

            # Otherwise, latest wins
            return True

        elif self.conflict_strategy == ConflictResolutionStrategy.MANUAL:
            # Require manual resolution
            logger.error(f"❌ Manual conflict resolution required for: {key}")
            return False

        # Default: latest wins
        return True


# Global singleton
_shared_context_instance: SharedContextManager | None = None


def get_shared_context(
    conflict_strategy: str | None = None,
    agent_priorities: dict[str, int] | None = None
) -> SharedContextManager:
    """
    Get global SharedContextManager instance (singleton).

    Args:
        conflict_strategy: Conflict resolution strategy (first call only)
        agent_priorities: Agent priorities (first call only)

    Returns:
        Global SharedContextManager instance
    """
    global _shared_context_instance

    if _shared_context_instance is None:
        _shared_context_instance = SharedContextManager(
            conflict_strategy=conflict_strategy or ConflictResolutionStrategy.LATEST_WINS,
            agent_priorities=agent_priorities
        )

    return _shared_context_instance
