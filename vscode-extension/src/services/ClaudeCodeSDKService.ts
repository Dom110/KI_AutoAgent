/**
 * ClaudeCodeSDKService - Integration with official Claude Code SDK
 * Replaces the browser-based ClaudeWebService with direct SDK calls
 */
import * as vscode from 'vscode';
import * as child_process from 'child_process';
import * as path from 'path';

interface ClaudeCodeResponse {
    success: boolean;
    output?: string;
    error?: string;
    exitCode?: number;
}

interface ChatMessage {
    role: 'system' | 'user' | 'assistant';
    content: string;
}

export class ClaudeCodeSDKService {
    private claudeCodePath: string | undefined;
    private isAvailable: boolean = false;
    private workspaceFolder: string | undefined;
    
    constructor() {
        this.initializeService();
    }
    
    private async initializeService() {
        // Check if Claude Code is installed
        this.claudeCodePath = await this.findClaudeCode();
        this.isAvailable = !!this.claudeCodePath;
        
        // Get workspace folder
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (workspaceFolders && workspaceFolders.length > 0) {
            this.workspaceFolder = workspaceFolders[0].uri.fsPath;
        }
        
        if (this.isAvailable) {
            console.log('✅ Claude Code SDK found at:', this.claudeCodePath);
        } else {
            console.warn('⚠️ Claude Code not found. Please install: npm install -g @anthropic-ai/claude-code');
        }
    }
    
    private async findClaudeCode(): Promise<string | undefined> {
        return new Promise((resolve) => {
            // Try to find claude command
            child_process.exec('which claude', (error, stdout) => {
                if (!error && stdout) {
                    resolve(stdout.trim());
                } else {
                    // Try common locations
                    const commonPaths = [
                        '/usr/local/bin/claude',
                        '/usr/bin/claude',
                        path.join(process.env.HOME || '', '.npm-global/bin/claude'),
                        path.join(process.env.HOME || '', '.local/bin/claude')
                    ];
                    
                    for (const claudePath of commonPaths) {
                        try {
                            if (require('fs').existsSync(claudePath)) {
                                resolve(claudePath);
                                return;
                            }
                        } catch {}
                    }
                    
                    resolve(undefined);
                }
            });
        });
    }
    
    public async isServiceAvailable(): Promise<boolean> {
        if (!this.isAvailable) {
            // Try to find it again (user might have installed it)
            await this.initializeService();
        }
        return this.isAvailable;
    }
    
    public async chat(
        messages: ChatMessage[],
        temperature: number = 0.7,
        useTools: boolean = false
    ): Promise<string> {
        
        if (!await this.isServiceAvailable()) {
            throw new Error(
                'Claude Code SDK not available. Please install it:\n' +
                'npm install -g @anthropic-ai/claude-code\n\n' +
                'Then restart VS Code.'
            );
        }
        
        // Convert messages to prompt
        const prompt = this.messagesToPrompt(messages);
        
        // Execute claude command
        const response = await this.executeClaudeCommand(prompt, useTools);
        
        if (!response.success) {
            throw new Error(response.error || 'Claude Code execution failed');
        }
        
        return response.output || '';
    }
    
    public async executeWithTools(
        prompt: string,
        allowFileOperations: boolean = true,
        allowTerminalCommands: boolean = false
    ): Promise<string> {
        
        if (!await this.isServiceAvailable()) {
            throw new Error('Claude Code SDK not available');
        }
        
        const flags: string[] = [];
        
        // Add tool flags based on permissions
        if (allowFileOperations) {
            flags.push('--allow-file-operations');
        }
        
        if (allowTerminalCommands) {
            flags.push('--allow-terminal');
        }
        
        // Execute with tools enabled
        const response = await this.executeClaudeCommand(prompt, true, flags);
        
        if (!response.success) {
            throw new Error(response.error || 'Claude Code execution failed');
        }
        
        return response.output || '';
    }
    
    private messagesToPrompt(messages: ChatMessage[]): string {
        let prompt = '';
        
        for (const message of messages) {
            if (message.role === 'system') {
                prompt += `System: ${message.content}\n\n`;
            } else if (message.role === 'user') {
                prompt += `User: ${message.content}\n\n`;
            } else if (message.role === 'assistant') {
                prompt += `Assistant: ${message.content}\n\n`;
            }
        }
        
        return prompt.trim();
    }
    
    private async executeClaudeCommand(
        prompt: string,
        useTools: boolean = false,
        additionalFlags: string[] = []
    ): Promise<ClaudeCodeResponse> {
        
        return new Promise((resolve) => {
            if (!this.claudeCodePath) {
                resolve({
                    success: false,
                    error: 'Claude Code path not found'
                });
                return;
            }
            
            // Build command arguments
            const args: string[] = [];
            
            // Add tool flag if needed
            if (useTools) {
                args.push('--tools');
            }
            
            // Add additional flags
            args.push(...additionalFlags);
            
            // Add the prompt (escaped for shell)
            args.push(JSON.stringify(prompt));
            
            // Execute command
            const options: child_process.ExecOptions = {
                cwd: this.workspaceFolder,
                maxBuffer: 10 * 1024 * 1024, // 10MB buffer for large responses
                timeout: 60000, // 60 second timeout
                encoding: 'utf8' // Ensure stdout is always a string
            };
            
            const command = `${this.claudeCodePath} ${args.join(' ')}`;
            
            child_process.exec(command, options, (error, stdout, stderr) => {
                if (error) {
                    resolve({
                        success: false,
                        error: error.message,
                        exitCode: error.code
                    });
                } else {
                    resolve({
                        success: true,
                        output: stdout.toString(), // Convert to string to fix TypeScript error
                        exitCode: 0
                    });
                }
            });
        });
    }
    
    public async streamChat(
        messages: ChatMessage[],
        onChunk: (chunk: string) => void,
        temperature: number = 0.7
    ): Promise<void> {
        
        if (!await this.isServiceAvailable()) {
            throw new Error('Claude Code SDK not available');
        }
        
        const prompt = this.messagesToPrompt(messages);
        
        return new Promise((resolve, reject) => {
            if (!this.claudeCodePath) {
                reject(new Error('Claude Code path not found'));
                return;
            }
            
            // Use spawn for streaming output
            const claudeProcess = child_process.spawn(
                this.claudeCodePath,
                ['--stream', JSON.stringify(prompt)],
                {
                    cwd: this.workspaceFolder,
                    shell: true
                }
            );
            
            let buffer = '';
            
            claudeProcess.stdout.on('data', (data) => {
                const chunk = data.toString();
                buffer += chunk;
                
                // Process complete lines
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';
                
                for (const line of lines) {
                    if (line.trim()) {
                        onChunk(line);
                    }
                }
            });
            
            claudeProcess.stderr.on('data', (data) => {
                console.error('Claude Code stderr:', data.toString());
            });
            
            claudeProcess.on('close', (code) => {
                // Send any remaining buffer
                if (buffer.trim()) {
                    onChunk(buffer);
                }
                
                if (code === 0) {
                    resolve();
                } else {
                    reject(new Error(`Claude Code exited with code ${code}`));
                }
            });
            
            claudeProcess.on('error', (error) => {
                reject(error);
            });
        });
    }
    
    public async installClaudeCode(): Promise<boolean> {
        // Helper to install Claude Code SDK
        return new Promise((resolve) => {
            vscode.window.showInformationMessage(
                'Claude Code SDK is not installed. Would you like to install it now?',
                'Install',
                'Later'
            ).then(selection => {
                if (selection === 'Install') {
                    // Open terminal and run install command
                    const terminal = vscode.window.createTerminal('Install Claude Code');
                    terminal.show();
                    terminal.sendText('npm install -g @anthropic-ai/claude-code');
                    
                    // Wait a bit and check again
                    setTimeout(async () => {
                        await this.initializeService();
                        resolve(this.isAvailable);
                    }, 10000);
                } else {
                    resolve(false);
                }
            });
        });
    }
    
    public async checkAuthentication(): Promise<boolean> {
        if (!await this.isServiceAvailable()) {
            return false;
        }
        
        // Try a simple command to check if authenticated
        const response = await this.executeClaudeCommand('Hello, are you there?', false);
        return response.success;
    }
    
    public getServiceInfo(): {
        available: boolean;
        path?: string;
        workspace?: string;
    } {
        return {
            available: this.isAvailable,
            path: this.claudeCodePath,
            workspace: this.workspaceFolder
        };
    }
}