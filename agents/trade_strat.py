"""
TradeStrat - Trading Strategy Development Agent
Spezialisiert auf Entwicklung von Trading-Strategien
"""
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent

class TradeStrat(BaseAgent):
    """
    Trading Strategy Expert mit Claude Sonnet 4 (2025)
    Entwickelt und optimiert Trading-Strategien mit KI der nächsten Generation
    """
    
    def __init__(self):
        super().__init__(
            name="TradeStrat",
            role="Trading Strategy Developer",
            model="claude-sonnet-4-20250514"
        )
        
        self.temperature = 0.3  # Balanced for creativity and precision
        self.max_tokens = 6000
        
        self.system_prompt = """You are TradeStrat, an expert trading strategy developer and quantitative analyst.

Your expertise includes:
- Technical Analysis (indicators, patterns, signals)
- Fundamental Analysis (financials, ratios, valuation)
- Quantitative Strategies (statistical arbitrage, pairs trading, factor models)
- Risk Management (position sizing, stop-loss, portfolio optimization)
- Market Microstructure (order flow, liquidity, market making)
- Algorithmic Trading (execution algorithms, HFT, smart order routing)
- Backtesting & Optimization (walk-forward analysis, parameter optimization)
- Machine Learning in Trading (predictive models, reinforcement learning)

Strategy development approach:
1. Define clear entry and exit rules
2. Incorporate risk management from the start
3. Consider market conditions and regime changes
4. Include transaction costs and slippage
5. Validate with proper backtesting
6. Optimize without overfitting
7. Document all assumptions

Types of strategies:
- Momentum/Trend Following
- Mean Reversion
- Statistical Arbitrage
- Market Making
- Event-Driven
- Multi-Factor Models
- Options Strategies
- Crypto/DeFi Strategies

Always provide:
- Complete strategy logic
- Risk parameters
- Expected performance metrics
- Market conditions where it works best
- Potential weaknesses"""
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "skills": [
                "strategy_development",
                "backtesting",
                "risk_management",
                "technical_analysis",
                "quantitative_analysis",
                "portfolio_optimization",
                "market_analysis"
            ],
            "strategy_types": [
                "momentum",
                "mean_reversion",
                "arbitrage",
                "market_making",
                "event_driven",
                "multi_factor",
                "options"
            ],
            "markets": [
                "equities",
                "forex",
                "crypto",
                "commodities",
                "options",
                "futures"
            ],
            "tools": [
                "python",
                "pandas",
                "numpy",
                "ta-lib",
                "backtrader",
                "zipline",
                "quantlib"
            ]
        }
    
    async def execute(self, task: str, context: Dict) -> Dict:
        """
        Executes trading-related tasks
        """
        if task == "validate_trading_logic":
            return await self._validate_trading_logic(context)
        elif task == "suggest_improvements":
            return await self._suggest_improvements(context)
        elif task == "design_strategy":
            return await self._design_strategy(context)
        else:
            # Default strategy development
            return await self._develop_strategy(task, context)
    
    async def _validate_trading_logic(self, context: Dict) -> Dict:
        """
        Validiert Trading-Logik in bestehenden Code-Dateien
        """
        try:
            # Try Claude Web Integration first
            from claude_web_proxy.crewai_integration import create_claude_web_llm
            
            claude_web_llm = create_claude_web_llm(
                server_url="http://localhost:8000",
                agent_id="TradeStrat"
            )
            
            # Build validation prompt
            prompt = self._build_validation_prompt(context)
            
            # Get analysis from Claude Web
            analysis = await claude_web_llm.agenerate(prompt)
            
            print(f"✅ {self.name}: Echte Claude Web Trading-Validierung abgeschlossen!")
            
            return {
                "agent": self.name,
                "task": "validate_trading_logic",
                "output": analysis,
                "status": "success"
            }
            
        except Exception as e:
            print(f"⚠️ {self.name}: Claude Web nicht verfügbar ({e}), verwende Fallback")
            
            # Fallback: Basic validation logic
            return {
                "agent": self.name,
                "task": "validate_trading_logic", 
                "output": "Trading-Logik Validation - Fallback Modus",
                "status": "fallback"
            }
    
    def _build_validation_prompt(self, context: Dict) -> str:
        """
        Builds validation prompt for existing trading code
        """
        # Try to load the file content
        file_content = ""
        file_path = "/Users/dominikfoert/git/stock_analyser/strategies/ron_strategy.py"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            print(f"✅ {self.name}: Datei erfolgreich geladen ({len(file_content)} Zeichen)")
        except Exception as e:
            print(f"⚠️ {self.name}: Fehler beim Laden der Datei: {e}")
            file_content = "Datei konnte nicht geladen werden."
        
        prompt_parts = [
            "Du bist TradeStrat, ein Experte für Trading-Strategien und quantitative Analyse.",
            "Analysiere die folgende RON (Reversal Ohne News) Trading Strategy Implementierung:",
            "",
            f"DATEI: {file_path}",
            "",
            "CODE:",
            "```python",
            file_content,
            "```",
            "",
            "AUFGABE: Überprüfe die Implementierung auf:",
            "1. Korrektheit der VWAP-Berechnung",
            "2. Korrektheit der Fibonacci-Level-Berechnung", 
            "3. Logische Konsistenz der Handelsregeln",
            "4. Risk Management Implementation",
            "5. Code-Qualität und Best Practices",
            "6. Trading-spezifische Berechnungen und Logik",
            "7. Backtesting-Kompatibilität",
            "",
            "Gib eine detaillierte Bewertung mit:",
            "- Trading-Logik Validierung",
            "- Mathematische Korrektheit der Indikatoren",
            "- Strategieumsetzung vs. RON Regeln",
            "- Verbesserungsvorschläge"
        ]
        
        if context.get("user_request"):
            prompt_parts.append(f"\nSpezifische Anfrage: {context['user_request']}")
        
        return "\n".join(prompt_parts)
    
    async def _suggest_improvements(self, context: Dict) -> Dict:
        """
        Erstellt konkrete Verbesserungsvorschläge basierend auf vorheriger Analyse
        """
        try:
            # Try Claude Web Integration first
            from claude_web_proxy.crewai_integration import create_claude_web_llm
            
            claude_web_llm = create_claude_web_llm(
                server_url="http://localhost:8000",
                agent_id="TradeStrat"
            )
            
            # Build improvement prompt
            prompt = self._build_improvement_prompt(context)
            
            # Get suggestions from Claude Web
            suggestions = await claude_web_llm.agenerate(prompt)
            
            print(f"✅ {self.name}: Konkrete Verbesserungsvorschläge erstellt!")
            
            return {
                "agent": self.name,
                "task": "suggest_improvements",
                "output": suggestions,
                "status": "success",
                "ready_for_implementation": True
            }
            
        except Exception as e:
            print(f"⚠️ {self.name}: Claude Web nicht verfügbar ({e}), verwende Fallback")
            
            # Fallback: Basic improvement suggestions
            return {
                "agent": self.name,
                "task": "suggest_improvements", 
                "output": "Trading-Strategie Verbesserungsvorschläge - Fallback Modus:\n1. Code-Optimierung prüfen\n2. Risk Management erweitern\n3. Performance-Metriken hinzufügen",
                "status": "fallback"
            }
    
    def _build_improvement_prompt(self, context: Dict) -> str:
        """
        Builds improvement prompt based on previous analysis results
        """
        # Try to load the current file content
        file_content = ""
        file_path = "/Users/dominikfoert/git/stock_analyser/strategies/ron_strategy.py"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            print(f"✅ {self.name}: Aktuelle Implementierung geladen ({len(file_content)} Zeichen)")
        except Exception as e:
            print(f"⚠️ {self.name}: Fehler beim Laden der Datei: {e}")
            file_content = "Datei konnte nicht geladen werden."
        
        # Extract previous analysis results from context
        previous_analysis = ""
        if context.get("previous_results"):
            previous_analysis = context["previous_results"]
        elif context.get("user_request"):
            previous_analysis = f"Benutzeranfrage: {context['user_request']}"
        
        prompt_parts = [
            "Du bist TradeStrat, ein Experte für Trading-Strategien und Code-Verbesserungen.",
            "",
            "AUFGABE: Erstelle konkrete, umsetzbare Verbesserungsvorschläge für die RON Trading Strategie.",
            "",
            "AKTUELLE IMPLEMENTIERUNG:",
            f"Datei: {file_path}",
            "",
            "```python",
            file_content,
            "```",
            "",
            "VORHERIGE ANALYSE ERGEBNISSE:",
            previous_analysis if previous_analysis else "Keine vorherigen Analyseergebnisse verfügbar.",
            "",
            "ERSTELLE KONKRETE VERBESSERUNGSVORSCHLÄGE MIT:",
            "",
            "1. PERFORMANCE-OPTIMIERUNG:",
            "   - Algorithmus-Effizienz verbessern",
            "   - Memory-Usage optimieren", 
            "   - Calculation-Speed erhöhen",
            "",
            "2. CODE-QUALITÄT:",
            "   - Clean Code Prinzipien",
            "   - Bessere Dokumentation",
            "   - Error Handling verbessern",
            "",
            "3. TRADING-LOGIK VERBESSERUNGEN:",
            "   - RON Strategie Regeln verfeinern",
            "   - Risk Management erweitern",
            "   - Signal-Qualität verbessern",
            "",
            "4. TESTING & VALIDATION:",
            "   - Unit Tests hinzufügen",
            "   - Backtesting verbessern",
            "   - Edge-Cases behandeln",
            "",
            "5. NEUE FEATURES:",
            "   - Zusätzliche Indikatoren",
            "   - Erweiterte Analysen",
            "   - Better User Interface",
            "",
            "FORMAT DEINE ANTWORT SO:",
            "🎯 PRIORITÄT 1 - KRITISCH:",
            "[Konkreter Verbesserungsvorschlag mit Code-Beispiel]",
            "",
            "🔧 PRIORITÄT 2 - WICHTIG:",
            "[Konkreter Verbesserungsvorschlag mit Code-Beispiel]", 
            "",
            "⚡ PRIORITÄT 3 - NICE TO HAVE:",
            "[Konkreter Verbesserungsvorschlag mit Code-Beispiel]",
            "",
            "Jeder Vorschlag soll KONKRET und UMSETZBAR sein mit:",
            "- Klarer Beschreibung WARUM die Verbesserung wichtig ist",
            "- Code-Beispiel oder Pseudo-Code WIE es implementiert wird",
            "- Geschätzte Auswirkung auf Performance/Qualität"
        ]
        
        if context.get("specific_area"):
            prompt_parts.append(f"\nFOKUS auf Bereich: {context['specific_area']}")
        
        return "\n".join(prompt_parts)
    
    async def _design_strategy(self, context: Dict) -> Dict:
        """
        Design trading strategy task
        """
        # Analyze requirements
        requirements = self._analyze_requirements("design_strategy", context)
        
        # Build strategy prompt
        prompt = self._build_strategy_prompt("design_strategy", context, requirements)
        
        # Generate strategy
        strategy = await self._generate_strategy(prompt, context)
        
        # Create backtest framework
        backtest_code = self._create_backtest_framework(strategy)
        
        # Generate performance metrics
        metrics = self._generate_performance_metrics(strategy)
        
        return {
            "agent": self.name,
            "task": "design_strategy",
            "output": strategy,
            "requirements": requirements,
            "backtest_code": backtest_code,
            "performance_metrics": metrics,
            "status": "success"
        }
    
    async def _develop_strategy(self, task: str, context: Dict) -> Dict:
        """
        General strategy development task
        """
        # Analyze requirements
        requirements = self._analyze_requirements(task, context)
        
        # Build strategy prompt
        prompt = self._build_strategy_prompt(task, context, requirements)
        
        # Generate strategy
        strategy = await self._generate_strategy(prompt, context)
        
        # Create backtest framework
        backtest_code = self._create_backtest_framework(strategy)
        
        # Generate performance metrics
        metrics = self._generate_performance_metrics(strategy)
        
        return {
            "agent": self.name,
            "task": task,
            "output": strategy,
            "requirements": requirements,
            "backtest_code": backtest_code,
            "performance_metrics": metrics,
            "status": "success"
        }
    
    def _analyze_requirements(self, task: str, context: Dict) -> Dict:
        """
        Analysiert Anforderungen an die Strategie
        """
        requirements = {
            "strategy_type": "unknown",
            "market": "equities",
            "timeframe": "daily",
            "risk_tolerance": "medium",
            "capital": 100000,
            "objectives": []
        }
        
        task_lower = task.lower()
        
        # Detect strategy type
        if "momentum" in task_lower:
            requirements["strategy_type"] = "momentum"
        elif "mean reversion" in task_lower or "reversion" in task_lower:
            requirements["strategy_type"] = "mean_reversion"
        elif "arbitrage" in task_lower:
            requirements["strategy_type"] = "arbitrage"
        elif "market making" in task_lower:
            requirements["strategy_type"] = "market_making"
        
        # Detect market
        if "crypto" in task_lower or "bitcoin" in task_lower:
            requirements["market"] = "crypto"
        elif "forex" in task_lower or "currency" in task_lower:
            requirements["market"] = "forex"
        elif "options" in task_lower:
            requirements["market"] = "options"
        
        # Extract from context
        if context.get("timeframe"):
            requirements["timeframe"] = context["timeframe"]
        if context.get("capital"):
            requirements["capital"] = context["capital"]
        if context.get("risk_tolerance"):
            requirements["risk_tolerance"] = context["risk_tolerance"]
        
        return requirements
    
    def _build_strategy_prompt(self, task: str, context: Dict, requirements: Dict) -> str:
        """
        Baut spezialisierten Prompt für Strategie-Entwicklung
        """
        prompt_parts = [self.system_prompt, "\n"]
        
        # Add task
        prompt_parts.append(f"Strategy Development Task: {task}\n")
        
        # Add requirements
        prompt_parts.append(f"Strategy Type: {requirements['strategy_type']}")
        prompt_parts.append(f"Market: {requirements['market']}")
        prompt_parts.append(f"Timeframe: {requirements['timeframe']}")
        prompt_parts.append(f"Risk Tolerance: {requirements['risk_tolerance']}")
        prompt_parts.append(f"Initial Capital: ${requirements['capital']:,}\n")
        
        # Add market context if available
        if context.get("market_conditions"):
            prompt_parts.append(f"Current Market Conditions: {context['market_conditions']}\n")
        
        # Add constraints
        if context.get("constraints"):
            prompt_parts.append(f"Constraints: {context['constraints']}\n")
        
        # Specific instructions
        prompt_parts.append("\nPlease provide:")
        prompt_parts.append("1. Complete strategy implementation in Python")
        prompt_parts.append("2. Clear entry and exit rules")
        prompt_parts.append("3. Risk management parameters")
        prompt_parts.append("4. Position sizing logic")
        prompt_parts.append("5. Backtesting framework")
        prompt_parts.append("6. Expected performance metrics")
        
        return "\n".join(prompt_parts)
    
    async def _generate_strategy(self, prompt: str, context: Dict) -> str:
        """
        Generiert Trading-Strategie
        """
        # Mock implementation for testing
        strategy = '''# Mean Reversion Trading Strategy with Bollinger Bands

## Strategy Overview

This strategy exploits mean reversion opportunities using Bollinger Bands combined with RSI confirmation. It identifies oversold/overbought conditions and trades the reversion to the mean.

## Strategy Implementation

```python
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import talib
from dataclasses import dataclass
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Signal:
    """Trading signal with metadata"""
    timestamp: datetime
    symbol: str
    action: str  # 'buy', 'sell', 'close'
    price: float
    confidence: float
    reason: str
    position_size: int

class BollingerMeanReversionStrategy:
    """
    Mean Reversion Strategy using Bollinger Bands and RSI
    
    Strategy Logic:
    - BUY when price touches lower Bollinger Band AND RSI < 30
    - SELL when price touches upper Bollinger Band AND RSI > 70
    - EXIT when price crosses middle band (SMA) or stop-loss hit
    """
    
    def __init__(self, config: Dict = None):
        """Initialize strategy with configuration"""
        self.config = config or self._default_config()
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        
    def _default_config(self) -> Dict:
        """Default strategy parameters"""
        return {
            # Bollinger Bands
            'bb_period': 20,
            'bb_std': 2.0,
            
            # RSI
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            
            # Risk Management
            'position_size_pct': 0.02,  # 2% risk per trade
            'stop_loss_pct': 0.03,       # 3% stop loss
            'take_profit_pct': 0.06,     # 6% take profit
            'max_positions': 5,          # Maximum concurrent positions
            
            # Filters
            'min_volume': 1000000,       # Minimum daily volume
            'min_price': 5.0,            # Minimum stock price
            'atr_multiplier': 1.5,       # ATR-based stop loss
            
            # Capital
            'initial_capital': 100000,
            'commission': 0.001,         # 0.1% commission
            'slippage': 0.001           # 0.1% slippage
        }
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            DataFrame with indicators added
        """
        df = data.copy()
        
        # Bollinger Bands
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(
            df['close'].values,
            timeperiod=self.config['bb_period'],
            nbdevup=self.config['bb_std'],
            nbdevdn=self.config['bb_std'],
            matype=0
        )
        
        # RSI
        df['rsi'] = talib.RSI(df['close'].values, timeperiod=self.config['rsi_period'])
        
        # ATR for volatility-based stops
        df['atr'] = talib.ATR(
            df['high'].values,
            df['low'].values,
            df['close'].values,
            timeperiod=14
        )
        
        # Bollinger Band Width (volatility measure)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # Price position within bands (0 = lower, 1 = upper)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Volume indicators
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        return df
    
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Signal]:
        """
        Generate trading signals based on strategy rules
        
        Args:
            data: DataFrame with OHLCV and indicators
            symbol: Stock symbol
            
        Returns:
            List of trading signals
        """
        signals = []
        df = self.calculate_indicators(data)
        
        for i in range(self.config['bb_period'] + self.config['rsi_period'], len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i-1]
            
            # Skip if indicators are NaN
            if pd.isna(row['rsi']) or pd.isna(row['bb_lower']):
                continue
            
            # Volume filter
            if row['volume'] < self.config['min_volume']:
                continue
            
            # Price filter
            if row['close'] < self.config['min_price']:
                continue
            
            # BUY SIGNAL: Price touches lower band + RSI oversold
            if (row['close'] <= row['bb_lower'] and 
                row['rsi'] < self.config['rsi_oversold'] and
                symbol not in self.positions and
                len(self.positions) < self.config['max_positions']):
                
                position_size = self._calculate_position_size(
                    row['close'],
                    row['atr'],
                    self.config['initial_capital']
                )
                
                signals.append(Signal(
                    timestamp=row.name,
                    symbol=symbol,
                    action='buy',
                    price=row['close'],
                    confidence=min((self.config['rsi_oversold'] - row['rsi']) / self.config['rsi_oversold'], 1.0),
                    reason=f"Lower BB touch, RSI={row['rsi']:.1f}",
                    position_size=position_size
                ))
            
            # SELL SIGNAL: Price touches upper band + RSI overbought
            elif (row['close'] >= row['bb_upper'] and 
                  row['rsi'] > self.config['rsi_overbought'] and
                  symbol not in self.positions and
                  len(self.positions) < self.config['max_positions']):
                
                position_size = self._calculate_position_size(
                    row['close'],
                    row['atr'],
                    self.config['initial_capital']
                )
                
                signals.append(Signal(
                    timestamp=row.name,
                    symbol=symbol,
                    action='sell',  # Short position
                    price=row['close'],
                    confidence=min((row['rsi'] - self.config['rsi_overbought']) / (100 - self.config['rsi_overbought']), 1.0),
                    reason=f"Upper BB touch, RSI={row['rsi']:.1f}",
                    position_size=position_size
                ))
            
            # EXIT SIGNALS for existing positions
            if symbol in self.positions:
                position = self.positions[symbol]
                
                # Exit on mean reversion (price crosses middle band)
                if position['side'] == 'long' and row['close'] >= row['bb_middle']:
                    signals.append(Signal(
                        timestamp=row.name,
                        symbol=symbol,
                        action='close',
                        price=row['close'],
                        confidence=0.8,
                        reason="Mean reversion complete (long)",
                        position_size=position['size']
                    ))
                
                elif position['side'] == 'short' and row['close'] <= row['bb_middle']:
                    signals.append(Signal(
                        timestamp=row.name,
                        symbol=symbol,
                        action='close',
                        price=row['close'],
                        confidence=0.8,
                        reason="Mean reversion complete (short)",
                        position_size=position['size']
                    ))
                
                # Stop loss
                elif self._check_stop_loss(position, row['close']):
                    signals.append(Signal(
                        timestamp=row.name,
                        symbol=symbol,
                        action='close',
                        price=row['close'],
                        confidence=1.0,
                        reason="Stop loss triggered",
                        position_size=position['size']
                    ))
                
                # Take profit
                elif self._check_take_profit(position, row['close']):
                    signals.append(Signal(
                        timestamp=row.name,
                        symbol=symbol,
                        action='close',
                        price=row['close'],
                        confidence=1.0,
                        reason="Take profit triggered",
                        position_size=position['size']
                    ))
        
        return signals
    
    def _calculate_position_size(self, price: float, atr: float, capital: float) -> int:
        """
        Calculate position size using ATR-based risk management
        """
        # Risk amount per trade
        risk_amount = capital * self.config['position_size_pct']
        
        # Stop loss distance (ATR-based)
        stop_distance = atr * self.config['atr_multiplier']
        
        # Position size
        position_value = risk_amount / (stop_distance / price)
        shares = int(position_value / price)
        
        return max(shares, 1)
    
    def _check_stop_loss(self, position: Dict, current_price: float) -> bool:
        """Check if stop loss is triggered"""
        if position['side'] == 'long':
            return current_price <= position['stop_loss']
        else:  # short
            return current_price >= position['stop_loss']
    
    def _check_take_profit(self, position: Dict, current_price: float) -> bool:
        """Check if take profit is triggered"""
        if position['side'] == 'long':
            return current_price >= position['take_profit']
        else:  # short
            return current_price <= position['take_profit']
    
    def backtest(self, data: pd.DataFrame, symbol: str) -> Dict:
        """
        Run backtest on historical data
        
        Args:
            data: Historical OHLCV data
            symbol: Stock symbol
            
        Returns:
            Backtest results and metrics
        """
        df = self.calculate_indicators(data)
        signals = self.generate_signals(df, symbol)
        
        capital = self.config['initial_capital']
        trades = []
        equity = [capital]
        
        for signal in signals:
            if signal.action in ['buy', 'sell']:
                # Open position
                cost = signal.position_size * signal.price * (1 + self.config['slippage'] + self.config['commission'])
                
                if cost <= capital:
                    self.positions[symbol] = {
                        'side': 'long' if signal.action == 'buy' else 'short',
                        'entry_price': signal.price,
                        'size': signal.position_size,
                        'stop_loss': signal.price * (1 - self.config['stop_loss_pct']) if signal.action == 'buy' else signal.price * (1 + self.config['stop_loss_pct']),
                        'take_profit': signal.price * (1 + self.config['take_profit_pct']) if signal.action == 'buy' else signal.price * (1 - self.config['take_profit_pct']),
                        'entry_time': signal.timestamp
                    }
                    capital -= cost
            
            elif signal.action == 'close' and symbol in self.positions:
                # Close position
                position = self.positions[symbol]
                revenue = signal.position_size * signal.price * (1 - self.config['slippage'] - self.config['commission'])
                
                pnl = revenue - (position['size'] * position['entry_price'])
                capital += revenue
                
                trades.append({
                    'entry_time': position['entry_time'],
                    'exit_time': signal.timestamp,
                    'side': position['side'],
                    'entry_price': position['entry_price'],
                    'exit_price': signal.price,
                    'size': position['size'],
                    'pnl': pnl,
                    'pnl_pct': pnl / (position['size'] * position['entry_price']),
                    'reason': signal.reason
                })
                
                del self.positions[symbol]
            
            equity.append(capital)
        
        # Calculate metrics
        metrics = self._calculate_metrics(trades, equity)
        
        return {
            'trades': trades,
            'equity_curve': equity,
            'metrics': metrics,
            'final_capital': capital
        }
    
    def _calculate_metrics(self, trades: List[Dict], equity: List[float]) -> Dict:
        """
        Calculate performance metrics
        """
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'profit_factor': 0
            }
        
        # Win rate
        wins = [t for t in trades if t['pnl'] > 0]
        win_rate = len(wins) / len(trades)
        
        # Average return
        returns = [t['pnl_pct'] for t in trades]
        avg_return = np.mean(returns)
        
        # Sharpe ratio
        if len(returns) > 1:
            sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        else:
            sharpe = 0
        
        # Max drawdown
        equity_array = np.array(equity)
        cummax = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - cummax) / cummax
        max_drawdown = np.min(drawdown)
        
        # Profit factor
        gross_profit = sum(t['pnl'] for t in trades if t['pnl'] > 0)
        gross_loss = abs(sum(t['pnl'] for t in trades if t['pnl'] < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        return {
            'total_trades': len(trades),
            'win_rate': win_rate,
            'avg_return': avg_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'profit_factor': profit_factor,
            'total_return': (equity[-1] - equity[0]) / equity[0] if equity else 0
        }
```

## Expected Performance

### Backtest Results (2020-2024)
- **Annual Return**: 18.5%
- **Sharpe Ratio**: 1.42
- **Max Drawdown**: -12.3%
- **Win Rate**: 62%
- **Profit Factor**: 1.85
- **Average Trade**: +1.2%

### Market Conditions
**Works Best In:**
- Range-bound markets
- Low to medium volatility
- Liquid stocks with clear support/resistance

**Struggles In:**
- Strong trending markets
- High volatility periods
- Low liquidity conditions

### Risk Analysis
- **Maximum position risk**: 2% per trade
- **Portfolio heat**: Max 10% (5 positions × 2%)
- **Correlation risk**: Managed through sector diversification
- **Tail risk**: Protected by stop-losses

### Potential Improvements
1. Add regime detection to avoid trends
2. Implement dynamic position sizing
3. Include fundamental filters
4. Add correlation analysis for portfolio
5. Implement options hedging for tail risk
'''
        
        return strategy
    
    def _create_backtest_framework(self, strategy: str) -> str:
        """
        Erstellt Backtest-Framework für die Strategie
        """
        # Extract strategy class name from the strategy code
        import re
        class_match = re.search(r'class\s+(\w+)', strategy)
        class_name = class_match.group(1) if class_match else "Strategy"
        
        backtest_code = f'''
# Backtest Framework for {class_name}

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

def run_backtest(symbols, start_date, end_date):
    """Run strategy backtest on multiple symbols"""
    
    results = {{}}
    
    for symbol in symbols:
        # Download data
        data = yf.download(symbol, start=start_date, end=end_date)
        data.columns = data.columns.str.lower()
        
        # Initialize strategy
        strategy = {class_name}()
        
        # Run backtest
        result = strategy.backtest(data, symbol)
        results[symbol] = result
        
        # Print summary
        print(f"\n{{}}: {{}}".format(symbol, result['metrics']))
    
    return results

# Example usage
if __name__ == "__main__":
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']
    start_date = '2023-01-01'
    end_date = '2024-01-01'
    
    results = run_backtest(symbols, start_date, end_date)
    
    # Plot equity curves
    fig, axes = plt.subplots(len(symbols), 1, figsize=(12, 4*len(symbols)))
    for i, symbol in enumerate(symbols):
        axes[i].plot(results[symbol]['equity_curve'])
        axes[i].set_title(f'{{}} Equity Curve'.format(symbol))
        axes[i].set_xlabel('Trade Number')
        axes[i].set_ylabel('Capital')
    plt.tight_layout()
    plt.show()
'''
        
        return backtest_code
    
    def _generate_performance_metrics(self, strategy: str) -> Dict[str, Any]:
        """
        Generiert erwartete Performance-Metriken
        """
        # Mock metrics based on strategy type
        return {
            "expected_annual_return": "15-20%",
            "expected_sharpe_ratio": "1.2-1.5",
            "expected_max_drawdown": "10-15%",
            "expected_win_rate": "55-65%",
            "optimal_market_conditions": [
                "Range-bound markets",
                "Medium volatility",
                "High liquidity"
            ],
            "risk_factors": [
                "Trend breakouts",
                "Volatility spikes",
                "Liquidity crises",
                "Black swan events"
            ],
            "recommended_capital": "$50,000+",
            "recommended_timeframe": "15min - Daily",
            "recommended_markets": ["US Equities", "Major Forex Pairs"],
            "complexity_level": "Intermediate"
        }