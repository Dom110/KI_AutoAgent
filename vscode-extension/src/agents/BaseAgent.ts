/**
 * Enhanced BaseAgent with Configuration System Integration
 * Provides per-agent model selection, instruction loading, and self-adaptation
 */
import * as vscode from 'vscode';
import { AgentConfigurationManager } from '../core/AgentConfigurationManager';
import { OpenAIService } from '../utils/OpenAIService';
import { AnthropicService } from '../utils/AnthropicService';
import { WebSearchService } from '../utils/WebSearchService';
import { getClaudeCodeService } from '../services/ClaudeCodeService';
import { UnifiedChatMixin, ResponseType } from '../mixins/UnifiedChatMixin';

export interface AgentConfig {
    agentId: string;
    participantId: string;
    displayName: string;
    description: string;
    iconPath?: vscode.Uri;
    commands: string[];
}

export interface TaskRequest {
    prompt: string;
    context?: any;
    command?: string;
    projectType?: string;
    globalContext?: string;
    conversationHistory?: Array<{
        agent: string;
        step: string;
        content: string;
    }>;
    onPartialResponse?: (content: string) => void;
}

export interface TaskResult {
    status: 'success' | 'error' | 'partial_success';
    content: string;
    suggestions?: string[];
    references?: string[];
    metadata?: Record<string, any>;
}

export interface WorkflowStep {
    id: string;
    agent: string;
    description: string;
}

export abstract class BaseAgent extends UnifiedChatMixin {
    protected context: vscode.ExtensionContext;
    protected configManager: AgentConfigurationManager;
    protected openaiService: OpenAIService;
    protected anthropicService: AnthropicService;
    protected webSearchService: WebSearchService;
    
    public config: AgentConfig;
    protected instructions: string = '';
    protected selectedModel: string = '';
    
    // Properties for UnifiedChatMixin compatibility
    public name: string;
    public role: string;
    public model: string;

    constructor(
        context: vscode.ExtensionContext,
        config: AgentConfig,
        configManager?: AgentConfigurationManager
    ) {
        super(); // Initialize UnifiedChatMixin
        
        this.context = context;
        this.config = config;
        this.configManager = configManager || AgentConfigurationManager.getInstance(context);
        
        // Set properties for UnifiedChatMixin
        this.name = config.displayName || config.agentId;
        this.role = config.description;
        this.model = '';
        
        // Initialize services
        this.openaiService = new OpenAIService();
        this.anthropicService = new AnthropicService();
        this.webSearchService = new WebSearchService();
    }

    /**
     * Initialize agent with configuration system
     */
    public async initialize(): Promise<void> {
        try {
            // Load agent-specific model configuration
            this.selectedModel = this.configManager.getAgentModel(this.config.agentId);
            
            // Load agent instructions
            this.instructions = await this.configManager.getAgentInstructions(this.config.agentId);
            
            this.model = this.selectedModel; // Update model for UnifiedChatMixin
            console.log(this.showInitialization({ model: this.selectedModel }));
        } catch (error) {
            console.log(this.showError(`Failed to initialize ${this.config.agentId}`, error));
            // Use fallback configuration
            this.selectedModel = this.getDefaultModel();
            this.instructions = this.getDefaultInstructions();
        }
    }

    /**
     * Create VS Code chat handler for this agent
     */
    public createHandler(): vscode.ChatRequestHandler {
        return async (
            request: vscode.ChatRequest,
            context: vscode.ChatContext,
            stream: vscode.ChatResponseStream,
            token: vscode.CancellationToken
        ): Promise<any> => {
            const startTime = Date.now();
            let success = false;
            
            try {
                // Build enhanced prompt with instructions
                const enhancedPrompt = this.buildEnhancedPrompt(request.prompt, context);
                
                // Execute with configured model
                const result = await this.executeWithModel(enhancedPrompt, request, context);
                
                // Stream response
                stream.markdown(result.content);
                
                // Add suggestions if available
                if (result.suggestions && result.suggestions.length > 0) {
                    stream.markdown('\n\n**Suggestions:**\n');
                    result.suggestions.forEach(suggestion => {
                        stream.markdown(`• ${suggestion}\n`);
                    });
                }
                
                success = result.status === 'success' || result.status === 'partial_success';
                
                return result;
            } catch (error) {
                const errorMessage = `Error in ${this.config.displayName}: ${(error as Error).message}`;
                stream.markdown(errorMessage);
                console.log(this.showError(errorMessage, error));
                return {
                    status: 'error',
                    content: errorMessage
                };
            } finally {
                // Record performance for learning
                const responseTime = Date.now() - startTime;
                await this.recordPerformance(success, responseTime, request.prompt);
            }
        };
    }

    /**
     * Execute workflow step (used by MasterDispatcher)
     */
    public async executeStep(
        step: WorkflowStep,
        request: TaskRequest,
        previousResults: TaskResult[]
    ): Promise<TaskResult> {
        const startTime = Date.now();
        let success = false;
        
        try {
            // Build context-aware prompt
            const contextPrompt = this.buildWorkflowPrompt(step, request, previousResults);
            
            // Execute with configured model
            const result = await this.executeWithModel(contextPrompt, request);
            success = result.status === 'success' || result.status === 'partial_success';
            
            return result;
        } catch (error) {
            return {
                status: 'error',
                content: `Error in ${step.description}: ${(error as Error).message}`,
                metadata: { error: (error as Error).message }
            };
        } finally {
            // Record performance
            const responseTime = Date.now() - startTime;
            await this.recordPerformance(success, responseTime, request.prompt);
        }
    }

    /**
     * Execute with the configured model
     */
    protected async executeWithModel(
        prompt: string,
        request?: any,
        context?: vscode.ChatContext
    ): Promise<TaskResult> {
        const modelProvider = this.getModelProvider(this.selectedModel);
        
        switch (modelProvider) {
            case 'anthropic':
                return await this.executeWithClaude(prompt, request, context);
            case 'openai':
                return await this.executeWithGPT(prompt, request, context);
            case 'perplexity':
                return await this.executeWithPerplexity(prompt, request, context);
            default:
                throw new Error(`Unsupported model provider: ${modelProvider}`);
        }
    }

    /**
     * Execute with Claude models (via Claude Code App or API)
     */
    protected async executeWithClaude(
        prompt: string,
        request?: any,
        context?: vscode.ChatContext
    ): Promise<TaskResult> {
        try {
            // First, try to use Claude Code App (local CLI)
            const claudeCodeService = getClaudeCodeService();
            const isClaudeCodeAvailable = await claudeCodeService.isAvailable();
            
            if (isClaudeCodeAvailable) {
                // Use Claude Code App
                console.log(this.showInfo('Using Claude Code App', { model: this.selectedModel }));
                
                // Map model names to Claude Code CLI format
                let cliModel: 'opus' | 'sonnet' | 'default' = 'default';
                if (this.selectedModel.includes('opus')) {
                    cliModel = 'opus';
                } else if (this.selectedModel.includes('sonnet')) {
                    cliModel = 'sonnet';
                }
                
                const response = await claudeCodeService.sendMessage(prompt, {
                    model: cliModel,
                    temperature: 0.7,
                    maxTokens: this.getMaxTokens()
                });
                
                return {
                    status: 'success',
                    content: response.content,
                    metadata: {
                        model: this.selectedModel,
                        provider: 'claude-code-app',
                        ...response.metadata
                    }
                };
            } else {
                // Fall back to Anthropic API
                console.log(this.showFallbackMode('Claude Code App not available', 'Using Anthropic API'));
                
                const response = await this.anthropicService.chat(
                    [{ role: 'user', content: prompt }],
                    this.selectedModel,
                    this.getMaxTokens()
                );

                return {
                    status: 'success',
                    content: response,
                    metadata: {
                        model: this.selectedModel,
                        provider: 'anthropic-api'
                    }
                };
            }
        } catch (error) {
            const errorMessage = (error as Error).message;
            
            // Provide helpful error messages
            if (errorMessage.includes('Claude Code CLI not found')) {
                throw new Error(
                    `Claude Code CLI not installed. Please install with:\nnpm install -g @anthropic-ai/claude-code\n\nAlternatively, configure your Anthropic API key in VS Code settings.`
                );
            } else if (errorMessage.includes('API key')) {
                throw new Error(
                    `Anthropic API key not configured. Please add your API key in VS Code settings (search for "KI AutoAgent").`
                );
            } else {
                throw new Error(`Claude execution failed: ${errorMessage}`);
            }
        }
    }

    /**
     * Execute with GPT models
     */
    protected async executeWithGPT(
        prompt: string,
        request?: any,
        context?: vscode.ChatContext
    ): Promise<TaskResult> {
        try {
            const response = await this.openaiService.chat(
                [{ role: 'user', content: prompt }],
                this.selectedModel,
                this.getMaxTokens()
            );

            return {
                status: 'success',
                content: response,
                metadata: {
                    model: this.selectedModel,
                    provider: 'openai'
                }
            };
        } catch (error) {
            throw new Error(`GPT execution failed: ${(error as Error).message}`);
        }
    }

    /**
     * Execute with Perplexity (research-focused)
     */
    protected async executeWithPerplexity(
        prompt: string,
        request?: any,
        context?: vscode.ChatContext
    ): Promise<TaskResult> {
        try {
            const searchResponse = await this.webSearchService.search(prompt);
            
            // Combine search results with prompt
            const enhancedPrompt = `${prompt}\n\nBased on current web research:\n${searchResponse.results.slice(0, 5).map(r => `• ${r.title}: ${r.snippet}`).join('\n')}`;
            
            return {
                status: 'success',
                content: enhancedPrompt,
                references: searchResponse.results.map(r => r.url),
                metadata: {
                    model: this.selectedModel,
                    provider: 'perplexity',
                    searchResults: searchResponse.results.length
                }
            };
        } catch (error) {
            throw new Error(`Perplexity execution failed: ${(error as Error).message}`);
        }
    }

    /**
     * Build enhanced prompt with instructions
     */
    protected buildEnhancedPrompt(userPrompt: string, context?: vscode.ChatContext): string {
        let enhancedPrompt = this.instructions + '\n\n';
        
        // Add context information
        if (context) {
            enhancedPrompt += `## Context\n`;
            enhancedPrompt += `Previous messages: ${context.history.length}\n`;
        }
        
        // Add workspace context
        const workspace = vscode.workspace.workspaceFolders?.[0];
        if (workspace) {
            enhancedPrompt += `Workspace: ${workspace.name}\n`;
        }
        
        enhancedPrompt += `\n## User Request\n${userPrompt}\n\n`;
        enhancedPrompt += `## Instructions\nProvide a response following your agent instructions above. Be precise, actionable, and maintain your specialized expertise.`;
        
        return enhancedPrompt;
    }

    /**
     * Build workflow-specific prompt
     */
    protected buildWorkflowPrompt(
        step: WorkflowStep,
        request: TaskRequest,
        previousResults: TaskResult[]
    ): string {
        let prompt = this.instructions + '\n\n';
        
        // Include global conversation context if available
        if (request.globalContext) {
            prompt += request.globalContext + '\n\n';
        }
        
        prompt += `## Workflow Step: ${step.description}\n`;
        prompt += `## Original Request: ${request.prompt}\n\n`;
        
        // Include conversation history from current workflow if available
        if (request.conversationHistory && request.conversationHistory.length > 0) {
            prompt += `## Current Workflow Context:\n`;
            request.conversationHistory.forEach(entry => {
                prompt += `### ${entry.agent} (${entry.step}):\n${entry.content}\n\n`;
            });
        }
        
        // Include immediate previous results from this workflow
        if (previousResults.length > 0) {
            prompt += `## Immediate Previous Steps:\n`;
            previousResults.forEach((result, index) => {
                const agentName = result.metadata?.agent || `Agent ${index + 1}`;
                const stepName = result.metadata?.step || `Step ${index + 1}`;
                prompt += `### ${agentName} (${stepName}):\n${result.content}\n\n`;
            });
        }
        
        prompt += `## Your Task\nExecute "${step.description}" based on the information above. Provide specific, actionable results for this step.`;
        
        return prompt;
    }

    /**
     * Record performance for learning system
     */
    protected async recordPerformance(
        success: boolean,
        responseTime: number,
        context?: string
    ): Promise<void> {
        try {
            await this.configManager.recordAgentPerformance(
                this.config.agentId,
                success,
                responseTime,
                context
            );
            
            // Check if self-adaptation should occur
            if (success && await this.shouldSelfAdapt()) {
                await this.performSelfAdaptation(context);
            }
        } catch (error) {
            console.log(this.showWarning(`Failed to record performance for ${this.config.agentId}`, { error: (error as Error).message }));
        }
    }

    /**
     * Check if agent should perform self-adaptation
     */
    protected async shouldSelfAdapt(): Promise<boolean> {
        const learningConfig = this.configManager.getLearningConfig();
        if (!learningConfig.enabled || !learningConfig.learningModes.successBasedLearning) {
            return false;
        }
        
        const metrics = this.configManager.getAgentMetrics(this.config.agentId);
        if (!metrics || metrics.totalExecutions < 20) {
            return false; // Need more data
        }
        
        const successRate = metrics.successfulExecutions / metrics.totalExecutions;
        return successRate >= learningConfig.adaptationThreshold && 
               metrics.currentStreak >= 5; // 5 successful executions in a row
    }

    /**
     * Perform self-adaptation of instructions
     */
    protected async performSelfAdaptation(context?: string): Promise<void> {
        try {
            // This would analyze recent successful patterns and update instructions
            const adaptationPrompt = this.buildAdaptationPrompt(context);
            const result = await this.executeWithModel(adaptationPrompt);
            
            if (result.status === 'success') {
                const reason = `Self-adaptation based on ${this.config.agentId} success patterns`;
                await this.configManager.updateAgentInstructions(
                    this.config.agentId,
                    result.content,
                    reason,
                    'learning'
                );
                
                // Reload instructions
                this.instructions = await this.configManager.getAgentInstructions(this.config.agentId);
                
                console.log(this.showSuccess('Self-adapted instructions successfully'));
            }
        } catch (error) {
            console.log(this.showWarning(`Self-adaptation failed for ${this.config.agentId}`, { error: (error as Error).message }));
        }
    }

    /**
     * Build prompt for self-adaptation analysis
     */
    protected buildAdaptationPrompt(context?: string): string {
        const metrics = this.configManager.getAgentMetrics(this.config.agentId);
        
        return `
## Self-Adaptation Analysis for ${this.config.displayName}

### Current Instructions:
${this.instructions}

### Performance Metrics:
- Success Rate: ${metrics ? (metrics.successfulExecutions / metrics.totalExecutions * 100).toFixed(1) : 'N/A'}%
- Current Streak: ${metrics?.currentStreak || 0}
- Total Executions: ${metrics?.totalExecutions || 0}

### Recent Success Context:
${context || 'General successful interactions'}

### Task:
Analyze your current instructions and recent successful patterns. Suggest 2-3 specific improvements to your instructions that would:
1. Strengthen your successful approaches
2. Be more precise about your expertise
3. Better serve users in your specialized domain

Provide the updated instructions in the same format, keeping what works well and improving what could be better.
`;
    }

    // Utility methods
    protected getModelProvider(modelId: string): 'anthropic' | 'openai' | 'perplexity' {
        if (modelId.includes('claude')) return 'anthropic';
        if (modelId.includes('gpt')) return 'openai';
        if (modelId.includes('llama') || modelId.includes('sonar')) return 'perplexity';
        return 'anthropic'; // default
    }

    protected getMaxTokens(): number {
        return vscode.workspace.getConfiguration('kiAutoAgent').get('maxTokens', 4000);
    }

    // Abstract methods that subclasses must implement
    protected abstract getDefaultModel(): string;
    protected abstract getDefaultInstructions(): string;
}