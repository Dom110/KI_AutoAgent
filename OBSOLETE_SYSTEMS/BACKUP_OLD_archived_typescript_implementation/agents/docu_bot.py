"""
DocuBot - Documentation Generation Agent
Erstellt hochwertige Dokumentation und Guides
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent

class DocuBot(BaseAgent):
    """
    Documentation Expert mit GPT-4o (Nov 2024)
    Spezialisiert auf klare, strukturierte Dokumentation
    """
    
    def __init__(self):
        super().__init__(
            name="DocuBot",
            role="Documentation Specialist",
            model="gpt-4o-2024-11-20"
        )
        
        self.temperature = 0.3  # Lower for consistent documentation
        self.max_tokens = 4000
        
        self.system_prompt = """You are DocuBot, an expert documentation specialist.

Your expertise includes:
- API Documentation
- User Guides and Tutorials
- Technical Documentation
- README Files
- Code Comments and Docstrings
- Architecture Documentation
- Best Practices Guides

Documentation principles:
1. Clear and concise language
2. Logical structure and flow
3. Complete examples
4. Visual aids when helpful (diagrams, tables)
5. Accessibility for different audiences
6. Searchable and indexed content
7. Version control awareness

Output formats:
- Markdown (preferred)
- ReStructuredText
- HTML
- PDF-ready LaTeX
- Inline code documentation"""
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "skills": [
                "api_documentation",
                "user_guides",
                "technical_writing",
                "readme_creation",
                "docstring_generation",
                "tutorial_creation",
                "best_practices"
            ],
            "formats": [
                "markdown",
                "rst",
                "html",
                "latex",
                "sphinx"
            ],
            "specialties": [
                "developer_docs",
                "user_manuals",
                "api_reference",
                "quickstart_guides",
                "troubleshooting"
            ]
        }
    
    async def execute(self, task: str, context: Dict) -> Dict:
        """
        Generiert Dokumentation basierend auf Anforderungen
        """
        # Build documentation prompt
        prompt = self._build_documentation_prompt(task, context)
        
        # Generate documentation
        documentation = await self._generate_documentation(prompt, context)
        
        # Structure and format
        structured_docs = self._structure_documentation(documentation)
        
        return {
            "agent": self.name,
            "task": task,
            "output": documentation,
            "documentation": structured_docs,
            "format": context.get("format", "markdown"),
            "status": "success"
        }
    
    def _build_documentation_prompt(self, task: str, context: Dict) -> str:
        """
        Baut spezialisierten Prompt für Dokumentation
        """
        prompt_parts = [self.system_prompt, "\n"]
        
        # Add task
        prompt_parts.append(f"Task: {task}\n")
        
        # Add code context if available
        if context.get("code"):
            prompt_parts.append(f"Code to document:\n```python\n{context['code'][:2000]}\n```\n")
        
        # Add target audience
        if context.get("audience"):
            prompt_parts.append(f"Target audience: {context['audience']}\n")
        
        # Add documentation type
        if context.get("doc_type"):
            prompt_parts.append(f"Documentation type: {context['doc_type']}\n")
        
        # Specific instructions
        prompt_parts.append("\nPlease provide:")
        prompt_parts.append("1. Clear, well-structured documentation")
        prompt_parts.append("2. Examples where appropriate")
        prompt_parts.append("3. Proper formatting and sections")
        prompt_parts.append("4. Table of contents if lengthy")
        
        return "\n".join(prompt_parts)
    
    async def _generate_documentation(self, prompt: str, context: Dict) -> str:
        """
        Generiert Dokumentation
        """
        # Mock implementation for testing
        documentation = '''# Trading Bot Documentation

## Overview

This trading bot implements a momentum-based strategy designed to identify and capitalize on trending stocks. The system uses technical indicators and risk management principles to execute trades automatically.

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Usage](#usage)
4. [API Reference](#api-reference)
5. [Strategy Details](#strategy-details)
6. [Risk Management](#risk-management)
7. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- Python 3.8+
- pip package manager
- Trading account with supported broker

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/trading-bot.git
cd trading-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Broker Configuration
BROKER_API_KEY=your_api_key_here
BROKER_SECRET=your_secret_here
BROKER_ENDPOINT=https://api.broker.com

# Strategy Parameters
LOOKBACK_PERIOD=20
MOMENTUM_THRESHOLD=0.02
RISK_PERCENTAGE=0.02

# Trading Settings
MAX_POSITIONS=10
TRADING_HOURS_START=09:30
TRADING_HOURS_END=16:00
```

## Usage

### Quick Start

```python
from trading_bot import MomentumStrategy, TradingBot

# Initialize strategy
strategy = MomentumStrategy(
    lookback_period=20,
    momentum_threshold=0.02
)

# Create bot
bot = TradingBot(strategy)

# Run backtest
results = bot.backtest(
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Start live trading
bot.start_trading()
```

## API Reference

### MomentumStrategy

#### `__init__(lookback_period: int, momentum_threshold: float, risk_percentage: float)`

Initializes the momentum strategy.

**Parameters:**
- `lookback_period` (int): Number of periods for momentum calculation (default: 20)
- `momentum_threshold` (float): Minimum momentum for signal generation (default: 0.02)
- `risk_percentage` (float): Risk per trade as percentage of capital (default: 0.02)

#### `calculate_momentum(prices: pd.Series) -> float`

Calculates momentum indicator for given price series.

**Parameters:**
- `prices` (pd.Series): Historical price data

**Returns:**
- float: Momentum value as percentage change

#### `generate_signal(symbol: str, data: pd.DataFrame, capital: float) -> Optional[TradeSignal]`

Generates trading signal based on momentum analysis.

**Parameters:**
- `symbol` (str): Stock symbol
- `data` (pd.DataFrame): OHLCV data
- `capital` (float): Available capital

**Returns:**
- TradeSignal or None: Trade signal if conditions met

### TradingBot

#### `__init__(strategy: BaseStrategy, broker: Optional[Broker] = None)`

Initializes the trading bot.

**Parameters:**
- `strategy` (BaseStrategy): Trading strategy instance
- `broker` (Broker, optional): Broker connection instance

#### `start_trading()`

Starts live trading session.

**Raises:**
- `ConnectionError`: If broker connection fails
- `InsufficientFundsError`: If account balance too low

## Strategy Details

### Momentum Calculation

The strategy calculates momentum as:

```
Momentum = (Current Price / Price N periods ago) - 1
```

### Signal Generation

**Buy Signal:**
- Momentum > threshold
- Sufficient capital available
- Risk limits not exceeded

**Sell Signal:**
- Momentum < -threshold
- Position exists
- Stop loss or take profit triggered

## Risk Management

### Position Sizing

Position size is calculated using the Kelly Criterion with a safety factor:

```python
position_size = (capital * risk_percentage) / stop_loss_distance
```

### Stop Loss

- Fixed percentage: 2% below entry
- Trailing stop: Adjusts with profitable moves
- Time-based: Exit if no profit after N periods

### Portfolio Limits

- Maximum 10 concurrent positions
- No single position > 10% of portfolio
- Daily loss limit: 5% of capital

## Troubleshooting

### Common Issues

#### Connection Errors

```
Error: Failed to connect to broker API
```

**Solution:**
1. Check API credentials in `.env`
2. Verify network connection
3. Ensure API endpoint is correct

#### Data Issues

```
Error: Insufficient historical data
```

**Solution:**
1. Increase lookback period in data request
2. Check if symbol is valid
3. Verify market hours

#### Trading Errors

```
Error: Order rejected by broker
```

**Solution:**
1. Check account balance
2. Verify trading permissions
3. Ensure market is open

## Support

For issues and questions:
- GitHub Issues: [github.com/yourusername/trading-bot/issues]()
- Email: support@tradingbot.com
- Documentation: [docs.tradingbot.com]()

## License

MIT License - see LICENSE file for details.
'''
        
        return documentation
    
    def _structure_documentation(self, documentation: str) -> Dict[str, Any]:
        """
        Strukturiert Dokumentation in Sektionen
        """
        import re
        
        sections = {}
        current_section = "intro"
        current_content = []
        
        for line in documentation.split('\n'):
            if line.startswith('# '):
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = line[2:].lower().replace(' ', '_')
                current_content = [line]
            elif line.startswith('## '):
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = line[3:].lower().replace(' ', '_')
                current_content = [line]
            else:
                current_content.append(line)
        
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return {
            "sections": sections,
            "toc": list(sections.keys()),
            "word_count": len(documentation.split()),
            "has_examples": '```' in documentation,
            "format": "markdown"
        }