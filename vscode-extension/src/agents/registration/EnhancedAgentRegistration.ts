/**
 * Enhanced Agent Registration and Initialization
 * Registers the new enhanced agents with enterprise capabilities
 */

import * as vscode from 'vscode';
import { VSCodeMasterDispatcher } from '../../core/VSCodeMasterDispatcher';

// Import enhanced agents
import { EnhancedReviewerAgent } from '../EnhancedReviewerAgent';
import { EnhancedFixerBot } from '../EnhancedFixerBot';

// Import original agents for backward compatibility
import { ReviewerGPTAgent } from '../ReviewerGPTAgent';
import { FixerBotAgent } from '../FixerBotAgent';
import { OrchestratorAgent } from '../OrchestratorAgent';
import { ArchitectAgent } from '../ArchitectAgent';
import { CodeSmithAgent } from '../CodeSmithAgent';
import { DocuBotAgent } from '../DocuBotAgent';
import { OpusArbitratorAgent } from '../OpusArbitratorAgent';
import { TradeStratAgent } from '../TradeStratAgent';
import { ResearchAgent } from '../ResearchAgent';

/**
 * Configuration for enhanced agents
 */
export interface EnhancedAgentConfig {
    enableEnhancedAgents: boolean;
    replaceOriginalAgents: boolean;
    enableRuntimeAnalysis: boolean;
    enableDistributedTesting: boolean;
    enableAutoFix: boolean;
    enterpriseMode: boolean;
}

/**
 * Agent Registration Manager
 */
export class EnhancedAgentRegistration {
    private dispatcher: VSCodeMasterDispatcher;
    private context: vscode.ExtensionContext;
    private config: EnhancedAgentConfig;
    private agents: Map<string, any> = new Map();

    constructor(
        context: vscode.ExtensionContext,
        dispatcher: VSCodeMasterDispatcher
    ) {
        this.context = context;
        this.dispatcher = dispatcher;
        this.config = this.loadConfiguration();
    }

    /**
     * Register all agents including enhanced versions
     */
    async registerAllAgents(): Promise<void> {
        console.log('[EnhancedAgentRegistration] Starting agent registration...');

        try {
            // Register orchestrator (always needed)
            await this.registerAgent('orchestrator', OrchestratorAgent);

            // Register architect
            await this.registerAgent('architect', ArchitectAgent);

            // Register CodeSmith
            await this.registerAgent('codesmith', CodeSmithAgent);

            // Register DocuBot
            await this.registerAgent('docubot', DocuBotAgent);

            // Register OpusArbitrator
            await this.registerAgent('opus', OpusArbitratorAgent);

            // Register TradeStrat
            await this.registerAgent('tradestrat', TradeStratAgent);

            // Register ResearchAgent
            await this.registerAgent('research', ResearchAgent);

            // Register ReviewerAgent (enhanced or original)
            if (this.config.enableEnhancedAgents) {
                console.log('[EnhancedAgentRegistration] Registering ENHANCED ReviewerAgent');
                await this.registerAgent('enhanced-reviewer', EnhancedReviewerAgent);

                if (this.config.replaceOriginalAgents) {
                    // Replace original with enhanced
                    await this.registerAgent('reviewer', EnhancedReviewerAgent);
                } else {
                    // Keep both versions
                    await this.registerAgent('reviewer', ReviewerGPTAgent);
                }
            } else {
                // Original only
                await this.registerAgent('reviewer', ReviewerGPTAgent);
            }

            // Register FixerBot (enhanced or original)
            if (this.config.enableEnhancedAgents) {
                console.log('[EnhancedAgentRegistration] Registering ENHANCED FixerBot');
                await this.registerAgent('enhanced-fixer', EnhancedFixerBot);

                if (this.config.replaceOriginalAgents) {
                    // Replace original with enhanced
                    await this.registerAgent('fixer', EnhancedFixerBot);
                } else {
                    // Keep both versions
                    await this.registerAgent('fixer', FixerBotAgent);
                }
            } else {
                // Original only
                await this.registerAgent('fixer', FixerBotAgent);
            }

            console.log(`[EnhancedAgentRegistration] Successfully registered ${this.agents.size} agents`);

            // Show notification about enhanced agents
            if (this.config.enableEnhancedAgents) {
                vscode.window.showInformationMessage(
                    '🚀 Enhanced Agents Activated: Runtime Analysis, Distributed Testing, and Auto-Fix capabilities enabled!'
                );
            }

        } catch (error) {
            console.error('[EnhancedAgentRegistration] Registration error:', error);
            vscode.window.showErrorMessage(
                `Failed to register agents: ${(error as any).message}`
            );
        }
    }

    /**
     * Register a single agent
     */
    private async registerAgent(
        name: string,
        AgentClass: any
    ): Promise<void> {
        try {
            const agent = new AgentClass(this.context, this.dispatcher);
            this.agents.set(name, agent);
            this.dispatcher.registerAgent(name, agent);
            console.log(`[EnhancedAgentRegistration] Registered agent: ${name}`);
        } catch (error) {
            console.error(`[EnhancedAgentRegistration] Failed to register ${name}:`, error);
            throw error;
        }
    }

    /**
     * Load configuration
     */
    private loadConfiguration(): EnhancedAgentConfig {
        const config = vscode.workspace.getConfiguration('kiAutoAgent.enhanced');

        return {
            enableEnhancedAgents: config.get('enableEnhancedAgents', true),
            replaceOriginalAgents: config.get('replaceOriginalAgents', false),
            enableRuntimeAnalysis: config.get('enableRuntimeAnalysis', true),
            enableDistributedTesting: config.get('enableDistributedTesting', true),
            enableAutoFix: config.get('enableAutoFix', true),
            enterpriseMode: config.get('enterpriseMode', false)
        };
    }

    /**
     * Update configuration
     */
    async updateConfiguration(updates: Partial<EnhancedAgentConfig>): Promise<void> {
        const config = vscode.workspace.getConfiguration('kiAutoAgent.enhanced');

        for (const [key, value] of Object.entries(updates)) {
            await config.update(key, value, vscode.ConfigurationTarget.Global);
        }

        // Reload configuration
        this.config = this.loadConfiguration();

        // Re-register agents if needed
        if (updates.enableEnhancedAgents !== undefined ||
            updates.replaceOriginalAgents !== undefined) {
            await this.reregisterAgents();
        }
    }

    /**
     * Re-register agents after configuration change
     */
    private async reregisterAgents(): Promise<void> {
        console.log('[EnhancedAgentRegistration] Re-registering agents...');

        // Clear existing agents
        this.agents.clear();

        // Re-register all agents
        await this.registerAllAgents();
    }

    /**
     * Get registered agent
     */
    getAgent(name: string): any {
        return this.agents.get(name);
    }

    /**
     * Get all registered agents
     */
    getAllAgents(): Map<string, any> {
        return this.agents;
    }

    /**
     * Check if enhanced agents are enabled
     */
    areEnhancedAgentsEnabled(): boolean {
        return this.config.enableEnhancedAgents;
    }

    /**
     * Check if enterprise mode is enabled
     */
    isEnterpriseModeEnabled(): boolean {
        return this.config.enterpriseMode;
    }

    /**
     * Enable enterprise mode
     */
    async enableEnterpriseMode(): Promise<void> {
        await this.updateConfiguration({
            enterpriseMode: true,
            enableEnhancedAgents: true,
            enableRuntimeAnalysis: true,
            enableDistributedTesting: true,
            enableAutoFix: true
        });

        vscode.window.showInformationMessage(
            '🏢 Enterprise Mode Activated: All enhanced capabilities enabled!'
        );
    }

    /**
     * Dispose all agents
     */
    dispose(): void {
        this.agents.forEach(agent => {
            if (typeof agent.dispose === 'function') {
                agent.dispose();
            }
        });
        this.agents.clear();
    }
}

/**
 * Initialize enhanced agents
 */
export async function initializeEnhancedAgents(
    context: vscode.ExtensionContext
): Promise<EnhancedAgentRegistration> {
    console.log('[Enhanced] Initializing enhanced agent system...');

    // Create dispatcher
    const dispatcher = new VSCodeMasterDispatcher(context);

    // Create registration manager
    const registration = new EnhancedAgentRegistration(context, dispatcher);

    // Register all agents
    await registration.registerAllAgents();

    // Register commands for enterprise mode
    context.subscriptions.push(
        vscode.commands.registerCommand('kiAutoAgent.enableEnterpriseMode', async () => {
            await registration.enableEnterpriseMode();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('kiAutoAgent.toggleEnhancedAgents', async () => {
            const current = registration.areEnhancedAgentsEnabled();
            await registration.updateConfiguration({
                enableEnhancedAgents: !current
            });

            vscode.window.showInformationMessage(
                current ?
                '⚠️ Enhanced agents disabled. Using original agents.' :
                '🚀 Enhanced agents enabled with enterprise capabilities!'
            );
        })
    );

    // Add status bar item for enhanced mode
    const statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
    );

    statusBarItem.text = registration.areEnhancedAgentsEnabled() ?
        '$(rocket) Enhanced' :
        '$(circle-outline) Standard';

    statusBarItem.tooltip = registration.areEnhancedAgentsEnabled() ?
        'Enhanced agents with enterprise capabilities active' :
        'Standard agents active';

    statusBarItem.command = 'kiAutoAgent.toggleEnhancedAgents';
    statusBarItem.show();

    context.subscriptions.push(statusBarItem);

    // Dispose on deactivation
    context.subscriptions.push({
        dispose: () => registration.dispose()
    });

    console.log('[Enhanced] Enhanced agent system initialized successfully');

    return registration;
}

/**
 * Export configuration interface for settings
 */
export function contributeConfiguration(): any[] {
    return [
        {
            id: 'kiAutoAgent.enhanced',
            title: 'Enhanced Agent Settings',
            properties: {
                'kiAutoAgent.enhanced.enableEnhancedAgents': {
                    type: 'boolean',
                    default: true,
                    description: '🚀 Enable enhanced agents with enterprise capabilities'
                },
                'kiAutoAgent.enhanced.replaceOriginalAgents': {
                    type: 'boolean',
                    default: false,
                    description: '🔄 Replace original agents with enhanced versions'
                },
                'kiAutoAgent.enhanced.enableRuntimeAnalysis': {
                    type: 'boolean',
                    default: true,
                    description: '🔬 Enable runtime analysis and profiling capabilities'
                },
                'kiAutoAgent.enhanced.enableDistributedTesting': {
                    type: 'boolean',
                    default: true,
                    description: '🌐 Enable distributed systems testing capabilities'
                },
                'kiAutoAgent.enhanced.enableAutoFix': {
                    type: 'boolean',
                    default: true,
                    description: '🤖 Enable automated fix patterns'
                },
                'kiAutoAgent.enhanced.enterpriseMode': {
                    type: 'boolean',
                    default: false,
                    description: '🏢 Enable full enterprise mode with all capabilities'
                }
            }
        }
    ];
}