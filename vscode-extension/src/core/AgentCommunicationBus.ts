/**
 * AgentCommunicationBus - Inter-agent communication system
 * Enables agents to collaborate, share information, and coordinate actions
 */

import { EventEmitter } from 'events';

export interface AgentMessage {
    id: string;
    from: string;
    to: string | string[] | 'broadcast';
    type: MessageType;
    content: any;
    metadata: MessageMetadata;
    timestamp: number;
    replyTo?: string;
}

export enum MessageType {
    REQUEST = 'request',
    RESPONSE = 'response',
    NOTIFICATION = 'notification',
    QUERY = 'query',
    BROADCAST = 'broadcast',
    COLLABORATION_REQUEST = 'collaboration_request',
    COLLABORATION_RESPONSE = 'collaboration_response',
    TASK_DELEGATION = 'task_delegation',
    STATUS_UPDATE = 'status_update',
    ERROR = 'error',
    HELP_REQUEST = 'help_request',
    KNOWLEDGE_SHARE = 'knowledge_share',
    VALIDATION_REQUEST = 'validation_request',
    CONFLICT = 'conflict'
}

export interface MessageMetadata {
    priority: 'low' | 'normal' | 'high' | 'critical';
    requiresResponse: boolean;
    timeout?: number;
    conversationId?: string;
    workflowId?: string;
    retryCount?: number;
    confidence?: number;
    reasoning?: string;
}

export interface CollaborationSession {
    id: string;
    task: any;
    participants: string[];
    leader?: string;
    status: 'pending' | 'active' | 'completed' | 'failed';
    sharedContext: Map<string, any>;
    messages: AgentMessage[];
    results: Map<string, any>;
    startTime: number;
    endTime?: number;
}

export interface MessageHandler {
    agentId: string;
    messageTypes: MessageType[];
    handler: (message: AgentMessage) => Promise<any>;
    filter?: (message: AgentMessage) => boolean;
}

export interface CommunicationStats {
    totalMessages: number;
    messagesByType: Map<MessageType, number>;
    messagesByAgent: Map<string, number>;
    averageResponseTime: number;
    activeSessions: number;
    failedMessages: number;
}

export class AgentCommunicationBus {
    private static instance: AgentCommunicationBus;
    private eventBus: EventEmitter;
    private handlers: Map<string, MessageHandler[]> = new Map();
    private messageQueue: AgentMessage[] = [];
    private processingQueue: boolean = false;
    private collaborationSessions: Map<string, CollaborationSession> = new Map();
    private messageHistory: AgentMessage[] = [];
    private responseCallbacks: Map<string, (response: any) => void> = new Map();
    private stats: CommunicationStats;

    private constructor() {
        this.eventBus = new EventEmitter();
        this.eventBus.setMaxListeners(50);
        this.stats = this.initializeStats();
        this.startQueueProcessor();
    }

    public static getInstance(): AgentCommunicationBus {
        if (!AgentCommunicationBus.instance) {
            AgentCommunicationBus.instance = new AgentCommunicationBus();
        }
        return AgentCommunicationBus.instance;
    }

    /**
     * Register an agent to receive messages
     */
    public register(handler: MessageHandler): void {
        if (!this.handlers.has(handler.agentId)) {
            this.handlers.set(handler.agentId, []);
        }

        this.handlers.get(handler.agentId)!.push(handler);
        this.eventBus.emit('agent-registered', handler.agentId);
    }

    /**
     * Unregister an agent
     */
    public unregister(agentId: string): void {
        this.handlers.delete(agentId);
        this.eventBus.emit('agent-unregistered', agentId);
    }

    /**
     * Send a message to one or more agents
     */
    public async send(message: Omit<AgentMessage, 'id' | 'timestamp'>): Promise<string> {
        const fullMessage: AgentMessage = {
            ...message,
            id: this.generateMessageId(),
            timestamp: Date.now()
        };

        // Add to history
        this.messageHistory.push(fullMessage);
        this.stats.totalMessages++;
        this.updateStats(fullMessage);

        // Add to queue
        this.messageQueue.push(fullMessage);

        // Emit event
        this.eventBus.emit('message-sent', fullMessage);

        // Process queue if not already processing
        if (!this.processingQueue) {
            this.processQueue();
        }

        return fullMessage.id;
    }

    /**
     * Send a message and wait for response
     */
    public async request(
        message: Omit<AgentMessage, 'id' | 'timestamp'>,
        timeout: number = 30000
    ): Promise<any> {
        const messageId = await this.send({
            ...message,
            metadata: {
                ...(message.metadata || {}),
                requiresResponse: true,
                timeout
            }
        });

        return new Promise((resolve, reject) => {
            const timer = setTimeout(() => {
                this.responseCallbacks.delete(messageId);
                reject(new Error(`Request timeout for message ${messageId}`));
            }, timeout);

            this.responseCallbacks.set(messageId, (response) => {
                clearTimeout(timer);
                this.responseCallbacks.delete(messageId);
                resolve(response);
            });
        });
    }

    /**
     * Broadcast a message to all agents
     */
    public async broadcast(
        from: string,
        type: MessageType,
        content: any,
        metadata?: Partial<MessageMetadata>
    ): Promise<void> {
        await this.send({
            from,
            to: 'broadcast',
            type: MessageType.BROADCAST,
            content,
            metadata: {
                priority: 'normal',
                requiresResponse: false,
                ...metadata
            }
        });
    }

    /**
     * Start a collaboration session between agents
     */
    public async startCollaboration(
        task: any,
        participants: string[],
        leader?: string
    ): Promise<CollaborationSession> {
        const session: CollaborationSession = {
            id: this.generateSessionId(),
            task,
            participants,
            leader: leader || participants[0],
            status: 'pending',
            sharedContext: new Map(),
            messages: [],
            results: new Map(),
            startTime: Date.now()
        };

        this.collaborationSessions.set(session.id, session);

        // Notify all participants
        await Promise.all(participants.map(agentId =>
            this.send({
                from: 'system',
                to: agentId,
                type: MessageType.COLLABORATION_REQUEST,
                content: {
                    sessionId: session.id,
                    task,
                    participants,
                    leader: session.leader
                },
                metadata: {
                    priority: 'high',
                    requiresResponse: true,
                    conversationId: session.id
                }
            })
        ));

        session.status = 'active';
        this.eventBus.emit('collaboration-started', session);

        return session;
    }

    /**
     * Send a message within a collaboration session
     */
    public async collaborationMessage(
        sessionId: string,
        from: string,
        content: any,
        type: MessageType = MessageType.NOTIFICATION
    ): Promise<void> {
        const session = this.collaborationSessions.get(sessionId);
        if (!session) {
            throw new Error(`Collaboration session ${sessionId} not found`);
        }

        // Send to all participants except sender
        const recipients = session.participants.filter(p => p !== from);

        const message = {
            from,
            to: recipients,
            type,
            content,
            metadata: {
                priority: 'normal' as const,
                requiresResponse: false,
                conversationId: sessionId
            }
        };

        await this.send(message);

        // Add to session history
        session.messages.push({
            ...message,
            id: this.generateMessageId(),
            timestamp: Date.now()
        });
    }

    /**
     * Update shared context in collaboration session
     */
    public updateCollaborationContext(
        sessionId: string,
        agentId: string,
        key: string,
        value: any
    ): void {
        const session = this.collaborationSessions.get(sessionId);
        if (!session) return;

        session.sharedContext.set(key, value);

        // Notify other participants
        this.collaborationMessage(
            sessionId,
            agentId,
            { key, value },
            MessageType.STATUS_UPDATE
        );
    }

    /**
     * Complete a collaboration session
     */
    public completeCollaboration(sessionId: string, results: Map<string, any>): void {
        const session = this.collaborationSessions.get(sessionId);
        if (!session) return;

        session.status = 'completed';
        session.results = results;
        session.endTime = Date.now();

        this.eventBus.emit('collaboration-completed', session);

        // Clean up after delay
        setTimeout(() => {
            this.collaborationSessions.delete(sessionId);
        }, 60000);
    }

    /**
     * Request help from other agents
     */
    public async requestHelp(
        from: string,
        problem: any,
        preferredAgents?: string[]
    ): Promise<any> {
        const message = {
            from,
            to: preferredAgents || 'broadcast',
            type: MessageType.HELP_REQUEST,
            content: problem,
            metadata: {
                priority: 'high' as const,
                requiresResponse: true,
                timeout: 10000
            }
        };

        const responses: any[] = [];

        if (preferredAgents) {
            // Request from specific agents
            for (const agentId of preferredAgents) {
                try {
                    const response = await this.request(
                        { ...message, to: agentId, metadata: message.metadata },
                        10000
                    );
                    if (response) responses.push(response);
                } catch (error) {
                    console.warn(`No response from ${agentId}:`, error);
                }
            }
        } else {
            // Broadcast and collect responses
            await this.broadcast(from, MessageType.HELP_REQUEST, problem, {
                priority: 'high',
                requiresResponse: true
            });

            // Wait for responses
            await new Promise(resolve => setTimeout(resolve, 5000));

            // Collect responses from history
            const requestTime = Date.now();
            responses.push(...this.messageHistory
                .filter(msg =>
                    msg.type === MessageType.RESPONSE &&
                    msg.timestamp > requestTime - 5000 &&
                    msg.replyTo === message.from
                )
                .map(msg => msg.content)
            );
        }

        return responses;
    }

    /**
     * Share knowledge between agents
     */
    public async shareKnowledge(
        from: string,
        knowledge: any,
        relevantAgents?: string[]
    ): Promise<void> {
        await this.send({
            from,
            to: relevantAgents || 'broadcast',
            type: MessageType.KNOWLEDGE_SHARE,
            content: knowledge,
            metadata: {
                priority: 'low',
                requiresResponse: false
            }
        });
    }

    /**
     * Request validation from another agent
     */
    public async requestValidation(
        from: string,
        validator: string,
        content: any
    ): Promise<any> {
        return this.request({
            from,
            to: validator,
            type: MessageType.VALIDATION_REQUEST,
            content,
            metadata: {
                priority: 'normal',
                requiresResponse: true
            }
        }, 15000);
    }

    /**
     * Report a conflict requiring arbitration
     */
    public async reportConflict(
        reportingAgent: string,
        conflictingAgents: string[],
        issue: any
    ): Promise<void> {
        // Send to OpusArbitrator
        await this.send({
            from: reportingAgent,
            to: 'OpusArbitrator',
            type: MessageType.CONFLICT,
            content: {
                conflictingAgents,
                issue,
                reportedBy: reportingAgent
            },
            metadata: {
                priority: 'critical',
                requiresResponse: true
            }
        });
    }

    /**
     * Process message queue
     */
    private async processQueue(): Promise<void> {
        if (this.processingQueue || this.messageQueue.length === 0) return;

        this.processingQueue = true;

        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift()!;

            try {
                await this.deliverMessage(message);
            } catch (error) {
                console.error(`Error delivering message ${message.id}:`, error);
                this.stats.failedMessages++;

                // Retry logic
                if (message.metadata.retryCount === undefined) {
                    message.metadata.retryCount = 0;
                }

                if (message.metadata.retryCount < 3) {
                    message.metadata.retryCount++;
                    this.messageQueue.push(message);
                } else {
                    this.eventBus.emit('message-failed', { message, error });
                }
            }
        }

        this.processingQueue = false;
    }

    /**
     * Deliver a message to recipients
     */
    private async deliverMessage(message: AgentMessage): Promise<void> {
        const recipients = this.determineRecipients(message);

        for (const recipientId of recipients) {
            const handlers = this.handlers.get(recipientId) || [];

            for (const handler of handlers) {
                // Check if handler accepts this message type
                if (!handler.messageTypes.includes(message.type)) continue;

                // Apply filter if present
                if (handler.filter && !handler.filter(message)) continue;

                try {
                    const response = await handler.handler(message);

                    // Handle response if required
                    if (message.metadata.requiresResponse && response !== undefined) {
                        // Send response back
                        await this.send({
                            from: recipientId,
                            to: message.from,
                            type: MessageType.RESPONSE,
                            content: response,
                            metadata: {
                                priority: 'normal',
                                requiresResponse: false,
                                conversationId: message.metadata.conversationId
                            },
                            replyTo: message.id
                        });

                        // Trigger callback if waiting
                        const callback = this.responseCallbacks.get(message.id);
                        if (callback) {
                            callback(response);
                        }
                    }

                    this.eventBus.emit('message-delivered', { message, recipientId });
                } catch (error) {
                    console.error(`Handler error for ${recipientId}:`, error);
                    this.eventBus.emit('handler-error', { message, recipientId, error });
                }
            }
        }
    }

    /**
     * Determine message recipients
     */
    private determineRecipients(message: AgentMessage): string[] {
        if (message.to === 'broadcast') {
            return Array.from(this.handlers.keys());
        }

        if (Array.isArray(message.to)) {
            return message.to;
        }

        return [message.to];
    }

    /**
     * Start queue processor
     */
    private startQueueProcessor(): void {
        setInterval(() => {
            if (!this.processingQueue && this.messageQueue.length > 0) {
                this.processQueue();
            }
        }, 100);
    }

    /**
     * Initialize statistics
     */
    private initializeStats(): CommunicationStats {
        return {
            totalMessages: 0,
            messagesByType: new Map(),
            messagesByAgent: new Map(),
            averageResponseTime: 0,
            activeSessions: 0,
            failedMessages: 0
        };
    }

    /**
     * Update statistics
     */
    private updateStats(message: AgentMessage): void {
        // Update message type count
        const typeCount = this.stats.messagesByType.get(message.type) || 0;
        this.stats.messagesByType.set(message.type, typeCount + 1);

        // Update agent message count
        const agentCount = this.stats.messagesByAgent.get(message.from) || 0;
        this.stats.messagesByAgent.set(message.from, agentCount + 1);

        // Update active sessions
        this.stats.activeSessions = this.collaborationSessions.size;
    }

    /**
     * Get communication statistics
     */
    public getStats(): CommunicationStats {
        // Calculate average response time
        let totalResponseTime = 0;
        let responseCount = 0;

        this.messageHistory.forEach(msg => {
            if (msg.type === MessageType.RESPONSE && msg.replyTo) {
                const originalMsg = this.messageHistory.find(m => m.id === msg.replyTo);
                if (originalMsg) {
                    totalResponseTime += msg.timestamp - originalMsg.timestamp;
                    responseCount++;
                }
            }
        });

        this.stats.averageResponseTime = responseCount > 0
            ? totalResponseTime / responseCount
            : 0;

        return { ...this.stats };
    }

    /**
     * Get message history
     */
    public getMessageHistory(filter?: {
        from?: string;
        to?: string;
        type?: MessageType;
        conversationId?: string;
        startTime?: number;
        endTime?: number;
    }): AgentMessage[] {
        let history = [...this.messageHistory];

        if (filter) {
            if (filter.from) {
                history = history.filter(msg => msg.from === filter.from);
            }
            if (filter.to) {
                history = history.filter(msg =>
                    msg.to === filter.to ||
                    (Array.isArray(msg.to) && msg.to.includes(filter.to!))
                );
            }
            if (filter.type) {
                history = history.filter(msg => msg.type === filter.type);
            }
            if (filter.conversationId) {
                history = history.filter(msg =>
                    msg.metadata.conversationId === filter.conversationId
                );
            }
            if (filter.startTime) {
                history = history.filter(msg => msg.timestamp >= filter.startTime!);
            }
            if (filter.endTime) {
                history = history.filter(msg => msg.timestamp <= filter.endTime!);
            }
        }

        return history;
    }

    /**
     * Get active collaboration sessions
     */
    public getActiveSessions(): CollaborationSession[] {
        return Array.from(this.collaborationSessions.values())
            .filter(session => session.status === 'active');
    }

    /**
     * Generate unique message ID
     */
    private generateMessageId(): string {
        return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Generate unique session ID
     */
    private generateSessionId(): string {
        return `ses_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Clear all data (for testing/reset)
     */
    public clear(): void {
        this.messageQueue = [];
        this.messageHistory = [];
        this.collaborationSessions.clear();
        this.responseCallbacks.clear();
        this.stats = this.initializeStats();
    }
}

// Export singleton instance getter
export function getCommunicationBus(): AgentCommunicationBus {
    return AgentCommunicationBus.getInstance();
}