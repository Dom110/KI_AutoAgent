"""
Semgrep Analyzer - Security vulnerability detection
Stub implementation for compatibility
"""

import logging
from typing import Dict, Any, Callable, Optional

logger = logging.getLogger(__name__)


class SemgrepAnalyzer:
    """
    Security analysis using Semgrep
    This is a stub implementation - full version requires semgrep CLI
    """

    def __init__(self):
        logger.debug("SemgrepAnalyzer: Stub implementation - install semgrep for full functionality")

    async def run_analysis(
        self,
        root_path: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Run security analysis on codebase

        Returns:
            {
                'findings': [],
                'summary': {
                    'critical': 0,
                    'high': 0,
                    'medium': 0,
                    'low': 0
                }
            }
        """
        if progress_callback:
            await progress_callback("🔒 Security analysis (stub - install semgrep for real analysis)")

        return {
            'findings': [],
            'summary': {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0
            },
            'note': 'Stub implementation - install semgrep CLI for real security analysis'
        }
