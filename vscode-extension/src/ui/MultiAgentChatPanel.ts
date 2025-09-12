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
        const styleChatUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this._extensionUri, 'src', 'ui', 'webview', 'chat.css')
        );
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
                    <!-- Header with Agent Selector -->
                    <div id="chat-header">
                        <div id="agent-selector">
                            <label for="agent-dropdown">Agent:</label>
                            <select id="agent-dropdown">
                                <option value="orchestrator">🤖 Auto (Orchestrator)</option>
                                <option value="architect">🏗️ ArchitectGPT</option>
                                <option value="codesmith">💻 CodeSmithClaude</option>
                                <option value="tradestrat">📈 TradeStrat</option>
                                <option value="research">🔍 ResearchBot</option>
                                <option value="richter">⚖️ OpusRichter</option>
                                <option value="docu">📝 DocuBot</option>
                                <option value="reviewer">👁️ ReviewerGPT</option>
                                <option value="fixer">🔧 FixerBot</option>
                            </select>
                        </div>
                        <div id="mode-toggles">
                            <button class="mode-btn active" data-mode="auto" title="Automatic agent selection">Auto</button>
                            <button class="mode-btn" data-mode="single" title="Chat with single agent">Single</button>
                            <button class="mode-btn" data-mode="workflow" title="Multi-agent workflow">Workflow</button>
                        </div>
                    </div>
                    
                    <!-- Messages Container -->
                    <div id="messages-container">
                        <div class="welcome-message">
                            <h2>👋 Welcome to KI AutoAgent Chat</h2>
                            <p>Select an agent above or use Auto mode for intelligent routing.</p>
                            <div class="quick-actions">
                                <button class="quick-action" data-action="help">📚 Help</button>
                                <button class="quick-action" data-action="examples">💡 Examples</button>
                                <button class="quick-action" data-action="agents">🤖 View Agents</button>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Input Area -->
                    <div id="input-area">
                        <textarea id="message-input" 
                                  placeholder="Ask anything... (Shift+Enter for new line, Enter to send)"
                                  rows="2"></textarea>
                        <div id="input-actions">
                            <button id="send-btn" title="Send message">
                                <span class="codicon codicon-send"></span>
                            </button>
                            <button id="clear-btn" title="Clear chat">
                                <span class="codicon codicon-clear-all"></span>
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
        // This will be integrated with the actual agents
        // For now, return a simulated response
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve(`[${agentId}] Response to: ${prompt}\n\nThis is a simulated response. The actual agent integration will be connected here.`);
            }, 1000);
        });
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
            content: `❌ ${content}`,
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