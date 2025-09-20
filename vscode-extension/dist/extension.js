/******/ (() => { // webpackBootstrap
/******/ 	"use strict";
/******/ 	var __webpack_modules__ = ({

/***/ "./src/agents/ArchitectAgent.ts":
/*!**************************************!*\
  !*** ./src/agents/ArchitectAgent.ts ***!
  \**************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {


var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.ArchitectAgent = void 0;
/**
 * ArchitectGPT - System Architecture & Design Expert
 * Powered by GPT-4o for system design and architecture planning
 */
const vscode = __importStar(__webpack_require__(/*! vscode */ "vscode"));
const ChatAgent_1 = __webpack_require__(/*! ./base/ChatAgent */ "./src/agents/base/ChatAgent.ts");
const OpenAIService_1 = __webpack_require__(/*! ../utils/OpenAIService */ "./src/utils/OpenAIService.ts");
class ArchitectAgent extends ChatAgent_1.ChatAgent {
    constructor(context, dispatcher) {
        const config = {
            participantId: 'ki-autoagent.architect',
            name: 'architect',
            fullName: 'ArchitectGPT',
            description: 'System Architecture & Design Expert powered by GPT-5',
            model: 'gpt-5-2025-09-12',
            iconPath: vscode.Uri.joinPath(context.extensionUri, 'media', 'openai-icon.svg'),
            capabilities: [
                'System Design',
                'Architecture Patterns',
                'Tech Stack Planning',
                'Scalability Analysis',
                'Design Documentation'
            ],
            commands: [
                { name: 'design', description: 'Create system architecture and design patterns', handler: 'handleDesignCommand' },
                { name: 'analyze', description: 'Analyze existing codebase architecture', handler: 'handleAnalyzeCommand' },
                { name: 'plan', description: 'Create development and deployment plans', handler: 'handlePlanCommand' }
            ]
        };
        super(config, context, dispatcher);
        this.openAIService = new OpenAIService_1.OpenAIService();
    }
    async handleRequest(request, context, stream, token) {
        if (!this.validateApiConfig()) {
            stream.markdown('❌ OpenAI API key not configured. Please set it in VS Code settings.');
            return;
        }
        const command = request.command;
        const prompt = request.prompt;
        this.log(`Processing ${command ? `/${command}` : 'general'} request: ${prompt.substring(0, 100)}...`);
        if (command) {
            await this.handleCommand(command, prompt, stream, token);
        }
        else {
            // General architecture request
            await this.handleGeneralArchitectureRequest(prompt, stream, token);
        }
    }
    async processWorkflowStep(step, request, previousResults) {
        const context = await this.getWorkspaceContext();
        let systemPrompt = '';
        let userPrompt = '';
        switch (step.id) {
            case 'analyze':
                systemPrompt = this.getAnalyzeSystemPrompt();
                userPrompt = `Analyze the architecture requirements for: ${request.prompt}\n\nWorkspace Context:\n${context}`;
                break;
            case 'design':
                systemPrompt = this.getDesignSystemPrompt();
                userPrompt = `Create a system architecture design for: ${request.prompt}\n\nPrevious Analysis:\n${this.extractPreviousContent(previousResults)}`;
                break;
            default:
                systemPrompt = this.getGeneralSystemPrompt();
                userPrompt = `${request.prompt}\n\nContext:\n${context}`;
        }
        try {
            const response = await this.openAIService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);
            return {
                status: 'success',
                content: response,
                metadata: {
                    step: step.id,
                    agent: 'architect',
                    model: 'gpt-4o'
                }
            };
        }
        catch (error) {
            throw new Error(`Failed to process ${step.id}: ${error.message}`);
        }
    }
    // Command Handlers
    async handleDesignCommand(prompt, stream, token) {
        stream.progress('🏗️ Analyzing requirements and creating system design...');
        const context = await this.getWorkspaceContext();
        const systemPrompt = this.getDesignSystemPrompt();
        const userPrompt = `Create a comprehensive system architecture design for: ${prompt}\n\nWorkspace Context:\n${context}`;
        try {
            const response = await this.openAIService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);
            stream.markdown(response);
            // Offer to create architecture documentation
            this.createActionButton('📄 Create Architecture Document', 'ki-autoagent.createFile', ['ARCHITECTURE.md', response], stream);
            // Offer to proceed with implementation planning
            this.createActionButton('⚡ Plan Implementation', 'ki-autoagent.planImplementation', [prompt, response], stream);
        }
        catch (error) {
            stream.markdown(`❌ Error creating design: ${error.message}`);
        }
    }
    async handleAnalyzeCommand(prompt, stream, token) {
        stream.progress('🔍 Analyzing existing codebase architecture...');
        const context = await this.getWorkspaceContext();
        // Get project files for analysis
        const workspaceFiles = await this.getProjectStructure();
        const systemPrompt = this.getAnalyzeSystemPrompt();
        const userPrompt = `Analyze the architecture of this codebase: ${prompt}\n\nProject Structure:\n${workspaceFiles}\n\nWorkspace Context:\n${context}`;
        try {
            const response = await this.openAIService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);
            stream.markdown(response);
            // Offer architecture improvements
            this.createActionButton('🚀 Suggest Improvements', 'ki-autoagent.suggestImprovements', [response], stream);
        }
        catch (error) {
            stream.markdown(`❌ Error analyzing architecture: ${error.message}`);
        }
    }
    async handlePlanCommand(prompt, stream, token) {
        stream.progress('📋 Creating development and deployment plans...');
        const context = await this.getWorkspaceContext();
        const systemPrompt = this.getPlanSystemPrompt();
        const userPrompt = `Create a detailed development and deployment plan for: ${prompt}\n\nWorkspace Context:\n${context}`;
        try {
            const response = await this.openAIService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);
            stream.markdown(response);
            // Offer to create project roadmap
            this.createActionButton('🗺️ Create Roadmap', 'ki-autoagent.createFile', ['ROADMAP.md', response], stream);
        }
        catch (error) {
            stream.markdown(`❌ Error creating plan: ${error.message}`);
        }
    }
    async handleGeneralArchitectureRequest(prompt, stream, token) {
        stream.progress('🤔 Processing architecture request...');
        const context = await this.getWorkspaceContext();
        const systemPrompt = this.getGeneralSystemPrompt();
        const userPrompt = `${prompt}\n\nWorkspace Context:\n${context}`;
        try {
            const response = await this.openAIService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);
            stream.markdown(response);
        }
        catch (error) {
            stream.markdown(`❌ Error processing request: ${error.message}`);
        }
    }
    // System Prompts
    getGeneralSystemPrompt() {
        return `You are ArchitectGPT, a senior system architect and design expert. You specialize in:

- System architecture design and patterns
- Technology stack selection and evaluation
- Scalability and performance planning
- Microservices and distributed systems
- Database design and data modeling
- API design and integration patterns
- Security architecture
- DevOps and deployment strategies

Always provide:
1. Clear architectural reasoning
2. Multiple solution options when applicable
3. Trade-offs and considerations
4. Implementation guidance
5. Best practices and patterns

Format your responses with clear headings, diagrams where helpful (using mermaid syntax), and actionable recommendations.

${this.getSystemContextPrompt()}`;
    }
    getDesignSystemPrompt() {
        return `You are ArchitectGPT creating a comprehensive system architecture design. Follow this structure:

## System Architecture Design

### 1. Requirements Analysis
- Functional requirements
- Non-functional requirements (performance, scalability, security)
- Constraints and assumptions

### 2. High-Level Architecture
- System overview
- Major components and their responsibilities
- Data flow and interactions

### 3. Technology Stack
- Recommended technologies with rationale
- Alternatives considered
- Integration points

### 4. Database Design
- Data model
- Storage strategy
- Performance considerations

### 5. API Design
- Interface specifications
- Authentication/authorization
- Rate limiting and caching

### 6. Security Architecture
- Security measures
- Authentication/authorization
- Data protection

### 7. Deployment Architecture
- Infrastructure requirements
- Scaling strategy
- Monitoring and observability

### 8. Implementation Roadmap
- Development phases
- Dependencies and milestones
- Risk mitigation

Use mermaid diagrams where appropriate to illustrate the architecture.

${this.getSystemContextPrompt()}`;
    }
    getAnalyzeSystemPrompt() {
        return `You are ArchitectGPT analyzing an existing codebase architecture. Provide:

## Architecture Analysis

### 1. Current Architecture Overview
- Identify architectural patterns used
- Component structure and organization
- Technology stack assessment

### 2. Strengths
- What's working well
- Good design decisions
- Proper patterns implementation

### 3. Areas for Improvement
- Architectural debt
- Performance bottlenecks
- Security concerns
- Scalability limitations

### 4. Recommendations
- Prioritized improvement suggestions
- Refactoring opportunities
- Technology upgrades

### 5. Next Steps
- Immediate actions
- Long-term architectural goals
- Migration strategies

Be specific and provide actionable insights based on the codebase structure.

${this.getSystemContextPrompt()}`;
    }
    getPlanSystemPrompt() {
        return `You are ArchitectGPT creating development and deployment plans. Structure your response as:

## Development & Deployment Plan

### 1. Project Setup
- Repository structure
- Development environment
- Tool and dependency setup

### 2. Development Phases
- Phase breakdown with deliverables
- Timeline estimates
- Resource requirements

### 3. Implementation Strategy
- Development methodology
- Code review process
- Testing strategy

### 4. Deployment Strategy
- Environment setup (dev, staging, prod)
- CI/CD pipeline
- Rollback procedures

### 5. Risk Management
- Identified risks
- Mitigation strategies
- Contingency plans

### 6. Success Metrics
- KPIs and measurements
- Monitoring and alerting
- Performance benchmarks

Provide realistic timelines and clear milestones.

${this.getSystemContextPrompt()}`;
    }
    // Helper Methods
    async getProjectStructure() {
        try {
            const files = await vscode.workspace.findFiles('**/*.{py,js,ts,jsx,tsx,json,md}', '**/node_modules/**', 50);
            return files.map(file => file.fsPath.split('/').slice(-3).join('/')).join('\n');
        }
        catch (error) {
            return 'Unable to read project structure';
        }
    }
    extractPreviousContent(previousResults) {
        return previousResults
            .map(result => result.content)
            .join('\n\n---\n\n')
            .substring(0, 2000); // Limit context size
    }
}
exports.ArchitectAgent = ArchitectAgent;


/***/ }),

/***/ "./src/agents/CodeSmithAgent.ts":
/*!**************************************!*\
  !*** ./src/agents/CodeSmithAgent.ts ***!
  \**************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {


var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.CodeSmithAgent = void 0;
/**
 * CodeSmithClaude - Senior Python/Web Developer
 * Powered by Claude 3.5 Sonnet for code implementation and optimization
 */
const vscode = __importStar(__webpack_require__(/*! vscode */ "vscode"));
const ChatAgent_1 = __webpack_require__(/*! ./base/ChatAgent */ "./src/agents/base/ChatAgent.ts");
const AnthropicService_1 = __webpack_require__(/*! ../utils/AnthropicService */ "./src/utils/AnthropicService.ts");
const ClaudeCodeService_1 = __webpack_require__(/*! ../services/ClaudeCodeService */ "./src/services/ClaudeCodeService.ts");
class CodeSmithAgent extends ChatAgent_1.ChatAgent {
    constructor(context, dispatcher) {
        const config = {
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
        this.anthropicService = new AnthropicService_1.AnthropicService();
        this.claudeCodeService = (0, ClaudeCodeService_1.getClaudeCodeService)();
    }
    async handleRequest(request, context, stream, token) {
        const validationResult = await this.validateServiceConfig(stream);
        if (!validationResult) {
            return;
        }
        const command = request.command;
        const prompt = request.prompt;
        this.log(`Processing ${command ? `/${command}` : 'general'} request: ${prompt.substring(0, 100)}...`);
        if (command) {
            await this.handleCommand(command, prompt, stream, token);
        }
        else {
            await this.handleGeneralImplementationRequest(prompt, stream, token);
        }
    }
    // Override executeStep to use our custom implementation
    async executeStep(step, request, previousResults) {
        this.showDebug(`ExecuteStep called`, {
            step: step.id,
            hasStreamingCallback: !!request.onPartialResponse
        });
        return await this.processWorkflowStep(step, request, previousResults);
    }
    async processWorkflowStep(step, request, previousResults) {
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
                : response.content || '';
            // Extract metadata from response if available
            const responseMetadata = typeof response === 'object' && response !== null
                ? response.metadata
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
        }
        catch (error) {
            throw new Error(`Failed to process ${step.id}: ${error.message}`);
        }
    }
    // Command Handlers
    async handleImplementCommand(prompt, stream, token) {
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
                : response.content || '';
            stream.markdown(responseContent);
            // Extract code blocks for file creation
            const codeBlocks = this.extractCodeBlocks(responseContent);
            for (const block of codeBlocks) {
                if (block.filename) {
                    this.createActionButton(`📄 Create ${block.filename}`, 'ki-autoagent.createFile', [block.filename, block.code], stream);
                }
            }
            // Offer to create tests
            this.createActionButton('🧪 Generate Tests', 'ki-autoagent.generateTests', [prompt, response], stream);
        }
        catch (error) {
            stream.markdown(`❌ Error during implementation: ${error.message}`);
        }
    }
    async handleOptimizeCommand(prompt, stream, token) {
        stream.progress('🚀 Optimizing code for performance...');
        const context = await this.getWorkspaceContext();
        const systemPrompt = this.getOptimizationSystemPrompt();
        // Include current file content if available
        let codeToOptimize = '';
        if (context.includes('Selected text:')) {
            codeToOptimize = context;
        }
        else if (vscode.window.activeTextEditor) {
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
                : response.content || '';
            stream.markdown(responseContent);
            // Offer to apply optimizations
            const optimizedCode = this.extractMainCodeBlock(responseContent);
            if (optimizedCode) {
                this.createActionButton('✨ Apply Optimization', 'ki-autoagent.insertAtCursor', [optimizedCode], stream);
            }
        }
        catch (error) {
            stream.markdown(`❌ Error during optimization: ${error.message}`);
        }
    }
    async handleTestCommand(prompt, stream, token) {
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
                : response.content || '';
            stream.markdown(responseContent);
            // Extract test files for creation
            const testFiles = this.extractTestFiles(responseContent);
            for (const testFile of testFiles) {
                this.createActionButton(`🧪 Create ${testFile.filename}`, 'ki-autoagent.createFile', [testFile.filename, testFile.code], stream);
            }
            // Offer to run tests
            this.createActionButton('▶️ Run Tests', 'ki-autoagent.runTests', [], stream);
        }
        catch (error) {
            stream.markdown(`❌ Error generating tests: ${error.message}`);
        }
    }
    async handleFixCommand(prompt, stream, token) {
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
                : response.content || '';
            stream.markdown(responseContent);
        }
        catch (error) {
            stream.markdown(`❌ Error during bug fix: ${error.message}`);
        }
    }
    async handleDebugCommand(prompt, stream, token) {
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
                : response.content || '';
            stream.markdown(responseContent);
        }
        catch (error) {
            stream.markdown(`❌ Error during debugging: ${error.message}`);
        }
    }
    async handleRefactorCommand(prompt, stream, token) {
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
                : response.content || '';
            stream.markdown(responseContent);
        }
        catch (error) {
            stream.markdown(`❌ Error during refactoring: ${error.message}`);
        }
    }
    async handleModernizeCommand(prompt, stream, token) {
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
                : response.content || '';
            stream.markdown(responseContent);
        }
        catch (error) {
            stream.markdown(`❌ Error during modernization: ${error.message}`);
        }
    }
    async handleGeneralImplementationRequest(prompt, stream, token) {
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
                : response.content || '';
            stream.markdown(responseContent);
            // Auto-detect and offer file creation
            const codeBlocks = this.extractCodeBlocks(responseContent);
            for (const block of codeBlocks) {
                if (block.filename) {
                    this.createActionButton(`📄 Create ${block.filename}`, 'ki-autoagent.createFile', [block.filename, block.code], stream);
                }
            }
        }
        catch (error) {
            stream.markdown(`❌ Error processing request: ${error.message}`);
        }
    }
    // System Prompts
    getGeneralSystemPrompt() {
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
    getImplementationSystemPrompt() {
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
    getOptimizationSystemPrompt() {
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
    getTestingSystemPrompt() {
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
    async validateServiceConfig(stream) {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        const serviceMode = config.get('claude.serviceMode', 'claude-code');
        if (serviceMode === 'api') {
            if (!config.get('anthropic.apiKey')) {
                if (stream) {
                    stream.markdown('❌ **Anthropic API key not configured**\n\nPlease set your API key in VS Code settings:\n- Go to Settings\n- Search for "KI AutoAgent"\n- Set your Anthropic API key');
                }
                return false;
            }
        }
        else if (serviceMode === 'claude-code') {
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
    async getClaudeService(onPartialResponse) {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        const serviceMode = config.get('claude.serviceMode', 'claude-code');
        this.showDebug('Service configuration', {
            serviceMode,
            hasStreamingCallback: !!onPartialResponse
        });
        if (serviceMode === 'claude-code') {
            const isAvailable = await this.claudeCodeService.isAvailable();
            if (isAvailable) {
                this.showInfo('Using Claude Code CLI');
                return {
                    chat: async (messages) => {
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
                        }
                        else {
                            const response = await this.claudeCodeService.sendMessage(fullPrompt, {
                                model: 'sonnet',
                                temperature: 0.7
                            });
                            return response.content;
                        }
                    }
                };
            }
            else {
                this.showFallbackMode('Claude Code CLI not available', 'Using Anthropic API');
            }
        }
        // Fall back to Anthropic API
        this.showInfo('Using Anthropic API');
        return {
            chat: async (messages) => {
                return await this.anthropicService.chat(messages);
            }
        };
    }
    // Helper Methods
    extractCodeBlocks(content) {
        const codeBlockRegex = /```(\w+)?\s*(?:\/\/\s*(.+\.[\w]+))?\n([\s\S]*?)```/g;
        const blocks = [];
        let match;
        while ((match = codeBlockRegex.exec(content)) !== null) {
            const language = match[1] || 'text';
            const filename = match[2] || this.inferFilename(language, match[3]);
            const code = match[3];
            blocks.push({ filename, language, code });
        }
        return blocks;
    }
    extractTestFiles(content) {
        const blocks = this.extractCodeBlocks(content);
        return blocks
            .filter(block => block.filename &&
            (block.filename.includes('test') || block.filename.includes('spec')))
            .map(block => ({ filename: block.filename, code: block.code }));
    }
    extractMainCodeBlock(content) {
        const blocks = this.extractCodeBlocks(content);
        return blocks.length > 0 ? blocks[0].code : '';
    }
    inferFilename(language, code) {
        // Try to infer filename from code content
        if (language === 'python') {
            const classMatch = code.match(/class\s+(\w+)/);
            if (classMatch) {
                return `${classMatch[1].toLowerCase()}.py`;
            }
            return 'main.py';
        }
        else if (language === 'typescript' || language === 'javascript') {
            const classMatch = code.match(/(?:class|interface)\s+(\w+)/);
            if (classMatch) {
                return `${classMatch[1]}.${language === 'typescript' ? 'ts' : 'js'}`;
            }
            return `index.${language === 'typescript' ? 'ts' : 'js'}`;
        }
        return `code.${language}`;
    }
    extractPreviousContent(previousResults) {
        return previousResults
            .map(result => result.content)
            .join('\n\n---\n\n')
            .substring(0, 2000); // Limit context size
    }
}
exports.CodeSmithAgent = CodeSmithAgent;


/***/ }),

/***/ "./src/agents/DocuBotAgent.ts":
/*!************************************!*\
  !*** ./src/agents/DocuBotAgent.ts ***!
  \************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {


var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.DocuBotAgent = void 0;
/**
 * DocuBot - Technical Documentation Expert
 * Creates comprehensive documentation, READMEs, and API references
 */
const vscode = __importStar(__webpack_require__(/*! vscode */ "vscode"));
const ChatAgent_1 = __webpack_require__(/*! ./base/ChatAgent */ "./src/agents/base/ChatAgent.ts");
const OpenAIService_1 = __webpack_require__(/*! ../utils/OpenAIService */ "./src/utils/OpenAIService.ts");
const path = __importStar(__webpack_require__(/*! path */ "path"));
const fs = __importStar(__webpack_require__(/*! fs/promises */ "fs/promises"));
class DocuBotAgent extends ChatAgent_1.ChatAgent {
    constructor(context, dispatcher) {
        const config = {
            participantId: 'ki-autoagent.docu',
            name: 'docu',
            fullName: 'DocuBot',
            description: 'Technical Documentation Expert - Creates READMEs, API docs, user guides',
            model: 'gpt-5-2025-09-12',
            iconPath: vscode.Uri.joinPath(context.extensionUri, 'media', 'docu-icon.svg'),
            capabilities: [
                'README Generation',
                'API Documentation',
                'User Guides',
                'Code Comments',
                'Technical Writing',
                'Markdown Formatting',
                'JSDoc/DocStrings',
                'Changelog Creation'
            ],
            commands: [
                { name: 'readme', description: 'Generate README for project', handler: 'handleReadmeCommand' },
                { name: 'api', description: 'Create API documentation', handler: 'handleApiCommand' },
                { name: 'guide', description: 'Write user guide or tutorial', handler: 'handleGuideCommand' },
                { name: 'comments', description: 'Add documentation comments to code', handler: 'handleCommentsCommand' },
                { name: 'changelog', description: 'Generate changelog from commits', handler: 'handleChangelogCommand' },
                { name: 'update-instructions', description: 'Update agent instruction files', handler: 'handleUpdateInstructionsCommand' },
                { name: 'view-instructions', description: 'View agent instruction files', handler: 'handleViewInstructionsCommand' }
            ]
        };
        super(config, context, dispatcher);
        this.openAIService = new OpenAIService_1.OpenAIService();
    }
    async handleRequest(request, context, stream, token) {
        const command = request.command;
        const prompt = request.prompt;
        this.log(`Processing ${command ? `/${command}` : 'general'} documentation request: ${prompt.substring(0, 100)}...`);
        if (command) {
            await this.handleCommand(command, prompt, stream, token);
        }
        else {
            await this.handleGeneralDocumentationRequest(prompt, stream, token);
        }
    }
    async processWorkflowStep(step, request, previousResults) {
        try {
            let documentationContent = '';
            switch (step.id) {
                case 'document_code':
                    documentationContent = await this.generateCodeDocumentation(request, previousResults);
                    break;
                case 'create_readme':
                    documentationContent = await this.generateReadme(request, previousResults);
                    break;
                case 'api_docs':
                    documentationContent = await this.generateApiDocs(request, previousResults);
                    break;
                default:
                    documentationContent = await this.generateGeneralDocs(request, previousResults);
            }
            return {
                status: 'success',
                content: documentationContent,
                metadata: {
                    step: step.id,
                    agent: 'docu',
                    type: 'documentation'
                }
            };
        }
        catch (error) {
            throw new Error(`Failed to process documentation step ${step.id}: ${error.message}`);
        }
    }
    // Command Handlers
    async handleReadmeCommand(prompt, stream, token) {
        stream.progress('📝 Analyzing project structure...');
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                stream.markdown('❌ No workspace folder found');
                return;
            }
            // Analyze project structure
            const projectInfo = await this.analyzeProjectStructure(workspaceFolder.uri.fsPath);
            stream.progress('📝 Generating README...');
            const readmeContent = await this.createReadme(projectInfo, prompt);
            stream.markdown('## 📝 Generated README\n\n');
            stream.markdown('```markdown\n' + readmeContent + '\n```');
            // Offer to save
            this.createActionButton('💾 Save README.md', 'ki-autoagent.saveFile', ['README.md', readmeContent], stream);
        }
        catch (error) {
            stream.markdown(`❌ README generation failed: ${error.message}`);
        }
    }
    async handleApiCommand(prompt, stream, token) {
        stream.progress('🔍 Analyzing code for API endpoints...');
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                stream.markdown('❌ No workspace folder found');
                return;
            }
            // Find and analyze API endpoints
            const apiInfo = await this.analyzeApiEndpoints(workspaceFolder.uri.fsPath);
            stream.progress('📖 Generating API documentation...');
            const apiDocs = await this.createApiDocumentation(apiInfo, prompt);
            stream.markdown('## 📖 API Documentation\n\n');
            stream.markdown('```markdown\n' + apiDocs + '\n```');
            // Offer to save
            this.createActionButton('💾 Save API.md', 'ki-autoagent.saveFile', ['docs/API.md', apiDocs], stream);
        }
        catch (error) {
            stream.markdown(`❌ API documentation generation failed: ${error.message}`);
        }
    }
    async handleGuideCommand(prompt, stream, token) {
        stream.progress('📚 Creating user guide...');
        try {
            const guide = await this.createUserGuide(prompt);
            stream.markdown('## 📚 User Guide\n\n');
            stream.markdown(guide);
            // Offer to save
            this.createActionButton('💾 Save Guide', 'ki-autoagent.saveFile', ['docs/USER_GUIDE.md', guide], stream);
        }
        catch (error) {
            stream.markdown(`❌ Guide creation failed: ${error.message}`);
        }
    }
    async handleCommentsCommand(prompt, stream, token) {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            stream.markdown('❌ No active editor found. Please open a file to document.');
            return;
        }
        stream.progress('💬 Adding documentation comments...');
        try {
            const document = editor.document;
            const code = document.getText();
            const language = document.languageId;
            const documentedCode = await this.addDocumentationComments(code, language, prompt);
            stream.markdown('## 💬 Documented Code\n\n');
            stream.markdown('```' + language + '\n' + documentedCode + '\n```');
            // Offer to replace
            this.createActionButton('💾 Apply Comments', 'ki-autoagent.replaceContent', [documentedCode], stream);
        }
        catch (error) {
            stream.markdown(`❌ Comment generation failed: ${error.message}`);
        }
    }
    async handleChangelogCommand(prompt, stream, token) {
        stream.progress('📋 Analyzing commit history...');
        try {
            // Get git log
            const gitLog = await this.getGitLog();
            stream.progress('📋 Generating changelog...');
            const changelog = await this.createChangelog(gitLog, prompt);
            stream.markdown('## 📋 Changelog\n\n');
            stream.markdown('```markdown\n' + changelog + '\n```');
            // Offer to save
            this.createActionButton('💾 Save CHANGELOG.md', 'ki-autoagent.saveFile', ['CHANGELOG.md', changelog], stream);
        }
        catch (error) {
            stream.markdown(`❌ Changelog generation failed: ${error.message}`);
        }
    }
    async handleGeneralDocumentationRequest(prompt, stream, token) {
        stream.progress('📝 Creating documentation...');
        try {
            const documentation = await this.createGeneralDocumentation(prompt);
            stream.markdown('## 📝 Documentation\n\n');
            stream.markdown(documentation);
        }
        catch (error) {
            stream.markdown(`❌ Documentation creation failed: ${error.message}`);
        }
    }
    async handleUpdateInstructionsCommand(prompt, stream, token) {
        stream.progress('📝 Updating agent instructions...');
        try {
            // Parse agent name from prompt
            const agentMatch = prompt.match(/\b(orchestrator|architect|codesmith|tradestrat|research|opus-arbitrator|docu|reviewer|fixer)\b/i);
            if (!agentMatch) {
                stream.markdown('❌ Please specify which agent instructions to update (e.g., "update-instructions for codesmith")');
                return;
            }
            const agentName = agentMatch[1].toLowerCase();
            // Read current instructions
            const currentInstructions = await this.readInstructionFile(agentName);
            stream.progress('📝 Analyzing and improving instructions...');
            // Generate improvements
            const improvedInstructions = await this.improveInstructions(agentName, currentInstructions, prompt);
            stream.markdown(`## 📝 Improved Instructions for ${agentName}\n\n`);
            stream.markdown('```markdown\n' + improvedInstructions + '\n```');
            // Offer to save
            this.createActionButton('💾 Save Updated Instructions', 'ki-autoagent.saveInstructions', [agentName, improvedInstructions], stream);
        }
        catch (error) {
            stream.markdown(`❌ Instruction update failed: ${error.message}`);
        }
    }
    async handleViewInstructionsCommand(prompt, stream, token) {
        stream.progress('📖 Loading agent instructions...');
        try {
            // Parse agent name from prompt or list all
            const agentMatch = prompt.match(/\b(orchestrator|architect|codesmith|tradestrat|research|opus-arbitrator|docu|reviewer|fixer)\b/i);
            if (agentMatch) {
                const agentName = agentMatch[1].toLowerCase();
                const instructions = await this.readInstructionFile(agentName);
                stream.markdown(`## 📖 Instructions for ${agentName}\n\n`);
                stream.markdown('```markdown\n' + instructions + '\n```');
            }
            else {
                // List all available instruction files
                stream.markdown('## 📖 Available Agent Instructions\n\n');
                stream.markdown('Choose an agent to view instructions:\n');
                stream.markdown('- orchestrator\n');
                stream.markdown('- architect\n');
                stream.markdown('- codesmith\n');
                stream.markdown('- tradestrat\n');
                stream.markdown('- research\n');
                stream.markdown('- opus-arbitrator (richter)\n');
                stream.markdown('- docu\n');
                stream.markdown('- reviewer\n');
                stream.markdown('- fixer\n\n');
                stream.markdown('Use: `/view-instructions [agent-name]` to view specific instructions');
            }
        }
        catch (error) {
            stream.markdown(`❌ Failed to view instructions: ${error.message}`);
        }
    }
    // Helper Methods
    async analyzeProjectStructure(workspacePath) {
        // Analyze project files, package.json, etc.
        const projectInfo = {
            name: path.basename(workspacePath),
            path: workspacePath,
            hasPackageJson: false,
            dependencies: [],
            scripts: {},
            mainFiles: []
        };
        try {
            const packageJsonPath = path.join(workspacePath, 'package.json');
            const packageJson = JSON.parse(await fs.readFile(packageJsonPath, 'utf-8'));
            projectInfo.hasPackageJson = true;
            projectInfo.dependencies = Object.keys(packageJson.dependencies || {});
            projectInfo.scripts = packageJson.scripts || {};
        }
        catch (error) {
            // No package.json or error reading it
        }
        return projectInfo;
    }
    async analyzeApiEndpoints(workspacePath) {
        // Analyze code for API endpoints
        // This would be more sophisticated in a real implementation
        return {
            endpoints: [],
            baseUrl: '',
            authentication: 'unknown'
        };
    }
    async createReadme(projectInfo, additionalContext) {
        const prompt = `Create a comprehensive README.md for a project with the following information:

Project Name: ${projectInfo.name}
Has package.json: ${projectInfo.hasPackageJson}
Dependencies: ${projectInfo.dependencies.join(', ')}
Scripts: ${JSON.stringify(projectInfo.scripts, null, 2)}

Additional context: ${additionalContext}

Create a professional README with sections for:
- Project title and description
- Features
- Installation
- Usage
- Configuration (if applicable)
- API Reference (if applicable)
- Contributing
- License

Use proper markdown formatting with badges where appropriate.

${this.getSystemContextPrompt()}`;
        return await this.openAIService.chat([
            { role: 'system', content: 'You are DocuBot, an expert technical writer specializing in creating clear, comprehensive documentation.' },
            { role: 'user', content: prompt }
        ]);
    }
    async createApiDocumentation(apiInfo, additionalContext) {
        const prompt = `Create comprehensive API documentation based on the following:

${JSON.stringify(apiInfo, null, 2)}

Additional context: ${additionalContext}

Include:
- API overview
- Authentication
- Endpoints with request/response examples
- Error codes
- Rate limiting (if applicable)
- Examples in multiple languages

${this.getSystemContextPrompt()}`;
        return await this.openAIService.chat([
            { role: 'system', content: 'You are DocuBot, an expert in creating clear, comprehensive API documentation.' },
            { role: 'user', content: prompt }
        ]);
    }
    async createUserGuide(context) {
        const prompt = `Create a comprehensive user guide for the following:

${context}

Include:
- Getting Started
- Key Features
- Step-by-step tutorials
- Common use cases
- Troubleshooting
- FAQ

Make it user-friendly and easy to follow.

${this.getSystemContextPrompt()}`;
        return await this.openAIService.chat([
            { role: 'system', content: 'You are DocuBot, an expert in creating user-friendly documentation and guides.' },
            { role: 'user', content: prompt }
        ]);
    }
    async addDocumentationComments(code, language, context) {
        const prompt = `Add comprehensive documentation comments to this ${language} code:

${code}

Additional context: ${context}

Use the appropriate comment style for ${language} (JSDoc for JavaScript/TypeScript, docstrings for Python, etc.)
Document all functions, classes, and complex logic.

${this.getSystemContextPrompt()}`;
        return await this.openAIService.chat([
            { role: 'system', content: 'You are DocuBot, an expert in code documentation and technical writing.' },
            { role: 'user', content: prompt }
        ]);
    }
    async createChangelog(gitLog, context) {
        const prompt = `Create a CHANGELOG.md based on the following git history:

${gitLog}

Additional context: ${context}

Format using Keep a Changelog standard (https://keepachangelog.com/)
Group changes by version and category (Added, Changed, Deprecated, Removed, Fixed, Security)

${this.getSystemContextPrompt()}`;
        return await this.openAIService.chat([
            { role: 'system', content: 'You are DocuBot, an expert in creating clear, organized changelogs.' },
            { role: 'user', content: prompt }
        ]);
    }
    async createGeneralDocumentation(context) {
        const prompt = `Create comprehensive documentation for:

${context}

Make it clear, well-structured, and professional.

${this.getSystemContextPrompt()}`;
        return await this.openAIService.chat([
            { role: 'system', content: 'You are DocuBot, an expert technical writer creating clear, comprehensive documentation.' },
            { role: 'user', content: prompt }
        ]);
    }
    async getGitLog() {
        // Execute git log command
        const cp = __webpack_require__(/*! child_process */ "child_process");
        return new Promise((resolve, reject) => {
            cp.exec('git log --oneline -50', (error, stdout, stderr) => {
                if (error) {
                    reject(error);
                }
                else {
                    resolve(stdout);
                }
            });
        });
    }
    // Workflow helper methods
    async generateCodeDocumentation(request, previousResults) {
        const context = this.buildContextFromResults(previousResults);
        return this.createGeneralDocumentation(`Document the following code/feature:\n${request.prompt}\n\nContext from previous steps:\n${context}`);
    }
    async generateReadme(request, previousResults) {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            throw new Error('No workspace folder found');
        }
        const projectInfo = await this.analyzeProjectStructure(workspaceFolder.uri.fsPath);
        const context = this.buildContextFromResults(previousResults);
        return this.createReadme(projectInfo, `${request.prompt}\n\nContext:\n${context}`);
    }
    async generateApiDocs(request, previousResults) {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            throw new Error('No workspace folder found');
        }
        const apiInfo = await this.analyzeApiEndpoints(workspaceFolder.uri.fsPath);
        const context = this.buildContextFromResults(previousResults);
        return this.createApiDocumentation(apiInfo, `${request.prompt}\n\nContext:\n${context}`);
    }
    async generateGeneralDocs(request, previousResults) {
        const context = this.buildContextFromResults(previousResults);
        return this.createGeneralDocumentation(`${request.prompt}\n\nContext from previous steps:\n${context}`);
    }
    buildContextFromResults(results) {
        return results
            .filter(r => r.status === 'success')
            .map(r => `${r.metadata?.step || 'Step'}: ${r.content}`)
            .join('\n\n');
    }
    async readInstructionFile(agentName) {
        try {
            // Map agent names to instruction file names
            const fileNameMap = {
                'orchestrator': 'orchestrator-instructions',
                'architect': 'architect-instructions',
                'codesmith': 'codesmith-instructions',
                'tradestrat': 'tradestrat-instructions',
                'research': 'research-instructions',
                'opus-arbitrator': 'richter-instructions',
                'docu': 'docubot-instructions',
                'reviewer': 'reviewergpt-instructions',
                'fixer': 'fixerbot-instructions'
            };
            const fileName = fileNameMap[agentName] || `${agentName}-instructions`;
            const instructionPath = path.join(this.context.extensionPath, 'src', 'instructions', `${fileName}.md`);
            return await fs.readFile(instructionPath, 'utf-8');
        }
        catch (error) {
            throw new Error(`Failed to read instructions for ${agentName}: ${error.message}`);
        }
    }
    async writeInstructionFile(agentName, content) {
        try {
            // Map agent names to instruction file names
            const fileNameMap = {
                'orchestrator': 'orchestrator-instructions',
                'architect': 'architect-instructions',
                'codesmith': 'codesmith-instructions',
                'tradestrat': 'tradestrat-instructions',
                'research': 'research-instructions',
                'opus-arbitrator': 'richter-instructions',
                'docu': 'docubot-instructions',
                'reviewer': 'reviewergpt-instructions',
                'fixer': 'fixerbot-instructions'
            };
            const fileName = fileNameMap[agentName] || `${agentName}-instructions`;
            const instructionPath = path.join(this.context.extensionPath, 'src', 'instructions', `${fileName}.md`);
            await fs.writeFile(instructionPath, content, 'utf-8');
        }
        catch (error) {
            throw new Error(`Failed to write instructions for ${agentName}: ${error.message}`);
        }
    }
    async improveInstructions(agentName, currentInstructions, userContext) {
        const prompt = `Improve the instruction set for the ${agentName} agent.

Current instructions:
${currentInstructions}

User context and requirements:
${userContext}

Please improve these instructions by:
1. Ensuring clarity and completeness
2. Adding any missing capabilities or commands
3. Improving formatting and organization
4. Updating best practices
5. Ensuring consistency with the agent's role
6. Adding examples where helpful
7. Keeping the same markdown structure

Return the complete improved instruction set in markdown format.

${this.getSystemContextPrompt()}`;
        return await this.openAIService.chat([
            { role: 'system', content: 'You are DocuBot, an expert in creating and improving technical documentation and agent instructions.' },
            { role: 'user', content: prompt }
        ]);
    }
}
exports.DocuBotAgent = DocuBotAgent;


/***/ }),

/***/ "./src/agents/OpusArbitratorAgent.ts":
/*!*******************************************!*\
  !*** ./src/agents/OpusArbitratorAgent.ts ***!
  \*******************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {


var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.OpusArbitratorAgent = void 0;
const vscode = __importStar(__webpack_require__(/*! vscode */ "vscode"));
const ChatAgent_1 = __webpack_require__(/*! ./base/ChatAgent */ "./src/agents/base/ChatAgent.ts");
const AnthropicService_1 = __webpack_require__(/*! ../utils/AnthropicService */ "./src/utils/AnthropicService.ts");
const ClaudeCodeService_1 = __webpack_require__(/*! ../services/ClaudeCodeService */ "./src/services/ClaudeCodeService.ts");
class OpusArbitratorAgent extends ChatAgent_1.ChatAgent {
    constructor(context, dispatcher) {
        const config = {
            participantId: 'ki-autoagent.richter',
            name: 'richter',
            fullName: 'OpusArbitrator',
            description: '⚖️ Supreme Quality Judge powered by Claude Opus 4.1 - Final arbitrator for agent conflicts with superior reasoning capabilities',
            model: 'claude-4.1-opus-20250915',
            iconPath: vscode.Uri.joinPath(context.extensionUri, 'media', 'claude-icon.svg'),
            capabilities: [
                'Agent Conflict Resolution',
                'Supreme Decision Making',
                'Complex Reasoning & Analysis',
                'Multi-Agent Coordination',
                'Final Authority on Technical Disputes'
            ],
            commands: [
                { name: 'judge', description: 'Make supreme judgment on any matter', handler: 'handleJudgeCommand' },
                { name: 'evaluate', description: 'Deep technical evaluation of options', handler: 'handleEvaluateCommand' },
                { name: 'resolve', description: 'Resolve conflicts between agents', handler: 'handleResolveCommand' },
                { name: 'verdict', description: 'Final binding verdict on decisions', handler: 'handleVerdictCommand' }
            ]
        };
        super(config, context, dispatcher);
        this.anthropicService = new AnthropicService_1.AnthropicService();
        this.claudeCodeService = (0, ClaudeCodeService_1.getClaudeCodeService)();
    }
    async handleRequest(request, context, stream, token) {
        const validationResult = await this.validateServiceConfig(stream);
        if (!validationResult) {
            return;
        }
        const command = request.command;
        const prompt = request.prompt;
        this.log(`Processing ${command ? `/${command}` : 'general'} arbitration request: ${prompt.substring(0, 100)}...`);
        if (command) {
            await this.handleCommand(command, prompt, stream, token);
        }
        else {
            await this.handleGeneralArbitrationRequest(prompt, stream, token);
        }
    }
    async processWorkflowStep(step, request, previousResults) {
        const context = await this.getWorkspaceContext();
        let systemPrompt = '';
        let userPrompt = '';
        switch (step.id) {
            case 'conflict_analysis':
                systemPrompt = this.getConflictResolutionPrompt();
                userPrompt = `Analyze this agent conflict: ${request.prompt}\n\nContext:\n${context}`;
                break;
            case 'technical_evaluation':
                systemPrompt = this.getDeepEvaluationPrompt();
                userPrompt = `Evaluate technical options: ${request.prompt}\n\nPrevious Analysis:\n${this.extractPreviousContent(previousResults)}`;
                break;
            case 'final_judgment':
                systemPrompt = this.getFinalVerdictPrompt();
                userPrompt = `Deliver final judgment: ${request.prompt}\n\nContext:\n${context}`;
                break;
            default:
                systemPrompt = this.getSupremeJudgmentPrompt();
                userPrompt = `${request.prompt}\n\nContext:\n${context}`;
        }
        try {
            const claudeService = await this.getClaudeService();
            const response = await claudeService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);
            return {
                status: 'success',
                content: response,
                metadata: {
                    step: step.id,
                    agent: 'richter',
                    model: 'claude-opus-4-1-20250805'
                }
            };
        }
        catch (error) {
            throw new Error(`Failed to process ${step.id}: ${error.message}`);
        }
    }
    // Command Handlers
    async handleJudgeCommand(prompt, stream, token) {
        stream.progress('👑 OpusArbitrator applying supreme judgment...');
        const context = await this.getWorkspaceContext();
        const systemPrompt = this.getSupremeJudgmentPrompt();
        const userPrompt = `Apply supreme judgment: ${prompt}\n\nWorkspace Context:\n${context}`;
        try {
            const claudeService = await this.getClaudeService();
            const response = await claudeService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);
            stream.markdown('## 👑 SUPREME JUDGMENT\n\n');
            stream.markdown(response);
            stream.markdown('\n\n**⚖️ Judgment rendered by OpusArbitrator - Claude Opus 4.1**');
        }
        catch (error) {
            stream.markdown(`❌ **Judgment Error:** ${error.message}`);
        }
    }
    async handleResolveCommand(prompt, stream, token) {
        stream.progress('⚖️ OpusArbitrator analyzing conflict...');
        const context = await this.getWorkspaceContext();
        const systemPrompt = this.getConflictResolutionPrompt();
        const userPrompt = `Resolve this agent conflict: ${prompt}\n\nWorkspace Context:\n${context}`;
        try {
            const claudeService = await this.getClaudeService();
            const response = await claudeService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);
            stream.markdown('## ⚖️ SUPREME ARBITRATION DECISION\n\n');
            stream.markdown(response);
            stream.markdown('\n\n**🏛️ This decision is final and binding for all agents.**');
        }
        catch (error) {
            stream.markdown(`❌ **Arbitration Error:** ${error.message}`);
        }
    }
    async handleEvaluateCommand(prompt, stream, token) {
        stream.progress('🔍 OpusArbitrator performing deep evaluation...');
        const context = await this.getWorkspaceContext();
        const systemPrompt = this.getDeepEvaluationPrompt();
        const userPrompt = `Perform deep technical evaluation: ${prompt}\n\nWorkspace Context:\n${context}`;
        try {
            const claudeService = await this.getClaudeService();
            const response = await claudeService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);
            stream.markdown('## 🔍 DEEP TECHNICAL EVALUATION\n\n');
            stream.markdown(response);
            stream.markdown('\n\n**📊 Analysis conducted by OpusArbitrator with Claude Opus 4.1**');
        }
        catch (error) {
            stream.markdown(`❌ **Evaluation Error:** ${error.message}`);
        }
    }
    async handleVerdictCommand(prompt, stream, token) {
        stream.progress('⚡ OpusArbitrator delivering final verdict...');
        const context = await this.getWorkspaceContext();
        const systemPrompt = this.getFinalVerdictPrompt();
        const userPrompt = `Deliver final verdict on: ${prompt}\n\nWorkspace Context:\n${context}`;
        try {
            const claudeService = await this.getClaudeService();
            const response = await claudeService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);
            stream.markdown('## ⚡ FINAL VERDICT\n\n');
            stream.markdown(response);
            stream.markdown('\n\n**🏛️ VERDICT IS FINAL - All agents must comply**');
        }
        catch (error) {
            stream.markdown(`❌ **Verdict Error:** ${error.message}`);
        }
    }
    async handleGeneralArbitrationRequest(prompt, stream, token) {
        stream.progress('👑 OpusArbitrator applying supreme judgment...');
        const context = await this.getWorkspaceContext();
        const systemPrompt = this.getSupremeJudgmentPrompt();
        const userPrompt = `${prompt}\n\nWorkspace Context:\n${context}`;
        try {
            const claudeService = await this.getClaudeService();
            const response = await claudeService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);
            stream.markdown('## 👑 SUPREME JUDGMENT\n\n');
            stream.markdown(response);
            stream.markdown('\n\n**⚖️ Judgment rendered by OpusArbitrator - Claude Opus 4.1**');
        }
        catch (error) {
            stream.markdown(`❌ **Judgment Error:** ${error.message}`);
        }
    }
    // Service Methods
    async validateServiceConfig(stream) {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        const serviceMode = config.get('claude.serviceMode', 'claude-code');
        if (serviceMode === 'api') {
            const apiKey = config.get('anthropic.apiKey');
            if (!apiKey) {
                stream.markdown('❌ **Configuration Error**: Anthropic API key is required for Claude Opus 4.1\n\n');
                stream.markdown('Please configure your API key in VS Code Settings:\n');
                stream.markdown('1. Open Settings (Ctrl+,)\n');
                stream.markdown('2. Search for "KI AutoAgent"\n');
                stream.markdown('3. Set your Anthropic API key\n');
                return false;
            }
        }
        else if (serviceMode === 'claude-code') {
            const isClaudeCodeAvailable = await this.claudeCodeService.isAvailable();
            if (!isClaudeCodeAvailable) {
                stream.markdown(`❌ **Claude Code CLI not available for Opus 4.1**\n\n**To install:**\n\`\`\`bash\nnpm install -g @anthropic-ai/claude-code\n\`\`\`\n\nOr configure your Anthropic API key in VS Code settings.`);
                return false;
            }
        }
        return true;
    }
    async getClaudeService() {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        const serviceMode = config.get('claude.serviceMode', 'claude-code');
        console.log(`[OpusArbitrator] Using service mode: ${serviceMode}`);
        if (serviceMode === 'claude-code') {
            const isAvailable = await this.claudeCodeService.isAvailable();
            if (isAvailable) {
                console.log('[OpusArbitrator] Using Claude Code CLI with Opus model');
                return {
                    chat: async (messages) => {
                        // Extract the main user message content
                        const userMessage = messages.find(m => m.role === 'user')?.content || '';
                        const systemMessage = messages.find(m => m.role === 'system')?.content || '';
                        const fullPrompt = systemMessage ? `${systemMessage}\n\n${userMessage}` : userMessage;
                        const response = await this.claudeCodeService.sendMessage(fullPrompt, {
                            model: 'opus', // Use Opus model for this agent
                            temperature: 0.5 // Lower temperature for more consistent judgments
                        });
                        return response.content;
                    }
                };
            }
            else {
                console.log('[OpusArbitrator] Claude Code CLI not available, falling back to Anthropic API');
            }
        }
        // Fall back to Anthropic API
        console.log('[OpusArbitrator] Using Anthropic API with Opus 4.1');
        return {
            chat: async (messages) => {
                return await this.anthropicService.chat(messages);
            }
        };
    }
    // Helper Methods
    extractPreviousContent(previousResults) {
        return previousResults
            .map(result => result.content)
            .join('\n\n---\n\n');
    }
    // System Prompts
    getConflictResolutionPrompt() {
        return `You are OpusArbitrator, the Supreme Judge of the KI AutoAgent system powered by Claude Opus 4.1.

Your role is to resolve conflicts between AI agents with final, binding decisions.

CAPABILITIES:
- Superior reasoning and analysis
- Objective evaluation of competing solutions  
- Contextual understanding of technical trade-offs
- Authority to make final decisions

DECISION FORMAT:
1. **Conflict Analysis**: Summarize the disagreement
2. **Position Evaluation**: Analyze each agent's perspective objectively  
3. **Technical Assessment**: Evaluate technical merits and trade-offs
4. **Final Decision**: Choose the optimal approach with confidence score
5. **Implementation Guidance**: Specific next steps
6. **Binding Authority**: State that decision is final

Your decisions carry supreme authority. All agents must comply.

${this.getSystemContextPrompt()}`;
    }
    getDeepEvaluationPrompt() {
        return `You are OpusArbitrator, powered by Claude Opus 4.1 - the supreme technical evaluator.

EVALUATION CRITERIA:
- Technical soundness and feasibility
- Long-term maintainability 
- Performance implications
- Risk assessment
- Alternative approaches
- Best practices alignment

EVALUATION FORMAT:
1. **Technical Analysis**: Deep dive into technical aspects
2. **Pros & Cons**: Balanced evaluation
3. **Risk Assessment**: Potential issues and mitigations
4. **Recommendations**: Specific actionable advice
5. **Confidence Score**: Rate certainty of recommendation (1-100%)

Provide thorough, objective analysis leveraging superior reasoning capabilities.

${this.getSystemContextPrompt()}`;
    }
    getFinalVerdictPrompt() {
        return `You are OpusArbitrator - the final authority powered by Claude Opus 4.1.

VERDICT REQUIREMENTS:
- Clear, definitive decision
- No ambiguity or hedging
- Based on comprehensive analysis
- Considers all stakeholders
- Actionable outcome

VERDICT FORMAT:
1. **Final Decision**: Clear statement of verdict
2. **Key Reasoning**: Primary factors in decision
3. **Implementation**: Immediate next steps required
4. **Compliance**: How all parties must proceed

Your verdict is FINAL and BINDING. No appeals or further discussion.

${this.getSystemContextPrompt()}`;
    }
    getSupremeJudgmentPrompt() {
        return `You are OpusArbitrator, the Supreme Judge powered by Claude Opus 4.1.

As the highest authority in the KI AutoAgent system, you provide:
- Ultimate decision-making power
- Superior reasoning capabilities
- Objective, unbiased analysis
- Final resolution of all disputes

JUDGMENT PRINCIPLES:
- Logical, evidence-based decisions
- Consider technical merit above all
- Balance competing interests fairly
- Provide clear, actionable guidance
- Maintain system integrity

Apply your superior reasoning to deliver judgment that serves the greater good of the project.

${this.getSystemContextPrompt()}`;
    }
    getSlashCommands() {
        return [
            { command: 'judge', description: 'Make supreme judgment on any matter' },
            { command: 'evaluate', description: 'Deep technical evaluation of options' },
            { command: 'resolve', description: 'Resolve conflicts between agents' },
            { command: 'verdict', description: 'Final binding verdict on decisions' }
        ];
    }
}
exports.OpusArbitratorAgent = OpusArbitratorAgent;


/***/ }),

/***/ "./src/agents/OrchestratorAgent.ts":
/*!*****************************************!*\
  !*** ./src/agents/OrchestratorAgent.ts ***!
  \*****************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {


var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.OrchestratorAgent = void 0;
/**
 * Advanced Orchestrator Agent with Task Decomposition and Intelligent Workflow Management
 * Uses graph-based workflow execution, parallel processing, and memory-enhanced orchestration
 */
const vscode = __importStar(__webpack_require__(/*! vscode */ "vscode"));
const ChatAgent_1 = __webpack_require__(/*! ./base/ChatAgent */ "./src/agents/base/ChatAgent.ts");
const OpenAIService_1 = __webpack_require__(/*! ../utils/OpenAIService */ "./src/utils/OpenAIService.ts");
const AgentRegistry_1 = __webpack_require__(/*! ../core/AgentRegistry */ "./src/core/AgentRegistry.ts");
const WorkflowEngine_1 = __webpack_require__(/*! ../core/WorkflowEngine */ "./src/core/WorkflowEngine.ts");
const MemoryManager_1 = __webpack_require__(/*! ../core/MemoryManager */ "./src/core/MemoryManager.ts");
const SharedContextManager_1 = __webpack_require__(/*! ../core/SharedContextManager */ "./src/core/SharedContextManager.ts");
const AgentCommunicationBus_1 = __webpack_require__(/*! ../core/AgentCommunicationBus */ "./src/core/AgentCommunicationBus.ts");
const Memory_1 = __webpack_require__(/*! ../types/Memory */ "./src/types/Memory.ts");
class OrchestratorAgent extends ChatAgent_1.ChatAgent {
    constructor(context, dispatcher) {
        const config = {
            participantId: 'ki-autoagent.orchestrator',
            name: 'ki',
            fullName: 'Advanced KI AutoAgent Orchestrator',
            description: 'Intelligent task orchestration with decomposition, parallel execution, and memory',
            model: 'gpt-5-2025-09-12',
            iconPath: vscode.Uri.joinPath(context.extensionUri, 'media', 'orchestrator-icon.svg'),
            capabilities: [
                'Task Decomposition',
                'Parallel Execution',
                'Dynamic Workflow Adjustment',
                'Agent Conflict Resolution',
                'Memory-Based Learning',
                'Multi-Agent Collaboration'
            ],
            commands: [
                { name: 'task', description: 'Execute complex task with intelligent decomposition', handler: 'handleTaskCommand' },
                { name: 'agents', description: 'Show available specialized agents', handler: 'handleAgentsCommand' },
                { name: 'workflow', description: 'Create advanced multi-step workflow', handler: 'handleWorkflowCommand' },
                { name: 'decompose', description: 'Decompose complex task into subtasks', handler: 'handleDecomposeCommand' },
                { name: 'parallel', description: 'Execute tasks in parallel', handler: 'handleParallelCommand' }
            ]
        };
        super(config, context, dispatcher);
        this.activeWorkflows = new Map(); // workflowId -> description
        // Initialize advanced systems
        this.openAIService = new OpenAIService_1.OpenAIService();
        this.workflowEngine = new WorkflowEngine_1.WorkflowEngine();
        this.memoryManager = new MemoryManager_1.MemoryManager({
            maxMemories: 10000,
            similarityThreshold: 0.7,
            patternExtractionEnabled: true
        });
        this.sharedContext = (0, SharedContextManager_1.getSharedContext)();
        this.communicationBus = (0, AgentCommunicationBus_1.getCommunicationBus)();
        // Register for inter-agent communication
        this.registerCommunicationHandlers();
    }
    async handleRequest(request, context, stream, token) {
        const command = request.command;
        const prompt = request.prompt;
        // Immediate feedback with intelligence indicator
        stream.progress('🧠 Advanced Orchestrator analyzing complexity and decomposing task...');
        this.log(`Advanced Orchestrator processing: ${prompt.substring(0, 100)}...`);
        // Build context with memory
        const enhancedRequest = await this.buildContextWithMemory({
            prompt,
            context: { chatHistory: context.history }
        });
        if (command) {
            await this.handleCommand(command, prompt, stream, token);
        }
        else {
            // Analyze task complexity
            const complexity = await this.analyzeTaskComplexity(prompt);
            if (complexity === 'simple') {
                await this.handleSimpleTask(prompt, stream, token);
            }
            else if (complexity === 'moderate') {
                await this.handleModerateTask(prompt, stream, token);
            }
            else {
                await this.handleComplexTask(prompt, stream, token);
            }
        }
    }
    /**
     * Analyze task complexity to determine orchestration strategy
     */
    async analyzeTaskComplexity(prompt) {
        // Search memory for similar tasks
        const similarTasks = await this.memoryManager.search(prompt, {
            k: 5,
            type: Memory_1.MemoryType.EPISODIC
        });
        // If we have handled similar tasks, use learned complexity
        if (similarTasks.length > 0) {
            const complexities = similarTasks
                .map(t => t.entry.content.complexity)
                .filter(Boolean);
            if (complexities.length > 0) {
                // Return most common complexity
                const counts = complexities.reduce((acc, c) => {
                    acc[c] = (acc[c] || 0) + 1;
                    return acc;
                }, {});
                return Object.entries(counts)
                    .sort(([, a], [, b]) => b - a)[0][0];
            }
        }
        // Analyze prompt for complexity indicators
        const complexityIndicators = {
            complex: [
                /build.*system/i,
                /implement.*architecture/i,
                /create.*application/i,
                /develop.*platform/i,
                /design.*and.*implement/i,
                /multiple.*components/i,
                /full.*stack/i,
                /end.*to.*end/i,
                /microservices/i,
                /distributed/i
            ],
            moderate: [
                /create.*feature/i,
                /implement.*api/i,
                /add.*functionality/i,
                /refactor/i,
                /optimize/i,
                /debug.*and.*fix/i,
                /integrate/i,
                /migrate/i
            ],
            simple: [
                /fix.*bug/i,
                /update.*documentation/i,
                /write.*function/i,
                /create.*file/i,
                /explain/i,
                /what.*is/i,
                /how.*to/i,
                /show.*me/i,
                /list/i
            ]
        };
        // Check indicators
        for (const [level, patterns] of Object.entries(complexityIndicators)) {
            if (patterns.some(p => p.test(prompt))) {
                return level;
            }
        }
        // Default to moderate
        return 'moderate';
    }
    /**
     * Handle simple tasks with direct routing
     */
    async handleSimpleTask(prompt, stream, token) {
        stream.markdown(`## ⚡ Simple Task Execution\n\n`);
        // Get best agent for the task
        const registry = AgentRegistry_1.AgentRegistry.getInstance();
        const agent = registry.suggestAgentForTask(prompt);
        if (agent && agent !== 'orchestrator') {
            stream.markdown(`**Routing to @${agent}**\n\n`);
            // Create simple workflow
            const workflow = this.workflowEngine.createWorkflow(`Simple: ${prompt}`);
            const node = {
                id: 'execute',
                type: 'task',
                agentId: agent,
                task: prompt
            };
            this.workflowEngine.addNode(workflow.id, node);
            // Execute
            const results = await this.executeWorkflowWithProgress(workflow.id, prompt, stream);
            // Display results
            this.displayResults(results, stream);
            // Store in memory
            await this.storeTaskMemory(prompt, 'simple', workflow.id, results);
        }
        else {
            // Handle directly
            await this.handleDirectResponse(prompt, stream);
        }
    }
    /**
     * Handle moderate complexity tasks with sequential workflow
     */
    async handleModerateTask(prompt, stream, token) {
        stream.markdown(`## 🔄 Moderate Task Workflow\n\n`);
        // Decompose into subtasks
        const decomposition = await this.decomposeTask(prompt);
        stream.markdown(`**Identified ${decomposition.subtasks.length} subtasks**\n\n`);
        // Create workflow
        const workflow = this.workflowEngine.createWorkflow(`Moderate: ${prompt}`);
        // Add nodes for each subtask
        decomposition.subtasks.forEach(subtask => {
            const node = {
                id: subtask.id,
                type: 'task',
                agentId: subtask.agent,
                task: subtask.description,
                dependencies: subtask.dependencies
            };
            this.workflowEngine.addNode(workflow.id, node);
        });
        // Add edges based on dependencies
        decomposition.dependencies.forEach(dep => {
            this.workflowEngine.addEdge(workflow.id, {
                from: dep.from,
                to: dep.to
            });
        });
        // Display execution plan
        const plan = this.workflowEngine.createExecutionPlan(workflow.id);
        this.displayExecutionPlan(plan, stream);
        // Execute workflow
        const results = await this.executeWorkflowWithProgress(workflow.id, prompt, stream);
        // Display results
        this.displayResults(results, stream);
        // Store in memory
        await this.storeTaskMemory(prompt, 'moderate', workflow.id, results);
    }
    /**
     * Handle complex tasks with parallel execution and collaboration
     */
    async handleComplexTask(prompt, stream, token) {
        stream.markdown(`## 🚀 Complex Task Orchestration\n\n`);
        stream.markdown(`**Initiating advanced multi-agent collaboration...**\n\n`);
        // Decompose into subtasks
        const decomposition = await this.decomposeTask(prompt);
        stream.markdown(`### 📊 Task Analysis\n`);
        stream.markdown(`- **Complexity:** ${decomposition.complexity}\n`);
        stream.markdown(`- **Subtasks:** ${decomposition.subtasks.length}\n`);
        stream.markdown(`- **Required Agents:** ${decomposition.requiredAgents.join(', ')}\n`);
        stream.markdown(`- **Parallelizable:** ${decomposition.parallelizable ? 'Yes' : 'No'}\n`);
        stream.markdown(`- **Estimated Duration:** ${decomposition.estimatedDuration}ms\n\n`);
        // Start collaboration session
        const session = await this.communicationBus.startCollaboration({ task: prompt, decomposition }, decomposition.requiredAgents, 'orchestrator');
        stream.markdown(`**Collaboration Session Started:** ${session.id}\n\n`);
        // Create advanced workflow with parallel execution
        const workflow = this.workflowEngine.createWorkflow(`Complex: ${prompt}`);
        // Group parallelizable tasks
        const parallelGroups = this.groupParallelTasks(decomposition);
        // Create workflow nodes
        parallelGroups.forEach((group, index) => {
            if (group.length > 1) {
                // Create parallel node
                const parallelNode = {
                    id: `parallel_${index}`,
                    type: 'parallel',
                    children: group.map(t => t.id)
                };
                this.workflowEngine.addNode(workflow.id, parallelNode);
                // Add task nodes
                group.forEach(subtask => {
                    const taskNode = {
                        id: subtask.id,
                        type: 'task',
                        agentId: subtask.agent,
                        task: subtask.description
                    };
                    this.workflowEngine.addNode(workflow.id, taskNode);
                });
            }
            else {
                // Single task node
                const subtask = group[0];
                const taskNode = {
                    id: subtask.id,
                    type: 'task',
                    agentId: subtask.agent,
                    task: subtask.description,
                    dependencies: subtask.dependencies
                };
                this.workflowEngine.addNode(workflow.id, taskNode);
            }
        });
        // Add edges for dependencies
        decomposition.dependencies.forEach(dep => {
            this.workflowEngine.addEdge(workflow.id, {
                from: dep.from,
                to: dep.to,
                condition: dep.condition ? this.createCondition(dep.condition) : undefined
            });
        });
        // Display execution plan
        const plan = this.workflowEngine.createExecutionPlan(workflow.id);
        this.displayAdvancedExecutionPlan(plan, stream);
        // Execute with checkpointing
        stream.markdown(`### ⚡ Execution Progress\n\n`);
        const results = await this.executeComplexWorkflow(workflow.id, prompt, session.id, stream);
        // Complete collaboration
        this.communicationBus.completeCollaboration(session.id, results);
        // Display comprehensive results
        this.displayComplexResults(results, stream);
        // Store in memory with patterns
        await this.storeComplexTaskMemory(prompt, decomposition, workflow.id, results);
        // Extract and store patterns
        await this.extractAndStorePatterns(decomposition, results);
    }
    /**
     * Decompose task into subtasks using AI
     */
    async decomposeTask(prompt) {
        // Check memory for similar decompositions
        const similarTasks = await this.memoryManager.search(prompt, {
            k: 3,
            type: Memory_1.MemoryType.PROCEDURAL
        });
        if (similarTasks.length > 0 && similarTasks[0].similarity > 0.85) {
            // Reuse previous decomposition
            return similarTasks[0].entry.content.decomposition;
        }
        // Use AI to decompose
        const systemPrompt = `You are an expert task decomposer. Break down complex tasks into subtasks.

${this.getSystemContextPrompt()}

Analyze the task and provide a JSON response with:
{
  "mainGoal": "primary objective",
  "complexity": "simple|moderate|complex",
  "subtasks": [
    {
      "id": "unique_id",
      "description": "what to do",
      "agent": "best agent for this",
      "priority": 1-5,
      "dependencies": ["other_task_ids"],
      "expectedOutput": "what this produces",
      "estimatedDuration": milliseconds
    }
  ],
  "dependencies": [
    {
      "from": "task_id",
      "to": "task_id",
      "type": "sequential|parallel|conditional",
      "condition": "optional condition"
    }
  ],
  "estimatedDuration": total_milliseconds,
  "requiredAgents": ["agent1", "agent2"],
  "parallelizable": boolean
}

Available agents: architect, codesmith, docu, reviewer, fixer, tradestrat, opus-arbitrator, research`;
        const response = await this.openAIService.chat([
            { role: 'system', content: systemPrompt },
            { role: 'user', content: `Decompose this task: ${prompt}` }
        ]);
        try {
            const decomposition = JSON.parse(response);
            // Store in memory for future use
            await this.memoryManager.store('orchestrator', { prompt, decomposition }, Memory_1.MemoryType.PROCEDURAL, { importance: 0.8 });
            return decomposition;
        }
        catch (error) {
            // Fallback to simple decomposition
            return this.createSimpleDecomposition(prompt);
        }
    }
    /**
     * Create simple decomposition as fallback
     */
    createSimpleDecomposition(prompt) {
        const registry = AgentRegistry_1.AgentRegistry.getInstance();
        const agent = registry.suggestAgentForTask(prompt) || 'codesmith';
        return {
            mainGoal: prompt,
            complexity: 'simple',
            subtasks: [{
                    id: 'task_1',
                    description: prompt,
                    agent,
                    priority: 1,
                    dependencies: [],
                    expectedOutput: 'Task result',
                    estimatedDuration: 5000
                }],
            dependencies: [],
            estimatedDuration: 5000,
            requiredAgents: [agent],
            parallelizable: false
        };
    }
    /**
     * Group tasks that can be executed in parallel
     */
    groupParallelTasks(decomposition) {
        const groups = [];
        const processed = new Set();
        // Sort by priority
        const sorted = [...decomposition.subtasks].sort((a, b) => a.priority - b.priority);
        sorted.forEach(task => {
            if (processed.has(task.id))
                return;
            // Find tasks that can run in parallel with this one
            const parallelGroup = [task];
            processed.add(task.id);
            sorted.forEach(other => {
                if (processed.has(other.id))
                    return;
                // Check if they can run in parallel (no dependencies between them)
                const hasDirectDependency = decomposition.dependencies.some(dep => (dep.from === task.id && dep.to === other.id) ||
                    (dep.from === other.id && dep.to === task.id));
                if (!hasDirectDependency && other.dependencies.length === task.dependencies.length) {
                    parallelGroup.push(other);
                    processed.add(other.id);
                }
            });
            groups.push(parallelGroup);
        });
        return groups;
    }
    /**
     * Execute workflow with progress updates
     */
    async executeWorkflowWithProgress(workflowId, description, stream) {
        this.activeWorkflows.set(workflowId, description);
        // Subscribe to workflow events
        const workflow = this.workflowEngine['workflows'].get(workflowId);
        if (workflow) {
            this.workflowEngine['eventBus'].on('node-started', (event) => {
                if (event.workflowId === workflowId) {
                    stream.progress(`⚡ Executing: ${event.node.id}`);
                }
            });
            this.workflowEngine['eventBus'].on('node-completed', (event) => {
                if (event.workflowId === workflowId) {
                    stream.markdown(`✅ Completed: ${event.node.id}\n`);
                }
            });
        }
        // Execute workflow
        const context = new Map([
            ['prompt', description],
            ['sharedContext', this.sharedContext.getContext()]
        ]);
        const results = await this.workflowEngine.execute(workflowId, context);
        this.activeWorkflows.delete(workflowId);
        return results;
    }
    /**
     * Execute complex workflow with checkpointing and dynamic adjustment
     */
    async executeComplexWorkflow(workflowId, description, sessionId, stream) {
        const results = new Map();
        const workflow = this.workflowEngine['workflows'].get(workflowId);
        if (!workflow)
            return results;
        // Set up event handlers for real-time updates
        this.workflowEngine['eventBus'].on('stage-started', (event) => {
            if (event.workflowId === workflowId) {
                stream.markdown(`\n**Stage Started:** ${event.stage.stageId}\n`);
                // Update collaboration context
                this.communicationBus.updateCollaborationContext(sessionId, 'orchestrator', 'current_stage', event.stage);
            }
        });
        this.workflowEngine['eventBus'].on('node-completed', (event) => {
            if (event.workflowId === workflowId) {
                // Check if adjustment needed based on result
                if (event.result.status === 'failure') {
                    // Request help from other agents
                    this.requestAgentHelp(event.node, event.result.error);
                }
                // Update shared context
                this.sharedContext.updateContext('orchestrator', `result_${event.node.id}`, event.result);
            }
        });
        // Create checkpoints at critical stages
        this.workflowEngine['eventBus'].on('stage-completed', (event) => {
            if (event.workflowId === workflowId) {
                this.workflowEngine.createCheckpoint(workflowId, event.stage.stageId);
                stream.markdown(`💾 Checkpoint created at ${event.stage.stageId}\n`);
            }
        });
        // Execute with context
        const context = new Map([
            ['prompt', description],
            ['sessionId', sessionId],
            ['sharedContext', this.sharedContext.getContext()]
        ]);
        try {
            return await this.workflowEngine.execute(workflowId, context);
        }
        catch (error) {
            stream.markdown(`\n⚠️ **Workflow error, attempting recovery...**\n`);
            // Try to recover from last checkpoint
            const checkpoints = workflow.checkpoints;
            if (checkpoints.length > 0) {
                const lastCheckpoint = checkpoints[checkpoints.length - 1];
                this.workflowEngine.restoreFromCheckpoint(workflowId, lastCheckpoint.id);
                stream.markdown(`♻️ Restored from checkpoint: ${lastCheckpoint.nodeId}\n`);
                // Retry execution
                return await this.workflowEngine.execute(workflowId, context);
            }
            throw error;
        }
    }
    /**
     * Request help from other agents when stuck
     */
    async requestAgentHelp(node, error) {
        const helpResponse = await this.communicationBus.requestHelp('orchestrator', {
            node,
            error,
            context: this.sharedContext.getContext()
        });
        if (helpResponse && helpResponse.length > 0) {
            // Apply first suggested solution
            const solution = helpResponse[0];
            // Adjust workflow based on help
            this.workflowEngine.adjustWorkflow(node.id, {
                type: 'modify-node',
                nodeId: node.id,
                modifications: {
                    task: solution.suggestion || node.task
                }
            });
        }
    }
    /**
     * Display execution plan
     */
    displayExecutionPlan(plan, stream) {
        stream.markdown(`### 📋 Execution Plan\n\n`);
        stream.markdown(`**Stages:** ${plan.stages.length}\n`);
        stream.markdown(`**Parallelism:** ${plan.parallelism}x\n`);
        stream.markdown(`**Estimated Duration:** ${plan.estimatedDuration}ms\n\n`);
        plan.stages.forEach((stage, index) => {
            stream.markdown(`**Stage ${index + 1}:** ${stage.parallel ? '⚡ Parallel' : '📝 Sequential'}\n`);
            stage.nodes.forEach(node => {
                stream.markdown(`  - ${node.agentId || 'system'}: ${node.id}\n`);
            });
        });
        stream.markdown(`\n**Critical Path:** ${plan.criticalPath.join(' → ')}\n\n`);
    }
    /**
     * Display advanced execution plan
     */
    displayAdvancedExecutionPlan(plan, stream) {
        stream.markdown(`### 🚀 Advanced Execution Strategy\n\n`);
        // Create visual representation
        stream.markdown(`\`\`\`mermaid\ngraph TB\n`);
        plan.stages.forEach((stage, index) => {
            if (stage.parallel) {
                stream.markdown(`  subgraph "Stage ${index + 1} - Parallel"\n`);
                stage.nodes.forEach(node => {
                    stream.markdown(`    ${node.id}["${node.agentId}: ${node.id}"]\n`);
                });
                stream.markdown(`  end\n`);
            }
            else {
                stage.nodes.forEach(node => {
                    stream.markdown(`  ${node.id}["${node.agentId}: ${node.id}"]\n`);
                });
            }
        });
        // Add dependencies as edges
        plan.stages.forEach((stage, index) => {
            if (index > 0) {
                const prevStage = plan.stages[index - 1];
                prevStage.nodes.forEach(prevNode => {
                    stage.nodes.forEach(currNode => {
                        if (currNode.dependencies?.includes(prevNode.id)) {
                            stream.markdown(`  ${prevNode.id} --> ${currNode.id}\n`);
                        }
                    });
                });
            }
        });
        stream.markdown(`\`\`\`\n\n`);
        // Performance metrics
        stream.markdown(`**Performance Optimization:**\n`);
        stream.markdown(`- Parallel Execution Speed-up: ${plan.parallelism}x\n`);
        stream.markdown(`- Critical Path Length: ${plan.criticalPath.length} steps\n`);
        stream.markdown(`- Total Estimated Time: ${(plan.estimatedDuration / 1000).toFixed(1)}s\n\n`);
    }
    /**
     * Display simple results
     */
    displayResults(results, stream) {
        stream.markdown(`\n### 📊 Results\n\n`);
        results.forEach((result, nodeId) => {
            if (result.status === 'success') {
                stream.markdown(`**✅ ${nodeId}:**\n${result.output?.result || result.output || 'Completed'}\n\n`);
            }
            else if (result.status === 'failure') {
                stream.markdown(`**❌ ${nodeId}:** ${result.error}\n\n`);
            }
        });
    }
    /**
     * Display complex results with insights
     */
    displayComplexResults(results, stream) {
        stream.markdown(`\n### 🎯 Comprehensive Results\n\n`);
        // Group results by status
        const successes = [];
        const failures = [];
        results.forEach((result, nodeId) => {
            if (result.status === 'success') {
                successes.push({ nodeId, ...result });
            }
            else {
                failures.push({ nodeId, ...result });
            }
        });
        // Display successes
        if (successes.length > 0) {
            stream.markdown(`#### ✅ Successful Tasks (${successes.length})\n\n`);
            successes.forEach(result => {
                stream.markdown(`**${result.nodeId}:**\n`);
                stream.markdown(`${result.output?.result || result.output || 'Completed'}\n\n`);
            });
        }
        // Display failures
        if (failures.length > 0) {
            stream.markdown(`#### ⚠️ Failed Tasks (${failures.length})\n\n`);
            failures.forEach(result => {
                stream.markdown(`**${result.nodeId}:** ${result.error}\n`);
                stream.markdown(`*Suggestion:* Try using @fixer to resolve this issue\n\n`);
            });
        }
        // Display insights
        const insights = this.generateInsights(results);
        if (insights.length > 0) {
            stream.markdown(`#### 💡 Insights & Recommendations\n\n`);
            insights.forEach(insight => {
                stream.markdown(`- ${insight}\n`);
            });
        }
        // Display collaboration metrics
        const collaborationStats = this.communicationBus.getStats();
        stream.markdown(`\n#### 📈 Collaboration Metrics\n\n`);
        stream.markdown(`- Total Messages Exchanged: ${collaborationStats.totalMessages}\n`);
        stream.markdown(`- Average Response Time: ${collaborationStats.averageResponseTime.toFixed(0)}ms\n`);
        stream.markdown(`- Active Sessions: ${collaborationStats.activeSessions}\n`);
    }
    /**
     * Generate insights from results
     */
    generateInsights(results) {
        const insights = [];
        // Calculate success rate
        let successes = 0;
        let total = 0;
        results.forEach(result => {
            total++;
            if (result.status === 'success')
                successes++;
        });
        const successRate = (successes / total) * 100;
        if (successRate === 100) {
            insights.push('🎉 Perfect execution! All tasks completed successfully.');
        }
        else if (successRate >= 80) {
            insights.push(`✅ Good performance with ${successRate.toFixed(0)}% success rate.`);
        }
        else {
            insights.push(`⚠️ Room for improvement with ${successRate.toFixed(0)}% success rate.`);
        }
        // Analyze patterns
        const agents = new Map();
        results.forEach((result, nodeId) => {
            const agent = result.agent || 'unknown';
            agents.set(agent, (agents.get(agent) || 0) + 1);
        });
        const mostUsedAgent = Array.from(agents.entries())
            .sort(([, a], [, b]) => b - a)[0];
        if (mostUsedAgent) {
            insights.push(`📊 Most active agent: @${mostUsedAgent[0]} (${mostUsedAgent[1]} tasks)`);
        }
        // Check for bottlenecks
        const longRunning = Array.from(results.entries())
            .filter(([, r]) => r.duration > 10000)
            .map(([id]) => id);
        if (longRunning.length > 0) {
            insights.push(`⏱️ Potential bottlenecks detected in: ${longRunning.join(', ')}`);
        }
        return insights;
    }
    /**
     * Store task memory for learning
     */
    async storeTaskMemory(prompt, complexity, workflowId, results) {
        const taskMemory = {
            taskId: workflowId,
            description: prompt,
            decomposition: [],
            outcome: {
                status: this.determineOverallStatus(results),
                quality: this.calculateQuality(results),
                improvements: this.suggestImprovements(results)
            },
            duration: this.calculateTotalDuration(results),
            agentsInvolved: this.extractAgents(results),
            lessonsLearned: this.extractLessons(results)
        };
        await this.memoryManager.store('orchestrator', { prompt, complexity, taskMemory }, Memory_1.MemoryType.EPISODIC, { importance: 0.7 });
    }
    /**
     * Store complex task memory with patterns
     */
    async storeComplexTaskMemory(prompt, decomposition, workflowId, results) {
        const taskMemory = {
            taskId: workflowId,
            description: prompt,
            decomposition: decomposition.subtasks.map(st => ({
                stepId: st.id,
                description: st.description,
                assignedAgent: st.agent,
                status: results.has(st.id) && results.get(st.id).status === 'success'
                    ? 'completed'
                    : 'failed',
                output: results.get(st.id),
                dependencies: st.dependencies
            })),
            outcome: {
                status: this.determineOverallStatus(results),
                quality: this.calculateQuality(results),
                improvements: this.suggestImprovements(results)
            },
            duration: this.calculateTotalDuration(results),
            agentsInvolved: decomposition.requiredAgents,
            lessonsLearned: this.extractLessons(results)
        };
        await this.memoryManager.store('orchestrator', { prompt, decomposition, taskMemory }, Memory_1.MemoryType.EPISODIC, { importance: 0.9 });
    }
    /**
     * Extract and store patterns from successful execution
     */
    async extractAndStorePatterns(decomposition, results) {
        // Look for successful patterns
        const successfulSubtasks = decomposition.subtasks.filter(st => results.has(st.id) && results.get(st.id).status === 'success');
        if (successfulSubtasks.length > 0) {
            // Store as procedural memory
            await this.memoryManager.store('orchestrator', {
                pattern: 'successful_decomposition',
                mainGoal: decomposition.mainGoal,
                successfulApproach: successfulSubtasks.map(st => ({
                    agent: st.agent,
                    task: st.description,
                    priority: st.priority
                }))
            }, Memory_1.MemoryType.PROCEDURAL, { importance: 0.85 });
        }
        // Identify agent collaboration patterns
        const collaborations = new Map();
        decomposition.dependencies.forEach(dep => {
            const fromAgent = decomposition.subtasks.find(st => st.id === dep.from)?.agent;
            const toAgent = decomposition.subtasks.find(st => st.id === dep.to)?.agent;
            if (fromAgent && toAgent) {
                if (!collaborations.has(fromAgent)) {
                    collaborations.set(fromAgent, []);
                }
                collaborations.get(fromAgent).push(toAgent);
            }
        });
        if (collaborations.size > 0) {
            await this.memoryManager.store('orchestrator', {
                pattern: 'agent_collaboration',
                collaborations: Object.fromEntries(collaborations)
            }, Memory_1.MemoryType.SEMANTIC, { importance: 0.75 });
        }
    }
    // Utility methods for result analysis
    determineOverallStatus(results) {
        let successes = 0;
        let total = 0;
        results.forEach(result => {
            total++;
            if (result.status === 'success')
                successes++;
        });
        const rate = successes / total;
        if (rate === 1)
            return 'success';
        if (rate >= 0.5)
            return 'partial';
        return 'failure';
    }
    calculateQuality(results) {
        let totalQuality = 0;
        let count = 0;
        results.forEach(result => {
            count++;
            totalQuality += result.status === 'success' ? 1 : 0;
        });
        return count > 0 ? totalQuality / count : 0;
    }
    suggestImprovements(results) {
        const improvements = [];
        results.forEach((result, nodeId) => {
            if (result.status === 'failure') {
                improvements.push(`Improve error handling for ${nodeId}`);
            }
            if (result.duration > 15000) {
                improvements.push(`Optimize performance of ${nodeId}`);
            }
        });
        return improvements;
    }
    calculateTotalDuration(results) {
        let total = 0;
        results.forEach(result => {
            total += result.duration || 0;
        });
        return total;
    }
    extractAgents(results) {
        const agents = new Set();
        results.forEach(result => {
            if (result.agent) {
                agents.add(result.agent);
            }
        });
        return Array.from(agents);
    }
    extractLessons(results) {
        const lessons = [];
        // Analyze failures
        results.forEach((result, nodeId) => {
            if (result.status === 'failure') {
                lessons.push(`Task ${nodeId} failed: ${result.error}`);
            }
        });
        // Analyze successes
        const successCount = Array.from(results.values())
            .filter(r => r.status === 'success').length;
        if (successCount === results.size) {
            lessons.push('All tasks completed successfully - workflow is reliable');
        }
        return lessons;
    }
    createCondition(conditionStr) {
        return (context) => {
            // Simple condition evaluation
            // In production, use proper expression parser
            return true;
        };
    }
    /**
     * Handle direct response for simple queries
     */
    async handleDirectResponse(prompt, stream) {
        const systemPrompt = `You are an intelligent orchestrator. Answer directly and concisely.
${this.getSystemContextPrompt()}`;
        const response = await this.openAIService.chat([
            { role: 'system', content: systemPrompt },
            { role: 'user', content: prompt }
        ]);
        stream.markdown(response);
    }
    /**
     * Register communication handlers
     */
    registerCommunicationHandlers() {
        this.communicationBus.register({
            agentId: 'orchestrator',
            messageTypes: [
                AgentCommunicationBus_1.MessageType.CONFLICT,
                AgentCommunicationBus_1.MessageType.STATUS_UPDATE,
                AgentCommunicationBus_1.MessageType.ERROR
            ],
            handler: async (message) => {
                return await this.handleAgentMessage(message);
            }
        });
    }
    /**
     * Handle messages from other agents
     */
    async handleAgentMessage(message) {
        switch (message.type) {
            case AgentCommunicationBus_1.MessageType.CONFLICT:
                // Trigger OpusArbitrator for conflict resolution
                return await this.resolveConflict(message.content);
            case AgentCommunicationBus_1.MessageType.STATUS_UPDATE:
                // Update workflow status
                this.updateWorkflowStatus(message.content);
                return { acknowledged: true };
            case AgentCommunicationBus_1.MessageType.ERROR:
                // Handle agent errors
                return await this.handleAgentError(message.content);
            default:
                return { acknowledged: true };
        }
    }
    /**
     * Resolve conflicts between agents
     */
    async resolveConflict(conflict) {
        // Route to OpusArbitrator
        await this.communicationBus.send({
            from: 'orchestrator',
            to: 'OpusArbitrator',
            type: AgentCommunicationBus_1.MessageType.CONFLICT,
            content: conflict,
            metadata: {
                priority: 'critical',
                requiresResponse: true
            }
        });
        return { routing: 'OpusArbitrator' };
    }
    /**
     * Update workflow status based on agent updates
     */
    updateWorkflowStatus(update) {
        // Update shared context
        this.sharedContext.updateContext('orchestrator', `workflow_status_${update.workflowId}`, update);
    }
    /**
     * Handle errors from agents
     */
    async handleAgentError(error) {
        // Check if we can recover
        const recovery = await this.attemptRecovery(error);
        if (recovery) {
            return { recovery: true, action: recovery };
        }
        // Escalate to user
        return { recovery: false, escalate: true };
    }
    /**
     * Attempt to recover from agent errors
     */
    async attemptRecovery(error) {
        // Search memory for similar errors
        const similarErrors = await this.memoryManager.search(error, {
            k: 3,
            type: Memory_1.MemoryType.EPISODIC
        });
        if (similarErrors.length > 0) {
            // Found similar error with solution
            const solution = similarErrors[0].entry.content.solution;
            if (solution) {
                return solution;
            }
        }
        // Try alternative agent
        const registry = AgentRegistry_1.AgentRegistry.getInstance();
        const alternativeAgent = registry.suggestAgentForTask(error.task);
        if (alternativeAgent && alternativeAgent !== error.agent) {
            return {
                type: 'retry',
                agent: alternativeAgent
            };
        }
        return null;
    }
    /**
     * Build context with memory
     */
    async buildContextWithMemory(request) {
        // Search for relevant memories
        const memories = await this.memoryManager.search(request.prompt, {
            k: 10,
            type: Memory_1.MemoryType.EPISODIC
        });
        // Get shared context
        const sharedContext = this.sharedContext.getContext();
        return {
            ...request,
            memories: memories.map(m => m.entry.content),
            sharedContext,
            activeAgents: this.sharedContext.getActiveAgents()
        };
    }
    // Command handlers remain similar but use new orchestration methods
    // ... (rest of the command handlers can be kept or adapted as needed)
    // Required by ChatAgent abstract class
    async processWorkflowStep(step, request, previousResults) {
        // Use AI to intelligently decide how to handle the request
        const classificationPrompt = `You are the advanced orchestrator of a multi-agent AI system.

${this.getSystemAgentContext()}

Classify this request and decide how to handle it:
Request: "${request.prompt}"

Respond with a JSON object:
{
  "requestType": "query" | "simple_task" | "complex_task",
  "shouldAnswer": true/false (should orchestrator answer directly?),
  "reasoning": "brief explanation",
  "suggestedAgent": "agent_name or null if orchestrator handles it"
}

Rules:
- "query": Information requests, questions about the system, agent capabilities
- "simple_task": Single-step implementation, bug fix, or straightforward coding
- "complex_task": Multi-step projects requiring multiple agents
- Set shouldAnswer=true for queries about agents, system capabilities, or general questions
- Set shouldAnswer=false for implementation tasks that need specialist agents`;
        try {
            // Get AI classification
            const classificationResponse = await this.openAIService.chat([
                { role: 'system', content: classificationPrompt },
                { role: 'user', content: request.prompt }
            ]);
            let classification;
            try {
                classification = JSON.parse(classificationResponse);
            }
            catch {
                // Fallback if JSON parsing fails
                classification = {
                    requestType: 'query',
                    shouldAnswer: true,
                    reasoning: 'Failed to parse, treating as query'
                };
            }
            // Handle based on classification
            if (classification.shouldAnswer) {
                // Orchestrator answers directly with full context
                const answerPrompt = `You are the Advanced KI AutoAgent Orchestrator, the central intelligence coordinating a sophisticated multi-agent AI system.

${this.getSystemAgentContext()}

Important: When asked about agents, provide comprehensive details including:
- Agent names and their @mentions
- Specific capabilities and expertise
- AI models they use
- How they collaborate
- System features like memory, parallel execution, and learning

Answer this question thoroughly and helpfully:
"${request.prompt}"

Provide a complete, informative response with specific details about our capabilities.`;
                const response = await this.openAIService.chat([
                    { role: 'system', content: answerPrompt },
                    { role: 'user', content: request.prompt }
                ]);
                return {
                    status: 'success',
                    content: response,
                    metadata: {
                        step: step.id,
                        agent: 'orchestrator',
                        type: classification.requestType,
                        reasoning: classification.reasoning
                    }
                };
            }
            // For tasks, check complexity and handle accordingly
            if (classification.requestType === 'simple_task' && classification.suggestedAgent) {
                // Route to specific agent
                const node = {
                    id: step.id,
                    type: 'task',
                    agentId: classification.suggestedAgent,
                    task: request.prompt
                };
                const workflow = this.workflowEngine.createWorkflow(`Simple: ${request.prompt}`);
                this.workflowEngine.addNode(workflow.id, node);
                const results = await this.workflowEngine.execute(workflow.id);
                const stepResult = results.get(step.id);
                // Map workflow status to TaskResult status
                let taskStatus = 'error';
                if (stepResult?.status === 'success') {
                    taskStatus = 'success';
                }
                else if (stepResult?.status === 'failure') {
                    taskStatus = 'error';
                }
                else if (stepResult?.status === 'skipped') {
                    taskStatus = 'partial_success';
                }
                return {
                    status: taskStatus,
                    content: stepResult?.output?.result || stepResult?.output || 'Task completed',
                    metadata: {
                        step: step.id,
                        agent: classification.suggestedAgent,
                        type: 'routed_task'
                    }
                };
            }
            // For complex tasks, use full decomposition
            if (classification.requestType === 'complex_task') {
                const decomposition = await this.decomposeTask(request.prompt);
                // Create and execute workflow
                const workflow = this.workflowEngine.createWorkflow(`Complex: ${request.prompt}`);
                decomposition.subtasks.forEach(subtask => {
                    const node = {
                        id: subtask.id,
                        type: 'task',
                        agentId: subtask.agent,
                        task: subtask.description,
                        dependencies: subtask.dependencies
                    };
                    this.workflowEngine.addNode(workflow.id, node);
                });
                const results = await this.workflowEngine.execute(workflow.id);
                // Compile results
                const summary = this.compileWorkflowResults(results);
                return {
                    status: 'success',
                    content: summary,
                    metadata: {
                        step: step.id,
                        agent: 'orchestrator',
                        type: 'complex_workflow',
                        subtasks: decomposition.subtasks.length
                    }
                };
            }
            // Fallback: Orchestrator handles directly
            const response = await this.openAIService.chat([
                { role: 'system', content: `You are the Orchestrator. ${this.getSystemContextPrompt()}` },
                { role: 'user', content: request.prompt }
            ]);
            return {
                status: 'success',
                content: response,
                metadata: {
                    step: step.id,
                    agent: 'orchestrator',
                    type: 'direct_response'
                }
            };
        }
        catch (error) {
            return {
                status: 'error',
                content: `Error processing request: ${error.message}`,
                metadata: {
                    step: step.id,
                    agent: 'orchestrator',
                    error: error.message
                }
            };
        }
    }
    /**
     * Compile workflow results into a coherent summary
     */
    compileWorkflowResults(results) {
        const sections = [];
        sections.push('## Workflow Execution Complete\n');
        results.forEach((result, nodeId) => {
            if (result.status === 'success') {
                sections.push(`### ✅ ${nodeId}`);
                sections.push(result.output?.result || result.output || 'Completed');
                sections.push('');
            }
        });
        const failures = Array.from(results.entries())
            .filter(([, r]) => r.status !== 'success');
        if (failures.length > 0) {
            sections.push('### ⚠️ Issues Encountered');
            failures.forEach(([nodeId, result]) => {
                sections.push(`- **${nodeId}**: ${result.error || 'Failed'}`);
            });
        }
        return sections.join('\n');
    }
    /**
     * Dynamically generate system context about agents and capabilities
     */
    getSystemAgentContext() {
        const registry = AgentRegistry_1.AgentRegistry.getInstance();
        const agents = registry.getRegisteredAgents();
        // Build dynamic context about available agents
        const agentDescriptions = agents.map(agent => {
            return `- **${agent.id}** (${agent.name}): ${agent.specialization}. Can handle: ${agent.canHandle.join(', ')}`;
        }).join('\n');
        return `You are part of an advanced multi-agent AI system with the following capabilities:

## Available Specialist Agents:
${agentDescriptions}

## System Features:
- **Memory System**: 10k capacity with semantic search and pattern recognition
- **Parallel Execution**: Can run multiple tasks simultaneously for 5x speedup
- **Inter-Agent Collaboration**: Agents share knowledge and help each other
- **Learning**: System improves from past executions with 85% similarity threshold
- **Conflict Resolution**: OpusArbitrator resolves disagreements with superior reasoning

## Your Role as Orchestrator:
You coordinate these agents, decompose complex tasks, and ensure efficient execution.
For simple queries, you can answer directly. For complex tasks, orchestrate the appropriate agents.`;
    }
}
exports.OrchestratorAgent = OrchestratorAgent;


/***/ }),

/***/ "./src/agents/ResearchAgent.ts":
/*!*************************************!*\
  !*** ./src/agents/ResearchAgent.ts ***!
  \*************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {


var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.ResearchAgent = void 0;
/**
 * ResearchBot - Research & Information Expert
 * Uses web search for real-time information gathering and analysis
 */
const vscode = __importStar(__webpack_require__(/*! vscode */ "vscode"));
const ChatAgent_1 = __webpack_require__(/*! ./base/ChatAgent */ "./src/agents/base/ChatAgent.ts");
const WebSearchService_1 = __webpack_require__(/*! ../utils/WebSearchService */ "./src/utils/WebSearchService.ts");
const OpenAIService_1 = __webpack_require__(/*! ../utils/OpenAIService */ "./src/utils/OpenAIService.ts");
class ResearchAgent extends ChatAgent_1.ChatAgent {
    constructor(context, dispatcher) {
        const config = {
            participantId: 'ki-autoagent.research',
            name: 'research',
            fullName: 'ResearchBot',
            description: 'Research & Information Expert with real-time web access',
            model: 'perplexity-llama-3.1-sonar-huge-128k',
            iconPath: vscode.Uri.joinPath(context.extensionUri, 'media', 'perplexity-icon.svg'),
            capabilities: [
                'Web Research',
                'Real-time Information',
                'Technical Documentation Search',
                'Market Analysis',
                'Trend Research',
                'Competitive Analysis'
            ],
            commands: [
                { name: 'search', description: 'Search web for current information', handler: 'handleSearchCommand' },
                { name: 'documentation', description: 'Find and analyze technical documentation', handler: 'handleDocumentationCommand' },
                { name: 'market', description: 'Research market trends and analysis', handler: 'handleMarketCommand' },
                { name: 'compare', description: 'Compare technologies, tools, or solutions', handler: 'handleCompareCommand' }
            ]
        };
        super(config, context, dispatcher);
        this.webSearchService = new WebSearchService_1.WebSearchService();
        this.openAIService = new OpenAIService_1.OpenAIService();
    }
    async handleRequest(request, context, stream, token) {
        // Check if web access is available
        const webAccessAvailable = await this.webSearchService.isWebAccessAvailable();
        if (!webAccessAvailable) {
            const status = this.webSearchService.getSearchEngineStatus();
            stream.markdown(`❌ **Web access not configured**\n\n`);
            stream.markdown(`**Current search engine**: ${status.engine}\n`);
            stream.markdown(`**Status**: ${status.configured ? 'Configured' : 'Not configured'}\n\n`);
            stream.markdown(`💡 **To enable web research:**\n`);
            stream.markdown(`1. Open VS Code Settings (Cmd+,)\n`);
            stream.markdown(`2. Search for "KI AutoAgent"\n`);
            stream.markdown(`3. Configure your preferred search API:\n`);
            stream.markdown(`   - **Perplexity API** (recommended)\n`);
            stream.markdown(`   - **Tavily API** (web search specialist)\n`);
            stream.markdown(`   - **SERP API** (Google search)\n`);
            return;
        }
        const command = request.command;
        const prompt = request.prompt;
        this.log(`Processing ${command ? `/${command}` : 'general'} research request: ${prompt.substring(0, 100)}...`);
        if (command) {
            await this.handleCommand(command, prompt, stream, token);
        }
        else {
            await this.handleGeneralResearchRequest(prompt, stream, token);
        }
    }
    async processWorkflowStep(step, request, previousResults) {
        try {
            let searchQuery = '';
            let analysisPrompt = '';
            switch (step.id) {
                case 'market_research':
                    searchQuery = `${request.prompt} market trends analysis 2024`;
                    analysisPrompt = 'Analyze market trends and opportunities';
                    break;
                case 'tech_research':
                    searchQuery = `${request.prompt} technical documentation best practices`;
                    analysisPrompt = 'Research technical solutions and documentation';
                    break;
                case 'competitive_analysis':
                    searchQuery = `${request.prompt} competitors alternatives comparison`;
                    analysisPrompt = 'Compare competitive solutions and alternatives';
                    break;
                default:
                    searchQuery = request.prompt;
                    analysisPrompt = 'Research and analyze the given topic';
            }
            // Perform web search
            const searchResults = await this.webSearchService.search(searchQuery);
            // Analyze results with AI
            const analysis = await this.analyzeSearchResults(searchResults, analysisPrompt);
            return {
                status: 'success',
                content: analysis,
                metadata: {
                    step: step.id,
                    agent: 'research',
                    searchQuery,
                    resultsCount: searchResults.results.length
                }
            };
        }
        catch (error) {
            throw new Error(`Failed to process research step ${step.id}: ${error.message}`);
        }
    }
    // Command Handlers
    async handleSearchCommand(prompt, stream, token) {
        stream.progress('🔍 Searching the web for current information...');
        try {
            const searchResults = await this.webSearchService.search(prompt);
            stream.markdown(`## 🔍 Web Search Results\n\n`);
            stream.markdown(`**Query**: ${searchResults.query}\n`);
            stream.markdown(`**Results Found**: ${searchResults.totalResults}\n\n`);
            // Display search results
            for (let i = 0; i < searchResults.results.length; i++) {
                const result = searchResults.results[i];
                stream.markdown(`### ${i + 1}. ${result.title}\n`);
                stream.markdown(`**URL**: [${result.url}](${result.url})\n`);
                stream.markdown(`**Summary**: ${result.snippet}\n\n`);
            }
            // Analyze and synthesize results
            stream.progress('🧠 Analyzing search results...');
            const analysis = await this.analyzeSearchResults(searchResults, 'Provide a comprehensive analysis and synthesis of the search results');
            stream.markdown(`## 📊 Analysis & Insights\n\n`);
            stream.markdown(analysis);
            // Add source references
            searchResults.results.forEach((result, index) => {
                this.createActionButton(`📖 Read Source ${index + 1}`, 'vscode.open', [vscode.Uri.parse(result.url)], stream);
            });
        }
        catch (error) {
            stream.markdown(`❌ Search failed: ${error.message}`);
        }
    }
    async handleDocumentationCommand(prompt, stream, token) {
        stream.progress('📚 Searching for technical documentation...');
        const techQuery = `${prompt} documentation tutorial guide API reference`;
        try {
            const searchResults = await this.webSearchService.search(techQuery);
            stream.markdown(`## 📚 Documentation Research\n\n`);
            stream.markdown(`**Topic**: ${prompt}\n\n`);
            // Filter for documentation sources
            const docResults = searchResults.results.filter(result => result.url.includes('docs') ||
                result.url.includes('documentation') ||
                result.url.includes('api') ||
                result.url.includes('guide') ||
                result.title.toLowerCase().includes('documentation') ||
                result.title.toLowerCase().includes('guide'));
            if (docResults.length > 0) {
                stream.markdown(`### 📖 Official Documentation Found\n\n`);
                docResults.forEach((result, index) => {
                    stream.markdown(`**${index + 1}. ${result.title}**\n`);
                    stream.markdown(`- [${result.url}](${result.url})\n`);
                    stream.markdown(`- ${result.snippet}\n\n`);
                });
            }
            // Provide comprehensive analysis
            const analysis = await this.analyzeSearchResults(searchResults, 'Provide a comprehensive guide based on the documentation found, including key concepts, usage examples, and best practices');
            stream.markdown(`## 📋 Documentation Summary\n\n`);
            stream.markdown(analysis);
        }
        catch (error) {
            stream.markdown(`❌ Documentation search failed: ${error.message}`);
        }
    }
    async handleMarketCommand(prompt, stream, token) {
        stream.progress('📈 Researching market trends...');
        const marketQuery = `${prompt} market trends 2024 analysis statistics growth`;
        try {
            const searchResults = await this.webSearchService.search(marketQuery);
            stream.markdown(`## 📈 Market Research\n\n`);
            const analysis = await this.analyzeSearchResults(searchResults, 'Provide a comprehensive market analysis including current trends, growth statistics, key players, opportunities, and challenges');
            stream.markdown(analysis);
            // Offer to create market report
            this.createActionButton('📊 Create Market Report', 'ki-autoagent.createFile', [`market_research_${Date.now()}.md`, `# Market Research: ${prompt}\n\n${analysis}`], stream);
        }
        catch (error) {
            stream.markdown(`❌ Market research failed: ${error.message}`);
        }
    }
    async handleCompareCommand(prompt, stream, token) {
        stream.progress('⚖️ Comparing solutions...');
        const compareQuery = `${prompt} comparison alternatives pros cons review`;
        try {
            const searchResults = await this.webSearchService.search(compareQuery);
            stream.markdown(`## ⚖️ Comparison Analysis\n\n`);
            const analysis = await this.analyzeSearchResults(searchResults, 'Provide a detailed comparison including pros and cons, use cases, pricing (if available), and recommendations');
            stream.markdown(analysis);
            // Offer to create comparison table
            this.createActionButton('📋 Create Comparison Table', 'ki-autoagent.createComparisonTable', [prompt, analysis], stream);
        }
        catch (error) {
            stream.markdown(`❌ Comparison research failed: ${error.message}`);
        }
    }
    async handleGeneralResearchRequest(prompt, stream, token) {
        stream.progress('🔍 Conducting research...');
        try {
            const searchResults = await this.webSearchService.search(prompt);
            // Quick summary
            stream.markdown(`## 🔍 Research Summary\n\n`);
            stream.markdown(`**Topic**: ${prompt}\n`);
            stream.markdown(`**Sources**: ${searchResults.totalResults} results found\n\n`);
            // Comprehensive analysis
            const analysis = await this.analyzeSearchResults(searchResults, 'Provide comprehensive research findings with key insights, current state, and actionable information');
            stream.markdown(analysis);
            // Show top sources
            if (searchResults.results.length > 0) {
                stream.markdown(`\n## 📚 Key Sources\n\n`);
                searchResults.results.slice(0, 3).forEach((result, index) => {
                    stream.markdown(`${index + 1}. [${result.title}](${result.url})\n`);
                });
            }
        }
        catch (error) {
            stream.markdown(`❌ Research failed: ${error.message}`);
        }
    }
    // Helper Methods
    async analyzeSearchResults(searchResults, analysisPrompt) {
        const resultsContent = searchResults.results
            .map(result => `Title: ${result.title}\nURL: ${result.url}\nContent: ${result.snippet}`)
            .join('\n\n---\n\n');
        const systemPrompt = `You are ResearchBot, an expert research analyst. Analyze web search results and provide comprehensive, accurate, and actionable insights.

Key principles:
1. Synthesize information from multiple sources
2. Highlight key findings and trends
3. Provide actionable recommendations
4. Note any conflicting information
5. Include relevant statistics and data
6. Maintain objectivity and cite sources when possible

Format your response with clear headings and bullet points for readability.

${this.getSystemContextPrompt()}`;
        const userPrompt = `${analysisPrompt}

Search Query: ${searchResults.query}

Search Results:
${resultsContent}

Please provide a comprehensive analysis based on these search results.`;
        try {
            return await this.openAIService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);
        }
        catch (error) {
            return `Error analyzing results: ${error.message}`;
        }
    }
}
exports.ResearchAgent = ResearchAgent;


/***/ }),

/***/ "./src/agents/ReviewerGPTAgent.ts":
/*!****************************************!*\
  !*** ./src/agents/ReviewerGPTAgent.ts ***!
  \****************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {


var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.ReviewerGPTAgent = void 0;
/**
 * ReviewerGPT - Code Review & Security Expert
 * Performs comprehensive code reviews focusing on quality, security, and performance
 */
const vscode = __importStar(__webpack_require__(/*! vscode */ "vscode"));
const ChatAgent_1 = __webpack_require__(/*! ./base/ChatAgent */ "./src/agents/base/ChatAgent.ts");
const OpenAIService_1 = __webpack_require__(/*! ../utils/OpenAIService */ "./src/utils/OpenAIService.ts");
const path = __importStar(__webpack_require__(/*! path */ "path"));
class ReviewerGPTAgent extends ChatAgent_1.ChatAgent {
    constructor(context, dispatcher) {
        const config = {
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
        this.openAIService = new OpenAIService_1.OpenAIService();
    }
    async handleRequest(request, context, stream, token) {
        const command = request.command;
        const prompt = request.prompt;
        this.log(`Processing ${command ? `/${command}` : 'general'} review request: ${prompt.substring(0, 100)}...`);
        if (command) {
            await this.handleCommand(command, prompt, stream, token);
        }
        else {
            await this.handleGeneralReviewRequest(prompt, stream, token);
        }
    }
    async processWorkflowStep(step, request, previousResults) {
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
        }
        catch (error) {
            throw new Error(`Failed to process review step ${step.id}: ${error.message}`);
        }
    }
    // Command Handlers
    async handleReviewCommand(prompt, stream, token) {
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
            this.createActionButton('📋 Save Review Report', 'ki-autoagent.saveFile', [`reviews/review_${Date.now()}.md`, review], stream);
        }
        catch (error) {
            stream.markdown(`❌ Review failed: ${error.message}`);
        }
    }
    async handleBugsCommand(prompt, stream, token) {
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
                this.createActionButton('🔧 Send to CodeSmith for fixes', 'ki-autoagent.sendToAgent', ['codesmith', `Fix these bugs found in ${fileName}:\n\n${bugReport}`], stream);
            }
        }
        catch (error) {
            stream.markdown(`❌ Bug hunting failed: ${error.message}`);
        }
    }
    async handleDebugCommand(prompt, stream, token) {
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
                }
                else if (packageJson.scripts?.['start']) {
                    debugCommand = 'npm start';
                    projectType = 'Node.js/Web';
                }
                stream.markdown(`📦 **Project Type:** ${projectType}\n`);
                stream.markdown(`🚀 **Debug Command:** \`${debugCommand}\`\n\n`);
            }
            catch (error) {
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
            this.createActionButton('🐛 Report Bugs Found', 'ki-autoagent.sendToAgent', ['codesmith', 'Fix these bugs found during debug session'], stream);
            this.createActionButton('📋 Save Debug Log', 'ki-autoagent.saveFile', [`debug-log-${Date.now()}.txt`, 'Debug session log'], stream);
        }
        catch (error) {
            stream.markdown(`❌ Debug session failed: ${error.message}`);
        }
    }
    async handleTestUICommand(prompt, stream, token) {
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
            this.createActionButton('🔧 Report UI Bugs', 'ki-autoagent.sendToAgent', ['codesmith', 'Fix these UI bugs found during testing'], stream);
        }
        catch (error) {
            stream.markdown(`❌ UI testing failed: ${error.message}`);
        }
    }
    async handleSecurityCommand(prompt, stream, token) {
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
            }
            else {
                // Scan entire workspace
                code = await this.getWorkspaceCode();
                fileName = 'Workspace';
                language = 'multiple';
            }
            const securityReport = await this.performSecurityScan(code, fileName, language, prompt);
            stream.markdown('## 🔐 Security Analysis Report\n\n');
            stream.markdown(securityReport);
            // Add action buttons
            this.createActionButton('⚠️ Create Security Issues', 'ki-autoagent.createGitHubIssues', [securityReport], stream);
        }
        catch (error) {
            stream.markdown(`❌ Security scan failed: ${error.message}`);
        }
    }
    async handlePerformanceCommand(prompt, stream, token) {
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
        }
        catch (error) {
            stream.markdown(`❌ Performance analysis failed: ${error.message}`);
        }
    }
    async handleStandardsCommand(prompt, stream, token) {
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
        }
        catch (error) {
            stream.markdown(`❌ Standards check failed: ${error.message}`);
        }
    }
    async handleTestCommand(prompt, stream, token) {
        stream.progress('🧪 Reviewing test coverage...');
        try {
            const testReport = await this.reviewTestCoverage(prompt);
            stream.markdown('## 🧪 Test Coverage Review\n\n');
            stream.markdown(testReport);
            // Add suggestions for missing tests
            this.createActionButton('➕ Generate Missing Tests', 'ki-autoagent.generateTests', [], stream);
        }
        catch (error) {
            stream.markdown(`❌ Test review failed: ${error.message}`);
        }
    }
    async handleGeneralReviewRequest(prompt, stream, token) {
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
                    this.createActionButton('🔧 Send bugs to CodeSmith', 'ki-autoagent.sendToAgent', ['codesmith', `Please fix these bugs found by ReviewerGPT:\n\n${bugReport}`], stream);
                }
                // Then do a comprehensive review
                const review = await this.performGeneralReview({ prompt }, []);
                stream.markdown('\n## 🔍 Full Code Review\n\n');
                stream.markdown(review);
            }
            catch (error) {
                stream.markdown(`❌ Review failed: ${error.message}`);
            }
        }
        else {
            stream.progress('🔍 Performing review...');
            try {
                const review = await this.performGeneralReview({ prompt }, []);
                stream.markdown('## 🔍 Review Results\n\n');
                stream.markdown(review);
            }
            catch (error) {
                stream.markdown(`❌ Review failed: ${error.message}`);
            }
        }
    }
    async handleArchitectureReviewCommand(prompt, stream, token) {
        stream.progress('🏛️ Reviewing architecture against requirements...');
        try {
            // Get conversation context to extract requirements and architect's solution
            const conversationContext = prompt || 'Review the architect\'s understanding of the requirements';
            const architectureReview = await this.validateArchitectureUnderstanding(conversationContext);
            stream.markdown('## 🏛️ Architecture Validation Report\n\n');
            stream.markdown(architectureReview);
            // Offer to create detailed report
            this.createActionButton('📋 Save Validation Report', 'ki-autoagent.saveFile', [`architecture-validation-${Date.now()}.md`, architectureReview], stream);
        }
        catch (error) {
            stream.markdown(`❌ Architecture review failed: ${error.message}`);
        }
    }
    // Review Methods
    async reviewCode(code, fileName, language, context) {
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
    async performSecurityScan(code, fileName, language, context) {
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
    async analyzePerformance(code, fileName, language, context) {
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
    async checkCodingStandards(code, language, context) {
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
    async findCommonBugs(code, language) {
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
    async reviewTestCoverage(context) {
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
    async performCodeReview(request, previousResults) {
        const context = this.buildContextFromResults(previousResults);
        return this.reviewCode('', 'workflow', 'unknown', `${request.prompt}\n\nContext:\n${context}`);
    }
    async performSecurityCheck(request, previousResults) {
        const context = this.buildContextFromResults(previousResults);
        return this.performSecurityScan('', 'workflow', 'unknown', `${request.prompt}\n\nContext:\n${context}`);
    }
    async performPerformanceReview(request, previousResults) {
        const context = this.buildContextFromResults(previousResults);
        return this.analyzePerformance('', 'workflow', 'unknown', `${request.prompt}\n\nContext:\n${context}`);
    }
    async performGeneralReview(request, previousResults) {
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
    buildContextFromResults(results) {
        return results
            .filter(r => r.status === 'success')
            .map(r => `${r.metadata?.step || 'Step'}: ${r.content}`)
            .join('\n\n');
    }
    async getWorkspaceCode() {
        // This would scan the workspace for code files
        // For now, return a placeholder
        return 'Workspace code scanning not yet implemented';
    }
    async validateArchitectureUnderstanding(context) {
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
exports.ReviewerGPTAgent = ReviewerGPTAgent;


/***/ }),

/***/ "./src/agents/TradeStratAgent.ts":
/*!***************************************!*\
  !*** ./src/agents/TradeStratAgent.ts ***!
  \***************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {


var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.TradeStratAgent = void 0;
/**
 * TradeStrat - Trading Strategy Expert
 * Powered by Claude 3.5 Sonnet for trading strategy development and analysis
 */
const vscode = __importStar(__webpack_require__(/*! vscode */ "vscode"));
const ChatAgent_1 = __webpack_require__(/*! ./base/ChatAgent */ "./src/agents/base/ChatAgent.ts");
const AnthropicService_1 = __webpack_require__(/*! ../utils/AnthropicService */ "./src/utils/AnthropicService.ts");
const ClaudeCodeService_1 = __webpack_require__(/*! ../services/ClaudeCodeService */ "./src/services/ClaudeCodeService.ts");
class TradeStratAgent extends ChatAgent_1.ChatAgent {
    constructor(context, dispatcher) {
        const config = {
            participantId: 'ki-autoagent.tradestrat',
            name: 'tradestrat',
            fullName: 'TradeStrat',
            description: 'Trading Strategy Expert powered by Claude 4.1 Sonnet',
            model: 'claude-4.1-sonnet-20250920',
            iconPath: vscode.Uri.joinPath(context.extensionUri, 'media', 'trading-icon.svg'),
            capabilities: [
                'Trading Strategy Development',
                'RON Strategy Implementation',
                'Backtesting Frameworks',
                'Risk Management',
                'Portfolio Optimization',
                'Market Analysis'
            ],
            commands: [
                { name: 'strategy', description: 'Develop and implement trading strategies', handler: 'handleStrategyCommand' },
                { name: 'backtest', description: 'Create backtesting and validation systems', handler: 'handleBacktestCommand' },
                { name: 'risk', description: 'Implement risk management and portfolio optimization', handler: 'handleRiskCommand' }
            ]
        };
        super(config, context, dispatcher);
        this.anthropicService = new AnthropicService_1.AnthropicService();
        this.claudeCodeService = (0, ClaudeCodeService_1.getClaudeCodeService)();
    }
    async handleRequest(request, context, stream, token) {
        const validationResult = await this.validateServiceConfig(stream);
        if (!validationResult) {
            return;
        }
        const command = request.command;
        const prompt = request.prompt;
        this.log(`Processing ${command ? `/${command}` : 'general'} trading request: ${prompt.substring(0, 100)}...`);
        if (command) {
            await this.handleCommand(command, prompt, stream, token);
        }
        else {
            await this.handleGeneralTradingRequest(prompt, stream, token);
        }
    }
    async processWorkflowStep(step, request, previousResults) {
        const context = await this.getWorkspaceContext();
        let systemPrompt = '';
        let userPrompt = '';
        switch (step.id) {
            case 'strategy_design':
                systemPrompt = this.getStrategyDesignSystemPrompt();
                userPrompt = `Design a trading strategy for: ${request.prompt}\n\nWorkspace Context:\n${context}`;
                break;
            case 'backtest':
                systemPrompt = this.getBacktestSystemPrompt();
                userPrompt = `Create backtesting framework for: ${request.prompt}\n\nStrategy Design:\n${this.extractPreviousContent(previousResults)}`;
                break;
            case 'risk_analysis':
                systemPrompt = this.getRiskAnalysisSystemPrompt();
                userPrompt = `Analyze risk management for: ${request.prompt}\n\nContext:\n${context}`;
                break;
            case 'strategy_validation':
                systemPrompt = this.getValidationSystemPrompt();
                userPrompt = `Validate trading strategy: ${request.prompt}\n\nImplementation:\n${this.extractPreviousContent(previousResults)}`;
                break;
            default:
                systemPrompt = this.getGeneralSystemPrompt();
                userPrompt = `${request.prompt}\n\nContext:\n${context}`;
        }
        try {
            const claudeService = await this.getClaudeService();
            const response = await claudeService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);
            return {
                status: 'success',
                content: response,
                metadata: {
                    step: step.id,
                    agent: 'tradestrat',
                    model: 'claude-3.5-sonnet'
                }
            };
        }
        catch (error) {
            throw new Error(`Failed to process ${step.id}: ${error.message}`);
        }
    }
    // Command Handlers
    async handleStrategyCommand(prompt, stream, token) {
        stream.progress('📈 Developing trading strategy...');
        const context = await this.getWorkspaceContext();
        const systemPrompt = this.getStrategyDesignSystemPrompt();
        const userPrompt = `Develop a comprehensive trading strategy for: ${prompt}\n\nWorkspace Context:\n${context}`;
        try {
            const claudeService = await this.getClaudeService();
            const response = await claudeService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);
            stream.markdown(response);
            // Extract strategy components for implementation
            const pythonCode = this.extractPythonCode(response);
            if (pythonCode) {
                this.createActionButton('⚡ Implement Strategy', 'ki-autoagent.createFile', ['strategy.py', pythonCode], stream);
            }
            // Offer backtesting
            this.createActionButton('🧪 Create Backtest', 'ki-autoagent.createBacktest', [prompt, response], stream);
            // Offer risk analysis
            this.createActionButton('⚠️ Analyze Risks', 'ki-autoagent.analyzeRisks', [prompt, response], stream);
        }
        catch (error) {
            stream.markdown(`❌ Error developing strategy: ${error.message}`);
        }
    }
    async handleBacktestCommand(prompt, stream, token) {
        stream.progress('🧪 Creating backtesting framework...');
        const context = await this.getWorkspaceContext();
        const systemPrompt = this.getBacktestSystemPrompt();
        const userPrompt = `Create a comprehensive backtesting framework for: ${prompt}\n\nWorkspace Context:\n${context}`;
        try {
            const claudeService = await this.getClaudeService();
            const response = await claudeService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);
            stream.markdown(response);
            // Extract backtesting code
            const backtestCode = this.extractPythonCode(response);
            if (backtestCode) {
                this.createActionButton('📊 Create Backtest Framework', 'ki-autoagent.createFile', ['backtest_engine.py', backtestCode], stream);
            }
            // Offer to create test data
            this.createActionButton('📈 Generate Test Data', 'ki-autoagent.generateTestData', [prompt], stream);
        }
        catch (error) {
            stream.markdown(`❌ Error creating backtesting framework: ${error.message}`);
        }
    }
    async handleRiskCommand(prompt, stream, token) {
        stream.progress('⚠️ Implementing risk management...');
        const context = await this.getWorkspaceContext();
        const systemPrompt = this.getRiskManagementSystemPrompt();
        const userPrompt = `Implement comprehensive risk management for: ${prompt}\n\nWorkspace Context:\n${context}`;
        try {
            const claudeService = await this.getClaudeService();
            const response = await claudeService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);
            stream.markdown(response);
            // Extract risk management code
            const riskCode = this.extractPythonCode(response);
            if (riskCode) {
                this.createActionButton('🛡️ Implement Risk Management', 'ki-autoagent.createFile', ['risk_manager.py', riskCode], stream);
            }
            // Offer portfolio optimization
            this.createActionButton('📊 Optimize Portfolio', 'ki-autoagent.optimizePortfolio', [prompt, response], stream);
        }
        catch (error) {
            stream.markdown(`❌ Error implementing risk management: ${error.message}`);
        }
    }
    async handleGeneralTradingRequest(prompt, stream, token) {
        stream.progress('💹 Processing trading request...');
        const context = await this.getWorkspaceContext();
        const systemPrompt = this.getGeneralSystemPrompt();
        const userPrompt = `${prompt}\n\nWorkspace Context:\n${context}`;
        try {
            const claudeService = await this.getClaudeService();
            const response = await claudeService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);
            stream.markdown(response);
            // Detect if this is RON strategy related
            if (prompt.toLowerCase().includes('ron') || response.toLowerCase().includes('ron strategy')) {
                this.createActionButton('🎯 Implement RON Strategy', 'ki-autoagent.implementRON', [response], stream);
            }
            // Auto-detect code for implementation
            const tradingCode = this.extractPythonCode(response);
            if (tradingCode) {
                this.createActionButton('⚡ Implement Code', 'ki-autoagent.createFile', ['trading_implementation.py', tradingCode], stream);
            }
        }
        catch (error) {
            stream.markdown(`❌ Error processing trading request: ${error.message}`);
        }
    }
    // System Prompts
    getGeneralSystemPrompt() {
        return `You are TradeStrat, an expert trading strategy developer and quantitative analyst. You specialize in:

- Trading strategy design and implementation
- Algorithmic trading systems
- Risk management and portfolio optimization
- Backtesting and performance analysis
- Market microstructure and execution
- RON (Reversal of Numbers) strategy implementation
- Python-based trading systems (pandas, numpy, streamlit, yfinance)

Key principles:
1. Always prioritize risk management
2. Implement robust backtesting before live trading
3. Focus on statistical significance and edge detection
4. Consider market conditions and regime changes
5. Provide clear performance metrics and validation

Format your responses with detailed explanations, working code, and practical implementation guidance.

${this.getSystemContextPrompt()}`;
    }
    getStrategyDesignSystemPrompt() {
        return `You are TradeStrat designing a comprehensive trading strategy. Structure your response as:

## Trading Strategy Design

### 1. Strategy Overview
- Strategy name and concept
- Market conditions and timeframes
- Expected holding periods
- Target assets/markets

### 2. Entry Rules
- Precise entry conditions
- Technical indicators required
- Fundamental filters (if any)
- Signal confirmation methods

### 3. Exit Rules
- Profit-taking strategies
- Stop-loss implementation
- Time-based exits
- Market condition exits

### 4. Risk Management
- Position sizing methodology
- Maximum drawdown limits
- Correlation and diversification
- Portfolio-level risk controls

### 5. Implementation Details
- Required data sources
- Calculation methodology
- Code structure and modules
- Performance monitoring

### 6. Backtesting Framework
- Historical data requirements
- Performance metrics to track
- Stress testing scenarios
- Out-of-sample validation

Provide complete Python implementation with pandas/numpy for data handling.

${this.getSystemContextPrompt()}`;
    }
    getBacktestSystemPrompt() {
        return `You are TradeStrat creating a robust backtesting framework. Include:

## Backtesting Framework Design

### 1. Data Management
- Historical data ingestion
- Data cleaning and validation
- Corporate actions handling
- Survivorship bias considerations

### 2. Signal Generation
- Strategy logic implementation
- Signal timing and execution
- Lookahead bias prevention
- Realistic latency modeling

### 3. Execution Simulation
- Order execution modeling
- Slippage and transaction costs
- Market impact considerations
- Partial fill handling

### 4. Performance Metrics
- Return calculations
- Risk-adjusted metrics (Sharpe, Sortino)
- Drawdown analysis
- Trade-level statistics

### 5. Visualization and Reporting
- Equity curve plotting
- Trade analysis charts
- Performance attribution
- Stress test results

### 6. Validation Techniques
- Out-of-sample testing
- Walk-forward analysis
- Monte Carlo simulation
- Bootstrap analysis

Provide production-ready Python code with proper error handling and logging.

${this.getSystemContextPrompt()}`;
    }
    getRiskManagementSystemPrompt() {
        return `You are TradeStrat implementing comprehensive risk management. Cover:

## Risk Management Framework

### 1. Position Sizing
- Kelly criterion implementation
- Volatility-based sizing
- Maximum position limits
- Correlation adjustments

### 2. Portfolio Risk Controls
- Value-at-Risk (VaR) calculation
- Expected Shortfall (ES)
- Maximum drawdown limits
- Sector/asset concentration limits

### 3. Dynamic Risk Adjustment
- Volatility regime detection
- Risk scaling mechanisms
- Market stress indicators
- Emergency stop procedures

### 4. Monitoring and Alerts
- Real-time risk metrics
- Breach notifications
- Performance tracking
- Risk attribution analysis

### 5. Stress Testing
- Historical scenario analysis
- Monte Carlo stress tests
- Tail risk evaluation
- Correlation breakdown scenarios

### 6. Implementation Tools
- Risk calculation engines
- Alert systems
- Reporting dashboards
- Integration with trading systems

Focus on practical, implementable solutions with clear mathematical foundations.

${this.getSystemContextPrompt()}`;
    }
    getValidationSystemPrompt() {
        return `You are TradeStrat validating trading strategies for production readiness. Analyze:

## Strategy Validation Checklist

### 1. Statistical Validation
- Statistical significance of returns
- Consistency across time periods
- Performance in different market regimes
- Correlation with market factors

### 2. Implementation Validation
- Code correctness and efficiency
- Data quality and completeness
- Signal generation accuracy
- Execution logic verification

### 3. Risk Validation
- Maximum drawdown analysis
- Tail risk assessment
- Stress test results
- Portfolio-level impact

### 4. Operational Validation
- System reliability and uptime
- Error handling and recovery
- Monitoring and alerting
- Compliance requirements

### 5. Performance Validation
- Live vs backtest performance
- Transaction cost impact
- Capacity constraints
- Scalability considerations

Provide detailed assessment with specific recommendations for improvement.

${this.getSystemContextPrompt()}`;
    }
    getRiskAnalysisSystemPrompt() {
        return this.getRiskManagementSystemPrompt();
    }
    // Service Configuration Methods
    async validateServiceConfig(stream) {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        const serviceMode = config.get('claude.serviceMode', 'claude-code');
        if (serviceMode === 'api') {
            if (!config.get('anthropic.apiKey')) {
                if (stream) {
                    stream.markdown('❌ **Anthropic API key not configured**\n\nPlease set your API key in VS Code settings:\n- Go to Settings\n- Search for "KI AutoAgent"\n- Set your Anthropic API key');
                }
                return false;
            }
        }
        else if (serviceMode === 'claude-code') {
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
    async getClaudeService() {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        const serviceMode = config.get('claude.serviceMode', 'claude-code');
        console.log(`[TradeStratAgent] Using service mode: ${serviceMode}`);
        if (serviceMode === 'claude-code') {
            const isAvailable = await this.claudeCodeService.isAvailable();
            if (isAvailable) {
                console.log('[TradeStratAgent] Using Claude Code CLI');
                return {
                    chat: async (messages) => {
                        // Extract the main user message content
                        const userMessage = messages.find(m => m.role === 'user')?.content || '';
                        const systemMessage = messages.find(m => m.role === 'system')?.content || '';
                        const fullPrompt = systemMessage ? `${systemMessage}\n\n${userMessage}` : userMessage;
                        const response = await this.claudeCodeService.sendMessage(fullPrompt, {
                            model: 'sonnet',
                            temperature: 0.7
                        });
                        return response.content;
                    }
                };
            }
            else {
                console.log('[TradeStratAgent] Claude Code CLI not available, falling back to Anthropic API');
            }
        }
        // Fall back to Anthropic API
        console.log('[TradeStratAgent] Using Anthropic API');
        return {
            chat: async (messages) => {
                return await this.anthropicService.chat(messages);
            }
        };
    }
    // Helper Methods
    extractPythonCode(content) {
        const pythonBlockRegex = /```python\n([\s\S]*?)```/g;
        const match = pythonBlockRegex.exec(content);
        return match ? match[1] : '';
    }
    extractPreviousContent(previousResults) {
        return previousResults
            .map(result => result.content)
            .join('\n\n---\n\n')
            .substring(0, 2000); // Limit context size
    }
}
exports.TradeStratAgent = TradeStratAgent;


/***/ }),

/***/ "./src/agents/base/ChatAgent.ts":
/*!**************************************!*\
  !*** ./src/agents/base/ChatAgent.ts ***!
  \**************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {


var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.ChatAgent = void 0;
/**
 * Base Chat Agent class for VS Code Chat Extensions
 * All specialized agents inherit from this base class
 */
const vscode = __importStar(__webpack_require__(/*! vscode */ "vscode"));
const UnifiedChatMixin_1 = __webpack_require__(/*! ../../mixins/UnifiedChatMixin */ "./src/mixins/UnifiedChatMixin.ts");
const AgentRegistry_1 = __webpack_require__(/*! ../../core/AgentRegistry */ "./src/core/AgentRegistry.ts");
class ChatAgent extends UnifiedChatMixin_1.UnifiedChatMixin {
    constructor(config, context, dispatcher) {
        super(); // Initialize UnifiedChatMixin
        this.config = config;
        this.stats = {
            totalExecutions: 0,
            successCount: 0,
            totalResponseTime: 0,
            lastExecution: undefined
        };
        this.context = context;
        this.dispatcher = dispatcher;
        // Set properties for UnifiedChatMixin
        this.name = config.fullName || config.name;
        this.role = config.description;
        this.model = config.model;
    }
    /**
     * Create VS Code chat request handler
     */
    createHandler() {
        return async (request, context, stream, token) => {
            const startTime = Date.now();
            this.stats.totalExecutions++;
            this.stats.lastExecution = new Date();
            try {
                // Show agent info
                stream.progress(`🤖 ${this.config.fullName} is working...`);
                // Handle the request
                await this.handleRequest(request, context, stream, token);
                // Update success stats
                this.stats.successCount++;
                this.stats.totalResponseTime += Date.now() - startTime;
            }
            catch (error) {
                await this.handleError(error, stream);
                this.stats.totalResponseTime += Date.now() - startTime;
            }
        };
    }
    /**
     * Execute a workflow step (called by dispatcher)
     */
    async executeStep(step, request, previousResults) {
        try {
            return await this.processWorkflowStep(step, request, previousResults);
        }
        catch (error) {
            return {
                status: 'error',
                content: `Error executing ${step.description}: ${error.message}`,
                metadata: { error: error.message, step: step.id }
            };
        }
    }
    /**
     * Handle command-specific logic
     */
    async handleCommand(command, prompt, stream, token) {
        const commandHandler = this.config.commands.find(cmd => cmd.name === command);
        if (commandHandler) {
            const methodName = commandHandler.handler;
            if (typeof this[methodName] === 'function') {
                await this[methodName](prompt, stream, token);
            }
            else {
                stream.markdown(`❌ Command handler '${methodName}' not implemented for ${command}`);
            }
        }
        else {
            stream.markdown(`❌ Unknown command: /${command}`);
            await this.showAvailableCommands(stream);
        }
    }
    /**
     * Show available commands for this agent
     */
    async showAvailableCommands(stream) {
        stream.markdown(`## Available Commands for ${this.config.fullName}\n\n`);
        for (const cmd of this.config.commands) {
            stream.markdown(`- **/${cmd.name}** - ${cmd.description}\n`);
        }
        stream.markdown(`\n💡 Use \`@${this.config.name} /<command> <your request>\``);
    }
    /**
     * Get workspace context for AI models
     */
    async getWorkspaceContext() {
        const workspaceContext = await this.dispatcher.getWorkspaceContext();
        let contextString = '';
        if (workspaceContext.currentFile) {
            contextString += `Current file: ${workspaceContext.currentFile}\n`;
        }
        if (workspaceContext.selectedText) {
            contextString += `Selected text:\n\`\`\`\n${workspaceContext.selectedText}\n\`\`\`\n`;
        }
        if (workspaceContext.workspaceRoots && workspaceContext.workspaceRoots.length > 0) {
            contextString += `Workspace: ${workspaceContext.workspaceRoots[0].name}\n`;
        }
        // Add task delegation context
        contextString += `\n\n${this.getTaskDelegationContext()}`;
        return contextString;
    }
    /**
     * Get task delegation context for this agent
     */
    getTaskDelegationContext() {
        const registry = AgentRegistry_1.AgentRegistry.getInstance();
        const agentId = this.config.name.toLowerCase().replace('agent', '');
        return registry.getTaskDelegationInfo(agentId);
    }
    /**
     * Check if a task should be delegated to another agent
     */
    async checkForTaskDelegation(prompt) {
        const registry = AgentRegistry_1.AgentRegistry.getInstance();
        const currentAgentId = this.config.name.toLowerCase().replace('agent', '');
        const suggestedAgent = registry.suggestAgentForTask(prompt);
        if (suggestedAgent && suggestedAgent !== currentAgentId) {
            const agentInfo = registry.getAgentInfo(suggestedAgent);
            if (agentInfo) {
                return `💡 This task might be better suited for **@${suggestedAgent}** who specializes in ${agentInfo.specialization}.\n\nWould you like me to:\n1. Continue with my analysis\n2. Suggest forwarding to @${suggestedAgent}\n\nOr you can directly ask @${suggestedAgent} for help.`;
            }
        }
        return null;
    }
    /**
     * Get system context prompt with agent awareness
     */
    getSystemContextPrompt() {
        const registry = AgentRegistry_1.AgentRegistry.getInstance();
        return `
## Available Agents in KI_AutoAgent System:
${registry.getAgentListDescription()}

You are ${this.config.fullName} with role: ${this.config.description}
${this.getTaskDelegationContext()}
`;
    }
    /**
     * Render code in the chat with syntax highlighting
     */
    renderCode(code, language, stream, title) {
        if (title) {
            stream.markdown(`### ${title}\n\n`);
        }
        stream.markdown(`\`\`\`${language}\n${code}\n\`\`\`\n\n`);
    }
    /**
     * Create action buttons for the user
     */
    createActionButton(title, command, args, stream) {
        stream.button({
            command,
            title,
            arguments: args
        });
    }
    /**
     * Add file reference to chat
     */
    addFileReference(filePath, stream) {
        try {
            const uri = vscode.Uri.file(filePath);
            stream.reference(uri);
        }
        catch (error) {
            console.log(this.showError('Error adding file reference', error));
        }
    }
    /**
     * Error handler
     */
    async handleError(error, stream) {
        console.log(this.showError(`Error in ${this.config.fullName}`, error));
        stream.markdown(`❌ **Error**: ${error.message}\n\n`);
        stream.markdown(`💡 **Suggestions:**\n`);
        stream.markdown(`- Check your API keys in settings\n`);
        stream.markdown(`- Verify your internet connection\n`);
        stream.markdown(`- Try rephrasing your request\n`);
        // Offer to show help
        this.createActionButton('Show Help', 'ki-autoagent.showHelp', [this.config.participantId], stream);
    }
    /**
     * Get agent statistics
     */
    getStats() {
        return {
            ...this.stats,
            successRate: this.stats.totalExecutions > 0
                ? this.stats.successCount / this.stats.totalExecutions
                : 0,
            averageResponseTime: this.stats.totalExecutions > 0
                ? this.stats.totalResponseTime / this.stats.totalExecutions
                : 0
        };
    }
    /**
     * Get AI model configuration
     */
    getModelConfig() {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        let model = this.config.model;
        let apiKey;
        switch (model) {
            case 'gpt-4o':
            case 'gpt-4o-mini':
                apiKey = config.get('openai.apiKey');
                break;
            case 'claude-3.5-sonnet':
                apiKey = config.get('anthropic.apiKey');
                break;
            case 'perplexity-pro':
                apiKey = config.get('perplexity.apiKey');
                break;
        }
        return { model, apiKey };
    }
    /**
     * Validate API configuration
     */
    validateApiConfig() {
        const { apiKey } = this.getModelConfig();
        return !!apiKey;
    }
    /**
     * Get max tokens from configuration
     */
    getMaxTokens() {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        return config.get('maxTokens', 4000);
    }
    /**
     * Check if logging is enabled
     */
    isLoggingEnabled() {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        return config.get('enableLogging', true);
    }
    /**
     * Log message if logging is enabled
     */
    log(message, level = 'info') {
        if (this.isLoggingEnabled()) {
            const timestamp = new Date().toISOString();
            console[level](`[${timestamp}] ${this.config.fullName}: ${message}`);
        }
    }
}
exports.ChatAgent = ChatAgent;


/***/ }),

/***/ "./src/core/AgentCommunicationBus.ts":
/*!*******************************************!*\
  !*** ./src/core/AgentCommunicationBus.ts ***!
  \*******************************************/
/***/ ((__unused_webpack_module, exports, __webpack_require__) => {


/**
 * AgentCommunicationBus - Inter-agent communication system
 * Enables agents to collaborate, share information, and coordinate actions
 */
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.AgentCommunicationBus = exports.MessageType = void 0;
exports.getCommunicationBus = getCommunicationBus;
const events_1 = __webpack_require__(/*! events */ "events");
var MessageType;
(function (MessageType) {
    MessageType["REQUEST"] = "request";
    MessageType["RESPONSE"] = "response";
    MessageType["NOTIFICATION"] = "notification";
    MessageType["QUERY"] = "query";
    MessageType["BROADCAST"] = "broadcast";
    MessageType["COLLABORATION_REQUEST"] = "collaboration_request";
    MessageType["COLLABORATION_RESPONSE"] = "collaboration_response";
    MessageType["TASK_DELEGATION"] = "task_delegation";
    MessageType["STATUS_UPDATE"] = "status_update";
    MessageType["ERROR"] = "error";
    MessageType["HELP_REQUEST"] = "help_request";
    MessageType["KNOWLEDGE_SHARE"] = "knowledge_share";
    MessageType["VALIDATION_REQUEST"] = "validation_request";
    MessageType["CONFLICT"] = "conflict";
})(MessageType || (exports.MessageType = MessageType = {}));
class AgentCommunicationBus {
    constructor() {
        this.handlers = new Map();
        this.messageQueue = [];
        this.processingQueue = false;
        this.collaborationSessions = new Map();
        this.messageHistory = [];
        this.responseCallbacks = new Map();
        this.eventBus = new events_1.EventEmitter();
        this.eventBus.setMaxListeners(50);
        this.stats = this.initializeStats();
        this.startQueueProcessor();
    }
    static getInstance() {
        if (!AgentCommunicationBus.instance) {
            AgentCommunicationBus.instance = new AgentCommunicationBus();
        }
        return AgentCommunicationBus.instance;
    }
    /**
     * Register an agent to receive messages
     */
    register(handler) {
        if (!this.handlers.has(handler.agentId)) {
            this.handlers.set(handler.agentId, []);
        }
        this.handlers.get(handler.agentId).push(handler);
        this.eventBus.emit('agent-registered', handler.agentId);
    }
    /**
     * Unregister an agent
     */
    unregister(agentId) {
        this.handlers.delete(agentId);
        this.eventBus.emit('agent-unregistered', agentId);
    }
    /**
     * Send a message to one or more agents
     */
    async send(message) {
        const fullMessage = {
            ...message,
            id: this.generateMessageId(),
            timestamp: Date.now()
        };
        // Add to history
        this.messageHistory.push(fullMessage);
        this.stats.totalMessages++;
        this.updateStats(fullMessage);
        // Add to queue
        this.messageQueue.push(fullMessage);
        // Emit event
        this.eventBus.emit('message-sent', fullMessage);
        // Process queue if not already processing
        if (!this.processingQueue) {
            this.processQueue();
        }
        return fullMessage.id;
    }
    /**
     * Send a message and wait for response
     */
    async request(message, timeout = 30000) {
        const messageId = await this.send({
            ...message,
            metadata: {
                ...(message.metadata || {}),
                requiresResponse: true,
                timeout
            }
        });
        return new Promise((resolve, reject) => {
            const timer = setTimeout(() => {
                this.responseCallbacks.delete(messageId);
                reject(new Error(`Request timeout for message ${messageId}`));
            }, timeout);
            this.responseCallbacks.set(messageId, (response) => {
                clearTimeout(timer);
                this.responseCallbacks.delete(messageId);
                resolve(response);
            });
        });
    }
    /**
     * Broadcast a message to all agents
     */
    async broadcast(from, type, content, metadata) {
        await this.send({
            from,
            to: 'broadcast',
            type: MessageType.BROADCAST,
            content,
            metadata: {
                priority: 'normal',
                requiresResponse: false,
                ...metadata
            }
        });
    }
    /**
     * Start a collaboration session between agents
     */
    async startCollaboration(task, participants, leader) {
        const session = {
            id: this.generateSessionId(),
            task,
            participants,
            leader: leader || participants[0],
            status: 'pending',
            sharedContext: new Map(),
            messages: [],
            results: new Map(),
            startTime: Date.now()
        };
        this.collaborationSessions.set(session.id, session);
        // Notify all participants
        await Promise.all(participants.map(agentId => this.send({
            from: 'system',
            to: agentId,
            type: MessageType.COLLABORATION_REQUEST,
            content: {
                sessionId: session.id,
                task,
                participants,
                leader: session.leader
            },
            metadata: {
                priority: 'high',
                requiresResponse: true,
                conversationId: session.id
            }
        })));
        session.status = 'active';
        this.eventBus.emit('collaboration-started', session);
        return session;
    }
    /**
     * Send a message within a collaboration session
     */
    async collaborationMessage(sessionId, from, content, type = MessageType.NOTIFICATION) {
        const session = this.collaborationSessions.get(sessionId);
        if (!session) {
            throw new Error(`Collaboration session ${sessionId} not found`);
        }
        // Send to all participants except sender
        const recipients = session.participants.filter(p => p !== from);
        const message = {
            from,
            to: recipients,
            type,
            content,
            metadata: {
                priority: 'normal',
                requiresResponse: false,
                conversationId: sessionId
            }
        };
        await this.send(message);
        // Add to session history
        session.messages.push({
            ...message,
            id: this.generateMessageId(),
            timestamp: Date.now()
        });
    }
    /**
     * Update shared context in collaboration session
     */
    updateCollaborationContext(sessionId, agentId, key, value) {
        const session = this.collaborationSessions.get(sessionId);
        if (!session)
            return;
        session.sharedContext.set(key, value);
        // Notify other participants
        this.collaborationMessage(sessionId, agentId, { key, value }, MessageType.STATUS_UPDATE);
    }
    /**
     * Complete a collaboration session
     */
    completeCollaboration(sessionId, results) {
        const session = this.collaborationSessions.get(sessionId);
        if (!session)
            return;
        session.status = 'completed';
        session.results = results;
        session.endTime = Date.now();
        this.eventBus.emit('collaboration-completed', session);
        // Clean up after delay
        setTimeout(() => {
            this.collaborationSessions.delete(sessionId);
        }, 60000);
    }
    /**
     * Request help from other agents
     */
    async requestHelp(from, problem, preferredAgents) {
        const message = {
            from,
            to: preferredAgents || 'broadcast',
            type: MessageType.HELP_REQUEST,
            content: problem,
            metadata: {
                priority: 'high',
                requiresResponse: true,
                timeout: 10000
            }
        };
        const responses = [];
        if (preferredAgents) {
            // Request from specific agents
            for (const agentId of preferredAgents) {
                try {
                    const response = await this.request({ ...message, to: agentId, metadata: message.metadata }, 10000);
                    if (response)
                        responses.push(response);
                }
                catch (error) {
                    console.warn(`No response from ${agentId}:`, error);
                }
            }
        }
        else {
            // Broadcast and collect responses
            await this.broadcast(from, MessageType.HELP_REQUEST, problem, {
                priority: 'high',
                requiresResponse: true
            });
            // Wait for responses
            await new Promise(resolve => setTimeout(resolve, 5000));
            // Collect responses from history
            const requestTime = Date.now();
            responses.push(...this.messageHistory
                .filter(msg => msg.type === MessageType.RESPONSE &&
                msg.timestamp > requestTime - 5000 &&
                msg.replyTo === message.from)
                .map(msg => msg.content));
        }
        return responses;
    }
    /**
     * Share knowledge between agents
     */
    async shareKnowledge(from, knowledge, relevantAgents) {
        await this.send({
            from,
            to: relevantAgents || 'broadcast',
            type: MessageType.KNOWLEDGE_SHARE,
            content: knowledge,
            metadata: {
                priority: 'low',
                requiresResponse: false
            }
        });
    }
    /**
     * Request validation from another agent
     */
    async requestValidation(from, validator, content) {
        return this.request({
            from,
            to: validator,
            type: MessageType.VALIDATION_REQUEST,
            content,
            metadata: {
                priority: 'normal',
                requiresResponse: true
            }
        }, 15000);
    }
    /**
     * Report a conflict requiring arbitration
     */
    async reportConflict(reportingAgent, conflictingAgents, issue) {
        // Send to OpusArbitrator
        await this.send({
            from: reportingAgent,
            to: 'OpusArbitrator',
            type: MessageType.CONFLICT,
            content: {
                conflictingAgents,
                issue,
                reportedBy: reportingAgent
            },
            metadata: {
                priority: 'critical',
                requiresResponse: true
            }
        });
    }
    /**
     * Process message queue
     */
    async processQueue() {
        if (this.processingQueue || this.messageQueue.length === 0)
            return;
        this.processingQueue = true;
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            try {
                await this.deliverMessage(message);
            }
            catch (error) {
                console.error(`Error delivering message ${message.id}:`, error);
                this.stats.failedMessages++;
                // Retry logic
                if (message.metadata.retryCount === undefined) {
                    message.metadata.retryCount = 0;
                }
                if (message.metadata.retryCount < 3) {
                    message.metadata.retryCount++;
                    this.messageQueue.push(message);
                }
                else {
                    this.eventBus.emit('message-failed', { message, error });
                }
            }
        }
        this.processingQueue = false;
    }
    /**
     * Deliver a message to recipients
     */
    async deliverMessage(message) {
        const recipients = this.determineRecipients(message);
        for (const recipientId of recipients) {
            const handlers = this.handlers.get(recipientId) || [];
            for (const handler of handlers) {
                // Check if handler accepts this message type
                if (!handler.messageTypes.includes(message.type))
                    continue;
                // Apply filter if present
                if (handler.filter && !handler.filter(message))
                    continue;
                try {
                    const response = await handler.handler(message);
                    // Handle response if required
                    if (message.metadata.requiresResponse && response !== undefined) {
                        // Send response back
                        await this.send({
                            from: recipientId,
                            to: message.from,
                            type: MessageType.RESPONSE,
                            content: response,
                            metadata: {
                                priority: 'normal',
                                requiresResponse: false,
                                conversationId: message.metadata.conversationId
                            },
                            replyTo: message.id
                        });
                        // Trigger callback if waiting
                        const callback = this.responseCallbacks.get(message.id);
                        if (callback) {
                            callback(response);
                        }
                    }
                    this.eventBus.emit('message-delivered', { message, recipientId });
                }
                catch (error) {
                    console.error(`Handler error for ${recipientId}:`, error);
                    this.eventBus.emit('handler-error', { message, recipientId, error });
                }
            }
        }
    }
    /**
     * Determine message recipients
     */
    determineRecipients(message) {
        if (message.to === 'broadcast') {
            return Array.from(this.handlers.keys());
        }
        if (Array.isArray(message.to)) {
            return message.to;
        }
        return [message.to];
    }
    /**
     * Start queue processor
     */
    startQueueProcessor() {
        setInterval(() => {
            if (!this.processingQueue && this.messageQueue.length > 0) {
                this.processQueue();
            }
        }, 100);
    }
    /**
     * Initialize statistics
     */
    initializeStats() {
        return {
            totalMessages: 0,
            messagesByType: new Map(),
            messagesByAgent: new Map(),
            averageResponseTime: 0,
            activeSessions: 0,
            failedMessages: 0
        };
    }
    /**
     * Update statistics
     */
    updateStats(message) {
        // Update message type count
        const typeCount = this.stats.messagesByType.get(message.type) || 0;
        this.stats.messagesByType.set(message.type, typeCount + 1);
        // Update agent message count
        const agentCount = this.stats.messagesByAgent.get(message.from) || 0;
        this.stats.messagesByAgent.set(message.from, agentCount + 1);
        // Update active sessions
        this.stats.activeSessions = this.collaborationSessions.size;
    }
    /**
     * Get communication statistics
     */
    getStats() {
        // Calculate average response time
        let totalResponseTime = 0;
        let responseCount = 0;
        this.messageHistory.forEach(msg => {
            if (msg.type === MessageType.RESPONSE && msg.replyTo) {
                const originalMsg = this.messageHistory.find(m => m.id === msg.replyTo);
                if (originalMsg) {
                    totalResponseTime += msg.timestamp - originalMsg.timestamp;
                    responseCount++;
                }
            }
        });
        this.stats.averageResponseTime = responseCount > 0
            ? totalResponseTime / responseCount
            : 0;
        return { ...this.stats };
    }
    /**
     * Get message history
     */
    getMessageHistory(filter) {
        let history = [...this.messageHistory];
        if (filter) {
            if (filter.from) {
                history = history.filter(msg => msg.from === filter.from);
            }
            if (filter.to) {
                history = history.filter(msg => msg.to === filter.to ||
                    (Array.isArray(msg.to) && msg.to.includes(filter.to)));
            }
            if (filter.type) {
                history = history.filter(msg => msg.type === filter.type);
            }
            if (filter.conversationId) {
                history = history.filter(msg => msg.metadata.conversationId === filter.conversationId);
            }
            if (filter.startTime) {
                history = history.filter(msg => msg.timestamp >= filter.startTime);
            }
            if (filter.endTime) {
                history = history.filter(msg => msg.timestamp <= filter.endTime);
            }
        }
        return history;
    }
    /**
     * Get active collaboration sessions
     */
    getActiveSessions() {
        return Array.from(this.collaborationSessions.values())
            .filter(session => session.status === 'active');
    }
    /**
     * Generate unique message ID
     */
    generateMessageId() {
        return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    /**
     * Generate unique session ID
     */
    generateSessionId() {
        return `ses_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    /**
     * Clear all data (for testing/reset)
     */
    clear() {
        this.messageQueue = [];
        this.messageHistory = [];
        this.collaborationSessions.clear();
        this.responseCallbacks.clear();
        this.stats = this.initializeStats();
    }
}
exports.AgentCommunicationBus = AgentCommunicationBus;
// Export singleton instance getter
function getCommunicationBus() {
    return AgentCommunicationBus.getInstance();
}


/***/ }),

/***/ "./src/core/AgentConfigurationManager.ts":
/*!***********************************************!*\
  !*** ./src/core/AgentConfigurationManager.ts ***!
  \***********************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {


var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.AgentConfigurationManager = void 0;
/**
 * Agent Configuration Manager
 * Handles per-agent model selection, instruction loading, and self-adaptation
 */
const vscode = __importStar(__webpack_require__(/*! vscode */ "vscode"));
const path = __importStar(__webpack_require__(/*! path */ "path"));
const fs = __importStar(__webpack_require__(/*! fs/promises */ "fs/promises"));
const AgentConfiguration_1 = __webpack_require__(/*! ../types/AgentConfiguration */ "./src/types/AgentConfiguration.ts");
class AgentConfigurationManager {
    constructor(context) {
        this.configPath = '';
        this.context = context;
        this.configuration = {
            models: new Map(),
            instructions: new Map(),
            learning: this.getDefaultLearningConfig(),
            metrics: new Map()
        };
    }
    static getInstance(context) {
        if (!AgentConfigurationManager.instance) {
            AgentConfigurationManager.instance = new AgentConfigurationManager(context);
        }
        return AgentConfigurationManager.instance;
    }
    /**
     * Initialize configuration system
     */
    async initialize() {
        try {
            // Determine configuration path
            await this.determineConfigPath();
            // Ensure configuration directory structure exists
            await this.ensureConfigStructure();
            // Load existing configuration or create defaults
            await this.loadConfiguration();
            // Load instruction sets
            await this.loadInstructionSets();
            console.log('✅ AgentConfigurationManager initialized');
        }
        catch (error) {
            console.error('❌ Failed to initialize AgentConfigurationManager:', error);
            throw error;
        }
    }
    /**
     * Get agent model configuration
     */
    getAgentModel(agentId) {
        const config = this.configuration.models.get(agentId);
        return config?.selectedModel || AgentConfiguration_1.DEFAULT_AGENT_MODELS[agentId] || 'claude-sonnet-4-20250514';
    }
    /**
     * Set agent model
     */
    async setAgentModel(agentId, modelId) {
        const config = this.configuration.models.get(agentId) || this.createDefaultModelConfig(agentId);
        config.selectedModel = modelId;
        config.lastUpdated = new Date().toISOString();
        this.configuration.models.set(agentId, config);
        await this.saveModelConfiguration();
        console.log(`🤖 Updated ${agentId} model to ${modelId}`);
    }
    /**
     * Get agent instructions
     */
    async getAgentInstructions(agentId) {
        const instructionSet = this.configuration.instructions.get(agentId);
        if (instructionSet) {
            return instructionSet.content;
        }
        // Load from file if not in memory
        return await this.loadInstructionFile(agentId);
    }
    /**
     * Update agent instructions (self-adaptation)
     */
    async updateAgentInstructions(agentId, newContent, reason, trigger) {
        const currentInstructions = await this.getAgentInstructions(agentId);
        // Create adaptation record
        const adaptation = {
            timestamp: new Date().toISOString(),
            trigger,
            oldContent: currentInstructions,
            newContent,
            reason
        };
        // Update instruction set
        const instructionSet = this.configuration.instructions.get(agentId) || {
            agentId,
            version: '1.0.0',
            content: currentInstructions,
            lastModified: new Date().toISOString(),
            modifiedBy: trigger === 'manual' ? 'user' : 'self-adaptation',
            successRate: 0,
            totalExecutions: 0,
            adaptationHistory: []
        };
        instructionSet.content = newContent;
        instructionSet.lastModified = new Date().toISOString();
        instructionSet.modifiedBy = trigger === 'manual' ? 'user' : 'self-adaptation';
        instructionSet.adaptationHistory.push(adaptation);
        // Keep only last 50 adaptations to prevent memory bloat
        if (instructionSet.adaptationHistory.length > 50) {
            instructionSet.adaptationHistory = instructionSet.adaptationHistory.slice(-50);
        }
        this.configuration.instructions.set(agentId, instructionSet);
        // Save to file
        await this.saveInstructionFile(agentId, instructionSet);
        console.log(`📝 Updated instructions for ${agentId}: ${reason}`);
    }
    /**
     * Record agent performance for learning
     */
    async recordAgentPerformance(agentId, success, responseTime, context) {
        const metrics = this.configuration.metrics.get(agentId) || this.createDefaultMetrics(agentId);
        metrics.totalExecutions++;
        if (success) {
            metrics.successfulExecutions++;
            metrics.currentStreak++;
            metrics.bestStreak = Math.max(metrics.bestStreak, metrics.currentStreak);
        }
        else {
            metrics.failedExecutions++;
            metrics.currentStreak = 0;
        }
        // Update average response time
        const totalTime = metrics.averageResponseTime * (metrics.totalExecutions - 1) + responseTime;
        metrics.averageResponseTime = totalTime / metrics.totalExecutions;
        metrics.lastExecution = new Date().toISOString();
        this.configuration.metrics.set(agentId, metrics);
        // Check if auto-learning should trigger
        if (this.configuration.learning.enabled) {
            await this.checkForLearningOpportunity(agentId, success, context);
        }
        // Periodically save metrics
        if (metrics.totalExecutions % 10 === 0) {
            await this.saveMetrics();
        }
    }
    /**
     * Get available models for an agent
     */
    getAvailableModels() {
        return AgentConfiguration_1.AVAILABLE_MODELS;
    }
    /**
     * Get agent performance metrics
     */
    getAgentMetrics(agentId) {
        return this.configuration.metrics.get(agentId);
    }
    /**
     * Get learning configuration
     */
    getLearningConfig() {
        return this.configuration.learning;
    }
    /**
     * Update learning configuration
     */
    async updateLearningConfig(config) {
        this.configuration.learning = { ...this.configuration.learning, ...config };
        await this.saveLearningConfig();
    }
    // Private methods
    async determineConfigPath() {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (workspaceFolders && workspaceFolders.length > 0) {
            // Use workspace-specific configuration
            this.configPath = path.join(workspaceFolders[0].uri.fsPath, '.kiautoagent');
        }
        else {
            // Use global configuration in user's home directory
            const homeDir = process.env.HOME || process.env.USERPROFILE || '';
            this.configPath = path.join(homeDir, '.kiautoagent');
        }
    }
    async ensureConfigStructure() {
        const directories = [
            this.configPath,
            path.join(this.configPath, 'config'),
            path.join(this.configPath, 'instructionsets'),
            path.join(this.configPath, 'learning')
        ];
        for (const dir of directories) {
            try {
                await fs.mkdir(dir, { recursive: true });
            }
            catch (error) {
                console.warn(`Could not create directory ${dir}:`, error);
            }
        }
    }
    async loadConfiguration() {
        // Load model configurations
        await this.loadModelConfiguration();
        // Load learning configuration
        await this.loadLearningConfiguration();
        // Load metrics
        await this.loadMetrics();
    }
    async loadModelConfiguration() {
        try {
            const configFile = path.join(this.configPath, 'config', 'agent-models.json');
            const data = await fs.readFile(configFile, 'utf-8');
            const configs = JSON.parse(data);
            for (const config of configs) {
                this.configuration.models.set(config.agentId, config);
            }
        }
        catch (error) {
            // Create default configuration
            for (const [agentId, defaultModel] of Object.entries(AgentConfiguration_1.DEFAULT_AGENT_MODELS)) {
                this.configuration.models.set(agentId, this.createDefaultModelConfig(agentId));
            }
            await this.saveModelConfiguration();
        }
    }
    async saveModelConfiguration() {
        try {
            const configFile = path.join(this.configPath, 'config', 'agent-models.json');
            const configs = Array.from(this.configuration.models.values());
            await fs.writeFile(configFile, JSON.stringify(configs, null, 2));
        }
        catch (error) {
            console.error('Failed to save model configuration:', error);
        }
    }
    async loadInstructionSets() {
        const instructionDir = path.join(this.configPath, 'instructionsets');
        const agentIds = ['orchestrator', 'richter', 'architect', 'codesmith', 'tradestrat', 'research'];
        for (const agentId of agentIds) {
            try {
                await this.loadInstructionFile(agentId);
            }
            catch (error) {
                console.warn(`Could not load instructions for ${agentId}:`, error);
                // Copy from extension bundle
                await this.copyDefaultInstructionFile(agentId);
            }
        }
    }
    async loadInstructionFile(agentId) {
        const instructionFile = path.join(this.configPath, 'instructionsets', `${agentId}.md`);
        try {
            const content = await fs.readFile(instructionFile, 'utf-8');
            // Update in-memory instruction set
            const instructionSet = {
                agentId,
                version: '1.0.0',
                content,
                lastModified: new Date().toISOString(),
                modifiedBy: 'user',
                successRate: 0,
                totalExecutions: 0,
                adaptationHistory: []
            };
            this.configuration.instructions.set(agentId, instructionSet);
            return content;
        }
        catch (error) {
            throw new Error(`Could not load instruction file for ${agentId}: ${error}`);
        }
    }
    async saveInstructionFile(agentId, instructionSet) {
        const instructionFile = path.join(this.configPath, 'instructionsets', `${agentId}.md`);
        await fs.writeFile(instructionFile, instructionSet.content);
    }
    async copyDefaultInstructionFile(agentId) {
        try {
            const sourcePath = path.join(this.context.extensionPath, 'src', 'instructionsets', `${agentId}.md`);
            const targetPath = path.join(this.configPath, 'instructionsets', `${agentId}.md`);
            const content = await fs.readFile(sourcePath, 'utf-8');
            await fs.writeFile(targetPath, content);
            console.log(`📋 Copied default instructions for ${agentId}`);
        }
        catch (error) {
            console.error(`Failed to copy default instructions for ${agentId}:`, error);
        }
    }
    createDefaultModelConfig(agentId) {
        const defaultModel = AgentConfiguration_1.DEFAULT_AGENT_MODELS[agentId] || 'claude-sonnet-4-20250514';
        return {
            agentId,
            displayName: agentId.charAt(0).toUpperCase() + agentId.slice(1),
            selectedModel: defaultModel,
            availableModels: Object.keys(AgentConfiguration_1.AVAILABLE_MODELS),
            instructionFile: `${agentId}.md`,
            lastUpdated: new Date().toISOString(),
            performanceScore: 0
        };
    }
    createDefaultMetrics(agentId) {
        return {
            agentId,
            totalExecutions: 0,
            successfulExecutions: 0,
            failedExecutions: 0,
            averageResponseTime: 0,
            lastExecution: new Date().toISOString(),
            successPatterns: [],
            failurePatterns: [],
            currentStreak: 0,
            bestStreak: 0
        };
    }
    getDefaultLearningConfig() {
        return {
            enabled: true,
            adaptationThreshold: 0.8, // 80% success rate required
            maxAdaptationsPerDay: 3,
            confidenceLevel: 0.9,
            learningModes: {
                successBasedLearning: true,
                failureBasedLearning: false,
                patternRecognition: true,
                contextualAdaptation: true
            }
        };
    }
    async loadLearningConfiguration() {
        try {
            const configFile = path.join(this.configPath, 'config', 'learning-settings.json');
            const data = await fs.readFile(configFile, 'utf-8');
            this.configuration.learning = { ...this.configuration.learning, ...JSON.parse(data) };
        }
        catch (error) {
            // Use defaults and save
            await this.saveLearningConfig();
        }
    }
    async saveLearningConfig() {
        try {
            const configFile = path.join(this.configPath, 'config', 'learning-settings.json');
            await fs.writeFile(configFile, JSON.stringify(this.configuration.learning, null, 2));
        }
        catch (error) {
            console.error('Failed to save learning configuration:', error);
        }
    }
    async loadMetrics() {
        try {
            const metricsFile = path.join(this.configPath, 'config', 'performance-metrics.json');
            const data = await fs.readFile(metricsFile, 'utf-8');
            const metricsArray = JSON.parse(data);
            for (const metrics of metricsArray) {
                this.configuration.metrics.set(metrics.agentId, metrics);
            }
        }
        catch (error) {
            // No metrics file yet, will be created on first save
        }
    }
    async saveMetrics() {
        try {
            const metricsFile = path.join(this.configPath, 'config', 'performance-metrics.json');
            const metricsArray = Array.from(this.configuration.metrics.values());
            await fs.writeFile(metricsFile, JSON.stringify(metricsArray, null, 2));
        }
        catch (error) {
            console.error('Failed to save metrics:', error);
        }
    }
    async checkForLearningOpportunity(agentId, success, context) {
        const metrics = this.configuration.metrics.get(agentId);
        if (!metrics)
            return;
        const successRate = metrics.successfulExecutions / metrics.totalExecutions;
        // Only adapt if we have enough data and high success rate
        if (metrics.totalExecutions < 10)
            return;
        if (successRate < this.configuration.learning.adaptationThreshold)
            return;
        // Check if we haven't adapted too much today
        const today = new Date().toDateString();
        const instructionSet = this.configuration.instructions.get(agentId);
        const todayAdaptations = instructionSet?.adaptationHistory.filter(a => new Date(a.timestamp).toDateString() === today).length || 0;
        if (todayAdaptations >= this.configuration.learning.maxAdaptationsPerDay)
            return;
        // Trigger learning adaptation (would call LLM to analyze patterns and suggest improvements)
        console.log(`🧠 Learning opportunity detected for ${agentId}: ${successRate.toFixed(2)} success rate`);
        // This would be implemented to call the agent's model to analyze its own performance
        // and suggest instruction improvements
    }
}
exports.AgentConfigurationManager = AgentConfigurationManager;


/***/ }),

/***/ "./src/core/AgentRegistry.ts":
/*!***********************************!*\
  !*** ./src/core/AgentRegistry.ts ***!
  \***********************************/
/***/ ((__unused_webpack_module, exports) => {


Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.AgentRegistry = void 0;
class AgentRegistry {
    static getInstance() {
        if (!AgentRegistry.instance) {
            AgentRegistry.instance = new AgentRegistry();
        }
        return AgentRegistry.instance;
    }
    /**
     * Get all registered agents with their capabilities
     */
    getRegisteredAgents() {
        return Object.entries(AgentRegistry.AGENT_CAPABILITIES).map(([id, capability]) => ({
            id,
            name: this.getAgentDisplayName(id),
            model: capability.model,
            specialization: capability.specialization,
            canHandle: capability.canHandle,
            instructionSet: capability.instructionSet
        }));
    }
    /**
     * Get information about a specific agent
     */
    getAgentInfo(agentId) {
        const capability = AgentRegistry.AGENT_CAPABILITIES[agentId];
        if (!capability)
            return undefined;
        return {
            id: agentId,
            name: this.getAgentDisplayName(agentId),
            model: capability.model,
            specialization: capability.specialization,
            canHandle: capability.canHandle,
            instructionSet: capability.instructionSet
        };
    }
    /**
     * Suggest the best agent for a given task based on keywords
     */
    suggestAgentForTask(taskDescription) {
        const lowerTask = taskDescription.toLowerCase();
        let bestMatch = null;
        for (const [agentId, capability] of Object.entries(AgentRegistry.AGENT_CAPABILITIES)) {
            let score = 0;
            for (const keyword of capability.canHandle) {
                if (lowerTask.includes(keyword)) {
                    score += keyword.split('-').length; // Multi-word keywords get higher score
                }
            }
            if (score > 0 && (!bestMatch || score > bestMatch.score)) {
                bestMatch = { agent: agentId, score };
            }
        }
        return bestMatch?.agent || null;
    }
    /**
     * Get a formatted list of all agents for display
     */
    getAgentListDescription() {
        const agents = this.getRegisteredAgents();
        return agents.map((agent, index) => `${index + 1}. **${agent.name}** - ${agent.specialization} (${agent.model})`).join('\n');
    }
    /**
     * Get task delegation suggestions for a specific agent
     */
    getTaskDelegationInfo(currentAgentId) {
        const currentAgent = this.getAgentInfo(currentAgentId);
        if (!currentAgent)
            return '';
        const otherAgents = this.getRegisteredAgents().filter(a => a.id !== currentAgentId);
        let delegationInfo = `## Task Delegation Guidelines\n\n`;
        delegationInfo += `You are **${currentAgent.name}** specializing in: ${currentAgent.specialization}\n\n`;
        delegationInfo += `When encountering tasks outside your expertise, suggest these agents:\n\n`;
        for (const agent of otherAgents) {
            const keywords = agent.canHandle.slice(0, 3).join(', ');
            delegationInfo += `- **${keywords}** → Suggest: "@${agent.id} specializes in ${agent.specialization}"\n`;
        }
        delegationInfo += `\nYou ARE the expert for: ${currentAgent.canHandle.join(', ')}`;
        return delegationInfo;
    }
    getAgentDisplayName(agentId) {
        const nameMap = {
            'orchestrator': 'OrchestratorAgent',
            'architect': 'ArchitectAgent',
            'codesmith': 'CodeSmithAgent',
            'tradestrat': 'TradeStratAgent',
            'research': 'ResearchAgent',
            'opus-arbitrator': 'OpusArbitratorAgent',
            'docu': 'DocuBot',
            'reviewer': 'ReviewerGPT',
            'fixer': 'FixerBot'
        };
        return nameMap[agentId] || agentId;
    }
}
exports.AgentRegistry = AgentRegistry;
// Static registry of agent capabilities for task delegation
AgentRegistry.AGENT_CAPABILITIES = {
    'orchestrator': {
        specialization: 'Multi-Agent Workflow Coordination',
        canHandle: ['workflow', 'orchestration', 'multi-step', 'complex-tasks', 'coordination'],
        model: 'gpt-5-2025-09-12',
        instructionSet: 'orchestrator.md'
    },
    'architect': {
        specialization: 'System Architecture & Design',
        canHandle: ['architecture', 'design', 'patterns', 'scalability', 'tech-stack', 'system-design', 'database-design'],
        model: 'gpt-5-2025-09-12',
        instructionSet: 'architect.md'
    },
    'codesmith': {
        specialization: 'Code Implementation & Optimization',
        canHandle: ['coding', 'implementation', 'optimization', 'testing', 'debugging', 'refactoring', 'code-review'],
        model: 'claude-4.1-sonnet-20250920',
        instructionSet: 'codesmith.md'
    },
    'tradestrat': {
        specialization: 'Trading Strategies & Financial Analysis',
        canHandle: ['trading', 'algorithms', 'financial', 'backtesting', 'market-analysis', 'portfolio', 'risk-management'],
        model: 'claude-4.1-sonnet-20250920',
        instructionSet: 'tradestrat.md'
    },
    'research': {
        specialization: 'Web Research & Information Gathering',
        canHandle: ['research', 'web-search', 'documentation', 'fact-checking', 'information-gathering', 'api-docs'],
        model: 'perplexity-llama-3.1-sonar-huge-128k',
        instructionSet: 'research.md'
    },
    'opus-arbitrator': {
        specialization: 'Agent Conflict Resolution',
        canHandle: ['conflicts', 'decision-making', 'arbitration', 'dispute-resolution', 'consensus'],
        model: 'claude-4.1-opus-20250915',
        instructionSet: 'richter.md'
    },
    'docu': {
        specialization: 'Technical Documentation & API Reference',
        canHandle: ['documentation', 'readme', 'api-docs', 'user-guides', 'comments', 'changelog', 'technical-writing', 'instruction-management'],
        model: 'gpt-5-2025-09-12',
        instructionSet: 'docubot-instructions.md'
    },
    'reviewer': {
        specialization: 'Code Review & Security Analysis',
        canHandle: ['code-review', 'security', 'performance-analysis', 'standards', 'testing', 'quality-assurance', 'vulnerabilities', 'architecture-validation'],
        model: 'gpt-5-mini-2025-09-20',
        instructionSet: 'reviewergpt-instructions.md'
    },
    'fixer': {
        specialization: 'Bug Fixing & Optimization',
        canHandle: ['bug-fixing', 'debugging', 'error-resolution', 'optimization', 'refactoring', 'modernization', 'hotfix'],
        model: 'claude-4.1-sonnet-20250920',
        instructionSet: 'fixerbot-instructions.md'
    }
};


/***/ }),

/***/ "./src/core/ConversationContextManager.ts":
/*!************************************************!*\
  !*** ./src/core/ConversationContextManager.ts ***!
  \************************************************/
/***/ ((__unused_webpack_module, exports) => {


/**
 * Manages conversation context and history across multiple agent interactions
 * Ensures that agents can access and build upon previous outputs
 */
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.ConversationContextManager = void 0;
class ConversationContextManager {
    constructor() {
        this.conversationHistory = [];
        this.maxHistorySize = 50; // Keep last 50 interactions
    }
    static getInstance() {
        if (!ConversationContextManager.instance) {
            ConversationContextManager.instance = new ConversationContextManager();
        }
        return ConversationContextManager.instance;
    }
    /**
     * Add a new entry to the conversation history
     */
    addEntry(entry) {
        this.conversationHistory.push(entry);
        // Trim history if it exceeds max size
        if (this.conversationHistory.length > this.maxHistorySize) {
            this.conversationHistory = this.conversationHistory.slice(-this.maxHistorySize);
        }
        console.log(`[CONTEXT-MANAGER] Added entry from ${entry.agent} (${entry.step})`);
        console.log(`[CONTEXT-MANAGER] Total history size: ${this.conversationHistory.length} entries`);
    }
    /**
     * Get recent conversation history
     */
    getRecentHistory(limit = 5) {
        return this.conversationHistory.slice(-limit);
    }
    /**
     * Get conversation history for a specific agent
     */
    getAgentHistory(agentName, limit = 5) {
        return this.conversationHistory
            .filter(entry => entry.agent === agentName)
            .slice(-limit);
    }
    /**
     * Get formatted conversation context for inclusion in prompts
     */
    getFormattedContext(limit = 5) {
        const recent = this.getRecentHistory(limit);
        if (recent.length === 0) {
            return '';
        }
        let context = '\n## Conversation History:\n';
        recent.forEach(entry => {
            context += `\n### ${entry.agent} (${entry.step}) - ${entry.timestamp}:\n`;
            context += `**Input:** ${entry.input.substring(0, 200)}...\n`;
            context += `**Output:** ${entry.output.substring(0, 500)}...\n`;
        });
        return context;
    }
    /**
     * Get the last output from any agent
     */
    getLastOutput() {
        if (this.conversationHistory.length === 0) {
            return null;
        }
        return this.conversationHistory[this.conversationHistory.length - 1].output;
    }
    /**
     * Clear conversation history
     */
    clearHistory() {
        this.conversationHistory = [];
        console.log(`[CONTEXT-MANAGER] Conversation history cleared`);
    }
    /**
     * Export conversation history as JSON
     */
    exportHistory() {
        return JSON.stringify(this.conversationHistory, null, 2);
    }
    /**
     * Import conversation history from JSON
     */
    importHistory(jsonData) {
        try {
            const imported = JSON.parse(jsonData);
            if (Array.isArray(imported)) {
                this.conversationHistory = imported;
                console.log(`[CONTEXT-MANAGER] Imported ${imported.length} conversation entries`);
            }
        }
        catch (error) {
            console.error(`[CONTEXT-MANAGER] Failed to import history: ${error}`);
        }
    }
}
exports.ConversationContextManager = ConversationContextManager;


/***/ }),

/***/ "./src/core/MemoryManager.ts":
/*!***********************************!*\
  !*** ./src/core/MemoryManager.ts ***!
  \***********************************/
/***/ ((__unused_webpack_module, exports, __webpack_require__) => {


/**
 * MemoryManager - Vector-based memory system for agents
 * Provides semantic search, pattern extraction, and learning capabilities
 */
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.MemoryManager = void 0;
const events_1 = __webpack_require__(/*! events */ "events");
const Memory_1 = __webpack_require__(/*! ../types/Memory */ "./src/types/Memory.ts");
class MemoryManager {
    constructor(options = {}) {
        this.memories = new Map();
        this.embeddings = new Map();
        this.patterns = new Map();
        this.clusters = [];
        this.codePatterns = new Map();
        this.architecturePatterns = new Map();
        this.learningEntries = [];
        this.memoryIndex = new Map();
        this.agentMemories = new Map();
        this.options = {
            maxMemories: options.maxMemories || 10000,
            similarityThreshold: options.similarityThreshold || 0.7,
            clusteringEnabled: options.clusteringEnabled ?? true,
            patternExtractionEnabled: options.patternExtractionEnabled ?? true,
            autoForget: options.autoForget ?? true,
            forgetThreshold: options.forgetThreshold || 0.3
        };
        this.eventBus = new events_1.EventEmitter();
        this.initializeIndexes();
    }
    initializeIndexes() {
        Object.values(Memory_1.MemoryType).forEach(type => {
            this.memoryIndex.set(type, new Set());
        });
    }
    /**
     * Store a new memory with automatic embedding generation
     */
    async store(agentId, content, type, metadata = {}) {
        const id = this.generateMemoryId();
        // Generate embedding (simplified - in real implementation, use actual embedding model)
        const embedding = await this.generateEmbedding(content);
        const memory = {
            id,
            agentId,
            timestamp: Date.now(),
            content,
            embedding,
            type,
            metadata: {
                ...metadata,
                accessCount: 0,
                lastAccessed: Date.now(),
                importance: metadata.importance || this.calculateImportance(content, type)
            }
        };
        // Store memory
        this.memories.set(id, memory);
        this.embeddings.set(id, embedding);
        // Update indexes
        this.memoryIndex.get(type).add(id);
        if (!this.agentMemories.has(agentId)) {
            this.agentMemories.set(agentId, new Set());
        }
        this.agentMemories.get(agentId).add(id);
        // Auto-forget old memories if limit exceeded
        if (this.options.autoForget && this.memories.size > this.options.maxMemories) {
            await this.forgetOldMemories();
        }
        // Extract patterns if enabled
        if (this.options.patternExtractionEnabled) {
            await this.extractPatterns();
        }
        // Update clusters if enabled
        if (this.options.clusteringEnabled) {
            await this.updateClusters();
        }
        this.eventBus.emit('memory-stored', memory);
        return id;
    }
    /**
     * Retrieve memories by semantic similarity
     */
    async search(query, options = {}) {
        const k = options.k || 10;
        const minSimilarity = options.minSimilarity || this.options.similarityThreshold;
        // Generate query embedding
        const queryEmbedding = await this.generateEmbedding(query);
        // Filter memories based on options
        let candidateMemories = Array.from(this.memories.values());
        if (options.type) {
            const typeMemories = this.memoryIndex.get(options.type);
            if (typeMemories) {
                candidateMemories = candidateMemories.filter(m => typeMemories.has(m.id));
            }
        }
        if (options.agentId) {
            const agentMems = this.agentMemories.get(options.agentId);
            if (agentMems) {
                candidateMemories = candidateMemories.filter(m => agentMems.has(m.id));
            }
        }
        // Calculate similarities
        const results = candidateMemories
            .map(memory => {
            const similarity = this.cosineSimilarity(queryEmbedding, memory.embedding || []);
            const relevance = this.calculateRelevance(memory, similarity);
            // Update access count
            memory.metadata.accessCount = (memory.metadata.accessCount || 0) + 1;
            memory.metadata.lastAccessed = Date.now();
            return {
                entry: memory,
                similarity,
                relevance
            };
        })
            .filter(result => result.similarity >= minSimilarity)
            .sort((a, b) => b.relevance - a.relevance)
            .slice(0, k);
        this.eventBus.emit('memory-searched', { query, results });
        return results;
    }
    /**
     * Get memory by ID
     */
    get(id) {
        const memory = this.memories.get(id);
        if (memory) {
            memory.metadata.accessCount = (memory.metadata.accessCount || 0) + 1;
            memory.metadata.lastAccessed = Date.now();
        }
        return memory;
    }
    /**
     * Update an existing memory
     */
    async update(id, content, metadata) {
        const memory = this.memories.get(id);
        if (!memory) {
            throw new Error(`Memory ${id} not found`);
        }
        memory.content = content;
        memory.embedding = await this.generateEmbedding(content);
        if (metadata) {
            memory.metadata = { ...memory.metadata, ...metadata };
        }
        this.embeddings.set(id, memory.embedding);
        this.eventBus.emit('memory-updated', memory);
    }
    /**
     * Delete a memory
     */
    delete(id) {
        const memory = this.memories.get(id);
        if (!memory)
            return false;
        // Remove from all indexes
        this.memories.delete(id);
        this.embeddings.delete(id);
        this.memoryIndex.get(memory.type)?.delete(id);
        this.agentMemories.get(memory.agentId)?.delete(id);
        this.eventBus.emit('memory-deleted', memory);
        return true;
    }
    /**
     * Store a code pattern for reuse
     */
    storeCodePattern(pattern) {
        this.codePatterns.set(pattern.id, pattern);
        this.eventBus.emit('pattern-stored', { type: 'code', pattern });
    }
    /**
     * Retrieve relevant code patterns
     */
    async getRelevantCodePatterns(context, language) {
        const patterns = Array.from(this.codePatterns.values());
        // Filter by language if specified
        let relevant = language
            ? patterns.filter(p => p.language === language)
            : patterns;
        // Sort by success rate and recency
        relevant.sort((a, b) => {
            const scoreA = a.successRate * (1 / (Date.now() - a.lastUsed));
            const scoreB = b.successRate * (1 / (Date.now() - b.lastUsed));
            return scoreB - scoreA;
        });
        return relevant.slice(0, 5);
    }
    /**
     * Store an architecture pattern
     */
    storeArchitecturePattern(pattern) {
        this.architecturePatterns.set(pattern.id, pattern);
        this.eventBus.emit('pattern-stored', { type: 'architecture', pattern });
    }
    /**
     * Get relevant architecture patterns
     */
    getRelevantArchitecturePatterns(useCase) {
        return Array.from(this.architecturePatterns.values())
            .filter(pattern => pattern.useCases.some(uc => uc.toLowerCase().includes(useCase.toLowerCase())));
    }
    /**
     * Store a learning entry
     */
    storeLearning(learning) {
        this.learningEntries.push(learning);
        this.eventBus.emit('learning-stored', learning);
    }
    /**
     * Get learnings relevant to current context
     */
    getRelevantLearnings(context, limit = 5) {
        // Simple keyword matching - in production, use semantic search
        const keywords = context.toLowerCase().split(' ');
        return this.learningEntries
            .filter(entry => keywords.some(keyword => entry.description.toLowerCase().includes(keyword)))
            .sort((a, b) => {
            // Prioritize high impact and recent learnings
            const scoreA = (a.impact === 'high' ? 3 : a.impact === 'medium' ? 2 : 1) *
                (1 / (Date.now() - a.timestamp));
            const scoreB = (b.impact === 'high' ? 3 : b.impact === 'medium' ? 2 : 1) *
                (1 / (Date.now() - b.timestamp));
            return scoreB - scoreA;
        })
            .slice(0, limit);
    }
    /**
     * Extract patterns from stored memories
     */
    async extractPatterns() {
        // Group similar memories
        const groups = this.groupSimilarMemories();
        groups.forEach((group, pattern) => {
            if (group.length >= 3) { // Need at least 3 occurrences to be a pattern
                const patternEntry = {
                    id: this.generateMemoryId(),
                    pattern,
                    frequency: group.length,
                    examples: group.slice(0, 5),
                    extractedAt: Date.now()
                };
                this.patterns.set(patternEntry.id, patternEntry);
            }
        });
    }
    /**
     * Group similar memories for pattern extraction
     */
    groupSimilarMemories() {
        const groups = new Map();
        const processed = new Set();
        this.memories.forEach((memory, id) => {
            if (processed.has(id))
                return;
            const similar = this.findSimilarMemories(memory, 0.8);
            if (similar.length >= 2) {
                const pattern = this.extractPatternSignature(memory);
                groups.set(pattern, [memory, ...similar]);
                similar.forEach(s => processed.add(s.id));
            }
        });
        return groups;
    }
    /**
     * Find memories similar to given memory
     */
    findSimilarMemories(memory, threshold) {
        const similar = [];
        this.memories.forEach((other, id) => {
            if (id === memory.id)
                return;
            const similarity = this.cosineSimilarity(memory.embedding || [], other.embedding || []);
            if (similarity >= threshold) {
                similar.push(other);
            }
        });
        return similar;
    }
    /**
     * Update memory clusters
     */
    async updateClusters() {
        // Simple k-means clustering
        const k = Math.min(10, Math.floor(this.memories.size / 50));
        if (k < 2)
            return;
        // Initialize centroids
        const centroids = this.initializeCentroids(k);
        // Iterate until convergence
        let iterations = 0;
        let changed = true;
        while (changed && iterations < 50) {
            const newClusters = centroids.map(centroid => ({
                centroid,
                members: [],
                coherence: 0
            }));
            // Assign memories to nearest centroid
            this.memories.forEach(memory => {
                if (!memory.embedding)
                    return;
                let nearestIdx = 0;
                let maxSim = -1;
                centroids.forEach((centroid, idx) => {
                    const sim = this.cosineSimilarity(memory.embedding, centroid);
                    if (sim > maxSim) {
                        maxSim = sim;
                        nearestIdx = idx;
                    }
                });
                newClusters[nearestIdx].members.push(memory);
            });
            // Update centroids
            changed = false;
            newClusters.forEach((cluster, idx) => {
                if (cluster.members.length > 0) {
                    const newCentroid = this.calculateCentroid(cluster.members);
                    if (!this.vectorsEqual(centroids[idx], newCentroid)) {
                        centroids[idx] = newCentroid;
                        changed = true;
                    }
                }
            });
            this.clusters = newClusters;
            iterations++;
        }
        // Calculate cluster coherence
        this.clusters.forEach(cluster => {
            cluster.coherence = this.calculateClusterCoherence(cluster);
        });
        this.eventBus.emit('clusters-updated', this.clusters);
    }
    /**
     * Forget old, unimportant memories
     */
    async forgetOldMemories() {
        const memoriesToForget = [];
        const now = Date.now();
        const oneWeek = 7 * 24 * 60 * 60 * 1000;
        this.memories.forEach((memory, id) => {
            // Calculate forgetting score
            const age = now - memory.timestamp;
            const accessFrequency = (memory.metadata.accessCount || 0) / (age / oneWeek);
            const importance = memory.metadata.importance || 0.5;
            const retentionScore = (accessFrequency * 0.4) + (importance * 0.6);
            if (retentionScore < this.options.forgetThreshold) {
                memoriesToForget.push(id);
            }
        });
        // Keep at least 50% of max capacity
        const maxToForget = Math.floor(this.memories.size - (this.options.maxMemories * 0.5));
        memoriesToForget.slice(0, maxToForget).forEach(id => {
            this.delete(id);
        });
        if (memoriesToForget.length > 0) {
            this.eventBus.emit('memories-forgotten', memoriesToForget.length);
        }
    }
    /**
     * Generate embedding for content (simplified - use real embedding model in production)
     */
    async generateEmbedding(content) {
        // Simplified embedding generation
        // In production, use OpenAI embeddings or similar
        const text = JSON.stringify(content).toLowerCase();
        const embedding = new Array(384).fill(0);
        // Simple hash-based embedding
        for (let i = 0; i < text.length; i++) {
            const idx = (text.charCodeAt(i) * (i + 1)) % 384;
            embedding[idx] += 1;
        }
        // Normalize
        const magnitude = Math.sqrt(embedding.reduce((sum, val) => sum + val * val, 0));
        return embedding.map(val => val / (magnitude || 1));
    }
    /**
     * Calculate cosine similarity between two vectors
     */
    cosineSimilarity(a, b) {
        if (a.length !== b.length || a.length === 0)
            return 0;
        let dotProduct = 0;
        let magnitudeA = 0;
        let magnitudeB = 0;
        for (let i = 0; i < a.length; i++) {
            dotProduct += a[i] * b[i];
            magnitudeA += a[i] * a[i];
            magnitudeB += b[i] * b[i];
        }
        magnitudeA = Math.sqrt(magnitudeA);
        magnitudeB = Math.sqrt(magnitudeB);
        if (magnitudeA === 0 || magnitudeB === 0)
            return 0;
        return dotProduct / (magnitudeA * magnitudeB);
    }
    /**
     * Calculate relevance score for a memory
     */
    calculateRelevance(memory, similarity) {
        const recency = 1 / (1 + (Date.now() - memory.timestamp) / (24 * 60 * 60 * 1000));
        const importance = memory.metadata.importance || 0.5;
        const accessFrequency = Math.min(1, (memory.metadata.accessCount || 0) / 100);
        return (similarity * 0.4) + (recency * 0.2) + (importance * 0.3) + (accessFrequency * 0.1);
    }
    /**
     * Calculate importance of content
     */
    calculateImportance(content, type) {
        // Simple heuristic - in production, use more sophisticated analysis
        if (type === Memory_1.MemoryType.PROCEDURAL)
            return 0.8;
        if (type === Memory_1.MemoryType.SEMANTIC)
            return 0.7;
        if (type === Memory_1.MemoryType.EPISODIC)
            return 0.5;
        return 0.3;
    }
    /**
     * Extract pattern signature from memory
     */
    extractPatternSignature(memory) {
        // Simplified pattern extraction
        const content = JSON.stringify(memory.content);
        return content.substring(0, 50);
    }
    /**
     * Initialize cluster centroids
     */
    initializeCentroids(k) {
        const centroids = [];
        const memories = Array.from(this.memories.values()).filter(m => m.embedding);
        for (let i = 0; i < k && i < memories.length; i++) {
            centroids.push([...memories[i].embedding]);
        }
        return centroids;
    }
    /**
     * Calculate centroid of cluster members
     */
    calculateCentroid(members) {
        if (members.length === 0 || !members[0].embedding)
            return [];
        const dim = members[0].embedding.length;
        const centroid = new Array(dim).fill(0);
        members.forEach(member => {
            if (member.embedding) {
                member.embedding.forEach((val, idx) => {
                    centroid[idx] += val;
                });
            }
        });
        return centroid.map(val => val / members.length);
    }
    /**
     * Calculate cluster coherence
     */
    calculateClusterCoherence(cluster) {
        if (cluster.members.length < 2)
            return 1;
        let totalSimilarity = 0;
        let comparisons = 0;
        for (let i = 0; i < cluster.members.length; i++) {
            for (let j = i + 1; j < cluster.members.length; j++) {
                if (cluster.members[i].embedding && cluster.members[j].embedding) {
                    totalSimilarity += this.cosineSimilarity(cluster.members[i].embedding, cluster.members[j].embedding);
                    comparisons++;
                }
            }
        }
        return comparisons > 0 ? totalSimilarity / comparisons : 0;
    }
    /**
     * Check if two vectors are equal
     */
    vectorsEqual(a, b) {
        if (a.length !== b.length)
            return false;
        return a.every((val, idx) => Math.abs(val - b[idx]) < 0.001);
    }
    /**
     * Generate unique memory ID
     */
    generateMemoryId() {
        return `mem_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    /**
     * Get memory statistics
     */
    getStats() {
        const stats = {
            totalMemories: this.memories.size,
            byType: new Map(),
            byAgent: new Map(),
            averageAccessCount: 0,
            mostAccessedMemories: [],
            memoryGrowthRate: 0,
            patternCount: this.patterns.size,
            clusterCount: this.clusters.length
        };
        // Count by type
        this.memoryIndex.forEach((ids, type) => {
            stats.byType.set(type, ids.size);
        });
        // Count by agent
        this.agentMemories.forEach((ids, agent) => {
            stats.byAgent.set(agent, ids.size);
        });
        // Calculate average access count and find most accessed
        let totalAccess = 0;
        const memoriesByAccess = Array.from(this.memories.values())
            .sort((a, b) => (b.metadata.accessCount || 0) - (a.metadata.accessCount || 0));
        memoriesByAccess.forEach(memory => {
            totalAccess += memory.metadata.accessCount || 0;
        });
        stats.averageAccessCount = totalAccess / (this.memories.size || 1);
        stats.mostAccessedMemories = memoriesByAccess.slice(0, 10);
        return stats;
    }
    /**
     * Export memories for persistence
     */
    export() {
        const exportData = {
            memories: Array.from(this.memories.entries()),
            patterns: Array.from(this.patterns.entries()),
            codePatterns: Array.from(this.codePatterns.entries()),
            architecturePatterns: Array.from(this.architecturePatterns.entries()),
            learningEntries: this.learningEntries,
            timestamp: Date.now()
        };
        return JSON.stringify(exportData);
    }
    /**
     * Import memories from persistence
     */
    import(data) {
        const importData = JSON.parse(data);
        // Clear existing data
        this.memories.clear();
        this.patterns.clear();
        this.codePatterns.clear();
        this.architecturePatterns.clear();
        this.learningEntries = [];
        // Import memories
        importData.memories.forEach(([id, memory]) => {
            this.memories.set(id, memory);
            if (memory.embedding) {
                this.embeddings.set(id, memory.embedding);
            }
        });
        // Import patterns
        importData.patterns.forEach(([id, pattern]) => {
            this.patterns.set(id, pattern);
        });
        // Import code patterns
        importData.codePatterns.forEach(([id, pattern]) => {
            this.codePatterns.set(id, pattern);
        });
        // Import architecture patterns
        importData.architecturePatterns.forEach(([id, pattern]) => {
            this.architecturePatterns.set(id, pattern);
        });
        // Import learning entries
        this.learningEntries = importData.learningEntries || [];
        // Rebuild indexes
        this.rebuildIndexes();
        this.eventBus.emit('memories-imported', {
            count: this.memories.size,
            timestamp: importData.timestamp
        });
    }
    /**
     * Rebuild indexes after import
     */
    rebuildIndexes() {
        this.memoryIndex.clear();
        this.agentMemories.clear();
        this.initializeIndexes();
        this.memories.forEach(memory => {
            this.memoryIndex.get(memory.type)?.add(memory.id);
            if (!this.agentMemories.has(memory.agentId)) {
                this.agentMemories.set(memory.agentId, new Set());
            }
            this.agentMemories.get(memory.agentId)?.add(memory.id);
        });
    }
}
exports.MemoryManager = MemoryManager;


/***/ }),

/***/ "./src/core/SharedContextManager.ts":
/*!******************************************!*\
  !*** ./src/core/SharedContextManager.ts ***!
  \******************************************/
/***/ ((__unused_webpack_module, exports, __webpack_require__) => {


/**
 * SharedContextManager - Manages shared context between agents for collaboration
 * Enables agents to share knowledge, decisions, and intermediate results in real-time
 */
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.SharedContextManager = void 0;
exports.getSharedContext = getSharedContext;
const events_1 = __webpack_require__(/*! events */ "events");
class SharedContextManager {
    constructor() {
        this.context = new Map();
        this.contextHistory = [];
        this.subscribers = new Map();
        this.locks = new Map(); // key -> agentId holding lock
        this.version = 0;
        this.eventBus = new events_1.EventEmitter();
        this.eventBus.setMaxListeners(50); // Support many agents
        this.initializeContext();
    }
    static getInstance() {
        if (!SharedContextManager.instance) {
            SharedContextManager.instance = new SharedContextManager();
        }
        return SharedContextManager.instance;
    }
    initializeContext() {
        // Initialize with default context structure
        this.context.set('projectStructure', {});
        this.context.set('architectureDecisions', new Map());
        this.context.set('codePatterns', new Map());
        this.context.set('researchFindings', new Map());
        this.context.set('validationResults', new Map());
        this.context.set('currentWorkflow', null);
        this.context.set('globalMemories', []);
        this.context.set('agentOutputs', new Map());
    }
    /**
     * Update context with new information
     */
    async updateContext(agentId, key, value, metadata) {
        // Check if key is locked by another agent
        const lockHolder = this.locks.get(key);
        if (lockHolder && lockHolder !== agentId) {
            throw new Error(`Context key '${key}' is locked by agent ${lockHolder}`);
        }
        const update = {
            agentId,
            timestamp: Date.now(),
            key,
            value,
            metadata: {
                ...metadata,
                version: ++this.version
            }
        };
        // Update the context
        this.context.set(key, value);
        // Store in history for replay/debugging
        this.contextHistory.push(update);
        // Notify all subscribers
        await this.notifySubscribers(update);
        // Emit event for async listeners
        this.eventBus.emit('context-update', update);
    }
    /**
     * Get current context value
     */
    getContext(key) {
        if (key) {
            return this.context.get(key);
        }
        // Return entire context as object
        const contextObj = {};
        this.context.forEach((value, key) => {
            contextObj[key] = value;
        });
        return contextObj;
    }
    /**
     * Get context with memory of past updates
     */
    getContextWithHistory(key, limit = 10) {
        return this.contextHistory
            .filter(update => update.key === key)
            .slice(-limit);
    }
    /**
     * Subscribe to context updates
     */
    subscribe(agentId, callback, filter) {
        const subscriber = {
            agentId,
            callback,
            filter
        };
        if (!this.subscribers.has(agentId)) {
            this.subscribers.set(agentId, []);
        }
        this.subscribers.get(agentId).push(subscriber);
    }
    /**
     * Unsubscribe from context updates
     */
    unsubscribe(agentId) {
        this.subscribers.delete(agentId);
    }
    /**
     * Notify all subscribers of a context update
     */
    async notifySubscribers(update) {
        const promises = [];
        this.subscribers.forEach((subscriberList) => {
            subscriberList.forEach(subscriber => {
                // Skip the agent that made the update
                if (subscriber.agentId === update.agentId) {
                    return;
                }
                // Apply filter if provided
                if (subscriber.filter && !subscriber.filter(update)) {
                    return;
                }
                // Notify subscriber asynchronously
                promises.push(Promise.resolve(subscriber.callback(update)).catch(err => {
                    console.error(`Error notifying subscriber ${subscriber.agentId}:`, err);
                }));
            });
        });
        await Promise.all(promises);
    }
    /**
     * Acquire a lock on a context key (for atomic updates)
     */
    async acquireLock(agentId, key, timeout = 5000) {
        const startTime = Date.now();
        while (this.locks.has(key) && this.locks.get(key) !== agentId) {
            if (Date.now() - startTime > timeout) {
                throw new Error(`Timeout acquiring lock for key '${key}'`);
            }
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        this.locks.set(key, agentId);
    }
    /**
     * Release a lock on a context key
     */
    releaseLock(agentId, key) {
        if (this.locks.get(key) === agentId) {
            this.locks.delete(key);
        }
    }
    /**
     * Merge context from multiple agents (for conflict resolution)
     */
    async mergeContext(updates, resolver) {
        const grouped = new Map();
        // Group updates by key
        updates.forEach(update => {
            if (!grouped.has(update.key)) {
                grouped.set(update.key, []);
            }
            grouped.get(update.key).push(update);
        });
        // Process each key
        for (const [key, keyUpdates] of grouped) {
            if (keyUpdates.length === 1) {
                // No conflict, apply directly
                await this.updateContext(keyUpdates[0].agentId, key, keyUpdates[0].value, keyUpdates[0].metadata);
            }
            else {
                // Conflict - use resolver or last-write-wins
                const resolvedValue = resolver ? resolver(keyUpdates) : keyUpdates[keyUpdates.length - 1].value;
                await this.updateContext('system', key, resolvedValue, { resolved: true });
            }
        }
    }
    /**
     * Create a snapshot of current context (for checkpointing)
     */
    createSnapshot() {
        return {
            version: this.version,
            timestamp: Date.now(),
            context: new Map(this.context)
        };
    }
    /**
     * Restore context from snapshot
     */
    restoreSnapshot(snapshot) {
        this.context = new Map(snapshot.context);
        this.version = snapshot.version;
        this.eventBus.emit('context-restored', snapshot);
    }
    /**
     * Clear context (for new sessions)
     */
    clearContext() {
        this.context.clear();
        this.contextHistory = [];
        this.locks.clear();
        this.version = 0;
        this.initializeContext();
        this.eventBus.emit('context-cleared');
    }
    /**
     * Get agents currently working on the context
     */
    getActiveAgents() {
        const activeAgents = new Set();
        // Get agents from recent updates
        const recentTime = Date.now() - 60000; // Last minute
        this.contextHistory
            .filter(update => update.timestamp > recentTime)
            .forEach(update => activeAgents.add(update.agentId));
        return Array.from(activeAgents);
    }
    /**
     * Get collaboration insights
     */
    getCollaborationMetrics() {
        const metrics = {
            totalUpdates: this.contextHistory.length,
            activeAgents: this.getActiveAgents().length,
            contextKeys: this.context.size,
            lockedKeys: this.locks.size,
            version: this.version
        };
        // Calculate update frequency by agent
        const agentUpdates = new Map();
        this.contextHistory.forEach(update => {
            agentUpdates.set(update.agentId, (agentUpdates.get(update.agentId) || 0) + 1);
        });
        metrics.agentActivity = Object.fromEntries(agentUpdates);
        return metrics;
    }
}
exports.SharedContextManager = SharedContextManager;
// Export singleton instance getter
function getSharedContext() {
    return SharedContextManager.getInstance();
}


/***/ }),

/***/ "./src/core/VSCodeMasterDispatcher.ts":
/*!********************************************!*\
  !*** ./src/core/VSCodeMasterDispatcher.ts ***!
  \********************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {


var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.VSCodeMasterDispatcher = void 0;
/**
 * VS Code Master Dispatcher - Orchestrates AI agents in VS Code context
 * Adapted from CLI MasterDispatcher for VS Code extension environment
 */
const vscode = __importStar(__webpack_require__(/*! vscode */ "vscode"));
const ConversationContextManager_1 = __webpack_require__(/*! ./ConversationContextManager */ "./src/core/ConversationContextManager.ts");
class VSCodeMasterDispatcher {
    constructor(context) {
        this.agents = new Map();
        this.projectTypes = new Map();
        this.intentPatterns = new Map();
        this.context = context;
        this.contextManager = ConversationContextManager_1.ConversationContextManager.getInstance();
        this.initializeProjectTypes();
        this.initializeIntentPatterns();
    }
    /**
     * Process a task request and route to appropriate agents
     */
    async processRequest(request) {
        console.log(`\n🚦 [DISPATCHER] ====== processRequest called ======`);
        console.log(`🚦 [DISPATCHER] request.command: '${request.command}'`);
        console.log(`🚦 [DISPATCHER] request.command type: ${typeof request.command}`);
        console.log(`🚦 [DISPATCHER] request.prompt: "${request.prompt?.substring(0, 50)}..."`);
        console.log(`🚦 [DISPATCHER] Command check results:`);
        console.log(`🚦 [DISPATCHER]   - request.command exists: ${!!request.command}`);
        console.log(`🚦 [DISPATCHER]   - request.command !== 'auto': ${request.command !== 'auto'}`);
        console.log(`🚦 [DISPATCHER]   - request.command !== 'orchestrator': ${request.command !== 'orchestrator'}`);
        try {
            // Get workspace context
            const workspaceContext = await this.getWorkspaceContext();
            // Check if a specific agent was requested (single agent mode)
            if (request.command && request.command !== 'auto' && request.command !== 'orchestrator') {
                console.log(`🎯 [DISPATCHER] ✅ SINGLE AGENT MODE ACTIVATED`);
                console.log(`🎯 [DISPATCHER] Single agent mode: Using only ${request.command}`);
                // Create a single-step workflow for the specific agent
                const workflow = [{
                        id: 'execute',
                        agent: request.command,
                        description: `Execute with ${request.command}`
                    }];
                console.log(`🎯 [DISPATCHER] Created single-step workflow:`);
                console.log(`🎯 [DISPATCHER]   - Steps count: ${workflow.length}`);
                console.log(`🎯 [DISPATCHER]   - Step[0]: id='${workflow[0].id}', agent='${workflow[0].agent}'`);
                // Execute single agent
                const result = await this.executeWorkflow(workflow, {
                    ...request,
                    context: workspaceContext,
                    projectType: request.projectType || 'generic'
                });
                return result;
            }
            // Auto mode: Detect intent and create multi-step workflow
            console.log(`🎯 [DISPATCHER] ⚠️ AUTO MODE ACTIVATED (not single agent)`);
            console.log(`🎯 [DISPATCHER] Auto mode: Creating workflow based on intent`);
            // Detect intent and project type
            const intent = await this.detectIntent(request.prompt);
            const projectType = request.projectType || await this.detectProjectType(workspaceContext);
            // Create workflow
            const workflow = this.createWorkflow(intent, projectType);
            // Execute workflow
            const result = await this.executeWorkflow(workflow, {
                ...request,
                context: workspaceContext,
                projectType
            });
            return result;
        }
        catch (error) {
            return {
                status: 'error',
                content: `Error processing request: ${error.message}`,
                metadata: { error: error.message }
            };
        }
    }
    /**
     * Detect user intent from prompt
     */
    async detectIntent(prompt) {
        const lowerPrompt = prompt.toLowerCase();
        // Check if this is a question rather than a task
        const isQuestion = /^(what|which|how|was|welche|wie|wer|wo|wann|warum|show|list|explain)/i.test(prompt);
        const isImplementation = /(implement|create|build|write|code|develop)/i.test(prompt);
        // Query patterns - questions about the system or information
        if (isQuestion && !isImplementation) {
            // Questions about the system itself, agents, or instructions
            if (this.matchesPatterns(lowerPrompt, ['instruction', 'agent', 'system', 'available', 'haben wir', 'gibt es', 'welche'])) {
                return { type: 'query', confidence: 0.95, agent: 'orchestrator' };
            }
            // Architecture questions
            if (this.matchesPatterns(lowerPrompt, ['architecture', 'design', 'pattern', 'structure'])) {
                return { type: 'query', confidence: 0.9, agent: 'architect' };
            }
            // Research questions
            if (this.matchesPatterns(lowerPrompt, ['research', 'find', 'information', 'latest'])) {
                return { type: 'query', confidence: 0.85, agent: 'research' };
            }
            // Default query
            return { type: 'query', confidence: 0.7, agent: 'orchestrator' };
        }
        // Architecture patterns (for actual design tasks)
        if (this.matchesPatterns(lowerPrompt, ['design', 'architecture', 'system', 'plan', 'structure']) && isImplementation) {
            return { type: 'architecture', confidence: 0.9, agent: 'architect' };
        }
        // Implementation patterns
        if (this.matchesPatterns(lowerPrompt, ['implement', 'code', 'create', 'build', 'develop'])) {
            return { type: 'implementation', confidence: 0.85, agent: 'codesmith' };
        }
        // Documentation patterns
        if (this.matchesPatterns(lowerPrompt, ['document', 'readme', 'docs', 'explain', 'tutorial'])) {
            return { type: 'documentation', confidence: 0.9, agent: 'docu' };
        }
        // Review patterns
        if (this.matchesPatterns(lowerPrompt, ['review', 'check', 'analyze', 'audit', 'security'])) {
            return { type: 'review', confidence: 0.85, agent: 'reviewer' };
        }
        // Debug/Fix patterns
        if (this.matchesPatterns(lowerPrompt, ['fix', 'debug', 'error', 'bug', 'problem', 'issue'])) {
            return { type: 'debug', confidence: 0.9, agent: 'fixer' };
        }
        // Trading patterns
        if (this.matchesPatterns(lowerPrompt, ['trading', 'strategy', 'backtest', 'ron', 'market', 'stock'])) {
            return { type: 'trading', confidence: 0.95, agent: 'tradestrat' };
        }
        // Research patterns
        if (this.matchesPatterns(lowerPrompt, ['research', 'search', 'find', 'information', 'latest'])) {
            return { type: 'research', confidence: 0.8, agent: 'research' };
        }
        // Default - if we can't determine, treat as a query
        return { type: 'query', confidence: 0.5, agent: 'orchestrator' };
    }
    /**
     * Detect project type from workspace context
     */
    async detectProjectType(context) {
        if (!context?.workspaceRoots || context.workspaceRoots.length === 0) {
            return 'generic_software';
        }
        const workspaceRoot = context.workspaceRoots[0];
        try {
            // Check for package.json
            const packageJsonUri = vscode.Uri.joinPath(workspaceRoot.uri, 'package.json');
            try {
                const packageJsonContent = await vscode.workspace.fs.readFile(packageJsonUri);
                const packageJson = JSON.parse(packageJsonContent.toString());
                // Trading system indicators
                if (packageJson.dependencies?.['streamlit'] ||
                    packageJson.dependencies?.['yfinance'] ||
                    packageJson.dependencies?.['pandas']) {
                    return 'trading_system';
                }
                // Web API indicators
                if (packageJson.dependencies?.['fastapi'] ||
                    packageJson.dependencies?.['express'] ||
                    packageJson.dependencies?.['flask']) {
                    return 'web_api';
                }
                // React/Frontend indicators
                if (packageJson.dependencies?.['react'] ||
                    packageJson.dependencies?.['vue'] ||
                    packageJson.dependencies?.['angular']) {
                    return 'web_frontend';
                }
            }
            catch (error) {
                // package.json not found or invalid
            }
            // Check for requirements.txt (Python)
            const requirementsUri = vscode.Uri.joinPath(workspaceRoot.uri, 'requirements.txt');
            try {
                const requirementsContent = await vscode.workspace.fs.readFile(requirementsUri);
                const requirements = requirementsContent.toString();
                if (requirements.includes('yfinance') ||
                    requirements.includes('pandas') ||
                    requirements.includes('streamlit')) {
                    return 'trading_system';
                }
                if (requirements.includes('fastapi') ||
                    requirements.includes('flask') ||
                    requirements.includes('django')) {
                    return 'web_api';
                }
            }
            catch (error) {
                // requirements.txt not found
            }
            // Check for specific files
            const files = await vscode.workspace.findFiles('**/*.{py,js,ts,jsx,tsx}', '**/node_modules/**', 50);
            const filenames = files.map(uri => uri.fsPath.toLowerCase());
            if (filenames.some(f => f.includes('strategy') || f.includes('trading') || f.includes('backtest'))) {
                return 'trading_system';
            }
            if (filenames.some(f => f.includes('api') || f.includes('server') || f.includes('endpoint'))) {
                return 'web_api';
            }
        }
        catch (error) {
            console.error('Error detecting project type:', error);
        }
        return 'generic_software';
    }
    /**
     * Create workflow based on intent and project type
     * Note: Uses only available agents (architect, codesmith, tradestrat, research, richter, orchestrator)
     */
    createWorkflow(intent, projectType) {
        const projectDef = this.projectTypes.get(projectType);
        // Base workflow based on intent
        let workflow = [];
        switch (intent.type) {
            case 'query':
                // For queries, just use a single step with the appropriate agent
                workflow = [
                    { id: 'answer', agent: intent.agent, description: 'Answer query directly' }
                ];
                break;
            case 'architecture':
                workflow = [
                    { id: 'analyze', agent: 'architect', description: 'Analyze requirements and context' },
                    { id: 'design', agent: 'architect', description: 'Create architecture design' },
                    { id: 'review', agent: 'codesmith', description: 'Review architecture for best practices' } // Using codesmith instead of missing 'reviewer'
                ];
                break;
            case 'implementation':
                workflow = [
                    { id: 'plan', agent: 'architect', description: 'Plan implementation approach' },
                    { id: 'implement', agent: 'codesmith', description: 'Implement the solution' },
                    { id: 'test', agent: 'codesmith', description: 'Create tests' },
                    { id: 'review', agent: 'codesmith', description: 'Review implementation' } // Using codesmith instead of missing 'reviewer'
                ];
                break;
            case 'trading':
                workflow = [
                    { id: 'strategy_design', agent: 'tradestrat', description: 'Design trading strategy' },
                    { id: 'implement', agent: 'codesmith', description: 'Implement strategy code' },
                    { id: 'backtest', agent: 'tradestrat', description: 'Create backtesting framework' },
                    { id: 'review', agent: 'tradestrat', description: 'Review for trading best practices' } // Using tradestrat instead of missing 'reviewer'
                ];
                break;
            case 'debug':
                workflow = [
                    { id: 'analyze', agent: 'codesmith', description: 'Analyze the problem' }, // Using codesmith instead of missing 'fixer'
                    { id: 'fix', agent: 'codesmith', description: 'Implement fix' }, // Using codesmith instead of missing 'fixer'
                    { id: 'test', agent: 'codesmith', description: 'Test the fix' }
                ];
                break;
            case 'documentation':
                workflow = [
                    { id: 'analyze', agent: 'architect', description: 'Analyze documentation requirements' },
                    { id: 'document', agent: 'codesmith', description: 'Generate documentation' } // Using codesmith instead of missing 'docu'
                ];
                break;
            case 'research':
                workflow = [
                    { id: 'research', agent: 'research', description: 'Research and gather information' }
                ];
                break;
            default:
                workflow = [
                    { id: 'execute', agent: intent.agent || 'codesmith', description: 'Execute task' }
                ];
        }
        // Apply project-specific modifications ONLY if NOT a query
        // Queries should always be single-step and not modified
        if (intent.type !== 'query' && projectDef?.workflow) {
            // Merge project-specific workflow steps
            workflow = [...workflow, ...projectDef.workflow.filter(step => !workflow.some(w => w.id === step.id))];
        }
        return workflow;
    }
    /**
     * Execute workflow steps
     */
    async executeWorkflow(workflow, request) {
        const results = [];
        let finalResult = {
            status: 'success',
            content: '',
            suggestions: [],
            references: []
        };
        console.log(`🚀 [WORKFLOW] Starting workflow execution with ${workflow.length} steps`);
        console.log(`🚀 [WORKFLOW] Workflow steps: ${workflow.map(s => `${s.id}:${s.agent}`).join(' → ')}`);
        console.log(`🚀 [WORKFLOW] Current agent registry size: ${this.agents.size}`);
        console.log(`🚀 [WORKFLOW] Current registered agents: [${Array.from(this.agents.keys()).join(', ')}]`);
        for (const step of workflow) {
            try {
                console.log(`\n🔍 [WORKFLOW STEP] ========================================`);
                console.log(`🔍 [WORKFLOW STEP] Executing: ${step.description}`);
                console.log(`🔍 [WORKFLOW STEP] Looking for agent: "${step.agent}"`);
                console.log(`🔍 [WORKFLOW STEP] Agent registry has ${this.agents.size} agents`);
                console.log(`🔍 [WORKFLOW STEP] Available agents: [${Array.from(this.agents.keys()).join(', ')}]`);
                // Send partial response for workflow progress
                if (request.onPartialResponse) {
                    const stepIndex = workflow.indexOf(step) + 1;
                    request.onPartialResponse(`\n🔄 **Step ${stepIndex}/${workflow.length}**: @${step.agent} - ${step.description}\n\n`);
                }
                let agent = this.agents.get(step.agent);
                console.log(`🔍 [WORKFLOW STEP] Direct lookup for "${step.agent}": ${agent ? 'FOUND' : 'NOT FOUND'}`);
                // Try alternative agent mappings if direct lookup fails
                if (!agent) {
                    const agentMappings = {
                        'architect': ['architect', 'ki-autoagent.architect'],
                        'codesmith': ['codesmith', 'ki-autoagent.codesmith'],
                        'tradestrat': ['tradestrat', 'ki-autoagent.tradestrat'],
                        'research': ['research', 'ki-autoagent.research'],
                        'richter': ['richter', 'ki-autoagent.richter'],
                        'orchestrator': ['orchestrator', 'ki-autoagent.orchestrator']
                    };
                    // Try all possible names for this agent
                    const possibleNames = agentMappings[step.agent];
                    if (possibleNames) {
                        for (const possibleName of possibleNames) {
                            agent = this.agents.get(possibleName);
                            if (agent) {
                                console.log(`[DEBUG] Found agent ${step.agent} under name: ${possibleName}`);
                                break;
                            }
                        }
                    }
                }
                if (!agent) {
                    console.error(`[DEBUG] Agent ${step.agent} not found! Available agents: ${Array.from(this.agents.keys()).join(', ')}`);
                    // TEMPORARY FALLBACK: Use orchestrator for missing agents
                    agent = this.agents.get('orchestrator') || this.agents.get('ki-autoagent.orchestrator');
                    if (agent) {
                        console.warn(`[DEBUG] Using orchestrator as fallback for ${step.agent}`);
                    }
                    else {
                        const errorMsg = `Agent ${step.agent} not found. Registered agents: [${Array.from(this.agents.keys()).join(', ')}]`;
                        console.error(`❌ [WORKFLOW STEP] ${errorMsg}`);
                        throw new Error(errorMsg);
                    }
                }
                console.log(`[DEBUG] Found agent: ${step.agent}, executing step: ${step.description}`);
                console.log(`[DEBUG] Passing ${results.length} previous results to agent`);
                // Get recent conversation history from context manager
                const recentHistory = this.contextManager.getFormattedContext(5);
                // Create enriched request with accumulated context
                const enrichedRequest = {
                    ...request,
                    prompt: request.prompt,
                    conversationHistory: results.map(r => ({
                        agent: r.metadata?.agent || 'unknown',
                        step: r.metadata?.step || 'unknown',
                        content: r.content
                    })),
                    globalContext: recentHistory
                };
                const stepResult = await agent.executeStep(step, enrichedRequest, results);
                results.push(stepResult);
                // Save to conversation history
                this.contextManager.addEntry({
                    timestamp: new Date().toISOString(),
                    agent: step.agent,
                    step: step.id,
                    input: request.prompt,
                    output: stepResult.content,
                    metadata: stepResult.metadata
                });
                // Log inter-agent communication
                console.log(`[INTER-AGENT] ${step.agent} completed step '${step.id}' with ${stepResult.content.length} chars`);
                console.log(`[INTER-AGENT] Result saved to conversation history`);
                console.log(`[INTER-AGENT] Result will be passed to next agent in workflow`);
                // Send partial response for step completion
                if (request.onPartialResponse) {
                    const preview = stepResult.content.substring(0, 200);
                    request.onPartialResponse(`✅ Completed: ${preview}${stepResult.content.length > 200 ? '...' : ''}\n\n`);
                }
                // For single-step workflows (like queries), use the content directly
                // For multi-step workflows, accumulate results
                if (workflow.length === 1) {
                    finalResult.content = stepResult.content;
                    finalResult.metadata = { ...finalResult.metadata, ...stepResult.metadata, agent: step.agent };
                }
                else {
                    finalResult.content += `## ${step.description}\n\n${stepResult.content}\n\n`;
                }
                finalResult.suggestions?.push(...(stepResult.suggestions || []));
                finalResult.references?.push(...(stepResult.references || []));
                if (stepResult.status === 'error') {
                    finalResult.status = 'partial_success';
                }
            }
            catch (error) {
                const errorMessage = error.message || error;
                console.error(`❌ Error executing step ${step.id} (${step.agent}): ${errorMessage}`);
                finalResult.status = 'error';
                finalResult.content += `❌ Error in ${step.description}: ${errorMessage}\n\n`;
                // Add helpful error message for API issues
                if (errorMessage.includes('not found')) {
                    finalResult.content += `**Troubleshooting:**\n`;
                    finalResult.content += `- Registered agents: [${Array.from(this.agents.keys()).join(', ')}]\n`;
                    finalResult.content += `- Ensure all agents are properly initialized\n\n`;
                }
                else if (errorMessage.includes('quota') || errorMessage.includes('API')) {
                    finalResult.content += `**API Configuration Required:**\n`;
                    finalResult.content += `1. Open VS Code Settings (Cmd+,)\n`;
                    finalResult.content += `2. Search for "KI AutoAgent"\n`;
                    finalResult.content += `3. Configure your API keys:\n`;
                    finalResult.content += `   - OpenAI API Key\n`;
                    finalResult.content += `   - Anthropic API Key\n`;
                    finalResult.content += `   - Perplexity API Key\n\n`;
                }
                else if (errorMessage.includes('Claude Web Proxy')) {
                    finalResult.content += `**Claude Web Proxy Required:**\n`;
                    finalResult.content += `The Claude Web Proxy server is not running.\n`;
                    finalResult.content += `Please start the proxy server to use Claude models.\n\n`;
                }
            }
        }
        return finalResult;
    }
    /**
     * Get current workspace context
     */
    async getWorkspaceContext() {
        const activeEditor = vscode.window.activeTextEditor;
        const workspaceRoots = vscode.workspace.workspaceFolders;
        const openDocuments = vscode.workspace.textDocuments;
        let selectedText = '';
        let currentFile = '';
        if (activeEditor) {
            currentFile = activeEditor.document.fileName;
            if (!activeEditor.selection.isEmpty) {
                selectedText = activeEditor.document.getText(activeEditor.selection);
            }
        }
        return {
            activeEditor,
            workspaceRoots,
            openDocuments,
            selectedText,
            currentFile
        };
    }
    /**
     * Register an agent
     */
    registerAgent(agentId, agent) {
        console.log(`🔧 [DISPATCHER] Registering agent: ${agentId}`);
        console.log(`🔧 [DISPATCHER] Agent object type: ${typeof agent}`);
        console.log(`🔧 [DISPATCHER] Agent has executeStep: ${typeof agent.executeStep}`);
        console.log(`🔧 [DISPATCHER] Agent config: ${JSON.stringify(agent.config || 'NO CONFIG')}`);
        this.agents.set(agentId, agent);
        console.log(`🔧 [DISPATCHER] Total registered agents: ${this.agents.size}`);
        console.log(`🔧 [DISPATCHER] All registered agent IDs: [${Array.from(this.agents.keys()).join(', ')}]`);
        console.log(`🔧 [DISPATCHER] Agent storage verification - Can retrieve ${agentId}: ${this.agents.has(agentId) ? 'YES' : 'NO'}`);
        // Test immediate retrieval
        const testRetrieve = this.agents.get(agentId);
        console.log(`🔧 [DISPATCHER] Immediate retrieval test for ${agentId}: ${testRetrieve ? 'SUCCESS' : 'FAILED'}`);
    }
    /**
     * Get list of registered agent IDs
     */
    getRegisteredAgents() {
        return Array.from(this.agents.keys());
    }
    /**
     * Get agent statistics
     */
    async getAgentStats() {
        const stats = {};
        for (const [agentId, agent] of this.agents) {
            if (agent.getStats) {
                stats[agentId] = await agent.getStats();
            }
        }
        return stats;
    }
    matchesPatterns(text, patterns) {
        return patterns.some(pattern => text.includes(pattern));
    }
    initializeProjectTypes() {
        // Trading System
        this.projectTypes.set('trading_system', {
            name: 'Trading System',
            patterns: ['streamlit', 'yfinance', 'pandas', 'trading', 'strategy'],
            qualityGates: ['engine_parity', 'trading_validation', 'ron_compliance'],
            workflow: [
                { id: 'strategy_validation', agent: 'tradestrat', description: 'Validate trading strategy logic' },
                { id: 'risk_analysis', agent: 'tradestrat', description: 'Analyze risk management' }
            ],
            primaryAgent: 'tradestrat'
        });
        // Web API
        this.projectTypes.set('web_api', {
            name: 'Web API',
            patterns: ['fastapi', 'flask', 'express', 'api'],
            qualityGates: ['security_review', 'performance_check', 'api_design'],
            workflow: [
                { id: 'security_review', agent: 'codesmith', description: 'Security vulnerability check' }, // Using codesmith instead of missing 'reviewer'
                { id: 'api_documentation', agent: 'codesmith', description: 'Generate API documentation' } // Using codesmith instead of missing 'docu'
            ],
            primaryAgent: 'codesmith'
        });
        // Generic Software
        this.projectTypes.set('generic_software', {
            name: 'Generic Software',
            patterns: [],
            qualityGates: ['code_quality', 'performance', 'security'],
            workflow: [],
            primaryAgent: 'codesmith'
        });
    }
    initializeIntentPatterns() {
        // Define regex patterns for more sophisticated intent detection
        this.intentPatterns.set('architecture', [
            /\b(design|architect|structure|system)\b/i,
            /\b(plan|planning|blueprint)\b/i
        ]);
        this.intentPatterns.set('implementation', [
            /\b(implement|code|create|build|develop)\b/i,
            /\b(function|class|method|api)\b/i
        ]);
        // Add more patterns as needed
    }
}
exports.VSCodeMasterDispatcher = VSCodeMasterDispatcher;


/***/ }),

/***/ "./src/core/WorkflowEngine.ts":
/*!************************************!*\
  !*** ./src/core/WorkflowEngine.ts ***!
  \************************************/
/***/ ((__unused_webpack_module, exports, __webpack_require__) => {


/**
 * WorkflowEngine - Graph-based workflow execution for complex task orchestration
 * Enables parallel execution, conditional flows, and dynamic plan adjustment
 */
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.WorkflowEngine = void 0;
const events_1 = __webpack_require__(/*! events */ "events");
class WorkflowEngine {
    constructor() {
        this.workflows = new Map();
        this.executors = new Map();
        this.templates = new Map();
        this.eventBus = new events_1.EventEmitter();
        this.initializeTemplates();
    }
    /**
     * Create a new workflow
     */
    createWorkflow(name, template) {
        const id = this.generateWorkflowId();
        const workflow = {
            id,
            name,
            nodes: new Map(),
            edges: [],
            startNode: '',
            endNodes: [],
            context: new Map(),
            checkpoints: [],
            status: {
                state: 'pending',
                currentNodes: [],
                completedNodes: [],
                failedNodes: []
            }
        };
        // Apply template if provided
        if (template && this.templates.has(template)) {
            this.applyTemplate(workflow, this.templates.get(template));
        }
        this.workflows.set(id, workflow);
        this.eventBus.emit('workflow-created', workflow);
        return workflow;
    }
    /**
     * Add a node to the workflow
     */
    addNode(workflowId, node) {
        const workflow = this.workflows.get(workflowId);
        if (!workflow) {
            throw new Error(`Workflow ${workflowId} not found`);
        }
        workflow.nodes.set(node.id, node);
        // Set as start node if it's the first
        if (!workflow.startNode) {
            workflow.startNode = node.id;
        }
        this.eventBus.emit('node-added', { workflowId, node });
    }
    /**
     * Add an edge between nodes
     */
    addEdge(workflowId, edge) {
        const workflow = this.workflows.get(workflowId);
        if (!workflow) {
            throw new Error(`Workflow ${workflowId} not found`);
        }
        // Validate nodes exist
        if (!workflow.nodes.has(edge.from) || !workflow.nodes.has(edge.to)) {
            throw new Error(`Invalid edge: nodes not found`);
        }
        workflow.edges.push(edge);
        // Update node children
        const fromNode = workflow.nodes.get(edge.from);
        if (!fromNode.children) {
            fromNode.children = [];
        }
        fromNode.children.push(edge.to);
        // Update node dependencies
        const toNode = workflow.nodes.get(edge.to);
        if (!toNode.dependencies) {
            toNode.dependencies = [];
        }
        toNode.dependencies.push(edge.from);
        this.eventBus.emit('edge-added', { workflowId, edge });
    }
    /**
     * Create execution plan for the workflow
     */
    createExecutionPlan(workflowId) {
        const workflow = this.workflows.get(workflowId);
        if (!workflow) {
            throw new Error(`Workflow ${workflowId} not found`);
        }
        // Topological sort to find execution order
        const sortedNodes = this.topologicalSort(workflow);
        // Group nodes into stages based on dependencies
        const stages = this.groupIntoStages(workflow, sortedNodes);
        // Calculate critical path
        const criticalPath = this.findCriticalPath(workflow);
        // Estimate durations
        const estimatedDuration = this.estimateDuration(stages);
        const parallelism = this.calculateParallelism(stages);
        return {
            stages,
            estimatedDuration,
            parallelism,
            criticalPath
        };
    }
    /**
     * Execute a workflow
     */
    async execute(workflowId, context) {
        const workflow = this.workflows.get(workflowId);
        if (!workflow) {
            throw new Error(`Workflow ${workflowId} not found`);
        }
        // Initialize context
        if (context) {
            workflow.context = new Map([...workflow.context, ...context]);
        }
        // Create executor
        const executor = new WorkflowExecutor(workflow, this.eventBus);
        this.executors.set(workflowId, executor);
        // Update status
        workflow.status.state = 'running';
        workflow.status.startTime = Date.now();
        this.eventBus.emit('workflow-started', workflow);
        try {
            // Create execution plan
            const plan = this.createExecutionPlan(workflowId);
            // Execute plan
            const results = await executor.execute(plan);
            // Update status
            workflow.status.state = 'completed';
            workflow.status.endTime = Date.now();
            this.eventBus.emit('workflow-completed', { workflow, results });
            return results;
        }
        catch (error) {
            workflow.status.state = 'failed';
            workflow.status.error = error instanceof Error ? error.message : String(error);
            workflow.status.endTime = Date.now();
            this.eventBus.emit('workflow-failed', { workflow, error });
            throw error;
        }
        finally {
            this.executors.delete(workflowId);
        }
    }
    /**
     * Pause a running workflow
     */
    pause(workflowId) {
        const executor = this.executors.get(workflowId);
        if (executor) {
            executor.pause();
        }
    }
    /**
     * Resume a paused workflow
     */
    resume(workflowId) {
        const executor = this.executors.get(workflowId);
        if (executor) {
            executor.resume();
        }
    }
    /**
     * Cancel a workflow
     */
    cancel(workflowId) {
        const executor = this.executors.get(workflowId);
        if (executor) {
            executor.cancel();
        }
    }
    /**
     * Create a checkpoint
     */
    createCheckpoint(workflowId, nodeId) {
        const workflow = this.workflows.get(workflowId);
        if (!workflow)
            return;
        const checkpoint = {
            id: this.generateCheckpointId(),
            nodeId,
            timestamp: Date.now(),
            context: new Map(workflow.context),
            results: new Map()
        };
        workflow.checkpoints.push(checkpoint);
        this.eventBus.emit('checkpoint-created', { workflowId, checkpoint });
    }
    /**
     * Restore from checkpoint
     */
    restoreFromCheckpoint(workflowId, checkpointId) {
        const workflow = this.workflows.get(workflowId);
        if (!workflow)
            return;
        const checkpoint = workflow.checkpoints.find(cp => cp.id === checkpointId);
        if (!checkpoint) {
            throw new Error(`Checkpoint ${checkpointId} not found`);
        }
        // Restore context
        workflow.context = new Map(checkpoint.context);
        // Reset status to continue from checkpoint
        workflow.status.completedNodes = workflow.status.completedNodes.filter(nodeId => this.isNodeBeforeCheckpoint(workflow, nodeId, checkpoint.nodeId));
        this.eventBus.emit('checkpoint-restored', { workflowId, checkpoint });
    }
    /**
     * Adjust workflow dynamically
     */
    adjustWorkflow(workflowId, adjustment) {
        const workflow = this.workflows.get(workflowId);
        if (!workflow)
            return;
        switch (adjustment.type) {
            case 'add-node':
                this.addNode(workflowId, adjustment.node);
                break;
            case 'remove-node':
                this.removeNode(workflowId, adjustment.nodeId);
                break;
            case 'modify-node':
                this.modifyNode(workflowId, adjustment.nodeId, adjustment.modifications);
                break;
            case 'reroute':
                this.rerouteEdges(workflowId, adjustment.rerouting);
                break;
        }
        this.eventBus.emit('workflow-adjusted', { workflowId, adjustment });
    }
    /**
     * Initialize workflow templates
     */
    initializeTemplates() {
        // Complex Task Template
        this.templates.set('complex-task', {
            name: 'Complex Task',
            nodes: [
                { id: 'research', type: 'task', agentId: 'ResearchAgent' },
                { id: 'architect', type: 'task', agentId: 'ArchitectAgent', dependencies: ['research'] },
                { id: 'review-arch', type: 'task', agentId: 'ReviewerGPT', dependencies: ['architect'] },
                { id: 'implement', type: 'task', agentId: 'CodeSmithAgent', dependencies: ['review-arch'] },
                { id: 'test', type: 'task', agentId: 'FixerBot', dependencies: ['implement'] },
                { id: 'document', type: 'task', agentId: 'DocuBot', dependencies: ['test'] }
            ]
        });
        // Parallel Research Template
        this.templates.set('parallel-research', {
            name: 'Parallel Research',
            nodes: [
                { id: 'split', type: 'parallel' },
                { id: 'research1', type: 'task', agentId: 'ResearchAgent' },
                { id: 'research2', type: 'task', agentId: 'ResearchAgent' },
                { id: 'research3', type: 'task', agentId: 'ResearchAgent' },
                { id: 'merge', type: 'sequential', dependencies: ['research1', 'research2', 'research3'] },
                { id: 'synthesize', type: 'task', agentId: 'OrchestratorAgent', dependencies: ['merge'] }
            ]
        });
        // Iterative Improvement Template
        this.templates.set('iterative-improvement', {
            name: 'Iterative Improvement',
            nodes: [
                { id: 'initial', type: 'task', agentId: 'CodeSmithAgent' },
                { id: 'review', type: 'task', agentId: 'ReviewerGPT', dependencies: ['initial'] },
                { id: 'decision', type: 'decision', dependencies: ['review'] },
                { id: 'improve', type: 'task', agentId: 'FixerBot', dependencies: ['decision'] },
                { id: 'loop', type: 'loop', dependencies: ['improve'] }
            ]
        });
    }
    /**
     * Topological sort for node ordering
     */
    topologicalSort(workflow) {
        const sorted = [];
        const visited = new Set();
        const visiting = new Set();
        const visit = (nodeId) => {
            if (visited.has(nodeId))
                return;
            if (visiting.has(nodeId)) {
                throw new Error('Circular dependency detected in workflow');
            }
            visiting.add(nodeId);
            const node = workflow.nodes.get(nodeId);
            if (node?.children) {
                node.children.forEach(childId => visit(childId));
            }
            visiting.delete(nodeId);
            visited.add(nodeId);
            if (node)
                sorted.unshift(node);
        };
        // Start from root node
        visit(workflow.startNode);
        // Visit any disconnected nodes
        workflow.nodes.forEach((_, nodeId) => {
            if (!visited.has(nodeId)) {
                visit(nodeId);
            }
        });
        return sorted;
    }
    /**
     * Group nodes into execution stages
     */
    groupIntoStages(workflow, sortedNodes) {
        const stages = [];
        const nodeStage = new Map();
        sortedNodes.forEach(node => {
            let stage = 0;
            // Find maximum stage of dependencies
            if (node.dependencies) {
                node.dependencies.forEach(depId => {
                    const depStage = nodeStage.get(depId) || 0;
                    stage = Math.max(stage, depStage + 1);
                });
            }
            nodeStage.set(node.id, stage);
            // Add to stage
            if (!stages[stage]) {
                stages[stage] = {
                    stageId: `stage_${stage}`,
                    nodes: [],
                    parallel: true,
                    dependencies: stage > 0 ? [`stage_${stage - 1}`] : [],
                    estimatedDuration: 0
                };
            }
            stages[stage].nodes.push(node);
        });
        return stages;
    }
    /**
     * Find critical path through workflow
     */
    findCriticalPath(workflow) {
        const distances = new Map();
        const previous = new Map();
        // Initialize distances
        workflow.nodes.forEach((_, nodeId) => {
            distances.set(nodeId, 0);
        });
        // Calculate longest path (critical path)
        const sortedNodes = this.topologicalSort(workflow);
        sortedNodes.forEach(node => {
            const nodeDistance = distances.get(node.id) || 0;
            node.children?.forEach(childId => {
                const edgeWeight = 1; // Could use actual task duration estimates
                const childDistance = distances.get(childId) || 0;
                if (nodeDistance + edgeWeight > childDistance) {
                    distances.set(childId, nodeDistance + edgeWeight);
                    previous.set(childId, node.id);
                }
            });
        });
        // Find the end node with maximum distance
        let maxDistance = 0;
        let endNode = '';
        workflow.nodes.forEach((node, nodeId) => {
            if (!node.children || node.children.length === 0) {
                const distance = distances.get(nodeId) || 0;
                if (distance > maxDistance) {
                    maxDistance = distance;
                    endNode = nodeId;
                }
            }
        });
        // Reconstruct path
        const path = [];
        let current = endNode;
        while (current) {
            path.unshift(current);
            current = previous.get(current) || '';
        }
        return path;
    }
    /**
     * Estimate workflow duration
     */
    estimateDuration(stages) {
        return stages.reduce((total, stage) => {
            const stageDuration = stage.parallel
                ? Math.max(...stage.nodes.map(n => n.timeout || 5000))
                : stage.nodes.reduce((sum, n) => sum + (n.timeout || 5000), 0);
            return total + stageDuration;
        }, 0);
    }
    /**
     * Calculate workflow parallelism
     */
    calculateParallelism(stages) {
        const parallelCounts = stages.map(stage => stage.parallel ? stage.nodes.length : 1);
        return Math.max(...parallelCounts);
    }
    /**
     * Check if node is before checkpoint
     */
    isNodeBeforeCheckpoint(workflow, nodeId, checkpointNodeId) {
        // Simple check - in production, do proper graph traversal
        const sorted = this.topologicalSort(workflow);
        const nodeIdx = sorted.findIndex(n => n.id === nodeId);
        const checkpointIdx = sorted.findIndex(n => n.id === checkpointNodeId);
        return nodeIdx < checkpointIdx;
    }
    /**
     * Remove a node from workflow
     */
    removeNode(workflowId, nodeId) {
        const workflow = this.workflows.get(workflowId);
        if (!workflow)
            return;
        // Remove node
        workflow.nodes.delete(nodeId);
        // Remove edges
        workflow.edges = workflow.edges.filter(edge => edge.from !== nodeId && edge.to !== nodeId);
        // Update dependencies
        workflow.nodes.forEach(node => {
            if (node.dependencies) {
                node.dependencies = node.dependencies.filter(dep => dep !== nodeId);
            }
            if (node.children) {
                node.children = node.children.filter(child => child !== nodeId);
            }
        });
    }
    /**
     * Modify a node
     */
    modifyNode(workflowId, nodeId, modifications) {
        const workflow = this.workflows.get(workflowId);
        if (!workflow)
            return;
        const node = workflow.nodes.get(nodeId);
        if (!node)
            return;
        Object.assign(node, modifications);
    }
    /**
     * Reroute edges
     */
    rerouteEdges(workflowId, rerouting) {
        const workflow = this.workflows.get(workflowId);
        if (!workflow)
            return;
        rerouting.forEach(route => {
            const edgeIdx = workflow.edges.findIndex(e => e.from === route.from && e.to === route.to);
            if (edgeIdx >= 0) {
                workflow.edges[edgeIdx].to = route.newTo;
            }
        });
    }
    /**
     * Apply template to workflow
     */
    applyTemplate(workflow, template) {
        template.nodes.forEach(nodeConfig => {
            const node = {
                id: nodeConfig.id,
                type: nodeConfig.type,
                agentId: nodeConfig.agentId,
                dependencies: nodeConfig.dependencies
            };
            workflow.nodes.set(node.id, node);
        });
        // Auto-create edges based on dependencies
        workflow.nodes.forEach(node => {
            if (node.dependencies) {
                node.dependencies.forEach(depId => {
                    workflow.edges.push({ from: depId, to: node.id });
                });
            }
        });
        if (template.nodes.length > 0) {
            workflow.startNode = template.nodes[0].id;
        }
    }
    /**
     * Generate workflow ID
     */
    generateWorkflowId() {
        return `wf_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    /**
     * Generate checkpoint ID
     */
    generateCheckpointId() {
        return `cp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
}
exports.WorkflowEngine = WorkflowEngine;
/**
 * Workflow Executor - Handles actual execution of workflow
 */
class WorkflowExecutor {
    constructor(workflow, eventBus) {
        this.paused = false;
        this.cancelled = false;
        this.results = new Map();
        this.workflow = workflow;
        this.eventBus = eventBus;
    }
    async execute(plan) {
        for (const stage of plan.stages) {
            if (this.cancelled)
                break;
            // Wait if paused
            while (this.paused && !this.cancelled) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            // Execute stage
            await this.executeStage(stage);
            // Create checkpoint after each stage
            this.createCheckpoint(stage.stageId);
        }
        return this.results;
    }
    async executeStage(stage) {
        this.eventBus.emit('stage-started', { workflowId: this.workflow.id, stage });
        if (stage.parallel) {
            // Execute nodes in parallel
            const promises = stage.nodes.map(node => this.executeNode(node));
            await Promise.all(promises);
        }
        else {
            // Execute nodes sequentially
            for (const node of stage.nodes) {
                await this.executeNode(node);
            }
        }
        this.eventBus.emit('stage-completed', { workflowId: this.workflow.id, stage });
    }
    async executeNode(node) {
        const startTime = Date.now();
        let retries = 0;
        const maxRetries = node.retryPolicy?.maxAttempts || 1;
        this.workflow.status.currentNodes.push(node.id);
        this.eventBus.emit('node-started', { workflowId: this.workflow.id, node });
        while (retries < maxRetries) {
            try {
                // Execute based on node type
                let output;
                switch (node.type) {
                    case 'task':
                        output = await this.executeTask(node);
                        break;
                    case 'decision':
                        output = await this.executeDecision(node);
                        break;
                    case 'parallel':
                        output = await this.executeParallel(node);
                        break;
                    case 'sequential':
                        output = await this.executeSequential(node);
                        break;
                    case 'loop':
                        output = await this.executeLoop(node);
                        break;
                    default:
                        throw new Error(`Unknown node type: ${node.type}`);
                }
                // Store result
                const result = {
                    nodeId: node.id,
                    status: 'success',
                    output,
                    duration: Date.now() - startTime,
                    retries
                };
                this.results.set(node.id, result);
                this.workflow.status.completedNodes.push(node.id);
                this.workflow.status.currentNodes = this.workflow.status.currentNodes.filter(id => id !== node.id);
                this.eventBus.emit('node-completed', { workflowId: this.workflow.id, node, result });
                return;
            }
            catch (error) {
                retries++;
                if (retries < maxRetries) {
                    // Calculate backoff
                    const backoff = Math.min(1000 * Math.pow(node.retryPolicy?.backoffMultiplier || 2, retries), node.retryPolicy?.maxBackoffMs || 30000);
                    this.eventBus.emit('node-retry', {
                        workflowId: this.workflow.id,
                        node,
                        attempt: retries,
                        error
                    });
                    await new Promise(resolve => setTimeout(resolve, backoff));
                }
                else {
                    // Max retries exceeded
                    const result = {
                        nodeId: node.id,
                        status: 'failure',
                        error: error instanceof Error ? error.message : String(error),
                        duration: Date.now() - startTime,
                        retries
                    };
                    this.results.set(node.id, result);
                    this.workflow.status.failedNodes.push(node.id);
                    this.workflow.status.currentNodes = this.workflow.status.currentNodes.filter(id => id !== node.id);
                    this.eventBus.emit('node-failed', { workflowId: this.workflow.id, node, result });
                    throw error;
                }
            }
        }
    }
    async executeTask(node) {
        // Placeholder for actual task execution
        // In production, this would call the appropriate agent
        await new Promise(resolve => setTimeout(resolve, 1000));
        return { result: `Task ${node.id} completed by ${node.agentId}` };
    }
    async executeDecision(node) {
        if (!node.condition) {
            throw new Error(`Decision node ${node.id} missing condition`);
        }
        const decision = node.condition(this.workflow.context);
        return { decision };
    }
    async executeParallel(node) {
        if (!node.children)
            return {};
        const childNodes = node.children
            .map(childId => this.workflow.nodes.get(childId))
            .filter(Boolean);
        const promises = childNodes.map(child => this.executeNode(child));
        const results = await Promise.all(promises);
        return { parallel: true, results };
    }
    async executeSequential(node) {
        if (!node.children)
            return {};
        const results = [];
        for (const childId of node.children) {
            const childNode = this.workflow.nodes.get(childId);
            if (childNode) {
                await this.executeNode(childNode);
                results.push(this.results.get(childId));
            }
        }
        return { sequential: true, results };
    }
    async executeLoop(node) {
        if (!node.condition || !node.children || node.children.length === 0) {
            throw new Error(`Loop node ${node.id} missing condition or children`);
        }
        const results = [];
        let iteration = 0;
        const maxIterations = 100; // Safety limit
        while (node.condition(this.workflow.context) && iteration < maxIterations) {
            for (const childId of node.children) {
                const childNode = this.workflow.nodes.get(childId);
                if (childNode) {
                    await this.executeNode(childNode);
                    results.push(this.results.get(childId));
                }
            }
            iteration++;
        }
        return { loop: true, iterations: iteration, results };
    }
    createCheckpoint(stageId) {
        const checkpoint = {
            id: `cp_${Date.now()}`,
            nodeId: stageId,
            timestamp: Date.now(),
            context: new Map(this.workflow.context),
            results: new Map(this.results)
        };
        this.workflow.checkpoints.push(checkpoint);
        this.eventBus.emit('checkpoint-created', { workflowId: this.workflow.id, checkpoint });
    }
    pause() {
        this.paused = true;
        this.workflow.status.state = 'paused';
        this.eventBus.emit('workflow-paused', this.workflow);
    }
    resume() {
        this.paused = false;
        this.workflow.status.state = 'running';
        this.eventBus.emit('workflow-resumed', this.workflow);
    }
    cancel() {
        this.cancelled = true;
        this.workflow.status.state = 'failed';
        this.workflow.status.error = 'Workflow cancelled by user';
        this.eventBus.emit('workflow-cancelled', this.workflow);
    }
}


/***/ }),

/***/ "./src/extension.ts":
/*!**************************!*\
  !*** ./src/extension.ts ***!
  \**************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {


var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.activate = activate;
exports.deactivate = deactivate;
/**
 * KI AutoAgent VS Code Extension
 * Main extension entry point that registers all chat participants
 */
const vscode = __importStar(__webpack_require__(/*! vscode */ "vscode"));
const VSCodeMasterDispatcher_1 = __webpack_require__(/*! ./core/VSCodeMasterDispatcher */ "./src/core/VSCodeMasterDispatcher.ts");
const ClaudeCodeService_1 = __webpack_require__(/*! ./services/ClaudeCodeService */ "./src/services/ClaudeCodeService.ts");
const AgentConfigurationManager_1 = __webpack_require__(/*! ./core/AgentConfigurationManager */ "./src/core/AgentConfigurationManager.ts");
const ArchitectAgent_1 = __webpack_require__(/*! ./agents/ArchitectAgent */ "./src/agents/ArchitectAgent.ts");
const OrchestratorAgent_1 = __webpack_require__(/*! ./agents/OrchestratorAgent */ "./src/agents/OrchestratorAgent.ts");
const CodeSmithAgent_1 = __webpack_require__(/*! ./agents/CodeSmithAgent */ "./src/agents/CodeSmithAgent.ts");
const TradeStratAgent_1 = __webpack_require__(/*! ./agents/TradeStratAgent */ "./src/agents/TradeStratAgent.ts");
const ResearchAgent_1 = __webpack_require__(/*! ./agents/ResearchAgent */ "./src/agents/ResearchAgent.ts");
const OpusArbitratorAgent_1 = __webpack_require__(/*! ./agents/OpusArbitratorAgent */ "./src/agents/OpusArbitratorAgent.ts");
const DocuBotAgent_1 = __webpack_require__(/*! ./agents/DocuBotAgent */ "./src/agents/DocuBotAgent.ts");
const ReviewerGPTAgent_1 = __webpack_require__(/*! ./agents/ReviewerGPTAgent */ "./src/agents/ReviewerGPTAgent.ts");
// import { FixerBotAgent } from './agents/FixerBotAgent'; // DEPRECATED - Functionality integrated into CodeSmithAgent
// Multi-Agent Chat UI Components
const MultiAgentChatPanel_1 = __webpack_require__(/*! ./ui/MultiAgentChatPanel */ "./src/ui/MultiAgentChatPanel.ts");
const ChatWidget_1 = __webpack_require__(/*! ./ui/ChatWidget */ "./src/ui/ChatWidget.ts");
// Global output channel for debugging
let outputChannel;
async function activate(context) {
    // VERSION 2.3.9 - CLAUDE CODE CLI INTEGRATION (CORRECTED)
    console.log('🚀 KI AutoAgent v2.3.9: Extension activation started');
    // Create single output channel
    outputChannel = vscode.window.createOutputChannel('KI AutoAgent');
    outputChannel.clear();
    outputChannel.show(true);
    outputChannel.appendLine('🚀 KI AutoAgent Extension v2.3.9 Activating');
    outputChannel.appendLine('============================================');
    outputChannel.appendLine(`Time: ${new Date().toLocaleString()}`);
    outputChannel.appendLine(`VS Code Version: ${vscode.version}`);
    outputChannel.appendLine('');
    outputChannel.appendLine('✨ NEW: Claude Code CLI integration - Install with: npm install -g @anthropic-ai/claude-code');
    try {
        // Initialize the Agent Configuration Manager
        outputChannel.appendLine('Initializing Agent Configuration Manager...');
        const configManager = AgentConfigurationManager_1.AgentConfigurationManager.getInstance(context);
        await configManager.initialize();
        outputChannel.appendLine('✅ Agent Configuration Manager ready');
        // Initialize the master dispatcher
        outputChannel.appendLine('Initializing Master Dispatcher...');
        const dispatcher = new VSCodeMasterDispatcher_1.VSCodeMasterDispatcher(context);
        outputChannel.appendLine('✅ Master Dispatcher ready');
        // Initialize Chat Widget (Status Bar)
        outputChannel.appendLine('Initializing Chat Widget...');
        const chatWidget = new ChatWidget_1.ChatWidget(context, dispatcher);
        outputChannel.appendLine('✅ Chat Widget ready');
        // Register chat panel commands with error handling
        const commandsToRegister = [
            {
                id: 'ki-autoagent.showChat',
                handler: () => MultiAgentChatPanel_1.MultiAgentChatPanel.createOrShow(context.extensionUri, dispatcher)
            },
            {
                id: 'ki-autoagent.toggleChat',
                handler: () => MultiAgentChatPanel_1.MultiAgentChatPanel.createOrShow(context.extensionUri, dispatcher)
            },
            {
                id: 'ki-autoagent.quickChat',
                handler: () => {
                    MultiAgentChatPanel_1.MultiAgentChatPanel.createOrShow(context.extensionUri, dispatcher);
                    vscode.window.showInformationMessage('🤖 KI AutoAgent Chat ready! Use @ki for universal assistance or specific agents like @richter, @architect, @codesmith');
                }
            },
            {
                id: 'ki-autoagent.clearUnread',
                handler: () => {
                    if (!outputChannel) {
                        outputChannel = vscode.window.createOutputChannel('KI AutoAgent');
                    }
                    outputChannel.clear();
                    outputChannel.appendLine('Cleared messages');
                }
            }
        ];
        // Register commands with duplicate check
        for (const cmd of commandsToRegister) {
            try {
                const disposable = vscode.commands.registerCommand(cmd.id, cmd.handler);
                context.subscriptions.push(disposable);
                outputChannel.appendLine(`  ✅ Registered command: ${cmd.id}`);
            }
            catch (error) {
                outputChannel.appendLine(`  ⚠️ Command already exists: ${cmd.id} - skipping`);
            }
        }
        // Command registration complete
        outputChannel.appendLine('');
        // Initialize and register all agents 
        outputChannel.appendLine('\nCreating Agent Instances...');
        let agents = [];
        let agentCreationErrors = [];
        try {
            agents.push(new OrchestratorAgent_1.OrchestratorAgent(context, dispatcher));
            outputChannel.appendLine('  ✅ OrchestratorAgent created');
        }
        catch (error) {
            outputChannel.appendLine(`  ❌ OrchestratorAgent failed: ${error.message}`);
            agentCreationErrors.push(`OrchestratorAgent: ${error}`);
        }
        try {
            agents.push(new OpusArbitratorAgent_1.OpusArbitratorAgent(context, dispatcher));
            outputChannel.appendLine('  ✅ OpusArbitratorAgent created');
        }
        catch (error) {
            outputChannel.appendLine(`  ❌ OpusArbitratorAgent failed: ${error.message}`);
            agentCreationErrors.push(`OpusArbitratorAgent: ${error}`);
        }
        try {
            agents.push(new ArchitectAgent_1.ArchitectAgent(context, dispatcher));
            outputChannel.appendLine('  ✅ ArchitectAgent created');
        }
        catch (error) {
            outputChannel.appendLine(`  ❌ ArchitectAgent failed: ${error.message}`);
            agentCreationErrors.push(`ArchitectAgent: ${error}`);
        }
        try {
            agents.push(new CodeSmithAgent_1.CodeSmithAgent(context, dispatcher));
            outputChannel.appendLine('  ✅ CodeSmithAgent created');
        }
        catch (error) {
            outputChannel.appendLine(`  ❌ CodeSmithAgent failed: ${error.message}`);
            agentCreationErrors.push(`CodeSmithAgent: ${error}`);
        }
        try {
            agents.push(new TradeStratAgent_1.TradeStratAgent(context, dispatcher));
            outputChannel.appendLine('  ✅ TradeStratAgent created');
        }
        catch (error) {
            outputChannel.appendLine(`  ❌ TradeStratAgent failed: ${error.message}`);
            agentCreationErrors.push(`TradeStratAgent: ${error}`);
        }
        try {
            agents.push(new ResearchAgent_1.ResearchAgent(context, dispatcher));
            outputChannel.appendLine('  ✅ ResearchAgent created');
        }
        catch (error) {
            outputChannel.appendLine(`  ❌ ResearchAgent failed: ${error.message}`);
            agentCreationErrors.push(`ResearchAgent: ${error}`);
        }
        try {
            agents.push(new DocuBotAgent_1.DocuBotAgent(context, dispatcher));
            outputChannel.appendLine('  ✅ DocuBotAgent created');
        }
        catch (error) {
            outputChannel.appendLine(`  ❌ DocuBotAgent failed: ${error.message}`);
            agentCreationErrors.push(`DocuBotAgent: ${error}`);
        }
        try {
            agents.push(new ReviewerGPTAgent_1.ReviewerGPTAgent(context, dispatcher));
            outputChannel.appendLine('  ✅ ReviewerGPTAgent created');
        }
        catch (error) {
            outputChannel.appendLine(`  ❌ ReviewerGPTAgent failed: ${error.message}`);
            agentCreationErrors.push(`ReviewerGPTAgent: ${error}`);
        }
        // DEPRECATED: FixerBot functionality has been integrated into CodeSmithAgent
        // CodeSmith now handles: /fix, /debug, /refactor, /modernize commands
        // try {
        //     agents.push(new FixerBotAgent(context, dispatcher));
        //     outputChannel.appendLine('  ✅ FixerBotAgent created');
        // } catch (error) {
        //     outputChannel.appendLine(`  ❌ FixerBotAgent failed: ${(error as any).message}`);
        //     agentCreationErrors.push(`FixerBotAgent: ${error}`);
        // }
        outputChannel.appendLine(`Agent creation completed: ${agents.length} created, ${agentCreationErrors.length} errors`);
        if (agentCreationErrors.length > 0) {
            outputChannel.appendLine('Agent creation errors:');
            agentCreationErrors.forEach(error => outputChannel.appendLine(`  - ${error}`));
        }
        // Initialize all agents (TODO: Update agents to use new BaseAgent system)
        for (const agent of agents) {
            try {
                // Enhanced initialization will be added when agents are updated to use new BaseAgent
                console.log(`✅ Agent ${agent.config?.participantId || 'unknown'} ready`);
            }
            catch (error) {
                console.warn(`Failed to initialize agent:`, error);
            }
        }
        // Register each agent as a chat participant
        outputChannel.appendLine(`\nRegistering ${agents.length} agents...`);
        let registrationErrors = [];
        agents.forEach((agent, index) => {
            try {
                const participantId = agent.config.participantId;
                const participant = vscode.chat.createChatParticipant(participantId, agent.createHandler());
                // Set icon if available
                const iconPath = agent.config?.iconPath;
                if (iconPath) {
                    participant.iconPath = iconPath;
                }
                // Register the agent with dispatcher for orchestration
                const dispatcherAgentId = participantId.split('.')[1];
                outputChannel.appendLine(`  Registering with dispatcher: ${participantId} as '${dispatcherAgentId}'`);
                dispatcher.registerAgent(dispatcherAgentId, agent);
                // Add to subscriptions for cleanup
                context.subscriptions.push(participant);
                outputChannel.appendLine(`  ✅ Registered: ${participantId} (dispatcher ID: ${dispatcherAgentId})`);
            }
            catch (error) {
                const errorMsg = `Failed to register agent ${index + 1}: ${error.message}`;
                outputChannel.appendLine(`  ❌ ${errorMsg}`);
                registrationErrors.push(errorMsg);
            }
        });
        // Verify agent registration
        outputChannel.appendLine('\nVerifying agent registration with dispatcher:');
        const registeredAgents = dispatcher.getRegisteredAgents();
        outputChannel.appendLine(`  Registered agents: [${registeredAgents.join(', ')}]`);
        outputChannel.appendLine(`Registration completed: ${agents.length - registrationErrors.length} succeeded, ${registrationErrors.length} failed`);
        if (registrationErrors.length > 0) {
            outputChannel.appendLine('Registration errors:');
            registrationErrors.forEach(error => outputChannel.appendLine(`  - ${error}`));
        }
        // Register extension commands
        outputChannel.appendLine('\nRegistering extension commands...');
        registerCommands(context, dispatcher);
        outputChannel.appendLine('✅ Extension commands registered');
        // Show welcome message in output channel
        showWelcomeMessage(outputChannel);
        // Final success
        outputChannel.appendLine('\n✅ KI AUTOAGENT EXTENSION ACTIVATED!');
        outputChannel.appendLine('============================================');
        outputChannel.appendLine(`Total agents: ${agents.length}`);
        outputChannel.appendLine(`Registration errors: ${registrationErrors.length}`);
        outputChannel.appendLine(`Activated at: ${new Date().toLocaleString()}`);
        outputChannel.appendLine('\nType "@ki" in chat to get started!');
        // Single success notification
        vscode.window.showInformationMessage(`🎉 KI AutoAgent v${context.extension.packageJSON.version} activated! ${agents.length} agents ready.`);
    }
    catch (error) {
        // Handle any errors during extension activation
        const errorMsg = `KI AutoAgent activation failed: ${error.message || error}`;
        console.error(errorMsg);
        // Show error
        vscode.window.showErrorMessage(errorMsg);
        // Try to show error in output channel if available
        if (outputChannel) {
            outputChannel.appendLine(`\n❌ ACTIVATION ERROR:`);
            outputChannel.appendLine(`Error: ${error}`);
            outputChannel.appendLine(`Message: ${error.message}`);
            outputChannel.appendLine(`Stack: ${error.stack}`);
            outputChannel.show(true);
        }
    }
}
function deactivate() {
    console.log('👋 KI AutoAgent extension is deactivated');
}
function registerCommands(context, dispatcher) {
    // Command: Create File
    const createFileCommand = vscode.commands.registerCommand('ki-autoagent.createFile', async (filename, content) => {
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                vscode.window.showErrorMessage('No workspace folder open');
                return;
            }
            const fileUri = vscode.Uri.joinPath(workspaceFolder.uri, filename);
            await vscode.workspace.fs.writeFile(fileUri, Buffer.from(content, 'utf8'));
            // Open the created file
            const document = await vscode.workspace.openTextDocument(fileUri);
            await vscode.window.showTextDocument(document);
            vscode.window.showInformationMessage(`✅ Created file: ${filename}`);
        }
        catch (error) {
            vscode.window.showErrorMessage(`❌ Failed to create file: ${error.message}`);
        }
    });
    // Command: Insert at Cursor
    const insertAtCursorCommand = vscode.commands.registerCommand('ki-autoagent.insertAtCursor', async (content) => {
        try {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active text editor');
                return;
            }
            const position = editor.selection.active;
            await editor.edit(editBuilder => {
                editBuilder.insert(position, content);
            });
            vscode.window.showInformationMessage('✅ Content inserted at cursor');
        }
        catch (error) {
            vscode.window.showErrorMessage(`❌ Failed to insert content: ${error.message}`);
        }
    });
    // Command: Apply Suggestion
    const applySuggestionCommand = vscode.commands.registerCommand('ki-autoagent.applySuggestion', async (suggestionData) => {
        try {
            // Handle different types of suggestions
            if (suggestionData.type === 'file_creation') {
                await vscode.commands.executeCommand('ki-autoagent.createFile', suggestionData.filename, suggestionData.content);
            }
            else if (suggestionData.type === 'code_insertion') {
                await vscode.commands.executeCommand('ki-autoagent.insertAtCursor', suggestionData.code);
            }
            else {
                vscode.window.showInformationMessage(`Applied suggestion: ${suggestionData.description}`);
            }
        }
        catch (error) {
            vscode.window.showErrorMessage(`❌ Failed to apply suggestion: ${error.message}`);
        }
    });
    // Command: Test Claude Code CLI
    const testClaudeCommand = vscode.commands.registerCommand('ki-autoagent.testClaudeCLI', async () => {
        const outputChannel = vscode.window.createOutputChannel('Claude CLI Test');
        outputChannel.show();
        outputChannel.appendLine('🔍 Testing Claude Code CLI Integration...');
        outputChannel.appendLine('==========================================\n');
        try {
            const claudeService = (0, ClaudeCodeService_1.getClaudeCodeService)();
            // Check if CLI is available
            outputChannel.appendLine('1. Checking Claude CLI availability...');
            const isAvailable = await claudeService.isAvailable();
            if (!isAvailable) {
                outputChannel.appendLine('❌ Claude CLI not found!');
                outputChannel.appendLine('\nTo install Claude CLI:');
                outputChannel.appendLine('  npm install -g @anthropic-ai/claude-code');
                outputChannel.appendLine('\nOr use Anthropic API by configuring your API key in VS Code settings.');
                vscode.window.showErrorMessage('Claude CLI not installed. See output for installation instructions.');
                return;
            }
            outputChannel.appendLine('✅ Claude CLI is available!\n');
            // Test connection
            outputChannel.appendLine('2. Testing Claude CLI connection...');
            const testResult = await claudeService.testConnection();
            if (testResult.success) {
                outputChannel.appendLine(`✅ ${testResult.message}\n`);
                outputChannel.appendLine('3. Claude CLI Integration Status: WORKING');
                outputChannel.appendLine('==========================================');
                outputChannel.appendLine('✨ Everything is working correctly!');
                outputChannel.appendLine('\nYou can now use Claude-powered agents in your chat.');
                vscode.window.showInformationMessage('✅ Claude CLI is working correctly!');
            }
            else {
                outputChannel.appendLine(`❌ ${testResult.message}\n`);
                outputChannel.appendLine('3. Claude CLI Integration Status: ERROR');
                outputChannel.appendLine('==========================================');
                outputChannel.appendLine('Please check the error message above.');
                vscode.window.showErrorMessage(`Claude CLI test failed: ${testResult.message}`);
            }
        }
        catch (error) {
            outputChannel.appendLine(`\n❌ Test failed with error: ${error.message}`);
            outputChannel.appendLine('\nPlease check your configuration and try again.');
            vscode.window.showErrorMessage(`Claude CLI test failed: ${error.message}`);
        }
    });
    // Command: Show Agent Statistics
    const showAgentStatsCommand = vscode.commands.registerCommand('ki-autoagent.showAgentStats', async () => {
        try {
            const stats = await dispatcher.getAgentStats();
            if (Object.keys(stats).length === 0) {
                vscode.window.showInformationMessage('No agent statistics available yet');
                return;
            }
            // Create a new document to display stats
            const statsContent = formatAgentStats(stats);
            const document = await vscode.workspace.openTextDocument({
                content: statsContent,
                language: 'markdown'
            });
            await vscode.window.showTextDocument(document);
        }
        catch (error) {
            vscode.window.showErrorMessage(`❌ Failed to show stats: ${error.message}`);
        }
    });
    // Command: Show Help
    const showHelpCommand = vscode.commands.registerCommand('ki-autoagent.showHelp', async (agentId) => {
        const helpContent = generateHelpContent(agentId);
        const document = await vscode.workspace.openTextDocument({
            content: helpContent,
            language: 'markdown'
        });
        await vscode.window.showTextDocument(document);
    });
    // Command: Plan Implementation
    const planImplementationCommand = vscode.commands.registerCommand('ki-autoagent.planImplementation', async (task, architecture) => {
        // This would trigger the orchestrator to create an implementation plan
        vscode.window.showInformationMessage('Creating implementation plan...');
        // Could open chat with pre-filled message
    });
    // Command: Execute Workflow
    const executeWorkflowCommand = vscode.commands.registerCommand('ki-autoagent.executeWorkflow', async (task, workflow) => {
        vscode.window.showInformationMessage('Executing workflow...');
        // Implementation for workflow execution
    });
    // Command: Configure Agent Models
    const configureAgentModelsCommand = vscode.commands.registerCommand('ki-autoagent.configureAgentModels', async () => {
        const configManager = AgentConfigurationManager_1.AgentConfigurationManager.getInstance(context);
        const availableModels = configManager.getAvailableModels();
        // Show agent model configuration UI
        const agentIds = ['orchestrator', 'richter', 'architect', 'codesmith', 'tradestrat', 'research'];
        for (const agentId of agentIds) {
            const currentModel = configManager.getAgentModel(agentId);
            const modelOptions = Object.keys(availableModels).map(modelId => ({
                label: availableModels[modelId].name,
                description: `${availableModels[modelId].provider} - ${availableModels[modelId].tier}`,
                detail: `$${availableModels[modelId].costPerMillion.input}/$${availableModels[modelId].costPerMillion.output} per million tokens`,
                modelId
            }));
            const selected = await vscode.window.showQuickPick(modelOptions, {
                title: `Select model for ${agentId}`,
                placeHolder: `Current: ${currentModel}`,
                ignoreFocusOut: true
            });
            if (selected && selected.modelId !== currentModel) {
                await configManager.setAgentModel(agentId, selected.modelId);
                vscode.window.showInformationMessage(`✅ Updated ${agentId} model to ${selected.label}`);
            }
        }
    });
    // Command: Show Agent Performance
    const showAgentPerformanceCommand = vscode.commands.registerCommand('ki-autoagent.showAgentPerformance', async () => {
        const configManager = AgentConfigurationManager_1.AgentConfigurationManager.getInstance(context);
        const agentIds = ['orchestrator', 'richter', 'architect', 'codesmith', 'tradestrat', 'research'];
        let performanceReport = '# Agent Performance Report\n\n';
        performanceReport += `Generated: ${new Date().toLocaleString()}\n\n`;
        for (const agentId of agentIds) {
            const metrics = configManager.getAgentMetrics(agentId);
            const model = configManager.getAgentModel(agentId);
            performanceReport += `## ${agentId.charAt(0).toUpperCase() + agentId.slice(1)}\n`;
            performanceReport += `**Model:** ${model}\n`;
            if (metrics) {
                const successRate = (metrics.successfulExecutions / metrics.totalExecutions * 100).toFixed(1);
                performanceReport += `**Success Rate:** ${successRate}%\n`;
                performanceReport += `**Total Executions:** ${metrics.totalExecutions}\n`;
                performanceReport += `**Average Response Time:** ${metrics.averageResponseTime.toFixed(0)}ms\n`;
                performanceReport += `**Current Streak:** ${metrics.currentStreak}\n`;
                performanceReport += `**Best Streak:** ${metrics.bestStreak}\n`;
            }
            else {
                performanceReport += `**Status:** No performance data yet\n`;
            }
            performanceReport += '\n';
        }
        const document = await vscode.workspace.openTextDocument({
            content: performanceReport,
            language: 'markdown'
        });
        await vscode.window.showTextDocument(document);
    });
    // Command: Open Configuration Directory
    const openConfigDirectoryCommand = vscode.commands.registerCommand('ki-autoagent.openConfigDirectory', async () => {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (workspaceFolder) {
            const configPath = vscode.Uri.joinPath(workspaceFolder.uri, '.kiautoagent');
            try {
                await vscode.commands.executeCommand('vscode.openFolder', configPath, { forceNewWindow: false });
            }
            catch {
                vscode.window.showInformationMessage('Configuration directory will be created when first used');
            }
        }
        else {
            vscode.window.showWarningMessage('No workspace folder open');
        }
    });
    // Register all commands
    context.subscriptions.push(createFileCommand, insertAtCursorCommand, applySuggestionCommand, testClaudeCommand, showAgentStatsCommand, showHelpCommand, planImplementationCommand, executeWorkflowCommand, configureAgentModelsCommand, showAgentPerformanceCommand, openConfigDirectoryCommand);
    console.log('✅ All extension commands registered');
}
function showWelcomeMessage(outputChannel) {
    outputChannel.appendLine('🤖 KI AutoAgent VS Code Extension');
    outputChannel.appendLine('=======================================');
    outputChannel.appendLine('');
    outputChannel.appendLine('✅ Extension activated successfully!');
    outputChannel.appendLine('');
    outputChannel.appendLine('Available Agents:');
    outputChannel.appendLine('• @ki - Universal orchestrator (routes to best agent)');
    outputChannel.appendLine('• @richter - ⚖️ Supreme judge & conflict resolver (Opus 4.1)');
    outputChannel.appendLine('• @architect - System architecture & design');
    outputChannel.appendLine('• @codesmith - Code implementation & testing');
    outputChannel.appendLine('• @docu - Documentation generation');
    outputChannel.appendLine('• @reviewer - Code review & security');
    outputChannel.appendLine('• @fixer - Bug fixing & debugging');
    outputChannel.appendLine('• @tradestrat - Trading strategy development');
    outputChannel.appendLine('• @research - Web research & information gathering');
    outputChannel.appendLine('');
    outputChannel.appendLine('Getting Started:');
    outputChannel.appendLine('1. Open VS Code Chat panel (Ctrl+Shift+I)');
    outputChannel.appendLine('2. Type @ki followed by your request');
    outputChannel.appendLine('3. Or use specific agents like @architect, @codesmith, etc.');
    outputChannel.appendLine('');
    outputChannel.appendLine('Configuration:');
    outputChannel.appendLine('• Set your API keys in VS Code Settings');
    outputChannel.appendLine('• Search for "KI AutoAgent" in settings');
    outputChannel.appendLine('• Configure OpenAI, Anthropic, and Perplexity API keys');
    outputChannel.appendLine('');
    outputChannel.appendLine('Need help? Type "@ki /agents" to see all available agents!');
}
function formatAgentStats(stats) {
    let content = '# KI AutoAgent Statistics\n\n';
    content += `Generated at: ${new Date().toLocaleString()}\n\n`;
    for (const [agentId, agentStats] of Object.entries(stats)) {
        const { totalExecutions, successRate, averageResponseTime, lastExecution } = agentStats;
        content += `## ${agentId}\n\n`;
        content += `- **Total Executions:** ${totalExecutions}\n`;
        content += `- **Success Rate:** ${(successRate * 100).toFixed(1)}%\n`;
        content += `- **Average Response Time:** ${averageResponseTime.toFixed(0)}ms\n`;
        if (lastExecution) {
            content += `- **Last Execution:** ${new Date(lastExecution).toLocaleString()}\n`;
        }
        content += '\n';
    }
    return content;
}
function generateHelpContent(agentId) {
    let content = '# KI AutoAgent Help\n\n';
    if (agentId) {
        content += `## Help for ${agentId}\n\n`;
        // Add agent-specific help
    }
    else {
        content += '## Getting Started\n\n';
        content += 'KI AutoAgent is a universal multi-agent AI development platform for VS Code.\n\n';
        content += '### Available Agents\n\n';
        content += '- **@ki** - Universal orchestrator that automatically routes tasks\n';
        content += '- **@richter** - ⚖️ Supreme judge & conflict resolver (Claude Opus 4.1)\n';
        content += '- **@architect** - System architecture and design expert\n';
        content += '- **@codesmith** - Senior Python/Web developer\n';
        content += '- **@docu** - Technical documentation expert\n';
        content += '- **@reviewer** - Code review and security expert\n';
        content += '- **@fixer** - Bug fixing and optimization expert\n';
        content += '- **@tradestrat** - Trading strategy expert\n';
        content += '- **@research** - Research and information expert\n\n';
        content += '### Usage Examples\n\n';
        content += '```\n';
        content += '@ki create a REST API with FastAPI\n';
        content += '@richter judge which approach is better: microservices vs monolith\n';
        content += '@richter resolve this disagreement between @architect and @codesmith\n';
        content += '@architect design a microservices architecture\n';
        content += '@codesmith implement a Python class for user management\n';
        content += '@tradestrat develop a momentum trading strategy\n';
        content += '@fixer debug this error message\n';
        content += '```\n\n';
        content += '### Configuration\n\n';
        content += '1. Open VS Code Settings (Ctrl+,)\n';
        content += '2. Search for "KI AutoAgent"\n';
        content += '3. Configure your API keys:\n';
        content += '   - OpenAI API Key (for GPT models)\n';
        content += '   - Anthropic API Key (for Claude models)\n';
        content += '   - Perplexity API Key (for research)\n\n';
        content += '### Support\n\n';
        content += 'For issues and feature requests, please visit the GitHub repository.\n';
    }
    return content;
}


/***/ }),

/***/ "./src/mixins/UnifiedChatMixin.ts":
/*!****************************************!*\
  !*** ./src/mixins/UnifiedChatMixin.ts ***!
  \****************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {


var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.UnifiedChatMixin = exports.ResponseType = void 0;
/**
 * Unified Chat Mixin - Standardized Chat Properties for all Agents
 * Provides consistent response formatting and logging across all agents
 */
const vscode = __importStar(__webpack_require__(/*! vscode */ "vscode"));
var ResponseType;
(function (ResponseType) {
    ResponseType["INITIALIZATION"] = "initialization";
    ResponseType["EXECUTING"] = "executing";
    ResponseType["SUCCESS"] = "success";
    ResponseType["WARNING"] = "warning";
    ResponseType["ERROR"] = "error";
    ResponseType["FALLBACK"] = "fallback";
    ResponseType["INFO"] = "info";
    ResponseType["TOOL_USE"] = "tool_use";
    ResponseType["DEBUG"] = "debug";
})(ResponseType || (exports.ResponseType = ResponseType = {}));
class UnifiedChatMixin {
    constructor() {
        this.responseHistory = [];
        this.maxHistorySize = 100;
        this.chatConfig = this.getDefaultChatConfig();
        this.responseHistory = [];
    }
    /**
     * Get default chat configuration from VS Code settings or use defaults
     */
    getDefaultChatConfig() {
        const config = vscode.workspace.getConfiguration('ki-autoagent.chat');
        return {
            showEmojis: config.get('showEmojis', true),
            showTimestamps: config.get('showTimestamps', true),
            showDetailedResponses: config.get('showDetailedResponses', true),
            logLevel: config.get('logLevel', 'INFO'),
            responseFormat: config.get('responseFormat', 'detailed'),
            fallbackMode: config.get('fallbackMode', 'graceful')
        };
    }
    /**
     * Generate unified response with consistent formatting
     */
    unifiedResponse(responseType, message, details, logToHistory = true) {
        const responseParts = [];
        // Add emoji if enabled
        if (this.chatConfig.showEmojis) {
            const emoji = this.getEmojiForType(responseType);
            responseParts.push(`${emoji} `);
        }
        // Add timestamp if enabled
        if (this.chatConfig.showTimestamps) {
            const timestamp = new Date().toLocaleTimeString('en-US', {
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            responseParts.push(`[${timestamp}] `);
        }
        // Add agent name
        const agentName = this.getAgentName();
        responseParts.push(`**${agentName}**: `);
        // Add main message
        responseParts.push(message);
        // Add details if available and detailed responses enabled
        if (details && this.chatConfig.showDetailedResponses && this.chatConfig.responseFormat === 'detailed') {
            responseParts.push(this.formatDetails(details));
        }
        // Combine response
        const formattedResponse = responseParts.join('');
        // Log to history
        if (logToHistory) {
            this.logToHistory(responseType, message, details, formattedResponse);
        }
        // Log to console based on log level
        this.logResponse(responseType, formattedResponse);
        return formattedResponse;
    }
    /**
     * Get emoji for response type
     */
    getEmojiForType(responseType) {
        const emojiMap = {
            [ResponseType.INITIALIZATION]: "🚀",
            [ResponseType.EXECUTING]: "🛠️",
            [ResponseType.SUCCESS]: "✅",
            [ResponseType.WARNING]: "⚠️",
            [ResponseType.ERROR]: "❌",
            [ResponseType.FALLBACK]: "🔄",
            [ResponseType.INFO]: "ℹ️",
            [ResponseType.TOOL_USE]: "🔧",
            [ResponseType.DEBUG]: "🐛"
        };
        return emojiMap[responseType] || "📝";
    }
    /**
     * Format details object for display
     */
    formatDetails(details) {
        if (!details || Object.keys(details).length === 0) {
            return '';
        }
        const detailsStr = Object.entries(details)
            .map(([key, value]) => {
            const formattedKey = key.replace(/([A-Z])/g, ' $1').trim();
            const formattedValue = typeof value === 'object'
                ? JSON.stringify(value, null, 2)
                : value;
            return `      ${formattedKey}: ${formattedValue}`;
        })
            .join('\n');
        return `\n   📊 Details:\n${detailsStr}`;
    }
    /**
     * Get agent name - to be overridden by implementing classes
     */
    getAgentName() {
        // Try to get from various possible properties
        return this.name ||
            this.config?.agentId ||
            this.config?.name ||
            'Agent';
    }
    /**
     * Log response to console based on log level
     */
    logResponse(responseType, formattedResponse) {
        const logLevelMap = {
            [ResponseType.ERROR]: 'ERROR',
            [ResponseType.WARNING]: 'WARN',
            [ResponseType.DEBUG]: 'DEBUG',
            [ResponseType.INFO]: 'INFO',
            [ResponseType.SUCCESS]: 'INFO',
            [ResponseType.EXECUTING]: 'INFO',
            [ResponseType.INITIALIZATION]: 'INFO',
            [ResponseType.FALLBACK]: 'WARN',
            [ResponseType.TOOL_USE]: 'DEBUG'
        };
        const level = logLevelMap[responseType] || 'INFO';
        // Only log if meets minimum log level
        if (this.shouldLog(level)) {
            console.log(formattedResponse);
        }
    }
    /**
     * Check if should log based on configured log level
     */
    shouldLog(level) {
        const levels = ['DEBUG', 'INFO', 'WARN', 'ERROR'];
        const configuredLevel = levels.indexOf(this.chatConfig.logLevel);
        const messageLevel = levels.indexOf(level);
        return messageLevel >= configuredLevel;
    }
    /**
     * Log to response history
     */
    logToHistory(type, message, details, formattedResponse) {
        const entry = {
            timestamp: new Date(),
            type,
            agentName: this.getAgentName(),
            message,
            details,
            formattedResponse
        };
        this.responseHistory.push(entry);
        // Trim history if exceeds max size
        if (this.responseHistory.length > this.maxHistorySize) {
            this.responseHistory = this.responseHistory.slice(-this.maxHistorySize);
        }
    }
    // Standardized message methods
    /**
     * Show initialization message
     */
    showInitialization(additionalInfo) {
        const details = {
            role: this.role || 'Unknown',
            model: this.model || this.selectedModel || 'Unknown'
        };
        // Add capabilities if available
        if (typeof this.getCapabilities === 'function') {
            details.capabilities = this.getCapabilities();
        }
        if (additionalInfo) {
            Object.assign(details, additionalInfo);
        }
        return this.unifiedResponse(ResponseType.INITIALIZATION, "Ready to assist with advanced capabilities!", details);
    }
    /**
     * Show execution start message
     */
    showExecutionStart(task, context) {
        const details = {
            task: task.substring(0, 100), // Truncate long tasks
            contextKeys: context ? Object.keys(context) : []
        };
        // Add conversation history size if available
        if (context?.conversationHistory) {
            details.conversationHistorySize = context.conversationHistory.length;
        }
        return this.unifiedResponse(ResponseType.EXECUTING, `Starting execution: ${task.substring(0, 50)}${task.length > 50 ? '...' : ''}`, details);
    }
    /**
     * Show success message
     */
    showSuccess(message, details) {
        return this.unifiedResponse(ResponseType.SUCCESS, message, details);
    }
    /**
     * Show warning message
     */
    showWarning(message, details) {
        return this.unifiedResponse(ResponseType.WARNING, message, details);
    }
    /**
     * Show error message
     */
    showError(message, error) {
        const details = {};
        if (error) {
            details.error = error.message || String(error);
            if (error.stack && this.chatConfig.showDetailedResponses) {
                details.stack = error.stack.split('\n').slice(0, 3).join('\n');
            }
        }
        return this.unifiedResponse(ResponseType.ERROR, message, details);
    }
    /**
     * Show fallback mode message
     */
    showFallbackMode(reason, fallbackAction) {
        const details = {
            reason,
            fallbackAction,
            mode: this.chatConfig.fallbackMode
        };
        return this.unifiedResponse(ResponseType.FALLBACK, `Switching to fallback mode: ${reason}`, details);
    }
    /**
     * Show tool use message
     */
    showToolUse(toolName, parameters) {
        const details = {
            tool: toolName
        };
        if (parameters && this.chatConfig.showDetailedResponses) {
            details.parameters = parameters;
        }
        return this.unifiedResponse(ResponseType.TOOL_USE, `Using tool: ${toolName}`, details);
    }
    /**
     * Show info message
     */
    showInfo(message, details) {
        return this.unifiedResponse(ResponseType.INFO, message, details);
    }
    /**
     * Show debug message
     */
    showDebug(message, details) {
        return this.unifiedResponse(ResponseType.DEBUG, message, details);
    }
    // History management methods
    /**
     * Get response history
     */
    getResponseHistory() {
        return [...this.responseHistory]; // Return copy to prevent external modification
    }
    /**
     * Get formatted response history
     */
    getFormattedHistory(limit) {
        const history = limit
            ? this.responseHistory.slice(-limit)
            : this.responseHistory;
        return history
            .map(entry => entry.formattedResponse)
            .join('\n');
    }
    /**
     * Clear response history
     */
    clearHistory() {
        this.responseHistory = [];
    }
    /**
     * Export response history
     */
    exportHistory() {
        return JSON.stringify(this.responseHistory, null, 2);
    }
    /**
     * Update chat configuration
     */
    updateChatConfig(config) {
        Object.assign(this.chatConfig, config);
    }
    /**
     * Get current chat configuration
     */
    getChatConfig() {
        return { ...this.chatConfig };
    }
}
exports.UnifiedChatMixin = UnifiedChatMixin;


/***/ }),

/***/ "./src/services/ClaudeCodeService.ts":
/*!*******************************************!*\
  !*** ./src/services/ClaudeCodeService.ts ***!
  \*******************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {


var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.ClaudeCodeService = void 0;
exports.getClaudeCodeService = getClaudeCodeService;
/**
 * ClaudeCodeService - Integration with Claude Code CLI
 * Based on claude-code-chat implementation
 *
 * Requires: npm install -g @anthropic-ai/claude-code
 * This installs the 'claude' CLI command that this service uses
 */
const vscode = __importStar(__webpack_require__(/*! vscode */ "vscode"));
const child_process_1 = __webpack_require__(/*! child_process */ "child_process");
const events_1 = __webpack_require__(/*! events */ "events");
class ClaudeCodeService extends events_1.EventEmitter {
    constructor() {
        super();
        this.currentProcess = null;
        this.seenToolsInSession = null;
        this.pendingTools = new Map(); // Store tool calls by ID
        this.toolResults = new Map(); // Store tool results by ID
        this.toolGroupBuffer = []; // Buffer for grouping similar tools
        this.lastToolName = null;
        this.hasStartedTextOutput = false;
        this.outputChannel = vscode.window.createOutputChannel('Claude Code Service');
    }
    /**
     * Send a message to Claude using the Claude Code CLI with JSON streaming
     */
    async sendMessage(message, options = {}) {
        // Try simple text mode first as fallback
        try {
            return await this.sendStreamJsonMessage(message, options);
        }
        catch (error) {
            this.outputChannel.appendLine('[ClaudeCodeService] Stream JSON failed, falling back to text mode');
            return await this.sendSimpleMessage(message, options);
        }
    }
    /**
     * Send a message using simple text output (more reliable)
     */
    async sendSimpleMessage(message, options = {}) {
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
                const claudeProcess = (0, child_process_1.spawn)('claude', args, {
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
                            metadata: {}
                        });
                    }
                    else {
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
            }
            catch (error) {
                reject(error);
            }
        });
    }
    /**
     * Send a message with streaming support for real-time updates
     */
    async sendStreamingMessage(message, options = {}) {
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
                const claudeProcess = (0, child_process_1.spawn)('claude', args, {
                    shell: process.platform === 'win32',
                    stdio: ['pipe', 'pipe', 'pipe']
                });
                this.currentProcess = claudeProcess;
                let responseContent = '';
                let metadata = {};
                let hasReceivedText = false;
                let toolUseDetected = false;
                let buffer = '';
                const seenTools = new Set(); // Track tools to prevent duplicates
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
                            }
                            catch (error) {
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
                    }
                    else {
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
            }
            catch (error) {
                reject(error);
            }
        });
    }
    /**
     * Send a message using stream JSON output (advanced)
     */
    async sendStreamJsonMessage(message, options = {}) {
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
                const claudeProcess = (0, child_process_1.spawn)('claude', args, {
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
                let metadata = {};
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
                            }
                            catch (error) {
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
                    }
                    else {
                        reject(new Error(`Claude process exited with code ${code} and no response`));
                    }
                });
                // Handle process error
                claudeProcess.on('error', (error) => {
                    this.currentProcess = null;
                    if (error.message.includes('ENOENT')) {
                        reject(new Error('Claude Code CLI not found. Please install it with: npm install -g @anthropic-ai/claude-code'));
                    }
                    else {
                        reject(error);
                    }
                });
                // Send the message
                if (claudeProcess.stdin) {
                    claudeProcess.stdin.write(message + '\n');
                    claudeProcess.stdin.end();
                }
                else {
                    reject(new Error('Failed to write to Claude process stdin'));
                }
            }
            catch (error) {
                reject(error);
            }
        });
    }
    /**
     * Clean tool markers from content before sending to UI
     */
    cleanToolMarkers(content) {
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
    processJsonStreamData(data, callback) {
        // Handle Claude Code CLI specific events
        if (data.type === 'system') {
            // Handle different system subtypes
            if (data.subtype === 'init') {
                this.outputChannel.appendLine(`[ClaudeCodeService] System init: ${JSON.stringify(data.tools || []).substring(0, 100)}`);
                if (data.session_id) {
                    callback(null, { sessionId: data.session_id });
                }
                // Don't send initialization message to avoid clutter
            }
            else if (data.subtype === 'error') {
                this.outputChannel.appendLine(`[ClaudeCodeService] System error: ${data.message || 'Unknown error'}`);
                // Clean error messages too
                const cleanError = `\n⚠️ **System Error:** ${data.message || 'An unexpected error occurred'}\n`;
                callback(cleanError, null);
                callback(null, null, 'error');
            }
            else {
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
                    }
                    else if (content.type === 'tool_use') {
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
                        }
                        else {
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
                }
                else if (event.content_block.type === 'text') {
                    this.outputChannel.appendLine(`[ClaudeCodeService] Text block starting`);
                    // Flush any pending tool groups before starting text
                    this.flushToolGroup(callback);
                    this.hasStartedTextOutput = true;
                }
                else if (event.content_block.type === 'thinking') {
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
            const resultMetadata = {
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
        }
        else if (data.type === 'content') {
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
    async isAvailable() {
        return new Promise((resolve) => {
            this.outputChannel.appendLine('[ClaudeCodeService] Checking Claude Code CLI availability...');
            (0, child_process_1.exec)('which claude', (error, stdout, stderr) => {
                if (error) {
                    this.outputChannel.appendLine('[ClaudeCodeService] Claude Code CLI not found in PATH');
                    // Try another method
                    (0, child_process_1.exec)('claude --version', (error2, stdout2, stderr2) => {
                        if (error2) {
                            this.outputChannel.appendLine('[ClaudeCodeService] Claude Code CLI not available');
                            this.outputChannel.appendLine('[ClaudeCodeService] Install with: npm install -g @anthropic-ai/claude-code');
                            resolve(false);
                        }
                        else {
                            this.outputChannel.appendLine(`[ClaudeCodeService] Claude Code CLI found (version check): ${stdout2.trim()}`);
                            resolve(true);
                        }
                    });
                }
                else {
                    this.outputChannel.appendLine(`[ClaudeCodeService] Claude Code CLI found at: ${stdout.trim()}`);
                    // Also get version
                    (0, child_process_1.exec)('claude --version', (verError, verStdout) => {
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
    async testConnection() {
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
            }
            else {
                return {
                    success: false,
                    message: 'Claude CLI responded but with empty content'
                };
            }
        }
        catch (error) {
            const errorMsg = error.message;
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
    cancel() {
        if (this.currentProcess) {
            this.currentProcess.kill();
            this.currentProcess = null;
        }
    }
    /**
     * Flush grouped tools - send notification for grouped tools
     */
    flushToolGroup(callback) {
        if (this.toolGroupBuffer.length === 0)
            return;
        const toolName = this.toolGroupBuffer[0].name;
        let emoji = '🔧';
        let groupedMessage = '';
        // Get emoji for this tool type
        switch (toolName) {
            case 'TodoWrite':
                emoji = '📝';
                break;
            case 'Bash':
                emoji = '⚡';
                break;
            case 'Read':
                emoji = '📄';
                break;
            case 'Write':
            case 'Edit':
            case 'MultiEdit':
                emoji = '✏️';
                break;
            case 'Grep':
                emoji = '🔍';
                break;
            case 'Glob':
                emoji = '📁';
                break;
            case 'WebSearch':
                emoji = '🌐';
                break;
            case 'WebFetch':
                emoji = '🔗';
                break;
            case 'Task':
                emoji = '🤖';
                break;
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
        }
        else {
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
    formatToolDetails(toolName, input) {
        switch (toolName) {
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
    formatToolMessage(toolName, input) {
        let emoji = '🔧';
        let details = '';
        switch (toolName) {
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
    dispose() {
        this.cancel();
        this.outputChannel.dispose();
    }
}
exports.ClaudeCodeService = ClaudeCodeService;
// Singleton instance
let instance = null;
function getClaudeCodeService() {
    if (!instance) {
        instance = new ClaudeCodeService();
    }
    return instance;
}


/***/ }),

/***/ "./src/types/AgentConfiguration.ts":
/*!*****************************************!*\
  !*** ./src/types/AgentConfiguration.ts ***!
  \*****************************************/
/***/ ((__unused_webpack_module, exports) => {


/**
 * Agent Configuration Types for KI AutoAgent
 * Defines types for per-agent model selection and instruction management
 */
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.DEFAULT_AGENT_MODELS = exports.AVAILABLE_MODELS = void 0;
// Available Models Configuration
exports.AVAILABLE_MODELS = {
    // Claude Models (2025)
    'claude-opus-4-1-20250805': {
        name: 'Claude Opus 4.1',
        provider: 'anthropic',
        tier: 'supreme',
        strengths: ['reasoning', 'conflict-resolution', 'judgment'],
        costPerMillion: { input: 15, output: 75 }
    },
    'claude-sonnet-4-20250514': {
        name: 'Claude Sonnet 4',
        provider: 'anthropic',
        tier: 'premium',
        strengths: ['coding', 'analysis', 'implementation'],
        costPerMillion: { input: 3, output: 15 }
    },
    'claude-3-7-sonnet-20250219': {
        name: 'Claude 3.7 Sonnet',
        provider: 'anthropic',
        tier: 'standard',
        strengths: ['thinking', 'extended-reasoning'],
        costPerMillion: { input: 3, output: 15 }
    },
    // OpenAI Models (2024)
    'gpt-4o-2024-11-20': {
        name: 'GPT-4o (Latest)',
        provider: 'openai',
        tier: 'premium',
        strengths: ['multimodal', 'architecture', 'planning'],
        costPerMillion: { input: 2.5, output: 10 }
    },
    'gpt-4o-mini-2024-07-18': {
        name: 'GPT-4o Mini',
        provider: 'openai',
        tier: 'efficient',
        strengths: ['fast-responses', 'cost-effective', 'review'],
        costPerMillion: { input: 0.15, output: 0.6 }
    },
    // Perplexity Models
    'llama-3.1-sonar-small-128k-online': {
        name: 'Llama 3.1 Sonar (Online)',
        provider: 'perplexity',
        tier: 'research',
        strengths: ['web-search', 'real-time-data', 'research'],
        costPerMillion: { input: 0.2, output: 0.2 }
    }
};
// Default Agent-Model Mappings
exports.DEFAULT_AGENT_MODELS = {
    'orchestrator': 'claude-sonnet-4-20250514',
    'richter': 'claude-opus-4-1-20250805', // Supreme Judge needs Opus
    'architect': 'gpt-4o-2024-11-20', // Architecture planning
    'codesmith': 'claude-sonnet-4-20250514', // Best for coding
    'tradestrat': 'claude-sonnet-4-20250514', // Trading analysis
    'research': 'llama-3.1-sonar-small-128k-online' // Web research
};


/***/ }),

/***/ "./src/types/Memory.ts":
/*!*****************************!*\
  !*** ./src/types/Memory.ts ***!
  \*****************************/
/***/ ((__unused_webpack_module, exports) => {


/**
 * Memory Types for the Multi-Agent System
 * Defines the structure of different memory types and operations
 */
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.MemoryType = void 0;
var MemoryType;
(function (MemoryType) {
    MemoryType["WORKING"] = "working";
    MemoryType["EPISODIC"] = "episodic";
    MemoryType["SEMANTIC"] = "semantic";
    MemoryType["PROCEDURAL"] = "procedural"; // How to do things
})(MemoryType || (exports.MemoryType = MemoryType = {}));


/***/ }),

/***/ "./src/ui/ChatWidget.ts":
/*!******************************!*\
  !*** ./src/ui/ChatWidget.ts ***!
  \******************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {


var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.ChatWidget = void 0;
/**
 * ChatWidget - Status bar widget for KI AutoAgent Chat
 * Provides quick access to the chat panel from VS Code status bar
 */
const vscode = __importStar(__webpack_require__(/*! vscode */ "vscode"));
const MultiAgentChatPanel_1 = __webpack_require__(/*! ./MultiAgentChatPanel */ "./src/ui/MultiAgentChatPanel.ts");
class ChatWidget {
    constructor(context, dispatcher) {
        this.context = context;
        this.dispatcher = dispatcher;
        this.unreadCount = 0;
        this.lastMessage = '';
        // Create status bar item (right side, high priority)
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 1000 // High priority to appear on the right
        );
        this.updateStatusBar();
        this.statusBarItem.show();
        // Register commands
        this.registerCommands();
        // Add to subscriptions
        context.subscriptions.push(this.statusBarItem);
    }
    registerCommands() {
        // Toggle chat command
        const toggleCommand = vscode.commands.registerCommand('ki-autoagent.toggleChat', () => this.toggleChat());
        // Quick chat command (opens quick input)
        const quickChatCommand = vscode.commands.registerCommand('ki-autoagent.quickChat', () => this.showQuickChat());
        // Clear unread command
        const clearUnreadCommand = vscode.commands.registerCommand('ki-autoagent.clearUnread', () => this.clearUnreadCount());
        this.context.subscriptions.push(toggleCommand, quickChatCommand, clearUnreadCommand);
    }
    updateStatusBar() {
        // Build status bar text
        let text = '$(comment-discussion) KI Chat';
        if (this.unreadCount > 0) {
            text = `$(comment-discussion) KI Chat (${this.unreadCount})`;
            // Add warning background for unread messages
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
            // Start pulse animation
            if (!this.pulseInterval) {
                this.startPulseAnimation();
            }
        }
        else {
            // Clear background when no unread
            this.statusBarItem.backgroundColor = undefined;
            // Stop pulse animation
            if (this.pulseInterval) {
                this.stopPulseAnimation();
            }
        }
        this.statusBarItem.text = text;
        this.statusBarItem.command = 'ki-autoagent.toggleChat';
        // Update tooltip
        if (this.lastMessage) {
            this.statusBarItem.tooltip = new vscode.MarkdownString(`**KI AutoAgent Chat**\n\n` +
                `Last message: _${this.truncateMessage(this.lastMessage)}_\n\n` +
                `Click to open chat • Right-click for options`);
        }
        else {
            this.statusBarItem.tooltip = new vscode.MarkdownString(`**KI AutoAgent Chat**\n\n` +
                `Click to open multi-agent chat interface\n\n` +
                `Features:\n` +
                `• Chat with specialized AI agents\n` +
                `• Auto-routing to best agent\n` +
                `• Multi-agent workflows\n\n` +
                `Click to open • Right-click for options`);
        }
    }
    startPulseAnimation() {
        let isPulsing = false;
        this.pulseInterval = setInterval(() => {
            if (isPulsing) {
                this.statusBarItem.text = this.statusBarItem.text.replace('🔴', '$(comment-discussion)');
            }
            else {
                this.statusBarItem.text = this.statusBarItem.text.replace('$(comment-discussion)', '🔴');
            }
            isPulsing = !isPulsing;
        }, 1000);
    }
    stopPulseAnimation() {
        if (this.pulseInterval) {
            clearInterval(this.pulseInterval);
            this.pulseInterval = undefined;
            this.updateStatusBar();
        }
    }
    toggleChat() {
        const panel = MultiAgentChatPanel_1.MultiAgentChatPanel.createOrShow(this.context.extensionUri, this.dispatcher);
        this.clearUnreadCount();
        return panel;
    }
    async showQuickChat() {
        // Show quick input for fast message sending
        const message = await vscode.window.showInputBox({
            placeHolder: 'Type your message for KI AutoAgent...',
            prompt: 'Send a quick message to the AI agents',
            ignoreFocusOut: false
        });
        if (message) {
            // Open chat and send message
            const panel = this.toggleChat();
            if (panel) {
                // Send message to panel
                panel.addMessage({
                    role: 'user',
                    content: message,
                    timestamp: new Date().toISOString()
                });
                // Process the message (this would normally go through the dispatcher)
                setTimeout(() => {
                    panel.addMessage({
                        role: 'assistant',
                        content: 'Processing your request...',
                        agent: 'orchestrator',
                        timestamp: new Date().toISOString()
                    });
                }, 100);
            }
        }
    }
    updateUnreadCount(count) {
        this.unreadCount = count;
        this.updateStatusBar();
    }
    incrementUnread() {
        this.unreadCount++;
        this.updateStatusBar();
    }
    clearUnreadCount() {
        this.unreadCount = 0;
        this.updateStatusBar();
    }
    setLastMessage(message, agent) {
        this.lastMessage = agent ? `[${agent}] ${message}` : message;
        this.updateStatusBar();
    }
    truncateMessage(message, maxLength = 50) {
        if (message.length <= maxLength) {
            return message;
        }
        return message.substring(0, maxLength) + '...';
    }
    showNotification(message, agent) {
        // Show notification when chat is not open
        if (!MultiAgentChatPanel_1.MultiAgentChatPanel.currentPanel) {
            vscode.window.showInformationMessage(`KI Agent ${agent}: ${this.truncateMessage(message, 100)}`, 'Open Chat', 'Dismiss').then(selection => {
                if (selection === 'Open Chat') {
                    this.toggleChat();
                }
            });
            // Increment unread count
            this.incrementUnread();
            this.setLastMessage(message, agent);
        }
    }
    dispose() {
        if (this.pulseInterval) {
            clearInterval(this.pulseInterval);
        }
        this.statusBarItem.dispose();
    }
}
exports.ChatWidget = ChatWidget;


/***/ }),

/***/ "./src/ui/MultiAgentChatPanel.ts":
/*!***************************************!*\
  !*** ./src/ui/MultiAgentChatPanel.ts ***!
  \***************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {


var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.MultiAgentChatPanel = void 0;
/**
 * MultiAgentChatPanel - Main chat interface for KI AutoAgent
 * Provides a webview-based chat interface with agent selection and mode switching
 */
const vscode = __importStar(__webpack_require__(/*! vscode */ "vscode"));
const ConversationContextManager_1 = __webpack_require__(/*! ../core/ConversationContextManager */ "./src/core/ConversationContextManager.ts");
class MultiAgentChatPanel {
    // Singleton pattern für Panel
    static createOrShow(extensionUri, dispatcher) {
        const column = vscode.ViewColumn.Two;
        if (MultiAgentChatPanel.currentPanel) {
            MultiAgentChatPanel.currentPanel._panel.reveal(column);
            if (dispatcher) {
                MultiAgentChatPanel.currentPanel._dispatcher = dispatcher;
            }
            return MultiAgentChatPanel.currentPanel;
        }
        const panel = vscode.window.createWebviewPanel('multiAgentChat', 'KI AutoAgent Chat', column, {
            enableScripts: true,
            retainContextWhenHidden: true,
            localResourceRoots: [
                vscode.Uri.joinPath(extensionUri, 'media'),
                vscode.Uri.joinPath(extensionUri, 'src', 'ui', 'webview')
            ]
        });
        MultiAgentChatPanel.currentPanel = new MultiAgentChatPanel(panel, extensionUri, dispatcher);
        return MultiAgentChatPanel.currentPanel;
    }
    constructor(panel, extensionUri, dispatcher) {
        this._disposables = [];
        this._messages = [];
        this._currentAgent = 'orchestrator';
        this._currentMode = 'auto';
        this._panel = panel;
        this._extensionUri = extensionUri;
        this._dispatcher = dispatcher;
        this._contextManager = ConversationContextManager_1.ConversationContextManager.getInstance();
        // Set the webview's initial html content
        this._update();
        // Listen for when the panel is disposed
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        // Handle messages from the webview
        this._panel.webview.onDidReceiveMessage(message => this._handleWebviewMessage(message), null, this._disposables);
        // Restore messages when panel becomes visible
        this._panel.onDidChangeViewState(e => {
            if (this._panel.visible) {
                // Don't reset the HTML, just restore messages
                this._restoreMessages();
            }
        }, null, this._disposables);
    }
    _update() {
        const webview = this._panel.webview;
        this._panel.title = "KI AutoAgent Chat";
        this._panel.iconPath = vscode.Uri.joinPath(this._extensionUri, 'media', 'multi-agent-logo.svg');
        this._panel.webview.html = this._getHtmlForWebview(webview);
    }
    _getHtmlForWebview(webview) {
        // Local path to css styles
        const styleResetUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'reset.css'));
        const styleVSCodeUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'vscode.css'));
        // Add cache buster to force reload
        const cacheBuster = Date.now();
        const styleChatUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'src', 'ui', 'webview', 'chat-fixed.css')) + `?v=${cacheBuster}`;
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'src', 'ui', 'webview', 'chat.js'));
        // Use a nonce to only allow specific scripts to be run
        const nonce = getNonce();
        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="${styleResetUri}" rel="stylesheet">
                <link href="${styleVSCodeUri}" rel="stylesheet">
                <link href="${styleChatUri}" rel="stylesheet">
                <title>KI AutoAgent Chat</title>
            </head>
            <body>
                <div id="chat-container">
                    <!-- Minimalist Header -->
                    <div id="chat-header">
                        <h3>KI AutoAgent Chat</h3>
                        <button id="settings-btn" title="Settings">⚙️</button>
                    </div>
                    
                    <!-- Messages Container -->
                    <div id="messages-container">
                        <div class="welcome-message">
                            <h2>Welcome to KI AutoAgent</h2>
                            <p>Start a conversation with our AI agents</p>
                        </div>
                    </div>
                    
                    <!-- Input Section with Bottom Controls -->
                    <div id="input-section">
                        <!-- Action buttons above input -->
                        <div id="action-buttons">
                            <button id="plan-first-btn" class="action-btn" title="Plan before implementing">
                                📋 Plan First
                            </button>
                            <button id="thinking-mode-btn" class="action-btn toggle" title="Enable thinking mode">
                                💭 Thinking
                            </button>
                            <button id="stop-btn" class="action-btn danger" title="Stop current operation">
                                ⏹ Stop
                            </button>
                        </div>
                        
                        <textarea id="message-input" 
                                  placeholder="Message KI AutoAgent..."
                                  rows="3"></textarea>
                        
                        <div id="bottom-controls">
                            <div id="mode-selector">
                                <button class="mode-option active" data-agent="auto" title="Automatic agent selection">
                                    🤖 Auto
                                </button>
                                <button class="mode-option" data-agent="architect" title="System architecture & design">
                                    🏗️ Architect
                                </button>
                                <button class="mode-option" data-agent="codesmith" title="Code implementation">
                                    💻 CodeSmith
                                </button>
                                <button class="mode-option" data-agent="tradestrat" title="Trading strategies">
                                    📈 TradeStrat
                                </button>
                                <button class="mode-option" data-agent="research" title="Web research">
                                    🔍 Research
                                </button>
                                <button class="mode-option" data-agent="opus" title="Conflict resolution">
                                    ⚖️ Opus
                                </button>
                            </div>
                            
                            <button id="send-btn" title="Send message">
                                Send
                            </button>
                        </div>
                    </div>
                </div>
                <script nonce="${nonce}" src="${scriptUri}"></script>
            </body>
            </html>`;
    }
    async _handleWebviewMessage(message) {
        switch (message.command) {
            case 'sendMessage':
                await this._processUserMessage(message.text, message.agent, message.mode);
                break;
            case 'changeAgent':
                this._currentAgent = message.agent;
                vscode.window.showInformationMessage(`Switched to ${message.agent}`);
                break;
            case 'changeMode':
                this._currentMode = message.mode;
                vscode.window.showInformationMessage(`Mode changed to ${message.mode}`);
                break;
            case 'clearChat':
                this._messages = [];
                break;
            case 'quickAction':
                await this._handleQuickAction(message.action);
                break;
            case 'planFirst':
                await this._handlePlanFirst(message.text, message.agent, message.mode);
                break;
        }
    }
    async _processUserMessage(text, agent, mode) {
        console.log(`\n💬 [CHAT] ============== NEW MESSAGE ==============`);
        console.log(`💬 [CHAT] User text: "${text}"`);
        console.log(`💬 [CHAT] Selected agent: "${agent}"`);
        console.log(`💬 [CHAT] Selected mode: "${mode}"`);
        console.log(`💬 [CHAT] Current agent field: "${this._currentAgent}"`);
        console.log(`💬 [CHAT] Current mode field: "${this._currentMode}"`);
        // Add user message
        const userMessage = {
            role: 'user',
            content: text,
            timestamp: new Date().toISOString()
        };
        this._messages.push(userMessage);
        // Save to conversation history
        this._contextManager.addEntry({
            timestamp: new Date().toISOString(),
            agent: 'user',
            step: 'input',
            input: text,
            output: '',
            metadata: { mode, selectedAgent: agent }
        });
        this._panel.webview.postMessage({
            type: 'addMessage',
            message: userMessage
        });
        // Show typing indicator
        this._panel.webview.postMessage({
            type: 'showTyping',
            agent: agent
        });
        // Debug dispatcher state
        console.log(`🔧 [CHAT] Dispatcher check: ${this._dispatcher ? 'AVAILABLE' : 'NOT AVAILABLE'}`);
        if (this._dispatcher) {
            console.log(`🔧 [CHAT] Dispatcher type: ${typeof this._dispatcher}`);
            console.log(`🔧 [CHAT] Dispatcher has processRequest: ${typeof this._dispatcher.processRequest}`);
            console.log(`🔧 [CHAT] Dispatcher has getAgentStats: ${typeof this._dispatcher.getAgentStats}`);
            try {
                const stats = await this._dispatcher.getAgentStats();
                console.log(`🔧 [CHAT] Agent stats keys: [${Object.keys(stats).join(', ')}]`);
                console.log(`🔧 [CHAT] Agent stats count: ${Object.keys(stats).length}`);
            }
            catch (error) {
                console.error(`🔧 [CHAT] Error getting agent stats: ${error}`);
            }
        }
        else {
            console.error(`🔧 [CHAT] CRITICAL: No dispatcher available!`);
        }
        try {
            console.log(`🎯 [CHAT MODE] Decision tree:`);
            console.log(`🎯 [CHAT MODE] - mode === 'auto': ${mode === 'auto'}`);
            console.log(`🎯 [CHAT MODE] - mode === 'single': ${mode === 'single'}`);
            console.log(`🎯 [CHAT MODE] - mode === 'workflow': ${mode === 'workflow'}`);
            console.log(`🎯 [CHAT MODE] - this._dispatcher exists: ${!!this._dispatcher}`);
            // Process based on mode
            if (mode === 'auto' && this._dispatcher) {
                console.log(`🎯 [CHAT MODE] ✅ Entering AUTO mode with orchestrator`);
                // Create streaming message for orchestrator
                const streamingMessageId = `streaming-${Date.now()}`;
                this._addStreamingMessage(streamingMessageId, 'orchestrator');
                // Show immediate feedback
                this._updateStreamingMessage(streamingMessageId, '🎭 Analyzing your request...\n', false);
                // Use orchestrator with streaming
                const response = await this._callAgentWithStreaming('orchestrator', text, streamingMessageId);
                // Finalize the streaming message
                this._finalizeStreamingMessage(streamingMessageId, response.content, response.metadata);
                // Save to conversation history
                this._contextManager.addEntry({
                    timestamp: new Date().toISOString(),
                    agent: 'orchestrator',
                    step: 'orchestration',
                    input: text,
                    output: response.content,
                    metadata: response.metadata
                });
            }
            else if (mode === 'single') {
                console.log(`🎯 [CHAT MODE] ✅ Entering SINGLE mode with agent: "${agent}"`);
                console.log(`🎯 [CHAT MODE] Agent value type: ${typeof agent}`);
                console.log(`🎯 [CHAT MODE] Agent exact value: '${agent}'`);
                console.log(`🎯 [CHAT MODE] Agent length: ${agent?.length}`);
                // Create a streaming message placeholder
                const streamingMessageId = `streaming-${Date.now()}`;
                this._addStreamingMessage(streamingMessageId, agent);
                // Direct chat with selected agent
                const response = await this._callAgentWithStreaming(agent, text, streamingMessageId);
                // Finalize the streaming message with metadata
                this._finalizeStreamingMessage(streamingMessageId, response.content, response.metadata);
            }
            else if (mode === 'workflow') {
                console.log(`🎯 [CHAT MODE] ✅ Entering WORKFLOW mode`);
                // Multi-agent workflow - show inter-agent communication
                await this._processWorkflow(text);
            }
            else {
                console.error(`🎯 [CHAT MODE] ❌ No valid mode path! Defaulting to error message`);
                this._addErrorMessage(`Invalid mode configuration: mode="${mode}", agent="${agent}", dispatcher=${!!this._dispatcher}`);
            }
        }
        catch (error) {
            console.error('[DEBUG] Error in _processUserMessage:', error);
            this._addErrorMessage(`Error: ${error.message}`);
        }
        finally {
            this._panel.webview.postMessage({
                type: 'hideTyping'
            });
        }
    }
    async _callAgent(agentId, prompt) {
        console.log(`\n🤖 [CALL AGENT] ====================================`);
        console.log(`🤖 [CALL AGENT] AgentId: "${agentId}"`);
        console.log(`🤖 [CALL AGENT] Prompt: "${prompt.substring(0, 100)}..."`);
        console.log(`🤖 [CALL AGENT] Dispatcher available: ${!!this._dispatcher}`);
        if (!this._dispatcher) {
            const errorMsg = 'Error: No dispatcher available. Please check agent configuration.';
            console.error(`🤖 [CALL AGENT] ❌ ${errorMsg}`);
            return {
                content: errorMsg,
                metadata: null
            };
        }
        console.log(`🤖 [CALL AGENT] Dispatcher type: ${typeof this._dispatcher}`);
        console.log(`🤖 [CALL AGENT] Dispatcher.processRequest: ${typeof this._dispatcher.processRequest}`);
        try {
            // Create task request for the dispatcher
            const taskRequest = {
                prompt: prompt,
                command: agentId, // Use agent ID as command
                context: await this._getWorkspaceContext()
            };
            console.log('[DEBUG] Created taskRequest:', JSON.stringify(taskRequest, null, 2));
            console.log('[DEBUG] Calling dispatcher.processRequest...');
            // Call the real dispatcher
            const result = await this._dispatcher.processRequest(taskRequest);
            console.log('[DEBUG] Dispatcher returned:', JSON.stringify(result, null, 2));
            if (result.status === 'success' || result.status === 'partial_success') {
                return {
                    content: result.content,
                    metadata: result.metadata
                };
            }
            else {
                return {
                    content: `Error: ${result.content}`,
                    metadata: null
                };
            }
        }
        catch (error) {
            const errorMsg = `Agent Error: ${error.message}\nStack: ${error.stack}`;
            console.error('[DEBUG]', errorMsg);
            return {
                content: errorMsg,
                metadata: null
            };
        }
    }
    async _callAgentWithStreaming(agentId, prompt, messageId) {
        console.log(`\n🤖 [CALL AGENT WITH STREAMING] ====================================`);
        console.log(`🤖 [STREAMING] AgentId: "${agentId}"`);
        console.log(`🤖 [STREAMING] AgentId type: ${typeof agentId}`);
        console.log(`🤖 [STREAMING] AgentId exact: '${agentId}'`);
        console.log(`🤖 [STREAMING] MessageId: "${messageId}"`);
        console.log(`🤖 [STREAMING] Creating task request with command: '${agentId}'`);
        if (!this._dispatcher) {
            const errorMsg = 'Error: No dispatcher available. Please check agent configuration.';
            console.error(`🤖 [STREAMING] ❌ ${errorMsg}`);
            return {
                content: errorMsg,
                metadata: null
            };
        }
        try {
            let fullContent = '';
            // Get conversation history for context
            const conversationHistory = this._contextManager.getFormattedContext(10);
            // Create task request with streaming callback and conversation history
            const taskRequest = {
                prompt: prompt,
                command: agentId,
                context: await this._getWorkspaceContext(),
                globalContext: conversationHistory,
                onPartialResponse: (partialContent) => {
                    console.log(`🤖 [STREAMING] Partial content: ${partialContent.length} chars`);
                    // Check if this is a workflow step notification
                    if (partialContent.includes('🔄 **Step')) {
                        // Send as a separate system message
                        const stepMatch = partialContent.match(/🔄 \*\*Step (\d+)\/(\d+)\*\*: @(\w+) - (.+)/);
                        if (stepMatch) {
                            const [, current, total, agent, description] = stepMatch;
                            this._addSystemMessage(`🔄 Step ${current}/${total}: @${agent} - ${description}`);
                        }
                    }
                    else if (partialContent.includes('✅ Completed:')) {
                        // Don't add completion previews to the main message
                        // They will be shown in the final agent response
                        return;
                    }
                    else {
                        // Extract and process tool markers with agent context
                        const currentAgent = agentId; // Agent executing the tools
                        let cleanedContent = partialContent;
                        // Extract <<TOOL>> markers and create tool notifications with agent color
                        const toolMatches = [...partialContent.matchAll(/<<TOOL>>(.*?)<<TOOL_END>>/gs)];
                        for (const match of toolMatches) {
                            const toolContent = match[1];
                            this._addToolNotification(toolContent, currentAgent, messageId);
                            cleanedContent = cleanedContent.replace(match[0], '');
                        }
                        // Clean other markers
                        cleanedContent = cleanedContent
                            .replace(/<<TOOL_RESULT>>.*?<<TOOL_RESULT_END>>/gs, '')
                            .replace(/<<THINKING>>.*?<<THINKING_END>>/gs, '')
                            .replace(/🛠️ \*?Claude is using tools.*?\*?\n*/g, '');
                        // Check for new system tool message format
                        if (cleanedContent.includes('SYSTEM_TOOL_MESSAGE:')) {
                            const parts = cleanedContent.split('SYSTEM_TOOL_MESSAGE:');
                            if (parts[1]) {
                                this._addToolNotification(parts[1], currentAgent, messageId);
                                cleanedContent = parts[0];
                            }
                        }
                        // Only add text content if there's actual content after cleaning
                        if (cleanedContent.trim().length > 0) {
                            fullContent += cleanedContent;
                            this._updateStreamingMessage(messageId, cleanedContent);
                        }
                    }
                }
            };
            // Call the dispatcher
            const result = await this._dispatcher.processRequest(taskRequest);
            // Use accumulated content if available, otherwise use result content
            const finalContent = fullContent || result.content;
            // Save agent response to conversation history
            if (finalContent) {
                this._contextManager.addEntry({
                    timestamp: new Date().toISOString(),
                    agent: agentId,
                    step: 'response',
                    input: prompt,
                    output: finalContent,
                    metadata: result.metadata
                });
            }
            if (result.status === 'success' || result.status === 'partial_success') {
                return {
                    content: finalContent,
                    metadata: result.metadata
                };
            }
            else {
                return {
                    content: `Error: ${result.content}`,
                    metadata: null
                };
            }
        }
        catch (error) {
            const errorMsg = `Agent Error: ${error.message}`;
            console.error('[STREAMING]', errorMsg);
            return {
                content: errorMsg,
                metadata: null
            };
        }
    }
    _addStreamingMessage(messageId, agent) {
        // Create initial streaming message
        const streamingMessage = {
            role: 'assistant',
            content: '',
            agent: agent,
            timestamp: new Date().toISOString(),
            isCollapsible: false,
            metadata: { messageId, isStreaming: true }
        };
        this._messages.push(streamingMessage);
        this._panel.webview.postMessage({
            type: 'addStreamingMessage',
            message: streamingMessage
        });
    }
    _updateStreamingMessage(messageId, partialContent, isToolNotification = false) {
        // Keep track of processed content
        let contentToAdd = partialContent;
        let hasToolNotifications = false;
        let needsNewBubble = false;
        // Check for thinking notifications
        while (contentToAdd.includes('<<THINKING>>') && contentToAdd.includes('<<THINKING_END>>')) {
            const thinkingMatch = contentToAdd.match(/<<THINKING>>(.*?)<<THINKING_END>>/s);
            if (thinkingMatch) {
                const thinkingContent = thinkingMatch[1];
                this._addSystemNotification('💭 ' + thinkingContent, messageId);
                contentToAdd = contentToAdd.replace(/<<THINKING>>.*?<<THINKING_END>>/s, '');
                hasToolNotifications = true;
            }
            else {
                break;
            }
        }
        // Check for tool notifications marked with special tags
        while (contentToAdd.includes('<<TOOL>>') && contentToAdd.includes('<<TOOL_END>>')) {
            const toolMatch = contentToAdd.match(/<<TOOL>>(.*?)<<TOOL_END>>/s);
            if (toolMatch) {
                const toolContent = toolMatch[1];
                const toolMsgId = this._addSystemNotification(toolContent, messageId);
                contentToAdd = contentToAdd.replace(/<<TOOL>>.*?<<TOOL_END>>/s, '');
                hasToolNotifications = true;
            }
            else {
                break;
            }
        }
        // Check for tool results to update existing tool notifications
        while (contentToAdd.includes('<<TOOL_RESULT>>') && contentToAdd.includes('<<TOOL_RESULT_END>>')) {
            const resultMatch = contentToAdd.match(/<<TOOL_RESULT>>(.*?)<<TOOL_RESULT_END>>/s);
            if (resultMatch) {
                const [toolId, result] = resultMatch[1].split('||');
                // Find and update the corresponding tool message
                this._updateToolResult(toolId, result);
                contentToAdd = contentToAdd.replace(/<<TOOL_RESULT>>.*?<<TOOL_RESULT_END>>/s, '');
            }
            else {
                break;
            }
        }
        // Check for text start marker
        if (contentToAdd.includes('<<TEXT_START>>')) {
            contentToAdd = contentToAdd.replace(/<<TEXT_START>>/g, '');
            needsNewBubble = true;
        }
        // Only update main message if there's content left after removing notifications
        if (contentToAdd.trim()) {
            // If we need a new bubble or don't have an existing message, create one
            let message = this._messages.find(m => m.metadata?.messageId === messageId && m.role === 'assistant');
            if (needsNewBubble && !message) {
                // Create a new assistant message bubble
                const newMessage = {
                    role: 'assistant',
                    content: contentToAdd,
                    agent: 'assistant',
                    timestamp: new Date().toISOString(),
                    metadata: { messageId: `${messageId}-text`, isStreaming: true }
                };
                this._messages.push(newMessage);
                this._panel.webview.postMessage({
                    type: 'addStreamingMessage',
                    message: newMessage
                });
            }
            else if (message) {
                // Update existing message
                message.content += contentToAdd;
                this._panel.webview.postMessage({
                    type: 'updateStreamingMessage',
                    messageId: message.metadata?.messageId || messageId,
                    partialContent: contentToAdd
                });
            }
        }
    }
    _isSpecialMessage(content) {
        // Check if content is a tool notification or special message
        const specialPatterns = [
            /^🚀 \*\*Claude is initializing/,
            /^🔧 \*\*Using tool:/,
            /^⚠️ \*\*System Error:/,
            /^✨ \*\*Tool:/,
            /^📝 \*\*Result:/,
            /^✅ \*\*Task completed:/
        ];
        return specialPatterns.some(pattern => pattern.test(content));
    }
    _addSystemNotification(content, parentMessageId) {
        // Add a small delay to ensure proper ordering of messages
        const messageId = `system-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const systemMessage = {
            role: 'system',
            content: content,
            timestamp: new Date().toISOString(),
            metadata: {
                isSystemNotification: true,
                parentMessageId: parentMessageId,
                messageId: messageId
            }
        };
        this._messages.push(systemMessage);
        // Send as a separate addMessage event to create a new bubble
        setTimeout(() => {
            this._panel.webview.postMessage({
                type: 'addMessage',
                message: systemMessage
            });
        }, 10);
        return messageId;
    }
    _updateToolResult(toolId, result) {
        // Find the last tool message and update it with the result
        for (let i = this._messages.length - 1; i >= 0; i--) {
            const message = this._messages[i];
            if (message.role === 'system' && message.content.includes(toolId)) {
                // Append result to the tool message
                if (!message.content.includes('**Result:**')) {
                    message.content += `\n\n**Result:**\n${result}`;
                    // Update the message in the webview
                    this._panel.webview.postMessage({
                        type: 'updateMessage',
                        messageId: message.metadata?.messageId,
                        content: message.content
                    });
                }
                break;
            }
        }
    }
    _finalizeStreamingMessage(messageId, fullContent, metadata) {
        // Find and finalize the streaming message
        const message = this._messages.find(m => m.metadata?.messageId === messageId);
        if (message) {
            // Update agent if metadata includes it (for workflow results)
            if (metadata?.agent) {
                message.agent = metadata.agent;
            }
            // Don't add metadata info to content, add it as a separate message
            message.content = fullContent;
            message.metadata = { ...message.metadata, ...metadata, isStreaming: false };
            message.isCollapsible = fullContent.length > 500;
            this._panel.webview.postMessage({
                type: 'finalizeStreamingMessage',
                messageId: messageId,
                fullContent: message.content,
                metadata: message.metadata,
                agent: message.agent
            });
            // Add metadata as a separate completion message if available
            if (metadata && (metadata.usage || metadata.cost || metadata.duration)) {
                this._addCompletionMessage(metadata);
            }
        }
    }
    _addCompletionMessage(metadata) {
        let completionContent = '✅ **Task completed successfully!**\n\n';
        // Add execution details
        if (metadata.duration) {
            completionContent += `⏱️ **Execution Time:** ${metadata.duration}\n`;
        }
        // Add token usage
        if (metadata.usage) {
            const inputTokens = metadata.usage.inputTokens || 0;
            const outputTokens = metadata.usage.outputTokens || 0;
            const totalTokens = inputTokens + outputTokens;
            completionContent += `📊 **Tokens Used:** ${totalTokens} (Input: ${inputTokens}, Output: ${outputTokens})\n`;
        }
        // Add cost if available
        if (metadata.cost) {
            completionContent += `💰 **Cost:** $${metadata.cost.toFixed(4)}\n`;
        }
        // Add cache info if available
        if (metadata.usage?.cacheCreationInputTokens || metadata.usage?.cacheReadInputTokens) {
            const cacheCreation = metadata.usage.cacheCreationInputTokens || 0;
            const cacheRead = metadata.usage.cacheReadInputTokens || 0;
            completionContent += `💾 **Cache:** ${cacheCreation} created, ${cacheRead} read\n`;
        }
        const completionMessage = {
            role: 'system',
            content: completionContent,
            timestamp: new Date().toISOString(),
            metadata: {
                isCompletionMessage: true,
                ...metadata
            }
        };
        this._messages.push(completionMessage);
        this._panel.webview.postMessage({
            type: 'addMessage',
            message: completionMessage
        });
    }
    _buildMetadataInfo(metadata) {
        let metadataInfo = '';
        // Token usage
        if (metadata?.usage) {
            const inputTokens = metadata.usage.inputTokens || 0;
            const outputTokens = metadata.usage.outputTokens || 0;
            const cacheCreation = metadata.usage.cacheCreationInputTokens || 0;
            const cacheRead = metadata.usage.cacheReadInputTokens || 0;
            const totalTokens = inputTokens + outputTokens;
            metadataInfo += `\n\n---\n📊 **Tokens**: ${totalTokens} total (Input: ${inputTokens}, Output: ${outputTokens})`;
            if (cacheCreation > 0 || cacheRead > 0) {
                metadataInfo += `\n💾 **Cache**: ${cacheCreation} created, ${cacheRead} read`;
            }
        }
        // Cost and performance
        if (metadata?.totalCostUsd !== undefined) {
            metadataInfo += `\n💰 **Cost**: $${metadata.totalCostUsd.toFixed(6)}`;
        }
        if (metadata?.durationMs !== undefined) {
            metadataInfo += `\n⏱️ **Duration**: ${metadata.durationMs}ms`;
            if (metadata?.durationApiMs !== undefined) {
                metadataInfo += ` (API: ${metadata.durationApiMs}ms)`;
            }
        }
        // Session and model info
        if (metadata?.model) {
            metadataInfo += `\n🤖 **Model**: ${metadata.model}`;
        }
        if (metadata?.sessionId) {
            metadataInfo += `\n🔗 **Session**: ${metadata.sessionId.substring(0, 8)}...`;
        }
        // Stop reason
        if (metadata?.stopReason) {
            metadataInfo += `\n⚡ **Stop reason**: ${metadata.stopReason}`;
        }
        return metadataInfo;
    }
    async _getWorkspaceContext() {
        return {
            activeEditor: vscode.window.activeTextEditor,
            workspaceRoots: vscode.workspace.workspaceFolders,
            openDocuments: vscode.workspace.textDocuments,
            selectedText: vscode.window.activeTextEditor?.document.getText(vscode.window.activeTextEditor.selection),
            currentFile: vscode.window.activeTextEditor?.document.fileName
        };
    }
    async _processWorkflow(prompt) {
        // Simulate a multi-agent workflow
        const workflow = [
            { agent: 'orchestrator', action: 'Analyzing request...' },
            { agent: 'architect', action: 'Designing solution architecture...' },
            { agent: 'codesmith', action: 'Implementing code...' },
            { agent: 'reviewer', action: 'Reviewing implementation...' }
        ];
        for (const step of workflow) {
            // Show agent-to-agent communication
            const agentMessage = {
                role: 'agent-to-agent',
                content: step.action,
                agent: step.agent,
                timestamp: new Date().toISOString(),
                isCollapsible: true
            };
            this._messages.push(agentMessage);
            this._panel.webview.postMessage({
                type: 'addMessage',
                message: agentMessage
            });
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        // Final response
        this._addAgentResponse('Workflow completed successfully!', 'orchestrator');
    }
    _addAgentResponse(content, agent, metadata) {
        console.log(`📝 [ADD RESPONSE] Adding agent response`);
        console.log(`📝 [ADD RESPONSE] Content length: ${content?.length || 0}`);
        console.log(`📝 [ADD RESPONSE] Agent: ${agent}`);
        console.log(`📝 [ADD RESPONSE] Metadata:`, metadata);
        // Build comprehensive metadata info
        let metadataInfo = '';
        // Token usage
        if (metadata?.usage) {
            const inputTokens = metadata.usage.inputTokens || 0;
            const outputTokens = metadata.usage.outputTokens || 0;
            const cacheCreation = metadata.usage.cacheCreationInputTokens || 0;
            const cacheRead = metadata.usage.cacheReadInputTokens || 0;
            const totalTokens = inputTokens + outputTokens;
            metadataInfo += `\n\n---\n📊 **Tokens**: ${totalTokens} total (Input: ${inputTokens}, Output: ${outputTokens})`;
            if (cacheCreation > 0 || cacheRead > 0) {
                metadataInfo += `\n💾 **Cache**: ${cacheCreation} created, ${cacheRead} read`;
            }
        }
        // Cost and performance
        if (metadata?.totalCostUsd !== undefined) {
            metadataInfo += `\n💰 **Cost**: $${metadata.totalCostUsd.toFixed(6)}`;
        }
        if (metadata?.durationMs !== undefined) {
            metadataInfo += `\n⏱️ **Duration**: ${metadata.durationMs}ms`;
            if (metadata?.durationApiMs !== undefined) {
                metadataInfo += ` (API: ${metadata.durationApiMs}ms)`;
            }
        }
        // Session and model info
        if (metadata?.model) {
            metadataInfo += `\n🤖 **Model**: ${metadata.model}`;
        }
        if (metadata?.sessionId) {
            metadataInfo += `\n🔗 **Session**: ${metadata.sessionId.substring(0, 8)}...`;
        }
        // Stop reason
        if (metadata?.stopReason) {
            metadataInfo += `\n⚡ **Stop reason**: ${metadata.stopReason}`;
        }
        const assistantMessage = {
            role: 'assistant',
            content: content + metadataInfo,
            agent: agent,
            timestamp: new Date().toISOString(),
            isCollapsible: content.length > 500,
            metadata: metadata
        };
        this._messages.push(assistantMessage);
        console.log(`📝 [ADD RESPONSE] Final message to send:`, assistantMessage);
        console.log(`📝 [ADD RESPONSE] Total messages in history: ${this._messages.length}`);
        const postResult = this._panel.webview.postMessage({
            type: 'addMessage',
            message: assistantMessage
        });
        console.log(`📝 [ADD RESPONSE] postMessage result:`, postResult);
    }
    _addSystemMessage(content) {
        const systemMessage = {
            role: 'system',
            content: content,
            timestamp: new Date().toISOString()
        };
        this._messages.push(systemMessage);
        this._panel.webview.postMessage({
            type: 'addMessage',
            message: systemMessage
        });
    }
    _addToolNotification(content, agentName, relatedMessageId) {
        const toolMsgId = `tool_${Date.now()}_${Math.random()}`;
        // Get agent-specific color based on normalized agent name
        const normalizedAgent = agentName.toLowerCase().replace('agent', '').replace('gpt', '').replace('claude', '');
        const agentColor = this._getAgentColor(normalizedAgent);
        const agentEmoji = this._getAgentEmoji(normalizedAgent);
        const toolMessage = {
            role: 'system',
            content: content,
            agent: agentName,
            timestamp: new Date().toISOString(),
            metadata: {
                isToolNotification: true,
                relatedMessageId,
                toolMsgId,
                agentColor,
                agentEmoji,
                agentName
            }
        };
        this._messages.push(toolMessage);
        // Send to WebView with tool notification flag
        this._panel.webview.postMessage({
            type: 'addMessage',
            message: toolMessage
        });
        return toolMsgId;
    }
    _getAgentColor(agent) {
        const colors = {
            'orchestrator': '#8B5CF6', // Purple
            'architect': '#10B981', // Emerald Green (changed from blue)
            'codesmith': '#F97316', // Orange
            'research': '#EAB308', // Gold
            'tradestrat': '#14B8A6', // Turquoise
            'opusarbitrator': '#DC2626', // Crimson
            'docubot': '#6366F1', // Indigo
            'reviewer': '#EC4899', // Pink
            'fixer': '#8B5CF6' // Purple
        };
        return colors[agent.toLowerCase()] || '#3B82F6'; // Default to blue for system
    }
    _getAgentEmoji(agent) {
        const emojis = {
            'orchestrator': '🎯',
            'architect': '🏗️',
            'codesmith': '🛠️',
            'research': '🔍',
            'tradestrat': '📈',
            'opusarbitrator': '⚖️',
            'docubot': '📚',
            'reviewer': '🔎',
            'fixer': '🔧'
        };
        return emojis[agent.toLowerCase()] || '🤖';
    }
    _addErrorMessage(content) {
        const errorMessage = {
            role: 'system',
            content: content,
            timestamp: new Date().toISOString()
        };
        this._messages.push(errorMessage);
        this._panel.webview.postMessage({
            type: 'addMessage',
            message: errorMessage
        });
    }
    _restoreMessages() {
        // Send all stored messages back to the webview
        if (this._messages.length > 0) {
            this._panel.webview.postMessage({
                type: 'restoreMessages',
                messages: this._messages
            });
        }
    }
    async _handleQuickAction(action) {
        switch (action) {
            case 'help':
                this._addAgentResponse(`## KI AutoAgent Help\n\n` +
                    `**Modes:**\n` +
                    `- **Auto**: Automatically routes to the best agent\n` +
                    `- **Single**: Direct chat with selected agent\n` +
                    `- **Workflow**: Multi-agent collaboration\n\n` +
                    `**Commands:**\n` +
                    `- Type your question and press Enter\n` +
                    `- Use Shift+Enter for multiline input\n` +
                    `- Select agents from dropdown\n`, 'system');
                break;
            case 'examples':
                this._addAgentResponse(`## Example Prompts\n\n` +
                    `**Architecture:**\n` +
                    `"Design a microservices architecture for an e-commerce platform"\n\n` +
                    `**Coding:**\n` +
                    `"Implement a REST API with FastAPI and PostgreSQL"\n\n` +
                    `**Trading:**\n` +
                    `"Create a momentum trading strategy with risk management"\n\n` +
                    `**Research:**\n` +
                    `"Find the latest best practices for React performance optimization"\n`, 'system');
                break;
            case 'agents':
                this._addAgentResponse(`## Available Agents\n\n` +
                    `🤖 **Orchestrator**: Automatic task routing\n` +
                    `🏗️ **ArchitectGPT**: System design and architecture\n` +
                    `💻 **CodeSmithClaude**: Code implementation\n` +
                    `📈 **TradeStrat**: Trading strategies\n` +
                    `🔍 **ResearchBot**: Web research\n` +
                    `⚖️ **OpusRichter**: Quality judgment\n` +
                    `📝 **DocuBot**: Documentation\n` +
                    `👁️ **ReviewerGPT**: Code review\n` +
                    `🔧 **FixerBot**: Bug fixing\n`, 'system');
                break;
        }
    }
    async _handlePlanFirst(text, agent, mode) {
        // Add user message with plan request
        const planPrompt = `PLAN FIRST: ${text}\n\nPlease provide a detailed plan before implementing. Break down the task into clear steps.`;
        const userMessage = {
            role: 'user',
            content: planPrompt,
            timestamp: new Date().toISOString()
        };
        this._messages.push(userMessage);
        this._panel.webview.postMessage({
            type: 'addMessage',
            message: userMessage
        });
        // Save to conversation history
        this._contextManager.addEntry({
            timestamp: new Date().toISOString(),
            agent: 'user',
            step: 'plan_request',
            input: planPrompt,
            output: '',
            metadata: { mode, selectedAgent: agent, isPlanFirst: true }
        });
        // Process with agent
        this._panel.webview.postMessage({
            type: 'showTyping',
            agent: agent
        });
        try {
            // Force single agent mode for planning
            const streamingMessageId = `streaming-${Date.now()}`;
            this._addStreamingMessage(streamingMessageId, agent);
            const response = await this._callAgentWithStreaming(agent === 'auto' ? 'codesmith' : agent, planPrompt, streamingMessageId);
            this._finalizeStreamingMessage(streamingMessageId, response.content, response.metadata);
        }
        catch (error) {
            console.error('[PLAN FIRST] Error:', error);
            this._addErrorMessage(`Error: ${error.message}`);
        }
        finally {
            this._panel.webview.postMessage({
                type: 'hideTyping'
            });
        }
    }
    addMessage(message) {
        this._messages.push(message);
        this._panel.webview.postMessage({
            type: 'addMessage',
            message: message
        });
    }
    dispose() {
        MultiAgentChatPanel.currentPanel = undefined;
        this._panel.dispose();
        while (this._disposables.length) {
            const x = this._disposables.pop();
            if (x) {
                x.dispose();
            }
        }
    }
}
exports.MultiAgentChatPanel = MultiAgentChatPanel;
function getNonce() {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}


/***/ }),

/***/ "./src/utils/AnthropicService.ts":
/*!***************************************!*\
  !*** ./src/utils/AnthropicService.ts ***!
  \***************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {


var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.AnthropicService = void 0;
/**
 * Anthropic Service for Claude model interactions
 */
const vscode = __importStar(__webpack_require__(/*! vscode */ "vscode"));
class AnthropicService {
    constructor() {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        this.apiKey = config.get('anthropic.apiKey', '');
        this.baseURL = 'https://api.anthropic.com/v1';
    }
    async chat(messages, model = 'claude-3-5-sonnet-20241022', maxTokens = 4000, temperature = 0.7) {
        if (!this.apiKey) {
            throw new Error('Anthropic API key not configured');
        }
        // Anthropic expects system message separate from messages
        const systemMessage = messages.find(m => m.role === 'system');
        const conversationMessages = messages.filter(m => m.role !== 'system');
        const requestBody = {
            model,
            max_tokens: maxTokens,
            temperature,
            system: systemMessage?.content || '',
            messages: conversationMessages.map(msg => ({
                role: msg.role,
                content: msg.content
            }))
        };
        try {
            const response = await fetch(`${this.baseURL}/messages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': this.apiKey,
                    'anthropic-version': '2023-06-01'
                },
                body: JSON.stringify(requestBody)
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: { message: response.statusText } }));
                throw new Error(`Anthropic API error: ${errorData.error?.message || response.statusText}`);
            }
            const data = await response.json();
            if (!data.content || data.content.length === 0) {
                throw new Error('No response from Anthropic API');
            }
            // Extract text from content blocks
            return data.content
                .filter(block => block.type === 'text')
                .map(block => block.text)
                .join('');
        }
        catch (error) {
            if (error instanceof Error) {
                throw error;
            }
            throw new Error(`Anthropic API request failed: ${error}`);
        }
    }
    async streamChat(messages, onChunk, model = 'claude-3-5-sonnet-20241022', maxTokens = 4000, temperature = 0.7) {
        if (!this.apiKey) {
            throw new Error('Anthropic API key not configured');
        }
        const systemMessage = messages.find(m => m.role === 'system');
        const conversationMessages = messages.filter(m => m.role !== 'system');
        const requestBody = {
            model,
            max_tokens: maxTokens,
            temperature,
            system: systemMessage?.content || '',
            messages: conversationMessages.map(msg => ({
                role: msg.role,
                content: msg.content
            })),
            stream: true
        };
        try {
            const response = await fetch(`${this.baseURL}/messages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': this.apiKey,
                    'anthropic-version': '2023-06-01'
                },
                body: JSON.stringify(requestBody)
            });
            if (!response.ok) {
                throw new Error(`Anthropic API error: ${response.statusText}`);
            }
            const reader = response.body?.getReader();
            if (!reader) {
                throw new Error('Failed to get response stream');
            }
            const decoder = new TextDecoder();
            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    break;
                }
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n').filter(line => line.trim() !== '');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.substring(6);
                        if (data === '[DONE]') {
                            return;
                        }
                        try {
                            const parsed = JSON.parse(data);
                            if (parsed.type === 'content_block_delta') {
                                const text = parsed.delta?.text;
                                if (text) {
                                    onChunk(text);
                                }
                            }
                        }
                        catch (error) {
                            // Ignore parsing errors for incomplete chunks
                        }
                    }
                }
            }
        }
        catch (error) {
            throw new Error(`Anthropic streaming failed: ${error}`);
        }
    }
    validateApiKey() {
        return !!this.apiKey && this.apiKey.startsWith('sk-ant-');
    }
    async testConnection() {
        try {
            await this.chat([
                { role: 'user', content: 'Test connection' }
            ], 'claude-3-5-sonnet-20241022', 10);
            return true;
        }
        catch (error) {
            return false;
        }
    }
}
exports.AnthropicService = AnthropicService;


/***/ }),

/***/ "./src/utils/OpenAIService.ts":
/*!************************************!*\
  !*** ./src/utils/OpenAIService.ts ***!
  \************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {


var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.OpenAIService = void 0;
/**
 * OpenAI Service for GPT model interactions
 */
const vscode = __importStar(__webpack_require__(/*! vscode */ "vscode"));
class OpenAIService {
    constructor() {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        this.apiKey = config.get('openai.apiKey', '');
        this.baseURL = 'https://api.openai.com/v1';
    }
    async chat(messages, model = 'gpt-4o', maxTokens = 4000, temperature = 0.7) {
        if (!this.apiKey) {
            throw new Error('OpenAI API key not configured');
        }
        const requestBody = {
            model,
            messages,
            max_tokens: maxTokens,
            temperature,
            stream: false
        };
        try {
            const response = await fetch(`${this.baseURL}/chat/completions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.apiKey}`
                },
                body: JSON.stringify(requestBody)
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: { message: response.statusText } }));
                throw new Error(`OpenAI API error: ${errorData.error?.message || response.statusText}`);
            }
            const data = await response.json();
            if (!data.choices || data.choices.length === 0) {
                throw new Error('No response from OpenAI API');
            }
            return data.choices[0].message.content;
        }
        catch (error) {
            if (error instanceof Error) {
                throw error;
            }
            throw new Error(`OpenAI API request failed: ${error}`);
        }
    }
    async streamChat(messages, onChunk, model = 'gpt-4o', maxTokens = 4000, temperature = 0.7) {
        if (!this.apiKey) {
            throw new Error('OpenAI API key not configured');
        }
        const requestBody = {
            model,
            messages,
            max_tokens: maxTokens,
            temperature,
            stream: true
        };
        try {
            const response = await fetch(`${this.baseURL}/chat/completions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.apiKey}`
                },
                body: JSON.stringify(requestBody)
            });
            if (!response.ok) {
                throw new Error(`OpenAI API error: ${response.statusText}`);
            }
            const reader = response.body?.getReader();
            if (!reader) {
                throw new Error('Failed to get response stream');
            }
            const decoder = new TextDecoder();
            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    break;
                }
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n').filter(line => line.trim() !== '');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.substring(6);
                        if (data === '[DONE]') {
                            return;
                        }
                        try {
                            const parsed = JSON.parse(data);
                            const content = parsed.choices?.[0]?.delta?.content;
                            if (content) {
                                onChunk(content);
                            }
                        }
                        catch (error) {
                            // Ignore parsing errors for incomplete chunks
                        }
                    }
                }
            }
        }
        catch (error) {
            throw new Error(`OpenAI streaming failed: ${error}`);
        }
    }
    validateApiKey() {
        return !!this.apiKey && this.apiKey.startsWith('sk-');
    }
    async testConnection() {
        try {
            await this.chat([
                { role: 'user', content: 'Test connection' }
            ], 'gpt-4o-mini', 10);
            return true;
        }
        catch (error) {
            return false;
        }
    }
}
exports.OpenAIService = OpenAIService;


/***/ }),

/***/ "./src/utils/WebSearchService.ts":
/*!***************************************!*\
  !*** ./src/utils/WebSearchService.ts ***!
  \***************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {


var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.WebSearchService = void 0;
/**
 * Web Search Service for real-time research and information gathering
 */
const vscode = __importStar(__webpack_require__(/*! vscode */ "vscode"));
class WebSearchService {
    constructor() {
        this.config = vscode.workspace.getConfiguration('kiAutoAgent');
    }
    async search(query) {
        const webAccessEnabled = this.config.get('webAccess.enabled', true);
        if (!webAccessEnabled) {
            throw new Error('Web access is disabled in settings');
        }
        const searchEngine = this.config.get('webAccess.searchEngine', 'perplexity');
        const maxResults = this.config.get('webAccess.maxResults', 5);
        switch (searchEngine) {
            case 'perplexity':
                return await this.searchWithPerplexity(query, maxResults);
            case 'tavily':
                return await this.searchWithTavily(query, maxResults);
            case 'serp':
                return await this.searchWithSERP(query, maxResults);
            case 'custom':
                return await this.searchWithCustom(query, maxResults);
            default:
                throw new Error(`Unknown search engine: ${searchEngine}`);
        }
    }
    async searchWithPerplexity(query, maxResults) {
        const apiKey = this.config.get('perplexity.apiKey');
        if (!apiKey) {
            throw new Error('Perplexity API key not configured');
        }
        try {
            const response = await fetch('https://api.perplexity.ai/chat/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`
                },
                body: JSON.stringify({
                    model: 'llama-3.1-sonar-small-128k-online',
                    messages: [
                        {
                            role: 'system',
                            content: 'You are a helpful research assistant. Provide comprehensive information with sources.'
                        },
                        {
                            role: 'user',
                            content: `Research and provide detailed information about: ${query}`
                        }
                    ],
                    max_tokens: 1000,
                    temperature: 0.2,
                    return_citations: true
                })
            });
            if (!response.ok) {
                throw new Error(`Perplexity API error: ${response.statusText}`);
            }
            const data = await response.json();
            const content = data.choices[0]?.message?.content || '';
            const citations = data.citations || [];
            // Convert Perplexity response to SearchResponse format
            const results = citations.slice(0, maxResults).map((citation, index) => ({
                title: `Source ${index + 1}`,
                url: citation.url || '',
                snippet: citation.text || '',
                content: content
            }));
            // If no citations but we have content, create a general result
            if (results.length === 0 && content) {
                results.push({
                    title: 'Perplexity Research Result',
                    url: 'https://perplexity.ai',
                    snippet: content.substring(0, 200) + '...',
                    content: content
                });
            }
            return {
                query,
                results,
                totalResults: results.length
            };
        }
        catch (error) {
            throw new Error(`Perplexity search failed: ${error}`);
        }
    }
    async searchWithTavily(query, maxResults) {
        const apiKey = this.config.get('tavily.apiKey');
        if (!apiKey) {
            throw new Error('Tavily API key not configured');
        }
        try {
            const response = await fetch('https://api.tavily.com/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    api_key: apiKey,
                    query: query,
                    search_depth: 'advanced',
                    include_answer: true,
                    include_images: false,
                    include_raw_content: true,
                    max_results: maxResults
                })
            });
            if (!response.ok) {
                throw new Error(`Tavily API error: ${response.statusText}`);
            }
            const data = await response.json();
            const results = (data.results || []).map((result) => ({
                title: result.title || '',
                url: result.url || '',
                snippet: result.content || '',
                content: result.raw_content || result.content
            }));
            return {
                query,
                results,
                totalResults: data.results?.length || 0
            };
        }
        catch (error) {
            throw new Error(`Tavily search failed: ${error}`);
        }
    }
    async searchWithSERP(query, maxResults) {
        const apiKey = this.config.get('serp.apiKey');
        if (!apiKey) {
            throw new Error('SERP API key not configured');
        }
        try {
            const url = new URL('https://serpapi.com/search');
            url.searchParams.append('q', query);
            url.searchParams.append('api_key', apiKey);
            url.searchParams.append('engine', 'google');
            url.searchParams.append('num', maxResults.toString());
            const response = await fetch(url.toString());
            if (!response.ok) {
                throw new Error(`SERP API error: ${response.statusText}`);
            }
            const data = await response.json();
            const results = (data.organic_results || []).map((result) => ({
                title: result.title || '',
                url: result.link || '',
                snippet: result.snippet || '',
                content: result.snippet || ''
            }));
            return {
                query,
                results,
                totalResults: data.organic_results?.length || 0
            };
        }
        catch (error) {
            throw new Error(`SERP search failed: ${error}`);
        }
    }
    async searchWithCustom(query, maxResults) {
        const endpoint = this.config.get('customSearch.endpoint');
        const apiKey = this.config.get('customSearch.apiKey');
        if (!endpoint) {
            throw new Error('Custom search endpoint not configured');
        }
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(apiKey && { 'Authorization': `Bearer ${apiKey}` })
                },
                body: JSON.stringify({
                    query,
                    max_results: maxResults
                })
            });
            if (!response.ok) {
                throw new Error(`Custom search API error: ${response.statusText}`);
            }
            const data = await response.json();
            // Assume custom API returns results in our expected format
            return {
                query,
                results: data.results || [],
                totalResults: data.total_results || 0
            };
        }
        catch (error) {
            throw new Error(`Custom search failed: ${error}`);
        }
    }
    async isWebAccessAvailable() {
        const webAccessEnabled = this.config.get('webAccess.enabled', true);
        if (!webAccessEnabled) {
            return false;
        }
        const searchEngine = this.config.get('webAccess.searchEngine', 'perplexity');
        switch (searchEngine) {
            case 'perplexity':
                return !!this.config.get('perplexity.apiKey');
            case 'tavily':
                return !!this.config.get('tavily.apiKey');
            case 'serp':
                return !!this.config.get('serp.apiKey');
            case 'custom':
                return !!this.config.get('customSearch.endpoint');
            default:
                return false;
        }
    }
    getSearchEngineStatus() {
        const searchEngine = this.config.get('webAccess.searchEngine', 'perplexity');
        switch (searchEngine) {
            case 'perplexity':
                return {
                    engine: 'Perplexity',
                    configured: !!this.config.get('perplexity.apiKey')
                };
            case 'tavily':
                return {
                    engine: 'Tavily',
                    configured: !!this.config.get('tavily.apiKey')
                };
            case 'serp':
                return {
                    engine: 'SERP API',
                    configured: !!this.config.get('serp.apiKey')
                };
            case 'custom':
                return {
                    engine: 'Custom',
                    configured: !!this.config.get('customSearch.endpoint')
                };
            default:
                return {
                    engine: searchEngine,
                    configured: false,
                    error: 'Unknown search engine'
                };
        }
    }
}
exports.WebSearchService = WebSearchService;


/***/ }),

/***/ "child_process":
/*!********************************!*\
  !*** external "child_process" ***!
  \********************************/
/***/ ((module) => {

module.exports = require("child_process");

/***/ }),

/***/ "events":
/*!*************************!*\
  !*** external "events" ***!
  \*************************/
/***/ ((module) => {

module.exports = require("events");

/***/ }),

/***/ "fs/promises":
/*!******************************!*\
  !*** external "fs/promises" ***!
  \******************************/
/***/ ((module) => {

module.exports = require("fs/promises");

/***/ }),

/***/ "path":
/*!***********************!*\
  !*** external "path" ***!
  \***********************/
/***/ ((module) => {

module.exports = require("path");

/***/ }),

/***/ "vscode":
/*!*************************!*\
  !*** external "vscode" ***!
  \*************************/
/***/ ((module) => {

module.exports = require("vscode");

/***/ })

/******/ 	});
/************************************************************************/
/******/ 	// The module cache
/******/ 	var __webpack_module_cache__ = {};
/******/ 	
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/ 		// Check if module is in cache
/******/ 		var cachedModule = __webpack_module_cache__[moduleId];
/******/ 		if (cachedModule !== undefined) {
/******/ 			return cachedModule.exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = __webpack_module_cache__[moduleId] = {
/******/ 			// no module.id needed
/******/ 			// no module.loaded needed
/******/ 			exports: {}
/******/ 		};
/******/ 	
/******/ 		// Execute the module function
/******/ 		__webpack_modules__[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/ 	
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/ 	
/************************************************************************/
/******/ 	
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	// This entry module is referenced by other modules so it can't be inlined
/******/ 	var __webpack_exports__ = __webpack_require__("./src/extension.ts");
/******/ 	module.exports = __webpack_exports__;
/******/ 	
/******/ })()
;
//# sourceMappingURL=extension.js.map