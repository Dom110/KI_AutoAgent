/**
 * BackendManager - Manages Python backend lifecycle
 * Automatically starts and monitors the Python FastAPI server
 */

import * as vscode from 'vscode';
import { spawn, ChildProcess, exec } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import axios from 'axios';
import * as net from 'net';

export class BackendManager {
    private static instance: BackendManager;
    private backendProcess: ChildProcess | null = null;
    private outputChannel: vscode.OutputChannel;
    private isRunning: boolean = false;
    private startupAttempts: number = 0;
    private lastAttemptTime: number = 0;
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
            // Extract port from backend URL
            const urlParts = this.backendUrl.match(/:(\d+)/);
            const port = parseInt(urlParts ? urlParts[1] : '8000');

            // Check if backend is already running and healthy
            const isAlreadyRunning = await this.checkBackendHealth();
            if (isAlreadyRunning) {
                this.outputChannel.appendLine('✅ Backend already running and healthy');
                this.isRunning = true;
                return true;
            }

            // Check if port is occupied by a stale process
            const portInUse = await this.isPortInUse(port);
            if (portInUse) {
                this.outputChannel.appendLine(`⚠️ Port ${port} is in use. Attempting to free it...`);
                const killed = await this.killProcessOnPort(port);
                if (killed) {
                    this.outputChannel.appendLine(`✅ Freed port ${port}`);
                    // Wait longer for port to be fully released
                    await new Promise(resolve => setTimeout(resolve, 3000));

                    // Double-check the port is free
                    const stillInUse = await this.isPortInUse(port);
                    if (stillInUse) {
                        this.outputChannel.appendLine(`⚠️ Port ${port} still in use after cleanup. Waiting longer...`);
                        await new Promise(resolve => setTimeout(resolve, 2000));
                    }
                } else {
                    this.outputChannel.appendLine(`❌ Could not free port ${port}. Please manually stop the process.`);
                    throw new Error(`Port ${port} is already in use`);
                }
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

            this.backendProcess = spawn(pythonExecutable, [
                '-m', 'uvicorn',
                'api.server:app',
                '--host', '0.0.0.0',
                '--port', port.toString(),
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

            // Handle stderr - Python logs INFO to stderr by default
            this.backendProcess.stderr?.on('data', (data) => {
                const output = data.toString();

                // Check if it's actually an error or just INFO/DEBUG logs
                if (output.includes('ERROR') || output.includes('CRITICAL') || output.includes('Exception') || output.includes('Traceback')) {
                    this.outputChannel.append(`❌ Error: ${output}`);
                } else if (output.includes('WARNING')) {
                    this.outputChannel.append(`⚠️ Warning: ${output}`);
                } else {
                    // It's just INFO or DEBUG output from Python logging
                    this.outputChannel.append(output);
                }
            });

            // Handle process exit
            this.backendProcess.on('exit', (code) => {
                this.outputChannel.appendLine(`Backend process exited with code ${code}`);
                this.isRunning = false;

                // Only restart if not manually stopped
                if (code !== 0 && this.startupAttempts < this.maxStartupAttempts && this.backendProcess) {
                    this.startupAttempts++;
                    this.outputChannel.appendLine(`Attempting restart (${this.startupAttempts}/${this.maxStartupAttempts})...`);

                    // Clean up the old process
                    this.backendProcess = null;

                    // Try to restart after a delay
                    setTimeout(async () => {
                        // Reset attempts if it's been a while since last attempt
                        if (Date.now() - (this.lastAttemptTime || 0) > 60000) {
                            this.startupAttempts = 0;
                        }
                        this.lastAttemptTime = Date.now();
                        await this.startBackend();
                    }, 3000);
                } else if (code !== 0) {
                    this.outputChannel.appendLine('❌ Backend failed to start after maximum attempts');
                    vscode.window.showErrorMessage('KI AutoAgent Backend failed to start. Please check the output for errors.');
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
     * Check if a port is in use
     */
    private async isPortInUse(port: number): Promise<boolean> {
        return new Promise((resolve) => {
            const server = net.createServer();

            server.once('error', (err: any) => {
                if (err.code === 'EADDRINUSE') {
                    resolve(true);
                } else {
                    resolve(false);
                }
            });

            server.once('listening', () => {
                server.close();
                resolve(false);
            });

            server.listen(port, '127.0.0.1');
        });
    }

    /**
     * Kill process on specific port
     */
    private async killProcessOnPort(port: number): Promise<boolean> {
        return new Promise((resolve) => {
            const platform = process.platform;

            if (platform === 'darwin' || platform === 'linux') {
                // First, get all PIDs using the port
                exec(`lsof -ti:${port}`, (error, stdout, stderr) => {
                    if (error || !stdout.trim()) {
                        this.outputChannel.appendLine(`⚠️ No process found on port ${port}`);
                        resolve(true); // Port is already free
                        return;
                    }

                    const pids = stdout.trim().split('\n').filter(pid => pid);
                    this.outputChannel.appendLine(`Found ${pids.length} process(es) on port ${port}: ${pids.join(', ')}`);

                    // Kill each process
                    let killedCount = 0;
                    let attemptedCount = 0;

                    pids.forEach((pid) => {
                        // Try SIGTERM first
                        exec(`kill -TERM ${pid} 2>/dev/null`, (termError) => {
                            if (termError) {
                                // If SIGTERM fails, try SIGKILL
                                exec(`kill -9 ${pid} 2>/dev/null`, (killError) => {
                                    attemptedCount++;
                                    if (!killError) {
                                        killedCount++;
                                        this.outputChannel.appendLine(`✅ Force killed PID ${pid}`);
                                    }

                                    if (attemptedCount === pids.length) {
                                        if (killedCount > 0) {
                                            this.outputChannel.appendLine(`✅ Killed ${killedCount}/${pids.length} process(es) on port ${port}`);
                                            resolve(true);
                                        } else {
                                            this.outputChannel.appendLine(`❌ Could not kill processes on port ${port}`);
                                            resolve(false);
                                        }
                                    }
                                });
                            } else {
                                attemptedCount++;
                                killedCount++;
                                this.outputChannel.appendLine(`✅ Gracefully terminated PID ${pid}`);

                                if (attemptedCount === pids.length) {
                                    this.outputChannel.appendLine(`✅ Killed ${killedCount}/${pids.length} process(es) on port ${port}`);
                                    resolve(true);
                                }
                            }
                        });
                    });
                });
            } else if (platform === 'win32') {
                // On Windows, use netstat and taskkill
                const command = `for /f "tokens=5" %a in ('netstat -aon ^| findstr :${port}') do taskkill /PID %a /F`;
                exec(command, (error, stdout, stderr) => {
                    if (error) {
                        this.outputChannel.appendLine(`⚠️ Could not kill process on port ${port}: ${error.message}`);
                        resolve(false);
                    } else {
                        this.outputChannel.appendLine(`✅ Killed process on port ${port}`);
                        resolve(true);
                    }
                });
            } else {
                this.outputChannel.appendLine(`⚠️ Unsupported platform: ${platform}`);
                resolve(false);
                return;
            }
        });
    }

    /**
     * Gracefully stop the backend with cleanup
     */
    public async stopBackend(force: boolean = false): Promise<void> {
        if (!this.backendProcess) {
            this.outputChannel.appendLine('No backend process to stop');
            return;
        }

        this.outputChannel.appendLine('Stopping backend...');

        // Try graceful shutdown first
        if (!force) {
            this.backendProcess.kill('SIGTERM');

            // Wait for graceful shutdown
            await new Promise((resolve) => {
                let timeout = setTimeout(() => {
                    this.outputChannel.appendLine('⚠️ Graceful shutdown timeout, forcing...');
                    this.backendProcess?.kill('SIGKILL');
                    resolve(void 0);
                }, 5000);

                this.backendProcess?.once('exit', () => {
                    clearTimeout(timeout);
                    this.outputChannel.appendLine('✅ Backend stopped gracefully');
                    resolve(void 0);
                });
            });
        } else {
            // Force kill immediately
            this.backendProcess.kill('SIGKILL');
            this.outputChannel.appendLine('✅ Backend force stopped');
        }

        this.backendProcess = null;
        this.isRunning = false;
        this.startupAttempts = 0;
    }

    /**
     * Dispose and cleanup
     */
    public dispose(): void {
        this.stopBackend();
        this.outputChannel.dispose();
    }
}