/**
 * ClaudeCodeService - Integration with Claude Code CLI
 * Based on claude-code-chat implementation
 * 
 * Requires: npm install -g @anthropic-ai/claude-code
 * This installs the 'claude' CLI command that this service uses
 */
import * as vscode from 'vscode';
import { spawn, exec, ChildProcess } from 'child_process';
import { EventEmitter } from 'events';

export interface ClaudeMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
}

export interface ClaudeResponse {
    content: string;
    metadata?: {
        model?: string;
        usage?: {
            inputTokens: number;
            outputTokens: number;
            totalCost?: number;
        };
    };
}

export interface ClaudeOptions {
    model?: 'opus' | 'sonnet' | 'default';
    temperature?: number;
    maxTokens?: number;
}

export class ClaudeCodeService extends EventEmitter {
    private outputChannel: vscode.OutputChannel;
    private currentProcess: ChildProcess | null = null;
    private seenToolsInSession: Set<string> | null = null;
    private pendingTools: Map<string, any> = new Map(); // Store tool calls by ID
    private toolResults: Map<string, any> = new Map(); // Store tool results by ID
    private toolGroupBuffer: any[] = []; // Buffer for grouping similar tools
    private lastToolName: string | null = null;
    private hasStartedTextOutput = false;
    
    constructor() {
        super();
        this.outputChannel = vscode.window.createOutputChannel('Claude Code Service');
    }

    /**
     * Send a message to Claude using the Claude Code CLI with JSON streaming
     */
    async sendMessage(
        message: string, 
        options: ClaudeOptions = {}
    ): Promise<ClaudeResponse> {
        // Try simple text mode first as fallback
        try {
            return await this.sendStreamJsonMessage(message, options);
        } catch (error) {
            this.outputChannel.appendLine('[ClaudeCodeService] Stream JSON failed, falling back to text mode');
            return await this.sendSimpleMessage(message, options);
        }
    }

    /**
     * Send a message using simple text output (more reliable)
     */
    async sendSimpleMessage(
        message: string,
        options: ClaudeOptions = {}
    ): Promise<ClaudeResponse> {
        return new Promise((resolve, reject) => {
            try {
                const args = [
                    '--print', // Non-interactive mode
                    '--output-format', 'text' // Simple text output
                    // Allow tools - Claude will use them intelligently
                ];

                if (options.model && options.model !== 'default') {
                    args.push('--model', options.model);
                }

                this.outputChannel.appendLine(`[ClaudeCodeService] Using simple text mode with args: ${args.join(' ')}`);

                const claudeProcess = spawn('claude', args, {
                    shell: process.platform === 'win32',
                    stdio: ['pipe', 'pipe', 'pipe']
                });

                let output = '';
                let errorOutput = '';

                claudeProcess.stdout.on('data', (data) => {
                    output += data.toString();
                });

                claudeProcess.stderr.on('data', (data) => {
                    errorOutput += data.toString();
                });

                claudeProcess.on('exit', (code) => {
                    if (code === 0 || output.length > 0) {
                        resolve({
                            content: output.trim(),
                            metadata: { }
                        });
                    } else {
                        reject(new Error(`Claude CLI failed: ${errorOutput || 'No output'}`));
                    }
                });

                claudeProcess.on('error', (error) => {
                    reject(error);
                });

                // Send the message
                if (claudeProcess.stdin) {
                    claudeProcess.stdin.write(message);
                    claudeProcess.stdin.end();
                }
            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Send a message with streaming support for real-time updates
     */
    async sendStreamingMessage(
        message: string,
        options: ClaudeOptions & {
            onPartialResponse?: (content: string) => void;
            onMetadata?: (metadata: any) => void;
        } = {}
    ): Promise<ClaudeResponse> {
        this.outputChannel.appendLine('[ClaudeCodeService] Starting streaming message...');
        
        return new Promise((resolve, reject) => {
            try {
                // Prepare CLI arguments for streaming
                const args = [
                    '--print', // Non-interactive mode
                    '--verbose', // Required for stream-json
                    '--output-format', 'stream-json', // Stream JSON output
                    '--include-partial-messages' // Include partial messages as they arrive
                ];

                // Add model if specified
                if (options.model && options.model !== 'default') {
                    args.push('--model', options.model);
                }

                this.outputChannel.appendLine(`[ClaudeCodeService] Spawning claude CLI with streaming`);

                const claudeProcess = spawn('claude', args, {
                    shell: process.platform === 'win32',
                    stdio: ['pipe', 'pipe', 'pipe']
                });

                this.currentProcess = claudeProcess;

                let responseContent = '';
                let metadata: any = {};
                let hasReceivedText = false;
                let toolUseDetected = false;
                let buffer = '';
                const seenTools = new Set<string>(); // Track tools to prevent duplicates

                // Handle stdout (JSON stream)
                claudeProcess.stdout.on('data', (data) => {
                    buffer += data.toString();
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || ''; // Keep last incomplete line in buffer

                    for (const line of lines) {
                        if (line.trim()) {
                            try {
                                const jsonData = JSON.parse(line.trim());
                                
                                this.processJsonStreamData(jsonData, (content, meta, eventType) => {
                                    if (content) {
                                        responseContent += content;
                                        hasReceivedText = true;
                                        
                                        // Call the partial response callback for real-time updates
                                        if (options.onPartialResponse) {
                                            options.onPartialResponse(content);
                                        }
                                    }
                                    if (meta) {
                                        metadata = { ...metadata, ...meta };
                                        
                                        // Call metadata callback
                                        if (options.onMetadata) {
                                            options.onMetadata(meta);
                                        }
                                    }
                                    if (eventType === 'tool_use') {
                                        toolUseDetected = true;
                                        // Don't terminate - let Claude continue using tools
                                        this.outputChannel.appendLine(`[ClaudeCodeService] Tool detected - continuing execution`);
                                    }
                                    // Remove this duplicate tool_info handling - we handle it elsewhere
                                });
                            } catch (error) {
                                this.outputChannel.appendLine(`[ClaudeCodeService] Failed to parse JSON: ${line.substring(0, 100)}`);
                            }
                        }
                    }
                });

                // Handle stderr
                claudeProcess.stderr.on('data', (data) => {
                    const error = data.toString();
                    this.outputChannel.appendLine(`[ClaudeCodeService] Claude CLI stderr: ${error}`);
                });

                // Handle process exit
                claudeProcess.on('exit', (code, signal) => {
                    this.currentProcess = null;
                    
                    if (code === 0 || responseContent.length > 0) {
                        resolve({
                            content: responseContent || 'No response received from Claude',
                            metadata: metadata
                        });
                    } else {
                        reject(new Error(`Claude process exited with code ${code} and no response`));
                    }
                });

                // Handle process error
                claudeProcess.on('error', (error) => {
                    this.currentProcess = null;
                    reject(error);
                });

                // Send the message
                if (claudeProcess.stdin) {
                    claudeProcess.stdin.write(message);
                    claudeProcess.stdin.end();
                }
            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Send a message using stream JSON output (advanced)
     */
    async sendStreamJsonMessage(
        message: string, 
        options: ClaudeOptions = {}
    ): Promise<ClaudeResponse> {
        return new Promise((resolve, reject) => {
            try {
                // Prepare CLI arguments
                const args = [
                    '--print', // Non-interactive mode
                    '--verbose', // Required for stream-json
                    '--output-format', 'stream-json', // Stream JSON output
                    '--include-partial-messages' // Include partial messages as they arrive
                    // Allow tools - we'll filter out tool calls and only show text
                ];

                // Add model if specified
                if (options.model && options.model !== 'default') {
                    args.push('--model', options.model);
                }

                // Claude CLI doesn't support temperature or max-tokens
                // These would need to be configured globally in Claude settings

                this.outputChannel.appendLine(`[ClaudeCodeService] Spawning claude CLI with args: ${args.join(' ')}`);
                this.outputChannel.appendLine(`[ClaudeCodeService] Message length: ${message.length} characters`);
                this.outputChannel.appendLine(`[ClaudeCodeService] First 200 chars of message: ${message.substring(0, 200)}...`);

                // Spawn the Claude process
                const claudeProcess = spawn('claude', args, {
                    shell: process.platform === 'win32',
                    stdio: ['pipe', 'pipe', 'pipe'],
                    env: {
                        ...process.env,
                        FORCE_COLOR: '0',
                        NO_COLOR: '1'
                    }
                });

                this.currentProcess = claudeProcess;

                let rawOutput = '';
                let responseContent = '';
                let metadata: any = {};

                // Handle stdout (JSON stream)
                claudeProcess.stdout.on('data', (data) => {
                    const chunk = data.toString();
                    this.outputChannel.appendLine(`[ClaudeCodeService] Raw chunk: ${chunk.substring(0, 200)}`);
                    rawOutput += chunk;
                    const lines = rawOutput.split('\n');
                    rawOutput = lines.pop() || '';

                    for (const line of lines) {
                        if (line.trim()) {
                            try {
                                const jsonData = JSON.parse(line.trim());
                                this.outputChannel.appendLine(`[ClaudeCodeService] Parsed JSON type: ${jsonData.type}`);
                                
                                this.processJsonStreamData(jsonData, (content, meta, eventType) => {
                                    if (content) {
                                        responseContent += content;
                                        hasReceivedText = true;
                                        this.outputChannel.appendLine(`[ClaudeCodeService] Added content: "${content.substring(0, 50)}..."`);
                                    }
                                    if (meta) {
                                        metadata = { ...metadata, ...meta };
                                        this.outputChannel.appendLine(`[ClaudeCodeService] Updated metadata: ${JSON.stringify(meta)}`);
                                    }
                                    if (eventType === 'tool_use') {
                                        toolUseDetected = true;
                                        this.outputChannel.appendLine(`[ClaudeCodeService] Tool use detected - will terminate after text`);
                                        
                                        // If we have text and Claude is using tools, terminate the process
                                        // We can't handle tool results, so we just take the text we got
                                        if (hasReceivedText && responseContent.length > 0) {
                                            this.outputChannel.appendLine(`[ClaudeCodeService] Terminating process - we have text but can't handle tools`);
                                            claudeProcess.kill('SIGTERM');
                                        }
                                    }
                                });
                            } catch (error) {
                                this.outputChannel.appendLine(`[ClaudeCodeService] Failed to parse JSON: ${line.substring(0, 100)}`);
                            }
                        }
                    }
                });

                // Handle stderr
                claudeProcess.stderr.on('data', (data) => {
                    const error = data.toString();
                    this.outputChannel.appendLine(`[ClaudeCodeService] Claude CLI stderr: ${error}`);
                    // Don't treat stderr as fatal - claude CLI may output debug info to stderr
                });

                // Track if we've received text content
                let hasReceivedText = false;
                let toolUseDetected = false;

                // Handle process exit
                claudeProcess.on('exit', (code, signal) => {
                    this.currentProcess = null;
                    this.outputChannel.appendLine(`[ClaudeCodeService] Process exited with code: ${code}, signal: ${signal}`);
                    this.outputChannel.appendLine(`[ClaudeCodeService] Total response length: ${responseContent.length} characters`);
                    
                    if (code === 0 || responseContent.length > 0) {
                        // Even if exit code is non-zero, if we got content, return it
                        this.outputChannel.appendLine(`[ClaudeCodeService] FINAL RESPONSE: "${responseContent.substring(0, 500)}..."`);
                        resolve({
                            content: responseContent || 'No response received from Claude',
                            metadata: metadata
                        });
                    } else {
                        reject(new Error(`Claude process exited with code ${code} and no response`))
                    }
                });

                // Handle process error
                claudeProcess.on('error', (error) => {
                    this.currentProcess = null;
                    
                    if (error.message.includes('ENOENT')) {
                        reject(new Error(
                            'Claude Code CLI not found. Please install it with: npm install -g @anthropic-ai/claude-code'
                        ));
                    } else {
                        reject(error);
                    }
                });

                // Send the message
                if (claudeProcess.stdin) {
                    claudeProcess.stdin.write(message + '\n');
                    claudeProcess.stdin.end();
                } else {
                    reject(new Error('Failed to write to Claude process stdin'));
                }

            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Clean tool markers from content before sending to UI
     */
    private cleanToolMarkers(content: string): string {
        // Remove tool detail markers but keep the actual text content
        return content
            .replace(/<<TOOL>>.*?<<TOOL_END>>/gs, '') // Remove tool call details
            .replace(/<<TOOL_RESULT>>.*?<<TOOL_RESULT_END>>/gs, '') // Remove tool result details
            .replace(/<<THINKING>>.*?<<THINKING_END>>/gs, '') // Remove thinking markers
            .replace(/🛠️ \*?Claude is using tools.*?\*?\n*/g, '') // Remove tool announcements
            .trim();
    }

    /**
     * Process JSON stream data from Claude
     */
    private processJsonStreamData(
        data: any,
        callback: (content: string | null, metadata: any | null, eventType?: string) => void
    ): void {
        // Handle Claude Code CLI specific events
        if (data.type === 'system') {
            // Handle different system subtypes
            if (data.subtype === 'init') {
                this.outputChannel.appendLine(`[ClaudeCodeService] System init: ${JSON.stringify(data.tools || []).substring(0, 100)}`);
                if (data.session_id) {
                    callback(null, { sessionId: data.session_id });
                }
                // Don't send initialization message to avoid clutter
            } else if (data.subtype === 'error') {
                this.outputChannel.appendLine(`[ClaudeCodeService] System error: ${data.message || 'Unknown error'}`);
                // Clean error messages too
                const cleanError = `\n⚠️ **System Error:** ${data.message || 'An unexpected error occurred'}\n`;
                callback(cleanError, null);
                callback(null, null, 'error');
            } else {
                this.outputChannel.appendLine(`[ClaudeCodeService] System event (${data.subtype})`);
            }
        }
        // Handle assistant messages (text and tool use)
        else if (data.type === 'assistant' && data.message) {
            if (data.message.content && Array.isArray(data.message.content)) {
                for (const content of data.message.content) {
                    // Only show text content to user, ignore tool_use content
                    if (content.type === 'text' && content.text) {
                        callback(content.text, null);
                    } else if (content.type === 'tool_use') {
                        // Log tool use and notify user
                        this.outputChannel.appendLine(`[ClaudeCodeService] Tool use: ${content.name} (${content.id})`);
                        this.outputChannel.appendLine(`[ClaudeCodeService] Tool input: ${JSON.stringify(content.input)}`);
                        
                        // Store tool call for later result matching
                        this.pendingTools.set(content.id, {
                            name: content.name,
                            input: content.input,
                            id: content.id
                        });
                        
                        // Check if we should group this tool with previous ones
                        if (this.lastToolName === content.name) {
                            // Same tool type, add to buffer
                            this.toolGroupBuffer.push({
                                name: content.name,
                                input: content.input,
                                id: content.id
                            });
                        } else {
                            // Different tool or first tool, flush previous buffer if any
                            this.flushToolGroup(callback);
                            // Start new buffer
                            this.toolGroupBuffer = [{
                                name: content.name,
                                input: content.input,
                                id: content.id
                            }];
                            this.lastToolName = content.name;
                        }
                    }
                }
            }
            // Handle metadata if present
            if (data.message.model || data.message.id) {
                callback(null, {
                    model: data.message.model,
                    id: data.message.id
                });
            }
        }
        // Handle user messages (tool results)
        else if (data.type === 'user' && data.message) {
            // Tool results - store them and send update
            if (data.message.content && Array.isArray(data.message.content)) {
                for (const content of data.message.content) {
                    if (content.type === 'tool_result') {
                        this.outputChannel.appendLine(`[ClaudeCodeService] Tool result for ${content.tool_use_id}: ${content.content?.substring(0, 200)}`);
                        // Store the result
                        const result = content.content || content.output || '';
                        this.toolResults.set(content.tool_use_id, result);
                        
                        // Check if this completes any pending tools in the buffer
                        const pendingTool = this.pendingTools.get(content.tool_use_id);
                        if (pendingTool) {
                            pendingTool.result = result;
                            
                            // Find tool in buffer and update it
                            const toolInBuffer = this.toolGroupBuffer.find(t => t.id === content.tool_use_id);
                            if (toolInBuffer) {
                                toolInBuffer.result = result;
                            }
                        }
                        
                        // Don't send tool result markers to UI - they're handled internally
                    }
                }
            }
        }
        // Handle stream events from Claude CLI (new format)
        else if (data.type === 'stream_event' && data.event) {
            const event = data.event;
            
            // Handle content block deltas (text chunks)
            if (event.type === 'content_block_delta' && event.delta) {
                if (event.delta.type === 'text_delta' && event.delta.text) {
                    // Ensure tools are flushed before sending text
                    if (this.toolGroupBuffer.length > 0) {
                        this.flushToolGroup(callback);
                    }
                    callback(event.delta.text, null);
                }
                // Handle thinking deltas (Claude's reasoning)
                else if (event.delta.type === 'thinking_delta' && event.delta.text) {
                    // Log thinking but don't show to user (can be enabled later)
                    this.outputChannel.appendLine(`[ClaudeCodeService] Thinking: ${event.delta.text.substring(0, 100)}`);
                }
                // Accumulate tool input for later use
                else if (event.delta.type === 'input_json_delta') {
                    // We could accumulate the partial JSON here if needed
                    this.outputChannel.appendLine(`[ClaudeCodeService] Tool input delta: ${event.delta.partial_json?.substring(0, 100)}`);
                }
            }
            // Handle content block start
            else if (event.type === 'content_block_start' && event.content_block) {
                if (event.content_block.type === 'tool_use') {
                    this.outputChannel.appendLine(`[ClaudeCodeService] Tool use starting: ${event.content_block.name}`);
                    // Tool notification will be sent when we receive the complete input
                } else if (event.content_block.type === 'text') {
                    this.outputChannel.appendLine(`[ClaudeCodeService] Text block starting`);
                    // Flush any pending tool groups before starting text
                    this.flushToolGroup(callback);
                    this.hasStartedTextOutput = true;
                } else if (event.content_block.type === 'thinking') {
                    this.outputChannel.appendLine(`[ClaudeCodeService] Thinking block starting`);
                    // Don't send thinking markers to UI
                }
            }
            // Handle content block stop
            else if (event.type === 'content_block_stop') {
                this.outputChannel.appendLine(`[ClaudeCodeService] Content block stopped (index: ${event.index})`);
            }
            // Handle message start (metadata)
            else if (event.type === 'message_start' && event.message) {
                callback(null, { 
                    model: event.message.model,
                    id: event.message.id 
                });
            }
            // Handle message delta (usage info and stop reasons)
            else if (event.type === 'message_delta') {
                if (event.usage) {
                    callback(null, {
                        usage: {
                            inputTokens: event.usage.input_tokens || 0,
                            outputTokens: event.usage.output_tokens || 0,
                            cacheCreationInputTokens: event.usage.cache_creation_input_tokens || 0,
                            cacheReadInputTokens: event.usage.cache_read_input_tokens || 0
                        }
                    });
                }
                if (event.delta?.stop_reason) {
                    this.outputChannel.appendLine(`[ClaudeCodeService] Stop reason: ${event.delta.stop_reason}`);
                    callback(null, { stopReason: event.delta.stop_reason });
                    
                    // Don't send tool usage notifications - tools are shown in separate bubbles
                }
            }
            // Handle message stop
            else if (event.type === 'message_stop') {
                this.outputChannel.appendLine(`[ClaudeCodeService] Message stopped`);
                // Flush any remaining tool groups
                this.flushToolGroup(callback);
                // Clear for next message
                if (this.seenToolsInSession) {
                    this.seenToolsInSession.clear();
                }
                this.pendingTools.clear();
                this.toolResults.clear();
                this.toolGroupBuffer = [];
                this.lastToolName = null;
                this.hasStartedTextOutput = false;
                callback(null, null, 'message_stop');
            }
            // Handle error events
            else if (event.type === 'error') {
                this.outputChannel.appendLine(`[ClaudeCodeService] Stream error: ${event.error?.message || 'Unknown error'}`);
                callback(null, { error: event.error }, 'error');
            }
            // Handle ping events (keep-alive)
            else if (event.type === 'ping') {
                this.outputChannel.appendLine(`[ClaudeCodeService] Ping received`);
            }
        }
        // Handle result event (final with detailed info)
        else if (data.type === 'result') {
            this.outputChannel.appendLine(`[ClaudeCodeService] Final result received`);
            
            // Extract detailed result metadata
            const resultMetadata: any = {
                resultType: data.subtype || 'unknown'
            };
            
            if (data.total_cost_usd !== undefined) {
                resultMetadata.totalCostUsd = data.total_cost_usd;
            }
            if (data.duration_ms !== undefined) {
                resultMetadata.durationMs = data.duration_ms;
            }
            if (data.duration_api_ms !== undefined) {
                resultMetadata.durationApiMs = data.duration_api_ms;
            }
            if (data.num_turns !== undefined) {
                resultMetadata.numTurns = data.num_turns;
            }
            if (data.is_error !== undefined) {
                resultMetadata.isError = data.is_error;
            }
            
            callback(null, resultMetadata, 'result');
        }
        // Handle older format (fallback)
        else if (data.type === 'message') {
            if (data.role === 'assistant' && data.content) {
                callback(data.content, null);
            }
        } else if (data.type === 'content') {
            if (data.text) {
                callback(data.text, null);
            }
        }
        // Debug unknown types
        else {
            this.outputChannel.appendLine(`[ClaudeCodeService] Unknown data type: ${JSON.stringify(data).substring(0, 200)}`);
        }
    }

    /**
     * Check if Claude CLI is available
     */
    async isAvailable(): Promise<boolean> {
        return new Promise((resolve) => {
            this.outputChannel.appendLine('[ClaudeCodeService] Checking Claude Code CLI availability...');
            exec('which claude', (error, stdout, stderr) => {
                if (error) {
                    this.outputChannel.appendLine('[ClaudeCodeService] Claude Code CLI not found in PATH');
                    // Try another method
                    exec('claude --version', (error2, stdout2, stderr2) => {
                        if (error2) {
                            this.outputChannel.appendLine('[ClaudeCodeService] Claude Code CLI not available');
                            this.outputChannel.appendLine('[ClaudeCodeService] Install with: npm install -g @anthropic-ai/claude-code');
                            resolve(false);
                        } else {
                            this.outputChannel.appendLine(`[ClaudeCodeService] Claude Code CLI found (version check): ${stdout2.trim()}`);
                            resolve(true);
                        }
                    });
                } else {
                    this.outputChannel.appendLine(`[ClaudeCodeService] Claude Code CLI found at: ${stdout.trim()}`);
                    // Also get version
                    exec('claude --version', (verError, verStdout) => {
                        if (!verError) {
                            this.outputChannel.appendLine(`[ClaudeCodeService] Version: ${verStdout.trim()}`);
                        }
                    });
                    resolve(true);
                }
            });
        });
    }

    /**
     * Test Claude CLI with a simple message
     */
    async testConnection(): Promise<{ success: boolean; message: string }> {
        try {
            this.outputChannel.appendLine('[ClaudeCodeService] Testing Claude CLI connection...');
            
            const isAvailable = await this.isAvailable();
            if (!isAvailable) {
                return {
                    success: false,
                    message: 'Claude Code CLI not installed. Install with: npm install -g @anthropic-ai/claude-code'
                };
            }
            
            // Try a simple test message using text mode for reliability
            const response = await this.sendSimpleMessage('Hi, just testing the connection. Reply with "Connection successful!"', {
                model: 'default'
            });
            
            if (response.content && response.content.length > 0) {
                this.outputChannel.appendLine('[ClaudeCodeService] Test successful!');
                return {
                    success: true,
                    message: `Claude CLI working! Response: ${response.content.substring(0, 100)}`
                };
            } else {
                return {
                    success: false,
                    message: 'Claude CLI responded but with empty content'
                };
            }
        } catch (error) {
            const errorMsg = (error as Error).message;
            this.outputChannel.appendLine(`[ClaudeCodeService] Test failed: ${errorMsg}`);
            return {
                success: false,
                message: `Claude CLI test failed: ${errorMsg}`
            };
        }
    }

    /**
     * Cancel current Claude process if running
     */
    cancel(): void {
        if (this.currentProcess) {
            this.currentProcess.kill();
            this.currentProcess = null;
        }
    }

    /**
     * Flush grouped tools - send notification for grouped tools
     */
    private flushToolGroup(callback: (content: string | null, metadata: any | null, type?: string) => void): void {
        if (this.toolGroupBuffer.length === 0) return;
        
        const toolName = this.toolGroupBuffer[0].name;
        let emoji = '🔧';
        let groupedMessage = '';
        
        // Get emoji for this tool type
        switch(toolName) {
            case 'TodoWrite': emoji = '📝'; break;
            case 'Bash': emoji = '⚡'; break;
            case 'Read': emoji = '📄'; break;
            case 'Write': case 'Edit': case 'MultiEdit': emoji = '✏️'; break;
            case 'Grep': emoji = '🔍'; break;
            case 'Glob': emoji = '📁'; break;
            case 'WebSearch': emoji = '🌐'; break;
            case 'WebFetch': emoji = '🔗'; break;
            case 'Task': emoji = '🤖'; break;
        }
        
        // Format grouped message
        if (this.toolGroupBuffer.length === 1) {
            // Single tool - format normally
            const tool = this.toolGroupBuffer[0];
            groupedMessage = this.formatToolMessage(tool.name, tool.input);
            
            // Add result if available
            const result = this.toolResults.get(tool.id);
            if (result) {
                const truncatedResult = result.length > 200 ? result.substring(0, 200) + '...' : result;
                groupedMessage += `\n\n**Result:**\n${truncatedResult}`;
            }
        } else {
            // Multiple tools of same type - group them
            groupedMessage = `${emoji} **${toolName} (${this.toolGroupBuffer.length} operations)**\n\n`;
            for (const tool of this.toolGroupBuffer) {
                const details = this.formatToolDetails(tool.name, tool.input);
                groupedMessage += `• ${details}\n`;
                
                // Add result if available
                const result = this.toolResults.get(tool.id);
                if (result) {
                    const truncatedResult = result.length > 100 ? result.substring(0, 100) + '...' : result;
                    groupedMessage += `  → ${truncatedResult}\n`;
                }
            }
        }
        
        // Send the tool notification as a separate system message (without markers)
        // The UI will handle this as a blue bubble
        callback(`SYSTEM_TOOL_MESSAGE:${groupedMessage}`, null, 'tool_info');
        
        // Clear the buffer
        this.toolGroupBuffer = [];
    }
    
    /**
     * Format tool details (without emoji, for grouped display)
     */
    private formatToolDetails(toolName: string, input: any): string {
        switch(toolName) {
            case 'TodoWrite':
                const todoCount = input?.todos?.length || 0;
                return `${todoCount} tasks`;
            
            case 'Bash':
                const command = input?.command || '';
                return command;
            
            case 'Read':
                const readPath = input?.file_path || '';
                const fileName = readPath.split('/').pop() || readPath;
                let readDetails = fileName;
                if (input?.offset || input?.limit) {
                    readDetails += ` (lines ${input.offset || 0}-${(input.offset || 0) + (input.limit || 0)})`;
                }
                return readDetails;
            
            case 'Write':
                const writePath = input?.file_path || '';
                const writeFile = writePath.split('/').pop() || writePath;
                return writeFile;
            
            case 'Edit':
            case 'MultiEdit':
                const editPath = input?.file_path || '';
                const editFile = editPath.split('/').pop() || editPath;
                let editDetails = editFile;
                if (toolName === 'MultiEdit' && input?.edits) {
                    editDetails += ` (${input.edits.length} edits)`;
                }
                return editDetails;
            
            case 'Grep':
                const pattern = input?.pattern || '';
                return `"${pattern.substring(0, 30)}${pattern.length > 30 ? '...' : ''}"`;
            
            case 'Glob':
                const globPattern = input?.pattern || '';
                return globPattern;
            
            case 'WebSearch':
                const query = input?.query || '';
                return `"${query.substring(0, 40)}${query.length > 40 ? '...' : ''}"`;
            
            case 'WebFetch':
                const url = input?.url || '';
                const domain = url.match(/^https?:\/\/([^\/]+)/)?.[1] || url;
                return domain;
            
            case 'Task':
                const subagent = input?.subagent_type || 'agent';
                return subagent;
            
            default:
                return JSON.stringify(input).substring(0, 50);
        }
    }

    /**
     * Format tool message with parameters
     */
    private formatToolMessage(toolName: string, input: any): string {
        let emoji = '🔧';
        let details = '';
        
        switch(toolName) {
            case 'TodoWrite':
                emoji = '📝';
                const todoCount = input?.todos?.length || 0;
                details = `TodoWrite\n${todoCount} tasks`;
                break;
            
            case 'Bash':
                emoji = '⚡';
                const command = input?.command || '';
                details = `Bash\n${command}`;
                break;
            
            case 'Read':
                emoji = '📄';
                const readPath = input?.file_path || '';
                const fileName = readPath.split('/').pop() || readPath;
                details = `Read\n${fileName}`;
                if (input?.offset || input?.limit) {
                    details += ` (lines ${input.offset || 0}-${(input.offset || 0) + (input.limit || 0)})`;
                }
                break;
            
            case 'Write':
                emoji = '✏️';
                const writePath = input?.file_path || '';
                const writeFile = writePath.split('/').pop() || writePath;
                details = `Write\n${writeFile}`;
                break;
            
            case 'Edit':
            case 'MultiEdit':
                emoji = '✏️';
                const editPath = input?.file_path || '';
                const editFile = editPath.split('/').pop() || editPath;
                details = `${toolName}\n${editFile}`;
                if (toolName === 'MultiEdit' && input?.edits) {
                    details += ` (${input.edits.length} edits)`;
                }
                break;
            
            case 'Grep':
                emoji = '🔍';
                const pattern = input?.pattern || '';
                details = `Grep\n"${pattern.substring(0, 30)}${pattern.length > 30 ? '...' : ''}"`;
                break;
            
            case 'Glob':
                emoji = '📁';
                const globPattern = input?.pattern || '';
                details = `Glob\n${globPattern}`;
                break;
            
            case 'WebSearch':
                emoji = '🌐';
                const query = input?.query || '';
                details = `WebSearch\n"${query.substring(0, 40)}${query.length > 40 ? '...' : ''}"`;
                break;
            
            case 'WebFetch':
                emoji = '🔗';
                const url = input?.url || '';
                const domain = url.match(/^https?:\/\/([^\/]+)/)?.[1] || url;
                details = `WebFetch\n${domain}`;
                break;
            
            case 'Task':
                emoji = '🤖';
                const subagent = input?.subagent_type || 'agent';
                details = `Task\n${subagent}`;
                break;
            
            default:
                details = `${toolName}`;
        }
        
        return `${emoji} **${details}**`;
    }

    dispose(): void {
        this.cancel();
        this.outputChannel.dispose();
    }
}

// Singleton instance
let instance: ClaudeCodeService | null = null;

export function getClaudeCodeService(): ClaudeCodeService {
    if (!instance) {
        instance = new ClaudeCodeService();
    }
    return instance;
}