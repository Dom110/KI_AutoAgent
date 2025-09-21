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
            this.sendMessage({
                type: 'agentResponse',
                agent: message.agent,
                content: message.content,
                timestamp: message.timestamp
            });
        });

        this.backendClient.on('thinking', (message: BackendMessage) => {
            this.sendMessage({
                type: 'agentThinking',
                agent: message.agent,
                content: message.content
            });
        });

        this.backendClient.on('complete', (message: BackendMessage) => {
            this.sendMessage({
                type: 'complete',
                agent: message.agent,
                metadata: message.metadata
            });
        });
    }

    private async handleChatMessage(message: any) {
        // Send user message to webview
        this.sendMessage({
            type: 'userMessage',
            content: message.content
        });

        // Send to backend
        await this.backendClient.sendChatMessage({
            prompt: message.content,
            agent: message.agent || 'orchestrator',
            mode: message.mode || 'auto',
            thinkingMode: message.thinkingMode || false
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
            </style>
        </head>
        <body>
            <div id="header">
                <span style="font-size: 1.5em;">🤖</span>
                <h2 style="margin: 0;">KI AutoAgent Chat</h2>
                <span style="margin-left: auto; opacity: 0.7;">
                    Connected to Python Backend
                </span>
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
                    <button id="send-button">Send</button>
                </div>
            </div>

            <script>
                const vscode = acquireVsCodeApi();
                const messagesDiv = document.getElementById('messages');
                const messageInput = document.getElementById('message-input');
                const sendButton = document.getElementById('send-button');
                const agentOptions = document.querySelectorAll('.agent-option');

                let selectedAgent = 'orchestrator';

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
                    if (!content) return;

                    vscode.postMessage({
                        type: 'chat',
                        content: content,
                        agent: selectedAgent,
                        mode: 'auto'
                    });

                    messageInput.value = '';
                }

                sendButton.addEventListener('click', sendMessage);
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

                        case 'agentThinking':
                            addThinkingMessage(message.agent, message.content);
                            break;

                        case 'agentResponse':
                            removeThinkingMessage();
                            addMessage(message.content, 'agent', message.agent);
                            break;

                        case 'complete':
                            removeThinkingMessage();
                            break;
                    }
                });

                function addMessage(content, type, agent) {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'message ' + type + '-message';

                    if (agent) {
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
                    contentDiv.textContent = content || 'Thinking...';
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

                function formatContent(content) {
                    // Basic markdown formatting
                    return content
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        .replace(/\*(.*?)\*/g, '<em>$1</em>')
                        .replace(/\n/g, '<br>')
                        .replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>');
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