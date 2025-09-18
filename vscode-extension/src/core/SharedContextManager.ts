/**
 * SharedContextManager - Manages shared context between agents for collaboration
 * Enables agents to share knowledge, decisions, and intermediate results in real-time
 */

import { EventEmitter } from 'events';

export interface ContextUpdate {
    agentId: string;
    timestamp: number;
    key: string;
    value: any;
    metadata?: {
        confidence?: number;
        dependencies?: string[];
        version?: number;
    };
}

export interface SharedContext {
    projectStructure?: any;
    architectureDecisions?: Map<string, any>;
    codePatterns?: Map<string, any>;
    researchFindings?: Map<string, any>;
    validationResults?: Map<string, any>;
    currentWorkflow?: any;
    globalMemories?: any[];
    agentOutputs?: Map<string, any>;
}

export interface ContextSubscriber {
    agentId: string;
    callback: (update: ContextUpdate) => void;
    filter?: (update: ContextUpdate) => boolean;
}

export class SharedContextManager {
    private static instance: SharedContextManager;
    private context: Map<string, any> = new Map();
    private contextHistory: ContextUpdate[] = [];
    private subscribers: Map<string, ContextSubscriber[]> = new Map();
    private eventBus: EventEmitter;
    private locks: Map<string, string> = new Map(); // key -> agentId holding lock
    private version: number = 0;

    private constructor() {
        this.eventBus = new EventEmitter();
        this.eventBus.setMaxListeners(50); // Support many agents
        this.initializeContext();
    }

    public static getInstance(): SharedContextManager {
        if (!SharedContextManager.instance) {
            SharedContextManager.instance = new SharedContextManager();
        }
        return SharedContextManager.instance;
    }

    private initializeContext(): void {
        // Initialize with default context structure
        this.context.set('projectStructure', {});
        this.context.set('architectureDecisions', new Map());
        this.context.set('codePatterns', new Map());
        this.context.set('researchFindings', new Map());
        this.context.set('validationResults', new Map());
        this.context.set('currentWorkflow', null);
        this.context.set('globalMemories', []);
        this.context.set('agentOutputs', new Map());
    }

    /**
     * Update context with new information
     */
    public async updateContext(agentId: string, key: string, value: any, metadata?: any): Promise<void> {
        // Check if key is locked by another agent
        const lockHolder = this.locks.get(key);
        if (lockHolder && lockHolder !== agentId) {
            throw new Error(`Context key '${key}' is locked by agent ${lockHolder}`);
        }

        const update: ContextUpdate = {
            agentId,
            timestamp: Date.now(),
            key,
            value,
            metadata: {
                ...metadata,
                version: ++this.version
            }
        };

        // Update the context
        this.context.set(key, value);

        // Store in history for replay/debugging
        this.contextHistory.push(update);

        // Notify all subscribers
        await this.notifySubscribers(update);

        // Emit event for async listeners
        this.eventBus.emit('context-update', update);
    }

    /**
     * Get current context value
     */
    public getContext(key?: string): any {
        if (key) {
            return this.context.get(key);
        }
        // Return entire context as object
        const contextObj: any = {};
        this.context.forEach((value, key) => {
            contextObj[key] = value;
        });
        return contextObj;
    }

    /**
     * Get context with memory of past updates
     */
    public getContextWithHistory(key: string, limit: number = 10): ContextUpdate[] {
        return this.contextHistory
            .filter(update => update.key === key)
            .slice(-limit);
    }

    /**
     * Subscribe to context updates
     */
    public subscribe(agentId: string, callback: (update: ContextUpdate) => void, filter?: (update: ContextUpdate) => boolean): void {
        const subscriber: ContextSubscriber = {
            agentId,
            callback,
            filter
        };

        if (!this.subscribers.has(agentId)) {
            this.subscribers.set(agentId, []);
        }

        this.subscribers.get(agentId)!.push(subscriber);
    }

    /**
     * Unsubscribe from context updates
     */
    public unsubscribe(agentId: string): void {
        this.subscribers.delete(agentId);
    }

    /**
     * Notify all subscribers of a context update
     */
    private async notifySubscribers(update: ContextUpdate): Promise<void> {
        const promises: Promise<void>[] = [];

        this.subscribers.forEach((subscriberList) => {
            subscriberList.forEach(subscriber => {
                // Skip the agent that made the update
                if (subscriber.agentId === update.agentId) {
                    return;
                }

                // Apply filter if provided
                if (subscriber.filter && !subscriber.filter(update)) {
                    return;
                }

                // Notify subscriber asynchronously
                promises.push(
                    Promise.resolve(subscriber.callback(update)).catch(err => {
                        console.error(`Error notifying subscriber ${subscriber.agentId}:`, err);
                    })
                );
            });
        });

        await Promise.all(promises);
    }

    /**
     * Acquire a lock on a context key (for atomic updates)
     */
    public async acquireLock(agentId: string, key: string, timeout: number = 5000): Promise<void> {
        const startTime = Date.now();

        while (this.locks.has(key) && this.locks.get(key) !== agentId) {
            if (Date.now() - startTime > timeout) {
                throw new Error(`Timeout acquiring lock for key '${key}'`);
            }
            await new Promise(resolve => setTimeout(resolve, 100));
        }

        this.locks.set(key, agentId);
    }

    /**
     * Release a lock on a context key
     */
    public releaseLock(agentId: string, key: string): void {
        if (this.locks.get(key) === agentId) {
            this.locks.delete(key);
        }
    }

    /**
     * Merge context from multiple agents (for conflict resolution)
     */
    public async mergeContext(updates: ContextUpdate[], resolver?: (conflicts: ContextUpdate[]) => any): Promise<void> {
        const grouped = new Map<string, ContextUpdate[]>();

        // Group updates by key
        updates.forEach(update => {
            if (!grouped.has(update.key)) {
                grouped.set(update.key, []);
            }
            grouped.get(update.key)!.push(update);
        });

        // Process each key
        for (const [key, keyUpdates] of grouped) {
            if (keyUpdates.length === 1) {
                // No conflict, apply directly
                await this.updateContext(keyUpdates[0].agentId, key, keyUpdates[0].value, keyUpdates[0].metadata);
            } else {
                // Conflict - use resolver or last-write-wins
                const resolvedValue = resolver ? resolver(keyUpdates) : keyUpdates[keyUpdates.length - 1].value;
                await this.updateContext('system', key, resolvedValue, { resolved: true });
            }
        }
    }

    /**
     * Create a snapshot of current context (for checkpointing)
     */
    public createSnapshot(): { version: number; timestamp: number; context: Map<string, any> } {
        return {
            version: this.version,
            timestamp: Date.now(),
            context: new Map(this.context)
        };
    }

    /**
     * Restore context from snapshot
     */
    public restoreSnapshot(snapshot: { version: number; timestamp: number; context: Map<string, any> }): void {
        this.context = new Map(snapshot.context);
        this.version = snapshot.version;
        this.eventBus.emit('context-restored', snapshot);
    }

    /**
     * Clear context (for new sessions)
     */
    public clearContext(): void {
        this.context.clear();
        this.contextHistory = [];
        this.locks.clear();
        this.version = 0;
        this.initializeContext();
        this.eventBus.emit('context-cleared');
    }

    /**
     * Get agents currently working on the context
     */
    public getActiveAgents(): string[] {
        const activeAgents = new Set<string>();

        // Get agents from recent updates
        const recentTime = Date.now() - 60000; // Last minute
        this.contextHistory
            .filter(update => update.timestamp > recentTime)
            .forEach(update => activeAgents.add(update.agentId));

        return Array.from(activeAgents);
    }

    /**
     * Get collaboration insights
     */
    public getCollaborationMetrics(): any {
        const metrics: any = {
            totalUpdates: this.contextHistory.length,
            activeAgents: this.getActiveAgents().length,
            contextKeys: this.context.size,
            lockedKeys: this.locks.size,
            version: this.version
        };

        // Calculate update frequency by agent
        const agentUpdates = new Map<string, number>();
        this.contextHistory.forEach(update => {
            agentUpdates.set(update.agentId, (agentUpdates.get(update.agentId) || 0) + 1);
        });
        metrics.agentActivity = Object.fromEntries(agentUpdates);

        return metrics;
    }
}

// Export singleton instance getter
export function getSharedContext(): SharedContextManager {
    return SharedContextManager.getInstance();
}