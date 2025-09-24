"""
Project-based permanent cache without TTLs.
Fails fast if Redis is not available - no fallbacks.
"""
import redis
import msgpack
import hashlib
import json
import logging
import sys
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ProjectCache:
    """
    Permanent cache - NEVER expires automatically
    Invalidation only through:
    1. File changes (auto-detected)
    2. User request
    3. Agent-detected inconsistencies
    """

    def __init__(self, project_path: str):
        # Import exception at runtime to avoid circular imports
        from core.exceptions import CacheNotAvailableError

        try:
            self.redis = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=False,  # We use msgpack for binary data
                socket_connect_timeout=5
            )
            # Test connection
            self.redis.ping()
            self.connected = True
            logger.info("✅ Redis cache connected")
        except redis.ConnectionError as e:
            # NO FALLBACK - fail immediately
            raise CacheNotAvailableError(
                component="ProjectCache",
                file=__file__,
                line=35
            )
        except Exception as e:
            # Any other Redis error also fails fast
            raise CacheNotAvailableError(
                component=f"ProjectCache ({type(e).__name__})",
                file=__file__,
                line=35
            )

        self.project_path = project_path
        self.project_hash = hashlib.md5(project_path.encode()).hexdigest()[:8]

    def _get_key(self, cache_type: str, sub_key: Optional[str] = None) -> str:
        """Generate Redis key for cache entry"""
        base = f"ki_autoagent:{self.project_hash}:{cache_type}"
        if sub_key:
            return f"{base}:{sub_key}"
        return base

    async def get(self, cache_type: str, sub_key: Optional[str] = None) -> Optional[Dict]:
        """Get from cache - NO expiry check needed!"""
        # No check needed - if we got here, Redis is connected

        try:
            key = self._get_key(cache_type, sub_key)
            data = self.redis.get(key)

            if data:
                logger.debug(f"Cache hit for {cache_type}/{sub_key}")
                return msgpack.unpackb(data, raw=False)

            logger.debug(f"Cache miss for {cache_type}/{sub_key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def set(self, cache_type: str, data: Dict, sub_key: Optional[str] = None):
        """
        Store in cache - NO TTL/expire parameter!
        Data stays forever until explicitly invalidated
        """
        # No check needed - if we got here, Redis is connected

        try:
            key = self._get_key(cache_type, sub_key)
            packed = msgpack.packb(data)

            # Store data WITHOUT expiry
            self.redis.set(key, packed)

            # Store metadata for validation
            meta_key = f"{key}:meta"
            self.redis.hset(meta_key, mapping={
                'created_at': datetime.now().isoformat(),
                'size': len(packed),
                'version': '4.0.14'
            })

            logger.debug(f"Cached {cache_type}/{sub_key} permanently")
        except Exception as e:
            logger.error(f"Cache set error: {e}")

    async def invalidate(self, cache_type: str, sub_keys: Optional[list] = None):
        """
        Invalidate specific cache entries
        If sub_keys is None, invalidate all entries of this type
        """
        # No check needed - if we got here, Redis is connected

        try:
            if sub_keys:
                for sub_key in sub_keys:
                    key = self._get_key(cache_type, sub_key)
                    self.redis.delete(key, f"{key}:meta")
                    logger.debug(f"Invalidated {cache_type}/{sub_key}")
            else:
                # Invalidate all entries of this type
                pattern = self._get_key(cache_type, "*")
                for key in self.redis.scan_iter(match=pattern):
                    self.redis.delete(key)
                logger.debug(f"Invalidated all {cache_type} entries")
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")

    async def invalidate_partial(self, cache_type: str, file_path: str):
        """
        Invalidate only part of a cache (for a specific file)
        Instead of invalidating entire cache, update it to remove specific file data
        """
        # No check needed - if we got here, Redis is connected

        try:
            # Get existing cache
            cached_data = await self.get(cache_type)
            if not cached_data:
                return

            # Remove data for specific file from different cache structures
            modified = False

            # Handle different cache structures
            if 'files' in cached_data and isinstance(cached_data['files'], dict):
                if file_path in cached_data['files']:
                    del cached_data['files'][file_path]
                    modified = True

            # Handle AST structure
            if 'ast' in cached_data and 'files' in cached_data['ast']:
                if file_path in cached_data['ast']['files']:
                    del cached_data['ast']['files'][file_path]
                    modified = True

            # Handle metrics structure
            if 'file_metrics' in cached_data and file_path in cached_data['file_metrics']:
                del cached_data['file_metrics'][file_path]
                modified = True

            # Handle security findings
            if 'findings' in cached_data and isinstance(cached_data['findings'], list):
                cached_data['findings'] = [
                    f for f in cached_data['findings']
                    if f.get('file') != file_path
                ]
                modified = True

            # Update cache with modified data
            if modified:
                await self.set(cache_type, cached_data)
                logger.info(f"♻️ Partially invalidated {cache_type} for {file_path}")
            else:
                logger.debug(f"No data to invalidate in {cache_type} for {file_path}")

        except Exception as e:
            logger.error(f"Failed to partially invalidate cache: {e}")

    async def clear_all(self):
        """Clear ALL cache for this project"""
        # No check needed - if we got here, Redis is connected

        try:
            pattern = f"ki_autoagent:{self.project_hash}:*"
            count = 0
            for key in self.redis.scan_iter(match=pattern):
                self.redis.delete(key)
                count += 1
            logger.info(f"Cleared {count} cache entries for project")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")

    async def get_stats(self) -> Dict:
        """Get cache statistics"""
        # No check needed - if we got here, Redis is connected

        try:
            pattern = f"ki_autoagent:{self.project_hash}:*"
            keys = list(self.redis.scan_iter(match=pattern))
            total_size = 0

            for key in keys:
                if not key.endswith(b':meta'):
                    size = self.redis.memory_usage(key) or 0
                    total_size += size

            return {
                "status": "connected",
                "entries": len([k for k in keys if not k.endswith(b':meta')]),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2)
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e)}