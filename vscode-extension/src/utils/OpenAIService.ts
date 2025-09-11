/**
 * OpenAI Service for GPT model interactions
 */
import * as vscode from 'vscode';

interface ChatMessage {
    role: 'system' | 'user' | 'assistant';
    content: string;
}

interface ChatResponse {
    choices: Array<{
        message: {
            content: string;
        };
    }>;
}

export class OpenAIService {
    private apiKey: string;
    private baseURL: string;

    constructor() {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        this.apiKey = config.get<string>('openai.apiKey', '');
        this.baseURL = 'https://api.openai.com/v1';
    }

    async chat(
        messages: ChatMessage[],
        model: string = 'gpt-4o',
        maxTokens: number = 4000,
        temperature: number = 0.7
    ): Promise<string> {
        
        if (!this.apiKey) {
            throw new Error('OpenAI API key not configured');
        }

        const requestBody = {
            model,
            messages,
            max_tokens: maxTokens,
            temperature,
            stream: false
        };

        try {
            const response = await fetch(`${this.baseURL}/chat/completions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.apiKey}`
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: { message: response.statusText } }));
                throw new Error(`OpenAI API error: ${(errorData as any).error?.message || response.statusText}`);
            }

            const data= await response.json() as ChatResponse;
            
            if (!data.choices || data.choices.length === 0) {
                throw new Error('No response from OpenAI API');
            }

            return data.choices[0].message.content;

        } catch (error) {
            if (error instanceof Error) {
                throw error;
            }
            throw new Error(`OpenAI API request failed: ${error}`);
        }
    }

    async streamChat(
        messages: ChatMessage[],
        onChunk: (chunk: string) => void,
        model: string = 'gpt-4o',
        maxTokens: number = 4000,
        temperature: number = 0.7
    ): Promise<void> {
        
        if (!this.apiKey) {
            throw new Error('OpenAI API key not configured');
        }

        const requestBody = {
            model,
            messages,
            max_tokens: maxTokens,
            temperature,
            stream: true
        };

        try {
            const response = await fetch(`${this.baseURL}/chat/completions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.apiKey}`
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                throw new Error(`OpenAI API error: ${response.statusText}`);
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
                            const content = parsed.choices?.[0]?.delta?.content;
                            
                            if (content) {
                                onChunk(content);
                            }
                        } catch (error) {
                            // Ignore parsing errors for incomplete chunks
                        }
                    }
                }
            }

        } catch (error) {
            throw new Error(`OpenAI streaming failed: ${error}`);
        }
    }

    validateApiKey(): boolean {
        return !!this.apiKey && this.apiKey.startsWith('sk-');
    }

    async testConnection(): Promise<boolean> {
        try {
            await this.chat([
                { role: 'user', content: 'Test connection' }
            ], 'gpt-4o-mini', 10);
            return true;
        } catch (error) {
            return false;
        }
    }
}