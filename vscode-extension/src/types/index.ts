/**
 * Type definitions for KI AutoAgent VS Code Extension
 */
import * as vscode from 'vscode';

export interface AgentConfig {
    participantId: string;
    name: string;
    fullName: string;
    description: string;
    model: string;
    iconPath?: vscode.Uri;
    capabilities: string[];
    commands: AgentCommand[];
}

export interface AgentCommand {
    name: string;
    description: string;
    handler: string;
}

export interface TaskRequest {
    prompt: string;
    command?: string;
    context?: WorkspaceContext;
    projectType?: string;
    globalContext?: string;
    conversationHistory?: Array<{
        agent: string;
        step: string;
        content: string;
    }>;
    onPartialResponse?: (content: string) => void;
    thinkingMode?: boolean;
    mode?: 'single' | 'auto' | 'workflow' | 'planning' | 'layered';
}

export interface TaskResult {
    status: 'success' | 'partial_success' | 'error';
    content: string;
    suggestions?: Suggestion[];
    references?: vscode.Uri[];
    metadata?: Record<string, any>;
}

export interface Suggestion {
    title: string;
    description: string;
    action: string;
    data: any;
}

export interface WorkspaceContext {
    activeEditor?: vscode.TextEditor;
    workspaceRoots?: readonly vscode.WorkspaceFolder[];
    openDocuments?: readonly vscode.TextDocument[];
    selectedText?: string;
    currentFile?: string;
    projectType?: string;
    packageJson?: any;
}

export interface Intent {
    type: string;
    confidence: number;
    agent: string;
    workflow?: string[];
}

export interface WorkflowStep {
    id: string;
    agent: string;
    description: string;
    dependencies?: string[];
    input?: any;
    output?: any;
}

export interface AgentStats {
    totalExecutions: number;
    successRate: number;
    averageResponseTime: number;
    lastExecution?: Date;
}

export interface ProjectTypeDefinition {
    name: string;
    patterns: string[];
    qualityGates: string[];
    workflow: WorkflowStep[];
    primaryAgent: string;
}

export type AIModel = 'gpt-4o' | 'claude-3.5-sonnet' | 'gpt-4o-mini' | 'perplexity-pro';

export interface APIConfig {
    openai?: {
        apiKey: string;
        baseURL?: string;
    };
    anthropic?: {
        apiKey: string;
        baseURL?: string;
    };
    perplexity?: {
        apiKey: string;
        baseURL?: string;
    };
}