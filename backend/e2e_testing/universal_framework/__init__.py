"""
Universal Framework E2E Testing - Supports Any JavaScript/Python Framework

This module provides framework-agnostic E2E test generation that works with:
- Frontend: React, Vue, Angular, Svelte, Next.js, Nuxt
- Backend: FastAPI, Flask, Django, Express
- And many more...

Key Classes:
- FrameworkDetector: Auto-detects framework
- UniversalE2ETestGenerator: Generates tests for any framework
- BaseComponentAnalyzer: Base class for framework adapters

Usage:
    from backend.e2e_testing.universal_framework import UniversalE2ETestGenerator
    
    # Any framework - same code!
    generator = UniversalE2ETestGenerator("/path/to/app")
    result = generator.analyze_app()
    tests = generator.generate_tests()
    
    # Works for React, Vue, Angular, FastAPI, etc.!
"""

from .framework_detector import FrameworkDetector, FrameworkInfo
from .base_analyzer import (
    BaseComponentAnalyzer,
    UniversalAppStructure,
    Component,
    Route,
    Service,
)
from .universal_generator import UniversalE2ETestGenerator, analyze_and_generate_tests

__all__ = [
    'FrameworkDetector',
    'FrameworkInfo',
    'BaseComponentAnalyzer',
    'UniversalAppStructure',
    'Component',
    'Route',
    'Service',
    'UniversalE2ETestGenerator',
    'analyze_and_generate_tests',
]