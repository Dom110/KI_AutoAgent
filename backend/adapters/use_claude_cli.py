"""
Utility to use Claude CLI instead of Anthropic API

This patches the subgraphs to use ClaudeCLISimple instead of ChatAnthropic.

Usage:
    # At the start of your script/test:
    from adapters.use_claude_cli import use_claude_cli
    use_claude_cli()

    # Now all agents will use Claude CLI instead of API
    from workflow_v6 import WorkflowV6
    workflow = WorkflowV6(workspace_path="/path")

Author: KI AutoAgent Team
Python: 3.13+
"""

import sys
from unittest.mock import Mock

def use_claude_cli():
    """
    Patch langchain_anthropic.ChatAnthropic to use ClaudeCLISimple.

    This allows existing code to work without changes while using
    the Claude CLI instead of the Anthropic API.
    """
    from adapters.claude_cli_simple import ClaudeCLISimple

    # Create a mock module
    mock_anthropic = Mock()
    mock_anthropic.ChatAnthropic = ClaudeCLISimple

    # Replace in sys.modules
    sys.modules['langchain_anthropic'] = mock_anthropic

    print("✅ Claude CLI adapter activated")
    print("   All ChatAnthropic calls will use `claude --print`")
