"""
Centralized Error Handler with Help Message

Ensures that the help/documentation navigation message is shown exactly once
when any critical error occurs.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global flag to ensure message is shown only once per process
_help_message_shown = False


def print_help_message_once():
    """
    Print the documentation navigation help message exactly once.
    Subsequent calls are ignored.
    """
    global _help_message_shown
    
    if _help_message_shown:
        return
    
    _help_message_shown = True
    
    help_message = """
================================================================================
                    📞 WELCHE DATEI LESEN?
================================================================================

WENN...                              DANN LESE...
───────────────────────────────────────────────────────────────────────────────
Ich weiß nicht wie ich starte        → START_HERE.md
Ich brauche schnelle Hilfe           → DEUTSCHE_ANLEITUNG.md
Ich will alles verstehen             → START_SERVER_GUIDE.md
Ich brauche technische Details       → COMPLETION_SUMMARY.md
Ich muss berichten                   → EXECUTIVE_SUMMARY_DE.txt
Ich deploye auf Production           → PRODUCTION_STATUS.md
Ich brauche einen Quick Check        → README_LATEST.md
Ich suche eine spezifische Info      → FILES_OVERVIEW.txt (diese!)

================================================================================
"""
    
    print(help_message)
    logger.info("Help message displayed")


def handle_critical_error(error_type: str, error_message: str, show_help: bool = True):
    """
    Handle a critical error and optionally show help message.
    
    Args:
        error_type: Type of error (e.g., "DATABASE_ERROR", "API_ERROR", "STARTUP_ERROR")
        error_message: Detailed error message
        show_help: Whether to show help message (default: True)
    """
    error_box = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         ❌ CRITICAL ERROR
║ Type: {error_type:<76}║
╚══════════════════════════════════════════════════════════════════════════════╝

Error Details:
{error_message}

"""
    
    print(error_box)
    logger.error(f"{error_type}: {error_message}")
    
    if show_help:
        print_help_message_once()


def handle_startup_error(error_message: str, suggestions: Optional[list] = None):
    """
    Handle a startup-specific error with suggestions.
    
    Args:
        error_message: Detailed error message
        suggestions: Optional list of fix suggestions
    """
    error_box = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ❌ STARTUP ERROR
╚══════════════════════════════════════════════════════════════════════════════╝

Error:
{error_message}
"""
    
    if suggestions:
        error_box += "\n✅ SUGGESTED FIXES:\n"
        for i, suggestion in enumerate(suggestions, 1):
            error_box += f"   {i}. {suggestion}\n"
    
    error_box += "\n"
    
    print(error_box)
    logger.error(f"Startup Error: {error_message}")
    
    print_help_message_once()


def handle_api_error(api_name: str, error_message: str, status_code: Optional[int] = None):
    """
    Handle API-related errors.
    
    Args:
        api_name: Name of the API (e.g., "OpenAI", "Anthropic")
        error_message: Detailed error message
        status_code: HTTP status code if applicable
    """
    status_info = f" (HTTP {status_code})" if status_code else ""
    
    error_box = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ❌ API ERROR - {api_name}{status_info}
╚══════════════════════════════════════════════════════════════════════════════╝

Error Details:
{error_message}

💡 COMMON SOLUTIONS:
   • Check API key configuration in ~/.ki_autoagent/config/.env
   • Verify API credentials are correct and have sufficient permissions
   • Check API account balance/quota at provider dashboard
   • Ensure API endpoint is accessible

"""
    
    print(error_box)
    logger.error(f"{api_name} API Error: {error_message}")
    
    print_help_message_once()


def handle_runtime_error(error_message: str, context: Optional[str] = None):
    """
    Handle runtime errors during execution.
    
    Args:
        error_message: Detailed error message
        context: Optional context information about where error occurred
    """
    error_box = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ❌ RUNTIME ERROR
╚══════════════════════════════════════════════════════════════════════════════╝

Error Details:
{error_message}
"""
    
    if context:
        error_box += f"\nContext: {context}\n"
    
    error_box += "\n"
    
    print(error_box)
    logger.error(f"Runtime Error: {error_message}" + (f" (Context: {context})" if context else ""))
    
    print_help_message_once()


def reset_help_message_flag():
    """
    Reset the help message flag. Useful for testing or multi-session scenarios.
    """
    global _help_message_shown
    _help_message_shown = False
    logger.debug("Help message flag reset")