/**
 * MemoryManager - Vector-based memory system for agents
 * Provides semantic search, pattern extraction, and learning capabilities
 */

import { EventEmitter } from 'events';
import {
    MemoryEntry,
    MemoryType,
    MemorySearchResult,
    MemoryPattern,
    MemoryCluster,
    MemoryMetadata,
    MemoryStats,
    TaskMemory,
    CodePattern,
    ArchitecturePattern,
    LearningEntry
} from '../types/Memory';

export interface MemoryOptions {
    maxMemories?: number;
    similarityThreshold?: number;
    clusteringEnabled?: boolean;
    patternExtractionEnabled?: boolean;
    autoForget?: boolean;
    forgetThreshold?: number;
}

export class MemoryManager {
    private memories: Map<string, MemoryEntry> = new Map();
    private embeddings: Map<string, number[]> = new Map();
    private patterns: Map<string, MemoryPattern> = new Map();
    private clusters: MemoryCluster[] = [];
    private codePatterns: Map<string, CodePattern> = new Map();
    private architecturePatterns: Map<string, ArchitecturePattern> = new Map();
    private learningEntries: LearningEntry[] = [];
    private eventBus: EventEmitter;
    private options: MemoryOptions;
    private memoryIndex: Map<MemoryType, Set<string>> = new Map();
    private agentMemories: Map<string, Set<string>> = new Map();

    constructor(options: MemoryOptions = {}) {
        this.options = {
            maxMemories: options.maxMemories || 10000,
            similarityThreshold: options.similarityThreshold || 0.7,
            clusteringEnabled: options.clusteringEnabled ?? true,
            patternExtractionEnabled: options.patternExtractionEnabled ?? true,
            autoForget: options.autoForget ?? true,
            forgetThreshold: options.forgetThreshold || 0.3
        };

        this.eventBus = new EventEmitter();
        this.initializeIndexes();
    }

    private initializeIndexes(): void {
        Object.values(MemoryType).forEach(type => {
            this.memoryIndex.set(type, new Set());
        });
    }

    /**
     * Store a new memory with automatic embedding generation
     */
    public async store(
        agentId: string,
        content: any,
        type: MemoryType,
        metadata: Partial<MemoryMetadata> = {}
    ): Promise<string> {
        const id = this.generateMemoryId();

        // Generate embedding (simplified - in real implementation, use actual embedding model)
        const embedding = await this.generateEmbedding(content);

        const memory: MemoryEntry = {
            id,
            agentId,
            timestamp: Date.now(),
            content,
            embedding,
            type,
            metadata: {
                ...metadata,
                accessCount: 0,
                lastAccessed: Date.now(),
                importance: metadata.importance || this.calculateImportance(content, type)
            }
        };

        // Store memory
        this.memories.set(id, memory);
        this.embeddings.set(id, embedding);

        // Update indexes
        this.memoryIndex.get(type)!.add(id);
        if (!this.agentMemories.has(agentId)) {
            this.agentMemories.set(agentId, new Set());
        }
        this.agentMemories.get(agentId)!.add(id);

        // Auto-forget old memories if limit exceeded
        if (this.options.autoForget && this.memories.size > this.options.maxMemories!) {
            await this.forgetOldMemories();
        }

        // Extract patterns if enabled
        if (this.options.patternExtractionEnabled) {
            await this.extractPatterns();
        }

        // Update clusters if enabled
        if (this.options.clusteringEnabled) {
            await this.updateClusters();
        }

        this.eventBus.emit('memory-stored', memory);
        return id;
    }

    /**
     * Retrieve memories by semantic similarity
     */
    public async search(
        query: any,
        options: {
            k?: number;
            type?: MemoryType;
            agentId?: string;
            minSimilarity?: number;
        } = {}
    ): Promise<MemorySearchResult[]> {
        const k = options.k || 10;
        const minSimilarity = options.minSimilarity || this.options.similarityThreshold!;

        // Generate query embedding
        const queryEmbedding = await this.generateEmbedding(query);

        // Filter memories based on options
        let candidateMemories = Array.from(this.memories.values());

        if (options.type) {
            const typeMemories = this.memoryIndex.get(options.type);
            if (typeMemories) {
                candidateMemories = candidateMemories.filter(m => typeMemories.has(m.id));
            }
        }

        if (options.agentId) {
            const agentMems = this.agentMemories.get(options.agentId);
            if (agentMems) {
                candidateMemories = candidateMemories.filter(m => agentMems.has(m.id));
            }
        }

        // Calculate similarities
        const results: MemorySearchResult[] = candidateMemories
            .map(memory => {
                const similarity = this.cosineSimilarity(
                    queryEmbedding,
                    memory.embedding || []
                );
                const relevance = this.calculateRelevance(memory, similarity);

                // Update access count
                memory.metadata.accessCount = (memory.metadata.accessCount || 0) + 1;
                memory.metadata.lastAccessed = Date.now();

                return {
                    entry: memory,
                    similarity,
                    relevance
                };
            })
            .filter(result => result.similarity >= minSimilarity)
            .sort((a, b) => b.relevance - a.relevance)
            .slice(0, k);

        this.eventBus.emit('memory-searched', { query, results });
        return results;
    }

    /**
     * Get memory by ID
     */
    public get(id: string): MemoryEntry | undefined {
        const memory = this.memories.get(id);
        if (memory) {
            memory.metadata.accessCount = (memory.metadata.accessCount || 0) + 1;
            memory.metadata.lastAccessed = Date.now();
        }
        return memory;
    }

    /**
     * Update an existing memory
     */
    public async update(id: string, content: any, metadata?: Partial<MemoryMetadata>): Promise<void> {
        const memory = this.memories.get(id);
        if (!memory) {
            throw new Error(`Memory ${id} not found`);
        }

        memory.content = content;
        memory.embedding = await this.generateEmbedding(content);
        if (metadata) {
            memory.metadata = { ...memory.metadata, ...metadata };
        }

        this.embeddings.set(id, memory.embedding);
        this.eventBus.emit('memory-updated', memory);
    }

    /**
     * Delete a memory
     */
    public delete(id: string): boolean {
        const memory = this.memories.get(id);
        if (!memory) return false;

        // Remove from all indexes
        this.memories.delete(id);
        this.embeddings.delete(id);
        this.memoryIndex.get(memory.type)?.delete(id);
        this.agentMemories.get(memory.agentId)?.delete(id);

        this.eventBus.emit('memory-deleted', memory);
        return true;
    }

    /**
     * Store a code pattern for reuse
     */
    public storeCodePattern(pattern: CodePattern): void {
        this.codePatterns.set(pattern.id, pattern);
        this.eventBus.emit('pattern-stored', { type: 'code', pattern });
    }

    /**
     * Retrieve relevant code patterns
     */
    public async getRelevantCodePatterns(context: string, language?: string): Promise<CodePattern[]> {
        const patterns = Array.from(this.codePatterns.values());

        // Filter by language if specified
        let relevant = language
            ? patterns.filter(p => p.language === language)
            : patterns;

        // Sort by success rate and recency
        relevant.sort((a, b) => {
            const scoreA = a.successRate * (1 / (Date.now() - a.lastUsed));
            const scoreB = b.successRate * (1 / (Date.now() - b.lastUsed));
            return scoreB - scoreA;
        });

        return relevant.slice(0, 5);
    }

    /**
     * Store an architecture pattern
     */
    public storeArchitecturePattern(pattern: ArchitecturePattern): void {
        this.architecturePatterns.set(pattern.id, pattern);
        this.eventBus.emit('pattern-stored', { type: 'architecture', pattern });
    }

    /**
     * Get relevant architecture patterns
     */
    public getRelevantArchitecturePatterns(useCase: string): ArchitecturePattern[] {
        return Array.from(this.architecturePatterns.values())
            .filter(pattern =>
                pattern.useCases.some(uc =>
                    uc.toLowerCase().includes(useCase.toLowerCase())
                )
            );
    }

    /**
     * Store a learning entry
     */
    public storeLearning(learning: LearningEntry): void {
        this.learningEntries.push(learning);
        this.eventBus.emit('learning-stored', learning);
    }

    /**
     * Get learnings relevant to current context
     */
    public getRelevantLearnings(context: string, limit: number = 5): LearningEntry[] {
        // Simple keyword matching - in production, use semantic search
        const keywords = context.toLowerCase().split(' ');

        return this.learningEntries
            .filter(entry =>
                keywords.some(keyword =>
                    entry.description.toLowerCase().includes(keyword)
                )
            )
            .sort((a, b) => {
                // Prioritize high impact and recent learnings
                const scoreA = (a.impact === 'high' ? 3 : a.impact === 'medium' ? 2 : 1) *
                              (1 / (Date.now() - a.timestamp));
                const scoreB = (b.impact === 'high' ? 3 : b.impact === 'medium' ? 2 : 1) *
                              (1 / (Date.now() - b.timestamp));
                return scoreB - scoreA;
            })
            .slice(0, limit);
    }

    /**
     * Extract patterns from stored memories
     */
    private async extractPatterns(): Promise<void> {
        // Group similar memories
        const groups = this.groupSimilarMemories();

        groups.forEach((group, pattern) => {
            if (group.length >= 3) { // Need at least 3 occurrences to be a pattern
                const patternEntry: MemoryPattern = {
                    id: this.generateMemoryId(),
                    pattern,
                    frequency: group.length,
                    examples: group.slice(0, 5),
                    extractedAt: Date.now()
                };
                this.patterns.set(patternEntry.id, patternEntry);
            }
        });
    }

    /**
     * Group similar memories for pattern extraction
     */
    private groupSimilarMemories(): Map<string, MemoryEntry[]> {
        const groups = new Map<string, MemoryEntry[]>();
        const processed = new Set<string>();

        this.memories.forEach((memory, id) => {
            if (processed.has(id)) return;

            const similar = this.findSimilarMemories(memory, 0.8);
            if (similar.length >= 2) {
                const pattern = this.extractPatternSignature(memory);
                groups.set(pattern, [memory, ...similar]);
                similar.forEach(s => processed.add(s.id));
            }
        });

        return groups;
    }

    /**
     * Find memories similar to given memory
     */
    private findSimilarMemories(memory: MemoryEntry, threshold: number): MemoryEntry[] {
        const similar: MemoryEntry[] = [];

        this.memories.forEach((other, id) => {
            if (id === memory.id) return;

            const similarity = this.cosineSimilarity(
                memory.embedding || [],
                other.embedding || []
            );

            if (similarity >= threshold) {
                similar.push(other);
            }
        });

        return similar;
    }

    /**
     * Update memory clusters
     */
    private async updateClusters(): Promise<void> {
        // Simple k-means clustering
        const k = Math.min(10, Math.floor(this.memories.size / 50));
        if (k < 2) return;

        // Initialize centroids
        const centroids = this.initializeCentroids(k);

        // Iterate until convergence
        let iterations = 0;
        let changed = true;

        while (changed && iterations < 50) {
            const newClusters: MemoryCluster[] = centroids.map(centroid => ({
                centroid,
                members: [],
                coherence: 0
            }));

            // Assign memories to nearest centroid
            this.memories.forEach(memory => {
                if (!memory.embedding) return;

                let nearestIdx = 0;
                let maxSim = -1;

                centroids.forEach((centroid, idx) => {
                    const sim = this.cosineSimilarity(memory.embedding!, centroid);
                    if (sim > maxSim) {
                        maxSim = sim;
                        nearestIdx = idx;
                    }
                });

                newClusters[nearestIdx].members.push(memory);
            });

            // Update centroids
            changed = false;
            newClusters.forEach((cluster, idx) => {
                if (cluster.members.length > 0) {
                    const newCentroid = this.calculateCentroid(cluster.members);
                    if (!this.vectorsEqual(centroids[idx], newCentroid)) {
                        centroids[idx] = newCentroid;
                        changed = true;
                    }
                }
            });

            this.clusters = newClusters;
            iterations++;
        }

        // Calculate cluster coherence
        this.clusters.forEach(cluster => {
            cluster.coherence = this.calculateClusterCoherence(cluster);
        });

        this.eventBus.emit('clusters-updated', this.clusters);
    }

    /**
     * Forget old, unimportant memories
     */
    private async forgetOldMemories(): Promise<void> {
        const memoriesToForget: string[] = [];
        const now = Date.now();
        const oneWeek = 7 * 24 * 60 * 60 * 1000;

        this.memories.forEach((memory, id) => {
            // Calculate forgetting score
            const age = now - memory.timestamp;
            const accessFrequency = (memory.metadata.accessCount || 0) / (age / oneWeek);
            const importance = memory.metadata.importance || 0.5;

            const retentionScore = (accessFrequency * 0.4) + (importance * 0.6);

            if (retentionScore < this.options.forgetThreshold!) {
                memoriesToForget.push(id);
            }
        });

        // Keep at least 50% of max capacity
        const maxToForget = Math.floor(this.memories.size - (this.options.maxMemories! * 0.5));
        memoriesToForget.slice(0, maxToForget).forEach(id => {
            this.delete(id);
        });

        if (memoriesToForget.length > 0) {
            this.eventBus.emit('memories-forgotten', memoriesToForget.length);
        }
    }

    /**
     * Generate embedding for content (simplified - use real embedding model in production)
     */
    private async generateEmbedding(content: any): Promise<number[]> {
        // Simplified embedding generation
        // In production, use OpenAI embeddings or similar
        const text = JSON.stringify(content).toLowerCase();
        const embedding = new Array(384).fill(0);

        // Simple hash-based embedding
        for (let i = 0; i < text.length; i++) {
            const idx = (text.charCodeAt(i) * (i + 1)) % 384;
            embedding[idx] += 1;
        }

        // Normalize
        const magnitude = Math.sqrt(embedding.reduce((sum, val) => sum + val * val, 0));
        return embedding.map(val => val / (magnitude || 1));
    }

    /**
     * Calculate cosine similarity between two vectors
     */
    private cosineSimilarity(a: number[], b: number[]): number {
        if (a.length !== b.length || a.length === 0) return 0;

        let dotProduct = 0;
        let magnitudeA = 0;
        let magnitudeB = 0;

        for (let i = 0; i < a.length; i++) {
            dotProduct += a[i] * b[i];
            magnitudeA += a[i] * a[i];
            magnitudeB += b[i] * b[i];
        }

        magnitudeA = Math.sqrt(magnitudeA);
        magnitudeB = Math.sqrt(magnitudeB);

        if (magnitudeA === 0 || magnitudeB === 0) return 0;
        return dotProduct / (magnitudeA * magnitudeB);
    }

    /**
     * Calculate relevance score for a memory
     */
    private calculateRelevance(memory: MemoryEntry, similarity: number): number {
        const recency = 1 / (1 + (Date.now() - memory.timestamp) / (24 * 60 * 60 * 1000));
        const importance = memory.metadata.importance || 0.5;
        const accessFrequency = Math.min(1, (memory.metadata.accessCount || 0) / 100);

        return (similarity * 0.4) + (recency * 0.2) + (importance * 0.3) + (accessFrequency * 0.1);
    }

    /**
     * Calculate importance of content
     */
    private calculateImportance(content: any, type: MemoryType): number {
        // Simple heuristic - in production, use more sophisticated analysis
        if (type === MemoryType.PROCEDURAL) return 0.8;
        if (type === MemoryType.SEMANTIC) return 0.7;
        if (type === MemoryType.EPISODIC) return 0.5;
        return 0.3;
    }

    /**
     * Extract pattern signature from memory
     */
    private extractPatternSignature(memory: MemoryEntry): string {
        // Simplified pattern extraction
        const content = JSON.stringify(memory.content);
        return content.substring(0, 50);
    }

    /**
     * Initialize cluster centroids
     */
    private initializeCentroids(k: number): number[][] {
        const centroids: number[][] = [];
        const memories = Array.from(this.memories.values()).filter(m => m.embedding);

        for (let i = 0; i < k && i < memories.length; i++) {
            centroids.push([...memories[i].embedding!]);
        }

        return centroids;
    }

    /**
     * Calculate centroid of cluster members
     */
    private calculateCentroid(members: MemoryEntry[]): number[] {
        if (members.length === 0 || !members[0].embedding) return [];

        const dim = members[0].embedding.length;
        const centroid = new Array(dim).fill(0);

        members.forEach(member => {
            if (member.embedding) {
                member.embedding.forEach((val, idx) => {
                    centroid[idx] += val;
                });
            }
        });

        return centroid.map(val => val / members.length);
    }

    /**
     * Calculate cluster coherence
     */
    private calculateClusterCoherence(cluster: MemoryCluster): number {
        if (cluster.members.length < 2) return 1;

        let totalSimilarity = 0;
        let comparisons = 0;

        for (let i = 0; i < cluster.members.length; i++) {
            for (let j = i + 1; j < cluster.members.length; j++) {
                if (cluster.members[i].embedding && cluster.members[j].embedding) {
                    totalSimilarity += this.cosineSimilarity(
                        cluster.members[i].embedding!,
                        cluster.members[j].embedding!
                    );
                    comparisons++;
                }
            }
        }

        return comparisons > 0 ? totalSimilarity / comparisons : 0;
    }

    /**
     * Check if two vectors are equal
     */
    private vectorsEqual(a: number[], b: number[]): boolean {
        if (a.length !== b.length) return false;
        return a.every((val, idx) => Math.abs(val - b[idx]) < 0.001);
    }

    /**
     * Generate unique memory ID
     */
    private generateMemoryId(): string {
        return `mem_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Get memory statistics
     */
    public getStats(): MemoryStats {
        const stats: MemoryStats = {
            totalMemories: this.memories.size,
            byType: new Map(),
            byAgent: new Map(),
            averageAccessCount: 0,
            mostAccessedMemories: [],
            memoryGrowthRate: 0,
            patternCount: this.patterns.size,
            clusterCount: this.clusters.length
        };

        // Count by type
        this.memoryIndex.forEach((ids, type) => {
            stats.byType.set(type, ids.size);
        });

        // Count by agent
        this.agentMemories.forEach((ids, agent) => {
            stats.byAgent.set(agent, ids.size);
        });

        // Calculate average access count and find most accessed
        let totalAccess = 0;
        const memoriesByAccess = Array.from(this.memories.values())
            .sort((a, b) => (b.metadata.accessCount || 0) - (a.metadata.accessCount || 0));

        memoriesByAccess.forEach(memory => {
            totalAccess += memory.metadata.accessCount || 0;
        });

        stats.averageAccessCount = totalAccess / (this.memories.size || 1);
        stats.mostAccessedMemories = memoriesByAccess.slice(0, 10);

        return stats;
    }

    /**
     * Export memories for persistence
     */
    public export(): string {
        const exportData = {
            memories: Array.from(this.memories.entries()),
            patterns: Array.from(this.patterns.entries()),
            codePatterns: Array.from(this.codePatterns.entries()),
            architecturePatterns: Array.from(this.architecturePatterns.entries()),
            learningEntries: this.learningEntries,
            timestamp: Date.now()
        };

        return JSON.stringify(exportData);
    }

    /**
     * Import memories from persistence
     */
    public import(data: string): void {
        const importData = JSON.parse(data);

        // Clear existing data
        this.memories.clear();
        this.patterns.clear();
        this.codePatterns.clear();
        this.architecturePatterns.clear();
        this.learningEntries = [];

        // Import memories
        importData.memories.forEach(([id, memory]: [string, MemoryEntry]) => {
            this.memories.set(id, memory);
            if (memory.embedding) {
                this.embeddings.set(id, memory.embedding);
            }
        });

        // Import patterns
        importData.patterns.forEach(([id, pattern]: [string, MemoryPattern]) => {
            this.patterns.set(id, pattern);
        });

        // Import code patterns
        importData.codePatterns.forEach(([id, pattern]: [string, CodePattern]) => {
            this.codePatterns.set(id, pattern);
        });

        // Import architecture patterns
        importData.architecturePatterns.forEach(([id, pattern]: [string, ArchitecturePattern]) => {
            this.architecturePatterns.set(id, pattern);
        });

        // Import learning entries
        this.learningEntries = importData.learningEntries || [];

        // Rebuild indexes
        this.rebuildIndexes();

        this.eventBus.emit('memories-imported', {
            count: this.memories.size,
            timestamp: importData.timestamp
        });
    }

    /**
     * Rebuild indexes after import
     */
    private rebuildIndexes(): void {
        this.memoryIndex.clear();
        this.agentMemories.clear();
        this.initializeIndexes();

        this.memories.forEach(memory => {
            this.memoryIndex.get(memory.type)?.add(memory.id);

            if (!this.agentMemories.has(memory.agentId)) {
                this.agentMemories.set(memory.agentId, new Set());
            }
            this.agentMemories.get(memory.agentId)?.add(memory.id);
        });
    }
}