/**
 * Claude Web Service - Integration with Claude Pro Web Sessions
 * Uses the existing claude_web_proxy system instead of API keys
 */
import * as vscode from 'vscode';

interface ClaudeWebResponse {
    response: string;
    conversation_id?: string;
    success: boolean;
    error?: string;
}

interface ChatMessage {
    role: 'system' | 'user' | 'assistant';
    content: string;
}

export class ClaudeWebService {
    private baseUrl: string;
    private conversationId?: string;
    private planType: string;
    
    constructor() {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        this.baseUrl = config.get<string>('claudeWeb.serverUrl', 'http://localhost:8000');
        this.planType = config.get<string>('claudeWeb.planType', 'pro');
    }

    async chat(
        messages: ChatMessage[],
        temperature: number = 0.7
    ): Promise<string> {
        
        // Check if Claude Web Proxy is available
        const isAvailable = await this.checkServerAvailable();
        if (!isAvailable) {
            throw new Error('Claude Web Proxy server not available. Please start the server first.');
        }

        try {
            // Convert messages to conversation format
            const systemMessage = messages.find(m => m.role === 'system');
            const userMessages = messages.filter(m => m.role === 'user');
            const lastUserMessage = userMessages[userMessages.length - 1];
            
            if (!lastUserMessage) {
                throw new Error('No user message provided');
            }

            // Combine system prompt with user message if needed
            let prompt = lastUserMessage.content;
            if (systemMessage) {
                prompt = `${systemMessage.content}\n\nUser: ${prompt}`;
            }

            const response = await fetch(`${this.baseUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: prompt,
                    conversation_id: this.conversationId,
                    temperature: temperature,
                    plan_type: this.planType
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Unknown error' })) as any;
                throw new Error(`Claude Web API error: ${errorData.error || response.statusText}`);
            }

            const data = await response.json() as ClaudeWebResponse;
            
            if (!data.success) {
                throw new Error(`Claude Web error: ${data.error || 'Unknown error'}`);
            }

            // Store conversation ID for context
            if (data.conversation_id) {
                this.conversationId = data.conversation_id;
            }

            return data.response;

        } catch (error) {
            if (error instanceof Error) {
                throw error;
            }
            throw new Error(`Claude Web request failed: ${error}`);
        }
    }

    async streamChat(
        messages: ChatMessage[],
        onChunk: (chunk: string) => void,
        temperature: number = 0.7
    ): Promise<void> {
        
        const isAvailable = await this.checkServerAvailable();
        if (!isAvailable) {
            throw new Error('Claude Web Proxy server not available');
        }

        try {
            const systemMessage = messages.find(m => m.role === 'system');
            const userMessages = messages.filter(m => m.role === 'user');
            const lastUserMessage = userMessages[userMessages.length - 1];
            
            if (!lastUserMessage) {
                throw new Error('No user message provided');
            }

            let prompt = lastUserMessage.content;
            if (systemMessage) {
                prompt = `${systemMessage.content}\n\nUser: ${prompt}`;
            }

            const response = await fetch(`${this.baseUrl}/chat/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: prompt,
                    conversation_id: this.conversationId,
                    temperature: temperature,
                    plan_type: this.planType
                })
            });

            if (!response.ok) {
                throw new Error(`Claude Web streaming error: ${response.statusText}`);
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
                            if (parsed.chunk) {
                                onChunk(parsed.chunk);
                            }
                            if (parsed.conversation_id) {
                                this.conversationId = parsed.conversation_id;
                            }
                        } catch (error) {
                            // Ignore parsing errors for incomplete chunks
                        }
                    }
                }
            }

        } catch (error) {
            throw new Error(`Claude Web streaming failed: ${error}`);
        }
    }

    async checkServerAvailable(): Promise<boolean> {
        try {
            const response = await fetch(`${this.baseUrl}/health`, {
                method: 'GET',
                timeout: 5000
            } as any);
            return response.ok;
        } catch (error) {
            return false;
        }
    }

    async getServerStatus(): Promise<{
        available: boolean;
        url: string;
        version?: string;
        error?: string;
    }> {
        try {
            const response = await fetch(`${this.baseUrl}/status`, {
                method: 'GET',
                timeout: 5000
            } as any);
            
            if (response.ok) {
                const data = await response.json() as any;
                return {
                    available: true,
                    url: this.baseUrl,
                    version: data.version || 'unknown'
                };
            } else {
                return {
                    available: false,
                    url: this.baseUrl,
                    error: `Server returned ${response.status}`
                };
            }
        } catch (error) {
            return {
                available: false,
                url: this.baseUrl,
                error: error instanceof Error ? error.message : 'Connection failed'
            };
        }
    }

    async resetConversation(): Promise<void> {
        this.conversationId = undefined;
    }

    async startNewConversation(): Promise<string | undefined> {
        try {
            const response = await fetch(`${this.baseUrl}/conversation/new`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json() as any;
                this.conversationId = data.conversation_id;
                return this.conversationId;
            }
        } catch (error) {
            console.error('Failed to start new conversation:', error);
        }
        return undefined;
    }

    getConversationId(): string | undefined {
        return this.conversationId;
    }

    validateWebAccess(): boolean {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        const webAccessEnabled = config.get<boolean>('claudeWeb.enabled', true);
        const serverUrl = config.get<string>('claudeWeb.serverUrl', 'http://localhost:8000');
        
        return webAccessEnabled && !!serverUrl;
    }

    async testConnection(): Promise<boolean> {
        try {
            const status = await this.getServerStatus();
            return status.available;
        } catch (error) {
            return false;
        }
    }
}