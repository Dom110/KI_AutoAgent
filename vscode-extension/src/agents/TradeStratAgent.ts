/**
 * TradeStrat - Trading Strategy Expert
 * Powered by Claude 3.5 Sonnet for trading strategy development and analysis
 */
import * as vscode from 'vscode';
import { ChatAgent } from './base/ChatAgent';
import { AgentConfig, TaskRequest, TaskResult, WorkflowStep } from '../types';
import { VSCodeMasterDispatcher } from '../core/VSCodeMasterDispatcher';
import { AnthropicService } from '../utils/AnthropicService';

export class TradeStratAgent extends ChatAgent {
    private anthropicService: AnthropicService;

    constructor(context: vscode.ExtensionContext, dispatcher: VSCodeMasterDispatcher) {
        const config: AgentConfig = {
            participantId: 'ki-autoagent.tradestrat',
            name: 'tradestrat',
            fullName: 'TradeStrat',
            description: 'Trading Strategy Expert powered by Claude 3.5 Sonnet',
            model: 'claude-3.5-sonnet',
            capabilities: [
                'Trading Strategy Development',
                'RON Strategy Implementation',
                'Backtesting Frameworks',
                'Risk Management',
                'Portfolio Optimization',
                'Market Analysis'
            ],
            commands: [
                { name: 'strategy', description: 'Develop and implement trading strategies', handler: 'handleStrategyCommand' },
                { name: 'backtest', description: 'Create backtesting and validation systems', handler: 'handleBacktestCommand' },
                { name: 'risk', description: 'Implement risk management and portfolio optimization', handler: 'handleRiskCommand' }
            ]
        };

        super(config, context, dispatcher);
        this.anthropicService = new AnthropicService();
    }

    protected async handleRequest(
        request: vscode.ChatRequest,
        context: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
        if (!this.validateApiConfig()) {
            stream.markdown('❌ Anthropic API key not configured. Please set it in VS Code settings.');
            return;
        }

        const command = request.command;
        const prompt = request.prompt;

        this.log(`Processing ${command ? `/${command}` : 'general'} trading request: ${prompt.substring(0, 100)}...`);

        if (command) {
            await this.handleCommand(command, prompt, stream, token);
        } else {
            await this.handleGeneralTradingRequest(prompt, stream, token);
        }
    }

    protected async processWorkflowStep(
        step: WorkflowStep,
        request: TaskRequest,
        previousResults: TaskResult[]
    ): Promise<TaskResult> {
        
        const context = await this.getWorkspaceContext();
        
        let systemPrompt = '';
        let userPrompt = '';

        switch (step.id) {
            case 'strategy_design':
                systemPrompt = this.getStrategyDesignSystemPrompt();
                userPrompt = `Design a trading strategy for: ${request.prompt}\n\nWorkspace Context:\n${context}`;
                break;
                
            case 'backtest':
                systemPrompt = this.getBacktestSystemPrompt();
                userPrompt = `Create backtesting framework for: ${request.prompt}\n\nStrategy Design:\n${this.extractPreviousContent(previousResults)}`;
                break;
                
            case 'risk_analysis':
                systemPrompt = this.getRiskAnalysisSystemPrompt();
                userPrompt = `Analyze risk management for: ${request.prompt}\n\nContext:\n${context}`;
                break;
                
            case 'strategy_validation':
                systemPrompt = this.getValidationSystemPrompt();
                userPrompt = `Validate trading strategy: ${request.prompt}\n\nImplementation:\n${this.extractPreviousContent(previousResults)}`;
                break;
                
            default:
                systemPrompt = this.getGeneralSystemPrompt();
                userPrompt = `${request.prompt}\n\nContext:\n${context}`;
        }

        try {
            const response = await this.anthropicService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);

            return {
                status: 'success',
                content: response,
                metadata: { 
                    step: step.id,
                    agent: 'tradestrat',
                    model: 'claude-3.5-sonnet'
                }
            };

        } catch (error) {
            throw new Error(`Failed to process ${step.id}: ${(error as any).message}`);
        }
    }

    // Command Handlers

    private async handleStrategyCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
        stream.progress('📈 Developing trading strategy...');
        
        const context = await this.getWorkspaceContext();
        const systemPrompt = this.getStrategyDesignSystemPrompt();
        const userPrompt = `Develop a comprehensive trading strategy for: ${prompt}\n\nWorkspace Context:\n${context}`;

        try {
            const response = await this.anthropicService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);

            stream.markdown(response);

            // Extract strategy components for implementation
            const pythonCode = this.extractPythonCode(response);
            if (pythonCode) {
                this.createActionButton(
                    '⚡ Implement Strategy',
                    'ki-autoagent.createFile',
                    ['strategy.py', pythonCode],
                    stream
                );
            }

            // Offer backtesting
            this.createActionButton(
                '🧪 Create Backtest',
                'ki-autoagent.createBacktest',
                [prompt, response],
                stream
            );

            // Offer risk analysis
            this.createActionButton(
                '⚠️ Analyze Risks',
                'ki-autoagent.analyzeRisks',
                [prompt, response],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ Error developing strategy: ${(error as any).message}`);
        }
    }

    private async handleBacktestCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
        stream.progress('🧪 Creating backtesting framework...');
        
        const context = await this.getWorkspaceContext();
        const systemPrompt = this.getBacktestSystemPrompt();
        const userPrompt = `Create a comprehensive backtesting framework for: ${prompt}\n\nWorkspace Context:\n${context}`;

        try {
            const response = await this.anthropicService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);

            stream.markdown(response);

            // Extract backtesting code
            const backtestCode = this.extractPythonCode(response);
            if (backtestCode) {
                this.createActionButton(
                    '📊 Create Backtest Framework',
                    'ki-autoagent.createFile',
                    ['backtest_engine.py', backtestCode],
                    stream
                );
            }

            // Offer to create test data
            this.createActionButton(
                '📈 Generate Test Data',
                'ki-autoagent.generateTestData',
                [prompt],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ Error creating backtesting framework: ${(error as any).message}`);
        }
    }

    private async handleRiskCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
        stream.progress('⚠️ Implementing risk management...');
        
        const context = await this.getWorkspaceContext();
        const systemPrompt = this.getRiskManagementSystemPrompt();
        const userPrompt = `Implement comprehensive risk management for: ${prompt}\n\nWorkspace Context:\n${context}`;

        try {
            const response = await this.anthropicService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);

            stream.markdown(response);

            // Extract risk management code
            const riskCode = this.extractPythonCode(response);
            if (riskCode) {
                this.createActionButton(
                    '🛡️ Implement Risk Management',
                    'ki-autoagent.createFile',
                    ['risk_manager.py', riskCode],
                    stream
                );
            }

            // Offer portfolio optimization
            this.createActionButton(
                '📊 Optimize Portfolio',
                'ki-autoagent.optimizePortfolio',
                [prompt, response],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ Error implementing risk management: ${(error as any).message}`);
        }
    }

    private async handleGeneralTradingRequest(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
        stream.progress('💹 Processing trading request...');
        
        const context = await this.getWorkspaceContext();
        const systemPrompt = this.getGeneralSystemPrompt();
        const userPrompt = `${prompt}\n\nWorkspace Context:\n${context}`;

        try {
            const response = await this.anthropicService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);

            stream.markdown(response);

            // Detect if this is RON strategy related
            if (prompt.toLowerCase().includes('ron') || response.toLowerCase().includes('ron strategy')) {
                this.createActionButton(
                    '🎯 Implement RON Strategy',
                    'ki-autoagent.implementRON',
                    [response],
                    stream
                );
            }

            // Auto-detect code for implementation
            const tradingCode = this.extractPythonCode(response);
            if (tradingCode) {
                this.createActionButton(
                    '⚡ Implement Code',
                    'ki-autoagent.createFile',
                    ['trading_implementation.py', tradingCode],
                    stream
                );
            }

        } catch (error) {
            stream.markdown(`❌ Error processing trading request: ${(error as any).message}`);
        }
    }

    // System Prompts

    private getGeneralSystemPrompt(): string {
        return `You are TradeStrat, an expert trading strategy developer and quantitative analyst. You specialize in:

- Trading strategy design and implementation
- Algorithmic trading systems
- Risk management and portfolio optimization
- Backtesting and performance analysis
- Market microstructure and execution
- RON (Reversal of Numbers) strategy implementation
- Python-based trading systems (pandas, numpy, streamlit, yfinance)

Key principles:
1. Always prioritize risk management
2. Implement robust backtesting before live trading
3. Focus on statistical significance and edge detection
4. Consider market conditions and regime changes
5. Provide clear performance metrics and validation

Format your responses with detailed explanations, working code, and practical implementation guidance.`;
    }

    private getStrategyDesignSystemPrompt(): string {
        return `You are TradeStrat designing a comprehensive trading strategy. Structure your response as:

## Trading Strategy Design

### 1. Strategy Overview
- Strategy name and concept
- Market conditions and timeframes
- Expected holding periods
- Target assets/markets

### 2. Entry Rules
- Precise entry conditions
- Technical indicators required
- Fundamental filters (if any)
- Signal confirmation methods

### 3. Exit Rules
- Profit-taking strategies
- Stop-loss implementation
- Time-based exits
- Market condition exits

### 4. Risk Management
- Position sizing methodology
- Maximum drawdown limits
- Correlation and diversification
- Portfolio-level risk controls

### 5. Implementation Details
- Required data sources
- Calculation methodology
- Code structure and modules
- Performance monitoring

### 6. Backtesting Framework
- Historical data requirements
- Performance metrics to track
- Stress testing scenarios
- Out-of-sample validation

Provide complete Python implementation with pandas/numpy for data handling.`;
    }

    private getBacktestSystemPrompt(): string {
        return `You are TradeStrat creating a robust backtesting framework. Include:

## Backtesting Framework Design

### 1. Data Management
- Historical data ingestion
- Data cleaning and validation
- Corporate actions handling
- Survivorship bias considerations

### 2. Signal Generation
- Strategy logic implementation
- Signal timing and execution
- Lookahead bias prevention
- Realistic latency modeling

### 3. Execution Simulation
- Order execution modeling
- Slippage and transaction costs
- Market impact considerations
- Partial fill handling

### 4. Performance Metrics
- Return calculations
- Risk-adjusted metrics (Sharpe, Sortino)
- Drawdown analysis
- Trade-level statistics

### 5. Visualization and Reporting
- Equity curve plotting
- Trade analysis charts
- Performance attribution
- Stress test results

### 6. Validation Techniques
- Out-of-sample testing
- Walk-forward analysis
- Monte Carlo simulation
- Bootstrap analysis

Provide production-ready Python code with proper error handling and logging.`;
    }

    private getRiskManagementSystemPrompt(): string {
        return `You are TradeStrat implementing comprehensive risk management. Cover:

## Risk Management Framework

### 1. Position Sizing
- Kelly criterion implementation
- Volatility-based sizing
- Maximum position limits
- Correlation adjustments

### 2. Portfolio Risk Controls
- Value-at-Risk (VaR) calculation
- Expected Shortfall (ES)
- Maximum drawdown limits
- Sector/asset concentration limits

### 3. Dynamic Risk Adjustment
- Volatility regime detection
- Risk scaling mechanisms
- Market stress indicators
- Emergency stop procedures

### 4. Monitoring and Alerts
- Real-time risk metrics
- Breach notifications
- Performance tracking
- Risk attribution analysis

### 5. Stress Testing
- Historical scenario analysis
- Monte Carlo stress tests
- Tail risk evaluation
- Correlation breakdown scenarios

### 6. Implementation Tools
- Risk calculation engines
- Alert systems
- Reporting dashboards
- Integration with trading systems

Focus on practical, implementable solutions with clear mathematical foundations.`;
    }

    private getValidationSystemPrompt(): string {
        return `You are TradeStrat validating trading strategies for production readiness. Analyze:

## Strategy Validation Checklist

### 1. Statistical Validation
- Statistical significance of returns
- Consistency across time periods
- Performance in different market regimes
- Correlation with market factors

### 2. Implementation Validation
- Code correctness and efficiency
- Data quality and completeness
- Signal generation accuracy
- Execution logic verification

### 3. Risk Validation
- Maximum drawdown analysis
- Tail risk assessment
- Stress test results
- Portfolio-level impact

### 4. Operational Validation
- System reliability and uptime
- Error handling and recovery
- Monitoring and alerting
- Compliance requirements

### 5. Performance Validation
- Live vs backtest performance
- Transaction cost impact
- Capacity constraints
- Scalability considerations

Provide detailed assessment with specific recommendations for improvement.`;
    }

    private getRiskAnalysisSystemPrompt(): string {
        return this.getRiskManagementSystemPrompt();
    }

    // Helper Methods

    private extractPythonCode(content: string): string {
        const pythonBlockRegex = /```python\n([\s\S]*?)```/g;
        const match = pythonBlockRegex.exec(content);
        return match ? match[1] : '';
    }

    private extractPreviousContent(previousResults: TaskResult[]): string {
        return previousResults
            .map(result => result.content)
            .join('\n\n---\n\n')
            .substring(0, 2000); // Limit context size
    }
}