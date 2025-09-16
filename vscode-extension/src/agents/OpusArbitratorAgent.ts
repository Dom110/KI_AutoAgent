import * as vscode from 'vscode';
import { ChatAgent } from './base/ChatAgent';
import { AgentConfig, TaskRequest, TaskResult, WorkflowStep } from '../types';
import { VSCodeMasterDispatcher } from '../core/VSCodeMasterDispatcher';
import { AnthropicService } from '../utils/AnthropicService';
import { getClaudeCodeService, ClaudeCodeService } from '../services/ClaudeCodeService';

export class OpusArbitratorAgent extends ChatAgent {
    private anthropicService: AnthropicService;
    private claudeCodeService: ClaudeCodeService;

    constructor(context: vscode.ExtensionContext, dispatcher: VSCodeMasterDispatcher) {
        const config: AgentConfig = {
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

        this.log(`Processing ${command ? `/${command}` : 'general'} arbitration request: ${prompt.substring(0, 100)}...`);

        if (command) {
            await this.handleCommand(command, prompt, stream, token);
        } else {
            await this.handleGeneralArbitrationRequest(prompt, stream, token);
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

        } catch (error) {
            throw new Error(`Failed to process ${step.id}: ${(error as any).message}`);
        }
    }

    // Command Handlers

    private async handleJudgeCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
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

        } catch (error) {
            stream.markdown(`❌ **Judgment Error:** ${(error as any).message}`);
        }
    }

    private async handleResolveCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
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

        } catch (error) {
            stream.markdown(`❌ **Arbitration Error:** ${(error as any).message}`);
        }
    }

    private async handleEvaluateCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
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

        } catch (error) {
            stream.markdown(`❌ **Evaluation Error:** ${(error as any).message}`);
        }
    }

    private async handleVerdictCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
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

        } catch (error) {
            stream.markdown(`❌ **Verdict Error:** ${(error as any).message}`);
        }
    }

    private async handleGeneralArbitrationRequest(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
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

        } catch (error) {
            stream.markdown(`❌ **Judgment Error:** ${(error as any).message}`);
        }
    }

    // Service Methods

    private async validateServiceConfig(stream: vscode.ChatResponseStream): Promise<boolean> {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        const serviceMode = config.get<string>('claude.serviceMode', 'claude-code');
        
        if (serviceMode === 'api') {
            const apiKey = config.get<string>('anthropic.apiKey');
            if (!apiKey) {
                stream.markdown('❌ **Configuration Error**: Anthropic API key is required for Claude Opus 4.1\n\n');
                stream.markdown('Please configure your API key in VS Code Settings:\n');
                stream.markdown('1. Open Settings (Ctrl+,)\n');
                stream.markdown('2. Search for "KI AutoAgent"\n');
                stream.markdown('3. Set your Anthropic API key\n');
                return false;
            }
        } else if (serviceMode === 'claude-code') {
            const isClaudeCodeAvailable = await this.claudeCodeService.isAvailable();
            if (!isClaudeCodeAvailable) {
                stream.markdown(`❌ **Claude Code CLI not available for Opus 4.1**\n\n**To install:**\n\`\`\`bash\nnpm install -g @anthropic-ai/claude-code\n\`\`\`\n\nOr configure your Anthropic API key in VS Code settings.`);
                return false;
            }
        }
        
        return true;
    }

    private async getClaudeService(): Promise<{ chat: (messages: any[]) => Promise<string> }> {
        const config = vscode.workspace.getConfiguration('kiAutoAgent');
        const serviceMode = config.get<string>('claude.serviceMode', 'claude-code');
        
        console.log(`[OpusArbitrator] Using service mode: ${serviceMode}`);

        if (serviceMode === 'claude-code') {
            const isAvailable = await this.claudeCodeService.isAvailable();
            if (isAvailable) {
                console.log('[OpusArbitrator] Using Claude Code CLI with Opus model');
                return {
                    chat: async (messages: any[]) => {
                        // Extract the main user message content
                        const userMessage = messages.find(m => m.role === 'user')?.content || '';
                        const systemMessage = messages.find(m => m.role === 'system')?.content || '';
                        const fullPrompt = systemMessage ? `${systemMessage}\n\n${userMessage}` : userMessage;
                        
                        const response = await this.claudeCodeService.sendMessage(fullPrompt, {
                            model: 'opus', // Use Opus model for this agent
                            temperature: 0.5  // Lower temperature for more consistent judgments
                        });
                        return response.content;
                    }
                };
            } else {
                console.log('[OpusArbitrator] Claude Code CLI not available, falling back to Anthropic API');
            }
        }
        
        // Fall back to Anthropic API
        console.log('[OpusArbitrator] Using Anthropic API with Opus 4.1');
        return {
            chat: async (messages: any[]) => {
                return await this.anthropicService.chat(messages);
            }
        };
    }

    // Helper Methods

    private extractPreviousContent(previousResults: TaskResult[]): string {
        return previousResults
            .map(result => result.content)
            .join('\n\n---\n\n');
    }

    // System Prompts

    private getConflictResolutionPrompt(): string {
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

    private getDeepEvaluationPrompt(): string {
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

    private getFinalVerdictPrompt(): string {
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

    private getSupremeJudgmentPrompt(): string {
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

    protected getSlashCommands(): Array<{ command: string; description: string }> {
        return [
            { command: 'judge', description: 'Make supreme judgment on any matter' },
            { command: 'evaluate', description: 'Deep technical evaluation of options' },
            { command: 'resolve', description: 'Resolve conflicts between agents' },
            { command: 'verdict', description: 'Final binding verdict on decisions' }
        ];
    }
}