/**
 * Unified Chat Mixin - Standardized Chat Properties for all Agents
 * Provides consistent response formatting and logging across all agents
 */
import * as vscode from 'vscode';

export enum ResponseType {
    INITIALIZATION = "initialization",
    EXECUTING = "executing",
    SUCCESS = "success",
    WARNING = "warning",
    ERROR = "error",
    FALLBACK = "fallback",
    INFO = "info",
    TOOL_USE = "tool_use",
    DEBUG = "debug"
}

export interface ChatConfig {
    showEmojis: boolean;
    showTimestamps: boolean;
    showDetailedResponses: boolean;
    logLevel: string;
    responseFormat: 'detailed' | 'simple';
    fallbackMode: 'graceful' | 'strict';
}

export interface ResponseEntry {
    timestamp: Date;
    type: ResponseType;
    agentName: string;
    message: string;
    details?: any;
    formattedResponse: string;
}

export class UnifiedChatMixin {
    protected chatConfig: ChatConfig;
    protected responseHistory: ResponseEntry[] = [];
    private maxHistorySize: number = 100;

    constructor() {
        this.chatConfig = this.getDefaultChatConfig();
        this.responseHistory = [];
    }

    /**
     * Get default chat configuration from VS Code settings or use defaults
     */
    protected getDefaultChatConfig(): ChatConfig {
        const config = vscode.workspace.getConfiguration('ki-autoagent.chat');
        
        return {
            showEmojis: config.get<boolean>('showEmojis', true),
            showTimestamps: config.get<boolean>('showTimestamps', true),
            showDetailedResponses: config.get<boolean>('showDetailedResponses', true),
            logLevel: config.get<string>('logLevel', 'INFO'),
            responseFormat: config.get<'detailed' | 'simple'>('responseFormat', 'detailed'),
            fallbackMode: config.get<'graceful' | 'strict'>('fallbackMode', 'graceful')
        };
    }

    /**
     * Generate unified response with consistent formatting
     */
    public unifiedResponse(
        responseType: ResponseType,
        message: string,
        details?: Record<string, any>,
        logToHistory: boolean = true
    ): string {
        const responseParts: string[] = [];
        
        // Add emoji if enabled
        if (this.chatConfig.showEmojis) {
            const emoji = this.getEmojiForType(responseType);
            responseParts.push(`${emoji} `);
        }
        
        // Add timestamp if enabled
        if (this.chatConfig.showTimestamps) {
            const timestamp = new Date().toLocaleTimeString('en-US', { 
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            responseParts.push(`[${timestamp}] `);
        }
        
        // Add agent name
        const agentName = this.getAgentName();
        responseParts.push(`**${agentName}**: `);
        
        // Add main message
        responseParts.push(message);
        
        // Add details if available and detailed responses enabled
        if (details && this.chatConfig.showDetailedResponses && this.chatConfig.responseFormat === 'detailed') {
            responseParts.push(this.formatDetails(details));
        }
        
        // Combine response
        const formattedResponse = responseParts.join('');
        
        // Log to history
        if (logToHistory) {
            this.logToHistory(responseType, message, details, formattedResponse);
        }
        
        // Log to console based on log level
        this.logResponse(responseType, formattedResponse);
        
        return formattedResponse;
    }

    /**
     * Get emoji for response type
     */
    private getEmojiForType(responseType: ResponseType): string {
        const emojiMap: Record<ResponseType, string> = {
            [ResponseType.INITIALIZATION]: "🚀",
            [ResponseType.EXECUTING]: "🛠️",
            [ResponseType.SUCCESS]: "✅",
            [ResponseType.WARNING]: "⚠️",
            [ResponseType.ERROR]: "❌",
            [ResponseType.FALLBACK]: "🔄",
            [ResponseType.INFO]: "ℹ️",
            [ResponseType.TOOL_USE]: "🔧",
            [ResponseType.DEBUG]: "🐛"
        };
        return emojiMap[responseType] || "📝";
    }

    /**
     * Format details object for display
     */
    private formatDetails(details: Record<string, any>): string {
        if (!details || Object.keys(details).length === 0) {
            return '';
        }
        
        const detailsStr = Object.entries(details)
            .map(([key, value]) => {
                const formattedKey = key.replace(/([A-Z])/g, ' $1').trim();
                const formattedValue = typeof value === 'object' 
                    ? JSON.stringify(value, null, 2) 
                    : value;
                return `      ${formattedKey}: ${formattedValue}`;
            })
            .join('\n');
        
        return `\n   📊 Details:\n${detailsStr}`;
    }

    /**
     * Get agent name - to be overridden by implementing classes
     */
    protected getAgentName(): string {
        // Try to get from various possible properties
        return (this as any).name || 
               (this as any).config?.agentId || 
               (this as any).config?.name ||
               'Agent';
    }

    /**
     * Log response to console based on log level
     */
    private logResponse(responseType: ResponseType, formattedResponse: string): void {
        const logLevelMap: Record<ResponseType, string> = {
            [ResponseType.ERROR]: 'ERROR',
            [ResponseType.WARNING]: 'WARN',
            [ResponseType.DEBUG]: 'DEBUG',
            [ResponseType.INFO]: 'INFO',
            [ResponseType.SUCCESS]: 'INFO',
            [ResponseType.EXECUTING]: 'INFO',
            [ResponseType.INITIALIZATION]: 'INFO',
            [ResponseType.FALLBACK]: 'WARN',
            [ResponseType.TOOL_USE]: 'DEBUG'
        };
        
        const level = logLevelMap[responseType] || 'INFO';
        
        // Only log if meets minimum log level
        if (this.shouldLog(level)) {
            console.log(formattedResponse);
        }
    }

    /**
     * Check if should log based on configured log level
     */
    private shouldLog(level: string): boolean {
        const levels = ['DEBUG', 'INFO', 'WARN', 'ERROR'];
        const configuredLevel = levels.indexOf(this.chatConfig.logLevel);
        const messageLevel = levels.indexOf(level);
        return messageLevel >= configuredLevel;
    }

    /**
     * Log to response history
     */
    private logToHistory(
        type: ResponseType, 
        message: string, 
        details: any, 
        formattedResponse: string
    ): void {
        const entry: ResponseEntry = {
            timestamp: new Date(),
            type,
            agentName: this.getAgentName(),
            message,
            details,
            formattedResponse
        };
        
        this.responseHistory.push(entry);
        
        // Trim history if exceeds max size
        if (this.responseHistory.length > this.maxHistorySize) {
            this.responseHistory = this.responseHistory.slice(-this.maxHistorySize);
        }
    }

    // Standardized message methods

    /**
     * Show initialization message
     */
    public showInitialization(additionalInfo?: Record<string, any>): string {
        const details: Record<string, any> = {
            role: (this as any).role || 'Unknown',
            model: (this as any).model || (this as any).selectedModel || 'Unknown'
        };
        
        // Add capabilities if available
        if (typeof (this as any).getCapabilities === 'function') {
            details.capabilities = (this as any).getCapabilities();
        }
        
        if (additionalInfo) {
            Object.assign(details, additionalInfo);
        }
        
        return this.unifiedResponse(
            ResponseType.INITIALIZATION,
            "Ready to assist with advanced capabilities!",
            details
        );
    }

    /**
     * Show execution start message
     */
    public showExecutionStart(task: string, context?: Record<string, any>): string {
        const details: Record<string, any> = {
            task: task.substring(0, 100), // Truncate long tasks
            contextKeys: context ? Object.keys(context) : []
        };
        
        // Add conversation history size if available
        if (context?.conversationHistory) {
            details.conversationHistorySize = context.conversationHistory.length;
        }
        
        return this.unifiedResponse(
            ResponseType.EXECUTING,
            `Starting execution: ${task.substring(0, 50)}${task.length > 50 ? '...' : ''}`,
            details
        );
    }

    /**
     * Show success message
     */
    public showSuccess(message: string, details?: Record<string, any>): string {
        return this.unifiedResponse(ResponseType.SUCCESS, message, details);
    }

    /**
     * Show warning message
     */
    public showWarning(message: string, details?: Record<string, any>): string {
        return this.unifiedResponse(ResponseType.WARNING, message, details);
    }

    /**
     * Show error message
     */
    public showError(message: string, error?: Error | any): string {
        const details: Record<string, any> = {};
        
        if (error) {
            details.error = error.message || String(error);
            if (error.stack && this.chatConfig.showDetailedResponses) {
                details.stack = error.stack.split('\n').slice(0, 3).join('\n');
            }
        }
        
        return this.unifiedResponse(ResponseType.ERROR, message, details);
    }

    /**
     * Show fallback mode message
     */
    public showFallbackMode(reason: string, fallbackAction: string): string {
        const details = {
            reason,
            fallbackAction,
            mode: this.chatConfig.fallbackMode
        };
        
        return this.unifiedResponse(
            ResponseType.FALLBACK,
            `Switching to fallback mode: ${reason}`,
            details
        );
    }

    /**
     * Show tool use message
     */
    public showToolUse(toolName: string, parameters?: Record<string, any>): string {
        const details: Record<string, any> = {
            tool: toolName
        };
        
        if (parameters && this.chatConfig.showDetailedResponses) {
            details.parameters = parameters;
        }
        
        return this.unifiedResponse(
            ResponseType.TOOL_USE,
            `Using tool: ${toolName}`,
            details
        );
    }

    /**
     * Show info message
     */
    public showInfo(message: string, details?: Record<string, any>): string {
        return this.unifiedResponse(ResponseType.INFO, message, details);
    }

    /**
     * Show debug message
     */
    public showDebug(message: string, details?: Record<string, any>): string {
        return this.unifiedResponse(ResponseType.DEBUG, message, details);
    }

    // History management methods

    /**
     * Get response history
     */
    public getResponseHistory(): ResponseEntry[] {
        return [...this.responseHistory]; // Return copy to prevent external modification
    }

    /**
     * Get formatted response history
     */
    public getFormattedHistory(limit?: number): string {
        const history = limit 
            ? this.responseHistory.slice(-limit)
            : this.responseHistory;
        
        return history
            .map(entry => entry.formattedResponse)
            .join('\n');
    }

    /**
     * Clear response history
     */
    public clearHistory(): void {
        this.responseHistory = [];
    }

    /**
     * Export response history
     */
    public exportHistory(): string {
        return JSON.stringify(this.responseHistory, null, 2);
    }

    /**
     * Update chat configuration
     */
    public updateChatConfig(config: Partial<ChatConfig>): void {
        Object.assign(this.chatConfig, config);
    }

    /**
     * Get current chat configuration
     */
    public getChatConfig(): ChatConfig {
        return { ...this.chatConfig };
    }
}