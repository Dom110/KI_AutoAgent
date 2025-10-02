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

export interface ValidationResult {
    isComplete: boolean;
    completedItems: string[];
    missingItems: string[];
    bugs: string[];
    recommendations: string[];
    confidence: number;
}

export interface ValidationWorkflow {
    enabled: boolean;
    maxIterations: number;
    agents: string[];
    autoFix: boolean;
}

// ============================================================================
// v5.2.0: Architecture Proposal System - WebSocket Message Types
// ============================================================================

/**
 * Architecture proposal structure
 */
export interface ArchitectureProposal {
    summary: string;                  // High-level architecture overview
    improvements: string;              // Suggested improvements based on research
    tech_stack: string;                // Recommended technologies with justifications
    structure: string;                 // Folder/module structure
    risks: string;                     // Potential challenges and mitigations
    research_insights: string;         // Key research findings
}

/**
 * Message sent from backend when architecture proposal is ready
 */
export interface ArchitectureProposalMessage {
    type: 'architecture_proposal' | 'architecture_proposal_revised';
    proposal: ArchitectureProposal;
    formatted_message: string;         // Markdown formatted for display
    session_id: string;
}

/**
 * Message sent from frontend to backend with user's decision
 */
export interface ArchitectureApprovalRequest {
    type: 'architecture_approval';
    session_id: string;
    decision: 'approved' | 'rejected' | 'modified';
    feedback?: string;                 // Optional user comments/changes
}

/**
 * Response from backend after processing approval
 */
export interface ArchitectureApprovalResponse {
    type: 'architectureApprovalProcessed';
    session_id: string;
    decision: 'approved' | 'rejected' | 'modified';
    message: string;
}

/**
 * Union type for all WebSocket messages
 */
export type WebSocketMessage =
    | { type: 'connected'; session_id: string; client_id: string; version: string }
    | { type: 'chat'; content: string }
    | { type: 'response'; agent: string; content: string; metadata?: any }
    | { type: 'agent_thinking'; agent: string; message: string }
    | { type: 'step_completed'; agent: string; task: string; result: any }
    | { type: 'error'; message: string; traceback?: string }
    | { type: 'planFirstModeUpdated'; enabled: boolean }
    | { type: 'setWorkspace'; workspace_path: string }
    | ArchitectureProposalMessage
    | ArchitectureApprovalRequest
    | ArchitectureApprovalResponse;

// ============================================================================
// End of v5.2.0 Message Types
// ============================================================================