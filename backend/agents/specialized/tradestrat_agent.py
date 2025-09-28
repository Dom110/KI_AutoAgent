"""
TradeStrat Agent - Trading Strategy and Financial Analysis Expert
Specialized in algorithmic trading and financial systems
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..base.chat_agent import ChatAgent
from ..base.base_agent import (
    AgentConfig, TaskRequest, TaskResult, AgentCapability
)
from utils.claude_code_service import ClaudeCodeService, ClaudeCodeConfig

logger = logging.getLogger(__name__)

class TradeStratAgent(ChatAgent):
    """
    Trading Strategy and Financial Analysis Expert
    - Algorithmic trading strategies
    - Risk management systems
    - Market analysis
    - Backtesting frameworks
    - Financial calculations
    """

    def __init__(self):
        config = AgentConfig(
            agent_id="tradestrat",
            name="TradeStrat",
            full_name="Trading Strategy Expert",
            description="Specialized in algorithmic trading and financial analysis",
            model="claude-4.1-sonnet-20250920",
            capabilities=[
                AgentCapability.CODE_GENERATION,
                AgentCapability.ARCHITECTURE_DESIGN
            ],
            temperature=0.4,  # Lower for precise financial calculations
            max_tokens=4000,
            icon="📈",
            instructions_path=".ki_autoagent/instructions/tradestrat-instructions.md"
        )
        super().__init__(config)
        # Use Claude CLI - NO FALLBACKS
        self.ai_service = ClaudeCodeService(
            ClaudeCodeConfig(model="sonnet")
        )
        if not self.ai_service.is_available():
            logger.error("TradeStrat requires Claude CLI! Install with: npm install -g @anthropic-ai/claude-code")

    async def execute(self, request: TaskRequest) -> TaskResult:
        """
        Execute trading strategy task
        """
        try:
            system_prompt = """
            You are TradeStrat, an expert in algorithmic trading and financial systems.
            Your expertise includes:
            1. 📈 Trading Strategies - Design and implement algorithms
            2. ⚠️ Risk Management - Position sizing, stop losses, portfolio optimization
            3. 📊 Market Analysis - Technical indicators, price patterns
            4. 🧪 Backtesting - Historical performance validation
            5. 💰 Financial Math - Options pricing, portfolio theory
            
            Always consider:
            - Risk-adjusted returns
            - Transaction costs
            - Market microstructure
            - Regulatory compliance
            - Performance metrics (Sharpe, Sortino, Max Drawdown)
            """

            if not self.ai_service.is_available():
                raise Exception("Claude CLI not available for TradeStrat")

            response = await self.ai_service.complete(
                prompt=request.prompt,
                system_prompt=system_prompt,
                temperature=0.4
            )

            return TaskResult(
                status="success",
                content=response,
                agent=self.config.agent_id,
                metadata={
                    "model": self.config.model,
                    "analysis_type": "trading_strategy",
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"TradeStrat execution error: {e}")
            return TaskResult(
                status="error",
                content=error_msg,
                agent=self.config.agent_id
            )

    # ASIMOV RULE 1: NO FALLBACK - FALLBACK METHOD REMOVED
    # All fallback functionality has been eliminated to enforce fail-fast architecture
    # If TradeStrat cannot provide trading strategy analysis, the system must fail explicitly

    async def _process_agent_request(self, message: Any) -> Any:
        """Process request from another agent"""
        request = TaskRequest(
            prompt=message.get("prompt", ""),
            context=message.get("context", {})
        )
        result = await self.execute(request)
        return result.content
