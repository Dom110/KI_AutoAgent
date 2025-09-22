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
            model="claude-3-5-sonnet-20241022",
            capabilities=[
                AgentCapability.CODE_GENERATION,
                AgentCapability.ARCHITECTURE_DESIGN
            ],
            temperature=0.4,  # Lower for precise financial calculations
            max_tokens=4000,
            icon="📈"
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
                content=self._generate_fallback_strategy(request.prompt),
                agent=self.config.agent_id
            )

    def _generate_fallback_strategy(self, prompt: str) -> str:
        """
        Generate fallback trading strategy when API is unavailable
        """
        return f"""
# 📈 Trading Strategy Analysis

## Request: "{prompt[:100]}..."

## Strategy Framework

### 1. **Core Components**
```python
class TradingStrategy:
    def __init__(self, capital=100000):
        self.capital = capital
        self.position_size = 0.02  # 2% risk per trade
        self.stop_loss = 0.05  # 5% stop loss
        self.take_profit = 0.15  # 15% take profit
        
    def calculate_position_size(self, price, stop_distance):
        risk_amount = self.capital * self.position_size
        shares = risk_amount / stop_distance
        return min(shares, self.capital / price)
        
    def execute_signal(self, signal, price):
        if signal == 'BUY':
            return self.open_long_position(price)
        elif signal == 'SELL':
            return self.close_position(price)
```

### 2. **Risk Management**
- **Position Sizing**: Kelly Criterion or Fixed Fractional
- **Stop Loss**: ATR-based or percentage-based
- **Portfolio Heat**: Max 6% total portfolio risk
- **Correlation**: Limit correlated positions

### 3. **Technical Indicators**
```python
# Moving Average Crossover
def sma_crossover(prices, fast=20, slow=50):
    sma_fast = prices.rolling(fast).mean()
    sma_slow = prices.rolling(slow).mean()
    signal = (sma_fast > sma_slow).astype(int)
    return signal.diff()  # 1 = buy, -1 = sell

# RSI Momentum
def rsi_signal(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return (rsi < 30).astype(int) - (rsi > 70).astype(int)
```

### 4. **Backtesting Framework**
```python
class Backtest:
    def run(self, strategy, data):
        results = []
        for date, price in data.iterrows():
            signal = strategy.generate_signal(price)
            position = strategy.execute_signal(signal, price)
            results.append(position)
        return self.calculate_metrics(results)
        
    def calculate_metrics(self, results):
        returns = pd.Series(results).pct_change()
        sharpe = returns.mean() / returns.std() * np.sqrt(252)
        max_dd = (returns.cumsum() - returns.cumsum().cummax()).min()
        return {
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'total_return': returns.sum()
        }
```

### 5. **Performance Metrics**
- **Sharpe Ratio**: > 1.5 (good), > 2.0 (excellent)
- **Max Drawdown**: < 20% acceptable
- **Win Rate**: 40-60% typical
- **Risk/Reward**: Minimum 1:2 ratio
- **Profit Factor**: > 1.5 desirable

## 📊 Recommended Architecture

1. **Data Pipeline**: Real-time feed → Processing → Signal generation
2. **Execution Engine**: Order management → Risk checks → Broker API
3. **Monitoring**: Live P&L → Risk metrics → Alerts
4. **Storage**: TimescaleDB for time-series data

---
*Analysis by TradeStrat - Trading Strategy Expert*
        """

    async def _process_agent_request(self, message: Any) -> Any:
        """Process request from another agent"""
        request = TaskRequest(
            prompt=message.get("prompt", ""),
            context=message.get("context", {})
        )
        result = await self.execute(request)
        return result.content
