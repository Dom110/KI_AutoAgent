"""
Session Persistence Store

Provides persistent storage for WebSocket sessions across connections.
Sessions are stored in-memory with optional file-based persistence.

Author: KI AutoAgent v7.0
Date: 2025-11-07
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SessionStore:
    """
    Persistent storage for WebSocket sessions.

    Features:
    - In-memory storage for fast access
    - Optional file-based persistence
    - Session expiration (default: 24 hours)
    - Thread-safe operations
    """

    def __init__(self, storage_path: Path | None = None, expiration_hours: int = 24):
        """
        Initialize session store.

        Args:
            storage_path: Optional path to JSON file for persistence
            expiration_hours: Hours before session expires (default: 24)
        """
        self.storage_path = storage_path
        self.expiration_hours = expiration_hours
        self._sessions: dict[str, dict[str, Any]] = {}

        # Load from file if exists
        if self.storage_path and self.storage_path.exists():
            self._load_from_file()

    def create_session(self, session_id: str, workspace_path: str, client_id: str) -> dict[str, Any]:
        """
        Create new session.

        Args:
            session_id: Unique session ID
            workspace_path: Workspace path for this session
            client_id: WebSocket client ID

        Returns:
            Session data dict
        """
        session = {
            "session_id": session_id,
            "workspace_path": workspace_path,
            "client_id": client_id,
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "messages": [],
            "conversation_state": {},
            "workflow_history": []
        }

        self._sessions[session_id] = session
        self._save_to_file()

        logger.info(f"📝 Created session: {session_id} for workspace: {workspace_path}")
        return session

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """
        Get session by ID.

        Args:
            session_id: Session ID to retrieve

        Returns:
            Session data dict or None if not found/expired
        """
        session = self._sessions.get(session_id)

        if not session:
            return None

        # Check expiration
        if self._is_expired(session):
            logger.info(f"⏰ Session expired: {session_id}")
            del self._sessions[session_id]
            self._save_to_file()
            return None

        # Update last accessed
        session["last_accessed"] = datetime.now().isoformat()
        return session

    def update_session(self, session_id: str, updates: dict[str, Any]) -> bool:
        """
        Update session data.

        Args:
            session_id: Session ID to update
            updates: Dict of fields to update

        Returns:
            True if updated, False if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return False

        session.update(updates)
        session["last_accessed"] = datetime.now().isoformat()
        self._save_to_file()

        return True

    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """
        Add message to session conversation history.

        Args:
            session_id: Session ID
            role: Message role (user/assistant/system)
            content: Message content

        Returns:
            True if added, False if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return False

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }

        session["messages"].append(message)
        session["last_accessed"] = datetime.now().isoformat()
        self._save_to_file()

        return True

    def add_workflow_event(self, session_id: str, agent: str, action: str, result: Any) -> bool:
        """
        Add workflow event to session history.

        Args:
            session_id: Session ID
            agent: Agent name that performed action
            action: Action performed
            result: Result of action

        Returns:
            True if added, False if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return False

        event = {
            "agent": agent,
            "action": action,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

        session["workflow_history"].append(event)
        session["last_accessed"] = datetime.now().isoformat()
        self._save_to_file()

        return True

    def delete_session(self, session_id: str) -> bool:
        """
        Delete session.

        Args:
            session_id: Session ID to delete

        Returns:
            True if deleted, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._save_to_file()
            logger.info(f"🗑️  Deleted session: {session_id}")
            return True
        return False

    def cleanup_expired(self) -> int:
        """
        Remove all expired sessions.

        Returns:
            Number of sessions removed
        """
        expired = [
            session_id
            for session_id, session in self._sessions.items()
            if self._is_expired(session)
        ]

        for session_id in expired:
            del self._sessions[session_id]

        if expired:
            self._save_to_file()
            logger.info(f"🧹 Cleaned up {len(expired)} expired sessions")

        return len(expired)

    def get_all_sessions(self) -> list[dict[str, Any]]:
        """
        Get all active sessions.

        Returns:
            List of session data dicts
        """
        self.cleanup_expired()
        return list(self._sessions.values())

    def _is_expired(self, session: dict[str, Any]) -> bool:
        """Check if session is expired."""
        try:
            last_accessed = datetime.fromisoformat(session["last_accessed"])
            age_hours = (datetime.now() - last_accessed).total_seconds() / 3600
            return age_hours > self.expiration_hours
        except (KeyError, ValueError):
            return True

    def _save_to_file(self) -> None:
        """Save sessions to file."""
        if not self.storage_path:
            return

        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump(self._sessions, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Failed to save sessions: {e}")

    def _load_from_file(self) -> None:
        """Load sessions from file."""
        try:
            with open(self.storage_path, 'r') as f:
                self._sessions = json.load(f)

            # Cleanup expired on load
            expired_count = self.cleanup_expired()

            logger.info(f"✅ Loaded {len(self._sessions)} sessions from {self.storage_path}")
            if expired_count > 0:
                logger.info(f"   Removed {expired_count} expired sessions")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load sessions: {e}")
            self._sessions = {}


# Global session store instance
_session_store: SessionStore | None = None


def get_session_store(storage_path: Path | None = None) -> SessionStore:
    """
    Get global session store instance.

    Args:
        storage_path: Optional path for file-based persistence

    Returns:
        Global SessionStore instance
    """
    global _session_store

    if _session_store is None:
        # Default storage path
        if storage_path is None:
            storage_path = Path.home() / ".ki_autoagent" / "sessions" / "sessions.json"

        _session_store = SessionStore(storage_path=storage_path)

    return _session_store
