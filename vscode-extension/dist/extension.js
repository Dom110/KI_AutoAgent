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
            description: 'System Architecture & Design Expert powered by GPT-4o',
            model: 'gpt-4o',
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
            description: 'Senior Python/Web Developer powered by Claude 3.5 Sonnet',
            model: 'claude-3.5-sonnet',
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
                { name: 'optimize', description: 'Optimize existing code for performance', handler: 'handleOptimizeCommand' },
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
            model: 'claude-opus-4-1-20250805',
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
 * Orchestrator Agent - Universal AI assistant that routes tasks to specialized agents
 * This is the main entry point that users interact with
 */
const vscode = __importStar(__webpack_require__(/*! vscode */ "vscode"));
const ChatAgent_1 = __webpack_require__(/*! ./base/ChatAgent */ "./src/agents/base/ChatAgent.ts");
const OpenAIService_1 = __webpack_require__(/*! ../utils/OpenAIService */ "./src/utils/OpenAIService.ts");
class OrchestratorAgent extends ChatAgent_1.ChatAgent {
    constructor(context, dispatcher) {
        const config = {
            participantId: 'ki-autoagent.orchestrator',
            name: 'ki',
            fullName: 'KI AutoAgent Orchestrator',
            description: 'Universal AI assistant that automatically routes tasks to specialized agents',
            model: 'gpt-4o',
            iconPath: vscode.Uri.joinPath(context.extensionUri, 'media', 'orchestrator-icon.svg'),
            capabilities: [
                'Intent Recognition',
                'Agent Orchestration',
                'Workflow Management',
                'Project Type Detection',
                'Multi-Agent Coordination'
            ],
            commands: [
                { name: 'task', description: 'Execute a development task with automatic agent selection', handler: 'handleTaskCommand' },
                { name: 'agents', description: 'Show available specialized agents', handler: 'handleAgentsCommand' },
                { name: 'workflow', description: 'Create a multi-step development workflow', handler: 'handleWorkflowCommand' }
            ]
        };
        super(config, context, dispatcher);
        this.openAIService = new OpenAIService_1.OpenAIService();
    }
    async handleRequest(request, context, stream, token) {
        const command = request.command;
        const prompt = request.prompt;
        this.log(`Orchestrator processing ${command ? `/${command}` : 'general'} request: ${prompt.substring(0, 100)}...`);
        if (command) {
            await this.handleCommand(command, prompt, stream, token);
        }
        else {
            // General orchestration - the main flow
            await this.handleGeneralRequest(prompt, stream, token);
        }
    }
    async processWorkflowStep(step, request, previousResults) {
        // Orchestrator doesn't typically process individual steps
        // It coordinates other agents
        return {
            status: 'success',
            content: `Orchestrator coordinated step: ${step.description}`,
            metadata: {
                step: step.id,
                agent: 'orchestrator'
            }
        };
    }
    // Main orchestration logic
    async handleGeneralRequest(prompt, stream, token) {
        stream.progress('🧠 Analyzing task and selecting optimal agents...');
        try {
            // Step 1: Detect intent and project type
            const intent = await this.dispatcher.detectIntent(prompt);
            const workspaceContext = await this.dispatcher.getWorkspaceContext();
            const projectType = await this.dispatcher.detectProjectType(workspaceContext);
            // Show analysis
            stream.markdown(`## 🎯 Task Analysis\n\n`);
            stream.markdown(`**Intent:** ${intent.type} (Confidence: ${(intent.confidence * 100).toFixed(0)}%)\n`);
            stream.markdown(`**Primary Agent:** @${intent.agent}\n`);
            stream.markdown(`**Project Type:** ${projectType}\n\n`);
            // Step 2: Create workflow
            const workflow = this.dispatcher.createWorkflow(intent, projectType);
            if (workflow.length > 1) {
                stream.markdown(`## 🔄 Execution Workflow\n\n`);
                workflow.forEach((step, index) => {
                    stream.markdown(`${index + 1}. **@${step.agent}**: ${step.description}\n`);
                });
                stream.markdown('\n');
            }
            // Step 3: Execute workflow
            stream.progress('⚡ Executing workflow...');
            const taskRequest = {
                prompt,
                context: workspaceContext,
                projectType
            };
            const result = await this.dispatcher.executeWorkflow(workflow, taskRequest);
            // Step 4: Display results
            stream.markdown(`## 📤 Results\n\n`);
            stream.markdown(result.content);
            // Step 5: Add action buttons
            if (result.suggestions && result.suggestions.length > 0) {
                stream.markdown(`## 💡 Suggested Actions\n\n`);
                result.suggestions.forEach(suggestion => {
                    this.createActionButton(suggestion.title, 'ki-autoagent.applySuggestion', [suggestion.data], stream);
                });
            }
            // Step 6: Add file references
            if (result.references && result.references.length > 0) {
                stream.markdown(`## 📁 Referenced Files\n\n`);
                result.references.forEach(uri => {
                    stream.reference(uri);
                });
            }
            // Step 7: Offer follow-up actions
            this.createActionButton('📊 Show Agent Statistics', 'ki-autoagent.showAgentStats', [], stream);
        }
        catch (error) {
            stream.markdown(`❌ **Error during orchestration**: ${error.message}\n\n`);
            // Fallback to single agent
            stream.markdown(`💡 **Fallback**: Routing to @codesmith for direct assistance...\n\n`);
            // You could implement fallback logic here
            await this.handleFallback(prompt, stream, token);
        }
    }
    // Command Handlers
    async handleTaskCommand(prompt, stream, token) {
        stream.markdown(`## 📋 Task Execution\n\n`);
        stream.markdown(`**Task:** ${prompt}\n\n`);
        // Same as general request but with explicit task framing
        await this.handleGeneralRequest(prompt, stream, token);
    }
    async handleAgentsCommand(prompt, stream, token) {
        stream.markdown(`## 🤖 Available Specialized Agents\n\n`);
        const agents = [
            { name: '@architect', fullName: 'ArchitectGPT', description: 'System Architecture & Design Expert', model: 'GPT-4o', specialties: 'Design, Architecture, Planning' },
            { name: '@codesmith', fullName: 'CodeSmithClaude', description: 'Senior Python/Web Developer', model: 'Claude Sonnet 4', specialties: 'Implementation, Testing, Optimization' },
            { name: '@docu', fullName: 'DocuBot', description: 'Technical Documentation Expert', model: 'GPT-4o', specialties: 'Docs, README, API Reference' },
            { name: '@reviewer', fullName: 'ReviewerGPT', description: 'Code Review & Security Expert', model: 'GPT-4o-mini', specialties: 'QA, Security, Performance' },
            { name: '@fixer', fullName: 'FixerBot', description: 'Bug Fixing & Optimization Expert', model: 'Claude Sonnet 4', specialties: 'Debugging, Patching, Refactoring' },
            { name: '@tradestrat', fullName: 'TradeStrat', description: 'Trading Strategy Expert', model: 'Claude Sonnet 4', specialties: 'Strategies, Backtesting, Risk' },
            { name: '@richter', fullName: 'OpusArbitrator', description: '⚖️ Supreme Quality Judge powered by Claude Opus 4.1', model: 'Claude Opus 4.1', specialties: 'Conflict Resolution, Supreme Decisions, Complex Reasoning' },
            { name: '@research', fullName: 'ResearchBot', description: 'Research & Information Expert', model: 'Perplexity Pro', specialties: 'Web Research, Documentation, Analysis' }
        ];
        for (const agent of agents) {
            stream.markdown(`### ${agent.name} - ${agent.fullName}\n`);
            stream.markdown(`**Model:** ${agent.model}\n`);
            stream.markdown(`**Description:** ${agent.description}\n`);
            stream.markdown(`**Specialties:** ${agent.specialties}\n\n`);
        }
        stream.markdown(`## 💡 Usage Examples\n\n`);
        stream.markdown(`- \`@architect design a microservices architecture\`\n`);
        stream.markdown(`- \`@codesmith implement a REST API with FastAPI\`\n`);
        stream.markdown(`- \`@tradestrat create a momentum trading strategy\`\n`);
        stream.markdown(`- \`@fixer debug this error message\`\n`);
        stream.markdown(`- \`@richter judge which solution is better\`\n`);
        stream.markdown(`- \`@research find the latest Python testing frameworks\`\n\n`);
        stream.markdown(`## 🔄 Automatic Routing\n\n`);
        stream.markdown(`You can also just describe your task naturally, and I'll automatically select the best agent(s) and create a workflow:\n\n`);
        stream.markdown(`- \`"Create a trading bot with risk management"\`\n`);
        stream.markdown(`- \`"Build a REST API for user management"\`\n`);
        stream.markdown(`- \`"Fix the performance issue in this function"\`\n`);
        // Get current agent stats
        try {
            const stats = await this.dispatcher.getAgentStats();
            if (Object.keys(stats).length > 0) {
                stream.markdown(`## 📊 Agent Statistics\n\n`);
                for (const [agentId, agentStats] of Object.entries(stats)) {
                    const { successRate, totalExecutions, averageResponseTime } = agentStats;
                    stream.markdown(`**${agentId}**: ${totalExecutions} executions, ${(successRate * 100).toFixed(1)}% success rate, ${averageResponseTime.toFixed(0)}ms avg response\n`);
                }
            }
        }
        catch (error) {
            // Stats not available yet
        }
    }
    async handleWorkflowCommand(prompt, stream, token) {
        stream.progress('📋 Creating multi-step workflow...');
        try {
            // Analyze the request to create a detailed workflow
            const context = await this.getWorkspaceContext();
            const systemPrompt = this.getWorkflowSystemPrompt();
            const userPrompt = `Create a detailed multi-step workflow for: ${prompt}\n\nWorkspace Context:\n${context}`;
            const response = await this.openAIService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);
            stream.markdown(`## 🔄 Generated Workflow\n\n`);
            stream.markdown(response);
            // Offer to execute the workflow
            this.createActionButton('⚡ Execute This Workflow', 'ki-autoagent.executeWorkflow', [prompt, response], stream);
        }
        catch (error) {
            stream.markdown(`❌ Error creating workflow: ${error.message}`);
        }
    }
    // Fallback handler
    async handleFallback(prompt, stream, token) {
        // Simple fallback using GPT-4o directly
        try {
            const systemPrompt = `You are a helpful coding assistant. Provide clear, actionable assistance for development tasks.

${this.getSystemContextPrompt()}`;
            const response = await this.openAIService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: prompt }
            ]);
            stream.markdown(response);
        }
        catch (error) {
            stream.markdown(`❌ Fallback also failed: ${error.message}`);
        }
    }
    // System prompts
    getWorkflowSystemPrompt() {
        return `You are a workflow planning expert. Create detailed, step-by-step workflows for development tasks.

For each workflow, provide:

## Workflow: [Task Name]

### Overview
Brief description of what this workflow accomplishes.

### Prerequisites
- Required tools, knowledge, or setup

### Steps
1. **Step Name** (@agent-name)
   - Detailed description
   - Expected deliverables
   - Dependencies

2. **Next Step** (@agent-name)
   - And so on...

### Success Criteria
- How to know the workflow is complete
- Quality checks

### Estimated Timeline
- Time estimates for each phase

Available agents:
- @architect (system design, architecture)
- @codesmith (implementation, testing)
- @docu (documentation)
- @reviewer (code review, security)
- @fixer (debugging, fixes)
- @tradestrat (trading strategies)
- @richter (supreme arbitrator, conflict resolution, final decisions)
- @research (web research, information)

Make workflows realistic, actionable, and well-structured.

${this.getSystemContextPrompt()}`;
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
            model: 'gpt-4o',
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
            description: 'Trading Strategy Expert powered by Claude 3.5 Sonnet',
            model: 'claude-3.5-sonnet',
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
            'opus-arbitrator': 'OpusArbitratorAgent'
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
        model: 'gpt-4o',
        instructionSet: 'orchestrator.md'
    },
    'architect': {
        specialization: 'System Architecture & Design',
        canHandle: ['architecture', 'design', 'patterns', 'scalability', 'tech-stack', 'system-design', 'database-design'],
        model: 'gpt-4o-2024-11-20',
        instructionSet: 'architect.md'
    },
    'codesmith': {
        specialization: 'Code Implementation & Optimization',
        canHandle: ['coding', 'implementation', 'optimization', 'testing', 'debugging', 'refactoring', 'code-review'],
        model: 'claude-sonnet-4-20250514',
        instructionSet: 'codesmith.md'
    },
    'tradestrat': {
        specialization: 'Trading Strategies & Financial Analysis',
        canHandle: ['trading', 'algorithms', 'financial', 'backtesting', 'market-analysis', 'portfolio', 'risk-management'],
        model: 'claude-sonnet-4-20250514',
        instructionSet: 'tradestrat.md'
    },
    'research': {
        specialization: 'Web Research & Information Gathering',
        canHandle: ['research', 'web-search', 'documentation', 'fact-checking', 'information-gathering', 'api-docs'],
        model: 'llama-3.1-sonar-small-128k-online',
        instructionSet: 'research.md'
    },
    'opus-arbitrator': {
        specialization: 'Agent Conflict Resolution',
        canHandle: ['conflicts', 'decision-making', 'arbitration', 'dispute-resolution', 'consensus'],
        model: 'claude-opus-4-1-20250805',
        instructionSet: 'richter.md'
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
        // Architecture patterns
        if (this.matchesPatterns(lowerPrompt, ['design', 'architecture', 'system', 'plan', 'structure'])) {
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
        // Default to implementation
        return { type: 'implementation', confidence: 0.5, agent: 'codesmith' };
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
        // Apply project-specific modifications
        if (projectDef?.workflow) {
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
                // Accumulate results
                finalResult.content += `## ${step.description}\n\n${stepResult.content}\n\n`;
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
// Multi-Agent Chat UI Components
const MultiAgentChatPanel_1 = __webpack_require__(/*! ./ui/MultiAgentChatPanel */ "./src/ui/MultiAgentChatPanel.ts");
const ChatWidget_1 = __webpack_require__(/*! ./ui/ChatWidget */ "./src/ui/ChatWidget.ts");
// TODO: Implement remaining agents
// import { DocuAgent } from './agents/DocuAgent';
// import { ReviewerAgent } from './agents/ReviewerAgent';
// import { FixerAgent } from './agents/FixerAgent';
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
                // Send a fancy initialization message
                const initMessage = `🚀 **Claude is initializing...** Ready to assist with advanced capabilities!\n\n`;
                callback(initMessage, null);
            }
            else if (data.subtype === 'error') {
                this.outputChannel.appendLine(`[ClaudeCodeService] System error: ${data.message || 'Unknown error'}`);
                callback(`\n⚠️ **System Error:** ${data.message || 'An unexpected error occurred'}\n`, null);
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
                        // Send tool result notification immediately
                        const truncatedResult = result.length > 300 ? result.substring(0, 300) + '...' : result;
                        callback(`<<TOOL_RESULT>>${content.tool_use_id}||${truncatedResult}<<TOOL_RESULT_END>>`, null);
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
                    // Send thinking notification as separate message
                    callback(`<<THINKING>>💭 **Thinking...**<<THINKING_END>>`, null);
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
                    // If stop reason is tool_use, notify user that Claude is working with tools
                    if (event.delta.stop_reason === 'tool_use') {
                        callback(`\n\n🛠️ *Claude is using tools to help with your request...*\n`, null);
                    }
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
        // Send the grouped notification only as a separate bubble
        callback(`<<TOOL>>${groupedMessage}<<TOOL_END>>`, null);
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
                // Use orchestrator for automatic routing
                const response = await this._callAgent('orchestrator', text);
                this._addAgentResponse(response.content, 'orchestrator', response.metadata);
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
                    fullContent += partialContent;
                    this._updateStreamingMessage(messageId, partialContent);
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
            // Don't add metadata info to content, add it as a separate message
            message.content = fullContent;
            message.metadata = { ...message.metadata, ...metadata, isStreaming: false };
            message.isCollapsible = fullContent.length > 500;
            this._panel.webview.postMessage({
                type: 'finalizeStreamingMessage',
                messageId: messageId,
                fullContent: message.content,
                metadata: message.metadata
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