"""
Project Contexts Package

This package contains domain-specific project contexts for the KI_AutoAgent system.
Each context provides specialized instructions, quality gates, and requirements
for different software domains (trading, web apps, APIs, etc.).
"""

from .base_project_context import BaseProjectContext, ProjectSpecification
from .trading_project_context import TradingProjectContext
from .web_app_context import WebAppProjectContext

__all__ = [
    'BaseProjectContext',
    'ProjectSpecification',
    'TradingProjectContext',
    'WebAppProjectContext'
]