"""
Project Cache Service
Provides caching for project analysis results to improve performance
"""

import json
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ProjectCache:
    """
    Cache for project analysis results
    Stores results in workspace cache directory

    v5.8.0: Supports both:
    - Legacy: project_root → creates .ki_autoagent_ws/cache inside
    - New: explicit cache_dir path (for $WORKSPACE/.ki_autoagent_ws/cache/)
    """

    def __init__(self, project_root: str, cache_duration_hours: int = 24):
        """
        Initialize project cache

        Args:
            project_root: Can be either:
                          - Workspace root (legacy) → creates .ki_autoagent_ws/cache inside
                          - Cache directory path (v5.8.0) → uses directly
            cache_duration_hours: How long to keep cached data (default 24h)
        """
        project_path = Path(project_root)

        # v5.8.0: If project_root ends with 'cache', use it directly
        # Otherwise, use legacy behavior (create .ki_autoagent_ws/cache inside)
        if project_path.name == "cache":
            self.cache_dir = project_path
            self.project_root = project_path.parent.parent  # Go up from cache/.ki_autoagent_ws/
        else:
            # Legacy behavior
            self.project_root = project_path
            self.cache_dir = self.project_root / ".ki_autoagent_ws" / "cache"

        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.connected = True  # Always connected for file-based cache

        # Create cache directory if it doesn't exist
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"📦 ProjectCache initialized: {self.cache_dir}")
        except Exception as e:
            logger.error(f"Failed to create cache directory: {e}")
            self.connected = False

    def _get_cache_key(self, key: str) -> str:
        """Generate cache filename from key"""
        # Use hash to create safe filename
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return f"{hash_key}.json"

    def _get_cache_path(self, key: str) -> Path:
        """Get full path to cache file"""
        return self.cache_dir / self._get_cache_key(key)

    def get(self, key: str) -> Optional[Any]:
        """
        Get cached value

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)

            # Check if cache is expired
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cached_time > self.cache_duration:
                logger.debug(f"Cache expired for key: {key}")
                cache_path.unlink()  # Delete expired cache
                return None

            logger.debug(f"✅ Cache hit for key: {key}")
            return cache_data['value']

        except Exception as e:
            logger.warning(f"Failed to read cache for key {key}: {e}")
            return None

    def set(self, key: str, value: Any) -> None:
        """
        Set cached value

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
        """
        cache_path = self._get_cache_path(key)

        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'key': key,
                'value': value
            }

            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)

            logger.debug(f"💾 Cached value for key: {key}")

        except Exception as e:
            logger.warning(f"Failed to write cache for key {key}: {e}")

    def invalidate(self, key: str) -> None:
        """
        Invalidate (delete) cached value

        Args:
            key: Cache key to invalidate
        """
        cache_path = self._get_cache_path(key)

        if cache_path.exists():
            cache_path.unlink()
            logger.debug(f"🗑️  Invalidated cache for key: {key}")

    def clear_all(self) -> None:
        """Clear all cached data"""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
        logger.info("🗑️  All cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            'total_entries': len(cache_files),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'cache_dir': str(self.cache_dir)
        }
