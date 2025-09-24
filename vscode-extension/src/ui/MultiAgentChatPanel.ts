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
    private backendClient: BackendClient;

    // UI State
    private _thinkingMode: boolean = false;
    private _thinkingIntensity: 'quick' | 'normal' | 'deep' | 'layered' = 'normal';
    private _isProcessing: boolean = false;
    private _conversationHistory: any[] = [];
    private _streamBuffer: Map<string, string> = new Map();

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
        // Handle responses from backend
        this.backendClient.on('response', (message: BackendMessage) => {
            // Reset processing flag when we get a response
            this._isProcessing = false;

            // Clear stream buffer for this agent
            const agent = message.agent || 'orchestrator';
            this._streamBuffer.delete(agent);

            this.sendMessage({
                type: 'agentResponse',
                agent: agent,
                content: message.content,
                timestamp: message.timestamp
            });

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
            this.sendMessage({
                type: 'agentThinking',
                agent: message.agent,
                content: message.content
            });
        });

        this.backendClient.on('progress', (message: BackendMessage) => {
            // Handle streaming chunks
            const agent = message.agent || 'orchestrator';

            // Accumulate chunks in buffer
            if (!this._streamBuffer.has(agent)) {
                this._streamBuffer.set(agent, '');
            }

            if (message.content) {
                const current = this._streamBuffer.get(agent) || '';
                this._streamBuffer.set(agent, current + message.content);
            }

            // Send progress update to UI
            this.sendMessage({
                type: 'progress',
                agent: agent,
                content: this._streamBuffer.get(agent),
                isStreaming: true
            });
        });

        this.backendClient.on('complete', (message: BackendMessage) => {
            // Also reset here for safety
            this._isProcessing = false;
            this.sendMessage({
                type: 'complete',
                agent: message.agent,
                metadata: message.metadata
            });
        });
    }

    private async handleChatMessage(message: any) {
        if (this._isProcessing) {
            vscode.window.showWarningMessage('Please wait for the current operation to complete');
            return;
        }

        this._isProcessing = true;

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

        // Send to backend with thinking mode
        await this.backendClient.sendChatMessage({
            prompt: message.content,
            agent: message.agent || 'orchestrator',
            mode: message.mode || 'auto',
            thinkingMode: this._thinkingMode
        });
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

    private async handlePause() {
        // Send pause signal to backend
        if (this.backendClient) {
            await this.backendClient.sendMessage({
                type: 'pause'
            });
        }
        this.sendMessage({ type: 'pauseActivated' });
        vscode.window.showInformationMessage('Task paused. You can add instructions or stop.');
    }

    private async handleResumeWithInstructions(instructions?: string) {
        // Send resume signal with optional instructions
        if (this.backendClient) {
            await this.backendClient.sendMessage({
                type: 'resume',
                additionalInstructions: instructions
            });
        }
        this.sendMessage({ type: 'resumed' });
        vscode.window.showInformationMessage(instructions ?
            'Resuming with additional instructions' : 'Resuming task');
    }

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
            const response = await fetch(`http://localhost:8000/api/conversation/history?limit=${message.limit || 20}&project_path=${encodeURIComponent(projectPath)}`);

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
        this._panel.webview.postMessage(message);
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
                }

                #message-input {
                    flex: 1;
                    padding: 10px;
                    background: var(--vscode-input-background);
                    color: var(--vscode-input-foreground);
                    border: 1px solid var(--vscode-input-border);
                    border-radius: 4px;
                    font-size: 14px;
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
                    padding: 10px 15px;
                    background: var(--vscode-notifications-background);
                    border: 1px solid var(--vscode-notifications-border);
                    border-radius: 8px;
                    display: none;
                    align-items: center;
                    gap: 10px;
                    z-index: 1000;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
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
                    color: var(--vscode-foreground);
                    font-size: 13px;
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
                    <button id="pause-btn" class="header-btn warning" title="Pause Task">⏸️ Pause</button>
                    <span style="opacity: 0.7; font-size: 0.9em;">Backend ✅</span>
                </div>
            </div>

            <div id="messages"></div>

            <div id="input-container">
                <div id="agent-selector">
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
                    <input
                        type="text"
                        id="message-input"
                        placeholder="Type your message..."
                        autofocus
                    />
                    <button type="button" id="send-button">Send 📤</button>
                </div>
            </div>

            <script>
                console.log('Chat UI Script initializing...');

                const vscode = acquireVsCodeApi();
                const messagesDiv = document.getElementById('messages');
                const messageInput = document.getElementById('message-input');
                const sendButton = document.getElementById('send-button');
                const agentOptions = document.querySelectorAll('.agent-option');
                const newChatBtn = document.getElementById('new-chat-btn');
                const historyBtn = document.getElementById('history-btn');
                const thinkingBtn = document.getElementById('thinking-btn');
                const pauseBtn = document.getElementById('pause-btn');

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

                // Load conversation history on startup
                setTimeout(() => {
                    console.log('Loading conversation history...');
                    vscode.postMessage({
                        type: 'loadHistory',
                        limit: 20
                    });
                }, 500); // Small delay to ensure webview is ready

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

                    // Disable inputs while processing
                    if (sendButton) sendButton.disabled = true;
                    if (messageInput) messageInput.disabled = true;

                    vscode.postMessage({
                        type: 'chat',
                        content: content,
                        agent: selectedAgent,
                        mode: 'auto'
                    });

                    messageInput.value = '';
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

                // Function to update pause button state
                function updatePauseButtonState() {
                    if (pauseBtn) {
                        pauseBtn.disabled = !isProcessing || isPaused;
                        pauseBtn.style.opacity = (isProcessing && !isPaused) ? '1.0' : '0.5';
                        pauseBtn.style.cursor = (isProcessing && !isPaused) ? 'pointer' : 'not-allowed';
                    }
                }

                let isPaused = false;

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
                    if (active) {
                        activityIndicator.classList.add('active');
                        activityIndicator.querySelector('.text').textContent = text;
                    } else {
                        activityIndicator.classList.remove('active');
                    }
                }
                messageInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage();
                    }
                });

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
                            isProcessing = true;
                            updatePauseButtonState();
                            updateActivityIndicator(true, message.content || 'Processing...');
                            addThinkingMessage(message.agent, message.content);
                            break;

                        case 'progress':
                            // Update existing progress message or create new one
                            updateProgressMessage(message.agent, message.content);
                            updateActivityIndicator(true, message.content || 'Processing...');
                            break;

                        case 'agentResponse':
                            // Always reset processing state on response
                            isProcessing = false;
                            updatePauseButtonState();
                            updateActivityIndicator(false);
                            removeThinkingMessage();
                            removeProgressMessages();
                            addMessage(message.content, 'agent', message.agent);
                            // Re-enable input and button
                            if (sendButton) sendButton.disabled = false;
                            if (messageInput) messageInput.disabled = false;
                            break;

                        case 'complete':
                            // Double-check processing state is reset
                            isProcessing = false;
                            updatePauseButtonState();
                            updateActivityIndicator(false);
                            removeThinkingMessage();
                            removeProgressMessages();
                            if (sendButton) sendButton.disabled = false;
                            if (messageInput) messageInput.disabled = false;
                            break;

                        case 'clearChat':
                            messagesDiv.innerHTML = '';
                            isProcessing = false;
                            updatePauseButtonState();
                            updateActivityIndicator(false);
                            if (sendButton) sendButton.disabled = false;
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
                            if (sendButton) sendButton.disabled = false;
                            if (messageInput) messageInput.disabled = false;
                            break;
                    }
                });

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

        this._panel.dispose();

        while (this._disposables.length) {
            const disposable = this._disposables.pop();
            if (disposable) {
                disposable.dispose();
            }
        }
    }
}