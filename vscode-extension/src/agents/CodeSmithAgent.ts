/**
 * CodeSmithClaude - Senior Python/Web Developer
 * Powered by Claude 3.5 Sonnet for code implementation and optimization
 */
import * as vscode from 'vscode';
import { ChatAgent } from './base/ChatAgent';
import { AgentConfig, TaskRequest, TaskResult, WorkflowStep } from '../types';
import { VSCodeMasterDispatcher } from '../core/VSCodeMasterDispatcher';
import { AnthropicService } from '../utils/AnthropicService';
import { getClaudeCodeService, ClaudeCodeService } from '../services/ClaudeCodeService';

export class CodeSmithAgent extends ChatAgent {
    private anthropicService: AnthropicService;
    private claudeCodeService: ClaudeCodeService;

    constructor(context: vscode.ExtensionContext, dispatcher: VSCodeMasterDispatcher) {
        const config: AgentConfig = {
            participantId: 'ki-autoagent.codesmith',
            name: 'codesmith',
            fullName: 'CodeSmithClaude',
            description: 'Senior Python/Web Developer powered by Claude 4.1 Sonnet',
            model: 'claude-4.1-sonnet-20250920',
            iconPath: vscode.Uri.joinPath(context.extensionUri, 'media', 'claude-icon.svg'),
            capabilities: [
                'Python Development',
                'Web Development',
                'API Implementation',
                'Testing & TDD',
                'Code Optimization',
                'Framework Integration'
            ],
            commands: [
                { name: 'implement', description: 'Implement code based on specifications', handler: 'handleImplementCommand' },
                { name: 'fix', description: 'Fix bugs and issues in code', handler: 'handleFixCommand' },
                { name: 'debug', description: 'Debug and resolve issues', handler: 'handleDebugCommand' },
                { name: 'optimize', description: 'Optimize existing code for performance', handler: 'handleOptimizeCommand' },
                { name: 'refactor', description: 'Refactor code for better structure', handler: 'handleRefactorCommand' },
                { name: 'modernize', description: 'Modernize legacy code', handler: 'handleModernizeCommand' },
                { name: 'test', description: 'Generate comprehensive test suites', handler: 'handleTestCommand' }
            ]
        };

        super(config, context, dispatcher);
        this.anthropicService = new AnthropicService();
        this.claudeCodeService = getClaudeCodeService();
    }

    protected async handleRequest(
        request: vscode.ChatRequest,
        context: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
        const validationResult = await this.validateServiceConfig(stream);
        if (!validationResult) {
            return;
        }

        const command = request.command;
        const prompt = request.prompt;

        this.log(`Processing ${command ? `/${command}` : 'general'} request: ${prompt.substring(0, 100)}...`);

        if (command) {
            await this.handleCommand(command, prompt, stream, token);
        } else {
            await this.handleGeneralImplementationRequest(prompt, stream, token);
        }
    }

    // Override executeStep to use our custom implementation
    public async executeStep(
        step: WorkflowStep,
        request: TaskRequest & { onPartialResponse?: (content: string) => void },
        previousResults: TaskResult[]
    ): Promise<TaskResult> {
        this.showDebug(`ExecuteStep called`, { 
            step: step.id, 
            hasStreamingCallback: !!request.onPartialResponse 
        });
        return await this.processWorkflowStep(step, request, previousResults);
    }

    protected async processWorkflowStep(
        step: WorkflowStep,
        request: TaskRequest & { onPartialResponse?: (content: string) => void; globalContext?: string },
        previousResults: TaskResult[]
    ): Promise<TaskResult> {
        
        const context = await this.getWorkspaceContext();
        
        // Build conversation history from previous results
        let conversationHistory = '';
        
        // Include global context if available
        if (request.globalContext) {
            conversationHistory += request.globalContext;
        }
        
        // Add immediate previous results for this workflow
        if (previousResults.length > 0) {
            conversationHistory += '\n\n## Current Workflow Progress:\n';
            previousResults.forEach((result, index) => {
                const agentName = result.metadata?.agent || `Agent ${index + 1}`;
                const stepId = result.metadata?.step || 'unknown';
                conversationHistory += `\n### ${agentName} (${stepId}):\n${result.content}\n`;
            });
        }
        
        let systemPrompt = '';
        let userPrompt = '';

        switch (step.id) {
            case 'implement':
                systemPrompt = this.getImplementationSystemPrompt();
                userPrompt = `Implement the following: ${request.prompt}\n\nWorkspace Context:\n${context}${conversationHistory}`;
                break;
                
            case 'test':
                systemPrompt = this.getTestingSystemPrompt();
                userPrompt = `Create comprehensive tests for: ${request.prompt}\n\nPrevious Implementation:\n${this.extractPreviousContent(previousResults)}`;
                break;
                
            case 'optimize':
                systemPrompt = this.getOptimizationSystemPrompt();
                userPrompt = `Optimize this implementation: ${request.prompt}\n\nContext:\n${context}${conversationHistory}`;
                break;
                
            default:
                systemPrompt = this.getGeneralSystemPrompt();
                userPrompt = `${request.prompt}\n\nContext:\n${context}${conversationHistory}`;
        }

        try {
            // Pass streaming callback if provided
            const claudeService = await this.getClaudeService(request.onPartialResponse);
            const response = await claudeService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);

            // Extract content string from response object
            const responseContent = typeof response === 'string' 
                ? response 
                : (response as any).content || '';

            // Extract metadata from response if available
            const responseMetadata = typeof response === 'object' && response !== null
                ? (response as any).metadata
                : {};

            this.showDebug('Response received', {
                contentLength: responseContent.length,
                metadata: responseMetadata
            });

            return {
                status: 'success',
                content: responseContent,
                metadata: { 
                    step: step.id,
                    agent: 'codesmith',
                    model: 'claude-3.5-sonnet',
                    ...responseMetadata
                }
            };

        } catch (error) {
            throw new Error(`Failed to process ${step.id}: ${(error as any).message}`);
        }
    }

    // Command Handlers

    private async handleImplementCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
        stream.progress('⚡ Implementing your requirements...');
        
        const context = await this.getWorkspaceContext();
        const systemPrompt = this.getImplementationSystemPrompt();
        const userPrompt = `Implement the following requirements: ${prompt}\n\nWorkspace Context:\n${context}`;

        try {
            const claudeService = await this.getClaudeService();
            const response = await claudeService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);

            // Extract content string from response object
            const responseContent = typeof response === 'string' 
                ? response 
                : (response as any).content || '';
            stream.markdown(responseContent);

            // Extract code blocks for file creation
            const codeBlocks = this.extractCodeBlocks(responseContent);
            
            for (const block of codeBlocks) {
                if (block.filename) {
                    this.createActionButton(
                        `📄 Create ${block.filename}`,
                        'ki-autoagent.createFile',
                        [block.filename, block.code],
                        stream
                    );
                }
            }

            // Offer to create tests
            this.createActionButton(
                '🧪 Generate Tests',
                'ki-autoagent.generateTests',
                [prompt, response],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ Error during implementation: ${(error as any).message}`);
        }
    }

    private async handleOptimizeCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
        stream.progress('🚀 Optimizing code for performance...');
        
        const context = await this.getWorkspaceContext();
        const systemPrompt = this.getOptimizationSystemPrompt();
        
        // Include current file content if available
        let codeToOptimize = '';
        if (context.includes('Selected text:')) {
            codeToOptimize = context;
        } else if (vscode.window.activeTextEditor) {
            const document = vscode.window.activeTextEditor.document;
            codeToOptimize = `Current file: ${document.fileName}\n\`\`\`${document.languageId}\n${document.getText()}\n\`\`\``;
        }
        
        const userPrompt = `Optimize the following code: ${prompt}\n\nCode to optimize:\n${codeToOptimize}`;

        try {
            const claudeService = await this.getClaudeService();
            const response = await claudeService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);

            // Extract content string from response object
            const responseContent = typeof response === 'string' 
                ? response 
                : (response as any).content || '';
            stream.markdown(responseContent);

            // Offer to apply optimizations
            const optimizedCode = this.extractMainCodeBlock(responseContent);
            if (optimizedCode) {
                this.createActionButton(
                    '✨ Apply Optimization',
                    'ki-autoagent.insertAtCursor',
                    [optimizedCode],
                    stream
                );
            }

        } catch (error) {
            stream.markdown(`❌ Error during optimization: ${(error as any).message}`);
        }
    }

    private async handleTestCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
        stream.progress('🧪 Generating comprehensive test suite...');
        
        const context = await this.getWorkspaceContext();
        const systemPrompt = this.getTestingSystemPrompt();
        const userPrompt = `Generate comprehensive tests for: ${prompt}\n\nWorkspace Context:\n${context}`;

        try {
            const claudeService = await this.getClaudeService();
            const response = await claudeService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);

            // Extract content string from response object
            const responseContent = typeof response === 'string' 
                ? response 
                : (response as any).content || '';
            stream.markdown(responseContent);

            // Extract test files for creation
            const testFiles = this.extractTestFiles(responseContent);
            
            for (const testFile of testFiles) {
                this.createActionButton(
                    `🧪 Create ${testFile.filename}`,
                    'ki-autoagent.createFile',
                    [testFile.filename, testFile.code],
                    stream
                );
            }

            // Offer to run tests
            this.createActionButton(
                '▶️ Run Tests',
                'ki-autoagent.runTests',
                [],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ Error generating tests: ${(error as any).message}`);
        }
    }

    private async handleFixCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('🔧 Fixing bugs and issues...');

        const context = await this.getWorkspaceContext();
        const systemPrompt = `You are CodeSmithClaude, an expert bug fixer. Your task is to:
1. Identify the root cause of the bug
2. Implement a robust fix
3. Ensure no new bugs are introduced
4. Add error handling where needed
5. Test the fix thoroughly

${this.getSystemContextPrompt()}`;

        const userPrompt = `Fix the following issue: ${prompt}\n\nWorkspace Context:\n${context}`;

        try {
            const claudeService = await this.getClaudeService();
            const response = await claudeService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);

            const responseContent = typeof response === 'string'
                ? response
                : (response as any).content || '';
            stream.markdown(responseContent);

        } catch (error) {
            stream.markdown(`❌ Error during bug fix: ${(error as any).message}`);
        }
    }

    private async handleDebugCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('🐛 Debugging and analyzing issue...');

        const context = await this.getWorkspaceContext();
        const systemPrompt = `You are CodeSmithClaude, an expert debugger. Your task is to:
1. Analyze error messages and stack traces
2. Identify the root cause
3. Add debug logging to trace the issue
4. Provide step-by-step debugging instructions
5. Suggest a permanent fix

${this.getSystemContextPrompt()}`;

        const userPrompt = `Debug this issue: ${prompt}\n\nWorkspace Context:\n${context}`;

        try {
            const claudeService = await this.getClaudeService();
            const response = await claudeService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);

            const responseContent = typeof response === 'string'
                ? response
                : (response as any).content || '';
            stream.markdown(responseContent);

        } catch (error) {
            stream.markdown(`❌ Error during debugging: ${(error as any).message}`);
        }
    }

    private async handleRefactorCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('♻️ Refactoring code for better structure...');

        const context = await this.getWorkspaceContext();
        const systemPrompt = `You are CodeSmithClaude, a refactoring expert. Your task is to:
1. Improve code structure and organization
2. Apply design patterns where appropriate
3. Reduce code duplication (DRY principle)
4. Improve naming and readability
5. Maintain functionality while improving quality

${this.getSystemContextPrompt()}`;

        const userPrompt = `Refactor the following: ${prompt}\n\nWorkspace Context:\n${context}`;

        try {
            const claudeService = await this.getClaudeService();
            const response = await claudeService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);

            const responseContent = typeof response === 'string'
                ? response
                : (response as any).content || '';
            stream.markdown(responseContent);

        } catch (error) {
            stream.markdown(`❌ Error during refactoring: ${(error as any).message}`);
        }
    }

    private async handleModernizeCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('🚀 Modernizing legacy code...');

        const context = await this.getWorkspaceContext();
        const systemPrompt = `You are CodeSmithClaude, a code modernization expert. Your task is to:
1. Update deprecated APIs and methods
2. Use modern language features (async/await, arrow functions, etc.)
3. Update to latest framework versions
4. Improve TypeScript types
5. Add modern tooling support

${this.getSystemContextPrompt()}`;

        const userPrompt = `Modernize the following code: ${prompt}\n\nWorkspace Context:\n${context}`;

        try {
            const claudeService = await this.getClaudeService();
            const response = await claudeService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);

            const responseContent = typeof response === 'string'
                ? response
                : (response as any).content || '';
            stream.markdown(responseContent);

        } catch (error) {
            stream.markdown(`❌ Error during modernization: ${(error as any).message}`);
        }
    }

    private async handleGeneralImplementationRequest(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
        stream.progress('💻 Processing implementation request...');
        
        const context = await this.getWorkspaceContext();
        const systemPrompt = this.getGeneralSystemPrompt();
        const userPrompt = `${prompt}\n\nWorkspace Context:\n${context}`;

        try {
            const claudeService = await this.getClaudeService();
            const response = await claudeService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);

            // Extract content string from response object
            const responseContent = typeof response === 'string' 
                ? response 
                : (response as any).content || '';
            stream.markdown(responseContent);

            // Auto-detect and offer file creation
            const codeBlocks = this.extractCodeBlocks(responseContent);
            for (const block of codeBlocks) {
                if (block.filename) {
                    this.createActionButton(
                        `📄 Create ${block.filename}`,
                        'ki-autoagent.createFile',
                        [block.filename, block.code],
                        stream
                    );
                }
            }

        } catch (error) {
            stream.markdown(`❌ Error processing request: ${(error as any).message}`);
        }
    }

    // System Prompts

    private getGeneralSystemPrompt(): string {
        return `You are CodeSmithClaude, a senior Python and web developer with expertise in:

- Python development (Django, FastAPI, Flask, Streamlit)
- Web development (React, TypeScript, JavaScript)
- API design and implementation
- Database design and ORM usage
- Testing strategies (pytest, unittest, Jest)
- Code optimization and performance
- Modern development practices

Always provide:
1. Clean, readable, and well-documented code
2. Proper error handling and validation
3. Performance considerations
4. Security best practices
5. Testing recommendations

Format your responses with clear explanations and working code examples.

${this.getSystemContextPrompt()}`;
    }

    private getImplementationSystemPrompt(): string {
        return `You are CodeSmithClaude implementing code based on specifications. Follow this structure:

## Implementation Plan

### 1. Analysis
- Break down requirements
- Identify components needed
- Choose appropriate patterns

### 2. Core Implementation
- Main functionality with proper structure
- Error handling and validation
- Clear documentation

### 3. Integration Points
- How this connects to existing code
- Dependencies and imports
- Configuration requirements

### 4. Usage Examples
- How to use the implemented code
- Example scenarios
- Common patterns

### 5. Next Steps
- Testing recommendations
- Potential improvements
- Deployment considerations

Provide complete, working code with filenames when appropriate. Focus on clean, maintainable solutions.

${this.getSystemContextPrompt()}`;
    }

    private getOptimizationSystemPrompt(): string {
        return `You are CodeSmithClaude optimizing code for performance. Follow this approach:

## Code Optimization Analysis

### 1. Current Code Analysis
- Identify performance bottlenecks
- Analyze complexity and efficiency
- Spot potential issues

### 2. Optimization Strategies
- Algorithm improvements
- Data structure optimizations
- Caching opportunities
- Memory efficiency

### 3. Optimized Implementation
- Improved code with explanations
- Performance comparisons
- Benchmark suggestions

### 4. Trade-offs
- Performance vs readability
- Memory vs speed
- Complexity considerations

Always maintain code readability while improving performance. Explain your optimization choices.

${this.getSystemContextPrompt()}`;
    }

    private getTestingSystemPrompt(): string {
        return `You are CodeSmithClaude creating comprehensive test suites. Structure your tests as:

## Test Suite Design

### 1. Test Strategy
- Test types needed (unit, integration, e2e)
- Coverage goals
- Testing framework choice

### 2. Unit Tests
- Test individual functions/methods
- Edge cases and error conditions
- Mocking strategies

### 3. Integration Tests
- Component interactions
- API endpoint testing
- Database integration

### 4. Test Utilities
- Fixtures and test data
- Helper functions
- Setup/teardown

### 5. Test Configuration
- Test runner setup
- CI/CD integration
- Coverage reporting

Provide complete, runnable tests with clear assertions and good coverage.

${this.getSystemContextPrompt()}`;
    }

    // Service Configuration Methods

    private async validateServiceConfig(stream?: vscode.ChatResponseStream): Promise<boolean> {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        const serviceMode = config.get<string>('claude.serviceMode', 'claude-code');

        if (serviceMode === 'api') {
            if (!config.get<string>('anthropic.apiKey')) {
                if (stream) {
                    stream.markdown('❌ **Anthropic API key not configured**\n\nPlease set your API key in VS Code settings:\n- Go to Settings\n- Search for "KI AutoAgent"\n- Set your Anthropic API key');
                }
                return false;
            }
        } else if (serviceMode === 'claude-code') {
            const isClaudeCodeAvailable = await this.claudeCodeService.isAvailable();
            if (!isClaudeCodeAvailable) {
                if (stream) {
                    stream.markdown(`❌ **Claude Code CLI not available**\n\n**To install:**\n\`\`\`bash\nnpm install -g @anthropic-ai/claude-code\n\`\`\`\n\nOr configure your Anthropic API key in VS Code settings.`);
                }
                return false;
            }
        }

        return true;
    }

    private async getClaudeService(onPartialResponse?: (content: string) => void): Promise<{ chat: (messages: any[]) => Promise<any> }> {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        const serviceMode = config.get<string>('claude.serviceMode', 'claude-code');

        this.showDebug('Service configuration', {
            serviceMode,
            hasStreamingCallback: !!onPartialResponse
        });

        if (serviceMode === 'claude-code') {
            const isAvailable = await this.claudeCodeService.isAvailable();
            if (isAvailable) {
                this.showInfo('Using Claude Code CLI');
                return {
                    chat: async (messages: any[]) => {
                        // Extract the main user message content
                        const userMessage = messages.find(m => m.role === 'user')?.content || '';
                        const systemMessage = messages.find(m => m.role === 'system')?.content || '';
                        const fullPrompt = systemMessage ? `${systemMessage}\n\n${userMessage}` : userMessage;
                        
                        // Use streaming if callback provided
                        if (onPartialResponse) {
                            this.showDebug('Using streaming message');
                            const response = await this.claudeCodeService.sendStreamingMessage(fullPrompt, {
                                model: 'sonnet',
                                temperature: 0.7,
                                onPartialResponse: onPartialResponse
                            });
                            return response;
                        } else {
                            const response = await this.claudeCodeService.sendMessage(fullPrompt, {
                                model: 'sonnet',
                                temperature: 0.7
                            });
                            return response.content;
                        }
                    }
                };
            } else {
                this.showFallbackMode('Claude Code CLI not available', 'Using Anthropic API');
            }
        }
        
        // Fall back to Anthropic API
        this.showInfo('Using Anthropic API');
        return {
            chat: async (messages: any[]) => {
                return await this.anthropicService.chat(messages);
            }
        };
    }

    // Helper Methods

    private extractCodeBlocks(content: string): Array<{filename?: string, language: string, code: string}> {
        const codeBlockRegex = /```(\w+)?\s*(?:\/\/\s*(.+\.[\w]+))?\n([\s\S]*?)```/g;
        const blocks: Array<{filename?: string, language: string, code: string}> = [];
        
        let match;
        while ((match = codeBlockRegex.exec(content)) !== null) {
            const language = match[1] || 'text';
            const filename = match[2] || this.inferFilename(language, match[3]);
            const code = match[3];
            
            blocks.push({ filename, language, code });
        }
        
        return blocks;
    }

    private extractTestFiles(content: string): Array<{filename: string, code: string}> {
        const blocks = this.extractCodeBlocks(content);
        return blocks
            .filter(block => 
                block.filename && 
                (block.filename.includes('test') || block.filename.includes('spec'))
            )
            .map(block => ({ filename: block.filename!, code: block.code }));
    }

    private extractMainCodeBlock(content: string): string {
        const blocks = this.extractCodeBlocks(content);
        return blocks.length > 0 ? blocks[0].code : '';
    }

    private inferFilename(language: string, code: string): string {
        // Try to infer filename from code content
        if (language === 'python') {
            const classMatch = code.match(/class\s+(\w+)/);
            if (classMatch) {
                return `${classMatch[1].toLowerCase()}.py`;
            }
            return 'main.py';
        } else if (language === 'typescript' || language === 'javascript') {
            const classMatch = code.match(/(?:class|interface)\s+(\w+)/);
            if (classMatch) {
                return `${classMatch[1]}.${language === 'typescript' ? 'ts' : 'js'}`;
            }
            return `index.${language === 'typescript' ? 'ts' : 'js'}`;
        }
        
        return `code.${language}`;
    }

    private extractPreviousContent(previousResults: TaskResult[]): string {
        return previousResults
            .map(result => result.content)
            .join('\n\n---\n\n')
            .substring(0, 2000); // Limit context size
    }
}