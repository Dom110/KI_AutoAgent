"""
Radon Metrics - Code complexity and maintainability metrics
Stub implementation for compatibility
"""

import logging
from typing import Dict, Any, Callable, Optional

logger = logging.getLogger(__name__)


class RadonMetrics:
    """
    Code complexity metrics using Radon
    This is a stub implementation - full version requires radon library
    """

    def __init__(self):
        logger.debug("RadonMetrics: Stub implementation - install radon for full functionality")

    async def calculate_all_metrics(
        self,
        root_path: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Calculate code metrics (complexity, maintainability, etc.)

        Returns:
            {
                'summary': {
                    'average_complexity': 0,
                    'average_maintainability': 0,
                    'quality_score': 0
                },
                'files': []
            }
        """
        if progress_callback:
            await progress_callback("📊 Code metrics calculation (stub - install radon for real analysis)")

        return {
            'summary': {
                'average_complexity': 0.0,
                'average_maintainability': 0.0,
                'quality_score': 0.0
            },
            'files': [],
            'note': 'Stub implementation - install radon library for real code metrics'
        }
