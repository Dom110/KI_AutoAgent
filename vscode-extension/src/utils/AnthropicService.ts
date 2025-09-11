/**
 * Anthropic Service for Claude model interactions
 */
import * as vscode from 'vscode';

interface ChatMessage {
    role: 'system' | 'user' | 'assistant';
    content: string;
}

interface ChatResponse {
    content: Array<{
        text: string;
        type: string;
    }>;
}

export class AnthropicService {
    private apiKey: string;
    private baseURL: string;

    constructor() {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        this.apiKey = config.get<string>('anthropic.apiKey', '');
        this.baseURL = 'https://api.anthropic.com/v1';
    }

    async chat(
        messages: ChatMessage[],
        model: string = 'claude-3-5-sonnet-20241022',
        maxTokens: number = 4000,
        temperature: number = 0.7
    ): Promise<string> {
        
        if (!this.apiKey) {
            throw new Error('Anthropic API key not configured');
        }

        // Anthropic expects system message separate from messages
        const systemMessage = messages.find(m => m.role === 'system');
        const conversationMessages = messages.filter(m => m.role !== 'system');

        const requestBody = {
            model,
            max_tokens: maxTokens,
            temperature,
            system: systemMessage?.content || '',
            messages: conversationMessages.map(msg => ({
                role: msg.role,
                content: msg.content
            }))
        };

        try {
            const response = await fetch(`${this.baseURL}/messages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': this.apiKey,
                    'anthropic-version': '2023-06-01'
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: { message: response.statusText } }));
                throw new Error(`Anthropic API error: ${(errorData as any).error?.message || response.statusText}`);
            }

            const data= await response.json() as ChatResponse;
            
            if (!data.content || data.content.length === 0) {
                throw new Error('No response from Anthropic API');
            }

            // Extract text from content blocks
            return data.content
                .filter(block => block.type === 'text')
                .map(block => block.text)
                .join('');

        } catch (error) {
            if (error instanceof Error) {
                throw error;
            }
            throw new Error(`Anthropic API request failed: ${error}`);
        }
    }

    async streamChat(
        messages: ChatMessage[],
        onChunk: (chunk: string) => void,
        model: string = 'claude-3-5-sonnet-20241022',
        maxTokens: number = 4000,
        temperature: number = 0.7
    ): Promise<void> {
        
        if (!this.apiKey) {
            throw new Error('Anthropic API key not configured');
        }

        const systemMessage = messages.find(m => m.role === 'system');
        const conversationMessages = messages.filter(m => m.role !== 'system');

        const requestBody = {
            model,
            max_tokens: maxTokens,
            temperature,
            system: systemMessage?.content || '',
            messages: conversationMessages.map(msg => ({
                role: msg.role,
                content: msg.content
            })),
            stream: true
        };

        try {
            const response = await fetch(`${this.baseURL}/messages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': this.apiKey,
                    'anthropic-version': '2023-06-01'
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                throw new Error(`Anthropic API error: ${response.statusText}`);
            }

            const reader = response.body?.getReader();
            if (!reader) {
                throw new Error('Failed to get response stream');
            }

            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                
                if (done) {
                    break;
                }

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n').filter(line => line.trim() !== '');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.substring(6);
                        
                        if (data === '[DONE]') {
                            return;
                        }

                        try {
                            const parsed = JSON.parse(data);
                            
                            if (parsed.type === 'content_block_delta') {
                                const text = parsed.delta?.text;
                                if (text) {
                                    onChunk(text);
                                }
                            }
                        } catch (error) {
                            // Ignore parsing errors for incomplete chunks
                        }
                    }
                }
            }

        } catch (error) {
            throw new Error(`Anthropic streaming failed: ${error}`);
        }
    }

    validateApiKey(): boolean {
        return !!this.apiKey && this.apiKey.startsWith('sk-ant-');
    }

    async testConnection(): Promise<boolean> {
        try {
            await this.chat([
                { role: 'user', content: 'Test connection' }
            ], 'claude-3-5-sonnet-20241022', 10);
            return true;
        } catch (error) {
            return false;
        }
    }
}