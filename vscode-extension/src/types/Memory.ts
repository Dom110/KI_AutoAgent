/**
 * Memory Types for the Multi-Agent System
 * Defines the structure of different memory types and operations
 */

export interface MemoryEntry {
    id: string;
    agentId: string;
    timestamp: number;
    content: any;
    embedding?: number[];
    metadata: MemoryMetadata;
    type: MemoryType;
}

export interface MemoryMetadata {
    projectId?: string;
    taskId?: string;
    confidence?: number;
    tags?: string[];
    source?: string;
    relatedMemories?: string[];
    accessCount?: number;
    lastAccessed?: number;
    importance?: number;
}

export enum MemoryType {
    WORKING = 'working',      // Current task context
    EPISODIC = 'episodic',    // Specific events/interactions
    SEMANTIC = 'semantic',    // General knowledge
    PROCEDURAL = 'procedural' // How to do things
}

export interface MemorySearchResult {
    entry: MemoryEntry;
    similarity: number;
    relevance: number;
}

export interface MemoryPattern {
    id: string;
    pattern: string;
    frequency: number;
    examples: MemoryEntry[];
    extractedAt: number;
}

export interface MemoryCluster {
    centroid: number[];
    members: MemoryEntry[];
    label?: string;
    coherence: number;
}

export interface CodePattern {
    id: string;
    language: string;
    pattern: string;
    description: string;
    usage: string[];
    examples: CodeExample[];
    successRate: number;
    lastUsed: number;
}

export interface CodeExample {
    code: string;
    context: string;
    outcome: 'success' | 'failure' | 'partial';
    feedback?: string;
}

export interface ArchitecturePattern {
    id: string;
    name: string;
    type: 'microservices' | 'monolith' | 'serverless' | 'hybrid' | 'other';
    description: string;
    components: ArchitectureComponent[];
    useCases: string[];
    pros: string[];
    cons: string[];
    diagram?: string;
}

export interface ArchitectureComponent {
    name: string;
    responsibility: string;
    technologies: string[];
    interfaces: string[];
    dependencies: string[];
}

export interface TaskMemory {
    taskId: string;
    description: string;
    decomposition: TaskStep[];
    outcome: TaskOutcome;
    duration: number;
    agentsInvolved: string[];
    lessonsLearned: string[];
}

export interface TaskStep {
    stepId: string;
    description: string;
    assignedAgent: string;
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
    output?: any;
    dependencies: string[];
}

export interface TaskOutcome {
    status: 'success' | 'partial' | 'failure';
    quality: number; // 0-1
    feedback?: string;
    improvements?: string[];
}

export interface ConversationMemory {
    conversationId: string;
    participants: string[];
    messages: Message[];
    context: Map<string, any>;
    summary?: string;
    keyDecisions: Decision[];
    timestamp: number;
}

export interface Message {
    id: string;
    sender: string;
    content: string;
    timestamp: number;
    intent?: string;
    entities?: Entity[];
}

export interface Entity {
    type: string;
    value: string;
    confidence: number;
}

export interface Decision {
    id: string;
    description: string;
    madeBy: string;
    reasoning: string;
    alternatives: string[];
    outcome?: string;
    timestamp: number;
}

export interface LearningEntry {
    id: string;
    type: 'success' | 'failure' | 'insight';
    description: string;
    context: any;
    impact: 'high' | 'medium' | 'low';
    applicability: string[];
    timestamp: number;
}

export interface MemoryStats {
    totalMemories: number;
    byType: Map<MemoryType, number>;
    byAgent: Map<string, number>;
    averageAccessCount: number;
    mostAccessedMemories: MemoryEntry[];
    memoryGrowthRate: number;
    patternCount: number;
    clusterCount: number;
}