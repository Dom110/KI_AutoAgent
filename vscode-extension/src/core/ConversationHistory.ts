import * as vscode from 'vscode';

export interface ConversationMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
    agent?: string;
    timestamp: string;
    metadata?: any;
}

export interface Conversation {
    id: string;
    title: string;
    created: string;
    lastModified: string;
    messages: ConversationMessage[];
}

export class ConversationHistory {
    private static instance: ConversationHistory;
    private context: vscode.ExtensionContext;
    private currentSessionId: string;
    private readonly MAX_HISTORY_SIZE = 50; // Maximum conversations
    private readonly MAX_MESSAGES_PER_CONVERSATION = 100;
    private readonly STORAGE_KEY = 'kiAutoAgent.conversations';
    private readonly CURRENT_SESSION_KEY = 'kiAutoAgent.currentSessionId';

    private constructor(context: vscode.ExtensionContext) {
        this.context = context;
        this.currentSessionId = this.loadCurrentSessionId() || this.generateSessionId();
    }

    public static initialize(context: vscode.ExtensionContext): ConversationHistory {
        if (!ConversationHistory.instance) {
            ConversationHistory.instance = new ConversationHistory(context);
        }
        return ConversationHistory.instance;
    }

    public static getInstance(): ConversationHistory {
        if (!ConversationHistory.instance) {
            throw new Error('ConversationHistory not initialized. Call initialize() first.');
        }
        return ConversationHistory.instance;
    }

    /**
     * Generate a new session ID
     */
    private generateSessionId(): string {
        const now = new Date();
        return `session_${now.getFullYear()}_${String(now.getMonth() + 1).padStart(2, '0')}_${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}_${String(now.getMinutes()).padStart(2, '0')}_${String(now.getSeconds()).padStart(2, '0')}`;
    }

    /**
     * Load current session ID from storage
     */
    private loadCurrentSessionId(): string | undefined {
        return this.context.globalState.get<string>(this.CURRENT_SESSION_KEY);
    }

    /**
     * Save current session ID to storage
     */
    private saveCurrentSessionId(sessionId: string): void {
        this.context.globalState.update(this.CURRENT_SESSION_KEY, sessionId);
    }

    /**
     * Get all conversations from storage
     */
    private getAllConversations(): Record<string, Conversation> {
        return this.context.globalState.get<Record<string, Conversation>>(this.STORAGE_KEY, {});
    }

    /**
     * Save all conversations to storage
     */
    private saveAllConversations(conversations: Record<string, Conversation>): void {
        // Limit to MAX_HISTORY_SIZE most recent conversations
        const sortedIds = Object.keys(conversations)
            .sort((a, b) => {
                const dateA = new Date(conversations[a].lastModified).getTime();
                const dateB = new Date(conversations[b].lastModified).getTime();
                return dateB - dateA; // Most recent first
            })
            .slice(0, this.MAX_HISTORY_SIZE);

        const limitedConversations: Record<string, Conversation> = {};
        sortedIds.forEach(id => {
            limitedConversations[id] = conversations[id];
        });

        this.context.globalState.update(this.STORAGE_KEY, limitedConversations);
    }

    /**
     * Create a new conversation session
     */
    public createNewSession(title?: string): string {
        const sessionId = this.generateSessionId();
        const now = new Date().toISOString();

        const conversation: Conversation = {
            id: sessionId,
            title: title || `Chat ${new Date().toLocaleString()}`,
            created: now,
            lastModified: now,
            messages: []
        };

        const conversations = this.getAllConversations();
        conversations[sessionId] = conversation;
        this.saveAllConversations(conversations);

        this.currentSessionId = sessionId;
        this.saveCurrentSessionId(sessionId);

        return sessionId;
    }

    /**
     * Get the current session
     */
    public getCurrentSession(): Conversation | null {
        const conversations = this.getAllConversations();
        if (!this.currentSessionId || !conversations[this.currentSessionId]) {
            // Create a new session if none exists
            this.currentSessionId = this.createNewSession();
            return this.getCurrentSession();
        }
        return conversations[this.currentSessionId];
    }

    /**
     * Add a message to the current conversation
     */
    public addMessage(message: ConversationMessage): void {
        const conversations = this.getAllConversations();
        const currentSession = this.getCurrentSession();

        if (!currentSession) {
            console.error('No current session available');
            return;
        }

        // Ensure we have the conversation in our local copy
        if (!conversations[this.currentSessionId]) {
            conversations[this.currentSessionId] = currentSession;
        }

        // Add timestamp if not present
        if (!message.timestamp) {
            message.timestamp = new Date().toISOString();
        }

        // Add message (limit to MAX_MESSAGES)
        conversations[this.currentSessionId].messages.push(message);

        // Limit messages to MAX_MESSAGES_PER_CONVERSATION
        if (conversations[this.currentSessionId].messages.length > this.MAX_MESSAGES_PER_CONVERSATION) {
            conversations[this.currentSessionId].messages =
                conversations[this.currentSessionId].messages.slice(-this.MAX_MESSAGES_PER_CONVERSATION);
        }

        // Update last modified time
        conversations[this.currentSessionId].lastModified = new Date().toISOString();

        // Update title if it's the first user message
        if (conversations[this.currentSessionId].messages.filter(m => m.role === 'user').length === 1
            && message.role === 'user') {
            const truncatedContent = message.content.substring(0, 50);
            conversations[this.currentSessionId].title = truncatedContent +
                (message.content.length > 50 ? '...' : '');
        }

        this.saveAllConversations(conversations);
    }

    /**
     * Save the current conversation (called before switching sessions)
     */
    public saveCurrentConversation(): void {
        // Messages are already saved incrementally via addMessage
        // This method is here for explicit save if needed
        const conversations = this.getAllConversations();
        if (this.currentSessionId && conversations[this.currentSessionId]) {
            conversations[this.currentSessionId].lastModified = new Date().toISOString();
            this.saveAllConversations(conversations);
        }
    }

    /**
     * Load a specific conversation by ID
     */
    public loadConversation(sessionId: string): Conversation | null {
        const conversations = this.getAllConversations();
        if (conversations[sessionId]) {
            this.currentSessionId = sessionId;
            this.saveCurrentSessionId(sessionId);
            return conversations[sessionId];
        }
        return null;
    }

    /**
     * Get list of all conversations (for history view)
     */
    public listConversations(): Conversation[] {
        const conversations = this.getAllConversations();
        return Object.values(conversations)
            .sort((a, b) => {
                const dateA = new Date(a.lastModified).getTime();
                const dateB = new Date(b.lastModified).getTime();
                return dateB - dateA; // Most recent first
            });
    }

    /**
     * Clear a specific conversation
     */
    public clearConversation(sessionId: string): void {
        const conversations = this.getAllConversations();
        delete conversations[sessionId];
        this.saveAllConversations(conversations);

        // If we cleared the current session, create a new one
        if (sessionId === this.currentSessionId) {
            this.createNewSession();
        }
    }

    /**
     * Clear all conversation history
     */
    public clearAllHistory(): void {
        this.context.globalState.update(this.STORAGE_KEY, {});
        this.createNewSession();
    }

    /**
     * Get messages for the current session
     */
    public getCurrentMessages(): ConversationMessage[] {
        const session = this.getCurrentSession();
        return session ? session.messages : [];
    }

    /**
     * Get current session ID
     */
    public getCurrentSessionId(): string {
        return this.currentSessionId;
    }

    /**
     * Update conversation settings from VS Code configuration
     */
    public updateSettings(): void {
        const config = vscode.workspace.getConfiguration('kiAutoAgent.history');
        const maxConversations = config.get<number>('maxConversations');
        const maxMessages = config.get<number>('maxMessagesPerConversation');

        if (maxConversations && maxConversations > 0) {
            (this as any).MAX_HISTORY_SIZE = maxConversations;
        }
        if (maxMessages && maxMessages > 0) {
            (this as any).MAX_MESSAGES_PER_CONVERSATION = maxMessages;
        }
    }
}