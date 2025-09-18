/**
 * ReviewerGPT - Code Review & Security Expert
 * Performs comprehensive code reviews focusing on quality, security, and performance
 */
import * as vscode from 'vscode';
import { ChatAgent } from './base/ChatAgent';
import { AgentConfig, TaskRequest, TaskResult, WorkflowStep } from '../types';
import { VSCodeMasterDispatcher } from '../core/VSCodeMasterDispatcher';
import { OpenAIService } from '../utils/OpenAIService';
import * as path from 'path';

export class ReviewerGPTAgent extends ChatAgent {
    private openAIService: OpenAIService;

    constructor(context: vscode.ExtensionContext, dispatcher: VSCodeMasterDispatcher) {
        const config: AgentConfig = {
            participantId: 'ki-autoagent.reviewer',
            name: 'reviewer',
            fullName: 'ReviewerGPT',
            description: 'Code Review & Security Expert - Reviews code quality, security, and performance',
            model: 'gpt-5-mini-2025-09-20',
            iconPath: vscode.Uri.joinPath(context.extensionUri, 'media', 'reviewer-icon.svg'),
            capabilities: [
                'Code Quality Review',
                'Security Vulnerability Detection',
                'Performance Analysis',
                'Best Practices Check',
                'SOLID Principles',
                'Design Pattern Analysis',
                'Test Coverage Review',
                'Dependency Audit'
            ],
            commands: [
                { name: 'review', description: 'Comprehensive code review', handler: 'handleReviewCommand' },
                { name: 'bugs', description: 'Active bug hunting in code', handler: 'handleBugsCommand' },
                { name: 'debug', description: 'Run app and debug issues', handler: 'handleDebugCommand' },
                { name: 'test-ui', description: 'Test UI interactions', handler: 'handleTestUICommand' },
                { name: 'security', description: 'Security vulnerability scan', handler: 'handleSecurityCommand' },
                { name: 'performance', description: 'Performance analysis', handler: 'handlePerformanceCommand' },
                { name: 'standards', description: 'Check coding standards', handler: 'handleStandardsCommand' },
                { name: 'test', description: 'Review test coverage', handler: 'handleTestCommand' },
                { name: 'architecture-review', description: 'Validate architect understanding of requirements', handler: 'handleArchitectureReviewCommand' }
            ]
        };

        super(config, context, dispatcher);
        this.openAIService = new OpenAIService();
    }

    protected async handleRequest(
        request: vscode.ChatRequest,
        context: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        const command = request.command;
        const prompt = request.prompt;

        this.log(`Processing ${command ? `/${command}` : 'general'} review request: ${prompt.substring(0, 100)}...`);

        if (command) {
            await this.handleCommand(command, prompt, stream, token);
        } else {
            await this.handleGeneralReviewRequest(prompt, stream, token);
        }
    }

    protected async processWorkflowStep(
        step: WorkflowStep,
        request: TaskRequest,
        previousResults: TaskResult[]
    ): Promise<TaskResult> {

        try {
            let reviewResult = '';
            let foundBugs = false;

            switch (step.id) {
                case 'code_review':
                    reviewResult = await this.performCodeReview(request, previousResults);
                    break;

                case 'security_check':
                    reviewResult = await this.performSecurityCheck(request, previousResults);
                    break;

                case 'performance_review':
                    reviewResult = await this.performPerformanceReview(request, previousResults);
                    break;

                default:
                    reviewResult = await this.performGeneralReview(request, previousResults);
            }

            // Check if bugs were found and need to be sent back to CodeSmith
            if (reviewResult.includes('🚨 BUGS FOUND') || reviewResult.includes('Critical issues')) {
                foundBugs = true;
                reviewResult += '\n\n🔄 **RECOMMENDATION**: These issues should be sent back to @codesmith for immediate fixes.';
            }

            return {
                status: foundBugs ? 'partial_success' : 'success',
                content: reviewResult,
                metadata: {
                    step: step.id,
                    agent: 'reviewer',
                    type: 'review',
                    foundBugs: foundBugs,
                    requiresCodeSmithFix: foundBugs
                },
                suggestions: foundBugs ? [{
                    title: '🔧 Send to CodeSmith for fixes',
                    description: 'Send the found bugs to CodeSmith for immediate fixing',
                    action: 'send_to_codesmith',
                    data: { issues: reviewResult }
                }] : []
            };

        } catch (error) {
            throw new Error(`Failed to process review step ${step.id}: ${(error as any).message}`);
        }
    }

    // Command Handlers

    private async handleReviewCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            stream.markdown('❌ No active editor found. Please open a file to review.');
            return;
        }

        stream.progress('🔍 Performing comprehensive code review...');

        try {
            const document = editor.document;
            const code = document.getText();
            const fileName = path.basename(document.fileName);
            const language = document.languageId;

            const review = await this.reviewCode(code, fileName, language, prompt);

            stream.markdown('## 🔍 Code Review Report\n\n');
            stream.markdown(review);

            // Add action buttons
            this.createActionButton(
                '📋 Save Review Report',
                'ki-autoagent.saveFile',
                [`reviews/review_${Date.now()}.md`, review],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ Review failed: ${(error as any).message}`);
        }
    }

    private async handleBugsCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('🐛 Actively hunting for bugs...');

        try {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                stream.markdown('❌ No active editor found. Please open a file to review.');
                return;
            }

            const document = editor.document;
            const code = document.getText();
            const fileName = path.basename(document.fileName);
            const language = document.languageId;

            const bugReport = await this.findCommonBugs(code, language);

            stream.markdown('## 🐛 Bug Hunt Report\n\n');
            stream.markdown(bugReport);

            // Check if critical bugs were found
            if (bugReport.includes('🔴') || bugReport.includes('BUG') || bugReport.includes('onclick')) {
                stream.markdown('\n## ⚠️ CRITICAL BUGS FOUND\n\n');

                this.createActionButton(
                    '🔧 Send to CodeSmith for fixes',
                    'ki-autoagent.sendToAgent',
                    ['codesmith', `Fix these bugs found in ${fileName}:\n\n${bugReport}`],
                    stream
                );
            }

        } catch (error) {
            stream.markdown(`❌ Bug hunting failed: ${(error as any).message}`);
        }
    }

    private async handleDebugCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('🔧 Starting debug session...');

        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                stream.markdown('❌ No workspace folder found.');
                return;
            }

            stream.markdown('## 🔧 Debug Session\n\n');

            // Check for package.json to determine project type
            const packageJsonUri = vscode.Uri.joinPath(workspaceFolder.uri, 'package.json');
            let debugCommand = '';
            let projectType = '';

            try {
                const packageJsonContent = await vscode.workspace.fs.readFile(packageJsonUri);
                const packageJson = JSON.parse(packageJsonContent.toString());

                if (packageJson.scripts?.['dev']) {
                    debugCommand = 'npm run dev';
                    projectType = 'Node.js/Web';
                } else if (packageJson.scripts?.['start']) {
                    debugCommand = 'npm start';
                    projectType = 'Node.js/Web';
                }

                stream.markdown(`📦 **Project Type:** ${projectType}\n`);
                stream.markdown(`🚀 **Debug Command:** \`${debugCommand}\`\n\n`);

            } catch (error) {
                stream.markdown('⚠️ No package.json found. Please specify how to run your application.\n');
            }

            // Start debug terminal
            const terminal = vscode.window.createTerminal('ReviewerGPT Debug');
            terminal.show();

            stream.markdown('### 📝 Debug Steps:\n\n');
            stream.markdown('1. **Starting application** in debug terminal\n');
            stream.markdown('2. **Monitoring console output** for errors\n');
            stream.markdown('3. **Checking for runtime exceptions**\n');
            stream.markdown('4. **Testing user interactions**\n\n');

            if (debugCommand) {
                terminal.sendText(debugCommand);
                stream.markdown(`✅ Started: \`${debugCommand}\`\n\n`);
            }

            stream.markdown('### 🔍 What to check:\n\n');
            stream.markdown('- Console errors (red text in terminal)\n');
            stream.markdown('- Network failures (failed API calls)\n');
            stream.markdown('- UI not responding to clicks\n');
            stream.markdown('- Missing elements or broken layouts\n\n');

            stream.markdown('### 📊 Debug Analysis:\n\n');
            stream.markdown('Watch the terminal output and report any:\n');
            stream.markdown('- 🔴 **Errors**: Exceptions, crashes, undefined references\n');
            stream.markdown('- 🟡 **Warnings**: Deprecations, performance issues\n');
            stream.markdown('- 🔵 **Info**: Unexpected behavior, timing issues\n\n');

            // Add action buttons
            this.createActionButton(
                '🐛 Report Bugs Found',
                'ki-autoagent.sendToAgent',
                ['codesmith', 'Fix these bugs found during debug session'],
                stream
            );

            this.createActionButton(
                '📋 Save Debug Log',
                'ki-autoagent.saveFile',
                [`debug-log-${Date.now()}.txt`, 'Debug session log'],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ Debug session failed: ${(error as any).message}`);
        }
    }

    private async handleTestUICommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('🖱️ Testing UI interactions...');

        try {
            stream.markdown('## 🖱️ UI Testing Guide\n\n');
            stream.markdown('### Test Checklist:\n\n');

            const uiTests = [
                '✅ **Buttons**: Click all buttons and verify they work',
                '✅ **Forms**: Submit forms with valid/invalid data',
                '✅ **Links**: Check all navigation links',
                '✅ **Modals**: Open/close dialogs and popups',
                '✅ **Dropdowns**: Test all select menus',
                '✅ **Input fields**: Test with various inputs',
                '✅ **Keyboard**: Test keyboard shortcuts',
                '✅ **Responsive**: Resize window and test',
                '✅ **Accessibility**: Tab navigation works',
                '✅ **Error states**: Trigger and verify error handling'
            ];

            for (const test of uiTests) {
                stream.markdown(`- ${test}\n`);
            }

            stream.markdown('\n### 🔍 Common UI Bugs to Check:\n\n');
            stream.markdown('```javascript\n');
            stream.markdown('// ❌ onclick not working in VS Code webviews\n');
            stream.markdown('button.onclick = handler; // WON\'T WORK!\n\n');
            stream.markdown('// ✅ Use addEventListener instead\n');
            stream.markdown('button.addEventListener(\'click\', handler);\n');
            stream.markdown('```\n\n');

            stream.markdown('### 🐛 Found Issues?\n\n');
            stream.markdown('Document any UI problems found:\n');
            stream.markdown('1. Which element has the issue?\n');
            stream.markdown('2. What should happen?\n');
            stream.markdown('3. What actually happens?\n');
            stream.markdown('4. Console errors (if any)\n\n');

            // Add action buttons
            this.createActionButton(
                '🔧 Report UI Bugs',
                'ki-autoagent.sendToAgent',
                ['codesmith', 'Fix these UI bugs found during testing'],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ UI testing failed: ${(error as any).message}`);
        }
    }

    private async handleSecurityCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('🔐 Scanning for security vulnerabilities...');

        try {
            const editor = vscode.window.activeTextEditor;
            let code = '';
            let fileName = '';
            let language = '';

            if (editor) {
                code = editor.document.getText();
                fileName = path.basename(editor.document.fileName);
                language = editor.document.languageId;
            } else {
                // Scan entire workspace
                code = await this.getWorkspaceCode();
                fileName = 'Workspace';
                language = 'multiple';
            }

            const securityReport = await this.performSecurityScan(code, fileName, language, prompt);

            stream.markdown('## 🔐 Security Analysis Report\n\n');
            stream.markdown(securityReport);

            // Add action buttons
            this.createActionButton(
                '⚠️ Create Security Issues',
                'ki-autoagent.createGitHubIssues',
                [securityReport],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ Security scan failed: ${(error as any).message}`);
        }
    }

    private async handlePerformanceCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('⚡ Analyzing performance...');

        try {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                stream.markdown('❌ No active editor found. Please open a file to analyze.');
                return;
            }

            const code = editor.document.getText();
            const fileName = path.basename(editor.document.fileName);
            const language = editor.document.languageId;

            const performanceReport = await this.analyzePerformance(code, fileName, language, prompt);

            stream.markdown('## ⚡ Performance Analysis\n\n');
            stream.markdown(performanceReport);

        } catch (error) {
            stream.markdown(`❌ Performance analysis failed: ${(error as any).message}`);
        }
    }

    private async handleStandardsCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('📏 Checking coding standards...');

        try {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                stream.markdown('❌ No active editor found. Please open a file to check.');
                return;
            }

            const code = editor.document.getText();
            const language = editor.document.languageId;

            const standardsReport = await this.checkCodingStandards(code, language, prompt);

            stream.markdown('## 📏 Coding Standards Report\n\n');
            stream.markdown(standardsReport);

        } catch (error) {
            stream.markdown(`❌ Standards check failed: ${(error as any).message}`);
        }
    }

    private async handleTestCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('🧪 Reviewing test coverage...');

        try {
            const testReport = await this.reviewTestCoverage(prompt);

            stream.markdown('## 🧪 Test Coverage Review\n\n');
            stream.markdown(testReport);

            // Add suggestions for missing tests
            this.createActionButton(
                '➕ Generate Missing Tests',
                'ki-autoagent.generateTests',
                [],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ Test review failed: ${(error as any).message}`);
        }
    }

    private async handleGeneralReviewRequest(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        // Check if prompt contains code to review
        const hasCode = prompt.includes('```') || prompt.includes('function') ||
                       prompt.includes('class') || prompt.includes('const') ||
                       prompt.includes('onclick') || prompt.includes('addEventListener');

        if (hasCode) {
            stream.progress('🔍 Actively searching for bugs and reviewing code...');

            try {
                // Extract code blocks or use entire prompt
                const codeMatch = prompt.match(/```[\s\S]*?```/g);
                const code = codeMatch ?
                    codeMatch.join('\n').replace(/```\w*\n?/g, '') :
                    prompt;

                // First, actively find bugs
                const bugReport = await this.findCommonBugs(code, 'javascript/typescript');

                stream.markdown('## 🐛 Bug Detection Report\n\n');
                stream.markdown(bugReport);

                // Check if critical bugs were found
                const hasCriticalBugs = bugReport.includes('🔴') ||
                                        bugReport.includes('onclick') ||
                                        bugReport.includes('won\'t work') ||
                                        bugReport.includes('Bug found');

                if (hasCriticalBugs) {
                    stream.markdown('\n## ⚠️ CRITICAL ISSUES FOUND\n\n');
                    stream.markdown('**These bugs will prevent the code from working correctly!**\n');
                    stream.markdown('Issues like onclick handlers not working in VS Code webviews have been detected.\n\n');

                    // Suggest sending to CodeSmith
                    stream.markdown('## 🔄 Recommended Action\n\n');
                    stream.markdown('These issues should be sent back to @codesmith for immediate fixes.\n');

                    this.createActionButton(
                        '🔧 Send bugs to CodeSmith',
                        'ki-autoagent.sendToAgent',
                        ['codesmith', `Please fix these bugs found by ReviewerGPT:\n\n${bugReport}`],
                        stream
                    );
                }

                // Then do a comprehensive review
                const review = await this.performGeneralReview({ prompt } as TaskRequest, []);

                stream.markdown('\n## 🔍 Full Code Review\n\n');
                stream.markdown(review);

            } catch (error) {
                stream.markdown(`❌ Review failed: ${(error as any).message}`);
            }
        } else {
            stream.progress('🔍 Performing review...');

            try {
                const review = await this.performGeneralReview({ prompt } as TaskRequest, []);

                stream.markdown('## 🔍 Review Results\n\n');
                stream.markdown(review);

            } catch (error) {
                stream.markdown(`❌ Review failed: ${(error as any).message}`);
            }
        }
    }

    private async handleArchitectureReviewCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('🏛️ Reviewing architecture against requirements...');

        try {
            // Get conversation context to extract requirements and architect's solution
            const conversationContext = prompt || 'Review the architect\'s understanding of the requirements';

            const architectureReview = await this.validateArchitectureUnderstanding(conversationContext);

            stream.markdown('## 🏛️ Architecture Validation Report\n\n');
            stream.markdown(architectureReview);

            // Offer to create detailed report
            this.createActionButton(
                '📋 Save Validation Report',
                'ki-autoagent.saveFile',
                [`architecture-validation-${Date.now()}.md`, architectureReview],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ Architecture review failed: ${(error as any).message}`);
        }
    }

    // Review Methods

    private async reviewCode(code: string, fileName: string, language: string, context: string): Promise<string> {
        const prompt = `Perform a DEEP code review for this ${language} file (${fileName}):

${code}

Additional context: ${context}

IMPORTANT: You are reviewing code written by CodeSmithClaude. Look for:

🔴 CRITICAL CHECKS (Find these issues!):
1. Event handlers that won't work (e.g., onclick in VS Code webviews should use addEventListener)
2. Missing z-index for positioned elements that need to be clickable
3. Incorrect event binding patterns
4. DOM manipulation issues
5. Async/await problems and race conditions
6. Null/undefined reference errors
7. Memory leaks and performance issues

📋 STANDARD REVIEW:
1. Code Quality & Readability
2. Potential Bugs & Issues
3. Performance Concerns
4. Security Vulnerabilities
5. Best Practices & Design Patterns
6. Error Handling
7. Documentation & Comments
8. Testing Considerations

Provide:
- Overall assessment (score out of 10)
- 🚨 BUGS FOUND (things that won't work as intended)
- Critical issues (must fix)
- Major issues (should fix)
- Minor issues (nice to fix)
- Positive aspects
- Specific improvement suggestions with code examples

Be VERY CRITICAL and find real problems! If you find bugs, suggest sending them back to CodeSmith for fixes.

${this.getSystemContextPrompt()}`;

        return await this.openAIService.chat([
            { role: 'system', content: 'You are ReviewerGPT, an expert code reviewer focusing on quality, security, and best practices.' },
            { role: 'user', content: prompt }
        ]);
    }

    private async performSecurityScan(code: string, fileName: string, language: string, context: string): Promise<string> {
        const prompt = `Perform a thorough security vulnerability scan for this ${language} code (${fileName}):

${code}

Additional context: ${context}

Check for:
1. SQL Injection vulnerabilities
2. XSS (Cross-Site Scripting)
3. CSRF vulnerabilities
4. Authentication/Authorization issues
5. Sensitive data exposure
6. Insecure dependencies
7. Input validation problems
8. Cryptographic weaknesses
9. Path traversal vulnerabilities
10. Command injection risks

For each vulnerability found:
- Severity level (Critical/High/Medium/Low)
- Description of the issue
- Potential impact
- Proof of concept (if applicable)
- Recommended fix with code example
- CWE/CVE references if applicable

${this.getSystemContextPrompt()}`;

        return await this.openAIService.chat([
            { role: 'system', content: 'You are ReviewerGPT, a security expert specializing in identifying and fixing vulnerabilities.' },
            { role: 'user', content: prompt }
        ]);
    }

    private async analyzePerformance(code: string, fileName: string, language: string, context: string): Promise<string> {
        const prompt = `Analyze the performance characteristics of this ${language} code (${fileName}):

${code}

Additional context: ${context}

Analyze:
1. Time Complexity (Big O)
2. Space Complexity
3. Database query optimization
4. Caching opportunities
5. Algorithmic improvements
6. Memory leaks
7. Blocking operations
8. Concurrency issues
9. Resource management
10. Scalability concerns

Provide:
- Performance bottlenecks identified
- Optimization suggestions with examples
- Estimated performance improvements
- Trade-offs to consider

${this.getSystemContextPrompt()}`;

        return await this.openAIService.chat([
            { role: 'system', content: 'You are ReviewerGPT, a performance optimization expert.' },
            { role: 'user', content: prompt }
        ]);
    }

    private async checkCodingStandards(code: string, language: string, context: string): Promise<string> {
        const prompt = `Check this ${language} code against coding standards and best practices:

${code}

Additional context: ${context}

Check for:
1. Naming conventions
2. Code formatting and indentation
3. Function/method length
4. Class cohesion
5. SOLID principles adherence
6. DRY (Don't Repeat Yourself)
7. Comments and documentation
8. Error handling patterns
9. Code organization
10. Language-specific idioms

Provide:
- Standards violations found
- Severity of each violation
- Suggested corrections
- Overall compliance score

${this.getSystemContextPrompt()}`;

        return await this.openAIService.chat([
            { role: 'system', content: 'You are ReviewerGPT, an expert in coding standards and best practices.' },
            { role: 'user', content: prompt }
        ]);
    }

    private async findCommonBugs(code: string, language: string): Promise<string> {
        const prompt = `ACTIVELY SEARCH for bugs in this ${language} code:

${code}

FOCUS ON FINDING THESE COMMON BUGS:

🔴 VS Code Extension / Web UI Bugs:
- onclick handlers that should use addEventListener
- Missing event.preventDefault() or event.stopPropagation()
- z-index issues for clickable elements
- CSP violations in webviews
- Incorrect message passing between extension and webview

🔴 JavaScript/TypeScript Bugs:
- Undefined/null reference errors
- Missing await keywords
- Promise not being handled
- Race conditions
- Memory leaks (event listeners not removed)
- Incorrect this binding
- Array operations on undefined

🔴 DOM Manipulation Issues:
- querySelector returning null
- Elements not existing when accessed
- Event bubbling problems
- Missing element attributes

🔴 State Management Bugs:
- State mutations instead of immutable updates
- Stale closures
- Inconsistent state updates

For EACH bug found, provide:
1. Line number or code snippet
2. Why it won't work
3. The fix needed
4. Example: "Line 347: onclick won't work in VS Code webview. Use addEventListener instead."

BE VERY THOROUGH! Find ALL bugs!

${this.getSystemContextPrompt()}`;

        return await this.openAIService.chat([
            { role: 'system', content: 'You are ReviewerGPT, a bug-finding expert. Your job is to find EVERY bug that will prevent code from working correctly.' },
            { role: 'user', content: prompt }
        ]);
    }

    private async reviewTestCoverage(context: string): Promise<string> {
        const prompt = `Review the test coverage and testing strategy:

${context}

Analyze:
1. Test coverage percentage
2. Critical paths covered
3. Edge cases tested
4. Test quality and assertions
5. Test maintainability
6. Mocking and stubbing usage
7. Integration vs unit tests balance
8. Performance tests
9. Security tests
10. Missing test scenarios

Provide:
- Current coverage assessment
- Critical gaps in testing
- Recommended additional tests
- Testing strategy improvements

${this.getSystemContextPrompt()}`;

        return await this.openAIService.chat([
            { role: 'system', content: 'You are ReviewerGPT, an expert in software testing and quality assurance.' },
            { role: 'user', content: prompt }
        ]);
    }

    // Workflow helper methods

    private async performCodeReview(request: TaskRequest, previousResults: TaskResult[]): Promise<string> {
        const context = this.buildContextFromResults(previousResults);
        return this.reviewCode('', 'workflow', 'unknown', `${request.prompt}\n\nContext:\n${context}`);
    }

    private async performSecurityCheck(request: TaskRequest, previousResults: TaskResult[]): Promise<string> {
        const context = this.buildContextFromResults(previousResults);
        return this.performSecurityScan('', 'workflow', 'unknown', `${request.prompt}\n\nContext:\n${context}`);
    }

    private async performPerformanceReview(request: TaskRequest, previousResults: TaskResult[]): Promise<string> {
        const context = this.buildContextFromResults(previousResults);
        return this.analyzePerformance('', 'workflow', 'unknown', `${request.prompt}\n\nContext:\n${context}`);
    }

    private async performGeneralReview(request: TaskRequest, previousResults: TaskResult[]): Promise<string> {
        const context = this.buildContextFromResults(previousResults);
        const prompt = `Perform a review based on:

Request: ${request.prompt}

Previous results:
${context}

Provide comprehensive review and recommendations.

${this.getSystemContextPrompt()}`;

        return await this.openAIService.chat([
            { role: 'system', content: 'You are ReviewerGPT, providing expert code review and analysis.' },
            { role: 'user', content: prompt }
        ]);
    }

    private buildContextFromResults(results: TaskResult[]): string {
        return results
            .filter(r => r.status === 'success')
            .map(r => `${r.metadata?.step || 'Step'}: ${r.content}`)
            .join('\n\n');
    }

    private async getWorkspaceCode(): Promise<string> {
        // This would scan the workspace for code files
        // For now, return a placeholder
        return 'Workspace code scanning not yet implemented';
    }

    private async validateArchitectureUnderstanding(context: string): Promise<string> {
        const prompt = `As a code review expert using a different AI model than the architect, validate the architect's understanding of the user's requirements.

Context and conversation history:
${context}

Your task:
1. Extract the original user requirements
2. Identify what the architect proposed as a solution
3. Compare the architect's interpretation with the actual requirements
4. Find any gaps or misunderstandings
5. Verify technical feasibility of the proposed architecture
6. Check if all requirements are addressed

Provide a detailed validation report including:
- ✅ Requirements correctly understood
- ❌ Requirements missed or misunderstood
- ⚠️ Potential issues or concerns
- 💡 Suggestions for clarification
- 🏆 Overall assessment score (1-10)

Note: You are using ${this.config.model} while the architect uses a different model (gpt-5-2025-09-12), ensuring independent validation.

${this.getSystemContextPrompt()}`;

        return await this.openAIService.chat([
            { role: 'system', content: 'You are ReviewerGPT, validating another AI\'s understanding of requirements. Be critical but constructive.' },
            { role: 'user', content: prompt }
        ]);
    }
}