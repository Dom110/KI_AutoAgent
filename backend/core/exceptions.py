"""
Custom exception classes for KI AutoAgent
Provides detailed error information with file, line, and solution guidance
"""

import sys
import traceback
from typing import List, Dict, Any


class DependencyError(Exception):
    """Raised when required dependencies are missing at startup"""

    def __init__(self, errors: List[Dict[str, Any]]):
        self.errors = errors
        super().__init__(self._format_errors())

    def _format_errors(self) -> str:
        """Format errors into a detailed message"""
        msg = "\n" + "="*80 + "\n"
        msg += "🚨 SYSTEM STARTUP FAILED - MISSING DEPENDENCIES\n"
        msg += "="*80 + "\n\n"

        for i, error in enumerate(self.errors, 1):
            msg += f"❌ ERROR {i}: {error['component']}\n"
            msg += f"{'─'*60}\n"
            msg += f"📁 Location:  {error['file']}:{error['line']}\n"
            msg += f"❗ Problem:   {error['error']}\n"
            msg += f"💡 Solution:  {error['solution']}\n"
            if error.get('traceback'):
                msg += f"\n📋 Traceback:\n{error['traceback']}\n"
            msg += "\n"

        msg += "="*80 + "\n"
        msg += "⚠️  The system cannot start until these dependencies are resolved.\n"
        msg += "="*80 + "\n"
        return msg


class CacheNotAvailableError(Exception):
    """Raised when cache system is not available"""

    def __init__(self, component: str, file: str = None, line: int = None):
        # Get file and line if not provided
        if not file or not line:
            frame = sys._getframe(1)
            file = file or frame.f_code.co_filename
            line = line or frame.f_lineno

        msg = f"""
{'='*80}
🚨 CACHE SYSTEM NOT AVAILABLE
{'='*80}

❌ Component: {component}
📁 Location:  {file}:{line}

❗ Problem:   Redis cache is required but not available
💡 Solutions:

1. Install Redis Python client:
   pip install redis

2. Start Redis server using Docker:
   docker run -d -p 6379:6379 redis:7-alpine

3. Or install Redis locally:
   - macOS:  brew install redis && brew services start redis
   - Linux:  sudo apt-get install redis-server && sudo systemctl start redis
   - Windows: Use Docker or WSL2

4. Verify Redis is running:
   redis-cli ping
   (should return PONG)

{'='*80}
⚠️  The system REQUIRES Redis for caching. No fallback available.
{'='*80}
"""
        super().__init__(msg)


class IndexingNotAvailableError(Exception):
    """Raised when code indexing tools are not available"""

    def __init__(self, missing_package: str, file: str = None, line: int = None):
        # Get file and line if not provided
        if not file or not line:
            frame = sys._getframe(1)
            file = file or frame.f_code.co_filename
            line = line or frame.f_lineno

        msg = f"""
{'='*80}
🚨 CODE INDEXING TOOLS NOT AVAILABLE
{'='*80}

❌ Missing Package: {missing_package}
📁 Location:  {file}:{line}

❗ Problem:   Required code analysis tools are not installed
💡 Solution:

Install the missing packages:
pip install tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-typescript

Or install all analysis tools:
pip install -r requirements.txt

{'='*80}
⚠️  Code analysis features will NOT work without these packages.
{'='*80}
"""
        super().__init__(msg)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing"""

    def __init__(self, config_item: str, current_value: Any, expected: str,
                 file: str = None, line: int = None):
        # Get file and line if not provided
        if not file or not line:
            frame = sys._getframe(1)
            file = file or frame.f_code.co_filename
            line = line or frame.f_lineno

        msg = f"""
{'='*80}
🚨 CONFIGURATION ERROR
{'='*80}

❌ Config Item: {config_item}
📁 Location:    {file}:{line}
❗ Current:     {current_value}
✅ Expected:    {expected}

💡 Please check your configuration and ensure it matches the expected format.

{'='*80}
"""
        super().__init__(msg)


class SystemNotReadyError(Exception):
    """Raised when system is not properly initialized"""

    def __init__(self, component: str, reason: str, solution: str,
                 file: str = None, line: int = None):
        # Get file and line if not provided
        if not file or not line:
            frame = sys._getframe(1)
            file = file or frame.f_code.co_filename
            line = line or frame.f_lineno

        msg = f"""
{'='*80}
🚨 SYSTEM NOT READY
{'='*80}

❌ Component:  {component}
📁 Location:   {file}:{line}
❗ Reason:     {reason}
💡 Solution:   {solution}

{'='*80}
"""
        super().__init__(msg)