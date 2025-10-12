/**
 * BackendClient - WebSocket client for Python backend communication
 * Handles all communication between VS Code extension and Python backend
 */

import * as vscode from 'vscode';
import WebSocket from 'ws';
import { EventEmitter } from 'events';

export interface BackendMessage {
    type: 'chat' | 'command' | 'workflow' | 'agent_response' | 'agent_thinking' | 'agent_progress' | 'agent_complete' | 'agent_tool_start' | 'agent_tool_complete' | 'error' | 'connection' | 'complete' | 'progress' | 'stream_chunk' | 'pause' | 'resume' | 'stopAndRollback' | 'pauseActivated' | 'resumed' | 'stoppedAndRolledBack' | 'clarificationNeeded' | 'clarificationResponse' | 'session_restore' | 'connected' | 'initialized' | 'init' | 'response' | 'step_completed' | 'architecture_proposal' | 'architecture_proposal_revised' | 'architectureApprovalProcessed' | 'status' | 'approval_request' | 'approval_response' | 'workflow_complete' | 'result' | 'claude_cli_start' | 'claude_cli_complete' | 'claude_cli_error';
    content?: string;
    agent?: string;
    model?: string;  // v6.1-alpha: Claude model name
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
    proposal?: any;  // For architecture_proposal messages
    decision?: string;  // For architectureApprovalProcessed messages
    feedback?: string;  // For architecture_approval outgoing messages
    tool?: string;  // For agent_tool_start/complete messages
    tool_status?: string;  // For agent_tool_start/complete messages ("running" | "success" | "error")
    tool_result?: string;  // For agent_tool_complete messages
    tool_details?: {  // For agent_tool_start/complete messages (v5.8.1)
        files_read?: string[];
        files_written?: string[];
        scanning?: string[];
        ignoring?: string[];
        todos_added?: string[];
        todos_completed?: string[];
        files_analyzed?: number;
        languages?: string[];
        loc?: number;
        complexity_avg?: number;
        security_issues?: number;
        dependencies?: Record<string, string>;
        [key: string]: any;  // Allow additional properties
    };
    // v6.0.0: Approval Manager fields
    request_id?: string;  // For approval_request/response
    action_type?: string;  // For approval_request
    description?: string;  // For approval_request
    approved?: boolean;  // For approval_response
    // v6.0.0: Workflow complete fields
    success?: boolean;  // For workflow_complete
    quality_score?: number;  // For workflow_complete
    execution_time?: number;  // For workflow_complete
    analysis?: any;  // For workflow_complete (v6 insights)
    adaptations?: any;  // For workflow_complete (v6 insights)
    health?: any;  // For workflow_complete (v6 insights)
    errors?: any[];  // For workflow_complete
    warnings?: any[];  // For workflow_complete
    v6_systems_used?: any;  // For workflow_complete
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
        // Fallback to default (v6.0.0 Integrated port)
        return 'localhost:8002';
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
            const backendUrl = config.get<string>('backend.url', 'localhost:8002');  // v6.0.0 Integrated port
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
                this.log(`💭 ${message.agent || 'Agent'} thinking: ${message.content || message.message || ''}`);
                this.emit('thinking', message);
                this.emit('agent_activity', message);  // v5.8.1: Also emit for new activity visualization
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
                this.emit('agent_activity', message);  // v5.8.1: Also emit for new activity visualization
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

            case 'architecture_proposal':
            case 'architecture_proposal_revised':
                this.log(`🏛️ Architecture Proposal ${message.type === 'architecture_proposal_revised' ? '(Revised)' : ''}`);
                this.log(`📋 Proposal data: ${message.proposal ? 'Present' : 'Missing'}`);
                // Forward to UI - use exact event name that MultiAgentChatPanel expects!
                this.emit(message.type, message);  // v5.8.1: emit exact type (architecture_proposal or architecture_proposal_revised)
                break;

            case 'architectureApprovalProcessed':
                this.log(`✅ Architecture approval processed: ${message.decision}`);
                this.emit('architectureApprovalProcessed', message);
                break;

            case 'agent_complete':
                this.log(`✅ ${message.agent} completed: ${message.content || ''}`);
                this.emit('agent_activity', message);
                break;

            case 'agent_tool_start':
            case 'agent_tool_complete':
                const toolAction = message.type === 'agent_tool_start' ? 'started' : 'completed';
                this.log(`🔧 ${message.agent} tool ${toolAction}: ${message.tool} [${message.tool_status}]`);
                this.emit('agent_activity', message);
                break;

            case 'status':
                // v6.0.0: Workflow status updates
                this.log(`📊 v6 Status: ${message.status} - ${message.message}`);
                this.emit('progress', message);
                break;

            case 'approval_request':
                // v6.0.0: Approval requests from Approval Manager
                this.log(`🔐 v6 Approval Request: ${message.action_type} - ${message.description}`);
                this.emit('approval_request', message);
                break;

            case 'result':
                // v6.1-alpha: Final workflow result (comprehensive format)
                const resultMsg = message as any;
                this.log(`🎉 Workflow Result - Success: ${resultMsg.success} - Quality: ${resultMsg.quality_score}`);
                if (resultMsg.subtype === 'workflow_complete') {
                    this.log(`   ⏱️ Execution Time: ${resultMsg.execution_time}`);
                    this.log(`   📊 Agents Completed: ${resultMsg.agents_completed?.length || 0}`);
                    this.log(`   💾 Files Generated: ${resultMsg.files_generated || 0}`);
                }
                // Emit as both 'result' and 'workflow_complete' for compatibility
                this.emit('result', message);
                this.emit('workflow_complete', message);
                this.emit('complete', message);
                break;

            case 'workflow_complete':
                // v6.0.0: Workflow completion with v6 insights
                this.log(`🎉 v6 Workflow Complete - Quality: ${message.quality_score} - Success: ${message.success}`);
                this.emit('workflow_complete', message);
                this.emit('complete', message);
                break;

            case 'claude_cli_start':
                // v6.1-alpha: Claude CLI subprocess started
                this.log(`🚀 Claude CLI Started: ${message.agent} (${message.model})`);
                this.log(`   Tools: ${(message as any).tools?.join(', ') || 'unknown'}`);
                this.log(`   Permission Mode: ${(message as any).permission_mode || 'unknown'}`);
                this.emit('agent_activity', {
                    type: 'agent_activity',
                    activity_type: 'agent_progress',
                    agent: message.agent,
                    content: `🚀 Starting Claude CLI code generation...`,
                    tool: 'claude-cli',
                    tool_status: 'running'
                });
                break;

            case 'claude_cli_complete':
                // v6.1-alpha: Claude CLI subprocess completed successfully
                const cliMsg = message as any;
                this.log(`✅ Claude CLI Complete: ${message.agent}`);
                this.log(`   Duration: ${cliMsg.duration_ms ? (cliMsg.duration_ms / 1000).toFixed(2) + 's' : 'unknown'}`);
                this.log(`   Events: ${cliMsg.events_count || 'unknown'}`);
                this.log(`   Output Length: ${cliMsg.output_length || 'unknown'} chars`);
                this.emit('agent_activity', {
                    type: 'agent_activity',
                    activity_type: 'agent_tool_complete',
                    agent: message.agent,
                    content: `✅ Code generation completed (${cliMsg.duration_ms ? (cliMsg.duration_ms / 1000).toFixed(1) + 's' : 'unknown'})`,
                    tool: 'claude-cli',
                    tool_status: 'success'
                });
                break;

            case 'claude_cli_error':
                // v6.1-alpha: Claude CLI subprocess failed
                const errMsg = message as any;
                this.log(`❌ Claude CLI Error: ${message.agent}`);
                this.log(`   Error Type: ${errMsg.error_type || 'unknown'}`);
                this.log(`   Error: ${errMsg.error || 'unknown'}`);
                this.emit('agent_activity', {
                    type: 'agent_activity',
                    activity_type: 'agent_tool_complete',
                    agent: message.agent,
                    content: `❌ Code generation failed: ${errMsg.error || 'unknown error'}`,
                    tool: 'claude-cli',
                    tool_status: 'error'
                });
                // Also emit as error for error handling
                this.emit('error', {
                    type: 'error',
                    agent: message.agent,
                    message: `Claude CLI error: ${errMsg.error}`,
                    details: { error_type: errMsg.error_type, duration_ms: errMsg.duration_ms }
                });
                break;

            default:
                this.log(`⚠️ Unhandled message type: ${message.type}`);
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