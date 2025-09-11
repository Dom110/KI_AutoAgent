"""
CodeSmithClaude - Python Developer Agent
Spezialisiert auf Code-Generierung mit Claude 3.5 Sonnet
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent

class CodeSmithClaude(BaseAgent):
    """
    Expert Python Developer mit Trading-Fokus
    Nutzt Claude 3.5 Sonnet für beste Code-Qualität
    """
    
    def __init__(self):
        super().__init__(
            name="CodeSmithClaude",
            role="Python Developer",
            model="claude-3-5-sonnet-20241022"
        )
        
        self.temperature = 0.2  # Lower for more consistent code
        self.max_tokens = 8000  # More tokens for complete implementations
        
        self.system_prompt = """You are CodeSmithClaude, an expert Python developer specializing in financial and trading systems.

Your expertise includes:
- Python 3.11+ with type hints and modern features
- Trading libraries: pandas, numpy, ib_insync, ccxt, backtrader, zipline
- Web frameworks: FastAPI, Django, Flask, Streamlit
- Async programming and concurrency
- Database integration: SQLAlchemy, PostgreSQL, MongoDB
- Testing: pytest, unittest, mock
- Clean Code principles and SOLID design patterns

When writing code:
1. Always use type hints for function signatures
2. Write comprehensive docstrings (Google style)
3. Include error handling and validation
4. Follow PEP 8 style guidelines
5. Optimize for readability and performance
6. Add inline comments for complex logic
7. Consider edge cases and error scenarios

Code quality standards:
- DRY (Don't Repeat Yourself)
- SOLID principles
- Defensive programming
- Comprehensive error handling
- Performance optimization
- Security best practices"""
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "skills": [
                "python",
                "pandas",
                "numpy",
                "async_programming",
                "api_development",
                "testing",
                "debugging",
                "refactoring"
            ],
            "frameworks": [
                "fastapi",
                "django",
                "flask",
                "streamlit",
                "pytest"
            ],
            "trading_libs": [
                "ib_insync",
                "ccxt",
                "backtrader",
                "zipline",
                "yfinance"
            ],
            "databases": [
                "postgresql",
                "mongodb",
                "redis",
                "sqlite"
            ],
            "output_types": [
                "implementation",
                "module",
                "class",
                "function",
                "tests"
            ]
        }
    
    async def execute(self, task: str, context: Dict) -> Dict:
        """
        Implementiert Code basierend auf Anforderungen
        """
        # Build specialized prompt for code generation
        prompt = self._build_coding_prompt(task, context)
        
        # Generate code (mock for now)
        code = await self._generate_code(prompt, context)
        
        # Validate generated code
        validation = self._validate_code(code)
        
        # Extract and organize code
        organized_code = self._organize_code(code)
        
        return {
            "agent": self.name,
            "task": task,
            "output": code,
            "code": organized_code,
            "validation": validation,
            "status": "success" if validation["valid"] else "needs_review"
        }
    
    def _build_coding_prompt(self, task: str, context: Dict) -> str:
        """
        Baut spezialisierten Prompt für Code-Generierung
        """
        prompt_parts = [self.system_prompt, "\n"]
        
        # Add task
        prompt_parts.append(f"Task: {task}\n")
        
        # Add architecture context if available
        if context.get("architecture"):
            prompt_parts.append(f"Architecture Context:\n{context['architecture'][:1000]}\n")
        
        # Add specific requirements
        if context.get("requirements"):
            prompt_parts.append(f"Requirements:\n{context['requirements']}\n")
        
        # Add technology constraints
        if context.get("technologies"):
            prompt_parts.append(f"Use these technologies: {context['technologies']}\n")
        
        # Specific instructions
        prompt_parts.append("\nPlease provide:")
        prompt_parts.append("1. Complete, working Python implementation")
        prompt_parts.append("2. Type hints for all functions")
        prompt_parts.append("3. Comprehensive docstrings")
        prompt_parts.append("4. Error handling")
        prompt_parts.append("5. Example usage if applicable")
        prompt_parts.append("6. Unit tests if appropriate")
        
        return "\n".join(prompt_parts)
    
    async def _generate_code(self, prompt: str, context: Dict) -> str:
        """
        Generiert Python-Code
        """
        # Mock implementation for testing
        # In production: Use Anthropic API with Claude 3.5 Sonnet
        
        code = '''"""
Trading Bot Implementation
A complete trading bot with momentum strategy
"""
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TradeSignal:
    """Represents a trading signal"""
    symbol: str
    action: str  # 'buy', 'sell', 'hold'
    confidence: float
    timestamp: datetime
    price: float
    quantity: int
    
class MomentumStrategy:
    """
    Momentum-based trading strategy
    Identifies stocks with strong momentum for trading opportunities
    """
    
    def __init__(
        self,
        lookback_period: int = 20,
        momentum_threshold: float = 0.02,
        risk_percentage: float = 0.02
    ):
        """
        Initialize momentum strategy
        
        Args:
            lookback_period: Number of periods for momentum calculation
            momentum_threshold: Minimum momentum threshold for signals
            risk_percentage: Risk per trade as percentage of capital
        """
        self.lookback_period = lookback_period
        self.momentum_threshold = momentum_threshold
        self.risk_percentage = risk_percentage
        self.positions: Dict[str, float] = {}
        
    def calculate_momentum(self, prices: pd.Series) -> float:
        """
        Calculate momentum indicator
        
        Args:
            prices: Series of historical prices
            
        Returns:
            Momentum value as percentage change
        """
        if len(prices) < self.lookback_period:
            return 0.0
            
        recent_prices = prices.tail(self.lookback_period)
        return (recent_prices.iloc[-1] / recent_prices.iloc[0] - 1)
    
    def generate_signal(
        self,
        symbol: str,
        data: pd.DataFrame,
        capital: float
    ) -> Optional[TradeSignal]:
        """
        Generate trading signal based on momentum
        
        Args:
            symbol: Stock symbol
            data: DataFrame with OHLCV data
            capital: Available capital
            
        Returns:
            TradeSignal if conditions met, None otherwise
        """
        try:
            # Calculate momentum
            momentum = self.calculate_momentum(data['close'])
            
            # Current price
            current_price = data['close'].iloc[-1]
            
            # Position sizing
            position_size = self._calculate_position_size(
                capital,
                current_price
            )
            
            # Generate signal based on momentum
            if momentum > self.momentum_threshold:
                return TradeSignal(
                    symbol=symbol,
                    action='buy',
                    confidence=min(momentum / self.momentum_threshold, 1.0),
                    timestamp=datetime.now(),
                    price=current_price,
                    quantity=position_size
                )
            elif momentum < -self.momentum_threshold:
                return TradeSignal(
                    symbol=symbol,
                    action='sell',
                    confidence=min(abs(momentum) / self.momentum_threshold, 1.0),
                    timestamp=datetime.now(),
                    price=current_price,
                    quantity=position_size
                )
            else:
                return TradeSignal(
                    symbol=symbol,
                    action='hold',
                    confidence=0.5,
                    timestamp=datetime.now(),
                    price=current_price,
                    quantity=0
                )
                
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return None
    
    def _calculate_position_size(
        self,
        capital: float,
        price: float
    ) -> int:
        """
        Calculate position size based on risk management
        
        Args:
            capital: Available capital
            price: Current stock price
            
        Returns:
            Number of shares to trade
        """
        risk_amount = capital * self.risk_percentage
        shares = int(risk_amount / price)
        return max(shares, 1)  # At least 1 share
    
    async def backtest(
        self,
        data: pd.DataFrame,
        initial_capital: float = 10000
    ) -> Dict[str, float]:
        """
        Backtest the strategy on historical data
        
        Args:
            data: Historical price data
            initial_capital: Starting capital
            
        Returns:
            Dictionary with performance metrics
        """
        capital = initial_capital
        trades = []
        
        for i in range(self.lookback_period, len(data)):
            window = data.iloc[:i+1]
            signal = self.generate_signal('TEST', window, capital)
            
            if signal and signal.action != 'hold':
                # Simulate trade execution
                if signal.action == 'buy':
                    cost = signal.price * signal.quantity
                    if cost <= capital:
                        capital -= cost
                        trades.append(signal)
                elif signal.action == 'sell' and trades:
                    # Simplified: sell all positions
                    revenue = signal.price * signal.quantity
                    capital += revenue
        
        # Calculate metrics
        total_return = (capital - initial_capital) / initial_capital
        num_trades = len(trades)
        
        return {
            'total_return': total_return,
            'final_capital': capital,
            'num_trades': num_trades,
            'avg_trade_size': np.mean([t.quantity for t in trades]) if trades else 0
        }


# Example usage
async def main():
    """Example usage of the momentum strategy"""
    
    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    prices = 100 + np.cumsum(np.random.randn(100) * 2)
    
    data = pd.DataFrame({
        'date': dates,
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, 100)
    })
    
    # Initialize strategy
    strategy = MomentumStrategy(
        lookback_period=20,
        momentum_threshold=0.02,
        risk_percentage=0.02
    )
    
    # Generate signal
    signal = strategy.generate_signal('AAPL', data, 10000)
    if signal:
        print(f"Signal: {signal.action} {signal.quantity} shares at ${signal.price:.2f}")
        print(f"Confidence: {signal.confidence:.2%}")
    
    # Run backtest
    results = await strategy.backtest(data)
    print(f"Backtest Results:")
    print(f"  Total Return: {results['total_return']:.2%}")
    print(f"  Final Capital: ${results['final_capital']:.2f}")
    print(f"  Number of Trades: {results['num_trades']}")


if __name__ == "__main__":
    asyncio.run(main())
'''
        
        return code
    
    def _organize_code(self, code: str) -> Dict[str, str]:
        """
        Organisiert Code in Komponenten
        """
        import re
        
        organized = {
            "full_code": code,
            "classes": [],
            "functions": [],
            "imports": []
        }
        
        # Extract classes
        class_pattern = r'class\s+(\w+).*?(?=class\s+\w+|def\s+\w+|$)'
        classes = re.findall(class_pattern, code, re.DOTALL)
        organized["classes"] = classes
        
        # Extract functions
        func_pattern = r'def\s+(\w+)\s*\([^)]*\)'
        functions = re.findall(func_pattern, code)
        organized["functions"] = functions
        
        # Extract imports
        import_pattern = r'^(?:from|import)\s+.+$'
        imports = re.findall(import_pattern, code, re.MULTILINE)
        organized["imports"] = imports
        
        return organized