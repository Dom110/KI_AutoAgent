/**
 * AI Classification Service
 * Provides unified interface for AI-based intent classification using multiple providers
 */

import * as vscode from 'vscode';
import { ClassificationOptions } from '../types/IntentTypes';

/**
 * Service for AI-based classification with multiple AI providers
 */
export class AIClassificationService {
    /**
     * Primary AI provider
     */
    private primaryAI: 'gpt-4' | 'claude' | 'auto';

    /**
     * Fallback AI provider
     */
    private fallbackAI: 'gpt-4' | 'claude' | 'auto';

    /**
     * Configuration
     */
    private config: vscode.WorkspaceConfiguration;

    /**
     * Cache for embeddings
     */
    private embeddingCache: Map<string, number[]> = new Map();

    constructor() {
        this.config = vscode.workspace.getConfiguration('kiAutoAgent.ai.intentClassification');
        this.primaryAI = this.config.get('provider', 'gpt-4');
        this.fallbackAI = this.primaryAI === 'gpt-4' ? 'claude' : 'gpt-4';
    }

    /**
     * Classify text using AI
     */
    public async classify(
        prompt: string,
        options: ClassificationOptions = {}
    ): Promise<any> {
        const provider = options.provider || this.primaryAI;
        const timeout = options.timeout || 10000;

        try {
            // Create promise with timeout
            const classificationPromise = this.performClassification(prompt, provider);
            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Classification timeout')), timeout)
            );

            // Race between classification and timeout
            const result = await Promise.race([classificationPromise, timeoutPromise]);

            // If consensus is requested, get multiple opinions
            if (options.useConsensus) {
                return await this.getConsensusClassification(prompt, ['gpt-4', 'claude']);
            }

            return result;
        } catch (error) {
            console.error('Classification failed with primary provider:', error);

            // Try fallback provider
            if (provider !== this.fallbackAI) {
                console.log('Attempting fallback provider:', this.fallbackAI);
                return await this.performClassification(prompt, this.fallbackAI);
            }

            throw error;
        }
    }

    /**
     * Perform classification with specific provider
     */
    private async performClassification(
        prompt: string,
        provider: 'gpt-4' | 'claude' | 'auto'
    ): Promise<any> {
        if (provider === 'auto') {
            // Choose provider based on availability and performance
            provider = await this.selectBestProvider();
        }

        switch (provider) {
            case 'gpt-4':
                return await this.classifyWithGPT4(prompt);
            case 'claude':
                return await this.classifyWithClaude(prompt);
            default:
                throw new Error(`Unknown provider: ${provider}`);
        }
    }

    /**
     * Classify using GPT-4
     */
    private async classifyWithGPT4(prompt: string): Promise<any> {
        try {
            // Get OpenAI service (assuming it exists in the codebase)
            const openAIKey = this.config.get('openaiApiKey', '');
            if (!openAIKey) {
                throw new Error('OpenAI API key not configured');
            }

            // Simulate API call (replace with actual implementation)
            const response = await this.callOpenAI(prompt, openAIKey);
            return response;
        } catch (error) {
            console.error('GPT-4 classification failed:', error);
            throw error;
        }
    }

    /**
     * Classify using Claude
     */
    private async classifyWithClaude(prompt: string): Promise<any> {
        try {
            // Get Claude service (assuming it exists in the codebase)
            const anthropicKey = this.config.get('anthropicApiKey', '');
            if (!anthropicKey) {
                throw new Error('Anthropic API key not configured');
            }

            // Simulate API call (replace with actual implementation)
            const response = await this.callClaude(prompt, anthropicKey);
            return response;
        } catch (error) {
            console.error('Claude classification failed:', error);
            throw error;
        }
    }

    /**
     * Get text embedding for semantic similarity
     */
    public async getEmbedding(text: string): Promise<number[]> {
        // Check cache
        const cached = this.embeddingCache.get(text);
        if (cached) {
            return cached;
        }

        try {
            // Use OpenAI embeddings API
            const embedding = await this.fetchEmbedding(text);

            // Cache the result
            this.embeddingCache.set(text, embedding);

            // Limit cache size
            if (this.embeddingCache.size > 1000) {
                const firstKey = this.embeddingCache.keys().next().value;
                if (firstKey !== undefined) {
                    this.embeddingCache.delete(firstKey);
                }
            }

            return embedding;
        } catch (error) {
            console.error('Failed to get embedding:', error);
            // Return random embedding as fallback
            return Array(1536).fill(0).map(() => Math.random());
        }
    }

    /**
     * Calculate semantic similarity between two texts
     */
    public async calculateSemanticSimilarity(text1: string, text2: string): Promise<number> {
        try {
            const embedding1 = await this.getEmbedding(text1);
            const embedding2 = await this.getEmbedding(text2);

            // Calculate cosine similarity
            return this.cosineSimilarity(embedding1, embedding2);
        } catch (error) {
            console.error('Failed to calculate similarity:', error);
            return 0;
        }
    }

    /**
     * Detect sarcasm in text
     */
    public async detectSarcasm(text: string): Promise<{ isSarcastic: boolean; confidence: number }> {
        const prompt = `
Analyze the following text for sarcasm. Consider tone, context, and linguistic markers.

Text: "${text}"

Respond with JSON:
{
  "isSarcastic": true/false,
  "confidence": 0.0-1.0,
  "indicators": ["list", "of", "sarcasm", "indicators"]
}
`;

        try {
            const response = await this.classify(prompt, { timeout: 5000 });
            return typeof response === 'string' ? JSON.parse(response) : response;
        } catch (error) {
            console.error('Sarcasm detection failed:', error);
            return { isSarcastic: false, confidence: 0.5 };
        }
    }

    /**
     * Detect urgency in text
     */
    public async detectUrgency(text: string): Promise<'high' | 'medium' | 'low'> {
        const prompt = `
Analyze the urgency level of this request:

Text: "${text}"

Consider:
- Time-related keywords (now, immediately, asap, when you can)
- Emotional tone
- Imperative language

Respond with: "high", "medium", or "low"
`;

        try {
            const response = await this.classify(prompt, { timeout: 3000 });
            const urgency = response.trim().toLowerCase();
            return urgency as 'high' | 'medium' | 'low';
        } catch (error) {
            console.error('Urgency detection failed:', error);
            return 'medium';
        }
    }

    /**
     * Detect language of text
     */
    public async detectLanguage(text: string): Promise<string> {
        const prompt = `
Detect the language of this text:

"${text}"

Respond with ISO 639-1 code (e.g., "en" for English, "de" for German, "fr" for French)
`;

        try {
            const response = await this.classify(prompt, { timeout: 3000 });
            return response.trim().toLowerCase();
        } catch (error) {
            console.error('Language detection failed:', error);
            return 'unknown';
        }
    }

    /**
     * Get consensus classification from multiple models
     */
    public async getConsensusClassification(
        text: string,
        models: string[]
    ): Promise<any> {
        try {
            // Get classifications from all models
            const classifications = await Promise.all(
                models.map(model => this.performClassification(text, model as any))
            );

            // Merge and analyze results
            return this.mergeClassifications(classifications);
        } catch (error) {
            console.error('Consensus classification failed:', error);
            // Return first successful classification
            for (const model of models) {
                try {
                    return await this.performClassification(text, model as any);
                } catch (e) {
                    continue;
                }
            }
            throw new Error('All models failed');
        }
    }

    /**
     * Select best available provider
     */
    private async selectBestProvider(): Promise<'gpt-4' | 'claude'> {
        // Check which providers are configured
        const openAIKey = this.config.get('openaiApiKey', '');
        const anthropicKey = this.config.get('anthropicApiKey', '');

        if (openAIKey && !anthropicKey) {
            return 'gpt-4';
        } else if (anthropicKey && !openAIKey) {
            return 'claude';
        } else if (openAIKey && anthropicKey) {
            // Both available, choose based on recent performance
            // For now, default to GPT-4
            return 'gpt-4';
        } else {
            throw new Error('No AI providers configured');
        }
    }

    /**
     * Merge multiple classifications into consensus
     */
    private mergeClassifications(classifications: any[]): any {
        if (classifications.length === 0) {
            throw new Error('No classifications to merge');
        }

        if (classifications.length === 1) {
            return classifications[0];
        }

        // Parse all classifications
        const parsed = classifications.map(c => {
            try {
                return typeof c === 'string' ? JSON.parse(c) : c;
            } catch {
                return null;
            }
        }).filter(c => c !== null);

        if (parsed.length === 0) {
            return classifications[0];
        }

        // Count intent votes
        const intentVotes: Record<string, number> = {};
        let totalConfidence = 0;

        for (const classification of parsed) {
            intentVotes[classification.intent] = (intentVotes[classification.intent] || 0) + 1;
            totalConfidence += classification.confidence || 0;
        }

        // Find most common intent
        const mostCommonIntent = Object.entries(intentVotes)
            .sort(([, a], [, b]) => b - a)[0][0];

        // Calculate average confidence
        const avgConfidence = totalConfidence / parsed.length;

        // Combine reasoning
        const combinedReasoning = parsed
            .map(c => c.reasoning)
            .filter(r => r)
            .join('; ');

        return {
            intent: mostCommonIntent,
            confidence: avgConfidence,
            reasoning: `Consensus from ${parsed.length} models: ${combinedReasoning}`,
            suggestedAction: parsed[0].suggestedAction,
            consensus: true,
            modelAgreement: intentVotes[mostCommonIntent] / parsed.length
        };
    }

    /**
     * Calculate cosine similarity between two vectors
     */
    private cosineSimilarity(vec1: number[], vec2: number[]): number {
        if (vec1.length !== vec2.length) {
            throw new Error('Vectors must have same length');
        }

        let dotProduct = 0;
        let norm1 = 0;
        let norm2 = 0;

        for (let i = 0; i < vec1.length; i++) {
            dotProduct += vec1[i] * vec2[i];
            norm1 += vec1[i] * vec1[i];
            norm2 += vec2[i] * vec2[i];
        }

        norm1 = Math.sqrt(norm1);
        norm2 = Math.sqrt(norm2);

        if (norm1 === 0 || norm2 === 0) {
            return 0;
        }

        return dotProduct / (norm1 * norm2);
    }

    /**
     * Mock OpenAI API call (to be replaced with actual implementation)
     */
    private async callOpenAI(prompt: string, apiKey: string): Promise<any> {
        // This would be replaced with actual OpenAI API call
        // For now, return a mock response
        return JSON.stringify({
            intent: 'uncertain',
            confidence: 0.5,
            reasoning: 'Mock OpenAI response',
            suggestedAction: 'Ask for clarification'
        });
    }

    /**
     * Mock Claude API call (to be replaced with actual implementation)
     */
    private async callClaude(prompt: string, apiKey: string): Promise<any> {
        // This would be replaced with actual Claude API call
        // For now, return a mock response
        return JSON.stringify({
            intent: 'uncertain',
            confidence: 0.5,
            reasoning: 'Mock Claude response',
            suggestedAction: 'Ask for clarification'
        });
    }

    /**
     * Mock embedding fetch (to be replaced with actual implementation)
     */
    private async fetchEmbedding(text: string): Promise<number[]> {
        // This would be replaced with actual embedding API call
        // For now, return a mock embedding
        return Array(1536).fill(0).map(() => Math.random() - 0.5);
    }

    /**
     * Clear all caches
     */
    public clearCache(): void {
        this.embeddingCache.clear();
    }
}