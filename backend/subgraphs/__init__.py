"""
v6.1 Subgraphs - Claude CLI Compatible

All LangGraph subgraphs for the v6.1 workflow.
Uses ClaudeCLISimple instead of broken langchain-anthropic.
Documentation: V6_0_ARCHITECTURE.md
"""

# Use v6.1 versions (no langchain-anthropic dependency)
from .research_subgraph_v6_1 import create_research_subgraph
from .architect_subgraph_v6 import create_architect_subgraph
from .codesmith_subgraph_v6_1 import create_codesmith_subgraph
from .reviewfix_subgraph_v6_1 import create_reviewfix_subgraph

__all__ = [
    "create_research_subgraph",
    "create_architect_subgraph",
    "create_codesmith_subgraph",
    "create_reviewfix_subgraph",
]
