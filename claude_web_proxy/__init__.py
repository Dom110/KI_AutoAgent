"""
Claude Web Proxy Package
Browser-based Claude.ai integration for CrewAI
"""

__version__ = "1.0.0"
__author__ = "KI_AutoAgent System"

# Export main classes for easy importing
from .claude_browser import ClaudeBrowser
from .crewai_integration import ClaudeWebLLM, create_claude_web_llm

__all__ = [
    'ClaudeBrowser',
    'ClaudeWebLLM', 
    'create_claude_web_llm'
]