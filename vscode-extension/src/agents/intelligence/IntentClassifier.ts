/**
 * AI-based Intent Classification for Natural Language Understanding
 * Replaces primitive keyword matching with intelligent context-aware classification
 */

import {
    IntentClassification,
    ConversationMessage,
    ProposedPlan,
    ContextFactors,
    ClassificationOptions
} from '../../types/IntentTypes';
import { ConversationContext } from './ConversationContext';

/**
 * Intelligent Intent Classifier using AI for natural language understanding
 */
export class IntentClassifier {
    /**
     * AI service for classification (will be injected)
     */
    private aiService: any;

    /**
     * Conversation context manager
     */
    private context: ConversationContext;

    /**
     * Cache for recent classifications
     */
    private classificationCache: Map<string, IntentClassification> = new Map();

    /**
     * Cache duration in milliseconds
     */
    private readonly CACHE_DURATION = 5000; // 5 seconds

    constructor(aiService: any, context: ConversationContext) {
        this.aiService = aiService;
        this.context = context;
    }

    /**
     * Classify user intent using AI
     */
    public async classifyIntent(
        userInput: string,
        proposedPlan: ProposedPlan | null,
        conversationHistory: ConversationMessage[],
        options: ClassificationOptions = {}
    ): Promise<IntentClassification> {
        // Check cache first
        const cacheKey = this.getCacheKey(userInput, proposedPlan?.id);
        const cached = this.getCachedClassification(cacheKey);
        if (cached) {
            return cached;
        }

        try {
            // Build comprehensive context
            const contextFactors = await this.analyzeContextFactors(userInput, proposedPlan);

            // Build AI prompt
            const prompt = this.buildClassificationPrompt(
                userInput,
                proposedPlan,
                conversationHistory,
                contextFactors
            );

            // Get AI classification
            const aiResponse = await this.aiService.classify(prompt, options);

            // Parse and validate AI response
            const classification = this.parseAIResponse(aiResponse, contextFactors);

            // Apply confidence adjustments based on context
            classification.confidence += this.context.getConfidenceAdjustment(classification.confidence);
            classification.confidence = Math.max(0, Math.min(1, classification.confidence));

            // Cache the result
            this.cacheClassification(cacheKey, classification);

            return classification;
        } catch (error) {
            console.error('Classification failed:', error);

            // Fallback classification
            return this.getFallbackClassification(userInput, proposedPlan);
        }
    }

    /**
     * Build AI prompt for classification
     */
    private buildClassificationPrompt(
        userInput: string,
        proposedPlan: ProposedPlan | null,
        conversationHistory: ConversationMessage[],
        contextFactors: ContextFactors
    ): string {
        const userPatterns = this.context.getUserPatterns();
        const rejectionRate = this.context.getPlanRejectionRate();

        return `You are an intent classifier for a multi-agent AI system. Analyze the user's response to determine their intent.

CONTEXT:
${proposedPlan ? `
- A plan was proposed ${contextFactors.timeElapsed} seconds ago
- Plan: "${proposedPlan.description}"
- Plan steps: ${proposedPlan.steps.map(s => `${s.order}. ${s.agentName}: ${s.task}`).join('\n  ')}
- Original request: "${proposedPlan.originalPrompt}"
` : '- No plan has been proposed recently'}

CONVERSATION HISTORY (last ${conversationHistory.length} messages):
${conversationHistory.map(msg => `${msg.role}: ${msg.content}`).join('\n')}

USER'S CURRENT MESSAGE: "${userInput}"

USER BEHAVIOR PATTERNS:
- Typical confirmation style: ${userPatterns.confirmationStyle}
- Average response time: ${userPatterns.averageResponseTime.toFixed(1)}s
- Common phrases: ${userPatterns.typicalPhrases.slice(0, 5).join(', ')}
- Historical plan rejection rate: ${(rejectionRate * 100).toFixed(1)}%

CLASSIFY the user's intent into ONE of these categories:

1. "confirm_execution" - User wants to execute the proposed plan
   Examples: "ja", "mach das", "los geht's", "sounds good", "let's do it", "perfekt"

2. "request_clarification" - User wants more information before deciding
   Examples: "zeig mir mehr", "was genau?", "explain more", "und dann?", "wie funktioniert das?"

3. "reject" - User doesn't want this plan
   Examples: "nein", "nicht so", "anders", "stop", "vergiss es", "cancel"

4. "modify_plan" - User wants changes to the plan
   Examples: "ja aber anders", "fast richtig", "ändere schritt 2", "but change X"

5. "new_request" - This is a completely new request, ignoring the plan
   Examples: Starting with "ich will", "create", "build", unrelated to plan

6. "uncertain" - Cannot determine intent clearly

IMPORTANT NUANCES TO CONSIDER:
- "ja, aber..." often means "modify_plan", not "confirm_execution"
- "ok" alone might be acknowledgment, not confirmation (check context)
- Short responses like "gut" need context - could be approval or just acknowledgment
- Time elapsed matters: old plans + "ok" = likely not confirmation
- Sarcasm: "super idee 🙄" = likely "reject"
- Questions usually mean "request_clarification"
- Conditional language ("wenn", "falls", "sofern") suggests "modify_plan" or "request_clarification"

RESPONSE FORMAT (JSON):
{
  "intent": "<category>",
  "confidence": <0.0-1.0>,
  "reasoning": "<explain your classification>",
  "suggestedAction": "<what should happen next>",
  "keyIndicators": ["<phrase1>", "<phrase2>"],
  "hasConditions": <true/false>,
  "sentimentAnalysis": "<positive/neutral/negative>"
}

Consider:
- If time > 60 seconds since plan, reduce confidence by 20%
- If message contains questions, lean toward "request_clarification"
- If message is very short (<5 chars), check if it matches user's typical phrases
- German and English inputs should be handled equally well`;
    }

    /**
     * Parse AI response into IntentClassification
     */
    private parseAIResponse(
        aiResponse: any,
        contextFactors: ContextFactors
    ): IntentClassification {
        try {
            // Handle both string and object responses
            const parsed = typeof aiResponse === 'string'
                ? JSON.parse(aiResponse)
                : aiResponse;

            // Map sentiment to tone
            const sentimentToTone: Record<string, any> = {
                'positive': 'positive',
                'neutral': 'neutral',
                'negative': 'negative'
            };

            return {
                intent: parsed.intent || 'uncertain',
                confidence: Math.max(0, Math.min(1, parsed.confidence || 0.5)),
                reasoning: parsed.reasoning || 'AI classification completed',
                suggestedAction: parsed.suggestedAction || this.getDefaultAction(parsed.intent),
                contextFactors: {
                    ...contextFactors,
                    hasConditions: parsed.hasConditions || false,
                    userTone: sentimentToTone[parsed.sentimentAnalysis] || 'neutral'
                }
            };
        } catch (error) {
            console.error('Failed to parse AI response:', error);

            // Return uncertain classification
            return {
                intent: 'uncertain',
                confidence: 0.3,
                reasoning: 'Failed to parse AI response',
                suggestedAction: 'Ask user for clarification',
                contextFactors
            };
        }
    }

    /**
     * Analyze context factors
     */
    private async analyzeContextFactors(
        userInput: string,
        proposedPlan: ProposedPlan | null
    ): Promise<ContextFactors> {
        const timeElapsed = proposedPlan
            ? (Date.now() - proposedPlan.timestamp.getTime()) / 1000
            : Infinity;

        // Detect conditions in input
        const hasConditions = this.context.analyzeConditionalResponse(userInput);

        // Detect language (simple heuristic, could be enhanced with AI)
        const language = this.detectLanguage(userInput);

        // Simple sarcasm detection (could be enhanced with AI)
        const sarcasmDetected = this.detectSarcasm(userInput);

        // Analyze urgency
        const urgencyLevel = this.analyzeUrgency(userInput);

        // Get previous intent from context
        const recentHistory = this.context.getRecentContext(2);
        const previousIntent = recentHistory.length > 0
            ? recentHistory[0].metadata?.intent || null
            : null;

        return {
            timeElapsed,
            previousIntent,
            userTone: 'neutral', // Will be updated by AI
            hasConditions,
            language,
            sarcasmDetected,
            urgencyLevel
        };
    }

    /**
     * Get default action for an intent
     */
    private getDefaultAction(intent: string): string {
        const actions: Record<string, string> = {
            'confirm_execution': 'Execute the proposed plan',
            'request_clarification': 'Provide more details about the plan',
            'reject': 'Cancel the plan and ask for alternatives',
            'modify_plan': 'Ask for specific modifications',
            'new_request': 'Process as a new request',
            'uncertain': 'Ask user to clarify their intent'
        };

        return actions[intent] || actions['uncertain'];
    }

    /**
     * Fallback classification when AI fails
     */
    private getFallbackClassification(
        userInput: string,
        proposedPlan: ProposedPlan | null
    ): IntentClassification {
        const input = userInput.toLowerCase().trim();
        const hasConditions = this.context.analyzeConditionalResponse(userInput);

        // Simple keyword-based fallback
        let intent: any = 'uncertain';
        let confidence = 0.3;
        let reasoning = 'Fallback classification (AI unavailable)';

        // Check for clear confirmations
        if (/^(ja|yes|ok|okay|gut|good|mach|los|go|genau|exactly)$/i.test(input)) {
            intent = proposedPlan ? 'confirm_execution' : 'uncertain';
            confidence = proposedPlan && this.context.getTimeSinceLastPlan() < 30 ? 0.6 : 0.3;
            reasoning = 'Simple affirmative detected';
        }
        // Check for clear rejections
        else if (/^(nein|no|nicht|not|stop|cancel|abbrechen)$/i.test(input)) {
            intent = 'reject';
            confidence = 0.7;
            reasoning = 'Clear rejection detected';
        }
        // Check for questions
        else if (input.includes('?') || /\b(was|wie|warum|wann|wo|what|how|why|when|where)\b/i.test(input)) {
            intent = 'request_clarification';
            confidence = 0.6;
            reasoning = 'Question detected';
        }
        // Check for conditional responses
        else if (hasConditions) {
            intent = 'modify_plan';
            confidence = 0.5;
            reasoning = 'Conditional language detected';
        }

        const timeElapsed = proposedPlan
            ? (Date.now() - proposedPlan.timestamp.getTime()) / 1000
            : Infinity;

        return {
            intent,
            confidence,
            reasoning,
            suggestedAction: this.getDefaultAction(intent),
            contextFactors: {
                timeElapsed,
                previousIntent: null,
                userTone: 'neutral',
                hasConditions,
                language: 'unknown',
                sarcasmDetected: false,
                urgencyLevel: 'medium'
            }
        };
    }

    /**
     * Simple language detection
     */
    private detectLanguage(text: string): string {
        const germanIndicators = /\b(der|die|das|ich|du|sie|wir|ihr|ist|sind|haben|werden|können|müssen|aber|und|oder|nicht|kein|mach|zeig)\b/gi;
        const englishIndicators = /\b(the|a|an|i|you|he|she|we|they|is|are|have|will|can|must|but|and|or|not|no|do|show)\b/gi;

        const germanCount = (text.match(germanIndicators) || []).length;
        const englishCount = (text.match(englishIndicators) || []).length;

        if (germanCount > englishCount) {
            return 'de';
        } else if (englishCount > germanCount) {
            return 'en';
        } else {
            return 'unknown';
        }
    }

    /**
     * Simple sarcasm detection
     */
    private detectSarcasm(text: string): boolean {
        const sarcasmIndicators = [
            /\.\.\./,                    // Ellipsis often indicates sarcasm
            /🙄|😒|😏|🤨/,               // Sarcastic emojis
            /\bnicht\s*\.$/i,            // "... nicht." at end
            /\b(toll|super|klasse).*\./i, // Overly positive with period
            /\byeah\s+right\b/i,         // "yeah right"
            /\bas\s+if\b/i,              // "as if"
        ];

        return sarcasmIndicators.some(pattern => pattern.test(text));
    }

    /**
     * Analyze urgency level
     */
    private analyzeUrgency(text: string): 'high' | 'medium' | 'low' {
        const highUrgency = /\b(sofort|immediately|jetzt|now|schnell|quick|asap|dringend|urgent)\b/i;
        const lowUrgency = /\b(später|later|wenn du zeit hast|when you have time|kein stress|no rush)\b/i;

        if (highUrgency.test(text)) {
            return 'high';
        } else if (lowUrgency.test(text)) {
            return 'low';
        } else {
            return 'medium';
        }
    }

    /**
     * Generate cache key
     */
    private getCacheKey(userInput: string, planId?: string): string {
        return `${userInput.toLowerCase().trim()}_${planId || 'no-plan'}`;
    }

    /**
     * Get cached classification if still valid
     */
    private getCachedClassification(key: string): IntentClassification | null {
        const cached = this.classificationCache.get(key);
        if (!cached) {
            return null;
        }

        // Check if cache is still valid
        const age = Date.now() - (cached as any).timestamp;
        if (age > this.CACHE_DURATION) {
            this.classificationCache.delete(key);
            return null;
        }

        return cached;
    }

    /**
     * Cache a classification
     */
    private cacheClassification(key: string, classification: IntentClassification): void {
        (classification as any).timestamp = Date.now();
        this.classificationCache.set(key, classification);

        // Clean old cache entries
        if (this.classificationCache.size > 100) {
            const oldestKey = this.classificationCache.keys().next().value;
            if (oldestKey !== undefined) {
                this.classificationCache.delete(oldestKey);
            }
        }
    }

    /**
     * Clear classification cache
     */
    public clearCache(): void {
        this.classificationCache.clear();
    }
}