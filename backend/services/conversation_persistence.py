"""
Persistent conversation history storage
"""
import sqlite3
import os
import json
import logging
from datetime import datetime
from typing import List, Dict
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class ConversationPersistence:
    """
    SQLite-based conversation storage
    """

    def __init__(self):
        # Global conversations database in user home
        db_dir = os.path.expanduser('~/.ki_autoagent')
        os.makedirs(db_dir, exist_ok=True)

        self.db_path = os.path.join(db_dir, 'conversations.db')
        self._init_db()
        logger.info(f"✅ Conversation database initialized at {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_path TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    agent TEXT,
                    metadata TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_project_timestamp
                ON conversations(project_path, timestamp DESC);

                -- Session tracking table
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_path TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(project_path, session_id)
                );

                CREATE INDEX IF NOT EXISTS idx_session_project
                ON sessions(project_path, last_activity DESC);
            ''')
            conn.commit()

    async def save_message(self, project_path: str, message: Dict):
        """Save a message to history"""
        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO conversations (project_path, role, content, agent, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                project_path,
                message['role'],
                message['content'],
                message.get('agent', 'orchestrator'),
                json.dumps(message.get('metadata', {}))
            ))
            conn.commit()
            logger.debug(f"Saved {message['role']} message for {project_path}")

    async def load_history(self, project_path: str, limit: int = 100) -> List[Dict]:
        """Load conversation history for a project"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM conversations
                WHERE project_path = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (project_path, limit))

            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'role': row['role'],
                    'content': row['content'],
                    'agent': row['agent'],
                    'metadata': json.loads(row['metadata'] or '{}'),
                    'timestamp': row['timestamp']
                })

            # Return in chronological order
            return list(reversed(messages))

    async def get_recent_context(self, project_path: str, limit: int = 10) -> str:
        """Get recent conversation context as formatted string"""
        history = await self.load_history(project_path, limit)

        if not history:
            return "No previous conversation history."

        context_lines = []
        for msg in history:
            role = msg['role'].capitalize()
            agent = f" ({msg['agent']})" if msg['agent'] and msg['agent'] != 'orchestrator' else ""
            content = msg['content'][:500]  # Truncate long messages
            context_lines.append(f"{role}{agent}: {content}")

        return "\n".join(context_lines)

    async def clear_project_history(self, project_path: str):
        """Clear all conversation history for a project"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                DELETE FROM conversations WHERE project_path = ?
            ''', (project_path,))
            deleted_count = cursor.rowcount
            conn.commit()
            logger.info(f"Cleared {deleted_count} messages for {project_path}")
            return deleted_count

    async def export_history(self, project_path: str) -> Dict:
        """Export conversation history as JSON"""
        history = await self.load_history(project_path, limit=10000)  # Large limit for export

        return {
            'project': project_path,
            'exported_at': datetime.now().isoformat(),
            'message_count': len(history),
            'messages': history
        }

    async def import_history(self, data: Dict):
        """Import conversation history from JSON"""
        project_path = data.get('project')
        messages = data.get('messages', [])

        if not project_path:
            raise ValueError("Project path required for import")

        for msg in messages:
            await self.save_message(project_path, msg)

        logger.info(f"Imported {len(messages)} messages for {project_path}")

    async def get_stats(self, project_path: str = None) -> Dict:
        """Get conversation statistics"""
        with self._get_connection() as conn:
            if project_path:
                cursor = conn.execute('''
                    SELECT
                        COUNT(*) as total_messages,
                        COUNT(DISTINCT DATE(timestamp)) as total_days,
                        MIN(timestamp) as first_message,
                        MAX(timestamp) as last_message
                    FROM conversations
                    WHERE project_path = ?
                ''', (project_path,))
            else:
                cursor = conn.execute('''
                    SELECT
                        COUNT(*) as total_messages,
                        COUNT(DISTINCT project_path) as total_projects,
                        COUNT(DISTINCT DATE(timestamp)) as total_days,
                        MIN(timestamp) as first_message,
                        MAX(timestamp) as last_message
                    FROM conversations
                ''')

            stats = dict(cursor.fetchone())

            # Get database file size
            if os.path.exists(self.db_path):
                stats['db_size_mb'] = round(os.path.getsize(self.db_path) / (1024 * 1024), 2)
            else:
                stats['db_size_mb'] = 0

            return stats

    async def cleanup_old_messages(self, days_to_keep: int = 30):
        """Remove messages older than specified days"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                DELETE FROM conversations
                WHERE timestamp < datetime('now', '-' || ? || ' days')
            ''', (days_to_keep,))
            deleted_count = cursor.rowcount
            conn.commit()
            logger.info(f"Cleaned up {deleted_count} old messages")
            return deleted_count