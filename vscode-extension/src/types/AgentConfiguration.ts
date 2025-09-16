/**
 * Agent Configuration Types for KI AutoAgent
 * Defines types for per-agent model selection and instruction management
 */

export interface AgentModelConfig {
    agentId: string;
    displayName: string;
    selectedModel: string;
    availableModels: string[];
    instructionFile: string;
    lastUpdated: string;
    performanceScore: number;
}

export interface InstructionSet {
    agentId: string;
    version: string;
    content: string;
    lastModified: string;
    modifiedBy: 'user' | 'self-adaptation' | 'auto-learning';
    successRate: number;
    totalExecutions: number;
    adaptationHistory: InstructionAdaptation[];
}

export interface InstructionAdaptation {
    timestamp: string;
    trigger: 'success' | 'failure' | 'manual' | 'learning';
    oldContent: string;
    newContent: string;
    reason: string;
    performanceImpact?: number;
}

export interface LearningConfig {
    enabled: boolean;
    adaptationThreshold: number; // Success rate required for adaptation
    maxAdaptationsPerDay: number;
    confidenceLevel: number; // How confident to be before adapting
    learningModes: {
        successBasedLearning: boolean;
        failureBasedLearning: boolean;
        patternRecognition: boolean;
        contextualAdaptation: boolean;
    };
}

export interface PerformanceMetrics {
    agentId: string;
    totalExecutions: number;
    successfulExecutions: number;
    failedExecutions: number;
    averageResponseTime: number;
    lastExecution: string;
    successPatterns: ActionPattern[];
    failurePatterns: ActionPattern[];
    currentStreak: number;
    bestStreak: number;
}

export interface ActionPattern {
    pattern: string;
    frequency: number;
    successRate: number;
    contexts: string[];
    lastSeen: string;
}

export interface AgentConfigurationSystem {
    models: Map<string, AgentModelConfig>;
    instructions: Map<string, InstructionSet>;
    learning: LearningConfig;
    metrics: Map<string, PerformanceMetrics>;
}

// Available Models Configuration
export const AVAILABLE_MODELS = {
    // Claude Models (2025)
    'claude-opus-4-1-20250805': {
        name: 'Claude Opus 4.1',
        provider: 'anthropic',
        tier: 'supreme',
        strengths: ['reasoning', 'conflict-resolution', 'judgment'],
        costPerMillion: { input: 15, output: 75 }
    },
    'claude-sonnet-4-20250514': {
        name: 'Claude Sonnet 4',
        provider: 'anthropic', 
        tier: 'premium',
        strengths: ['coding', 'analysis', 'implementation'],
        costPerMillion: { input: 3, output: 15 }
    },
    'claude-3-7-sonnet-20250219': {
        name: 'Claude 3.7 Sonnet',
        provider: 'anthropic',
        tier: 'standard', 
        strengths: ['thinking', 'extended-reasoning'],
        costPerMillion: { input: 3, output: 15 }
    },
    
    // OpenAI Models (2024)
    'gpt-4o-2024-11-20': {
        name: 'GPT-4o (Latest)',
        provider: 'openai',
        tier: 'premium',
        strengths: ['multimodal', 'architecture', 'planning'],
        costPerMillion: { input: 2.5, output: 10 }
    },
    'gpt-4o-mini-2024-07-18': {
        name: 'GPT-4o Mini',
        provider: 'openai', 
        tier: 'efficient',
        strengths: ['fast-responses', 'cost-effective', 'review'],
        costPerMillion: { input: 0.15, output: 0.6 }
    },
    
    // Perplexity Models
    'llama-3.1-sonar-small-128k-online': {
        name: 'Llama 3.1 Sonar (Online)',
        provider: 'perplexity',
        tier: 'research',
        strengths: ['web-search', 'real-time-data', 'research'],
        costPerMillion: { input: 0.2, output: 0.2 }
    }
} as const;

// Default Agent-Model Mappings
export const DEFAULT_AGENT_MODELS = {
    'orchestrator': 'claude-sonnet-4-20250514',
    'richter': 'claude-opus-4-1-20250805', // Supreme Judge needs Opus
    'architect': 'gpt-4o-2024-11-20', // Architecture planning
    'codesmith': 'claude-sonnet-4-20250514', // Best for coding
    'tradestrat': 'claude-sonnet-4-20250514', // Trading analysis
    'research': 'llama-3.1-sonar-small-128k-online' // Web research
} as const;