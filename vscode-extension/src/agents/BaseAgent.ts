/**
 * Enhanced BaseAgent with Memory, Collaboration, and Configuration System Integration
 * Provides memory management, inter-agent communication, and intelligent collaboration
 */
import * as vscode from 'vscode';
import { AgentConfigurationManager } from '../core/AgentConfigurationManager';
import { OpenAIService } from '../utils/OpenAIService';
import { AnthropicService } from '../utils/AnthropicService';
import { WebSearchService } from '../utils/WebSearchService';
import { getClaudeCodeService } from '../services/ClaudeCodeService';
import { UnifiedChatMixin, ResponseType } from '../mixins/UnifiedChatMixin';
import { MemoryManager } from '../core/MemoryManager';
import { SharedContextManager, getSharedContext } from '../core/SharedContextManager';
import { AgentCommunicationBus, getCommunicationBus, MessageType, AgentMessage } from '../core/AgentCommunicationBus';
import { MemoryType, CodePattern, ArchitecturePattern, LearningEntry } from '../types/Memory';

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

    // Memory and Collaboration Systems
    protected memoryManager: MemoryManager;
    protected sharedContext: SharedContextManager;
    protected communicationBus: AgentCommunicationBus;
    protected collaborationSessions: Set<string> = new Set();

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

        // Initialize memory and collaboration systems
        this.memoryManager = new MemoryManager({
            maxMemories: 5000,
            similarityThreshold: 0.75,
            clusteringEnabled: true,
            patternExtractionEnabled: true
        });

        this.sharedContext = getSharedContext();
        this.communicationBus = getCommunicationBus();

        // Register for inter-agent communication
        this.registerCommunicationHandlers();
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
            // Build context with memory
            const enhancedRequest = await this.buildContextWithMemory(request);

            // Build context-aware prompt
            const contextPrompt = this.buildWorkflowPrompt(step, enhancedRequest, previousResults);

            // Update shared context with current task
            await this.updateSharedContext(`current_task_${this.config.agentId}`, {
                step: step.description,
                request: request.prompt,
                timestamp: Date.now()
            });

            // Execute with configured model
            const result = await this.executeWithModel(contextPrompt, enhancedRequest);
            success = result.status === 'success' || result.status === 'partial_success';

            // Store successful execution in memory
            if (success) {
                await this.storeMemory(
                    {
                        task: step.description,
                        request: request.prompt,
                        result: result.content,
                        metadata: result.metadata
                    },
                    MemoryType.EPISODIC,
                    { importance: 0.7 }
                );

                // Update shared context with results
                await this.updateSharedContext(`result_${step.id}`, {
                    agent: this.config.agentId,
                    content: result.content,
                    status: result.status
                });

                // Record learning if pattern detected
                this.recordLearning(
                    'success',
                    `Successfully completed: ${step.description}`,
                    { step, result }
                );
            }

            return result;
        } catch (error) {
            // Store failure for learning
            await this.storeMemory(
                {
                    task: step.description,
                    error: (error as Error).message,
                    context: request
                },
                MemoryType.EPISODIC,
                { importance: 0.8, type: 'failure' }
            );

            this.recordLearning(
                'failure',
                `Failed: ${step.description} - ${(error as Error).message}`,
                { step, error: (error as Error).message }
            );

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

    // ================ MEMORY & COLLABORATION METHODS ================

    /**
     * Build context with memory and shared knowledge
     */
    protected async buildContextWithMemory(request: TaskRequest): Promise<TaskRequest> {
        // Retrieve relevant memories
        const relevantMemories = await this.memoryManager.search(request.prompt, {
            k: 10,
            type: MemoryType.EPISODIC,
            agentId: this.config.agentId
        });

        // Get shared context
        const sharedContext = this.sharedContext.getContext();

        // Get relevant learnings
        const learnings = this.memoryManager.getRelevantLearnings(request.prompt, 5);

        // Enhance request with memory context
        const enhancedRequest: TaskRequest = {
            ...request,
            context: {
                ...request.context,
                memories: relevantMemories.map(r => r.entry.content),
                sharedKnowledge: sharedContext,
                learnings: learnings,
                collaboratingAgents: this.sharedContext.getActiveAgents()
            }
        };

        return enhancedRequest;
    }

    /**
     * Store experience in memory
     */
    protected async storeMemory(
        content: any,
        type: MemoryType,
        metadata?: any
    ): Promise<void> {
        await this.memoryManager.store(
            this.config.agentId,
            content,
            type,
            {
                ...metadata,
                projectId: vscode.workspace.workspaceFolders?.[0]?.name,
                timestamp: Date.now()
            }
        );
    }

    /**
     * Update shared context with agent findings
     */
    protected async updateSharedContext(key: string, value: any): Promise<void> {
        await this.sharedContext.updateContext(
            this.config.agentId,
            key,
            value,
            {
                confidence: 0.8,
                timestamp: Date.now()
            }
        );

        // Broadcast important updates
        if (this.isImportantUpdate(key)) {
            await this.communicationBus.broadcast(
                this.config.agentId,
                MessageType.KNOWLEDGE_SHARE,
                { key, value },
                { priority: 'high' }
            );
        }
    }

    /**
     * Request collaboration from other agents
     */
    protected async requestCollaboration(
        task: any,
        requiredAgents: string[]
    ): Promise<any> {
        const session = await this.communicationBus.startCollaboration(
            task,
            [this.config.agentId, ...requiredAgents],
            this.config.agentId
        );

        this.collaborationSessions.add(session.id);

        // Wait for collaboration to complete
        return new Promise((resolve) => {
            const checkInterval = setInterval(() => {
                if (session.status === 'completed') {
                    clearInterval(checkInterval);
                    this.collaborationSessions.delete(session.id);
                    resolve(session.results);
                }
            }, 1000);

            // Timeout after 30 seconds
            setTimeout(() => {
                clearInterval(checkInterval);
                this.collaborationSessions.delete(session.id);
                resolve(null);
            }, 30000);
        });
    }

    /**
     * Register communication handlers for this agent
     */
    private registerCommunicationHandlers(): void {
        this.communicationBus.register({
            agentId: this.config.agentId,
            messageTypes: [
                MessageType.REQUEST,
                MessageType.COLLABORATION_REQUEST,
                MessageType.HELP_REQUEST,
                MessageType.VALIDATION_REQUEST,
                MessageType.KNOWLEDGE_SHARE
            ],
            handler: async (message: AgentMessage) => {
                return await this.handleIncomingMessage(message);
            }
        });

        // Subscribe to shared context updates
        this.sharedContext.subscribe(
            this.config.agentId,
            (update) => {
                this.handleContextUpdate(update);
            }
        );
    }

    /**
     * Handle incoming messages from other agents
     */
    protected async handleIncomingMessage(message: AgentMessage): Promise<any> {
        switch (message.type) {
            case MessageType.HELP_REQUEST:
                return await this.provideHelp(message.content);

            case MessageType.COLLABORATION_REQUEST:
                return await this.joinCollaboration(message.content);

            case MessageType.VALIDATION_REQUEST:
                return await this.validateContent(message.content);

            case MessageType.KNOWLEDGE_SHARE:
                await this.processSharedKnowledge(message.content);
                return { acknowledged: true };

            default:
                return await this.processGenericRequest(message.content);
        }
    }

    /**
     * Provide help to requesting agent
     */
    protected async provideHelp(problem: any): Promise<any> {
        // Check if this agent can help
        if (!this.canHelp(problem)) {
            return null;
        }

        // Search memory for similar problems
        const similarProblems = await this.memoryManager.search(problem, {
            k: 5,
            type: MemoryType.PROCEDURAL
        });

        if (similarProblems.length > 0) {
            return {
                agent: this.config.agentId,
                solutions: similarProblems.map(r => r.entry.content),
                confidence: Math.max(...similarProblems.map(r => r.similarity))
            };
        }

        return null;
    }

    /**
     * Join a collaboration session
     */
    protected async joinCollaboration(request: any): Promise<any> {
        const { sessionId, task, leader } = request;
        this.collaborationSessions.add(sessionId);

        // Prepare for collaboration
        const preparation = await this.prepareForCollaboration(task);

        // Update shared context for this session
        await this.communicationBus.updateCollaborationContext(
            sessionId,
            this.config.agentId,
            `${this.config.agentId}_ready`,
            preparation
        );

        return {
            accepted: true,
            agent: this.config.agentId,
            preparation
        };
    }

    /**
     * Validate content from another agent
     */
    protected async validateContent(content: any): Promise<any> {
        // Override in specialized agents
        return {
            valid: true,
            agent: this.config.agentId,
            feedback: 'No specific validation implemented'
        };
    }

    /**
     * Process shared knowledge from other agents
     */
    protected async processSharedKnowledge(knowledge: any): Promise<void> {
        // Store in memory for future reference
        await this.storeMemory(
            knowledge,
            MemoryType.SEMANTIC,
            {
                source: 'shared_knowledge',
                importance: 0.6
            }
        );
    }

    /**
     * Process generic request from another agent
     */
    protected async processGenericRequest(content: any): Promise<any> {
        // Use standard execution path
        const result = await this.executeWithModel(JSON.stringify(content));
        return result.content;
    }

    /**
     * Handle shared context updates
     */
    protected handleContextUpdate(update: any): void {
        // Override in specialized agents to react to context changes
        console.log(`${this.config.agentId} received context update:`, update.key);
    }

    /**
     * Check if agent can help with problem
     */
    protected canHelp(problem: any): boolean {
        // Simple keyword matching - override in specialized agents
        const problemText = JSON.stringify(problem).toLowerCase();
        const expertise = this.config.description.toLowerCase();

        return expertise.split(' ').some(word =>
            word.length > 3 && problemText.includes(word)
        );
    }

    /**
     * Prepare for collaboration
     */
    protected async prepareForCollaboration(task: any): Promise<any> {
        // Gather relevant knowledge
        const relevantMemories = await this.memoryManager.search(task, {
            k: 5,
            type: MemoryType.SEMANTIC
        });

        return {
            agent: this.config.agentId,
            expertise: this.config.description,
            relevantKnowledge: relevantMemories.map(r => r.entry.content),
            readyToCollaborate: true
        };
    }

    /**
     * Check if update is important enough to broadcast
     */
    protected isImportantUpdate(key: string): boolean {
        const importantKeys = [
            'architectureDecisions',
            'criticalFindings',
            'securityIssues',
            'performanceBottlenecks'
        ];

        return importantKeys.some(k => key.includes(k));
    }

    /**
     * Store code pattern for reuse
     */
    protected storeCodePattern(pattern: CodePattern): void {
        this.memoryManager.storeCodePattern(pattern);
    }

    /**
     * Store architecture pattern for reuse
     */
    protected storeArchitecturePattern(pattern: ArchitecturePattern): void {
        this.memoryManager.storeArchitecturePattern(pattern);
    }

    /**
     * Record learning from experience
     */
    protected recordLearning(
        type: 'success' | 'failure' | 'insight',
        description: string,
        context: any
    ): void {
        const learning: LearningEntry = {
            id: `learn_${Date.now()}`,
            type,
            description,
            context,
            impact: 'medium',
            applicability: [this.config.agentId],
            timestamp: Date.now()
        };

        this.memoryManager.storeLearning(learning);
    }

    /**
     * Cleanup on agent disposal
     */
    public dispose(): void {
        this.communicationBus.unregister(this.config.agentId);
        this.sharedContext.unsubscribe(this.config.agentId);
    }
}