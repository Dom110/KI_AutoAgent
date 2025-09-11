/**
 * Base Chat Agent class for VS Code Chat Extensions
 * All specialized agents inherit from this base class
 */
import * as vscode from 'vscode';
import { AgentConfig, TaskRequest, TaskResult, WorkflowStep, AIModel } from '../../types';
import { VSCodeMasterDispatcher } from '../../core/VSCodeMasterDispatcher';

export abstract class ChatAgent {
    protected context: vscode.ExtensionContext;
    protected dispatcher: VSCodeMasterDispatcher;
    protected stats = {
        totalExecutions: 0,
        successCount: 0,
        totalResponseTime: 0,
        lastExecution: undefined as Date | undefined
    };

    constructor(
        protected config: AgentConfig,
        context: vscode.ExtensionContext,
        dispatcher: VSCodeMasterDispatcher
    ) {
        this.context = context;
        this.dispatcher = dispatcher;
    }

    /**
     * Create VS Code chat request handler
     */
    createHandler(): vscode.ChatRequestHandler {
        return async (
            request: vscode.ChatRequest,
            context: vscode.ChatContext,
            stream: vscode.ChatResponseStream,
            token: vscode.CancellationToken
        ) => {
            const startTime = Date.now();
            this.stats.totalExecutions++;
            this.stats.lastExecution = new Date();

            try {
                // Show agent info
                stream.progress(`🤖 ${this.config.fullName} is working...`);
                
                // Handle the request
                await this.handleRequest(request, context, stream, token);
                
                // Update success stats
                this.stats.successCount++;
                this.stats.totalResponseTime += Date.now() - startTime;

            } catch (error) {
                await this.handleError(error as Error, stream);
                this.stats.totalResponseTime += Date.now() - startTime;
            }
        };
    }

    /**
     * Main request handler - to be implemented by each agent
     */
    protected abstract handleRequest(
        request: vscode.ChatRequest,
        context: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void>;

    /**
     * Execute a workflow step (called by dispatcher)
     */
    async executeStep(
        step: WorkflowStep,
        request: TaskRequest,
        previousResults: TaskResult[]
    ): Promise<TaskResult> {
        try {
            return await this.processWorkflowStep(step, request, previousResults);
        } catch (error) {
            return {
                status: 'error',
                content: `Error executing ${step.description}: ${error.message}`,
                metadata: { error: error.message, step: step.id }
            };
        }
    }

    /**
     * Process a workflow step - to be implemented by each agent
     */
    protected abstract processWorkflowStep(
        step: WorkflowStep,
        request: TaskRequest,
        previousResults: TaskResult[]
    ): Promise<TaskResult>;

    /**
     * Handle command-specific logic
     */
    protected async handleCommand(
        command: string,
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        const commandHandler = this.config.commands.find(cmd => cmd.name === command);
        
        if (commandHandler) {
            const methodName = commandHandler.handler;
            if (typeof (this as any)[methodName] === 'function') {
                await (this as any)[methodName](prompt, stream, token);
            } else {
                stream.markdown(`❌ Command handler '${methodName}' not implemented for ${command}`);
            }
        } else {
            stream.markdown(`❌ Unknown command: /${command}`);
            await this.showAvailableCommands(stream);
        }
    }

    /**
     * Show available commands for this agent
     */
    protected async showAvailableCommands(stream: vscode.ChatResponseStream): Promise<void> {
        stream.markdown(`## Available Commands for ${this.config.fullName}\n\n`);
        
        for (const cmd of this.config.commands) {
            stream.markdown(`- **/${cmd.name}** - ${cmd.description}\n`);
        }
        
        stream.markdown(`\n💡 Use \`@${this.config.name} /<command> <your request>\``);
    }

    /**
     * Get workspace context for AI models
     */
    protected async getWorkspaceContext(): Promise<string> {
        const workspaceContext = await this.dispatcher.getWorkspaceContext();
        
        let contextString = '';
        
        if (workspaceContext.currentFile) {
            contextString += `Current file: ${workspaceContext.currentFile}\n`;
        }
        
        if (workspaceContext.selectedText) {
            contextString += `Selected text:\n\`\`\`\n${workspaceContext.selectedText}\n\`\`\`\n`;
        }
        
        if (workspaceContext.workspaceRoots && workspaceContext.workspaceRoots.length > 0) {
            contextString += `Workspace: ${workspaceContext.workspaceRoots[0].name}\n`;
        }
        
        return contextString;
    }

    /**
     * Render code in the chat with syntax highlighting
     */
    protected renderCode(
        code: string,
        language: string,
        stream: vscode.ChatResponseStream,
        title?: string
    ): void {
        if (title) {
            stream.markdown(`### ${title}\n\n`);
        }
        stream.markdown(`\`\`\`${language}\n${code}\n\`\`\`\n\n`);
    }

    /**
     * Create action buttons for the user
     */
    protected createActionButton(
        title: string,
        command: string,
        args: any[],
        stream: vscode.ChatResponseStream
    ): void {
        stream.button({
            command,
            title,
            arguments: args
        });
    }

    /**
     * Add file reference to chat
     */
    protected addFileReference(
        filePath: string,
        stream: vscode.ChatResponseStream
    ): void {
        try {
            const uri = vscode.Uri.file(filePath);
            stream.reference(uri);
        } catch (error) {
            console.error('Error adding file reference:', error);
        }
    }

    /**
     * Error handler
     */
    protected async handleError(error: Error, stream: vscode.ChatResponseStream): Promise<void> {
        console.error(`Error in ${this.config.fullName}:`, error);
        
        stream.markdown(`❌ **Error**: ${error.message}\n\n`);
        stream.markdown(`💡 **Suggestions:**\n`);
        stream.markdown(`- Check your API keys in settings\n`);
        stream.markdown(`- Verify your internet connection\n`);
        stream.markdown(`- Try rephrasing your request\n`);
        
        // Offer to show help
        this.createActionButton(
            'Show Help',
            'ki-autoagent.showHelp',
            [this.config.participantId],
            stream
        );
    }

    /**
     * Get agent statistics
     */
    getStats() {
        return {
            ...this.stats,
            successRate: this.stats.totalExecutions > 0 
                ? this.stats.successCount / this.stats.totalExecutions 
                : 0,
            averageResponseTime: this.stats.totalExecutions > 0
                ? this.stats.totalResponseTime / this.stats.totalExecutions
                : 0
        };
    }

    /**
     * Get AI model configuration
     */
    protected getModelConfig(): { model: AIModel; apiKey?: string } {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        
        let model: AIModel = this.config.model as AIModel;
        let apiKey: string | undefined;
        
        switch (model) {
            case 'gpt-4o':
            case 'gpt-4o-mini':
                apiKey = config.get<string>('openai.apiKey');
                break;
            case 'claude-3.5-sonnet':
                apiKey = config.get<string>('anthropic.apiKey');
                break;
            case 'perplexity-pro':
                apiKey = config.get<string>('perplexity.apiKey');
                break;
        }
        
        return { model, apiKey };
    }

    /**
     * Validate API configuration
     */
    protected validateApiConfig(): boolean {
        const { apiKey } = this.getModelConfig();
        return !!apiKey;
    }

    /**
     * Get max tokens from configuration
     */
    protected getMaxTokens(): number {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        return config.get<number>('maxTokens', 4000);
    }

    /**
     * Check if logging is enabled
     */
    protected isLoggingEnabled(): boolean {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        return config.get<boolean>('enableLogging', true);
    }

    /**
     * Log message if logging is enabled
     */
    protected log(message: string, level: 'info' | 'warn' | 'error' = 'info'): void {
        if (this.isLoggingEnabled()) {
            const timestamp = new Date().toISOString();
            console[level](`[${timestamp}] ${this.config.fullName}: ${message}`);
        }
    }
}