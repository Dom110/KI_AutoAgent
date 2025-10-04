/**
 * BackendClient - WebSocket client for Python backend communication
 * Handles all communication between VS Code extension and Python backend
 */

import * as vscode from 'vscode';
import WebSocket from 'ws';
import { EventEmitter } from 'events';

export interface BackendMessage {
    type: 'chat' | 'command' | 'workflow' | 'agent_response' | 'agent_thinking' | 'agent_progress' | 'error' | 'connection' | 'complete' | 'progress' | 'stream_chunk' | 'pause' | 'resume' | 'stopAndRollback' | 'pauseActivated' | 'resumed' | 'stoppedAndRolledBack' | 'clarificationNeeded' | 'clarificationResponse' | 'session_restore' | 'connected' | 'initialized' | 'init' | 'response' | 'step_completed';
    content?: string;
    agent?: string;
    metadata?: any;
    timestamp?: string;
    done?: boolean;  // For stream_chunk messages
    message?: string;  // For error and progress messages
    status?: string;  // For response status
    error?: string;  // For error messages
    details?: any;  // For additional error details
    additionalInstructions?: string;  // For resume with instructions
    data?: any;  // For pause/resume/rollback data
    response?: any;  // For clarification response
    task?: any;  // For session_restore - original task info
    progress?: any[];  // For session_restore - progress messages
    result?: any;  // For session_restore - completed result
    session_id?: string;  // For initialized message
    client_id?: string;  // For initialized message
    workspace_path?: string;  // For initialized message
    requires_init?: boolean;  // For connected message
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
    private debugChannel: vscode.OutputChannel | null = null;

    private constructor(private wsUrl: string) {
        super();
        this.outputChannel = vscode.window.createOutputChannel('Backend Client');
    }

    /**
     * Get the backend URL (without ws:// prefix)
     */
    public getBackendUrl(): string {
        // Extract host:port from ws://host:port/ws/chat
        const match = this.wsUrl.match(/ws:\/\/([^\/]+)/);
        if (match) {
            return match[1];
        }
        // Fallback to default (v5.0.0 LangGraph port)
        return 'localhost:8001';
    }

    /**
     * Set a debug channel to forward logs to
     */
    public setDebugChannel(channel: vscode.OutputChannel): void {
        this.debugChannel = channel;
        this.log('🔗 Debug channel connected to BackendClient');
    }

    /**
     * Log to both output channel and optional debug channel
     */
    private log(message: string): void {
        this.outputChannel.appendLine(message);
        if (this.debugChannel) {
            this.debugChannel.appendLine(`[BackendClient] ${message}`);
        }
    }

    public static getInstance(wsUrl?: string): BackendClient {
        // Get URL from configuration if not provided
        if (!wsUrl) {
            const config = vscode.workspace.getConfiguration('kiAutoAgent');
            const backendUrl = config.get<string>('backend.url', 'localhost:8001');  // v5.0.0 LangGraph port
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
     * v5.8.1: Send init message with workspace_path after connection
     */
    public async connect(): Promise<void> {
        return new Promise((resolve, reject) => {
            try {
                // Get workspace path for init message
                const workspaceFolders = vscode.workspace.workspaceFolders;
                const workspacePath = workspaceFolders && workspaceFolders.length > 0
                    ? workspaceFolders[0].uri.fsPath
                    : null;

                if (!workspacePath) {
                    const error = new Error('No workspace folder open. Please open a folder or workspace.');
                    this.log(`❌ ${error.message}`);
                    reject(error);
                    return;
                }

                this.log(`🔌 Connecting to backend at ${this.wsUrl}...`);
                this.log(`📂 Workspace: ${workspacePath}`);

                this.ws = new WebSocket(this.wsUrl);

                // Track initialization state
                let isInitialized = false;

                this.ws.on('open', () => {
                    this.log('✅ WebSocket connected, waiting for server handshake...');
                });

                this.ws.on('message', (data: WebSocket.Data) => {
                    try {
                        const message = JSON.parse(data.toString()) as BackendMessage;

                        // v5.8.1: Handle handshake sequence
                        if (message.type === 'connected' && !isInitialized) {
                            this.log('📩 Received server welcome, sending init message...');

                            // Send init message with workspace_path
                            const initMessage = {
                                type: 'init',
                                workspace_path: workspacePath
                            };

                            this.ws?.send(JSON.stringify(initMessage));
                            this.log(`📤 Sent init message with workspace: ${workspacePath}`);
                        }
                        else if (message.type === 'initialized') {
                            // Initialization complete
                            isInitialized = true;
                            this.isConnected = true;
                            this.reconnectAttempts = 0;

                            this.log(`✅ Workspace initialized: ${message.workspace_path}`);
                            this.log(`🔑 Session ID: ${message.session_id}`);
                            this.emit('connected');

                            // Process queued messages
                            this.processMessageQueue();

                            resolve();
                        }
                        else if (message.type === 'error') {
                            this.log(`❌ Server error: ${message.message || message.error}`);
                            if (!isInitialized) {
                                reject(new Error(message.message || 'Initialization failed'));
                            }
                        }
                        else {
                            // Normal message handling
                            this.handleMessage(message);
                        }
                    } catch (error) {
                        this.log(`❌ Failed to parse message: ${error}`);
                    }
                });

                this.ws.on('error', (error) => {
                    this.log(`❌ WebSocket error: ${error.message}`);
                    this.emit('error', error);

                    if (!this.isConnected) {
                        reject(error);
                    }
                });

                this.ws.on('close', () => {
                    this.isConnected = false;
                    this.log('❌ Disconnected from backend');
                    this.emit('disconnected');

                    // Attempt reconnection
                    this.scheduleReconnect();
                });

            } catch (error) {
                this.log(`❌ Connection failed: ${error}`);
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
    public async sendMessage(message: BackendMessage): Promise<void> {
        if (!this.isConnected || !this.ws) {
            this.log('⚠️ Not connected, queuing message');
            this.messageQueue.push(message);

            // Try to reconnect
            if (!this.reconnectTimer) {
                await this.connect();
            }
            return;
        }

        try {
            this.ws.send(JSON.stringify(message));
            this.log(`📤 Sent: ${message.type}`);
        } catch (error) {
            this.log(`❌ Failed to send message: ${error}`);
            this.messageQueue.push(message);
            throw error;
        }
    }

    /**
     * Handle incoming messages from the backend
     */
    private handleMessage(message: BackendMessage): void {
        this.log(`📨 Received: ${message.type}`);

        switch (message.type) {
            case 'connection':
            case 'connected':  // LangGraph v5.0.0 sends 'connected'
                this.emit('welcome', message);
                break;

            case 'agent_thinking':
                this.emit('thinking', message);
                break;

            case 'response':  // LangGraph v5.0.0 response
                this.log(`✅ LangGraph Response: ${message.agent || 'orchestrator'} - Content: ${message.content ? 'Present' : 'Missing'}`);
                // Log the actual content for debugging
                if (message.content) {
                    this.log(`📝 Content preview: ${message.content.substring(0, 100)}...`);
                }
                this.emit('response', message);
                break;

            case 'step_completed':  // LangGraph v5.0.0 intermediate step
                this.log(`📊 Step Completed: ${message.agent || 'orchestrator'}`);
                this.emit('step_completed', message);
                break;

            case 'agent_progress':
                // Validate content before emitting
                const progressContent = message.message || message.content || '';
                if (!progressContent || progressContent === 'undefined') {
                    this.log(`⚠️ Skipping agent_progress with undefined content from ${message.agent}`);
                    break;
                }
                this.log(`📊 Agent Progress: ${message.agent} - ${progressContent}`);
                this.emit('progress', message);
                break;

            case 'agent_response':
                this.log(`✅ Agent Response: ${message.agent} - Status: ${message.status}`);
                if (message.status === 'error') {
                    this.log(`❌ Error Details: ${message.content}`);
                }
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
                    // Intermediate chunk - validate content before emitting as progress
                    const chunkContent = message.content || message.message || '';
                    if (!chunkContent || chunkContent === 'undefined') {
                        this.log(`⚠️ Skipping stream_chunk with undefined content from ${message.agent}`);
                        break;
                    }
                    this.emit('progress', message);
                }
                break;

            case 'error':
                this.log(`❌ ERROR: ${message.message || message.error || JSON.stringify(message)}`);
                if (message.agent) {
                    this.log(`   Agent: ${message.agent}`);
                }
                if (message.details) {
                    this.log(`   Details: ${JSON.stringify(message.details)}`);
                }
                this.emit('error', message);
                break;

            case 'complete':
                this.emit('complete', message);
                break;

            case 'session_restore':
                this.log(`🔄 Session restore: ${message.status} - ${message.message}`);
                this.emit('session_restore', message);
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
                    this.log(`❌ Failed to send queued message: ${error}`);
                });
            }
        }
    }

    /**
     * Schedule reconnection attempt
     */
    private scheduleReconnect(): void {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            this.log('❌ Max reconnection attempts reached');
            vscode.window.showErrorMessage(
                'Failed to connect to Python backend. Please start it manually.'
            );
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);

        this.log(
            `⏳ Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
        );

        this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connect().catch(error => {
                this.log(`❌ Reconnection failed: ${error}`);
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