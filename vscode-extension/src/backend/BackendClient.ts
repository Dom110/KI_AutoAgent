/**
 * BackendClient - WebSocket client for Python backend communication
 * Handles all communication between VS Code extension and Python backend
 */

import * as vscode from 'vscode';
import WebSocket from 'ws';
import { EventEmitter } from 'events';

export interface BackendMessage {
    type: 'chat' | 'command' | 'workflow' | 'agent_response' | 'agent_thinking' | 'agent_progress' | 'error' | 'connection' | 'complete' | 'progress' | 'stream_chunk';
    content?: string;
    agent?: string;
    metadata?: any;
    timestamp?: string;
    done?: boolean;  // For stream_chunk messages
}

export interface ChatRequest {
    prompt: string;
    agent?: string;
    context?: any;
    command?: string;
    thinkingMode?: boolean;
    mode?: 'single' | 'auto' | 'workflow';
}

export class BackendClient extends EventEmitter {
    private static instance: BackendClient;
    private ws: WebSocket | null = null;
    private reconnectTimer: NodeJS.Timeout | null = null;
    private reconnectAttempts: number = 0;
    private maxReconnectAttempts: number = 5;
    private isConnected: boolean = false;
    private messageQueue: BackendMessage[] = [];
    private outputChannel: vscode.OutputChannel;

    private constructor(private wsUrl: string) {
        super();
        this.outputChannel = vscode.window.createOutputChannel('Backend Client');
    }

    public static getInstance(wsUrl?: string): BackendClient {
        // Get URL from configuration if not provided
        if (!wsUrl) {
            const config = vscode.workspace.getConfiguration('kiAutoAgent');
            const backendUrl = config.get<string>('backend.url', 'localhost:8000');
            const wsProtocol = backendUrl.startsWith('https') ? 'wss' : 'ws';
            const cleanUrl = backendUrl.replace(/^https?:\/\//, '');
            wsUrl = `${wsProtocol}://${cleanUrl}/ws/chat`;
        }

        if (!BackendClient.instance) {
            BackendClient.instance = new BackendClient(wsUrl);
        }
        return BackendClient.instance;
    }

    /**
     * Connect to the backend WebSocket
     */
    public async connect(): Promise<void> {
        return new Promise((resolve, reject) => {
            try {
                this.outputChannel.appendLine(`🔌 Connecting to backend at ${this.wsUrl}...`);

                this.ws = new WebSocket(this.wsUrl);

                this.ws.on('open', () => {
                    this.isConnected = true;
                    this.reconnectAttempts = 0;
                    this.outputChannel.appendLine('✅ Connected to backend!');
                    this.emit('connected');

                    // Process queued messages
                    this.processMessageQueue();

                    resolve();
                });

                this.ws.on('message', (data: WebSocket.Data) => {
                    try {
                        const message = JSON.parse(data.toString()) as BackendMessage;
                        this.handleMessage(message);
                    } catch (error) {
                        this.outputChannel.appendLine(`❌ Failed to parse message: ${error}`);
                    }
                });

                this.ws.on('error', (error) => {
                    this.outputChannel.appendLine(`❌ WebSocket error: ${error.message}`);
                    this.emit('error', error);

                    if (!this.isConnected) {
                        reject(error);
                    }
                });

                this.ws.on('close', () => {
                    this.isConnected = false;
                    this.outputChannel.appendLine('❌ Disconnected from backend');
                    this.emit('disconnected');

                    // Attempt reconnection
                    this.scheduleReconnect();
                });

            } catch (error) {
                this.outputChannel.appendLine(`❌ Connection failed: ${error}`);
                reject(error);
            }
        });
    }

    /**
     * Send a chat message to the backend
     */
    public async sendChatMessage(request: ChatRequest): Promise<void> {
        const message: BackendMessage = {
            type: 'chat',
            content: request.prompt,
            agent: request.agent || 'orchestrator',
            metadata: {
                context: request.context,
                command: request.command,
                thinkingMode: request.thinkingMode,
                mode: request.mode
            }
        };

        return this.sendMessage(message);
    }

    /**
     * Send a command to the backend
     */
    public async sendCommand(command: string, args: any = {}): Promise<void> {
        const message: BackendMessage = {
            type: 'command',
            content: command,
            metadata: args
        };

        return this.sendMessage(message);
    }

    /**
     * Send a workflow request to the backend
     */
    public async sendWorkflow(workflow: any): Promise<void> {
        const message: BackendMessage = {
            type: 'workflow',
            metadata: { workflow }
        };

        return this.sendMessage(message);
    }

    /**
     * Send a message to the backend
     */
    private async sendMessage(message: BackendMessage): Promise<void> {
        if (!this.isConnected || !this.ws) {
            this.outputChannel.appendLine('⚠️ Not connected, queuing message');
            this.messageQueue.push(message);

            // Try to reconnect
            if (!this.reconnectTimer) {
                await this.connect();
            }
            return;
        }

        try {
            this.ws.send(JSON.stringify(message));
            this.outputChannel.appendLine(`📤 Sent: ${message.type}`);
        } catch (error) {
            this.outputChannel.appendLine(`❌ Failed to send message: ${error}`);
            this.messageQueue.push(message);
            throw error;
        }
    }

    /**
     * Handle incoming messages from the backend
     */
    private handleMessage(message: BackendMessage): void {
        this.outputChannel.appendLine(`📨 Received: ${message.type}`);

        switch (message.type) {
            case 'connection':
                this.emit('welcome', message);
                break;

            case 'agent_thinking':
                this.emit('thinking', message);
                break;

            case 'agent_progress':
                this.emit('progress', message);
                break;

            case 'agent_response':
                this.emit('response', message);
                break;

            case 'stream_chunk':
                // Handle streaming responses
                if (message.done) {
                    // Final chunk - emit as complete response
                    this.emit('response', {
                        ...message,
                        type: 'agent_response'
                    });
                } else {
                    // Intermediate chunk - emit as progress
                    this.emit('progress', message);
                }
                break;

            case 'error':
                this.emit('error', message);
                break;

            case 'complete':
                this.emit('complete', message);
                break;

            default:
                this.emit('message', message);
        }
    }

    /**
     * Process queued messages after reconnection
     */
    private processMessageQueue(): void {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            if (message) {
                this.sendMessage(message).catch(error => {
                    this.outputChannel.appendLine(`❌ Failed to send queued message: ${error}`);
                });
            }
        }
    }

    /**
     * Schedule reconnection attempt
     */
    private scheduleReconnect(): void {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            this.outputChannel.appendLine('❌ Max reconnection attempts reached');
            vscode.window.showErrorMessage(
                'Failed to connect to Python backend. Please start it manually.'
            );
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);

        this.outputChannel.appendLine(
            `⏳ Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
        );

        this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connect().catch(error => {
                this.outputChannel.appendLine(`❌ Reconnection failed: ${error}`);
            });
        }, delay);
    }

    /**
     * Disconnect from the backend
     */
    public disconnect(): void {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        this.isConnected = false;
    }

    /**
     * Check if connected
     */
    public isConnectedToBackend(): boolean {
        return this.isConnected;
    }

    /**
     * Dispose and cleanup
     */
    public dispose(): void {
        this.disconnect();
        this.outputChannel.dispose();
        this.removeAllListeners();
    }
}