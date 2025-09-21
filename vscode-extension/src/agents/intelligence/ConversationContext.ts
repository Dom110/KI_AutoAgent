/**
 * Conversation Context Management for Intelligent Decision Making
 * Tracks conversation history, user patterns, and learning from interactions
 */

import {
    ConversationMessage,
    UserCommunicationPattern,
    ProposedPlan,
    ClassificationMetrics
} from '../../types/IntentTypes';

/**
 * Manages conversation context and learns from user interactions
 */
export class ConversationContext {
    /**
     * Conversation history
     */
    private history: ConversationMessage[] = [];

    /**
     * History of proposed plans
     */
    private planHistory: ProposedPlan[] = [];

    /**
     * Learned user communication patterns
     */
    private userPatterns: UserCommunicationPattern = {
        prefersExplicitConfirmation: false,
        averageResponseTime: 0,
        typicalPhrases: [],
        confirmationStyle: 'direct',
        classificationAccuracy: 0,
        sampleSize: 0
    };

    /**
     * Classification metrics for monitoring
     */
    private metrics: ClassificationMetrics = {
        totalClassifications: 0,
        correctClassifications: 0,
        falsePositives: 0,
        falseNegatives: 0,
        averageConfidence: 0,
        userCorrections: 0,
        accuracyByIntent: new Map(),
        improvementTrend: []
    };

    /**
     * Response time tracking
     */
    private lastMessageTime: Date | null = null;

    /**
     * Learning data for pattern recognition
     */
    private learningData: Map<string, any> = new Map();

    /**
     * Add a message to conversation history
     */
    public addMessage(message: ConversationMessage): void {
        // Track response time
        if (message.role === 'user' && this.lastMessageTime) {
            const responseTime = (message.timestamp.getTime() - this.lastMessageTime.getTime()) / 1000;
            this.updateAverageResponseTime(responseTime);
        }

        // Add to history
        this.history.push(message);

        // Update last message time
        if (message.role === 'assistant') {
            this.lastMessageTime = message.timestamp;
        }

        // Keep history size manageable (last 100 messages)
        if (this.history.length > 100) {
            this.history = this.history.slice(-100);
        }

        // Extract typical phrases from user messages
        if (message.role === 'user') {
            this.extractTypicalPhrases(message.content);
        }
    }

    /**
     * Get recent conversation context
     */
    public getRecentContext(messageCount: number = 5): ConversationMessage[] {
        return this.history.slice(-messageCount);
    }

    /**
     * Get time since last proposed plan (in seconds)
     */
    public getTimeSinceLastPlan(): number {
        if (this.planHistory.length === 0) {
            return Infinity;
        }

        const lastPlan = this.planHistory[this.planHistory.length - 1];
        return (Date.now() - lastPlan.timestamp.getTime()) / 1000;
    }

    /**
     * Add a proposed plan to history
     */
    public addProposedPlan(plan: ProposedPlan): void {
        this.planHistory.push(plan);

        // Keep only last 10 plans
        if (this.planHistory.length > 10) {
            this.planHistory = this.planHistory.slice(-10);
        }
    }

    /**
     * Get the last proposed plan
     */
    public getLastProposedPlan(): ProposedPlan | null {
        return this.planHistory.length > 0
            ? this.planHistory[this.planHistory.length - 1]
            : null;
    }

    /**
     * Get user's communication style based on learned patterns
     */
    public getUserCommunicationStyle(): 'direct' | 'indirect' | 'conditional' {
        return this.userPatterns.confirmationStyle;
    }

    /**
     * Calculate plan rejection rate
     */
    public getPlanRejectionRate(): number {
        if (this.planHistory.length === 0) {
            return 0;
        }

        const rejectedPlans = this.planHistory.filter(p => p.status === 'rejected').length;
        return rejectedPlans / this.planHistory.length;
    }

    /**
     * Learn from user interaction
     */
    public learnFromInteraction(
        intent: string,
        wasCorrect: boolean,
        userCorrection?: string
    ): void {
        // Update metrics
        this.metrics.totalClassifications++;

        if (wasCorrect) {
            this.metrics.correctClassifications++;
        } else {
            if (userCorrection) {
                this.metrics.userCorrections++;
            }
        }

        // Update accuracy by intent
        const currentAccuracy = this.metrics.accuracyByIntent.get(intent) || 0;
        const currentCount = this.learningData.get(`${intent}_count`) || 0;
        const newAccuracy = (currentAccuracy * currentCount + (wasCorrect ? 1 : 0)) / (currentCount + 1);
        this.metrics.accuracyByIntent.set(intent, newAccuracy);
        this.learningData.set(`${intent}_count`, currentCount + 1);

        // Update user patterns
        this.updateUserPatterns(intent, wasCorrect);

        // Calculate overall accuracy
        this.updateOverallAccuracy();
    }

    /**
     * Get user communication patterns
     */
    public getUserPatterns(): UserCommunicationPattern {
        return { ...this.userPatterns };
    }

    /**
     * Get classification metrics
     */
    public getMetrics(): ClassificationMetrics {
        return { ...this.metrics };
    }

    /**
     * Check if user prefers explicit confirmations
     */
    public prefersExplicitConfirmation(): boolean {
        // If user has corrected false positives multiple times, prefer explicit
        const falsePositiveRate = this.metrics.falsePositives / Math.max(1, this.metrics.totalClassifications);
        return falsePositiveRate > 0.2 || this.userPatterns.prefersExplicitConfirmation;
    }

    /**
     * Get confidence adjustment based on context
     */
    public getConfidenceAdjustment(baseConfidence: number): number {
        let adjustment = 0;

        // Reduce confidence if time since plan is high
        const timeSinceLastPlan = this.getTimeSinceLastPlan();
        if (timeSinceLastPlan > 300) { // 5 minutes
            adjustment -= 0.2;
        } else if (timeSinceLastPlan > 60) { // 1 minute
            adjustment -= 0.1;
        }

        // Increase confidence if user typically confirms quickly
        if (this.userPatterns.averageResponseTime < 5 && timeSinceLastPlan < 10) {
            adjustment += 0.1;
        }

        // Reduce confidence if rejection rate is high
        const rejectionRate = this.getPlanRejectionRate();
        if (rejectionRate > 0.5) {
            adjustment -= 0.15;
        }

        // Adjust based on historical accuracy
        const overallAccuracy = this.metrics.correctClassifications / Math.max(1, this.metrics.totalClassifications);
        if (overallAccuracy < 0.7) {
            adjustment -= 0.1;
        } else if (overallAccuracy > 0.9) {
            adjustment += 0.05;
        }

        return Math.max(-0.3, Math.min(0.2, adjustment));
    }

    /**
     * Analyze if response seems conditional (e.g., "yes, but...")
     */
    public analyzeConditionalResponse(text: string): boolean {
        const conditionalPatterns = [
            /\b(aber|but|jedoch|though|although|falls|wenn|if|sofern)\b/i,
            /\b(ja|yes|ok).*\b(aber|but|jedoch|though)\b/i,
            /\b(erst|zuerst|first|before|vorher)\b/i,
            /\b(nachdem|after|dann|then)\b/i
        ];

        return conditionalPatterns.some(pattern => pattern.test(text));
    }

    /**
     * Clear conversation context
     */
    public clear(): void {
        this.history = [];
        this.lastMessageTime = null;
    }

    /**
     * Export learning data for persistence
     */
    public exportLearningData(): string {
        return JSON.stringify({
            userPatterns: this.userPatterns,
            metrics: this.metrics,
            learningData: Array.from(this.learningData.entries())
        });
    }

    /**
     * Import learning data from persistence
     */
    public importLearningData(data: string): void {
        try {
            const parsed = JSON.parse(data);
            this.userPatterns = parsed.userPatterns || this.userPatterns;
            this.metrics = parsed.metrics || this.metrics;
            this.learningData = new Map(parsed.learningData || []);

            // Recreate Map for accuracyByIntent
            if (parsed.metrics?.accuracyByIntent) {
                this.metrics.accuracyByIntent = new Map(Object.entries(parsed.metrics.accuracyByIntent));
            }
        } catch (error) {
            console.error('Failed to import learning data:', error);
        }
    }

    // Private helper methods

    /**
     * Update average response time
     */
    private updateAverageResponseTime(responseTime: number): void {
        const currentAvg = this.userPatterns.averageResponseTime;
        const sampleSize = this.userPatterns.sampleSize;

        this.userPatterns.averageResponseTime =
            (currentAvg * sampleSize + responseTime) / (sampleSize + 1);
        this.userPatterns.sampleSize++;
    }

    /**
     * Extract typical phrases from user messages
     */
    private extractTypicalPhrases(text: string): void {
        // Extract confirmation-like phrases
        const confirmationPhrases = [
            /\b(ja|yes|ok|okay|gut|good|mach|do|los|go|weiter|continue)\b/gi,
            /\b(genau|exactly|richtig|correct|stimmt|right)\b/gi,
            /\b(perfekt|perfect|super|great|klasse)\b/gi
        ];

        for (const pattern of confirmationPhrases) {
            const matches = text.match(pattern);
            if (matches) {
                for (const match of matches) {
                    if (!this.userPatterns.typicalPhrases.includes(match.toLowerCase())) {
                        this.userPatterns.typicalPhrases.push(match.toLowerCase());
                    }
                }
            }
        }

        // Keep only the 20 most common phrases
        if (this.userPatterns.typicalPhrases.length > 20) {
            this.userPatterns.typicalPhrases = this.userPatterns.typicalPhrases.slice(-20);
        }
    }

    /**
     * Update user patterns based on interactions
     */
    private updateUserPatterns(intent: string, wasCorrect: boolean): void {
        // Detect if user prefers explicit confirmations
        if (intent === 'confirm_execution' && !wasCorrect) {
            this.metrics.falsePositives++;

            // If we have multiple false positives, user likely prefers explicit
            if (this.metrics.falsePositives > 2) {
                this.userPatterns.prefersExplicitConfirmation = true;
            }
        }

        // Detect confirmation style
        const recentMessages = this.getRecentContext(10);
        const userMessages = recentMessages.filter(m => m.role === 'user');

        let directCount = 0;
        let conditionalCount = 0;

        for (const msg of userMessages) {
            if (this.analyzeConditionalResponse(msg.content)) {
                conditionalCount++;
            } else if (msg.content.length < 20) { // Short messages are often direct
                directCount++;
            }
        }

        if (conditionalCount > directCount * 1.5) {
            this.userPatterns.confirmationStyle = 'conditional';
        } else if (directCount > conditionalCount * 2) {
            this.userPatterns.confirmationStyle = 'direct';
        } else {
            this.userPatterns.confirmationStyle = 'indirect';
        }
    }

    /**
     * Update overall classification accuracy
     */
    private updateOverallAccuracy(): void {
        const accuracy = this.metrics.correctClassifications /
                        Math.max(1, this.metrics.totalClassifications);

        this.userPatterns.classificationAccuracy = accuracy;

        // Update improvement trend
        this.metrics.improvementTrend.push(accuracy * 100);

        // Keep only last 20 data points for trend
        if (this.metrics.improvementTrend.length > 20) {
            this.metrics.improvementTrend = this.metrics.improvementTrend.slice(-20);
        }
    }
}