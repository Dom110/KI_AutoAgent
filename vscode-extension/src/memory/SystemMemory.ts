/**
 * System Memory Store - Specialized memory management for system understanding
 * Manages architecture knowledge, function inventories, and learned patterns
 * with version tracking and intelligent retrieval.
 */

import {
    SystemKnowledge,
    ArchitectureModel,
    FunctionInventory,
    LearningRepository,
    SystemMetadata,
    Component,
    FunctionSignature,
    SuccessPattern,
    FailurePattern,
    UserPreference,
    CodePattern,
    WorkflowPattern,
    ArchitecturePattern,
    SystemAnalysisResult,
    CodeHotspot,
    OptimizationPattern
} from '../types/SystemKnowledge';
import { MemoryEntry, MemoryType, MemorySearchResult } from '../types/Memory';
import { MemoryManager } from '../core/MemoryManager';

/**
 * Configuration for system memory
 */
export interface SystemMemoryConfig {
    maxArchitectureVersions: number;
    maxPatternHistory: number;
    similarityThreshold: number;
    autoCompaction: boolean;
    persistToDisk: boolean;
    memoryPath?: string;
}

/**
 * Specialized memory store for system understanding
 */
export class SystemMemoryStore {
    private memoryManager: MemoryManager;
    private systemKnowledge: SystemKnowledge | null = null;
    private architectureHistory: Map<string, ArchitectureModel> = new Map();
    private functionHistory: Map<string, FunctionInventory> = new Map();
    private patternCache: Map<string, any> = new Map();
    private config: SystemMemoryConfig;
    private lastAnalysis: Date | null = null;
    private isDirty: boolean = false;

    constructor(config: SystemMemoryConfig) {
        this.config = config;
        this.memoryManager = new MemoryManager({
            maxMemories: 10000,
            similarityThreshold: config.similarityThreshold,
            patternExtractionEnabled: true
        });

        if (config.persistToDisk && config.memoryPath) {
            this.loadFromDisk(config.memoryPath);
        }
    }

    /**
     * Store complete system knowledge
     */
    public async storeSystemKnowledge(knowledge: SystemKnowledge): Promise<void> {
        // Version the architecture
        const version = this.generateVersion();
        knowledge.architecture.version = version;
        knowledge.metadata.lastUpdate = new Date();

        // Store in history
        this.architectureHistory.set(version, knowledge.architecture);
        this.functionHistory.set(version, knowledge.functions);

        // Update current knowledge
        this.systemKnowledge = knowledge;
        this.lastAnalysis = new Date();
        this.isDirty = true;

        // Store in memory manager for semantic search
        await this.memoryManager.store(
            'system',
            {
                type: 'system_knowledge',
                knowledge,
                version,
                timestamp: new Date()
            },
            MemoryType.SEMANTIC,
            { importance: 1.0 }
        );

        // Extract and store patterns
        await this.extractAndStorePatterns(knowledge);

        // Auto-compact if needed
        if (this.config.autoCompaction) {
            await this.compactHistory();
        }

        // Persist if configured
        if (this.config.persistToDisk && this.config.memoryPath) {
            await this.saveToDisk(this.config.memoryPath);
        }
    }

    /**
     * Retrieve current system knowledge
     */
    public getSystemKnowledge(): SystemKnowledge | null {
        return this.systemKnowledge;
    }

    /**
     * Update architecture model only
     */
    public async updateArchitecture(architecture: ArchitectureModel): Promise<void> {
        if (!this.systemKnowledge) {
            throw new Error('No system knowledge exists. Perform initial analysis first.');
        }

        const version = this.generateVersion();
        architecture.version = version;
        architecture.lastAnalysis = new Date();

        this.architectureHistory.set(version, architecture);
        this.systemKnowledge.architecture = architecture;
        this.isDirty = true;

        await this.memoryManager.store(
            'system',
            {
                type: 'architecture_update',
                architecture,
                version,
                timestamp: new Date()
            },
            MemoryType.EPISODIC,
            { importance: 0.8 }
        );
    }

    /**
     * Update function inventory only
     */
    public async updateFunctionInventory(inventory: FunctionInventory): Promise<void> {
        if (!this.systemKnowledge) {
            throw new Error('No system knowledge exists. Perform initial analysis first.');
        }

        const version = this.generateVersion();
        this.functionHistory.set(version, inventory);
        this.systemKnowledge.functions = inventory;
        this.isDirty = true;

        await this.memoryManager.store(
            'system',
            {
                type: 'function_update',
                inventory,
                version,
                timestamp: new Date()
            },
            MemoryType.EPISODIC,
            { importance: 0.7 }
        );
    }

    /**
     * Add a success pattern
     */
    public async addSuccessPattern(pattern: SuccessPattern): Promise<void> {
        if (!this.systemKnowledge) {
            throw new Error('No system knowledge exists.');
        }

        // Check for similar patterns
        const similar = await this.findSimilarPattern(pattern.description);
        if (similar && similar.similarity > 0.9) {
            // Update existing pattern
            const existing = this.systemKnowledge.learnings.successPatterns.find(
                p => p.id === similar.pattern.id
            );
            if (existing) {
                existing.occurrences++;
                existing.lastUsed = new Date();
                existing.successRate =
                    (existing.successRate * (existing.occurrences - 1) + 1) / existing.occurrences;
            }
        } else {
            // Add new pattern
            this.systemKnowledge.learnings.successPatterns.push(pattern);
        }

        await this.memoryManager.store(
            'system',
            {
                type: 'success_pattern',
                pattern,
                timestamp: new Date()
            },
            MemoryType.PROCEDURAL,
            { importance: 0.9 }
        );

        this.isDirty = true;
    }

    /**
     * Add a failure pattern to avoid
     */
    public async addFailurePattern(pattern: FailurePattern): Promise<void> {
        if (!this.systemKnowledge) {
            throw new Error('No system knowledge exists.');
        }

        // Check for similar failures
        const similar = await this.findSimilarPattern(pattern.description);
        if (similar && similar.similarity > 0.85) {
            // Update existing pattern
            const existing = this.systemKnowledge.learnings.failurePatterns.find(
                p => p.id === similar.pattern.id
            );
            if (existing) {
                existing.occurrences++;
                existing.lastSeen = new Date();
                if (pattern.severity === 'high' || pattern.severity === 'medium') {
                    existing.severity = pattern.severity;
                }
            }
        } else {
            // Add new pattern
            this.systemKnowledge.learnings.failurePatterns.push(pattern);
        }

        await this.memoryManager.store(
            'system',
            {
                type: 'failure_pattern',
                pattern,
                timestamp: new Date()
            },
            MemoryType.PROCEDURAL,
            { importance: 0.95 } // Higher importance for failures
        );

        this.isDirty = true;
    }

    /**
     * Track user preference
     */
    public async trackUserPreference(preference: UserPreference): Promise<void> {
        if (!this.systemKnowledge) {
            throw new Error('No system knowledge exists.');
        }

        const existing = this.systemKnowledge.learnings.userPreferences.find(
            p => p.category === preference.category && p.preference === preference.preference
        );

        if (existing) {
            existing.frequency++;
            existing.lastObserved = new Date();
            existing.confidence = Math.min(1.0, existing.confidence + 0.05);
        } else {
            this.systemKnowledge.learnings.userPreferences.push(preference);
        }

        await this.memoryManager.store(
            'system',
            {
                type: 'user_preference',
                preference,
                timestamp: new Date()
            },
            MemoryType.SEMANTIC,
            { importance: 0.6 }
        );

        this.isDirty = true;
    }

    /**
     * Find component by ID or name
     */
    public findComponent(identifier: string): Component | undefined {
        if (!this.systemKnowledge) return undefined;

        const byId = this.systemKnowledge.architecture.components[identifier];
        if (byId) return byId;

        return Object.values(this.systemKnowledge.architecture.components)
            .find(c => c.name === identifier);
    }

    /**
     * Find function by signature or name
     */
    public findFunction(identifier: string): FunctionSignature | undefined {
        if (!this.systemKnowledge) return undefined;

        // Search all modules
        for (const functions of Object.values(this.systemKnowledge.functions.byModule)) {
            const found = functions.find(f =>
                f.id === identifier ||
                f.name === identifier ||
                f.signature === identifier
            );
            if (found) return found;
        }

        return undefined;
    }

    /**
     * Get components with high complexity
     */
    public getComplexComponents(threshold: number = 10): Component[] {
        if (!this.systemKnowledge) return [];

        return Object.values(this.systemKnowledge.architecture.components)
            .filter(c => c.complexity.overall === 'complex' || c.complexity.overall === 'critical')
            .sort((a, b) => b.complexity.cyclomatic - a.complexity.cyclomatic);
    }

    /**
     * Get code hotspots
     */
    public getHotspots(severity?: 'low' | 'medium' | 'high' | 'critical'): CodeHotspot[] {
        if (!this.systemKnowledge) return [];

        let hotspots = this.systemKnowledge.functions.hotspots;

        if (severity) {
            hotspots = hotspots.filter(h => h.severity === severity);
        }

        return hotspots.sort((a, b) => {
            const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
            return severityOrder[b.severity] - severityOrder[a.severity];
        });
    }

    /**
     * Find similar pattern
     */
    public async findSimilarPattern(description: string): Promise<{
        pattern: any;
        similarity: number;
    } | null> {
        const results = await this.memoryManager.search(
            description,
            {
                k: 1,
                type: MemoryType.PROCEDURAL
            }
        );

        if (results.length > 0 && results[0].similarity > this.config.similarityThreshold) {
            return {
                pattern: results[0].entry.content,
                similarity: results[0].similarity
            };
        }

        return null;
    }

    /**
     * Get applicable patterns for a context
     */
    public async getApplicablePatterns(context: string): Promise<{
        success: SuccessPattern[];
        failures: FailurePattern[];
        code: CodePattern[];
        optimizations: OptimizationPattern[];
    }> {
        if (!this.systemKnowledge) {
            return { success: [], failures: [], code: [], optimizations: [] };
        }

        // Search for relevant patterns
        const results = await this.memoryManager.search(
            context,
            {
                k: 10,
                type: MemoryType.PROCEDURAL
            }
        );

        const applicable = {
            success: [] as SuccessPattern[],
            failures: [] as FailurePattern[],
            code: [] as CodePattern[],
            optimizations: [] as OptimizationPattern[]
        };

        for (const result of results) {
            if (result.similarity < this.config.similarityThreshold) continue;

            const content = result.entry.content;
            if (content.type === 'success_pattern') {
                applicable.success.push(content.pattern);
            } else if (content.type === 'failure_pattern') {
                applicable.failures.push(content.pattern);
            } else if (content.type === 'code_pattern') {
                applicable.code.push(content.pattern);
            } else if (content.type === 'optimization_pattern') {
                applicable.optimizations.push(content.pattern);
            }
        }

        return applicable;
    }

    /**
     * Get user preferences for a category
     */
    public getUserPreferences(category?: string): UserPreference[] {
        if (!this.systemKnowledge) return [];

        let preferences = this.systemKnowledge.learnings.userPreferences;

        if (category) {
            preferences = preferences.filter(p => p.category === category);
        }

        return preferences
            .filter(p => p.confidence > 0.5) // Only return confident preferences
            .sort((a, b) => b.confidence - a.confidence);
    }

    /**
     * Get architecture evolution
     */
    public getArchitectureEvolution(limit: number = 10): ArchitectureModel[] {
        const versions = Array.from(this.architectureHistory.entries())
            .sort((a, b) => b[0].localeCompare(a[0]))
            .slice(0, limit);

        return versions.map(([_, arch]) => arch);
    }

    /**
     * Calculate architecture diff
     */
    public calculateArchitectureDiff(fromVersion?: string): {
        added: Component[];
        modified: Component[];
        removed: string[];
    } {
        if (!this.systemKnowledge) {
            return { added: [], modified: [], removed: [] };
        }

        const currentComponents = this.systemKnowledge.architecture.components;

        if (!fromVersion || !this.architectureHistory.has(fromVersion)) {
            // No comparison version, return all as added
            return {
                added: Object.values(currentComponents),
                modified: [],
                removed: []
            };
        }

        const oldArchitecture = this.architectureHistory.get(fromVersion)!;
        const oldComponents = oldArchitecture.components;

        const added: Component[] = [];
        const modified: Component[] = [];
        const removed: string[] = [];

        // Find added and modified
        for (const [id, component] of Object.entries(currentComponents)) {
            if (!oldComponents[id]) {
                added.push(component);
            } else if (component.lastModified > oldComponents[id].lastModified) {
                modified.push(component);
            }
        }

        // Find removed
        for (const id of Object.keys(oldComponents)) {
            if (!currentComponents[id]) {
                removed.push(id);
            }
        }

        return { added, modified, removed };
    }

    /**
     * Predict next likely changes
     */
    public async predictNextChanges(): Promise<{
        components: string[];
        reason: string;
        confidence: number;
    }[]> {
        if (!this.systemKnowledge) return [];

        const predictions: any[] = [];

        // Analyze modification frequency
        const frequentlyModified = Object.values(this.systemKnowledge.architecture.components)
            .filter(c => c.complexity.overall === 'complex' || c.complexity.overall === 'critical')
            .sort((a, b) => b.dependencies.length - a.dependencies.length)
            .slice(0, 5);

        for (const component of frequentlyModified) {
            predictions.push({
                components: [component.id],
                reason: `High complexity (${component.complexity.overall}) with ${component.dependencies.length} dependencies`,
                confidence: 0.7
            });
        }

        // Check for patterns in recent changes
        const recentPatterns = this.systemKnowledge.learnings.successPatterns
            .filter(p => p.lastUsed && (new Date().getTime() - p.lastUsed.getTime()) < 7 * 24 * 60 * 60 * 1000)
            .slice(0, 3);

        for (const pattern of recentPatterns) {
            predictions.push({
                components: pattern.applicableScenarios,
                reason: `Based on pattern: ${pattern.name}`,
                confidence: pattern.successRate
            });
        }

        return predictions;
    }

    /**
     * Extract and store patterns from knowledge
     */
    private async extractAndStorePatterns(knowledge: SystemKnowledge): Promise<void> {
        // Extract architecture patterns
        for (const pattern of knowledge.architecture.patterns) {
            await this.memoryManager.store(
                'system',
                {
                    type: 'architecture_pattern',
                    pattern,
                    timestamp: new Date()
                },
                MemoryType.PROCEDURAL,
                { importance: 0.8 }
            );
        }

        // Extract frequently used functions as patterns
        const frequentFunctions = Object.values(knowledge.functions.byModule)
            .flat()
            .filter(f => f.modificationFrequency > 5)
            .slice(0, 20);

        for (const func of frequentFunctions) {
            await this.memoryManager.store(
                'system',
                {
                    type: 'frequent_function',
                    function: func,
                    timestamp: new Date()
                },
                MemoryType.SEMANTIC,
                { importance: 0.6 }
            );
        }
    }

    /**
     * Compact history to save memory
     */
    private async compactHistory(): Promise<void> {
        // Keep only the last N versions
        if (this.architectureHistory.size > this.config.maxArchitectureVersions) {
            const versions = Array.from(this.architectureHistory.keys())
                .sort()
                .slice(0, -this.config.maxArchitectureVersions);

            for (const version of versions) {
                this.architectureHistory.delete(version);
                this.functionHistory.delete(version);
            }
        }

        // Clean up old patterns
        if (this.systemKnowledge) {
            // Remove low-confidence patterns
            this.systemKnowledge.learnings.successPatterns =
                this.systemKnowledge.learnings.successPatterns
                    .filter(p => p.successRate > 0.3);

            // Remove old failure patterns
            const cutoff = new Date();
            cutoff.setDate(cutoff.getDate() - 30);
            this.systemKnowledge.learnings.failurePatterns =
                this.systemKnowledge.learnings.failurePatterns
                    .filter(p => p.lastSeen > cutoff);
        }
    }

    /**
     * Generate version string
     */
    private generateVersion(): string {
        const now = new Date();
        return `${now.getFullYear()}${(now.getMonth() + 1).toString().padStart(2, '0')}${now.getDate().toString().padStart(2, '0')}_${now.getHours().toString().padStart(2, '0')}${now.getMinutes().toString().padStart(2, '0')}${now.getSeconds().toString().padStart(2, '0')}`;
    }

    /**
     * Load from disk
     */
    private async loadFromDisk(path: string): Promise<void> {
        try {
            const fs = await import('fs/promises');
            const data = await fs.readFile(path, 'utf-8');
            const parsed = JSON.parse(data);

            this.systemKnowledge = parsed.systemKnowledge;
            this.architectureHistory = new Map(parsed.architectureHistory);
            this.functionHistory = new Map(parsed.functionHistory);
            this.lastAnalysis = parsed.lastAnalysis ? new Date(parsed.lastAnalysis) : null;

            this.isDirty = false;
        } catch (error) {
            console.log('No existing memory found, starting fresh');
        }
    }

    /**
     * Save to disk
     */
    private async saveToDisk(path: string): Promise<void> {
        if (!this.isDirty) return;

        try {
            const fs = await import('fs/promises');
            const data = {
                systemKnowledge: this.systemKnowledge,
                architectureHistory: Array.from(this.architectureHistory.entries()),
                functionHistory: Array.from(this.functionHistory.entries()),
                lastAnalysis: this.lastAnalysis
            };

            await fs.writeFile(path, JSON.stringify(data, null, 2));
            this.isDirty = false;
        } catch (error) {
            console.error('Failed to save memory to disk:', error);
        }
    }

    /**
     * Get memory statistics
     */
    public getStatistics(): {
        totalComponents: number;
        totalFunctions: number;
        totalPatterns: number;
        architectureVersions: number;
        memoryUsage: number;
        lastAnalysis: Date | null;
    } {
        return {
            totalComponents: this.systemKnowledge ?
                Object.keys(this.systemKnowledge.architecture.components).length : 0,
            totalFunctions: this.systemKnowledge ?
                Object.values(this.systemKnowledge.functions.byModule).flat().length : 0,
            totalPatterns: this.systemKnowledge ?
                this.systemKnowledge.learnings.successPatterns.length +
                this.systemKnowledge.learnings.failurePatterns.length : 0,
            architectureVersions: this.architectureHistory.size,
            memoryUsage: process.memoryUsage().heapUsed,
            lastAnalysis: this.lastAnalysis
        };
    }
}