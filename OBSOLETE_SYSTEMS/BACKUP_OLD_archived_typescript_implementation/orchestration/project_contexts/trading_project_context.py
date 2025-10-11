"""
Trading Project Context for KI_AutoAgent

This module provides trading-specific context for the stock_analyser project and other trading systems.
Contains detailed RON strategy specifications and Live/Backtest engine parity requirements.
"""

from typing import Dict, List, Any
from .base_project_context import BaseProjectContext, ProjectSpecification
import json

# Detailed RON Strategy Specification (moved from stock_analyser_context.py)
DETAILED_RON_STRATEGY = {
    "strategy_name": "RON Strategy",
    "strategy_description": "Reversal trading strategy using VWAP and Fibonacci retracements",
    
    "precise_rules": {
        "market_scan": {
            "time_window": "16:00-20:00 UTC (US After-Hours)",
            "chart_timeframe": "1-minute bars (M1)",
            "market_type": "US liquid stocks",
            "scan_criteria": "Stocks far from VWAP",
            "direction": "Both long and short trades allowed",
            "cutoff_time": "No new trades after 20:00 UTC"
        },
        
        "technical_setup": {
            "fibonacci_calculation": {
                "high": "Day's highest price (session high)",
                "low": "Day's lowest price (session low)", 
                "levels": ["0%", "23.6%", "38.2%", "50%", "61.8%", "78.6%", "100%"],
                "direction": "From day high to day low"
            },
            
            "vwap_requirement": {
                "condition": "VWAP must be ABOVE 50% Fibonacci retracement level",
                "applies_to": "Long trades only",
                "calculation": "Volume-weighted average price from session start"
            },
            
            "ema9_confirmation": {
                "period": "9 periods on 1-minute chart",
                "entry_condition": "Price closes ABOVE EMA9 on current 1-minute bar",
                "confirmation": "Next 1-minute bar makes NEW HIGH above previous bar's high"
            }
        },
        
        "entry_logic": {
            "long_entry_conditions": [
                "Time between 16:00-20:00 UTC",
                "VWAP > 50% Fibonacci retracement", 
                "Current 1min bar closes ABOVE EMA9",
                "NEXT 1min bar makes new high (higher than previous bar high)",
                "Sufficient space to 38.2% Fibonacci level for 1:1 CRV"
            ],
            
            "crv_calculation": {
                "stop_loss_distance": "Distance from entry to stop loss",
                "target_distance": "Distance from entry to target",
                "minimum_crv": "1:1 (target distance >= stop loss distance)",
                "space_requirement": "Must have space to 38.2% Fibonacci level"
            }
        },
        
        "exit_logic": {
            "take_profit_placement": "50% Fibonacci retracement OR VWAP (whichever is closer)",
            "stop_loss_placement": "Below entry level (exact calculation method needed)",
            "partial_exits": "Allowed at technical resistance levels",
            "forced_exit": "ALL positions closed at 21:59 UTC",
            "crv_minimum": "Overall CRV must remain >= 1:1"
        },
        
        "timing_precision": {
            "scan_frequency": "Every 1 minute during 16:00-20:00",
            "data_points": "OHLCV for each 1-minute bar",
            "decision_timing": "At close of each 1-minute bar",
            "execution_timing": "Beginning of next 1-minute bar"
        }
    },
    
    "implementation_requirements": {
        "file_structure": "Separate .py file for RON strategy implementation",
        "data_assumptions": "All data treated as LIVE data (no future leak)",
        "calculation_precision": "Use Decimal type for all financial calculations", 
        "error_handling": "Follow stock_analyser fallback policy strictly"
    }
}

# Stock Analyser Project Guidelines (moved from stock_analyser_context.py)
STOCK_ANALYSER_SHARED_INSTRUCTIONS = {
    "project_name": "stock_analyser",
    "development_guidelines": {
        "function_size": "Kleine Funktionsänderungen bei neuimplementierten Features",
        "code_style": "Kleinteilige Funktionen", 
        "attitude": "sei begeistert dabei",
        "environment": "das projekt ist in einem venv"
    },
    
    "trading_rules": {
        "data_policy": "Zukunftsvorhersagen gibt es nicht. Immer Live Daten annehmen",
        "testing_consistency": "Backtest Logik soll der Live Trading Logik 1:1 entsprechen",
        "yfinance_restriction": "yf ist B - nicht verwenden"
    },
    
    "fallback_policy": {
        "allowed": [
            "Retry with shorter duration",
            "Retry with delayed data", 
            "Alternative Abrufmethoden (gleiches Ergebnis)",
            "Zeitweise Wiederholungen bei Verbindungsproblemen"
        ],
        "forbidden": [
            "Return None/Empty DataFrame",
            "Partial data ohne Warnung",
            "Silent failures", 
            "Alternative Datenquellen (yfinance statt IB)",
            "Skip failed symbols"
        ],
        "principle": "Lieber crashen als falsches Verhalten"
    },
    
    "ron_strategy": {
        "trading_window": "16:00-20:00 Uhr",
        "chart_type": "M1 Chart",
        "indicators": ["VWAP", "EMA9", "Fibonacci Retracement"],
        "crv_requirement": "> 1:1",
        "file_structure": "je Strategie wird eine eigene py Datei erstellt"
    },
    
    "technical_stack": {
        "broker_api": "Interactive Brokers TWS API",
        "ui_framework": "Streamlit", 
        "caching": "Redis-based architecture",
        "data_types": "Use Decimal for financial calculations"
    }
}

# Engine Parity Requirements (moved from stock_analyser_context.py)
ENGINE_PARITY_REQUIREMENTS = {
    "critical_principle": "Backtest must function EXACTLY like Live trading",
    
    "data_handling": {
        "chart_data_loading": "All chart data can be pre-loaded for backtest",
        "decision_timing": "Decisions made minute by minute, iteratively",
        "no_future_leak": "Only use data available up to current minute",
        "live_simulation": "Backtest simulates live conditions exactly"
    },
    
    "engine_architecture": {
        "unified_engine": "Single engine for both Live and Backtest",
        "decoupled_design": "Engine separated from chart display",
        "result_flow": "Engine -> Results -> Chart annotations",
        "timing_difference": "Live: 1x/minute, Backtest: fast as possible but 1min increments"
    },
    
    "implementation_mandate": {
        "every_agent_must_understand": [
            "RON strategy rules EXACTLY as specified",
            "Live/Backtest parity is CRITICAL",
            "No future leak in backtest data",
            "Iterative minute-by-minute processing",
            "Engine-Chart decoupling architecture"
        ]
    },
    
    "ron_strategy_precision": DETAILED_RON_STRATEGY,
    
    "quality_gates_addition": {
        "engine_parity_check": "Verify Live and Backtest use same logic",
        "future_leak_check": "Ensure no forward-looking data used",
        "timing_precision_check": "Verify minute-by-minute processing",
        "strategy_accuracy_check": "RON rules implemented exactly as specified"
    }
}


class TradingProjectContext(BaseProjectContext):
    """Trading-specific project context for stock_analyser and other trading systems"""
    
    def __init__(self, project_name: str = "trading_system"):
        super().__init__(project_name)
    
    def get_domain_instructions(self) -> str:
        """Return trading-specific instructions for agents"""
        return f"""
TRADING SYSTEM DEVELOPMENT INSTRUCTIONS:

PROJECT: {self.project_name}

1. TRADING DOMAIN KNOWLEDGE:
{json.dumps(STOCK_ANALYSER_SHARED_INSTRUCTIONS, indent=2)}

2. RON STRATEGY PRECISION:
{json.dumps(DETAILED_RON_STRATEGY, indent=2)}

3. LIVE/BACKTEST PARITY REQUIREMENTS:
{json.dumps(ENGINE_PARITY_REQUIREMENTS, indent=2)}

CRITICAL IMPLEMENTATION RULES:
- NO FUTURE DATA LEAK in backtests
- Live and Backtest engines must use IDENTICAL logic
- Process minute-by-minute iteratively
- Use Decimal precision for financial calculations
- Follow strict fallback policy (crash rather than silent fail)
- Separate .py file for each trading strategy
- Redis-based caching architecture
- Interactive Brokers TWS API integration
- Streamlit UI framework

AGENT-SPECIFIC ENHANCEMENTS:
{json.dumps(self.get_agent_enhancement_instructions(), indent=2)}
"""
    
    def get_quality_gates(self) -> List[str]:
        """Return trading-specific quality gate class names"""
        return [
            "TradingSystemQualityGate",
            "RONStrategyQualityGate", 
            "EngineParityQualityGate",
            "SecurityQualityGate",  # Financial systems need security
            "PerformanceQualityGate"  # Trading systems need performance
        ]
    
    def get_project_specifics(self) -> ProjectSpecification:
        """Return trading project specifications"""
        return ProjectSpecification(
            name=self.project_name,
            domain="Financial Trading Systems",
            programming_languages=["Python"],
            frameworks=["Streamlit", "Redis", "Interactive Brokers API", "pandas", "numpy"],
            architecture_patterns=[
                "Event-Driven Architecture",
                "Engine-Chart Decoupling",
                "Live/Backtest Parity",
                "Redis Caching Layer",
                "Minute-by-Minute Processing"
            ],
            special_requirements=[
                "No future data leak",
                "Decimal precision calculations", 
                "RON strategy mathematical accuracy",
                "Real-time data processing",
                "Risk management (CRV >= 1:1)",
                "After-hours trading (16:00-20:00 UTC)"
            ],
            compliance_standards=[
                "Trading system fallback policy",
                "Financial calculation accuracy",
                "Data integrity requirements",
                "Real-time processing standards"
            ]
        )
    
    def get_agent_enhancement_instructions(self) -> Dict[str, str]:
        """Return agent-specific enhancements for trading domain"""
        return {
            "ResearchBot": """
TRADING RESEARCH FOCUS:
- Interactive Brokers API documentation and best practices
- Existing stock_analyser codebase patterns
- VWAP, EMA9, and Fibonacci calculation examples
- Live/Backtest engine architecture patterns
- Trading system error handling and fallback strategies
- Redis caching patterns for financial data
- Streamlit financial dashboard examples
""",
            
            "ArchitectGPT": """
TRADING ARCHITECTURE FOCUS:
- Design unified engine for Live/Backtest parity
- Plan engine-chart decoupling architecture
- Design RON strategy implementation structure
- Consider Redis caching integration patterns
- Plan Streamlit UI integration for trading
- Ensure minute-by-minute processing architecture
- Design risk management and CRV calculation systems
""",
            
            "CodeSmithClaude": """
TRADING IMPLEMENTATION FOCUS:
- Implement RON strategy EXACTLY as specified
- Ensure Live/Backtest use IDENTICAL logic
- Process minute-by-minute iteratively (no future leak)
- Use Decimal type for ALL financial calculations
- Follow fallback policy strictly (crash vs silent fail)
- Create separate .py files for each strategy
- Implement comprehensive error handling
- Integrate with Interactive Brokers TWS API
""",
            
            "ReviewerGPT": """
TRADING REVIEW FOCUS:
- Verify RON strategy rules implemented exactly
- Validate Live/Backtest parity (same logic)
- Check for future data leak violations
- Confirm Decimal precision usage
- Validate CRV calculations (>= 1:1)
- Check fallback policy adherence
- Verify trading hours restrictions
- Review engine-chart decoupling
""",
            
            "FixerBot": """
TRADING FIXES FOCUS:
- Maintain RON strategy mathematical precision
- Preserve Live/Backtest parity during fixes
- Ensure no regression in trading logic
- Fix without introducing future data leaks
- Maintain Decimal precision calculations
- Follow stock_analyser coding standards
""",
            
            "TradeStrat": """
TRADING STRATEGY FOCUS:
- Implement RON strategy logic precisely
- Ensure proper risk management (CRV >= 1:1)
- Implement position sizing calculations
- Add stop loss and take profit logic
- Follow trading hours restrictions (16:00-20:00)
- Implement VWAP, EMA9, Fibonacci calculations
""",
            
            "DocuBot": """
TRADING DOCUMENTATION FOCUS:
- Document RON strategy implementation details
- Explain Live/Backtest parity architecture
- Update CLAUDE.md with trading patterns
- Document financial calculation precision
- Create API interface documentation
- Document risk management procedures
"""
        }
    
    def get_iteration_limits(self) -> Dict[str, int]:
        """Trading systems may need more iterations due to complexity"""
        return {
            "max_iterations": 15,  # More iterations for complex trading logic
            "complexity_boost_threshold": 10,
            "quality_gate_failures_limit": 5  # Financial accuracy is critical
        }