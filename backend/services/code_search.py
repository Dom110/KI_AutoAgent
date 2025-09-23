"""
Lightweight SQLite-based code search
"""
import sqlite3
import os
import json
import logging
from typing import List, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class LightweightCodeSearch:
    """
    SQLite FTS5 instead of Elasticsearch
    - Only 5MB overhead
    - In-process (no server needed)
    - Fast enough for local projects
    """

    def __init__(self, project_path: str):
        db_dir = os.path.join(project_path, '.ki_autoagent')
        os.makedirs(db_dir, exist_ok=True)

        self.db_path = os.path.join(db_dir, 'search.db')
        self.project_path = project_path
        self._setup_tables()
        logger.info(f"✅ Code search database initialized at {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _setup_tables(self):
        """Create FTS5 virtual table for full-text search"""
        with self._get_connection() as conn:
            # Check if FTS5 is available
            cursor = conn.execute("PRAGMA compile_options")
            fts5_available = any("FTS5" in str(row[0]) for row in cursor)

            if not fts5_available:
                logger.warning("⚠️ SQLite FTS5 not available, using basic search")
                # Create basic table without FTS
                conn.executescript('''
                    CREATE TABLE IF NOT EXISTS functions (
                        id INTEGER PRIMARY KEY,
                        file_path TEXT,
                        function_name TEXT,
                        signature TEXT,
                        docstring TEXT,
                        code_body TEXT,
                        return_type TEXT,
                        parameters TEXT,
                        line_number INTEGER,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE INDEX IF NOT EXISTS idx_function_name
                    ON functions(function_name);

                    CREATE INDEX IF NOT EXISTS idx_file_path
                    ON functions(file_path);
                ''')
            else:
                # Create FTS5 tables
                conn.executescript('''
                    CREATE TABLE IF NOT EXISTS functions (
                        id INTEGER PRIMARY KEY,
                        file_path TEXT,
                        function_name TEXT,
                        signature TEXT,
                        docstring TEXT,
                        code_body TEXT,
                        return_type TEXT,
                        parameters TEXT,
                        line_number INTEGER,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE VIRTUAL TABLE IF NOT EXISTS functions_fts USING fts5(
                        file_path,
                        function_name,
                        signature,
                        docstring,
                        code_body,
                        content=functions,
                        tokenize='porter unicode61'
                    );

                    CREATE TRIGGER IF NOT EXISTS functions_ai AFTER INSERT ON functions BEGIN
                        INSERT INTO functions_fts(
                            rowid, file_path, function_name, signature, docstring, code_body
                        ) VALUES (
                            new.id, new.file_path, new.function_name,
                            new.signature, new.docstring, new.code_body
                        );
                    END;

                    CREATE TRIGGER IF NOT EXISTS functions_au AFTER UPDATE ON functions BEGIN
                        UPDATE functions_fts SET
                            file_path = new.file_path,
                            function_name = new.function_name,
                            signature = new.signature,
                            docstring = new.docstring,
                            code_body = new.code_body
                        WHERE rowid = new.id;
                    END;

                    CREATE TRIGGER IF NOT EXISTS functions_ad AFTER DELETE ON functions BEGIN
                        DELETE FROM functions_fts WHERE rowid = old.id;
                    END;
                ''')

            conn.commit()
            logger.debug("Database tables created successfully")

    async def index_function(self, func_data: Dict):
        """Index a function for searching"""
        with self._get_connection() as conn:
            # Check if function already exists
            existing = conn.execute('''
                SELECT id FROM functions
                WHERE file_path = ? AND function_name = ? AND line_number = ?
            ''', (
                func_data['file_path'],
                func_data['name'],
                func_data.get('line_number', 0)
            )).fetchone()

            if existing:
                # Update existing
                conn.execute('''
                    UPDATE functions SET
                        signature = ?, docstring = ?, code_body = ?,
                        return_type = ?, parameters = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    func_data['signature'],
                    func_data.get('docstring', ''),
                    func_data.get('body', ''),
                    func_data.get('return_type', ''),
                    json.dumps(func_data.get('parameters', [])),
                    existing['id']
                ))
            else:
                # Insert new
                conn.execute('''
                    INSERT INTO functions (
                        file_path, function_name, signature, docstring,
                        code_body, return_type, parameters, line_number
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    func_data['file_path'],
                    func_data['name'],
                    func_data['signature'],
                    func_data.get('docstring', ''),
                    func_data.get('body', ''),
                    func_data.get('return_type', ''),
                    json.dumps(func_data.get('parameters', [])),
                    func_data.get('line_number', 0)
                ))

            conn.commit()

    async def search(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Full-text search across all indexed functions
        """
        with self._get_connection() as conn:
            # Check if FTS5 table exists
            cursor = conn.execute('''
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='functions_fts'
            ''')

            if cursor.fetchone():
                # Use FTS5 search
                cursor = conn.execute('''
                    SELECT
                        f.file_path,
                        f.function_name,
                        f.signature,
                        f.docstring,
                        snippet(functions_fts, 4, '<b>', '</b>', '...', 32) as snippet,
                        f.line_number
                    FROM functions f
                    JOIN functions_fts ON f.id = functions_fts.rowid
                    WHERE functions_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                ''', (query, limit))
            else:
                # Fallback to LIKE search
                search_term = f'%{query}%'
                cursor = conn.execute('''
                    SELECT
                        file_path,
                        function_name,
                        signature,
                        docstring,
                        substr(code_body, 1, 200) as snippet,
                        line_number
                    FROM functions
                    WHERE function_name LIKE ? OR docstring LIKE ? OR code_body LIKE ?
                    LIMIT ?
                ''', (search_term, search_term, search_term, limit))

            return [dict(row) for row in cursor.fetchall()]

    async def search_by_signature(self, return_type: str = None, param_types: List[str] = None) -> List[Dict]:
        """Search functions by signature characteristics"""
        with self._get_connection() as conn:
            query = "SELECT * FROM functions WHERE 1=1"
            params = []

            if return_type:
                query += " AND return_type LIKE ?"
                params.append(f"%{return_type}%")

            if param_types:
                for param_type in param_types:
                    query += " AND parameters LIKE ?"
                    params.append(f"%{param_type}%")

            query += " LIMIT 50"

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    async def clear_file(self, file_path: str):
        """Remove all functions from a specific file"""
        with self._get_connection() as conn:
            conn.execute('DELETE FROM functions WHERE file_path = ?', (file_path,))
            conn.commit()

    async def get_stats(self) -> Dict:
        """Get search database statistics"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT
                    COUNT(*) as total_functions,
                    COUNT(DISTINCT file_path) as total_files
                FROM functions
            ''')
            stats = dict(cursor.fetchone())

            # Get database file size
            if os.path.exists(self.db_path):
                stats['db_size_mb'] = round(os.path.getsize(self.db_path) / (1024 * 1024), 2)
            else:
                stats['db_size_mb'] = 0

            return stats