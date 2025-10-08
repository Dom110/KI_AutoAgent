"""
Adapters for external services.

This module contains adapters that allow integration with external services
that don't have native LangChain support.
"""

from .claude_cli_simple import ClaudeCLISimple

__all__ = ["ClaudeCLISimple"]
