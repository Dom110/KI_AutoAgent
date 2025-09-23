"""
File system watcher for cache invalidation
"""
import os
import hashlib
import asyncio
from pathlib import Path
from typing import Set, Dict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

logger = logging.getLogger(__name__)


class ProjectFileWatcher(FileSystemEventHandler):
    """
    Watches project files and invalidates cache on changes
    """

    def __init__(self, project_path: str, project_cache):
        self.project_path = project_path
        self.project_cache = project_cache
        self.observer = None
        self.file_hashes: Dict[str, str] = {}

        # Patterns to ignore
        self.ignore_patterns = {
            '__pycache__', '.git', 'node_modules', '.venv', 'venv',
            '.ki_autoagent', '.pytest_cache', '*.pyc', '*.pyo',
            'redis-data', '.DS_Store', 'dist', 'build', '*.egg-info'
        }

        # Supported file extensions
        self.watch_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx',
            '.java', '.cpp', '.c', '.h', '.hpp',
            '.go', '.rs', '.swift', '.kt', '.rb',
            '.php', '.cs', '.scala', '.r', '.m'
        }

    def start(self):
        """Start watching the project directory"""
        try:
            self.observer = Observer()
            self.observer.schedule(self, self.project_path, recursive=True)
            self.observer.start()
            logger.info(f"🔍 Started file watcher for {self.project_path}")
        except Exception as e:
            logger.error(f"Failed to start file watcher: {e}")

    def stop(self):
        """Stop watching"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("File watcher stopped")

    def _should_watch(self, path: str) -> bool:
        """Check if file should be watched"""
        path_obj = Path(path)

        # Check ignore patterns
        for pattern in self.ignore_patterns:
            if pattern.startswith('*'):
                # Handle glob patterns
                if path_obj.name.endswith(pattern[1:]):
                    return False
            elif pattern in str(path_obj):
                return False

        # Only watch code files
        return path_obj.suffix in self.watch_extensions

    def on_modified(self, event):
        """File modified - invalidate relevant caches"""
        if event.is_directory:
            return

        if not self._should_watch(event.src_path):
            return

        rel_path = os.path.relpath(event.src_path, self.project_path)
        logger.info(f"📝 File modified: {rel_path}")

        # Schedule async invalidation
        asyncio.create_task(self._invalidate_affected_caches(rel_path))

    def on_created(self, event):
        """New file created"""
        if event.is_directory:
            return

        if not self._should_watch(event.src_path):
            return

        rel_path = os.path.relpath(event.src_path, self.project_path)
        logger.info(f"➕ File created: {rel_path}")

        # New files affect dependency graph and full analysis
        asyncio.create_task(self.project_cache.invalidate('dependency_graph'))
        asyncio.create_task(self.project_cache.invalidate('full_system_analysis'))

    def on_deleted(self, event):
        """File deleted"""
        if event.is_directory:
            return

        if not self._should_watch(event.src_path):
            return

        rel_path = os.path.relpath(event.src_path, self.project_path)
        logger.info(f"➖ File deleted: {rel_path}")

        # Deleted files affect everything
        asyncio.create_task(self.project_cache.invalidate('dependency_graph'))
        asyncio.create_task(self.project_cache.invalidate('full_system_analysis'))
        asyncio.create_task(self.project_cache.invalidate('ast_index', [rel_path]))

    async def _invalidate_affected_caches(self, file_path: str):
        """
        Intelligently invalidate only affected caches
        """
        try:
            # AST index - only for this file
            await self.project_cache.invalidate('ast_index', [file_path])

            # Metrics - only for this file
            await self.project_cache.invalidate('metrics', [file_path])

            # Dependency graph - might be affected
            await self.project_cache.invalidate('dependency_graph')

            # Full system analysis - needs refresh
            await self.project_cache.invalidate('full_system_analysis')

            # Patterns and security analysis remain valid unless explicitly refreshed

            logger.info(f"♻️ Invalidated caches affected by {file_path}")
        except Exception as e:
            logger.error(f"Failed to invalidate caches: {e}")

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

    def has_file_changed(self, file_path: str) -> bool:
        """Check if file has actually changed"""
        current_hash = self._calculate_file_hash(file_path)
        previous_hash = self.file_hashes.get(file_path)

        if current_hash != previous_hash:
            self.file_hashes[file_path] = current_hash
            return True

        return False