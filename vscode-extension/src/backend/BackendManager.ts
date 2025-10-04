/**
 * BackendManager - Manages connection to global Python backend service
 * v5.8.1: Backend runs as global service, extension only connects
 */

import * as vscode from 'vscode';
import axios from 'axios';

export class BackendManager {
    private static instance: BackendManager;
    private outputChannel: vscode.OutputChannel;
    private isConnected: boolean = false;

    // Get configuration from settings
    private get backendUrl(): string {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        const url = config.get<string>('backend.url', 'localhost:8001');
        return url.startsWith('http') ? url : `http://${url}`;
    }

    private get wsUrl(): string {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        const url = config.get<string>('backend.url', 'localhost:8001');
        const wsProtocol = url.startsWith('https') ? 'wss' : 'ws';
        const cleanUrl = url.replace(/^https?:\/\//, '');
        return `${wsProtocol}://${cleanUrl}/ws/chat`;
    }

    private constructor(private context: vscode.ExtensionContext) {
        this.outputChannel = vscode.window.createOutputChannel('KI AutoAgent Backend');
    }

    public static getInstance(context: vscode.ExtensionContext): BackendManager {
        if (!BackendManager.instance) {
            BackendManager.instance = new BackendManager(context);
        }
        return BackendManager.instance;
    }

    /**
     * Check if backend is running and healthy
     * v5.8.1: Backend is a global service, we only check if it's available
     */
    public async ensureBackendRunning(): Promise<boolean> {
        this.outputChannel.appendLine('🔍 Checking backend service...');

        const isHealthy = await this.checkBackendHealth();

        if (!isHealthy) {
            this.outputChannel.appendLine('❌ Backend service is not running');
            this.showBackendNotRunningInstructions();
            return false;
        }

        this.outputChannel.appendLine('✅ Backend service is running and healthy');
        this.isConnected = true;
        return true;
    }

    /**
     * Check if backend is healthy
     */
    public async checkBackendHealth(): Promise<boolean> {
        try {
            const response = await axios.get(`${this.backendUrl}/health`, {
                timeout: 2000
            });
            return response.data.status === 'healthy';
        } catch (error) {
            return false;
        }
    }

    /**
     * Show instructions for starting the global backend service
     */
    private showBackendNotRunningInstructions(): void {
        const homeDir = require('os').homedir();
        const instructions = `
❌ KI AutoAgent Backend is not running!

The backend now runs as a global service (v5.8.1+).

To start the backend:
  1. Open a terminal
  2. Run: ${homeDir}/.ki_autoagent/start.sh

To check status:
  ${homeDir}/.ki_autoagent/status.sh

To stop:
  ${homeDir}/.ki_autoagent/stop.sh

The backend will serve all your VS Code workspaces from a single process.
Each workspace is isolated via the workspace_path sent during connection.
`;

        this.outputChannel.appendLine(instructions);
        this.outputChannel.show();

        vscode.window.showErrorMessage(
            'KI AutoAgent Backend is not running. Please start it manually.',
            'Show Instructions',
            'Check Status'
        ).then(async action => {
            if (action === 'Show Instructions') {
                this.outputChannel.show();
            } else if (action === 'Check Status') {
                const isHealthy = await this.checkBackendHealth();
                if (isHealthy) {
                    vscode.window.showInformationMessage('✅ Backend is now running!');
                    this.isConnected = true;
                } else {
                    vscode.window.showWarningMessage('❌ Backend is still not running');
                }
            }
        });
    }

    /**
     * Get backend status
     */
    public getStatus(): { running: boolean; url: string; wsUrl: string } {
        return {
            running: this.isConnected,
            url: this.backendUrl,
            wsUrl: this.wsUrl
        };
    }

    /**
     * Get WebSocket URL
     */
    public getWebSocketUrl(): string {
        return this.wsUrl;
    }

    /**
     * Get backend URL
     */
    public getBackendUrl(): string {
        return this.backendUrl;
    }

    /**
     * v5.8.1: Backend runs as global service - no need to stop per extension
     * This method is kept for backwards compatibility but does nothing
     */
    public async stopBackend(): Promise<void> {
        this.outputChannel.appendLine('ℹ️  Backend runs as global service. Use $HOME/.ki_autoagent/stop.sh to stop it.');
        this.isConnected = false;
    }

    /**
     * Dispose and cleanup
     */
    public dispose(): void {
        // Don't stop the backend - it's a global service
        this.isConnected = false;
        this.outputChannel.dispose();
    }
}
