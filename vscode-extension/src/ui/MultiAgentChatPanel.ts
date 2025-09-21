/**
 * MultiAgentChatPanel - Main chat interface for KI AutoAgent
 * Provides a webview-based chat interface with agent selection and mode switching
 */
import * as vscode from 'vscode';
import * as path from 'path';
import { ConversationContextManager } from '../core/ConversationContextManager';
import { ConversationHistory, ConversationMessage } from '../core/ConversationHistory';

interface ChatMessage {
    role: 'user' | 'assistant' | 'system' | 'agent-to-agent';
    content: string;
    agent?: string;
    timestamp: string;
    isCollapsible?: boolean;
    metadata?: any;
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
    private _contextManager: ConversationContextManager;
    private workflowSteps: Map<string, any> = new Map(); // Track workflow steps
    private _thinkingMode: boolean = false; // Thinking mode state
    private _thinkingIntensity: 'quick' | 'normal' | 'deep' | 'layered' = 'normal'; // Thinking intensity
    private _currentOperation: any = null; // Current operation for cancellation
    private _isProcessing: boolean = false; // Track if processing
    private _conversationHistory: ConversationHistory | null = null; // Conversation history
    private _showReasoning: boolean = false; // Show agent reasoning
    private _attachedFiles: string[] = []; // Attached files for context
    private _isCompactMode: boolean = false; // Compact display mode

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
        this._contextManager = ConversationContextManager.getInstance();

        // Initialize conversation history if context available
        try {
            const context = (global as any).extensionContext;
            if (context) {
                this._conversationHistory = ConversationHistory.initialize(context);
                // Load existing messages from current session after webview is ready
                setTimeout(() => {
                    this._loadHistoryMessages();

                    // Check and apply compact mode setting
                    const config = vscode.workspace.getConfiguration('kiAutoAgent.ui');
                    this._isCompactMode = config.get<boolean>('compactMode', false);
                    if (this._isCompactMode) {
                        this._panel.webview.postMessage({
                            type: 'setCompactMode',
                            enabled: true
                        });
                    }
                }, 500);
            }
        } catch (error) {
            console.log('[Chat] Conversation history not available:', error);
        }
        
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

        // Restore messages when panel becomes visible
        this._panel.onDidChangeViewState(
            e => {
                if (this._panel.visible) {
                    // Don't reset the HTML, just restore messages
                    this._restoreMessages();
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
                        <!-- Action buttons above input -->
                        <div id="action-buttons">
                            <button id="new-chat-btn" class="action-btn" title="Start New Chat (Ctrl+N)">
                                ➕ New Chat
                            </button>
                            <button id="compact-btn" class="action-btn toggle" title="Toggle Compact View">
                                📦 Compact
                            </button>
                            <button id="history-btn" class="action-btn" title="Browse Conversation History">
                                📜 History
                            </button>
                            <button id="plan-first-btn" class="action-btn" title="Plan before implementing">
                                📋 Plan First
                            </button>
                            <button id="thinking-mode-btn" class="action-btn toggle" title="Enable thinking mode">
                                💭 Thinking
                            </button>
                            <select id="thinking-intensity" class="thinking-select" title="Select thinking intensity" style="display:none;">
                                <option value="quick">🧠 Quick</option>
                                <option value="normal" selected>🧠🧠 Normal</option>
                                <option value="deep">🧠🧠🧠 Deep</option>
                                <option value="layered">🧠➕🧠 Layered</option>
                            </select>
                            <button id="stop-btn" class="action-btn danger" title="Stop current operation">
                                ⏹ Stop
                            </button>
                        </div>
                        
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
                                <button class="mode-option" data-agent="docubot" title="Documentation">
                                    📝 DocuBot
                                </button>
                                <button class="mode-option" data-agent="reviewer" title="Code Review">
                                    🔍 Reviewer
                                </button>
                                <button class="mode-option" data-agent="fixer" title="Bug Fixing">
                                    🔧 Fixer
                                </button>
                            </div>

                            <div id="input-controls">
                                <button id="attach-btn" class="input-btn" title="Attach file">
                                    📎
                                </button>
                                <button id="send-btn" title="Send message">
                                    Send
                                </button>
                            </div>
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
            case 'planFirst':
                await this._handlePlanFirst(message.text, message.agent, message.mode);
                break;
            case 'stopOperation':
                this._cancelCurrentOperation();
                break;
            case 'toggleThinkingMode':
                this._thinkingMode = message.enabled;
                if (message.intensity) {
                    this._thinkingIntensity = message.intensity;
                }
                vscode.window.showInformationMessage(`Thinking mode ${message.enabled ? 'enabled' : 'disabled'} (${this._thinkingIntensity})`);
                break;
            case 'setThinkingIntensity':
                this._thinkingIntensity = message.intensity;
                vscode.window.showInformationMessage(`Thinking intensity: ${this._thinkingIntensity}`);
                break;
            case 'newChat':
                await this._handleNewChat();
                break;
            case 'setCompactMode':
                this._isCompactMode = message.enabled;
                const config = vscode.workspace.getConfiguration('kiAutoAgent.ui');
                config.update('compactMode', this._isCompactMode, vscode.ConfigurationTarget.Global);
                break;
            case 'loadHistory':
            case 'showHistory':
                await this.showHistoryPicker();
                break;
        }
    }

    private async _processUserMessage(text: string, agent: string, mode: string) {
        console.log(`\n💬 [CHAT] ============== NEW MESSAGE ==============`);
        console.log(`💬 [CHAT] User text: "${text}"`);
        console.log(`💬 [CHAT] Selected agent: "${agent}"`);
        console.log(`💬 [CHAT] Selected mode: "${mode}"`);
        console.log(`💬 [CHAT] Current agent field: "${this._currentAgent}"`);
        console.log(`💬 [CHAT] Current mode field: "${this._currentMode}"`);
        
        // Add user message
        const userMessage: ChatMessage = {
            role: 'user',
            content: text,
            timestamp: new Date().toISOString()
        };
        this._messages.push(userMessage);

        // Save to conversation history
        this._saveToHistory('user', text);
        this._contextManager.addEntry({
            timestamp: new Date().toISOString(),
            agent: 'user',
            step: 'input',
            input: text,
            output: '',
            metadata: { mode, selectedAgent: agent }
        });
        
        this._panel.webview.postMessage({
            type: 'addMessage',
            message: userMessage
        });

        // Show typing indicator
        this._panel.webview.postMessage({
            type: 'showTyping',
            agent: agent
        });

        // Debug dispatcher state
        console.log(`🔧 [CHAT] Dispatcher check: ${this._dispatcher ? 'AVAILABLE' : 'NOT AVAILABLE'}`);
        if (this._dispatcher) {
            console.log(`🔧 [CHAT] Dispatcher type: ${typeof this._dispatcher}`);
            console.log(`🔧 [CHAT] Dispatcher has processRequest: ${typeof this._dispatcher.processRequest}`);
            console.log(`🔧 [CHAT] Dispatcher has getAgentStats: ${typeof this._dispatcher.getAgentStats}`);
            
            try {
                const stats = await this._dispatcher.getAgentStats();
                console.log(`🔧 [CHAT] Agent stats keys: [${Object.keys(stats).join(', ')}]`);
                console.log(`🔧 [CHAT] Agent stats count: ${Object.keys(stats).length}`);
            } catch (error) {
                console.error(`🔧 [CHAT] Error getting agent stats: ${error}`);
            }
        } else {
            console.error(`🔧 [CHAT] CRITICAL: No dispatcher available!`);
        }

        try {
            console.log(`🎯 [CHAT MODE] Decision tree:`);
            console.log(`🎯 [CHAT MODE] - mode === 'auto': ${mode === 'auto'}`);
            console.log(`🎯 [CHAT MODE] - mode === 'single': ${mode === 'single'}`);
            console.log(`🎯 [CHAT MODE] - mode === 'workflow': ${mode === 'workflow'}`);
            console.log(`🎯 [CHAT MODE] - this._dispatcher exists: ${!!this._dispatcher}`);
            
            // Process based on mode
            if (mode === 'auto' && this._dispatcher) {
                console.log(`🎯 [CHAT MODE] ✅ Entering AUTO mode with orchestrator`);

                // Create streaming message for orchestrator
                const streamingMessageId = `streaming-${Date.now()}`;
                this._addStreamingMessage(streamingMessageId, 'orchestrator');

                // Show immediate feedback
                this._updateStreamingMessage(streamingMessageId, '🎭 Analyzing your request...\n', false);

                // Use orchestrator with streaming
                const response = await this._callAgentWithStreaming('orchestrator', text, streamingMessageId);

                // Finalize the streaming message
                this._finalizeStreamingMessage(streamingMessageId, response.content, response.metadata);

                // Save orchestrator response to conversation history
                this._saveToHistory('assistant', response.content, 'orchestrator');

                // Save to context manager for future reference
                this._contextManager.addEntry({
                    timestamp: new Date().toISOString(),
                    agent: 'orchestrator',
                    step: 'orchestration',
                    input: text,
                    output: response.content,
                    metadata: response.metadata
                });
            } else if (mode === 'single') {
                console.log(`🎯 [CHAT MODE] ✅ Entering SINGLE mode with agent: "${agent}"`);
                console.log(`🎯 [CHAT MODE] Agent value type: ${typeof agent}`);
                console.log(`🎯 [CHAT MODE] Agent exact value: '${agent}'`);
                console.log(`🎯 [CHAT MODE] Agent length: ${agent?.length}`);
                
                // Create a streaming message placeholder
                const streamingMessageId = `streaming-${Date.now()}`;
                this._addStreamingMessage(streamingMessageId, agent);
                
                // Direct chat with selected agent
                const response = await this._callAgentWithStreaming(agent, text, streamingMessageId);

                // Finalize the streaming message with metadata
                this._finalizeStreamingMessage(streamingMessageId, response.content, response.metadata);

                // Save agent response to conversation history
                this._saveToHistory('assistant', response.content, agent);
            } else if (mode === 'workflow') {
                console.log(`🎯 [CHAT MODE] ✅ Entering WORKFLOW mode`);
                // Multi-agent workflow - show inter-agent communication
                await this._processWorkflow(text);
            } else {
                console.error(`🎯 [CHAT MODE] ❌ No valid mode path! Defaulting to error message`);
                this._addErrorMessage(`Invalid mode configuration: mode="${mode}", agent="${agent}", dispatcher=${!!this._dispatcher}`);
            }
        } catch (error) {
            console.error('[DEBUG] Error in _processUserMessage:', error);
            this._addErrorMessage(`Error: ${(error as any).message}`);
        } finally {
            this._panel.webview.postMessage({
                type: 'hideTyping'
            });
        }
    }

    private async _callAgent(agentId: string, prompt: string): Promise<{ content: string, metadata?: any }> {
        console.log(`\n🤖 [CALL AGENT] ====================================`);
        console.log(`🤖 [CALL AGENT] AgentId: "${agentId}"`);
        console.log(`🤖 [CALL AGENT] Prompt: "${prompt.substring(0, 100)}..."`);
        console.log(`🤖 [CALL AGENT] Dispatcher available: ${!!this._dispatcher}`);
        
        if (!this._dispatcher) {
            const errorMsg = 'Error: No dispatcher available. Please check agent configuration.';
            console.error(`🤖 [CALL AGENT] ❌ ${errorMsg}`);
            return {
                content: errorMsg,
                metadata: null
            };
        }
        
        console.log(`🤖 [CALL AGENT] Dispatcher type: ${typeof this._dispatcher}`);
        console.log(`🤖 [CALL AGENT] Dispatcher.processRequest: ${typeof this._dispatcher.processRequest}`);

        try {
            // Create task request for the dispatcher
            const taskRequest = {
                prompt: prompt,
                command: agentId, // Use agent ID as command
                context: await this._getWorkspaceContext()
            };

            console.log('[DEBUG] Created taskRequest:', JSON.stringify(taskRequest, null, 2));
            console.log('[DEBUG] Calling dispatcher.processRequest...');

            // Call the real dispatcher
            const result = await this._dispatcher.processRequest(taskRequest);
            
            console.log('[DEBUG] Dispatcher returned:', JSON.stringify(result, null, 2));
            
            if (result.status === 'success' || result.status === 'partial_success') {
                return {
                    content: result.content,
                    metadata: result.metadata
                };
            } else {
                return {
                    content: `Error: ${result.content}`,
                    metadata: null
                };
            }
        } catch (error) {
            const errorMsg = `Agent Error: ${(error as any).message}\nStack: ${(error as any).stack}`;
            console.error('[DEBUG]', errorMsg);
            return {
                content: errorMsg,
                metadata: null
            };
        }
    }

    private async _callAgentWithStreaming(agentId: string, prompt: string, messageId: string): Promise<{ content: string, metadata?: any }> {
        console.log(`\n🤖 [CALL AGENT WITH STREAMING] ====================================`);
        console.log(`🤖 [STREAMING] AgentId: "${agentId}"`);
        console.log(`🤖 [STREAMING] AgentId type: ${typeof agentId}`);
        console.log(`🤖 [STREAMING] AgentId exact: '${agentId}'`);
        console.log(`🤖 [STREAMING] MessageId: "${messageId}"`);
        console.log(`🤖 [STREAMING] Creating task request with command: '${agentId}'`);

        if (!this._dispatcher) {
            const errorMsg = 'Error: No dispatcher available. Please check agent configuration.';
            console.error(`🤖 [STREAMING] ❌ ${errorMsg}`);
            return {
                content: errorMsg,
                metadata: null
            };
        }

        let stallCheckInterval: NodeJS.Timeout | undefined;
        let fullContent = ''; // Moved outside try block for access in catch

        try {
            let lastUpdateTime = Date.now();
            const TIMEOUT_MS = 120000; // 2 minutes timeout
            const STALL_DETECTION_MS = 30000; // 30 seconds without update

            // Get conversation history for context
            const conversationHistory = this._contextManager.getFormattedContext(10);

            // Create timeout promise
            const timeoutPromise = new Promise<never>((_, reject) => {
                setTimeout(() => {
                    reject(new Error(`Agent response timed out after ${TIMEOUT_MS / 1000} seconds`));
                }, TIMEOUT_MS);
            });

            // Create stall detection interval
            stallCheckInterval = setInterval(() => {
                const timeSinceLastUpdate = Date.now() - lastUpdateTime;
                if (timeSinceLastUpdate > STALL_DETECTION_MS) {
                    console.warn(`[STREAMING] Warning: No updates for ${timeSinceLastUpdate / 1000} seconds`);
                }
            }, 10000); // Check every 10 seconds

            // Create task request with streaming callback and conversation history
            const taskRequest = {
                prompt: prompt,
                command: agentId,
                context: await this._getWorkspaceContext(),
                globalContext: conversationHistory,
                thinkingMode: this._thinkingMode, // Pass thinking mode to agents
                mode: this._thinkingIntensity === 'layered' ? 'layered' : undefined,
                onPartialResponse: (partialContent: string) => {
                    lastUpdateTime = Date.now(); // Update timestamp on each chunk
                    console.log(`🤖 [STREAMING] Partial content: ${partialContent.length} chars`);

                    // Check if this is a workflow step notification
                    if (partialContent.includes('🔄 **Step')) {
                        // Send as a separate system message
                        const stepMatch = partialContent.match(/🔄 \*\*Step (\d+)\/(\d+)\*\*: @(\w+) - (.+)/);
                        if (stepMatch) {
                            const [, current, total, agent, description] = stepMatch;
                            this._addSystemMessage(`🔄 Step ${current}/${total}: @${agent} - ${description}`);
                        }
                    } else if (partialContent.includes('✅ Completed:')) {
                        // Don't add completion previews to the main message
                        // They will be shown in the final agent response
                        return;
                    } else {
                        // Extract and process tool markers with agent context
                        const currentAgent = agentId; // Agent executing the tools
                        let cleanedContent = partialContent;

                        // Extract <<TOOL>> markers and create tool notifications with agent color
                        const toolMatches = [...partialContent.matchAll(/<<TOOL>>(.*?)<<TOOL_END>>/gs)];
                        for (const match of toolMatches) {
                            const toolContent = match[1];
                            this._addToolNotification(toolContent, currentAgent, messageId);
                            cleanedContent = cleanedContent.replace(match[0], '');
                        }

                        // Clean other markers
                        cleanedContent = cleanedContent
                            .replace(/<<TOOL_RESULT>>.*?<<TOOL_RESULT_END>>/gs, '')
                            .replace(/<<THINKING>>.*?<<THINKING_END>>/gs, '')
                            .replace(/🛠️ \*?Claude is using tools.*?\*?\n*/g, '');

                        // Check for new system tool message format
                        if (cleanedContent.includes('SYSTEM_TOOL_MESSAGE:')) {
                            const parts = cleanedContent.split('SYSTEM_TOOL_MESSAGE:');
                            if (parts[1]) {
                                this._addToolNotification(parts[1], currentAgent, messageId);
                                cleanedContent = parts[0];
                            }
                        }

                        // Only add text content if there's actual content after cleaning
                        if (cleanedContent.trim().length > 0) {
                            fullContent += cleanedContent;
                            this._updateStreamingMessage(messageId, cleanedContent);
                        }
                    }
                }
            };

            // Call the dispatcher with timeout
            const result = await Promise.race([
                this._dispatcher.processRequest(taskRequest),
                timeoutPromise
            ]);

            // Clear stall detection
            clearInterval(stallCheckInterval);

            // Prioritize accumulated streaming content if available and non-empty
            // Fall back to result content if streaming didn't provide content
            const finalContent = fullContent.trim().length > 0 ? fullContent : result.content;
            
            // Save agent response to conversation history
            if (finalContent) {
                this._contextManager.addEntry({
                    timestamp: new Date().toISOString(),
                    agent: agentId,
                    step: 'response',
                    input: prompt,
                    output: finalContent,
                    metadata: result.metadata
                });
            }
            
            if (result.status === 'success' || result.status === 'partial_success') {
                return {
                    content: finalContent,
                    metadata: result.metadata
                };
            } else {
                return {
                    content: `Error: ${result.content}`,
                    metadata: null
                };
            }
        } catch (error) {
            // Clear stall detection if still running
            if (typeof stallCheckInterval !== 'undefined') {
                clearInterval(stallCheckInterval);
            }

            const errorMsg = `Agent Error: ${(error as any).message}`;
            console.error('[STREAMING] Error during agent execution:', error);
            console.error('[STREAMING] Stack trace:', (error as any).stack);

            // Try to salvage partial content if available
            if (fullContent.trim().length > 0) {
                console.log('[STREAMING] Recovering partial content:', fullContent.length, 'chars');
                return {
                    content: fullContent + '\n\n[Response interrupted due to error]',
                    metadata: {
                        error: errorMsg,
                        partial: true
                    }
                };
            }

            return {
                content: errorMsg,
                metadata: {
                    error: errorMsg
                }
            };
        }
    }

    private _addStreamingMessage(messageId: string, agent: string) {
        // Create initial streaming message
        const streamingMessage: ChatMessage = {
            role: 'assistant',
            content: '',
            agent: agent,
            timestamp: new Date().toISOString(),
            isCollapsible: false,
            metadata: { messageId, isStreaming: true }
        };
        this._messages.push(streamingMessage);
        // Save streaming start to history
        this._saveToHistory('assistant', '', agent);

        this._panel.webview.postMessage({
            type: 'addStreamingMessage',
            message: streamingMessage
        });
    }

    private _updateStreamingMessage(messageId: string, partialContent: string, isToolNotification: boolean = false) {
        // Keep track of processed content
        let contentToAdd = partialContent;
        let hasToolNotifications = false;
        let needsNewBubble = false;
        
        // Check for workflow step notifications
        if (contentToAdd.includes('🔄 **Step')) {
            const stepMatch = contentToAdd.match(/🔄 \*\*Step (\d+)\/(\d+)\*\*: @(\w+) - (.+)/);
            if (stepMatch) {
                const [fullMatch, current, total, agent, description] = stepMatch;

                // Initialize workflow container if first step
                if (current === '1') {
                    this._initWorkflowContainer(messageId);
                }

                // Update workflow step
                this._updateWorkflowStep(messageId, parseInt(current), parseInt(total), agent, description);

                // Remove step notification from main content
                contentToAdd = contentToAdd.replace(fullMatch, '');
            }
        }

        // Check for step completion
        if (contentToAdd.includes('✅ Completed:')) {
            const completionMatch = contentToAdd.match(/✅ Completed: (.+)/);
            if (completionMatch) {
                // Find current step number from workflow steps
                const stepKeys = Array.from(this.workflowSteps.keys()).filter(key => key.startsWith(`${messageId}-step-`));
                const currentStep = stepKeys.length;

                if (currentStep > 0) {
                    this._completeWorkflowStep(messageId, currentStep, completionMatch[1]);
                    contentToAdd = contentToAdd.replace(completionMatch[0], '');
                }
            }
        }

        // Check for final result marker
        if (contentToAdd.includes('✅ Task completed') || contentToAdd.includes('<<FINAL_RESULT>>')) {
            if (this.workflowSteps.size > 0) {
                // Clean up markers
                contentToAdd = contentToAdd.replace(/<<FINAL_RESULT>>/g, '');
                contentToAdd = contentToAdd.replace(/✅ Task completed successfully!/g, '');

                // Create final result bubble
                if (contentToAdd.trim()) {
                    this._createFinalResultBubble(messageId, contentToAdd.trim());
                    return; // Don't process further
                }
            }
        }

        // Check for thinking notifications
        while (contentToAdd.includes('<<THINKING>>') && contentToAdd.includes('<<THINKING_END>>')) {
            const thinkingMatch = contentToAdd.match(/<<THINKING>>(.*?)<<THINKING_END>>/s);
            if (thinkingMatch) {
                const thinkingContent = thinkingMatch[1];
                this._addSystemNotification('💭 ' + thinkingContent, messageId);
                contentToAdd = contentToAdd.replace(/<<THINKING>>.*?<<THINKING_END>>/s, '');
                hasToolNotifications = true;
            } else {
                break;
            }
        }
        
        // Check for tool notifications marked with special tags
        while (contentToAdd.includes('<<TOOL>>') && contentToAdd.includes('<<TOOL_END>>')) {
            const toolMatch = contentToAdd.match(/<<TOOL>>(.*?)<<TOOL_END>>/s);
            if (toolMatch) {
                const toolContent = toolMatch[1];
                const toolMsgId = this._addSystemNotification(toolContent, messageId);
                contentToAdd = contentToAdd.replace(/<<TOOL>>.*?<<TOOL_END>>/s, '');
                hasToolNotifications = true;
            } else {
                break;
            }
        }
        
        // Check for tool results to update existing tool notifications
        while (contentToAdd.includes('<<TOOL_RESULT>>') && contentToAdd.includes('<<TOOL_RESULT_END>>')) {
            const resultMatch = contentToAdd.match(/<<TOOL_RESULT>>(.*?)<<TOOL_RESULT_END>>/s);
            if (resultMatch) {
                const [toolId, result] = resultMatch[1].split('||');
                // Find and update the corresponding tool message
                this._updateToolResult(toolId, result);
                contentToAdd = contentToAdd.replace(/<<TOOL_RESULT>>.*?<<TOOL_RESULT_END>>/s, '');
            } else {
                break;
            }
        }
        
        // Check for text start marker
        if (contentToAdd.includes('<<TEXT_START>>')) {
            contentToAdd = contentToAdd.replace(/<<TEXT_START>>/g, '');
            needsNewBubble = true;
        }
        
        // Only update main message if there's content left after removing notifications
        if (contentToAdd.trim()) {
            // If we need a new bubble or don't have an existing message, create one
            let message = this._messages.find(m => m.metadata?.messageId === messageId && m.role === 'assistant');
            
            if (needsNewBubble && !message) {
                // Create a new assistant message bubble
                const newMessage: ChatMessage = {
                    role: 'assistant',
                    content: contentToAdd,
                    agent: 'assistant',
                    timestamp: new Date().toISOString(),
                    metadata: { messageId: `${messageId}-text`, isStreaming: true }
                };
                this._messages.push(newMessage);
                
                this._panel.webview.postMessage({
                    type: 'addStreamingMessage',
                    message: newMessage
                });
            } else if (message) {
                // Update existing message
                message.content += contentToAdd;
                
                this._panel.webview.postMessage({
                    type: 'updateStreamingMessage',  
                    messageId: message.metadata?.messageId || messageId,
                    partialContent: contentToAdd
                });
            }
        }
    }

    private _isSpecialMessage(content: string): boolean {
        // Check if content is a tool notification or special message
        const specialPatterns = [
            /^🚀 \*\*Claude is initializing/,
            /^🔧 \*\*Using tool:/,
            /^⚠️ \*\*System Error:/,
            /^✨ \*\*Tool:/,
            /^📝 \*\*Result:/,
            /^✅ \*\*Task completed:/
        ];
        return specialPatterns.some(pattern => pattern.test(content));
    }

    private _addSystemNotification(content: string, parentMessageId?: string): string {
        // Add a small delay to ensure proper ordering of messages
        const messageId = `system-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const systemMessage: ChatMessage = {
            role: 'system',
            content: content,
            timestamp: new Date().toISOString(),
            metadata: { 
                isSystemNotification: true, 
                parentMessageId: parentMessageId,
                messageId: messageId
            }
        };
        this._messages.push(systemMessage);
        // Save system notification to history
        this._saveToHistory('system', content);

        // Send as a separate addMessage event to create a new bubble
        setTimeout(() => {
            this._panel.webview.postMessage({
                type: 'addMessage',
                message: systemMessage
            });
        }, 10);
        
        return messageId;
    }
    
    private _updateToolResult(toolId: string, result: string) {
        // Find the last tool message and update it with the result
        for (let i = this._messages.length - 1; i >= 0; i--) {
            const message = this._messages[i];
            if (message.role === 'system' && message.content.includes(toolId)) {
                // Append result to the tool message
                if (!message.content.includes('**Result:**')) {
                    message.content += `\n\n**Result:**\n${result}`;
                    
                    // Update the message in the webview
                    this._panel.webview.postMessage({
                        type: 'updateMessage',
                        messageId: message.metadata?.messageId,
                        content: message.content
                    });
                }
                break;
            }
        }
    }

    private _finalizeStreamingMessage(messageId: string, fullContent: string, metadata?: any) {
        // Find and finalize the streaming message
        const message = this._messages.find(m => m.metadata?.messageId === messageId);
        if (message) {
            // Update agent if metadata includes it (for workflow results)
            if (metadata?.agent) {
                message.agent = metadata.agent;
            }

            // Don't add metadata info to content, add it as a separate message
            message.content = fullContent;
            message.metadata = { ...message.metadata, ...metadata, isStreaming: false };
            message.isCollapsible = fullContent.length > 500;

            this._panel.webview.postMessage({
                type: 'finalizeStreamingMessage',
                messageId: messageId,
                fullContent: message.content,
                metadata: message.metadata,
                agent: message.agent
            });

            // Add metadata as a separate completion message if available
            if (metadata && (metadata.usage || metadata.cost || metadata.duration)) {
                this._addCompletionMessage(metadata);
            }
        }
    }

    private _addCompletionMessage(metadata: any) {
        let completionContent = '✅ **Task completed successfully!**\n\n';
        
        // Add execution details
        if (metadata.duration) {
            completionContent += `⏱️ **Execution Time:** ${metadata.duration}\n`;
        }
        
        // Add token usage
        if (metadata.usage) {
            const inputTokens = metadata.usage.inputTokens || 0;
            const outputTokens = metadata.usage.outputTokens || 0;
            const totalTokens = inputTokens + outputTokens;
            completionContent += `📊 **Tokens Used:** ${totalTokens} (Input: ${inputTokens}, Output: ${outputTokens})\n`;
        }
        
        // Add cost if available
        if (metadata.cost) {
            completionContent += `💰 **Cost:** $${metadata.cost.toFixed(4)}\n`;
        }
        
        // Add cache info if available
        if (metadata.usage?.cacheCreationInputTokens || metadata.usage?.cacheReadInputTokens) {
            const cacheCreation = metadata.usage.cacheCreationInputTokens || 0;
            const cacheRead = metadata.usage.cacheReadInputTokens || 0;
            completionContent += `💾 **Cache:** ${cacheCreation} created, ${cacheRead} read\n`;
        }
        
        const completionMessage: ChatMessage = {
            role: 'system',
            content: completionContent,
            timestamp: new Date().toISOString(),
            metadata: { 
                isCompletionMessage: true,
                ...metadata
            }
        };
        this._messages.push(completionMessage);
        
        this._panel.webview.postMessage({
            type: 'addMessage',
            message: completionMessage
        });
    }

    private _buildMetadataInfo(metadata?: any): string {
        let metadataInfo = '';
        
        // Token usage
        if (metadata?.usage) {
            const inputTokens = metadata.usage.inputTokens || 0;
            const outputTokens = metadata.usage.outputTokens || 0;
            const cacheCreation = metadata.usage.cacheCreationInputTokens || 0;
            const cacheRead = metadata.usage.cacheReadInputTokens || 0;
            const totalTokens = inputTokens + outputTokens;
            
            metadataInfo += `\n\n---\n📊 **Tokens**: ${totalTokens} total (Input: ${inputTokens}, Output: ${outputTokens})`;
            
            if (cacheCreation > 0 || cacheRead > 0) {
                metadataInfo += `\n💾 **Cache**: ${cacheCreation} created, ${cacheRead} read`;
            }
        }
        
        // Cost and performance
        if (metadata?.totalCostUsd !== undefined) {
            metadataInfo += `\n💰 **Cost**: $${metadata.totalCostUsd.toFixed(6)}`;
        }
        if (metadata?.durationMs !== undefined) {
            metadataInfo += `\n⏱️ **Duration**: ${metadata.durationMs}ms`;
            if (metadata?.durationApiMs !== undefined) {
                metadataInfo += ` (API: ${metadata.durationApiMs}ms)`;
            }
        }
        
        // Session and model info
        if (metadata?.model) {
            metadataInfo += `\n🤖 **Model**: ${metadata.model}`;
        }
        if (metadata?.sessionId) {
            metadataInfo += `\n🔗 **Session**: ${metadata.sessionId.substring(0, 8)}...`;
        }
        
        // Stop reason
        if (metadata?.stopReason) {
            metadataInfo += `\n⚡ **Stop reason**: ${metadata.stopReason}`;
        }
        
        return metadataInfo;
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

    private _addAgentResponse(content: string, agent: string, metadata?: any) {
        console.log(`📝 [ADD RESPONSE] Adding agent response`);
        console.log(`📝 [ADD RESPONSE] Content length: ${content?.length || 0}`);
        console.log(`📝 [ADD RESPONSE] Agent: ${agent}`);
        console.log(`📝 [ADD RESPONSE] Metadata:`, metadata);
        
        // Build comprehensive metadata info
        let metadataInfo = '';
        
        // Token usage
        if (metadata?.usage) {
            const inputTokens = metadata.usage.inputTokens || 0;
            const outputTokens = metadata.usage.outputTokens || 0;
            const cacheCreation = metadata.usage.cacheCreationInputTokens || 0;
            const cacheRead = metadata.usage.cacheReadInputTokens || 0;
            const totalTokens = inputTokens + outputTokens;
            
            metadataInfo += `\n\n---\n📊 **Tokens**: ${totalTokens} total (Input: ${inputTokens}, Output: ${outputTokens})`;
            
            if (cacheCreation > 0 || cacheRead > 0) {
                metadataInfo += `\n💾 **Cache**: ${cacheCreation} created, ${cacheRead} read`;
            }
        }
        
        // Cost and performance
        if (metadata?.totalCostUsd !== undefined) {
            metadataInfo += `\n💰 **Cost**: $${metadata.totalCostUsd.toFixed(6)}`;
        }
        if (metadata?.durationMs !== undefined) {
            metadataInfo += `\n⏱️ **Duration**: ${metadata.durationMs}ms`;
            if (metadata?.durationApiMs !== undefined) {
                metadataInfo += ` (API: ${metadata.durationApiMs}ms)`;
            }
        }
        
        // Session and model info
        if (metadata?.model) {
            metadataInfo += `\n🤖 **Model**: ${metadata.model}`;
        }
        if (metadata?.sessionId) {
            metadataInfo += `\n🔗 **Session**: ${metadata.sessionId.substring(0, 8)}...`;
        }
        
        // Stop reason
        if (metadata?.stopReason) {
            metadataInfo += `\n⚡ **Stop reason**: ${metadata.stopReason}`;
        }

        const assistantMessage: ChatMessage = {
            role: 'assistant',
            content: content + metadataInfo,
            agent: agent,
            timestamp: new Date().toISOString(),
            isCollapsible: content.length > 500,
            metadata: metadata
        };
        this._messages.push(assistantMessage);
        // Save complete response to history
        this._saveToHistory('assistant', content + metadataInfo, agent);

        console.log(`📝 [ADD RESPONSE] Final message to send:`, assistantMessage);
        console.log(`📝 [ADD RESPONSE] Total messages in history: ${this._messages.length}`);
        
        const postResult = this._panel.webview.postMessage({
            type: 'addMessage',
            message: assistantMessage
        });
        
        console.log(`📝 [ADD RESPONSE] postMessage result:`, postResult);
    }

    private _addSystemMessage(content: string) {
        const systemMessage: ChatMessage = {
            role: 'system',
            content: content,
            timestamp: new Date().toISOString()
        };
        this._messages.push(systemMessage);

        this._panel.webview.postMessage({
            type: 'addMessage',
            message: systemMessage
        });
    }

    private _addToolNotification(content: string, agentName: string, relatedMessageId?: string): string {
        const toolMsgId = `tool_${Date.now()}_${Math.random()}`;

        // Get agent-specific color based on normalized agent name
        const normalizedAgent = agentName.toLowerCase().replace('agent', '').replace('gpt', '').replace('claude', '');
        const agentColor = this._getAgentColor(normalizedAgent);
        const agentEmoji = this._getAgentEmoji(normalizedAgent);

        const toolMessage: ChatMessage = {
            role: 'system',
            content: content,
            agent: agentName,
            timestamp: new Date().toISOString(),
            metadata: {
                isToolNotification: true,
                relatedMessageId,
                toolMsgId,
                agentColor,
                agentEmoji,
                agentName
            }
        };

        this._messages.push(toolMessage);

        // Send to WebView with tool notification flag
        this._panel.webview.postMessage({
            type: 'addMessage',
            message: toolMessage
        });

        return toolMsgId;
    }

    private _getAgentColor(agent: string): string {
        const colors: { [key: string]: string } = {
            'orchestrator': '#8B5CF6',     // Purple
            'architect': '#10B981',        // Emerald Green (changed from blue)
            'codesmith': '#F97316',        // Orange
            'research': '#EAB308',         // Gold
            'tradestrat': '#14B8A6',       // Turquoise
            'opusarbitrator': '#DC2626',   // Crimson
            'docubot': '#6366F1',          // Indigo
            'reviewer': '#EC4899',         // Pink
            'fixer': '#8B5CF6'             // Purple
        };
        return colors[agent.toLowerCase()] || '#3B82F6'; // Default to blue for system
    }

    private _getAgentEmoji(agent: string): string {
        const emojis: { [key: string]: string } = {
            'orchestrator': '🎯',
            'architect': '🏗️',
            'codesmith': '🛠️',
            'research': '🔍',
            'tradestrat': '📈',
            'opusarbitrator': '⚖️',
            'docubot': '📚',
            'reviewer': '🔎',
            'fixer': '🔧'
        };
        return emojis[agent.toLowerCase()] || '🤖';
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

    private _restoreMessages() {
        // Send all stored messages back to the webview
        if (this._messages.length > 0) {
            this._panel.webview.postMessage({
                type: 'restoreMessages',
                messages: this._messages
            });
        }
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

    private async _handlePlanFirst(text: string, agent: string, mode: string) {
        // Add user message with plan request - PLANNING ONLY MODE
        const planPrompt = `PLANNING MODE ONLY - DO NOT IMPLEMENT OR WRITE CODE:

${text}

Instructions for planning:
1. Break down the task into detailed steps
2. List ALL changes that need to be made (be comprehensive)
3. Identify which files need to be modified
4. Specify what each change will accomplish
5. DO NOT write any code or make any implementations
6. Wait for user approval before proceeding with implementation

Please provide a numbered step-by-step plan only.`;

        const userMessage: ChatMessage = {
            role: 'user',
            content: `📋 **PLAN FIRST REQUEST**\n\n${text}`,
            timestamp: new Date().toISOString()
        };
        this._messages.push(userMessage);

        this._panel.webview.postMessage({
            type: 'addMessage',
            message: userMessage
        });

        // Save to conversation history with planning flag
        this._contextManager.addEntry({
            timestamp: new Date().toISOString(),
            agent: 'user',
            step: 'plan_request',
            input: planPrompt,
            output: '',
            metadata: {
                mode: 'planning',
                selectedAgent: agent,
                isPlanFirst: true,
                originalRequest: text
            }
        });

        // Process with agent
        this._panel.webview.postMessage({
            type: 'showTyping',
            agent: agent
        });

        try {
            // Route to orchestrator for planning regardless of selected agent
            const planningAgent = 'orchestrator';
            const streamingMessageId = `streaming-${Date.now()}`;
            this._addStreamingMessage(streamingMessageId, planningAgent);

            // Call orchestrator with planning-only prompt
            const response = await this._dispatcher.processRequest({
                command: 'plan',
                prompt: planPrompt,
                mode: 'planning',
                projectType: 'generic',
                onPartialResponse: (partial: string) => {
                    this._updateStreamingMessage(streamingMessageId, partial);
                }
            });

            // Add confirmation request
            const confirmMessage = '\n\n---\n✅ **Plan complete!** Would you like me to proceed with implementation? Reply "yes" to continue or provide feedback to adjust the plan.';

            this._finalizeStreamingMessage(
                streamingMessageId,
                response.content + confirmMessage,
                { ...response.metadata, isPlan: true }
            );
        } catch (error) {
            console.error('[PLAN FIRST] Error:', error);
            this._addErrorMessage(`Error creating plan: ${(error as any).message}`);
        } finally {
            this._panel.webview.postMessage({
                type: 'hideTyping'
            });
        }
    }

    private _cancelCurrentOperation() {
        console.log('[CHAT] Cancelling current operation...');
        this._isProcessing = false;

        // Cancel any ongoing operations
        if (this._currentOperation) {
            if (typeof this._currentOperation.cancel === 'function') {
                this._currentOperation.cancel();
            }
            this._currentOperation = null;
        }

        // Notify webview
        this._panel.webview.postMessage({
            type: 'operationStopped'
        });

        // Add system message
        this._addSystemMessage('⛔ Operation cancelled by user');
    }

    public addMessage(message: ChatMessage) {
        this._messages.push(message);
        this._panel.webview.postMessage({
            type: 'addMessage',
            message: message
        });
    }

    // Workflow step management methods
    private _initWorkflowContainer(messageId: string): void {
        this._panel.webview.postMessage({
            type: 'initWorkflow',
            messageId,
            timestamp: new Date().toISOString()
        });
    }

    private _updateWorkflowStep(messageId: string, step: number, total: number, agent: string, description: string): void {
        const stepId = `${messageId}-step-${step}`;
        const stepData = {
            step,
            total,
            agent,
            description,
            status: 'in_progress',
            startTime: Date.now(),
            result: null
        };

        this.workflowSteps.set(stepId, stepData);

        this._panel.webview.postMessage({
            type: 'updateWorkflowStep',
            messageId,
            stepData
        });
    }

    private _completeWorkflowStep(messageId: string, step: number, result: string): void {
        const stepId = `${messageId}-step-${step}`;
        const stepData = this.workflowSteps.get(stepId);

        if (stepData) {
            stepData.status = 'completed';
            stepData.result = result;
            stepData.endTime = Date.now();

            this._panel.webview.postMessage({
                type: 'completeWorkflowStep',
                messageId,
                stepData
            });
        }
    }

    private _createFinalResultBubble(messageId: string, content: string): void {
        const finalMessage: ChatMessage = {
            role: 'assistant',
            content,
            agent: 'orchestrator',
            timestamp: new Date().toISOString(),
            metadata: {
                messageId: `${messageId}-final`,
                isFinalResult: true
            }
        };

        this._messages.push(finalMessage);
        // Save final result to history
        this._saveToHistory('assistant', content, 'orchestrator');
        this._panel.webview.postMessage({
            type: 'addFinalResult',
            message: finalMessage
        });
    }

    /**
     * Load messages from conversation history
     */
    private _loadHistoryMessages(): void {
        if (!this._conversationHistory) return;

        const messages = this._conversationHistory.getCurrentMessages();
        if (messages && messages.length > 0) {
            // Convert history messages to chat messages
            this._messages = messages.map(msg => ({
                role: msg.role,
                content: msg.content,
                agent: msg.agent || 'assistant',
                timestamp: msg.timestamp,
                metadata: msg.metadata
            }));

            // Send messages to webview
            this._restoreMessages();
        }
    }

    /**
     * Save message to conversation history
     */
    private _saveToHistory(role: 'user' | 'assistant' | 'system', content: string, agent?: string): void {
        if (!this._conversationHistory) return;

        const historyMessage: ConversationMessage = {
            role,
            content,
            agent,
            timestamp: new Date().toISOString(),
            metadata: {
                thinkingMode: this._thinkingMode,
                thinkingIntensity: this._thinkingIntensity
            }
        };

        this._conversationHistory.addMessage(historyMessage);
    }

    /**
     * Handle new chat request
     */
    private async _handleNewChat(): Promise<void> {
        if (!this._conversationHistory) {
            // If no history manager, just clear messages
            this._messages = [];
            this._contextManager.clearContext();
            this._panel.webview.postMessage({ type: 'clearChat' });
            return;
        }

        // Save current conversation
        this._conversationHistory.saveCurrentConversation();

        // Create new session
        const newSessionId = this._conversationHistory.createNewSession();

        // Clear messages and context
        this._messages = [];
        this._contextManager.clearContext();

        // Notify webview
        this._panel.webview.postMessage({
            type: 'clearChat',
            sessionId: newSessionId
        });

        // Add system message
        const systemMessage: ChatMessage = {
            role: 'system',
            content: '🆕 New chat session started',
            timestamp: new Date().toISOString(),
            metadata: { isSystemNotification: true }
        };
        this._messages.push(systemMessage);
        this._panel.webview.postMessage({ type: 'addMessage', message: systemMessage });
    }

    /**
     * Show history picker
     */
    public async showHistoryPicker(): Promise<void> {
        if (!this._conversationHistory) {
            vscode.window.showWarningMessage('Conversation history is not available');
            return;
        }

        const conversations = this._conversationHistory.listConversations();
        if (conversations.length === 0) {
            vscode.window.showInformationMessage('No conversation history available');
            return;
        }

        const items = conversations.map(conv => ({
            label: conv.title,
            description: `${new Date(conv.lastModified).toLocaleString()} - ${conv.messages.length} messages`,
            detail: conv.id,
            conversation: conv
        }));

        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: 'Select a conversation to load',
            canPickMany: false
        });

        if (selected) {
            // Load the selected conversation
            const conversation = this._conversationHistory.loadConversation(selected.conversation.id);
            if (conversation) {
                // Clear current messages
                this._messages = [];
                this._contextManager.clearContext();

                // Load historical messages
                this._loadHistoryMessages();

                // Notify webview
                this._panel.webview.postMessage({
                    type: 'conversationLoaded',
                    title: conversation.title,
                    messageCount: conversation.messages.length
                });
            }
        }
    }

    /**
     * Handle regenerate response
     */
    private async _handleRegenerate(text: string, agent: string, mode: string): Promise<void> {
        // Re-send the message to get a new response
        await this._processUserMessage(text, agent, mode);
    }

    /**
     * Handle export chat to file
     */
    private async _handleExportChat(content: string): Promise<void> {
        const options: vscode.SaveDialogOptions = {
            defaultUri: vscode.Uri.file(`chat-export-${new Date().toISOString().split('T')[0]}.md`),
            filters: {
                'Markdown': ['md'],
                'All Files': ['*']
            }
        };

        const uri = await vscode.window.showSaveDialog(options);
        if (uri) {
            await vscode.workspace.fs.writeFile(uri, Buffer.from(content, 'utf8'));
            vscode.window.showInformationMessage(`Chat exported to ${uri.fsPath}`);
        }
    }

    /**
     * Handle file attachment
     */
    private async _handleAttachFile(): Promise<void> {
        const options: vscode.OpenDialogOptions = {
            canSelectMany: false,
            openLabel: 'Attach',
            filters: {
                'All Files': ['*']
            }
        };

        const fileUri = await vscode.window.showOpenDialog(options);
        if (fileUri && fileUri[0]) {
            const filePath = fileUri[0].fsPath;
            this._attachedFiles.push(filePath);

            // Notify webview about attached file
            this._panel.webview.postMessage({
                type: 'fileAttached',
                fileName: vscode.Uri.file(filePath).path.split('/').pop(),
                filePath: filePath
            });

            vscode.window.showInformationMessage(`File attached: ${filePath.split('/').pop()}`);
        }
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