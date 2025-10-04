"""
Smart File Watcher Service
Monitors file changes and invalidates caches when files are modified
"""

import time
from pathlib import Path
from typing import Dict, Set, Optional, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SmartFileWatcher:
    """
    Watches files for changes and triggers cache invalidation
    Uses file modification times (mtime) for change detection
    """

    def __init__(self, project_root: str, cache=None, debounce_seconds: int = 5):
        """
        Initialize file watcher

        Args:
            project_root: Root directory to watch
            cache: Optional cache instance to invalidate on changes
            debounce_seconds: Debounce interval for change detection
        """
        self.project_root = Path(project_root)
        self.cache = cache
        self.debounce_seconds = debounce_seconds
        self._watched_files: Dict[Path, float] = {}  # path -> mtime
        self._callbacks: Dict[Path, Set[Callable]] = {}  # path -> callbacks
        self._running = False
        logger.info(f"👁️  SmartFileWatcher initialized for: {self.project_root}")

    def watch_file(self, file_path: str, callback: Optional[Callable] = None) -> None:
        """
        Start watching a file for changes

        Args:
            file_path: Path to file (relative to project root or absolute)
            callback: Optional callback function to call when file changes
        """
        full_path = self._resolve_path(file_path)

        if not full_path.exists():
            logger.warning(f"File does not exist: {full_path}")
            return

        # Store current modification time
        mtime = full_path.stat().st_mtime
        self._watched_files[full_path] = mtime

        # Register callback if provided
        if callback:
            if full_path not in self._callbacks:
                self._callbacks[full_path] = set()
            self._callbacks[full_path].add(callback)

        logger.debug(f"👁️  Watching file: {full_path}")

    def watch_directory(self, dir_path: str, pattern: str = "**/*.py",
                       callback: Optional[Callable] = None) -> None:
        """
        Watch all files matching pattern in directory

        Args:
            dir_path: Directory path
            pattern: Glob pattern for files to watch
            callback: Optional callback for changes
        """
        full_dir = self._resolve_path(dir_path)

        if not full_dir.is_dir():
            logger.warning(f"Directory does not exist: {full_dir}")
            return

        for file_path in full_dir.glob(pattern):
            if file_path.is_file():
                self.watch_file(str(file_path), callback)

        logger.info(f"👁️  Watching directory: {full_dir} ({pattern})")

    def check_changes(self) -> Dict[str, datetime]:
        """
        Check all watched files for changes

        Returns:
            Dict of changed files with their modification times
        """
        changes = {}

        for file_path, old_mtime in list(self._watched_files.items()):
            if not file_path.exists():
                logger.warning(f"Watched file deleted: {file_path}")
                del self._watched_files[file_path]
                continue

            current_mtime = file_path.stat().st_mtime

            if current_mtime > old_mtime:
                # File has changed
                changes[str(file_path)] = datetime.fromtimestamp(current_mtime)
                self._watched_files[file_path] = current_mtime

                # Trigger callbacks
                if file_path in self._callbacks:
                    for callback in self._callbacks[file_path]:
                        try:
                            callback(str(file_path))
                        except Exception as e:
                            logger.error(f"Callback error for {file_path}: {e}")

                logger.info(f"📝 File changed: {file_path}")

        return changes

    def stop_watching(self, file_path: str) -> None:
        """
        Stop watching a file

        Args:
            file_path: Path to stop watching
        """
        full_path = self._resolve_path(file_path)

        if full_path in self._watched_files:
            del self._watched_files[full_path]

        if full_path in self._callbacks:
            del self._callbacks[full_path]

        logger.debug(f"👁️  Stopped watching: {full_path}")

    def stop_all(self) -> None:
        """Stop watching all files"""
        self._watched_files.clear()
        self._callbacks.clear()
        self._running = False
        logger.info("👁️  Stopped watching all files")

    def get_watched_files(self) -> Set[str]:
        """Get set of all watched file paths"""
        return {str(p) for p in self._watched_files.keys()}

    def _resolve_path(self, file_path: str) -> Path:
        """Resolve path relative to project root"""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.project_root / path
        return path.resolve()

    def start(self) -> None:
        """
        Start file watching (non-blocking)
        Sets running flag but doesn't start continuous monitoring
        Call check_changes() manually or use start_monitoring() for continuous mode
        """
        self._running = True
        logger.info(f"👁️  File watcher started (call check_changes() to check for updates)")

    def stop(self) -> None:
        """Stop file watching"""
        self._running = False
        logger.info("👁️  File watcher stopped")

    def start_monitoring(self, interval_seconds: int = 5) -> None:
        """
        Start continuous monitoring (blocking)

        Args:
            interval_seconds: Check interval in seconds
        """
        self._running = True
        logger.info(f"👁️  Started continuous monitoring (interval: {interval_seconds}s)")

        try:
            while self._running:
                self.check_changes()
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("👁️  Monitoring stopped by user")
        finally:
            self._running = False
