"""
Task Cancellation Support for KI AutoAgent
"""
import asyncio
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class CancelToken:
    """Thread-safe cancellation token"""

    def __init__(self):
        self._cancelled = False
        self._lock = asyncio.Lock()

    async def cancel(self):
        """Cancel this token"""
        async with self._lock:
            self._cancelled = True
            logger.info("Cancel token activated")

    @property
    def is_cancelled(self) -> bool:
        """Check if cancelled"""
        return self._cancelled

    async def check_cancellation(self):
        """Raises CancelledError if cancelled"""
        if self._cancelled:
            raise asyncio.CancelledError("Task was cancelled by user")


class TaskCancelledException(Exception):
    """Raised when a task is cancelled"""
    pass