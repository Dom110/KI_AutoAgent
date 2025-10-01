"""
KI_AutoAgent - Multi-Agent System
Alle verfügbaren Agenten für das System
"""

from .base_agent import BaseAgent
from .architect_gpt import ArchitectGPT
from .codesmith_claude import CodeSmithClaude
from .docu_bot import DocuBot
from .reviewer_gpt import ReviewerGPT
from .fixer_bot import FixerBot
from .trade_strat import TradeStrat
from .research_bot import ResearchBot
from .opus_arbitrator import OpusArbitrator

__all__ = [
    'BaseAgent',
    'ArchitectGPT',
    'CodeSmithClaude',
    'DocuBot',
    'ReviewerGPT',
    'FixerBot',
    'TradeStrat',
    'ResearchBot',
    'OpusArbitrator'
]

# Agent Registry
AVAILABLE_AGENTS = {
    "ArchitectGPT": ArchitectGPT,
    "CodeSmithClaude": CodeSmithClaude,
    "DocuBot": DocuBot,
    "ReviewerGPT": ReviewerGPT,
    "FixerBot": FixerBot,
    "TradeStrat": TradeStrat,
    "ResearchBot": ResearchBot,
    "OpusArbitrator": OpusArbitrator
}