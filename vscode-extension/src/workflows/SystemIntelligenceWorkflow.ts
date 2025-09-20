/**
 * System Intelligence Workflow - Orchestrates system analysis and continuous learning
 * This workflow coordinates agents to build and maintain a comprehensive understanding
 * of the codebase, learn from patterns, and improve over time.
 */

import * as vscode from 'vscode';
import {
    SystemKnowledge,
    ArchitectureModel,
    FunctionInventory,
    SystemAnalysisResult,
    Component,
    FunctionSignature,
    ArchitecturePattern,
    CodeHotspot,
    SuccessPattern,
    FailurePattern,
    UserPreference,
    LearningRepository,
    SystemMetadata,
    ComponentMap,
    DependencyGraph,
    FunctionCallGraph,
    ModuleStructure,
    ComplexityScore,
    CodePattern,
    OptimizationPattern
} from '../types/SystemKnowledge';
import { SystemMemoryStore, SystemMemoryConfig } from '../memory/SystemMemory';
import { VSCodeMasterDispatcher } from '../core/VSCodeMasterDispatcher';
import { SharedContextManager, getSharedContext } from '../core/SharedContextManager';
import { AgentCommunicationBus, getCommunicationBus, MessageType } from '../core/AgentCommunicationBus';
import { WorkflowEngine } from '../core/WorkflowEngine';
import { TaskRequest, TaskResult, WorkflowStep, WorkspaceContext } from '../types';

/**
 * Configuration for system intelligence workflow
 */
export interface SystemIntelligenceConfig {
    autoAnalyze: boolean;
    continuousLearning: boolean;
    analysisDepth: 'shallow' | 'normal' | 'deep';
    patternExtractionThreshold: number;
    updateInterval: number; // ms
    memoryConfig: SystemMemoryConfig;
}

/**
 * Main workflow for system intelligence
 */
export class SystemIntelligenceWorkflow {
    private systemMemory: SystemMemoryStore;
    private dispatcher: VSCodeMasterDispatcher;
    private sharedContext: SharedContextManager;
    private communicationBus: AgentCommunicationBus;
    private workflowEngine: WorkflowEngine;
    private config: SystemIntelligenceConfig;
    private isAnalyzing: boolean = false;
    private analysisSession: string | null = null;
    private continuousLearningTimer: NodeJS.Timeout | null = null;
    private outputChannel: vscode.OutputChannel;

    constructor(
        dispatcher: VSCodeMasterDispatcher,
        config: SystemIntelligenceConfig
    ) {
        this.dispatcher = dispatcher;
        this.config = config;
        this.systemMemory = new SystemMemoryStore(config.memoryConfig);
        this.sharedContext = getSharedContext();
        this.communicationBus = getCommunicationBus();
        this.workflowEngine = new WorkflowEngine();
        this.outputChannel = vscode.window.createOutputChannel('System Intelligence');

        // Start continuous learning if enabled
        if (config.continuousLearning) {
            this.startContinuousLearning();
        }
    }

    /**
     * Initialize system understanding - called on extension activation
     */
    public async initializeSystemUnderstanding(): Promise<SystemAnalysisResult> {
        if (this.isAnalyzing) {
            throw new Error('Analysis already in progress');
        }

        this.isAnalyzing = true;
        this.analysisSession = this.generateSessionId();
        this.outputChannel.show();
        this.outputChannel.appendLine('🧠 Starting System Intelligence Analysis...');

        try {
            // Check if we have existing knowledge
            const existingKnowledge = this.systemMemory.getSystemKnowledge();
            if (existingKnowledge && !this.shouldReanalyze(existingKnowledge)) {
                this.outputChannel.appendLine('✅ Using existing system knowledge (up to date)');
                return this.createAnalysisResult(existingKnowledge);
            }

            // Start collaboration session
            const session = await this.communicationBus.startCollaboration(
                {
                    task: 'System Analysis',
                    goal: 'Build comprehensive understanding of the codebase'
                },
                ['architect', 'codesmith', 'docu', 'reviewer'],
                'orchestrator'
            );

            this.outputChannel.appendLine(`📋 Collaboration session started: ${session.id}`);

            // Phase 1: Architecture Analysis
            this.outputChannel.appendLine('\n📐 Phase 1: Architecture Analysis');
            const architecture = await this.analyzeArchitecture();

            // Phase 2: Function Inventory
            this.outputChannel.appendLine('\n🔧 Phase 2: Function Inventory');
            const functions = await this.analyzeFunctions();

            // Phase 3: Pattern Extraction
            this.outputChannel.appendLine('\n🔍 Phase 3: Pattern Extraction');
            const learnings = await this.extractPatterns(architecture, functions);

            // Phase 4: System Metadata
            this.outputChannel.appendLine('\n📊 Phase 4: System Metadata');
            const metadata = await this.gatherMetadata();

            // Phase 5: Quality Analysis
            this.outputChannel.appendLine('\n✨ Phase 5: Quality Analysis');
            const insights = await this.analyzeQuality(architecture, functions);

            // Combine into system knowledge
            const knowledge: SystemKnowledge = {
                architecture,
                functions,
                learnings,
                metadata
            };

            // Store in memory
            await this.systemMemory.storeSystemKnowledge(knowledge);

            // Share with all agents
            await this.shareKnowledge(knowledge);

            // Generate documentation
            await this.generateDocumentation(knowledge);

            // Complete collaboration
            const resultsMap = new Map<string, any>();
            resultsMap.set('knowledge', knowledge);
            await this.communicationBus.completeCollaboration(session.id, resultsMap);

            this.outputChannel.appendLine('\n✅ System Intelligence Analysis Complete!');

            const result = this.createAnalysisResult(knowledge);
            return result;

        } finally {
            this.isAnalyzing = false;
            this.analysisSession = null;
        }
    }

    /**
     * Analyze system architecture
     */
    private async analyzeArchitecture(): Promise<ArchitectureModel> {
        this.outputChannel.appendLine('  → Requesting architecture analysis from ArchitectAgent...');

        const request: TaskRequest = {
            prompt: `Analyze the complete architecture of this codebase. Include:
            1. Component identification and classification
            2. Dependency mapping and analysis
            3. Architectural patterns detection
            4. Layer identification and violations
            5. Module structure analysis
            6. Quality metrics calculation

            Return a comprehensive ArchitectureModel structure.

            Analysis depth: ${this.config.analysisDepth}
            Session ID: ${this.analysisSession}`
        };

        const workflow: WorkflowStep[] = [
            { id: 'analyze-architecture', agent: 'architect', description: 'Analyze system architecture' }
        ];

        const result = await this.dispatcher.executeWorkflow(workflow, request);

        if (result.status !== 'success') {
            throw new Error(`Architecture analysis failed: ${result.content}`);
        }

        // Parse the result into ArchitectureModel
        const architecture = this.parseArchitectureResult(result);

        this.outputChannel.appendLine(`  ✓ Found ${Object.keys(architecture.components).length} components`);
        this.outputChannel.appendLine(`  ✓ Detected ${architecture.patterns.length} patterns`);
        this.outputChannel.appendLine(`  ✓ Identified ${architecture.layers.length} layers`);

        return architecture;
    }

    /**
     * Analyze functions and create inventory
     */
    private async analyzeFunctions(): Promise<FunctionInventory> {
        this.outputChannel.appendLine('  → Requesting function analysis from CodeSmithAgent...');

        const request: TaskRequest = {
            prompt: `Analyze all functions in the codebase. Include:
            1. Complete function signatures and metadata
            2. Complexity analysis for each function
            3. Call graph construction
            4. Category classification
            5. Hotspot identification
            6. Duplicate detection

            Return a comprehensive FunctionInventory structure.

            Analysis depth: ${this.config.analysisDepth}
            Session ID: ${this.analysisSession}`
        };

        const workflow: WorkflowStep[] = [
            { id: 'analyze-functions', agent: 'codesmith', description: 'Analyze all functions' }
        ];

        const result = await this.dispatcher.executeWorkflow(workflow, request);

        if (result.status !== 'success') {
            throw new Error(`Function analysis failed: ${result.content}`);
        }

        // Parse the result into FunctionInventory
        const inventory = this.parseFunctionResult(result);

        const totalFunctions = Object.values(inventory.byModule).flat().length;
        this.outputChannel.appendLine(`  ✓ Analyzed ${totalFunctions} functions`);
        this.outputChannel.appendLine(`  ✓ Found ${inventory.hotspots.length} hotspots`);
        this.outputChannel.appendLine(`  ✓ Built call graph with ${inventory.callGraph.nodes.length} nodes`);

        return inventory;
    }

    /**
     * Extract patterns from analysis
     */
    private async extractPatterns(
        architecture: ArchitectureModel,
        functions: FunctionInventory
    ): Promise<LearningRepository> {
        this.outputChannel.appendLine('  → Extracting patterns and learnings...');

        // Initialize repository
        const learnings: LearningRepository = {
            successPatterns: [],
            failurePatterns: [],
            userPreferences: [],
            optimizations: [],
            codePatterns: [],
            workflowPatterns: []
        };

        // Extract architecture patterns as success patterns
        for (const pattern of architecture.patterns) {
            if (pattern.quality > this.config.patternExtractionThreshold) {
                learnings.successPatterns.push({
                    id: `arch_${pattern.id}`,
                    name: pattern.name,
                    description: `Architectural pattern: ${pattern.name}`,
                    context: 'architecture',
                    solution: pattern.instances[0]?.implementation || '',
                    occurrences: pattern.frequency,
                    successRate: pattern.quality,
                    lastUsed: new Date(),
                    applicableScenarios: pattern.instances.map(i => i.location),
                    benefits: pattern.benefits,
                    examples: pattern.instances.map(i => ({
                        code: i.implementation,
                        description: `Instance at ${i.location}`,
                        context: 'architecture',
                        result: `Effectiveness: ${i.effectiveness}`
                    }))
                });
            }
        }

        // Extract common function patterns
        const functionPatterns = this.extractFunctionPatterns(functions);
        learnings.codePatterns.push(...functionPatterns);

        // Extract optimization opportunities
        const optimizations = this.identifyOptimizations(functions);
        learnings.optimizations.push(...optimizations);

        this.outputChannel.appendLine(`  ✓ Extracted ${learnings.successPatterns.length} success patterns`);
        this.outputChannel.appendLine(`  ✓ Found ${learnings.codePatterns.length} code patterns`);
        this.outputChannel.appendLine(`  ✓ Identified ${learnings.optimizations.length} optimizations`);

        return learnings;
    }

    /**
     * Extract function patterns
     */
    private extractFunctionPatterns(inventory: FunctionInventory): CodePattern[] {
        const patterns: CodePattern[] = [];
        const functionGroups = new Map<string, FunctionSignature[]>();

        // Group functions by category
        for (const functions of Object.values(inventory.byModule)) {
            for (const func of functions) {
                const key = `${func.category}_${func.parameters.length}_${func.async}`;
                if (!functionGroups.has(key)) {
                    functionGroups.set(key, []);
                }
                functionGroups.get(key)!.push(func);
            }
        }

        // Extract patterns from groups
        for (const [key, functions] of functionGroups.entries()) {
            if (functions.length >= 3) {
                // Common pattern found
                const [category, paramCount, isAsync] = key.split('_');
                patterns.push({
                    id: `func_pattern_${key}`,
                    name: `${category} function pattern`,
                    category,
                    template: this.generateFunctionTemplate(functions[0]),
                    parameters: functions[0].parameters.map(p => ({
                        name: p.name,
                        type: p.type,
                        description: p.description || '',
                        example: ''
                    })),
                    usage: functions.map(f => ({
                        location: f.path,
                        timestamp: new Date(),
                        success: true,
                        modifications: []
                    })),
                    effectiveness: 0.8,
                    tags: [category, isAsync === 'true' ? 'async' : 'sync']
                });
            }
        }

        return patterns;
    }

    /**
     * Identify optimization opportunities
     */
    private identifyOptimizations(inventory: FunctionInventory): OptimizationPattern[] {
        const optimizations: OptimizationPattern[] = [];

        // Find complex functions that could be simplified
        for (const func of inventory.metrics.mostComplex) {
            if (func.complexity.cyclomatic > 15) {
                optimizations.push({
                    id: `opt_simplify_${func.id}`,
                    name: `Simplify ${func.name}`,
                    type: 'complexity',
                    before: func.signature,
                    after: 'Break into smaller functions',
                    improvement: Math.min(50, func.complexity.cyclomatic * 2),
                    applicability: [func.path],
                    tradeoffs: ['May increase total lines of code', 'Requires refactoring tests']
                });
            }
        }

        // Find duplicates that could be merged
        for (const group of inventory.metrics.duplicates) {
            if (group.similarity > 0.9) {
                optimizations.push({
                    id: `opt_merge_${group.functions[0]}`,
                    name: `Merge duplicate functions`,
                    type: 'complexity',
                    before: `${group.functions.length} duplicate functions`,
                    after: 'Single reusable function',
                    improvement: (group.functions.length - 1) * 100 / group.functions.length,
                    applicability: group.functions,
                    tradeoffs: ['May need parameter adjustment']
                });
            }
        }

        return optimizations;
    }

    /**
     * Gather system metadata
     */
    private async gatherMetadata(): Promise<SystemMetadata> {
        this.outputChannel.appendLine('  → Gathering system metadata...');

        const workspace = vscode.workspace.workspaceFolders?.[0];
        if (!workspace) {
            throw new Error('No workspace folder found');
        }

        // Get file statistics
        const files = await vscode.workspace.findFiles('**/*.{ts,js,tsx,jsx,py,java,go,rs}', '**/node_modules/**');

        // Detect languages
        const languages = new Set<string>();
        for (const file of files) {
            const ext = file.path.split('.').pop();
            if (ext) {
                languages.add(this.mapExtensionToLanguage(ext));
            }
        }

        // Create metadata
        const metadata: SystemMetadata = {
            version: '1.0.0',
            lastFullAnalysis: new Date(),
            lastUpdate: new Date(),
            totalFiles: files.length,
            totalFunctions: 0, // Will be updated from function inventory
            totalComponents: 0, // Will be updated from architecture
            language: Array.from(languages),
            frameworks: await this.detectFrameworks(),
            testCoverage: {
                lines: 0,
                branches: 0,
                functions: 0,
                statements: 0
            },
            buildSystem: await this.detectBuildSystem(),
            repository: {
                url: '',
                branch: 'main',
                lastCommit: '',
                contributors: 0
            }
        };

        this.outputChannel.appendLine(`  ✓ Found ${metadata.totalFiles} files`);
        this.outputChannel.appendLine(`  ✓ Languages: ${metadata.language.join(', ')}`);
        this.outputChannel.appendLine(`  ✓ Build system: ${metadata.buildSystem}`);

        return metadata;
    }

    /**
     * Analyze system quality
     */
    private async analyzeQuality(
        architecture: ArchitectureModel,
        functions: FunctionInventory
    ): Promise<any> {
        this.outputChannel.appendLine('  → Requesting quality analysis from ReviewerGPT...');

        const request: TaskRequest = {
            prompt: `Review the system quality based on:
            Architecture: ${JSON.stringify(architecture.quality)}
            Functions: ${JSON.stringify(functions.metrics)}
            Hotspots: ${JSON.stringify(functions.hotspots)}

            Provide insights, recommendations, risks, and opportunities.

            Session ID: ${this.analysisSession}`
        };

        const workflow: WorkflowStep[] = [
            { id: 'review-quality', agent: 'reviewer', description: 'Review system quality' }
        ];

        const result = await this.dispatcher.executeWorkflow(workflow, request);

        if (result.status !== 'success') {
            this.outputChannel.appendLine('  ⚠️ Quality analysis failed, using defaults');
            return {
                insights: [],
                recommendations: [],
                risks: [],
                opportunities: []
            };
        }

        return this.parseQualityResult(result);
    }

    /**
     * Start continuous learning
     */
    public startContinuousLearning(): void {
        if (this.continuousLearningTimer) {
            return;
        }

        this.continuousLearningTimer = setInterval(
            () => this.continuousLearningCycle(),
            this.config.updateInterval
        );

        this.outputChannel.appendLine('🔄 Continuous learning started');
    }

    /**
     * Stop continuous learning
     */
    public stopContinuousLearning(): void {
        if (this.continuousLearningTimer) {
            clearInterval(this.continuousLearningTimer);
            this.continuousLearningTimer = null;
            this.outputChannel.appendLine('⏹️ Continuous learning stopped');
        }
    }

    /**
     * Continuous learning cycle
     */
    private async continuousLearningCycle(): Promise<void> {
        try {
            const knowledge = this.systemMemory.getSystemKnowledge();
            if (!knowledge) {
                return;
            }

            // Check for file changes
            const changes = await this.detectChanges(knowledge);
            if (changes.length === 0) {
                return;
            }

            this.outputChannel.appendLine(`🔄 Detected ${changes.length} changes, updating knowledge...`);

            // Perform delta analysis
            const deltaKnowledge = await this.performDeltaAnalysis(changes);

            // Extract patterns from changes
            await this.extractPatternsFromChanges(changes);

            // Update memory
            if (deltaKnowledge.architecture) {
                await this.systemMemory.updateArchitecture(deltaKnowledge.architecture);
            }
            if (deltaKnowledge.functions) {
                await this.systemMemory.updateFunctionInventory(deltaKnowledge.functions);
            }

            // Share updates with agents
            await this.shareKnowledgeUpdate(deltaKnowledge);

            this.outputChannel.appendLine('✓ Knowledge updated successfully');

        } catch (error) {
            this.outputChannel.appendLine(`⚠️ Continuous learning error: ${error}`);
        }
    }

    /**
     * Detect changes since last analysis
     */
    private async detectChanges(knowledge: SystemKnowledge): Promise<vscode.Uri[]> {
        const changes: vscode.Uri[] = [];
        const lastAnalysis = knowledge.metadata.lastUpdate;

        const files = await vscode.workspace.findFiles('**/*.{ts,js,tsx,jsx}', '**/node_modules/**');

        for (const file of files) {
            const stat = await vscode.workspace.fs.stat(file);
            if (stat.mtime > lastAnalysis.getTime()) {
                changes.push(file);
            }
        }

        return changes;
    }

    /**
     * Perform delta analysis on changes
     */
    private async performDeltaAnalysis(changes: vscode.Uri[]): Promise<Partial<SystemKnowledge>> {
        const updates: Partial<SystemKnowledge> = {};

        // Analyze changed files
        const request: TaskRequest = {
            prompt: `Analyze the following changed files and update system knowledge:
            ${changes.map(c => c.fsPath).join('\n')}

            Provide delta updates for architecture and functions.

            Current knowledge components: ${this.systemMemory.getSystemKnowledge()?.architecture ? Object.keys(this.systemMemory.getSystemKnowledge()!.architecture.components).length : 0}`
        };

        const architectWorkflow: WorkflowStep[] = [
            { id: 'delta-architecture', agent: 'architect', description: 'Analyze architecture changes' }
        ];
        const functionWorkflow: WorkflowStep[] = [
            { id: 'delta-functions', agent: 'codesmith', description: 'Analyze function changes' }
        ];

        const architectResult = await this.dispatcher.executeWorkflow(architectWorkflow, request);
        const functionResult = await this.dispatcher.executeWorkflow(functionWorkflow, request);

        if (architectResult.status === 'success') {
            updates.architecture = this.parseArchitectureResult(architectResult);
        }

        if (functionResult.status === 'success') {
            updates.functions = this.parseFunctionResult(functionResult);
        }

        return updates;
    }

    /**
     * Extract patterns from changes
     */
    private async extractPatternsFromChanges(changes: vscode.Uri[]): Promise<void> {
        // Track modification patterns
        for (const change of changes) {
            const path = change.fsPath;
            const component = this.systemMemory.findComponent(path);

            if (component) {
                // Track as user preference
                const preference: UserPreference = {
                    id: `pref_modify_${component.type}`,
                    category: 'structure',
                    preference: `Frequently modifies ${component.type} components`,
                    examples: [path],
                    confidence: 0.6,
                    frequency: 1,
                    lastObserved: new Date()
                };

                await this.systemMemory.trackUserPreference(preference);
            }
        }
    }

    /**
     * Share knowledge with all agents
     */
    private async shareKnowledge(knowledge: SystemKnowledge): Promise<void> {
        this.outputChannel.appendLine('\n📢 Sharing knowledge with all agents...');

        // Update shared context
        await this.sharedContext.updateContext(
            'system',
            'architecture',
            knowledge.architecture,
            { version: knowledge.architecture.version }
        );

        await this.sharedContext.updateContext(
            'system',
            'functions',
            knowledge.functions,
            { totalFunctions: Object.values(knowledge.functions.byModule).flat().length }
        );

        await this.sharedContext.updateContext(
            'system',
            'patterns',
            knowledge.learnings,
            { patternCount: knowledge.learnings.successPatterns.length }
        );

        // Broadcast to all agents
        await this.communicationBus.broadcast(
            'system',
            MessageType.STATUS_UPDATE,
            {
                event: 'system_knowledge_updated',
                knowledge: {
                    components: Object.keys(knowledge.architecture.components).length,
                    functions: Object.values(knowledge.functions.byModule).flat().length,
                    patterns: knowledge.learnings.successPatterns.length
                }
            }
        );

        this.outputChannel.appendLine('  ✓ Knowledge shared with all agents');
    }

    /**
     * Share knowledge update
     */
    private async shareKnowledgeUpdate(update: Partial<SystemKnowledge>): Promise<void> {
        await this.communicationBus.broadcast(
            'system',
            MessageType.STATUS_UPDATE,
            {
                event: 'system_knowledge_delta',
                update
            }
        );
    }

    /**
     * Generate documentation
     */
    private async generateDocumentation(knowledge: SystemKnowledge): Promise<void> {
        this.outputChannel.appendLine('\n📝 Generating documentation...');

        const request: TaskRequest = {
            prompt: `Generate comprehensive documentation for the system based on the analysis:
            - Architecture overview with ${Object.keys(knowledge.architecture.components).length} components
            - Function inventory with ${Object.values(knowledge.functions.byModule).flat().length} functions
            - ${knowledge.learnings.successPatterns.length} identified patterns
            - ${knowledge.functions.hotspots.length} hotspots requiring attention

            Create README.md and ARCHITECTURE.md files.

            Session ID: ${this.analysisSession}`
        };

        const workflow: WorkflowStep[] = [
            { id: 'generate-docs', agent: 'docu', description: 'Generate documentation' }
        ];

        const result = await this.dispatcher.executeWorkflow(workflow, request);

        if (result.status === 'success') {
            this.outputChannel.appendLine('  ✓ Documentation generated successfully');
        } else {
            this.outputChannel.appendLine('  ⚠️ Documentation generation failed');
        }
    }

    /**
     * Check if reanalysis is needed
     */
    private shouldReanalyze(knowledge: SystemKnowledge): boolean {
        const daysSinceAnalysis = (new Date().getTime() - knowledge.metadata.lastFullAnalysis.getTime()) / (1000 * 60 * 60 * 24);
        return daysSinceAnalysis > 7; // Reanalyze weekly
    }

    /**
     * Create analysis result
     */
    private createAnalysisResult(knowledge: SystemKnowledge): SystemAnalysisResult {
        return {
            knowledge,
            insights: [],
            recommendations: [],
            risks: [],
            opportunities: [],
            timestamp: new Date(),
            duration: 0
        };
    }

    /**
     * Parse architecture result from agent
     */
    private parseArchitectureResult(result: TaskResult): ArchitectureModel {
        // In production, this would parse the actual agent response
        // For now, return a structured result
        try {
            const parsed = JSON.parse(result.content);
            return parsed as ArchitectureModel;
        } catch {
            // Fallback to default structure
            return {
                components: {},
                dependencies: {
                    nodes: [],
                    edges: [],
                    cycles: [],
                    metrics: {
                        totalDependencies: 0,
                        maxDepth: 0,
                        avgDependenciesPerComponent: 0,
                        circularDependencies: 0,
                        stabilityIndex: 0
                    }
                },
                patterns: [],
                layers: [],
                modules: [],
                version: '1.0.0',
                lastAnalysis: new Date(),
                quality: {
                    maintainability: 75,
                    reliability: 80,
                    security: 70,
                    performance: 85,
                    testability: 60,
                    documentation: 50,
                    overall: 70,
                    trend: 'stable',
                    issues: []
                }
            };
        }
    }

    /**
     * Parse function result from agent
     */
    private parseFunctionResult(result: TaskResult): FunctionInventory {
        try {
            const parsed = JSON.parse(result.content);
            return parsed as FunctionInventory;
        } catch {
            // Fallback to default structure
            return {
                byModule: {},
                byCategory: {},
                byComplexity: {
                    simple: [],
                    moderate: [],
                    complex: [],
                    critical: []
                },
                callGraph: {
                    nodes: [],
                    edges: [],
                    clusters: [],
                    entryPoints: [],
                    hotPaths: []
                },
                metrics: {
                    total: 0,
                    byComplexity: {
                        simple: 0,
                        moderate: 0,
                        complex: 0,
                        critical: 0
                    },
                    averageComplexity: 0,
                    mostComplex: [],
                    mostCalled: [],
                    unused: [],
                    duplicates: []
                },
                hotspots: []
            };
        }
    }

    /**
     * Parse quality result from agent
     */
    private parseQualityResult(result: TaskResult): any {
        try {
            return JSON.parse(result.content);
        } catch {
            return {
                insights: [],
                recommendations: [],
                risks: [],
                opportunities: []
            };
        }
    }

    /**
     * Generate function template
     */
    private generateFunctionTemplate(func: FunctionSignature): string {
        const params = func.parameters.map(p => `${p.name}: ${p.type}`).join(', ');
        return `${func.async ? 'async ' : ''}function ${func.name}(${params}): ${func.returnType} { }`;
    }

    /**
     * Map extension to language
     */
    private mapExtensionToLanguage(ext: string): string {
        const mapping: Record<string, string> = {
            'ts': 'TypeScript',
            'tsx': 'TypeScript',
            'js': 'JavaScript',
            'jsx': 'JavaScript',
            'py': 'Python',
            'java': 'Java',
            'go': 'Go',
            'rs': 'Rust'
        };
        return mapping[ext] || ext;
    }

    /**
     * Detect frameworks
     */
    private async detectFrameworks(): Promise<any[]> {
        const frameworks: any[] = [];

        // Check package.json for Node.js projects
        const packageJson = await vscode.workspace.findFiles('**/package.json', '**/node_modules/**', 1);
        if (packageJson.length > 0) {
            frameworks.push({ name: 'Node.js', version: 'latest', usage: 'core' });
        }

        return frameworks;
    }

    /**
     * Detect build system
     */
    private async detectBuildSystem(): Promise<string> {
        const files = await vscode.workspace.findFiles('**/{webpack.config.js,vite.config.js,rollup.config.js,tsconfig.json}', '**/node_modules/**', 1);

        if (files.length > 0) {
            const filename = files[0].path.split('/').pop();
            if (filename?.includes('webpack')) return 'webpack';
            if (filename?.includes('vite')) return 'vite';
            if (filename?.includes('rollup')) return 'rollup';
            if (filename?.includes('tsconfig')) return 'TypeScript';
        }

        return 'unknown';
    }

    /**
     * Generate session ID
     */
    private generateSessionId(): string {
        return `analysis_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Get workflow statistics
     */
    public getStatistics(): any {
        return {
            memoryStats: this.systemMemory.getStatistics(),
            isAnalyzing: this.isAnalyzing,
            continuousLearning: this.continuousLearningTimer !== null,
            sessionId: this.analysisSession
        };
    }
}