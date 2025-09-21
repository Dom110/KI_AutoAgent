/**
 * Manages conversation context and history across multiple agent interactions
 * Ensures that agents can access and build upon previous outputs
 */

export interface ConversationEntry {
    timestamp: string;
    agent: string;
    step: string;
    input: string;
    output: string;
    metadata?: any;
}

export class ConversationContextManager {
    private static instance: ConversationContextManager;
    private conversationHistory: ConversationEntry[] = [];
    private maxHistorySize: number = 50; // Keep last 50 interactions
    
    private constructor() {}
    
    public static getInstance(): ConversationContextManager {
        if (!ConversationContextManager.instance) {
            ConversationContextManager.instance = new ConversationContextManager();
        }
        return ConversationContextManager.instance;
    }
    
    /**
     * Add a new entry to the conversation history
     */
    public addEntry(entry: ConversationEntry): void {
        this.conversationHistory.push(entry);
        
        // Trim history if it exceeds max size
        if (this.conversationHistory.length > this.maxHistorySize) {
            this.conversationHistory = this.conversationHistory.slice(-this.maxHistorySize);
        }
        
        console.log(`[CONTEXT-MANAGER] Added entry from ${entry.agent} (${entry.step})`);
        console.log(`[CONTEXT-MANAGER] Total history size: ${this.conversationHistory.length} entries`);
    }
    
    /**
     * Get recent conversation history
     */
    public getRecentHistory(limit: number = 5): ConversationEntry[] {
        return this.conversationHistory.slice(-limit);
    }
    
    /**
     * Get conversation history for a specific agent
     */
    public getAgentHistory(agentName: string, limit: number = 5): ConversationEntry[] {
        return this.conversationHistory
            .filter(entry => entry.agent === agentName)
            .slice(-limit);
    }
    
    /**
     * Get formatted conversation context for inclusion in prompts
     */
    public getFormattedContext(limit: number = 5): string {
        const recent = this.getRecentHistory(limit);
        if (recent.length === 0) {
            return '';
        }
        
        let context = '\n## Conversation History:\n';
        recent.forEach(entry => {
            context += `\n### ${entry.agent} (${entry.step}) - ${entry.timestamp}:\n`;
            context += `**Input:** ${entry.input.substring(0, 200)}...\n`;
            context += `**Output:** ${entry.output.substring(0, 500)}...\n`;
        });
        
        return context;
    }
    
    /**
     * Get the last output from any agent
     */
    public getLastOutput(): string | null {
        if (this.conversationHistory.length === 0) {
            return null;
        }
        return this.conversationHistory[this.conversationHistory.length - 1].output;
    }
    
    /**
     * Clear conversation history
     */
    public clearHistory(): void {
        this.conversationHistory = [];
        console.log(`[CONTEXT-MANAGER] Conversation history cleared`);
    }
    
    /**
     * Export conversation history as JSON
     */
    public exportHistory(): string {
        return JSON.stringify(this.conversationHistory, null, 2);
    }
    
    /**
     * Import conversation history from JSON
     */
    public importHistory(jsonData: string): void {
        try {
            const imported = JSON.parse(jsonData);
            if (Array.isArray(imported)) {
                this.conversationHistory = imported;
                console.log(`[CONTEXT-MANAGER] Imported ${imported.length} conversation entries`);
            }
        } catch (error) {
            console.error(`[CONTEXT-MANAGER] Failed to import history: ${error}`);
        }
    }

    /**
     * Clear the conversation context
     */
    public clearContext(): void {
        this.conversationHistory = [];
        console.log('[CONTEXT-MANAGER] Conversation history cleared');
    }
}