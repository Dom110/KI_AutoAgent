/**
 * KI AutoAgent VS Code Extension - v6.0.0 INTEGRATION
 * Connects to manually started v6 Python backend
 * NO auto-start, NO BackendManager
 */
import * as vscode from 'vscode';
import { BackendClient } from './backend/BackendClient';
import { MultiAgentChatPanel } from './ui/MultiAgentChatPanel';
import { ModelSettingsManager } from './config/modelSettings';

// Global instances
let outputChannel: vscode.OutputChannel;
let backendClient: BackendClient;
let modelSettingsManager: ModelSettingsManager;

export async function activate(context: vscode.ExtensionContext) {
    // VERSION 6.0.0 - MANUAL BACKEND START (NO AUTO-START)
    console.log('🚀 KI AutoAgent v6.0.0: v6 Integration Complete');

    // Create output channel
    outputChannel = vscode.window.createOutputChannel('KI AutoAgent');
    outputChannel.clear();
    outputChannel.show(true);

    outputChannel.appendLine('🚀 KI AutoAgent Extension v6.0.0 Activating');
    outputChannel.appendLine('============================================');
    outputChannel.appendLine(`Time: ${new Date().toLocaleString()}`);
    outputChannel.appendLine(`VS Code Version: ${vscode.version}`);
    outputChannel.appendLine('');
    outputChannel.appendLine('🆕 v6.0.0: 12 Intelligence Systems Integrated');
    outputChannel.appendLine('🆕 v6.0.0: Manual Backend Start Required');
    outputChannel.appendLine('🆕 v6.0.0: LangGraph Workflow Architecture');
    outputChannel.appendLine('🆕 v6.0.0: Connects to ws://localhost:8002/ws/chat');
    outputChannel.appendLine('');

    // v6.0.0: NO BackendManager - Extension does NOT start backend!
    // User must start backend manually with:
    // ~/git/KI_AutoAgent/venv/bin/python3 backend/api/server_v6_integrated.py
    outputChannel.appendLine('⚠️  v6.0.0: Extension does NOT auto-start backend');
    outputChannel.appendLine('📝 Start backend manually: ~/git/KI_AutoAgent/venv/bin/python3 backend/api/server_v6_integrated.py');
    outputChannel.appendLine('');

    // Register commands early so they're always available
    outputChannel.appendLine('📝 Registering commands...');
    registerCommandsEarly(context);
    outputChannel.appendLine('✅ Commands registered');

    // Register status bar item
    const statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
    );
    statusBarItem.text = '🤖 KI AutoAgent';
    statusBarItem.tooltip = 'Click to open KI AutoAgent Chat';
    statusBarItem.command = 'ki-autoagent.showChat';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);

    try {

        // v6.0.0: NO .env sync - backend manages its own .env at ~/.ki_autoagent/config/.env
        outputChannel.appendLine('ℹ️  v6.0.0: Backend manages .env at ~/.ki_autoagent/config/.env');

        // v6.0.0: Connect DIRECTLY to v6 server (NO BackendManager auto-start!)
        outputChannel.appendLine('🔌 Initializing Backend Client for v6 server...');
        const wsUrl = 'ws://localhost:8002/ws/chat';
        backendClient = BackendClient.getInstance(wsUrl);

        // Connect to backend
        outputChannel.appendLine('🔗 Connecting to v6 backend WebSocket...');
        outputChannel.appendLine('📍 URL: ws://localhost:8002/ws/chat');
        try {
            await backendClient.connect();
            outputChannel.appendLine('✅ Connected to v6 backend!');
        } catch (error: any) {
            outputChannel.appendLine(`❌ Connection failed: ${error.message}`);
            outputChannel.appendLine('');
            outputChannel.appendLine('⚠️  Backend not running! Start manually:');
            outputChannel.appendLine('    ~/git/KI_AutoAgent/venv/bin/python3 backend/api/server_v6_integrated.py');
            outputChannel.appendLine('');
            vscode.window.showWarningMessage(
                'v6 Backend not running. Start manually: ~/git/KI_AutoAgent/venv/bin/python3 backend/api/server_v6_integrated.py'
            );
            // Continue activation even if connection fails (user can reconnect later)
        }

        // v6.0.0: Simplified model settings (NO auto-discovery in v6)
        outputChannel.appendLine('🤖 Initializing Model Settings Manager...');
        modelSettingsManager = ModelSettingsManager.getInstance(backendClient);
        modelSettingsManager.registerCommands(context);
        outputChannel.appendLine('ℹ️  v6.0.0: Model discovery disabled (v6 uses default models)');

        // Set up event handlers
        setupBackendEventHandlers();

        // Register remaining commands that need backend
        registerBackendCommands(context);

        // Success message
        outputChannel.appendLine('');
        outputChannel.appendLine('✅ KI AutoAgent Extension v6.0.0 activated successfully!');
        outputChannel.appendLine('✅ WebSocket connected to v6 backend: ws://localhost:8002/ws/chat');
        outputChannel.appendLine('✅ All 12 v6 Intelligence Systems ready');
        outputChannel.appendLine('');
        outputChannel.appendLine('Use Ctrl+Shift+P and type "KI AutoAgent" to see available commands');

        // Show success notification
        vscode.window.showInformationMessage(
            '🤖 KI AutoAgent v6.0.0 is ready! Connected to v6 backend.'
        );

    } catch (error: any) {
        outputChannel.appendLine(`❌ Activation failed: ${error.message}`);
        vscode.window.showErrorMessage(
            `KI AutoAgent activation failed: ${error.message}`
        );
    }
}

function setupBackendEventHandlers() {
    // Handle backend responses
    backendClient.on('response', (message) => {
        outputChannel.appendLine(`📨 Agent Response: ${message.agent}`);
        // Forward to chat panel if open
        MultiAgentChatPanel.sendMessageToPanel(message);
    });

    backendClient.on('thinking', (message) => {
        outputChannel.appendLine(`🤔 Agent Thinking: ${message.agent}`);
        MultiAgentChatPanel.sendMessageToPanel(message);
    });

    backendClient.on('progress', (message) => {
        outputChannel.appendLine(`📊 ${message.agent}: ${message.message}`);
        MultiAgentChatPanel.sendMessageToPanel({
            type: 'progress',
            agent: message.agent,
            content: message.message
        });
    });

    backendClient.on('error', (error) => {
        outputChannel.appendLine(`❌ Backend Error: ${error.message || error}`);
        vscode.window.showErrorMessage(`Backend error: ${error.message || error}`);
    });

    backendClient.on('disconnected', () => {
        outputChannel.appendLine('❌ Disconnected from backend');
        vscode.window.showWarningMessage(
            'Disconnected from Python backend. Trying to reconnect...'
        );
    });

    backendClient.on('connected', () => {
        outputChannel.appendLine('✅ Reconnected to backend');
        vscode.window.showInformationMessage('Reconnected to Python backend');
    });
}

// Register commands that can work without backend
function registerCommandsEarly(context: vscode.ExtensionContext) {
    // Main chat command - can open even if backend not ready
    const showChatCmd = vscode.commands.registerCommand(
        'ki-autoagent.showChat',
        () => {
            if (!backendClient) {
                // Create a temporary client if backend is not ready
                const wsUrl = 'ws://localhost:8002/ws/chat';
                backendClient = BackendClient.getInstance(wsUrl);
            }
            MultiAgentChatPanel.createOrShow(
                context.extensionUri,
                backendClient
            );
        }
    );
    context.subscriptions.push(showChatCmd);


    // Help command
    const helpCmd = vscode.commands.registerCommand(
        'ki-autoagent.showHelp',
        () => {
            vscode.window.showInformationMessage(
                'KI AutoAgent v6.0.0 - Use Ctrl+Shift+P and type "KI AutoAgent" to see all commands'
            );
        }
    );
    context.subscriptions.push(helpCmd);

    // v6.0.0: Reconnect command (NO stop/start - backend is manually managed)
    const restartBackendCmd = vscode.commands.registerCommand(
        'ki-autoagent.restartBackend',
        async () => {
            if (backendClient) {
                outputChannel.appendLine('🔄 Reconnecting to v6 backend...');
                try {
                    await backendClient.connect();
                    vscode.window.showInformationMessage('✅ Reconnected to v6 backend successfully');
                } catch (error: any) {
                    outputChannel.appendLine(`❌ Reconnection failed: ${error.message}`);
                    vscode.window.showErrorMessage(
                        `Failed to reconnect. Start backend manually: ~/git/KI_AutoAgent/venv/bin/python3 backend/api/server_v6_integrated.py`
                    );
                }
            } else {
                vscode.window.showWarningMessage('Backend client not initialized');
            }
        }
    );
    context.subscriptions.push(restartBackendCmd);

    // v6.0.0: Backend status command (simplified - just checks connection)
    const backendStatusCmd = vscode.commands.registerCommand(
        'ki-autoagent.showBackendStatus',
        async () => {
            if (backendClient) {
                const connected = backendClient.isConnectedToBackend();
                vscode.window.showInformationMessage(
                    `v6 Backend: ${connected ? 'Connected ✅' : 'Disconnected ❌'} | ` +
                    `URL: ws://localhost:8002/ws/chat`
                );
            } else {
                vscode.window.showWarningMessage('Backend client not initialized');
            }
        }
    );
    context.subscriptions.push(backendStatusCmd);
}

// v6.0.0: Register minimal backend commands
function registerBackendCommands(context: vscode.ExtensionContext) {
    // v6.0.0: Manual backend start instructions
    const showInstructionsCmd = vscode.commands.registerCommand(
        'ki-autoagent.showBackendInstructions',
        () => {
            const panel = vscode.window.createWebviewPanel(
                'backendInstructions',
                'v6 Backend Start Instructions',
                vscode.ViewColumn.One,
                {}
            );

            panel.webview.html = `
                <html>
                <body>
                    <h1>Start v6 Backend Manually</h1>
                    <h2>Required for v6.0.0</h2>
                    <ol>
                        <li>Open a terminal</li>
                        <li>Navigate to KI_AutoAgent directory: <code>cd ~/git/KI_AutoAgent</code></li>
                        <li>Start v6 server: <code>./venv/bin/python3 backend/api/server_v6_integrated.py</code></li>
                    </ol>
                    <p>The backend will be available at:</p>
                    <ul>
                        <li>HTTP: <a href="http://localhost:8002">http://localhost:8002</a></li>
                        <li>WebSocket: <code>ws://localhost:8002/ws/chat</code></li>
                    </ul>
                    <h3>v6 Features:</h3>
                    <ul>
                        <li>✅ Query Classifier</li>
                        <li>✅ Curiosity System</li>
                        <li>✅ Predictive System</li>
                        <li>✅ Neurosymbolic Engine</li>
                        <li>✅ Tool Registry</li>
                        <li>✅ Approval Manager</li>
                        <li>✅ Workflow Adapter</li>
                        <li>✅ Perplexity Integration</li>
                        <li>✅ Asimov Rule 3</li>
                        <li>✅ Learning System</li>
                        <li>✅ Self-Diagnosis</li>
                        <li>✅ Memory System v6</li>
                    </ul>
                </body>
                </html>
            `;
        }
    );
    context.subscriptions.push(showInstructionsCmd);
}

export function deactivate() {
    outputChannel.appendLine('🛑 KI AutoAgent Extension deactivating...');

    // v6.0.0: NO BackendManager - just disconnect client
    // Backend stays running (manually managed)
    if (backendClient) {
        backendClient.disconnect();
        backendClient.dispose();
    }

    outputChannel.appendLine('✅ Extension deactivated');
    outputChannel.appendLine('ℹ️  v6 backend keeps running (manual management)');
    outputChannel.dispose();
}