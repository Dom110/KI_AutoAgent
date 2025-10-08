/**
 * MultiAgentChatPanel - Backend Integrated Version
 * Chat UI that connects to Python backend via WebSocket
 */

import * as vscode from 'vscode';
import { BackendClient, BackendMessage } from '../backend/BackendClient';

export class MultiAgentChatPanel {
    public static currentPanel: MultiAgentChatPanel | undefined;
    private static readonly viewType = 'kiAutoAgentChat';

    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionUri: vscode.Uri;
    private _disposables: vscode.Disposable[] = [];
    private _isDisposed = false;
    private backendClient: BackendClient;

    // UI State
    private _thinkingMode: boolean = false;
    private _thinkingIntensity: 'quick' | 'normal' | 'deep' | 'layered' = 'normal';
    private _isProcessing: boolean = false;
    private _conversationHistory: any[] = [];
    private _streamBuffer: Map<string, string> = new Map();
    private static debugChannel: vscode.OutputChannel;

    // Progress message deduplication
    private lastProgressMessage: Map<string, string> = new Map();
    private progressDebounceTimers: Map<string, NodeJS.Timeout> = new Map();
    private processedMessages: Set<string> = new Set();

    public static createOrShow(
        extensionUri: vscode.Uri,
        backendClient: BackendClient
    ) {
        const column = vscode.ViewColumn.Beside;

        // If panel exists, reveal it
        if (MultiAgentChatPanel.currentPanel) {
            MultiAgentChatPanel.currentPanel._panel.reveal(column);
            return;
        }

        // Create new panel
        const panel = vscode.window.createWebviewPanel(
            MultiAgentChatPanel.viewType,
            '🤖 KI AutoAgent Chat',
            column,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        MultiAgentChatPanel.currentPanel = new MultiAgentChatPanel(
            panel,
            extensionUri,
            backendClient
        );
    }

    public static sendMessageToPanel(message: BackendMessage) {
        if (MultiAgentChatPanel.currentPanel) {
            MultiAgentChatPanel.currentPanel.sendMessage(message);
        }
    }

    private constructor(
        panel: vscode.WebviewPanel,
        extensionUri: vscode.Uri,
        backendClient: BackendClient
    ) {
        this._panel = panel;
        this._extensionUri = extensionUri;
        this.backendClient = backendClient;

        // Create debug output channel if not exists
        if (!MultiAgentChatPanel.debugChannel) {
            MultiAgentChatPanel.debugChannel = vscode.window.createOutputChannel('KI AutoAgent Debug');
            MultiAgentChatPanel.debugChannel.appendLine('🔍 Debug Console initialized');
            MultiAgentChatPanel.debugChannel.show();
        }

        // Connect BackendClient to debug channel
        if (this.backendClient && (this.backendClient as any).setDebugChannel) {
            (this.backendClient as any).setDebugChannel(MultiAgentChatPanel.debugChannel);
        }

        // Set HTML content
        this._update();

        // Handle messages from webview
        this._panel.webview.onDidReceiveMessage(
            async (message) => {
                switch (message.type) {
                    case 'chat':
                        await this.handleChatMessage(message);
                        break;
                    case 'selectAgent':
                        await this.handleAgentSelection(message);
                        break;
                    case 'command':
                        await this.handleCommand(message);
                        break;
                    case 'newChat':
                        await this.handleNewChat();
                        break;
                    case 'pause':
                        await this.handlePause();
                        break;
                    case 'resumeWithInstructions':
                        await this.handleResumeWithInstructions(message.instructions);
                        break;
                    case 'stopAndRollback':
                        await this.handleStopAndRollback();
                        break;
                    case 'toggleThinking':
                        this.handleToggleThinking(message);
                        break;
                    case 'showHistory':
                        await this.handleShowHistory();
                        break;
                    case 'loadHistory':
                        await this.handleLoadHistory(message);
                        break;
                    case 'debug':
                        this.handleDebugMessage(message);
                        break;
                    case 'architecture_approval':
                        // v5.2.0: Forward architecture approval to backend
                        await this.handleArchitectureApproval(message);
                        break;
                }
            },
            null,
            this._disposables
        );

        // Handle panel disposal
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

        // Setup backend event handlers
        this.setupBackendHandlers();
    }

    private setupBackendHandlers() {
        MultiAgentChatPanel.debugChannel.appendLine('🔗 Setting up backend handlers...');

        // Handle responses from backend
        this.backendClient.on('response', (message: BackendMessage) => {
            const agent = message.agent || 'orchestrator';
            const content = message.content || 'No content received';

            MultiAgentChatPanel.debugChannel.appendLine(`📥 Received response from ${agent}: ${content.substring(0, 100)}...`);
            MultiAgentChatPanel.debugChannel.appendLine(`📝 Full content length: ${content.length} characters`);

            // Reset processing flag when we get a response
            this._isProcessing = false;

            // Clear stream buffer for this agent
            this._streamBuffer.delete(agent);

            // Send to webview
            const msgToSend = {
                type: 'response',  // Changed to 'response' for v5.0.0
                agent: agent,
                content: content,
                timestamp: message.timestamp || new Date().toISOString()
            };

            MultiAgentChatPanel.debugChannel.appendLine(`🚀 Sending to webview: ${JSON.stringify(msgToSend).substring(0, 200)}...`);
            this.sendMessage(msgToSend);

            // Add to history
            if (message.content) {
                this._conversationHistory.push({
                    role: 'assistant',
                    content: message.content,
                    agent: agent,
                    timestamp: new Date().toISOString()
                });
            }
        });

        this.backendClient.on('thinking', (message: BackendMessage) => {
            // v5.9.0 FIX: Filter out undefined/empty content before sending
            const content = message.content || message.message || '';
            if (!content || content === 'undefined' || content === 'null') {
                MultiAgentChatPanel.debugChannel.appendLine(`⚠️ Skipping thinking message with undefined content from ${message.agent}`);
                return;
            }

            MultiAgentChatPanel.debugChannel.appendLine(`💭 Agent thinking: ${message.agent || 'orchestrator'}`);
            this.sendMessage({
                type: 'agent_thinking',  // Use underscore for v5.0.0
                agent: message.agent || 'orchestrator',
                content: content
            });
        });

        this.backendClient.on('progress', (message: BackendMessage) => {
            // Handle progress updates from agents
            const agent = message.agent || 'orchestrator';
            const content = message.content || message.message || '';

            // Skip empty or undefined content
            if (!content || content === 'undefined') {
                return;
            }

            // Check for duplicate message
            const lastMessage = this.lastProgressMessage.get(agent);
            if (lastMessage === content) {
                return; // Skip duplicate
            }

            // Clear any existing debounce timer for this agent
            if (this.progressDebounceTimers.has(agent)) {
                clearTimeout(this.progressDebounceTimers.get(agent)!);
            }

            // Debounce rapid updates (50ms)
            const timer = setTimeout(() => {
                MultiAgentChatPanel.debugChannel.appendLine(`⏳ Progress from ${agent}: ${content}`);

                // Send progress update to UI
                this.sendMessage({
                    type: 'progress',
                    agent: agent,
                    content: content,
                    isStreaming: false,
                    timestamp: Date.now()
                });

                // Store this as the last message for this agent
                this.lastProgressMessage.set(agent, content);

                // Clean up timer reference
                this.progressDebounceTimers.delete(agent);
            }, 50);

            this.progressDebounceTimers.set(agent, timer);
        });

        this.backendClient.on('complete', (message: BackendMessage) => {
            MultiAgentChatPanel.debugChannel.appendLine(`✅ Complete from ${message.agent}`);
            // Also reset here for safety
            this._isProcessing = false;
            this.sendMessage({
                type: 'complete',
                agent: message.agent,
                metadata: message.metadata
            });
        });

        // Handle step_completed from LangGraph v5.0.0
        this.backendClient.on('step_completed', (message: any) => {
            MultiAgentChatPanel.debugChannel.appendLine(`📊 Step completed: ${message.agent} - ${message.task}`);
            this.sendMessage({
                type: 'step_completed',
                agent: message.agent || 'orchestrator',
                result: message.result || ''
            });
        });

        // Handle errors
        this.backendClient.on('error', (error: any) => {
            MultiAgentChatPanel.debugChannel.appendLine(`❌ Backend error: ${error.message || error.error || JSON.stringify(error)}`);
            this._isProcessing = false;
            vscode.window.showErrorMessage(`Backend error: ${error.message || 'Unknown error'}`);
        });

        // Handle welcome/connection
        this.backendClient.on('welcome', (message: any) => {
            MultiAgentChatPanel.debugChannel.appendLine(`🎉 Connected to backend: ${message.message || 'Connection established'}`);
        });

        // Handle session restoration (reconnection to running tasks)
        this.backendClient.on('session_restore', (message: any) => {
            MultiAgentChatPanel.debugChannel.appendLine(`🔄 Session restore: ${message.status} - ${message.message}`);

            if (message.status === 'running') {
                // Show notification about running task
                vscode.window.showInformationMessage(
                    `🔄 You have a task still running: "${message.task?.prompt?.substring(0, 50)}..."`,
                    'View Progress'
                ).then(selection => {
                    if (selection === 'View Progress') {
                        // Show the last progress messages
                        if (message.progress && message.progress.length > 0) {
                            message.progress.forEach((p: any) => {
                                this.sendMessage({
                                    type: 'progress',
                                    agent: message.task?.agent || 'orchestrator',
                                    content: p.message,
                                    isStreaming: false
                                });
                            });
                        }
                    }
                });

                // Mark as processing
                this._isProcessing = true;
            } else if (message.status === 'completed') {
                // Show notification about completed task
                vscode.window.showInformationMessage(
                    `✅ Your previous task has completed: "${message.task?.prompt?.substring(0, 50)}..."`,
                    'View Result'
                ).then(selection => {
                    if (selection === 'View Result') {
                        // Display the result
                        if (message.result) {
                            this.sendMessage({
                                type: 'agentResponse',
                                agent: message.task?.agent || 'orchestrator',
                                content: message.result.content || 'Task completed',
                                timestamp: new Date().toISOString()
                            });
                        }
                    }
                });
            }
        });

        // v5.2.0: Handle architecture proposal messages
        this.backendClient.on('architecture_proposal', (message: any) => {
            MultiAgentChatPanel.debugChannel.appendLine(`📋 Architecture proposal received`);
            this.sendMessage({
                type: 'architecture_proposal',
                proposal: message.proposal,
                session_id: message.session_id,
                formatted_message: message.formatted_message
            });
        });

        this.backendClient.on('architecture_proposal_revised', (message: any) => {
            MultiAgentChatPanel.debugChannel.appendLine(`📋 Revised architecture proposal received`);
            this.sendMessage({
                type: 'architecture_proposal_revised',
                proposal: message.proposal,
                session_id: message.session_id,
                formatted_message: message.formatted_message
            });
        });

        this.backendClient.on('architectureApprovalProcessed', (message: any) => {
            MultiAgentChatPanel.debugChannel.appendLine(`✅ Architecture approval processed: ${message.decision}`);
            this.sendMessage({
                type: 'architectureApprovalProcessed',
                session_id: message.session_id,
                decision: message.decision,
                message: message.message
            });
        });

        // v5.8.1: Agent Activity Visualization
        this.backendClient.on('agent_activity', (message: any) => {
            MultiAgentChatPanel.debugChannel.appendLine(`🔧 Agent activity: ${message.type} from ${message.agent}`);
            this.sendMessage({
                type: 'agent_activity',
                activity_type: message.type,
                agent: message.agent,
                content: message.content,
                tool: message.tool,
                tool_status: message.tool_status,
                tool_result: message.tool_result,
                timestamp: message.timestamp
            });
        });

        MultiAgentChatPanel.debugChannel.appendLine('✅ Backend handlers setup complete');
    }

    private async handleChatMessage(message: any) {
        if (this._isProcessing) {
            vscode.window.showWarningMessage('Please wait for the current operation to complete');
            return;
        }

        this._isProcessing = true;

        // Log to debug console
        MultiAgentChatPanel.debugChannel.appendLine(`\n📨 User Message: ${message.content}`);
        MultiAgentChatPanel.debugChannel.appendLine(`   Agent: ${message.agent || 'orchestrator'}`);
        MultiAgentChatPanel.debugChannel.appendLine(`   Mode: ${message.mode || 'auto'}`);

        // Send user message to webview
        this.sendMessage({
            type: 'userMessage',
            content: message.content
        });

        // Add to history
        this._conversationHistory.push({
            role: 'user',
            content: message.content,
            timestamp: new Date().toISOString()
        });

        // Get workspace path for backend
        const workspaceFolders = vscode.workspace.workspaceFolders;
        const workspacePath = workspaceFolders ? workspaceFolders[0].uri.fsPath : undefined;

        // Send to backend with thinking mode and workspace path
        MultiAgentChatPanel.debugChannel.appendLine(`📤 Sending message to backend...`);
        MultiAgentChatPanel.debugChannel.appendLine(`   Workspace: ${workspacePath}`);
        MultiAgentChatPanel.debugChannel.appendLine(`   Connected: ${this.backendClient.isConnectedToBackend()}`);

        try {
            await this.backendClient.sendChatMessage({
            prompt: message.content,
            agent: message.agent || 'orchestrator',
            mode: message.mode || 'auto',
            thinkingMode: this._thinkingMode,
            context: {
                workspace_path: workspacePath || process.cwd()
            }
            });
            MultiAgentChatPanel.debugChannel.appendLine(`✅ Message sent successfully`);
        } catch (error: any) {
            MultiAgentChatPanel.debugChannel.appendLine(`❌ Failed to send message: ${error.message}`);
            console.error('Send error:', error);
        }
    }

    private async handleAgentSelection(message: any) {
        // Update UI to show selected agent
        this.sendMessage({
            type: 'agentSelected',
            agent: message.agent
        });
    }

    private async handleCommand(message: any) {
        await this.backendClient.sendCommand(message.command, message.args);
    }

    private async handleNewChat() {
        this._conversationHistory = [];
        this._isProcessing = false;
        this.sendMessage({ type: 'clearChat' });
        vscode.window.showInformationMessage('New chat session started');
    }

    // ============================================================================
    // OBSOLETE v5.9.0: Backend message sending for pause/resume
    // Reason: Backend doesn't implement pause/resume message handlers yet
    // Error: "Unknown message type: pause/resume" from backend
    // Status: Functionality works UI-only, backend integration pending
    // Decision: Keep UI functionality, skip backend messages until implemented
    // Marked for: Backend implementation OR removal after v5.9.0 testing
    // ============================================================================

    private async handlePause() {
        // OBSOLETE v5.9.0: Backend call commented out - not yet implemented
        // Original backend call that causes errors:
        /*
        if (this.backendClient) {
            await this.backendClient.sendMessage({
                type: 'pause'
            });
        }
        */

        // UI-only pause functionality (still works)
        this.sendMessage({ type: 'pauseActivated' });
        vscode.window.showInformationMessage('Task paused. You can add instructions or stop.');
    }

    private async handleResumeWithInstructions(instructions?: string) {
        // OBSOLETE v5.9.0: Backend call commented out - not yet implemented
        // Original backend call that causes errors:
        /*
        if (this.backendClient) {
            await this.backendClient.sendMessage({
                type: 'resume',
                additionalInstructions: instructions
            });
        }
        */

        // UI-only resume functionality (still works)
        this.sendMessage({ type: 'resumed' });
        vscode.window.showInformationMessage(instructions ?
            'Resuming with additional instructions' : 'Resuming task');
    }

    // ============================================================================
    // END OBSOLETE SECTION - Backend pause/resume calls above marked for review
    // ============================================================================

    private async handleStopAndRollback() {
        // Send stop and rollback signal
        if (this.backendClient) {
            await this.backendClient.sendMessage({
                type: 'stopAndRollback'
            });
        }
        this._isProcessing = false;
        this.sendMessage({ type: 'stoppedAndRolledBack' });
        vscode.window.showInformationMessage('Task stopped and rolled back to last checkpoint');
    }

    private handleToggleThinking(message: any) {
        this._thinkingMode = message.enabled;
        if (message.intensity) {
            this._thinkingIntensity = message.intensity;
        }
        this.sendMessage({
            type: 'thinkingModeChanged',
            enabled: this._thinkingMode,
            intensity: this._thinkingIntensity
        });
    }

    private async handleShowHistory() {
        if (this._conversationHistory.length === 0) {
            vscode.window.showInformationMessage('No conversation history available');
            return;
        }

        // For now, just show count - full history implementation can be added later
        vscode.window.showInformationMessage(`Conversation has ${this._conversationHistory.length} messages`);
    }

    /**
     * v5.2.0: Handle architecture proposal approval from user
     */
    private async handleArchitectureApproval(message: any) {
        MultiAgentChatPanel.debugChannel.appendLine(`📋 Handling architecture approval: ${message.decision}`);

        try {
            // v5.8.1: Send approval as direct message type (not command!)
            await this.backendClient.sendMessage({
                type: 'architecture_approval' as any,
                session_id: message.session_id,
                decision: message.decision,
                feedback: message.feedback || ''
            });

            MultiAgentChatPanel.debugChannel.appendLine(`✅ Architecture approval sent to backend: ${message.decision}`);

        } catch (error) {
            MultiAgentChatPanel.debugChannel.appendLine(`❌ Error sending architecture approval: ${error}`);
            vscode.window.showErrorMessage(`Failed to send architecture approval: ${error}`);
        }
    }

    private async handleLoadHistory(message: any) {
        // Get project path
        const workspaceFolders = vscode.workspace.workspaceFolders;
        const projectPath = workspaceFolders ? workspaceFolders[0].uri.fsPath : undefined;

        if (!projectPath) {
            console.log('No workspace folder found, skipping history load');
            return;
        }

        try {
            // Request history from backend
            const response = await fetch(`http://localhost:8001/api/conversation/history?limit=${message.limit || 20}&project_path=${encodeURIComponent(projectPath)}`);

            if (response.ok) {
                // Type the response data properly
                interface HistoryResponse {
                    history: Array<{
                        role: string;
                        content: string;
                        agent?: string;
                        timestamp?: string;
                    }>;
                    source: string;
                    project?: string;
                }

                const data = await response.json() as HistoryResponse;

                if (data.history && data.history.length > 0) {
                    console.log(`Loaded ${data.history.length} messages from ${data.source} storage`);

                    // Display history in chat
                    for (const msg of data.history) {
                        const isUser = msg.role === 'user';
                        this.sendMessage({
                            type: 'historyMessage',
                            content: msg.content,
                            agent: msg.agent || 'unknown',
                            isUser: isUser,
                            timestamp: msg.timestamp
                        });
                    }

                    // Store in memory
                    this._conversationHistory = data.history;
                }
            }
        } catch (error) {
            console.error('Failed to load conversation history:', error);
        }
    }

    private sendMessage(message: any) {
        // Check if webview is still active before sending messages
        // This prevents "Webview is disposed" errors when chat is closed during processing
        if (this._isDisposed) {
            MultiAgentChatPanel.debugChannel.appendLine(`⚠️ Webview disposed, skipping message (normal if chat was closed)`);
            return;
        }

        // Create unique message ID for deduplication (skip for certain message types that should always go through)
        const skipDedup = ['userMessage', 'clearChat', 'agentResponse', 'error', 'complete', 'historyMessage', 'agentThinking', 'agent_thinking'];
        if (!skipDedup.includes(message.type)) {
            const messageId = `${message.type}-${message.agent || ''}-${message.content || ''}-${message.timestamp || ''}`;

            // Check if already processed
            if (this.processedMessages.has(messageId)) {
                MultiAgentChatPanel.debugChannel.appendLine(`⚡ Skipping duplicate message: ${message.type} from ${message.agent}`);
                return;
            }

            // Mark as processed
            this.processedMessages.add(messageId);

            // Clean old messages (keep last 100)
            if (this.processedMessages.size > 100) {
                const entries = Array.from(this.processedMessages);
                entries.slice(0, entries.length - 100).forEach(id => {
                    this.processedMessages.delete(id);
                });
            }
        }

        try {
            if (this._panel && this._panel.webview) {
                this._panel.webview.postMessage(message);
            }
        } catch (error) {
            // v5.9.0 FIX: NEVER mark as disposed here - let dispose() handle it
            // Race conditions can cause temporary errors that don't mean panel is disposed
            MultiAgentChatPanel.debugChannel.appendLine(`⚠️ Error sending message (${message.type}): ${error}`);
            // Don't set _isDisposed = true here!
        }
    }

    private handleDebugMessage(message: any) {
        // Log debug messages from webview to VS Code debug console
        const timestamp = new Date().toLocaleTimeString();
        const level = message.level || 'LOG';
        const content = message.content || message.message || '';

        MultiAgentChatPanel.debugChannel.appendLine(`[${timestamp}] [${level}] ${content}`);

        // Also log details if provided
        if (message.details) {
            MultiAgentChatPanel.debugChannel.appendLine(`  Details: ${JSON.stringify(message.details, null, 2)}`);
        }
    }

    private _update() {
        const webview = this._panel.webview;
        this._panel.title = '🤖 KI AutoAgent Chat';
        this._panel.webview.html = this._getHtmlForWebview(webview);
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        return `<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>KI AutoAgent Chat</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    margin: 0;
                    padding: 0;
                    display: flex;
                    flex-direction: column;
                    height: 100vh;
                    background: var(--vscode-editor-background);
                    color: var(--vscode-editor-foreground);
                }

                #header {
                    padding: 10px;
                    background: var(--vscode-titleBar-activeBackground);
                    color: var(--vscode-titleBar-activeForeground);
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }

                #messages {
                    flex: 1;
                    overflow-y: auto;
                    padding: 20px;
                }

                .message {
                    margin-bottom: 15px;
                    padding: 10px;
                    border-radius: 8px;
                    max-width: 80%;
                }

                .user-message {
                    background: var(--vscode-input-background);
                    margin-left: auto;
                    border: 1px solid var(--vscode-input-border);
                }

                .agent-message {
                    background: var(--vscode-editor-inactiveSelectionBackground);
                }

                .agent-thinking {
                    opacity: 0.7;
                    font-style: italic;
                }

                .agent-badge {
                    display: inline-block;
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-size: 0.85em;
                    margin-right: 5px;
                    background: var(--vscode-badge-background);
                    color: var(--vscode-badge-foreground);
                }

                #input-container {
                    padding: 20px;
                    background: var(--vscode-sideBar-background);
                    border-top: 1px solid var(--vscode-panel-border);
                }

                #input-row {
                    display: flex;
                    gap: 10px;
                    align-items: flex-end;
                }

                #message-input {
                    flex: 1;
                    padding: 10px;
                    background: var(--vscode-input-background);
                    color: var(--vscode-input-foreground);
                    border: 1px solid var(--vscode-input-border);
                    border-radius: 4px;
                    font-size: 14px;
                    font-family: var(--vscode-font-family);
                    resize: none;
                    overflow-y: auto;
                    min-height: 40px;
                    max-height: 150px;
                    line-height: 1.4;
                }

                #send-button {
                    padding: 10px 20px;
                    background: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: bold;
                }

                #send-button:hover {
                    background: var(--vscode-button-hoverBackground);
                }

                #agent-selector {
                    margin-bottom: 10px;
                    display: flex;
                    gap: 5px;
                    flex-wrap: wrap;
                }

                .agent-option {
                    padding: 5px 10px;
                    background: var(--vscode-button-secondaryBackground);
                    color: var(--vscode-button-secondaryForeground);
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                }

                #plan-first-btn {
                    padding: 5px 10px;
                    background: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                    font-weight: bold;
                    margin-right: 10px;
                }

                #plan-first-btn:hover {
                    background: var(--vscode-button-hoverBackground);
                }

                #plan-first-btn.active {
                    background: var(--vscode-editorWarning-foreground);
                    color: var(--vscode-editor-background);
                }

                .agent-option.selected {
                    background: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                }

                .agent-option:hover {
                    opacity: 0.8;
                }

                .header-btn {
                    padding: 5px 10px;
                    background: var(--vscode-button-secondaryBackground);
                    color: var(--vscode-button-secondaryForeground);
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                }

                .header-btn:hover {
                    background: var(--vscode-button-secondaryHoverBackground);
                }

                .header-btn.active {
                    background: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                }

                .header-btn.danger {
                    background: #d73a49;
                    color: white;
                }

                .header-btn.danger:hover {
                    background: #cb2431;
                }

                .header-btn.danger:disabled {
                    background: #6a6a6a;
                    opacity: 0.5;
                    cursor: not-allowed;
                }

                /* Activity indicator */
                .activity-indicator {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    padding: 12px 18px;
                    background: var(--vscode-notifications-background, #1e1e1e);
                    border: 2px solid var(--vscode-notifications-border, #454545);
                    border-radius: 10px;
                    display: none;
                    align-items: center;
                    gap: 12px;
                    z-index: 9999;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.4);
                    min-width: 200px;
                    max-width: 400px;
                    font-family: var(--vscode-font-family);
                }

                .activity-indicator.active {
                    display: flex;
                }

                .activity-indicator .spinner {
                    width: 16px;
                    height: 16px;
                    border: 2px solid var(--vscode-progressBar-background);
                    border-top-color: transparent;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }

                @keyframes spin {
                    to { transform: rotate(360deg); }
                }

                .activity-indicator .text {
                    color: var(--vscode-foreground, #cccccc);
                    font-size: 13px;
                    font-weight: 500;
                    line-height: 1.4;
                    word-wrap: break-word;
                }

                /* Progress bubble for updates */
                .message.progress-update {
                    background: var(--vscode-editor-inactiveSelectionBackground) !important;
                    border: 1px solid var(--vscode-panel-border);
                    padding: 8px 12px;
                    margin: 5px 0;
                }

                /* Agent-specific bubble colors for dark mode - semi-transparent */
                body.vscode-dark .message.architect,
                body.vscode-dark .message.architect-bubble {
                    background: rgba(30, 58, 95, 0.3) !important;
                    border: 1px solid rgba(42, 74, 127, 0.5);
                    backdrop-filter: blur(8px);
                }

                body.vscode-dark .message.codesmith,
                body.vscode-dark .message.codesmith-bubble {
                    background: rgba(58, 46, 95, 0.3) !important;
                    border: 1px solid rgba(74, 62, 127, 0.5);
                    backdrop-filter: blur(8px);
                }

                body.vscode-dark .message.orchestrator,
                body.vscode-dark .message.orchestrator-bubble {
                    background: rgba(74, 46, 74, 0.3) !important;
                    border: 1px solid rgba(106, 78, 106, 0.5);
                    backdrop-filter: blur(8px);
                }

                body.vscode-dark .message.research,
                body.vscode-dark .message.research-bubble {
                    background: rgba(46, 74, 58, 0.3) !important;
                    border: 1px solid rgba(62, 106, 74, 0.5);
                    backdrop-filter: blur(8px);
                }

                body.vscode-dark .message.reviewer,
                body.vscode-dark .message.reviewer-bubble {
                    background: rgba(74, 58, 46, 0.3) !important;
                    border: 1px solid rgba(106, 90, 62, 0.5);
                    backdrop-filter: blur(8px);
                }

                body.vscode-dark .message.performance_bot,
                body.vscode-dark .message.performance-bubble,
                body.vscode-dark .message.performance-bot-bubble {
                    background: rgba(90, 58, 46, 0.3) !important;
                    border: 1px solid rgba(122, 90, 62, 0.5);
                    backdrop-filter: blur(8px);
                }

                body.vscode-dark .message.fixer,
                body.vscode-dark .message.fixer-bubble {
                    background: rgba(46, 90, 74, 0.3) !important;
                    border: 1px solid rgba(62, 122, 106, 0.5);
                    backdrop-filter: blur(8px);
                }

                body.vscode-dark .message.docubot,
                body.vscode-dark .message.docubot-bubble {
                    background: rgba(90, 74, 46, 0.3) !important;
                    border: 1px solid rgba(122, 106, 62, 0.5);
                    backdrop-filter: blur(8px);
                }

                body.vscode-dark .message.tradestrat,
                body.vscode-dark .message.tradestrat-bubble {
                    background: rgba(74, 46, 90, 0.3) !important;
                    border: 1px solid rgba(106, 62, 122, 0.5);
                    backdrop-filter: blur(8px);
                }

                body.vscode-dark .message.opus-arbitrator,
                body.vscode-dark .message.opus-arbitrator-bubble {
                    background: rgba(90, 46, 46, 0.3) !important;
                    border: 1px solid rgba(122, 62, 62, 0.5);
                    backdrop-filter: blur(8px);
                }

                /* Light mode colors - semi-transparent */
                body.vscode-light .message.architect,
                body.vscode-light .message.architect-bubble {
                    background: rgba(230, 242, 255, 0.5) !important;
                    border: 1px solid rgba(179, 217, 255, 0.7);
                    backdrop-filter: blur(8px);
                }

                body.vscode-light .message.codesmith,
                body.vscode-light .message.codesmith-bubble {
                    background: rgba(240, 230, 255, 0.5) !important;
                    border: 1px solid rgba(217, 179, 255, 0.7);
                    backdrop-filter: blur(8px);
                }

                body.vscode-light .message.orchestrator,
                body.vscode-light .message.orchestrator-bubble {
                    background: rgba(255, 230, 240, 0.5) !important;
                    border: 1px solid rgba(255, 179, 217, 0.7);
                    backdrop-filter: blur(8px);
                }

                body.vscode-light .message.research,
                body.vscode-light .message.research-bubble {
                    background: rgba(230, 255, 240, 0.5) !important;
                    border: 1px solid rgba(179, 255, 217, 0.7);
                    backdrop-filter: blur(8px);
                }

                body.vscode-light .message.reviewer,
                body.vscode-light .message.reviewer-bubble {
                    background: rgba(255, 245, 230, 0.5) !important;
                    border: 1px solid rgba(255, 223, 179, 0.7);
                    backdrop-filter: blur(8px);
                }

                body.vscode-light .message.performance_bot,
                body.vscode-light .message.performance-bubble,
                body.vscode-light .message.performance-bot-bubble {
                    background: rgba(255, 230, 230, 0.5) !important;
                    border: 1px solid rgba(255, 179, 179, 0.7);
                    backdrop-filter: blur(8px);
                }

                body.vscode-light .message.fixer,
                body.vscode-light .message.fixer-bubble {
                    background: rgba(230, 255, 245, 0.5) !important;
                    border: 1px solid rgba(179, 255, 233, 0.7);
                    backdrop-filter: blur(8px);
                }

                body.vscode-light .message.docubot,
                body.vscode-light .message.docubot-bubble {
                    background: rgba(255, 250, 230, 0.5) !important;
                    border: 1px solid rgba(255, 240, 179, 0.7);
                    backdrop-filter: blur(8px);
                }

                body.vscode-light .message.tradestrat,
                body.vscode-light .message.tradestrat-bubble {
                    background: rgba(250, 230, 255, 0.5) !important;
                    border: 1px solid rgba(240, 179, 255, 0.7);
                    backdrop-filter: blur(8px);
                }

                body.vscode-light .message.opus-arbitrator,
                body.vscode-light .message.opus-arbitrator-bubble {
                    background: rgba(255, 230, 235, 0.5) !important;
                    border: 1px solid rgba(255, 179, 190, 0.7);
                    backdrop-filter: blur(8px);
                }

                #send-button {
                    padding: 8px 16px;
                    background: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 500;
                    min-width: 80px;
                }

                #send-button:hover {
                    background: var(--vscode-button-hoverBackground);
                }

                #send-button:active {
                    transform: scale(0.98);
                }

                #send-button:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }

                /* Markdown Styles */
                .message h1, .message h2, .message h3 {
                    margin-top: 10px;
                    margin-bottom: 5px;
                    font-weight: bold;
                }

                .message h1 {
                    font-size: 1.5em;
                    color: var(--vscode-textLink-foreground);
                }

                .message h2 {
                    font-size: 1.3em;
                    color: var(--vscode-textLink-activeForeground);
                }

                .message h3 {
                    font-size: 1.1em;
                }

                .message code {
                    background: var(--vscode-textCodeBlock-background);
                    color: var(--vscode-textPreformat-foreground);
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-family: var(--vscode-editor-font-family);
                    font-size: 0.9em;
                }

                .message pre {
                    background: var(--vscode-textCodeBlock-background);
                    color: var(--vscode-textPreformat-foreground);
                    padding: 10px;
                    border-radius: 5px;
                    overflow-x: auto;
                    margin: 10px 0;
                }

                .message pre code {
                    background: transparent;
                    padding: 0;
                }

                .message ul, .message ol {
                    margin: 5px 0;
                    padding-left: 20px;
                }

                .message li {
                    margin: 3px 0;
                }

                .message strong {
                    font-weight: bold;
                    color: var(--vscode-textLink-foreground);
                }

                .message em {
                    font-style: italic;
                    color: var(--vscode-descriptionForeground);
                }

                .message p {
                    margin: 8px 0;
                    line-height: 1.5;
                }

                .message blockquote {
                    border-left: 3px solid var(--vscode-textBlockQuote-border);
                    padding-left: 10px;
                    margin: 10px 0;
                    color: var(--vscode-textBlockQuote-color);
                }

                /* Warning button style for pause */
                .header-btn.warning {
                    background: #f0ad4e;
                    color: white;
                }

                .header-btn.warning:hover {
                    background: #ec971f;
                }

                .header-btn.warning:disabled {
                    background: #6a6a6a;
                    opacity: 0.5;
                    cursor: not-allowed;
                }

                /* Pause overlay and dialog */
                .pause-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.5);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 2000;
                }

                .pause-dialog {
                    background: var(--vscode-editor-background);
                    border: 1px solid var(--vscode-widget-border);
                    border-radius: 8px;
                    padding: 20px;
                    max-width: 500px;
                    width: 90%;
                    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
                }

                .pause-dialog h3 {
                    margin: 0 0 15px 0;
                    color: var(--vscode-foreground);
                    font-size: 1.2em;
                }

                .pause-dialog p {
                    margin: 10px 0;
                    color: var(--vscode-foreground);
                }

                .pause-dialog textarea {
                    width: 100%;
                    background: var(--vscode-input-background);
                    color: var(--vscode-input-foreground);
                    border: 1px solid var(--vscode-input-border);
                    border-radius: 4px;
                    padding: 8px;
                    font-family: var(--vscode-font-family);
                    font-size: 14px;
                    resize: vertical;
                    margin-bottom: 15px;
                }

                .pause-dialog .pause-actions {
                    display: flex;
                    gap: 10px;
                    justify-content: flex-end;
                }

                .pause-dialog .btn {
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                    transition: background 0.2s;
                }

                .pause-dialog .btn.primary {
                    background: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                }

                .pause-dialog .btn.primary:hover {
                    background: var(--vscode-button-hoverBackground);
                }

                .pause-dialog .btn.info {
                    background: #17a2b8;
                    color: white;
                }

                .pause-dialog .btn.info:hover {
                    background: #138496;
                }

                .pause-dialog .btn.danger {
                    background: #d73a49;
                    color: white;
                }

                .pause-dialog .btn.danger:hover {
                    background: #cb2431;
                }

                /* Initialization overlay */
                .initialization-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.85);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 10000;
                    backdrop-filter: blur(5px);
                }

                .initialization-overlay.fade-out {
                    animation: fadeOut 0.3s ease-out;
                }

                @keyframes fadeOut {
                    from { opacity: 1; }
                    to { opacity: 0; }
                }

                .initialization-content {
                    background: var(--vscode-editor-background);
                    border: 1px solid var(--vscode-panel-border);
                    border-radius: 8px;
                    padding: 30px;
                    text-align: center;
                    max-width: 400px;
                }

                .initialization-content .spinner {
                    width: 50px;
                    height: 50px;
                    border: 3px solid var(--vscode-progressBar-background);
                    border-top-color: transparent;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 20px;
                }

                .initialization-content h2 {
                    margin: 0 0 10px;
                    color: var(--vscode-editor-foreground);
                }

                .initialization-content p {
                    margin: 0 0 20px;
                    color: var(--vscode-descriptionForeground);
                    font-size: 14px;
                }

                .progress-bar {
                    width: 100%;
                    height: 4px;
                    background: var(--vscode-input-background);
                    border-radius: 2px;
                    overflow: hidden;
                }

                .progress-fill {
                    height: 100%;
                    background: var(--vscode-progressBar-background);
                    width: 0;
                    animation: progressAnimation 30s ease-out;
                }

                @keyframes progressAnimation {
                    0% { width: 0%; }
                    20% { width: 20%; }
                    40% { width: 35%; }
                    60% { width: 60%; }
                    80% { width: 85%; }
                    100% { width: 95%; }
                }

                /* Progress message styling */
                .progress-update {
                    background: var(--vscode-notebook-cellStatusBarItemHoverBackground);
                    border-left: 3px solid var(--vscode-progressBar-background);
                    padding: 10px;
                    margin: 10px 0;
                }

                .progress-update .agent-badge {
                    background: var(--vscode-progressBar-background);
                    color: var(--vscode-editor-background);
                    padding: 2px 8px;
                    border-radius: 3px;
                    font-size: 12px;
                    font-weight: bold;
                    margin-right: 8px;
                }

                .progress-content {
                    color: var(--vscode-editor-foreground);
                    margin-top: 5px;
                }

                /* v5.8.1: Agent Activity Visualization */
                .agent-activity {
                    background: var(--vscode-editor-inactiveSelectionBackground);
                    border-radius: 8px;
                    padding: 12px;
                    margin: 12px 0;
                    transition: opacity 0.3s ease;
                }

                .agent-activity .activity-header {
                    margin-bottom: 8px;
                }

                .agent-activity .agent-badge {
                    background: var(--vscode-badge-background);
                    color: var(--vscode-badge-foreground);
                    padding: 4px 10px;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: bold;
                    text-transform: capitalize;
                }

                .agent-activity .activity-content {
                    padding-left: 8px;
                }

                .agent-activity .activity-item {
                    padding: 6px 0;
                    font-size: 13px;
                    color: var(--vscode-editor-foreground);
                    opacity: 0.9;
                }

                .agent-activity .activity-item.thinking {
                    font-style: italic;
                    color: var(--vscode-descriptionForeground);
                }

                .agent-activity .activity-item.tool-running {
                    color: var(--vscode-charts-blue);
                }

                .agent-activity .activity-item.tool-success {
                    color: var(--vscode-charts-green);
                }

                .agent-activity .activity-item.tool-error {
                    color: var(--vscode-charts-red);
                }

                .agent-activity .activity-item.complete {
                    color: var(--vscode-charts-green);
                    font-weight: 600;
                }

                /* Agent-specific activity colors (inherit from existing agent colors) */
                .architect-activity {
                    border-left: 4px solid rgba(42, 74, 127, 0.8);
                }

                .codesmith-activity {
                    border-left: 4px solid rgba(74, 62, 127, 0.8);
                }

                .orchestrator-activity {
                    border-left: 4px solid rgba(106, 78, 106, 0.8);
                }

                .reviewer-activity {
                    border-left: 4px solid rgba(106, 90, 62, 0.8);
                }

                .fixer-activity {
                    border-left: 4px solid rgba(62, 122, 106, 0.8);
                }
            </style>
        </head>
        <body>
            <div id="header">
                <span style="font-size: 1.5em;">🤖</span>
                <h2 style="margin: 0;">KI AutoAgent Chat</h2>
                <div style="margin-left: auto; display: flex; gap: 10px; align-items: center;">
                    <button id="new-chat-btn" class="header-btn" title="New Chat">➕ New</button>
                    <button id="history-btn" class="header-btn" title="History">📜 History</button>
                    <button id="thinking-btn" class="header-btn" title="Toggle Thinking Mode">💭 Thinking</button>
                    <button id="agent-thinking-btn" class="header-btn" title="Agent Schritte anzeigen">🧠 Agent Schritte</button>
                    <button id="pause-btn" class="header-btn warning" title="Pause Task">⏸️ Pause</button>
                    <span style="opacity: 0.7; font-size: 0.9em;">Backend ✅</span>
                </div>
            </div>

            <div id="messages"></div>

            <div id="input-container">
                <div id="agent-selector">
                    <button id="plan-first-btn" class="control-button" title="Show plan before executing">
                        📋 Plan First
                    </button>
                    <button class="agent-option selected" data-agent="orchestrator">
                        🎯 Orchestrator
                    </button>
                    <button class="agent-option" data-agent="architect">
                        🏗️ Architect
                    </button>
                    <button class="agent-option" data-agent="codesmith">
                        💻 CodeSmith
                    </button>
                    <button class="agent-option" data-agent="research">
                        🔍 Research
                    </button>
                    <button class="agent-option" data-agent="reviewer">
                        🔎 Reviewer
                    </button>
                    <button class="agent-option" data-agent="docu">
                        📚 Documentation
                    </button>
                    <button class="agent-option" data-agent="opus-arbitrator">
                        ⚖️ Arbitrator
                    </button>
                </div>

                <div id="input-row">
                    <textarea
                        id="message-input"
                        placeholder="Type your message... (Shift+Enter for new line)"
                        autofocus
                        rows="1"
                    ></textarea>
                    <button type="button" id="send-button">Send 📤</button>
                    <button type="button" id="stop-button" style="display: none;">Stop ⏹️</button>
                </div>
            </div>

            <script>
                const vscode = acquireVsCodeApi();

                // Override console methods to send to VS Code debug console
                const originalConsole = {
                    log: console.log,
                    error: console.error,
                    warn: console.warn,
                    debug: console.debug,
                    info: console.info
                };

                function sendDebugMessage(level, args) {
                    const message = Array.from(args).map(arg => {
                        if (typeof arg === 'object') {
                            return JSON.stringify(arg);
                        }
                        return String(arg);
                    }).join(' ');

                    vscode.postMessage({
                        type: 'debug',
                        level: level,
                        content: message
                    });

                    // Also call original console method for webview developer tools
                    originalConsole[level.toLowerCase()].apply(console, args);
                }

                console.log = function() { sendDebugMessage('LOG', arguments); };
                console.error = function() { sendDebugMessage('ERROR', arguments); };
                console.warn = function() { sendDebugMessage('WARN', arguments); };
                console.debug = function() { sendDebugMessage('DEBUG', arguments); };
                console.info = function() { sendDebugMessage('INFO', arguments); };

                console.log('Chat UI Script initializing...');
                const messagesDiv = document.getElementById('messages');
                const messageInput = document.getElementById('message-input');
                const sendButton = document.getElementById('send-button');
                const stopButton = document.getElementById('stop-button');
                const agentOptions = document.querySelectorAll('.agent-option');
                const newChatBtn = document.getElementById('new-chat-btn');
                const historyBtn = document.getElementById('history-btn');
                const thinkingBtn = document.getElementById('thinking-btn');
                const agentThinkingBtn = document.getElementById('agent-thinking-btn');
                const pauseBtn = document.getElementById('pause-btn');
                const planFirstBtn = document.getElementById('plan-first-btn');

                // Debug check
                console.log('Elements found:', {
                    messagesDiv: !!messagesDiv,
                    messageInput: !!messageInput,
                    sendButton: !!sendButton,
                    agentOptions: agentOptions.length
                });

                let selectedAgent = 'orchestrator';
                let thinkingMode = false;
                let isProcessing = false;
                let planFirstMode = false;

                // Load conversation history on startup
                setTimeout(() => {
                    console.log('Loading conversation history...');
                    vscode.postMessage({
                        type: 'loadHistory',
                        limit: 20
                    });
                }, 500); // Small delay to ensure webview is ready

                // Define addMessage function before it's used
                function addMessage(content, type, agent) {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'message ' + type + '-message';

                    // Add agent-specific class for styling
                    if (agent) {
                        const agentClass = agent.toLowerCase().replace(/[^a-z0-9]/g, '-');
                        messageDiv.classList.add(agentClass + '-bubble');
                        const badge = document.createElement('span');
                        badge.className = 'agent-badge';
                        badge.textContent = agent;
                        messageDiv.appendChild(badge);
                    }

                    const contentDiv = document.createElement('div');
                    contentDiv.innerHTML = formatContent(content);
                    messageDiv.appendChild(contentDiv);

                    messagesDiv.appendChild(messageDiv);
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                }

                // Agent selection
                agentOptions.forEach(option => {
                    option.addEventListener('click', () => {
                        agentOptions.forEach(opt => opt.classList.remove('selected'));
                        option.classList.add('selected');
                        selectedAgent = option.dataset.agent;

                        vscode.postMessage({
                            type: 'selectAgent',
                            agent: selectedAgent
                        });
                    });
                });

                // Send message
                function sendMessage() {
                    const content = messageInput.value.trim();
                    if (!content || isProcessing) {
                        console.log('No content to send or still processing');
                        return;
                    }

                    console.log('Sending message:', content, 'to agent:', selectedAgent);

                    // Set processing state
                    isProcessing = true;
                    updatePauseButtonState();
                    updateActivityIndicator(true, 'Sending message...');

                    // Show stop button, hide send button
                    if (stopButton) {
                        stopButton.style.display = 'inline-block';
                        sendButton.style.display = 'none';
                    }

                    // Disable inputs while processing
                    if (messageInput) messageInput.disabled = true;

                    vscode.postMessage({
                        type: 'chat',
                        content: content,
                        agent: selectedAgent,
                        mode: 'auto',
                        planFirst: planFirstMode
                    });

                    messageInput.value = '';
                    autoResizeTextarea();
                }

                // Bind send button
                if (sendButton) {
                    sendButton.addEventListener('click', (e) => {
                        e.preventDefault();
                        console.log('Send button clicked');
                        sendMessage();
                    });
                } else {
                    console.error('Send button not found!');
                }

                // Bind stop button
                if (stopButton) {
                    stopButton.addEventListener('click', (e) => {
                        e.preventDefault();
                        console.log('Stop button clicked');
                        vscode.postMessage({
                            type: 'stopAndRollback'
                        });
                        // Hide stop button, show send button
                        stopButton.style.display = 'none';
                        sendButton.style.display = 'inline-block';
                        // Re-enable inputs
                        if (messageInput) messageInput.disabled = false;
                        isProcessing = false;
                        updateActivityIndicator(false);
                    });
                }

                // Header button handlers
                newChatBtn.addEventListener('click', () => {
                    if (confirm('Start a new chat session? Current conversation will be saved.')) {
                        vscode.postMessage({ type: 'newChat' });
                        messagesDiv.innerHTML = '';
                    }
                });

                historyBtn.addEventListener('click', () => {
                    vscode.postMessage({ type: 'showHistory' });
                });

                thinkingBtn.addEventListener('click', () => {
                    thinkingMode = !thinkingMode;
                    thinkingBtn.classList.toggle('active', thinkingMode);
                    vscode.postMessage({
                        type: 'toggleThinking',
                        enabled: thinkingMode,
                        intensity: 'normal'
                    });
                });

                // Agent Thinking Button - zeigt interne Agent-Schritte
                let showAgentThinking = false;
                agentThinkingBtn.addEventListener('click', () => {
                    showAgentThinking = !showAgentThinking;
                    agentThinkingBtn.classList.toggle('active', showAgentThinking);
                    vscode.postMessage({
                        type: 'toggleAgentThinking',
                        enabled: showAgentThinking
                    });

                    // Update existing messages visibility
                    const thinkingMessages = document.querySelectorAll('.agent-thinking-message');
                    thinkingMessages.forEach(msg => {
                        msg.style.display = showAgentThinking ? 'block' : 'none';
                    });
                });

                // Function to update pause button state
                function updatePauseButtonState() {
                    if (pauseBtn) {
                        pauseBtn.disabled = !isProcessing || isPaused;
                        pauseBtn.style.opacity = (isProcessing && !isPaused) ? '1.0' : '0.5';
                        pauseBtn.style.cursor = (isProcessing && !isPaused) ? 'pointer' : 'not-allowed';
                    }
                }

                let isPaused = false;

                // Plan-First button handler
                if (planFirstBtn) {
                    planFirstBtn.addEventListener('click', () => {
                        planFirstMode = !planFirstMode;
                        planFirstBtn.classList.toggle('active', planFirstMode);

                        // Show notification
                        const mode = planFirstMode ? 'enabled' : 'disabled';
                        const modeMessage = planFirstMode
                            ? 'I will show you the execution plan before running tasks.'
                            : 'I will execute tasks immediately.';
                        addMessage('📋 Plan-First mode ' + mode + '. ' + modeMessage, 'system');

                        // Save preference
                        vscode.postMessage({
                            type: 'planFirstMode',
                            enabled: planFirstMode
                        });
                    });
                }

                pauseBtn.addEventListener('click', () => {
                    if (isProcessing && !isPaused) {
                        vscode.postMessage({ type: 'pause' });
                        isPaused = true;
                        showPauseUI();
                        updatePauseButtonState();
                    }
                });

                // Function to show pause UI with instruction input
                function showPauseUI() {
                    const pauseOverlay = document.createElement('div');
                    pauseOverlay.className = 'pause-overlay';
                    pauseOverlay.innerHTML = [
                        '<div class="pause-dialog">',
                        '<h3>⏸️ Task Paused</h3>',
                        '<p>Add additional instructions or stop the task:</p>',
                        '<textarea id="pause-instructions" placeholder="Enter additional instructions (optional)..." rows="4"></textarea>',
                        '<div class="pause-actions">',
                        '<button id="resume-btn" class="btn primary">▶️ Resume</button>',
                        '<button id="resume-with-instructions-btn" class="btn info">📝 Resume with Instructions</button>',
                        '<button id="stop-rollback-btn" class="btn danger">🔄 Stop & Rollback</button>',
                        '</div>',
                        '</div>'
                    ].join('');
                    document.body.appendChild(pauseOverlay);

                    // Handle pause dialog buttons
                    document.getElementById('resume-btn').addEventListener('click', () => {
                        vscode.postMessage({ type: 'resumeWithInstructions' });
                        document.body.removeChild(pauseOverlay);
                        isPaused = false;
                        updatePauseButtonState();
                    });

                    document.getElementById('resume-with-instructions-btn').addEventListener('click', () => {
                        const instructions = document.getElementById('pause-instructions').value;
                        if (instructions.trim()) {
                            vscode.postMessage({
                                type: 'resumeWithInstructions',
                                instructions: instructions
                            });
                            document.body.removeChild(pauseOverlay);
                            isPaused = false;
                            updatePauseButtonState();
                        } else {
                            alert('Please enter instructions or click Resume to continue without changes');
                        }
                    });

                    document.getElementById('stop-rollback-btn').addEventListener('click', () => {
                        if (confirm('Are you sure you want to stop and rollback to the last checkpoint?')) {
                            vscode.postMessage({ type: 'stopAndRollback' });
                            document.body.removeChild(pauseOverlay);
                            isPaused = false;
                            isProcessing = false;
                            updatePauseButtonState();
                        }
                    });
                }

                // Create activity indicator
                const activityIndicator = document.createElement('div');
                activityIndicator.className = 'activity-indicator';

                const spinner = document.createElement('div');
                spinner.className = 'spinner';

                const text = document.createElement('div');
                text.className = 'text';
                text.textContent = 'Processing...';

                activityIndicator.appendChild(spinner);
                activityIndicator.appendChild(text);
                document.body.appendChild(activityIndicator);

                function updateActivityIndicator(active, text = 'Processing...') {
                    console.log('🔄 updateActivityIndicator called:', active, text);
                    if (active) {
                        activityIndicator.classList.add('active');
                        const textElement = activityIndicator.querySelector('.text');
                        if (textElement) {
                            textElement.textContent = text;
                        }
                        console.log('✅ Activity indicator made active with text:', text);
                    } else {
                        activityIndicator.classList.remove('active');
                        console.log('⏹️ Activity indicator hidden');
                    }
                }
                // Auto-resize textarea
                function autoResizeTextarea() {
                    messageInput.style.height = 'auto';
                    const newHeight = Math.min(messageInput.scrollHeight, 150);
                    messageInput.style.height = newHeight + 'px';
                }

                // Handle textarea input
                messageInput.addEventListener('input', autoResizeTextarea);

                // Handle Enter key (send) vs Shift+Enter (new line)
                messageInput.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage();
                    }
                });

                // Initialize textarea height
                autoResizeTextarea();

                // Handle messages from extension
                window.addEventListener('message', event => {
                    const message = event.data;

                    switch (message.type) {
                        case 'userMessage':
                            addMessage(message.content, 'user');
                            break;

                        case 'historyMessage':
                            // Display history message from persistent storage
                            if (message.isUser) {
                                addMessage(message.content, 'user');
                            } else {
                                addMessage(message.content, 'assistant', message.agent);
                            }
                            break;

                        case 'agentThinking':
                        case 'agent_thinking':  // LangGraph v5.0.0 sends 'agent_thinking' type
                            isProcessing = true;
                            updatePauseButtonState();
                            updateActivityIndicator(true, message.content || message.message || 'Processing...');
                            addThinkingMessage(message.agent || 'orchestrator', message.content || message.message);
                            break;

                        case 'progress':
                            console.log('📊 Progress message received:', message.agent, message.content);
                            // Update existing progress message or create new one
                            updateProgressMessage(message.agent, message.content);
                            updateActivityIndicator(true, message.content || 'Processing...');
                            break;

                        case 'agentResponse':
                        case 'response':  // LangGraph v5.0.0 sends 'response' type
                            // Always reset processing state on response
                            isProcessing = false;
                            updatePauseButtonState();
                            updateActivityIndicator(false);
                            removeThinkingMessage();
                            removeProgressMessages();

                            // Handle content - check if it's present
                            if (message.content) {
                                addMessage(message.content, 'agent', message.agent || 'orchestrator');
                            } else {
                                console.warn('Response received without content:', message);
                            }

                            // Re-enable input and button
                            if (stopButton) {
                                stopButton.style.display = 'none';
                                sendButton.style.display = 'inline-block';
                            }
                            if (messageInput) messageInput.disabled = false;
                            break;

                        case 'complete':
                        case 'step_completed':  // LangGraph v5.0.0 sends 'step_completed' for intermediate steps
                            // For step_completed, don't reset processing state yet
                            if (message.type === 'step_completed' && message.result) {
                                // Show intermediate result
                                updateProgressMessage(message.agent || 'orchestrator', message.result);
                            } else {
                                // For 'complete', reset everything
                                isProcessing = false;
                                updatePauseButtonState();
                                updateActivityIndicator(false);
                                removeThinkingMessage();
                                removeProgressMessages();
                                if (stopButton) {
                                    stopButton.style.display = 'none';
                                    sendButton.style.display = 'inline-block';
                                }
                                if (messageInput) messageInput.disabled = false;
                            }
                            break;

                        case 'clearChat':
                            messagesDiv.innerHTML = '';
                            isProcessing = false;
                            updatePauseButtonState();
                            updateActivityIndicator(false);
                            if (stopButton) {
                                stopButton.style.display = 'none';
                                sendButton.style.display = 'inline-block';
                            }
                            if (messageInput) messageInput.disabled = false;
                            break;

                        case 'pauseActivated':
                            isPaused = true;
                            updatePauseButtonState();
                            break;

                        case 'resumed':
                            isPaused = false;
                            updatePauseButtonState();
                            break;

                        case 'stoppedAndRolledBack':
                            isProcessing = false;
                            isPaused = false;
                            updatePauseButtonState();
                            updateActivityIndicator(false);
                            removeThinkingMessage();
                            removeProgressMessages();
                            if (stopButton) {
                                stopButton.style.display = 'none';
                                sendButton.style.display = 'inline-block';
                            }
                            if (messageInput) messageInput.disabled = false;
                            break;

                        case 'architecture_proposal':
                        case 'architecture_proposal_revised':
                            // v5.2.0: Architecture Proposal System
                            console.log('📋 Architecture proposal received:', message);

                            // Remove any existing proposal cards
                            const existingProposal = document.querySelector('.architecture-proposal-card');
                            if (existingProposal) {
                                existingProposal.remove();
                            }

                            // Create and display proposal card
                            const proposalCard = createArchitectureProposalCard(
                                message.proposal,
                                message.session_id || '',
                                message.type === 'architecture_proposal_revised'
                            );
                            messagesDiv.appendChild(proposalCard);
                            messagesDiv.scrollTop = messagesDiv.scrollHeight;

                            // Disable input while waiting for decision
                            if (messageInput) messageInput.disabled = true;
                            if (sendButton) sendButton.style.display = 'none';
                            break;

                        case 'architectureApprovalProcessed':
                            // v5.2.0: Approval was processed
                            console.log('✅ Architecture approval processed:', message.decision);

                            // Remove proposal card
                            const proposalToRemove = document.querySelector('.architecture-proposal-card');
                            if (proposalToRemove) {
                                proposalToRemove.remove();
                            }

                            // Show confirmation message
                            addMessage(
                                \`Architecture proposal \${message.decision}. Continuing with implementation...\`,
                                'system',
                                'architect'
                            );

                            // Re-enable input
                            if (messageInput) messageInput.disabled = false;
                            if (sendButton) sendButton.style.display = 'inline-block';
                            break;

                        case 'agent_activity':
                            // v5.8.1: Agent Activity Visualization
                            showAgentActivity(message);
                            break;
                    }
                });

                function addThinkingMessage(agent, content) {
                    removeThinkingMessage();

                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'message agent-message agent-thinking';
                    messageDiv.id = 'thinking-message';

                    const badge = document.createElement('span');
                    badge.className = 'agent-badge';
                    badge.textContent = agent;
                    messageDiv.appendChild(badge);

                    const contentDiv = document.createElement('div');
                    contentDiv.innerHTML = formatContent(content || 'Thinking...');
                    messageDiv.appendChild(contentDiv);

                    messagesDiv.appendChild(messageDiv);
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                }

                function removeThinkingMessage() {
                    const thinkingMsg = document.getElementById('thinking-message');
                    if (thinkingMsg) {
                        thinkingMsg.remove();
                    }
                }

                // Map to track progress messages by agent
                const progressMessages = new Map();

                function updateProgressMessage(agent, content) {
                    let progressDiv = progressMessages.get(agent);

                    if (!progressDiv) {
                        // Create new progress message
                        progressDiv = document.createElement('div');
                        progressDiv.className = 'message system-message progress-update';
                        progressDiv.id = 'progress-' + agent.replace(/[^a-z0-9]/gi, '-');

                        const badge = document.createElement('span');
                        badge.className = 'agent-badge';
                        badge.textContent = agent + ' Progress';
                        progressDiv.appendChild(badge);

                        const contentDiv = document.createElement('div');
                        contentDiv.className = 'progress-content';
                        progressDiv.appendChild(contentDiv);

                        messagesDiv.appendChild(progressDiv);
                        progressMessages.set(agent, progressDiv);
                    }

                    // Update content
                    const contentDiv = progressDiv.querySelector('.progress-content');
                    if (contentDiv) {
                        contentDiv.innerHTML = formatContent(content);
                    }

                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                }

                function removeProgressMessages() {
                    progressMessages.forEach((div, agent) => {
                        if (div.parentNode) {
                            div.parentNode.removeChild(div);
                        }
                    });
                    progressMessages.clear();
                }

                // ============================================================================
                // v5.8.1: Agent Activity Visualization
                // ============================================================================

                const agentActivityMap = new Map();  // agent -> activity div

                function showAgentActivity(message) {
                    const {activity_type, agent, content, tool, tool_status, tool_result} = message;

                    // Get or create agent activity container
                    let activityDiv = agentActivityMap.get(agent);

                    if (!activityDiv) {
                        activityDiv = document.createElement('div');
                        activityDiv.className = \`agent-activity \${agent}-activity\`;
                        activityDiv.innerHTML = \`
                            <div class="activity-header">
                                <span class="agent-badge">\${agent}</span>
                            </div>
                            <div class="activity-content"></div>
                        \`;
                        messagesDiv.appendChild(activityDiv);
                        agentActivityMap.set(agent, activityDiv);
                    }

                    const activityContent = activityDiv.querySelector('.activity-content');

                    if (activity_type === 'agent_thinking') {
                        activityContent.innerHTML = \`<div class="activity-item thinking">💭 \${content}</div>\`;
                    } else if (activity_type === 'agent_progress') {
                        const progressItem = document.createElement('div');
                        progressItem.className = 'activity-item progress';
                        progressItem.innerHTML = \`📊 \${content}\`;
                        activityContent.appendChild(progressItem);
                    } else if (activity_type === 'agent_tool_start') {
                        const toolItem = document.createElement('div');
                        toolItem.className = 'activity-item tool-running';
                        toolItem.id = \`tool-\${agent}-\${tool}\`;
                        toolItem.innerHTML = \`🔧 \${tool}() → ⏳ Running...\`;
                        activityContent.appendChild(toolItem);
                    } else if (activity_type === 'agent_tool_complete') {
                        const toolItem = document.getElementById(\`tool-\${agent}-\${tool}\`);
                        if (toolItem) {
                            const icon = tool_status === 'success' ? '✅' : '❌';
                            toolItem.className = \`activity-item tool-\${tool_status}\`;
                            toolItem.innerHTML = \`🔧 \${tool}() → \${icon} \${tool_status}\`;
                        }
                    } else if (activity_type === 'agent_complete') {
                        const completeItem = document.createElement('div');
                        completeItem.className = 'activity-item complete';
                        completeItem.innerHTML = \`✅ \${content || 'Completed'}\`;
                        activityContent.appendChild(completeItem);

                        // Remove activity div after 2 seconds
                        setTimeout(() => {
                            if (activityDiv.parentNode) {
                                activityDiv.style.opacity = '0';
                                setTimeout(() => {
                                    if (activityDiv.parentNode) activityDiv.parentNode.removeChild(activityDiv);
                                    agentActivityMap.delete(agent);
                                }, 300);
                            }
                        }, 2000);
                    }

                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                }

                // ============================================================================
                // v5.2.0: Architecture Proposal Card
                // ============================================================================

                function createArchitectureProposalCard(proposal, sessionId, isRevised) {
                    const card = document.createElement('div');
                    card.className = 'architecture-proposal-card message';
                    card.style.cssText = \`
                        background: var(--vscode-editor-background);
                        border: 2px solid var(--vscode-focusBorder);
                        border-radius: 8px;
                        padding: 20px;
                        margin: 16px 0;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                    \`;

                    // Header
                    const header = document.createElement('div');
                    header.style.cssText = 'border-bottom: 1px solid var(--vscode-panel-border); padding-bottom: 12px; margin-bottom: 16px;';
                    header.innerHTML = \`
                        <h2 style="margin: 0; color: var(--vscode-foreground); font-size: 20px;">
                            🏛️ Architecture Proposal \${isRevised ? '(Revised)' : ''}
                        </h2>
                        <p style="margin: 8px 0 0 0; color: var(--vscode-descriptionForeground); font-size: 13px;">
                            Please review the proposed architecture and provide your decision
                        </p>
                    \`;
                    card.appendChild(header);

                    // Content sections
                    const sections = [
                        { title: '📊 Summary', content: proposal.summary, expanded: true },
                        { title: '✨ Suggested Improvements', content: proposal.improvements, expanded: true },
                        { title: '🛠️ Tech Stack', content: proposal.tech_stack, expanded: false },
                        { title: '📁 Project Structure', content: proposal.structure, expanded: false },
                        { title: '⚠️ Risks & Mitigations', content: proposal.risks, expanded: false },
                        { title: '🔍 Research Insights', content: proposal.research_insights, expanded: false }
                    ];

                    sections.forEach((section, index) => {
                        const sectionDiv = document.createElement('div');
                        sectionDiv.style.cssText = 'margin-bottom: 16px;';

                        const sectionHeader = document.createElement('div');
                        sectionHeader.style.cssText = \`
                            cursor: pointer;
                            padding: 8px;
                            background: var(--vscode-list-hoverBackground);
                            border-radius: 4px;
                            font-weight: 600;
                            display: flex;
                            align-items: center;
                            justify-content: space-between;
                        \`;

                        const titleSpan = document.createElement('span');
                        titleSpan.textContent = section.title;
                        sectionHeader.appendChild(titleSpan);

                        const toggleIcon = document.createElement('span');
                        toggleIcon.textContent = section.expanded ? '▼' : '▶';
                        toggleIcon.style.cssText = 'font-size: 10px;';
                        sectionHeader.appendChild(toggleIcon);

                        const sectionContent = document.createElement('div');
                        sectionContent.style.cssText = \`
                            padding: 12px;
                            margin-top: 8px;
                            background: var(--vscode-editor-background);
                            border-left: 3px solid var(--vscode-focusBorder);
                            border-radius: 0 4px 4px 0;
                            white-space: pre-wrap;
                            display: \${section.expanded ? 'block' : 'none'};
                        \`;
                        sectionContent.innerHTML = formatContent(section.content || 'No information provided');

                        sectionHeader.onclick = () => {
                            const isExpanded = sectionContent.style.display !== 'none';
                            sectionContent.style.display = isExpanded ? 'none' : 'block';
                            toggleIcon.textContent = isExpanded ? '▶' : '▼';
                        };

                        sectionDiv.appendChild(sectionHeader);
                        sectionDiv.appendChild(sectionContent);
                        card.appendChild(sectionDiv);
                    });

                    // Feedback textarea (initially hidden)
                    const feedbackSection = document.createElement('div');
                    feedbackSection.style.cssText = 'margin: 16px 0; display: none;';
                    feedbackSection.id = 'feedback-section';

                    const feedbackLabel = document.createElement('label');
                    feedbackLabel.textContent = 'Your feedback or requested changes:';
                    feedbackLabel.style.cssText = 'display: block; margin-bottom: 8px; font-weight: 500;';

                    const feedbackTextarea = document.createElement('textarea');
                    feedbackTextarea.id = 'proposal-feedback';
                    feedbackTextarea.placeholder = 'Describe what you would like to change...';
                    feedbackTextarea.style.cssText = \`
                        width: 100%;
                        min-height: 80px;
                        padding: 8px;
                        background: var(--vscode-input-background);
                        color: var(--vscode-input-foreground);
                        border: 1px solid var(--vscode-input-border);
                        border-radius: 4px;
                        font-family: var(--vscode-font-family);
                        resize: vertical;
                    \`;

                    feedbackSection.appendChild(feedbackLabel);
                    feedbackSection.appendChild(feedbackTextarea);
                    card.appendChild(feedbackSection);

                    // Action buttons
                    const buttonContainer = document.createElement('div');
                    buttonContainer.style.cssText = 'display: flex; gap: 12px; margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--vscode-panel-border);';

                    const approveBtn = createProposalButton('✅ Approve', '#28a745', () => {
                        sendArchitectureApproval(sessionId, 'approved', '');
                        card.style.opacity = '0.6';
                        card.style.pointerEvents = 'none';
                    });

                    const modifyBtn = createProposalButton('✏️ Modify', '#ffc107', () => {
                        const feedbackSection = card.querySelector('#feedback-section');
                        if (feedbackSection.style.display === 'none') {
                            feedbackSection.style.display = 'block';
                            modifyBtn.textContent = '📤 Submit Changes';
                        } else {
                            const feedback = feedbackTextarea.value.trim();
                            if (!feedback) {
                                vscode.postMessage({
                                    command: 'showError',
                                    message: 'Please provide feedback for modifications'
                                });
                                return;
                            }
                            sendArchitectureApproval(sessionId, 'modified', feedback);
                            card.style.opacity = '0.6';
                            card.style.pointerEvents = 'none';
                        }
                    });

                    const rejectBtn = createProposalButton('❌ Reject', '#dc3545', () => {
                        if (confirm('Are you sure you want to reject this architecture proposal?')) {
                            sendArchitectureApproval(sessionId, 'rejected', '');
                            card.style.opacity = '0.6';
                            card.style.pointerEvents = 'none';
                        }
                    });

                    buttonContainer.appendChild(approveBtn);
                    buttonContainer.appendChild(modifyBtn);
                    buttonContainer.appendChild(rejectBtn);
                    card.appendChild(buttonContainer);

                    return card;
                }

                function createProposalButton(text, color, onClick) {
                    const btn = document.createElement('button');
                    btn.textContent = text;
                    btn.style.cssText = \`
                        flex: 1;
                        padding: 10px 20px;
                        background: \${color};
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: opacity 0.2s;
                    \`;
                    btn.onmouseover = () => btn.style.opacity = '0.8';
                    btn.onmouseout = () => btn.style.opacity = '1';
                    btn.onclick = onClick;
                    return btn;
                }

                function sendArchitectureApproval(sessionId, decision, feedback) {
                    console.log(\`📤 Sending architecture approval: \${decision}\`, { sessionId, feedback });
                    vscode.postMessage({
                        type: 'architecture_approval',
                        session_id: sessionId,
                        decision: decision,
                        feedback: feedback
                    });
                }

                // ============================================================================
                // End of v5.2.0 Architecture Proposal Card
                // ============================================================================

                // Initialization overlay functions
                function showInitializationOverlay() {
                    if (document.getElementById('initialization-overlay')) return;

                    const overlay = document.createElement('div');
                    overlay.id = 'initialization-overlay';
                    overlay.className = 'initialization-overlay';
                    overlay.innerHTML = [
                        '<div class="initialization-content">',
                        '    <div class="spinner"></div>',
                        '    <h2>🚀 Initializing System</h2>',
                        '    <p id="init-status">Preparing KI AutoAgent...</p>',
                        '    <div id="init-progress" class="progress-bar">',
                        '        <div class="progress-fill"></div>',
                        '    </div>',
                        '</div>'
                    ].join('');
                    document.body.appendChild(overlay);
                }

                function hideInitializationOverlay() {
                    const overlay = document.getElementById('initialization-overlay');
                    if (overlay) {
                        overlay.classList.add('fade-out');
                        setTimeout(() => overlay.remove(), 300);
                    }
                    isInitializing = false;
                }

                function updateInitStatus(status) {
                    const statusEl = document.getElementById('init-status');
                    if (statusEl) {
                        statusEl.textContent = status;
                    }
                }

                function formatContent(content) {
                    // Enhanced markdown and formatting support
                    if (!content) return '';

                    // First escape HTML for security
                    const escapeMap = {
                        '&': '&amp;',
                        '<': '&lt;',
                        '>': '&gt;',
                        '"': '&quot;',
                        "'": '&#039;'
                    };

                    let escaped = '';
                    for (let i = 0; i < content.length; i++) {
                        const char = content[i];
                        escaped += escapeMap[char] || char;
                    }

                    // Convert markdown-style formatting
                    // Headers
                    escaped = escaped.replace(/^### (.+)$/gm, '<h3>$1</h3>');
                    escaped = escaped.replace(/^## (.+)$/gm, '<h2>$1</h2>');
                    escaped = escaped.replace(/^# (.+)$/gm, '<h1>$1</h1>');

                    // Bold and Italic
                    escaped = escaped.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>');
                    escaped = escaped.replace(/\\*(.+?)\\*/g, '<em>$1</em>');

                    // Code blocks - match triple backticks
                    const codeBlockStart = escaped.indexOf('&lt;code&gt;&lt;code&gt;&lt;code&gt;');
                    if (codeBlockStart !== -1) {
                        const codeBlockEnd = escaped.indexOf('&lt;code&gt;&lt;code&gt;&lt;code&gt;', codeBlockStart + 1);
                        if (codeBlockEnd !== -1) {
                            const before = escaped.substring(0, codeBlockStart);
                            const code = escaped.substring(codeBlockStart + 39, codeBlockEnd);
                            const after = escaped.substring(codeBlockEnd + 39);
                            escaped = before + '&lt;pre&gt;&lt;code&gt;' + code + '&lt;/code&gt;&lt;/pre&gt;' + after;
                        }
                    }

                    // Inline code - match single backticks
                    escaped = escaped.replace(/&lt;code&gt;([^&]+)&lt;code&gt;/g, '&lt;code&gt;$1&lt;/code&gt;');

                    // Lists
                    escaped = escaped.replace(/^\\* (.+)$/gm, '<li>$1</li>');
                    escaped = escaped.replace(/^- (.+)$/gm, '<li>$1</li>');
                    escaped = escaped.replace(/^\\d+\\. (.+)$/gm, '<li>$1</li>');

                    // Wrap consecutive li elements in ul
                    escaped = escaped.replace(/(<li>.+<\\/li>\\s*)+/g, function(match) {
                        return '<ul>' + match + '</ul>';
                    });

                    // Line breaks
                    escaped = escaped.split('\\n\\n').join('</p><p>');
                    escaped = escaped.split('\\n').join('<br>');

                    // Wrap in paragraph if not already wrapped
                    if (!escaped.startsWith('<')) {
                        escaped = '<p>' + escaped + '</p>';
                    }

                    return escaped;
                }
            </script>
        </body>
        </html>`;
    }

    public dispose() {
        MultiAgentChatPanel.currentPanel = undefined;
        this._isDisposed = true;

        // Clean up BackendClient event listeners to prevent "Webview is disposed" errors
        if (this.backendClient) {
            this.backendClient.removeAllListeners('response');
            this.backendClient.removeAllListeners('thinking');
            this.backendClient.removeAllListeners('progress');
            this.backendClient.removeAllListeners('complete');
            this.backendClient.removeAllListeners('error');
            this.backendClient.removeAllListeners('welcome');
            this.backendClient.removeAllListeners('stream_chunk');
            MultiAgentChatPanel.debugChannel.appendLine('✅ Cleaned up BackendClient event listeners');
        }

        this._panel.dispose();

        while (this._disposables.length) {
            const disposable = this._disposables.pop();
            if (disposable) {
                disposable.dispose();
            }
        }
    }
}