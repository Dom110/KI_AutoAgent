"""
Trading System Development Workflow
Specialized workflow for financial trading system development
"""

from typing import Dict, List, Any
from datetime import datetime
import logging

from .base_workflow import BaseWorkflow
from ..shared_context import SharedContext

logger = logging.getLogger(__name__)

class TradingSystemWorkflow(BaseWorkflow):
    """
    Specialized workflow for developing financial trading systems
    Includes financial-specific validation, backtesting, and risk management
    """
    
    def __init__(self, name: str = "Trading System Workflow"):
        super().__init__(name)
        self.workflow_steps = [
            "trading_requirements_analysis",
            "strategy_design",
            "risk_management_design", 
            "backtesting_framework_setup",
            "strategy_implementation",
            "backtesting_execution",
            "performance_analysis",
            "risk_validation",
            "paper_trading_setup",
            "live_trading_preparation",
            "compliance_validation",
            "deployment_monitoring"
        ]
    
    def get_workflow_steps(self) -> List[str]:
        """Return trading system specific workflow steps"""
        return self.workflow_steps
    
    def get_step_agents(self, step: str) -> List[str]:
        """Map trading workflow steps to specialized agents"""
        step_agent_mapping = {
            "trading_requirements_analysis": ["TradeStrat", "ResearchBot"],
            "strategy_design": ["TradeStrat", "ArchitectGPT"],
            "risk_management_design": ["TradeStrat", "ArchitectGPT"],
            "backtesting_framework_setup": ["CodeSmithClaude", "TradeStrat"],
            "strategy_implementation": ["CodeSmithClaude", "TradeStrat"],
            "backtesting_execution": ["TradeStrat", "CodeSmithClaude"],
            "performance_analysis": ["TradeStrat", "ResearchBot"],
            "risk_validation": ["TradeStrat", "ReviewerGPT"],
            "paper_trading_setup": ["CodeSmithClaude", "TradeStrat"],
            "live_trading_preparation": ["TradeStrat", "ArchitectGPT"],
            "compliance_validation": ["ReviewerGPT", "TradeStrat"],
            "deployment_monitoring": ["CodeSmithClaude", "ArchitectGPT"]
        }
        return step_agent_mapping.get(step, ["TradeStrat"])
    
    def get_step_instructions(self, step: str, context: SharedContext) -> str:
        """Provide trading-specific instructions for each workflow step"""
        
        base_context = f"""
TRADING PROJECT CONTEXT: {getattr(context, 'user_request', 'Trading System Development')}
CURRENT STEP: {step}
ITERATION: {getattr(context, 'current_iteration', 0) + 1}

IMPORTANT TRADING REQUIREMENTS:
- All monetary calculations MUST use Decimal for precision
- Risk management is MANDATORY in all components
- Backtesting must simulate real market conditions
- Live trading requires extensive validation
- Compliance with financial regulations required

"""
        
        step_instructions = {
            "trading_requirements_analysis": """
TRADING REQUIREMENTS ANALYSIS:

Analyze and define comprehensive trading system requirements:

1. TRADING STRATEGY REQUIREMENTS:
   - Strategy type (momentum, mean reversion, arbitrage, etc.)
   - Market focus (stocks, forex, crypto, commodities)
   - Timeframes (scalping, day trading, swing, position)
   - Entry/exit signal definitions
   - Position sizing methodology

2. RISK MANAGEMENT REQUIREMENTS:
   - Maximum drawdown limits
   - Position size limits
   - Stop-loss strategies
   - Portfolio exposure limits
   - Risk-reward ratios

3. PERFORMANCE REQUIREMENTS:
   - Target returns
   - Maximum acceptable risk
   - Sharpe ratio expectations
   - Latency requirements
   - Execution speed needs

4. DATA REQUIREMENTS:
   - Historical data depth
   - Real-time data feeds
   - Alternative data sources
   - Data quality standards
   - Backup data sources

5. REGULATORY REQUIREMENTS:
   - Jurisdiction compliance
   - Reporting requirements
   - Audit trail needs
   - Documentation standards

DELIVERABLES:
- Trading requirements specification
- Risk management framework
- Performance targets
- Data requirements document
- Regulatory compliance checklist
""",

            "strategy_design": """
TRADING STRATEGY DESIGN:

Design the core trading strategy and algorithm:

1. STRATEGY LOGIC:
   - Signal generation methodology
   - Entry conditions (price, volume, indicators)
   - Exit conditions (profit targets, stop losses)
   - Position sizing algorithm
   - Timing considerations

2. TECHNICAL INDICATORS:
   - Primary indicators selection
   - Secondary confirmation indicators
   - Custom indicator development
   - Indicator parameter optimization
   - Multi-timeframe analysis

3. MARKET CONDITIONS:
   - Bull market adaptations
   - Bear market adjustments
   - Sideways market handling
   - Volatility regime detection
   - Market session considerations

4. BACKTESTING DESIGN:
   - Historical testing methodology
   - Out-of-sample validation
   - Walk-forward analysis
   - Monte Carlo simulation
   - Stress testing scenarios

DELIVERABLES:
- Strategy specification document
- Pseudocode for algorithm
- Indicator definitions
- Backtesting methodology
- Strategy flowcharts
""",

            "risk_management_design": """
RISK MANAGEMENT SYSTEM DESIGN:

Design comprehensive risk management framework:

1. POSITION RISK MANAGEMENT:
   - Position sizing methods (fixed, percentage, volatility-based)
   - Maximum position size limits
   - Correlation-based position limits
   - Sector/asset class limits
   - Single-name concentration limits

2. PORTFOLIO RISK MANAGEMENT:
   - Value at Risk (VaR) calculations
   - Expected Shortfall (CVaR)
   - Portfolio beta management
   - Diversification requirements
   - Leverage constraints

3. OPERATIONAL RISK CONTROLS:
   - Order validation checks
   - Price reasonability checks
   - Volume validation
   - Connection monitoring
   - Fail-safe mechanisms

4. DYNAMIC RISK ADJUSTMENT:
   - Volatility-based sizing
   - Drawdown-triggered scaling
   - Market condition adjustments
   - Real-time risk monitoring
   - Automatic position reduction

DELIVERABLES:
- Risk management specification
- Risk calculation algorithms
- Risk monitoring framework
- Emergency procedures
- Risk reporting templates
""",

            "backtesting_framework_setup": """
BACKTESTING FRAMEWORK SETUP:

Establish robust backtesting infrastructure:

1. DATA INFRASTRUCTURE:
   - Historical data ingestion
   - Data cleaning and validation
   - Corporate actions handling
   - Survivorship bias elimination
   - Data quality checks

2. SIMULATION ENGINE:
   - Order execution simulation
   - Slippage and commission modeling
   - Market impact simulation
   - Liquidity constraints
   - Realistic fill models

3. PERFORMANCE METRICS:
   - Return calculations
   - Risk metrics (Sharpe, Sortino, Calmar)
   - Drawdown analysis
   - Win/loss statistics
   - Trade analysis

4. VALIDATION FRAMEWORK:
   - Cross-validation methods
   - Out-of-sample testing
   - Parameter sensitivity analysis
   - Overfitting detection
   - Statistical significance testing

DELIVERABLES:
- Backtesting engine code
- Data pipeline implementation
- Performance calculation modules
- Validation test suite
- Reporting framework
""",

            "strategy_implementation": """
STRATEGY IMPLEMENTATION:

Implement the trading strategy in production-ready code:

1. CORE STRATEGY CODE:
   - Signal generation algorithms
   - Entry/exit logic implementation
   - Position sizing calculations
   - Risk checks integration
   - Error handling and logging

2. DATA HANDLING:
   - Real-time data processing
   - Historical data access
   - Data validation routines
   - Missing data handling
   - Data normalization

3. ORDER MANAGEMENT:
   - Order creation and validation
   - Order execution monitoring
   - Fill confirmation handling
   - Order modification logic
   - Cancellation procedures

4. STATE MANAGEMENT:
   - Position tracking
   - P&L calculations
   - Portfolio state maintenance
   - Strategy state persistence
   - Recovery procedures

DELIVERABLES:
- Production strategy code
- Unit tests for all components
- Integration tests
- Configuration management
- Error handling documentation
""",

            "backtesting_execution": """
BACKTESTING EXECUTION:

Execute comprehensive backtesting of the trading strategy:

1. HISTORICAL BACKTESTING:
   - Full historical period testing
   - Multiple timeframe validation
   - Different market conditions
   - Various starting dates
   - Parameter sensitivity analysis

2. OUT-OF-SAMPLE TESTING:
   - Reserved test data validation
   - Forward testing simulation
   - Walk-forward optimization
   - Cross-validation results
   - Robustness verification

3. STRESS TESTING:
   - Market crash scenarios
   - High volatility periods
   - Low liquidity conditions
   - Extended drawdown periods
   - Black swan events

4. MONTE CARLO SIMULATION:
   - Random order shuffle testing
   - Bootstrap resampling
   - Confidence intervals
   - Worst-case scenarios
   - Distribution analysis

DELIVERABLES:
- Comprehensive backtest results
- Performance statistics
- Risk analysis report
- Sensitivity analysis
- Stress test outcomes
""",

            "performance_analysis": """
PERFORMANCE ANALYSIS:

Analyze strategy performance and identify improvements:

1. RETURN ANALYSIS:
   - Absolute and relative returns
   - Risk-adjusted returns
   - Benchmark comparisons
   - Alpha and beta analysis
   - Attribution analysis

2. RISK ANALYSIS:
   - Volatility analysis
   - Maximum drawdown periods
   - Risk concentration analysis
   - Tail risk assessment
   - Correlation analysis

3. TRADE ANALYSIS:
   - Win/loss ratios
   - Average trade statistics
   - Trade duration analysis
   - Profit factor calculations
   - Trade clustering effects

4. IMPROVEMENT IDENTIFICATION:
   - Performance bottlenecks
   - Risk hotspots
   - Optimization opportunities
   - Parameter refinement
   - Strategy enhancements

DELIVERABLES:
- Performance analysis report
- Risk assessment document
- Trade statistics summary
- Improvement recommendations
- Optimization suggestions
""",

            "risk_validation": """
RISK VALIDATION:

Validate risk management effectiveness:

1. RISK MODEL VALIDATION:
   - VaR model backtesting
   - Risk model accuracy
   - Stress test validation
   - Correlation model testing
   - Volatility forecast validation

2. POSITION LIMIT TESTING:
   - Maximum position validation
   - Concentration limit testing
   - Correlation limit effectiveness
   - Dynamic limit adjustments
   - Override mechanisms

3. DRAWDOWN ANALYSIS:
   - Maximum drawdown validation
   - Recovery time analysis
   - Drawdown frequency
   - Risk-adjusted drawdowns
   - Sequential loss impact

4. SCENARIO TESTING:
   - Crisis scenario simulation
   - Market regime changes
   - Liquidity crisis testing
   - Operational failure scenarios
   - Extreme event validation

DELIVERABLES:
- Risk validation report
- Model accuracy metrics
- Stress test results
- Limit effectiveness analysis
- Risk improvement plan
""",

            "paper_trading_setup": """
PAPER TRADING SETUP:

Establish paper trading environment for strategy validation:

1. SIMULATION ENVIRONMENT:
   - Real-time market data feed
   - Live order simulation
   - Realistic execution modeling
   - Commission and slippage simulation
   - Market hours simulation

2. MONITORING SYSTEM:
   - Real-time P&L tracking
   - Position monitoring
   - Risk metric calculation
   - Performance measurement
   - Alert system setup

3. VALIDATION FRAMEWORK:
   - Strategy behavior validation
   - Risk control verification
   - Order execution testing
   - Data feed reliability
   - System stability testing

4. REPORTING SYSTEM:
   - Daily performance reports
   - Risk management reports
   - Trade execution analysis
   - System health monitoring
   - Compliance reporting

DELIVERABLES:
- Paper trading system
- Monitoring dashboard
- Validation test results
- Performance tracking system
- Alert and reporting framework
""",

            "live_trading_preparation": """
LIVE TRADING PREPARATION:

Prepare system for live trading deployment:

1. PRODUCTION ENVIRONMENT:
   - Live broker integration
   - Real-time data connections
   - Order routing setup
   - Backup systems configuration
   - Disaster recovery procedures

2. OPERATIONAL PROCEDURES:
   - Daily startup procedures
   - Market open procedures
   - End-of-day procedures
   - Emergency shutdown
   - System maintenance

3. MONITORING AND ALERTS:
   - Real-time system monitoring
   - Performance alert thresholds
   - Risk alert configuration
   - System failure alerts
   - Escalation procedures

4. SAFETY MECHANISMS:
   - Kill switches
   - Position limit enforcement
   - Risk limit monitoring
   - Automatic system shutdown
   - Manual override procedures

DELIVERABLES:
- Production deployment package
- Operational runbooks
- Monitoring system configuration
- Emergency procedures
- Safety mechanism validation
""",

            "compliance_validation": """
COMPLIANCE VALIDATION:

Ensure regulatory compliance and audit readiness:

1. REGULATORY REQUIREMENTS:
   - Registration requirements
   - Reporting obligations
   - Record keeping standards
   - Best execution compliance
   - Market making rules

2. AUDIT TRAIL:
   - Complete trade logging
   - Decision audit trail
   - System change tracking
   - Performance reporting
   - Risk management evidence

3. DOCUMENTATION:
   - Strategy documentation
   - Risk management procedures
   - Operational procedures
   - System architecture
   - Compliance policies

4. REPORTING SYSTEM:
   - Regulatory reporting
   - Internal reporting
   - Client reporting
   - Risk reporting
   - Performance reporting

DELIVERABLES:
- Compliance validation report
- Audit trail system
- Documentation package
- Reporting system setup
- Regulatory submission preparation
""",

            "deployment_monitoring": """
DEPLOYMENT MONITORING:

Establish comprehensive monitoring for live trading:

1. SYSTEM MONITORING:
   - Server health monitoring
   - Data feed monitoring
   - Order execution monitoring
   - Network connectivity
   - Database performance

2. STRATEGY MONITORING:
   - Real-time P&L tracking
   - Position monitoring
   - Risk metric calculation
   - Performance attribution
   - Strategy drift detection

3. MARKET MONITORING:
   - Market condition assessment
   - Volatility monitoring
   - Liquidity assessment
   - News impact monitoring
   - Regime change detection

4. ALERTING SYSTEM:
   - System failure alerts
   - Performance deviation alerts
   - Risk threshold breaches
   - Market condition changes
   - Manual intervention needs

DELIVERABLES:
- Monitoring system implementation
- Alert configuration
- Dashboard setup
- Reporting automation
- Maintenance procedures
"""
        }
        
        instruction = step_instructions.get(step, f"Execute {step} with focus on trading system requirements.")
        return base_context + instruction
    
    def validate_step_completion(self, step: str, step_output: Dict[str, Any]) -> bool:
        """Validate trading workflow step completion with financial-specific criteria"""
        
        if not step_output or 'content' not in step_output:
            return False
        
        content = step_output['content'].lower()
        
        # Trading-specific validation criteria
        validation_criteria = {
            "trading_requirements_analysis": [
                "risk", "return", "drawdown", "strategy", "requirements"
            ],
            "strategy_design": [
                "signal", "entry", "exit", "indicator", "backtest"
            ],
            "risk_management_design": [
                "risk", "position", "limit", "var", "drawdown"
            ],
            "backtesting_framework_setup": [
                "backtest", "historical", "simulation", "performance", "data"
            ],
            "strategy_implementation": [
                "implementation", "code", "algorithm", "decimal", "error"
            ],
            "backtesting_execution": [
                "backtest", "result", "performance", "sharpe", "return"
            ],
            "performance_analysis": [
                "performance", "return", "risk", "analysis", "sharpe"
            ],
            "risk_validation": [
                "risk", "validation", "var", "stress", "scenario"
            ],
            "paper_trading_setup": [
                "paper", "simulation", "real-time", "monitoring", "validation"
            ],
            "live_trading_preparation": [
                "live", "production", "broker", "monitoring", "safety"
            ],
            "compliance_validation": [
                "compliance", "regulatory", "audit", "documentation", "reporting"
            ],
            "deployment_monitoring": [
                "monitoring", "deployment", "alert", "performance", "system"
            ]
        }
        
        criteria = validation_criteria.get(step, [])
        matches = sum(1 for criterion in criteria if criterion in content)
        
        # Require higher validation threshold for trading systems
        return matches >= len(criteria) * 0.6
    
    def get_workflow_description(self) -> str:
        """Describe the trading system workflow"""
        return """
Trading System Development Workflow

This specialized workflow implements a comprehensive development lifecycle for financial trading systems:

1. Trading Requirements Analysis - Define strategy, risk, and performance requirements
2. Strategy Design - Design core trading algorithm and signals
3. Risk Management Design - Establish comprehensive risk controls
4. Backtesting Framework Setup - Build robust testing infrastructure
5. Strategy Implementation - Code the trading strategy
6. Backtesting Execution - Comprehensive historical validation
7. Performance Analysis - Analyze returns, risks, and improvements
8. Risk Validation - Validate risk management effectiveness
9. Paper Trading Setup - Establish simulation environment
10. Live Trading Preparation - Prepare for production deployment
11. Compliance Validation - Ensure regulatory compliance
12. Deployment Monitoring - Establish live trading monitoring

This workflow emphasizes risk management, regulatory compliance, and thorough validation
before live trading deployment. Each step includes financial industry best practices
and specialized validation criteria for trading systems.
"""

    def get_success_criteria(self) -> Dict[str, List[str]]:
        """Define success criteria for trading workflow"""
        return {
            "trading_requirements_analysis": [
                "Trading strategy clearly defined",
                "Risk management requirements specified",
                "Performance targets established",
                "Data requirements documented",
                "Regulatory requirements identified"
            ],
            "strategy_design": [
                "Entry/exit signals defined",
                "Position sizing methodology specified",
                "Technical indicators selected",
                "Backtesting approach designed",
                "Strategy logic documented"
            ],
            "risk_management_design": [
                "Position limits established",
                "Portfolio risk controls defined",
                "VaR methodology specified",
                "Dynamic risk adjustments designed",
                "Emergency procedures documented"
            ],
            "backtesting_framework_setup": [
                "Historical data pipeline established",
                "Execution simulation implemented",
                "Performance metrics calculated",
                "Validation framework created",
                "Reporting system functional"
            ],
            "strategy_implementation": [
                "Strategy algorithm implemented",
                "Risk controls integrated",
                "Order management functional",
                "State management implemented",
                "Error handling comprehensive"
            ],
            "backtesting_execution": [
                "Historical backtesting completed",
                "Out-of-sample testing performed",
                "Stress testing executed",
                "Monte Carlo analysis conducted",
                "Results statistically significant"
            ],
            "performance_analysis": [
                "Return analysis completed",
                "Risk metrics calculated",
                "Trade statistics analyzed",
                "Benchmark comparisons performed",
                "Improvement opportunities identified"
            ],
            "risk_validation": [
                "Risk models validated",
                "Position limits tested",
                "Drawdown analysis completed",
                "Scenario testing performed",
                "Risk controls verified"
            ],
            "paper_trading_setup": [
                "Simulation environment operational",
                "Real-time monitoring functional",
                "Validation framework active",
                "Reporting system operational",
                "Performance tracking accurate"
            ],
            "live_trading_preparation": [
                "Production environment ready",
                "Broker integration tested",
                "Monitoring systems operational",
                "Safety mechanisms validated",
                "Operational procedures documented"
            ],
            "compliance_validation": [
                "Regulatory requirements met",
                "Audit trail complete",
                "Documentation comprehensive",
                "Reporting system compliant",
                "Compliance procedures established"
            ],
            "deployment_monitoring": [
                "System monitoring operational",
                "Strategy monitoring active",
                "Market monitoring functional",
                "Alert system configured",
                "Maintenance procedures established"
            ]
        }