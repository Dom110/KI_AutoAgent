/**
 * BackendManager - Manages Python backend lifecycle
 * Automatically starts and monitors the Python FastAPI server
 */

import * as vscode from 'vscode';
import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import axios from 'axios';

export class BackendManager {
    private static instance: BackendManager;
    private backendProcess: ChildProcess | null = null;
    private outputChannel: vscode.OutputChannel;
    private isRunning: boolean = false;
    private startupAttempts: number = 0;
    private readonly maxStartupAttempts: number = 3;

    // Get configuration from settings
    private get backendUrl(): string {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        const url = config.get<string>('backend.url', 'localhost:8000');
        return url.startsWith('http') ? url : `http://${url}`;
    }

    private get wsUrl(): string {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        const url = config.get<string>('backend.url', 'localhost:8000');
        const wsProtocol = url.startsWith('https') ? 'wss' : 'ws';
        const cleanUrl = url.replace(/^https?:\/\//, '');
        return `${wsProtocol}://${cleanUrl}/ws/chat`;
    }

    private get pythonPath(): string {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        return config.get<string>('backend.pythonPath', 'python3');
    }

    private get autoStart(): boolean {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        return config.get<boolean>('backend.autoStart', true);
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
     * Start the Python backend automatically
     */
    public async startBackend(): Promise<boolean> {
        // Check if auto-start is disabled
        if (!this.autoStart) {
            this.outputChannel.appendLine('⚠️ Backend auto-start is disabled in settings');
            this.outputChannel.appendLine('Starting backend check only...');
            return await this.checkBackendHealth();
        }
        if (this.isRunning) {
            this.outputChannel.appendLine('✅ Backend already running');
            return true;
        }

        this.outputChannel.show();
        this.outputChannel.appendLine('🚀 Starting Python backend...');

        try {
            // Check if backend is already running (started manually)
            const isAlreadyRunning = await this.checkBackendHealth();
            if (isAlreadyRunning) {
                this.outputChannel.appendLine('✅ Backend already running (external process)');
                this.isRunning = true;
                return true;
            }

            // Get backend directory path
            const workspaceRoot = vscode.workspace.rootPath;
            if (!workspaceRoot) {
                throw new Error('No workspace folder open');
            }

            const backendDir = path.join(workspaceRoot, 'backend');
            const venvPython = path.join(backendDir, 'venv', 'bin', 'python');
            const serverPath = path.join(backendDir, 'api', 'server.py');

            // Check if backend directory exists
            if (!fs.existsSync(backendDir)) {
                throw new Error(`Backend directory not found: ${backendDir}`);
            }

            // Check if virtual environment exists
            if (!fs.existsSync(venvPython)) {
                this.outputChannel.appendLine('⚠️ Virtual environment not found, using system Python');
                // Use system Python as fallback
            }

            // Start the backend process
            const pythonExecutable = fs.existsSync(venvPython) ? venvPython : this.pythonPath;

            // Extract port from backend URL
            const urlParts = this.backendUrl.match(/:(\d+)$/);
            const port = urlParts ? urlParts[1] : '8000';

            this.backendProcess = spawn(pythonExecutable, [
                '-m', 'uvicorn',
                'api.server:app',
                '--host', '0.0.0.0',
                '--port', port,
                '--reload'
            ], {
                cwd: backendDir,
                env: {
                    ...process.env,
                    PYTHONPATH: backendDir
                }
            });

            // Handle stdout
            this.backendProcess.stdout?.on('data', (data) => {
                const output = data.toString();
                this.outputChannel.append(output);

                // Check for startup completion
                if (output.includes('Uvicorn running on') || output.includes('Application startup complete')) {
                    this.outputChannel.appendLine('✅ Backend started successfully!');
                    this.isRunning = true;
                    vscode.window.showInformationMessage('🤖 KI AutoAgent Backend is ready!');
                }
            });

            // Handle stderr
            this.backendProcess.stderr?.on('data', (data) => {
                this.outputChannel.append(`❌ Error: ${data.toString()}`);
            });

            // Handle process exit
            this.backendProcess.on('exit', (code) => {
                this.outputChannel.appendLine(`Backend process exited with code ${code}`);
                this.isRunning = false;

                // Auto-restart if crashed unexpectedly
                if (code !== 0 && this.startupAttempts < this.maxStartupAttempts) {
                    this.startupAttempts++;
                    this.outputChannel.appendLine(`Attempting restart (${this.startupAttempts}/${this.maxStartupAttempts})...`);
                    setTimeout(() => this.startBackend(), 2000);
                }
            });

            // Wait for backend to be ready
            await this.waitForBackend();

            return true;

        } catch (error: any) {
            this.outputChannel.appendLine(`❌ Failed to start backend: ${error.message}`);
            vscode.window.showErrorMessage(`Failed to start Python backend: ${error.message}`);

            // Show instructions to start manually
            const action = await vscode.window.showErrorMessage(
                'Python backend failed to start automatically.',
                'Show Instructions',
                'Retry'
            );

            if (action === 'Show Instructions') {
                this.showManualStartInstructions();
            } else if (action === 'Retry') {
                this.startupAttempts++;
                return await this.startBackend();
            }

            return false;
        }
    }

    /**
     * Stop the Python backend
     */
    public async stopBackend(): Promise<void> {
        if (this.backendProcess) {
            this.outputChannel.appendLine('🛑 Stopping Python backend...');
            this.backendProcess.kill('SIGTERM');
            this.backendProcess = null;
            this.isRunning = false;
            this.outputChannel.appendLine('✅ Backend stopped');
        }
    }

    /**
     * Check if backend is healthy
     */
    public async checkBackendHealth(): Promise<boolean> {
        try {
            const response = await axios.get(`${this.backendUrl}/`, {
                timeout: 2000
            });
            return response.data.status === 'healthy';
        } catch (error) {
            return false;
        }
    }

    /**
     * Wait for backend to be ready
     */
    private async waitForBackend(maxWaitTime: number = 30000): Promise<void> {
        const startTime = Date.now();
        const checkInterval = 1000;

        return new Promise((resolve, reject) => {
            const timer = setInterval(async () => {
                const elapsed = Date.now() - startTime;

                if (elapsed > maxWaitTime) {
                    clearInterval(timer);
                    reject(new Error('Backend startup timeout'));
                    return;
                }

                const isHealthy = await this.checkBackendHealth();
                if (isHealthy) {
                    clearInterval(timer);
                    this.isRunning = true;
                    this.outputChannel.appendLine('✅ Backend is ready!');
                    resolve();
                }
            }, checkInterval);
        });
    }

    /**
     * Show manual start instructions
     */
    private showManualStartInstructions(): void {
        const instructions = `
# Manual Backend Start Instructions

1. Open a terminal
2. Navigate to the backend directory:
   cd backend

3. Activate virtual environment:
   source venv/bin/activate  # On macOS/Linux
   .\\venv\\Scripts\\activate  # On Windows

4. Start the server:
   python -m uvicorn api.server:app --reload

5. The backend should be available at http://localhost:8000
`;

        this.outputChannel.appendLine(instructions);
        this.outputChannel.show();
    }

    /**
     * Get backend status
     */
    public getStatus(): { running: boolean; url: string; wsUrl: string } {
        return {
            running: this.isRunning,
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
     * Dispose and cleanup
     */
    public dispose(): void {
        this.stopBackend();
        this.outputChannel.dispose();
    }
}