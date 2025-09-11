/**
 * Orchestrator Agent - Universal AI assistant that routes tasks to specialized agents
 * This is the main entry point that users interact with
 */
import * as vscode from 'vscode';
import { ChatAgent } from './base/ChatAgent';
import { AgentConfig, TaskRequest, TaskResult, WorkflowStep } from '../types';
import { VSCodeMasterDispatcher } from '../core/VSCodeMasterDispatcher';
import { OpenAIService } from '../utils/OpenAIService';

export class OrchestratorAgent extends ChatAgent {
    private openAIService: OpenAIService;

    constructor(context: vscode.ExtensionContext, dispatcher: VSCodeMasterDispatcher) {
        const config: AgentConfig = {
            participantId: 'ki-autoagent.orchestrator',
            name: 'ki',
            fullName: 'KI AutoAgent Orchestrator',
            description: 'Universal AI assistant that automatically routes tasks to specialized agents',
            model: 'gpt-4o',
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

        this.log(`Orchestrator processing ${command ? `/${command}` : 'general'} request: ${prompt.substring(0, 100)}...`);

        if (command) {
            await this.handleCommand(command, prompt, stream, token);
        } else {
            // General orchestration - the main flow
            await this.handleGeneralRequest(prompt, stream, token);
        }
    }

    protected async processWorkflowStep(
        step: WorkflowStep,
        request: TaskRequest,
        previousResults: TaskResult[]
    ): Promise<TaskResult> {
        
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
    private async handleGeneralRequest(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
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
            
            const taskRequest: TaskRequest = {
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
                    this.createActionButton(
                        suggestion.title,
                        'ki-autoagent.applySuggestion',
                        [suggestion.data],
                        stream
                    );
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
            this.createActionButton(
                '📊 Show Agent Statistics',
                'ki-autoagent.showAgentStats',
                [],
                stream
            );
            
        } catch (error) {
            stream.markdown(`❌ **Error during orchestration**: ${error.message}\n\n`);
            
            // Fallback to single agent
            stream.markdown(`💡 **Fallback**: Routing to @${intent?.agent || 'codesmith'} for direct assistance...\n\n`);
            
            // You could implement fallback logic here
            await this.handleFallback(prompt, stream, token);
        }
    }

    // Command Handlers

    private async handleTaskCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
        stream.markdown(`## 📋 Task Execution\n\n`);
        stream.markdown(`**Task:** ${prompt}\n\n`);
        
        // Same as general request but with explicit task framing
        await this.handleGeneralRequest(prompt, stream, token);
    }

    private async handleAgentsCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
        stream.markdown(`## 🤖 Available Specialized Agents\n\n`);
        
        const agents = [
            { name: '@architect', fullName: 'ArchitectGPT', description: 'System Architecture & Design Expert', model: 'GPT-4o', specialties: 'Design, Architecture, Planning' },
            { name: '@codesmith', fullName: 'CodeSmithClaude', description: 'Senior Python/Web Developer', model: 'Claude 3.5 Sonnet', specialties: 'Implementation, Testing, Optimization' },
            { name: '@docu', fullName: 'DocuBot', description: 'Technical Documentation Expert', model: 'GPT-4o', specialties: 'Docs, README, API Reference' },
            { name: '@reviewer', fullName: 'ReviewerGPT', description: 'Code Review & Security Expert', model: 'GPT-4o-mini', specialties: 'QA, Security, Performance' },
            { name: '@fixer', fullName: 'FixerBot', description: 'Bug Fixing & Optimization Expert', model: 'Claude 3.5 Sonnet', specialties: 'Debugging, Patching, Refactoring' },
            { name: '@tradestrat', fullName: 'TradeStrat', description: 'Trading Strategy Expert', model: 'Claude 3.5 Sonnet', specialties: 'Strategies, Backtesting, Risk' },
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
                    const { successRate, totalExecutions, averageResponseTime } = agentStats as any;
                    stream.markdown(`**${agentId}**: ${totalExecutions} executions, ${(successRate * 100).toFixed(1)}% success rate, ${averageResponseTime.toFixed(0)}ms avg response\n`);
                }
            }
        } catch (error) {
            // Stats not available yet
        }
    }

    private async handleWorkflowCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
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
            this.createActionButton(
                '⚡ Execute This Workflow',
                'ki-autoagent.executeWorkflow',
                [prompt, response],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ Error creating workflow: ${error.message}`);
        }
    }

    // Fallback handler
    private async handleFallback(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
        // Simple fallback using GPT-4o directly
        try {
            const systemPrompt = `You are a helpful coding assistant. Provide clear, actionable assistance for development tasks.`;
            const response = await this.openAIService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: prompt }
            ]);

            stream.markdown(response);

        } catch (error) {
            stream.markdown(`❌ Fallback also failed: ${error.message}`);
        }
    }

    // System prompts

    private getWorkflowSystemPrompt(): string {
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
- @research (web research, information)

Make workflows realistic, actionable, and well-structured.`;
    }
}