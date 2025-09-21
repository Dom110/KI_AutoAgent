/**
 * ArchitectGPT - System Architecture & Design Expert
 * Powered by GPT-4o for system design and architecture planning
 */
import * as vscode from 'vscode';
import { ChatAgent } from './base/ChatAgent';
import { AgentConfig, TaskRequest, TaskResult, WorkflowStep } from '../types';
import { VSCodeMasterDispatcher } from '../core/VSCodeMasterDispatcher';
import { OpenAIService } from '../utils/OpenAIService';

export class ArchitectAgent extends ChatAgent {
    private openAIService: OpenAIService;

    constructor(context: vscode.ExtensionContext, dispatcher: VSCodeMasterDispatcher) {
        const config: AgentConfig = {
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
        this.openAIService = new OpenAIService();
    }

    protected async handleRequest(
        request: vscode.ChatRequest,
        context: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
        if (!this.validateApiConfig()) {
            stream.markdown('❌ OpenAI API key not configured. Please set it in VS Code settings.');
            return;
        }

        const command = request.command;
        const prompt = request.prompt;

        this.log(`Processing ${command ? `/${command}` : 'general'} request: ${prompt.substring(0, 100)}...`);

        if (command) {
            await this.handleCommand(command, prompt, stream, token);
        } else {
            // General architecture request
            await this.handleGeneralArchitectureRequest(prompt, stream, token);
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
            case 'analyze':
            case 'analyze_project':
                systemPrompt = this.getAnalyzeSystemPrompt();
                const analyzeContext = request.globalContext || '';
                userPrompt = `${analyzeContext ? `Conversation Context:\n${analyzeContext}\n\n` : ''}Analyze the architecture requirements for: ${request.prompt}\n\nWorkspace Context:\n${context}`;
                break;

            case 'design':
                systemPrompt = this.getDesignSystemPrompt();
                const conversationContext = request.globalContext || '';
                userPrompt = `${conversationContext ? `Conversation Context:\n${conversationContext}\n\n` : ''}Create a system architecture design for: ${request.prompt}\n\nPrevious Analysis:\n${this.extractPreviousContent(previousResults)}`;
                break;

            case 'synthesize_recommendations':
                systemPrompt = this.getSynthesisSystemPrompt();
                const synthesisContext = request.globalContext || '';
                userPrompt = `${synthesisContext ? `Conversation Context:\n${synthesisContext}\n\n` : ''}\nOriginal Request: ${request.prompt}\n\nFindings from previous steps:\n${this.extractPreviousContent(previousResults)}\n\nSynthesize all findings into comprehensive, actionable recommendations.`;
                break;

            default:
                systemPrompt = this.getGeneralSystemPrompt();
                const globalCtx = request.globalContext || '';
                userPrompt = `${globalCtx ? `Conversation History:\n${globalCtx}\n\n` : ''}${request.prompt}\n\nContext:\n${context}`;
        }

        try {
            let response = '';

            // Use streaming if callback provided and available
            if ((request as any).onPartialResponse && this.openAIService.streamChat) {
                await this.openAIService.streamChat(
                    [
                        { role: 'system', content: systemPrompt },
                        { role: 'user', content: userPrompt }
                    ],
                    (chunk: string) => {
                        response += chunk;
                        (request as any).onPartialResponse!(chunk);
                    }
                );
            } else {
                response = await this.openAIService.chat([
                    { role: 'system', content: systemPrompt },
                    { role: 'user', content: userPrompt }
                ]);
            }

            return {
                status: 'success',
                content: response,
                metadata: {
                    step: step.id,
                    agent: 'architect',
                    model: 'gpt-4o'
                }
            };

        } catch (error) {
            throw new Error(`Failed to process ${step.id}: ${(error as any).message}`);
        }
    }

    // Command Handlers

    private async handleDesignCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
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
            this.createActionButton(
                '📄 Create Architecture Document',
                'ki-autoagent.createFile',
                ['ARCHITECTURE.md', response],
                stream
            );

            // Offer to proceed with implementation planning
            this.createActionButton(
                '⚡ Plan Implementation',
                'ki-autoagent.planImplementation',
                [prompt, response],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ Error creating design: ${(error as any).message}`);
        }
    }

    private async handleAnalyzeCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
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
            this.createActionButton(
                '🚀 Suggest Improvements',
                'ki-autoagent.suggestImprovements',
                [response],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ Error analyzing architecture: ${(error as any).message}`);
        }
    }

    private async handlePlanCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
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
            this.createActionButton(
                '🗺️ Create Roadmap',
                'ki-autoagent.createFile',
                ['ROADMAP.md', response],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ Error creating plan: ${(error as any).message}`);
        }
    }

    private async handleGeneralArchitectureRequest(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
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

        } catch (error) {
            stream.markdown(`❌ Error processing request: ${(error as any).message}`);
        }
    }

    // System Prompts

    private getGeneralSystemPrompt(): string {
        return `You are ArchitectGPT, a senior system architect and design expert.

CORE RESPONSIBILITY:
You analyze and understand any software project by examining its codebase, then provide architectural guidance based on what you discover.

PROJECT DISCOVERY APPROACH:
1. **Analyze Project Structure**: Identify project type from files (package.json, requirements.txt, Cargo.toml, etc.)
2. **Detect Technology Stack**: Understand frameworks, libraries, and tools being used
3. **Find UI Components**: Locate and catalog existing UI elements if present
4. **Map Architecture**: Identify patterns (MVC, MVVM, microservices, etc.)
5. **Understand Context**: Use discovered information to provide relevant recommendations

You specialize in:
- System architecture design and patterns
- Technology stack selection and evaluation
- Component discovery and analysis
- Scalability and performance planning
- Database design and data modeling
- API design and integration patterns
- Security architecture
- DevOps and deployment strategies

When asked about UI components or architecture:
1. First analyze the current project to understand what you're working with
2. Scan for existing components in the actual codebase
3. Provide recommendations based on the discovered project type
4. Suggest improvements that fit the current technology stack
5. Never assume - always discover first

Always provide:
1. Clear architectural reasoning based on project analysis
2. Multiple solution options when applicable
3. Trade-offs and considerations
4. Implementation guidance specific to the discovered stack
5. Best practices for the identified project type

Format your responses with clear headings, diagrams where helpful (using mermaid syntax), and actionable recommendations.

${this.getSystemContextPrompt()}`;
    }

    private getDesignSystemPrompt(): string {
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

    private getAnalyzeSystemPrompt(): string {
        return `You are ArchitectGPT analyzing software architecture.

ANALYSIS APPROACH:
1. **Project Type Detection**: Identify what kind of project this is
2. **Technology Stack**: List all technologies, frameworks, and libraries found
3. **Component Scanning**: Find and catalog all UI components if present
4. **Architecture Patterns**: Identify design patterns and structure
5. **Integration Points**: Map APIs, services, and external dependencies

Provide:

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

    private getSynthesisSystemPrompt(): string {
        return `You are ArchitectGPT synthesizing findings from multiple sources to provide comprehensive recommendations.

YOUR TASK:
1. **Combine Findings**: Integrate project analysis, code scanning results, and web research
2. **Contextual Recommendations**: Provide suggestions specific to the discovered project type
3. **Practical Guidance**: Offer implementable solutions that fit the current codebase
4. **Best Practices**: Include industry standards relevant to the project
5. **Clear Structure**: Organize recommendations logically and actionably

STRUCTURE YOUR RESPONSE:

## Comprehensive UI Component Recommendations

### 📊 Project Analysis Summary
- Project Type: [discovered type]
- Technology Stack: [discovered stack]
- UI Framework: [if applicable]
- Architecture Pattern: [discovered pattern]

### 🔍 Current Components in Your Codebase
[List components found during code scan]

### 🌐 Industry Best Practices & Research Findings
[Relevant practices for this project type]

### 💡 Recommended UI Components/Solutions
[Specific recommendations based on all findings]

### 🛠️ Implementation Guide
[Step-by-step implementation for the current project]

### 📝 Code Examples
[Specific code examples using the project's technology stack]

Be specific, practical, and ensure all recommendations fit the discovered project context.

${this.getSystemContextPrompt()}`;
    }

    private getPlanSystemPrompt(): string {
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

    private async getProjectStructure(): Promise<string> {
        try {
            const files = await vscode.workspace.findFiles('**/*.{py,js,ts,jsx,tsx,json,md}', '**/node_modules/**', 50);
            return files.map(file => file.fsPath.split('/').slice(-3).join('/')).join('\n');
        } catch (error) {
            return 'Unable to read project structure';
        }
    }

    private extractPreviousContent(previousResults: TaskResult[]): string {
        return previousResults
            .map(result => result.content)
            .join('\n\n---\n\n')
            .substring(0, 2000); // Limit context size
    }
}