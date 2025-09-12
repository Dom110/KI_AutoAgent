/**
 * MultiAgentChatPanel - Main chat interface for KI AutoAgent
 * Provides a webview-based chat interface with agent selection and mode switching
 */
import * as vscode from 'vscode';
import * as path from 'path';

interface ChatMessage {
    role: 'user' | 'assistant' | 'system' | 'agent-to-agent';
    content: string;
    agent?: string;
    timestamp: string;
    isCollapsible?: boolean;
}

export class MultiAgentChatPanel {
    public static currentPanel: MultiAgentChatPanel | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionUri: vscode.Uri;
    private _disposables: vscode.Disposable[] = [];
    private _messages: ChatMessage[] = [];
    private _currentAgent: string = 'orchestrator';
    private _currentMode: 'single' | 'auto' | 'workflow' = 'auto';
    private _dispatcher: any; // Will be set from extension

    // Singleton pattern für Panel
    public static createOrShow(extensionUri: vscode.Uri, dispatcher?: any) {
        const column = vscode.ViewColumn.Two;
        
        if (MultiAgentChatPanel.currentPanel) {
            MultiAgentChatPanel.currentPanel._panel.reveal(column);
            if (dispatcher) {
                MultiAgentChatPanel.currentPanel._dispatcher = dispatcher;
            }
            return MultiAgentChatPanel.currentPanel;
        }

        const panel = vscode.window.createWebviewPanel(
            'multiAgentChat',
            'KI AutoAgent Chat',
            column,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [
                    vscode.Uri.joinPath(extensionUri, 'media'),
                    vscode.Uri.joinPath(extensionUri, 'src', 'ui', 'webview')
                ]
            }
        );

        MultiAgentChatPanel.currentPanel = new MultiAgentChatPanel(panel, extensionUri, dispatcher);
        return MultiAgentChatPanel.currentPanel;
    }

    private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri, dispatcher?: any) {
        this._panel = panel;
        this._extensionUri = extensionUri;
        this._dispatcher = dispatcher;
        
        // Set the webview's initial html content
        this._update();
        
        // Listen for when the panel is disposed
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        
        // Handle messages from the webview
        this._panel.webview.onDidReceiveMessage(
            message => this._handleWebviewMessage(message),
            null,
            this._disposables
        );

        // Update the content based on view changes
        this._panel.onDidChangeViewState(
            e => {
                if (this._panel.visible) {
                    this._update();
                }
            },
            null,
            this._disposables
        );
    }

    private _update() {
        const webview = this._panel.webview;
        this._panel.title = "KI AutoAgent Chat";
        this._panel.iconPath = vscode.Uri.joinPath(this._extensionUri, 'media', 'multi-agent-logo.svg');
        this._panel.webview.html = this._getHtmlForWebview(webview);
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        // Local path to css styles
        const styleResetUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this._extensionUri, 'media', 'reset.css')
        );
        const styleVSCodeUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this._extensionUri, 'media', 'vscode.css')
        );
        // Add cache buster to force reload
        const cacheBuster = Date.now();
        const styleChatUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this._extensionUri, 'src', 'ui', 'webview', 'chat-fixed.css')
        ) + `?v=${cacheBuster}`;
        const scriptUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this._extensionUri, 'src', 'ui', 'webview', 'chat.js')
        );

        // Use a nonce to only allow specific scripts to be run
        const nonce = getNonce();

        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="${styleResetUri}" rel="stylesheet">
                <link href="${styleVSCodeUri}" rel="stylesheet">
                <link href="${styleChatUri}" rel="stylesheet">
                <title>KI AutoAgent Chat</title>
            </head>
            <body>
                <div id="chat-container">
                    <!-- Minimalist Header -->
                    <div id="chat-header">
                        <h3>KI AutoAgent Chat</h3>
                        <button id="settings-btn" title="Settings">⚙️</button>
                    </div>
                    
                    <!-- Messages Container -->
                    <div id="messages-container">
                        <div class="welcome-message">
                            <h2>Welcome to KI AutoAgent</h2>
                            <p>Start a conversation with our AI agents</p>
                        </div>
                    </div>
                    
                    <!-- Input Section with Bottom Controls -->
                    <div id="input-section">
                        <textarea id="message-input" 
                                  placeholder="Message KI AutoAgent..."
                                  rows="3"></textarea>
                        
                        <div id="bottom-controls">
                            <div id="mode-selector">
                                <button class="mode-option active" data-agent="auto" title="Automatic agent selection">
                                    🤖 Auto
                                </button>
                                <button class="mode-option" data-agent="architect" title="System architecture & design">
                                    🏗️ Architect
                                </button>
                                <button class="mode-option" data-agent="codesmith" title="Code implementation">
                                    💻 CodeSmith
                                </button>
                                <button class="mode-option" data-agent="tradestrat" title="Trading strategies">
                                    📈 TradeStrat
                                </button>
                                <button class="mode-option" data-agent="research" title="Web research">
                                    🔍 Research
                                </button>
                                <button class="mode-option" data-agent="opus" title="Conflict resolution">
                                    ⚖️ Opus
                                </button>
                            </div>
                            
                            <button id="send-btn" title="Send message">
                                Send
                            </button>
                        </div>
                    </div>
                </div>
                <script nonce="${nonce}" src="${scriptUri}"></script>
            </body>
            </html>`;
    }

    private async _handleWebviewMessage(message: any) {
        switch (message.command) {
            case 'sendMessage':
                await this._processUserMessage(message.text, message.agent, message.mode);
                break;
            case 'changeAgent':
                this._currentAgent = message.agent;
                vscode.window.showInformationMessage(`Switched to ${message.agent}`);
                break;
            case 'changeMode':
                this._currentMode = message.mode;
                vscode.window.showInformationMessage(`Mode changed to ${message.mode}`);
                break;
            case 'clearChat':
                this._messages = [];
                break;
            case 'quickAction':
                await this._handleQuickAction(message.action);
                break;
        }
    }

    private async _processUserMessage(text: string, agent: string, mode: string) {
        // Add user message
        const userMessage: ChatMessage = {
            role: 'user',
            content: text,
            timestamp: new Date().toISOString()
        };
        this._messages.push(userMessage);
        
        this._panel.webview.postMessage({
            type: 'addMessage',
            message: userMessage
        });

        // Show typing indicator
        this._panel.webview.postMessage({
            type: 'showTyping',
            agent: agent
        });

        try {
            // Process based on mode
            if (mode === 'auto' && this._dispatcher) {
                // Use orchestrator for automatic routing
                const response = await this._callAgent('orchestrator', text);
                this._addAgentResponse(response, 'orchestrator');
            } else if (mode === 'single') {
                // Direct chat with selected agent
                const response = await this._callAgent(agent, text);
                this._addAgentResponse(response, agent);
            } else if (mode === 'workflow') {
                // Multi-agent workflow - show inter-agent communication
                await this._processWorkflow(text);
            }
        } catch (error) {
            this._addErrorMessage(`Error: ${(error as any).message}`);
        } finally {
            this._panel.webview.postMessage({
                type: 'hideTyping'
            });
        }
    }

    private async _callAgent(agentId: string, prompt: string): Promise<string> {
        if (!this._dispatcher) {
            return 'Error: No dispatcher available. Please check agent configuration.';
        }

        try {
            // Create task request for the dispatcher
            const taskRequest = {
                prompt: prompt,
                command: agentId, // Use agent ID as command
                context: await this._getWorkspaceContext()
            };

            // Call the real dispatcher
            const result = await this._dispatcher.processRequest(taskRequest);
            
            if (result.status === 'success' || result.status === 'partial_success') {
                return result.content;
            } else {
                return `Error: ${result.content}`;
            }
        } catch (error) {
            return `Agent Error: ${(error as any).message}`;
        }
    }

    private async _getWorkspaceContext() {
        return {
            activeEditor: vscode.window.activeTextEditor,
            workspaceRoots: vscode.workspace.workspaceFolders,
            openDocuments: vscode.workspace.textDocuments,
            selectedText: vscode.window.activeTextEditor?.document.getText(vscode.window.activeTextEditor.selection),
            currentFile: vscode.window.activeTextEditor?.document.fileName
        };
    }

    private async _processWorkflow(prompt: string) {
        // Simulate a multi-agent workflow
        const workflow = [
            { agent: 'orchestrator', action: 'Analyzing request...' },
            { agent: 'architect', action: 'Designing solution architecture...' },
            { agent: 'codesmith', action: 'Implementing code...' },
            { agent: 'reviewer', action: 'Reviewing implementation...' }
        ];

        for (const step of workflow) {
            // Show agent-to-agent communication
            const agentMessage: ChatMessage = {
                role: 'agent-to-agent',
                content: step.action,
                agent: step.agent,
                timestamp: new Date().toISOString(),
                isCollapsible: true
            };
            this._messages.push(agentMessage);
            
            this._panel.webview.postMessage({
                type: 'addMessage',
                message: agentMessage
            });

            await new Promise(resolve => setTimeout(resolve, 500));
        }

        // Final response
        this._addAgentResponse('Workflow completed successfully!', 'orchestrator');
    }

    private _addAgentResponse(content: string, agent: string) {
        const assistantMessage: ChatMessage = {
            role: 'assistant',
            content: content,
            agent: agent,
            timestamp: new Date().toISOString(),
            isCollapsible: content.length > 500
        };
        this._messages.push(assistantMessage);
        
        this._panel.webview.postMessage({
            type: 'addMessage',
            message: assistantMessage
        });
    }

    private _addErrorMessage(content: string) {
        const errorMessage: ChatMessage = {
            role: 'system',
            content: content,
            timestamp: new Date().toISOString()
        };
        this._messages.push(errorMessage);
        
        this._panel.webview.postMessage({
            type: 'addMessage',
            message: errorMessage
        });
    }

    private async _handleQuickAction(action: string) {
        switch (action) {
            case 'help':
                this._addAgentResponse(
                    `## KI AutoAgent Help\n\n` +
                    `**Modes:**\n` +
                    `- **Auto**: Automatically routes to the best agent\n` +
                    `- **Single**: Direct chat with selected agent\n` +
                    `- **Workflow**: Multi-agent collaboration\n\n` +
                    `**Commands:**\n` +
                    `- Type your question and press Enter\n` +
                    `- Use Shift+Enter for multiline input\n` +
                    `- Select agents from dropdown\n`,
                    'system'
                );
                break;
            case 'examples':
                this._addAgentResponse(
                    `## Example Prompts\n\n` +
                    `**Architecture:**\n` +
                    `"Design a microservices architecture for an e-commerce platform"\n\n` +
                    `**Coding:**\n` +
                    `"Implement a REST API with FastAPI and PostgreSQL"\n\n` +
                    `**Trading:**\n` +
                    `"Create a momentum trading strategy with risk management"\n\n` +
                    `**Research:**\n` +
                    `"Find the latest best practices for React performance optimization"\n`,
                    'system'
                );
                break;
            case 'agents':
                this._addAgentResponse(
                    `## Available Agents\n\n` +
                    `🤖 **Orchestrator**: Automatic task routing\n` +
                    `🏗️ **ArchitectGPT**: System design and architecture\n` +
                    `💻 **CodeSmithClaude**: Code implementation\n` +
                    `📈 **TradeStrat**: Trading strategies\n` +
                    `🔍 **ResearchBot**: Web research\n` +
                    `⚖️ **OpusRichter**: Quality judgment\n` +
                    `📝 **DocuBot**: Documentation\n` +
                    `👁️ **ReviewerGPT**: Code review\n` +
                    `🔧 **FixerBot**: Bug fixing\n`,
                    'system'
                );
                break;
        }
    }

    public addMessage(message: ChatMessage) {
        this._messages.push(message);
        this._panel.webview.postMessage({
            type: 'addMessage',
            message: message
        });
    }

    public dispose() {
        MultiAgentChatPanel.currentPanel = undefined;
        this._panel.dispose();
        while (this._disposables.length) {
            const x = this._disposables.pop();
            if (x) {
                x.dispose();
            }
        }
    }
}

function getNonce() {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}