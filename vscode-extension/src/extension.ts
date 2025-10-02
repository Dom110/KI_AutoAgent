/**
 * KI AutoAgent VS Code Extension - BACKEND INTEGRATED VERSION
 * Connects to Python backend for all agent intelligence
 */
import * as vscode from 'vscode';
import { BackendManager } from './backend/BackendManager';
import { BackendClient } from './backend/BackendClient';
import { MultiAgentChatPanel } from './ui/MultiAgentChatPanel';
import { ModelSettingsManager } from './config/modelSettings';

// Global instances
let outputChannel: vscode.OutputChannel;
let backendManager: BackendManager;
let backendClient: BackendClient;
let modelSettingsManager: ModelSettingsManager;

/**
 * Sync VS Code settings to backend/.env file
 * This ensures Python backend always has latest API keys
 */
async function syncSettingsToEnv(channel: vscode.OutputChannel): Promise<void> {
    const fs = require('fs').promises;
    const path = require('path');

    try {
        // Get settings
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        const openaiKey = config.get<string>('openai.apiKey', '');
        const anthropicKey = config.get<string>('anthropic.apiKey', '');
        const perplexityKey = config.get<string>('perplexity.apiKey', '');

        // Get workspace folder
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || workspaceFolders.length === 0) {
            channel.appendLine('⚠️ No workspace folder found, skipping .env sync');
            return;
        }

        const workspacePath = workspaceFolders[0].uri.fsPath;
        const envPath = path.join(workspacePath, 'backend', '.env');

        // Read existing .env if it exists
        let envContent = '';
        try {
            envContent = await fs.readFile(envPath, 'utf8');
        } catch (error) {
            // .env doesn't exist, will create new one
            channel.appendLine('📝 Creating new .env file...');
        }

        // Parse existing .env
        const envLines: string[] = envContent.split('\n');
        const envMap = new Map<string, string>();

        for (const line of envLines) {
            if (line.trim() && !line.startsWith('#')) {
                const [key, ...valueParts] = line.split('=');
                if (key) {
                    envMap.set(key.trim(), valueParts.join('='));
                }
            }
        }

        // Update with settings values (only if provided in settings)
        if (openaiKey) {
            envMap.set('OPENAI_API_KEY', openaiKey);
            channel.appendLine('  ✓ Updated OPENAI_API_KEY');
        }
        if (anthropicKey) {
            envMap.set('ANTHROPIC_API_KEY', anthropicKey);
            channel.appendLine('  ✓ Updated ANTHROPIC_API_KEY');
        }
        if (perplexityKey) {
            envMap.set('PERPLEXITY_API_KEY', perplexityKey);
            channel.appendLine('  ✓ Updated PERPLEXITY_API_KEY');
        }

        // Build new .env content
        const newEnvLines: string[] = [];
        newEnvLines.push('# API Keys - Auto-synced from VS Code settings');
        newEnvLines.push('# Edit in: VS Code Settings → KI AutoAgent');
        newEnvLines.push('');

        for (const [key, value] of envMap) {
            newEnvLines.push(`${key}=${value}`);
        }

        // Write back to .env
        await fs.writeFile(envPath, newEnvLines.join('\n'), 'utf8');
        channel.appendLine(`  📁 Written to: ${envPath}`);

    } catch (error: any) {
        channel.appendLine(`❌ Failed to sync settings to .env: ${error.message}`);
        // Don't throw - allow extension to continue even if sync fails
    }
}

/**
 * Watch for settings changes and auto-sync to .env
 */
function watchSettingsChanges(channel: vscode.OutputChannel): vscode.Disposable {
    return vscode.workspace.onDidChangeConfiguration(async (e) => {
        if (e.affectsConfiguration('kiAutoAgent.openai.apiKey') ||
            e.affectsConfiguration('kiAutoAgent.anthropic.apiKey') ||
            e.affectsConfiguration('kiAutoAgent.perplexity.apiKey')) {

            channel.appendLine('🔄 Settings changed, re-syncing to .env...');
            await syncSettingsToEnv(channel);
            channel.appendLine('✅ Settings re-synced');

            // Notify user that backend may need restart
            const action = await vscode.window.showInformationMessage(
                'API keys updated. Restart backend for changes to take effect?',
                'Restart Backend',
                'Not Now'
            );

            if (action === 'Restart Backend') {
                vscode.commands.executeCommand('ki-autoagent.restartBackend');
            }
        }
    });
}

export async function activate(context: vscode.ExtensionContext) {
    // VERSION 4.0.0 - PYTHON BACKEND ARCHITECTURE
    console.log('🚀 KI AutoAgent v4.0.0: Python Backend Architecture');

    // Create output channel
    outputChannel = vscode.window.createOutputChannel('KI AutoAgent');
    outputChannel.clear();
    outputChannel.show(true);

    outputChannel.appendLine('🚀 KI AutoAgent Extension v4.0.5 Activating');
    outputChannel.appendLine('============================================');
    outputChannel.appendLine(`Time: ${new Date().toLocaleString()}`);
    outputChannel.appendLine(`VS Code Version: ${vscode.version}`);
    outputChannel.appendLine('');
    outputChannel.appendLine('🆕 NEW: Python Backend Architecture');
    outputChannel.appendLine('🆕 NEW: All agents run in Python backend');
    outputChannel.appendLine('🆕 NEW: WebSocket real-time communication');
    outputChannel.appendLine('🆕 NEW: Auto-start backend on extension activation');
    outputChannel.appendLine('');

    // Initialize Backend Manager early
    outputChannel.appendLine('📦 Initializing Backend Manager...');
    backendManager = BackendManager.getInstance(context);

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

        // Sync settings to .env BEFORE starting backend
        outputChannel.appendLine('🔑 Syncing API keys from settings to .env...');
        await syncSettingsToEnv(outputChannel);
        outputChannel.appendLine('✅ Settings synced to .env');

        // Start Python backend automatically
        outputChannel.appendLine('🐍 Starting Python backend...');
        const backendStarted = await backendManager.startBackend();

        if (!backendStarted) {
            // Backend failed to start, show warning
            const action = await vscode.window.showWarningMessage(
                'Python backend failed to start automatically. The extension will work with limited functionality.',
                'Start Manually',
                'Continue Anyway'
            );

            if (action === 'Start Manually') {
                // Show instructions
                outputChannel.appendLine('📝 Showing manual start instructions...');
                vscode.commands.executeCommand('ki-autoagent.showBackendInstructions');
            }
        } else {
            outputChannel.appendLine('✅ Python backend is running!');
        }

        // Initialize Backend Client
        outputChannel.appendLine('🔌 Initializing Backend Client...');
        const wsUrl = backendManager.getWebSocketUrl();
        backendClient = BackendClient.getInstance(wsUrl);

        // Connect to backend
        outputChannel.appendLine('🔗 Connecting to backend WebSocket...');
        await backendClient.connect();
        outputChannel.appendLine('✅ Connected to backend!');

        // Initialize Model Settings Manager
        outputChannel.appendLine('🤖 Initializing Model Settings Manager...');
        modelSettingsManager = ModelSettingsManager.getInstance(backendClient);

        // Auto-discover models if enabled (with rich descriptions)
        const config = vscode.workspace.getConfiguration('kiAutoAgent.models');
        if (config.get('autoDiscover', true)) {
            outputChannel.appendLine('🔍 Auto-discovering available AI models with descriptions...');
            outputChannel.appendLine('   Fetching 15 GPT models (incl. Realtime, o1)...');
            outputChannel.appendLine('   Fetching 5 Claude models (Opus, Sonnet)...');
            outputChannel.appendLine('   Fetching 5 Perplexity models (Research)...');
            try {
                // Use new rich discovery method instead of legacy refreshAvailableModels
                await modelSettingsManager.discoverModelsOnStartup();
                outputChannel.appendLine('✅ Model discovery complete with pros/cons/cost info!');
            } catch (error) {
                outputChannel.appendLine(`⚠️ Model discovery failed: ${error}`);
                outputChannel.appendLine('   Continuing with default models...');
            }
        }

        // Register model management commands
        modelSettingsManager.registerCommands(context);

        // Watch for settings changes and auto-sync
        const settingsWatcher = watchSettingsChanges(outputChannel);
        context.subscriptions.push(settingsWatcher);

        // Set up event handlers
        setupBackendEventHandlers();

        // Register remaining commands that need backend
        registerBackendCommands(context);

        // Success message
        outputChannel.appendLine('');
        outputChannel.appendLine('✅ KI AutoAgent Extension activated successfully!');
        outputChannel.appendLine('✅ Python backend is running on http://localhost:8001');
        outputChannel.appendLine('✅ WebSocket connected to ws://localhost:8001/ws/chat');
        outputChannel.appendLine('');
        outputChannel.appendLine('Use Ctrl+Shift+P and type "KI AutoAgent" to see available commands');

        // Show success notification
        vscode.window.showInformationMessage(
            '🤖 KI AutoAgent is ready! Python backend is running.'
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
                const wsUrl = 'ws://localhost:8001/ws/chat';
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
                'KI AutoAgent v4.0.5 - Use Ctrl+Shift+P and type "KI AutoAgent" to see all commands'
            );
        }
    );
    context.subscriptions.push(helpCmd);

    // Stop backend command
    const stopBackendCmd = vscode.commands.registerCommand(
        'ki-autoagent.stopBackend',
        async () => {
            if (backendManager) {
                outputChannel.appendLine('🛑 Stopping backend...');
                await backendManager.stopBackend();
                vscode.window.showInformationMessage('Backend stopped');
            } else {
                vscode.window.showWarningMessage('Backend manager not initialized');
            }
        }
    );
    context.subscriptions.push(stopBackendCmd);

    // Restart backend command
    const restartBackendCmd = vscode.commands.registerCommand(
        'ki-autoagent.restartBackend',
        async () => {
            if (backendManager) {
                outputChannel.appendLine('🔄 Restarting backend...');
                await backendManager.stopBackend();
                await new Promise(resolve => setTimeout(resolve, 2000));
                const started = await backendManager.startBackend();
                if (started && backendClient) {
                    await backendClient.connect();
                    vscode.window.showInformationMessage('Backend restarted successfully');
                }
            } else {
                vscode.window.showWarningMessage('Backend manager not initialized');
            }
        }
    );
    context.subscriptions.push(restartBackendCmd);

    // Backend status command
    const backendStatusCmd = vscode.commands.registerCommand(
        'ki-autoagent.showBackendStatus',
        async () => {
            if (backendManager) {
                const status = backendManager.getStatus();
                const health = await backendManager.checkBackendHealth();
                vscode.window.showInformationMessage(
                    `Backend: ${status.running ? 'Running ✅' : 'Stopped ❌'} | ` +
                    `Health: ${health ? 'Healthy ✅' : 'Unhealthy ❌'} | ` +
                    `URL: ${status.url}`
                );
            } else {
                vscode.window.showWarningMessage('Backend not yet initialized');
            }
        }
    );
    context.subscriptions.push(backendStatusCmd);
}

// Register commands that need backend connection
function registerBackendCommands(context: vscode.ExtensionContext) {
    // Manual backend start instructions
    const showInstructionsCmd = vscode.commands.registerCommand(
        'ki-autoagent.showBackendInstructions',
        () => {
            const panel = vscode.window.createWebviewPanel(
                'backendInstructions',
                'Backend Start Instructions',
                vscode.ViewColumn.One,
                {}
            );

            panel.webview.html = `
                <html>
                <body>
                    <h1>Start Python Backend Manually</h1>
                    <ol>
                        <li>Open a terminal</li>
                        <li>Navigate to backend directory: <code>cd backend</code></li>
                        <li>Activate virtual environment: <code>source venv/bin/activate</code></li>
                        <li>Start server: <code>python -m uvicorn api.server:app --reload</code></li>
                    </ol>
                    <p>The backend should be available at <a href="http://localhost:8000">http://localhost:8000</a></p>
                </body>
                </html>
            `;
        }
    );
    context.subscriptions.push(showInstructionsCmd);
}

export function deactivate() {
    outputChannel.appendLine('🛑 KI AutoAgent Extension deactivating...');

    // Stop backend
    if (backendManager) {
        backendManager.stopBackend();
        backendManager.dispose();
    }

    // Disconnect client
    if (backendClient) {
        backendClient.disconnect();
        backendClient.dispose();
    }

    outputChannel.appendLine('✅ Extension deactivated');
    outputChannel.dispose();
}