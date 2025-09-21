/**
 * FixerBot - Live Testing & Validation Expert
 * Runs applications, tests changes live, validates output, and suggests fixes
 * Enhanced with automated testing and real-time validation capabilities
 */
import * as vscode from 'vscode';
import { ChatAgent } from './base/ChatAgent';
import { AgentConfig, TaskRequest, TaskResult, WorkflowStep } from '../types';
import { VSCodeMasterDispatcher } from '../core/VSCodeMasterDispatcher';
import { ClaudeCodeService } from '../services/ClaudeCodeService';
import * as path from 'path';
import * as child_process from 'child_process';
import * as fs from 'fs';
import * as http from 'http';
import * as https from 'https';

interface TestResult {
    status: 'OK' | 'NOT_OK';
    errors?: string[];
    output?: string;
    suggestions?: string[];
    validations?: ValidationResult[];
}

interface ValidationResult {
    test: string;
    passed: boolean;
    message: string;
}

interface ProcessResult {
    success: boolean;
    output: string;
    error?: string;
    exitCode?: number;
}

export class FixerBotAgent extends ChatAgent {
    private claudeService: ClaudeCodeService;
    private runningProcesses: Map<string, child_process.ChildProcess> = new Map();
    private testCommands: Map<string, string[]> = new Map([
        ['npm', ['npm test', 'npm run test', 'npm run test:unit']],
        ['python', ['pytest', 'python -m pytest', 'python -m unittest']],
        ['java', ['mvn test', 'gradle test']],
        ['go', ['go test ./...']]
    ]);
    private startCommands: Map<string, string[]> = new Map([
        ['npm', ['npm start', 'npm run dev', 'npm run serve']],
        ['python', ['python app.py', 'python main.py', 'flask run', 'uvicorn main:app --reload']],
        ['java', ['mvn spring-boot:run', 'java -jar target/*.jar']],
        ['go', ['go run .', 'go run main.go']]
    ]);

    constructor(context: vscode.ExtensionContext, dispatcher: VSCodeMasterDispatcher) {
        const config: AgentConfig = {
            participantId: 'ki-autoagent.fixer',
            name: 'fixer',
            fullName: 'FixerBot',
            description: 'Live Testing Expert - Runs apps, validates changes, and ensures quality',
            model: 'claude-4.1-sonnet-20250920',
            iconPath: vscode.Uri.joinPath(context.extensionUri, 'media', 'fixer-icon.svg'),
            capabilities: [
                'Bug Detection & Fixing',
                'Error Resolution',
                'Performance Optimization',
                'Code Refactoring',
                'Memory Leak Fixes',
                'Crash Debugging',
                'Hotfix Creation',
                'Legacy Code Modernization'
            ],
            commands: [
                { name: 'fix', description: 'Fix bugs in current code', handler: 'handleFixCommand' },
                { name: 'debug', description: 'Debug and diagnose issues', handler: 'handleDebugCommand' },
                { name: 'optimize', description: 'Optimize code performance', handler: 'handleOptimizeCommand' },
                { name: 'refactor', description: 'Refactor code structure', handler: 'handleRefactorCommand' },
                { name: 'modernize', description: 'Update legacy code', handler: 'handleModernizeCommand' }
            ]
        };

        super(config, context, dispatcher);
        this.claudeService = new ClaudeCodeService();
    }

    protected async handleRequest(
        request: vscode.ChatRequest,
        context: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        const command = request.command;
        const prompt = request.prompt;

        this.log(`Processing ${command ? `/${command}` : 'general'} fix request: ${prompt.substring(0, 100)}...`);

        if (command) {
            await this.handleCommand(command, prompt, stream, token);
        } else {
            await this.handleGeneralFixRequest(prompt, stream, token);
        }
    }

    protected async processWorkflowStep(
        step: WorkflowStep,
        request: TaskRequest,
        previousResults: TaskResult[]
    ): Promise<TaskResult> {

        try {
            let fixResult = '';

            switch (step.id) {
                case 'bug_fix':
                    fixResult = await this.fixBugs(request, previousResults);
                    break;

                case 'performance_optimization':
                    fixResult = await this.optimizePerformance(request, previousResults);
                    break;

                case 'refactoring':
                    fixResult = await this.refactorCode(request, previousResults);
                    break;

                case 'error_resolution':
                    fixResult = await this.resolveErrors(request, previousResults);
                    break;

                default:
                    fixResult = await this.performGeneralFix(request, previousResults);
            }

            return {
                status: 'success',
                content: fixResult,
                metadata: {
                    step: step.id,
                    agent: 'fixer',
                    type: 'fix'
                }
            };

        } catch (error) {
            throw new Error(`Failed to process fix step ${step.id}: ${(error as any).message}`);
        }
    }

    // Command Handlers

    private async handleFixCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            stream.markdown('❌ No active editor found. Please open a file with bugs to fix.');
            return;
        }

        stream.progress('🔧 Analyzing code for bugs...');

        try {
            const document = editor.document;
            const code = document.getText();
            const fileName = path.basename(document.fileName);
            const language = document.languageId;

            // Find and fix bugs
            const bugAnalysis = await this.analyzeBugs(code, fileName, language, prompt);

            stream.markdown('## 🔧 Bug Analysis & Fixes\n\n');
            stream.markdown(bugAnalysis.report);

            if (bugAnalysis.fixedCode) {
                stream.markdown('\n### 📝 Fixed Code:\n');
                stream.markdown('```' + language + '\n' + bugAnalysis.fixedCode + '\n```');

                // Offer to apply fixes
                this.createActionButton(
                    '✅ Apply Fixes',
                    'ki-autoagent.replaceContent',
                    [bugAnalysis.fixedCode],
                    stream
                );

                // Offer to create patch
                this.createActionButton(
                    '🩹 Create Patch File',
                    'ki-autoagent.createPatch',
                    [code, bugAnalysis.fixedCode],
                    stream
                );
            }

        } catch (error) {
            stream.markdown(`❌ Bug fixing failed: ${(error as any).message}`);
        }
    }

    private async handleDebugCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('🐛 Starting debug analysis...');

        try {
            const editor = vscode.window.activeTextEditor;
            let debugContext = prompt;

            if (editor) {
                const code = editor.document.getText();
                const selection = editor.selection;
                const selectedText = editor.document.getText(selection);

                debugContext = `${prompt}\n\nFile: ${editor.document.fileName}\n`;
                if (selectedText) {
                    debugContext += `\nSelected code:\n${selectedText}`;
                } else {
                    debugContext += `\nFull code:\n${code}`;
                }
            }

            const debugAnalysis = await this.performDebugAnalysis(debugContext);

            stream.markdown('## 🐛 Debug Analysis\n\n');
            stream.markdown(debugAnalysis);

            // Offer debug actions
            this.createActionButton(
                '📍 Add Debug Logging',
                'ki-autoagent.addDebugLogging',
                [],
                stream
            );

            this.createActionButton(
                '🔍 Add Breakpoints',
                'ki-autoagent.addBreakpoints',
                [],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ Debug analysis failed: ${(error as any).message}`);
        }
    }

    private async handleOptimizeCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('⚡ Optimizing code performance...');

        try {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                stream.markdown('❌ No active editor found. Please open a file to optimize.');
                return;
            }

            const code = editor.document.getText();
            const language = editor.document.languageId;

            const optimization = await this.optimizeCode(code, language, prompt);

            stream.markdown('## ⚡ Performance Optimization\n\n');
            stream.markdown(optimization.report);

            if (optimization.optimizedCode) {
                stream.markdown('\n### 🚀 Optimized Code:\n');
                stream.markdown('```' + language + '\n' + optimization.optimizedCode + '\n```');

                // Show performance improvements
                if (optimization.improvements) {
                    stream.markdown('\n### 📊 Performance Improvements:\n');
                    stream.markdown(optimization.improvements);
                }

                // Offer to apply
                this.createActionButton(
                    '⚡ Apply Optimizations',
                    'ki-autoagent.replaceContent',
                    [optimization.optimizedCode],
                    stream
                );
            }

        } catch (error) {
            stream.markdown(`❌ Optimization failed: ${(error as any).message}`);
        }
    }

    private async handleRefactorCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('🔨 Refactoring code structure...');

        try {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                stream.markdown('❌ No active editor found. Please open a file to refactor.');
                return;
            }

            const code = editor.document.getText();
            const language = editor.document.languageId;

            const refactoring = await this.refactorCodeStructure(code, language, prompt);

            stream.markdown('## 🔨 Code Refactoring\n\n');
            stream.markdown(refactoring.report);

            if (refactoring.refactoredCode) {
                stream.markdown('\n### ✨ Refactored Code:\n');
                stream.markdown('```' + language + '\n' + refactoring.refactoredCode + '\n```');

                // Offer to apply
                this.createActionButton(
                    '🔨 Apply Refactoring',
                    'ki-autoagent.replaceContent',
                    [refactoring.refactoredCode],
                    stream
                );

                // Offer to create before/after comparison
                this.createActionButton(
                    '📊 View Comparison',
                    'ki-autoagent.showDiff',
                    [code, refactoring.refactoredCode],
                    stream
                );
            }

        } catch (error) {
            stream.markdown(`❌ Refactoring failed: ${(error as any).message}`);
        }
    }

    private async handleModernizeCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('🆕 Modernizing legacy code...');

        try {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                stream.markdown('❌ No active editor found. Please open a legacy file to modernize.');
                return;
            }

            const code = editor.document.getText();
            const language = editor.document.languageId;

            const modernization = await this.modernizeLegacyCode(code, language, prompt);

            stream.markdown('## 🆕 Code Modernization\n\n');
            stream.markdown(modernization.report);

            if (modernization.modernCode) {
                stream.markdown('\n### 🌟 Modernized Code:\n');
                stream.markdown('```' + language + '\n' + modernization.modernCode + '\n```');

                // List improvements
                stream.markdown('\n### 📋 Modernization Changes:\n');
                stream.markdown(modernization.changes);

                // Offer to apply
                this.createActionButton(
                    '🆕 Apply Modernization',
                    'ki-autoagent.replaceContent',
                    [modernization.modernCode],
                    stream
                );
            }

        } catch (error) {
            stream.markdown(`❌ Modernization failed: ${(error as any).message}`);
        }
    }

    private async handleGeneralFixRequest(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('🔧 Analyzing and fixing issues...');

        try {
            const fix = await this.performGeneralFix({ prompt } as TaskRequest, []);

            stream.markdown('## 🔧 Fix Results\n\n');
            stream.markdown(fix);

        } catch (error) {
            stream.markdown(`❌ Fix failed: ${(error as any).message}`);
        }
    }

    // Fix Methods

    private async analyzeBugs(code: string, fileName: string, language: string, context: string): Promise<any> {
        const prompt = `Analyze this ${language} code for bugs and provide fixes:

File: ${fileName}

Code:
${code}

Additional context: ${context}

Tasks:
1. Identify all bugs (syntax errors, logic errors, runtime errors)
2. Explain each bug and its impact
3. Provide fixed code with all bugs resolved
4. Include comments explaining the fixes

Return in format:
- Bug list with descriptions
- Fixed code
- Explanation of changes

${this.getSystemContextPrompt()}`;

        const response = await this.claudeService.sendMessage(prompt);

        // Parse response to extract report and fixed code
        const content = typeof response === 'string' ? response : response.content || '';
        return {
            report: content,
            fixedCode: this.extractCodeFromResponse(content, language)
        };
    }

    private async performDebugAnalysis(context: string): Promise<string> {
        const prompt = `Perform detailed debug analysis:

${context}

Provide:
1. Root cause analysis
2. Step-by-step debugging approach
3. Potential error sources
4. Debug logging recommendations
5. Breakpoint placement suggestions
6. Variable inspection points
7. Test cases to reproduce issue

${this.getSystemContextPrompt()}`;

        const response = await this.claudeService.sendMessage(prompt);
        return typeof response === 'string' ? response : response.content || '';
    }

    private async optimizeCode(code: string, language: string, context: string): Promise<any> {
        const prompt = `Optimize this ${language} code for performance:

Code:
${code}

Additional context: ${context}

Optimization goals:
1. Reduce time complexity
2. Minimize memory usage
3. Eliminate redundant operations
4. Optimize loops and iterations
5. Improve caching
6. Enhance parallelization opportunities

Provide:
- Performance analysis
- Optimized code
- Specific improvements made
- Expected performance gains

${this.getSystemContextPrompt()}`;

        const response = await this.claudeService.sendMessage(prompt);
        const content = typeof response === 'string' ? response : response.content || '';

        return {
            report: content,
            optimizedCode: this.extractCodeFromResponse(content, language),
            improvements: this.extractImprovements(content)
        };
    }

    private async refactorCodeStructure(code: string, language: string, context: string): Promise<any> {
        const prompt = `Refactor this ${language} code for better structure and maintainability:

Code:
${code}

Additional context: ${context}

Refactoring goals:
1. Apply SOLID principles
2. Extract methods/functions
3. Reduce coupling
4. Increase cohesion
5. Improve naming
6. Simplify complex logic
7. Remove code duplication

Provide:
- Refactoring analysis
- Refactored code
- List of improvements

${this.getSystemContextPrompt()}`;

        const response = await this.claudeService.sendMessage(prompt);
        const content = typeof response === 'string' ? response : response.content || '';

        return {
            report: content,
            refactoredCode: this.extractCodeFromResponse(content, language)
        };
    }

    private async modernizeLegacyCode(code: string, language: string, context: string): Promise<any> {
        const prompt = `Modernize this legacy ${language} code to use current best practices:

Code:
${code}

Additional context: ${context}

Modernization tasks:
1. Update to latest language features
2. Replace deprecated APIs
3. Use modern patterns and idioms
4. Improve async/await usage
5. Update dependency usage
6. Apply current security practices
7. Enhance type safety

Provide:
- Modernization analysis
- Updated code
- List of changes made

${this.getSystemContextPrompt()}`;

        const response = await this.claudeService.sendMessage(prompt);
        const content = typeof response === 'string' ? response : response.content || '';

        return {
            report: content,
            modernCode: this.extractCodeFromResponse(content, language),
            changes: this.extractChanges(content)
        };
    }

    // Workflow helper methods

    private async fixBugs(request: TaskRequest, previousResults: TaskResult[]): Promise<string> {
        const context = this.buildContextFromResults(previousResults);
        const response = await this.claudeService.sendMessage(
            `Fix bugs based on: ${request.prompt}\n\nContext:\n${context}`
        );
        return typeof response === 'string' ? response : response.content || '';
    }

    private async optimizePerformance(request: TaskRequest, previousResults: TaskResult[]): Promise<string> {
        const context = this.buildContextFromResults(previousResults);
        const response = await this.claudeService.sendMessage(
            `Optimize performance: ${request.prompt}\n\nContext:\n${context}`
        );
        return typeof response === 'string' ? response : response.content || '';
    }

    private async refactorCode(request: TaskRequest, previousResults: TaskResult[]): Promise<string> {
        const context = this.buildContextFromResults(previousResults);
        const response = await this.claudeService.sendMessage(
            `Refactor code: ${request.prompt}\n\nContext:\n${context}`
        );
        return typeof response === 'string' ? response : response.content || '';
    }

    private async resolveErrors(request: TaskRequest, previousResults: TaskResult[]): Promise<string> {
        const context = this.buildContextFromResults(previousResults);
        const response = await this.claudeService.sendMessage(
            `Resolve errors: ${request.prompt}\n\nContext:\n${context}`
        );
        return typeof response === 'string' ? response : response.content || '';
    }

    private async performGeneralFix(request: TaskRequest, previousResults: TaskResult[]): Promise<string> {
        const context = this.buildContextFromResults(previousResults);
        const prompt = `Fix the following issue:

Request: ${request.prompt}

Previous results:
${context}

Provide comprehensive fix with explanation.

${this.getSystemContextPrompt()}`;

        const response = await this.claudeService.sendMessage(prompt);
        return typeof response === 'string' ? response : response.content || '';
    }

    // Helper methods

    private buildContextFromResults(results: TaskResult[]): string {
        return results
            .filter(r => r.status === 'success')
            .map(r => `${r.metadata?.step || 'Step'}: ${r.content}`)
            .join('\n\n');
    }

    private extractCodeFromResponse(response: string, language: string): string {
        // Extract code blocks from markdown response
        const codeBlockRegex = new RegExp('```' + language + '?\\n([\\s\\S]*?)```', 'g');
        const matches = response.match(codeBlockRegex);
        if (matches && matches.length > 0) {
            // Return the last code block (assumed to be the fixed/optimized version)
            const lastMatch = matches[matches.length - 1];
            return lastMatch.replace(new RegExp('```' + language + '?\\n'), '').replace(/```$/, '');
        }
        return '';
    }

    private extractImprovements(content: string): string {
        // Extract performance improvements section
        const improvementsMatch = content.match(/improvements?:?\s*([\s\S]*?)(?:\n##|\n###|$)/i);
        return improvementsMatch ? improvementsMatch[1].trim() : '';
    }

    private extractChanges(content: string): string {
        // Extract changes section
        const changesMatch = content.match(/changes?:?\s*([\s\S]*?)(?:\n##|\n###|$)/i);
        return changesMatch ? changesMatch[1].trim() : '';
    }

    // ================ LIVE TESTING & VALIDATION METHODS ================

    /**
     * Test code changes live by running the application
     */
    public async testLive(code: string, projectPath?: string): Promise<TestResult> {
        console.log('[FIXERBOT] Starting live testing...');

        try {
            // Detect project type
            const projectType = await this.detectProjectType(projectPath);
            console.log(`[FIXERBOT] Detected project type: ${projectType}`);

            // Start application
            const appProcess = await this.runApplication(projectType, projectPath);

            // Give app time to start
            await this.waitForAppStart(appProcess, 5000);

            // Run validation tests
            const validations = await this.validateApplication(projectType);

            // Run unit tests
            const testResults = await this.runTests(projectType, projectPath);

            // Analyze results
            const analysis = this.analyzeResults(validations, testResults, appProcess.output);

            // Kill the process
            this.killProcess(appProcess.pid);

            return analysis;

        } catch (error) {
            console.error('[FIXERBOT] Live testing error:', error);
            return {
                status: 'NOT_OK',
                errors: [(error as any).message],
                suggestions: ['Check project setup', 'Verify dependencies are installed']
            };
        }
    }

    /**
     * Detect project type from files
     */
    private async detectProjectType(projectPath?: string): Promise<string> {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        const basePath = projectPath || workspaceFolder?.uri.fsPath || '';

        // Check for package.json (Node.js)
        if (fs.existsSync(path.join(basePath, 'package.json'))) {
            return 'npm';
        }

        // Check for requirements.txt or setup.py (Python)
        if (fs.existsSync(path.join(basePath, 'requirements.txt')) ||
            fs.existsSync(path.join(basePath, 'setup.py'))) {
            return 'python';
        }

        // Check for pom.xml or build.gradle (Java)
        if (fs.existsSync(path.join(basePath, 'pom.xml'))) {
            return 'maven';
        }
        if (fs.existsSync(path.join(basePath, 'build.gradle'))) {
            return 'gradle';
        }

        // Check for go.mod (Go)
        if (fs.existsSync(path.join(basePath, 'go.mod'))) {
            return 'go';
        }

        return 'unknown';
    }

    /**
     * Run the application
     */
    private async runApplication(projectType: string, projectPath?: string): Promise<ProcessResult & { pid: number }> {
        const commands = this.startCommands.get(projectType) || [];
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        const cwd = projectPath || workspaceFolder?.uri.fsPath || process.cwd();

        for (const command of commands) {
            try {
                console.log(`[FIXERBOT] Trying to start app with: ${command}`);

                const child = child_process.spawn(command, {
                    cwd,
                    shell: true,
                    env: { ...process.env, NODE_ENV: 'test' }
                });

                const processKey = `app_${Date.now()}`;
                this.runningProcesses.set(processKey, child);

                // Collect output
                let output = '';
                let error = '';

                child.stdout?.on('data', (data) => {
                    output += data.toString();
                });

                child.stderr?.on('data', (data) => {
                    error += data.toString();
                });

                // Return immediately with running process
                return {
                    success: true,
                    output,
                    error,
                    pid: child.pid!
                };

            } catch (error) {
                console.error(`[FIXERBOT] Failed to start with ${command}:`, error);
            }
        }

        throw new Error('Could not start application with any known command');
    }

    /**
     * Wait for application to start
     */
    private async waitForAppStart(process: ProcessResult, timeout: number): Promise<void> {
        return new Promise((resolve) => {
            setTimeout(resolve, timeout);
        });
    }

    /**
     * Validate running application
     */
    private async validateApplication(projectType: string): Promise<ValidationResult[]> {
        const validations: ValidationResult[] = [];

        // Check if HTTP server is responding
        const httpCheck = await this.checkHttpEndpoint('http://localhost:3000');
        validations.push({
            test: 'HTTP Server Check',
            passed: httpCheck.success,
            message: httpCheck.message
        });

        // Check for common API endpoints
        const apiCheck = await this.checkHttpEndpoint('http://localhost:3000/api/health');
        validations.push({
            test: 'API Health Check',
            passed: apiCheck.success,
            message: apiCheck.message
        });

        return validations;
    }

    /**
     * Check HTTP endpoint
     */
    private async checkHttpEndpoint(url: string): Promise<{ success: boolean; message: string }> {
        return new Promise((resolve) => {
            const protocol = url.startsWith('https') ? https : http;

            protocol.get(url, (res) => {
                resolve({
                    success: res.statusCode === 200,
                    message: `Status: ${res.statusCode}`
                });
            }).on('error', (error) => {
                resolve({
                    success: false,
                    message: error.message
                });
            });
        });
    }

    /**
     * Run unit tests
     */
    private async runTests(projectType: string, projectPath?: string): Promise<ProcessResult> {
        const commands = this.testCommands.get(projectType) || [];
        const cwd = projectPath || vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || process.cwd();

        for (const command of commands) {
            try {
                console.log(`[FIXERBOT] Running tests with: ${command}`);

                const result = await this.executeCommand(command, cwd);

                if (result.success || result.output.includes('passing') || result.output.includes('passed')) {
                    return result;
                }
            } catch (error) {
                console.error(`[FIXERBOT] Test command failed: ${command}`, error);
            }
        }

        return {
            success: false,
            output: 'No test command found or all tests failed',
            error: 'Could not run tests'
        };
    }

    /**
     * Execute command and wait for result
     */
    private async executeCommand(command: string, cwd: string): Promise<ProcessResult> {
        return new Promise((resolve) => {
            child_process.exec(command, { cwd }, (error, stdout, stderr) => {
                resolve({
                    success: !error,
                    output: stdout,
                    error: stderr,
                    exitCode: error?.code
                });
            });
        });
    }

    /**
     * Analyze test results and generate report
     */
    private analyzeResults(
        validations: ValidationResult[],
        testResults: ProcessResult,
        appOutput: string
    ): TestResult {
        const errors: string[] = [];
        const suggestions: string[] = [];

        // Check validations
        const failedValidations = validations.filter(v => !v.passed);
        failedValidations.forEach(v => {
            errors.push(`${v.test}: ${v.message}`);
        });

        // Check test results
        if (!testResults.success) {
            errors.push('Unit tests failed');
            if (testResults.error) {
                errors.push(testResults.error);
            }
        }

        // Check for common errors in app output
        if (appOutput.includes('Error') || appOutput.includes('Exception')) {
            errors.push('Application errors detected in console output');
        }

        // Generate suggestions based on errors
        if (errors.length > 0) {
            if (errors.some(e => e.includes('Cannot find module'))) {
                suggestions.push('Run npm install to install missing dependencies');
            }
            if (errors.some(e => e.includes('port') || e.includes('EADDRINUSE'))) {
                suggestions.push('Port already in use. Kill other processes or use different port');
            }
            if (errors.some(e => e.includes('syntax'))) {
                suggestions.push('Check for syntax errors in recent changes');
            }
            if (errors.some(e => e.includes('test'))) {
                suggestions.push('Review failing test cases and update implementation');
            }
        }

        return {
            status: errors.length === 0 ? 'OK' : 'NOT_OK',
            errors,
            output: appOutput.substring(0, 1000), // First 1000 chars
            suggestions,
            validations
        };
    }

    /**
     * Kill running process
     */
    private killProcess(pid: number): void {
        try {
            process.kill(pid, 'SIGTERM');
            console.log(`[FIXERBOT] Killed process ${pid}`);
        } catch (error) {
            console.error(`[FIXERBOT] Failed to kill process ${pid}:`, error);
        }
    }

    /**
     * Generate fix suggestions based on errors
     */
    public generateFixSuggestions(testResult: TestResult): string[] {
        const suggestions: string[] = [...(testResult.suggestions || [])];

        // Add specific suggestions based on error patterns
        testResult.errors?.forEach(error => {
            if (error.includes('undefined')) {
                suggestions.push('Check for undefined variables or missing initializations');
            }
            if (error.includes('null')) {
                suggestions.push('Add null checks before accessing properties');
            }
            if (error.includes('timeout')) {
                suggestions.push('Increase timeouts or optimize async operations');
            }
            if (error.includes('connection')) {
                suggestions.push('Verify network connections and API endpoints');
            }
        });

        return [...new Set(suggestions)]; // Remove duplicates
    }
}