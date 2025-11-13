"""
E2E Testing Framework for React Applications
Production-ready E2E test generation and execution
"""

from .test_generator import E2ETestGenerator
from .browser_engine import BrowserEngine
from .react_analyzer import ReactComponentAnalyzer
from .test_executor import PlaywrightTestExecutor
from .assertions import TestAssertions

__all__ = [
    'E2ETestGenerator',
    'BrowserEngine',
    'ReactComponentAnalyzer',
    'PlaywrightTestExecutor',
    'TestAssertions',
]

__version__ = '1.0.0'