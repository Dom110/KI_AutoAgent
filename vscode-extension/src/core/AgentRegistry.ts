/**
 * Agent Registry and Task Delegation System
 * Central registry for all agents with capability mapping and task delegation logic
 */
import * as vscode from 'vscode';

export interface AgentCapability {
    id: string;
    name: string;
    model: string;
    specialization: string;
    canHandle: string[];
    instructionSet: string;
}

export class AgentRegistry {
    private static instance: AgentRegistry;

    // Static registry of agent capabilities for task delegation
    public static readonly AGENT_CAPABILITIES: Record<string, {
        specialization: string;
        canHandle: string[];
        model: string;
        instructionSet: string;
    }> = {
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

    public static getInstance(): AgentRegistry {
        if (!AgentRegistry.instance) {
            AgentRegistry.instance = new AgentRegistry();
        }
        return AgentRegistry.instance;
    }

    /**
     * Get all registered agents with their capabilities
     */
    public getRegisteredAgents(): AgentCapability[] {
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
    public getAgentInfo(agentId: string): AgentCapability | undefined {
        const capability = AgentRegistry.AGENT_CAPABILITIES[agentId];
        if (!capability) return undefined;

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
    public suggestAgentForTask(taskDescription: string): string | null {
        const lowerTask = taskDescription.toLowerCase();
        let bestMatch: { agent: string; score: number } | null = null;

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
    public getAgentListDescription(): string {
        const agents = this.getRegisteredAgents();
        return agents.map((agent, index) =>
            `${index + 1}. **${agent.name}** - ${agent.specialization} (${agent.model})`
        ).join('\n');
    }

    /**
     * Get task delegation suggestions for a specific agent
     */
    public getTaskDelegationInfo(currentAgentId: string): string {
        const currentAgent = this.getAgentInfo(currentAgentId);
        if (!currentAgent) return '';

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

    private getAgentDisplayName(agentId: string): string {
        const nameMap: Record<string, string> = {
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