/**
 * CodeSmithClaude - Senior Python/Web Developer
 * Powered by Claude 3.5 Sonnet for code implementation and optimization
 */
import * as vscode from 'vscode';
import { ChatAgent } from './base/ChatAgent';
import { AgentConfig, TaskRequest, TaskResult, WorkflowStep } from '../types';
import { VSCodeMasterDispatcher } from '../core/VSCodeMasterDispatcher';
import { AnthropicService } from '../utils/AnthropicService';

export class CodeSmithAgent extends ChatAgent {
    private anthropicService: AnthropicService;

    constructor(context: vscode.ExtensionContext, dispatcher: VSCodeMasterDispatcher) {
        const config: AgentConfig = {
            participantId: 'ki-autoagent.codesmith',
            name: 'codesmith',
            fullName: 'CodeSmithClaude',
            description: 'Senior Python/Web Developer powered by Claude 3.5 Sonnet',
            model: 'claude-3.5-sonnet',
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
                { name: 'optimize', description: 'Optimize existing code for performance', handler: 'handleOptimizeCommand' },
                { name: 'test', description: 'Generate comprehensive test suites', handler: 'handleTestCommand' }
            ]
        };

        super(config, context, dispatcher);
        this.anthropicService = new AnthropicService();
    }

    protected async handleRequest(
        request: vscode.ChatRequest,
        context: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
        if (!this.validateApiConfig()) {
            stream.markdown('❌ Anthropic API key not configured. Please set it in VS Code settings.');
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

    protected async processWorkflowStep(
        step: WorkflowStep,
        request: TaskRequest,
        previousResults: TaskResult[]
    ): Promise<TaskResult> {
        
        const context = await this.getWorkspaceContext();
        
        let systemPrompt = '';
        let userPrompt = '';

        switch (step.id) {
            case 'implement':
                systemPrompt = this.getImplementationSystemPrompt();
                userPrompt = `Implement the following: ${request.prompt}\n\nWorkspace Context:\n${context}`;
                break;
                
            case 'test':
                systemPrompt = this.getTestingSystemPrompt();
                userPrompt = `Create comprehensive tests for: ${request.prompt}\n\nPrevious Implementation:\n${this.extractPreviousContent(previousResults)}`;
                break;
                
            case 'optimize':
                systemPrompt = this.getOptimizationSystemPrompt();
                userPrompt = `Optimize this implementation: ${request.prompt}\n\nContext:\n${context}`;
                break;
                
            default:
                systemPrompt = this.getGeneralSystemPrompt();
                userPrompt = `${request.prompt}\n\nContext:\n${context}`;
        }

        try {
            const response = await this.anthropicService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);

            return {
                status: 'success',
                content: response,
                metadata: { 
                    step: step.id,
                    agent: 'codesmith',
                    model: 'claude-3.5-sonnet'
                }
            };

        } catch (error) {
            throw new Error(`Failed to process ${step.id}: ${error.message}`);
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
            const response = await this.anthropicService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);

            stream.markdown(response);

            // Extract code blocks for file creation
            const codeBlocks = this.extractCodeBlocks(response);
            
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
            stream.markdown(`❌ Error during implementation: ${error.message}`);
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
            const response = await this.anthropicService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);

            stream.markdown(response);

            // Offer to apply optimizations
            const optimizedCode = this.extractMainCodeBlock(response);
            if (optimizedCode) {
                this.createActionButton(
                    '✨ Apply Optimization',
                    'ki-autoagent.insertAtCursor',
                    [optimizedCode],
                    stream
                );
            }

        } catch (error) {
            stream.markdown(`❌ Error during optimization: ${error.message}`);
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
            const response = await this.anthropicService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);

            stream.markdown(response);

            // Extract test files for creation
            const testFiles = this.extractTestFiles(response);
            
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
            stream.markdown(`❌ Error generating tests: ${error.message}`);
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
            const response = await this.anthropicService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);

            stream.markdown(response);

            // Auto-detect and offer file creation
            const codeBlocks = this.extractCodeBlocks(response);
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
            stream.markdown(`❌ Error processing request: ${error.message}`);
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

Format your responses with clear explanations and working code examples.`;
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

Provide complete, working code with filenames when appropriate. Focus on clean, maintainable solutions.`;
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

Always maintain code readability while improving performance. Explain your optimization choices.`;
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

Provide complete, runnable tests with clear assertions and good coverage.`;
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