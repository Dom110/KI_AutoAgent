/**
 * System Knowledge Types - Core data structures for system understanding and learning
 * These types enable the multi-agent system to build and maintain a comprehensive
 * understanding of the codebase, learn from patterns, and improve over time.
 */

import { MemoryType } from './Memory';

/**
 * Complete system knowledge including architecture, functions, and learned patterns
 */
export interface SystemKnowledge {
    architecture: ArchitectureModel;
    functions: FunctionInventory;
    learnings: LearningRepository;
    metadata: SystemMetadata;
}

/**
 * Comprehensive architecture model of the system
 */
export interface ArchitectureModel {
    components: ComponentMap;
    dependencies: DependencyGraph;
    patterns: ArchitecturePattern[];
    layers: SystemLayer[];
    modules: ModuleStructure[];
    version: string;
    lastAnalysis: Date;
    quality: QualityMetrics;
}

/**
 * Map of system components
 */
export interface ComponentMap {
    [componentId: string]: Component;
}

export interface Component {
    id: string;
    name: string;
    type: 'class' | 'interface' | 'module' | 'service' | 'utility' | 'component';
    path: string;
    description: string;
    responsibilities: string[];
    dependencies: string[];
    exports: ExportedItem[];
    complexity: ComplexityScore;
    lastModified: Date;
}

/**
 * Dependency relationships between components
 */
export interface DependencyGraph {
    nodes: DependencyNode[];
    edges: DependencyEdge[];
    cycles: DependencyCycle[];
    metrics: DependencyMetrics;
}

export interface DependencyNode {
    id: string;
    componentId: string;
    type: string;
    weight: number;
}

export interface DependencyEdge {
    from: string;
    to: string;
    type: 'import' | 'inherit' | 'implement' | 'use' | 'compose';
    strength: 'strong' | 'weak' | 'optional';
}

export interface DependencyCycle {
    nodes: string[];
    severity: 'low' | 'medium' | 'high';
    suggestion: string;
}

/**
 * Architectural patterns detected in the system
 */
export interface ArchitecturePattern {
    id: string;
    name: string;
    type: 'structural' | 'behavioral' | 'creational' | 'architectural';
    instances: PatternInstance[];
    benefits: string[];
    drawbacks: string[];
    frequency: number;
    quality: number; // 0-1
}

export interface PatternInstance {
    location: string;
    components: string[];
    implementation: string;
    effectiveness: number; // 0-1
}

/**
 * System layers and their relationships
 */
export interface SystemLayer {
    name: string;
    level: number;
    components: string[];
    allowedDependencies: string[]; // Which layers can this depend on
    violations: LayerViolation[];
}

export interface LayerViolation {
    from: string;
    to: string;
    severity: 'warning' | 'error';
    suggestion: string;
}

/**
 * Complete function inventory of the system
 */
export interface FunctionInventory {
    byModule: ModuleFunctionMap;
    byCategory: CategoryFunctionMap;
    byComplexity: ComplexityFunctionMap;
    callGraph: FunctionCallGraph;
    metrics: FunctionMetrics;
    hotspots: CodeHotspot[];
}

export interface ModuleFunctionMap {
    [modulePath: string]: FunctionSignature[];
}

export interface CategoryFunctionMap {
    [category: string]: FunctionSignature[];
}

export interface ComplexityFunctionMap {
    simple: FunctionSignature[];
    moderate: FunctionSignature[];
    complex: FunctionSignature[];
    critical: FunctionSignature[];
}

/**
 * Detailed function signature and metadata
 */
export interface FunctionSignature {
    id: string;
    name: string;
    path: string;
    module: string;
    signature: string;
    parameters: Parameter[];
    returnType: string;
    async: boolean;
    generator: boolean;
    complexity: ComplexityScore;
    category: string;
    purpose: string;
    sideEffects: string[];
    tests: TestCoverage;
    lastModified: Date;
    modificationFrequency: number;
}

export interface Parameter {
    name: string;
    type: string;
    optional: boolean;
    default?: any;
    description?: string;
}

export interface ComplexityScore {
    cyclomatic: number;
    cognitive: number;
    lines: number;
    parameters: number;
    dependencies: number;
    overall: 'simple' | 'moderate' | 'complex' | 'critical';
}

/**
 * Function call relationships
 */
export interface FunctionCallGraph {
    nodes: CallNode[];
    edges: CallEdge[];
    clusters: CallCluster[];
    entryPoints: string[];
    hotPaths: CallPath[];
}

export interface CallNode {
    functionId: string;
    calls: number;
    calledBy: number;
    isRecursive: boolean;
}

export interface CallEdge {
    from: string;
    to: string;
    count: number;
    async: boolean;
}

export interface CallCluster {
    id: string;
    functions: string[];
    cohesion: number;
    coupling: number;
}

export interface CallPath {
    path: string[];
    frequency: number;
    performance: number;
}

/**
 * Code quality hotspots that need attention
 */
export interface CodeHotspot {
    location: string;
    type: 'complexity' | 'duplication' | 'debt' | 'performance' | 'security';
    severity: 'low' | 'medium' | 'high' | 'critical';
    description: string;
    suggestion: string;
    effort: number; // hours to fix
}

/**
 * Repository of learned patterns and knowledge
 */
export interface LearningRepository {
    successPatterns: SuccessPattern[];
    failurePatterns: FailurePattern[];
    userPreferences: UserPreference[];
    optimizations: OptimizationPattern[];
    codePatterns: CodePattern[];
    workflowPatterns: WorkflowPattern[];
}

/**
 * Patterns that led to successful outcomes
 */
export interface SuccessPattern {
    id: string;
    name: string;
    description: string;
    context: string;
    solution: string;
    occurrences: number;
    successRate: number;
    lastUsed: Date;
    applicableScenarios: string[];
    benefits: string[];
    examples: PatternExample[];
}

/**
 * Patterns that led to failures (to avoid)
 */
export interface FailurePattern {
    id: string;
    name: string;
    description: string;
    context: string;
    problem: string;
    occurrences: number;
    severity: 'low' | 'medium' | 'high';
    consequences: string[];
    alternatives: string[];
    lastSeen: Date;
}

/**
 * Learned user preferences and patterns
 */
export interface UserPreference {
    id: string;
    category: 'style' | 'architecture' | 'naming' | 'structure' | 'workflow';
    preference: string;
    examples: string[];
    confidence: number; // 0-1
    frequency: number;
    lastObserved: Date;
}

/**
 * Performance optimization patterns
 */
export interface OptimizationPattern {
    id: string;
    name: string;
    type: 'performance' | 'memory' | 'complexity' | 'readability';
    before: string;
    after: string;
    improvement: number; // percentage
    applicability: string[];
    tradeoffs: string[];
}

/**
 * Reusable code patterns
 */
export interface CodePattern {
    id: string;
    name: string;
    category: string;
    template: string;
    parameters: PatternParameter[];
    usage: CodePatternUsage[];
    effectiveness: number;
    tags: string[];
}

export interface PatternParameter {
    name: string;
    type: string;
    description: string;
    example: string;
}

export interface CodePatternUsage {
    location: string;
    timestamp: Date;
    success: boolean;
    modifications: string[];
}

/**
 * Workflow patterns for common tasks
 */
export interface WorkflowPattern {
    id: string;
    name: string;
    trigger: string;
    steps: WorkflowStep[];
    agents: string[];
    averageDuration: number;
    successRate: number;
    lastExecuted: Date;
}

export interface WorkflowStep {
    order: number;
    agent: string;
    action: string;
    input: any;
    expectedOutput: any;
    alternatives: string[];
}

/**
 * Pattern examples for reference
 */
export interface PatternExample {
    code: string;
    description: string;
    context: string;
    result: string;
}

/**
 * System metadata and versioning
 */
export interface SystemMetadata {
    version: string;
    lastFullAnalysis: Date;
    lastUpdate: Date;
    totalFiles: number;
    totalFunctions: number;
    totalComponents: number;
    language: string[];
    frameworks: Framework[];
    testCoverage: TestCoverage;
    buildSystem: string;
    repository: RepositoryInfo;
}

export interface Framework {
    name: string;
    version: string;
    usage: 'core' | 'utility' | 'testing' | 'build';
}

export interface TestCoverage {
    lines: number;
    branches: number;
    functions: number;
    statements: number;
}

export interface RepositoryInfo {
    url: string;
    branch: string;
    lastCommit: string;
    contributors: number;
}

/**
 * Module structure information
 */
export interface ModuleStructure {
    path: string;
    name: string;
    type: 'core' | 'feature' | 'utility' | 'test' | 'config';
    exports: ExportedItem[];
    imports: ImportedItem[];
    internalDependencies: string[];
    externalDependencies: string[];
    metrics: ModuleMetrics;
}

export interface ExportedItem {
    name: string;
    type: 'function' | 'class' | 'interface' | 'const' | 'type' | 'enum';
    isDefault: boolean;
}

export interface ImportedItem {
    name: string;
    source: string;
    type: 'named' | 'default' | 'namespace';
}

export interface ModuleMetrics {
    cohesion: number;
    coupling: number;
    instability: number;
    abstractness: number;
    distance: number; // from main sequence
}

/**
 * Function and dependency metrics
 */
export interface FunctionMetrics {
    total: number;
    byComplexity: ComplexityDistribution;
    averageComplexity: number;
    mostComplex: FunctionSignature[];
    mostCalled: FunctionSignature[];
    unused: FunctionSignature[];
    duplicates: DuplicateGroup[];
}

export interface ComplexityDistribution {
    simple: number;
    moderate: number;
    complex: number;
    critical: number;
}

export interface DuplicateGroup {
    functions: string[];
    similarity: number;
    suggestion: 'merge' | 'extract' | 'keep';
}

export interface DependencyMetrics {
    totalDependencies: number;
    maxDepth: number;
    avgDependenciesPerComponent: number;
    circularDependencies: number;
    stabilityIndex: number;
}

/**
 * Quality metrics for the system
 */
export interface QualityMetrics {
    maintainability: number; // 0-100
    reliability: number;
    security: number;
    performance: number;
    testability: number;
    documentation: number;
    overall: number;
    trend: 'improving' | 'stable' | 'declining';
    issues: QualityIssue[];
}

export interface QualityIssue {
    category: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    location: string;
    description: string;
    impact: string;
    effort: number; // hours to fix
    suggestion: string;
}

/**
 * System analysis result
 */
export interface SystemAnalysisResult {
    knowledge: SystemKnowledge;
    insights: AnalysisInsight[];
    recommendations: Recommendation[];
    risks: Risk[];
    opportunities: Opportunity[];
    timestamp: Date;
    duration: number; // ms
}

export interface AnalysisInsight {
    type: 'architecture' | 'performance' | 'quality' | 'pattern' | 'dependency';
    title: string;
    description: string;
    impact: 'low' | 'medium' | 'high';
    evidence: string[];
}

export interface Recommendation {
    priority: 'low' | 'medium' | 'high' | 'critical';
    category: string;
    title: string;
    description: string;
    effort: number; // hours
    impact: string;
    steps: string[];
}

export interface Risk {
    severity: 'low' | 'medium' | 'high' | 'critical';
    category: string;
    description: string;
    probability: number; // 0-1
    impact: string;
    mitigation: string;
}

export interface Opportunity {
    value: 'low' | 'medium' | 'high';
    category: string;
    description: string;
    effort: number;
    benefits: string[];
    approach: string;
}