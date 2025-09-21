/**
 * Type definitions for AI-based Intent Classification System
 * Provides intelligent understanding of user confirmations and requests
 */

/**
 * Main classification result from AI intent analysis
 */
export interface IntentClassification {
    /**
     * The classified intent type
     */
    intent:
        | 'confirm_execution'      // User wants to execute the proposed plan
        | 'request_clarification'  // User needs more information
        | 'reject'                 // User declines the plan
        | 'modify_plan'            // User wants changes to the plan
        | 'new_request'            // Completely new request, ignoring plan
        | 'uncertain';             // AI cannot determine intent clearly

    /**
     * Confidence score (0.0 - 1.0)
     * <0.6: Low confidence, should ask for clarification
     * 0.6-0.8: Medium confidence, may proceed with caution
     * >0.8: High confidence, can proceed
     */
    confidence: number;

    /**
     * AI's reasoning for this classification
     */
    reasoning: string;

    /**
     * Suggested next action based on the classification
     */
    suggestedAction: string;

    /**
     * Contextual factors that influenced the decision
     */
    contextFactors: ContextFactors;
}

/**
 * Contextual factors affecting intent classification
 */
export interface ContextFactors {
    /**
     * Time elapsed since plan was proposed (in seconds)
     */
    timeElapsed: number;

    /**
     * Previous intent from conversation history
     */
    previousIntent: string | null;

    /**
     * Detected user tone/sentiment
     */
    userTone: 'positive' | 'neutral' | 'negative' | 'uncertain';

    /**
     * Whether conditional approval was detected (e.g., "yes, but...")
     */
    hasConditions: boolean;

    /**
     * Detected language of the user input
     */
    language: string;

    /**
     * Whether sarcasm was detected
     */
    sarcasmDetected: boolean;

    /**
     * Urgency level of the request
     */
    urgencyLevel: 'high' | 'medium' | 'low';
}

/**
 * User communication pattern learned over time
 */
export interface UserCommunicationPattern {
    /**
     * Whether user typically uses explicit confirmations
     */
    prefersExplicitConfirmation: boolean;

    /**
     * Average time user takes to respond (in seconds)
     */
    averageResponseTime: number;

    /**
     * Common phrases used by this user
     */
    typicalPhrases: string[];

    /**
     * User's typical confirmation style
     */
    confirmationStyle: 'direct' | 'indirect' | 'conditional';

    /**
     * Accuracy of past classifications for this user
     */
    classificationAccuracy: number;

    /**
     * Number of interactions analyzed
     */
    sampleSize: number;
}

/**
 * Options for classification request
 */
export interface ClassificationOptions {
    /**
     * Whether to use multiple AI models for consensus
     */
    useConsensus?: boolean;

    /**
     * Minimum confidence threshold
     */
    minConfidence?: number;

    /**
     * Whether to detect sarcasm
     */
    detectSarcasm?: boolean;

    /**
     * Whether to analyze urgency
     */
    analyzeUrgency?: boolean;

    /**
     * Maximum response time in milliseconds
     */
    timeout?: number;

    /**
     * Preferred AI provider
     */
    provider?: 'gpt-4' | 'claude' | 'auto';
}

/**
 * Message in conversation history
 */
export interface ConversationMessage {
    /**
     * Who sent the message
     */
    role: 'user' | 'assistant' | 'system';

    /**
     * Message content
     */
    content: string;

    /**
     * When the message was sent
     */
    timestamp: Date;

    /**
     * Optional metadata
     */
    metadata?: {
        intent?: string;
        confidence?: number;
        planId?: string;
        [key: string]: any;
    };
}

/**
 * Proposed plan structure
 */
export interface ProposedPlan {
    /**
     * Unique identifier for the plan
     */
    id: string;

    /**
     * Description of what the plan will do
     */
    description: string;

    /**
     * Original user prompt that triggered this plan
     */
    originalPrompt: string;

    /**
     * When the plan was proposed
     */
    timestamp: Date;

    /**
     * Steps in the plan
     */
    steps: PlanStep[];

    /**
     * Current status
     */
    status: 'proposed' | 'accepted' | 'rejected' | 'modified' | 'executed';
}

/**
 * Individual step in a plan
 */
export interface PlanStep {
    /**
     * Execution order
     */
    order: number;

    /**
     * Which agent will execute this step
     */
    agentName: string;

    /**
     * Task to be performed
     */
    task: string;

    /**
     * Human-readable description
     */
    description: string;

    /**
     * Dependencies on other steps
     */
    dependencies?: string[];

    /**
     * Estimated duration in seconds
     */
    estimatedDuration?: number;
}

/**
 * Classification metrics for monitoring
 */
export interface ClassificationMetrics {
    /**
     * Total number of classifications performed
     */
    totalClassifications: number;

    /**
     * Number of correct classifications (validated by user)
     */
    correctClassifications: number;

    /**
     * Classifications where execution happened incorrectly
     */
    falsePositives: number;

    /**
     * Classifications where execution should have happened but didn't
     */
    falseNegatives: number;

    /**
     * Average confidence across all classifications
     */
    averageConfidence: number;

    /**
     * Number of times user corrected the classification
     */
    userCorrections: number;

    /**
     * Accuracy by intent type
     */
    accuracyByIntent: Map<string, number>;

    /**
     * Improvement trend over time (percentage)
     */
    improvementTrend: number[];
}

/**
 * Configuration for AI Classification
 */
export interface AIClassificationConfig {
    /**
     * Whether AI classification is enabled
     */
    enabled: boolean;

    /**
     * Primary AI provider
     */
    provider: 'gpt-4' | 'claude' | 'auto';

    /**
     * Confidence threshold for automatic execution
     */
    confidenceThreshold: number;

    /**
     * Whether to require explicit confirmation for low confidence
     */
    requireExplicitConfirmation: boolean;

    /**
     * Whether to learn from user corrections
     */
    learnFromCorrections: boolean;

    /**
     * Whether to use multiple models for consensus
     */
    multiModelConsensus: boolean;

    /**
     * Cache duration for classifications (in seconds)
     */
    cacheDuration: number;
}